#!/usr/bin/env python3
"""Load Archive C letter-suffix leftover plant identities from compact JSONL."""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from .catalog_extract import sha256_bytes
from .plants_extract import leftover_plants_letter_jsonl_path
from .vocabulary import LEFTOVER_LETTER_PINS, LEFTOVER_PLANT_ROW_KEYS


def load_leftover_plants_letter(
    letter: str,
    path: Path | None = None,
) -> tuple[Mapping[str, Any], ...]:
    if letter not in LEFTOVER_LETTER_PINS:
        raise ValueError(f"unknown leftover plants letter {letter!r}")
    pin = LEFTOVER_LETTER_PINS[letter]
    plants_path = path if path is not None else leftover_plants_letter_jsonl_path(letter)
    try:
        text = plants_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ValueError(f"cannot load EVH leftover plants {letter} {plants_path}: {exc}") from exc
    if "\r" in text or not text.endswith("\n"):
        raise ValueError(f"{plants_path.name} must be LF-framed jsonl")
    source_path = str(pin["path"])
    expected_n = int(pin["n_rows"])
    rows = tuple(
        _plant_row(line, index, plants_path.name, source_path)
        for index, line in enumerate(text.splitlines(), start=1)
    )
    if not rows:
        raise ValueError(f"{plants_path.name} must contain leftover plant rows")
    canonical = leftover_plants_letter_jsonl_path(letter)
    if plants_path.resolve() == canonical.resolve():
        digest = sha256_bytes(text.encode())
        expected_sha = str(pin["plants_sha256"])
        if digest != expected_sha:
            raise ValueError(f"{plants_path.name} sha256 drifted from vocabulary")
        if len(rows) != expected_n:
            raise ValueError(
                f"{plants_path.name} must contain {expected_n} rows, found {len(rows)}"
            )
    return rows


def _plant_row(line: str, index: int, name: str, source_path: str) -> dict[str, Any]:
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
    if row["source"] != source_path:
        raise ValueError(f"{ctx} source must be {source_path}")
    return {key: row[key] for key in LEFTOVER_PLANT_ROW_KEYS}
