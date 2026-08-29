#!/usr/bin/env python3
"""Focused tests for reward ontology v1 and conservative conversion."""

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

_TESTS = Path(__file__).resolve().parent
if str(_TESTS) not in sys.path:
    sys.path.insert(0, str(_TESTS))

from reward_test_helpers import (  # noqa: E402
    MAGNITUDE,
    PIPELINES,
    SCHEMA,
    all_fixture_records,
    components,
    preference,
    rich,
)

if str(PIPELINES) not in sys.path:
    sys.path.insert(0, str(PIPELINES))

import curate_rewards  # noqa: E402


class RewardOntologyV1Tests(unittest.TestCase):
    def test_schema_declares_exclusive_comparability_classes(self):
        schema = json.loads(SCHEMA.read_text())
        annotation = schema["$defs"]["annotation"]
        self.assertEqual(
            annotation["properties"]["comparability"]["enum"],
            [
                "magnitude_comparable",
                "sign_order_only",
                "exclude_from_reward_training",
            ],
        )
        self.assertEqual(
            annotation["properties"]["magnitude"]["properties"]["canonical_unit"]["const"],
            "usd_10000_risk_adjusted_delta",
        )
        self.assertEqual(len(annotation["allOf"]), 2)

    def test_structured_usd_rich_preference_is_magnitude_comparable(self):
        units = "1.0 reward unit = USD 10,000 (risk-adjusted); deltas vs baseline"
        record = preference(
            components(1.0, unit_usd=10000, units=units, rich_values=True),
            components(-1.0, unit_usd=10000, units=units, rich_values=True),
        )
        record["rejected"]["reward_components"]["task_progress"] = rich(-1.2)
        record["rejected"]["reward_components"]["safety"] = rich(0.0)
        record["rejected"]["reward_components"]["efficiency"] = rich(0.2)

        curated, sidecar = curate_rewards.curate_record(
            record, source_path="factory/batch-r03.jsonl", source_line=2
        )

        annotation = curated["reward_training"]
        self.assertEqual(annotation["comparability"], "magnitude_comparable")
        magnitudes = curate_rewards.canonical_magnitudes(curated)
        self.assertEqual(magnitudes["/chosen/reward_components"], 1.0)
        self.assertEqual(magnitudes["/rejected/reward_components"], -1.0)
        self.assertEqual(len(sidecar["source_rewards"]), 2)
        self.assertTrue(all(item["status"] == "valid" for item in sidecar["arithmetic"]))
        self.assertEqual(record["chosen"]["reward_components"], curated["chosen"]["reward_components"])

    def test_text_only_legacy_usd_unit_converts_to_canonical_scale(self):
        chosen = {
            "task_progress": 3.0,
            "safety": 0.6,
            "total": 3.6,
            "units": "1.0 = $2,000; risk-adjusted terms priced by audit",
        }
        rejected = {
            "task_progress": 0.2,
            "safety": -0.8,
            "total": -0.6,
            "units": "1.0 = $2,000; risk-adjusted terms priced by audit",
        }
        curated, _ = curate_rewards.curate_record(preference(chosen, rejected))

        values = curated["reward_training"]["magnitude"]["values"]
        by_pointer = {value["json_pointer"]: value for value in values}
        self.assertEqual(
            by_pointer["/chosen/reward_components"]["conversion_factor"], 0.2
        )
        self.assertEqual(
            by_pointer["/chosen/reward_components"]["canonical_value"], 0.72
        )

    def test_explicit_migration_evidence_calibrates_a_partially_labeled_pair(self):
        record = preference(
            {
                "task_progress": 3.0,
                "safety": 0.6,
                "total": 3.6,
                "units": "1.0 = $2,000; audited_true_reward basis",
            },
            {
                "task_progress": 0.2,
                "safety": -0.8,
                "total": -0.6,
                "units": "1.0 = $2,000; risk-adjusted terms",
            },
        )
        calibration = {
            "source_unit_usd": 2000,
            "canonical_factor": 0.2,
            "evidence_ref": "units-migration.json#/records/1",
        }

        without_evidence, _ = curate_rewards.curate_record(record)
        with_evidence, sidecar = curate_rewards.curate_record(
            record, calibration=calibration
        )

        self.assertEqual(
            without_evidence["reward_training"]["comparability"],
            "sign_order_only",
        )
        annotation = with_evidence["reward_training"]
        self.assertEqual(annotation["comparability"], "magnitude_comparable")
        self.assertIn("external_calibration_evidence", annotation["reason_codes"])
        by_pointer = {
            value["json_pointer"]: value.get("calibration_source")
            for value in annotation["magnitude"]["values"]
        }
        self.assertEqual(
            by_pointer["/chosen/reward_components"],
            "units-migration.json#/records/1",
        )
        self.assertEqual(
            by_pointer["/rejected/reward_components"],
            "source_reward_fields",
        )
        self.assertEqual(
            sidecar["calibration"]["source_unit_usd"],
            2000,
        )
        self.assertEqual(
            sidecar["calibration"]["evidence_ref"],
            "units-migration.json#/records/1",
        )

    def test_units_migration_loader_ignores_null_and_coarse_guess(self):
        migration = {
            "records": [
                {
                    "scope": "preferences.jsonl (r1-1..r1-6)",
                    "usd_conversion_factor": None,
                    "coarse_affine_guess_factor": 0.27,
                },
                {
                    "scope": "batch-r02.jsonl / ffpc-r2-001 (grid)",
                    "usd_conversion_factor": 0.2,
                },
            ]
        }
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "units-migration.json"
            path.write_text(json.dumps(migration))
            catalog = curate_rewards.load_units_migration(path)

        self.assertEqual(set(catalog), {"ffpc-r2-001"})
        self.assertEqual(catalog["ffpc-r2-001"]["source_unit_usd"], 2000.0)
        self.assertEqual(catalog["ffpc-r2-001"]["canonical_factor"], 0.2)

    def test_unitless_preference_is_order_only_without_magnitude(self):
        record = preference(
            {"task_progress": 0.7, "safety": 0.3, "total": 1.0},
            {"task_progress": -0.4, "safety": -0.1, "total": -0.5},
        )
        curated, sidecar = curate_rewards.curate_record(record)

        annotation = curated["reward_training"]
        self.assertEqual(annotation["comparability"], "sign_order_only")
        self.assertNotIn("magnitude", annotation)
        self.assertEqual(
            annotation["order"]["relation"], "preferred_gt_dispreferred"
        )
        with self.assertRaises(curate_rewards.MagnitudeNotComparable):
            curate_rewards.canonical_magnitudes(curated)
        self.assertEqual(
            sidecar["source_rewards"][0]["value"],
            record["chosen"]["reward_components"],
        )

    def test_design_margin_preference_stays_order_only(self):
        units = "normalized berthing-episode scale; 1.0 ~= one design-margin quantum"
        record = preference(
            {"task_progress": 1.0, "safety": 1.0, "total": 2.0, "units": units},
            {"task_progress": -0.5, "safety": 0.0, "total": -0.5, "units": units},
        )
        curated, _ = curate_rewards.curate_record(record)
        self.assertEqual(
            curated["reward_training"]["comparability"], "sign_order_only"
        )

    def test_conflicting_unit_declarations_never_emit_magnitude(self):
        record = preference(
            components(
                1.0,
                unit_usd=10000,
                units="1.0 = $2,000; risk-adjusted terms",
            ),
            components(
                -1.0,
                unit_usd=10000,
                units="1.0 = $2,000; risk-adjusted terms",
            ),
        )
        record["rejected"]["reward_components"].update(
            {"task_progress": -1.2, "safety": 0.0, "efficiency": 0.2}
        )
        curated, _ = curate_rewards.curate_record(record)
        annotation = curated["reward_training"]
        self.assertEqual(annotation["comparability"], "sign_order_only")
        self.assertIn("magnitude_calibration_conflict", annotation["reason_codes"])
        self.assertNotIn("magnitude", annotation)

    def test_arithmetic_mismatch_excludes_even_with_explicit_units(self):
        units = "1.0 reward unit = USD 10,000 (risk-adjusted); deltas vs baseline"
        record = preference(
            components(99.0, unit_usd=10000, units=units),
            components(-1.0, unit_usd=10000, units=units),
        )
        record["rejected"]["reward_components"].update(
            {"task_progress": -1.2, "safety": 0.0, "efficiency": 0.2}
        )
        curated, sidecar = curate_rewards.curate_record(record)
        annotation = curated["reward_training"]
        self.assertEqual(annotation["comparability"], "exclude_from_reward_training")
        self.assertEqual(annotation["reason_codes"], ["reward_arithmetic_mismatch"])
        self.assertIn("invalid", {item["status"] for item in sidecar["arithmetic"]})

    def test_reward_order_conflict_excludes_from_reward_training(self):
        record = preference(
            {"task_progress": 0.0, "safety": 0.0, "total": 0.0},
            {"task_progress": 0.5, "safety": 0.5, "total": 1.0},
        )
        curated, _ = curate_rewards.curate_record(record)
        self.assertEqual(
            curated["reward_training"]["reason_codes"],
            ["reward_order_conflicts_with_preference"],
        )

    def test_uncalibrated_thalamic_total_is_excluded_not_magnitude_mixed(self):
        record = {
            "id": "thalamic-fixture",
            "reward_components": components(1.0),
        }
        curated, sidecar = curate_rewards.curate_record(record)
        annotation = curated["reward_training"]
        self.assertEqual(annotation["comparability"], "exclude_from_reward_training")
        self.assertEqual(annotation["reason_codes"], ["magnitude_calibration_missing"])
        self.assertEqual(sidecar["arithmetic"][0]["status"], "valid")
        with self.assertRaises(curate_rewards.MagnitudeNotComparable):
            curate_rewards.canonical_magnitudes(curated)

    def test_weighted_ouroboros_shape_reconciles_but_remains_uncalibrated(self):
        record = {
            "id": "ouroboros-fixture",
            "reward_components": {
                "components": {"task": 0.8, "safety": 0.6},
                "weights": {"task": 0.25, "safety": 0.75},
                "total": 0.65,
                "aggregation": "weighted sum",
            },
        }
        curated, sidecar = curate_rewards.curate_record(record)
        self.assertEqual(sidecar["arithmetic"][0]["status"], "valid")
        self.assertEqual(
            curated["reward_training"]["comparability"],
            "exclude_from_reward_training",
        )

    def test_coding_episode_reward_is_preserved_and_excluded(self):
        record = {
            "goal": "repair a flaky test",
            "steps": [],
            "outcome": "fixed",
            "reward": {
                "success": True,
                "quality": 0.9,
                "cost": {"tokens": 68000, "usd_est": 2.1},
            },
        }
        curated, sidecar = curate_rewards.curate_record(record)
        self.assertEqual(
            curated["reward_training"]["comparability"],
            "exclude_from_reward_training",
        )
        self.assertEqual(
            curated["reward_training"]["reason_codes"],
            ["noncanonical_reward_scope"],
        )
        self.assertEqual(sidecar["source_rewards"][0]["value"], record["reward"])

    def test_transform_is_idempotent_and_sidecar_restores_exact_source(self):
        record = preference(
            {"task_progress": 0.8, "safety": 0.2, "total": 1.0},
            {"task_progress": -0.5, "safety": -0.5, "total": -1.0},
        )
        frozen = copy.deepcopy(record)
        first, first_sidecar = curate_rewards.curate_record(
            record, source_path="factory/preferences.jsonl", source_line=7
        )
        second, second_sidecar = curate_rewards.curate_record(
            first, source_path="factory/preferences.jsonl", source_line=7
        )

        self.assertEqual(first, second)
        self.assertEqual(first_sidecar, second_sidecar)
        self.assertEqual(record, frozen, "input record must not be mutated")
        self.assertEqual(
            curate_rewards.restore_source_record(first, first_sidecar), frozen
        )

    def test_runtime_validator_rejects_magnitude_on_order_only_annotation(self):
        record = preference(
            {"task_progress": 1.0, "safety": 0.0, "total": 1.0},
            {"task_progress": 0.0, "safety": 0.0, "total": 0.0},
        )
        curated, _ = curate_rewards.curate_record(record)
        malformed = copy.deepcopy(curated["reward_training"])
        malformed["magnitude"] = {
            "canonical_unit": "usd_10000_risk_adjusted_delta",
            "aggregation": "linear_unit_conversion_only",
            "values": [],
        }
        with self.assertRaisesRegex(
            curate_rewards.RewardOntologyError, "must not expose"
        ):
            curate_rewards.validate_ontology_document(malformed)

    def test_runtime_validator_rejects_class_reason_contradictions(self):
        units = "1 reward unit = USD 10000 risk-adjusted"
        record = {
            "reward_components": components(
                1.0, unit_usd=10000, units=units
            )
        }
        curated, sidecar = curate_rewards.curate_record(record)

        malformed_annotation = copy.deepcopy(curated["reward_training"])
        malformed_annotation["reason_codes"] = ["no_source_reward"]
        with self.assertRaisesRegex(
            curate_rewards.RewardOntologyError,
            "does not match any declared comparability rule",
        ):
            curate_rewards.validate_ontology_document(malformed_annotation)

        malformed_sidecar = copy.deepcopy(sidecar)
        malformed_sidecar["classification"]["reason_codes"] = ["no_source_reward"]
        malformed_sidecar.pop("sidecar_id")
        malformed_sidecar["sidecar_id"] = curate_rewards._sha256(malformed_sidecar)
        with self.assertRaisesRegex(
            curate_rewards.RewardOntologyError,
            "does not match any declared comparability rule",
        ):
            curate_rewards.validate_ontology_document(malformed_sidecar)

    def test_sidecar_hash_and_annotation_link_are_enforced(self):
        record = preference(
            {"task_progress": 1.0, "safety": 0.0, "total": 1.0},
            {"task_progress": 0.0, "safety": 0.0, "total": 0.0},
        )
        curated, sidecar = curate_rewards.curate_record(record)

        tampered_sidecar = copy.deepcopy(sidecar)
        tampered_sidecar["classification"]["reason_codes"].append("tampered")
        with self.assertRaisesRegex(
            curate_rewards.RewardOntologyError, "content hash mismatch"
        ):
            curate_rewards.validate_ontology_document(tampered_sidecar)

        wrong_link = copy.deepcopy(curated)
        wrong_link["reward_training"]["source_sidecar_id"] = "sha256:" + "0" * 64
        with self.assertRaisesRegex(
            curate_rewards.RewardOntologyError, "different sidecar"
        ):
            curate_rewards.restore_source_record(wrong_link, sidecar)

    def test_sidecar_reason_codes_must_be_strings_after_rehash(self):
        record = preference(
            {"task_progress": 1.0, "safety": 0.0, "total": 1.0},
            {"task_progress": 0.0, "safety": 0.0, "total": 0.0},
        )
        _curated, sidecar = curate_rewards.curate_record(record)
        malformed = copy.deepcopy(sidecar)
        malformed["classification"]["reason_codes"].append(1)
        malformed.pop("sidecar_id")
        malformed["sidecar_id"] = curate_rewards._sha256(malformed)

        with self.assertRaisesRegex(
            curate_rewards.RewardOntologyError,
            "invalid sidecar classification",
        ):
            curate_rewards.validate_ontology_document(malformed)

    def test_annotation_reason_codes_reject_unhashable_elements(self):
        record = {"id": "single-cal", "reward_components": components(1.0)}
        curated, _sidecar = curate_rewards.curate_record(record)
        malformed = copy.deepcopy(curated["reward_training"])
        malformed["reason_codes"] = [{}]
        with self.assertRaisesRegex(
            curate_rewards.RewardOntologyError,
            "reason_codes must be nonempty and unique",
        ):
            curate_rewards.validate_ontology_document(malformed)

    def test_stored_preference_verdict_must_match_a_preference_rule(self):
        record = preference(
            {
                "task_progress": 1.0,
                "safety": 0.0,
                "total": 1.0,
                "unit_usd": 10000,
                "units": "1.0 reward unit = USD 10,000 (risk-adjusted)",
            },
            {
                "task_progress": 0.0,
                "safety": 0.0,
                "total": 0.0,
                "unit_usd": 10000,
                "units": "1.0 reward unit = USD 10,000 (risk-adjusted)",
            },
        )
        _curated, sidecar = curate_rewards.curate_record(record)
        malformed = copy.deepcopy(sidecar)
        malformed["classification"] = {
            "comparability": "magnitude_comparable",
            "reason_codes": [
                "explicit_usd_unit_calibration",
                "reward_arithmetic_verified",
            ],
        }
        malformed.pop("sidecar_id")
        malformed["sidecar_id"] = curate_rewards._sha256(malformed)
        with self.assertRaisesRegex(
            curate_rewards.RewardOntologyError,
            "does not match any declared comparability rule",
        ):
            curate_rewards.validate_ontology_document(malformed)

    def test_jsonl_loader_rejects_overflow_float_literals(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "overflow.jsonl"
            path.write_text(
                '{"reward_components":{"total":1e400}}\n', encoding="utf-8"
            )
            with self.assertRaisesRegex(
                curate_rewards.RewardOntologyError,
                "non-finite JSON number",
            ):
                list(curate_rewards._load_jsonl(path))

    def test_sidecar_arithmetic_must_be_a_list(self):
        record = preference(
            {"task_progress": 1.0, "safety": 0.0, "total": 1.0},
            {"task_progress": 0.0, "safety": 0.0, "total": 0.0},
        )
        _curated, sidecar = curate_rewards.curate_record(record)
        malformed = copy.deepcopy(sidecar)
        malformed["arithmetic"] = None
        malformed.pop("sidecar_id")
        malformed["sidecar_id"] = curate_rewards._sha256(malformed)

        with self.assertRaisesRegex(
            curate_rewards.RewardOntologyError, "sidecar arithmetic must be a list"
        ):
            curate_rewards.validate_ontology_document(malformed)

    def test_sidecar_arithmetic_entries_are_fail_closed(self):
        record = preference(
            {"task_progress": 1.0, "safety": 0.0, "total": 1.0},
            {"task_progress": 0.0, "safety": 0.0, "total": 0.0},
        )
        _curated, sidecar = curate_rewards.curate_record(record)
        cases = (
            (["not-an-object"], "invalid sidecar arithmetic entry"),
            (
                [{"status": "bogus", "method": "unweighted_component_sum"}],
                "invalid sidecar arithmetic status",
            ),
            (
                [{"status": "valid", "method": "invented"}],
                "uncatalogued arithmetic method",
            ),
        )
        for arithmetic, message in cases:
            malformed = copy.deepcopy(sidecar)
            malformed["arithmetic"] = arithmetic
            malformed.pop("sidecar_id")
            malformed["sidecar_id"] = curate_rewards._sha256(malformed)
            with self.assertRaisesRegex(
                curate_rewards.RewardOntologyError, message
            ):
                curate_rewards.validate_ontology_document(malformed)

    def test_s08_emits_external_calibration_evidence(self):
        record = {"id": "single-cal", "reward_components": components(1.0)}
        calibration = {
            "source_unit_usd": 2000,
            "canonical_factor": 0.2,
            "evidence_ref": "units-migration.json#/records/1",
        }

        without_evidence, _ = curate_rewards.curate_record(record)
        with_evidence, sidecar = curate_rewards.curate_record(
            record, calibration=calibration
        )

        self.assertNotIn(
            "external_calibration_evidence",
            without_evidence["reward_training"]["reason_codes"],
        )
        annotation = with_evidence["reward_training"]
        self.assertEqual(annotation["comparability"], "magnitude_comparable")
        self.assertIn("external_calibration_evidence", annotation["reason_codes"])
        self.assertNotIn("explicit_usd_unit_calibration", annotation["reason_codes"])
        self.assertEqual(
            sidecar["calibration"]["evidence_ref"],
            "units-migration.json#/records/1",
        )

    def test_preference_order_uses_canonical_unit_conversion(self):
        units_small = "1.0 reward unit = USD 1,000 (risk-adjusted); deltas vs baseline"
        units_large = "1.0 reward unit = USD 10,000 (risk-adjusted); deltas vs baseline"
        record = preference(
            {
                "task_progress": 3.0,
                "safety": 0.0,
                "total": 3.0,
                "unit_usd": 1000,
                "units": units_small,
            },
            {
                "task_progress": 2.0,
                "safety": 0.0,
                "total": 2.0,
                "unit_usd": 10000,
                "units": units_large,
            },
        )
        curated, _sidecar = curate_rewards.curate_record(record)
        self.assertEqual(
            curated["reward_training"]["comparability"],
            "exclude_from_reward_training",
        )
        self.assertIn(
            "reward_order_conflicts_with_preference",
            curated["reward_training"]["reason_codes"],
        )

    def test_external_calibration_reason_is_reserved_to_p05_and_s08(self):
        document = copy.deepcopy(curate_rewards.CONVERSION_POLICY)
        r00 = next(
            rule
            for rule in document["policy"]["comparability_rules"]
            if rule["id"] == "R00"
        )
        r00["reason_codes"] = list(r00["reason_codes"]) + [
            "external_calibration_evidence"
        ]
        with self.assertRaisesRegex(
            curate_rewards.RewardOntologyError,
            "reserved for optional codes",
        ):
            curate_rewards.validate_conversion_policy(document)

    def test_sidecar_calibration_reason_linkage_is_fail_closed(self):
        record = {"id": "single-cal", "reward_components": components(1.0)}
        calibration = {
            "source_unit_usd": 2000,
            "canonical_factor": 0.2,
            "evidence_ref": "units-migration.json#/records/1",
        }
        _curated, sidecar = curate_rewards.curate_record(
            record, calibration=calibration
        )

        missing_reason = copy.deepcopy(sidecar)
        missing_reason["classification"]["reason_codes"] = [
            code
            for code in missing_reason["classification"]["reason_codes"]
            if code != "external_calibration_evidence"
        ]
        missing_reason.pop("sidecar_id", None)
        missing_reason["sidecar_id"] = curate_rewards._sha256(missing_reason)
        with self.assertRaisesRegex(
            curate_rewards.RewardOntologyError,
            "sidecar calibration requires external_calibration_evidence",
        ):
            curate_rewards.validate_ontology_document(missing_reason)

        missing_calibration = copy.deepcopy(sidecar)
        missing_calibration.pop("calibration")
        missing_calibration.pop("sidecar_id", None)
        missing_calibration["sidecar_id"] = curate_rewards._sha256(missing_calibration)
        with self.assertRaisesRegex(
            curate_rewards.RewardOntologyError,
            "external_calibration_evidence requires an applied sidecar calibration",
        ):
            curate_rewards.validate_ontology_document(missing_calibration)

    def test_runtime_validator_recomputes_canonical_conversion(self):
        units = "1.0 reward unit = USD 10,000 (risk-adjusted); deltas vs baseline"
        record = preference(
            components(1.0, unit_usd=10000, units=units),
            components(-1.0, unit_usd=10000, units=units),
        )
        record["rejected"]["reward_components"].update(
            {"task_progress": -1.2, "safety": 0.0, "efficiency": 0.2}
        )
        curated, _ = curate_rewards.curate_record(record)
        malformed = copy.deepcopy(curated["reward_training"])
        malformed["magnitude"]["values"][0]["canonical_value"] = 999.0

        with self.assertRaisesRegex(
            curate_rewards.RewardOntologyError, "converted value mismatch"
        ):
            curate_rewards.validate_ontology_document(malformed)

class MagnitudeMixingTests(unittest.TestCase):
    """An uncalibrated record cannot enter a magnitude-weighted set."""

    def curated(self, name, line_number):
        for candidate_name, candidate_line, record in all_fixture_records():
            if (candidate_name, candidate_line) == (name, line_number):
                curated, _sidecar = curate_rewards.curate_record(
                    record, source_path=name, source_line=line_number
                )
                return curated
        raise AssertionError(f"no fixture record at {name}:{line_number}")

    def test_a_comparable_cohort_yields_canonical_values(self):
        cohort = curate_rewards.magnitude_training_cohort(
            [
                self.curated("ffpc-preferences.jsonl", 1),
                self.curated("ffpc-preferences.jsonl", 2),
                self.curated("thalamic-trajectories.jsonl", 2),
            ]
        )
        self.assertEqual(len(cohort), 3)
        for member in cohort:
            self.assertEqual(
                member["canonical_unit"], curate_rewards.CANONICAL_UNIT
            )
            self.assertEqual(
                member["aggregation"], curate_rewards.MAGNITUDE_AGGREGATION
            )
            self.assertTrue(member["values"])
        self.assertAlmostEqual(
            cohort[0]["values"]["/chosen/reward_components"],
            3.11 * 2.0,
            places=9,
        )

    def test_one_uncalibrated_member_refuses_the_whole_cohort(self):
        comparable = self.curated("ffpc-preferences.jsonl", 1)
        for name, line_number in (
            ("ffpc-preferences.jsonl", 4),
            ("thalamic-trajectories.jsonl", 1),
        ):
            uncalibrated = self.curated(name, line_number)
            with self.assertRaisesRegex(
                curate_rewards.MagnitudeNotComparable,
                "may contain only magnitude_comparable records",
            ):
                curate_rewards.magnitude_training_cohort([comparable, uncalibrated])
            with self.assertRaises(curate_rewards.MagnitudeNotComparable):
                curate_rewards.canonical_magnitudes(uncalibrated)

    def test_an_unannotated_record_cannot_join_a_cohort(self):
        with self.assertRaisesRegex(
            curate_rewards.MagnitudeNotComparable, "no usable comparability class"
        ):
            curate_rewards.magnitude_training_cohort([{"reward_components": {}}])

    def test_duplicate_magnitude_pointers_are_rejected(self):
        curated = self.curated("ffpc-preferences.jsonl", 1)
        values = curated[curate_rewards.ANNOTATION_FIELD]["magnitude"]["values"]
        values.append(copy.deepcopy(values[0]))

        with self.assertRaisesRegex(
            curate_rewards.RewardOntologyError, "duplicate magnitude json_pointer"
        ):
            curate_rewards.canonical_magnitudes(curated)
        with self.assertRaisesRegex(
            curate_rewards.RewardOntologyError, "duplicate magnitude json_pointer"
        ):
            curate_rewards.magnitude_training_cohort([curated])

    def test_uncalibrated_annotations_never_carry_canonical_values(self):
        for name, line_number, record in all_fixture_records():
            curated, _sidecar = curate_rewards.curate_record(
                record, source_path=name, source_line=line_number
            )
            annotation = curated[curate_rewards.ANNOTATION_FIELD]
            if annotation["comparability"] == MAGNITUDE:
                self.assertIn("magnitude", annotation)
            else:
                self.assertNotIn("magnitude", annotation)
                json_text = json.dumps(annotation)
                self.assertNotIn("canonical_value", json_text)
                self.assertNotIn(curate_rewards.CANONICAL_UNIT, json_text)



if __name__ == '__main__':
    unittest.main()
