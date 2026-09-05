#!/usr/bin/env python3
"""Issue #45 leaf tests for the per-dataset card schema declaration."""

import unittest

from card_schema_test_support import (
    EPISODE_FIELD_ORDER,
    EPISODE_JSON_COLUMNS,
    FEATURES_YAML,
    META_JSON_YAML,
    NOT_DECLARED,
    REFLECTION_OPTIONAL_ROW,
    REWARD_JSON_YAML,
    VIEWER_SCHEMA_HEADING,
    DeclarationTestCase,
    feature_names,
    publisher,
)

SPARSE_REWARD = "sparse-reward-long-tasks"


class SparseRewardLongTasksDeclarationTests(DeclarationTestCase):
    """Issue #45: the union `reward` key-bag that broke the viewer's first cast.

    Every count asserted here was derived from the read-only mirror at
    ``~/rmems/hf/grok-4.6/sparse-reward-long-tasks`` (6551 records over 6551
    ``data/raw/batch-r*.jsonl`` shards, 0 parse failures), not from the issue
    text.
    """

    DATASET = SPARSE_REWARD
    ISSUE = 45
    # The Hub item and published-payload facts the card must render, derived
    # from the read-only mirror at ~/rmems/hf/grok-4.6/sparse-reward-long-tasks.
    HUB_ITEM = {
        "slug": "sparse-reward-long-task-factory",
        "hub": SPARSE_REWARD,
        "pretty": "Sparse Reward Long Tasks",
        "blurb": "Sparse-reward leftover-goal long tasks (final reward only).",
        "tags": ["synthetic-data", "sparse-reward", "long-horizon"],
    }
    SUMMARY = publisher.PayloadSummary(
        records=6551,
        bytes_=67907183,
        first="r01",
        last="r6551",
        names=["batch-r01.jsonl", "batch-r6551.jsonl"],
    )

    def test_declaration_matches_the_observed_union_schema(self):
        names = self.names()
        self.assertEqual(feature_names(self.declaration["features"]), EPISODE_FIELD_ORDER)
        # Unlike long-horizon-coding, every record here carries a `plan`.
        self.assertNotIn("optional", names["plan"])
        self.assertEqual(names["plan"]["dtype"], "string")
        self.assertEqual(names["meta"]["dtype"], "json")
        self.assertEqual(names["reward"]["dtype"], "json")
        _steps, tool_call = self.assert_episode_steps(names, "16252 of 211140 steps")
        self.assertEqual(tool_call["name"]["dtype"], "string")
        self.assertEqual(self.declaration["issues"], [45])

    def test_the_reward_key_bag_that_broke_the_cast_is_declared_json(self):
        # The viewer inferred struct<success: bool> from the early shards and
        # then could not cast terminal_only / horizon_steps. Both keys must be
        # named on the card, and `reward` must not be a struct.
        self.assert_json_columns(EPISODE_JSON_COLUMNS)
        reward_note = self.names()["reward"]["note"]
        for key in ("success", "terminal_only", "horizon_steps", "mid_reward_steps"):
            self.assertIn(f"`{key}`", reward_note)

    def test_card_front_matter_declares_the_default_config_over_raw_batches(self):
        self.assert_front_matter_declares_default_config(
            FEATURES_YAML,
            REWARD_JSON_YAML,
            META_JSON_YAML,
            # No card-only annotation may leak into the YAML block.
            absent=("optional:", "note:"),
        )

    def test_card_body_discloses_the_six_designed_leftover_mill_records(self):
        self.assertIn(VIEWER_SCHEMA_HEADING, self.card)
        self.assert_card_names_records(
            (
                "srl-r6134-networkd-dhcp-ipv4-only-c67a",
                "srl-r6135-chrony-maxslewrate-vs-ntpd-ffb5",
                "srl-r6136-nft-flowtable-timeout-vs-ipt-035c",
                "srl-r6137-podman-events-logger-journald-e10f",
                "srl-r6138-buildah-format-oci-vs-docker-b703",
                "srl-r6139-skopeo-dest-tls-verify-db0f",
            )
        )
        self.assertIn(REFLECTION_OPTIONAL_ROW, self.card)
        self.assertNotIn(NOT_DECLARED, self.card)

    def test_card_body_owns_this_factory_as_the_source_of_the_frozen_census(self):
        # #43 froze the published factory_mix census: the srl-* rows it names
        # live in other dumps, so this card discloses the direction.
        self.assert_card_has(
            "srl-r500-networkd-dhcp-ipv4-only-c67a",
            "observability-debug-trajectories",
            "eval-harness-trajectories",
            "/43",
        )


if __name__ == "__main__":
    unittest.main()
