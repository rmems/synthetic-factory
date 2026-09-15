#!/usr/bin/env python3
"""Load the committed EVH catalog extract and bind it to the source pins."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from .catalog_extract import catalog_json_path
from .sources import MILL_SOURCES, catalog_sources
from .vocabulary import CATALOG_SCHEMA_ID, FACTORY, GENERATOR, PRESERVE_COMMIT, SLICE_ID


@dataclass(frozen=True)
class EvhDestCatalog:
    dest: str
    shape: str
    n_rows: int
    first_slug: str
    last_slug: str
    start_round: int
    void_base: int
    offset: int
    tag: str | None = None
    to: int | None = None
    kw1: str | None = None
    kw2: str | None = None
    kw3: str | None = None
    pairs: tuple[Mapping[str, Any], ...] = ()


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
    n_catalogs: int
    first_slug: str
    last_slug: str
    generator: str
    factory: str
    catalogs: tuple[EvhDestCatalog, ...] = ()


@dataclass(frozen=True)
class EvhCatalog:
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


def load_catalog(path=None) -> EvhCatalog:
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
    catalog = EvhCatalog(
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


def _dest_from_row(row: Mapping[str, Any]) -> EvhDestCatalog:
    return EvhDestCatalog(
        dest=row["dest"],
        shape=row["shape"],
        n_rows=row["n_rows"],
        first_slug=row["first_slug"],
        last_slug=row["last_slug"],
        start_round=row["start_round"],
        void_base=row["void_base"],
        offset=row["offset"],
        tag=row.get("tag"),
        to=row.get("to"),
        kw1=row.get("kw1"),
        kw2=row.get("kw2"),
        kw3=row.get("kw3"),
        pairs=tuple(row.get("pairs") or ()),
    )


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
        n_catalogs=row["n_catalogs"],
        first_slug=row["first_slug"],
        last_slug=row["last_slug"],
        generator=row["generator"],
        factory=row["factory"],
        catalogs=tuple(_dest_from_row(item) for item in row.get("catalogs") or ()),
    )


def _bind_sources(catalog: EvhCatalog) -> None:
    expected = {source.mill_id: source for source in catalog_sources()}
    if set(catalog.mills) != set(expected):
        raise ValueError(
            "catalog mills drifted from sources: "
            f"extra={sorted(set(catalog.mills) - set(expected))} "
            f"missing={sorted(set(expected) - set(catalog.mills))}"
        )
    if len(MILL_SOURCES) != 9:
        raise ValueError(f"expected 9 EVH sources, found {len(MILL_SOURCES)}")
    slice_mill = catalog.mills["_gen_evh_plants_r801"]
    if len(slice_mill.catalogs) != 1:
        raise ValueError("r801 slice must be a single destination catalog")
    slice_dest = slice_mill.catalogs[0]
    if len(slice_dest.pairs) != slice_dest.n_rows:
        raise ValueError("r801 slice n_rows does not match extracted pairs")
    for mill_id, mill in catalog.mills.items():
        source = expected[mill_id]
        if mill.path != source.path or mill.blob_sha != source.blob_sha:
            raise ValueError(f"{mill_id} pin disagrees with sources.py")
        if mill_id != "_gen_evh_plants_r801" and any(dest.pairs for dest in mill.catalogs):
            raise ValueError(f"{mill_id} is not the first slice and must omit pair rows")


CATALOG = load_catalog()
