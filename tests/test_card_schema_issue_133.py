#!/usr/bin/env python3
"""PR #133 / issue #72 leaf tests for the per-dataset card schema declaration."""

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
    PLAN_PRESENT_ROW,
    REFLECTION_OPTIONAL_ROW,
    REWARD_JSON_YAML,
    TOOL_CALL_FIELDS,
    VIEWER_SCHEMA_HEADING,
    DeclarationTestCase,
    card_schema,
    publisher,
)

SEARCH_INDEX_REBUILD = "search-index-rebuild-trajectories"


SIR_THIN_META_IDS = (
    "sir-r01-es-mapping-conflict-reindex",
    "sir-r01-alias-swap-old-index-leftover",
    "sir-r05-meili-swap-filterable-5bb8",
    "sir-r05-typesense-alias-facet-8d44",
    "sir-r06-manticore-attach-rt-a091",
    "sir-r06-sonic-flushb-then-push-7e80",
)


SIR_LANE_IDS = (
    "sir-r2-os-alias-swap-p5",
    "sir-r2-solr-tlog-p5",
    "sir-r3-os-alias-swap-p5",
    "sir-r3-solr-tlog-p5",
    "sir-r4-os-alias-swap-p15",
    "sir-r4-solr-tlog-p15",
)


class SearchIndexRebuildDeclarationTests(DeclarationTestCase):
    """PR #133 / issue #72: thin `meta` vs the designed/lane union schema.

    Numbers below are the counted union over the 250 published records in
    ``data/raw/batch-r01.jsonl`` .. ``batch-r125.jsonl`` (4123 steps).
    """

    DATASET = SEARCH_INDEX_REBUILD
    ISSUE = 72
    MISSING_MESSAGE = "PR #133 is missing the config/card-schemas declaration for issue #72"
    HUB_ITEM = {
        "slug": "search-index-rebuild-factory",
        "hub": SEARCH_INDEX_REBUILD,
        "pretty": "Search Index Rebuild Trajectories",
        "blurb": "Search leftover-segment / schema rebuild episodes.",
        "tags": ["synthetic-data", "trajectories", "search", "indexing"],
    }
    SUMMARY = publisher.PayloadSummary(
        records=250,
        bytes_=1525810,
        first="r01",
        last="r125",
        names=[f"batch-r{n:02d}.jsonl" for n in range(1, 126)],
    )

    def test_declaration_matches_the_observed_union_schema(self):
        names = self.names()
        self.assertEqual(set(names), EPISODE_FIELDS)
        self.assertEqual(self.declaration["issues"], [72])
        self.assertEqual(self.declaration["config_name"], "default")
        self.assertEqual(self.declaration["split"], "train")
        self.assertEqual(self.declaration["data_files"], DEFAULT_DATA_FILES)
        self.assertEqual(names["meta"]["dtype"], "json")
        self.assertEqual(names["reward"]["dtype"], "json")
        _steps, tool_call = self.assert_episode_steps(names)
        self.assertEqual(set(tool_call), TOOL_CALL_FIELDS)
        self.assertEqual(tool_call["name"]["dtype"], "string")

    def test_plan_is_a_mandatory_string_here_not_an_optional_field(self):
        # The worked example (#36) declares `plan` optional. In this dataset it is
        # a string on all 250 records, so declaring it optional would be a lie.
        plan = self.feature("plan")
        self.assertEqual(plan["dtype"], "string")
        self.assertNotIn("optional", plan)
        self.assertIn(PLAN_PRESENT_ROW, self.card)

    def test_only_the_three_key_bag_columns_are_declared_json(self):
        self.assert_json_columns(EPISODE_JSON_COLUMNS)

    def test_card_front_matter_declares_the_default_config_over_raw_batches(self):
        self.assert_front_matter_declares_default_config(
            FEATURES_YAML,
            META_JSON_YAML,
            REWARD_JSON_YAML,
            ARGS_JSON_YAML,
            # Card-only annotations must never reach the YAML.
            absent=("optional", "note:"),
        )

    def test_card_body_discloses_the_thin_meta_lane_and_stub_records(self):
        self.assertIn(VIEWER_SCHEMA_HEADING, self.card)
        self.assertNotIn(NOT_DECLARED, self.card)
        self.assert_card_has("issues/72", DISCLOSURES_HEADING)
        self.assert_card_names_records(SIR_THIN_META_IDS + SIR_LANE_IDS)
        self.assert_card_has(
            "`sir-r26-typesense-synonym-used`",
            REFLECTION_OPTIONAL_ROW,
            "4038 of 4123 steps",
        )

    def test_card_owns_the_same_factory_leftover_naming_without_claiming_a_mix(self):
        self.assert_card_has(
            "leftover-segment",
            "109 of 250 ids",
            "no dest-stamped foreign payload in this dataset",
            "decision_basis",
        )

    def test_the_declared_glob_covers_every_published_shard(self):
        every_shard = [f"batch-r{n:02d}.jsonl" for n in range(1, 126)]
        self.assertEqual(
            card_schema.payload_coverage_errors(self.declaration, every_shard), []
        )
        self.assertTrue(
            card_schema.payload_coverage_errors(
                self.declaration, every_shard + ["episodes.jsonl"]
            )
        )


if __name__ == "__main__":
    unittest.main()
