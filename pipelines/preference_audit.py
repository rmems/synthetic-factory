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
    canonical_json,
)

__all__ = [
    "AUDIT_HEADER_FIELDS",
    "AUDIT_NAME",
    "AUDIT_PAIR_FIELDS",
    "AUDIT_SCHEMA_VERSION",
    "AUDIT_SOURCE_FILE_FIELDS",
    "audit_differences",
    "build_audit",
    "render_audit_markdown",
    "source_files_by_path",
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
    # Backslashes first: escaping only the pipe turns a value that already
    # ends in a backslash into ``\\|``, where the first backslash escapes the
    # second and hands the pipe back to the table parser as a delimiter.
    return text.replace("\\", "\\\\").replace("|", "\\|")


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
        # ``0`` and ``false`` are record ids the JSON audit preserves; only
        # a genuinely absent id may be rendered as one.
        identifier = (
            "_(no record id)_"
            if record_id is None
            else _markdown_code_cell(record_id)
        )
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


_MISSING = object()


def _json_type_name(value: Any) -> str:
    """Name a value's JSON type, keeping ``true`` distinct from ``1``."""

    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, (int, float)):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    if value is None:
        return "null"
    return type(value).__name__


def _json_equal(left: Any, right: Any) -> bool:
    """Whether two audited values agree in JSON type as well as in value.

    Python scores ``False == 0`` and ``True == 1``, so a value-only check
    would accept an expected audit that rewrote ``same_state: false`` as the
    number ``0``. The published document is evidence, and a change of type is
    a change of evidence, so compare the two the way JSON does.
    """

    if _json_type_name(left) != _json_type_name(right):
        return False
    if isinstance(left, dict):
        return set(left) == set(right) and all(
            _json_equal(left[key], right[key]) for key in left
        )
    if isinstance(left, list):
        return len(left) == len(right) and all(
            _json_equal(one, other) for one, other in zip(left, right)
        )
    return left == right


def _json_key(value: Any) -> tuple[str, str]:
    """Key a JSON value by type and canonical text.

    Keying by the value alone lets ``source_line: true`` index the same slot
    as line ``1`` -- Python hashes them identically -- and raises outright on
    a list or an object, so an audit with a structured location could not be
    compared at all.
    """

    try:
        return _json_type_name(value), canonical_json(value)
    except (TypeError, ValueError):
        return _json_type_name(value), repr(value)


def _pair_location(pair: dict[str, Any]) -> tuple[tuple[str, str], tuple[str, str]]:
    return _json_key(pair.get("source_path")), _json_key(pair.get("source_line"))


def _pair_location_text(pair: dict[str, Any]) -> str:
    return f"{pair.get('source_path')}:{pair.get('source_line')}"


def _pair_order(pair: dict[str, Any]) -> tuple[str, int, str]:
    """Sort pairs by path then by line, with real line numbers in order."""

    line = pair.get("source_line")
    number = line if isinstance(line, int) and not isinstance(line, bool) else 0
    return str(pair.get("source_path")), number, str(line)


def _pairs_by_location(pairs: Any) -> tuple[dict[Any, dict[str, Any]], list[str]]:
    """Index impure pairs by typed location, reporting any duplicate.

    Two rows at one source location would silently overwrite each other. If
    the survivor then matched the scan, the expected list could carry an
    extra or conflicting row -- and disagree with its own summary -- while
    the drift check still exited successfully.
    """

    located: dict[Any, dict[str, Any]] = {}
    duplicates: list[str] = []
    for pair in pairs if isinstance(pairs, list) else ():
        if not isinstance(pair, dict):
            continue
        location = _pair_location(pair)
        if location in located:
            duplicates.append(
                f"{_pair_location_text(pair)}: "
                "impure pair is listed more than once in the audit"
            )
            continue
        located[location] = pair
    return located, sorted(dict.fromkeys(duplicates))


def source_files_by_path(files: Any) -> dict[str, dict[str, Any]]:
    """Key a source-file inventory by its relative path."""

    if not isinstance(files, (list, tuple)):
        return {}
    return {
        entry["source_path"]: entry
        for entry in files
        if isinstance(entry, dict) and isinstance(entry.get("source_path"), str)
    }


def _duplicate_source_paths(files: Any) -> list[str]:
    """Name any relative path a source-file inventory lists more than once."""

    seen: set[str] = set()
    duplicates: list[str] = []
    for entry in files if isinstance(files, (list, tuple)) else ():
        if not isinstance(entry, dict):
            continue
        source_path = entry.get("source_path")
        if not isinstance(source_path, str):
            continue
        if source_path in seen:
            duplicates.append(
                f"{source_path}: source file is listed more than once in the audit"
            )
        seen.add(source_path)
    return sorted(dict.fromkeys(duplicates))


def _field_differences(
    prefix: str,
    expected_entry: dict[str, Any],
    actual_entry: dict[str, Any],
    field_names: Any,
) -> list[str]:
    """Report each named field that is absent on either side or disagrees.

    ``.get()`` alone cannot tell a dropped key from a key whose value is
    ``null``, which is how a published row could quietly lose a field and
    still reconcile. A sentinel keeps the two cases apart so the check
    verifies that a required field is *present* as well as equal.
    """

    differences: list[str] = []
    for field_name in field_names:
        label = f"{prefix}{field_name}"
        want = expected_entry.get(field_name, _MISSING)
        got = actual_entry.get(field_name, _MISSING)
        if want is _MISSING and got is _MISSING:
            differences.append(f"{label}: absent from both the audit and this scan")
        elif want is _MISSING:
            differences.append(f"{label}: absent from the audit, got {got!r}")
        elif got is _MISSING:
            differences.append(f"{label}: expected {want!r}, absent from this scan")
        elif not _json_equal(want, got):
            differences.append(f"{label}: expected {want!r}, got {got!r}")
    return differences


AUDIT_HEADER_FIELDS = ("schema_version", "audit", "transform")
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

    return _field_differences("", expected, actual, AUDIT_HEADER_FIELDS)


def _audit_summary_differences(expected: dict[str, Any], actual: dict[str, Any]) -> list[str]:
    """Every summary counter present on either side that disagrees."""

    expected_summary = expected.get("summary")
    expected_summary = expected_summary if isinstance(expected_summary, dict) else {}
    return _field_differences(
        "summary.",
        expected_summary,
        actual["summary"],
        sorted(set(expected_summary) | set(actual["summary"])),
    )


def _audit_source_file_differences(
    expected: dict[str, Any], actual: dict[str, Any]
) -> list[str]:
    """Source-file inventory drift, by path then by field."""

    expected_files = source_files_by_path(expected.get("source_files"))
    actual_files = source_files_by_path(actual.get("source_files"))
    differences = _duplicate_source_paths(expected.get("source_files"))
    differences.extend(
        f"{source_path}: audited source file is absent from this scan"
        for source_path in sorted(set(expected_files) - set(actual_files))
    )
    differences.extend(
        f"{source_path}: source file is absent from the audit"
        for source_path in sorted(set(actual_files) - set(expected_files))
    )
    for source_path in sorted(set(expected_files) & set(actual_files)):
        differences.extend(
            _field_differences(
                f"{source_path}: ",
                expected_files[source_path],
                actual_files[source_path],
                AUDIT_SOURCE_FILE_FIELDS,
            )
        )
    return differences


def _audit_impure_pair_differences(
    expected: dict[str, Any], actual: dict[str, Any]
) -> list[str]:
    """Per-pair drift, by source location then by field."""

    expected_pairs, differences = _pairs_by_location(expected.get("impure_pairs"))
    actual_pairs, actual_duplicates = _pairs_by_location(actual["impure_pairs"])
    differences.extend(actual_duplicates)
    differences.extend(
        f"{_pair_location_text(expected_pairs[location])}: "
        "audited impure pair is absent from this scan"
        for location in sorted(
            set(expected_pairs) - set(actual_pairs),
            key=lambda item: _pair_order(expected_pairs[item]),
        )
    )
    differences.extend(
        f"{_pair_location_text(actual_pairs[location])}: "
        "impure pair is absent from the audit"
        for location in sorted(
            set(actual_pairs) - set(expected_pairs),
            key=lambda item: _pair_order(actual_pairs[item]),
        )
    )
    for location in sorted(
        set(expected_pairs) & set(actual_pairs),
        key=lambda item: _pair_order(actual_pairs[item]),
    ):
        differences.extend(
            _field_differences(
                f"{_pair_location_text(actual_pairs[location])}: ",
                expected_pairs[location],
                actual_pairs[location],
                AUDIT_PAIR_FIELDS,
            )
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
