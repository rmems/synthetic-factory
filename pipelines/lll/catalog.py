#!/usr/bin/env python3
"""Pinned leftover leftover leftover catalog: load, pin, and AST-extract.

A catalog directory holds ``CATALOG.json`` and ``plants.jsonl``. Historical
leftover leftover leftover mill scripts are read only as text through
:func:`plants_from_source` (``ast.parse``, ``exec: false``).
"""

from __future__ import annotations

import ast
import hashlib
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ._contract import (
    CATALOG_FILENAME,
    CATALOG_FORMAT,
    DEFAULT_CATALOG_ID,
    FACTORY,
    FINDING_CATALOG_FIELD_INVALID,
    FINDING_CATALOG_FIELD_MISSING,
    FINDING_CATALOG_FILE_MISSING,
    FINDING_FACTORY_NOT_REGISTERED,
    FINDING_MILL_NOT_FOUND,
    FINDING_PLANT_DUPLICATE,
    FINDING_PLANT_FIELD_INVALID,
    FINDING_PLANT_FIELD_MISSING,
    FINDING_PLANT_NOT_FOUND,
    FINDING_PLANTS_SHA_MISMATCH,
    FINDING_SOURCE_NOT_PARSEABLE,
    GENERATOR,
    LEGACY_COMMIT,
    LEGACY_REF,
    LllRefusal,
    MILL_PREFIX,
    PAIR_KEYS,
    PLANTS_FILENAME,
    QUOTA_PER_ROUND,
    RECORD_KIND,
    RECORD_PREFIX,
    SOURCE_MILLS,
    bind_import_twin,
    dumps_exact_json,
    load_strict_json,
    refuse_when,
    repo_root,
    shown,
)

REQUIRED_META_FIELDS = (
    "catalog_id",
    "factory",
    "format",
    "mill_prefix",
    "mills",
    "pair_count",
    "plant_count",
    "plants_sha256",
    "quota_per_round",
    "record_kind",
    "record_prefix",
    "source",
)
REQUIRED_SOURCE_FIELDS = ("commit", "method", "not_executed", "ref", "scripts")
SLUG_CHARS = frozenset("abcdefghijklmnopqrstuvwxyz0123456789-")

__all__ = [
    "Catalog",
    "Mill",
    "Plant",
    "catalog_check",
    "default_catalog_dir",
    "load_catalog",
    "plants_from_source",
    "sha256_bytes",
]


@dataclass(frozen=True)
class Plant:
    """One leftover leftover leftover pair identity extracted from ``fn_pair``."""

    plant_id: str
    mill_id: str
    source: str
    base_round: int
    index: int
    title: str
    success_slug: str
    fail_slug: str
    success_plant: str
    fail_plant: str

    def pair_fields(self) -> dict[str, str]:
        return {key: getattr(self, key) for key in PAIR_KEYS}

    def as_mapping(self) -> dict[str, Any]:
        return {
            "base_round": self.base_round,
            "fail_plant": self.fail_plant,
            "fail_slug": self.fail_slug,
            "index": self.index,
            "mill_id": self.mill_id,
            "plant_id": self.plant_id,
            "source": self.source,
            "success_plant": self.success_plant,
            "success_slug": self.success_slug,
            "title": self.title,
        }


@dataclass(frozen=True)
class Mill:
    mill_id: str
    base_round: int
    source: str
    blob_sha: str
    pair_count: int
    plant_count: int


@dataclass(frozen=True)
class Catalog:
    catalog_id: str
    directory: Path
    factory: str
    plants_sha256: str
    plants: tuple[Plant, ...]
    mills: tuple[Mill, ...]
    meta: Mapping[str, Any]

    def plant(self, plant_id: str) -> Plant:
        for item in self.plants:
            if item.plant_id == plant_id:
                return item
        raise LllRefusal(FINDING_PLANT_NOT_FOUND, f"no plant {shown(plant_id)}")

    def mill_plants(self, mill_id: str) -> tuple[Plant, ...]:
        found = tuple(item for item in self.plants if item.mill_id == mill_id)
        refuse_when(not found, FINDING_MILL_NOT_FOUND, f"no mill {shown(mill_id)}")
        return found


def default_catalog_dir() -> Path:
    return repo_root() / "config" / "lll"


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _call_name(node: ast.AST) -> str | None:
    if not isinstance(node, ast.Call):
        return None
    func = node.func
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return func.attr
    return None


def _literal(node: ast.AST) -> Any:
    try:
        return ast.literal_eval(node)
    except (ValueError, TypeError, SyntaxError):
        return None


def _tuple_names(node: ast.AST) -> tuple[str, ...] | None:
    if not isinstance(node, ast.Assign) or len(node.targets) != 1:
        return None
    target = node.targets[0]
    if not isinstance(target, ast.Tuple):
        return None
    names: list[str] = []
    for elt in target.elts:
        if not isinstance(elt, ast.Name):
            return None
        names.append(elt.id)
    return tuple(names)


def _fn_pair_args(node: ast.Assign) -> list[str] | None:
    if _call_name(node.value) != "fn_pair":
        return None
    args = [_literal(item) for item in node.value.args]
    if len(args) < 4 or not all(isinstance(item, str) and item for item in args[:4]):
        return None
    return [item for item in args[:4] if isinstance(item, str)]


def _append_title(node: ast.AST) -> str | None:
    if not isinstance(node, ast.Expr) or not isinstance(node.value, ast.Call):
        return None
    call = node.value
    if not isinstance(call.func, ast.Attribute) or call.func.attr != "append":
        return None
    if not isinstance(call.func.value, ast.Name) or call.func.value.id != "PAIRS":
        return None
    if len(call.args) != 1 or not isinstance(call.args[0], ast.Tuple):
        return None
    if not call.args[0].elts:
        return None
    title = _literal(call.args[0].elts[0])
    return title if isinstance(title, str) and title else None


def plants_from_source(
    source: str,
    *,
    mill_id: str,
    path: str,
    base_round: int,
) -> tuple[Plant, ...]:
    """Extract leftover leftover leftover ``fn_pair`` identities. Never exec."""

    try:
        tree = ast.parse(source, filename=path)
    except SyntaxError as exc:
        raise LllRefusal(FINDING_SOURCE_NOT_PARSEABLE, f"{path} does not parse: {exc}") from exc
    pending: list[str] | None = None
    rows: list[Plant] = []
    seen: set[str] = set()
    for node in tree.body:
        names = _tuple_names(node)
        if names == ("fa", "fb") and isinstance(node, ast.Assign):
            pending = _fn_pair_args(node)
            refuse_when(
                pending is None,
                FINDING_SOURCE_NOT_PARSEABLE,
                f"{path} has a malformed fn_pair bind",
            )
            continue
        title = _append_title(node)
        if title is None:
            continue
        refuse_when(
            pending is None,
            FINDING_SOURCE_NOT_PARSEABLE,
            f"{path} appends a leftover leftover leftover pair without fn_pair",
        )
        assert pending is not None
        plant_id = f"{mill_id}:{pending[0]}"
        refuse_when(plant_id in seen, FINDING_PLANT_DUPLICATE, f"{path} duplicate {plant_id}")
        seen.add(plant_id)
        rows.append(
            Plant(
                plant_id=plant_id,
                mill_id=mill_id,
                source=path,
                base_round=base_round,
                index=len(rows),
                title=title,
                success_slug=pending[0],
                fail_slug=pending[1],
                success_plant=pending[2],
                fail_plant=pending[3],
            )
        )
        pending = None
    refuse_when(
        pending is not None,
        FINDING_SOURCE_NOT_PARSEABLE,
        f"{path} has a leftover leftover leftover fn_pair without PAIRS.append",
    )
    refuse_when(
        not rows,
        FINDING_SOURCE_NOT_PARSEABLE,
        f"{path} has no leftover leftover leftover pairs",
    )
    return tuple(rows)


def _require_str(mapping: Mapping[str, Any], key: str, where: str) -> str:
    value = mapping.get(key)
    refuse_when(
        not isinstance(value, str) or not value.strip(),
        FINDING_CATALOG_FIELD_INVALID if where == "catalog" else FINDING_PLANT_FIELD_INVALID,
        f"{where} {key} must be a non-empty string",
    )
    assert isinstance(value, str)
    return value


def _require_int(mapping: Mapping[str, Any], key: str, where: str) -> int:
    value = mapping.get(key)
    refuse_when(
        type(value) is not int or value < 0,
        FINDING_CATALOG_FIELD_INVALID if where == "catalog" else FINDING_PLANT_FIELD_INVALID,
        f"{where} {key} must be a non-negative int",
    )
    assert type(value) is int
    return value


def _slug_ok(value: str) -> bool:
    return bool(value) and value[0].isalpha() and set(value) <= SLUG_CHARS


def _plant_from_row(row: Mapping[str, Any], index: int) -> Plant:
    refuse_when(
        not isinstance(row, Mapping),
        FINDING_PLANT_FIELD_INVALID,
        f"plant {index} is not an object",
    )
    missing = [key for key in Plant.__dataclass_fields__ if key not in row]
    refuse_when(
        missing,
        FINDING_PLANT_FIELD_MISSING,
        f"plant {index} missing {missing}",
    )
    mill_id = _require_str(row, "mill_id", "plant")
    success_slug = _require_str(row, "success_slug", "plant")
    fail_slug = _require_str(row, "fail_slug", "plant")
    success_plant = _require_str(row, "success_plant", "plant")
    fail_plant = _require_str(row, "fail_plant", "plant")
    title = _require_str(row, "title", "plant")
    source = _require_str(row, "source", "plant")
    plant_id = _require_str(row, "plant_id", "plant")
    base_round = _require_int(row, "base_round", "plant")
    row_index = _require_int(row, "index", "plant")
    refuse_when(
        plant_id != f"{mill_id}:{success_slug}",
        FINDING_PLANT_FIELD_INVALID,
        f"plant_id {shown(plant_id)} does not match mill and success slug",
    )
    slugs = (success_slug, fail_slug, success_plant, fail_plant)
    refuse_when(
        not all(_slug_ok(item) for item in slugs),
        FINDING_PLANT_FIELD_INVALID,
        f"plant {shown(plant_id)} has an invalid leftover leftover leftover slug",
    )
    return Plant(
        plant_id=plant_id,
        mill_id=mill_id,
        source=source,
        base_round=base_round,
        index=row_index,
        title=title,
        success_slug=success_slug,
        fail_slug=fail_slug,
        success_plant=success_plant,
        fail_plant=fail_plant,
    )


def _mill_from_row(row: Mapping[str, Any]) -> Mill:
    refuse_when(
        not isinstance(row, Mapping),
        FINDING_CATALOG_FIELD_INVALID,
        "mill row is not an object",
    )
    return Mill(
        mill_id=_require_str(row, "mill_id", "catalog"),
        base_round=_require_int(row, "base_round", "catalog"),
        source=_require_str(row, "source", "catalog"),
        blob_sha=_require_str(row, "blob_sha", "catalog"),
        pair_count=_require_int(row, "pair_count", "catalog"),
        plant_count=_require_int(row, "plant_count", "catalog"),
    )


def _registry_factories() -> set[str]:
    payload = load_strict_json((repo_root() / "config" / "FACTORY-REGISTRY.json").read_text())
    rows = payload.get("factories") if isinstance(payload, Mapping) else None
    refuse_when(
        not isinstance(rows, list),
        FINDING_FACTORY_NOT_REGISTERED,
        "factory registry is malformed",
    )
    return {
        str(row["path_id"])
        for row in rows
        if isinstance(row, Mapping) and isinstance(row.get("path_id"), str)
    }


def load_catalog(directory: Path | None = None) -> Catalog:
    catalog_dir = Path(directory) if directory is not None else default_catalog_dir()
    header_path = catalog_dir / CATALOG_FILENAME
    plants_path = catalog_dir / PLANTS_FILENAME
    refuse_when(
        not header_path.is_file(),
        FINDING_CATALOG_FILE_MISSING,
        f"missing {header_path}",
    )
    refuse_when(
        not plants_path.is_file(),
        FINDING_CATALOG_FILE_MISSING,
        f"missing {plants_path}",
    )
    header = load_strict_json(header_path.read_text())
    refuse_when(
        not isinstance(header, Mapping),
        FINDING_CATALOG_FIELD_INVALID,
        "CATALOG.json is not an object",
    )
    missing = [key for key in REQUIRED_META_FIELDS if key not in header]
    refuse_when(
        missing,
        FINDING_CATALOG_FIELD_MISSING,
        f"CATALOG.json missing {missing}",
    )
    source = header.get("source")
    refuse_when(
        not isinstance(source, Mapping),
        FINDING_CATALOG_FIELD_INVALID,
        "source is not an object",
    )
    source_missing = [key for key in REQUIRED_SOURCE_FIELDS if key not in source]
    refuse_when(
        source_missing,
        FINDING_CATALOG_FIELD_MISSING,
        f"source missing {source_missing}",
    )
    plants_text = plants_path.read_bytes()
    digest = sha256_bytes(plants_text)
    declared = _require_str(header, "plants_sha256", "catalog")
    refuse_when(digest != declared, FINDING_PLANTS_SHA_MISMATCH, "plants.jsonl digest drifted")
    plants: list[Plant] = []
    seen: set[str] = set()
    for index, line in enumerate(plants_text.decode().splitlines()):
        if not line.strip():
            continue
        row = load_strict_json(line)
        refuse_when(
            not isinstance(row, Mapping),
            FINDING_PLANT_FIELD_INVALID,
            f"plant line {index} is not an object",
        )
        plant = _plant_from_row(row, index)
        refuse_when(plant.plant_id in seen, FINDING_PLANT_DUPLICATE, f"duplicate {plant.plant_id}")
        seen.add(plant.plant_id)
        plants.append(plant)
    mills = tuple(_mill_from_row(row) for row in header["mills"])
    refuse_when(
        _require_str(header, "factory", "catalog") != FACTORY,
        FINDING_CATALOG_FIELD_INVALID,
        f"factory must be {FACTORY}",
    )
    refuse_when(
        FACTORY not in _registry_factories(),
        FINDING_FACTORY_NOT_REGISTERED,
        f"{FACTORY} is not a reviewed registry row",
    )
    return Catalog(
        catalog_id=_require_str(header, "catalog_id", "catalog"),
        directory=catalog_dir,
        factory=FACTORY,
        plants_sha256=declared,
        plants=tuple(plants),
        mills=mills,
        meta=header,
    )


def catalog_check(directory: Path | None = None) -> list[str]:
    """Return coded findings. An empty list means the pinned catalog is sound."""

    try:
        loaded = load_catalog(directory)
    except LllRefusal as exc:
        return [str(exc)]
    findings: list[str] = []
    if loaded.catalog_id != DEFAULT_CATALOG_ID:
        findings.append(f"{FINDING_CATALOG_FIELD_INVALID}: catalog_id must be {DEFAULT_CATALOG_ID}")
    if loaded.meta.get("format") != CATALOG_FORMAT:
        findings.append(f"{FINDING_CATALOG_FIELD_INVALID}: format must be {CATALOG_FORMAT}")
    if loaded.meta.get("mill_prefix") != MILL_PREFIX:
        findings.append(f"{FINDING_CATALOG_FIELD_INVALID}: mill_prefix must be {MILL_PREFIX}")
    if loaded.meta.get("record_prefix") != RECORD_PREFIX:
        findings.append(f"{FINDING_CATALOG_FIELD_INVALID}: record_prefix must be {RECORD_PREFIX}")
    if loaded.meta.get("record_kind") != RECORD_KIND:
        findings.append(f"{FINDING_CATALOG_FIELD_INVALID}: record_kind must be {RECORD_KIND}")
    if loaded.meta.get("quota_per_round") != QUOTA_PER_ROUND:
        findings.append(
            f"{FINDING_CATALOG_FIELD_INVALID}: quota_per_round must be {QUOTA_PER_ROUND}"
        )
    if loaded.meta.get("pair_count") != len(loaded.plants):
        findings.append(f"{FINDING_CATALOG_FIELD_INVALID}: pair_count does not match plants.jsonl")
    if loaded.meta.get("plant_count") != len(loaded.plants) * 2:
        findings.append(f"{FINDING_CATALOG_FIELD_INVALID}: plant_count must be two per pair")
    if len(loaded.mills) != len(SOURCE_MILLS):
        findings.append(f"{FINDING_CATALOG_FIELD_INVALID}: mill pin count drifted")
    expected = {item[0]: item for item in SOURCE_MILLS}
    for mill in loaded.mills:
        pin = expected.get(mill.mill_id)
        if pin is None:
            findings.append(f"{FINDING_MILL_NOT_FOUND}: unexpected mill {mill.mill_id}")
            continue
        _, source, base_round, blob_sha = pin
        if (mill.source, mill.base_round, mill.blob_sha) != (source, base_round, blob_sha):
            findings.append(
                f"{FINDING_CATALOG_FIELD_INVALID}: mill pin drifted for {mill.mill_id}"
            )
        owned = loaded.mill_plants(mill.mill_id)
        if mill.pair_count != len(owned) or mill.plant_count != len(owned) * 2:
            findings.append(
                f"{FINDING_CATALOG_FIELD_INVALID}: mill counts drifted for {mill.mill_id}"
            )
    source = loaded.meta["source"]
    if source.get("ref") != LEGACY_REF or source.get("commit") != LEGACY_COMMIT:
        findings.append(
            f"{FINDING_CATALOG_FIELD_INVALID}: leftover leftover leftover source pin drifted"
        )
    if source.get("method") != "git-show+ast.parse":
        findings.append(f"{FINDING_CATALOG_FIELD_INVALID}: extract method must stay AST-only")
    scripts = source.get("scripts")
    if scripts != [item[1] for item in SOURCE_MILLS]:
        findings.append(f"{FINDING_CATALOG_FIELD_INVALID}: source scripts drifted")
    if loaded.meta.get("generator") not in {None, GENERATOR}:
        findings.append(f"{FINDING_CATALOG_FIELD_INVALID}: generator must stay {GENERATOR}")
    return findings


def render_plants_jsonl(plants: tuple[Plant, ...]) -> bytes:
    """Exact leftover leftover leftover plant bytes used for the digest pin."""

    lines = [
        dumps_exact_json(plant.as_mapping(), ensure_ascii=False, sort_keys=True)
        for plant in plants
    ]
    return ("".join(line + "\n" for line in lines)).encode()


bind_import_twin(__name__)
