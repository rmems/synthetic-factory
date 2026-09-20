#!/usr/bin/env python3
"""Energy-preference family gap tests (tamper-and-recheck regressions).

Split out of ``test_distillation_review_gaps.py``: every test fails against
the code as it stood before the fix it names. The recurring shape is: take a
record the generator produced, tamper with one derived field, recompute
``provenance.record_sha256`` so the digest check is satisfied, and assert the
family checker still objects.
"""

import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "pipelines"))



import energy_preferences as ep
import validate_distill as vd
from oracle_grounded import distill_contract as oc  # noqa: E402
from distill_gap_test_support import clone, rehash  # noqa: E402

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

    def test_a_negative_recorded_cost_is_refused_case(self):
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

    def test_candidate_success_must_be_a_boolean_case(self):
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




class NinthRoundEnergyGaps(unittest.TestCase):
    """Energy-preference findings of the ninth review pass."""

    def _record(self):
        meter, probe = ep.select_meter(prefer_energy=False)
        return clone(
            ep.build_records(
                20260823, 1, meter=meter, meter_probe=probe, repeats=1, warmup=0
            )[0]
        )

    def test_the_rederived_safety_violation_list_is_required(self):
        # Deleting safety_violations from the unsafe candidate skipped the
        # comparison: pairwise consumers saw a constraint-rejected candidate
        # with no recorded reason.
        record = self._record()
        unsafe = [
            candidate
            for candidate in record["result"]["candidates"]
            if candidate["id"] == "unclipped_proportional"
        ][0]
        self.assertFalse(unsafe["safety_ok"])
        del unsafe["safety_violations"]
        rehash(record)
        errors = ep.check_family(record, "x")
        self.assertTrue(
            any("safety_violations must list" in e for e in errors), errors
        )

    def test_measurement_run_knobs_are_validated_case(self):
        # warmup=-5 was silently normalised to zero by the live meters while
        # the oracle configuration still recorded -5; fractional or zero
        # settings failed later inside range() or the grid division.
        for knobs in (
            {"repeats": 0},
            {"repeats": 1.5},
            {"warmup": -5},
            {"warmup": True},
            {"fine_steps": 0},
            {"coarse_steps": -1},
        ):
            with self.subTest(knobs=knobs):
                with self.assertRaises(oc.ContractError):
                    ep.build_records(20260823, 1, **knobs)

    def test_a_swapped_policy_allocation_is_not_reproducible(self):
        # Replacing coarse_grid's allocation with analytic_kkt's — deriving
        # quality, safety and membership consistently and rehashing — passed
        # validation while the retained cost was still attributed to the
        # coarse-grid workload.
        record = self._record()
        by_id = {c["id"]: c for c in record["result"]["candidates"]}
        coarse, kkt = by_id["coarse_grid"], by_id["analytic_kkt"]
        state = record["scenario"]["state"]
        weights = [float(w) for w in state["actuator_weights"]]
        caps = [float(c) for c in state["actuator_caps"]]
        demand = float(state["demand"])
        floor = record["scenario"]["constraints"]["quality_floor"]
        optimum = ep.objective(
            weights, ep.analytic_allocation(demand, weights, caps)
        )
        coarse["allocation"] = list(kkt["allocation"])
        evaluation = ep.evaluate_allocation(
            list(coarse["allocation"]),
            demand=demand,
            weights=weights,
            caps=caps,
            optimum=optimum,
            quality_floor=floor,
        )
        coarse["task_quality"] = evaluation.task_quality
        coarse["safety_ok"] = evaluation.safety_ok
        coarse["safety_violations"] = list(evaluation.violations)
        coarse["success"] = evaluation.success
        for item in record["result"]["measurements"]:
            detail = item.get("detail") or {}
            if (
                detail.get("candidate") == "coarse_grid"
                and item["quantity"] == "task_quality"
            ):
                item["value"] = evaluation.task_quality
        preference = record["result"].get("preference")
        if preference is not None:
            feasible = ep._feasible_candidates(record["result"]["candidates"], floor)
            preference["feasible"] = sorted(c["id"] for c in feasible)
        rehash(record)
        errors = ep.check_family(record, "x")
        self.assertTrue(
            any("ALLOCATION_NOT_REPRODUCIBLE" in e for e in errors), errors
        )

    def test_a_foreign_candidate_id_cannot_dodge_the_recompute(self):
        record = self._record()
        by_id = {c["id"]: c for c in record["result"]["candidates"]}
        by_id["coarse_grid"]["id"] = "mystery_policy"
        rehash(record)
        errors = ep.check_family(record, "x")
        self.assertTrue(any("UNKNOWN_POLICY_ID" in e for e in errors), errors)

    def test_foreign_implementation_cannot_skip_allocation_replay(self):
        record = self._record()
        record["oracle"]["implementation"] = "pipelines/foreign_energy.py:OtherOracle"
        rehash(record)
        errors = ep.check_family(record, "x")
        self.assertTrue(
            any("ORACLE_IMPLEMENTATION_NOT_REPLAYABLE" in e for e in errors),
            errors,
        )

    def test_solver_settings_outside_the_replay_domain_are_findings(self):
        record = self._record()
        record["oracle"]["configuration"]["fine_steps"] = 10**9
        rehash(record)
        errors = ep.check_family(record, "x")
        self.assertTrue(
            any(
                "fine_steps must be an integer >= 1 and <= 128" in e
                for e in errors
            ),
            errors,
        )

    def test_max_rss_is_a_per_workload_peak_not_a_high_water_delta(self):
        # ru_maxrss is the process-lifetime high-water mark: subtracting two
        # snapshots reported every equal-or-smaller footprint as
        # max_rss_kb: 0 — all four committed fixture candidates carried the
        # false zero.
        meter = ep.ProcessResourceMeter()
        if not ep._reset_peak_rss():
            reading = meter.measure(lambda: None, repeats=1, warmup=0)
            self.assertNotIn(
                "max_rss_kb",
                [item["quantity"] for item in reading.extra],
                "an unmeasurable peak must be unmeasured, not zero",
            )
            self.skipTest("no resettable peak-RSS counter on this platform")

        def hungry():
            buffer = bytearray(64 * 1024 * 1024)
            buffer[::4096] = b"x" * len(buffer[::4096])
            return len(buffer)

        hungry_reading = meter.measure(hungry, repeats=1, warmup=0)
        lean_reading = meter.measure(lambda: None, repeats=1, warmup=0)
        by_quantity = {
            item["quantity"]: item["value"] for item in hungry_reading.extra
        }
        lean_by_quantity = {
            item["quantity"]: item["value"] for item in lean_reading.extra
        }
        self.assertGreaterEqual(
            by_quantity["max_rss_kb"],
            64 * 1024,
            "the workload's own 64 MiB peak must be visible",
        )
        self.assertGreater(
            by_quantity["max_rss_kb"],
            lean_by_quantity["max_rss_kb"],
            "a later lean workload must not inherit the hungry peak — the "
            "counter is reset per workload, not process-lifetime",
        )




class EnergyOracleContractGaps(unittest.TestCase):
    """energy_preferences.py: oracle identity and probe must agree."""

    @classmethod
    def setUpClass(cls):
        cls.records = ep.build_records(3, 2)

    def test_run_knobs_beyond_the_replayable_grid_are_refused(self):
        # The validator replays the grid; a knob beyond MAX_REPLAY_STEPS
        # produces a record the validator cannot check.
        with self.assertRaises(oc.ContractError):
            ep.build_records(
                3, 1, fine_steps=ep.MAX_REPLAY_STEPS + 1
            )
        with self.assertRaises(oc.ContractError):
            ep.build_records(
                3, 1, coarse_steps=ep.MAX_REPLAY_STEPS + 1
            )

    def test_an_oracle_type_that_disagrees_with_its_implementation_is_a_finding(
        self,
    ):
        record = clone(self.records[0])
        record["oracle"]["type"] = "recorded_measurement"
        rehash(record)
        errors = ep.check_family(record, "x")
        self.assertTrue(
            any("ORACLE_TYPE_MISMATCH" in error for error in errors),
            f"a mismatched oracle type/implementation pair passed: {errors}",
        )

    def test_a_negative_demand_is_a_finding(self):
        record = clone(self.records[0])
        record["scenario"]["state"]["demand"] = -1.0
        rehash(record)
        errors = ep.check_family(record, "x")
        self.assertTrue(
            any("demand" in error for error in errors),
            f"a negative demand passed: {errors}",
        )

    def test_a_selected_meter_that_was_never_available_is_a_finding(self):
        # The probe may select only a meter it actually probed as available.
        record = clone(self.records[0])
        record["oracle"]["configuration"]["meter_probe"]["selected"] = (
            "intel_rapl_powercap"
        )
        rehash(record)
        errors = ep.check_family(record, "x")
        self.assertTrue(
            any("selected" in error for error in errors),
            f"an unavailable selected meter passed: {errors}",
        )




