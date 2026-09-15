#!/usr/bin/env python3
"""Pinned GQL plant catalog: load, pin, and AST-extract (never exec).

A catalog directory holds ``CATALOG.json`` (identity, factory, mill pins)
and ``plants.jsonl`` (one plant per line). Load verifies the plants digest
and every required field before a plant is trusted. Historical mill scripts
are read only as text through :func:`plants_from_source`.
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
    FACTORY,
    FINDING_CATALOG_FIELD_INVALID,
    FINDING_CATALOG_FIELD_MISSING,
    FINDING_CATALOG_FILE_MISSING,
    FINDING_CATALOG_SHA256_MISMATCH,
    FINDING_FACTORY_NOT_REGISTERED,
    FINDING_MILL_NOT_FOUND,
    FINDING_PLANT_DUPLICATE_ID,
    FINDING_PLANT_FIELD_INVALID,
    FINDING_PLANT_FIELD_MISSING,
    FINDING_PLANT_NOT_FOUND,
    FINDING_SOURCE_NOT_PARSEABLE,
    GqlRefusal,
    MILL_PREFIX,
    PLANTS_FILENAME,
    QUOTA_PER_ROUND,
    RECORD_KIND,
    SHAPE_PAIR,
    SHAPE_SURFACE,
    bind_import_twin,
    load_strict_json,
    repo_root,
)

OK_KEYS = (
    "slug",
    "surface",
    "avoid",
    "disable",
    "plan",
    "fix",
    "src",
    "test",
    "extra",
    "cfg",
    "bug",
    "slo",
    "residual",
    "src_obs",
    "test_obs",
    "fail_obs",
    "rg_obs",
    "wrong_edit_old",
    "wrong_edit_new",
    "fix_contents",
    "suite",
)
BAD_KEYS = (
    "slug",
    "surface",
    "avoid",
    "disable",
    "plan",
    "fix",
    "src",
    "test",
    "extra",
    "cfg",
    "bug",
    "slo",
    "residual",
    "src_obs",
    "test_obs",
    "fail_obs",
    "rg_obs",
    "wrong_edit_old",
    "wrong_edit_new",
    "fix_contents",
    "xfail_note",
)
SURFACE_ROW_KEYS = (
    "idx",
    "sid",
    "fid",
    "product",
    "mech",
    "vs",
    "old",
    "new",
    "prod",
    "coverage",
)
MILL_ID_RE = re.compile(r"^gql_r[0-9]+$")
SLUG_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
LITERAL_NAMES = ("PAIRS", "EXTRA", "PLANTS", "CATALOG")

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
    """One leftover-execution plant: pair (ok/bad sides) or surface tuple."""

    plant_id: str
    mill_id: str
    source: str
    base_round: int
    shape: str
    slug: str
    plant: str
    coverage: int
    payload: Mapping[str, Any]


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
        raise GqlRefusal(FINDING_PLANT_NOT_FOUND, f"no plant {plant_id!r} in the catalog")

    def mill_plants(self, mill_id: str) -> tuple[Plant, ...]:
        found = tuple(item for item in self.plants if item.mill_id == mill_id)
        if not found:
            raise GqlRefusal(FINDING_MILL_NOT_FOUND, f"no mill {mill_id!r} in the catalog")
        return found


def default_catalog_dir() -> Path:
    return repo_root() / "config" / "gql"


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _const_eval(node: ast.AST) -> Any:
    """Literal values only. ``S(**kwargs)`` is a dict; other calls refuse."""

    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.List):
        return [_const_eval(item) for item in node.elts]
    if isinstance(node, ast.Tuple):
        return tuple(_const_eval(item) for item in node.elts)
    if isinstance(node, ast.Dict):
        if any(key is None for key in node.keys):
            raise GqlRefusal(FINDING_SOURCE_NOT_PARSEABLE, "plant source uses dict unpacking")
        return {_const_eval(key): _const_eval(value) for key, value in zip(node.keys, node.values)}
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        return -_const_eval(node.operand)
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
        if node.func.id == "S" and not node.args:
            return {kw.arg: _const_eval(kw.value) for kw in node.keywords}
    raise GqlRefusal(
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


def _require_text(value: Any, where: str, code: str, *, strip: bool = True) -> str:
    if not isinstance(value, str) or not value.strip():
        raise GqlRefusal(code, f"{where} must be a non-empty string")
    if strip and value != value.strip():
        raise GqlRefusal(code, f"{where} must be a stripped string")
    return value


def _require_int(value: Any, where: str, code: str, minimum: int = 0) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < minimum:
        raise GqlRefusal(code, f"{where} must be an int >= {minimum}")
    return value


def _side_dict(raw: Any, keys: tuple[str, ...], where: str) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raise GqlRefusal(FINDING_SOURCE_NOT_PARSEABLE, f"{where} is not an object")
    missing = [key for key in keys if key not in raw]
    if missing:
        raise GqlRefusal(FINDING_PLANT_FIELD_MISSING, f"{where} missing {missing[0]}")
    out: dict[str, Any] = {}
    for key in keys:
        value = raw[key]
        if key == "suite":
            out[key] = _require_int(value, f"{where}.{key}", FINDING_PLANT_FIELD_INVALID, 1)
            continue
        out[key] = _require_text(
            value, f"{where}.{key}", FINDING_PLANT_FIELD_MISSING, strip=False
        )
    return out


def _pair_from_raw(
    raw: Any, *, mill_id: str, source: str, base_round: int, index: int
) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raise GqlRefusal(FINDING_SOURCE_NOT_PARSEABLE, f"{source}[{index}] is not an object")
    plant = _require_text(raw.get("plant"), f"{source}[{index}].plant", FINDING_PLANT_FIELD_MISSING)
    return {
        "bad": _side_dict(raw.get("bad"), BAD_KEYS, f"{source}[{index}].bad"),
        "base_round": base_round,
        "coverage": _require_int(
            raw.get("coverage"), f"{source}[{index}].coverage", FINDING_PLANT_FIELD_INVALID, 1
        ),
        "field": _require_text(
            raw.get("field"), f"{source}[{index}].field", FINDING_PLANT_FIELD_MISSING
        ),
        "mill_id": mill_id,
        "next": _require_text(
            raw.get("next"), f"{source}[{index}].next", FINDING_PLANT_FIELD_MISSING, strip=False
        ),
        "ok": _side_dict(raw.get("ok"), OK_KEYS, f"{source}[{index}].ok"),
        "plant": plant,
        "plant_id": f"{mill_id}:{plant}",
        "shape": SHAPE_PAIR,
        "slug": plant,
        "source": source,
        "window": _require_text(
            raw.get("window", "Distinct leftover execution."),
            f"{source}[{index}].window",
            FINDING_PLANT_FIELD_MISSING,
            strip=False,
        ),
    }


def _surface_from_raw(
    raw: Any, *, mill_id: str, source: str, base_round: int, index: int
) -> dict[str, Any]:
    if not isinstance(raw, tuple) or len(raw) != 9:
        raise GqlRefusal(FINDING_SOURCE_NOT_PARSEABLE, f"{source}[{index}] is not a 9-tuple")
    off, sid, fid, product, mech, vs, plant, old, new = raw
    if off != index:
        raise GqlRefusal(FINDING_SOURCE_NOT_PARSEABLE, f"{source}[{index}] idx {off} != {index}")
    sid_text = _require_text(sid, f"{source}[{index}].sid", FINDING_PLANT_FIELD_MISSING)
    return {
        "base_round": base_round,
        "coverage": 70 + (index % 17),
        "fid": _require_text(fid, f"{source}[{index}].fid", FINDING_PLANT_FIELD_MISSING),
        "idx": index,
        "mech": _require_text(mech, f"{source}[{index}].mech", FINDING_PLANT_FIELD_MISSING),
        "mill_id": mill_id,
        "new": _require_text(new, f"{source}[{index}].new", FINDING_PLANT_FIELD_MISSING),
        "old": _require_text(old, f"{source}[{index}].old", FINDING_PLANT_FIELD_MISSING),
        "plant": _require_text(plant, f"{source}[{index}].plant", FINDING_PLANT_FIELD_MISSING),
        "plant_id": f"{mill_id}:{sid_text}",
        "prod": sid_text.split("-", 1)[0],
        "product": _require_text(product, f"{source}[{index}].product", FINDING_PLANT_FIELD_MISSING),
        "shape": SHAPE_SURFACE,
        "sid": sid_text,
        "slug": sid_text,
        "source": source,
        "vs": _require_text(vs, f"{source}[{index}].vs", FINDING_PLANT_FIELD_MISSING),
    }


def plants_from_source(
    text: str,
    *,
    mill_id: str,
    source: str,
    base_round: int | None = None,
) -> tuple[dict[str, Any], ...]:
    """AST-extract PAIRS / EXTRA / CATALOG from mill source text. Never exec."""

    try:
        tree = ast.parse(text)
    except SyntaxError as exc:
        raise GqlRefusal(
            FINDING_SOURCE_NOT_PARSEABLE, f"{source} does not parse: {exc}"
        ) from exc
    found: dict[str, ast.AST] = {}
    inferred_base: Any = None
    banned_node: ast.AST | None = None
    for node in tree.body:
        assigned = _assigned_name(node)
        if assigned is None:
            continue
        name, value = assigned
        if name in LITERAL_NAMES:
            found[name] = value
        elif name in {"BASE", "CATALOG_FIRST"}:
            inferred_base = _const_eval(value)
        elif name == "BANNED":
            banned_node = value
    # EXTRA before a computed PAIRS binding; never follow unused-pair loops.
    if "EXTRA" in found:
        raw_plants = _const_eval(found["EXTRA"])
        shape = SHAPE_PAIR
    elif "PAIRS" in found:
        raw_plants = _const_eval(found["PAIRS"])
        shape = SHAPE_PAIR
    elif "PLANTS" in found:
        raw_plants = _const_eval(found["PLANTS"])
        shape = SHAPE_PAIR
    elif "CATALOG" in found:
        raw_plants = _const_eval(found["CATALOG"])
        shape = SHAPE_SURFACE
    else:
        raise GqlRefusal(FINDING_SOURCE_NOT_PARSEABLE, f"{source} has no plant literal")
    if not isinstance(raw_plants, list) or not raw_plants:
        raise GqlRefusal(FINDING_SOURCE_NOT_PARSEABLE, f"{source} plant literal is empty")
    if not MILL_ID_RE.fullmatch(mill_id):
        raise GqlRefusal(FINDING_PLANT_FIELD_INVALID, f"mill_id {mill_id!r} is not gql_rNNN")
    base = inferred_base if base_round is None else base_round
    if base is None:
        base = int(mill_id[len("gql_r") :])
    base = _require_int(base, f"{source} BASE", FINDING_PLANT_FIELD_INVALID, 1)
    rows = []
    for index, raw in enumerate(raw_plants):
        if shape == SHAPE_PAIR:
            rows.append(
                _pair_from_raw(raw, mill_id=mill_id, source=source, base_round=base, index=index)
            )
        else:
            rows.append(
                _surface_from_raw(raw, mill_id=mill_id, source=source, base_round=base, index=index)
            )
    if banned_node is not None:
        banned = _const_eval(banned_node)
        if not isinstance(banned, (list, tuple)):
            raise GqlRefusal(FINDING_SOURCE_NOT_PARSEABLE, f"{source} BANNED is not a list")
        tokens = {str(token).lower() for token in banned}
        for row in rows:
            for side_name in ("ok", "bad"):
                slug = str(row[side_name]["slug"]).lower()
                for token in tokens:
                    if token in slug:
                        raise GqlRefusal(
                            FINDING_PLANT_FIELD_INVALID,
                            f"{source} {side_name}.slug carries banned token {token}",
                        )
    return tuple(rows)


def _field(mapping: Any, key: str, kinds: type | tuple[type, ...], where: str) -> Any:
    if not isinstance(mapping, dict):
        raise GqlRefusal(FINDING_CATALOG_FIELD_INVALID, f"{where} must be an object")
    if key not in mapping:
        raise GqlRefusal(FINDING_CATALOG_FIELD_MISSING, f"{where}.{key} is missing")
    value = mapping[key]
    if isinstance(value, bool) and kinds is not bool:
        raise GqlRefusal(FINDING_CATALOG_FIELD_INVALID, f"{where}.{key} has the wrong type")
    if not isinstance(value, kinds):
        raise GqlRefusal(FINDING_CATALOG_FIELD_INVALID, f"{where}.{key} has the wrong type")
    return value


def _payload_text(row: Mapping[str, Any], key: str, where: str, *, strip: bool = True) -> str:
    return _require_text(row.get(key), f"{where}.{key}", FINDING_PLANT_FIELD_MISSING, strip=strip)


def _plant_from_row(row: Any, where: str) -> Plant:
    if not isinstance(row, dict):
        raise GqlRefusal(FINDING_PLANT_FIELD_INVALID, f"{where} must be an object")
    mill_id = _require_text(row.get("mill_id"), f"{where}.mill_id", FINDING_PLANT_FIELD_INVALID)
    slug = _require_text(row.get("slug"), f"{where}.slug", FINDING_PLANT_FIELD_INVALID)
    if not MILL_ID_RE.fullmatch(mill_id):
        raise GqlRefusal(FINDING_PLANT_FIELD_INVALID, f"{where}.mill_id is not gql_rNNN")
    if not SLUG_RE.fullmatch(slug):
        raise GqlRefusal(FINDING_PLANT_FIELD_INVALID, f"{where}.slug is not a plant slug")
    plant_id = _require_text(row.get("plant_id"), f"{where}.plant_id", FINDING_PLANT_FIELD_INVALID)
    expected = f"{mill_id}:{slug}"
    if plant_id != expected:
        raise GqlRefusal(FINDING_PLANT_FIELD_INVALID, f"{where}.plant_id must be {expected!r}")
    base_round = _require_int(row.get("base_round"), f"{where}.base_round", FINDING_PLANT_FIELD_INVALID, 1)
    shape = _require_text(row.get("shape"), f"{where}.shape", FINDING_PLANT_FIELD_INVALID)
    plant = _require_text(row.get("plant"), f"{where}.plant", FINDING_PLANT_FIELD_MISSING)
    coverage = _require_int(row.get("coverage"), f"{where}.coverage", FINDING_PLANT_FIELD_INVALID, 1)
    source = _require_text(row.get("source"), f"{where}.source", FINDING_PLANT_FIELD_MISSING)
    if shape == SHAPE_PAIR:
        payload = {
            "bad": _side_dict(row.get("bad"), BAD_KEYS, f"{where}.bad"),
            "field": _payload_text(row, "field", where),
            "next": _payload_text(row, "next", where, strip=False),
            "ok": _side_dict(row.get("ok"), OK_KEYS, f"{where}.ok"),
            "window": _payload_text(row, "window", where, strip=False),
        }
    elif shape == SHAPE_SURFACE:
        payload = {key: _payload_text(row, key, where) for key in SURFACE_ROW_KEYS if key != "idx" and key != "coverage"}
        payload["idx"] = _require_int(row.get("idx"), f"{where}.idx", FINDING_PLANT_FIELD_INVALID, 0)
        payload["coverage"] = coverage
    else:
        raise GqlRefusal(FINDING_PLANT_FIELD_INVALID, f"{where}.shape must be pair or surface")
    return Plant(
        plant_id=plant_id,
        mill_id=mill_id,
        source=source,
        base_round=base_round,
        shape=shape,
        slug=slug,
        plant=plant,
        coverage=coverage,
        payload=payload,
    )


def _mill_from_row(row: Any, where: str) -> Mill:
    mill_id = _require_text(
        _field(row, "mill_id", str, where), f"{where}.mill_id", FINDING_CATALOG_FIELD_INVALID
    )
    if not MILL_ID_RE.fullmatch(mill_id):
        raise GqlRefusal(FINDING_CATALOG_FIELD_INVALID, f"{where}.mill_id is not gql_rNNN")
    base_round = _field(row, "base_round", int, where)
    if isinstance(base_round, bool) or base_round < 1:
        raise GqlRefusal(
            FINDING_CATALOG_FIELD_INVALID, f"{where}.base_round must be a positive int"
        )
    plant_count = _field(row, "plant_count", int, where)
    if isinstance(plant_count, bool) or plant_count < 1:
        raise GqlRefusal(
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
        raise GqlRefusal(FINDING_CATALOG_FILE_MISSING, f"{path} is unreadable: {exc}") from exc
    if not text.endswith("\n") or "\r" in text:
        raise GqlRefusal(FINDING_CATALOG_FIELD_INVALID, f"{path.name} must be LF-framed jsonl")
    rows = []
    for index, line in enumerate(text.splitlines(), start=1):
        if not line:
            raise GqlRefusal(FINDING_CATALOG_FIELD_INVALID, f"{path.name}:{index} is empty")
        try:
            rows.append(load_strict_json(line))
        except ValueError as exc:
            raise GqlRefusal(
                FINDING_CATALOG_FIELD_INVALID, f"{path.name}:{index} is not strict JSON"
            ) from exc
    return tuple(rows)


def _registry_factory_ids() -> set[str]:
    path = repo_root() / "config" / "FACTORY-REGISTRY.json"
    try:
        payload = load_strict_json(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise GqlRefusal(
            FINDING_FACTORY_NOT_REGISTERED, f"factory registry is unreadable: {exc}"
        ) from exc
    factories = payload.get("factories") if isinstance(payload, dict) else None
    if not isinstance(factories, list):
        raise GqlRefusal(FINDING_FACTORY_NOT_REGISTERED, "factory registry factories is not a list")
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
        raise GqlRefusal(FINDING_CATALOG_FILE_MISSING, f"{meta_path} is missing") from exc
    try:
        meta = load_strict_json(meta_text)
    except ValueError as exc:
        raise GqlRefusal(
            FINDING_CATALOG_FIELD_INVALID, f"{CATALOG_FILENAME} is not strict JSON"
        ) from exc
    catalog_id = _require_text(
        _field(meta, "catalog_id", str, CATALOG_FILENAME),
        f"{CATALOG_FILENAME}.catalog_id",
        FINDING_CATALOG_FIELD_INVALID,
    )
    fmt = _field(meta, "format", str, CATALOG_FILENAME)
    if fmt != CATALOG_FORMAT:
        raise GqlRefusal(
            FINDING_CATALOG_FIELD_INVALID,
            f"{CATALOG_FILENAME}.format must be {CATALOG_FORMAT}",
        )
    factory = _field(meta, "factory", str, CATALOG_FILENAME)
    if factory != FACTORY:
        raise GqlRefusal(
            FINDING_CATALOG_FIELD_INVALID, f"{CATALOG_FILENAME}.factory must be {FACTORY}"
        )
    prefix = _field(meta, "mill_prefix", str, CATALOG_FILENAME)
    if prefix != MILL_PREFIX:
        raise GqlRefusal(
            FINDING_CATALOG_FIELD_INVALID,
            f"{CATALOG_FILENAME}.mill_prefix must be {MILL_PREFIX}",
        )
    kind = _field(meta, "record_kind", str, CATALOG_FILENAME)
    if kind != RECORD_KIND:
        raise GqlRefusal(
            FINDING_CATALOG_FIELD_INVALID,
            f"{CATALOG_FILENAME}.record_kind must be {RECORD_KIND}",
        )
    quota = _field(meta, "quota_per_round", int, CATALOG_FILENAME)
    if isinstance(quota, bool) or quota != QUOTA_PER_ROUND:
        raise GqlRefusal(
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
        raise GqlRefusal(FINDING_CATALOG_FILE_MISSING, f"{plants_path} is missing") from exc
    digest = sha256_bytes(plants_bytes)
    if digest != plants_sha256:
        raise GqlRefusal(
            FINDING_CATALOG_SHA256_MISMATCH,
            f"{PLANTS_FILENAME} digest {digest} != catalog pin {plants_sha256}",
        )
    if factory not in _registry_factory_ids():
        raise GqlRefusal(FINDING_FACTORY_NOT_REGISTERED, f"{factory} is not a registry path_id")
    rows = _read_jsonl(plants_path)
    if len(rows) != plant_count:
        raise GqlRefusal(
            FINDING_CATALOG_FIELD_INVALID,
            f"{CATALOG_FILENAME}.plant_count is {plant_count}, file has {len(rows)}",
        )
    plants = tuple(
        _plant_from_row(row, f"{PLANTS_FILENAME}:{i}") for i, row in enumerate(rows, start=1)
    )
    seen: set[str] = set()
    for plant in plants:
        if plant.plant_id in seen:
            raise GqlRefusal(FINDING_PLANT_DUPLICATE_ID, f"duplicate plant_id {plant.plant_id}")
        seen.add(plant.plant_id)
    by_mill: dict[str, int] = {}
    for plant in plants:
        by_mill[plant.mill_id] = by_mill.get(plant.mill_id, 0) + 1
    mill_ids = {mill.mill_id for mill in mills}
    if mill_ids != set(by_mill):
        raise GqlRefusal(
            FINDING_CATALOG_FIELD_INVALID, "catalog mills do not match plant mill_id values"
        )
    for mill in mills:
        if by_mill[mill.mill_id] != mill.plant_count:
            raise GqlRefusal(
                FINDING_CATALOG_FIELD_INVALID,
                f"{mill.mill_id} plant_count {mill.plant_count} != {by_mill[mill.mill_id]}",
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
