#!/usr/bin/env python3
"""Bridge, provenance, and exact-JSON package identity contracts."""

from __future__ import annotations

import sys
import unittest
from types import ModuleType
from unittest import mock

if __package__:
    from . import pipeline_import_catalog
    from .pipeline_import_test_support import (
        PIPELINES,
        REPO,
        direct_pipeline_path,
        isolated_pipeline_modules,
    )
else:
    import pipeline_import_catalog
    from pipeline_import_test_support import (
        PIPELINES,
        REPO,
        direct_pipeline_path,
        isolated_pipeline_modules,
    )


VALIDATE_PROVENANCE_MODULES = (
    "validate_run_provenance",
    "validate_run_spikes",
)


def _validate_provenance_pair(first: str):
    if first == "direct":
        with direct_pipeline_path():
            direct = pipeline_import_catalog.load_direct("validate_run_provenance")
        packaged = pipeline_import_catalog.load_package("validate_run_provenance")
    else:
        packaged = pipeline_import_catalog.load_package("validate_run_provenance")
        with direct_pipeline_path():
            direct = pipeline_import_catalog.load_direct("validate_run_provenance")
    return direct, packaged


class PipelineBridgeImportContracts(unittest.TestCase):
    def _assert_validate_run_provenance_identity(self, first: str) -> None:
        with isolated_pipeline_modules(VALIDATE_PROVENANCE_MODULES):
            direct, packaged = _validate_provenance_pair(first)
            self.assertIs(direct, packaged)

    def test_direct_first_validate_run_provenance_retains_identity(self):
        self._assert_validate_run_provenance_identity("direct")

    def test_package_first_validate_run_provenance_retains_identity(self):
        self._assert_validate_run_provenance_identity("package")

    def test_00_direct_first_bridge_modules_retain_identity(self):
        with direct_pipeline_path():
            import curate_bridge as direct_bridge
            import curate_bridge_materialize_fs as direct_materialize_fs

        import pipelines
        from pipelines import curate_bridge as packaged_bridge
        from pipelines import curate_bridge_materialize_fs as packaged_materialize_fs

        sibling_names = (
            "curate_bridge",
            "curate_bridge_events",
            "curate_bridge_gate",
            "curate_bridge_materialize",
            "curate_bridge_materialize_fs",
            "curate_bridge_raster",
            "curate_bridge_raster_numbers",
            "validate_run",
            "validate_run_spikes",
        )
        for name in sibling_names:
            with self.subTest(name=name):
                self.assertIs(sys.modules[name], getattr(pipelines, name))
        self.assertIs(direct_bridge, packaged_bridge)
        self.assertIs(direct_bridge.CurationDecision, packaged_bridge.CurationDecision)
        self.assertIs(direct_materialize_fs, packaged_materialize_fs)
        self.assertIs(
            direct_materialize_fs.BridgeCurationError,
            packaged_materialize_fs.BridgeCurationError,
        )

    def test_curate_bridge_imports_from_the_pipelines_package(self):
        from pipelines import curate_bridge

        self.assertTrue(callable(curate_bridge.curate_jsonl))

    def test_materializer_imports_through_the_pipelines_namespace(self):
        pipelines_path = str(PIPELINES)
        with mock.patch.object(
            sys,
            "path",
            [entry for entry in sys.path if entry != pipelines_path],
        ):
            from pipelines import curate_bridge_materialize as packaged_materializer

        self.assertTrue(issubclass(packaged_materializer.BridgeCurationError, ValueError))

    def test_bridge_siblings_expose_public_facade_contracts(self):
        from pipelines import curate_bridge_events
        from pipelines import curate_bridge_gate
        from pipelines import curate_bridge_materialize
        from pipelines import curate_bridge_raster

        public_helpers = (
            (curate_bridge_events, "adjacent_descents"),
            (curate_bridge_events, "canonical_marker"),
            (curate_bridge_events, "declared_clock_domains"),
            (curate_bridge_events, "explicit_order_fields"),
            (curate_bridge_events, "record_locator"),
            (curate_bridge_gate, "validate_gate_compute"),
            (curate_bridge_gate, "validate_gate_snn"),
            (curate_bridge_materialize, "safe_relative_path"),
            (curate_bridge_raster, "finite_float"),
            (curate_bridge_raster, "is_finite_number"),
            (curate_bridge_raster, "nonnegative_json_integer"),
            (curate_bridge_raster, "spike_energy"),
            (curate_bridge_raster, "validate_raster"),
            (curate_bridge_raster, "validate_third_factor"),
        )
        for module, name in public_helpers:
            with self.subTest(module=module.__name__, name=name):
                self.assertTrue(callable(getattr(module, name)))

    def test_exact_json_has_one_identity_in_package_and_direct_modes(self):
        from pipelines import exact_json as packaged_exact_json

        with direct_pipeline_path():
            import exact_json as direct_exact_json

        value = direct_exact_json.parse_finite_json_float("1.00000000000000001")
        self.assertIs(packaged_exact_json, direct_exact_json)
        self.assertIs(
            packaged_exact_json.ExactJSONFloat,
            direct_exact_json.ExactJSONFloat,
        )
        self.assertEqual(
            packaged_exact_json.dumps_exact_json({"value": value}),
            '{"value":1.00000000000000001}',
        )

    def test_package_rejects_foreign_top_level_exact_json_module(self):
        import pipelines

        foreign = ModuleType("exact_json")
        foreign.__file__ = str(REPO.parent / "unrelated" / "exact_json.py")
        with mock.patch.dict(sys.modules, {"exact_json": foreign}):
            self.assertIsNone(pipelines._local_sibling_module("exact_json"))


if __name__ == "__main__":
    unittest.main()
