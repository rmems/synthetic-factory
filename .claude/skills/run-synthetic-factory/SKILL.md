---
name: run-synthetic-factory
description: Run, launch, validate, audit, harvest, snapshot, or resume the Spikenaut/Agoge synthetic data factory. Use for factory generation windows, raw output health, per-factory round frontiers, training-readiness reports, safe publication, and promotion.
---

# Run the Synthetic Data Factory

Operate the repository as a bounded data-production system. Five factories may
run concurrently; rounds within each factory are sequential and transactional.
Treat `outputs/raw/` as immutable committed evidence, not a scratch directory.

## Respect the requested scope

- For **observe, harvest, audit, review, or report** requests, run only read-only
  commands. Do not launch, stop, message, or re-prompt generators.
- For **launch or resume** requests, complete the preflight below and launch one
  fresh bounded workflow. Do not infer permission to mutate cleaned/curated data.
- For **stop** requests, stop at the current workflow boundary and report any
  reserved/unpublished stages. Do not delete them.
- Never claim outputs are training-ready from JSON parsing or shape validation
  alone. The corpus audit is the training gate.

All commands run from the repository root. Canonical skill directory:
`.claude/skills/run-synthetic-factory/`.

## Read-only preflight

```bash
# Tooling self-test, including no-clobber transactional publication
python3 .claude/skills/run-synthetic-factory/driver.py smoke

# Stable-copy structural check; reports shape/event defects
python3 .claude/skills/run-synthetic-factory/driver.py validate outputs/raw/<date>

# Full stable-copy gate: structural + deep invariants + corpus readiness
python3 .claude/skills/run-synthetic-factory/driver.py audit outputs/raw/<date>

# Marker-aware, validated per-factory frontiers
python3 .claude/skills/run-synthetic-factory/driver.py frontiers outputs/raw/<date> --json
```

`validate` is structural/invariant evidence. `audit` additionally checks reward
arithmetic, IDs, provenance, preference context purity, duplicates, reward/tag
entropy, record lengths, neuromorphic ordering/density, and SNN distillation
readiness — a 20-50 ms raster excerpt with a routing table on every bridge
record, the `spikes = round(neurons * rate * window_s)` budget, and at least one
spike-implemented `gate_snn` head per round. A nonzero audit is a real training
blocker; report it rather than relabeling the corpus as clean.

To load those rasters for a distillation probe — `(neuron_id, t_us)` events,
populations, routing, third-factor eligibility, and gate heads, all read from
structured JSON and never from prose counts:

```bash
python3 pipelines/spike_probe.py --strict outputs/raw/<date>
python3 pipelines/spike_probe.py --jsonl outputs/raw/<date> > rasters.jsonl
```

## Snapshot before every launch

```bash
python3 .claude/skills/run-synthetic-factory/driver.py \
  snapshot outputs/raw/<date> pre-window-<N>
```

Snapshots are sibling directories and never overwrite an existing path. Record
the snapshot path and the audit result before generation.

## Launch one bounded window

Use a fresh Workflow invocation with the committed script:

```text
Workflow({
  scriptPath: "<repo>/.claude/skills/run-synthetic-factory/factory-window.workflow.js",
  args: {
    date: "<YYYY-MM-DD>",
    root: "<absolute-repo-path>",
    starts: {
      "thalamic-trajectory-factory": <frontier next_round>,
      "multi-agent-ouroboros-swarm": <frontier next_round>,
      "neuromorphic-event-language-bridge": <frontier next_round>,
      "failure-as-fuel-preference-cascade": <frontier next_round>,
      "agentic-coding-trajectory-factory": <frontier next_round>
    },
    end: <inclusive-bounded-round>
  }
})
```

Do not use `resumeFromRunId` for a prior parallel window. Cached interleavings
are not a round allocator. Start a new workflow from freshly measured frontiers.

**Respect prior early-stops.** A plateau early-stop leaves no marker in the run
tree — frontiers alone will happily re-queue the very rounds the last window
declined. Before filling `starts`, run:

```bash
python3 .claude/skills/run-synthetic-factory/driver.py \
  token-efficiency outputs/raw/<date> --json
```

and OMIT every factory whose `early_stop` is true — that flag is the current
trailing two-low streak, not a historical latch (a later healthy NOTES clears
it). The workflow skips factories with no start. Re-include a still-plateaued
factory only when its prompt, quotas, or gap targets have changed enough to
expect fresh novelty.

The flag only exists if rounds report their novelty, so `round_txn.py publish`
now rejects staged NOTES that omit `Novel coverage: <N>%` or state a value
outside 0–100 — on every registered lane, including the legacy Thalamic
factories. A generation agent that hits that error should repair its staged
notes and republish; it is not a batch defect. Rounds committed before the
contract are unaffected and stay readable. See `docs/token-efficiency.md`.

The workflow runs at most five agents at once. Each generated round is followed
by one bounded, read-only marker verifier in the same per-factory lane; it checks
the frontier plus marker file hashes before progress is counted. Each factory
opens its circuit on
the first agent error, session-limit response, identity mismatch, quota mismatch,
or missing completion-marker claim. It does not queue a storm of doomed later
rounds. Other factory loops remain independent.

## Round transaction contract

Agents must use `pipelines/round_txn.py`; prompt-only “do not overwrite” rules
are insufficient.

```bash
python3 pipelines/round_txn.py reserve \
  outputs/raw/<date>/<factory> --round <N> --expected <quota>

# Write only inside staging_dir returned above, then:
python3 pipelines/round_txn.py publish \
  outputs/raw/<date>/<factory> --round <N> --token <token>

python3 pipelines/round_txn.py frontier outputs/raw/<date>/<factory>
```

Publication requires the exact quota, a nonempty NOTES file, zero deep-check
errors or warnings, and no destination collision. Files are staged under
`outputs/staging/`; `ROUND-rNN.complete.json` is the atomic visibility point.
An interrupted publish is resumable with the same token. Never delete a
reservation or staging directory just because an agent stopped.

Publication also runs `pipelines/verify_execution.py` in strict mode and fails
closed: a `failed` record can never be published, and an `inconclusive`
(cannot-verify) record blocks the round until the batch is regenerated with
observable execution evidence or an operator records an explicit waiver.

```bash
python3 pipelines/round_txn.py publish \
  outputs/raw/<date>/<factory> --round <N> --token <token> \
  --allow-inconclusive "<why this batch cannot be verified>"
```

The waiver and the verified/inconclusive/failed counts are written into
`ROUND-rNN.complete.json`. Never treat cannot-verify as verified — see
`docs/verify-execution.md`.

New trajectories use `schemas/thalamic-trajectory-v2.schema.json`, which makes
top-level IDs and canonical state provenance mandatory. The unsuffixed schema
is retained only so legacy raw records remain inspectable without rewriting.

## Harvest and status reporting

Take a stable snapshot or use `driver.py audit`, then report:

- workflow ID/state and completed/error agent counts from actual workflow data;
- committed rounds from completion markers (or validated legacy baseline);
- files, records, bytes, and approximate tokens per factory;
- structural errors versus corpus-level blockers, separately;
- ID/provenance coverage, preference purity, reward-shape entropy, duplicate
  content, bridge ordering/density, and factories that under-produce;
- exact timestamp and whether numbers came from live raw, a snapshot, or a
  workflow journal.

Never estimate agent-token usage from output bytes without labeling the method.
Output-token estimates (`bytes / 4`) and model usage tokens are different units.

## Promotion

Raw data is immutable. Promote only into a brand-new destination:

```bash
python3 pipelines/promote.py outputs/raw/<date> outputs/cleaned/<new-label>
```

The promoter refuses an existing destination and any destination nested inside
the raw source. Do not promote while `audit` is blocked unless the user explicitly
asks for a diagnostic cleaned copy; never describe such a copy as curated.

## Failure handling

- **Session limit / model safeguard:** the affected factory circuit opens for
  the window. Keep committed rounds, preserve staging, and resume later from a
  fresh frontier after the external condition changes.
- **Reservation says wrong frontier:** supplied starts are stale or another
  writer owns the round. Re-measure; never skip ahead or add a filename suffix.
- **Publish validation failure:** repair only the staged batch and retry with the
  same token. Do not hand-edit committed raw output.
- **Existing reservation:** inspect its JSON and staging directory. Resume the
  same transaction if ownership is known; otherwise stop and report it.
- **Legacy malformed batch:** it does not advance the validated legacy frontier.
  Preserve it as evidence and report/quarantine through an explicit curation
  decision rather than silently rewriting it.
