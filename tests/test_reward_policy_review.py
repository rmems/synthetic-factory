#!/usr/bin/env python3
"""Review follow-up tests for the reward conversion policy."""

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
    PIPELINES,
    components,
    write_jsonl,
)

if str(PIPELINES) not in sys.path:
    sys.path.insert(0, str(PIPELINES))

import curate_rewards  # noqa: E402


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


if __name__ == '__main__':
    unittest.main()
