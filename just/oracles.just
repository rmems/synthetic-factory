# Parity-oracle recipes: availability is honest reporting, never a fallback.

# Report which parity oracles can run here: neuro, hardware and NIR (read-only)
oracle-availability:
    {{python}} pipelines/neuro_oracle.py
    {{python}} pipelines/hardware_parity.py availability
    {{python}} pipelines/nir_equivalence.py availability

# [WRITE] Generate oracle-grounded records into a NEW directory; refuses existing and outputs/raw
write-oracle-generate dest *args: (_refuse-new-destination dest)
    @dest_dir="$1"; shift; {{python}} pipelines/oracle_generate.py "$dest_dir" "$@"

# Validate oracle-grounded records by re-running each oracle (read-only)
oracle-validate run:
    {{python}} pipelines/oracle_validate.py --reproduce "$1"

# [WRITE] Generate hardware-parity records into a NEW directory; refuses existing and outputs/raw
write-hardware-generate dest round="1": (_refuse-new-destination dest)
    {{python}} pipelines/hardware_parity.py generate "$1" --round "$2"

# [WRITE] Generate NIR-equivalence records into a NEW directory; refuses existing and outputs/raw
write-nir-generate dest round="1": (_refuse-new-destination dest)
    {{python}} pipelines/nir_equivalence.py generate "$1" --round "$2"
