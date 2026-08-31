#!/usr/bin/env python3
"""Exact-member filesystem reading for the export authenticator.

Split out of ``export_hf.py`` by responsibility: every COMPOSE member is
resolved without symlink or hard-link aliases, read through a pinned
descriptor that rejects identity changes, and parsed as LF-framed JSONL.
"""

from __future__ import annotations

import hashlib
import os
import stat
from pathlib import Path, PurePosixPath
from typing import Any

from export_contract import ExportError, _loads_json

def _contains_raw_segments(parts: tuple[str, ...]) -> bool:
    return any(
        parts[index : index + 2] == ("outputs", "raw")
        for index in range(len(parts) - 1)
    )


def _is_under_raw(path: Path) -> bool:
    """Reject both a lexical raw path and a symlink-resolved raw destination."""

    return _contains_raw_segments(path.parts) or _contains_raw_segments(
        path.resolve(strict=False).parts
    )


def _member_relative(raw_path: Any, label: str) -> PurePosixPath:
    """Validate one member path as a canonical, contained POSIX relative."""

    if not isinstance(raw_path, str) or not raw_path or "\\" in raw_path:
        raise ExportError(f"{label}: path must be a nonempty POSIX string")
    relative = PurePosixPath(raw_path)
    non_canonical = relative.as_posix() != raw_path or relative.is_absolute()
    if non_canonical or any(part in {"", ".", ".."} for part in relative.parts):
        raise ExportError(f"{label}: unsafe relative path {raw_path!r}")
    return relative


def _require_inside_root(
    curated_root: Path, candidate: Path, relative: PurePosixPath, label: str
) -> None:
    """Refuse a member whose resolution aliases or escapes its root."""

    raw_path = relative.as_posix()
    try:
        root_resolved = curated_root.resolve(strict=True)
        resolved = candidate.resolve(strict=True)
    except FileNotFoundError as exc:
        raise ExportError(f"{label}: declared file is missing: {raw_path}") from exc
    expected = root_resolved.joinpath(*relative.parts)
    if resolved != expected or root_resolved not in resolved.parents:
        raise ExportError(f"{label}: path is a symlink alias or escapes its root: {raw_path}")


def _require_unique_regular(candidate: Path, raw_path: str, label: str) -> None:
    """Refuse anything but a hard-link-free regular file at the member path."""

    try:
        metadata = candidate.lstat()
    except FileNotFoundError as exc:
        raise ExportError(f"{label}: declared file is missing: {raw_path}") from exc
    if not stat.S_ISREG(metadata.st_mode):
        raise ExportError(f"{label}: path is not an exact regular file: {raw_path}")
    if metadata.st_nlink != 1:
        raise ExportError(f"{label}: hard-link aliases are not accepted: {raw_path}")


def _compose_member_path(curated_root: Path, raw_path: Any, label: str) -> Path:
    """Resolve one exact regular COMPOSE member without aliases or tree escape."""

    relative = _member_relative(raw_path, label)
    candidate = curated_root.joinpath(*relative.parts)
    _require_inside_root(curated_root, candidate, relative, label)
    _require_unique_regular(candidate, raw_path, label)
    return candidate


def _read_pinned_descriptor(
    path: Path, before: os.stat_result, raw_path: Any, label: str
) -> tuple[os.stat_result, bytes]:
    """Open without following links, validate the descriptor, read it fully."""

    # O_NONBLOCK keeps a member swapped for a FIFO from hanging the open;
    # the fstat below then rejects it. Regular-file reads ignore the flag.
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | os.O_NONBLOCK
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise ExportError(f"{label}: cannot open exact regular file {raw_path!r}: {exc}") from exc
    try:
        opened = os.fstat(descriptor)
        if not stat.S_ISREG(opened.st_mode) or opened.st_nlink != 1:
            raise ExportError(f"{label}: opened identity is not a unique regular file")
        if (before.st_dev, before.st_ino) != (opened.st_dev, opened.st_ino):
            raise ExportError(f"{label}: path identity changed while opening")
        chunks: list[bytes] = []
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            chunks.append(chunk)
    finally:
        os.close(descriptor)
    return opened, b"".join(chunks)


def _read_exact_regular_file(root: Path, raw_path: Any, label: str) -> tuple[Path, bytes]:
    """Read one path through a pinned descriptor and reject identity changes."""

    path = _compose_member_path(root, raw_path, label)
    before = path.lstat()
    opened, payload = _read_pinned_descriptor(path, before, raw_path, label)
    after = path.lstat()
    if (after.st_dev, after.st_ino) != (opened.st_dev, opened.st_ino):
        raise ExportError(f"{label}: path identity changed while reading")
    if path.resolve(strict=True) != root.resolve(strict=True).joinpath(
        *PurePosixPath(str(raw_path)).parts
    ):
        raise ExportError(f"{label}: path became a symlink alias while reading")
    return path, payload


def _lf_jsonl_documents(payload: bytes, label: str) -> list[Any]:
    """Parse JSONL with LF as the only record separator."""

    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ExportError(f"{label}: payload is not UTF-8: {exc}") from exc
    if text and not text.endswith("\n"):
        raise ExportError(f"{label}: JSONL must end with a newline")
    lines = text.split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    documents: list[Any] = []
    for line_number, line in enumerate(lines, 1):
        if not line.strip():
            raise ExportError(f"{label}:{line_number}: JSONL has a blank line")
        documents.append(_loads_json(line, f"{label}:{line_number}"))
    return documents


def _authenticated_descriptor(
    curated_root: Path,
    summary: dict[str, Any],
    key: str,
    expected_path: str,
) -> tuple[dict[str, Any], list[Any]]:
    descriptor = summary.get(key)
    if not isinstance(descriptor, dict):
        raise ExportError(f"COMPOSE.json: {key} descriptor must be an object")
    if descriptor.get("path") != expected_path:
        raise ExportError(
            f"COMPOSE.json: {key} path must be {expected_path!r}, "
            f"got {descriptor.get('path')!r}"
        )
    _path, payload = _read_exact_regular_file(
        curated_root, descriptor["path"], f"COMPOSE {key}"
    )
    digest = hashlib.sha256(payload).hexdigest()
    if descriptor.get("sha256") != digest:
        raise ExportError(f"COMPOSE.json: {key} digest mismatch")
    documents = _lf_jsonl_documents(payload, descriptor["path"])
    entries = descriptor.get("entries")
    if isinstance(entries, bool) or not isinstance(entries, int) or entries < 0:
        raise ExportError(f"COMPOSE.json: {key}.entries must be nonnegative")
    if entries != len(documents):
        raise ExportError(
            f"COMPOSE.json: {key} entry count {entries} != {len(documents)}"
        )
    return dict(descriptor), documents


def _require_exact_directory(path: Path, label: str) -> Path:
    """Require a real directory reached without a symlinked path alias."""

    try:
        metadata = path.lstat()
        resolved = path.resolve(strict=True)
    except FileNotFoundError as exc:
        raise ExportError(f"{label}: directory is missing: {path}") from exc
    absolute = Path(os.path.abspath(path))
    if not stat.S_ISDIR(metadata.st_mode) or resolved != absolute:
        raise ExportError(f"{label}: directory path must be an exact non-symlink identity")
    return resolved

def iter_alias_free_jsonl(root: Path, label: str) -> list[Path]:
    """Enumerate every JSONL under ``root``, refusing any symlink entry.

    ``Path.rglob`` silently skips a symlinked directory, so an aliased
    subtree — and every JSONL visible through it — would simply vanish from
    the snapshot instead of failing closed.
    """

    members: list[Path] = []
    pending = [Path(root)]
    while pending:
        directory = pending.pop()
        try:
            with os.scandir(directory) as scan:
                entries = sorted(scan, key=lambda entry: entry.name)
        except OSError as exc:
            raise ExportError(f"{label}: cannot enumerate {directory}: {exc}") from exc
        for entry in entries:
            try:
                metadata = entry.stat(follow_symlinks=False)
            except OSError as exc:
                raise ExportError(
                    f"{label}: cannot inspect {entry.path}: {exc}"
                ) from exc
            if stat.S_ISLNK(metadata.st_mode):
                raise ExportError(
                    f"{label}: tree contains a symlink alias: {entry.path}"
                )
            if stat.S_ISDIR(metadata.st_mode):
                pending.append(Path(entry.path))
            elif entry.name.endswith(".jsonl"):
                members.append(Path(entry.path))
    return sorted(members)
