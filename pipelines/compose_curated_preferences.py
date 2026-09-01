#!/usr/bin/env python3
"""Preference-stage orchestration for curated record composition."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

_PIPELINES = Path(__file__).resolve().parent
if str(_PIPELINES) not in sys.path:
    sys.path.insert(0, str(_PIPELINES))

import curate_preferences  # noqa: E402
from compose_contract import (  # noqa: E402
    ACTION_EXCLUDED,
    ACTION_NOT_APPLICABLE,
    ACTION_RETAINED,
    COMPOSE_NAME,
    COMPOSE_VERSION,
    ComposeDecision,
    REASON_MIXED_PREFERENCE_FAMILIES,
    REASON_TRAJECTORY_SIDE_INVALID,
)
from compose_curated_context import (  # noqa: E402
    RecordContext,
    StageDefinition,
    stage,
)
from compose_trajectory import (  # noqa: E402
    _compat_trajectory_preference,
    _curate_trajectory_sides,
    _is_same_state_pair,
    _mixed_preference_families,
    is_preference_record,
)
from record_kind import preference_side_kinds  # noqa: E402


PREFERENCES_STAGE = StageDefinition(
    "preferences",
    curate_preferences.TRANSFORM_NAME,
    curate_preferences.TRANSFORM_VERSION,
)
COMPOSE_PREFERENCES_STAGE = StageDefinition(
    "preferences", COMPOSE_NAME, COMPOSE_VERSION
)


@dataclass(frozen=True)
class SideCuration:
    """One trajectory pair's side-level curation evidence."""

    record: dict[str, Any] | None
    manifests: dict[str, dict[str, Any]]
    reasons: tuple[str, ...]
    changed: bool


@dataclass(frozen=True)
class SideFailure:
    """Classification metadata for a failed side-correction branch."""

    kinds: tuple[str, str]
    classification: str
    schema: str | None = None


def _trajectory_preference(record: dict[str, Any], reviewed_module: Any):
    """Dispatch to the reviewed trajectory gate when the sibling exists."""

    if reviewed_module is None:
        return (
            _compat_trajectory_preference(record),
            "trajectory-pair-preference-curation",
            "1.1.0-compatible-core",
            "compatible_core",
        )
    return (
        reviewed_module.curate_trajectory_pair(record),
        reviewed_module.TRANSFORM_NAME,
        reviewed_module.TRANSFORM_VERSION,
        "reviewed_module",
    )


def _curate_sides(record: dict[str, Any], context: RecordContext) -> SideCuration:
    """Normalize the trajectory helper's tuple into named immutable evidence."""

    curated, manifests, reasons, changed = _curate_trajectory_sides(
        record,
        source_path=context.source.path,
        source_line=context.source.line,
    )
    return SideCuration(curated, manifests, tuple(reasons), changed)


def _side_curation_failed_decision(
    stages: list[dict[str, Any]],
    curation: SideCuration,
    failure: SideFailure,
) -> ComposeDecision:
    """Exclude a pair whose sides cannot be repaired by their coding lane."""

    reasons = list(
        dict.fromkeys([REASON_TRAJECTORY_SIDE_INVALID, *curation.reasons])
    )
    evidence: dict[str, Any] = {
        "reason_codes": reasons,
        "lane_action": ACTION_EXCLUDED,
        "classification": failure.classification,
        "side_kinds": list(failure.kinds),
        "side_curation": curation.manifests,
        "side_curation_changed": curation.changed,
    }
    if failure.schema is not None:
        evidence["schema"] = failure.schema
    stages.append(stage(COMPOSE_PREFERENCES_STAGE, ACTION_EXCLUDED, **evidence))
    return ComposeDecision(
        ACTION_EXCLUDED, None, tuple(reasons), tuple(stages), None, None
    )


def _retained_preference_stage(
    stages: list[dict[str, Any]],
    definition: StageDefinition,
    evidence: dict[str, Any],
) -> None:
    """Append a preference stage using its already-decided retention state."""

    stages.append(stage(definition, evidence.pop("action"), **evidence))


def _compose_same_state_preference(
    current: dict[str, Any],
    stages: list[dict[str, Any]],
    context: RecordContext,
) -> "ComposeDecision | tuple[Any, list[str]]":
    """Curate a same-state Thalamic trajectory pair."""

    kinds = preference_side_kinds(current)
    curation = _curate_sides(current, context)
    if curation.record is None:
        return _side_curation_failed_decision(
            stages,
            curation,
            SideFailure(kinds, "same_state_side_curation_failed", "same_state_pair"),
        )
    decision = curate_preferences.curate_preference_record(curation.record)
    retained = decision.record is not None
    reasons = list(decision.reason_codes)
    if retained:
        reasons = list(dict.fromkeys([*curation.reasons, *reasons]))
    _retained_preference_stage(
        stages,
        PREFERENCES_STAGE,
        {
            "action": ACTION_RETAINED if retained else ACTION_EXCLUDED,
            "reason_codes": reasons,
            "lane_action": "repaired" if retained and curation.changed else decision.action,
            "classification": decision.classification,
            "side_kinds": list(kinds),
            "schema": "same_state_pair",
            "context_diff_paths": list(decision.context_diff_paths),
            "side_curation": curation.manifests,
            "side_curation_changed": curation.changed,
        },
    )
    return decision, reasons


def _compose_mixed_family_preference_exclusion(
    kinds: tuple[str, str], stages: list[dict[str, Any]]
) -> ComposeDecision:
    """Refuse a pair whose sides belong to different record families."""

    reasons = [REASON_MIXED_PREFERENCE_FAMILIES]
    stages.append(
        stage(
            COMPOSE_PREFERENCES_STAGE,
            ACTION_EXCLUDED,
            reason_codes=reasons,
            lane_action=ACTION_EXCLUDED,
            classification="mixed_preference_side_families",
            side_kinds=list(kinds),
        )
    )
    return ComposeDecision(
        ACTION_EXCLUDED, None, tuple(reasons), tuple(stages), None, None
    )


def _compose_episode_preference(
    current: dict[str, Any],
    stages: list[dict[str, Any]],
    context: RecordContext,
) -> "ComposeDecision | tuple[Any, list[str]]":
    """Curate an episode/episode coding trajectory pair."""

    kinds = preference_side_kinds(current)
    curation = _curate_sides(current, context)
    if curation.record is None:
        return _side_curation_failed_decision(
            stages,
            curation,
            SideFailure(kinds, "trajectory_side_curation_failed"),
        )
    decision, name, version, implementation = _trajectory_preference(
        curation.record, context.trajectory_preferences
    )
    reasons = list(dict.fromkeys([*curation.reasons, *decision.reason_codes]))
    retained = decision.record is not None
    definition = StageDefinition("preferences", name, version)
    _retained_preference_stage(
        stages,
        definition,
        {
            "action": ACTION_RETAINED if retained else ACTION_EXCLUDED,
            "reason_codes": reasons,
            "lane_action": "repaired" if retained and curation.changed else decision.action,
            "classification": decision.classification,
            "side_kinds": list(kinds),
            "implementation": implementation,
            "shared_goal": decision.shared_goal,
            "overlap": decision.overlap,
            "side_validation_errors": decision.side_validation_errors or {},
            "side_curation": curation.manifests,
            "side_curation_changed": curation.changed,
        },
    )
    return decision, reasons


def _compose_legacy_preference(
    current: dict[str, Any],
    stages: list[dict[str, Any]],
) -> tuple[Any, list[str]]:
    """Curate a legacy pre-episode Thalamic-shaped pair."""

    kinds = preference_side_kinds(current)
    decision = curate_preferences.curate_preference_record(current)
    reasons = list(decision.reason_codes)
    retained = decision.record is not None
    stages.append(
        stage(
            PREFERENCES_STAGE,
            ACTION_RETAINED if retained else ACTION_EXCLUDED,
            reason_codes=reasons,
            lane_action=decision.action,
            classification=decision.classification,
            side_kinds=list(kinds),
            context_diff_paths=list(decision.context_diff_paths),
        )
    )
    return decision, reasons


def _preference_branch(
    current: dict[str, Any],
    stages: list[dict[str, Any]],
    context: RecordContext,
):
    """Choose the branch matching a preference pair's two side families."""

    kinds = preference_side_kinds(current)
    if _is_same_state_pair(current):
        return _compose_same_state_preference(current, stages, context)
    if _mixed_preference_families(kinds):
        return _compose_mixed_family_preference_exclusion(kinds, stages)
    if kinds == ("episode", "episode"):
        return _compose_episode_preference(current, stages, context)
    return _compose_legacy_preference(current, stages)


def _compose_preferences_stage(
    current: dict[str, Any],
    stages: list[dict[str, Any]],
    context: RecordContext,
) -> "ComposeDecision | dict[str, Any]":
    """Run the preference branch and normalize its retained/excluded outcome."""

    if not is_preference_record(current):
        stages.append(
            stage(
                PREFERENCES_STAGE,
                ACTION_NOT_APPLICABLE,
                lane_action=ACTION_NOT_APPLICABLE,
            )
        )
        return current
    outcome = _preference_branch(current, stages, context)
    if isinstance(outcome, ComposeDecision):
        return outcome
    decision, reasons = outcome
    if decision.record is None:
        return ComposeDecision(
            ACTION_EXCLUDED, None, tuple(reasons), tuple(stages), None, None
        )
    return decision.record
