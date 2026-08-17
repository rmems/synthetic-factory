# Synthetic Data Factory (Fable 5 / Thalamic / Spikenaut / Agoge)

Prompts, schemas, raw Claude outputs, cleaned trajectories, and pipelines for high-quality synthetic data generation.

## Structure
- `prompts/` — the 7 factory prompts (ready to paste into Fable 5)
- `schemas/` — Thalamic and trajectory schemas
- `outputs/raw/` — dated dumps straight from Fable sessions
- `outputs/cleaned/` — post-processed
- `outputs/curated/` — ready for training / HF export
- `pipelines/` — post-processing scripts
- `experiments/` — parallel runs and notes

## Quick start
Copy any prompt from `prompts/` into a Fable 5 chat and iterate with:
"Expand every section significantly. Increase density and realism. Critique what is still weak and improve it. Never summarize previous material."
