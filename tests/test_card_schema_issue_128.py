#!/usr/bin/env python3
"""Issue #69 leaf tests for the per-dataset card schema declaration."""

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


OBSERVABILITY_DEBUG = "observability-debug-trajectories"


class ObservabilityDebugDeclarationTests(unittest.TestCase):
    """Issue #69: episode-only top-level extras beside a designed-only `meta`."""

    def setUp(self):
        self.declaration = card_schema.load(OBSERVABILITY_DEBUG)
        self.assertIsNotNone(self.declaration, "config/card-schemas is missing #69")
        self.item = {
            "slug": "observability-debug-factory",
            "hub": OBSERVABILITY_DEBUG,
            "pretty": "Observability Debug Trajectories",
            "blurb": "Observability leftover-lie (wrong dashboard / dropped label) episodes.",
            "tags": ["synthetic-data", "trajectories", "observability", "tracing"],
        }
        self.card = publisher.render_card(
            self.item,
            records=1749,
            bytes_=10567586,
            first="r01",
            last="r875",
            payload_names=["batch-r01.jsonl", "batch-r500.jsonl", "batch-r875.jsonl"],
        )

    def test_declaration_matches_the_observed_union_schema(self):
        features = self.declaration["features"]
        self.assertEqual(
            [feature["name"] for feature in features],
            [
                "id",
                "goal",
                "plan",
                "lie",
                "red_herring",
                "diagnosis",
                "recovery",
                "verification",
                "steps",
                "outcome",
                "reward",
                "meta",
            ],
        )
        names = {feature["name"]: feature for feature in features}
        # `plan` is a string on all 1749 records here, unlike #36 where it is optional.
        self.assertNotIn("optional", names["plan"])
        self.assertEqual(names["plan"]["dtype"], "string")
        self.assertEqual(names["meta"]["dtype"], "json")
        self.assertEqual(names["reward"]["dtype"], "json")
        steps = {feature["name"]: feature for feature in names["steps"]["list"]}
        self.assertEqual(
            set(steps), {"n", "decision_basis", "tool_call", "observation", "reflection"}
        )
        self.assertTrue(steps["reflection"]["optional"])
        tool_call = {feature["name"]: feature for feature in steps["tool_call"]["struct"]}
        self.assertEqual(tool_call["args"]["dtype"], "json")
        self.assertEqual(self.declaration["issues"], [69])

    def test_episode_only_extras_are_optional_typed_structs_not_json(self):
        names = {feature["name"]: feature for feature in self.declaration["features"]}
        for extra in ("lie", "red_herring", "diagnosis", "recovery", "verification"):
            with self.subTest(extra=extra):
                feature = names[extra]
                self.assertTrue(feature["optional"], f"{extra} must be optional")
                # Each extra has one uniform key set across all 316 episode records,
                # so it is declared as a searchable struct rather than a json blob.
                self.assertIn("struct", feature)
        red_herring = {
            child["name"]: child for child in names["red_herring"]["struct"]
        }
        self.assertEqual(
            set(red_herring), {"dashboard", "why_plausible", "dismissed_at_step"}
        )
        self.assertTrue(red_herring["dismissed_at_step"]["optional"])
        self.assertEqual(red_herring["dismissed_at_step"]["dtype"], "int64")
        for extra in ("diagnosis", "recovery", "verification"):
            with self.subTest(extra=extra):
                child = {c["name"]: c for c in names[extra]["struct"]}
                self.assertEqual(child["step"]["dtype"], "int64")

    def test_only_the_real_key_bags_are_declared_json(self):
        self.assertEqual(
            card_schema.json_columns(self.declaration["features"]),
            ["steps[].tool_call.args", "reward", "meta"],
        )

    def test_card_front_matter_declares_the_default_config_over_raw_batches(self):
        front_matter = self.card.split("---", 2)[1]
        self.assertIn("configs:\n- config_name: default\n", front_matter)
        self.assertIn('    path: "data/raw/batch-*.jsonl"\n', front_matter)
        self.assertIn("dataset_info:\n  features:\n", front_matter)
        self.assertIn("  - name: meta\n    dtype: json\n", front_matter)
        self.assertIn(
            "  - name: lie\n    struct:\n    - name: kind\n      dtype: string\n",
            front_matter,
        )
        # The card-only annotations never reach the emitted YAML.
        self.assertNotIn("optional:", front_matter)
        # license/tags/status claims stay exactly where they were.
        self.assertIn("license: apache-2.0", front_matter)
        self.assertIn("**not training-ready**", self.card)

    def test_card_body_discloses_the_dest_stamped_sparse_reward_row(self):
        self.assertIn("## Dataset viewer schema", self.card)
        self.assertNotIn("**Not declared yet.**", self.card)
        self.assertIn("`srl-r500-networkd-dhcp-ipv4-only-c67a`", self.card)
        self.assertIn("issues/43", self.card)
        self.assertIn("| `lie` | optional |", self.card)
        self.assertIn("| `red_herring.dismissed_at_step` | optional |", self.card)
        self.assertIn("| `steps[].reflection` | optional |", self.card)
        self.assertIn("| `plan` | present on every record |", self.card)


if __name__ == "__main__":
    unittest.main()

