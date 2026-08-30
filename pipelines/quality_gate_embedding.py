#!/usr/bin/env python3
"""Deterministic lexical embedding and near-duplicate clustering.

This module owns only the semantic embedding layer of the quality gate.  The
exact-identity projection remains in :mod:`quality_gate_identity`, which keeps
the dependency direction one-way and lets ``quality_gate`` remain a small
compatibility facade.
"""

from __future__ import annotations

import hashlib
import itertools
import math
import unicodedata
from collections import Counter, defaultdict
from dataclasses import dataclass, field

from quality_gate_identity import canonical_blob, semantic_similarity_view


DEFAULT_EMBEDDING_THRESHOLD: float = 0.97
"""Default cosine-similarity threshold for embedding deduplication."""

EMBEDDING_ENCODER = "lexical-tfidf/7"
"""Versioned identifier for the deterministic semantic encoder."""

EMBEDDING_MINHASH_SLOTS = 32
EMBEDDING_LSH_BANDS = 8
EMBEDDING_MIN_THRESHOLD: float = (1.0 / EMBEDDING_LSH_BANDS) ** (
    EMBEDDING_LSH_BANDS / EMBEDDING_MINHASH_SLOTS
)
EMBEDDING_CANDIDATE_SKETCH = "weighted-tier-minhash/1"
EMBEDDING_SKETCH_LEVELS = 64
DEFAULT_MAX_EMBEDDING_PAIRS = 2_000_000

_BIGRAM_SEP = "\x00"
_ORDER_MARK = "\x02"
_PATH_SEP = "\x1f"
_SKETCH_SEP = "\x1e"
_GAP_SEP = "\x1d"

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


def validate_embedding_threshold(threshold: float) -> float:
    """Return a sound threshold, or reject values below the LSH recall bound."""
    if math.isfinite(threshold) and EMBEDDING_MIN_THRESHOLD <= threshold < 1.0:
        return threshold
    raise ValueError(
        "threshold must be a finite cosine in "
        f"[{EMBEDDING_MIN_THRESHOLD:.4f}, 1), got {threshold!r}"
    )


def _element_digest(value) -> str:
    """Return a short stable digest for one complete list element."""
    blob = canonical_blob(value)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:8]


def _path_child(path: str, key) -> str:
    """Return an unambiguous JSON-pointer-like child path."""
    escaped = str(key).replace("~", "~0").replace("/", "~1")
    return f"{path}/k:{escaped}"


def _uses_unsegmented_script(word: str) -> bool:
    """Whether ``word`` needs the grapheme fallback used for unspaced text."""
    return any(
        marker in unicodedata.name(char, "")
        for char in word
        for marker in _UNSEGMENTED_SCRIPT_MARKERS
    )


def _graphemes(word: str) -> list[str]:
    """Return a stdlib-only approximation of extended grapheme clusters."""
    clusters: list[str] = []
    for char in word:
        if unicodedata.category(char).startswith("M") and clusters:
            clusters[-1] += char
        else:
            clusters.append(char)
    return clusters


def _character_unit_kind(char: str, active_kind: str | None) -> str:
    """Classify one character for the ordered string-unit scanner."""
    if char.isspace():
        return "space"
    category = unicodedata.category(char)
    if char == "_" or char.isalnum():
        return "word"
    if category.startswith("M") and active_kind == "word":
        return "word"
    return "operator"


@dataclass
class _StringScan:
    active_kind: str | None = None
    active_chars: list[str] = field(default_factory=list)
    active_gap: str = ""
    pending_gap: str = ""


def _flush_string_scan(state):
    if not state.active_chars:
        return ()
    unit = (state.active_kind, "".join(state.active_chars), state.active_gap)
    state.active_kind = None
    state.active_chars.clear()
    state.active_gap = ""
    return (unit,)


def _consume_string_char(state, char):
    kind = _character_unit_kind(char, state.active_kind)
    if kind == "space":
        emitted = _flush_string_scan(state)
        state.pending_gap += char
        return emitted
    emitted = ()
    if state.active_kind != kind:
        emitted = _flush_string_scan(state)
        state.active_kind = kind
        state.active_gap, state.pending_gap = state.pending_gap, ""
    state.active_chars.append(char)
    return emitted


def _string_units(text: str):
    """Yield ordered ``(kind, unit, preceding_gap)`` triples.

    Whitespace rides on the following unit.  This preserves exact gaps without
    breaking the word-to-word bigram chain that carries prose and code order.
    """
    state = _StringScan()
    for char in unicodedata.normalize("NFC", text):
        yield from _consume_string_char(state, char)
    yield from _flush_string_scan(state)


def _unsegmented_features(path: str, unit: str, gap: str) -> list[str]:
    """Return recall-friendly graphemes plus one order-sensitive whole unit."""
    features = [f"{path}{_PATH_SEP}str-char:{cluster}" for cluster in _graphemes(unit)]
    features.append(f"{path}{_PATH_SEP}str-seq:{unit}{_GAP_SEP}{gap}")
    return features


def _string_unit_features(path: str, kind: str, unit: str, gap: str) -> list[str]:
    """Encode one scanned string unit without erasing case or operators."""
    if kind == "operator":
        return [f"{path}{_PATH_SEP}str-op:{unit}{_GAP_SEP}{gap}"]
    if _uses_unsegmented_script(unit):
        return _unsegmented_features(path, unit, gap)
    return [
        f"{path}{_PATH_SEP}str-fold:{unit.casefold()}{_GAP_SEP}{gap}",
        f"{path}{_PATH_SEP}str-case:{unit}{_GAP_SEP}{gap}",
    ]


def _append_string_features(text: str, out: list[str], path: str) -> None:
    """Append all semantic features for a string leaf."""
    normalized = unicodedata.normalize("NFC", text)
    if not normalized:
        out.append(f"{path}{_PATH_SEP}str-empty")
        return
    emitted = False
    for kind, unit, gap in _string_units(normalized):
        emitted = True
        out.extend(_string_unit_features(path, kind, unit, gap))
    if not emitted:
        out.append(f"{path}{_PATH_SEP}str-whitespace")


def _scalar_feature(value) -> str | None:
    """Return the typed feature suffix for a non-string scalar."""
    if value is None:
        return "null"
    if isinstance(value, bool):
        return f"bool:{'true' if value else 'false'}"
    if isinstance(value, int):
        return f"int:{value}"
    if isinstance(value, float):
        return f"float:{value!r}"
    return None


def _append_mapping_features(value: dict, out: list[str], path: str) -> None:
    """Traverse a mapping in canonical key order."""
    if not value:
        out.append(f"{path}{_PATH_SEP}dict-empty")
        return
    for key in sorted(value):
        _leaf_words(value[key], out, _path_child(path, key))


def _adjacent_digest_features(path: str, digests: list[str]):
    """Yield stable directed edges for every adjacent list-element pair."""
    for left, right in itertools.pairwise(digests):
        yield f"{_ORDER_MARK}{path}{_PATH_SEP}adj:{left}>{right}"


def _append_sequence_features(value, out: list[str], path: str) -> None:
    """Encode list content, directed adjacency, and ambiguous repetitions."""
    if not value:
        out.append(f"{path}{_PATH_SEP}list-empty")
        return
    digests = [_element_digest(item) for item in value]
    out.extend(_adjacent_digest_features(path, digests))
    repeated = len(set(digests)) != len(digests)
    for index, (item, digest) in enumerate(zip(value, digests)):
        if repeated:
            out.append(f"{_ORDER_MARK}{path}{_PATH_SEP}pos:{index}:{digest}")
        _leaf_words(item, out, f"{path}/i")


def _leaf_words(value, out: list[str], path: str = "$") -> None:
    """Collect canonical, path-qualified features from semantic leaf values."""
    if isinstance(value, dict):
        _append_mapping_features(value, out, path)
        return
    if isinstance(value, (list, tuple)):
        _append_sequence_features(value, out, path)
        return
    if isinstance(value, str):
        _append_string_features(value, out, path)
        return
    feature = _scalar_feature(value)
    if feature is not None:
        out.append(f"{path}{_PATH_SEP}{feature}")


def embedding_tokens(obj) -> Counter:
    """Return term counts (unigrams plus order-preserving bigrams)."""
    words: list[str] = []
    _leaf_words(semantic_similarity_view(obj), words)
    tokens = Counter(words)
    chain = [word for word in words if not word.startswith(_ORDER_MARK)]
    tokens.update(
        f"{first}{_BIGRAM_SEP}{second}"
        for first, second in itertools.pairwise(chain)
    )
    return tokens


def _tfidf_vector(tokens, idf):
    """Return an L2-normalized sublinear TF-IDF vector."""
    vector = {
        token: (1.0 + math.log(count)) * idf[token]
        for token, count in tokens.items()
        if idf[token]
    }
    norm = math.sqrt(sum(weight * weight for weight in vector.values()))
    if not norm:
        return None
    return {token: weight / norm for token, weight in vector.items()}


def candidate_sketch_features(vector):
    """Yield deterministic frequency-aware tiers for candidate recall."""
    for token in sorted(vector):
        tiers = max(1, math.ceil(vector[token] * EMBEDDING_SKETCH_LEVELS))
        for tier in range(tiers):
            yield f"{token}{_SKETCH_SEP}{tier}"


def _cosine(left, right) -> float:
    """Return the bounded dot product of two normalized sparse vectors."""
    if len(left) > len(right):
        left, right = right, left
    total = sum(weight * right[token] for token, weight in left.items() if token in right)
    return min(1.0, max(-1.0, total))


def _minhash_bin(token: str) -> tuple[int, int]:
    """Return the one-permutation slot and value for one sketch token."""
    digest = int.from_bytes(
        hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest(), "big"
    )
    return digest % EMBEDDING_MINHASH_SLOTS, digest // EMBEDDING_MINHASH_SLOTS


def _occupied_minhash_bins(tokens) -> list[int | None]:
    """Build the sparse one-permutation sketch before densification."""
    bins: list[int | None] = [None] * EMBEDDING_MINHASH_SLOTS
    for token in tokens:
        slot, value = _minhash_bin(token)
        current = bins[slot]
        if current is None or value < current:
            bins[slot] = value
    return bins


def _next_occupied_value(bins: tuple[int | None, ...], slot: int) -> int:
    """Rotate from an empty slot to the next original occupied slot."""
    slots = len(bins)
    return next(
        value
        for step in range(1, slots)
        if (value := bins[(slot + step) % slots]) is not None
    )


def _densify_minhash_bins(bins: list[int | None]) -> tuple[int, ...]:
    """Fill empty bins from the immutable pre-densification sketch."""
    occupied = tuple(bins)
    return tuple(
        value if value is not None else _next_occupied_value(occupied, slot)
        for slot, value in enumerate(occupied)
    )


def _minhash_signature(tokens):
    """Return a deterministic one-permutation MinHash signature."""
    bins = _occupied_minhash_bins(tokens)
    if not any(value is not None for value in bins):
        return None
    return _densify_minhash_bins(bins)


def _lsh_buckets(signatures):
    """Group record indices by equal MinHash bands."""
    rows = EMBEDDING_MINHASH_SLOTS // EMBEDDING_LSH_BANDS
    buckets = defaultdict(list)
    for index, signature in signatures:
        for band in range(EMBEDDING_LSH_BANDS):
            start = band * rows
            buckets[(band, signature[start: start + rows])].append(index)
    return buckets


def _distinct_bucket_pairs(buckets):
    """Yield each pair nominated by one or more LSH buckets exactly once."""
    seen = set()
    for members in buckets.values():
        for pair in itertools.combinations(members, 2):
            if pair not in seen:
                seen.add(pair)
                yield pair


def _candidate_pairs(signatures, max_pairs):
    """Return deterministic candidate pairs and whether an extra pair was cut."""
    pairs = []
    for pair in _distinct_bucket_pairs(_lsh_buckets(signatures)):
        if len(pairs) >= max_pairs:
            return sorted(pairs), True
        pairs.append(pair)
    return sorted(pairs), False


class _Union:
    """Union-find over record indices, used to group accepted pairs."""

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

    def union(self, left, right) -> None:
        left_root, right_root = self.find(left), self.find(right)
        if left_root != right_root:
            low, high = sorted((left_root, right_root))
            self.parent[high] = low

    def groups(self):
        clusters = defaultdict(list)
        for item in sorted(self.parent):
            clusters[self.find(item)].append(item)
        return [members for _, members in sorted(clusters.items()) if len(members) > 1]


def _where(record) -> dict:
    return {"file": record["file"], "line": record["line"]}


def _embedding_stats(threshold: float) -> dict:
    """Return the initial report shape for one embedding pass."""
    return {
        "enabled": True,
        "encoder": EMBEDDING_ENCODER,
        "candidate_sketch": EMBEDDING_CANDIDATE_SKETCH,
        "threshold": threshold,
        "compared_records": 0,
        "candidate_pairs": 0,
        "truncated": False,
    }


def _corpus_idf(records, indices) -> dict:
    """Build one document-frequency map over all embeddable records."""
    document_freq = Counter()
    for index in indices:
        document_freq.update(records[index]["tokens"].keys())
    population = len(indices)
    return {
        token: math.log((population + 1) / (count + 1)) + 1.0
        for token, count in document_freq.items()
    }


def _vectors_and_signatures(records, indices, idf):
    """Consume token counters and return exact vectors plus LSH signatures."""
    vectors = {}
    signatures = []
    for index in indices:
        record = records[index]
        vector = _tfidf_vector(record["tokens"], idf)
        record["tokens"] = None
        if vector is None:
            continue
        vectors[index] = vector
        signature = _minhash_signature(candidate_sketch_features(vector))
        if signature is not None:
            signatures.append((index, signature))
    return vectors, signatures


def _remember_best_match(best_match, index, other, similarity) -> None:
    """Keep the strongest deterministic accepted neighbor for one record."""
    current = best_match.get(index)
    if current is None or similarity > current[0]:
        best_match[index] = similarity, other


def _accepted_pair_graph(vectors, pairs, threshold):
    """Return union groups and strongest neighbors for accepted candidates."""
    union = _Union()
    best_match = {}
    for left, right in pairs:
        similarity = _cosine(vectors[left], vectors[right])
        if similarity <= threshold:
            continue
        union.union(left, right)
        _remember_best_match(best_match, left, right, similarity)
        _remember_best_match(best_match, right, left, similarity)
    return union, best_match


def _cluster_summary(records, members, best_match, threshold) -> dict:
    """Render one accepted connected component for the quality report."""
    keeper = records[members[0]]
    cluster_similarity = max(best_match[index][0] for index in members)
    return {
        "kind": "embedding",
        "size": len(members),
        "threshold": threshold,
        "encoder": EMBEDDING_ENCODER,
        "max_similarity": round(cluster_similarity, 6),
        "representative": _where(keeper),
        "members": [_where(records[index]) for index in members],
        "reason": (
            f"{len(members) - 1} excluded record(s) linked by cosine > "
            f"{threshold}; representative {keeper['file']}:{keeper['line']} is retained"
        ),
    }


def _match_relationship(records, members, other) -> str:
    """Describe whether an excluded item matched the keeper or another member."""
    keeper = records[members[0]]
    if other == members[0]:
        return f"vs retained representative {keeper['file']}:{keeper['line']}"
    match = records[other]
    return (
        f"vs cluster member {match['file']}:{match['line']}; retained "
        f"representative is {keeper['file']}:{keeper['line']}"
    )


def _duplicate_entry(context, index) -> dict:
    """Render one excluded member of an embedding cluster."""
    records, members, best_match, threshold = context
    keeper = records[members[0]]
    similarity, other = best_match[index]
    match = records[other]
    return {
        "file": records[index]["file"],
        "line": records[index]["line"],
        "kind": "embedding",
        "similarity": round(similarity, 6),
        "duplicate_of": _where(keeper),
        "matched_with": _where(match),
        "reason": (
            f"embedding near-duplicate: cosine {similarity:.4f} > {threshold} "
            f"{_match_relationship(records, members, other)} "
            f"(encoder {EMBEDDING_ENCODER})"
        ),
    }


def _render_embedding_groups(records, union, best_match, threshold):
    """Render accepted components as duplicate and cluster report entries."""
    duplicates = []
    clusters = []
    for members in union.groups():
        clusters.append(_cluster_summary(records, members, best_match, threshold))
        context = records, members, best_match, threshold
        duplicates.extend(
            _duplicate_entry(context, index)
            for index in members[1:]
        )
    duplicates.sort(key=lambda entry: (entry["file"], entry["line"]))
    return duplicates, clusters


def _embedding_duplicates(records, threshold, max_pairs):
    """Cluster tokenized records by exact cosine after LSH nomination.

    Token counters are consumed as vectors are built.  The corpus-wide IDF map
    is explicitly released before candidate generation so it does not inflate
    peak memory during the pair phase.
    """
    stats = _embedding_stats(threshold)
    embeddable = [index for index, record in enumerate(records) if record["tokens"]]
    if len(embeddable) < 2:
        stats["compared_records"] = len(embeddable)
        return [], [], stats
    idf = _corpus_idf(records, embeddable)
    vectors, signatures = _vectors_and_signatures(records, embeddable, idf)
    stats["compared_records"] = len(vectors)
    del idf
    pairs, truncated = _candidate_pairs(signatures, max_pairs)
    stats["candidate_pairs"] = len(pairs)
    stats["truncated"] = truncated
    union, best_match = _accepted_pair_graph(vectors, pairs, threshold)
    duplicates, clusters = _render_embedding_groups(
        records, union, best_match, threshold
    )
    return duplicates, clusters, stats
