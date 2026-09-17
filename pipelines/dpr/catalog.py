#!/usr/bin/env python3
"""Load the committed DPR catalog extract and bind it to the source pins."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
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
from .sources import MILL_SOURCES, MillSource, catalog_sources
from .catalog_extract import is_representative_pair_row
from .vocabulary import (
    CATALOG_SCHEMA_ID,
    CATALOG_SLICE,
    DEFERRED_PAIR_KEYS,
    FACTORY,
    GENERATOR,
    PRESERVE_COMMIT,
    REPRESENTATIVE_PAIR_POLICY,
    SLICE_PAIR_ROWS,
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
    document = _load_header(catalog_path)
    package_dir = catalog_path.parent
    plants = _rows_by_mill(_load_jsonl(plants_jsonl_path(package_dir)))
    pairs = _merge_pair_rows(_load_pair_jsonl(pairs_jsonl_path(package_dir)))
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


def _load_header(catalog_path: Path) -> dict[str, Any]:
    document = json.loads(catalog_path.read_text(encoding="utf-8"))
    _refuse_header_identity(document, catalog_path)
    return document


def _refuse_header_identity(document: Mapping[str, Any], catalog_path: Path) -> None:
    expected = {
        "schema": CATALOG_SCHEMA_ID,
        "slice": CATALOG_SLICE,
        "preserve_commit": PRESERVE_COMMIT,
        "factory": FACTORY,
        "generator": GENERATOR,
    }
    for key, value in expected.items():
        if document.get(key) != value:
            raise ValueError(f"{catalog_path} {key} drifted from vocabulary")


def _load_pair_jsonl(path: Path) -> dict[str, tuple[Mapping[str, Any], ...]]:
    text = path.read_text(encoding="utf-8")
    _refuse_jsonl_framing(path, text)
    representative: list[dict[str, Any]] = []
    deferred: list[dict[str, Any]] = []
    for index, line in enumerate(text.splitlines(), start=1):
        row = _parse_jsonl_row(path, index, line)
        if is_representative_pair_row(row):
            representative.append(row)
        else:
            deferred.append(_parse_deferred_pair_row(path, index, row))
    if len(representative) != SLICE_PAIR_ROWS:
        raise ValueError(f"{path.name} representative rows {len(representative)} != {SLICE_PAIR_ROWS}")
    rep_by_mill = _rows_by_mill(representative)
    def_by_mill = _rows_by_mill(deferred)
    merged: dict[str, tuple[Mapping[str, Any], ...]] = {}
    for mill_id in set(rep_by_mill) | set(def_by_mill):
        rep = list(rep_by_mill.get(mill_id, ()))
        body = list(def_by_mill.get(mill_id, ()))
        policy = REPRESENTATIVE_PAIR_POLICY.get(mill_id)
        if policy == "all":
            merged[mill_id] = tuple(rep)
        elif policy == "ends":
            if len(rep) != 2:
                raise ValueError(f"{mill_id} representative ends slice must have 2 rows")
            merged[mill_id] = tuple([rep[0], *body, rep[1]])
        else:
            merged[mill_id] = tuple(body)
    return merged


def _parse_deferred_pair_row(path: Path, index: int, row: Mapping[str, Any]) -> dict[str, Any]:
    keys = set(row.keys())
    if keys != set(DEFERRED_PAIR_KEYS):
        raise ValueError(f"{path.name}:{index} deferred keys drifted")
    return dict(row)


def _merge_pair_rows(grouped: dict[str, tuple[Mapping[str, Any], ...]]) -> dict[str, tuple[Mapping[str, Any], ...]]:
    return grouped


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    text = path.read_text(encoding="utf-8")
    _refuse_jsonl_framing(path, text)
    return [
        _parse_jsonl_row(path, index, line)
        for index, line in enumerate(text.splitlines(), start=1)
    ]


def _refuse_jsonl_framing(path: Path, text: str) -> None:
    if "\r" in text:
        raise ValueError(f"{path.name} must be LF-framed jsonl")
    if text and not text.endswith("\n"):
        raise ValueError(f"{path.name} must be LF-framed jsonl")


def _parse_jsonl_row(path: Path, index: int, line: str) -> dict[str, Any]:
    if not line or line[:1].isspace():
        raise ValueError(f"{path.name}:{index} is not compact jsonl")
    row = json.loads(line)
    if not isinstance(row, dict) or not row.get("mill_id"):
        raise ValueError(f"{path.name}:{index} is missing mill_id")
    return row


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


def _refuse_end_slugs(mill: MillCatalog, rows: Sequence[Mapping[str, Any]]) -> None:
    if rows[0]["slug"] != mill.first_slug:
        raise ValueError(f"{mill.mill_id} first committed row drifted from header")
    if rows[-1]["slug"] != mill.last_slug:
        raise ValueError(f"{mill.mill_id} last committed row drifted from header")


def _bind_plants(mill: MillCatalog) -> None:
    if mill.n_rows != len(mill.plants):
        raise ValueError(f"{mill.mill_id} leftover plants are not fully committed")
    _refuse_end_slugs(mill, mill.plants)


def _bind_pairs(mill: MillCatalog) -> None:
    if len(mill.pairs) != mill.n_rows:
        raise ValueError(
            f"{mill.mill_id} committed {len(mill.pairs)} pairs, expected {mill.n_rows}"
        )
    if mill.pairs:
        _refuse_end_slugs(mill, mill.pairs)


def _bind_one_mill(mill: MillCatalog, source: MillSource) -> None:
    if mill.path != source.path or mill.blob_sha != source.blob_sha:
        raise ValueError(f"{mill.mill_id} pin disagrees with sources.py")
    if mill.kind != source.kind:
        raise ValueError(f"{mill.mill_id} kind disagrees with sources.py")
    if mill.kind == KIND_PLANTS:
        _bind_plants(mill)
        return
    _bind_pairs(mill)


def _refuse_source_set(catalog: DprCatalog, expected: Mapping[str, MillSource]) -> None:
    if set(catalog.mills) != set(expected):
        raise ValueError(
            "catalog mills drifted from sources: "
            f"extra={sorted(set(catalog.mills) - set(expected))} "
            f"missing={sorted(set(expected) - set(catalog.mills))}"
        )
    if len(MILL_SOURCES) != 39:
        raise ValueError(f"expected 39 DPR sources, found {len(MILL_SOURCES)}")


def _bind_sources(catalog: DprCatalog) -> None:
    expected = {source.mill_id: source for source in catalog_sources()}
    _refuse_source_set(catalog, expected)
    committed_pairs = 0
    committed_plants = 0
    for mill_id, mill in catalog.mills.items():
        _bind_one_mill(mill, expected[mill_id])
        committed_pairs += len(mill.pairs)
        committed_plants += len(mill.plants)
    if catalog.committed_pair_rows != committed_pairs:
        raise ValueError("committed_pair_rows does not match pairs.jsonl")
    if catalog.committed_plant_rows != committed_plants:
        raise ValueError("committed_plant_rows does not match plants.jsonl")


CATALOG = load_catalog()
