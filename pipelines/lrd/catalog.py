#!/usr/bin/env python3
"""Pinned LRD pair catalog: load, pin, and AST-extract (never exec).

A catalog directory holds ``CATALOG.json`` (identity, factory, mill pins)
and ``plants.jsonl`` (one pair per line). Load verifies the plants digest
and every required field before a pair is trusted. Historical leftover
mill scripts are read only as text through :func:`plants_from_source`.
Hopper scripts (``dpr-lrd-hopper*``) and ``lrd-loop-*`` drivers are refused.
"""

from __future__ import annotations

import ast
import hashlib
import re
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, TypeGuard

from ._contract import (
    CATALOG_FILENAME,
    CATALOG_FORMAT,
    CATALOG_SLICE,
    FACTORY,
    FULL_MILL_COUNTS,
    FULL_PLANT_COUNT,
    SHAPE_LEGACY,
    SHAPE_LEFTOVER3,
    SHAPE_LLL,
    SHAPE_P_COOKIE,
    SHAPE_P_IDTOKEN,
    FINDING_CATALOG_FIELD_INVALID,
    FINDING_CATALOG_FIELD_MISSING,
    FINDING_CATALOG_FILE_MISSING,
    FINDING_CATALOG_SHA256_MISMATCH,
    FINDING_FACTORY_NOT_REGISTERED,
    FINDING_HOPPER_REFUSED,
    FINDING_MILL_NOT_FOUND,
    FINDING_PLANT_DUPLICATE_ID,
    FINDING_PLANT_FIELD_INVALID,
    FINDING_PLANT_FIELD_MISSING,
    FINDING_PLANT_NOT_FOUND,
    FINDING_SOURCE_NOT_PARSEABLE,
    HOPPER_DEF_NAMES,
    PAIR_KEYS,
    PLANTS_FILENAME,
    PREFIX,
    QUOTA_PER_ROUND,
    RECORD_KIND,
    bind_import_twin,
    default_catalog_dir,
    load_strict_json,
    refuse,
    refuse_when,
    repo_root,
)

MILL_ID_RE = re.compile(r"^lrd_r[0-9]+$")
SLUG_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")

from . import catalog_extract as _extract

__all__ = [
    "CATALOG_FILENAME",
    "Catalog",
    "MILL_ID_RE",
    "Mill",
    "PLANTS_FILENAME",
    "Plant",
    "ast_extract_plants",
    "catalog_check",
    "default_catalog_dir",
    "load_catalog",
    "plants_from_source",
    "refuse_hopper_source",
    "sha256_bytes",
]

ast_extract_plants = _extract.ast_extract_plants
refuse_hopper_source = _extract.refuse_hopper_source
_refuse_loop_source = _extract.refuse_loop_source


@dataclass(frozen=True)
class Plant:
    """One AST-extracted redaction plant (legacy ``dict`` or leftover3 pair)."""

    plant_id: str
    mill_id: str
    source: str
    base_round: int
    shape: str
    slug: str
    payload: Mapping[str, Any] | None
    mod: str
    drop: str
    stack: str
    field: str
    naive: str
    conf: str
    conf2: str
    oldc: str
    newc: str
    old2: str
    new2: str
    test: str
    ticket: str
    fail: str
    domain: str


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
        refuse(FINDING_PLANT_NOT_FOUND, f"no plant {plant_id!r} in the catalog")

    def mill_plants(self, mill_id: str) -> tuple[Plant, ...]:
        found = tuple(item for item in self.plants if item.mill_id == mill_id)
        refuse_when(not found, FINDING_MILL_NOT_FOUND, f"no mill {mill_id!r} in the catalog")
        return found


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _const_eval(node: ast.AST) -> Any:
    """Literal values and keyword-only ``dict(...)`` calls. Never exec."""

    # Every recursive call is made here and the helpers below never recurse, so a
    # list, dict, ``dict(...)`` or unary-minus level costs one frame (a tuple level
    # two, with its generator), as it did before the helpers were split out.
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.List):
        return [_const_eval(item) for item in node.elts]
    if isinstance(node, ast.Tuple):
        return tuple(_const_eval(item) for item in node.elts)
    if _is_negation(node):
        return -_const_eval(node.operand)
    return {_const_eval(key): _const_eval(value) for key, value in _mapping_entries(node)}


def _is_negation(node: ast.AST) -> TypeGuard[ast.UnaryOp]:
    return isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub)


def _mapping_entries(node: ast.AST) -> list[tuple[ast.expr, ast.expr]]:
    """Key/value nodes of a dict display or a keyword-only ``dict(...)`` call.

    ``**`` unpacking is refused before any value is evaluated, and anything else is
    refused as a non-literal call or a non-constant. A keyword name becomes a constant
    key node, so both spellings share ``_const_eval``'s one comprehension.
    """

    if isinstance(node, ast.Dict):
        if None in node.keys:
            refuse(FINDING_SOURCE_NOT_PARSEABLE, "pair source uses dict unpacking")
        return [(key, value) for key, value in zip(node.keys, node.values) if key is not None]
    if not isinstance(node, ast.Call):
        refuse(
            FINDING_SOURCE_NOT_PARSEABLE,
            f"pair source is not a constant ({type(node).__name__})",
        )
    if not _is_keyword_dict_call(node):
        refuse(
            FINDING_SOURCE_NOT_PARSEABLE,
            f"pair source uses a non-literal call ({type(node).__name__})",
        )
    return [(ast.Constant(keyword.arg), keyword.value) for keyword in node.keywords]


def _is_keyword_dict_call(node: ast.Call) -> bool:
    func = node.func
    if not isinstance(func, ast.Name) or func.id != "dict":
        return False
    return not node.args and None not in [keyword.arg for keyword in node.keywords]


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


def _refuse_hopper_defs(source: str, tree: ast.AST) -> None:
    defs = {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    refuse_when(
        bool(defs & HOPPER_DEF_NAMES),
        FINDING_HOPPER_REFUSED,
        f"{source} defines mill_and_publish; hopper exec is refused",
    )


def plants_from_source(
    text: str,
    *,
    mill_id: str,
    source: str,
    base_round: int | None = None,
) -> tuple[dict[str, Any], ...]:
    """AST-extract ``PAIRS`` from leftover-mill source text. Never exec."""

    refuse_hopper_source(source)
    _refuse_loop_source(source)
    try:
        tree = ast.parse(text)
    except SyntaxError as exc:
        refuse(FINDING_SOURCE_NOT_PARSEABLE, f"{source} does not parse: {exc}")
    _refuse_hopper_defs(source, tree)
    raw_pairs, inferred_base = _module_pairs_and_base(tree)
    refuse_when(
        not isinstance(raw_pairs, list) or not raw_pairs,
        FINDING_SOURCE_NOT_PARSEABLE,
        f"{source} has no PAIRS list",
    )
    refuse_when(
        not MILL_ID_RE.fullmatch(mill_id),
        FINDING_PLANT_FIELD_INVALID,
        f"mill_id {mill_id!r} is not lrd_rNNN",
    )
    base = _resolve_base(inferred_base, base_round, mill_id, source)
    return _source_pair_rows(raw_pairs, mill_id, source, base)


def _is_positive_int(value: Any) -> bool:
    if isinstance(value, bool) or not isinstance(value, int):
        return False
    return value >= 1


def _module_pairs_and_base(tree: ast.Module) -> tuple[Any, Any]:
    """Constant-evaluate the module-level ``PAIRS`` and ``BASE`` (last assignment wins)."""

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
    return raw_pairs, inferred_base


def _resolve_base(inferred_base: Any, base_round: int | None, mill_id: str, source: str) -> int:
    base = inferred_base if base_round is None else base_round
    if base is None:
        base = int(mill_id[len("lrd_r") :])
    refuse_when(
        not _is_positive_int(base),
        FINDING_PLANT_FIELD_INVALID,
        f"{source} BASE must be a positive int",
    )
    return base


def _source_pair_rows(
    raw_pairs: list[Any], mill_id: str, source: str, base: int
) -> tuple[dict[str, Any], ...]:
    rows = []
    for index, raw in enumerate(raw_pairs):
        _require_source_pair(raw, f"{source} PAIRS[{index}]")
        row = {
            "plant_id": f"{mill_id}:{raw['slug']}",
            "mill_id": mill_id,
            "source": source,
            "base_round": base,
        }
        row.update({key: raw[key] for key in PAIR_KEYS})
        rows.append(row)
    return tuple(rows)


def _require_source_pair(raw: Any, where: str) -> None:
    refuse_when(
        not isinstance(raw, dict),
        FINDING_SOURCE_NOT_PARSEABLE,
        f"{where} is not an object",
    )
    missing = [key for key in PAIR_KEYS if key not in raw]
    refuse_when(
        bool(missing),
        FINDING_PLANT_FIELD_MISSING,
        f"{where} missing {missing[0] if missing else ''}",
    )


def _field(mapping: Any, key: str, kinds: type | tuple[type, ...], where: str) -> Any:
    refuse_when(
        not isinstance(mapping, dict),
        FINDING_CATALOG_FIELD_INVALID,
        f"{where} must be an object",
    )
    refuse_when(key not in mapping, FINDING_CATALOG_FIELD_MISSING, f"{where}.{key} is missing")
    value = mapping[key]
    if isinstance(value, bool) and kinds is not bool:
        refuse(FINDING_CATALOG_FIELD_INVALID, f"{where}.{key} has the wrong type")
    refuse_when(
        not isinstance(value, kinds),
        FINDING_CATALOG_FIELD_INVALID,
        f"{where}.{key} has the wrong type",
    )
    return value


def _is_stripped_text(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    return bool(value.strip()) and value == value.strip()


def _require_text(value: Any, where: str, code: str) -> str:
    refuse_when(
        not _is_stripped_text(value),
        code,
        f"{where} must be a non-empty stripped string",
    )
    return value


_PLANT_SHAPES = frozenset(
    {
        SHAPE_LEGACY,
        SHAPE_LEFTOVER3,
        SHAPE_P_IDTOKEN,
        SHAPE_P_COOKIE,
        SHAPE_LLL,
    }
)
# The legacy text fields a Plant carries besides its identity (``slug`` is identity).
_PLANT_TEXT_KEYS = tuple(key for key in PAIR_KEYS if key != "slug")


def _plant_from_row(row: Any, where: str) -> Plant:
    refuse_when(
        not isinstance(row, dict),
        FINDING_PLANT_FIELD_INVALID,
        f"{where} must be an object",
    )
    mill_id, slug, plant_id = _plant_identity(row, where)
    base_round = row.get("base_round")
    refuse_when(
        not _is_positive_int(base_round),
        FINDING_PLANT_FIELD_INVALID,
        f"{where}.base_round must be a positive int",
    )
    shape = row.get("shape", SHAPE_LEGACY)
    refuse_when(
        not isinstance(shape, str) or shape not in _PLANT_SHAPES,
        FINDING_PLANT_FIELD_INVALID,
        f"{where}.shape is not a supported extract shape",
    )
    source = _require_text(row.get("source"), f"{where}.source", FINDING_PLANT_FIELD_MISSING)
    common = {
        "plant_id": plant_id,
        "mill_id": mill_id,
        "source": source,
        "base_round": base_round,
        "shape": shape,
        "slug": slug,
    }
    if shape == SHAPE_LEGACY:
        return _legacy_plant(row, where, common)
    return _payload_plant(row, where, common)


def _plant_identity(row: dict[str, Any], where: str) -> tuple[str, str, str]:
    mill_id = _require_text(row.get("mill_id"), f"{where}.mill_id", FINDING_PLANT_FIELD_INVALID)
    slug = _require_text(row.get("slug"), f"{where}.slug", FINDING_PLANT_FIELD_INVALID)
    refuse_when(
        not MILL_ID_RE.fullmatch(mill_id),
        FINDING_PLANT_FIELD_INVALID,
        f"{where}.mill_id is not lrd_rNNN",
    )
    refuse_when(
        not SLUG_RE.fullmatch(slug),
        FINDING_PLANT_FIELD_INVALID,
        f"{where}.slug is not a plant slug",
    )
    plant_id = _require_text(row.get("plant_id"), f"{where}.plant_id", FINDING_PLANT_FIELD_INVALID)
    expected = f"{mill_id}:{slug}"
    refuse_when(
        plant_id != expected,
        FINDING_PLANT_FIELD_INVALID,
        f"{where}.plant_id must be {expected!r}",
    )
    return mill_id, slug, plant_id


def _legacy_plant(row: dict[str, Any], where: str, common: dict[str, Any]) -> Plant:
    fields = {
        key: _require_text(row.get(key), f"{where}.{key}", FINDING_PLANT_FIELD_MISSING)
        for key in PAIR_KEYS
    }
    return _build_plant(common, None, fields)


def _payload_plant(row: dict[str, Any], where: str, common: dict[str, Any]) -> Plant:
    payload = row.get("payload")
    refuse_when(
        not isinstance(payload, dict),
        FINDING_PLANT_FIELD_INVALID,
        f"{where}.payload must be an object",
    )
    return _build_plant(common, payload, dict.fromkeys(_PLANT_TEXT_KEYS, ""))


def _build_plant(
    common: dict[str, Any], payload: dict[str, Any] | None, text: Mapping[str, str]
) -> Plant:
    return Plant(
        **common,
        payload=payload,
        mod=text["mod"],
        drop=text["drop"],
        stack=text["stack"],
        field=text["field"],
        naive=text["naive"],
        conf=text["conf"],
        conf2=text["conf2"],
        oldc=text["oldc"],
        newc=text["newc"],
        old2=text["old2"],
        new2=text["new2"],
        test=text["test"],
        ticket=text["ticket"],
        fail=text["fail"],
        domain=text["domain"],
    )


def _mill_from_row(row: Any, where: str) -> Mill:
    mill_id = _require_text(
        _field(row, "mill_id", str, where), f"{where}.mill_id", FINDING_CATALOG_FIELD_INVALID
    )
    refuse_when(
        not MILL_ID_RE.fullmatch(mill_id),
        FINDING_CATALOG_FIELD_INVALID,
        f"{where}.mill_id is not lrd_rNNN",
    )
    base_round = _field(row, "base_round", int, where)
    refuse_when(
        isinstance(base_round, bool) or base_round < 1,
        FINDING_CATALOG_FIELD_INVALID,
        f"{where}.base_round must be a positive int",
    )
    plant_count = _field(row, "plant_count", int, where)
    refuse_when(
        isinstance(plant_count, bool) or plant_count < 1,
        FINDING_CATALOG_FIELD_INVALID,
        f"{where}.plant_count must be a positive int",
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
        refuse(FINDING_CATALOG_FILE_MISSING, f"{path} is unreadable: {exc}")
    refuse_when(
        not text.endswith("\n") or "\r" in text,
        FINDING_CATALOG_FIELD_INVALID,
        f"{path.name} must be LF-framed jsonl",
    )
    rows = []
    for index, line in enumerate(text.splitlines(), start=1):
        refuse_when(not line, FINDING_CATALOG_FIELD_INVALID, f"{path.name}:{index} is empty")
        try:
            rows.append(load_strict_json(line))
        except ValueError:
            refuse(FINDING_CATALOG_FIELD_INVALID, f"{path.name}:{index} is not strict JSON")
    return tuple(rows)


def _registry_factory_ids() -> set[str]:
    path = repo_root() / "config" / "FACTORY-REGISTRY.json"
    try:
        payload = load_strict_json(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        refuse(FINDING_FACTORY_NOT_REGISTERED, f"factory registry is unreadable: {exc}")
    factories = payload.get("factories") if isinstance(payload, dict) else None
    if not isinstance(factories, list):
        refuse(FINDING_FACTORY_NOT_REGISTERED, "factory registry factories is not a list")
    path_ids = (row.get("path_id") for row in factories if isinstance(row, dict))
    return {path_id for path_id in path_ids if isinstance(path_id, str)}


def load_catalog(directory: Path | None = None) -> Catalog:
    """Load a catalog directory and refuse unless every pin holds."""

    catalog_dir = Path(default_catalog_dir() if directory is None else directory)
    plants_path = catalog_dir / PLANTS_FILENAME
    meta = _read_meta(catalog_dir / CATALOG_FILENAME)
    catalog_id = _require_text(
        _field(meta, "catalog_id", str, CATALOG_FILENAME),
        f"{CATALOG_FILENAME}.catalog_id",
        FINDING_CATALOG_FIELD_INVALID,
    )
    _require_pinned_text(meta, "format", CATALOG_FORMAT)
    factory = _require_pinned_text(meta, "factory", FACTORY)
    _require_pinned_text(meta, "mill_prefix", PREFIX)
    _require_pinned_text(meta, "record_kind", RECORD_KIND)
    _require_quota(meta)
    plant_count, full_plant_count, representative = _meta_plant_counts(meta)
    plants_sha256 = _field(meta, "plants_sha256", str, CATALOG_FILENAME)
    mill_rows = _field(meta, "mills", list, CATALOG_FILENAME)
    mills = tuple(
        _mill_from_row(row, f"{CATALOG_FILENAME}.mills[{i}]") for i, row in enumerate(mill_rows)
    )
    digest = _pinned_plants_digest(plants_path, plants_sha256)
    refuse_when(
        factory not in _registry_factory_ids(),
        FINDING_FACTORY_NOT_REGISTERED,
        f"{factory} is not a registry path_id",
    )
    plants = _load_plants(plants_path, plant_count)
    by_mill = _plants_per_mill(plants)
    mill_ids = {mill.mill_id for mill in mills}
    refuse_when(
        mill_ids != set(by_mill),
        FINDING_CATALOG_FIELD_INVALID,
        "catalog mills do not match plant mill_id values",
    )
    if representative:
        _check_representative_inventory(mills, by_mill, full_plant_count)
    else:
        _check_exact_inventory(mills, by_mill)
    return Catalog(
        catalog_id=catalog_id,
        directory=catalog_dir,
        factory=factory,
        plants_sha256=digest,
        plants=plants,
        mills=mills,
        meta=meta,
    )


def _read_meta(meta_path: Path) -> Any:
    try:
        meta_text = meta_path.read_text(encoding="utf-8")
    except OSError:
        refuse(FINDING_CATALOG_FILE_MISSING, f"{meta_path} is missing")
    try:
        return load_strict_json(meta_text)
    except ValueError:
        refuse(FINDING_CATALOG_FIELD_INVALID, f"{CATALOG_FILENAME} is not strict JSON")


def _require_pinned_text(meta: Any, key: str, expected: str) -> str:
    value = _field(meta, key, str, CATALOG_FILENAME)
    refuse_when(
        value != expected,
        FINDING_CATALOG_FIELD_INVALID,
        f"{CATALOG_FILENAME}.{key} must be {expected}",
    )
    return value


def _require_quota(meta: Any) -> None:
    quota = _field(meta, "quota_per_round", int, CATALOG_FILENAME)
    refuse_when(
        isinstance(quota, bool) or quota != QUOTA_PER_ROUND,
        FINDING_CATALOG_FIELD_INVALID,
        f"{CATALOG_FILENAME}.quota_per_round must be {QUOTA_PER_ROUND}",
    )


def _meta_plant_counts(meta: Any) -> tuple[int, int, bool]:
    """Committed and full plant counts, and whether the meta pins the full slice."""

    plant_count = _field(meta, "plant_count", int, CATALOG_FILENAME)
    full_raw = meta.get("full_plant_count", plant_count)
    refuse_when(
        not isinstance(full_raw, int) or isinstance(full_raw, bool),
        FINDING_CATALOG_FIELD_INVALID,
        f"{CATALOG_FILENAME}.full_plant_count must be an int",
    )
    full_plant_count = full_raw
    refuse_when(
        isinstance(full_plant_count, bool) or full_plant_count < plant_count,
        FINDING_CATALOG_FIELD_INVALID,
        f"{CATALOG_FILENAME}.full_plant_count must be >= plant_count",
    )
    representative = meta.get("slice") == CATALOG_SLICE
    if representative:
        refuse_when(
            full_plant_count != FULL_PLANT_COUNT,
            FINDING_CATALOG_FIELD_INVALID,
            f"{CATALOG_FILENAME}.full_plant_count must be {FULL_PLANT_COUNT}",
        )
    return plant_count, full_plant_count, representative


def _pinned_plants_digest(plants_path: Path, plants_sha256: str) -> str:
    try:
        plants_bytes = plants_path.read_bytes()
    except OSError:
        refuse(FINDING_CATALOG_FILE_MISSING, f"{plants_path} is missing")
    digest = sha256_bytes(plants_bytes)
    refuse_when(
        digest != plants_sha256,
        FINDING_CATALOG_SHA256_MISMATCH,
        f"{PLANTS_FILENAME} digest {digest} != catalog pin {plants_sha256}",
    )
    return digest


def _load_plants(plants_path: Path, plant_count: int) -> tuple[Plant, ...]:
    rows = _read_jsonl(plants_path)
    refuse_when(
        len(rows) != plant_count,
        FINDING_CATALOG_FIELD_INVALID,
        f"{CATALOG_FILENAME}.plant_count is {plant_count}, file has {len(rows)}",
    )
    plants = tuple(
        _plant_from_row(row, f"{PLANTS_FILENAME}:{i}") for i, row in enumerate(rows, start=1)
    )
    seen: set[str] = set()
    for plant in plants:
        refuse_when(
            plant.plant_id in seen,
            FINDING_PLANT_DUPLICATE_ID,
            f"duplicate plant_id {plant.plant_id}",
        )
        seen.add(plant.plant_id)
    return plants


def _plants_per_mill(plants: tuple[Plant, ...]) -> dict[str, int]:
    by_mill: dict[str, int] = {}
    for plant in plants:
        by_mill[plant.mill_id] = by_mill.get(plant.mill_id, 0) + 1
    return by_mill


def _check_representative_inventory(
    mills: tuple[Mill, ...], by_mill: dict[str, int], full_plant_count: int
) -> None:
    """Full slice: the mill pins carry the full inventory; the file commits a subset of each."""

    refuse_when(
        sum(mill.plant_count for mill in mills) != full_plant_count,
        FINDING_CATALOG_FIELD_INVALID,
        "mill plant_count values must sum to full_plant_count",
    )
    refuse_when(
        tuple((mill.mill_id, mill.plant_count) for mill in mills) != FULL_MILL_COUNTS,
        FINDING_CATALOG_FIELD_INVALID,
        "mill inventory does not match FULL_MILL_COUNTS",
    )
    for mill in mills:
        committed = by_mill.get(mill.mill_id, 0)
        refuse_when(
            committed < 1 or committed > mill.plant_count,
            FINDING_CATALOG_FIELD_INVALID,
            f"{mill.mill_id} committed {committed} outside 1..{mill.plant_count}",
        )


def _check_exact_inventory(mills: tuple[Mill, ...], by_mill: dict[str, int]) -> None:
    for mill in mills:
        refuse_when(
            by_mill.get(mill.mill_id, 0) != mill.plant_count,
            FINDING_CATALOG_FIELD_INVALID,
            f"{mill.mill_id} plant_count {mill.plant_count} != {by_mill.get(mill.mill_id, 0)}",
        )


def catalog_check(directory: Path | None = None) -> list[dict[str, str]]:
    """Load the catalog. An invalid catalog is a refusal, not a finding list."""

    loaded = load_catalog(directory)
    if loaded.plants:
        return []
    return [{"code": FINDING_CATALOG_FIELD_INVALID, "detail": "empty catalog"}]


bind_import_twin(__name__)
