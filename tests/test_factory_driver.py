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
from unittest import mock

REPO = Path(__file__).resolve().parents[1]
DRIVER_PATH = REPO / ".claude" / "skills" / "run-synthetic-factory" / "driver.py"
SPEC = importlib.util.spec_from_file_location("factory_driver", DRIVER_PATH)
factory_driver = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(factory_driver)

from round_txn import TransactionError  # noqa: E402


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
        notes = factory / f"NOTES-r{round_number:02d}.md"
        batch.write_text(
            json.dumps(factory_driver.thalamic(f"batch-{round_number}")) + "\n"
        )
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
                        },
                        {
                            "name": notes.name,
                            "sha256": hashlib.sha256(notes.read_bytes()).hexdigest(),
                        },
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
                '{"version":1,"legacy_baseline":0,"commit_point":"ROUND-rNN.complete.json"}\n'
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

            (factory / "NOTES-r02.md").write_text("Novel coverage: 99%\n")
            with self.assertRaisesRegex(TransactionError, "hash mismatch"):
                factory_driver.factory_token_efficiency(factory)

    def test_lettered_notes_do_not_double_count_one_round(self):
        with tempfile.TemporaryDirectory() as td:
            factory = Path(td) / "marker-factory"
            factory.mkdir()
            (factory / ".round-marker-mode.json").write_text(
                '{"version":1,"legacy_baseline":0,"commit_point":"ROUND-rNN.complete.json"}\n'
            )
            self._write_notes(factory, [(1, 12.0), (2, 4.0)])
            self._write_complete_marker(factory, 1)
            self._write_complete_marker(factory, 2)
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

    def test_named_snapshot_refuses_symlinked_source_payloads(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            run = root / "run"
            run.mkdir()
            outside = root / "outside.jsonl"
            outside.write_text('{"id":"external"}\n')
            (run / "batch-r01.jsonl").symlink_to(outside)

            with self.assertRaisesRegex(TransactionError, "unsafe symlinked path"):
                factory_driver.cmd_snapshot(run, "safe")

            self.assertFalse((root / "run-safe").exists())


class FactoryDriverAudit(unittest.TestCase):
    def test_audit_refuses_a_symlinked_source_payload(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            run = root / "run"
            factory = run / "marker-factory"
            factory.mkdir(parents=True)
            outside = root / "outside.jsonl"
            outside.write_text('{"id":"external"}\n')
            (factory / "batch-r01.jsonl").symlink_to(outside)

            with self.assertRaisesRegex(TransactionError, "unsafe symlinked path"):
                factory_driver.cmd_audit(run)

    def test_audit_snapshot_excludes_uncommitted_marker_batches(self):
        with tempfile.TemporaryDirectory() as td:
            run = Path(td) / "run"
            factory = run / "marker-factory"
            factory.mkdir(parents=True)
            (factory / ".round-marker-mode.json").write_text(
                '{"version":1,"legacy_baseline":0,"commit_point":"ROUND-rNN.complete.json"}\n'
            )
            batch = factory / "batch-r01.jsonl"
            notes = factory / "NOTES-r01.md"
            batch.write_text(json.dumps(factory_driver.thalamic("committed")) + "\n")
            notes.write_text("Novel coverage: 80%\n")
            marker = factory / "ROUND-r01.complete.json"
            marker.write_text(
                json.dumps(
                    {
                        "factory": factory.name,
                        "round": 1,
                        "commit_point": marker.name,
                        "files": [
                            {"name": batch.name, "sha256": hashlib.sha256(batch.read_bytes()).hexdigest()},
                            {"name": notes.name, "sha256": hashlib.sha256(notes.read_bytes()).hexdigest()},
                        ],
                    }
                )
                + "\n"
            )
            (factory / "batch-r02.jsonl").write_text('{"id":"interrupted"}\n')
            nested = factory / "work"
            nested.mkdir()
            (nested / "batch-r03.jsonl").write_text('{"id":"nested-interrupted"}\n')
            seen = []

            def observe_snapshot(_script, snapshot, *_options):
                snap_factory = snapshot / factory.name
                seen.append(
                    {
                        path.relative_to(snap_factory).as_posix()
                        for path in snap_factory.rglob("*.jsonl")
                    }
                )
                return 0, "", ""

            with mock.patch.object(factory_driver, "run_tool", side_effect=observe_snapshot), redirect_stdout(
                StringIO()
            ):
                self.assertEqual(factory_driver.cmd_audit(run), 0)

        self.assertEqual(seen, [{"batch-r01.jsonl"}] * 3)


if __name__ == "__main__":
    unittest.main()
