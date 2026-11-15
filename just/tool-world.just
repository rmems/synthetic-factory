# Tool-world recipes: deterministic environment, replay is the oracle.

# Check the pinned tool-world catalog loads and digests match (read-only)
tw-catalog-check:
    {{python}} pipelines/tool_world_cli.py catalog-check --json

# [WRITE] Generate a tool-world run under outputs/tool-world/<label>; refuses an existing destination
write-tw-generate label seed="1" count="3":
    #!/usr/bin/env bash
    set -euo pipefail
    case "$1" in ""|*[!A-Za-z0-9._-]*|.*|*..*) echo "refusing unsafe tool-world label: $1" >&2; exit 2;; esac
    case "$2" in ""|*[!0-9]*) echo "refusing non-numeric seed: $2" >&2; exit 2;; esac
    case "$3" in ""|*[!0-9]*) echo "refusing non-numeric count: $3" >&2; exit 2;; esac
    dest="outputs/tool-world/$1"
    {{python}} -c {{quote(_guard_raw_py)}} "$dest"
    {{python}} -c {{quote(_guard_exists_py)}} "$dest"
    exec {{python}} pipelines/tool_world_cli.py generate --seed "$2" --count "$3" --out "$dest" --json

# Replay every record of a tool-world run, e.g. `just tw-replay outputs/tool-world/<label>` (read-only)
tw-replay run:
    {{python}} pipelines/tool_world_cli.py replay "$1" --json

# [MAINTENANCE] Re-pin tool-world catalog digests in place after a reviewed pack edit (fixed tracked file)
maintain-tw-catalog-pins:
    {{python}} pipelines/tool_world_cli.py catalog-check --write-pins --json

# Plan honest-stop generation with a dry run, no network or writes (read-only)
honest-stop-dry-run seed="1" count="4":
    {{python}} pipelines/honest_stop_cli.py generate --dry-run --seed "$1" --count "$2"

# Plan an honest-stop export with a dry run, no writes (read-only)
honest-stop-export-dry-run:
    {{python}} pipelines/honest_stop_cli.py export --dry-run
