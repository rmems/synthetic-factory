#!/usr/bin/env python3
"""Pinned-descriptor byte capture for exact export members."""

from __future__ import annotations

import os
import sys
from pathlib import Path, PurePosixPath
from typing import Any

if __package__:
    from . import _expose_package_sibling, _local_sibling_module, _require_local_sibling

    if _local_sibling_module("export_members_read", allow_initializing=True):
        import export_members_read as _direct_export_members_read

        _require_local_sibling(_direct_export_members_read, "export_members_read")
        del _direct_export_members_read
    from .export_contract import ExportError
    from .export_members_path import compose_member_path, is_unique_regular
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "export_members_read"
    )
    from export_contract import ExportError
    from export_members_path import compose_member_path, is_unique_regular

_READ_CHUNK_SIZE = 1024 * 1024


def stable_file_identity(metadata: os.stat_result) -> tuple[int, ...]:
    """Return fields that must remain unchanged across an exact read."""

    return (
        metadata.st_dev,
        metadata.st_ino,
        metadata.st_mode,
        metadata.st_nlink,
        metadata.st_size,
        metadata.st_mtime_ns,
        metadata.st_ctime_ns,
    )


def _open_pinned_descriptor(path: Path, raw_path: Any, label: str) -> int:
    """Open a member without following links or blocking on a FIFO swap."""

    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | os.O_NONBLOCK
    try:
        return os.open(path, flags)
    except OSError as exc:
        raise ExportError(
            f"{label}: cannot open exact regular file {raw_path!r}: {exc}"
        ) from exc


def _require_opened_regular(opened: os.stat_result, label: str) -> None:
    """Refuse a descriptor that does not name one unique regular file."""

    if not is_unique_regular(opened):
        raise ExportError(f"{label}: opened identity is not a unique regular file")


def _require_same_identity(
    expected: os.stat_result, actual: os.stat_result, message: str
) -> None:
    """Require two observations to name an unchanged file identity."""

    if stable_file_identity(expected) != stable_file_identity(actual):
        raise ExportError(message)


def _read_descriptor_bytes(descriptor: int) -> bytes:
    """Read one pinned descriptor to EOF in bounded chunks."""

    chunks: list[bytes] = []
    while chunk := os.read(descriptor, _READ_CHUNK_SIZE):
        chunks.append(chunk)
    return b"".join(chunks)


def _capture_descriptor(
    descriptor: int, before: os.stat_result, label: str
) -> tuple[os.stat_result, bytes]:
    """Capture bytes while proving the descriptor identity stays stable."""

    opened = os.fstat(descriptor)
    _require_opened_regular(opened, label)
    _require_same_identity(
        before, opened, f"{label}: path identity changed while opening"
    )
    payload = _read_descriptor_bytes(descriptor)
    _require_same_identity(
        opened,
        os.fstat(descriptor),
        f"{label}: source identity changed while reading",
    )
    return opened, payload


def read_pinned_descriptor(
    path: Path, before: os.stat_result, raw_path: Any, label: str
) -> tuple[os.stat_result, bytes]:
    """Open without following links, validate the descriptor, and read it."""

    descriptor = _open_pinned_descriptor(path, raw_path, label)
    try:
        return _capture_descriptor(descriptor, before, label)
    finally:
        os.close(descriptor)


def _resolved_after_read(root: Path, path: Path, raw_path: Any, label: str) -> bool:
    """Return whether resolution still matches the originally declared path."""

    try:
        resolved_path = path.resolve(strict=True)
        expected_path = root.resolve(strict=True).joinpath(
            *PurePosixPath(str(raw_path)).parts
        )
    except (OSError, RuntimeError) as exc:
        raise ExportError(f"{label}: cannot resolve file after reading") from exc
    return resolved_path == expected_path


def read_exact_regular_file(root: Path, raw_path: Any, label: str) -> tuple[Path, bytes]:
    """Read one path through a pinned descriptor and reject identity changes."""

    path = compose_member_path(root, raw_path, label)
    before = path.lstat()
    opened, payload = read_pinned_descriptor(path, before, raw_path, label)
    _require_same_identity(
        opened,
        path.lstat(),
        f"{label}: path identity changed while reading",
    )
    if not _resolved_after_read(root, path, raw_path, label):
        raise ExportError(f"{label}: path became a symlink alias while reading")
    return path, payload


if __package__:
    _expose_package_sibling(__name__)
