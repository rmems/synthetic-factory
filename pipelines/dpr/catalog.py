#!/usr/bin/env python3
"""Load the committed DPR catalog extract and bind it to the source pins."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .catalog_extract import (
    KIND_PAIRS,
    KIND_PLANTS,
    catalog_json_path,
    pairs_jsonl_path,
    plants_jsonl_path,
)
from .sources import MILL_SOURCES, catalog_sources
from .vocabulary import (
    CATALOG_SCHEMA_ID,
    CATALOG_SLICE,
    FACTORY,
    GENERATOR,
    PRESERVE_COMMIT,
    REPRESENTATIVE_PAIR_POLICY,
)


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
    list_name: str | None = None
    max_rounds: int | None = None
    pairs: tuple[Mapping[str, Any], ...] = ()
    plants: tuple[Mapping[str, Any], ...] = ()


@dataclass(frozen=True)
class DprCatalog:
    schema: str
    slice: str
    source_ref: str
    preserve_commit: str
    factory: str
    generator: str
    mills: Mapping[str, MillCatalog]
    committed_pair_rows: int
    committed_plant_rows: int

    @property
    def n_pair_rows(self) -> int:
        return sum(mill.n_rows for mill in self.mills.values() if mill.kind == KIND_PAIRS)

    @property
    def n_plant_rows(self) -> int:
        return sum(mill.n_rows for mill in self.mills.values() if mill.kind == KIND_PLANTS)


def load_catalog(path: Path | None = None) -> DprCatalog:
    catalog_path = path if path is not None else catalog_json_path()
    package_dir = catalog_path.parent
    document = json.loads(catalog_path.read_text(encoding="utf-8"))
    if document.get("schema") != CATALOG_SCHEMA_ID:
        raise ValueError(f"{catalog_path} schema is not {CATALOG_SCHEMA_ID}")
    if document.get("slice") != CATALOG_SLICE:
        raise ValueError(f"{catalog_path} slice is not {CATALOG_SLICE}")
    if document.get("preserve_commit") != PRESERVE_COMMIT:
        raise ValueError(f"{catalog_path} preserve_commit drifted from vocabulary")
    if document.get("factory") != FACTORY or document.get("generator") != GENERATOR:
        raise ValueError(f"{catalog_path} factory/generator drifted from vocabulary")
    plants = _rows_by_mill(_load_jsonl(plants_jsonl_path(package_dir)))
    pairs = _rows_by_mill(_load_jsonl(pairs_jsonl_path(package_dir)))
    mills = {
        mill_id: _mill_from_row(row, plants.get(mill_id, ()), pairs.get(mill_id, ()))
        for mill_id, row in document["mills"].items()
    }
    catalog = DprCatalog(
        schema=document["schema"],
        slice=document["slice"],
        source_ref=document["source_ref"],
        preserve_commit=document["preserve_commit"],
        factory=document["factory"],
        generator=document["generator"],
        mills=mills,
        committed_pair_rows=document["committed_pair_rows"],
        committed_plant_rows=document["committed_plant_rows"],
    )
    _bind_sources(catalog)
    return catalog


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    text = path.read_text(encoding="utf-8")
    if "\r" in text or (text and not text.endswith("\n")):
        raise ValueError(f"{path.name} must be LF-framed jsonl")
    rows: list[dict[str, Any]] = []
    for index, line in enumerate(text.splitlines(), start=1):
        if not line or line[:1].isspace():
            raise ValueError(f"{path.name}:{index} is not compact jsonl")
        row = json.loads(line)
        if not isinstance(row, dict) or not row.get("mill_id"):
            raise ValueError(f"{path.name}:{index} is missing mill_id")
        rows.append(row)
    return rows


def _rows_by_mill(rows: list[Mapping[str, Any]]) -> dict[str, tuple[dict[str, Any], ...]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        mill_id = str(row["mill_id"])
        grouped.setdefault(mill_id, []).append(
            {key: value for key, value in row.items() if key != "mill_id"}
        )
    return {mill_id: tuple(items) for mill_id, items in grouped.items()}


def _mill_from_row(
    row: Mapping[str, Any],
    plants: tuple[Mapping[str, Any], ...],
    pairs: tuple[Mapping[str, Any], ...],
) -> MillCatalog:
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
        list_name=row.get("list_name"),
        max_rounds=row.get("max_rounds"),
        pairs=pairs,
        plants=plants,
    )


def _expected_committed_pairs(mill: MillCatalog) -> int:
    policy = REPRESENTATIVE_PAIR_POLICY.get(mill.mill_id)
    if policy == "all":
        return mill.n_rows
    if policy == "ends":
        return 2 if mill.n_rows > 1 else mill.n_rows
    return 0


def _bind_sources(catalog: DprCatalog) -> None:
    expected = {source.mill_id: source for source in catalog_sources()}
    if set(catalog.mills) != set(expected):
        raise ValueError(
            "catalog mills drifted from sources: "
            f"extra={sorted(set(catalog.mills) - set(expected))} "
            f"missing={sorted(set(expected) - set(catalog.mills))}"
        )
    if len(MILL_SOURCES) != 39:
        raise ValueError(f"expected 39 DPR sources, found {len(MILL_SOURCES)}")
    committed_pairs = 0
    committed_plants = 0
    for mill_id, mill in catalog.mills.items():
        source = expected[mill_id]
        if mill.path != source.path or mill.blob_sha != source.blob_sha:
            raise ValueError(f"{mill_id} pin disagrees with sources.py")
        if mill.kind != source.kind:
            raise ValueError(f"{mill_id} kind disagrees with sources.py")
        if mill.kind == KIND_PLANTS:
            if mill.n_rows != len(mill.plants):
                raise ValueError(f"{mill_id} leftover plants are not fully committed")
            if mill.plants[0]["slug"] != mill.first_slug:
                raise ValueError(f"{mill_id} first plant drifted from header")
            if mill.plants[-1]["slug"] != mill.last_slug:
                raise ValueError(f"{mill_id} last plant drifted from header")
            committed_plants += len(mill.plants)
            continue
        expected_pairs = _expected_committed_pairs(mill)
        if len(mill.pairs) != expected_pairs:
            raise ValueError(
                f"{mill_id} committed {len(mill.pairs)} pairs, expected {expected_pairs}"
            )
        if mill.pairs:
            if mill.pairs[0]["slug"] != mill.first_slug:
                raise ValueError(f"{mill_id} first committed pair drifted from header")
            if mill.pairs[-1]["slug"] != mill.last_slug:
                raise ValueError(f"{mill_id} last committed pair drifted from header")
        committed_pairs += len(mill.pairs)
    if catalog.committed_pair_rows != committed_pairs:
        raise ValueError("committed_pair_rows does not match pairs.jsonl")
    if catalog.committed_plant_rows != committed_plants:
        raise ValueError("committed_plant_rows does not match plants.jsonl")


CATALOG = load_catalog()
