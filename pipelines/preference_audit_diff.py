#!/usr/bin/env python3
"""Fail closed when a fresh scan has drifted from a published audit.

``audit --expect`` exists to answer one question: does this corpus still say
what the committed audit says it says? Everything here therefore treats the
expected document as evidence rather than as configuration, and reports a
difference wherever the two disagree.

Three kinds of disagreement are easy to miss and are handled explicitly. A
field can be *absent* rather than merely null, so comparison goes through a
sentinel instead of ``.get()``. A value can change JSON *type* without
changing Python equality -- ``false`` to ``0``, ``1`` to ``true`` -- so
comparison is by type as well as value. And a location can be listed twice,
silently overwriting its twin, so both inventories report a repeated key.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

_PIPELINES = Path(__file__).resolve().parent
if str(_PIPELINES) not in sys.path:
    sys.path.insert(0, str(_PIPELINES))

from preference_model import json_equal, json_key  # noqa: E402

__all__ = [
    "AUDIT_COLLECTIONS",
    "AUDIT_HEADER_FIELDS",
    "AUDIT_PAIR_FIELDS",
    "AUDIT_SOURCE_FILE_FIELDS",
    "audit_differences",
    "parse_expected_audit",
    "source_files_by_path",
]


_MISSING = object()

# Which document a reported fault came from. Named so a message can never
# blame the scan for something the audit said, or the reverse.
_AUDIT_SIDE = "the audit"
_SCAN_SIDE = "this scan"


def _reject_duplicate_members(members: list[tuple[str, Any]]) -> dict[str, Any]:
    """Refuse a JSON object that names the same member twice.

    ``json.loads`` keeps the last value for a repeated member, so a forged
    one placed before the real one is parsed away before any comparison can
    see it -- a bypass that sits underneath every check in this module,
    including the duplicate-location checks, because it happens while the
    document is still being read.
    """

    parsed: dict[str, Any] = {}
    for key, value in members:
        if key in parsed:
            raise ValueError(f"duplicate object member: {key!r}")
        parsed[key] = value
    return parsed


def parse_expected_audit(text: str) -> Any:
    """Parse a published audit document, fail-closed on repeated members."""

    return json.loads(text, object_pairs_hook=_reject_duplicate_members)


def _pair_location(pair: dict[str, Any]) -> tuple[tuple[str, str], tuple[str, str]]:
    return json_key(pair.get("source_path")), json_key(pair.get("source_line"))


def _pair_location_text(pair: dict[str, Any]) -> str:
    return f"{pair.get('source_path')}:{pair.get('source_line')}"


def _pair_order(pair: dict[str, Any]) -> tuple[str, int, str]:
    """Sort pairs by path then by line, with real line numbers in order."""

    line = pair.get("source_line")
    number = line if isinstance(line, int) and not isinstance(line, bool) else 0
    return str(pair.get("source_path")), number, str(line)


def _pairs_by_location(
    pairs: Any, side: str
) -> tuple[dict[Any, dict[str, Any]], list[str]]:
    """Index impure pairs by typed location, reporting any duplicate.

    Two rows at one source location would silently overwrite each other. If
    the survivor then matched the scan, the expected list could carry an
    extra or conflicting row -- and disagree with its own summary -- while
    the drift check still exited successfully. Both sides are checked: a
    scan cannot currently emit a duplicate, and this is what would say so if
    that ever stopped being true. A row that is not an object is reported for
    the same reason, rather than quietly dropped.
    """

    located: dict[Any, dict[str, Any]] = {}
    duplicates: list[str] = []
    for index, pair in enumerate(pairs if isinstance(pairs, list) else ()):
        if not isinstance(pair, dict):
            # Skipping the row would let a scalar appended to a published list
            # pass as no drift at all, while the list stopped reconciling with
            # its own summary.
            duplicates.append(
                f"impure_pairs[{index}]: row in {side} is not an object"
            )
            continue
        location = _pair_location(pair)
        if location in located:
            duplicates.append(
                f"{_pair_location_text(pair)}: "
                f"impure pair is listed more than once in {side}"
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


def _source_file_inventory_faults(files: Any, side: str) -> list[str]:
    """Rows a source-file inventory cannot be compared through.

    Two faults make a row uncomparable and both have to be reported rather
    than skipped: a row the comparison cannot read or key, and a path that
    would silently collapse onto an earlier row. Either one, left quiet,
    would let an edited inventory reconcile against a scan it no longer
    describes.
    """

    faults: list[str] = []
    seen: set[str] = set()
    for index, entry in enumerate(files if isinstance(files, (list, tuple)) else ()):
        label = f"source_files[{index}]: row in {side}"
        if not isinstance(entry, dict):
            faults.append(f"{label} is not an object")
            continue
        source_path = entry.get("source_path")
        if not isinstance(source_path, str):
            faults.append(f"{label} has no string source_path")
            continue
        if source_path in seen:
            faults.append(
                f"{source_path}: source file is listed more than once in {side}"
            )
        seen.add(source_path)
    return faults


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
        elif not json_equal(want, got):
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


AUDIT_COLLECTIONS = ("impure_pairs", "source_files")


def _audit_collection_faults(document: dict[str, Any], side: str) -> list[str]:
    """Collections that must be present and a list before any row is read.

    Every row-level check below reads an absent or scalar collection as "no
    rows". On a corpus that genuinely has none of that kind, deleting the
    whole collection from a published audit would therefore match the scan
    exactly and exit 0, underneath the per-row and per-field checks.
    """

    faults: list[str] = []
    for name in AUDIT_COLLECTIONS:
        value = document.get(name, _MISSING)
        if value is _MISSING:
            faults.append(f"{name}: absent from {side}")
        elif not isinstance(value, list):
            faults.append(f"{name}: is not a list in {side}")
    return faults


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
    differences = _source_file_inventory_faults(
        expected.get("source_files"), _AUDIT_SIDE
    )
    differences.extend(
        _source_file_inventory_faults(actual.get("source_files"), _SCAN_SIDE)
    )
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

    expected_pairs, differences = _pairs_by_location(expected.get("impure_pairs"), _AUDIT_SIDE)
    actual_pairs, actual_duplicates = _pairs_by_location(actual["impure_pairs"], _SCAN_SIDE)
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
        *_audit_collection_faults(expected, _AUDIT_SIDE),
        *_audit_collection_faults(actual, _SCAN_SIDE),
        *_audit_header_differences(expected, actual),
        *_audit_summary_differences(expected, actual),
        *_audit_source_file_differences(expected, actual),
        *_audit_impure_pair_differences(expected, actual),
    ]
