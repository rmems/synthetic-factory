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


def _open_canonical_directory(root: Path, *, label: str) -> int:
    """Open one canonical directory and bind callers to its verified inode."""

    root = Path(root)
    try:
        canonical_root = root.resolve(strict=True)
        path_stat = root.lstat()
    except OSError as exc:
        raise PreferenceArmsError(f"{label} cannot be resolved: {root}: {exc}") from exc
    if canonical_root != root:
        raise PreferenceArmsError(f"{label} is not canonical: {root}")
    if stat.S_ISLNK(path_stat.st_mode) or not stat.S_ISDIR(path_stat.st_mode):
        raise PreferenceArmsError(f"{label} is not a real directory: {root}")
    flags = os.O_RDONLY
    if hasattr(os, "O_DIRECTORY"):
        flags |= os.O_DIRECTORY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    directory_fd = -1
    try:
        directory_fd = os.open(root, flags)
        opened_stat = os.fstat(directory_fd)
        if not stat.S_ISDIR(opened_stat.st_mode) or not _same_file_identity(path_stat, opened_stat):
            raise PreferenceArmsError(f"{label} changed while it was opened: {root}")
        return directory_fd
    except BaseException:
        if directory_fd >= 0:
            os.close(directory_fd)
        raise


def _require_open_directory_identity(root: Path, root_fd: int, *, label: str) -> None:
    """Require the canonical pathname to still name the bound directory."""

    try:
        current_stat = Path(root).lstat()
        opened_stat = os.fstat(root_fd)
    except OSError as exc:
        raise PreferenceArmsError(f"{label} changed while open: {root}: {exc}") from exc
    if (
        stat.S_ISLNK(current_stat.st_mode)
        or not stat.S_ISDIR(current_stat.st_mode)
        or not _same_file_identity(current_stat, opened_stat)
    ):
        raise PreferenceArmsError(f"{label} changed while open: {root}")


def _read_regular_artifact_from_directory(
    root_fd: int,
    name: str,
    *,
    label: str,
    max_bytes: int | None = None,
) -> bytes:
    """Read one regular artifact relative to an already-bound directory."""

    if not isinstance(name, str) or Path(name).name != name:
        raise PreferenceArmsError(f"{label} name is not a safe basename: {name!r}")
    file_fd = -1
    try:
        file_stat = os.stat(name, dir_fd=root_fd, follow_symlinks=False)
        if stat.S_ISLNK(file_stat.st_mode) or not stat.S_ISREG(file_stat.st_mode):
            raise PreferenceArmsError(f"{label} is not a real file: {name}")
        if max_bytes is not None and file_stat.st_size > max_bytes:
            raise PreferenceArmsError(f"{label} exceeds the {max_bytes}-byte limit: {name}")
        flags = os.O_RDONLY
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        file_fd = os.open(name, flags, dir_fd=root_fd)
        opened_stat = os.fstat(file_fd)
        if not stat.S_ISREG(opened_stat.st_mode):
            raise PreferenceArmsError(f"{label} is not a real file: {name}")
        if not _same_file_identity(file_stat, opened_stat):
            raise PreferenceArmsError(f"{label} changed while it was opened: {name}")
        if max_bytes is not None and opened_stat.st_size > max_bytes:
            raise PreferenceArmsError(f"{label} exceeds the {max_bytes}-byte limit: {name}")
        with os.fdopen(file_fd, "rb") as handle:
            file_fd = -1
            payload = handle.read(None if max_bytes is None else max_bytes + 1)
        if max_bytes is not None and len(payload) > max_bytes:
            raise PreferenceArmsError(f"{label} exceeds the {max_bytes}-byte limit: {name}")
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
