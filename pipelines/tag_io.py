"""Destination preflight and atomic writes for tag curation."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from tag_constants import RAW_OUTPUT_ROOT
from tag_jsonutil import canonical_json

try:
    from pipelines.raw_tree_guard import is_under_raw as _is_under_raw_tree
except ImportError:
    from raw_tree_guard import is_under_raw as _is_under_raw_tree


def _is_under_raw(path: Path) -> bool:
    return _is_under_raw_tree(path, RAW_OUTPUT_ROOT)


def _unlink_created_file(path: Path, identity: tuple[int, int]) -> None:
    """Remove ``path`` only when it still names the file this run created."""
    try:
        current = path.lstat()
    except FileNotFoundError:
        return
    if (current.st_dev, current.st_ino) == identity:
        path.unlink()


def _open_exclusive(path: Path) -> tuple[int, tuple[int, int]]:
    try:
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    except FileExistsError as exc:
        raise FileExistsError(
            f"refusing to replace existing destination: {path}"
        ) from exc
    state = os.fstat(descriptor)
    return descriptor, (state.st_dev, state.st_ino)


def _refuse_if_raw(path: Path, descriptor: int, identity: tuple[int, int]) -> None:
    if _is_under_raw(path) or _is_under_raw(path.resolve(strict=False)):
        os.close(descriptor)
        _unlink_created_file(path, identity)
        raise ValueError(f"refusing to write inside immutable raw evidence: {path}")


def _write_new_jsonl(
    path: Path, values: list[dict[str, Any]]
) -> tuple[int, int]:
    """Write one JSONL file without replacing any pre-existing path."""
    if _is_under_raw(path):
        raise ValueError(f"refusing to write inside immutable raw evidence: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, identity = _open_exclusive(path)
    _refuse_if_raw(path, descriptor, identity)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            for value in values:
                handle.write(canonical_json(value))
                handle.write("\n")
    except BaseException:
        _unlink_created_file(path, identity)
        raise
    return identity


def _preflight_destinations(paths: list[Path]) -> None:
    resolved = [path.resolve(strict=False) for path in paths]
    if len(set(resolved)) != len(resolved):
        raise ValueError("output destinations must be distinct")
    _reject_nested_destinations(resolved)
    for path in paths:
        if _is_under_raw(path):
            raise ValueError(
                f"refusing to write inside immutable raw evidence: {path}"
            )
        if path.exists():
            raise FileExistsError(
                f"refusing to replace existing destination: {path}"
            )


def _reject_nested_destinations(resolved: list[Path]) -> None:
    for index, path in enumerate(resolved):
        for other in resolved[index + 1 :]:
            if path in other.parents or other in path.parents:
                raise ValueError(
                    "output destinations must not contain one another"
                )


def _prepare_destination_parents(
    destinations: list[tuple[Path, list[dict[str, Any]]]],
) -> None:
    for path, _values in destinations:
        path.parent.mkdir(parents=True, exist_ok=True)
        if _is_under_raw(path) or _is_under_raw(path.parent):
            raise ValueError(
                f"refusing to write inside immutable raw evidence: {path}"
            )


def _write_destinations(
    destinations: list[tuple[Path, list[dict[str, Any]]]],
) -> None:
    """Publish a destination set, rolling back this run's files on failure."""
    _prepare_destination_parents(destinations)
    created: list[tuple[Path, tuple[int, int]]] = []
    try:
        for path, values in destinations:
            identity = _write_new_jsonl(path, values)
            created.append((path, identity))
    except BaseException:
        for path, identity in reversed(created):
            _unlink_created_file(path, identity)
        raise
