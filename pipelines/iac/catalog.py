#!/usr/bin/env python3
"""Load the committed IAC catalog extract and bind it to the source pins."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
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
    PLANTS_B_BLOB_SHA,
    PLANTS_B_FILENAME,
    PLANTS_B_SOURCE_PATH,
    PLANTS_B_SOURCE_SHA256,
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
    archive_b_more: ArchiveBSource
    plants_sha256: str
    plants_b_sha256: str
    plants: tuple[ArchiveBPlant, ...]
    plants_b: tuple[ArchiveBPlant, ...]

    @property
    def n_pair_rows(self) -> int:
        return sum(mill.n_rows for mill in self.mills.values())


@dataclass(frozen=True)
class ArchivePin:
    path: str
    blob_sha: str
    source_sha256: str


_ARCHIVE_BINDS = (
    (
        "archive_b",
        "plants",
        ArchivePin(PLANTS_SOURCE_PATH, PLANTS_BLOB_SHA, PLANTS_SOURCE_SHA256),
    ),
    (
        "archive_b_more",
        "plants_b",
        ArchivePin(PLANTS_B_SOURCE_PATH, PLANTS_B_BLOB_SHA, PLANTS_B_SOURCE_SHA256),
    ),
)

_PINNED_DOCUMENT_KEYS = (
    ("schema", CATALOG_SCHEMA_ID),
    ("preserve_commit", PRESERVE_COMMIT),
    ("slice", SLICE_ID),
)


def load_catalog(path=None) -> IacCatalog:
    catalog_path = path if path is not None else catalog_json_path()
    document = json.loads(catalog_path.read_text(encoding="utf-8"))
    for key, expected in _PINNED_DOCUMENT_KEYS:
        if document.get(key) != expected:
            raise ValueError(f"{catalog_path} {key} drifted from vocabulary")
    if document.get("factory") != FACTORY or document.get("generator") != GENERATOR:
        raise ValueError(f"{catalog_path} factory/generator drifted from vocabulary")
    plants_sha256, plants = _load_plants_sidecar(
        catalog_path, document, PLANTS_FILENAME, "plants_sha256"
    )
    plants_b_sha256, plants_b = _load_plants_sidecar(
        catalog_path, document, PLANTS_B_FILENAME, "plants_b_sha256"
    )
    catalog = IacCatalog(
        schema=document["schema"],
        source_ref=document["source_ref"],
        preserve_commit=document["preserve_commit"],
        factory=document["factory"],
        generator=document["generator"],
        slice=document["slice"],
        mills={mill_id: _mill_from_row(row) for mill_id, row in document["mills"].items()},
        archive_b=_archive_b_from_row(document["archive_b"]),
        archive_b_more=_archive_b_from_row(document["archive_b_more"]),
        plants_sha256=plants_sha256,
        plants_b_sha256=plants_b_sha256,
        plants=plants,
        plants_b=plants_b,
    )
    _bind_sources(catalog)
    for attr, plants_attr, pin in _ARCHIVE_BINDS:
        _bind_archive_b(
            getattr(catalog, attr),
            plants=getattr(catalog, plants_attr),
            pin=pin,
        )
    return catalog


def _load_plants_sidecar(
    catalog_path: Path,
    document: Mapping[str, Any],
    filename: str,
    digest_key: str,
) -> tuple[str, tuple[ArchiveBPlant, ...]]:
    sidecar = catalog_path.parent / filename
    digest = sha256_bytes(sidecar.read_bytes())
    if document.get(digest_key) != digest:
        raise ValueError(f"{sidecar} digest drifted from CATALOG.json")
    return digest, _plants_from_jsonl(sidecar.read_text(encoding="utf-8"))


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


def _bind_archive_b(
    archive_b: ArchiveBSource,
    *,
    plants: tuple[ArchiveBPlant, ...],
    pin: ArchivePin,
) -> None:
    boundary_slugs_match = not plants or (
        plants[0].success_slug == archive_b.first_slug
        and plants[-1].success_slug == archive_b.last_slug
    )
    checks = (
        (
            archive_b.ref == ARCHIVE_B_REF and archive_b.commit == ARCHIVE_B_COMMIT,
            "archive ref/commit drifted from vocabulary",
        ),
        (archive_b.path == pin.path, "archive path drifted from vocabulary"),
        (
            archive_b.blob_sha == pin.blob_sha and archive_b.sha256 == pin.source_sha256,
            "archive source pin drifted from vocabulary",
        ),
        (archive_b.n_plants == len(plants), "n_plants does not match committed JSONL"),
        (boundary_slugs_match, "first/last slug drifted from committed JSONL"),
    )
    for ok, message in checks:
        if not ok:
            raise ValueError(f"{pin.path} {message}")


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
