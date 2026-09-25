#!/usr/bin/env python3
"""Energy meter / oracle gap tests (tamper-and-recheck regressions).

Split out of ``test_distill_energy_gaps.py``: RAPL zone accounting, replayed
meter bindings, measured-reading provenance, and oracle identity checks.
"""

import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "pipelines"))



import energy_preferences as ep  # noqa: E402
from oracle_grounded import distill_contract as oc  # noqa: E402
from distill_gap_test_support import (  # noqa: E402
    clone,
    measurements_for,
    rehash,
    set_cost_measurement,
)

class EnergyMeterAndDerivationGaps(unittest.TestCase):
    """energy_preferences.py: RAPL zones, replay binding, measured readings."""

    @classmethod
    def setUpClass(cls):
        cls.records = ep.build_records(20260823, 1, ep.MeterSpec(repeats=1, warmup=0))

    def record(self) -> dict:
        return clone(self.records[0])

    @staticmethod
    def _rapl_tree(root: Path, zones: dict[str, tuple[str, int]]) -> None:
        for zone, (label, microjoules) in zones.items():
            domain = root / zone
            domain.mkdir()
            (domain / "energy_uj").write_text(f"{microjoules}\n")
            (domain / "name").write_text(f"{label}\n")

    def _rapl_cost_joules(
        self,
        zones: dict[str, tuple[str, int]],
        writes: dict[str, int],
    ) -> float:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._rapl_tree(root, zones)
            meter = ep.RaplEnergyMeter(root=root)

            def workload():
                for zone, microjoules in writes.items():
                    (root / zone / "energy_uj").write_text(f"{microjoules}\n")

            return meter.measure(workload, repeats=1, warmup=0).cost_value

    def test_rapl_subzones_are_not_double_counted(self):
        # The package counter already includes its core/uncore children, so
        # summing every flat entry counted selected components twice and
        # could reorder the preference between workloads with different
        # component mixes.
        cost = self._rapl_cost_joules(
            {
                "intel-rapl:0": ("package-0", 1_000_000),
                "intel-rapl:0:0": ("core", 500_000),
            },
            {"intel-rapl:0": 3_000_000, "intel-rapl:0:0": 1_500_000},
        )
        self.assertAlmostEqual(cost, 2.0, places=6)

    def test_psys_beside_package_zones_is_not_added_on_top(self):
        cost = self._rapl_cost_joules(
            {
                "intel-rapl:0": ("package-0", 1_000_000),
                "intel-rapl:1": ("psys", 2_000_000),
            },
            {"intel-rapl:0": 3_000_000, "intel-rapl:1": 9_000_000},
        )
        self.assertAlmostEqual(cost, 2.0, places=6)

    def test_a_lone_psys_zone_is_still_a_measurement(self):
        cost = self._rapl_cost_joules(
            {"intel-rapl:0": ("psys", 1_000_000)},
            {"intel-rapl:0": 4_000_000},
        )
        self.assertAlmostEqual(cost, 3.0, places=6)

    def test_a_replayed_cost_is_bound_to_the_solver_configuration(self):
        # A recording taken at one grid resolution used to replay cleanly
        # against another: the grid policy ran a different search while the
        # old energy reading was attached to it.
        scenario = ep.propose_scenarios(21, 1)[0]["scenario"]
        observations = {
            ep.workload_key(policy, scenario, ep.MeterProtocol(fine_steps=12, coarse_steps=4)): {
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
            21, 1, ep.MeterSpec(meter=meter, fine_steps=12, coarse_steps=4)
        )
        self.assertEqual(ep.check_family(records[0], "x"), [])
        default_spec = ep.MeterSpec(meter=meter)
        with self.assertRaises(oc.OracleUnavailable):
            ep.build_records(21, 1, default_spec)

    def _preferred(self, record: dict) -> dict:
        preferred_id = record["result"]["preference"]["preferred"]
        return next(
            c for c in record["result"]["candidates"] if c["id"] == preferred_id
        )

    def _readings_for(self, record: dict, candidate_id: str, quantity: str):
        yield from measurements_for(record, candidate_id, quantity)

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
        record = clone(ep.build_records(20260823, 1, ep.MeterSpec(repeats=1, warmup=0))[0])
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
        record = clone(ep.build_records(20260823, 1, ep.MeterSpec(repeats=1, warmup=0))[0])
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
                20260823,
                1,
                ep.MeterSpec(meter=meter, meter_probe=probe, repeats=1, warmup=0),
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
                spec = ep.MeterSpec(**knobs)
                with self.assertRaises(oc.ContractError):
                    ep.build_records(20260823, 1, spec)

    def _restated_candidate(self, candidate: dict, evaluation) -> None:
        """Re-derive a candidate's quality/safety fields from an evaluation."""

        candidate["task_quality"] = evaluation.task_quality
        candidate["safety_ok"] = evaluation.safety_ok
        candidate["safety_violations"] = list(evaluation.violations)
        candidate["success"] = evaluation.success

    def _restated_feasible(self, record: dict) -> None:
        """Re-derive the preference's feasible list after a candidate swap."""

        preference = record["result"].get("preference")
        if preference is None:
            return
        floor = record["scenario"]["constraints"]["quality_floor"]
        feasible = ep._feasible_candidates(record["result"]["candidates"], floor)
        preference["feasible"] = sorted(c["id"] for c in feasible)

    def _swap_for_evaluation(self, record: dict):
        """Put analytic_kkt's allocation on coarse_grid, scored as stated."""

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
        return ep.evaluate_allocation(
            list(coarse["allocation"]),
            ep.ProblemSpec(
                demand=demand, weights=weights, caps=caps,
                optimum=optimum, quality_floor=floor,
            ),
        )

    def test_a_swapped_policy_allocation_is_not_reproducible(self):
        # Replacing coarse_grid's allocation with analytic_kkt's — deriving
        # quality, safety and membership consistently and rehashing — passed
        # validation while the retained cost was still attributed to the
        # coarse-grid workload.
        record = self._record()
        evaluation = self._swap_for_evaluation(record)
        coarse = next(
            c for c in record["result"]["candidates"] if c["id"] == "coarse_grid"
        )
        self._restated_candidate(coarse, evaluation)
        set_cost_measurement(
            record, "coarse_grid", "task_quality", evaluation.task_quality
        )
        self._restated_feasible(record)
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
        for knob, overshoot in (("fine_steps", 1), ("coarse_steps", 1)):
            spec = ep.MeterSpec(**{knob: ep.MAX_REPLAY_STEPS + overshoot})
            with self.subTest(knob=knob), self.assertRaises(oc.ContractError):
                ep.build_records(3, 1, spec)

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
