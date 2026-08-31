#!/usr/bin/env python3
"""Issue #63 leaf tests for the per-dataset card schema declaration.

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


FEATURE_FLAG_DEBUG = "feature-flag-debug-trajectories"


class FeatureFlagDebugDeclarationTests(unittest.TestCase):
    """Issue #63: thin `meta` vs the designed/plant shapes that widen it."""

    def setUp(self):
        self.declaration = card_schema.load(FEATURE_FLAG_DEBUG)
        self.assertIsNotNone(self.declaration, "config/card-schemas is missing #63")
        self.item = {
            "slug": "feature-flag-debug-factory",
            "hub": FEATURE_FLAG_DEBUG,
            "pretty": "Feature Flag Debug Trajectories",
            "blurb": "Feature-flag leftover assignment/override debug episodes.",
            "tags": ["synthetic-data", "trajectories", "feature-flags"],
        }
        self.card = publisher.render_card(
            self.item,
            records=220,
            bytes_=1523718,
            first="r01",
            last="r110",
            payload_names=[f"batch-r{n:02d}.jsonl" for n in range(1, 111)],
        )

    def test_declaration_matches_the_observed_union_schema(self):
        names = {feature["name"]: feature for feature in self.declaration["features"]}
        self.assertEqual(
            set(names),
            {"id", "goal", "plan", "steps", "outcome", "reward", "meta"},
        )
        # `plan` is a string on all 220 records here, unlike the #36 dataset.
        self.assertNotIn("optional", names["plan"])
        self.assertEqual(names["plan"]["dtype"], "string")
        self.assertEqual(names["meta"]["dtype"], "json")
        self.assertEqual(names["reward"]["dtype"], "json")
        steps = {feature["name"]: feature for feature in names["steps"]["list"]}
        self.assertEqual(
            set(steps), {"n", "decision_basis", "tool_call", "observation", "reflection"}
        )
        self.assertTrue(steps["reflection"]["optional"])
        for required in ("n", "decision_basis", "tool_call", "observation"):
            self.assertNotIn("optional", steps[required])
        tool_call = {feature["name"]: feature for feature in steps["tool_call"]["struct"]}
        self.assertEqual(set(tool_call), {"name", "args"})
        self.assertEqual(tool_call["args"]["dtype"], "json")
        self.assertEqual(self.declaration["issues"], [63])

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
        # Card-only annotations must never reach the YAML.
        self.assertNotIn("optional", front_matter)
        # license/tags/status claims stay exactly where they were.
        self.assertIn("license: apache-2.0", front_matter)
        self.assertIn("**not training-ready**", self.card)

    def test_card_body_owns_the_leftover_mechanic_and_the_optional_reflection(self):
        self.assertIn("## Dataset viewer schema", self.card)
        self.assertNotIn("**Not declared yet.**", self.card)
        self.assertIn("| `steps[].reflection` | optional |", self.card)
        self.assertIn("| `plan` | present on every record |", self.card)
        # The leftover names are this factory's own mechanic, not a foreign mill.
        self.assertIn("advertised leftover assignment/override mechanic", self.card)
        self.assertIn("no dest-stamped foreign payload", self.card)
        self.assertIn("`decision_basis`", self.card)

    def test_declared_globs_cover_every_published_shard(self):
        payload_names = [f"batch-r{n:02d}.jsonl" for n in range(1, 111)]
        self.assertEqual(
            card_schema.payload_coverage_errors(self.declaration, payload_names), []
        )
        # A shard the glob cannot reach is a hard error, not a silent drop.
        self.assertTrue(
            card_schema.payload_coverage_errors(
                self.declaration, payload_names + ["extra.jsonl"]
            )
        )


if __name__ == "__main__":
    unittest.main()

