#!/usr/bin/env python3
"""round_txn and curate_identity confine operator paths right after parsing (S8707, B2 of #211).

Each CLI refuses a path outside the working, home and temp trees with
argparse's own error shape (exit 2) before any filesystem sink runs, and keeps
working for paths under a temporary directory. The library entry points
underneath keep their signatures; only ``main`` changes.
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

import curate_identity  # noqa: E402
import round_txn  # noqa: E402

REFUSAL = "outside the working, home and temp trees"
OUTSIDE = ("/etc/passwd", "../" * 12 + "etc/passwd")
TXN_SINKS = ("frontier_status", "reserve", "publish", "abort", "migrate_preference_v1_markers")


class _FunnelCase(unittest.TestCase):
    """Shared assertions for the two post-parse funnels."""

    def assertRefused(self, call, *args):
        """``call(*args)`` exits 2 with argparse's refusal; args are bound here, not in a closure."""
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr), self.assertRaises(SystemExit) as raised:
            call(*args)
        self.assertEqual(raised.exception.code, 2)
        self.assertIn(REFUSAL, stderr.getvalue())
        self.assertIn("error:", stderr.getvalue())


class RoundTxnFunnel(_FunnelCase):
    parser = argparse.ArgumentParser(prog="round_txn.py")

    def test_factory_dir_is_refused_outside_the_operator_trees(self):
        for candidate in OUTSIDE:
            with self.subTest(candidate=candidate):
                self.assertRefused(
                    round_txn._confined_factory_dir,
                    self.parser,
                    SimpleNamespace(factory_dir=candidate),
                )

    def test_factory_dir_under_the_operator_trees_resolves(self):
        with tempfile.TemporaryDirectory() as td:
            confined = round_txn._confined_factory_dir(
                self.parser, SimpleNamespace(factory_dir=td)
            )
        self.assertEqual(confined, Path(os.path.realpath(td)))

    def test_a_missing_factory_dir_is_refused_as_empty(self):
        stderr = io.StringIO()
        args = SimpleNamespace(factory_dir=None)
        with contextlib.redirect_stderr(stderr), self.assertRaises(SystemExit) as raised:
            round_txn._confined_factory_dir(self.parser, args)
        self.assertEqual(raised.exception.code, 2)
        self.assertIn("factory_dir: the path is empty", stderr.getvalue())

    def test_parse_args_still_returns_the_namespace(self):
        args = round_txn.parse_args(["frontier", "some-dir"])
        self.assertEqual(args.command, "frontier")
        self.assertEqual(args.factory_dir, "some-dir")


class RoundTxnCli(_FunnelCase):
    def test_every_subcommand_refuses_before_its_sink_runs(self):
        commands = {
            "frontier": ["frontier", "{bad}"],
            "migrate-preference-v1": ["migrate-preference-v1", "{bad}"],
            "reserve": ["reserve", "{bad}", "--round", "1", "--expected", "1"],
            "publish": ["publish", "{bad}", "--round", "1", "--token", "t"],
            "abort": ["abort", "{bad}", "--round", "1", "--token", "t"],
        }
        for label, argv in commands.items():
            for bad in OUTSIDE:
                with self.subTest(command=label, bad=bad), contextlib.ExitStack() as stack:
                    mocks = {
                        name: stack.enter_context(mock.patch.object(round_txn, name))
                        for name in TXN_SINKS
                    }
                    self.assertRefused(round_txn.main, [a.replace("{bad}", bad) for a in argv])
                    for sink in mocks.values():
                        sink.assert_not_called()

    def test_frontier_under_a_temporary_directory_still_works(self):
        with tempfile.TemporaryDirectory() as td:
            factory = Path(td) / "lane"
            factory.mkdir()
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                self.assertEqual(round_txn.main(["frontier", str(factory)]), 0)
        result = json.loads(stdout.getvalue())
        self.assertEqual(result["factory"], "lane")
        self.assertEqual(result["mode"], "legacy")
        self.assertEqual(result["next_round"], 1)

    def test_transaction_errors_keep_exit_1_after_the_funnel(self):
        with tempfile.TemporaryDirectory() as td:
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                self.assertEqual(round_txn.main(["frontier", os.path.join(td, "absent")]), 1)
        self.assertIn("ERROR: not a factory directory", stderr.getvalue())


class IdentityFunnel(_FunnelCase):
    parser = argparse.ArgumentParser(prog="curate_identity.py")

    def test_each_path_argument_is_refused_outside_the_operator_trees(self):
        with tempfile.TemporaryDirectory() as td:
            for candidate in OUTSIDE:
                with self.subTest(name="source", candidate=candidate):
                    self.assertRefused(
                        curate_identity._inputs,
                        self.parser,
                        SimpleNamespace(source=Path(candidate), out=None),
                    )
                with self.subTest(name="out", candidate=candidate):
                    self.assertRefused(
                        curate_identity._inputs,
                        self.parser,
                        SimpleNamespace(source=Path(td), out=Path(candidate)),
                    )

    def test_paths_under_the_operator_trees_resolve_and_absent_out_stays_none(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(os.path.realpath(td))
            paths = curate_identity._inputs(
                self.parser, SimpleNamespace(source=Path(td) / "src", out=None)
            )
            self.assertEqual(paths, curate_identity.Inputs(source=root / "src", out=None))
            paths = curate_identity._inputs(
                self.parser, SimpleNamespace(source=Path(td) / "src", out=Path(td) / "dest")
            )
        self.assertEqual(paths.out, root / "dest")


class IdentityCli(_FunnelCase):
    def test_each_argument_refuses_before_its_sink_runs(self):
        commands = {"source": ["{bad}"], "--out": ["src", "--out", "{bad}"]}
        for label, argv in commands.items():
            for bad in OUTSIDE:
                with (
                    self.subTest(argument=label, bad=bad),
                    mock.patch.object(curate_identity, "iter_source_records") as reader,
                    mock.patch.object(curate_identity, "write_run") as writer,
                ):
                    self.assertRefused(
                        curate_identity.main, [a.replace("{bad}", bad) for a in argv]
                    )
                    reader.assert_not_called()
                    writer.assert_not_called()

    def test_paths_under_a_temporary_directory_reach_the_sinks(self):
        with tempfile.TemporaryDirectory() as td:
            missing = Path(td) / "missing-source"
            dest = Path(td) / "dest"
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                self.assertEqual(curate_identity.main([str(missing), "--out", str(dest)]), 1)
            self.assertIn("source does not exist", stderr.getvalue())
            self.assertFalse(dest.exists())
            source = Path(td) / "empty.jsonl"
            source.write_text("", encoding="utf-8")
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                self.assertEqual(curate_identity.main([str(source)]), 0)
        summary = json.loads(stdout.getvalue())
        self.assertEqual(summary["records"], 0)
        self.assertNotIn("source", summary)


if __name__ == "__main__":
    unittest.main()
