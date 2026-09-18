#!/usr/bin/env python3
"""Load the committed AZR catalog extract and bind it to the source pins."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass, replace
from typing import Any

from .catalog_extract import (
    catalog_json_path,
    is_slice_mill,
    load_pair_rows,
    pair_identity,
    pairs_jsonl_path,
)
from .sources import MILL_SOURCES, catalog_sources
from .vocabulary import (
    BULKY_MILL_ID,
    BULKY_N_ROWS,
    CATALOG_SCHEMA_ID,
    DEFERRED_PAIR_ROWS,
    FACTORY,
    GENERATOR,
    PAIRS_FILENAME,
    PRESERVE_COMMIT,
    SLICE_ID,
    SLICE_MILL_ID,
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
    first_slug: str
    last_slug: str
    generator: str
    factory: str
    first_fail_slug: str | None = None
    last_fail_slug: str | None = None
    companion_path: str | None = None
    extra_plant_paths: tuple[str, ...] | None = None
    n_own_rows: int | None = None
    pairs: tuple[Mapping[str, Any], ...] = ()


@dataclass(frozen=True)
class AzrCatalog:
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

    @property
    def n_deferred_pair_rows(self) -> int:
        return sum(
            mill.n_rows for mill_id, mill in self.mills.items() if not is_slice_mill(mill_id)
        )


def load_catalog(path=None) -> AzrCatalog:
    catalog_path = path if path is not None else catalog_json_path()
    document = json.loads(catalog_path.read_text(encoding="utf-8"))
    if document.get("schema") != CATALOG_SCHEMA_ID:
        raise ValueError(f"{catalog_path} schema is not {CATALOG_SCHEMA_ID}")
    if document.get("preserve_commit") != PRESERVE_COMMIT:
        raise ValueError(f"{catalog_path} preserve_commit drifted from vocabulary")
    if document.get("factory") != FACTORY or document.get("generator") != GENERATOR:
        raise ValueError(f"{catalog_path} factory/generator drifted from vocabulary")
    if document.get("slice") != SLICE_ID:
        raise ValueError(f"{catalog_path} slice drifted from vocabulary")
    mills = {mill_id: _mill_from_row(row) for mill_id, row in document["mills"].items()}
    _bind_header(mills)
    mills = _overlay_deferred_pairs(mills, load_pair_rows(pairs_jsonl_path(catalog_path.parent)))
    catalog = AzrCatalog(
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


def _mill_from_row(row: Mapping[str, Any]) -> MillCatalog:
    extras = row.get("extra_plant_paths")
    return MillCatalog(
        mill_id=row["mill_id"],
        path=row["path"],
        blob_sha=row["blob_sha"],
        sha256=row["sha256"],
        kind=row["kind"],
        shape=row["shape"],
        catalog_first=row.get("catalog_first"),
        n_rows=row["n_rows"],
        first_slug=row["first_slug"],
        last_slug=row["last_slug"],
        generator=row["generator"],
        factory=row["factory"],
        first_fail_slug=row.get("first_fail_slug"),
        last_fail_slug=row.get("last_fail_slug"),
        companion_path=row.get("companion_path"),
        extra_plant_paths=tuple(extras) if extras else None,
        n_own_rows=row.get("n_own_rows"),
        pairs=tuple(row.get("pairs") or ()),
    )


def _bind_header(mills: Mapping[str, MillCatalog]) -> None:
    expected = {source.mill_id: source for source in catalog_sources()}
    if set(mills) != set(expected):
        raise ValueError(
            "catalog mills drifted from sources: "
            f"extra={sorted(set(mills) - set(expected))} "
            f"missing={sorted(set(expected) - set(mills))}"
        )
    slice_mill = mills[SLICE_MILL_ID]
    if len(slice_mill.pairs) != slice_mill.n_rows:
        raise ValueError("r1181 slice n_rows does not match extracted pairs")
    for mill_id, mill in mills.items():
        source = expected[mill_id]
        if mill.path != source.path or mill.blob_sha != source.blob_sha:
            raise ValueError(f"{mill_id} pin disagrees with sources.py")
        if not is_slice_mill(mill_id) and mill.pairs:
            raise ValueError(f"{mill_id} is not the first slice and must omit pair rows")


def _overlay_deferred_pairs(
    mills: Mapping[str, MillCatalog], rows: list[dict[str, Any]]
) -> dict[str, MillCatalog]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault(row["mill_id"], []).append(row)
    if SLICE_MILL_ID in grouped:
        raise ValueError(f"{PAIRS_FILENAME} must omit the r1181 first-slice mill")
    out = dict(mills)
    for mill_id, mill_rows in grouped.items():
        if mill_id not in mills:
            raise ValueError(f"{PAIRS_FILENAME} names unknown mill {mill_id}")
        expected_index = list(range(len(mill_rows)))
        if [row["i"] for row in mill_rows] != expected_index:
            raise ValueError(f"{mill_id} pair index drifted")
        if any(row["path"] != mills[mill_id].path for row in mill_rows):
            raise ValueError(f"{mill_id} path drifted from catalog")
        out[mill_id] = replace(
            mills[mill_id],
            pairs=tuple(pair_identity(row) for row in mill_rows),
        )
    return out


def _bind_sources(catalog: AzrCatalog) -> None:
    if len(MILL_SOURCES) != 76:
        raise ValueError(f"expected 76 AZR sources, found {len(MILL_SOURCES)}")
    if catalog.n_deferred_pair_rows != DEFERRED_PAIR_ROWS:
        raise ValueError("deferred pair width drifted from vocabulary")
    bulky = catalog.mills[BULKY_MILL_ID]
    if bulky.n_rows != BULKY_N_ROWS or len(bulky.pairs) != BULKY_N_ROWS:
        raise ValueError("r1205 bulky width drifted from vocabulary")
    for mill_id, mill in catalog.mills.items():
        if len(mill.pairs) != mill.n_rows:
            raise ValueError(f"{mill_id} n_rows does not match committed pair identities")
        if mill.pairs[0]["success_slug"] != mill.first_slug:
            raise ValueError(f"{mill_id} first_slug drifted from pair identities")
        if mill.pairs[-1]["success_slug"] != mill.last_slug:
            raise ValueError(f"{mill_id} last_slug drifted from pair identities")


CATALOG = load_catalog()
