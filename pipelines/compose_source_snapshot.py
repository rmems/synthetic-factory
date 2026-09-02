#!/usr/bin/env python3
"""Exact source-member reads and transaction-visible source enumeration."""

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
    from .compose_contract import ComposeError
    from .compose_destination_binding import (
        _directory_identity,
        _require_exact_directory,
        _verify_directory_binding,
    )
    from .round_txn import committed_jsonl_paths, marker_mode_path
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "compose_source_snapshot"
    )
    from compose_contract import ComposeError
    from compose_destination_binding import (
        _directory_identity,
        _require_exact_directory,
        _verify_directory_binding,
    )
    from round_txn import committed_jsonl_paths, marker_mode_path

MemberResolver = Callable[[Path, Any, str], Path]
OpenedIdentityCheck = Callable[[os.stat_result, os.stat_result, str], None]
DescriptorDrain = Callable[[int], bytes]
SourcePathCheck = Callable[[Path, Path, Any, os.stat_result | None, str], None]
PinnedChildReader = Callable[..., bytes]
RoundVisibilityFilter = Callable[[Path, list[str]], list[str]]


def _unsafe_relative_component(relative: PurePosixPath) -> bool:
    """Whether a normalized relative path contains traversal components."""

    return any(part in {"", ".", ".."} for part in relative.parts)


def _require_member_text(raw_path: Any, label: str) -> str:
    if not isinstance(raw_path, str):
        raise ComposeError(f"{label}: path must be a nonempty POSIX string")
    if not raw_path:
        raise ComposeError(f"{label}: path must be a nonempty POSIX string")
    return raw_path


def _reject_member_separator(raw_path: str, label: str) -> None:
    if "\\" in raw_path:
        raise ComposeError(f"{label}: path must be a nonempty POSIX string")


def _reject_unsafe_member_text(raw_path: str, label: str) -> None:
    if "\0" in raw_path:
        raise ComposeError(f"{label}: unsafe relative path {raw_path!r}")


def _require_canonical_member(
    relative: PurePosixPath, raw_path: str, label: str
) -> None:
    if relative.as_posix() != raw_path:
        raise ComposeError(f"{label}: unsafe relative path {raw_path!r}")
    if relative.is_absolute():
        raise ComposeError(f"{label}: unsafe relative path {raw_path!r}")
    if _unsafe_relative_component(relative):
        raise ComposeError(f"{label}: unsafe relative path {raw_path!r}")


def _validated_member_relative(raw_path: Any, label: str) -> PurePosixPath:
    """Reject anything that is not a plain, in-tree POSIX relative path."""

    raw_path = _require_member_text(raw_path, label)
    _reject_member_separator(raw_path, label)
    _reject_unsafe_member_text(raw_path, label)
    relative = PurePosixPath(raw_path)
    _require_canonical_member(relative, raw_path, label)
    return relative


def _assert_unaliased_regular_member(
    metadata: os.stat_result, *, label: str, raw_path: Any
) -> None:
    """A source member must be exactly one regular file, not an alias of one."""

    if not stat.S_ISREG(metadata.st_mode):
        raise ComposeError(f"{label}: source member is not a regular file: {raw_path}")
    if metadata.st_nlink != 1:
        raise ComposeError(f"{label}: hard-link aliases are not accepted: {raw_path}")


def _source_member_path(root: Path, raw_path: Any, label: str) -> Path:
    """Resolve one exact regular source member without aliases or tree escape."""

    relative = _validated_member_relative(raw_path, label)
    root_resolved = root.resolve(strict=True)
    candidate = root_resolved.joinpath(*relative.parts)
    try:
        resolved = candidate.resolve(strict=True)
        metadata = candidate.lstat()
    except FileNotFoundError as exc:
        raise ComposeError(f"{label}: source member is missing: {raw_path}") from exc
    expected = root_resolved.joinpath(*relative.parts)
    if resolved != expected:
        raise ComposeError(f"{label}: source member is a symlink alias: {raw_path}")
    if root_resolved not in resolved.parents:
        raise ComposeError(f"{label}: source member is a symlink alias: {raw_path}")
    _assert_unaliased_regular_member(metadata, label=label, raw_path=raw_path)
    return candidate


def _stable_file_identity(metadata: os.stat_result) -> tuple[int, ...]:
    """Fields that must remain stable while one source member is read."""

    return (
        metadata.st_dev,
        metadata.st_ino,
        metadata.st_mode,
        metadata.st_nlink,
        metadata.st_size,
        metadata.st_mtime_ns,
        metadata.st_ctime_ns,
    )


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


def _scan_source_directory(directory: Path) -> list[Any]:
    """List one source directory in a stable, name-sorted order."""

    try:
        with os.scandir(directory) as scan:
            return sorted(scan, key=lambda entry: entry.name)
    except OSError as exc:
        raise ComposeError(f"cannot enumerate source directory {directory}: {exc}") from exc


def _source_entry_metadata(entry: Any, path: Path) -> os.stat_result:
    """Stat one source entry without following, or accepting, an alias."""

    try:
        metadata = entry.stat(follow_symlinks=False)
    except OSError as exc:
        raise ComposeError(f"cannot inspect source member {path}: {exc}") from exc
    if stat.S_ISLNK(metadata.st_mode):
        raise ComposeError(f"source tree contains a symlink alias: {path}")
    return metadata


def _collect_source_directory(
    root: Path, directory: Path, members: list[str]
) -> list[Path]:
    """Append this directory's JSONL members; return its child directories."""

    child_directories: list[Path] = []
    for entry in _scan_source_directory(directory):
        path = Path(entry.path)
        metadata = _source_entry_metadata(entry, path)
        if entry.name.endswith(".jsonl"):
            relative = path.relative_to(root).as_posix()
            _source_member_path(root, relative, f"compose source {relative}")
            members.append(relative)
        elif stat.S_ISDIR(metadata.st_mode):
            child_directories.append(path)
    return child_directories


def _enclosing_marker_root(
    root: Path,
    parent: Path,
    marker_roots: dict[Path, Path | None],
) -> Path | None:
    """Return and memoize the nearest enclosing marker-mode directory."""

    visited = []
    current = parent
    while current not in marker_roots:
        visited.append(current)
        if marker_mode_path(current) is not None:
            found = current
            break
        if current in {root, current.parent}:
            found = None
            break
        current = current.parent
    else:
        found = marker_roots[current]
    for directory in visited:
        marker_roots[directory] = found
    return found


def _committed_paths(
    marker_root: Path,
    committed: dict[Path, set[Path]],
) -> set[Path]:
    """Return and memoize committed JSONL paths below one marker root."""

    if marker_root not in committed:
        committed[marker_root] = {
            candidate.resolve() for candidate in committed_jsonl_paths(marker_root)
        }
    return committed[marker_root]


@dataclass(frozen=True)
class RoundVisibilityHooks:
    """Facade-selected lookups for round-transaction visibility."""

    enclosing_marker_root: Callable[..., Path | None]
    committed_paths: Callable[..., set[Path]]


def round_visible_members(
    root: Path,
    members: list[str],
    hooks: RoundVisibilityHooks,
) -> list[str]:
    """Keep only members exposed by the round-transaction contract."""

    marker_roots: dict[Path, Path | None] = {}
    committed: dict[Path, set[Path]] = {}
    visible: list[str] = []
    for relative in members:
        path = root.joinpath(*PurePosixPath(relative).parts)
        marker_root = hooks.enclosing_marker_root(root, path.parent, marker_roots)
        if marker_root is None:
            visible.append(relative)
            continue
        if path.resolve() in hooks.committed_paths(marker_root, committed):
            visible.append(relative)
    return visible


def source_jsonl_members(
    root: Path,
    visible_members: RoundVisibilityFilter,
) -> tuple[str, ...]:
    """Enumerate a source tree without following filesystem aliases."""

    root = _require_exact_directory(root, "source run")
    members: list[str] = []
    pending = [root]
    while pending:
        directory = pending.pop()
        if _require_exact_directory(directory, "source directory") != directory:
            raise ComposeError(f"source directory identity changed: {directory}")
        child_directories = _collect_source_directory(root, directory, members)
        pending.extend(reversed(child_directories))
    return tuple(sorted(visible_members(root, members)))


if __package__:
    _expose_package_sibling(__name__)
