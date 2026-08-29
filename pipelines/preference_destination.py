#!/usr/bin/env python3
"""Where a curated preference run may be written, and how the file is made.

One responsibility: deciding that a destination is safe to create, and then
creating it atomically or not at all. Nothing here knows what a preference
pair is, so this module sits strictly below curation and imports nothing
from it.

Three refusals, all fail-closed:

* ``outputs/raw/`` is immutable evidence. A destination that names or
  aliases it -- through a symlink, a bind mount, or a shared inode -- is
  refused before any file is opened, and again after the parent directory
  is pinned open, so a directory swapped between the two checks cannot land
  a write inside the raw tree.
* An existing path is never clobbered, and a missing parent is an error
  rather than an implicit mkdir.
* A destination may not replace its own source, or sit inside it.

Creation pins the parent directory with ``O_DIRECTORY|O_NOFOLLOW`` and
creates the file with ``O_EXCL`` relative to that descriptor, so the path
that was checked is the path that is written.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

_PIPELINES = Path(__file__).resolve().parent
if str(_PIPELINES) not in sys.path:
    sys.path.insert(0, str(_PIPELINES))

try:
    from pipelines.raw_tree_guard import is_under_raw as _guard_is_under_raw
except ImportError:  # python3 pipelines/preference_destination.py
    from raw_tree_guard import is_under_raw as _guard_is_under_raw

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
RAW_OUTPUT_ROOT = REPOSITORY_ROOT / "outputs" / "raw"


class PreferenceCurationError(RuntimeError):
    """Raised when source or destination handling would be unsafe."""


def _is_under_raw(path: Path) -> bool:
    """Whether ``path`` names or aliases the repository's raw output tree."""

    return _guard_is_under_raw(path, RAW_OUTPUT_ROOT)


def _refuse_raw_destination(destination: Path, label: str) -> None:
    if not _is_under_raw(destination):
        return
    # A file source has no directory to nest inside, and a directory source
    # does not contain its own siblings, so the remaining destination checks
    # cannot keep a curated write out of the immutable raw tree on their own.
    raise PreferenceCurationError(
        f"{label} would write inside immutable raw evidence: {destination}"
    )


def _refuse_existing_destination(destination: Path, label: str) -> None:
    if destination.exists():
        raise PreferenceCurationError(
            f"{label} already exists; refusing overwrite: {destination}"
        )
    if destination.parent.is_dir():
        return
    raise PreferenceCurationError(
        f"{label} parent does not exist: {destination.parent}"
    )


def _destination_replaces_source(source: Path, destination: Path) -> bool:
    return source.resolve() == destination.resolve(strict=False)


def _destination_inside_source(source: Path, destination: Path) -> bool:
    if not source.is_dir():
        return False
    return source.resolve() in destination.resolve(strict=False).parents


def _refuse_source_collision(source: Path, destination: Path, label: str) -> None:
    if _destination_replaces_source(source, destination):
        raise PreferenceCurationError(f"{label} cannot replace source: {destination}")
    if not _destination_inside_source(source, destination):
        return
    raise PreferenceCurationError(
        f"{label} cannot be written inside source: {destination}"
    )


def _assert_new_destination(source: Path, destination: Path, label: str) -> None:
    _refuse_raw_destination(destination, label)
    _refuse_existing_destination(destination, label)
    _refuse_source_collision(source, destination, label)


def _open_destination_parent(path: Path) -> int:
    flags = os.O_RDONLY | os.O_DIRECTORY | getattr(os, "O_NOFOLLOW", 0)
    try:
        return os.open(path.parent, flags)
    except OSError as exc:
        raise PreferenceCurationError(
            f"destination parent is not a pinned directory: {path.parent}"
        ) from exc


def _refuse_opened_parent(parent_fd: int, destination: Path) -> None:
    try:
        opened = Path(os.readlink(f"/proc/self/fd/{parent_fd}"))
    except OSError:
        opened = destination.parent
    _refuse_raw_destination(opened, "destination")
    _refuse_raw_destination(opened / destination.name, "destination")


def _create_exclusive_file(path: Path, payload: str, created: list[Path]) -> None:
    parent_fd = _open_destination_parent(path)
    try:
        _refuse_opened_parent(parent_fd, path)
        descriptor = os.open(
            path.name,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL,
            0o644,
            dir_fd=parent_fd,
        )
    finally:
        os.close(parent_fd)
    created.append(path)
    with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())


def _fsync_parents(paths: list[Path]) -> None:
    # Durable file contents still need a durable directory entry.
    for directory in dict.fromkeys(path.parent for path in paths):
        directory_descriptor = os.open(directory, os.O_RDONLY)
        try:
            os.fsync(directory_descriptor)
        finally:
            os.close(directory_descriptor)


def _unlink_created(created: list[Path]) -> None:
    # Remove only files this invocation created; pre-existing paths are
    # rejected before and during O_EXCL creation.
    for path in created:
        try:
            path.unlink()
        except FileNotFoundError:
            pass
