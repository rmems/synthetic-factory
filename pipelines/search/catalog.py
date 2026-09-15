#!/usr/bin/env python3
"""Load the committed search catalog extract and bind it to the source pins."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from .catalog_extract import (
    catalog_json_path,
    load_r72_header,
    load_r72_rows,
    r72_jsonl_path,
)
from .sources import MILL_SOURCES, R72_SOURCE, catalog_sources
from .vocabulary import (
    CATALOG_SCHEMA_ID,
    FACTORY,
    GENERATOR,
    KIND_HOME_PAIRS,
    PRESERVE_COMMIT,
    R72_BLOB_SHA,
    R72_CATALOG_FIRST,
    R72_FIRST_SLUG,
    R72_JSONL_SHA256,
    R72_LAST_SLUG,
    R72_MILL_ID,
    R72_N_ROWS,
    R72_PATH,
    R72_SHA256,
    R72_SLICE_ID,
    SLICE_ID,
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
    n_rounds: int
    n_rows: int
    n_hops: int
    first_slug: str
    last_slug: str
    generator: str
    factory: str
    hops: tuple[str, ...]
    doc_first_line: str
    pairs: tuple[Mapping[str, Any], ...] = ()


@dataclass(frozen=True)
class SearchCatalog:
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
    def hops(self) -> frozenset[str]:
        return frozenset(hop for mill in self.mills.values() for hop in mill.hops)


@dataclass(frozen=True)
class HomeMillCatalog:
    mill_id: str
    path: str
    blob_sha: str
    kind: str
    catalog_first: int
    n_rows: int
    first_slug: str
    last_slug: str
    slice: str
    pairs: tuple[Mapping[str, Any], ...]


def load_catalog(path=None) -> SearchCatalog:
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
    catalog = SearchCatalog(
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
    hops = row.get("hops") or ()
    return MillCatalog(
        mill_id=row["mill_id"],
        path=row["path"],
        blob_sha=row["blob_sha"],
        sha256=row["sha256"],
        kind=row["kind"],
        shape=row["shape"],
        catalog_first=row["catalog_first"],
        n_rounds=row["n_rounds"],
        n_rows=row["n_rows"],
        n_hops=row["n_hops"],
        first_slug=row["first_slug"],
        last_slug=row["last_slug"],
        generator=row["generator"],
        factory=row["factory"],
        hops=tuple(hops),
        doc_first_line=row.get("doc_first_line", ""),
        pairs=tuple(row.get("pairs") or ()),
    )


def _bind_sources(catalog: SearchCatalog) -> None:
    expected = {source.mill_id: source for source in catalog_sources()}
    if set(catalog.mills) != set(expected):
        raise ValueError(
            "catalog mills drifted from sources: "
            f"extra={sorted(set(catalog.mills) - set(expected))} "
            f"missing={sorted(set(expected) - set(catalog.mills))}"
        )
    if len(MILL_SOURCES) != 2:
        raise ValueError(f"expected 2 search leftover mills, found {len(MILL_SOURCES)}")
    for mill_id, mill in catalog.mills.items():
        source = expected[mill_id]
        if mill.path != source.path or mill.blob_sha != source.blob_sha:
            raise ValueError(f"{mill_id} pin disagrees with sources.py")
        if mill.catalog_first != source.catalog_first:
            raise ValueError(f"{mill_id} catalog_first disagrees with sources.py")
        if mill.n_hops != source.n_hops or mill.n_hops != len(mill.hops):
            raise ValueError(f"{mill_id} hop count disagrees with sources.py")
        if mill.n_rows != mill.n_rounds or len(mill.pairs) != mill.n_rows:
            raise ValueError(f"{mill_id} pair rows do not match n_rows")


def load_r72(path=None) -> HomeMillCatalog:
    header = load_r72_header()
    mill = header["mill"]
    if mill.get("mill_id") != R72_MILL_ID or mill.get("path") != R72_PATH:
        raise ValueError("r72 header mill pin drifted from vocabulary")
    if mill.get("blob_sha") != R72_BLOB_SHA or mill.get("sha256") != R72_SHA256:
        raise ValueError("r72 header source hashes drifted from vocabulary")
    if header.get("pairs_sha256") != R72_JSONL_SHA256:
        raise ValueError("r72 header pairs_sha256 drifted from vocabulary")
    jsonl_path = path if path is not None else r72_jsonl_path()
    rows = load_r72_rows(jsonl_path)
    if len(rows) != R72_N_ROWS:
        raise ValueError(f"{jsonl_path} expected {R72_N_ROWS} rows, found {len(rows)}")
    first = rows[0]["success_slug"]
    last = rows[-1]["success_slug"]
    if first != R72_FIRST_SLUG or last != R72_LAST_SLUG:
        raise ValueError(f"{jsonl_path} first/last slugs drifted: {first} / {last}")
    for offset, row in enumerate(rows):
        expected_round = R72_CATALOG_FIRST + offset
        if row.get("round") != expected_round:
            raise ValueError(f"{jsonl_path} row {offset} round drifted from {expected_round}")
    source = R72_SOURCE
    if source.mill_id != R72_MILL_ID or source.path != R72_PATH:
        raise ValueError("r72 source pin drifted from vocabulary")
    if source.catalog_first != R72_CATALOG_FIRST or source.n_hops != 0:
        raise ValueError("r72 source window drifted from vocabulary")
    if source.kind != KIND_HOME_PAIRS:
        raise ValueError("r72 source kind is not home-pairs")
    return HomeMillCatalog(
        mill_id=R72_MILL_ID,
        path=R72_PATH,
        blob_sha=source.blob_sha,
        kind=KIND_HOME_PAIRS,
        catalog_first=R72_CATALOG_FIRST,
        n_rows=len(rows),
        first_slug=first,
        last_slug=last,
        slice=R72_SLICE_ID,
        pairs=tuple(rows),
    )


CATALOG = load_catalog()
R72 = load_r72()
