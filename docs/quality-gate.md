# Quality Gate — sf-xua

Dedup + synthetic/real mix enforcement before volume training. The gate is
the last check between ``pipelines/promote.py`` and any training run.

```
raw JSONL (append-only SoT)
    │
    ▼
pipelines/promote.py  ──►  cleaned/<date>/   (provenance remapped, spike trains sorted)
    │
    ▼
pipelines/quality_gate.py --threshold 0.97   ──►  blocked?  ──►  train / fix
```

Co-authored-by: Muse Code powered by Muse Spark <muse-spark@meta.com>

## What it checks

| Check | Signal | Fail mode |
|---|---|---|
| **Exact-hash dedup** | SHA-256 over canonical JSON of ``state + proposed_action + executed_action`` (fallback ``chosen/rejected``) | ``blocked = true``, exit 1 |
| **Embedding dedup** | Pairwise cosine similarity over record embeddings | Group added to ``duplicates`` with ``kind="embedding"`` when ``cosine_sim > threshold``; also sets ``blocked`` |
| **Synthetic/real mix** | Buckets ``provenance.kind`` / ``state.sim_or_real`` → synthetic ``{designed, simulated, hil}`` vs ``{real, unknown}`` | Warns when ``synthetic_ratio > 0.5``; target ~0.30 / 0.70 per SOTA |

## Embedding dedup threshold

### Definition

When embeddings are available, every record is embedded once (shared
encoder) and pairwise cosine similarity is computed. A pair is a
near-duplicate iff

```
cosine_sim(a, b) > threshold
```

All records above the threshold are grouped and reported as a
``duplicate_group``. Downstream stages should reuse the same
``--threshold`` value so provenance stays comparable across runs.

### Default: 0.97

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

### Tuning

Sweep ``0.93 / 0.95 / 0.97 / 0.98`` on a held-out factory slice:

1. Run the gate at each candidate and collect duplicate groups.
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

- Default lives in ``pipelines/quality_gate.py:DEFAULT_EMBEDDING_THRESHOLD``.
  Downstream embedding stages should ``from quality_gate import
  DEFAULT_EMBEDDING_THRESHOLD`` rather than re-defining the value.
- CLI override: ``--threshold <float>`` (e.g., ``--threshold 0.95``).
  The chosen value is echoed in the JSON output as ``threshold`` for
  auditability.

### When embeddings are not wired

The gate still enforces exact-hash dedup unconditionally. The
``threshold`` value is recorded in output for provenance even when no
embedding stage runs, so adding embeddings later does not change the
gate's interface.

## Synthetic / real mix

- **Synthetic**: ``{designed, simulated, hil}`` (all promoted
  ``provenance.kind`` values that originate from the factory).
- **Real/unknown**: ``{real, unknown}`` and any record where the
  provenance field is missing (counted conservatively toward real so
  the gate never understates synthetic share).
- **Guidance**: SOTA (``Demystifying Synthetic Data``) finds ~0.30
  rephrased synthetic / 0.70 real optimal for the target tasks. The
  gate warns at ``> 0.5`` and expects a human override justification if
  the ratio is intentionally higher.
- Promotion already normalizes ``sim_or_real → provenance.kind`` so mix
  counting is consistent between raw and cleaned trees.

## Usage

```bash
# Exact-hash + mix check (no embeddings needed)
python3 pipelines/quality_gate.py outputs/cleaned/2026-08-17 --json

# With explicit threshold (pin for CI)
python3 pipelines/quality_gate.py outputs/cleaned/2026-08-17 --threshold 0.97 --json

# Human-readable stderr
python3 pipelines/quality_gate.py outputs/cleaned/2026-08-17 --threshold 0.95
echo $?   # 0 = pass, 1 = blocked (duplicates)
```

JSON output fields:

```json
{
  "counts": {"total": 1234, "unique_hashes": 1230, "duplicate_groups": 2},
  "mix": {"synthetic": 380, "real_unknown": 854, "total": 1234, "synthetic_ratio": 0.308, "provenance": {"designed": 200, "simulated": 180, "unknown": 854}},
  "duplicates": [{"file": "batch-r02.jsonl", "line": 214, "hash": "a1b2c3d4e5f60123"}],
  "warnings": [],
  "blocked": false,
  "threshold": 0.97
}
```

## Integration with ``pipelines/promote.py``

``promote.py`` writes ``cleaned_out`` but does **not** gate it. The
intended pipeline is:

```bash
python3 pipelines/promote.py outputs/raw/2026-08-17 outputs/cleaned/2026-08-17
python3 pipelines/quality_gate.py outputs/cleaned/2026-08-17 --threshold 0.97 --json
# only train if exit 0 and synthetic_ratio ≈ 0.3
```

CI should:

- Run the gate as a required check after promotion.
- Treat ``blocked == true`` as a hard failure (do not train).
- Treat ``warnings`` (mix > 0.5) as a soft failure requiring review
  and an explicit override comment.

See ``pipelines/promote.py`` module docstring for the same contract
and ``pipelines/quality_gate.py`` for the authoritative threshold
documentation.

## References

- Thalamic schema: ``schemas/thalamic.md`` / ``schemas/provenance.md``
- SOTA mix guidance: ``Demystifying Synthetic Data`` (≈30% rephrased synthetic)
- Deep record checks: ``pipelines/check_records.py`` (spike order, reward arithmetic, duplicate IDs)
