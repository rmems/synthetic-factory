#!/usr/bin/env python3
"""Issue #40 leaf tests for the per-dataset card schema declaration."""

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


SAFETY_CALIBRATION = "safety-calibration-cases"


class SafetyCalibrationDeclarationTests(unittest.TestCase):
    """Issue #40: `reward.recovered_overrefusal` plus mutually exclusive extras.

    Counts below are derived from the published mirror
    (`~/rmems/hf/grok-4.6/safety-calibration-cases`, 5354 shards / 16062 records
    / 142873 steps), not transcribed from the issue body.
    """

    def setUp(self):
        self.declaration = card_schema.load(SAFETY_CALIBRATION)
        self.assertIsNotNone(self.declaration, "config/card-schemas is missing #40")
        self.item = {
            "slug": "safety-calibration-factory",
            "hub": SAFETY_CALIBRATION,
            "pretty": "Safety Calibration Cases",
            "blurb": "Safety leftover-refusal calibration cases.",
            "tags": ["synthetic-data", "safety", "calibration", "refusal"],
        }
        self.card = publisher.render_card(
            self.item,
            records=16062,
            bytes_=76017664,
            first="r01",
            last="r5354",
            payload_names=["batch-r01.jsonl", "batch-r5354.jsonl"],
        )

    def test_declaration_matches_the_observed_union_schema(self):
        names = {feature["name"]: feature for feature in self.declaration["features"]}
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
                "vector",
                "benign_twin",
            },
        )
        self.assertEqual(names["should_refuse"]["dtype"], "bool")
        for required in ("id", "goal", "case_type", "decision", "rationale", "outcome"):
            self.assertNotIn("optional", names[required], required)
        # The 18 annotation-free records and the three mutually exclusive extras.
        for optional in ("trigger", "redirect", "vector", "benign_twin"):
            with self.subTest(field=optional):
                self.assertTrue(names[optional]["optional"])
                self.assertEqual(names[optional]["dtype"], "string")
                self.assertIn("of 16062 records", names[optional]["note"])
        steps = {feature["name"]: feature for feature in names["steps"]["list"]}
        # No `reflection` here: every one of the 142873 steps has the same four keys.
        self.assertEqual(set(steps), {"n", "decision_basis", "tool_call", "observation"})
        tool_call = {feature["name"]: feature for feature in steps["tool_call"]["struct"]}
        self.assertEqual(set(tool_call), {"name", "args"})
        self.assertEqual(self.declaration["issues"], [40])

    def test_key_bag_columns_are_declared_json(self):
        # `reward` is the column the viewer died casting; `meta` is a key-bag too
        # because `sim_or_real` is absent from 771 of 16062 records.
        self.assertEqual(
            card_schema.json_columns(self.declaration["features"]),
            ["steps[].tool_call.args", "reward", "meta"],
        )
        names = {feature["name"]: feature for feature in self.declaration["features"]}
        self.assertIn("recovered_overrefusal", names["reward"]["note"])
        self.assertIn("sim_or_real", names["meta"]["note"])

    def test_card_front_matter_declares_the_default_config_over_raw_batches(self):
        front_matter = self.card.split("---", 2)[1]
        self.assertIn("configs:\n- config_name: default\n", front_matter)
        self.assertIn('    path: "data/raw/batch-*.jsonl"\n', front_matter)
        self.assertIn("  - name: reward\n    dtype: json\n", front_matter)
        self.assertIn("  - name: should_refuse\n    dtype: bool\n", front_matter)
        self.assertIn("  - name: benign_twin\n    dtype: string\n", front_matter)
        self.assertNotIn("optional", front_matter)
        self.assertIn("license: apache-2.0", front_matter)
        self.assertIn("**not training-ready**", self.card)

    def test_card_body_discloses_the_case_type_split_and_the_annotation_gap(self):
        self.assertIn("## Dataset viewer schema", self.card)
        self.assertNotIn("**Not declared yet.**", self.card)
        # The 5354 x 3 split the issue asks the card to disclose.
        self.assertIn("5354 / 5354 / 5354", self.card)
        for case_type in ("correct_refusal", "incorrect_refusal", "missed_refusal"):
            self.assertIn(f"`{case_type}`", self.card)
        self.assertIn("| `trigger` | optional |", self.card)
        self.assertIn("| `benign_twin` | optional |", self.card)
        self.assertIn("`saf-r123-pickle-load-uploads`", self.card)
        self.assertIn("`saf-r128-sourcemap-secrets`", self.card)

    def test_every_disclosed_record_id_is_a_safety_case_id(self):
        ids = [
            record_id
            for disclosure in self.declaration["disclosures"]
            for record_id in disclosure["ids"]
        ]
        self.assertEqual(len(ids), 18)
        self.assertEqual(len(set(ids)), 18)
        for record_id in ids:
            with self.subTest(record_id=record_id):
                self.assertRegex(record_id, r"^saf-r12[3-8]-")


if __name__ == "__main__":
    unittest.main()

