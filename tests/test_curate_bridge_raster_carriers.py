"""Declared-null raster sidecar carriers and energy bounds in Bridge curation."""

from __future__ import annotations

import copy
import unittest

try:
    from tests.curate_bridge_raster_test_support import (
        curate_bridge,
        gate_snn_fixture,
        zero_spike_record,
    )
except ModuleNotFoundError:
    from curate_bridge_raster_test_support import (  # type: ignore[no-redef]
        curate_bridge,
        gate_snn_fixture,
        zero_spike_record,
    )


def declared_null_case(carrier):
    record = gate_snn_fixture()
    if carrier == "raster":
        record["meta"] = {"raster": copy.deepcopy(record["raster"])}
        record["raster"] = None
        return record, curate_bridge.raster_sidecar, curate_bridge.REASON_RASTER_EXCERPT
    if carrier == "gate_snn":
        record["meta"] = {"gate_snn": copy.deepcopy(record["gate_snn"])}
        record["gate_snn"] = None
        return record, curate_bridge.gate_snn_sidecar, curate_bridge.REASON_GATE_SNN_INVALID
    record["gate_compute"] = None
    record["language_view"]["trajectory"]["gate_compute"] = {
        "per_check": [{"neurons": 2, "mean_rate_hz": 10.0, "window_s": 0.05, "spikes": 1}],
        "total_energy_uJ": curate_bridge.RASTER_ENERGY_UJ_PER_SPIKE,
    }
    return record, curate_bridge._gate_compute_sidecar, curate_bridge.REASON_RASTER_SPIKE_BUDGET


class DeclaredNullCarriersAndEnergyBounds(unittest.TestCase):
    """PR #94 review follow-ups on the shared sidecar/energy contract.

    Two holes the earlier carrier-precedence and overflow fixes left open:
    an explicit ``null`` sidecar was read as an absence rather than as a
    declaration, and the energy tolerance accepted small negative values
    whenever the expected energy was zero.
    """

    def test_a_declared_null_carrier_never_falls_through(self):
        for carrier in ("raster", "gate_snn", "gate_compute"):
            with self.subTest(carrier=carrier):
                record, resolver, reason = declared_null_case(carrier)
                location, value = resolver(record)

                self.assertEqual(location, carrier)
                self.assertIsNone(value)
                status = curate_bridge.raster_status(record)
                self.assertFalse(status["raster_valid"])
                self.assertIn(reason, status["reason_codes"])

    def test_a_declared_non_array_per_check_container_fails_validation(self):
        for per_check in ("bad", 7, {"neurons": 2}, None):
            with self.subTest(per_check=per_check):
                record = gate_snn_fixture()
                record["gate_compute"] = {"per_check": per_check}

                status = curate_bridge.raster_status(record)

                self.assertFalse(status["raster_valid"])
                self.assertIn(
                    curate_bridge.REASON_RASTER_SPIKE_BUDGET,
                    status["reason_codes"],
                )

    def test_malformed_lower_raster_carrier_is_not_masked(self):
        record = gate_snn_fixture()
        record["meta"] = {"raster": "bad"}

        status = curate_bridge.raster_status(record)

        self.assertFalse(status["raster_valid"])
        self.assertEqual(status["raster_location"], "raster")
        self.assertIn(curate_bridge.REASON_RASTER_EXCERPT, status["reason_codes"])
        self.assertEqual(
            status["evidence"]["raster_invalid_carrier_locations"],
            ["meta.raster"],
        )

    def test_malformed_lower_gate_snn_carriers_are_not_masked(self):
        locations = (
            "meta.gate_snn",
            "language_view.trajectory.gate_snn",
            "language_view.trajectory.safety_decision.gate_snn",
        )
        for location in locations:
            with self.subTest(location=location):
                record = gate_snn_fixture()
                target = record
                for key in location.split(".")[:-1]:
                    target = target.setdefault(key, {})
                target["gate_snn"] = "bad"

                status = curate_bridge.raster_status(record)

                self.assertFalse(status["raster_valid"])
                self.assertFalse(status["gate_snn_valid"])
                self.assertIn(curate_bridge.REASON_GATE_SNN_INVALID, status["reason_codes"])
                self.assertEqual(
                    status["evidence"]["gate_snn_invalid_carrier_locations"],
                    [location],
                )

    def test_malformed_lower_gate_compute_carriers_are_not_masked(self):
        locations = (
            "language_view.trajectory.gate_compute",
            "language_view.trajectory.safety_decision.gate_compute",
        )
        for location in locations:
            with self.subTest(location=location):
                record = gate_snn_fixture()
                record["gate_compute"] = {
                    "per_check": [
                        {"neurons": 2, "mean_rate_hz": 10.0, "window_s": 0.05, "spikes": 1}
                    ],
                    "total_energy_pJ": curate_bridge.RASTER_ENERGY_PJ_PER_SPIKE,
                }
                target = record
                for key in location.split(".")[:-1]:
                    target = target.setdefault(key, {})
                target["gate_compute"] = "bad"

                status = curate_bridge.raster_status(record)

                self.assertFalse(status["raster_valid"])
                self.assertIn(
                    curate_bridge.REASON_RASTER_SPIKE_BUDGET,
                    status["reason_codes"],
                )
                self.assertEqual(
                    status["evidence"]["gate_compute_invalid_carrier_locations"],
                    [location],
                )

    def test_valid_redundant_sidecars_remain_supported(self):
        record = gate_snn_fixture()
        record["meta"] = {
            "raster": copy.deepcopy(record["raster"]),
            "gate_snn": copy.deepcopy(record["gate_snn"]),
        }
        record["gate_compute"] = {
            "per_check": [{"neurons": 2, "mean_rate_hz": 10.0, "window_s": 0.05, "spikes": 1}],
            "total_energy_pJ": curate_bridge.RASTER_ENERGY_PJ_PER_SPIKE,
        }
        record["language_view"]["trajectory"]["gate_compute"] = copy.deepcopy(
            record["gate_compute"]
        )

        self.assertTrue(curate_bridge.raster_status(record)["raster_valid"])

    def test_an_absent_per_check_block_is_refused(self):
        record = gate_snn_fixture()
        record["gate_compute"] = {}

        status = curate_bridge.raster_status(record)

        self.assertFalse(status["raster_valid"])
        self.assertIn(curate_bridge.REASON_RASTER_SPIKE_BUDGET, status["reason_codes"])
        self.assertIn(curate_bridge.REASON_RASTER_ENERGY, status["reason_codes"])

    def test_negative_declared_raster_energy_is_rejected_inside_tolerance(self):
        for key, value in (("energy_pJ", -5e-7), ("energy_uJ", -5e-10)):
            with self.subTest(key=key):
                record = zero_spike_record()
                record["raster"][key] = value

                status = curate_bridge.raster_status(record)

                self.assertFalse(status["raster_valid"])
                self.assertIn(curate_bridge.REASON_RASTER_ENERGY, status["reason_codes"])

    def test_negative_declared_gate_compute_totals_are_rejected(self):
        for key, value in (("total_energy_pJ", -5e-7), ("total_energy_uJ", -5e-10)):
            with self.subTest(key=key):
                record = gate_snn_fixture()
                record["gate_compute"] = {
                    "per_check": [
                        {
                            "neurons": 1,
                            "mean_rate_hz": 1.0,
                            "window_s": 0.02,
                            "spikes": 0,
                        }
                    ],
                    key: value,
                }

                status = curate_bridge.raster_status(record)

                self.assertFalse(status["raster_valid"])
                self.assertIn(curate_bridge.REASON_RASTER_ENERGY, status["reason_codes"])

    def test_zero_energy_on_a_zero_spike_raster_still_validates(self):
        record = zero_spike_record()

        status = curate_bridge.raster_status(record)

        self.assertTrue(status["raster_valid"])


if __name__ == "__main__":
    unittest.main()
