# Tool-world recipes: deterministic environment, replay is the oracle.

# Check the pinned tool-world catalog loads and digests match (read-only)
tw-catalog-check:
    {{python}} pipelines/tool_world_cli.py catalog-check --json

# [WRITE] Generate a tool-world run under outputs/tool-world/<label>; refuses an existing destination
write-tw-generate label seed="1" count="3":
    #!/usr/bin/env bash
    set -euo pipefail
    case "{{label}}" in ""|*/*|*\\*|..|.) echo "refusing unsafe tool-world label: {{label}}" >&2; exit 2;; esac
    dest="outputs/tool-world/{{label}}"
    if [ -e "$dest" ] || [ -L "$dest" ]; then echo "refusing existing destination: $dest" >&2; exit 2; fi
    exec {{python}} pipelines/tool_world_cli.py generate --seed {{seed}} --count {{count}} --out "$dest" --json

# Replay every record of a tool-world run, e.g. `just tw-replay outputs/tool-world/<label>` (read-only)
tw-replay run:
    {{python}} pipelines/tool_world_cli.py replay "{{run}}" --json

# [WRITE] Re-pin tool-world catalog digests in place after a reviewed pack edit (only in-place writer here)
write-tw-repin:
    {{python}} pipelines/tool_world_cli.py catalog-check --write-pins --json

# Plan honest-stop generation with a dry run, no network or writes (read-only)
honest-stop-dry-run seed="1" count="4":
    {{python}} pipelines/honest_stop_cli.py generate --dry-run --seed {{seed}} --count {{count}}

# Plan an honest-stop export with a dry run, no writes (read-only)
honest-stop-export-dry-run:
    {{python}} pipelines/honest_stop_cli.py export --dry-run
