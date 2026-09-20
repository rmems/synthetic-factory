#!/usr/bin/env python3
"""Family validator for ``snn-energy-routing-preferences``.

Split out of ``energy_preferences.py`` verbatim: :func:`check_family` replays
the declared candidate policies, re-derives quality, safety and the preference
from the scenario, and reconciles every measurement against the meter that the
record claims produced it. Every name here is re-exported from
``energy_preferences`` so existing call sites resolve unchanged.
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

_PIPELINES = Path(__file__).resolve().parent
if str(_PIPELINES) not in sys.path:
    sys.path.insert(0, str(_PIPELINES))

from oracle_grounded import distill_contract as oc  # noqa: E402

if __package__:
    from .energy_contract import (
        ABSTAIN_NO_FEASIBLE,
        ABSTAIN_NO_MEASUREMENT,
        DECISION_RULE,
        FAMILY,
        MAX_ACTUATORS,
        MAX_REPLAY_STEPS,
        PREFERENCE_OBJECTIVE,
        QUALITY_TOLERANCE,
        SAFETY_ENVELOPE,
        SUPPORTED_COST_QUANTITIES,
        _ORACLE_TYPE_BY_IMPLEMENTATION,
        _genuine_int_at_least,
    )
    from .energy_generator import (
        POLICY_DESCRIPTIONS,
        build_records,
        choose_preference,
        _check_run_knobs,
        _feasible_candidates,
        _policy_workloads,
    )
    from .energy_task import (
        PolicyEvaluation,
        analytic_allocation,
        evaluate_allocation,
        objective,
    )
else:
    from energy_contract import (
        ABSTAIN_NO_FEASIBLE,
        ABSTAIN_NO_MEASUREMENT,
        DECISION_RULE,
        FAMILY,
        MAX_ACTUATORS,
        MAX_REPLAY_STEPS,
        PREFERENCE_OBJECTIVE,
        QUALITY_TOLERANCE,
        SAFETY_ENVELOPE,
        SUPPORTED_COST_QUANTITIES,
        _ORACLE_TYPE_BY_IMPLEMENTATION,
        _genuine_int_at_least,
    )
    from energy_generator import (
        POLICY_DESCRIPTIONS,
        build_records,
        choose_preference,
        _check_run_knobs,
        _feasible_candidates,
        _policy_workloads,
    )
    from energy_task import (
        PolicyEvaluation,
        analytic_allocation,
        evaluate_allocation,
        objective,
    )


def _allocation_rejection(allocation: Any, caps: list[float]) -> str | None:
    """The reason an allocation cannot be evaluated at all, if there is one."""

    if allocation is None or (isinstance(allocation, list) and not allocation):
        return "NO_FEASIBLE_ALLOCATION_FOUND"
    if not isinstance(allocation, list) or not all(
        oc.is_number(value) for value in allocation
    ):
        return "ALLOCATION_NOT_NUMERIC"
    if len(allocation) != len(caps):
        return "ALLOCATION_WIDTH_MISMATCH"
    return None


def _allocation_shape_error(
    allocation: Any, caps: list[Any], spot: str
) -> list[str]:
    """A malformed allocation is record corruption, not a derived failure.

    The builder's only no-solution representation is ``None`` (stored as an
    empty vector). Anything else that is not a finite numeric vector of the
    actuator width never came from ``evaluate_allocation`` — converting it
    into ``ALLOCATION_NOT_NUMERIC`` let a tampered candidate restate the
    derived failure values and ship a fabricated policy failure to pairwise
    consumers.
    """

    if allocation is None or (isinstance(allocation, list) and not allocation):
        return []
    if (
        not isinstance(allocation, list)
        or not all(oc.is_number(value) for value in allocation)
        or len(allocation) != len(caps)
    ):
        return [
            f"{spot}.allocation must be null, empty, or a finite numeric "
            "vector with one entry per actuator cap"
        ]
    return []


def _cap_violations(allocation: list[Any], caps: list[float]) -> list[str]:
    """Per-actuator cap and sign violations, in actuator order."""

    violations: list[str] = []
    for index, (value, cap) in enumerate(zip(allocation, caps)):
        if float(value) > float(cap) + 1e-9:
            violations.append(f"ACTUATOR_{index}_OVER_CAP")
        if float(value) < -1e-9:
            violations.append(f"ACTUATOR_{index}_NEGATIVE")
    return violations


def _derive_safety(
    allocation: Any, demand: float, caps: list[float]
) -> tuple[bool, list[str]]:
    """Re-derive a candidate's safety from its allocation and the scenario.

    Mirrors :func:`evaluate_allocation`, so a record whose ``safety_ok`` was
    edited away from what its own allocation implies becomes a finding rather
    than a preferred candidate.
    """

    rejection = _allocation_rejection(allocation, caps)
    if rejection is not None:
        return False, [rejection]
    violations = _cap_violations(allocation, caps)
    if abs(sum(float(value) for value in allocation) - demand) > 1e-6:
        violations.append("DEMAND_NOT_MET")
    return (not violations), violations


@dataclass(frozen=True)
class _Reading:
    """One usable oracle reading: value, instrument, and whether it measured."""

    value: float
    meter: str
    measured: Any


@dataclass(frozen=True)
class _CandidateContext:
    """Record-level facts every candidate is checked against."""

    measured_costs: dict[tuple[str, str], _Reading]
    corpus_quantity: Any
    can_derive_safety: bool
    caps: Any
    demand: Any
    weights: list[float] | None
    optimum: float | None
    solver: tuple[int, int] | None = None


def _check_oracle_implementation_replayable(
    record: dict[str, Any], where: str
) -> list[str]:
    """Foreign ``oracle.implementation`` must not skip allocation replay.

    Renaming the implementation off ``pipelines/energy_preferences.py:`` used
    to set solver=None and leave allocation checks as no-ops while safety and
    quality still passed against a forged stored allocation.
    """

    oracle = record.get("oracle")
    if not isinstance(oracle, dict):
        return []
    implementation = oracle.get("implementation")
    if isinstance(implementation, str) and implementation.startswith(
        "pipelines/energy_preferences.py:"
    ):
        expected_type = _ORACLE_TYPE_BY_IMPLEMENTATION.get(implementation)
        if expected_type is not None and oracle.get("type") != expected_type:
            # A live meter stamped `recorded_measurement` (or a replay meter
            # stamped `measured_execution`) erases the distinction between a
            # cost measured on this run and one replayed from another run.
            return [
                f"{where}.oracle.type: ORACLE_TYPE_MISMATCH — "
                f"{implementation} must declare type {expected_type!r}, got "
                f"{oracle.get('type')!r}"
            ]
        return []
    return [
        f"{where}.oracle.implementation: ORACLE_IMPLEMENTATION_NOT_REPLAYABLE — "
        "this family's allocations are only authenticable when implementation "
        f"is under pipelines/energy_preferences.py:, got {implementation!r}"
    ]


def _replay_solver_settings(record: dict[str, Any]) -> tuple[int, int] | None:
    """``(fine_steps, coarse_steps)`` when this module's suite is replayable.

    Only records produced by this module's policy implementations can have
    their allocations recomputed; a foreign oracle's policies are not
    executable here. Malformed or out-of-range solver settings are reported
    by the oracle-audit check, so returning ``None`` for them does not open
    a bypass.
    """

    oracle = record.get("oracle")
    if not isinstance(oracle, dict):
        return None
    implementation = oracle.get("implementation")
    if not isinstance(implementation, str) or not implementation.startswith(
        "pipelines/energy_preferences.py:"
    ):
        return None
    configuration = oracle.get("configuration")
    if not isinstance(configuration, dict):
        return None
    fine = configuration.get("fine_steps")
    coarse = configuration.get("coarse_steps")
    for steps in (fine, coarse):
        if not _genuine_int_at_least(steps, 1) or steps > MAX_REPLAY_STEPS:
            return None
    return int(fine), int(coarse)


def _check_scenario_constraints(
    scenario: Any, where: str
) -> tuple[list[str], float | None]:
    """Constraint checks, and the quality floor the preference is held to."""

    errors: list[str] = []
    if not isinstance(scenario, dict):
        return errors, None
    if scenario.get("objective") != PREFERENCE_OBJECTIVE:
        errors.append(f"{where}.scenario.objective must state {PREFERENCE_OBJECTIVE!r}")
    constraints = scenario.get("constraints")
    if not isinstance(constraints, dict):
        errors.append(f"{where}.scenario.constraints must be an object")
        return errors, None
    quality_floor: float | None = None
    floor = constraints.get("quality_floor")
    if not oc.is_number(floor):
        errors.append(
            f"{where}.scenario.constraints.quality_floor must be a number"
        )
    elif not 0.0 <= float(floor) <= 1.0:
        # task_quality is a ratio in [0, 1]; a floor of -1 admits every safe
        # candidate regardless of quality, and a floor above 1 admits none.
        errors.append(
            f"{where}.scenario.constraints.quality_floor must lie in [0, 1], "
            f"got {floor!r}"
        )
    else:
        quality_floor = float(floor)
    if constraints.get("safety_envelope") != SAFETY_ENVELOPE:
        errors.append(
            f"{where}.scenario.constraints.safety_envelope must state the "
            f"enforced envelope {SAFETY_ENVELOPE!r}, got "
            f"{constraints.get('safety_envelope')!r} — the description the "
            "student sees has to be the rule the labels were derived under"
        )
    return errors, quality_floor


def _check_scenario_state(scenario: Any, where: str) -> list[str]:
    """The allocation state every label is grounded in must be re-derivable.

    Silently skipping derivation when the state is malformed would let a
    record drop ``scenario.state`` (or its demand, caps or weights) and
    disable the safety, quality and reference-objective checks in one move
    while its unchanged candidates stayed curation-eligible.
    """

    if not isinstance(scenario, dict):
        return []
    state = scenario.get("state")
    if not isinstance(state, dict):
        return [
            f"{where}.scenario.state must be an object carrying the "
            "allocation problem the candidates were measured on"
        ]
    errors: list[str] = []
    if not (
        oc.is_number(state.get("demand")) and float(state["demand"]) >= 0.0
    ):
        errors.append(
            f"{where}.scenario.state.demand must be a non-negative number"
        )
    caps = state.get("actuator_caps")
    if not (
        isinstance(caps, list)
        and caps
        and all(oc.is_number(cap) for cap in caps)
    ):
        errors.append(
            f"{where}.scenario.state.actuator_caps must be a non-empty array "
            "of numbers"
        )
    if isinstance(caps, list) and len(caps) > MAX_ACTUATORS:
        errors.append(
            f"{where}.scenario.state.actuator_caps must contain at most {MAX_ACTUATORS} "
            "actuators for bounded policy replay"
        )
    weights = state.get("actuator_weights")
    if not (
        isinstance(weights, list)
        and isinstance(caps, list)
        and weights
        and len(weights) == len(caps)
        and all(oc.is_number(w) and float(w) > 0.0 for w in weights)
    ):
        errors.append(
            f"{where}.scenario.state.actuator_weights must be positive "
            "numbers, one per actuator cap"
        )
    return errors


def _proposed_actions(scenario: Any) -> dict[str, Any] | None:
    """id -> description of the proposed candidate actions, or None if unusable."""

    actions = scenario.get("candidate_actions") if isinstance(scenario, dict) else None
    if not isinstance(actions, list) or not actions:
        return None
    proposed: dict[str, Any] = {}
    for action in actions:
        if not isinstance(action, dict) or not isinstance(action.get("id"), str):
            return None
        proposed[action["id"]] = action.get("description")
    if len(proposed) != len(actions):
        return None
    return proposed


def _check_candidate_binding(
    scenario: Any, candidates: list[Any], where: str
) -> list[str]:
    """The measured candidates must be the proposed decision problem's.

    The student is shown ``scenario.candidate_actions`` as the choices on
    offer; the oracle measured ``result.candidates``. Nothing reconciled the
    two, so a record could present one action set while its preference was
    grounded in another — pairing the visible decision problem with a winner
    the student was never offered.
    """

    proposed = _proposed_actions(scenario)
    if proposed is None:
        return [
            f"{where}.scenario.candidate_actions must list each proposed "
            "policy exactly once as an object with a string id"
        ]
    measured = {
        candidate["id"]: candidate.get("description")
        for candidate in candidates
        if isinstance(candidate, dict) and isinstance(candidate.get("id"), str)
    }
    if set(proposed) != set(measured):
        return [
            f"{where}: CANDIDATE_SET_MISMATCH — scenario.candidate_actions "
            f"proposes {sorted(proposed)} but result.candidates measured "
            f"{sorted(measured)}"
        ]
    return [
        f"{where}: candidate {candidate_id!r} is described as "
        f"{measured[candidate_id]!r} but was proposed as "
        f"{proposed[candidate_id]!r}"
        for candidate_id in sorted(proposed)
        if measured[candidate_id] != proposed[candidate_id]
    ]


def _check_cost_denomination(result: dict[str, Any], where: str) -> list[str]:
    """The corpus quantity, and the energy flag that must follow from it.

    The flag that tells a joule corpus from a second corpus. Readers,
    MANIFEST.json and the "no theoretical energy" rule all lean on it, so it
    has to follow from the quantity rather than be asserted alongside it.
    """

    errors: list[str] = []
    corpus_quantity = result.get("cost_quantity")
    cost_is_energy = result.get("cost_is_energy")
    if not oc.is_enum_value(corpus_quantity, SUPPORTED_COST_QUANTITIES):
        # Any registered quantity used to pass, so a record could quietly
        # minimise temperature or latency under this family's name.
        errors.append(
            f"{where}.result.cost_quantity must be one of "
            f"{sorted(SUPPORTED_COST_QUANTITIES)}, got {corpus_quantity!r}"
        )
    if not isinstance(cost_is_energy, bool):
        errors.append(f"{where}.result.cost_is_energy must be a boolean")
    elif cost_is_energy != oc.is_enum_value(corpus_quantity, oc.ENERGY_QUANTITIES):
        errors.append(
            f"{where}.result.cost_is_energy is {cost_is_energy} but cost_quantity "
            f"is {corpus_quantity!r} — the flag must follow the quantity"
        )
    return errors


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
        return evaluate_allocation(
            [float(value) for value in allocation],
            demand=float(context.demand),
            weights=context.weights,
            caps=caps,
            optimum=context.optimum,
            quality_floor=0.0,
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
    workloads = _policy_workloads(
        float(context.demand),
        context.weights,
        caps,
        fine_steps=fine_steps,
        coarse_steps=coarse_steps,
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


def _feasible_rivals(
    candidates: list[Any], preferred_id: Any, quality_floor: float
) -> list[dict[str, Any]]:
    """Every other candidate that is safe, clears the floor, and has a cost."""

    return [
        candidate
        for candidate in candidates
        if isinstance(candidate, dict)
        and candidate.get("id") != preferred_id
        and candidate.get("safety_ok") is True
        and oc.is_number(candidate.get("task_quality"))
        and float(candidate["task_quality"]) >= quality_floor
        and oc.is_number(candidate.get("cost_value"))
    ]


def _check_preferred_cost_minimality(
    preferred: dict[str, Any],
    candidates: list[Any],
    quality_floor: float,
    where: str,
) -> list[str]:
    """The preferred candidate must be the cheapest feasible one, tie-break included.

    ``preferred`` came out of a ``{candidate["id"]: candidate}`` index, so its
    ``id`` is the very object the preference named.
    """

    errors: list[str] = []
    preferred_id = preferred["id"]
    preferred_cost = float(preferred["cost_value"])
    feasible_rivals = _feasible_rivals(candidates, preferred_id, quality_floor)
    cheaper_feasible = [
        candidate["id"]
        for candidate in feasible_rivals
        if float(candidate["cost_value"]) < preferred_cost - 1e-12
    ]
    if cheaper_feasible:
        errors.append(
            f"{where}.result.preference: NOT_MINIMAL_FEASIBLE_COST — "
            f"{sorted(cheaper_feasible)} are feasible and cheaper than "
            f"{preferred_id!r}"
        )
    # `choose_preference` breaks a cost tie by candidate id, which coarse
    # counters make a real case rather than a theoretical one. Without this
    # either side of a tie validates, so the label is not a function of the
    # measurements.
    tied_lower_id = [
        candidate["id"]
        for candidate in feasible_rivals
        if abs(float(candidate["cost_value"]) - preferred_cost) <= 1e-12
        and isinstance(candidate.get("id"), str)
        and isinstance(preferred_id, str)
        and candidate["id"] < preferred_id
    ]
    if tied_lower_id:
        errors.append(
            f"{where}.result.preference: TIE_NOT_BROKEN_BY_ID — "
            f"{sorted(tied_lower_id)} tie {preferred_id!r} on measured cost "
            "and sort before it, so the documented tie-break selects the "
            "first of those instead"
        )
    return errors


def _derived_membership(
    candidates: list[Any], quality_floor: float, preferred: dict[str, Any]
) -> dict[str, list[str]]:
    """The membership lists ``choose_preference`` would derive."""

    rows = [
        candidate
        for candidate in candidates
        if isinstance(candidate, dict) and isinstance(candidate.get("id"), str)
    ]
    preferred_id = preferred["id"]
    preferred_cost = float(preferred["cost_value"])
    return {
        "over": sorted(row["id"] for row in rows if row["id"] != preferred_id),
        "feasible": sorted(
            row["id"] for row in _feasible_candidates(rows, quality_floor)
        ),
        "cheaper_but_constraint_violating": sorted(
            row["id"]
            for row in rows
            if row["id"] != preferred_id
            and oc.is_number(row.get("cost_value"))
            and float(row["cost_value"]) < preferred_cost
        ),
    }


def _membership_field_error(
    preference: dict[str, Any], field: str, expected: list[str], where: str
) -> list[str]:
    recorded = preference.get(field)
    recorded_ids = (
        sorted(str(item) for item in recorded) if isinstance(recorded, list) else None
    )
    if recorded_ids == expected:
        return []
    return [
        f"{where}.result.preference.{field}: "
        f"PREFERENCE_MEMBERSHIP_NOT_REPRODUCIBLE — recorded "
        f"{recorded!r} but the measured candidates yield {expected}"
    ]


def _check_preference_membership(
    preference: dict[str, Any],
    candidates: list[Any],
    quality_floor: float,
    preferred: dict[str, Any],
    where: str,
) -> list[str]:
    """``over``, ``feasible`` and the cheaper-but-rejected list are derived.

    ``choose_preference`` computes all three from the measured candidates.
    Left unchecked, a record could ship arbitrary lists — no opponents, a
    fabricated feasible set, or a false account of which constraints rejected
    each policy — while everything else validated clean, and pairwise
    consumers would train on that account.
    """

    errors: list[str] = []
    derived = _derived_membership(candidates, quality_floor, preferred)
    for field, expected in derived.items():
        errors += _membership_field_error(preference, field, expected, where)
    restated_floor = preference.get("quality_floor")
    if not oc.is_number(restated_floor) or (
        abs(float(restated_floor) - quality_floor) > 1e-12
    ):
        errors.append(
            f"{where}.result.preference.quality_floor is {restated_floor!r} "
            f"but the scenario constraint is {quality_floor}"
        )
    return errors


def _check_preference_restatement(
    preference: dict[str, Any], preferred: dict[str, Any], where: str
) -> list[str]:
    """The preference restates the winner's cost; it must not drift.

    If that restatement is free to drift, a record can advertise a cheap
    energy figure while the candidate it points at was measured in seconds.
    """

    errors: list[str] = []
    preferred_id = preferred["id"]
    if preference.get("cost_quantity") != preferred.get("cost_quantity"):
        errors.append(
            f"{where}.result.preference.cost_quantity is "
            f"{preference.get('cost_quantity')!r} but {preferred_id!r} was measured "
            f"in {preferred.get('cost_quantity')!r}"
        )
    if not oc.is_number(preference.get("cost_value")) or (
        oc.is_number(preferred.get("cost_value"))
        and abs(float(preference["cost_value"]) - float(preferred["cost_value"])) > 1e-12
    ):
        errors.append(
            f"{where}.result.preference.cost_value is "
            f"{preference.get('cost_value')!r} but {preferred_id!r} measured "
            f"{preferred.get('cost_value')!r}"
        )
    return errors


def _check_preferred_feasibility(
    preferred: dict[str, Any], quality_floor: float | None, where: str
) -> list[str]:
    """The winner must itself be safe and clear the quality floor."""

    errors: list[str] = []
    preferred_id = preferred["id"]
    if not oc.is_true(preferred.get("safety_ok")):
        errors.append(
            f"{where}.result.preference: PREFERRED_CANDIDATE_UNSAFE — "
            f"{preferred_id!r} violates {preferred.get('safety_violations')}"
        )
    if quality_floor is not None and oc.is_number(preferred.get("task_quality")):
        if float(preferred["task_quality"]) < quality_floor:
            errors.append(
                f"{where}.result.preference: PREFERRED_CANDIDATE_BELOW_QUALITY_FLOOR "
                f"({preferred['task_quality']} < {quality_floor})"
            )
    return errors


def _preferred_candidate(
    preference: dict[str, Any], candidates: list[Any]
) -> dict[str, Any] | None:
    """The candidate the preference names, if it names a measured one."""

    preferred = preference.get("preferred")
    if not isinstance(preferred, str) or not preferred:
        # A JSON object or array here is unhashable: looking it up raised
        # TypeError straight out of the family checker, and validate_path does
        # not catch that — one malformed record aborted validation of the
        # whole run instead of being reported as one bad line.
        return None
    by_id = {
        candidate["id"]: candidate
        for candidate in candidates
        if isinstance(candidate, dict) and isinstance(candidate.get("id"), str)
    }
    return by_id.get(preferred)


def _check_abstention_feasibility(
    result: dict[str, Any],
    candidates: list[Any],
    quality_floor: float | None,
    where: str,
) -> list[str]:
    """An abstention must be earned by the measured candidates.

    The family's only abstention path is ``choose_preference`` finding no
    feasible candidate, so a record relabelled ``abstained`` while its own
    measurements still contain safe, quality-clearing, costed candidates is
    a silently discarded label, not an oracle abstention.
    """

    if quality_floor is None:
        # The malformed floor carries its own finding; without it the
        # feasible set cannot be re-derived.
        return []
    errors: list[str] = []
    reason = result.get("abstention_reason")
    if reason != ABSTAIN_NO_FEASIBLE:
        errors.append(
            f"{where}.result.abstention_reason must be the canonical "
            f"{ABSTAIN_NO_FEASIBLE!r} — it is this family's only abstention"
        )
    feasible = _feasible_candidates(
        [c for c in candidates if isinstance(c, dict)], quality_floor
    )
    if feasible:
        errors.append(
            f"{where}.result: FALSE_ABSTENTION — "
            f"{sorted(c['id'] for c in feasible if isinstance(c.get('id'), str))} "
            "satisfy the quality and safety constraints, so the oracle had a "
            "preference to record"
        )
    return errors


def _check_preference(
    result: dict[str, Any],
    candidates: list[Any],
    quality_floor: float | None,
    where: str,
) -> list[str]:
    """The preference, and the restatements of the winner it must agree with."""

    errors: list[str] = []
    status = result.get("status")
    preference = result.get("preference")
    if status == oc.RESULT_ABSTAINED:
        if preference is not None:
            errors.append(
                f"{where}.result: an abstained result must not carry a preference"
            )
        return errors + _check_abstention_feasibility(
            result, candidates, quality_floor, where
        )
    if not isinstance(preference, dict):
        return errors + [
            f"{where}.result.preference must be an object (or the result must abstain)"
        ]
    if preference.get("decision_rule") != DECISION_RULE:
        errors.append(f"{where}.result.preference.decision_rule must be {DECISION_RULE!r}")
    preferred = _preferred_candidate(preference, candidates)
    if preferred is None:
        return errors + [
            f"{where}.result.preference.preferred must name a measured candidate"
        ]
    errors += _check_preference_restatement(preference, preferred, where)
    errors += _check_preferred_feasibility(preferred, quality_floor, where)
    # A non-numeric preferred cost is a finding, not an exception. `float()` on
    # it used to raise straight out of the family checker, and validate_path
    # does not catch that — one malformed record would abort validation of the
    # entire run instead of being reported as one bad line.
    if quality_floor is not None and oc.is_number(preferred.get("cost_value")):
        errors += _check_preferred_cost_minimality(
            preferred, candidates, quality_floor, where
        )
        errors += _check_preference_membership(
            preference, candidates, quality_floor, preferred, where
        )
    return errors


def _check_oracle_audit(record: dict[str, Any], where: str) -> list[str]:
    """The audit metadata behind an authoritative measured preference.

    Nothing validated ``oracle.configuration`` or ``oracle.fingerprint``, so
    deleting both left a record curation-eligible while no longer
    identifying the meter host, probe result, repeat/warmup settings, or
    solver configuration behind its measured costs — the documented audit
    trail for oracle-grounded energy.
    """

    oracle = record.get("oracle")
    if not isinstance(oracle, dict):
        # The envelope reports a missing or malformed oracle block.
        return []
    errors: list[str] = []
    fingerprint = oracle.get("fingerprint")
    if not isinstance(fingerprint, dict) or not fingerprint:
        errors.append(
            f"{where}.oracle.fingerprint must identify the meter host that "
            "measured this record"
        )
    configuration = oracle.get("configuration")
    if not isinstance(configuration, dict):
        return errors + [
            f"{where}.oracle.configuration must record the meter probe and "
            "solver settings behind the measured costs"
        ]
    errors += _check_configuration_bounds(configuration, where)
    return errors + _check_meter_probe(configuration, record.get("result"), where)


def _check_meter_probe(configuration: dict[str, Any], result: Any, where: str) -> list[str]:
    """Reconcile the selected meter probe with the declared cost quantity."""

    errors: list[str] = []
    probe = configuration.get("meter_probe")
    if not isinstance(probe, dict):
        return errors + [
            f"{where}.oracle.configuration.meter_probe must document the "
            "probed meters and the selection"
        ]
    selected = probe.get("selected")
    if not isinstance(selected, str) or not selected.strip():
        errors.append(
            f"{where}.oracle.configuration.meter_probe.selected must name "
            "the selected meter"
        )
    else:
        probed = probe.get("probed")
        entries = (
            [entry for entry in probed if isinstance(entry, dict)]
            if isinstance(probed, list)
            else []
        )
        if not any(
            entry.get("meter") == selected and entry.get("available") is True
            for entry in entries
        ):
            errors.append(
                f"{where}.oracle.configuration.meter_probe.selected is "
                f"{selected!r} but the probe found no such meter available — "
                "the audit must name a meter that was actually probed and "
                "usable"
            )
    corpus_quantity = result.get("cost_quantity") if isinstance(result, dict) else None
    cost_is_energy = result.get("cost_is_energy") if isinstance(result, dict) else None
    if probe.get("cost_quantity") != corpus_quantity:
        errors.append(
            f"{where}.oracle.configuration.meter_probe.cost_quantity is "
            f"{probe.get('cost_quantity')!r} but the corpus is denominated "
            f"in {corpus_quantity!r}"
        )
    if probe.get("cost_is_energy") != cost_is_energy:
        errors.append(
            f"{where}.oracle.configuration.meter_probe.cost_is_energy is "
            f"{probe.get('cost_is_energy')!r} but result.cost_is_energy is "
            f"{cost_is_energy!r}"
        )
    return errors


def _check_configuration_bounds(configuration: dict[str, Any], where: str) -> list[str]:
    """Match declared execution bounds to the domains accepted by the builder."""

    errors: list[str] = []
    # The same domains the builder refuses to run outside of. "Any number"
    # let a record declare a fractional warmup or a billion-step grid — an
    # audit no execution matches, and (for the grid) a replay bound nothing
    # could afford to honour.
    for key, floor, ceiling in (
        ("repeats", 1, None),
        ("warmup", 0, None),
        ("fine_steps", 1, MAX_REPLAY_STEPS),
        ("coarse_steps", 1, MAX_REPLAY_STEPS),
    ):
        value = configuration.get(key)
        if not _genuine_int_at_least(value, floor) or (
            ceiling is not None and value > ceiling
        ):
            bound = f" and <= {ceiling}" if ceiling is not None else ""
            errors.append(
                f"{where}.oracle.configuration.{key} must be an integer "
                f">= {floor}{bound}, got {value!r}"
            )
    return errors


def _check_fingerprinted_meter(
    record: dict[str, Any], candidates: list[Any], where: str
) -> list[str]:
    oracle = record.get("oracle")
    fingerprint = oracle.get("fingerprint") if isinstance(oracle, dict) else None
    meter = fingerprint.get("meter") if isinstance(fingerprint, dict) else None
    if not isinstance(meter, str) or not meter.strip():
        return [f"{where}.oracle.fingerprint.meter must name the physical instrument"]
    return [
        f"{where}.result.candidates[{index}].cost_meter must match oracle.fingerprint.meter"
        for index, candidate in enumerate(candidates)
        if isinstance(candidate, dict) and candidate.get("cost_meter") != meter
    ]


def check_family(record: dict[str, Any], where: str) -> list[str]:
    """Family checks: measured cost, and a preference that respects limits."""

    scenario = record.get("scenario")
    errors, quality_floor = _check_scenario_constraints(scenario, where)
    errors += _check_scenario_state(scenario, where)
    errors += oc.check_oracle_label_leak(record, where)
    errors += _check_oracle_audit(record, where)

    result = record.get("result")
    if not isinstance(result, dict):
        return errors + [f"{where}.result must be an object"]

    candidates = result.get("candidates")
    if not isinstance(candidates, list) or len(candidates) < 2:
        return errors + [
            f"{where}.result.candidates must list at least two measured candidates"
        ]

    errors += _check_fingerprinted_meter(record, candidates, where)
    errors += _check_candidate_binding(scenario, candidates, where)
    errors += _check_cost_denomination(result, where)
    measurement_errors, measured_costs = _collect_measured_costs(result, where)
    errors += measurement_errors

    errors += _check_oracle_implementation_replayable(record, where)

    can_derive_safety, caps, demand = _safety_derivation_inputs(scenario)
    weights, optimum = _quality_derivation_inputs(
        scenario, can_derive_safety=can_derive_safety, caps=caps, demand=demand
    )
    context = _CandidateContext(
        measured_costs=measured_costs,
        corpus_quantity=result.get("cost_quantity"),
        can_derive_safety=can_derive_safety,
        caps=caps,
        demand=demand,
        weights=weights,
        optimum=optimum,
        solver=_replay_solver_settings(record),
    )
    errors += _check_reference_objective(result, context, where)

    seen_candidate_ids: set[str] = set()
    for index, candidate in enumerate(candidates):
        spot = f"{where}.result.candidates[{index}]"
        errors += _check_candidate(candidate, spot, seen_candidate_ids, context)
        errors += _check_candidate_success(candidate, spot, quality_floor)

    return errors + _check_preference(result, candidates, quality_floor, where)
