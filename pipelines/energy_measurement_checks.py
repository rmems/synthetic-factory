#!/usr/bin/env python3
"""Measurement and derivation checks for ``snn-energy-routing-preferences``.

Split out of ``energy_check.py`` verbatim: collect the usable meter
readings a candidate claims, derive the quality and safety inputs from
the scenario, and re-derive the recorded quality from those inputs.
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
        _allocation_rejection,
    )
    from .energy_check_types import (
        _CandidateContext,
        _Reading,
    )
    from .energy_contract import (
        MAX_ACTUATORS,
        QUALITY_TOLERANCE,
    )
    from .energy_task import (
        ProblemSpec,
        analytic_allocation,
        evaluate_allocation,
        objective,
    )
else:
    from energy_allocation import (
        _allocation_rejection,
    )
    from energy_check_types import (
        _CandidateContext,
        _Reading,
    )
    from energy_contract import (
        MAX_ACTUATORS,
        QUALITY_TOLERANCE,
    )
    from energy_task import (
        ProblemSpec,
        analytic_allocation,
        evaluate_allocation,
        objective,
    )


def _usable_measurement(item: Any) -> tuple[tuple[str, str], _Reading] | None:
    """The ``(key, reading)`` of a measurement, or None if it is not usable."""

    if not isinstance(item, dict):
        return None
    detail = item.get("detail")
    candidate_id = detail.get("candidate") if isinstance(detail, dict) else None
    quantity = item.get("quantity")
    meter = item.get("meter")
    if (
        isinstance(candidate_id, str)
        and isinstance(quantity, str)
        and oc.is_number(item.get("value"))
        and isinstance(meter, str)
    ):
        reading = _Reading(
            value=item["value"], meter=meter, measured=item.get("measured")
        )
        return (candidate_id, quantity), reading
    return None

def _collect_measured_costs(
    result: dict[str, Any], where: str
) -> tuple[list[str], dict[tuple[str, str], _Reading]]:
    """Index the oracle measurements, reporting readings that contradict.

    Keyed by a tuple, not a joined string, so a candidate id containing the
    separator cannot be made to collide with another candidate's reading.
    """

    errors: list[str] = []
    measured_costs: dict[tuple[str, str], _Reading] = {}
    measurements = result.get("measurements")
    measurements = measurements if isinstance(measurements, list) else []
    for item in measurements:
        usable = _usable_measurement(item)
        if usable is None:
            continue
        key, reading = usable
        previous = measured_costs.get(key)
        if previous is None:
            measured_costs[key] = reading
            continue
        # Silently keeping the first reading made the preference depend
        # on JSON array order while the record still carried the
        # contradicting one. Two readings that disagree are a finding.
        if (
            abs(float(previous.value) - float(reading.value)) > 1e-12
            or previous.meter != reading.meter
            or (previous.measured is True) != (reading.measured is True)
        ):
            candidate_id, quantity = key
            errors.append(
                f"{where}.result.measurements: CONFLICTING_MEASUREMENT — "
                f"{quantity} for candidate {candidate_id!r} is recorded "
                f"both as {previous.value!r} ({previous.meter}) and "
                f"{reading.value!r} ({reading.meter})"
            )
    return errors, measured_costs

def _safety_derivation_inputs(scenario: Any) -> tuple[bool, Any, Any]:
    """The scenario state needed to re-derive a candidate's safety verdict."""

    state = scenario.get("state") if isinstance(scenario, dict) else None
    caps = state.get("actuator_caps") if isinstance(state, dict) else None
    demand = state.get("demand") if isinstance(state, dict) else None
    can_derive_safety = (
        isinstance(caps, list)
        and 1 <= len(caps) <= MAX_ACTUATORS
        and all(oc.is_number(cap) for cap in caps)
        and oc.is_number(demand)
    )
    return can_derive_safety, caps, demand


# Slack for re-deriving task_quality from a recorded allocation. Allocations
# are stored rounded to 9 places and qualities to 6, so an exact comparison
# would reject honest records; a real tamper has to move the quality by
# orders of magnitude more than this to matter against a 0.98 floor.

def _usable_weights(scenario: Any, caps: Any) -> list[float] | None:
    """The actuator weights, when they can parameterise the objective."""

    state = scenario.get("state") if isinstance(scenario, dict) else None
    weights = state.get("actuator_weights") if isinstance(state, dict) else None
    if (
        isinstance(weights, list)
        and len(weights) == len(caps)
        and all(oc.is_number(w) and float(w) > 0.0 for w in weights)
    ):
        return [float(w) for w in weights]
    return None

def _quality_derivation_inputs(
    scenario: Any, *, can_derive_safety: bool, caps: Any, demand: Any
) -> tuple[list[float] | None, float | None]:
    """The weights and re-derived optimum quality is measured against."""

    if not can_derive_safety:
        return None, None
    weights = _usable_weights(scenario, caps)
    if weights is None:
        return None, None
    optimum = objective(
        weights,
        analytic_allocation(float(demand), weights, [float(cap) for cap in caps]),
    )
    return weights, optimum

def _derived_quality(allocation: Any, context: _CandidateContext) -> float | None:
    """The task quality this allocation earns, or None when unevaluable.

    Non-numeric or wrong-width allocations are already reported by the safety
    derivation; a policy that produced no answer has quality 0.0 by definition.
    """

    caps = [float(cap) for cap in context.caps]
    if _allocation_rejection(allocation, caps) is None:
        problem = ProblemSpec(
            demand=float(context.demand),
            weights=context.weights,
            caps=caps,
            optimum=context.optimum,
            quality_floor=0.0,
        )
        return evaluate_allocation(
            [float(value) for value in allocation], problem
        ).task_quality
    if allocation is None or (isinstance(allocation, list) and not allocation):
        return 0.0
    return None

def _check_quality_derivation(
    candidate: dict[str, Any], spot: str, context: _CandidateContext
) -> list[str]:
    """task_quality is a function of the allocation and the scenario state.

    Binding the candidate's quality to its oracle measurement is not enough:
    editing both together keeps them agreeing while lowering the cheapest safe
    candidate below the floor, so a correctly rehashed record could steer the
    preference to a more expensive candidate and stay validation-clean.
    Re-deriving the quality from the recorded allocation pins both stored
    values to the arithmetic the scenario defines.
    """

    if context.optimum is None or context.weights is None:
        return []
    derived = _derived_quality(candidate.get("allocation"), context)
    if derived is None:
        return []
    recorded = candidate.get("task_quality")
    if oc.is_number(recorded) and abs(float(recorded) - derived) > QUALITY_TOLERANCE:
        return [
            f"{spot}: QUALITY_NOT_REPRODUCIBLE — task_quality is {recorded} "
            f"but re-evaluating the recorded allocation against the scenario "
            f"state yields {derived}"
        ]
    return []

def _check_reference_objective(
    result: dict[str, Any], context: _CandidateContext, where: str
) -> list[str]:
    """The restated reference objective must match the scenario's own optimum."""

    if context.optimum is None:
        return []
    recorded = result.get("reference_objective")
    if not oc.is_number(recorded):
        # The scenario supplies everything needed to derive the optimum, so
        # a deleted or non-numeric restatement is a finding — skipping the
        # comparison silently lost the reference target that grounds
        # candidate quality.
        return [
            f"{where}.result.reference_objective must restate the scenario "
            f"optimum as a finite number — the state derives "
            f"{round(context.optimum, 12)}"
        ]
    if abs(float(recorded) - context.optimum) > 1e-9:
        return [
            f"{where}.result.reference_objective is {recorded} but the "
            f"scenario state yields {round(context.optimum, 12)}"
        ]
    return []
