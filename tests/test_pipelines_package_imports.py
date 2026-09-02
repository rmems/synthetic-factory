#!/usr/bin/env python3
"""Core package/direct-import compatibility regressions."""

from __future__ import annotations

import sys
import unittest

if __package__:
    from . import pipeline_import_catalog
    from .pipeline_import_test_support import (
        PIPELINES,
        clean_package_imports,
        repository_pipeline_module,
    )
else:
    import pipeline_import_catalog
    from pipeline_import_test_support import (
        PIPELINES,
        clean_package_imports,
        repository_pipeline_module,
    )


REFACTORED_FACADES = (
    "census",
    "check_records",
    "coding_constants",
    "coding_verify",
    "coding_verify_manifest",
    "coding_verify_steps",
    "compose_contract",
    "compose_curated",
    "compose_mill",
    "compose_trajectory",
    "curate_agentic",
    "curate_agentic_output",
    "curate_agentic_shapes",
    "curate_coding",
    "curate_identity",
    "curate_preferences",
    "curate_rewards",
    "curate_trajectory_preferences",
    "leftover_mill",
    "mill_evidence",
    "mill_family",
    "mill_ownership",
    "mill_resolution",
    "preference_audit",
    "preference_audit_diff",
    "preference_context",
    "preference_model",
    "preference_reconcile",
    "preference_record",
    "preference_repair",
    "preference_writer",
    "reward_calibration",
    "reward_document",
    "reward_mapping",
    "reward_ontology",
    "reward_policy",
    "reward_units",
    "reward_vocabulary",
    "round_txn",
    "round_txn_preference",
    "round_txn_raster",
    "training_audit_mill",
    "training_audit_report",
    "trajectory_pair_curation",
    "trajectory_pair_gate",
    "trajectory_pair_shape",
    "trajectory_pair_vocabulary",
)


class PipelinesPackageImports(unittest.TestCase):
    def test_existing_facades_import_cleanly_from_the_package(self):
        for name in ("compose_curated", "compose_destination", "training_audit"):
            with self.subTest(name=name):
                with clean_package_imports():
                    self.assertNotIn(str(PIPELINES), sys.path)
                    module = pipeline_import_catalog.load_package(name)
                    self.assertEqual(module.__name__, f"pipelines.{name}")
                    self.assertNotIn(str(PIPELINES), sys.path)

    def test_export_contract_and_viewer_import_from_a_clean_package(self):
        """Package consumers need the export contract without CLI-path leakage."""

        with clean_package_imports():
            self.assertNotIn(str(PIPELINES), sys.path)
            contract = pipeline_import_catalog.load_package("export_contract")
            viewer = pipeline_import_catalog.load_package("export_viewer")
            self.assertIs(viewer.ExportError, contract.ExportError)
            self.assertIs(viewer.ViewerRow, contract.ViewerRow)
            self.assertNotIn(str(PIPELINES), sys.path)

    def test_refactored_facades_support_package_and_direct_import_modes(self):
        """Every refactored facade remains usable through both supported modes."""

        with clean_package_imports():
            self.assertNotIn(str(PIPELINES), sys.path)
            packaged = {
                name: pipeline_import_catalog.load_package(name) for name in REFACTORED_FACADES
            }
            for name, module in packaged.items():
                with self.subTest(mode="package", name=name):
                    self.assertEqual(module.__package__, "pipelines")
                    self.assertTrue(repository_pipeline_module(module))
            self.assertNotIn(str(PIPELINES), sys.path)

        with clean_package_imports():
            sys.path.insert(0, str(PIPELINES))
            try:
                direct = {
                    name: pipeline_import_catalog.load_direct(name) for name in REFACTORED_FACADES
                }
            finally:
                sys.path.remove(str(PIPELINES))
            for name, module in direct.items():
                with self.subTest(mode="direct", name=name):
                    self.assertEqual(module.__package__, "")
                    self.assertTrue(repository_pipeline_module(module))


if __name__ == "__main__":
    unittest.main()
