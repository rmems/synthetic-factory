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
    "mill_script_inventory_schema",
    "mill_script_inventory_families",
    "mill_script_inventory_git",
    "mill_script_inventory",
    "oracle_grounded.native_profiles",
    "oracle_grounded.native_runtime",
    "oracle_grounded.native_checks",
    "oracle_grounded.native_gate",
    "oracle_generate",
    "oracle_generate_fs",
    "oracle_generate_parents",
    "oracle_generate_prepare",
    "oracle_generate_publish",
    "oracle_generate_records",
    "oracle_validate",
    "oracle_record_stages",
    "oracle_record_envelope",
    "oracle_record_generator",
    "oracle_validate_records",
    "oracle_validate_tree",
    "oracle_validate_manifest",
    "oracle_validate_manifest_records",
    "oracle_checks_facade",
    "oracle_validate_snapshot",
    "oracle_validate_capture",
    "oracle_validate_run",
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
    "compose_oracle_selection",
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
    "reward_parse",
    "reward_parse_values",
    "reward_parse_patterns",
    "reward_policy",
    "rights_record",
    "training_audit",
    "training_audit_axes",
    "training_audit_observe",
    "training_audit_rights",
    "training_audit_rights_manifest",
    "training_audit_rights_coverage",
    "compose_curated_rights",
    "curate_gate_rights",
    "training_audit_record",
    "training_audit_reasoning",
    "training_audit_snapshot",
    "training_audit_completion",
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
    "curate_identity_provenance",
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

# (module in the direct map, attribute, module in the packaged map): the
# direct and packaged copies of a split module must expose the same object.
# The core CLIs raise and classify across the twin boundary — a split copy
# makes ``except GateError`` miss and ``isinstance`` of a FactoryRow fail —
# so the classes and functions are pinned, not just the modules.
SPLIT_TWIN_ATTRIBUTES = (
    ("compose_curated_context", "SourceCoordinates", "compose_curated_context"),
    ("compose_curated_run", "ComposeRunState", "compose_curated_run"),
    ("compose_curated_run_context", "ComposeRunState", "compose_curated_run"),
    ("export_members_auth", "AuthenticationRequest", "export_members_auth"),
    ("reward_mapping", "RewardOntologyError", "reward_mapping"),
    ("reward_parse", "RewardOntologyError", "reward_mapping"),
    ("validate_run_provenance", "check_provenance", "validate_run_provenance"),
    ("validate_run_thalamic", "check_meta_round", "validate_run_thalamic"),
    ("validate_run_outcomes", "terminal_outcome_agrees", "validate_run_outcomes"),
    ("validate_run_reward_total", "check_reward_total", "validate_run_reward_total"),
    ("curate_gate", "GateError", "curate_gate"),
    ("round_txn", "TransactionError", "round_txn"),
    ("validate_run", "check_line", "validate_run"),
    ("validate_run_episode", "check_episode", "validate_run_episode"),
    (
        "validate_run_preference",
        "staging_preference_goal_errors",
        "validate_run_preference",
    ),
    ("validate_run_routes", "check_line", "validate_run_routes"),
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
    def _assert_module_twins(self, direct, packaged, first: str) -> None:
        for name in NEW_SPLIT_MODULES:
            with self.subTest(first=first, name=name):
                self.assertIs(direct[name], packaged[name])

    def _assert_twin_attributes(self, direct, packaged) -> None:
        for left_name, attribute, right_name in SPLIT_TWIN_ATTRIBUTES:
            with self.subTest(left=left_name, attribute=attribute, right=right_name):
                self.assertIs(
                    getattr(direct[left_name], attribute),
                    getattr(packaged[right_name], attribute),
                )

    def _assert_new_split_module_identity(self, first: str) -> None:
        with isolated_pipeline_modules(NEW_SPLIT_MODULES):
            direct, packaged = _load_in_order(NEW_SPLIT_MODULES, first)
            self._assert_module_twins(direct, packaged, first)
            self._assert_twin_attributes(direct, packaged)
            self._assert_identity_export_twins(direct, packaged)

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
            direct["curate_identity"]._provenance_mapping_sha256,
            direct["curate_identity_provenance"].provenance_mapping_sha256,
        )
        self.assertIs(
            direct["curate_identity"]._seal_provenance_mapping,
            direct["curate_identity_provenance"].seal_provenance_mapping,
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
