#!/usr/bin/env python3
"""Read a committed NELB ``plants.jsonl`` through the public catalog API."""

from __future__ import annotations

from pathlib import Path

from nelb import catalog as cat
from nelb._contract import (
    FINDING_CATALOG_FILE_MISSING,
    FINDING_DUPLICATE_ID,
    FINDING_FIELD_INVALID,
    NelbRefusal,
    load_strict_json,
    shown,
)


def round_from_record_id(record_id: str) -> int | None:
    """Round encoded in a ``nelb-rNN-...`` record id, or None when the id has none."""

    if not record_id.startswith("nelb-r"):
        return None
    token = record_id[6:].split("-", 1)[0]
    digits = "".join(ch for ch in token if ch.isdigit())
    return int(digits) if digits else None


def read_committed_plants(path: Path) -> tuple[cat.Plant, ...]:
    """Read committed plants without calling ``nelb.catalog``'s private helpers."""

    text = _plants_text(path)
    plants: list[cat.Plant] = []
    seen: dict[str, int] = {}
    for index, line in enumerate(text.splitlines(), start=1):
        plants.append(_plant_from_line(path, index, line, seen))
    return tuple(plants)


def _plants_text(path: Path) -> str:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise NelbRefusal(FINDING_CATALOG_FILE_MISSING, f"{path} is unreadable: {exc}") from exc
    if not text.endswith("\n"):
        raise NelbRefusal(FINDING_FIELD_INVALID, f"{path.name} must be LF-framed jsonl")
    if "\r" in text:
        raise NelbRefusal(FINDING_FIELD_INVALID, f"{path.name} must be LF-framed jsonl")
    return text


def _plant_from_line(path: Path, index: int, line: str, seen: dict[str, int]) -> cat.Plant:
    if not line:
        raise NelbRefusal(FINDING_FIELD_INVALID, f"{path.name}:{index} is empty")
    row = _json_object(path, index, line)
    plant = cat.plant_from_mapping(row, f"{path.name}:{index}")
    _refuse_duplicate(plant, seen)
    seen[plant.record_id] = plant.source_round
    return plant


def _json_object(path: Path, index: int, line: str) -> dict:
    try:
        row = load_strict_json(line)
    except ValueError as exc:
        raise NelbRefusal(
            FINDING_FIELD_INVALID, f"{path.name}:{index} is not strict JSON: {exc}"
        ) from exc
    if not isinstance(row, dict):
        raise NelbRefusal(FINDING_FIELD_INVALID, f"{path.name}:{index} is not an object")
    return row


def _refuse_duplicate(plant: cat.Plant, seen: dict[str, int]) -> None:
    previous = seen.get(plant.record_id)
    if previous is None:
        return
    raise NelbRefusal(
        FINDING_DUPLICATE_ID,
        f"record_id {shown(plant.record_id)} repeats (r{previous} and r{plant.source_round})",
    )
