#!/usr/bin/env python3
"""Issue #49 leaf tests for the per-dataset card schema declaration."""

import unittest

from card_schema_test_support import (
    DEFAULT_DATA_FILES,
    DISCLOSURES_HEADING,
    EPISODE_FIELD_ORDER,
    FEATURES_YAML,
    NOT_DECLARED,
    NO_FOREIGN_PAYLOAD,
    REFLECTION_OPTIONAL_ROW,
    REWARD_JSON_YAML,
    VIEWER_SCHEMA_HEADING,
    DeclarationTestCase,
    by_name,
    feature_names,
    publisher,
)

PROTO_BREAKING = "proto-breaking-change-trajectories"


class ProtoBreakingChangeDeclarationTests(DeclarationTestCase):
    """Issue #49: `reward` is a seven-shape key-bag, so the parquet index fails.

    The numbers asserted here are derived from the published payload at
    ``~/rmems/hf/grok-4.6/proto-breaking-change-trajectories`` (1707 shards,
    3414 records, 70670 steps), not copied from the issue body.
    """

    DATASET = PROTO_BREAKING
    ISSUE = 49
    # The Hub item and published-payload facts the card must render, derived
    # from the mirror at ~/rmems/hf/grok-4.6/proto-breaking-change-trajectories.
    HUB_ITEM = {
        "slug": "proto-breaking-change-factory",
        "hub": PROTO_BREAKING,
        "pretty": "Proto Breaking Change Trajectories",
        "blurb": "Protobuf leftover-compat breaking-change episodes.",
        "tags": ["synthetic-data", "trajectories", "protobuf", "api"],
    }
    SUMMARY = publisher.PayloadSummary(
        records=3414,
        bytes_=25953665,
        first="r01",
        last="r1707",
        names=["batch-r01.jsonl", "batch-r1707.jsonl"],
    )

    def test_declaration_matches_the_observed_union_schema(self):
        self.assertEqual(feature_names(self.declaration["features"]), EPISODE_FIELD_ORDER)
        names = self.names()
        # Unlike long-horizon-coding, every record here carries `plan`.
        self.assertEqual(names["plan"]["dtype"], "string")
        self.assertNotIn("optional", names["plan"])
        self.assertEqual(names["reward"]["dtype"], "json")
        self.assertEqual(
            by_name(names["meta"]["struct"]),
            {
                "factory": {"name": "factory", "dtype": "string"},
                "generator": {"name": "generator", "dtype": "string"},
                "round": {"name": "round", "dtype": "int64"},
            },
        )
        steps, tool_call = self.assert_episode_steps(names, "2948 of 70670 steps")
        self.assertEqual(steps["n"]["dtype"], "int64")
        self.assertEqual(tool_call["name"]["dtype"], "string")
        self.assertEqual(self.declaration["issues"], [49])
        self.assertEqual(self.declaration["data_files"], DEFAULT_DATA_FILES)

    def test_optional_reward_keys_are_documented_not_declared_as_columns(self):
        # `buf_breaking` / `xfailed` must never become their own struct fields:
        # `reward` is one `json` column, and the variants live in its note.
        self.assert_json_columns(["steps[].tool_call.args", "reward"])
        reward = self.feature("reward")
        self.assertIn("`buf_breaking` on 2814 of 3414", reward["note"])
        self.assertIn("`xfailed` on 1686 of 3414", reward["note"])

    def test_card_front_matter_declares_the_default_config_over_raw_batches(self):
        self.assert_front_matter_declares_default_config(
            FEATURES_YAML,
            REWARD_JSON_YAML,
            "  - name: meta\n"
            "    struct:\n"
            "    - name: factory\n"
            "      dtype: string\n"
            "    - name: generator\n"
            "      dtype: string\n"
            "    - name: round\n"
            "      dtype: int64\n",
            # Card-only annotations must not leak into the HF feature encoding.
            absent=("optional:", "note:"),
        )

    def test_card_body_discloses_the_reward_variants_and_optional_reflection(self):
        self.assertIn(VIEWER_SCHEMA_HEADING, self.card)
        self.assertNotIn(NOT_DECLARED, self.card)
        self.assert_card_has(
            REFLECTION_OPTIONAL_ROW,
            "| `reward` | present on every record |",
            DISCLOSURES_HEADING,
            "3414-record published snapshot audited for issue #49",
            "1686 `{buf_breaking, cost_steps, success, tests_passed, xfailed}`",
            "`skipped` (10), `ignored` (7), `disabled` (2) or `pending` (2)",
            NO_FOREIGN_PAYLOAD,
            "https://github.com/rmems/synthetic-factory/issues/49",
        )


if __name__ == "__main__":
    unittest.main()
