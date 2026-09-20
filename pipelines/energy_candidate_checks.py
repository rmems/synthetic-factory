#!/usr/bin/env python3
"""Per-candidate verdict checks for ``snn-energy-routing-preferences``.

Split out of ``energy_check.py`` verbatim: reconcile each recorded
candidate — safety, quality and cost bindings, measurements, the success
flag — and replay the solver to confirm the recorded allocation.
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
    from .energy_allocation import (
        _allocation_shape_error,
        _derive_safety,
    )
    from .energy_check_types import _CandidateContext
    from .energy_contract import SUPPORTED_COST_QUANTITIES
    from .energy_generator import (
        MeterProtocol,
        POLICY_DESCRIPTIONS,
        _policy_workloads,
    )
    from .energy_measurement_checks import _check_quality_derivation
    from .energy_task import ProblemSpec
else:
    from energy_allocation import (
        _allocation_shape_error,
        _derive_safety,
    )
    from energy_check_types import _CandidateContext
    from energy_contract import SUPPORTED_COST_QUANTITIES
    from energy_generator import (
        MeterProtocol,
        POLICY_DESCRIPTIONS,
        _policy_workloads,
    )
    from energy_measurement_checks import _check_quality_derivation
    from energy_task import ProblemSpec


def _check_candidate_safety(
    candidate: dict[str, Any], spot: str, context: _CandidateContext
) -> list[str]:
    """safety_ok and safety_violations, re-derived from the scenario state."""

    errors: list[str] = []
    if not isinstance(candidate.get("safety_ok"), bool):
        errors.append(f"{spot}.safety_ok must be a boolean")
    elif context.can_derive_safety:
        shape_errors = _allocation_shape_error(
            candidate.get("allocation"), list(context.caps), spot
        )
        if shape_errors:
            # Deriving from a corrupt allocation would only restate the
            # fabricated failure the tamper wrote; report the corruption.
            return errors + shape_errors
        # safety_ok summarises the allocation; it is not an independent
        # fact. Trusting it lets an obviously over-cap allocation be
        # preferred as the feasible minimum.
        derived_ok, derived_violations = _derive_safety(
            candidate.get("allocation"),
            float(context.demand),
            [float(c) for c in context.caps],
        )
        if candidate["safety_ok"] is not derived_ok:
            errors.append(
                f"{spot}: SAFETY_NOT_REPRODUCIBLE — safety_ok is "
                f"{candidate['safety_ok']} but the recorded allocation "
                f"against the scenario state yields {derived_ok} "
                f"({sorted(derived_violations)})"
            )
        recorded_violations = candidate.get("safety_violations")
        if not isinstance(recorded_violations, list):
            # The list is derived; absence is a finding, not a pass. Deleting
            # it from an unsafe candidate and rehashing left pairwise
            # consumers with a constraint-rejected candidate and no recorded
            # reason.
            errors.append(
                f"{spot}.safety_violations must list the violations the "
                f"recorded allocation derives ({sorted(derived_violations)}), "
                f"got {recorded_violations!r}"
            )
        elif sorted(
            str(item) for item in recorded_violations
        ) != sorted(derived_violations):
            errors.append(
                f"{spot}: SAFETY_NOT_REPRODUCIBLE — safety_violations are "
                f"{sorted(str(v) for v in recorded_violations)} but the "
                f"allocation yields {sorted(derived_violations)}"
            )
    return errors

def _check_quality_binding(
    candidate: dict[str, Any],
    candidate_id: str,
    spot: str,
    context: _CandidateContext,
) -> list[str]:
    """Quality gates the preference as hard as cost, so bind it to its measurement.

    Otherwise a candidate can claim 0.99 while its oracle measurement says
    0.0 and still clear the floor.
    """

    quality_key = (candidate_id, "task_quality")
    reading = context.measured_costs.get(quality_key)
    if reading is None:
        return [
            f"{spot}: UNMEASURED_TASK_QUALITY — no oracle measurement of "
            f"task_quality for candidate {candidate_id!r}"
        ]
    errors: list[str] = []
    if reading.measured is not True:
        # A reading marked `measured: false` is a model wearing a
        # measurement's clothes. Quality gates the preference, so the reading
        # that backs it has to be one the oracle actually took.
        errors.append(
            f"{spot}: UNMEASURED_TASK_QUALITY — the task_quality reading for "
            f"candidate {candidate_id!r} is marked measured: "
            f"{reading.measured!r}, so nothing measured backs the quality gate"
        )
    if oc.is_number(candidate.get("task_quality")) and (
        abs(reading.value - float(candidate["task_quality"])) > 1e-9
    ):
        errors.append(
            f"{spot}.task_quality disagrees with the oracle measurement "
            f"({candidate['task_quality']} vs {reading.value})"
        )
    return errors

def _check_cost_binding(
    candidate: dict[str, Any],
    candidate_id: str,
    spot: str,
    context: _CandidateContext,
) -> list[str]:
    """Bind the recorded cost and its instrument to the oracle measurement."""

    quantity = candidate.get("cost_quantity")
    candidate_meter = candidate.get("cost_meter")
    reading = context.measured_costs.get((candidate_id, quantity))
    if reading is None:
        return [
            f"{spot}: UNMEASURED_COST — no oracle measurement of {quantity} "
            f"for candidate {candidate_id!r}"
        ]
    errors: list[str] = []
    if reading.measured is not True:
        # The preference minimises this number. A cost whose backing reading
        # says `measured: false` is a modelled cost, which is exactly what
        # this family exists to refuse.
        errors.append(
            f"{spot}: UNMEASURED_COST — the {quantity} reading backing "
            f"candidate {candidate_id!r} is marked measured: "
            f"{reading.measured!r}, so no measured cost stands behind it"
        )
    if abs(reading.value - float(candidate["cost_value"])) > 1e-12:
        errors.append(
            f"{spot}.cost_value disagrees with the oracle measurement "
            f"({candidate['cost_value']} vs {reading.value})"
        )
    if reading.meter != candidate_meter:
        errors.append(
            f"{spot}.cost_meter is {candidate_meter!r} but the measurement "
            f"meter is {reading.meter!r}"
        )
    return errors

def _check_candidate_measurements(
    candidate: dict[str, Any],
    candidate_id: str,
    spot: str,
    context: _CandidateContext,
) -> list[str]:
    """Bind a candidate's quality, cost and meter to the oracle measurements."""

    errors: list[str] = []
    quantity = candidate.get("cost_quantity")
    if not oc.is_enum_value(quantity, SUPPORTED_COST_QUANTITIES):
        errors.append(
            f"{spot}.cost_quantity must be one of "
            f"{sorted(SUPPORTED_COST_QUANTITIES)}, got {quantity!r}"
        )
        return errors
    if (
        oc.is_enum_value(context.corpus_quantity, oc.QUANTITY_UNITS)
        and quantity != context.corpus_quantity
    ):
        errors.append(
            f"{spot}.cost_quantity is {quantity!r} but the record is "
            f"denominated in {context.corpus_quantity!r} — costs must be comparable"
        )
    if not oc.is_number(candidate.get("cost_value")):
        errors.append(f"{spot}.cost_value must be a number")
        return errors
    if float(candidate["cost_value"]) < 0.0:
        # Cheapest wins, so a negative cost takes the preference outright.
        # No meter in this pipeline can produce one.
        errors.append(
            f"{spot}: NEGATIVE_COST — {candidate['cost_value']} "
            f"{quantity} is not a physically possible measurement"
        )
    candidate_meter = candidate.get("cost_meter")
    if not isinstance(candidate_meter, str) or not candidate_meter:
        errors.append(f"{spot}.cost_meter must be a non-empty string")
        return errors
    # cost_meter names the *instrument*, not the oracle. On the replay path
    # the oracle is `recorded_power_run` while the instrument that actually
    # took the reading stays `external_power_meter`, so pinning cost_meter to
    # oracle.name or meter_probe.selected would reject every recorded run.
    # Bind the candidate to its cited measurement here; the family audit
    # also binds that instrument to oracle.fingerprint.meter.
    errors += _check_quality_binding(candidate, candidate_id, spot, context)
    errors += _check_cost_binding(candidate, candidate_id, spot, context)
    return errors

def _check_candidate_success(
    candidate: Any, spot: str, quality_floor: float | None
) -> list[str]:
    """``success`` is a summary of safety and the floor, not a free bit.

    ``build_records`` writes ``success = safety_ok and task_quality >=
    quality_floor``; nothing re-derived it, so flipping the unsafe
    candidate's ``false`` to ``true`` and rehashing left a curation-eligible
    record with contradictory candidate labels.
    """

    if not isinstance(candidate, dict):
        return []
    success = candidate.get("success")
    if not isinstance(success, bool):
        return [f"{spot}.success must be a boolean"]
    if quality_floor is None or not oc.is_number(candidate.get("task_quality")):
        # The floor and the quality carry their own findings when malformed;
        # without them the summary cannot be re-derived.
        return []
    expected = (
        candidate.get("safety_ok") is True
        and float(candidate["task_quality"]) >= quality_floor
    )
    if success is not expected:
        return [
            f"{spot}.success is {success} but safety_ok "
            f"{candidate.get('safety_ok')!r} and task_quality "
            f"{candidate['task_quality']} against quality_floor "
            f"{quality_floor} give {expected}"
        ]
    return []

def _expected_policy_allocation(
    candidate_id: str, context: _CandidateContext
) -> list[float]:
    """The stored form of the allocation the named policy computes here."""

    fine_steps, coarse_steps = context.solver
    caps = [float(cap) for cap in context.caps]
    problem = ProblemSpec(
        demand=float(context.demand),
        weights=context.weights,
        caps=caps,
        optimum=context.optimum,
        quality_floor=0.0,
    )
    workloads = _policy_workloads(
        problem, MeterProtocol(fine_steps=fine_steps, coarse_steps=coarse_steps)
    )
    allocation = workloads[candidate_id]()
    if allocation is None:
        return []
    return [round(float(value), 9) for value in allocation]

def _check_allocation_reproducibility(
    candidate: dict[str, Any],
    candidate_id: str,
    spot: str,
    context: _CandidateContext,
) -> list[str]:
    """The stored allocation must be what the named policy computes.

    Safety, quality and cost are all re-derived from the *stored* allocation,
    so replacing one policy's allocation with another's — updating the
    derived fields consistently and rehashing — stayed validation-clean while
    the retained measured cost was still the named workload's. The policies
    are deterministic functions of the scenario state and the recorded solver
    settings, so the advertised output is recomputed rather than trusted.
    """

    if (
        context.solver is None
        or not context.can_derive_safety
        or context.weights is None
    ):
        return []
    if candidate_id not in POLICY_DESCRIPTIONS:
        return [
            f"{spot}: UNKNOWN_POLICY_ID — {candidate_id!r} is not one of this "
            f"oracle's executable policies {sorted(POLICY_DESCRIPTIONS)}, so "
            "its allocation cannot be recomputed"
        ]
    recorded = candidate.get("allocation")
    if not isinstance(recorded, list) or not all(
        oc.is_number(value) for value in recorded
    ):
        # The safety derivation already reports the malformed shape.
        return []
    expected = _expected_policy_allocation(candidate_id, context)
    if len(recorded) != len(expected) or any(
        abs(float(value) - target) > 1e-9
        for value, target in zip(recorded, expected)
    ):
        return [
            f"{spot}: ALLOCATION_NOT_REPRODUCIBLE — the recorded allocation "
            f"is not what policy {candidate_id!r} computes on this scenario "
            f"state with the recorded solver settings ({expected})"
        ]
    return []

def _check_candidate(
    candidate: Any,
    spot: str,
    seen_candidate_ids: set[str],
    context: _CandidateContext,
) -> list[str]:
    """One measured candidate, in the order the findings were emitted."""

    if not isinstance(candidate, dict):
        return [f"{spot} must be an object"]
    candidate_id = candidate.get("id")
    if not isinstance(candidate_id, str) or not candidate_id:
        return [f"{spot}.id must be a non-empty string"]
    if candidate_id in seen_candidate_ids:
        # The preference names a candidate by id. Two candidates sharing one
        # makes the winning allocation ambiguous, and the cost measurements
        # can no longer be attributed to either.
        return [
            f"{spot}: DUPLICATE_CANDIDATE_ID — {candidate_id!r} is already "
            "used by an earlier candidate"
        ]
    seen_candidate_ids.add(candidate_id)
    errors = _check_candidate_safety(candidate, spot, context)
    if not oc.is_number(candidate.get("task_quality")):
        errors.append(f"{spot}.task_quality must be a number")
    errors += _check_quality_derivation(candidate, spot, context)
    errors += _check_allocation_reproducibility(candidate, candidate_id, spot, context)
    errors += _check_candidate_measurements(candidate, candidate_id, spot, context)
    return errors
