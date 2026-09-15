#!/usr/bin/env python3
"""Load the committed leftover catalog extract and bind it to the source pins."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from .catalog_extract import catalog_json_path
from .sources import MILL_SOURCES, catalog_sources, slug_sources
from .vocabulary import (
    CATALOG_SCHEMA_ID,
    FACTORY,
    GENERATOR,
    KIND_STEMS,
    KIND_TABLES,
    PRESERVE_COMMIT,
    SHAPE_STEMS,
    SHAPE_TABLES,
    SLICE_ID,
    TABLE_NAMES,
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
    n_table_rows: int
    n_pair_slots: int
    first_slug: str
    last_slug: str
    generator: str
    factory: str
    banned_slugs: tuple[str, ...] | None = None
    banned_snippets: tuple[str, ...] | None = None
    banned_keys: tuple[str, ...] | None = None
    tables: Mapping[str, tuple[tuple[Any, ...], ...]] | None = None
    stems: tuple[tuple[Any, ...], ...] | None = None
    froms: tuple[Any, ...] | None = None
    canons: tuple[Any, ...] | None = None
    lims: tuple[tuple[Any, ...], ...] | None = None
    nums: Mapping[str, Mapping[str, Any]] | None = None


@dataclass(frozen=True)
class SlugListing:
    mill_id: str
    path: str
    blob_sha: str
    sha256: str
    kind: str
    n_rows: int
    first_slug: str
    last_slug: str


@dataclass(frozen=True)
class LefCatalog:
    schema: str
    source_ref: str
    preserve_commit: str
    factory: str
    generator: str
    slice: str
    n_catalog_rows: int
    n_table_rows: int
    n_pair_slots: int
    slugs: SlugListing
    mills: Mapping[str, MillCatalog]


def load_catalog(path=None) -> LefCatalog:
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
    slugs = _slugs_from_row(document["slugs"])
    catalog = LefCatalog(
        schema=document["schema"],
        source_ref=document["source_ref"],
        preserve_commit=document["preserve_commit"],
        factory=document["factory"],
        generator=document["generator"],
        slice=document["slice"],
        n_catalog_rows=document["n_catalog_rows"],
        n_table_rows=document["n_table_rows"],
        n_pair_slots=document["n_pair_slots"],
        slugs=slugs,
        mills=mills,
    )
    _bind_sources(catalog)
    return catalog


def _mill_from_row(row: Mapping[str, Any]) -> MillCatalog:
    tables = row.get("tables")
    stems = row.get("stems")
    lims = row.get("lims")
    return MillCatalog(
        mill_id=row["mill_id"],
        path=row["path"],
        blob_sha=row["blob_sha"],
        sha256=row["sha256"],
        kind=row["kind"],
        shape=row["shape"],
        catalog_first=row.get("catalog_first"),
        n_rows=row["n_rows"],
        n_table_rows=row["n_table_rows"],
        n_pair_slots=row["n_pair_slots"],
        first_slug=row["first_slug"],
        last_slug=row["last_slug"],
        generator=row["generator"],
        factory=row["factory"],
        banned_slugs=tuple(row["banned_slugs"]) if row.get("banned_slugs") else None,
        banned_snippets=(
            tuple(row["banned_snippets"]) if row.get("banned_snippets") else None
        ),
        banned_keys=tuple(row["banned_keys"]) if row.get("banned_keys") else None,
        tables=_tables_from_row(tables) if tables else None,
        stems=tuple(tuple(row) for row in stems) if stems else None,
        froms=tuple(row["froms"]) if row.get("froms") else None,
        canons=tuple(row["canons"]) if row.get("canons") else None,
        lims=tuple(tuple(item) for item in lims) if lims else None,
        nums=row.get("nums"),
    )


def _tables_from_row(
    tables: Mapping[str, Any],
) -> dict[str, tuple[tuple[Any, ...], ...]]:
    return {
        name: tuple(tuple(row) for row in tables.get(name) or ())
        for name in TABLE_NAMES
    }


def _slugs_from_row(row: Mapping[str, Any]) -> SlugListing:
    return SlugListing(
        mill_id=row["mill_id"],
        path=row["path"],
        blob_sha=row["blob_sha"],
        sha256=row["sha256"],
        kind=row["kind"],
        n_rows=row["n_rows"],
        first_slug=row["first_slug"],
        last_slug=row["last_slug"],
    )


def _bind_sources(catalog: LefCatalog) -> None:
    expected = {source.mill_id: source for source in catalog_sources()}
    if set(catalog.mills) != set(expected):
        raise ValueError(
            "catalog mills drifted from sources: "
            f"extra={sorted(set(catalog.mills) - set(expected))} "
            f"missing={sorted(set(expected) - set(catalog.mills))}"
        )
    if len(MILL_SOURCES) != 7:
        raise ValueError(f"expected 7 leftover sources, found {len(MILL_SOURCES)}")
    slug_pins = slug_sources()
    if len(slug_pins) != 1:
        raise ValueError("expected one leftover used-slug listing pin")
    pin = slug_pins[0]
    if (
        catalog.slugs.path != pin.path
        or catalog.slugs.blob_sha != pin.blob_sha
        or catalog.slugs.mill_id != pin.mill_id
    ):
        raise ValueError("used-slug listing pin disagrees with sources.py")
    widths = 0
    for mill_id, mill in catalog.mills.items():
        source = expected[mill_id]
        if mill.path != source.path or mill.blob_sha != source.blob_sha:
            raise ValueError(f"{mill_id} pin disagrees with sources.py")
        if mill.kind != source.kind:
            raise ValueError(f"{mill_id} kind disagrees with sources.py")
        if mill.n_rows * 6 != mill.n_table_rows:
            raise ValueError(f"{mill_id} n_table_rows does not match n_rows")
        if mill.n_rows * 3 != mill.n_pair_slots:
            raise ValueError(f"{mill_id} n_pair_slots does not match n_rows")
        if mill.shape == SHAPE_TABLES:
            if mill.tables is None:
                raise ValueError(f"{mill_id} six-tables mill omitted tables")
            if mill.kind != KIND_TABLES:
                raise ValueError(f"{mill_id} tables shape must use kind=tables")
            for name in TABLE_NAMES:
                if len(mill.tables[name]) != mill.n_rows:
                    raise ValueError(f"{mill_id} {name} width drifted from n_rows")
        if mill.shape == SHAPE_STEMS:
            if mill.stems is None or len(mill.stems) != mill.n_rows:
                raise ValueError(f"{mill_id} stems width drifted from n_rows")
            if mill.tables is not None:
                raise ValueError(f"{mill_id} is the stems mill and must omit tables")
            if mill.kind != KIND_STEMS:
                raise ValueError(f"{mill_id} stems shape must use kind=stems")
        widths += mill.n_rows
    if catalog.n_catalog_rows != widths:
        raise ValueError("catalog n_catalog_rows drifted from mill widths")


CATALOG = load_catalog() if catalog_json_path().exists() else None
