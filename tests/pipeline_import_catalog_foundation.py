"""Static non-compose pipeline loaders for import-order tests."""

from __future__ import annotations

from collections.abc import Callable
from types import ModuleType

_MODULES = (
    "census",
    "check_records",
    "coding_constants",
    "coding_verify",
    "coding_verify_manifest",
    "coding_verify_steps",
    "curate_agentic",
    "curate_agentic_output",
    "curate_agentic_shapes",
    "curate_coding",
    "curate_gate",
    "curate_gate_bindings",
    "curate_gate_compose",
    "curate_gate_contract",
    "curate_gate_digest",
    "curate_gate_evidence",
    "curate_gate_evidence_verify",
    "curate_gate_gates",
    "curate_gate_identity_gate",
    "curate_gate_identity_mapping",
    "curate_gate_lanes",
    "curate_gate_manifests",
    "curate_gate_merge",
    "curate_gate_paths",
    "curate_gate_plan",
    "curate_gate_promotion",
    "curate_gate_records",
    "curate_gate_review",
    "curate_gate_reward",
    "curate_gate_reward_sidecars",
    "curate_identity",
    "curate_identity_checks",
    "curate_identity_evidence",
    "curate_identity_json",
    "curate_identity_manifest",
    "curate_identity_manifest_fields",
    "curate_identity_materialize",
    "curate_identity_output",
    "curate_identity_owners",
    "curate_identity_procedural",
    "curate_identity_provenance",
    "curate_identity_registry",
    "curate_identity_registry_fields",
    "curate_identity_registry_rows",
    "curate_identity_shapes",
    "curate_identity_source_iter",
    "curate_identity_sources",
    "curate_identity_stages",
    "curate_identity_tree",
    "curate_identity_writer",
    "curate_preferences",
    "curate_rewards",
    "curate_trajectory_preferences",
    "leftover_mill",
    "mill_evidence",
    "mill_family",
    "mill_ownership",
    "mill_resolution",
    "operator_paths",
    "preference_audit",
    "preference_audit_diff",
    "preference_context",
    "preference_model",
    "preference_reconcile",
    "preference_record",
    "preference_repair",
    "preference_writer",
    "raw_tree_guard",
    "reward_calibration",
    "reward_document",
    "reward_mapping",
    "reward_ontology",
    "reward_parse",
    "reward_parse_patterns",
    "reward_parse_values",
    "reward_policy",
    "reward_units",
    "reward_vocabulary",
    "round_txn",
    "round_txn_agentic",
    "round_txn_agentic_cascade",
    "round_txn_agentic_terms",
    "round_txn_agentic_types",
    "round_txn_preference",
    "round_txn_raster",
    "training_audit",
    "training_audit_axes",
    "training_audit_mill",
    "training_audit_observe",
    "training_audit_reasoning",
    "training_audit_record",
    "training_audit_report",
    "training_audit_snapshot",
    "trajectory_pair_curation",
    "trajectory_pair_gate",
    "trajectory_pair_shape",
    "trajectory_pair_vocabulary",
    "validate_run",
    "validate_run_cli",
    "validate_run_episode",
    "validate_run_episode_turns",
    "validate_run_multi_agent",
    "validate_run_multi_agent_roster",
    "validate_run_outcomes",
    "validate_run_preference",
    "validate_run_preference_context",
    "validate_run_provenance",
    "validate_run_reward_total",
    "validate_run_rewards",
    "validate_run_routes",
    "validate_run_safety",
    "validate_run_thalamic",
)

Loader = Callable[[], ModuleType]


def _direct_loader(name: str) -> Loader:
    def load() -> ModuleType:
        return __import__(name)

    return load


def _package_loader(name: str) -> Loader:
    def load() -> ModuleType:
        return __import__(f"pipelines.{name}", fromlist=[name])

    return load


LOADER_PAIRS: dict[str, tuple[Loader, Loader]] = {
    name: (_direct_loader(name), _package_loader(name)) for name in _MODULES
}
DIRECT_LOADERS = {name: loaders[0] for name, loaders in LOADER_PAIRS.items()}
PACKAGE_LOADERS = {name: loaders[1] for name, loaders in LOADER_PAIRS.items()}
