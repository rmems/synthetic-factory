#!/usr/bin/env python3
"""Trajectory-preference goal repair and per-side episode validation.

Split out of ``compose_trajectory`` by responsibility: run the canonical
episode validator over each preference side, locate every goal a record
carries, and apply PR #93's evidence-preserving whitespace-only goal repair.
"""

from __future__ import annotations

import copy
import sys
from typing import Any, Mapping

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("compose_trajectory_goals")
    from .compose_contract import TRAJECTORY_GOAL_LOCATIONS
    from .validate_run import THALAMIC_CORE_KEYS, check_episode
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "compose_trajectory_goals"
    )
    from compose_contract import TRAJECTORY_GOAL_LOCATIONS
    from validate_run import THALAMIC_CORE_KEYS, check_episode


def _trajectory_side_validation_errors(
    record: Mapping[str, Any],
) -> dict[str, tuple[str, ...]]:
    """Run the canonical episode validator over each trajectory-preference side."""

    found: dict[str, tuple[str, ...]] = {}
    for side_name in ("chosen", "rejected"):
        side = record.get(side_name)
        if not isinstance(side, dict):
            continue
        errors = check_episode(side, side_name, require_goal=False)
        if all(key in side for key in THALAMIC_CORE_KEYS):
            errors.append(f"{side_name}: Thalamic trajectory side is not an episode")
        if errors:
            found[side_name] = tuple(errors)
    return found


def _trajectory_goal_owner(record: dict[str, Any], path: tuple[str, ...]) -> dict[str, Any] | None:
    owner: Any = record
    for key in path[:-1]:
        owner = owner.get(key) if isinstance(owner, dict) else None
    return owner if isinstance(owner, dict) else None


def _present_trajectory_goals(
    record: dict[str, Any],
) -> list[tuple[tuple[str, ...], str]]:
    """Every goal location this record actually carries as a string."""

    present: list[tuple[tuple[str, ...], str]] = []
    for path in TRAJECTORY_GOAL_LOCATIONS:
        owner = _trajectory_goal_owner(record, path)
        if owner is None:
            continue
        value = owner.get(path[-1])
        if isinstance(value, str):
            present.append((path, value))
    return present


def _whitespace_only_goal(present: list[tuple[tuple[str, ...], str]]) -> str | None:
    """The single canonical goal, when the goals differ only in whitespace.

    ``None`` whenever the repair would invent evidence: fewer than two goals
    to reconcile, goals that already agree, goals that still differ once
    whitespace is collapsed, or a goal that collapses to nothing.
    """

    if len(present) < 2:
        return None
    values = [value for _path, value in present]
    normalized = {" ".join(value.split()) for value in values}
    if len(set(values)) == 1 or len(normalized) != 1:
        return None
    return normalized.pop() or None


def _normalize_trajectory_goal_whitespace(
    record: dict[str, Any],
) -> dict[str, Any] | None:
    """Apply PR #93's evidence-preserving goal whitespace repair."""

    present = _present_trajectory_goals(record)
    canonical_goal = _whitespace_only_goal(present)
    if canonical_goal is None:
        return None

    repaired = copy.deepcopy(record)
    for path, _value in present:
        owner = _trajectory_goal_owner(repaired, path)
        if owner is not None:
            owner[path[-1]] = canonical_goal
    return repaired


if __package__:
    _expose_package_sibling(__name__)
