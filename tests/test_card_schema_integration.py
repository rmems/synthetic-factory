#!/usr/bin/env python3
"""Integration tests spanning card_schema and the publisher.

Covers the publisher's consumption of declarations end to end (``cmd_schemas``,
``render_card``, ``card_schema_audit``) plus the first concrete dataset that
uses the mechanism: `long-horizon-coding-trajectories` (issue #36).
"""

import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "pipelines"))
sys.path.insert(0, str(REPO / "scripts"))

import card_schema  # noqa: E402
import publish_grok46_hub as publisher  # noqa: E402

LONG_HORIZON = "long-horizon-coding-trajectories"

MINIMAL = {
    "version": 1,
    "dataset": "example-trajectories",
    "note": "Declared because raw meta shapes vary.",
    "features": [
        {"name": "id", "dtype": "string"},
        {"name": "meta", "dtype": "json"},
    ],
}


def write_declaration(root: Path, dataset: str, payload: dict) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    path = root / f"{dataset}.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


class PublisherIntegrationTests(unittest.TestCase):
    """The publisher must consume declarations, and must never skip one silently."""

    def test_every_declaration_on_disk_is_valid_and_names_a_real_dataset(self):
        declared, _undeclared, orphaned = publisher.card_schema_audit()
        self.assertEqual(orphaned, [], "declaration files that name no known dataset")
        known = set(publisher.known_hub_names())
        for name in declared:
            with self.subTest(dataset=name):
                declaration = publisher.card_declaration(name)
                self.assertIsNotNone(declaration)
                self.assertIn(name, known)

    def test_schemas_command_is_loud_about_orphans_and_gaps(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "card-schemas"
            write_declaration(root, "not-a-real-dataset", {**MINIMAL, "dataset": "x"})
            report = io.StringIO()
            errors = io.StringIO()
            with mock.patch.object(card_schema, "SCHEMA_ROOT", root), redirect_stdout(
                report
            ), redirect_stderr(errors):
                orphan_code = publisher.cmd_schemas()
                root.joinpath("not-a-real-dataset.json").unlink()
                clean_code = publisher.cmd_schemas()
                strict_code = publisher.cmd_schemas(strict=True)
            self.assertEqual((orphan_code, clean_code, strict_code), (2, 0, 1))
            self.assertIn("names no known dataset", errors.getvalue())
            self.assertIn("UNDECLARED  long-horizon-coding-trajectories", report.getvalue())

    def test_schemas_command_rejects_an_unrenderable_declaration(self):
        cases = (
            ("config_name", {"config_name": "bad---name"}),
            ("split", {"split": "bad---name"}),
            ("body_utf8", {"note": "bad\ud800note"}),
        )
        for case, overrides in cases:
            with self.subTest(case=case), tempfile.TemporaryDirectory() as td:
                root = Path(td) / "card-schemas"
                payload = {**MINIMAL, "dataset": LONG_HORIZON}
                payload.update(overrides)
                write_declaration(root, LONG_HORIZON, payload)
                with mock.patch.object(card_schema, "SCHEMA_ROOT", root):
                    with self.assertRaisesRegex(
                        SystemExit, "cannot render card schema"
                    ):
                        publisher.cmd_schemas()

    def test_a_broken_declaration_fails_the_card_instead_of_degrading_it(self):
        item = {
            "slug": "long-horizon-coding-factory",
            "hub": LONG_HORIZON,
            "pretty": "Long Horizon Coding Trajectories",
            "blurb": "Test factory.",
            "tags": ["synthetic-data"],
        }
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "card-schemas"
            write_declaration(root, LONG_HORIZON, {**MINIMAL, "dataset": LONG_HORIZON, "note": ""})
            with mock.patch.object(card_schema, "SCHEMA_ROOT", root):
                with self.assertRaisesRegex(SystemExit, "non-empty 'note'"):
                    publisher.render_card(
                        item,
                        records=2,
                        bytes_=10,
                        first="r01",
                        last="r02",
                        payload_names=["batch-r01.jsonl"],
                    )

    def test_render_card_refuses_a_declaration_that_misses_a_payload(self):
        item = {
            "slug": "long-horizon-coding-factory",
            "hub": LONG_HORIZON,
            "pretty": "Long Horizon Coding Trajectories",
            "blurb": "Test factory.",
            "tags": ["synthetic-data"],
        }
        with self.assertRaisesRegex(SystemExit, "does not cover the published payload"):
            publisher.render_card(
                item,
                records=2,
                bytes_=10,
                first=None,
                last=None,
                payload_names=["episodes.jsonl"],
            )

    def test_an_undeclared_dataset_card_carries_the_visible_placeholder(self):
        # Use a name that no published dataset owns so adding a declaration for
        # a real dataset cannot accidentally turn this fallback test green.
        item = {
            "slug": "still-undeclared-factory",
            "hub": "still-undeclared-trajectories",
            "pretty": "Still Undeclared Trajectories",
            "blurb": "Test factory.",
            "tags": ["synthetic-data"],
        }
        self.assertIsNone(card_schema.load(item["hub"]))
        card = publisher.render_card(
            item,
            records=2,
            bytes_=10,
            first="r01",
            last="r02",
            payload_names=["batch-r01.jsonl"],
        )
        front_matter = card.split("---", 2)[1]
        self.assertNotIn("configs:", front_matter)
        self.assertNotIn("dataset_info:", front_matter)
        self.assertIn("**Not declared yet.**", card)


class LongHorizonCodingDeclarationTests(unittest.TestCase):
    """Issue #36: the first dataset to use the mechanism end to end."""

    def setUp(self):
        self.declaration = card_schema.load(LONG_HORIZON)
        self.assertIsNotNone(self.declaration, "config/card-schemas is missing #36")
        self.item = {
            "slug": "long-horizon-coding-factory",
            "hub": LONG_HORIZON,
            "pretty": "Long Horizon Coding Trajectories",
            "blurb": "Long-horizon coding-agent leftover-bug episodes.",
            "tags": ["synthetic-data", "trajectories"],
        }
        self.card = publisher.render_card(
            self.item,
            records=9970,
            bytes_=94602148,
            first="r01",
            last="r4985",
            payload_names=["batch-r01.jsonl", "batch-r02.jsonl"],
        )

    def test_declaration_matches_the_observed_union_schema(self):
        names = {feature["name"]: feature for feature in self.declaration["features"]}
        self.assertEqual(
            set(names),
            {"id", "goal", "plan", "steps", "outcome", "reward", "meta"},
        )
        self.assertTrue(names["plan"]["optional"])
        self.assertEqual(names["meta"]["dtype"], "json")
        self.assertEqual(names["reward"]["dtype"], "json")
        steps = {feature["name"]: feature for feature in names["steps"]["list"]}
        self.assertEqual(
            set(steps), {"n", "decision_basis", "tool_call", "observation", "reflection"}
        )
        self.assertTrue(steps["reflection"]["optional"])
        tool_call = {feature["name"]: feature for feature in steps["tool_call"]["struct"]}
        self.assertEqual(tool_call["args"]["dtype"], "json")
        self.assertEqual(self.declaration["issues"], [36])

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
        # license/tags/status claims stay exactly where they were.
        self.assertIn("license: apache-2.0", front_matter)
        self.assertIn("**not training-ready**", self.card)

    def test_card_body_discloses_the_two_tagged_records(self):
        self.assertIn("## Dataset viewer schema", self.card)
        self.assertIn("`lhc-r02-lockfile-pin-c4e1`", self.card)
        self.assertIn("`lhc-r02-race-cache-9aa0`", self.card)
        self.assertIn("| `plan` | optional |", self.card)
        self.assertIn("| `steps[].reflection` | optional |", self.card)
        self.assertNotIn("**Not declared yet.**", self.card)


if __name__ == "__main__":
    unittest.main()
