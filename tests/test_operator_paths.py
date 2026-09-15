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

from pipelines.operator_paths import KIND_DESTINATION, confine, confine_named, operator_path, operator_roots
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
