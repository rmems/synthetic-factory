## Session bootstrap

- Factory slug: `cascading-error-recovery-factory`
- Shared rules: `prompts/_agentic-factory-contract.md`
- Run tree: `outputs/raw/2026-08-19-agentic/cascading-error-recovery-factory`
- Reserve, stage, validate, and publish only through `pipelines/round_txn.py`
- Never write generated content directly into `outputs/raw/`
- Not Thalamic. No `spike_events`, Spikenaut, rasters, or `sim_or_real: real`
- Invented plants are `designed`. `meta.generator` is `"grok-4.6"`

You produce coding episodes whose load-bearing event is a **fault that
propagates**, then a visible diagnosis and recovery. Still an `episode` record.

### Batch quota

- Exactly **2** episodes (`FACTORY_QUOTAS["cascading-error-recovery-factory"] == 2`)
- Reserve: `python3 pipelines/round_txn.py reserve <factory-dir> --round N --expected 2`
- Write only into returned `staging_dir` at exact `batch_file` and `notes_file`
- One JSON object per nonblank JSONL line — no fences, headings, comments
- NOTES must include `Novel coverage: <N>%`, then publish with the reservation token

### Shape (per JSONL line)

```json
{
  "id": "cer-rNN-<slug>-<hash>",
  "goal": "task in force when the fault is introduced",
  "error_introduced": {"step": 4, "kind": "stale-lock", "payload": "lock file left by crashed writer"},
  "steps": [Step, "..."],
  "diagnosis": "root cause + why later steps inherited it",
  "outcome": "recovered state or explicit uncontained failure",
  "reward": {"success": true, "cascade_steps": 5, "recovered": 1},
  "meta": {"factory": "cascading-error-recovery-factory", "round": 1, "generator": "grok-4.6"}
}
```

`Step` matches the shared episode envelope: `n`, `decision_basis`, `tool_call`,
`observation`. No hidden CoT keys.

### Cascade rules

- Introduce one concrete fault (`error_introduced.step` ≥ 2, not the last step).
- The next **3–8** steps must **inherit** the fault (wrong cache, poisoned lock,
  bad schema assumed downstream, retry amplifying the same error). Do not reset
  the world between those steps.
- Then a diagnosis step whose `observation` or `reflection` names the root cause,
  plus a top-level `diagnosis` grounded in the same introduced fault, followed
  by a recovery whose `decision_basis` cites both that diagnosis and fault.
- One episode fully recovers; one remains partially contained or hands off.
  Negated recovery or terminal failure cannot receive a recovered/success label.
- Vary fault class across the pair (stale state, silent truncate, auth expiry,
  schema drift, retry storm). Same problem before and after the fault.

### NOTES

Fault step, cascade length, diagnosis step, recovery quality, next densify target.
Repair staging only. Never invent `c` suffixes.
