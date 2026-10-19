#!/usr/bin/env python3
"""The pluggable student: what a solver sees and how one attempt is scored.

A solver receives only the broken module (never the original program) and returns a
candidate module text. The stage, not the solver, decides success: the candidate must be a legal rewrite
of the target body (:func:`mutation.candidate_problem`, so it cannot edit the doctests) and the
reference harness must run it to a pass with at least one doctest attempted. A solver that
raises, or returns a non-string, fails closed or counts as a failed attempt respectively.

Real solver wiring (the student adapter, #160) is a follow-up: this module is the seam.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from . import band_vocabulary as bv
from . import mutation
from . import vocabulary as cv
from ._contract import bind_import_twin
from .gate import Harness
from .proposal import GateProgram

__all__ = ["BandTask", "Scorer", "Solver", "attempt_all"]


@dataclass(frozen=True)
class BandTask:
    """One verified task as the solver sees it: the broken module and its target function."""

    proposal_id: str
    program_id: str
    function: str
    broken_text: str


class Solver(Protocol):
    def solve(self, task: BandTask, attempt: int) -> str: ...


class Scorer:
    """Scores a candidate against the reference harness for one program."""

    def __init__(self, program: GateProgram, harness: Harness) -> None:
        self.program, self.harness = program, harness

    def passes(self, candidate: object) -> bool:
        if not isinstance(candidate, str) or "\x00" in candidate or "\r" in candidate:
            return False
        try:
            if mutation.candidate_problem(self.program, candidate) is not None:
                return False
        except (SyntaxError, ValueError, RecursionError):
            return False
        result = self.harness.run(candidate, self.program.function)
        return result.outcome == cv.OUTCOME_PASSED and result.attempted > 0


def _one(solver: Solver, task: BandTask, attempt: int) -> object:
    try:
        return solver.solve(task, attempt)
    except Exception as exc:  # a student crash must stop the run, never read as a failed attempt
        raise cv.GateRefusal(
            bv.REFUSE_SOLVER_FAILED, f"{task.proposal_id} attempt {attempt}: {type(exc).__name__}",
        ) from exc


def attempt_all(solver: Solver, task: BandTask, scorer: Scorer, attempts: int) -> int:
    """Run ``attempts`` independent attempts and return how many the harness scored a pass."""

    return sum(scorer.passes(_one(solver, task, attempt)) for attempt in range(attempts))


bind_import_twin(__name__)
