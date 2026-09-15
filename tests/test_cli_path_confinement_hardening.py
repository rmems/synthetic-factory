#!/usr/bin/env python3
"""Dataset CLIs refuse unsafe leaves through operator_paths before any sink.

Covers the remaining S8707 surface on ``curate_rewards``,
``curate_preferences``, ``verify_execution``, ``next_round`` and
``round_txn``: traversal, absolute escape, input/output symlinks, dangling
links, FIFO/device leaves, and destination replacement. A failed validation
must not create a partial destination, marker, or temporary artifact.
"""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import os
import stat
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

_TESTS = Path(__file__).resolve().parent
_PIPELINES = _TESTS.parent / "pipelines"
for entry in (_TESTS, _PIPELINES):
    if str(entry) not in sys.path:
        sys.path.insert(0, str(entry))

from preference_test_support import pair, write_jsonl  # noqa: E402

import curate_preferences  # noqa: E402
import curate_rewards  # noqa: E402
import next_round  # noqa: E402
import round_txn  # noqa: E402
import verify_execution  # noqa: E402

SECRETS = ("passwd", "HOME=")


def _fifo(path: Path) -> Path:
    os.mkfifo(path)
    return path


class _FunnelCase(unittest.TestCase):
    def assertRefused(self, call, *args, needle, argument, candidate=None):
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr), self.assertRaises(SystemExit) as raised:
            call(*args)
        self.assertEqual(raised.exception.code, 2)
        text = stderr.getvalue()
        self.assertIn("error:", text)
        self.assertIn(f"{argument}:", text)
        self.assertIn(needle, text)
        for secret in SECRETS:
            self.assertNotIn(secret, text)
        if candidate is not None:
            self.assertNotIn(os.fspath(candidate), text)


class RewardsHardening(_FunnelCase):
    parser = argparse.ArgumentParser(prog="curate_rewards.py")

    def test_traversal_and_absolute_escape_name_the_argument(self):
        for candidate in ("/etc/passwd", "../" * 12 + "etc/passwd"):
            with self.subTest(candidate=candidate):
                self.assertRefused(
                    curate_rewards._inputs,
                    self.parser,
                    SimpleNamespace(input=candidate),
                    needle="outside the working, home and temp trees",
                    argument="input",
                )

    def test_input_symlink_and_dangling_symlink_are_refused(self):
        with tempfile.TemporaryDirectory() as td:
            real = Path(td) / "real.jsonl"
            real.write_text("{}\n", encoding="utf-8")
            link = Path(td) / "linked.jsonl"
            dangling = Path(td) / "dangling.jsonl"
            link.symlink_to(real)
            dangling.symlink_to(Path(td) / "missing")
            self.assertRefused(
                curate_rewards._inputs,
                self.parser,
                SimpleNamespace(input=str(link)),
                needle="the path is a symlink",
                argument="input",
            )
            self.assertRefused(
                curate_rewards._inputs,
                self.parser,
                SimpleNamespace(input=str(dangling)),
                needle="the path is a dangling symlink",
                argument="input",
            )

    def test_fifo_input_is_refused(self):
        with tempfile.TemporaryDirectory() as td:
            fifo = _fifo(Path(td) / "pipe")
            self.assertRefused(
                curate_rewards._inputs,
                self.parser,
                SimpleNamespace(input=str(fifo)),
                needle="the path is a special file",
                argument="input",
            )

    def test_output_symlink_and_destination_replacement_leave_no_artifact(self):
        with tempfile.TemporaryDirectory() as td:
            source = Path(td) / "in.jsonl"
            source.write_text(json.dumps({"reward_components": {"total": 1.0}}) + "\n")
            existing = Path(td) / "out.jsonl"
            existing.write_text("keep\n", encoding="utf-8")
            link = Path(td) / "linked-out.jsonl"
            link.symlink_to(existing)
            sidecar = Path(td) / "side.jsonl"
            for bad, needle, argument in (
                (str(link), "the path is a symlink", "output"),
                (str(existing), "the destination already exists", "output"),
            ):
                with (
                    self.subTest(bad=bad),
                    mock.patch.object(curate_rewards, "convert_jsonl") as sink,
                ):
                    self.assertRefused(
                        curate_rewards.main,
                        ["convert", str(source), bad, str(sidecar)],
                        needle=needle,
                        argument=argument,
                    )
                    sink.assert_not_called()
            self.assertEqual(existing.read_text(encoding="utf-8"), "keep\n")
            self.assertFalse(sidecar.exists())

    def test_classify_under_a_temporary_directory_still_works(self):
        with tempfile.TemporaryDirectory() as td:
            source = Path(td) / "one.jsonl"
            source.write_text(json.dumps({"reward_components": {"total": 1.0}}) + "\n")
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                self.assertEqual(curate_rewards.main(["classify", str(source)]), 0)
            self.assertEqual(json.loads(stdout.getvalue())["records"], 1)


class PreferencesHardening(_FunnelCase):
    parser = argparse.ArgumentParser(prog="curate_preferences.py")

    def test_output_symlink_and_replacement_are_refused_before_write_run(self):
        with tempfile.TemporaryDirectory() as td:
            source = Path(td) / "pairs.jsonl"
            write_jsonl(source, [pair("confined")])
            existing = Path(td) / "out.jsonl"
            existing.write_text("keep\n", encoding="utf-8")
            link = Path(td) / "linked-out.jsonl"
            link.symlink_to(existing)
            manifest = Path(td) / "manifest.jsonl"
            for bad, needle, flag in (
                (str(link), "the path is a symlink", "--output"),
                (str(existing), "the destination already exists", "--output"),
            ):
                with (
                    self.subTest(bad=bad),
                    mock.patch.object(curate_preferences, "write_run") as writer,
                    mock.patch.object(curate_preferences, "curate_source") as source_fn,
                ):
                    self.assertRefused(
                        curate_preferences.main,
                        ["curate", str(source), "--output", bad, "--manifest", str(manifest)],
                        needle=needle,
                        argument=flag,
                    )
                    writer.assert_not_called()
                    source_fn.assert_not_called()
            self.assertEqual(existing.read_text(encoding="utf-8"), "keep\n")
            self.assertFalse(manifest.exists())

    def test_scan_under_a_temporary_directory_still_works(self):
        with tempfile.TemporaryDirectory() as td:
            source = Path(td) / "pairs.jsonl"
            write_jsonl(source, [pair("confined")])
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                self.assertEqual(curate_preferences.main(["scan", str(source), "--json"]), 0)
            self.assertEqual(json.loads(stdout.getvalue())["summary"]["retained_pairs"], 1)


class VerifyExecutionHardening(_FunnelCase):
    parser = argparse.ArgumentParser(prog="verify_execution.py")

    def test_record_fifo_and_symlink_are_refused_before_jsonl_lines(self):
        with tempfile.TemporaryDirectory() as td:
            real = Path(td) / "batch.jsonl"
            real.write_text("\n", encoding="utf-8")
            link = Path(td) / "linked.jsonl"
            link.symlink_to(real)
            fifo = _fifo(Path(td) / "pipe")
            for candidate, needle, argument in (
                (str(link), "the path is a symlink", "--record"),
                (str(fifo), "the path is a special file", "--record"),
            ):
                with (
                    self.subTest(candidate=candidate),
                    mock.patch.object(verify_execution, "jsonl_lines") as lines,
                ):
                    self.assertRefused(
                        verify_execution.main,
                        ["--record", candidate],
                        needle=needle,
                        argument=argument,
                    )
                    lines.assert_not_called()

    def test_batch_under_a_temporary_directory_still_works(self):
        with tempfile.TemporaryDirectory() as td:
            batch = Path(td) / "batch-r01.jsonl"
            batch.write_text("\n", encoding="utf-8")
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout), self.assertRaises(SystemExit) as raised:
                verify_execution.main(["--batch", str(batch), "--json"])
            self.assertEqual(raised.exception.code, 0)
            self.assertEqual(json.loads(stdout.getvalue())["counts"]["total"], 0)


class NextRoundHardening(_FunnelCase):
    parser = argparse.ArgumentParser(prog="next_round.py")

    def test_symlink_and_fifo_factory_dirs_are_refused_before_allocate(self):
        with tempfile.TemporaryDirectory() as td:
            factory = Path(td) / "lane"
            factory.mkdir()
            link = Path(td) / "linked-lane"
            link.symlink_to(factory, target_is_directory=True)
            fifo = _fifo(Path(td) / "pipe")
            for candidate, needle in (
                (str(link), "the path is a symlink"),
                (str(fifo), "the path is a special file"),
            ):
                with (
                    self.subTest(candidate=candidate),
                    mock.patch.object(next_round, "allocate") as allocate,
                    mock.patch.object(next_round, "write_index") as index,
                ):
                    self.assertRefused(
                        next_round.main,
                        [candidate],
                        needle=needle,
                        argument="path",
                    )
                    allocate.assert_not_called()
                    index.assert_not_called()

    def test_a_factory_directory_under_temp_still_works(self):
        with tempfile.TemporaryDirectory() as td:
            factory = Path(td) / "lane"
            factory.mkdir()
            (factory / "batch-r01.jsonl").write_text("{}\n", encoding="utf-8")
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout), self.assertRaises(SystemExit) as raised:
                next_round.main([str(factory)])
            self.assertEqual(raised.exception.code, 0)
            self.assertEqual(json.loads(stdout.getvalue())["next_round"], 2)


class RoundTxnHardening(_FunnelCase):
    parser = argparse.ArgumentParser(prog="round_txn.py")

    def test_symlink_and_fifo_factory_dirs_leave_no_marker(self):
        with tempfile.TemporaryDirectory() as td:
            factory = Path(td) / "lane"
            factory.mkdir()
            link = Path(td) / "linked-lane"
            link.symlink_to(factory, target_is_directory=True)
            fifo = _fifo(Path(td) / "pipe")
            for candidate, needle, argv in (
                (str(link), "the path is a symlink", ["frontier", str(link)]),
                (str(fifo), "the path is a special file", ["reserve", str(fifo), "--round", "1", "--expected", "1"]),
            ):
                with (
                    self.subTest(candidate=candidate),
                    mock.patch.object(round_txn, "frontier_status") as frontier,
                    mock.patch.object(round_txn, "reserve") as reserve,
                ):
                    self.assertRefused(
                        round_txn.main,
                        argv,
                        needle=needle,
                        argument="factory_dir",
                    )
                    frontier.assert_not_called()
                    reserve.assert_not_called()
            self.assertEqual(list(factory.iterdir()), [])

    def test_frontier_under_a_temporary_directory_still_works(self):
        with tempfile.TemporaryDirectory() as td:
            factory = Path(td) / "lane"
            factory.mkdir()
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                self.assertEqual(round_txn.main(["frontier", str(factory)]), 0)
            self.assertEqual(json.loads(stdout.getvalue())["factory"], "lane")


class DeviceLeaf(unittest.TestCase):
    def test_dev_null_is_a_character_device(self):
        self.assertTrue(stat.S_ISCHR(os.lstat("/dev/null").st_mode))


if __name__ == "__main__":
    unittest.main()
