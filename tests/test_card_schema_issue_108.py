#!/usr/bin/env python3
"""Issue #49 leaf tests for the per-dataset card schema declaration."""

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


PROTO_BREAKING = "proto-breaking-change-trajectories"


class ProtoBreakingChangeDeclarationTests(unittest.TestCase):
    """Issue #49: `reward` is a seven-shape key-bag, so the parquet index fails.

    The numbers asserted here are derived from the published payload at
    ``~/rmems/hf/grok-4.6/proto-breaking-change-trajectories`` (1707 shards,
    3414 records, 70670 steps), not copied from the issue body.
    """

    def setUp(self):
        self.declaration = card_schema.load(PROTO_BREAKING)
        self.assertIsNotNone(self.declaration, "config/card-schemas is missing #49")
        self.item = {
            "slug": "proto-breaking-change-factory",
            "hub": PROTO_BREAKING,
            "pretty": "Proto Breaking Change Trajectories",
            "blurb": "Protobuf leftover-compat breaking-change episodes.",
            "tags": ["synthetic-data", "trajectories", "protobuf", "api"],
        }
        self.card = publisher.render_card(
            self.item,
            records=3414,
            bytes_=25953665,
            first="r01",
            last="r1707",
            payload_names=["batch-r01.jsonl", "batch-r1707.jsonl"],
        )

    def test_declaration_matches_the_observed_union_schema(self):
        features = self.declaration["features"]
        self.assertEqual(
            [feature["name"] for feature in features],
            ["id", "goal", "plan", "steps", "outcome", "reward", "meta"],
        )
        names = {feature["name"]: feature for feature in features}
        # Unlike long-horizon-coding, every record here carries `plan`.
        self.assertEqual(names["plan"]["dtype"], "string")
        self.assertNotIn("optional", names["plan"])
        self.assertEqual(names["reward"]["dtype"], "json")
        meta = {feature["name"]: feature for feature in names["meta"]["struct"]}
        self.assertEqual(
            meta,
            {
                "factory": {"name": "factory", "dtype": "string"},
                "generator": {"name": "generator", "dtype": "string"},
                "round": {"name": "round", "dtype": "int64"},
            },
        )
        steps = {feature["name"]: feature for feature in names["steps"]["list"]}
        self.assertEqual(
            set(steps), {"n", "decision_basis", "tool_call", "observation", "reflection"}
        )
        self.assertEqual(steps["n"]["dtype"], "int64")
        self.assertTrue(steps["reflection"]["optional"])
        self.assertIn("2948 of 70670 steps", steps["reflection"]["note"])
        tool_call = {feature["name"]: feature for feature in steps["tool_call"]["struct"]}
        self.assertEqual(tool_call["name"]["dtype"], "string")
        self.assertEqual(tool_call["args"]["dtype"], "json")
        self.assertEqual(self.declaration["issues"], [49])
        self.assertEqual(self.declaration["data_files"], ["data/raw/batch-*.jsonl"])

    def test_optional_reward_keys_are_documented_not_declared_as_columns(self):
        # `buf_breaking` / `xfailed` must never become their own struct fields:
        # `reward` is one `json` column, and the variants live in its note.
        self.assertEqual(
            card_schema.json_columns(self.declaration["features"]),
            ["steps[].tool_call.args", "reward"],
        )
        reward = next(
            feature
            for feature in self.declaration["features"]
            if feature["name"] == "reward"
        )
        self.assertIn("`buf_breaking` on 2814 of 3414", reward["note"])
        self.assertIn("`xfailed` on 1686 of 3414", reward["note"])

    def test_card_front_matter_declares_the_default_config_over_raw_batches(self):
        front_matter = self.card.split("---", 2)[1]
        self.assertIn("configs:\n- config_name: default\n", front_matter)
        self.assertIn('    path: "data/raw/batch-*.jsonl"\n', front_matter)
        self.assertIn("dataset_info:\n  features:\n", front_matter)
        self.assertIn("  - name: reward\n    dtype: json\n", front_matter)
        self.assertIn(
            "  - name: meta\n"
            "    struct:\n"
            "    - name: factory\n"
            "      dtype: string\n"
            "    - name: generator\n"
            "      dtype: string\n"
            "    - name: round\n"
            "      dtype: int64\n",
            front_matter,
        )
        # Card-only annotations must not leak into the HF feature encoding.
        self.assertNotIn("optional:", front_matter)
        self.assertNotIn("note:", front_matter)
        # license/tags/status claims stay exactly where they were.
        self.assertIn("license: apache-2.0", front_matter)
        self.assertIn("**not training-ready**", self.card)

    def test_card_body_discloses_the_reward_variants_and_optional_reflection(self):
        self.assertIn("## Dataset viewer schema", self.card)
        self.assertNotIn("**Not declared yet.**", self.card)
        self.assertIn("| `steps[].reflection` | optional |", self.card)
        self.assertIn("| `reward` | present on every record |", self.card)
        self.assertIn("### Known payload disclosures", self.card)
        self.assertIn("3414-record published snapshot audited for issue #49", self.card)
        self.assertIn("1686 `{buf_breaking, cost_steps, success, tests_passed, xfailed}`", self.card)
        self.assertIn("`skipped` (10), `ignored` (7), `disabled` (2) or `pending` (2)", self.card)
        self.assertIn("no dest-stamped foreign payload", self.card)
        self.assertIn("https://github.com/rmems/synthetic-factory/issues/49", self.card)


if __name__ == "__main__":
    unittest.main()
