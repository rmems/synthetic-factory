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

# Rust sf-oracle (same toolchain and gates as .github/workflows/python.yml).
export CC=gcc
export CXX=g++
if ! command -v rustup >/dev/null 2>&1; then
  curl -sSf https://sh.rustup.rs | sh -s -- -y --default-toolchain 1.98.1 --profile minimal
fi
# shellcheck source=/dev/null
source "${HOME}/.cargo/env"
rustup toolchain install 1.98.1 \
  --profile minimal \
  --component rustfmt \
  --component clippy
rustup default 1.98.1
cargo +1.98.1 fetch --locked
cargo +1.98.1 fmt --all --check
cargo +1.98.1 clippy --locked --all-targets -- -D warnings
cargo +1.98.1 test --locked -p sf-oracle
cargo +1.98.1 build --locked -p sf-oracle
export SF_ORACLE_RUST_BIN="${PWD}/target/debug/sf-oracle"
.venv/bin/python -m unittest discover -s tests -p 'test_oracle_rust_end_to_end.py' -q
