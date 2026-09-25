#!/usr/bin/env python3
"""Family validator for ``snn-energy-routing-preferences``.

Split out of ``energy_preferences.py`` verbatim: :func:`check_family` replays
the declared candidate policies, re-derives quality, safety and the preference
from the scenario, and reconciles every measurement against the meter that the
record claims produced it. Scenario checks live in
``energy_scenario_checks``, measurement/derivation checks in
``energy_measurement_checks``, per-candidate verdicts in
``energy_candidate_checks``, the preference layer in
``energy_preference_checks``, and oracle-audit checks in
``energy_audit_checks``. Every name here is re-exported from
``energy_preferences`` so existing call sites resolve unchanged.
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
    from .energy_audit_checks import (
        _check_fingerprinted_meter,
        _check_oracle_audit,
        _check_oracle_implementation_replayable,
        _replay_solver_settings,
    )
    from .energy_candidate_checks import _check_candidate, _check_candidate_success
    from .energy_check_types import _CandidateContext
    from .energy_measurement_checks import (
        _check_reference_objective,
        _collect_measured_costs,
        _quality_derivation_inputs,
        _safety_derivation_inputs,
    )
    from .energy_preference_checks import _check_preference
    from .energy_scenario_checks import (
        _check_candidate_binding,
        _check_cost_denomination,
        _check_scenario_constraints,
        _check_scenario_state,
    )
else:
    from energy_audit_checks import (
        _check_fingerprinted_meter,
        _check_oracle_audit,
        _check_oracle_implementation_replayable,
        _replay_solver_settings,
    )
    from energy_candidate_checks import _check_candidate, _check_candidate_success
    from energy_check_types import _CandidateContext
    from energy_measurement_checks import (
        _check_reference_objective,
        _collect_measured_costs,
        _quality_derivation_inputs,
        _safety_derivation_inputs,
    )
    from energy_preference_checks import _check_preference
    from energy_scenario_checks import (
        _check_candidate_binding,
        _check_cost_denomination,
        _check_scenario_constraints,
        _check_scenario_state,
    )


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
