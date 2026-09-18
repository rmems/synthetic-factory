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
from typing import NamedTuple
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

OUTSIDE = "outside the working, home and temp trees"
REWARD_ROW = json.dumps({"reward_components": {"total": 1.0}}) + "\n"


class Expected(NamedTuple):
    needle: str
    argument: str


def _fifo(path: Path) -> Path:
    os.mkfifo(path)
    return path


def _linked_existing(root: Path, name: str) -> tuple[Path, Path]:
    existing = root / name
    existing.write_text("keep\n", encoding="utf-8")
    link = root / f"linked-{name}"
    link.symlink_to(existing)
    return existing, link


class _FunnelCase:
    def assertRefused(self, call, argv, expected: Expected):
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr), self.assertRaises(SystemExit) as raised:
            call(*argv)
        self.assertEqual(raised.exception.code, 2)
        text = stderr.getvalue()
        self.assertIn("error:", text)
        self.assertIn(f"{expected.argument}:", text)
        self.assertIn(expected.needle, text)
        self.assertNotIn("passwd", text)
        self.assertNotIn("HOME=", text)


class FunnelLeaves(_FunnelCase, unittest.TestCase):
    """Direct funnels refuse unsafe leaves before any CLI sink is selected."""

    def test_verify_selected_file_mode_ignores_an_inactive_positional_run_dir(self):
        """A selected --record or --batch path takes precedence over run_dir."""

        parser = argparse.ArgumentParser(prog="verify_execution.py")
        with tempfile.TemporaryDirectory() as td:
            for option, field in (("record", "record"), ("batch", "batch")):
                with self.subTest(option=option):
                    selected = Path(td) / f"{option}.jsonl"
                    selected.write_text("{}\n", encoding="utf-8")
                    values = {"run_dir": "/etc/passwd", "record": None, "batch": None}
                    values[field] = str(selected)

                    run_dir, record, batch = verify_execution._confined(
                        parser, SimpleNamespace(**values)
                    )

                    self.assertIsNone(run_dir)
                    self.assertEqual(record if field == "record" else batch, selected)
                    self.assertIsNone(batch if field == "record" else record)

    def test_verify_selected_record_cannot_fall_back_to_a_valid_run_dir(self):
        """Mode precedence selects --record even if only run_dir is confined."""

        parser = argparse.ArgumentParser(prog="verify_execution.py")
        with tempfile.TemporaryDirectory() as td:
            self.assertRefused(
                verify_execution._confined,
                (
                    parser,
                    SimpleNamespace(run_dir=td, record="/etc/passwd", batch=None),
                ),
                Expected(OUTSIDE, "--record"),
            )

    def test_rewards_and_verify_refuse_escape_symlink_dangling_fifo(self):
        rewards = argparse.ArgumentParser(prog="curate_rewards.py")
        verify = argparse.ArgumentParser(prog="verify_execution.py")
        for candidate in ("/etc/passwd", "../" * 12 + "etc/passwd"):
            with self.subTest(candidate=candidate):
                self.assertRefused(
                    curate_rewards._inputs,
                    (rewards, SimpleNamespace(input=candidate)),
                    Expected(OUTSIDE, "input"),
                )
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            real = root / "real.jsonl"
            real.write_text("{}\n", encoding="utf-8")
            link = root / "linked.jsonl"
            dangling = root / "dangling.jsonl"
            link.symlink_to(real)
            dangling.symlink_to(root / "missing")
            fifo = _fifo(root / "pipe")
            cases = (
                (curate_rewards._inputs, rewards, SimpleNamespace(input=str(link)), Expected("the path is a symlink", "input")),
                (curate_rewards._inputs, rewards, SimpleNamespace(input=str(dangling)), Expected("the path is a dangling symlink", "input")),
                (curate_rewards._inputs, rewards, SimpleNamespace(input=str(fifo)), Expected("the path is a special file", "input")),
                (verify_execution._confined, verify, SimpleNamespace(run_dir=None, record=str(link), batch=None), Expected("the path is a symlink", "--record")),
                (verify_execution._confined, verify, SimpleNamespace(run_dir=None, record=str(fifo), batch=None), Expected("the path is a special file", "--record")),
            )
            for funnel, parser, args, expected in cases:
                with self.subTest(expected=expected):
                    self.assertRefused(funnel, (parser, args), expected)


class WriterLeaves(_FunnelCase, unittest.TestCase):
    def test_convert_and_curate_refuse_output_symlink_and_replacement(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            reward_src = root / "in.jsonl"
            reward_src.write_text(REWARD_ROW, encoding="utf-8")
            pref_src = root / "pairs.jsonl"
            write_jsonl(pref_src, [pair("confined")])
            existing, link = _linked_existing(root, "out.jsonl")
            sidecar = root / "side.jsonl"
            manifest = root / "manifest.jsonl"
            writers = (
                (curate_rewards, "convert_jsonl", ["convert", str(reward_src), str(link), str(sidecar)], Expected("the path is a symlink", "output")),
                (curate_rewards, "convert_jsonl", ["convert", str(reward_src), str(existing), str(sidecar)], Expected("the destination already exists", "output")),
                (curate_preferences, "write_run", ["curate", str(pref_src), "--output", str(link), "--manifest", str(manifest)], Expected("the path is a symlink", "--output")),
                (curate_preferences, "write_run", ["curate", str(pref_src), "--output", str(existing), "--manifest", str(manifest)], Expected("the destination already exists", "--output")),
            )
            for module, sink_name, argv, expected in writers:
                with self.subTest(argv=argv), mock.patch.object(module, sink_name) as sink:
                    self.assertRefused(module.main, (argv,), expected)
                    sink.assert_not_called()
            self.assertEqual(existing.read_text(encoding="utf-8"), "keep\n")
            self.assertFalse(sidecar.exists())
            self.assertFalse(manifest.exists())


class FactoryLeaves(_FunnelCase, unittest.TestCase):
    def test_next_round_and_round_txn_refuse_symlink_and_fifo_factory_dirs(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            factory = root / "lane"
            factory.mkdir()
            link = root / "linked-lane"
            link.symlink_to(factory, target_is_directory=True)
            fifo = _fifo(root / "pipe")
            cases = (
                (next_round, [str(link)], Expected("the path is a symlink", "path"), ("allocate", "write_index")),
                (next_round, [str(fifo)], Expected("the path is a special file", "path"), ("allocate", "write_index")),
                (round_txn, ["frontier", str(link)], Expected("the path is a symlink", "factory_dir"), ("frontier_status", "reserve")),
                (round_txn, ["reserve", str(fifo), "--round", "1", "--expected", "1"], Expected("the path is a special file", "factory_dir"), ("frontier_status", "reserve")),
            )
            for module, argv, expected, sinks in cases:
                with self.subTest(argv=argv), contextlib.ExitStack() as stack:
                    mocks = [stack.enter_context(mock.patch.object(module, name)) for name in sinks]
                    self.assertRefused(module.main, (argv,), expected)
                    for sink in mocks:
                        sink.assert_not_called()
            self.assertEqual(list(factory.iterdir()), [])


class HappyPaths(unittest.TestCase):
    def test_temp_directory_workflows_still_work(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            reward = root / "one.jsonl"
            reward.write_text(REWARD_ROW, encoding="utf-8")
            pairs = root / "pairs.jsonl"
            write_jsonl(pairs, [pair("confined")])
            batch = root / "batch-r01.jsonl"
            batch.write_text("\n", encoding="utf-8")
            factory = root / "lane"
            factory.mkdir()
            (factory / "batch-r01.jsonl").write_text("{}\n", encoding="utf-8")

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                self.assertEqual(curate_rewards.main(["classify", str(reward)]), 0)
            self.assertEqual(json.loads(stdout.getvalue())["records"], 1)

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                self.assertEqual(curate_preferences.main(["scan", str(pairs), "--json"]), 0)
            self.assertEqual(json.loads(stdout.getvalue())["summary"]["retained_pairs"], 1)

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout), self.assertRaises(SystemExit) as raised:
                verify_execution.main(["--batch", str(batch), "--json"])
            self.assertEqual(raised.exception.code, 0)
            self.assertEqual(json.loads(stdout.getvalue())["counts"]["total"], 0)

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout), self.assertRaises(SystemExit) as raised:
                next_round.main([str(factory)])
            self.assertEqual(raised.exception.code, 0)
            self.assertEqual(json.loads(stdout.getvalue())["next_round"], 2)

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                self.assertEqual(round_txn.main(["frontier", str(factory)]), 0)
            self.assertEqual(json.loads(stdout.getvalue())["factory"], "lane")


class DeviceLeaf(unittest.TestCase):
    def test_dev_null_is_a_character_device(self):
        self.assertTrue(stat.S_ISCHR(os.lstat("/dev/null").st_mode))


if __name__ == "__main__":
    unittest.main()
