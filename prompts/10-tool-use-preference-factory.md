## Session bootstrap

- Factory slug: `tool-use-preference-factory`
- Shared rules: `prompts/_agentic-factory-contract.md`
- Run tree: `outputs/raw/2026-08-19-agentic/tool-use-preference-factory`
- Reserve, stage, validate, and publish only through `pipelines/round_txn.py`
- Never write generated content directly into `outputs/raw/`
- Not Thalamic. No `spike_events`, Spikenaut, rasters, or `sim_or_real: real`
- Invented plants are `designed`. `meta.generator` is `"grok-4.6"`

You produce **DPO/ORPO-ready preference pairs** whose sides are coding
**episodes**, not Thalamic trajectories. Routes as `preference` via
`check_line` (`_episode_like` sides). This is not factory 05's two-session
cascade.

### Batch quota

- Exactly **3** pairs (`FACTORY_QUOTAS["tool-use-preference-factory"] == 3`)
- Reserve: `python3 pipelines/round_txn.py reserve <factory-dir> --round N --expected 3`
- Write only into returned `staging_dir` at exact `batch_file` and `notes_file`
- One JSON object per nonblank JSONL line — no fences, headings, comments
- NOTES must include `Novel coverage: <N>%`, then publish with the reservation token

### Shape (per JSONL line)

```json
{
  "id": "tup-rNN-<slug>-<hash>",
  "goal": "shared task — identical for both sides",
  "chosen": {
    "steps": [Step],
    "outcome": "safer / more correct tool use",
    "reward": {"success": true}
  },
  "rejected": {
    "steps": [Step],
    "outcome": "what the worse tool policy did",
    "reward": {"success": false}
  },
  "critique": "why chosen is better on the same problem",
  "reward": {"success": true},
  "meta": {"factory": "tool-use-preference-factory", "round": 1, "generator": "grok-4.6"}
}
```

Each side is episode-like: non-empty `steps` with `decision_basis`, `tool_call`,
`observation`. Top-level `goal` is required (or `chosen.goal`). **`critique` is
a non-empty string** — blank or missing fails publish.

### Preference rules

- **Same problem both sides.** Do not change the file, API, or success criterion
  between `chosen` and `rejected`. Contrast tool policy, not a different ticket.
- Teach gate/execution/recovery quality: atomic write vs in-place, verify-before-
  delete vs blind `rm`, retry-with-backoff vs tight loop, scoped grep vs dump.
- 4–10 steps per side is enough if the contrast is load-bearing.
- Three distinct tool-use lessons per batch. No hidden CoT keys.

### NOTES

The three contrasts, confirmation that the problem is identical per pair,
weakest critique, next densify target. Repair staging only. Never invent `c` suffixes.
