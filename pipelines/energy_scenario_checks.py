#!/usr/bin/env python3
"""Scenario checks for ``snn-energy-routing-preferences`` records.

Split out of ``energy_check.py`` verbatim: validate the declared scenario
(constraints, state, proposed actions) and the candidate-list binding
before any candidate is replayed.
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
    from .energy_allocation import _positive_weights
    from .energy_contract import (
        MAX_ACTUATORS,
        PREFERENCE_OBJECTIVE,
        SAFETY_ENVELOPE,
        SUPPORTED_COST_QUANTITIES,
    )
else:
    from energy_allocation import _positive_weights
    from energy_contract import (
        MAX_ACTUATORS,
        PREFERENCE_OBJECTIVE,
        SAFETY_ENVELOPE,
        SUPPORTED_COST_QUANTITIES,
    )


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
        isinstance(caps, list)
        and _positive_weights(weights)
        and len(weights) == len(caps)
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
