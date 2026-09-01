"""Static export-module loaders for import-order tests."""

from __future__ import annotations

from collections.abc import Callable
from types import ModuleType


def _direct_export_contract() -> ModuleType:
    import export_contract as module

    return module


def _package_export_contract() -> ModuleType:
    import pipelines.export_contract as module

    return module


def _direct_export_members() -> ModuleType:
    import export_members as module

    return module


def _package_export_members() -> ModuleType:
    import pipelines.export_members as module

    return module


def _direct_export_members_auth() -> ModuleType:
    import export_members_auth as module

    return module


def _package_export_members_auth() -> ModuleType:
    import pipelines.export_members_auth as module

    return module


def _direct_export_members_jsonl() -> ModuleType:
    import export_members_jsonl as module

    return module


def _package_export_members_jsonl() -> ModuleType:
    import pipelines.export_members_jsonl as module

    return module


def _direct_export_members_path() -> ModuleType:
    import export_members_path as module

    return module


def _package_export_members_path() -> ModuleType:
    import pipelines.export_members_path as module

    return module


def _direct_export_members_read() -> ModuleType:
    import export_members_read as module

    return module


def _package_export_members_read() -> ModuleType:
    import pipelines.export_members_read as module

    return module


def _direct_export_provenance() -> ModuleType:
    import export_provenance as module

    return module


def _package_export_provenance() -> ModuleType:
    import pipelines.export_provenance as module

    return module


def _direct_export_split() -> ModuleType:
    import export_split as module

    return module


def _package_export_split() -> ModuleType:
    import pipelines.export_split as module

    return module


def _direct_export_viewer() -> ModuleType:
    import export_viewer as module

    return module


def _package_export_viewer() -> ModuleType:
    import pipelines.export_viewer as module

    return module


DIRECT_LOADERS: dict[str, Callable[[], ModuleType]] = {
    "export_contract": _direct_export_contract,
    "export_members": _direct_export_members,
    "export_members_auth": _direct_export_members_auth,
    "export_members_jsonl": _direct_export_members_jsonl,
    "export_members_path": _direct_export_members_path,
    "export_members_read": _direct_export_members_read,
    "export_provenance": _direct_export_provenance,
    "export_split": _direct_export_split,
    "export_viewer": _direct_export_viewer,
}
PACKAGE_LOADERS: dict[str, Callable[[], ModuleType]] = {
    "export_contract": _package_export_contract,
    "export_members": _package_export_members,
    "export_members_auth": _package_export_members_auth,
    "export_members_jsonl": _package_export_members_jsonl,
    "export_members_path": _package_export_members_path,
    "export_members_read": _package_export_members_read,
    "export_provenance": _package_export_provenance,
    "export_split": _package_export_split,
    "export_viewer": _package_export_viewer,
}
