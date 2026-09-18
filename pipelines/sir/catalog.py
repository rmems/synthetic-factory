#!/usr/bin/env python3
"""Load the committed sir catalog extract and bind it to the source pins."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .catalog_extract import catalog_json_path, pairs_jsonl_path
from .sources import MILL_SOURCES, MillSource, catalog_sources
from .vocabulary import (
    CATALOG_SCHEMA_ID,
    FACTORY,
    GENERATOR,
    PAIR_FIELD_ORDER,
    PRESERVE_COMMIT,
    SHAPE_PAIR_6TUPLES,
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
    _require_header(document, catalog_path)
    pair_rows = _load_pair_rows(pairs_jsonl_path(catalog_path.parent))
    _require_pair_groups(pair_rows, document["mills"])
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


def _require_header(document, path: Path) -> None:
    expected = {
        "schema": CATALOG_SCHEMA_ID,
        "preserve_commit": PRESERVE_COMMIT,
        "factory": FACTORY,
        "generator": GENERATOR,
        "slice": SLICE_ID,
        "family": "sir",
    }
    for key, value in expected.items():
        if document.get(key) != value:
            raise ValueError(f"{path} {key} drifted from vocabulary")


def _load_pair_rows(path: Path) -> dict[str, tuple[Mapping[str, Any], ...]]:
    text = path.read_bytes().decode("utf-8")
    if "\r" in text or not text.endswith("\n"):
        raise ValueError(f"{path.name} must be LF-framed jsonl")
    grouped: dict[str, list[Mapping[str, Any]]] = {}
    for index, line in enumerate(text[:-1].split("\n"), start=1):
        row = _pair_record(line, f"{path.name}:{index}")
        grouped.setdefault(row["mill_id"], []).append(row)
    return {mill_id: tuple(rows) for mill_id, rows in grouped.items()}


def _pair_record(line: str, where: str) -> Mapping[str, Any]:
    if not line or line.startswith((" ", "\t")):
        raise ValueError(f"{where} is not a compact JSONL record")
    row = json.loads(line)
    if set(row) != set(PAIR_FIELD_ORDER):
        raise ValueError(f"{where} keys drifted from PAIR_FIELD_ORDER")
    return row


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


def _require_pair_groups(groups, mills) -> None:
    if set(groups) != set(mills):
        raise ValueError("pair JSONL mill IDs drift from catalog header")


def _bind_sources(catalog: SirCatalog, document: Mapping[str, Any]) -> None:
    expected = {source.mill_id: source for source in catalog_sources()}
    _require_source_inventory(catalog, expected)
    if document.get("n_pair_rows") != catalog.n_pair_rows:
        raise ValueError("catalog n_pair_rows disagrees with mill rows")
    for mill_id, mill in catalog.mills.items():
        _require_source_pin(mill, expected[mill_id])
        _require_mill_vocabulary(mill)
        _require_mill_rows(mill)


def _require_source_inventory(catalog: SirCatalog, expected: Mapping[str, MillSource]) -> None:
    if set(catalog.mills) != set(expected):
        raise ValueError(
            "catalog mills drifted from sources: "
            f"extra={sorted(set(catalog.mills) - set(expected))} "
            f"missing={sorted(set(expected) - set(catalog.mills))}"
        )
    if len(MILL_SOURCES) != 5:
        raise ValueError(f"expected 5 sir catalog mills, found {len(MILL_SOURCES)}")


def _require_source_pin(mill: MillCatalog, source: MillSource) -> None:
    fields = ("path", "blob_sha", "catalog_first", "n_rows", "n_hops", "loads_sibling", "kind")
    for field in fields:
        if getattr(mill, field) != getattr(source, field):
            raise ValueError(f"{mill.mill_id} {field} disagrees with sources.py")


def _require_mill_vocabulary(mill: MillCatalog) -> None:
    expected = {"factory": FACTORY, "generator": GENERATOR, "shape": SHAPE_PAIR_6TUPLES}
    for field, value in expected.items():
        if getattr(mill, field) != value:
            raise ValueError(f"{mill.mill_id} {field} drifted from vocabulary")


def _require_mill_rows(mill: MillCatalog) -> None:
    expected = {"n_rounds": mill.n_rows, "n_hops": len(mill.hops), "n_rows": len(mill.pairs)}
    for field, value in expected.items():
        if getattr(mill, field) != value:
            raise ValueError(f"{mill.mill_id} {field} disagrees with catalog contents")
    _require_boundary_slugs(mill)


def _require_boundary_slugs(mill: MillCatalog) -> None:
    if mill.pairs[0]["success_slug"] != mill.first_slug:
        raise ValueError(f"{mill.mill_id} first_slug disagrees with jsonl")
    if mill.pairs[-1]["success_slug"] != mill.last_slug:
        raise ValueError(f"{mill.mill_id} last_slug disagrees with jsonl")


CATALOG = load_catalog()
