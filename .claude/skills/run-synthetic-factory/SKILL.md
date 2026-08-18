---
name: run-synthetic-factory
description: Run, launch, validate, harvest, or resume the Spikenaut/Agoge synthetic data factory — start windowed generation workflows, validate outputs/raw run trees against the Thalamic schema, compute per-factory round frontiers, snapshot before relaunch. Use for "run the factory", "launch generation", "validate the run", "harvest outputs", "resume generation".
---

# Run the Synthetic Data Factory

This repo is not a server or GUI — it's a **data factory**: 7 prompts (`prompts/`), a
Thalamic trajectory schema (`schemas/`), a validator (`pipelines/validate_run.py`),
and dated run trees under `outputs/raw/<date>/`. "Running" it means launching a
**Workflow** of 5 factory subagents that generate → self-critique → densify JSONL
batches, then harvesting/validating what lands. All paths below are relative to
the repo root. Driver: `.claude/skills/run-synthetic-factory/driver.py`
(python3, stdlib only — no prerequisites beyond python3).

## Driver (agent path — start here)

```bash
# self-test: validator accepts all 4 record kinds, rejects violations, frontiers work
python3 .claude/skills/run-synthetic-factory/driver.py smoke

# validate a run tree (copies it to a temp dir first — safe on a LIVE, mid-write run)
python3 .claude/skills/run-synthetic-factory/driver.py validate outputs/raw/2026-08-17

# per-factory highest flushed round + next round (--json for machine-readable)
python3 .claude/skills/run-synthetic-factory/driver.py frontiers outputs/raw/2026-08-17 --json

# durable pre-relaunch snapshot (refuses to clobber an existing one)
python3 .claude/skills/run-synthetic-factory/driver.py snapshot outputs/raw/2026-08-17 w5
```

`validate` exits 0 on a clean tree, nonzero with per-line errors on stderr.
The 2026-08-17 run validates clean: 189 records (105 thalamic / 42 preference /
39 bridge_pair / 3 episode).

## Launch a generation window (Workflow tool)

Generation runs as a Claude Code **Workflow** (requires a Claude session; there is
no standalone CLI for this part). The committed, battle-tested script is
`.claude/skills/run-synthetic-factory/factory-window.workflow.js`. Procedure:

1. `snapshot` the run tree (see above) — always, before any launch.
2. `frontiers --json` to get each factory's `next_round`.
3. Launch with the Workflow tool:

```
Workflow({
  scriptPath: "<repo>/.claude/skills/run-synthetic-factory/factory-window.workflow.js",
  args: {
    date: "2026-08-17",                    // run dir name under outputs/raw/
    root: "<abs repo path>",
    starts: {                              // from frontiers --json next_round values
      "thalamic-trajectory-factory": 12,
      "multi-agent-ouroboros-swarm": 14,
      "neuromorphic-event-language-bridge": 13,
      "failure-as-fuel-preference-cascade": 11,
      "agentic-coding-trajectory-factory": 10
    },
    end: 26                                // inclusive backstop round
  }
})
```

Each round-agent reads its factory prompt + the two newest `NOTES-r*.md`, generates
its quota (5 thalamic / 1 swarm / 3 bridge / 3 preference / 2 coding records),
self-critiques into a new NOTES file, and returns a structured summary. A window of
~20 rounds costs roughly 3M subagent tokens over ~2 h. While it runs: harvest with
`validate` + `frontiers` periodically. Stop anytime with TaskStop on the workflow's
task id.

## Test

`smoke` (above) is the test suite for the tooling. For the data itself, `validate`
IS the test: `python3 pipelines/validate_run.py <run_dir>` directly if you don't
need the live-tree-safe copy (`--write` also emits `manifest.json` into the dir).

## Gotchas (all hit in production on 2026-08-17)

- **Session limits kill windows.** Generation burns the account's ~5 h session
  window in ~2 h, then every queued round fails with "You've hit your session
  limit · resets H:10". The failures are harmless — completed batches stay on
  disk. Relaunch a **fresh** window at the reset time from new frontiers.
- **Never `resumeFromRunId` across windows.** The 5 factory loops run in
  parallel; their agent-call interleaving is nondeterministic, so the resume
  cache prefix breaks and completed rounds RE-RUN live — which overwrote batch
  files once (recovered from snapshots). Fresh launch + `starts` from
  `frontiers` is the safe pattern; the script's no-overwrite contract
  ("c"-suffix on collision) is the backstop.
- **Snapshot before every launch.** `driver.py snapshot <run> wN`. This turned
  two would-be data losses into non-events.
- **Model safeguards can false-positive one round** (happened once in ~60
  rounds: an API-level flag killed thalamic r05). The loop logs it and
  continues; the round's scenario space is simply retried by a later round.
- **`NEXT_ROUND.json`** in the run dir is a frontier manifest the factory
  agents maintain themselves. It's benign; agents may update it (the one
  allowed mutation). Trust `driver.py frontiers` over it if they disagree.
- **Validate the copy, not the live tree.** A snapshot mid-write can have a
  truncated final line; `driver.py validate` copies first for exactly this
  reason. A bad FINAL line of a growing file is in-flight, not a defect.
- **`find -newermt 'HH:MM'` fails on this box** — `find` is `bfs`, which wants
  ISO timestamps (`-newermt 2026-08-17T13:11:00Z`). For overwrite checks,
  compare file sizes against the last snapshot instead.

## Troubleshooting

- `refusing to overwrite existing snapshot` → intended; pick a new label
  (`w5`, `prehalt2`, …).
- Validator errors like `safety_decision.decision must be ACCEPT|MODIFY|REJECT`
  or `JSON parse error` → a factory emitted a malformed record; the message has
  `file:line`. Quarantine the line, don't hand-fix generated content silently.
- Workflow result shows dozens of `failed: You've hit your session limit` →
  see Gotchas #1; nothing to repair, relaunch at reset.
- A factory dir has `batch-rNNc.jsonl` files → the no-overwrite contract fired
  on a name collision; both files are real data, the validator picks up both.
