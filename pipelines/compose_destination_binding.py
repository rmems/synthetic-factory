#!/usr/bin/env python3
"""Pinned directory identities shared by compose source and destination I/O."""

from __future__ import annotations

import os
import shutil
import stat
import sys
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

if __package__:
    from . import _expose_package_sibling, _local_sibling_module, _require_local_sibling

    if _local_sibling_module("compose_destination_binding", allow_initializing=True):
        import compose_destination_binding as _direct_compose_destination_binding

        _require_local_sibling(
            _direct_compose_destination_binding,
            "compose_destination_binding",
        )
        del _direct_compose_destination_binding
    from .compose_contract import ComposeError
    from .raw_tree_guard import contains_raw_segments
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "compose_destination_binding"
    )
    from compose_contract import ComposeError
    from raw_tree_guard import contains_raw_segments

DESTINATION_PARENT_LABEL = "destination parent"

# Compatibility callers import this symbol through ``compose_destination``.
_contains_raw_segments = contains_raw_segments


def _is_under_raw(path: Path) -> bool:
    """Reject lexical raw aliases as well as symlink-resolved raw paths."""

    if _contains_raw_segments(path.parts):
        return True
    return _contains_raw_segments(path.resolve(strict=False).parts)


def _require_exact_directory(path: Path, label: str) -> Path:
    """Require a real directory reached without a symlinked path alias."""

    try:
        metadata = path.lstat()
        resolved = path.resolve(strict=True)
    except FileNotFoundError as exc:
        raise ComposeError(f"{label} is missing: {path}") from exc
    absolute = Path(os.path.abspath(path))
    if not stat.S_ISDIR(metadata.st_mode):
        raise ComposeError(f"{label} must be an exact non-symlink directory: {path}")
    if resolved != absolute:
        raise ComposeError(f"{label} must be an exact non-symlink directory: {path}")
    return resolved


def _directory_identity(metadata: os.stat_result) -> tuple[int, int, int]:
    """Identity fields that do not change when directory entries are added."""

    return metadata.st_dev, metadata.st_ino, stat.S_IFMT(metadata.st_mode)


@dataclass(frozen=True)
class DirectoryBinding:
    """The path and descriptor observations for one pinned directory."""

    metadata: os.stat_result
    opened: os.stat_result
    resolved: Path
    absolute: Path
    expected_identity: tuple[int, int, int] | None = None

    def matches(self) -> bool:
        """Whether every observation still identifies the expected directory."""

        if not stat.S_ISDIR(self.metadata.st_mode):
            return False
        if not stat.S_ISDIR(self.opened.st_mode):
            return False
        if self.resolved != self.absolute:
            return False
        opened_identity = _directory_identity(self.opened)
        if _directory_identity(self.metadata) != opened_identity:
            return False
        if self.expected_identity is None:
            return True
        return opened_identity == self.expected_identity


def directory_binding_matches(binding: DirectoryBinding) -> bool:
    """Return whether one captured path-to-descriptor binding still holds."""

    return binding.matches()


def _verify_directory_binding(
    path: Path,
    descriptor: int,
    label: str,
    *,
    expected_identity: tuple[int, int, int] | None = None,
) -> None:
    """Require ``path`` and a pinned descriptor to name the same directory."""

    try:
        binding = DirectoryBinding(
            metadata=path.lstat(),
            opened=os.fstat(descriptor),
            resolved=path.resolve(strict=True),
            absolute=Path(os.path.abspath(path)),
            expected_identity=expected_identity,
        )
    except OSError as exc:
        raise ComposeError(f"{label} changed while it was pinned: {path}") from exc
    if not binding.matches():
        raise ComposeError(f"{label} changed while it was pinned: {path}")


def _assert_descriptor_outside_raw(descriptor: int, label: str) -> None:
    """Require the kernel's current descriptor path to remain outside raw."""

    try:
        current_path = os.readlink(f"/proc/self/fd/{descriptor}")
    except OSError:
        return
    if _contains_raw_segments(tuple(PurePosixPath(current_path).parts)):
        raise ComposeError(
            f"{label}: destination was relocated into immutable raw evidence"
        )


def _assert_descriptor_contained(
    root_descriptor: int, descriptor: int, label: str
) -> None:
    """Require a pinned component to remain below its destination root."""

    try:
        root_path = Path(os.readlink(f"/proc/self/fd/{root_descriptor}"))
        current_path = Path(os.readlink(f"/proc/self/fd/{descriptor}"))
    except OSError:
        return
    if current_path == root_path:
        return
    if root_path in current_path.parents:
        return
    raise ComposeError(f"{label}: component escaped its pinned destination root")


@dataclass
class PinnedDestination:
    """A new destination held by directory descriptors until commit or cleanup."""

    path: Path
    root: Path
    parent_descriptor: int
    destination_descriptor: int
    parent_identity: tuple[int, int, int]
    destination_identity: tuple[int, int, int]
    closed: bool = False

    def verify_binding(self) -> None:
        """Require both descriptors to retain their original path bindings."""

        if self.closed:
            raise ComposeError("destination pin was already closed")
        _verify_directory_binding(
            self.path.parent,
            self.parent_descriptor,
            DESTINATION_PARENT_LABEL,
            expected_identity=self.parent_identity,
        )
        _verify_directory_binding(
            self.path,
            self.destination_descriptor,
            "destination",
            expected_identity=self.destination_identity,
        )

    def _entry_is_ours(self) -> bool:
        try:
            current = os.stat(
                self.path.name,
                dir_fd=self.parent_descriptor,
                follow_symlinks=False,
            )
        except OSError:
            return False
        if not stat.S_ISDIR(current.st_mode):
            return False
        return _directory_identity(current) == self.destination_identity

    def cleanup(self) -> None:
        """Remove only the directory created through the pinned parent."""

        if self.closed:
            return
        os.close(self.destination_descriptor)
        if self._entry_is_ours():
            shutil.rmtree(
                self.path.name,
                ignore_errors=True,
                dir_fd=self.parent_descriptor,
            )
        os.close(self.parent_descriptor)
        self.closed = True

    def finish(self) -> None:
        """Verify lexical bindings survived, then release the descriptors."""

        if self.closed:
            raise ComposeError("destination pin was already closed")
        try:
            self.verify_binding()
        except BaseException:
            self.cleanup()
            raise
        os.close(self.destination_descriptor)
        os.close(self.parent_descriptor)
        self.closed = True


def _destination_descriptor(target: int | PinnedDestination) -> int:
    """Return the root descriptor carried by a raw or fully bound target."""

    if isinstance(target, PinnedDestination):
        return target.destination_descriptor
    return target


def _verify_destination_target(target: int | PinnedDestination) -> None:
    """Reject relocation when the caller retained the complete root binding."""

    if isinstance(target, PinnedDestination):
        _assert_descriptor_outside_raw(target.destination_descriptor, "destination")
        target.verify_binding()


if __package__:
    _expose_package_sibling(__name__)
