#!/usr/bin/env python3
"""Load the committed NTP catalog extract and bind it to the source pins."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from .catalog_extract import (
    catalog_json_path,
    leftover_jsonl_path,
    mills_jsonl_path,
    pairs_jsonl_path,
    themes_jsonl_path,
)
from .sources import MILL_SOURCES, catalog_sources
from .vocabulary import (
    CATALOG_SCHEMA_ID,
    FACTORY,
    GENERATOR,
    LEFTOVER_FILENAME,
    MILLS_FILENAME,
    PRESERVE_COMMIT,
    SLICE_ID,
    SLICE_MILL_ID,
    PAIRS_FILENAME,
    PAIR_MILL_IDS,
    THEME_MILL_ID,
    THEME_MILL_IDS,
    THEMES_FILENAME,
)


@dataclass(frozen=True)
class MillCatalog:
    mill_id: str
    path: str
    blob_sha: str
    sha256: str
    kind: str
    shape: str
    catalog_first: int | None
    n_rows: int
    n_success: int
    n_leftover: int
    first_slug: str
    last_slug: str
    first_leftover_slug: str
    last_leftover_slug: str
    generator: str
    factory: str
    success: tuple[Mapping[str, Any], ...] = ()
    leftover: tuple[Mapping[str, Any], ...] = ()


@dataclass(frozen=True)
class NtpCatalog:
    schema: str
    source_ref: str
    preserve_commit: str
    factory: str
    generator: str
    slice: str
    mills: Mapping[str, MillCatalog]

    @property
    def n_pair_rows(self) -> int:
        return sum(mill.n_rows for mill in self.mills.values())


# Header pins checked in this order; the first drift names the failure.
_HEADER_PINS: tuple[tuple[tuple[str, ...], tuple[str, ...], str], ...] = (
    (("schema",), (CATALOG_SCHEMA_ID,), f"schema is not {CATALOG_SCHEMA_ID}"),
    (("preserve_commit",), (PRESERVE_COMMIT,), "preserve_commit drifted from vocabulary"),
    (
        ("factory", "generator"),
        (FACTORY, GENERATOR),
        "factory/generator drifted from vocabulary",
    ),
    (("slice",), (SLICE_ID,), "slice drifted from vocabulary"),
    (("mills_filename",), (MILLS_FILENAME,), "mills_filename drifted from vocabulary"),
    (("leftover_filename",), (LEFTOVER_FILENAME,), "leftover_filename drifted from vocabulary"),
    (("themes_filename",), (THEMES_FILENAME,), "themes_filename drifted from vocabulary"),
    (("pairs_filename",), (PAIRS_FILENAME,), "pairs_filename drifted from vocabulary"),
)


def load_catalog(path=None) -> NtpCatalog:
    catalog_path = path if path is not None else catalog_json_path()
    package_dir = catalog_path.parent
    document = json.loads(catalog_path.read_text(encoding="utf-8"))
    _check_header(document, catalog_path)
    mill_rows = _load_jsonl(mills_jsonl_path(package_dir))
    leftover_rows = _load_jsonl(leftover_jsonl_path(package_dir))
    theme_rows = _load_jsonl(themes_jsonl_path(package_dir))
    pair_rows = _load_jsonl(pairs_jsonl_path(package_dir))
    slice_lists = _slice_themes(leftover_rows)
    theme_lists = _theme_lists(theme_rows)
    pair_lists = _pair_lists(pair_rows)
    mills = {}
    for row in mill_rows:
        mill_id = row["mill_id"]
        row = _attach_slice_rows(row, slice_lists, theme_lists, pair_lists)
        mills[mill_id] = _mill_from_row(row)
    catalog = NtpCatalog(
        schema=document["schema"],
        source_ref=document["source_ref"],
        preserve_commit=document["preserve_commit"],
        factory=document["factory"],
        generator=document["generator"],
        slice=document["slice"],
        mills=mills,
    )
    _bind_sources(catalog)
    return catalog


def _check_header(document: Mapping[str, Any], catalog_path) -> None:
    for keys, expected, message in _HEADER_PINS:
        if any(document.get(key) != value for key, value in zip(keys, expected, strict=True)):
            raise ValueError(f"{catalog_path} {message}")
    if "mills" in document:
        raise ValueError(f"{catalog_path} must keep mill rows in {MILLS_FILENAME}")


def _attach_slice_rows(
    row: dict[str, Any],
    slice_lists: tuple[list[dict[str, Any]], list[dict[str, Any]]],
    theme_lists: tuple[dict[str, list[dict[str, Any]]], dict[str, list[dict[str, Any]]]],
    pair_lists: tuple[dict[str, list[dict[str, Any]]], dict[str, list[dict[str, Any]]]],
) -> dict[str, Any]:
    """Return ``row`` with its committed success / leftover identities, if any."""

    mill_id = row["mill_id"]
    if mill_id == SLICE_MILL_ID:
        success, leftover = slice_lists
    elif mill_id in THEME_MILL_IDS:
        success, leftover = theme_lists[0][mill_id], theme_lists[1][mill_id]
    elif mill_id in PAIR_MILL_IDS:
        success, leftover = pair_lists[0][mill_id], pair_lists[1][mill_id]
    else:
        return row
    return {**row, "success": success, "leftover": leftover}


def _load_jsonl(path) -> list[dict[str, Any]]:
    text = path.read_text(encoding="utf-8")
    if "\r" in text or not text.endswith("\n"):
        raise ValueError(f"{path.name} must be LF-framed jsonl")
    rows: list[dict[str, Any]] = []
    for index, line in enumerate(text.splitlines(), start=1):
        if not line:
            raise ValueError(f"{path.name}:{index} is empty")
        row = json.loads(line)
        if not isinstance(row, dict):
            raise ValueError(f"{path.name}:{index} must be a JSON object")
        rows.append(row)
    if not rows:
        raise ValueError(f"{path.name} must contain at least one row")
    return rows


def _slice_themes(
    leftover_rows: Sequence[Mapping[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    success: list[dict[str, Any]] = []
    leftover: list[dict[str, Any]] = []
    for index, row in enumerate(leftover_rows):
        kind = row.get("kind")
        identity = {key: value for key, value in row.items() if key != "kind"}
        bucket = _kind_bucket(kind, success, leftover)
        if bucket is None:
            raise ValueError(f"{LEFTOVER_FILENAME}:{index + 1} kind is not success or leftover")
        bucket.append(identity)
    return success, leftover


def _theme_lists(
    theme_rows: Sequence[Mapping[str, Any]],
) -> tuple[dict[str, list[dict[str, Any]]], dict[str, list[dict[str, Any]]]]:
    success, leftover = _per_mill_lists(theme_rows, THEME_MILL_IDS, THEMES_FILENAME, "theme")
    if THEME_MILL_ID not in success or not success[THEME_MILL_ID]:
        raise ValueError(f"{THEMES_FILENAME} must include {THEME_MILL_ID} success rows")
    if not leftover[THEME_MILL_ID]:
        raise ValueError(f"{THEMES_FILENAME} must include {THEME_MILL_ID} leftover rows")
    return success, leftover


def _pair_lists(
    pair_rows: Sequence[Mapping[str, Any]],
) -> tuple[dict[str, list[dict[str, Any]]], dict[str, list[dict[str, Any]]]]:
    success, leftover = _per_mill_lists(pair_rows, PAIR_MILL_IDS, PAIRS_FILENAME, "pair")
    for mill_id in PAIR_MILL_IDS:
        if not success[mill_id] or not leftover[mill_id]:
            raise ValueError(f"{PAIRS_FILENAME} must include rows for {mill_id}")
    return success, leftover


def _per_mill_lists(
    rows: Sequence[Mapping[str, Any]],
    mill_ids: frozenset[str],
    filename: str,
    slice_label: str,
) -> tuple[dict[str, list[dict[str, Any]]], dict[str, list[dict[str, Any]]]]:
    """Group ``mill_id``-tagged identity rows into per-mill success / leftover lists."""

    success: dict[str, list[dict[str, Any]]] = {mill_id: [] for mill_id in mill_ids}
    leftover: dict[str, list[dict[str, Any]]] = {mill_id: [] for mill_id in mill_ids}
    for index, row in enumerate(rows):
        mill_id = row.get("mill_id")
        kind = row.get("kind")
        if mill_id not in mill_ids:
            raise ValueError(f"{filename}:{index + 1} mill_id is not a {slice_label} slice")
        identity = {
            key: value for key, value in row.items() if key not in ("kind", "mill_id")
        }
        bucket = _kind_bucket(kind, success, leftover)
        if bucket is None:
            raise ValueError(f"{filename}:{index + 1} kind is not success or leftover")
        bucket[mill_id].append(identity)
    return success, leftover


def _kind_bucket(kind: Any, success: Any, leftover: Any) -> Any:
    """``success`` / ``leftover`` for the matching row kind, else ``None``."""

    if kind == "success":
        return success
    if kind == "leftover":
        return leftover
    return None


def _mill_from_row(row: Mapping[str, Any]) -> MillCatalog:
    return MillCatalog(
        mill_id=row["mill_id"],
        path=row["path"],
        blob_sha=row["blob_sha"],
        sha256=row["sha256"],
        kind=row["kind"],
        shape=row["shape"],
        catalog_first=row.get("catalog_first"),
        n_rows=row["n_rows"],
        n_success=row["n_success"],
        n_leftover=row["n_leftover"],
        first_slug=row["first_slug"],
        last_slug=row["last_slug"],
        first_leftover_slug=row["first_leftover_slug"],
        last_leftover_slug=row["last_leftover_slug"],
        generator=row["generator"],
        factory=row["factory"],
        success=tuple(row.get("success") or ()),
        leftover=tuple(row.get("leftover") or ()),
    )


def _bind_sources(catalog: NtpCatalog) -> None:
    expected = {source.mill_id: source for source in catalog_sources()}
    _check_mill_set(catalog, expected)
    _check_slice_counts(catalog.mills[SLICE_MILL_ID], "leftover slice")
    _check_slice_counts(catalog.mills[THEME_MILL_ID], "theme slice")
    committed_slices = {SLICE_MILL_ID, *THEME_MILL_IDS, *PAIR_MILL_IDS}
    for mill_id, mill in catalog.mills.items():
        _check_mill_pin(mill, expected[mill_id], committed_slices)


def _check_mill_set(catalog: NtpCatalog, expected: Mapping[str, Any]) -> None:
    if set(catalog.mills) != set(expected):
        raise ValueError(
            "catalog mills drifted from sources: "
            f"extra={sorted(set(catalog.mills) - set(expected))} "
            f"missing={sorted(set(expected) - set(catalog.mills))}"
        )
    if len(MILL_SOURCES) != 84:
        raise ValueError(f"expected 84 NTP sources, found {len(MILL_SOURCES)}")


def _check_slice_counts(mill: MillCatalog, label: str) -> None:
    if len(mill.success) != mill.n_success:
        raise ValueError(f"{label} n_success does not match extracted success themes")
    if len(mill.leftover) != mill.n_leftover:
        raise ValueError(f"{label} n_leftover does not match extracted leftover themes")


def _check_mill_pin(mill: MillCatalog, source: Any, committed_slices: set[str]) -> None:
    mill_id = mill.mill_id
    if mill.path != source.path or mill.blob_sha != source.blob_sha:
        raise ValueError(f"{mill_id} pin disagrees with sources.py")
    if mill_id in PAIR_MILL_IDS:
        if _row_counts_drifted(mill):
            raise ValueError(f"{mill_id} pair slice row counts drifted from mills.jsonl")
        return
    if mill_id in committed_slices:
        return
    if mill.success or mill.leftover:
        raise ValueError(f"{mill_id} is not a committed slice and must omit theme rows")


def _row_counts_drifted(mill: MillCatalog) -> bool:
    return len(mill.success) != mill.n_success or len(mill.leftover) != mill.n_leftover


CATALOG = load_catalog()
