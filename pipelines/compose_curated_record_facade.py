#!/usr/bin/env python3
"""Live compatibility adapters for curated record and source-line composition."""

from __future__ import annotations

import sys
from types import ModuleType
from typing import TYPE_CHECKING, Any, Mapping, MutableMapping

if TYPE_CHECKING:
    from compose_curated_context import RecordContext
    from compose_curated_record import RecordServices

if __package__:
    from . import _expose_package_sibling, _local_sibling_module, _require_local_sibling

    if _local_sibling_module("compose_curated_record_facade", allow_initializing=True):
        import compose_curated_record_facade as _direct_record_facade

        _require_local_sibling(_direct_record_facade, "compose_curated_record_facade")
        del _direct_record_facade
    from .compose_contract import (
        ACTION_EXCLUDED,
        ComposeDecision,
    )
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "compose_curated_record_facade"
    )
    from compose_contract import (
        ACTION_EXCLUDED,
        ComposeDecision,
    )


_FACADE: ModuleType | None = None


def bind_facade(facade: ModuleType) -> None:
    global _FACADE
    _FACADE = facade


def _facade() -> ModuleType:
    global _FACADE
    resolver = getattr(sys.modules.get("pipelines"), "_canonical_sibling_binding", None)
    if resolver is not None:
        _FACADE = resolver("compose_curated", _FACADE)
    if _FACADE is None:
        raise RuntimeError("compose_curated facade is not bound")
    return _FACADE


def _facade_delegate(callable_: Any, *args: Any, **kwargs: Any):
    return callable_(*args, **kwargs)


def _trajectory_preference(record: dict[str, Any]) -> tuple[Any, str, str, str]:
    facade = _facade()
    reviewed = facade.curate_trajectory_preferences
    if reviewed is not None:
        return (
            reviewed.curate_trajectory_pair(record),
            reviewed.TRANSFORM_NAME,
            reviewed.TRANSFORM_VERSION,
            "reviewed_module",
        )
    return (
        facade._compat_trajectory_preference(record),
        "trajectory-pair-preference-curation",
        "1.1.0-compatible-core",
        "compatible_core",
    )


def _stage(
    lane: str,
    name: str,
    version: str,
    action: str,
    **extra: Any,
) -> dict[str, Any]:
    facade = _facade()
    return facade._facade_delegate(
        facade.stage, facade.StageDefinition(lane, name, version), action, **extra
    )


def _coding_steps_repaired_copy(
    record: Mapping[str, Any],
    *,
    source_path: str,
    source_line: int,
    source_sha256: str,
) -> dict[str, Any] | None:
    facade = _facade()
    curated: Any = facade._PROBE_FAILED
    with facade.contextlib.suppress(Exception):
        curated, _manifest = facade.curate_coding.curate_episode(
            facade.copy.deepcopy(dict(record)),
            source_path=source_path,
            source_line=source_line,
            source_hash=source_sha256,
        )
    if curated is facade._PROBE_FAILED:
        return None
    return curated if isinstance(curated, dict) else None


def _side_curation_failed_decision(
    stages: list[dict[str, Any]],
    side_curation: dict[str, dict[str, Any]],
    side_curation_reasons: list[str],
    side_curation_changed: bool,
    *,
    side_kinds: tuple[str, str],
    classification: str,
    **stage_extra: Any,
) -> ComposeDecision:
    facade = _facade()
    reasons = list(dict.fromkeys([facade.REASON_TRAJECTORY_SIDE_INVALID, *side_curation_reasons]))
    stages.append(
        facade._stage(
            "preferences",
            facade.COMPOSE_NAME,
            facade.COMPOSE_VERSION,
            facade.ACTION_EXCLUDED,
            reason_codes=reasons,
            lane_action=facade.ACTION_EXCLUDED,
            classification=classification,
            side_kinds=list(side_kinds),
            **stage_extra,
            side_curation=side_curation,
            side_curation_changed=side_curation_changed,
        )
    )
    return ComposeDecision(ACTION_EXCLUDED, None, tuple(reasons), tuple(stages), None, None)


def _compose_same_state_preference(
    current: dict[str, Any],
    side_kinds: tuple[str, str],
    stages: list[dict[str, Any]],
    *,
    source_path: str,
    source_line: int,
) -> "ComposeDecision | tuple[Any, list[str]]":
    facade = _facade()
    curated, evidence, reasons, changed = facade._curate_trajectory_sides(
        current, source_path=source_path, source_line=source_line
    )
    if curated is None:
        return facade._side_curation_failed_decision(
            stages,
            evidence,
            reasons,
            changed,
            side_kinds=side_kinds,
            classification="same_state_side_curation_failed",
            schema="same_state_pair",
        )
    decision = facade.curate_preferences.curate_preference_record(curated)
    preference_reasons = list(decision.reason_codes)
    if decision.record is not None:
        preference_reasons = list(dict.fromkeys([*reasons, *preference_reasons]))
    stages.append(
        facade._stage(
            "preferences",
            facade.curate_preferences.TRANSFORM_NAME,
            facade.curate_preferences.TRANSFORM_VERSION,
            facade.ACTION_RETAINED if decision.record is not None else facade.ACTION_EXCLUDED,
            reason_codes=preference_reasons,
            lane_action="repaired" if decision.record is not None and changed else decision.action,
            classification=decision.classification,
            side_kinds=list(side_kinds),
            schema="same_state_pair",
            context_diff_paths=list(decision.context_diff_paths),
            side_curation=evidence,
            side_curation_changed=changed,
        )
    )
    return decision, preference_reasons


def _compose_mixed_family_preference_exclusion(
    side_kinds: tuple[str, str], stages: list[dict[str, Any]]
) -> ComposeDecision:
    facade = _facade()
    reasons = [facade.REASON_MIXED_PREFERENCE_FAMILIES]
    stages.append(
        facade._stage(
            "preferences",
            facade.COMPOSE_NAME,
            facade.COMPOSE_VERSION,
            facade.ACTION_EXCLUDED,
            reason_codes=reasons,
            lane_action=facade.ACTION_EXCLUDED,
            classification="mixed_preference_side_families",
            side_kinds=list(side_kinds),
        )
    )
    return ComposeDecision(ACTION_EXCLUDED, None, tuple(reasons), tuple(stages), None, None)


def _compose_episode_preference(
    current: dict[str, Any],
    side_kinds: tuple[str, str],
    stages: list[dict[str, Any]],
    *,
    source_path: str,
    source_line: int,
) -> "ComposeDecision | tuple[Any, list[str]]":
    facade = _facade()
    curated, evidence, reasons, changed = facade._curate_trajectory_sides(
        current, source_path=source_path, source_line=source_line
    )
    if curated is None:
        return facade._side_curation_failed_decision(
            stages,
            evidence,
            reasons,
            changed,
            side_kinds=side_kinds,
            classification="trajectory_side_curation_failed",
        )
    decision, name, version, implementation = facade._trajectory_preference(curated)
    preference_reasons = list(dict.fromkeys([*reasons, *decision.reason_codes]))
    retained = decision.record is not None
    stages.append(
        facade._stage(
            "preferences",
            name,
            version,
            facade.ACTION_RETAINED if retained else facade.ACTION_EXCLUDED,
            reason_codes=preference_reasons,
            lane_action="repaired" if retained and changed else decision.action,
            classification=decision.classification,
            side_kinds=list(side_kinds),
            implementation=implementation,
            shared_goal=decision.shared_goal,
            overlap=decision.overlap,
            side_validation_errors=decision.side_validation_errors or {},
            side_curation=evidence,
            side_curation_changed=changed,
        )
    )
    return decision, preference_reasons


def _compose_legacy_preference(
    current: dict[str, Any],
    side_kinds: tuple[str, str],
    stages: list[dict[str, Any]],
) -> tuple[Any, list[str]]:
    facade = _facade()
    decision = facade.curate_preferences.curate_preference_record(current)
    reasons = list(decision.reason_codes)
    stages.append(
        facade._stage(
            "preferences",
            facade.curate_preferences.TRANSFORM_NAME,
            facade.curate_preferences.TRANSFORM_VERSION,
            facade.ACTION_RETAINED if decision.record is not None else facade.ACTION_EXCLUDED,
            reason_codes=reasons,
            lane_action=decision.action,
            classification=decision.classification,
            side_kinds=list(side_kinds),
            context_diff_paths=list(decision.context_diff_paths),
        )
    )
    return decision, reasons


def _compose_preferences_stage(
    current: dict[str, Any],
    stages: list[dict[str, Any]],
    *,
    source_path: str,
    source_line: int,
) -> "ComposeDecision | dict[str, Any]":
    facade = _facade()
    if not facade.is_preference_record(current):
        stages.append(
            facade._stage(
                "preferences",
                facade.curate_preferences.TRANSFORM_NAME,
                facade.curate_preferences.TRANSFORM_VERSION,
                facade.ACTION_NOT_APPLICABLE,
                lane_action=facade.ACTION_NOT_APPLICABLE,
            )
        )
        return current
    side_kinds = facade.preference_side_kinds(current)
    if facade._is_same_state_pair(current):
        outcome = facade._compose_same_state_preference(
            current, side_kinds, stages, source_path=source_path, source_line=source_line
        )
    elif facade._mixed_preference_families(side_kinds):
        return facade._compose_mixed_family_preference_exclusion(side_kinds, stages)
    elif side_kinds == ("episode", "episode"):
        outcome = facade._compose_episode_preference(
            current, side_kinds, stages, source_path=source_path, source_line=source_line
        )
    else:
        outcome = facade._compose_legacy_preference(current, side_kinds, stages)
    if isinstance(outcome, ComposeDecision):
        return outcome
    decision, reasons = outcome
    if decision.record is None:
        return ComposeDecision(ACTION_EXCLUDED, None, tuple(reasons), tuple(stages), None, None)
    return decision.record


def _coding_lane_curator(current: dict[str, Any], registered_kind: Any) -> Any:
    facade = _facade()
    if registered_kind in {"multi_agent", "safety_case"}:
        return facade.curate_agentic
    if facade.is_bridge_record(current):
        return None
    if facade.is_episode_record(current):
        return facade.curate_coding
    return None


def _append_coding_lane_stage(
    stages: list[dict[str, Any]], module: Any, curated: Any, manifest: Mapping[str, Any]
) -> "ComposeDecision | Any":
    facade = _facade()
    reasons = list(manifest.get("reason_codes", []))
    stages.append(
        facade._stage(
            "coding",
            module.TRANSFORM_NAME,
            module.TRANSFORM_VERSION,
            facade.ACTION_RETAINED if curated is not None else facade.ACTION_EXCLUDED,
            reason_codes=reasons,
            lane_action=manifest.get("action"),
            detail=manifest,
        )
    )
    if curated is None:
        return ComposeDecision(ACTION_EXCLUDED, None, tuple(reasons), tuple(stages), None, None)
    return curated


def _bridge_view_trajectory(record: Mapping[str, Any]) -> dict[str, Any] | None:
    facade = _facade()
    view = record.get("language_view")
    trajectory = view.get("trajectory") if isinstance(view, Mapping) else None
    if not isinstance(trajectory, dict):
        return None
    if facade.curate_coding.steps_path(trajectory) is not None:
        return trajectory
    if facade.curate_coding.contains_hidden_reasoning_key(trajectory):
        return trajectory
    return None


def _compose_bridge_view_coding(
    current: dict[str, Any],
    trajectory: dict[str, Any],
    stages: list[dict[str, Any]],
    *,
    source_path: str,
    source_line: int,
) -> "ComposeDecision | dict[str, Any]":
    facade = _facade()
    if facade.curate_coding.steps_path(trajectory) is not None:
        module = facade.curate_coding
        curated, detail = module.curate_episode(
            trajectory,
            source_path=f"{source_path}#language_view.trajectory",
            source_line=source_line,
            source_hash=facade._canonical_sha256(trajectory),
        )
        detail = facade.copy.deepcopy(detail)
    else:
        module = facade.curate_agentic
        curated, detail = facade._strip_hidden_only_side(trajectory)
    detail["embedded_at"] = "language_view.trajectory"
    if curated is None:
        return facade._append_coding_lane_stage(stages, module, None, detail)
    updated = facade.copy.deepcopy(current)
    updated["language_view"]["trajectory"] = curated
    if facade.curate_coding.contains_hidden_reasoning_key(updated):
        updated, wrapper = facade._strip_hidden_only_side(updated)
        removed = wrapper["hidden_reasoning_fields_removed"]
        detail["hidden_reasoning_fields_removed"] = (
            detail.get("hidden_reasoning_fields_removed", 0) + removed
        )
        detail["wrapper_hidden_reasoning_fields_removed"] = removed
        detail["reason_codes"] = list(
            dict.fromkeys([*detail.get("reason_codes", []), *wrapper.get("reason_codes", [])])
        )
        if removed:
            detail["action"] = "modified"
    return facade._append_coding_lane_stage(stages, module, updated, detail)


def _hidden_only_curation_applies(current: dict[str, Any], registered_kind: Any) -> bool:
    facade = _facade()
    governed = (
        registered_kind == "thalamic"
        or facade.is_preference_record(current)
        or facade.is_bridge_record(current)
    )
    return governed and facade.curate_coding.contains_hidden_reasoning_key(current)


def _compose_coding_stage(
    current: dict[str, Any],
    registered_kind: Any,
    stages: list[dict[str, Any]],
    *,
    source_path: str,
    source_line: int,
    source_sha256: str,
) -> "ComposeDecision | dict[str, Any]":
    facade = _facade()
    module = facade._coding_lane_curator(current, registered_kind)
    if module is None:
        trajectory = (
            facade._bridge_view_trajectory(current) if facade.is_bridge_record(current) else None
        )
        if trajectory is not None:
            return facade._compose_bridge_view_coding(
                current, trajectory, stages, source_path=source_path, source_line=source_line
            )
        if facade._hidden_only_curation_applies(current, registered_kind):
            cleaned, detail = facade._strip_hidden_only_side(current)
            return facade._append_coding_lane_stage(stages, facade.curate_agentic, cleaned, detail)
        stages.append(
            facade._stage(
                "coding",
                facade.curate_coding.TRANSFORM_NAME,
                facade.curate_coding.TRANSFORM_VERSION,
                facade.ACTION_NOT_APPLICABLE,
                lane_action=facade.ACTION_NOT_APPLICABLE,
            )
        )
        return current
    curator = (
        facade.curate_agentic.curate_record
        if module is facade.curate_agentic
        else facade.curate_coding.curate_episode
    )
    curated, manifest = curator(
        current, source_path=source_path, source_line=source_line, source_hash=source_sha256
    )
    return facade._append_coding_lane_stage(stages, module, curated, manifest)


def _compose_rewards_stage(
    current: dict[str, Any],
    stages: list[dict[str, Any]],
    *,
    source_path: str,
    source_line: int,
    calibration: Any,
) -> "ComposeDecision | tuple[dict[str, Any], dict[str, Any] | None]":
    facade = _facade()
    try:
        annotated, reward_sidecar = facade.curate_rewards.curate_record(
            current,
            source_path=source_path,
            source_line=source_line,
            calibration=calibration,
        )
    except facade.curate_rewards.RewardOntologyError as exc:
        return facade._facade_delegate(facade._reward_refusal_impl, stages, exc)
    annotation = annotated[facade.curate_rewards.ANNOTATION_FIELD]
    if annotation["source_reward_count"]:
        return facade._facade_delegate(
            facade._retained_rewards_impl, annotated, reward_sidecar, stages
        )
    return facade._facade_delegate(facade._reward_not_applicable_impl, annotated, stages)


def _record_services() -> RecordServices:
    facade = _facade()
    return facade.RecordServices(
        lambda record, stages, source: facade._compose_identity_stage(
            record,
            stages,
            source_path=source.path,
            source_line=source.line,
            source_sha256=source.sha256,
        ),
        lambda current, stages, source: facade._compose_bridge_stage(
            current,
            stages,
            source_path=source.path,
            source_line=source.line,
            source_sha256=source.sha256,
            source_file_sha256=source.file_sha256,
        ),
        lambda current, stages, context: facade._compose_preferences_stage(
            current, stages, source_path=context.source.path, source_line=context.source.line
        ),
        lambda current, kind, stages, context: facade._compose_coding_stage(
            current,
            kind,
            stages,
            source_path=context.source.path,
            source_line=context.source.line,
            source_sha256=context.source.sha256,
        ),
        lambda current, stages, context: facade._compose_rewards_stage(
            current,
            stages,
            source_path=context.source.path,
            source_line=context.source.line,
            calibration=context.calibration,
        ),
    )


def compose_record(
    record: Any,
    *,
    source_path: str,
    source_line: int,
    source_sha256: str,
    source_file_sha256: str | None = None,
    calibration: Any = None,
) -> ComposeDecision:
    facade = _facade()
    source = facade.SourceCoordinates(source_path, source_line, source_sha256, source_file_sha256)
    context = facade.RecordContext(source, calibration, facade.curate_trajectory_preferences)
    return facade._facade_delegate(
        facade._compose_record_impl, record, context, facade._record_services()
    )


def _compose_record_from_context(record: Any, context: RecordContext) -> ComposeDecision:
    source = context.source
    return _facade().compose_record(
        record,
        source_path=source.path,
        source_line=source.line,
        source_sha256=source.sha256,
        source_file_sha256=source.file_sha256,
        calibration=context.calibration,
    )


def compose_source_line(
    physical_line: bytes,
    *,
    source_path: str,
    source_line: int,
    source_file_sha256: str,
    calibration_catalog: Mapping[str, Any] | None = None,
    seen_source_semantics: MutableMapping[str, tuple[str, int]] | None = None,
    seen_curated_semantics: MutableMapping[str, tuple[str, int]] | None = None,
) -> ComposeDecision:
    facade = _facade()
    context = facade.SourceLineContext(
        source_path,
        source_line,
        source_file_sha256,
        calibration_catalog,
        seen_source_semantics,
        seen_curated_semantics,
        facade.curate_trajectory_preferences,
        facade._canonical_sha256,
        facade._compose_record_from_context,
        facade.calibration_for,
        facade._reject_duplicate_object_keys,
        facade.reject_json_constant,
        facade._excluded_source_line,
        facade._deduplicate_curated_record,
    )
    return facade._facade_delegate(facade._compose_source_line_impl, physical_line, context)


__all__ = """
_append_coding_lane_stage _bridge_view_trajectory _coding_lane_curator _coding_steps_repaired_copy
_compose_bridge_view_coding _compose_coding_stage _compose_episode_preference _compose_legacy_preference
_compose_mixed_family_preference_exclusion _compose_preferences_stage
_compose_rewards_stage _compose_same_state_preference _facade_delegate
_hidden_only_curation_applies _side_curation_failed_decision _stage _trajectory_preference compose_record compose_source_line
""".split()


if __package__:
    _expose_package_sibling(__name__)
