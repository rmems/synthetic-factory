#!/usr/bin/env python3
"""Tests for shared code review preference tail sequences."""

from __future__ import annotations

import sys
import unittest
from dataclasses import dataclass
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PIPELINES = REPO / "pipelines"

sys.path.insert(0, str(PIPELINES))

import code_review_preference_tail as crp_tail  # noqa: E402
from pipelines import code_review_preference_tail as crp_tail_pkg  # noqa: E402


@dataclass(frozen=True)
class DummyPlant:
    repo: str = "rmems/mock-repo"
    core: str = "src/core.py"
    test: str = "tests/test_core.py"
    line: int = 42
    defect: str = "unauthenticated admin endpoint"
    fix: str = "require session token"
    missing: str = "tests unauthenticated access"
    nit: str = "handler"


class CodeReviewPreferenceTailTests(unittest.TestCase):
    def setUp(self):
        self.plant = DummyPlant()
        self.pr = 1901
        self.rid = 901901

    def test_direct_and_package_import_are_one_module(self):
        self.assertIs(crp_tail, crp_tail_pkg)

    def test_chosen_tail_structure_and_safe_repro_path(self):
        steps = crp_tail.chosen_tail(self.plant, self.pr, self.rid)
        self.assertEqual(len(steps), 6)
        step_numbers = [s["n"] for s in steps]
        self.assertEqual(step_numbers, [8, 9, 10, 11, 12, 13])

        repro_step = steps[2]
        self.assertEqual(repro_step["n"], 10)
        self.assertEqual(repro_step["tool_call"]["name"], "write_file")
        path = repro_step["tool_call"]["args"]["path"]
        self.assertEqual(path, f".synthetic-factory/repros/pr{self.pr}-blocking-repro.txt")
        self.assertFalse(path.startswith(f"/{'tmp'}/"))
        self.assertIn("reflection", repro_step)
        self.assertIn("observation", repro_step)

        first_step = steps[0]
        self.assertIn("REQUEST_CHANGES", first_step["tool_call"]["args"]["command"])
        self.assertIn(self.plant.defect, first_step["tool_call"]["args"]["command"])

    def test_rejected_tail_structure_and_steps(self):
        steps = crp_tail.rejected_tail(self.plant, self.pr)
        self.assertEqual(len(steps), 5)
        step_numbers = [s["n"] for s in steps]
        self.assertEqual(step_numbers, [8, 9, 10, 11, 12])

        review_step = steps[2]
        self.assertEqual(review_step["n"], 10)
        self.assertIn("APPROVE", review_step["tool_call"]["args"]["command"])


if __name__ == "__main__":
    unittest.main()
