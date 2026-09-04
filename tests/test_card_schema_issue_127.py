#!/usr/bin/env python3
"""Issue #68 leaf tests for the per-dataset card schema declaration."""

import unittest

from card_schema_test_support import (
    ARGS_JSON_YAML,
    DISCLOSURES_HEADING,
    EPISODE_FIELDS,
    EPISODE_JSON_COLUMNS,
    FEATURES_YAML,
    META_JSON_YAML,
    NOT_DECLARED,
    PLAN_PRESENT_ROW,
    REFLECTION_OPTIONAL_ROW,
    REWARD_JSON_YAML,
    STEP_FIELDS,
    TOOL_CALL_FIELDS,
    TRAIN_SPLIT_YAML,
    VIEWER_SCHEMA_HEADING,
    DeclarationTestCase,
    publisher,
)

K8S_CRASHLOOP = "k8s-crashloop-trajectories"


class K8sCrashloopDeclarationTests(DeclarationTestCase):
    """Issue #68: thin `meta` vs the late `designed` / `plant` / `kind` records.

    Every count asserted here was derived from the published mirror
    (1643 shards, 3286 records, 55903 steps), not copied from the issue text.
    """

    MILL_IDS = (
        "gql-r1330-edgedb-globals-after-access-policy",
        "gql-r1330-edgedb-drop-session-globals",
        "gql-r1331-prisma-preview-client-after-generate",
        "gql-r1331-prisma-disable-preview-flags",
        "gql-r1332-gqlgen-gofield-after-bind-rename",
        "gql-r1332-gqlgen-drop-field-bind",
        "gql-r1333-juniper-field-with-after-executor",
        "gql-r1333-juniper-drop-executor-with",
        "gql-r1334-async-graphql-guard-after-complexity",
        "gql-r1334-async-graphql-disable-field-guard",
        "gql-r1335-absinthe-pipeline-after-phase-swap",
        "gql-r1335-absinthe-drop-pipeline-phase",
    )
    DESIGNED_PLANT_IDS = (
        "kcl-r1336-deploy-termination-grace-0-be0a",
        "kcl-r1336-deploy-startup-probe-fail-1-ed58",
        "kcl-r1337-deploy-share-process-namespace-332f",
        "kcl-r1337-deploy-fs-group-change-policy-df26",
        "kcl-r1338-sts-pod-management-parallel-0394",
        "kcl-r1338-cronjob-concurrency-forbid-b46b",
    )

    DATASET = K8S_CRASHLOOP
    ISSUE = 68
    HUB_ITEM = {
        "slug": "k8s-crashloop-factory",
        "hub": K8S_CRASHLOOP,
        "pretty": "K8S Crashloop Trajectories",
        "blurb": "Kubernetes CrashLoop leftover-field episodes.",
        "tags": ["synthetic-data", "kubernetes"],
    }
    SUMMARY = publisher.PayloadSummary(
        records=3286,
        bytes_=27423440,
        first="r01",
        last="r1643",
        names=["batch-r01.jsonl", "batch-r1330.jsonl", "batch-r1643.jsonl"],
    )

    def test_declaration_matches_the_observed_union_schema(self):
        names = self.names()
        self.assertEqual(set(names), EPISODE_FIELDS)
        self.assertEqual(self.declaration["issues"], [68])
        for scalar in ("id", "goal", "plan", "outcome"):
            with self.subTest(scalar=scalar):
                self.assertEqual(names[scalar]["dtype"], "string")
                self.assertNotIn("optional", names[scalar])
        self.assertEqual(names["meta"]["dtype"], "json")
        self.assertEqual(names["reward"]["dtype"], "json")
        self.assertIn("list", names["steps"])
        self.assertNotIn("dtype", names["steps"])
        steps = self.step_features(names)
        self.assertEqual(set(steps), STEP_FIELDS)
        self.assertEqual(steps["n"]["dtype"], "int64")
        for scalar in ("decision_basis", "observation", "reflection"):
            with self.subTest(step_scalar=scalar):
                self.assertEqual(steps[scalar]["dtype"], "string")
        self.assertTrue(steps["reflection"]["optional"])
        self.assertIn("struct", steps["tool_call"])
        self.assertNotIn("dtype", steps["tool_call"])
        tool_call = self.tool_call_features(steps)
        self.assertEqual(set(tool_call), TOOL_CALL_FIELDS)
        self.assertEqual(tool_call["name"]["dtype"], "string")
        self.assertEqual(tool_call["args"]["dtype"], "json")

    def test_plan_is_mandatory_here_unlike_the_worked_example(self):
        # `plan` is a string on all 3286 records in this dump. Copying the
        # optional `plan` of #36 would publish a claim the payload denies.
        plan = self.feature("plan")
        self.assertEqual(plan["dtype"], "string")
        self.assertNotIn("optional", plan)
        self.assertIn(PLAN_PRESENT_ROW, self.card)

    def test_key_bag_columns_are_declared_json(self):
        self.assert_json_columns(EPISODE_JSON_COLUMNS)

    def test_card_front_matter_declares_the_default_config_over_raw_batches(self):
        self.assert_front_matter_declares_default_config(
            TRAIN_SPLIT_YAML,
            FEATURES_YAML,
            META_JSON_YAML,
            REWARD_JSON_YAML,
            ARGS_JSON_YAML,
            # Card-only annotations must never be read back as a feature type.
            absent=("optional", "note:"),
        )

    def test_card_body_owns_the_dest_stamped_mill_rows_without_re_filing_them(self):
        self.assert_card_has(VIEWER_SCHEMA_HEADING, DISCLOSURES_HEADING)
        self.assert_card_names_records(self.MILL_IDS)
        # The 12 rows are attributed to the frozen census in #44, not re-filed.
        self.assertIn("issues/44", self.card)

    def test_card_body_keeps_the_designed_plant_outlier_with_this_issue(self):
        self.assert_card_names_records(self.DESIGNED_PLANT_IDS)
        self.assertIn("run_terminal_command", self.card)
        self.assertNotIn("issues/43", self.card)

    def test_card_body_separates_the_own_leftover_mechanic_from_the_mill(self):
        self.assert_card_has(
            "791 of the 3274 `kcl-*` records",
            "803 leftover-in-goal",
            REFLECTION_OPTIONAL_ROW,
        )
        self.assertNotIn(NOT_DECLARED, self.card)


if __name__ == "__main__":
    unittest.main()
