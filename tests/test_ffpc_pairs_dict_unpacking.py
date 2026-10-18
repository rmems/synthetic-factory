#!/usr/bin/env python3
"""An int-keyed ``PAIRS`` dict skips a ``**mapping`` entry like any non-int key."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "pipelines"))

from ffpc import catalog as cat  # noqa: E402

_SOURCE = (
    "FACTORY = 'failure-as-fuel-preference-cascade'\n"
    "EXTRA = {9: {'id': 'ffpc-r22-009', 'goal': 'g9'}}\n"
    "PAIRS = {\n"
    "    1: {'id': 'ffpc-r22-001', 'goal': 'g1', 'failure_archetype': 'f1'},\n"
    "{unpacking}"
    "    2: {'id': 'ffpc-r22-002', 'goal': 'g2', 'gate_flaw_class': 'f2'},\n"
    "    3: {'id': 'ffpc-r22-003', 'goal': 'g3'},\n"
    "}\n"
)


class IntKeyedPairsUnpacking(unittest.TestCase):
    def test_a_double_star_entry_is_skipped(self):
        plain = cat.plants_from_source(_SOURCE.replace("{unpacking}", ""), "ffpc-r22-build.py")
        unpacked = cat.plants_from_source(
            _SOURCE.replace("{unpacking}", "    **EXTRA,\n"), "ffpc-r22-build.py"
        )
        self.assertEqual([plant.index for plant in plain], [1, 2, 3])
        self.assertEqual(unpacked, plain)


if __name__ == "__main__":
    unittest.main()
