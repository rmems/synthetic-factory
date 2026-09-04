"""Vocabularies and shape predicates of the parity record contract.

Split out of ``parity_contract`` by responsibility (CodeScene: Overall Code
Complexity); every name is re-exported from ``parity_contract`` so existing
``contract.<name>`` readers resolve unchanged. This module owns what the
parity families decide for themselves and every other sibling reads: the
contract version, the record kinds and their dataset/schema pins, the verdict
and reason-code vocabularies, the oracle-only keys, the envelope key list, and
the three shape predicates the block checks are written against.
"""

from __future__ import annotations


CONTRACT_VERSION = "1.0.0"

KIND_HARDWARE_PARITY = "hardware_parity"
KIND_NIR_EQUIVALENCE = "nir_equivalence"
RECORD_KINDS = (KIND_HARDWARE_PARITY, KIND_NIR_EQUIVALENCE)

DATASET_FOR_KIND = {
    KIND_HARDWARE_PARITY: "hardware-parity-spike-trajectories",
    KIND_NIR_EQUIVALENCE: "nir-cross-runtime-equivalence",
}

SCHEMA_VERSION_FOR_KIND = {
    KIND_HARDWARE_PARITY: "1.0.0",
    KIND_NIR_EQUIVALENCE: "1.0.0",
}

# `match` and `mismatch` are the two evidence-bearing verdicts. `unsupported`
# means an oracle refused a construct on purpose (still evidence).
# `inconclusive` means no oracle pair executed -- never a pass.
VERDICT_MATCH = "match"
VERDICT_MISMATCH = "mismatch"
VERDICT_UNSUPPORTED = "unsupported"
VERDICT_INCONCLUSIVE = "inconclusive"
VERDICTS = (VERDICT_MATCH, VERDICT_MISMATCH, VERDICT_UNSUPPORTED, VERDICT_INCONCLUSIVE)
# Everything that is not a clean match is a parity failure for view purposes.
PASSING_VERDICTS = frozenset({VERDICT_MATCH})

# Fields only an oracle may fill. A generator's candidate_prediction that
# carries any of these is trying to author a measurement.
ORACLE_ONLY_KEYS = frozenset(
    {
        "spikes",
        "spike_events",
        "membrane",
        "measured_latency_ms",
        "latency",
        "parity",
        "parity_metrics",
        "outputs",
        "output_digest",
        "output_trace",
        "spike_count",
        "final_membrane",
        "roundtrip",
        "comparison",
        "repeat_digests",
        "quantization",
        "bitstream",
        "hardware",
        "capture",
    }
)

REASON_CODES = frozenset(
    {
        # contract layer
        "ENVELOPE_MALFORMED",
        "GENERATOR_SELF_CERTIFIED",
        "GENERATOR_SUBSTITUTED_FOR_ORACLE",
        "RESULT_NOT_ORACLE_BACKED",
        "RESULT_DIGEST_UNLINKED",
        "VERDICT_UNKNOWN",
        "PROVENANCE_KIND_INVALID",
        "PROVENANCE_CLAIMS_REAL",
        "TRAINING_VIEW_HIDES_FAILURE",
        # hardware parity
        "HW_PROVENANCE_MISSING",
        "HW_TARGET_UNKNOWN",
        "INPUT_FIXTURE_MISMATCH",
        "Q88_PROVENANCE_MISSING",
        "Q88_PROVENANCE_MISMATCH",
        "PARITY_METRIC_MISMATCH",
        "PARITY_VERDICT_INCONSISTENT",
        "SPIKE_BITMAP_DISAGREEMENT",
        "ACTION_DISAGREEMENT",
        "MEMBRANE_DIVERGENCE",
        "QUANTIZATION_SATURATION",
        "REPEATABILITY_UNPROVEN",
        "LATENCY_NOT_MEASURED",
        "ORACLE_UNAVAILABLE",
        "DEPLOYMENT_TRACE_NOT_REDERIVABLE",
        # NIR equivalence
        "NO_EXECUTED_RUNTIME_PAIR",
        "UNAVAILABLE_RUNTIME_HAS_OUTPUT",
        "RUNTIME_STATUS_UNKNOWN",
        "COMPARISON_MISMATCH",
        "DIVERGENCE_SUPPRESSED",
        "DIVERGENCE_RESET_CONVENTION",
        "DIVERGENCE_DELAY_SEMANTICS",
        "DIVERGENCE_RECURRENT_ORDER",
        "DIVERGENCE_NUMERIC_TOLERANCE",
        "DIVERGENCE_EVENT_STREAM",
        "DIVERGENCE_SPIKE_COUNT",
        "DIVERGENCE_INTERNAL_STATE",
        "RUNTIME_NOT_INSTALLED",
        "RUNTIME_ADAPTER_NOT_IMPLEMENTED",
        "RUNTIME_GRAPH_ERROR",
        "ROUNDTRIP_PARSE_FAILURE",
        "ROUNDTRIP_STRUCTURE_MISMATCH",
        "STRUCTURE_DIGEST_MISMATCH",
        "UNSUPPORTED_CONSTRUCT",
        "UNSUPPORTED_NOT_DIAGNOSED",
    }
)

ENVELOPE_KEYS = (
    "id",
    "record_kind",
    "dataset",
    "schema_version",
    "generator",
    "scenario",
    "intervention",
    "candidate_prediction",
    "oracle",
    "result",
    "provenance",
    "validation",
    "meta",
)


def _is_object(value):
    return isinstance(value, dict)


def _nonempty_str(value):
    return isinstance(value, str) and bool(value.strip())


def _is_positive_round(value):
    """A round is a true int >= 1; bool is not an acceptable round."""
    return isinstance(value, int) and not isinstance(value, bool) and value >= 1
