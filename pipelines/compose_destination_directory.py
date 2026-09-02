#!/usr/bin/env python3
"""Exact directory identity and observation checks for pinned compose I/O."""

from __future__ import annotations

import os
import stat
import sys
from dataclasses import dataclass
from pathlib import Path

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("compose_destination_directory")
    from .compose_contract import ComposeError
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "compose_destination_directory"
    )
    from compose_contract import ComposeError


def _directory_observations(path: Path) -> tuple[os.stat_result, Path]:
    return path.lstat(), path.resolve(strict=True)


def _required_directory_observations(path: Path, label: str) -> tuple[os.stat_result, Path]:
    """Observe a required directory while normalizing resolution failures."""

    try:
        return _directory_observations(path)
    except FileNotFoundError as exc:
        raise ComposeError(f"{label} is missing: {path}") from exc
    except (OSError, RuntimeError) as exc:
        raise ComposeError(f"{label} cannot be resolved safely: {path}") from exc


def _require_exact_directory(path: Path, label: str) -> Path:
    """Require a real directory reached without a symlinked path alias."""

    metadata, resolved = _required_directory_observations(path, label)
    absolute = Path(os.path.abspath(path))
    if not stat.S_ISDIR(metadata.st_mode):
        raise ComposeError(f"{label} must be an exact non-symlink directory: {path}")
    if resolved != absolute:
        raise ComposeError(f"{label} must be an exact non-symlink directory: {path}")
    return resolved


def _directory_identity(metadata: os.stat_result) -> tuple[int, int, int]:
    """Identity fields that do not change when directory entries are added."""

    return metadata.st_dev, metadata.st_ino, stat.S_IFMT(metadata.st_mode)


def _fresh_directory_names(descriptor: int, label: str) -> list[str]:
    """Enumerate through a fresh open description with an offset at zero."""

    flags = (
        os.O_RDONLY
        | getattr(os, "O_DIRECTORY", 0)
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_CLOEXEC", 0)
    )
    try:
        scan_descriptor = os.open(".", flags, dir_fd=descriptor)
    except OSError as exc:
        raise ComposeError(f"{label}: cannot open directory for enumeration") from exc
    try:
        if _directory_identity(os.fstat(scan_descriptor)) != _directory_identity(
            os.fstat(descriptor)
        ):
            raise ComposeError(f"{label}: directory identity changed before enumeration")
        return sorted(os.listdir(scan_descriptor))
    except OSError as exc:
        raise ComposeError(f"{label}: cannot enumerate directory") from exc
    finally:
        os.close(scan_descriptor)


def _require_empty_directory(descriptor: int, label: str) -> None:
    """Require a newly pinned private directory to contain no adopted bytes."""

    entries = _fresh_directory_names(descriptor, label)
    if entries:
        raise ComposeError(f"{label}: new directory was not empty when pinned")


def _require_safe_new_directory(
    descriptor: int,
    parent_descriptor: int,
    label: str,
) -> None:
    """Require expected owner/device metadata for one new private directory."""

    try:
        opened = os.fstat(descriptor)
        parent = os.fstat(parent_descriptor)
    except OSError as exc:
        raise ComposeError(f"{label}: cannot authenticate new directory") from exc
    if _directory_identity(opened)[2] != stat.S_IFDIR:
        raise ComposeError(f"{label}: new entry is not an exact directory")
    if opened.st_dev != parent.st_dev or opened.st_uid != os.geteuid():
        raise ComposeError(f"{label}: new directory has unexpected ownership metadata")


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

        opened_identity = _directory_identity(self.opened)
        checks = (
            stat.S_ISDIR(self.metadata.st_mode),
            stat.S_ISDIR(self.opened.st_mode),
            self.resolved == self.absolute,
            _directory_identity(self.metadata) == opened_identity,
            (self.expected_identity is None or opened_identity == self.expected_identity),
        )
        return all(checks)


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
        metadata, resolved = _directory_observations(path)
        binding = DirectoryBinding(
            metadata=metadata,
            opened=os.fstat(descriptor),
            resolved=resolved,
            absolute=Path(os.path.abspath(path)),
            expected_identity=expected_identity,
        )
    except (OSError, RuntimeError) as exc:
        raise ComposeError(f"{label} changed while it was pinned: {path}") from exc
    if not binding.matches():
        raise ComposeError(f"{label} changed while it was pinned: {path}")


if __package__:
    _expose_package_sibling(__name__)
