#!/usr/bin/env python3
"""Build, render, and re-verify the published impure-pair audit.

The audit is the public evidence behind a curated preference corpus: every
impure pair by source location and record id, the reason codes behind its
decision, and the counters those rows have to reconcile against.

Three responsibilities meet here because they are three views of one
document. ``build_audit`` derives it from a scan, ``render_audit_markdown``
publishes it, and ``audit_differences`` fails closed when a fresh scan has
drifted from a document published earlier. Rendering treats every audited
value as hostile: a record id comes from source JSONL, not from an internal
enum, so it is escaped before it can add table columns or hide a row.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any

_PIPELINES = Path(__file__).resolve().parent
if str(_PIPELINES) not in sys.path:
    sys.path.insert(0, str(_PIPELINES))

from preference_model import (  # noqa: E402
    ACTION_EXCLUDED,
    ACTION_REPAIRED,
    CurationRun,
    PreferenceCurationError,
)

__all__ = [
    "AUDIT_NAME",
    "AUDIT_PAIR_FIELDS",
    "AUDIT_SCHEMA_VERSION",
    "AUDIT_SOURCE_FILE_FIELDS",
    "audit_differences",
    "build_audit",
    "render_audit_markdown",
]

AUDIT_NAME = "same-context-preference-audit"
AUDIT_SCHEMA_VERSION = "1.1.0"


def _divergent_context_fields(entry: dict[str, Any]) -> list[str]:
    """Return the canonical context fields that differ across the two sides."""

    fields = []
    if entry.get("same_state") is False:
        fields.append("state")
    if entry.get("same_proposed_action") is False:
        fields.append("proposed_action")
    return fields


def build_audit(run: CurationRun) -> dict[str, Any]:
    """Return the public impure-pair audit document for one curation run.

    The document is the machine-readable half of the published audit: every
    impure pair by source location and record id, the reason codes behind its
    curation decision, and the state/proposal split that reconciles a
    ``same_state``-only count against the full same-context count.
    """

    summary = run.summary
    impure_pairs = [
        {
            "source_path": entry["source_path"],
            "source_line": entry["source_line"],
            "source_sha256": entry["source_sha256"],
            "record_id": entry["source_record_id"],
            "action": entry["action"],
            "classification": entry["classification"],
            "reason_codes": list(entry["reason_codes"]),
            "same_state": entry["same_state"],
            "same_proposed_action": entry["same_proposed_action"],
            "divergent_context_fields": _divergent_context_fields(entry),
            "context_diff_paths": list(entry["context_diff_paths"]),
        }
        for entry in run.manifest
        if entry["action"] in (ACTION_REPAIRED, ACTION_EXCLUDED)
        and (
            entry["same_state"] is not True
            or entry["same_proposed_action"] is not True
        )
    ]
    balanced = (
        summary["state_only_divergent_pairs"]
        + summary["proposed_action_only_divergent_pairs"]
        + summary["both_context_fields_divergent_pairs"]
        + summary["context_undetermined_pairs"]
    )
    if balanced != summary["impure_pairs"] or len(impure_pairs) != summary["impure_pairs"]:
        raise PreferenceCurationError(
            "internal error: impure-pair reconciliation does not balance "
            f"({len(impure_pairs)} listed, {balanced} bucketed, "
            f"{summary['impure_pairs']} impure)"
        )
    return {
        "schema_version": AUDIT_SCHEMA_VERSION,
        "audit": AUDIT_NAME,
        "transform": dict(summary["transform"]),
        "summary": {
            "preference_pairs": summary["preference_records"],
            "impure_pairs": summary["impure_pairs"],
            "same_state_pairs": summary["same_state_pairs"],
            "state_divergent_pairs": summary["state_divergent_pairs"],
            "state_undetermined_pairs": summary["state_undetermined_pairs"],
            "proposed_action_divergent_pairs": summary["proposed_action_divergent_pairs"],
            "proposed_action_undetermined_pairs": summary["proposed_action_undetermined_pairs"],
            "state_only_divergent_pairs": summary["state_only_divergent_pairs"],
            "proposed_action_only_divergent_pairs": summary["proposed_action_only_divergent_pairs"],
            "both_context_fields_divergent_pairs": summary["both_context_fields_divergent_pairs"],
            "context_undetermined_pairs": summary["context_undetermined_pairs"],
            "curated_retained_pairs": summary["retained_pairs"],
            "curated_repaired_pairs": summary["actions"].get(ACTION_REPAIRED, 0),
            "curated_excluded_pairs": summary["excluded_pairs"],
            "retained_context_purity_pct": summary["retained_context_purity_pct"],
        },
        "source_files": [dict(entry) for entry in run.source_files],
        "impure_pairs": impure_pairs,
    }


def _yes_no(value: bool | None) -> str:
    if value is None:
        return "n/a"
    return "yes" if value else "no"


def _markdown_cell_text(value: Any) -> str:
    """Flatten a source-controlled value into exactly one Markdown table cell.

    ``record_id``, ``source_path`` and the reason codes come from the audited
    JSON rather than from a constrained internal enum. A newline ends the
    table row and a ``|`` opens the next cell -- inside a code span too -- so
    a crafted value could otherwise add columns, inject rows, or visually
    hide a record from the published per-pair evidence.
    """

    text = str(value)
    for control in ("\r\n", "\r", "\n", "\t"):
        text = text.replace(control, " ")
    return text.replace("|", "\\|")


def _markdown_code_cell(value: Any) -> str:
    """Wrap a source-controlled value in a code span it cannot break out of."""

    text = _markdown_cell_text(value)
    # CommonMark closes a code span at the first backtick run matching the
    # opening one, so the fence must be longer than the longest run inside,
    # and a value that starts or ends with a backtick needs the pad space
    # that the reader strips back off.
    longest = max((len(run) for run in re.findall("`+", text)), default=0)
    fence = "`" * (longest + 1)
    pad = " " if text.startswith("`") or text.endswith("`") else ""
    return f"{fence}{pad}{text}{pad}{fence}"


def render_audit_markdown(audit: dict[str, Any]) -> str:
    """Render the audit document as the published Markdown tables."""

    summary = audit["summary"]
    lines = [
        "| Measure | Pairs |",
        "| --- | ---: |",
        f"| Published preference pairs | {summary['preference_pairs']} |",
        f"| `same_state = false` (state diverges) | {summary['state_divergent_pairs']} |",
        "| `same_proposed_action = false` (proposal diverges) | "
        f"{summary['proposed_action_divergent_pairs']} |",
        f"| Impure pairs (either field diverges) | {summary['impure_pairs']} |",
        f"| - state only | {summary['state_only_divergent_pairs']} |",
        f"| - proposed action only | {summary['proposed_action_only_divergent_pairs']} |",
        f"| - both fields | {summary['both_context_fields_divergent_pairs']} |",
        f"| - context not comparable | {summary['context_undetermined_pairs']} |",
        f"| Curated keep (already identical + repaired) | {summary['curated_retained_pairs']} |",
        f"| Curated exclude | {summary['curated_excluded_pairs']} |",
        f"| Curated same-context purity | {summary['retained_context_purity_pct']:.1f}% |",
        "",
        "| Pair | Source | `same_state` | `same_proposed_action` | Curation | Reason codes |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for pair in audit["impure_pairs"]:
        record_id = pair["record_id"]
        identifier = _markdown_code_cell(record_id) if record_id else "_(no record id)_"
        reasons = (
            ", ".join(_markdown_code_cell(code) for code in pair["reason_codes"])
            or "_(none)_"
        )
        location = _markdown_code_cell(
            f"{pair['source_path']}:{pair['source_line']}"
        )
        lines.append(
            f"| {identifier} "
            f"| {location} "
            f"| {_yes_no(pair['same_state'])} "
            f"| {_yes_no(pair['same_proposed_action'])} "
            f"| {_markdown_cell_text(pair['action'])} "
            f"| {reasons} |"
        )
    return "\n".join(lines)

def _location_sort_key(location: tuple[Any, Any]) -> tuple[str, int, str]:
    path_part, line_part = location
    line_number = line_part if isinstance(line_part, int) else 0
    return (str(path_part), line_number, str(line_part))


def _pairs_by_location(pairs: Any) -> dict[tuple[Any, Any], dict[str, Any]]:
    located: dict[tuple[Any, Any], dict[str, Any]] = {}
    for pair in pairs if isinstance(pairs, list) else ():
        if isinstance(pair, dict):
            located[(pair.get("source_path"), pair.get("source_line"))] = pair
    return located


def _source_files_by_path(files: Any) -> dict[str, dict[str, Any]]:
    """Key a source-file inventory by its relative path."""

    if not isinstance(files, (list, tuple)):
        return {}
    return {
        entry["source_path"]: entry
        for entry in files
        if isinstance(entry, dict) and isinstance(entry.get("source_path"), str)
    }


AUDIT_PAIR_FIELDS = (
    "source_sha256",
    "record_id",
    "action",
    "classification",
    "reason_codes",
    "same_state",
    "same_proposed_action",
    "divergent_context_fields",
    "context_diff_paths",
)
AUDIT_SOURCE_FILE_FIELDS = ("source_file_sha256",)


def _audit_header_differences(expected: dict[str, Any], actual: dict[str, Any]) -> list[str]:
    """Identity fields that must match before any count is comparable."""

    return [
        f"{key}: expected {expected.get(key)!r}, got {actual.get(key)!r}"
        for key in ("schema_version", "audit", "transform")
        if expected.get(key) != actual.get(key)
    ]


def _audit_summary_differences(expected: dict[str, Any], actual: dict[str, Any]) -> list[str]:
    """Every summary counter present on either side that disagrees."""

    expected_summary = expected.get("summary")
    expected_summary = expected_summary if isinstance(expected_summary, dict) else {}
    return [
        f"summary.{key}: expected {expected_summary.get(key)!r}, "
        f"got {actual['summary'].get(key)!r}"
        for key in sorted(set(expected_summary) | set(actual["summary"]))
        if expected_summary.get(key) != actual["summary"].get(key)
    ]


def _audit_source_file_differences(
    expected: dict[str, Any], actual: dict[str, Any]
) -> list[str]:
    """Source-file inventory drift, by path then by field."""

    expected_files = _source_files_by_path(expected.get("source_files"))
    actual_files = _source_files_by_path(actual.get("source_files"))
    differences = [
        f"{source_path}: audited source file is absent from this scan"
        for source_path in sorted(set(expected_files) - set(actual_files))
    ]
    differences.extend(
        f"{source_path}: source file is absent from the audit"
        for source_path in sorted(set(actual_files) - set(expected_files))
    )
    for source_path in sorted(set(expected_files) & set(actual_files)):
        for field_name in AUDIT_SOURCE_FILE_FIELDS:
            want = expected_files[source_path].get(field_name)
            got = actual_files[source_path].get(field_name)
            if want != got:
                differences.append(
                    f"{source_path}: {field_name}: expected {want!r}, got {got!r}"
                )
    return differences


def _audit_impure_pair_differences(
    expected: dict[str, Any], actual: dict[str, Any]
) -> list[str]:
    """Per-pair drift, by source location then by field."""

    expected_pairs = _pairs_by_location(expected.get("impure_pairs"))
    actual_pairs = _pairs_by_location(actual["impure_pairs"])
    differences = [
        f"{location[0]}:{location[1]}: audited impure pair is absent from this scan"
        for location in sorted(
            set(expected_pairs) - set(actual_pairs), key=_location_sort_key
        )
    ]
    differences.extend(
        f"{location[0]}:{location[1]}: impure pair is absent from the audit"
        for location in sorted(
            set(actual_pairs) - set(expected_pairs), key=_location_sort_key
        )
    )
    for location in sorted(
        set(expected_pairs) & set(actual_pairs), key=_location_sort_key
    ):
        for field_name in AUDIT_PAIR_FIELDS:
            want = expected_pairs[location].get(field_name)
            got = actual_pairs[location].get(field_name)
            if want != got:
                differences.append(
                    f"{location[0]}:{location[1]}: {field_name}: "
                    f"expected {want!r}, got {got!r}"
                )
    return differences


def audit_differences(expected: Any, actual: dict[str, Any]) -> list[str]:
    """Return every way ``actual`` departs from a previously published audit."""

    if not isinstance(expected, dict):
        return ["expected audit document is not a JSON object"]
    return [
        *_audit_header_differences(expected, actual),
        *_audit_summary_differences(expected, actual),
        *_audit_source_file_differences(expected, actual),
        *_audit_impure_pair_differences(expected, actual),
    ]
