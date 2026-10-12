#!/usr/bin/env python3
"""Load Archive B leftover plant pair identities from compact JSONL."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from ._jsonl_rows import parse_rows, plant_row, read_lf_jsonl, require_pinned
from .plants_extract import leftover_plants_jsonl_path
from .vocabulary import (
    LEFTOVER_PLANTS_N_ROWS,
    LEFTOVER_PLANTS_SHA256,
)


def load_leftover_plants(path: Path | None = None) -> tuple[Mapping[str, Any], ...]:
    plants_path = path if path is not None else leftover_plants_jsonl_path()
    text = read_lf_jsonl(plants_path, "cannot load EVH leftover plants")
    rows = parse_rows(text, plants_path.name, _plant_row, "must contain leftover plant rows")
    if plants_path.resolve() == leftover_plants_jsonl_path().resolve():
        require_pinned(
            text,
            rows,
            "leftover-plants.jsonl",
            (LEFTOVER_PLANTS_SHA256, LEFTOVER_PLANTS_N_ROWS),
        )
    return rows


def _plant_row(line: str, index: int, name: str) -> dict[str, Any]:
    return plant_row(line, f"{name}:{index}", None)
