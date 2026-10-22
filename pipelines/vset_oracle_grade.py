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
    from .vset_oracle_remote import grade_test as _grade_test
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
    from vset_oracle_remote import grade_test as _grade_test

_CAPTURE_LIMIT = 4000


def _suite_ok(rows: list[dict[str, str]], expected: list[str]) -> bool:
    reported = sorted(row["id"] for row in rows)
    declared = sorted(expected)
    if reported != declared:
        return False
    if not declared:
        return False
    return all(row["status"] == "ok" for row in rows)


def _suite_report(
    rows: list[dict[str, str]], expected: list[str], captured: str
) -> dict[str, Any]:
    ordered = sorted(rows, key=lambda item: item["id"])
    report: dict[str, Any] = {
        "tests": ordered,
        "failures": sum(item["status"] == "FAIL" for item in ordered),
        "errors": sum(item["status"] == "ERROR" for item in ordered),
        "ok": _suite_ok(ordered, expected),
    }
    report["result_hash"] = _sha256_text(_canonical_json(report["tests"]))
    if captured.strip():
        report["captured_output"] = captured[-_CAPTURE_LIMIT:]
    return report


def _spec_for(test_id: str, modules: list[dict[str, str]]) -> dict[str, str]:
    for item in modules:
        if test_id.startswith(item["module"] + "."):
            return item
    raise VSetValidationError(
        ERR_ORACLE_EXECUTION_MISMATCH, f"oracle runner failed: unknown test {test_id}"
    )


def _class_and_method(test_id: str, module_name: str) -> tuple[str, str]:
    class_name, dot, method_name = test_id[len(module_name) + 1 :].rpartition(".")
    if not dot:
        raise VSetValidationError(
            ERR_ORACLE_EXECUTION_MISMATCH, f"oracle runner failed: bad test id {test_id}"
        )
    if not class_name:
        raise VSetValidationError(
            ERR_ORACLE_EXECUTION_MISMATCH, f"oracle runner failed: bad test id {test_id}"
        )
    if not method_name:
        raise VSetValidationError(
            ERR_ORACLE_EXECUTION_MISMATCH, f"oracle runner failed: bad test id {test_id}"
        )
    return class_name, method_name


def grade_suite(
    work: Path,
    modules: list[dict[str, str]],
    expected: list[str],
    sources: dict[str, dict[str, str]],
) -> dict[str, Any]:
    """Run every declared id here and build the suite report."""

    rows: list[dict[str, str]] = []
    captured: list[str] = []
    for spec in modules:
        _require_match(spec, expected, sources[spec["folder"]])
    for test_id in expected:
        spec = _spec_for(test_id, modules)
        names = _class_and_method(test_id, spec["module"])
        status, text = _grade_test(work, spec, names, sources[spec["folder"]])
        rows.append({"id": test_id, "status": status})
        captured.append(text)
    return _suite_report(rows, expected, "".join(captured))


if __package__:  # pragma: no cover - package-child import path
    _expose_package_sibling(__name__)
