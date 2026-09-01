#!/usr/bin/env python3
"""Compatibility facade for fail-closed compose source and destination I/O.

The implementation is separated by responsibility, while this module keeps
the established helper surface and monkeypatch seams used by callers and the
filesystem race tests. Orchestration deliberately resolves those seams here
at call time so a test can still interpose at the exact vulnerable syscall
window.
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from compose_contract import ComposeError, sha256_hex  # noqa: E402
from compose_destination_binding import (
    DESTINATION_PARENT_LABEL as _DESTINATION_PARENT_LABEL,
    DirectoryBinding,
    PinnedDestination,
    _assert_descriptor_contained,
    _assert_descriptor_outside_raw,
    _contains_raw_segments,
    _destination_descriptor,
    _directory_identity,
    _is_under_raw,
    _require_exact_directory,
    _verify_destination_target,
    _verify_directory_binding,
    directory_binding_matches,
)
from compose_destination_creation import (
    _assert_destination_disjoint,
    _assert_new_destination,
    _created_destination_identity,
    _discard_created_destination,
    _open_created_destination,
    _pinned_root_path,
    _refuse_existing_destination,
    _verify_destination_parent_residency,
    create_pinned_destination as _create_pinned_destination,
)
from compose_destination_writer import (
    _create_child_directory,
    _destination_write_parts as _validated_destination_write_parts,
    _open_child_directory_entry,
    _open_new_leaf,
    _open_pinned_child_directory as _pin_child_directory,
    _remove_created_directory,
    _remove_created_file,
    _rollback_child_directory,
    _verify_pinned_child,
    _write_all,
)
from compose_source_snapshot import (
    DescriptorReadHooks,
    ExactReadHooks,
    PinnedChildRead,
    RoundVisibilityHooks,
    SourcePathRead,
    _assert_opened_source_identity,
    _assert_unaliased_regular_member,
    _collect_source_directory,
    _committed_paths,
    _drain_descriptor,
    _enclosing_marker_root,
    _open_pinned_child,
    _scan_source_directory,
    _source_entry_metadata,
    _source_member_path,
    _stable_file_identity,
    _validated_member_relative,
    assert_source_path_unchanged,
    read_exact_child_file,
    read_exact_regular_file,
    read_pinned_child_bytes,
    round_visible_members,
    source_jsonl_members as enumerate_source_jsonl_members,
)

_PIPELINES = Path(__file__).resolve().parent
_COMPATIBILITY_MODULES = (sys,)

__all__ = (
    "ComposeError",
    "PinnedDestination",
    "_DESTINATION_PARENT_LABEL",
    "_assert_descriptor_contained",
    "_assert_destination_disjoint",
    "_assert_new_destination",
    "_assert_opened_source_identity",
    "_assert_source_path_unchanged",
    "_assert_unaliased_regular_member",
    "_collect_source_directory",
    "_committed_paths",
    "_contains_raw_segments",
    "_create_child_directory",
    "create_pinned_destination",
    "_create_pinned_new_directory",
    "_created_destination_identity",
    "_destination_write_parts",
    "_directory_binding_matches",
    "_directory_identity",
    "_discard_created_destination",
    "_drain_descriptor",
    "_enclosing_marker_root",
    "_is_under_raw",
    "_open_child_directory_entry",
    "_open_created_destination",
    "_open_pinned_child",
    "_open_pinned_child_directory",
    "_pinned_root_path",
    "_read_exact_child_file",
    "_read_exact_regular_file",
    "_read_pinned_child_bytes",
    "_refuse_existing_destination",
    "_require_exact_directory",
    "_rollback_child_directory",
    "_round_visible_members",
    "_scan_source_directory",
    "_source_entry_metadata",
    "_source_member_path",
    "_stable_file_identity",
    "_validated_member_relative",
    "_verify_destination_parent_residency",
    "_verify_directory_binding",
    "_verify_pinned_child",
    "_write_new_text",
    "source_jsonl_members",
    "write_pinned_new_bytes",
)


def _directory_binding_matches(*observations: Any, **named: Any) -> bool:
    """Compatibility adapter from the historical five-part call surface."""

    return directory_binding_matches(DirectoryBinding(*observations, **named))


def _assert_source_path_unchanged(*observations: Any, **named: Any) -> None:
    """Compatibility adapter for one completed source-path read."""

    assert_source_path_unchanged(SourcePathRead(*observations, **named))


def _descriptor_read_hooks() -> DescriptorReadHooks:
    """Resolve descriptor-read seams from the facade at call time."""

    return DescriptorReadHooks(
        assert_opened_identity=_assert_opened_source_identity,
        drain_descriptor=_drain_descriptor,
    )


def _read_exact_regular_file(
    root: Path, raw_path: Any, label: str
) -> tuple[Path, bytes]:
    """Read a source member while retaining the monkeypatch-visible resolver."""

    return read_exact_regular_file(
        root,
        raw_path,
        label,
        ExactReadHooks(
            resolve_member=_source_member_path,
            descriptor=_descriptor_read_hooks(),
            assert_path_unchanged=_assert_source_path_unchanged,
        ),
    )


def _read_pinned_child_bytes(*observations: Any, **named: Any) -> bytes:
    """Compatibility adapter for a pinned direct-child read."""

    return read_pinned_child_bytes(
        PinnedChildRead(*observations, **named),
        _descriptor_read_hooks(),
    )


def _read_exact_child_file(
    parent: Path,
    name: str,
    label: str,
) -> tuple[Path, bytes]:
    """Read a direct child through the facade's pinned-read seam."""

    return read_exact_child_file(
        parent,
        name,
        label,
        _read_pinned_child_bytes,
    )


def _round_visible_members(root: Path, members: list[str]) -> list[str]:
    """Filter source members through facade-selected transaction lookups."""

    return round_visible_members(
        root,
        members,
        RoundVisibilityHooks(
            enclosing_marker_root=_enclosing_marker_root,
            committed_paths=_committed_paths,
        ),
    )


def source_jsonl_members(root: Path) -> tuple[str, ...]:
    """Enumerate source members through the facade visibility seam."""

    return enumerate_source_jsonl_members(root, _round_visible_members)


def create_pinned_destination(
    source_run: Path, destination: Path
) -> PinnedDestination:
    """Create a destination while retaining the existing-name race seam."""

    return _create_pinned_destination(
        source_run,
        destination,
        _refuse_existing_destination,
    )


def _destination_write_parts(relative: Any, label: str) -> tuple[str, ...]:
    """Validate a destination path through the compatibility surface."""

    return _validated_destination_write_parts(relative, label)


def _open_pinned_child_directory(
    parent_descriptor: int, name: str, label: str
) -> tuple[int, bool]:
    """Pin one child while retaining the relocation-race patch seam."""

    return _pin_child_directory(parent_descriptor, name, label)


@dataclass(frozen=True)
class BoundDestinationAccess:
    """A pinned parent and the destination authority that contains it."""

    target: int | PinnedDestination
    parent_descriptor: int
    label: str

    @property
    def root_descriptor(self) -> int:
        return _destination_descriptor(self.target)

    def verify_parent(self) -> None:
        _verify_destination_target(self.target)
        _assert_descriptor_contained(
            self.root_descriptor,
            self.parent_descriptor,
            self.label,
        )
        _assert_descriptor_outside_raw(self.parent_descriptor, self.label)

    def verify_child(self, descriptor: int) -> None:
        _verify_destination_target(self.target)
        _assert_descriptor_contained(
            self.root_descriptor,
            descriptor,
            self.label,
        )


def _open_bound_destination_directory(
    target: int | PinnedDestination,
    parent_descriptor: int,
    name: str,
    label: str,
) -> int:
    """Create and pin one directory while retaining the root path binding."""

    access = BoundDestinationAccess(target, parent_descriptor, label)
    access.verify_parent()
    child_descriptor, created = _open_pinned_child_directory(
        parent_descriptor,
        name,
        label,
    )
    try:
        access.verify_child(child_descriptor)
    except BaseException:
        if created:
            _remove_created_directory(parent_descriptor, name)
        os.close(child_descriptor)
        raise
    return child_descriptor


def _create_pinned_new_directory(
    target: int | PinnedDestination, name: str, label: str
) -> None:
    """Create one checked child directory through a pinned destination."""

    parent_descriptor = _destination_descriptor(target)
    child_descriptor = _open_bound_destination_directory(
        target,
        parent_descriptor,
        name,
        label,
    )
    os.close(child_descriptor)


def _open_bound_destination_leaf(
    target: int | PinnedDestination,
    parent_descriptor: int,
    leaf: str,
    label: str,
) -> int:
    """Create one new leaf and verify the bound root before returning it."""

    access = BoundDestinationAccess(target, parent_descriptor, label)
    access.verify_parent()
    descriptor = _open_new_leaf(parent_descriptor, leaf, label)
    try:
        access.verify_child(descriptor)
    except BaseException:
        _remove_created_file(parent_descriptor, leaf)
        os.close(descriptor)
        raise
    return descriptor


@dataclass(frozen=True)
class DestinationLeafWrite:
    """The complete authority and payload for one destination leaf write."""

    target: int | PinnedDestination
    parent_descriptor: int
    leaf: str
    payload: bytes
    label: str


def _write_destination_leaf(write: DestinationLeafWrite) -> None:
    """Write and revalidate one exclusively created destination leaf."""

    descriptor = _open_bound_destination_leaf(
        write.target,
        write.parent_descriptor,
        write.leaf,
        write.label,
    )
    root_descriptor = _destination_descriptor(write.target)
    try:
        _write_all(descriptor, write.payload)
        _assert_descriptor_contained(root_descriptor, descriptor, write.label)
        _assert_descriptor_outside_raw(descriptor, write.label)
        _verify_destination_target(write.target)
    except BaseException:
        _remove_created_file(write.parent_descriptor, write.leaf)
        raise
    finally:
        os.close(descriptor)


def _write_bound_destination_leaf(*parts: Any, **named: Any) -> None:
    """Compatibility adapter for a context-bound destination leaf write."""

    _write_destination_leaf(DestinationLeafWrite(*parts, **named))


def write_pinned_new_bytes(
    target: int | PinnedDestination,
    relative: Any,
    payload: bytes,
    label: str = "destination",
) -> str:
    """Create one new file under a pinned root, pinning every component."""

    root_descriptor = _destination_descriptor(target)
    parts = _destination_write_parts(relative, label)
    opened: list[int] = []
    current = root_descriptor
    try:
        for name in parts[:-1]:
            current = _open_bound_destination_directory(
                target,
                current,
                name,
                label,
            )
            opened.append(current)
        _write_destination_leaf(
            DestinationLeafWrite(
                target=target,
                parent_descriptor=current,
                leaf=parts[-1],
                payload=payload,
                label=label,
            )
        )
    finally:
        for descriptor in reversed(opened):
            os.close(descriptor)
    return sha256_hex(payload)


def _write_new_text(
    target: int | PinnedDestination, relative: Any, text: str
) -> str:
    """Create one new destination file exclusively and hash its bytes."""

    return write_pinned_new_bytes(
        target,
        relative,
        text.encode("utf-8"),
        f"destination {relative}",
    )
