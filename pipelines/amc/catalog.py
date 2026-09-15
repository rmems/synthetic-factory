#!/usr/bin/env python3
"""Load the committed AMC catalog extract and bind it to the source pins."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .catalog_extract import catalog_json_path
from .sources import MILL_SOURCES, catalog_sources
from .vocabulary import (
    CATALOG_SCHEMA_ID,
    FACTORY,
    GENERATOR,
    KIND_LEFTOVER,
    KIND_PAIRS,
    PRESERVE_COMMIT,
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
    max_rounds: int | None = None
    n_prefix: int | None = None
    n_new: int | None = None
    prefix_mill: str | None = None
    pairs: tuple[Mapping[str, Any], ...] = ()


@dataclass(frozen=True)
class AmcCatalog:
    schema: str
    source_ref: str
    preserve_commit: str
    factory: str
    generator: str
    mills: Mapping[str, MillCatalog]

    @property
    def n_pair_rows(self) -> int:
        return sum(mill.n_rows for mill in self.mills.values())


def load_catalog(path: Path | None = None) -> AmcCatalog:
    catalog_path = path if path is not None else catalog_json_path()
    document = json.loads(catalog_path.read_text(encoding="utf-8"))
    if document.get("schema") != CATALOG_SCHEMA_ID:
        raise ValueError(f"{catalog_path} schema is not {CATALOG_SCHEMA_ID}")
    if document.get("preserve_commit") != PRESERVE_COMMIT:
        raise ValueError(f"{catalog_path} preserve_commit drifted from vocabulary")
    if document.get("factory") != FACTORY or document.get("generator") != GENERATOR:
        raise ValueError(f"{catalog_path} factory/generator drifted from vocabulary")
    mills = {mill_id: _mill_from_row(row) for mill_id, row in document["mills"].items()}
    catalog = AmcCatalog(
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
        max_rounds=row.get("max_rounds"),
        n_prefix=row.get("n_prefix"),
        n_new=row.get("n_new"),
        prefix_mill=row.get("prefix_mill"),
        pairs=tuple(row.get("pairs") or ()),
    )


def _bind_sources(catalog: AmcCatalog) -> None:
    expected = {source.mill_id: source for source in catalog_sources()}
    if set(catalog.mills) != set(expected):
        raise ValueError(
            "catalog mills drifted from sources: "
            f"extra={sorted(set(catalog.mills) - set(expected))} "
            f"missing={sorted(set(expected) - set(catalog.mills))}"
        )
    if len(MILL_SOURCES) != 23:
        raise ValueError(f"expected 23 AMC sources, found {len(MILL_SOURCES)}")
    for mill_id, mill in catalog.mills.items():
        source = expected[mill_id]
        if mill.path != source.path or mill.blob_sha != source.blob_sha:
            raise ValueError(f"{mill_id} pin disagrees with sources.py")
        if mill.kind != source.kind:
            raise ValueError(f"{mill_id} kind disagrees with sources.py")
        if mill.kind not in {KIND_PAIRS, KIND_LEFTOVER}:
            raise ValueError(f"{mill_id} catalog kind {mill.kind} is not bindable")
        if mill.n_rows != len(mill.pairs):
            raise ValueError(f"{mill_id} n_rows does not match extracted rows")


CATALOG = load_catalog()
