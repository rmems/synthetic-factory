#!/usr/bin/env python3
"""Load the committed sir catalog extract and bind it to the source pins."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .catalog_extract import catalog_json_path, pairs_jsonl_path
from .sources import MILL_SOURCES, catalog_sources
from .vocabulary import (
    CATALOG_SCHEMA_ID,
    FACTORY,
    GENERATOR,
    PAIR_FIELD_ORDER,
    PRESERVE_COMMIT,
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
    loads_sibling: str
    source_lines: int
    doc_first_line: str
    pairs: tuple[Mapping[str, Any], ...] = ()


@dataclass(frozen=True)
class SirCatalog:
    schema: str
    family: str
    source_ref: str
    preserve_commit: str
    factory: str
    generator: str
    slice: str
    extraction: str
    mills: Mapping[str, MillCatalog]

    @property
    def n_pair_rows(self) -> int:
        return sum(mill.n_rows for mill in self.mills.values())

    @property
    def hops(self) -> frozenset[str]:
        return frozenset(hop for mill in self.mills.values() for hop in mill.hops)


def load_catalog(path=None) -> SirCatalog:
    catalog_path = path if path is not None else catalog_json_path()
    catalog_path = Path(catalog_path)
    document = json.loads(catalog_path.read_text(encoding="utf-8"))
    if document.get("schema") != CATALOG_SCHEMA_ID:
        raise ValueError(f"{catalog_path} schema is not {CATALOG_SCHEMA_ID}")
    if document.get("preserve_commit") != PRESERVE_COMMIT:
        raise ValueError(f"{catalog_path} preserve_commit drifted from vocabulary")
    if document.get("factory") != FACTORY or document.get("generator") != GENERATOR:
        raise ValueError(f"{catalog_path} factory/generator drifted from vocabulary")
    if document.get("slice") != SLICE_ID:
        raise ValueError(f"{catalog_path} slice drifted from vocabulary")
    if document.get("family") != "sir":
        raise ValueError(f"{catalog_path} family drifted from sir")
    pair_rows = _load_pair_rows(pairs_jsonl_path(catalog_path.parent))
    mills = {
        mill_id: _mill_from_row(row, pair_rows.get(mill_id, ()))
        for mill_id, row in document["mills"].items()
    }
    catalog = SirCatalog(
        schema=document["schema"],
        family=document["family"],
        source_ref=document["source_ref"],
        preserve_commit=document["preserve_commit"],
        factory=document["factory"],
        generator=document["generator"],
        slice=document["slice"],
        extraction=document["extraction"],
        mills=mills,
    )
    _bind_sources(catalog, document)
    return catalog


def _load_pair_rows(path: Path) -> dict[str, tuple[Mapping[str, Any], ...]]:
    text = path.read_text(encoding="utf-8")
    if "\r" in text or not text.endswith("\n"):
        raise ValueError(f"{path.name} must be LF-framed jsonl")
    grouped: dict[str, list[Mapping[str, Any]]] = {}
    for index, line in enumerate(text.splitlines(), start=1):
        if not line or line.startswith((" ", "\t")):
            raise ValueError(f"{path.name}:{index} is not a compact JSONL record")
        row = json.loads(line)
        if set(row) != set(PAIR_FIELD_ORDER):
            raise ValueError(f"{path.name}:{index} keys drifted from PAIR_FIELD_ORDER")
        grouped.setdefault(row["mill_id"], []).append(row)
    return {mill_id: tuple(rows) for mill_id, rows in grouped.items()}


def _mill_from_row(row: Mapping[str, Any], pairs: tuple[Mapping[str, Any], ...]) -> MillCatalog:
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
        loads_sibling=row.get("loads_sibling", ""),
        source_lines=row["source_lines"],
        doc_first_line=row.get("doc_first_line", ""),
        pairs=pairs,
    )


def _bind_sources(catalog: SirCatalog, document: Mapping[str, Any]) -> None:
    expected = {source.mill_id: source for source in catalog_sources()}
    if set(catalog.mills) != set(expected):
        raise ValueError(
            "catalog mills drifted from sources: "
            f"extra={sorted(set(catalog.mills) - set(expected))} "
            f"missing={sorted(set(expected) - set(catalog.mills))}"
        )
    if len(MILL_SOURCES) != 5:
        raise ValueError(f"expected 5 sir catalog mills, found {len(MILL_SOURCES)}")
    if document.get("n_pair_rows") != catalog.n_pair_rows:
        raise ValueError("catalog n_pair_rows disagrees with mill rows")
    for mill_id, mill in catalog.mills.items():
        source = expected[mill_id]
        if mill.path != source.path or mill.blob_sha != source.blob_sha:
            raise ValueError(f"{mill_id} pin disagrees with sources.py")
        if mill.catalog_first != source.catalog_first:
            raise ValueError(f"{mill_id} catalog_first disagrees with sources.py")
        if mill.n_rows != source.n_rows or mill.n_rows != mill.n_rounds:
            raise ValueError(f"{mill_id} pair rows do not match n_rows")
        if mill.n_hops != source.n_hops or mill.n_hops != len(mill.hops):
            raise ValueError(f"{mill_id} hop count disagrees with sources.py")
        if mill.loads_sibling != source.loads_sibling:
            raise ValueError(f"{mill_id} loads_sibling disagrees with sources.py")
        if mill.kind != source.kind:
            raise ValueError(f"{mill_id} kind disagrees with sources.py")
        if len(mill.pairs) != mill.n_rows:
            raise ValueError(f"{mill_id} jsonl rows do not match n_rows")
        if mill.pairs[0]["success_slug"] != mill.first_slug:
            raise ValueError(f"{mill_id} first_slug disagrees with jsonl")
        if mill.pairs[-1]["success_slug"] != mill.last_slug:
            raise ValueError(f"{mill_id} last_slug disagrees with jsonl")


CATALOG = load_catalog()
