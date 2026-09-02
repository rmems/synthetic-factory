#!/usr/bin/env python3
"""Transactional orchestration supplied with facade-owned call boundaries."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Mapping

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("compose_curated_run")
    from .compose_contract import (
        ACTION_EXCLUDED,
        ACTION_RETAINED,
        COMPOSE_NAME,
        COMPOSE_VERSION,
        LANE_ORDER,
        MANIFEST_DIRNAME,
        MANIFEST_FILENAME,
        RECORDS_DIRNAME,
        REWARD_SIDECAR_FILENAME,
        SUMMARY_FILENAME,
        ComposeDecision,
        ComposeError,
        canonical_json,
        published_source_coordinate,
        published_source_snapshot,
        sha256_hex,
    )
    from .compose_curated_calibration import CalibrationContext
    from .compose_curated_context import SemanticRegistry, SourceLineCoordinate
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "compose_curated_run"
    )
    from compose_contract import (
        ACTION_EXCLUDED,
        ACTION_RETAINED,
        COMPOSE_NAME,
        COMPOSE_VERSION,
        LANE_ORDER,
        MANIFEST_DIRNAME,
        MANIFEST_FILENAME,
        RECORDS_DIRNAME,
        REWARD_SIDECAR_FILENAME,
        SUMMARY_FILENAME,
        ComposeDecision,
        ComposeError,
        canonical_json,
        published_source_coordinate,
        published_source_snapshot,
        sha256_hex,
    )
    from compose_curated_calibration import CalibrationContext
    from compose_curated_context import SemanticRegistry, SourceLineCoordinate


CLI_DESCRIPTION = __doc__.split("\n\n")[0]
_published_source_coordinate = published_source_coordinate


@dataclass(frozen=True)
class ComposeRunContext:
    source_run: Path
    destination: Path
    units_migration: Path | None = None


@dataclass(frozen=True)
class SourceServices:
    require_exact_directory: Callable[[Path, str], Path]
    source_jsonl_members: Callable[[Path], tuple[str, ...]]
    captured_source_payloads: Callable[[Path, tuple[str, ...]], dict[str, bytes]]
    source_snapshot_identities: Callable[..., dict[str, tuple[tuple[int, ...], str, bool]]]
    index_compose_mills: Callable[..., Mapping[tuple[str, int], Any]]
    compose_source_line: Callable[..., ComposeDecision]


@dataclass(frozen=True)
class DestinationServices:
    create_pinned_destination: Callable[[Path, Path], Any]
    create_pinned_new_directory: Callable[[Any, str, str], None]
    write_new_text: Callable[[Any, str, str], str]
    read_exact_regular_file: Callable[..., tuple[Path, bytes]]


@dataclass(frozen=True)
class ReportServices:
    load_calibration: Callable[..., tuple[dict[str, Any], dict[str, Any]]]
    audit_records: Callable[[Path, int], dict[str, Any]]
    transform_contract: Callable[[], dict[str, Any]]


@dataclass(frozen=True)
class ComposeRunServices:
    source: SourceServices
    destination: DestinationServices
    report: ReportServices


@dataclass(frozen=True)
class ComposeRunHooks:
    """Facade-owned orchestration seams resolved for one compose invocation."""

    new_manifest_entry: Callable[..., dict[str, Any]]
    claim_output_id: Callable[..., None]
    record_retained_line: Callable[..., None]
    record_excluded_line: Callable[..., None]
    mill_quarantined_decision: Callable[[Any], ComposeDecision]
    compose_one_line: Callable[..., None]
    write_emitted_records: Callable[..., None]
    compose_source_file: Callable[..., None]
    capture_source_snapshot: Callable[..., Any]
    write_compose_provenance: Callable[..., tuple[str, str]]
    authenticate_composed_artifacts: Callable[..., None]
    compose_run_summary: Callable[..., dict[str, Any]]
    commit_compose_summary: Callable[..., None]
    jsonl_physical_lines: Callable[[bytes], list[bytes]]


@dataclass(frozen=True)
class ComposeCliServices:
    run: ComposeRunServices
    caught_errors: tuple[type[BaseException], ...]


@dataclass(frozen=True)
class SourceLineContext:
    relative: str
    line_number: int
    source_file_sha256: str
    catalog: Mapping[str, Any] | None
    emitted: list[str]
    mill_findings: Mapping[tuple[str, int], Any] | None = None


@dataclass(frozen=True)
class PhysicalSourceLine:
    payload: bytes
    context: SourceLineContext


@dataclass(frozen=True)
class RetainedLineContext:
    entry: dict[str, Any]
    relative: str
    location: str
    emitted: list[str]


@dataclass(frozen=True)
class SourceFileContext:
    relative: str
    raw_file: bytes
    destination_target: Any
    catalog: Mapping[str, Any] | None
    mill_findings: Mapping[tuple[str, int], Any] | None = None


@dataclass(frozen=True)
class SummaryContext:
    resolved_source: Path
    destination_path: Path
    calibration_descriptor: Any
    calibrated_records: int
    manifest_sha256: str
    sidecar_sha256: str
    records_dir: Path


@dataclass(frozen=True)
class SourceBatchContext:
    source_members: tuple[str, ...]
    payload_by_member: Mapping[str, bytes]
    destination_target: Any
    catalog: Mapping[str, Any]
    mill_findings: Mapping[tuple[str, int], Any]


@dataclass(frozen=True)
class TransactionContext:
    pinned_destination: Any
    resolved_source: Path
    source_members: tuple[str, ...]
    payload_by_member: Mapping[str, bytes]
    mill_findings: Mapping[tuple[str, int], Any]
    catalog: Mapping[str, Any]
    calibration_descriptor: Mapping[str, Any]


@dataclass(frozen=True)
class SummaryCommitContext:
    pinned_destination: Any
    summary: Mapping[str, Any]
    manifest_sha256: str | None = None
    sidecar_sha256: str | None = None


@dataclass
class ComposeRunState:
    counts: Counter[str] = field(default_factory=Counter)
    exclusions: Counter[str] = field(default_factory=Counter)
    lane_actions: dict[str, Counter[str]] = field(
        default_factory=lambda: {lane: Counter() for lane in LANE_ORDER}
    )
    manifest_lines: list[str] = field(default_factory=list)
    sidecar_lines: list[str] = field(default_factory=list)
    outputs: list[dict[str, Any]] = field(default_factory=list)
    emitted_ids: dict[str, str] = field(default_factory=dict)
    seen_source_semantics: dict[str, tuple[str, int]] = field(default_factory=dict)
    seen_curated_semantics: dict[str, tuple[str, int]] = field(default_factory=dict)


def jsonl_physical_lines(raw_file: bytes) -> list[bytes]:
    physical_lines = raw_file.split(b"\n")
    terminated_lines = len(physical_lines) - 1
    if physical_lines and physical_lines[-1] == b"":
        physical_lines.pop()
    framed = min(terminated_lines, len(physical_lines))
    physical_lines[:framed] = map(_without_terminal_cr, physical_lines[:framed])
    return physical_lines


def _without_terminal_cr(physical_line: bytes) -> bytes:
    """Remove JSONL framing's CR only when the line ended in CRLF."""

    return physical_line[:-1] if physical_line.endswith(b"\r") else physical_line


def new_manifest_entry(context: SourceLineContext, source_sha256: str) -> dict[str, Any]:
    return {
        "compose_name": COMPOSE_NAME,
        "compose_version": COMPOSE_VERSION,
        "lane_order": list(LANE_ORDER),
        "source_path": context.relative,
        "source_line": context.line_number,
        "source_sha256": source_sha256,
        "source_file_sha256": context.source_file_sha256,
    }


def claim_output_id(state: ComposeRunState, output_id: Any, location: str) -> None:
    if output_id is None:
        return
    previous = state.emitted_ids.get(output_id)
    if previous is not None:
        raise ComposeError(f"canonical ID collision {output_id!r}: {previous} and {location}")
    state.emitted_ids[output_id] = location


def record_retained_line(
    state: ComposeRunState,
    decision: ComposeDecision,
    context: RetainedLineContext,
    claim_output_id_fn: Callable[..., None] = claim_output_id,
) -> None:
    line = canonical_json(decision.record)
    claim_output_id_fn(state, decision.output_id, context.location)
    context.emitted.append(line)
    context.entry.update(
        {
            "output_path": f"{RECORDS_DIRNAME}/{context.relative}",
            "output_line": len(context.emitted),
            "output_id": decision.output_id,
            "output_sha256": sha256_hex(line.encode("utf-8")),
        }
    )
    state.counts["retained"] += 1
    if decision.reward_sidecar is not None:
        context.entry["reward_sidecar_id"] = decision.reward_sidecar["sidecar_id"]
        state.sidecar_lines.append(canonical_json(decision.reward_sidecar))


def record_excluded_line(
    state: ComposeRunState, decision: ComposeDecision, entry: dict[str, Any]
) -> None:
    entry.update(
        {
            "output_path": None,
            "output_line": None,
            "output_id": None,
            "output_sha256": None,
        }
    )
    state.counts["excluded"] += 1
    for reason in decision.reason_codes or ("compose.unspecified",):
        state.exclusions[reason] += 1


def mill_quarantined_decision(finding: Any) -> ComposeDecision:
    reasons = list(finding.reason_codes)
    stage = {
        "lane": "source",
        "transform_name": COMPOSE_NAME,
        "transform_version": COMPOSE_VERSION,
        "action": ACTION_EXCLUDED,
        "reason_codes": reasons,
        "classification": "foreign_mill_quarantined",
        "detail": finding.as_dict(),
    }
    return ComposeDecision(
        ACTION_EXCLUDED,
        None,
        tuple(reasons),
        (stage,),
        None,
        None,
    )


def _line_decision(
    state: ComposeRunState,
    source_line: PhysicalSourceLine,
    services: SourceServices,
    hooks: ComposeRunHooks,
) -> ComposeDecision:
    context = source_line.context
    finding = None
    if context.mill_findings is not None:
        finding = context.mill_findings.get((context.relative, context.line_number))
    if finding is not None:
        return hooks.mill_quarantined_decision(finding)
    return services.compose_source_line(
        source_line.payload,
        SourceLineCoordinate(context.relative, context.line_number, context.source_file_sha256),
        calibration_catalog=context.catalog,
        semantics=SemanticRegistry(state.seen_source_semantics, state.seen_curated_semantics),
    )


def _account_lane_actions(state: ComposeRunState, decision: ComposeDecision) -> None:
    for stage in decision.stages:
        lane = stage["lane"]
        if lane in state.lane_actions:
            state.lane_actions[lane][stage["action"]] += 1


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


def write_emitted_records(
    state: ComposeRunState,
    context: SourceFileContext,
    emitted: list[str],
    services: DestinationServices,
) -> None:
    output_path = f"{RECORDS_DIRNAME}/{context.relative}"
    digest = services.write_new_text(
        context.destination_target,
        output_path,
        "".join(line + "\n" for line in emitted),
    )
    state.outputs.append({"path": output_path, "records": len(emitted), "sha256": digest})
    state.counts["output_files"] += 1


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


def write_compose_provenance(
    state: ComposeRunState, destination_target: Any, services: DestinationServices
) -> tuple[str, str]:
    manifest_sha256 = services.write_new_text(
        destination_target,
        f"{MANIFEST_DIRNAME}/{MANIFEST_FILENAME}",
        "".join(line + "\n" for line in state.manifest_lines),
    )
    sidecar_sha256 = services.write_new_text(
        destination_target,
        f"{MANIFEST_DIRNAME}/{REWARD_SIDECAR_FILENAME}",
        "".join(line + "\n" for line in state.sidecar_lines),
    )
    return manifest_sha256, sidecar_sha256


def authenticate_composed_artifacts(
    pinned_destination: Any,
    expected_digests: Mapping[str, str],
    services: DestinationServices,
) -> None:
    pinned_destination.verify_binding()
    for relative, expected_digest in sorted(expected_digests.items()):
        _path, payload = services.read_exact_regular_file(
            pinned_destination.root,
            relative,
            f"compose artifact {relative}",
        )
        if sha256_hex(payload) != expected_digest:
            raise ComposeError(f"compose artifact {relative} changed before compose commit")
    pinned_destination.verify_binding()


def _summary_counts(state: ComposeRunState) -> dict[str, int]:
    counts = state.counts
    return {
        "source_files": counts["source_files"],
        "source_records": counts["source_records"],
        "blank_lines": counts["blank_lines"],
        "retained": counts["retained"],
        "excluded": counts["excluded"],
        "output_files": counts["output_files"],
        "reward_sidecars": len(state.sidecar_lines),
    }


def compose_run_summary(
    state: ComposeRunState,
    context: SummaryContext,
    services: ReportServices,
) -> dict[str, Any]:
    return {
        "compose_name": COMPOSE_NAME,
        "compose_version": COMPOSE_VERSION,
        "source_run": str(context.resolved_source),
        "destination": str(context.destination_path),
        "lane_order": list(LANE_ORDER),
        "transforms": services.transform_contract(),
        "calibration": context.calibration_descriptor,
        "calibrated_records": context.calibrated_records,
        "counts": _summary_counts(state),
        "lane_actions": {
            lane: dict(sorted(actions.items())) for lane, actions in state.lane_actions.items()
        },
        "exclusions": dict(sorted(state.exclusions.items())),
        "outputs": state.outputs,
        "manifest": {
            "path": f"{MANIFEST_DIRNAME}/{MANIFEST_FILENAME}",
            "entries": len(state.manifest_lines),
            "sha256": context.manifest_sha256,
        },
        "reward_sidecars": {
            "path": f"{MANIFEST_DIRNAME}/{REWARD_SIDECAR_FILENAME}",
            "entries": len(state.sidecar_lines),
            "sha256": context.sidecar_sha256,
        },
        "audit": services.audit_records(context.records_dir, state.counts["retained"]),
    }


def commit_compose_summary(
    state: ComposeRunState,
    context: SummaryCommitContext,
    services: DestinationServices,
    authenticate: Callable[..., None] = authenticate_composed_artifacts,
) -> None:
    pinned_destination = context.pinned_destination
    summary = context.summary
    summary_sha256 = services.write_new_text(
        pinned_destination,
        SUMMARY_FILENAME,
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
    )
    expected_digests = {item["path"]: item["sha256"] for item in state.outputs}
    expected_digests.update(
        {
            summary["manifest"]["path"]: (
                summary["manifest"]["sha256"]
                if context.manifest_sha256 is None
                else context.manifest_sha256
            ),
            summary["reward_sidecars"]["path"]: (
                summary["reward_sidecars"]["sha256"]
                if context.sidecar_sha256 is None
                else context.sidecar_sha256
            ),
            SUMMARY_FILENAME: summary_sha256,
        }
    )
    authenticate(pinned_destination, expected_digests, services)


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


if __package__:
    _expose_package_sibling(__name__)
