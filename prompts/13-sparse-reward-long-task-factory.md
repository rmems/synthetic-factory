## Session bootstrap

- Factory slug: `sparse-reward-long-task-factory`
- Shared rules: `prompts/_agentic-factory-contract.md`
- Run tree: `outputs/raw/2026-08-19-agentic/sparse-reward-long-task-factory`
- Reserve, stage, validate, and publish only through `pipelines/round_txn.py`
- Never write generated content directly into `outputs/raw/`
- Not Thalamic. No `spike_events`, Spikenaut, rasters, or `sim_or_real: real`
- Invented plants are `designed`. `meta.generator` is `"grok-4.6"`

You produce **one long episode whose reward is terminal only**. Routes as
`episode`. Intermediate steps carry evidence, not scores.

### Batch quota

- Exactly **1** episode (`FACTORY_QUOTAS["sparse-reward-long-task-factory"] == 1`)
- Reserve: `python3 pipelines/round_txn.py reserve <factory-dir> --round N --expected 1`
- Write only into returned `staging_dir` at exact `batch_file` and `notes_file`
- One JSON object per nonblank JSONL line — no fences, headings, comments
- NOTES must include `Novel coverage: <N>%`, then publish with the reservation token

### Shape (per JSONL line)

```json
{
  "id": "srl-rNN-<slug>-<hash>",
  "goal": "multi-hour / multi-module task with a late verification",
  "steps": [Step, "... 25-60 items"],
  "outcome": "terminal observable result",
  "reward": {"success": true, "terminal_only": true, "horizon_steps": 36},
  "meta": {"factory": "sparse-reward-long-task-factory", "round": 1, "generator": "grok-4.6"}
}
```

`Step`: `{n, decision_basis, tool_call, observation}`. **No `reward` key on
steps.** `reward` exists only at the episode root and must include `success`.

### Horizon rules

- **25–60 steps**, numbered 1..K with no gaps.
- Credit assignment is terminal: the agent cannot see `reward` until `outcome`.
  Do not sprinkle `tests_passed` / `score` onto intermediate steps.
- The task must need the length (multi-file migration, flaky-then-real bug,
  long repro). Pad-free: every step changes files, tests, or beliefs.
- Include at least two failed hypotheses that are abandoned from observations,
  not from a mid-episode score.
- No hidden CoT keys. No neuromorphic wrapping.

### NOTES

Step count, where hypotheses were abandoned, confirmation that no step carries
a reward, next densify target. Repair staging only. Never invent `c` suffixes.
