#!/usr/bin/env python3
"""Exact-contract energy regressions for Bridge raster curation."""

from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

try:
    from tests.test_curate_bridge import curate_bridge, gate_snn_fixture
except ModuleNotFoundError:
    from test_curate_bridge import (  # type: ignore[no-redef]
        curate_bridge,
        gate_snn_fixture,
    )

from exact_json import dumps_exact_json, parse_finite_json_float  # noqa: E402
import spike_probe  # noqa: E402


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

    def test_unrepresentable_derived_energy_is_a_bounded_validation_defect(self):
        record = gate_snn_fixture()
        record["raster"].update(
            {
                "window_ms": 50,
                "window_s": 0.05,
                "neurons": 10**4095,
                "mean_rate_hz": 20,
                "spikes": 10**4095,
            }
        )
        record["raster"].pop("energy_pJ", None)
        record["raster"].pop("energy_uJ", None)

        status = curate_bridge.raster_status(record)

        self.assertFalse(status["raster_valid"])
        self.assertIn(curate_bridge.REASON_RASTER_ENERGY, status["reason_codes"])
        self.assertFalse(status["evidence"]["raster_derived_energy_valid"])
        self.assertIsNone(spike_probe.normalize_raster(record))
        dumps_exact_json(status["evidence"])

    def test_representable_boundary_energy_remains_loadable(self):
        record = gate_snn_fixture()
        record["raster"].update(
            {
                "window_ms": 50,
                "window_s": 0.05,
                "neurons": 10**4094,
                "mean_rate_hz": 20,
                "spikes": 10**4094,
            }
        )
        record["raster"].pop("energy_pJ", None)
        record["raster"].pop("energy_uJ", None)

        status = curate_bridge.raster_status(record)
        normalized = spike_probe.normalize_raster(record)

        self.assertTrue(status["raster_valid"], status["reason_codes"])
        self.assertIsNotNone(normalized)
        dumps_exact_json(normalized)

    def test_jsonl_reports_unrepresentable_derived_energy_without_crashing(self):
        record = gate_snn_fixture()
        record["raster"].update(
            {
                "window_ms": 50,
                "window_s": 0.05,
                "neurons": 10**4095,
                "mean_rate_hz": 20,
                "spikes": 10**4095,
            }
        )
        record["raster"].pop("energy_pJ", None)
        record["raster"].pop("energy_uJ", None)

        with tempfile.TemporaryDirectory() as td:
            source = Path(td) / "unrepresentable-energy.jsonl"
            source.write_text(dumps_exact_json(record) + "\n")
            stdout = io.StringIO()
            stderr = io.StringIO()
            with redirect_stdout(stdout), redirect_stderr(stderr):
                code = spike_probe.main(["--jsonl", str(source)])

        self.assertEqual(code, 1)
        self.assertEqual(stdout.getvalue(), "")
        problems = [json.loads(line) for line in stderr.getvalue().splitlines()]
        self.assertEqual(len(problems), 1)
        self.assertEqual(problems[0]["reason_codes"], ["BRIDGE_ENERGY_MISMATCH"])


if __name__ == "__main__":
    unittest.main()
