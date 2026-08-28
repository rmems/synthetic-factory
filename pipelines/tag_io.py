"""Destination preflight and transactional writes for tag curation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from tag_write import (
    _is_under_raw,
    _prepare_destination_parents,
    _unlink_created_file,
    _write_new_jsonl,
)

__all__ = (
    "_is_under_raw",
    "_preflight_destinations",
    "_unlink_created_file",
    "_write_destinations",
)


def _require_distinct_destinations(paths: list[Path]) -> list[Path]:
    resolved = [path.resolve(strict=False) for path in paths]
    if len(set(resolved)) != len(resolved):
        raise ValueError("output destinations must be distinct")
    return resolved


def _reject_nested_pair(path: Path, other: Path) -> None:
    if path in other.parents or other in path.parents:
        raise ValueError("output destinations must not contain one another")


def _reject_nested_destinations(resolved: list[Path]) -> None:
    for index, path in enumerate(resolved):
        for other in resolved[index + 1 :]:
            _reject_nested_pair(path, other)


def _reject_existing_destination(path: Path) -> None:
    if path.exists():
        raise FileExistsError(f"refusing to replace existing destination: {path}")


def _reject_raw_destination(path: Path) -> None:
    if _is_under_raw(path):
        raise ValueError(f"refusing to write inside immutable raw evidence: {path}")


def _preflight_one(path: Path) -> None:
    _reject_raw_destination(path)
    _reject_existing_destination(path)


def _preflight_destinations(paths: list[Path]) -> None:
    resolved = _require_distinct_destinations(paths)
    _reject_nested_destinations(resolved)
    for path in paths:
        _preflight_one(path)


def _create_destinations(
    destinations: list[tuple[Path, list[dict[str, Any]]]],
    created: list[tuple[Path, tuple[int, int]]],
) -> None:
    for path, values in destinations:
        identity = _write_new_jsonl(path, values)
        created.append((path, identity))


def _rollback_created(created: list[tuple[Path, tuple[int, int]]]) -> None:
    for path, identity in reversed(created):
        _unlink_created_file(path, identity)


def _write_destinations(
    destinations: list[tuple[Path, list[dict[str, Any]]]],
) -> None:
    """Publish a destination set, rolling back this run's files on failure."""
    _prepare_destination_parents(destinations)
    created: list[tuple[Path, tuple[int, int]]] = []
    try:
        _create_destinations(destinations, created)
    except BaseException:
        _rollback_created(created)
        raise
