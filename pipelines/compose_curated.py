#!/usr/bin/env python3
"""Compose record-level curation transforms into a new authenticated tree.

This is the stable compatibility facade. Cohesive record, source-line, and
transaction implementations live in the ``compose_curated_*`` modules; the
adapters here retain historical signatures and resolve patch seams per call.
"""

from __future__ import annotations

import argparse
import contextlib
import copy
import json
import os
import re
import sys
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, MutableMapping

if __package__:
    from . import _expose_package_sibling, _local_sibling_module, _require_local_sibling

    if _local_sibling_module("compose_curated", allow_initializing=True):
        import compose_curated as _direct_compose_curated

        _require_local_sibling(_direct_compose_curated, "compose_curated")
        del _direct_compose_curated
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
    from . import compose_contract as _contract
    from . import compose_curated_calibration as _calibration_impl
    from . import compose_curated_coding as _coding_stage_impl
    from . import compose_curated_identity as _identity_impl
    from . import compose_curated_identity_facade as _identity_facade
    from . import compose_curated_record_facade as _record_facade
    from . import compose_curated_record as _record_impl
    from . import compose_curated_run as _run_impl
    from . import compose_curated_run_facade as _run_facade
    from . import compose_destination as _destination
    from . import compose_trajectory as _trajectory
    from .check_records import reject_json_constant
    from .census import factory_identity_for_path
    from .curate_identity import _parse_finite_json_float, _reject_duplicate_object_keys
    from .record_kind import preference_side_kinds
    from .round_txn import TransactionError
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "compose_curated"
    )
    import compose_contract as _contract
    import compose_curated_calibration as _calibration_impl
    import compose_curated_coding as _coding_stage_impl
    import compose_curated_identity as _identity_impl
    import compose_curated_identity_facade as _identity_facade
    import compose_curated_record_facade as _record_facade
    import compose_curated_record as _record_impl
    import compose_curated_run as _run_impl
    import compose_curated_run_facade as _run_facade
    import compose_destination as _destination
    import compose_mill
    import compose_trajectory as _trajectory
    import curate_agentic
    import curate_bridge
    import curate_coding
    import curate_identity
    import curate_preferences
    import curate_rewards
    import training_audit
    from check_records import reject_json_constant
    from census import factory_identity_for_path
    from curate_identity import _parse_finite_json_float, _reject_duplicate_object_keys
    from record_kind import preference_side_kinds
    from round_txn import TransactionError

try:
    if __package__:
        from . import curate_trajectory_preferences
    else:
        import curate_trajectory_preferences
except ModuleNotFoundError as missing_import:
    allowed_missing = {
        "curate_trajectory_preferences",
        f"{__package__}.curate_trajectory_preferences",
    }
    if missing_import.name not in allowed_missing:
        raise
    curate_trajectory_preferences = None


def _reexport(module: Any, names: str) -> None:
    globals().update({name: getattr(module, name) for name in names.split()})


_reexport(
    _contract,
    """
    ACTION_EXCLUDED ACTION_NOT_APPLICABLE ACTION_RETAINED COMPOSE_NAME
    COMPOSE_VERSION ComposeDecision ComposeError FFPC_UNITS_MIGRATION LANE_ORDER
    MANIFEST_DIRNAME MANIFEST_FILENAME PREFERENCE_CANDIDATE_KEYS RECORDS_DIRNAME
    REASON_DUPLICATE_CURATED_RECORD REASON_DUPLICATE_SOURCE_RECORD
    REASON_EMPTY_CORPUS REASON_INVALID_JSON REASON_INVALID_UTF8
    REASON_MIXED_PREFERENCE_FAMILIES REASON_REWARD_ONTOLOGY
    REASON_TRAJECTORY_GATE_PASSED REASON_TRAJECTORY_GOAL_NORMALIZED
    REASON_TRAJECTORY_IDENTICAL REASON_TRAJECTORY_OUTCOME_MISSING
    REASON_TRAJECTORY_OUTCOME_NOT_DIVERGENT REASON_TRAJECTORY_PREFIX_ABSENT
    REASON_TRAJECTORY_REWARD_MISSING REASON_TRAJECTORY_REWARD_NOT_DIVERGENT
    REASON_TRAJECTORY_SIDE_INVALID REASON_TRAJECTORY_STEPS_EMPTY
    REASON_TRAJECTORY_STEPS_INVALID REWARD_SIDECAR_FILENAME SUMMARY_FILENAME
    TRAJECTORY_GOAL_LOCATIONS _TrajectoryPreferenceDecision _canonical_sha256
    canonical_json sha256_hex
    """,
)
_reexport(
    _destination,
    """
    PinnedDestination _assert_descriptor_contained _assert_destination_disjoint
    _assert_new_destination _assert_opened_source_identity
    _assert_source_path_unchanged _assert_unaliased_regular_member
    _collect_source_directory _contains_raw_segments _create_pinned_new_directory
    _destination_write_parts _directory_binding_matches _directory_identity
    _discard_created_destination _drain_descriptor _is_under_raw
    _open_pinned_child _open_pinned_child_directory _pinned_root_path
    _read_exact_child_file _read_exact_regular_file _read_pinned_child_bytes
    _refuse_existing_destination _require_exact_directory _scan_source_directory
    _source_entry_metadata _source_member_path _stable_file_identity
    _validated_member_relative _verify_directory_binding _verify_pinned_child
    _write_new_text create_pinned_destination source_jsonl_members
    write_pinned_new_bytes
    """,
)
_reexport(
    _trajectory,
    """
    _TRAJECTORY_DIVERGENCE_FIELDS _compat_trajectory_preference
    _curate_trajectory_sides _is_same_state_pair _mixed_preference_families
    _normalize_trajectory_goal_whitespace _present_trajectory_goals
    _strip_hidden_only_side _trajectory_divergence_reasons
    _trajectory_gate_passed _trajectory_goal_owner _trajectory_side_needs_coding
    _trajectory_side_validation_errors _trajectory_step_reasons
    _whitespace_only_goal is_bridge_record is_episode_record is_preference_record
    """,
)
ACTION_EXCLUDED = _contract.ACTION_EXCLUDED
COMPOSE_NAME = _contract.COMPOSE_NAME
COMPOSE_VERSION = _contract.COMPOSE_VERSION
ComposeDecision = _contract.ComposeDecision
ComposeError = _contract.ComposeError
PinnedDestination = _destination.PinnedDestination
TRAJECTORY_GOAL_LOCATIONS = _contract.TRAJECTORY_GOAL_LOCATIONS
_TrajectoryPreferenceDecision = _contract._TrajectoryPreferenceDecision
_facade_delegate = _record_facade._facade_delegate
_stage = _record_facade._stage
for _facade_module in (_identity_facade, _record_facade):
    for _name in _facade_module.__all__:
        globals()[_name] = getattr(_facade_module, _name)

_identity_facade.bind_facade(sys.modules[__name__])
_record_facade.bind_facade(sys.modules[__name__])
_PIPELINES = Path(__file__).resolve().parent
REASON_IDENTITY_INVALID_PAYLOAD_SHAPE = _identity_impl.REASON_IDENTITY_INVALID_PAYLOAD_SHAPE
BRIDGE_ORDER_ERROR_FRAGMENT = _identity_impl.BRIDGE_ORDER_ERROR_FRAGMENT
CODING_STEP_ERROR_RE = _identity_impl.CODING_STEP_ERROR_RE
PREFERENCE_STEP_ERROR_RE = _identity_impl.PREFERENCE_STEP_ERROR_RE
_PROBE_FAILED = _identity_impl._PROBE_FAILED
_captured_source_payloads_impl = _run_impl.captured_source_payloads
_load_calibration_impl = _calibration_impl.load_calibration
_compact_audit_report_impl = _calibration_impl.compact_audit_report
compact_audit_report = _identity_facade.compact_audit_report

CalibrationContext = _identity_facade.CalibrationContext
CalibrationServices = _identity_facade.CalibrationServices
RecordContext = _coding_stage_impl.RecordContext
RecordServices = _record_impl.RecordServices
SourceCoordinates = _identity_impl.SourceCoordinates
SourceLineContext = _identity_facade._source_impl.SourceLineContext
StageDefinition = _coding_stage_impl.StageDefinition
stage = _coding_stage_impl.stage
_only_identity_shape_details = _identity_impl._only_identity_shape_details
_calibration_services = _identity_facade._calibration_services
_record_services = _record_facade._record_services
_compose_record_from_context = _record_facade._compose_record_from_context
_compose_record_impl = _record_impl.compose_record
_compose_source_line_impl = _identity_facade._source_impl.compose_source_line
_retained_rewards_impl = _coding_stage_impl._retained_rewards
_reward_not_applicable_impl = _coding_stage_impl._reward_not_applicable
_reward_refusal_impl = _coding_stage_impl._reward_refusal
_transform_contract_impl = _identity_facade._source_impl.transform_contract
_authenticate_composed_artifacts_impl = _run_impl.authenticate_composed_artifacts
_capture_source_snapshot_impl = _run_impl.capture_source_snapshot
_claim_output_id_impl = _run_impl.claim_output_id
_commit_compose_summary_impl = _run_impl.commit_compose_summary
_compose_one_line_impl = _run_impl.compose_one_line
_compose_run_impl = _run_impl.compose_run
_compose_run_summary_impl = _run_impl.compose_run_summary
_compose_source_file_impl = _run_impl.compose_source_file
_new_manifest_entry_impl = _run_impl.new_manifest_entry
_record_excluded_line_impl = _run_impl.record_excluded_line
_record_retained_line_impl = _run_impl.record_retained_line
_write_compose_provenance_impl = _run_impl.write_compose_provenance
_write_emitted_records_impl = _run_impl.write_emitted_records
_facade_run_hooks = _run_facade.facade_run_hooks
_facade_run_services = _run_facade.facade_run_services

ComposeRunContext = _run_impl.ComposeRunContext
ComposeRunHooks = _run_impl.ComposeRunHooks
ComposeRunServices = _run_impl.ComposeRunServices
ComposeRunState = _run_impl.ComposeRunState
PhysicalSourceLine = _run_impl.PhysicalSourceLine
RetainedLineContext = _run_impl.RetainedLineContext
RunSourceLineContext = _run_impl.SourceLineContext
SourceFileContext = _run_impl.SourceFileContext
SummaryCommitContext = _run_impl.SummaryCommitContext
SummaryContext = _run_impl.SummaryContext
_ComposeRunState = ComposeRunState
_COMPATIBILITY_BINDINGS = (
    os,
    contextlib,
    copy,
    re,
    Counter,
    dataclass,
    field,
    MutableMapping,
    curate_agentic,
    curate_bridge,
    curate_coding,
    curate_preferences,
    training_audit,
    reject_json_constant,
    factory_identity_for_path,
    _parse_finite_json_float,
    _reject_duplicate_object_keys,
    preference_side_kinds,
)


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
            repaired,
            source_path,
            source_line,
            source_sha256,
        )
    )
    if retry.action == "retained" and isinstance(retry.record, dict):
        return retry
    return None


def _jsonl_physical_lines(raw_file: bytes) -> list[bytes]:
    return _run_impl.jsonl_physical_lines(raw_file)


def jsonl_physical_lines(raw_file: bytes) -> list[bytes]:
    return _facade_delegate(_jsonl_physical_lines, raw_file)


def _new_manifest_entry(
    relative: Any,
    line_number: int,
    source_sha256: str,
    source_file_sha256: str,
) -> dict[str, Any]:
    context = RunSourceLineContext(relative, line_number, source_file_sha256, None, [])
    return _facade_delegate(_new_manifest_entry_impl, context, source_sha256)


def _claim_output_id(state: _ComposeRunState, output_id: Any, location: str) -> None:
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
    return _facade_delegate(_record_retained_line_impl, state, decision, context, _claim_output_id)


def _record_excluded_line(
    state: _ComposeRunState,
    decision: ComposeDecision,
    entry: dict[str, Any],
) -> None:
    return _facade_delegate(_record_excluded_line_impl, state, decision, entry)


def mill_quarantined_decision(finding: Any) -> ComposeDecision:
    reasons = list(finding.reason_codes)
    evidence = _stage(
        "source",
        COMPOSE_NAME,
        COMPOSE_VERSION,
        ACTION_EXCLUDED,
        reason_codes=reasons,
        classification="foreign_mill_quarantined",
        detail=finding.as_dict(),
    )
    return ComposeDecision(ACTION_EXCLUDED, None, tuple(reasons), (evidence,), None, None)


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
        relative, line_number, source_file_sha256, catalog, emitted, mill_findings
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
    context = SourceFileContext(relative, raw_file, destination_target, catalog, mill_findings)
    return _facade_delegate(
        _compose_source_file_impl, state, context, _run_services(), _run_hooks()
    )


def _capture_source_snapshot(
    resolved_source: Path,
) -> tuple[tuple[str, ...], dict[str, bytes], dict[str, tuple[str, bool]]]:
    return _facade_delegate(_capture_source_snapshot_impl, resolved_source, _run_services().source)


def _write_compose_provenance(
    state: _ComposeRunState,
    destination_target: int | PinnedDestination,
) -> tuple[str, str]:
    return _facade_delegate(
        _write_compose_provenance_impl, state, destination_target, _run_services().destination
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
    return _facade_delegate(_compose_run_summary_impl, state, context, _run_services().report)


def _commit_compose_summary(
    state: _ComposeRunState,
    pinned_destination: PinnedDestination,
    summary: Mapping[str, Any],
    manifest_sha256: str,
    sidecar_sha256: str,
) -> None:
    context = SummaryCommitContext(pinned_destination, summary, manifest_sha256, sidecar_sha256)

    def authenticate(pinned, expected, _services):
        return _authenticate_composed_artifacts(pinned, expected)

    return _facade_delegate(
        _commit_compose_summary_impl, state, context, _run_services().destination, authenticate
    )


def _run_services() -> ComposeRunServices:
    return _facade_delegate(
        _facade_run_services, sys.modules[__name__], compose_mill.index_compose_mills
    )


def _run_hooks() -> ComposeRunHooks:
    return _facade_delegate(_facade_run_hooks, sys.modules[__name__])


def compose_run(
    source_run: str | Path,
    destination: str | Path,
    *,
    units_migration: str | Path | None = None,
) -> dict[str, Any]:
    context = ComposeRunContext(
        Path(source_run),
        Path(destination),
        Path(units_migration) if units_migration is not None else None,
    )
    return _facade_delegate(_compose_run_impl, context, _run_services(), _run_hooks())


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

__all__ = """
ACTION_EXCLUDED ACTION_NOT_APPLICABLE ACTION_RETAINED COMPOSE_NAME COMPOSE_VERSION
ComposeDecision ComposeError FFPC_UNITS_MIGRATION LANE_ORDER MANIFEST_DIRNAME
MANIFEST_FILENAME PREFERENCE_CANDIDATE_KEYS REASON_DUPLICATE_CURATED_RECORD
REASON_DUPLICATE_SOURCE_RECORD REASON_EMPTY_CORPUS REASON_INVALID_JSON
REASON_INVALID_UTF8 REASON_MIXED_PREFERENCE_FAMILIES REASON_REWARD_ONTOLOGY
REASON_TRAJECTORY_GATE_PASSED REASON_TRAJECTORY_GOAL_NORMALIZED
REASON_TRAJECTORY_IDENTICAL REASON_TRAJECTORY_OUTCOME_MISSING
REASON_TRAJECTORY_OUTCOME_NOT_DIVERGENT REASON_TRAJECTORY_PREFIX_ABSENT
REASON_TRAJECTORY_REWARD_MISSING REASON_TRAJECTORY_REWARD_NOT_DIVERGENT
REASON_TRAJECTORY_SIDE_INVALID REASON_TRAJECTORY_STEPS_EMPTY
REASON_TRAJECTORY_STEPS_INVALID RECORDS_DIRNAME REWARD_SIDECAR_FILENAME
SUMMARY_FILENAME TRAJECTORY_GOAL_LOCATIONS PinnedDestination
_TRAJECTORY_DIVERGENCE_FIELDS _TrajectoryPreferenceDecision
_assert_descriptor_contained _assert_destination_disjoint _assert_new_destination
_assert_opened_source_identity _assert_source_path_unchanged
_assert_unaliased_regular_member _canonical_sha256 _collect_source_directory
_compat_trajectory_preference _contains_raw_segments create_pinned_destination
_create_pinned_new_directory _curate_trajectory_sides _destination_write_parts
_directory_binding_matches _directory_identity _discard_created_destination
_drain_descriptor _is_same_state_pair _is_under_raw _mixed_preference_families
_normalize_trajectory_goal_whitespace _open_pinned_child
_open_pinned_child_directory _pinned_root_path _present_trajectory_goals
_read_exact_child_file _read_exact_regular_file _read_pinned_child_bytes
_refuse_existing_destination _require_exact_directory _scan_source_directory
_source_entry_metadata _source_member_path _stable_file_identity
_trajectory_divergence_reasons _trajectory_gate_passed _trajectory_goal_owner
_trajectory_side_needs_coding _trajectory_side_validation_errors
_trajectory_step_reasons _validated_member_relative _verify_directory_binding
_verify_pinned_child _whitespace_only_goal _write_new_text write_pinned_new_bytes
calibration_for canonical_json compose_record compose_run compose_source_line
curate_trajectory_preferences is_bridge_record is_episode_record
is_preference_record jsonl_physical_lines main parse_args sha256_hex
source_jsonl_members transform_contract
""".split()

if __package__:
    _expose_package_sibling(__name__)

if __name__ == "__main__":
    raise SystemExit(main())
