#!/usr/bin/env python3
"""Low-level descriptor operations for exclusive compose destination writes."""

from __future__ import annotations

import os
import stat
from pathlib import PurePosixPath
from typing import Any

from compose_contract import ComposeError
from compose_destination_binding import _directory_identity


def _unsafe_destination_component(candidate: PurePosixPath) -> bool:
    """Whether a normalized destination path contains traversal components."""

    return any(part in {"", ".", ".."} for part in candidate.parts)


def _destination_path_text(relative: Any) -> Any:
    """Normalize the supported pure-path input without validating it yet."""

    if isinstance(relative, PurePosixPath):
        return relative.as_posix()
    return relative


def _require_destination_text(raw: Any, label: str) -> str:
    if not isinstance(raw, str):
        raise ComposeError(f"{label}: destination path must be a nonempty POSIX string")
    if not raw:
        raise ComposeError(f"{label}: destination path must be a nonempty POSIX string")
    return raw


def _reject_destination_separator(raw: str, label: str) -> None:
    if "\\" in raw:
        raise ComposeError(f"{label}: destination path must be a nonempty POSIX string")


def _reject_unsafe_destination_text(raw: str, label: str) -> None:
    if "\0" in raw:
        raise ComposeError(f"{label}: unsafe destination path {raw!r}")


def _require_canonical_destination(
    candidate: PurePosixPath, raw: str, label: str
) -> None:
    if candidate.as_posix() != raw:
        raise ComposeError(f"{label}: unsafe destination path {raw!r}")
    if candidate.is_absolute():
        raise ComposeError(f"{label}: unsafe destination path {raw!r}")
    if _unsafe_destination_component(candidate):
        raise ComposeError(f"{label}: unsafe destination path {raw!r}")


def _destination_write_parts(relative: Any, label: str) -> tuple[str, ...]:
    """Validate one destination-relative POSIX path used for a new file."""

    raw = _require_destination_text(_destination_path_text(relative), label)
    _reject_destination_separator(raw, label)
    _reject_unsafe_destination_text(raw, label)
    candidate = PurePosixPath(raw)
    _require_canonical_destination(candidate, raw, label)
    return candidate.parts


def _create_child_directory(parent_descriptor: int, name: str, label: str) -> bool:
    """Create one component and report whether this call created it."""

    try:
        os.mkdir(name, 0o755, dir_fd=parent_descriptor)
    except FileExistsError:
        return False
    except OSError as exc:
        raise ComposeError(
            f"{label}: cannot create directory component {name!r}: {exc}"
        ) from exc
    return True


def _open_child_directory_entry(
    parent_descriptor: int, name: str, label: str
) -> int:
    """Open one exact directory entry without following links."""

    flags = (
        os.O_RDONLY
        | getattr(os, "O_DIRECTORY", 0)
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_CLOEXEC", 0)
    )
    try:
        return os.open(name, flags, dir_fd=parent_descriptor)
    except OSError as exc:
        raise ComposeError(
            f"{label}: directory component {name!r} is not an exact directory"
        ) from exc


def _remove_created_directory(parent_descriptor: int, name: str) -> None:
    """Best-effort rollback for a directory created through a pinned parent."""

    try:
        os.rmdir(name, dir_fd=parent_descriptor)
    except OSError:
        pass


def _remove_created_file(parent_descriptor: int, name: str) -> None:
    """Best-effort rollback for a file created through a pinned parent."""

    try:
        os.unlink(name, dir_fd=parent_descriptor)
    except OSError:
        pass


def _rollback_child_directory(
    created: bool, parent_descriptor: int, name: str
) -> None:
    """Remove a failed component only when this call created it."""

    if created:
        _remove_created_directory(parent_descriptor, name)


def _verify_pinned_child(
    descriptor: int, parent_descriptor: int, name: str, label: str
) -> None:
    """Require the opened child and its entry to be one directory."""

    entry = os.stat(name, dir_fd=parent_descriptor, follow_symlinks=False)
    opened = os.fstat(descriptor)
    if not stat.S_ISDIR(entry.st_mode):
        raise ComposeError(
            f"{label}: directory component {name!r} changed while it was pinned"
        )
    if not stat.S_ISDIR(opened.st_mode):
        raise ComposeError(
            f"{label}: directory component {name!r} changed while it was pinned"
        )
    if _directory_identity(entry) != _directory_identity(opened):
        raise ComposeError(
            f"{label}: directory component {name!r} changed while it was pinned"
        )


def _open_pinned_child_directory(
    parent_descriptor: int, name: str, label: str
) -> tuple[int, bool]:
    """Create or reuse one child directory and pin it without links."""

    created = _create_child_directory(parent_descriptor, name, label)
    try:
        descriptor = _open_child_directory_entry(parent_descriptor, name, label)
    except BaseException:
        _rollback_child_directory(created, parent_descriptor, name)
        raise
    try:
        _verify_pinned_child(descriptor, parent_descriptor, name, label)
    except BaseException:
        os.close(descriptor)
        _rollback_child_directory(created, parent_descriptor, name)
        raise
    return descriptor, created


def _open_new_leaf(parent_descriptor: int, leaf: str, label: str) -> int:
    """Exclusively open one exact destination leaf under a pinned parent."""

    flags = (
        os.O_WRONLY
        | os.O_CREAT
        | os.O_EXCL
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_CLOEXEC", 0)
    )
    try:
        return os.open(leaf, flags, 0o644, dir_fd=parent_descriptor)
    except OSError as exc:
        raise ComposeError(f"{label}: cannot create new file {leaf!r}: {exc}") from exc


def _write_all(descriptor: int, payload: bytes) -> None:
    """Write all bytes to one already-opened regular destination leaf."""

    written = 0
    while written < len(payload):
        written += os.write(descriptor, payload[written:])
