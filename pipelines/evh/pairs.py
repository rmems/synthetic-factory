#!/usr/bin/env python3
"""Load the deferred EVH pair identities from compact ``pairs.jsonl``.

Rows are flat: mill_id + dest + r801-style identity keys. Dest catalogs stay
counts-only in ``CATALOG.json``. Metric constructor bodies stay on the
preserve-commit blobs.
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from ._jsonl_rows import (
    decode_object_row,
    parse_rows,
    read_lf_jsonl,
    require_exact_keys,
    require_pinned,
)
from .catalog_extract import PAIR_ROW_KEYS, pairs_jsonl_path
from .vocabulary import FIRST_SLICE_MILL_ID, PAIRS_N_ROWS, PAIRS_SHA256

NESTED_REFUSAL_KEYS = ("catalogs", "pairs")


def load_pairs(path: Path | None = None) -> tuple[Mapping[str, Any], ...]:
    pairs_path = path if path is not None else pairs_jsonl_path()
    text = read_lf_jsonl(pairs_path, "cannot load EVH pairs")
    rows = parse_rows(text, pairs_path.name, _pair_row, "must contain deferred pair rows")
    if pairs_path.resolve() == pairs_jsonl_path().resolve():
        require_pinned(text, rows, "pairs.jsonl", (PAIRS_SHA256, PAIRS_N_ROWS))
    return rows


def _pair_row(line: str, index: int, name: str) -> dict[str, Any]:
    ctx = f"{name}:{index}"
    row = decode_object_row(line, ctx)
    extra_nested = [key for key in NESTED_REFUSAL_KEYS if key in row]
    if extra_nested:
        raise ValueError(f"{ctx} nests dest objects: {extra_nested}")
    require_exact_keys(row, PAIR_ROW_KEYS, ctx)
    _require_pair_owner(row, ctx)
    return {key: row[key] for key in PAIR_ROW_KEYS}


def _require_pair_owner(row: Mapping[str, Any], ctx: str) -> None:
    mill_id = row["mill_id"]
    dest = row["dest"]
    if not isinstance(mill_id, str) or not mill_id:
        raise ValueError(f"{ctx} mill_id must be a non-empty string")
    if not isinstance(dest, str) or not dest:
        raise ValueError(f"{ctx} dest must be a non-empty string")
    if mill_id == FIRST_SLICE_MILL_ID:
        raise ValueError(f"{ctx} must omit the r801 first slice")
