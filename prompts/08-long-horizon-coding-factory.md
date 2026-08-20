## Session bootstrap

- Factory slug: `long-horizon-coding-factory`
- Shared rules: `prompts/_agentic-factory-contract.md`
- Run tree: `outputs/raw/2026-08-19-agentic/long-horizon-coding-factory`
- Reserve, stage, validate, and publish only through `pipelines/round_txn.py`
- Never write generated content directly into `outputs/raw/`
- Not Thalamic. No `spike_events`, Spikenaut, rasters, or `sim_or_real: real`
- Invented plants are `designed`. `meta.generator` is `"grok-4.6"`

You produce long multi-turn coding-agent episodes (`goal` + `steps` + `outcome` +
`reward`). Routes as `episode` via `validate_run.check_episode`.

### Batch quota

- Exactly **2** episodes (`FACTORY_QUOTAS["long-horizon-coding-factory"] == 2`)
- Reserve: `python3 pipelines/round_txn.py reserve <factory-dir> --round N --expected 2`
- Write only into returned `staging_dir` at exact `batch_file` and `notes_file`
- One JSON object per nonblank JSONL line — no fences, headings, comments
- NOTES must include `Novel coverage: <N>%`, then
  `python3 pipelines/round_txn.py publish <factory-dir> --round N --token TOKEN`

### Shape (per JSONL line)

```json
{
  "id": "lhc-rNN-<slug>-<hash>",
  "goal": "issue / task the agent was given",
  "plan": "optional initial approach (not a substitute for decision_basis)",
  "steps": [Step, "... 18-28 items"],
  "outcome": "what landed or the explicit handoff / residual risk",
  "reward": {"success": true, "tests_passed": 14, "cost_steps": 22},
  "meta": {"factory": "long-horizon-coding-factory", "round": 1, "generator": "grok-4.6"}
}
```

Each `Step`: `{n, decision_basis, tool_call: {name, args}, observation, reflection?}`.
`n` is 1..K with no gaps. `decision_basis` is observable (`Plan:` / `Observation:` /
`Reflection:` / `Tool call:`), ≤240 chars, citing a prior visible field. Never emit
`thought`, `chain_of_thought`, `scratch`, or `inner_monologue`.

`reward` must include boolean `success`. Extra numeric fields must be finite.

### Horizon rules

- **18–28 steps** per episode (longer than factory 04's 12–17).
- Arc: explore → hypothesis → repro → edit → test → iterate → verify.
- Include at least one `edit → test → fail → re-read → fix` loop.
- One episode succeeds; the other is partial success, mitigation, or handoff.
- Vary codebase type and bug class across the pair. No neuromorphic wrapping.

### NOTES

Step counts, where the debug loop lands, residual synthetic tells, next densify target.
Repair staging only. Never invent `c` suffixes.
