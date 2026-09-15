#!/usr/bin/env python3
"""Operator paths stay under the working, home or temp trees and refuse unsafe leaves."""

import argparse
import contextlib
import io
import os
import stat
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from pipelines.operator_paths import (
    KIND_DESTINATION,
    _under_root,
    confine,
    confine_named,
    operator_path,
    operator_roots,
)
from scripts import operator_paths as scripts_operator_paths


def _fifo(path: Path) -> Path:
    os.mkfifo(path)
    return path


class Confinement(unittest.TestCase):
    def test_paths_under_the_operator_roots_resolve(self):
        for candidate in (os.getcwd(), str(Path.home() / "x"), tempfile.gettempdir() + "/y"):
            with self.subTest(candidate=candidate):
                self.assertEqual(
                    operator_path(candidate),
                    Path(os.path.realpath(candidate)),
                )

    def test_paths_outside_every_root_are_refused_after_resolution(self):
        for candidate in ("/etc/passwd", os.getcwd() + "/../" * 12 + "etc/passwd"):
            with self.subTest(candidate=candidate), self.assertRaises(
                argparse.ArgumentTypeError
            ) as raised:
                operator_path(candidate)
            self.assertIn("outside the working, home and temp trees", str(raised.exception))
            self.assertNotIn("passwd", str(raised.exception))
            self.assertNotIn(str(Path.home()), str(raised.exception))
            self.assertNotIn(tempfile.gettempdir(), str(raised.exception))

    def test_refusals_name_the_argument_without_the_typed_path(self):
        with self.assertRaises(argparse.ArgumentTypeError) as raised:
            operator_path("/etc/passwd", argument="input")
        self.assertEqual(
            str(raised.exception),
            "input: the path lies outside the working, home and temp trees",
        )

    def test_a_filesystem_root_operator_root_accepts_absolute_paths(self):
        candidate = os.path.join(os.getcwd(), "input.jsonl")
        self.assertTrue(_under_root("/opt/factory/input.jsonl", "/"))
        self.assertTrue(_under_root("/opt/factory/input.jsonl", "/opt/factory/"))
        self.assertFalse(_under_root("/etc/passwd", "/opt/factory"))
        self.assertFalse(_under_root("/opt/factory/input.jsonl", "factory"))
        with mock.patch(
            "pipelines.operator_paths.operator_roots", return_value=("/",)
        ):
            self.assertEqual(
                operator_path(candidate, argument="input"),
                Path(os.path.realpath(candidate)),
            )

    def test_non_pathlike_values_and_unsupported_kinds_are_refused(self):
        with self.assertRaises(argparse.ArgumentTypeError) as raised:
            operator_path(object(), argument="input")
        self.assertEqual(str(raised.exception), "input: the path is empty")
        with self.assertRaises(argparse.ArgumentTypeError) as raised:
            operator_path(".", argument="input", kind="alias")
        self.assertEqual(str(raised.exception), "input: the path kind is not supported")

    def test_bytes_paths_under_an_operator_root_still_resolve(self):
        with tempfile.TemporaryDirectory() as td:
            encoded = os.fsencode(os.path.join(td, "input.jsonl"))
            self.assertEqual(
                operator_path(encoded, argument="input"),
                Path(os.path.realpath(os.fsdecode(encoded))),
            )

    def test_empty_paths_are_refused(self):
        for candidate in ("", "   ", "\n"):
            with self.subTest(candidate=repr(candidate)), self.assertRaises(
                argparse.ArgumentTypeError
            ) as raised:
                operator_path(candidate, argument="source")
            self.assertEqual(str(raised.exception), "source: the path is empty")


class LeafSafety(unittest.TestCase):
    def test_input_and_output_symlinks_are_refused(self):
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "real.jsonl"
            target.write_text("{}\n", encoding="utf-8")
            link = Path(td) / "linked.jsonl"
            link.symlink_to(target)
            with self.assertRaises(argparse.ArgumentTypeError) as raised:
                operator_path(link, argument="--output")
            self.assertEqual(str(raised.exception), "--output: the path is a symlink")
            self.assertNotIn(str(link), str(raised.exception))

    def test_dangling_symlinks_are_refused(self):
        with tempfile.TemporaryDirectory() as td:
            link = Path(td) / "dangling"
            link.symlink_to(Path(td) / "missing-target")
            with self.assertRaises(argparse.ArgumentTypeError) as raised:
                operator_path(link, argument="input")
            self.assertEqual(str(raised.exception), "input: the path is a dangling symlink")

    def test_an_unreadable_leaf_is_refused(self):
        with tempfile.TemporaryDirectory() as td:
            leaf = Path(td) / "sealed"
            leaf.write_text("keep\n", encoding="utf-8")
            real_lstat = os.lstat
            hits = {"n": 0}

            def lstat(path, *args, **kwargs):
                target = os.fsdecode(os.fspath(path))
                if os.path.normpath(target) == os.path.normpath(leaf):
                    hits["n"] += 1
                    if hits["n"] >= 2:
                        raise OSError("cannot inspect")
                return real_lstat(path, *args, **kwargs)

            with (
                mock.patch("pipelines.operator_paths.os.lstat", side_effect=lstat),
                self.assertRaises(argparse.ArgumentTypeError) as raised,
            ):
                operator_path(leaf, argument="input")
            self.assertEqual(str(raised.exception), "input: the path cannot be inspected")

    def test_fifo_and_device_leaves_are_refused(self):
        with tempfile.TemporaryDirectory() as td:
            fifo = _fifo(Path(td) / "named-pipe")
            with self.assertRaises(argparse.ArgumentTypeError) as raised:
                operator_path(fifo, argument="input")
            self.assertEqual(str(raised.exception), "input: the path is a special file")
        with self.assertRaises(argparse.ArgumentTypeError) as raised:
            operator_path("/dev/null", argument="--output")
        self.assertEqual(str(raised.exception), "--output: the path is a special file")
        self.assertTrue(stat.S_ISCHR(os.lstat("/dev/null").st_mode))

    def test_destination_replacement_is_refused_after_the_path_is_confined(self):
        with tempfile.TemporaryDirectory() as td:
            existing = Path(td) / "already.jsonl"
            existing.write_text("keep\n", encoding="utf-8")
            with self.assertRaises(argparse.ArgumentTypeError) as raised:
                operator_path(
                    existing, argument="--output", kind=KIND_DESTINATION
                )
            self.assertEqual(str(raised.exception), "--output: the destination already exists")
            self.assertEqual(existing.read_text(encoding="utf-8"), "keep\n")

    def test_a_missing_prefix_before_dotdot_cannot_skip_leaf_guards(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            real = root / "real.jsonl"
            real.write_text("keep\n", encoding="utf-8")
            link = root / "linked.jsonl"
            link.symlink_to(real)
            dangling = root / "dangling.jsonl"
            dangling.symlink_to(root / "missing-target")
            _fifo(root / "named-pipe")
            missing = root / "missing-dir"
            cases = (
                (missing / ".." / "linked.jsonl", "the path is a symlink"),
                (missing / ".." / "dangling.jsonl", "the path is a dangling symlink"),
                (missing / ".." / "named-pipe", "the path is a special file"),
            )
            for candidate, reason in cases:
                with self.subTest(reason=reason):
                    with self.assertRaises(argparse.ArgumentTypeError) as raised:
                        operator_path(candidate, argument="input")
                    self.assertEqual(str(raised.exception), f"input: {reason}")
            existing = missing / ".." / "real.jsonl"
            with self.assertRaises(argparse.ArgumentTypeError) as raised:
                operator_path(existing, argument="--output", kind=KIND_DESTINATION)
            self.assertEqual(str(raised.exception), "--output: the destination already exists")
            self.assertEqual(real.read_text(encoding="utf-8"), "keep\n")
            fresh = missing / ".." / "new.jsonl"
            confined = operator_path(fresh, argument="--output", kind=KIND_DESTINATION)
            self.assertEqual(confined, Path(os.path.realpath(root / "new.jsonl")))
            self.assertFalse(fresh.exists())

    def test_dotdot_through_a_symlink_parent_still_refuses_the_real_leaf(self):
        with tempfile.TemporaryDirectory() as td, tempfile.TemporaryDirectory() as outside:
            targetdir = Path(outside) / "targetdir"
            targetdir.mkdir()
            fifo = _fifo(Path(outside) / "named-pipe")
            (Path(td) / "symdir").symlink_to(targetdir)
            spelling = Path(td) / "symdir" / ".." / fifo.name
            self.assertFalse(os.path.lexists(os.path.normpath(spelling)))
            with self.assertRaises(argparse.ArgumentTypeError) as raised:
                operator_path(spelling, argument="input")
            self.assertEqual(str(raised.exception), "input: the path is a special file")

    def test_a_new_destination_under_temp_still_resolves(self):
        with tempfile.TemporaryDirectory() as td:
            destination = Path(td) / "new.jsonl"
            confined = operator_path(
                destination, argument="--output", kind=KIND_DESTINATION
            )
            self.assertEqual(confined, Path(os.path.realpath(destination)))
            self.assertFalse(destination.exists())


class ConfineHelper(unittest.TestCase):
    def test_absent_values_stay_none_and_parser_errors_name_the_argument(self):
        parser = argparse.ArgumentParser(prog="tool")
        self.assertIsNone(confine(parser, None, argument="input"))
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr), self.assertRaises(SystemExit) as raised:
            confine(parser, "/etc/passwd", argument="input")
        self.assertEqual(raised.exception.code, 2)
        self.assertIn("error: input:", stderr.getvalue())
        self.assertNotIn("passwd", stderr.getvalue())

    def test_confine_named_applies_destination_kind(self):
        parser = argparse.ArgumentParser(prog="tool")
        with tempfile.TemporaryDirectory() as td:
            existing = Path(td) / "already.jsonl"
            existing.write_text("keep\n", encoding="utf-8")
            named = argparse.Namespace(source=td, output=str(existing))
            arguments = {"source": "source", "output": "--output"}
            destinations = frozenset({"output"})
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr), self.assertRaises(SystemExit) as raised:
                confine_named(parser, named, arguments, destinations)
            self.assertEqual(raised.exception.code, 2)
            self.assertIn("--output: the destination already exists", stderr.getvalue())
            self.assertEqual(existing.read_text(encoding="utf-8"), "keep\n")


class CompatibilitySpelling(unittest.TestCase):
    """``scripts.operator_paths`` keeps resolving to the pipelines implementation."""

    def test_both_spellings_are_one_implementation(self):
        self.assertIs(scripts_operator_paths.operator_path, operator_path)
        self.assertIs(scripts_operator_paths.operator_roots, operator_roots)


if __name__ == "__main__":
    unittest.main()
