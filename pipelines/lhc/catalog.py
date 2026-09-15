#!/usr/bin/env python3
"""Load the committed LHC catalog extract and bind it to the source pins."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .sources import MILL_SOURCES, MillSource, catalog_sources
from .vocabulary import (
    CATALOG_FILENAME,
    CATALOG_SCHEMA_ID,
    FACTORY,
    GENERATOR,
    PRESERVE_COMMIT,
    SLICE_ID,
    SLICE_MILL_ID,
    SOURCE_COUNT,
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
    n_plants: int
    first_slug: str
    last_slug: str
    generator: str
    factory: str
    used_from: int | None = None
    pairs: tuple[Mapping[str, Any], ...] = ()


@dataclass(frozen=True)
class LhcCatalog:
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
    def n_plant_rows(self) -> int:
        return sum(mill.n_plants for mill in self.mills.values())


_IDENTITY_KEYS = (
    ("schema", CATALOG_SCHEMA_ID),
    ("preserve_commit", PRESERVE_COMMIT),
    ("factory", FACTORY),
    ("generator", GENERATOR),
    ("slice", SLICE_ID),
)


def _require_identity(document: Mapping[str, Any], catalog_path: Path) -> None:
    for key, expected in _IDENTITY_KEYS:
        if document.get(key) != expected:
            raise ValueError(f"{catalog_path} {key} drifted from vocabulary")


def load_catalog(path=None) -> LhcCatalog:
    catalog_path = path if path is not None else catalog_json_path()
    document = json.loads(catalog_path.read_text(encoding="utf-8"))
    _require_identity(document, catalog_path)
    expected = {source.mill_id: source for source in catalog_sources()}
    mills = {
        mill_id: _mill_from_row(mill_id, row, expected[mill_id])
        for mill_id, row in document["mills"].items()
    }
    catalog = LhcCatalog(
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
    mill_id: str, row: Mapping[str, Any], source: MillSource
) -> MillCatalog:
    return MillCatalog(
        mill_id=mill_id,
        path=source.path,
        blob_sha=source.blob_sha,
        sha256="",
        kind=source.kind,
        shape=row["shape"],
        catalog_first=row.get("catalog_first"),
        n_rows=row["n_rows"],
        n_plants=row["n_plants"],
        first_slug=row["first_slug"],
        last_slug=row["last_slug"],
        generator=GENERATOR,
        factory=FACTORY,
        used_from=row.get("used_from"),
        pairs=tuple(row.get("pairs") or ()),
    )


def _require_mill_ids(catalog: LhcCatalog, expected: Mapping[str, MillSource]) -> None:
    extra = sorted(set(catalog.mills) - set(expected))
    missing = sorted(set(expected) - set(catalog.mills))
    if extra or missing:
        raise ValueError(f"catalog mills drifted from sources: extra={extra} missing={missing}")


def _require_slice_pairs(catalog: LhcCatalog) -> None:
    slice_mill = catalog.mills[SLICE_MILL_ID]
    if len(slice_mill.pairs) != slice_mill.n_rows:
        raise ValueError("w4x-r4358 slice n_rows does not match extracted pairs")


def _require_pins(catalog: LhcCatalog, expected: Mapping[str, MillSource]) -> None:
    for mill_id, mill in catalog.mills.items():
        source = expected[mill_id]
        if mill.path != source.path or mill.blob_sha != source.blob_sha:
            raise ValueError(f"{mill_id} pin disagrees with sources.py")
        if mill_id != SLICE_MILL_ID and mill.pairs:
            raise ValueError(f"{mill_id} is not the first slice and must omit pair rows")


def _bind_sources(catalog: LhcCatalog) -> None:
    expected = {source.mill_id: source for source in catalog_sources()}
    _require_mill_ids(catalog, expected)
    if len(MILL_SOURCES) != SOURCE_COUNT:
        raise ValueError(f"expected {SOURCE_COUNT} LHC sources, found {len(MILL_SOURCES)}")
    _require_slice_pairs(catalog)
    _require_pins(catalog, expected)


def catalog_json_path(package_dir: Path | None = None) -> Path:
    root = package_dir if package_dir is not None else Path(__file__).resolve().parent
    return root / CATALOG_FILENAME


def _dump_mill_row(mill_id: str, mill: Mapping[str, Any], suffix: str) -> str:
    key = json.dumps(mill_id, ensure_ascii=True)
    if mill.get("pairs"):
        dumped = json.dumps(mill, ensure_ascii=True, indent=2, sort_keys=True)
        dumped = dumped.replace("\n", "\n    ")
    else:
        dumped = json.dumps(mill, ensure_ascii=True, sort_keys=True, separators=(", ", ": "))
    return f"    {key}: {dumped}{suffix}"


def _dump_mills_object(mills: Mapping[str, Any], suffix: str) -> list[str]:
    lines = ['  "mills": {']
    mill_ids = sorted(mills)
    for index, mill_id in enumerate(mill_ids):
        mill_suffix = "," if index < len(mill_ids) - 1 else ""
        lines.append(_dump_mill_row(mill_id, mills[mill_id], mill_suffix))
    lines.append(f"  }}{suffix}")
    return lines


def _dump_document_entry(key: str, value: Any, suffix: str) -> list[str]:
    if key == "mills":
        return _dump_mills_object(value, suffix)
    dumped = json.dumps(value, ensure_ascii=True, indent=2, sort_keys=True)
    dumped = dumped.replace("\n", "\n  ")
    return [f"  {json.dumps(key, ensure_ascii=True)}: {dumped}{suffix}"]


def dumps_catalog(document: Mapping[str, Any]) -> str:
    """Pretty header; one-line count rows; pretty-print only the w4x pair slice."""

    lines = ["{"]
    keys = sorted(document)
    for index, key in enumerate(keys):
        suffix = "," if index < len(keys) - 1 else ""
        lines.extend(_dump_document_entry(key, document[key], suffix))
    lines.append("}")
    return "\n".join(lines) + "\n"


def write_catalog_document(document: Mapping[str, Any], path: Path | None = None) -> Path:
    destination = path if path is not None else catalog_json_path()
    destination.write_text(dumps_catalog(document), encoding="utf-8")
    return destination


CATALOG = load_catalog()
