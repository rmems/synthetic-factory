#!/usr/bin/env python3
"""Load the deferred MDB pair identities (compact JSONL).

PR-b. r709's 37 identities stay in ``CATALOG.json``. The remaining 1284
rows live here, one compact object per line. Mill publishers are not
vendored and are never executed.
"""

from __future__ import annotations

import json
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .catalog import CATALOG
from .catalog_extract import is_slice_mill
from .sources import catalog_sources
from .vocabulary import DEFERRED_PAIR_ROWS, PAIRS_FILENAME, SLICE_MILL_ID

PAIR_KEYS = (
    "fail",
    "fail_plant",
    "fail_slug",
    "mill_id",
    "path",
    "success_plant",
    "success_slug",
)


@dataclass(frozen=True)
class DeferredPair:
    mill_id: str
    path: str
    success_slug: str
    fail_slug: str
    success_plant: str | None
    fail_plant: str | None
    fail: bool


def compact_pair_row(mill_id: str, path: str, pair: Mapping[str, Any]) -> dict[str, Any]:
    """Identity-only pair row: slugs, plants, fail flag, and mill pin."""

    return {
        "fail": bool(pair.get("fail", True)),
        "fail_plant": pair.get("fail_plant"),
        "fail_slug": pair["fail_slug"],
        "mill_id": mill_id,
        "path": path,
        "success_plant": pair.get("success_plant"),
        "success_slug": pair["success_slug"],
    }


def dumps_pair_line(row: Mapping[str, Any]) -> str:
    return json.dumps(row, ensure_ascii=True, separators=(",", ":"), sort_keys=True)


def dumps_pairs_jsonl(rows: list[Mapping[str, Any]]) -> str:
    return "".join(dumps_pair_line(row) + "\n" for row in rows)


def pairs_jsonl_path(package_dir: Path | None = None) -> Path:
    root = package_dir if package_dir is not None else Path(__file__).resolve().parent
    return root / PAIRS_FILENAME


def deferred_sources():
    return tuple(source for source in catalog_sources() if not is_slice_mill(source.mill_id))


def load_pairs(path: Path | None = None) -> tuple[DeferredPair, ...]:
    """Fail closed if the deferred JSONL drifts from the catalog pins."""

    pairs_path = path if path is not None else pairs_jsonl_path()
    text = pairs_path.read_text(encoding="utf-8")
    _refuse_framing(text, pairs_path)
    rows = [_parse_line(line, index) for index, line in enumerate(text.splitlines(), start=1)]
    if len(rows) != DEFERRED_PAIR_ROWS:
        raise ValueError(f"{pairs_path.name} has {len(rows)} rows, expected {DEFERRED_PAIR_ROWS}")
    _bind_catalog(rows, pairs_path)
    return tuple(_pair_from_row(row) for row in rows)


def _refuse_framing(text: str, path: Path) -> None:
    if "\r" in text:
        raise ValueError(f"{path.name} must be LF-only")
    if not text.endswith("\n"):
        raise ValueError(f"{path.name} must end with a newline")
    if not text:
        raise ValueError(f"{path.name} is empty")


def _parse_line(line: str, index: int) -> dict[str, Any]:
    raw = _decode_compact_line(line, index)
    _check_pair_fields(raw, index)
    return raw


def _decode_compact_line(line: str, index: int) -> dict[str, Any]:
    """One unindented line holding exactly ``PAIR_KEYS`` in compact sorted JSON."""

    if not line or line[0] in " \t":
        raise ValueError(f"{PAIRS_FILENAME}:{index} is empty or indented")
    try:
        raw = json.loads(line)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{PAIRS_FILENAME}:{index} is not JSON: {exc}") from exc
    if not isinstance(raw, dict) or set(raw) != set(PAIR_KEYS):
        raise ValueError(f"{PAIRS_FILENAME}:{index} keys drifted from {PAIR_KEYS}")
    if dumps_pair_line(raw) != line:
        raise ValueError(f"{PAIRS_FILENAME}:{index} is not compact sorted JSON")
    return raw


def _check_pair_fields(raw: Mapping[str, Any], index: int) -> None:
    if raw["mill_id"] == SLICE_MILL_ID:
        raise ValueError(f"{PAIRS_FILENAME}:{index} repeats the r709 slice")
    if not isinstance(raw["fail"], bool):
        raise ValueError(f"{PAIRS_FILENAME}:{index}.fail must be a bool")
    for key in ("mill_id", "path", "success_slug", "fail_slug"):
        if not _is_nonempty_str(raw[key]):
            raise ValueError(f"{PAIRS_FILENAME}:{index}.{key} must be a nonempty string")
    for key in ("success_plant", "fail_plant"):
        value = raw[key]
        if value is not None and not _is_nonempty_str(value):
            raise ValueError(f"{PAIRS_FILENAME}:{index}.{key} must be a string or null")


def _is_nonempty_str(value: Any) -> bool:
    return isinstance(value, str) and bool(value)


def _bind_catalog(rows: Sequence[Mapping[str, Any]], path: Path) -> None:
    expected = {source.mill_id: source for source in deferred_sources()}
    counts = Counter(row["mill_id"] for row in rows)
    if set(counts) != set(expected):
        raise ValueError(
            f"{path.name} mills drifted: "
            f"extra={sorted(set(counts) - set(expected))} "
            f"missing={sorted(set(expected) - set(counts))}"
        )
    _check_mill_rows(_group_by_mill(rows, expected))


def _group_by_mill(
    rows: Sequence[Mapping[str, Any]], expected: Mapping[str, Any]
) -> dict[str, list[Mapping[str, Any]]]:
    """Rows per deferred mill, refusing a path that disagrees with the pins or a repeat."""

    seen: set[tuple[str, str, str]] = set()
    grouped: dict[str, list[Mapping[str, Any]]] = {mill_id: [] for mill_id in expected}
    for row in rows:
        mill_id = row["mill_id"]
        mill = CATALOG.mills[mill_id]
        if row["path"] != mill.path or row["path"] != expected[mill_id].path:
            raise ValueError(f"{mill_id} path disagrees with catalog pins")
        key = (mill_id, row["success_slug"], row["fail_slug"])
        if key in seen:
            raise ValueError(f"duplicate deferred pair {key}")
        seen.add(key)
        grouped[mill_id].append(row)
    return grouped


def _check_mill_rows(grouped: Mapping[str, list[Mapping[str, Any]]]) -> None:
    """Each mill's JSONL rows match the catalog's row count and first/last slug."""

    for mill_id, mill_rows in grouped.items():
        mill = CATALOG.mills[mill_id]
        if len(mill_rows) != mill.n_rows:
            raise ValueError(f"{mill_id} has {len(mill_rows)} jsonl rows, catalog n_rows={mill.n_rows}")
        if mill_rows[0]["success_slug"] != mill.first_slug:
            raise ValueError(f"{mill_id} first_slug drifted from catalog")
        if mill_rows[-1]["success_slug"] != mill.last_slug:
            raise ValueError(f"{mill_id} last_slug drifted from catalog")


def _pair_from_row(row: Mapping[str, Any]) -> DeferredPair:
    return DeferredPair(
        mill_id=row["mill_id"],
        path=row["path"],
        success_slug=row["success_slug"],
        fail_slug=row["fail_slug"],
        success_plant=row["success_plant"],
        fail_plant=row["fail_plant"],
        fail=row["fail"],
    )


PAIRS = load_pairs()
