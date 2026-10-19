#!/usr/bin/env python3
"""The gate: one verdict per proposal, procedural or model-backed, through one code path.

Evaluation order, first failing rule wins:

1. ``denylisted`` -- the program id is on the eval denylist (checked first so eval programs are
   never parsed or executed on behalf of a proposal).
2. ``parse_error`` -- the row is malformed, the program is unknown, the edit does not resolve
   to exactly one span inside the target body (outside the docstring), the mutant does not
   compile, does not load, or kills the interpreter.
3. ``duplicate`` -- ``sha256(program_id, span, replacement_text)`` was kept in a prior run or
   earlier in this one.
4. ``original_fails`` -- the unmodified program does not pass all of its doctests (or has none).
5. ``timeout`` -- the mutant exceeded the wall-clock budget (rejected, never kept).
6. ``mutant_passes`` -- the mutant passes every doctest.
7. ``kept`` -- the mutant fails at least one doctest.
"""

from __future__ import annotations

import hashlib
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any, NamedTuple, Protocol

from . import mutation
from . import vocabulary as cv
from ._contract import bind_import_twin
from .dedup_index import PriorIndex, dedup_key
from .denylist import Denylist
from .harness import HarnessResult
from .proposal import GateProgram, GateProposal, MalformedProposal

__all__ = ["Decision", "Gate", "Harness", "Rules"]


class Harness(Protocol):
    def run(self, program_text: str, function: str) -> HarnessResult: ...


@dataclass(frozen=True)
class Decision:
    """One proposal's verdict and the evidence behind it; ``as_row`` is the tasks.jsonl row."""

    proposal_id: str
    program_id: str | None
    source: str | None
    verdict: str
    detail: str
    start_byte: int | None = None
    end_byte: int | None = None
    original_text: str | None = None
    replacement_text: str | None = None
    dedup_key: str | None = None
    program_sha256: str | None = None
    mutant_sha256: str | None = None
    doctests: Mapping[str, int] | None = None

    def as_row(self) -> dict[str, Any]:
        row = {
            "format": cv.TASKS_FORMAT, "proposal_id": self.proposal_id,
            "program_id": self.program_id, "source": self.source, "verdict": self.verdict,
            "detail": self.detail, "start_byte": self.start_byte, "end_byte": self.end_byte,
            "original_text": self.original_text, "replacement_text": self.replacement_text,
            "dedup_key": self.dedup_key, "program_sha256": self.program_sha256,
            "mutant_sha256": self.mutant_sha256, "doctests": dict(self.doctests or {}),
        }
        return row


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _original_problem(result: HarnessResult) -> str | None:
    if result.outcome == cv.OUTCOME_PASSED:
        return None if result.attempted > 0 else cv.DETAIL_NO_DOCTESTS
    return {
        cv.OUTCOME_FAILED: cv.DETAIL_ORIGINAL_FAILED,
        cv.OUTCOME_LOAD_ERROR: cv.DETAIL_ORIGINAL_LOAD_ERROR,
        cv.OUTCOME_TIMEOUT: cv.DETAIL_ORIGINAL_TIMEOUT,
    }.get(result.outcome, cv.DETAIL_ORIGINAL_CRASHED)


_MUTANT_VERDICTS = {
    cv.OUTCOME_FAILED: (cv.VERDICT_KEPT, cv.DETAIL_MUTANT_FAILED_DOCTESTS),
    cv.OUTCOME_PASSED: (cv.VERDICT_MUTANT_PASSES, cv.DETAIL_MUTANT_PASSED_ALL),
    cv.OUTCOME_TIMEOUT: (cv.VERDICT_TIMEOUT, cv.DETAIL_MUTANT_TIMEOUT),
    cv.OUTCOME_LOAD_ERROR: (cv.VERDICT_PARSE_ERROR, cv.DETAIL_MUTANT_LOAD_ERROR),
}


class Rules(NamedTuple):
    """What a run is judged against: the required eval denylist and the prior-run index."""

    denylist: Denylist
    prior: PriorIndex


def _check_rules(rules: Rules) -> None:
    cv.refuse_when(
        not isinstance(rules.denylist, Denylist) or not len(rules.denylist),
        cv.REFUSE_DENYLIST_MISSING, "the gate needs a loaded, non-empty eval denylist",
    )
    cv.refuse_when(
        not isinstance(rules.prior, PriorIndex), cv.REFUSE_INDEX_MALFORMED, "prior index not loaded",
    )


def _check_programs(programs: Mapping[str, GateProgram]) -> None:
    bad = [pid for pid, program in programs.items() if program.program_id != pid]
    cv.refuse_when(bool(bad), cv.REFUSE_PROGRAM_INVALID, f"program key/id mismatch: {bad[:1]}")


class Gate:
    """Holds the programs, the required rules and the harness for one run."""

    def __init__(self, programs: Mapping[str, GateProgram], rules: Rules, harness: Harness) -> None:
        _check_rules(rules)
        _check_programs(programs)
        selfcheck = getattr(harness, "selfcheck", None)
        if callable(selfcheck):
            selfcheck()
        self.programs, self.harness = programs, harness
        self.denylist, self.prior = rules.denylist, rules.prior
        self.kept: dict[str, dict[str, Any]] = {}
        self._originals: dict[str, str | None] = {}
        self._mutants: dict[str, HarnessResult] = {}

    def run(self, items: Iterable[GateProposal | MalformedProposal]) -> list[Decision]:
        return [self.decide(item) for item in items]

    def decide(self, item: GateProposal | MalformedProposal) -> Decision:
        source = item.source if isinstance(item, GateProposal) else None
        if item.program_id is not None and item.program_id in self.denylist:
            return Decision(item.proposal_id, item.program_id, source, cv.VERDICT_DENYLISTED,
                            cv.DETAIL_ON_DENYLIST)
        if isinstance(item, MalformedProposal):
            return Decision(item.proposal_id, item.program_id, None, cv.VERDICT_PARSE_ERROR, item.detail)
        program = self.programs.get(item.program_id)
        if program is None:
            return Decision(item.proposal_id, item.program_id, source, cv.VERDICT_PARSE_ERROR,
                            cv.DETAIL_UNKNOWN_PROGRAM)
        resolved = mutation.resolve(program, item)
        if isinstance(resolved, str):
            return Decision(item.proposal_id, item.program_id, source, cv.VERDICT_PARSE_ERROR, resolved)
        return self._verify(item, program, resolved)

    def _verify(
        self, item: GateProposal, program: GateProgram, resolved: mutation.Resolved,
    ) -> Decision:
        key, edit_start, edit_end = dedup_key(item.program_id, program.text, resolved.mutant_text)
        base = {
            "proposal_id": item.proposal_id, "program_id": item.program_id, "source": item.source,
            "start_byte": resolved.start, "end_byte": resolved.end,
            "original_text": resolved.original_text, "replacement_text": item.replacement_text,
            "dedup_key": key, "program_sha256": _sha(program.text),
        }
        if key in self.prior or key in self.kept:
            detail = cv.DETAIL_PRIOR_RUN if key in self.prior else cv.DETAIL_THIS_RUN
            return Decision(verdict=cv.VERDICT_DUPLICATE, detail=detail, **base)
        problem = self._original(program)
        if problem is not None:
            return Decision(verdict=cv.VERDICT_ORIGINAL_FAILS, detail=problem, **base)
        result = self._mutant(key, program, resolved)
        verdict, detail = _MUTANT_VERDICTS.get(
            result.outcome, (cv.VERDICT_PARSE_ERROR, cv.DETAIL_MUTANT_CRASHED),
        )
        decision = Decision(
            verdict=verdict, detail=detail, mutant_sha256=_sha(resolved.mutant_text),
            doctests={"attempted": result.attempted, "failed": result.failed}, **base,
        )
        if verdict == cv.VERDICT_KEPT:
            self.kept[key] = {
                "format": cv.INDEX_FORMAT, "key": key, "program_id": item.program_id,
                "start_byte": edit_start, "end_byte": edit_end,
            }
        return decision

    def _original(self, program: GateProgram) -> str | None:
        if program.program_id not in self._originals:
            result = self.harness.run(program.text, program.function)
            self._originals[program.program_id] = _original_problem(result)
        return self._originals[program.program_id]

    def _mutant(self, key: str, program: GateProgram, resolved: mutation.Resolved) -> HarnessResult:
        if key not in self._mutants:
            self._mutants[key] = self.harness.run(resolved.mutant_text, program.function)
        return self._mutants[key]


bind_import_twin(__name__)
