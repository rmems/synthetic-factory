#!/usr/bin/env python3
"""Load the committed NTP catalog extract and bind it to the source pins."""

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
    GENERATOR,
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
    for mill_id, mill in catalog.mills.items():
        source = expected[mill_id]
        if mill.path != source.path or mill.blob_sha != source.blob_sha:
            raise ValueError(f"{mill_id} pin disagrees with sources.py")
        if mill_id != SLICE_MILL_ID and (mill.success or mill.leftover):
            raise ValueError(f"{mill_id} is not the first slice and must omit theme rows")


CATALOG = load_catalog()
