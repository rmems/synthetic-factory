#!/usr/bin/env python3
"""The pinned program catalog: loading, pins, doctest examples, hidden cases.

A catalog directory holds ``CATALOG.json`` (identity, upstream, pins),
``programs.jsonl`` (one program per line, the module text as a JSON string so
no linter or test discovery ever touches third-party code) and
``LICENSE.upstream``. Load and pin verification live in :mod:`.catalog_load`
so this module stays the types, doctest helpers and ``catalog_check``.
:func:`catalog_check` is the "original passes" demonstration: every
program's original must pass its public examples and its hidden cases twice
identically, and a certifying reference must agree with the pinned wants twice.
"""

from __future__ import annotations

import ast
import doctest
import hashlib
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import executor as ex
from . import vocabulary as cv
from ._contract import bind_import_twin, oc

CATALOG_FILENAME = "CATALOG.json"
PROGRAMS_FILENAME = "programs.jsonl"
LICENSE_FILENAME = "LICENSE.upstream"
SPLITS = ("train", "validation", "held_out")
MAX_CASE_ARGS_CHARS = 4_096
MAX_PUBLIC_EXAMPLES = 48  # 72 total rows fit the 1 MiB report budget with UTF-8 output
_UPSTREAM_FIELDS = ("repository", "commit", "path", "file_sha256", "function", "license")

__all__ = [
    "CATALOG_FILENAME", "LICENSE_FILENAME", "PROGRAMS_FILENAME", "Catalog", "Example", "Program",
    "Reference", "catalog_check", "examples_of", "examples_sha256", "function_node",
    "load_catalog", "sha256_text",
]


@dataclass(frozen=True)
class Example:
    """One doctest example of the target function, as the parser sees it."""

    example_id: str
    source: str
    want: str
    exc_msg: str | None

    def key(self) -> tuple[str, str, str | None]:
        return (self.source, self.want, self.exc_msg)


@dataclass(frozen=True)
class Reference:
    """The complementary oracle: a sibling, a reviewed expression, or the original itself."""

    kind: str
    function: str | None = None
    source: str | None = None
    sha256: str | None = None

    @property
    def certifying(self) -> bool:
        return self.kind in cv.CERTIFYING_REFERENCE_KINDS


@dataclass(frozen=True)
class Program:
    """One pinned program: identity, module text, public examples and hidden cases."""

    program_id: str
    family: str
    upstream: Mapping[str, Any]
    text: str
    sha256: str
    function: str
    examples: tuple[Example, ...]
    examples_sha256: str
    reference: Reference
    cases: tuple[Mapping[str, str], ...]
    group_id: str | None
    split: str | None

    def job(self, label: str, text: str | None = None) -> ex.Job:
        """A harness job over this program's function and cases (``text`` overrides the module)."""

        module_text = self.text if text is None else text
        return ex.Job(
            label, module_text, self.function, self.cases, expected_public=len(self.examples)
        )

    def reference_job(self, label: str) -> ex.Job:
        reference = self.reference
        return ex.Job(label, reference.source or "", reference.function or "", self.cases, False)


@dataclass(frozen=True)
class Catalog:
    catalog_id: str
    directory: Path
    meta: dict[str, Any]
    programs_sha256: str
    license_sha256: str
    programs: tuple[Program, ...]

    def program(self, program_id: str) -> Program:
        for program in self.programs:
            if program.program_id == program_id:
                return program
        raise cv.RepairRefusal(
            cv.FINDING_PROGRAM_NOT_FOUND, f"no program {cv.shown(program_id)} in the catalog"
        )


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def function_defs(text: str, function: str) -> list[ast.FunctionDef]:
    """Every module-level ``def`` named ``function`` in ``text``, in order."""

    return [
        node for node in ast.parse(text).body
        if isinstance(node, ast.FunctionDef) and node.name == function
    ]


def function_node(text: str, function: str) -> ast.FunctionDef | None:
    """The module-level ``def`` named ``function`` in ``text``, or None.

    When the name is bound more than once, the last definition matches import
    semantics; catalog loading refuses the duplicate before this is relied on.
    """

    found = function_defs(text, function)
    return found[-1] if found else None


def examples_of(text: str, function: str) -> tuple[Example, ...]:
    """The doctest examples of the target function's docstring, in order."""

    node = function_node(text, function)
    if node is None:
        return ()
    docstring = ast.get_docstring(node, clean=True) or ""
    parsed = doctest.DocTestParser().get_examples(docstring)  # ValueError on a bad directive
    for item in parsed:
        if item.options.get(doctest.FAIL_FAST):
            raise ValueError("doctest FAIL_FAST directive stops row reporting")
    executable = [item for item in parsed if not item.options.get(doctest.SKIP)]
    return tuple(
        Example(f"{function}:{index}", item.source, item.want, item.exc_msg)
        for index, item in enumerate(executable)
    )


def examples_sha256(examples: tuple[Example, ...]) -> str:
    return sha256_text(oc.canonical_json([list(example.key()) for example in examples]))


from .catalog_load import load_catalog  # noqa: E402  types must exist first


# --- the original-passes check -------------------------------------------


def _finding(code: str, program: Program, detail: str) -> dict[str, str]:
    return {"code": code, "program_id": program.program_id, "detail": detail}


def _phase_code(report: ex.PhaseReport, timeout: str, error: str) -> str | None:
    if report.status == cv.PHASE_TIMEOUT:
        return timeout
    if not report.ok:
        return error
    return None


def _failing(rows: tuple[dict[str, Any], ...]) -> list[str]:
    return [row["id"] for row in rows if row["status"] != cv.ROW_SUCCESS]


def _execution_failure(program: Program, reports: tuple[ex.PhaseReport, ...]) -> dict | None:
    """The first run that timed out or did not load, as a finding."""

    for report in reports:
        code = _phase_code(report, cv.REASON_ORIGINAL_TIMEOUT, cv.REASON_ORIGINAL_HARNESS_ERROR)
        if code is not None:
            return _finding(code, program, report.detail)
    return None


def _suite_findings(program: Program, report: ex.PhaseReport) -> list[dict[str, str]]:
    suites = (
        (report.public, cv.REASON_ORIGINAL_FAILS_PUBLIC),
        (report.hidden, cv.REASON_ORIGINAL_FAILS_HIDDEN),
    )
    return [
        _finding(code, program, ", ".join(_failing(rows)))
        for rows, code in suites if _failing(rows)
    ]


def _original_findings(program: Program, executor: ex.Executor) -> list[dict[str, str]]:
    """Both runs must load and finish; the first must pass; the second must agree."""

    label = f"{cv.PHASE_ORIGINAL}:{program.program_id}"
    reports = (executor.run(program.job(label)), executor.run(program.job(label)))
    failure = _execution_failure(program, reports)
    if failure is not None:
        return [failure]
    first, second = reports
    findings = _suite_findings(program, first)
    if (first.public, first.hidden) != (second.public, second.hidden):
        findings.append(_finding(cv.CHECK_SOURCE_NONDETERMINISTIC, program, "two runs differ"))
    return findings


def _reference_findings(program: Program, executor: ex.Executor) -> list[dict[str, str]]:
    """Both certifying runs must load and finish; hidden rows must agree and match the pins."""

    if not program.reference.certifying:
        return []
    label = f"reference:{program.program_id}"
    reports = (executor.run(program.reference_job(label)), executor.run(program.reference_job(label)))
    for report in reports:
        code = _phase_code(report, cv.CHECK_REFERENCE_TIMEOUT, cv.CHECK_REFERENCE_HARNESS_ERROR)
        if code is not None:
            return [_finding(code, program, report.detail)]
    first, second = reports
    if first.hidden != second.hidden:
        return [_finding(cv.CHECK_SOURCE_NONDETERMINISTIC, program, "two reference runs differ")]
    disagreeing = _failing(first.hidden)
    if disagreeing or len(first.hidden) != len(program.cases):
        detail = ", ".join(disagreeing) or "row count"
        return [_finding(cv.CHECK_REFERENCE_DISAGREES, program, detail)]
    return []


def catalog_check(catalog: Catalog, executor: ex.Executor) -> list[dict[str, str]]:
    """Every original passes twice identically and its certifying reference agrees twice."""

    findings: list[dict[str, str]] = []
    for program in catalog.programs:
        findings += _original_findings(program, executor)
        findings += _reference_findings(program, executor)
    return findings


bind_import_twin(__name__)
