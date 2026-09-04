#!/usr/bin/env python3
"""Issue #71 leaf tests for the per-dataset card schema declaration."""

import json
import unittest

from card_schema_test_support import (
    META_JSON_YAML,
    NOT_DECLARED,
    REFLECTION_OPTIONAL_ROW,
    REWARD_JSON_YAML,
    STEPS_YAML_FEATURE,
    STEP_FIELDS,
    VIEWER_SCHEMA_HEADING,
    DeclarationTestCase,
    card_schema,
    feature_names,
    mirror_path,
    needs_mirror,
    publisher,
)

RAG_RETRIEVAL_DEBUG = "rag-retrieval-debug-trajectories"
RAG_RETRIEVAL_DEBUG_MIRROR = mirror_path(RAG_RETRIEVAL_DEBUG)
RAG_SLUG = "rag-retrieval-debug-factory"

# The published column order: the five episode-only extras sit between `plan`
# and `steps`.
RAG_FIELD_ORDER = [
    "id", "goal", "plan", "error_introduced", "propagation", "diagnosis",
    "recovery", "verification", "steps", "outcome", "reward", "meta",
]


def _hub_item():
    """The publisher's own Hub item for this factory: registry blurb and tags."""
    blurb, extra_tags = publisher.META[RAG_SLUG]
    tags = [
        "synthetic-data",
        "agentic-workflows",
        "grok-4.6",
        "provenance",
        "trajectories",
        *extra_tags,
    ]
    return {
        "slug": RAG_SLUG,
        "hub": publisher.hub_name(RAG_SLUG),
        "pretty": publisher.pretty_name(RAG_RETRIEVAL_DEBUG),
        "blurb": blurb,
        "tags": list(dict.fromkeys(tags)),
    }


class RagRetrievalDebugDeclarationTests(DeclarationTestCase):
    """Issue #71: episode-only top-level extras against an otherwise thin record."""

    EVH_IDS = [
        "evh-r21-cite-orphan-c3e8",
        "evh-r21-hybrid-sku-a91b",
        "evh-r22-rerank-pad-d7f2",
        "evh-r22-ragas-param-b4c1",
        "evh-r23-embed-mismatch-e5a0",
        "evh-r23-tenant-filter-f2c9",
        "evh-r24-table-split-a8d3",
        "evh-r24-mmr-drop-b7e1",
        "evh-r25-stale-alias-c4b2",
        "evh-r25-compress-numeral-d9aa",
        "evh-r26-parent-cite-e1f6",
        "evh-r26-hnsw-ef-f8c0",
        "evh-r27-cohere-topn-a6b8",
        "evh-r27-recency-bury-c2d4",
        "evh-r28-lost-middle-g3a1",
        "evh-r28-weaviate-cert-h4b2",
        "evh-r29-history-embed-j5c3",
        "evh-r29-pinecone-ns-k6d4",
    ]

    DATASET = RAG_RETRIEVAL_DEBUG
    ISSUE = 71
    HUB_ITEM = _hub_item()
    SUMMARY = publisher.PayloadSummary(
        records=1876,
        bytes_=10831457,
        first="r01",
        last="r938",
        names=[f"batch-r{n:02d}.jsonl" for n in range(1, 939)],
    )

    def setUp(self):
        super().setUp()
        self.assertEqual(self.item["hub"], RAG_RETRIEVAL_DEBUG)

    def test_declaration_matches_the_observed_union_schema(self):
        self.assertEqual(self.declaration["issues"], [71])
        self.assertEqual(feature_names(self.declaration["features"]), RAG_FIELD_ORDER)
        names = self.names()
        # `plan` is a string on all 1876 records here, unlike issue #36's dataset.
        self.assertEqual(names["plan"]["dtype"], "string")
        self.assertNotIn("optional", names["plan"])
        self.assertIn("observed snapshot through round 938", names["plan"]["note"])
        steps = self.step_features(names)
        self.assertEqual(set(steps), STEP_FIELDS)
        self.assertTrue(steps["reflection"]["optional"])
        self.assertEqual(steps["n"]["dtype"], "int64")
        tool_call = self.tool_call_features(steps)
        self.assertEqual(tool_call["args"]["dtype"], "json")

    def test_yaml_projection_is_the_complete_annotation_free_feature_tree(self):
        self.assertEqual(
            card_schema.yaml_features(self.declaration["features"]),
            [
                {"name": "id", "dtype": "string"},
                {"name": "goal", "dtype": "string"},
                {"name": "plan", "dtype": "string"},
                {"name": "error_introduced", "dtype": "json"},
                {"name": "propagation", "dtype": "json"},
                {"name": "diagnosis", "dtype": "json"},
                {"name": "recovery", "dtype": "json"},
                {"name": "verification", "dtype": "json"},
                STEPS_YAML_FEATURE,
                {"name": "outcome", "dtype": "string"},
                {"name": "reward", "dtype": "json"},
                {"name": "meta", "dtype": "json"},
            ],
        )

    def test_episode_only_extras_are_optional_json_columns(self):
        names = self.names()
        expected = [
            "error_introduced",
            "propagation",
            "diagnosis",
            "recovery",
            "verification",
        ]
        for field in expected:
            with self.subTest(field=field):
                feature = names[field]
                self.assertTrue(feature["optional"])
                self.assertEqual(feature["dtype"], "json")
                self.assertRegex(
                    feature["note"],
                    r"observed snapshot through round \d+: present on \d+ of \d+ records",
                )
                self.assertRegex(feature["note"], r"(?:drift|cast failure)")

    def test_json_columns_include_episode_objects_and_key_bags(self):
        self.assert_json_columns(
            [
                "error_introduced",
                "propagation",
                "diagnosis",
                "recovery",
                "verification",
                "steps[].tool_call.args",
                "reward",
                "meta",
            ]
        )

    def test_card_front_matter_declares_the_default_config_over_raw_batches(self):
        self.assert_front_matter_declares_default_config(
            REWARD_JSON_YAML,
            META_JSON_YAML,
            "  - name: error_introduced\n    dtype: json\n",
            "  - name: propagation\n    dtype: json\n",
            absent=("optional", "note:"),
        )

    def test_card_body_discloses_the_eighteen_dest_stamped_mill_records(self):
        self.assertIn(VIEWER_SCHEMA_HEADING, self.card)
        self.assertNotIn(NOT_DECLARED, self.card)
        disclosure = self.declaration["disclosures"][0]
        self.assertEqual(disclosure["ids"], self.EVH_IDS)
        self.assertEqual(len(disclosure["ids"]), 18)
        self.assert_card_names_records(self.EVH_IDS)
        self.assert_card_has(
            "issues/43",
            "| `error_introduced` | optional |",
            REFLECTION_OPTIONAL_ROW,
            # The third, unowned `sir-*` class is absent here and says so.
            "No unowned third leftover class is present here.",
        )

    @needs_mirror(RAG_RETRIEVAL_DEBUG_MIRROR)
    def test_published_mirror_matches_the_snapshot_claims(self):
        payloads = sorted(RAG_RETRIEVAL_DEBUG_MIRROR.glob("batch-*.jsonl"))
        self.assertEqual(len(payloads), 938)
        records = 0
        extra_counts = {
            name: 0
            for name in (
                "error_introduced",
                "propagation",
                "diagnosis",
                "recovery",
                "verification",
            )
        }
        evh_ids = set()
        for payload in payloads:
            with payload.open(encoding="utf-8") as handle:
                for line_number, line in enumerate(handle, start=1):
                    if not line.strip():
                        continue
                    record = json.loads(line)
                    plan = record.get("plan")
                    self.assertIsInstance(plan, str, f"{payload.name}:{line_number}")
                    self.assertTrue(plan.strip(), f"{payload.name}:{line_number}")
                    for name in extra_counts:
                        extra_counts[name] += name in record
                    if record["id"].startswith("evh-"):
                        evh_ids.add(record["id"])
                    records += 1

        self.assertEqual(records, 1876)
        self.assertEqual(set(extra_counts.values()), {76})
        self.assertEqual(evh_ids, set(self.EVH_IDS))


if __name__ == "__main__":
    unittest.main()
