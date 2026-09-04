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

## Generator rule

Frontier hosted-model outputs (Claude Fable 5, GPT-5.6-Sol, Grok 4.6, Muse
Spark) are research-only under #161 (`intended_use: research_only`,
`project_training_policy: blocked`). Training-candidate data comes from
procedural generators, deterministic in-repo simulators, and later DeepSeek /
Nemotron lanes (#170). Every generator, in either lane, follows this rule:

- **No generator-specific literals in shared pipelines.** `round_txn`,
  `curate_*`, `compose_*`, and `export_hf` read `config/FACTORY-REGISTRY.json`
  only. The `grok-4.6` literal in `pipelines/round_txn.py` is tracked as #174;
  do not copy the pattern.
- **One generator = one registry row + one package under `generators/` + one
  fixture under `tests/fixtures/` + one test module.** Missing any of the four
  means the generator is not onboarded.
- **Provenance stamps carry `generator`, `generator_version` (the source
  digest), `catalog_digest`, and `catalog_authorship`.** A catalog authored in
  a frontier session makes every record research-only (#173); only
  human-authored or permissively sourced catalogs with an authorship
  attestation yield training candidates.
- **Generators never hop factories or rewrite `meta.factory`.** A record is
  published under the factory it was generated for; a mismatch is quarantined
  by identity, not patched.
- **`outputs/raw/` stays immutable.** Generators append new rounds through the
  transactional round path and never edit published bytes.
- **The prompt-driven lane is legacy.** Prompts pasted into a hosted chat
  produce research-only records; do not scale that lane to accumulate tokens.

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
When even a declared union cannot describe a record honestly, the record is
defective, not the schema: escalate through the quarantine-ledger path
(`KIND_MIX_QUARANTINE` in `pipelines/leftover_mill.py`, documented in
`docs/leftover-mill-quarantine.md`) — add the record's provenance to the
ledger, open a tracking issue so the operator can review the quarantine, and
let the published card report the exclusion. Both routes keep the raw bytes
untouched.

## Cursor Cloud specific instructions

Cloud agents should start from `.cursor/environment.json`, which builds
`.cursor/Dockerfile` (Ubuntu 24.04, git, sudo, Python 3). The install script
creates `.venv`, compiles the pipelines, runs unit tests, and runs the
operator smoke check.

Do not COPY the repo into the image. Cursor checks out the target commit.
Do not treat `outputs/raw/` as a scratch directory. Prefer the committed
fixtures and `driver.py smoke` for environment verification.
