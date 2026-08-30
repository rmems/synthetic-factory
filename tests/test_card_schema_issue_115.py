#!/usr/bin/env python3
"""Issue #54 leaf tests for the per-dataset card schema declaration."""

try:
    # The shared helpers live in test_card_schema_integration once the infra
    # branch's split of test_card_schema.py lands beneath this leaf.
    import test_card_schema_integration as _shared
except ModuleNotFoundError:  # pre-split trees still ship the monolith
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


EMAIL_WEBHOOK = "email-webhook-retry-trajectories"


class EmailWebhookRetryDeclarationTests(unittest.TestCase):
    """Issue #54: 190 records over 95 shards, thin `meta` first, leftover mill inside.

    Every count asserted here was derived from the read-only published mirror at
    `~/rmems/hf/grok-4.6/email-webhook-retry-trajectories/`, not from the issue
    text: 190 records, 3131 steps, 0 parse failures.
    """

    PAYLOAD_NAMES = [f"batch-r{index:02d}.jsonl" for index in range(1, 96)]

    def setUp(self):
        self.declaration = card_schema.load(EMAIL_WEBHOOK)
        self.assertIsNotNone(self.declaration, "config/card-schemas is missing #54")
        self.item = {
            "slug": "email-webhook-retry-factory",
            "hub": EMAIL_WEBHOOK,
            "pretty": "Email Webhook Retry Trajectories",
            "blurb": "Email-webhook leftover event-PK retry episodes.",
            "tags": ["synthetic-data", "email", "webhooks"],
        }
        self.card = publisher.render_card(
            self.item,
            records=190,
            bytes_=1385245,
            first="r01",
            last="r95",
            payload_names=self.PAYLOAD_NAMES,
        )

    def test_declaration_matches_the_observed_union_schema(self):
        features = self.declaration["features"]
        self.assertEqual(
            [feature["name"] for feature in features],
            ["id", "goal", "plan", "steps", "outcome", "reward", "meta"],
        )
        names = {feature["name"]: feature for feature in features}
        # Unlike long-horizon-coding, every top-level field is on all 190
        # records -- `plan` included. Declaring it optional here would be a
        # transcription of the sibling dataset, not of this payload.
        for name in ("id", "goal", "plan", "outcome"):
            with self.subTest(field=name):
                self.assertEqual(names[name]["dtype"], "string")
                self.assertNotIn("optional", names[name])
        self.assertEqual(names["meta"]["dtype"], "json")
        self.assertEqual(names["reward"]["dtype"], "json")
        self.assertEqual(self.declaration["issues"], [54])

    def test_step_struct_declares_the_only_optional_field(self):
        top = {feature["name"]: feature for feature in self.declaration["features"]}
        steps = {feature["name"]: feature for feature in top["steps"]["list"]}
        self.assertEqual(
            set(steps), {"n", "decision_basis", "tool_call", "observation", "reflection"}
        )
        self.assertTrue(steps["reflection"]["optional"])
        self.assertIn("2989 of 3131", steps["reflection"]["note"])
        for name in ("n", "decision_basis", "tool_call", "observation"):
            with self.subTest(field=name):
                self.assertNotIn("optional", steps[name])
        tool_call = {
            feature["name"]: feature for feature in steps["tool_call"]["struct"]
        }
        self.assertEqual(tool_call["name"]["dtype"], "string")
        self.assertEqual(tool_call["args"]["dtype"], "json")

    def test_key_bag_columns_are_declared_json(self):
        self.assertEqual(
            card_schema.json_columns(self.declaration["features"]),
            ["steps[].tool_call.args", "reward", "meta"],
        )

    def test_declared_glob_covers_all_ninety_five_published_shards(self):
        self.assertEqual(
            card_schema.payload_coverage_errors(self.declaration, self.PAYLOAD_NAMES),
            [],
        )

    def test_card_front_matter_declares_the_default_config_over_raw_batches(self):
        front_matter = self.card.split("---", 2)[1]
        self.assertIn("configs:\n- config_name: default\n", front_matter)
        self.assertIn('    path: "data/raw/batch-*.jsonl"\n', front_matter)
        self.assertIn("  - name: meta\n    dtype: json\n", front_matter)
        self.assertIn("  - name: reward\n    dtype: json\n", front_matter)
        # `meta` as a struct is exactly the cast the datasets-server died on.
        self.assertNotIn("  - name: meta\n    struct:\n", front_matter)
        self.assertIn("license: apache-2.0", front_matter)
        self.assertIn("**not training-ready**", self.card)
        self.assertNotIn("**Not declared yet.**", self.card)

    def test_card_body_discloses_the_leftover_mill_and_the_thin_meta_records(self):
        self.assertIn("## Dataset viewer schema", self.card)
        for record_id in (
            "sir-r56-meili-swap-leftover3c-rebuild",
            "sir-r56-meili-drop-index-leftover3c-handoff",
            "sir-r57-typesense-alias-leftover3c-rebuild",
            "sir-r57-typesense-drop-coll-leftover3c-handoff",
            "sir-r58-sonic-push-leftover3c-rebuild",
            "sir-r58-sonic-drop-bucket-leftover3c-handoff",
        ):
            with self.subTest(record_id=record_id):
                self.assertIn(f"`{record_id}`", self.card)
        self.assertIn("issues/43", self.card)
        self.assertIn("issues/44", self.card)
        for record_id in (
            "ewr-r01-webhook-retry-dup-delivery",
            "ewr-r09-ses-event-dest-unique-5e08",
        ):
            with self.subTest(record_id=record_id):
                self.assertIn(f"`{record_id}`", self.card)
        self.assertIn("| `steps[].reflection` | optional |", self.card)
        self.assertNotIn("| `plan` | optional |", self.card)

    def test_leftover_mill_disclosure_lists_exactly_the_frozen_six_ids(self):
        mill = [
            disclosure
            for disclosure in self.declaration["disclosures"]
            if 43 in disclosure["issues"] and disclosure["ids"]
        ]
        self.assertEqual(len(mill), 1, "expected one leftover-mill id disclosure")
        self.assertEqual(len(mill[0]["ids"]), 6)
        self.assertTrue(
            all(record_id.startswith("sir-") for record_id in mill[0]["ids"]),
            mill[0]["ids"],
        )


if __name__ == "__main__":
    unittest.main()

