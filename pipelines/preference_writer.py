#!/usr/bin/env python3
"""Write one curation run to destinations that must not already exist.

Every guard here exists because the destination is the only place this lane
can do irreversible damage. Writing anywhere under ``outputs/raw/`` is
refused outright, an existing path is never overwritten, and a destination
that would replace or nest inside the scanned source is rejected before any
file is created. Creation itself goes through ``O_EXCL`` against a pinned
parent directory descriptor, so a symlink swapped in mid-write cannot
redirect the payload, and a partial write is unlinked rather than published.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

_PIPELINES = Path(__file__).resolve().parent
if str(_PIPELINES) not in sys.path:
    sys.path.insert(0, str(_PIPELINES))

from preference_model import (  # noqa: E402
    CurationRun,
    PreferenceCurationError,
    canonical_json,
    is_under_raw,
)

__all__ = ["write_run"]


def _refuse_raw_destination(destination: Path, label: str) -> None:
    if not is_under_raw(destination):
        return
    # A file source has no directory to nest inside, and a directory source
    # does not contain its own siblings, so the remaining destination checks
    # cannot keep a curated write out of the immutable raw tree on their own.
    raise PreferenceCurationError(
        f"{label} would write inside immutable raw evidence: {destination}"
    )


def _refuse_existing_destination(destination: Path, label: str) -> None:
    if destination.exists():
        raise PreferenceCurationError(
            f"{label} already exists; refusing overwrite: {destination}"
        )
    if destination.parent.is_dir():
        return
    raise PreferenceCurationError(
        f"{label} parent does not exist: {destination.parent}"
    )


def _destination_replaces_source(source: Path, destination: Path) -> bool:
    return source.resolve() == destination.resolve(strict=False)


def _destination_inside_source(source: Path, destination: Path) -> bool:
    if not source.is_dir():
        return False
    return source.resolve() in destination.resolve(strict=False).parents


def _refuse_source_collision(source: Path, destination: Path, label: str) -> None:
    if _destination_replaces_source(source, destination):
        raise PreferenceCurationError(f"{label} cannot replace source: {destination}")
    if not _destination_inside_source(source, destination):
        return
    raise PreferenceCurationError(
        f"{label} cannot be written inside source: {destination}"
    )


def _assert_new_destination(source: Path, destination: Path, label: str) -> None:
    _refuse_raw_destination(destination, label)
    _refuse_existing_destination(destination, label)
    _refuse_source_collision(source, destination, label)


def _jsonl_payload(records: tuple[dict[str, Any], ...]) -> str:
    return "".join(canonical_json(record) + "\n" for record in records)


def _open_destination_parent(path: Path) -> int:
    flags = os.O_RDONLY | os.O_DIRECTORY | getattr(os, "O_NOFOLLOW", 0)
    try:
        return os.open(path.parent, flags)
    except OSError as exc:
        raise PreferenceCurationError(
            f"destination parent is not a pinned directory: {path.parent}"
        ) from exc


def _refuse_opened_parent(parent_fd: int, destination: Path) -> None:
    try:
        opened = Path(os.readlink(f"/proc/self/fd/{parent_fd}"))
    except OSError:
        opened = destination.parent
    _refuse_raw_destination(opened, "destination")
    _refuse_raw_destination(opened / destination.name, "destination")


def _create_exclusive_file(path: Path, payload: str, created: list[Path]) -> None:
    parent_fd = _open_destination_parent(path)
    try:
        _refuse_opened_parent(parent_fd, path)
        descriptor = os.open(
            path.name,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL,
            0o644,
            dir_fd=parent_fd,
        )
    finally:
        os.close(parent_fd)
    created.append(path)
    with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())


def _fsync_parents(paths: list[Path]) -> None:
    # Durable file contents still need a durable directory entry.
    for directory in dict.fromkeys(path.parent for path in paths):
        directory_descriptor = os.open(directory, os.O_RDONLY)
        try:
            os.fsync(directory_descriptor)
        finally:
            os.close(directory_descriptor)


def _unlink_created(created: list[Path]) -> None:
    # Remove only files this invocation created; pre-existing paths are
    # rejected before and during O_EXCL creation.
    for path in created:
        try:
            path.unlink()
        except FileNotFoundError:
            pass


def write_run(run: CurationRun, source: Path, output: Path, manifest: Path) -> None:
    """Write a curation run to two absent destinations without clobbering."""

    source = Path(source)
    output = Path(output)
    manifest = Path(manifest)
    if output.resolve(strict=False) == manifest.resolve(strict=False):
        raise PreferenceCurationError("output and manifest destinations must differ")
    _assert_new_destination(source, output, "output")
    _assert_new_destination(source, manifest, "manifest")

    created: list[Path] = []
    try:
        for path, payload in (
            (output, _jsonl_payload(run.records)),
            (manifest, _jsonl_payload(run.manifest)),
        ):
            _create_exclusive_file(path, payload, created)
        _fsync_parents(created)
    except Exception:
        _unlink_created(created)
        raise
