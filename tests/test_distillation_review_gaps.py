#!/usr/bin/env python3
"""Regression tests for the review findings on the #78 distillation families.

Every test here fails against the code as it stood before the fix it names.
The recurring shape is: take a record the generator produced, tamper with one
derived field, recompute ``provenance.record_sha256`` so the digest check is
satisfied, and assert the family checker still objects. A finding that only
the digest catches is not a finding — the digest only proves the file has not
been edited since it was written, not that what was written was true.
"""

import json
import math
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "pipelines"))

import energy_preferences as ep  # noqa: E402
import fault_recovery as fr  # noqa: E402
import moe_router as mr  # noqa: E402
import oracle_contract as oc  # noqa: E402
import router_baseline as rb  # noqa: E402
import validate_distill as vd  # noqa: E402


def rehash(record: dict) -> dict:
    """Re-stamp the content digest so only the family check can object."""

    record["provenance"]["record_sha256"] = oc.record_digest(record)
    return record


def clone(record: dict) -> dict:
    return json.loads(json.dumps(record))


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
        # A negative (or NaN) ratio can never mark an event corrupt, so the
        # declared disturbance ran as a no-op labelled `continue`.
        for ratio in (-0.5, 1.5, float("nan"), float("inf"), "0.4", None, True):
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
        for ratio in (0.0, 1.0):
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

    def test_an_oracle_without_meters_is_refused(self):
        with self.assertRaises(oc.ContractError) as caught:
            fr.build_records(3, 1, oracle=fr.FaultOracle())
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


class EnergyScenarioBindingGaps(unittest.TestCase):
    """energy_preferences.py: the scenario the labels are grounded in."""

    @classmethod
    def setUpClass(cls):
        cls.records = ep.build_records(20260824, 1, repeats=1, warmup=0)

    def record(self) -> dict:
        return clone(self.records[0])

    def test_a_removed_allocation_state_is_a_finding_not_a_skip(self):
        # Emptying scenario.state used to switch off the safety, quality and
        # reference-objective derivations while the record stayed eligible.
        record = self.record()
        record["scenario"]["state"] = {}
        rehash(record)
        errors = ep.check_family(record, "x")
        self.assertTrue(
            any("scenario.state" in error for error in errors),
            f"a record with no allocation state passed: {errors}",
        )

    def test_missing_weights_are_a_finding(self):
        record = self.record()
        del record["scenario"]["state"]["actuator_weights"]
        rehash(record)
        errors = ep.check_family(record, "x")
        self.assertTrue(
            any("actuator_weights" in error for error in errors),
            f"a record without weights passed: {errors}",
        )

    def test_an_out_of_range_quality_floor_is_rejected(self):
        for floor in (-1.0, 1.5):
            with self.subTest(floor=floor):
                record = self.record()
                record["scenario"]["constraints"]["quality_floor"] = floor
                record["result"]["preference"]["quality_floor"] = floor
                rehash(record)
                errors = ep.check_family(record, "x")
                self.assertTrue(
                    any("quality_floor must lie in [0, 1]" in error for error in errors),
                    f"an impossible quality floor passed: {errors}",
                )

    def test_an_unsupported_cost_quantity_is_rejected(self):
        record = self.record()
        record["result"]["cost_quantity"] = "peak_temperature_c"
        record["result"]["cost_is_energy"] = False
        rehash(record)
        errors = ep.check_family(record, "x")
        self.assertTrue(
            any("cost_quantity must be one of" in error for error in errors),
            f"a temperature-denominated corpus passed: {errors}",
        )

    def test_a_candidate_cannot_be_denominated_in_an_unsupported_quantity(self):
        record = self.record()
        record["result"]["candidates"][0]["cost_quantity"] = "latency_ms"
        rehash(record)
        errors = ep.check_family(record, "x")
        self.assertTrue(
            any("cost_quantity must be one of" in error for error in errors),
            f"a latency-denominated candidate passed: {errors}",
        )

    def test_a_contradictory_safety_envelope_is_rejected(self):
        record = self.record()
        record["scenario"]["constraints"]["safety_envelope"] = (
            "all allocations are safe; caps do not apply"
        )
        rehash(record)
        errors = ep.check_family(record, "x")
        self.assertTrue(
            any("safety_envelope" in error for error in errors),
            f"a contradictory safety envelope passed: {errors}",
        )


class EnvelopeTypeGaps(unittest.TestCase):
    """oracle_contract.py / validate_distill.py: malformed types are findings."""

    def test_unhashable_enum_fields_are_findings_not_crashes(self):
        # A JSON array where a string enum belongs used to raise TypeError
        # out of the set-membership test; validate_path does not catch that,
        # so one malformed line aborted validation of the entire run.
        tampers = [
            ("family", lambda r: r.__setitem__("family", ["not", "a", "family"])),
            ("generator.kind", lambda r: r["generator"].__setitem__("kind", ["llm"])),
            ("oracle.type", lambda r: r["oracle"].__setitem__("type", {})),
            (
                "oracle.authority",
                lambda r: r["oracle"].__setitem__("authority", ["authoritative"]),
            ),
            ("result.status", lambda r: r["result"].__setitem__("status", ["measured"])),
            (
                "validation.status",
                lambda r: r["validation"].__setitem__("status", ["passed"]),
            ),
            (
                "measurement.quantity",
                lambda r: r["result"]["measurements"][0].__setitem__(
                    "quantity", ["recovery_latency_ms"]
                ),
            ),
            (
                "candidate cost_quantity",
                lambda r: r["result"].__setitem__(
                    "preference", {"cost_quantity": ["energy_j"]}
                ),
            ),
        ]
        for label, tamper in tampers:
            with self.subTest(field=label):
                record = clone(fr.build_records(3, 1)[0])
                tamper(record)
                errors = vd.check_record(record, "x")
                self.assertTrue(errors, f"{label}: no findings reported")


class EnergyPreferenceGaps(unittest.TestCase):
    """energy_preferences.py"""

    @classmethod
    def setUpClass(cls):
        cls.records = ep.build_records(20260823, 2, repeats=1, warmup=0)

    def record(self) -> dict:
        return clone(self.records[0])

    def test_an_untampered_energy_record_still_validates(self):
        for record in self.records:
            with self.subTest(record=record["id"]):
                self.assertEqual(ep.check_family(record, "x"), [])

    def test_an_unsafe_allocation_cannot_claim_to_be_safe(self):
        # safety_ok is a summary of the allocation, not an independent fact.
        record = self.record()
        preferred_id = record["result"]["preference"]["preferred"]
        candidate = next(
            c for c in record["result"]["candidates"] if c["id"] == preferred_id
        )
        caps = record["scenario"]["state"]["actuator_caps"]
        candidate["allocation"] = [cap * 5.0 for cap in caps]
        candidate["safety_ok"] = True
        candidate["safety_violations"] = []
        rehash(record)
        errors = ep.check_family(record, "x")
        self.assertTrue(
            any("SAFETY_NOT_REPRODUCIBLE" in error for error in errors),
            f"an over-cap allocation passed as safe: {errors}",
        )

    def _sync_measurements(self, record: dict, candidate_id: str, twin: dict) -> None:
        """Point one candidate's oracle measurements at its own values."""

        for item in record["result"]["measurements"]:
            detail = item.get("detail")
            if not isinstance(detail, dict) or detail.get("candidate") != candidate_id:
                continue
            if item["quantity"] == twin["cost_quantity"]:
                item["value"] = twin["cost_value"]
                item["meter"] = twin["cost_meter"]
            elif item["quantity"] == "task_quality":
                item["value"] = twin["task_quality"]

    def _clone_onto(self, record: dict, template: dict, candidate_id: str) -> dict:
        """Make one candidate identical to the template in all the rule reads."""

        twin = next(
            c for c in record["result"]["candidates"] if c["id"] == candidate_id
        )
        twin["allocation"] = list(template["allocation"])
        twin["task_quality"] = template["task_quality"]
        twin["safety_ok"] = True
        twin["safety_violations"] = []
        twin["cost_value"] = template["cost_value"]
        twin["cost_quantity"] = template["cost_quantity"]
        twin["cost_meter"] = template["cost_meter"]
        self._sync_measurements(record, candidate_id, twin)
        return twin

    def _set_cost_measurement(
        self, record: dict, candidate_id: str, quantity: str, value: float
    ) -> None:
        """Restate one candidate's measured cost."""

        for item in record["result"]["measurements"]:
            detail = item.get("detail")
            if (
                isinstance(detail, dict)
                and detail.get("candidate") == candidate_id
                and item["quantity"] == quantity
            ):
                item["value"] = value

    def test_an_equal_cost_tie_must_break_to_the_lower_id(self):
        record = self.record()
        candidates = record["result"]["candidates"]
        preference = record["result"]["preference"]
        template = next(c for c in candidates if c["id"] == preference["preferred"])
        # Two feasible candidates, identical in every respect the decision rule
        # reads, tied on measured cost. `choose_preference` breaks that tie by
        # id, so naming the larger id must not validate.
        low_id, high_id = sorted(
            c["id"] for c in candidates if c["id"] != template["id"]
        )[:2]
        for candidate_id in (low_id, high_id):
            self._clone_onto(record, template, candidate_id)
        # Make the tie the cheapest pair, and name the wrong side of it.
        template["cost_value"] = float(template["cost_value"]) + 1.0
        self._set_cost_measurement(
            record, template["id"], template["cost_quantity"], template["cost_value"]
        )
        winner = next(c for c in candidates if c["id"] == high_id)
        preference["preferred"] = high_id
        preference["cost_value"] = winner["cost_value"]
        preference["cost_quantity"] = winner["cost_quantity"]
        preference["over"] = sorted(c["id"] for c in candidates if c["id"] != high_id)
        rehash(record)
        errors = ep.check_family(record, "x")
        self.assertTrue(
            any("TIE_NOT_BROKEN_BY_ID" in error for error in errors),
            f"the wrong side of a cost tie was preferred: {errors}",
        )
        self.assertFalse(
            any("NOT_MINIMAL_FEASIBLE_COST" in error for error in errors),
            f"a tie must not read as a strictly cheaper rival: {errors}",
        )

    def test_a_nonnumeric_preferred_cost_is_a_finding_not_a_crash(self):
        record = self.record()
        preferred_id = record["result"]["preference"]["preferred"]
        for candidate in record["result"]["candidates"]:
            if candidate["id"] == preferred_id:
                candidate["cost_value"] = "cheap"
        rehash(record)
        # Must not raise: one malformed record may not abort validation of the
        # whole run.
        errors = ep.check_family(record, "x")
        self.assertTrue(errors)

    def test_duplicate_candidate_ids_are_rejected(self):
        record = self.record()
        candidates = record["result"]["candidates"]
        duplicate = clone(candidates[1])
        duplicate["id"] = candidates[0]["id"]
        candidates.append(duplicate)
        rehash(record)
        errors = ep.check_family(record, "x")
        self.assertTrue(
            any("DUPLICATE_CANDIDATE_ID" in error for error in errors),
            f"a duplicate candidate id passed: {errors}",
        )

    def test_conflicting_measurements_for_one_candidate_are_rejected(self):
        record = self.record()
        measurements = record["result"]["measurements"]
        cost_quantity = record["result"]["cost_quantity"]
        original = next(
            item
            for item in measurements
            if item.get("quantity") == cost_quantity
            and isinstance(item.get("detail"), dict)
        )
        conflicting = clone(original)
        conflicting["value"] = float(original["value"]) + 1.0
        measurements.append(conflicting)
        rehash(record)
        errors = ep.check_family(record, "x")
        self.assertTrue(
            any("CONFLICTING_MEASUREMENT" in error for error in errors),
            f"two disagreeing readings for one candidate passed: {errors}",
        )

    def test_a_recording_must_name_the_physical_meter(self):
        meter = ep.RecordedEnergyMeter(
            {"observations": {"a": {"cost_value": 1.0}}, "cost_quantity": "energy_j"}
        )
        available, detail = meter.available()
        self.assertFalse(available, "a recording with no meter was accepted")
        self.assertIn("meter", detail)

    def test_a_recording_that_names_its_meter_is_accepted(self):
        meter = ep.RecordedEnergyMeter(
            {
                "meter": "external_power_meter",
                "cost_quantity": "energy_j",
                "observations": {"a": {"cost_value": 1.0}},
            }
        )
        available, _ = meter.available()
        self.assertTrue(available)
        # The instrument stays the physical meter, not the replay wrapper.
        self.assertEqual(meter.lookup("a").meter, "external_power_meter")

    def test_a_negative_recorded_cost_is_refused(self):
        meter = ep.RecordedEnergyMeter(
            {
                "meter": "external_power_meter",
                "cost_quantity": "energy_j",
                "observations": {"a": {"cost_value": -1.0}},
            }
        )
        with self.assertRaises(oc.OracleUnavailable):
            meter.lookup("a")

    def test_a_negative_candidate_cost_is_a_finding(self):
        record = self.record()
        candidate = record["result"]["candidates"][0]
        candidate["cost_value"] = -1.0
        for item in record["result"]["measurements"]:
            detail = item.get("detail")
            if (
                isinstance(detail, dict)
                and detail.get("candidate") == candidate["id"]
                and item.get("quantity") == candidate["cost_quantity"]
            ):
                item["value"] = -1.0
        rehash(record)
        errors = ep.check_family(record, "x")
        self.assertTrue(
            any("NEGATIVE_COST" in error for error in errors),
            f"a negative measured cost passed: {errors}",
        )


class EnergyMeterAndDerivationGaps(unittest.TestCase):
    """energy_preferences.py: RAPL zones, replay binding, measured readings."""

    @classmethod
    def setUpClass(cls):
        cls.records = ep.build_records(20260823, 1, repeats=1, warmup=0)

    def record(self) -> dict:
        return clone(self.records[0])

    @staticmethod
    def _rapl_tree(root: Path, zones: dict[str, tuple[str, int]]) -> None:
        for zone, (label, microjoules) in zones.items():
            domain = root / zone
            domain.mkdir()
            (domain / "energy_uj").write_text(f"{microjoules}\n")
            (domain / "name").write_text(f"{label}\n")

    def test_rapl_subzones_are_not_double_counted(self):
        # The package counter already includes its core/uncore children, so
        # summing every flat entry counted selected components twice and
        # could reorder the preference between workloads with different
        # component mixes.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._rapl_tree(
                root,
                {
                    "intel-rapl:0": ("package-0", 1_000_000),
                    "intel-rapl:0:0": ("core", 500_000),
                },
            )
            meter = ep.RaplEnergyMeter(root=root)

            def workload():
                (root / "intel-rapl:0" / "energy_uj").write_text("3000000\n")
                (root / "intel-rapl:0:0" / "energy_uj").write_text("1500000\n")

            reading = meter.measure(workload, repeats=1, warmup=0)
            self.assertAlmostEqual(reading.cost_value, 2.0, places=6)

    def test_psys_beside_package_zones_is_not_added_on_top(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._rapl_tree(
                root,
                {
                    "intel-rapl:0": ("package-0", 1_000_000),
                    "intel-rapl:1": ("psys", 2_000_000),
                },
            )
            meter = ep.RaplEnergyMeter(root=root)

            def workload():
                (root / "intel-rapl:0" / "energy_uj").write_text("3000000\n")
                (root / "intel-rapl:1" / "energy_uj").write_text("9000000\n")

            reading = meter.measure(workload, repeats=1, warmup=0)
            self.assertAlmostEqual(reading.cost_value, 2.0, places=6)

    def test_a_lone_psys_zone_is_still_a_measurement(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._rapl_tree(root, {"intel-rapl:0": ("psys", 1_000_000)})
            meter = ep.RaplEnergyMeter(root=root)

            def workload():
                (root / "intel-rapl:0" / "energy_uj").write_text("4000000\n")

            reading = meter.measure(workload, repeats=1, warmup=0)
            self.assertAlmostEqual(reading.cost_value, 3.0, places=6)

    def test_a_replayed_cost_is_bound_to_the_solver_configuration(self):
        # A recording taken at one grid resolution used to replay cleanly
        # against another: the grid policy ran a different search while the
        # old energy reading was attached to it.
        scenario = ep.propose_scenarios(21, 1)[0]["scenario"]
        observations = {
            ep.workload_key(policy, scenario, fine_steps=12, coarse_steps=4): {
                "cost_value": cost
            }
            for policy, cost in (
                ("analytic_kkt", 8.0),
                ("coarse_grid", 3.0),
                ("exhaustive_grid", 31.0),
                ("unclipped_proportional", 0.2),
            )
        }
        meter = ep.RecordedEnergyMeter(
            {
                "run_id": "metered-run-2",
                "meter": "external_power_meter",
                "cost_quantity": "energy_j",
                "observations": observations,
            }
        )
        records = ep.build_records(
            21, 1, meter=meter, fine_steps=12, coarse_steps=4
        )
        self.assertEqual(ep.check_family(records[0], "x"), [])
        with self.assertRaises(oc.OracleUnavailable):
            ep.build_records(21, 1, meter=meter)

    def _preferred(self, record: dict) -> dict:
        preferred_id = record["result"]["preference"]["preferred"]
        return next(
            c for c in record["result"]["candidates"] if c["id"] == preferred_id
        )

    def _readings_for(self, record: dict, candidate_id: str, quantity: str):
        for item in record["result"]["measurements"]:
            detail = item.get("detail")
            if (
                isinstance(detail, dict)
                and detail.get("candidate") == candidate_id
                and item.get("quantity") == quantity
            ):
                yield item

    def test_a_cost_reading_marked_unmeasured_is_a_finding(self):
        # Every reading backing the preference marked `measured: false` used
        # to pass because unrelated wall-time readings stayed true.
        record = self.record()
        preferred = self._preferred(record)
        for item in self._readings_for(
            record, preferred["id"], preferred["cost_quantity"]
        ):
            item["measured"] = False
        rehash(record)
        errors = ep.check_family(record, "x")
        self.assertTrue(
            any("UNMEASURED_COST" in error for error in errors),
            f"an unmeasured preferred cost passed: {errors}",
        )

    def test_a_quality_reading_marked_unmeasured_is_a_finding(self):
        record = self.record()
        preferred = self._preferred(record)
        for item in self._readings_for(record, preferred["id"], "task_quality"):
            item["measured"] = False
        rehash(record)
        errors = ep.check_family(record, "x")
        self.assertTrue(
            any("UNMEASURED_TASK_QUALITY" in error for error in errors),
            f"an unmeasured quality reading passed: {errors}",
        )

    def test_a_jointly_edited_quality_is_re_derived_from_the_allocation(self):
        # Editing the candidate's quality and its measurement together kept
        # them agreeing while lowering the cheapest safe candidate below the
        # floor; the allocation arithmetic now pins both.
        record = self.record()
        preferred = self._preferred(record)
        preferred["task_quality"] = 0.5
        for item in self._readings_for(record, preferred["id"], "task_quality"):
            item["value"] = 0.5
        rehash(record)
        errors = ep.check_family(record, "x")
        self.assertTrue(
            any("QUALITY_NOT_REPRODUCIBLE" in error for error in errors),
            f"a jointly edited task_quality passed: {errors}",
        )

    def test_a_tampered_reference_objective_is_a_finding(self):
        record = self.record()
        record["result"]["reference_objective"] = (
            float(record["result"]["reference_objective"]) * 2.0
        )
        rehash(record)
        errors = ep.check_family(record, "x")
        self.assertTrue(
            any("reference_objective" in error for error in errors),
            f"a tampered reference objective passed: {errors}",
        )

    def test_preference_membership_fields_are_rederived(self):
        # `over`, `feasible` and `cheaper_but_constraint_violating` are
        # derived by choose_preference; arbitrary lists used to pass cleanly,
        # so pairwise consumers could receive no opponents at all.
        for field, bogus in (
            ("over", []),
            ("feasible", ["nonexistent_policy"]),
            # A named-but-never-measured policy: guaranteed to differ from
            # the derived list whatever this host's timings were.
            ("cheaper_but_constraint_violating", ["nonexistent_policy"]),
        ):
            with self.subTest(field=field):
                record = self.record()
                record["result"]["preference"][field] = bogus
                rehash(record)
                errors = ep.check_family(record, "x")
                self.assertTrue(
                    any(
                        "PREFERENCE_MEMBERSHIP_NOT_REPRODUCIBLE" in error
                        and f"preference.{field}" in error
                        for error in errors
                    ),
                    f"a fabricated {field} list passed: {errors}",
                )

    def test_a_restated_quality_floor_cannot_drift(self):
        record = self.record()
        record["result"]["preference"]["quality_floor"] = 0.5
        rehash(record)
        errors = ep.check_family(record, "x")
        self.assertTrue(
            any("preference.quality_floor" in error for error in errors),
            f"a drifted quality floor passed: {errors}",
        )


class RouterGaps(unittest.TestCase):
    """moe_router.py"""

    @classmethod
    def setUpClass(cls):
        cls.records = mr.build_records(11, 3, oracle=mr.ReferenceMoERouter())

    def record(self) -> dict:
        return clone(self.records[0])

    def test_an_untampered_router_record_still_validates(self):
        for record in self.records:
            with self.subTest(record=record["id"]):
                self.assertEqual(mr.check_family(record, "x"), [])

    def test_the_margin_is_recomputed_from_the_logits(self):
        record = self.record()
        layer = record["result"]["routing"]["layers"][0]
        self.assertIsInstance(layer.get("router_logits"), list)
        layer["top1_top2_margin"] = float(layer["top1_top2_margin"]) + 0.5
        rehash(record)
        errors = mr.check_family(record, "x")
        self.assertTrue(
            any("top1_top2_margin" in error for error in errors),
            f"a fabricated margin passed: {errors}",
        )

    def test_the_entropy_is_recomputed_from_the_logits(self):
        record = self.record()
        layer = record["result"]["routing"]["layers"][0]
        experts = len(layer["router_logits"])
        # Below ln(num_experts), so only a recomputation catches it.
        layer["routing_entropy"] = round(math.log(experts) * 0.5, 6)
        rehash(record)
        errors = mr.check_family(record, "x")
        self.assertTrue(
            any("routing_entropy" in error for error in errors),
            f"a fabricated entropy passed: {errors}",
        )

    def test_routing_layers_must_be_in_model_order(self):
        record = self.record()
        layers = record["result"]["routing"]["layers"]
        self.assertGreater(len(layers), 1)
        record["result"]["routing"]["layers"] = [layers[-1]] + layers[:-1]
        rehash(record)
        errors = mr.check_family(record, "x")
        self.assertTrue(
            any("model order" in error for error in errors),
            f"out-of-order routing layers passed: {errors}",
        )

    def test_a_malformed_configuration_digest_is_rejected(self):
        record = self.record()
        record["oracle"]["fingerprint"]["configuration_sha256"] = "not-a-digest"
        rehash(record)
        errors = mr.check_family(record, "x")
        self.assertTrue(
            any("configuration_sha256" in error for error in errors),
            f"a malformed configuration digest passed: {errors}",
        )

    def test_a_reference_router_needs_at_least_one_layer(self):
        with self.assertRaises(oc.ContractError):
            mr.ReferenceMoERouter(num_layers=0)
        with self.assertRaises(oc.ContractError):
            mr.ReferenceMoERouter(num_layers=-1)

    def test_a_mutable_teacher_revision_is_refused(self):
        # A branch name is not a checkpoint: the same name can serve different
        # weights tomorrow, and configuration_sha256 only covers the config.
        commit = "a" * 40
        self.assertEqual(mr.resolve_checkpoint(commit, None), commit)
        self.assertEqual(mr.resolve_checkpoint("main", commit), commit)
        with self.assertRaises(oc.OracleUnavailable):
            mr.resolve_checkpoint("main", None)
        with self.assertRaises(oc.OracleUnavailable):
            mr.resolve_checkpoint(None, None)


def _teacher_recording(texts):
    """A replay recording of routing the reference oracle really computed."""

    reference = mr.ReferenceMoERouter()
    return {
        "run_id": "gap-r1",
        "recorded_at": "2026-08-23T00:00:00Z",
        "teacher": {
            "is_llm_teacher": True,
            "model": "unit-test/not-a-real-moe-checkpoint",
            "revision_or_checkpoint": "1234567890abcdef1234567890abcdef12345678",
            "configuration_sha256": reference.fingerprint()["configuration_sha256"],
            "num_local_experts": reference.num_experts,
            "num_experts_per_tok": reference.top_k,
            "num_layers": reference.num_layers,
        },
        "observations": {
            mr.RecordedTeacherRouter.key_for(text): reference.route(text).as_dict()
            for text in texts
        },
    }


class RecordedRouterGaps(unittest.TestCase):
    """moe_router.py: replayed recordings fail closed, ids stay bounded."""

    def _oracle_with_layer(self, layer: dict) -> mr.RecordedTeacherRouter:
        recording = _teacher_recording(["ctx"])
        key = mr.RecordedTeacherRouter.key_for("ctx")
        recording["observations"][key]["layers"][0].update(layer)
        return mr.RecordedTeacherRouter(recording)

    def test_an_empty_top_k_fails_closed_not_with_index_error(self):
        # `_summarise` used to raise IndexError out of the oracle boundary.
        oracle = self._oracle_with_layer({"top_k_experts": []})
        with self.assertRaises(oc.OracleUnavailable):
            oracle.route("ctx")

    def test_recorded_expert_ids_are_not_coerced(self):
        # int() quietly turned `true` into 1 and 3.7 into 3, letting invalid
        # expert identifiers into the replayed observation.
        for bogus in ([True, 1], [3.7, 1], ["2", 1]):
            with self.subTest(experts=bogus):
                oracle = self._oracle_with_layer({"top_k_experts": bogus})
                with self.assertRaises(oc.OracleUnavailable):
                    oracle.route("ctx")

    def test_recorded_logits_must_be_finite_numbers(self):
        oracle = self._oracle_with_layer({"router_logits": ["1.0", 2.0]})
        with self.assertRaises(oc.OracleUnavailable):
            oracle.route("ctx")

    def test_a_recording_without_an_expert_count_is_unavailable(self):
        recording = _teacher_recording(["ctx"])
        del recording["teacher"]["num_local_experts"]
        available, detail = mr.RecordedTeacherRouter(recording).available()
        self.assertFalse(available)
        self.assertIn("num_local_experts", detail)

    def test_an_authoritative_record_must_declare_its_expert_count(self):
        # Without a declared count the range check was disabled: a recording
        # with no logits could carry ids like [-1, 999] into curation.
        texts = [
            proposal["scenario"]["context"]
            for proposal in mr.propose_contexts(11, 1)
        ]
        oracle = mr.RecordedTeacherRouter(_teacher_recording(texts))
        record = clone(mr.build_records(11, 1, oracle=oracle)[0])
        self.assertEqual(mr.check_family(record, "x"), [])
        del record["oracle"]["fingerprint"]["num_local_experts"]
        rehash(record)
        errors = mr.check_family(record, "x")
        self.assertTrue(
            any("num_local_experts" in error for error in errors),
            f"an authoritative record without an expert count passed: {errors}",
        )

    def test_a_reference_only_record_needs_no_declared_count(self):
        record = clone(mr.build_records(11, 1)[0])
        del record["oracle"]["fingerprint"]["num_local_experts"]
        rehash(record)
        errors = [
            error
            for error in mr.check_family(record, "x")
            if "num_local_experts" in error
        ]
        self.assertEqual(errors, [])


class RouterTrajectoryGaps(unittest.TestCase):
    """moe_router.py: checkpoints, widths and trajectories stay bound."""

    @classmethod
    def setUpClass(cls):
        texts = [
            proposal["scenario"]["context"]
            for proposal in mr.propose_contexts(11, 1)
        ]
        oracle = mr.RecordedTeacherRouter(_teacher_recording(texts))
        cls.teacher_record = mr.build_records(11, 1, oracle=oracle)[0]
        cls.reference_record = mr.build_records(11, 1)[0]

    def test_a_mutable_recording_revision_is_refused_at_the_boundary(self):
        recording = _teacher_recording(["ctx"])
        recording["teacher"]["revision_or_checkpoint"] = "main"
        available, detail = mr.RecordedTeacherRouter(recording).available()
        self.assertFalse(available)
        self.assertIn("mutable revision", detail)

    def test_an_authoritative_record_must_pin_an_immutable_checkpoint(self):
        record = clone(self.teacher_record)
        self.assertEqual(mr.check_family(record, "x"), [])
        record["oracle"]["fingerprint"]["revision_or_checkpoint"] = "main"
        rehash(record)
        errors = mr.check_family(record, "x")
        self.assertTrue(
            any("revision_or_checkpoint" in error for error in errors),
            f"a mutable authoritative checkpoint passed: {errors}",
        )

    def test_the_declared_top_k_width_is_enforced(self):
        record = clone(self.teacher_record)
        layer = record["result"]["routing"]["layers"][0]
        logits = layer["router_logits"]
        top3 = sorted(range(len(logits)), key=lambda e: (-logits[e], e))[:3]
        layer["top_k_experts"] = top3
        rehash(record)
        errors = mr.check_family(record, "x")
        self.assertTrue(
            any("num_experts_per_tok" in error for error in errors),
            f"a wider top-k than the teacher declares passed: {errors}",
        )

    def _drop_layers(self, keep: list[int]) -> dict:
        from collections import Counter

        record = clone(self.reference_record)
        layers = [record["result"]["routing"]["layers"][i] for i in keep]
        record["result"]["routing"]["layers"] = layers
        tops = [layer["top_k_experts"][0] for layer in layers]
        modal, count = Counter(tops).most_common(1)[0]
        record["result"]["top1_expert"] = modal
        record["result"]["routing"]["top1_expert"] = modal
        agreement = round(count / len(tops), 6)
        record["result"]["routing"]["expert_agreement"] = agreement
        last = layers[-1]
        for item in record["result"]["measurements"]:
            if item["quantity"] == "top1_top2_margin":
                item["value"] = last["top1_top2_margin"]
                item["detail"]["layer"] = last["layer"]
            if item["quantity"] == "routing_entropy":
                item["value"] = last["routing_entropy"]
                item["detail"]["layer"] = last["layer"]
            if item["quantity"] == "expert_agreement":
                item["value"] = agreement
                item["detail"]["across_layers"] = len(layers)
        return rehash(record)

    def test_a_gapped_layer_trajectory_is_rejected(self):
        record = self._drop_layers([0, 2])
        errors = mr.check_family(record, "x")
        self.assertTrue(
            any("contiguously" in error for error in errors),
            f"a gapped layer trajectory passed: {errors}",
        )

    def test_a_dropped_suffix_is_rejected_when_the_count_is_declared(self):
        record = self._drop_layers([0, 1])
        errors = mr.check_family(record, "x")
        self.assertTrue(
            any("num_layers" in error for error in errors),
            f"a suffix-dropped trajectory passed: {errors}",
        )

    def test_laundering_cannot_hide_behind_a_renamed_fingerprint_model(self):
        # Renaming fingerprint.model used to be enough: the oracle's own
        # name/type/implementation still said reference_moe_router, but only
        # the fingerprint string was checked.
        record = clone(self.reference_record)
        record["oracle"]["authority"] = oc.AUTHORITY_AUTHORITATIVE
        record["oracle"]["fingerprint"]["model"] = "totally-legit-teacher"
        record["oracle"]["fingerprint"]["is_llm_teacher"] = True
        record["oracle"]["fingerprint"]["revision_or_checkpoint"] = "a" * 40
        record["result"]["is_llm_teacher"] = True
        record["result"]["teacher_grounded"] = True
        rehash(record)
        errors = mr.check_family(record, "x")
        self.assertTrue(
            any("LAUNDERED_REFERENCE_ORACLE" in error for error in errors),
            f"a laundered reference oracle passed: {errors}",
        )


class RouterTieBreakGaps(unittest.TestCase):
    """moe_router.py: serialisation rounding must not reject honest top-k."""

    LOGITS = [2.0, 2.0, 1.0, 0.5, 0.4, 0.3, 0.2, 0.1]

    def _layer(self, experts):
        return {
            "layer": 0,
            "top_k_experts": experts,
            "router_logits": list(self.LOGITS),
            "top1_top2_margin": 0.0,
            "routing_entropy": 1.0,
        }

    def test_either_side_of_a_rounded_tie_is_accepted(self):
        # The stored logits are rounded to six places, so a teacher that
        # ordered by full precision can put the higher id first over values
        # that round together; demanding the id-ordered tie-break rejected
        # honest records.
        for experts in ([0, 1], [1, 0]):
            with self.subTest(experts=experts):
                self.assertEqual(
                    mr._check_layer_logits(self._layer(experts), "x"), []
                )

    def test_a_strictly_smaller_logit_still_cannot_be_top_k(self):
        for experts in ([2, 0], [0, 2], [7, 1]):
            with self.subTest(experts=experts):
                self.assertTrue(
                    mr._check_layer_logits(self._layer(experts), "x")
                )

    def test_out_of_range_ids_still_disagree_with_the_logits(self):
        self.assertTrue(mr._check_layer_logits(self._layer([-1, 0]), "x"))


class CompactInputGaps(unittest.TestCase):
    """moe_router.py: the student input must recompute from the context."""

    def setUp(self):
        self.record = clone(mr.build_records(3, 1)[0])

    def test_tampered_compact_features_are_caught(self):
        # Same width, all finite — only recomputation can catch it, and
        # router_baseline would otherwise train on a corrupted input-label
        # pairing.
        features = self.record["scenario"]["compact_input"]["features"]
        features[0] = float(features[0]) + 0.25
        rehash(self.record)
        errors = mr.check_family(self.record, "x")
        self.assertTrue(
            any("COMPACT_INPUT_NOT_REPRODUCIBLE" in error for error in errors),
            f"tampered compact features passed: {errors}",
        )

    def test_an_unknown_featurizer_cannot_dodge_recomputation(self):
        self.record["scenario"]["compact_input"]["featurizer"] = "custom/9.9.9"
        rehash(self.record)
        errors = mr.check_family(self.record, "x")
        self.assertTrue(
            any("featurizer" in error for error in errors),
            f"an unknown featurizer passed: {errors}",
        )

    def test_missing_dims_cannot_dodge_recomputation(self):
        del self.record["scenario"]["compact_input"]["feature_dim"]
        rehash(self.record)
        errors = mr.check_family(self.record, "x")
        self.assertTrue(
            any("feature_dim" in error for error in errors),
            f"a record without a declared feature_dim passed: {errors}",
        )

    def test_an_absurd_feature_dim_is_a_finding_not_an_allocation(self):
        # Recomputation must not be a memory amplifier: a declared dimension
        # of a few billion gets a finding, never a bucket allocation.
        self.record["scenario"]["compact_input"]["feature_dim"] = 10**12
        rehash(self.record)
        errors = mr.check_family(self.record, "x")
        self.assertTrue(
            any("feature_dim" in error for error in errors),
            f"an absurd feature_dim passed: {errors}",
        )


class BaselineGaps(unittest.TestCase):
    """router_baseline.py"""

    def test_records_without_a_valid_id_are_skipped_not_keyed_as_none(self):
        # str(None) used to give every id-less record the literal id "None",
        # so they all hashed into one train/test bucket.
        records = mr.build_records(11, 4)
        broken = clone(records[0])
        del broken["id"]
        samples = rb.dataset_from_records([broken] + records[1:])
        self.assertEqual(len(samples), len(records) - 1)
        self.assertNotIn("None", {sample.record_id for sample in samples})

    def test_duplicate_record_ids_are_refused(self):
        records = mr.build_records(11, 4)
        with self.assertRaises(rb.BaselineError):
            rb.dataset_from_records(records + [clone(records[0])])

    def test_the_cli_refuses_a_corpus_with_a_tampered_record(self):
        import contextlib
        import io

        records = mr.build_records(11, 30)
        tampered = clone(records[0])
        tampered["result"]["top1_expert"] = (
            int(tampered["result"]["top1_expert"]) + 1
        ) % 8
        rehash(tampered)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "router.jsonl"
            oc.write_jsonl(path, records[1:] + [tampered])
            stderr = io.StringIO()
            with contextlib.redirect_stdout(io.StringIO()):
                with contextlib.redirect_stderr(stderr):
                    exit_code = rb.main(["evaluate", str(path), "--iterations", "5"])
            self.assertEqual(exit_code, 2)
            self.assertIn("not a clean router-family corpus", stderr.getvalue())

    def test_the_cli_refuses_a_non_router_family_record(self):
        import contextlib
        import io

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "mixed.jsonl"
            oc.write_jsonl(path, mr.build_records(11, 10) + fr.build_records(3, 1))
            with contextlib.redirect_stdout(io.StringIO()):
                with contextlib.redirect_stderr(io.StringIO()):
                    exit_code = rb.main(["evaluate", str(path), "--iterations", "5"])
            self.assertEqual(exit_code, 2)

    def test_a_linear_verdict_must_beat_the_best_baseline(self):
        # The MLP can lead the linear model without clearing nonlinear_margin.
        # Reporting the lower logistic accuracy would let an SNN "pass" while
        # losing to a baseline that was already run.
        report = {
            "verdict": rb.VERDICT_LINEAR,
            "baselines": {
                "logistic_regression": {"model": "logistic_regression", "accuracy": 0.80},
                "mlp": {"model": "mlp", "accuracy": 0.84},
            },
            "best": {"model": "mlp", "accuracy": 0.84},
        }
        gate = rb.escalation_gate(report)
        self.assertTrue(gate["escalate_to_snn"])
        self.assertEqual(gate["must_beat"], 0.84)


class FixtureBuilderGaps(unittest.TestCase):
    """scripts/build_distillation_fixture.py"""

    def test_force_can_rebuild_a_committed_fixture_layout(self):
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "_bdf", REPO / "scripts" / "build_distillation_fixture.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "distillation-run"
            # The committed fixture layout: this script's own manifest beside
            # the family folders.
            (out / "moe-router").mkdir(parents=True)
            (out / "MANIFEST.json").write_text(
                json.dumps({"generated_by": module.MANIFEST_PRODUCER}) + "\n",
                encoding="utf-8",
            )
            (out / "moe-router" / "batch-r01.jsonl").write_text("", encoding="utf-8")
            self.assertTrue(module.can_rebuild(out))
            module.assert_rebuildable(out)

    def test_force_still_refuses_a_directory_that_is_not_a_fixture_run(self):
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "_bdf", REPO / "scripts" / "build_distillation_fixture.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "not-a-run"
            (out / "src").mkdir(parents=True)
            (out / "src" / "main.py").write_text("x = 1\n", encoding="utf-8")
            self.assertFalse(module.can_rebuild(out))
            with self.assertRaises(SystemExit):
                module.assert_rebuildable(out)
            self.assertTrue((out / "src" / "main.py").exists())

    def test_force_refuses_a_path_that_is_not_a_directory(self):
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "_bdf", REPO / "scripts" / "build_distillation_fixture.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "a-file"
            out.write_text("not a run\n", encoding="utf-8")
            self.assertFalse(module.can_rebuild(out))
            with self.assertRaises(SystemExit):
                module.assert_rebuildable(out)

    def test_force_refuses_a_directory_with_a_foreign_manifest(self):
        # A dataset or project directory that merely contains an unrelated
        # file named MANIFEST.json used to be declared rebuildable and handed
        # to shutil.rmtree.
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "_bdf", REPO / "scripts" / "build_distillation_fixture.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "precious-dataset"
            out.mkdir()
            (out / "MANIFEST.json").write_text(
                json.dumps({"name": "someone-else's dataset"}), encoding="utf-8"
            )
            (out / "corpus.parquet").write_text("data", encoding="utf-8")
            self.assertFalse(module.can_rebuild(out))
            with self.assertRaises(SystemExit):
                module.assert_rebuildable(out)
            self.assertTrue((out / "corpus.parquet").exists())

    def test_an_unparsable_manifest_is_not_rebuildable(self):
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "_bdf", REPO / "scripts" / "build_distillation_fixture.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "distillation-run"
            (out / "moe-router").mkdir(parents=True)
            (out / "MANIFEST.json").write_text("{ not json", encoding="utf-8")
            self.assertFalse(module.can_rebuild(out))

    def test_a_blocked_validation_aborts_the_rebuild(self):
        # A generator regression used to write MANIFEST.json and exit 0 even
        # though the freshly written run had validation findings.
        import importlib.util
        from unittest import mock

        spec = importlib.util.spec_from_file_location(
            "_bdf", REPO / "scripts" / "build_distillation_fixture.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        blocked_report = {
            "blocked": True,
            "findings": [{"file": "f", "line": 1, "error": "boom"}],
        }
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "run"
            out.mkdir()
            with mock.patch.object(
                module.validate_distill, "validate_path", return_value=blocked_report
            ):
                with self.assertRaises(SystemExit) as caught:
                    module._validation_summary(out)
            self.assertIn("refusing to publish MANIFEST.json", str(caught.exception))


class ThirdRoundEnergyGaps(unittest.TestCase):
    """energy_preferences.py — the third review pass on the hardened checks."""

    @classmethod
    def setUpClass(cls):
        cls.records = ep.build_records(20260823, 1, repeats=1, warmup=0)

    def record(self) -> dict:
        return clone(self.records[0])

    def test_a_non_string_preferred_id_is_a_finding_not_a_typeerror(self):
        # A JSON object or array in preference.preferred is unhashable, so
        # the candidate lookup raised TypeError straight out of the family
        # checker — and validate_path does not catch checker exceptions, so
        # one malformed record aborted validation of the entire run.
        for bad in ({"id": "analytic_kkt"}, ["analytic_kkt"], 7, None, ""):
            record = self.record()
            record["result"]["preference"]["preferred"] = bad
            rehash(record)
            with self.subTest(preferred=bad):
                errors = ep.check_family(record, "x")
                self.assertTrue(
                    any("must name a measured candidate" in e for e in errors),
                    f"a non-string preferred id passed: {errors}",
                )

    def test_the_measured_candidates_must_be_the_proposed_actions(self):
        # Nothing reconciled scenario.candidate_actions with
        # result.candidates, so a record could show the student one action
        # set while its preference was grounded in another.
        record = self.record()
        record["scenario"]["candidate_actions"] = [
            {"id": "fake", "description": "an action the oracle never measured"}
        ]
        rehash(record)
        errors = ep.check_family(record, "x")
        self.assertTrue(
            any("CANDIDATE_SET_MISMATCH" in e for e in errors),
            f"an unrelated proposed action set passed: {errors}",
        )

    def test_a_proposed_description_must_match_the_measured_candidate(self):
        record = self.record()
        record["scenario"]["candidate_actions"][0]["description"] = (
            "a different policy story"
        )
        rehash(record)
        errors = ep.check_family(record, "x")
        self.assertTrue(
            any("was proposed as" in e for e in errors),
            f"a diverging policy description passed: {errors}",
        )

    def test_missing_or_duplicated_candidate_actions_are_findings(self):
        without = self.record()
        del without["scenario"]["candidate_actions"]
        duplicated = self.record()
        duplicated["scenario"]["candidate_actions"].append(
            dict(duplicated["scenario"]["candidate_actions"][0])
        )
        for label, record in (("missing", without), ("duplicated", duplicated)):
            rehash(record)
            with self.subTest(candidate_actions=label):
                errors = ep.check_family(record, "x")
                self.assertTrue(
                    any(
                        "candidate_actions must list each proposed" in e
                        for e in errors
                    ),
                    f"{label} candidate_actions passed: {errors}",
                )

    def test_a_replayed_cost_labels_its_oracle_recorded_measurement(self):
        # RecordedEnergyMeter replays a cost recorded by a metered run
        # elsewhere; only task quality and safety execute locally. Labelling
        # that oracle `measured_execution` claimed a live metered execution
        # this run never performed.
        scenario = ep.propose_scenarios(21, 1)[0]["scenario"]
        observations = {
            ep.workload_key(policy, scenario, fine_steps=12, coarse_steps=4): {
                "cost_value": cost
            }
            for policy, cost in (
                ("analytic_kkt", 8.0),
                ("coarse_grid", 3.0),
                ("exhaustive_grid", 31.0),
                ("unclipped_proportional", 0.2),
            )
        }
        meter = ep.RecordedEnergyMeter(
            {
                "run_id": "metered-run-3",
                "meter": "external_power_meter",
                "cost_quantity": "energy_j",
                "observations": observations,
            }
        )
        records = ep.build_records(21, 1, meter=meter, fine_steps=12, coarse_steps=4)
        self.assertEqual(records[0]["oracle"]["type"], "recorded_measurement")
        self.assertEqual(ep.check_family(records[0], "x"), [])
        self.assertEqual(vd.check_record(records[0], "x"), [])
        # A meter read around the locally executed workload keeps its claim.
        self.assertEqual(self.records[0]["oracle"]["type"], "measured_execution")


class ThirdRoundRouterGaps(unittest.TestCase):
    """moe_router.py and router_baseline.py — the third review pass."""

    @classmethod
    def setUpClass(cls):
        cls.records = mr.build_records(20260823, 8)

    def test_a_boolean_top1_label_cannot_impersonate_expert_0_or_1(self):
        # False == 0 and True == 1, so a JSON boolean passed the modal
        # equality checks while router_baseline._genuine_int rejected it and
        # silently dropped the sample — a cleanly validating record could
        # skew the baseline by vanishing from it.
        record = next(
            clone(r) for r in self.records if r["result"]["top1_expert"] in (0, 1)
        )
        flag = bool(record["result"]["top1_expert"])
        record["result"]["top1_expert"] = flag
        record["result"]["routing"]["top1_expert"] = flag
        rehash(record)
        errors = mr.check_family(record, "x")
        self.assertEqual(
            sum("genuine integer expert id" in e for e in errors), 2, errors
        )
        self.assertIsNone(rb._target_label(record["result"], rb.TARGET_TOP1))

    def test_promised_router_measurements_cannot_be_dropped(self):
        # The reconciliation loop only validated the readings present, so a
        # record could delete promised compact targets and stay
        # curation-eligible after a rehash.
        for missing in ("routing_entropy", "expert_agreement", "top1_top2_margin"):
            record = clone(self.records[0])
            record["result"]["measurements"] = [
                item
                for item in record["result"]["measurements"]
                if item.get("quantity") != missing
            ]
            rehash(record)
            with self.subTest(missing=missing):
                errors = mr.check_family(record, "x")
                self.assertTrue(
                    any(f"must record {missing}" in e for e in errors),
                    f"dropping {missing} passed: {errors}",
                )

    def test_the_baseline_refuses_an_abstained_router_result(self):
        record = clone(self.records[1])
        record["result"]["status"] = "abstained"
        record["result"]["abstention_reason"] = "teacher unavailable for this batch"
        rehash(record)
        # The record is valid — an oracle may honestly abstain —
        self.assertEqual(vd.check_record(record, "x"), [])
        # — but its routing fields must never become labels ...
        self.assertEqual(rb.dataset_from_records([record]), [])
        # ... and the CLI gate refuses loudly instead of filtering silently.
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "records.jsonl"
            path.write_text(oc.canonical_json(record) + "\n", encoding="utf-8")
            with self.assertRaises(rb.BaselineError) as caught:
                rb._clean_router_records(str(path))
        self.assertIn(
            "only evaluates measured router results", str(caught.exception)
        )

    def test_min_lift_must_be_finite_and_non_negative(self):
        # argparse accepts `--min-lift nan`; NaN survived the max() floor and
        # made every lift comparison false, so a large holdout could emit a
        # learnable verdict no finite threshold would grant.
        for bad in (float("nan"), float("inf"), -0.05):
            with self.subTest(min_lift=bad):
                with self.assertRaises(rb.BaselineError) as caught:
                    rb.evaluate_baselines([], min_lift=bad)
                self.assertIn("min_lift", str(caught.exception))


class FourthRoundContractGaps(unittest.TestCase):
    """oracle_contract.py — the fourth review pass."""

    def test_oracle_summaries_cannot_hide_in_generator_namespaces(self):
        # `top1_expert` was missing from the oracle-only denylist, so the
        # teacher label could be copied into the student-visible scenario.
        record = clone(mr.build_records(20260823, 1)[0])
        record["scenario"]["top1_expert"] = record["result"]["top1_expert"]
        rehash(record)
        errors = vd.check_record(record, "x")
        self.assertTrue(
            any(
                "ORACLE_FIELD_IN_GENERATOR_NAMESPACE" in e and "top1_expert" in e
                for e in errors
            ),
            f"a leaked teacher label passed: {errors}",
        )

    def test_measurement_values_respect_their_quantity_domains(self):
        # Any finite number used to pass: wall_time_s could go to -5 and
        # task_quality to 1.5 with only the digest to recompute.
        for quantity, value, fragment in (
            ("wall_time_s", -5.0, "cannot be negative"),
            ("task_quality", 1.5, "must lie in [0, 1]"),
        ):
            record = clone(ep.build_records(20260823, 1, repeats=1, warmup=0)[0])
            tampered = False
            for item in record["result"]["measurements"]:
                if item["quantity"] == quantity:
                    item["value"] = value
                    tampered = True
                    break
            self.assertTrue(tampered, f"no {quantity} measurement to tamper")
            rehash(record)
            with self.subTest(quantity=quantity):
                errors = vd.check_record(record, "x")
                self.assertTrue(
                    any(fragment in e for e in errors),
                    f"{quantity} = {value} passed: {errors}",
                )


class FourthRoundRouterGaps(unittest.TestCase):
    """moe_router.py — the fourth review pass."""

    @classmethod
    def setUpClass(cls):
        texts = [p["scenario"]["context"] for p in mr.propose_contexts(11, 2)]
        cls.recording = _teacher_recording(texts)
        oracle = mr.RecordedTeacherRouter(cls.recording)
        cls.teacher_records = mr.build_records(11, 2, oracle=oracle)

    def test_an_authoritative_router_must_declare_top_k_and_layers(self):
        # Both equality checks were conditional on the declaration being
        # present, so deleting the field freed the recorded trajectory from
        # the teacher configuration while staying curation-eligible.
        for field in ("num_experts_per_tok", "num_layers"):
            record = clone(self.teacher_records[0])
            del record["oracle"]["fingerprint"][field]
            rehash(record)
            with self.subTest(field=field):
                errors = mr.check_family(record, "x")
                self.assertTrue(
                    any(
                        f"{field} must declare a positive value" in e
                        for e in errors
                    ),
                    f"an authoritative record without {field} passed: {errors}",
                )

    def test_a_reference_only_record_needs_no_declared_widths(self):
        record = clone(mr.build_records(11, 1)[0])
        del record["oracle"]["fingerprint"]["num_experts_per_tok"]
        del record["oracle"]["fingerprint"]["num_layers"]
        rehash(record)
        errors = [
            e
            for e in mr.check_family(record, "x")
            if "must declare a positive value" in e
        ]
        self.assertEqual(errors, [])

    def test_a_recording_without_declared_widths_is_refused(self):
        for field in ("num_experts_per_tok", "num_layers"):
            recording = clone(self.recording)
            del recording["teacher"][field]
            with self.subTest(field=field):
                ok, detail = mr.RecordedTeacherRouter(recording).available()
                self.assertFalse(ok)
                self.assertIn(field, detail)

    def test_truncated_router_logits_are_rejected(self):
        # A shortened array still containing the selected ids passed the
        # ordering check while changing the entropy and logit targets.
        record, index = next(
            (clone(candidate), i)
            for candidate in self.teacher_records
            # Not the last layer: its summaries feed result.measurements.
            for i, lay in enumerate(candidate["result"]["routing"]["layers"][:-1])
            if max(lay["top_k_experts"]) + 1 < len(lay["router_logits"])
        )
        layer = record["result"]["routing"]["layers"][index]
        keep = max(layer["top_k_experts"]) + 1
        layer["router_logits"] = layer["router_logits"][:keep]
        values = [float(v) for v in layer["router_logits"]]
        ordered = sorted(values, reverse=True)
        layer["top1_top2_margin"] = round(ordered[0] - ordered[1], 6)
        layer["routing_entropy"] = round(
            mr.entropy_nats(mr.softmax(values)), 6
        )
        rehash(record)
        errors = mr.check_family(record, "x")
        self.assertTrue(
            any("router_logits lists" in e for e in errors),
            f"a truncated logit distribution passed: {errors}",
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
                with self.assertRaises(oc.ContractError):
                    simulator.run(scenario, disturbance(onset))
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


class FourthRoundEnergyGaps(unittest.TestCase):
    """energy_preferences.py — the fourth review pass."""

    def test_candidate_success_is_re_derived(self):
        # success = safety_ok and task_quality >= quality_floor is how the
        # builder writes it; nothing re-derived it, so the unsafe candidate
        # could claim success after a rehash.
        record = clone(ep.build_records(20260823, 1, repeats=1, warmup=0)[0])
        unsafe = next(
            c
            for c in record["result"]["candidates"]
            if c["id"] == "unclipped_proportional"
        )
        unsafe["success"] = True
        rehash(record)
        errors = ep.check_family(record, "x")
        self.assertTrue(
            any(".success is True" in e for e in errors),
            f"a flipped success summary passed: {errors}",
        )

    def test_candidate_success_must_be_a_boolean(self):
        record = clone(ep.build_records(20260823, 1, repeats=1, warmup=0)[0])
        next(
            c for c in record["result"]["candidates"] if c["id"] == "analytic_kkt"
        )["success"] = 1
        rehash(record)
        errors = ep.check_family(record, "x")
        self.assertTrue(
            any(".success must be a boolean" in e for e in errors),
            f"an integer success passed: {errors}",
        )


class FourthRoundBaselineGaps(unittest.TestCase):
    """router_baseline.py — the fourth review pass."""

    def test_iteration_counts_must_be_positive_integers(self):
        # `--iterations 0` trained neither advertised baseline yet still
        # published their initial predictions into the escalation gate.
        for kwargs in (
            {"logistic_iterations": 0},
            {"mlp_iterations": -3},
            {"logistic_iterations": True},
        ):
            with self.subTest(**kwargs):
                with self.assertRaises(rb.BaselineError) as caught:
                    rb.evaluate_baselines([], **kwargs)
                self.assertIn("positive integer", str(caught.exception))


class FifthRoundEnergyGaps(unittest.TestCase):
    """energy_preferences.py and the shared meter allowlist — fifth pass."""

    @classmethod
    def setUpClass(cls):
        cls.records = ep.build_records(20260823, 1, repeats=1, warmup=0)

    def record(self) -> dict:
        return clone(self.records[0])

    def test_a_malformed_allocation_is_corruption_not_a_derived_failure(self):
        # ["bad"] used to convert into ALLOCATION_NOT_NUMERIC, so restating
        # the derived failure values shipped a fabricated policy failure.
        record = self.record()
        candidate = next(
            c for c in record["result"]["candidates"] if c["id"] == "coarse_grid"
        )
        candidate["allocation"] = ["bad"]
        candidate["safety_ok"] = False
        candidate["safety_violations"] = ["ALLOCATION_NOT_NUMERIC"]
        candidate["task_quality"] = 0.0
        for item in record["result"]["measurements"]:
            detail = item.get("detail", {})
            if (
                detail.get("candidate") == "coarse_grid"
                and item["quantity"] == "task_quality"
            ):
                item["value"] = 0.0
        rehash(record)
        errors = ep.check_family(record, "x")
        self.assertTrue(
            any(
                "must be null, empty, or a finite numeric vector" in e
                for e in errors
            ),
            f"a fabricated policy failure passed: {errors}",
        )

    def test_the_reference_objective_must_be_restated(self):
        # Deleting it (or writing a string) skipped the comparison even
        # though the scenario derives the optimum.
        for mutate in ("delete", "string"):
            record = self.record()
            if mutate == "delete":
                del record["result"]["reference_objective"]
            else:
                record["result"]["reference_objective"] = "high"
            rehash(record)
            with self.subTest(mutate=mutate):
                errors = ep.check_family(record, "x")
                self.assertTrue(
                    any("must restate the scenario optimum" in e for e in errors),
                    f"a lost reference objective passed: {errors}",
                )

    def test_the_replay_wrapper_is_not_a_physical_energy_meter(self):
        # `recorded_power_run` is the replay wrapper; renaming every joule
        # reading's meter to it used to stay validation-clean while hiding
        # the physical instrument.
        scenario = ep.propose_scenarios(21, 1)[0]["scenario"]
        observations = {
            ep.workload_key(policy, scenario, fine_steps=12, coarse_steps=4): {
                "cost_value": cost
            }
            for policy, cost in (
                ("analytic_kkt", 8.0),
                ("coarse_grid", 3.0),
                ("exhaustive_grid", 31.0),
                ("unclipped_proportional", 0.2),
            )
        }
        meter = ep.RecordedEnergyMeter(
            {
                "run_id": "metered-run-5",
                "meter": "external_power_meter",
                "cost_quantity": "energy_j",
                "observations": observations,
            }
        )
        record = ep.build_records(21, 1, meter=meter, fine_steps=12, coarse_steps=4)[0]
        self.assertEqual(ep.check_family(record, "x") + vd.check_record(record, "x"), [])
        tampered = clone(record)
        for item in tampered["result"]["measurements"]:
            if item["quantity"] == "energy_j":
                item["meter"] = "recorded_power_run"
        for candidate in tampered["result"]["candidates"]:
            candidate["cost_meter"] = "recorded_power_run"
        rehash(tampered)
        errors = ep.check_family(tampered, "x") + vd.check_record(tampered, "x")
        self.assertTrue(
            any("recorded_power_run" in e for e in errors),
            f"the replay wrapper passed as a physical meter: {errors}",
        )


class FifthRoundFaultGaps(unittest.TestCase):
    """fault_recovery.py — fifth pass."""

    @classmethod
    def setUpClass(cls):
        cls.records = fr.build_records(11, 12)

    def test_invalid_system_controls_are_refused(self):
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
                with self.assertRaises(oc.ContractError) as caught:
                    fr.RelayReflexSimulator().run(
                        record["scenario"], record["intervention"]
                    )
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


class FifthRoundRouterGaps(unittest.TestCase):
    """moe_router.py — fifth pass."""

    @classmethod
    def setUpClass(cls):
        cls.records = mr.build_records(20260823, 2)

    def test_a_promised_target_marked_unmeasured_is_not_reconciled(self):
        # `measured: false` on a promised compact target still counted as
        # reconciled, publishing a modelled value as a grounded router
        # measurement.
        record = clone(self.records[0])
        for item in record["result"]["measurements"]:
            if item["quantity"] == "routing_entropy":
                item["measured"] = False
        rehash(record)
        errors = mr.check_family(record, "x")
        self.assertTrue(
            any(
                "must record routing_entropy as a measured numeric reading" in e
                for e in errors
            ),
            f"an unmeasured promised target passed: {errors}",
        )

    def test_an_unhashable_quantity_is_a_finding_not_a_typeerror(self):
        record = clone(self.records[1])
        record["result"]["measurements"][0]["quantity"] = ["routing_entropy"]
        rehash(record)
        errors = mr.check_family(record, "x")  # must not raise
        self.assertTrue(errors, "a malformed quantity produced no finding")
        self.assertTrue(
            any("unknown quantity" in e for e in vd.check_record(record, "x")),
            "the shared checker no longer flags the malformed item",
        )

    def test_recorded_layer_indices_are_not_coerced(self):
        # int() silently rewrote 0.9 to 0 and True to 1, normalising
        # malformed recording metadata into a validation-clean trajectory.
        for bogus in (0.9, True, "0"):
            recording = _teacher_recording(["ctx"])
            key = mr.RecordedTeacherRouter.key_for("ctx")
            recording["observations"][key]["layers"][0]["layer"] = bogus
            with self.subTest(layer=bogus):
                with self.assertRaises(oc.OracleUnavailable) as caught:
                    mr.RecordedTeacherRouter(recording).route("ctx")
                self.assertIn("genuine integer", str(caught.exception))


class SixthRoundContractGaps(unittest.TestCase):
    """oracle_contract.py and validate_distill.py — sixth pass."""

    def test_overflowing_float_literals_are_parse_failures(self):
        # json.loads turns 1e999 into inf; the first canonical
        # re-serialisation (allow_nan=False) then raised out of validation
        # instead of reporting the offending line.
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "rows.jsonl"
            path.write_text('{"value": 1e999}\n{"ok": 1.5}\n', encoding="utf-8")
            rows = oc.read_jsonl(str(path))
        self.assertIsNone(rows[0][1])
        self.assertEqual(rows[1][1], {"ok": 1.5})

    def test_a_lifted_validation_stamp_is_a_finding(self):
        # check_record verified the content digest but never the stamp
        # binding, so a verdict lifted from another record — any well-formed
        # 64-hex digest — stayed structurally valid.
        record = clone(fr.build_records(11, 1)[0])
        stamped = oc.stamp_validation(
            record, validator="validate_distill", version="1.0.0", findings=[]
        )
        self.assertEqual(vd.check_record(stamped, "x"), [])
        lifted = clone(stamped)
        lifted["validation"]["validator"]["validated_digest"] = "0" * 64
        errors = vd.check_record(lifted, "x")
        self.assertTrue(
            any("formed over the exact record" in e for e in errors),
            f"a lifted stamp passed: {errors}",
        )


class SixthRoundEnergyGaps(unittest.TestCase):
    """energy_preferences.py — sixth pass."""

    def test_rapl_counts_every_wrap_across_repeats(self):
        # Endpoint sampling around the whole batch could only ever add one
        # counter range: three repeats consuming 0.6R each net +0.8R at the
        # endpoints (delta >= 0, no unwrap), reporting 8 J for an 18 J run.
        # Per-repeat sampling observes the wrap in the middle interval.
        range_uj = 10_000_000
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            domain = root / "intel-rapl:0"
            domain.mkdir()
            (domain / "energy_uj").write_text("0\n")
            (domain / "max_energy_range_uj").write_text(f"{range_uj}\n")
            meter = ep.RaplEnergyMeter(root=root)
            state = {"uj": 0}

            def workload():
                state["uj"] = (state["uj"] + 6_000_000) % range_uj
                (domain / "energy_uj").write_text(f"{state['uj']}\n")

            reading = meter.measure(workload, repeats=3, warmup=0)
        # 3 x 6 J measured; the mean per repeat is 6 J, not (8/3) J.
        self.assertAlmostEqual(reading.cost_value, 6.0, places=6)

    def test_an_abstention_needs_an_empty_feasible_set(self):
        # Relabelling a measured record `abstained` while its own
        # measurements still contained feasible candidates validated cleanly
        # as a false oracle abstention.
        record = clone(ep.build_records(20260823, 1, repeats=1, warmup=0)[0])
        record["result"]["status"] = "abstained"
        record["result"]["abstention_reason"] = ep.ABSTAIN_NO_FEASIBLE
        del record["result"]["preference"]
        rehash(record)
        errors = ep.check_family(record, "x")
        self.assertTrue(
            any("FALSE_ABSTENTION" in e for e in errors),
            f"a false abstention passed: {errors}",
        )

    def test_an_abstention_reason_must_be_canonical(self):
        record = clone(ep.build_records(20260823, 1, repeats=1, warmup=0)[0])
        record["result"]["status"] = "abstained"
        record["result"]["abstention_reason"] = "meter broke mid-run"
        del record["result"]["preference"]
        rehash(record)
        errors = ep.check_family(record, "x")
        self.assertTrue(
            any("canonical" in e for e in errors),
            f"a non-canonical abstention reason passed: {errors}",
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
                with self.assertRaises(oc.ContractError):
                    fr.RelayReflexSimulator().run(
                        record["scenario"], record["intervention"]
                    )
                errors = fr.check_family(record, "x")
                self.assertTrue(
                    any(fragment in e for e in errors),
                    f"an oversized {key} passed validation: {errors}",
                )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
