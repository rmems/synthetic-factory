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
    FLAVORS,
    MILL_PREFIX,
    PAIR_KEYS,
    PLANTS_FILENAME,
    QUOTA_PER_ROUND,
    RECORD_KIND,
    SafRefusal,
    bind_import_twin,
    load_strict_json,
    repo_root,
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
class Plant:
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

    for node_type, evaluate in _CONST_EVALUATORS:
        if isinstance(node, node_type):
            return evaluate(node)
    raise _not_a_constant(node)


def _not_a_constant(node: ast.AST) -> SafRefusal:
    return SafRefusal(
        FINDING_SOURCE_NOT_PARSEABLE,
        f"pair source is not a constant ({type(node).__name__})",
    )


def _const_constant(node: ast.Constant) -> Any:
    return node.value


def _const_list(node: ast.List) -> list[Any]:
    return [_const_eval(item) for item in node.elts]


def _const_tuple(node: ast.Tuple) -> tuple[Any, ...]:
    return tuple(_const_eval(item) for item in node.elts)


def _const_dict(node: ast.Dict) -> dict[Any, Any]:
    if any(key is None for key in node.keys):
        raise SafRefusal(FINDING_SOURCE_NOT_PARSEABLE, "pair source uses dict unpacking")
    return {_const_eval(key): _const_eval(value) for key, value in zip(node.keys, node.values)}


def _const_negative(node: ast.UnaryOp) -> Any:
    if not isinstance(node.op, ast.USub):
        raise _not_a_constant(node)
    return -_const_eval(node.operand)


def _const_dict_call(node: ast.Call) -> dict[str, Any]:
    if not _is_keyword_dict_call(node):
        raise SafRefusal(
            FINDING_SOURCE_NOT_PARSEABLE,
            f"pair source uses a non-literal call ({type(node).__name__})",
        )
    return {
        keyword.arg: _const_eval(keyword.value) for keyword in node.keywords
    }


def _is_keyword_dict_call(node: ast.Call) -> bool:
    """``dict(key=literal, ...)`` with no positional or ``**`` arguments."""

    func = node.func
    if not isinstance(func, ast.Name) or func.id != "dict":
        return False
    if node.args:
        return False
    return all(keyword.arg is not None for keyword in node.keywords)


# Checked in this order; anything else is not a constant.
_CONST_EVALUATORS = (
    (ast.Constant, _const_constant),
    (ast.List, _const_list),
    (ast.Tuple, _const_tuple),
    (ast.Dict, _const_dict),
    (ast.UnaryOp, _const_negative),
    (ast.Call, _const_dict_call),
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


def plants_from_source(
    text: str,
    *,
    mill_id: str,
    source: str,
    base_round: int | None = None,
) -> tuple[dict[str, Any], ...]:
    """AST-extract ``PAIRS`` from leftover-mill source text. Never exec."""

    raw_pairs, inferred_base = _pairs_and_base(_parse_source(text, source))
    if not isinstance(raw_pairs, list) or not raw_pairs:
        raise SafRefusal(FINDING_SOURCE_NOT_PARSEABLE, f"{source} has no PAIRS list")
    if not MILL_ID_RE.fullmatch(mill_id):
        raise SafRefusal(FINDING_PLANT_FIELD_INVALID, f"mill_id {mill_id!r} is not saf_rNNN")
    base = _source_base_round(
        inferred_base if base_round is None else base_round, mill_id, source
    )
    rows = []
    for index, raw in enumerate(raw_pairs):
        _require_pair_keys(raw, index, source)
        row = {
            "plant_id": f"{mill_id}:{raw['slug']}",
            "mill_id": mill_id,
            "source": source,
            "base_round": base,
        }
        row.update({key: raw[key] for key in PAIR_KEYS})
        rows.append(row)
    return tuple(rows)


def _parse_source(text: str, source: str) -> ast.Module:
    try:
        return ast.parse(text)
    except SyntaxError as exc:
        raise SafRefusal(
            FINDING_SOURCE_NOT_PARSEABLE, f"{source} does not parse: {exc}"
        ) from exc


def _pairs_and_base(tree: ast.Module) -> tuple[Any, Any]:
    """Literal ``PAIRS`` and ``BASE`` values; the last assignment of each wins."""

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


def _source_base_round(base: Any, mill_id: str, source: str) -> int:
    """The mill's base round, defaulting to the ``saf_rNNN`` number."""

    if base is None:
        base = int(mill_id[len("saf_r") :])
    if not _is_positive_int(base):
        raise SafRefusal(FINDING_PLANT_FIELD_INVALID, f"{source} BASE must be a positive int")
    return base


def _require_pair_keys(raw: Any, index: int, source: str) -> None:
    if not isinstance(raw, dict):
        raise SafRefusal(
            FINDING_SOURCE_NOT_PARSEABLE, f"{source} PAIRS[{index}] is not an object"
        )
    missing = [key for key in PAIR_KEYS if key not in raw]
    if missing:
        raise SafRefusal(
            FINDING_PLANT_FIELD_MISSING,
            f"{source} PAIRS[{index}] missing {missing[0]}",
        )


def _is_positive_int(value: Any) -> bool:
    if isinstance(value, bool) or not isinstance(value, int):
        return False
    return value >= 1


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


def _plant_identity(row: Any, where: str) -> tuple[str, str, str]:
    """``(plant_id, mill_id, slug)`` of a plants.jsonl row, refusing any that drift."""

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
    return plant_id, mill_id, slug


def _plant_from_row(row: Any, where: str) -> Plant:
    plant_id, mill_id, slug = _plant_identity(row, where)
    base_round = row.get("base_round")
    if not _is_positive_int(base_round):
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
    path = repo_root() / "config" / "FACTORY-REGISTRY.json"
    try:
        payload = load_strict_json(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise SafRefusal(
            FINDING_FACTORY_NOT_REGISTERED, f"factory registry is unreadable: {exc}"
        ) from exc
    factories = payload.get("factories") if isinstance(payload, dict) else None
    if not isinstance(factories, list):
        raise SafRefusal(FINDING_FACTORY_NOT_REGISTERED, "factory registry factories is not a list")
    return {
        row.get("path_id")
        for row in factories
        if isinstance(row, dict) and isinstance(row.get("path_id"), str)
    }


def load_catalog(directory: Path | None = None) -> Catalog:
    """Load a catalog directory and refuse unless every pin holds."""

    catalog_dir = Path(default_catalog_dir() if directory is None else directory)
    meta = _read_meta(catalog_dir / CATALOG_FILENAME)
    catalog_id, factory = _require_meta_pins(meta)
    plant_count = _field(meta, "plant_count", int, CATALOG_FILENAME)
    plants_sha256 = _field(meta, "plants_sha256", str, CATALOG_FILENAME)
    mill_rows = _field(meta, "mills", list, CATALOG_FILENAME)
    mills = tuple(
        _mill_from_row(row, f"{CATALOG_FILENAME}.mills[{i}]") for i, row in enumerate(mill_rows)
    )
    plants_path = catalog_dir / PLANTS_FILENAME
    digest = _pinned_plants_digest(plants_path, plants_sha256)
    if factory not in _registry_factory_ids():
        raise SafRefusal(FINDING_FACTORY_NOT_REGISTERED, f"{factory} is not a registry path_id")
    plants = _load_plants(plants_path, plant_count)
    _check_mill_plant_counts(mills, plants)
    return Catalog(
        catalog_id=catalog_id,
        directory=catalog_dir,
        factory=factory,
        plants_sha256=digest,
        plants=plants,
        mills=mills,
        meta=meta,
    )


# ``CATALOG.json`` string fields that must equal the package contract, in check order.
_PINNED_META = (
    ("format", CATALOG_FORMAT),
    ("factory", FACTORY),
    ("mill_prefix", MILL_PREFIX),
    ("record_kind", RECORD_KIND),
)


def _read_meta(meta_path: Path) -> Any:
    try:
        meta_text = meta_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise SafRefusal(FINDING_CATALOG_FILE_MISSING, f"{meta_path} is missing") from exc
    try:
        return load_strict_json(meta_text)
    except ValueError as exc:
        raise SafRefusal(
            FINDING_CATALOG_FIELD_INVALID, f"{CATALOG_FILENAME} is not strict JSON"
        ) from exc


def _require_meta_pins(meta: Any) -> tuple[str, str]:
    """``(catalog_id, factory)`` once the identity, contract, and quota pins hold."""

    catalog_id = _require_text(
        _field(meta, "catalog_id", str, CATALOG_FILENAME),
        f"{CATALOG_FILENAME}.catalog_id",
        FINDING_CATALOG_FIELD_INVALID,
    )
    for key, expected in _PINNED_META:
        if _field(meta, key, str, CATALOG_FILENAME) != expected:
            raise SafRefusal(
                FINDING_CATALOG_FIELD_INVALID, f"{CATALOG_FILENAME}.{key} must be {expected}"
            )
    quota = _field(meta, "quota_per_round", int, CATALOG_FILENAME)
    if isinstance(quota, bool) or quota != QUOTA_PER_ROUND:
        raise SafRefusal(
            FINDING_CATALOG_FIELD_INVALID,
            f"{CATALOG_FILENAME}.quota_per_round must be {QUOTA_PER_ROUND}",
        )
    return catalog_id, meta["factory"]


def _pinned_plants_digest(plants_path: Path, plants_sha256: str) -> str:
    try:
        plants_bytes = plants_path.read_bytes()
    except OSError as exc:
        raise SafRefusal(FINDING_CATALOG_FILE_MISSING, f"{plants_path} is missing") from exc
    digest = sha256_bytes(plants_bytes)
    if digest != plants_sha256:
        raise SafRefusal(
            FINDING_CATALOG_SHA256_MISMATCH,
            f"{PLANTS_FILENAME} digest {digest} != catalog pin {plants_sha256}",
        )
    return digest


def _load_plants(plants_path: Path, plant_count: int) -> tuple[Plant, ...]:
    """Every plants.jsonl row as a plant: the pinned count, no repeated plant_id."""

    rows = _read_jsonl(plants_path)
    if len(rows) != plant_count:
        raise SafRefusal(
            FINDING_CATALOG_FIELD_INVALID,
            f"{CATALOG_FILENAME}.plant_count is {plant_count}, file has {len(rows)}",
        )
    plants = tuple(
        _plant_from_row(row, f"{PLANTS_FILENAME}:{i}") for i, row in enumerate(rows, start=1)
    )
    seen: set[str] = set()
    for plant in plants:
        if plant.plant_id in seen:
            raise SafRefusal(FINDING_PLANT_DUPLICATE_ID, f"duplicate plant_id {plant.plant_id}")
        seen.add(plant.plant_id)
    return plants


def _check_mill_plant_counts(mills: tuple[Mill, ...], plants: tuple[Plant, ...]) -> None:
    by_mill: dict[str, int] = {}
    for plant in plants:
        by_mill[plant.mill_id] = by_mill.get(plant.mill_id, 0) + 1
    mill_ids = {mill.mill_id for mill in mills}
    if mill_ids != set(by_mill):
        raise SafRefusal(
            FINDING_CATALOG_FIELD_INVALID, "catalog mills do not match plant mill_id values"
        )
    for mill in mills:
        if by_mill[mill.mill_id] != mill.plant_count:
            raise SafRefusal(
                FINDING_CATALOG_FIELD_INVALID,
                f"{mill.mill_id} plant_count {mill.plant_count} != {by_mill[mill.mill_id]}",
            )


def catalog_check(directory: Path | None = None) -> list[dict[str, str]]:
    """Load the catalog. An invalid catalog is a refusal, not a finding list."""

    loaded = load_catalog(directory)
    if loaded.plants:
        return []
    return [{"code": FINDING_CATALOG_FIELD_INVALID, "detail": "empty catalog"}]


bind_import_twin(__name__)
