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
from typing import Any

from ._contract import (
    CATALOG_FILENAME,
    CATALOG_FORMAT,
    CATALOG_SLICE,
    EXTRACT_METHOD,
    FACTORY,
    FULL_MILL_COUNTS,
    FULL_PLANT_COUNT,
    SHAPE_LEGACY,
    SHAPE_LEFTOVER3,
    SHAPE_LLL,
    SHAPE_P_COOKIE,
    SHAPE_P_IDTOKEN,
    SOURCE_COMMIT,
    SOURCE_MILLS,
    SOURCE_REF,
    FINDING_CATALOG_FIELD_INVALID,
    FINDING_CATALOG_FIELD_MISSING,
    FINDING_CATALOG_FILE_MISSING,
    FINDING_CATALOG_SHA256_MISMATCH,
    FINDING_FACTORY_NOT_REGISTERED,
    FINDING_HOPPER_REFUSED,
    FINDING_LOOP_REFUSED,
    FINDING_MILL_NOT_FOUND,
    FINDING_PLANT_DUPLICATE_ID,
    FINDING_PLANT_FIELD_INVALID,
    FINDING_PLANT_FIELD_MISSING,
    FINDING_PLANT_NOT_FOUND,
    FINDING_SOURCE_NOT_PARSEABLE,
    HOPPER_DEF_NAMES,
    HOPPER_NAME_MARKERS,
    LOOP_NAME_MARKERS,
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


def _source_filename(source: str) -> str:
    return Path(source).name.lower()


def refuse_hopper_source(source: str) -> None:
    """Refuse dpr-lrd hoppers. They stay with dpr; this package never execs them."""

    name = _source_filename(source)
    hopper = any(marker in name for marker in HOPPER_NAME_MARKERS)
    refuse_when(
        hopper,
        FINDING_HOPPER_REFUSED,
        f"{source} is a dpr hopper; hopper exec stays with dpr",
    )


def _refuse_loop_source(source: str) -> None:
    name = _source_filename(source)
    loop = any(marker in name for marker in LOOP_NAME_MARKERS)
    refuse_when(
        loop,
        FINDING_LOOP_REFUSED,
        f"{source} is an lrd loop, not a mill catalog",
    )


def _const_eval(node: ast.AST) -> Any:
    """Literal values and keyword-only ``dict(...)`` calls. Never exec."""

    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.List):
        return [_const_eval(item) for item in node.elts]
    if isinstance(node, ast.Tuple):
        return tuple(_const_eval(item) for item in node.elts)
    if isinstance(node, ast.Dict):
        refuse_when(
            any(key is None for key in node.keys),
            FINDING_SOURCE_NOT_PARSEABLE,
            "pair source uses dict unpacking",
        )
        return {_const_eval(key): _const_eval(value) for key, value in zip(node.keys, node.values)}
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
            return {keyword.arg: _const_eval(keyword.value) for keyword in node.keywords}
        refuse(
            FINDING_SOURCE_NOT_PARSEABLE,
            f"pair source uses a non-literal call ({type(node).__name__})",
        )
    refuse(
        FINDING_SOURCE_NOT_PARSEABLE,
        f"pair source is not a constant ({type(node).__name__})",
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
    base = inferred_base if base_round is None else base_round
    if base is None:
        base = int(mill_id[len("lrd_r") :])
    refuse_when(
        not isinstance(base, int) or isinstance(base, bool) or base < 1,
        FINDING_PLANT_FIELD_INVALID,
        f"{source} BASE must be a positive int",
    )
    rows = []
    for index, raw in enumerate(raw_pairs):
        refuse_when(
            not isinstance(raw, dict),
            FINDING_SOURCE_NOT_PARSEABLE,
            f"{source} PAIRS[{index}] is not an object",
        )
        missing = [key for key in PAIR_KEYS if key not in raw]
        refuse_when(
            bool(missing),
            FINDING_PLANT_FIELD_MISSING,
            f"{source} PAIRS[{index}] missing {missing[0] if missing else ''}",
        )
        row = {
            "plant_id": f"{mill_id}:{raw['slug']}",
            "mill_id": mill_id,
            "source": source,
            "base_round": base,
        }
        row.update({key: raw[key] for key in PAIR_KEYS})
        rows.append(row)
    return tuple(rows)


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


def _require_text(value: Any, where: str, code: str) -> str:
    refuse_when(
        not isinstance(value, str) or not value.strip() or value != value.strip(),
        code,
        f"{where} must be a non-empty stripped string",
    )
    return value


def _plant_from_row(row: Any, where: str) -> Plant:
    refuse_when(
        not isinstance(row, dict),
        FINDING_PLANT_FIELD_INVALID,
        f"{where} must be an object",
    )
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
    base_round = row.get("base_round")
    refuse_when(
        not isinstance(base_round, int) or isinstance(base_round, bool) or base_round < 1,
        FINDING_PLANT_FIELD_INVALID,
        f"{where}.base_round must be a positive int",
    )
    shape = row.get("shape", SHAPE_LEGACY)
    refuse_when(
        not isinstance(shape, str) or shape
        not in {
            SHAPE_LEGACY,
            SHAPE_LEFTOVER3,
            SHAPE_P_IDTOKEN,
            SHAPE_P_COOKIE,
            SHAPE_LLL,
        },
        FINDING_PLANT_FIELD_INVALID,
        f"{where}.shape is not a supported extract shape",
    )
    source = _require_text(row.get("source"), f"{where}.source", FINDING_PLANT_FIELD_MISSING)
    if shape == SHAPE_LEGACY:
        fields = {
            key: _require_text(row.get(key), f"{where}.{key}", FINDING_PLANT_FIELD_MISSING)
            for key in PAIR_KEYS
        }
        return Plant(
            plant_id=plant_id,
            mill_id=mill_id,
            source=source,
            base_round=base_round,
            shape=shape,
            slug=slug,
            payload=None,
            mod=fields["mod"],
            drop=fields["drop"],
            stack=fields["stack"],
            field=fields["field"],
            naive=fields["naive"],
            conf=fields["conf"],
            conf2=fields["conf2"],
            oldc=fields["oldc"],
            newc=fields["newc"],
            old2=fields["old2"],
            new2=fields["new2"],
            test=fields["test"],
            ticket=fields["ticket"],
            fail=fields["fail"],
            domain=fields["domain"],
        )
    payload = row.get("payload")
    refuse_when(
        not isinstance(payload, dict),
        FINDING_PLANT_FIELD_INVALID,
        f"{where}.payload must be an object",
    )
    return Plant(
        plant_id=plant_id,
        mill_id=mill_id,
        source=source,
        base_round=base_round,
        shape=shape,
        slug=slug,
        payload=payload,
        mod="",
        drop="",
        stack="",
        field="",
        naive="",
        conf="",
        conf2="",
        oldc="",
        newc="",
        old2="",
        new2="",
        test="",
        ticket="",
        fail="",
        domain="",
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
    refuse_when(
        not isinstance(factories, list),
        FINDING_FACTORY_NOT_REGISTERED,
        "factory registry factories is not a list",
    )
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
    except OSError:
        refuse(FINDING_CATALOG_FILE_MISSING, f"{meta_path} is missing")
    try:
        meta = load_strict_json(meta_text)
    except ValueError:
        refuse(FINDING_CATALOG_FIELD_INVALID, f"{CATALOG_FILENAME} is not strict JSON")
    catalog_id = _require_text(
        _field(meta, "catalog_id", str, CATALOG_FILENAME),
        f"{CATALOG_FILENAME}.catalog_id",
        FINDING_CATALOG_FIELD_INVALID,
    )
    fmt = _field(meta, "format", str, CATALOG_FILENAME)
    refuse_when(
        fmt != CATALOG_FORMAT,
        FINDING_CATALOG_FIELD_INVALID,
        f"{CATALOG_FILENAME}.format must be {CATALOG_FORMAT}",
    )
    factory = _field(meta, "factory", str, CATALOG_FILENAME)
    refuse_when(
        factory != FACTORY,
        FINDING_CATALOG_FIELD_INVALID,
        f"{CATALOG_FILENAME}.factory must be {FACTORY}",
    )
    prefix = _field(meta, "mill_prefix", str, CATALOG_FILENAME)
    refuse_when(
        prefix != PREFIX,
        FINDING_CATALOG_FIELD_INVALID,
        f"{CATALOG_FILENAME}.mill_prefix must be {PREFIX}",
    )
    kind = _field(meta, "record_kind", str, CATALOG_FILENAME)
    refuse_when(
        kind != RECORD_KIND,
        FINDING_CATALOG_FIELD_INVALID,
        f"{CATALOG_FILENAME}.record_kind must be {RECORD_KIND}",
    )
    quota = _field(meta, "quota_per_round", int, CATALOG_FILENAME)
    refuse_when(
        isinstance(quota, bool) or quota != QUOTA_PER_ROUND,
        FINDING_CATALOG_FIELD_INVALID,
        f"{CATALOG_FILENAME}.quota_per_round must be {QUOTA_PER_ROUND}",
    )
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
    plants_sha256 = _field(meta, "plants_sha256", str, CATALOG_FILENAME)
    mill_rows = _field(meta, "mills", list, CATALOG_FILENAME)
    mills = tuple(
        _mill_from_row(row, f"{CATALOG_FILENAME}.mills[{i}]") for i, row in enumerate(mill_rows)
    )
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
    refuse_when(
        factory not in _registry_factory_ids(),
        FINDING_FACTORY_NOT_REGISTERED,
        f"{factory} is not a registry path_id",
    )
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
    by_mill: dict[str, int] = {}
    for plant in plants:
        by_mill[plant.mill_id] = by_mill.get(plant.mill_id, 0) + 1
    mill_ids = {mill.mill_id for mill in mills}
    refuse_when(
        mill_ids != set(by_mill),
        FINDING_CATALOG_FIELD_INVALID,
        "catalog mills do not match plant mill_id values",
    )
    if representative:
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
    else:
        for mill in mills:
            refuse_when(
                by_mill.get(mill.mill_id, 0) != mill.plant_count,
                FINDING_CATALOG_FIELD_INVALID,
                f"{mill.mill_id} plant_count {mill.plant_count} != {by_mill.get(mill.mill_id, 0)}",
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
