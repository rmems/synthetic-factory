#!/usr/bin/env python3
"""Load the committed CST catalog extract and bind it to the source pins."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .catalog_extract import KIND_PAIRS, KIND_PLANTS, catalog_json_path
from .sources import MILL_SOURCES, catalog_sources
from .vocabulary import CATALOG_SCHEMA_ID, FACTORY, GENERATOR, PRESERVE_COMMIT


@dataclass(frozen=True)
class MillCatalog:
    mill_id: str
    path: str
    blob_sha: str
    sha256: str
    kind: str
    catalog_first: int | None
    n_rows: int
    first_slug: str
    last_slug: str
    generator: str
    factory: str
    pair_arity: int | None = None
    pair_fields: tuple[str, ...] | None = None
    max_rounds: int | None = None
    pairs: tuple[tuple[Any, ...], ...] = ()
    plants: tuple[Mapping[str, Any], ...] = ()


@dataclass(frozen=True)
class CstCatalog:
    schema: str
    source_ref: str
    preserve_commit: str
    factory: str
    generator: str
    mills: Mapping[str, MillCatalog]

    @property
    def n_pair_rows(self) -> int:
        return sum(mill.n_rows for mill in self.mills.values() if mill.kind == KIND_PAIRS)

    @property
    def n_plant_rows(self) -> int:
        return sum(mill.n_rows for mill in self.mills.values() if mill.kind == KIND_PLANTS)


def load_catalog(path: Path | None = None) -> CstCatalog:
    catalog_path = path if path is not None else catalog_json_path()
    document = json.loads(catalog_path.read_text(encoding="utf-8"))
    if document.get("schema") != CATALOG_SCHEMA_ID:
        raise ValueError(f"{catalog_path} schema is not {CATALOG_SCHEMA_ID}")
    if document.get("preserve_commit") != PRESERVE_COMMIT:
        raise ValueError(f"{catalog_path} preserve_commit drifted from vocabulary")
    if document.get("factory") != FACTORY or document.get("generator") != GENERATOR:
        raise ValueError(f"{catalog_path} factory/generator drifted from vocabulary")
    mills = {mill_id: _mill_from_row(row) for mill_id, row in document["mills"].items()}
    catalog = CstCatalog(
        schema=document["schema"],
        source_ref=document["source_ref"],
        preserve_commit=document["preserve_commit"],
        factory=document["factory"],
        generator=document["generator"],
        mills=mills,
    )
    _bind_sources(catalog)
    return catalog


def _mill_from_row(row: Mapping[str, Any]) -> MillCatalog:
    fields = row.get("pair_fields")
    return MillCatalog(
        mill_id=row["mill_id"],
        path=row["path"],
        blob_sha=row["blob_sha"],
        sha256=row["sha256"],
        kind=row["kind"],
        catalog_first=row.get("catalog_first"),
        n_rows=row["n_rows"],
        first_slug=row["first_slug"],
        last_slug=row["last_slug"],
        generator=row["generator"],
        factory=row["factory"],
        pair_arity=row.get("pair_arity"),
        pair_fields=tuple(fields) if fields else None,
        max_rounds=row.get("max_rounds"),
        pairs=tuple(tuple(pair) for pair in row.get("pairs") or ()),
        plants=tuple(row.get("plants") or ()),
    )


def _bind_sources(catalog: CstCatalog) -> None:
    expected = {source.mill_id: source for source in catalog_sources()}
    if set(catalog.mills) != set(expected):
        raise ValueError(
            "catalog mills drifted from sources: "
            f"extra={sorted(set(catalog.mills) - set(expected))} "
            f"missing={sorted(set(expected) - set(catalog.mills))}"
        )
    if len(MILL_SOURCES) != 21:
        raise ValueError(f"expected 21 CST sources, found {len(MILL_SOURCES)}")
    for mill_id, mill in catalog.mills.items():
        source = expected[mill_id]
        if mill.path != source.path or mill.blob_sha != source.blob_sha or mill.kind != source.kind:
            raise ValueError(f"{mill_id} pin disagrees with sources.py")
        if mill.n_rows != len(mill.pairs) + len(mill.plants):
            raise ValueError(f"{mill_id} n_rows does not match extracted rows")


CATALOG = load_catalog()
