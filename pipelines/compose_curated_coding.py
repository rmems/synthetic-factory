#!/usr/bin/env python3
"""Coding and reward stages for curated record composition."""

from __future__ import annotations

import copy
import sys
from typing import Any, Mapping

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("compose_curated_coding")
    from . import curate_agentic, curate_coding, curate_rewards
    from .compose_contract import (
        ACTION_EXCLUDED,
        ACTION_NOT_APPLICABLE,
        ACTION_RETAINED,
        ComposeDecision,
        REASON_REWARD_ONTOLOGY,
        canonical_sha256,
    )
    from .compose_curated_context import RecordContext, StageDefinition, stage
    from .compose_trajectory import (
        _strip_hidden_only_side,
        is_bridge_record,
        is_episode_record,
        is_preference_record,
    )
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "compose_curated_coding"
    )
    import curate_agentic
    import curate_coding
    import curate_rewards
    from compose_contract import (
        ACTION_EXCLUDED,
        ACTION_NOT_APPLICABLE,
        ACTION_RETAINED,
        ComposeDecision,
        REASON_REWARD_ONTOLOGY,
        canonical_sha256,
    )
    from compose_curated_context import RecordContext, StageDefinition, stage
    from compose_trajectory import (
        _strip_hidden_only_side,
        is_bridge_record,
        is_episode_record,
        is_preference_record,
    )


CODING_STAGE = StageDefinition(
    "coding", curate_coding.TRANSFORM_NAME, curate_coding.TRANSFORM_VERSION
)
REWARDS_STAGE = StageDefinition(
    "rewards",
    curate_rewards.ANNOTATION_FIELD,
    curate_rewards.REWARD_TRANSFORM_VERSION,
)


def _coding_lane_curator(current: dict[str, Any], registered_kind: Any) -> Any:
    """Return the coding owner module for this registered record shape."""

    if registered_kind in {"multi_agent", "safety_case"}:
        return curate_agentic
    if is_bridge_record(current):
        return None
    if is_episode_record(current):
        return curate_coding
    return None


def _append_coding_lane_stage(
    stages: list[dict[str, Any]],
    module: Any,
    curated: Any,
    manifest: Mapping[str, Any],
) -> "ComposeDecision | Any":
    """Append coding evidence and normalize a refusal into ComposeDecision."""

    reasons = list(manifest.get("reason_codes", []))
    definition = StageDefinition(
        "coding", module.TRANSFORM_NAME, module.TRANSFORM_VERSION
    )
    stages.append(
        stage(
            definition,
            ACTION_RETAINED if curated is not None else ACTION_EXCLUDED,
            reason_codes=reasons,
            lane_action=manifest.get("action"),
            detail=manifest,
        )
    )
    if curated is None:
        return ComposeDecision(
            ACTION_EXCLUDED, None, tuple(reasons), tuple(stages), None, None
        )
    return curated


def _bridge_view_trajectory(record: Mapping[str, Any]) -> dict[str, Any] | None:
    """Return an embedded bridge trajectory when its coding lane must run."""

    view = record.get("language_view")
    trajectory = view.get("trajectory") if isinstance(view, Mapping) else None
    if not isinstance(trajectory, dict):
        return None
    has_steps = curate_coding.steps_path(trajectory) is not None
    if has_steps or curate_coding.contains_hidden_reasoning_key(trajectory):
        return trajectory
    return None


def _curate_bridge_trajectory(
    trajectory: dict[str, Any], context: RecordContext
) -> tuple[Any, Any, dict[str, Any]]:
    """Run the correct coding implementation for one embedded trajectory."""

    if curate_coding.steps_path(trajectory) is None:
        curated, detail = _strip_hidden_only_side(trajectory)
        return curate_agentic, curated, detail
    curated, manifest = curate_coding.curate_episode(
        trajectory,
        source_path=f"{context.source.path}#language_view.trajectory",
        source_line=context.source.line,
        source_hash=canonical_sha256(trajectory),
    )
    return curate_coding, curated, copy.deepcopy(manifest)


def _strip_bridge_wrapper(
    updated: dict[str, Any], detail: dict[str, Any]
) -> dict[str, Any]:
    """Strip hidden fields from the bridge wrapper and merge its evidence."""

    if not curate_coding.contains_hidden_reasoning_key(updated):
        return updated
    cleaned, wrapper_detail = _strip_hidden_only_side(updated)
    removed = wrapper_detail["hidden_reasoning_fields_removed"]
    detail["hidden_reasoning_fields_removed"] = (
        detail.get("hidden_reasoning_fields_removed", 0) + removed
    )
    detail["wrapper_hidden_reasoning_fields_removed"] = removed
    detail["reason_codes"] = list(
        dict.fromkeys(
            [
                *detail.get("reason_codes", []),
                *wrapper_detail.get("reason_codes", []),
            ]
        )
    )
    if removed:
        detail["action"] = "modified"
    return cleaned


def _compose_bridge_view_coding(
    current: dict[str, Any],
    trajectory: dict[str, Any],
    stages: list[dict[str, Any]],
    context: RecordContext,
) -> "ComposeDecision | dict[str, Any]":
    """Curate the embedded language-view trajectory through its owning lane."""

    module, curated, detail = _curate_bridge_trajectory(trajectory, context)
    detail["embedded_at"] = "language_view.trajectory"
    if curated is None:
        return _append_coding_lane_stage(stages, module, None, detail)
    updated = copy.deepcopy(current)
    updated["language_view"]["trajectory"] = curated
    updated = _strip_bridge_wrapper(updated, detail)
    return _append_coding_lane_stage(stages, module, updated, detail)


def _hidden_only_curation_applies(
    current: dict[str, Any], registered_kind: Any
) -> bool:
    """Whether a retained non-episode wrapper still carries private fields."""

    governed = (
        registered_kind == "thalamic"
        or is_preference_record(current)
        or is_bridge_record(current)
    )
    return governed and curate_coding.contains_hidden_reasoning_key(current)


def _compose_without_coding_module(
    current: dict[str, Any],
    registered_kind: Any,
    stages: list[dict[str, Any]],
    context: RecordContext,
) -> "ComposeDecision | dict[str, Any]":
    """Handle embedded, hidden-only, and not-applicable coding paths."""

    trajectory = _bridge_view_trajectory(current) if is_bridge_record(current) else None
    if trajectory is not None:
        return _compose_bridge_view_coding(current, trajectory, stages, context)
    if _hidden_only_curation_applies(current, registered_kind):
        cleaned, detail = _strip_hidden_only_side(current)
        return _append_coding_lane_stage(stages, curate_agentic, cleaned, detail)
    stages.append(
        stage(CODING_STAGE, ACTION_NOT_APPLICABLE, lane_action=ACTION_NOT_APPLICABLE)
    )
    return current


def _compose_coding_stage(
    current: dict[str, Any],
    registered_kind: Any,
    stages: list[dict[str, Any]],
    context: RecordContext,
) -> "ComposeDecision | dict[str, Any]":
    """Run the applicable coding lane or record why none applies."""

    module = _coding_lane_curator(current, registered_kind)
    if module is None:
        return _compose_without_coding_module(
            current, registered_kind, stages, context
        )
    curator = (
        curate_agentic.curate_record
        if module is curate_agentic
        else curate_coding.curate_episode
    )
    curated, manifest = curator(
        current,
        source_path=context.source.path,
        source_line=context.source.line,
        source_hash=context.source.sha256,
    )
    return _append_coding_lane_stage(stages, module, curated, manifest)


def reward_refusal(
    stages: list[dict[str, Any]], exc: curate_rewards.RewardOntologyError
) -> ComposeDecision:
    """Record one fail-closed reward ontology refusal."""

    stages.append(
        stage(
            REWARDS_STAGE,
            ACTION_EXCLUDED,
            reason_codes=[REASON_REWARD_ONTOLOGY],
            lane_action=ACTION_EXCLUDED,
            detail={"error": str(exc)},
        )
    )
    return ComposeDecision(
        ACTION_EXCLUDED,
        None,
        (REASON_REWARD_ONTOLOGY,),
        tuple(stages),
        None,
        None,
    )


def retained_rewards(
    annotated: dict[str, Any],
    sidecar: dict[str, Any],
    stages: list[dict[str, Any]],
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Record the ontology annotation and reversible source sidecar."""

    annotation = annotated[curate_rewards.ANNOTATION_FIELD]
    stages.append(
        stage(
            REWARDS_STAGE,
            ACTION_RETAINED,
            reason_codes=annotation["reason_codes"],
            lane_action=annotation["comparability"],
            comparability=annotation["comparability"],
            source_sidecar_id=annotation["source_sidecar_id"],
            source_reward_count=annotation["source_reward_count"],
        )
    )
    return annotated, sidecar


def reward_not_applicable(
    annotated: dict[str, Any], stages: list[dict[str, Any]]
) -> tuple[dict[str, Any], None]:
    """Remove stale annotations from a record with no source rewards."""

    annotated.pop(curate_rewards.ANNOTATION_FIELD, None)
    stages.append(
        stage(
            REWARDS_STAGE,
            ACTION_NOT_APPLICABLE,
            lane_action=ACTION_NOT_APPLICABLE,
            source_reward_count=0,
        )
    )
    return annotated, None


def _compose_rewards_stage(
    current: dict[str, Any],
    stages: list[dict[str, Any]],
    context: RecordContext,
) -> "ComposeDecision | tuple[dict[str, Any], dict[str, Any] | None]":
    """Run the reward ontology last so sidecars bind the final payload."""

    try:
        annotated, sidecar = curate_rewards.curate_record(
            current,
            source_path=context.source.path,
            source_line=context.source.line,
            calibration=context.calibration,
        )
    except curate_rewards.RewardOntologyError as exc:
        return reward_refusal(stages, exc)
    annotation = annotated[curate_rewards.ANNOTATION_FIELD]
    if annotation["source_reward_count"]:
        return retained_rewards(annotated, sidecar, stages)
    return reward_not_applicable(annotated, stages)


if __package__:
    _expose_package_sibling(__name__)
