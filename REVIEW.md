# Local Python CI

This file is the local review contract for Python changes. Run the gates from
the repository root before pushing a pull request. They mirror the `Python`,
`Python smoke`, Qodana, and Codecov jobs without mutating raw factory output.

## One-time setup

Use Python 3.14, matching GitHub Actions. Keep the coverage dependency local:

```bash
python3.14 -m venv .venv
. .venv/bin/activate
python -m pip install coverage==7.15.4
```

Do not put tokens in this file, shell history, or command output. GitHub reads
`CODECOV_TOKEN` and `QODANA_TOKEN` from repository secrets.

## Required Python gates

```bash
python -m compileall -q pipelines scripts tests .claude/skills/run-synthetic-factory/driver.py
python -m coverage erase
python -m coverage run -m unittest discover -s tests -p 'test_*.py' -v
python -m coverage report --show-missing
python -m coverage xml
python .claude/skills/run-synthetic-factory/driver.py smoke
python pipelines/census.py tests/fixtures/mini-run
```

The census must report exactly one parse failure. The mini-run intentionally
contains one malformed JSON record, so its structural validator must fail and
must identify a JSON parse error:

```bash
(
  set +e
  python pipelines/validate_run.py tests/fixtures/mini-run 2>validate.err
  status=$?
  set -e
  test "$status" -ne 0
  grep -F "JSON parse error" validate.err
)
```

Remove `validate.err` after checking it. `coverage.xml` is the same artifact the
Codecov action uploads and is intentionally ignored by Git.

## Local Qodana gate

Qodana must use the Python interpreter shipped in its Python image; otherwise
PyCharm reports false unresolved-stdlib and invalid-annotation findings. Docker
and the Qodana CLI are required for this optional local reproduction of CI:

```bash
qodana scan \
  --image jetbrains/qodana-python-community:2026.1 \
  --skip-pull \
  -e QODANA_PYTHON_PATH=/opt/miniconda3/bin/python3
```

The repository workflow uses the licensed `qodana-python` linter and its
`QODANA_TOKEN`; the token-free community image is only the local equivalent for
Python inspections. Qodana's separate sanity preflight is disabled because it
ignores the path exclusions for the repository's tested runtime imports and
suspends before producing useful results; the normal Python inspection profile
remains enabled. A newer local CLI may warn that its version differs from the
pinned 2026.1 image. In a linked Git worktree, Qodana may also warn that the
checkout's external Git administrative directory is not mounted; source
analysis still runs, but commit-diff metadata is unavailable in that local run.

## Review result

A change is locally review-ready only when compilation, all unit tests, coverage
generation, driver smoke, census expectations, and the Qodana detailed summary
pass. Report each result separately; do not call the PR green merely because one
gate passed.
