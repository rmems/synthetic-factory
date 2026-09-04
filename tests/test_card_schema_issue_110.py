#!/usr/bin/env python3
"""Issue #42 leaf tests for the per-dataset card schema declaration."""

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


SANDBOX_REFUSAL = "sandbox-refusal-trajectories"


class SandboxRefusalDeclarationTests(unittest.TestCase):
    """Issue #42: optional case-type extras plus a two-keyset `reward`.

    Every number asserted here was derived by scanning the published mirror
    (1634 shards, 4902 records) rather than copied from the issue text.
    """

    def setUp(self):
        self.declaration = card_schema.load(SANDBOX_REFUSAL)
        self.assertIsNotNone(self.declaration, "config/card-schemas is missing #42")
        self.item = {
            "slug": "sandbox-refusal-factory",
            "hub": SANDBOX_REFUSAL,
            "pretty": "Sandbox Refusal Trajectories",
            "blurb": "Sandbox leftover-policy refusal / allow cases.",
            "tags": ["synthetic-data", "trajectories", "sandbox", "safety"],
        }
        self.card = publisher.render_card(
            self.item,
            # Exercise a later snapshot: reusable schema prose must not freeze
            # the r1634 record counts into every future card render.
            records=5784,
            bytes_=18135666,
            first="r01",
            last="r1928",
            payload_names=["batch-r01.jsonl", "batch-r1928.jsonl"],
        )

    def test_declaration_matches_the_observed_union_schema(self):
        names = {feature["name"]: feature for feature in self.declaration["features"]}
        self.assertIn("`family` is absent from rounds 1 to 358", self.declaration["note"])
        self.assertIn("reward object", self.declaration["note"])
        self.assertNotIn("four case-type extras", self.declaration["note"])
        self.assertEqual(
            set(names),
            {
                "id",
                "goal",
                "case_type",
                "should_refuse",
                "decision",
                "rationale",
                "steps",
                "outcome",
                "reward",
                "meta",
                "trigger",
                "redirect",
                "benign_twin",
                "vector",
                "family",
            },
        )
        self.assertEqual(names["should_refuse"]["dtype"], "bool")
        self.assertEqual(names["case_type"]["dtype"], "string")
        self.assertEqual(self.declaration["issues"], [42])
        self.assertEqual(self.declaration["data_files"], ["data/raw/batch-*.jsonl"])

    def test_only_the_four_case_type_extras_are_optional(self):
        optional = {
            feature["name"]
            for feature in self.declaration["features"]
            if feature.get("optional")
        }
        # `trigger` sits next to the extras in the raw record but is on every
        # record, so declaring it optional would understate the payload.
        self.assertEqual(optional, {"redirect", "benign_twin", "vector", "family"})
        notes = {
            feature["name"]: feature.get("note", "")
            for feature in self.declaration["features"]
        }
        self.assertIn("every `correct_refusal` case", notes["redirect"])
        self.assertIn("every `incorrect_refusal` case", notes["benign_twin"])
        self.assertIn("every `missed_refusal` case", notes["vector"])
        self.assertIn("round 359 onward", notes["family"])

    def test_key_bag_columns_are_declared_json(self):
        self.assertEqual(
            card_schema.json_columns(self.declaration["features"]),
            ["steps[].tool_call.args", "reward", "meta"],
        )

    def test_steps_declare_the_public_decision_basis_and_no_reflection(self):
        names = {feature["name"]: feature for feature in self.declaration["features"]}
        steps = {feature["name"]: feature for feature in names["steps"]["list"]}
        self.assertEqual(set(steps), {"n", "decision_basis", "tool_call", "observation"})
        tool_call = {f["name"]: f for f in steps["tool_call"]["struct"]}
        self.assertEqual(set(tool_call), {"name", "args"})
        self.assertEqual(tool_call["args"]["dtype"], "json")

    def test_card_front_matter_declares_the_default_config_over_raw_batches(self):
        front_matter = self.card.split("---", 2)[1]
        self.assertIn("configs:\n- config_name: default\n", front_matter)
        self.assertIn('    path: "data/raw/batch-*.jsonl"\n', front_matter)
        self.assertIn("dataset_info:\n  features:\n", front_matter)
        self.assertIn("  - name: reward\n    dtype: json\n", front_matter)
        self.assertIn("  - name: meta\n    dtype: json\n", front_matter)
        self.assertIn("  - name: should_refuse\n    dtype: bool\n", front_matter)
        # The extras are plain strings; declaring them keeps the cast alive.
        self.assertIn("  - name: family\n    dtype: string\n", front_matter)
        self.assertIn("license: apache-2.0", front_matter)
        self.assertIn("**not training-ready**", self.card)

    def test_card_body_discloses_the_case_split_and_the_double_extra_record(self):
        self.assertIn("## Dataset viewer schema", self.card)
        self.assertNotIn("**Not declared yet.**", self.card)
        self.assertIn("one `correct_refusal`", self.card)
        self.assertIn("one `incorrect_refusal`", self.card)
        self.assertIn("one `missed_refusal`", self.card)
        self.assertNotIn("4902", self.card)
        self.assertNotIn("1634 records", self.card)
        self.assertNotIn("1635", self.card)
        self.assertIn("one-record surplus", self.card)
        self.assertIn("`sbox-r191-agents-md-token-exfil-refuse`", self.card)
        self.assertIn("| `redirect` | optional |", self.card)
        self.assertIn("| `benign_twin` | optional |", self.card)
        self.assertIn("| `vector` | optional |", self.card)
        self.assertIn("| `family` | optional |", self.card)
        self.assertIn("| `trigger` | present on every record |", self.card)
        self.assertIn("issues/42", self.card)


if __name__ == "__main__":
    unittest.main()
