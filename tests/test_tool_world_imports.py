#!/usr/bin/env python3
"""Both import spellings of every tool-world module are one object, in any order."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import tool_world_import_probe as probe
import tool_world_test_support as support

REPO = support.REPO
PACKAGE_DIR = support.PIPELINES / probe.PACKAGE


def discovered_modules() -> frozenset[str]:
    """Every module file under the package, named the way the probe lists them."""
    names = set()
    for path in PACKAGE_DIR.rglob("*.py"):
        if "__pycache__" in path.parts:
            continue
        parts = list(path.relative_to(PACKAGE_DIR).with_suffix("").parts)
        if parts[-1] == "__init__":
            parts.pop()
        if parts:
            names.add(".".join(parts))
    return frozenset(names)


class InProcess(unittest.TestCase):
    def setUp(self):
        if str(REPO) not in sys.path:
            sys.path.append(str(REPO))

    def test_probe_lists_every_module_file_in_the_package(self):
        self.assertEqual(frozenset(probe.MODULES), discovered_modules())
        self.assertEqual(len(set(probe.MODULES)), len(probe.MODULES))

    def test_every_module_is_one_object_under_both_spellings(self):
        flat, packaged = probe.import_flat(), probe.import_packaged()
        self.assertEqual(set(flat), {"", *probe.MODULES})
        self.assertEqual(set(packaged), set(flat))
        for name in ("", *probe.MODULES):
            flat_name, packaged_name = probe.spellings(name)
            with self.subTest(module=flat_name):
                self.assertIs(flat[name], packaged[name])
                self.assertIs(sys.modules[flat_name], flat[name])
                self.assertIs(sys.modules[packaged_name], flat[name])

    def test_the_refusal_class_and_the_cli_entry_are_one_object(self):
        from pipelines.tool_world import cli as packaged_cli
        from pipelines.tool_world import vocabulary as packaged_cv

        import tool_world_cli as entry
        from tool_world import cli as flat_cli

        self.assertIs(packaged_cv.ToolWorldRefusal, support.cv.ToolWorldRefusal)
        self.assertIs(packaged_cli.run, flat_cli.run)
        self.assertIs(entry.main, flat_cli.run)


class FreshInterpreter(unittest.TestCase):
    @staticmethod
    def fresh(form):
        return probe.in_fresh_interpreter(probe.run_form, form)

    def test_each_form_alone(self):
        self.assertEqual(self.fresh("cli"), {"family": support.cv.FAMILY})
        self.assertEqual(self.fresh("package"), {"family": support.cv.FAMILY})

    def test_both_orders_bind_one_object_and_one_refusal_class(self):
        for form in ("cli_then_package", "package_then_cli"):
            with self.subTest(form=form):
                report = self.fresh(form)
                self.assertTrue(report["one_object"], report)
                self.assertTrue(report["one_refusal_class"], report)
                self.assertEqual(report["split_modules"], [])


if __name__ == "__main__":
    unittest.main()
