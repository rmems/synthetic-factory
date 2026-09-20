#!/usr/bin/env python3
"""Family validator for ``neuromorphic-fault-recovery``.

Split out of ``fault_recovery.py`` verbatim: :func:`check_family` re-derives the
oracle outcome from the declared disturbance, replays the recorded simulation,
and reconciles every meter identity and replay hint. Every name here is
re-exported from ``fault_recovery`` so existing call sites resolve unchanged.
"""

from __future__ import annotations

import sys
from dataclasses import field  # noqa: F401
from pathlib import Path
from typing import Any

_PIPELINES = Path(__file__).resolve().parent
if str(_PIPELINES) not in sys.path:
    sys.path.insert(0, str(_PIPELINES))

from oracle_grounded import distill_contract as oc  # noqa: E402
from oracle_grounded import envelope  # noqa: E402
from oracle_grounded import fault_vocabulary  # noqa: E402

if __package__:
    from .fault_records import _derived_measurements, _disturbance, _trace_summary
    from .fault_simulator import (
        DEFAULT_SYSTEM,
        DISTURBANCES,
        ORACLE_IMPLEMENTATION,
        ORACLE_NAME,
        OUTCOME_PRECEDENCE,
        OUTCOME_LABELS,
        OUTCOMES,
        PARAMETER_SPEC,
        RelayReflexSimulator,
        _genuine_count,
        describe,
    )
else:
    from fault_records import _derived_measurements, _disturbance, _trace_summary
    from fault_simulator import (
        DEFAULT_SYSTEM,
        DISTURBANCES,
        ORACLE_IMPLEMENTATION,
        ORACLE_NAME,
        OUTCOME_PRECEDENCE,
        OUTCOME_LABELS,
        OUTCOMES,
        PARAMETER_SPEC,
        RelayReflexSimulator,
        _genuine_count,
        describe,
    )


def _valid_trace_counts(summary: Any) -> bool:
    if not isinstance(summary, dict):
        return False
    return (_genuine_count(summary.get("ticks"))
            and _genuine_count(summary.get("saturated_ticks"))
            and oc.is_number(summary.get("max_staleness_ms"))
            and oc.is_number(summary.get("max_jitter_ms")))


def _check_replay_labels(result: dict[str, Any], replay: Any, where: str) -> list[str]:
    """The recorded label, reasons and integrity flag against the replay."""

    errors: list[str] = []
    if result.get("outcome") != replay.outcome:
        errors.append(
            f"{where}.result.outcome: OUTCOME_NOT_REPRODUCIBLE — recorded "
            f"{result.get('outcome')!r} but re-running the simulator over this "
            f"scenario yields {replay.outcome!r}"
        )
    summary = result.get("trace_summary")
    expected_summary = _trace_summary(replay)
    if summary != expected_summary or not _valid_trace_counts(summary):
        errors.append(f"{where}.result.trace_summary: OUTCOME_NOT_REPRODUCIBLE")
    recorded_reasons = result.get("reason_codes")
    if isinstance(recorded_reasons, list) and sorted(
        str(reason) for reason in recorded_reasons
    ) != sorted(replay.reason_codes):
        errors.append(
            f"{where}.result.reason_codes: OUTCOME_NOT_REPRODUCIBLE — recorded "
            f"{sorted(str(r) for r in recorded_reasons)} but the simulator "
            f"reports {sorted(replay.reason_codes)}"
        )
    integrity = result.get("integrity_violation")
    if not isinstance(integrity, bool):
        # The flag is replay-derived, so its absence is a finding, not a
        # reason to skip the comparison: deleting it was all it took for a
        # malformed-spike record to lose its `true` integrity signal and
        # stay curation-eligible.
        errors.append(
            f"{where}.result.integrity_violation must be a boolean — the "
            f"simulator replay reports {replay.integrity_violation}"
        )
    elif integrity is not replay.integrity_violation:
        errors.append(
            f"{where}.result.integrity_violation: OUTCOME_NOT_REPRODUCIBLE — "
            f"recorded {integrity} but the simulator "
            f"reports {replay.integrity_violation}"
        )
    return errors


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

    recorded_quantities = {
        item.get("quantity")
        for item in items
        if isinstance(item.get("quantity"), str) and oc.is_true(item.get("measured"))
    }
    missing = sorted(
        quantity
        for quantity, target in expected.items()
        if target is not None and quantity not in recorded_quantities
    )
    if missing:
        return [
            f"{where}.result: OUTCOME_NOT_REPRODUCIBLE — the replay derives "
            f"measurements {missing} that the record does not carry as "
            "measured readings"
        ]
    return []


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
    if not (
        isinstance(scenario, dict)
        and isinstance(intervention, dict)
        and isinstance(result, dict)
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


def _check_intervention_parameters(
    kind: str, parameters: Any, where: str
) -> list[str]:
    """The parameter set this disturbance kind requires, and nothing extra."""

    if not isinstance(parameters, dict):
        return [f"{where}.intervention.parameters must be an object"]
    errors: list[str] = []
    required, optional = PARAMETER_SPEC[kind]
    missing = [key for key in required if key not in parameters]
    if missing:
        errors.append(
            f"{where}.intervention.parameters: {kind} requires {sorted(missing)}"
        )
    unknown = sorted(set(parameters) - set(required) - set(optional))
    if unknown:
        errors.append(
            f"{where}.intervention.parameters: {kind} does not use {unknown}"
        )
    return errors


def _check_disturbance_kind_match(
    record: dict[str, Any], kind: str, where: str
) -> list[str]:
    """The scenario is what the student sees; the intervention is what was simulated.

    If they name different faults, the record pairs one fault's description
    with another fault's label.
    """

    scenario = record.get("scenario")
    if not isinstance(scenario, dict):
        return []
    if "disturbance_kind" not in scenario:
        # Absence is a finding, not a pass: deleting the field left the
        # student-visible scenario no longer identifying the fault whose
        # outcome the intervention simulated.
        return [
            f"{where}.scenario.disturbance_kind must be present and name "
            f"the simulated fault ({kind!r})"
        ]
    declared = scenario.get("disturbance_kind")
    if declared != kind:
        return [
            f"{where}.scenario.disturbance_kind: DISTURBANCE_KIND_MISMATCH "
            f"— the scenario presents {declared!r} but the label was "
            f"produced by simulating {kind!r}"
        ]
    return []


def _check_intervention(record: dict[str, Any], where: str) -> list[str]:
    """The proposed disturbance, its parameters, and the scenario that names it."""

    intervention = record.get("intervention")
    if not isinstance(intervention, dict):
        return [f"{where}.intervention must describe the proposed disturbance"]
    kind = intervention.get("kind")
    if kind not in DISTURBANCES:
        return [
            f"{where}.intervention.kind must be one of {sorted(DISTURBANCES)}, "
            f"got {kind!r}"
        ]
    errors = _check_intervention_parameters(
        kind, intervention.get("parameters"), where
    )
    errors += _check_disturbance_kind_match(record, kind, where)
    if kind == "burst_corruption":
        errors += _check_requested_corruption(record, where)
    return errors


def _check_requested_corruption(record: dict[str, Any], where: str) -> list[str]:
    """Requested severity is a restatement of the intervention, not a new reading."""

    parameters = record["intervention"].get("parameters")
    result = record.get("result")
    if not isinstance(parameters, dict) or not isinstance(result, dict):
        return []
    target = parameters.get("corrupt_ratio")
    if not oc.is_number(target):
        return []
    measurements = result.get("measurements")
    errors: list[str] = []
    for item in measurements if isinstance(measurements, list) else []:
        if not isinstance(item, dict) or item.get("quantity") != "corrupt_ratio":
            continue
        detail = item.get("detail")
        requested = detail.get("requested") if isinstance(detail, dict) else None
        if not oc.is_number(requested) or requested != target:
            errors.append(
                f"{where}.result.measurements.corrupt_ratio.detail.requested "
                "must match intervention.parameters.corrupt_ratio"
            )
    return errors


def _check_candidate_prediction(record: dict[str, Any], where: str) -> list[str]:
    """The student's proposed outcome, when the record carries one."""

    errors: list[str] = []
    prediction = record.get("candidate_prediction")
    if isinstance(prediction, dict):
        predicted = prediction.get("predicted_outcome")
        if predicted is not None and predicted not in OUTCOMES:
            errors.append(
                f"{where}.candidate_prediction.predicted_outcome must be one of "
                f"{sorted(OUTCOMES)}, got {predicted!r}"
            )
        elif isinstance(predicted, str) and prediction.get("predicted_outcome_label") != OUTCOME_LABELS[predicted]:
            errors.append(
                f"{where}.candidate_prediction.predicted_outcome_label must be "
                f"{OUTCOME_LABELS[predicted]!r}"
            )
    return errors


def _check_outcome(result: dict[str, Any], where: str) -> list[str]:
    """The recorded outcome, its prose label, and the reasons behind it."""

    errors: list[str] = []
    outcome = result.get("outcome")
    if outcome not in OUTCOMES:
        errors.append(
            f"{where}.result.outcome must be one of {sorted(OUTCOMES)}, got {outcome!r}"
        )
    elif result.get("outcome_label") != OUTCOME_LABELS[outcome]:
        # The label preserves the issue's prose vocabulary beside the
        # canonical outcome; absence is a finding, not a pass. Deleting it
        # and rehashing silently removed the promised traceability field
        # while the record stayed curation-eligible.
        errors.append(
            f"{where}.result.outcome_label must be {OUTCOME_LABELS[outcome]!r} "
            f"— the emitted prose label for {outcome!r} — got "
            f"{result.get('outcome_label')!r}"
        )
    reasons = result.get("reason_codes")
    if not isinstance(reasons, list) or not reasons:
        errors.append(
            f"{where}.result.reason_codes must be a non-empty array — every fault "
            "outcome needs an explicit reason"
        )
    return errors


def _check_prediction_agreement(record: dict[str, Any], where: str) -> list[str]:
    """``result.prediction_agreement`` is derived, not an independent fact.

    Flipping it to ``"agree"`` would corrupt every disagreement analysis while
    the replay still reproduced the outcome, so it is recomputed from the
    prediction and the outcome instead of being trusted.
    """

    result = record.get("result")
    if not isinstance(result, dict):
        return []
    if "prediction_agreement" not in result:
        # The field is derived, so its absence is a finding, not a pass:
        # deleting it made the record silently disappear from the
        # disagreement analyses this emitted field supports.
        return [
            f"{where}.result.prediction_agreement must be present — it is "
            "derived from the prediction and the outcome"
        ]
    agreement = result.get("prediction_agreement")
    if agreement not in ("agree", "disagree"):
        return [
            f"{where}.result.prediction_agreement must be 'agree' or "
            f"'disagree', got {agreement!r}"
        ]
    prediction = record.get("candidate_prediction")
    predicted = (
        prediction.get("predicted_outcome") if isinstance(prediction, dict) else None
    )
    outcome = result.get("outcome")
    if not isinstance(predicted, str):
        # An agreement label without the prediction it grades is arbitrary:
        # deleting candidate_prediction (or just predicted_outcome) used to
        # skip the derivation check while the label stayed curation-eligible.
        return [
            f"{where}.result.prediction_agreement is recorded but "
            "candidate_prediction.predicted_outcome is missing — an "
            "agreement label needs the prediction it grades"
        ]
    if not oc.is_enum_value(outcome, OUTCOMES):
        return []
    expected = "agree" if predicted == outcome else "disagree"
    if agreement != expected:
        return [
            f"{where}.result.prediction_agreement is {agreement!r} but the "
            f"prediction {predicted!r} against outcome {outcome!r} yields "
            f"{expected!r}"
        ]
    return []


def _check_oracle_configuration_binding(
    record: dict[str, Any], where: str
) -> list[str]:
    """The oracle block must describe the configuration behind its label.

    The replay reads only ``scenario.system``, so a rewritten or deleted
    ``oracle.configuration.system`` stayed validation-clean while the
    authoritative oracle block no longer described the run that produced its
    label — breaking reproducibility and provenance audits.
    """

    oracle = record.get("oracle")
    if not isinstance(oracle, dict) or oracle.get("name") != ORACLE_NAME:
        return []
    if oracle.get("implementation") != ORACLE_IMPLEMENTATION and (
        oracle.get("type") != "deterministic_simulator"
    ):
        return []
    scenario = record.get("scenario")
    recorded_system = scenario.get("system", {}) if isinstance(scenario, dict) else {}
    configuration = oracle.get("configuration")
    if not isinstance(configuration, dict):
        return [
            f"{where}.oracle.configuration must record the simulator's "
            "system and precedence"
        ]
    # The recorded system is the *effective* one: the oracle fills every key
    # the scenario omits from DEFAULT_SYSTEM before running, so the binding
    # compares against that merged configuration, not the partial input.
    effective_system = {**DEFAULT_SYSTEM, **recorded_system}
    errors: list[str] = []
    # Strict JSON equality: Python's == conflates true with 1.0, so a record
    # could replace a numeric setting with a boolean, recompute its digest,
    # and still claim the oracle block describes the replayed configuration.
    if not envelope.strict_json_equal(configuration.get("system"), effective_system):
        errors.append(
            f"{where}.oracle.configuration.system does not match "
            "scenario.system — the oracle block must describe the "
            "configuration that produced its label"
        )
    if configuration.get("precedence") != list(OUTCOME_PRECEDENCE):
        errors.append(
            f"{where}.oracle.configuration.precedence must be the canonical "
            f"outcome precedence {list(OUTCOME_PRECEDENCE)}"
        )
    return errors



def _canonical_oracle_name(name: str) -> str:
    """Collapse orthography that still *looks* like ``ORACLE_NAME``.

    Used only to detect near-miss escapes. Acceptance still requires the exact
    ``ORACLE_NAME`` string — we never strip-and-accept a forged name.
    """

    # Zero-width / BOM format chars survive ``str.strip``; drop them explicitly.
    for noise in ("\u200b", "\u200c", "\u200d", "\ufeff"):
        name = name.replace(noise, "")
    # Unicode whitespace (ASCII space, NBSP, thin space, …) via strip.
    collapsed = name.strip().replace("_", "-").casefold()
    return collapsed


def _oracle_name_is_near_miss(name: Any) -> bool:
    """True when ``name`` is not exact ``ORACLE_NAME`` but canonicalizes to it."""

    if not isinstance(name, str) or name == ORACLE_NAME:
        return False
    return _canonical_oracle_name(name) == _canonical_oracle_name(ORACLE_NAME)


def _check_oracle_name_identity(
    record: dict[str, Any], where: str
) -> list[str]:
    """``oracle.name`` must be exact ``ORACLE_NAME`` for this family.

    Trailing/leading space, NBSP, underscore rename, case variants, and foreign
    names used to early-return out of type-binding + re-sim (exact
    ``== ORACLE_NAME``), leaving a forged ``hardware_replay`` continue
    curation-eligible (FAULT-NAME-IDENTITY-ESCAPE). Reject any non-exact name;
    do not normalize-and-accept.
    """

    oracle = record.get("oracle")
    if not isinstance(oracle, dict):
        return []
    name = oracle.get("name")
    if name == ORACLE_NAME:
        return []
    if _oracle_name_is_near_miss(name):
        detail = (
            f"near-miss name {name!r} must be exact {ORACLE_NAME!r} "
            "(whitespace / underscore / case variants are not accepted)"
        )
    else:
        detail = (
            f"foreign name {name!r} must be exact {ORACLE_NAME!r} "
            "(this family does not accept other oracle names)"
        )
    return [f"{where}.oracle.name: ORACLE_NAME_MISMATCH — {detail}"]


def _check_oracle_implementation_identity(
    record: dict[str, Any], where: str
) -> list[str]:
    """``relay-reflex-sim`` must declare the exact in-process implementation.

    Trailing whitespace or a truncated class name used to miss both the type
    binder and the re-sim gate (exact ``== ORACLE_IMPLEMENTATION``), leaving a
    forged ``hardware_replay`` continue curation-eligible.
    """

    oracle = record.get("oracle")
    if not isinstance(oracle, dict):
        return []
    if oracle.get("name") != ORACLE_NAME:
        return []
    implementation = oracle.get("implementation")
    if implementation == ORACLE_IMPLEMENTATION:
        return []
    return [
        f"{where}.oracle.implementation: ORACLE_IMPLEMENTATION_MISMATCH — "
        f"{ORACLE_NAME} must declare implementation {ORACLE_IMPLEMENTATION!r}, "
        f"got {implementation!r}"
    ]


def _check_simulator_type_binding(record: dict[str, Any], where: str) -> list[str]:
    """Our in-process simulator must declare deterministic_simulator type."""

    oracle = record.get("oracle")
    if not isinstance(oracle, dict):
        return []
    if oracle.get("name") != ORACLE_NAME:
        return []
    if oracle.get("implementation") != ORACLE_IMPLEMENTATION:
        return []
    if oracle.get("type") == "deterministic_simulator":
        return []
    return [
        f"{where}.oracle.type: ORACLE_TYPE_MISMATCH — {ORACLE_IMPLEMENTATION} "
        f"must declare type deterministic_simulator, got {oracle.get('type')!r}"
    ]


def check_family(record: dict[str, Any], where: str) -> list[str]:
    """Family checks layered on top of the shared envelope."""

    # The family's declared label policy is code (fault_vocabulary), not record
    # data; refuse any of its keys inside the generator-owned sections.
    errors = oc.check_oracle_label_leak(
        record, where, policy=fault_vocabulary.ORACLE_LABEL_POLICY
    )
    errors += _check_intervention(record, where)
    errors += _check_candidate_prediction(record, where)
    result = record.get("result")
    if not isinstance(result, dict):
        return errors + [f"{where}.result must be an object"]
    errors += _check_outcome(result, where)
    errors += _check_prediction_agreement(record, where)
    errors += _check_oracle_configuration_binding(record, where)
    errors += _check_oracle_name_identity(record, where)
    errors += _check_oracle_implementation_identity(record, where)
    errors += _check_simulator_type_binding(record, where)
    errors += _recheck_deterministic_outcome(record, where)
    return errors
