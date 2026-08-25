#!/usr/bin/env python3
"""Tests for measured-execution energy preferences.

The determinism-sensitive assertions run against a deterministic fake meter so
they do not depend on this machine's timing. A separate test exercises the real
``ProcessResourceMeter`` end to end, asserting only what a measurement can
honestly promise.
"""

import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "pipelines"))

import energy_preferences as ep  # noqa: E402
import oracle_contract as oc  # noqa: E402


class FakeMeter(ep.EnergyOracle):
    """Deterministic stand-in that still requires the workload to execute."""

    name = "process_resource_meter"
    version = "test"
    cost_quantity = "cpu_time_s"
    measures_energy = False

    def __init__(self, costs=None):
        self.costs = costs or {}
        self.calls = 0

    def available(self):
        return True, "fake"

    def measure(self, workload, *, repeats, warmup):
        self.calls += 1
        allocation = workload()
        cost = self.costs.get(self.calls, 0.001 * self.calls)
        return ep.MeterReading(
            meter=self.name,
            cost_quantity=self.cost_quantity,
            cost_value=cost,
            extra=(oc.new_measurement("repeats", float(repeats), self.name),),
            detail={"allocation_len": len(allocation)},
        )


class FakeEnergyMeter(FakeMeter):
    """A fake that claims to measure joules, for the energy-denominated path."""

    name = "intel_rapl_powercap"
    cost_quantity = "energy_j"
    measures_energy = True


class AllocationTask(unittest.TestCase):
    def test_analytic_solution_respects_caps_and_meets_demand(self):
        weights = [1.0, 2.0, 0.5, 1.5]
        caps = [0.3, 0.5, 0.2, 0.5]
        allocation = ep.analytic_allocation(1.0, weights, caps)
        self.assertAlmostEqual(sum(allocation), 1.0, places=9)
        for value, cap in zip(allocation, caps):
            self.assertLessEqual(value, cap + 1e-9)

    def test_analytic_beats_a_coarse_grid_on_the_objective(self):
        weights = [1.0, 2.0, 0.5, 1.5]
        caps = [0.6, 0.6, 0.6, 0.6]
        exact = ep.objective(weights, ep.analytic_allocation(1.0, weights, caps))
        coarse = ep.objective(weights, ep.grid_allocation(1.0, weights, caps, 4))
        self.assertLess(exact, coarse + 1e-12)

    def test_a_grid_with_no_feasible_point_reports_no_solution(self):
        # Never an all-zero allocation: its objective is 0.0, lower than the
        # true optimum, so a caller comparing objectives would rank a policy
        # that solved nothing above one that solved the problem.
        weights = [1.0, 1.0, 1.0, 1.0]
        caps = [0.2, 0.2, 0.2, 0.2]
        self.assertIsNone(ep.grid_allocation(1.0, weights, caps, 2))
        evaluation = ep.evaluate_allocation(
            None, demand=1.0, weights=weights, caps=caps,
            optimum=0.25, quality_floor=0.98,
        )
        self.assertFalse(evaluation.safety_ok)
        self.assertEqual(evaluation.violations, ("NO_FEASIBLE_ALLOCATION_FOUND",))
        self.assertEqual(evaluation.task_quality, 0.0)

    def test_the_analytic_solver_matches_an_exhaustive_grid(self):
        import random as _random

        rng = _random.Random(1)
        for _ in range(60):
            n = 4
            weights = [round(rng.uniform(0.3, 3.0), 3) for _ in range(n)]
            demand = round(rng.uniform(0.5, 2.0), 3)
            caps = [round(rng.uniform(demand / n * 0.6, demand / n * 2.0), 3)
                    for _ in range(n)]
            if sum(caps) <= demand:
                caps = [round(cap + demand / n, 3) for cap in caps]
            exact = ep.analytic_allocation(demand, weights, caps)
            self.assertAlmostEqual(sum(exact), demand, places=6)
            for value, cap in zip(exact, caps):
                self.assertLessEqual(value, cap + 1e-9)
            grid = ep.grid_allocation(demand, weights, caps, 12)
            if grid is not None:
                self.assertLessEqual(
                    ep.objective(weights, exact), ep.objective(weights, grid) + 1e-9
                )

    def test_unclipped_allocation_can_break_a_cap(self):
        weights = [0.5, 2.0, 2.0, 2.0]
        allocation = ep.unclipped_allocation(1.0, weights)
        self.assertAlmostEqual(sum(allocation), 1.0, places=9)
        self.assertGreater(allocation[0], 0.4)

    def test_evaluation_flags_over_cap_and_unmet_demand(self):
        weights = [1.0, 1.0]
        caps = [0.4, 0.4]
        optimum = ep.objective(weights, [0.4, 0.4])
        over = ep.evaluate_allocation(
            [0.8, 0.0], demand=0.8, weights=weights, caps=caps,
            optimum=optimum, quality_floor=0.98,
        )
        self.assertFalse(over.safety_ok)
        self.assertIn("ACTUATOR_0_OVER_CAP", over.violations)
        short = ep.evaluate_allocation(
            [0.2, 0.2], demand=0.8, weights=weights, caps=caps,
            optimum=optimum, quality_floor=0.98,
        )
        self.assertIn("DEMAND_NOT_MET", short.violations)


class MeterBoundary(unittest.TestCase):
    def test_process_meter_measures_a_real_execution(self):
        calls = {"n": 0}

        def workload():
            calls["n"] += 1
            return sum(index * index for index in range(2000))

        reading = ep.ProcessResourceMeter().measure(workload, repeats=3, warmup=1)
        self.assertEqual(calls["n"], 4)
        self.assertEqual(reading.cost_quantity, "cpu_time_s")
        self.assertGreaterEqual(reading.cost_value, 0.0)
        quantities = {item["quantity"] for item in reading.extra}
        self.assertIn("wall_time_s", quantities)
        self.assertIn("latency_ms", quantities)

    def test_process_meter_rejects_zero_repeats(self):
        with self.assertRaises(oc.ContractError):
            ep.ProcessResourceMeter().measure(lambda: None, repeats=0, warmup=0)

    def test_rapl_meter_rejects_zero_repeats(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            domain = root / "intel-rapl:0"
            domain.mkdir()
            (domain / "energy_uj").write_text("1000000\n")
            meter = ep.RaplEnergyMeter(root=root)
            with self.assertRaises(oc.ContractError):
                meter.measure(lambda: None, repeats=0, warmup=0)

    def test_rapl_meter_reports_unavailable_rather_than_guessing(self):
        with tempfile.TemporaryDirectory() as tmp:
            meter = ep.RaplEnergyMeter(root=Path(tmp))
            available, detail = meter.available()
            self.assertFalse(available)
            self.assertIn("no intel-rapl domains", detail)
            with self.assertRaises(oc.OracleUnavailable):
                meter.measure(lambda: None, repeats=1, warmup=0)

    def test_rapl_meter_reads_a_synthetic_powercap_tree(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            domain = root / "intel-rapl:0"
            domain.mkdir()
            (domain / "energy_uj").write_text("1000000\n")
            (domain / "max_energy_range_uj").write_text("262143328850\n")
            meter = ep.RaplEnergyMeter(root=root)
            self.assertTrue(meter.available()[0])

            def workload():
                (domain / "energy_uj").write_text("3000000\n")

            reading = meter.measure(workload, repeats=1, warmup=0)
            self.assertEqual(reading.cost_quantity, "energy_j")
            self.assertAlmostEqual(reading.cost_value, 2.0, places=6)

    def test_recorded_meter_fails_closed_on_an_unknown_key(self):
        meter = ep.RecordedEnergyMeter(
            {
                "run_id": "r1",
                "meter": "external_power_meter",
                "cost_quantity": "energy_j",
                "observations": {"policy_a": {"cost_value": 8.0}},
            }
        )
        self.assertTrue(meter.available()[0])
        self.assertAlmostEqual(meter.lookup("policy_a").cost_value, 8.0)
        with self.assertRaises(oc.OracleUnavailable):
            meter.lookup("policy_zzz")

    def test_recorded_meter_will_not_be_used_as_a_live_meter(self):
        meter = ep.RecordedEnergyMeter({"observations": {"a": {"cost_value": 1.0}}})
        with self.assertRaises(oc.OracleUnavailable):
            meter.measure(lambda: None, repeats=1, warmup=0)

    def test_meter_selection_reports_everything_it_probed(self):
        meter, probe = ep.select_meter(prefer_energy=True)
        self.assertEqual(probe["selected"], meter.name)
        self.assertEqual(probe["cost_is_energy"], meter.measures_energy)
        self.assertTrue(probe["probed"])
        for entry in probe["probed"]:
            self.assertIn("available", entry)
            self.assertTrue(entry["detail"])

    def test_meters_report_names_the_unavailable_meter(self):
        report = ep.meters_report()
        names = {entry["meter"] for entry in report["meters"]}
        self.assertIn("intel_rapl_powercap", names)
        self.assertIn("process_resource_meter", names)
        self.assertIn("no path from a measured second to a joule", report["note"])


class PreferenceRule(unittest.TestCase):
    def candidates(self):
        return [
            {"id": "correct_expensive", "task_quality": 1.0, "safety_ok": True,
             "cost_value": 31.0, "cost_quantity": "energy_j"},
            {"id": "correct_cheap", "task_quality": 1.0, "safety_ok": True,
             "cost_value": 8.0, "cost_quantity": "energy_j"},
            {"id": "wrong_cheapest", "task_quality": 0.2, "safety_ok": True,
             "cost_value": 0.2, "cost_quantity": "energy_j"},
        ]

    def test_lowest_energy_is_not_automatically_preferred(self):
        preference, abstention = ep.choose_preference(self.candidates(), 0.98)
        self.assertIsNone(abstention)
        self.assertEqual(preference["preferred"], "correct_cheap")
        self.assertEqual(
            preference["cheaper_but_constraint_violating"], ["wrong_cheapest"]
        )

    def test_an_unsafe_candidate_is_never_preferred(self):
        candidates = self.candidates()
        candidates.append(
            {"id": "unsafe_fastest", "task_quality": 1.0, "safety_ok": False,
             "cost_value": 0.05, "cost_quantity": "energy_j"}
        )
        preference, _ = ep.choose_preference(candidates, 0.98)
        self.assertEqual(preference["preferred"], "correct_cheap")
        self.assertIn("unsafe_fastest", preference["cheaper_but_constraint_violating"])
        self.assertNotIn("unsafe_fastest", preference["feasible"])

    def test_no_feasible_candidate_abstains_rather_than_choosing(self):
        candidates = [
            {"id": "a", "task_quality": 0.1, "safety_ok": True, "cost_value": 1.0,
             "cost_quantity": "cpu_time_s"},
            {"id": "b", "task_quality": 1.0, "safety_ok": False, "cost_value": 0.5,
             "cost_quantity": "cpu_time_s"},
        ]
        preference, abstention = ep.choose_preference(candidates, 0.98)
        self.assertIsNone(preference)
        self.assertEqual(abstention, ep.ABSTAIN_NO_FEASIBLE)

    def test_ties_break_deterministically_by_id(self):
        candidates = [
            {"id": "zeta", "task_quality": 1.0, "safety_ok": True, "cost_value": 1.0,
             "cost_quantity": "cpu_time_s"},
            {"id": "alpha", "task_quality": 1.0, "safety_ok": True, "cost_value": 1.0,
             "cost_quantity": "cpu_time_s"},
        ]
        preference, _ = ep.choose_preference(candidates, 0.98)
        self.assertEqual(preference["preferred"], "alpha")


class RecordsAreMeasured(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.records = ep.build_records(20260823, 3, repeats=3)

    def test_records_pass_the_envelope_and_family_checks(self):
        for record in self.records:
            where = record["id"]
            self.assertEqual(oc.check_envelope(record, where), [])
            self.assertEqual(oc.check_digest(record, where), [])
            self.assertEqual(ep.check_family(record, where), [])

    def test_cost_is_not_claimed_to_be_energy_without_an_energy_meter(self):
        for record in self.records:
            result = record["result"]
            if not result["cost_is_energy"]:
                self.assertEqual(result["cost_quantity"], "cpu_time_s")
                quantities = {
                    item["quantity"] for item in result["measurements"]
                }
                self.assertFalse(quantities & oc.ENERGY_QUANTITIES)

    def test_every_candidate_cost_is_backed_by_a_measurement(self):
        for record in self.records:
            measured = {
                (item["detail"]["candidate"], item["quantity"]): item["value"]
                for item in record["result"]["measurements"]
                if isinstance(item.get("detail"), dict)
                and "candidate" in item["detail"]
            }
            for candidate in record["result"]["candidates"]:
                key = (candidate["id"], candidate["cost_quantity"])
                self.assertIn(key, measured)
                self.assertEqual(measured[key], candidate["cost_value"])

    def test_the_unsafe_policy_is_never_preferred(self):
        # Only what a real measurement can promise. Whether the unsafe policy
        # also lands *cheaper* depends on this host's clock granularity, so
        # that half is asserted against the deterministic meter instead
        # (DeterministicMeterPaths).
        for record in self.records:
            by_id = {c["id"]: c for c in record["result"]["candidates"]}
            unclipped = by_id["unclipped_proportional"]
            self.assertFalse(unclipped["safety_ok"])
            self.assertTrue(unclipped["safety_violations"])
            preference = record["result"]["preference"]
            self.assertNotEqual(preference["preferred"], "unclipped_proportional")
            self.assertNotIn("unclipped_proportional", preference["feasible"])

    def test_the_meter_probe_is_recorded_on_the_oracle(self):
        for record in self.records:
            probe = record["oracle"]["configuration"]["meter_probe"]
            self.assertEqual(probe["selected"], record["oracle"]["name"])
            self.assertTrue(record["oracle"]["fingerprint"]["platform"])

    def test_generator_namespaces_carry_no_measurement(self):
        for record in self.records:
            self.assertEqual(oc.check_generator_oracle_separation(record, "x"), [])


class DeterministicMeterPaths(unittest.TestCase):
    def test_a_deterministic_meter_prefers_the_cheapest_feasible_policy(self):
        # Call order is alphabetical: analytic, coarse, exhaustive, unclipped.
        # The cheapest two measurements go to a policy below the quality floor
        # and to the unsafe one, so a "cheapest wins" rule would pick either.
        costs = {1: 0.1, 2: 0.05, 3: 1.0, 4: 0.01}
        meter = FakeMeter(costs)
        records = ep.build_records(7, 1, meter=meter, repeats=2)
        result = records[0]["result"]
        preference = result["preference"]
        self.assertEqual(preference["preferred"], "analytic_kkt")
        self.assertEqual(ep.check_family(records[0], "x"), [])
        self.assertEqual(meter.calls, 4)
        self.assertEqual(
            preference["cheaper_but_constraint_violating"],
            ["coarse_grid", "unclipped_proportional"],
        )
        by_id = {c["id"]: c for c in result["candidates"]}
        self.assertLess(
            by_id["unclipped_proportional"]["cost_value"],
            by_id["analytic_kkt"]["cost_value"],
        )
        self.assertFalse(by_id["unclipped_proportional"]["safety_ok"])

    def test_an_energy_meter_produces_an_energy_denominated_record(self):
        records = ep.build_records(7, 1, meter=FakeEnergyMeter(), repeats=2)
        record = records[0]
        self.assertTrue(record["result"]["cost_is_energy"])
        self.assertEqual(record["result"]["preference"]["cost_quantity"], "energy_j")
        self.assertEqual(oc.check_envelope(record, "x"), [])
        self.assertEqual(oc.check_no_theoretical_energy_claim(record, "x"), [])

    def test_an_unavailable_meter_is_refused_rather_than_worked_around(self):
        class DeadMeter(FakeMeter):
            def available(self):
                return False, "counter not readable"

        with self.assertRaises(oc.OracleUnavailable):
            ep.build_records(7, 1, meter=DeadMeter())


class FamilyChecks(unittest.TestCase):
    def setUp(self):
        self.record = ep.build_records(7, 1, meter=FakeMeter(), repeats=2)[0]

    def test_an_unsafe_preferred_candidate_is_rejected(self):
        preferred = self.record["result"]["preference"]["preferred"]
        for candidate in self.record["result"]["candidates"]:
            if candidate["id"] == preferred:
                candidate["safety_ok"] = False
                candidate["safety_violations"] = ["ACTUATOR_0_OVER_CAP"]
        errors = ep.check_family(self.record, "x")
        self.assertTrue(
            any("PREFERRED_CANDIDATE_UNSAFE" in error for error in errors)
        )

    def test_a_preferred_candidate_below_the_quality_floor_is_rejected(self):
        preferred = self.record["result"]["preference"]["preferred"]
        for candidate in self.record["result"]["candidates"]:
            if candidate["id"] == preferred:
                candidate["task_quality"] = 0.1
        errors = ep.check_family(self.record, "x")
        self.assertTrue(
            any("BELOW_QUALITY_FLOOR" in error for error in errors)
        )

    def test_a_cheaper_feasible_candidate_makes_the_preference_non_minimal(self):
        preference = self.record["result"]["preference"]
        for candidate in self.record["result"]["candidates"]:
            if candidate["id"] != preference["preferred"]:
                candidate["safety_ok"] = True
                candidate["task_quality"] = 1.0
                candidate["cost_value"] = 0.0
                for item in self.record["result"]["measurements"]:
                    detail = item.get("detail") or {}
                    if (
                        detail.get("candidate") == candidate["id"]
                        and item["quantity"] == candidate["cost_quantity"]
                    ):
                        item["value"] = 0.0
                break
        errors = ep.check_family(self.record, "x")
        self.assertTrue(
            any("NOT_MINIMAL_FEASIBLE_COST" in error for error in errors)
        )

    def test_a_cost_that_no_measurement_backs_is_rejected(self):
        self.record["result"]["candidates"][0]["cost_value"] = 999.0
        errors = ep.check_family(self.record, "x")
        self.assertTrue(
            any("disagrees with the oracle measurement" in error for error in errors)
        )

    def test_a_candidate_with_no_measurement_at_all_is_rejected(self):
        candidate = self.record["result"]["candidates"][0]
        self.record["result"]["measurements"] = [
            item
            for item in self.record["result"]["measurements"]
            if (item.get("detail") or {}).get("candidate") != candidate["id"]
        ]
        errors = ep.check_family(self.record, "x")
        self.assertTrue(any("UNMEASURED_COST" in error for error in errors))

    def test_a_missing_quality_floor_is_rejected(self):
        del self.record["scenario"]["constraints"]["quality_floor"]
        errors = ep.check_family(self.record, "x")
        self.assertTrue(any("quality_floor" in error for error in errors))

    def test_an_abstained_record_must_not_carry_a_preference(self):
        self.record["result"]["status"] = oc.RESULT_ABSTAINED
        errors = ep.check_family(self.record, "x")
        self.assertTrue(
            any("must not carry a preference" in error for error in errors)
        )


class Cli(unittest.TestCase):
    def test_meters_subcommand_emits_json(self):
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            self.assertEqual(ep.main(["meters"]), 0)
        payload = json.loads(buffer.getvalue())
        self.assertEqual(payload["family"], ep.FAMILY)

    def test_measure_writes_jsonl(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "batch.jsonl"
            with contextlib.redirect_stdout(io.StringIO()):
                exit_code = ep.main(
                    ["measure", "--seed", "5", "--count", "1", "--repeats", "2",
                     "--output", str(out)]
                )
            self.assertEqual(exit_code, 0)
            self.assertEqual(len(oc.read_jsonl(out)), 1)


if __name__ == "__main__":
    unittest.main()
