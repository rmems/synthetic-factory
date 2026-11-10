# Rust oracle recipes. Every recipe fails closed when the pinned toolchain
# is absent instead of falling through to whatever cargo is on PATH.

[private]
_require-rust:
    @rustup run {{rust_toolchain}} rustc --version >/dev/null 2>&1 || { echo "Rust {{rust_toolchain}} not installed; run: rustup toolchain install {{rust_toolchain}} --profile minimal --component rustfmt --component clippy" >&2; exit 1; }

# Check formatting of the Rust workspace with the pinned toolchain (read-only)
rust-fmt: _require-rust
    cargo +{{rust_toolchain}} fmt --all --check

# Lint the Rust workspace with clippy, warnings denied (read-only)
rust-clippy: _require-rust
    cargo +{{rust_toolchain}} clippy --locked --all-targets -- -D warnings

# Run the sf-oracle crate tests with the pinned toolchain
rust-test: _require-rust
    cargo +{{rust_toolchain}} test --locked -p sf-oracle

# Build the sf-oracle binary with the pinned toolchain
rust-build: _require-rust
    cargo +{{rust_toolchain}} build --locked -p sf-oracle

# Run the full Rust check CI runs: fmt, clippy, crate tests and build
rust-check: rust-fmt rust-clippy rust-test rust-build

# Exercise native oracle generation end-to-end via coverage (builds sf-oracle first)
oracle-e2e: rust-build
    @{{python}} -m coverage --version | grep -Fq "{{coverage_version}}" || { echo "expected coverage {{coverage_version}}; run: {{python}} -m pip install --only-binary ':all:' coverage=={{coverage_version}}" >&2; exit 1; }
    SF_ORACLE_RUST_BIN="${SF_ORACLE_RUST_BIN:-$PWD/target/debug/sf-oracle}" {{python}} -m coverage run -p -m unittest discover -s tests -p 'test_oracle_rust_end_to_end.py' -v
