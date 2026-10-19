#!/usr/bin/env python3
"""Write a family run into a destination that must not already exist.

Every generator family (``crp``, ``code_leftover3``, ``ttf``, ``nelb``, ``ffpc``,
``maos``, ``pkg``) writes its batch and notes files with the same guards: refuse
a destination that names or aliases ``outputs/raw/``, refuse an existing path,
pin the parent directory by descriptor, create each file ``O_EXCL`` against the
pinned directory, and unlink a partial tree on any failure (including Ctrl-C).
Only the refusal type differs per family, so the family hands in its own
``refuse`` / ``refuse_when`` primitives and this module carries the single copy
of the file-system logic.
"""

from __future__ import annotations

import os
from collections.abc import Callable
from dataclasses import dataclass, replace
from pathlib import Path
from typing import NoReturn

if __name__.startswith("pipelines."):
    from ..oracle_grounded.import_twins import bind_import_twin
else:
    from oracle_grounded.import_twins import bind_import_twin

FINDING_DESTINATION_EXISTS = "DESTINATION_EXISTS"
FINDING_DESTINATION_UNDER_RAW = "DESTINATION_UNDER_RAW"

__all__ = [
    "Guards",
    "bind",
    "check_destination",
    "fsync_destination",
    "write_run",
]

_DIR_FLAGS = os.O_RDONLY | os.O_DIRECTORY | getattr(os, "O_NOFOLLOW", 0)


@dataclass(frozen=True)
class Guards:
    """A family's refusal primitives and raw-tree predicate."""

    refuse: Callable[[str, str], NoReturn]
    refuse_when: Callable[[bool, str, str], None]
    is_under_raw: Callable[[Path], bool]
    fsync: Callable[[int, int], None] | None = None


@dataclass(frozen=True)
class _CreatedFile:
    """A file this invocation created, addressed by its pinned parent."""

    parent_fd: int
    name: str


def check_destination(guards: Guards, out_dir: Path) -> None:
    """Refuse a raw-tree or already-existing destination before any write."""

    guards.refuse_when(
        guards.is_under_raw(out_dir),
        FINDING_DESTINATION_UNDER_RAW,
        f"{out_dir} names or aliases the raw tree",
    )
    guards.refuse_when(
        out_dir.exists(), FINDING_DESTINATION_EXISTS, f"{out_dir} already exists"
    )


def fsync_destination(dest_fd: int, parent_fd: int) -> None:
    os.fsync(dest_fd)
    os.fsync(parent_fd)


def _opened_path(fd: int, fallback: Path) -> Path:
    try:
        return Path(os.readlink(f"/proc/self/fd/{fd}"))
    except OSError:
        return fallback


def _refuse_raw_path(guards: Guards, path: Path, origin: Path) -> None:
    guards.refuse_when(
        guards.is_under_raw(path),
        FINDING_DESTINATION_UNDER_RAW,
        f"{origin} names or aliases the raw tree",
    )


def _refuse_opened_parent(guards: Guards, parent_fd: int, destination: Path) -> None:
    opened = _opened_path(parent_fd, destination.parent)
    _refuse_raw_path(guards, opened, destination)
    _refuse_raw_path(guards, opened / destination.name, destination)


def _text_handle(descriptor: int):
    """Wrap ``descriptor`` in a text handle; close it here if wrapping fails, so it never leaks."""

    try:
        return os.fdopen(descriptor, "w", encoding="utf-8", newline="\n")
    except BaseException:
        os.close(descriptor)
        raise


def _create_exclusive_file(
    parent_fd: int, name: str, payload: str, created: list[_CreatedFile]
) -> None:
    descriptor = os.open(
        name,
        os.O_WRONLY | os.O_CREAT | os.O_EXCL,
        0o644,
        dir_fd=parent_fd,
    )
    created.append(_CreatedFile(parent_fd, name))
    with _text_handle(descriptor) as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())


def _unlink_created(created: list[_CreatedFile]) -> None:
    for entry in created:
        try:
            os.unlink(entry.name, dir_fd=entry.parent_fd)
        except FileNotFoundError:
            pass


def _rmdir_created(parent_fd: int, name: str) -> None:
    try:
        os.rmdir(name, dir_fd=parent_fd)
    except OSError:
        pass


def write_run(
    guards: Guards,
    out_dir: Path,
    files: tuple[tuple[str, str], ...],
) -> None:
    """Create ``out_dir`` and its files exclusively; unlink a partial tree."""

    out_dir.parent.mkdir(parents=True, exist_ok=True)
    parent_fd = os.open(out_dir.parent, _DIR_FLAGS)
    dest_fd = -1
    created: list[_CreatedFile] = []
    created_dir = False
    try:
        _refuse_opened_parent(guards, parent_fd, out_dir)
        try:
            os.mkdir(out_dir.name, dir_fd=parent_fd)
        except FileExistsError:
            guards.refuse(FINDING_DESTINATION_EXISTS, f"{out_dir} already exists")
        created_dir = True
        dest_fd = os.open(out_dir.name, _DIR_FLAGS, dir_fd=parent_fd)
        _refuse_raw_path(guards, _opened_path(dest_fd, out_dir), out_dir)
        for name, payload in files:
            _create_exclusive_file(dest_fd, name, payload, created)
        (guards.fsync or fsync_destination)(dest_fd, parent_fd)
    except BaseException:
        # Not `Exception`: a Ctrl-C during the payload write or the fsync
        # would otherwise leave a half-written destination behind, and the
        # next run refuses to overwrite it.
        _unlink_created(created)
        if created_dir:
            _rmdir_created(parent_fd, out_dir.name)
        raise
    finally:
        if dest_fd >= 0:
            os.close(dest_fd)
        os.close(parent_fd)


def bind(
    namespace: dict,
    guards: Guards,
    vendor_check: Callable[[tuple[Path, ...]], None] | None = None,
) -> tuple[Callable[[Path], None], Callable[..., None], Callable[[int, int], None]]:
    """Build a family's ``(_check_destination, _write_run, _fsync_destination)``.

    ``namespace`` is the family's ``generate`` module globals; the writer looks
    ``_fsync_destination`` up there on every call, so a test (or a family) that
    replaces it still intercepts the durability step.
    """

    def late_fsync(dest_fd: int, parent_fd: int) -> None:
        namespace["_fsync_destination"](dest_fd, parent_fd)

    bound = replace(guards, fsync=late_fsync)

    def check_family_destination(out_dir: Path) -> None:
        if vendor_check is not None:
            vendor_check((out_dir,))
        check_destination(bound, out_dir)

    def write_family_run(out_dir: Path, files: tuple[tuple[str, str], ...]) -> None:
        """Create ``out_dir`` and its files exclusively; unlink a partial tree."""
        write_run(bound, out_dir, files)

    return check_family_destination, write_family_run, fsync_destination


bind_import_twin(__name__)
