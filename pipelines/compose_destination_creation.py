#!/usr/bin/env python3
"""Exclusive destination creation through pinned directory descriptors."""

from __future__ import annotations

import os
import shutil
import stat
import sys
from pathlib import Path
from typing import Callable

if __package__:
    from . import _expose_package_sibling, _local_sibling_module, _require_local_sibling

    if _local_sibling_module("compose_destination_creation", allow_initializing=True):
        import compose_destination_creation as _direct_compose_destination_creation

        _require_local_sibling(
            _direct_compose_destination_creation,
            "compose_destination_creation",
        )
        del _direct_compose_destination_creation
    from .compose_contract import ComposeError
    from .compose_destination_binding import (
        DESTINATION_PARENT_LABEL,
        PinnedDestination,
        _assert_descriptor_outside_raw,
        _directory_identity,
        _is_under_raw,
        _require_exact_directory,
        _verify_directory_binding,
    )
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "compose_destination_creation"
    )
    from compose_contract import ComposeError
    from compose_destination_binding import (
        DESTINATION_PARENT_LABEL,
        PinnedDestination,
        _assert_descriptor_outside_raw,
        _directory_identity,
        _is_under_raw,
        _require_exact_directory,
        _verify_directory_binding,
    )

ExistingDestinationCheck = Callable[[int, Path], None]


def _assert_destination_disjoint(
    resolved_source: Path, resolved_destination: Path
) -> None:
    """Require source and destination trees to be fully disjoint."""

    if resolved_source == resolved_destination:
        raise ComposeError("destination cannot replace the source run")
    if resolved_source in resolved_destination.parents:
        raise ComposeError("destination cannot be written inside the source run")
    if resolved_destination in resolved_source.parents:
        raise ComposeError("destination cannot contain the source run")


def _assert_new_destination(
    source_run: Path, destination: Path
) -> tuple[Path, tuple[int, int, int]]:
    """Validate a new destination and capture its exact parent identity."""

    if os.path.lexists(destination):
        raise ComposeError(f"refusing to overwrite an existing destination: {destination}")
    if _is_under_raw(destination):
        raise ComposeError(f"refusing to write inside immutable raw evidence: {destination}")
    _assert_destination_disjoint(
        source_run.resolve(),
        destination.resolve(strict=False),
    )
    parent = _require_exact_directory(destination.parent, DESTINATION_PARENT_LABEL)
    return parent, _directory_identity(parent.lstat())


def _refuse_existing_destination(parent_descriptor: int, destination: Path) -> None:
    """Refuse a destination name that already exists under the pinned parent."""

    try:
        os.stat(
            destination.name,
            dir_fd=parent_descriptor,
            follow_symlinks=False,
        )
    except FileNotFoundError:
        return
    raise ComposeError(f"refusing to overwrite an existing destination: {destination}")


def _pinned_root_path(destination_descriptor: int) -> Path:
    """Return the descriptor-addressed root every later write goes through."""

    root = Path(f"/proc/self/fd/{destination_descriptor}")
    if not root.is_dir():
        raise ComposeError("pinned destination descriptor is not path-addressable")
    return root


def _discard_created_destination(
    parent_descriptor: int,
    destination: Path,
    created_identity: tuple[int, int, int],
) -> None:
    """Remove a partly created destination, but only the one we created."""

    try:
        current = os.stat(
            destination.name,
            dir_fd=parent_descriptor,
            follow_symlinks=False,
        )
    except OSError:
        return
    if _directory_identity(current) == created_identity:
        shutil.rmtree(
            destination.name,
            ignore_errors=True,
            dir_fd=parent_descriptor,
        )


def _verify_destination_parent_residency(
    parent: Path,
    parent_descriptor: int,
    expected_identity: tuple[int, int, int],
) -> None:
    """Require the pinned parent to remain at its requested non-raw path."""

    _assert_descriptor_outside_raw(parent_descriptor, DESTINATION_PARENT_LABEL)
    _verify_directory_binding(
        parent,
        parent_descriptor,
        DESTINATION_PARENT_LABEL,
        expected_identity=expected_identity,
    )


def _created_destination_identity(
    parent_descriptor: int, destination: Path
) -> tuple[int, int, int]:
    """Validate and identify the directory created under the pinned parent."""

    created = os.stat(
        destination.name,
        dir_fd=parent_descriptor,
        follow_symlinks=False,
    )
    if not stat.S_ISDIR(created.st_mode):
        raise ComposeError(f"new destination is not a directory: {destination}")
    return _directory_identity(created)


def _open_created_destination(
    parent_descriptor: int,
    destination: Path,
    flags: int,
    expected_identity: tuple[int, int, int],
) -> int:
    """Open the new destination and retain only its expected identity."""

    descriptor = os.open(destination.name, flags, dir_fd=parent_descriptor)
    if _directory_identity(os.fstat(descriptor)) == expected_identity:
        return descriptor
    os.close(descriptor)
    raise ComposeError("destination identity changed while opening")


def _directory_open_flags() -> int:
    return (
        os.O_RDONLY
        | getattr(os, "O_DIRECTORY", 0)
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_CLOEXEC", 0)
    )


def create_pinned_destination(
    source_run: Path,
    destination: Path,
    refuse_existing: ExistingDestinationCheck,
) -> PinnedDestination:
    """Create one exclusive destination relative to a pinned parent."""

    parent, parent_identity = _assert_new_destination(source_run, destination)
    destination = Path(os.path.abspath(destination))
    flags = _directory_open_flags()
    parent_descriptor = os.open(parent, flags)
    destination_descriptor: int | None = None
    created_identity: tuple[int, int, int] | None = None
    try:
        _verify_destination_parent_residency(
            parent, parent_descriptor, parent_identity
        )
        refuse_existing(parent_descriptor, destination)
        _verify_destination_parent_residency(
            parent, parent_descriptor, parent_identity
        )
        os.mkdir(destination.name, 0o755, dir_fd=parent_descriptor)
        created_identity = _created_destination_identity(
            parent_descriptor,
            destination,
        )
        _verify_destination_parent_residency(
            parent, parent_descriptor, parent_identity
        )
        destination_descriptor = _open_created_destination(
            parent_descriptor,
            destination,
            flags,
            created_identity,
        )
        _verify_destination_parent_residency(
            parent, parent_descriptor, parent_identity
        )
        _assert_descriptor_outside_raw(destination_descriptor, "destination")
        _verify_directory_binding(
            destination,
            destination_descriptor,
            "destination",
            expected_identity=created_identity,
        )
        return PinnedDestination(
            path=destination,
            root=_pinned_root_path(destination_descriptor),
            parent_descriptor=parent_descriptor,
            destination_descriptor=destination_descriptor,
            parent_identity=parent_identity,
            destination_identity=created_identity,
        )
    except BaseException:
        if destination_descriptor is not None:
            os.close(destination_descriptor)
        if created_identity is not None:
            _discard_created_destination(
                parent_descriptor,
                destination,
                created_identity,
            )
        os.close(parent_descriptor)
        raise


if __package__:
    _expose_package_sibling(__name__)
