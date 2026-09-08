#!/usr/bin/env python3
"""The verdict: a pure decision table over the execution phases, plus the evidence it exposes.

Rules run in order and the first that holds decides; every code is declared
in the family vocabulary. Nothing here executes code or reads a record's own
stamps: an exporter re-derives every stored verdict from the stored rows with
the same function, and a replay re-derives it from fresh rows. Verdict codes
say what was observed ("no observed failure"), never what is unknowable.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from . import catalog as cat
from . import executor as ex
from . import vocabulary as cv
from ._contract import bind_import_twin, oc

__all__ = [
    "DecisionContext", "Phases", "Verdict", "decide", "failing_ids", "phase_block",
    "pre_repair_problem", "public_evidence", "render_evidence", "result_hash", "tests_tampered",
]


@dataclass(frozen=True)
class Phases:
    original: ex.PhaseReport
    mutant: ex.PhaseReport | None = None
    repaired: ex.PhaseReport | None = None


@dataclass(frozen=True)
class DecisionContext:
    """What the verdict needs beyond the rows: the reference kind and the two static guards."""

    reference_kind: str
    repair_restores: bool
    tests_tampered: bool
    hidden_case_count: int


@dataclass(frozen=True)
class Verdict:
    outcome: str
    reason_codes: tuple[str, ...]
    oracle_status: str

    @property
    def accepted(self) -> bool:
        return self.outcome == cv.OUTCOME_ACCEPTED


def failing_ids(rows: tuple[dict[str, Any], ...]) -> tuple[str, ...]:
    return tuple(row["id"] for row in rows if row["status"] != cv.ROW_SUCCESS)


def _phase_code(report: ex.PhaseReport | None, timeout: str, error: str) -> str | None:
    if report is not None and report.status == cv.PHASE_TIMEOUT:
        return timeout
    if report is None or not report.ok:
        return error
    return None


def _original_problem(original: ex.PhaseReport) -> str | None:
    code = _phase_code(original, cv.REASON_ORIGINAL_TIMEOUT, cv.REASON_ORIGINAL_HARNESS_ERROR)
    if code is not None:
        return code
    if failing_ids(original.public):
        return cv.REASON_ORIGINAL_FAILS_PUBLIC
    if failing_ids(original.hidden):
        return cv.REASON_ORIGINAL_FAILS_HIDDEN
    return None


def _mutant_problem(mutant: ex.PhaseReport | None, context: DecisionContext) -> str | None:
    code = _phase_code(mutant, cv.REASON_MUTANT_TIMEOUT, cv.REASON_MUTANT_HARNESS_ERROR)
    if code is not None:
        return code
    public_failed = bool(failing_ids(mutant.public))
    hidden_failed = bool(failing_ids(mutant.hidden))
    if not public_failed and not hidden_failed:
        return cv.REASON_MUTANT_NO_OBSERVED_FAILURE
    if not public_failed:
        return cv.REASON_MUTANT_NO_PUBLIC_FAILURE
    if not hidden_failed and context.hidden_case_count:
        return cv.REASON_MUTANT_NO_HIDDEN_FAILURE
    return None


def _repair_problem(repaired: ex.PhaseReport | None) -> str | None:
    code = _phase_code(repaired, cv.REASON_REPAIR_TIMEOUT, cv.REASON_REPAIR_HARNESS_ERROR)
    if code is not None:
        return code
    if failing_ids(repaired.public):
        return cv.REASON_REPAIR_FAILS_PUBLIC
    if failing_ids(repaired.hidden):
        return cv.REASON_REPAIR_FAILS_HIDDEN
    return None


def pre_repair_problem(phases: Phases, context: DecisionContext) -> str | None:
    """The first rule that rejects before the repaired phase needs to run, or None."""

    problem = _original_problem(phases.original) or _mutant_problem(phases.mutant, context)
    if problem is not None:
        return problem
    if not context.repair_restores:
        return cv.REASON_REPAIR_DOES_NOT_RESTORE
    if context.tests_tampered:
        return cv.REASON_PUBLIC_TESTS_TAMPERED
    return None


def _oracle_status(phases: Phases, context: DecisionContext) -> str:
    if _original_problem(phases.original) is not None:
        return cv.STATUS_INVALID
    if context.reference_kind in cv.CERTIFYING_REFERENCE_KINDS and context.hidden_case_count:
        return cv.STATUS_VALIDATED
    return cv.STATUS_PROVISIONAL


def decide(phases: Phases, context: DecisionContext) -> Verdict:
    """The verdict over complete phases: pure, so it can be re-derived from stored rows."""

    status = _oracle_status(phases, context)
    problem = pre_repair_problem(phases, context) or _repair_problem(phases.repaired)
    if problem is not None:
        return Verdict(cv.OUTCOME_REJECTED, (problem,), status)
    reasons = [cv.REASON_MUTANT_FAILS_PUBLIC]
    if failing_ids(phases.mutant.hidden):
        reasons.append(cv.REASON_MUTANT_FAILS_HIDDEN)
    reasons.append(cv.REASON_REPAIR_PASSES_ALL)
    if status != cv.STATUS_VALIDATED:
        reasons.append(cv.REASON_HIDDEN_CHECK_UNAVAILABLE)
    return Verdict(cv.OUTCOME_ACCEPTED, tuple(reasons), status)


def tests_tampered(examples: tuple[cat.Example, ...], repaired_text: str, function: str) -> bool:
    """True unless the repaired module's doctest examples are exactly the catalog's."""

    try:
        repaired = cat.examples_of(repaired_text, function)
    except (SyntaxError, ValueError):
        return True
    return [e.key() for e in repaired] != [e.key() for e in examples]


def phase_block(report: ex.PhaseReport | None) -> dict[str, Any] | None:
    """The digestable form of one phase: statuses and ``{id, status}`` rows only."""

    if report is None:
        return None
    public, hidden = ex.rows_of(report.public), ex.rows_of(report.hidden)
    block = {"status": report.status, "load_ok": report.load_ok, "public": public, "hidden": hidden}
    block["sha256"] = cat.sha256_text(oc.canonical_json([public, hidden]))
    return block


def result_hash(phases_block: dict[str, Any]) -> str:
    return cat.sha256_text(oc.canonical_json(phases_block))


def _example_index(row_id: str) -> int:
    return int(row_id.rpartition(":")[2])


def _entry(row: dict[str, Any], example: cat.Example) -> dict[str, Any]:
    return {
        "example_id": example.example_id, "source": example.source, "want": example.want,
        "got": row.get("got", ""), "truncated": bool(row.get("truncated", False)),
    }


def _fits(entries: list[dict[str, Any]], entry: dict[str, Any]) -> bool:
    if not entries:
        return True
    if len(entries) >= cv.MAX_EVIDENCE_EXAMPLES:
        return False
    return len(render_evidence(entries + [entry], 0)) <= cv.MAX_EVIDENCE_CHARS


def public_evidence(
    mutant: ex.PhaseReport, examples: tuple[cat.Example, ...]
) -> tuple[list[dict[str, Any]], int]:
    """The failing public examples of the mutant, bounded: ``(entries, omitted_count)``."""

    failing = [row for row in mutant.public if row["status"] != cv.ROW_SUCCESS]
    entries: list[dict[str, Any]] = []
    for row in sorted(failing, key=lambda r: _example_index(r["id"])):
        entry = _entry(row, examples[_example_index(row["id"])])
        if not _fits(entries, entry):
            break
        entries.append(entry)
    if entries and len(render_evidence(entries, 0)) > cv.MAX_EVIDENCE_CHARS:
        excess = len(render_evidence(entries, 0)) - cv.MAX_EVIDENCE_CHARS
        entries[0]["got"] = entries[0]["got"][: max(0, len(entries[0]["got"]) - excess)]
        entries[0]["truncated"] = True
    return entries, len(failing) - len(entries)


def _indent(text: str) -> str:
    lines = text.rstrip("\n").split("\n") if text.strip() else []
    return "\n".join(f"    {line}" for line in lines)


def _render_entry(entry: dict[str, Any]) -> str:
    want = _indent(entry["want"]) if entry["want"].strip() else "Expected nothing"
    got = _indent(entry["got"]) if entry["got"].strip() else "Got nothing"
    if entry["truncated"]:
        got += "\n    ...[truncated]"
    expected_line = "Expected:\n" if want != "Expected nothing" else ""
    got_line = "Got:\n" if got != "Got nothing" else ""
    return f"Failed example:\n{_indent(entry['source'])}\n{expected_line}{want}\n{got_line}{got}"


def render_evidence(entries: list[dict[str, Any]], omitted: int) -> str:
    """The prompt's failure block: doctest-style, from the bounded entries only."""

    parts = [_render_entry(entry) for entry in entries]
    if omitted:
        parts.append(cv.EVIDENCE_MORE.format(count=omitted))
    return "\n\n".join(parts)


bind_import_twin(__name__)
