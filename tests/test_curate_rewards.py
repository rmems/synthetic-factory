#!/usr/bin/env python3
"""Focused tests for reward ontology v1 and conservative conversion."""

import collections
import copy
import hashlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from contextlib import redirect_stderr, redirect_stdout

REPO = Path(__file__).resolve().parents[1]
PIPELINES = REPO / "pipelines"
SCHEMA = REPO / "schemas" / "reward-ontology-v1.schema.json"
sys.path.insert(0, str(PIPELINES))

import curate_gate  # noqa: E402
import curate_rewards  # noqa: E402


def rich(value):
    return {"value": value, "detail": "fixture evidence"}


def components(total, *, unit_usd=None, units=None, rich_values=False):
    values = {
        "task_progress": 1.2,
        "safety": -0.4,
        "efficiency": 0.2,
    }
    if rich_values:
        values = {key: rich(value) for key, value in values.items()}
    values["total"] = total
    if unit_usd is not None:
        values["unit_usd"] = unit_usd
    if units is not None:
        values["units"] = units
    return values


def preference(chosen_reward, rejected_reward):
    return {
        "id": "pref-fixture",
        "chosen": {"reward_components": chosen_reward},
        "rejected": {"reward_components": rejected_reward},
        "critique": "chosen is preferred on observable process evidence",
    }


def write_jsonl(path, records):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(
            json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n"
            for record in records
        ),
        encoding="utf-8",
    )


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

    def test_jsonl_conversion_is_no_clobber_and_uses_reversible_sidecars(self):
        record = preference(
            {"task_progress": 0.8, "safety": 0.2, "total": 1.0},
            {"task_progress": -0.5, "safety": -0.5, "total": -1.0},
        )
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "input.jsonl"
            output = root / "out" / "records.jsonl"
            sidecars = root / "out" / "reward-sidecars.jsonl"
            manifest = root / "out" / "manifest.json"
            source.write_text(json.dumps(record) + "\n")

            summary = curate_rewards.convert_jsonl(
                source,
                output,
                sidecars,
                source_path="factory/preferences.jsonl",
                manifest_path=manifest,
            )
            self.assertEqual(summary["records"], 1)
            self.assertEqual(summary["manifest"], str(manifest))
            converted = json.loads(output.read_text())
            sidecar = json.loads(sidecars.read_text())
            entries = json.loads(manifest.read_text())
            self.assertEqual(len(entries), 1)
            self.assertEqual(entries[0]["source_path"], "factory/preferences.jsonl")
            self.assertEqual(entries[0]["source_line"], 1)
            self.assertEqual(entries[0]["transform_name"], "reward_ontology")
            self.assertEqual(entries[0]["transform_version"], "reward-ontology-v1")
            self.assertEqual(entries[0]["action"], "retained")
            self.assertEqual(
                entries[0]["output_hash"],
                hashlib.sha256(curate_rewards._canonical_bytes(converted)).hexdigest(),
            )
            self.assertEqual(
                curate_rewards.restore_source_record(converted, sidecar), record
            )
            with self.assertRaisesRegex(
                curate_rewards.RewardOntologyError, "refusing to overwrite"
            ):
                curate_rewards.convert_jsonl(
                    source,
                    output,
                    sidecars,
                    manifest_path=manifest,
                )

    def test_run_conversion_is_deterministic_and_gate_compatible(self):
        alpha_record = preference(
            {"task_progress": 0.8, "safety": 0.2, "total": 1.0},
            {"task_progress": -0.5, "safety": -0.5, "total": -1.0},
        )
        alpha_record["id"] = "alpha-pref"
        zeta_record = {
            "id": "zeta-reward",
            "reward_components": components(1.0),
        }
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "source-run"
            alpha_relative = Path("alpha-factory/nested/preferences.jsonl")
            zeta_relative = Path("zeta-factory/batch-r02.jsonl")
            # Create in reverse lexical order to prove traversal order is path-stable.
            write_jsonl(source / zeta_relative, [zeta_record])
            write_jsonl(source / alpha_relative, [alpha_record])

            first = root / "lane-reward-a"
            second = root / "lane-reward-b"
            summary = curate_rewards.convert_run(source, first)
            curate_rewards.convert_run(source, second)

            ordered_relatives = [alpha_relative.as_posix(), zeta_relative.as_posix()]
            manifest = json.loads((first / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(summary["files"], 2)
            self.assertEqual(summary["records"], 2)
            self.assertEqual(
                [entry["source_path"] for entry in manifest],
                ordered_relatives,
            )
            self.assertEqual(
                sorted(path.relative_to(first).as_posix() for path in first.rglob("*.jsonl")),
                [
                    alpha_relative.as_posix(),
                    "reward-sidecars.jsonl",
                    zeta_relative.as_posix(),
                ],
            )

            expected_manifest = []
            for relative in (alpha_relative, zeta_relative):
                raw_line = (source / relative).read_bytes().split(b"\n")[0]
                converted = json.loads((first / relative).read_text(encoding="utf-8"))
                annotation = converted["reward_training"]
                expected_manifest.append(
                    {
                        "action": "retained",
                        "classification": annotation["comparability"],
                        "output_hash": hashlib.sha256(
                            curate_rewards._canonical_bytes(converted)
                        ).hexdigest(),
                        "output_id": converted["id"],
                        "reason_codes": annotation["reason_codes"],
                        "source_hash": hashlib.sha256(raw_line).hexdigest(),
                        "source_line": 1,
                        "source_path": relative.as_posix(),
                        "transform_name": "reward_ontology",
                        "transform_version": "reward-ontology-v1",
                    }
                )
            self.assertEqual(manifest, expected_manifest)

            sidecars = [
                json.loads(line)
                for line in (first / "reward-sidecars.jsonl").read_text().splitlines()
            ]
            self.assertEqual(
                [sidecar["source"]["path"] for sidecar in sidecars],
                ordered_relatives,
            )
            self.assertEqual(
                (first / "manifest.json").read_bytes(),
                (second / "manifest.json").read_bytes(),
            )
            self.assertEqual(
                (first / "reward-sidecars.jsonl").read_bytes(),
                (second / "reward-sidecars.jsonl").read_bytes(),
            )
            for relative in (alpha_relative, zeta_relative):
                self.assertEqual(
                    (first / relative).read_bytes(),
                    (second / relative).read_bytes(),
                )

            lane = {
                "order": 4,
                "bead": "sf-c5l.4",
                "transform": "reward_ontology",
                "version": curate_rewards.ONTOLOGY_VERSION,
                "outputs_dir": first,
                "manifest_path": first / "manifest.json",
                "manifest_format": "json",
                "artifacts": [
                    {
                        "kind": curate_gate.REWARD_SIDECAR_KIND,
                        "source_path": first / "reward-sidecars.jsonl",
                        "destination": Path("reward-sidecars.jsonl"),
                    }
                ],
            }
            prepared = curate_gate._prepare_lane(  # noqa: SLF001
                lane,
                curate_gate._load_source_records(source),  # noqa: SLF001
            )
            self.assertEqual(len(prepared["entries"]), 2)
            self.assertEqual(len(prepared["records"]), 2)
            self.assertEqual(prepared["artifacts"][0]["_documents"], 2)

    def test_run_conversion_copies_units_migration_and_seals_sidecar_calibration(self):
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
        record["id"] = "ffpc-r2-001"
        migration = {
            "records": [
                {
                    "scope": "batch-r02.jsonl / ffpc-r2-001 (grid)",
                    "usd_conversion_factor": 0.2,
                }
            ]
        }
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "source-run"
            write_jsonl(source / "ffpc" / "preferences.jsonl", [record])
            migration_path = root / "units-migration.json"
            migration_path.write_text(json.dumps(migration) + "\n", encoding="utf-8")
            output = root / "lane-reward"
            catalog = curate_rewards.load_units_migration(migration_path)

            curate_rewards.convert_run(
                source,
                output,
                calibration_catalog=catalog,
                units_migration=migration_path,
            )

            copied = output / curate_rewards.RUN_CALIBRATION_FILENAME
            self.assertEqual(copied.read_bytes(), migration_path.read_bytes())
            sidecar = json.loads(
                (output / curate_rewards.RUN_SIDECAR_FILENAME).read_text().splitlines()[0]
            )
            annotation = json.loads(
                (output / "ffpc" / "preferences.jsonl").read_text().splitlines()[0]
            )["reward_training"]
            self.assertEqual(annotation["comparability"], "magnitude_comparable")
            self.assertIn("external_calibration_evidence", annotation["reason_codes"])
            self.assertEqual(sidecar["calibration"]["source_unit_usd"], 2000)
            self.assertEqual(sidecar["source"]["record_id"], "ffpc-r2-001")

    def test_run_conversion_rejects_existing_symlinked_and_raw_destinations(self):
        record = {"id": "fixture", "reward_components": components(1.0)}
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "source-run"
            write_jsonl(source / "factory-a/batch.jsonl", [record])

            existing = root / "existing-lane"
            existing.mkdir()
            marker = existing / "keep.txt"
            marker.write_text("untouched", encoding="utf-8")
            with self.assertRaisesRegex(
                curate_rewards.RewardOntologyError,
                "refusing to overwrite existing run destination",
            ):
                curate_rewards.convert_run(source, existing)
            self.assertEqual(marker.read_text(encoding="utf-8"), "untouched")

            symlink_target = root / "symlink-target"
            symlink_target.mkdir()
            symlink_destination = root / "symlink-lane"
            symlink_destination.symlink_to(symlink_target, target_is_directory=True)
            with self.assertRaisesRegex(
                curate_rewards.RewardOntologyError,
                "symlinked path component",
            ):
                curate_rewards.convert_run(source, symlink_destination)
            self.assertEqual(list(symlink_target.iterdir()), [])

            raw_destination = root / "outputs" / "raw" / "reward-lane"
            raw_destination.parent.mkdir(parents=True)
            with self.assertRaisesRegex(
                curate_rewards.RewardOntologyError,
                "immutable outputs/raw",
            ):
                curate_rewards.convert_run(source, raw_destination)
            self.assertFalse(raw_destination.exists())

    def test_run_conversion_cleans_partial_tree_after_later_file_failure(self):
        record = {"id": "valid-first", "reward_components": components(1.0)}
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "source-run"
            valid_source = source / "alpha-factory/batch.jsonl"
            invalid_source = source / "zeta-factory/batch.jsonl"
            write_jsonl(valid_source, [record])
            invalid_source.parent.mkdir(parents=True)
            invalid_source.write_text('{"id": "invalid"\n', encoding="utf-8")
            destination = root / "lane-reward"

            with self.assertRaisesRegex(
                curate_rewards.RewardOntologyError,
                "invalid JSON",
            ):
                curate_rewards.convert_run(source, destination)

            self.assertFalse(destination.exists())
            self.assertEqual(
                json.loads(valid_source.read_text(encoding="utf-8")),
                record,
            )

    def test_migration_bytes_and_run_cli_use_catalog_record_key(self):
        payload = json.dumps(
            {
                "records": [
                    {
                        "scope": "batch-r02.jsonl / ffpc-r2-001 (grid)",
                        "usd_conversion_factor": 0.2,
                    }
                ]
            }
        ).encode("utf-8")
        catalog = curate_rewards.load_units_migration_bytes(payload)
        key = curate_rewards.catalog_record_key("FFPC-R2-001")
        self.assertEqual(key, "ffpc-r2-001")
        self.assertEqual(set(catalog), {key})
        self.assertEqual(catalog[key]["canonical_factor"], 0.2)

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "source-run"
            write_jsonl(
                source / "alpha-factory/batch.jsonl",
                [{"id": "cli-reward", "reward_components": components(1.0)}],
            )
            output = root / "lane-reward"
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                code = curate_rewards.main(["run", str(source), str(output)])
            self.assertEqual(code, 0)
            self.assertEqual(json.loads(stdout.getvalue())["records"], 1)

            empty = root / "empty-run"
            empty.mkdir()
            (empty / "blank.jsonl").write_text("", encoding="utf-8")
            with self.assertRaisesRegex(
                curate_rewards.RewardOntologyError, "holds no JSONL records"
            ):
                curate_rewards.convert_run(empty, root / "out-empty")

            reserved = source / curate_rewards.RUN_SIDECAR_FILENAME
            reserved.write_text("{}\n", encoding="utf-8")
            with self.assertRaisesRegex(
                curate_rewards.RewardOntologyError, "aggregate sidecar"
            ):
                curate_rewards.convert_run(source, root / "out-reserved")


FIXTURES = REPO / "tests" / "fixtures" / "reward-ontology"
MAPPING = REPO / "schemas" / "reward-ontology-v1.mapping.json"


def _raw_run_dir():
    """Locate the gitignored 2026-08-17 run, which a worktree leaves upstream."""
    candidates = [REPO, *list(REPO.parents)[:3]]
    for base in candidates:
        candidate = base / "outputs" / "raw" / "2026-08-17"
        if candidate.is_dir():
            return candidate
    return REPO / "outputs" / "raw" / "2026-08-17"


RAW_RUN = _raw_run_dir()

# Pinned so a fixture edit has to be deliberate: the per-line decision table
# below is only evidence while these bytes are the bytes it was derived from.
FIXTURE_SHA256 = {
    "bridge-pairs.jsonl":
        "7ee2bb2ee58d60daa164a7408285b984518843a1ec456408c86dda0a7932738a",
    "coding-episodes.jsonl":
        "77f38e312388338b659c4e4e9d25d679f0f0e989188aad0772367509ff109ddb",
    "ffpc-preferences.jsonl":
        "a1b29353a63ce5ae56484795ad3641c9bc2f1bfa062b7882b442b5c5ce1c6876",
    "swarm-trajectories.jsonl":
        "e886ee80ab94525727df281944fc4e633b227885bab94defcd45e7a37cb49e00",
    "thalamic-trajectories.jsonl":
        "7e56fe052633dc7cc14658be56d2f4b68a6437af063b3bea2096f9e550067944",
}

MAGNITUDE = "magnitude_comparable"
ORDER_ONLY = "sign_order_only"
EXCLUDED = "exclude_from_reward_training"

# (file, 1-indexed line) -> (rule id, comparability, reason codes)
FIXTURE_DECISIONS = {
    ("ffpc-preferences.jsonl", 1): (
        "P05", MAGNITUDE,
        ["preference_order_verified", "reward_arithmetic_verified",
         "explicit_usd_unit_calibration"],
    ),
    ("ffpc-preferences.jsonl", 2): (
        "P05", MAGNITUDE,
        ["preference_order_verified", "reward_arithmetic_verified",
         "explicit_usd_unit_calibration"],
    ),
    ("ffpc-preferences.jsonl", 3): (
        "P07", ORDER_ONLY,
        ["preference_order_verified", "magnitude_calibration_incomplete"],
    ),
    ("ffpc-preferences.jsonl", 4): (
        "P08", ORDER_ONLY,
        ["preference_order_verified", "magnitude_calibration_missing"],
    ),
    ("ffpc-preferences.jsonl", 5): (
        "P06", ORDER_ONLY,
        ["preference_order_verified", "magnitude_calibration_conflict"],
    ),
    ("ffpc-preferences.jsonl", 6): (
        "P04", EXCLUDED, ["reward_order_conflicts_with_preference"],
    ),
    ("ffpc-preferences.jsonl", 7): (
        "P02", EXCLUDED, ["reward_arithmetic_mismatch"],
    ),
    ("ffpc-preferences.jsonl", 8): (
        "P03", EXCLUDED, ["unsupported_reward_layout"],
    ),
    ("ffpc-preferences.jsonl", 9): (
        "P01", EXCLUDED, ["ambiguous_preference_reward_scopes"],
    ),
    ("thalamic-trajectories.jsonl", 1): (
        "S07", EXCLUDED, ["magnitude_calibration_missing"],
    ),
    ("thalamic-trajectories.jsonl", 2): (
        "S08", MAGNITUDE,
        ["reward_arithmetic_verified", "explicit_usd_unit_calibration"],
    ),
    ("thalamic-trajectories.jsonl", 3): (
        "S06", EXCLUDED, ["magnitude_semantics_missing"],
    ),
    ("thalamic-trajectories.jsonl", 4): (
        "S05", EXCLUDED, ["magnitude_calibration_conflict"],
    ),
    ("thalamic-trajectories.jsonl", 5): (
        "S03", EXCLUDED, ["reward_arithmetic_mismatch"],
    ),
    ("thalamic-trajectories.jsonl", 6): (
        "S07", EXCLUDED, ["magnitude_calibration_missing"],
    ),
    ("thalamic-trajectories.jsonl", 7): (
        "S04", EXCLUDED, ["unsupported_reward_layout"],
    ),
    ("thalamic-trajectories.jsonl", 8): (
        "S04", EXCLUDED, ["unsupported_reward_layout"],
    ),
    ("swarm-trajectories.jsonl", 1): (
        "S07", EXCLUDED, ["magnitude_calibration_missing"],
    ),
    ("swarm-trajectories.jsonl", 2): (
        "S07", EXCLUDED, ["magnitude_calibration_missing"],
    ),
    ("swarm-trajectories.jsonl", 3): (
        "S01", EXCLUDED, ["multiple_reward_scopes"],
    ),
    ("swarm-trajectories.jsonl", 4): (
        "S04", EXCLUDED, ["unsupported_reward_layout"],
    ),
    ("swarm-trajectories.jsonl", 5): (
        "S04", EXCLUDED, ["unsupported_reward_layout"],
    ),
    ("bridge-pairs.jsonl", 1): (
        "S02", EXCLUDED, ["noncanonical_reward_scope"],
    ),
    ("bridge-pairs.jsonl", 2): (
        "S01", EXCLUDED, ["multiple_reward_scopes"],
    ),
    ("coding-episodes.jsonl", 1): (
        "S07", EXCLUDED, ["magnitude_calibration_missing"],
    ),
    ("coding-episodes.jsonl", 2): (
        "S02", EXCLUDED, ["noncanonical_reward_scope"],
    ),
    ("coding-episodes.jsonl", 3): (
        "S01", EXCLUDED, ["multiple_reward_scopes"],
    ),
    ("coding-episodes.jsonl", 4): (
        "R00", EXCLUDED, ["no_source_reward"],
    ),
}


def fixture_records(name):
    path = FIXTURES / name
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if line.strip():
            yield line_number, json.loads(line)


def all_fixture_records():
    for name in sorted(FIXTURE_SHA256):
        for line_number, record in fixture_records(name):
            yield name, line_number, record


class ConversionPolicyMappingTests(unittest.TestCase):
    """The mapping is the policy, not a description of it."""

    def test_module_policy_tables_come_from_the_mapping(self):
        document = json.loads(MAPPING.read_text(encoding="utf-8"))
        self.assertEqual(document, curate_rewards.CONVERSION_POLICY)
        policy = document["policy"]
        arithmetic = policy["arithmetic"]
        conversion = policy["conversion"]

        self.assertEqual(curate_rewards.ANNOTATION_FIELD, policy["annotation_field"])
        self.assertEqual(
            curate_rewards.REWARD_KEYS, frozenset(policy["reward_keys"])
        )
        self.assertEqual(curate_rewards.CANONICAL_SCOPE, policy["canonical_scope"])
        self.assertEqual(
            curate_rewards.PREFERENCE_POINTERS,
            (policy["preference_scope"]["preferred"],
             policy["preference_scope"]["dispreferred"]),
        )
        self.assertEqual(
            curate_rewards.WEIGHTED_CONTAINERS, tuple(arithmetic["weighted_containers"])
        )
        self.assertEqual(
            curate_rewards.WEIGHT_ALIASES,
            {name: tuple(group) for name, group in arithmetic["weight_aliases"].items()},
        )
        self.assertEqual(
            curate_rewards.UNWEIGHTED_EXCLUDE,
            frozenset(
                key
                for group in arithmetic["non_component_keys"].values()
                for key in group
            ),
        )
        self.assertEqual(curate_rewards.CANONICAL_UNIT, conversion["canonical_unit"])
        self.assertEqual(
            float(curate_rewards.CANONICAL_UNIT_USD), conversion["canonical_unit_usd"]
        )
        self.assertEqual(
            curate_rewards.USD_UNIT_RE.pattern, conversion["usd_unit_pattern"]
        )
        self.assertEqual(
            curate_rewards.REASON_CODES, frozenset(policy["reason_codes"])
        )

    def test_policy_document_validates_through_the_ontology_validator(self):
        document = json.loads(MAPPING.read_text(encoding="utf-8"))
        self.assertIs(
            curate_rewards.validate_ontology_document(document), document
        )
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        branches = {branch["$ref"] for branch in schema["oneOf"]}
        self.assertIn("#/$defs/conversionPolicy", branches)
        self.assertEqual(
            schema["$defs"]["conversionPolicy"]["properties"]["document_type"]["const"],
            "reward_conversion_policy",
        )
        conversion_schema = schema["$defs"]["conversionPolicy"]["properties"][
            "policy"
        ]["properties"]["conversion"]
        self.assertTrue(
            {
                "canonical_unit",
                "canonical_unit_usd",
                "aggregation",
                "required_semantics_substring",
                "structured_unit_field",
                "text_unit_field",
                "usd_unit_pattern",
                "external_calibration",
            }
            <= set(conversion_schema["required"])
        )
        self.assertEqual(
            set(conversion_schema["properties"]["external_calibration"]["required"]),
            {"record_id_pattern", "factor_field", "scope_field"},
        )

    def test_schema_declares_the_runtime_policy_and_census_contracts(self):
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        conversion_policy = schema["$defs"]["conversionPolicy"]
        policy_schema = conversion_policy["properties"]["policy"]
        self.assertIn("arithmetic", policy_schema["required"])
        self.assertEqual(
            policy_schema["properties"]["arithmetic"]["$ref"],
            "#/$defs/policyArithmetic",
        )
        arithmetic_required = set(schema["$defs"]["policyArithmetic"]["required"])
        self.assertTrue(
            {
                "default_tolerance",
                "declared_total_field",
                "weights_field",
                "rounding_decimals_field",
                "rounding_declaration_pattern",
                "rounding_declaration_fields",
                "nested_component_key",
                "weighted_containers",
                "weight_aliases",
                "non_component_keys",
                "methods",
            }
            <= arithmetic_required
        )
        expected = conversion_policy["properties"]["expected_classification"]
        self.assertIn("by_factory", expected["required"])
        vocabulary_required = set(
            conversion_policy["properties"]["source_vocabulary"]["required"]
        )
        self.assertTrue({"scope_keys", "arithmetic"} <= vocabulary_required)
        self.assertEqual(
            set(expected["properties"]["by_factory"]["additionalProperties"]["required"]),
            {"records", "comparability", "reason_codes"},
        )

    def test_schema_constrains_the_runtime_policy_routing_fields(self):
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        properties = schema["$defs"]["conversionPolicy"]["properties"][
            "policy"
        ]["properties"]

        self.assertEqual(properties["annotation_field"]["type"], "string")
        self.assertEqual(properties["annotation_field"]["minLength"], 1)
        self.assertEqual(properties["reward_keys"]["type"], "array")
        self.assertTrue(properties["reward_keys"]["uniqueItems"])
        self.assertEqual(
            properties["reward_keys"]["items"],
            {"type": "string", "minLength": 1},
        )
        self.assertEqual(properties["canonical_scope"]["pattern"], "^/.+")
        preference = properties["preference_scope"]
        self.assertEqual(
            set(preference["required"]),
            {"preferred", "dispreferred", "relation"},
        )
        self.assertEqual(
            preference["properties"]["relation"]["const"],
            "preferred_gt_dispreferred",
        )
        for side in ("preferred", "dispreferred"):
            self.assertEqual(
                preference["properties"][side],
                {"type": "string", "pattern": "^/.+"},
            )
        classes = properties["comparability_classes"]
        self.assertEqual(
            set(classes["required"]),
            {
                "magnitude_comparable",
                "sign_order_only",
                "exclude_from_reward_training",
            },
        )
        self.assertEqual(classes["minProperties"], 3)
        dispositions = properties["component_dispositions"]
        self.assertEqual(len(dispositions["required"]), 7)
        self.assertEqual(dispositions["minProperties"], 7)

    def test_every_declared_reason_code_is_cited_by_a_declared_rule(self):
        policy = curate_rewards.CONVERSION_POLICY["policy"]
        cited = set()
        for rule in policy["comparability_rules"]:
            cited.update(rule["reason_codes"])
            cited.update(rule.get("optional_reason_codes", ()))
        self.assertEqual(cited, set(policy["reason_codes"]))

    def test_a_broken_policy_is_refused_rather_than_silently_defaulted(self):
        document = json.loads(MAPPING.read_text(encoding="utf-8"))

        cases = {
            "unknown conversion policy document_type": ("document_type", "nonsense"),
            "unknown reward mapping version": ("mapping_version", "reward-mapping-v9"),
            "unknown reward ontology version": ("ontology_version", "reward-ontology-v9"),
        }
        for expected, (field, value) in cases.items():
            broken = copy.deepcopy(document)
            broken[field] = value
            with self.assertRaisesRegex(
                curate_rewards.RewardOntologyError, expected
            ):
                curate_rewards.validate_conversion_policy(broken)

        orphan = copy.deepcopy(document)
        orphan["policy"]["reason_codes"]["never_emitted"] = "orphan code"
        with self.assertRaisesRegex(
            curate_rewards.RewardOntologyError, "cited by no rule"
        ):
            curate_rewards.validate_conversion_policy(orphan)

        uncatalogued = copy.deepcopy(document)
        uncatalogued["policy"]["comparability_rules"][0]["reason_codes"] = ["invented"]
        with self.assertRaisesRegex(
            curate_rewards.RewardOntologyError, "uncatalogued reason codes"
        ):
            curate_rewards.validate_conversion_policy(uncatalogued)

        duplicate = copy.deepcopy(document)
        duplicate["policy"]["comparability_rules"].append(
            copy.deepcopy(duplicate["policy"]["comparability_rules"][0])
        )
        with self.assertRaisesRegex(
            curate_rewards.RewardOntologyError, "duplicate comparability rule id"
        ):
            curate_rewards.validate_conversion_policy(duplicate)

        stray_weight = copy.deepcopy(document)
        stray_weight["policy"]["arithmetic"]["weights_field"] = "task_progress"
        with self.assertRaisesRegex(
            curate_rewards.RewardOntologyError, "declared unit_calibration key"
        ):
            curate_rewards.validate_conversion_policy(stray_weight)

        stray_container = copy.deepcopy(document)
        stray_container["policy"]["arithmetic"]["nested_component_key"] = "not_declared"
        with self.assertRaisesRegex(
            curate_rewards.RewardOntologyError, "declared weighted container"
        ):
            curate_rewards.validate_conversion_policy(stray_container)

        bad_pattern = copy.deepcopy(document)
        bad_pattern["policy"]["conversion"]["usd_unit_pattern"] = "([0-9]"
        with self.assertRaisesRegex(
            curate_rewards.RewardOntologyError, "not a valid regular expression"
        ):
            curate_rewards.validate_conversion_policy(bad_pattern)

        bad_tolerance = copy.deepcopy(document)
        bad_tolerance["policy"]["arithmetic"]["default_tolerance"] = 0
        with self.assertRaisesRegex(
            curate_rewards.RewardOntologyError, "must be positive and finite"
        ):
            curate_rewards.validate_conversion_policy(bad_tolerance)

        missing_vocabulary = copy.deepcopy(document)
        missing_vocabulary.pop("source_vocabulary")
        with self.assertRaisesRegex(
            curate_rewards.RewardOntologyError, "source_vocabulary"
        ):
            curate_rewards.validate_conversion_policy(missing_vocabulary)

        empty_vocabulary = copy.deepcopy(document)
        empty_vocabulary["source_vocabulary"] = {}
        with self.assertRaisesRegex(
            curate_rewards.RewardOntologyError, "source_vocabulary"
        ):
            curate_rewards.validate_conversion_policy(empty_vocabulary)

        wrong_key_count = copy.deepcopy(document)
        wrong_key_count["source_vocabulary"]["unique_component_keys"] -= 1
        with self.assertRaisesRegex(
            curate_rewards.RewardOntologyError, "unique_component_keys"
        ):
            curate_rewards.validate_conversion_policy(wrong_key_count)

        wrong_disposition = copy.deepcopy(document)
        wrong_disposition["source_vocabulary"]["component_keys"][
            "task_progress"
        ]["disposition"] = "narrative_annotation"
        with self.assertRaisesRegex(
            curate_rewards.RewardOntologyError, "disposition must be"
        ):
            curate_rewards.validate_conversion_policy(wrong_disposition)

        overlapping_aliases = copy.deepcopy(document)
        overlapping_aliases["policy"]["arithmetic"]["weight_aliases"]["safety"] = [
            "safety",
            "task_progress",
        ]
        with self.assertRaisesRegex(
            curate_rewards.RewardOntologyError, "weight alias groups must be disjoint"
        ):
            curate_rewards.validate_conversion_policy(overlapping_aliases)

        annotation_collision = copy.deepcopy(document)
        annotation_collision["policy"]["annotation_field"] = "reward_components"
        with self.assertRaisesRegex(
            curate_rewards.RewardOntologyError, "must not be a declared reward key"
        ):
            curate_rewards.validate_conversion_policy(annotation_collision)

        bad_preference = copy.deepcopy(document)
        bad_preference["policy"]["preference_scope"]["preferred"] = "/chosen/not_reward"
        with self.assertRaisesRegex(
            curate_rewards.RewardOntologyError, "must target a declared reward key"
        ):
            curate_rewards.validate_conversion_policy(bad_preference)

        shared_unit_fields = copy.deepcopy(document)
        shared_unit_fields["policy"]["conversion"]["text_unit_field"] = (
            shared_unit_fields["policy"]["conversion"]["structured_unit_field"]
        )
        with self.assertRaisesRegex(
            curate_rewards.RewardOntologyError,
            "structured and textual unit fields must be distinct",
        ):
            curate_rewards.validate_conversion_policy(shared_unit_fields)

        shared_calibration_fields = copy.deepcopy(document)
        shared_calibration_fields["policy"]["conversion"]["external_calibration"][
            "scope_field"
        ] = shared_calibration_fields["policy"]["conversion"]["external_calibration"][
            "factor_field"
        ]
        with self.assertRaisesRegex(
            curate_rewards.RewardOntologyError,
            "external calibration fields must be distinct",
        ):
            curate_rewards.validate_conversion_policy(shared_calibration_fields)

        nonnumeric_pattern = copy.deepcopy(document)
        nonnumeric_pattern["policy"]["arithmetic"][
            "rounding_declaration_pattern"
        ] = "(abc)"
        with self.assertRaisesRegex(
            curate_rewards.RewardOntologyError, "capture group must be numeric"
        ):
            curate_rewards.validate_conversion_policy(nonnumeric_pattern)

        foreign_unit = copy.deepcopy(document)
        foreign_unit["policy"]["conversion"]["canonical_unit"] = "eur"
        with self.assertRaisesRegex(
            curate_rewards.RewardOntologyError,
            "canonical_unit must match the annotation schema constant",
        ):
            curate_rewards.validate_conversion_policy(foreign_unit)

        impossible_pair = copy.deepcopy(document)
        impossible_pair["source_vocabulary"]["shapes"][0][
            "arithmetic_status"
        ] = "unsupported"
        with self.assertRaisesRegex(
            curate_rewards.RewardOntologyError,
            "incompatible with method",
        ):
            curate_rewards.validate_conversion_policy(impossible_pair)

        stale_occurrences = copy.deepcopy(document)
        stale_occurrences["source_vocabulary"]["shapes"][0]["occurrences"] = 999999
        with self.assertRaisesRegex(
            curate_rewards.RewardOntologyError,
            "shape occurrences must sum to reward_instances",
        ):
            curate_rewards.validate_conversion_policy(stale_occurrences)

    def test_missing_or_invalid_mapping_file_is_a_loud_failure(self):
        with tempfile.TemporaryDirectory() as td:
            missing = Path(td) / "absent.json"
            with self.assertRaisesRegex(
                curate_rewards.RewardOntologyError, "conversion policy is unreadable"
            ):
                curate_rewards.load_conversion_policy(missing)

            garbage = Path(td) / "garbage.json"
            garbage.write_text("{not json", encoding="utf-8")
            with self.assertRaisesRegex(
                curate_rewards.RewardOntologyError, "invalid conversion policy JSON"
            ):
                curate_rewards.load_conversion_policy(garbage)

    def test_an_undeclared_verdict_cannot_be_emitted(self):
        with self.assertRaisesRegex(
            curate_rewards.RewardOntologyError, "undeclared comparability rule"
        ):
            curate_rewards.comparability_rule("Z99")
        with self.assertRaisesRegex(
            curate_rewards.RewardOntologyError, "declares exclude_from_reward_training"
        ):
            curate_rewards._require_declared_rule(
                curate_rewards.MAGNITUDE_COMPARABLE, ["no_source_reward"], "R00"
            )
        with self.assertRaisesRegex(
            curate_rewards.RewardOntologyError, "declares reason codes"
        ):
            curate_rewards._require_declared_rule(
                curate_rewards.EXCLUDE, ["multiple_reward_scopes"], "R00"
            )

    def test_policy_requires_every_runtime_classification_rule_id(self):
        document = copy.deepcopy(curate_rewards.CONVERSION_POLICY)
        r00 = next(
            rule
            for rule in document["policy"]["comparability_rules"]
            if rule["id"] == "R00"
        )
        r00["id"] = "renamed-R00"

        with self.assertRaisesRegex(
            curate_rewards.RewardOntologyError,
            "missing runtime-required ids.*R00",
        ):
            curate_rewards.validate_conversion_policy(document)

    def test_comparability_rule_returns_a_defensive_copy(self):
        stored = next(
            rule for rule in curate_rewards.COMPARABILITY_RULES if rule["id"] == "S08"
        )
        original = copy.deepcopy(stored)
        try:
            exposed = curate_rewards.comparability_rule("S08")
            exposed["comparability"] = curate_rewards.SIGN_ORDER_ONLY
            exposed["reason_codes"].append("no_source_reward")
            self.assertEqual(curate_rewards.comparability_rule("S08"), original)
            self.assertEqual(stored, original)
        finally:
            stored.clear()
            stored.update(original)

    def test_classification_verdicts_are_read_from_the_matched_rule(self):
        rules = copy.deepcopy(list(curate_rewards.COMPARABILITY_RULES))
        p01 = next(rule for rule in rules if rule["id"] == "P01")
        p01["comparability"] = curate_rewards.SIGN_ORDER_ONLY
        p01["reason_codes"] = ["magnitude_calibration_missing"]
        source_rewards = [
            {
                "json_pointer": curate_rewards.PREFERENCE_POINTERS[0],
                "value_sha256": "sha256:" + "0" * 64,
                "value": {"total": 1.0},
            }
        ]

        original = curate_rewards.COMPARABILITY_RULES
        try:
            curate_rewards.COMPARABILITY_RULES = tuple(rules)
            verdict = curate_rewards._classify(source_rewards, [])
        finally:
            curate_rewards.COMPARABILITY_RULES = original
        self.assertEqual(
            verdict,
            (
                curate_rewards.SIGN_ORDER_ONLY,
                ["magnitude_calibration_missing"],
                None,
                "P01",
            ),
        )


class SourceVocabularyMappingTests(unittest.TestCase):
    """The frozen 510-key / 140-shape mapping is checkable without the raw run."""

    def setUp(self):
        self.vocabulary = curate_rewards.CONVERSION_POLICY["source_vocabulary"]

    def test_the_mapping_covers_the_five_hundred_ten_keys_and_hundred_forty_shapes(self):
        self.assertEqual(self.vocabulary["run"], "2026-08-17")
        self.assertEqual(self.vocabulary["unique_component_keys"], 510)
        self.assertEqual(self.vocabulary["unique_shapes"], 140)
        self.assertEqual(len(self.vocabulary["component_keys"]), 510)
        self.assertEqual(len(self.vocabulary["shapes"]), 140)
        self.assertEqual(
            sum(self.vocabulary["dispositions"].values()),
            self.vocabulary["unique_component_keys"],
        )

    def test_every_recorded_disposition_follows_the_declared_rules(self):
        recorded = collections.Counter()
        for key, entry in self.vocabulary["component_keys"].items():
            expected = curate_rewards.disposition_for_observed_types(
                key, entry["observed_types"]
            )
            self.assertEqual(
                entry["disposition"],
                expected,
                f"{key} is mapped as {entry['disposition']}, not {expected}",
            )
            self.assertIn(entry["disposition"], curate_rewards.COMPONENT_DISPOSITIONS)
            recorded[entry["disposition"]] += 1
        self.assertEqual(dict(recorded), self.vocabulary["dispositions"])

    def test_no_narrative_or_structural_key_is_mapped_as_a_magnitude_term(self):
        for key, entry in self.vocabulary["component_keys"].items():
            if entry["disposition"] != curate_rewards.DISPOSITION_MAGNITUDE_TERM:
                continue
            self.assertNotIn(key, curate_rewards.UNWEIGHTED_EXCLUDE)
            self.assertTrue(
                set(entry["observed_types"]) <= {"number", "value-object"},
                f"{key} is a magnitude term but was observed as "
                f"{entry['observed_types']}",
            )

    def test_every_shape_selects_the_arithmetic_branch_its_signature_implies(self):
        for row in self.vocabulary["shapes"]:
            members = dict(
                part.split(":", 1) for part in row["signature"].split("|") if ":" in part
            )
            method = row["arithmetic_method"]
            self.assertIn(method, curate_rewards.ARITHMETIC_METHODS)
            self.assertIn(row["arithmetic_status"], curate_rewards.ARITHMETIC_STATUSES)
            total = members.get(curate_rewards.DECLARED_TOTAL_KEY)
            if total not in {"int", "float"}:
                self.assertEqual(method, "no_numeric_total", row["signature"])
                continue
            if curate_rewards.WEIGHTS_FIELD in members:
                self.assertTrue(
                    method.startswith("declared_weighted_sum"), row["signature"]
                )
            else:
                self.assertTrue(
                    method.startswith("unweighted_component_sum"), row["signature"]
                )

    def test_policy_rejects_shape_methods_incompatible_with_the_signature(self):
        document = curate_rewards.CONVERSION_POLICY
        cases = []
        for expected_method, incompatible_method in (
            ("no_numeric_total", "declared_weighted_sum"),
            ("declared_weighted_sum", "unweighted_component_sum"),
            ("unweighted_component_sum", "declared_weighted_sum"),
        ):
            shape = next(
                copy.deepcopy(row)
                for row in document["source_vocabulary"]["shapes"]
                if row.get("arithmetic_method") == expected_method
            )
            shape["arithmetic_method"] = incompatible_method
            cases.append((expected_method, shape))

        for name, shape in cases:
            with self.subTest(name=name):
                malformed = copy.deepcopy(document)
                index = next(
                    index
                    for index, row in enumerate(
                        malformed["source_vocabulary"]["shapes"]
                    )
                    if row["signature"] == shape["signature"]
                )
                malformed["source_vocabulary"]["shapes"][index] = shape
                with self.assertRaisesRegex(
                    curate_rewards.RewardOntologyError,
                    "incompatible with signature",
                ):
                    curate_rewards.validate_conversion_policy(malformed)

    def test_census_emits_and_policy_accepts_plural_arithmetic_outcomes(self):
        census = curate_rewards.reward_census(
            [
                {
                    "reward_components": {
                        "review_probe_component": 1.0,
                        "total": 1.0,
                    }
                },
                {
                    "reward_components": {
                        "review_probe_component": 1.0,
                        "total": 2.0,
                    }
                },
            ]
        )
        self.assertEqual(len(census["shapes"]), 1)
        shape = census["shapes"][0]
        self.assertNotIn("arithmetic_status", shape)
        self.assertNotIn("arithmetic_method", shape)
        self.assertEqual(
            shape["arithmetic_outcomes"],
            [
                {"status": "invalid", "method": "unweighted_component_sum"},
                {"status": "valid", "method": "unweighted_component_sum"},
            ],
        )

        document = copy.deepcopy(curate_rewards.CONVERSION_POLICY)
        document["source_vocabulary"]["shapes"][0] = shape
        document["source_vocabulary"]["reward_instances"] = sum(
            item["occurrences"] for item in document["source_vocabulary"]["shapes"]
        )
        document["source_vocabulary"]["arithmetic"] = [
            {
                "status": "valid",
                "method": "unweighted_component_sum",
                "occurrences": document["source_vocabulary"]["reward_instances"],
            }
        ]
        self.assertIs(curate_rewards.validate_conversion_policy(document), document)

    def test_malformed_shape_arithmetic_outcomes_are_refused(self):
        document = curate_rewards.CONVERSION_POLICY
        base_shape = copy.deepcopy(document["source_vocabulary"]["shapes"][0])
        outcome = {
            "status": base_shape["arithmetic_status"],
            "method": base_shape["arithmetic_method"],
        }
        cases = {
            "singular and plural": (
                {**base_shape, "arithmetic_outcomes": [outcome]},
                "exactly one",
            ),
            "half singular": (
                {key: value for key, value in base_shape.items()
                 if key != "arithmetic_method"},
                "arithmetic_method",
            ),
            "empty plural": (
                {
                    "signature": base_shape["signature"],
                    "occurrences": base_shape["occurrences"],
                    "arithmetic_outcomes": [],
                },
                "nonempty list",
            ),
            "duplicate plural": (
                {
                    "signature": base_shape["signature"],
                    "occurrences": base_shape["occurrences"],
                    "arithmetic_outcomes": [outcome, copy.deepcopy(outcome)],
                },
                "duplicate arithmetic outcome",
            ),
        }
        for name, (shape, message) in cases.items():
            with self.subTest(name=name):
                malformed = copy.deepcopy(document)
                malformed["source_vocabulary"]["shapes"][0] = shape
                with self.assertRaisesRegex(
                    curate_rewards.RewardOntologyError, message
                ):
                    curate_rewards.validate_conversion_policy(malformed)

    def test_by_factory_census_must_reconcile_with_global_counts(self):
        document = curate_rewards.CONVERSION_POLICY
        factory = "agentic-coding-trajectory-factory"

        wrong_records = copy.deepcopy(document)
        entry = wrong_records["expected_classification"]["by_factory"][factory]
        entry["records"] += 1
        entry["comparability"]["exclude_from_reward_training"] += 1
        with self.assertRaisesRegex(
            curate_rewards.RewardOntologyError,
            "by_factory records must sum to records",
        ):
            curate_rewards.validate_conversion_policy(wrong_records)

        wrong_classes = copy.deepcopy(document)
        entry = wrong_classes["expected_classification"]["by_factory"][factory]
        entry["comparability"]["exclude_from_reward_training"] -= 1
        entry["comparability"]["sign_order_only"] = 1
        with self.assertRaisesRegex(
            curate_rewards.RewardOntologyError,
            "by_factory comparability counts must match",
        ):
            curate_rewards.validate_conversion_policy(wrong_classes)

        wrong_reasons = copy.deepcopy(document)
        entry = wrong_reasons["expected_classification"]["by_factory"][factory]
        entry["reason_codes"]["magnitude_calibration_missing"] -= 1
        entry["reason_codes"]["explicit_usd_unit_calibration"] = 1
        with self.assertRaisesRegex(
            curate_rewards.RewardOntologyError,
            "by_factory reason-code counts must match",
        ):
            curate_rewards.validate_conversion_policy(wrong_reasons)

    def test_the_frozen_classification_census_is_internally_consistent(self):
        expected = curate_rewards.CONVERSION_POLICY["expected_classification"]
        self.assertEqual(expected["run"], "2026-08-17")
        self.assertEqual(sum(expected["comparability"].values()), expected["records"])
        self.assertTrue(
            set(expected["comparability"]) <= curate_rewards.COMPARABILITY_CLASSES
        )
        self.assertTrue(set(expected["reason_codes"]) <= curate_rewards.REASON_CODES)
        by_factory = expected["by_factory"]
        self.assertEqual(
            sum(entry["records"] for entry in by_factory.values()), expected["records"]
        )
        rolled = collections.Counter()
        for entry in by_factory.values():
            rolled.update(entry["comparability"])
        self.assertEqual(dict(rolled), expected["comparability"])
        self.assertEqual(
            expected["comparability"],
            {
                "exclude_from_reward_training": 153,
                "magnitude_comparable": 34,
                "sign_order_only": 8,
            },
        )


class RewardShapeVocabularyTests(unittest.TestCase):
    def test_reward_signature_matches_the_training_audits_shape_vocabulary(self):
        import training_audit

        seen = 0
        for _name, _line, record in all_fixture_records():
            for _path, reward in training_audit.walk_key(record, "reward_components"):
                seen += 1
                self.assertEqual(
                    curate_rewards.reward_signature(reward),
                    training_audit.reward_shape(reward),
                )
        self.assertGreater(seen, 0)

    def test_disposition_and_summation_never_disagree(self):
        probes = [
            ("task_progress", 0.5),
            ("task_progress", {"value": 0.5, "note": "rich"}),
            ("task_progress", {"note": "no numeric value"}),
            ("task_progress", "0.5"),
            ("task_progress", True),
            ("task_progress", None),
            ("task_progress", [0.5]),
            ("components", {"task": 0.5}),
            ("components", 0.5),
            ("actual", {"task": 0.5}),
            ("summary", {"note": "text"}),
            ("total", 1.0),
            ("unit_usd", 20000),
            ("rounding_decimals", 4),
            ("notes", "free text"),
            ("weights", {"task": 1.0}),
        ]
        for key, value in probes:
            disposition = curate_rewards.component_disposition(key, value)
            self.assertEqual(
                disposition == curate_rewards.DISPOSITION_MAGNITUDE_TERM,
                curate_rewards.contributes_to_total(key, value),
                f"{key}={value!r} is {disposition}",
            )

    def test_an_unseen_key_is_never_promoted_to_a_magnitude_term(self):
        self.assertEqual(
            curate_rewards.component_disposition("never_seen_in_any_run"),
            curate_rewards.DISPOSITION_AMBIGUOUS,
        )
        self.assertEqual(
            curate_rewards.component_disposition("task_progress"),
            curate_rewards.DISPOSITION_MAGNITUDE_TERM,
        )
        self.assertEqual(
            curate_rewards.component_disposition("total"),
            curate_rewards.DISPOSITION_DECLARED_TOTAL,
        )

    def test_nonfinite_values_are_never_numeric_magnitude_terms(self):
        for value in (float("nan"), float("inf"), float("-inf")):
            self.assertEqual(curate_rewards.value_type(value), "unknown")
            self.assertEqual(
                curate_rewards.component_disposition("new_component", value),
                curate_rewards.DISPOSITION_AMBIGUOUS,
            )
            self.assertFalse(
                curate_rewards.contributes_to_total("new_component", value)
            )
            self.assertEqual(
                curate_rewards.value_type({"value": value}), "object"
            )

    def test_jsonl_loader_rejects_nonfinite_numeric_constants(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "nonfinite.jsonl"
            path.write_text('{"reward_components":{"total":NaN}}\n', encoding="utf-8")
            with self.assertRaisesRegex(
                curate_rewards.RewardOntologyError,
                r"non-standard JSON numeric constant NaN",
            ):
                list(curate_rewards._load_jsonl(path))


class RewardOntologyFixtureRegression(unittest.TestCase):
    """Bind the mapped layout families to deterministic ontology decisions."""

    def test_fixture_bytes_are_pinned(self):
        for name, digest in FIXTURE_SHA256.items():
            data = (FIXTURES / name).read_bytes()
            self.assertEqual(
                hashlib.sha256(data).hexdigest(),
                digest,
                f"{name} changed; re-derive FIXTURE_DECISIONS before repinning",
            )

    def test_every_fixture_line_maps_to_its_declared_rule(self):
        seen = set()
        for name, line_number, record in all_fixture_records():
            key = (name, line_number)
            self.assertIn(key, FIXTURE_DECISIONS, f"undocumented fixture line {key}")
            rule_id, comparability, reasons = FIXTURE_DECISIONS[key]
            curated, sidecar = curate_rewards.curate_record(
                record, source_path=name, source_line=line_number
            )
            annotation = curated[curate_rewards.ANNOTATION_FIELD]
            self.assertEqual(annotation["comparability"], comparability, key)
            self.assertEqual(annotation["reason_codes"], reasons, key)
            self.assertEqual(
                sidecar["classification"],
                {"comparability": comparability, "reason_codes": reasons},
                key,
            )
            rule = curate_rewards.comparability_rule(rule_id)
            self.assertEqual(rule["comparability"], comparability, key)
            self.assertTrue(
                set(rule["reason_codes"]) <= set(reasons),
                f"{key} does not carry rule {rule_id}'s reason codes",
            )
            seen.add(key)
        self.assertEqual(seen, set(FIXTURE_DECISIONS))

    def test_the_fixture_corpus_exercises_every_declared_rule_and_method(self):
        rules = set()
        methods = set()
        for name, line_number, record in all_fixture_records():
            _curated, sidecar = curate_rewards.curate_record(
                record, source_path=name, source_line=line_number
            )
            _c, _r, _p, rule_id = curate_rewards._classify(
                sidecar["source_rewards"], sidecar["arithmetic"]
            )
            rules.add(rule_id)
            methods.update(entry["method"] for entry in sidecar["arithmetic"])
        self.assertEqual(
            rules,
            {rule["id"] for rule in curate_rewards.COMPARABILITY_RULES},
        )
        self.assertEqual(methods, set(curate_rewards.REQUIRED_ARITHMETIC_METHODS))

    def test_every_retained_record_declares_a_comparability_class(self):
        classes = collections.Counter()
        for name, line_number, record in all_fixture_records():
            curated, _sidecar = curate_rewards.curate_record(
                record, source_path=name, source_line=line_number
            )
            self.assertIn(curate_rewards.ANNOTATION_FIELD, curated)
            classes[curate_rewards.comparability_of(curated)] += 1
        self.assertEqual(sum(classes.values()), len(FIXTURE_DECISIONS))
        self.assertEqual(classes[MAGNITUDE], 3)
        self.assertEqual(classes[ORDER_ONLY], 3)
        self.assertEqual(classes[EXCLUDED], len(FIXTURE_DECISIONS) - 6)

    def test_curation_is_deterministic_idempotent_and_non_mutating(self):
        for name, line_number, record in all_fixture_records():
            before = json.dumps(record, sort_keys=True)
            first, first_sidecar = curate_rewards.curate_record(
                record, source_path=name, source_line=line_number
            )
            second, second_sidecar = curate_rewards.curate_record(
                record, source_path=name, source_line=line_number
            )
            self.assertEqual(first, second)
            self.assertEqual(first_sidecar, second_sidecar)
            again, again_sidecar = curate_rewards.curate_record(
                first, source_path=name, source_line=line_number
            )
            self.assertEqual(again, first)
            self.assertEqual(again_sidecar, first_sidecar)
            self.assertEqual(json.dumps(record, sort_keys=True), before)

    def test_every_source_reward_stays_recoverable(self):
        for name, line_number, record in all_fixture_records():
            curated, sidecar = curate_rewards.curate_record(
                record, source_path=name, source_line=line_number
            )
            self.assertEqual(
                curate_rewards.restore_source_record(curated, sidecar), record
            )
            self.assertEqual(
                curated[curate_rewards.ANNOTATION_FIELD]["source_reward_count"],
                len(sidecar["source_rewards"]),
            )
            for entry in sidecar["source_rewards"]:
                self.assertIn("value", entry)

    def test_classify_jsonl_summarises_each_layout_family(self):
        summary = curate_rewards.classify_jsonl(FIXTURES / "ffpc-preferences.jsonl")
        self.assertEqual(summary["records"], 9)
        self.assertEqual(
            summary["comparability"],
            {MAGNITUDE: 2, ORDER_ONLY: 3, EXCLUDED: 4},
        )
        swarm = curate_rewards.classify_jsonl(FIXTURES / "swarm-trajectories.jsonl")
        self.assertEqual(swarm["comparability"], {EXCLUDED: 5})

    def test_the_census_cli_reproduces_the_fixture_vocabulary(self):
        census = curate_rewards.census_jsonl(
            [FIXTURES / name for name in sorted(FIXTURE_SHA256)]
        )
        self.assertEqual(census["records"], len(FIXTURE_DECISIONS))
        self.assertEqual(census["scope_keys"], ["reward_components"])
        self.assertEqual(
            sum(census["dispositions"].values()), census["unique_component_keys"]
        )
        for key, entry in census["component_keys"].items():
            self.assertEqual(
                entry["disposition"],
                curate_rewards.disposition_for_observed_types(
                    key, entry["observed_types"]
                ),
            )
        # Two bare `reward` scopes live outside the census scope but inside the
        # ontology's, and neither is dropped.
        self.assertEqual(
            census["ontology_scope_instances"] - census["reward_instances"], 2
        )
        self.assertEqual(
            set(census["dispositions"]),
            set(curate_rewards.COMPONENT_DISPOSITIONS),
        )

    def test_census_rejects_non_object_records(self):
        with self.assertRaisesRegex(
            curate_rewards.RewardOntologyError, "census records must be objects"
        ):
            curate_rewards.reward_census(["not-an-object"])

    def test_census_scope_key_accepts_reward_and_rejects_unknown(self):
        records = []
        for _name, _line, record in all_fixture_records():
            records.append(record)
        census = curate_rewards.reward_census(records, scope_keys=["reward"])
        self.assertEqual(census["scope_keys"], ["reward"])
        self.assertGreater(census["reward_instances"], 0)
        with self.assertRaisesRegex(
            curate_rewards.RewardOntologyError,
            "census scope names non-reward keys",
        ):
            curate_rewards.reward_census(records, scope_keys=["not_a_reward"])

    def test_census_cli_scope_key_and_unknown_scope(self):
        with tempfile.TemporaryDirectory() as td:
            source = Path(td) / "in.jsonl"
            source.write_text(
                json.dumps({"id": "r1", "reward": 1.0}) + "\n",
                encoding="utf-8",
            )
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                code = curate_rewards.main(
                    ["census", str(source), "--scope-key", "reward"]
                )
            self.assertEqual(code, 0)
            summary = json.loads(stdout.getvalue())
            self.assertEqual(summary["scope_keys"], ["reward"])
            self.assertEqual(summary["reward_instances"], 1)
            self.assertNotIn("component_keys", summary)
            stderr = io.StringIO()
            with redirect_stdout(io.StringIO()), redirect_stderr(stderr):
                code = curate_rewards.main(
                    ["census", str(source), "--scope-key", "not_a_reward"]
                )
            self.assertEqual(code, 2)
            self.assertIn("census scope names non-reward keys", stderr.getvalue())


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


@unittest.skipUnless(
    RAW_RUN.is_dir(), "the 2026-08-17 raw run is not present in this checkout"
)
class MappedRunFidelity(unittest.TestCase):
    """Opt-in: the frozen mapping still describes the run it was derived from."""

    @classmethod
    def setUpClass(cls):
        cls.records = []
        for path in sorted(RAW_RUN.rglob("*.jsonl")):
            for line_number, line in enumerate(
                path.read_text(encoding="utf-8").splitlines(), 1
            ):
                if line.strip():
                    cls.records.append(
                        (path.parent.name, path.name, line_number, json.loads(line))
                    )

    def test_the_frozen_vocabulary_matches_the_raw_run(self):
        census = curate_rewards.reward_census(
            record for _f, _n, _l, record in self.records
        )
        frozen = curate_rewards.CONVERSION_POLICY["source_vocabulary"]
        for field in (
            "records",
            "reward_instances",
            "ontology_scope_instances",
            "unique_component_keys",
            "unique_shapes",
            "dispositions",
            "arithmetic",
            "component_keys",
            "shapes",
        ):
            self.assertEqual(census[field], frozen[field], field)

    def test_the_frozen_classification_matches_the_raw_run(self):
        classes = collections.Counter()
        reasons = collections.Counter()
        for factory, name, line_number, record in self.records:
            curated, sidecar = curate_rewards.curate_record(
                record, source_path=f"{factory}/{name}", source_line=line_number
            )
            annotation = curated[curate_rewards.ANNOTATION_FIELD]
            classes[annotation["comparability"]] += 1
            reasons.update(annotation["reason_codes"])
            self.assertEqual(
                curate_rewards.restore_source_record(curated, sidecar),
                record,
                f"{factory}/{name}:{line_number}",
            )
        expected = curate_rewards.CONVERSION_POLICY["expected_classification"]
        self.assertEqual(dict(sorted(classes.items())), expected["comparability"])
        self.assertEqual(dict(sorted(reasons.items())), expected["reason_codes"])


class ReviewFollowUpPolicyTests(unittest.TestCase):
    def policy(self):
        return copy.deepcopy(curate_rewards.CONVERSION_POLICY)

    def test_numeric_pattern_must_match_and_stay_numeric(self):
        document = self.policy()
        document["policy"]["arithmetic"]["rounding_declaration_pattern"] = "(zzzznomatch)"
        with self.assertRaisesRegex(
            curate_rewards.RewardOntologyError, "must match a numeric sample"
        ):
            curate_rewards.validate_conversion_policy(document)
        document["policy"]["arithmetic"]["rounding_declaration_pattern"] = r"(\d+|xyz)"
        with self.assertRaisesRegex(
            curate_rewards.RewardOntologyError, "capture group must be numeric"
        ):
            curate_rewards.validate_conversion_policy(document)

    def test_weight_aliases_must_not_overlap_non_component_keys(self):
        document = self.policy()
        document["policy"]["arithmetic"]["weight_aliases"]["total"] = [
            "total"
        ]
        with self.assertRaisesRegex(
            curate_rewards.RewardOntologyError,
            "weight aliases must not overlap non_component_keys",
        ):
            curate_rewards.validate_conversion_policy(document)

    def test_required_semantics_must_retain_risk_adjustment(self):
        document = self.policy()
        document["policy"]["conversion"]["required_semantics_substring"] = "usd"
        with self.assertRaisesRegex(
            curate_rewards.RewardOntologyError,
            "risk-adjustment marker",
        ):
            curate_rewards.validate_conversion_policy(document)

    def test_preference_pointers_reject_nested_reward_keys(self):
        document = self.policy()
        document["policy"]["preference_scope"]["preferred"] = (
            "/chosen/reward_components/reward"
        )
        document["policy"]["preference_scope"]["dispreferred"] = (
            "/rejected/reward_components/reward"
        )
        with self.assertRaisesRegex(
            curate_rewards.RewardOntologyError,
            "nested reward-key segment",
        ):
            curate_rewards.validate_conversion_policy(document)

    def test_ontology_scope_instances_must_cover_reward_instances(self):
        document = self.policy()
        document["source_vocabulary"]["ontology_scope_instances"] = 1
        with self.assertRaisesRegex(
            curate_rewards.RewardOntologyError,
            "ontology_scope_instances must be at least reward_instances",
        ):
            curate_rewards.validate_conversion_policy(document)

    def test_canonical_unit_usd_must_be_10000(self):
        document = self.policy()
        document["policy"]["conversion"]["canonical_unit_usd"] = 1
        with self.assertRaisesRegex(
            curate_rewards.RewardOntologyError, "canonical_unit_usd must be 10000"
        ):
            curate_rewards.validate_conversion_policy(document)

    def test_preference_pointers_must_differ_from_canonical_scope(self):
        document = self.policy()
        document["policy"]["preference_scope"]["preferred"] = document["policy"][
            "canonical_scope"
        ]
        with self.assertRaisesRegex(
            curate_rewards.RewardOntologyError,
            "preference pointers must differ from canonical_scope",
        ):
            curate_rewards.validate_conversion_policy(document)

    def test_runtime_rule_classes_are_bound(self):
        document = self.policy()
        for rule in document["policy"]["comparability_rules"]:
            if rule["id"] == "R00":
                rule["comparability"] = curate_rewards.MAGNITUDE_COMPARABLE
        with self.assertRaisesRegex(
            curate_rewards.RewardOntologyError,
            "rule R00 must declare comparability",
        ):
            curate_rewards.validate_conversion_policy(document)

    def test_component_occurrences_cannot_exceed_instances(self):
        document = self.policy()
        key = next(iter(document["source_vocabulary"]["component_keys"]))
        document["source_vocabulary"]["component_keys"][key]["occurrences"] = 999999
        with self.assertRaisesRegex(
            curate_rewards.RewardOntologyError,
            "occurrences must not exceed reward_instances",
        ):
            curate_rewards.validate_conversion_policy(document)

    def test_scope_keys_must_be_a_unique_list(self):
        document = self.policy()
        document["source_vocabulary"]["scope_keys"] = "reward_components"
        with self.assertRaisesRegex(
            curate_rewards.RewardOntologyError,
            "scope_keys must be a unique nonempty list of strings",
        ):
            curate_rewards.validate_conversion_policy(document)

    def test_arithmetic_census_must_reconcile(self):
        document = self.policy()
        missing = copy.deepcopy(document)
        del missing["source_vocabulary"]["arithmetic"]
        with self.assertRaisesRegex(
            curate_rewards.RewardOntologyError, "arithmetic must be a nonempty list"
        ):
            curate_rewards.validate_conversion_policy(missing)
        document["source_vocabulary"]["arithmetic"][0]["occurrences"] = 999999
        with self.assertRaisesRegex(
            curate_rewards.RewardOntologyError,
            "arithmetic occurrences must sum to reward_instances",
        ):
            curate_rewards.validate_conversion_policy(document)

    def test_canonical_scope_uses_json_pointer_escaping(self):
        document = self.policy()
        document["policy"]["reward_keys"] = list(document["policy"]["reward_keys"]) + [
            "a/b"
        ]
        document["policy"]["canonical_scope"] = "/a/b"
        with self.assertRaisesRegex(
            curate_rewards.RewardOntologyError,
            "canonical_scope must name a declared reward key",
        ):
            curate_rewards.validate_conversion_policy(document)

    def test_census_signature_escapes_separator_keys(self):
        census = curate_rewards.reward_census(
            [{"reward_components": {"a|b": 1, "total": 1}}]
        )
        signature = census["shapes"][0]["signature"]
        self.assertIn("a\\|b:int", signature)
        self.assertNotIn("a|b:int|", signature + "|")

    def test_census_jsonl_materializes_generator_paths(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "one.jsonl"
            write_jsonl(path, [{"reward_components": {"total": 1.0}}])
            result = curate_rewards.census_jsonl((p for p in [path]))
        self.assertEqual(result["inputs"], [str(path)])
        self.assertGreaterEqual(result["records"], 1)

    def test_load_units_migration_bytes_uses_mapped_fields(self):
        payload = json.dumps(
            {
                "records": [
                    {
                        curate_rewards.MIGRATION_FACTOR_FIELD: 0.2,
                        curate_rewards.MIGRATION_SCOPE_FIELD: "ffpc-r2-001 extra",
                    }
                ]
            }
        ).encode("utf-8")
        catalog = curate_rewards.load_units_migration_bytes(payload, label="mem")
        self.assertIn(curate_rewards.catalog_record_key("ffpc-r2-001"), catalog)

    def test_invalid_policy_utf8_is_an_ontology_error(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "policy.json"
            path.write_bytes(b"\xff\xfe not utf-8")
            with self.assertRaises(curate_rewards.RewardOntologyError):
                curate_rewards.load_conversion_policy(path)

    def test_incomplete_source_reward_entries_are_rejected(self):
        record = {"id": "x", "reward_components": components(1.0)}
        _curated, sidecar = curate_rewards.curate_record(record)
        sidecar["source_rewards"][0].pop("value")
        sidecar.pop("sidecar_id", None)
        sidecar["sidecar_id"] = curate_rewards._sha256(sidecar)
        with self.assertRaisesRegex(
            curate_rewards.RewardOntologyError, "invalid source reward entry"
        ):
            curate_rewards.validate_ontology_document(sidecar)


if __name__ == "__main__":
    unittest.main()
