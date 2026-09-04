#!/usr/bin/env python3
"""Issue #48 leaf tests for the per-dataset card schema declaration."""

import unittest

from card_schema_test_support import (
    ARGS_JSON_YAML,
    DEFAULT_DATA_FILES,
    DISCLOSURES_HEADING,
    EPISODE_FIELDS,
    EPISODE_JSON_COLUMNS,
    FEATURES_YAML,
    META_JSON_YAML,
    NOT_DECLARED,
    NO_FOREIGN_PAYLOAD,
    REFLECTION_OPTIONAL_ROW,
    REWARD_JSON_YAML,
    TOOL_CALL_FIELDS,
    VIEWER_SCHEMA_HEADING,
    DeclarationTestCase,
    card_schema,
    publisher,
)

SCAN_REMEDIATION = "secret-scan-remediation-trajectories"


class SecretScanRemediationDeclarationTests(DeclarationTestCase):
    """Issue #48: `reward` is not uniform, so the parquet index cannot be built.

    Every count asserted here was derived from the published mirror at
    `~/rmems/hf/grok-4.6/secret-scan-remediation-trajectories` (2068 records
    over 1034 raw shards, 31549 steps), not copied from the issue text.
    """

    DATASET = SCAN_REMEDIATION
    ISSUE = 48
    HUB_ITEM = {
        "slug": "secret-scan-remediation-factory",
        "hub": SCAN_REMEDIATION,
        "pretty": "Secret Scan Remediation Trajectories",
        "blurb": "Secret-scan leftover-allowlist / baseline remediation.",
        "tags": ["synthetic-data", "trajectories", "secrets", "security"],
    }
    SUMMARY = publisher.PayloadSummary(
        records=2068,
        bytes_=16694229,
        first="r01",
        last="r1034",
        names=["batch-r01.jsonl", "batch-r1034.jsonl"],
    )

    def test_declaration_matches_the_observed_union_schema(self):
        names = self.names()
        self.assertEqual(set(names), EPISODE_FIELDS)
        # Unlike long-horizon-coding, `plan` is a string on all 2068 records.
        self.assertNotIn("optional", names["plan"])
        self.assertEqual(names["plan"]["dtype"], "string")
        self.assertEqual(names["reward"]["dtype"], "json")
        self.assertEqual(names["meta"]["dtype"], "json")
        steps, tool_call = self.assert_episode_steps(names)
        for required in ("n", "decision_basis", "observation"):
            self.assertNotIn("optional", steps[required])
        self.assertEqual(set(tool_call), TOOL_CALL_FIELDS)
        self.assertEqual(self.declaration["issues"], [48])

    def test_key_bag_columns_are_declared_json(self):
        self.assert_json_columns(EPISODE_JSON_COLUMNS)

    def test_data_files_cover_the_published_batch_payload(self):
        # The mirror publishes only `batch-rNN.jsonl`; there is no legacy
        # `episodes.jsonl` to carry, so the default glob is the whole payload.
        self.assertEqual(self.declaration["data_files"], DEFAULT_DATA_FILES)
        self.assertEqual(
            card_schema.payload_coverage_errors(
                self.declaration, ["batch-r01.jsonl", "batch-r1034.jsonl"]
            ),
            [],
        )

    def test_card_front_matter_declares_the_default_config_over_raw_batches(self):
        self.assert_front_matter_declares_default_config(
            FEATURES_YAML,
            REWARD_JSON_YAML,
            META_JSON_YAML,
            ARGS_JSON_YAML,
            # `optional` is a card annotation only; it must not reach the YAML.
            "    - name: reflection\n      dtype: string\n",
            absent=("optional",),
        )

    def test_card_body_discloses_the_reward_variants_and_optional_reflection(self):
        self.assertIn(VIEWER_SCHEMA_HEADING, self.card)
        self.assertNotIn(NOT_DECLARED, self.card)
        self.assert_card_has(
            REFLECTION_OPTIONAL_ROW,
            "present on 158 of 31549 steps",
            "`pr` on 1912, `handoff` on 967 and `xfailed` on 12",
            DISCLOSURES_HEADING,
            "`reward` has five key sets",
            NO_FOREIGN_PAYLOAD,
            "`decision_basis`",
        )


if __name__ == "__main__":
    unittest.main()
