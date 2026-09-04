#!/usr/bin/env python3
"""Issue #51 leaf tests for the per-dataset card schema declaration."""

import unittest

from card_schema_test_support import (
    DEFAULT_DATA_FILES,
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
    publisher,
)

GRAPHQL_NPLUSONE = "graphql-nplusone-trajectories"


class GraphqlNPlusOneDeclarationTests(DeclarationTestCase):
    """Issue #51: preview works, parquet index fails on the `reward` key-bag."""

    DATASET = GRAPHQL_NPLUSONE
    ISSUE = 51
    HUB_ITEM = {
        "slug": "graphql-nplusone-factory",
        "hub": GRAPHQL_NPLUSONE,
        "pretty": "Graphql Nplusone Trajectories",
        "blurb": "GraphQL leftover dataloader / N+1 episodes.",
        "tags": ["synthetic-data", "trajectories", "graphql"],
    }
    SUMMARY = publisher.PayloadSummary(
        records=632,
        bytes_=3343360,
        first="r01",
        last="r316",
        names=["batch-r01.jsonl", "batch-r316.jsonl"],
    )

    def test_declaration_matches_the_observed_union_schema(self):
        names = self.names()
        self.assertEqual(set(names), EPISODE_FIELDS)
        # Unlike #36, `plan` is on every record here, so it is not optional.
        self.assertNotIn("optional", names["plan"])
        self.assertEqual(names["meta"]["dtype"], "json")
        self.assertEqual(names["reward"]["dtype"], "json")
        steps, tool_call = self.assert_episode_steps(names, "567 of 10181 steps")
        self.assertEqual(steps["n"]["dtype"], "int64")
        self.assertEqual(set(tool_call), TOOL_CALL_FIELDS)
        self.assertEqual(tool_call["name"]["dtype"], "string")
        self.assertEqual(self.declaration["issues"], [51])
        self.assertEqual(self.declaration["data_files"], DEFAULT_DATA_FILES)

    def test_key_bag_columns_are_declared_json(self):
        self.assert_json_columns(EPISODE_JSON_COLUMNS)

    def test_reward_note_records_the_conditional_handoff_and_xfailed_counts(self):
        note = self.names()["reward"]["note"]
        for fragment in (
            "`handoff` and `xfailed` on 251",
            "`plan_changes` on 628",
            "`duration_min`, `retries`, `wasted_calls` on 44",
        ):
            self.assertIn(fragment, note)

    def test_card_front_matter_declares_the_default_config_over_raw_batches(self):
        self.assert_front_matter_declares_default_config(
            FEATURES_YAML, REWARD_JSON_YAML, META_JSON_YAML
        )

    def test_card_body_discloses_the_optional_fields_and_the_kind_misuse(self):
        self.assert_card_has(
            VIEWER_SCHEMA_HEADING,
            REFLECTION_OPTIONAL_ROW,
            "| `reward` | present on every record |",
            "`meta.kind` is inconsistent across rounds",
            NO_FOREIGN_PAYLOAD,
        )
        self.assertNotIn(NOT_DECLARED, self.card)


if __name__ == "__main__":
    unittest.main()
