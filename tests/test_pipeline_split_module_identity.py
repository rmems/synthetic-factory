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
    "compose_curated_calibration_lookup",
    "compose_curated_coding",
    "compose_curated_context",
    "compose_curated_facade_bootstrap",
    "compose_curated_identity",
    "compose_curated_identity_repairs",
    "compose_curated_identity_deferral",
    "compose_curated_identity_facade",
    "compose_curated_identity_facade_binding",
    "compose_curated_identity_facade_lanes",
    "compose_curated_identity_facade_semantics",
    "compose_curated_preferences",
    "compose_curated_record",
    "compose_curated_record_facade",
    "compose_curated_run",
    "compose_curated_run_context",
    "compose_curated_run_lines",
    "compose_curated_run_artifacts",
    "compose_curated_run_cli",
    "compose_curated_run_facade",
    "compose_curated_source",
    "compose_curated_source_pointers",
    "compose_curated_source_semantics",
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
    "training_audit_record",
    "training_audit_reasoning",
    "training_audit_snapshot",
    "curate_agentic",
    "curate_gate",
    "curate_gate_contract",
    "curate_gate_digest",
    "curate_gate_paths",
    "curate_gate_plan",
    "curate_gate_merge",
    "curate_gate_manifests",
    "curate_gate_evidence",
    "curate_gate_evidence_verify",
    "curate_gate_records",
    "curate_gate_bindings",
    "curate_gate_identity_gate",
    "curate_gate_identity_mapping",
    "curate_gate_review",
    "curate_gate_lanes",
    "curate_gate_compose",
    "curate_gate_reward",
    "curate_gate_reward_sidecars",
    "curate_gate_gates",
    "curate_identity",
    "curate_trajectory_preferences",
    "round_txn",
    "validate_run",
    "validate_run_provenance",
    "curate_identity_registry_fields",
    "curate_identity_registry_rows",
    "curate_identity_registry",
    "curate_identity_json",
    "curate_gate_promotion",
    "round_txn_agentic_cascade",
    "round_txn_agentic_types",
    "round_txn_agentic_terms",
    "round_txn_agentic",
    "validate_run_safety",
    "operator_paths",
    "validate_run_rewards",
    "validate_run_thalamic",
    "validate_run_outcomes",
    "validate_run_reward_total",
    "validate_run_episode",
    "validate_run_episode_turns",
    "validate_run_multi_agent",
    "validate_run_multi_agent_roster",
    "validate_run_preference",
    "validate_run_preference_context",
    "validate_run_routes",
    "validate_run_cli",
)
RUN_SUPPORT_MODULES = (
    "compose_curated_run_cli",
    "compose_curated_run_facade",
    # validate_run_rewards once re-exported check_reward_total from
    # validate_run_reward_total, which imports validate_run_rewards back, so
    # importing reward_total first raised AttributeError on a partial module.
    "validate_run_reward_total",
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
                direct["compose_curated_run_context"].ComposeRunState,
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
            self.assertIs(
                direct["validate_run_thalamic"].check_meta_round,
                packaged["validate_run_thalamic"].check_meta_round,
            )
            self.assertIs(
                direct["validate_run_outcomes"].terminal_outcome_agrees,
                packaged["validate_run_outcomes"].terminal_outcome_agrees,
            )
            self.assertIs(
                direct["validate_run_reward_total"].check_reward_total,
                packaged["validate_run_reward_total"].check_reward_total,
            )
            # The four core CLIs raise and classify across the twin boundary:
            # a split copy makes ``except GateError`` miss and ``isinstance``
            # of a FactoryRow fail, so pin the classes, not just the modules.
            self.assertIs(
                direct["curate_gate"].GateError,
                packaged["curate_gate"].GateError,
            )
            self._assert_identity_export_twins(direct, packaged)
            self.assertIs(
                direct["round_txn"].TransactionError,
                packaged["round_txn"].TransactionError,
            )
            self.assertIs(
                direct["validate_run"].check_line,
                packaged["validate_run"].check_line,
            )
            self.assertIs(
                direct["validate_run_episode"].check_episode,
                packaged["validate_run_episode"].check_episode,
            )
            self.assertIs(
                direct["validate_run_preference"].staging_preference_goal_errors,
                packaged["validate_run_preference"].staging_preference_goal_errors,
            )
            self.assertIs(
                direct["validate_run_routes"].check_line,
                packaged["validate_run_routes"].check_line,
            )

    def _assert_identity_export_twins(self, direct, packaged) -> None:
        self.assertIs(
            direct["curate_identity"].FactoryRow,
            packaged["curate_identity"].FactoryRow,
        )
        self.assertIs(
            direct["curate_identity"].FactoryRow,
            direct["curate_identity_registry"].FactoryRow,
        )
        self.assertIs(
            direct["curate_identity_registry"].FactoryRow,
            direct["curate_identity_registry_rows"].FactoryRow,
        )
        self.assertIs(
            direct["curate_identity"].IdentityCurationError,
            direct["curate_identity_json"].IdentityCurationError,
        )
        self.assertIs(
            direct["curate_identity"].load_registry,
            direct["curate_identity_registry"].load_registry,
        )
        self.assertIs(
            direct["curate_identity"].default_registry,
            direct["curate_identity_registry"].default_registry,
        )
        self.assertIs(
            direct["curate_identity"].ExactJSONFloat,
            direct["curate_identity_json"].ExactJSONFloat,
        )
        self.assertIs(
            direct["curate_identity"].dumps_exact_json,
            direct["curate_identity_json"].dumps_exact_json,
        )
        self.assertIs(
            direct["curate_identity"].PROVIDERS,
            direct["curate_identity_registry"].PROVIDERS,
        )

    def test_all_new_split_modules_retain_identity_direct_first(self):
        self._assert_new_split_module_identity("direct")

    def test_all_new_split_modules_retain_identity_package_first(self):
        self._assert_new_split_module_identity("package")

    def test_facade_adopts_sibling_registry_cache_when_imported_second(self):
        with isolated_pipeline_modules(NEW_SPLIT_MODULES):
            with direct_pipeline_path():
                registry = pipeline_import_catalog.load_direct("curate_identity_registry")
                loaded = registry.default_registry()
                identity = pipeline_import_catalog.load_direct("curate_identity")
            self.assertIs(identity._DEFAULT_REGISTRY, loaded)
            self.assertIs(identity.default_registry(), loaded)

    def test_run_support_modules_import_first_in_both_modes(self):
        for name in RUN_SUPPORT_MODULES:
            for first in ("direct", "package"):
                with (
                    self.subTest(name=name, first=first),
                    isolated_pipeline_modules(NEW_SPLIT_MODULES),
                ):
                    direct, packaged = _load_in_order((name,), first)
                    self.assertIs(direct[name], packaged[name])


if __name__ == "__main__":
    unittest.main()
