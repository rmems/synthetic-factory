#!/usr/bin/env python3
"""Compact ``pairs.jsonl`` helpers for the LHC deferred catalog slice."""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from .catalog_extract import is_deferred_excluded_mill, is_slice_mill
from .vocabulary import CATALOG_FILENAME, PAIR_IDENTITY_KEYS, PAIR_ROW_KEYS, PAIRS_FILENAME


def pairs_jsonl_path(package_dir: Path | None = None) -> Path:
    root = package_dir if package_dir is not None else Path(__file__).resolve().parent
    return root / PAIRS_FILENAME


def catalog_json_path(package_dir: Path | None = None) -> Path:
    root = package_dir if package_dir is not None else Path(__file__).resolve().parent
    return root / CATALOG_FILENAME


def pair_identity(pair: Mapping[str, Any]) -> dict[str, Any]:
    return {key: pair[key] for key in PAIR_IDENTITY_KEYS}


def pair_jsonl_row(
    mill_id: str, path: str, index: int, pair: Mapping[str, Any]
) -> dict[str, Any]:
    row = pair_identity(pair)
    row["i"] = index
    row["mill_id"] = mill_id
    row["path"] = path
    return row


def deferred_pair_rows(records: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """JSONL rows for every mill except the w4x slice and the w4cl side package."""

    ordered = sorted(
        (
            record
            for record in records
            if not is_slice_mill(record["mill_id"])
            and not is_deferred_excluded_mill(record["mill_id"])
        ),
        key=lambda record: (record["catalog_first"], record["mill_id"]),
    )
    rows: list[dict[str, Any]] = []
    for record in ordered:
        for index, pair in enumerate(record["pairs"]):
            rows.append(pair_jsonl_row(record["mill_id"], record["path"], index, pair))
    return rows


def dumps_pairs_jsonl(rows: list[Mapping[str, Any]]) -> str:
    lines = [
        json.dumps(row, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
        for row in rows
    ]
    return "\n".join(lines) + "\n"


def load_pair_rows(path: Path | None = None) -> list[dict[str, Any]]:
    destination = path if path is not None else pairs_jsonl_path()
    try:
        text = destination.read_text(encoding="utf-8")
    except OSError as exc:
        raise ValueError(f"cannot load LHC pairs {destination}: {exc}") from exc
    if "\r" in text or not text.endswith("\n"):
        raise ValueError(f"{destination.name} must be LF-framed jsonl")
    rows: list[dict[str, Any]] = []
    for index, line in enumerate(text.splitlines(), start=1):
        if not line:
            raise ValueError(f"{destination.name}:{index} is empty")
        if line.startswith((" ", "\t")):
            raise ValueError(f"{destination.name}:{index} is not compact")
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"{destination.name}:{index} is not JSON: {exc}") from exc
        if not isinstance(row, dict) or set(row) != set(PAIR_ROW_KEYS):
            raise ValueError(f"{destination.name}:{index} keys differ")
        rows.append(row)
    if not rows:
        raise ValueError(f"{destination.name} must contain deferred pair identities")
    return rows
