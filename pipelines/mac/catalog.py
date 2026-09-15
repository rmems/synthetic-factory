#!/usr/bin/env python3
"""Pinned mac catalog: identity slice, source pins, and load checks.

``CATALOG.json`` holds 24 representative plant identities plus sha pins
for every leftover mill / hop-loop on ``legacy-mill-lane``. Full turn
payloads stay off this PR so the slice stays under the mill burst line
cap. Load raises rather than excluding a drifted pin.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ._contract import (
    CATALOG_FILENAME,
    CATALOG_ID,
    CATALOG_SCHEMA,
    FACTORY,
    FAMILY_PREFIX,
    FINDING_CATALOG_EMPTY,
    FINDING_CATALOG_FIELD_INVALID,
    FINDING_CATALOG_FIELD_MISSING,
    FINDING_CATALOG_FILE_MISSING,
    FINDING_DUPLICATE_FAMILY,
    GENERATOR,
    SOURCE_COMMIT,
    SOURCE_REF,
    bind_import_twin,
    load_strict_json,
    package_dir,
    refuse,
    refuse_first,
    refuse_when,
    shown,
)
from .generate import SHAPE_A, SHAPE_P, SHAPE_SCEN, plants_from_source

REQUIRED_META = (
    "catalog_id",
    "family",
    "schema",
    "factory",
    "generator",
    "source",
    "extract",
    "sources",
    "plants",
)
CATALOG_ROLES = frozenset({"catalog", "loop"})

__all__ = [
    "Catalog",
    "Plant",
    "SourcePin",
    "catalog_check",
    "catalog_path",
    "load_catalog",
    "plants_from_source",
]


@dataclass(frozen=True)
class Plant:
    source: str
    shape: str
    slug: str
    goal: str | None = None
    process: str | None = None
    metric: str | None = None
    spike: str | None = None

    def as_mapping(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "source": self.source,
            "shape": self.shape,
            "slug": self.slug,
        }
        if self.shape == SHAPE_A:
            payload.update(
                {"process": self.process, "metric": self.metric, "spike": self.spike}
            )
            return payload
        payload["goal"] = self.goal
        return payload


@dataclass(frozen=True)
class SourcePin:
    path: str
    role: str
    shape: str
    blob_sha1: str
    sha256: str
    n_rows: int
    first_family: str | None = None


@dataclass(frozen=True)
class Catalog:
    catalog_id: str
    factory: str
    plants: tuple[Plant, ...]
    sources: tuple[SourcePin, ...]
    extract: Mapping[str, Any]
    meta: Mapping[str, Any]


def catalog_path() -> Path:
    return package_dir() / CATALOG_FILENAME


def _as_mapping(value: Any, where: str) -> dict[str, Any]:
    refuse_when(
        not isinstance(value, dict),
        FINDING_CATALOG_FIELD_INVALID,
        f"{where} must be an object",
    )
    return value


def _as_str(value: Any, where: str) -> str:
    refuse_when(
        not isinstance(value, str) or not value,
        FINDING_CATALOG_FIELD_INVALID,
        f"{where} must be a non-empty string, got {shown(value)}",
    )
    return value


def _as_int(value: Any, where: str) -> int:
    refuse_when(
        type(value) is not int,
        FINDING_CATALOG_FIELD_INVALID,
        f"{where} must be an int, got {shown(value)}",
    )
    return value


def _plant_from_mapping(row: Mapping[str, Any], where: str) -> Plant:
    source = _as_str(row.get("source"), f"{where}.source")
    shape = _as_str(row.get("shape"), f"{where}.shape")
    slug = _as_str(row.get("slug"), f"{where}.slug")
    if shape == SHAPE_A:
        return Plant(
            source=source,
            shape=shape,
            slug=slug,
            process=_as_str(row.get("process"), f"{where}.process"),
            metric=_as_str(row.get("metric"), f"{where}.metric"),
            spike=_as_str(row.get("spike"), f"{where}.spike"),
        )
    refuse_when(
        shape not in {SHAPE_P, SHAPE_SCEN},
        FINDING_CATALOG_FIELD_INVALID,
        f"{where}.shape {shown(shape)} is not a mac catalog shape",
    )
    return Plant(
        source=source,
        shape=shape,
        slug=slug,
        goal=_as_str(row.get("goal"), f"{where}.goal"),
    )


def _source_from_mapping(row: Mapping[str, Any], where: str) -> SourcePin:
    role = _as_str(row.get("role"), f"{where}.role")
    refuse_when(
        role not in CATALOG_ROLES,
        FINDING_CATALOG_FIELD_INVALID,
        f"{where}.role {shown(role)} is not a pinned mac role",
    )
    digest = _as_str(row.get("sha256"), f"{where}.sha256")
    refuse_when(
        len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest),
        FINDING_CATALOG_FIELD_INVALID,
        f"{where}.sha256 is not a lowercase hex digest",
    )
    first_family = row.get("first_family")
    return SourcePin(
        path=_as_str(row.get("path"), f"{where}.path"),
        role=role,
        shape=_as_str(row.get("shape"), f"{where}.shape"),
        blob_sha1=_as_str(row.get("blob_sha1"), f"{where}.blob_sha1"),
        sha256=digest,
        n_rows=_as_int(row.get("n_rows"), f"{where}.n_rows"),
        first_family=None if first_family is None else _as_str(first_family, f"{where}.first_family"),
    )


def load_catalog(path: Path | None = None) -> Catalog:
    catalog_file = catalog_path() if path is None else path
    refuse_when(
        not catalog_file.is_file(),
        FINDING_CATALOG_FILE_MISSING,
        f"missing {catalog_file}",
    )
    meta = _as_mapping(
        load_strict_json(catalog_file.read_text(encoding="utf-8")),
        "CATALOG.json",
    )
    missing = [key for key in REQUIRED_META if key not in meta]
    refuse_when(bool(missing), FINDING_CATALOG_FIELD_MISSING, f"CATALOG.json missing {missing}")
    refuse_first((
        (meta.get("catalog_id") != CATALOG_ID, FINDING_CATALOG_FIELD_INVALID,
         f"catalog_id {shown(meta.get('catalog_id'))} != {CATALOG_ID}"),
        (meta.get("family") != FAMILY_PREFIX, FINDING_CATALOG_FIELD_INVALID,
         f"family {shown(meta.get('family'))} != {FAMILY_PREFIX}"),
        (meta.get("schema") != CATALOG_SCHEMA, FINDING_CATALOG_FIELD_INVALID,
         f"schema {shown(meta.get('schema'))} != {CATALOG_SCHEMA}"),
        (meta.get("factory") != FACTORY, FINDING_CATALOG_FIELD_INVALID,
         f"factory {shown(meta.get('factory'))} != {FACTORY}"),
        (meta.get("generator") != GENERATOR, FINDING_CATALOG_FIELD_INVALID,
         f"generator {shown(meta.get('generator'))} != {GENERATOR}"),
    ))
    source = _as_mapping(meta.get("source"), "source")
    refuse_first((
        (source.get("ref") != SOURCE_REF, FINDING_CATALOG_FIELD_INVALID,
         f"source.ref {shown(source.get('ref'))} != {SOURCE_REF}"),
        (source.get("commit") != SOURCE_COMMIT, FINDING_CATALOG_FIELD_INVALID,
         f"source.commit drifted from {SOURCE_COMMIT}"),
        (source.get("method") != "git-show+ast.parse", FINDING_CATALOG_FIELD_INVALID,
         "source.method must be git-show+ast.parse"),
        (source.get("exec") is not False, FINDING_CATALOG_FIELD_INVALID,
         "source.exec must be false"),
    ))
    extract = _as_mapping(meta.get("extract"), "extract")
    raw_plants = meta.get("plants")
    raw_sources = meta.get("sources")
    refuse_when(not isinstance(raw_plants, list) or not raw_plants,
                FINDING_CATALOG_EMPTY, "catalog has no plants")
    refuse_when(not isinstance(raw_sources, list) or not raw_sources,
                FINDING_CATALOG_EMPTY, "catalog has no source pins")
    plants = tuple(
        _plant_from_mapping(_as_mapping(row, f"plants[{index}]"), f"plants[{index}]")
        for index, row in enumerate(raw_plants)
    )
    sources = tuple(
        _source_from_mapping(_as_mapping(row, f"sources[{index}]"), f"sources[{index}]")
        for index, row in enumerate(raw_sources)
    )
    return Catalog(
        catalog_id=CATALOG_ID,
        factory=FACTORY,
        plants=plants,
        sources=sources,
        extract=extract,
        meta=meta,
    )


def catalog_check(path: Path | None = None) -> dict[str, Any]:
    """Fail closed unless pins, uniqueness, and extract counts hold."""

    loaded = load_catalog(path)
    refuse_when(not loaded.plants, FINDING_CATALOG_EMPTY, "catalog has no plants")
    slugs: dict[str, str] = {}
    for plant in loaded.plants:
        key = f"{plant.source}:{plant.slug}"
        if key in slugs:
            refuse(FINDING_DUPLICATE_FAMILY, f"slug {shown(plant.slug)} repeats in {plant.source}")
        slugs[key] = plant.shape
    catalog_sources = tuple(pin for pin in loaded.sources if pin.role == "catalog")
    refuse_when(
        any(pin.n_rows < 1 for pin in catalog_sources),
        FINDING_CATALOG_FIELD_INVALID,
        "a catalog source pin has n_rows < 1",
    )
    full_rows = sum(pin.n_rows for pin in catalog_sources)
    refuse_when(
        loaded.extract.get("full_row_count") != full_rows,
        FINDING_CATALOG_FIELD_INVALID,
        f"extract.full_row_count {shown(loaded.extract.get('full_row_count'))} != {full_rows}",
    )
    refuse_when(
        loaded.extract.get("committed_rows") != len(loaded.plants),
        FINDING_CATALOG_FIELD_INVALID,
        "extract.committed_rows drifted from the plant slice",
    )
    refuse_when(
        loaded.extract.get("full_source_files") != len(loaded.sources),
        FINDING_CATALOG_FIELD_INVALID,
        "extract.full_source_files drifted from the source pins",
    )
    return {
        "status": "ok",
        "catalog_id": loaded.catalog_id,
        "factory": loaded.factory,
        "plants": len(loaded.plants),
        "sources": len(loaded.sources),
        "catalog_files": len(catalog_sources),
        "full_row_count": full_rows,
        "first_round": 3034,
        "exec": False,
    }


bind_import_twin(__name__)
