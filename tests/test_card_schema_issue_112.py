#!/usr/bin/env python3
"""Issue #52 leaf tests for the per-dataset card schema declaration."""

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


WEBSOCKET_RECONNECT = "websocket-reconnect-trajectories"


class WebsocketReconnectDeclarationTests(unittest.TestCase):
    """Issue #52: thin `meta` in batch-r01 vs `designed`/`domain`/`stack` later."""

    def setUp(self):
        self.declaration = card_schema.load(WEBSOCKET_RECONNECT)
        self.assertIsNotNone(self.declaration, "config/card-schemas is missing #52")
        self.item = {
            "slug": "websocket-reconnect-factory",
            "hub": WEBSOCKET_RECONNECT,
            "pretty": "Websocket Reconnect Trajectories",
            "blurb": "WebSocket leftover-resume / reconnect episodes.",
            "tags": ["synthetic-data", "trajectories", "websocket"],
        }
        self.card = publisher.render_card(
            self.item,
            records=322,
            bytes_=2375680,
            first="01",
            last="161",
            payload_names=["batch-r01.jsonl", "batch-r161.jsonl"],
        )

    def test_declaration_matches_the_observed_union_schema(self):
        names = {feature["name"]: feature for feature in self.declaration["features"]}
        self.assertEqual(
            set(names),
            {"id", "goal", "plan", "steps", "outcome", "reward", "meta"},
        )
        # Unlike #36's dataset, every one of the 322 records carries a `plan`.
        self.assertNotIn("optional", names["plan"])
        self.assertEqual(names["plan"]["dtype"], "string")
        self.assertEqual(names["meta"]["dtype"], "json")
        self.assertEqual(names["reward"]["dtype"], "json")
        steps = {feature["name"]: feature for feature in names["steps"]["list"]}
        self.assertEqual(
            set(steps), {"n", "decision_basis", "tool_call", "observation", "reflection"}
        )
        self.assertTrue(steps["reflection"]["optional"])
        self.assertIn("5081 of 5314 steps", steps["reflection"]["note"])
        tool_call = {feature["name"]: feature for feature in steps["tool_call"]["struct"]}
        self.assertEqual(set(tool_call), {"name", "args"})
        self.assertEqual(tool_call["args"]["dtype"], "json")
        self.assertEqual(self.declaration["issues"], [52])

    def test_key_bag_columns_are_declared_json(self):
        self.assertEqual(
            card_schema.json_columns(self.declaration["features"]),
            ["steps[].tool_call.args", "reward", "meta"],
        )

    def test_meta_note_records_the_thin_and_lane_subsets(self):
        meta = next(
            feature
            for feature in self.declaration["features"]
            if feature["name"] == "meta"
        )
        for key in ("kind", "seed", "designed", "domain", "stack"):
            self.assertIn(f"`{key}`", meta["note"])
        self.assertIn("312 of 322", meta["note"])
        self.assertIn("`lane` on 12 of 322", meta["note"])

    def test_card_front_matter_declares_the_default_config_over_raw_batches(self):
        front_matter = self.card.split("---", 2)[1]
        self.assertIn("configs:\n- config_name: default\n", front_matter)
        self.assertIn('    path: "data/raw/batch-*.jsonl"\n', front_matter)
        self.assertIn("dataset_info:\n  features:\n", front_matter)
        self.assertIn("  - name: meta\n    dtype: json\n", front_matter)
        self.assertIn("  - name: reward\n    dtype: json\n", front_matter)
        # license/tags/status claims stay exactly where they were.
        self.assertIn("license: apache-2.0", front_matter)
        self.assertIn("**not training-ready**", self.card)

    def test_card_body_discloses_the_ten_thin_meta_records(self):
        self.assertIn("## Dataset viewer schema", self.card)
        self.assertIn("`wsr-r01-resubscribe-on-reconnect`", self.card)
        self.assertIn("`wsr-r11-close-1005-backoff-7c2d`", self.card)
        self.assertIn("`meta.lane`", self.card)
        self.assertIn("no dest-stamped foreign payload", self.card)
        self.assertIn("does not infer generator-file provenance", self.card)
        self.assertNotIn("mill_wsr_leftover", self.card)
        self.assertIn("| `steps[].reflection` | optional |", self.card)
        self.assertIn("| `plan` | present on every record |", self.card)
        self.assertNotIn("**Not declared yet.**", self.card)


if __name__ == "__main__":
    unittest.main()
