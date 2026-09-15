#!/usr/bin/env python3
"""Load the committed SSR catalog extract and bind it to the source pins."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from .catalog_extract import catalog_json_path
from .sources import MILL_SOURCES, assert_source_count, catalog_sources
from .vocabulary import (
    CATALOG_SCHEMA_ID,
    FACTORY,
    GENERATOR,
    PRESERVE_COMMIT,
    SLICE_ID,
    SLICE_MILL_ID,
    SOURCE_FILE_COUNT,
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
    first_slug: str | None
    last_slug: str | None
    generator: str
    factory: str
    n_tails: int | None = None
    first_tail: str | None = None
    last_tail: str | None = None
    last_success_tail: str | None = None
    exec_target: str | None = None
    pairs: tuple[Mapping[str, Any], ...] = ()


@dataclass(frozen=True)
class SsrCatalog:
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


def load_catalog(path=None) -> SsrCatalog:
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
    extract = document.get("extract")
    if not isinstance(extract, dict) or extract.get("exec") is not False:
        raise ValueError(f"{catalog_path} extract.exec must be false")
    if extract.get("method") != "ast.parse":
        raise ValueError(f"{catalog_path} extract.method must be ast.parse")
    if extract.get("source_files") != SOURCE_FILE_COUNT:
        raise ValueError(f"{catalog_path} extract.source_files drifted")
    mills = {mill_id: _mill_from_row(row) for mill_id, row in document["mills"].items()}
    catalog = SsrCatalog(
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
        first_slug=row.get("first_slug"),
        last_slug=row.get("last_slug"),
        generator=row["generator"],
        factory=row["factory"],
        n_tails=row.get("n_tails"),
        first_tail=row.get("first_tail"),
        last_tail=row.get("last_tail"),
        last_success_tail=row.get("last_success_tail"),
        exec_target=row.get("exec_target"),
        pairs=tuple(row.get("pairs") or ()),
    )


def _bind_sources(catalog: SsrCatalog) -> None:
    assert_source_count()
    expected = {source.mill_id: source for source in catalog_sources()}
    if set(catalog.mills) != set(expected):
        raise ValueError(
            "catalog mills drifted from sources: "
            f"extra={sorted(set(catalog.mills) - set(expected))} "
            f"missing={sorted(set(expected) - set(catalog.mills))}"
        )
    if len(MILL_SOURCES) != SOURCE_FILE_COUNT:
        raise ValueError(f"expected {SOURCE_FILE_COUNT} SSR sources")
    slice_mill = catalog.mills[SLICE_MILL_ID]
    if len(slice_mill.pairs) != slice_mill.n_rows:
        raise ValueError("r181 slice n_rows does not match extracted pairs")
    for mill_id, mill in catalog.mills.items():
        source = expected[mill_id]
        if mill.path != source.path or mill.blob_sha != source.blob_sha:
            raise ValueError(f"{mill_id} pin disagrees with sources.py")
        if mill_id != SLICE_MILL_ID and mill.pairs:
            raise ValueError(f"{mill_id} is not the first slice and must omit pair rows")


CATALOG = load_catalog()
