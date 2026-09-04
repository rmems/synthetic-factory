#!/usr/bin/env python3
"""Issue #60 leaf tests for the per-dataset card schema declaration."""

import unittest

from card_schema_test_support import (
    EPISODE_FIELD_ORDER,
    EPISODE_JSON_COLUMNS,
    FEATURES_YAML,
    META_JSON_YAML,
    NOT_DECLARED,
    NO_FOREIGN_PAYLOAD,
    PLAN_OPTIONAL_ROW,
    PLAN_PRESENT_ROW,
    REFLECTION_OPTIONAL_ROW,
    REWARD_JSON_YAML,
    VIEWER_SCHEMA_HEADING,
    DeclarationTestCase,
    publisher,
)


class DbMigrationRepairDeclarationTests(DeclarationTestCase):
    """Issue #60: thin `meta` on four early records vs the plant/surface union.

    The counts asserted here are derived from the published mirror
    (`~/rmems/hf/grok-4.6/db-migration-repair-trajectories/data/raw`, 1363
    shards / 2726 records / 43630 steps), not copied from the issue text.
    """

    DATASET = "db-migration-repair-trajectories"
    ISSUE = 60
    HUB_ITEM = {
        "slug": "db-migration-repair-factory",
        "hub": DATASET,
        "pretty": "Db Migration Repair Trajectories",
        "blurb": "Database migration leftover-object repair episodes.",
        "tags": ["synthetic-data", "trajectories", "database", "migrations"],
    }
    SUMMARY = publisher.PayloadSummary(
        records=2726,
        bytes_=15978203,
        first="r01",
        last="r1363",
        names=["batch-r01.jsonl", "batch-r02.jsonl", "batch-r1363.jsonl"],
    )

    def test_declaration_matches_the_observed_union_schema(self):
        names = self.names()
        self.assertEqual(list(names), EPISODE_FIELD_ORDER)
        self.assertEqual(self.declaration["issues"], [60])
        note = self.declaration["note"]
        self.assertIn("can read the equally thin `batch-r02.jsonl`", note)
        self.assertIn("richer rows beginning in `batch-r03.jsonl`", note)
        self.assertNotIn("any later shard", note)
        self.assertEqual(names["meta"]["dtype"], "json")
        self.assertEqual(names["reward"]["dtype"], "json")
        self.assert_episode_steps(names, "11 of 43630")

    def test_plan_is_mandatory_here_unlike_the_long_horizon_dataset(self):
        # `plan` is on all 2726 records in this dataset. Copying the
        # long-horizon declaration's `optional: true` would publish a false
        # claim on the card's field table.
        plan = self.feature("plan")
        self.assertNotIn("optional", plan)
        self.assertNotIn(PLAN_OPTIONAL_ROW, self.card)
        self.assertIn(PLAN_PRESENT_ROW, self.card)

    def test_key_bag_columns_are_declared_json(self):
        self.assert_json_columns(EPISODE_JSON_COLUMNS)

    def test_card_front_matter_declares_the_default_config_over_raw_batches(self):
        self.assert_front_matter_declares_default_config(
            FEATURES_YAML,
            META_JSON_YAML,
            REWARD_JSON_YAML,
            # Card-only annotations must never reach the YAML.
            absent=("optional", "note:"),
        )

    def test_card_body_discloses_the_four_thin_meta_records(self):
        self.assertIn(VIEWER_SCHEMA_HEADING, self.card)
        self.assertNotIn(NOT_DECLARED, self.card)
        self.assert_card_names_records(
            (
                "dmr-r01-alembic-notnull-no-default",
                "dmr-r01-pg-invalid-concurrent-index",
                "dmr-r02-flyway-checksum-manual-sql",
                "dmr-r02-django-runpython-irreversible",
            )
        )
        self.assert_card_has(
            "seed the datasets-server's inferred schema",
            "The 2722 later records add",
            "those richer later rows are the cast failures",
            REFLECTION_OPTIONAL_ROW,
        )

    def test_card_body_separates_the_own_leftover_mechanic_from_a_foreign_mill(self):
        self.assert_card_has(
            "172 of 2726 record ids contain `leftover`",
            "advertised leftover-object mechanic",
            NO_FOREIGN_PAYLOAD,
        )
        # The frozen censuses are cited for the class definition only.
        self.assert_card_has("issues/43", "issues/44")


if __name__ == "__main__":
    unittest.main()
