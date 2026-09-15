#!/usr/bin/env python3
"""Pinned CSV plant catalog: load, pin, and AST-extract (never exec).

A catalog directory holds ``CATALOG.json`` (identity, factory, mill pins)
and ``plants.jsonl`` (one leftover leftover leftover pair per line). Load
verifies the plants digest and every required field before a plant is
trusted. Historical leftover mill scripts are read only as text through
:func:`plants_from_source`.
"""

from __future__ import annotations

import ast
import hashlib
import re
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ._contract import (
    CATALOG_FILENAME,
    CATALOG_FORMAT,
    CsvRefusal,
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
    MILL_PREFIX,
    PAIR_KEYS,
    PLANTS_FILENAME,
    QUOTA_PER_ROUND,
    RECORD_KIND,
    RECORD_PREFIX,
    bind_import_twin,
    load_strict_json,
    repo_root,
)

MILL_ID_RE = re.compile(r"^csv_r[0-9]+$")
SLUG_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
TICKET_RE = re.compile(r"^[A-Z0-9]+(?:-[A-Z0-9]+)+$")

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
    """One leftover leftover leftover ingest pair extracted from ``dict()``."""

    plant_id: str
    mill_id: str
    source: str
    base_round: int
    index: int
    slug: str
    fail: str
    mod: str
    drop: str
    keep: str
    naive: str
    stack: str
    drop_stack: str
    doc: str
    doc2: str
    domain: str
    ticket: str
    test_ok: str
    test_fail: str
    short: str
    dshort: str
    first_wrong: str

    def pair_fields(self) -> dict[str, str]:
        return {key: getattr(self, key) for key in PAIR_KEYS}


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
        raise CsvRefusal(FINDING_PLANT_NOT_FOUND, f"no plant {plant_id!r} in the catalog")

    def mill_plants(self, mill_id: str) -> tuple[Plant, ...]:
        found = tuple(item for item in self.plants if item.mill_id == mill_id)
        if not found:
            raise CsvRefusal(FINDING_MILL_NOT_FOUND, f"no mill {mill_id!r} in the catalog")
        return found


def default_catalog_dir() -> Path:
    return repo_root() / "config" / "csv"


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _const_eval(node: ast.AST) -> Any:
    """Literal values only. Never exec, compile, or eval."""

    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.List):
        return [_const_eval(item) for item in node.elts]
    if isinstance(node, ast.Tuple):
        return tuple(_const_eval(item) for item in node.elts)
    if isinstance(node, ast.Dict):
        if any(key is None for key in node.keys):
            raise CsvRefusal(FINDING_SOURCE_NOT_PARSEABLE, "plant source uses dict unpacking")
        return {_const_eval(key): _const_eval(value) for key, value in zip(node.keys, node.values)}
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        return -_const_eval(node.operand)
    raise CsvRefusal(
        FINDING_SOURCE_NOT_PARSEABLE,
        f"plant source is not a constant ({type(node).__name__})",
    )


def _assigned_name(node: ast.AST) -> tuple[str, ast.AST] | None:
    if isinstance(node, ast.Assign) and len(node.targets) == 1:
        target = node.targets[0]
        if isinstance(target, ast.Name):
            return target.id, node.value
    if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
        if node.value is not None:
            return node.target.id, node.value
    return None


def _dict_call(node: ast.AST, where: str) -> dict[str, Any]:
    if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Name):
        raise CsvRefusal(FINDING_SOURCE_NOT_PARSEABLE, f"{where} is not a dict() call")
    if node.func.id != "dict":
        raise CsvRefusal(FINDING_SOURCE_NOT_PARSEABLE, f"{where} is not a dict() call")
    if node.args or any(keyword.arg is None for keyword in node.keywords):
        raise CsvRefusal(FINDING_SOURCE_NOT_PARSEABLE, f"{where} must be keyword-only dict()")
    mapped: dict[str, Any] = {}
    for keyword in node.keywords:
        mapped[keyword.arg] = _const_eval(keyword.value)
    return mapped


def plants_from_source(
    text: str,
    *,
    mill_id: str,
    source: str,
    base_round: int | None = None,
) -> tuple[dict[str, Any], ...]:
    """AST-extract ``PAIRS = [dict(...), ...]``. Never exec."""

    try:
        tree = ast.parse(text)
    except SyntaxError as exc:
        raise CsvRefusal(
            FINDING_SOURCE_NOT_PARSEABLE, f"{source} does not parse: {exc}"
        ) from exc
    raw_pairs: ast.AST | None = None
    inferred_base: Any = None
    factory: Any = None
    prefix: Any = None
    for node in tree.body:
        assigned = _assigned_name(node)
        if assigned is None:
            continue
        name, value = assigned
        if name == "PAIRS":
            raw_pairs = value
        elif name == "CATALOG_FIRST":
            inferred_base = _const_eval(value)
        elif name in {"FAC", "FACTORY"}:
            factory = _const_eval(value)
        elif name == "PREFIX":
            prefix = _const_eval(value)
    if factory is not None and factory != FACTORY:
        raise CsvRefusal(
            FINDING_SOURCE_NOT_PARSEABLE,
            f"{source} FACTORY {factory!r} is not {FACTORY}",
        )
    if prefix is not None and prefix != RECORD_PREFIX:
        raise CsvRefusal(
            FINDING_SOURCE_NOT_PARSEABLE,
            f"{source} PREFIX {prefix!r} is not {RECORD_PREFIX}",
        )
    if not isinstance(raw_pairs, ast.List) or not raw_pairs.elts:
        raise CsvRefusal(FINDING_SOURCE_NOT_PARSEABLE, f"{source} has no PAIRS list")
    if not MILL_ID_RE.fullmatch(mill_id):
        raise CsvRefusal(FINDING_PLANT_FIELD_INVALID, f"mill_id {mill_id!r} is not csv_rNNN")
    base = inferred_base if base_round is None else base_round
    if base is None:
        base = int(mill_id[len("csv_r") :])
    if not isinstance(base, int) or isinstance(base, bool) or base < 1:
        raise CsvRefusal(
            FINDING_PLANT_FIELD_INVALID,
            f"{source} CATALOG_FIRST must be a positive int",
        )
    rows = []
    seen: set[str] = set()
    seen_fail: set[str] = set()
    seen_ticket: set[str] = set()
    for index, item in enumerate(raw_pairs.elts):
        mapping = _dict_call(item, f"{source} PAIRS[{index}]")
        missing = [key for key in PAIR_KEYS if key not in mapping]
        if missing:
            raise CsvRefusal(
                FINDING_SOURCE_NOT_PARSEABLE,
                f"{source} PAIRS[{index}] missing {missing[0]}",
            )
        extra = [key for key in mapping if key not in PAIR_KEYS]
        if extra:
            raise CsvRefusal(
                FINDING_SOURCE_NOT_PARSEABLE,
                f"{source} PAIRS[{index}] has extra {extra[0]}",
            )
        fields: dict[str, str] = {}
        for key in PAIR_KEYS:
            value = mapping[key]
            if not isinstance(value, str) or not value.strip() or value != value.strip():
                raise CsvRefusal(
                    FINDING_SOURCE_NOT_PARSEABLE,
                    f"{source} PAIRS[{index}].{key} must be a stripped string",
                )
            fields[key] = value
        slug = fields["slug"]
        plant_id = f"{mill_id}:{slug}"
        if plant_id in seen:
            raise CsvRefusal(FINDING_PLANT_DUPLICATE, f"{source} duplicate {plant_id}")
        if fields["fail"] in seen_fail:
            raise CsvRefusal(FINDING_PLANT_DUPLICATE, f"{source} duplicate fail {fields['fail']}")
        if fields["ticket"] in seen_ticket:
            raise CsvRefusal(
                FINDING_PLANT_DUPLICATE, f"{source} duplicate ticket {fields['ticket']}"
            )
        seen.add(plant_id)
        seen_fail.add(fields["fail"])
        seen_ticket.add(fields["ticket"])
        rows.append(
            {
                "plant_id": plant_id,
                "mill_id": mill_id,
                "source": source,
                "base_round": base,
                "index": index,
                **fields,
            }
        )
    return tuple(rows)


def _field(mapping: Any, key: str, kinds: type | tuple[type, ...], where: str) -> Any:
    if not isinstance(mapping, dict):
        raise CsvRefusal(FINDING_CATALOG_FIELD_INVALID, f"{where} must be an object")
    if key not in mapping:
        raise CsvRefusal(FINDING_CATALOG_FIELD_MISSING, f"{where}.{key} is missing")
    value = mapping[key]
    if isinstance(value, bool) and kinds is not bool:
        raise CsvRefusal(FINDING_CATALOG_FIELD_INVALID, f"{where}.{key} has the wrong type")
    if not isinstance(value, kinds):
        raise CsvRefusal(FINDING_CATALOG_FIELD_INVALID, f"{where}.{key} has the wrong type")
    return value


def _require_text(value: Any, where: str, code: str) -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise CsvRefusal(code, f"{where} must be a non-empty stripped string")
    return value


def _plant_from_row(row: Any, where: str) -> Plant:
    if not isinstance(row, dict):
        raise CsvRefusal(FINDING_PLANT_FIELD_INVALID, f"{where} must be an object")
    mill_id = _require_text(row.get("mill_id"), f"{where}.mill_id", FINDING_PLANT_FIELD_INVALID)
    slug = _require_text(row.get("slug"), f"{where}.slug", FINDING_PLANT_FIELD_INVALID)
    if not MILL_ID_RE.fullmatch(mill_id):
        raise CsvRefusal(FINDING_PLANT_FIELD_INVALID, f"{where}.mill_id is not csv_rNNN")
    if not SLUG_RE.fullmatch(slug):
        raise CsvRefusal(FINDING_PLANT_FIELD_INVALID, f"{where}.slug is not a plant slug")
    plant_id = _require_text(row.get("plant_id"), f"{where}.plant_id", FINDING_PLANT_FIELD_INVALID)
    expected = f"{mill_id}:{slug}"
    if plant_id != expected:
        raise CsvRefusal(FINDING_PLANT_FIELD_INVALID, f"{where}.plant_id must be {expected!r}")
    base_round = row.get("base_round")
    if not isinstance(base_round, int) or isinstance(base_round, bool) or base_round < 1:
        raise CsvRefusal(FINDING_PLANT_FIELD_INVALID, f"{where}.base_round must be a positive int")
    index = row.get("index")
    if not isinstance(index, int) or isinstance(index, bool) or index < 0:
        raise CsvRefusal(FINDING_PLANT_FIELD_INVALID, f"{where}.index must be a non-negative int")
    fields = {
        key: _require_text(row.get(key), f"{where}.{key}", FINDING_PLANT_FIELD_MISSING)
        for key in PAIR_KEYS
    }
    if not SLUG_RE.fullmatch(fields["fail"]):
        raise CsvRefusal(FINDING_PLANT_FIELD_INVALID, f"{where}.fail is not a plant slug")
    if not TICKET_RE.fullmatch(fields["ticket"]):
        raise CsvRefusal(FINDING_PLANT_FIELD_INVALID, f"{where}.ticket is not a ticket id")
    return Plant(
        plant_id=plant_id,
        mill_id=mill_id,
        source=_require_text(row.get("source"), f"{where}.source", FINDING_PLANT_FIELD_MISSING),
        base_round=base_round,
        index=index,
        **fields,
    )


def _mill_from_row(row: Any, where: str) -> Mill:
    mill_id = _require_text(
        _field(row, "mill_id", str, where), f"{where}.mill_id", FINDING_CATALOG_FIELD_INVALID
    )
    if not MILL_ID_RE.fullmatch(mill_id):
        raise CsvRefusal(FINDING_CATALOG_FIELD_INVALID, f"{where}.mill_id is not csv_rNNN")
    base_round = _field(row, "base_round", int, where)
    if isinstance(base_round, bool) or base_round < 1:
        raise CsvRefusal(
            FINDING_CATALOG_FIELD_INVALID, f"{where}.base_round must be a positive int"
        )
    plant_count = _field(row, "plant_count", int, where)
    if isinstance(plant_count, bool) or plant_count < 1:
        raise CsvRefusal(
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
        raise CsvRefusal(FINDING_CATALOG_FILE_MISSING, f"{path} is unreadable: {exc}") from exc
    if not text.endswith("\n") or "\r" in text:
        raise CsvRefusal(FINDING_CATALOG_FIELD_INVALID, f"{path.name} must be LF-framed jsonl")
    rows = []
    for index, line in enumerate(text.splitlines(), start=1):
        if not line:
            raise CsvRefusal(FINDING_CATALOG_FIELD_INVALID, f"{path.name}:{index} is empty")
        try:
            rows.append(load_strict_json(line))
        except ValueError as exc:
            raise CsvRefusal(
                FINDING_CATALOG_FIELD_INVALID, f"{path.name}:{index} is not strict JSON"
            ) from exc
    return tuple(rows)


def _registry_factory_ids() -> set[str]:
    path = repo_root() / "config" / "FACTORY-REGISTRY.json"
    try:
        payload = load_strict_json(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise CsvRefusal(
            FINDING_FACTORY_NOT_REGISTERED, f"factory registry is unreadable: {exc}"
        ) from exc
    factories = payload.get("factories") if isinstance(payload, dict) else None
    if not isinstance(factories, list):
        raise CsvRefusal(FINDING_FACTORY_NOT_REGISTERED, "factory registry factories is not a list")
    return {
        row.get("path_id")
        for row in factories
        if isinstance(row, dict) and isinstance(row.get("path_id"), str)
    }


def load_catalog(directory: Path | None = None) -> Catalog:
    """Load a catalog directory and refuse unless every pin holds."""

    catalog_dir = Path(default_catalog_dir() if directory is None else directory)
    meta_path = catalog_dir / CATALOG_FILENAME
    plants_path = catalog_dir / PLANTS_FILENAME
    try:
        meta_text = meta_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise CsvRefusal(FINDING_CATALOG_FILE_MISSING, f"{meta_path} is missing") from exc
    try:
        meta = load_strict_json(meta_text)
    except ValueError as exc:
        raise CsvRefusal(
            FINDING_CATALOG_FIELD_INVALID, f"{CATALOG_FILENAME} is not strict JSON"
        ) from exc
    catalog_id = _require_text(
        _field(meta, "catalog_id", str, CATALOG_FILENAME),
        f"{CATALOG_FILENAME}.catalog_id",
        FINDING_CATALOG_FIELD_INVALID,
    )
    fmt = _field(meta, "format", str, CATALOG_FILENAME)
    if fmt != CATALOG_FORMAT:
        raise CsvRefusal(
            FINDING_CATALOG_FIELD_INVALID,
            f"{CATALOG_FILENAME}.format must be {CATALOG_FORMAT}",
        )
    factory = _field(meta, "factory", str, CATALOG_FILENAME)
    if factory != FACTORY:
        raise CsvRefusal(
            FINDING_CATALOG_FIELD_INVALID, f"{CATALOG_FILENAME}.factory must be {FACTORY}"
        )
    prefix = _field(meta, "mill_prefix", str, CATALOG_FILENAME)
    if prefix != MILL_PREFIX:
        raise CsvRefusal(
            FINDING_CATALOG_FIELD_INVALID,
            f"{CATALOG_FILENAME}.mill_prefix must be {MILL_PREFIX}",
        )
    kind = _field(meta, "record_kind", str, CATALOG_FILENAME)
    if kind != RECORD_KIND:
        raise CsvRefusal(
            FINDING_CATALOG_FIELD_INVALID,
            f"{CATALOG_FILENAME}.record_kind must be {RECORD_KIND}",
        )
    record_prefix = _field(meta, "record_prefix", str, CATALOG_FILENAME)
    if record_prefix != RECORD_PREFIX:
        raise CsvRefusal(
            FINDING_CATALOG_FIELD_INVALID,
            f"{CATALOG_FILENAME}.record_prefix must be {RECORD_PREFIX}",
        )
    quota = _field(meta, "quota_per_round", int, CATALOG_FILENAME)
    if isinstance(quota, bool) or quota != QUOTA_PER_ROUND:
        raise CsvRefusal(
            FINDING_CATALOG_FIELD_INVALID,
            f"{CATALOG_FILENAME}.quota_per_round must be {QUOTA_PER_ROUND}",
        )
    plant_count = _field(meta, "plant_count", int, CATALOG_FILENAME)
    plants_sha256 = _field(meta, "plants_sha256", str, CATALOG_FILENAME)
    mill_rows = _field(meta, "mills", list, CATALOG_FILENAME)
    mills = tuple(
        _mill_from_row(row, f"{CATALOG_FILENAME}.mills[{i}]") for i, row in enumerate(mill_rows)
    )
    try:
        plants_bytes = plants_path.read_bytes()
    except OSError as exc:
        raise CsvRefusal(FINDING_CATALOG_FILE_MISSING, f"{plants_path} is missing") from exc
    digest = sha256_bytes(plants_bytes)
    if digest != plants_sha256:
        raise CsvRefusal(
            FINDING_PLANTS_SHA_MISMATCH,
            f"{PLANTS_FILENAME} digest {digest} != catalog pin {plants_sha256}",
        )
    if factory not in _registry_factory_ids():
        raise CsvRefusal(FINDING_FACTORY_NOT_REGISTERED, f"{factory} is not a registry path_id")
    rows = _read_jsonl(plants_path)
    if len(rows) != plant_count:
        raise CsvRefusal(
            FINDING_CATALOG_FIELD_INVALID,
            f"{CATALOG_FILENAME}.plant_count is {plant_count}, file has {len(rows)}",
        )
    plants = tuple(
        _plant_from_row(row, f"{PLANTS_FILENAME}:{i}") for i, row in enumerate(rows, start=1)
    )
    seen: set[str] = set()
    seen_slugs: set[str] = set()
    seen_fail: set[str] = set()
    seen_ticket: set[str] = set()
    for plant in plants:
        if plant.plant_id in seen:
            raise CsvRefusal(FINDING_PLANT_DUPLICATE, f"duplicate plant_id {plant.plant_id}")
        seen.add(plant.plant_id)
        if plant.slug in seen_slugs:
            raise CsvRefusal(FINDING_PLANT_DUPLICATE, f"duplicate slug {plant.slug}")
        seen_slugs.add(plant.slug)
        if plant.fail in seen_fail:
            raise CsvRefusal(FINDING_PLANT_DUPLICATE, f"duplicate fail {plant.fail}")
        seen_fail.add(plant.fail)
        if plant.ticket in seen_ticket:
            raise CsvRefusal(FINDING_PLANT_DUPLICATE, f"duplicate ticket {plant.ticket}")
        seen_ticket.add(plant.ticket)
    by_mill: dict[str, int] = {}
    for plant in plants:
        by_mill[plant.mill_id] = by_mill.get(plant.mill_id, 0) + 1
    mill_ids = {mill.mill_id for mill in mills}
    if mill_ids != set(by_mill):
        raise CsvRefusal(
            FINDING_CATALOG_FIELD_INVALID, "catalog mills do not match plant mill_id values"
        )
    for mill in mills:
        if by_mill[mill.mill_id] != mill.plant_count:
            raise CsvRefusal(
                FINDING_CATALOG_FIELD_INVALID,
                f"{mill.mill_id} plant_count {mill.plant_count} != {by_mill[mill.mill_id]}",
            )
        for plant in plants:
            if plant.mill_id == mill.mill_id and plant.base_round != mill.base_round:
                raise CsvRefusal(
                    FINDING_CATALOG_FIELD_INVALID,
                    f"{plant.plant_id} base_round != mill base_round",
                )
    return Catalog(
        catalog_id=catalog_id,
        directory=catalog_dir,
        factory=factory,
        plants_sha256=digest,
        plants=plants,
        mills=mills,
        meta=meta,
    )


def catalog_check(directory: Path | None = None) -> list[dict[str, str]]:
    """Load the catalog. An invalid catalog is a refusal, not a finding list."""

    loaded = load_catalog(directory)
    if loaded.plants:
        return []
    return [{"code": FINDING_CATALOG_FIELD_INVALID, "detail": "empty catalog"}]


bind_import_twin(__name__)
