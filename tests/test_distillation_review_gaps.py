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
            "revision_or_checkpoint": "rev-abc123",
            "configuration_sha256": reference.fingerprint()["configuration_sha256"],
            "num_local_experts": reference.num_experts,
            "num_experts_per_tok": reference.top_k,
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


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
