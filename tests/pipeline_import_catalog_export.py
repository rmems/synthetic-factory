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


def _direct_export_viewer_codec() -> ModuleType:
    import export_viewer_codec as module

    return module


def _package_export_viewer_codec() -> ModuleType:
    import pipelines.export_viewer_codec as module

    return module


def _direct_export_viewer_reader() -> ModuleType:
    import export_viewer_reader as module

    return module


def _package_export_viewer_reader() -> ModuleType:
    import pipelines.export_viewer_reader as module

    return module


def _direct_export_viewer_writer() -> ModuleType:
    import export_viewer_writer as module

    return module


def _package_export_viewer_writer() -> ModuleType:
    import pipelines.export_viewer_writer as module

    return module


def _direct_export_compose_manifest() -> ModuleType:
    import export_compose_manifest as module

    return module


def _package_export_compose_manifest() -> ModuleType:
    import pipelines.export_compose_manifest as module

    return module


def _direct_export_curated() -> ModuleType:
    import export_curated as module

    return module


def _package_export_curated() -> ModuleType:
    import pipelines.export_curated as module

    return module


def _direct_export_destination() -> ModuleType:
    import export_destination as module

    return module


def _package_export_destination() -> ModuleType:
    import pipelines.export_destination as module

    return module


def _direct_export_protocol() -> ModuleType:
    import export_protocol as module

    return module


def _package_export_protocol() -> ModuleType:
    import pipelines.export_protocol as module

    return module


DIRECT_LOADERS: dict[str, Callable[[], ModuleType]] = {
    "export_compose_manifest": _direct_export_compose_manifest,
    "export_contract": _direct_export_contract,
    "export_curated": _direct_export_curated,
    "export_destination": _direct_export_destination,
    "export_members": _direct_export_members,
    "export_members_auth": _direct_export_members_auth,
    "export_members_jsonl": _direct_export_members_jsonl,
    "export_members_path": _direct_export_members_path,
    "export_members_read": _direct_export_members_read,
    "export_protocol": _direct_export_protocol,
    "export_provenance": _direct_export_provenance,
    "export_split": _direct_export_split,
    "export_viewer": _direct_export_viewer,
    "export_viewer_codec": _direct_export_viewer_codec,
    "export_viewer_reader": _direct_export_viewer_reader,
    "export_viewer_writer": _direct_export_viewer_writer,
}
PACKAGE_LOADERS: dict[str, Callable[[], ModuleType]] = {
    "export_compose_manifest": _package_export_compose_manifest,
    "export_contract": _package_export_contract,
    "export_curated": _package_export_curated,
    "export_destination": _package_export_destination,
    "export_members": _package_export_members,
    "export_members_auth": _package_export_members_auth,
    "export_members_jsonl": _package_export_members_jsonl,
    "export_members_path": _package_export_members_path,
    "export_members_read": _package_export_members_read,
    "export_protocol": _package_export_protocol,
    "export_provenance": _package_export_provenance,
    "export_split": _package_export_split,
    "export_viewer": _package_export_viewer,
    "export_viewer_codec": _package_export_viewer_codec,
    "export_viewer_reader": _package_export_viewer_reader,
    "export_viewer_writer": _package_export_viewer_writer,
}
