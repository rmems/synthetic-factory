#!/usr/bin/env python3
"""Both import spellings of every family module are one object, in any order."""

import multiprocessing
import sys
import unittest
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import code_repair_import_probe  # noqa: E402
from code_repair_test_support import FAMILY_MODULES, REPO, cli, vocabulary as cv  # noqa: E402


class InProcess(unittest.TestCase):
    def test_every_family_module_is_one_object_under_both_spellings(self):
        if str(REPO) not in sys.path:
            sys.path.append(str(REPO))
        from pipelines.code_repair import cli as packaged

        self.assertIs(packaged, cli)
        for name in FAMILY_MODULES:
            with self.subTest(name=name):
                self.assertIs(sys.modules[f"code_repair.{name}"], sys.modules[f"pipelines.code_repair.{name}"])
        self.assertEqual(code_repair_import_probe.MODULES, FAMILY_MODULES)


class FreshInterpreter(unittest.TestCase):
    def fresh(self, form):
        context = multiprocessing.get_context("spawn")
        with ProcessPoolExecutor(max_workers=1, mp_context=context) as pool:
            return pool.submit(code_repair_import_probe.run_form, form).result(timeout=120)

    def test_each_form_alone(self):
        self.assertEqual(self.fresh("cli"), {"family": cv.FAMILY})
        self.assertEqual(self.fresh("package"), {"family": cv.FAMILY})

    def test_both_orders_bind_one_object_and_one_refusal_class(self):
        for form in ("cli_then_package", "package_then_cli"):
            with self.subTest(form=form):
                report = self.fresh(form)
                self.assertTrue(report["one_object"], report)
                self.assertTrue(report["one_refusal_class"], report)
                self.assertEqual(report["split_modules"], [])


if __name__ == "__main__":
    unittest.main()
