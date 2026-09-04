#!/usr/bin/env python3
"""Issue #42 leaf tests for the per-dataset card schema declaration."""

import unittest

from card_schema_test_support import (
    DEFAULT_DATA_FILES,
    EPISODE_JSON_COLUMNS,
    FEATURES_YAML,
    META_JSON_YAML,
    NOT_DECLARED,
    REWARD_JSON_YAML,
    TOOL_CALL_FIELDS,
    VIEWER_SCHEMA_HEADING,
    DeclarationTestCase,
    publisher,
)

SANDBOX_REFUSAL = "sandbox-refusal-trajectories"


class SandboxRefusalDeclarationTests(DeclarationTestCase):
    """Issue #42: optional case-type extras plus a two-keyset `reward`.

    Every number asserted here was derived by scanning the published mirror
    (1634 shards, 4902 records) rather than copied from the issue text.
    """

    DATASET = SANDBOX_REFUSAL
    ISSUE = 42
    HUB_ITEM = {
        "slug": "sandbox-refusal-factory",
        "hub": SANDBOX_REFUSAL,
        "pretty": "Sandbox Refusal Trajectories",
        "blurb": "Sandbox leftover-policy refusal / allow cases.",
        "tags": ["synthetic-data", "trajectories", "sandbox", "safety"],
    }
    # Exercise a later snapshot: reusable schema prose must not freeze the
    # r1634 record counts into every future card render.
    SUMMARY = publisher.PayloadSummary(
        records=5784,
        bytes_=18135666,
        first="r01",
        last="r1928",
        names=["batch-r01.jsonl", "batch-r1928.jsonl"],
    )

    def test_declaration_matches_the_observed_union_schema(self):
        names = self.names()
        self.assertIn("`family` is absent from rounds 1 to 358", self.declaration["note"])
        self.assertIn("reward object", self.declaration["note"])
        self.assertNotIn("four case-type extras", self.declaration["note"])
        self.assertEqual(
            set(names),
            {
                "id",
                "goal",
                "case_type",
                "should_refuse",
                "decision",
                "rationale",
                "steps",
                "outcome",
                "reward",
                "meta",
                "trigger",
                "redirect",
                "benign_twin",
                "vector",
                "family",
            },
        )
        self.assertEqual(names["should_refuse"]["dtype"], "bool")
        self.assertEqual(names["case_type"]["dtype"], "string")
        self.assertEqual(self.declaration["issues"], [42])
        self.assertEqual(self.declaration["data_files"], DEFAULT_DATA_FILES)

    def test_only_the_four_case_type_extras_are_optional(self):
        optional = {
            feature["name"]
            for feature in self.declaration["features"]
            if feature.get("optional")
        }
        # `trigger` sits next to the extras in the raw record but is on every
        # record, so declaring it optional would understate the payload.
        self.assertEqual(optional, {"redirect", "benign_twin", "vector", "family"})
        notes = {
            feature["name"]: feature.get("note", "")
            for feature in self.declaration["features"]
        }
        self.assertIn("every `correct_refusal` case", notes["redirect"])
        self.assertIn("every `incorrect_refusal` case", notes["benign_twin"])
        self.assertIn("every `missed_refusal` case", notes["vector"])
        self.assertIn("round 359 onward", notes["family"])

    def test_key_bag_columns_are_declared_json(self):
        self.assert_json_columns(EPISODE_JSON_COLUMNS)

    def test_steps_declare_the_public_decision_basis_and_no_reflection(self):
        steps = self.step_features(self.names())
        self.assertEqual(set(steps), {"n", "decision_basis", "tool_call", "observation"})
        tool_call = self.tool_call_features(steps)
        self.assertEqual(set(tool_call), TOOL_CALL_FIELDS)
        self.assertEqual(tool_call["args"]["dtype"], "json")

    def test_card_front_matter_declares_the_default_config_over_raw_batches(self):
        self.assert_front_matter_declares_default_config(
            FEATURES_YAML,
            REWARD_JSON_YAML,
            META_JSON_YAML,
            "  - name: should_refuse\n    dtype: bool\n",
            # The extras are plain strings; declaring them keeps the cast alive.
            "  - name: family\n    dtype: string\n",
        )

    def test_card_body_discloses_the_case_split_and_the_double_extra_record(self):
        self.assertIn(VIEWER_SCHEMA_HEADING, self.card)
        self.assertNotIn(NOT_DECLARED, self.card)
        self.assert_card_has(
            "one `correct_refusal`", "one `incorrect_refusal`", "one `missed_refusal`"
        )
        self.assert_card_lacks("4902", "1634 records", "1635")
        self.assert_card_has(
            "one-record surplus",
            "`sbox-r191-agents-md-token-exfil-refuse`",
            "| `redirect` | optional |",
            "| `benign_twin` | optional |",
            "| `vector` | optional |",
            "| `family` | optional |",
            "| `trigger` | present on every record |",
            "issues/42",
        )


if __name__ == "__main__":
    unittest.main()
