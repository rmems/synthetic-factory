#!/usr/bin/env python3
"""Mill-usage-burst plan slice A (``cer`` / cascading-error-recovery)."""

from __future__ import annotations

import ast
import subprocess
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "pipelines"))

import cer.plants_r1901 as plants_r1901  # noqa: E402
import cer.record_builder as cer_builder  # noqa: E402
from cer.usage_burst_plan import load_mill_usage_burst_plan  # noqa: E402
from cer import vocabulary as cv  # noqa: E402
from mill_reviewed_vocabulary import REVIEWED_MILL_PREFIX_HOMES  # noqa: E402


def _legacy_pairs(script_name: str) -> tuple[list, int, int]:
    src = subprocess.check_output(
        ["git", "show", f"origin/legacy-mill-lane:experiments/{script_name}"],
        text=True,
        cwd=REPO,
    )
    tree = ast.parse(src)
    ns: dict = {}
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id in ("PAIRS", "START", "N_ROUNDS"):
                    exec(ast.unparse(node), ns)
    return ns["PAIRS"], ns["START"], ns["N_ROUNDS"]


class CerMillUsageBurstTests(unittest.TestCase):
    def test_reviewed_prefix_maps_to_factory(self):
        self.assertEqual(REVIEWED_MILL_PREFIX_HOMES[cv.FAMILY_PREFIX], cv.FACTORY)

    def test_plan_loads_and_matches_plants(self):
        plan = load_mill_usage_burst_plan(repo_root=REPO)
        self.assertEqual(plan.slice, "A")
        self.assertEqual(plan.counts(), {"mills": 2, "rounds": 32, "pairs": 32, "episodes": 64})
        self.assertEqual([m.mill_id for m in plan.mills], ["cer_r1901", "cer_r1958"])

    def test_plants_r1901_matches_legacy_ast_extract(self):
        legacy_pairs, start, n_rounds = _legacy_pairs("cer_r1901_leftover3_mill.py")
        self.assertEqual(start, plants_r1901.START)
        self.assertEqual(n_rounds, plants_r1901.N_ROUNDS)
        self.assertEqual(len(legacy_pairs), len(plants_r1901.PAIRS))
        self.assertEqual(legacy_pairs[0][0]["slug"], plants_r1901.PAIRS[0][0]["slug"])

    def test_record_builder_on_first_plant_pair(self):
        ok, bad = plants_r1901.PAIRS[0]
        rnd = plants_r1901.START
        rec_ok = cer_builder.episode(rnd, ok)
        rec_bad = cer_builder.episode(rnd, bad)
        self.assertTrue(rec_ok["id"].startswith("cer-r1901-"))
        self.assertEqual(len(rec_ok["steps"]), 19)
        self.assertTrue(rec_ok["reward"]["success"])
        self.assertFalse(rec_bad["reward"]["success"])
        notes = cer_builder.notes_markdown(rnd, rec_ok, rec_bad, ok_slug=ok["slug"], fail_slug=bad["slug"])
        self.assertIn("Novel coverage: 85%", notes)

    def test_sid_is_deterministic(self):
        self.assertEqual(
            cer_builder.sid(1966, "cache-status-hit-stale"),
            cer_builder.sid(1966, "cache-status-hit-stale"),
        )


if __name__ == "__main__":
    unittest.main()
