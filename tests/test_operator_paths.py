#!/usr/bin/env python3
"""Operator paths for the code-repair scripts stay under the working, home or temp trees."""

import argparse
import os
import tempfile
import unittest
from pathlib import Path

from scripts import operator_paths


class Confinement(unittest.TestCase):
    def test_paths_under_the_operator_roots_resolve(self):
        for candidate in (os.getcwd(), str(Path.home() / "x"), tempfile.gettempdir() + "/y"):
            with self.subTest(candidate=candidate):
                self.assertEqual(operator_paths.operator_path(candidate), Path(os.path.realpath(candidate)))

    def test_paths_outside_every_root_are_refused_after_resolution(self):
        for candidate in ("/etc/passwd", os.getcwd() + "/../" * 12 + "etc/passwd"):
            with self.subTest(candidate=candidate), self.assertRaises(argparse.ArgumentTypeError):
                operator_paths.operator_path(candidate)


class CompatibilitySpelling(unittest.TestCase):
    """``scripts.operator_paths`` keeps resolving to the pipelines implementation."""

    def test_both_spellings_are_one_implementation(self):
        import pipelines.operator_paths as pipelines_operator_paths

        self.assertIs(operator_paths.operator_path, pipelines_operator_paths.operator_path)
        self.assertIs(operator_paths.operator_roots, pipelines_operator_paths.operator_roots)


if __name__ == "__main__":
    unittest.main()
