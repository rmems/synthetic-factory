#!/usr/bin/env python3
"""Vocabulary of the distillation record contract (issue #78).

The families and the schema-version pin, the generator kind / oracle type /
authority / status vocabularies, the oracle-only key set and the ``predicted_*``
naming rule, and the unit / meter / energy registry. Nothing here checks or
builds a record; the sibling modules of ``distill_contract`` do that over
these names.

The domain-neutral primitives the shared envelope owns (#172) are bound here
under the names the contract has always exported, so ``distill_contract.X``
keeps working: they are the envelope's own objects.
"""

from __future__ import annotations

from typing import Any

from . import envelope
from .import_twins import bind_import_twin

GENERATOR_SECTIONS = envelope.GENERATOR_SECTIONS
SHA256_RE = envelope.SHA256_RE
ISO_8601_RE = envelope.ISO_8601_RE
ContractError = envelope.ContractError
OracleUnavailable = envelope.OracleUnavailable
canonical_json = envelope.canonical_json
utc_now_iso = envelope.utc_now_iso
is_number = envelope.is_number
is_enum_value = envelope.is_enum_value
record_digest = envelope.record_digest

SCHEMA_VERSION = "oracle-grounded/1.0.0"

FAMILIES = (
    "neuromorphic-fault-recovery",
    "snn-energy-routing-preferences",
    "moe-router-distillation-trajectories",
)

GENERATOR_AUTHORITY = "propose_only"
GENERATOR_KINDS = frozenset({"programmatic", "llm", "human", "hybrid"})

AUTHORITY_AUTHORITATIVE = "authoritative"
AUTHORITY_REFERENCE_ONLY = "reference_only"
ORACLE_AUTHORITIES = frozenset({AUTHORITY_AUTHORITATIVE, AUTHORITY_REFERENCE_ONLY})

# An oracle type names *how* truth was obtained, never who asked for it.
ORACLE_TYPES = frozenset(
    {
        "deterministic_simulator",
        "measured_execution",
        "recorded_measurement",
        "real_model_router",
        "reference_model_router",
        "hardware_replay",
    }
)

RESULT_MEASURED = "measured"
RESULT_ABSTAINED = "abstained"
RESULT_STATUSES = frozenset({RESULT_MEASURED, RESULT_ABSTAINED})

VALIDATION_UNVALIDATED = "unvalidated"
VALIDATION_PASSED = "passed"
VALIDATION_FAILED = "failed"
VALIDATION_STATUSES = frozenset(
    {VALIDATION_UNVALIDATED, VALIDATION_PASSED, VALIDATION_FAILED}
)

# Keys that only an oracle may write. Compared by exact key name at any depth
# inside a generator-owned section (``GENERATOR_SECTIONS``) by the envelope's
# bounded reserved-key scan.
ORACLE_ONLY_KEYS = frozenset(
    {
        "measurements",
        "measurement",
        "measured_by",
        "outcome",
        "reason_codes",
        "joules",
        "energy_j",
        "power_w",
        "cpu_time_s",
        "wall_time_s",
        "latency_ms",
        "router_logits",
        "top_k_experts",
        "expert_ids",
        "routing_entropy",
        "top1_top2_margin",
        "expert_agreement",
        "task_quality",
        "preference",
        "safety_ok",
        "result",
        # Emitted oracle summaries. `top1_expert` was missing, so a router
        # record could copy the teacher label into the student-visible
        # scenario namespace, rehash, and hand training a trivially leaked
        # target; the rest are the same class of oracle-owned outputs.
        "top1_expert",
        "routing",
        "teacher_grounded",
        "outcome_label",
        "prediction_agreement",
        "integrity_violation",
        "detection_latency_ms",
        "recovery_latency_ms",
        "candidates",
        "reference_objective",
        "cost_is_energy",
        "abstention_reason",
    }
)

# Direct keys allowed under candidate_prediction. Everything else must be
# ``predicted_*`` so a generator guess can never be mistaken for a label.
PREDICTION_FREE_KEYS = frozenset({"rationale", "confidence", "method"})
PREDICTION_PREFIX = "predicted_"

# quantity -> canonical unit. A measurement must declare the canonical unit.
QUANTITY_UNITS = {
    "energy_j": "J",
    "energy_per_op_j": "J",
    "power_w": "W",
    "cpu_time_s": "s",
    "wall_time_s": "s",
    "latency_ms": "ms",
    "detection_latency_ms": "ms",
    "recovery_latency_ms": "ms",
    "temperature_c": "degC",
    "peak_temperature_c": "degC",
    "max_rss_kb": "kB",
    "context_switches": "count",
    "healthy_channel_count": "count",
    "dropped_event_count": "count",
    "residual_error": "ratio",
    "corrupt_ratio": "ratio",
    "task_quality": "ratio",
    "routing_entropy": "nat",
    "top1_top2_margin": "logit",
    "expert_agreement": "ratio",
    "repeats": "count",
}

# Quantity domains. `is_number` alone accepted any finite value, so a
# rehashed record could serve wall_time_s = -5, a negative event count, or a
# ratio outside [0, 1] as an oracle measurement target. Temperatures are the
# only listed quantities a physical reading may take below zero.
NON_NEGATIVE_QUANTITIES = frozenset(
    {
        "energy_j",
        "energy_per_op_j",
        "power_w",
        "cpu_time_s",
        "wall_time_s",
        "latency_ms",
        "detection_latency_ms",
        "recovery_latency_ms",
        "max_rss_kb",
        "context_switches",
        "healthy_channel_count",
        "dropped_event_count",
        "repeats",
        "routing_entropy",
        "top1_top2_margin",
    }
)
UNIT_INTERVAL_QUANTITIES = frozenset(
    {
        "residual_error",
        "corrupt_ratio",
        "task_quality",
        "expert_agreement",
    }
)

ENERGY_QUANTITIES = frozenset({"energy_j", "energy_per_op_j", "power_w"})

# Meters that physically measure energy. Anything outside this set may not
# produce an energy-class quantity. `recorded_power_run` is deliberately
# absent: it is the replay *wrapper*, not an instrument — a replayed joule
# must name the physical meter the recording says took it, or a file of bare
# observations could launder energy readings behind the wrapper's name.
MEASURED_ENERGY_METERS = frozenset(
    {
        "intel_rapl_powercap",
        "external_power_meter",
        "board_power_rail",
    }
)

# Meters that model rather than measure. Legal for non-energy bookkeeping and
# for explicitly modeled quantities, never for an energy claim.
MODELED_METERS = frozenset(
    {
        "analytic_op_count",
        "synops_model",
        "spike_energy_model",
        "datasheet_estimate",
    }
)


def is_true(value: Any) -> bool:
    """Identity test against ``True`` for fields untrusted input controls.

    ``bool(value)`` would accept any truthy JSON value — ``"yes"``, ``[0]``,
    ``1`` — where the contract demands the boolean itself, so gates built on
    truthiness fail open on malformed records. Only ``True`` is true here.
    """

    return value is True


def is_genuine_int(value: Any) -> bool:
    """True for a genuine integer — never a boolean wearing int's clothes."""

    return isinstance(value, int) and not isinstance(value, bool)


def missing_string(value: Any) -> bool:
    """True unless ``value`` is a string with something other than whitespace."""

    return not isinstance(value, str) or not value.strip()


bind_import_twin(__name__)
