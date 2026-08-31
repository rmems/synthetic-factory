# Agent notes

This repository is a bounded synthetic-data factory. There is no long-running
HTTP service. The runnable surface is stdlib Python CLIs under `pipelines/`
plus the operator driver at
`.claude/skills/run-synthetic-factory/driver.py`.

Track work with Beads (`bd`). Do not add markdown TODO lists.

## Local checks

```bash
python3 -m unittest discover -s tests -p 'test_*.py' -q
python3 .claude/skills/run-synthetic-factory/driver.py smoke
python3 pipelines/census.py tests/fixtures/mini-run
```

`tests/fixtures/mini-run` includes one intentional JSON parse failure.
`validate_run.py` on that path is expected to exit nonzero.

## Review contracts (do not "fix" these)

Codex/review bots: these are accepted fail-closed contracts, not bugs.
Cite this section instead of inventing defensive defaults.

- **Mapping is SoT.** `schemas/reward-ontology-v1.mapping.json` is loaded at
  import in `pipelines/curate_rewards.py`. A missing, unreadable, or invalid
  mapping is a loud `RewardOntologyError`. Do not lazy-load the policy so
  utilities can import without it.
- **No `.get()` around guarded preference pointers.** `_classify` requires
  `set(rewards_by_pointer) == set(PREFERENCE_POINTERS)` before indexing.
  A missing pointer is **P01**, not a `KeyError`. Do not wrap that index in
  `.get()`.
- **Wrap records.** Coding steps live at `executed_action.steps`.
  `verify_curation` uses `_steps_path` / `_record_steps`. Do not assume
  `record["steps"]`. `coding_wrap_record` is a **record structural** reason
  (`RECORD_STRUCTURAL_REASONS`), not a retained-step reason.
- **Dual removal fields.** If both `thought_fields_removed` and
  `hidden_reasoning_fields_removed` are present, both must agree and match
  the accounting total. Do not pick one and ignore the other.
- **S08 calibration.** `external_calibration_evidence` is an optional reason
  on **S08** (and P05) when sidecar calibration is applied. Do not strip it
  or require it on uncalibrated S07/S08 paths.
- **Frozen reward census.** Mapping `source_vocabulary` is `records=195`,
  `reward_instances=247`, `ontology_scope_instances=258`. Do not "fix" 195
  back to 189 or rewrite `scope_note` to 252.
- **`canonical_unit_usd` is 10000.** Not any positive number.
- **`outputs/raw/` is immutable.** Never write, clobber, or stage into it.
- **History is append-only.** Do not amend, rebase, or recreate published
  Fable/Codex/Grok SHAs. Existing Claude worktrees for a PR are the working
  copy; do not start a parallel tree for that PR.
- **Claude authorship window.** Claude (Fable 5) only implemented on the
  night of 2026-08-23 through midnight 2026-08-24 (America/Chicago). On this
  stack that is the original objects `03b6557`, `b5b19078`, `883fbf8f`,
  `99ebca6a` (and the same-night trailer twin `8df3793`). Codex owns every
  follow-up after that window. Do **not** add `Co-authored-by: Claude` to
  restacks, GitHub rebases, Grok recovery merges, or any later commit.
  A copied Claude trailer on a later SHA is a restack, not new Claude work.

## Hugging Face card viewer schemas

Published cards declare their Dataset Viewer schema by hand, one JSON file per
dataset at `config/card-schemas/<hub-dataset-name>.json`. The format and the
rules live in `pipelines/card_schema.py`. Audit the set with:

```bash
python3 scripts/publish_grok46_hub.py schemas          # lists declared/undeclared
python3 scripts/publish_grok46_hub.py schemas --strict # nonzero while any gap remains
```

A dataset with no declaration publishes a card that says so. Never rewrite
historical raw JSONL to fix a viewer schema — declare the union on the card.

## Cursor Cloud specific instructions

Cloud agents should start from `.cursor/environment.json`, which builds
`.cursor/Dockerfile` (Ubuntu 24.04, git, sudo, Python 3). The install script
creates `.venv`, compiles the pipelines, runs unit tests, and runs the
operator smoke check.

Do not COPY the repo into the image. Cursor checks out the target commit.
Do not treat `outputs/raw/` as a scratch directory. Prefer the committed
fixtures and `driver.py smoke` for environment verification.
