# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repository is

A bounded synthetic-data factory: stdlib-only Python CLIs under `pipelines/`, a
reviewed factory registry in `config/FACTORY-REGISTRY.json`, schemas and policy
mappings in `schemas/`, and an operator driver at
`.claude/skills/run-synthetic-factory/driver.py`. There is no service to boot
and no third-party runtime dependency. Dataset payloads live outside git
(`outputs/raw/`, `outputs/cleaned/`, `outputs/curated/` are gitignored) and are
published to Hugging Face separately.

`AGENTS.md` is authoritative for the review contracts (fail-closed behaviours
that look like bugs; cite that section rather than "fixing" them), the Claude
authorship window, the generator rule, and the card viewer-schema rules — read
it before touching `pipelines/`. `README.md`
carries the project goal, the rights lanes, and the pipeline command reference.

## Commands

```bash
# Full unit suite (about 2,800 tests, ~70 s) and the operator smoke check; both run in CI
python3 -m unittest discover -s tests -p 'test_*.py' -q
python3 .claude/skills/run-synthetic-factory/driver.py smoke

# One module, one class, one test (tests put pipelines/ on sys.path themselves)
python3 -m unittest tests.test_rights_policy
python3 -m unittest tests.test_rights_policy.RightsPolicyTests
python3 -m unittest tests.test_rights_policy.RightsPolicyTests.test_committed_policy_is_loaded_and_bound_to_its_exact_bytes
python3 -m unittest discover -s tests -p 'test_rights_*.py'   # one family of modules

# Also run by CI (python.yml, python-smoke.yml)
python -m compileall -q pipelines scripts tests .claude/skills/run-synthetic-factory/driver.py
python3 pipelines/census.py tests/fixtures/mini-run   # validate_run.py on this fixture exits nonzero by design

# Lint: ruff is configured in pyproject.toml (py312, line length 100) but not run in CI
ruff check pipelines tests

# Operator audits on a run tree (all read-only)
python3 pipelines/training_audit.py [--strict] [--markdown] <run_dir>
python3 pipelines/leftover_mill.py [--strict] <run_dir>
python3 .claude/skills/run-synthetic-factory/driver.py validate|audit|frontiers|snapshot|token-efficiency <run_dir>

# Hugging Face: card viewer-schema audit and public release verification (network)
python3 scripts/publish_grok46_hub.py schemas            # --strict exits nonzero while any gap remains
python3 pipelines/verify_hf_release.py [--repo rmems/<dataset>]
```

CI runs the unit suite with branch coverage on Python 3.14 (`pyproject.toml`
still says `>=3.12`), the smoke check, Qodana (`qodana.yaml` documents the
deliberate inspection exclusions), and a scheduled, path-filtered Hub release
verification. CodeScene, Codacy, qlty (`.qlty/qlty.toml`, `smells.mode =
"block"`) and Codecov review every PR; the owner wants findings fixed by
refactoring, not suppressed.

## Architecture

### Data flow

```text
outputs/raw/<run>/<factory-slug>/batch-rNN.jsonl    append-only, immutable source of truth
        │  round_txn.py: reserve → stage → validate → publish; a round becomes visible when
        │  ROUND-rNN.complete.json is linked in, and existing paths are left untouched
        ▼
census.py · validate_run.py · check_records.py · training_audit.py    read-only reports and gates
        │
        ▼
curate_* lanes: identity, bridge, preferences, coding | agentic, rewards, tags    pure record transforms
        │  compose_curated.py applies them in one documented order into a brand-new tree
        ▼
outputs/curated/<label>/{records/, manifest/, COMPOSE.json}
        │  export_hf.py: refuses unless the training audit reports training_ready,
        │  then replays the compose contract from every source line before writing
        ▼
data/curated · data/viewer/records.parquet · data/splits · provenance.json · EVAL_PROTOCOL.md
```

`curate_gate.py integrate|promote` is the reviewed path over the same lanes: it
composes from an integration plan, records a stratified human-review sample,
and promotes only when every sampled record has a verdict.
`scripts/publish_grok46_hub.py` snapshots published rounds into `~/rmems/hf/`
and writes Hub cards from `config/card-schemas/`; `pipelines/verify_hf_release.py`
is the authority that proves the public release contract still holds.
`training_ready` is a structural and quality verdict, not training
eligibility — that is `project_training_policy: allowed` on a registry row,
and no row carries it yet.

### Invariants that shape every module

- **Fail closed; write only to new destinations.** The cleaned, curated,
  compose, export, and promotion writers target a brand-new destination and
  refuse one that exists (pick a new label rather than clearing the old tree);
  `raw_tree_guard.py` refuses any write that names or aliases `outputs/raw/`.
  The one regenerated file is the `NEXT_ROUND.json` index written by
  `next_round.py --write-index`, which is an index, not a record. Unknown
  provenance, an unknown record kind, a missing mapping, or a rights field
  that drifts from the loaded policy is a loud error rather than a default.
- **The registry is the identity authority.** `config/FACTORY-REGISTRY.json`
  (`factory-registry-v0.2`) resolves exact `path_id` then exact
  `payload_factory` to a row carrying `record_kinds`, provider/channel,
  `rights_profile_id`, `intended_use`, and `project_training_policy`.
  Onboarding a generator needs a reviewed row *and* a matching
  `(generator, generator_version)` entry in `_REVIEWED_GENERATOR_RIGHTS`
  (`pipelines/curate_identity.py`); the loader rejects one without the other.
  Today every row is `research_only` / `blocked` (hosted-frontier profile).
- **Record kind comes from the payload, not the directory.**
  `record_kind.classify_kind` is the single classifier (order: thalamic,
  preference, bridge_pair, safety_case, multi_agent, episode). "Mill mix" — a
  record whose `meta.factory`, id prefix, or goal family belongs to another
  lane — is resolved by `mill_family.py`, reported by census, and quarantined by
  `curate_agentic.py`; the literal `leftover` in an id is not the test
  (`leftover_mill.py`).
- **Policy is data.** `schemas/reward-ontology-v1.mapping.json` and
  `schemas/rights-policy-v1.mapping.json` are loaded and strictly validated at
  import by `reward_*` / `rights_*`; `schemas/tag-taxonomy-v1.json` is the
  default taxonomy path. Do not lazy-load a mapping to make an import cheap.
- **Exact JSON.** `exact_json` / `strict_jsonl` keep decimal tokens and reject
  non-strict input; digests and manifests are computed over those bytes, so
  re-serialize a payload only through `exact_json`, not `json.dumps`.

### Import conventions in `pipelines/`

Most modules work both as a direct CLI (`python3 pipelines/x.py`, which puts
`pipelines/` on `sys.path` and does `import sibling`) and as a package child
(`from pipelines import x`, which does `from . import sibling`) by opening
with the same prelude:

```python
if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling
    _assert_direct_sibling("x")
    from . import sibling as _sibling
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)("x")
    import sibling as _sibling
```

`pipelines/__init__.py` binds the direct-name and package-name copies to one
module object so classes such as the exact-JSON decimal token keep one
identity. Copy the prelude from a sibling when adding a module; a package child
that others import both ways also needs a loader in `_PACKAGE_SIBLING_LOADERS`.
Fourteen older modules are direct-execution only because they import siblings
by bare name (`next_round`, `quality_gate_audit`, `quality_gate_embedding`,
`card_schema`, `card_schema_validate`, `card_schema_yaml`, `tag_io`,
`tag_jsonl`, `tag_record`, `tag_regex`, `tag_taxonomy`, `tag_write`,
`verify_execution`, `verify_execution_shapes`); `import pipelines.next_round`
raises `ModuleNotFoundError`. That is why `driver.py` and
`scripts/publish_grok46_hub.py` insert `pipelines/` into `sys.path` before
importing (`qodana.yaml` documents the resulting inspection exclusion).

Large features are split into many small sibling modules by responsibility
(`compose_curated_*`, `export_*`, `rights_*`, `mill_*`). `compose_curated.py`
is a compatibility facade whose adapters read their `_name` seams through the
live module namespace so tests can patch `compose_curated.<name>`
(`tests/test_compose_curated_facade_contract.py` pins that). Keep new splits
responsibility-shaped rather than extracting helpers by size.

### Tests and fixtures

`tests/` has one module per pipeline concern plus contract tests. Fixtures
under `tests/fixtures/` are small run trees (`mini-run`, `rounds`,
`preference-arms`, `card-schema`, …); tests that exercise writers build their
trees in temporary directories because raw trees are immutable.

### Work tracking and environments

Issues are tracked with Beads (`bd`) mirrored to GitHub issues
(`.claude/skills/plan-github-issue/SKILL.md`); do not add markdown TODO lists.
Cursor Cloud agents build from `.cursor/environment.json` + `.cursor/Dockerfile`;
do not COPY the repo into the image and do not treat `outputs/raw/` as scratch.
