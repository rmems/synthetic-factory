#!/usr/bin/env python3
"""Mill-usage-burst plan slice A (``cer`` / cascading-error-recovery)."""

from __future__ import annotations

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

# Pins from the AST extract of cer_r1901 (do not git-show leftover mills in CI).
_R1901_START = 1901
_R1901_N_ROUNDS = 16
_R1901_N_PAIRS = 16
_R1901_FIRST_SLUG = "cache-status-hit-stale"


class CerMillUsageBurstTests(unittest.TestCase):
    def test_reviewed_prefix_maps_to_factory(self):
        self.assertEqual(REVIEWED_MILL_PREFIX_HOMES[cv.FAMILY_PREFIX], cv.FACTORY)

    def test_plan_loads_and_matches_plants(self):
        plan = load_mill_usage_burst_plan(repo_root=REPO)
        self.assertEqual(plan.slice, "A")
        self.assertEqual(plan.counts(), {"mills": 2, "rounds": 32, "pairs": 32, "episodes": 64})
        self.assertEqual([m.mill_id for m in plan.mills], ["cer_r1901", "cer_r1958"])

    def test_plants_r1901_matches_legacy_ast_extract(self):
        self.assertEqual(plants_r1901.START, _R1901_START)
        self.assertEqual(plants_r1901.N_ROUNDS, _R1901_N_ROUNDS)
        self.assertEqual(len(plants_r1901.PAIRS), _R1901_N_PAIRS)
        self.assertEqual(plants_r1901.PAIRS[0][0]["slug"], _R1901_FIRST_SLUG)

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
