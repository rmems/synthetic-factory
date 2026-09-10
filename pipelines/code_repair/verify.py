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
from .evidence import public_evidence, render_evidence
from ._contract import bind_import_twin, oc

__all__ = [
    "DecisionContext", "Phases", "Verdict", "decide", "failing_ids", "phase_block",
    "pre_repair_problem", "public_evidence", "render_evidence", "result_hash", "tests_tampered",
    "phases_from_blocks",
]


@dataclass(frozen=True)
class Phases:
    """The executed phases; ``reference`` is the certifying reference over the hidden cases."""

    original: ex.PhaseReport
    mutant: ex.PhaseReport | None = None
    repaired: ex.PhaseReport | None = None
    reference: ex.PhaseReport | None = None
    original_repeat: ex.PhaseReport | None = None


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
    if report is None or not report.ok or report.environment.get("limits_applied") is not True:
        return error
    return None


def _original_problem(original: ex.PhaseReport) -> str | None:
    code = _phase_code(original, cv.REASON_ORIGINAL_TIMEOUT, cv.REASON_ORIGINAL_HARNESS_ERROR)
    if code is not None:
        return code
    if not original.public:
        # A program with no public example cannot show a failure; the catalog refuses it too.
        return cv.REASON_ORIGINAL_HARNESS_ERROR
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
    rules = ((not public_failed and not hidden_failed, cv.REASON_MUTANT_NO_OBSERVED_FAILURE),
             (not public_failed, cv.REASON_MUTANT_NO_PUBLIC_FAILURE),
             (not hidden_failed and context.hidden_case_count, cv.REASON_MUTANT_NO_HIDDEN_FAILURE))
    return next((reason for holds, reason in rules if holds), None)


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

    problem = _source_problem(phases) or _mutant_problem(phases.mutant, context)
    if problem is not None:
        return problem
    if not context.repair_restores:
        return cv.REASON_REPAIR_DOES_NOT_RESTORE
    if context.tests_tampered:
        return cv.REASON_PUBLIC_TESTS_TAMPERED
    return None


def _source_problem(phases: Phases) -> str | None:
    problem = _original_problem(phases.original)
    if problem is not None:
        return problem
    if phases.original_repeat is None:
        return cv.REASON_SOURCE_NONDETERMINISTIC
    if phase_block(phases.original) != phase_block(phases.original_repeat):
        return cv.REASON_SOURCE_NONDETERMINISTIC
    return None


def _reference_certifies(phases: Phases, context: DecisionContext) -> bool:
    """A certifying reference that was executed in this run and answered every pinned case."""

    reference = phases.reference
    if context.reference_kind not in cv.CERTIFYING_REFERENCE_KINDS or not context.hidden_case_count:
        return False
    if reference is None or not reference.ok or reference.environment.get("limits_applied") is not True:
        return False
    return len(reference.hidden) == context.hidden_case_count and not failing_ids(reference.hidden)


def _oracle_status(phases: Phases, context: DecisionContext) -> str:
    if _source_problem(phases) is not None:
        return cv.STATUS_INVALID
    if _reference_certifies(phases, context):
        return cv.STATUS_VALIDATED
    return cv.STATUS_PROVISIONAL


def _uncertified_reason(context: DecisionContext) -> str:
    """Why an accepted record is only provisional: no reference, or one that did not certify."""

    if context.reference_kind in cv.CERTIFYING_REFERENCE_KINDS and context.hidden_case_count:
        return cv.REASON_REFERENCE_NOT_CERTIFYING
    return cv.REASON_HIDDEN_CHECK_UNAVAILABLE


def decide(phases: Phases, context: DecisionContext) -> Verdict:
    """The verdict over complete phases: pure, so it can be re-derived from stored rows."""

    status = _oracle_status(phases, context)
    problem = pre_repair_problem(phases, context) or _repair_problem(phases.repaired)
    if problem is None and phase_block(phases.original) != phase_block(phases.repaired):
        problem = cv.REASON_SOURCE_NONDETERMINISTIC
        status = cv.STATUS_INVALID
    if problem is not None:
        return Verdict(cv.OUTCOME_REJECTED, (problem,), status)
    reasons = [cv.REASON_MUTANT_FAILS_PUBLIC]
    if phases.mutant is not None and failing_ids(phases.mutant.hidden):
        reasons.append(cv.REASON_MUTANT_FAILS_HIDDEN)
    reasons.append(cv.REASON_REPAIR_PASSES_ALL)
    if status != cv.STATUS_VALIDATED:
        reasons.append(_uncertified_reason(context))
    return Verdict(cv.OUTCOME_ACCEPTED, tuple(reasons), status)


def tests_tampered(examples: tuple[cat.Example, ...], repaired_text: str, function: str) -> bool:
    """True unless the repaired module's doctest examples are exactly the catalog's."""

    try:
        repaired = cat.examples_of(repaired_text, function)
    except (SyntaxError, ValueError):
        return True
    return [e.key() for e in repaired] != [e.key() for e in examples]


def phase_block(report: ex.PhaseReport | None) -> dict[str, Any] | None:
    """Stable source, limits, status and observation evidence for one executed phase."""

    if report is None:
        return None
    public, hidden = ex.rows_of(report.public), ex.rows_of(report.hidden)
    block = {"status": report.status, "load_ok": report.load_ok, "public": public, "hidden": hidden}
    block["module_sha256"] = report.module_sha256
    block["limits_applied"] = report.environment.get("limits_applied")
    block["sha256"] = cat.sha256_text(oc.canonical_json([public, hidden]))
    return block


def phases_from_blocks(blocks: dict[str, Any]) -> Phases:
    """Reconstruct complete stable reports; callers validate their family shape first."""
    reports = {}
    for phase in cv.PHASES:
        block = blocks[phase]
        reports[phase] = None if block is None else ex.PhaseReport(
            block["status"], block["load_ok"], tuple(block["public"]), tuple(block["hidden"]),
            {"limits_applied": block["limits_applied"]}, module_sha256=block["module_sha256"])
    return Phases(**reports)


def result_hash(phases_block: dict[str, Any]) -> str:
    return cat.sha256_text(oc.canonical_json(phases_block))


bind_import_twin(__name__)
