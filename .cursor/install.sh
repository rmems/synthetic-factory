#!/usr/bin/env bash
# Idempotent Cloud Agent install: prefetch dependencies and compile the tree.
# Lint, unit tests, and operator smoke belong in GitHub Actions, not the snapshot build.
set -euo pipefail

python3 -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 14) else 1)' \
  || { echo "install.sh requires Python >= 3.14 (got $(python3 --version 2>&1))" >&2; exit 1; }

# Code-repair bwrap hides /workspace only when the harness workdir is outside it.
# Keep temp dirs on /tmp so a long agent session does not point TMPDIR under the repo.
export TMPDIR="${TMPDIR:-/tmp}"

python3 -m venv .venv
.venv/bin/python -m compileall -q pipelines tests .claude/skills/run-synthetic-factory/driver.py

# Rust sf-oracle: prefetch and compile only (toolchain 1.98.1, same as CI).
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
cargo +1.98.1 build --locked -p sf-oracle
cargo +1.98.1 test --no-run --locked -p sf-oracle
export SF_ORACLE_RUST_BIN="${PWD}/target/debug/sf-oracle"

# Login shells and non-interactive steps should find rustup without sourcing ~/.cargo/env.
CARGO_BIN="${HOME}/.cargo/bin"
if [[ -d "${CARGO_BIN}" ]]; then
  if [[ ! -f /etc/profile.d/cursor-cargo.sh ]]; then
    sudo tee /etc/profile.d/cursor-cargo.sh >/dev/null <<'EOF'
# Cursor synthetic-factory cloud install: rustup on PATH for login shells.
if [ -d "${HOME}/.cargo/bin" ]; then
  export PATH="${HOME}/.cargo/bin:${PATH}"
fi
EOF
    sudo chmod 644 /etc/profile.d/cursor-cargo.sh
  fi
  for tool in cargo rustc rustup rustfmt clippy-driver cargo-fmt cargo-clippy; do
    src="${CARGO_BIN}/${tool}"
    dst="/usr/local/bin/${tool}"
    [[ -x "${src}" ]] || continue
    if [[ -e "${dst}" ]]; then
      if [[ -L "${dst}" ]] && [[ "$(readlink -f "${dst}")" = "$(readlink -f "${src}")" ]]; then
        continue
      fi
      continue
    fi
    sudo ln -sf "${src}" "${dst}"
  done
fi
