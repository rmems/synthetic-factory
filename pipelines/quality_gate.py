#!/usr/bin/env python3
"""Quality gate before volume — dedup + synthetic/real mix enforcement.

Enforces SOTA guidance (~30% rephrased synthetic / 70% real) and prevents
crude-synthetic collapse via exact-hash **and** embedding near-duplicate
dedup. Both dedup signals and the mix policy are blocking — see
``docs/quality-gate.md``.

Dedup signals
-------------
1. Exact-hash dedup (always on): SHA-256 of a canonical training-identity
   view. The view includes states, decisions, actions, outcomes and rewards,
   while omitting a wrapper's bookkeeping id. Any hash collision →
   ``blocked = true``. This catches verbatim training-unit duplicates.

2. Embedding dedup (on by default, ``--no-embedding-dedup`` to skip):
   every retained record is embedded once by a shared, deterministic
   encoder and pairs with ``cosine_sim > threshold`` are grouped into a
   near-duplicate cluster. One member of each cluster is kept; the rest
   are reported in ``duplicates`` with ``kind="embedding"`` and a
   ``reason``, and the gate blocks.

   Default threshold: ``0.97``

   Rationale:
   - 0.97 cosine ≈ 14° angular distance. Empirically, rephrased
     synthetic trajectories from the same factory prompt cluster at
     0.93–0.96, while true paraphrases of distinct scenarios sit at
     0.85–0.92. Setting 0.97 keeps recall high for collapse-mode
     outputs (temperature collapse, template regurgitation) while
     avoiding false positives on legitimately similar domains.
   - Lowering to 0.93–0.95 increases recall (catches looser paraphrases)
     but raises false-positive rate on overlapping domains (e.g., two
     dairy-AMS episodes sharing SOP boilerplate). Raising to 0.98–0.99
     reduces false positives further but may miss template-level dedup
     that still harms diversity.
   - Tuning guidance: sweep 0.93/0.95/0.97/0.98 on a held-out factory
     slice and inspect duplicate groups. Prefer the highest threshold
     that still collapses known duplicate seeds (same seed, temp=0
     re-runs). Record the chosen value in the run's ``quality_report``.

   Encoder: this repository is stdlib-only, so the shipped encoder is a
   deterministic lexical one (``EMBEDDING_ENCODER``) — TF-IDF over a
   semantic-similarity view that excludes canonical record identifiers.
   Path-qualified, case-sensitive Unicode words, operators, typed empty/null
   sentinels and position-qualified sequence leaves keep code and structure
   observable. Features are L2-normalized, so the dot product *is* the cosine.
   Candidate pairs come from a separate frequency-aware weighted sketch and
   every candidate is then scored exactly, so precision is exact and only
   recall is approximate (see ``EMBEDDING_LSH_BANDS``).

Synthetic / Real Mix
--------------------
Counts ``state.sim_or_real`` / ``provenance.kind`` values. Buckets
``{designed, simulated, hil}`` as synthetic and ``{real, unknown}`` as
real_unknown; records with no recognized label are reported separately as
``unlabeled`` rather than assumed real. The policy is **blocking**:
``synthetic_ratio`` above ``target + tolerance`` (default 0.30 + 0.20 =
0.50) blocks promotion. Ratios above target but inside the tolerance band
warn. An optional floor (``--min-synthetic-ratio``) and an optional
unlabeled ceiling (``--max-unlabeled-ratio``) are off by default.

Usage:
  python3 pipelines/quality_gate.py <run_dir> [--json] [--threshold 0.97]
      [--mix-target 0.30] [--mix-tolerance 0.20] [--manifest PATH]

Co-authored-by: Muse Code powered by Muse Spark <muse-spark@meta.com>
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path
from typing import NamedTuple, Optional

_PIPELINES = Path(__file__).resolve().parent
if str(_PIPELINES) not in sys.path:
    sys.path.insert(0, str(_PIPELINES))
from check_records import walk_key  # noqa: E402
from training_audit import reward_shape  # noqa: E402

# ---------------------------------------------------------------------------
# Embedding dedup threshold — single source of truth. See module docstring
# and docs/quality-gate.md. Downstream embedding stages should import this
# constant rather than re-defining the value.
# ---------------------------------------------------------------------------
DEFAULT_EMBEDDING_THRESHOLD: float = 0.97
"""Default cosine-similarity threshold for embedding dedup.

Pairs with cosine_sim > DEFAULT_EMBEDDING_THRESHOLD are treated as
near-duplicates. Tuned to 0.97 (see module docstring for sweep guidance).
Override per-run via ``--threshold`` when you have evidence the factory's
paraphrase cluster sits higher/lower.
"""

# ---------------------------------------------------------------------------
# Synthetic/real mix policy — single source of truth for the ~30/70 default.
# ---------------------------------------------------------------------------
DEFAULT_TARGET_SYNTHETIC_RATIO: float = 0.30
"""SOTA-optimal share of rephrased synthetic data (``Demystifying Synthetic
Data``): ~30% synthetic / 70% real."""

DEFAULT_MIX_TOLERANCE: float = 0.20
"""Absolute slack above the target before the gate blocks. 0.30 + 0.20 = 0.50,
the ratio this gate used to merely warn at."""

SYNTHETIC_KINDS = frozenset({"designed", "simulated", "hil"})
"""Provenance labels counted as rephrased synthetic."""

REAL_KINDS = frozenset({"real", "unknown"})
"""Provenance labels counted as real/unknown. Anything else (including a
missing label) lands in the separate ``unlabeled`` bucket."""

MAX_ERROR_EXAMPLES = 10
"""Cap on per-category read/parse failure examples kept in the report."""

EMBEDDING_ENCODER = "lexical-tfidf/5"
"""Identifier of the shipped deterministic encoder, recorded in the report so
a corpus embedded by a different encoder is never compared against one of
these runs on threshold alone."""

EMBEDDING_MINHASH_SLOTS = 32
EMBEDDING_LSH_BANDS = 8
"""MinHash LSH banding for near-duplicate *candidate* generation: a 32-slot
one-permutation sketch read as 8 bands of 4. Every candidate is then scored
with an exact cosine, so banding can only cost recall, never precision. The
weighted-tier representation below makes sketch overlap track term frequency;
planted-clone and high-TF regressions guard recall."""

EMBEDDING_CANDIDATE_SKETCH = "weighted-tier-minhash/1"
"""Frequency-aware candidate representation, separate from exact identity
and the semantic TF-IDF vector used for the final verdict."""

EMBEDDING_SKETCH_LEVELS = 64
"""Number of deterministic weight tiers used to approximate weighted Jaccard.
Dominant repeated terms therefore dominate candidate recall just as they do
the final sublinear-TF cosine, instead of collapsing to one set member."""

DEFAULT_MAX_EMBEDDING_PAIRS = 2_000_000
"""Safety cap on candidate pairs. Hitting it blocks because a partial-recall
audit cannot certify the corpus."""

_BIGRAM_SEP = "\x00"
_PATH_SEP = "\x1f"
_SKETCH_SEP = "\x1e"

_IDENTITY_FIELDS = (
    "state",
    "steps",
    "proposed_action",
    "safety_decision",
    "executed_action",
    "future_outcome",
    "outcome",
    "reward_components",
    "reward",
    # Multi-agent coordination records share generic reward envelopes. The
    # training unit is the joint decision, not the boolean success flag.
    "goal",
    "agents",
    "transcript",
    "disagreements",
    "resolution",
    "joint_outcome",
)
_CANONICAL_ID_KEYS = frozenset(
    {"episode_id", "record_id", "trajectory_id", "pair_id", "sample_id"}
)
_SEMANTIC_ROOT_BOOKKEEPING_KEYS = frozenset(
    {"id", "meta", "provenance", "tag_provenance"}
)

# Unicode-name markers for scripts whose ordinary prose does not reliably
# provide spaces between lexical words. The fallback is intentionally limited
# to these scripts: segmenting every Latin/Arabic/etc. word into characters
# would discard useful word-level precision.
_UNSEGMENTED_SCRIPT_MARKERS = (
    "CJK",
    "IDEOGRAPH",
    "HIRAGANA",
    "KATAKANA",
    "THAI",
    "LAO",
    "KHMER",
    "MYANMAR",
)


class MixPolicy(NamedTuple):
    """Blocking synthetic/real mix policy. Defaults to ~30/70 with 0.20 slack."""

    target: float = DEFAULT_TARGET_SYNTHETIC_RATIO
    tolerance: float = DEFAULT_MIX_TOLERANCE
    max_synthetic_ratio: Optional[float] = None
    min_synthetic_ratio: Optional[float] = None
    max_unlabeled_ratio: Optional[float] = None

    @property
    def ceiling(self) -> float:
        """Blocking synthetic-ratio ceiling."""
        if self.max_synthetic_ratio is not None:
            return self.max_synthetic_ratio
        return min(1.0, self.target + self.tolerance)

    def validate(self) -> "MixPolicy":
        """Reject a policy that could never be satisfied. Returns self."""
        for name, value in (
            ("mix target", self.target),
            ("mix tolerance", self.tolerance),
            ("max synthetic ratio", self.max_synthetic_ratio),
            ("min synthetic ratio", self.min_synthetic_ratio),
            ("max unlabeled ratio", self.max_unlabeled_ratio),
        ):
            if value is None:
                continue
            if not math.isfinite(value) or not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be a finite ratio in [0, 1], got {value!r}")
        if self.min_synthetic_ratio is not None and self.min_synthetic_ratio > self.ceiling:
            raise ValueError(
                f"min synthetic ratio {self.min_synthetic_ratio} exceeds the "
                f"blocking ceiling {self.ceiling}"
            )
        return self

    def as_dict(self) -> dict:
        return {
            "target_synthetic_ratio": self.target,
            "tolerance": self.tolerance,
            "max_synthetic_ratio": self.ceiling,
            "min_synthetic_ratio": self.min_synthetic_ratio,
            "max_unlabeled_ratio": self.max_unlabeled_ratio,
            "blocking": True,
        }


def canonical_blob(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


_PREFERENCE_WRAPPER_FIELDS = (
    "goal",
    "critique",
    "reward",
    "reward_delta",
    "lesson_category",
)


def _preference_identity_side(value):
    """Return all modeled training fields from one preference side.

    Preference actions and outcomes are labels, not bookkeeping. Keeping only
    ``state`` made distinct preference training units exact-hash collisions.
    Malformed sides retain their complete value so unrelated malformed records
    do not all collapse to the same sentinel.
    """
    if not isinstance(value, dict):
        return value
    modeled = {key: value[key] for key in _IDENTITY_FIELDS if key in value}
    return modeled or value


def exact_identity_view(obj):
    """Canonical training identity used only by exact-hash dedup.

    Wrapper ids are deliberately outside modeled state/action records, as they
    were in the original contract. Multi-agent coordination keeps goal, agents,
    transcript, disagreements, resolution and joint_outcome so a shared
    ``{"success": true}`` reward cannot collapse unrelated debates. Preference
    wrappers keep the shared task, critique, and wrapper reward alongside the
    two sides. Canonical ids inside fallback shapes remain exact identity; the
    independent semantic view removes them before cosine.
    """
    if not isinstance(obj, dict):
        # A JSONL line that parses to a scalar/array must hash, not raise.
        return obj
    if "chosen" in obj or "rejected" in obj:
        # Malformed pairs (missing or non-object side) must hash, not raise —
        # this gate runs over untrusted generated JSONL. Both fields are always
        # present in the key set so a one-sided record stays distinguishable.
        view = {
            "chosen": _preference_identity_side(obj.get("chosen")),
            "rejected": _preference_identity_side(obj.get("rejected")),
        }
        for key in _PREFERENCE_WRAPPER_FIELDS:
            if key in obj:
                view[key] = obj[key]
        return view
    keys = {key: obj[key] for key in _IDENTITY_FIELDS if key in obj}
    if not keys:
        # Shapes this gate does not model (e.g. bridge records carrying state
        # under language_view) must not all hash to the empty key set, which
        # would report every record after the first as a duplicate.
        return obj
    return keys


def dedup_view(obj):
    """Backward-compatible name for the exact-identity representation."""
    return exact_identity_view(obj)


def _without_canonical_ids(value, *, root=True):
    """Copy ``value`` while removing only canonical record identifiers."""
    if isinstance(value, dict):
        return {
            key: _without_canonical_ids(child, root=False)
            for key, child in value.items()
            if key not in _CANONICAL_ID_KEYS
            and not (root and key in _SEMANTIC_ROOT_BOOKKEEPING_KEYS)
        }
    if isinstance(value, list):
        return [_without_canonical_ids(child, root=False) for child in value]
    if isinstance(value, tuple):
        return tuple(_without_canonical_ids(child, root=False) for child in value)
    return value


def semantic_similarity_view(obj):
    """Training semantics used only by the cosine encoder.

    Exact identity and semantic similarity intentionally differ: canonical ids
    can distinguish exact records, but must not hide otherwise identical
    training content from near-duplicate detection.
    """
    return _without_canonical_ids(exact_identity_view(obj))


def record_hash(obj):
    blob = canonical_blob(exact_identity_view(obj))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:16]


def _path_child(path, key):
    """Return an unambiguous JSON-pointer-like child path."""
    escaped = str(key).replace("~", "~0").replace("/", "~1")
    return f"{path}/k:{escaped}"


def _uses_unsegmented_script(word):
    for char in word:
        name = unicodedata.name(char, "")
        if any(marker in name for marker in _UNSEGMENTED_SCRIPT_MARKERS):
            return True
    return False


def _graphemes(word):
    """Return a stdlib-only approximation of extended grapheme clusters."""
    clusters = []
    for char in word:
        if unicodedata.category(char).startswith("M") and clusters:
            clusters[-1] += char
        else:
            clusters.append(char)
    return clusters


def _string_units(text):
    """Yield ordered word/operator units without erasing code semantics."""
    normalized = unicodedata.normalize("NFC", text)
    current = []
    punctuation = []

    def flush_word():
        if current:
            word = "".join(current)
            current.clear()
            return [("word", word)]
        return []

    def flush_punctuation():
        if punctuation:
            operator = "".join(punctuation)
            punctuation.clear()
            return [("operator", operator)]
        return []

    for char in normalized:
        category = unicodedata.category(char)
        word_char = char == "_" or char.isalnum() or (
            category.startswith("M") and current
        )
        if word_char:
            yield from flush_punctuation()
            current.append(char)
        elif char.isspace():
            yield from flush_word()
            yield from flush_punctuation()
        else:
            yield from flush_word()
            punctuation.append(char)
    yield from flush_word()
    yield from flush_punctuation()


def _leaf_words(value, out, path="$"):
    """Collect canonical, path-qualified Unicode words from leaf values.

    Qualifying values by their full field path prevents equal words under
    semantically different fields from becoming identical features. Mapping
    keys are traversed in sorted order so JSON insertion order cannot change
    cross-leaf bigrams. List positions are explicit: bigram multisets alone do
    not distinguish all repeated-token sequences.
    """
    if isinstance(value, dict):
        if not value:
            out.append(f"{path}{_PATH_SEP}dict-empty")
            return
        for key in sorted(value):
            _leaf_words(value[key], out, _path_child(path, key))
        return
    elif isinstance(value, (list, tuple)):
        if not value:
            out.append(f"{path}{_PATH_SEP}list-empty")
            return
        for index, item in enumerate(value):
            _leaf_words(item, out, f"{path}/i:{index}")
        return
    elif value is None:
        out.append(f"{path}{_PATH_SEP}null")
        return
    elif isinstance(value, bool):
        out.append(f"{path}{_PATH_SEP}bool:{'true' if value else 'false'}")
        return
    elif isinstance(value, int):
        out.append(f"{path}{_PATH_SEP}int:{value}")
        return
    elif isinstance(value, float):
        out.append(f"{path}{_PATH_SEP}float:{value!r}")
        return
    elif isinstance(value, str):
        text = unicodedata.normalize("NFC", value)
    else:
        # JSON inputs cannot contain other objects; keep this defensive path
        # non-throwing for direct callers.
        return
    if not text:
        out.append(f"{path}{_PATH_SEP}str-empty")
        return
    emitted = False
    for kind, unit in _string_units(text):
        emitted = True
        if kind == "operator":
            out.append(f"{path}{_PATH_SEP}str-op:{unit}")
        elif _uses_unsegmented_script(unit):
            # A whole CJK/Japanese/Thai sentence is one ``\w+`` match. Emit
            # path-qualified graphemes instead so a small edit retains enough
            # shared features to become an LSH candidate. ``embedding_tokens``
            # adds adjacent bigrams, preserving order and limiting anagram
            # false positives.
            out.extend(
                f"{path}{_PATH_SEP}str-char:{cluster}"
                for cluster in _graphemes(unit)
            )
        else:
            # Keep a folded channel for natural-language recall and an exact
            # channel so identifiers such as User/user remain distinguishable.
            out.append(f"{path}{_PATH_SEP}str-fold:{unit.casefold()}")
            out.append(f"{path}{_PATH_SEP}str-case:{unit}")
    if not emitted:
        out.append(f"{path}{_PATH_SEP}str-whitespace")


def embedding_tokens(obj):
    """Term counts (unigrams + bigrams) for the near-duplicate encoder."""
    words: list = []
    _leaf_words(semantic_similarity_view(obj), words)
    tokens = Counter(words)
    tokens.update(
        f"{first}{_BIGRAM_SEP}{second}" for first, second in zip(words, words[1:])
    )
    return tokens


def _tfidf_vector(tokens, idf):
    """L2-normalized sublinear TF-IDF vector, so a dot product is a cosine."""
    vector = {}
    for token, count in tokens.items():
        weight = (1.0 + math.log(count)) * idf[token]
        if weight:
            vector[token] = weight
    norm = math.sqrt(sum(weight * weight for weight in vector.values()))
    if not norm:
        return None
    return {token: weight / norm for token, weight in vector.items()}


def candidate_sketch_features(vector):
    """Frequency-aware feature tiers used only for LSH candidate recall.

    The final verdict still uses the exact TF-IDF cosine. Expanding each
    normalized weight into deterministic tiers approximates weighted Jaccard,
    so a term repeated thousands of times is not reduced to the same one-bit
    presence signal as a singleton.
    """
    for token in sorted(vector):
        tiers = max(1, math.ceil(vector[token] * EMBEDDING_SKETCH_LEVELS))
        for tier in range(tiers):
            yield f"{token}{_SKETCH_SEP}{tier}"


def _cosine(left, right):
    if len(left) > len(right):
        left, right = right, left
    total = sum(weight * right[token] for token, weight in left.items() if token in right)
    # Float error can push identical vectors a hair past 1.0.
    return min(1.0, max(-1.0, total))


def _minhash_signature(tokens):
    """One-permutation MinHash sketch of a token set.

    One hash per token (not one per token per permutation): the hash picks the
    bin, the rest of it is the value. Empty bins are filled by rotating to the
    next occupied bin, which keeps the sketch positional — and therefore
    bandable — without holding a per-token permutation table in memory.
    """
    slots = EMBEDDING_MINHASH_SLOTS
    bins = [None] * slots
    filled = 0
    for token in tokens:
        digest = int.from_bytes(
            hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest(), "big"
        )
        slot = digest % slots
        value = digest // slots
        current = bins[slot]
        if current is None:
            bins[slot] = value
            filled += 1
        elif value < current:
            bins[slot] = value
    if not filled:
        return None
    if filled < slots:
        # Donors come from the pre-densification sketch, so a borrowed value
        # can never be borrowed again and the result stays order-independent.
        occupied = list(bins)
        for slot in range(slots):
            if bins[slot] is not None:
                continue
            for step in range(1, slots):
                donor = occupied[(slot + step) % slots]
                if donor is not None:
                    bins[slot] = donor
                    break
    return tuple(bins)


def _candidate_pairs(signatures, max_pairs):
    """MinHash-LSH candidate pairs, in deterministic order.

    Returns ``(pairs, truncated)``. ``pairs`` is sorted so downstream
    clustering is reproducible regardless of bucket iteration order.
    """
    rows = EMBEDDING_MINHASH_SLOTS // EMBEDDING_LSH_BANDS
    buckets = defaultdict(list)
    for index, signature in signatures:
        for band in range(EMBEDDING_LSH_BANDS):
            buckets[(band, signature[band * rows: (band + 1) * rows])].append(index)
    pairs = set()
    truncated = False
    for members in buckets.values():
        if truncated:
            break
        if len(members) < 2:
            continue
        for offset, left in enumerate(members):
            for right in members[offset + 1:]:
                pair = (left, right)
                if pair in pairs:
                    continue
                if len(pairs) >= max_pairs:
                    truncated = True
                    break
                pairs.add(pair)
            if truncated:
                break
    return sorted(pairs), truncated


class _Union:
    """Union-find over record indices, used to group near-duplicate pairs."""

    def __init__(self):
        self.parent = {}

    def find(self, item):
        self.parent.setdefault(item, item)
        root = item
        while self.parent[root] != root:
            root = self.parent[root]
        while self.parent[item] != root:
            self.parent[item], item = root, self.parent[item]
        return root

    def union(self, left, right):
        left_root, right_root = self.find(left), self.find(right)
        if left_root != right_root:
            # Lowest index wins so the cluster representative is the first
            # occurrence in file/line order.
            low, high = sorted((left_root, right_root))
            self.parent[high] = low

    def groups(self):
        clusters = defaultdict(list)
        for item in sorted(self.parent):
            clusters[self.find(item)].append(item)
        return [members for _root, members in sorted(clusters.items()) if len(members) > 1]


def _where(record):
    return {"file": record["file"], "line": record["line"]}


def _state_provenance_kind(state):
    """Return the provenance label carried by a state object, if any."""
    if not isinstance(state, dict):
        return None
    kind = state.get("sim_or_real")
    if kind:
        return str(kind)
    nested = state.get("provenance")
    if isinstance(nested, dict) and nested.get("kind"):
        return str(nested["kind"])
    return None


def _owner_provenance_kind(owner):
    """Return one record owner's state/top-level provenance label."""
    if not isinstance(owner, dict):
        return None
    kind = _state_provenance_kind(owner.get("state"))
    if kind:
        return kind
    provenance = owner.get("provenance")
    if isinstance(provenance, dict) and provenance.get("kind"):
        return str(provenance["kind"])
    return None


def _record_provenance_kind(record):
    """Resolve one mix label per record, including nested record shapes.

    Preference pairs are one training record, so equal labels on both sides
    count once. A partial or conflicting pair stays unlabeled instead of being
    guessed from one side. Bridge trajectories likewise take precedence over
    a wrapper's generic top-level ``unknown`` promotion stamp.
    """
    if not isinstance(record, dict):
        return None

    state_kind = _state_provenance_kind(record.get("state"))
    if state_kind:
        return state_kind

    if "chosen" in record or "rejected" in record:
        chosen = _owner_provenance_kind(record.get("chosen"))
        rejected = _owner_provenance_kind(record.get("rejected"))
        if chosen and rejected and chosen == rejected:
            return chosen
        if chosen or rejected:
            return None

    view = record.get("language_view")
    trajectory = view.get("trajectory") if isinstance(view, dict) else None
    trajectory_kind = _owner_provenance_kind(trajectory)
    if trajectory_kind:
        return trajectory_kind

    provenance = record.get("provenance")
    provenance_kind = None
    if isinstance(provenance, dict) and provenance.get("kind"):
        provenance_kind = str(provenance["kind"])
    meta = record.get("meta")
    if isinstance(meta, dict):
        factory = meta.get("factory")
        if (
            isinstance(factory, str)
            and factory.strip()
            and provenance_kind in (None, "unknown")
        ):
            # This repository is itself a synthetic-data factory. Stateless
            # episode/swarm records still carry their generation origin even
            # though they have no state.sim_or_real field to normalize.
            return "designed"
    return provenance_kind


def _embedding_duplicates(records, threshold, max_pairs):
    """Cluster ``records`` by cosine similarity and return the excluded ones.

    ``records`` are the survivors of exact-hash dedup, in scan order, each
    carrying the term counts computed during the scan. Those counts are
    **consumed**: each record's ``tokens`` is released as soon as its vector
    exists, so a large tree never holds both representations at once. Returns
    ``(duplicates, clusters, stats)``; the first member of every cluster is
    kept and the rest are reported as excluded with a reason.
    """
    stats = {
        "enabled": True,
        "encoder": EMBEDDING_ENCODER,
        "candidate_sketch": EMBEDDING_CANDIDATE_SKETCH,
        "threshold": threshold,
        "compared_records": 0,
        "candidate_pairs": 0,
        "truncated": False,
    }
    # A record whose semantic view holds no features at all
    # cannot be embedded; exact-hash dedup already covers that case.
    embeddable = [index for index, record in enumerate(records) if record["tokens"]]
    if len(embeddable) < 2:
        stats["compared_records"] = len(embeddable)
        return [], [], stats

    document_freq = Counter()
    for index in embeddable:
        document_freq.update(records[index]["tokens"].keys())
    population = len(embeddable)
    idf = {
        token: math.log((population + 1) / (count + 1)) + 1.0
        for token, count in document_freq.items()
    }
    del document_freq

    vectors = {}
    signatures = []
    for index in embeddable:
        record = records[index]
        vector = _tfidf_vector(record["tokens"], idf)
        record["tokens"] = None  # the term counts are not needed again
        if vector is None:
            continue
        vectors[index] = vector
        signature = _minhash_signature(candidate_sketch_features(vector))
        if signature is not None:
            signatures.append((index, signature))
    stats["compared_records"] = len(vectors)

    pairs, truncated = _candidate_pairs(signatures, max_pairs)
    stats["candidate_pairs"] = len(pairs)
    stats["truncated"] = truncated

    union = _Union()
    best_match = {}
    for left, right in pairs:
        similarity = _cosine(vectors[left], vectors[right])
        if similarity <= threshold:
            continue
        union.union(left, right)
        for index, other in ((left, right), (right, left)):
            current = best_match.get(index)
            if current is None or similarity > current[0]:
                best_match[index] = (similarity, other)

    duplicates = []
    clusters = []
    for members in union.groups():
        keeper = records[members[0]]
        # ``union`` is updated only for an accepted pair, and that same branch
        # writes ``best_match`` for both endpoints. Therefore every member of
        # every multi-record union group has at least one accepted match.
        cluster_similarity = max(best_match[index][0] for index in members)
        clusters.append(
            {
                "kind": "embedding",
                "size": len(members),
                "threshold": threshold,
                "encoder": EMBEDDING_ENCODER,
                "max_similarity": round(cluster_similarity, 6),
                "representative": _where(keeper),
                "members": [_where(records[index]) for index in members],
                "reason": (
                    f"{len(members) - 1} excluded record(s) linked by cosine > "
                    f"{threshold}; representative {keeper['file']}:{keeper['line']} "
                    "is retained"
                ),
            }
        )
        for index in members[1:]:
            similarity, other = best_match[index]
            match = records[other]
            representative = _where(keeper)
            matched_with = _where(match)
            if other == members[0]:
                relationship = (
                    f"vs retained representative {keeper['file']}:{keeper['line']}"
                )
            else:
                relationship = (
                    f"vs cluster member {match['file']}:{match['line']}; retained "
                    f"representative is {keeper['file']}:{keeper['line']}"
                )
            duplicates.append(
                {
                    "file": records[index]["file"],
                    "line": records[index]["line"],
                    "kind": "embedding",
                    "similarity": round(similarity, 6),
                    "duplicate_of": representative,
                    "matched_with": matched_with,
                    "reason": (
                        f"embedding near-duplicate: cosine {similarity:.4f} > "
                        f"{threshold} {relationship} "
                        f"(encoder {EMBEDDING_ENCODER})"
                    ),
                }
            )
    duplicates.sort(key=lambda entry: (entry["file"], entry["line"]))
    return duplicates, clusters, stats


def audit_run(
    run_dir: Path,
    threshold: float = DEFAULT_EMBEDDING_THRESHOLD,
    mix_policy: Optional[MixPolicy] = None,
    embedding_dedup: bool = True,
    max_embedding_pairs: int = DEFAULT_MAX_EMBEDDING_PAIRS,
):
    """Audit a run directory for duplicates and mix.

    Args:
        run_dir: directory to recurse for ``*.jsonl``.
        threshold: cosine-similarity threshold for embedding dedup. Pairs
            strictly above it are near-duplicates; the value is recorded in
            ``result['threshold']`` for provenance.
        mix_policy: blocking synthetic/real policy. Defaults to ~30/70 with
            0.20 tolerance (``MixPolicy()``).
        embedding_dedup: run the embedding near-duplicate pass. Exact-hash
            dedup is unconditional.
        max_embedding_pairs: safety cap on LSH candidate pairs.

    Returns:
        dict with ``counts``, ``mix``, ``mix_policy``, ``duplicates``,
        ``duplicate_clusters``, ``embedding``, ``reward_shapes``, ``errors``,
        ``warnings``, ``blockers``, ``blocked``, ``threshold``.
    """
    if not math.isfinite(threshold) or not -1.0 <= threshold < 1.0:
        raise ValueError(
            f"threshold must be a finite cosine in [-1, 1), got {threshold!r}"
        )
    if max_embedding_pairs < 1:
        raise ValueError(f"max_embedding_pairs must be >= 1, got {max_embedding_pairs!r}")
    policy = (mix_policy or MixPolicy()).validate()
    run_dir = Path(run_dir)
    if not run_dir.is_dir():
        raise ValueError(f"run directory does not exist or is not a directory: {run_dir}")
    hashes = Counter()
    first_seen = {}
    provenance = Counter()
    reward_keys = Counter()
    reward_shapes = Counter()
    records_with_rewards = 0
    total = 0
    kept = []
    duplicates = []
    exact_clusters = defaultdict(list)
    unreadable_files = 0
    malformed_lines = 0
    unreadable_examples = []
    malformed_examples = []
    for path in sorted(run_dir.rglob("*.jsonl")):
        rel = path.relative_to(run_dir)
        try:
            # JSONL is UTF-8 by contract; never fall back to the locale encoding.
            lines = path.read_text(encoding="utf-8").splitlines()
        except (OSError, UnicodeDecodeError) as exc:
            unreadable_files += 1
            if len(unreadable_examples) < MAX_ERROR_EXAMPLES:
                unreadable_examples.append(
                    {"file": str(rel), "error": f"{type(exc).__name__}: {exc}"}
                )
            continue
        for lineno, line in enumerate(lines, 1):
            if not line.strip():
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError as exc:
                malformed_lines += 1
                if len(malformed_examples) < MAX_ERROR_EXAMPLES:
                    malformed_examples.append(
                        {"file": str(rel), "line": lineno, "error": str(exc)}
                    )
                continue
            total += 1
            where = {"file": str(rel), "line": lineno}
            h = record_hash(obj)
            hashes[h] += 1
            exact_clusters[h].append(where)
            if hashes[h] > 1:
                origin = first_seen[h]
                duplicates.append(
                    {
                        **where,
                        "hash": h,
                        "kind": "exact",
                        "duplicate_of": dict(origin),
                        "reason": (
                            f"exact content hash {h} already seen at "
                            f"{origin['file']}:{origin['line']}"
                        ),
                    }
                )
            else:
                first_seen[h] = where
                if embedding_dedup:
                    # Tokenize now and drop the parsed record: the term counts
                    # are all the embedding pass needs, so a large tree never
                    # holds both the corpus and its encodings at once.
                    kept.append({**where, "tokens": embedding_tokens(obj)})
            # Count one provenance label per record. Nested preference and
            # bridge shapes are resolved before generic wrapper provenance.
            prov = _record_provenance_kind(obj)
            if prov:
                provenance[prov] += 1
            # Reward-shape entropy is reported, never blocked on, and never
            # aggregated across magnitudes (issue #5 owns the ontology fix).
            seen_reward = False
            for _reward_path, reward in walk_key(obj, "reward_components"):
                seen_reward = True
                if isinstance(reward, dict):
                    reward_keys.update(str(key) for key in reward)
                reward_shapes[reward_shape(reward)] += 1
            records_with_rewards += int(seen_reward)

    embedding_stats = {
        "enabled": False,
        "encoder": EMBEDDING_ENCODER,
        "candidate_sketch": EMBEDDING_CANDIDATE_SKETCH,
        "threshold": threshold,
        "compared_records": 0,
        "candidate_pairs": 0,
        "truncated": False,
    }
    embedding_duplicates = []
    embedding_clusters = []
    if embedding_dedup:
        embedding_duplicates, embedding_clusters, embedding_stats = _embedding_duplicates(
            kept, threshold, max_embedding_pairs
        )
    exact_duplicate_count = len(duplicates)
    duplicates.extend(embedding_duplicates)

    duplicate_clusters = [
        {
            "kind": "exact",
            "hash": digest,
            "size": len(members),
            "representative": dict(members[0]),
            "members": [dict(member) for member in members],
            "reason": f"{len(members)} records share exact content hash {digest}",
        }
        for digest, members in exact_clusters.items()
        if len(members) > 1
    ]
    duplicate_clusters.extend(embedding_clusters)

    # Mix guidance: rephrased synthetic (designed/simulated/hil) vs real/unknown.
    # Records carrying no recognized provenance label are their own bucket —
    # folding them into real_unknown would assert "real" about unlabeled data.
    synthetic = sum(v for k, v in provenance.items() if k in SYNTHETIC_KINDS)
    real_unknown = sum(v for k, v in provenance.items() if k in REAL_KINDS)
    unlabeled = total - synthetic - real_unknown
    labeled = synthetic + real_unknown
    mix = {
        "synthetic": synthetic,
        "real_unknown": real_unknown,
        "unlabeled": unlabeled,
        "total": total,
        "provenance": dict(provenance),
        "synthetic_ratio": synthetic / total if total else 0.0,
        "unlabeled_ratio": unlabeled / total if total else 0.0,
        # Reported, never enforced: an unlabeled-heavy corpus makes this ratio
        # loud and the enforced (total-denominator) one quiet.
        "labeled_synthetic_ratio": synthetic / labeled if labeled else 0.0,
    }

    errors = {
        "unreadable_files": unreadable_files,
        "malformed_lines": malformed_lines,
        "unreadable_examples": unreadable_examples,
        "malformed_examples": malformed_examples,
    }

    # Gate: fail on any duplicate (exact or embedding), any unparseable input,
    # or a synthetic/real mix outside policy. Skipped files/lines are not
    # covered by any count above, so a run containing them cannot pass clean.
    blockers = []
    warnings = []
    if exact_duplicate_count:
        blockers.append(
            f"{exact_duplicate_count} exact-hash duplicate record(s) must be excluded"
        )
    if embedding_duplicates:
        blockers.append(
            f"{len(embedding_duplicates)} embedding near-duplicate record(s) "
            f"(cosine > {threshold}) must be excluded"
        )
    if unreadable_files:
        blockers.append(f"{unreadable_files} file(s) unreadable/undecodable")
        warnings.append(f"{unreadable_files} file(s) unreadable/undecodable — counts, mix and dedup cover only the readable subset")
    if malformed_lines:
        blockers.append(f"{malformed_lines} malformed JSON line(s)")
        warnings.append(f"{malformed_lines} malformed JSON line(s) skipped — counts, mix and dedup cover only the parseable subset")
    ratio = mix["synthetic_ratio"]
    if total:
        if ratio > policy.ceiling:
            blockers.append(
                f"synthetic_ratio {ratio:.2f} > {policy.ceiling:.2f} — mix policy is "
                f"~{policy.target:.2f} synthetic / {1 - policy.target:.2f} real "
                f"(Demystifying Synthetic Data), tolerance {policy.tolerance:.2f}"
            )
        elif ratio > policy.target:
            warnings.append(
                f"synthetic_ratio {ratio:.2f} > target {policy.target:.2f} but within "
                f"the blocking ceiling {policy.ceiling:.2f} — SOTA recommends "
                f"~{policy.target:.2f} synthetic / {1 - policy.target:.2f} real "
                "(Demystifying Synthetic Data)"
            )
        if (
            policy.max_unlabeled_ratio is not None
            and mix["unlabeled_ratio"] > policy.max_unlabeled_ratio
        ):
            blockers.append(
                f"unlabeled_ratio {mix['unlabeled_ratio']:.2f} > "
                f"{policy.max_unlabeled_ratio:.2f} — mix cannot be enforced on "
                "unlabeled data"
            )
        elif mix["unlabeled_ratio"] > 0.5:
            warnings.append(
                f"unlabeled_ratio {mix['unlabeled_ratio']:.2f} — the enforced "
                "synthetic_ratio understates the real synthetic share"
            )
    if policy.min_synthetic_ratio is not None and ratio < policy.min_synthetic_ratio:
        blockers.append(
            f"synthetic_ratio {ratio:.2f} < floor {policy.min_synthetic_ratio:.2f}"
        )
    if embedding_stats["truncated"]:
        blockers.append(
            f"embedding candidate cap {max_embedding_pairs} reached — near-duplicate "
            "recall is partial, so this run cannot be certified"
        )
    if not embedding_dedup:
        warnings.append(
            "embedding dedup disabled — only exact-hash duplicates were excluded"
        )

    return {"counts": {"total": total, "unique_hashes": len(hashes),
                       "duplicate_groups": len([h for h, c in hashes.items() if c > 1]),
                       "embedding_duplicate_groups": len(embedding_clusters),
                       "excluded_records": len(duplicates),
                       "unreadable_files": unreadable_files,
                       "malformed_lines": malformed_lines},
            "mix": mix, "mix_policy": policy.as_dict(), "duplicates": duplicates,
            "duplicate_clusters": duplicate_clusters, "embedding": embedding_stats,
            "reward_shapes": {
                "records_with_reward_components": records_with_rewards,
                "unique_component_keys": len(reward_keys),
                "unique_shapes": len(reward_shapes),
                "top_component_keys": reward_keys.most_common(20),
                "top_shapes": reward_shapes.most_common(10),
            },
            "errors": errors, "warnings": warnings, "blockers": blockers,
            "blocked": bool(blockers), "threshold": threshold}


def validate_manifest_target(path, run_dir, *, allow_within_run=False):
    """Validate that a manifest target cannot overwrite audited evidence."""
    path = Path(path)
    run_dir = Path(run_dir)
    resolved_path = path.resolve()
    resolved_run = run_dir.resolve()
    if path.suffix.lower() == ".jsonl":
        raise ValueError(f"manifest path must not be a JSONL input: {path}")
    if path.exists() or path.is_symlink():
        raise ValueError(f"refusing to overwrite existing manifest path: {path}")
    if allow_within_run and (
        resolved_path == resolved_run or resolved_path in resolved_run.parents
    ):
        raise ValueError(
            "manifest path must not equal or contain the promotion destination: "
            f"{path}"
        )
    if (
        not allow_within_run
        and (resolved_path == resolved_run or resolved_run in resolved_path.parents)
    ):
        raise ValueError(
            f"manifest path must be outside the audited run directory: {path}"
        )
    return path


def write_manifest(path, run_dir, result, *, allow_within_run=False):
    """Create the curated sidecar manifest without overwriting any path."""
    path = validate_manifest_target(
        path, run_dir, allow_within_run=allow_within_run
    )
    manifest = {
        "schema": "quality-manifest/1",
        "generated_by": "pipelines/quality_gate.py",
        "run_dir": str(run_dir),
        **result,
    }
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("x", encoding="utf-8") as handle:
            handle.write(json.dumps(manifest, indent=2) + "\n")
    except OSError as exc:
        raise ValueError(
            f"could not create manifest {path}: {type(exc).__name__}: {exc}"
        ) from exc
    return path


def main(argv=None):
    p = argparse.ArgumentParser(description="Quality gate — dedup + mix enforcement")
    p.add_argument("run_dir", help="run directory")
    p.add_argument("--json", action="store_true", help="emit JSON")
    p.add_argument(
        "--threshold",
        type=float,
        default=DEFAULT_EMBEDDING_THRESHOLD,
        help=(
            "cosine-similarity threshold for embedding near-duplicate exclusion "
            "in [-1, 1) (default: %(default)s). Pairs strictly above it are excluded and "
            "block the gate. See module docstring and docs/quality-gate.md for "
            "tuning guidance."
        ),
    )
    p.add_argument(
        "--no-embedding-dedup",
        dest="embedding_dedup",
        action="store_false",
        help="skip the embedding near-duplicate pass (exact-hash dedup still runs)",
    )
    p.add_argument(
        "--max-embedding-pairs",
        type=int,
        default=DEFAULT_MAX_EMBEDDING_PAIRS,
        help=(
            "blocking cap on LSH candidate pairs; observing an omitted pair "
            "fails closed (default: %(default)s)"
        ),
    )
    p.add_argument(
        "--mix-target",
        type=float,
        default=DEFAULT_TARGET_SYNTHETIC_RATIO,
        help="target synthetic share (default: %(default)s, i.e. ~30/70)",
    )
    p.add_argument(
        "--mix-tolerance",
        type=float,
        default=DEFAULT_MIX_TOLERANCE,
        help="slack above the target before the gate blocks (default: %(default)s)",
    )
    p.add_argument(
        "--max-synthetic-ratio",
        type=float,
        default=None,
        help="explicit blocking ceiling; overrides --mix-target + --mix-tolerance",
    )
    p.add_argument(
        "--min-synthetic-ratio",
        type=float,
        default=None,
        help="optional blocking floor on the synthetic share (default: no floor)",
    )
    p.add_argument(
        "--max-unlabeled-ratio",
        type=float,
        default=None,
        help=(
            "optional blocking ceiling on records with no recognized provenance "
            "label (default: warn only, above 0.5)"
        ),
    )
    p.add_argument(
        "--manifest",
        default=None,
        help=(
            "write the curated sidecar manifest (mix report + duplicate clusters) "
            "to this path"
        ),
    )
    args = p.parse_args(argv)
    policy = MixPolicy(
        target=args.mix_target,
        tolerance=args.mix_tolerance,
        max_synthetic_ratio=args.max_synthetic_ratio,
        min_synthetic_ratio=args.min_synthetic_ratio,
        max_unlabeled_ratio=args.max_unlabeled_ratio,
    )
    run_dir = Path(args.run_dir)
    written = None
    try:
        if args.manifest:
            validate_manifest_target(args.manifest, run_dir)
        result = audit_run(
            run_dir,
            threshold=args.threshold,
            mix_policy=policy,
            embedding_dedup=args.embedding_dedup,
            max_embedding_pairs=args.max_embedding_pairs,
        )
        if args.manifest:
            written = write_manifest(args.manifest, run_dir, result)
    except ValueError as exc:
        p.error(str(exc))  # exits 2
    if written is not None:
        print(f"MANIFEST: {written}", file=sys.stderr)
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(json.dumps({"counts": result["counts"], "mix": result["mix"],
                          "mix_policy": result["mix_policy"],
                          "embedding": result["embedding"],
                          "reward_shapes": {k: v for k, v in result["reward_shapes"].items()
                                            if not k.startswith("top_")},
                          "blocked": result["blocked"],
                          "threshold": result["threshold"]}, indent=2))
        for b in result["blockers"]:
            print(f"BLOCKED: {b}", file=sys.stderr)
        for w in result["warnings"]:
            print(f"WARN: {w}", file=sys.stderr)
        for d in result["duplicates"]:
            print(f"DUPLICATE: {d['file']}:{d['line']} ({d['reason']})", file=sys.stderr)
        for e in result["errors"]["unreadable_examples"]:
            print(f"UNREADABLE: {e['file']} ({e['error']})", file=sys.stderr)
        for e in result["errors"]["malformed_examples"]:
            print(f"MALFORMED: {e['file']}:{e['line']} ({e['error']})", file=sys.stderr)
    sys.exit(1 if result["blocked"] else 0)


if __name__ == "__main__":
    main()
