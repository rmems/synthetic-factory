#!/usr/bin/env python3
"""Exact source-member reads and transaction-visible source enumeration.

Member-path validation lives in ``compose_source_snapshot_members`` and
source enumeration plus round visibility in
``compose_source_snapshot_visibility``; this module keeps the
descriptor-authenticated reads and re-exports both siblings so
``compose_destination`` sees one snapshot surface.
"""

from __future__ import annotations

import os
import stat
import sys
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Callable

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("compose_source_snapshot")
    from . import compose_source_snapshot_members as _members_module
    from . import compose_source_snapshot_visibility as _visibility_module
    from .compose_contract import ComposeError
    from .compose_destination_binding import (
        _directory_identity,
        _require_exact_directory,
        _verify_directory_binding,
    )
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "compose_source_snapshot"
    )
    import compose_source_snapshot_members as _members_module
    import compose_source_snapshot_visibility as _visibility_module
    from compose_contract import ComposeError
    from compose_destination_binding import (
        _directory_identity,
        _require_exact_directory,
        _verify_directory_binding,
    )

_assert_unaliased_regular_member = _members_module.assert_unaliased_regular_member
_reject_member_separator = _members_module.reject_member_separator
_reject_unsafe_member_text = _members_module.reject_unsafe_member_text
_require_canonical_member = _members_module.require_canonical_member
_require_member_text = _members_module.require_member_text
_source_member_path = _members_module.source_member_path
_stable_file_identity = _members_module.stable_file_identity
_unsafe_relative_component = _members_module.unsafe_relative_component
_validated_member_relative = _members_module.validated_member_relative
RoundVisibilityFilter = _visibility_module.RoundVisibilityFilter
RoundVisibilityHooks = _visibility_module.RoundVisibilityHooks
_collect_source_directory = _visibility_module.collect_source_directory
_committed_paths = _visibility_module.committed_paths
_enclosing_marker_root = _visibility_module.enclosing_marker_root
_scan_source_directory = _visibility_module.scan_source_directory
_source_entry_metadata = _visibility_module.source_entry_metadata
round_visible_members = _visibility_module.round_visible_members
source_jsonl_members = _visibility_module.source_jsonl_members

__all__ = (
    "DescriptorDrain",
    "DescriptorReadHooks",
    "ExactReadHooks",
    "MemberResolver",
    "OpenedIdentityCheck",
    "PinnedChildRead",
    "PinnedChildReader",
    "RoundVisibilityFilter",
    "RoundVisibilityHooks",
    "SourcePathCheck",
    "SourcePathRead",
    "_assert_opened_source_identity",
    "_assert_unaliased_regular_member",
    "_collect_source_directory",
    "_committed_paths",
    "_drain_descriptor",
    "_enclosing_marker_root",
    "_open_pinned_child",
    "_reject_member_separator",
    "_reject_unsafe_member_text",
    "_require_canonical_member",
    "_require_completed_read",
    "_require_matching_source_identity",
    "_require_member_text",
    "_scan_source_directory",
    "_source_entry_metadata",
    "_source_member_path",
    "_source_metadata_after",
    "_stable_file_identity",
    "_unsafe_relative_component",
    "_validated_member_relative",
    "assert_source_path_unchanged",
    "read_exact_child_file",
    "read_exact_regular_file",
    "read_pinned_child_bytes",
    "round_visible_members",
    "source_jsonl_members",
)

MemberResolver = Callable[[Path, Any, str], Path]
OpenedIdentityCheck = Callable[[os.stat_result, os.stat_result, str], None]
DescriptorDrain = Callable[[int], bytes]
SourcePathCheck = Callable[[Path, Path, Any, os.stat_result | None, str], None]
PinnedChildReader = Callable[..., bytes]


def _drain_descriptor(descriptor: int) -> bytes:
    """Read one already-pinned descriptor to EOF without re-opening it."""

    chunks: list[bytes] = []
    while True:
        chunk = os.read(descriptor, 1024 * 1024)
        if not chunk:
            return b"".join(chunks)
        chunks.append(chunk)


def _assert_opened_source_identity(
    before: os.stat_result, opened: os.stat_result, label: str
) -> None:
    """Require the held descriptor to match the file observed by path."""

    if not stat.S_ISREG(opened.st_mode):
        raise ComposeError(f"{label}: opened identity is not a regular file")
    if opened.st_nlink != 1:
        raise ComposeError(f"{label}: hard-link aliases are not accepted")
    if _stable_file_identity(before) != _stable_file_identity(opened):
        raise ComposeError(f"{label}: source identity changed while opening")


@dataclass(frozen=True)
class SourcePathRead:
    """The path observations needed to reauthenticate one completed read."""

    path: Path
    root: Path
    raw_path: Any
    opened_after: os.stat_result | None
    label: str


@dataclass(frozen=True)
class DescriptorReadHooks:
    """Facade-selected operations for one descriptor-authenticated read."""

    assert_opened_identity: OpenedIdentityCheck
    drain_descriptor: DescriptorDrain


@dataclass(frozen=True)
class ExactReadHooks:
    """Facade-selected operations for one path-authenticated source read."""

    resolve_member: MemberResolver
    descriptor: DescriptorReadHooks
    assert_path_unchanged: SourcePathCheck


def _source_metadata_after(read: SourcePathRead) -> os.stat_result:
    try:
        return read.path.lstat()
    except FileNotFoundError as exc:
        raise ComposeError(
            f"{read.label}: source member disappeared while reading"
        ) from exc


def _require_completed_read(read: SourcePathRead) -> os.stat_result:
    if read.opened_after is None:
        raise ComposeError(f"{read.label}: source path identity changed while reading")
    return read.opened_after


def _require_matching_source_identity(
    read: SourcePathRead,
    after: os.stat_result,
    opened_after: os.stat_result,
) -> None:
    if _stable_file_identity(after) != _stable_file_identity(opened_after):
        raise ComposeError(f"{read.label}: source path identity changed while reading")


def assert_source_path_unchanged(read: SourcePathRead) -> None:
    """Require the source path to retain the descriptor's exact identity."""

    after = _source_metadata_after(read)
    opened_after = _require_completed_read(read)
    _require_matching_source_identity(read, after, opened_after)
    relative = PurePosixPath(str(read.raw_path))
    expected = read.root.resolve(strict=True).joinpath(*relative.parts)
    if read.path.resolve(strict=True) != expected:
        raise ComposeError(
            f"{read.label}: source path became a symlink alias while reading"
        )


def read_exact_regular_file(
    root: Path,
    raw_path: Any,
    label: str,
    hooks: ExactReadHooks,
) -> tuple[Path, bytes]:
    """Read one unique source file through a pinned descriptor."""

    path = hooks.resolve_member(root, raw_path, label)
    before = path.lstat()
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | os.O_NONBLOCK
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise ComposeError(f"{label}: cannot open exact source file: {exc}") from exc
    try:
        opened_before = os.fstat(descriptor)
        hooks.descriptor.assert_opened_identity(before, opened_before, label)
        payload = hooks.descriptor.drain_descriptor(descriptor)
        opened_after = os.fstat(descriptor)
        if _stable_file_identity(opened_before) != _stable_file_identity(opened_after):
            raise ComposeError(f"{label}: source identity changed while reading")
    finally:
        os.close(descriptor)
    hooks.assert_path_unchanged(
        path,
        root,
        raw_path,
        opened_after,
        label,
    )
    return path, payload


def _open_pinned_child(
    name: str, parent_descriptor: int, label: str
) -> tuple[os.stat_result, int]:
    """Stat and open one child through its pinned parent descriptor."""

    try:
        before = os.stat(name, dir_fd=parent_descriptor, follow_symlinks=False)
        flags = (
            os.O_RDONLY
            | getattr(os, "O_NOFOLLOW", 0)
            | getattr(os, "O_CLOEXEC", 0)
            | os.O_NONBLOCK
        )
        descriptor = os.open(name, flags, dir_fd=parent_descriptor)
    except OSError as exc:
        raise ComposeError(f"{label}: cannot open exact source file: {exc}") from exc
    return before, descriptor


@dataclass(frozen=True)
class PinnedChildRead:
    """A direct child and the pinned identities used to read it."""

    name: str
    parent_descriptor: int
    file_descriptor: int
    before: os.stat_result
    label: str


def read_pinned_child_bytes(
    read: PinnedChildRead,
    hooks: DescriptorReadHooks,
) -> bytes:
    """Read an opened child, proving its identity held across the read."""

    opened_before = os.fstat(read.file_descriptor)
    hooks.assert_opened_identity(read.before, opened_before, read.label)
    payload = hooks.drain_descriptor(read.file_descriptor)
    opened_after = os.fstat(read.file_descriptor)
    after = os.stat(
        read.name,
        dir_fd=read.parent_descriptor,
        follow_symlinks=False,
    )
    if _stable_file_identity(opened_before) != _stable_file_identity(opened_after):
        raise ComposeError(f"{read.label}: source identity changed while reading")
    if _stable_file_identity(after) != _stable_file_identity(opened_after):
        raise ComposeError(f"{read.label}: source identity changed while reading")
    return payload


def read_exact_child_file(
    parent: Path,
    name: str,
    label: str,
    read_pinned_child: PinnedChildReader,
) -> tuple[Path, bytes]:
    """Read one direct child while its exact parent remains pinned."""

    parent = _require_exact_directory(parent, f"{label} parent")
    expected_identity = _directory_identity(parent.lstat())
    flags = (
        os.O_RDONLY
        | getattr(os, "O_DIRECTORY", 0)
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_CLOEXEC", 0)
    )
    try:
        parent_descriptor = os.open(parent, flags)
    except OSError as exc:
        raise ComposeError(f"{label} parent changed while it was pinned: {parent}") from exc
    file_descriptor: int | None = None
    try:
        _verify_directory_binding(
            parent,
            parent_descriptor,
            f"{label} parent",
            expected_identity=expected_identity,
        )
        before, file_descriptor = _open_pinned_child(name, parent_descriptor, label)
        payload = read_pinned_child(
            name,
            parent_descriptor,
            file_descriptor,
            before,
            label,
        )
        _verify_directory_binding(
            parent,
            parent_descriptor,
            f"{label} parent",
            expected_identity=expected_identity,
        )
        return parent / name, payload
    finally:
        if file_descriptor is not None:
            os.close(file_descriptor)
        os.close(parent_descriptor)


if __package__:
    _expose_package_sibling(__name__)
