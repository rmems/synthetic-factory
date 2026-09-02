#!/usr/bin/env python3
"""Low-level descriptor operations for exclusive compose destination writes."""

from __future__ import annotations

import os
import stat
import sys
from pathlib import PurePosixPath
from typing import Any

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("compose_destination_writer")
    from .compose_contract import ComposeError
    from .compose_destination_binding import (
        _directory_identity,
        _private_entry_name,
        _quarantine_owned_entry,
        _rename_noreplace,
        _require_empty_directory,
        _require_safe_new_directory,
    )
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "compose_destination_writer"
    )
    from compose_contract import ComposeError
    from compose_destination_binding import (
        _directory_identity,
        _private_entry_name,
        _quarantine_owned_entry,
        _rename_noreplace,
        _require_empty_directory,
        _require_safe_new_directory,
    )

_PRIVATE_CHILD_ATTEMPTS = 8


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


def _remove_created_directory_if_identity(
    parent_descriptor: int,
    name: str,
    expected_identity: tuple[int, int, int],
) -> None:
    """Best-effort rollback that never removes a different directory entry."""

    _quarantine_owned_entry(
        parent_descriptor,
        name,
        expected_identity,
        "destination directory rollback",
    )


def _remove_created_file_if_identity(
    parent_descriptor: int,
    name: str,
    expected_identity: tuple[int, int, int],
) -> None:
    """Best-effort rollback that never removes a different file entry."""

    _quarantine_owned_entry(
        parent_descriptor,
        name,
        expected_identity,
        "destination file rollback",
    )


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

    try:
        os.stat(name, dir_fd=parent_descriptor, follow_symlinks=False)
    except FileNotFoundError:
        return _create_and_publish_child_directory(parent_descriptor, name, label)
    except OSError as exc:
        raise ComposeError(
            f"{label}: cannot inspect directory component {name!r}: {exc}"
        ) from exc
    descriptor = _open_child_directory_entry(parent_descriptor, name, label)
    try:
        _verify_pinned_child(descriptor, parent_descriptor, name, label)
    except BaseException:
        os.close(descriptor)
        raise
    return descriptor, False


def _create_private_child(parent_descriptor: int, label: str) -> str:
    """Create an unpublished child with bounded no-replace name selection."""

    for _attempt in range(_PRIVATE_CHILD_ATTEMPTS):
        private_name = _private_entry_name("directory")
        try:
            os.mkdir(private_name, 0o755, dir_fd=parent_descriptor)
        except FileExistsError:
            continue
        except OSError as exc:
            raise ComposeError(f"{label}: cannot create private directory: {exc}") from exc
        return private_name
    raise ComposeError(f"{label}: cannot allocate a private directory name")


def _create_and_publish_child_directory(
    parent_descriptor: int,
    name: str,
    label: str,
) -> tuple[int, bool]:
    """Pin an empty private directory before atomically attaching its name."""

    private_name = _create_private_child(parent_descriptor, label)
    descriptor: int | None = None
    identity: tuple[int, int, int] | None = None
    try:
        identity = _directory_identity(
            os.stat(
                private_name,
                dir_fd=parent_descriptor,
                follow_symlinks=False,
            )
        )
        descriptor = _open_child_directory_entry(
            parent_descriptor,
            private_name,
            label,
        )
        _verify_pinned_child(
            descriptor,
            parent_descriptor,
            private_name,
            label,
        )
        _require_safe_new_directory(descriptor, parent_descriptor, label)
        _require_empty_directory(descriptor, label)
        try:
            _rename_noreplace(parent_descriptor, private_name, name)
        except OSError as exc:
            raise ComposeError(
                f"{label}: cannot publish directory component {name!r}: {exc}"
            ) from exc
        _verify_pinned_child(descriptor, parent_descriptor, name, label)
        return descriptor, True
    except BaseException:
        if descriptor is not None:
            os.close(descriptor)
        if identity is not None:
            candidate = name if _entry_has_identity(parent_descriptor, name, identity) else private_name
            _remove_created_directory_if_identity(
                parent_descriptor,
                candidate,
                identity,
            )
        raise


def _entry_has_identity(
    parent_descriptor: int,
    name: str,
    expected_identity: tuple[int, int, int],
) -> bool:
    try:
        metadata = os.stat(name, dir_fd=parent_descriptor, follow_symlinks=False)
    except OSError:
        return False
    return _directory_identity(metadata) == expected_identity


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


if __package__:
    _expose_package_sibling(__name__)
