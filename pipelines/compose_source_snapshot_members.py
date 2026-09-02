#!/usr/bin/env python3
"""Source member-path validation and alias refusal for compose snapshots."""

from __future__ import annotations

import os
import stat
import sys
from pathlib import Path, PurePosixPath
from typing import Any

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("compose_source_snapshot_members")
    from .compose_contract import ComposeError
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "compose_source_snapshot_members"
    )
    from compose_contract import ComposeError


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


if __package__:
    _expose_package_sibling(__name__)
