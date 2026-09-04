#!/usr/bin/env python3
"""Issue #59 leaf tests for the per-dataset card schema declaration."""

import unittest

from card_schema_test_support import (
    ARGS_JSON_YAML,
    DEFAULT_DATA_FILES,
    EPISODE_FIELDS,
    EPISODE_JSON_COLUMNS,
    FEATURES_YAML,
    LONG_HORIZON,
    META_JSON_YAML,
    NOT_DECLARED,
    PLAN_PRESENT_ROW,
    REFLECTION_OPTIONAL_ROW,
    REWARD_JSON_YAML,
    TOOL_CALL_FIELDS,
    VIEWER_SCHEMA_HEADING,
    DeclarationTestCase,
    by_name,
    card_schema,
    publisher,
)

DATA_PIPELINE_REPAIR = "data-pipeline-repair-trajectories"


class DataPipelineRepairDeclarationTests(DeclarationTestCase):
    """Issue #59: evolving `meta` plus a 1074-key `reward` bag.

    Every count asserted here was derived from the read-only mirror at
    ~/rmems/hf/grok-4.6/data-pipeline-repair-trajectories (3056 shards,
    6112 records, 101200 steps, 0 parse failures).
    """

    DATASET = DATA_PIPELINE_REPAIR
    ISSUE = 59
    HUB_ITEM = {
        "slug": "data-pipeline-repair-factory",
        "hub": DATA_PIPELINE_REPAIR,
        "pretty": "Data Pipeline Repair Trajectories",
        "blurb": "Schema-drift and late-data pipeline repair episodes.",
        "tags": ["synthetic-data", "trajectories", "data-pipeline", "etl"],
    }
    SUMMARY = publisher.PayloadSummary(
        records=6112,
        bytes_=58979846,
        first="r01",
        last="r3056",
        names=["batch-r01.jsonl", "batch-r2623.jsonl", "batch-r3056.jsonl"],
    )

    def test_declaration_matches_the_observed_union_schema(self):
        names = self.names()
        self.assertEqual(set(names), EPISODE_FIELDS)
        self.assertEqual(names["meta"]["dtype"], "json")
        self.assertEqual(names["reward"]["dtype"], "json")
        steps, tool_call = self.assert_episode_steps(names)
        self.assertEqual(steps["n"]["dtype"], "int64")
        self.assertEqual(set(tool_call), TOOL_CALL_FIELDS)
        self.assertEqual(self.declaration["issues"], [59])
        self.assertEqual(self.declaration["data_files"], DEFAULT_DATA_FILES)

    def test_plan_is_mandatory_here_unlike_the_worked_example(self):
        """`plan` is on 6112 of 6112 records; optionality is never copied."""
        plan = self.feature("plan")
        self.assertFalse(plan.get("optional", False))
        self.assertEqual(plan["dtype"], "string")
        sibling_plan = by_name(card_schema.load(LONG_HORIZON)["features"])["plan"]
        self.assertTrue(sibling_plan["optional"])
        self.assertIn(PLAN_PRESENT_ROW, self.card)

    def test_key_bag_columns_are_declared_json(self):
        self.assert_json_columns(EPISODE_JSON_COLUMNS)

    def test_card_front_matter_declares_the_default_config_over_raw_batches(self):
        self.assert_front_matter_declares_default_config(
            FEATURES_YAML, META_JSON_YAML, REWARD_JSON_YAML, ARGS_JSON_YAML
        )

    def test_card_body_discloses_the_sixteen_dest_stamped_leftovers(self):
        leftovers = next(
            disclosure
            for disclosure in self.declaration["disclosures"]
            if disclosure["ids"]
        )
        self.assertEqual(len(leftovers["ids"]), 16)
        self.assertEqual(leftovers["issues"], [43, 44])
        self.assertTrue(
            all(record_id.startswith("dbc-r26") for record_id in leftovers["ids"])
        )
        self.assert_card_has(
            VIEWER_SCHEMA_HEADING,
            "`dbc-r2623-nydus-rafs-blobcache-digest-leftover`",
            "`dbc-r2630-kaniko-snapshotmode-redo-leftover`",
            REFLECTION_OPTIONAL_ROW,
        )
        self.assertNotIn(NOT_DECLARED, self.card)

    def test_the_factory_own_leftover_mechanic_is_not_reported_as_foreign(self):
        """The advertised `leftover` repair mechanic is native, not a mill mix."""
        sentences = [
            disclosure["summary"] for disclosure in self.declaration["disclosures"]
        ]
        native = next(text for text in sentences if "6096" in text)
        self.assertIn("meta.kind=episode", native)
        self.assertIn("own advertised repair mechanic", native)
        self.assertIn("6096 records are `data-pipeline-repair-factory`", self.card)


if __name__ == "__main__":
    unittest.main()
