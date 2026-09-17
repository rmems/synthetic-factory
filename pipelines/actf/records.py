#!/usr/bin/env python3
"""Assemble per-version ACTF AST-extraction records. No recovered mill is copied."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import ast_scan as scan
from . import lineage as lin
from . import vocabulary as cv
from ._contract import bind_import_twin, is_under_raw

__all__ = [
    "ExtractedRecord",
    "scan_lineage",
    "scan_recovery_tree",
    "summarize",
]


@dataclass(frozen=True)
class ExtractedRecord:
    """One lineage version (or one unrecoverable lineage exclusion)."""

    path_key: str
    version_label: str | None
    version_id: str | None
    classification: str
    syntax_status: str
    source_sha256: str | None
    features: dict[str, Any] | None
    operations: tuple[dict[str, Any], ...]
    excluded: bool
    reason: str | None
    original_path: str

    def as_mapping(self) -> dict[str, Any]:
        return {
            "family": cv.FAMILY,
            "corpus": cv.CORPUS,
            "record_kind": cv.RECORD_KIND,
            "path_key": self.path_key,
            "version_label": self.version_label,
            "version_id": self.version_id,
            "classification": self.classification,
            "syntax_status": self.syntax_status,
            "source_sha256": self.source_sha256,
            "features": self.features,
            "operations": list(self.operations),
            "excluded": self.excluded,
            "reason": self.reason,
            "original_path": self.original_path,
        }


def _unrecoverable(lineage: lin.Lineage) -> ExtractedRecord:
    return ExtractedRecord(
        path_key=lineage.path_key,
        version_label=None,
        version_id=None,
        classification=lineage.classification,
        syntax_status="",
        source_sha256=None,
        features=None,
        operations=(),
        excluded=True,
        reason=cv.REASON_UNRECOVERABLE_LINEAGE,
        original_path=lineage.original_path,
    )


def _from_scan(lineage: lin.Lineage, version: lin.VersionRef, result: scan.ScanResult) -> ExtractedRecord:
    reason = result.excluded_reason
    if reason == cv.REASON_SYNTAX_ERROR and result.syntax_error and "UTF-8" in result.syntax_error:
        reason = cv.REASON_SOURCE_UNREADABLE
    return ExtractedRecord(
        path_key=lineage.path_key,
        version_label=version.version_label,
        version_id=version.version_id,
        classification=lineage.classification,
        syntax_status=result.syntax_status,
        source_sha256=result.source_sha256 or None,
        features=None if result.features is None else result.features.as_mapping(),
        operations=tuple(item.as_mapping() for item in result.operations),
        excluded=reason is not None,
        reason=reason,
        original_path=lineage.original_path,
    )


def scan_lineage(lineage: lin.Lineage) -> tuple[ExtractedRecord, ...]:
    """Scan every version of one lineage. Unrecoverable lineages yield one exclusion."""

    if not lineage.is_recoverable:
        return (_unrecoverable(lineage),)
    if not lineage.versions:
        return (_unrecoverable(lineage),)
    return tuple(_from_scan(lineage, version, scan.scan_version(version)) for version in lineage.versions)


def scan_recovery_tree(recovery_root: Path) -> tuple[ExtractedRecord, ...]:
    """Walk the recover-grok ACTF family. Refuses a root under ``outputs/raw/``."""

    root = Path(recovery_root)
    cv.refuse_vendor_destination(root)
    cv.refuse_when(
        is_under_raw(root),
        cv.FINDING_RECOVERY_ROOT_UNDER_RAW,
        f"recovery root names the immutable raw tree: {cv.shown(str(root))}",
    )
    records: list[ExtractedRecord] = []
    for lineage in lin.read_recovery_tree(root):
        records.extend(scan_lineage(lineage))
    return tuple(records)


def summarize(records: tuple[ExtractedRecord, ...] | list[ExtractedRecord]) -> dict[str, Any]:
    """Exact-JSON summary of an AST extraction pass."""

    classification = Counter(record.classification for record in records)
    syntax = Counter(record.syntax_status for record in records if record.syntax_status)
    operations = Counter(
        finding["category"]
        for record in records
        for finding in record.operations
    )
    exclusions = Counter(record.reason for record in records if record.excluded and record.reason)
    return {
        "family": cv.FAMILY,
        "corpus": cv.CORPUS,
        "factory": cv.FACTORY,
        "recovery_session": cv.RECOVERY_SESSION,
        "lineages": len({record.path_key for record in records}),
        "records": len(records),
        "excluded": sum(1 for record in records if record.excluded),
        "by_classification": dict(sorted(classification.items())),
        "by_syntax_status": dict(sorted(syntax.items())),
        "by_operation_category": dict(sorted(operations.items())),
        "exclusions": dict(sorted(exclusions.items())),
    }


bind_import_twin(__name__)
