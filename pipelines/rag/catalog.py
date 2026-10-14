#!/usr/bin/env python3
"""Pinned RAG plant catalog: load, pin, and AST-extract (never exec).

A catalog directory holds ``CATALOG.json`` (identity, factory, mill pins)
and ``plants.jsonl`` (one leftover-filter pair per line). Load verifies the
plants digest and every required field before a plant is trusted. Historical
leftover mill scripts are read only as text through :func:`plants_from_source`.
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
    FACTORY,
    FINDING_CATALOG_FIELD_INVALID,
    FINDING_CATALOG_FIELD_MISSING,
    FINDING_CATALOG_FILE_MISSING,
    FINDING_FACTORY_NOT_REGISTERED,
    FINDING_MILL_NOT_FOUND,
    FINDING_PLANT_DUPLICATE_ID,
    FINDING_PLANT_FIELD_INVALID,
    FINDING_PLANT_FIELD_MISSING,
    FINDING_PLANT_NOT_FOUND,
    FINDING_SOURCE_NOT_PARSEABLE,
    RagRefusal,
    bind_import_twin,
    load_strict_json,
    repo_root,
)

CATALOG_FILENAME = _contract.CATALOG_FILENAME
CATALOG_FORMAT = _contract.CATALOG_FORMAT
FINDING_CATALOG_SHA256_MISMATCH = _contract.FINDING_CATALOG_SHA256_MISMATCH
MILL_PREFIX = _contract.MILL_PREFIX
PLANTS_FILENAME = _contract.PLANTS_FILENAME
QUOTA_PER_ROUND = _contract.QUOTA_PER_ROUND
RECORD_KIND = _contract.RECORD_KIND

if (__package__ or "").startswith("pipelines."):
    from ..catalog_cli.source_const import (
        load_pinned_catalog,
        plant_const_eval,
        registry_factory_ids,
        require_positive_base,
    )
else:
    from catalog_cli.source_const import (
        load_pinned_catalog,
        plant_const_eval,
        registry_factory_ids,
        require_positive_base,
    )

MILL_ID_RE = re.compile(r"^rag_r[0-9]+$")
SLUG_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
TOKEN_RE = re.compile(r"^[A-Za-z][A-Za-z0-9]*$")

__all__ = [
    "Catalog",
    "Mill",
    "Plant",
    "catalog_check",
    "default_catalog_dir",
    "expand_pair",
    "load_catalog",
    "plants_from_source",
    "sha256_bytes",
]


@dataclass(frozen=True)
class Plant:
    """One leftover leftover leftover retrieval pair extracted from ``P()``."""

    plant_id: str
    mill_id: str
    source: str
    base_round: int
    slug: str
    eng: str
    leftover: str
    ticket_ok: str
    ticket_fail: str


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
        raise RagRefusal(FINDING_PLANT_NOT_FOUND, f"no plant {plant_id!r} in the catalog")

    def mill_plants(self, mill_id: str) -> tuple[Plant, ...]:
        found = tuple(item for item in self.plants if item.mill_id == mill_id)
        if not found:
            raise RagRefusal(FINDING_MILL_NOT_FOUND, f"no mill {mill_id!r} in the catalog")
        return found

    def plant_for_round(self, rnd: int) -> Plant:
        if not self.plants:
            raise RagRefusal(FINDING_PLANT_NOT_FOUND, "catalog has no plants")
        base = self.mills[0].base_round
        index = (rnd - base) % len(self.plants)
        return self.plants[index]


def default_catalog_dir() -> Path:
    return repo_root() / "config" / "rag"


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def expand_pair(
    eng: str,
    leftover: str,
    ticket_ok: str,
    ticket_fail: str,
) -> tuple[dict[str, str], dict[str, str]]:
    """Replay the legacy ``P()`` field template without executing mill source."""

    ok = {
        "slug": f"{eng}-leftover-{leftover}-filter-lll",
        "domain": f"{eng}-leftover-leftover-leftover-{leftover}-filter",
        "seed": f"{eng}-leftover-{leftover}-filter-lll",
        "root": f"{eng}-lll",
        "f1": f"{eng}-lll/retrieve.py",
        "f2": f"{eng}-lll/index.yml",
        "token": f"TESTONLY_rag_{eng[:4]}_{leftover[:4]}_lll_n0t_live",
        "wrong": "drop leftover leftover leftover filter to raise recall",
        "right": f"bind leftover leftover leftover {leftover} filter on {eng}",
        "ticket": ticket_ok,
        "leftover": leftover,
        "eng": eng,
    }
    fail = {
        "slug": f"{eng}-drop-{leftover}-handoff-lll",
        "domain": f"{eng}-drop-leftover-leftover-leftover-{leftover}",
        "seed": f"{eng}-drop-{leftover}-handoff-lll",
        "root": f"{eng}-lll",
        "f1": f"{eng}-lll/retrieve.py",
        "f2": f"{eng}-lll/cluster.yml",
        "token": f"TESTONLY_rag_{eng[:4]}_drop_{leftover[:4]}_lll_n0t_live",
        "wrong": f"unlink leftover leftover leftover {leftover}",
        "right": f"platform leftover leftover leftover {leftover} index",
        "ticket": ticket_fail,
        "platform": f"search-plat-{eng}",
        "leftover": leftover,
        "eng": eng,
    }
    return ok, fail


def _const_eval(node: ast.AST) -> Any:
    """Literal values only. Refuses calls, names, and starred dicts."""

    return plant_const_eval(node, RagRefusal, FINDING_SOURCE_NOT_PARSEABLE)


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


def _p_call_args(node: ast.AST) -> tuple[str, str, str, str] | None:
    if not isinstance(node, ast.Call):
        return None
    func = node.func
    if not isinstance(func, ast.Name) or func.id != "P":
        return None
    if node.keywords or any(isinstance(arg, ast.Starred) for arg in node.args):
        raise RagRefusal(FINDING_SOURCE_NOT_PARSEABLE, "P() must be four positional literals")
    if len(node.args) != 4:
        raise RagRefusal(FINDING_SOURCE_NOT_PARSEABLE, "P() must have four arguments")
    values = [_const_eval(arg) for arg in node.args]
    if any(not isinstance(item, str) or not item for item in values):
        raise RagRefusal(FINDING_SOURCE_NOT_PARSEABLE, "P() arguments must be non-empty strings")
    return values[0], values[1], values[2], values[3]


def _rows_from_pairs(
    elts: list[ast.AST],
    mill_id: str,
    source: str,
    base: int,
) -> tuple[dict[str, Any], ...]:
    rows = []
    seen: set[str] = set()
    for index, item in enumerate(elts):
        args = _p_call_args(item)
        if args is None:
            raise RagRefusal(
                FINDING_SOURCE_NOT_PARSEABLE,
                f"{source} PAIRS[{index}] is not a P() literal call",
            )
        eng, leftover, ticket_ok, ticket_fail = args
        slug = f"{eng}-{leftover}"
        plant_id = f"{mill_id}:{slug}"
        if plant_id in seen:
            raise RagRefusal(FINDING_PLANT_DUPLICATE_ID, f"{source} duplicate {plant_id}")
        seen.add(plant_id)
        rows.append(
            {
                "plant_id": plant_id,
                "mill_id": mill_id,
                "source": source,
                "base_round": base,
                "slug": slug,
                "eng": eng,
                "leftover": leftover,
                "ticket_ok": ticket_ok,
                "ticket_fail": ticket_fail,
            }
        )
    return tuple(rows)


def plants_from_source(
    text: str,
    *,
    mill_id: str,
    source: str,
    base_round: int | None = None,
) -> tuple[dict[str, Any], ...]:
    """AST-extract ``PAIRS = [P(...), ...]`` from leftover-mill text. Never exec."""

    try:
        tree = ast.parse(text)
    except SyntaxError as exc:
        raise RagRefusal(
            FINDING_SOURCE_NOT_PARSEABLE, f"{source} does not parse: {exc}"
        ) from exc
    raw_pairs: ast.AST | None = None
    inferred_base: Any = None
    factory: Any = None
    for node in tree.body:
        assigned = _assigned_name(node)
        if assigned is None:
            continue
        name, value = assigned
        if name == "PAIRS":
            raw_pairs = value
        elif name == "CATALOG_FIRST":
            inferred_base = _const_eval(value)
        elif name == "FACTORY":
            factory = _const_eval(value)
    if factory is not None and factory != FACTORY:
        raise RagRefusal(
            FINDING_SOURCE_NOT_PARSEABLE,
            f"{source} FACTORY {factory!r} is not {FACTORY}",
        )
    if not isinstance(raw_pairs, ast.List) or not raw_pairs.elts:
        raise RagRefusal(FINDING_SOURCE_NOT_PARSEABLE, f"{source} has no PAIRS list")
    if not MILL_ID_RE.fullmatch(mill_id):
        raise RagRefusal(FINDING_PLANT_FIELD_INVALID, f"mill_id {mill_id!r} is not rag_rNNN")
    base = require_positive_base(
        inferred_base if base_round is None else base_round,
        mill_id,
        "rag_r",
        lambda: RagRefusal(
            FINDING_PLANT_FIELD_INVALID,
            f"{source} CATALOG_FIRST must be a positive int",
        ),
    )
    return _rows_from_pairs(raw_pairs.elts, mill_id, source, base)


def _field(mapping: Any, key: str, kinds: type | tuple[type, ...], where: str) -> Any:
    if not isinstance(mapping, dict):
        raise RagRefusal(FINDING_CATALOG_FIELD_INVALID, f"{where} must be an object")
    if key not in mapping:
        raise RagRefusal(FINDING_CATALOG_FIELD_MISSING, f"{where}.{key} is missing")
    value = mapping[key]
    if isinstance(value, bool) and kinds is not bool:
        raise RagRefusal(FINDING_CATALOG_FIELD_INVALID, f"{where}.{key} has the wrong type")
    if not isinstance(value, kinds):
        raise RagRefusal(FINDING_CATALOG_FIELD_INVALID, f"{where}.{key} has the wrong type")
    return value


def _require_text(value: Any, where: str, code: str) -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise RagRefusal(code, f"{where} must be a non-empty stripped string")
    return value


def _plant_from_row(row: Any, where: str) -> Plant:
    if not isinstance(row, dict):
        raise RagRefusal(FINDING_PLANT_FIELD_INVALID, f"{where} must be an object")
    mill_id = _require_text(row.get("mill_id"), f"{where}.mill_id", FINDING_PLANT_FIELD_INVALID)
    slug = _require_text(row.get("slug"), f"{where}.slug", FINDING_PLANT_FIELD_INVALID)
    if not MILL_ID_RE.fullmatch(mill_id):
        raise RagRefusal(FINDING_PLANT_FIELD_INVALID, f"{where}.mill_id is not rag_rNNN")
    if not SLUG_RE.fullmatch(slug):
        raise RagRefusal(FINDING_PLANT_FIELD_INVALID, f"{where}.slug is not a plant slug")
    plant_id = _require_text(row.get("plant_id"), f"{where}.plant_id", FINDING_PLANT_FIELD_INVALID)
    expected = f"{mill_id}:{slug}"
    if plant_id != expected:
        raise RagRefusal(FINDING_PLANT_FIELD_INVALID, f"{where}.plant_id must be {expected!r}")
    base_round = row.get("base_round")
    if not isinstance(base_round, int) or isinstance(base_round, bool) or base_round < 1:
        raise RagRefusal(FINDING_PLANT_FIELD_INVALID, f"{where}.base_round must be a positive int")
    eng = _require_text(row.get("eng"), f"{where}.eng", FINDING_PLANT_FIELD_MISSING)
    leftover = _require_text(row.get("leftover"), f"{where}.leftover", FINDING_PLANT_FIELD_MISSING)
    if not TOKEN_RE.fullmatch(eng):
        raise RagRefusal(FINDING_PLANT_FIELD_INVALID, f"{where}.eng is not a token")
    if not TOKEN_RE.fullmatch(leftover):
        raise RagRefusal(FINDING_PLANT_FIELD_INVALID, f"{where}.leftover is not a token")
    if slug != f"{eng}-{leftover}":
        raise RagRefusal(
            FINDING_PLANT_FIELD_INVALID,
            f"{where}.slug must be {eng!s}-{leftover}",
        )
    return Plant(
        plant_id=plant_id,
        mill_id=mill_id,
        source=_require_text(row.get("source"), f"{where}.source", FINDING_PLANT_FIELD_MISSING),
        base_round=base_round,
        slug=slug,
        eng=eng,
        leftover=leftover,
        ticket_ok=_require_text(
            row.get("ticket_ok"), f"{where}.ticket_ok", FINDING_PLANT_FIELD_MISSING
        ),
        ticket_fail=_require_text(
            row.get("ticket_fail"), f"{where}.ticket_fail", FINDING_PLANT_FIELD_MISSING
        ),
    )


def _mill_from_row(row: Any, where: str) -> Mill:
    mill_id = _require_text(
        _field(row, "mill_id", str, where), f"{where}.mill_id", FINDING_CATALOG_FIELD_INVALID
    )
    if not MILL_ID_RE.fullmatch(mill_id):
        raise RagRefusal(FINDING_CATALOG_FIELD_INVALID, f"{where}.mill_id is not rag_rNNN")
    base_round = _field(row, "base_round", int, where)
    if isinstance(base_round, bool) or base_round < 1:
        raise RagRefusal(
            FINDING_CATALOG_FIELD_INVALID, f"{where}.base_round must be a positive int"
        )
    plant_count = _field(row, "plant_count", int, where)
    if isinstance(plant_count, bool) or plant_count < 1:
        raise RagRefusal(
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
        raise RagRefusal(FINDING_CATALOG_FILE_MISSING, f"{path} is unreadable: {exc}") from exc
    if not text.endswith("\n") or "\r" in text:
        raise RagRefusal(FINDING_CATALOG_FIELD_INVALID, f"{path.name} must be LF-framed jsonl")
    rows = []
    for index, line in enumerate(text.splitlines(), start=1):
        if not line:
            raise RagRefusal(FINDING_CATALOG_FIELD_INVALID, f"{path.name}:{index} is empty")
        try:
            rows.append(load_strict_json(line))
        except ValueError as exc:
            raise RagRefusal(
                FINDING_CATALOG_FIELD_INVALID, f"{path.name}:{index} is not strict JSON"
            ) from exc
    return tuple(rows)


def _registry_factory_ids() -> set[str]:
    return registry_factory_ids(
        repo_root,
        load_strict_json,
        lambda message: RagRefusal(FINDING_FACTORY_NOT_REGISTERED, message),
    )


def load_catalog(directory: Path | None = None) -> Catalog:
    """Load a catalog directory and refuse unless every pin holds."""

    return load_pinned_catalog(directory, sys.modules[__name__], _contract, RagRefusal)



def catalog_check(directory: Path | None = None) -> list[dict[str, str]]:
    """Load the catalog. An invalid catalog is a refusal, not a finding list."""

    loaded = load_catalog(directory)
    if loaded.plants:
        return []
    return [{"code": FINDING_CATALOG_FIELD_INVALID, "detail": "empty catalog"}]


bind_import_twin(__name__)
