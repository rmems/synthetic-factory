#!/usr/bin/env python3
"""Seeded generation: byte-identical runs, the candidate-only summary, and request refusals.

Each test generates into a private catalog under a temporary directory;
the committed catalog pins are never read or edited.
"""

from __future__ import annotations

import dataclasses
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import tool_world_test_support as support
from tool_world_record_support import FACTORY, PACK, RunSandbox, read_candidates, refusal

# The support modules go first: they put pipelines/ on sys.path for the imports below.
# isort: split
from tool_world import generate, records
from tool_world import vocabulary as cv
from tool_world._contract import load_strict_json, sha256_bytes
from tool_world.policies import scripted

ROW_KEYS = frozenset(
    {"id", "task_id", "factory", "variant", "steps", "success", "decision", "faults_fired"}
)


class GenerateRun(unittest.TestCase):
    def setUp(self):
        self.box = RunSandbox(self)
        self.root = self.box.root
        self.catalog_dir = self.box.catalog_dir
        self.catalog = self.box.catalog

    def test_two_runs_with_one_seed_are_byte_identical(self):
        first = generate.run(self.box.request(out_dir=self.root / "a"))
        second = generate.run(self.box.request(out_dir=self.root / "b"))
        self.assertEqual(first, second)
        for name in (generate.CANDIDATES_FILENAME, generate.RUN_FILENAME, generate.NOTES_FILENAME):
            with self.subTest(file=name):
                self.assertEqual(
                    (self.root / "a" / name).read_bytes(), (self.root / "b" / name).read_bytes()
                )
        self.assertIn(
            "Run seed 1", (self.root / "a" / generate.NOTES_FILENAME).read_text(encoding="utf-8")
        )

    def test_the_summary_describes_a_candidate_only_run(self):
        summary = generate.run(self.box.request())
        candidates = (self.root / "run" / generate.CANDIDATES_FILENAME).read_bytes()
        self.assertEqual(
            (
                summary["format"],
                summary["family"],
                summary["generator"],
                summary["generator_version"],
            ),
            (cv.RUN_FORMAT, cv.FAMILY, cv.GENERATOR_NAME, cv.GENERATOR_VERSION),
        )
        self.assertEqual(summary["run_id"], f"twd-run-1-{self.catalog.catalog_sha256[:12]}")
        self.assertEqual(summary["catalog_sha256"], self.catalog.catalog_sha256)
        self.assertEqual(summary["policy_sha256"], scripted.policy_sha256())
        self.assertEqual((summary["seed"], summary["count"], summary["factory"]), (1, 2, FACTORY))
        self.assertEqual(summary["produced_at"], support.PRODUCED_AT)
        self.assertEqual(summary["records"], len(summary["rows"]))
        self.assertEqual(summary["records"], summary["accepted"] + summary["measured"])
        self.assertEqual(summary["candidates_sha256"], sha256_bytes(candidates))
        self.assertTrue(summary["candidate_only"])
        self.assertFalse(summary["self_certified_training_ready"])
        run_file = self.root / "run" / generate.RUN_FILENAME
        self.assertEqual(load_strict_json(run_file.read_text(encoding="utf-8")), summary)
        for row in summary["rows"]:
            self.assertEqual(set(row), ROW_KEYS)

    def test_gold_only_runs_accept_every_record(self):
        summary = generate.run(self.box.request(variants="gold", count=3))
        self.assertEqual(summary["records"], 3)
        for row in summary["rows"]:
            with self.subTest(task=row["task_id"]):
                self.assertEqual(
                    (row["variant"], row["decision"], row["success"]), ("gold", "accept", True)
                )
        for record in read_candidates(self.root / "run"):
            self.assertEqual(record["training_view"]["meta"]["variant"], "gold")

    def test_the_header_redraws_the_inventory(self):
        summary = generate.run(self.box.request())
        named = [row["id"] for row in summary["rows"]]
        self.assertEqual(generate.expected_ids(self.box.catalog, summary), named)
        with refusal(self, cv.FINDING_COUNT_OUT_OF_DOMAIN, "count must be an integer"):
            generate.expected_ids(self.box.catalog, {**summary, "count": "2"})
        with refusal(self, cv.FINDING_SEED_INVALID, "seed must be an integer"):
            generate.expected_ids(self.box.catalog, {**summary, "seed": None})
        with refusal(self, cv.FINDING_RUN_FILE_INVALID, "policy_sha256 must be a string"):
            generate.expected_ids(self.box.catalog, {**summary, "policy_sha256": None})

    def test_one_record_is_reproducible_without_the_batch(self):
        summary = generate.run(self.box.request())
        first = read_candidates(self.root / "run")[0]
        row = summary["rows"][0]
        pack = self.catalog.pack(PACK)
        draw = generate.Draw(pack, pack.task(row["task_id"]), row["variant"], 1)
        self.assertEqual(first["environment"]["seed"], draw.seed(1))
        run = records.RunContext(
            self.catalog.catalog_sha256, summary["run_id"], summary["policy_sha256"]
        )
        self.assertEqual(generate.generate_record(draw, 1, run), first)
        self.assertNotEqual(draw.seed(1), dataclasses.replace(draw, index=2).seed(1))
        self.assertNotEqual(draw.seed(1), draw.seed(2))

    def test_request_refusals(self):
        cases = (
            ({"seed": "7"}, cv.FINDING_SEED_INVALID),
            ({"seed": True}, cv.FINDING_SEED_INVALID),
            ({"seed": -1}, cv.FINDING_SEED_INVALID),
            ({"count": 0}, cv.FINDING_COUNT_OUT_OF_DOMAIN),
            ({"count": cv.MAX_COUNT + 1}, cv.FINDING_COUNT_OUT_OF_DOMAIN),
            ({"count": cv.MAX_COUNT}, cv.FINDING_COUNT_OUT_OF_DOMAIN),
            ({"variants": "some"}, cv.FINDING_COUNT_OUT_OF_DOMAIN),
            ({"factory": "tool-world-shell-factory"}, cv.FINDING_SURFACE_UNKNOWN),
            ({"produced_at": "yesterday"}, cv.FINDING_PRODUCED_AT_NOT_A_TIMESTAMP),
        )
        for overrides, code in cases:
            with self.subTest(overrides=overrides), refusal(self, code):
                generate.run(self.box.request(**overrides))
        self.assertFalse((self.root / "run").exists())

    def test_destinations_that_exist_or_alias_the_raw_tree_are_refused(self):
        (self.root / "run").mkdir()
        with refusal(self, cv.FINDING_DESTINATION_EXISTS, "already exists"):
            generate.run(self.box.request())
        raw = self.root / "outputs" / "raw" / "run"
        with refusal(self, cv.FINDING_DESTINATION_UNDER_RAW, "raw tree"):
            generate.run(self.box.request(out_dir=raw))
        self.assertFalse(raw.exists())


if __name__ == "__main__":
    unittest.main()
