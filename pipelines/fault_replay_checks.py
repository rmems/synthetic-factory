#!/usr/bin/env python3
"""Replay checks for ``neuromorphic-fault-recovery`` records.

Split out of ``fault_check.py`` verbatim: re-run the recorded disturbance
through :class:`fault_simulator.RelayReflexSimulator` and reconcile the
recorded labels, reasons, measurements, and trace summary against the replay.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

_PIPELINES = Path(__file__).resolve().parent
if str(_PIPELINES) not in sys.path:
    sys.path.insert(0, str(_PIPELINES))

from oracle_grounded import distill_contract as oc  # noqa: E402

if __package__:
    from .fault_records import _derived_measurements, _trace_summary
    from .fault_simulator import RelayReflexSimulator
    from .fault_types import ORACLE_IMPLEMENTATION, ORACLE_NAME, _genuine_count
else:
    from fault_records import _derived_measurements, _trace_summary
    from fault_simulator import RelayReflexSimulator
    from fault_types import ORACLE_IMPLEMENTATION, ORACLE_NAME, _genuine_count


def _valid_trace_counts(summary: Any) -> bool:
    if not isinstance(summary, dict):
        return False
    return (_genuine_count(summary.get("ticks"))
            and _genuine_count(summary.get("saturated_ticks"))
            and oc.is_number(summary.get("max_staleness_ms"))
            and oc.is_number(summary.get("max_jitter_ms")))


def _check_outcome_label(result: dict[str, Any], replay: Any, where: str) -> list[str]:
    if result.get("outcome") == replay.outcome:
        return []
    return [
        f"{where}.result.outcome: OUTCOME_NOT_REPRODUCIBLE — recorded "
        f"{result.get('outcome')!r} but re-running the simulator over this "
        f"scenario yields {replay.outcome!r}"
    ]


def _check_trace_summary_label(
    result: dict[str, Any], replay: Any, where: str
) -> list[str]:
    summary = result.get("trace_summary")
    if summary != _trace_summary(replay) or not _valid_trace_counts(summary):
        return [f"{where}.result.trace_summary: OUTCOME_NOT_REPRODUCIBLE"]
    return []


def _check_reason_codes(result: dict[str, Any], replay: Any, where: str) -> list[str]:
    recorded_reasons = result.get("reason_codes")
    if not isinstance(recorded_reasons, list):
        return []
    if sorted(str(reason) for reason in recorded_reasons) == sorted(replay.reason_codes):
        return []
    return [
        f"{where}.result.reason_codes: OUTCOME_NOT_REPRODUCIBLE — recorded "
        f"{sorted(str(r) for r in recorded_reasons)} but the simulator "
        f"reports {sorted(replay.reason_codes)}"
    ]


def _check_integrity_label(result: dict[str, Any], replay: Any, where: str) -> list[str]:
    integrity = result.get("integrity_violation")
    if not isinstance(integrity, bool):
        # The flag is replay-derived, so its absence is a finding, not a
        # reason to skip the comparison: deleting it was all it took for a
        # malformed-spike record to lose its `true` integrity signal and
        # stay curation-eligible.
        return [
            f"{where}.result.integrity_violation must be a boolean — the "
            f"simulator replay reports {replay.integrity_violation}"
        ]
    if integrity is not replay.integrity_violation:
        return [
            f"{where}.result.integrity_violation: OUTCOME_NOT_REPRODUCIBLE — "
            f"recorded {integrity} but the simulator "
            f"reports {replay.integrity_violation}"
        ]
    return []


def _check_replay_labels(result: dict[str, Any], replay: Any, where: str) -> list[str]:
    """The recorded label, reasons and integrity flag against the replay."""

    return (
        _check_outcome_label(result, replay, where)
        + _check_trace_summary_label(result, replay, where)
        + _check_reason_codes(result, replay, where)
        + _check_integrity_label(result, replay, where)
    )


# The simulator instrument each replay-derived quantity is read from. A
# reading that keeps the derived value but renames its meter falsifies
# measurement provenance while every value comparison still passes.
_REPLAY_METERS: dict[str, str] = {
    "detection_latency_ms": RelayReflexSimulator.meter_clock,
    "recovery_latency_ms": RelayReflexSimulator.meter_clock,
    "healthy_channel_count": RelayReflexSimulator.meter_state,
    "dropped_event_count": RelayReflexSimulator.meter_state,
    "residual_error": RelayReflexSimulator.meter_state,
    "corrupt_ratio": RelayReflexSimulator.meter_state,
    "peak_temperature_c": RelayReflexSimulator.meter_thermal,
}


def _missing_replay_quantities(
    expected: dict[str, float | None], items: list[dict[str, Any]], where: str
) -> list[str]:
    """Presence first: every derived target needs a reading the oracle took.

    Validating only the readings that remain would let a record delete the
    replay-derived latencies, counts and ratios wholesale and keep a single
    surviving reading as its "measured" result — and a reading flipped to
    ``measured: false`` is a modelled value wearing a measurement's name, so
    it does not count as carrying the target either.
    """

    recorded_quantities = _measured_quantities(items)
    missing = _unrecorded_targets(expected, recorded_quantities)
    if missing:
        return [
            f"{where}.result: OUTCOME_NOT_REPRODUCIBLE — the replay derives "
            f"measurements {missing} that the record does not carry as "
            "measured readings"
        ]
    return []


def _measured_quantities(items: list[dict[str, Any]]) -> set[str]:
    return {
        item.get("quantity")
        for item in items
        if isinstance(item.get("quantity"), str) and oc.is_true(item.get("measured"))
    }


def _unrecorded_targets(
    expected: dict[str, float | None], recorded: set[str]
) -> list[str]:
    return sorted(
        quantity
        for quantity, target in expected.items()
        if target is not None and quantity not in recorded
    )


def _replay_item_errors(
    item: dict[str, Any],
    expected: dict[str, float | None],
    record_meters: dict[str, str],
    where: str,
) -> list[str]:
    """One recorded reading against the value and meter the replay derives."""

    quantity = item.get("quantity")
    if not oc.is_enum_value(quantity, expected):
        return []
    target = expected[quantity]
    if target is None:
        # The replay derives no such value — a `detection_latency_ms` on
        # a run with no detection is a fabricated oracle-attributed
        # target, not a reading to skip.
        return [
            f"{where}.result: OUTCOME_NOT_REPRODUCIBLE — the record "
            f"carries {quantity} but the replay derives no such "
            "measurement"
        ]
    errors: list[str] = []
    if not oc.is_true(item.get("measured")):
        errors.append(
            f"{where}.result: OUTCOME_NOT_REPRODUCIBLE — the {quantity} "
            f"reading is marked measured: {item.get('measured')!r}, but every "
            "replay-derived fault target must be a reading the simulator "
            "actually took"
        )
    if item.get("meter") != record_meters[quantity]:
        errors.append(
            f"{where}.result: MEASUREMENT_PROVENANCE_NOT_REPRODUCIBLE — "
            f"{quantity} is attributed to meter {item.get('meter')!r} but "
            f"the producing oracle reads it from {record_meters[quantity]!r}"
        )
    if oc.is_number(item.get("value")) and (
        abs(float(item["value"]) - float(target)) > 1e-6
    ):
        errors.append(
            f"{where}.result: OUTCOME_NOT_REPRODUCIBLE — measured "
            f"{quantity} is {item['value']} but the simulator derives "
            f"{target}"
        )
    return errors


# Quantity -> the meter role an oracle reads it from. ``_REPLAY_METERS``
# supplies the simulator's own instruments; an oracle that stamps a
# ``configuration.meters`` role map (as ``oracle_block`` now does) names its
# own meters instead, so an injected oracle's readings are validated against
# the meters it declared rather than the simulator defaults.
_QUANTITY_METER_ROLE = {
    "detection_latency_ms": "clock",
    "recovery_latency_ms": "clock",
    "healthy_channel_count": "state",
    "dropped_event_count": "state",
    "residual_error": "state",
    "corrupt_ratio": "state",
    "peak_temperature_c": "thermal",
}


def _record_meters(record: dict[str, Any]) -> dict[str, str]:
    """Replay-derived expected meters: the record's declared roles, else the
    simulator's own."""

    expected = dict(_REPLAY_METERS)
    oracle = record.get("oracle")
    configuration = oracle.get("configuration") if isinstance(oracle, dict) else None
    declared = configuration.get("meters") if isinstance(configuration, dict) else None
    if isinstance(declared, dict):
        for quantity, role in _QUANTITY_METER_ROLE.items():
            meter = declared.get(role)
            if isinstance(meter, str) and meter.strip():
                expected[quantity] = meter
    return expected


def _check_replay_measurements(
    result: dict[str, Any], replay: Any, record_meters: dict[str, str], where: str
) -> list[str]:
    """The recorded measurements against the ones the replay derives."""

    expected = _derived_measurements(replay)
    measurements = result.get("measurements")
    items = [
        item
        for item in (measurements if isinstance(measurements, list) else [])
        if isinstance(item, dict)
    ]
    errors = _missing_replay_quantities(expected, items, where)
    for item in items:
        errors += _replay_item_errors(item, expected, record_meters, where)
    return errors


def _replayable_blocks(
    record: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]] | None:
    """The scenario/intervention/result of a record this oracle can replay.

    Replay is keyed on the in-process simulator identity (name + implementation),
    not ``oracle.type``. Flipping type to vocabulary-legal ``hardware_replay``
    while keeping ``RelayReflexSimulator`` must not disable the gate.
    """

    oracle = record.get("oracle")
    if not isinstance(oracle, dict):
        return None
    if oracle.get("name") != ORACLE_NAME:
        return None
    if oracle.get("implementation") != ORACLE_IMPLEMENTATION:
        return None
    scenario = record.get("scenario")
    intervention = record.get("intervention")
    result = record.get("result")
    if not all(
        isinstance(block, dict)
        for block in (scenario, intervention, result)
    ):
        return None
    return scenario, intervention, result


def _recheck_deterministic_outcome(record: dict[str, Any], where: str) -> list[str]:
    """Re-run the simulator and compare, for records it produced.

    The scenario and the intervention fully determine this oracle's answer, so
    the label is reproducible rather than merely unfalsifiable. Without this,
    editing ``result.outcome`` to another vocabulary member, updating its prose
    label and reason code, and recomputing the digest produces a record that
    validates clean and is curated as authoritative ground truth.

    Only the in-process simulator is re-run. A hardware replay oracle is not
    reproducible here, and silently "correcting" its labels to the simulator's
    would be worse than not checking.
    """

    blocks = _replayable_blocks(record)
    if blocks is None:
        return []
    scenario, intervention, result = blocks
    try:
        replay = RelayReflexSimulator().run(scenario, intervention)
    except (oc.ContractError, KeyError, TypeError, ValueError) as exc:
        return [
            f"{where}.result: OUTCOME_NOT_REPRODUCIBLE — the recorded scenario "
            f"and intervention do not run on {ORACLE_NAME}: {exc}"
        ]
    return _check_replay_labels(result, replay, where) + _check_replay_measurements(
        result, replay, _record_meters(record), where
    )

