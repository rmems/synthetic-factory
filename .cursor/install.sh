#!/usr/bin/env bash
# Idempotent Cloud Agent install: compile the tree and run the operator smoke check.
# Full unittest discovery (~5k tests, 30-40 min) belongs in GitHub Actions, not here.
set -euo pipefail

python3 -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 14) else 1)' \
  || { echo "install.sh requires Python >= 3.14 (got $(python3 --version 2>&1))" >&2; exit 1; }

# Code-repair bwrap hides /workspace only when the harness workdir is outside it.
# Keep temp dirs on /tmp so a long agent session does not point TMPDIR under the repo.
export TMPDIR="${TMPDIR:-/tmp}"

python3 -m venv .venv
.venv/bin/python -m compileall -q pipelines tests .claude/skills/run-synthetic-factory/driver.py
.venv/bin/python .claude/skills/run-synthetic-factory/driver.py smoke
