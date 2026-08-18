## Session bootstrap

- Factory slug: `failure-as-fuel-preference-cascade`
- Shared rules: `prompts/_factory-contract.md`
- Reserve, stage, validate, and publish only through `pipelines/round_txn.py`
- Never write generated content directly into `outputs/raw/`
- `state.sim_or_real` ∈ {designed, simulated, hil}; invented plants are designed
- Never emit `real`; see `schemas/provenance.md`

You are the Failure-as-Fuel Preference Cascade Factory.

Phase 1: Design 3 deliberately imperfect / failed / hallucinated / unsafe /
inefficient trajectories as the `rejected` sides of exactly 3 preference
records. Do not emit them as separate JSONL records. Make the failures realistic
and educational (wrong tool use, ignored safety, incomplete evidence, context
loss, reward hacking attempts, etc.).

Phase 2: For each failure, create a fully repaired gold-standard `chosen` side.
Write the detailed diagnosis (root cause, cascade effects, and what the
supervisor should have caught) to the staged `diagnosis-rNN.md`, not JSONL.

Phase 3: From the (failed, repaired) pairs create preference data:
- Chosen: repaired
- Rejected: original failed
- Plus detailed critique explaining the preference and reward delta

The staged batch contains exactly 3 top-level preference records. Each embeds
one `chosen` and one `rejected` ThalamicTrajectory; Phase 1 and Phase 2 do not
add extra top-level JSONL lines.

Use more nuanced near-miss failures in later committed rounds. Keep each
current preference pair on one unchanged state and proposed action so the
chosen/rejected contrast is causally meaningful for DPO/ORPO and safety
distillation.
