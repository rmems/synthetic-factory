#!/usr/bin/env python3
"""Transactional orchestration supplied with facade-owned call boundaries.

The run coordinates and services, the per-line framing and manifest
accounting, and the destination artifacts live in the
``compose_curated_run_context``, ``compose_curated_run_lines``, and
``compose_curated_run_artifacts`` siblings; this module keeps the orchestration
that ``default_run_hooks`` resolves and re-exports every sibling name.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any, Callable, Mapping

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("compose_curated_run")
    from . import compose_contract as _contract
    from . import compose_curated_run_artifacts as _artifacts
    from . import compose_curated_run_context as _run_context
    from . import compose_curated_run_lines as _lines
    from .compose_curated_calibration import CalibrationContext
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "compose_curated_run"
    )
    import compose_contract as _contract
    import compose_curated_run_artifacts as _artifacts
    import compose_curated_run_context as _run_context
    import compose_curated_run_lines as _lines
    from compose_curated_calibration import CalibrationContext

ACTION_RETAINED = _contract.ACTION_RETAINED
MANIFEST_DIRNAME = _contract.MANIFEST_DIRNAME
RECORDS_DIRNAME = _contract.RECORDS_DIRNAME
ComposeError = _contract.ComposeError
canonical_json = _contract.canonical_json
published_source_coordinate = _contract.published_source_coordinate
published_source_snapshot = _contract.published_source_snapshot
sha256_hex = _contract.sha256_hex
ComposeCliServices = _run_context.ComposeCliServices
ComposeRunContext = _run_context.ComposeRunContext
ComposeRunHooks = _run_context.ComposeRunHooks
ComposeRunServices = _run_context.ComposeRunServices
ComposeRunState = _run_context.ComposeRunState
DestinationServices = _run_context.DestinationServices
PhysicalSourceLine = _run_context.PhysicalSourceLine
ReportServices = _run_context.ReportServices
RetainedLineContext = _run_context.RetainedLineContext
SourceBatchContext = _run_context.SourceBatchContext
SourceFileContext = _run_context.SourceFileContext
SourceLineContext = _run_context.SourceLineContext
SourceServices = _run_context.SourceServices
SummaryCommitContext = _run_context.SummaryCommitContext
SummaryContext = _run_context.SummaryContext
TransactionContext = _run_context.TransactionContext
_account_lane_actions = _lines._account_lane_actions
_line_decision = _lines._line_decision
_without_terminal_cr = _lines._without_terminal_cr
claim_output_id = _lines.claim_output_id
jsonl_physical_lines = _lines.jsonl_physical_lines
mill_quarantined_decision = _lines.mill_quarantined_decision
new_manifest_entry = _lines.new_manifest_entry
record_excluded_line = _lines.record_excluded_line
record_retained_line = _lines.record_retained_line
_summary_counts = _artifacts._summary_counts
authenticate_composed_artifacts = _artifacts.authenticate_composed_artifacts
commit_compose_summary = _artifacts.commit_compose_summary
compose_run_summary = _artifacts.compose_run_summary
write_compose_provenance = _artifacts.write_compose_provenance
write_emitted_records = _artifacts.write_emitted_records


CLI_DESCRIPTION = __doc__.split("\n\n")[0]
_published_source_coordinate = published_source_coordinate


def compose_one_line(
    state: ComposeRunState,
    source_line: PhysicalSourceLine,
    services: SourceServices,
    hooks: ComposeRunHooks | None = None,
) -> None:
    active = hooks or default_run_hooks()
    physical_line = source_line.payload
    context = source_line.context
    state.counts["source_records"] += 1
    entry = active.new_manifest_entry(context, sha256_hex(physical_line))
    decision = _line_decision(state, source_line, services, active)
    entry.update(
        {
            "action": decision.action,
            "reason_codes": list(decision.reason_codes),
            "stages": [dict(stage) for stage in decision.stages],
        }
    )
    _account_lane_actions(state, decision)
    retained = decision.action == ACTION_RETAINED and decision.record is not None
    if retained:
        retained_context = RetainedLineContext(
            entry,
            context.relative,
            f"{context.relative}:{context.line_number}",
            context.emitted,
        )
        active.record_retained_line(state, decision, retained_context)
    else:
        active.record_excluded_line(state, decision, entry)
    state.manifest_lines.append(canonical_json(entry))


def compose_source_file(
    state: ComposeRunState,
    context: SourceFileContext,
    services: ComposeRunServices,
    hooks: ComposeRunHooks | None = None,
) -> None:
    active = hooks or default_run_hooks()
    source_file_sha256 = sha256_hex(context.raw_file)
    state.counts["source_files"] += 1
    emitted: list[str] = []
    for line_number, physical_line in enumerate(active.jsonl_physical_lines(context.raw_file), 1):
        if not physical_line.strip():
            state.counts["blank_lines"] += 1
            continue
        line_context = SourceLineContext(
            context.relative,
            line_number,
            source_file_sha256,
            context.catalog,
            emitted,
            context.mill_findings,
        )
        active.compose_one_line(
            state,
            PhysicalSourceLine(physical_line, line_context),
            services.source,
            active,
        )
    if emitted:
        active.write_emitted_records(state, context, emitted, services.destination)


def captured_source_payloads(
    resolved_source: Path,
    source_members: tuple[str, ...],
    read_exact_regular_file: Callable[..., tuple[Path, bytes]],
) -> dict[str, bytes]:
    return {
        relative: read_exact_regular_file(resolved_source, relative, f"compose source {relative}")[
            1
        ]
        for relative in source_members
    }


def capture_source_snapshot(
    resolved_source: Path, services: SourceServices
) -> tuple[tuple[str, ...], dict[str, bytes], dict[str, tuple[str, bool]]]:
    source_members = services.source_jsonl_members(resolved_source)
    identities = services.source_snapshot_identities(resolved_source, source_members)
    payloads = services.captured_source_payloads(resolved_source, source_members)
    if services.source_jsonl_members(resolved_source) != source_members:
        raise ComposeError("source member set changed while capturing the source snapshot")
    current = services.source_snapshot_identities(resolved_source, source_members)
    if current != identities:
        raise ComposeError("source member identity changed while capturing the source snapshot")
    factory_identities = {
        relative: (factory, verified)
        for relative, (_file_identity, factory, verified) in identities.items()
    }
    return source_members, payloads, factory_identities


def _write_source_members(
    state: ComposeRunState,
    context: SourceBatchContext,
    services: ComposeRunServices,
    hooks: ComposeRunHooks,
) -> None:
    for relative in context.source_members:
        source_context = SourceFileContext(
            relative,
            context.payload_by_member[relative],
            context.destination_target,
            context.catalog,
            context.mill_findings,
        )
        hooks.compose_source_file(state, source_context, services)


def _write_transaction(
    state: ComposeRunState,
    context: TransactionContext,
    services: ComposeRunServices,
    hooks: ComposeRunHooks,
) -> dict[str, Any]:
    pinned_destination = context.pinned_destination
    destination_target = pinned_destination
    services.destination.create_pinned_new_directory(
        destination_target, RECORDS_DIRNAME, "destination"
    )
    services.destination.create_pinned_new_directory(
        destination_target, MANIFEST_DIRNAME, "destination"
    )
    member_context = SourceBatchContext(
        context.source_members,
        context.payload_by_member,
        destination_target,
        context.catalog,
        context.mill_findings,
    )
    _write_source_members(state, member_context, services, hooks)
    manifest_sha256, sidecar_sha256 = hooks.write_compose_provenance(
        state, destination_target, services.destination
    )
    summary_context = SummaryContext(
        context.resolved_source,
        pinned_destination.path,
        context.calibration_descriptor,
        len(context.catalog),
        manifest_sha256,
        sidecar_sha256,
        pinned_destination.root / RECORDS_DIRNAME,
    )
    summary = hooks.compose_run_summary(state, summary_context, services.report)
    commit_context = SummaryCommitContext(
        pinned_destination,
        summary,
        manifest_sha256,
        sidecar_sha256,
    )
    hooks.commit_compose_summary(state, commit_context, services.destination)
    return summary


def compose_run(
    context: ComposeRunContext,
    services: ComposeRunServices,
    hooks: ComposeRunHooks | None = None,
) -> dict[str, Any]:
    active = hooks or default_run_hooks()
    resolved_source = services.source.require_exact_directory(context.source_run, "source run")
    source_members, payload_by_member, identities = active.capture_source_snapshot(
        resolved_source, services.source
    )
    source_members, payload_by_member, identities = published_source_snapshot(
        source_members,
        payload_by_member,
        identities,
    )
    mill_findings = services.source.index_compose_mills(
        payload_by_member, identities, active.jsonl_physical_lines
    )
    catalog, calibration_descriptor = services.report.load_calibration(
        CalibrationContext(resolved_source, context.units_migration)
    )
    pinned_destination = services.destination.create_pinned_destination(
        resolved_source, context.destination
    )
    state = ComposeRunState()
    transaction = TransactionContext(
        pinned_destination,
        resolved_source,
        source_members,
        payload_by_member,
        mill_findings,
        catalog,
        calibration_descriptor,
    )
    try:
        summary = _write_transaction(state, transaction, services, active)
    except BaseException:
        pinned_destination.cleanup()
        raise
    pinned_destination.finish()
    return summary


def default_run_hooks() -> ComposeRunHooks:
    """Return the split module's native call graph for direct consumers."""

    return ComposeRunHooks(
        new_manifest_entry,
        claim_output_id,
        record_retained_line,
        record_excluded_line,
        mill_quarantined_decision,
        compose_one_line,
        write_emitted_records,
        compose_source_file,
        capture_source_snapshot,
        write_compose_provenance,
        authenticate_composed_artifacts,
        compose_run_summary,
        commit_compose_summary,
        jsonl_physical_lines,
    )


def facade_run_services(
    facade: Any, index_compose_mills: Callable[..., Mapping[tuple[str, int], Any]]
) -> ComposeRunServices:
    """Resolve facade services after the core module has initialized."""

    if __package__:
        from .compose_curated_run_facade import facade_run_services as implementation
    else:
        from compose_curated_run_facade import facade_run_services as implementation
    return implementation(facade, index_compose_mills)


def facade_run_hooks(facade: Any) -> ComposeRunHooks:
    """Resolve facade hooks after the core module has initialized."""

    if __package__:
        from .compose_curated_run_facade import facade_run_hooks as implementation
    else:
        from compose_curated_run_facade import facade_run_hooks as implementation
    return implementation(facade)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse the public CLI arguments without an import-time support cycle."""

    if __package__:
        from .compose_curated_run_cli import parse_args as implementation
    else:
        from compose_curated_run_cli import parse_args as implementation
    return implementation(argv)


def main(
    argv: list[str] | None,
    services: ComposeCliServices,
    hooks: ComposeRunHooks | None = None,
) -> int:
    """Run the public CLI without an import-time support cycle."""

    if __package__:
        from .compose_curated_run_cli import main as implementation
    else:
        from compose_curated_run_cli import main as implementation
    return implementation(argv, services, hooks)


__all__ = """
CLI_DESCRIPTION ComposeCliServices ComposeRunContext ComposeRunHooks
ComposeRunServices ComposeRunState DestinationServices PhysicalSourceLine
ReportServices RetainedLineContext SourceBatchContext SourceFileContext
SourceLineContext SourceServices SummaryCommitContext SummaryContext
TransactionContext _account_lane_actions _line_decision
_published_source_coordinate _summary_counts _without_terminal_cr
_write_source_members _write_transaction authenticate_composed_artifacts
capture_source_snapshot captured_source_payloads claim_output_id
commit_compose_summary compose_one_line compose_run compose_run_summary
compose_source_file default_run_hooks facade_run_hooks facade_run_services
jsonl_physical_lines main mill_quarantined_decision new_manifest_entry
parse_args record_excluded_line record_retained_line write_compose_provenance
write_emitted_records
""".split()


if __package__:
    _expose_package_sibling(__name__)
