# Factory contract (prompts 01–05)

Shared session rules. Do not start factory 06 or 07 from these prompts.

1. Run `python3 pipelines/next_round.py <this-factory-dir>` first.
2. Write **only** the unused `batch-rNN.jsonl` + `NOTES-rNN.md` that command names.
3. Never overwrite existing files.
4. `state.sim_or_real` must be `designed` | `simulated` | `hil`. Invented plants are `designed`. Never write `real`. Remap table: `schemas/provenance.md`.
5. `reward_components.total` must match the declared aggregation.
6. Bridge: `spike_events` globally time-sorted.
