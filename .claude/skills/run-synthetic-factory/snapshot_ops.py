#!/usr/bin/env python3
"""Snapshot machinery for the operator driver.

Copying a possibly-live run tree safely: no-follow descriptor copies, atomic
no-replace publication, and marker-visibility pruning so a snapshot never
crosses a transaction commit point. The driver keeps command dispatch; the
unsafe filesystem mechanics live here.
"""

from __future__ import annotations

import ctypes
import errno
import os
import shutil
import stat
import sys
import tempfile
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent
REPO = SKILL_DIR.parents[2]
PIPELINES = REPO / "pipelines"
if str(PIPELINES) not in sys.path:
    sys.path.insert(0, str(PIPELINES))

from round_txn import (  # noqa: E402
    TransactionError,
    committed_jsonl_paths,
    marker_mode_path,
)

AT_FDCWD = -100
RENAME_NOREPLACE = 1


def rename_snapshot_noreplace(src, dst):
    """Atomically publish a directory without replacing an existing path."""
    try:
        renameat2 = ctypes.CDLL(None, use_errno=True).renameat2
    except AttributeError as exc:
        raise TransactionError("atomic no-replace snapshot rename is unavailable") from exc
    renameat2.argtypes = (
        ctypes.c_int,
        ctypes.c_char_p,
        ctypes.c_int,
        ctypes.c_char_p,
        ctypes.c_uint,
    )
    renameat2.restype = ctypes.c_int
    if (
        renameat2(
            AT_FDCWD,
            os.fsencode(src),
            AT_FDCWD,
            os.fsencode(dst),
            RENAME_NOREPLACE,
        )
        == 0
    ):
        return
    error_number = ctypes.get_errno()
    if error_number in {errno.EEXIST, errno.ENOTEMPTY}:
        raise FileExistsError(error_number, os.strerror(error_number), dst)
    if error_number in {errno.EINVAL, errno.ENOSYS}:
        raise TransactionError("atomic no-replace snapshot rename is unavailable")
    raise OSError(error_number, os.strerror(error_number), f"{src} -> {dst}")


def reject_snapshot_symlinks(src):
    """Reject source trees whose snapshot would dereference external paths."""
    for path in src.rglob("*"):
        if path.is_symlink():
            raise TransactionError(f"cannot snapshot unsafe symlinked path: {path}")


def _open_snapshot_entry(entry, source_fd, source_path):
    """Open one scandir entry no-follow, translating failures to TransactionError."""
    try:
        return os.open(
            entry.name,
            os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW,
            dir_fd=source_fd,
        )
    except OSError as exc:
        raise TransactionError(
            f"cannot snapshot path safely: {source_path / entry.name}: {exc.strerror}"
        ) from exc


def _copy_snapshot_child_directory(entry_fd, entry_stat, entry_name, destination_fd, entry_path):
    """Recreate one directory entry and copy its subtree into it."""
    os.mkdir(entry_name, mode=0o700, dir_fd=destination_fd)
    child_destination_fd = os.open(
        entry_name,
        os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
        dir_fd=destination_fd,
    )
    try:
        _copy_snapshot_directory(entry_fd, child_destination_fd, entry_path)
        os.fchmod(child_destination_fd, stat.S_IMODE(entry_stat.st_mode))
    finally:
        os.close(child_destination_fd)


def _copy_snapshot_file(entry_fd, entry_stat, entry_name, destination_fd):
    """Copy one regular file's bytes and mode into the staged tree."""
    destination_file_fd = os.open(
        entry_name,
        os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
        mode=0o600,
        dir_fd=destination_fd,
    )
    with (
        os.fdopen(os.dup(entry_fd), "rb") as source_file,
        os.fdopen(destination_file_fd, "wb") as destination_file,
    ):
        shutil.copyfileobj(source_file, destination_file)
        os.fchmod(
            destination_file.fileno(),
            stat.S_IMODE(entry_stat.st_mode),
        )


def _copy_snapshot_entry(entry, source_fd, destination_fd, source_path):
    """Copy one scandir entry (dir or regular file) without following links."""
    entry_path = source_path / entry.name
    entry_fd = _open_snapshot_entry(entry, source_fd, source_path)
    try:
        entry_stat = os.fstat(entry_fd)
        if stat.S_ISDIR(entry_stat.st_mode):
            _copy_snapshot_child_directory(
                entry_fd, entry_stat, entry.name, destination_fd, entry_path
            )
        elif stat.S_ISREG(entry_stat.st_mode):
            _copy_snapshot_file(entry_fd, entry_stat, entry.name, destination_fd)
        else:
            raise TransactionError(f"cannot snapshot unsafe non-file path: {entry_path}")
    finally:
        os.close(entry_fd)


def _copy_snapshot_directory(source_fd, destination_fd, source_path):
    """Copy an opened directory without following source-side links."""
    with os.scandir(source_fd) as entries:
        for entry in entries:
            _copy_snapshot_entry(entry, source_fd, destination_fd, source_path)


def copy_snapshot_tree(src, dst):
    """Copy a tree through no-follow descriptors, then verify the result."""
    try:
        source_fd = os.open(src, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    except OSError as exc:
        raise TransactionError(f"cannot snapshot source safely: {src}: {exc.strerror}") from exc
    try:
        source_stat = os.fstat(source_fd)
        try:
            dst.mkdir(mode=0o700)
            destination_fd = os.open(dst, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        except OSError as exc:
            raise TransactionError(f"cannot stage snapshot safely: {dst}: {exc.strerror}") from exc
        try:
            _copy_snapshot_directory(source_fd, destination_fd, src)
            os.fchmod(destination_fd, stat.S_IMODE(source_stat.st_mode))
        finally:
            os.close(destination_fd)
    finally:
        os.close(source_fd)
    reject_snapshot_symlinks(dst)


def snapshot_to_temp(src, prefix, directory=None):
    reject_snapshot_symlinks(src)
    temp = tempfile.TemporaryDirectory(prefix=prefix, dir=directory)
    snap = Path(temp.name) / src.name
    try:
        copy_snapshot_tree(src, snap)
    except BaseException:
        temp.cleanup()
        raise
    return temp, snap


def marker_visible_jsonl_paths(run_dir):
    """Resolve marker visibility while the original staging layout is intact."""
    visible = {}
    for factory in run_dir.iterdir():
        if not factory.is_dir() or factory.is_symlink() or marker_mode_path(factory) is None:
            continue
        visible[factory.name] = {
            path.relative_to(factory) for path in committed_jsonl_paths(factory)
        }
    return visible


def prune_snapshot_to_marker_visibility(snapshot, visible_by_factory):
    """Remove JSONL that was not committed when the live snapshot began."""
    for factory_name, committed in visible_by_factory.items():
        factory = snapshot / factory_name
        for path in factory.rglob("*.jsonl"):
            if path.relative_to(factory) not in committed:
                path.unlink()


def _snapshot_attempt(src, prefix, directory):
    """One bracketed copy: returns the snapshot on stable visibility, else None."""
    reject_snapshot_symlinks(src)
    visible_before = marker_visible_jsonl_paths(src)
    try:
        temp, snap = (
            snapshot_to_temp(src, prefix)
            if directory is None
            else snapshot_to_temp(src, prefix, directory)
        )
    except TransactionError as exc:
        if isinstance(exc.__cause__, FileNotFoundError):
            return None
        raise
    try:
        visible_after = marker_visible_jsonl_paths(src)
    except BaseException:
        temp.cleanup()
        raise
    if visible_before == visible_after:
        return temp, snap, visible_before
    temp.cleanup()
    return None


def marker_visible_snapshot(src, prefix, directory=None):
    """Copy one run without crossing its monotonic transaction commit point."""
    for _attempt in range(3):
        result = _snapshot_attempt(src, prefix, directory)
        if result is not None:
            return result
    raise TransactionError(
        f"run changed transaction visibility repeatedly while snapshotting: {src}"
    )
