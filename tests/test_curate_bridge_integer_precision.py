#!/usr/bin/env python3
"""Exact integer-precision regressions for Bridge spike budgets."""

from __future__ import annotations

import json
import unittest
from fractions import Fraction

try:
    from tests.test_curate_bridge import curate_bridge, gate_snn_fixture
except ModuleNotFoundError:
    from test_curate_bridge import curate_bridge, gate_snn_fixture  # type: ignore[no-redef]

import spike_probe  # noqa: E402
from exact_json import dumps_exact_json  # noqa: E402


class BridgeIntegerPrecision(unittest.TestCase):
    neurons = 10**18 + 2
    rounded_collision = 10**18

    def _assert_spike_mismatch(self, status, evidence_key):
        self.assertEqual(status["evidence"][evidence_key][0]["expected"], self.neurons)
        self.assertIn(curate_bridge.REASON_RASTER_SPIKE_BUDGET, status["reason_codes"])

    def test_large_raster_population_keeps_unit_precision(self):
        self.assertEqual(float(self.neurons), float(self.rounded_collision))
        raster_record = gate_snn_fixture()
        raster_record["raster"].update(
            {
                "window_ms": 40,
                "window_s": 0.04,
                "neurons": self.neurons,
                "mean_rate_hz": 25,
                "spikes": self.rounded_collision,
            }
        )
        raster_record["raster"].pop("energy_pJ", None)
        raster_record["raster"].pop("energy_uJ", None)
        raster_status = curate_bridge.raster_status(raster_record)
        self.assertEqual(raster_status["evidence"]["raster_expected_spikes"], self.neurons)
        self.assertIn(curate_bridge.REASON_RASTER_SPIKE_BUDGET, raster_status["reason_codes"])

    def test_large_gate_population_keeps_unit_precision(self):
        gate_record = gate_snn_fixture()
        gate_record["gate_snn"].update({"decision_window_ms": 40, "decision_window_s": 0.04})
        gate_record["gate_snn"]["populations"][0].update(
            {
                "neurons": self.neurons,
                "mean_rate_hz": 25,
                "spikes": float(self.rounded_collision),
            }
        )
        gate_status = curate_bridge.raster_status(gate_record)
        self._assert_spike_mismatch(gate_status, "gate_snn_spike_mismatches")

    def test_large_gate_compute_population_keeps_unit_precision(self):
        compute_record = gate_snn_fixture()
        compute_record["gate_compute"] = {
            "per_check": [
                {
                    "neurons": self.neurons,
                    "mean_rate_hz": 25,
                    "window_s": 0.04,
                    "spikes": float(self.rounded_collision),
                }
            ]
        }
        compute_status = curate_bridge.raster_status(compute_record)
        self._assert_spike_mismatch(compute_status, "gate_compute_spike_mismatches")

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

    def test_extreme_integer_rate_keeps_a_bounded_exact_spike_product(self):
        rate = 10**309
        expected = 2 * 10**307

        raster_record = gate_snn_fixture()
        raster_record["raster"].update(
            {
                "window_ms": 20,
                "window_s": 0.02,
                "neurons": 1,
                "mean_rate_hz": rate,
                "spikes": expected,
            }
        )
        raster_record["raster"].pop("energy_pJ", None)
        raster_record["raster"].pop("energy_uJ", None)
        raster_record["raster"]["excerpt"] = [{"t_us": 1000, "neuron_id": 0}]
        raster_status = curate_bridge.raster_status(raster_record)
        self.assertTrue(raster_status["raster_valid"], raster_status["reason_codes"])
        self.assertEqual(raster_status["evidence"]["raster_expected_spikes"], expected)
        normalized = spike_probe.normalize_raster(raster_record)
        self.assertIsNotNone(normalized)
        dumps_exact_json(normalized)

        gate_record = gate_snn_fixture()
        gate_record["gate_snn"].update(
            {
                "decision_window_ms": 20,
                "decision_window_s": 0.02,
                "populations": [
                    {
                        "name": "exact-rate",
                        "neurons": 1,
                        "threshold": 1,
                        "mean_rate_hz": rate,
                        "spikes": expected,
                    }
                ],
            }
        )
        gate_status = curate_bridge.raster_status(gate_record)
        self.assertTrue(gate_status["raster_valid"], gate_status["reason_codes"])

        compute_record = gate_snn_fixture()
        compute_record["gate_compute"] = {
            "per_check": [
                {
                    "neurons": 1,
                    "mean_rate_hz": rate,
                    "window_s": 0.02,
                    "spikes": expected,
                }
            ]
        }
        compute_status = curate_bridge.raster_status(compute_record)
        self.assertTrue(compute_status["raster_valid"], compute_status["reason_codes"])

    def test_large_exact_gate_spike_product_is_checked_without_overflow(self):
        record = gate_snn_fixture()
        record["gate_snn"]["decision_window_ms"] = 1e308
        record["gate_snn"]["decision_window_s"] = 1e308 / 1000.0
        record["gate_snn"]["populations"][0]["mean_rate_hz"] = 1e308
        record["gate_snn"]["populations"][0]["spikes"] = 1

        status = curate_bridge.raster_status(record)

        self.assertFalse(status["raster_valid"])
        self.assertIn(curate_bridge.REASON_RASTER_SPIKE_BUDGET, status["reason_codes"])
        mismatch = status["evidence"]["gate_snn_spike_mismatches"][0]
        self.assertGreater(mismatch["expected"], 10**600)
        self.assertEqual(mismatch["actual"], 1)

    def _literal_decimal_record(self, declared_spikes):
        record = gate_snn_fixture()
        record["raster"].update(
            {
                "neurons": self.neurons,
                "mean_rate_hz": 25,
                "spikes": declared_spikes,
                "window_ms": 40,
                "window_s": 0.04,
            }
        )
        record["raster"].pop("energy_pJ", None)
        record["raster"].pop("energy_uJ", None)
        payload = json.dumps(record, separators=(",", ":"))
        payload = payload.replace(
            '"mean_rate_hz":25',
            '"mean_rate_hz":25.000000000000001',
            1,
        )
        return curate_bridge._parse_source_record(payload)

    def test_literal_decimal_precision_controls_the_budget(self):
        exact = round(
            Fraction("25.000000000000001") * Fraction("0.04") * self.neurons
        )
        wrong_status = curate_bridge.raster_status(
            self._literal_decimal_record(self.neurons)
        )
        exact_record = self._literal_decimal_record(exact)
        exact_status = curate_bridge.raster_status(exact_record)

        self.assertEqual(wrong_status["evidence"]["raster_expected_spikes"], exact)
        self.assertIn(curate_bridge.REASON_RASTER_SPIKE_BUDGET, wrong_status["reason_codes"])
        self.assertTrue(exact_status["raster_valid"])
        self.assertIn(
            b'"mean_rate_hz":25.000000000000001',
            curate_bridge.canonical_json_bytes(exact_record),
        )


if __name__ == "__main__":
    unittest.main()
