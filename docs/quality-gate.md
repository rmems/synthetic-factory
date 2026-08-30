# Quality Gate — sf-xua

Dedup + synthetic/real mix enforcement before volume training. The gate is
the last check between ``pipelines/promote.py`` and any training run.

```text
raw JSONL (append-only SoT)
    │
    ▼
pipelines/promote.py  ──►  cleaned/<date>/   (provenance remapped, spike trains sorted)
    │                         │
    │                         └── quality-manifest.json
    ▼
pipelines/quality_gate.py (invoked automatically; standalone CLI also available)
    │
    ▼
blocked?  ──►  train / fix
```

Co-authored-by: Muse Code powered by Muse Spark <muse-spark@meta.com>

## What it checks

| Check | Signal | Fail mode |
|---|---|---|
| **Exact-hash dedup** | SHA-256 over a canonical training-identity view: states, decisions, actions, outcomes and rewards (fallback: whole record) | ``blocked = true``, exit 1 |
| **Embedding dedup** | Cosine similarity over a separate semantic view with canonical record ids removed. Pairs above ``--threshold`` (default 0.97) are clustered; one member is kept, the rest are excluded with a ``reason`` | ``blocked = true``, exit 1 |
| **Synthetic/real mix** | Buckets ``provenance.kind`` / ``state.sim_or_real`` → synthetic ``{designed, simulated, hil}`` vs ``{real, unknown}`` vs ``unlabeled`` (no recognized label) | **Blocks** above the ceiling (default ``0.30 target + 0.20 tolerance = 0.50``); warns between target and ceiling |
| **Read/parse failures** | Files that cannot be read or UTF-8 decoded, and lines that are not valid JSON | Counted in ``errors`` with examples; ``blocked = true``, exit 1 |
| **Reward-shape entropy** | Distinct ``reward_components`` keys and structural shapes | **Report only.** Magnitudes are never mixed or aggregated — the ontology fix belongs to sf-c5l.4 |

Every reason the gate blocked is listed in ``blockers``; soft findings stay
in ``warnings``.

## Embedding dedup

### Definition

Every record that survives exact-hash dedup is embedded once by a shared
encoder and pairwise cosine similarity is computed. A pair is a
near-duplicate iff

```text
cosine_sim(a, b) > threshold
```

Near-duplicate pairs are merged into clusters (union-find). The
**first record in file/line order is the representative and is kept**;
every other cluster member appears in ``duplicates`` with
``kind="embedding"``, its ``similarity``, ``duplicate_of`` pointing to the
retained representative, ``matched_with`` identifying the scored edge that
put it in the cluster, and a human-readable ``reason``. Keeping those two
references separate matters for transitive clusters: C may match excluded B
even when retained A is below threshold. The cluster itself is emitted in
``duplicate_clusters``. Exact-hash duplicates use the same blocking semantics
with ``kind="exact"``.

Every ``duplicates`` entry still carries ``file``, ``line`` and
``reason``. ``hash`` appears only on ``kind="exact"`` entries and
``similarity`` only on ``kind="embedding"`` ones, so read ``kind``
first.

### Three deliberately separate representations

The gate does not reuse one lossy projection for three different jobs:

1. ``exact_identity_view`` preserves the fields that define a training unit.
   Preference actions and outcomes are included, while wrapper bookkeeping ids
   stay outside modeled state/action records. Per-factory supervision counts as
   modeled content: Thalamic ``spike_events``, the event-language bridge's
   ``language_view`` and ``raster``, and the safety-calibration ``case_type`` /
   ``rationale`` / ``decision`` labels are all part of the identity, so records
   that differ only there are distinct training units.
2. ``semantic_similarity_view`` removes canonical record identifiers such as
   ``id`` and ``episode_id``, plus root bookkeeping metadata, before lexical
   encoding. An id or round-stamp change cannot hide an otherwise identical
   training example.
3. ``candidate_sketch_features`` turns normalized TF-IDF weights into
   deterministic tiers for LSH recall. The exact cosine vector remains the
   only near-duplicate verdict.

### The shipped encoder

This repository is stdlib-only (see ``AGENTS.md``), so the encoder is
lexical, not learned:

- **``EMBEDDING_ENCODER = "lexical-tfidf/8"``** — TF-IDF over Unicode word
  unigrams *and* bigrams of every **path-qualified leaf value** in the
  semantic-similarity view. A feature combines the full field path with the leaf
  word, so shared schema alone contributes nothing while the same value under
  semantically different fields stays distinct. CJK, Japanese, Thai, Lao,
  Khmer and Myanmar runs use path-qualified grapheme tokens because those
  scripts do not reliably place spaces between words; adjacent-token bigrams
  allow small edits to share candidate features, and the whole run is also
  emitted as one ``str-seq:`` feature. That whole-run feature is what makes
  the encoder order-sensitive for these scripts: a grapheme bag plus adjacent
  bigrams is not injective over sequences, so ``甲乙甲丙甲`` and ``甲丙甲乙甲``
  otherwise scored cosine 1.0.
- **Whitespace is a boundary, not a token.** Each unit carries the exact
  whitespace run that preceded it, so indentation and ``https://safe /admin``
  versus ``https://safe/admin`` stay distinguishable. Emitting whitespace as
  its own token instead would place it between every pair of prose words, and
  the adjacent-token bigrams would then relate each word only to a shared
  separator — ``a b c d`` and ``a c b d`` would embed identically.
- Mapping keys are traversed in canonical sorted order before bigrams are
  formed. Equivalent JSON objects therefore embed identically regardless of
  insertion order. Every list carries directed adjacent-element full SHA-256
  digest features, so reversing distinct elements cannot preserve the
  embedding by sharing boundary words or a shortened-digest collision. Lists
  with repeated elements additionally carry explicit positions because their
  adjacency multisets can still be ambiguous. A leading insertion preserves
  the untouched adjacency edges instead of renumbering every later semantic
  leaf.
- Unicode tokenization preserves non-ASCII scripts instead of reducing two
  unrelated multilingual records to their shared ASCII metadata. Combining
  marks stay attached to their base grapheme, so Thai text is not fragmented
  by Python's narrower ``\w`` behavior.
- Numeric and Boolean scalars are atomic, typed features (for example,
  ``int:-5``, ``float:5.0`` and ``bool:true``). ``null``, empty strings, empty
  lists and empty objects have distinct typed sentinels. String words retain
  both folded and case-sensitive channels, and punctuation/operator runs are
  tokens, so ``User``/``user`` and ``<``/``>`` do not collapse.
- Sublinear term frequency (``1 + log tf``) times smoothed IDF
  (``log((N+1)/(df+1)) + 1``), L2-normalized, so the dot product **is**
  the cosine.
- No weights, no download, no randomness: two runs over the same tree
  produce byte-identical reports, which is what makes the gate usable as
  a required CI check.

The encoder id is recorded in the report and in every embedding cluster
so a corpus embedded by some other encoder is never compared against
these runs on threshold alone. Swapping in a learned encoder later means
bumping ``EMBEDDING_ENCODER`` and re-calibrating the threshold — the
report shape does not change.

Practical reading of 0.97 for this encoder: two records match when they
share ~97% of their weighted vocabulary, i.e. the difference is a handful
of tokens in a long narrative. That is the template-regurgitation /
temperature-collapse signature, not a genuine paraphrase.

### Candidate generation and cost

All-pairs cosine is quadratic, so candidates come from a **frequency-aware,
banded one-permutation MinHash sketch**
(``EMBEDDING_CANDIDATE_SKETCH = "weighted-tier-minhash/1"``;
``EMBEDDING_MINHASH_SLOTS = 32`` slots read as
``EMBEDDING_LSH_BANDS = 8`` bands of 4) and every candidate is then scored
with an exact cosine. Normalized TF-IDF weights expand into deterministic
tiers before one hash per sketch feature fills the sketch;
empty slots are densified by rotation, so no per-token permutation table
is ever held in memory. Consequences:

- **Precision is exact.** Nothing is excluded without a real cosine above
  the threshold.
- **Recall is approximate.** Weighted tiers prevent a dominant repeated term
  from collapsing to one set member; the committed regression includes a
  high-cosine pair whose unweighted token-set overlap is low, plus planted
  clones that differ in one field.
- ``--max-embedding-pairs`` (default 2,000,000) caps candidate pairs. The
  report sets ``embedding.truncated`` only after observing an additional
  distinct pair that would be omitted. Partial recall **blocks** the gate;
  producing exactly the cap remains complete and does not block.
- Cost is roughly linear in records: ~2s and ~270 MB over baseline for
  5,000 narrative records with an adversarially unique vocabulary. Peak
  memory holds one term-count map per retained record; parsed records are
  dropped as they are read and each term-count map is released as soon as
  its vector exists. ``--no-embedding-dedup`` skips the pass entirely and
  says so in ``warnings``; exact-hash dedup still runs.

### Default threshold: 0.97

- **Angular distance**: ``arccos(0.97) ≈ 14°``. Tight enough to keep
  legitimately similar domains separate.
- **Empirical separation** (factory corpus, held-out r06–r07):
  - Rephrased synthetic from the same prompt: 0.93–0.96
  - Distinct scenarios with overlapping boilerplate (e.g., dairy AMS SOP
    language): 0.85–0.92
  - Temperature-collapse / template regurgitation: 0.97–0.99+
- **Why 0.97**: highest threshold that still collapses known duplicate
  seeds (same seed, ``temp=0`` re-runs) in the calibration set, while
  keeping false-positive groups near zero on the overlapping-domain
  slice.
- The grapheme fallback leaves whitespace-delimited encoder behavior
  unchanged. Before promoting a new unsegmented-script corpus, extend the
  same held-out sweep with minimally edited and genuinely distinct records in
  that script; the committed Chinese/Japanese/Thai cases guard the failure
  mode, not every language's operating point.
- ``tests/fixtures/embedding-dedup/`` is the regression case: seven
  records, six distinct (max pairwise cosine 0.06) and one planted
  near-duplicate that differs only in ``state.tick`` — invisible to
  exact hashing and above 0.97 to the encoder.
- ``--threshold`` must be finite in ``[EMBEDDING_MIN_THRESHOLD, 1)``, which is
  about ``[0.5946, 1)``. The lower bound is the supported operating floor for
  this sketch: MinHash-LSH nomination degrades sharply below the banding
  scheme's S-curve knee, ``(1/bands) ** (1/rows)`` — about 0.59 for the shipped
  8 bands of 4. Recall remains approximate above the knee, as stated earlier;
  the floor prevents configurations that the sketch is especially unsuited to
  honor, but it is not a deterministic recall guarantee. A run that requires
  exhaustive enforcement needs an exhaustive comparator rather than this
  sketch. ``1.0`` is rejected instead of acting as a silent embedding-dedup
  disable switch; use the explicit ``--no-embedding-dedup`` flag when that is
  truly intended.

### Tuning

Sweep ``0.93 / 0.95 / 0.97 / 0.98`` on a held-out factory slice:

1. Run the gate at each candidate and collect duplicate clusters.
2. Score recall on injected duplicate seeds and precision on the
   overlapping-domain slice.
3. Pick the **highest** threshold with recall ≥ 0.99 on the seeds.
4. Record the chosen value in the run's ``quality_report`` and pass it
   explicitly (``--threshold <value>``) so CI is pinned, not floating.

Lower thresholds (0.93–0.95) catch looser paraphrases but flag more
false positives on shared boilerplate. Higher thresholds (0.98–0.99)
reduce false positives further but miss template-level collapse that
still harms diversity.

### Constants

- Default is exported by ``pipelines/quality_gate.py`` as
  ``DEFAULT_EMBEDDING_THRESHOLD``.
  Downstream embedding stages should ``from quality_gate import
  DEFAULT_EMBEDDING_THRESHOLD`` rather than re-defining the value.
- CLI override: ``--threshold <float>`` (e.g., ``--threshold 0.95``).
  The chosen value is echoed in the JSON output as ``threshold`` and on
  every embedding cluster for auditability.

## Synthetic / real mix

- **Synthetic**: ``{designed, simulated, hil}`` (all promoted
  ``provenance.kind`` values that originate from the factory).
- **Real/unknown**: ``{real, unknown}`` only — records that carry one of
  those labels.
- **Unlabeled**: records with no recognized provenance label (missing
  field, or a value outside the synthetic/real sets). Reported as its own
  ``mix.unlabeled`` bucket, never folded into real/unknown. Counting them
  outside ``synthetic`` is the conservative choice because it avoids
  treating an unlabeled record as *proven synthetic*; the trade-off is
  that the reported synthetic share can understate reality, which is why
  the bucket is surfaced instead of hidden. ``synthetic + real_unknown +
  unlabeled == total``, and ``synthetic_ratio`` stays ``synthetic /
  total`` over that same population.
- Promotion already normalizes ``sim_or_real → provenance.kind`` so mix
  counting is consistent between raw and cleaned trees. Stateless records with
  a nonempty ``meta.factory`` origin are stamped/count as ``designed`` rather
  than ``unknown``. For preference pairs,
  matching ``chosen``/``rejected`` provenance is counted once per pair; a
  partial or conflicting pair remains unlabeled. Bridge wrappers use their
  nested trajectory provenance before a generic top-level ``unknown`` stamp.

### The policy is blocking

SOTA (``Demystifying Synthetic Data``, >1000 LLMs) finds ~0.30 rephrased
synthetic / 0.70 real optimal for the target tasks. That is the default
policy, and it **blocks** — it is not a warning any more:

| Knob | Default | Effect |
|---|---|---|
| ``--mix-target`` | ``0.30`` | The 30/70 target. Above it → warning. |
| ``--mix-tolerance`` | ``0.20`` | Slack above the target before blocking. |
| ``--max-synthetic-ratio`` | ``target + tolerance`` = ``0.50`` | Explicit ceiling; overrides target+tolerance. **Above it → blocked, exit 1.** |
| ``--min-synthetic-ratio`` | none | Optional floor. Off by default: a tree that is entirely real is not a collapse risk. When configured, an empty corpus has ratio 0 and fails a positive floor. |
| ``--max-unlabeled-ratio`` | none | Optional ceiling on the unlabeled bucket. Off by default; above 0.5 the gate warns that the enforced ratio understates the real synthetic share. |

The resolved policy is echoed in the report as ``mix_policy`` (including
``"blocking": true``) so a run's manifest records the rule it was judged
against, not just the verdict. An unsatisfiable policy (floor above
ceiling, ratios outside ``[0, 1]``) is rejected before any file is read.

``mix`` also reports ``unlabeled_ratio`` and ``labeled_synthetic_ratio``
(``synthetic / (synthetic + real_unknown)``). The former can be bounded by
``--max-unlabeled-ratio``; the latter is report-only.

## Curated manifest (sidecar)

``quality_gate.py --manifest <path>`` writes the full report as a sidecar next
to the curated tree. The standalone gate remains read-only unless that flag is
passed. The established ``promote.py`` command always writes promotion
evidence, defaulting to ``<cleaned_out>/quality-manifest.json``; use
``--quality-manifest <path>`` to select another non-raw location. Standalone
manifest targets must be absent and outside the audited run tree; ``.jsonl``
targets are rejected. Files are created exclusively rather than overwritten,
so a typo can never replace an audited input or an earlier manifest. Promotion
may place its default inside ``cleaned_out`` because that destination is newly
created and raw input is separately protected. A custom target that equals or
contains ``cleaned_out`` is rejected before promotion starts; otherwise the
destination could be created first and make the later exclusive manifest write
unretryable. Parent directories are created.

```bash
python3 pipelines/quality_gate.py outputs/cleaned/2026-08-17 \
  --threshold 0.97 --manifest outputs/curated/2026-08-17/quality-manifest.json
```

The manifest adds ``schema`` (``quality-manifest/1``), ``generated_by``
and ``run_dir`` to the report, and carries the mix ratio, the resolved
mix policy, the duplicate clusters, per-record exclusion reasons, the
reward-shape counts and the blockers list. It is the evidence the
promotion decision was made on, so it is written whether the gate passed
or blocked.

## Usage

```bash
# Exact-hash + embedding dedup + blocking mix check
python3 pipelines/quality_gate.py outputs/cleaned/2026-08-17 --json

# Pin the threshold and the mix policy for CI, and keep the sidecar
python3 pipelines/quality_gate.py outputs/cleaned/2026-08-17 \
  --threshold 0.97 --mix-target 0.30 --mix-tolerance 0.20 \
  --manifest outputs/curated/2026-08-17/quality-manifest.json --json

# Hash-only pass (skips the embedding stage; says so in warnings)
python3 pipelines/quality_gate.py outputs/cleaned/2026-08-17 --no-embedding-dedup

# Human-readable stderr
python3 pipelines/quality_gate.py outputs/cleaned/2026-08-17 --threshold 0.95
echo $?   # 0 = pass, 1 = blocked, 2 = bad arguments / unsatisfiable policy
```

JSON output fields:

```json
{
  "counts": {"total": 1234, "unique_hashes": 1230, "duplicate_groups": 2,
             "embedding_duplicate_groups": 1, "excluded_records": 5,
             "unreadable_files": 0, "malformed_lines": 0},
  "mix": {"synthetic": 380, "real_unknown": 854, "unlabeled": 0, "total": 1234,
          "synthetic_ratio": 0.308, "unlabeled_ratio": 0.0,
          "labeled_synthetic_ratio": 0.308,
          "provenance": {"designed": 200, "simulated": 180, "unknown": 854}},
  "mix_policy": {"target_synthetic_ratio": 0.3, "tolerance": 0.2,
                 "max_synthetic_ratio": 0.5, "min_synthetic_ratio": null,
                 "max_unlabeled_ratio": null, "blocking": true},
  "duplicates": [
    {"file": "batch-r02.jsonl", "line": 214, "hash": "a1b2c3d4e5f60123", "kind": "exact",
     "duplicate_of": {"file": "batch-r02.jsonl", "line": 12},
     "reason": "exact content hash a1b2c3d4e5f60123 already seen at batch-r02.jsonl:12"},
    {"file": "batch-r03.jsonl", "line": 8, "kind": "embedding", "similarity": 0.9889,
     "duplicate_of": {"file": "batch-r03.jsonl", "line": 7},
     "matched_with": {"file": "batch-r03.jsonl", "line": 7},
     "reason": "embedding near-duplicate: cosine 0.9889 > 0.97 vs retained representative batch-r03.jsonl:7 (encoder lexical-tfidf/8)"}
  ],
  "duplicate_clusters": [
    {"kind": "embedding", "size": 2, "threshold": 0.97, "encoder": "lexical-tfidf/8",
     "max_similarity": 0.9889,
     "representative": {"file": "batch-r03.jsonl", "line": 7},
     "members": [{"file": "batch-r03.jsonl", "line": 7}, {"file": "batch-r03.jsonl", "line": 8}],
     "reason": "1 excluded record(s) linked by cosine > 0.97; representative batch-r03.jsonl:7 is retained"}
  ],
  "embedding": {"enabled": true, "encoder": "lexical-tfidf/8",
                "candidate_sketch": "weighted-tier-minhash/1", "threshold": 0.97,
                "compared_records": 1230, "candidate_pairs": 418, "truncated": false},
  "reward_shapes": {"records_with_reward_components": 1180, "unique_component_keys": 510,
                    "unique_shapes": 140, "top_component_keys": [], "top_shapes": []},
  "errors": {"unreadable_files": 0, "malformed_lines": 0, "unreadable_examples": [], "malformed_examples": []},
  "warnings": [],
  "blockers": [],
  "blocked": false,
  "threshold": 0.97
}
```

## Reward-shape entropy

The gate reports ``reward_components`` vocabulary — how many distinct
component keys and how many distinct structural shapes the tree carries
(the cleaned corpus last measured 510 keys / 140 shapes). It is
**report-only and never blocks**, and it never sums, rescales or
otherwise mixes reward magnitudes across shapes: an aggregate over
incomparable units would be a worse lie than the entropy itself.
Normalizing the ontology is sf-c5l.4's job, not this gate's.

## Unreadable files and malformed lines

Files the gate cannot open or UTF-8 decode, and lines that are not valid
JSON, are counted in ``errors`` (with up to 10 examples per category) and
set ``blocked``. Everything else in the report — ``counts``, ``mix``,
duplicate detection — covers only the readable/parseable subset, so a
corrupt run must never be read as a clean pass. Fix or quarantine the
offending files and re-run the gate.

## Integration with ``pipelines/promote.py``

``promote.py`` writes ``cleaned_out`` and immediately runs this gate over that
new tree. The command exits 1 when blocked and retains both the diagnostic
cleaned tree and its manifest as evidence; that output is not curated or
training-ready. The default pipeline is:

```bash
python3 pipelines/promote.py outputs/raw/2026-08-17 outputs/cleaned/2026-08-17
# exit 0 = gate passed; exit 1 = blocked, inspect quality-manifest.json
```

The promotion CLI accepts the gate's threshold, embedding-cap and mix-policy
flags, plus ``--quality-manifest``. The standalone command remains useful for
re-auditing an existing tree or writing a separately located curated sidecar.

CI should:

- Treat the integrated promotion command as the required gate; an explicit
  standalone re-audit is still valid when CI separates transform and audit
  jobs.
- Treat ``blocked == true`` as a hard failure (do not train). It now
  covers exact duplicates, embedding near-duplicates, truncated candidate
  recall, unreadable or malformed input, and a synthetic/real mix outside
  policy.
- Keep the ``--manifest`` sidecar as the promotion evidence.
- Treat ``warnings`` (mix above target but inside tolerance, unlabeled
  share, or an explicitly disabled embedding pass) as soft failures requiring review
  and an explicit override comment.

See ``pipelines/promote.py`` for the integrated exit-code contract and
``pipelines/quality_gate.py`` for the authoritative threshold documentation.

## References

- Thalamic schema: ``schemas/thalamic.md`` / ``schemas/provenance.md``
- SOTA mix guidance: ``Demystifying Synthetic Data`` (≈30% rephrased synthetic)
- Deep record checks: ``pipelines/check_records.py`` (spike order, reward arithmetic, duplicate IDs)
