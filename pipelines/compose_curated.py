#!/usr/bin/env python3
"""Compose record-level curation transforms into a new authenticated tree.

The implementation is split by responsibility. This module remains the
stable command/API facade and resolves collaborators at call time so existing
monkeypatch seams continue to exercise the vulnerable filesystem windows.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, Mapping

_PIPELINES = Path(__file__).resolve().parent
if str(_PIPELINES) not in sys.path:
    sys.path.insert(0, str(_PIPELINES))

import compose_mill  # noqa: E402
import curate_identity  # noqa: E402
import curate_rewards  # noqa: E402
import training_audit  # noqa: E402
from check_records import reject_json_constant  # noqa: E402
from census import factory_identity_for_path  # noqa: E402
from compose_contract import (  # noqa: E402
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
from compose_curated_calibration import (  # noqa: E402
    CalibrationContext,
    CalibrationServices,
    audit_records as _audit_records_impl,
    compact_audit_report,
    load_calibration as _load_calibration_impl,
)
from compose_curated_context import RecordContext, SourceCoordinates  # noqa: E402
from compose_curated_identity import (  # noqa: E402
    BRIDGE_ORDER_ERROR_FRAGMENT,
    calibration_for,
)
from compose_curated_record import compose_record as _compose_record_impl  # noqa: E402
from compose_curated_run import (  # noqa: E402
    ComposeCliServices,
    ComposeRunContext,
    ComposeRunServices,
    ComposeRunState,
    DestinationServices,
    ReportServices,
    SourceServices,
    authenticate_composed_artifacts as _authenticate_composed_artifacts,
    captured_source_payloads as _captured_source_payloads_impl,
    claim_output_id as _claim_output_id,
    commit_compose_summary as _commit_compose_summary,
    compose_one_line as _compose_one_line,
    compose_run as _compose_run_impl,
    compose_run_summary as _compose_run_summary,
    compose_source_file as _compose_source_file,
    jsonl_physical_lines,
    main as _main_impl,
    mill_quarantined_decision,
    new_manifest_entry as _new_manifest_entry,
    parse_args,
    record_excluded_line as _record_excluded_line,
    record_retained_line as _record_retained_line,
    write_compose_provenance as _write_compose_provenance,
    write_emitted_records as _write_emitted_records,
)
from compose_curated_source import (  # noqa: E402
    SourceLineContext,
    compose_source_line as _compose_source_line_impl,
    transform_contract as _transform_contract_impl,
)
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

try:  # PR #93 is a sibling stack; use its reviewed gate when present.
    import curate_trajectory_preferences  # type: ignore[import-not-found]  # noqa: E402
except ModuleNotFoundError as missing_import:  # pragma: no cover - stack topology
    if missing_import.name != "curate_trajectory_preferences":
        raise
    curate_trajectory_preferences = None


def _required(arguments: dict[str, Any], name: str) -> Any:
    """Pop a required compatibility keyword with Python-like diagnostics."""

    try:
        return arguments.pop(name)
    except KeyError as exc:
        raise TypeError(f"missing required keyword-only argument: {name!r}") from exc


def _reject_unexpected(arguments: Mapping[str, Any], function_name: str) -> None:
    """Reject compatibility keywords not declared by the historical API."""

    if arguments:
        names = ", ".join(sorted(arguments))
        raise TypeError(f"{function_name} got unexpected keyword arguments: {names}")


def compose_record(record: Any, **arguments: Any) -> ComposeDecision:
    """Run every applicable record lane without mutating the input."""

    values = dict(arguments)
    source = SourceCoordinates(
        _required(values, "source_path"),
        _required(values, "source_line"),
        _required(values, "source_sha256"),
        values.pop("source_file_sha256", None),
    )
    context = RecordContext(
        source,
        values.pop("calibration", None),
        curate_trajectory_preferences,
    )
    _reject_unexpected(values, "compose_record")
    return _compose_record_impl(record, context)


def compose_source_line(physical_line: bytes, **arguments: Any) -> ComposeDecision:
    """Compose one exact LF-framed source line through every record lane."""

    values = dict(arguments)
    context = SourceLineContext(
        source_path=_required(values, "source_path"),
        source_line=_required(values, "source_line"),
        source_file_sha256=_required(values, "source_file_sha256"),
        calibration_catalog=values.pop("calibration_catalog", None),
        seen_source_semantics=values.pop("seen_source_semantics", None),
        seen_curated_semantics=values.pop("seen_curated_semantics", None),
        trajectory_preferences=curate_trajectory_preferences,
        canonical_sha256=_canonical_sha256,
    )
    _reject_unexpected(values, "compose_source_line")
    return _compose_source_line_impl(physical_line, context)


def transform_contract() -> dict[str, Any]:
    """Return the exact transforms written into the compose summary."""

    return _transform_contract_impl(curate_trajectory_preferences)


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

    return _captured_source_payloads_impl(
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

    return _load_calibration_impl(
        CalibrationContext(source_run, units_migration), _calibration_services()
    )


def _audit_records(records_dir: Path, record_count: int) -> dict[str, Any]:
    """Compatibility boundary for the compact strict audit."""

    return _audit_records_impl(records_dir, record_count, _calibration_services())


def _run_services() -> ComposeRunServices:
    """Resolve every historical monkeypatch seam for one transaction."""

    source = SourceServices(
        _require_exact_directory,
        source_jsonl_members,
        _captured_source_payloads,
        _source_snapshot_identities,
        compose_mill.index_compose_mills,
        compose_source_line,
    )
    destination = DestinationServices(
        create_pinned_destination,
        _create_pinned_new_directory,
        _write_new_text,
        _read_exact_regular_file,
    )
    report = ReportServices(
        lambda context: _load_calibration(
            context.source_run, context.units_migration
        ),
        _audit_records,
        transform_contract,
    )
    return ComposeRunServices(source, destination, report)


def compose_run(
    source_run: str | Path,
    destination: str | Path,
    **arguments: Any,
) -> dict[str, Any]:
    """Compose every JSONL record into a new descriptor-pinned destination."""

    values = dict(arguments)
    units = values.pop("units_migration", None)
    _reject_unexpected(values, "compose_run")
    context = ComposeRunContext(
        Path(source_run),
        Path(destination),
        Path(units) if units is not None else None,
    )
    return _compose_run_impl(context, _run_services())


def main(argv: list[str] | None = None) -> int:
    """Run the stable compose CLI."""

    errors = (
        ComposeError,
        curate_identity.IdentityCurationError,
        curate_rewards.RewardOntologyError,
        TransactionError,
        OSError,
    )
    return _main_impl(argv, ComposeCliServices(_run_services(), errors))


_ComposeRunState = ComposeRunState
_jsonl_physical_lines = jsonl_physical_lines

# These names were historically module attributes used by tests and stacked
# branches. Referencing them explicitly preserves that compatibility surface
# without widening star imports through ``__all__``.
_COMPATIBILITY_EXPORTS = (
    os,
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
