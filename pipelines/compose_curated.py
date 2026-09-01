#!/usr/bin/env python3
"""Compose record-level curation transforms into a new authenticated tree.

The implementation is split by responsibility. This module remains the
stable command/API facade and resolves collaborators at call time so existing
monkeypatch seams continue to exercise the vulnerable filesystem windows.
"""

from __future__ import annotations

import os
import sys
import argparse
import contextlib
import copy
import json
import re
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, MutableMapping

if __package__:
    from . import (
        compose_mill,
        curate_agentic,
        curate_bridge,
        curate_coding,
        curate_identity,
        curate_preferences,
        curate_rewards,
        training_audit,
    )
    from .check_records import reject_json_constant
    from .census import factory_identity_for_path
    from .compose_contract import (
        ACTION_EXCLUDED,
        ACTION_NOT_APPLICABLE,
        ACTION_RETAINED,
        COMPOSE_NAME,
        COMPOSE_VERSION,
        FFPC_UNITS_MIGRATION,
        LANE_ORDER,
        MANIFEST_DIRNAME,
        MANIFEST_FILENAME,
        PREFERENCE_CANDIDATE_KEYS,
        REASON_DUPLICATE_CURATED_RECORD,
        REASON_DUPLICATE_SOURCE_RECORD,
        REASON_EMPTY_CORPUS,
        REASON_INVALID_JSON,
        REASON_INVALID_UTF8,
        REASON_MIXED_PREFERENCE_FAMILIES,
        REASON_REWARD_ONTOLOGY,
        REASON_TRAJECTORY_GATE_PASSED,
        REASON_TRAJECTORY_GOAL_NORMALIZED,
        REASON_TRAJECTORY_IDENTICAL,
        REASON_TRAJECTORY_OUTCOME_MISSING,
        REASON_TRAJECTORY_OUTCOME_NOT_DIVERGENT,
        REASON_TRAJECTORY_PREFIX_ABSENT,
        REASON_TRAJECTORY_REWARD_MISSING,
        REASON_TRAJECTORY_REWARD_NOT_DIVERGENT,
        REASON_TRAJECTORY_SIDE_INVALID,
        REASON_TRAJECTORY_STEPS_EMPTY,
        REASON_TRAJECTORY_STEPS_INVALID,
        RECORDS_DIRNAME,
        REWARD_SIDECAR_FILENAME,
        SUMMARY_FILENAME,
        TRAJECTORY_GOAL_LOCATIONS,
        ComposeDecision,
        ComposeError,
        _canonical_sha256,
        _TrajectoryPreferenceDecision,
        canonical_json,
        sha256_hex,
    )
    from .compose_curated_calibration import (
        CalibrationContext,
        CalibrationServices,
        load_calibration as _load_calibration_impl,
    )
    from .compose_curated_context import (
        RecordContext,
        SourceCoordinates,
        StageDefinition,
        stage,
    )
    from . import compose_curated_identity as _identity_impl
    from .compose_curated_identity import BRIDGE_ORDER_ERROR_FRAGMENT
    from .compose_curated_record import (
        RecordServices,
        compose_record as _compose_record_impl,
    )
    from .compose_curated_run import (
        ComposeRunContext,
        ComposeRunHooks,
        ComposeRunServices,
        ComposeRunState,
        PhysicalSourceLine,
        RetainedLineContext,
        SourceFileContext,
        SourceLineContext as RunSourceLineContext,
        SummaryCommitContext,
        SummaryContext,
        authenticate_composed_artifacts as _authenticate_composed_artifacts_impl,
        captured_source_payloads as _captured_source_payloads_impl,
        capture_source_snapshot as _capture_source_snapshot_impl,
        claim_output_id as _claim_output_id_impl,
        commit_compose_summary as _commit_compose_summary_impl,
        compose_one_line as _compose_one_line_impl,
        compose_run as _compose_run_impl,
        compose_run_summary as _compose_run_summary_impl,
        compose_source_file as _compose_source_file_impl,
        facade_run_hooks as _facade_run_hooks,
        facade_run_services as _facade_run_services,
        new_manifest_entry as _new_manifest_entry_impl,
        record_excluded_line as _record_excluded_line_impl,
        record_retained_line as _record_retained_line_impl,
        write_compose_provenance as _write_compose_provenance_impl,
        write_emitted_records as _write_emitted_records_impl,
    )
    from .compose_curated_source import (
        SourceLineContext,
        compose_source_line as _compose_source_line_impl,
        transform_contract as _transform_contract_impl,
    )
    from .compose_destination import (
        PinnedDestination,
        _assert_descriptor_contained,
        _assert_destination_disjoint,
        _assert_new_destination,
        _assert_opened_source_identity,
        _assert_source_path_unchanged,
        _assert_unaliased_regular_member,
        _collect_source_directory,
        _contains_raw_segments,
        _create_pinned_new_directory,
        _destination_write_parts,
        _directory_binding_matches,
        _directory_identity,
        _discard_created_destination,
        _drain_descriptor,
        _is_under_raw,
        _open_pinned_child,
        _open_pinned_child_directory,
        _pinned_root_path,
        _read_exact_child_file,
        _read_exact_regular_file,
        _read_pinned_child_bytes,
        _refuse_existing_destination,
        _require_exact_directory,
        _scan_source_directory,
        _source_entry_metadata,
        _source_member_path,
        _stable_file_identity,
        _validated_member_relative,
        _verify_directory_binding,
        _verify_pinned_child,
        _write_new_text,
        create_pinned_destination,
        source_jsonl_members,
        write_pinned_new_bytes,
    )
    from .compose_trajectory import (
        _TRAJECTORY_DIVERGENCE_FIELDS,
        _compat_trajectory_preference,
        _curate_trajectory_sides,
        _is_same_state_pair,
        _mixed_preference_families,
        _normalize_trajectory_goal_whitespace,
        _present_trajectory_goals,
        _strip_hidden_only_side,
        _trajectory_divergence_reasons,
        _trajectory_gate_passed,
        _trajectory_goal_owner,
        _trajectory_side_needs_coding,
        _trajectory_side_validation_errors,
        _trajectory_step_reasons,
        _whitespace_only_goal,
        is_bridge_record,
        is_episode_record,
        is_preference_record,
    )
    from .curate_identity import (
        _parse_finite_json_float,
        _reject_duplicate_object_keys,
    )
    from .record_kind import preference_side_kinds
    from .round_txn import TransactionError
else:
    import compose_mill
    import curate_agentic
    import curate_bridge
    import curate_coding
    import curate_identity
    import curate_preferences
    import curate_rewards
    import training_audit
    from check_records import reject_json_constant
    from census import factory_identity_for_path
    from compose_contract import (
    ACTION_EXCLUDED,
    ACTION_NOT_APPLICABLE,
    ACTION_RETAINED,
    COMPOSE_NAME,
    COMPOSE_VERSION,
    FFPC_UNITS_MIGRATION,
    LANE_ORDER,
    MANIFEST_DIRNAME,
    MANIFEST_FILENAME,
    PREFERENCE_CANDIDATE_KEYS,
    REASON_DUPLICATE_CURATED_RECORD,
    REASON_DUPLICATE_SOURCE_RECORD,
    REASON_EMPTY_CORPUS,
    REASON_INVALID_JSON,
    REASON_INVALID_UTF8,
    REASON_MIXED_PREFERENCE_FAMILIES,
    REASON_REWARD_ONTOLOGY,
    REASON_TRAJECTORY_GATE_PASSED,
    REASON_TRAJECTORY_GOAL_NORMALIZED,
    REASON_TRAJECTORY_IDENTICAL,
    REASON_TRAJECTORY_OUTCOME_MISSING,
    REASON_TRAJECTORY_OUTCOME_NOT_DIVERGENT,
    REASON_TRAJECTORY_PREFIX_ABSENT,
    REASON_TRAJECTORY_REWARD_MISSING,
    REASON_TRAJECTORY_REWARD_NOT_DIVERGENT,
    REASON_TRAJECTORY_SIDE_INVALID,
    REASON_TRAJECTORY_STEPS_EMPTY,
    REASON_TRAJECTORY_STEPS_INVALID,
    RECORDS_DIRNAME,
    REWARD_SIDECAR_FILENAME,
    SUMMARY_FILENAME,
    TRAJECTORY_GOAL_LOCATIONS,
    ComposeDecision,
    ComposeError,
    _canonical_sha256,
    _TrajectoryPreferenceDecision,
    canonical_json,
    sha256_hex,
    )
    from compose_curated_calibration import (
    CalibrationContext,
    CalibrationServices,
    load_calibration as _load_calibration_impl,
    )
    from compose_curated_context import (
    RecordContext,
    SourceCoordinates,
    StageDefinition,
    stage,
    )
    import compose_curated_identity as _identity_impl
    from compose_curated_identity import BRIDGE_ORDER_ERROR_FRAGMENT
    from compose_curated_record import (
    RecordServices,
    compose_record as _compose_record_impl,
    )
    from compose_curated_run import (
    ComposeRunContext,
    ComposeRunServices,
    ComposeRunHooks,
    ComposeRunState,
    PhysicalSourceLine,
    SourceLineContext as RunSourceLineContext,
    RetainedLineContext,
    SourceFileContext,
    SummaryContext,
    SummaryCommitContext,
    authenticate_composed_artifacts as _authenticate_composed_artifacts_impl,
    captured_source_payloads as _captured_source_payloads_impl,
    capture_source_snapshot as _capture_source_snapshot_impl,
    claim_output_id as _claim_output_id_impl,
    commit_compose_summary as _commit_compose_summary_impl,
    compose_one_line as _compose_one_line_impl,
    compose_run as _compose_run_impl,
    compose_run_summary as _compose_run_summary_impl,
    compose_source_file as _compose_source_file_impl,
    facade_run_hooks as _facade_run_hooks,
    facade_run_services as _facade_run_services,
    new_manifest_entry as _new_manifest_entry_impl,
    record_excluded_line as _record_excluded_line_impl,
    record_retained_line as _record_retained_line_impl,
    write_compose_provenance as _write_compose_provenance_impl,
    write_emitted_records as _write_emitted_records_impl,
    )
    from compose_curated_source import (
    SourceLineContext,
    compose_source_line as _compose_source_line_impl,
    transform_contract as _transform_contract_impl,
    )
    from compose_destination import (
    PinnedDestination,
    _assert_descriptor_contained,
    _assert_destination_disjoint,
    _assert_new_destination,
    _assert_opened_source_identity,
    _assert_source_path_unchanged,
    _assert_unaliased_regular_member,
    _collect_source_directory,
    _contains_raw_segments,
    _create_pinned_new_directory,
    _destination_write_parts,
    _directory_binding_matches,
    _directory_identity,
    _discard_created_destination,
    _drain_descriptor,
    _is_under_raw,
    _open_pinned_child,
    _open_pinned_child_directory,
    _pinned_root_path,
    _read_exact_child_file,
    _read_exact_regular_file,
    _read_pinned_child_bytes,
    _refuse_existing_destination,
    _require_exact_directory,
    _scan_source_directory,
    _source_entry_metadata,
    _source_member_path,
    _stable_file_identity,
    _validated_member_relative,
    _verify_directory_binding,
    _verify_pinned_child,
    _write_new_text,
    create_pinned_destination,
    source_jsonl_members,
    write_pinned_new_bytes,
    )
    from compose_trajectory import (
    _TRAJECTORY_DIVERGENCE_FIELDS,
    _compat_trajectory_preference,
    _curate_trajectory_sides,
    _is_same_state_pair,
    _mixed_preference_families,
    _normalize_trajectory_goal_whitespace,
    _present_trajectory_goals,
    _strip_hidden_only_side,
    _trajectory_divergence_reasons,
    _trajectory_gate_passed,
    _trajectory_goal_owner,
    _trajectory_side_needs_coding,
    _trajectory_side_validation_errors,
    _trajectory_step_reasons,
    _whitespace_only_goal,
    is_bridge_record,
    is_episode_record,
    is_preference_record,
    )
    from curate_identity import (
    _parse_finite_json_float,
    _reject_duplicate_object_keys,
    )
    from record_kind import preference_side_kinds
    from round_txn import TransactionError

try:  # PR #93 is a sibling stack; consume its reviewed contract when present.
    if __package__:
        from . import curate_trajectory_preferences
    else:
        import curate_trajectory_preferences
except ModuleNotFoundError as missing_import:  # pragma: no cover - branch topology decides this
    allowed_missing = {
        "curate_trajectory_preferences",
        f"{__package__}.curate_trajectory_preferences",
    }
    if missing_import.name not in allowed_missing:
        raise
    curate_trajectory_preferences = None

_PIPELINES = Path(__file__).resolve().parent


REASON_IDENTITY_INVALID_PAYLOAD_SHAPE = (
    _identity_impl.REASON_IDENTITY_INVALID_PAYLOAD_SHAPE
)
CODING_STEP_ERROR_RE = _identity_impl.CODING_STEP_ERROR_RE
_PROBE_FAILED = _identity_impl._PROBE_FAILED


def _facade_delegate(callable_: Any, *args: Any, **kwargs: Any):
    """Keep compatibility adapters on one auditable delegation spine."""

    return callable_(*args, **kwargs)


def _trajectory_preference(record: dict[str, Any]) -> tuple[Any, str, str, str]:
    if curate_trajectory_preferences is not None:
        return (
            curate_trajectory_preferences.curate_trajectory_pair(record),
            curate_trajectory_preferences.TRANSFORM_NAME,
            curate_trajectory_preferences.TRANSFORM_VERSION,
            "reviewed_module",
        )
    return (
        _compat_trajectory_preference(record),
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
    return _facade_delegate(
        stage, StageDefinition(lane, name, version), action, **extra
    )


def _container_calibration_id_candidates(container: Mapping[str, Any]):
    for key in curate_identity.LEGACY_ID_KEYS:
        value = container.get(key)
        if isinstance(value, str) and value.strip():
            yield value.strip()


def _owner_calibration_id_candidates(owner: Mapping[str, Any]):
    for container in (owner, owner.get("meta"), owner.get("state")):
        if isinstance(container, Mapping):
            yield from _container_calibration_id_candidates(container)


def _calibration_id_candidates(record: Mapping[str, Any]):
    yield from _owner_calibration_id_candidates(record)
    for side in ("chosen", "rejected"):
        owner = record.get(side)
        if isinstance(owner, Mapping):
            yield from _owner_calibration_id_candidates(owner)


def calibration_for(
    record: Mapping[str, Any], catalog: Mapping[str, Any] | None
) -> Any:
    if not catalog or not isinstance(record, Mapping):
        return None
    for candidate in _facade_delegate(_calibration_id_candidates, record):
        calibration = catalog.get(curate_rewards.catalog_record_key(candidate))
        if calibration is not None:
            return calibration
    return None


def _only_identity_shape_details(mapping: Mapping[str, Any], matches: Any) -> bool:
    if list(mapping.get("reason_codes", [])) != [
        REASON_IDENTITY_INVALID_PAYLOAD_SHAPE
    ]:
        return False
    details = mapping.get("details")
    return bool(
        isinstance(details, list)
        and details
        and all(isinstance(detail, str) and matches(detail) for detail in details)
    )


def _is_bridge_order_only_rejection(mapping: Mapping[str, Any]) -> bool:
    return _only_identity_shape_details(
        mapping, lambda detail: BRIDGE_ORDER_ERROR_FRAGMENT in detail
    )


def _is_coding_step_only_rejection(mapping: Mapping[str, Any]) -> bool:
    return _only_identity_shape_details(
        mapping, lambda detail: CODING_STEP_ERROR_RE.match(detail) is not None
    )


def _source_preference_shape(record: Any) -> tuple[Any, bool]:
    if not (is_preference_record(record) and isinstance(record, Mapping)):
        return None, False
    side_kinds = preference_side_kinds(record)
    mixed = not _is_same_state_pair(record) and _mixed_preference_families(
        side_kinds
    )
    return side_kinds, mixed


def _identity_stage_evidence(
    identity_result: Any,
    deferred_lane: str | None,
    source_side_kinds: Any,
    mixed_preference_families: bool,
) -> tuple[list[str], dict[str, Any]]:
    reasons = list(identity_result.mapping.get("reason_codes", []))
    detail = copy.deepcopy(identity_result.mapping)
    if deferred_lane == "bridge":
        detail["bridge_order_deferred_to_bridge_lane"] = True
    if deferred_lane == "coding":
        detail["coding_steps_deferred_to_coding_lane"] = True
    if source_side_kinds is not None:
        detail["preference_side_kinds"] = list(source_side_kinds)
    if mixed_preference_families:
        detail["identity_reason_codes"] = reasons
        reasons = [REASON_MIXED_PREFERENCE_FAMILIES]
    return reasons, detail


def _bridge_order_repaired_copy(
    record: Mapping[str, Any],
    *,
    source_path: str,
    source_line: int,
    source_sha256: str,
) -> dict[str, Any] | None:
    decision: Any = _PROBE_FAILED
    with contextlib.suppress(Exception):
        decision = _facade_delegate(
            curate_bridge.curate_record,
            record,
            source_path=source_path,
            source_line=source_line,
            source_hash=source_sha256,
            source_file_hash=None,
        )
    if decision is _PROBE_FAILED:
        return None
    if decision.action != "repair" or not isinstance(decision.output_record, dict):
        return None
    return decision.output_record


def _coding_steps_repaired_copy(
    record: Mapping[str, Any],
    *,
    source_path: str,
    source_line: int,
    source_sha256: str,
) -> dict[str, Any] | None:
    curated: Any = _PROBE_FAILED
    with contextlib.suppress(Exception):
        curated, _manifest = _facade_delegate(
            curate_coding.curate_episode,
            copy.deepcopy(dict(record)),
            source_path=source_path,
            source_line=source_line,
            source_hash=source_sha256,
        )
    if curated is _PROBE_FAILED:
        return None
    return curated if isinstance(curated, dict) else None


def _identity_retry(
    repaired: dict[str, Any] | None,
    *,
    source_path: str,
    source_line: int,
    source_sha256: str,
):
    if repaired is None:
        return None
    retry = curate_identity.curate_record(
        curate_identity.SourceRecord(
            record=repaired,
            source_path=source_path,
            source_line=source_line,
            source_sha256=source_sha256,
        )
    )
    if retry.action == "retained" and isinstance(retry.record, dict):
        return retry
    return None


def _deferred_lane_repair(
    record: Any,
    identity_result: Any,
    *,
    source_path: str,
    source_line: int,
    source_sha256: str,
) -> tuple[Any, str | None]:
    if identity_result.action == "retained" or not isinstance(record, Mapping):
        return identity_result, None
    coordinates = {
        "source_path": source_path,
        "source_line": source_line,
        "source_sha256": source_sha256,
    }
    retries = (
        (
            is_bridge_record(record)
            and _is_bridge_order_only_rejection(identity_result.mapping),
            _bridge_order_repaired_copy,
            "bridge",
        ),
        (
            isinstance(record.get("steps"), list)
            and _is_coding_step_only_rejection(identity_result.mapping),
            _coding_steps_repaired_copy,
            "coding",
        ),
    )
    for applies, repair, lane in retries:
        if applies:
            retry = _identity_retry(repair(record, **coordinates), **coordinates)
            if retry is not None:
                return retry, lane
    return identity_result, None


def _compose_identity_stage(
    record: Any,
    stages: list[dict[str, Any]],
    *,
    source_path: str,
    source_line: int,
    source_sha256: str,
) -> "ComposeDecision | tuple[dict[str, Any], Any]":
    source_side_kinds, mixed_families = _source_preference_shape(record)
    result = curate_identity.curate_record(
        curate_identity.SourceRecord(
            record=record,
            source_path=source_path,
            source_line=source_line,
            source_sha256=source_sha256,
        )
    )
    result, deferred_lane = _deferred_lane_repair(
        record,
        result,
        source_path=source_path,
        source_line=source_line,
        source_sha256=source_sha256,
    )
    reasons, detail = _identity_stage_evidence(
        result,
        deferred_lane,
        source_side_kinds,
        mixed_families,
    )
    stages.append(
        _stage(
            "identity",
            curate_identity.TRANSFORM_NAME,
            curate_identity.TRANSFORM_VERSION,
            ACTION_RETAINED if result.action == "retained" else ACTION_EXCLUDED,
            reason_codes=reasons,
            lane_action=result.action,
            detail=detail,
        )
    )
    if result.action != "retained" or result.record is None:
        return ComposeDecision(
            ACTION_EXCLUDED, None, tuple(reasons), tuple(stages), None, None
        )
    current: dict[str, Any] = result.record
    if deferred_lane == "bridge":
        current["spike_events"] = copy.deepcopy(record["spike_events"])
    if deferred_lane == "coding":
        current["steps"] = copy.deepcopy(record["steps"])
    return current, result.mapping.get("record_kind")


def _compose_bridge_stage(
    current: dict[str, Any],
    stages: list[dict[str, Any]],
    *,
    source_path: str,
    source_line: int,
    source_sha256: str,
    source_file_sha256: str | None,
) -> "ComposeDecision | dict[str, Any]":
    if not is_bridge_record(current):
        stages.append(
            _stage(
                "bridge",
                curate_bridge.TRANSFORM_NAME,
                curate_bridge.TRANSFORM_VERSION,
                ACTION_NOT_APPLICABLE,
                lane_action=ACTION_NOT_APPLICABLE,
            )
        )
        return current
    decision = curate_bridge.curate_record(
        current,
        source_path=source_path,
        source_line=source_line,
        source_hash=source_sha256,
        source_file_hash=source_file_sha256,
    )
    reasons = list(decision.manifest.get("reason_codes", []))
    retained = decision.output_record is not None
    stages.append(
        _stage(
            "bridge",
            curate_bridge.TRANSFORM_NAME,
            curate_bridge.TRANSFORM_VERSION,
            ACTION_RETAINED if retained else ACTION_EXCLUDED,
            reason_codes=reasons,
            lane_action=decision.action,
            detail=decision.manifest,
        )
    )
    if not retained:
        return ComposeDecision(
            ACTION_EXCLUDED, None, tuple(reasons), tuple(stages), None, None
        )
    return decision.output_record


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
    preference_reasons = list(
        dict.fromkeys([REASON_TRAJECTORY_SIDE_INVALID, *side_curation_reasons])
    )
    stages.append(
        _stage(
            "preferences",
            COMPOSE_NAME,
            COMPOSE_VERSION,
            ACTION_EXCLUDED,
            reason_codes=preference_reasons,
            lane_action=ACTION_EXCLUDED,
            classification=classification,
            side_kinds=list(side_kinds),
            **stage_extra,
            side_curation=side_curation,
            side_curation_changed=side_curation_changed,
        )
    )
    return ComposeDecision(
        ACTION_EXCLUDED,
        None,
        tuple(preference_reasons),
        tuple(stages),
        None,
        None,
    )


def _compose_same_state_preference(
    current: dict[str, Any],
    side_kinds: tuple[str, str],
    stages: list[dict[str, Any]],
    *,
    source_path: str,
    source_line: int,
) -> "ComposeDecision | tuple[Any, list[str]]":
    curated, evidence, reasons, changed = _curate_trajectory_sides(
        current, source_path=source_path, source_line=source_line
    )
    if curated is None:
        return _side_curation_failed_decision(
            stages,
            evidence,
            reasons,
            changed,
            side_kinds=side_kinds,
            classification="same_state_side_curation_failed",
            schema="same_state_pair",
        )
    decision = curate_preferences.curate_preference_record(curated)
    retained = decision.record is not None
    preference_reasons = list(decision.reason_codes)
    if retained:
        preference_reasons = list(dict.fromkeys([*reasons, *preference_reasons]))
    stages.append(
        _stage(
            "preferences",
            curate_preferences.TRANSFORM_NAME,
            curate_preferences.TRANSFORM_VERSION,
            ACTION_RETAINED if retained else ACTION_EXCLUDED,
            reason_codes=preference_reasons,
            lane_action="repaired" if retained and changed else decision.action,
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
    side_kinds: tuple[str, str],
    stages: list[dict[str, Any]],
) -> ComposeDecision:
    preference_reasons = [REASON_MIXED_PREFERENCE_FAMILIES]
    stages.append(
        _stage(
            "preferences",
            COMPOSE_NAME,
            COMPOSE_VERSION,
            ACTION_EXCLUDED,
            reason_codes=preference_reasons,
            lane_action=ACTION_EXCLUDED,
            classification="mixed_preference_side_families",
            side_kinds=list(side_kinds),
        )
    )
    return ComposeDecision(
        ACTION_EXCLUDED,
        None,
        tuple(preference_reasons),
        tuple(stages),
        None,
        None,
    )


def _compose_episode_preference(
    current: dict[str, Any],
    side_kinds: tuple[str, str],
    stages: list[dict[str, Any]],
    *,
    source_path: str,
    source_line: int,
) -> "ComposeDecision | tuple[Any, list[str]]":
    curated, evidence, reasons, changed = _curate_trajectory_sides(
        current, source_path=source_path, source_line=source_line
    )
    if curated is None:
        return _side_curation_failed_decision(
            stages,
            evidence,
            reasons,
            changed,
            side_kinds=side_kinds,
            classification="trajectory_side_curation_failed",
        )
    decision, name, version, implementation = _trajectory_preference(curated)
    preference_reasons = list(
        dict.fromkeys([*reasons, *decision.reason_codes])
    )
    retained = decision.record is not None
    stages.append(
        _stage(
            "preferences",
            name,
            version,
            ACTION_RETAINED if retained else ACTION_EXCLUDED,
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
    decision = curate_preferences.curate_preference_record(current)
    reasons = list(decision.reason_codes)
    stages.append(
        _stage(
            "preferences",
            curate_preferences.TRANSFORM_NAME,
            curate_preferences.TRANSFORM_VERSION,
            ACTION_RETAINED if decision.record is not None else ACTION_EXCLUDED,
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
    if not is_preference_record(current):
        stages.append(
            _stage(
                "preferences",
                curate_preferences.TRANSFORM_NAME,
                curate_preferences.TRANSFORM_VERSION,
                ACTION_NOT_APPLICABLE,
                lane_action=ACTION_NOT_APPLICABLE,
            )
        )
        return current
    side_kinds = preference_side_kinds(current)
    if _is_same_state_pair(current):
        outcome = _compose_same_state_preference(
            current,
            side_kinds,
            stages,
            source_path=source_path,
            source_line=source_line,
        )
    elif _mixed_preference_families(side_kinds):
        return _compose_mixed_family_preference_exclusion(side_kinds, stages)
    elif side_kinds == ("episode", "episode"):
        outcome = _compose_episode_preference(
            current,
            side_kinds,
            stages,
            source_path=source_path,
            source_line=source_line,
        )
    else:
        outcome = _compose_legacy_preference(current, side_kinds, stages)
    if isinstance(outcome, ComposeDecision):
        return outcome
    decision, reasons = outcome
    if decision.record is None:
        return ComposeDecision(
            ACTION_EXCLUDED, None, tuple(reasons), tuple(stages), None, None
        )
    return decision.record


def _coding_lane_curator(current: dict[str, Any], registered_kind: Any) -> Any:
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
    reasons = list(manifest.get("reason_codes", []))
    stages.append(
        _stage(
            "coding",
            module.TRANSFORM_NAME,
            module.TRANSFORM_VERSION,
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
    view = record.get("language_view")
    trajectory = view.get("trajectory") if isinstance(view, Mapping) else None
    if not isinstance(trajectory, dict):
        return None
    needs_coding = curate_coding.steps_path(trajectory) is not None
    if needs_coding or curate_coding.contains_hidden_reasoning_key(trajectory):
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
    if curate_coding.steps_path(trajectory) is not None:
        module = curate_coding
        curated, detail = curate_coding.curate_episode(
            trajectory,
            source_path=f"{source_path}#language_view.trajectory",
            source_line=source_line,
            source_hash=_canonical_sha256(trajectory),
        )
        detail = copy.deepcopy(detail)
    else:
        module = curate_agentic
        curated, detail = _strip_hidden_only_side(trajectory)
    detail["embedded_at"] = "language_view.trajectory"
    if curated is None:
        return _append_coding_lane_stage(stages, module, None, detail)
    updated = copy.deepcopy(current)
    updated["language_view"]["trajectory"] = curated
    if curate_coding.contains_hidden_reasoning_key(updated):
        updated, wrapper = _strip_hidden_only_side(updated)
        removed = wrapper["hidden_reasoning_fields_removed"]
        detail["hidden_reasoning_fields_removed"] = (
            detail.get("hidden_reasoning_fields_removed", 0) + removed
        )
        detail["wrapper_hidden_reasoning_fields_removed"] = removed
        detail["reason_codes"] = list(
            dict.fromkeys(
                [*detail.get("reason_codes", []), *wrapper.get("reason_codes", [])]
            )
        )
        if removed:
            detail["action"] = "modified"
    return _append_coding_lane_stage(stages, module, updated, detail)


def _hidden_only_curation_applies(
    current: dict[str, Any], registered_kind: Any
) -> bool:
    governed = (
        registered_kind == "thalamic"
        or is_preference_record(current)
        or is_bridge_record(current)
    )
    return governed and curate_coding.contains_hidden_reasoning_key(current)


def _compose_coding_stage(
    current: dict[str, Any],
    registered_kind: Any,
    stages: list[dict[str, Any]],
    *,
    source_path: str,
    source_line: int,
    source_sha256: str,
) -> "ComposeDecision | dict[str, Any]":
    module = _coding_lane_curator(current, registered_kind)
    if module is None:
        trajectory = (
            _bridge_view_trajectory(current) if is_bridge_record(current) else None
        )
        if trajectory is not None:
            return _compose_bridge_view_coding(
                current,
                trajectory,
                stages,
                source_path=source_path,
                source_line=source_line,
            )
        if _hidden_only_curation_applies(current, registered_kind):
            cleaned, detail = _strip_hidden_only_side(current)
            return _append_coding_lane_stage(
                stages, curate_agentic, cleaned, detail
            )
        stages.append(
            _stage(
                "coding",
                curate_coding.TRANSFORM_NAME,
                curate_coding.TRANSFORM_VERSION,
                ACTION_NOT_APPLICABLE,
                lane_action=ACTION_NOT_APPLICABLE,
            )
        )
        return current
    curator = (
        curate_agentic.curate_record
        if module is curate_agentic
        else curate_coding.curate_episode
    )
    curated, manifest = curator(
        current,
        source_path=source_path,
        source_line=source_line,
        source_hash=source_sha256,
    )
    return _append_coding_lane_stage(stages, module, curated, manifest)


def _compose_rewards_stage(
    current: dict[str, Any],
    stages: list[dict[str, Any]],
    *,
    source_path: str,
    source_line: int,
    calibration: Any,
) -> "ComposeDecision | tuple[dict[str, Any], dict[str, Any] | None]":
    sidecar: dict[str, Any] | None = None
    try:
        annotated, reward_sidecar = curate_rewards.curate_record(
            current,
            source_path=source_path,
            source_line=source_line,
            calibration=calibration,
        )
    except curate_rewards.RewardOntologyError as exc:
        stages.append(
            _stage(
                "rewards",
                curate_rewards.ANNOTATION_FIELD,
                curate_rewards.REWARD_TRANSFORM_VERSION,
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
    annotation = annotated[curate_rewards.ANNOTATION_FIELD]
    if annotation["source_reward_count"]:
        current = annotated
        sidecar = reward_sidecar
        stages.append(
            _stage(
                "rewards",
                curate_rewards.ANNOTATION_FIELD,
                curate_rewards.REWARD_TRANSFORM_VERSION,
                ACTION_RETAINED,
                reason_codes=annotation["reason_codes"],
                lane_action=annotation["comparability"],
                comparability=annotation["comparability"],
                source_sidecar_id=annotation["source_sidecar_id"],
                source_reward_count=annotation["source_reward_count"],
            )
        )
    else:
        current = annotated
        current.pop(curate_rewards.ANNOTATION_FIELD, None)
        stages.append(
            _stage(
                "rewards",
                curate_rewards.ANNOTATION_FIELD,
                curate_rewards.REWARD_TRANSFORM_VERSION,
                ACTION_NOT_APPLICABLE,
                lane_action=ACTION_NOT_APPLICABLE,
                source_reward_count=0,
            )
        )
    return current, sidecar


def _record_services() -> RecordServices:
    return RecordServices(
        lambda record, stages, source: _compose_identity_stage(
            record,
            stages,
            source_path=source.path,
            source_line=source.line,
            source_sha256=source.sha256,
        ),
        lambda current, stages, source: _compose_bridge_stage(
            current,
            stages,
            source_path=source.path,
            source_line=source.line,
            source_sha256=source.sha256,
            source_file_sha256=source.file_sha256,
        ),
        lambda current, stages, context: _compose_preferences_stage(
            current,
            stages,
            source_path=context.source.path,
            source_line=context.source.line,
        ),
        lambda current, registered_kind, stages, context: _compose_coding_stage(
            current,
            registered_kind,
            stages,
            source_path=context.source.path,
            source_line=context.source.line,
            source_sha256=context.source.sha256,
        ),
        lambda current, stages, context: _compose_rewards_stage(
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
    """Run every applicable record lane without mutating the input."""

    source = SourceCoordinates(
        source_path,
        source_line,
        source_sha256,
        source_file_sha256,
    )
    context = RecordContext(
        source,
        calibration,
        curate_trajectory_preferences,
    )
    return _facade_delegate(_compose_record_impl, record, context, _record_services())


def _compose_record_from_context(
    record: Any,
    context: RecordContext,
) -> ComposeDecision:
    source = context.source
    return compose_record(
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
    """Compose one exact LF-framed source line through every record lane."""

    context = SourceLineContext(
        source_path=source_path,
        source_line=source_line,
        source_file_sha256=source_file_sha256,
        calibration_catalog=calibration_catalog,
        seen_source_semantics=seen_source_semantics,
        seen_curated_semantics=seen_curated_semantics,
        trajectory_preferences=curate_trajectory_preferences,
        canonical_sha256=_canonical_sha256,
        record_composer=_compose_record_from_context,
        calibration_lookup=calibration_for,
        duplicate_key_rejector=_reject_duplicate_object_keys,
        constant_rejector=reject_json_constant,
        excluded_source_line=_excluded_source_line,
        deduplicate_curated_record=_deduplicate_curated_record,
    )
    return _facade_delegate(_compose_source_line_impl, physical_line, context)


def _identity_owner(record: dict[str, Any], pointer: Any) -> dict[str, Any] | None:
    if pointer == "/":
        return record
    if not isinstance(pointer, str) or not pointer.startswith("/"):
        return None
    owner: Any = record
    for token in pointer[1:].split("/"):
        key = token.replace("~1", "/").replace("~0", "~")
        if not isinstance(owner, dict):
            return None
        owner = owner.get(key)
    return owner if isinstance(owner, dict) else None


def _json_pointer_tokens(pointer: Any) -> list[str] | None:
    if not isinstance(pointer, str) or not pointer.startswith("/") or pointer == "/":
        return None
    return [
        token.replace("~1", "/").replace("~0", "~")
        for token in pointer[1:].split("/")
    ]


def _pop_json_pointer(record: dict[str, Any], pointer: Any) -> None:
    tokens = _json_pointer_tokens(pointer)
    if tokens is None:
        return
    owner: Any = record
    for token in tokens[:-1]:
        if not isinstance(owner, dict):
            return
        owner = owner.get(token)
    if isinstance(owner, dict) and tokens[-1]:
        owner.pop(tokens[-1], None)


def _original_id_paths(originals: Any) -> list[str]:
    if not isinstance(originals, list):
        return []
    return [
        item["path"]
        for item in originals
        if isinstance(item, dict) and isinstance(item.get("path"), str)
    ]


def _mapped_legacy_id_paths(detail: Mapping[str, Any] | None) -> tuple[str, ...]:
    if not isinstance(detail, Mapping):
        return ()
    paths = _original_id_paths(detail.get("original_ids"))
    mappings = detail.get("id_mappings")
    if isinstance(mappings, list):
        for mapping in mappings:
            if isinstance(mapping, dict):
                paths.extend(_original_id_paths(mapping.get("original_ids")))
    return tuple(dict.fromkeys(paths))


def _semantic_identity_owners(record: dict[str, Any]) -> list[dict[str, Any]]:
    owners = [record]
    for side in ("chosen", "rejected"):
        owner = record.get(side)
        if isinstance(owner, dict):
            owners.append(owner)
    view = record.get("language_view")
    trajectory = view.get("trajectory") if isinstance(view, Mapping) else None
    if isinstance(trajectory, dict):
        owners.append(trajectory)
    return owners


def _identity_stage_detail_of(decision: ComposeDecision) -> dict[str, Any] | None:
    identity_stage = next(
        (item for item in decision.stages if item.get("lane") == "identity"), None
    )
    detail = identity_stage.get("detail") if isinstance(identity_stage, dict) else None
    return detail if isinstance(detail, dict) else None


def _strip_assigned_ids(
    semantic: dict[str, Any], detail: dict[str, Any] | None
) -> None:
    mappings = detail.get("id_mappings") if isinstance(detail, dict) else None
    for mapping in mappings if isinstance(mappings, list) else ():
        if not isinstance(mapping, dict):
            continue
        owner = _identity_owner(semantic, mapping.get("owner_path"))
        if owner is not None and owner.get("id") == mapping.get("output_id"):
            owner.pop("id", None)
    for path in _mapped_legacy_id_paths(detail):
        _pop_json_pointer(semantic, path)


def _strip_provenance_labels(semantic: dict[str, Any]) -> None:
    for owner in _semantic_identity_owners(semantic):
        meta = owner.get("meta")
        if not isinstance(meta, dict):
            continue
        for label in ("factory", "generator", "generator_version", "run", "round"):
            meta.pop(label, None)


def _strip_sidecar_binding(semantic: dict[str, Any]) -> None:
    annotation = semantic.get(curate_rewards.ANNOTATION_FIELD)
    if not isinstance(annotation, dict):
        return
    annotation.pop("source_sidecar_id", None)
    magnitude = annotation.get("magnitude")
    values = magnitude.get("values") if isinstance(magnitude, dict) else None
    for value in values if isinstance(values, list) else ():
        if isinstance(value, dict):
            value.pop("calibration_source", None)


def _post_transform_semantic_sha256(decision: ComposeDecision) -> str:
    if decision.record is None:
        raise ComposeError("cannot hash a missing curated record")
    semantic = copy.deepcopy(decision.record)
    _strip_assigned_ids(semantic, _identity_stage_detail_of(decision))
    _strip_provenance_labels(semantic)
    _strip_sidecar_binding(semantic)
    return _canonical_sha256(semantic)


def _deduplicate_curated_record(
    decision: ComposeDecision,
    *,
    source_path: str,
    source_line: int,
    seen_curated_semantics: MutableMapping[str, tuple[str, int]] | None,
) -> ComposeDecision:
    if (
        seen_curated_semantics is None
        or decision.action != ACTION_RETAINED
        or decision.record is None
    ):
        return decision
    digest = _post_transform_semantic_sha256(decision)
    first = seen_curated_semantics.get(digest)
    if first is None:
        seen_curated_semantics[digest] = (source_path, source_line)
        return decision
    duplicate = _stage(
        "post_transform_dedup",
        COMPOSE_NAME,
        COMPOSE_VERSION,
        ACTION_EXCLUDED,
        reason_codes=[REASON_DUPLICATE_CURATED_RECORD],
        semantic_sha256=digest,
        first_source_path=first[0],
        first_source_line=first[1],
    )
    return ComposeDecision(
        ACTION_EXCLUDED,
        None,
        (REASON_DUPLICATE_CURATED_RECORD,),
        (*decision.stages, duplicate),
        None,
        None,
    )


def _excluded_source_line(reason: str, detail: dict[str, Any]) -> ComposeDecision:
    return ComposeDecision(
        ACTION_EXCLUDED,
        None,
        (reason,),
        (
            _stage(
                "source",
                COMPOSE_NAME,
                COMPOSE_VERSION,
                ACTION_EXCLUDED,
                reason_codes=[reason],
                detail=detail,
            ),
        ),
        None,
        None,
    )


def transform_contract() -> dict[str, Any]:
    """Return the exact transforms written into the compose summary."""

    return _facade_delegate(
        _transform_contract_impl, curate_trajectory_preferences
    )


def _source_snapshot_identities(
    resolved_source: Path, source_members: tuple[str, ...]
) -> dict[str, tuple[tuple[int, ...], str, bool]]:
    """Capture file and factory identities through facade-owned seams."""

    identities = {}
    for relative in source_members:
        path = _facade_delegate(
            _source_member_path,
            resolved_source, relative, f"compose source {relative}"
        )
        factory, verified = _facade_delegate(
            factory_identity_for_path, resolved_source, path
        )
        identities[relative] = (_stable_file_identity(path.lstat()), factory, verified)
    return identities


def _captured_source_payloads(
    resolved_source: Path, source_members: tuple[str, ...]
) -> dict[str, bytes]:
    """Read every captured member exactly once through the current facade."""

    return _facade_delegate(
        _captured_source_payloads_impl,
        resolved_source, source_members, _read_exact_regular_file
    )


def _calibration_services() -> CalibrationServices:
    """Resolve calibration and audit collaborators at invocation time."""

    return CalibrationServices(
        _read_exact_child_file,
        _reject_duplicate_object_keys,
        reject_json_constant,
        _parse_finite_json_float,
        curate_rewards.units_migration_catalog,
        sha256_hex,
        training_audit.audit_run,
    )


def _load_calibration(
    source_run: Path, units_migration: Path | None
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Compatibility boundary for fail-closed calibration loading."""

    return _facade_delegate(
        _load_calibration_impl,
        CalibrationContext(source_run, units_migration), _calibration_services()
    )


def compact_audit_report(
    report: Mapping[str, Any] | None, record_count: int
) -> dict[str, Any]:
    """Return the exact compact audit declaration stored in ``COMPOSE.json``."""

    if record_count == 0:
        return {
            "run_dir": RECORDS_DIRNAME,
            "records": 0,
            "training_ready": False,
            "blockers": [REASON_EMPTY_CORPUS],
        }
    if report is None:
        raise ComposeError("nonempty compact audit requires an audit report")
    return {
        "run_dir": RECORDS_DIRNAME,
        "records": report["totals"]["records"],
        "training_ready": bool(report["training_ready"]),
        "blockers": list(report["blockers"]),
        "identity_coverage_pct": report["identity"]["coverage_pct"],
        "provenance_canonical_pct": report["provenance"]["canonical_pct"],
        "preference_context_purity_pct": report["preferences"]["context_purity_pct"],
    }


def _audit_records(records_dir: Path, record_count: int) -> dict[str, Any]:
    """Audit the curated payload and refuse to call an empty corpus ready."""

    report = training_audit.audit_run(records_dir) if record_count else None
    return _facade_delegate(compact_audit_report, report, record_count)


def _jsonl_physical_lines(raw_file: bytes) -> list[bytes]:
    """Split LF-framed JSONL into physical lines without decoding first."""

    physical_lines = raw_file.split(b"\n")
    terminated_lines = len(physical_lines) - 1
    if physical_lines and physical_lines[-1] == b"":
        physical_lines.pop()
    for index in range(min(terminated_lines, len(physical_lines))):
        if physical_lines[index].endswith(b"\r"):
            physical_lines[index] = physical_lines[index][:-1]
    return physical_lines


def jsonl_physical_lines(raw_file: bytes) -> list[bytes]:
    """Public boundary for exact LF-framed JSONL splitting."""

    return _facade_delegate(_jsonl_physical_lines, raw_file)


def _new_manifest_entry(
    relative: Any,
    line_number: int,
    source_sha256: str,
    source_file_sha256: str,
) -> dict[str, Any]:
    context = RunSourceLineContext(
        relative,
        line_number,
        source_file_sha256,
        None,
        [],
    )
    return _facade_delegate(_new_manifest_entry_impl, context, source_sha256)


def _claim_output_id(
    state: _ComposeRunState,
    output_id: Any,
    location: str,
) -> None:
    return _facade_delegate(_claim_output_id_impl, state, output_id, location)


def _record_retained_line(
    state: _ComposeRunState,
    decision: ComposeDecision,
    entry: dict[str, Any],
    *,
    relative: Any,
    location: str,
    emitted: list[str],
) -> None:
    context = RetainedLineContext(entry, relative, location, emitted)
    return _facade_delegate(
        _record_retained_line_impl,
        state,
        decision,
        context,
        _claim_output_id,
    )


def _record_excluded_line(
    state: _ComposeRunState,
    decision: ComposeDecision,
    entry: dict[str, Any],
) -> None:
    return _facade_delegate(_record_excluded_line_impl, state, decision, entry)


def mill_quarantined_decision(finding: Any) -> ComposeDecision:
    """Exclude a corpus-level mill finding before any lane can run."""

    reasons = list(finding.reason_codes)
    return ComposeDecision(
        ACTION_EXCLUDED,
        None,
        tuple(reasons),
        (
            _stage(
                "source",
                COMPOSE_NAME,
                COMPOSE_VERSION,
                ACTION_EXCLUDED,
                reason_codes=reasons,
                classification="foreign_mill_quarantined",
                detail=finding.as_dict(),
            ),
        ),
        None,
        None,
    )


def _compose_one_line(
    state: _ComposeRunState,
    physical_line: bytes,
    *,
    relative: Any,
    line_number: int,
    source_file_sha256: str,
    catalog: Mapping[str, Any] | None,
    emitted: list[str],
    mill_findings: Mapping[tuple[str, int], Any] | None = None,
) -> None:
    context = RunSourceLineContext(
        relative,
        line_number,
        source_file_sha256,
        catalog,
        emitted,
        mill_findings,
    )
    return _facade_delegate(
        _compose_one_line_impl,
        state,
        PhysicalSourceLine(physical_line, context),
        _run_services().source,
        _run_hooks(),
    )


def _write_emitted_records(
    state: _ComposeRunState,
    destination_target: int | PinnedDestination,
    relative: Any,
    emitted: list[str],
) -> None:
    context = SourceFileContext(relative, b"", destination_target, None)
    return _facade_delegate(
        _write_emitted_records_impl,
        state,
        context,
        emitted,
        _run_services().destination,
    )


def _compose_source_file(
    state: _ComposeRunState,
    *,
    relative: Any,
    raw_file: bytes,
    destination_target: int | PinnedDestination,
    catalog: Mapping[str, Any] | None,
    mill_findings: Mapping[tuple[str, int], Any] | None = None,
) -> None:
    context = SourceFileContext(
        relative,
        raw_file,
        destination_target,
        catalog,
        mill_findings,
    )
    return _facade_delegate(
        _compose_source_file_impl,
        state,
        context,
        _run_services(),
        _run_hooks(),
    )


def _capture_source_snapshot(
    resolved_source: Path,
) -> tuple[
    tuple[str, ...],
    dict[str, bytes],
    dict[str, tuple[str, bool]],
]:
    return _facade_delegate(
        _capture_source_snapshot_impl, resolved_source, _run_services().source
    )


def _write_compose_provenance(
    state: _ComposeRunState,
    destination_target: int | PinnedDestination,
) -> tuple[str, str]:
    return _facade_delegate(
        _write_compose_provenance_impl,
        state,
        destination_target,
        _run_services().destination,
    )


def _authenticate_composed_artifacts(
    pinned_destination: PinnedDestination,
    expected_digests: Mapping[str, str],
) -> None:
    return _facade_delegate(
        _authenticate_composed_artifacts_impl,
        pinned_destination,
        expected_digests,
        _run_services().destination,
    )


def _compose_run_summary(
    state: _ComposeRunState,
    *,
    resolved_source: Path,
    destination_path: Path,
    calibration_descriptor: Any,
    calibrated_records: int,
    manifest_sha256: str,
    sidecar_sha256: str,
    records_dir: Path,
) -> dict[str, Any]:
    context = SummaryContext(
        resolved_source,
        destination_path,
        calibration_descriptor,
        calibrated_records,
        manifest_sha256,
        sidecar_sha256,
        records_dir,
    )
    return _facade_delegate(
        _compose_run_summary_impl, state, context, _run_services().report
    )


def _commit_compose_summary(
    state: _ComposeRunState,
    pinned_destination: PinnedDestination,
    summary: Mapping[str, Any],
    manifest_sha256: str,
    sidecar_sha256: str,
) -> None:
    return _facade_delegate(
        _commit_compose_summary_impl,
        state,
        SummaryCommitContext(
            pinned_destination,
            summary,
            manifest_sha256,
            sidecar_sha256,
        ),
        _run_services().destination,
        lambda pinned, expected, _services: _authenticate_composed_artifacts(
            pinned,
            expected,
        ),
    )


def _run_services() -> ComposeRunServices:
    """Resolve every historical monkeypatch seam for one transaction."""

    return _facade_delegate(
        _facade_run_services,
        sys.modules[__name__],
        compose_mill.index_compose_mills,
    )


def _run_hooks() -> ComposeRunHooks:
    """Resolve every run helper through the facade's live module bindings."""

    return _facade_delegate(_facade_run_hooks, sys.modules[__name__])


def compose_run(
    source_run: str | Path,
    destination: str | Path,
    *,
    units_migration: str | Path | None = None,
) -> dict[str, Any]:
    """Compose every JSONL record into a new descriptor-pinned destination."""

    context = ComposeRunContext(
        Path(source_run),
        Path(destination),
        Path(units_migration) if units_migration is not None else None,
    )
    return _facade_delegate(
        _compose_run_impl, context, _run_services(), _run_hooks()
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("source_run", help="source run directory (read-only)")
    parser.add_argument("destination", help="new curated destination (must not exist)")
    parser.add_argument(
        "--units-migration",
        help="explicit reward calibration sidecar; defaults to the FFPC sidecar",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="exit 1 when the composed tree is not training_ready",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        summary = compose_run(
            args.source_run, args.destination, units_migration=args.units_migration
        )
    except (
        ComposeError,
        curate_identity.IdentityCurationError,
        curate_rewards.RewardOntologyError,
        TransactionError,
        OSError,
    ) as exc:
        print(f"compose_curated: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    if args.strict and not summary["audit"]["training_ready"]:
        for blocker in summary["audit"]["blockers"]:
            print(f"blocker: {blocker}", file=sys.stderr)
        return 1
    return 0


_ComposeRunState = ComposeRunState

# These names were historically module attributes used by tests and stacked
# branches. Referencing them explicitly preserves that compatibility surface
# without widening star imports through ``__all__``.
_COMPATIBILITY_EXPORTS = (
    os,
    sys,
    argparse,
    contextlib,
    copy,
    json,
    re,
    Counter,
    dataclass,
    field,
    curate_agentic,
    curate_bridge,
    curate_coding,
    curate_preferences,
    preference_side_kinds,
    compact_audit_report,
    mill_quarantined_decision,
    TRAJECTORY_GOAL_LOCATIONS,
    _TrajectoryPreferenceDecision,
    BRIDGE_ORDER_ERROR_FRAGMENT,
    _authenticate_composed_artifacts,
    _claim_output_id,
    _commit_compose_summary,
    _compose_one_line,
    _compose_run_summary,
    _compose_source_file,
    _new_manifest_entry,
    _record_excluded_line,
    _record_retained_line,
    _write_compose_provenance,
    _write_emitted_records,
)


__all__ = [
    "ACTION_EXCLUDED",
    "ACTION_NOT_APPLICABLE",
    "ACTION_RETAINED",
    "COMPOSE_NAME",
    "COMPOSE_VERSION",
    "ComposeDecision",
    "ComposeError",
    "FFPC_UNITS_MIGRATION",
    "LANE_ORDER",
    "MANIFEST_DIRNAME",
    "MANIFEST_FILENAME",
    "PREFERENCE_CANDIDATE_KEYS",
    "REASON_DUPLICATE_CURATED_RECORD",
    "REASON_DUPLICATE_SOURCE_RECORD",
    "REASON_EMPTY_CORPUS",
    "REASON_INVALID_JSON",
    "REASON_INVALID_UTF8",
    "REASON_MIXED_PREFERENCE_FAMILIES",
    "REASON_REWARD_ONTOLOGY",
    "REASON_TRAJECTORY_GATE_PASSED",
    "REASON_TRAJECTORY_GOAL_NORMALIZED",
    "REASON_TRAJECTORY_IDENTICAL",
    "REASON_TRAJECTORY_OUTCOME_MISSING",
    "REASON_TRAJECTORY_OUTCOME_NOT_DIVERGENT",
    "REASON_TRAJECTORY_PREFIX_ABSENT",
    "REASON_TRAJECTORY_REWARD_MISSING",
    "REASON_TRAJECTORY_REWARD_NOT_DIVERGENT",
    "REASON_TRAJECTORY_SIDE_INVALID",
    "REASON_TRAJECTORY_STEPS_EMPTY",
    "REASON_TRAJECTORY_STEPS_INVALID",
    "RECORDS_DIRNAME",
    "REWARD_SIDECAR_FILENAME",
    "SUMMARY_FILENAME",
    "TRAJECTORY_GOAL_LOCATIONS",
    "PinnedDestination",
    "_TRAJECTORY_DIVERGENCE_FIELDS",
    "_TrajectoryPreferenceDecision",
    "_assert_descriptor_contained",
    "_assert_destination_disjoint",
    "_assert_new_destination",
    "_assert_opened_source_identity",
    "_assert_source_path_unchanged",
    "_assert_unaliased_regular_member",
    "_canonical_sha256",
    "_collect_source_directory",
    "_compat_trajectory_preference",
    "_contains_raw_segments",
    "create_pinned_destination",
    "_create_pinned_new_directory",
    "_curate_trajectory_sides",
    "_destination_write_parts",
    "_directory_binding_matches",
    "_directory_identity",
    "_discard_created_destination",
    "_drain_descriptor",
    "_is_same_state_pair",
    "_is_under_raw",
    "_mixed_preference_families",
    "_normalize_trajectory_goal_whitespace",
    "_open_pinned_child",
    "_open_pinned_child_directory",
    "_pinned_root_path",
    "_present_trajectory_goals",
    "_read_exact_child_file",
    "_read_exact_regular_file",
    "_read_pinned_child_bytes",
    "_refuse_existing_destination",
    "_require_exact_directory",
    "_scan_source_directory",
    "_source_entry_metadata",
    "_source_member_path",
    "_stable_file_identity",
    "_trajectory_divergence_reasons",
    "_trajectory_gate_passed",
    "_trajectory_goal_owner",
    "_trajectory_side_needs_coding",
    "_trajectory_side_validation_errors",
    "_trajectory_step_reasons",
    "_validated_member_relative",
    "_verify_directory_binding",
    "_verify_pinned_child",
    "_whitespace_only_goal",
    "_write_new_text",
    "write_pinned_new_bytes",
    "calibration_for",
    "canonical_json",
    "compose_record",
    "compose_run",
    "compose_source_line",
    "curate_trajectory_preferences",
    "is_bridge_record",
    "is_episode_record",
    "is_preference_record",
    "jsonl_physical_lines",
    "main",
    "parse_args",
    "sha256_hex",
    "source_jsonl_members",
    "transform_contract",
]


if __name__ == "__main__":
    raise SystemExit(main())
