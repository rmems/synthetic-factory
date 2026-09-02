#!/usr/bin/env python3
"""Exact-member authentication and alias-free export-tree enumeration.

The filesystem path, pinned-read, strict JSONL, and descriptor responsibilities
live in focused sibling modules. Their names remain re-exported here so the
historical ``export_members`` and ``export_hf`` compatibility surfaces do not
change.
"""

from __future__ import annotations

import os
import stat
import sys
from pathlib import Path
from typing import Any

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("export_members")
    from .export_contract import ExportError
    from .export_members_auth import (
        AuthenticationDependencies as _AuthenticationDependencies,
        AuthenticationRequest as _AuthenticationRequest,
        authenticate_descriptor as _authenticate_descriptor,
    )
    from .export_members_jsonl import (
        lf_jsonl_documents as _lf_jsonl_documents,
        lf_jsonl_lines as _lf_jsonl_lines,
    )
    from .export_members_path import (
        compose_member_path as _compose_member_path,
        is_under_raw as _is_under_raw,
        member_relative as _member_relative,
        require_exact_directory as _require_exact_directory,
        require_inside_root as _require_inside_root,
        require_unique_regular as _require_unique_regular,
    )
    from .export_members_read import (
        read_exact_regular_file as _read_exact_regular_file,
        read_pinned_descriptor as _read_pinned_descriptor,
        stable_file_identity as _stable_file_identity,
    )
    from .raw_tree_guard import contains_raw_segments
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "export_members"
    )
    from export_contract import ExportError
    from export_members_auth import (
        AuthenticationDependencies as _AuthenticationDependencies,
        AuthenticationRequest as _AuthenticationRequest,
        authenticate_descriptor as _authenticate_descriptor,
    )
    from export_members_jsonl import (
        lf_jsonl_documents as _lf_jsonl_documents,
        lf_jsonl_lines as _lf_jsonl_lines,
    )
    from export_members_path import (
        compose_member_path as _compose_member_path,
        is_under_raw as _is_under_raw,
        member_relative as _member_relative,
        require_exact_directory as _require_exact_directory,
        require_inside_root as _require_inside_root,
        require_unique_regular as _require_unique_regular,
    )
    from export_members_read import (
        read_exact_regular_file as _read_exact_regular_file,
        read_pinned_descriptor as _read_pinned_descriptor,
        stable_file_identity as _stable_file_identity,
    )
    from raw_tree_guard import contains_raw_segments

# Compatibility alias retained for ``export_hf`` and pre-split callers.
_contains_raw_segments = contains_raw_segments


def _authenticated_descriptor(
    curated_root: Path,
    summary: dict[str, Any],
    key: str,
    expected_path: str,
) -> tuple[dict[str, Any], list[Any]]:
    """Authenticate through the compatibility facade's call-time seams."""
    return _authenticate_descriptor(
        _AuthenticationRequest(curated_root, summary, key, expected_path),
        _AuthenticationDependencies(
            _read_exact_regular_file,
            _lf_jsonl_documents,
        ),
    )


__all__ = [
    "ExportError",
    "_authenticated_descriptor",
    "_compose_member_path",
    "_contains_raw_segments",
    "_is_under_raw",
    "_lf_jsonl_documents",
    "_lf_jsonl_lines",
    "_member_relative",
    "_read_exact_regular_file",
    "_read_pinned_descriptor",
    "_require_exact_directory",
    "_require_inside_root",
    "_require_unique_regular",
    "_stable_file_identity",
    "iter_alias_free_jsonl",
]


def _scanned_snapshot_entries(directory: Path, label: str) -> list[os.DirEntry]:
    """List one directory's entries in stable name order, failing closed."""

    try:
        with os.scandir(directory) as scan:
            return sorted(scan, key=lambda entry: entry.name)
    except OSError as exc:
        raise ExportError(f"{label}: cannot enumerate {directory}: {exc}") from exc


def _entry_metadata(entry: os.DirEntry, label: str) -> os.stat_result:
    """Inspect one tree entry without following a symlink."""

    try:
        return entry.stat(follow_symlinks=False)
    except OSError as exc:
        raise ExportError(f"{label}: cannot inspect {entry.path}: {exc}") from exc


def _jsonl_entry_action(entry: os.DirEntry, metadata: os.stat_result, label: str) -> str:
    """Classify a JSONL-named entry, requiring one exact regular file."""

    if not stat.S_ISREG(metadata.st_mode):
        raise ExportError(f"{label}: JSONL entry is not an exact regular file: {entry.path}")
    return "member"


def _ordinary_entry_action(metadata: os.stat_result) -> str:
    """Classify a non-JSONL entry as a directory or ignored file."""

    return "descend" if stat.S_ISDIR(metadata.st_mode) else "ignore"


def _classified_snapshot_entry(entry: os.DirEntry, label: str) -> str:
    """Classify one alias-free tree entry for snapshot traversal."""

    metadata = _entry_metadata(entry, label)
    if stat.S_ISLNK(metadata.st_mode):
        raise ExportError(f"{label}: tree contains a symlink alias: {entry.path}")
    if entry.name.endswith(".jsonl"):
        return _jsonl_entry_action(entry, metadata, label)
    return _ordinary_entry_action(metadata)


def _record_snapshot_entry(
    entry: os.DirEntry, action: str, pending: list[Path], members: list[Path]
) -> None:
    """Record one classified entry in the traversal's matching collection."""

    if action == "descend":
        pending.append(Path(entry.path))
        return
    if action == "member":
        members.append(Path(entry.path))


def iter_alias_free_jsonl(root: Path, label: str) -> list[Path]:
    """Enumerate every JSONL under ``root`` while refusing symlink entries."""

    members: list[Path] = []
    pending = [Path(root)]
    while pending:
        for entry in _scanned_snapshot_entries(pending.pop(), label):
            action = _classified_snapshot_entry(entry, label)
            _record_snapshot_entry(entry, action, pending, members)
    return sorted(members)


if __package__:
    _expose_package_sibling(__name__)
