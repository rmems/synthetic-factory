#!/usr/bin/env python3
"""Family validator for ``neuromorphic-fault-recovery``.

Split out of ``fault_recovery.py`` verbatim: :func:`check_family` re-derives the
oracle outcome from the declared disturbance, replays the recorded simulation,
and reconciles every meter identity and replay hint. Record-replay checks live
in ``fault_replay_checks`` and oracle-identity checks in
``fault_oracle_checks``; every name here is re-exported from
``fault_recovery`` so existing call sites resolve unchanged.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

_PIPELINES = Path(__file__).resolve().parent
if str(_PIPELINES) not in sys.path:
    sys.path.insert(0, str(_PIPELINES))

from oracle_grounded import distill_contract as oc  # noqa: E402
from oracle_grounded import fault_vocabulary  # noqa: E402

if __package__:
    from . import fault_oracle_checks as _oracle_checks
    from . import fault_replay_checks as _replay_checks
    from . import fault_types as _fault_types
else:
    import fault_oracle_checks as _oracle_checks
    import fault_replay_checks as _replay_checks
    import fault_types as _fault_types

_check_oracle_configuration_binding = _oracle_checks._check_oracle_configuration_binding
_check_oracle_implementation_identity = _oracle_checks._check_oracle_implementation_identity
_check_oracle_name_identity = _oracle_checks._check_oracle_name_identity
_check_simulator_type_binding = _oracle_checks._check_simulator_type_binding
_recheck_deterministic_outcome = _replay_checks._recheck_deterministic_outcome
DISTURBANCES = _fault_types.DISTURBANCES
OUTCOME_LABELS = _fault_types.OUTCOME_LABELS
OUTCOMES = _fault_types.OUTCOMES
PARAMETER_SPEC = _fault_types.PARAMETER_SPEC


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


def _requested_corruption_problem(
    item: Any, target: Any, where: str
) -> str | None:
    """The mismatch of one measurement's requested ratio, if any."""

    if not isinstance(item, dict) or item.get("quantity") != "corrupt_ratio":
        return None
    detail = item.get("detail")
    requested = detail.get("requested") if isinstance(detail, dict) else None
    if not oc.is_number(requested) or requested != target:
        return (
            f"{where}.result.measurements.corrupt_ratio.detail.requested "
            "must match intervention.parameters.corrupt_ratio"
        )
    return None


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
    items = measurements if isinstance(measurements, list) else []
    return [
        problem
        for item in items
        if (problem := _requested_corruption_problem(item, target, where)) is not None
    ]


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
    if not isinstance(predicted, str):
        # An agreement label without the prediction it grades is arbitrary:
        # deleting candidate_prediction (or just predicted_outcome) used to
        # skip the derivation check while the label stayed curation-eligible.
        return [
            f"{where}.result.prediction_agreement is recorded but "
            "candidate_prediction.predicted_outcome is missing — an "
            "agreement label needs the prediction it grades"
        ]
    return _agreement_mismatch(result, agreement, predicted, where)


def _agreement_mismatch(
    result: dict[str, Any], agreement: Any, predicted: str, where: str
) -> list[str]:
    """The recorded label against what the prediction and outcome yield."""

    outcome = result.get("outcome")
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
