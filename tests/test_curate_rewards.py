#!/usr/bin/env python3
"""Focused tests for reward ontology v1 and conservative conversion."""

import collections
import copy
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PIPELINES = REPO / "pipelines"
SCHEMA = REPO / "schemas" / "reward-ontology-v1.schema.json"
sys.path.insert(0, str(PIPELINES))

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
        with_evidence, _ = curate_rewards.curate_record(
            record, calibration=calibration
        )

        self.assertEqual(
            without_evidence["reward_training"]["comparability"],
            "sign_order_only",
        )
        annotation = with_evidence["reward_training"]
        self.assertEqual(annotation["comparability"], "magnitude_comparable")
        self.assertIn("external_calibration_evidence", annotation["reason_codes"])
        self.assertTrue(
            all(
                value["calibration_source"]
                == "units-migration.json#/records/1"
                for value in annotation["magnitude"]["values"]
            )
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
            source.write_text(json.dumps(record) + "\n")

            summary = curate_rewards.convert_jsonl(
                source,
                output,
                sidecars,
                source_path="factory/preferences.jsonl",
            )
            self.assertEqual(summary["records"], 1)
            converted = json.loads(output.read_text())
            sidecar = json.loads(sidecars.read_text())
            self.assertEqual(
                curate_rewards.restore_source_record(converted, sidecar), record
            )
            with self.assertRaisesRegex(
                curate_rewards.RewardOntologyError, "refusing to overwrite"
            ):
                curate_rewards.convert_jsonl(source, output, sidecars)


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
        ["explicit_usd_unit_calibration", "preference_order_verified",
         "reward_arithmetic_verified"],
    ),
    ("ffpc-preferences.jsonl", 2): (
        "P05", MAGNITUDE,
        ["explicit_usd_unit_calibration", "preference_order_verified",
         "reward_arithmetic_verified"],
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
        ["explicit_usd_unit_calibration", "reward_arithmetic_verified"],
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
                "exclude_from_reward_training": 147,
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
                "non-finite numeric constant NaN",
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


if __name__ == "__main__":
    unittest.main()
