"""The record envelope contract: closed vocabularies and the reserved-key scan.

Every other ``record_*`` module checks records against the vocabulary defined
here. The envelope keeps generator-authored and oracle-authored content in
disjoint subtrees; these constants say exactly which keys belong to whom, and
the reserved-key scan is how a generator is caught authoring measurement-shaped
content it must never produce.
"""

SCHEMA_ID = "oracle-grounded/v1"
GENERATOR_SECTIONS = ("generator", "scenario", "intervention", "candidate_prediction")
ENVELOPE_KEYS = (
    "schema",
    "id",
    "family",
    "generator",
    "scenario",
    "intervention",
    "candidate_prediction",
    "proposal_hash",
    "oracle",
    "result",
    "result_hash",
    "provenance",
    "validation",
    "meta",
)
ORACLE_KEYS = (
    "id",
    "type",
    "implementation",
    "authority",
    "requested_runtime",
    "runtime_bound",
    "repo",
    "commit",
    "dirty",
    "module",
    "module_digest",
    "version",
    "configuration",
    "seed",
    "units",
    "stages",
    "availability",
)
# The oracle, provenance, and meta blocks are authoritative execution
# provenance that no content hash covers, so their vocabularies are closed: a
# sibling key nothing here wrote (an "attestation", say) would be an
# unsupported provenance claim.
ORACLE_ALLOWED_KEYS = frozenset(ORACLE_KEYS) | {"description"}
PROVENANCE_ALLOWED_KEYS = frozenset(
    {"kind", "claimed", "oracle_grounded", "generator_authored", "oracle_authored"}
)
META_ALLOWED_KEYS = frozenset({"factory", "round", "tags"})
STAGE_ALLOWED_KEYS = frozenset(
    {
        "stage",
        "requested_runtime",
        "implementation",
        "oracle_id",
        "version",
        "module_digest",
        "runtime_commit",
        "executable",
    }
)
# Measurement-shaped keys a generator must never author. The scan is over the
# generator subtrees only; the oracle is of course free to use them.
RESERVED_GENERATOR_KEYS = frozenset(
    {
        "ground_truth",
        "measured",
        "module_digest",
        "oracle_commit",
        "oracle_result",
        "produced_by",
        "result",
        "result_hash",
    }
)
# Same vocabulary as schemas/provenance.md. `real` is never emitted.
ALLOWED_PROVENANCE_KIND = frozenset({"designed", "simulated", "hil", "unknown"})
TRAINING_PROVENANCE_KIND = frozenset({"designed", "simulated", "hil"})


class GenerationError(RuntimeError):
    """A record could not be produced; the caller decides whether to skip."""


# One reserved key already rejects the record, so the scan stops collecting
# paths at this cap: a schema-open stored payload full of reserved keys must
# not be able to turn path collection into a multi-megabyte finding string.
MAX_RESERVED_KEY_HITS = 25


def _reserved_hits_in_mapping(value, path, hits):
    for key, item in value.items():
        if len(hits) >= MAX_RESERVED_KEY_HITS:
            break
        here = f"{path}.{key}" if path else str(key)
        if key in RESERVED_GENERATOR_KEYS:
            hits.append(here)
        _collect_reserved_key_hits(item, here, hits)


def _collect_reserved_key_hits(value, path, hits):
    if isinstance(value, dict):
        _reserved_hits_in_mapping(value, path, hits)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            if len(hits) >= MAX_RESERVED_KEY_HITS:
                break
            _collect_reserved_key_hits(item, f"{path}[{index}]", hits)


def _reserved_key_hits(value, path=""):
    """Paths of oracle-reserved keys, capped at ``MAX_RESERVED_KEY_HITS``."""
    hits = []
    _collect_reserved_key_hits(value, path, hits)
    return hits


def _reserved_key_listing(hits):
    """Human-readable path list, marking when the bounded scan stopped early."""
    listed = ", ".join(sorted(hits))
    if len(hits) >= MAX_RESERVED_KEY_HITS:
        listed += ", ... (scan capped)"
    return listed


def proposal_of(record):
    """Exactly the generator-authored subtree that ``proposal_hash`` covers."""
    return {section: record.get(section) for section in GENERATOR_SECTIONS}
