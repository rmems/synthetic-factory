#!/usr/bin/env python3
"""Package/direct-import compatibility regressions for pipeline modules."""

from __future__ import annotations

import importlib
import sys
import unittest
from contextlib import contextmanager
from pathlib import Path
from types import ModuleType
from unittest import mock


REPO = Path(__file__).resolve().parents[1]
PIPELINES = REPO / "pipelines"


class PipelinesPackageImports(unittest.TestCase):
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
    NEW_SPLIT_MODULES = (
        "compose_contract",
        "compose_curated",
        "compose_mill",
        "compose_curated_calibration",
        "compose_curated_coding",
        "compose_curated_context",
        "compose_curated_identity",
        "compose_curated_preferences",
        "compose_curated_record",
        "compose_curated_run",
        "compose_curated_source",
        "compose_destination_binding",
        "compose_destination_creation",
        "compose_destination_writer",
        "compose_source_snapshot",
        "export_contract",
        "export_members_auth",
        "export_members_jsonl",
        "export_members_path",
        "export_members_read",
        "export_viewer",
        "preference_audit_diff",
        "raw_tree_guard",
        "preference_context",
        "reward_mapping",
        "reward_policy",
        "training_audit_snapshot",
        "curate_agentic",
        "curate_trajectory_preferences",
        "validate_run_provenance",
    )

    @staticmethod
    def _repository_pipeline_module(module: ModuleType) -> bool:
        origin = getattr(module, "__file__", None)
        if origin is None:
            return False
        try:
            return Path(origin).resolve().is_relative_to(PIPELINES)
        except OSError:
            return False

    def _repository_pipeline_modules(self) -> dict[str, ModuleType]:
        return {
            name: module
            for name, module in tuple(sys.modules.items())
            if self._repository_pipeline_module(module)
        }

    @staticmethod
    def _remove_modules(names) -> None:
        for name in names:
            sys.modules.pop(name, None)

    def _discard_loaded_repository_modules(self) -> None:
        self._remove_modules(self._repository_pipeline_modules())

    @contextmanager
    def _clean_package_imports(self):
        original_path = list(sys.path)
        saved = self._repository_pipeline_modules()
        self._remove_modules(saved)
        sys.path[:] = [entry for entry in sys.path if entry != str(PIPELINES)]
        try:
            yield
        finally:
            self._discard_loaded_repository_modules()
            sys.modules.update(saved)
            sys.path[:] = original_path

    def test_existing_facades_import_cleanly_from_the_package(self):
        for name in ("compose_curated", "compose_destination", "training_audit"):
            with self.subTest(name=name):
                with self._clean_package_imports():
                    self.assertNotIn(str(PIPELINES), sys.path)
                    module = importlib.import_module(f"pipelines.{name}")
                    self.assertEqual(module.__name__, f"pipelines.{name}")
                    self.assertNotIn(str(PIPELINES), sys.path)

    def test_export_contract_and_viewer_import_from_a_clean_package(self):
        """Package consumers need the export contract without CLI-path leakage."""

        with self._clean_package_imports():
            self.assertNotIn(str(PIPELINES), sys.path)
            contract = importlib.import_module("pipelines.export_contract")
            viewer = importlib.import_module("pipelines.export_viewer")
            self.assertIs(viewer.ExportError, contract.ExportError)
            self.assertIs(viewer.ViewerRow, contract.ViewerRow)
            self.assertNotIn(str(PIPELINES), sys.path)

    def test_refactored_facades_support_package_and_direct_import_modes(self):
        """Every refactored facade remains usable through both supported modes."""

        with self._clean_package_imports():
            self.assertNotIn(str(PIPELINES), sys.path)
            packaged = {
                name: importlib.import_module(f"pipelines.{name}")
                for name in self.REFACTORED_FACADES
            }
            for name, module in packaged.items():
                with self.subTest(mode="package", name=name):
                    self.assertEqual(module.__package__, "pipelines")
                    self.assertTrue(self._repository_pipeline_module(module))
            self.assertNotIn(str(PIPELINES), sys.path)

        with self._clean_package_imports():
            sys.path.insert(0, str(PIPELINES))
            try:
                direct = {
                    name: importlib.import_module(name)
                    for name in self.REFACTORED_FACADES
                }
            finally:
                sys.path.remove(str(PIPELINES))
            for name, module in direct.items():
                with self.subTest(mode="direct", name=name):
                    self.assertEqual(module.__package__, "")
                    self.assertTrue(self._repository_pipeline_module(module))

    def _new_split_module_aliases(self) -> tuple[str, ...]:
        return ("pipelines",) + tuple(
            module_name
            for name in self.NEW_SPLIT_MODULES
            for module_name in (name, f"pipelines.{name}")
        )

    def _saved_package_attributes(
        self, package: ModuleType | None
    ) -> dict[str, ModuleType | None]:
        if package is None:
            return {}
        return {
            name: getattr(package, name, None) for name in self.NEW_SPLIT_MODULES
        }

    @staticmethod
    def _restore_module_aliases(
        names: tuple[str, ...], saved: dict[str, ModuleType | None]
    ) -> None:
        for name in names:
            sys.modules.pop(name, None)
        sys.modules.update(
            {name: module for name, module in saved.items() if module is not None}
        )

    @staticmethod
    def _restore_package_attributes(
        package: ModuleType | None,
        attributes: dict[str, ModuleType | None],
    ) -> None:
        if package is None:
            return
        for name, original in attributes.items():
            if original is None:
                package.__dict__.pop(name, None)
            else:
                setattr(package, name, original)

    @contextmanager
    def _isolated_new_split_modules(self):
        names = self._new_split_module_aliases()
        saved = {name: sys.modules.pop(name, None) for name in names}
        original_package = saved["pipelines"]
        original_attributes = self._saved_package_attributes(original_package)
        try:
            yield
        finally:
            self._restore_module_aliases(names, saved)
            self._restore_package_attributes(original_package, original_attributes)

    def _assert_new_split_module_identity(self, first: str) -> None:
        with self._isolated_new_split_modules():
            if first == "direct":
                sys.path.insert(0, str(PIPELINES))
                try:
                    direct = {
                        name: importlib.import_module(name)
                        for name in self.NEW_SPLIT_MODULES
                    }
                finally:
                    sys.path.remove(str(PIPELINES))
                packaged = {
                    name: importlib.import_module(f"pipelines.{name}")
                    for name in self.NEW_SPLIT_MODULES
                }
            else:
                packaged = {
                    name: importlib.import_module(f"pipelines.{name}")
                    for name in self.NEW_SPLIT_MODULES
                }
                sys.path.insert(0, str(PIPELINES))
                try:
                    direct = {
                        name: importlib.import_module(name)
                        for name in self.NEW_SPLIT_MODULES
                    }
                finally:
                    sys.path.remove(str(PIPELINES))
            for name in self.NEW_SPLIT_MODULES:
                with self.subTest(first=first, name=name):
                    self.assertIs(direct[name], packaged[name])
            self.assertIs(
                direct["compose_curated_context"].SourceCoordinates,
                packaged["compose_curated_context"].SourceCoordinates,
            )
            self.assertIs(
                direct["compose_curated_run"].ComposeRunState,
                packaged["compose_curated_run"].ComposeRunState,
            )
            self.assertIs(
                direct["export_members_auth"].AuthenticationRequest,
                packaged["export_members_auth"].AuthenticationRequest,
            )
            self.assertIs(
                direct["reward_mapping"].RewardOntologyError,
                packaged["reward_mapping"].RewardOntologyError,
            )
            self.assertIs(
                direct["validate_run_provenance"].check_provenance,
                packaged["validate_run_provenance"].check_provenance,
            )

    def test_all_new_split_modules_retain_identity_direct_first(self):
        self._assert_new_split_module_identity("direct")

    def test_all_new_split_modules_retain_identity_package_first(self):
        self._assert_new_split_module_identity("package")

    @contextmanager
    def _isolated_validate_run_provenance_modules(self):
        names = (
            "pipelines",
            "pipelines.validate_run_provenance",
            "pipelines.validate_run_spikes",
            "validate_run_provenance",
            "validate_run_spikes",
        )
        saved = {name: sys.modules.pop(name, None) for name in names}
        original_package = saved["pipelines"]
        original_attribute = getattr(
            original_package,
            "validate_run_provenance",
            None,
        )
        try:
            yield
        finally:
            for name in names:
                sys.modules.pop(name, None)
            sys.modules.update(
                {name: module for name, module in saved.items() if module is not None}
            )
            if original_package is not None:
                if original_attribute is None:
                    original_package.__dict__.pop("validate_run_provenance", None)
                else:
                    original_package.validate_run_provenance = original_attribute

    def _assert_validate_run_provenance_identity(self, first: str) -> None:
        with self._isolated_validate_run_provenance_modules():
            if first == "direct":
                sys.path.insert(0, str(PIPELINES))
                try:
                    direct = importlib.import_module("validate_run_provenance")
                finally:
                    sys.path.remove(str(PIPELINES))
                packaged = importlib.import_module("pipelines.validate_run_provenance")
            else:
                packaged = importlib.import_module("pipelines.validate_run_provenance")
                sys.path.insert(0, str(PIPELINES))
                try:
                    direct = importlib.import_module("validate_run_provenance")
                finally:
                    sys.path.remove(str(PIPELINES))
            self.assertIs(direct, packaged)

    def test_direct_first_validate_run_provenance_retains_identity(self):
        self._assert_validate_run_provenance_identity("direct")

    def test_package_first_validate_run_provenance_retains_identity(self):
        self._assert_validate_run_provenance_identity("package")

    def test_00_direct_first_bridge_modules_retain_identity(self):
        sys.path.insert(0, str(PIPELINES))
        try:
            import curate_bridge as direct_bridge
            import curate_bridge_materialize_fs as direct_materialize_fs
        finally:
            sys.path.remove(str(PIPELINES))

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

        sys.path.insert(0, str(PIPELINES))
        try:
            import exact_json as direct_exact_json
        finally:
            sys.path.remove(str(PIPELINES))

        value = direct_exact_json.parse_finite_json_float("1.00000000000000001")
        self.assertIs(packaged_exact_json, direct_exact_json)
        self.assertIs(packaged_exact_json.ExactJSONFloat, direct_exact_json.ExactJSONFloat)
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
