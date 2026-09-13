#!/usr/bin/env python3
"""File-descriptor-bound reads that refuse symlinks and TOCTOU swaps."""

from __future__ import annotations

import os
import stat
from pathlib import Path

import sys

_PIPELINES = Path(__file__).resolve().parent
if str(_PIPELINES) not in sys.path:
    sys.path.insert(0, str(_PIPELINES))

from preference_arms_text import PreferenceArmsError  # noqa: E402


def _same_file_identity(left: os.stat_result, right: os.stat_result) -> bool:
    return (left.st_dev, left.st_ino) == (right.st_dev, right.st_ino)


def _is_real_directory(path_stat: os.stat_result) -> bool:
    """Report whether one stat record names a directory rather than a symlink."""

    return not stat.S_ISLNK(path_stat.st_mode) and stat.S_ISDIR(path_stat.st_mode)


def _is_real_file(path_stat: os.stat_result) -> bool:
    """Report whether one stat record names a regular file rather than a symlink."""

    return not stat.S_ISLNK(path_stat.st_mode) and stat.S_ISREG(path_stat.st_mode)


def _directory_open_flags() -> int:
    """Build the open flags that bind a directory without following a symlink."""

    flags = os.O_RDONLY
    if hasattr(os, "O_DIRECTORY"):
        flags |= os.O_DIRECTORY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    return flags


def _regular_file_open_flags() -> int:
    """Build the open flags that bind a regular file without following a symlink."""

    flags = os.O_RDONLY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    return flags


def _stat_canonical_directory(root: Path, *, label: str) -> os.stat_result:
    """Stat one directory pathname that must already be canonical and unfollowed."""

    try:
        canonical_root = root.resolve(strict=True)
        path_stat = root.lstat()
    except OSError as exc:
        raise PreferenceArmsError(f"{label} cannot be resolved: {root}: {exc}") from exc
    if canonical_root != root:
        raise PreferenceArmsError(f"{label} is not canonical: {root}")
    if not _is_real_directory(path_stat):
        raise PreferenceArmsError(f"{label} is not a real directory: {root}")
    return path_stat


def _is_opened_directory(path_stat: os.stat_result, opened_stat: os.stat_result) -> bool:
    """Report whether a just-opened descriptor still names the stat'ed directory."""

    return stat.S_ISDIR(opened_stat.st_mode) and _same_file_identity(path_stat, opened_stat)


def _open_canonical_directory(root: Path, *, label: str) -> int:
    """Open one canonical directory and bind callers to its verified inode."""

    root = Path(root)
    path_stat = _stat_canonical_directory(root, label=label)
    directory_fd = -1
    try:
        directory_fd = os.open(root, _directory_open_flags())
        opened_stat = os.fstat(directory_fd)
        if not _is_opened_directory(path_stat, opened_stat):
            raise PreferenceArmsError(f"{label} changed while it was opened: {root}")
        return directory_fd
    except BaseException:
        if directory_fd >= 0:
            os.close(directory_fd)
        raise


def _is_bound_directory(current_stat: os.stat_result, opened_stat: os.stat_result) -> bool:
    """Report whether a pathname still names the directory behind the bound descriptor."""

    return _is_real_directory(current_stat) and _same_file_identity(current_stat, opened_stat)


def _require_open_directory_identity(root: Path, root_fd: int, *, label: str) -> None:
    """Require the canonical pathname to still name the bound directory."""

    try:
        current_stat = Path(root).lstat()
        opened_stat = os.fstat(root_fd)
    except OSError as exc:
        raise PreferenceArmsError(f"{label} changed while open: {root}: {exc}") from exc
    if not _is_bound_directory(current_stat, opened_stat):
        raise PreferenceArmsError(f"{label} changed while open: {root}")


def _require_safe_basename(name: str, label: str) -> None:
    """Reject any artifact name that is not a plain basename."""

    if not isinstance(name, str) or Path(name).name != name:
        raise PreferenceArmsError(f"{label} name is not a safe basename: {name!r}")


def _require_regular_artifact(path_stat: os.stat_result, name: str, label: str) -> None:
    """Reject one artifact whose pathname does not name a regular file."""

    if not _is_real_file(path_stat):
        raise PreferenceArmsError(f"{label} is not a real file: {name}")


def _require_size_within_limit(size: int, name: str, label: str, max_bytes: int | None) -> None:
    """Reject one artifact whose byte count exceeds the caller's limit."""

    if max_bytes is not None and size > max_bytes:
        raise PreferenceArmsError(f"{label} exceeds the {max_bytes}-byte limit: {name}")


def _require_unswapped_artifact(
    file_stat: os.stat_result,
    opened_stat: os.stat_result,
    name: str,
    label: str,
) -> None:
    """Reject one just-opened artifact whose inode no longer matches the pathname."""

    if not stat.S_ISREG(opened_stat.st_mode):
        raise PreferenceArmsError(f"{label} is not a real file: {name}")
    if not _same_file_identity(file_stat, opened_stat):
        raise PreferenceArmsError(f"{label} changed while it was opened: {name}")


def _read_regular_artifact_from_directory(
    root_fd: int,
    name: str,
    *,
    label: str,
    max_bytes: int | None = None,
) -> bytes:
    """Read one regular artifact relative to an already-bound directory."""

    _require_safe_basename(name, label)
    file_fd = -1
    try:
        file_stat = os.stat(name, dir_fd=root_fd, follow_symlinks=False)
        _require_regular_artifact(file_stat, name, label)
        _require_size_within_limit(file_stat.st_size, name, label, max_bytes)
        file_fd = os.open(name, _regular_file_open_flags(), dir_fd=root_fd)
        opened_stat = os.fstat(file_fd)
        _require_unswapped_artifact(file_stat, opened_stat, name, label)
        _require_size_within_limit(opened_stat.st_size, name, label, max_bytes)
        with os.fdopen(file_fd, "rb") as handle:
            file_fd = -1
            payload = handle.read(None if max_bytes is None else max_bytes + 1)
        _require_size_within_limit(len(payload), name, label, max_bytes)
        return payload
    except PreferenceArmsError:
        raise
    except OSError as exc:
        raise PreferenceArmsError(f"{label} cannot be read: {name}: {exc}") from exc
    finally:
        if file_fd >= 0:
            os.close(file_fd)


def _read_regular_artifact(
    root: Path,
    name: str,
    *,
    label: str,
    max_bytes: int | None = None,
) -> bytes:
    root_fd = -1
    try:
        root_fd = _open_canonical_directory(root, label=f"{label} root")
        return _read_regular_artifact_from_directory(
            root_fd,
            name,
            label=label,
            max_bytes=max_bytes,
        )
    finally:
        if root_fd >= 0:
            os.close(root_fd)
