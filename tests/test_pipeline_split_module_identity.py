#!/usr/bin/env python3
"""Import-order identity contracts for split pipeline modules."""

from __future__ import annotations

import unittest

if __package__:
    from . import pipeline_import_catalog
    from .pipeline_import_test_support import (
        direct_pipeline_path,
        isolated_pipeline_modules,
    )
else:
    import pipeline_import_catalog
    from pipeline_import_test_support import (
        direct_pipeline_path,
        isolated_pipeline_modules,
    )


NEW_SPLIT_MODULES = (
    "compose_contract",
    "compose_curated",
    "compose_mill",
    "compose_curated_calibration",
    "compose_curated_coding",
    "compose_curated_context",
    "compose_curated_facade_bootstrap",
    "compose_curated_identity",
    "compose_curated_identity_facade",
    "compose_curated_preferences",
    "compose_curated_record",
    "compose_curated_record_facade",
    "compose_curated_run",
    "compose_curated_run_cli",
    "compose_curated_run_facade",
    "compose_curated_source",
    "compose_destination",
    "compose_destination_binding",
    "compose_destination_creation",
    "compose_destination_writer",
    "compose_destination_directory",
    "compose_destination_rename",
    "compose_destination_tree",
    "compose_source_snapshot",
    "compose_source_snapshot_members",
    "compose_source_snapshot_visibility",
    "compose_trajectory_gate",
    "compose_trajectory_goals",
    "export_compose_manifest",
    "export_contract",
    "export_curated",
    "export_destination",
    "export_members",
    "export_members_auth",
    "export_members_jsonl",
    "export_members_path",
    "export_members_read",
    "export_protocol",
    "export_provenance",
    "export_split",
    "export_viewer",
    "export_viewer_codec",
    "export_viewer_reader",
    "export_viewer_writer",
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
RUN_SUPPORT_MODULES = (
    "compose_curated_run_cli",
    "compose_curated_run_facade",
)


def _load_direct(names: tuple[str, ...]):
    with direct_pipeline_path():
        return {name: pipeline_import_catalog.load_direct(name) for name in names}


def _load_package(names: tuple[str, ...]):
    return {name: pipeline_import_catalog.load_package(name) for name in names}


def _load_in_order(names: tuple[str, ...], first: str):
    if first == "direct":
        direct = _load_direct(names)
        packaged = _load_package(names)
    else:
        packaged = _load_package(names)
        direct = _load_direct(names)
    return direct, packaged


class SplitModuleIdentityContracts(unittest.TestCase):
    def _assert_new_split_module_identity(self, first: str) -> None:
        with isolated_pipeline_modules(NEW_SPLIT_MODULES):
            direct, packaged = _load_in_order(NEW_SPLIT_MODULES, first)
            for name in NEW_SPLIT_MODULES:
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

    def test_run_support_modules_import_first_in_both_modes(self):
        for name in RUN_SUPPORT_MODULES:
            for first in ("direct", "package"):
                with self.subTest(name=name, first=first):
                    with isolated_pipeline_modules(NEW_SPLIT_MODULES):
                        direct, packaged = _load_in_order((name,), first)
                        self.assertIs(direct[name], packaged[name])


if __name__ == "__main__":
    unittest.main()
