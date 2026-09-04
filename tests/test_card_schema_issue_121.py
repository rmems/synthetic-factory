#!/usr/bin/env python3
"""Issue #63 leaf tests for the per-dataset card schema declaration."""

import unittest

from card_schema_test_support import (
    EPISODE_JSON_COLUMNS,
    FEATURES_YAML,
    META_JSON_YAML,
    NOT_DECLARED,
    NO_FOREIGN_PAYLOAD,
    PLAN_PRESENT_ROW,
    PLAN_STRING_YAML,
    REFLECTION_OPTIONAL_ROW,
    REWARD_JSON_YAML,
    TOOL_CALL_FIELDS,
    VIEWER_SCHEMA_HEADING,
    DeclarationTestCase,
    card_schema,
    publisher,
)

FEATURE_FLAG_DEBUG = "feature-flag-debug-trajectories"
PAYLOAD_NAMES = [f"batch-r{n:02d}.jsonl" for n in range(1, 111)]


class FeatureFlagDebugDeclarationTests(DeclarationTestCase):
    """Issue #63: thin `meta` vs the designed/plant shapes that widen it."""

    DATASET = FEATURE_FLAG_DEBUG
    ISSUE = 63
    HUB_ITEM = {
        "slug": "feature-flag-debug-factory",
        "hub": FEATURE_FLAG_DEBUG,
        "pretty": "Feature Flag Debug Trajectories",
        "blurb": "Feature-flag leftover assignment/override debug episodes.",
        "tags": ["synthetic-data", "trajectories", "feature-flags"],
    }
    SUMMARY = publisher.PayloadSummary(
        records=220, bytes_=1523718, first="r01", last="r110", names=PAYLOAD_NAMES
    )

    def test_declaration_matches_the_observed_union_schema(self):
        # `plan` is a string on all 220 records here, unlike the #36 dataset.
        _names, steps, tool_call = self.assert_episode_union()
        for required in ("n", "decision_basis", "tool_call", "observation"):
            self.assertNotIn("optional", steps[required])
        self.assertEqual(set(tool_call), TOOL_CALL_FIELDS)

    def test_key_bag_columns_are_declared_json(self):
        self.assert_json_columns(EPISODE_JSON_COLUMNS)

    def test_card_front_matter_declares_the_default_config_over_raw_batches(self):
        self.assert_front_matter_declares_default_config(
            FEATURES_YAML,
            META_JSON_YAML,
            REWARD_JSON_YAML,
            PLAN_STRING_YAML,
            # Card-only annotations must never reach the YAML.
            absent=("optional",),
        )

    def test_card_body_owns_the_leftover_mechanic_and_the_optional_reflection(self):
        self.assertIn(VIEWER_SCHEMA_HEADING, self.card)
        self.assertNotIn(NOT_DECLARED, self.card)
        self.assert_card_has(
            REFLECTION_OPTIONAL_ROW,
            PLAN_PRESENT_ROW,
            # The leftover names are this factory's own mechanic, not a foreign mill.
            "advertised leftover assignment/override mechanic",
            NO_FOREIGN_PAYLOAD,
            "`decision_basis`",
        )

    def test_declared_globs_cover_every_published_shard(self):
        self.assertEqual(
            card_schema.payload_coverage_errors(self.declaration, PAYLOAD_NAMES), []
        )
        # A shard the glob cannot reach is a hard error, not a silent drop.
        self.assertTrue(
            card_schema.payload_coverage_errors(
                self.declaration, PAYLOAD_NAMES + ["extra.jsonl"]
            )
        )


if __name__ == "__main__":
    unittest.main()
