#!/usr/bin/env python3
"""Issue #57 leaf tests for the per-dataset card schema declaration."""

import unittest

from card_schema_test_support import (
    ARGS_JSON_YAML,
    DEFAULT_DATA_FILES,
    EPISODE_FIELDS,
    EPISODE_JSON_COLUMNS,
    META_JSON_YAML,
    NOT_DECLARED,
    PLAN_OPTIONAL_ROW,
    PLAN_PRESENT_ROW,
    REFLECTION_OPTIONAL_ROW,
    REWARD_JSON_YAML,
    TOOL_CALL_FIELDS,
    VIEWER_SCHEMA_HEADING,
    DeclarationTestCase,
    card_schema,
    publisher,
)

CACHE_STAMPEDE = "cache-stampede-trajectories"
AUDITED_SCOPE = "audited 3456-record snapshot through round 1728"


def _has_digit(text):
    """True for a string that pins at least one digit-bearing count."""
    return isinstance(text, str) and any(character.isdigit() for character in text)


def _nested_features(feature):
    """Return the child features declared under a `list` or `struct` key."""
    children = []
    for key in ("list", "struct"):
        nested = feature.get(key)
        if isinstance(nested, list):
            children.extend(nested)
    return children


def _numeric_feature_notes(features):
    """Yield every digit-bearing feature `note`, descending into list/struct."""
    stack = list(reversed(features))
    while stack:
        feature = stack.pop()
        if _has_digit(feature.get("note")):
            yield feature["note"]
        stack.extend(reversed(_nested_features(feature)))


def _disclosure_texts(disclosures):
    """Yield each disclosure's prose: the sentence itself or its summary."""
    for disclosure in disclosures:
        yield disclosure if isinstance(disclosure, str) else disclosure["summary"]


class CacheStampedeDeclarationTests(DeclarationTestCase):
    """Issue #57: thin `meta` vs the designed / dest-stamped union on this dump."""

    DATASET = CACHE_STAMPEDE
    ISSUE = 57
    HUB_ITEM = {
        "slug": "cache-stampede-factory",
        "hub": CACHE_STAMPEDE,
        "pretty": "Cache Stampede Trajectories",
        "blurb": "Cache stampede leftover-key / lock / singleflight episodes.",
        "tags": ["synthetic-data", "cache", "stampede"],
    }
    # Counts derived from the 1728-shard local mirror: 3456 records,
    # 50403 steps, 0 parse failures.
    SUMMARY = publisher.PayloadSummary(
        records=3456,
        bytes_=20725966,
        first="r01",
        last="r1728",
        names=["batch-r01.jsonl", "batch-r1401.jsonl", "batch-r1728.jsonl"],
    )

    def test_declaration_matches_the_observed_union_schema(self):
        names = self.names()
        self.assertEqual(set(names), EPISODE_FIELDS)
        # `plan` is on the entire audited snapshot, but the wildcard may add
        # future shards that are not constrained by that historical census.
        self.assertTrue(names["plan"]["optional"])
        self.assertIn(AUDITED_SCOPE, names["plan"]["note"])
        self.assertEqual(names["meta"]["dtype"], "json")
        self.assertEqual(names["reward"]["dtype"], "json")
        steps, tool_call = self.assert_episode_steps(names, "5029 of 50403")
        self.assertEqual(steps["n"]["dtype"], "int64")
        self.assertEqual(set(tool_call), TOOL_CALL_FIELDS)
        self.assertEqual(self.declaration["issues"], [57])

    def test_key_bag_columns_are_declared_json(self):
        self.assert_json_columns(EPISODE_JSON_COLUMNS)

    def test_the_default_config_covers_every_published_shard(self):
        self.assertEqual(self.declaration["data_files"], DEFAULT_DATA_FILES)
        self.assertEqual(
            card_schema.payload_coverage_errors(
                self.declaration,
                [f"batch-r{index:02d}.jsonl" for index in range(1, 1729)],
            ),
            [],
        )

    def test_card_front_matter_declares_the_default_config_over_raw_batches(self):
        self.assert_front_matter_declares_default_config(
            META_JSON_YAML, REWARD_JSON_YAML, ARGS_JSON_YAML
        )
        self.assertNotIn(NOT_DECLARED, self.card)

    def test_card_body_attributes_each_dest_stamped_class_to_its_owner(self):
        self.assertIn(VIEWER_SCHEMA_HEADING, self.card)
        # The 18 rows owned by #44 -- disclosed, not re-filed.
        self.assert_card_has(
            "issues/44",
            "`gql-r1405-postgraphile-drop-wrap`",
            "`dbc-r1413-overlayfs-opaque-xattr-l3`",
        )
        # The 8 search-index leftover3c rows -- disclosed, no new mill issue.
        self.assert_card_has(
            "`sir-r1401-manticore-rt-leftover3c-rebuild`",
            "`sir-r1404-solr-drop-core-leftover3c-handoff`",
        )

    def test_card_body_does_not_misreport_the_advertised_leftover_mechanic(self):
        self.assert_card_has(
            "387 of the 3430 `cst-*` records carry `leftover` in the record id",
            "advertised cache leftover-key mechanic",
            "not a MIXED-kind signal",
        )

    def test_card_body_reports_the_optional_and_key_bag_fields(self):
        self.assert_card_has(REFLECTION_OPTIONAL_ROW, PLAN_OPTIONAL_ROW)
        self.assertNotIn(PLAN_PRESENT_ROW, self.card)
        self.assert_card_has(
            "`steps[].tool_call.args`, `reward`, `meta`",
            "no hidden `thought` or `internal_reasoning`",
        )

    def test_all_fixed_counts_are_scoped_to_the_audited_snapshot(self):
        annotations = [
            self.declaration["note"],
            *_numeric_feature_notes(self.declaration["features"]),
            *(
                text
                for text in _disclosure_texts(self.declaration["disclosures"])
                if _has_digit(text)
            ),
        ]

        self.assertTrue(annotations)
        for annotation in annotations:
            self.assertIn(AUDITED_SCOPE, annotation)
        self.assertIn(AUDITED_SCOPE, self.card)


if __name__ == "__main__":
    unittest.main()
