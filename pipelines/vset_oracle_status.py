"""Map a unittest result onto one oracle status.

Kept apart from the child runner so that module stays under the file
complexity gate. A fixture error is recorded on a holder, and a subtest
failure is recorded on the subtest, not on the test object.
"""

from __future__ import annotations

import sys
import unittest

if __package__:  # pragma: no cover - package-child import path
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("vset_oracle_status")
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "vset_oracle_status"
    )


def _problem_status(result: unittest.TestResult) -> str:
    if result.errors:
        return "ERROR"
    if result.failures:
        return "FAIL"
    if result.unexpectedSuccesses:
        return "unexpectedSuccess"
    return ""


def status(result: unittest.TestResult) -> str:
    """Whole-result label used when a suite is one test."""

    problem = _problem_status(result)
    if problem:
        return problem
    if result.expectedFailures:
        return "expectedFailure"
    if result.skipped:
        return "SKIP"
    if result.testsRun:
        return "ok"
    return "ERROR"


def _row_owner(item: object) -> object:
    if isinstance(item, tuple):
        return item[0]
    return item


def _same_case(found: object, test: unittest.case.TestCase) -> bool:
    if found is test:
        return True
    return getattr(found, "test_case", None) is test


def _names_class(text: str, test: unittest.case.TestCase) -> bool:
    if test.__class__.__qualname__ not in text:
        return False
    return test.__class__.__module__ in text


def _module_fixture(text: str) -> bool:
    if "setUpModule" in text:
        return True
    if "tearDownModule" in text:
        return True
    return False


def _names_module(text: str, test: unittest.case.TestCase) -> bool:
    if not _module_fixture(text):
        return False
    return test.__class__.__module__ in text


def _holder_for(found: object, test: unittest.case.TestCase) -> bool:
    text = getattr(found, "description", "")
    if not isinstance(text, str):
        return False
    if _names_class(text, test):
        return True
    return _names_module(text, test)


def _labeled(rows: object, test: unittest.case.TestCase, label: str) -> str:
    for item in rows:  # type: ignore[union-attr]
        found = _row_owner(item)
        if _same_case(found, test):
            return label
        if _holder_for(found, test):
            return label
    return ""


def _unrun_failure(result: unittest.TestResult) -> str:
    if result.testsRun:
        return ""
    if result.errors:
        return "ERROR"
    if result.failures:
        return "FAIL"
    return ""


def case_status(result: unittest.TestResult, test: unittest.case.TestCase) -> str:
    """Status of one test, including its subtests and class fixtures."""

    checks = (
        (result.errors, "ERROR"),
        (result.failures, "FAIL"),
        (result.skipped, "SKIP"),
        (result.expectedFailures, "expectedFailure"),
        (result.unexpectedSuccesses, "unexpectedSuccess"),
    )
    for rows, label in checks:
        found = _labeled(rows, test, label)
        if found:
            return found
    pending = _unrun_failure(result)
    if pending:
        return pending
    return "ok"


if __package__:  # pragma: no cover - package-child import path
    _expose_package_sibling(__name__)
