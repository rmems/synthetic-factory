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
from collections.abc import Callable, Mapping, Sequence
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


def _dict_items(node: ast.Dict) -> list[tuple[ast.expr, ast.expr]]:
    """The key and value nodes of a dict literal; ``**`` unpacking refuses before any is read."""

    items: list[tuple[ast.expr, ast.expr]] = []
    for key, value in zip(node.keys, node.values):
        if key is None:
            raise GqlRefusal(FINDING_SOURCE_NOT_PARSEABLE, "plant source uses dict unpacking")
        items.append((key, value))
    return items


def _bare_s_call(node: ast.AST) -> ast.Call | None:
    """``S(**kwargs)``: a call of the name ``S`` with keywords only, else None."""

    if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Name):
        return None
    return node if node.func.id == "S" and not node.args else None


def _negated(values: list[Any]) -> Any:
    return -values[0]


def _const_parts(node: ast.AST) -> tuple[Sequence[ast.AST], Callable[[list[Any]], Any]]:
    """A list, a negation or an ``S(**kwargs)`` call as (child nodes, rebuild); others refuse.

    ``_const_eval`` evaluates the children itself, so a nesting level costs one frame.
    """

    if isinstance(node, ast.List):
        return node.elts, list
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        return (node.operand,), _negated
    call = _bare_s_call(node)
    if call is None:
        raise GqlRefusal(
            FINDING_SOURCE_NOT_PARSEABLE,
            f"plant source is not a constant ({type(node).__name__})",
        )
    names = [kw.arg for kw in call.keywords]
    return [kw.value for kw in call.keywords], lambda values: dict(zip(names, values))


def _const_eval(node: ast.AST) -> Any:
    """Literal values only. ``S(**kwargs)`` is a dict; other calls refuse."""

    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Tuple):
        return tuple(_const_eval(item) for item in node.elts)
    if isinstance(node, ast.Dict):
        return {_const_eval(key): _const_eval(value) for key, value in _dict_items(node)}
    children, rebuild = _const_parts(node)
    return rebuild([_const_eval(child) for child in children])


def _assigned_name(node: ast.AST) -> tuple[str, ast.AST] | None:
    if isinstance(node, ast.Assign) and len(node.targets) == 1:
        target = node.targets[0]
        if isinstance(target, ast.Name):
            return target.id, node.value
    if (
        isinstance(node, ast.AnnAssign)
        and isinstance(node.target, ast.Name)
        and node.value is not None
    ):
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


@dataclass(frozen=True)
class _MillSource:
    """The mill a raw plant literal was read from: id, source path, and base round."""

    mill_id: str
    source: str
    base_round: int


def _pair_from_raw(raw: Any, mill: _MillSource, index: int) -> dict[str, Any]:
    mill_id, source, base_round = mill.mill_id, mill.source, mill.base_round
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


def _surface_from_raw(raw: Any, mill: _MillSource, index: int) -> dict[str, Any]:
    mill_id, source, base_round = mill.mill_id, mill.source, mill.base_round
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


# EXTRA before a computed PAIRS binding; never follow unused-pair loops.
_PLANT_LITERALS = (
    ("EXTRA", SHAPE_PAIR),
    ("PAIRS", SHAPE_PAIR),
    ("PLANTS", SHAPE_PAIR),
    ("CATALOG", SHAPE_SURFACE),
)


def _module_literals(tree: ast.Module) -> tuple[dict[str, ast.AST], Any, ast.AST | None]:
    """Plant literal nodes by name, the evaluated BASE / CATALOG_FIRST, and the BANNED node."""

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
    return found, inferred_base, banned_node


def _raw_plants(found: Mapping[str, ast.AST], source: str) -> tuple[list[Any], str]:
    for name, shape in _PLANT_LITERALS:
        if name in found:
            raw_plants = _const_eval(found[name])
            break
    else:
        raise GqlRefusal(FINDING_SOURCE_NOT_PARSEABLE, f"{source} has no plant literal")
    if not isinstance(raw_plants, list) or not raw_plants:
        raise GqlRefusal(FINDING_SOURCE_NOT_PARSEABLE, f"{source} plant literal is empty")
    return raw_plants, shape


def _base_round(inferred_base: Any, base_round: int | None, mill_id: str, source: str) -> int:
    base = inferred_base if base_round is None else base_round
    if base is None:
        base = int(mill_id[len("gql_r") :])
    return _require_int(base, f"{source} BASE", FINDING_PLANT_FIELD_INVALID, 1)


def _refuse_banned_slugs(banned_node: ast.AST, rows: list[dict[str, Any]], source: str) -> None:
    banned = _const_eval(banned_node)
    if not isinstance(banned, (list, tuple)):
        raise GqlRefusal(FINDING_SOURCE_NOT_PARSEABLE, f"{source} BANNED is not a list")
    tokens = {str(token).lower() for token in banned}
    for row in rows:
        for side_name in ("ok", "bad"):
            slug = str(row[side_name]["slug"]).lower()
            hit = next((token for token in tokens if token in slug), None)
            if hit is not None:
                raise GqlRefusal(
                    FINDING_PLANT_FIELD_INVALID,
                    f"{source} {side_name}.slug carries banned token {hit}",
                )


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
    found, inferred_base, banned_node = _module_literals(tree)
    raw_plants, shape = _raw_plants(found, source)
    if not MILL_ID_RE.fullmatch(mill_id):
        raise GqlRefusal(FINDING_PLANT_FIELD_INVALID, f"mill_id {mill_id!r} is not gql_rNNN")
    mill = _MillSource(mill_id, source, _base_round(inferred_base, base_round, mill_id, source))
    build = _pair_from_raw if shape == SHAPE_PAIR else _surface_from_raw
    rows = [build(raw, mill, index) for index, raw in enumerate(raw_plants)]
    if banned_node is not None:
        _refuse_banned_slugs(banned_node, rows, source)
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


def _plant_identity(row: Mapping[str, Any], where: str) -> tuple[str, str, str]:
    """``(mill_id, slug, plant_id)``; ``plant_id`` must be ``mill_id:slug``."""

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
    return mill_id, slug, plant_id


def _plant_payload(row: Mapping[str, Any], where: str, shape: str, coverage: int) -> dict[str, Any]:
    if shape == SHAPE_PAIR:
        return {
            "bad": _side_dict(row.get("bad"), BAD_KEYS, f"{where}.bad"),
            "field": _payload_text(row, "field", where),
            "next": _payload_text(row, "next", where, strip=False),
            "ok": _side_dict(row.get("ok"), OK_KEYS, f"{where}.ok"),
            "window": _payload_text(row, "window", where, strip=False),
        }
    if shape == SHAPE_SURFACE:
        payload: dict[str, Any] = {
            key: _payload_text(row, key, where)
            for key in SURFACE_ROW_KEYS
            if key not in ("idx", "coverage")
        }
        payload["idx"] = _require_int(row.get("idx"), f"{where}.idx", FINDING_PLANT_FIELD_INVALID, 0)
        payload["coverage"] = coverage
        return payload
    raise GqlRefusal(FINDING_PLANT_FIELD_INVALID, f"{where}.shape must be pair or surface")


def _plant_from_row(row: Any, where: str) -> Plant:
    if not isinstance(row, dict):
        raise GqlRefusal(FINDING_PLANT_FIELD_INVALID, f"{where} must be an object")
    mill_id, slug, plant_id = _plant_identity(row, where)
    base_round = _require_int(row.get("base_round"), f"{where}.base_round", FINDING_PLANT_FIELD_INVALID, 1)
    shape = _require_text(row.get("shape"), f"{where}.shape", FINDING_PLANT_FIELD_INVALID)
    plant = _require_text(row.get("plant"), f"{where}.plant", FINDING_PLANT_FIELD_MISSING)
    coverage = _require_int(row.get("coverage"), f"{where}.coverage", FINDING_PLANT_FIELD_INVALID, 1)
    source = _require_text(row.get("source"), f"{where}.source", FINDING_PLANT_FIELD_MISSING)
    return Plant(
        plant_id=plant_id,
        mill_id=mill_id,
        source=source,
        base_round=base_round,
        shape=shape,
        slug=slug,
        plant=plant,
        coverage=coverage,
        payload=_plant_payload(row, where, shape, coverage),
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
        row["path_id"]
        for row in factories
        if isinstance(row, dict) and isinstance(row.get("path_id"), str)
    }


# Catalog header fields pinned to this family, checked in this order.
_PINNED_META = (
    ("format", str, CATALOG_FORMAT),
    ("factory", str, FACTORY),
    ("mill_prefix", str, MILL_PREFIX),
    ("record_kind", str, RECORD_KIND),
    ("quota_per_round", int, QUOTA_PER_ROUND),
)


def _read_meta(meta_path: Path) -> Any:
    try:
        meta_text = meta_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise GqlRefusal(FINDING_CATALOG_FILE_MISSING, f"{meta_path} is missing") from exc
    try:
        return load_strict_json(meta_text)
    except ValueError as exc:
        raise GqlRefusal(
            FINDING_CATALOG_FIELD_INVALID, f"{CATALOG_FILENAME} is not strict JSON"
        ) from exc


def _require_pinned_meta(meta: Any) -> None:
    for key, kind, expected in _PINNED_META:
        value = _field(meta, key, kind, CATALOG_FILENAME)
        if isinstance(value, bool) or value != expected:
            raise GqlRefusal(
                FINDING_CATALOG_FIELD_INVALID,
                f"{CATALOG_FILENAME}.{key} must be {expected}",
            )


def _pinned_plants_digest(plants_path: Path, plants_sha256: str) -> str:
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
    return digest


def _load_plants(plants_path: Path, plant_count: int) -> tuple[Plant, ...]:
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
    return plants


def _require_mill_counts(mills: tuple[Mill, ...], plants: tuple[Plant, ...]) -> None:
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


def load_catalog(directory: Path | None = None) -> Catalog:
    """Load a catalog directory and refuse unless every pin holds."""

    catalog_dir = Path(default_catalog_dir() if directory is None else directory)
    meta = _read_meta(catalog_dir / CATALOG_FILENAME)
    catalog_id = _require_text(
        _field(meta, "catalog_id", str, CATALOG_FILENAME),
        f"{CATALOG_FILENAME}.catalog_id",
        FINDING_CATALOG_FIELD_INVALID,
    )
    _require_pinned_meta(meta)
    factory = meta["factory"]
    plant_count = _field(meta, "plant_count", int, CATALOG_FILENAME)
    plants_sha256 = _field(meta, "plants_sha256", str, CATALOG_FILENAME)
    mill_rows = _field(meta, "mills", list, CATALOG_FILENAME)
    mills = tuple(
        _mill_from_row(row, f"{CATALOG_FILENAME}.mills[{i}]") for i, row in enumerate(mill_rows)
    )
    plants_path = catalog_dir / PLANTS_FILENAME
    digest = _pinned_plants_digest(plants_path, plants_sha256)
    if factory not in _registry_factory_ids():
        raise GqlRefusal(FINDING_FACTORY_NOT_REGISTERED, f"{factory} is not a registry path_id")
    plants = _load_plants(plants_path, plant_count)
    _require_mill_counts(mills, plants)
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
