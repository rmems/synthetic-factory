#!/usr/bin/env python3
"""Contracts for the literal-bound pipeline import catalog."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

if __package__:
    from . import pipeline_import_catalog
else:
    import pipeline_import_catalog


REPO = Path(__file__).resolve().parents[1]
PIPELINES = REPO / "pipelines"


class PipelineImportCatalogContracts(unittest.TestCase):
    def test_known_export_module_loads_in_both_supported_modes(self):
        sys.path.insert(0, str(PIPELINES))
        try:
            direct = pipeline_import_catalog.load_direct("export_split")
        finally:
            sys.path.remove(str(PIPELINES))

        packaged = pipeline_import_catalog.load_package("export_split")
        self.assertIs(direct, packaged)

    def test_unknown_module_name_is_rejected_before_import(self):
        with self.assertRaisesRegex(ValueError, "not in the pipeline import catalog"):
            pipeline_import_catalog.load_package("operator_supplied.module")


if __name__ == "__main__":
    unittest.main()
