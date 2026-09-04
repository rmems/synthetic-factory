#!/usr/bin/env python3
"""Issue #53 leaf tests for the per-dataset card schema declaration."""

import unittest

from card_schema_test_support import (
    ARGS_JSON_YAML,
    DISCLOSURES_HEADING,
    EPISODE_FIELD_ORDER,
    EPISODE_JSON_COLUMNS,
    FEATURES_YAML,
    META_JSON_YAML,
    NOT_DECLARED,
    REFLECTION_OPTIONAL_ROW,
    REWARD_JSON_YAML,
    STEP_FIELDS,
    TOOL_CALL_FIELDS,
    VIEWER_SCHEMA_HEADING,
    DeclarationTestCase,
    by_name,
    feature_names,
    publisher,
)

RATE_LIMIT = "rate-limit-backoff-trajectories"


RATE_LIMIT_GQL_MILL_IDS = (
    "gql-r135-hotchocolate-cost-analyzer-after-projection",
    "gql-r135-hotchocolate-disable-cost",
    "gql-r136-strawberry-relay-connection-after-override",
    "gql-r136-strawberry-drop-relay",
    "gql-r137-mercurius-persisted-query-after-schema",
    "gql-r137-mercurius-disable-persisted",
    "gql-r138-graphene-django-filter-after-queryset",
    "gql-r138-graphene-drop-filterset",
    "gql-r139-hasura-remote-schema-after-perm-reload",
    "gql-r139-hasura-disable-remote-schema",
)


RATE_LIMIT_SIR_MILL_IDS = (
    "sir-r114-quickwit-split-leftover3c-rebuild",
    "sir-r114-quickwit-drop-split-leftover3c-handoff",
)


RATE_LIMIT_THIN_META_IDS = (
    "rlb-r01-retry-after-seconds-ignored",
    "rlb-r01-retry-after-http-date-skew",
    "rlb-r02-reset-epoch-ignored",
    "rlb-r02-retry-after-zero-ms",
    "rlb-r07-http-503-retry-after-2d91",
    "rlb-r07-token-bucket-10rps-7e80",
    "rlb-r08-retry-after-zero-floor-5bb8",
    "rlb-r08-exp-min-retry-after-8d44",
)


class RateLimitBackoffDeclarationTests(DeclarationTestCase):
    """Issue #53: thin `meta` on the earliest rounds plus optional `reward.mid_reward`.

    The counts asserted here were derived by scanning every published record in
    the read-only mirror at
    ``~/rmems/hf/grok-4.6/rate-limit-backoff-trajectories`` (312 records across
    156 shards, 5148 steps, 0 parse failures), not transcribed from the issue.
    """

    DATASET = RATE_LIMIT
    ISSUE = 53
    HUB_ITEM = {
        "slug": "rate-limit-backoff-factory",
        "hub": RATE_LIMIT,
        "pretty": "Rate Limit Backoff Trajectories",
        "blurb": "API leftover-budget header vs naive-RPS episodes.",
        "tags": [
            "synthetic-data",
            "agentic-workflows",
            "grok-4.6",
            "provenance",
            "trajectories",
            "rate-limit",
        ],
    }
    SUMMARY = publisher.PayloadSummary(
        records=312,
        bytes_=2426868,
        first="r01",
        last="r156",
        names=["batch-r01.jsonl", "batch-r114.jsonl", "batch-r135.jsonl"],
    )

    def test_declaration_matches_the_observed_union_schema(self):
        self.assertEqual(feature_names(self.declaration["features"]), EPISODE_FIELD_ORDER)
        names = self.names()
        # Every top-level field is on all 312 records: unlike the sibling dumps
        # nothing here is optional at the top level, `plan` included.
        for name, feature in names.items():
            with self.subTest(field=name):
                self.assertNotIn("optional", feature, f"{name} is on every record")
        # The two key-bags the viewer's cast died on.
        self.assertEqual(names["meta"]["dtype"], "json")
        self.assertEqual(names["reward"]["dtype"], "json")
        self.assertEqual(self.declaration["issues"], [53])

    def test_steps_keep_the_public_decision_basis_and_a_json_arg_bag(self):
        children = by_name(self.feature("steps")["list"])
        self.assertEqual(set(children), STEP_FIELDS)
        self.assertEqual(children["n"]["dtype"], "int64")
        self.assertEqual(children["decision_basis"]["dtype"], "string")
        # 4831 of 5148 steps carry it; the rest read back as null.
        self.assertTrue(children["reflection"]["optional"])
        self.assertIn("4831 of 5148 steps", children["reflection"]["note"])
        tool_call = self.tool_call_features(children)
        self.assertEqual(set(tool_call), TOOL_CALL_FIELDS)
        self.assertEqual(tool_call["name"]["dtype"], "string")
        self.assertEqual(tool_call["args"]["dtype"], "json")

    def test_key_bag_columns_are_declared_json(self):
        self.assert_json_columns(EPISODE_JSON_COLUMNS)

    def test_reward_note_records_the_optional_mid_reward_count(self):
        names = self.names()
        # The issue's headline optional key: 136 of 312 records add it.
        self.assertIn("`mid_reward` on 136", names["reward"]["note"])
        self.assertIn("`handoff` / `xfailed` on 7", names["reward"]["note"])
        # `plant` and `lane` are the meta keys that no other record carries.
        self.assertIn("`plant` on 10", names["meta"]["note"])
        self.assertIn("`lane` on 8", names["meta"]["note"])

    def test_schema_note_attributes_thin_meta_to_all_four_batches(self):
        note = self.declaration["note"]
        for batch in ("r01", "r02", "r07", "r08"):
            with self.subTest(batch=batch):
                self.assertIn(f"`batch-{batch}.jsonl`", note)

    def test_card_front_matter_declares_the_default_config_over_raw_batches(self):
        self.assert_front_matter_declares_default_config(
            FEATURES_YAML,
            META_JSON_YAML,
            REWARD_JSON_YAML,
            ARGS_JSON_YAML,
            # Card-only annotations must never be read back as a feature type.
            absent=("optional",),
        )

    def test_card_body_discloses_the_twelve_dest_stamped_mill_records(self):
        self.assertIn(VIEWER_SCHEMA_HEADING, self.card)
        self.assertNotIn(NOT_DECLARED, self.card)
        self.assertIn(DISCLOSURES_HEADING, self.card)
        # Issue #53 claimed "no leftover-mill mix and no foreign factory"; the
        # mirror carries 10 `gql-` rows (#44's count) plus 2 `sir-` rows.
        self.assert_card_names_records(RATE_LIMIT_GQL_MILL_IDS + RATE_LIMIT_SIR_MILL_IDS)
        self.assert_card_names_records(RATE_LIMIT_THIN_META_IDS)
        self.assert_card_has(REFLECTION_OPTIONAL_ROW, "issues/53", "issues/44")


if __name__ == "__main__":
    unittest.main()
