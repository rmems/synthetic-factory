#!/usr/bin/env python3
"""Exact destination-tree capture through pinned directory descriptors."""

from __future__ import annotations

import hashlib
import os
import stat
import sys
from dataclasses import dataclass, field
from pathlib import PurePosixPath
from typing import Callable

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("compose_destination_tree")
    from .compose_contract import ComposeError
    from .compose_destination_directory import _directory_identity, _fresh_directory_names
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "compose_destination_tree"
    )
    from compose_contract import ComposeError
    from compose_destination_directory import _directory_identity, _fresh_directory_names


@dataclass(frozen=True)
class _TreePath:
    """Descriptor-relative name used during exact-tree capture."""

    parent_descriptor: int
    name: str
    relative_parts: tuple[str, ...]

    @property
    def relative(self) -> str:
        return PurePosixPath(*self.relative_parts).as_posix()


@dataclass(frozen=True)
class _TreeEntry:
    """One path and metadata observation from the destination tree."""

    path: _TreePath
    metadata: os.stat_result

    @property
    def relative(self) -> str:
        return self.path.relative


@dataclass
class _DestinationTreeSnapshot:
    """Exact topology and byte digests observed through pinned descriptors.

    ``outside_raw`` is the caller's raw-relocation guard for one opened
    descriptor; the capture never decides raw residency on its own.
    """

    outside_raw: Callable[[int, str], None]
    directories: set[str] = field(default_factory=set)
    digests: dict[str, str] = field(default_factory=dict)

    @staticmethod
    def _file_identity(metadata: os.stat_result) -> tuple[int, ...]:
        return (
            metadata.st_dev,
            metadata.st_ino,
            metadata.st_mode,
            metadata.st_nlink,
            metadata.st_size,
            metadata.st_mtime_ns,
            metadata.st_ctime_ns,
        )

    @staticmethod
    def _open(path: _TreePath, *, directory: bool) -> int:
        flags = (
            os.O_RDONLY
            | getattr(os, "O_NOFOLLOW", 0)
            | getattr(
                os,
                "O_CLOEXEC",
                0,
            )
        )
        flags |= getattr(os, "O_DIRECTORY", 0) if directory else os.O_NONBLOCK
        try:
            return os.open(path.name, flags, dir_fd=path.parent_descriptor)
        except OSError as exc:
            kind = "directory" if directory else "file"
            raise ComposeError(
                f"destination tree {kind} cannot be opened: {path.relative}"
            ) from exc

    @staticmethod
    def _metadata(path: _TreePath) -> os.stat_result:
        try:
            return os.stat(
                path.name,
                dir_fd=path.parent_descriptor,
                follow_symlinks=False,
            )
        except OSError as exc:
            raise ComposeError(
                f"destination tree entry cannot be inspected: {path.relative}"
            ) from exc

    @classmethod
    def _require_stable_file(
        cls,
        expected: os.stat_result,
        actual: os.stat_result,
        relative: str,
    ) -> None:
        if cls._file_identity(expected) != cls._file_identity(actual):
            raise ComposeError(f"destination tree file changed: {relative}")

    @staticmethod
    def _digest_file(descriptor: int) -> str:
        digest = hashlib.sha256()
        while chunk := os.read(descriptor, 1 << 20):
            digest.update(chunk)
        return digest.hexdigest()

    def _read_file(self, entry: _TreeEntry) -> str:
        """Hash one unique regular entry through a stable pinned descriptor."""

        if not stat.S_ISREG(entry.metadata.st_mode) or entry.metadata.st_nlink != 1:
            raise ComposeError(f"destination tree contains unsafe file: {entry.relative}")
        descriptor = self._open(entry.path, directory=False)
        try:
            self.outside_raw(
                descriptor,
                f"destination tree file {entry.relative}",
            )
            opened = os.fstat(descriptor)
            self._require_stable_file(entry.metadata, opened, entry.relative)
            digest = self._digest_file(descriptor)
            self._require_stable_file(opened, os.fstat(descriptor), entry.relative)
            self._require_stable_file(
                opened,
                self._metadata(entry.path),
                entry.relative,
            )
            return digest
        except OSError as exc:
            raise ComposeError(f"destination tree file cannot be read: {entry.relative}") from exc
        finally:
            os.close(descriptor)

    def _scan_child_directory(self, entry: _TreeEntry) -> None:
        self.directories.add(entry.relative)
        child = self._open(entry.path, directory=True)
        try:
            opened = os.fstat(child)
            self.outside_raw(
                child,
                f"destination tree directory {entry.relative}",
            )
            if _directory_identity(entry.metadata) != _directory_identity(opened):
                raise ComposeError(f"destination tree directory changed: {entry.relative}")
            self._scan_directory(child, entry.path.relative_parts)
            current = self._metadata(entry.path)
            if _directory_identity(opened) != _directory_identity(current):
                raise ComposeError(f"destination tree directory changed: {entry.relative}")
        finally:
            os.close(child)

    def _scan_directory(
        self,
        descriptor: int,
        prefix: tuple[str, ...],
    ) -> None:
        for name in _fresh_directory_names(descriptor, "destination tree"):
            path = _TreePath(descriptor, name, (*prefix, name))
            entry = _TreeEntry(path, self._metadata(path))
            if stat.S_ISDIR(entry.metadata.st_mode):
                self._scan_child_directory(entry)
            elif stat.S_ISREG(entry.metadata.st_mode):
                self.digests[entry.relative] = self._read_file(entry)
            else:
                raise ComposeError(f"destination tree contains unsafe entry: {entry.relative}")

    def capture(self, descriptor: int) -> tuple[frozenset[str], dict[str, str]]:
        self._scan_directory(descriptor, ())
        return frozenset(self.directories), self.digests


if __package__:
    _expose_package_sibling(__name__)
