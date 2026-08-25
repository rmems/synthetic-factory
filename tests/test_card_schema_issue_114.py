#!/usr/bin/env python3
"""Issue #41 leaf tests for the per-dataset card schema declaration."""

import test_card_schema as _shared

unittest = _shared.unittest
io = _shared.io
json = _shared.json
tempfile = _shared.tempfile
redirect_stderr = _shared.redirect_stderr
redirect_stdout = _shared.redirect_stdout
Path = _shared.Path
mock = _shared.mock
REPO = _shared.REPO
card_schema = _shared.card_schema
publisher = _shared.publisher
LONG_HORIZON = _shared.LONG_HORIZON
MINIMAL = _shared.MINIMAL
write_declaration = _shared.write_declaration


MULTI_AGENT = "multi-agent-coordination-transcripts"


class MultiAgentCoordinationDeclarationTests(unittest.TestCase):
    """Issue #41: a transcript shape whose `reward` is a per-record key bag.

    The counts asserted here were derived read-only from the published mirror
    at ``~/rmems/hf/grok-4.6/multi-agent-coordination-transcripts`` (3784
    records over 3784 ``batch-r*.jsonl`` shards, 0 parse failures) and
    re-confirmed against the full factory source tree, where the same shape
    holds over all 4390 rounds.
    """

    def setUp(self):
        self.declaration = card_schema.load(MULTI_AGENT)
        self.assertIsNotNone(self.declaration, "config/card-schemas is missing #41")
        self.item = {
            "slug": "multi-agent-coordination-factory",
            "hub": MULTI_AGENT,
            "pretty": publisher.pretty_name(MULTI_AGENT),
            "blurb": "Multi-agent leftover-disagreement coordination transcripts.",
            "tags": ["synthetic-data", "multi-agent", "coordination"],
        }
        self.card = publisher.render_card(
            self.item,
            records=3784,
            bytes_=10212000,
            first="r01",
            last="r3784",
            payload_names=["batch-r01.jsonl", "batch-r3784.jsonl"],
        )
        self.grown_card = publisher.render_card(
            self.item,
            records=4390,
            bytes_=11854000,
            first="r01",
            last="r4390",
            payload_names=["batch-r01.jsonl", "batch-r4390.jsonl"],
        )

    def test_declaration_matches_the_observed_union_schema(self):
        names = {feature["name"]: feature for feature in self.declaration["features"]}
        self.assertEqual(
            [feature["name"] for feature in self.declaration["features"]],
            [
                "id",
                "goal",
                "outcome",
                "agents",
                "transcript",
                "disagreements",
                "resolution",
                "joint_outcome",
                "reward",
                "meta",
            ],
        )
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
        agents = {feature["name"]: feature for feature in names["agents"]["list"]}
        self.assertEqual(set(agents), {"role", "mandate", "name"})
        self.assertTrue(agents["name"]["optional"])
        transcript = {feature["name"]: feature for feature in names["transcript"]["list"]}
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
        names = {feature["name"]: feature for feature in self.declaration["features"]}
        self.assertEqual(names["resolution"]["dtype"], "string")
        self.assertEqual(names["joint_outcome"]["dtype"], "string")
        self.assertEqual(names["disagreements"]["list"], "string")
        self.assertIsInstance(names["agents"]["list"], list)
        self.assertEqual(card_schema.json_columns(self.declaration["features"]), ["reward", "meta"])

    def test_card_front_matter_declares_the_default_config_over_raw_batches(self):
        front_matter = self.card.split("---", 2)[1]
        self.assertIn("configs:\n- config_name: default\n", front_matter)
        self.assertIn('    path: "data/raw/batch-*.jsonl"\n', front_matter)
        self.assertIn("dataset_info:\n  features:\n", front_matter)
        self.assertIn("  - name: reward\n    dtype: json\n", front_matter)
        self.assertIn("  - name: meta\n    dtype: json\n", front_matter)
        self.assertIn("  - name: disagreements\n    list: string\n", front_matter)
        # `n` is a YAML reserved word and must survive as a quoted scalar.
        self.assertIn('    - name: "n"\n      dtype: int64\n', front_matter)
        self.assertIn("license: apache-2.0", front_matter)
        self.assertIn("**not training-ready**", self.card)

    def test_card_body_discloses_optional_outcome_and_the_designed_records(self):
        self.assertIn("## Dataset viewer schema", self.card)
        self.assertNotIn("**Not declared yet.**", self.card)
        self.assertIn("| `outcome` | optional |", self.card)
        self.assertIn("| `agents[].name` | optional |", self.card)
        self.assertIn("Top-level `outcome` is a genuine optional field", self.card)
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
        for record_id in designed[0]["ids"]:
            self.assertIn(f"`{record_id}`", self.card)

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
