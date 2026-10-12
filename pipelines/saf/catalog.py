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
    """Literal values and keyword-only ``dict(...)`` calls. Never exec.

    Nested values recurse straight back into this function, one frame per level
    (two for a tuple's generator) as before; the helpers it calls never recurse.
    """

    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, (ast.List, ast.Tuple)):
        return (
            list(map(_const_eval, node.elts))
            if isinstance(node, ast.List)
            else tuple(_const_eval(item) for item in node.elts)
        )
    literal = _literal_dict_parts(node)
    if literal is not None:
        return dict(zip(map(_const_eval, literal[0]), map(_const_eval, literal[1])))
    call = _dict_call_parts(node)
    if call is not None:
        return dict(zip(call[0], map(_const_eval, call[1])))
    operand = _negated_operand(node)
    if operand is None:
        raise SafRefusal(FINDING_SOURCE_NOT_PARSEABLE, _not_literal_message(node))
    return -_const_eval(operand)


def _literal_dict_parts(node: ast.AST) -> tuple[list[ast.expr], list[ast.expr]] | None:
    """Key and value nodes of a ``{...}`` literal without ``**`` unpacking."""

    if not isinstance(node, ast.Dict):
        return None
    keys = [key for key in node.keys if key is not None]
    return (keys, node.values) if len(keys) == len(node.keys) else None


def _dict_call_parts(node: ast.AST) -> tuple[list[str | None], list[ast.expr]] | None:
    """Names and value nodes of a keyword-only ``dict(...)`` call."""

    if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Name):
        return None
    names = [keyword.arg for keyword in node.keywords]
    if node.func.id != "dict" or node.args or None in names:
        return None
    return names, [keyword.value for keyword in node.keywords]


def _negated_operand(node: ast.AST) -> ast.expr | None:
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        return node.operand
    return None


def _not_literal_message(node: ast.AST) -> str:
    """``**`` in a dict, a call other than ``dict(k=v)``, or any other node kind."""

    if isinstance(node, ast.Dict):
        return "pair source uses dict unpacking"
    if isinstance(node, ast.Call):
        return f"pair source uses a non-literal call ({type(node).__name__})"
    return f"pair source is not a constant ({type(node).__name__})"


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


def plants_from_source(
    text: str,
    *,
    mill_id: str,
    source: str,
    base_round: int | None = None,
) -> tuple[dict[str, Any], ...]:
    """AST-extract ``PAIRS`` from leftover-mill source text. Never exec."""

    raw_pairs, inferred_base = _parse_pairs_and_base(text, source)
    if not isinstance(raw_pairs, list) or not raw_pairs:
        raise SafRefusal(FINDING_SOURCE_NOT_PARSEABLE, f"{source} has no PAIRS list")
    base = _checked_base_round(mill_id, source, inferred_base, base_round)
    return _pair_rows(raw_pairs, mill_id, source, base)


def _parse_pairs_and_base(text: str, source: str) -> tuple[Any, Any]:
    """Parse the mill text; literal ``PAIRS`` and ``BASE``, the last of each wins."""

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
    return raw_pairs, inferred_base


def _checked_base_round(
    mill_id: str, source: str, inferred_base: Any, base_round: int | None
) -> int:
    """A ``saf_rNNN`` mill id and its positive base round."""

    if not MILL_ID_RE.fullmatch(mill_id):
        raise SafRefusal(FINDING_PLANT_FIELD_INVALID, f"mill_id {mill_id!r} is not saf_rNNN")
    base = inferred_base if base_round is None else base_round
    if base is None:
        base = int(mill_id[len("saf_r") :])
    if not isinstance(base, int) or isinstance(base, bool) or base < 1:
        raise SafRefusal(FINDING_PLANT_FIELD_INVALID, f"{source} BASE must be a positive int")
    return base


def _pair_rows(
    raw_pairs: list[Any], mill_id: str, source: str, base: int
) -> tuple[dict[str, Any], ...]:
    """One catalog row per ``PAIRS`` object, refusing a non-object or a missing key."""

    rows = []
    for index, raw in enumerate(raw_pairs):
        _require_pair_object(raw, index, source)
        row = {
            "plant_id": f"{mill_id}:{raw['slug']}",
            "mill_id": mill_id,
            "source": source,
            "base_round": base,
        }
        row.update({key: raw[key] for key in PAIR_KEYS})
        rows.append(row)
    return tuple(rows)


def _require_pair_object(raw: Any, index: int, source: str) -> None:
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
    plant_id = _checked_plant_id(row, where, mill_id, slug)
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


def _checked_plant_id(row: dict[str, Any], where: str, mill_id: str, slug: str) -> str:
    """Well-formed mill_id and slug, and a plant_id that joins them."""

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
    return plant_id


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
    rows = [row for row in factories if isinstance(row, dict)]
    return {row["path_id"] for row in rows if isinstance(row.get("path_id"), str)}


def load_catalog(directory: Path | None = None) -> Catalog:
    """Load a catalog directory and refuse unless every pin holds."""

    catalog_dir = Path(default_catalog_dir() if directory is None else directory)
    meta_path = catalog_dir / CATALOG_FILENAME
    plants_path = catalog_dir / PLANTS_FILENAME
    meta, catalog_id = _read_pair_meta(meta_path)
    factory = _require_pair_contract(meta)
    plant_count = _field(meta, "plant_count", int, CATALOG_FILENAME)
    plants_sha256 = _field(meta, "plants_sha256", str, CATALOG_FILENAME)
    mill_rows = _field(meta, "mills", list, CATALOG_FILENAME)
    mills = tuple(
        _mill_from_row(row, f"{CATALOG_FILENAME}.mills[{i}]") for i, row in enumerate(mill_rows)
    )
    digest = _registered_digest(plants_path, plants_sha256, factory)
    plants = _pair_plants(plants_path, plant_count)
    _check_unique_and_counted(plants, mills)
    return Catalog(
        catalog_id=catalog_id,
        directory=catalog_dir,
        factory=factory,
        plants_sha256=digest,
        plants=plants,
        mills=mills,
        meta=meta,
    )


def _read_pair_meta(meta_path: Path) -> tuple[Any, str]:
    """Strict CATALOG.json with a catalog_id and the pinned format."""

    try:
        meta_text = meta_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise SafRefusal(FINDING_CATALOG_FILE_MISSING, f"{meta_path} is missing") from exc
    try:
        meta = load_strict_json(meta_text)
    except ValueError as exc:
        raise SafRefusal(
            FINDING_CATALOG_FIELD_INVALID, f"{CATALOG_FILENAME} is not strict JSON"
        ) from exc
    catalog_id = _require_text(
        _field(meta, "catalog_id", str, CATALOG_FILENAME),
        f"{CATALOG_FILENAME}.catalog_id",
        FINDING_CATALOG_FIELD_INVALID,
    )
    fmt = _field(meta, "format", str, CATALOG_FILENAME)
    if fmt != CATALOG_FORMAT:
        raise SafRefusal(
            FINDING_CATALOG_FIELD_INVALID,
            f"{CATALOG_FILENAME}.format must be {CATALOG_FORMAT}",
        )
    return meta, catalog_id


def _require_pair_contract(meta: Any) -> str:
    """The factory, mill prefix, record kind, and quota pins."""

    factory = _field(meta, "factory", str, CATALOG_FILENAME)
    if factory != FACTORY:
        raise SafRefusal(
            FINDING_CATALOG_FIELD_INVALID, f"{CATALOG_FILENAME}.factory must be {FACTORY}"
        )
    prefix = _field(meta, "mill_prefix", str, CATALOG_FILENAME)
    if prefix != MILL_PREFIX:
        raise SafRefusal(
            FINDING_CATALOG_FIELD_INVALID,
            f"{CATALOG_FILENAME}.mill_prefix must be {MILL_PREFIX}",
        )
    kind = _field(meta, "record_kind", str, CATALOG_FILENAME)
    if kind != RECORD_KIND:
        raise SafRefusal(
            FINDING_CATALOG_FIELD_INVALID,
            f"{CATALOG_FILENAME}.record_kind must be {RECORD_KIND}",
        )
    quota = _field(meta, "quota_per_round", int, CATALOG_FILENAME)
    if isinstance(quota, bool) or quota != QUOTA_PER_ROUND:
        raise SafRefusal(
            FINDING_CATALOG_FIELD_INVALID,
            f"{CATALOG_FILENAME}.quota_per_round must be {QUOTA_PER_ROUND}",
        )
    return factory


def _registered_digest(plants_path: Path, plants_sha256: str, factory: str) -> str:
    """plants.jsonl matches its pin and the factory is a registry path_id."""

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
    if factory not in _registry_factory_ids():
        raise SafRefusal(FINDING_FACTORY_NOT_REGISTERED, f"{factory} is not a registry path_id")
    return digest


def _pair_plants(plants_path: Path, plant_count: int) -> tuple[Plant, ...]:
    rows = _read_jsonl(plants_path)
    if len(rows) != plant_count:
        raise SafRefusal(
            FINDING_CATALOG_FIELD_INVALID,
            f"{CATALOG_FILENAME}.plant_count is {plant_count}, file has {len(rows)}",
        )
    plants = tuple(
        _plant_from_row(row, f"{PLANTS_FILENAME}:{i}") for i, row in enumerate(rows, start=1)
    )
    return plants


def _check_unique_and_counted(plants: tuple[Plant, ...], mills: tuple[Mill, ...]) -> None:
    """Unique plant ids, and per-mill counts that match the catalog mills."""

    seen: set[str] = set()
    for plant in plants:
        if plant.plant_id in seen:
            raise SafRefusal(FINDING_PLANT_DUPLICATE_ID, f"duplicate plant_id {plant.plant_id}")
        seen.add(plant.plant_id)
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
