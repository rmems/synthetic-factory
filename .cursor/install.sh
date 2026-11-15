#!/usr/bin/env bash
# Idempotent Cloud Agent install: prefetch dependencies and compile the tree.
# Lint, unit tests, and operator smoke belong in GitHub Actions, not the snapshot build.
set -euo pipefail

python3 -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 15) else 1)' \
  || { echo "install.sh requires Python >= 3.15 (got $(python3 --version 2>&1))" >&2; exit 1; }

# Code-repair bwrap hides /workspace only when the harness workdir is outside it.
# Keep temp dirs on /tmp so a long agent session does not point TMPDIR under the repo.
export TMPDIR="${TMPDIR:-/tmp}"

python3 -m venv .venv
.venv/bin/python -m compileall -q pipelines tests .claude/skills/run-synthetic-factory/driver.py

# Rust sf-oracle: prefetch and compile only (toolchain 1.99.0, same as CI).
export CC=gcc
export CXX=g++
if ! command -v rustup >/dev/null 2>&1; then
  # Pinned rustup-init, same download and checksum as .agents/setup. The
  # checksum is only published for x86_64, matching the Cursor cloud image.
  readonly RUSTUP_VERSION=1.28.2
  readonly RUSTUP_SHA256=20a06e644b0d9bd2fbdbfd52d42540bdde820ea7df86e92e533c073da0cdd43c
  if [[ "$(uname -m)" != x86_64 ]]; then
    echo "install.sh requires x86_64 for the pinned rustup download (got $(uname -m))." >&2
    exit 1
  fi
  # rustup-init dispatches on argv[0]: the basename must start with
  # "rustup-init" or it runs in proxy mode instead of installing.
  installer_dir="$(mktemp -d)"
  installer="${installer_dir}/rustup-init"
  curl --fail --location --silent --show-error --proto '=https' --tlsv1.2 \
    "https://static.rust-lang.org/rustup/archive/${RUSTUP_VERSION}/x86_64-unknown-linux-gnu/rustup-init" \
    --output "$installer"
  printf '%s  %s\n' "$RUSTUP_SHA256" "$installer" | sha256sum --check --status
  chmod 0755 "$installer"
  "$installer" -y --no-modify-path --default-toolchain none --profile minimal
  rm -rf "$installer_dir"
fi
# shellcheck source=/dev/null
source "${HOME}/.cargo/env"
rustup toolchain install 1.99.0 \
  --profile minimal \
  --component rustfmt \
  --component clippy
rustup default 1.99.0
cargo +1.99.0 fetch --locked
cargo +1.99.0 build --locked -p sf-oracle
cargo +1.99.0 test --no-run --locked -p sf-oracle
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
    # Never replace an existing name, including a dangling symlink.
    if [[ -e "${dst}" || -L "${dst}" ]]; then
      continue
    fi
    sudo ln -sf "${src}" "${dst}"
  done
fi
