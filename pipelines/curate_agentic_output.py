#!/usr/bin/env python3
"""Write a cleaned tree, or write nothing at all.

Every path that puts curated bytes on disk lives here, and each one is
fail-closed by construction: nothing is written inside ``outputs/raw/``,
nothing replaces an existing destination, and a failure part-way through
removes whatever the attempt already created rather than leaving a half
tree behind. Metadata is deliberately written as ``.json`` and never
``.jsonl``, because every validator and training audit in this repo treats
that extension as record payload.

Deciding *what* to write is ``curate_agentic.py``'s job; this module only
decides whether writing it is safe, and makes the write atomic.

Split out of ``curate_agentic.py`` verbatim; ``write_cleaned_tree`` is
re-exported from ``curate_agentic`` so existing call sites resolve unchanged.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from curate_agentic_shapes import canonical_json


def is_under_raw(path: Path) -> bool:
    """True when ``path`` resolves inside the immutable raw evidence tree."""
    parts = path.resolve(strict=False).parts
    return any(
        parts[index : index + 2] == ("outputs", "raw")
        for index in range(len(parts) - 1)
    )


def _reject_unwritable_destination(out: Path) -> None:
    """Refuse a destination that is raw evidence, or that already exists."""
    if is_under_raw(out):
        raise ValueError(f"refusing to write inside immutable raw evidence: {out}")
    if out.exists():
        raise FileExistsError(f"refusing to replace existing destination: {out}")


def preflight_out(source: Path, out: Path) -> None:
    """Refuse an output destination that would damage or shadow the source."""
    _reject_unwritable_destination(out)
    source_resolved = source.resolve(strict=False)
    out_resolved = out.resolve(strict=False)
    if source_resolved == out_resolved:
        raise ValueError(f"output cannot replace source: {out}")
    if source.is_dir() and source_resolved in out_resolved.parents:
        raise ValueError(f"output cannot be written inside source: {out}")


def _open_new(path: Path):
    """Create ``path`` exclusively, refusing raw evidence, and return the fd."""
    if is_under_raw(path):
        raise ValueError(f"refusing to write inside immutable raw evidence: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    return os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)


def write_new_jsonl(path: Path, values: list[dict[str, Any]]) -> None:
    descriptor = _open_new(path)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            for value in values:
                handle.write(canonical_json(value))
                handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
    except BaseException:
        path.unlink(missing_ok=True)
        raise


def write_new_json(path: Path, value: Any) -> None:
    """Write one metadata document without making it a record-scanner input."""
    descriptor = _open_new(path)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(value, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
    except BaseException:
        path.unlink(missing_ok=True)
        raise


def _require_quarantine_applied(run: dict[str, Any]) -> None:
    """Refuse to write unless the run resolved multi-factory mill ownership."""
    summary = run.get("summary")
    mill_summary = (
        summary.get("mill_family") if isinstance(summary, dict) else None
    )
    if not isinstance(mill_summary, dict) or (
        mill_summary.get("quarantine_applied") is not True
    ):
        raise ValueError(
            "refusing cleaned output without multi-factory mill ownership context"
        )


def _unlink_quietly(path: Path) -> None:
    """Remove one file, tolerating one that is already gone."""
    try:
        path.unlink()
    except FileNotFoundError:
        pass


def _rmdir_quietly(path: Path) -> None:
    """Remove one directory, tolerating a missing or still-populated one."""
    try:
        path.rmdir()
    except OSError:
        pass


def _purge_contents(out: Path) -> None:
    """Remove everything under ``out``, deepest entry first."""
    for leftover in sorted(out.rglob("*"), reverse=True):
        if leftover.is_file():
            leftover.unlink(missing_ok=True)
        elif leftover.is_dir():
            _rmdir_quietly(leftover)


def _remove_partial_tree(out: Path, created: list[Path]) -> None:
    """Undo a part-written tree, deepest entry first."""
    for path in reversed(created):
        _unlink_quietly(path)
    if out.exists() and out.is_dir():
        _purge_contents(out)
        _rmdir_quietly(out)


def _write_tree(run: dict[str, Any], out: Path, created: list[Path]) -> None:
    """Write the records and the two metadata documents, tracking what exists."""
    out.mkdir(parents=True, exist_ok=False)
    for relative, records in sorted(run["records_by_rel"].items()):
        dest = out / relative
        write_new_jsonl(dest, records)
        created.append(dest)
    # Metadata must not have a .jsonl suffix: every standard validator and
    # training audit recursively treats that extension as record payload.
    manifest_path = out / "CURATE-MANIFEST.json"
    write_new_json(manifest_path, run["decisions"])
    created.append(manifest_path)
    report_path = out / "CURATE-REPORT.json"
    write_new_json(report_path, run["summary"])
    created.append(report_path)


def write_cleaned_tree(run: dict[str, Any], out: Path) -> None:
    """Write retained JSONL plus scanner-safe JSON metadata in a new directory."""
    _require_quarantine_applied(run)
    out = Path(out)
    created: list[Path] = []
    try:
        _write_tree(run, out, created)
    except BaseException:
        _remove_partial_tree(out, created)
        raise
