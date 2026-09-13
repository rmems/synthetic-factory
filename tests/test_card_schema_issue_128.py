#!/usr/bin/env python3
"""Issue #69 leaf tests for the per-dataset card schema declaration."""

import unittest

from card_schema_test_support import (
    EPISODE_JSON_COLUMNS,
    FEATURES_YAML,
    META_JSON_YAML,
    NOT_DECLARED,
    PLAN_PRESENT_ROW,
    REFLECTION_OPTIONAL_ROW,
    VIEWER_SCHEMA_HEADING,
    DeclarationTestCase,
    by_name,
    feature_names,
    publisher,
)

OBSERVABILITY_DEBUG = "observability-debug-trajectories"

# The published column order: the five episode-only extras sit between `plan`
# and `steps`.
OBSERVABILITY_FIELD_ORDER = [
    "id", "goal", "plan", "lie", "red_herring", "diagnosis",
    "recovery", "verification", "steps", "outcome", "reward", "meta",
]


class ObservabilityDebugDeclarationTests(DeclarationTestCase):
    """Issue #69: episode-only top-level extras beside a designed-only `meta`."""

    DATASET = OBSERVABILITY_DEBUG
    ISSUE = 69
    HUB_ITEM = {
        "slug": "observability-debug-factory",
        "hub": OBSERVABILITY_DEBUG,
        "pretty": "Observability Debug Trajectories",
        "blurb": "Observability leftover-lie (wrong dashboard / dropped label) episodes.",
        "tags": ["synthetic-data", "trajectories", "observability", "tracing"],
    }
    SUMMARY = publisher.PayloadSummary(
        records=1749,
        bytes_=10567586,
        first="r01",
        last="r875",
        names=["batch-r01.jsonl", "batch-r500.jsonl", "batch-r875.jsonl"],
    )

    def test_declaration_matches_the_observed_union_schema(self):
        self.assertEqual(feature_names(self.declaration["features"]), OBSERVABILITY_FIELD_ORDER)
        names = self.names()
        for scalar in ("id", "goal", "outcome"):
            with self.subTest(scalar=scalar):
                self.assertEqual(names[scalar]["dtype"], "string")
                self.assertNotIn("optional", names[scalar])
                self.assertIn("present on all 1749 records", names[scalar]["note"])
        # `plan` is a string on all 1749 records here, unlike #36 where it is optional.
        self.assertNotIn("optional", names["plan"])
        self.assertEqual(names["plan"]["dtype"], "string")
        self.assertEqual(names["meta"]["dtype"], "json")
        self.assertEqual(names["reward"]["dtype"], "json")
        self.assert_episode_steps(names)
        self.assertEqual(self.declaration["issues"], [69])

    def test_episode_only_extras_are_optional_typed_structs_not_json(self):
        names = self.names()
        for extra in ("lie", "red_herring", "diagnosis", "recovery", "verification"):
            with self.subTest(extra=extra):
                feature = names[extra]
                self.assertTrue(feature["optional"], f"{extra} must be optional")
                # Each extra has one uniform key set across all 316 episode records,
                # so it is declared as a searchable struct rather than a json blob.
                self.assertIn("struct", feature)
        red_herring = by_name(names["red_herring"]["struct"])
        self.assertEqual(
            set(red_herring), {"dashboard", "why_plausible", "dismissed_at_step"}
        )
        self.assertTrue(red_herring["dismissed_at_step"]["optional"])
        self.assertEqual(red_herring["dismissed_at_step"]["dtype"], "int64")
        for extra in ("diagnosis", "recovery", "verification"):
            with self.subTest(extra=extra):
                child = by_name(names[extra]["struct"])
                self.assertEqual(child["step"]["dtype"], "int64")

    def test_only_the_real_key_bags_are_declared_json(self):
        self.assert_json_columns(EPISODE_JSON_COLUMNS)

    def test_card_front_matter_declares_the_default_config_over_raw_batches(self):
        self.assert_front_matter_declares_default_config(
            FEATURES_YAML,
            META_JSON_YAML,
            "  - name: lie\n    struct:\n    - name: kind\n      dtype: string\n",
            # The card-only annotations never reach the emitted YAML.
            absent=("optional:",),
        )

    def test_card_body_discloses_the_dest_stamped_sparse_reward_row(self):
        self.assertIn(VIEWER_SCHEMA_HEADING, self.card)
        self.assertNotIn(NOT_DECLARED, self.card)
        self.assert_card_has(
            "`srl-r500-networkd-dhcp-ipv4-only-c67a`",
            "issues/43",
            "| `lie` | optional |",
            "| `red_herring.dismissed_at_step` | optional |",
            REFLECTION_OPTIONAL_ROW,
            PLAN_PRESENT_ROW,
        )


if __name__ == "__main__":
    unittest.main()
