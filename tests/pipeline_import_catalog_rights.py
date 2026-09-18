"""Static rights and simulator pipeline loaders for import-order tests."""

from __future__ import annotations

from collections.abc import Callable
from types import ModuleType


def _direct_rights_policy_placeholders() -> ModuleType:
    import rights_policy_placeholders as module

    return module


def _package_rights_policy_placeholders() -> ModuleType:
    import pipelines.rights_policy_placeholders as module

    return module


def _direct_rights_policy_semantics() -> ModuleType:
    import rights_policy_semantics as module

    return module


def _package_rights_policy_semantics() -> ModuleType:
    import pipelines.rights_policy_semantics as module

    return module


def _direct_curate_identity_registry_evidence() -> ModuleType:
    import curate_identity_registry_evidence as module

    return module


def _package_curate_identity_registry_evidence() -> ModuleType:
    import pipelines.curate_identity_registry_evidence as module

    return module


def _direct_curate_identity_registry_sources() -> ModuleType:
    import curate_identity_registry_sources as module

    return module


def _package_curate_identity_registry_sources() -> ModuleType:
    import pipelines.curate_identity_registry_sources as module

    return module


def _direct_curate_identity_simulator() -> ModuleType:
    import curate_identity_simulator as module

    return module


def _package_curate_identity_simulator() -> ModuleType:
    import pipelines.curate_identity_simulator as module

    return module


def _direct_curate_gate_simulator_identity() -> ModuleType:
    import curate_gate_simulator_identity as module

    return module


def _package_curate_gate_simulator_identity() -> ModuleType:
    import pipelines.curate_gate_simulator_identity as module

    return module


def _direct_curate_identity_simulator_process() -> ModuleType:
    import curate_identity_simulator_process as module

    return module


def _package_curate_identity_simulator_process() -> ModuleType:
    import pipelines.curate_identity_simulator_process as module

    return module


def _direct_curate_identity_simulator_worker() -> ModuleType:
    import curate_identity_simulator_worker as module

    return module


def _package_curate_identity_simulator_worker() -> ModuleType:
    import pipelines.curate_identity_simulator_worker as module

    return module


Loader = Callable[[], ModuleType]
LOADER_PAIRS: dict[str, tuple[Loader, Loader]] = {
    "curate_gate_simulator_identity": (
        _direct_curate_gate_simulator_identity,
        _package_curate_gate_simulator_identity,
    ),
    "curate_identity_registry_evidence": (
        _direct_curate_identity_registry_evidence,
        _package_curate_identity_registry_evidence,
    ),
    "curate_identity_registry_sources": (
        _direct_curate_identity_registry_sources,
        _package_curate_identity_registry_sources,
    ),
    "curate_identity_simulator": (
        _direct_curate_identity_simulator,
        _package_curate_identity_simulator,
    ),
    "curate_identity_simulator_process": (
        _direct_curate_identity_simulator_process,
        _package_curate_identity_simulator_process,
    ),
    "curate_identity_simulator_worker": (
        _direct_curate_identity_simulator_worker,
        _package_curate_identity_simulator_worker,
    ),
    "rights_policy_placeholders": (
        _direct_rights_policy_placeholders,
        _package_rights_policy_placeholders,
    ),
    "rights_policy_semantics": (
        _direct_rights_policy_semantics,
        _package_rights_policy_semantics,
    ),
}
DIRECT_LOADERS = {name: loaders[0] for name, loaders in LOADER_PAIRS.items()}
PACKAGE_LOADERS = {name: loaders[1] for name, loaders in LOADER_PAIRS.items()}
