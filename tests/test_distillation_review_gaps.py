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


class BaselineGaps(unittest.TestCase):
    """router_baseline.py"""

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
            # The committed fixture layout: a manifest beside family folders.
            (out / "moe-router").mkdir(parents=True)
            (out / "MANIFEST.json").write_text("{}\n", encoding="utf-8")
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


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
