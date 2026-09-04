#!/usr/bin/env python3
"""Issue #48 leaf tests for the per-dataset card schema declaration."""

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


SCAN_REMEDIATION = "secret-scan-remediation-trajectories"


class SecretScanRemediationDeclarationTests(unittest.TestCase):
    """Issue #48: `reward` is not uniform, so the parquet index cannot be built.

    Every count asserted here was derived from the published mirror at
    `~/rmems/hf/grok-4.6/secret-scan-remediation-trajectories` (2068 records
    over 1034 raw shards, 31549 steps), not copied from the issue text.
    """

    def setUp(self):
        self.declaration = card_schema.load(SCAN_REMEDIATION)
        self.assertIsNotNone(self.declaration, "config/card-schemas is missing #48")
        self.item = {
            "slug": "secret-scan-remediation-factory",
            "hub": SCAN_REMEDIATION,
            "pretty": "Secret Scan Remediation Trajectories",
            "blurb": "Secret-scan leftover-allowlist / baseline remediation.",
            "tags": ["synthetic-data", "trajectories", "secrets", "security"],
        }
        self.card = publisher.render_card(
            self.item,
            records=2068,
            bytes_=16694229,
            first="r01",
            last="r1034",
            payload_names=["batch-r01.jsonl", "batch-r1034.jsonl"],
        )

    def test_declaration_matches_the_observed_union_schema(self):
        names = {feature["name"]: feature for feature in self.declaration["features"]}
        self.assertEqual(
            set(names),
            {"id", "goal", "plan", "steps", "outcome", "reward", "meta"},
        )
        # Unlike long-horizon-coding, `plan` is a string on all 2068 records.
        self.assertNotIn("optional", names["plan"])
        self.assertEqual(names["plan"]["dtype"], "string")
        self.assertEqual(names["reward"]["dtype"], "json")
        self.assertEqual(names["meta"]["dtype"], "json")
        steps = {feature["name"]: feature for feature in names["steps"]["list"]}
        self.assertEqual(
            set(steps), {"n", "decision_basis", "tool_call", "observation", "reflection"}
        )
        self.assertTrue(steps["reflection"]["optional"])
        for required in ("n", "decision_basis", "observation"):
            self.assertNotIn("optional", steps[required])
        tool_call = {feature["name"]: feature for feature in steps["tool_call"]["struct"]}
        self.assertEqual(set(tool_call), {"name", "args"})
        self.assertEqual(tool_call["args"]["dtype"], "json")
        self.assertEqual(self.declaration["issues"], [48])

    def test_key_bag_columns_are_declared_json(self):
        self.assertEqual(
            card_schema.json_columns(self.declaration["features"]),
            ["steps[].tool_call.args", "reward", "meta"],
        )

    def test_data_files_cover_the_published_batch_payload(self):
        # The mirror publishes only `batch-rNN.jsonl`; there is no legacy
        # `episodes.jsonl` to carry, so the default glob is the whole payload.
        self.assertEqual(self.declaration["data_files"], ["data/raw/batch-*.jsonl"])
        self.assertEqual(
            card_schema.payload_coverage_errors(
                self.declaration, ["batch-r01.jsonl", "batch-r1034.jsonl"]
            ),
            [],
        )

    def test_card_front_matter_declares_the_default_config_over_raw_batches(self):
        front_matter = self.card.split("---", 2)[1]
        self.assertIn("configs:\n- config_name: default\n", front_matter)
        self.assertIn('    path: "data/raw/batch-*.jsonl"\n', front_matter)
        self.assertIn("dataset_info:\n  features:\n", front_matter)
        self.assertIn("  - name: reward\n    dtype: json\n", front_matter)
        self.assertIn("  - name: meta\n    dtype: json\n", front_matter)
        self.assertIn("      - name: args\n        dtype: json\n", front_matter)
        # `optional` is a card annotation only; it must not reach the YAML.
        self.assertIn("    - name: reflection\n      dtype: string\n", front_matter)
        self.assertNotIn("optional", front_matter)
        # license/tags/status claims stay exactly where they were.
        self.assertIn("license: apache-2.0", front_matter)
        self.assertIn("**not training-ready**", self.card)

    def test_card_body_discloses_the_reward_variants_and_optional_reflection(self):
        self.assertIn("## Dataset viewer schema", self.card)
        self.assertNotIn("**Not declared yet.**", self.card)
        self.assertIn("| `steps[].reflection` | optional |", self.card)
        self.assertIn("present on 158 of 31549 steps", self.card)
        self.assertIn("`pr` on 1912, `handoff` on 967 and `xfailed` on 12", self.card)
        self.assertIn("### Known payload disclosures", self.card)
        self.assertIn("`reward` has five key sets", self.card)
        self.assertIn("no dest-stamped foreign payload", self.card)
        self.assertIn("`decision_basis`", self.card)


if __name__ == "__main__":
    unittest.main()
