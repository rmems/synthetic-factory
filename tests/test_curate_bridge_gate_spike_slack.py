"""Regression: gate spike budgets must not accumulate a one-spike slack.

Refs #545. ``validate_gate_compute`` and the ``gate_snn`` population budget used
to accept ``abs(spikes - round(neurons × rate × window)) <= 1`` per entry. A
whole-number product therefore still allowed ±1, so one thousand exact-1
checks declaring 0 spikes passed while a single 1000-spike shortfall did not.
"""
from __future__ import annotations

import math
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO / "pipelines") not in sys.path:
    sys.path.insert(0, str(REPO / "pipelines"))

import curate_bridge_gate as g  # noqa: E402
from curate_bridge_raster import (  # noqa: E402
    RASTER_ENERGY_PJ_PER_SPIKE as PJ,
    REASON_RASTER_SPIKE_BUDGET,
    _expected_spikes,
    _spikes_match_product,
)


def _reasons_compute(gc):
    rc, ev = [], {}
    g.validate_gate_compute(gc, reason_codes=rc, evidence=ev)
    return rc, ev


def _reasons_snn(spec):
    rc, ev = [], {}
    g.validate_gate_snn(spec, reason_codes=rc, evidence=ev)
    return rc, ev


def _gate(checks):
    total = sum(check["spikes"] for check in checks)
    return {"per_check": checks, "total_energy_pJ": total * PJ}


class BridgeGateSpikeSlack(unittest.TestCase):
    def test_whole_product_requires_exact_spikes(self):
        exact = {"neurons": 1, "mean_rate_hz": 1, "window_s": 1, "spikes": 1}
        short = dict(exact, spikes=0)
        self.assertEqual(_reasons_compute(_gate([exact]))[0], [])
        for spikes in (0, 2):
            with self.subTest(spikes=spikes):
                rc, _ = _reasons_compute(_gate([dict(exact, spikes=spikes)]))
                self.assertIn(REASON_RASTER_SPIKE_BUDGET, rc)

        many = _gate([short] * 1000)
        one = _gate([{"neurons": 1000, "mean_rate_hz": 1, "window_s": 1, "spikes": 0}])
        many_rc, _ = _reasons_compute(many)
        one_rc, _ = _reasons_compute(one)
        self.assertIn(REASON_RASTER_SPIKE_BUDGET, many_rc)
        self.assertIn(REASON_RASTER_SPIKE_BUDGET, one_rc)

    def test_fractional_product_accepts_floor_or_ceil(self):
        # 3 × 10 × 0.05 = 1.5
        base = {"neurons": 3, "mean_rate_hz": 10.0, "window_s": 0.05}
        product = 3 * 10.0 * 0.05
        self.assertNotEqual(product, math.floor(product))
        for spikes in (math.floor(product), math.ceil(product)):
            with self.subTest(spikes=spikes):
                rc, _ = _reasons_compute(_gate([dict(base, spikes=spikes)]))
                self.assertEqual(rc, [])
        for spikes in (math.floor(product) - 1, math.ceil(product) + 1):
            with self.subTest(spikes=spikes):
                rc, _ = _reasons_compute(_gate([dict(base, spikes=spikes)]))
                self.assertIn(REASON_RASTER_SPIKE_BUDGET, rc)

    def test_honest_multi_check_gate_still_passes(self):
        checks = [
            {"neurons": 100, "mean_rate_hz": 10.0, "window_s": 1.0, "spikes": 1000},
            {"neurons": 3, "mean_rate_hz": 10.0, "window_s": 0.05, "spikes": 1},
            {"neurons": 3, "mean_rate_hz": 10.0, "window_s": 0.05, "spikes": 2},
        ]
        rc, ev = _reasons_compute(_gate(checks))
        self.assertEqual(rc, [])
        self.assertEqual(ev["gate_compute_total_spikes"], 1003)

    def test_gate_snn_population_follows_the_same_rule(self):
        window_ms = 25
        window_s = window_ms / 1000
        # 64 × 40 × 0.025 = 64 exactly; ±1 must fail.
        exact = {
            "name": "gate_accept",
            "neurons": 64,
            "threshold": 1.0,
            "mean_rate_hz": 40,
            "spikes": 64,
        }
        # 5 × 30 × 0.025 = 3.75; floor 3 and ceil 4 both pass.
        fractional = {
            "name": "gate_reject",
            "neurons": 5,
            "threshold": 1.0,
            "mean_rate_hz": 30,
            "spikes": 4,
        }
        product = 5 * 30 * window_s
        self.assertEqual((math.floor(product), math.ceil(product)), (3, 4))

        honest = {
            "decision_window_ms": window_ms,
            "decision": "ACCEPT",
            "populations": [exact, fractional],
        }
        self.assertEqual(_reasons_snn(honest)[0], [])

        short = {
            "decision_window_ms": window_ms,
            "decision": "ACCEPT",
            "populations": [dict(exact, spikes=63)],
        }
        rc, ev = _reasons_snn(short)
        self.assertIn(REASON_RASTER_SPIKE_BUDGET, rc)
        self.assertFalse(ev["gate_snn_populations_valid"])

        for spikes in (3, 4):
            with self.subTest(spikes=spikes):
                spec = {
                    "decision_window_ms": window_ms,
                    "decision": "ACCEPT",
                    "populations": [dict(fractional, spikes=spikes)],
                }
                self.assertEqual(_reasons_snn(spec)[0], [])

    def test_helper_pins_whole_versus_fractional_bounds(self):
        self.assertTrue(_spikes_match_product(1, 1, 1, 1))
        self.assertFalse(_spikes_match_product(0, 1, 1, 1))
        self.assertFalse(_spikes_match_product(2, 1, 1, 1))
        self.assertEqual(_expected_spikes(1, 1, 1), 1)
        self.assertTrue(_spikes_match_product(1, 3, 10.0, 0.05))
        self.assertTrue(_spikes_match_product(2, 3, 10.0, 0.05))
        self.assertFalse(_spikes_match_product(0, 3, 10.0, 0.05))
        self.assertFalse(_spikes_match_product(3, 3, 10.0, 0.05))


if __name__ == "__main__":
    unittest.main()
