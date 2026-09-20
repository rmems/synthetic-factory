#!/usr/bin/env python3
"""Allocation-domain helpers for ``snn-energy-routing-preferences``.

Split out of ``energy_check.py`` verbatim: per-candidate allocation shape
and cap checks, the safety derivation, and positive-weight validation —
shared by the scenario and candidate checks.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

_PIPELINES = Path(__file__).resolve().parent
if str(_PIPELINES) not in sys.path:
    sys.path.insert(0, str(_PIPELINES))

from oracle_grounded import distill_contract as oc  # noqa: E402


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


def _positive_weights(weights: Any) -> bool:
    """A non-empty list of strictly positive numeric weights."""

    if not isinstance(weights, list) or not weights:
        return False
    return all(oc.is_number(w) and float(w) > 0.0 for w in weights)
