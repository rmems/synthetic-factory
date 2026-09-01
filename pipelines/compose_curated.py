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

import compose_mill  # noqa: E402
import curate_identity  # noqa: E402
import curate_rewards  # noqa: E402
import training_audit  # noqa: E402
from check_records import reject_json_constant  # noqa: E402
from census import factory_identity_for_path  # noqa: E402
from compose_contract import (  # noqa: E402,F401
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
    audit_records as _audit_records_impl,
    compact_audit_report,
    load_calibration as _load_calibration_impl,
)
from compose_curated_context import (
    RecordContext,
    SourceCoordinates,
    StageDefinition,
    stage,
)
from compose_curated_identity import (
    BRIDGE_ORDER_ERROR_FRAGMENT,
    calibration_for,
)
import compose_curated_coding as _coding_impl
import compose_curated_identity as _identity_impl
import compose_curated_preferences as _preferences_impl
import compose_curated_source as _source_impl
from compose_curated_record import (
    RecordServices,
    compose_record as _compose_record_impl,
)
from compose_curated_run import (
    ComposeCliServices,
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
    jsonl_physical_lines,
    main as _main_impl,
    mill_quarantined_decision as _mill_quarantined_decision_impl,
    new_manifest_entry as _new_manifest_entry_impl,
    parse_args,
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
import curate_agentic
import curate_bridge
import curate_coding
import curate_preferences
from record_kind import preference_side_kinds
from compose_destination import (  # noqa: E402,F401
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
from compose_trajectory import (  # noqa: E402,F401
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
from curate_identity import (  # noqa: E402
    _parse_finite_json_float,
    _reject_duplicate_object_keys,
)
from round_txn import TransactionError  # noqa: E402

_PIPELINES = Path(__file__).resolve().parent

try:  # PR #93 is a sibling stack; consume its reviewed contract when present.
    import curate_trajectory_preferences  # type: ignore[import-not-found]  # noqa: E402
except ModuleNotFoundError as missing_import:  # pragma: no cover - branch topology decides this
    if missing_import.name != "curate_trajectory_preferences":
        raise
    curate_trajectory_preferences = None


REASON_IDENTITY_INVALID_PAYLOAD_SHAPE = (
    _identity_impl.REASON_IDENTITY_INVALID_PAYLOAD_SHAPE
)
CODING_STEP_ERROR_RE = _identity_impl.CODING_STEP_ERROR_RE
_PROBE_FAILED = _identity_impl._PROBE_FAILED


def _facade_delegate(implementation: Any, *args: Any, **kwargs: Any):
    """Keep compatibility adapters on one auditable delegation spine."""

    return implementation(*args, **kwargs)


def _source_coordinates(
    source_path: str,
    source_line: int,
    source_sha256: str,
    source_file_sha256: str | None = None,
) -> SourceCoordinates:
    return SourceCoordinates(
        source_path,
        source_line,
        source_sha256,
        source_file_sha256,
    )


def _trajectory_preference(record: dict[str, Any]) -> tuple[Any, str, str, str]:
    return _facade_delegate(
        _preferences_impl._trajectory_preference,
        record,
        curate_trajectory_preferences,
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


_container_calibration_id_candidates = (
    _identity_impl._container_calibration_id_candidates
)
_owner_calibration_id_candidates = _identity_impl._owner_calibration_id_candidates
_calibration_id_candidates = _identity_impl._calibration_id_candidates
_is_bridge_order_only_rejection = _identity_impl._is_bridge_order_only_rejection
_is_coding_step_only_rejection = _identity_impl._is_coding_step_only_rejection
_source_preference_shape = _identity_impl._source_preference_shape
_identity_stage_evidence = _identity_impl._identity_stage_evidence


def _bridge_order_repaired_copy(
    record: Mapping[str, Any],
    *,
    source_path: str,
    source_line: int,
    source_sha256: str,
) -> dict[str, Any] | None:
    decision: Any = _PROBE_FAILED
    with contextlib.suppress(Exception):
        decision = curate_bridge.curate_record(
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
        curated, _manifest = curate_coding.curate_episode(
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
    curation = _preferences_impl.SideCuration(
        None,
        side_curation,
        tuple(side_curation_reasons),
        side_curation_changed,
    )
    failure = _preferences_impl.SideFailure(
        side_kinds,
        classification,
        stage_extra.pop("schema", None),
        stage_extra,
    )
    return _facade_delegate(
        _preferences_impl._side_curation_failed_decision,
        stages,
        curation,
        failure,
    )


def _preference_context(source_path: str, source_line: int) -> RecordContext:
    return RecordContext(
        _source_coordinates(source_path, source_line, ""),
        trajectory_preferences=curate_trajectory_preferences,
    )


def _preference_with_context(implementation: Any, arguments: tuple[Any, ...]):
    current, stages, context, side_kinds = arguments
    inputs = (current, stages, context)
    if side_kinds is None:
        return _facade_delegate(implementation, *inputs)
    return _facade_delegate(implementation, *inputs, side_kinds)


def _compose_same_state_preference(
    current: dict[str, Any],
    side_kinds: tuple[str, str],
    stages: list[dict[str, Any]],
    *,
    source_path: str,
    source_line: int,
) -> "ComposeDecision | tuple[Any, list[str]]":
    return _preference_with_context(
        _preferences_impl._compose_same_state_preference,
        (
            current,
            stages,
            _preference_context(source_path, source_line),
            side_kinds,
        ),
    )


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
    return _preference_with_context(
        _preferences_impl._compose_episode_preference,
        (
            current,
            stages,
            _preference_context(source_path, source_line),
            side_kinds,
        ),
    )


def _compose_legacy_preference(
    current: dict[str, Any],
    side_kinds: tuple[str, str],
    stages: list[dict[str, Any]],
) -> tuple[Any, list[str]]:
    return _facade_delegate(
        _preferences_impl._compose_legacy_preference,
        current,
        stages,
        side_kinds,
    )


def _compose_preferences_stage(
    current: dict[str, Any],
    stages: list[dict[str, Any]],
    *,
    source_path: str,
    source_line: int,
) -> "ComposeDecision | dict[str, Any]":
    return _preference_with_context(
        _preferences_impl._compose_preferences_stage,
        (
            current,
            stages,
            _preference_context(source_path, source_line),
            None,
        ),
    )


_coding_lane_curator = _coding_impl._coding_lane_curator
_append_coding_lane_stage = _coding_impl._append_coding_lane_stage
_bridge_view_trajectory = _coding_impl._bridge_view_trajectory


def _compose_bridge_view_coding(
    current: dict[str, Any],
    trajectory: dict[str, Any],
    stages: list[dict[str, Any]],
    *,
    source_path: str,
    source_line: int,
) -> "ComposeDecision | dict[str, Any]":
    return _facade_delegate(
        _coding_impl._compose_bridge_view_coding,
        current,
        trajectory,
        stages,
        RecordContext(_source_coordinates(source_path, source_line, "")),
    )


_hidden_only_curation_applies = _coding_impl._hidden_only_curation_applies


def _compose_coding_stage(
    current: dict[str, Any],
    registered_kind: Any,
    stages: list[dict[str, Any]],
    *,
    source_path: str,
    source_line: int,
    source_sha256: str,
) -> "ComposeDecision | dict[str, Any]":
    return _facade_delegate(
        _coding_impl._compose_coding_stage,
        current,
        registered_kind,
        stages,
        RecordContext(
            _source_coordinates(source_path, source_line, source_sha256)
        ),
    )


def _compose_rewards_stage(
    current: dict[str, Any],
    stages: list[dict[str, Any]],
    *,
    source_path: str,
    source_line: int,
    calibration: Any,
) -> "ComposeDecision | tuple[dict[str, Any], dict[str, Any] | None]":
    return _facade_delegate(
        _coding_impl._compose_rewards_stage,
        current,
        stages,
        RecordContext(
            _source_coordinates(source_path, source_line, ""),
            calibration,
        ),
    )


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
    )
    return _facade_delegate(_compose_source_line_impl, physical_line, context)


_identity_owner = _source_impl._identity_owner
_json_pointer_tokens = _source_impl._json_pointer_tokens
_pop_json_pointer = _source_impl._pop_json_pointer
_original_id_paths = _source_impl._original_id_paths
_mapped_legacy_id_paths = _source_impl._mapped_legacy_id_paths
_semantic_identity_owners = _source_impl._semantic_identity_owners
_identity_stage_detail_of = _source_impl._identity_stage_detail_of
_strip_assigned_ids = _source_impl._strip_assigned_ids
_strip_provenance_labels = _source_impl._strip_provenance_labels
_strip_sidecar_binding = _source_impl._strip_sidecar_binding


def _post_transform_semantic_sha256(decision: ComposeDecision) -> str:
    context = SourceLineContext("", 0, "", canonical_sha256=_canonical_sha256)
    return _facade_delegate(
        _source_impl._post_transform_semantic_sha256, decision, context
    )


def _deduplicate_curated_record(
    decision: ComposeDecision,
    *,
    source_path: str,
    source_line: int,
    seen_curated_semantics: MutableMapping[str, tuple[str, int]] | None,
) -> ComposeDecision:
    context = SourceLineContext(
        source_path,
        source_line,
        "",
        seen_curated_semantics=seen_curated_semantics,
        canonical_sha256=_canonical_sha256,
    )
    return _facade_delegate(
        _source_impl._deduplicate_curated_record, decision, context
    )


_excluded_source_line = _source_impl._excluded_source_line


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
        path = _source_member_path(
            resolved_source, relative, f"compose source {relative}"
        )
        factory, verified = factory_identity_for_path(resolved_source, path)
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


def _audit_records(records_dir: Path, record_count: int) -> dict[str, Any]:
    """Compatibility boundary for the compact strict audit."""

    return _facade_delegate(
        _audit_records_impl, records_dir, record_count, _calibration_services()
    )


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


mill_quarantined_decision = _mill_quarantined_decision_impl


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


def main(argv: list[str] | None = None) -> int:
    """Run the stable compose CLI."""

    errors = (
        ComposeError,
        curate_identity.IdentityCurationError,
        curate_rewards.RewardOntologyError,
        TransactionError,
        OSError,
    )
    return _facade_delegate(
        _main_impl,
        argv,
        ComposeCliServices(_run_services(), errors),
        _run_hooks(),
    )


_ComposeRunState = ComposeRunState
_jsonl_physical_lines = jsonl_physical_lines

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
