#!/usr/bin/env python3
"""Issue #60 leaf tests for the per-dataset card schema declaration."""

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


class DbMigrationRepairDeclarationTests(unittest.TestCase):
    """Issue #60: thin `meta` on four early records vs the plant/surface union.

    The counts asserted here are derived from the published mirror
    (`~/rmems/hf/grok-4.6/db-migration-repair-trajectories/data/raw`, 1363
    shards / 2726 records / 43630 steps), not copied from the issue text.
    """

    DATASET = "db-migration-repair-trajectories"

    def setUp(self):
        self.declaration = card_schema.load(self.DATASET)
        self.assertIsNotNone(self.declaration, "config/card-schemas is missing #60")
        self.item = {
            "slug": "db-migration-repair-factory",
            "hub": self.DATASET,
            "pretty": "Db Migration Repair Trajectories",
            "blurb": "Database migration leftover-object repair episodes.",
            "tags": ["synthetic-data", "trajectories", "database", "migrations"],
        }
        self.card = publisher.render_card(
            self.item,
            records=2726,
            bytes_=15978203,
            first="r01",
            last="r1363",
            payload_names=["batch-r01.jsonl", "batch-r02.jsonl", "batch-r1363.jsonl"],
        )

    def test_declaration_matches_the_observed_union_schema(self):
        names = {feature["name"]: feature for feature in self.declaration["features"]}
        self.assertEqual(
            list(names),
            ["id", "goal", "plan", "steps", "outcome", "reward", "meta"],
        )
        self.assertEqual(self.declaration["issues"], [60])
        self.assertEqual(names["meta"]["dtype"], "json")
        self.assertEqual(names["reward"]["dtype"], "json")
        steps = {feature["name"]: feature for feature in names["steps"]["list"]}
        self.assertEqual(
            set(steps), {"n", "decision_basis", "tool_call", "observation", "reflection"}
        )
        self.assertTrue(steps["reflection"]["optional"])
        self.assertIn("11 of 43630", steps["reflection"]["note"])
        tool_call = {feature["name"]: feature for feature in steps["tool_call"]["struct"]}
        self.assertEqual(tool_call["args"]["dtype"], "json")

    def test_plan_is_mandatory_here_unlike_the_long_horizon_dataset(self):
        # `plan` is on all 2726 records in this dataset. Copying the
        # long-horizon declaration's `optional: true` would publish a false
        # claim on the card's field table.
        plan = next(
            feature
            for feature in self.declaration["features"]
            if feature["name"] == "plan"
        )
        self.assertNotIn("optional", plan)
        self.assertNotIn("| `plan` | optional |", self.card)
        self.assertIn("| `plan` | present on every record |", self.card)

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
        self.assertIn("license: apache-2.0", front_matter)
        self.assertIn("**not training-ready**", self.card)
        # Card-only annotations must never reach the YAML.
        self.assertNotIn("optional", front_matter)
        self.assertNotIn("note:", front_matter)

    def test_card_body_discloses_the_four_thin_meta_records(self):
        self.assertIn("## Dataset viewer schema", self.card)
        self.assertNotIn("**Not declared yet.**", self.card)
        for record_id in (
            "dmr-r01-alembic-notnull-no-default",
            "dmr-r01-pg-invalid-concurrent-index",
            "dmr-r02-flyway-checksum-manual-sql",
            "dmr-r02-django-runpython-irreversible",
        ):
            with self.subTest(record_id=record_id):
                self.assertIn(f"`{record_id}`", self.card)
        self.assertIn("| `steps[].reflection` | optional |", self.card)

    def test_card_body_separates_the_own_leftover_mechanic_from_a_foreign_mill(self):
        self.assertIn("172 of 2726 record ids contain `leftover`", self.card)
        self.assertIn("advertised leftover-object mechanic", self.card)
        self.assertIn("no dest-stamped foreign payload", self.card)
        # The frozen censuses are cited for the class definition only.
        self.assertIn("issues/43", self.card)
        self.assertIn("issues/44", self.card)


if __name__ == "__main__":
    unittest.main()

