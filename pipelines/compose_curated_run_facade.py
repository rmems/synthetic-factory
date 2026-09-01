#!/usr/bin/env python3
"""Live compatibility bindings for the composed-run transaction facade."""

from __future__ import annotations

from typing import Any, Callable, Mapping

if __package__:
    from .compose_curated_run_bootstrap import (
        ComposeRunHooks,
        ComposeRunServices,
        DestinationServices,
        ReportServices,
        SourceServices,
        expose_run_adapter,
    )
else:
    from compose_curated_run_bootstrap import (
        ComposeRunHooks,
        ComposeRunServices,
        DestinationServices,
        ReportServices,
        SourceServices,
        expose_run_adapter,
    )


def facade_run_services(
    facade: Any, index_compose_mills: Callable[..., Mapping[tuple[str, int], Any]]
) -> ComposeRunServices:
    """Resolve one transaction's collaborators from the live facade namespace."""

    return ComposeRunServices(
        SourceServices(
            facade._require_exact_directory,
            facade.source_jsonl_members,
            facade._captured_source_payloads,
            facade._source_snapshot_identities,
            index_compose_mills,
            facade.compose_source_line,
        ),
        DestinationServices(
            facade.create_pinned_destination,
            facade._create_pinned_new_directory,
            facade._write_new_text,
            facade._read_exact_regular_file,
        ),
        ReportServices(
            lambda context: facade._load_calibration(context.source_run, context.units_migration),
            facade._audit_records,
            facade.transform_contract,
        ),
    )


def _line_hooks(facade: Any) -> tuple[Callable[..., Any], ...]:
    return (
        lambda context, digest: facade._new_manifest_entry(
            context.relative, context.line_number, digest, context.source_file_sha256
        ),
        facade._claim_output_id,
        lambda state, decision, context: facade._record_retained_line(
            state,
            decision,
            context.entry,
            relative=context.relative,
            location=context.location,
            emitted=context.emitted,
        ),
        facade._record_excluded_line,
        facade.mill_quarantined_decision,
        lambda state, source_line, _services, _hooks: facade._compose_one_line(
            state,
            source_line.payload,
            relative=source_line.context.relative,
            line_number=source_line.context.line_number,
            source_file_sha256=source_line.context.source_file_sha256,
            catalog=source_line.context.catalog,
            emitted=source_line.context.emitted,
            mill_findings=source_line.context.mill_findings,
        ),
    )


def _source_hooks(facade: Any) -> tuple[Callable[..., Any], ...]:
    return (
        lambda state, context, emitted, _services: facade._write_emitted_records(
            state, context.destination_target, context.relative, emitted
        ),
        lambda state, context, _services: facade._compose_source_file(
            state,
            relative=context.relative,
            raw_file=context.raw_file,
            destination_target=context.destination_target,
            catalog=context.catalog,
            mill_findings=context.mill_findings,
        ),
        lambda resolved, _services: facade._capture_source_snapshot(resolved),
    )


def _finalize_hooks(facade: Any) -> tuple[Callable[..., Any], ...]:
    return (
        lambda state, destination, _services: facade._write_compose_provenance(state, destination),
        lambda pinned, expected, _services: facade._authenticate_composed_artifacts(
            pinned, expected
        ),
        lambda state, context, _services: facade._compose_run_summary(
            state,
            resolved_source=context.resolved_source,
            destination_path=context.destination_path,
            calibration_descriptor=context.calibration_descriptor,
            calibrated_records=context.calibrated_records,
            manifest_sha256=context.manifest_sha256,
            sidecar_sha256=context.sidecar_sha256,
            records_dir=context.records_dir,
        ),
        lambda state, context, _services: facade._commit_compose_summary(
            state,
            context.pinned_destination,
            context.summary,
            context.manifest_sha256,
            context.sidecar_sha256,
        ),
    )


def facade_run_hooks(facade: Any) -> ComposeRunHooks:
    """Build hooks that preserve every historical facade monkeypatch seam."""

    return ComposeRunHooks(
        *_line_hooks(facade),
        *_source_hooks(facade),
        *_finalize_hooks(facade),
        facade.jsonl_physical_lines,
    )


expose_run_adapter(__name__)
