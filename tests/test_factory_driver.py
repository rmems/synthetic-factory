#!/usr/bin/env python3
"""Regression tests for the operator driver's byte-tolerant census paths."""

import importlib.util
import hashlib
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DRIVER_PATH = REPO / ".claude" / "skills" / "run-synthetic-factory" / "driver.py"
SPEC = importlib.util.spec_from_file_location("factory_driver", DRIVER_PATH)
factory_driver = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(factory_driver)


class FactoryTokenEfficiency(unittest.TestCase):
    def _write_notes(self, factory, rounds):
        for rn, coverage in rounds:
            text = (
                f"Novel coverage: {coverage}%\n"
                if coverage is not None
                else "Self-critique without a coverage line.\n"
            )
            (factory / f"NOTES-r{rn:02d}.md").write_text(text)

    def _write_complete_marker(self, factory, round_number):
        batch = factory / f"batch-r{round_number:02d}.jsonl"
        batch.write_text(f'{{"id":"batch-{round_number}"}}\n')
        marker = factory / f"ROUND-r{round_number:02d}.complete.json"
        marker.write_text(
            json.dumps(
                {
                    "factory": factory.name,
                    "round": round_number,
                    "commit_point": marker.name,
                    "files": [
                        {
                            "name": batch.name,
                            "sha256": hashlib.sha256(batch.read_bytes()).hexdigest(),
                        }
                    ],
                }
            )
            + "\n"
        )

    def test_early_stop_clears_after_later_healthy_notes(self):
        with tempfile.TemporaryDirectory() as td:
            factory = Path(td) / "recovered-factory"
            factory.mkdir()
            self._write_notes(factory, [(1, 4.0), (2, 3.0), (3, 12.0)])
            info = factory_driver.factory_token_efficiency(factory)
            self.assertFalse(info["early_stop"])
            self.assertIsNone(info["early_stop_at_round"])

    def test_early_stop_holds_when_trailing_streak_is_still_low(self):
        with tempfile.TemporaryDirectory() as td:
            factory = Path(td) / "plateau-factory"
            factory.mkdir()
            self._write_notes(factory, [(1, 12.0), (2, 4.0), (3, 3.0)])
            info = factory_driver.factory_token_efficiency(factory)
            self.assertTrue(info["early_stop"])
            self.assertEqual(info["early_stop_at_round"], 3)

    def test_unparseable_notes_hold_but_do_not_latch_past_recovery(self):
        with tempfile.TemporaryDirectory() as td:
            factory = Path(td) / "held-then-recovered"
            factory.mkdir()
            self._write_notes(factory, [(1, 4.0), (2, 3.0), (3, None), (4, 18.0)])
            info = factory_driver.factory_token_efficiency(factory)
            self.assertFalse(info["early_stop"])
            self.assertIsNone(info["early_stop_at_round"])

    def test_unparseable_notes_hold_a_trailing_streak(self):
        with tempfile.TemporaryDirectory() as td:
            factory = Path(td) / "held-plateau"
            factory.mkdir()
            self._write_notes(factory, [(1, 4.0), (2, 3.0), (3, None)])
            info = factory_driver.factory_token_efficiency(factory)
            self.assertTrue(info["early_stop"])
            self.assertEqual(info["early_stop_at_round"], 2)

    def test_marker_mode_ignores_uncommitted_notes(self):
        with tempfile.TemporaryDirectory() as td:
            factory = Path(td) / "marker-factory"
            factory.mkdir()
            (factory / ".round-marker-mode.json").write_text(
                '{"version":1,"legacy_baseline":0}\n'
            )
            self._write_notes(factory, [(1, 4.0), (2, 3.0)])

            info = factory_driver.factory_token_efficiency(factory)
            self.assertEqual(info["rounds"], [])
            self.assertFalse(info["early_stop"])

            self._write_complete_marker(factory, 1)
            self._write_complete_marker(factory, 2)
            info = factory_driver.factory_token_efficiency(factory)
            self.assertTrue(info["early_stop"])
            self.assertEqual(info["early_stop_at_round"], 2)

    def test_lettered_notes_do_not_double_count_one_round(self):
        with tempfile.TemporaryDirectory() as td:
            factory = Path(td) / "marker-factory"
            factory.mkdir()
            (factory / ".round-marker-mode.json").write_text(
                '{"version":1,"legacy_baseline":2}\n'
            )
            self._write_notes(factory, [(1, 12.0), (2, 4.0)])
            (factory / "NOTES-r02b.md").write_text("Novel coverage: 3%\n")

            info = factory_driver.factory_token_efficiency(factory)

        self.assertFalse(info["early_stop"])
        self.assertEqual(
            [(item["round"], item["file"]) for item in info["rounds"]],
            [(1, "NOTES-r01.md"), (2, "NOTES-r02.md")],
        )


class FactoryDriverBytes(unittest.TestCase):
    def test_count_records_tolerates_invalid_utf8(self):
        with tempfile.TemporaryDirectory() as td:
            factory = Path(td) / "factory"
            factory.mkdir()
            (factory / "bad-bytes.jsonl").write_bytes(b"{}\xff\n\n{}\n")
            self.assertEqual(factory_driver.count_records(factory), 2)

    def test_snapshot_tolerates_invalid_utf8(self):
        with tempfile.TemporaryDirectory() as td:
            run = Path(td) / "run"
            run.mkdir()
            (run / "bad-bytes.jsonl").write_bytes(b"{}\xff\n")
            with redirect_stdout(StringIO()):
                factory_driver.cmd_snapshot(run, "bytes")
            self.assertEqual((Path(td) / "run-bytes" / "bad-bytes.jsonl").read_bytes(), b"{}\xff\n")


if __name__ == "__main__":
    unittest.main()
