"""Static compose-module loaders for import-order tests."""

from __future__ import annotations

from collections.abc import Callable
from types import ModuleType


def _direct_compose_contract() -> ModuleType:
    import compose_contract as module

    return module


def _package_compose_contract() -> ModuleType:
    import pipelines.compose_contract as module

    return module


def _direct_compose_curated() -> ModuleType:
    import compose_curated as module

    return module


def _package_compose_curated() -> ModuleType:
    import pipelines.compose_curated as module

    return module


def _direct_compose_curated_calibration() -> ModuleType:
    import compose_curated_calibration as module

    return module


def _package_compose_curated_calibration() -> ModuleType:
    import pipelines.compose_curated_calibration as module

    return module


def _direct_compose_curated_calibration_lookup() -> ModuleType:
    import compose_curated_calibration_lookup as module

    return module


def _package_compose_curated_calibration_lookup() -> ModuleType:
    import pipelines.compose_curated_calibration_lookup as module

    return module


def _direct_compose_curated_coding() -> ModuleType:
    import compose_curated_coding as module

    return module


def _package_compose_curated_coding() -> ModuleType:
    import pipelines.compose_curated_coding as module

    return module


def _direct_compose_curated_context() -> ModuleType:
    import compose_curated_context as module

    return module


def _package_compose_curated_context() -> ModuleType:
    import pipelines.compose_curated_context as module

    return module


def _direct_compose_curated_facade_bootstrap() -> ModuleType:
    import compose_curated_facade_bootstrap as module

    return module


def _package_compose_curated_facade_bootstrap() -> ModuleType:
    import pipelines.compose_curated_facade_bootstrap as module

    return module


def _direct_compose_curated_identity() -> ModuleType:
    import compose_curated_identity as module

    return module


def _package_compose_curated_identity() -> ModuleType:
    import pipelines.compose_curated_identity as module

    return module


def _direct_compose_curated_identity_repairs() -> ModuleType:
    import compose_curated_identity_repairs as module

    return module


def _package_compose_curated_identity_repairs() -> ModuleType:
    import pipelines.compose_curated_identity_repairs as module

    return module


def _direct_compose_curated_identity_deferral() -> ModuleType:
    import compose_curated_identity_deferral as module

    return module


def _package_compose_curated_identity_deferral() -> ModuleType:
    import pipelines.compose_curated_identity_deferral as module

    return module


def _direct_compose_curated_identity_facade() -> ModuleType:
    import compose_curated_identity_facade as module

    return module


def _package_compose_curated_identity_facade() -> ModuleType:
    import pipelines.compose_curated_identity_facade as module

    return module


def _direct_compose_curated_identity_facade_binding() -> ModuleType:
    import compose_curated_identity_facade_binding as module

    return module


def _package_compose_curated_identity_facade_binding() -> ModuleType:
    import pipelines.compose_curated_identity_facade_binding as module

    return module


def _direct_compose_curated_identity_facade_lanes() -> ModuleType:
    import compose_curated_identity_facade_lanes as module

    return module


def _package_compose_curated_identity_facade_lanes() -> ModuleType:
    import pipelines.compose_curated_identity_facade_lanes as module

    return module


def _direct_compose_curated_identity_facade_semantics() -> ModuleType:
    import compose_curated_identity_facade_semantics as module

    return module


def _package_compose_curated_identity_facade_semantics() -> ModuleType:
    import pipelines.compose_curated_identity_facade_semantics as module

    return module


def _direct_compose_curated_preferences() -> ModuleType:
    import compose_curated_preferences as module

    return module


def _package_compose_curated_preferences() -> ModuleType:
    import pipelines.compose_curated_preferences as module

    return module


def _direct_compose_curated_record() -> ModuleType:
    import compose_curated_record as module

    return module


def _package_compose_curated_record() -> ModuleType:
    import pipelines.compose_curated_record as module

    return module


def _direct_compose_curated_record_dispatch() -> ModuleType:
    import compose_curated_record_dispatch as module

    return module


def _package_compose_curated_record_dispatch() -> ModuleType:
    import pipelines.compose_curated_record_dispatch as module

    return module


def _direct_compose_curated_record_facade() -> ModuleType:
    import compose_curated_record_facade as module

    return module


def _package_compose_curated_record_facade() -> ModuleType:
    import pipelines.compose_curated_record_facade as module

    return module


def _direct_compose_curated_record_services() -> ModuleType:
    import compose_curated_record_services as module

    return module


def _package_compose_curated_record_services() -> ModuleType:
    import pipelines.compose_curated_record_services as module

    return module


def _direct_compose_curated_run() -> ModuleType:
    import compose_curated_run as module

    return module


def _package_compose_curated_run() -> ModuleType:
    import pipelines.compose_curated_run as module

    return module


def _direct_compose_curated_run_context() -> ModuleType:
    import compose_curated_run_context as module

    return module


def _package_compose_curated_run_context() -> ModuleType:
    import pipelines.compose_curated_run_context as module

    return module


def _direct_compose_curated_run_lines() -> ModuleType:
    import compose_curated_run_lines as module

    return module


def _package_compose_curated_run_lines() -> ModuleType:
    import pipelines.compose_curated_run_lines as module

    return module


def _direct_compose_curated_run_artifacts() -> ModuleType:
    import compose_curated_run_artifacts as module

    return module


def _package_compose_curated_run_artifacts() -> ModuleType:
    import pipelines.compose_curated_run_artifacts as module

    return module


def _direct_compose_curated_run_bootstrap() -> ModuleType:
    import compose_curated_run_bootstrap as module

    return module


def _package_compose_curated_run_bootstrap() -> ModuleType:
    import pipelines.compose_curated_run_bootstrap as module

    return module


def _direct_compose_curated_run_cli() -> ModuleType:
    import compose_curated_run_cli as module

    return module


def _package_compose_curated_run_cli() -> ModuleType:
    import pipelines.compose_curated_run_cli as module

    return module


def _direct_compose_curated_run_facade() -> ModuleType:
    import compose_curated_run_facade as module

    return module


def _package_compose_curated_run_facade() -> ModuleType:
    import pipelines.compose_curated_run_facade as module

    return module


def _direct_compose_curated_source() -> ModuleType:
    import compose_curated_source as module

    return module


def _package_compose_curated_source() -> ModuleType:
    import pipelines.compose_curated_source as module

    return module


def _direct_compose_curated_source_pointers() -> ModuleType:
    import compose_curated_source_pointers as module

    return module


def _package_compose_curated_source_pointers() -> ModuleType:
    import pipelines.compose_curated_source_pointers as module

    return module


def _direct_compose_curated_source_semantics() -> ModuleType:
    import compose_curated_source_semantics as module

    return module


def _package_compose_curated_source_semantics() -> ModuleType:
    import pipelines.compose_curated_source_semantics as module

    return module


def _direct_compose_destination() -> ModuleType:
    import compose_destination as module

    return module


def _package_compose_destination() -> ModuleType:
    import pipelines.compose_destination as module

    return module


def _direct_compose_destination_binding() -> ModuleType:
    import compose_destination_binding as module

    return module


def _package_compose_destination_binding() -> ModuleType:
    import pipelines.compose_destination_binding as module

    return module


def _direct_compose_destination_creation() -> ModuleType:
    import compose_destination_creation as module

    return module


def _package_compose_destination_creation() -> ModuleType:
    import pipelines.compose_destination_creation as module

    return module


def _direct_compose_destination_writer() -> ModuleType:
    import compose_destination_writer as module

    return module


def _package_compose_destination_writer() -> ModuleType:
    import pipelines.compose_destination_writer as module

    return module


def _direct_compose_destination_directory() -> ModuleType:
    import compose_destination_directory as module

    return module


def _package_compose_destination_directory() -> ModuleType:
    import pipelines.compose_destination_directory as module

    return module


def _direct_compose_destination_rename() -> ModuleType:
    import compose_destination_rename as module

    return module


def _package_compose_destination_rename() -> ModuleType:
    import pipelines.compose_destination_rename as module

    return module


def _direct_compose_destination_tree() -> ModuleType:
    import compose_destination_tree as module

    return module


def _package_compose_destination_tree() -> ModuleType:
    import pipelines.compose_destination_tree as module

    return module


def _direct_compose_mill() -> ModuleType:
    import compose_mill as module

    return module


def _package_compose_mill() -> ModuleType:
    import pipelines.compose_mill as module

    return module


def _direct_compose_source_snapshot() -> ModuleType:
    import compose_source_snapshot as module

    return module


def _package_compose_source_snapshot() -> ModuleType:
    import pipelines.compose_source_snapshot as module

    return module


def _direct_compose_source_snapshot_members() -> ModuleType:
    import compose_source_snapshot_members as module

    return module


def _package_compose_source_snapshot_members() -> ModuleType:
    import pipelines.compose_source_snapshot_members as module

    return module


def _direct_compose_source_snapshot_visibility() -> ModuleType:
    import compose_source_snapshot_visibility as module

    return module


def _package_compose_source_snapshot_visibility() -> ModuleType:
    import pipelines.compose_source_snapshot_visibility as module

    return module


def _direct_compose_trajectory() -> ModuleType:
    import compose_trajectory as module

    return module


def _package_compose_trajectory() -> ModuleType:
    import pipelines.compose_trajectory as module

    return module


def _direct_compose_trajectory_gate() -> ModuleType:
    import compose_trajectory_gate as module

    return module


def _package_compose_trajectory_gate() -> ModuleType:
    import pipelines.compose_trajectory_gate as module

    return module


def _direct_compose_trajectory_goals() -> ModuleType:
    import compose_trajectory_goals as module

    return module


def _package_compose_trajectory_goals() -> ModuleType:
    import pipelines.compose_trajectory_goals as module

    return module


Loader = Callable[[], ModuleType]
LOADER_PAIRS: dict[str, tuple[Loader, Loader]] = {
    "compose_contract": (_direct_compose_contract, _package_compose_contract),
    "compose_curated": (_direct_compose_curated, _package_compose_curated),
    "compose_curated_calibration": (
        _direct_compose_curated_calibration,
        _package_compose_curated_calibration,
    ),
    "compose_curated_calibration_lookup": (
        _direct_compose_curated_calibration_lookup,
        _package_compose_curated_calibration_lookup,
    ),
    "compose_curated_coding": (
        _direct_compose_curated_coding,
        _package_compose_curated_coding,
    ),
    "compose_curated_context": (
        _direct_compose_curated_context,
        _package_compose_curated_context,
    ),
    "compose_curated_facade_bootstrap": (
        _direct_compose_curated_facade_bootstrap,
        _package_compose_curated_facade_bootstrap,
    ),
    "compose_curated_identity": (
        _direct_compose_curated_identity,
        _package_compose_curated_identity,
    ),
    "compose_curated_identity_repairs": (
        _direct_compose_curated_identity_repairs,
        _package_compose_curated_identity_repairs,
    ),
    "compose_curated_identity_deferral": (
        _direct_compose_curated_identity_deferral,
        _package_compose_curated_identity_deferral,
    ),
    "compose_curated_identity_facade": (
        _direct_compose_curated_identity_facade,
        _package_compose_curated_identity_facade,
    ),
    "compose_curated_identity_facade_binding": (
        _direct_compose_curated_identity_facade_binding,
        _package_compose_curated_identity_facade_binding,
    ),
    "compose_curated_identity_facade_lanes": (
        _direct_compose_curated_identity_facade_lanes,
        _package_compose_curated_identity_facade_lanes,
    ),
    "compose_curated_identity_facade_semantics": (
        _direct_compose_curated_identity_facade_semantics,
        _package_compose_curated_identity_facade_semantics,
    ),
    "compose_curated_preferences": (
        _direct_compose_curated_preferences,
        _package_compose_curated_preferences,
    ),
    "compose_curated_record": (
        _direct_compose_curated_record,
        _package_compose_curated_record,
    ),
    "compose_curated_record_dispatch": (
        _direct_compose_curated_record_dispatch,
        _package_compose_curated_record_dispatch,
    ),
    "compose_curated_record_facade": (
        _direct_compose_curated_record_facade,
        _package_compose_curated_record_facade,
    ),
    "compose_curated_record_services": (
        _direct_compose_curated_record_services,
        _package_compose_curated_record_services,
    ),
    "compose_curated_run": (_direct_compose_curated_run, _package_compose_curated_run),
    "compose_curated_run_context": (
        _direct_compose_curated_run_context,
        _package_compose_curated_run_context,
    ),
    "compose_curated_run_lines": (
        _direct_compose_curated_run_lines,
        _package_compose_curated_run_lines,
    ),
    "compose_curated_run_artifacts": (
        _direct_compose_curated_run_artifacts,
        _package_compose_curated_run_artifacts,
    ),
    "compose_curated_run_bootstrap": (
        _direct_compose_curated_run_bootstrap,
        _package_compose_curated_run_bootstrap,
    ),
    "compose_curated_run_cli": (
        _direct_compose_curated_run_cli,
        _package_compose_curated_run_cli,
    ),
    "compose_curated_run_facade": (
        _direct_compose_curated_run_facade,
        _package_compose_curated_run_facade,
    ),
    "compose_curated_source": (
        _direct_compose_curated_source,
        _package_compose_curated_source,
    ),
    "compose_curated_source_pointers": (
        _direct_compose_curated_source_pointers,
        _package_compose_curated_source_pointers,
    ),
    "compose_curated_source_semantics": (
        _direct_compose_curated_source_semantics,
        _package_compose_curated_source_semantics,
    ),
    "compose_destination": (_direct_compose_destination, _package_compose_destination),
    "compose_destination_binding": (
        _direct_compose_destination_binding,
        _package_compose_destination_binding,
    ),
    "compose_destination_creation": (
        _direct_compose_destination_creation,
        _package_compose_destination_creation,
    ),
    "compose_destination_writer": (
        _direct_compose_destination_writer,
        _package_compose_destination_writer,
    ),
    "compose_destination_directory": (
        _direct_compose_destination_directory,
        _package_compose_destination_directory,
    ),
    "compose_destination_rename": (
        _direct_compose_destination_rename,
        _package_compose_destination_rename,
    ),
    "compose_destination_tree": (
        _direct_compose_destination_tree,
        _package_compose_destination_tree,
    ),
    "compose_mill": (_direct_compose_mill, _package_compose_mill),
    "compose_source_snapshot": (
        _direct_compose_source_snapshot,
        _package_compose_source_snapshot,
    ),
    "compose_source_snapshot_members": (
        _direct_compose_source_snapshot_members,
        _package_compose_source_snapshot_members,
    ),
    "compose_source_snapshot_visibility": (
        _direct_compose_source_snapshot_visibility,
        _package_compose_source_snapshot_visibility,
    ),
    "compose_trajectory": (_direct_compose_trajectory, _package_compose_trajectory),
    "compose_trajectory_gate": (
        _direct_compose_trajectory_gate,
        _package_compose_trajectory_gate,
    ),
    "compose_trajectory_goals": (
        _direct_compose_trajectory_goals,
        _package_compose_trajectory_goals,
    ),
}
DIRECT_LOADERS = {name: loaders[0] for name, loaders in LOADER_PAIRS.items()}
PACKAGE_LOADERS = {name: loaders[1] for name, loaders in LOADER_PAIRS.items()}
