#!/usr/bin/env python3
"""Issue #62 leaf tests for the per-dataset card schema declaration."""

import unittest

from card_schema_test_support import (
    DEFAULT_DATA_FILES,
    EPISODE_FIELD_ORDER,
    META_JSON_YAML,
    NOT_DECLARED,
    PLAN_PRESENT_ROW,
    REFLECTION_OPTIONAL_ROW,
    VIEWER_SCHEMA_HEADING,
    DeclarationTestCase,
    card_schema,
    feature_names,
    publisher,
)

EVAL_HARNESS = "eval-harness-trajectories"


class EvalHarnessDeclarationTests(DeclarationTestCase):
    """Issue #62: thin `meta` vs `designed`/`domain`, plus `plan` string-or-list."""

    DATASET = EVAL_HARNESS
    ISSUE = 62
    HUB_ITEM = {
        "slug": "eval-harness-trajectory-factory",
        "hub": EVAL_HARNESS,
        "pretty": "Eval Harness Trajectories",
        "blurb": "DeepEval/pytest eval-loop leftover-judge episodes.",
        "tags": ["synthetic-data", "trajectories", "evaluation", "pytest"],
    }
    SUMMARY = publisher.PayloadSummary(
        records=2203,
        bytes_=12773376,
        first="r01",
        last="r1104",
        names=["batch-r01.jsonl", "batch-r1104.jsonl"],
    )

    def test_declaration_matches_the_observed_union_schema(self):
        self.assertEqual(feature_names(self.declaration["features"]), EPISODE_FIELD_ORDER)
        names = self.names()
        self.assertEqual(names["meta"]["dtype"], "json")
        self.assertEqual(names["reward"]["dtype"], "json")
        self.assert_episode_steps(names)
        self.assertEqual(self.declaration["issues"], [62])

    def test_plan_is_a_mandatory_json_union_not_an_optional_string(self):
        # `plan` is on all 2203 records, so it must not be copied as optional
        # from the #36 example; it is a string on 1961 and a list on 242, which
        # is the union that breaks a `string` cast.
        plan = self.feature("plan")
        self.assertEqual(plan["dtype"], "json")
        self.assertNotIn("optional", plan)
        self.assertIn("1961", plan["note"])
        self.assertIn("242", plan["note"])

    def test_type_varying_and_key_bag_columns_are_declared_json(self):
        self.assert_json_columns(["plan", "steps[].tool_call.args", "reward", "meta"])
        self.assertIn("Columns declared as `json` may differ", self.card)
        self.assertNotIn("Key-bag columns are declared", self.card)

    def test_reward_note_accounts_for_the_four_twice_occurring_keys(self):
        reward = self.feature("reward")
        for key in ("val_mean_after", "invent_after", "ok_after", "clean_after"):
            with self.subTest(key=key):
                self.assertIn(key, reward["note"])
        self.assertIn("69 keys appear on exactly one record", reward["note"])

    def test_declared_data_files_cover_the_published_batches(self):
        self.assertEqual(self.declaration["data_files"], DEFAULT_DATA_FILES)
        self.assertEqual(
            card_schema.payload_coverage_errors(
                self.declaration,
                ["batch-r01.jsonl", "batch-r132.jsonl", "batch-r1104.jsonl"],
            ),
            [],
        )

    def test_card_front_matter_declares_the_default_config_over_raw_batches(self):
        self.assert_front_matter_declares_default_config(
            "  - name: plan\n    dtype: json\n",
            META_JSON_YAML,
            absent=("optional",),
        )

    def test_card_body_discloses_the_five_sparse_reward_mill_records(self):
        self.assertIn(VIEWER_SCHEMA_HEADING, self.card)
        self.assertNotIn(NOT_DECLARED, self.card)
        self.assert_card_names_records(
            (
                "srl-r641-networkd-dhcp-ipv4-only-c67a",
                "srl-r642-chrony-maxslewrate-vs-ntpd-ffb5",
                "srl-r643-nft-flowtable-timeout-vs-ipt-035c",
                "srl-r644-podman-events-logger-journald-e10f",
                "srl-r645-buildah-format-oci-vs-docker-b703",
            )
        )
        self.assert_card_has("issues/43", "factory-mix leftover-mill payload")
        self.assertNotIn("dest-stamped leftover-mill payload", self.card)
        self.assert_card_has(PLAN_PRESENT_ROW, REFLECTION_OPTIONAL_ROW)
        self.assertNotIn("scripts/eval_harness_unique_mill", self.card)
        self.assertIn("same-factory `evh-*` records", self.card)


if __name__ == "__main__":
    unittest.main()
