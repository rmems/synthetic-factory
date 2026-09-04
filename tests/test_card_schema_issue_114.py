#!/usr/bin/env python3
"""Issue #41 leaf tests for the per-dataset card schema declaration."""

import unittest

from card_schema_test_support import (
    FEATURES_YAML,
    META_JSON_YAML,
    NOT_DECLARED,
    QUOTED_N_YAML,
    REWARD_JSON_YAML,
    VIEWER_SCHEMA_HEADING,
    DeclarationTestCase,
    by_name,
    card_schema,
    feature_names,
    publisher,
)

MULTI_AGENT = "multi-agent-coordination-transcripts"

# The transcript column order: no `plan` or `steps`, one `agents` list and
# one `transcript` list around the coordination narrative.
MULTI_AGENT_FIELD_ORDER = [
    "id", "goal", "outcome", "agents", "transcript",
    "disagreements", "resolution", "joint_outcome", "reward", "meta",
]

# The same card rendered for a later snapshot, so the schema prose can be
# checked for counts frozen from the earlier one.
GROWN_SUMMARY = publisher.PayloadSummary(
    records=4390,
    bytes_=11854000,
    first="r01",
    last="r4390",
    names=["batch-r01.jsonl", "batch-r4390.jsonl"],
)


class MultiAgentCoordinationDeclarationTests(DeclarationTestCase):
    """Issue #41: a transcript shape whose `reward` is a per-record key bag.

    The counts asserted here were derived read-only from the published mirror
    at ``~/rmems/hf/grok-4.6/multi-agent-coordination-transcripts`` (3784
    records over 3784 ``batch-r*.jsonl`` shards, 0 parse failures) and
    re-confirmed against the full factory source tree, where the same shape
    holds over all 4390 rounds.
    """

    DATASET = MULTI_AGENT
    ISSUE = 41
    HUB_ITEM = {
        "slug": "multi-agent-coordination-factory",
        "hub": MULTI_AGENT,
        "pretty": publisher.pretty_name(MULTI_AGENT),
        "blurb": "Multi-agent leftover-disagreement coordination transcripts.",
        "tags": ["synthetic-data", "multi-agent", "coordination"],
    }
    SUMMARY = publisher.PayloadSummary(
        records=3784,
        bytes_=10212000,
        first="r01",
        last="r3784",
        names=["batch-r01.jsonl", "batch-r3784.jsonl"],
    )

    def setUp(self):
        super().setUp()
        self.grown_card = self.render_card(GROWN_SUMMARY)

    def test_declaration_matches_the_observed_union_schema(self):
        names = self.names()
        self.assertEqual(feature_names(self.declaration["features"]), MULTI_AGENT_FIELD_ORDER)
        # `outcome` is the only optional top-level column.
        self.assertTrue(names["outcome"]["optional"])
        self.assertEqual(names["outcome"]["dtype"], "string")
        self.assertEqual(
            [
                name
                for name, optional, _note in card_schema.field_notes(self.declaration["features"])
                if optional
            ],
            ["outcome", "agents[].name"],
        )
        agents = by_name(names["agents"]["list"])
        self.assertEqual(set(agents), {"role", "mandate", "name"})
        self.assertTrue(agents["name"]["optional"])
        transcript = by_name(names["transcript"]["list"])
        self.assertEqual(set(transcript), {"n", "speaker", "content"})
        self.assertEqual(transcript["n"]["dtype"], "int64")
        self.assertEqual(self.declaration["issues"], [41])

    def test_narrative_columns_are_not_declared_as_key_bags(self):
        """The issue text asked for `resolution` / `agents` as json; the data disagrees.

        `resolution` and `joint_outcome` are plain strings on every audited record,
        `disagreements` is a list of plain strings, and `agents` is a uniform
        struct list. Only `reward` and `meta` are real key bags, so only those
        two give up their columns to `json`.
        """
        names = self.names()
        self.assertEqual(names["resolution"]["dtype"], "string")
        self.assertEqual(names["joint_outcome"]["dtype"], "string")
        self.assertEqual(names["disagreements"]["list"], "string")
        self.assertIsInstance(names["agents"]["list"], list)
        self.assert_json_columns(["reward", "meta"])

    def test_card_front_matter_declares_the_default_config_over_raw_batches(self):
        self.assert_front_matter_declares_default_config(
            FEATURES_YAML,
            REWARD_JSON_YAML,
            META_JSON_YAML,
            "  - name: disagreements\n    list: string\n",
            # `n` is a YAML reserved word and must survive as a quoted scalar.
            QUOTED_N_YAML,
        )

    def test_card_body_discloses_optional_outcome_and_the_designed_records(self):
        self.assertIn(VIEWER_SCHEMA_HEADING, self.card)
        self.assertNotIn(NOT_DECLARED, self.card)
        self.assert_card_has(
            "| `outcome` | optional |",
            "| `agents[].name` | optional |",
            "Top-level `outcome` is a genuine optional field",
        )
        designed = [feature for feature in self.declaration["disclosures"] if feature["ids"]]
        self.assertEqual(len(designed), 1)
        self.assertEqual(
            designed[0]["ids"],
            [
                f"mac-r{round_}-{tail}"
                for round_, tail in zip(
                    range(3297, 3311),
                    (
                        "merge-queue-vs-rebase",
                        "deploy-vs-rollback",
                        "feature-flag-vs-kill",
                        "incident-vs-page",
                        "lock-vs-fence",
                        "schema-vs-expand",
                        "cache-vs-stampede",
                        "rate-limit-vs-shed",
                        "auth-vs-session-wipe",
                        "payment-vs-refund",
                        "search-vs-reindex",
                        "queue-vs-purge",
                        "cert-vs-revoke",
                        "k8s-vs-drain",
                    ),
                )
            ],
        )
        summary = designed[0]["summary"]
        self.assertIn(
            "each of the fourteen has 3 agents and 10 transcript turns "
            "while using the dataset's standard `agents` / `transcript` field schema",
            summary,
        )
        self.assertIn("Cardinality is not uniform outside this fixed subset", summary)
        self.assertNotIn(
            "same 3-agent / 10-turn transcript shape as the rest of the dataset",
            summary,
        )
        self.assertIn(summary, self.card)
        # #43 froze the published factory_mix census; none of the 30 ids it
        # names is in this dataset, so these 14 are same-factory phrasing.
        self.assertEqual(designed[0]["issues"], [43])
        self.assert_card_names_records(designed[0]["ids"])

    def test_schema_prose_remains_truthful_when_the_snapshot_grows(self):
        self.assertIn("The release contains 3784 raw records", self.card)
        self.assertIn("`data/raw/batch-r3784.jsonl`", self.card)
        self.assertIn("The release contains 4390 raw records", self.grown_card)
        self.assertIn("`data/raw/batch-r4390.jsonl`", self.grown_card)

        section = card_schema.body_section(self.declaration)
        self.assertIn(section, self.card)
        self.assertIn(section, self.grown_card)
        for stale_literal in (
            "2766 of 3784",
            "1018",
            "11361",
            "45303",
            "3902",
            "3639",
            "3775",
            "2766 of 4390",
            "1624",
            "13179",
            "51363",
            "4508",
            "4245",
            "4381",
        ):
            with self.subTest(stale_literal=stale_literal):
                self.assertNotIn(stale_literal, section)


if __name__ == "__main__":
    unittest.main()
