#!/usr/bin/env python3
"""The persisted duplicate index: kept-proposal keys across runs, read-only until a new write.

A key is ``sha256(program_id, span, replacement_text)`` over exact-JSON bytes of
``[KEY_FORMAT, program_id, start_byte, end_byte, replacement_text]``. Only kept proposals
are indexed: a rejected proposal is deterministic and is re-rejected on its own merits, so
the index stays the list of tasks that already exist. Each run reads every prior index file
it is given and writes a new, cumulative ``dedup-index.jsonl`` into its own new destination;
no existing file is touched, and the next run needs only the newest one.
"""

from __future__ import annotations

import hashlib
import os
import re
import stat
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import vocabulary as cv
from ._contract import (
    StrictJsonlError, bind_import_twin, dumps_exact_json, load_strict_json, strict_lf_jsonl_lines,
)

__all__ = ["PriorIndex", "dedup_key", "index_bytes", "load_prior"]

_KEY = re.compile(r"[0-9a-f]{64}")
_FIELDS = frozenset({"format", "key", "program_id", "start_byte", "end_byte"})


def dedup_key(program_id: str, start_byte: int, end_byte: int, replacement_text: str) -> str:
    payload = dumps_exact_json([cv.KEY_FORMAT, program_id, start_byte, end_byte, replacement_text])
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class PriorIndex:
    """Every key seen in prior runs, the rows that carry them, and each file's digest."""

    rows: Mapping[str, dict[str, Any]]
    files: tuple[dict[str, Any], ...]

    def __contains__(self, key: object) -> bool:
        return key in self.rows

    @classmethod
    def empty(cls) -> PriorIndex:
        return cls({}, ())


def _row_is_sound(row: object) -> bool:
    if not isinstance(row, dict) or set(row) != _FIELDS or row["format"] != cv.INDEX_FORMAT:
        return False
    spans = (row["start_byte"], row["end_byte"])
    return (
        isinstance(row["key"], str) and _KEY.fullmatch(row["key"]) is not None
        and isinstance(row["program_id"], str) and bool(row["program_id"])
        and all(isinstance(n, int) and not isinstance(n, bool) and n >= 0 for n in spans)
    )


def _read(path: Path) -> bytes:
    try:
        cv.refuse_when(
            not stat.S_ISREG(os.stat(path).st_mode), cv.REFUSE_INDEX_UNREADABLE,
            f"prior index {path} is not a regular file",
        )
        with path.open("rb") as handle:
            data = handle.read(cv.MAX_INDEX_BYTES + 1)
    except OSError as exc:
        raise cv.GateRefusal(cv.REFUSE_INDEX_UNREADABLE, f"prior index {path}: {exc}") from exc
    cv.refuse_when(
        len(data) > cv.MAX_INDEX_BYTES, cv.REFUSE_INDEX_MALFORMED, f"prior index {path} is too large",
    )
    return data


def _parse_file(path: Path, data: bytes) -> list[dict[str, Any]]:
    try:
        lines = strict_lf_jsonl_lines(data, str(path))
        rows = [load_strict_json(line) for line in lines]
    except (StrictJsonlError, ValueError, RecursionError) as exc:
        raise cv.GateRefusal(cv.REFUSE_INDEX_MALFORMED, f"prior index {path}: {exc}") from exc
    bad = next((n for n, row in enumerate(rows, 1) if not _row_is_sound(row)), None)
    cv.refuse_when(bad is not None, cv.REFUSE_INDEX_MALFORMED, f"prior index {path}:{bad} is not an index row")
    keys = [row["key"] for row in rows]
    cv.refuse_when(
        len(set(keys)) != len(keys), cv.REFUSE_INDEX_MALFORMED, f"prior index {path} repeats a key",
    )
    return rows


def load_prior(paths: Iterable[Path | str]) -> PriorIndex:
    """Union of the given index files; an absent or malformed file refuses the run."""

    merged: dict[str, dict[str, Any]] = {}
    files: list[dict[str, Any]] = []
    for item in paths:
        path = Path(item)
        data = _read(path)
        rows = _parse_file(path, data)
        files.append({"path": path.name, "sha256": hashlib.sha256(data).hexdigest(), "keys": len(rows)})
        for row in rows:
            merged.setdefault(row["key"], row)
    return PriorIndex(merged, tuple(files))


def index_bytes(rows: Iterable[Mapping[str, Any]]) -> bytes:
    """Deterministic index bytes: one exact-JSON row per key, sorted by key."""

    ordered = sorted(rows, key=lambda row: row["key"])
    return "".join(dumps_exact_json(dict(row)) + "\n" for row in ordered).encode("utf-8")


bind_import_twin(__name__)
