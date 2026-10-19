#!/usr/bin/env python3
"""Shared fixtures for the ``test_task_gate*`` modules: programs, proposals and a fake harness."""

import sys
from pathlib import Path

TESTS = Path(__file__).resolve().parent
REPO = TESTS.parent
sys.path[:0] = [str(REPO / "pipelines")]

# Re-exported for the test modules (``name as name`` marks an explicit re-export).
from task_gate import dedup_index as dedup_index
from task_gate import denylist as denylist
from task_gate import gate as gate
from task_gate import harness as harness
from task_gate import mutation as mutation
from task_gate import procedural as procedural
from task_gate import proposal as proposal
from task_gate import report as report
from task_gate import runner as runner
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


def rules(deny=DENY, prior=None):
    """The gate's rules: the denylist and a prior index (empty unless given)."""

    return gate.Rules(deny, dedup_index.PriorIndex.empty() if prior is None else prior)


def refused(call, *args):
    """The refusal code ``call(*args)`` raises, or None when it does not refuse.

    Callers build every argument first, so the only call that can raise is the one under test.
    """

    try:
        call(*args)
    except cv.GateRefusal as exc:
        return exc.code
    return None


def span_of(text, needle):
    """``(start_byte, end_byte)`` of the only occurrence of ``needle`` in ``text``."""

    if text.count(needle) != 1:
        raise ValueError(f"{needle!r} must occur exactly once in the program text")
    start = len(text[: text.index(needle)].encode("utf-8"))
    return start, start + len(needle.encode("utf-8"))


def proposal_for(replacement="a - b", needle="a + b", program=PROGRAM, **fields):
    """An explicit-offset proposal over ``program``; extra keyword fields override."""

    start, end = span_of(program.text, needle)
    values = {
        "proposal_id": f"p-{program.program_id}-{start}-{replacement}",
        "program_id": program.program_id, "replacement_text": replacement, "source": "model",
        "original_text": needle, "start_byte": start, "end_byte": end,
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
