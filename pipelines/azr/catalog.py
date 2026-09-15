#!/usr/bin/env python3
"""Load the committed AZR catalog extract and bind it to the source pins."""

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
    N_SOURCES,
    PRESERVE_COMMIT,
    SLICE_ID,
)

SLICE_MILL = "azr-mill-r1181"


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


def _bind_sources(catalog: AzrCatalog) -> None:
    expected = {source.mill_id: source for source in catalog_sources()}
    if set(catalog.mills) != set(expected):
        raise ValueError(
            "catalog mills drifted from sources: "
            f"extra={sorted(set(catalog.mills) - set(expected))} "
            f"missing={sorted(set(expected) - set(catalog.mills))}"
        )
    if len(MILL_SOURCES) != N_SOURCES:
        raise ValueError(f"expected {N_SOURCES} AZR sources, found {len(MILL_SOURCES)}")
    slice_mill = catalog.mills[SLICE_MILL]
    if len(slice_mill.pairs) != slice_mill.n_rows:
        raise ValueError("r1181 slice n_rows does not match extracted pairs")
    for mill_id, mill in catalog.mills.items():
        source = expected[mill_id]
        if mill.path != source.path or mill.blob_sha != source.blob_sha:
            raise ValueError(f"{mill_id} pin disagrees with sources.py")
        if mill_id != SLICE_MILL and mill.pairs:
            raise ValueError(f"{mill_id} is not the first slice and must omit pair rows")


CATALOG = load_catalog()
