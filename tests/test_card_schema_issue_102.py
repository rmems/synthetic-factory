#!/usr/bin/env python3
"""Issue #39 leaf tests for the per-dataset card schema declaration."""

import unittest

from card_schema_test_support import (
    ARGS_JSON_YAML,
    DEFAULT_DATA_FILES,
    DISCLOSURES_HEADING,
    EPISODE_FIELD_ORDER,
    EPISODE_JSON_COLUMNS,
    META_JSON_YAML,
    NOT_DECLARED,
    REFLECTION_OPTIONAL_ROW,
    REWARD_JSON_YAML,
    STEP_FIELD_ORDER,
    DeclarationTestCase,
    card_schema,
    feature_names,
    publisher,
)

BROWSER_TOOL_USE = "browser-tool-use-trajectories"


BROWSER_LEFTOVER_MILL_IDS = (
    "obs-r649-lightstep-max-spans-zero-leftover",
    "obs-r649-chrono-drop-metric-name-leftover",
    "sir-r650-meili-swap-leftover3c-rebuild",
    "sir-r650-meili-drop-index-leftover3c-handoff",
    "sir-r651-typesense-alias-leftover3c-rebuild",
    "sir-r651-typesense-drop-coll-leftover3c-handoff",
    "sir-r652-sonic-push-leftover3c-rebuild",
    "sir-r652-sonic-drop-bucket-leftover3c-handoff",
    "sir-r653-tantivy-commit-leftover3c-rebuild",
    "sir-r653-tantivy-drop-writer-leftover3c-handoff",
)


class BrowserToolUseDeclarationTests(DeclarationTestCase):
    """Issue #39: reward key-bag drift plus ten leftover-mill records.

    Every count asserted here was derived read-only from the published mirror
    `~/rmems/hf/grok-4.6/browser-tool-use-trajectories` (1111 payloads, 2222
    records, 29707 steps, 0 parse failures). The assertions are hermetic: they
    pin the declaration, so a later hand edit that drifts from the scan is
    caught without the test reaching outside the repository.
    """

    DATASET = BROWSER_TOOL_USE
    ISSUE = 39
    HUB_ITEM = {
        "slug": "browser-tool-use-factory",
        "hub": BROWSER_TOOL_USE,
        "pretty": "Browser Tool Use Trajectories",
        "blurb": "Browser selector-fail/retry episodes.",
        "tags": ["synthetic-data", "trajectories"],
    }
    SUMMARY = publisher.PayloadSummary(
        records=2222,
        bytes_=10285056,
        first="01",
        last="1111",
        names=["batch-r01.jsonl", "batch-r649.jsonl", "batch-r653.jsonl"],
    )

    def test_declaration_matches_the_observed_union_schema(self):
        self.assertEqual(feature_names(self.declaration["features"]), EPISODE_FIELD_ORDER)
        names = self.names()
        # All 2222 records share one top-level key set, so -- unlike #36 --
        # `plan` is present on every record and must not be marked optional.
        for name, feature in names.items():
            with self.subTest(field=name):
                self.assertFalse(feature.get("optional", False))
        self.assertEqual(names["plan"]["dtype"], "string")
        self.assertEqual(names["reward"]["dtype"], "json")
        self.assertEqual(names["meta"]["dtype"], "json")
        self.assertEqual(self.declaration["issues"], [39])

    def test_step_schema_marks_only_reflection_optional(self):
        steps = self.step_features(self.names())
        self.assertEqual(list(steps), STEP_FIELD_ORDER)
        self.assertTrue(steps["reflection"]["optional"])
        self.assertIn("2991 of 29707 steps", steps["reflection"]["note"])
        for name in ("n", "decision_basis", "tool_call", "observation"):
            with self.subTest(field=name):
                self.assertFalse(steps[name].get("optional", False))
        tool_call = self.tool_call_features(steps)
        self.assertEqual(list(tool_call), ["name", "args"])
        self.assertEqual(tool_call["name"]["dtype"], "string")
        self.assertEqual(tool_call["args"]["dtype"], "json")

    def test_every_type_varying_column_is_declared_json(self):
        # `reward`, `meta` and `tool_call.args` are the three key bags; nothing
        # else in this dataset varies, so nothing else should be `json`.
        self.assert_json_columns(EPISODE_JSON_COLUMNS)

    def test_note_names_the_reward_keys_the_inferred_cast_died_on(self):
        note = self.declaration["note"]
        self.assertIn("reward", note)
        self.assertIn("http_403s", note)
        self.assertIn("pager_last_row_still_broken", note)

    def test_default_batch_glob_covers_every_published_payload(self):
        self.assertEqual(self.declaration["data_files"], DEFAULT_DATA_FILES)
        # The mirror publishes only `batch-rNNNN.jsonl`; there is no legacy
        # `episodes.jsonl` in this factory, so the default glob is complete.
        self.assertEqual(
            card_schema.payload_coverage_errors(
                self.declaration,
                ["batch-r01.jsonl", "batch-r649.jsonl", "batch-r1111.jsonl"],
            ),
            [],
        )
        self.assertTrue(card_schema.payload_coverage_errors(self.declaration, ["episodes.jsonl"]))

    def test_card_front_matter_declares_the_default_config_over_raw_batches(self):
        self.assert_front_matter_declares_default_config(
            REWARD_JSON_YAML,
            META_JSON_YAML,
            ARGS_JSON_YAML,
            # A required field must not leak the card-only annotations.
            absent=("optional",),
        )

    def test_card_body_discloses_all_ten_foreign_leftover_records(self):
        disclosed = {
            record_id
            for disclosure in self.declaration["disclosures"]
            for record_id in disclosure["ids"]
        }
        self.assertEqual(disclosed, set(BROWSER_LEFTOVER_MILL_IDS))
        self.assertIn(DISCLOSURES_HEADING, self.card)
        self.assert_card_names_records(BROWSER_LEFTOVER_MILL_IDS)
        self.assert_card_has(
            "search-index-rebuild-factory",
            "observability-debug-factory",
            REFLECTION_OPTIONAL_ROW,
        )
        self.assertNotIn(NOT_DECLARED, self.card)


if __name__ == "__main__":
    unittest.main()
