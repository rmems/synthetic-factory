#!/usr/bin/env python3
"""Issue #47 leaf tests for the per-dataset card schema declaration."""

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


EXPECTED_FEATURE_MANIFEST = (
    ("id", "string", False),
    ("goal", "string", False),
    ("plan", "string", False),
    ("steps", "list", False),
    ("steps[].n", "int64", False),
    ("steps[].decision_basis", "string", False),
    ("steps[].tool_call", "struct", False),
    ("steps[].tool_call.name", "string", False),
    ("steps[].tool_call.args", "json", False),
    ("steps[].observation", "string", False),
    ("steps[].reflection", "string", True),
    ("outcome", "string", False),
    ("reward", "json", False),
    ("meta", "json", False),
)


def feature_manifest(features, prefix=""):
    """Flatten a declaration without consulting the independent expected manifest."""
    manifest = []
    for feature in features:
        path = f"{prefix}{feature['name']}"
        encodings = [key for key in ("dtype", "list", "struct") if key in feature]
        if len(encodings) != 1:
            raise AssertionError(f"{path} has {len(encodings)} feature encodings")
        encoding = encodings[0]
        manifest.append(
            (
                path,
                feature[encoding] if encoding == "dtype" else encoding,
                feature.get("optional", False),
            )
        )
        if encoding == "list":
            manifest.extend(feature_manifest(feature["list"], f"{path}[]."))
        elif encoding == "struct":
            manifest.extend(feature_manifest(feature["struct"], f"{path}."))
    return tuple(manifest)


class LogRedactionDeclarationTests(unittest.TestCase):
    """Issue #47: thin `meta` vs `designed` / `domain` / `stack`, plus reward extras."""

    DATASET = "log-redaction-trajectories"

    def setUp(self):
        self.declaration = card_schema.load(self.DATASET)
        self.assertIsNotNone(self.declaration, "config/card-schemas is missing #47")
        self.item = {
            "slug": "log-redaction-factory",
            "hub": self.DATASET,
            "pretty": "Log Redaction Trajectories",
            "blurb": "Log leftover-secret redaction vs mute-logger episodes.",
            "tags": ["synthetic-data", "trajectories", "logging", "redaction", "privacy"],
        }
        self.card = publisher.render_card(
            self.item,
            records=344,
            bytes_=1928793,
            first="r01",
            last="r172",
            payload_names=["batch-r01.jsonl", "batch-r172.jsonl"],
        )

    def test_complete_feature_manifest_matches_the_independent_data_scan(self):
        # This oracle was derived from the read-only 344-record scan. It is
        # intentionally separate from the declaration so omitted fields, wrong
        # fixed dtypes, and incorrect required/optional flags cannot self-validate.
        self.assertEqual(feature_manifest(self.declaration["features"]), EXPECTED_FEATURE_MANIFEST)

    def test_declaration_matches_the_observed_union_schema(self):
        names = {feature["name"]: feature for feature in self.declaration["features"]}
        self.assertEqual(
            set(names),
            {"id", "goal", "plan", "steps", "outcome", "reward", "meta"},
        )
        # Unlike #36, every one of the 344 records carries `plan`, so it is not
        # declared optional here.
        self.assertNotIn("optional", names["plan"])
        self.assertEqual(names["plan"]["dtype"], "string")
        self.assertEqual(names["meta"]["dtype"], "json")
        self.assertEqual(names["reward"]["dtype"], "json")
        steps = {feature["name"]: feature for feature in names["steps"]["list"]}
        self.assertEqual(
            set(steps), {"n", "decision_basis", "tool_call", "observation", "reflection"}
        )
        self.assertTrue(steps["reflection"]["optional"])
        self.assertNotIn("optional", steps["decision_basis"])
        tool_call = {feature["name"]: feature for feature in steps["tool_call"]["struct"]}
        self.assertEqual(set(tool_call), {"name", "args"})
        self.assertEqual(tool_call["args"]["dtype"], "json")
        self.assertEqual(self.declaration["issues"], [47])
        self.assertEqual(self.declaration["data_files"], ["data/raw/batch-*.jsonl"])

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
        # Card-only annotations must never reach the feature encoding.
        self.assertNotIn("optional", front_matter)
        self.assertIn("license: apache-2.0", front_matter)
        self.assertIn("**not training-ready**", self.card)

    def test_card_body_discloses_the_thin_meta_and_lane_records(self):
        self.assertIn("## Dataset viewer schema", self.card)
        self.assertNotIn("**Not declared yet.**", self.card)
        self.assertIn("| `steps[].reflection` | optional |", self.card)
        self.assertIn("`lrd-r01-access-log-bearer-token`", self.card)
        self.assertIn("`lrd-r25-gha-step-summary-pat-artifact-handoff`", self.card)
        self.assertIn("`lrd-r2-json-jwt-nested-p2`", self.card)
        self.assertIn("issues/47", self.card)

    def test_disclosures_name_every_record_the_inferred_cast_trips_on(self):
        by_summary = {
            disclosure["summary"]: disclosure for disclosure in self.declaration["disclosures"]
        }
        thin = [
            disclosure for summary, disclosure in by_summary.items() if "thin `meta`" in summary
        ]
        lane = [
            disclosure for summary, disclosure in by_summary.items() if "`meta.lane`" in summary
        ]
        self.assertEqual((len(thin), len(lane)), (1, 1))
        self.assertEqual(len(thin[0]["ids"]), 36)
        self.assertEqual(len(set(thin[0]["ids"])), 36)
        self.assertEqual(len(lane[0]["ids"]), 8)
        self.assertEqual(len(set(lane[0]["ids"])), 8)
        self.assertFalse(set(thin[0]["ids"]) & set(lane[0]["ids"]))


if __name__ == "__main__":
    unittest.main()
