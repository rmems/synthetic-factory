#!/usr/bin/env python3
"""Preference-layer checks for ``snn-energy-routing-preferences`` records.

Split out of ``energy_check.py`` verbatim: feasible rivals, preferred
cost minimality, membership and restatement, abstention feasibility, and
the :func:`_check_preference` driver that applies them in order.
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
    from .energy_contract import (
        ABSTAIN_NO_FEASIBLE,
        DECISION_RULE,
    )
    from .energy_generator import _feasible_candidates
else:
    from energy_contract import (
        ABSTAIN_NO_FEASIBLE,
        DECISION_RULE,
    )
    from energy_generator import _feasible_candidates


def _feasible_rivals(
    candidates: list[Any], preferred_id: Any, quality_floor: float
) -> list[dict[str, Any]]:
    """Every other candidate that is safe, clears the floor, and has a cost."""

    return [
        candidate
        for candidate in candidates
        if _feasible_rival(candidate, preferred_id, quality_floor)
    ]

def _feasible_rival(
    candidate: Any, preferred_id: Any, quality_floor: float
) -> bool:
    """One candidate that is safe, clears the floor, and has a cost."""

    if not isinstance(candidate, dict):
        return False
    if candidate.get("id") == preferred_id or candidate.get("safety_ok") is not True:
        return False
    quality = candidate.get("task_quality")
    if not oc.is_number(quality) or float(quality) < quality_floor:
        return False
    return oc.is_number(candidate.get("cost_value"))

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
        if _tie_broken_below(candidate, preferred_id, preferred_cost)
    ]
    if tied_lower_id:
        errors.append(
            f"{where}.result.preference: TIE_NOT_BROKEN_BY_ID — "
            f"{sorted(tied_lower_id)} tie {preferred_id!r} on measured cost "
            "and sort before it, so the documented tie-break selects the "
            "first of those instead"
        )
    return errors

def _tie_broken_below(
    candidate: dict[str, Any], preferred_id: Any, preferred_cost: float
) -> bool:
    """A rival tied on measured cost that the id tie-break must take first."""

    if abs(float(candidate["cost_value"]) - preferred_cost) > 1e-12:
        return False
    if not isinstance(candidate.get("id"), str):
        return False
    if not isinstance(preferred_id, str):
        return False
    return candidate["id"] < preferred_id

def _derived_membership(
    candidates: list[Any], quality_floor: float, preferred: dict[str, Any]
) -> dict[str, list[str]]:
    """The membership lists ``choose_preference`` would derive."""

    rows = _identified_candidates(candidates)
    return {
        "over": _ids_besides(rows, preferred["id"]),
        "feasible": sorted(
            row["id"] for row in _feasible_candidates(rows, quality_floor)
        ),
        "cheaper_but_constraint_violating": _cheaper_rejected_ids(
            rows, preferred
        ),
    }


def _identified_candidates(candidates: list[Any]) -> list[dict[str, Any]]:
    return [
        candidate
        for candidate in candidates
        if isinstance(candidate, dict) and isinstance(candidate.get("id"), str)
    ]


def _ids_besides(rows: list[dict[str, Any]], preferred_id: str) -> list[str]:
    return sorted(row["id"] for row in rows if row["id"] != preferred_id)


def _cheaper_rejected_ids(
    rows: list[dict[str, Any]], preferred: dict[str, Any]
) -> list[str]:
    preferred_id = preferred["id"]
    preferred_cost = float(preferred["cost_value"])
    return sorted(
        row["id"]
        for row in rows
        if _cheaper_rejected_row(row, preferred_id, preferred_cost)
    )

def _cheaper_rejected_row(
    row: dict[str, Any], preferred_id: Any, preferred_cost: float
) -> bool:
    if row["id"] == preferred_id:
        return False
    if not oc.is_number(row.get("cost_value")):
        return False
    return float(row["cost_value"]) < preferred_cost

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
    where: str,
) -> list[str]:
    """``over``, ``feasible`` and the cheaper-but-rejected list are derived.

    ``choose_preference`` computes all three from the measured candidates.
    Left unchecked, a record could ship arbitrary lists — no opponents, a
    fabricated feasible set, or a false account of which constraints rejected
    each policy — while everything else validated clean, and pairwise
    consumers would train on that account.
    """

    preferred = _preferred_candidate(preference, candidates)
    if preferred is None:
        return []
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
    if _cost_value_drifts(preference, preferred):
        errors.append(
            f"{where}.result.preference.cost_value is "
            f"{preference.get('cost_value')!r} but {preferred_id!r} measured "
            f"{preferred.get('cost_value')!r}"
        )
    return errors

def _cost_value_drifts(
    preference: dict[str, Any], preferred: dict[str, Any]
) -> bool:
    """True when the restated cost is missing or differs from the winner's."""

    if not oc.is_number(preference.get("cost_value")):
        return True
    if not oc.is_number(preferred.get("cost_value")):
        return False
    return (
        abs(float(preference["cost_value"]) - float(preferred["cost_value"]))
        > 1e-12
    )

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
    return _check_abstention_reason(
        result, where
    ) + _false_abstention_errors(candidates, quality_floor, where)


def _check_abstention_reason(result: dict[str, Any], where: str) -> list[str]:
    if result.get("abstention_reason") != ABSTAIN_NO_FEASIBLE:
        return [
            f"{where}.result.abstention_reason must be the canonical "
            f"{ABSTAIN_NO_FEASIBLE!r} — it is this family's only abstention"
        ]
    return []


def _false_abstention_errors(
    candidates: list[Any], quality_floor: float, where: str
) -> list[str]:
    feasible = _feasible_candidates(
        [c for c in candidates if isinstance(c, dict)], quality_floor
    )
    if not feasible:
        return []
    return [
        f"{where}.result: FALSE_ABSTENTION — "
        f"{sorted(c['id'] for c in feasible if isinstance(c.get('id'), str))} "
        "satisfy the quality and safety constraints, so the oracle had a "
        "preference to record"
    ]

def _check_abstained_preference(preference: Any, where: str) -> list[str]:
    if preference is not None:
        return [f"{where}.result: an abstained result must not carry a preference"]
    return []


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
        errors += _check_abstained_preference(preference, where)
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
            preference, candidates, quality_floor, where
        )
    return errors
