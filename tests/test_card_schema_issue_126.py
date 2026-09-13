#!/usr/bin/env python3
"""Issue #64 leaf tests for the per-dataset card schema declaration."""

import unittest

from card_schema_test_support import (
    ARGS_JSON_YAML,
    DEFAULT_DATA_FILES,
    EPISODE_FIELD_ORDER,
    EPISODE_JSON_COLUMNS,
    LONG_HORIZON,
    META_JSON_YAML,
    NOT_DECLARED,
    REFLECTION_OPTIONAL_ROW,
    REWARD_JSON_YAML,
    STEP_FIELDS,
    VIEWER_SCHEMA_HEADING,
    DeclarationTestCase,
    by_name,
    card_schema,
    publisher,
)

FLAKY_TEST_QUARANTINE = "flaky-test-quarantine-trajectories"


class FlakyTestQuarantineDeclarationTests(DeclarationTestCase):
    """Issue #64: thin `meta` vs the later `designed` leftovers, plus 14 dest-stamped rows.

    Every count asserted here was derived from the read-only mirror at
    `~/rmems/hf/grok-4.6/flaky-test-quarantine-trajectories` (1575 shards,
    3150 records, 38604 steps, 0 parse failures).
    """

    SIR_IDS = (
        "sir-r1537-weaviate-alias-leftover-lll-rebuild",
        "sir-r1537-weaviate-drop-class-leftover-lll-handoff",
        "sir-r1538-qdrant-alias-leftover-lll-rebuild",
        "sir-r1538-qdrant-delete-coll-leftover-lll-handoff",
        "sir-r1539-milvus-alias-leftover-lll-rebuild",
        "sir-r1539-milvus-drop-coll-leftover-lll-handoff",
        "sir-r1540-pinecone-ns-leftover-lll-rebuild",
        "sir-r1540-pinecone-delete-index-leftover-lll-handoff",
        "sir-r1541-chroma-persist-leftover-lll-rebuild",
        "sir-r1541-chroma-delete-coll-leftover-lll-handoff",
        "sir-r1542-lancedb-compact-leftover-lll-rebuild",
        "sir-r1542-lancedb-overwrite-leftover-lll-handoff",
        "sir-r1543-pgvector-hnsw-leftover-lll-rebuild",
        "sir-r1543-pgvector-drop-hnsw-leftover-lll-handoff",
    )

    DATASET = FLAKY_TEST_QUARANTINE
    ISSUE = 64
    HUB_ITEM = {
        "slug": "flaky-test-quarantine-factory",
        "hub": FLAKY_TEST_QUARANTINE,
        "pretty": "Flaky Test Quarantine Trajectories",
        "blurb": "Flaky-test leftover-cause quarantine episodes.",
        "tags": ["synthetic-data", "trajectories", "testing", "flaky-tests"],
    }
    SUMMARY = publisher.PayloadSummary(
        records=3150,
        bytes_=12326850,
        first="r01",
        last="r1575",
        names=[f"batch-r{n}.jsonl" for n in range(1, 1576)],
    )

    def test_declaration_matches_the_observed_union_schema(self):
        names = self.names()
        self.assertEqual(list(names), EPISODE_FIELD_ORDER)
        self.assertEqual(self.declaration["issues"], [64])
        self.assertEqual(self.declaration["data_files"], DEFAULT_DATA_FILES)
        self.assertEqual(names["meta"]["dtype"], "json")
        self.assertEqual(names["reward"]["dtype"], "json")
        steps = self.step_features(names)
        self.assertEqual(set(steps), STEP_FIELDS)
        tool_call = self.tool_call_features(steps)
        self.assertEqual(tool_call["args"]["dtype"], "json")

    def test_plan_is_mandatory_here_unlike_the_worked_example(self):
        # 3150 of 3150 records carry a string `plan`. Optionality is derived from
        # this dump, never copied from `long-horizon-coding-trajectories`.
        plan = self.feature("plan")
        self.assertNotIn("optional", plan)
        self.assertEqual(plan["dtype"], "string")
        borrowed = by_name(card_schema.load(LONG_HORIZON)["features"])["plan"]
        self.assertTrue(borrowed["optional"])

    def test_only_step_reflection_is_optional(self):
        rows = card_schema.field_notes(self.declaration["features"])
        optional = [path for path, is_optional, _note in rows if is_optional]
        self.assertEqual(optional, ["steps[].reflection"])
        self.assertIn("6586 of 38604 steps", dict((p, n) for p, _o, n in rows)[
            "steps[].reflection"
        ])

    def test_key_bag_columns_are_declared_json(self):
        self.assert_json_columns(EPISODE_JSON_COLUMNS)

    def test_reward_note_names_the_variants_the_issue_census_omitted(self):
        reward = self.feature("reward")
        # Derived from the mirror: issue #64 lists 13 keys plus `drop_flag_*`;
        # these three key variants are real and were missing from that census.
        for key in ("skip_applied", "repeats_ok", "locales_ok"):
            with self.subTest(key=key):
                self.assertIn(f"`{key}`", reward["note"])

    def test_card_front_matter_declares_the_default_config_over_raw_batches(self):
        self.assert_front_matter_declares_default_config(
            META_JSON_YAML, REWARD_JSON_YAML, ARGS_JSON_YAML, absent=("optional",)
        )

    def test_card_body_discloses_every_dest_stamped_leftover(self):
        self.assertIn(VIEWER_SCHEMA_HEADING, self.card)
        self.assertNotIn(NOT_DECLARED, self.card)
        self.assert_card_names_records(self.SIR_IDS)
        self.assert_card_has(
            REFLECTION_OPTIONAL_ROW,
            "98 calls total: 42 `pytest` and 56 `fetch`",
            "across the 231 steps in those episodes",
        )
        self.assertNotIn("tool calls (231 of", self.card)

    def test_disclosures_keep_ownership_and_separate_the_advertised_mechanic(self):
        summaries = [d["summary"] for d in self.declaration["disclosures"]]
        joined = " ".join(summaries)
        sir = next(d for d in self.declaration["disclosures"] if d["ids"])
        self.assertEqual(list(sir["ids"]), list(self.SIR_IDS))
        self.assertEqual(sir["issues"], [64])
        # The 14 belong to neither frozen census, so #64 must own them.
        self.assertIn("issue 43", joined)
        self.assertIn("issue 44", joined)
        # This factory's own leftover-* naming must not be sold as a foreign dump.
        self.assertIn("advertised mechanic", joined)
        self.assertIn("3136", joined)


if __name__ == "__main__":
    unittest.main()
