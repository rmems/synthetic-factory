# Read-only operator audits on a run tree, plus the reviewed write/maintenance recipes.

# Census a run tree: JSON counts and mill mix, no writes
census run:
    {{python}} pipelines/census.py "$1"

# Census the committed mini-run fixture (read-only)
census-fixture:
    {{python}} pipelines/census.py tests/fixtures/mini-run

# Validate a run through the driver on a stable snapshot copy (read-only)
validate run:
    {{python}} .claude/skills/run-synthetic-factory/driver.py validate "$1"

# Validate a run tree directly with the shape gate, no manifest written (read-only)
validate-run run:
    {{python}} pipelines/validate_run.py "$1"

# Run all three driver audit layers on a stable snapshot copy (read-only)
audit run:
    {{python}} .claude/skills/run-synthetic-factory/driver.py audit "$1"

# Report per-factory frontier and next round for a run (read-only)
frontiers run:
    {{python}} .claude/skills/run-synthetic-factory/driver.py frontiers "$1"

# Report token-efficiency / early-stop status per factory (read-only)
token-efficiency run:
    {{python}} .claude/skills/run-synthetic-factory/driver.py token-efficiency "$1"

# Run the training-readiness audit on a run, e.g. `just training-audit <run> --strict` (read-only)
training-audit run *args:
    @run_dir="$1"; shift; exec {{python}} pipelines/training_audit.py "$run_dir" "$@"

# Report leftover mill mix in a run, e.g. `just leftover-mill <run> --strict` (read-only)
leftover-mill run *args:
    @run_dir="$1"; shift; exec {{python}} pipelines/leftover_mill.py "$run_dir" "$@"

# Deep-check records in a run: reward, spike order and ids (read-only)
check-records run:
    {{python}} pipelines/check_records.py "$1"

# Check the mill-script inventory classification (read-only)
mill-inventory-check:
    {{python}} pipelines/mill_script_inventory.py --check

# Validate VSET records or a manifest target, e.g. `just validate-vset <target> --oracle --pack <dir>` (read-only)
validate-vset target *args:
    @target_path="$1"; shift; exec {{python}} pipelines/validate_vset.py "$target_path" "$@"

# Report VSET fixture pin drift only, no writes (read-only)
vset-pins-check:
    {{python}} scripts/refresh_vset_fixture_pins.py --check

# [WRITE] Snapshot a run to the sibling <run>-<label> tree; refuses outputs/raw and an existing destination
write-snapshot run label:
    #!/usr/bin/env bash
    set -euo pipefail
    src="$1"; src="${src%/}"
    case "$2" in ""|*[!A-Za-z0-9._-]*|.*|*..*) echo "refusing unsafe snapshot label: $2" >&2; exit 2;; esac
    dest="$(dirname "$src")/$(basename "$src")-$2"
    {{python}} -c {{quote(_guard_raw_py)}} "$dest"
    {{python}} -c {{quote(_guard_exists_py)}} "$dest"
    exec {{python}} .claude/skills/run-synthetic-factory/driver.py snapshot "$src" "$2"

# [MAINTENANCE] Write manifest.json into an existing run with validate_run.py --write; refuses outputs/raw
maintain-run-manifest run: (_refuse-raw run)
    {{python}} pipelines/validate_run.py --write "$1"

# [WRITE] Clean a source run into a NEW cleaned tree; refuses an existing destination and outputs/raw
write-curate-identity source dest: (_refuse-new-destination dest)
    {{python}} pipelines/curate_identity.py "$1" --out "$2"

# [WRITE] Promote a raw run into a NEW cleaned tree; refuses an existing destination and outputs/raw
write-promote source dest: (_refuse-new-destination dest)
    {{python}} pipelines/promote.py "$1" "$2"

# [WRITE] Compose curation lanes into a NEW curated tree; refuses an existing destination and outputs/raw
write-compose source dest *args: (_refuse-new-destination dest)
    @src="$1"; dest_dir="$2"; shift 2; {{python}} pipelines/compose_curated.py "$src" "$dest_dir" "$@"

# [WRITE] Export a curated tree to a NEW export tree; refuses an existing destination and outputs/raw
write-export source dest *args: (_refuse-new-destination dest)
    @src_dir="$1"; dest_dir="$2"; shift 2; {{python}} pipelines/export_hf.py "$src_dir" "$dest_dir" "$@"

# [WRITE] Integrate a curation plan into a NEW cleaned tree; refuses an existing destination and outputs/raw
write-curate-integrate plan dest: (_refuse-new-destination dest)
    {{python}} pipelines/curate_gate.py integrate --plan "$1" --cleaned-out "$2"

# [WRITE] Promote a reviewed cleaned tree to a NEW curated tree; refuses an existing destination and outputs/raw
write-curate-promote cleaned review dest: (_refuse-new-destination dest)
    {{python}} pipelines/curate_gate.py promote --cleaned "$1" --review "$2" --curated-out "$3"

# [MAINTENANCE] Rewrite VSET fixture pins in place from the live registry/pack bytes (reviewed edits only)
maintain-vset-pins:
    {{python}} scripts/refresh_vset_fixture_pins.py
