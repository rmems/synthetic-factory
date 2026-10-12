#!/usr/bin/env python3
"""Raster spike-arithmetic regression tests for Bridge curation."""

from __future__ import annotations

import json
import unittest

try:
    from tests.curate_bridge_raster_test_support import (
        curate_bridge,
        decide,
        gate_snn_fixture,
        zero_spike_record,
    )
except ModuleNotFoundError:
    from curate_bridge_raster_test_support import (  # type: ignore[no-redef]
        curate_bridge,
        decide,
        gate_snn_fixture,
        zero_spike_record,
    )

from exact_json import dumps_exact_json, exact_fraction, parse_finite_json_float

_OTHER_ENERGY_UNIT = {"energy_pJ": "energy_uJ", "energy_uJ": "energy_pJ"}


def _scaled_raster_record(spikes, energy_key, energy):
    """The reference record scaled to ``spikes`` at 25 Hz over a 40 ms window.

    The raster declares its energy only under ``energy_key``; the other unit's
    total is removed so that it cannot decide the comparison.
    """
    record = gate_snn_fixture()
    record["raster"].update(
        {
            "neurons": spikes,
            "mean_rate_hz": 25,
            "window_ms": 40,
            "window_s": 0.04,
            "spikes": spikes,
            energy_key: energy,
        }
    )
    record["raster"].pop(_OTHER_ENERGY_UNIT[energy_key], None)
    return record


class RasterArithmeticReviewFollowUps(unittest.TestCase):
    """Spike-arithmetic holes the PR #94 review found in the shared validator.

    Every downstream consumer — the curator, the publish gate, the training
    audit and the distillation probe — reads ``raster_status``, so a budget
    the validator cannot evaluate has to surface as a reason code rather than
    as an exception or as a silently accepted record.
    """

    def test_unrepresentable_spike_count_is_a_budget_defect_not_an_overflow(self):
        record = gate_snn_fixture()
        record["raster"]["spikes"] = 10**400
        record["raster"]["energy_uJ"] = 1.0

        status = curate_bridge.raster_status(record)

        self.assertFalse(status["raster_valid"])
        self.assertIn(curate_bridge.REASON_RASTER_SPIKE_BUDGET, status["reason_codes"])

    def test_unrepresentable_energy_evidence_stays_json_serializable(self):
        record = gate_snn_fixture()
        record["raster"]["spikes"] = 10**400
        record["raster"]["energy_pJ"] = 1.0
        record["raster"]["energy_uJ"] = 1.0

        decision = decide(record)

        self.assertEqual(decision.action, "quarantine")
        json.dumps(decision.manifest, allow_nan=False)

    def test_gate_compute_totals_survive_an_unrepresentable_spike_sum(self):
        record = gate_snn_fixture()
        record["gate_compute"] = {
            "per_check": [
                {
                    "neurons": 4,
                    "mean_rate_hz": 10.0,
                    "window_s": 0.05,
                    "spikes": 10**400,
                }
            ],
            "total_energy_uJ": 1.0,
        }

        status = curate_bridge.raster_status(record)

        self.assertFalse(status["raster_valid"])
        json.dumps(status["evidence"], allow_nan=False)

    def test_gate_population_total_is_bounded_before_evidence_serialization(self):
        record = gate_snn_fixture()
        huge_population = 6 * 10**4095
        for population in record["gate_snn"]["populations"]:
            population["neurons"] = huge_population
            population.pop("mean_rate_hz", None)
            population.pop("spikes", None)

        status = curate_bridge.raster_status(record)

        self.assertFalse(status["raster_valid"])
        self.assertIn(curate_bridge.REASON_GATE_SNN_INVALID, status["reason_codes"])
        self.assertFalse(status["evidence"]["gate_snn_populations_valid"])
        self.assertNotIn("gate_snn_invalid_population_indices", status["evidence"])
        self.assertNotIn("gate_snn_total_neurons", status["evidence"])
        dumps_exact_json(status["evidence"])

    def test_gate_compute_sum_is_bounded_before_evidence_serialization(self):
        record = gate_snn_fixture()
        large_spike_count = 6 * 10**4095
        record["gate_compute"] = {
            "per_check": [
                {"neurons": 1, "mean_rate_hz": 1, "window_s": 1, "spikes": value}
                for value in (large_spike_count, large_spike_count)
            ]
        }

        status = curate_bridge.raster_status(record)

        self.assertFalse(status["raster_valid"])
        self.assertFalse(status["evidence"]["gate_compute_total_spikes_valid"])
        self.assertNotIn("gate_compute_total_spikes", status["evidence"])
        dumps_exact_json(status["evidence"])

    def test_excerpt_endpoint_does_not_receive_a_float_tolerance(self):
        record = zero_spike_record()
        record["raster"].pop("window_s")
        record["raster"]["window_ms"] = parse_finite_json_float(
            "20.0009999999999995"
        )
        record["raster"]["excerpt"] = [{"t_us": 20001, "neuron_id": 0}]

        status = curate_bridge.raster_status(record)

        self.assertFalse(status["raster_valid"])
        self.assertIn(curate_bridge.REASON_RASTER_EXCERPT, status["reason_codes"])

    def test_population_budget_mismatch_marks_population_evidence_invalid(self):
        record = gate_snn_fixture()
        record["gate_snn"]["populations"][0]["spikes"] += 10

        status = curate_bridge.raster_status(record)

        self.assertFalse(status["raster_valid"])
        self.assertFalse(status["evidence"]["gate_snn_populations_valid"])

    def test_a_malformed_declared_gate_compute_carrier_is_not_skipped(self):
        record = gate_snn_fixture()
        record["gate_compute"] = "bad"
        record["language_view"]["trajectory"]["gate_compute"] = {
            "per_check": [{"neurons": 2, "mean_rate_hz": 10.0, "window_s": 0.05, "spikes": 1}]
        }

        self.assertEqual(curate_bridge._gate_compute_sidecar(record), ("gate_compute", "bad"))
        status = curate_bridge.raster_status(record)

        self.assertFalse(status["raster_valid"])
        self.assertIn(curate_bridge.REASON_RASTER_SPIKE_BUDGET, status["reason_codes"])

    def test_gate_compute_budget_operands_must_be_physically_positive(self):
        for check in (
            {"neurons": -2, "mean_rate_hz": -3.0, "window_s": 1.0, "spikes": 6},
            {"neurons": 0, "mean_rate_hz": 10.0, "window_s": 0.05, "spikes": 0},
            {"neurons": 4, "mean_rate_hz": 10.0, "window_s": -0.05, "spikes": -2},
        ):
            with self.subTest(check=check):
                record = gate_snn_fixture()
                record["gate_compute"] = {"per_check": [check]}

                status = curate_bridge.raster_status(record)

                self.assertFalse(status["raster_valid"])
                self.assertIn(
                    curate_bridge.REASON_RASTER_SPIKE_BUDGET,
                    status["reason_codes"],
                )

    def test_a_well_formed_gate_compute_budget_still_passes(self):
        record = gate_snn_fixture()
        record["gate_compute"] = {
            "per_check": [{"neurons": 4, "mean_rate_hz": 10.0, "window_s": 0.05, "spikes": 2}],
            "total_energy_pJ": 2 * curate_bridge.RASTER_ENERGY_PJ_PER_SPIKE,
        }

        status = curate_bridge.raster_status(record)

        self.assertTrue(status["raster_valid"], status["reason_codes"])
        self.assertTrue(status["evidence"]["gate_compute_spike_budget_valid"])

    def test_large_integer_raster_energy_does_not_hide_one_pj_mismatch(self):
        record = gate_snn_fixture()
        spikes = 2**53
        expected_energy = spikes * curate_bridge.RASTER_ENERGY_PJ_PER_SPIKE
        record["raster"].update(
            {
                "neurons": spikes,
                "mean_rate_hz": 25,
                "window_ms": 40,
                "window_s": 0.04,
                "spikes": spikes,
                "energy_pJ": expected_energy,
            }
        )
        record["raster"].pop("energy_uJ", None)

        exact = curate_bridge.raster_status(record)
        self.assertTrue(exact["raster_valid"], exact["reason_codes"])
        self.assertEqual(
            exact["evidence"]["raster_expected_energy_pJ"],
            expected_energy,
        )
        self.assertEqual(float(expected_energy), float(expected_energy + 1))

        record["raster"]["energy_pJ"] = expected_energy + 1
        mismatch = curate_bridge.raster_status(record)
        self.assertFalse(mismatch["raster_valid"])
        self.assertIn(curate_bridge.REASON_RASTER_ENERGY, mismatch["reason_codes"])

    def test_large_integer_gate_total_does_not_hide_one_pj_mismatch(self):
        record = gate_snn_fixture()
        spikes = 2**53
        expected_energy = spikes * curate_bridge.RASTER_ENERGY_PJ_PER_SPIKE
        record["gate_compute"] = {
            "per_check": [
                {
                    "neurons": spikes,
                    "mean_rate_hz": 1,
                    "window_s": 1,
                    "spikes": spikes,
                }
            ],
            "total_energy_pJ": expected_energy,
        }

        exact = curate_bridge.raster_status(record)
        self.assertTrue(exact["raster_valid"], exact["reason_codes"])

        record["gate_compute"]["total_energy_pJ"] = expected_energy + 1
        mismatch = curate_bridge.raster_status(record)
        self.assertFalse(mismatch["raster_valid"])
        self.assertIn(curate_bridge.REASON_RASTER_ENERGY, mismatch["reason_codes"])

    def test_decimal_pj_token_does_not_hide_one_pj_mismatch(self):
        record = _scaled_raster_record(
            10**16, "energy_pJ", parse_finite_json_float("230000000000000001.0")
        )

        status = curate_bridge.raster_status(record)

        self.assertFalse(status["raster_valid"])
        self.assertIn(curate_bridge.REASON_RASTER_ENERGY, status["reason_codes"])

    def test_large_exact_uj_token_matches_integer_spike_energy(self):
        record = _scaled_raster_record(
            2**52, "energy_uJ", parse_finite_json_float("103582791429.521408")
        )

        status = curate_bridge.raster_status(record)

        self.assertTrue(status["raster_valid"], status["reason_codes"])

    def test_precision_sensitive_rate_is_preserved_in_evidence(self):
        record = gate_snn_fixture()
        rate = parse_finite_json_float("12.000000000000001")
        record["raster"]["mean_rate_hz"] = rate

        status = curate_bridge.raster_status(record)

        self.assertTrue(status["raster_valid"], status["reason_codes"])
        emitted = status["evidence"]["raster_rate_hz"]
        self.assertEqual(exact_fraction(emitted), exact_fraction(rate))
        self.assertIn("12.000000000000001", dumps_exact_json(status["evidence"]))

    def test_subnormal_third_factor_tau_is_preserved_in_evidence(self):
        record = gate_snn_fixture()
        tau = parse_finite_json_float("1e-400")
        record["raster"]["routing"]["third_factor"]["tau_e_s"] = tau

        status = curate_bridge.raster_status(record)

        self.assertTrue(status["raster_valid"], status["reason_codes"])
        emitted = status["evidence"]["raster_third_factor_tau_e_s"]
        self.assertEqual(exact_fraction(emitted), exact_fraction(tau))
        self.assertIn("1e-400", dumps_exact_json(status["evidence"]))

    def test_derived_alias_beyond_exact_bound_fails_closed(self):
        record = gate_snn_fixture()
        record["raster"].pop("window_s", None)
        record["raster"]["window_ms"] = parse_finite_json_float("1e-4096")

        status = curate_bridge.raster_status(record)

        self.assertFalse(status["raster_valid"])
        self.assertIn(curate_bridge.REASON_RASTER_WINDOW, status["reason_codes"])

    def test_conflicting_eligibility_time_aliases_are_rejected(self):
        record = gate_snn_fixture()
        record["raster"]["routing"]["third_factor"]["tau_e_ms"] = 1

        status = curate_bridge.raster_status(record)

        self.assertFalse(status["raster_valid"])
        self.assertIn(curate_bridge.REASON_THIRD_FACTOR_INVALID, status["reason_codes"])

    def test_agreeing_eligibility_time_aliases_stay_valid(self):
        record = gate_snn_fixture()
        record["raster"]["routing"]["third_factor"]["tau_e_ms"] = 2000

        status = curate_bridge.raster_status(record)

        self.assertTrue(status["raster_valid"], status["reason_codes"])
        self.assertEqual(status["evidence"]["raster_third_factor_tau_e_s"], 2.0)


if __name__ == "__main__":
    unittest.main()
