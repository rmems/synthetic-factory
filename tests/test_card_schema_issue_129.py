#!/usr/bin/env python3
"""Issue #67 leaf tests for the per-dataset card schema declaration."""

import json
import unittest

from card_schema_test_support import (
    EPISODE_FIELDS,
    EPISODE_JSON_COLUMNS,
    FEATURES_YAML,
    META_JSON_YAML,
    NOT_DECLARED,
    PLAN_PRESENT_ROW,
    PLAN_STRING_YAML,
    REFLECTION_OPTIONAL_ROW,
    VIEWER_SCHEMA_HEADING,
    DeclarationTestCase,
    mirror_path,
    needs_mirror,
    publisher,
)

INFRA_AS_CODE = "infra-as-code-trajectories"
INFRA_AS_CODE_MIRROR = mirror_path(INFRA_AS_CODE)

_SCAN: dict = {}

_needs_mirror = needs_mirror(INFRA_AS_CODE_MIRROR)


def _scan_mirror():
    """Read every published shard once and memoize it for the whole module."""
    if "scan" in _SCAN:
        return _SCAN["scan"]
    payloads = sorted(INFRA_AS_CODE_MIRROR.glob("batch-*.jsonl"))
    per_shard = []
    for payload in payloads:
        with payload.open(encoding="utf-8") as handle:
            per_shard.append(
                (payload.name, [json.loads(line) for line in handle if line.strip()])
            )
    records = [record for _name, rows in per_shard for record in rows]
    _SCAN["scan"] = (per_shard, records)
    return _SCAN["scan"]


def _reward_census(records):
    """Per-key record counts plus the value type census of `reward.handoff`."""
    reward_counts: dict = {}
    handoff_types: dict = {}
    for record in records:
        for key, value in record["reward"].items():
            reward_counts[key] = reward_counts.get(key, 0) + 1
            if key == "handoff":
                kind = type(value).__name__
                handoff_types[kind] = handoff_types.get(kind, 0) + 1
    return reward_counts, handoff_types


def _reflection_rounds(records):
    """The `meta.round` of every step that carries a `reflection`."""
    return [
        record["meta"]["round"]
        for record in records
        for step in record["steps"]
        if "reflection" in step
    ]


def _meta_split(records):
    """The thin-`meta` record count and the sorted rounds of the wide records."""
    thin = sum(
        1
        for record in records
        if set(record["meta"]) == {"factory", "generator", "round"}
    )
    wide_rounds = sorted(
        record["meta"]["round"] for record in records if "kind" in record["meta"]
    )
    return thin, wide_rounds


class InfraAsCodeDeclarationTests(DeclarationTestCase):
    """Issue #67: thin `meta` vs the `plant` / `kind` rounds kills the cast."""

    DATASET = INFRA_AS_CODE
    ISSUE = 67
    HUB_ITEM = {
        "slug": "infra-as-code-factory",
        "hub": INFRA_AS_CODE,
        "pretty": "Infra As Code Trajectories",
        "blurb": "Terraform/Kubernetes leftover-object IaC repair.",
        "tags": ["synthetic-data", "trajectories", "terraform", "kubernetes", "iac"],
    }
    SUMMARY = publisher.PayloadSummary(
        records=5208,
        bytes_=29388051,
        first="r01",
        last="r2604",
        names=["batch-r01.jsonl", "batch-r1416.jsonl", "batch-r2604.jsonl"],
    )

    def test_declaration_matches_the_observed_union_schema(self):
        names = self.names()
        self.assertEqual(set(names), EPISODE_FIELDS)
        # `plan` is a string on all 5208 records here; the worked example's
        # optional `plan` must not be copied over.
        self.assertEqual(names["plan"]["dtype"], "string")
        self.assertNotIn("optional", names["plan"])
        self.assertEqual(names["meta"]["dtype"], "json")
        self.assertEqual(names["reward"]["dtype"], "json")
        self.assert_episode_steps(names, "17436 of 87554")
        self.assertEqual(self.declaration["issues"], [67])

    def test_key_bag_columns_are_declared_json(self):
        self.assert_json_columns(EPISODE_JSON_COLUMNS)

    def test_meta_note_records_the_split_the_viewer_dies_on(self):
        meta = self.feature("meta")
        # 4190 thin + 1018 wide = 5208 records; the wide rounds are contiguous.
        for fragment in ("1018", "78-586", "4190", "1-77", "587-2604", "sim_or_real"):
            self.assertIn(fragment, meta["note"])

    def test_reward_note_names_the_only_type_varying_key(self):
        reward = self.feature("reward")
        # `handoff` is the single int-or-string key; the tests_* counters are not.
        self.assertIn("`handoff` is the only key whose value type varies", reward["note"])
        for singleton in ("wrong_cluster_apply", "replicas", "targets_healthy"):
            self.assertIn(singleton, reward["note"])

    # -- Re-derived from the payload, not from the declaration -------------
    #
    # Rounds 1417-2604 were published on 2026-08-26, after the issue #67
    # census was derived at the r1416 frontier. The three mirror-backed tests
    # below re-derive the declared totals from the payload, so a declaration
    # still carrying the r1416-frontier counts fails, and they pin the claim
    # that the growth widened nothing: no new reward key, no new tool, no new
    # arg key, and no `reflection` outside rounds 1-1416.

    @_needs_mirror
    def test_published_mirror_layout_matches_the_r2604_release(self):
        per_shard, records = _scan_mirror()
        self.assertEqual(len(per_shard), 2604)
        self.assertEqual({len(rows) for _name, rows in per_shard}, {2})
        self.assertEqual(len(records), 5208)
        self.assertEqual(len({record["id"] for record in records}), 5208)

    @_needs_mirror
    def test_published_mirror_reconciles_the_reflection_and_meta_growth(self):
        _per_shard, records = _scan_mirror()
        steps_total = sum(len(record["steps"]) for record in records)
        reflections = _reflection_rounds(records)
        thin, wide_rounds = _meta_split(records)
        self.assertEqual(steps_total, 87554)
        self.assertEqual(len(reflections), 17436)
        self.assertLessEqual(max(reflections), 1416)
        self.assertEqual(thin, 4190)
        self.assertEqual(len(wide_rounds), 1018)
        self.assertEqual((wide_rounds[0], wide_rounds[-1]), (78, 586))
        self.assertIn(f"on all {len(records)} records", self.feature("meta")["note"])
        self.assertIn(
            f"{len(reflections)} of {steps_total}",
            self.step_features(self.names())["reflection"]["note"],
        )

    @_needs_mirror
    def test_published_mirror_reconciles_the_reward_census(self):
        _per_shard, records = _scan_mirror()
        reward_counts, handoff_types = _reward_census(records)
        self.assertEqual(reward_counts["tests_passed"], 5180)
        self.assertEqual(reward_counts["handoff"], 2606)
        self.assertEqual(reward_counts["tests_failed"], 2576)
        self.assertEqual(handoff_types, {"int": 2593, "str": 13})
        self.assertIn(
            f"`handoff` on {reward_counts['handoff']}", self.feature("reward")["note"]
        )

    def test_card_front_matter_declares_the_default_config_over_raw_batches(self):
        self.assert_front_matter_declares_default_config(
            FEATURES_YAML, META_JSON_YAML, PLAN_STRING_YAML
        )

    def test_card_body_owns_the_leftover_mechanic_without_claiming_a_mill(self):
        self.assertIn(VIEWER_SCHEMA_HEADING, self.card)
        self.assertNotIn(NOT_DECLARED, self.card)
        self.assert_card_has(
            REFLECTION_OPTIONAL_ROW,
            PLAN_PRESENT_ROW,
            # The 13 string-valued handoff ids are named on the card.
            "`iac-r03-b-helm-reuse-values-tag-drift`",
            "`iac-r27-b-helm-history-max-zero`",
            # Same-factory leftover naming is disclosed as the advertised mechanic,
            # and the inbound-mill disclosure defers to the destination dumps.
            "advertised mechanic",
            "There is no inbound leftover mill in this dataset",
            "/issues/43",
            "/issues/44",
        )


if __name__ == "__main__":
    unittest.main()
