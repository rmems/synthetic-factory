#!/usr/bin/env python3
"""``pipelines.oracle_grounded.__all__`` names only submodules that exist.

Six of the eight names it carried -- canon, families, generators, oracles,
record, sim -- were the layout of an abandoned branch, so
``from pipelines.oracle_grounded import *`` raised ``AttributeError`` on the
first of them (SonarCloud python:S5807, six occurrences).
"""

from __future__ import annotations

import importlib
import unittest
from pathlib import Path


class PackageStarImportSurface(unittest.TestCase):
    def setUp(self):
        self.package = importlib.import_module("pipelines.oracle_grounded")
        here = Path(self.package.__file__).parent
        self.submodules = {path.stem for path in here.glob("*.py")} - {"__init__"}

    def test_every_declared_name_is_a_real_submodule(self):
        undefined = [name for name in self.package.__all__ if name not in self.submodules]

        self.assertEqual(undefined, [])

    def test_every_declared_name_binds_the_submodule_a_star_import_would_take(self):
        """What ``import *`` does for a package: import the name, then bind it.

        The old ``__all__`` failed at the binding step with ``AttributeError``,
        so assert the binding rather than running an ``exec``.
        """

        for name in self.package.__all__:
            with self.subTest(name=name):
                module = importlib.import_module(f"pipelines.oracle_grounded.{name}")

                self.assertIs(getattr(self.package, name), module)


if __name__ == "__main__":
    unittest.main()
