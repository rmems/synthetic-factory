#!/usr/bin/env python3
"""Frozen coordinates, services, hooks, and mutable state for one compose run."""

from __future__ import annotations

import sys
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Mapping

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("compose_curated_run_context")
    from .compose_contract import ComposeDecision, LANE_ORDER
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "compose_curated_run_context"
    )
    from compose_contract import ComposeDecision, LANE_ORDER


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


if __package__:
    _expose_package_sibling(__name__)
