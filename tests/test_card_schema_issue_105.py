#!/usr/bin/env python3
"""Issue #46 leaf tests for the per-dataset card schema declaration."""

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


API_CONTRACT = "api-contract-migration-trajectories"


class ApiContractMigrationDeclarationTests(unittest.TestCase):
    """Issue #46: leftover mill mix plus `meta` drift in the contract-migration dump.

    Counts come from a read-only scan of the published mirror
    ``~/rmems/hf/grok-4.6/api-contract-migration-trajectories``: 4006 shards,
    8012 records, 130021 steps, 0 parse failures.
    """

    def setUp(self):
        self.declaration = card_schema.load(API_CONTRACT)
        self.assertIsNotNone(self.declaration, "config/card-schemas is missing #46")
        self.item = {
            "slug": "api-contract-migration-factory",
            "hub": API_CONTRACT,
            "pretty": "Api Contract Migration Trajectories",
            "blurb": "OpenAPI / protocol leftover contract-migration episodes.",
            "tags": ["synthetic-data", "trajectories", "openapi"],
        }
        self.card = publisher.render_card(
            self.item,
            records=8012,
            bytes_=78346988,
            first="r01",
            last="r999",
            payload_names=["batch-r01.jsonl", "batch-r3714.jsonl", "batch-r98.jsonl"],
        )

    def test_declaration_matches_the_observed_union_schema(self):
        names = {feature["name"]: feature for feature in self.declaration["features"]}
        self.assertEqual(
            set(names),
            {"id", "goal", "plan", "steps", "outcome", "reward", "meta"},
        )
        # Unlike long-horizon-coding, every one of the 8012 records carries a
        # `plan`, so it is declared present rather than optional.
        self.assertNotIn("optional", names["plan"])
        self.assertEqual(names["meta"]["dtype"], "json")
        self.assertEqual(names["reward"]["dtype"], "json")
        steps = {feature["name"]: feature for feature in names["steps"]["list"]}
        self.assertEqual(
            set(steps), {"n", "decision_basis", "tool_call", "observation", "reflection"}
        )
        self.assertTrue(steps["reflection"]["optional"])
        self.assertIn("129909 of 130021 steps", steps["reflection"]["note"])
        tool_call = {feature["name"]: feature for feature in steps["tool_call"]["struct"]}
        self.assertEqual(tool_call["args"]["dtype"], "json")
        self.assertEqual(self.declaration["issues"], [46])

    def test_key_bag_columns_are_declared_json(self):
        self.assertEqual(
            card_schema.json_columns(self.declaration["features"]),
            ["steps[].tool_call.args", "reward", "meta"],
        )

    def test_reward_note_names_every_extra_key_found_in_the_payload(self):
        reward = next(
            feature
            for feature in self.declaration["features"]
            if feature["name"] == "reward"
        )
        # The issue body listed only breaking_oasdiff / xfailed / handoff; the
        # mirror also carries a single `skipped`.
        for key in ("breaking_oasdiff", "xfailed", "skipped", "handoff"):
            with self.subTest(key=key):
                self.assertIn(f"`{key}`", reward["note"])

    def test_card_front_matter_declares_the_default_config_over_raw_batches(self):
        front_matter = self.card.split("---", 2)[1]
        self.assertIn("configs:\n- config_name: default\n", front_matter)
        self.assertIn('    path: "data/raw/batch-*.jsonl"\n', front_matter)
        self.assertIn("dataset_info:\n  features:\n", front_matter)
        self.assertIn("  - name: meta\n    dtype: json\n", front_matter)
        self.assertIn("  - name: reward\n    dtype: json\n", front_matter)
        self.assertIn("license: apache-2.0", front_matter)
        self.assertIn("**not training-ready**", self.card)

    def test_card_body_discloses_the_two_leftover_mill_records(self):
        self.assertIn("## Dataset viewer schema", self.card)
        self.assertIn("`dbc-r3714-buildkit-cache-mount-id-leftover`", self.card)
        self.assertIn("`dbc-r3714-buildkit-cache-mount-sharing-locked-leftover`", self.card)
        self.assertIn("### Known payload disclosures", self.card)
        self.assertNotIn("**Not declared yet.**", self.card)

    def test_card_body_discloses_the_six_thin_meta_records(self):
        for record_id in (
            "acm-r01-disc-wallet-map-b7e2",
            "acm-r01-orders-v2-email-req-4c91",
            "acm-r02-addprop-reqid-a61e",
            "acm-r02-callback-hmac256-9b30",
            "acm-r98-oas31-null-phone-d4a2",
            "acm-r98-idem-header-sunset-7e19",
        ):
            with self.subTest(record_id=record_id):
                self.assertIn(f"`{record_id}`", self.card)
        self.assertIn("| `steps[].reflection` | optional |", self.card)

    def test_declared_globs_cover_every_published_shard_name(self):
        # The mirror publishes 4006 shards and nothing but `batch-rNN.jsonl`.
        self.assertEqual(
            card_schema.payload_coverage_errors(
                self.declaration,
                ["batch-r01.jsonl", "batch-r98.jsonl", "batch-r3714.jsonl", "batch-r4006.jsonl"],
            ),
            [],
        )
        self.assertTrue(
            card_schema.payload_coverage_errors(self.declaration, ["episodes.jsonl"])
        )


if __name__ == "__main__":
    unittest.main()

