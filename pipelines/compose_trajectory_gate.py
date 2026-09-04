#!/usr/bin/env python3
"""Fail-closed compatible core of the PR #93 trajectory-preference gate.

Split out of ``compose_trajectory`` by responsibility: the step, divergence,
and direction checks that decide whether a trajectory pair is retained,
repaired, or excluded when the reviewed sibling gate module is absent.
"""

from __future__ import annotations

import sys
from typing import Any, Mapping

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("compose_trajectory_gate")
    from . import compose_contract as _compose_contract
    from . import curate_agentic
    from .compose_trajectory_goals import (
        normalize_trajectory_goal_whitespace,
        trajectory_side_validation_errors,
    )
    from .trajectory_pair_gate import preference_direction_failures
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "compose_trajectory_gate"
    )
    import compose_contract as _compose_contract
    import curate_agentic
    from compose_trajectory_goals import (
        normalize_trajectory_goal_whitespace,
        trajectory_side_validation_errors,
    )
    from trajectory_pair_gate import preference_direction_failures

ACTION_EXCLUDED = _compose_contract.ACTION_EXCLUDED
ACTION_RETAINED = _compose_contract.ACTION_RETAINED
REASON_TRAJECTORY_GATE_PASSED = _compose_contract.REASON_TRAJECTORY_GATE_PASSED
REASON_TRAJECTORY_GOAL_NORMALIZED = _compose_contract.REASON_TRAJECTORY_GOAL_NORMALIZED
REASON_TRAJECTORY_IDENTICAL = _compose_contract.REASON_TRAJECTORY_IDENTICAL
REASON_TRAJECTORY_OUTCOME_MISSING = _compose_contract.REASON_TRAJECTORY_OUTCOME_MISSING
REASON_TRAJECTORY_OUTCOME_NOT_DIVERGENT = _compose_contract.REASON_TRAJECTORY_OUTCOME_NOT_DIVERGENT
REASON_TRAJECTORY_PREFIX_ABSENT = _compose_contract.REASON_TRAJECTORY_PREFIX_ABSENT
REASON_TRAJECTORY_REWARD_MISSING = _compose_contract.REASON_TRAJECTORY_REWARD_MISSING
REASON_TRAJECTORY_REWARD_NOT_DIVERGENT = _compose_contract.REASON_TRAJECTORY_REWARD_NOT_DIVERGENT
REASON_TRAJECTORY_SIDE_INVALID = _compose_contract.REASON_TRAJECTORY_SIDE_INVALID
REASON_TRAJECTORY_STEPS_EMPTY = _compose_contract.REASON_TRAJECTORY_STEPS_EMPTY
REASON_TRAJECTORY_STEPS_INVALID = _compose_contract.REASON_TRAJECTORY_STEPS_INVALID
_TrajectoryPreferenceDecision = _compose_contract.TrajectoryPreferenceDecision
canonical_json = _compose_contract.canonical_json

TRAJECTORY_DIVERGENCE_FIELDS = (
    (
        "outcome",
        REASON_TRAJECTORY_OUTCOME_MISSING,
        REASON_TRAJECTORY_OUTCOME_NOT_DIVERGENT,
    ),
    (
        "reward",
        REASON_TRAJECTORY_REWARD_MISSING,
        REASON_TRAJECTORY_REWARD_NOT_DIVERGENT,
    ),
)


def trajectory_steps(side: Any) -> Any:
    """Return one side's steps without treating non-objects as mappings."""

    return side.get("steps") if isinstance(side, dict) else None


def trajectory_step_shape_reason(chosen_steps: Any, rejected_steps: Any) -> str | None:
    """Return the first structural step-array failure in gate order."""

    if not isinstance(chosen_steps, list) or not isinstance(rejected_steps, list):
        return REASON_TRAJECTORY_STEPS_INVALID
    if not chosen_steps or not rejected_steps:
        return REASON_TRAJECTORY_STEPS_EMPTY
    return None


def trajectory_step_reasons(chosen: Any, rejected: Any, overlap: Mapping[str, Any]) -> list[str]:
    """Why the pair's step arrays fail PR #93's gate, in gate order."""

    chosen_steps = trajectory_steps(chosen)
    rejected_steps = trajectory_steps(rejected)
    shape_reason = trajectory_step_shape_reason(chosen_steps, rejected_steps)
    if shape_reason is not None:
        return [shape_reason]

    reasons: list[str] = []
    if canonical_json(chosen_steps) == canonical_json(rejected_steps):
        reasons.append(REASON_TRAJECTORY_IDENTICAL)
    if not overlap["shared_steps"]:
        reasons.append(REASON_TRAJECTORY_PREFIX_ABSENT)
    return reasons


def trajectory_divergence_reasons(chosen: Any, rejected: Any) -> list[str]:
    """Why the pair's outcome and reward evidence fails to diverge."""

    if not isinstance(chosen, dict) or not isinstance(rejected, dict):
        return []

    reasons: list[str] = []
    for field_name, missing_reason, same_reason in TRAJECTORY_DIVERGENCE_FIELDS:
        if chosen.get(field_name) is None or rejected.get(field_name) is None:
            reasons.append(missing_reason)
        elif canonical_json(chosen[field_name]) == canonical_json(rejected[field_name]):
            reasons.append(same_reason)
    return reasons


def trajectory_gate_passed(
    curated: dict[str, Any],
    overlap: Mapping[str, Any],
    *,
    removed_thoughts: Any,
    normalized: Any,
) -> _TrajectoryPreferenceDecision:
    """The accepted decision, repaired if the gate had to touch the record."""

    repaired = bool(removed_thoughts) or normalized is not None
    reasons: list[str] = []
    if removed_thoughts:
        reasons.append(curate_agentic.REASON_THOUGHT_REMOVED)
    if normalized is not None:
        reasons.append(REASON_TRAJECTORY_GOAL_NORMALIZED)
    reasons.append(REASON_TRAJECTORY_GATE_PASSED)
    return _TrajectoryPreferenceDecision(
        action="repaired" if repaired else ACTION_RETAINED,
        classification=("trajectory_pair_repaired" if repaired else "trajectory_pair_gate_passed"),
        reason_codes=tuple(reasons),
        record=curated,
        shared_goal=True,
        overlap=overlap,
    )


def compat_trajectory_preference(
    record: dict[str, Any],
) -> _TrajectoryPreferenceDecision:
    """Enforce PR #93's non-repairing core when its sibling module is absent.

    The sibling owns richer reject diagnostics. This compatibility path keeps
    its acceptance contract and evidence-preserving repairs: valid episode
    sides, one goal, a non-empty shared step prefix, non-identical trajectories,
    divergent outcome and reward evidence, hidden-thought removal, and
    whitespace-only goal normalization.
    """

    curated, removed_thoughts = curate_agentic.strip_hidden_thought_keys(record)
    normalized = normalize_trajectory_goal_whitespace(curated)
    if normalized is not None:
        curated = normalized

    shared_goal, goal_reason = curate_agentic.shared_preference_goal(curated)
    side_errors = trajectory_side_validation_errors(curated)
    chosen = curated.get("chosen")
    rejected = curated.get("rejected")
    overlap = curate_agentic.prefix_overlap(chosen, rejected)

    # Collected in gate order: the reason codes are public evidence, so the
    # sequence a reader sees has to stay stable.
    reasons: list[str] = []
    if not shared_goal and goal_reason is not None:
        reasons.append(goal_reason)
    if side_errors:
        reasons.append(REASON_TRAJECTORY_SIDE_INVALID)
    reasons.extend(trajectory_step_reasons(chosen, rejected, overlap))
    reasons.extend(trajectory_divergence_reasons(chosen, rejected))
    reasons.extend(preference_direction_failures(curated))

    if reasons:
        return _TrajectoryPreferenceDecision(
            action=ACTION_EXCLUDED,
            classification="unsupported_trajectory_pair",
            reason_codes=tuple(dict.fromkeys(reasons)),
            record=None,
            shared_goal=shared_goal,
            overlap=overlap,
            side_validation_errors=side_errors or None,
        )
    return trajectory_gate_passed(
        curated,
        overlap,
        removed_thoughts=removed_thoughts,
        normalized=normalized,
    )


if __package__:
    _expose_package_sibling(__name__)
