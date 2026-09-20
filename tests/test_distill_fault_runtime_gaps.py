#!/usr/bin/env python3
"""Fault-recovery runtime/oracle-configuration gap tests.

Split out of ``test_distill_fault_gaps.py``: declarations that would run as
silent no-ops, and the oracle block's binding to the simulated controls.
"""

import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "pipelines"))

import fault_recovery as fr  # noqa: E402
from oracle_grounded import distill_contract as oc  # noqa: E402
from distill_gap_test_support import clone, rehash  # noqa: E402


class FaultRunTimeContractGaps(unittest.TestCase):
    """fault_recovery.py: declarations that would run as silent no-ops."""

    def setUp(self):
        self.sim = fr.RelayReflexSimulator()
        self.scenario = {"system": dict(fr.DEFAULT_SYSTEM)}

    def _run(self, kind, **parameters):
        return self.sim.run(self.scenario, {"kind": kind, "parameters": parameters})

    def test_an_unknown_system_control_is_refused(self):
        # A typo'd key would be silently ignored while the record claims the
        # caller's system was simulated.
        scenario = {"system": {**fr.DEFAULT_SYSTEM, "ambint_c": 50.0}}
        with self.assertRaises(oc.ContractError):
            self.sim.run(
                scenario,
                {"kind": "delayed_result",
                 "parameters": {"channels": ["c0"], "delay_ms": 4.0}},
            )

    def test_a_flat_thermal_ladder_is_refused(self):
        # Equal rungs made the ladder a no-op: the relay can never warn before
        # it is already past the limit.
        scenario = {"system": {**fr.DEFAULT_SYSTEM, "thermal_warn_c": 38.0}}
        with self.assertRaises(oc.ContractError):
            self.sim.run(
                scenario,
                {"kind": "thermal_excursion",
                 "parameters": {"onset_ms": 4.0, "ramp_ms": 8.0, "peak_c": 90.0}},
            )

    def test_a_peak_at_or_below_ambient_is_refused(self):
        ambient = fr.DEFAULT_SYSTEM["ambient_c"]
        for peak in (ambient - 1.0, ambient):
            with self.subTest(peak=peak):
                with self.assertRaises(oc.ContractError):
                    self._run(
                        "thermal_excursion",
                        onset_ms=4.0, ramp_ms=8.0, peak_c=peak,
                    )

    def test_a_thermal_onset_on_the_last_tick_is_refused(self):
        # The excursion ramps by fraction of ramp_ms; starting on the last
        # tick leaves no tick where the ramp fraction is nonzero.
        last_tick_ms = (
            fr.DEFAULT_SYSTEM["ticks"] - 1
        ) * fr.DEFAULT_SYSTEM["tick_ms"]
        for onset in (last_tick_ms, last_tick_ms + 1.0):
            with self.subTest(onset=onset):
                with self.assertRaises(oc.ContractError):
                    self._run(
                        "thermal_excursion",
                        onset_ms=onset, ramp_ms=8.0, peak_c=90.0,
                    )

    def test_a_fallback_only_channel_list_is_refused(self):
        # "redundant_relay_b" is a known name (the fallback source) but the
        # tick loop visits primary channels only — the declared fault would
        # affect nothing.
        with self.assertRaises(oc.ContractError):
            self._run(
                "sensor_loss",
                channels=["redundant_relay_b"],
                onset_ms=4.0,
                duration_ms=8.0,
            )

    def test_a_malformed_count_beyond_burst_capacity_is_refused(self):
        # One malformed event per affected live channel per tick: 1 channel
        # over 24 ticks can emit at most 24.
        with self.assertRaises(oc.ContractError):
            self._run(
                "malformed_spike_burst",
                channels=["c0"],
                malformed_count=fr.DEFAULT_SYSTEM["ticks"] + 1,
                malformed_kind="negative_amplitude",
            )


class FaultOracleConfigurationGaps(unittest.TestCase):
    """fault_recovery.py: the oracle block binds the simulated controls."""

    @classmethod
    def setUpClass(cls):
        cls.records = fr.build_records(3, 6)

    def test_a_tampered_declared_system_is_a_finding(self):
        # The oracle records the merged effective system, so a validator
        # replaying the scenario against the declared system must catch the
        # swap even when the scenario itself was left alone.
        record = clone(self.records[0])
        record["oracle"]["configuration"]["system"]["ambient_c"] = 10.0
        rehash(record)
        errors = fr.check_family(record, "x")
        self.assertTrue(
            any("configuration" in error for error in errors),
            f"a swapped declared system passed: {errors}",
        )

    def test_a_relabelled_meter_is_a_finding(self):
        # Quantities are replayed through the meter the oracle declares for
        # them; renaming the meter keeps the value right while the provenance
        # lies.
        record = clone(self.records[0])
        for item in record["result"]["measurements"]:
            if item["quantity"] == "detection_latency_ms":
                item["meter"] = "simulator_state"
        rehash(record)
        errors = fr.check_family(record, "x")
        self.assertTrue(
            any("reads it from" in error for error in errors),
            f"a relabelled meter passed: {errors}",
        )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
