#!/usr/bin/env python3
"""Source-tree enumeration and round-transaction visibility for compose."""

from __future__ import annotations

import os
import stat
import sys
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Callable

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("compose_source_snapshot_visibility")
    from .compose_contract import ComposeError
    from .compose_destination_binding import _require_exact_directory
    from .compose_source_snapshot_members import _source_member_path
    from .round_txn import committed_jsonl_paths, marker_mode_path
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "compose_source_snapshot_visibility"
    )
    from compose_contract import ComposeError
    from compose_destination_binding import _require_exact_directory
    from compose_source_snapshot_members import _source_member_path
    from round_txn import committed_jsonl_paths, marker_mode_path

RoundVisibilityFilter = Callable[[Path, list[str]], list[str]]


def _scan_source_directory(directory: Path) -> list[Any]:
    """List one source directory in a stable, name-sorted order."""

    try:
        with os.scandir(directory) as scan:
            return sorted(scan, key=lambda entry: entry.name)
    except OSError as exc:
        raise ComposeError(f"cannot enumerate source directory {directory}: {exc}") from exc


def _source_entry_metadata(entry: Any, path: Path) -> os.stat_result:
    """Stat one source entry without following, or accepting, an alias."""

    try:
        metadata = entry.stat(follow_symlinks=False)
    except OSError as exc:
        raise ComposeError(f"cannot inspect source member {path}: {exc}") from exc
    if stat.S_ISLNK(metadata.st_mode):
        raise ComposeError(f"source tree contains a symlink alias: {path}")
    return metadata


def _collect_source_directory(
    root: Path, directory: Path, members: list[str]
) -> list[Path]:
    """Append this directory's JSONL members; return its child directories."""

    child_directories: list[Path] = []
    for entry in _scan_source_directory(directory):
        path = Path(entry.path)
        metadata = _source_entry_metadata(entry, path)
        if entry.name.endswith(".jsonl"):
            relative = path.relative_to(root).as_posix()
            _source_member_path(root, relative, f"compose source {relative}")
            members.append(relative)
        elif stat.S_ISDIR(metadata.st_mode):
            child_directories.append(path)
    return child_directories


def _enclosing_marker_root(
    root: Path,
    parent: Path,
    marker_roots: dict[Path, Path | None],
) -> Path | None:
    """Return and memoize the nearest enclosing marker-mode directory."""

    visited = []
    current = parent
    while current not in marker_roots:
        visited.append(current)
        if marker_mode_path(current) is not None:
            found = current
            break
        if current in {root, current.parent}:
            found = None
            break
        current = current.parent
    else:
        found = marker_roots[current]
    for directory in visited:
        marker_roots[directory] = found
    return found


def _committed_paths(
    marker_root: Path,
    committed: dict[Path, set[Path]],
) -> set[Path]:
    """Return and memoize committed JSONL paths below one marker root."""

    if marker_root not in committed:
        committed[marker_root] = {
            candidate.resolve() for candidate in committed_jsonl_paths(marker_root)
        }
    return committed[marker_root]


@dataclass(frozen=True)
class RoundVisibilityHooks:
    """Facade-selected lookups for round-transaction visibility."""

    enclosing_marker_root: Callable[..., Path | None]
    committed_paths: Callable[..., set[Path]]


def round_visible_members(
    root: Path,
    members: list[str],
    hooks: RoundVisibilityHooks,
) -> list[str]:
    """Keep only members exposed by the round-transaction contract."""

    marker_roots: dict[Path, Path | None] = {}
    committed: dict[Path, set[Path]] = {}
    visible: list[str] = []
    for relative in members:
        path = root.joinpath(*PurePosixPath(relative).parts)
        marker_root = hooks.enclosing_marker_root(root, path.parent, marker_roots)
        if marker_root is None:
            visible.append(relative)
            continue
        if path.resolve() in hooks.committed_paths(marker_root, committed):
            visible.append(relative)
    return visible


def source_jsonl_members(
    root: Path,
    visible_members: RoundVisibilityFilter,
) -> tuple[str, ...]:
    """Enumerate a source tree without following filesystem aliases."""

    root = _require_exact_directory(root, "source run")
    members: list[str] = []
    pending = [root]
    while pending:
        directory = pending.pop()
        if _require_exact_directory(directory, "source directory") != directory:
            raise ComposeError(f"source directory identity changed: {directory}")
        child_directories = _collect_source_directory(root, directory, members)
        pending.extend(reversed(child_directories))
    return tuple(sorted(visible_members(root, members)))


if __package__:
    _expose_package_sibling(__name__)
