#!/usr/bin/env python3
"""Fail-closed tests for the machine-readable reward conversion policy."""

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
    MAPPING,
    PIPELINES,
    SCHEMA,
)

if str(PIPELINES) not in sys.path:
    sys.path.insert(0, str(PIPELINES))

import curate_rewards  # noqa: E402


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

        import reward_ontology

        original = curate_rewards.COMPARABILITY_RULES
        try:
            patched = tuple(rules)
            curate_rewards.COMPARABILITY_RULES = patched
            reward_ontology.COMPARABILITY_RULES = patched
            verdict = curate_rewards._classify(source_rewards, [])
        finally:
            curate_rewards.COMPARABILITY_RULES = original
            reward_ontology.COMPARABILITY_RULES = original
        self.assertEqual(
            verdict,
            (
                curate_rewards.SIGN_ORDER_ONLY,
                ["magnitude_calibration_missing"],
                None,
                "P01",
            ),
        )



if __name__ == '__main__':
    unittest.main()
