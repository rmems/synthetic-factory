#!/usr/bin/env python3
"""Issue #58 leaf tests for the per-dataset card schema declaration."""

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


CSV_EXCEL_INGEST = "csv-excel-ingest-trajectories"


class CsvExcelIngestDeclarationTests(unittest.TestCase):
    """Issue #58: thin `meta` vs `designed` / `domain` / `stack` kills the cast.

    Every count asserted here was derived from the unmodified published mirror
    at ``~/rmems/hf/grok-4.6/csv-excel-ingest-trajectories`` (152 shards, two
    records each, 304 records, 5015 steps, 0 parse failures), not copied from
    the issue text.
    """

    def setUp(self):
        self.declaration = card_schema.load(CSV_EXCEL_INGEST)
        self.assertIsNotNone(self.declaration, "config/card-schemas is missing #58")
        self.item = {
            "slug": "csv-excel-ingest-factory",
            "hub": CSV_EXCEL_INGEST,
            "pretty": "Csv Excel Ingest Trajectories",
            "blurb": "CSV/Excel/sidecar leftover ingest repair episodes.",
            "tags": ["csv", "excel", "ingest"],
        }
        self.card = publisher.render_card(
            self.item,
            records=304,
            bytes_=2197062,
            first="r01",
            last="r152",
            payload_names=[f"batch-r{n:02d}.jsonl" for n in range(1, 153)],
        )

    def test_declaration_matches_the_observed_union_schema(self):
        names = {feature["name"]: feature for feature in self.declaration["features"]}
        self.assertEqual(
            set(names),
            {"id", "goal", "plan", "steps", "outcome", "reward", "meta"},
        )
        self.assertEqual(self.declaration["issues"], [58])
        self.assertEqual(self.declaration["data_files"], ["data/raw/batch-*.jsonl"])
        self.assertEqual(names["meta"]["dtype"], "json")
        self.assertEqual(names["reward"]["dtype"], "json")
        steps = {feature["name"]: feature for feature in names["steps"]["list"]}
        self.assertEqual(
            set(steps), {"n", "decision_basis", "tool_call", "observation", "reflection"}
        )
        self.assertTrue(steps["reflection"]["optional"])
        tool_call = {feature["name"]: feature for feature in steps["tool_call"]["struct"]}
        self.assertEqual(tool_call["args"]["dtype"], "json")

    def test_plan_is_mandatory_here_unlike_the_worked_example(self):
        """`plan` is on all 304 records; #36 marks the same field optional."""
        plan = next(
            feature
            for feature in self.declaration["features"]
            if feature["name"] == "plan"
        )
        self.assertEqual(plan["dtype"], "string")
        self.assertNotIn("optional", plan)
        self.assertIn("304", plan["note"])
        long_horizon = card_schema.load(LONG_HORIZON)
        sibling = next(
            feature for feature in long_horizon["features"] if feature["name"] == "plan"
        )
        self.assertTrue(sibling["optional"])

    def test_key_bag_columns_are_declared_json(self):
        self.assertEqual(
            card_schema.json_columns(self.declaration["features"]),
            ["steps[].tool_call.args", "reward", "meta"],
        )

    def test_card_front_matter_declares_the_default_config_over_raw_batches(self):
        front_matter = self.card.split("---", 2)[1]
        self.assertIn("configs:\n- config_name: default\n", front_matter)
        self.assertIn("  data_files:\n  - split: train\n", front_matter)
        self.assertIn('    path: "data/raw/batch-*.jsonl"\n', front_matter)
        self.assertIn("dataset_info:\n  features:\n", front_matter)
        self.assertIn("  - name: meta\n    dtype: json\n", front_matter)
        self.assertIn("  - name: reward\n    dtype: json\n", front_matter)
        self.assertIn("  - name: plan\n    dtype: string\n", front_matter)
        # license/tags/status claims stay exactly where they were.
        self.assertIn("license: apache-2.0", front_matter)
        self.assertIn("**not training-ready**", self.card)

    def test_card_only_annotations_stay_out_of_the_front_matter(self):
        front_matter = self.card.split("---", 2)[1]
        self.assertNotIn("optional:", front_matter)
        self.assertNotIn("note:", front_matter)
        self.assertNotIn("4870", front_matter)

    def test_card_body_discloses_the_two_dest_stamped_leftover_rows(self):
        self.assertIn("## Dataset viewer schema", self.card)
        self.assertNotIn("**Not declared yet.**", self.card)
        self.assertIn("`dbc-r64-bake-hcl-cache-from-leftover`", self.card)
        self.assertIn("`dbc-r64-bake-group-target-leftover`", self.card)
        # Attributed to the frozen leftover-mill census, not re-filed.
        self.assertIn("/issues/43", self.card)
        self.assertIn("/issues/44", self.card)

    def test_card_body_discloses_both_disjoint_eight_record_groups(self):
        self.assertIn("`cei-r01-csv-header-swap-amount-date`", self.card)
        self.assertIn("`cei-r08-csv-sci-notation-cents-8a11`", self.card)
        self.assertIn("`lane`", self.card)
        self.assertIn("does not overlap", self.card)

    def test_card_body_reports_the_derived_optional_counts(self):
        self.assertIn("| `steps[].reflection` | optional |", self.card)
        self.assertIn("4870 of 5015 steps", self.card)
        self.assertIn("| `plan` | present on every record |", self.card)
        self.assertIn("5015 steps publishes a public `decision_basis`", self.card)


if __name__ == "__main__":
    unittest.main()

