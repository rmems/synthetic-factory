#!/usr/bin/env python3
"""Issue #58 leaf tests for the per-dataset card schema declaration."""

import unittest

from card_schema_test_support import (
    DEFAULT_DATA_FILES,
    EPISODE_FIELDS,
    EPISODE_JSON_COLUMNS,
    FEATURES_YAML,
    LONG_HORIZON,
    META_JSON_YAML,
    NOT_DECLARED,
    PLAN_PRESENT_ROW,
    PLAN_STRING_YAML,
    REFLECTION_OPTIONAL_ROW,
    REWARD_JSON_YAML,
    VIEWER_SCHEMA_HEADING,
    DeclarationTestCase,
    by_name,
    card_schema,
    publisher,
)

CSV_EXCEL_INGEST = "csv-excel-ingest-trajectories"


class CsvExcelIngestDeclarationTests(DeclarationTestCase):
    """Issue #58: thin `meta` vs `designed` / `domain` / `stack` kills the cast.

    Every count asserted here was derived from the unmodified published mirror
    at ``~/rmems/hf/grok-4.6/csv-excel-ingest-trajectories`` (152 shards, two
    records each, 304 records, 5015 steps, 0 parse failures), not copied from
    the issue text.
    """

    DATASET = CSV_EXCEL_INGEST
    ISSUE = 58
    HUB_ITEM = {
        "slug": "csv-excel-ingest-factory",
        "hub": CSV_EXCEL_INGEST,
        "pretty": "Csv Excel Ingest Trajectories",
        "blurb": "CSV/Excel/sidecar leftover ingest repair episodes.",
        "tags": ["csv", "excel", "ingest"],
    }
    SUMMARY = publisher.PayloadSummary(
        records=304,
        bytes_=2197062,
        first="r01",
        last="r152",
        names=[f"batch-r{n:02d}.jsonl" for n in range(1, 153)],
    )

    def test_declaration_matches_the_observed_union_schema(self):
        names = self.names()
        self.assertEqual(set(names), EPISODE_FIELDS)
        self.assertEqual(self.declaration["issues"], [58])
        self.assertEqual(self.declaration["data_files"], DEFAULT_DATA_FILES)
        self.assertEqual(names["meta"]["dtype"], "json")
        self.assertEqual(names["reward"]["dtype"], "json")
        self.assert_episode_steps(names)

    def test_plan_is_mandatory_here_unlike_the_worked_example(self):
        """`plan` is on all 304 records; #36 marks the same field optional."""
        plan = self.feature("plan")
        self.assertEqual(plan["dtype"], "string")
        self.assertNotIn("optional", plan)
        self.assertIn("304", plan["note"])
        sibling = by_name(card_schema.load(LONG_HORIZON)["features"])["plan"]
        self.assertTrue(sibling["optional"])

    def test_key_bag_columns_are_declared_json(self):
        self.assert_json_columns(EPISODE_JSON_COLUMNS)

    def test_card_front_matter_declares_the_default_config_over_raw_batches(self):
        self.assert_front_matter_declares_default_config(
            "  data_files:\n  - split: train\n",
            FEATURES_YAML,
            META_JSON_YAML,
            REWARD_JSON_YAML,
            PLAN_STRING_YAML,
        )

    def test_card_only_annotations_stay_out_of_the_front_matter(self):
        front_matter = self.front_matter()
        self.assertNotIn("optional:", front_matter)
        self.assertNotIn("note:", front_matter)
        self.assertNotIn("4870", front_matter)

    def test_card_body_discloses_the_two_dest_stamped_leftover_rows(self):
        self.assertIn(VIEWER_SCHEMA_HEADING, self.card)
        self.assertNotIn(NOT_DECLARED, self.card)
        self.assert_card_has(
            "`dbc-r64-bake-hcl-cache-from-leftover`",
            "`dbc-r64-bake-group-target-leftover`",
        )
        # Attributed to the frozen leftover-mill census, not re-filed.
        self.assert_card_has("/issues/43", "/issues/44")

    def test_card_body_discloses_both_disjoint_eight_record_groups(self):
        self.assert_card_has(
            "`cei-r01-csv-header-swap-amount-date`",
            "`cei-r08-csv-sci-notation-cents-8a11`",
            "`lane`",
            "does not overlap",
        )

    def test_card_body_reports_the_derived_optional_counts(self):
        self.assert_card_has(
            REFLECTION_OPTIONAL_ROW,
            "4870 of 5015 steps",
            PLAN_PRESENT_ROW,
            "5015 steps publishes a public `decision_basis`",
        )


if __name__ == "__main__":
    unittest.main()
