#!/usr/bin/env python3
"""Issue #37 leaf tests for the per-dataset card schema declaration."""

import unittest

from card_schema_test_support import (
    FEATURES_YAML,
    NOT_DECLARED,
    STEP_FIELDS,
    TOOL_CALL_FIELDS,
    VIEWER_SCHEMA_HEADING,
    DeclarationTestCase,
    by_name,
    publisher,
)


EXPECTED_FEATURE_MANIFEST = (
    ("id", "string", False),
    ("lesson_category", "string", True),
    ("goal", "string", True),
    ("outcome", "string", True),
    ("chosen", "struct", False),
    ("chosen.goal", "string", True),
    ("chosen.steps", "list", False),
    ("chosen.steps[].n", "int64", False),
    ("chosen.steps[].decision_basis", "string", False),
    ("chosen.steps[].tool_call", "struct", False),
    ("chosen.steps[].tool_call.name", "string", False),
    ("chosen.steps[].tool_call.args", "json", False),
    ("chosen.steps[].observation", "string", False),
    ("chosen.steps[].reflection", "string", True),
    ("chosen.outcome", "string", False),
    ("chosen.reward", "json", False),
    ("rejected", "struct", False),
    ("rejected.goal", "string", True),
    ("rejected.steps", "list", False),
    ("rejected.steps[].n", "int64", False),
    ("rejected.steps[].decision_basis", "string", False),
    ("rejected.steps[].tool_call", "struct", False),
    ("rejected.steps[].tool_call.name", "string", False),
    ("rejected.steps[].tool_call.args", "json", False),
    ("rejected.steps[].observation", "string", False),
    ("rejected.steps[].reflection", "string", True),
    ("rejected.outcome", "string", False),
    ("rejected.reward", "json", False),
    ("critique", "string", False),
    ("reward", "json", False),
    ("meta", "json", False),
)


def _walk_features(features, prefix):
    """Yield (path, encoding-or-dtype, optional) rows in declaration order."""
    child_prefixes = {"list": "{path}[].", "struct": "{path}."}
    for feature in features:
        path = f"{prefix}{feature['name']}"
        encodings = [key for key in ("dtype", "list", "struct") if key in feature]
        if len(encodings) != 1:
            raise AssertionError(f"{path} has {len(encodings)} feature encodings")
        encoding = encodings[0]
        yield (
            path,
            feature[encoding] if encoding == "dtype" else encoding,
            feature.get("optional", False),
        )
        if encoding in child_prefixes:
            child_prefix = child_prefixes[encoding].format(path=path)
            yield from _walk_features(feature[encoding], child_prefix)


def feature_manifest(features, prefix=""):
    """Flatten a declaration without consulting the independent expected manifest."""
    return tuple(_walk_features(features, prefix))


class ToolUsePreferenceDeclarationTests(DeclarationTestCase):
    """Issue #37: a preference triple whose steps are nested one branch deep.

    Unlike #36 the step struct is not a top-level column: `chosen` and
    `rejected` each carry their own `steps` / `outcome` / `reward`, so the
    union has to be declared twice and `reward` exists at two levels with two
    different key bags. The top-level union spans the published mirror (6192
    records, 147471 steps) and the current producer contract.
    """

    DATASET = "tool-use-preference-pairs"
    ISSUE = 37
    HUB_ITEM = {
        "slug": "tool-use-preference-factory",
        "hub": DATASET,
        "pretty": "Tool Use Preference Pairs",
        "blurb": "Tool-use leftover-fork chosen/rejected preference pairs.",
        "tags": ["synthetic-data", "preference-data"],
    }
    SUMMARY = publisher.PayloadSummary(
        records=6192,
        bytes_=55617283,
        first="r01",
        last="r2064",
        names=["batch-r01.jsonl", "batch-r2064.jsonl"],
    )

    def test_complete_feature_manifest_matches_the_independent_contract_scan(self):
        # This oracle is intentionally separate from the declaration: it combines
        # the read-only published-data census with the current producer contract,
        # so omitted paths, wrong fixed dtypes, and incorrect optional flags fail.
        self.assertEqual(feature_manifest(self.declaration["features"]), EXPECTED_FEATURE_MANIFEST)

    def test_declaration_matches_the_published_and_producer_union_schema(self):
        names = self.names()
        self.assertEqual(
            set(names),
            {
                "id",
                "lesson_category",
                "goal",
                "outcome",
                "chosen",
                "rejected",
                "critique",
                "reward",
                "meta",
            },
        )
        # Historical rows omit lesson_category; current rows omit the historical
        # record-level outcome and may move the shared goal into both branches.
        self.assertEqual(
            [name for name, feature in names.items() if feature.get("optional")],
            ["lesson_category", "goal", "outcome"],
        )
        self.assertEqual(names["lesson_category"]["dtype"], "string")
        self.assertEqual(names["goal"]["dtype"], "string")
        self.assertEqual(names["outcome"]["dtype"], "string")
        self.assertEqual(names["reward"]["dtype"], "json")
        self.assertEqual(names["meta"]["dtype"], "json")
        self.assertEqual(self.declaration["issues"], [37])

    def test_both_branches_declare_the_same_nested_step_union(self):
        names = self.names()
        for side in ("chosen", "rejected"):
            branch = by_name(names[side]["struct"])
            self.assertEqual(set(branch), {"goal", "steps", "outcome", "reward"}, side)
            self.assertEqual(branch["goal"]["dtype"], "string", side)
            self.assertTrue(branch["goal"]["optional"], side)
            self.assertEqual(branch["outcome"]["dtype"], "string", side)
            # The per-branch reward is its own key bag, not the record-level one.
            self.assertEqual(branch["reward"]["dtype"], "json", side)
            steps = by_name(branch["steps"]["list"])
            self.assertEqual(set(steps), STEP_FIELDS, side)
            self.assertEqual(steps["n"]["dtype"], "int64", side)
            self.assertTrue(steps["reflection"]["optional"], side)
            tool_call = by_name(steps["tool_call"]["struct"])
            self.assertEqual(set(tool_call), TOOL_CALL_FIELDS, side)
            self.assertEqual(tool_call["name"]["dtype"], "string", side)
            # Heterogeneous `body` values are why args cannot be a struct.
            self.assertEqual(tool_call["args"]["dtype"], "json", side)

    def test_key_bag_columns_are_declared_json(self):
        self.assert_json_columns(
            [
                "chosen.steps[].tool_call.args",
                "chosen.reward",
                "rejected.steps[].tool_call.args",
                "rejected.reward",
                "reward",
                "meta",
            ]
        )

    def test_card_front_matter_declares_the_default_config_over_raw_batches(self):
        front_matter = self.assert_front_matter_declares_default_config(
            FEATURES_YAML,
            "  - name: lesson_category\n    dtype: string\n",
            "  - name: outcome\n    dtype: string\n",
            # Bare `n` is a YAML 1.1 boolean, so the step index must stay quoted.
            '      - name: "n"\n        dtype: int64\n',
            # Card-only annotations never reach the feature encoding.
            absent=("optional:", "note:"),
        )
        self.assertEqual(front_matter.count("- name: goal\n"), 3)
        # The two fields the datasets-server could not cast, once per branch.
        self.assertEqual(front_matter.count("      - name: reflection\n        dtype: string\n"), 2)
        self.assertEqual(front_matter.count("        - name: args\n          dtype: json\n"), 2)

    def test_card_body_documents_the_optional_reflection_and_empty_args(self):
        self.assert_card_has(
            VIEWER_SCHEMA_HEADING,
            "| `chosen.steps[].reflection` | optional | present on 55556 of 73741",
            "| `rejected.steps[].reflection` | optional | present on 57153 of 73730",
            "`chosen.steps[].tool_call.args`",
            "`rejected.steps[].tool_call.args`",
            "| `lesson_category` | optional |",
            "| `goal` | optional |",
            "| `outcome` | optional |",
            "| `chosen.goal` | optional |",
            "| `rejected.goal` | optional |",
        )
        self.assert_card_names_records(
            (
                "tup-r03-diatool-slot-fill",
                "tup-r03-diatool-oos-reject",
                "tup-r08-diatool-redundant-slot",
            )
        )
        self.assert_card_has(
            "no leftover-mill mix",
            "Current valid batches require a non-empty `lesson_category`",
        )
        self.assertNotIn(NOT_DECLARED, self.card)


if __name__ == "__main__":
    unittest.main()
