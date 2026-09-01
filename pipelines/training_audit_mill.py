#!/usr/bin/env python3
"""Shared mill-quarantine preparation for the training-readiness audit."""

import json
from pathlib import Path

from check_records import reject_json_constant
from census import factory_identity_for_path
from exact_json import parse_finite_json_float
from mill_family import MillFinding, MillIndex, summarize


def _finding_row(finding: MillFinding) -> dict:
    row = finding.as_dict()
    ref = finding.ref
    if isinstance(ref, tuple) and len(ref) == 2:
        source, line = ref
        row["source"] = str(source)
        row["line"] = line
    return row


def _index_findings(
    run_dir: Path,
    files: list[Path] | list[tuple[Path, bytes]],
):
    mills = MillIndex()
    for item in files:
        if isinstance(item, tuple):
            relative, payload = item
        else:
            path = Path(item)
            relative = path.relative_to(run_dir)
            payload = path.read_bytes()
        factory, verified = factory_identity_for_path(run_dir, run_dir / relative)
        for line_number, raw_line in enumerate(payload.split(b"\n"), 1):
            if not raw_line.strip():
                continue
            try:
                line = raw_line.decode("utf-8")
                record = json.loads(
                    line,
                    parse_constant=reject_json_constant,
                    parse_float=parse_finite_json_float,
                )
            except (ValueError, RecursionError):
                continue
            mills.add(
                factory,
                record,
                (relative.as_posix(), line_number),
                factory_verified=verified,
            )
    return mills.findings()


def index_mill_quarantine(
    run_dir: Path,
    files: list[Path] | list[tuple[Path, bytes]],
):
    """Return lookup and report views from one shared-detector pass.

    Audit callers pass the immutable ``(relative path, payload bytes)``
    snapshot. Plain paths remain accepted for compatibility with direct
    callers and are captured once before detection.
    """

    findings = _index_findings(run_dir, files)
    report = summarize(findings)
    report["quarantined_records"] = [_finding_row(item) for item in findings]
    return {item.ref: item for item in findings}, report
