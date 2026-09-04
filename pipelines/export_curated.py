#!/usr/bin/env python3
"""Read the curated corpus exactly and fingerprint it for the export snapshot.

Split out of ``export_hf.py`` by responsibility: every curated JSONL file is
read through the exact-member reader, proven to reproduce its own bytes line
by line, and reduced to the byte snapshot the audit and the replay authenticate.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Sequence

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("export_curated")
    from .export_contract import (
        CURATED_DIRNAME,
        CuratedFile,
        ExportError,
        ViewerRow,
        _loads_json,
    )
    from .export_members import _lf_jsonl_lines, _read_exact_regular_file, iter_alias_free_jsonl
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "export_curated"
    )
    from export_contract import (
        CURATED_DIRNAME,
        CuratedFile,
        ExportError,
        ViewerRow,
        _loads_json,
    )
    from export_members import _lf_jsonl_lines, _read_exact_regular_file, iter_alias_free_jsonl


def _read_curated_file(
    path: Path, relative: str, *, payload: bytes | None = None
) -> CuratedFile:
    """Read one curated JSONL file and prove its lines reproduce its bytes."""

    source_file = f"{CURATED_DIRNAME}/{relative}"
    payload = path.read_bytes() if payload is None else payload
    lines = _lf_jsonl_lines(payload, f"{relative}: curated")
    rows: list[ViewerRow] = []
    for line_number, line in enumerate(lines, 1):
        _loads_json(line, f"{relative}:{line_number}: curated line")
        rows.append(
            ViewerRow(
                source_file=source_file, source_line=line_number, record_json=line
            )
        )
    # Every physical line is now one row with its own line number, so the rows
    # rebuild ``payload`` exactly and the exported copy can be the source bytes.
    return CuratedFile(source_file=source_file, payload=payload, rows=tuple(rows))


def collect_files(records_dir: Path) -> list[CuratedFile]:
    """Read every curated JSONL file in stable path order."""

    files: list[CuratedFile] = []
    for path in iter_alias_free_jsonl(records_dir, "curated records"):
        relative = path.relative_to(records_dir).as_posix()
        exact_path, payload = _read_exact_regular_file(
            records_dir, relative, f"curated payload {relative}"
        )
        files.append(_read_curated_file(exact_path, relative, payload=payload))
    return files


def collect_rows(records_dir: Path) -> list[ViewerRow]:
    """Read every curated JSONL line in stable path and line order."""

    return [row for curated in collect_files(records_dir) for row in curated.rows]


def _snapshot_relative_path(curated: CuratedFile) -> str:
    """Return one curated payload path relative to the records directory."""

    prefix = f"{CURATED_DIRNAME}/"
    if not curated.source_file.startswith(prefix):
        raise ExportError(f"invalid curated source path: {curated.source_file}")
    return curated.source_file.removeprefix(prefix)


def _snapshot_payloads(curated_files: Sequence[CuratedFile]) -> dict[str, bytes]:
    """Build an unambiguous relative-path to exact-byte snapshot."""

    snapshot: dict[str, bytes] = {}
    for curated in curated_files:
        relative = _snapshot_relative_path(curated)
        if relative in snapshot:
            raise ExportError(f"duplicate curated snapshot path: {relative}")
        snapshot[relative] = curated.payload
    return snapshot


def _curated_snapshot_fingerprint(
    files: Sequence[CuratedFile],
) -> tuple[tuple[str, ...], tuple[bytes, ...]]:
    """Return the member names and payloads that define one curated snapshot."""

    return (
        tuple(item.source_file for item in files),
        tuple(item.payload for item in files),
    )


if __package__:
    _expose_package_sibling(__name__)
