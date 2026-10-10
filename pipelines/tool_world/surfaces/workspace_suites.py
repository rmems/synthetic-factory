#!/usr/bin/env python3
"""Declared test suites of the workspace surface: checked at load, evaluated against the tree.

A suite is a pack member listing cases; each case checks one path of the
virtual tree. ``check_suite`` refuses at load any suite the evaluator could
not run, so ``evaluate_suite`` never meets an unexpected shape. The evaluation
is a function of the current files alone, so an edit changes the outcome; only
a scheduled flaky-test fault fails a case for another reason, and it does so
with a timeout no file content could cause.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .. import vocabulary as cv
from .._contract import bind_import_twin, sha256_bytes

__all__ = ["check_suite", "evaluate_suite"]

_TIMEOUT_FAILURE = "ETIMEDOUT after 30s (environment)"
_CHECK_FIELDS: Mapping[str, tuple[str, ...]] = {
    "file_exists": ("path",),
    "file_contains": ("path", "text"),
    "file_not_contains": ("path", "text"),
    "file_sha256": ("path", "sha256"),
}


# --- one check against the text found at its path --------------------------


def _contains(text: str, check: Mapping[str, Any]) -> str | None:
    return None if check["text"] in text else f"{check['path']} lacks {check['text']!r}"


def _not_contains(text: str, check: Mapping[str, Any]) -> str | None:
    if check["text"] not in text:
        return None
    return f"{check['path']} still contains {check['text']!r}"


def _sha256_matches(text: str, check: Mapping[str, Any]) -> str | None:
    if sha256_bytes(text.encode("utf-8")) == check["sha256"]:
        return None
    return f"{check['path']} content differs"


_CHECKS = {
    "file_exists": lambda text, check: None,
    "file_contains": _contains,
    "file_not_contains": _not_contains,
    "file_sha256": _sha256_matches,
}


# --- evaluation ------------------------------------------------------------


def evaluate_suite(
    files: Mapping[str, str], spec: Mapping[str, Any], flaky_case: str | None = None
) -> dict[str, Any]:
    """Every case of a checked suite against ``files``: counts plus one FAIL line per failure."""
    failures = []
    for case in spec["cases"]:
        message = _case_failure(files, case, flaky_case)
        if message is not None:
            failures.append(f"FAIL {case['id']}: {message}")
    passed = len(spec["cases"]) - len(failures)
    return {"passed": passed, "failed": len(failures), "failures": failures}


def _case_failure(
    files: Mapping[str, str], case: Mapping[str, Any], flaky_case: str | None
) -> str | None:
    """Why a case fails, or None; the flaky case times out whatever the tree holds."""
    if case["id"] == flaky_case:
        return _TIMEOUT_FAILURE
    check = case["check"]
    text = files.get(check["path"])
    if text is None:
        return f"{check['path']} does not exist"
    return _CHECKS[check["kind"]](text, check)


# --- load-time checks ------------------------------------------------------


def _check_case(case: Any, where: str) -> str:
    """Refuse a case the suite evaluator could not run; return its id."""
    cv.refuse_when(
        not isinstance(case, Mapping) or not isinstance(case.get("id"), str) or not case["id"],
        cv.FINDING_PACK_FIELD_INVALID,
        f"{where}: a case must be an object with a nonempty string id",
    )
    check = case.get("check")
    kind = check.get("kind") if isinstance(check, Mapping) else None
    cv.refuse_when(
        not isinstance(kind, str) or kind not in _CHECK_FIELDS,
        cv.FINDING_PACK_FIELD_INVALID,
        f"{where}: case {case['id']!r} needs a check whose kind is one of {list(_CHECK_FIELDS)}",
    )
    fields = _CHECK_FIELDS[check["kind"]]
    cv.refuse_when(
        set(check) != {"kind", *fields} or any(not isinstance(check[key], str) for key in fields),
        cv.FINDING_PACK_FIELD_INVALID,
        f"{where}: a {check['kind']} check carries exactly the string fields {list(fields)}",
    )
    return case["id"]


def check_suite(name: str, spec: Any, where: str) -> None:
    """Refuse a declared suite at load so ``evaluate_suite`` never meets an unexpected shape."""
    cv.refuse_when(
        not isinstance(spec, Mapping)
        or spec.get("suite") != name
        or not isinstance(spec.get("cases"), list)
        or not spec["cases"],
        cv.FINDING_PACK_FIELD_INVALID,
        f"{where}: a suite must declare suite == {name!r} and a nonempty cases list",
    )
    ids = [_check_case(case, f"{where}.cases[{index}]") for index, case in enumerate(spec["cases"])]
    cv.refuse_when(
        len(set(ids)) != len(ids), cv.FINDING_PACK_FIELD_INVALID, f"{where}: duplicate case ids"
    )


bind_import_twin(__name__)
