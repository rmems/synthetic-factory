#!/usr/bin/env python3
"""Issue #62 leaf tests for the per-dataset card schema declaration."""

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


EVAL_HARNESS = "eval-harness-trajectories"


class EvalHarnessDeclarationTests(unittest.TestCase):
    """Issue #62: thin `meta` vs `designed`/`domain`, plus `plan` string-or-list."""

    def setUp(self):
        self.declaration = card_schema.load(EVAL_HARNESS)
        self.assertIsNotNone(self.declaration, "config/card-schemas is missing #62")
        self.item = {
            "slug": "eval-harness-trajectory-factory",
            "hub": EVAL_HARNESS,
            "pretty": "Eval Harness Trajectories",
            "blurb": "DeepEval/pytest eval-loop leftover-judge episodes.",
            "tags": ["synthetic-data", "trajectories", "evaluation", "pytest"],
        }
        self.card = publisher.render_card(
            self.item,
            records=2203,
            bytes_=12773376,
            first="r01",
            last="r1104",
            payload_names=["batch-r01.jsonl", "batch-r1104.jsonl"],
        )

    def test_declaration_matches_the_observed_union_schema(self):
        features = self.declaration["features"]
        self.assertEqual(
            [feature["name"] for feature in features],
            ["id", "goal", "plan", "steps", "outcome", "reward", "meta"],
        )
        names = {feature["name"]: feature for feature in features}
        self.assertEqual(names["meta"]["dtype"], "json")
        self.assertEqual(names["reward"]["dtype"], "json")
        steps = {feature["name"]: feature for feature in names["steps"]["list"]}
        self.assertEqual(
            set(steps), {"n", "decision_basis", "tool_call", "observation", "reflection"}
        )
        self.assertTrue(steps["reflection"]["optional"])
        tool_call = {feature["name"]: feature for feature in steps["tool_call"]["struct"]}
        self.assertEqual(tool_call["args"]["dtype"], "json")
        self.assertEqual(self.declaration["issues"], [62])

    def test_plan_is_a_mandatory_json_union_not_an_optional_string(self):
        # `plan` is on all 2203 records, so it must not be copied as optional
        # from the #36 example; it is a string on 1961 and a list on 242, which
        # is the union that breaks a `string` cast.
        plan = next(
            feature
            for feature in self.declaration["features"]
            if feature["name"] == "plan"
        )
        self.assertEqual(plan["dtype"], "json")
        self.assertNotIn("optional", plan)
        self.assertIn("1961", plan["note"])
        self.assertIn("242", plan["note"])

    def test_type_varying_and_key_bag_columns_are_declared_json(self):
        self.assertEqual(
            card_schema.json_columns(self.declaration["features"]),
            ["plan", "steps[].tool_call.args", "reward", "meta"],
        )

    def test_declared_data_files_cover_the_published_batches(self):
        self.assertEqual(self.declaration["data_files"], ["data/raw/batch-*.jsonl"])
        self.assertEqual(
            card_schema.payload_coverage_errors(
                self.declaration,
                ["batch-r01.jsonl", "batch-r132.jsonl", "batch-r1104.jsonl"],
            ),
            [],
        )

    def test_card_front_matter_declares_the_default_config_over_raw_batches(self):
        front_matter = self.card.split("---", 2)[1]
        self.assertIn("configs:\n- config_name: default\n", front_matter)
        self.assertIn('    path: "data/raw/batch-*.jsonl"\n', front_matter)
        self.assertIn("  - name: plan\n    dtype: json\n", front_matter)
        self.assertIn("  - name: meta\n    dtype: json\n", front_matter)
        self.assertIn("license: apache-2.0", front_matter)
        self.assertIn("**not training-ready**", self.card)
        self.assertNotIn("optional", front_matter)

    def test_card_body_discloses_the_five_sparse_reward_mill_records(self):
        self.assertIn("## Dataset viewer schema", self.card)
        self.assertNotIn("**Not declared yet.**", self.card)
        for record_id in (
            "srl-r641-networkd-dhcp-ipv4-only-c67a",
            "srl-r642-chrony-maxslewrate-vs-ntpd-ffb5",
            "srl-r643-nft-flowtable-timeout-vs-ipt-035c",
            "srl-r644-podman-events-logger-journald-e10f",
            "srl-r645-buildah-format-oci-vs-docker-b703",
        ):
            with self.subTest(record_id=record_id):
                self.assertIn(f"`{record_id}`", self.card)
        self.assertIn("issues/43", self.card)
        self.assertIn("| `plan` | present on every record |", self.card)
        self.assertIn("| `steps[].reflection` | optional |", self.card)
        self.assertIn("eval_harness_unique_mill", self.card)


if __name__ == "__main__":
    unittest.main()

