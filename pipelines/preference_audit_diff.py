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

import sys
from pathlib import Path
from typing import Any

_PIPELINES = Path(__file__).resolve().parent
if str(_PIPELINES) not in sys.path:
    sys.path.insert(0, str(_PIPELINES))

from preference_model import canonical_json  # noqa: E402

__all__ = [
    "AUDIT_HEADER_FIELDS",
    "AUDIT_PAIR_FIELDS",
    "AUDIT_SOURCE_FILE_FIELDS",
    "audit_differences",
    "source_files_by_path",
]


_MISSING = object()


# ``bool`` is a subclass of ``int``, so it has to be matched first or every
# ``true`` in an audited document would name itself a number.
_JSON_TYPE_NAMES = (
    (bool, "boolean"),
    (str, "string"),
    (int, "number"),
    (float, "number"),
    (list, "array"),
    (dict, "object"),
)


def _json_type_name(value: Any) -> str:
    """Name a value's JSON type, keeping ``true`` distinct from ``1``."""

    if value is None:
        return "null"
    for python_type, type_name in _JSON_TYPE_NAMES:
        if isinstance(value, python_type):
            return type_name
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


def _pairs_by_location(
    pairs: Any, side: str
) -> tuple[dict[Any, dict[str, Any]], list[str]]:
    """Index impure pairs by typed location, reporting any duplicate.

    Two rows at one source location would silently overwrite each other. If
    the survivor then matched the scan, the expected list could carry an
    extra or conflicting row -- and disagree with its own summary -- while
    the drift check still exited successfully. Both sides are checked: a
    scan cannot currently emit a duplicate, and this is what would say so if
    that ever stopped being true.
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


def _duplicate_source_paths(files: Any, side: str) -> list[str]:
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
                f"{source_path}: source file is listed more than once in {side}"
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
    differences = _duplicate_source_paths(expected.get("source_files"), "the audit")
    differences.extend(
        _duplicate_source_paths(actual.get("source_files"), "this scan")
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

    expected_pairs, differences = _pairs_by_location(
        expected.get("impure_pairs"), "the audit"
    )
    actual_pairs, actual_duplicates = _pairs_by_location(
        actual["impure_pairs"], "this scan"
    )
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
