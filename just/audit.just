# Read-only operator audits on a run tree, plus the `write-*` curation lanes.

# Census a run tree: JSON counts and mill mix, no writes
census run:
    {{python}} pipelines/census.py "{{run}}"

# Census the committed mini-run fixture (read-only)
census-fixture:
    {{python}} pipelines/census.py tests/fixtures/mini-run

# Validate a run through the driver on a stable snapshot copy (read-only)
validate run:
    {{python}} .claude/skills/run-synthetic-factory/driver.py validate "{{run}}"

# Validate a run tree directly with the shape gate, no manifest written (read-only)
validate-run run:
    {{python}} pipelines/validate_run.py "{{run}}"

# Run all three driver audit layers on a stable snapshot copy (read-only)
audit run:
    {{python}} .claude/skills/run-synthetic-factory/driver.py audit "{{run}}"

# Report per-factory frontier and next round for a run (read-only)
frontiers run:
    {{python}} .claude/skills/run-synthetic-factory/driver.py frontiers "{{run}}"

# Report token-efficiency / early-stop status per factory (read-only)
token-efficiency run:
    {{python}} .claude/skills/run-synthetic-factory/driver.py token-efficiency "{{run}}"

# Run the training-readiness audit on a run, e.g. `just training-audit <run> --strict` (read-only)
training-audit run *args:
    {{python}} pipelines/training_audit.py {{args}} "{{run}}"

# Report leftover mill mix in a run, e.g. `just leftover-mill <run> --strict` (read-only)
leftover-mill run *args:
    {{python}} pipelines/leftover_mill.py {{args}} "{{run}}"

# Deep-check records in a run: reward, spike order and ids (read-only)
check-records run:
    {{python}} pipelines/check_records.py "{{run}}"

# Check the mill-script inventory classification (read-only)
mill-inventory-check:
    {{python}} pipelines/mill_script_inventory.py --check

# Validate VSET records or a manifest target (read-only)
validate-vset target *args:
    {{python}} pipelines/validate_vset.py {{args}} "{{target}}"

# Report VSET fixture pin drift only, no writes (read-only)
vset-pins-check:
    {{python}} scripts/refresh_vset_fixture_pins.py --check

# [WRITE] Snapshot a run to the sibling <run>-<label> tree; refuses an existing destination
write-snapshot run label:
    #!/usr/bin/env bash
    set -euo pipefail
    src="{{run}}"; src="${src%/}"
    case "{{label}}" in ""|*/*|*\\*|..|.) echo "refusing unsafe snapshot label: {{label}}" >&2; exit 2;; esac
    dest="$(dirname "$src")/$(basename "$src")-{{label}}"
    if [ -e "$dest" ] || [ -L "$dest" ]; then echo "refusing existing destination: $dest" >&2; exit 2; fi
    exec {{python}} .claude/skills/run-synthetic-factory/driver.py snapshot "$src" "{{label}}"

# [WRITE] Write manifest.json into a named run with validate_run.py --write (in-place; refuses outputs/raw)
write-validate-manifest run:
    @case "{{run}}" in outputs/raw|outputs/raw/*|*/outputs/raw|*/outputs/raw/*) echo "refusing outputs/raw destination: {{run}}" >&2; exit 2;; esac
    {{python}} pipelines/validate_run.py --write "{{run}}"

# [WRITE] Clean a source run into a NEW cleaned tree; refuses an existing destination and outputs/raw
write-curate-identity source dest:
    @case "{{dest}}" in outputs/raw|outputs/raw/*|*/outputs/raw|*/outputs/raw/*) echo "refusing outputs/raw destination: {{dest}}" >&2; exit 2;; esac; if [ -e "{{dest}}" ] || [ -L "{{dest}}" ]; then echo "refusing existing destination: {{dest}}" >&2; exit 2; fi
    {{python}} pipelines/curate_identity.py "{{source}}" --out "{{dest}}"

# [WRITE] Promote a raw run into a NEW cleaned tree; refuses an existing destination and outputs/raw
write-promote source dest:
    @case "{{dest}}" in outputs/raw|outputs/raw/*|*/outputs/raw|*/outputs/raw/*) echo "refusing outputs/raw destination: {{dest}}" >&2; exit 2;; esac; if [ -e "{{dest}}" ] || [ -L "{{dest}}" ]; then echo "refusing existing destination: {{dest}}" >&2; exit 2; fi
    {{python}} pipelines/promote.py "{{source}}" "{{dest}}"

# [WRITE] Compose curation lanes into a NEW curated tree; refuses an existing destination and outputs/raw
write-compose source dest *args:
    @case "{{dest}}" in outputs/raw|outputs/raw/*|*/outputs/raw|*/outputs/raw/*) echo "refusing outputs/raw destination: {{dest}}" >&2; exit 2;; esac; if [ -e "{{dest}}" ] || [ -L "{{dest}}" ]; then echo "refusing existing destination: {{dest}}" >&2; exit 2; fi
    {{python}} pipelines/compose_curated.py "{{source}}" "{{dest}}" {{args}}

# [WRITE] Export a curated tree to a NEW export tree; refuses an existing destination and outputs/raw
write-export source dest *args:
    @case "{{dest}}" in outputs/raw|outputs/raw/*|*/outputs/raw|*/outputs/raw/*) echo "refusing outputs/raw destination: {{dest}}" >&2; exit 2;; esac; if [ -e "{{dest}}" ] || [ -L "{{dest}}" ]; then echo "refusing existing destination: {{dest}}" >&2; exit 2; fi
    {{python}} pipelines/export_hf.py "{{source}}" "{{dest}}" {{args}}

# [WRITE] Integrate a curation plan into a NEW cleaned tree; refuses an existing destination and outputs/raw
write-curate-integrate plan dest:
    @case "{{dest}}" in outputs/raw|outputs/raw/*|*/outputs/raw|*/outputs/raw/*) echo "refusing outputs/raw destination: {{dest}}" >&2; exit 2;; esac; if [ -e "{{dest}}" ] || [ -L "{{dest}}" ]; then echo "refusing existing destination: {{dest}}" >&2; exit 2; fi
    {{python}} pipelines/curate_gate.py integrate --plan "{{plan}}" --cleaned-out "{{dest}}"

# [WRITE] Promote a reviewed cleaned tree to a NEW curated tree; refuses an existing destination and outputs/raw
write-curate-promote cleaned review dest:
    @case "{{dest}}" in outputs/raw|outputs/raw/*|*/outputs/raw|*/outputs/raw/*) echo "refusing outputs/raw destination: {{dest}}" >&2; exit 2;; esac; if [ -e "{{dest}}" ] || [ -L "{{dest}}" ]; then echo "refusing existing destination: {{dest}}" >&2; exit 2; fi
    {{python}} pipelines/curate_gate.py promote --cleaned "{{cleaned}}" --review "{{review}}" --curated-out "{{dest}}"

# [WRITE] Rewrite VSET fixture pins in place from the live registry/pack bytes (reviewed edits only)
write-vset-pins:
    {{python}} scripts/refresh_vset_fixture_pins.py
