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
    def _assert_loads_in_both_supported_modes(self, name):
        sys.path.insert(0, str(PIPELINES))
        try:
            direct = pipeline_import_catalog.load_direct(name)
        finally:
            sys.path.remove(str(PIPELINES))

        packaged = pipeline_import_catalog.load_package(name)
        self.assertIs(direct, packaged)

    def test_known_export_module_loads_in_both_supported_modes(self):
        self._assert_loads_in_both_supported_modes("export_split")

    def test_unknown_module_name_is_rejected_before_import(self):
        with self.assertRaisesRegex(ValueError, "not in the pipeline import catalog"):
            pipeline_import_catalog.load_package("operator_supplied.module")

    def test_curate_identity_boundaries_load_in_both_supported_modes(self):
        for name in ("curate_identity_output", "curate_identity_stages"):
            with self.subTest(name=name):
                self._assert_loads_in_both_supported_modes(name)


if __name__ == "__main__":
    unittest.main()
