"""Regression: curate_bridge_gate.validate_gate_compute must refuse missing evidence.

A missing per_check used to become an empty list, and a missing energy key was
skipped, so an empty or label-only gate_compute passed. The validator is called
directly; the upstream sidecar walk in curate_bridge is not exercised here.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO / "pipelines") not in sys.path:
    sys.path.insert(0, str(REPO / "pipelines"))

import curate_bridge_gate as g  # noqa: E402
from curate_bridge_raster import RASTER_ENERGY_UJ_PER_SPIKE as U, _expected_spikes  # noqa: E402

E = _expected_spikes(100, 10.0, 1.0)
CHECK = {"neurons": 100, "rate_hz": 10.0, "window_s": 1.0, "spikes": E}

FORGES = {
    "empty_gate_compute": {},
    "per_check_empty_energy_zero": {"per_check": [], "total_energy_uJ": 0.0},
    "bare_source_kind_loihi": {"source_kind": "measured_on_loihi"},
    "honest_check_energy_omitted": {"per_check": [dict(CHECK)]},
}


def reasons(gc):
    rc, ev = [], {}
    g.validate_gate_compute(gc, reason_codes=rc, evidence=ev)
    return rc


class BridgeGateComputeForges(unittest.TestCase):
    def test_control_honest_accepted(self):
        self.assertEqual(reasons({"per_check": [dict(CHECK)], "total_energy_uJ": E * U}), [])

    def test_control_spikes_off_by_50_rejected(self):
        bad = dict(CHECK, spikes=E + 50)
        self.assertTrue(reasons({"per_check": [bad], "total_energy_uJ": (E + 50) * U}))

    def test_forge_missing_evidence_refused(self):
        for name, gc in FORGES.items():
            with self.subTest(variant=name):
                self.assertTrue(reasons(gc), f"{name}: accepted with no reason codes")


if __name__ == "__main__":
    unittest.main()
