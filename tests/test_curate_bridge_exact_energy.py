#!/usr/bin/env python3
"""Exact-contract energy regressions for Bridge raster curation."""

from __future__ import annotations

import unittest

try:
    from tests.test_curate_bridge import curate_bridge, gate_snn_fixture
except ModuleNotFoundError:
    from test_curate_bridge import (  # type: ignore[no-redef]
        curate_bridge,
        gate_snn_fixture,
    )

from exact_json import dumps_exact_json, parse_finite_json_float  # noqa: E402


class ExactRasterEnergyBounds(unittest.TestCase):
    """Keep declared and derived raster energy exact at contract limits."""

    def test_energy_comparison_rejects_number_beyond_exact_contract(self):
        record = gate_snn_fixture()
        record["raster"]["energy_pJ"] = 10**4096

        status = curate_bridge.raster_status(record)

        self.assertFalse(status["raster_valid"])
        self.assertIn(curate_bridge.REASON_RASTER_ENERGY, status["reason_codes"])

    def test_contract_bounded_energy_stays_exact_beyond_float_range(self):
        record = gate_snn_fixture()
        spikes = 10**307
        expected_energy = spikes * curate_bridge.RASTER_ENERGY_PJ_PER_SPIKE
        record["raster"].update(
            {
                "neurons": spikes,
                "mean_rate_hz": 20,
                "window_ms": 50,
                "window_s": parse_finite_json_float("0.05"),
                "spikes": spikes,
                "energy_pJ": expected_energy,
            }
        )
        record["raster"].pop("energy_uJ", None)
        self.assertGreater(expected_energy, 10**308)
        dumps_exact_json(record, sort_keys=False)

        status = curate_bridge.raster_status(record)

        self.assertTrue(status["raster_valid"], status["reason_codes"])
        self.assertEqual(
            status["evidence"]["raster_expected_energy_pJ"],
            expected_energy,
        )
        self.assertTrue(status["evidence"]["raster_energy_pJ_valid"])


if __name__ == "__main__":
    unittest.main()
