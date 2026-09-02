#!/usr/bin/env python3
"""Exclusive destination creation through pinned directory descriptors."""

from __future__ import annotations

import os
import stat
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("compose_destination_creation")
    from .compose_contract import ComposeError
    from .compose_destination_binding import (
        DESTINATION_PARENT_LABEL,
        PinnedDestination,
        _assert_descriptor_outside_raw,
        _directory_identity,
        _is_under_raw,
        _private_entry_name,
        _quarantine_owned_entry,
        _require_empty_directory,
        _require_exact_directory,
        _require_safe_new_directory,
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
        _private_entry_name,
        _quarantine_owned_entry,
        _require_empty_directory,
        _require_exact_directory,
        _require_safe_new_directory,
        _verify_directory_binding,
    )

ExistingDestinationCheck = Callable[[int, Path], None]
_PRIVATE_DESTINATION_ATTEMPTS = 8


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
    try:
        resolved_source = source_run.resolve()
        resolved_destination = destination.resolve(strict=False)
    except (OSError, RuntimeError) as exc:
        raise ComposeError(
            f"cannot resolve source/destination paths safely: {exc}"
        ) from exc
    _assert_destination_disjoint(resolved_source, resolved_destination)
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
    """Detach a partly created destination without deleting a public name."""

    _quarantine_owned_entry(
        parent_descriptor,
        destination.name,
        created_identity,
        "destination creation rollback",
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


def _create_private_destination(
    parent_descriptor: int,
    destination: Path,
) -> Path:
    """Create one unpublished destination name with bounded collision retry."""

    for _attempt in range(_PRIVATE_DESTINATION_ATTEMPTS):
        private = destination.with_name(_private_entry_name("destination"))
        try:
            os.mkdir(private.name, 0o755, dir_fd=parent_descriptor)
        except FileExistsError:
            continue
        except OSError as exc:
            raise ComposeError(f"cannot create private destination: {exc}") from exc
        return private
    raise ComposeError("cannot allocate a private destination name")


def _cleanup_failed_destination(
    parent_descriptor: int,
    destination_descriptor: int | None,
    destination: Path,
    created_identity: tuple[int, int, int] | None,
) -> None:
    """Close pinned descriptors and remove only this invocation's directory."""

    if destination_descriptor is not None:
        os.close(destination_descriptor)
    try:
        if created_identity is not None:
            _discard_created_destination(
                parent_descriptor,
                destination,
                created_identity,
            )
    finally:
        os.close(parent_descriptor)


@dataclass
class _DestinationCreation:
    """Mutable descriptor state for one private destination transaction."""

    destination: Path
    refuse_existing: ExistingDestinationCheck
    parent: Path
    parent_identity: tuple[int, int, int]
    flags: int
    parent_descriptor: int
    destination_descriptor: int | None = None
    created_identity: tuple[int, int, int] | None = None
    created_path: Path | None = None

    def _verify_parent(self) -> None:
        _verify_destination_parent_residency(
            self.parent,
            self.parent_descriptor,
            self.parent_identity,
        )

    def _create_private_root(self) -> None:
        self._verify_parent()
        self.refuse_existing(self.parent_descriptor, self.destination)
        self._verify_parent()
        self.created_path = _create_private_destination(
            self.parent_descriptor,
            self.destination,
        )
        self.created_identity = _created_destination_identity(
            self.parent_descriptor,
            self.created_path,
        )

    def _open_private_root(self) -> None:
        self._verify_parent()
        self.destination_descriptor = _open_created_destination(
            self.parent_descriptor,
            self.created_path,
            self.flags,
            self.created_identity,
        )
        _require_safe_new_directory(
            self.destination_descriptor,
            self.parent_descriptor,
            "destination",
        )
        _require_empty_directory(self.destination_descriptor, "destination")
        self._verify_parent()
        _assert_descriptor_outside_raw(self.destination_descriptor, "destination")
        _verify_directory_binding(
            self.created_path,
            self.destination_descriptor,
            "destination",
            expected_identity=self.created_identity,
        )

    def _pinned_destination(self) -> PinnedDestination:
        return PinnedDestination(
            path=self.destination,
            root=_pinned_root_path(self.destination_descriptor),
            parent_descriptor=self.parent_descriptor,
            destination_descriptor=self.destination_descriptor,
            parent_identity=self.parent_identity,
            destination_identity=self.created_identity,
            staged_name=self.created_path.name,
        )

    def create(self) -> PinnedDestination:
        try:
            self._create_private_root()
            self._open_private_root()
            return self._pinned_destination()
        except BaseException:
            _cleanup_failed_destination(
                self.parent_descriptor,
                self.destination_descriptor,
                self.created_path or self.destination,
                self.created_identity,
            )
            raise


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
    return _DestinationCreation(
        destination=destination,
        refuse_existing=refuse_existing,
        parent=parent,
        parent_identity=parent_identity,
        flags=flags,
        parent_descriptor=parent_descriptor,
    ).create()


if __package__:
    _expose_package_sibling(__name__)
