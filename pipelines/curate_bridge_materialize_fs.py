#!/usr/bin/env python3
"""Filesystem safety primitives for atomic Bridge materialization."""

from __future__ import annotations

import ctypes
import errno
import os
import sys
from collections.abc import Iterable
from pathlib import Path


_AT_FDCWD = -100
_RENAME_NOREPLACE = 1


class BridgeCurationError(ValueError):
    """The curation input or source-root contract is invalid."""


def _is_under_raw(path: Path) -> bool:
    parts = path.resolve(strict=False).parts
    return ("outputs", "raw") in zip(parts, parts[1:])


def _unsafe_relative_path(path: Path) -> bool:
    if path.is_absolute() or bool(path.anchor):
        return True
    if not path.parts:
        return True
    return ".." in path.parts


def _safe_relative_path(value: str, *, label: str) -> Path:
    path = Path(value)
    if _unsafe_relative_path(path):
        raise BridgeCurationError(f"{label} must be a safe relative path: {value!r}")
    return path


def _manifest_path(name: str) -> Path:
    relative = _safe_relative_path(name, label="manifest_name")
    if relative.suffix != ".json":
        raise BridgeCurationError("manifest_name must end in .json")
    return relative


def _materialization_sources(
    sources: Iterable[str | Path],
    root_resolved: Path,
) -> list[Path]:
    source_paths = list(map(Path, sources))
    for source in source_paths:
        if not source.is_file():
            raise BridgeCurationError(f"source must be a real JSONL file: {source}")
        if source.is_symlink():
            raise BridgeCurationError(f"source must be a real JSONL file: {source}")
        if not source.resolve(strict=True).is_relative_to(root_resolved):
            raise BridgeCurationError(f"source is outside source_root: {source}")
    return source_paths


def _write_exclusive(path: Path, payload: bytes) -> None:
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
    except BaseException:
        path.unlink(missing_ok=True)
        raise


def _rename_windows(source: Path, destination: Path) -> None:
    try:
        source.rename(destination)
    except FileExistsError as exc:
        raise BridgeCurationError(
            f"destination already exists; refusing overwrite: {destination}"
        ) from exc


def _rename_linux(source: Path, destination: Path) -> None:
    libc = ctypes.CDLL(None, use_errno=True)
    try:
        renameat2 = libc.renameat2
    except AttributeError as exc:
        raise BridgeCurationError(
            "atomic no-replace publication requires Linux renameat2 with RENAME_NOREPLACE"
        ) from exc
    renameat2.argtypes = [
        ctypes.c_int,
        ctypes.c_char_p,
        ctypes.c_int,
        ctypes.c_char_p,
        ctypes.c_uint,
    ]
    renameat2.restype = ctypes.c_int
    result = renameat2(
        _AT_FDCWD,
        os.fsencode(source),
        _AT_FDCWD,
        os.fsencode(destination),
        _RENAME_NOREPLACE,
    )
    if result == 0:
        return
    error = ctypes.get_errno()
    if error in {errno.EEXIST, errno.ENOTEMPTY}:
        raise BridgeCurationError(f"destination already exists; refusing overwrite: {destination}")
    raise BridgeCurationError(f"cannot atomically publish {destination}: {os.strerror(error)}")


def _rename_noreplace(source: Path, destination: Path) -> None:
    """Atomically publish ``source`` while refusing any existing destination."""

    if os.name == "nt":
        _rename_windows(source, destination)
        return
    if sys.platform != "linux":
        raise BridgeCurationError(
            f"atomic no-replace publication is unsupported on platform {sys.platform!r}"
        )
    _rename_linux(source, destination)


def _symlinked_ancestor(path: Path) -> Path | None:
    """Return the first lexical path component that is a symlink."""

    absolute = path.absolute()
    current = Path(absolute.anchor)
    for part in absolute.parts[1:]:
        current /= part
        if current.is_symlink():
            return current
    return None
