# Parity-oracle recipes: availability is honest reporting, never a fallback.

# Report which parity oracles can run here: neuro, hardware and NIR (read-only)
oracle-availability:
    {{python}} pipelines/neuro_oracle.py
    {{python}} pipelines/hardware_parity.py availability
    {{python}} pipelines/nir_equivalence.py availability

# [WRITE] Generate oracle-grounded records into a NEW directory; refuses existing and outputs/raw
write-oracle-generate dest *args:
    @case "{{dest}}" in outputs/raw|outputs/raw/*|*/outputs/raw|*/outputs/raw/*) echo "refusing outputs/raw destination: {{dest}}" >&2; exit 2;; esac; if [ -e "{{dest}}" ] || [ -L "{{dest}}" ]; then echo "refusing existing destination: {{dest}}" >&2; exit 2; fi
    {{python}} pipelines/oracle_generate.py "{{dest}}" {{args}}

# Validate oracle-grounded records by re-running each oracle (read-only)
oracle-validate run:
    {{python}} pipelines/oracle_validate.py --reproduce "{{run}}"

# [WRITE] Generate hardware-parity records into a NEW directory; refuses existing and outputs/raw
write-hardware-generate dest round="1":
    @case "{{dest}}" in outputs/raw|outputs/raw/*|*/outputs/raw|*/outputs/raw/*) echo "refusing outputs/raw destination: {{dest}}" >&2; exit 2;; esac; if [ -e "{{dest}}" ] || [ -L "{{dest}}" ]; then echo "refusing existing destination: {{dest}}" >&2; exit 2; fi
    {{python}} pipelines/hardware_parity.py generate "{{dest}}" --round {{round}}

# [WRITE] Generate NIR-equivalence records into a NEW directory; refuses existing and outputs/raw
write-nir-generate dest round="1":
    @case "{{dest}}" in outputs/raw|outputs/raw/*|*/outputs/raw|*/outputs/raw/*) echo "refusing outputs/raw destination: {{dest}}" >&2; exit 2;; esac; if [ -e "{{dest}}" ] || [ -L "{{dest}}" ]; then echo "refusing existing destination: {{dest}}" >&2; exit 2; fi
    {{python}} pipelines/nir_equivalence.py generate "{{dest}}" --round {{round}}
