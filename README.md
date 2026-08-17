# Synthetic Data Factory (Fable 5 / Thalamic / Spikenaut / Agoge)

Prompts, schemas, raw Claude outputs, cleaned trajectories, and pipelines for high-quality synthetic data generation.

**Notebook:** [synthetic-factory on Notion](https://app.notion.com/p/racconcity/synthetic-factory-3bfb11c37ce78056ac11fec43e6f01e7). Repo is source of truth. Raw JSONL is **append-only**.

## Structure
- `prompts/` — factory prompts 01–07. 01–05 start with a session bootstrap; shared rules in `prompts/_factory-contract.md`
- `schemas/` — Thalamic schema + `provenance.md`
- `outputs/raw/` — dated dumps. `2026-08-17/` is the live run; `2026-08-17-prehalt/` is the pre-resume copy. `NEXT_ROUND.json` is a generated index, not a record
- `outputs/cleaned/` — remapped copies (`sim_or_real` never `real`)
- `outputs/curated/` — ready for training / HF export (empty)
- `pipelines/` — census, next-round allocator, shape validator, deep checker, promote
- `experiments/` — harvest notes (`2026-08-17-quality-report.md` is a mid-run snapshot; `2026-08-17-grok-census.md` is current)

## Before the next Fable session

```bash
python3 pipelines/next_round.py outputs/raw/2026-08-17/<factory-slug>
# writes only the unused batch-rNN.jsonl + NOTES-rNN.md that it prints
# never overwrite

python3 pipelines/next_round.py --write-index outputs/raw/2026-08-17
```

Do **not** start prompts 06 or 07 until 01–05 have a cleaned slice you are willing to train on.

## Pipelines

```bash
python3 pipelines/census.py outputs/raw/2026-08-17          # JSON counts; no writes
python3 pipelines/validate_run.py outputs/raw/2026-08-17    # shape gate; no manifest unless --write
python3 pipelines/check_records.py outputs/raw/2026-08-17   # reward / spike order / ids
python3 pipelines/promote.py outputs/raw/2026-08-17 outputs/cleaned/2026-08-17
```

Tests: `python3 -m unittest discover -s tests -p 'test_*.py' -q`

## Quick start (generation)

Copy `prompts/01`–`05` into a Fable 5 chat (bootstrap first). Then:
"Expand every section significantly. Increase density and realism. Critique what is still weak and improve it. Never summarize previous material."
