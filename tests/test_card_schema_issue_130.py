#!/usr/bin/env python3
"""Issue #70 leaf tests for the per-dataset card schema declaration."""

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


QUEUE_BACKPRESSURE = "queue-backpressure-trajectories"


class QueueBackpressureDeclarationTests(unittest.TestCase):
    """Issue #70: thin `meta` vs designed/lane leftover schema.

    Counts asserted here were derived read-only from the published mirror
    ``~/rmems/hf/grok-4.6/queue-backpressure-trajectories``: 141 shards
    ``batch-r01``-``batch-r141``, 282 records, 0 parse failures, 4649 steps.
    """

    def setUp(self):
        self.declaration = card_schema.load(QUEUE_BACKPRESSURE)
        self.assertIsNotNone(self.declaration, "config/card-schemas is missing #70")
        self.item = {
            "slug": "queue-backpressure-factory",
            "hub": QUEUE_BACKPRESSURE,
            "pretty": "Queue Backpressure Trajectories",
            "blurb": "Queue leftover-bound / backpressure episodes.",
            "tags": ["synthetic-data", "queues", "backpressure"],
        }
        self.card = publisher.render_card(
            self.item,
            records=282,
            bytes_=2048818,
            first="r01",
            last="r141",
            payload_names=["batch-r01.jsonl", "batch-r74.jsonl", "batch-r141.jsonl"],
        )

    def test_declaration_matches_the_observed_union_schema(self):
        names = {feature["name"]: feature for feature in self.declaration["features"]}
        self.assertEqual(
            set(names),
            {"id", "goal", "plan", "steps", "outcome", "reward", "meta"},
        )
        # `plan` is a string on all 282 records here, unlike #36 where it is
        # optional: declaring it optional would understate the payload.
        self.assertEqual(names["plan"]["dtype"], "string")
        self.assertNotIn("optional", names["plan"])
        self.assertEqual(names["meta"]["dtype"], "json")
        self.assertEqual(names["reward"]["dtype"], "json")
        steps = {feature["name"]: feature for feature in names["steps"]["list"]}
        self.assertEqual(
            set(steps), {"n", "decision_basis", "tool_call", "observation", "reflection"}
        )
        self.assertTrue(steps["reflection"]["optional"])
        self.assertIn("4448 of 4649", steps["reflection"]["note"])
        tool_call = {feature["name"]: feature for feature in steps["tool_call"]["struct"]}
        self.assertEqual(tool_call["name"]["dtype"], "string")
        self.assertEqual(tool_call["args"]["dtype"], "json")
        self.assertEqual(self.declaration["issues"], [70])

    def test_key_bag_columns_are_declared_json(self):
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
        self.assertIn("  - name: reward\n    dtype: json\n", front_matter)
        self.assertIn("  - name: plan\n    dtype: string\n", front_matter)
        # license/tags/status claims stay exactly where they were.
        self.assertIn("license: apache-2.0", front_matter)
        self.assertIn("**not training-ready**", self.card)

    def test_card_body_discloses_the_thin_meta_and_lane_records(self):
        self.assertIn("## Dataset viewer schema", self.card)
        self.assertNotIn("**Not declared yet.**", self.card)
        self.assertIn("`qbp-r01-amqp-prefetch-unbounded`", self.card)
        self.assertIn("`qbp-r09-huey-immediate-false-7b22`", self.card)
        self.assertIn("`qbp-r2-sqs-inflight-p3`", self.card)
        self.assertIn("`qbp-r3-rabbit-prefetch-p13`", self.card)
        self.assertIn("| `steps[].reflection` | optional |", self.card)
        self.assertIn("| `plan` | present on every record |", self.card)

    def test_card_body_owns_the_six_dest_stamped_sir_records(self):
        for record_id in (
            "sir-r74-bleve-alias-leftover3c-rebuild",
            "sir-r74-bleve-drop-leftover3c-handoff",
            "sir-r75-lucene-nrt-leftover3c-rebuild",
            "sir-r75-lucene-drop-leftover3c-handoff",
            "sir-r76-pg-trgm-conc-leftover3c-rebuild",
            "sir-r76-pg-trgm-drop-leftover3c-handoff",
        ):
            self.assertIn(f"`{record_id}`", self.card)
        # The class is disclosed as unowned, not as already tracked: rendering
        # it under a "Tracked in #43, #44" link would be an overclaim.
        self.assertIn("No GitHub issue currently owns this class", self.card)
        sir_disclosure = next(
            item
            for item in self.declaration["disclosures"]
            if any(record_id.startswith("sir-") for record_id in item["ids"])
        )
        self.assertEqual(sir_disclosure["issues"], [])
        self.assertEqual(len(sir_disclosure["ids"]), 6)

    def test_same_factory_leftover_naming_is_not_claimed_as_foreign_payload(self):
        self.assertIn("advertised leftover-bound mechanic", self.card)
        self.assertIn("96 name `leftover` in the id", self.card)
        self.assertIn("public `decision_basis` (4649 of 4649)", self.card)


if __name__ == "__main__":
    unittest.main()

