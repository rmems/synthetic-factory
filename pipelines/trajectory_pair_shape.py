#!/usr/bin/env python3
"""Shape rules for the trajectory-pair preference lane.

This module answers one question: *is this record a well-formed trajectory
pair, and if not, which lane owns it?* It never judges whether a well-formed
pair carries usable contrast — that is ``trajectory_pair_gate``.
"""

from __future__ import annotations

from typing import Any

from trajectory_pair_vocabulary import (
    DEFAULT_POLICY,
    PAIR_SIDES,
    SAME_STATE_FIELDS,
    GatePolicy,
)
from validate_run import THALAMIC_CORE_KEYS, check_episode


def is_pair_candidate(record: Any) -> bool:
    """Whether ``record`` claims to be a preference pair at all."""

    return isinstance(record, dict) and ("chosen" in record or "rejected" in record)


def is_same_state_pair(record: dict[str, Any]) -> bool:
    """Whether both sides carry the Fable ``state``/``proposed_action`` schema."""

    return all(
        isinstance(side, dict)
        and all(isinstance(side.get(field_name), dict) for field_name in SAME_STATE_FIELDS)
        for side in (record.get(name) for name in PAIR_SIDES)
    )


def steps_of(side: Any) -> list[Any] | None:
    """The side's ``steps`` list, or ``None`` when it is missing or not a list."""

    if not isinstance(side, dict):
        return None
    steps = side.get("steps")
    return steps if isinstance(steps, list) else None


def _non_empty_text_error(record: dict[str, Any], field_name: str) -> str | None:
    value = record.get(field_name)
    if isinstance(value, str) and value.strip():
        return None
    return f"pair: {field_name} must be a non-empty string"


def _object_error(record: dict[str, Any], field_name: str) -> str | None:
    if isinstance(record.get(field_name), dict):
        return None
    return f"pair: {field_name} must be an object"


def _optional_critique_error(record: dict[str, Any]) -> str | None:
    if "critique" not in record:
        return None
    value = record["critique"]
    if isinstance(value, str) and value.strip():
        return None
    return "pair: critique must be a non-empty string when present"


def pair_envelope_validation_errors(record: dict[str, Any]) -> tuple[str, ...]:
    """Return errors for the trajectory-pair fields outside its two arms."""

    candidates = (
        *(_non_empty_text_error(record, name) for name in ("id", "outcome")),
        *(_object_error(record, name) for name in ("reward", "meta")),
        _optional_critique_error(record),
    )
    return tuple(error for error in candidates if error is not None)


def _step_ordinal_error(step: Any, index: int, side_name: str) -> str | None:
    if not isinstance(step, dict):
        return None
    ordinal = step.get("n")
    if type(ordinal) is int and ordinal == index:
        return None
    return f"{side_name} step {index - 1}: n must be the integer {index}"


def step_number_errors(side: dict[str, Any], side_name: str) -> tuple[str, ...]:
    """Require exact, one-based step ordinals without bool-as-int coercion."""

    steps = side.get("steps")
    if not isinstance(steps, list):
        return ()
    candidates = (
        _step_ordinal_error(step, index, side_name)
        for index, step in enumerate(steps, 1)
    )
    return tuple(error for error in candidates if error is not None)


def _one_side_episode_errors(
    side: dict[str, Any], side_name: str, policy: GatePolicy
) -> tuple[str, ...]:
    """Canonical episode-shape errors for one arm, under ``policy``."""

    errors = check_episode(
        side,
        side_name,
        require_goal=False,
        forbid_hidden_thought=True,
        enforce_terminal_outcome=policy.enforce_outcome_agreement,
    )
    errors.extend(step_number_errors(side, side_name))
    if all(key in side for key in THALAMIC_CORE_KEYS):
        errors.append(f"{side_name}: Thalamic trajectory side is not an episode")
    return tuple(errors)


def side_episode_validation_errors(
    record: dict[str, Any], policy: GatePolicy = DEFAULT_POLICY
) -> dict[str, tuple[str, ...]]:
    """Return canonical episode-shape errors for each preference side."""

    found: dict[str, tuple[str, ...]] = {}
    for side_name in PAIR_SIDES:
        side = record.get(side_name)
        if not isinstance(side, dict):
            continue
        errors = _one_side_episode_errors(side, side_name, policy)
        if errors:
            found[side_name] = errors
    return found


def classify_pair_schema(record: Any, policy: GatePolicy = DEFAULT_POLICY) -> str:
    """Route one record to the lane that owns it."""

    if not isinstance(record, dict):
        return "not_an_object"
    if not is_pair_candidate(record):
        return "non_preference_record"
    if not all(isinstance(record.get(side), dict) for side in PAIR_SIDES):
        return "sides_not_objects"
    if is_same_state_pair(record):
        return "same_state_pair"
    if pair_envelope_validation_errors(record) or side_episode_validation_errors(record, policy):
        return "malformed_trajectory_pair"
    return "trajectory_pair"
