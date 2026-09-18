#!/usr/bin/env python3
"""Load Archive C leftover plant pair identities from compact JSONL."""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from .catalog_extract import sha256_bytes
from .plants_extract import leftover_plants_b_jsonl_path
from .vocabulary import (
    ARCHIVE_C_PATH,
    LEFTOVER_PLANTS_B_N_ROWS,
    LEFTOVER_PLANTS_B_SHA256,
    LEFTOVER_PLANT_ROW_KEYS,
)


def load_leftover_plants_b(path: Path | None = None) -> tuple[Mapping[str, Any], ...]:
    plants_path = path if path is not None else leftover_plants_b_jsonl_path()
    try:
        text = plants_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ValueError(f"cannot load EVH leftover plants b {plants_path}: {exc}") from exc
    if "\r" in text or not text.endswith("\n"):
        raise ValueError(f"{plants_path.name} must be LF-framed jsonl")
    rows = tuple(
        _plant_row(line, index, plants_path.name)
        for index, line in enumerate(text.splitlines(), start=1)
    )
    if not rows:
        raise ValueError(f"{plants_path.name} must contain leftover plant rows")
    if plants_path.resolve() == leftover_plants_b_jsonl_path().resolve():
        digest = sha256_bytes(text.encode())
        if digest != LEFTOVER_PLANTS_B_SHA256:
            raise ValueError("leftover-plants-b.jsonl sha256 drifted from vocabulary")
        if len(rows) != LEFTOVER_PLANTS_B_N_ROWS:
            raise ValueError(
                f"leftover-plants-b.jsonl must contain {LEFTOVER_PLANTS_B_N_ROWS} rows, "
                f"found {len(rows)}"
            )
    return rows


def _plant_row(line: str, index: int, name: str) -> dict[str, Any]:
    ctx = f"{name}:{index}"
    if not line or line.startswith((" ", "\t")):
        raise ValueError(f"{ctx} is not a compact JSONL row")
    try:
        row = json.loads(line)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{ctx} is not JSON: {exc}") from exc
    if not isinstance(row, dict):
        raise ValueError(f"{ctx} must be an object")
    actual = set(row)
    expected = set(LEFTOVER_PLANT_ROW_KEYS)
    if actual != expected:
        raise ValueError(
            f"{ctx} keys differ: missing={sorted(expected - actual)} "
            f"extra={sorted(actual - expected)}"
        )
    pair_index = row["index"]
    if not isinstance(pair_index, int) or isinstance(pair_index, bool):
        raise ValueError(f"{ctx} index must be an int")
    for key in LEFTOVER_PLANT_ROW_KEYS:
        if key == "index":
            continue
        if not isinstance(row[key], str) or not row[key]:
            raise ValueError(f"{ctx} {key} must be a non-empty string")
    if row["source"] != ARCHIVE_C_PATH:
        raise ValueError(f"{ctx} source must be {ARCHIVE_C_PATH}")
    return {key: row[key] for key in LEFTOVER_PLANT_ROW_KEYS}
