#!/usr/bin/env python3
"""Issue #54 leaf tests for the per-dataset card schema declaration."""

import unittest

from card_schema_test_support import (
    EPISODE_FIELD_ORDER,
    EPISODE_JSON_COLUMNS,
    META_JSON_YAML,
    NOT_DECLARED,
    PLAN_OPTIONAL_ROW,
    REFLECTION_OPTIONAL_ROW,
    REWARD_JSON_YAML,
    STEP_FIELDS,
    VIEWER_SCHEMA_HEADING,
    DeclarationTestCase,
    card_schema,
    feature_names,
    publisher,
)

EMAIL_WEBHOOK = "email-webhook-retry-trajectories"


class EmailWebhookRetryDeclarationTests(DeclarationTestCase):
    """Issue #54: 190 records over 95 shards, thin `meta` first, leftover mill inside.

    Every count asserted here was derived from the read-only published mirror at
    `~/rmems/hf/grok-4.6/email-webhook-retry-trajectories/`, not from the issue
    text: 190 records, 3131 steps, 0 parse failures.
    """

    PAYLOAD_NAMES = [f"batch-r{index:02d}.jsonl" for index in range(1, 96)]

    DATASET = EMAIL_WEBHOOK
    ISSUE = 54
    HUB_ITEM = {
        "slug": "email-webhook-retry-factory",
        "hub": EMAIL_WEBHOOK,
        "pretty": "Email Webhook Retry Trajectories",
        "blurb": "Email-webhook leftover event-PK retry episodes.",
        "tags": ["synthetic-data", "email", "webhooks"],
    }
    SUMMARY = publisher.PayloadSummary(
        records=190, bytes_=1385245, first="r01", last="r95", names=PAYLOAD_NAMES
    )

    def test_declaration_matches_the_observed_union_schema(self):
        self.assertEqual(feature_names(self.declaration["features"]), EPISODE_FIELD_ORDER)
        names = self.names()
        # Unlike long-horizon-coding, every top-level field is on all 190
        # records -- `plan` included. Declaring it optional here would be a
        # transcription of the sibling dataset, not of this payload.
        for name in ("id", "goal", "plan", "outcome"):
            with self.subTest(field=name):
                self.assertEqual(names[name]["dtype"], "string")
                self.assertNotIn("optional", names[name])
        self.assertEqual(names["meta"]["dtype"], "json")
        self.assertEqual(names["reward"]["dtype"], "json")
        self.assertEqual(self.declaration["issues"], [54])

    def test_step_struct_declares_the_only_optional_field(self):
        steps = self.step_features(self.names())
        self.assertEqual(set(steps), STEP_FIELDS)
        self.assertTrue(steps["reflection"]["optional"])
        self.assertIn("2989 of 3131", steps["reflection"]["note"])
        for name in ("n", "decision_basis", "tool_call", "observation"):
            with self.subTest(field=name):
                self.assertNotIn("optional", steps[name])
        tool_call = self.tool_call_features(steps)
        self.assertEqual(tool_call["name"]["dtype"], "string")
        self.assertEqual(tool_call["args"]["dtype"], "json")

    def test_key_bag_columns_are_declared_json(self):
        self.assert_json_columns(EPISODE_JSON_COLUMNS)

    def test_declared_glob_covers_all_ninety_five_published_shards(self):
        self.assertEqual(
            card_schema.payload_coverage_errors(self.declaration, self.PAYLOAD_NAMES),
            [],
        )

    def test_card_front_matter_declares_the_default_config_over_raw_batches(self):
        self.assert_front_matter_declares_default_config(
            META_JSON_YAML,
            REWARD_JSON_YAML,
            # `meta` as a struct is exactly the cast the datasets-server died on.
            absent=("  - name: meta\n    struct:\n",),
        )
        self.assertNotIn(NOT_DECLARED, self.card)

    def test_card_body_discloses_the_leftover_mill_and_the_thin_meta_records(self):
        self.assertIn(VIEWER_SCHEMA_HEADING, self.card)
        self.assert_card_names_records(
            (
                "sir-r56-meili-swap-leftover3c-rebuild",
                "sir-r56-meili-drop-index-leftover3c-handoff",
                "sir-r57-typesense-alias-leftover3c-rebuild",
                "sir-r57-typesense-drop-coll-leftover3c-handoff",
                "sir-r58-sonic-push-leftover3c-rebuild",
                "sir-r58-sonic-drop-bucket-leftover3c-handoff",
            )
        )
        self.assert_card_has("issues/43", "issues/44")
        self.assert_card_names_records(
            ("ewr-r01-webhook-retry-dup-delivery", "ewr-r09-ses-event-dest-unique-5e08")
        )
        self.assertIn(REFLECTION_OPTIONAL_ROW, self.card)
        self.assertNotIn(PLAN_OPTIONAL_ROW, self.card)

    def test_leftover_mill_disclosure_lists_exactly_the_frozen_six_ids(self):
        mill = [
            disclosure
            for disclosure in self.declaration["disclosures"]
            if 43 in disclosure["issues"] and disclosure["ids"]
        ]
        self.assertEqual(len(mill), 1, "expected one leftover-mill id disclosure")
        self.assertEqual(len(mill[0]["ids"]), 6)
        self.assertTrue(
            all(record_id.startswith("sir-") for record_id in mill[0]["ids"]),
            mill[0]["ids"],
        )


if __name__ == "__main__":
    unittest.main()
