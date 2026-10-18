"""Shared compact-JSONL framing and row checks for the EVH identity loaders.

Each loader keeps its own error wording; these helpers take the wording (or
the label it is built from) as an argument and never add a default.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Any

from .catalog_extract import sha256_bytes
from .vocabulary import LEFTOVER_PLANT_ROW_KEYS


def read_lf_jsonl(path: Path, load_error: str) -> str:
    """Read ``path`` and require LF framing with a trailing newline."""

    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ValueError(f"{load_error} {path}: {exc}") from exc
    if not _is_lf_framed(text):
        raise ValueError(f"{path.name} must be LF-framed jsonl")
    return text


def _is_lf_framed(text: str) -> bool:
    return "\r" not in text and text.endswith("\n")


def parse_rows(
    text: str,
    name: str,
    parse_row: Callable[[str, int, str], dict[str, Any]],
    empty_error: str,
) -> tuple[dict[str, Any], ...]:
    rows = tuple(
        parse_row(line, index, name) for index, line in enumerate(text.splitlines(), start=1)
    )
    if not rows:
        raise ValueError(f"{name} {empty_error}")
    return rows


def require_pinned(
    text: str,
    rows: Sequence[Mapping[str, Any]],
    label: str,
    pins: tuple[str, int],
) -> None:
    """Bind a canonical file to its vocabulary ``(sha256, n_rows)`` pins."""

    expected_sha, expected_n = pins
    if sha256_bytes(text.encode()) != expected_sha:
        raise ValueError(f"{label} sha256 drifted from vocabulary")
    if len(rows) != expected_n:
        raise ValueError(f"{label} must contain {expected_n} rows, found {len(rows)}")


def decode_object_row(line: str, ctx: str) -> dict[str, Any]:
    if not _is_compact_line(line):
        raise ValueError(f"{ctx} is not a compact JSONL row")
    try:
        row = json.loads(line)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{ctx} is not JSON: {exc}") from exc
    if not isinstance(row, dict):
        raise ValueError(f"{ctx} must be an object")
    return row


def _is_compact_line(line: str) -> bool:
    return bool(line) and not line.startswith((" ", "\t"))


def require_exact_keys(row: Mapping[str, Any], keys: Sequence[str], ctx: str) -> None:
    actual = set(row)
    expected = set(keys)
    if actual != expected:
        raise ValueError(
            f"{ctx} keys differ: missing={sorted(expected - actual)} "
            f"extra={sorted(actual - expected)}"
        )


def plant_row(line: str, ctx: str, source_path: str | None) -> dict[str, Any]:
    """One leftover plant identity; ``source_path`` pins the ``source`` field."""

    row = decode_object_row(line, ctx)
    require_exact_keys(row, LEFTOVER_PLANT_ROW_KEYS, ctx)
    _require_plant_fields(row, ctx)
    if source_path is not None and row["source"] != source_path:
        raise ValueError(f"{ctx} source must be {source_path}")
    return {key: row[key] for key in LEFTOVER_PLANT_ROW_KEYS}


_PLANT_TEXT_KEYS = tuple(key for key in LEFTOVER_PLANT_ROW_KEYS if key != "index")


def _require_plant_fields(row: Mapping[str, Any], ctx: str) -> None:
    if not _is_int(row["index"]):
        raise ValueError(f"{ctx} index must be an int")
    for key in _PLANT_TEXT_KEYS:
        if not _is_nonempty_str(row[key]):
            raise ValueError(f"{ctx} {key} must be a non-empty string")


def _is_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _is_nonempty_str(value: Any) -> bool:
    return isinstance(value, str) and bool(value)
