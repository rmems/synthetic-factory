#!/usr/bin/env python3
"""Pinned FLK plant catalog: load, pin, and AST-extract (never exec).

A catalog directory holds ``CATALOG.json`` (identity, factory, mill pins)
and ``plants.jsonl`` (one plant per line). Load verifies the plants digest
and every required field before a plant is trusted. Historical leftover
mill scripts are read only as text through :func:`plants_from_source`.
"""

from __future__ import annotations

import ast
import hashlib
import re
import sys
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import _contract
from ._contract import (
    FINDING_CATALOG_FIELD_INVALID,
    FINDING_CATALOG_FIELD_MISSING,
    FINDING_CATALOG_FILE_MISSING,
    FINDING_FACTORY_NOT_REGISTERED,
    FINDING_MILL_NOT_FOUND,
    FINDING_PLANT_FIELD_INVALID,
    FINDING_PLANT_FIELD_MISSING,
    FINDING_PLANT_NOT_FOUND,
    FINDING_SOURCE_NOT_PARSEABLE,
    FlkRefusal,
    bind_import_twin,
    load_strict_json,
    repo_root,
)

CATALOG_FILENAME = _contract.CATALOG_FILENAME
CATALOG_FORMAT = _contract.CATALOG_FORMAT
FACTORY = _contract.FACTORY
FINDING_CATALOG_SHA256_MISMATCH = _contract.FINDING_CATALOG_SHA256_MISMATCH
FINDING_PLANT_DUPLICATE_ID = _contract.FINDING_PLANT_DUPLICATE_ID
MILL_PREFIX = _contract.MILL_PREFIX
PLANTS_FILENAME = _contract.PLANTS_FILENAME
QUOTA_PER_ROUND = _contract.QUOTA_PER_ROUND
RECORD_KIND = _contract.RECORD_KIND

if (__package__ or "").startswith("pipelines."):
    from ..catalog_cli.pinned_load import keyed_plants_from_source, load_pinned_catalog
    from ..catalog_cli.source_const import plant_const_eval, registry_factory_ids
else:
    from catalog_cli.pinned_load import keyed_plants_from_source, load_pinned_catalog
    from catalog_cli.source_const import plant_const_eval, registry_factory_ids

PLANT_KEYS = (
    "slug",
    "runner",
    "drop",
    "cause",
    "cmd",
    "drop_cmd",
    "file",
    "src",
    "mut",
    "ok",
    "leftover",
    "assign",
    "isolate",
    "naive",
    "ci",
    "ticket",
)
MILL_ID_RE = re.compile(r"^flk_r[0-9]+$")
SLUG_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")

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
    """One leftover-cause plant: runner, flake cause, isolate vs naive skip."""

    plant_id: str
    mill_id: str
    source: str
    base_round: int
    slug: str
    runner: str
    drop: str
    cause: str
    cmd: str
    drop_cmd: str
    test_file: str
    source_file: str
    mut: str
    ok: str
    leftover: str
    assign: str
    isolate: str
    naive: str
    ci: str
    ticket: str


@dataclass(frozen=True)
class Mill:
    mill_id: str
    base_round: int
    source: str
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
        raise FlkRefusal(FINDING_PLANT_NOT_FOUND, f"no plant {plant_id!r} in the catalog")

    def mill_plants(self, mill_id: str) -> tuple[Plant, ...]:
        found = tuple(item for item in self.plants if item.mill_id == mill_id)
        if not found:
            raise FlkRefusal(FINDING_MILL_NOT_FOUND, f"no mill {mill_id!r} in the catalog")
        return found


def default_catalog_dir() -> Path:
    return repo_root() / "config" / "flk"


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _const_eval(node: ast.AST) -> Any:
    """Literal values only. Refuses calls, names, and starred dicts."""

    return plant_const_eval(node, FlkRefusal, FINDING_SOURCE_NOT_PARSEABLE)


_SOURCE_SPEC = {
    "list_name": "PLANTS",
    "base_name": "BASE",
    "prefix": "flk_r",
    "pattern": "flk_rNNN",
    "keys": PLANT_KEYS,
    "label": "PLANTS",
    "evaluate": _const_eval,
    "fullmatch": MILL_ID_RE.fullmatch,
}
_SOURCE_REFUSALS = (
    FlkRefusal,
    FINDING_SOURCE_NOT_PARSEABLE,
    FINDING_PLANT_FIELD_INVALID,
    FINDING_PLANT_FIELD_MISSING,
)


def plants_from_source(
    text: str, *, mill_id: str, source: str, base_round: int | None = None
) -> tuple[dict[str, Any], ...]:
    """AST-extract ``PLANTS`` from leftover-mill source text. Never exec."""

    identity = {"mill_id": mill_id, "source": source, "base_round": base_round}
    return keyed_plants_from_source(text, identity, _SOURCE_SPEC, _SOURCE_REFUSALS)


def _field(mapping: Any, key: str, kinds: type | tuple[type, ...], where: str) -> Any:
    if not isinstance(mapping, dict):
        raise FlkRefusal(FINDING_CATALOG_FIELD_INVALID, f"{where} must be an object")
    if key not in mapping:
        raise FlkRefusal(FINDING_CATALOG_FIELD_MISSING, f"{where}.{key} is missing")
    value = mapping[key]
    if isinstance(value, bool) and kinds is not bool:
        raise FlkRefusal(FINDING_CATALOG_FIELD_INVALID, f"{where}.{key} has the wrong type")
    if not isinstance(value, kinds):
        raise FlkRefusal(FINDING_CATALOG_FIELD_INVALID, f"{where}.{key} has the wrong type")
    return value


def _require_text(value: Any, where: str, code: str) -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise FlkRefusal(code, f"{where} must be a non-empty stripped string")
    return value


def _plant_from_row(row: Any, where: str) -> Plant:
    if not isinstance(row, dict):
        raise FlkRefusal(FINDING_PLANT_FIELD_INVALID, f"{where} must be an object")
    mill_id = _require_text(row.get("mill_id"), f"{where}.mill_id", FINDING_PLANT_FIELD_INVALID)
    slug = _require_text(row.get("slug"), f"{where}.slug", FINDING_PLANT_FIELD_INVALID)
    if not MILL_ID_RE.fullmatch(mill_id):
        raise FlkRefusal(FINDING_PLANT_FIELD_INVALID, f"{where}.mill_id is not flk_rNNN")
    if not SLUG_RE.fullmatch(slug):
        raise FlkRefusal(FINDING_PLANT_FIELD_INVALID, f"{where}.slug is not a plant slug")
    plant_id = _require_text(row.get("plant_id"), f"{where}.plant_id", FINDING_PLANT_FIELD_INVALID)
    expected = f"{mill_id}:{slug}"
    if plant_id != expected:
        raise FlkRefusal(
            FINDING_PLANT_FIELD_INVALID,
            f"{where}.plant_id must be {expected!r}",
        )
    base_round = row.get("base_round")
    if not isinstance(base_round, int) or isinstance(base_round, bool) or base_round < 1:
        raise FlkRefusal(FINDING_PLANT_FIELD_INVALID, f"{where}.base_round must be a positive int")
    fields = {
        key: _require_text(row.get(key), f"{where}.{key}", FINDING_PLANT_FIELD_MISSING)
        for key in PLANT_KEYS
    }
    return Plant(
        plant_id=plant_id,
        mill_id=mill_id,
        source=_require_text(row.get("source"), f"{where}.source", FINDING_PLANT_FIELD_MISSING),
        base_round=base_round,
        slug=slug,
        runner=fields["runner"],
        drop=fields["drop"],
        cause=fields["cause"],
        cmd=fields["cmd"],
        drop_cmd=fields["drop_cmd"],
        test_file=fields["file"],
        source_file=fields["src"],
        mut=fields["mut"],
        ok=fields["ok"],
        leftover=fields["leftover"],
        assign=fields["assign"],
        isolate=fields["isolate"],
        naive=fields["naive"],
        ci=fields["ci"],
        ticket=fields["ticket"],
    )


def _mill_from_row(row: Any, where: str) -> Mill:
    mill_id = _require_text(
        _field(row, "mill_id", str, where), f"{where}.mill_id", FINDING_CATALOG_FIELD_INVALID
    )
    if not MILL_ID_RE.fullmatch(mill_id):
        raise FlkRefusal(FINDING_CATALOG_FIELD_INVALID, f"{where}.mill_id is not flk_rNNN")
    base_round = _field(row, "base_round", int, where)
    if isinstance(base_round, bool) or base_round < 1:
        raise FlkRefusal(
            FINDING_CATALOG_FIELD_INVALID, f"{where}.base_round must be a positive int"
        )
    plant_count = _field(row, "plant_count", int, where)
    if isinstance(plant_count, bool) or plant_count < 1:
        raise FlkRefusal(
            FINDING_CATALOG_FIELD_INVALID, f"{where}.plant_count must be a positive int"
        )
    return Mill(
        mill_id=mill_id,
        base_round=base_round,
        source=_require_text(
            _field(row, "source", str, where), f"{where}.source", FINDING_CATALOG_FIELD_INVALID
        ),
        plant_count=plant_count,
    )


def _read_jsonl(path: Path) -> tuple[Any, ...]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise FlkRefusal(FINDING_CATALOG_FILE_MISSING, f"{path} is unreadable: {exc}") from exc
    if not text.endswith("\n") or "\r" in text:
        raise FlkRefusal(FINDING_CATALOG_FIELD_INVALID, f"{path.name} must be LF-framed jsonl")
    rows = []
    for index, line in enumerate(text.splitlines(), start=1):
        if not line:
            raise FlkRefusal(FINDING_CATALOG_FIELD_INVALID, f"{path.name}:{index} is empty")
        try:
            rows.append(load_strict_json(line))
        except ValueError as exc:
            raise FlkRefusal(
                FINDING_CATALOG_FIELD_INVALID, f"{path.name}:{index} is not strict JSON"
            ) from exc
    return tuple(rows)


def _registry_factory_ids() -> set[str]:
    return registry_factory_ids(
        repo_root,
        load_strict_json,
        lambda message: FlkRefusal(FINDING_FACTORY_NOT_REGISTERED, message),
    )


CATALOG_HOOKS = (
    _field,
    _require_text,
    _mill_from_row,
    _plant_from_row,
    _read_jsonl,
    _registry_factory_ids,
)


def load_catalog(directory: Path | None = None) -> Catalog:
    """Load a catalog directory and refuse unless every pin holds."""

    return load_pinned_catalog(directory, sys.modules[__name__], _contract, FlkRefusal)



def catalog_check(directory: Path | None = None) -> list[dict[str, str]]:
    """Load the catalog. An invalid catalog is a refusal, not a finding list."""

    loaded = load_catalog(directory)
    if loaded.plants:
        return []
    return [{"code": FINDING_CATALOG_FIELD_INVALID, "detail": "empty catalog"}]


bind_import_twin(__name__)
