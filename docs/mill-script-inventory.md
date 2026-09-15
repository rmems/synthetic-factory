# Mill-script inventory — production vs archived generators

> Policy: `config/MILL-SCRIPT-INVENTORY.json`
> Guard: `pipelines/mill_script_inventory.py`
> Issue: [rmems/synthetic-factory#211](https://github.com/rmems/synthetic-factory/issues/211) step 5 / Linear RM-1341

## 1. What this table is

A mill *generator* is a one-shot leftover-round script (`*_mill.py`,
`*_leftover*_r*.py`, `scripts/*_mill/`). Those scripts live on
`origin/legacy-mill-lane` and as machine-local copies; they are not the mill
*detectors* on main (`leftover_mill.py`, `mill_family.py`, `compose_mill.py`).

The inventory classifies every matching **tracked** script as:

| classification | quality_scope | meaning |
|---|---|---|
| `production` | `production` | core detector, cleaned mill-family package, or their tests |
| `retained_historical_generator` | `archived` | recoverable leftover mill; do not vendor or import |
| `removable_duplicate` | `archived` | classified duplicate; none exist on main |

A new path matching `match_patterns` fails `python3 pipelines/mill_script_inventory.py --check`
until it has a row. That is the guard. There is no blanket `*_mill.py` or
`experiments/` suppression: those patterns hit `leftover_mill.py` and the
tracked harvest notes.

## 2. Where historical generators live

```bash
git fetch origin legacy-mill-lane
git show origin/legacy-mill-lane:experiments/srl_r6110_leftover3_mill.py | head
```

Mill-family packages under `pipelines/<family>/` AST-extract catalogs from those
bytes and pin path, SHA-256, and commit. Raw JSONL is not rewritten. Git
history is not rewritten.

## 3. Quality scope (qlty before / after)

#211 measured mill/leftover generators as 223 per-file qlty hits and most of
the similar-code blocks when a local `qlty check` walked untracked workstation
files (1,931 issues vs 285 on tracked `pipelines scripts tests`). B6 named
those generators in `.gitignore` but used `pipelines/*_mill.py` and
`experiments/`, which `git check-ignore --no-index` matches against
`leftover_mill.py`, `compose_mill.py`, `training_audit_mill.py`, and
`experiments/2026-08-19-quality-report.md`.

| measurement | before this slice | after |
|---|---|---|
| gitignore hits on production `*_mill.py` detectors | 3 | **0** |
| gitignore hits on tracked `experiments/*.md` harvest notes | 3 | **0** |
| gitignore hits on `experiments/*_mill.py` generators | yes (via `experiments/`) | **yes** (explicit mill/leftover/`_gen`/`plants` globs) |
| qlty `exclude_patterns` for leftover generators | none (gitignore only) | reviewed globs from the inventory |
| qlty hits on `tests/test_leftover_mill.py` / `leftover_mill.py` | would fire under a blanket `*leftover*` exclude | **not excluded** |
| tracked `pipelines scripts tests` qlty issue count | unchanged dataset; generators stay untracked | unchanged — archived copies still not on main |

Production entrypoints (`scripts/publish_grok46_hub.py`,
`pipelines/curate_preferences.py`, compose/export) keep importing
`leftover_mill`. They must not import a module named in
`historical_generator_policy.example_paths`.

## 4. Adding a mill script

1. Classify it in `config/MILL-SCRIPT-INVENTORY.json` (`scripts` if it is
   tracked on main; otherwise it is covered by `historical_generator_policy`).
2. If it is archived, add a quality-scope glob only if the existing reviewed
   patterns do not already match — never `**/*_mill.py`.
3. Run `python3 pipelines/mill_script_inventory.py --check` and
   `python3 -m unittest tests.test_mill_script_inventory`.
