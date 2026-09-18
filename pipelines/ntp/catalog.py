#!/usr/bin/env python3
"""Load the committed NTP catalog extract and bind it to the source pins."""

from __future__ import annotations

import json
from collections.abc import Mapping
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


def load_catalog(path=None) -> NtpCatalog:
    catalog_path = path if path is not None else catalog_json_path()
    package_dir = catalog_path.parent
    document = json.loads(catalog_path.read_text(encoding="utf-8"))
    if document.get("schema") != CATALOG_SCHEMA_ID:
        raise ValueError(f"{catalog_path} schema is not {CATALOG_SCHEMA_ID}")
    if document.get("preserve_commit") != PRESERVE_COMMIT:
        raise ValueError(f"{catalog_path} preserve_commit drifted from vocabulary")
    if document.get("factory") != FACTORY or document.get("generator") != GENERATOR:
        raise ValueError(f"{catalog_path} factory/generator drifted from vocabulary")
    if document.get("slice") != SLICE_ID:
        raise ValueError(f"{catalog_path} slice drifted from vocabulary")
    if document.get("mills_filename") != MILLS_FILENAME:
        raise ValueError(f"{catalog_path} mills_filename drifted from vocabulary")
    if document.get("leftover_filename") != LEFTOVER_FILENAME:
        raise ValueError(f"{catalog_path} leftover_filename drifted from vocabulary")
    if document.get("themes_filename") != THEMES_FILENAME:
        raise ValueError(f"{catalog_path} themes_filename drifted from vocabulary")
    if document.get("pairs_filename") != PAIRS_FILENAME:
        raise ValueError(f"{catalog_path} pairs_filename drifted from vocabulary")
    if "mills" in document:
        raise ValueError(f"{catalog_path} must keep mill rows in {MILLS_FILENAME}")
    mill_rows = _load_jsonl(mills_jsonl_path(package_dir))
    leftover_rows = _load_jsonl(leftover_jsonl_path(package_dir))
    theme_rows = _load_jsonl(themes_jsonl_path(package_dir))
    pair_rows = _load_jsonl(pairs_jsonl_path(package_dir))
    success, leftover = _slice_themes(leftover_rows)
    theme_success, theme_leftover = _theme_lists(theme_rows)
    pair_success, pair_leftover = _pair_lists(pair_rows)
    mills = {}
    for row in mill_rows:
        mill_id = row["mill_id"]
        if mill_id == SLICE_MILL_ID:
            row = {**row, "success": success, "leftover": leftover}
        elif mill_id in THEME_MILL_IDS:
            row = {
                **row,
                "success": theme_success[mill_id],
                "leftover": theme_leftover[mill_id],
            }
        elif mill_id in PAIR_MILL_IDS:
            row = {
                **row,
                "success": pair_success[mill_id],
                "leftover": pair_leftover[mill_id],
            }
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
    leftover_rows: list[Mapping[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    success: list[dict[str, Any]] = []
    leftover: list[dict[str, Any]] = []
    for index, row in enumerate(leftover_rows):
        kind = row.get("kind")
        identity = {key: value for key, value in row.items() if key != "kind"}
        if kind == "success":
            success.append(identity)
            continue
        if kind == "leftover":
            leftover.append(identity)
            continue
        raise ValueError(f"{LEFTOVER_FILENAME}:{index + 1} kind is not success or leftover")
    return success, leftover


def _theme_lists(
    theme_rows: list[Mapping[str, Any]],
) -> tuple[dict[str, list[dict[str, Any]]], dict[str, list[dict[str, Any]]]]:
    success: dict[str, list[dict[str, Any]]] = {mill_id: [] for mill_id in THEME_MILL_IDS}
    leftover: dict[str, list[dict[str, Any]]] = {mill_id: [] for mill_id in THEME_MILL_IDS}
    for index, row in enumerate(theme_rows):
        mill_id = row.get("mill_id")
        kind = row.get("kind")
        if mill_id not in THEME_MILL_IDS:
            raise ValueError(f"{THEMES_FILENAME}:{index + 1} mill_id is not a theme slice")
        identity = {
            key: value for key, value in row.items() if key not in ("kind", "mill_id")
        }
        if kind == "success":
            success[mill_id].append(identity)
            continue
        if kind == "leftover":
            leftover[mill_id].append(identity)
            continue
        raise ValueError(f"{THEMES_FILENAME}:{index + 1} kind is not success or leftover")
    if THEME_MILL_ID not in success or not success[THEME_MILL_ID]:
        raise ValueError(f"{THEMES_FILENAME} must include {THEME_MILL_ID} success rows")
    if not leftover[THEME_MILL_ID]:
        raise ValueError(f"{THEMES_FILENAME} must include {THEME_MILL_ID} leftover rows")
    return success, leftover


def _pair_lists(
    pair_rows: list[Mapping[str, Any]],
) -> tuple[dict[str, list[dict[str, Any]]], dict[str, list[dict[str, Any]]]]:
    success: dict[str, list[dict[str, Any]]] = {mill_id: [] for mill_id in PAIR_MILL_IDS}
    leftover: dict[str, list[dict[str, Any]]] = {mill_id: [] for mill_id in PAIR_MILL_IDS}
    for index, row in enumerate(pair_rows):
        mill_id = row.get("mill_id")
        kind = row.get("kind")
        if mill_id not in PAIR_MILL_IDS:
            raise ValueError(f"{PAIRS_FILENAME}:{index + 1} mill_id is not a pair slice")
        identity = {
            key: value for key, value in row.items() if key not in ("kind", "mill_id")
        }
        if kind == "success":
            success[mill_id].append(identity)
            continue
        if kind == "leftover":
            leftover[mill_id].append(identity)
            continue
        raise ValueError(f"{PAIRS_FILENAME}:{index + 1} kind is not success or leftover")
    for mill_id in PAIR_MILL_IDS:
        if not success[mill_id] or not leftover[mill_id]:
            raise ValueError(f"{PAIRS_FILENAME} must include rows for {mill_id}")
    return success, leftover


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
    if set(catalog.mills) != set(expected):
        raise ValueError(
            "catalog mills drifted from sources: "
            f"extra={sorted(set(catalog.mills) - set(expected))} "
            f"missing={sorted(set(expected) - set(catalog.mills))}"
        )
    if len(MILL_SOURCES) != 84:
        raise ValueError(f"expected 84 NTP sources, found {len(MILL_SOURCES)}")
    slice_mill = catalog.mills[SLICE_MILL_ID]
    if len(slice_mill.success) != slice_mill.n_success:
        raise ValueError("leftover slice n_success does not match extracted success themes")
    if len(slice_mill.leftover) != slice_mill.n_leftover:
        raise ValueError("leftover slice n_leftover does not match extracted leftover themes")
    theme_mill = catalog.mills[THEME_MILL_ID]
    if len(theme_mill.success) != theme_mill.n_success:
        raise ValueError("theme slice n_success does not match extracted success themes")
    if len(theme_mill.leftover) != theme_mill.n_leftover:
        raise ValueError("theme slice n_leftover does not match extracted leftover themes")
    committed_slices = {SLICE_MILL_ID, *THEME_MILL_IDS, *PAIR_MILL_IDS}
    for mill_id, mill in catalog.mills.items():
        source = expected[mill_id]
        if mill.path != source.path or mill.blob_sha != source.blob_sha:
            raise ValueError(f"{mill_id} pin disagrees with sources.py")
        if mill_id in PAIR_MILL_IDS:
            if len(mill.success) != mill.n_success or len(mill.leftover) != mill.n_leftover:
                raise ValueError(f"{mill_id} pair slice row counts drifted from mills.jsonl")
            continue
        if mill_id not in committed_slices and (mill.success or mill.leftover):
            raise ValueError(f"{mill_id} is not a committed slice and must omit theme rows")


CATALOG = load_catalog()
