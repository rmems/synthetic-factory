#!/usr/bin/env python3
"""Issue #52 leaf tests for the per-dataset card schema declaration."""

import re
import unittest
from pathlib import Path

from card_schema_test_support import (
    EPISODE_FIELDS,
    EPISODE_JSON_COLUMNS,
    FEATURES_YAML,
    META_JSON_YAML,
    NOT_DECLARED,
    NO_FOREIGN_PAYLOAD,
    PLAN_PRESENT_ROW,
    REFLECTION_OPTIONAL_ROW,
    REWARD_JSON_YAML,
    TOOL_CALL_FIELDS,
    VIEWER_SCHEMA_HEADING,
    DeclarationTestCase,
    bag_key_counts,
    feature_index,
    iter_steps,
    mirror_path,
    needs_mirror,
    publisher,
    scan_mirror,
)

WEBSOCKET_RECONNECT = "websocket-reconnect-trajectories"
WEBSOCKET_RECONNECT_MIRROR = mirror_path(WEBSOCKET_RECONNECT)

_needs_mirror = needs_mirror(WEBSOCKET_RECONNECT_MIRROR)


def _scan_mirror():
    """Re-derive the declaration's payload facts from the published shards.

    Memoized: several tests below re-derive different facts from one scan.
    """
    return scan_mirror(WEBSOCKET_RECONNECT_MIRROR)


class WebsocketReconnectDeclarationTests(DeclarationTestCase):
    """Issue #52: thin `meta` in batch-r01 vs `designed`/`domain`/`stack` later."""

    DATASET = WEBSOCKET_RECONNECT
    ISSUE = 52
    HUB_ITEM = {
        "slug": "websocket-reconnect-factory",
        "hub": WEBSOCKET_RECONNECT,
        "pretty": "Websocket Reconnect Trajectories",
        "blurb": "WebSocket leftover-resume / reconnect episodes.",
        "tags": ["synthetic-data", "trajectories", "websocket"],
    }
    SUMMARY = publisher.PayloadSummary(
        records=322,
        bytes_=2375680,
        first="r01",
        last="r161",
        names=["batch-r01.jsonl", "batch-r161.jsonl"],
    )

    def test_declaration_matches_the_observed_union_schema(self):
        names = self.names()
        self.assertEqual(set(names), EPISODE_FIELDS)
        # Unlike #36's dataset, every one of the 322 records carries a `plan`.
        self.assertNotIn("optional", names["plan"])
        self.assertEqual(names["plan"]["dtype"], "string")
        self.assertEqual(names["meta"]["dtype"], "json")
        self.assertEqual(names["reward"]["dtype"], "json")
        _steps, tool_call = self.assert_episode_steps(names, "5081 of 5314 steps")
        self.assertEqual(set(tool_call), TOOL_CALL_FIELDS)
        self.assertEqual(self.declaration["issues"], [52])

    def test_key_bag_columns_are_declared_json(self):
        self.assert_json_columns(EPISODE_JSON_COLUMNS)

    def test_meta_note_records_the_thin_and_lane_subsets(self):
        meta = self.feature("meta")
        for key in ("kind", "seed", "designed", "domain", "stack"):
            self.assertIn(f"`{key}`", meta["note"])
        self.assertIn("312 of 322", meta["note"])
        self.assertIn("`lane` on 12 of 322", meta["note"])

    def test_card_front_matter_declares_the_default_config_over_raw_batches(self):
        self.assert_front_matter_declares_default_config(
            FEATURES_YAML, META_JSON_YAML, REWARD_JSON_YAML
        )

    def test_card_body_discloses_the_ten_thin_meta_records(self):
        self.assert_card_has(
            VIEWER_SCHEMA_HEADING,
            "`wsr-r01-resubscribe-on-reconnect`",
            "`wsr-r11-close-1005-backoff-7c2d`",
            "`meta.lane`",
            NO_FOREIGN_PAYLOAD,
            "does not infer generator-file provenance",
        )
        self.assertNotIn("mill_wsr_leftover", self.card)
        self.assert_card_has(REFLECTION_OPTIONAL_ROW, PLAN_PRESENT_ROW)
        self.assertNotIn(NOT_DECLARED, self.card)

    def test_card_payload_prose_names_real_batch_shards(self):
        """Every `data/raw/batch-*.jsonl` the card prints must be a real shard.

        Regression guard for a fixture that passed `first="01"` / `last="161"`
        and so advertised `data/raw/batch-01.jsonl` -- a filename the publisher
        can never emit. `batch_label` derives labels as `r{number:02d}`, and
        `snapshot_one` only fills `first`/`last` when every shard is named
        `batch-{label}.jsonl`, so the rendered range is always `batch-rNN`.
        """
        printed = set(re.findall(r"data/raw/(batch-[0-9a-z]+\.jsonl)", self.card))
        self.assertIn("batch-r01.jsonl", printed)
        self.assertIn("batch-r161.jsonl", printed)
        for name in printed:
            with self.subTest(name=name):
                self.assertIsNotNone(
                    publisher.BATCH_NAME_RE.fullmatch(name),
                    f"{name} is not a shard name the publisher can produce",
                )
                label = publisher.batch_label(Path(name))
                self.assertEqual(f"batch-{label[2]}.jsonl", name)

    # -- Re-derived from the payload, not from the declaration -------------
    #
    # The other tests in this class compare the declaration against constants
    # typed alongside it, so they cannot catch the failure this declaration
    # exists to prevent: drifting away from what was actually published. The
    # tests below scan the read-only mirror and assert the declaration still
    # describes it.

    @_needs_mirror
    def test_published_shard_and_record_counts_match_the_declaration(self):
        shards, records = _scan_mirror()
        self.assertEqual(len(shards), 161)
        self.assertEqual(len(records), 322)

    @_needs_mirror
    def test_every_record_carries_exactly_the_declared_top_level_fields(self):
        _shards, records = _scan_mirror()
        names, optional = feature_index(self.declaration["features"])
        for shard, record in records:
            self.assertEqual(set(record) - set(names), set(), shard)
            self.assertEqual(set(names) - set(record) - optional, set(), shard)
            self.assertIsInstance(record["plan"], str)
            self.assertTrue(record["plan"].strip(), record["id"])
        self.assertIn(f"all {len(records)} records", names["plan"]["note"])

    @_needs_mirror
    def test_every_step_carries_exactly_the_declared_step_fields(self):
        _shards, records = _scan_mirror()
        names, _optional = feature_index(self.declaration["features"])
        step_names, step_optional = feature_index(names["steps"]["list"])
        for shard, step in iter_steps(records):
            self.assertEqual(set(step) - set(step_names), set(), shard)
            self.assertEqual(set(step_names) - set(step) - step_optional, set(), shard)
            self.assertEqual(set(step["tool_call"]), {"name", "args"})

    @_needs_mirror
    def test_step_note_matches_the_published_reflection_count(self):
        _shards, records = _scan_mirror()
        names, _optional = feature_index(self.declaration["features"])
        step_names, _step_optional = feature_index(names["steps"]["list"])
        steps = [step for _shard, step in iter_steps(records)]
        reflections = sum(1 for step in steps if "reflection" in step)
        self.assertIn(
            f"present on {reflections} of {len(steps)} steps",
            step_names["reflection"]["note"],
        )

    @_needs_mirror
    def test_both_key_bags_are_dicts_with_the_declared_always_present_keys(self):
        _shards, records = _scan_mirror()
        total = len(records)
        for bag in ("reward", "meta"):
            for _shard, record in records:
                self.assertIsInstance(record[bag], dict)
        self.assertEqual(
            {k for k, v in bag_key_counts(records, "meta").items() if v == total},
            {"factory", "generator", "round"},
        )
        self.assertEqual(
            {k for k, v in bag_key_counts(records, "reward").items() if v == total},
            {"success", "tests_passed", "cost_steps"},
        )

    @_needs_mirror
    def test_meta_note_matches_the_published_key_counts(self):
        _shards, records = _scan_mirror()
        names, _optional = feature_index(self.declaration["features"])
        counts = bag_key_counts(records, "meta")
        total = len(records)
        meta_note = names["meta"]["note"]
        self.assertIn(f"`stack` on {counts['kind']} of {total}", meta_note)
        self.assertIn(f"`lane` on {counts['lane']} of {total}", meta_note)

    @_needs_mirror
    def test_reward_note_matches_the_published_key_counts(self):
        _shards, records = _scan_mirror()
        names, _optional = feature_index(self.declaration["features"])
        counts = bag_key_counts(records, "reward")
        total = len(records)
        reward_note = names["reward"]["note"]
        self.assertIn(f"`wasted_calls` on {counts['retries']} of {total}", reward_note)
        self.assertIn(
            f"`plan_changes` on {counts['plan_changes']} of {total}", reward_note
        )
        self.assertIn(f"`handoff` on {counts['handoff']}", reward_note)
        self.assertIn(f"`xfailed` on {counts['xfailed']}", reward_note)

    @_needs_mirror
    def test_disclosed_thin_meta_ids_are_exactly_the_records_without_kind(self):
        _shards, records = _scan_mirror()
        thin = {
            record["id"] for _shard, record in records if "kind" not in record["meta"]
        }
        declared = {
            record_id
            for item in self.declaration["disclosures"]
            if isinstance(item, dict)
            for record_id in item["ids"]
        }
        self.assertEqual(declared, thin)

    @_needs_mirror
    def test_two_thin_meta_records_sit_in_the_batch_the_cast_is_built_on(self):
        _shards, records = _scan_mirror()
        self.assertEqual(
            sum(
                1
                for shard, record in records
                if shard == "batch-r01.jsonl" and "kind" not in record["meta"]
            ),
            2,
        )

    @_needs_mirror
    def test_record_ids_are_unique_and_namespaced_to_this_factory(self):
        _shards, records = _scan_mirror()
        ids = [record["id"] for _shard, record in records]
        self.assertEqual(len(set(ids)), len(ids))
        self.assertTrue(all(record_id.startswith("wsr-") for record_id in ids))


if __name__ == "__main__":
    unittest.main()
