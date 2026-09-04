#!/usr/bin/env python3
"""Package-first import contracts for the split export modules."""

import unittest

from pipelines import export_contract
from pipelines import export_members
from pipelines import export_provenance
from pipelines import export_split


class ExportPackageImports(unittest.TestCase):
    def test_split_modules_share_the_packaged_export_contract_types(self):
        self.assertIs(export_split.ExportError, export_contract.ExportError)
        self.assertIs(export_split.ViewerRow, export_contract.ViewerRow)
        self.assertEqual(export_provenance.EXPORT_NAME, export_contract.EXPORT_NAME)
        self.assertIs(export_members.ExportError, export_contract.ExportError)


if __name__ == "__main__":
    unittest.main()
