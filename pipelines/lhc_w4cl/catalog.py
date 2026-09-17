#!/usr/bin/env python3
"""Load the committed LHC w4cl catalog extract and bind it to the source pin."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from .catalog_extract import catalog_json_path
from .sources import MILL_SOURCES, catalog_sources
from .vocabulary import (
    CATALOG_SCHEMA_ID,
    FACTORY,
    FAMILY,
    GENERATOR,
    PRESERVE_COMMIT,
    SLICE_ID,
    SLICE_MILL_ID,
    SOURCE_COUNT,
)


@dataclass(frozen=True)
class MillCatalog:
    mill_id: str
    path: str
    blob_sha: str
    sha256: str
    kind: str
    shape: str
    catalog_first: int
    used_from: int
    n_rows: int
    n_plants: int
    first_slug: str
    last_slug: str
    generator: str
    factory: str
    doc_first_line: str
    plants: tuple[Mapping[str, Any], ...] = ()
    pairs: tuple[Mapping[str, Any], ...] = ()


@dataclass(frozen=True)
class LhcW4clCatalog:
    schema: str
    source_ref: str
    preserve_commit: str
    family: str
    factory: str
    generator: str
    slice: str
    mills: Mapping[str, MillCatalog]

    @property
    def n_pair_rows(self) -> int:
        return sum(mill.n_rows for mill in self.mills.values())

    @property
    def n_plant_rows(self) -> int:
        return sum(mill.n_plants for mill in self.mills.values())


def load_catalog(path=None) -> LhcW4clCatalog:
    catalog_path = path if path is not None else catalog_json_path()
    document = json.loads(catalog_path.read_text(encoding="utf-8"))
    _check_header(document, catalog_path)
    mills = {mill_id: _mill_from_row(row) for mill_id, row in document["mills"].items()}
    catalog = LhcW4clCatalog(
        schema=document["schema"],
        source_ref=document["source_ref"],
        preserve_commit=document["preserve_commit"],
        family=document["family"],
        factory=document["factory"],
        generator=document["generator"],
        slice=document["slice"],
        mills=mills,
    )
    _bind_sources(catalog)
    return catalog


def _check_header(document: Mapping[str, Any], catalog_path) -> None:
    checks = (
        (document.get("schema") != CATALOG_SCHEMA_ID, "schema"),
        (document.get("preserve_commit") != PRESERVE_COMMIT, "preserve_commit"),
        (document.get("family") != FAMILY, "family"),
        (document.get("factory") != FACTORY, "factory"),
        (document.get("generator") != GENERATOR, "generator"),
        (document.get("slice") != SLICE_ID, "slice"),
    )
    for drifted, field in checks:
        if drifted:
            raise ValueError(f"{catalog_path} {field} drifted from vocabulary")


def _mill_from_row(row: Mapping[str, Any]) -> MillCatalog:
    return MillCatalog(
        mill_id=row["mill_id"],
        path=row["path"],
        blob_sha=row["blob_sha"],
        sha256=row["sha256"],
        kind=row["kind"],
        shape=row["shape"],
        catalog_first=row["catalog_first"],
        used_from=row["used_from"],
        n_rows=row["n_rows"],
        n_plants=row["n_plants"],
        first_slug=row["first_slug"],
        last_slug=row["last_slug"],
        generator=row["generator"],
        factory=row["factory"],
        doc_first_line=row.get("doc_first_line", ""),
        plants=tuple(row.get("plants") or ()),
        pairs=tuple(row.get("pairs") or ()),
    )


def _bind_sources(catalog: LhcW4clCatalog) -> None:
    expected = {source.mill_id: source for source in catalog_sources()}
    if set(catalog.mills) != set(expected):
        raise ValueError(
            "catalog mills drifted from sources: "
            f"extra={sorted(set(catalog.mills) - set(expected))} "
            f"missing={sorted(set(expected) - set(catalog.mills))}"
        )
    if len(MILL_SOURCES) != SOURCE_COUNT:
        raise ValueError(f"expected {SOURCE_COUNT} w4cl mill, found {len(MILL_SOURCES)}")
    mill = catalog.mills[SLICE_MILL_ID]
    source = expected[SLICE_MILL_ID]
    if mill.path != source.path or mill.blob_sha != source.blob_sha:
        raise ValueError(f"{SLICE_MILL_ID} pin disagrees with sources.py")
    if mill.catalog_first != source.catalog_first:
        raise ValueError(f"{SLICE_MILL_ID} catalog_first disagrees with sources.py")
    if mill.n_rows != source.n_rows or len(mill.pairs) != mill.n_rows:
        raise ValueError(f"{SLICE_MILL_ID} pair rows do not match n_rows")
    if mill.n_plants != source.n_plants or len(mill.plants) != mill.n_plants:
        raise ValueError(f"{SLICE_MILL_ID} plant rows do not match n_plants")


CATALOG = load_catalog()
