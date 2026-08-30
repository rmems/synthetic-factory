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
from dataclasses import dataclass
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


@dataclass(frozen=True)
class _CreatedFile:
    """A file this invocation created, addressed by its pinned parent.

    ``path`` is only a label for messages. The parent descriptor stays open
    until the write is finished so that the durability fsync and any cleanup
    both address the directory the file was actually created in. Resolving
    the pathname again would let a directory renamed or repointed after
    creation redirect either operation onto an unrelated file -- including,
    in the worst case, immutable raw evidence.
    """

    parent_fd: int
    name: str
    path: Path


def _create_exclusive_file(
    path: Path, payload: str, created: list[_CreatedFile]
) -> None:
    parent_fd = _open_destination_parent(path)
    try:
        _refuse_opened_parent(parent_fd, path)
        descriptor = os.open(
            path.name,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL,
            0o644,
            dir_fd=parent_fd,
        )
    except BaseException:
        os.close(parent_fd)
        raise
    created.append(_CreatedFile(parent_fd, path.name, path))
    with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())


def _parent_descriptors(created: list[_CreatedFile]) -> list[int]:
    return list(dict.fromkeys(entry.parent_fd for entry in created))


def _fsync_parents(created: list[_CreatedFile]) -> None:
    # Durable file contents still need a durable directory entry, and the
    # directory to sync is the one the file was created in.
    for parent_fd in _parent_descriptors(created):
        os.fsync(parent_fd)


def _unlink_created(created: list[_CreatedFile]) -> None:
    # Remove only files this invocation created, through the descriptor they
    # were created against rather than through their pathname.
    for entry in created:
        try:
            os.unlink(entry.name, dir_fd=entry.parent_fd)
        except FileNotFoundError:
            pass


def _close_parents(created: list[_CreatedFile]) -> None:
    for parent_fd in _parent_descriptors(created):
        os.close(parent_fd)


def write_run(run: CurationRun, source: Path, output: Path, manifest: Path) -> None:
    """Write a curation run to two absent destinations without clobbering."""

    source = Path(source)
    output = Path(output)
    manifest = Path(manifest)
    if output.resolve(strict=False) == manifest.resolve(strict=False):
        raise PreferenceCurationError("output and manifest destinations must differ")
    _assert_new_destination(source, output, "output")
    _assert_new_destination(source, manifest, "manifest")

    created: list[_CreatedFile] = []
    try:
        for path, payload in (
            (output, _jsonl_payload(run.records)),
            (manifest, _jsonl_payload(run.manifest)),
        ):
            _create_exclusive_file(path, payload, created)
        _fsync_parents(created)
    except BaseException:
        # Not `Exception`: a Ctrl-C during the payload write or the fsync
        # would otherwise leave a half-written transaction behind, and the
        # next run refuses to overwrite it.
        _unlink_created(created)
        raise
    finally:
        _close_parents(created)
