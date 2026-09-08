#!/usr/bin/env python3
"""Vocabulary of the ``neuromorphic-fault-recovery`` family (issue #191, F1).

Identities, disturbances, outcomes and their precedence, the parameter spec,
the default relay, the meters, every reason code and finding code as a
declared constant, the family's oracle-label policy (declared at import from
family code, never read from a record) and the coded refusal type. No logic
beyond the refusal helpers.
"""

from __future__ import annotations

import copy
from collections.abc import Iterable
from typing import Any, NoReturn

from . import distill_labels as labels
from . import envelope
from .import_twins import bind_import_twin

FAMILY = "neuromorphic-fault-recovery"
GENERATOR_NAME = "fault-scenario-generator"
GENERATOR_VERSION = "1.0.0"
GENERATOR_KIND = "programmatic"
ORACLE_NAME = "relay-reflex-sim"
ORACLE_VERSION = "1.0.0"
ORACLE_TYPE = "deterministic_simulator"
# Literals chosen once: F2's identity checks compare them exactly, so they
# are never derived from ``__file__``.
ORACLE_IMPLEMENTATION = "pipelines/oracle_grounded/fault_simulator.py:RelayReflexSimulator"
BOUNDARY_IMPLEMENTATION = "pipelines/oracle_grounded/fault_boundary.py:FaultOracle"
PRODUCER = "pipelines/oracle_grounded/fault_oracle.py"
ORACLE_RUN = "in_process_deterministic"
RECORD_ID_PREFIX = "fr"
MISSION = "keep the relay loop inside its safety envelope"
PREDICTION_METHOD = "kind-keyed lookup that ignores severity"
PREDICTION_CONFIDENCE = 0.5

METER_CLOCK = "simulator_clock"
METER_STATE = "simulator_state"
METER_THERMAL = "simulator_thermal_model"
# quantity -> the meter role (an ``OracleMeters`` field) that takes it.
QUANTITY_METER_ROLES = {
    "detection_latency_ms": "clock",
    "recovery_latency_ms": "clock",
    "healthy_channel_count": "state",
    "dropped_event_count": "state",
    "residual_error": "state",
    "corrupt_ratio": "state",
    "peak_temperature_c": "thermal",
}

# The nine disturbances of issue #78; the order is load-bearing because the
# seeded generator cycles kinds by index.
SENSOR_LOSS = "sensor_loss"
STALE_SENSOR = "stale_sensor"
EVENT_JITTER = "event_jitter"
BURST_CORRUPTION = "burst_corruption"
THERMAL_EXCURSION = "thermal_excursion"
MISSING_CHANNEL = "missing_channel"
MALFORMED_SPIKE_BURST = "malformed_spike_burst"
DELAYED_RESULT = "delayed_result"
TEMPORARY_SATURATION = "temporary_saturation"
DISTURBANCES = (
    SENSOR_LOSS, STALE_SENSOR, EVENT_JITTER, BURST_CORRUPTION, THERMAL_EXCURSION,
    MISSING_CHANNEL, MALFORMED_SPIKE_BURST, DELAYED_RESULT, TEMPORARY_SATURATION,
)

OUTCOME_CONTINUE = "continue"
OUTCOME_DEGRADE = "degrade_gracefully"
OUTCOME_FALLBACK = "fallback"
OUTCOME_REFLEX = "reflex_action"
OUTCOME_QUARANTINE = "quarantine"
OUTCOME_FAIL_CLOSED = "fail_closed"
OUTCOMES = (
    OUTCOME_CONTINUE, OUTCOME_DEGRADE, OUTCOME_FALLBACK,
    OUTCOME_REFLEX, OUTCOME_QUARANTINE, OUTCOME_FAIL_CLOSED,
)
# The prose spelling of issue #78, mirrored into ``result.outcome_label``.
OUTCOME_LABELS = {
    OUTCOME_CONTINUE: "continue",
    OUTCOME_DEGRADE: "degrade gracefully",
    OUTCOME_FALLBACK: "fallback",
    OUTCOME_REFLEX: "reflex action",
    OUTCOME_QUARANTINE: "quarantine",
    OUTCOME_FAIL_CLOSED: "fail closed",
}
# Most protective first; the first tier with a fired reason decides.
OUTCOME_PRECEDENCE = (
    OUTCOME_FAIL_CLOSED, OUTCOME_QUARANTINE, OUTCOME_REFLEX,
    OUTCOME_FALLBACK, OUTCOME_DEGRADE, OUTCOME_CONTINUE,
)

# Order load-bearing (the generator draws ``rng.choice``). The first two
# corrupt an accepted stream; an unknown channel is rejected at the boundary
# and counts as a drop.
MALFORMED_KINDS = ("non_monotonic_time", "negative_amplitude", "unknown_channel")
MALFORMED_INTEGRITY_KINDS = frozenset(MALFORMED_KINDS[:2])

# kind -> (required, optional) parameter names, identical to #138.
PARAMETER_SPEC: dict[str, tuple[tuple[str, ...], tuple[str, ...]]] = {
    SENSOR_LOSS: (("channels", "onset_ms", "duration_ms"), ()),
    STALE_SENSOR: (("channels", "onset_ms", "duration_ms"), ()),
    EVENT_JITTER: (("channels", "onset_ms", "duration_ms", "jitter_ms"), ()),
    BURST_CORRUPTION: (("channels", "onset_ms", "duration_ms", "corrupt_ratio"), ()),
    THERMAL_EXCURSION: (("onset_ms", "ramp_ms", "peak_c"), ("channels",)),
    MISSING_CHANNEL: (("channels",), ()),
    MALFORMED_SPIKE_BURST: (("channels", "malformed_count", "malformed_kind"), ()),
    DELAYED_RESULT: (("delay_ms",), ("channels",)),
    TEMPORARY_SATURATION: (("channels", "onset_ms", "duration_ms"), ()),
}

DEFAULT_SYSTEM: dict[str, Any] = {
    "channels": ["c0", "c1", "c2", "c3"],
    "tick_ms": 2.0,
    "ticks": 24,
    "min_healthy_channels": 3,
    "stale_threshold_ms": 8.0,
    "jitter_tolerance_ms": 1.5,
    "ambient_c": 38.0,
    "thermal_warn_c": 62.0,
    "thermal_limit_c": 78.0,
    "thermal_shutdown_c": 92.0,
    "reflex_saturation_ticks": 4,
    "corruption_quarantine_ratio": 0.25,
    "deadline_ms": 12.0,
    "hard_deadline_ms": 40.0,
    "reflex_latency_ms": 1.0,
    "fallback_latency_ms": 4.0,
    "fallback_source": "redundant_relay_b",
}
SYSTEM_KEYS = frozenset(DEFAULT_SYSTEM)
# Bounded because the validator replays untrusted scenarios.
MAX_CHANNELS = 32
MAX_TICKS = 1000


def default_system() -> dict[str, Any]:
    """A private deep copy of ``DEFAULT_SYSTEM``; nothing aliases its channels."""
    return copy.deepcopy(DEFAULT_SYSTEM)


# Deliberately shallow: keyed on the kind alone, blind to severity, so the
# corpus holds real generator/oracle disagreements.
PREDICTION_BY_KIND = {
    SENSOR_LOSS: OUTCOME_FALLBACK,
    STALE_SENSOR: OUTCOME_DEGRADE,
    EVENT_JITTER: OUTCOME_CONTINUE,
    BURST_CORRUPTION: OUTCOME_QUARANTINE,
    THERMAL_EXCURSION: OUTCOME_REFLEX,
    MISSING_CHANNEL: OUTCOME_DEGRADE,
    MALFORMED_SPIKE_BURST: OUTCOME_QUARANTINE,
    DELAYED_RESULT: OUTCOME_FALLBACK,
    TEMPORARY_SATURATION: OUTCOME_DEGRADE,
}

# Outcome reason codes, in tier emission order.
REASON_NO_TIMELY_INPUT = "NO_TIMELY_INPUT"
REASON_THERMAL_SHUTDOWN = "THERMAL_SHUTDOWN"
REASON_INSUFFICIENT_HEALTHY_CHANNELS_NO_FALLBACK = "INSUFFICIENT_HEALTHY_CHANNELS_NO_FALLBACK"
REASON_MALFORMED_STREAM_QUARANTINED = "MALFORMED_STREAM_QUARANTINED"
REASON_CORRUPTION_ABOVE_QUARANTINE_THRESHOLD = "CORRUPTION_ABOVE_QUARANTINE_THRESHOLD"
REASON_THERMAL_LIMIT_REFLEX = "THERMAL_LIMIT_REFLEX"
REASON_SATURATION_REFLEX = "SATURATION_REFLEX"
REASON_FALLBACK_SOURCE_ENGAGED = "FALLBACK_SOURCE_ENGAGED"
REASON_STALE_BEYOND_THRESHOLD = "STALE_BEYOND_THRESHOLD"
REASON_JITTER_BEYOND_TOLERANCE = "JITTER_BEYOND_TOLERANCE"
REASON_EVENTS_DROPPED = "EVENTS_DROPPED"
REASON_CORRUPTION_BELOW_QUARANTINE_THRESHOLD = "CORRUPTION_BELOW_QUARANTINE_THRESHOLD"
REASON_THERMAL_WARN = "THERMAL_WARN"
REASON_RESULT_PAST_DEADLINE = "RESULT_PAST_DEADLINE"
REASON_REDUCED_CHANNEL_SET = "REDUCED_CHANNEL_SET"
REASON_WITHIN_TOLERANCE = "WITHIN_TOLERANCE"
REASON_CODES = (
    REASON_NO_TIMELY_INPUT, REASON_THERMAL_SHUTDOWN,
    REASON_INSUFFICIENT_HEALTHY_CHANNELS_NO_FALLBACK, REASON_MALFORMED_STREAM_QUARANTINED,
    REASON_CORRUPTION_ABOVE_QUARANTINE_THRESHOLD, REASON_THERMAL_LIMIT_REFLEX,
    REASON_SATURATION_REFLEX, REASON_FALLBACK_SOURCE_ENGAGED, REASON_STALE_BEYOND_THRESHOLD,
    REASON_JITTER_BEYOND_TOLERANCE, REASON_EVENTS_DROPPED,
    REASON_CORRUPTION_BELOW_QUARANTINE_THRESHOLD, REASON_THERMAL_WARN,
    REASON_RESULT_PAST_DEADLINE, REASON_REDUCED_CHANNEL_SET, REASON_WITHIN_TOLERANCE,
)
REASON_CODE_SET = frozenset(REASON_CODES)

# Refusal finding codes: every ``FaultRefusal`` carries exactly one. F2
# appends its replay and identity codes to this tuple.
FINDING_INPUT_NOT_AN_OBJECT = "INPUT_NOT_AN_OBJECT"
FINDING_SYSTEM_UNKNOWN_KEY = "SYSTEM_UNKNOWN_KEY"
FINDING_SYSTEM_CONTROL_OUT_OF_DOMAIN = "SYSTEM_CONTROL_OUT_OF_DOMAIN"
FINDING_THERMAL_LADDER_UNORDERED = "THERMAL_LADDER_UNORDERED"
FINDING_CHANNEL_LIST_INVALID = "CHANNEL_LIST_INVALID"
FINDING_FALLBACK_SOURCE_INVALID = "FALLBACK_SOURCE_INVALID"
FINDING_FALLBACK_SOURCE_IS_PRIMARY = "FALLBACK_SOURCE_IS_PRIMARY"
FINDING_HEALTHY_BUDGET_EXCEEDS_CHANNELS = "HEALTHY_BUDGET_EXCEEDS_CHANNELS"
FINDING_DEADLINE_ORDER_INVERTED = "DEADLINE_ORDER_INVERTED"
FINDING_HORIZON_NOT_FINITE = "HORIZON_NOT_FINITE"
FINDING_DISTURBANCE_KIND_UNKNOWN = "DISTURBANCE_KIND_UNKNOWN"
FINDING_PARAMETER_MISSING = "PARAMETER_MISSING"
FINDING_PARAMETER_UNKNOWN = "PARAMETER_UNKNOWN"
FINDING_PARAMETER_OUT_OF_DOMAIN = "PARAMETER_OUT_OF_DOMAIN"
FINDING_CHANNELS_NOT_A_LIST = "CHANNELS_NOT_A_LIST"
FINDING_CHANNELS_EMPTY = "CHANNELS_EMPTY"
FINDING_CHANNEL_UNKNOWN = "CHANNEL_UNKNOWN"
FINDING_CHANNELS_NO_RELAY_CHANNEL = "CHANNELS_NO_RELAY_CHANNEL"
FINDING_ONSET_BEYOND_HORIZON = "ONSET_BEYOND_HORIZON"
FINDING_PEAK_NOT_ABOVE_AMBIENT = "PEAK_NOT_ABOVE_AMBIENT"
FINDING_SEED_NOT_AN_INTEGER = "SEED_NOT_AN_INTEGER"
FINDING_COUNT_OUT_OF_DOMAIN = "COUNT_OUT_OF_DOMAIN"
FINDING_ORACLE_METERS_UNDECLARED = "ORACLE_METERS_UNDECLARED"
FINDING_PRODUCED_AT_NOT_A_TIMESTAMP = "PRODUCED_AT_NOT_A_TIMESTAMP"
FINDING_CODES = (
    FINDING_INPUT_NOT_AN_OBJECT, FINDING_SYSTEM_UNKNOWN_KEY,
    FINDING_SYSTEM_CONTROL_OUT_OF_DOMAIN, FINDING_THERMAL_LADDER_UNORDERED,
    FINDING_CHANNEL_LIST_INVALID, FINDING_FALLBACK_SOURCE_INVALID,
    FINDING_FALLBACK_SOURCE_IS_PRIMARY, FINDING_HEALTHY_BUDGET_EXCEEDS_CHANNELS,
    FINDING_DEADLINE_ORDER_INVERTED, FINDING_HORIZON_NOT_FINITE,
    FINDING_DISTURBANCE_KIND_UNKNOWN, FINDING_PARAMETER_MISSING, FINDING_PARAMETER_UNKNOWN,
    FINDING_PARAMETER_OUT_OF_DOMAIN, FINDING_CHANNELS_NOT_A_LIST, FINDING_CHANNELS_EMPTY,
    FINDING_CHANNEL_UNKNOWN, FINDING_CHANNELS_NO_RELAY_CHANNEL, FINDING_ONSET_BEYOND_HORIZON,
    FINDING_PEAK_NOT_ABOVE_AMBIENT, FINDING_SEED_NOT_AN_INTEGER, FINDING_COUNT_OUT_OF_DOMAIN,
    FINDING_ORACLE_METERS_UNDECLARED, FINDING_PRODUCED_AT_NOT_A_TIMESTAMP,
)
FINDING_CODE_SET = frozenset(FINDING_CODES)


class FaultRefusal(envelope.ContractError):
    """A coded contract refusal; ``str(exc)`` is ``"CODE: prose"``.

    A ``ContractError`` subclass, so every ``except ContractError`` still
    catches it under both import spellings. An undeclared code is a
    programming error and raises ``LookupError`` instead.
    """

    def __init__(self, code: str, message: str) -> None:
        if code not in FINDING_CODE_SET:
            raise LookupError(f"undeclared finding code: {code!r}")
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message


def refuse(code: str, message: str) -> NoReturn:
    raise FaultRefusal(code, message)


def refuse_when(holds: bool, code: str, message: str) -> None:
    """Raise the coded refusal when ``holds``; the single-check primitive."""
    if holds:
        raise FaultRefusal(code, message)


def refuse_first(problems: Iterable[tuple[bool, str, str]]) -> None:
    """Raise for the first ``(holds, code, message)`` that holds; lazy over the iterable."""
    for holds, code, message in problems:
        refuse_when(holds, code, message)


def finding_code(text: Any) -> str | None:
    """The declared code before the first ``": "`` of a finding string, or None."""
    head = str(text).split(": ", 1)[0]
    return head if head in FINDING_CODE_SET else None


# The oracle-label policy (D2): the sixteen keys the fault oracle writes as
# labels, thirteen at the top of ``result`` and three under ``trace_summary``.
# ``fault_oracle.EMITTED_LABEL_KEYS`` is asserted equal.
RESULT_LABEL_KEYS = frozenset(
    {
        "outcome", "outcome_label", "reason_codes", "detection_latency_ms",
        "recovery_latency_ms", "worst_healthy_channels", "dropped_event_count",
        "corrupt_event_count", "total_event_count", "peak_temperature_c",
        "integrity_violation", "prediction_agreement", "trace_summary",
    }
)
TRACE_SUMMARY_KEYS = frozenset({"max_staleness_ms", "max_jitter_ms", "saturated_ticks"})
ORACLE_LABEL_KEYS = RESULT_LABEL_KEYS | TRACE_SUMMARY_KEYS
# Declared once, at import, from family code; idempotent on re-import.
ORACLE_LABEL_POLICY = labels.declare_oracle_labels(FAMILY, ORACLE_LABEL_KEYS)

bind_import_twin(__name__)
