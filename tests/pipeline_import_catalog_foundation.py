"""Static non-compose pipeline loaders for import-order tests."""

from __future__ import annotations

from collections.abc import Callable
from types import ModuleType


def _direct_census() -> ModuleType:
    import census as module

    return module


def _package_census() -> ModuleType:
    import pipelines.census as module

    return module


def _direct_check_records() -> ModuleType:
    import check_records as module

    return module


def _package_check_records() -> ModuleType:
    import pipelines.check_records as module

    return module


def _direct_coding_constants() -> ModuleType:
    import coding_constants as module

    return module


def _package_coding_constants() -> ModuleType:
    import pipelines.coding_constants as module

    return module


def _direct_coding_verify() -> ModuleType:
    import coding_verify as module

    return module


def _package_coding_verify() -> ModuleType:
    import pipelines.coding_verify as module

    return module


def _direct_coding_verify_manifest() -> ModuleType:
    import coding_verify_manifest as module

    return module


def _package_coding_verify_manifest() -> ModuleType:
    import pipelines.coding_verify_manifest as module

    return module


def _direct_coding_verify_steps() -> ModuleType:
    import coding_verify_steps as module

    return module


def _package_coding_verify_steps() -> ModuleType:
    import pipelines.coding_verify_steps as module

    return module


def _direct_curate_agentic() -> ModuleType:
    import curate_agentic as module

    return module


def _package_curate_agentic() -> ModuleType:
    import pipelines.curate_agentic as module

    return module


def _direct_curate_agentic_output() -> ModuleType:
    import curate_agentic_output as module

    return module


def _package_curate_agentic_output() -> ModuleType:
    import pipelines.curate_agentic_output as module

    return module


def _direct_curate_agentic_shapes() -> ModuleType:
    import curate_agentic_shapes as module

    return module


def _package_curate_agentic_shapes() -> ModuleType:
    import pipelines.curate_agentic_shapes as module

    return module


def _direct_curate_coding() -> ModuleType:
    import curate_coding as module

    return module


def _package_curate_coding() -> ModuleType:
    import pipelines.curate_coding as module

    return module


def _direct_curate_identity() -> ModuleType:
    import curate_identity as module

    return module


def _package_curate_identity() -> ModuleType:
    import pipelines.curate_identity as module

    return module


def _direct_curate_preferences() -> ModuleType:
    import curate_preferences as module

    return module


def _package_curate_preferences() -> ModuleType:
    import pipelines.curate_preferences as module

    return module


def _direct_curate_rewards() -> ModuleType:
    import curate_rewards as module

    return module


def _package_curate_rewards() -> ModuleType:
    import pipelines.curate_rewards as module

    return module


def _direct_curate_trajectory_preferences() -> ModuleType:
    import curate_trajectory_preferences as module

    return module


def _package_curate_trajectory_preferences() -> ModuleType:
    import pipelines.curate_trajectory_preferences as module

    return module


def _direct_leftover_mill() -> ModuleType:
    import leftover_mill as module

    return module


def _package_leftover_mill() -> ModuleType:
    import pipelines.leftover_mill as module

    return module


def _direct_mill_evidence() -> ModuleType:
    import mill_evidence as module

    return module


def _package_mill_evidence() -> ModuleType:
    import pipelines.mill_evidence as module

    return module


def _direct_mill_family() -> ModuleType:
    import mill_family as module

    return module


def _package_mill_family() -> ModuleType:
    import pipelines.mill_family as module

    return module


def _direct_mill_ownership() -> ModuleType:
    import mill_ownership as module

    return module


def _package_mill_ownership() -> ModuleType:
    import pipelines.mill_ownership as module

    return module


def _direct_mill_resolution() -> ModuleType:
    import mill_resolution as module

    return module


def _package_mill_resolution() -> ModuleType:
    import pipelines.mill_resolution as module

    return module


def _direct_preference_audit() -> ModuleType:
    import preference_audit as module

    return module


def _package_preference_audit() -> ModuleType:
    import pipelines.preference_audit as module

    return module


def _direct_preference_audit_diff() -> ModuleType:
    import preference_audit_diff as module

    return module


def _package_preference_audit_diff() -> ModuleType:
    import pipelines.preference_audit_diff as module

    return module


def _direct_preference_context() -> ModuleType:
    import preference_context as module

    return module


def _package_preference_context() -> ModuleType:
    import pipelines.preference_context as module

    return module


def _direct_preference_model() -> ModuleType:
    import preference_model as module

    return module


def _package_preference_model() -> ModuleType:
    import pipelines.preference_model as module

    return module


def _direct_preference_reconcile() -> ModuleType:
    import preference_reconcile as module

    return module


def _package_preference_reconcile() -> ModuleType:
    import pipelines.preference_reconcile as module

    return module


def _direct_preference_record() -> ModuleType:
    import preference_record as module

    return module


def _package_preference_record() -> ModuleType:
    import pipelines.preference_record as module

    return module


def _direct_preference_repair() -> ModuleType:
    import preference_repair as module

    return module


def _package_preference_repair() -> ModuleType:
    import pipelines.preference_repair as module

    return module


def _direct_preference_writer() -> ModuleType:
    import preference_writer as module

    return module


def _package_preference_writer() -> ModuleType:
    import pipelines.preference_writer as module

    return module


def _direct_raw_tree_guard() -> ModuleType:
    import raw_tree_guard as module

    return module


def _package_raw_tree_guard() -> ModuleType:
    import pipelines.raw_tree_guard as module

    return module


def _direct_reward_calibration() -> ModuleType:
    import reward_calibration as module

    return module


def _package_reward_calibration() -> ModuleType:
    import pipelines.reward_calibration as module

    return module


def _direct_reward_document() -> ModuleType:
    import reward_document as module

    return module


def _package_reward_document() -> ModuleType:
    import pipelines.reward_document as module

    return module


def _direct_reward_mapping() -> ModuleType:
    import reward_mapping as module

    return module


def _package_reward_mapping() -> ModuleType:
    import pipelines.reward_mapping as module

    return module


def _direct_reward_ontology() -> ModuleType:
    import reward_ontology as module

    return module


def _package_reward_ontology() -> ModuleType:
    import pipelines.reward_ontology as module

    return module


def _direct_reward_policy() -> ModuleType:
    import reward_policy as module

    return module


def _package_reward_policy() -> ModuleType:
    import pipelines.reward_policy as module

    return module


def _direct_reward_units() -> ModuleType:
    import reward_units as module

    return module


def _package_reward_units() -> ModuleType:
    import pipelines.reward_units as module

    return module


def _direct_reward_vocabulary() -> ModuleType:
    import reward_vocabulary as module

    return module


def _package_reward_vocabulary() -> ModuleType:
    import pipelines.reward_vocabulary as module

    return module


def _direct_round_txn() -> ModuleType:
    import round_txn as module

    return module


def _package_round_txn() -> ModuleType:
    import pipelines.round_txn as module

    return module


def _direct_round_txn_preference() -> ModuleType:
    import round_txn_preference as module

    return module


def _package_round_txn_preference() -> ModuleType:
    import pipelines.round_txn_preference as module

    return module


def _direct_round_txn_raster() -> ModuleType:
    import round_txn_raster as module

    return module


def _package_round_txn_raster() -> ModuleType:
    import pipelines.round_txn_raster as module

    return module


def _direct_training_audit() -> ModuleType:
    import training_audit as module

    return module


def _package_training_audit() -> ModuleType:
    import pipelines.training_audit as module

    return module


def _direct_training_audit_mill() -> ModuleType:
    import training_audit_mill as module

    return module


def _package_training_audit_mill() -> ModuleType:
    import pipelines.training_audit_mill as module

    return module


def _direct_training_audit_report() -> ModuleType:
    import training_audit_report as module

    return module


def _package_training_audit_report() -> ModuleType:
    import pipelines.training_audit_report as module

    return module


def _direct_training_audit_snapshot() -> ModuleType:
    import training_audit_snapshot as module

    return module


def _package_training_audit_snapshot() -> ModuleType:
    import pipelines.training_audit_snapshot as module

    return module


def _direct_trajectory_pair_curation() -> ModuleType:
    import trajectory_pair_curation as module

    return module


def _package_trajectory_pair_curation() -> ModuleType:
    import pipelines.trajectory_pair_curation as module

    return module


def _direct_trajectory_pair_gate() -> ModuleType:
    import trajectory_pair_gate as module

    return module


def _package_trajectory_pair_gate() -> ModuleType:
    import pipelines.trajectory_pair_gate as module

    return module


def _direct_trajectory_pair_shape() -> ModuleType:
    import trajectory_pair_shape as module

    return module


def _package_trajectory_pair_shape() -> ModuleType:
    import pipelines.trajectory_pair_shape as module

    return module


def _direct_trajectory_pair_vocabulary() -> ModuleType:
    import trajectory_pair_vocabulary as module

    return module


def _package_trajectory_pair_vocabulary() -> ModuleType:
    import pipelines.trajectory_pair_vocabulary as module

    return module


def _direct_validate_run_provenance() -> ModuleType:
    import validate_run_provenance as module

    return module


def _package_validate_run_provenance() -> ModuleType:
    import pipelines.validate_run_provenance as module

    return module


Loader = Callable[[], ModuleType]
LOADER_PAIRS: dict[str, tuple[Loader, Loader]] = {
    "census": (_direct_census, _package_census),
    "check_records": (_direct_check_records, _package_check_records),
    "coding_constants": (_direct_coding_constants, _package_coding_constants),
    "coding_verify": (_direct_coding_verify, _package_coding_verify),
    "coding_verify_manifest": (_direct_coding_verify_manifest, _package_coding_verify_manifest),
    "coding_verify_steps": (_direct_coding_verify_steps, _package_coding_verify_steps),
    "curate_agentic": (_direct_curate_agentic, _package_curate_agentic),
    "curate_agentic_output": (_direct_curate_agentic_output, _package_curate_agentic_output),
    "curate_agentic_shapes": (_direct_curate_agentic_shapes, _package_curate_agentic_shapes),
    "curate_coding": (_direct_curate_coding, _package_curate_coding),
    "curate_identity": (_direct_curate_identity, _package_curate_identity),
    "curate_preferences": (_direct_curate_preferences, _package_curate_preferences),
    "curate_rewards": (_direct_curate_rewards, _package_curate_rewards),
    "curate_trajectory_preferences": (
        _direct_curate_trajectory_preferences,
        _package_curate_trajectory_preferences,
    ),
    "leftover_mill": (_direct_leftover_mill, _package_leftover_mill),
    "mill_evidence": (_direct_mill_evidence, _package_mill_evidence),
    "mill_family": (_direct_mill_family, _package_mill_family),
    "mill_ownership": (_direct_mill_ownership, _package_mill_ownership),
    "mill_resolution": (_direct_mill_resolution, _package_mill_resolution),
    "preference_audit": (_direct_preference_audit, _package_preference_audit),
    "preference_audit_diff": (_direct_preference_audit_diff, _package_preference_audit_diff),
    "preference_context": (_direct_preference_context, _package_preference_context),
    "preference_model": (_direct_preference_model, _package_preference_model),
    "preference_reconcile": (_direct_preference_reconcile, _package_preference_reconcile),
    "preference_record": (_direct_preference_record, _package_preference_record),
    "preference_repair": (_direct_preference_repair, _package_preference_repair),
    "preference_writer": (_direct_preference_writer, _package_preference_writer),
    "raw_tree_guard": (_direct_raw_tree_guard, _package_raw_tree_guard),
    "reward_calibration": (_direct_reward_calibration, _package_reward_calibration),
    "reward_document": (_direct_reward_document, _package_reward_document),
    "reward_mapping": (_direct_reward_mapping, _package_reward_mapping),
    "reward_ontology": (_direct_reward_ontology, _package_reward_ontology),
    "reward_policy": (_direct_reward_policy, _package_reward_policy),
    "reward_units": (_direct_reward_units, _package_reward_units),
    "reward_vocabulary": (_direct_reward_vocabulary, _package_reward_vocabulary),
    "round_txn": (_direct_round_txn, _package_round_txn),
    "round_txn_preference": (_direct_round_txn_preference, _package_round_txn_preference),
    "round_txn_raster": (_direct_round_txn_raster, _package_round_txn_raster),
    "training_audit": (_direct_training_audit, _package_training_audit),
    "training_audit_mill": (_direct_training_audit_mill, _package_training_audit_mill),
    "training_audit_report": (_direct_training_audit_report, _package_training_audit_report),
    "training_audit_snapshot": (_direct_training_audit_snapshot, _package_training_audit_snapshot),
    "trajectory_pair_curation": (
        _direct_trajectory_pair_curation,
        _package_trajectory_pair_curation,
    ),
    "trajectory_pair_gate": (_direct_trajectory_pair_gate, _package_trajectory_pair_gate),
    "trajectory_pair_shape": (_direct_trajectory_pair_shape, _package_trajectory_pair_shape),
    "trajectory_pair_vocabulary": (
        _direct_trajectory_pair_vocabulary,
        _package_trajectory_pair_vocabulary,
    ),
    "validate_run_provenance": (_direct_validate_run_provenance, _package_validate_run_provenance),
}
DIRECT_LOADERS = {name: loaders[0] for name, loaders in LOADER_PAIRS.items()}
PACKAGE_LOADERS = {name: loaders[1] for name, loaders in LOADER_PAIRS.items()}
