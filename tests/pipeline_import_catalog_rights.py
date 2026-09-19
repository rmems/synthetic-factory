"""Static rights-module loaders for import-order tests."""

from __future__ import annotations

from collections.abc import Callable
from types import ModuleType


def _direct_rights_record() -> ModuleType:
    import rights_record as module

    return module


def _package_rights_record() -> ModuleType:
    import pipelines.rights_record as module

    return module


def _direct_training_audit_rights() -> ModuleType:
    import training_audit_rights as module

    return module


def _package_training_audit_rights() -> ModuleType:
    import pipelines.training_audit_rights as module

    return module


def _direct_compose_curated_rights() -> ModuleType:
    import compose_curated_rights as module

    return module


def _package_compose_curated_rights() -> ModuleType:
    import pipelines.compose_curated_rights as module

    return module


def _direct_curate_gate_rights() -> ModuleType:
    import curate_gate_rights as module

    return module


def _package_curate_gate_rights() -> ModuleType:
    import pipelines.curate_gate_rights as module

    return module


def _direct_training_audit_rights_manifest() -> ModuleType:
    import training_audit_rights_manifest as module

    return module


def _package_training_audit_rights_manifest() -> ModuleType:
    import pipelines.training_audit_rights_manifest as module

    return module


def _direct_training_audit_rights_coverage() -> ModuleType:
    import training_audit_rights_coverage as module

    return module


def _package_training_audit_rights_coverage() -> ModuleType:
    import pipelines.training_audit_rights_coverage as module

    return module


def _direct_training_audit_completion() -> ModuleType:
    import training_audit_completion as module

    return module


def _package_training_audit_completion() -> ModuleType:
    import pipelines.training_audit_completion as module

    return module


Loader = Callable[[], ModuleType]
LOADER_PAIRS: dict[str, tuple[Loader, Loader]] = {
    "training_audit_rights_manifest": (
        _direct_training_audit_rights_manifest,
        _package_training_audit_rights_manifest,
    ),
    "training_audit_rights_coverage": (
        _direct_training_audit_rights_coverage,
        _package_training_audit_rights_coverage,
    ),
    "training_audit_completion": (
        _direct_training_audit_completion,
        _package_training_audit_completion,
    ),
    "rights_record": (_direct_rights_record, _package_rights_record),
    "training_audit_rights": (_direct_training_audit_rights, _package_training_audit_rights),
    "compose_curated_rights": (_direct_compose_curated_rights, _package_compose_curated_rights),
    "curate_gate_rights": (_direct_curate_gate_rights, _package_curate_gate_rights),
}
DIRECT_LOADERS = {name: loaders[0] for name, loaders in LOADER_PAIRS.items()}
PACKAGE_LOADERS = {name: loaders[1] for name, loaders in LOADER_PAIRS.items()}
