# Hugging Face publication checks. Read-only; Hub-writing publisher commands
# (snapshot/create/upload/collect/all) stay raw in README.md on purpose.

# Audit card viewer schemas, e.g. `just hub-schemas --strict` (read-only, reads neither root)
hub-schemas *args:
    {{python}} scripts/publish_grok46_hub.py schemas {{args}}

# Report local Hub mirror / factory source counts using the root variables (read-only)
hub-status:
    #!/usr/bin/env bash
    set -euo pipefail
    args=()
    if [ -n "{{hf_root}}" ]; then args+=(--hf-root "{{hf_root}}"); fi
    if [ -n "{{factory_root}}" ]; then args+=(--factory-root "{{factory_root}}"); fi
    exec {{python}} scripts/publish_grok46_hub.py status "${args[@]}"

# Verify public Hub releases, e.g. `just hf-verify --repo rmems/<dataset>` (network, read-only)
hf-verify *args:
    {{python}} pipelines/verify_hf_release.py {{args}}
