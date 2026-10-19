#!/usr/bin/env python3
"""Shared fixtures for the ``test_task_gate*`` modules: programs, proposals and a fake harness."""

import sys
from pathlib import Path

TESTS = Path(__file__).resolve().parent
REPO = TESTS.parent
sys.path[:0] = [str(REPO / "pipelines")]

from task_gate import denylist, dedup_index, gate, harness, mutation, procedural, proposal, report
from task_gate import runner
from task_gate import vocabulary as cv

ADD = '''def add(a, b):
    """Add two numbers.

    >>> add(1, 2)
    3
    >>> add(0, 0)
    0
    """
    return a + b
'''
BROKEN = ADD.replace("return a + b", "return a - b")
NO_DOCTESTS = "def add(a, b):\n    return a + b\n"
PROGRAM = proposal.GateProgram("prog-add", ADD, "add")
EVAL_PROGRAM = proposal.GateProgram("prog-eval", ADD, "add")
PROGRAMS = {"prog-add": PROGRAM, "prog-eval": EVAL_PROGRAM}
DENY = denylist.Denylist.of(["prog-eval"])
PASSED = harness.HarnessResult(cv.OUTCOME_PASSED, 2, 0)
FAILED = harness.HarnessResult(cv.OUTCOME_FAILED, 2, 1)

__all__ = [
    "ADD", "BROKEN", "DENY", "FAILED", "FakeHarness", "NO_DOCTESTS", "PASSED", "PROGRAM",
    "PROGRAMS", "REPO", "TESTS", "cv", "dedup_index", "denylist", "gate", "harness", "mutation",
    "procedural", "proposal", "proposal_for", "report", "runner", "span_of",
]


def span_of(text, needle):
    """``(start_byte, end_byte)`` of the only occurrence of ``needle`` in ``text``."""

    assert text.count(needle) == 1, needle
    start = len(text[: text.index(needle)].encode("utf-8"))
    return start, start + len(needle.encode("utf-8"))


def proposal_for(replacement="a - b", needle="a + b", program_id="prog-add", text=ADD, **fields):
    """An explicit-offset proposal over ``text``; extra keyword fields override."""

    start, end = span_of(text, needle)
    values = {
        "proposal_id": f"p-{program_id}-{start}-{replacement}", "program_id": program_id,
        "replacement_text": replacement, "source": "model", "original_text": needle,
        "start_byte": start, "end_byte": end,
    }
    values.update(fields)
    return proposal.GateProposal(**values)


class FakeHarness:
    """Serves scripted results by program text and records every call."""

    def __init__(self, results=None, default=FAILED):
        self.results = dict(results or {})
        self.default = default
        self.calls = []

    def run(self, program_text, function):
        self.calls.append((program_text, function))
        return self.results.get(program_text, self.default)
