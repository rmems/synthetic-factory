#!/usr/bin/env python3
"""catalog-check: every original passes twice identically, references agree, pins hold.

The loader (``catalog``) proves a catalog's files are what they claim; this
module proves what they claim is true: each original answers its own examples
and pinned cases in two runs that agree, each certifying reference answers the
same cases, and the structure digests, groups and splits recomputed from the
module texts match the pinned ones.
"""

from __future__ import annotations

from typing import Any, NamedTuple

from . import catalog as cat
from . import executor as ex
from . import lineage
from . import vocabulary as cv
from ._contract import bind_import_twin

__all__ = ["catalog_check", "catalog_structure_findings", "original_findings", "phase_code"]


def _finding(code: str, program: cat.Program, detail: str) -> dict[str, str]:
    return {"code": code, "program_id": program.program_id, "detail": detail}


def phase_code(report: ex.PhaseReport, timeout: str, error: str) -> str | None:
    if report.status == cv.PHASE_TIMEOUT:
        return timeout
    if not report.ok:
        return error
    return None


def _failing(rows: tuple[dict[str, Any], ...]) -> list[str]:
    return [row["id"] for row in rows if row["status"] != cv.ROW_SUCCESS]


def _execution_failure(program: cat.Program, reports: tuple[ex.PhaseReport, ...]) -> dict | None:
    """The first run that timed out or did not load, as a finding."""

    for report in reports:
        code = phase_code(report, cv.REASON_ORIGINAL_TIMEOUT, cv.REASON_ORIGINAL_HARNESS_ERROR)
        if code is not None:
            return _finding(code, program, report.detail)
    return None


def _suite_findings(program: cat.Program, report: ex.PhaseReport) -> list[dict[str, str]]:
    suites = (
        (report.public, cv.REASON_ORIGINAL_FAILS_PUBLIC),
        (report.hidden, cv.REASON_ORIGINAL_FAILS_HIDDEN),
    )
    return [
        _finding(code, program, ", ".join(_failing(rows)))
        for rows, code in suites
        if _failing(rows)
    ]


def original_findings(program: cat.Program, executor: ex.Executor) -> list[dict[str, str]]:
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


def _reference_findings(program: cat.Program, executor: ex.Executor) -> list[dict[str, str]]:
    if not program.reference.certifying:
        return []
    report = executor.run(program.reference_job(f"reference:{program.program_id}"))
    code = phase_code(report, cv.CHECK_REFERENCE_TIMEOUT, cv.CHECK_REFERENCE_HARNESS_ERROR)
    if code is not None:
        return [_finding(code, program, report.detail)]
    disagreeing = _failing(report.hidden)
    if disagreeing or len(report.hidden) != len(program.cases):
        detail = ", ".join(disagreeing) or "row count"
        return [_finding(cv.CHECK_REFERENCE_DISAGREES, program, detail)]
    return []


def catalog_structure_findings(catalog: cat.Catalog) -> list[dict[str, str]]:
    """Groups and splits recomputed from the module texts must match the pinned ones."""

    digests = {p.program_id: lineage.structure_digest(p.text) for p in catalog.programs}
    members = tuple(
        lineage.Member(p.program_id, p.upstream["path"], digests[p.program_id])
        for p in catalog.programs
    )
    groups = lineage.group_ids(members)
    findings: list[dict[str, str]] = []
    for program in catalog.programs:
        expected = _Structure(digests[program.program_id], groups[program.program_id], None)
        findings += _program_structure_findings(program, expected, catalog.split_policy)
    return findings + _empty_split_findings(catalog)


_structure_findings = catalog_structure_findings


class _Structure(NamedTuple):
    ast_digest: str
    group_id: str
    split: str | None


def _pin_findings(program: cat.Program, pinned: _Structure, expected: _Structure) -> list[dict]:
    """A pin that is present must match; with a split policy every pin must be present."""

    codes = (cv.CHECK_STRUCTURE_DIGEST_DRIFT, cv.CHECK_GROUP_DRIFT, cv.CHECK_SPLIT_DRIFT)
    findings = []
    for code, have, want in zip(codes, pinned, expected):
        if want is not None and have != want:
            findings.append(_finding(code, program, "missing" if have is None else want))
    return findings


def _program_structure_findings(
    program: cat.Program, expected: _Structure, policy: lineage.SplitPolicy | None
) -> list[dict[str, str]]:
    pinned = _Structure(program.ast_digest, program.group_id, program.split)
    if policy is None:
        # Without a policy a pin is optional; a present pin must still match (Codex on #202).
        optional = _Structure(
            expected.ast_digest if pinned.ast_digest is not None else None,
            expected.group_id if pinned.group_id is not None else None, None,
        )
        return _pin_findings(program, pinned, optional)
    anchor = lineage.anchor_for(expected.group_id, program.program_id)
    required = expected._replace(split=lineage.bucket_split(anchor, policy))
    return _pin_findings(program, pinned, required)


def _empty_split_findings(catalog: cat.Catalog) -> list[dict[str, str]]:
    if catalog.split_policy is None:
        return []
    present = {p.split for p in catalog.programs}
    weights = catalog.split_policy.weights
    missing = [name for name in lineage.SPLITS if weights[name] > 0 and name not in present]
    if not missing:
        return []
    where = cat.CATALOG_FILENAME
    detail = f"no program falls into {', '.join(missing)}; change the salt in {where}"
    return [{"code": cv.CHECK_SPLIT_EMPTY, "program_id": "*", "detail": detail}]


def catalog_check(catalog: cat.Catalog, executor: ex.Executor) -> list[dict[str, str]]:
    """Every original passes twice identically, references agree, groups and splits hold."""

    findings: list[dict[str, str]] = []
    for program in catalog.programs:
        findings += original_findings(program, executor)
        findings += _reference_findings(program, executor)
    return findings + catalog_structure_findings(catalog)


bind_import_twin(__name__)
