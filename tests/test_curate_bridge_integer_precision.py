#!/usr/bin/env python3
"""Exact integer-precision regressions for Bridge spike budgets."""

from __future__ import annotations

import unittest
from fractions import Fraction

try:
    from tests.test_curate_bridge import curate_bridge, gate_snn_fixture
except ModuleNotFoundError:
    from test_curate_bridge import curate_bridge, gate_snn_fixture  # type: ignore[no-redef]


class BridgeIntegerPrecision(unittest.TestCase):
    def test_large_neuron_counts_keep_unit_precision_in_every_budget(self):
        neurons = 10**18 + 2
        rounded_collision = 10**18
        self.assertEqual(float(neurons), float(rounded_collision))

        raster_record = gate_snn_fixture()
        raster_record["raster"].update(
            {
                "window_ms": 40,
                "window_s": 0.04,
                "neurons": neurons,
                "mean_rate_hz": 25,
                "spikes": rounded_collision,
            }
        )
        raster_record["raster"].pop("energy_pJ", None)
        raster_record["raster"].pop("energy_uJ", None)
        raster_status = curate_bridge.raster_status(raster_record)
        self.assertEqual(raster_status["evidence"]["raster_expected_spikes"], neurons)
        self.assertIn(curate_bridge.REASON_RASTER_SPIKE_BUDGET, raster_status["reason_codes"])

        gate_record = gate_snn_fixture()
        gate_record["gate_snn"].update({"decision_window_ms": 40, "decision_window_s": 0.04})
        gate_record["gate_snn"]["populations"][0].update(
            {
                "neurons": neurons,
                "mean_rate_hz": 25,
                "spikes": float(rounded_collision),
            }
        )
        gate_status = curate_bridge.raster_status(gate_record)
        self.assertEqual(
            gate_status["evidence"]["gate_snn_spike_mismatches"][0]["expected"],
            neurons,
        )
        self.assertIn(curate_bridge.REASON_RASTER_SPIKE_BUDGET, gate_status["reason_codes"])

        compute_record = gate_snn_fixture()
        compute_record["gate_compute"] = {
            "per_check": [
                {
                    "neurons": neurons,
                    "mean_rate_hz": 25,
                    "window_s": 0.04,
                    "spikes": float(rounded_collision),
                }
            ]
        }
        compute_status = curate_bridge.raster_status(compute_record)
        self.assertEqual(
            compute_status["evidence"]["gate_compute_spike_mismatches"][0]["expected"],
            neurons,
        )
        self.assertIn(curate_bridge.REASON_RASTER_SPIKE_BUDGET, compute_status["reason_codes"])

    def test_decimal_factors_do_not_magnify_binary_noise(self):
        neurons = 10**18 + 2
        expected = round(Fraction(3, 10) * neurons)
        declared = expected - 2
        record = gate_snn_fixture()
        record["gate_compute"] = {
            "per_check": [
                {
                    "neurons": neurons,
                    "mean_rate_hz": 3,
                    "window_s": 0.1,
                    "spikes": declared,
                }
            ]
        }

        status = curate_bridge.raster_status(record)

        mismatch = status["evidence"]["gate_compute_spike_mismatches"][0]
        self.assertEqual(mismatch["expected"], expected)
        self.assertEqual(mismatch["actual"], declared)
        self.assertIn(curate_bridge.REASON_RASTER_SPIKE_BUDGET, status["reason_codes"])


if __name__ == "__main__":
    unittest.main()
