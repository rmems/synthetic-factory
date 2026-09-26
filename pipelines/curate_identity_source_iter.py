#!/usr/bin/env python3
"""Committed source-record iteration for identity curation.

Split out of ``curate_identity_writer.py`` (CodeScene/qlty: High total
complexity) by responsibility; ``iter_source_records`` and the transaction
helpers remain re-exported from ``curate_identity`` so existing
``curate_identity.X`` call sites and test seams resolve unchanged.

Iteration yields only committed JSONL coordinates: symlinked entries,
uncommitted transaction payloads, and undecodable lines are refused rather
than skipped silently.
"""

from __future__ import annotations

import hashlib
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("curate_identity_source_iter")
    from . import curate_identity_json as _identity_json
    from . import curate_identity_sources as _sources
    from .round_txn import (
        TransactionError,
        committed_jsonl_paths,
        marker_mode_path,
    )
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "curate_identity_source_iter"
    )
    import curate_identity_json as _identity_json
    import curate_identity_sources as _sources
    from round_txn import (
        TransactionError,
        committed_jsonl_paths,
        marker_mode_path,
    )

IdentityCurationError = _identity_json.IdentityCurationError
SourceRecord = _sources.SourceRecord


def _fail(error: IdentityCurationError) -> None:
    """Raise ``error``; one raise site keeps fail-closed checks branch-light."""

    raise error


def _fail_chained(error: IdentityCurationError, cause: BaseException) -> None:
    """Raise ``error`` from ``cause`` for the single chained raise site."""

    raise error from cause


@dataclass(frozen=True)
class SourceIterDependencies:
    """Live facade JSON operations used while decoding source lines."""

    strict_json_loads: Callable[..., Any]
    is_json_whitespace: Callable[[str], bool]


def _marker_factory(
    jsonl_path: Path, enclosing_factory: dict[Path, Path | None]
) -> Path | None:
    """Return the transaction-marker root governing ``jsonl_path``, memoized."""

    visited: list[Path] = []
    current = jsonl_path.parent
    while True:
        if current in enclosing_factory:
            marker_root = enclosing_factory[current]
            break
        visited.append(current)
        if marker_mode_path(current) is not None:
            marker_root = current
            break
        parent = current.parent
        if parent == current:
            marker_root = None
            break
        current = parent
    for directory in visited:
        enclosing_factory[directory] = marker_root
    return marker_root


def _committed_member(
    path: Path, factory: Path, visible_by_factory: dict[Path, set[Path]]
) -> bool:
    if factory not in visible_by_factory:
        visible_by_factory[factory] = {
            candidate.resolve() for candidate in committed_jsonl_paths(factory)
        }
    return path.resolve() in visible_by_factory[factory]


def committed_source_paths(paths: Iterable[Path]) -> list[Path]:
    visible_by_factory: dict[Path, set[Path]] = {}
    enclosing_factory: dict[Path, Path | None] = {}
    visible: list[Path] = []
    for path in paths:
        factory = _marker_factory(path, enclosing_factory)
        if factory is None or _committed_member(path, factory, visible_by_factory):
            visible.append(path)
    return visible


def registered_factory_ancestor(directory: Path, registry) -> Path | None:
    for candidate in (directory, *directory.parents):
        if candidate.name in registry.by_path_id:
            return candidate
    return None


def source_relative_path(path: Path, source: Path, registry) -> str:
    factory_dir = registered_factory_ancestor(path.parent, registry)
    if factory_dir is not None:
        return path.relative_to(factory_dir.parent).as_posix()
    if source.is_file():
        return path.relative_to(path.parent.parent).as_posix()
    if path.parent == source:
        return path.relative_to(path.parent.parent).as_posix()
    return path.relative_to(source).as_posix()


def _directory_candidates(source: Path) -> list[Path]:
    jsonl_entries = sorted(source.rglob("*.jsonl"))
    symlink_entries = [path for path in jsonl_entries if path.is_symlink()]
    if symlink_entries:
        rendered = ", ".join(
            path.relative_to(source).as_posix() for path in symlink_entries
        )
        _fail(IdentityCurationError(
            f"source tree must not contain symlinked JSONL entries: {rendered}"
        ))
    candidates = [path for path in jsonl_entries if path.is_file()]
    if not candidates:
        _fail(IdentityCurationError(f"no JSONL files under source: {source}"))
    return candidates


def _source_candidates(source: Path) -> list[Path]:
    if source.is_file():
        if source.suffix != ".jsonl":
            _fail(IdentityCurationError(f"source is not a JSONL file: {source}"))
        if not source.parent.name:
            _fail(IdentityCurationError(
                f"JSONL source must be inside a factory directory: {source}"
            ))
        return [source]
    if source.is_dir():
        return _directory_candidates(source)
    _fail(IdentityCurationError(
        f"source is not a JSONL file or directory: {source}"
    ))


def _committed_candidates(source: Path, candidates: list[Path]) -> list[Path]:
    try:
        files = committed_source_paths(candidates)
    except TransactionError as exc:
        _fail_chained(IdentityCurationError(
            f"invalid source transaction state: {exc}"
        ), exc)
    if not files:
        _fail(IdentityCurationError(
            f"no committed JSONL files under source: {source}"
        ))
    return files


def _source_line_payload(physical_line: bytes) -> bytes:
    line_bytes = physical_line
    if line_bytes.endswith(b"\n"):
        line_bytes = line_bytes[:-1]
        if line_bytes.endswith(b"\r"):
            line_bytes = line_bytes[:-1]
    return line_bytes


def _decode_source_line(line_bytes: bytes, rel: str, line_no: int) -> str:
    try:
        return line_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        _fail_chained(IdentityCurationError(
            f"UTF-8 decode error at {rel}:{line_no}: {exc}"
        ), exc)


def _read_source_records(
    path: Path, rel: str, records: list, deps: SourceIterDependencies
) -> None:
    with path.open("rb") as handle:
        for line_no, physical_line in enumerate(handle, 1):
            line_bytes = _source_line_payload(physical_line)
            line = _decode_source_line(line_bytes, rel, line_no)
            if not line or deps.is_json_whitespace(line):
                continue
            try:
                obj = deps.strict_json_loads(line)
            except ValueError as exc:
                _fail_chained(IdentityCurationError(
                    f"JSON parse error at {rel}:{line_no}: {exc}"
                ), exc)
            digest = hashlib.sha256(line_bytes).hexdigest()
            records.append(SourceRecord(obj, rel, line_no, digest, line))


def iter_source_records(
    source: Path, registry, deps: SourceIterDependencies
) -> list[SourceRecord]:
    """Read JSONL records under ``source`` as identity source coordinates."""

    source = Path(source)
    if not source.exists():
        _fail(IdentityCurationError(f"source does not exist: {source}"))
    if source.is_symlink():
        _fail(IdentityCurationError(f"source must not be a symlink: {source}"))
    files = _committed_candidates(source, _source_candidates(source))
    records: list[SourceRecord] = []
    for path in files:
        _read_source_records(
            path, source_relative_path(path, source, registry), records, deps
        )
    return records


if __package__:
    _expose_package_sibling(__name__)
