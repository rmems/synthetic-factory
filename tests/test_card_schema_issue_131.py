#!/usr/bin/env python3
"""Issue #71 leaf tests for the per-dataset card schema declaration."""

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


RAG_RETRIEVAL_DEBUG = "rag-retrieval-debug-trajectories"


class RagRetrievalDebugDeclarationTests(unittest.TestCase):
    """Issue #71: episode-only top-level extras against an otherwise thin record."""

    def setUp(self):
        self.declaration = card_schema.load(RAG_RETRIEVAL_DEBUG)
        self.assertIsNotNone(self.declaration, "config/card-schemas is missing #71")
        self.item = {
            "slug": "rag-retrieval-debug-factory",
            "hub": RAG_RETRIEVAL_DEBUG,
            "pretty": "Rag Retrieval Debug Trajectories",
            "blurb": "RAG leftover-chunk / citation-miss debug episodes.",
            "tags": ["synthetic-data", "trajectories", "rag", "retrieval"],
        }
        self.card = publisher.render_card(
            self.item,
            records=1876,
            bytes_=10831457,
            first="r01",
            last="r938",
            payload_names=["batch-r01.jsonl", "batch-r670.jsonl", "batch-r938.jsonl"],
        )

    def test_declaration_matches_the_observed_union_schema(self):
        self.assertEqual(self.declaration["issues"], [71])
        self.assertEqual(
            [feature["name"] for feature in self.declaration["features"]],
            [
                "id",
                "goal",
                "plan",
                "error_introduced",
                "propagation",
                "diagnosis",
                "recovery",
                "verification",
                "steps",
                "outcome",
                "reward",
                "meta",
            ],
        )
        names = {feature["name"]: feature for feature in self.declaration["features"]}
        # `plan` is a string on all 1876 records here, unlike issue #36's dataset.
        self.assertEqual(names["plan"]["dtype"], "string")
        self.assertNotIn("optional", names["plan"])
        steps = {feature["name"]: feature for feature in names["steps"]["list"]}
        self.assertEqual(
            set(steps), {"n", "decision_basis", "tool_call", "observation", "reflection"}
        )
        self.assertTrue(steps["reflection"]["optional"])
        self.assertEqual(steps["n"]["dtype"], "int64")
        tool_call = {feature["name"]: feature for feature in steps["tool_call"]["struct"]}
        self.assertEqual(tool_call["args"]["dtype"], "json")

    def test_episode_only_extras_are_optional_typed_structs_not_key_bags(self):
        names = {feature["name"]: feature for feature in self.declaration["features"]}
        expected = {
            "error_introduced": {"step", "kind", "description"},
            "propagation": {"hops", "survived_steps", "mask", "first_symptom_step"},
            "diagnosis": {"step", "how_survived"},
            "recovery": {"step", "action"},
            "verification": {"step", "evidence"},
        }
        for field, children in expected.items():
            with self.subTest(field=field):
                feature = names[field]
                self.assertTrue(feature["optional"])
                self.assertIn("76 of 1876", feature["note"])
                # Every one of the 76 records carries the same keys with the
                # same types, so a struct keeps these columns filterable.
                self.assertNotIn("dtype", feature)
                self.assertEqual(
                    {child["name"] for child in feature["struct"]}, children
                )
        propagation = {
            child["name"]: child for child in names["propagation"]["struct"]
        }
        self.assertEqual(propagation["survived_steps"]["list"], "int64")

    def test_only_the_three_real_key_bags_are_declared_json(self):
        self.assertEqual(
            card_schema.json_columns(self.declaration["features"]),
            ["steps[].tool_call.args", "reward", "meta"],
        )

    def test_card_front_matter_declares_the_default_config_over_raw_batches(self):
        front_matter = self.card.split("---", 2)[1]
        self.assertIn("configs:\n- config_name: default\n", front_matter)
        self.assertIn('    path: "data/raw/batch-*.jsonl"\n', front_matter)
        self.assertIn("  - name: reward\n    dtype: json\n", front_matter)
        self.assertIn("  - name: meta\n    dtype: json\n", front_matter)
        self.assertIn("  - name: error_introduced\n    struct:\n", front_matter)
        self.assertIn("    - name: survived_steps\n      list: int64\n", front_matter)
        self.assertNotIn("optional", front_matter)
        self.assertIn("license: apache-2.0", front_matter)
        self.assertIn("**not training-ready**", self.card)

    def test_card_body_discloses_the_eighteen_dest_stamped_mill_records(self):
        self.assertIn("## Dataset viewer schema", self.card)
        self.assertNotIn("**Not declared yet.**", self.card)
        self.assertIn("`evh-r21-cite-orphan-c3e8`", self.card)
        self.assertIn("`evh-r29-pinecone-ns-k6d4`", self.card)
        self.assertIn("issues/43", self.card)
        self.assertIn("| `error_introduced` | optional |", self.card)
        self.assertIn("| `steps[].reflection` | optional |", self.card)
        # The third, unowned `sir-*` class is absent here and says so.
        self.assertIn("No unowned third leftover class is present here.", self.card)


if __name__ == "__main__":
    unittest.main()

