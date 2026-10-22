#!/usr/bin/env python3
"""Shared fixtures for the ``test_task_gate_band*`` modules: a gate run, contracts and a solver."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from task_gate_test_support import (
    ADD, DENY, PASSED, PROGRAMS, FakeHarness, proposal_for, cv,
)
from task_gate import band_run, runner
from task_gate import band_vocabulary as bv

REPLACEMENTS = ("a - b", "a * b", "b", "a", "a + b + 1")
STUDENT_PASSES = FakeHarness({ADD: PASSED})


def contract_document(attempts=10, low=0.1, high=0.9):
    return {
        "format": bv.CONTRACT_FORMAT, "attempts_per_task": attempts,
        "pass_rate_min": low, "pass_rate_max": high,
    }


ALIASES = {"attempts": "attempts_per_task", "low": "pass_rate_min", "high": "pass_rate_max"}


def write_contract(root, name="contract.json", **fields):
    """Write a valid contract with ``fields`` overriding it (``attempts``/``low``/``high`` or raw keys)."""

    path = Path(root) / name
    document = {**contract_document(), **{ALIASES.get(k, k): v for k, v in fields.items()}}
    path.write_text(json.dumps(document), encoding="utf-8")
    return path


def gate_tasks(root, replacements=REPLACEMENTS, extra=()):
    """Run the real task gate (fake harness) and return the path of its ``tasks.jsonl``."""

    proposals = [proposal_for(text) for text in replacements] + list(extra)
    out = Path(root) / "gate"
    runner.run(runner.GateRequest(PROGRAMS, proposals, DENY, out), FakeHarness({ADD: PASSED}))
    return out / cv.TASKS_FILENAME


def proposal_ids(tasks_path, verdict=cv.VERDICT_KEPT):
    rows = [json.loads(line) for line in Path(tasks_path).read_text().splitlines()]
    return [row["proposal_id"] for row in rows if row["verdict"] == verdict]


class ScriptedSolver:
    """Deterministic student: the first ``wins[proposal_id]`` attempts return the fix."""

    def __init__(self, wins, default=0):
        self.wins, self.default, self.calls = dict(wins), default, []

    def solve(self, task, attempt):
        self.calls.append((task.proposal_id, attempt))
        if attempt < self.wins.get(task.proposal_id, self.default):
            return ADD
        return task.broken_text


def run_band(root, wins, contract=None, **fields):
    """Run the band stage over a fresh gate run; return (summary, out dir, solver)."""

    tasks = gate_tasks(root)
    ids = proposal_ids(tasks)
    solver = ScriptedSolver({ids[i]: n for i, n in wins.items()})
    request = band_run.BandRequest(
        programs=PROGRAMS, tasks_path=tasks, contract=contract or write_contract(root, **fields),
        out=Path(root) / "band", generator="self",
    )
    return band_run.run(request, solver, STUDENT_PASSES), Path(root) / "band", solver


def read_rows(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines()]
