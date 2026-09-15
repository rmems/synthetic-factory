#!/usr/bin/env python3
"""Load deferred DPR pair identities (compact JSONL).

PR-b. The 21 representative pair bodies stay at the top of ``pairs.jsonl``.
The remaining 706 compact identities follow. Mill publishers are not vendored
and are never executed.
"""

from __future__ import annotations

import json
from collections import Counter
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .catalog_extract import catalog_json_path, is_representative_pair_row, pairs_jsonl_path
from .sources import catalog_sources
from .vocabulary import (
    DEFERRED_PAIR_KEYS,
    DEFERRED_PAIR_ROWS,
    PAIRS_FILENAME,
    REPRESENTATIVE_PAIR_POLICY,
    SLICE_PAIR_ROWS,
)


@dataclass(frozen=True)
class DeferredPair:
    mill_id: str
    path: str
    slug: str
    fail_slug: str


def dumps_deferred_line(row: Mapping[str, Any]) -> str:
    return json.dumps(row, ensure_ascii=True, separators=(",", ":"), sort_keys=True)


def deferred_sources():
    return tuple(
        source
        for source in catalog_sources()
        if source.kind == "pairs"
        and REPRESENTATIVE_PAIR_POLICY.get(source.mill_id) != "all"
    )


def load_deferred_pairs(path: Path | None = None) -> tuple[DeferredPair, ...]:
    """Fail closed if deferred JSONL drifts from catalog pins."""

    pairs_path = path if path is not None else pairs_jsonl_path()
    text = pairs_path.read_text(encoding="utf-8")
    _refuse_framing(text, pairs_path)
    rows = _split_jsonl(text, pairs_path)
    if len(rows) != DEFERRED_PAIR_ROWS:
        raise ValueError(
            f"{pairs_path.name} has {len(rows)} deferred rows, expected {DEFERRED_PAIR_ROWS}"
        )
    _bind_catalog(rows, pairs_path)
    return tuple(_pair_from_row(row) for row in rows)


def _refuse_framing(text: str, path: Path) -> None:
    if "\r" in text:
        raise ValueError(f"{path.name} must be LF-only")
    if not text.endswith("\n"):
        raise ValueError(f"{path.name} must end with a newline")


def _split_jsonl(text: str, path: Path) -> list[dict[str, Any]]:
    representative = 0
    deferred: list[dict[str, Any]] = []
    for index, line in enumerate(text.splitlines(), start=1):
        if not line or line[0] in " \t":
            raise ValueError(f"{path.name}:{index} is empty or indented")
        try:
            raw = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"{path.name}:{index} is not JSON: {exc}") from exc
        if not isinstance(raw, dict):
            raise ValueError(f"{path.name}:{index} is not an object")
        if is_representative_pair_row(raw):
            representative += 1
            continue
        deferred.append(_parse_deferred(raw, line, index))
    if representative != SLICE_PAIR_ROWS:
        raise ValueError(
            f"{path.name} has {representative} representative rows, expected {SLICE_PAIR_ROWS}"
        )
    return deferred


def _parse_deferred(raw: Mapping[str, Any], line: str, index: int) -> dict[str, str]:
    if set(raw) != set(DEFERRED_PAIR_KEYS):
        raise ValueError(f"{PAIRS_FILENAME}:{index} keys drifted from {DEFERRED_PAIR_KEYS}")
    row = {key: raw[key] for key in DEFERRED_PAIR_KEYS}
    if dumps_deferred_line(row) != line:
        raise ValueError(f"{PAIRS_FILENAME}:{index} is not compact sorted JSON")
    for key in DEFERRED_PAIR_KEYS:
        value = row[key]
        if not isinstance(value, str) or not value:
            raise ValueError(f"{PAIRS_FILENAME}:{index}.{key} must be a nonempty string")
    return row


def _mill_headers() -> dict[str, Mapping[str, Any]]:
    document = json.loads(catalog_json_path().read_text(encoding="utf-8"))
    mills = document.get("mills")
    if not isinstance(mills, dict):
        raise ValueError("CATALOG.json mills is missing")
    return mills


def _bind_catalog(rows: list[Mapping[str, Any]], path: Path) -> None:
    headers = _mill_headers()
    expected = {source.mill_id: source for source in deferred_sources()}
    counts = Counter(row["mill_id"] for row in rows)
    if set(counts) != set(expected):
        raise ValueError(
            f"{path.name} mills drifted: "
            f"extra={sorted(set(counts) - set(expected))} "
            f"missing={sorted(set(expected) - set(counts))}"
        )
    grouped: dict[str, list[Mapping[str, Any]]] = {mill_id: [] for mill_id in expected}
    seen: set[tuple[str, str, str]] = set()
    for row in rows:
        mill_id = row["mill_id"]
        if row["path"] != expected[mill_id].path:
            raise ValueError(f"{mill_id} path disagrees with sources.py")
        key = (mill_id, row["slug"], row["fail_slug"])
        if key in seen:
            raise ValueError(f"duplicate deferred pair {key}")
        seen.add(key)
        grouped[mill_id].append(row)
    for mill_id, mill_rows in grouped.items():
        mill = headers[mill_id]
        policy = REPRESENTATIVE_PAIR_POLICY.get(mill_id)
        expected_rows = mill["n_rows"]
        if policy == "ends":
            expected_rows = mill["n_rows"] - 2
        if len(mill_rows) != expected_rows:
            raise ValueError(
                f"{mill_id} has {len(mill_rows)} deferred rows, expected {expected_rows}"
            )
        if policy != "ends":
            if mill_rows[0]["slug"] != mill["first_slug"]:
                raise ValueError(f"{mill_id} first deferred slug drifted from catalog")
            if mill_rows[-1]["slug"] != mill["last_slug"]:
                raise ValueError(f"{mill_id} last deferred slug drifted from catalog")


def _pair_from_row(row: Mapping[str, Any]) -> DeferredPair:
    return DeferredPair(
        mill_id=row["mill_id"],
        path=row["path"],
        slug=row["slug"],
        fail_slug=row["fail_slug"],
    )


DEFERRED_PAIRS = load_deferred_pairs()
