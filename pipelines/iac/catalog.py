#!/usr/bin/env python3
"""Load the committed IAC catalog extract and bind it to the source pins."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from .catalog_extract import catalog_json_path
from .plants_extract import sha256_bytes
from .sources import MILL_SOURCES, catalog_sources
from .vocabulary import (
    ARCHIVE_B_COMMIT,
    ARCHIVE_B_REF,
    CATALOG_SCHEMA_ID,
    FACTORY,
    GENERATOR,
    PLANTS_BLOB_SHA,
    PLANTS_COMPACT_KEYS,
    PLANTS_FILENAME,
    PLANTS_SOURCE_PATH,
    PLANTS_SOURCE_SHA256,
    PRESERVE_COMMIT,
    SLICE_ID,
)


@dataclass(frozen=True)
class ArchiveBPlant:
    index: int
    success_slug: str
    fail_slug: str
    success_seed: str
    fail_seed: str
    scenario: str
    ticket: str
    test: str
    fail_handoff: bool


@dataclass(frozen=True)
class ArchiveBSource:
    ref: str
    commit: str
    path: str
    blob_sha: str
    sha256: str
    shape: str
    n_plants: int
    first_slug: str
    last_slug: str


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
    n_keep: int | None = None
    n_extra: int | None = None
    keep_slugs: tuple[str, ...] | None = None
    pairs: tuple[Mapping[str, Any], ...] = ()


@dataclass(frozen=True)
class IacCatalog:
    schema: str
    source_ref: str
    preserve_commit: str
    factory: str
    generator: str
    slice: str
    mills: Mapping[str, MillCatalog]
    archive_b: ArchiveBSource
    plants_sha256: str
    plants: tuple[ArchiveBPlant, ...]

    @property
    def n_pair_rows(self) -> int:
        return sum(mill.n_rows for mill in self.mills.values())


def load_catalog(path=None) -> IacCatalog:
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
    archive_b = _archive_b_from_row(document["archive_b"])
    plants_path = catalog_path.parent / PLANTS_FILENAME
    plants_payload = plants_path.read_bytes()
    plants_sha256 = sha256_bytes(plants_payload)
    if document.get("plants_sha256") != plants_sha256:
        raise ValueError(f"{plants_path} digest drifted from CATALOG.json")
    plants = _plants_from_jsonl(plants_path.read_text(encoding="utf-8"))
    catalog = IacCatalog(
        schema=document["schema"],
        source_ref=document["source_ref"],
        preserve_commit=document["preserve_commit"],
        factory=document["factory"],
        generator=document["generator"],
        slice=document["slice"],
        mills=mills,
        archive_b=archive_b,
        plants_sha256=plants_sha256,
        plants=plants,
    )
    _bind_sources(catalog)
    _bind_archive_b(catalog)
    return catalog


def _mill_from_row(row: Mapping[str, Any]) -> MillCatalog:
    keep = row.get("keep_slugs")
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
        n_keep=row.get("n_keep"),
        n_extra=row.get("n_extra"),
        keep_slugs=tuple(keep) if keep else None,
        pairs=tuple(row.get("pairs") or ()),
    )


def _archive_b_from_row(row: Mapping[str, Any]) -> ArchiveBSource:
    return ArchiveBSource(
        ref=row["ref"],
        commit=row["commit"],
        path=row["path"],
        blob_sha=row["blob_sha"],
        sha256=row["sha256"],
        shape=row["shape"],
        n_plants=row["n_plants"],
        first_slug=row["first_slug"],
        last_slug=row["last_slug"],
    )


def _plants_from_jsonl(text: str) -> tuple[ArchiveBPlant, ...]:
    rows: list[ArchiveBPlant] = []
    for line_no, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            continue
        payload = json.loads(line)
        missing = [key for key in PLANTS_COMPACT_KEYS if key not in payload]
        if missing:
            raise ValueError(f"plants.jsonl line {line_no} missing {missing}")
        rows.append(
            ArchiveBPlant(
                index=payload["index"],
                success_slug=payload["success_slug"],
                fail_slug=payload["fail_slug"],
                success_seed=payload["success_seed"],
                fail_seed=payload["fail_seed"],
                scenario=payload["scenario"],
                ticket=payload["ticket"],
                test=payload["test"],
                fail_handoff=bool(payload["fail_handoff"]),
            )
        )
    return tuple(rows)


def _bind_archive_b(catalog: IacCatalog) -> None:
    archive = catalog.archive_b
    if archive.ref != ARCHIVE_B_REF or archive.commit != ARCHIVE_B_COMMIT:
        raise ValueError("archive_b ref/commit drifted from vocabulary")
    if archive.path != PLANTS_SOURCE_PATH:
        raise ValueError("archive_b path drifted from vocabulary")
    if archive.blob_sha != PLANTS_BLOB_SHA or archive.sha256 != PLANTS_SOURCE_SHA256:
        raise ValueError("archive_b source pin drifted from vocabulary")
    if archive.n_plants != len(catalog.plants):
        raise ValueError("archive_b n_plants does not match plants.jsonl")
    if catalog.plants and (
        catalog.plants[0].success_slug != archive.first_slug
        or catalog.plants[-1].success_slug != archive.last_slug
    ):
        raise ValueError("archive_b first/last slug drifted from plants.jsonl")


def _bind_sources(catalog: IacCatalog) -> None:
    expected = {source.mill_id: source for source in catalog_sources()}
    if set(catalog.mills) != set(expected):
        raise ValueError(
            "catalog mills drifted from sources: "
            f"extra={sorted(set(catalog.mills) - set(expected))} "
            f"missing={sorted(set(expected) - set(catalog.mills))}"
        )
    if len(MILL_SOURCES) != 15:
        raise ValueError(f"expected 15 IAC sources, found {len(MILL_SOURCES)}")
    slice_mill = catalog.mills["iac-mill-r609"]
    if len(slice_mill.pairs) != slice_mill.n_rows:
        raise ValueError("r609 slice n_rows does not match extracted pairs")
    for mill_id, mill in catalog.mills.items():
        source = expected[mill_id]
        if mill.path != source.path or mill.blob_sha != source.blob_sha:
            raise ValueError(f"{mill_id} pin disagrees with sources.py")
        if mill_id != "iac-mill-r609" and mill.pairs:
            raise ValueError(f"{mill_id} is not the first slice and must omit pair rows")


CATALOG = load_catalog()
