"""Parent-side oracle grading.

Each declared test runs in this process through ``unittest``. Candidate
modules are not imported here. A child answers attribute and call requests
after importing ``src/``. The child has no pass channel: an early exit, a
replaced ``TestCase.run``, or a rewritten runner file cannot make a suite
``ok``. ``ok`` requires every id counted from the restored suite to have
run and passed.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

if __package__:  # pragma: no cover - package-child import path
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("vset_oracle_grade")
    from .vset_constants import (
        ERR_ORACLE_EXECUTION_MISMATCH,
        VSetValidationError,
        _canonical_json,
        _sha256_text,
    )
    from .vset_oracle_collect import require_match as _require_match
    from .vset_oracle_remote import grade_cases as _grade_cases
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "vset_oracle_grade"
    )
    from vset_constants import (
        ERR_ORACLE_EXECUTION_MISMATCH,
        VSetValidationError,
        _canonical_json,
        _sha256_text,
    )
    from vset_oracle_collect import require_match as _require_match
    from vset_oracle_remote import grade_cases as _grade_cases

_CAPTURE_LIMIT = 4000


def _ids(rows: list[dict[str, str]]) -> list[str]:
    return sorted(row["id"] for row in rows)


def _passed(row: dict[str, str]) -> bool:
    return row["status"] == "ok"


def _suite_ok(rows: list[dict[str, str]], expected: list[str]) -> bool:
    if _ids(rows) != sorted(expected):
        return False
    if not expected:
        return False
    return all(_passed(row) for row in rows)


def _ordered(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return sorted(rows, key=_row_id)


def _row_id(row: dict[str, str]) -> str:
    return row["id"]


def _count(rows: list[dict[str, str]], status: str) -> int:
    return sum(item["status"] == status for item in rows)


def _attach_capture(report: dict[str, Any], captured: str) -> None:
    if captured.strip():
        report["captured_output"] = captured[-_CAPTURE_LIMIT:]


def _suite_report(
    rows: list[dict[str, str]], expected: list[str], captured: str
) -> dict[str, Any]:
    ordered = _ordered(rows)
    report: dict[str, Any] = {
        "tests": ordered,
        "failures": _count(ordered, "FAIL"),
        "errors": _count(ordered, "ERROR"),
        "ok": _suite_ok(ordered, expected),
    }
    report["result_hash"] = _sha256_text(_canonical_json(report["tests"]))
    _attach_capture(report, captured)
    return report


def _spec_for(test_id: str, modules: list[dict[str, str]]) -> dict[str, str]:
    for item in modules:
        if test_id.startswith(item["module"] + "."):
            return item
    raise VSetValidationError(
        ERR_ORACLE_EXECUTION_MISMATCH, f"oracle runner failed: unknown test {test_id}"
    )


def _bad_test_id(test_id: str) -> VSetValidationError:
    return VSetValidationError(
        ERR_ORACLE_EXECUTION_MISMATCH, f"oracle runner failed: bad test id {test_id}"
    )


def _id_piece(part: str, dot: str, test_id: str) -> str:
    if not dot:
        raise _bad_test_id(test_id)
    if not part:
        raise _bad_test_id(test_id)
    return part


def _class_and_method(test_id: str, module_name: str) -> tuple[str, str]:
    class_name, dot, method_name = test_id[len(module_name) + 1 :].rpartition(".")
    _id_piece(class_name, dot, test_id)
    _id_piece(method_name, dot, test_id)
    return class_name, method_name


def _bucket(grouped: dict[str, list[str]], order: list[str], key: str) -> list[str]:
    if key not in grouped:
        order.append(key)
        grouped[key] = []
    return grouped[key]


def _group_ids(
    modules: list[dict[str, str]], expected: list[str]
) -> tuple[list[str], dict[str, list[str]]]:
    grouped: dict[str, list[str]] = {}
    order: list[str] = []
    for test_id in expected:
        spec = _spec_for(test_id, modules)
        _bucket(grouped, order, spec["module"]).append(test_id)
    return order, grouped


def _record_group(
    rows: list[dict[str, str]], ids: list[str], statuses: list[str]
) -> None:
    if len(statuses) != len(ids):
        statuses = ["ERROR"] * len(ids)
    for test_id, status in zip(ids, statuses, strict=True):
        rows.append({"id": test_id, "status": status})


def grade_suite(
    work: Path,
    modules: list[dict[str, str]],
    expected: list[str],
    bundle: tuple[dict[str, dict[str, str]], frozenset[str]],
) -> dict[str, Any]:
    """Run every declared id here and build the suite report."""

    sources, src_names = bundle
    rows: list[dict[str, str]] = []
    captured: list[str] = []
    for spec in modules:
        _require_match(spec, expected, sources[spec["folder"]])
    order, grouped = _group_ids(modules, expected)
    for key in order:
        ids = grouped[key]
        spec = _spec_for(ids[0], modules)
        cases = [_class_and_method(test_id, spec["module"]) for test_id in ids]
        statuses, text = _grade_cases(
            work, spec, cases, (sources[spec["folder"]], src_names)
        )
        _record_group(rows, ids, statuses)
        captured.append(text)
    return _suite_report(rows, expected, "".join(captured))


if __package__:  # pragma: no cover - package-child import path
    _expose_package_sibling(__name__)
