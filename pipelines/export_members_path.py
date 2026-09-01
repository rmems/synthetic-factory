#!/usr/bin/env python3
"""Canonical, alias-free filesystem paths for export members."""

from __future__ import annotations

import os
import stat
import sys
from pathlib import Path, PurePosixPath
from typing import Any

if __package__:
    from . import _expose_package_sibling, _local_sibling_module, _require_local_sibling

    if _local_sibling_module("export_members_path", allow_initializing=True):
        import export_members_path as _direct_export_members_path

        _require_local_sibling(_direct_export_members_path, "export_members_path")
        del _direct_export_members_path
    from .export_contract import ExportError
    from .raw_tree_guard import contains_raw_segments, is_under_raw as _guard_is_under_raw
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "export_members_path"
    )
    from export_contract import ExportError
    from raw_tree_guard import contains_raw_segments, is_under_raw as _guard_is_under_raw


def _resolved_non_strict(path: Path) -> Path:
    """Resolve a prospective path while normalizing filesystem failures."""

    try:
        return path.resolve(strict=False)
    except (OSError, RuntimeError) as exc:
        raise ExportError(f"cannot resolve path safely: {path}: {exc}") from exc


def is_under_raw(path: Path) -> bool:
    """Reject both a lexical raw path and a symlink-resolved destination."""

    if contains_raw_segments(path.parts):
        return True
    try:
        return _guard_is_under_raw(path)
    except (OSError, RuntimeError) as exc:
        raise ExportError(f"cannot resolve path safely: {path}: {exc}") from exc


def _is_member_path_text(raw_path: Any) -> bool:
    """Return whether a declaration has the required POSIX text shape."""

    return (
        isinstance(raw_path, str)
        and bool(raw_path)
        and "\\" not in raw_path
        and "\0" not in raw_path
    )


def _is_canonical_relative(relative: PurePosixPath, raw_path: str) -> bool:
    """Return whether parsing preserved one relative path exactly."""

    return relative.as_posix() == raw_path and not relative.is_absolute()


def _has_only_member_segments(relative: PurePosixPath) -> bool:
    """Return whether every path segment stays at or below its root."""

    return all(part not in {"", ".", ".."} for part in relative.parts)


def member_relative(raw_path: Any, label: str) -> PurePosixPath:
    """Validate one member path as a canonical, contained POSIX relative."""

    if not _is_member_path_text(raw_path):
        raise ExportError(f"{label}: path must be a nonempty POSIX string")
    relative = PurePosixPath(raw_path)
    if not _is_canonical_relative(relative, raw_path):
        raise ExportError(f"{label}: unsafe relative path {raw_path!r}")
    if not _has_only_member_segments(relative):
        raise ExportError(f"{label}: unsafe relative path {raw_path!r}")
    return relative


def _resolved_member(path: Path, raw_path: str, label: str) -> Path:
    """Resolve one declared member while preserving its evidence label."""

    try:
        return path.resolve(strict=True)
    except FileNotFoundError as exc:
        raise ExportError(f"{label}: declared file is missing: {raw_path}") from exc
    except (OSError, RuntimeError) as exc:
        raise ExportError(f"{label}: cannot resolve declared file: {raw_path}") from exc


def _is_exact_descendant(root: Path, resolved: Path, relative: PurePosixPath) -> bool:
    """Return whether resolution preserved the declared rooted identity."""

    expected = root.joinpath(*relative.parts)
    return resolved == expected and root in resolved.parents


def require_inside_root(
    curated_root: Path, candidate: Path, relative: PurePosixPath, label: str
) -> None:
    """Refuse a member whose resolution aliases or escapes its root."""

    raw_path = relative.as_posix()
    root_resolved = _resolved_member(curated_root, raw_path, label)
    resolved = _resolved_member(candidate, raw_path, label)
    if not _is_exact_descendant(root_resolved, resolved, relative):
        raise ExportError(f"{label}: path is a symlink alias or escapes its root: {raw_path}")


def _member_metadata(candidate: Path, raw_path: str, label: str) -> os.stat_result:
    """Inspect one member while normalizing a missing declaration."""

    try:
        return candidate.lstat()
    except FileNotFoundError as exc:
        raise ExportError(f"{label}: declared file is missing: {raw_path}") from exc
    except OSError as exc:
        raise ExportError(
            f"{label}: cannot inspect declared file: {raw_path}: {exc}"
        ) from exc


def is_unique_regular(metadata: os.stat_result) -> bool:
    """Return whether an identity is a regular file with no hard-link alias."""

    return stat.S_ISREG(metadata.st_mode) and metadata.st_nlink == 1


def require_unique_regular(candidate: Path, raw_path: str, label: str) -> None:
    """Refuse anything but a hard-link-free regular file at a member path."""

    metadata = _member_metadata(candidate, raw_path, label)
    if not stat.S_ISREG(metadata.st_mode):
        raise ExportError(f"{label}: path is not an exact regular file: {raw_path}")
    if metadata.st_nlink != 1:
        raise ExportError(f"{label}: hard-link aliases are not accepted: {raw_path}")


def compose_member_path(curated_root: Path, raw_path: Any, label: str) -> Path:
    """Resolve one exact regular COMPOSE member without aliases or escape."""

    relative = member_relative(raw_path, label)
    candidate = curated_root.joinpath(*relative.parts)
    require_inside_root(curated_root, candidate, relative, label)
    require_unique_regular(candidate, raw_path, label)
    return candidate


def _directory_metadata(path: Path, label: str) -> tuple[os.stat_result, Path]:
    """Inspect and resolve one required directory with contract errors."""

    try:
        return path.lstat(), path.resolve(strict=True)
    except FileNotFoundError as exc:
        raise ExportError(f"{label}: directory is missing: {path}") from exc
    except (OSError, RuntimeError) as exc:
        raise ExportError(f"{label}: cannot resolve directory: {path}") from exc


def _is_exact_directory(metadata: os.stat_result, resolved: Path, path: Path) -> bool:
    """Return whether the path directly names its real directory identity."""

    return stat.S_ISDIR(metadata.st_mode) and resolved == Path(os.path.abspath(path))


def require_exact_directory(path: Path, label: str) -> Path:
    """Require a real directory reached without a symlinked path alias."""

    metadata, resolved = _directory_metadata(path, label)
    if not _is_exact_directory(metadata, resolved, path):
        raise ExportError(f"{label}: directory path must be an exact non-symlink identity")
    return resolved


if __package__:
    _expose_package_sibling(__name__)
