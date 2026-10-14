#!/usr/bin/env python3
"""Pinned SAF pair catalog: load, pin, and AST-extract (never exec).

A catalog directory holds ``CATALOG.json`` (identity, factory, mill pins)
and ``plants.jsonl`` (one pair per line). Load verifies the plants digest
and every required field before a pair is trusted. Historical leftover
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
    FLAVORS,
    PAIR_KEYS,
    SafRefusal,
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
    from ..catalog_cli.source_const import (
        const_dict,
        keyed_plant_rows,
        load_pinned_catalog,
        registry_factory_ids,
        require_positive_base,
    )
else:
    from catalog_cli.source_const import (
        const_dict,
        keyed_plant_rows,
        load_pinned_catalog,
        registry_factory_ids,
        require_positive_base,
    )

MILL_ID_RE = re.compile(r"^saf_r[0-9]+$")
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
class CatalogPlant:
    """One leftover leftover leftover safety pair from ``saf_r5045``."""

    plant_id: str
    mill_id: str
    source: str
    base_round: int
    flavor: str
    slug: str
    twin: str
    plant: str
    mutate: str
    flag: str
    readonly: str
    runbook: str
    policy: str
    owner: str
    safe: str
    trigger: str
    ticket: str
    dest: str
    extra: str


Plant = CatalogPlant


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
        raise SafRefusal(FINDING_PLANT_NOT_FOUND, f"no plant {plant_id!r} in the catalog")

    def mill_plants(self, mill_id: str) -> tuple[Plant, ...]:
        found = tuple(item for item in self.plants if item.mill_id == mill_id)
        if not found:
            raise SafRefusal(FINDING_MILL_NOT_FOUND, f"no mill {mill_id!r} in the catalog")
        return found


def default_catalog_dir() -> Path:
    return repo_root() / "config" / "saf"


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _const_eval(node: ast.AST) -> Any:
    """Literal values and keyword-only ``dict(...)`` calls. Never exec."""

    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, (ast.List, ast.Tuple)):
        values = [_const_eval(item) for item in node.elts]
        return values if isinstance(node, ast.List) else tuple(values)
    if isinstance(node, ast.Dict):
        return const_dict(
            node,
            _const_eval,
            lambda: SafRefusal(
                FINDING_SOURCE_NOT_PARSEABLE, "pair source uses dict unpacking"
            ),
        )
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        return -_const_eval(node.operand)
    if isinstance(node, ast.Call):
        func = node.func
        if (
            isinstance(func, ast.Name)
            and func.id == "dict"
            and not node.args
            and all(keyword.arg is not None for keyword in node.keywords)
        ):
            return {
                keyword.arg: _const_eval(keyword.value) for keyword in node.keywords
            }
        raise SafRefusal(
            FINDING_SOURCE_NOT_PARSEABLE,
            f"pair source uses a non-literal call ({type(node).__name__})",
        )
    raise SafRefusal(
        FINDING_SOURCE_NOT_PARSEABLE,
        f"pair source is not a constant ({type(node).__name__})",
    )


def _assigned_name(node: ast.AST) -> tuple[str, ast.AST] | None:
    if isinstance(node, ast.Assign) and len(node.targets) == 1:
        target = node.targets[0]
        if isinstance(target, ast.Name):
            return target.id, node.value
    if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
        value = node.value
        if value is not None:
            return node.target.id, value
    return None


def plants_from_source(
    text: str,
    *,
    mill_id: str,
    source: str,
    base_round: int | None = None,
) -> tuple[dict[str, Any], ...]:
    """AST-extract ``PAIRS`` from leftover-mill source text. Never exec."""

    try:
        tree = ast.parse(text)
    except SyntaxError as exc:
        raise SafRefusal(
            FINDING_SOURCE_NOT_PARSEABLE, f"{source} does not parse: {exc}"
        ) from exc
    raw_pairs: Any = None
    inferred_base: Any = None
    for node in tree.body:
        assigned = _assigned_name(node)
        if assigned is None:
            continue
        name, value = assigned
        if name == "PAIRS":
            raw_pairs = _const_eval(value)
        elif name == "BASE":
            inferred_base = _const_eval(value)
    if not isinstance(raw_pairs, list) or not raw_pairs:
        raise SafRefusal(FINDING_SOURCE_NOT_PARSEABLE, f"{source} has no PAIRS list")
    if not MILL_ID_RE.fullmatch(mill_id):
        raise SafRefusal(FINDING_PLANT_FIELD_INVALID, f"mill_id {mill_id!r} is not saf_rNNN")
    base = require_positive_base(
        inferred_base if base_round is None else base_round,
        mill_id,
        "saf_r",
        lambda: SafRefusal(FINDING_PLANT_FIELD_INVALID, f"{source} BASE must be a positive int"),
    )
    return keyed_plant_rows(
        raw_pairs,
        PAIR_KEYS,
        {"mill_id": mill_id, "source": source, "base_round": base, "label": "PAIRS"},
        (
            lambda message: SafRefusal(FINDING_SOURCE_NOT_PARSEABLE, message),
            lambda message: SafRefusal(FINDING_PLANT_FIELD_MISSING, message),
        ),
    )


def _field(mapping: Any, key: str, kinds: type | tuple[type, ...], where: str) -> Any:
    if not isinstance(mapping, dict):
        raise SafRefusal(FINDING_CATALOG_FIELD_INVALID, f"{where} must be an object")
    if key not in mapping:
        raise SafRefusal(FINDING_CATALOG_FIELD_MISSING, f"{where}.{key} is missing")
    value = mapping[key]
    if isinstance(value, bool) and kinds is not bool:
        raise SafRefusal(FINDING_CATALOG_FIELD_INVALID, f"{where}.{key} has the wrong type")
    if not isinstance(value, kinds):
        raise SafRefusal(FINDING_CATALOG_FIELD_INVALID, f"{where}.{key} has the wrong type")
    return value


def _require_text(value: Any, where: str, code: str) -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise SafRefusal(code, f"{where} must be a non-empty stripped string")
    return value


def _plant_from_row(row: Any, where: str) -> Plant:
    if not isinstance(row, dict):
        raise SafRefusal(FINDING_PLANT_FIELD_INVALID, f"{where} must be an object")
    mill_id = _require_text(row.get("mill_id"), f"{where}.mill_id", FINDING_PLANT_FIELD_INVALID)
    slug = _require_text(row.get("slug"), f"{where}.slug", FINDING_PLANT_FIELD_INVALID)
    if not MILL_ID_RE.fullmatch(mill_id):
        raise SafRefusal(FINDING_PLANT_FIELD_INVALID, f"{where}.mill_id is not saf_rNNN")
    if not SLUG_RE.fullmatch(slug):
        raise SafRefusal(FINDING_PLANT_FIELD_INVALID, f"{where}.slug is not a plant slug")
    plant_id = _require_text(row.get("plant_id"), f"{where}.plant_id", FINDING_PLANT_FIELD_INVALID)
    expected = f"{mill_id}:{slug}"
    if plant_id != expected:
        raise SafRefusal(
            FINDING_PLANT_FIELD_INVALID,
            f"{where}.plant_id must be {expected!r}",
        )
    base_round = row.get("base_round")
    if not isinstance(base_round, int) or isinstance(base_round, bool) or base_round < 1:
        raise SafRefusal(FINDING_PLANT_FIELD_INVALID, f"{where}.base_round must be a positive int")
    fields = {
        key: _require_text(row.get(key), f"{where}.{key}", FINDING_PLANT_FIELD_MISSING)
        for key in PAIR_KEYS
    }
    flavor = fields["flavor"]
    if flavor not in FLAVORS:
        raise SafRefusal(FINDING_PLANT_FIELD_INVALID, f"{where}.flavor is not a saf flavor")
    return Plant(
        plant_id=plant_id,
        mill_id=mill_id,
        source=_require_text(row.get("source"), f"{where}.source", FINDING_PLANT_FIELD_MISSING),
        base_round=base_round,
        flavor=flavor,
        slug=slug,
        twin=fields["twin"],
        plant=fields["plant"],
        mutate=fields["mutate"],
        flag=fields["flag"],
        readonly=fields["readonly"],
        runbook=fields["runbook"],
        policy=fields["policy"],
        owner=fields["owner"],
        safe=fields["safe"],
        trigger=fields["trigger"],
        ticket=fields["ticket"],
        dest=fields["dest"],
        extra=fields["extra"],
    )


def _mill_from_row(row: Any, where: str) -> Mill:
    mill_id = _require_text(
        _field(row, "mill_id", str, where), f"{where}.mill_id", FINDING_CATALOG_FIELD_INVALID
    )
    if not MILL_ID_RE.fullmatch(mill_id):
        raise SafRefusal(FINDING_CATALOG_FIELD_INVALID, f"{where}.mill_id is not saf_rNNN")
    base_round = _field(row, "base_round", int, where)
    if isinstance(base_round, bool) or base_round < 1:
        raise SafRefusal(
            FINDING_CATALOG_FIELD_INVALID, f"{where}.base_round must be a positive int"
        )
    plant_count = _field(row, "plant_count", int, where)
    if isinstance(plant_count, bool) or plant_count < 1:
        raise SafRefusal(
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
        raise SafRefusal(FINDING_CATALOG_FILE_MISSING, f"{path} is unreadable: {exc}") from exc
    if not text.endswith("\n") or "\r" in text:
        raise SafRefusal(FINDING_CATALOG_FIELD_INVALID, f"{path.name} must be LF-framed jsonl")
    rows = []
    for index, line in enumerate(text.splitlines(), start=1):
        if not line:
            raise SafRefusal(FINDING_CATALOG_FIELD_INVALID, f"{path.name}:{index} is empty")
        try:
            rows.append(load_strict_json(line))
        except ValueError as exc:
            raise SafRefusal(
                FINDING_CATALOG_FIELD_INVALID, f"{path.name}:{index} is not strict JSON"
            ) from exc
    return tuple(rows)


def _registry_factory_ids() -> set[str]:
    return registry_factory_ids(
        repo_root,
        load_strict_json,
        lambda message: SafRefusal(FINDING_FACTORY_NOT_REGISTERED, message),
    )


def load_catalog(directory: Path | None = None) -> Catalog:
    """Load a catalog directory and refuse unless every pin holds."""

    return load_pinned_catalog(directory, sys.modules[__name__], _contract, SafRefusal)



def catalog_check(directory: Path | None = None) -> list[dict[str, str]]:
    """Load the catalog. An invalid catalog is a refusal, not a finding list."""

    loaded = load_catalog(directory)
    if loaded.plants:
        return []
    return [{"code": FINDING_CATALOG_FIELD_INVALID, "detail": "empty catalog"}]


bind_import_twin(__name__)
