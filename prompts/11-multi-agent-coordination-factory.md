## Session bootstrap

- Factory slug: `multi-agent-coordination-factory`
- Shared rules: `prompts/_agentic-factory-contract.md`
- Run tree: `outputs/raw/2026-08-19-agentic/multi-agent-coordination-factory`
- Reserve, stage, validate, and publish only through `pipelines/round_txn.py`
- Never write generated content directly into `outputs/raw/`
- Not Thalamic. No `spike_events`, Spikenaut, rasters, or `sim_or_real: real`
- Invented plants are `designed`. `meta.generator` is `"grok-4.6"`

You produce **multi-agent coordination transcripts** (not factory 02's
Ouroboros/Thalamic swarm). Routes as `multi_agent` via `check_multi_agent`.

### Batch quota

- Exactly **1** record (`FACTORY_QUOTAS["multi-agent-coordination-factory"] == 1`)
- Reserve: `python3 pipelines/round_txn.py reserve <factory-dir> --round N --expected 1`
- Write only into returned `staging_dir` at exact `batch_file` and `notes_file`
- One JSON object per nonblank JSONL line — no fences, headings, comments
- NOTES must include `Novel coverage: <N>%`, then publish with the reservation token

### Shape (per JSONL line)

```json
{
  "id": "mac-rNN-<slug>-<hash>",
  "goal": "joint decision the group must make",
  "agents": [
    {"role": "implementer", "mandate": "land the change"},
    {"role": "reviewer", "mandate": "block races"}
  ],
  "transcript": [
    {"n": 1, "speaker": "implementer", "content": "..."},
    {"n": 2, "speaker": "reviewer", "content": "..."}
  ],
  "disagreements": ["TTL race coverage"],
  "resolution": "what the group actually did",
  "joint_outcome": "shipped / blocked / split + residual risk",
  "reward": {"success": true},
  "meta": {"factory": "multi-agent-coordination-factory", "round": 1, "generator": "grok-4.6"}
}
```

Required by the checker: `goal`, `agents` (**≥ 2** roles with non-empty `role`),
non-empty `transcript` (each turn an object with `speaker`), `joint_outcome`,
`reward.success`. One role is not a coordination record.

### Coordination rules

- **2–4** named roles with distinct mandates. Speakers in the transcript must
  match `agents[].role`.
- At least one real disagreement that changes the plan; `resolution` cites it.
- 6–16 turns. No hidden CoT keys. Tool use, if any, is quoted in `content`
  (this shape has no `steps` array).

### NOTES

Roles, the disagreement that mattered, whether the joint outcome is earned,
next densify target. Repair staging only. Never invent `c` suffixes.
