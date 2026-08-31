"""Exclusive destination writes for tag curation."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from tag_constants import RAW_OUTPUT_ROOT
from tag_jsonutil import canonical_json

try:
    from pipelines.raw_tree_guard import is_under_raw as _is_under_raw_tree
except ImportError:
    from raw_tree_guard import is_under_raw as _is_under_raw_tree


def _is_under_raw(path: Path) -> bool:
    return _is_under_raw_tree(path, RAW_OUTPUT_ROOT)


def _raw_write_error(path: Path) -> ValueError:
    return ValueError(f"refusing to write inside immutable raw evidence: {path}")


def _unlink_created_file(path: Path, identity: tuple[int, int]) -> None:
    """Remove ``path`` only when it still names the file this run created."""
    try:
        current = path.lstat()
    except FileNotFoundError:
        return
    if (current.st_dev, current.st_ino) == identity:
        path.unlink()


def _fd_realpath(fd: int) -> Path:
    return Path(os.readlink(f"/proc/self/fd/{fd}"))


def _reject_raw_location(path: Path, origin: Path) -> None:
    if _is_under_raw(path):
        raise _raw_write_error(origin)


def _open_parent_directory(path: Path) -> int:
    parent = path.parent
    parent.mkdir(parents=True, exist_ok=True)
    _reject_raw_location(parent, path)
    _reject_raw_location(parent.resolve(strict=False), path)
    return os.open(parent, os.O_RDONLY | os.O_DIRECTORY)


def _stat_identity(fd: int) -> tuple[int, int]:
    state = os.fstat(fd)
    return state.st_dev, state.st_ino


def _close_and_unlink(descriptor: int, path: Path, identity: tuple[int, int]) -> None:
    try:
        created = _fd_realpath(descriptor)
    except OSError:
        created = path
    os.close(descriptor)
    _unlink_created_file(created, identity)
    _unlink_created_file(path, identity)


def _create_exclusive(parent_fd: int, path: Path) -> int:
    try:
        return os.open(
            path.name,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL,
            0o644,
            dir_fd=parent_fd,
        )
    except FileExistsError as exc:
        raise FileExistsError(
            f"refusing to replace existing destination: {path}"
        ) from exc


def _guard_created(descriptor: int, path: Path) -> tuple[int, tuple[int, int]]:
    identity = _stat_identity(descriptor)
    try:
        _reject_raw_location(_fd_realpath(descriptor), path)
    except ValueError:
        _close_and_unlink(descriptor, path, identity)
        raise
    return descriptor, identity


def _open_exclusive(path: Path) -> tuple[int, tuple[int, int]]:
    parent_fd = _open_parent_directory(path)
    try:
        _reject_raw_location(_fd_realpath(parent_fd), path)
        descriptor = _create_exclusive(parent_fd, path)
    finally:
        os.close(parent_fd)
    return _guard_created(descriptor, path)


def _write_jsonl_lines(descriptor: int, values: list[dict[str, Any]]) -> None:
    with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
        for value in values:
            handle.write(canonical_json(value))
            handle.write("\n")


def _write_new_jsonl(
    path: Path, values: list[dict[str, Any]]
) -> tuple[Path, tuple[int, int]]:
    """Write one JSONL file without replacing any pre-existing path."""
    _reject_raw_location(path, path)
    descriptor, identity = _open_exclusive(path)
    try:
        created = _fd_realpath(descriptor)
    except OSError:
        created = path
    try:
        _write_jsonl_lines(descriptor, values)
    except BaseException:
        _unlink_created_file(created, identity)
        raise
    return created, identity


def _prepare_destination_parents(
    destinations: list[tuple[Path, list[dict[str, Any]]]],
) -> None:
    for path, _values in destinations:
        path.parent.mkdir(parents=True, exist_ok=True)
        _reject_raw_location(path, path)
        _reject_raw_location(path.parent, path)
