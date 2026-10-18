#!/usr/bin/env python3
"""Load Archive C letter-suffix leftover plant identities from compact JSONL."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from ._jsonl_rows import parse_rows, plant_row, read_lf_jsonl, require_pinned
from .plants_extract import leftover_plants_letter_jsonl_path
from .vocabulary import LEFTOVER_LETTER_PINS


def load_leftover_plants_letter(
    letter: str,
    path: Path | None = None,
) -> tuple[Mapping[str, Any], ...]:
    if letter not in LEFTOVER_LETTER_PINS:
        raise ValueError(f"unknown leftover plants letter {letter!r}")
    pin = LEFTOVER_LETTER_PINS[letter]
    plants_path = path if path is not None else leftover_plants_letter_jsonl_path(letter)
    text = read_lf_jsonl(plants_path, f"cannot load EVH leftover plants {letter}")
    source_path = str(pin["path"])
    expected_n = int(pin["n_rows"])

    def _plant_row(line: str, index: int, name: str) -> dict[str, Any]:
        return plant_row(line, f"{name}:{index}", source_path)

    rows = parse_rows(text, plants_path.name, _plant_row, "must contain leftover plant rows")
    canonical = leftover_plants_letter_jsonl_path(letter)
    if plants_path.resolve() == canonical.resolve():
        require_pinned(text, rows, plants_path.name, (str(pin["plants_sha256"]), expected_n))
    return rows
