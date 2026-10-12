#!/usr/bin/env python3
"""Load Archive C leftover plant pair identities from compact JSONL."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from ._jsonl_rows import parse_rows, plant_row, read_lf_jsonl, require_pinned
from .plants_extract import leftover_plants_b_jsonl_path
from .vocabulary import (
    ARCHIVE_C_PATH,
    LEFTOVER_PLANTS_B_N_ROWS,
    LEFTOVER_PLANTS_B_SHA256,
)


def load_leftover_plants_b(path: Path | None = None) -> tuple[Mapping[str, Any], ...]:
    plants_path = path if path is not None else leftover_plants_b_jsonl_path()
    text = read_lf_jsonl(plants_path, "cannot load EVH leftover plants b")
    rows = parse_rows(text, plants_path.name, _plant_row, "must contain leftover plant rows")
    if plants_path.resolve() == leftover_plants_b_jsonl_path().resolve():
        require_pinned(
            text,
            rows,
            "leftover-plants-b.jsonl",
            (LEFTOVER_PLANTS_B_SHA256, LEFTOVER_PLANTS_B_N_ROWS),
        )
    return rows


def _plant_row(line: str, index: int, name: str) -> dict[str, Any]:
    return plant_row(line, f"{name}:{index}", ARCHIVE_C_PATH)
