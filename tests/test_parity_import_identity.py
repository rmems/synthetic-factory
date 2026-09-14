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


if __name__ == "__main__":
    unittest.main()
