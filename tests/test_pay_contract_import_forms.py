#!/usr/bin/env python3
"""Both import branches of the pay contract bind the same names to the same objects."""

import importlib.util
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PIPELINES = REPO / "pipelines"
sys.path.insert(0, str(PIPELINES))
if str(REPO) not in sys.path:
    sys.path.append(str(REPO))

import exact_json  # noqa: E402
from oracle_grounded import refusals  # noqa: E402
from pay import _contract as flat_contract  # noqa: E402

PACKAGE_NAME = "pipelines.pay._contract"


def _execute_package_spelling():
    """Run the contract's source under its package name, leaving ``sys.modules`` as found.

    The package branch may load ``pipelines`` and package-name aliases of modules
    already loaded flat; those entries are dropped again so no later test sees them.
    """

    spec = importlib.util.spec_from_file_location(PACKAGE_NAME, PIPELINES / "pay" / "_contract.py")
    module = importlib.util.module_from_spec(spec)
    found = dict(sys.modules)
    sys.modules[PACKAGE_NAME] = module
    try:
        spec.loader.exec_module(module)
    finally:
        for name in set(sys.modules) - set(found):
            del sys.modules[name]
        sys.modules.update(found)
    return module


def _public_names(module):
    return {name for name in vars(module) if not name.startswith("__")}


class PayContractImportForms(unittest.TestCase):
    def test_package_branch_imports_what_the_flat_branch_imports(self):
        packaged = _execute_package_spelling()
        self.assertEqual(packaged.__package__, "pipelines.pay")
        self.assertEqual(_public_names(packaged), _public_names(flat_contract))
        # The exact-JSON decimal class and the refusal base keep one identity across spellings,
        # so a refusal raised through either form is caught through the other.
        self.assertIs(packaged.ExactJSONFloat, exact_json.ExactJSONFloat)
        self.assertIs(packaged.refusals, refusals)
        self.assertIs(packaged.bind_import_twin, flat_contract.bind_import_twin)
        self.assertIs(packaged.PayRefusal.__base__, flat_contract.PayRefusal.__base__)
        self.assertEqual(packaged.FINDING_CODE_SET, flat_contract.FINDING_CODE_SET)
        self.assertIs(sys.modules[PACKAGE_NAME], flat_contract)


if __name__ == "__main__":
    unittest.main()
