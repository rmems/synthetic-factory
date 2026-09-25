#!/usr/bin/env python3
"""``pipelines.oracle_grounded.__all__`` names only submodules that exist.

The six family names main once carried as phantoms -- canon, families,
generators, oracles, record, sim -- are real submodules now that the
oracle-grounded family stack has landed, so they exist on disk but stay off
the star-import surface, which remains exactly the two declared names. The
package's two import names stay one object; a contract error raised through
one spelling is caught through the other; an unknown name still fails to
import.
"""

from __future__ import annotations

import ast
import importlib
import importlib.util
import multiprocessing
import sys
import unittest
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import oracle_grounded_package_probe as probe  # noqa: E402

DECLARED_NAMES = probe.DECLARED_NAMES


class PackageStarImportSurface(unittest.TestCase):
    def setUp(self):
        self.package = importlib.import_module("pipelines.oracle_grounded")
        here = Path(self.package.__file__).parent
        self.submodules = {path.stem for path in here.glob("*.py")} - {"__init__"}

    def test_every_declared_name_is_a_real_submodule(self):
        undefined = [name for name in self.package.__all__ if name not in self.submodules]

        self.assertEqual(undefined, [])

    def test_the_declared_surface_is_exactly_the_two_existing_names(self):
        self.assertEqual(tuple(self.package.__all__), DECLARED_NAMES)

    GRADUATED_NAMES = ("canon", "families", "generators", "oracles", "record", "sim")

    def test_the_graduated_family_modules_exist_but_stay_off_the_star_surface(self):
        for name in self.GRADUATED_NAMES:
            with self.subTest(name=name):
                self.assertIn(name, self.submodules)
                self.assertNotIn(name, self.package.__all__)

    def test_every_declared_name_binds_the_submodule_a_star_import_would_take(self):
        """What ``import *`` does for a package: import the name, then bind it.

        The old ``__all__`` failed at the binding step with ``AttributeError``,
        so assert the binding rather than running an ``exec``.
        """

        for name in self.package.__all__:
            with self.subTest(name=name):
                module = importlib.import_module(f"pipelines.oracle_grounded.{name}")

                self.assertIs(getattr(self.package, name), module)

    def test_an_unknown_name_fails_to_import_instead_of_succeeding(self):
        """An unknown name must resolve to nothing, not to some other module.

        ``find_spec`` settles existence without executing a module to find
        out; the literal import below keeps the ``ModuleNotFoundError`` half
        of the contract pinned directly.
        """

        self.assertIsNone(
            importlib.util.find_spec("pipelines.oracle_grounded.no_such_module")
        )

        with self.assertRaises(ModuleNotFoundError):
            importlib.import_module("pipelines.oracle_grounded.no_such_module")

    def test_explicit_sibling_imports_still_resolve(self):
        for name in ("envelope", "import_twins", "fault_oracle", "distill_contract"):
            with self.subTest(name=name):
                module = importlib.import_module(f"pipelines.oracle_grounded.{name}")
                self.assertEqual(module.__name__.rsplit(".", 1)[-1], name)


def _finally_bodies(source: str) -> list[ast.Module]:
    """Every ``finally:`` block in ``source``, as walkable modules."""

    return [
        ast.Module(body=node.finalbody, type_ignores=[])
        for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.Try)
    ]


def _finally_jumps(source: str) -> list[str]:
    """Jump statements inside a ``finally:``, which would suppress a primary outcome."""

    return [
        type(statement).__name__
        for body in _finally_bodies(source)
        for statement in ast.walk(body)
        if isinstance(statement, (ast.Return, ast.Break, ast.Continue))
    ]


class NoFinallyJumps(unittest.TestCase):
    def test_package_init_has_no_jump_inside_a_finally_block(self):
        source = Path(importlib.import_module("pipelines.oracle_grounded").__file__).read_text(
            encoding="utf-8"
        )
        self.assertEqual(_finally_jumps(source), [])


class SupportedImportForms(unittest.TestCase):
    """Both documented import forms work alone and together, in a fresh interpreter."""

    def fresh(self, form: str) -> dict:
        context = multiprocessing.get_context("spawn")
        with ProcessPoolExecutor(max_workers=1, mp_context=context) as pool:
            return pool.submit(probe.run_form, form).result(timeout=120)

    def test_the_cli_form_alone_binds_its_twin(self):
        report = self.fresh("cli")
        self.assertEqual(tuple(report["all"]), DECLARED_NAMES)
        self.assertTrue(report["twin_bound"], report)
        self.assertEqual(report["phantoms"], {})

    def test_the_package_form_alone_binds_its_twin(self):
        report = self.fresh("package")
        self.assertEqual(tuple(report["all"]), DECLARED_NAMES)
        self.assertTrue(report["twin_bound"], report)
        self.assertEqual(report["phantoms"], {})

    def test_both_orders_bind_one_object_and_keep_refusals_distinguishable(self):
        for form in ("cli_then_package", "package_then_cli"):
            with self.subTest(form=form):
                report = self.fresh(form)
                self.assertTrue(report["one_object"], report)
                self.assertTrue(report["one_refusal_class"], report)
                self.assertTrue(report["one_contract_error"], report)
                self.assertEqual(report["seed_outcome"], "contract_error")
                self.assertEqual(report["packaged_seed_caught_through_flat"], "caught_through_flat")
                self.assertEqual(report["undeclared_code"], "lookup_error")
                self.assertEqual(tuple(report["all"]), DECLARED_NAMES)
                self.assertEqual(report["declared_bound"], {name: True for name in DECLARED_NAMES})

    def test_both_orders_keep_the_dotted_attribute_chain_usable(self):
        """Binding the twin must not cost ``import pipelines.oracle_grounded.rng``.

        Registering the CLI module under its packaged name lets CPython skip the
        child load, which also skips setting the child on the parent package.
        ``pipelines/__init__`` re-attaches preloaded children so the dotted form
        keeps resolving.
        """

        for form in ("cli_then_package", "package_then_cli"):
            with self.subTest(form=form):
                report = self.fresh(form)
                # One object serves both spellings, so whichever form loaded the
                # submodule first owns ``__name__``. Either is a resolved chain;
                # an ``AttributeError`` string is not.
                self.assertIn(
                    report["dotted_attribute_chain"],
                    ("oracle_grounded.rng", "pipelines.oracle_grounded.rng"),
                    report,
                )


if __name__ == "__main__":
    unittest.main()
