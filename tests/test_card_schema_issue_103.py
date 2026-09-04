#!/usr/bin/env python3
"""Issue #47 leaf tests for the per-dataset card schema declaration."""

import unittest

from card_schema_test_support import (
    DEFAULT_DATA_FILES,
    EPISODE_FIELDS,
    EPISODE_JSON_COLUMNS,
    FEATURES_YAML,
    META_JSON_YAML,
    NOT_DECLARED,
    REFLECTION_OPTIONAL_ROW,
    REWARD_JSON_YAML,
    TOOL_CALL_FIELDS,
    VIEWER_SCHEMA_HEADING,
    DeclarationTestCase,
    publisher,
)


EXPECTED_FEATURE_MANIFEST = (
    ("id", "string", False),
    ("goal", "string", False),
    ("plan", "string", False),
    ("steps", "list", False),
    ("steps[].n", "int64", False),
    ("steps[].decision_basis", "string", False),
    ("steps[].tool_call", "struct", False),
    ("steps[].tool_call.name", "string", False),
    ("steps[].tool_call.args", "json", False),
    ("steps[].observation", "string", False),
    ("steps[].reflection", "string", True),
    ("outcome", "string", False),
    ("reward", "json", False),
    ("meta", "json", False),
)


def feature_manifest(features, prefix=""):
    """Flatten a declaration without consulting the independent expected manifest."""
    manifest = []
    for feature in features:
        path = f"{prefix}{feature['name']}"
        encodings = [key for key in ("dtype", "list", "struct") if key in feature]
        if len(encodings) != 1:
            raise AssertionError(f"{path} has {len(encodings)} feature encodings")
        encoding = encodings[0]
        manifest.append(
            (
                path,
                feature[encoding] if encoding == "dtype" else encoding,
                feature.get("optional", False),
            )
        )
        if encoding == "list":
            manifest.extend(feature_manifest(feature["list"], f"{path}[]."))
        elif encoding == "struct":
            manifest.extend(feature_manifest(feature["struct"], f"{path}."))
    return tuple(manifest)


class LogRedactionDeclarationTests(DeclarationTestCase):
    """Issue #47: thin `meta` vs `designed` / `domain` / `stack`, plus reward extras."""

    DATASET = "log-redaction-trajectories"
    ISSUE = 47
    HUB_ITEM = {
        "slug": "log-redaction-factory",
        "hub": DATASET,
        "pretty": "Log Redaction Trajectories",
        "blurb": "Log leftover-secret redaction vs mute-logger episodes.",
        "tags": ["synthetic-data", "trajectories", "logging", "redaction", "privacy"],
    }
    SUMMARY = publisher.PayloadSummary(
        records=344,
        bytes_=1928793,
        first="r01",
        last="r172",
        names=["batch-r01.jsonl", "batch-r172.jsonl"],
    )

    def test_complete_feature_manifest_matches_the_independent_data_scan(self):
        # This oracle was derived from the read-only 344-record scan. It is
        # intentionally separate from the declaration so omitted fields, wrong
        # fixed dtypes, and incorrect required/optional flags cannot self-validate.
        self.assertEqual(feature_manifest(self.declaration["features"]), EXPECTED_FEATURE_MANIFEST)

    def test_declaration_matches_the_observed_union_schema(self):
        names = self.names()
        self.assertEqual(set(names), EPISODE_FIELDS)
        # Unlike #36, every one of the 344 records carries `plan`, so it is not
        # declared optional here.
        self.assertNotIn("optional", names["plan"])
        self.assertEqual(names["plan"]["dtype"], "string")
        self.assertEqual(names["meta"]["dtype"], "json")
        self.assertEqual(names["reward"]["dtype"], "json")
        steps, tool_call = self.assert_episode_steps(names)
        self.assertNotIn("optional", steps["decision_basis"])
        self.assertEqual(set(tool_call), TOOL_CALL_FIELDS)
        self.assertEqual(self.declaration["issues"], [47])
        self.assertEqual(self.declaration["data_files"], DEFAULT_DATA_FILES)

    def test_key_bag_columns_are_declared_json(self):
        self.assert_json_columns(EPISODE_JSON_COLUMNS)

    def test_card_front_matter_declares_the_default_config_over_raw_batches(self):
        self.assert_front_matter_declares_default_config(
            FEATURES_YAML,
            META_JSON_YAML,
            REWARD_JSON_YAML,
            # Card-only annotations must never reach the feature encoding.
            absent=("optional",),
        )

    def test_card_body_discloses_the_thin_meta_and_lane_records(self):
        self.assertIn(VIEWER_SCHEMA_HEADING, self.card)
        self.assertNotIn(NOT_DECLARED, self.card)
        self.assert_card_has(
            REFLECTION_OPTIONAL_ROW,
            "`lrd-r01-access-log-bearer-token`",
            "`lrd-r25-gha-step-summary-pat-artifact-handoff`",
            "`lrd-r2-json-jwt-nested-p2`",
            "issues/47",
        )

    def test_disclosures_name_every_record_the_inferred_cast_trips_on(self):
        by_summary = {
            disclosure["summary"]: disclosure for disclosure in self.declaration["disclosures"]
        }
        thin = [
            disclosure for summary, disclosure in by_summary.items() if "thin `meta`" in summary
        ]
        lane = [
            disclosure for summary, disclosure in by_summary.items() if "`meta.lane`" in summary
        ]
        self.assertEqual((len(thin), len(lane)), (1, 1))
        self.assertEqual(len(thin[0]["ids"]), 36)
        self.assertEqual(len(set(thin[0]["ids"])), 36)
        self.assertEqual(len(lane[0]["ids"]), 8)
        self.assertEqual(len(set(lane[0]["ids"])), 8)
        self.assertFalse(set(thin[0]["ids"]) & set(lane[0]["ids"]))


if __name__ == "__main__":
    unittest.main()
