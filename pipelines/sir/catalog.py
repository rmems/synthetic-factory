#!/usr/bin/env python3
"""Load the committed sir catalog extract and bind it to the source pins."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

if __name__.startswith("pipelines."):
    from ..oracle_grounded.import_twins import bind_import_twin
else:
    from oracle_grounded.import_twins import bind_import_twin

from .catalog_extract import catalog_json_path, pairs_jsonl_path, sha256_bytes
from .catalog_model import MillCatalog, factory_hops, scalar_identity
from .sources import MILL_SOURCES, PAIRS_SHA256, MillSource, catalog_sources
from .vocabulary import (
    CATALOG_SCHEMA_ID,
    FACTORY,
    GENERATOR,
    LEGACY_REF,
    PAIR_FIELD_ORDER,
    PRESERVE_COMMIT,
    SHAPE_PAIR_6TUPLES,
    SLICE_ID,
)


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
    pair_rows = _load_pair_rows(pairs_jsonl_path(catalog_path.parent), document["mills"])
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
        "source_ref": LEGACY_REF,
        "preserve_commit": PRESERVE_COMMIT,
        "factory": FACTORY,
        "generator": GENERATOR,
        "slice": SLICE_ID,
        "family": "sir",
    }
    _require_fields(document, expected, f"{path} drifted from vocabulary")


def _require_fields(actual: Mapping, expected: Mapping, where: str) -> None:
    for key, value in expected.items():
        if actual.get(key) != value:
            raise ValueError(f"{where}: {key} mismatch")


def _load_pair_rows(path: Path, mills) -> dict[str, tuple[Mapping[str, Any], ...]]:
    payload = path.read_bytes()
    text = payload.decode("utf-8")
    if "\r" in text or not text.endswith("\n"):
        raise ValueError(f"{path.name} must be LF-framed jsonl")
    grouped: dict[str, list[Mapping[str, Any]]] = {}
    for index, line in enumerate(text[:-1].split("\n"), start=1):
        row = _pair_record(line, f"{path.name}:{index}")
        grouped.setdefault(row["mill_id"], []).append(row)
    _require_pair_groups(grouped, mills)
    if sha256_bytes(payload) != PAIRS_SHA256:
        raise ValueError(f"{path.name} SHA-256 disagrees with the preserved catalog pin")
    return {mill_id: tuple(rows) for mill_id, rows in grouped.items()}


def _pair_record(line: str, where: str) -> Mapping[str, Any]:
    if not line or line.startswith((" ", "\t")):
        raise ValueError(f"{where} is not a compact JSONL record")
    row = json.loads(line)
    if not isinstance(row, dict) or set(row) != set(PAIR_FIELD_ORDER):
        raise ValueError(f"{where} keys drifted from PAIR_FIELD_ORDER")
    _require_pair_values(row, where)
    return row


def _require_pair_values(row: Mapping[str, Any], where: str) -> None:
    if row["fail_handoff"] is not True:
        raise ValueError(f"{where} fail_handoff must be true")
    for field in PAIR_FIELD_ORDER:
        if field == "fail_handoff":
            continue
        _require_pair_text(row[field], f"{where} {field}")


def _require_pair_text(value: Any, where: str) -> None:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{where} must be a non-empty string")


def _mill_from_row(row: Mapping[str, Any], pairs: tuple[Mapping[str, Any], ...]) -> MillCatalog:
    hops = factory_hops(row.get("hops"), f"{row['mill_id']} hops")
    return MillCatalog(
        **scalar_identity(row),
        hops=tuple(hops),
        loads_sibling=row.get("loads_sibling", ""),
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
    if len(MILL_SOURCES) != 2:
        raise ValueError(f"expected 2 sir leftover mills, found {len(MILL_SOURCES)}")


def _require_source_pin(mill: MillCatalog, source: MillSource) -> None:
    fields = (
        "mill_id",
        "path",
        "blob_sha",
        "sha256",
        "catalog_first",
        "n_rows",
        "n_hops",
        "loads_sibling",
        "kind",
    )
    expected = {field: getattr(source, field) for field in fields}
    _require_fields(vars(mill), expected, f"{mill.mill_id} disagrees with sources.py")


def _require_mill_vocabulary(mill: MillCatalog) -> None:
    expected = {"factory": FACTORY, "generator": GENERATOR, "shape": SHAPE_PAIR_6TUPLES}
    _require_fields(vars(mill), expected, f"{mill.mill_id} drifted from vocabulary")


def _require_mill_rows(mill: MillCatalog) -> None:
    expected = {"n_rounds": mill.n_rows, "n_hops": len(mill.hops), "n_rows": len(mill.pairs)}
    _require_fields(vars(mill), expected, f"{mill.mill_id} disagrees with catalog contents")
    _require_boundary_slugs(mill)


def _require_boundary_slugs(mill: MillCatalog) -> None:
    if mill.pairs[0]["success_slug"] != mill.first_slug:
        raise ValueError(f"{mill.mill_id} first_slug disagrees with jsonl")
    if mill.pairs[-1]["success_slug"] != mill.last_slug:
        raise ValueError(f"{mill.mill_id} last_slug disagrees with jsonl")


CATALOG = load_catalog()

bind_import_twin(__name__)
