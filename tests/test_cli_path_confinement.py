#!/usr/bin/env python3
"""The small CLIs confine operator paths right after parsing (S8707, B3 of #211).

Each CLI refuses a path outside the working, home and temp trees with
argparse's own error shape (exit 2) before any filesystem sink runs, keeps
working for paths under a temporary directory, and never confines
``--source-path``, which is a label written into records rather than a path.
"""

import argparse
import contextlib
import io
import json
import os
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
import verify_execution  # noqa: E402

REFUSAL = "outside the working, home and temp trees"
OUTSIDE = ("/etc/passwd", "../" * 12 + "etc/passwd")


def _quiet():
    return contextlib.redirect_stderr(io.StringIO())


class _FunnelCase(unittest.TestCase):
    """Shared assertions for the three post-parse funnels."""

    def assertRefused(self, call, *args):
        """``call(*args)`` exits 2 with argparse's refusal; args are bound here, not in a closure."""
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr), self.assertRaises(SystemExit) as raised:
            call(*args)
        self.assertEqual(raised.exception.code, 2)
        self.assertIn(REFUSAL, stderr.getvalue())
        self.assertIn("error:", stderr.getvalue())


class RewardsFunnel(_FunnelCase):
    parser = argparse.ArgumentParser(prog="curate_rewards.py")

    def test_each_path_argument_is_refused_outside_the_operator_trees(self):
        for name in ("input", "output", "sidecars", "manifest", "units_migration"):
            for candidate in OUTSIDE:
                with self.subTest(name=name, candidate=candidate):
                    self.assertRefused(
                        curate_rewards._inputs, self.parser, SimpleNamespace(**{name: candidate})
                    )

    def test_census_confines_every_element_of_the_input_list(self):
        with tempfile.TemporaryDirectory() as td:
            good = os.path.join(td, "good.jsonl")
            for bad in OUTSIDE:
                with self.subTest(bad=bad):
                    self.assertRefused(
                        curate_rewards._inputs, self.parser, SimpleNamespace(inputs=[good, bad])
                    )
            paths = curate_rewards._inputs(self.parser, SimpleNamespace(inputs=[good, td]))
            self.assertEqual(paths.inputs, (Path(os.path.realpath(good)), Path(os.path.realpath(td))))

    def test_absent_arguments_stay_none_and_source_path_is_not_a_path(self):
        with tempfile.TemporaryDirectory() as td:
            paths = curate_rewards._inputs(
                self.parser, SimpleNamespace(input=td, source_path="/etc/passwd")
            )
        self.assertEqual(paths.input, Path(os.path.realpath(td)))
        self.assertNotIn("source_path", curate_rewards.Inputs._fields)
        for name in ("output", "sidecars", "manifest", "units_migration"):
            self.assertIsNone(getattr(paths, name))
        self.assertEqual(paths.inputs, ())


class RewardsCli(_FunnelCase):
    def test_every_subcommand_refuses_before_its_sink_runs(self):
        sinks = ("classify_jsonl", "convert_jsonl", "convert_run", "census_jsonl", "load_units_migration")
        commands = {
            "classify": ["classify", "{bad}"],
            "classify --units-migration": ["classify", "x.jsonl", "--units-migration", "{bad}"],
            "convert": ["convert", "x.jsonl", "out.jsonl", "{bad}"],
            "convert --manifest": ["convert", "x.jsonl", "out.jsonl", "side.jsonl", "--manifest", "{bad}"],
            "census": ["census", "x.jsonl", "{bad}"],
            "run": ["run", "x", "{bad}"],
        }
        for label, argv in commands.items():
            for bad in OUTSIDE:
                with self.subTest(command=label, bad=bad), contextlib.ExitStack() as stack:
                    mocks = {name: stack.enter_context(mock.patch.object(curate_rewards, name))
                             for name in sinks}
                    self.assertRefused(
                        curate_rewards.main, [a.replace("{bad}", bad) for a in argv]
                    )
                    for name, sink in mocks.items():
                        sink.assert_not_called()

    def test_paths_under_a_temporary_directory_still_work(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            one, two = root / "one.jsonl", root / "two.jsonl"
            for path in (one, two):
                path.write_text(json.dumps({"reward_components": {"total": 1.0}}) + "\n", encoding="utf-8")
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                self.assertEqual(curate_rewards.main(["classify", str(one)]), 0)
            summary = json.loads(stdout.getvalue())
            self.assertEqual(summary["input"], os.path.realpath(one))
            self.assertEqual(summary["records"], 1)
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                self.assertEqual(curate_rewards.main(["census", str(one), str(two)]), 0)
            census = json.loads(stdout.getvalue())
            self.assertEqual(census["inputs"], [os.path.realpath(one), os.path.realpath(two)])
            self.assertEqual(census["records"], 2)


class PreferencesFunnel(_FunnelCase):
    parser = argparse.ArgumentParser(prog="curate_preferences.py")

    def test_each_path_argument_is_refused_outside_the_operator_trees(self):
        for name in curate_preferences.Inputs._fields:
            for candidate in OUTSIDE:
                with self.subTest(name=name, candidate=candidate):
                    self.assertRefused(
                        curate_preferences._inputs,
                        self.parser,
                        SimpleNamespace(**{name: Path(candidate)}),
                    )

    def test_paths_under_the_operator_trees_resolve_and_absent_ones_stay_none(self):
        with tempfile.TemporaryDirectory() as td:
            paths = curate_preferences._inputs(
                self.parser, SimpleNamespace(source=Path(td), expect=Path(td) / "audit.json")
            )
        self.assertEqual(paths.source, Path(os.path.realpath(td)))
        self.assertEqual(paths.expect, Path(os.path.realpath(td)) / "audit.json")
        for name in ("output", "manifest", "first", "second"):
            self.assertIsNone(getattr(paths, name))


class PreferencesCli(_FunnelCase):
    def test_every_subcommand_refuses_before_its_sink_runs(self):
        commands = {
            "scan": ["scan", "{bad}"],
            "audit": ["audit", "{bad}"],
            "audit --expect": ["audit", "src", "--expect", "{bad}"],
            "reconcile first": ["reconcile", "{bad}", "src"],
            "reconcile second": ["reconcile", "src", "{bad}"],
            "curate source": ["curate", "{bad}", "--output", "o", "--manifest", "m"],
            "curate --output": ["curate", "src", "--output", "{bad}", "--manifest", "m"],
            "curate --manifest": ["curate", "src", "--output", "o", "--manifest", "{bad}"],
        }
        for label, argv in commands.items():
            for bad in OUTSIDE:
                with (self.subTest(command=label, bad=bad),
                      mock.patch.object(curate_preferences, "curate_source") as source,
                      mock.patch.object(curate_preferences, "write_run") as writer):
                    self.assertRefused(
                        curate_preferences.main, [a.replace("{bad}", bad) for a in argv]
                    )
                    source.assert_not_called()
                    writer.assert_not_called()

    def test_paths_under_a_temporary_directory_still_work(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "batch.jsonl"
            write_jsonl(source, [pair("confined")])
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                self.assertEqual(curate_preferences.main(["scan", str(source), "--json"]), 0)
            summary = json.loads(stdout.getvalue())["summary"]
            self.assertEqual(summary["source"], os.path.realpath(source))
            self.assertEqual(summary["retained_pairs"], 1)
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                self.assertEqual(
                    curate_preferences.main(["reconcile", str(source), str(source)]), 0
                )
            self.assertIn(f"{os.path.realpath(source)} and {os.path.realpath(source)} scan identically",
                          stdout.getvalue())


class VerifyExecutionFunnel(_FunnelCase):
    parser = argparse.ArgumentParser(prog="verify_execution.py")

    def test_each_path_argument_is_refused_outside_the_operator_trees(self):
        for name in ("run_dir", "record", "batch"):
            for candidate in OUTSIDE:
                with self.subTest(name=name, candidate=candidate):
                    args = SimpleNamespace(**{"run_dir": None, "record": None, "batch": None, name: candidate})
                    self.assertRefused(verify_execution._confined, self.parser, args)

    def test_selected_batch_path_resolves_and_inactive_values_stay_none(self):
        with tempfile.TemporaryDirectory() as td:
            args = SimpleNamespace(run_dir=td, record=None, batch=os.path.join(td, "b.jsonl"))
            run_dir, record, batch = verify_execution._confined(self.parser, args)
        self.assertIsNone(run_dir)
        self.assertIsNone(record)
        self.assertEqual(batch, Path(os.path.realpath(td)) / "b.jsonl")


class VerifyExecutionCli(_FunnelCase):
    def test_every_mode_refuses_before_its_sink_runs(self):
        commands = {"run_dir": ["{bad}"], "--record": ["--record", "{bad}"], "--batch": ["--batch", "{bad}"]}
        for label, argv in commands.items():
            for bad in OUTSIDE:
                with (self.subTest(mode=label, bad=bad),
                      mock.patch.object(verify_execution, "audit_run") as audit,
                      mock.patch.object(verify_execution, "verify_batch_for_frontier") as gate,
                      mock.patch.object(verify_execution, "jsonl_lines") as lines):
                    self.assertRefused(
                        verify_execution.main, [a.replace("{bad}", bad) for a in argv]
                    )
                    for sink in (audit, gate, lines):
                        sink.assert_not_called()

    def test_paths_under_a_temporary_directory_still_work(self):
        with tempfile.TemporaryDirectory() as td:
            batch = Path(td) / "batch-r01.jsonl"
            batch.write_text("\n", encoding="utf-8")
            for argv in (["--batch", str(batch), "--json"], [td, "--json"]):
                stdout = io.StringIO()
                with (self.subTest(argv=argv), contextlib.redirect_stdout(stdout),
                      self.assertRaises(SystemExit) as raised):
                    verify_execution.main(argv)
                self.assertEqual(raised.exception.code, 0)
                self.assertEqual(json.loads(stdout.getvalue())["counts"]["total"], 0)

    def test_missing_run_dir_still_prints_help_and_exits_2(self):
        with _quiet(), contextlib.redirect_stdout(io.StringIO()), self.assertRaises(SystemExit) as raised:
            verify_execution.main([])
        self.assertEqual(raised.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
