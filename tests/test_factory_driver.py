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


FIXTURES = REPO / "tests" / "fixtures"


class FactoryDriverSmoke(unittest.TestCase):
    def test_smoke_exercises_the_notes_gate_and_plateau_latch(self):
        buffer = StringIO()

        with redirect_stdout(buffer):
            code = factory_driver.cmd_smoke()

        self.assertEqual(code, 0)
        report = buffer.getvalue()
        self.assertIn("NOTES without a 'Novel coverage: <N>%' line cannot publish", report)
        self.assertIn("two consecutive sub-5% rounds early-stop the lane", report)

    def test_smoke_reports_an_unexpected_publish_rejection(self):
        buffer = StringIO()
        with mock.patch.object(
            factory_driver,
            "publish",
            side_effect=[TransactionError("unexpected transaction defect"), {"records": 1}],
        ), redirect_stdout(buffer):
            code = factory_driver.cmd_smoke()

        self.assertEqual(code, 1)
        self.assertIn(
            "unexpected publish rejection: unexpected transaction defect",
            buffer.getvalue(),
        )

    def test_smoke_reports_each_failed_notes_gate_invariant(self):
        buffer = StringIO()
        with mock.patch.object(
            factory_driver, "publish", side_effect=[{}, {"records": 0}]
        ), mock.patch.object(
            factory_driver,
            "factory_token_efficiency",
            return_value={"early_stop": False, "early_stop_at_round": None},
        ), redirect_stdout(buffer):
            code = factory_driver.cmd_smoke()

        self.assertEqual(code, 1)
        report = buffer.getvalue()
        self.assertIn("publish accepted NOTES without a 'Novel coverage' line", report)
        self.assertIn("transaction reserve/publish did not commit exactly one round", report)
        self.assertIn("coverage plateau did not early-stop", report)


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

    def test_duplicate_novel_coverage_lines_are_ambiguous(self):
        self.assertIsNone(
            factory_driver.parse_novel_coverage(
                "Novel coverage: 4%\nNovel coverage: 4%\n"
            )
        )
        self.assertIsNone(
            factory_driver.parse_novel_coverage(
                "Novel coverage: 4%\nNovel coverage: 80%\n"
            )
        )
        self.assertEqual(
            factory_driver.parse_novel_coverage("Novel coverage: 4%\n"), 4.0
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

    def test_named_snapshot_cleans_failed_staged_copy(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            run = root / "run"
            run.mkdir()
            (run / "entry.txt").write_text("inside\n")

            def fail_after_partial_copy(_src, staged):
                staged.mkdir()
                staged.joinpath("partial.txt").write_text("partial\n")
                raise TransactionError("source entry disappeared")

            with mock.patch.object(
                factory_driver,
                "copy_snapshot_tree",
                side_effect=fail_after_partial_copy,
            ), self.assertRaisesRegex(TransactionError, "source entry disappeared"):
                factory_driver.cmd_snapshot(run, "safe")

            self.assertFalse((root / "run-safe").exists())
            self.assertEqual(list(root.glob(".run-safe-*")), [])

    def test_named_snapshot_does_not_clobber_destination_created_before_publish(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            run = root / "run"
            run.mkdir()
            (run / "entry.txt").write_text("inside\n")
            dst = root / "run-safe"
            rename_noreplace = factory_driver.rename_snapshot_noreplace

            def create_destination_then_rename(staged, destination):
                destination.mkdir()
                destination.joinpath("owner.txt").write_text("other process\n")
                rename_noreplace(staged, destination)

            with mock.patch.object(
                factory_driver,
                "rename_snapshot_noreplace",
                side_effect=create_destination_then_rename,
            ), self.assertRaisesRegex(SystemExit, "refusing to overwrite"):
                factory_driver.cmd_snapshot(run, "safe")

            self.assertEqual(dst.joinpath("owner.txt").read_text(), "other process\n")
            self.assertEqual(list(root.glob(".run-safe-*")), [])

    def test_named_snapshot_keeps_only_marker_visible_batches(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            run = root / "run"
            factory = run / "marker-factory"
            factory.mkdir(parents=True)
            (factory / ".round-marker-mode.json").write_text(
                '{"version":1,"legacy_baseline":0,'
                '"commit_point":"ROUND-rNN.complete.json"}\n'
            )
            notes = factory / "NOTES-r01.md"
            notes.write_text("Novel coverage: 80%\n")
            batch = factory / "batch-r01.jsonl"
            batch.write_text(json.dumps(factory_driver.thalamic("committed")) + "\n")
            marker = factory / "ROUND-r01.complete.json"
            marker.write_text(
                json.dumps(
                    {
                        "version": 1,
                        "factory": factory.name,
                        "round": 1,
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
            (factory / "batch-r02.jsonl").write_text('{"id":"uncommitted"}\n')

            with redirect_stdout(StringIO()):
                factory_driver.cmd_snapshot(run, "stable")

            snapshot_factory = root / "run-stable" / factory.name
            self.assertTrue(snapshot_factory.joinpath(batch.name).exists())
            self.assertFalse(snapshot_factory.joinpath("batch-r02.jsonl").exists())

    def test_snapshot_rejects_symlink_replacement_after_preflight(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            run = root / "run"
            run.mkdir()
            entry = run / "entry.txt"
            entry.write_text("inside\n")
            outside = root / "outside.txt"
            outside.write_text("outside\n")

            def replace_after_preflight(_src):
                entry.unlink()
                entry.symlink_to(outside)

            with mock.patch.object(
                factory_driver,
                "reject_snapshot_symlinks",
                side_effect=replace_after_preflight,
            ), self.assertRaisesRegex(TransactionError, "cannot snapshot path safely"):
                factory_driver.snapshot_to_temp(run, "factory-symlink-preflight-")

    def test_snapshot_rejects_symlink_replacement_during_copy(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            run = root / "run"
            run.mkdir()
            entry = run / "entry.txt"
            entry.write_text("inside\n")
            outside = root / "outside.txt"
            outside.write_text("outside\n")
            real_open = factory_driver.os.open
            replaced = False

            def replace_during_open(path, flags, *args, **kwargs):
                nonlocal replaced
                if (
                    not replaced
                    and path == "entry.txt"
                    and kwargs.get("dir_fd") is not None
                    and not flags & factory_driver.os.O_CREAT
                ):
                    entry.unlink()
                    entry.symlink_to(outside)
                    replaced = True
                return real_open(path, flags, *args, **kwargs)

            with mock.patch.object(
                factory_driver.os, "open", side_effect=replace_during_open
            ), self.assertRaisesRegex(TransactionError, "cannot snapshot path safely"):
                factory_driver.snapshot_to_temp(run, "factory-symlink-copy-")

            self.assertTrue(replaced)

    def test_snapshot_wraps_destination_setup_failure(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            run = root / "run"
            run.mkdir()

            with self.assertRaisesRegex(
                TransactionError, "cannot stage snapshot safely"
            ) as captured:
                factory_driver.copy_snapshot_tree(
                    run, root / "missing-parent" / "snapshot"
                )

            self.assertIsInstance(captured.exception.__cause__, FileNotFoundError)


class FactoryDriverValidation(unittest.TestCase):
    def test_marker_visibility_brackets_copy_and_retries_on_commit(self):
        with tempfile.TemporaryDirectory() as td:
            run = Path(td) / "run"
            run.mkdir()
            events = []
            real_snapshot = factory_driver.snapshot_to_temp
            visibility = [
                {},
                {"factory": {Path("batch-r01.jsonl")}},
                {"factory": {Path("batch-r01.jsonl")}},
                {"factory": {Path("batch-r01.jsonl")}},
            ]

            def observe_visible(src):
                events.append("visibility")
                self.assertEqual(src, run)
                return visibility.pop(0)

            def observe_snapshot(src, prefix):
                events.append("copy")
                return real_snapshot(src, prefix)

            with mock.patch.object(
                factory_driver,
                "marker_visible_jsonl_paths",
                side_effect=observe_visible,
            ), mock.patch.object(
                factory_driver, "snapshot_to_temp", side_effect=observe_snapshot
            ):
                temp, _snapshot, visible = factory_driver.marker_visible_snapshot(
                    run, "factory-lock-test-"
                )
            temp.cleanup()

        self.assertEqual(visible, {"factory": {Path("batch-r01.jsonl")}})
        self.assertEqual(
            events,
            ["visibility", "copy", "visibility", "visibility", "copy", "visibility"],
        )

    def test_marker_visibility_retries_transient_cleanup_during_copy(self):
        with tempfile.TemporaryDirectory() as td:
            run = Path(td) / "run"
            run.mkdir()
            (run / "stable.txt").write_text("stable\n")
            real_snapshot = factory_driver.snapshot_to_temp
            attempts = 0

            def transient_cleanup(src, prefix):
                nonlocal attempts
                attempts += 1
                if attempts == 1:
                    try:
                        raise FileNotFoundError("transaction marker was cleaned up")
                    except FileNotFoundError as cause:
                        raise TransactionError("snapshot entry disappeared") from cause
                return real_snapshot(src, prefix)

            with mock.patch.object(
                factory_driver, "snapshot_to_temp", side_effect=transient_cleanup
            ):
                temp, snapshot, visible = factory_driver.marker_visible_snapshot(
                    run, "factory-cleanup-retry-"
                )
            try:
                self.assertEqual(snapshot.joinpath("stable.txt").read_text(), "stable\n")
                self.assertEqual(visible, {})
                self.assertEqual(attempts, 2)
            finally:
                temp.cleanup()

    def test_validate_snapshot_excludes_uncommitted_marker_batches(self):
        with tempfile.TemporaryDirectory() as td:
            run = Path(td) / "run"
            factory = run / "marker-factory"
            factory.mkdir(parents=True)
            (factory / ".round-marker-mode.json").write_text(
                '{"version":1,"legacy_baseline":0,'
                '"commit_point":"ROUND-rNN.complete.json"}\n'
            )
            (factory / "batch-r01.jsonl").write_text('{"broken":\n')
            seen = []

            def observe_snapshot(_script, snapshot, *_options):
                seen.extend(snapshot.rglob("*.jsonl"))
                return 0, "", ""

            with mock.patch.object(
                factory_driver, "run_tool", side_effect=observe_snapshot
            ), redirect_stdout(StringIO()):
                self.assertEqual(factory_driver.cmd_validate(run), 0)

        self.assertEqual(seen, [])


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
                        "version": 1,
                        "factory": factory.name,
                        "round": 1,
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

    def test_audit_resolves_inflight_sibling_ids_before_relocating_snapshot(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            run = root / "outputs" / "raw" / "2099-01-01"
            factory = run / "marker-factory"
            sibling = run / "sibling-factory"
            factory.mkdir(parents=True)
            sibling.mkdir()
            for path in (factory, sibling):
                (path / ".round-marker-mode.json").write_text(
                    '{"version":1,"legacy_baseline":0,'
                    '"commit_point":"ROUND-rNN.complete.json"}\n'
                )

            batch = factory / "batch-r01.jsonl"
            notes = factory / "NOTES-r01.md"
            batch.write_text(json.dumps(factory_driver.thalamic("committed")) + "\n")
            notes.write_text("Novel coverage: 80%\n")
            marker = factory / "ROUND-r01.complete.json"
            marker.write_text(
                json.dumps(
                    {
                        "version": 1,
                        "factory": factory.name,
                        "round": 1,
                        "records": 1,
                        "expected_records": 1,
                        "commit_point": marker.name,
                        "files": [
                            {"name": batch.name, "sha256": hashlib.sha256(batch.read_bytes()).hexdigest()},
                            {"name": notes.name, "sha256": hashlib.sha256(notes.read_bytes()).hexdigest()},
                        ],
                    }
                )
                + "\n"
            )

            token = "a" * 32
            stage = (
                root
                / "outputs"
                / "staging"
                / run.name
                / sibling.name
                / f"r01-{token}"
            )
            stage.mkdir(parents=True)
            (stage / "batch-r01.jsonl").write_text(
                json.dumps(factory_driver.thalamic("in-flight")) + "\n"
            )
            (sibling / "ROUND-r01.reserved.json").write_text(
                json.dumps(
                    {
                        "factory": sibling.name,
                        "round": 1,
                        "token": token,
                        "staging_dir": str(stage),
                    }
                )
                + "\n"
            )
            (sibling / "ROUND-r01.publishing.json").write_text(
                json.dumps({"factory": sibling.name, "round": 1, "token": token})
                + "\n"
            )

            with mock.patch.object(
                factory_driver, "run_tool", return_value=(0, "", "")
            ), redirect_stdout(StringIO()):
                self.assertEqual(factory_driver.cmd_audit(run), 0)


if __name__ == "__main__":
    unittest.main()
