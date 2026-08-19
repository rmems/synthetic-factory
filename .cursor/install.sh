#!/usr/bin/env bash
# Idempotent Cloud Agent install: prepare a venv and prove the pipelines import.
set -euo pipefail

python3 -m venv .venv
.venv/bin/python -m compileall -q pipelines tests .claude/skills/run-synthetic-factory/driver.py
.venv/bin/python -m unittest discover -s tests -p 'test_*.py' -q
.venv/bin/python .claude/skills/run-synthetic-factory/driver.py smoke
