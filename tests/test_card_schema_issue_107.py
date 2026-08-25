#!/usr/bin/env python3
"""Issue #51 leaf tests for the per-dataset card schema declaration."""

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


GRAPHQL_NPLUSONE = "graphql-nplusone-trajectories"


class GraphqlNPlusOneDeclarationTests(unittest.TestCase):
    """Issue #51: preview works, parquet index fails on the `reward` key-bag."""

    def setUp(self):
        self.declaration = card_schema.load(GRAPHQL_NPLUSONE)
        self.assertIsNotNone(self.declaration, "config/card-schemas is missing #51")
        self.item = {
            "slug": "graphql-nplusone-factory",
            "hub": GRAPHQL_NPLUSONE,
            "pretty": "Graphql Nplusone Trajectories",
            "blurb": "GraphQL leftover dataloader / N+1 episodes.",
            "tags": ["synthetic-data", "trajectories", "graphql"],
        }
        self.card = publisher.render_card(
            self.item,
            records=632,
            bytes_=3343360,
            first="r01",
            last="r316",
            payload_names=["batch-r01.jsonl", "batch-r316.jsonl"],
        )

    def test_declaration_matches_the_observed_union_schema(self):
        names = {feature["name"]: feature for feature in self.declaration["features"]}
        self.assertEqual(
            set(names),
            {"id", "goal", "plan", "steps", "outcome", "reward", "meta"},
        )
        # Unlike #36, `plan` is on every record here, so it is not optional.
        self.assertNotIn("optional", names["plan"])
        self.assertEqual(names["meta"]["dtype"], "json")
        self.assertEqual(names["reward"]["dtype"], "json")
        steps = {feature["name"]: feature for feature in names["steps"]["list"]}
        self.assertEqual(
            set(steps), {"n", "decision_basis", "tool_call", "observation", "reflection"}
        )
        self.assertEqual(steps["n"]["dtype"], "int64")
        self.assertTrue(steps["reflection"]["optional"])
        self.assertIn("567 of 10181 steps", steps["reflection"]["note"])
        tool_call = {feature["name"]: feature for feature in steps["tool_call"]["struct"]}
        self.assertEqual(set(tool_call), {"name", "args"})
        self.assertEqual(tool_call["name"]["dtype"], "string")
        self.assertEqual(tool_call["args"]["dtype"], "json")
        self.assertEqual(self.declaration["issues"], [51])
        self.assertEqual(self.declaration["data_files"], ["data/raw/batch-*.jsonl"])

    def test_key_bag_columns_are_declared_json(self):
        self.assertEqual(
            card_schema.json_columns(self.declaration["features"]),
            ["steps[].tool_call.args", "reward", "meta"],
        )

    def test_reward_note_records_the_optional_handoff_and_xfailed_counts(self):
        names = {feature["name"]: feature for feature in self.declaration["features"]}
        note = names["reward"]["note"]
        for fragment in (
            "`handoff` and `xfailed` on 251",
            "`plan_changes` on 628",
            "`duration_min`, `retries`, `wasted_calls` on 44",
        ):
            self.assertIn(fragment, note)

    def test_card_front_matter_declares_the_default_config_over_raw_batches(self):
        front_matter = self.card.split("---", 2)[1]
        self.assertIn("configs:\n- config_name: default\n", front_matter)
        self.assertIn('    path: "data/raw/batch-*.jsonl"\n', front_matter)
        self.assertIn("dataset_info:\n  features:\n", front_matter)
        self.assertIn("  - name: reward\n    dtype: json\n", front_matter)
        self.assertIn("  - name: meta\n    dtype: json\n", front_matter)
        self.assertIn("license: apache-2.0", front_matter)
        self.assertIn("**not training-ready**", self.card)

    def test_card_body_discloses_the_optional_fields_and_the_kind_misuse(self):
        self.assertIn("## Dataset viewer schema", self.card)
        self.assertIn("| `steps[].reflection` | optional |", self.card)
        self.assertIn("| `reward` | present on every record |", self.card)
        self.assertIn("`meta.kind` is inconsistent across rounds", self.card)
        self.assertIn("no dest-stamped foreign payload", self.card)
        self.assertNotIn("**Not declared yet.**", self.card)


if __name__ == "__main__":
    unittest.main()

