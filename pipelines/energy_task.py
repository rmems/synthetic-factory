#!/usr/bin/env python3
"""The constrained-allocation task for ``snn-energy-routing-preferences``.

Split out of ``energy_preferences.py`` verbatim: the quadratic objective, the
analytic KKT solver, the unclipped and grid policies, and
:func:`evaluate_allocation` — quality and safety scoring of one allocation.
Every name here is re-exported from ``energy_preferences`` so existing call
sites resolve unchanged.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

_PIPELINES = Path(__file__).resolve().parent
if str(_PIPELINES) not in sys.path:
    sys.path.insert(0, str(_PIPELINES))

from oracle_grounded import distill_contract as oc  # noqa: E402


# --------------------------------------------------------------------------
# Task: constrained actuator allocation
# --------------------------------------------------------------------------


def objective(weights: list[float], allocation: list[float]) -> float:
    """Quadratic effort of an allocation. Lower is better."""

    return sum(w * x * x for w, x in zip(weights, allocation))


def analytic_allocation(
    demand: float, weights: list[float], caps: list[float]
) -> list[float]:
    """Exact KKT solution of the capped quadratic allocation problem.

    Each round spreads the remaining demand proportionally to ``1/w``, pins any
    actuator that would exceed its cap, and repeats. Every pinned actuator was
    over its trial share, and the trial shares sum to the remaining demand, so
    the remainder stays strictly positive until the loop settles — the free set
    empties only when the caps cannot meet the demand at all.
    """

    n = len(weights)
    fixed: dict[int, float] = {}
    free = set(range(n))
    remaining = demand
    while free:
        inverse_sum = sum(1.0 / weights[i] for i in free)
        trial = {i: remaining / (weights[i] * inverse_sum) for i in free}
        violating = [i for i in free if trial[i] > caps[i] + 1e-12]
        if not violating:
            fixed.update(trial)
            break
        for index in violating:
            fixed[index] = caps[index]
            remaining -= caps[index]
            free.discard(index)
    return [fixed.get(i, 0.0) for i in range(n)]


def unclipped_allocation(demand: float, weights: list[float]) -> list[float]:
    """Proportional-to-1/w allocation that ignores the actuator caps.

    Achieves the lowest possible objective precisely because it is allowed to
    break the caps. Fast, high quality, and unsafe.
    """

    inverse_sum = sum(1.0 / w for w in weights)
    return [demand / (w * inverse_sum) for w in weights]


def _grid_allocations(demand: float, n: int, steps: int):
    """Yield every allocation of ``demand`` over ``n`` actuators on a grid."""

    step = demand / steps

    def walk(index: int, left: int, prefix: list[float]):
        if index == n - 1:
            yield prefix + [left * step]
            return
        for take in range(left + 1):
            yield from walk(index + 1, left - take, prefix + [take * step])

    yield from walk(0, steps, [])


def grid_allocation(
    demand: float, weights: list[float], caps: list[float], steps: int
) -> list[float] | None:
    """Exhaustive grid search. Correct up to grid resolution, and slow.

    Returns ``None`` when no point on the grid satisfies the caps. It must not
    return an all-zero allocation in that case: zeros have an objective of
    ``0.0``, *lower* than the true optimum, so any caller comparing objectives
    would rank a policy that solved nothing above one that solved the problem.
    ``None`` says "this policy found nothing", which is the actual outcome.
    """

    best: list[float] | None = None
    best_cost = float("inf")
    for candidate in _grid_allocations(demand, len(weights), steps):
        if any(x > cap + 1e-12 for x, cap in zip(candidate, caps)):
            continue
        cost = objective(weights, candidate)
        if cost < best_cost:
            best_cost = cost
            best = candidate
    return best


@dataclass(frozen=True)
class PolicyEvaluation:
    """Quality and safety of one policy's allocation, both measured."""

    allocation: tuple[float, ...]
    task_quality: float
    safety_ok: bool
    violations: tuple[str, ...]
    success: bool


def evaluate_allocation(
    allocation: list[float] | None,
    *,
    demand: float,
    weights: list[float],
    caps: list[float],
    optimum: float,
    quality_floor: float,
) -> PolicyEvaluation:
    """Score an allocation against the task objective and safety envelope.

    ``allocation is None`` means the policy produced no answer at all, which is
    reported as its own failure rather than folded into a safety violation.
    """

    if allocation is None:
        return PolicyEvaluation(
            allocation=(),
            task_quality=0.0,
            safety_ok=False,
            violations=("NO_FEASIBLE_ALLOCATION_FOUND",),
            success=False,
        )

    violations: list[str] = []
    for index, (value, cap) in enumerate(zip(allocation, caps)):
        if value > cap + 1e-9:
            violations.append(f"ACTUATOR_{index}_OVER_CAP")
        if value < -1e-9:
            violations.append(f"ACTUATOR_{index}_NEGATIVE")
    total = sum(allocation)
    if abs(total - demand) > 1e-6:
        violations.append("DEMAND_NOT_MET")
    achieved = objective(weights, allocation)
    quality = 0.0 if achieved <= 0 else min(1.0, optimum / achieved)
    safety_ok = not violations
    return PolicyEvaluation(
        allocation=tuple(round(value, 9) for value in allocation),
        task_quality=round(quality, 6),
        safety_ok=safety_ok,
        violations=tuple(violations),
        success=bool(safety_ok and quality >= quality_floor),
    )
