"""The parity families bind both import names to one module object.

The CLI form (``pipelines/`` on ``sys.path``, ``import hardware_parity``) and
the package form (``from pipelines import hardware_parity``) must each work
alone, and in either order must bind one object per module, so an
``OracleUnavailable`` raised through one name is caught through the other.
The decomposition into sibling modules once left every sibling on a
bare-name-only prelude, so the package-form facades re-exported bare-name
classes: ``pipelines.nir_equivalence.GraphError`` was not
``pipelines.nir_equivalence_graph.GraphError``. Each form runs in a child
interpreter started with the ``spawn`` method (``tests/parity_import_probe.py``),
so nothing this process already imported can mask a failure.
"""

import multiprocessing
import sys
import unittest
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import parity_import_probe  # noqa: E402


class OneObjectAcrossImportForms(unittest.TestCase):
    def fresh(self, form: str) -> dict:
        context = multiprocessing.get_context("spawn")
        with ProcessPoolExecutor(max_workers=1, mp_context=context) as pool:
            return pool.submit(parity_import_probe.run_form, form).result(timeout=180)

    def test_the_probe_covers_every_flat_sibling(self):
        self.assertEqual(len(parity_import_probe.FLAT_SIBLINGS), 50)
        for facade in parity_import_probe.FACADES:
            self.assertIn(facade, parity_import_probe.FLAT_SIBLINGS)

    def test_the_cli_form_alone(self):
        self.assertEqual(self.fresh("cli"), {"facades": sorted(parity_import_probe.FACADES)})

    def test_the_package_form_alone_binds_every_sibling(self):
        report = self.fresh("package")
        self.assertEqual(report["facades"], sorted(parity_import_probe.FACADES))
        self.assertEqual(report["split_siblings"], [])

    def test_either_order_is_one_object_and_one_error_class(self):
        for form in ("cli_then_package", "package_then_cli"):
            with self.subTest(form=form):
                report = self.fresh(form)
                self.assertTrue(report["one_object"], report)
                self.assertEqual(
                    {name for name, same in report["one_error_class"].items() if not same},
                    set(),
                    report,
                )
                self.assertEqual(report["split_siblings"], [], report)


class InProcessPackageForm(unittest.TestCase):
    """The package form taken after the CLI form, in this very process.

    The spawned-interpreter probes above prove each order in isolation; this
    class takes the package branch of every sibling's prelude here, where the
    suite has already imported the CLI form, so the branch and the loaders it
    relies on run under the same process the coverage report is taken from.
    """

    @classmethod
    def setUpClass(cls):
        if str(parity_import_probe.REPO) not in sys.path:
            sys.path.append(str(parity_import_probe.REPO))
        sys.path.insert(0, str(parity_import_probe.PIPELINES))
        import importlib

        cls.bare = {name: importlib.import_module(name) for name in parity_import_probe.FACADES}
        cls.packaged = {
            name: importlib.import_module(f"pipelines.{name}")
            for name in parity_import_probe.FACADES
        }

    def test_each_facade_is_one_object_under_both_names(self):
        for name in parity_import_probe.FACADES:
            with self.subTest(facade=name):
                self.assertIs(self.packaged[name], self.bare[name])

    def test_every_sibling_binds_both_names_in_process(self):
        self.assertEqual(parity_import_probe._split_siblings(), [])

    def test_every_registered_loader_returns_the_bound_sibling(self):
        # _join_package_sibling reaches a sibling through
        # ``_load_package_sibling`` while the package child is still
        # initializing; the loader must hand back the same object the bare
        # name is bound to, never a second copy.
        import pipelines

        for name in parity_import_probe.FLAT_SIBLINGS:
            with self.subTest(sibling=name):
                self.assertIn(name, pipelines._PACKAGE_SIBLING_NAMES)
                loaded = pipelines._load_package_sibling(name)
                self.assertIs(loaded, sys.modules[name])
                self.assertIs(loaded, sys.modules[f"pipelines.{name}"])


if __name__ == "__main__":
    unittest.main()
