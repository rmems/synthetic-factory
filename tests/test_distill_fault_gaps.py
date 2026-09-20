#!/usr/bin/env python3
"""Fault-recovery family gap tests (tamper-and-recheck regressions).

Split out of ``test_distillation_review_gaps.py``: every test fails against
the code as it stood before the fix it names. The recurring shape is: take a
record the generator produced, tamper with one derived field, recompute
``provenance.record_sha256`` so the digest check is satisfied, and assert the
family checker still objects.
"""

import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "pipelines"))



import fault_recovery as fr  # noqa: E402
from oracle_grounded import distill_contract as oc  # noqa: E402
from distill_gap_test_support import clone, rehash  # noqa: E402

class FaultRecoveryGaps(unittest.TestCase):
    """fault_recovery.py"""

    def record(self, seed: int = 3, count: int = 9) -> list[dict]:
        return fr.build_records(seed, count)

    def test_a_flipped_deterministic_outcome_is_re_derived(self):
        # The simulator is the oracle and the scenario fully determines its
        # answer, so a relabelled outcome is checkable, not merely unprovable.
        for record in self.record():
            other = next(o for o in fr.OUTCOMES if o != record["result"]["outcome"])
            tampered = clone(record)
            tampered["result"]["outcome"] = other
            tampered["result"]["outcome_label"] = fr.OUTCOME_LABELS[other]
            tampered["result"]["reason_codes"] = ["RELABELLED"]
            rehash(tampered)
            with self.subTest(record=record["id"]):
                self.assertEqual(oc.check_digest(tampered, "x"), [])
                errors = fr.check_family(tampered, "x")
                self.assertTrue(
                    any("OUTCOME_NOT_REPRODUCIBLE" in error for error in errors),
                    f"a relabelled outcome passed: {errors}",
                )

    def test_an_untampered_fault_record_still_validates(self):
        for record in self.record():
            with self.subTest(record=record["id"]):
                self.assertEqual(fr.check_family(record, "x"), [])

    def test_the_scenario_disturbance_must_match_the_intervention(self):
        record = clone(self.record(count=1)[0])
        other = next(k for k in fr.DISTURBANCES if k != record["intervention"]["kind"])
        record["scenario"]["disturbance_kind"] = other
        rehash(record)
        errors = fr.check_family(record, "x")
        self.assertTrue(
            any("DISTURBANCE_KIND_MISMATCH" in error for error in errors),
            f"a mismatched scenario/intervention pair passed: {errors}",
        )

    def test_an_unknown_malformed_burst_variant_is_refused(self):
        simulator = fr.RelayReflexSimulator()
        scenario = {"system": dict(fr.DEFAULT_SYSTEM)}
        disturbance = {
            "kind": "malformed_spike_burst",
            "parameters": {
                "channels": ["c0"],
                "malformed_count": 3,
                # A typo for "negative_amplitude". Silently treating it as
                # unknown_channel would fabricate a drop the caller never asked
                # for and label it authoritative.
                "malformed_kind": "negative_amplitdue",
            },
        }
        with self.assertRaises(oc.ContractError):
            simulator.run(scenario, disturbance)

    def test_every_declared_malformed_variant_still_runs(self):
        simulator = fr.RelayReflexSimulator()
        scenario = {"system": dict(fr.DEFAULT_SYSTEM)}
        for kind in fr.MALFORMED_KINDS:
            with self.subTest(kind=kind):
                result = simulator.run(
                    scenario,
                    {
                        "kind": "malformed_spike_burst",
                        "parameters": {
                            "channels": ["c0"],
                            "malformed_count": 3,
                            "malformed_kind": kind,
                        },
                    },
                )
                self.assertIn(result.outcome, fr.OUTCOMES)


class FaultChannelAndParameterGaps(unittest.TestCase):
    """fault_recovery.py: disturbances must not silently run as no-ops."""

    def setUp(self):
        self.sim = fr.RelayReflexSimulator()
        self.scenario = {"system": dict(fr.DEFAULT_SYSTEM)}

    def test_a_disturbance_naming_an_unknown_channel_is_refused(self):
        # A name absent from the relay and the fallback source used to be
        # silently narrowed away: the fault became a no-op that replayed as
        # an authoritative `continue`.
        with self.assertRaises(oc.ContractError) as caught:
            self.sim.run(
                self.scenario,
                {
                    "kind": "sensor_loss",
                    "parameters": {
                        "channels": ["typo"], "onset_ms": 4.0, "duration_ms": 14.0
                    },
                },
            )
        self.assertIn("unknown channels", str(caught.exception))

    def test_a_malformed_burst_on_only_unknown_channels_is_refused(self):
        with self.assertRaises(oc.ContractError):
            self.sim.run(
                self.scenario,
                {
                    "kind": "malformed_spike_burst",
                    "parameters": {
                        "channels": ["ghost"],
                        "malformed_count": 3,
                        "malformed_kind": "negative_amplitude",
                    },
                },
            )

    def test_a_crafted_unknown_channel_record_fails_validation(self):
        record = clone(fr.build_records(3, 9)[0])
        record["intervention"]["parameters"]["channels"] = ["typo"]
        rehash(record)
        errors = fr.check_family(record, "x")
        self.assertTrue(
            any("OUTCOME_NOT_REPRODUCIBLE" in error for error in errors),
            f"an unknown-channel intervention validated: {errors}",
        )

    def test_naming_the_fallback_source_is_still_a_known_channel(self):
        # The fallback source is a legitimate target (its loss must be seen),
        # so the unknown-channel guard may not reject it.
        result = self.sim.run(
            self.scenario,
            {
                "kind": "sensor_loss",
                "parameters": {
                    "channels": ["c0", "redundant_relay_b"],
                    "onset_ms": 4.0,
                    "duration_ms": 14.0,
                },
            },
        )
        self.assertIn(result.outcome, fr.OUTCOMES)

    def test_an_out_of_range_corrupt_ratio_is_refused(self):
        # A non-positive (or NaN) ratio can never mark an event corrupt, so
        # the declared disturbance ran as a no-op labelled `continue`.
        for ratio in (
            -0.5, 0.0, 1.5, float("nan"), float("inf"), "0.4", None, True
        ):
            with self.subTest(ratio=ratio):
                with self.assertRaises(oc.ContractError):
                    self.sim.run(
                        self.scenario,
                        {
                            "kind": "burst_corruption",
                            "parameters": {
                                "channels": ["c0"],
                                "onset_ms": 2.0,
                                "duration_ms": 40.0,
                                "corrupt_ratio": ratio,
                            },
                        },
                    )

    def test_the_ratio_boundaries_are_still_legal(self):
        # Zero is not a boundary here: it applies no corruption at all.
        for ratio in (0.5, 1.0):
            with self.subTest(ratio=ratio):
                result = self.sim.run(
                    self.scenario,
                    {
                        "kind": "burst_corruption",
                        "parameters": {
                            "channels": ["c0"],
                            "onset_ms": 2.0,
                            "duration_ms": 40.0,
                            "corrupt_ratio": ratio,
                        },
                    },
                )
                self.assertIn(result.outcome, fr.OUTCOMES)


class FaultMeterProvenanceGaps(unittest.TestCase):
    """fault_recovery.py: measurement meters come from the oracle boundary."""

    def test_an_injected_oracle_names_its_own_meters(self):
        # build_records used to hard-code simulator_* meters, so a hardware
        # replay's readings carried false measurement provenance.
        class BenchReplay(fr.RelayReflexSimulator):
            meter_clock = "bench_replay_clock"
            meter_state = "bench_replay_state"
            meter_thermal = "bench_replay_thermal_probe"

        records = fr.build_records(3, 2, oracle=BenchReplay())
        meters = {
            item["meter"]
            for record in records
            for item in record["result"]["measurements"]
        }
        self.assertTrue(meters)
        self.assertFalse(
            {meter for meter in meters if meter.startswith("simulator_")},
            meters,
        )
        self.assertLessEqual(
            meters,
            {"bench_replay_clock", "bench_replay_state", "bench_replay_thermal_probe"},
        )

    def test_an_oracle_without_meters_is_refused_case(self):
        oracle = fr.FaultOracle()
        with self.assertRaises(oc.ContractError) as caught:
            fr.build_records(3, 1, oracle=oracle)
        self.assertIn("measurement meters", str(caught.exception))

    def test_the_simulator_still_names_simulator_meters(self):
        record = fr.build_records(3, 1)[0]
        meters = {item["meter"] for item in record["result"]["measurements"]}
        self.assertLessEqual(
            meters,
            {"simulator_clock", "simulator_state", "simulator_thermal_model"},
        )


class FaultNoOpValueGaps(unittest.TestCase):
    """fault_recovery.py: parameter values that run as silent no-ops."""

    def setUp(self):
        self.sim = fr.RelayReflexSimulator()
        self.scenario = {"system": dict(fr.DEFAULT_SYSTEM)}

    def _run(self, kind, **parameters):
        return self.sim.run(self.scenario, {"kind": kind, "parameters": parameters})

    def test_invalid_numeric_parameters_are_refused(self):
        # A negative duration never opens the window; zero jitter perturbs
        # nothing; a zero-event burst is no burst. Each ran as `continue`.
        cases = [
            ("sensor_loss", {"channels": ["c0"], "onset_ms": 4.0, "duration_ms": -5.0}),
            ("sensor_loss", {"channels": ["c0"], "onset_ms": -1.0, "duration_ms": 5.0}),
            ("sensor_loss", {"channels": ["c0"], "onset_ms": 4.0, "duration_ms": 0.0}),
            (
                "event_jitter",
                {"channels": ["c0"], "onset_ms": 2.0, "duration_ms": 10.0,
                 "jitter_ms": 0.0},
            ),
            (
                "malformed_spike_burst",
                {"channels": ["c0"], "malformed_count": 0,
                 "malformed_kind": "negative_amplitude"},
            ),
            ("delayed_result", {"channels": ["c0"], "delay_ms": 0.0}),
            (
                "thermal_excursion",
                {"onset_ms": 6.0, "ramp_ms": -8.0, "peak_c": 84.0},
            ),
            (
                "thermal_excursion",
                {"onset_ms": 6.0, "ramp_ms": 8.0, "peak_c": float("nan")},
            ),
        ]
        for kind, parameters in cases:
            with self.subTest(kind=kind, parameters=parameters):
                with self.assertRaises(oc.ContractError):
                    self._run(kind, **parameters)

    def test_boundary_values_are_still_legal(self):
        result = self._run(
            "sensor_loss", channels=["c0"], onset_ms=0.0, duration_ms=6.0
        )
        self.assertIn(result.outcome, fr.OUTCOMES)

    def test_a_flipped_prediction_agreement_is_re_derived(self):
        records = fr.build_records(3, 9)
        record = clone(
            next(
                r for r in records
                if r["result"]["prediction_agreement"] == "disagree"
            )
        )
        record["result"]["prediction_agreement"] = "agree"
        rehash(record)
        errors = fr.check_family(record, "x")
        self.assertTrue(
            any("prediction_agreement" in error for error in errors),
            f"a flipped prediction_agreement passed: {errors}",
        )

    def test_dropped_replay_measurements_are_reported(self):
        record = clone(fr.build_records(3, 1)[0])
        record["result"]["measurements"] = [
            item
            for item in record["result"]["measurements"]
            if item["quantity"] == "peak_temperature_c"
        ]
        rehash(record)
        errors = fr.check_family(record, "x")
        self.assertTrue(
            any(
                "the record does not carry" in error and "recovery_latency_ms" in error
                for error in errors
            ),
            f"wholesale-deleted replay measurements passed: {errors}",
        )




class FourthRoundFaultGaps(unittest.TestCase):
    """fault_recovery.py — the fourth review pass."""

    @classmethod
    def setUpClass(cls):
        cls.records = fr.build_records(11, 12)

    def test_a_disturbance_beyond_the_horizon_is_refused(self):
        # onset_ms >= the horizon satisfied the non-negative floor while the
        # active window never opened: a declared fault replaying as an
        # authoritative `continue`.
        simulator = fr.RelayReflexSimulator()
        scenario = {"system": dict(fr.DEFAULT_SYSTEM)}
        last_tick_ms = (fr.DEFAULT_SYSTEM["ticks"] - 1) * fr.DEFAULT_SYSTEM["tick_ms"]

        def disturbance(onset):
            return {
                "kind": "sensor_loss",
                "parameters": {
                    "onset_ms": onset,
                    "duration_ms": 10.0,
                    "channels": ["c0"],
                },
            }

        for onset in (100.0, last_tick_ms + 1.0):
            with self.subTest(onset=onset):
                test_disturbance = disturbance(onset)
                with self.assertRaises(oc.ContractError):
                    simulator.run(scenario, test_disturbance)
        # The last observable tick is still a real fault window.
        simulator.run(scenario, disturbance(last_tick_ms))

    def test_a_tampered_onset_beyond_the_horizon_is_a_finding(self):
        record = next(
            clone(r)
            for r in self.records
            if r["intervention"]["kind"] == "sensor_loss"
        )
        record["intervention"]["parameters"]["onset_ms"] = 100.0
        rehash(record)
        errors = fr.check_family(record, "x")
        self.assertTrue(
            any("never occur" in e for e in errors),
            f"an out-of-window onset passed: {errors}",
        )

    def test_the_integrity_flag_must_be_present(self):
        # Deleting result.integrity_violation skipped the comparison, losing
        # a malformed-spike record's `true` integrity signal.
        record = next(
            clone(r)
            for r in self.records
            if r["result"].get("integrity_violation") is True
        )
        del record["result"]["integrity_violation"]
        rehash(record)
        errors = fr.check_family(record, "x")
        self.assertTrue(
            any("integrity_violation must be a boolean" in e for e in errors),
            f"a record without the replayed integrity flag passed: {errors}",
        )




class FifthRoundFaultGaps(unittest.TestCase):
    """fault_recovery.py — fifth pass."""

    @classmethod
    def setUpClass(cls):
        cls.records = fr.build_records(11, 12)

    def test_invalid_system_controls_are_refused_case(self):
        # corruption_quarantine_ratio: -1 flipped a below-threshold
        # corruption from degrade_gracefully to quarantine with zero
        # findings; a scrambled thermal ladder rewrites the tiers the same
        # way.
        base = next(
            clone(r)
            for r in self.records
            if r["intervention"]["kind"] == "burst_corruption"
        )
        for key, value, fragment in (
            ("corruption_quarantine_ratio", -1, "corruption_quarantine_ratio"),
            ("thermal_shutdown_c", 10.0, "thermal ladder"),
            ("ticks", 0, "ticks"),
            ("tick_ms", 0, "tick_ms"),
        ):
            record = clone(base)
            system = dict(record["scenario"].get("system", {}))
            system[key] = value
            record["scenario"]["system"] = system
            rehash(record)
            with self.subTest(control=key):
                simulator = fr.RelayReflexSimulator()
                with self.assertRaises(oc.ContractError) as caught:
                    simulator.run(record["scenario"], record["intervention"])
                self.assertIn(fragment, str(caught.exception))
                errors = fr.check_family(record, "x")
                self.assertTrue(
                    any(fragment in e for e in errors),
                    f"an invalid {key} passed validation: {errors}",
                )

    def test_the_oracle_configuration_must_describe_the_replayed_system(self):
        for mutate, fragment in (
            ("system", "does not match"),
            ("missing", "must record the simulator's"),
            ("precedence", "canonical"),
        ):
            record = clone(self.records[0])
            if mutate == "system":
                record["oracle"]["configuration"]["system"] = {"tick_ms": 999}
            elif mutate == "missing":
                del record["oracle"]["configuration"]
            else:
                record["oracle"]["configuration"]["precedence"] = ["continue"]
            rehash(record)
            with self.subTest(mutate=mutate):
                errors = fr.check_family(record, "x")
                self.assertTrue(
                    any(fragment in e for e in errors),
                    f"a rewritten oracle configuration passed: {errors}",
                )

    def test_the_prediction_agreement_field_must_be_present(self):
        record = clone(self.records[0])
        del record["result"]["prediction_agreement"]
        rehash(record)
        errors = fr.check_family(record, "x")
        self.assertTrue(
            any("prediction_agreement must be present" in e for e in errors),
            f"a record without the derived agreement passed: {errors}",
        )




class SixthRoundFaultGaps(unittest.TestCase):
    """fault_recovery.py — sixth pass."""

    @classmethod
    def setUpClass(cls):
        cls.records = fr.build_records(11, 12)

    def test_the_scenario_must_name_its_disturbance(self):
        record = clone(self.records[0])
        del record["scenario"]["disturbance_kind"]
        rehash(record)
        errors = fr.check_family(record, "x")
        self.assertTrue(
            any("disturbance_kind must be present" in e for e in errors),
            f"a scenario without its fault name passed: {errors}",
        )

    def test_agreement_requires_its_source_prediction(self):
        for mutate in ("candidate_prediction", "predicted_outcome"):
            record = clone(self.records[1])
            if mutate == "candidate_prediction":
                del record["candidate_prediction"]
            else:
                del record["candidate_prediction"]["predicted_outcome"]
            rehash(record)
            with self.subTest(removed=mutate):
                errors = fr.check_family(record, "x")
                self.assertTrue(
                    any("needs the prediction it grades" in e for e in errors),
                    f"an unanchored agreement label passed: {errors}",
                )

    def test_a_reading_the_replay_does_not_derive_is_a_finding(self):
        record = next(
            clone(r)
            for r in self.records
            if fr.RelayReflexSimulator()
            .run(r["scenario"], r["intervention"])
            .detection_latency_ms
            is None
        )
        record["result"]["measurements"].append(
            oc.new_measurement("detection_latency_ms", 3.5, "simulator_state")
        )
        rehash(record)
        errors = fr.check_family(record, "x")
        self.assertTrue(
            any("derives no such measurement" in e for e in errors),
            f"a fabricated latency target passed: {errors}",
        )

    def test_replay_workloads_are_bounded(self):
        # The validator replays untrusted scenarios: every live channel for
        # every tick, one trace entry per tick. Unbounded controls let one
        # record buy an arbitrarily large replay.
        for key, value, fragment in (
            ("ticks", 1001, "ticks"),
            ("channels", [f"c{i}" for i in range(33)], "channel"),
        ):
            record = clone(self.records[0])
            system = dict(record["scenario"].get("system", {}))
            system[key] = value
            record["scenario"]["system"] = system
            rehash(record)
            with self.subTest(control=key):
                simulator = fr.RelayReflexSimulator()
                with self.assertRaises(oc.ContractError):
                    simulator.run(record["scenario"], record["intervention"])
                errors = fr.check_family(record, "x")
                self.assertTrue(
                    any(fragment in e for e in errors),
                    f"an oversized {key} passed validation: {errors}",
                )




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




