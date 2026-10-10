#!/usr/bin/env python3
"""The committed tool-world fixture run is byte-reproduced by the current generator.

Regenerate it after an intentional generator or pack change:

    rm -rf tests/fixtures/tool-world-run
    python3 pipelines/tool_world_cli.py generate --seed 20261009 --count 12 \
        --out tests/fixtures/tool-world-run --produced-at 2026-10-09T00:00:00Z

The run pins the policy source digest and every pack digest, so any drift in
either shows up here before it shows up in a published round.
"""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import tool_world_test_support as support  # noqa: E402
from tool_world import generate, replay  # noqa: E402

catalog_mod = support.catalog_mod
FIXTURE = support.REPO / "tests" / "fixtures" / "tool-world-run"
FILES = (generate.CANDIDATES_FILENAME, generate.RUN_FILENAME, generate.NOTES_FILENAME)


class FixtureRun(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="tool-world-fixture-"))
        self.addCleanup(shutil.rmtree, self.root, True)
        self.summary = json.loads((FIXTURE / generate.RUN_FILENAME).read_text(encoding="utf-8"))

    def test_fixture_is_byte_reproduced_by_the_current_generator(self):
        out = self.root / "regenerated"
        generate.run(
            generate.RunRequest(
                catalog_dir=None,
                out_dir=out,
                seed=self.summary["seed"],
                count=self.summary["count"],
                factory=self.summary["factory"],
                variants=self.summary["variants"],
                produced_at=self.summary["produced_at"],
            )
        )
        for name in FILES:
            with self.subTest(file=name):
                self.assertEqual((out / name).read_bytes(), (FIXTURE / name).read_bytes())

    def test_fixture_replays_against_the_committed_catalog(self):
        result = replay.replay_run(FIXTURE, catalog_mod.load_catalog())
        self.assertTrue(
            result["passed"], [row for row in result["results"] if not row["agreement"]]
        )
        self.assertEqual(result["records"], self.summary["records"])

    def test_fixture_covers_every_factory_and_every_pack(self):
        rows = self.summary["rows"]
        catalog = catalog_mod.load_catalog()
        expected = {task.factory for _pack, task in catalog.tasks()}
        self.assertEqual({row["factory"] for row in rows}, expected)
        self.assertGreater(self.summary["accepted"], 0)
        self.assertGreater(self.summary["measured"], 0)


if __name__ == "__main__":
    unittest.main()
