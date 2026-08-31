#!/usr/bin/env python3
"""Repairs and the per-record decision for the trajectory-pair lane.

The only repairs this lane performs are removals and whitespace collapsing:
hidden reasoning keys are stripped, and a goal that differs only in whitespace
is normalized. Nothing here invents evidence — generated step or outcome text
is never rewritten.
"""

from __future__ import annotations

import copy
from typing import Any

from curate_agentic import (
    REASON_THOUGHT_REMOVED,
    canonical_json,
    prefix_overlap,
    shared_preference_goal,
    strip_hidden_thought_keys,
)
from trajectory_pair_gate import gate_failures
from trajectory_pair_shape import (
    classify_pair_schema,
    pair_envelope_validation_errors,
    side_episode_validation_errors,
)
from trajectory_pair_vocabulary import (
    ACTION_EXCLUDED,
    ACTION_REPAIRED,
    ACTION_RETAINED,
    ACTION_SKIPPED,
    DEFAULT_POLICY,
    GOAL_LOCATIONS,
    REASON_GATE_PASSED,
    REASON_GOAL_WHITESPACE_NORMALIZED,
    REASON_NOT_A_PAIR,
    REASON_RECORD_NOT_OBJECT,
    REASON_SAME_STATE_SCHEMA,
    REASON_SIDES_NOT_OBJECTS,
    GatePolicy,
    TrajectoryDecision,
)

# Schemas whose decision needs no gate evaluation: the record either is not
# this lane's to judge, or is malformed before any contrast question applies.
# Each entry is (action, classification, reason code).
ROUTED_SCHEMAS = {
    "not_an_object": (ACTION_EXCLUDED, "malformed_trajectory_pair", REASON_RECORD_NOT_OBJECT),
    "non_preference_record": (ACTION_SKIPPED, "non_preference_record", REASON_NOT_A_PAIR),
    "sides_not_objects": (ACTION_EXCLUDED, "malformed_trajectory_pair", REASON_SIDES_NOT_OBJECTS),
    # Fable FFPC pairs belong to curate_preferences. Skipping them keeps the
    # two lanes' retain rates on separate denominators.
    "same_state_pair": (ACTION_SKIPPED, "same_state_pair_out_of_scope", REASON_SAME_STATE_SCHEMA),
}


def _goal_owner(record: dict[str, Any], path: tuple[str, ...]) -> dict[str, Any] | None:
    owner: Any = record
    for key in path[:-1]:
        owner = owner.get(key) if isinstance(owner, dict) else None
    return owner if isinstance(owner, dict) else None


def _present_goals(record: dict[str, Any]) -> list[tuple[tuple[str, ...], str]]:
    """Every goal location that currently holds a string, in a fixed order."""

    present: list[tuple[tuple[str, ...], str]] = []
    for path in GOAL_LOCATIONS:
        owner = _goal_owner(record, path)
        value = owner.get(path[-1]) if owner is not None else None
        if isinstance(value, str):
            present.append((path, value))
    return present


def _sole_whitespace_drift(values: list[str]) -> str | None:
    """The one normalized goal, when whitespace is the only difference."""

    normalized = {" ".join(value.split()) for value in values}
    if len(set(values)) == 1 or len(normalized) != 1:
        return None
    return normalized.pop() or None


def normalize_goal_whitespace(record: dict[str, Any]) -> dict[str, Any] | None:
    """Collapse goal whitespace when that is the only goal difference.

    Applied only when at least two goal strings are present, they are not all
    byte-identical, and they are all identical after whitespace normalization.
    The repair rewrites nothing else and invents no goal text.
    """

    present = _present_goals(record)
    if len(present) < 2:
        return None
    canonical_goal = _sole_whitespace_drift([value for _path, value in present])
    if canonical_goal is None:
        return None

    repaired = copy.deepcopy(record)
    for path, _value in present:
        owner = _goal_owner(repaired, path)
        if owner is not None:
            owner[path[-1]] = canonical_goal
    return repaired


def changed_top_level_fields(source: dict[str, Any], curated: dict[str, Any]) -> tuple[str, ...]:
    """Top-level keys whose canonical value a repair changed."""

    return tuple(
        key
        for key in sorted(set(source) | set(curated))
        if canonical_json(source.get(key)) != canonical_json(curated.get(key))
    )


def _routed_decision(schema: str) -> TrajectoryDecision | None:
    routed = ROUTED_SCHEMAS.get(schema)
    if routed is None:
        return None
    action, classification, reason = routed
    return TrajectoryDecision(
        action=action,
        classification=classification,
        reason_codes=(reason,),
        record=None,
    )


def _malformed_decision(record: dict[str, Any], policy: GatePolicy) -> TrajectoryDecision:
    return TrajectoryDecision(
        action=ACTION_EXCLUDED,
        classification="malformed_trajectory_pair",
        reason_codes=gate_failures(record, policy),
        record=None,
        shared_goal=shared_preference_goal(record)[0],
        overlap=prefix_overlap(record.get("chosen"), record.get("rejected")),
        pair_validation_errors=pair_envelope_validation_errors(record) or None,
        side_validation_errors=side_episode_validation_errors(record, policy),
    )


def _apply_repairs(record: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    """Strip hidden reasoning and normalize goal whitespace, in that order."""

    repairs: list[str] = []
    curated, removed_thoughts = strip_hidden_thought_keys(record)
    if removed_thoughts:
        repairs.append(REASON_THOUGHT_REMOVED)

    normalized = normalize_goal_whitespace(curated)
    if normalized is not None:
        curated = normalized
        repairs.append(REASON_GOAL_WHITESPACE_NORMALIZED)
    return curated, repairs


def _gated_decision(
    record: dict[str, Any], policy: GatePolicy = DEFAULT_POLICY
) -> TrajectoryDecision:
    """Repair a well-shaped pair, then keep or exclude it on the gate result."""

    curated, repairs = _apply_repairs(record)
    shared_goal, _reason = shared_preference_goal(curated)
    overlap = prefix_overlap(curated.get("chosen"), curated.get("rejected"))

    failures = gate_failures(curated, policy)
    if failures:
        return TrajectoryDecision(
            action=ACTION_EXCLUDED,
            classification="unsupported_trajectory_pair",
            reason_codes=failures,
            record=None,
            shared_goal=shared_goal,
            overlap=overlap,
            pair_validation_errors=pair_envelope_validation_errors(curated) or None,
            side_validation_errors=side_episode_validation_errors(curated, policy) or None,
        )

    if repairs:
        return TrajectoryDecision(
            action=ACTION_REPAIRED,
            classification="trajectory_pair_repaired",
            reason_codes=(*repairs, REASON_GATE_PASSED),
            record=curated,
            shared_goal=shared_goal,
            overlap=overlap,
            changed_fields=changed_top_level_fields(record, curated),
        )
    return TrajectoryDecision(
        action=ACTION_RETAINED,
        classification="trajectory_pair_gate_passed",
        reason_codes=(REASON_GATE_PASSED,),
        record=curated,
        shared_goal=shared_goal,
        overlap=overlap,
    )


def curate_trajectory_pair(
    record: Any, policy: GatePolicy = DEFAULT_POLICY
) -> TrajectoryDecision:
    """Curate one record without mutating it."""

    schema = classify_pair_schema(record, policy)
    routed = _routed_decision(schema)
    if routed is not None:
        return routed
    if schema == "malformed_trajectory_pair":
        return _malformed_decision(record, policy)
    return _gated_decision(record, policy)
