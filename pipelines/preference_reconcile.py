#!/usr/bin/env python3
"""Compare two independent scans of one preference corpus.

Reconciliation answers a different question from the published audit. The
audit asks whether this scan still matches a document published earlier;
this module asks whether two copies of the same corpus, scanned separately,
reach the same verdicts from the same bytes.

The three buckets are kept apart on purpose. ``coverage`` reports records one
copy has and the other does not, ``decisions`` reports curation verdicts that
disagree, and ``payload`` reports agreeing verdicts reached from different
source bytes -- the last of which is the quiet failure a single counter
comparison would hide.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

_PIPELINES = Path(__file__).resolve().parent
if str(_PIPELINES) not in sys.path:
    sys.path.insert(0, str(_PIPELINES))

from preference_audit import (  # noqa: E402
    AUDIT_SOURCE_FILE_FIELDS,
    _location_sort_key,
    _source_files_by_path,
)
from preference_model import CurationRun  # noqa: E402

__all__ = [
    "RECONCILE_COVERAGE_KEYS",
    "RECONCILE_DECISION_FIELDS",
    "RECONCILE_PAYLOAD_FIELDS",
    "reconcile_runs",
]


RECONCILE_DECISION_FIELDS = (
    "action",
    "classification",
    "reason_codes",
    "same_state",
    "same_proposed_action",
    "context_diff_paths",
)
RECONCILE_PAYLOAD_FIELDS = ("source_sha256", "source_record_id")
RECONCILE_COVERAGE_KEYS = (
    "json_records_seen",
    "preference_records",
    "skipped_non_preference_records",
)


def _manifest_by_location(run: CurationRun) -> dict[tuple[str, int], dict[str, Any]]:
    """One scan's manifest entries keyed by source path and line."""

    return {
        (entry["source_path"], entry["source_line"]): entry for entry in run.manifest
    }


def _reconcile_summary_coverage(first: CurationRun, second: CurationRun) -> list[str]:
    """Denominator counters that disagree between two scans of one corpus."""

    return [
        f"summary.{key}: first {first.summary[key]}, second {second.summary[key]}"
        for key in RECONCILE_COVERAGE_KEYS
        if first.summary[key] != second.summary[key]
    ]


def _reconcile_source_files(
    first: CurationRun, second: CurationRun
) -> tuple[list[str], list[str]]:
    """Source-file inventory drift, split into coverage and payload."""

    first_files = _source_files_by_path(first.source_files)
    second_files = _source_files_by_path(second.source_files)
    coverage = [
        f"{source_path}: file present in the first source only"
        for source_path in sorted(set(first_files) - set(second_files))
    ]
    coverage.extend(
        f"{source_path}: file present in the second source only"
        for source_path in sorted(set(second_files) - set(first_files))
    )

    payload: list[str] = []
    for source_path in sorted(set(first_files) & set(second_files)):
        for field_name in AUDIT_SOURCE_FILE_FIELDS:
            first_value = first_files[source_path].get(field_name)
            second_value = second_files[source_path].get(field_name)
            if first_value != second_value:
                payload.append(
                    f"{source_path}: {field_name}: "
                    f"first {first_value!r}, second {second_value!r}"
                )
    return coverage, payload


def _reconcile_manifest_entries(
    first_entries: dict[tuple[str, int], dict[str, Any]],
    second_entries: dict[tuple[str, int], dict[str, Any]],
) -> tuple[list[str], list[str], list[str]]:
    """Per-record drift, split into coverage, decisions, and payload."""

    coverage = [
        f"{location[0]}:{location[1]}: present in the first source only"
        for location in sorted(
            set(first_entries) - set(second_entries), key=_location_sort_key
        )
    ]
    coverage.extend(
        f"{location[0]}:{location[1]}: present in the second source only"
        for location in sorted(
            set(second_entries) - set(first_entries), key=_location_sort_key
        )
    )

    decisions: list[str] = []
    payload: list[str] = []
    for location in sorted(
        set(first_entries) & set(second_entries), key=_location_sort_key
    ):
        for field_name, bucket in (
            *((name, decisions) for name in RECONCILE_DECISION_FIELDS),
            *((name, payload) for name in RECONCILE_PAYLOAD_FIELDS),
        ):
            first_value = first_entries[location].get(field_name)
            second_value = second_entries[location].get(field_name)
            if first_value != second_value:
                bucket.append(
                    f"{location[0]}:{location[1]}: {field_name}: "
                    f"first {first_value!r}, second {second_value!r}"
                )
    return coverage, decisions, payload


def reconcile_runs(first: CurationRun, second: CurationRun) -> dict[str, list[str]]:
    """Compare two scans of one corpus, keyed by source path and line.

    ``coverage`` reports records one copy has and the other does not,
    ``decisions`` reports curation verdicts that disagree, and ``payload``
    reports agreeing verdicts reached from different source bytes.
    """

    file_coverage, file_payload = _reconcile_source_files(first, second)
    entry_coverage, decisions, entry_payload = _reconcile_manifest_entries(
        _manifest_by_location(first), _manifest_by_location(second)
    )
    return {
        "coverage": [
            *_reconcile_summary_coverage(first, second),
            *file_coverage,
            *entry_coverage,
        ],
        "decisions": decisions,
        "payload": [*file_payload, *entry_payload],
    }
