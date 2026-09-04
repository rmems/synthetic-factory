#!/usr/bin/env python3
"""Issue #56 leaf tests for the per-dataset card schema declaration."""

import unittest

from card_schema_test_support import (
    EPISODE_FIELDS,
    EPISODE_JSON_COLUMNS,
    FEATURES_YAML,
    META_JSON_YAML,
    NOT_DECLARED,
    REFLECTION_OPTIONAL_ROW,
    REWARD_JSON_YAML,
    VIEWER_SCHEMA_HEADING,
    DeclarationTestCase,
    publisher,
)

AUTHZ_REGRESSION = "authz-regression-trajectories"


class AuthzRegressionDeclarationTests(DeclarationTestCase):
    """Issue #56: thin `meta` vs designed/domain/stack plus reward extras.

    Every count asserted here was derived by scanning the untouched public
    mirror at ``~/rmems/hf/grok-4.6/authz-regression-trajectories``: 3518
    records over 1759 shards, 59188 steps, 0 parse failures.
    """

    DATASET = AUTHZ_REGRESSION
    ISSUE = 56
    HUB_ITEM = {
        "slug": "authz-regression-factory",
        "hub": AUTHZ_REGRESSION,
        "pretty": "Authz Regression Trajectories",
        "blurb": "Authorization IDOR / BFLA leftover-mechanic episodes.",
        "tags": ["synthetic-data", "trajectories", "authz", "security", "idor"],
    }
    SUMMARY = publisher.PayloadSummary(
        records=3518,
        bytes_=21248000,
        first="r01",
        last="r1759",
        names=["batch-r01.jsonl", "batch-r1459.jsonl", "batch-r1759.jsonl"],
    )

    def test_declaration_matches_the_observed_union_schema(self):
        names = self.names()
        self.assertEqual(set(names), EPISODE_FIELDS | {"state"})
        # `plan` is on all 3518 records here, unlike the #36 dataset.
        self.assertNotIn("optional", names["plan"])
        self.assertEqual(names["meta"]["dtype"], "json")
        self.assertEqual(names["reward"]["dtype"], "json")
        _steps, tool_call = self.assert_episode_steps(names, "7181 of 59188 steps")
        self.assertIn("7 distinct key sets across 6 tools", tool_call["args"]["note"])
        self.assertIn("`read` uses `{path}` on 14678 steps", tool_call["args"]["note"])
        self.assertIn("`{offset, path}` on 3", tool_call["args"]["note"])
        self.assertEqual(self.declaration["issues"], [56])

    def test_state_is_optional_and_declared_as_a_uniform_struct(self):
        state = self.names()["state"]
        self.assertTrue(state["optional"])
        self.assertIn("480 of 3518", state["note"])
        # All 480 carry both keys with constant string values, so `state` is a
        # castable struct rather than a key-bag; it stays out of the json set.
        self.assertEqual(
            [child["name"] for child in state["struct"]], ["sim_or_real", "domain"]
        )
        self.assertEqual(
            {child["dtype"] for child in state["struct"]}, {"string"}
        )

    def test_key_bag_columns_are_declared_json(self):
        self.assert_json_columns(EPISODE_JSON_COLUMNS)

    def test_card_front_matter_declares_the_default_config_over_raw_batches(self):
        self.assert_front_matter_declares_default_config(
            FEATURES_YAML,
            META_JSON_YAML,
            REWARD_JSON_YAML,
            "  - name: state\n    struct:\n    - name: sim_or_real\n",
        )

    def test_card_body_discloses_the_ten_dest_stamped_leftovers(self):
        self.assert_card_has(
            VIEWER_SCHEMA_HEADING,
            "`sir-r1459-sqlite-vec-veci-leftover-lll-rebuild`",
            "`sir-r1463-os-drop-ism-leftover-lll-handoff`",
            "| `state` | optional |",
            REFLECTION_OPTIONAL_ROW,
            "/issues/43",
            "/issues/44",
        )
        self.assertNotIn(NOT_DECLARED, self.card)

    def test_card_body_states_the_derived_reward_split(self):
        # The reward extras are not the leftover-mill discriminator: 575 of the
        # 580 handoff/xfailed rows are ordinary `azr-*` episodes, and `retries`
        # is the key that is confined to the 5 dest-stamped rebuild rows.
        self.assert_card_has(
            "575 of those 580 are ordinary `azr-*`",
            "5 `sir-*-rebuild` rows",
            "no dest-stamped record has only the base reward key set",
        )


if __name__ == "__main__":
    unittest.main()
