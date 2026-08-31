#!/usr/bin/env python3
"""Regression tests for token-efficiency latch and convergence fixture."""

import hashlib
import importlib.util
import json
import tempfile
import unittest
from io import StringIO
from pathlib import Path
from contextlib import redirect_stdout

REPO = Path(__file__).resolve().parents[1]
DRIVER_PATH = REPO / ".claude" / "skills" / "run-synthetic-factory" / "driver.py"
SPEC = importlib.util.spec_from_file_location("factory_driver", DRIVER_PATH)
factory_driver = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(factory_driver)

from round_txn import TransactionError  # noqa: E402

FIXTURES = REPO / "tests" / "fixtures"


class TokenEfficiencyFixtureLatch(unittest.TestCase):
    """The committed convergence fixture must drive the documented latch.

    docs/token-efficiency.md promises that two consecutive NOTES under 5%
    early-stop a lane and that a healthy round clears the streak.  These run
    the real `driver.py token-efficiency --json` surface over committed NOTES
    rather than a tempdir, so the shipped fixture stays a working example of
    the prompt contract.
    """

    @classmethod
    def setUpClass(cls):
        run_dir = FIXTURES / "token-efficiency"
        cls.frontiers = {
            factory.name: factory_driver.frontier_status(factory)
            for factory in sorted(path for path in run_dir.iterdir() if path.is_dir())
        }
        buffer = StringIO()
        with redirect_stdout(buffer):
            cls.payload = factory_driver.cmd_token_efficiency(run_dir, as_json=True)
        cls.printed = json.loads(buffer.getvalue())
        cls.by_factory = {
            item["factory"]: item for item in cls.payload["token_efficiency"]
        }

    def test_json_output_matches_the_returned_payload(self):
        self.assertEqual(self.printed, json.loads(json.dumps(self.payload)))

    def test_fixture_rounds_are_hash_bound_marker_mode_commits(self):
        for factory, status in self.frontiers.items():
            with self.subTest(factory=factory):
                self.assertEqual(status["mode"], "marker")
                self.assertEqual(status["completed_markers"], [1, 2])
                self.assertEqual(status["highest_flushed"], 2)
                self.assertEqual(status["next_round"], 3)

    def test_two_consecutive_sub_threshold_notes_fire_early_stop(self):
        info = self.by_factory["thalamic-trajectory-factory"]
        self.assertEqual(
            [(item["round"], item["novel_coverage_pct"]) for item in info["rounds"]],
            [(1, 4.2), (2, 3.1)],
        )
        self.assertTrue(all(item["is_low"] for item in info["rounds"]))
        self.assertTrue(info["early_stop"])
        self.assertEqual(info["early_stop_at_round"], 2)
        self.assertEqual(info["threshold_pct"], 5.0)
        self.assertEqual(info["consecutive_required"], 2)
        self.assertEqual(info["saving_mode_pct"], 40)

    def test_a_healthy_round_clears_a_single_low_round(self):
        info = self.by_factory["agentic-coding-trajectory-factory"]
        self.assertEqual(
            [(item["round"], item["novel_coverage_pct"]) for item in info["rounds"]],
            [(1, 4.8), (2, 12.0)],
        )
        self.assertFalse(info["early_stop"])
        self.assertIsNone(info["early_stop_at_round"])

    def test_human_output_names_the_early_stop_round(self):
        buffer = StringIO()
        with redirect_stdout(buffer):
            factory_driver.cmd_token_efficiency(FIXTURES / "token-efficiency")
        report = buffer.getvalue()
        self.assertIn("thalamic-trajectory-factory: EARLY-STOP at r02", report)
        self.assertIn("agentic-coding-trajectory-factory: no early-stop", report)


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
                    "version": 1,
                    "factory": factory.name,
                    "round": round_number,
                    "records": 1,
                    "expected_records": 1,
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

    def test_historical_notes_keep_the_first_valid_coverage_claim(self):
        for notes, expected in (
            ("Novel coverage: 4%\nNovel coverage: 4%\n", 4.0),
            ("Novel coverage: 4%\nNovel coverage: 80%\n", 4.0),
            ("Novel coverage: malformed\nNovel coverage: 80%\n", 80.0),
            ("Novel coverage: 4% Novel coverage: 80%\n", 4.0),
            ("Novel coverage: 4% trailing prose\n", 4.0),
        ):
            with self.subTest(notes=notes):
                self.assertEqual(factory_driver.parse_novel_coverage(notes), expected)
        self.assertIsNone(
            factory_driver.parse_novel_coverage("Novel coverage: malformed\n")
        )

    def test_legacy_suffixes_still_drive_the_offline_plateau_latch(self):
        with tempfile.TemporaryDirectory() as td:
            factory = Path(td) / "legacy-suffix-factory"
            factory.mkdir()
            (factory / "NOTES-r01.md").write_text(
                "Novel coverage: 4% — low due to repetition\n"
            )
            (factory / "NOTES-r02.md").write_text(
                "Novel coverage: 3% — low due to repetition\n"
            )

            info = factory_driver.factory_token_efficiency(factory)

        self.assertTrue(info["early_stop"])
        self.assertEqual(info["early_stop_at_round"], 2)

    def test_legacy_multiline_claims_still_drive_the_offline_plateau_latch(self):
        with tempfile.TemporaryDirectory() as td:
            factory = Path(td) / "legacy-multiline-factory"
            factory.mkdir()
            (factory / "NOTES-r01.md").write_text("Novel coverage:\n4%\n")
            (factory / "NOTES-r02.md").write_text("Novel coverage:\n3%\n")

            info = factory_driver.factory_token_efficiency(factory)

        self.assertTrue(info["early_stop"])
        self.assertEqual(info["early_stop_at_round"], 2)

    def test_legacy_parser_keeps_split_claims_but_ignores_unrelated_percentages(self):
        self.assertEqual(
            factory_driver.parse_novel_coverage(
                "Novel coverage:\n80% of tests passed.\n"
            ),
            80.0,
        )
        self.assertIsNone(factory_driver.parse_novel_coverage("Test coverage: 80%\n"))
        self.assertEqual(
            factory_driver.parse_novel_coverage("\tNovel coverage:\t4 %\n"),
            4.0,
        )

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

    def test_marker_baseline_notes_require_a_visible_payload_round(self):
        with tempfile.TemporaryDirectory() as td:
            factory = Path(td) / "marker-factory"
            factory.mkdir()
            (factory / "batch-r26.jsonl").write_text(
                json.dumps(factory_driver.thalamic("legacy-r26")) + "\n"
            )
            (factory / "NOTES-r25.md").write_text("Novel coverage: 2%\n")
            (factory / "NOTES-r26.md").write_text("Novel coverage: 3%\n")
            (factory / ".round-marker-mode.json").write_text(
                '{"version":1,"legacy_baseline":26,"commit_point":"ROUND-rNN.complete.json"}\n'
            )

            info = factory_driver.factory_token_efficiency(factory)

        self.assertEqual(
            [(item["round"], item["file"]) for item in info["rounds"]],
            [(26, "NOTES-r26.md")],
        )
        self.assertFalse(info["early_stop"])

    def test_frontiers_counts_only_marker_visible_records(self):
        with tempfile.TemporaryDirectory() as td:
            run = Path(td) / "run"
            factory = run / "marker-factory"
            factory.mkdir(parents=True)
            (factory / ".round-marker-mode.json").write_text(
                '{"version":1,"legacy_baseline":0,"commit_point":"ROUND-rNN.complete.json"}\n'
            )
            self._write_notes(factory, [(1, 80.0)])
            self._write_complete_marker(factory, 1)
            (factory / "batch-r02.jsonl").write_text('{"id":"interrupted"}\n')
            (factory / "ROUND-r02.publishing.json").write_text("{}\n")

            with redirect_stdout(StringIO()):
                frontiers = factory_driver.cmd_frontiers(run)

        self.assertEqual(frontiers[0]["records"], 1)
        self.assertEqual(frontiers[0]["highest_flushed"], 1)


if __name__ == "__main__":
    unittest.main()
