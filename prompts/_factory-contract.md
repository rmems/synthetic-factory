# Factory contract (prompts 01–05)

These are training-data producers, not claims about live deployments. Do not
start factories 06 or 07 from this contract.

## Transactional output

1. A workflow/operator supplies the factory directory, round, and exact quota.
2. Before generating, reserve the round with
   `python3 pipelines/round_txn.py reserve <factory-dir> --round N --expected Q`.
3. Write every new artifact only into the returned `staging_dir`, using its
   exact `batch_file` and `notes_file`. Never write generated content directly
   into `outputs/raw/`; never invent `c` collision suffixes.
4. Emit exactly one complete JSON object per nonblank JSONL line—no fences,
   headings, comments, trailing prose, or multiline objects.
5. Self-critique in the staged notes, which MUST contain the line
   `Novel coverage: <N>%` (see "Novel coverage" below), then publish with
   `python3 pipelines/round_txn.py publish <factory-dir> --round N --token TOKEN`.
   Repair only staged files when validation fails. A round is complete only
   when its `ROUND-rNN.complete.json` marker exists.
6. Never overwrite, truncate, rename, delete, or hand-edit a committed raw file.

## Record integrity

- Every top-level record has a globally unique, stable string `id`.
- New Thalamic trajectories follow `schemas/thalamic-trajectory-v2.schema.json`;
  the unsuffixed schema remains a legacy-compatible reader contract.
- Every ThalamicTrajectory has object-valued `state`, `proposed_action`,
  `safety_decision`, `executed_action`, `future_outcome`, and
  `reward_components`.
- `safety_decision.decision` is exactly `ACCEPT`, `MODIFY`, or `REJECT`, with a
  concrete non-empty rationale tied to observable constraints.
- Use concise observable evidence and decision bases. Never emit hidden
  chain-of-thought, private scratch reasoning, or fabricated tool output framed
  as an actual execution trace.
- `state.sim_or_real` is exactly `designed`, `simulated`, or `hil`. Invented
  scenarios are `designed`; never write `real`. See `schemas/provenance.md`.
- `reward_components.total` follows one declared aggregation and reconciles
  numerically. Do not mix incomparable units as one scalar.
- Preference `chosen` and `rejected` share the exact same state and proposed
  action. The contrast must teach gate/execution/recovery quality, not reward a
  changed problem.
- Bridge `spike_events` are globally non-decreasing by finite timestamp and
  include finite amplitudes, channel IDs, realistic density, refractory gaps,
  adaptation, and noise.

## Novel coverage (required NOTES line)

Every staged `NOTES-rNN.md` must contain one line of the form:

```
Novel coverage: 12.3%
```

`N` is your honest estimate of the fraction of this round's scenarios, edges,
or failure modes that are novel relative to all prior committed rounds for this
factory. `round_txn.py publish` rejects a round whose notes omit the line or
state a value outside 0–100.

The line drives the token-efficiency early-stop: two consecutive rounds under
5% stop the lane and save ~40% of the plateau tail's generation and
verification tokens (`docs/token-efficiency.md`). Report a low number when
novelty really is low — over-reporting buys near-duplicate rounds at full
token cost, and under-reporting cuts a lane that still had signal left. An
optional parenthetical is accepted
(`Novel coverage (estimated): 4.2 %`); prose percentages elsewhere in the notes
are ignored, so the labeled line must be present verbatim.

## Quality

Use concrete constraints, measurable outcomes, calibrated uncertainty, varied
gate decisions, realistic failure/recovery, and genuinely distinct scenarios.
The notes must name residual weaknesses and a specific next densification target.
