#!/usr/bin/env python3
"""Issue #59 leaf tests for the per-dataset card schema declaration.

Self-contained on the public ``card_schema`` / ``publish_grok46_hub``
surface so this module imports identically before and after the shared
``tests/test_card_schema.py`` module is split.
"""

import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "pipelines"))
sys.path.insert(0, str(REPO / "scripts"))

import card_schema  # noqa: E402
import publish_grok46_hub as publisher  # noqa: E402

LONG_HORIZON = "long-horizon-coding-trajectories"


DATA_PIPELINE_REPAIR = "data-pipeline-repair-trajectories"


class DataPipelineRepairDeclarationTests(unittest.TestCase):
    """Issue #59: evolving `meta` plus a 1074-key `reward` bag.

    Every count asserted here was derived from the read-only mirror at
    ~/rmems/hf/grok-4.6/data-pipeline-repair-trajectories (3056 shards,
    6112 records, 101200 steps, 0 parse failures).
    """

    def setUp(self):
        self.declaration = card_schema.load(DATA_PIPELINE_REPAIR)
        self.assertIsNotNone(self.declaration, "config/card-schemas is missing #59")
        self.item = {
            "slug": "data-pipeline-repair-factory",
            "hub": DATA_PIPELINE_REPAIR,
            "pretty": "Data Pipeline Repair Trajectories",
            "blurb": "Schema-drift and late-data pipeline repair episodes.",
            "tags": ["synthetic-data", "trajectories", "data-pipeline", "etl"],
        }
        self.card = publisher.render_card(
            self.item,
            records=6112,
            bytes_=58979846,
            first="r01",
            last="r3056",
            payload_names=[
                "batch-r01.jsonl",
                "batch-r2623.jsonl",
                "batch-r3056.jsonl",
            ],
        )

    def test_declaration_matches_the_observed_union_schema(self):
        names = {feature["name"]: feature for feature in self.declaration["features"]}
        self.assertEqual(
            set(names),
            {"goal", "plan", "steps", "outcome", "reward", "id", "meta"},
        )
        self.assertEqual(names["meta"]["dtype"], "json")
        self.assertEqual(names["reward"]["dtype"], "json")
        steps = {feature["name"]: feature for feature in names["steps"]["list"]}
        self.assertEqual(
            set(steps), {"n", "decision_basis", "tool_call", "observation", "reflection"}
        )
        self.assertEqual(steps["n"]["dtype"], "int64")
        self.assertTrue(steps["reflection"]["optional"])
        tool_call = {feature["name"]: feature for feature in steps["tool_call"]["struct"]}
        self.assertEqual(set(tool_call), {"name", "args"})
        self.assertEqual(tool_call["args"]["dtype"], "json")
        self.assertEqual(self.declaration["issues"], [59])
        self.assertEqual(self.declaration["data_files"], ["data/raw/batch-*.jsonl"])

    def test_plan_is_mandatory_here_unlike_the_worked_example(self):
        """`plan` is on 6112 of 6112 records; optionality is never copied."""
        plan = next(
            feature
            for feature in self.declaration["features"]
            if feature["name"] == "plan"
        )
        self.assertFalse(plan.get("optional", False))
        self.assertEqual(plan["dtype"], "string")
        sibling = card_schema.load(LONG_HORIZON)
        sibling_plan = next(
            feature for feature in sibling["features"] if feature["name"] == "plan"
        )
        self.assertTrue(sibling_plan["optional"])
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
        self.assertIn("      - name: args\n        dtype: json\n", front_matter)
        self.assertIn("license: apache-2.0", front_matter)
        self.assertIn("**not training-ready**", self.card)

    def test_card_body_discloses_the_sixteen_dest_stamped_leftovers(self):
        leftovers = next(
            disclosure
            for disclosure in self.declaration["disclosures"]
            if disclosure["ids"]
        )
        self.assertEqual(len(leftovers["ids"]), 16)
        self.assertEqual(leftovers["issues"], [43, 44])
        self.assertTrue(
            all(record_id.startswith("dbc-r26") for record_id in leftovers["ids"])
        )
        self.assertIn("## Dataset viewer schema", self.card)
        self.assertIn("`dbc-r2623-nydus-rafs-blobcache-digest-leftover`", self.card)
        self.assertIn("`dbc-r2630-kaniko-snapshotmode-redo-leftover`", self.card)
        self.assertIn("| `steps[].reflection` | optional |", self.card)
        self.assertNotIn("**Not declared yet.**", self.card)

    def test_the_factory_own_leftover_mechanic_is_not_reported_as_foreign(self):
        """The advertised `leftover` repair mechanic is native, not a mill mix."""
        sentences = [
            disclosure["summary"] for disclosure in self.declaration["disclosures"]
        ]
        native = next(text for text in sentences if "6096" in text)
        self.assertIn("meta.kind=episode", native)
        self.assertIn("own advertised repair mechanic", native)
        self.assertIn("6096 records are `data-pipeline-repair-factory`", self.card)


if __name__ == "__main__":
    unittest.main()

