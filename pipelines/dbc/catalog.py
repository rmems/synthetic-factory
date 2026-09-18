#!/usr/bin/env python3
"""Load the committed DBC catalog extract and bind it to the source pins."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from .catalog_extract import catalog_json_path, pairs_jsonl_path, sha256_bytes
from .sources import EXCLUDED_LAUNDERERS, MILL_SOURCES, catalog_sources
from .vocabulary import (
    CATALOG_SCHEMA_ID,
    DEFERRED_PAIR_ROWS,
    EXCLUDED_LAUNDERER_PATHS,
    FACTORY,
    GENERATOR,
    N_PAIR_ROWS,
    PAIR_JSONL_KEYS,
    PAIRS_SHA256,
    PRESERVE_COMMIT,
    SLICE_ID,
    SLICE_MILL_ID,
    SLICE_PAIR_ROWS,
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
    n_skip: int | None = None
    n_extra: int | None = None
    skip_slugs: tuple[str, ...] | None = None
    n_new: int | None = None
    n_inherited: int | None = None
    pairs: tuple[Mapping[str, Any], ...] = ()


@dataclass(frozen=True)
class DbcCatalog:
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
    def n_deferred_pair_rows(self) -> int:
        return sum(
            len(mill.pairs)
            for mill_id, mill in self.mills.items()
            if mill_id != SLICE_MILL_ID
        )


def load_pairs_jsonl(path=None) -> tuple[Mapping[str, Any], ...]:
    """Load the compact deferred-identity JSONL. r193 stays in CATALOG.json."""

    pairs_path = path if path is not None else pairs_jsonl_path()
    payload = pairs_path.read_bytes()
    if sha256_bytes(payload) != PAIRS_SHA256:
        raise ValueError(f"{pairs_path} sha256 drifted from vocabulary")
    text = payload.decode("utf-8")
    if "\r" in text or not text.endswith("\n"):
        raise ValueError(f"{pairs_path.name} must be LF-framed compact JSONL")
    rows = tuple(_jsonl_row(line, index) for index, line in enumerate(text.splitlines(), 1))
    _refuse_jsonl_identity(rows)
    return rows


def _jsonl_row(line: str, index: int) -> dict[str, Any]:
    if not line or line.startswith((" ", "\t")):
        raise ValueError(f"pairs.jsonl:{index} is not compact")
    row = json.loads(line)
    if not isinstance(row, dict) or set(row) != set(PAIR_JSONL_KEYS):
        raise ValueError(f"pairs.jsonl:{index} keys drifted")
    mill_id = row["mill_id"]
    source_path = row["source_path"]
    if mill_id == SLICE_MILL_ID:
        raise ValueError("pairs.jsonl must omit the r193 first-slice rows")
    if _is_launderer(mill_id, source_path):
        raise ValueError(f"pairs.jsonl:{index} names an excluded leftover3 launderer")
    if row["fail_handoff"] is not True:
        raise ValueError(f"pairs.jsonl:{index} fail_handoff must be true")
    if not isinstance(row["success_slug"], str) or not row["success_slug"]:
        raise ValueError(f"pairs.jsonl:{index} success_slug must be non-empty")
    if not isinstance(row["fail_slug"], str) or not row["fail_slug"]:
        raise ValueError(f"pairs.jsonl:{index} fail_slug must be non-empty")
    return row


def _is_launderer(mill_id: str, source_path: str) -> bool:
    launderer_ids = {source.mill_id for source in EXCLUDED_LAUNDERERS}
    return mill_id in launderer_ids or source_path in EXCLUDED_LAUNDERER_PATHS


def _refuse_jsonl_identity(rows: tuple[Mapping[str, Any], ...]) -> None:
    if len(rows) != DEFERRED_PAIR_ROWS:
        raise ValueError(f"expected {DEFERRED_PAIR_ROWS} deferred pairs, found {len(rows)}")


def _group_jsonl(
    rows: tuple[Mapping[str, Any], ...], mill_ids: set[str]
) -> dict[str, tuple[Mapping[str, Any], ...]]:
    grouped: dict[str, list[Mapping[str, Any]]] = {}
    for row in rows:
        mill_id = str(row["mill_id"])
        if mill_id not in mill_ids:
            raise ValueError(f"pairs.jsonl names unknown mill {mill_id}")
        grouped.setdefault(mill_id, []).append(row)
    extra = sorted(set(grouped) - mill_ids)
    if extra:
        raise ValueError(f"pairs.jsonl names unknown mills: {extra}")
    missing = sorted(mill_ids - {SLICE_MILL_ID} - set(grouped))
    if missing:
        raise ValueError(f"pairs.jsonl missing deferred mills: {missing}")
    if SLICE_MILL_ID in grouped:
        raise ValueError("pairs.jsonl must omit the r193 first-slice rows")
    return {mill_id: tuple(pairs) for mill_id, pairs in grouped.items()}


def load_catalog(path=None) -> DbcCatalog:
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
    mill_rows = document["mills"]
    grouped = _group_jsonl(load_pairs_jsonl(), set(mill_rows))
    mills = {
        mill_id: _mill_from_row(row, grouped.get(mill_id, ()))
        for mill_id, row in mill_rows.items()
    }
    catalog = DbcCatalog(
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


def _mill_from_row(
    row: Mapping[str, Any], jsonl_pairs: tuple[Mapping[str, Any], ...] = ()
) -> MillCatalog:
    catalog_pairs = tuple(row.get("pairs") or ())
    mill_id = row["mill_id"]
    if mill_id == SLICE_MILL_ID:
        pairs = catalog_pairs
    else:
        if catalog_pairs:
            raise ValueError(f"{mill_id} is not the first slice and must omit CATALOG pair rows")
        pairs = jsonl_pairs
    skip = row.get("skip_slugs")
    return MillCatalog(
        mill_id=mill_id,
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
        n_skip=row.get("n_skip"),
        n_extra=row.get("n_extra"),
        skip_slugs=tuple(skip) if skip else None,
        n_new=row.get("n_new"),
        n_inherited=row.get("n_inherited"),
        pairs=pairs,
    )


def _bind_sources(catalog: DbcCatalog) -> None:
    expected = {source.mill_id: source for source in catalog_sources()}
    if set(catalog.mills) != set(expected):
        raise ValueError(
            "catalog mills drifted from sources: "
            f"extra={sorted(set(catalog.mills) - set(expected))} "
            f"missing={sorted(set(expected) - set(catalog.mills))}"
        )
    if len(MILL_SOURCES) != 67:
        raise ValueError(f"expected 67 included DBC sources, found {len(MILL_SOURCES)}")
    if len(EXCLUDED_LAUNDERERS) != 2:
        raise ValueError(f"expected 2 excluded launderers, found {len(EXCLUDED_LAUNDERERS)}")
    excluded_paths = {source.path for source in EXCLUDED_LAUNDERERS}
    if excluded_paths != set(EXCLUDED_LAUNDERER_PATHS):
        raise ValueError("excluded launderer paths drifted from vocabulary")
    launderer_ids = {source.mill_id for source in EXCLUDED_LAUNDERERS}
    if any(mill_id in catalog.mills for mill_id in launderer_ids):
        raise ValueError("launderer mill leaked into the committed catalog")
    if catalog.n_pair_rows != N_PAIR_ROWS:
        raise ValueError(f"catalog n_pair_rows drifted from {N_PAIR_ROWS}")
    if catalog.n_deferred_pair_rows != DEFERRED_PAIR_ROWS:
        raise ValueError(f"deferred pair rows drifted from {DEFERRED_PAIR_ROWS}")
    slice_mill = catalog.mills[SLICE_MILL_ID]
    if len(slice_mill.pairs) != SLICE_PAIR_ROWS:
        raise ValueError("r193 slice n_rows does not match extracted pairs")
    for mill_id, mill in catalog.mills.items():
        source = expected[mill_id]
        if mill.path != source.path or mill.blob_sha != source.blob_sha:
            raise ValueError(f"{mill_id} pin disagrees with sources.py")
        _bind_mill_pairs(mill, source.path)


def _bind_mill_pairs(mill: MillCatalog, source_path: str) -> None:
    if mill.mill_id == SLICE_MILL_ID:
        if len(mill.pairs) != mill.n_rows:
            raise ValueError("r193 slice n_rows does not match extracted pairs")
        return
    if len(mill.pairs) != mill.n_rows:
        raise ValueError(f"{mill.mill_id} deferred pairs drifted from n_rows")
    if mill.pairs[0]["success_slug"] != mill.first_slug:
        raise ValueError(f"{mill.mill_id} first_slug drifted from pairs.jsonl")
    if mill.pairs[-1]["success_slug"] != mill.last_slug:
        raise ValueError(f"{mill.mill_id} last_slug drifted from pairs.jsonl")
    if any(pair["source_path"] != source_path for pair in mill.pairs):
        raise ValueError(f"{mill.mill_id} source_path drifted from pairs.jsonl")
    if any(pair["mill_id"] != mill.mill_id for pair in mill.pairs):
        raise ValueError(f"{mill.mill_id} mill_id drifted from pairs.jsonl")


CATALOG = load_catalog()
