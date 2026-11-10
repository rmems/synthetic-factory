# Python test, lint and compile recipes (wrap the commands in CLAUDE.md).

# Run the full unit suite, read-only (respects TMPDIR; set it to a roomy dir)
test:
    #!/usr/bin/env bash
    set -euo pipefail
    if [ -z "${TMPDIR:-}" ]; then
      export TMPDIR=/tmp
      echo "test: TMPDIR was unset; using $TMPDIR (export TMPDIR to pick a roomier directory)"
    else
      echo "test: TMPDIR=$TMPDIR"
    fi
    exec {{python}} -m unittest discover -s tests -p 'test_*.py' -q -b

# Run one test module by bare name, e.g. `just test-module test_rights_policy`
test-module name:
    {{python}} -m unittest tests.{{name}}

# Run one fully-qualified test target, e.g. `just test-target tests.test_rights_policy.RightsPolicyTests`
test-target target:
    {{python}} -m unittest {{target}}

# Run one family of test modules by glob, e.g. `just test-family 'test_rights_*.py'`
test-family pattern:
    {{python}} -m unittest discover -s tests -p '{{pattern}}'

# Run the operator driver smoke check (read-only, temp-dir only)
smoke:
    {{python}} .claude/skills/run-synthetic-factory/driver.py smoke

# Compile all Python sources and tests without writing bytecode changes to git
compile:
    {{python}} -m compileall -q pipelines scripts tests .claude/skills/run-synthetic-factory/driver.py

# Run the gated ruff correctness rules exactly as CI runs them (ruff pin enforced)
lint:
    @ruff --version | grep -Fqx "ruff {{ruff_version}}" || { echo "expected ruff {{ruff_version}}; run: {{python}} -m pip install --only-binary ':all:' ruff=={{ruff_version}}" >&2; exit 1; }
    ruff check --no-cache --output-format=github --select F,E9,PLE,B --ignore PLE0605,B007,B008,B009,B010,B905 pipelines scripts tests .claude/skills/run-synthetic-factory/driver.py

# Run the ungated default ruff rule set (style findings, not CI-gated)
lint-style:
    ruff check pipelines tests

# Run one CI unittest shard with branch coverage, e.g. `just ci-shard 0` (coverage pin enforced)
ci-shard shard shards="4":
    @{{python}} -m coverage --version | grep -Fq "{{coverage_version}}" || { echo "expected coverage {{coverage_version}}; run: {{python}} -m pip install --only-binary ':all:' coverage=={{coverage_version}}" >&2; exit 1; }
    {{python}} scripts/ci_shard_tests.py --shard {{shard}} --shards {{shards}} --coverage
