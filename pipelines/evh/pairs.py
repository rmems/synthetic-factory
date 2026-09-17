#!/usr/bin/env python3
"""Load the deferred EVH pair identities from compact ``pairs.jsonl``.

Rows are flat: mill_id + dest + r801-style identity keys. Dest catalogs stay
counts-only in ``CATALOG.json``. Metric constructor bodies stay on the
preserve-commit blobs.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from .catalog_extract import PAIR_ROW_KEYS, pairs_jsonl_path, sha256_bytes
from .vocabulary import FIRST_SLICE_MILL_ID, PAIRS_N_ROWS, PAIRS_SHA256

NESTED_REFUSAL_KEYS = ("catalogs", "pairs")


def load_pairs(path: Path | None = None) -> tuple[Mapping[str, Any], ...]:
    pairs_path = path if path is not None else pairs_jsonl_path()
    try:
        text = pairs_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ValueError(f"cannot load EVH pairs {pairs_path}: {exc}") from exc
    if "\r" in text or not text.endswith("\n"):
        raise ValueError(f"{pairs_path.name} must be LF-framed jsonl")
    rows = tuple(
        _pair_row(line, index, pairs_path.name)
        for index, line in enumerate(text.splitlines(), start=1)
    )
    if not rows:
        raise ValueError(f"{pairs_path.name} must contain deferred pair rows")
    if pairs_path.resolve() == pairs_jsonl_path().resolve():
        digest = sha256_bytes(text.encode())
        if digest != PAIRS_SHA256:
            raise ValueError("pairs.jsonl sha256 drifted from vocabulary")
        if len(rows) != PAIRS_N_ROWS:
            raise ValueError(
                f"pairs.jsonl must contain {PAIRS_N_ROWS} rows, found {len(rows)}"
            )
    return rows


def _pair_row(line: str, index: int, name: str) -> dict[str, Any]:
    ctx = f"{name}:{index}"
    if not line or line.startswith((" ", "\t")):
        raise ValueError(f"{ctx} is not a compact JSONL row")
    try:
        row = json.loads(line)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{ctx} is not JSON: {exc}") from exc
    if not isinstance(row, dict):
        raise ValueError(f"{ctx} must be an object")
    extra_nested = [key for key in NESTED_REFUSAL_KEYS if key in row]
    if extra_nested:
        raise ValueError(f"{ctx} nests dest objects: {extra_nested}")
    actual = set(row)
    expected = set(PAIR_ROW_KEYS)
    if actual != expected:
        raise ValueError(
            f"{ctx} keys differ: missing={sorted(expected - actual)} "
            f"extra={sorted(actual - expected)}"
        )
    mill_id = row["mill_id"]
    dest = row["dest"]
    if not isinstance(mill_id, str) or not mill_id:
        raise ValueError(f"{ctx} mill_id must be a non-empty string")
    if not isinstance(dest, str) or not dest:
        raise ValueError(f"{ctx} dest must be a non-empty string")
    if mill_id == FIRST_SLICE_MILL_ID:
        raise ValueError(f"{ctx} must omit the r801 first slice")
    return {key: row[key] for key in PAIR_ROW_KEYS}
