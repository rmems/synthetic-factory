#!/usr/bin/env python3
"""Issue #38 leaf tests for the per-dataset card schema declaration."""

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


CASCADING = "cascading-error-recovery-trajectories"


CASCADING_LEFTOVER_IDS = (
    "dbc-r2021-containerd-content-lease-l3",
    "dbc-r2021-containerd-gc-root-label-l3",
    "dbc-r2022-crio-imagestore-pin-l3",
    "dbc-r2022-crio-overlay-merged-l3",
    "dbc-r2023-buildx-driver-opt-network-l3",
    "dbc-r2023-buildx-provenance-attest-l3",
    "dbc-r2024-bake-group-legacy-target-l3",
    "dbc-r2024-bake-hcl-cache-from-l3",
)


class CascadingErrorRecoveryDeclarationTests(unittest.TestCase):
    """Issue #38: the fault-report fields carry two shapes, so the cast fails.

    The counts asserted here were derived by scanning every published record in
    the read-only mirror at
    ``~/rmems/hf/grok-4.6/cascading-error-recovery-trajectories`` (4722 records
    across 2361 shards, 0 parse failures), not transcribed from the issue.
    """

    def setUp(self):
        self.declaration = card_schema.load(CASCADING)
        self.assertIsNotNone(self.declaration, "config/card-schemas is missing #38")
        self.item = {
            "slug": "cascading-error-recovery-factory",
            "hub": CASCADING,
            "pretty": "Cascading Error Recovery Trajectories",
            "blurb": "Cascading-error diagnosis and recovery (fault@4, multi-hop).",
            "tags": ["synthetic-data", "debugging", "recovery", "errors"],
        }
        self.card = publisher.render_card(
            self.item,
            records=4722,
            bytes_=31062016,
            first="01",
            last="2361",
            payload_names=["batch-r01.jsonl", "batch-r2021.jsonl"],
        )

    def test_declaration_matches_the_observed_union_schema(self):
        features = self.declaration["features"]
        self.assertEqual(
            [feature["name"] for feature in features],
            [
                "id",
                "goal",
                "plan",
                "error_introduced",
                "propagation",
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
        # Absent on the 8 leftover-mill rows (error_introduced/diagnosis) or on
        # the 2158-record family that publishes only a string diagnosis.
        for name in ("plan", "error_introduced", "propagation", "diagnosis", "recovery", "verification"):
            with self.subTest(field=name):
                self.assertTrue(names[name]["optional"], f"{name} is not on every record")
        # String on the majority, object on the 182-record family: json is the
        # only encoding that survives both without an Arrow cast error.
        for name in ("propagation", "diagnosis", "recovery", "verification"):
            with self.subTest(field=name):
                self.assertEqual(names[name]["dtype"], "json")
        self.assertEqual(names["reward"]["dtype"], "json")
        self.assertEqual(names["meta"]["dtype"], "json")
        self.assertEqual(self.declaration["issues"], [38])

    def test_error_introduced_declares_both_payload_and_description(self):
        error_introduced = next(
            feature
            for feature in self.declaration["features"]
            if feature["name"] == "error_introduced"
        )
        children = {child["name"]: child for child in error_introduced["struct"]}
        self.assertEqual(set(children), {"step", "kind", "payload", "description"})
        self.assertEqual(children["step"]["dtype"], "int64")
        self.assertEqual(children["kind"]["dtype"], "string")
        # The viewer's TypeError was exactly this pair: struct<step, kind,
        # payload> could not cast to struct<step, kind, description>.
        self.assertTrue(children["payload"]["optional"])
        self.assertTrue(children["description"]["optional"])

    def test_steps_keep_the_public_decision_basis_and_a_json_arg_bag(self):
        steps = next(
            feature for feature in self.declaration["features"] if feature["name"] == "steps"
        )
        children = {child["name"]: child for child in steps["list"]}
        self.assertEqual(
            set(children), {"n", "decision_basis", "tool_call", "observation", "reflection"}
        )
        self.assertTrue(children["reflection"]["optional"])
        tool_call = {child["name"]: child for child in children["tool_call"]["struct"]}
        self.assertEqual(tool_call["args"]["dtype"], "json")

    def test_key_bag_and_variant_columns_are_declared_json(self):
        self.assertEqual(
            card_schema.json_columns(self.declaration["features"]),
            [
                "propagation",
                "diagnosis",
                "recovery",
                "verification",
                "steps[].tool_call.args",
                "reward",
                "meta",
            ],
        )

    def test_card_front_matter_declares_the_default_config_over_raw_batches(self):
        front_matter = self.card.split("---", 2)[1]
        self.assertIn("configs:\n- config_name: default\n", front_matter)
        self.assertIn('    path: "data/raw/batch-*.jsonl"\n', front_matter)
        self.assertIn("dataset_info:\n  features:\n", front_matter)
        self.assertIn("  - name: error_introduced\n    struct:\n", front_matter)
        self.assertIn("    - name: description\n      dtype: string\n", front_matter)
        self.assertIn("  - name: diagnosis\n    dtype: json\n", front_matter)
        # Card-only annotations must never be read back as a feature type.
        self.assertNotIn("optional", front_matter)
        # license/tags/status claims stay exactly where they were.
        self.assertIn("license: apache-2.0", front_matter)
        self.assertIn("**not training-ready**", self.card)

    def test_card_body_discloses_the_eight_leftover_mill_records(self):
        self.assertIn("## Dataset viewer schema", self.card)
        self.assertNotIn("**Not declared yet.**", self.card)
        self.assertIn("### Known payload disclosures", self.card)
        for record_id in CASCADING_LEFTOVER_IDS:
            with self.subTest(record_id=record_id):
                self.assertIn(f"`{record_id}`", self.card)
        self.assertIn("| `plan` | optional |", self.card)
        self.assertIn("| `error_introduced.description` | optional |", self.card)
        self.assertIn("| `steps[].reflection` | optional |", self.card)
        self.assertIn("issues/38", self.card)


if __name__ == "__main__":
    unittest.main()

