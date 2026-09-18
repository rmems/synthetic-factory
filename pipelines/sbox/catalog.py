#!/usr/bin/env python3
"""Pinned sbox catalog: header pins plus compact ``plants.jsonl`` identities.

``CATALOG.json`` holds source pins and extract bookkeeping.
``plants.jsonl`` holds one AST-extracted identity per line. Mill scripts
stay on ``legacy-mill-lane``; load raises rather than excluding a drifted pin.
"""

from __future__ import annotations

import hashlib
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
    FINDING_CATALOG_SHA256_MISMATCH,
    FINDING_DUPLICATE_FAMILY,
    GENERATOR,
    PLANTS_FILENAME,
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
from .generate import (
    LEFTOVER_FIELDS,
    RUNTIME_FIELDS,
    SHAPE_LEFTOVER_DICT,
    SHAPE_LEFTOVER_ROW,
    SHAPE_RUNTIME,
    plants_from_source,
)

REQUIRED_META = (
    "catalog_id",
    "family",
    "schema",
    "factory",
    "generator",
    "source",
    "extract",
    "sources",
    "plants_filename",
    "plants_sha256",
)
CATALOG_ROLES = frozenset({"catalog", "loop", "plant-gen", "publisher"})

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
    family: str
    ok: str | None = None
    over: str | None = None
    miss: str | None = None
    trigger: str | None = None
    vector: str | None = None
    over_slug: str | None = None
    miss_slug: str | None = None
    inc: int | None = None
    proc: str | None = None

    def as_mapping(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "source": self.source,
            "shape": self.shape,
            "family": self.family,
        }
        if self.shape == SHAPE_RUNTIME:
            payload.update(
                {
                    "ok": self.ok,
                    "over": self.over,
                    "miss": self.miss,
                    "trigger": self.trigger,
                    "vector": self.vector,
                }
            )
            return payload
        payload.update(
            {
                "over_slug": self.over_slug,
                "miss_slug": self.miss_slug,
                "inc": self.inc,
                "proc": self.proc,
            }
        )
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
    first_round: int | None = None
    companion: str | None = None


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


def plants_path() -> Path:
    return package_dir() / PLANTS_FILENAME


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _read_jsonl(path: Path) -> tuple[dict[str, Any], ...]:
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        refuse(FINDING_CATALOG_FILE_MISSING, f"{path} is unreadable: {exc}")
    refuse_when(
        "\r" in raw,
        FINDING_CATALOG_FIELD_INVALID,
        f"{path.name} must not contain CR bytes",
    )
    if not raw:
        refuse(FINDING_CATALOG_EMPTY, f"{path.name} is empty")
    if not raw.endswith("\n"):
        refuse(FINDING_CATALOG_FIELD_INVALID, f"{path.name} must end with a trailing newline")
    lines = raw.split("\n")
    if lines[-1] == "":
        lines = lines[:-1]
    rows: list[dict[str, Any]] = []
    for index, line in enumerate(lines, 1):
        refuse_when(
            line != line.strip() or not line,
            FINDING_CATALOG_FIELD_INVALID,
            f"{path.name} line {index} must be one compact object",
        )
        try:
            row = load_strict_json(line)
        except ValueError as exc:
            refuse(FINDING_CATALOG_FIELD_INVALID, f"{path.name} line {index} is not strict JSON: {exc}")
        rows.append(_as_mapping(row, f"{path.name}:{index}"))
    return tuple(rows)


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
    family = _as_str(row.get("family"), f"{where}.family")
    if shape == SHAPE_RUNTIME:
        missing = [field for field in RUNTIME_FIELDS if field not in row]
        refuse_when(bool(missing), FINDING_CATALOG_FIELD_MISSING, f"{where} missing {missing}")
        return Plant(
            source=source,
            shape=shape,
            family=family,
            ok=_as_str(row["ok"], f"{where}.ok"),
            over=_as_str(row["over"], f"{where}.over"),
            miss=_as_str(row["miss"], f"{where}.miss"),
            trigger=_as_str(row["trigger"], f"{where}.trigger"),
            vector=_as_str(row["vector"], f"{where}.vector"),
        )
    refuse_when(
        shape not in {SHAPE_LEFTOVER_DICT, SHAPE_LEFTOVER_ROW},
        FINDING_CATALOG_FIELD_INVALID,
        f"{where}.shape {shown(shape)} is not a leftover catalog shape",
    )
    missing = [field for field in LEFTOVER_FIELDS if field not in row]
    refuse_when(bool(missing), FINDING_CATALOG_FIELD_MISSING, f"{where} missing {missing}")
    return Plant(
        source=source,
        shape=shape,
        family=family,
        over_slug=_as_str(row["over_slug"], f"{where}.over_slug"),
        miss_slug=_as_str(row["miss_slug"], f"{where}.miss_slug"),
        inc=_as_int(row["inc"], f"{where}.inc"),
        proc=_as_str(row["proc"], f"{where}.proc"),
    )


def _source_from_mapping(row: Mapping[str, Any], where: str) -> SourcePin:
    role = _as_str(row.get("role"), f"{where}.role")
    refuse_when(
        role not in CATALOG_ROLES,
        FINDING_CATALOG_FIELD_INVALID,
        f"{where}.role {shown(role)} is not a pinned sbox role",
    )
    digest = _as_str(row.get("sha256"), f"{where}.sha256")
    refuse_when(
        len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest),
        FINDING_CATALOG_FIELD_INVALID,
        f"{where}.sha256 is not a lowercase hex digest",
    )
    first_family = row.get("first_family")
    first_round = row.get("first_round")
    companion = row.get("companion")
    return SourcePin(
        path=_as_str(row.get("path"), f"{where}.path"),
        role=role,
        shape=_as_str(row.get("shape"), f"{where}.shape"),
        blob_sha1=_as_str(row.get("blob_sha1"), f"{where}.blob_sha1"),
        sha256=digest,
        n_rows=_as_int(row.get("n_rows"), f"{where}.n_rows"),
        first_family=None if first_family is None else _as_str(first_family, f"{where}.first_family"),
        first_round=None if first_round is None else _as_int(first_round, f"{where}.first_round"),
        companion=None if companion is None else _as_str(companion, f"{where}.companion"),
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
    plants_file = _as_str(meta.get("plants_filename"), "plants_filename")
    refuse_when(
        plants_file != PLANTS_FILENAME,
        FINDING_CATALOG_FIELD_INVALID,
        f"plants_filename {shown(plants_file)} != {PLANTS_FILENAME}",
    )
    pinned_digest = _as_str(meta.get("plants_sha256"), "plants_sha256")
    refuse_when(
        len(pinned_digest) != 64 or any(char not in "0123456789abcdef" for char in pinned_digest),
        FINDING_CATALOG_FIELD_INVALID,
        "plants_sha256 is not a lowercase hex digest",
    )
    jsonl_file = catalog_file.parent / plants_file
    try:
        plants_bytes = jsonl_file.read_bytes()
    except OSError as exc:
        refuse(FINDING_CATALOG_FILE_MISSING, f"missing {jsonl_file}: {exc}")
    digest = sha256_bytes(plants_bytes)
    refuse_when(
        digest != pinned_digest,
        FINDING_CATALOG_SHA256_MISMATCH,
        f"{plants_file} digest {digest} != catalog pin {pinned_digest}",
    )
    raw_sources = meta.get("sources")
    refuse_when(not isinstance(raw_sources, list) or not raw_sources,
                FINDING_CATALOG_EMPTY, "catalog has no source pins")
    plants = tuple(
        _plant_from_mapping(row, f"{plants_file}:{index}")
        for index, row in enumerate(_read_jsonl(jsonl_file), 1)
    )
    refuse_when(not plants, FINDING_CATALOG_EMPTY, "catalog has no plants")
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
    families: dict[str, str] = {}
    for plant in loaded.plants:
        key = f"{plant.source}:{plant.family}"
        if key in families:
            refuse(FINDING_DUPLICATE_FAMILY, f"family {shown(plant.family)} repeats in {plant.source}")
        families[key] = plant.shape
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
    deferred = loaded.extract.get("deferred_row_count")
    refuse_when(
        type(deferred) is not int or deferred != full_rows - len(loaded.plants),
        FINDING_CATALOG_FIELD_INVALID,
        "extract.deferred_row_count drifted from committed plants",
    )
    return {
        "status": "ok",
        "catalog_id": loaded.catalog_id,
        "factory": loaded.factory,
        "plants": len(loaded.plants),
        "sources": len(loaded.sources),
        "catalog_files": len(catalog_sources),
        "full_row_count": full_rows,
        "deferred_row_count": deferred,
        "first_round": 359,
        "exec": False,
    }


bind_import_twin(__name__)
