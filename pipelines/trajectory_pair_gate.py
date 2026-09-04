#!/usr/bin/env python3
"""Contrast rules for the trajectory-pair preference lane.

``trajectory_pair_shape`` decides whether a record *is* a trajectory pair.
This module decides whether a well-formed pair carries the contrast a DPO
consumer can learn from: one shared goal, a shared leading prefix, divergent
outcome and reward, and a preference direction that points one way.

Reasons accumulate in a fixed order so manifests are byte-stable across runs.
"""

from __future__ import annotations

from typing import Any

if __package__:
    from .curate_agentic import canonical_json, prefix_overlap, shared_preference_goal
    from .trajectory_pair_shape import (
        classify_pair_schema,
        pair_envelope_validation_errors,
        side_episode_validation_errors,
        steps_of,
    )
    from .trajectory_pair_vocabulary import (
        BRANCH_LABEL_MASK,
        BRANCH_LABEL_RE,
        DEFAULT_POLICY,
        GOAL_REASONS,
        PAIR_SIDES,
        REASON_BRANCH_LABEL_ONLY,
        REASON_OUTCOME_INVALID,
        REASON_OUTCOME_MISSING,
        REASON_OUTCOME_NOT_DIVERGENT,
        REASON_PAIR_ENVELOPE_INVALID,
        REASON_PAIR_IDENTICAL,
        REASON_PREFERENCE_DIRECTION_INVALID,
        REASON_PREFIX_ABSENT,
        REASON_REWARD_INVALID,
        REASON_REWARD_MISSING,
        REASON_REWARD_NOT_DIVERGENT,
        REASON_SIDE_EPISODE_INVALID,
        REASON_SIDES_NOT_OBJECTS,
        REASON_STEPS_EMPTY,
        REASON_STEPS_INVALID,
        REQUIRED_SIDE_SUCCESS,
        GatePolicy,
        is_finite_json_number,
    )
else:
    from curate_agentic import canonical_json, prefix_overlap, shared_preference_goal
    from trajectory_pair_shape import (
        classify_pair_schema,
        pair_envelope_validation_errors,
        side_episode_validation_errors,
        steps_of,
    )
    from trajectory_pair_vocabulary import (
        BRANCH_LABEL_MASK,
        BRANCH_LABEL_RE,
        DEFAULT_POLICY,
        GOAL_REASONS,
        PAIR_SIDES,
        REASON_BRANCH_LABEL_ONLY,
        REASON_OUTCOME_INVALID,
        REASON_OUTCOME_MISSING,
        REASON_OUTCOME_NOT_DIVERGENT,
        REASON_PAIR_ENVELOPE_INVALID,
        REASON_PAIR_IDENTICAL,
        REASON_PREFERENCE_DIRECTION_INVALID,
        REASON_PREFIX_ABSENT,
        REASON_REWARD_INVALID,
        REASON_REWARD_MISSING,
        REASON_REWARD_NOT_DIVERGENT,
        REASON_SIDE_EPISODE_INVALID,
        REASON_SIDES_NOT_OBJECTS,
        REASON_STEPS_EMPTY,
        REASON_STEPS_INVALID,
        REQUIRED_SIDE_SUCCESS,
        GatePolicy,
        is_finite_json_number,
    )

# Each entry is (field, missing reason, invalid reason, not-divergent reason).
DIVERGENCE_FIELDS = (
    ("outcome", REASON_OUTCOME_MISSING, REASON_OUTCOME_INVALID, REASON_OUTCOME_NOT_DIVERGENT),
    ("reward", REASON_REWARD_MISSING, REASON_REWARD_INVALID, REASON_REWARD_NOT_DIVERGENT),
)


def _mask_branch_labels(value: Any) -> Any:
    if isinstance(value, str):
        return BRANCH_LABEL_RE.sub(BRANCH_LABEL_MASK, value)
    if isinstance(value, dict):
        return {key: _mask_branch_labels(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_mask_branch_labels(item) for item in value]
    return value


def first_step_differs_by_branch_label_only(
    chosen_steps: list[Any], rejected_steps: list[Any]
) -> bool:
    """Whether step 1 matches once the words ``chosen``/``rejected`` are masked."""

    if not chosen_steps or not rejected_steps:
        return False
    left, right = chosen_steps[0], rejected_steps[0]
    if canonical_json(left) == canonical_json(right):
        return False
    return canonical_json(_mask_branch_labels(left)) == canonical_json(_mask_branch_labels(right))


def _field_has_validation_error(
    errors: dict[str, tuple[str, ...]], side_name: str, field_name: str
) -> bool:
    marker = f"{side_name}: {field_name}"
    return any(error.startswith(marker) for error in errors.get(side_name, ()))


def _divergence_failure(
    record: dict[str, Any],
    errors: dict[str, tuple[str, ...]],
    field: tuple[str, str, str, str],
) -> str | None:
    """The reject reason for one divergence field, or ``None`` when it is sound."""

    name, missing, invalid, not_divergent = field
    chosen = record["chosen"].get(name)
    rejected = record["rejected"].get(name)
    if chosen is None or rejected is None:
        return missing
    if any(_field_has_validation_error(errors, side, name) for side in PAIR_SIDES):
        return invalid
    if canonical_json(chosen) == canonical_json(rejected):
        return not_divergent
    return None


def side_field_failures(
    record: dict[str, Any], errors: dict[str, tuple[str, ...]]
) -> list[str]:
    """Reject reasons for missing or non-divergent ``outcome`` / ``reward``."""

    candidates = (_divergence_failure(record, errors, field) for field in DIVERGENCE_FIELDS)
    return [reason for reason in candidates if reason is not None]


def _side_success(record: dict[str, Any], side_name: str) -> Any:
    side = record.get(side_name)
    reward = side.get("reward") if isinstance(side, dict) else None
    return reward.get("success") if isinstance(reward, dict) else None


def _side_labels_misordered(record: dict[str, Any]) -> bool:
    """Whether either arm carries something other than its required exact label."""

    return any(
        _side_success(record, side_name) is not required
        for side_name, required in REQUIRED_SIDE_SUCCESS
    )


def _positive_magnitudes_invalid(pair_reward: dict[str, Any]) -> bool:
    return any(
        not is_finite_json_number(pair_reward[name]) or pair_reward[name] <= 0
        for name in ("preference_margin", "delta")
        if name in pair_reward
    )


def _same_goal_invalid(pair_reward: dict[str, Any]) -> bool:
    if "same_goal" not in pair_reward:
        return False
    value = pair_reward["same_goal"]
    return not is_finite_json_number(value) or value != 1.0


def _pair_evidence_invalid(pair_reward: Any) -> bool:
    """Whether pair-level directional metadata disagrees with the side labels."""

    if not isinstance(pair_reward, dict):
        return False
    if "success" in pair_reward and pair_reward["success"] is not True:
        return True
    return _positive_magnitudes_invalid(pair_reward) or _same_goal_invalid(pair_reward)


def preference_direction_failures(record: dict[str, Any]) -> list[str]:
    """Bind side labels and pair-level directional evidence to one ordering."""

    if _side_labels_misordered(record) or _pair_evidence_invalid(record.get("reward")):
        return [REASON_PREFERENCE_DIRECTION_INVALID]
    return []


def _goal_failures(record: dict[str, Any]) -> list[str]:
    ok, goal_reason = shared_preference_goal(record)
    if ok:
        return []
    # Sides are known objects here, so a goal failure is always a goal code;
    # the side-shape reason is mapped back to this lane's vocabulary anyway.
    return [goal_reason if goal_reason in GOAL_REASONS else REASON_SIDES_NOT_OBJECTS]


def _shape_failures(
    pair_errors: tuple[str, ...], side_errors: dict[str, tuple[str, ...]]
) -> list[str]:
    failures: list[str] = []
    if pair_errors:
        failures.append(REASON_PAIR_ENVELOPE_INVALID)
    if side_errors:
        failures.append(REASON_SIDE_EPISODE_INVALID)
    return failures


def _steps_are_unsafe_to_inspect(side_errors: dict[str, tuple[str, ...]]) -> bool:
    return any(
        error.startswith((f"{side_name}: steps", f"{side_name} step "))
        for side_name, errors in side_errors.items()
        for error in errors
    )


def _step_contrast_failures(
    record: dict[str, Any], chosen_steps: list[Any], rejected_steps: list[Any]
) -> list[str]:
    failures: list[str] = []
    if canonical_json(chosen_steps) == canonical_json(rejected_steps):
        failures.append(REASON_PAIR_IDENTICAL)
    if prefix_overlap(record["chosen"], record["rejected"])["shared_steps"]:
        return failures
    failures.append(REASON_PREFIX_ABSENT)
    if first_step_differs_by_branch_label_only(chosen_steps, rejected_steps):
        failures.append(REASON_BRANCH_LABEL_ONLY)
    return failures


def _steps_failures(
    record: dict[str, Any], side_errors: dict[str, tuple[str, ...]]
) -> list[str]:
    """Step-dependent reasons, skipped when the steps are unsafe to inspect."""

    chosen_steps = steps_of(record.get("chosen"))
    rejected_steps = steps_of(record.get("rejected"))
    if chosen_steps is None or rejected_steps is None:
        return [REASON_STEPS_INVALID]
    if not chosen_steps or not rejected_steps:
        return [REASON_STEPS_EMPTY]
    if _steps_are_unsafe_to_inspect(side_errors):
        return [REASON_STEPS_INVALID]
    return _step_contrast_failures(record, chosen_steps, rejected_steps)


def gate_failures(
    record: dict[str, Any], policy: GatePolicy = DEFAULT_POLICY
) -> tuple[str, ...]:
    """Return every reason a well-shaped trajectory pair fails the gate.

    ``record`` must have object-valued sides. Reasons accumulate in a fixed
    order so manifests are byte-stable across runs. Step-dependent checks are
    skipped when the steps are unsafe to inspect, but independent outcome and
    reward findings are still reported in the same pass.
    """

    side_errors = side_episode_validation_errors(record, policy)
    return (
        *_goal_failures(record),
        *_shape_failures(pair_envelope_validation_errors(record), side_errors),
        *_steps_failures(record, side_errors),
        *side_field_failures(record, side_errors),
        *preference_direction_failures(record),
    )


def pair_passes_gate(record: Any, policy: GatePolicy = DEFAULT_POLICY) -> bool:
    """Whether ``record`` is a trajectory pair that satisfies the gate."""

    return classify_pair_schema(record, policy) == "trajectory_pair" and not gate_failures(
        record, policy
    )
