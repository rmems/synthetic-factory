"""Destination preflight and atomic writes for tag curation."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from tag_constants import RAW_OUTPUT_ROOT
from tag_jsonutil import canonical_json


def _has_raw_tree_components(path: Path) -> bool:
    """Whether normalized ``path`` names an ``outputs/raw`` tree."""
    parts = path.parts
    return any(
        parts[index : index + 2] == ("outputs", "raw")
        for index in range(len(parts) - 1)
    )


def _stat_identity(path: Path) -> tuple[int, int] | None:
    try:
        state = path.stat()
    except OSError:
        return None
    return state.st_dev, state.st_ino


def _ancestor_identities(path: Path) -> set[tuple[int, int]]:
    identities: set[tuple[int, int]] = set()
    current = Path(os.path.abspath(path))
    seen: set[Path] = set()
    while current not in seen:
        seen.add(current)
        identity = _stat_identity(current)
        if identity is not None:
            identities.add(identity)
        parent = current.parent
        if parent == current:
            break
        current = parent
    return identities


def _is_under_raw(path: Path) -> bool:
    """Whether ``path`` names or aliases the repository's raw output tree."""
    lexical_path = Path(os.path.abspath(path))
    resolved_path = path.resolve(strict=False)
    if _has_raw_tree_components(lexical_path) or _has_raw_tree_components(
        resolved_path
    ):
        return True
    raw_identity = _stat_identity(RAW_OUTPUT_ROOT)
    if raw_identity is None:
        return False
    return raw_identity in _ancestor_identities(
        path
    ) or raw_identity in _ancestor_identities(path.parent)


def _unlink_created_file(path: Path, identity: tuple[int, int]) -> None:
    """Remove ``path`` only when it still names the file this run created."""
    try:
        current = path.lstat()
    except FileNotFoundError:
        return
    if (current.st_dev, current.st_ino) == identity:
        path.unlink()


def _write_new_jsonl(
    path: Path, values: list[dict[str, Any]]
) -> tuple[int, int]:
    """Write one JSONL file without replacing any pre-existing path."""
    if _is_under_raw(path):
        raise ValueError(f"refusing to write inside immutable raw evidence: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    # O_EXCL is the atomic no-clobber gate; preflight is only an early diagnostic.
    try:
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    except FileExistsError as exc:
        raise FileExistsError(
            f"refusing to replace existing destination: {path}"
        ) from exc
    state = os.fstat(descriptor)
    identity = (state.st_dev, state.st_ino)
    if _is_under_raw(path) or _is_under_raw(path.resolve(strict=False)):
        os.close(descriptor)
        _unlink_created_file(path, identity)
        raise ValueError(f"refusing to write inside immutable raw evidence: {path}")
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


def _write_destinations(
    destinations: list[tuple[Path, list[dict[str, Any]]]],
) -> None:
    """Publish a destination set, rolling back this run's files on failure."""
    for path, _values in destinations:
        path.parent.mkdir(parents=True, exist_ok=True)
        if _is_under_raw(path) or _is_under_raw(path.parent):
            raise ValueError(
                f"refusing to write inside immutable raw evidence: {path}"
            )

    created: list[tuple[Path, tuple[int, int]]] = []
    try:
        for path, values in destinations:
            identity = _write_new_jsonl(path, values)
            created.append((path, identity))
    except BaseException:
        for path, identity in reversed(created):
            _unlink_created_file(path, identity)
        raise
