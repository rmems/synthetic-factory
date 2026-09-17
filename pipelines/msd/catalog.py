#!/usr/bin/env python3
"""Pinned MSD plant catalog: load, pin, and AST-extract (never exec).

A catalog directory holds ``CATALOG.json`` (identity, factory, mill pins)
and ``plants.jsonl`` (one leftover surface per line). Load verifies the
plants digest and every required field before a plant is trusted.
Historical leftover mill scripts are read only as text through
:func:`plants_from_source`. ``P(**kwargs)`` and ``dict(**kwargs)`` calls
in ``PAIRS`` are constant-folded; the leftover-loop publisher is not a
catalog source.
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
    MILL_PREFIX,
    MsdRefusal,
    PLANTS_FILENAME,
    QUOTA_PER_ROUND,
    RECORD_KIND,
    bind_import_twin,
    load_strict_json,
    repo_root,
)

PLANT_KEYS = (
    "slug",
    "repo",
    "method",
    "leftover",
    "spec",
    "keep",
    "deadend",
    "extra",
    "freeze_still",
    "not_r",
    "adapt_cmd",
    "canon",
    "pfx",
    "grep",
    "ticket",
    "family",
    "schema_note",
    "peer",
)
R430_KEYS = (
    "slug",
    "repo",
    "method",
    "leftover",
    "spec",
    "keep",
    "deadend",
    "extra",
    "freeze_still",
    "not_r",
    "adapt_cmd",
    "canon",
    "pfx",
    "grep",
    "ticket",
    "family",
    "schema_note",
)
R747_KEYS = (
    "slug",
    "old",
    "new",
    "keep",
    "dead",
    "residual",
    "extra",
    "freeze",
    "family",
    "reject",
    "method",
    "peer",
    "ticket",
    "canon",
    "wid",
    "test_ok",
    "falseg",
    "map_fn",
    "success",
)
PLANT_CALLS = frozenset({"P", "dict"})
MILL_ID_RE = re.compile(r"^msd_r[0-9]+$")
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
    """One MCP leftover surface: old protocol shape versus required spec."""

    plant_id: str
    mill_id: str
    source: str
    base_round: int
    slug: str
    repo: str
    method: str
    leftover: str
    spec: str
    keep: str
    deadend: str
    extra: str
    freeze_still: str
    not_r: str
    adapt_cmd: str
    canon: str
    pfx: str
    grep: str
    ticket: str
    family: str
    schema_note: str
    peer: str


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
        raise MsdRefusal(FINDING_PLANT_NOT_FOUND, f"no plant {plant_id!r} in the catalog")

    def mill_plants(self, mill_id: str) -> tuple[Plant, ...]:
        found = tuple(item for item in self.plants if item.mill_id == mill_id)
        if not found:
            raise MsdRefusal(FINDING_MILL_NOT_FOUND, f"no mill {mill_id!r} in the catalog")
        return found


def default_catalog_dir() -> Path:
    return repo_root() / "config" / "msd"


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _const_eval(node: ast.AST) -> Any:
    """Literal values only. Refuses names, starred dicts, and unknown calls."""

    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.List):
        return [_const_eval(item) for item in node.elts]
    if isinstance(node, ast.Tuple):
        return tuple(_const_eval(item) for item in node.elts)
    if isinstance(node, ast.Set):
        return {_const_eval(item) for item in node.elts}
    if isinstance(node, ast.Dict):
        if any(key is None for key in node.keys):
            raise MsdRefusal(FINDING_SOURCE_NOT_PARSEABLE, "plant source uses dict unpacking")
        return {_const_eval(key): _const_eval(value) for key, value in zip(node.keys, node.values)}
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        return -_const_eval(node.operand)
    raise MsdRefusal(
        FINDING_SOURCE_NOT_PARSEABLE,
        f"plant source is not a constant ({type(node).__name__})",
    )


def _call_kwargs(node: ast.AST, where: str) -> dict[str, Any]:
    if (
        not isinstance(node, ast.Call)
        or not isinstance(node.func, ast.Name)
        or node.func.id not in PLANT_CALLS
        or node.args
        or any(kw.arg is None for kw in node.keywords)
    ):
        raise MsdRefusal(
            FINDING_SOURCE_NOT_PARSEABLE, f"{where} is not a constant P()/dict() call"
        )
    return {kw.arg: _const_eval(kw.value) for kw in node.keywords}


def _assigned_name(node: ast.AST) -> tuple[str, ast.AST] | None:
    if isinstance(node, ast.Assign) and len(node.targets) == 1:
        target = node.targets[0]
        if isinstance(target, ast.Name):
            return target.id, node.value
    if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
        if node.value is not None:
            return node.target.id, node.value
    return None


def _normalize_r430(raw: dict[str, Any], where: str) -> dict[str, Any]:
    missing = [key for key in R430_KEYS if key not in raw]
    if missing:
        raise MsdRefusal(FINDING_PLANT_FIELD_MISSING, f"{where} missing {missing[0]}")
    row = {key: raw[key] for key in R430_KEYS}
    row["peer"] = raw.get("peer", raw["method"])
    return row


def _normalize_r747(raw: dict[str, Any], where: str) -> dict[str, Any]:
    missing = [key for key in R747_KEYS if key not in raw]
    if missing:
        raise MsdRefusal(FINDING_PLANT_FIELD_MISSING, f"{where} missing {missing[0]}")
    success = raw["success"]
    if type(success) is not bool:
        raise MsdRefusal(FINDING_PLANT_FIELD_INVALID, f"{where}.success must be a bool")
    return {
        "slug": raw["slug"],
        "repo": "repo-mcp" if success else "llm-mcp",
        "method": raw["method"],
        "leftover": raw["old"],
        "spec": raw["new"],
        "keep": raw["keep"],
        "deadend": raw["dead"],
        "extra": raw["extra"],
        "freeze_still": raw["freeze"],
        "not_r": "prior leftover clones",
        "adapt_cmd": raw["reject"],
        "canon": raw["canon"],
        "pfx": raw["wid"],
        "grep": f"{raw['method']}|{raw['peer']}",
        "ticket": raw["ticket"],
        "family": raw["family"],
        "schema_note": raw["family"],
        "peer": raw["peer"],
    }


def _normalize_unified(raw: dict[str, Any], where: str) -> dict[str, Any]:
    if all(key in raw for key in R430_KEYS):
        return _normalize_r430(raw, where)
    if all(key in raw for key in R747_KEYS):
        return _normalize_r747(raw, where)
    if all(key in raw for key in PLANT_KEYS):
        return {key: raw[key] for key in PLANT_KEYS}
    raise MsdRefusal(
        FINDING_SOURCE_NOT_PARSEABLE,
        f"{where} is not an r430, r747, or unified plant",
    )


def _pairs_payload(tree: ast.Module) -> ast.AST | None:
    for node in tree.body:
        assigned = _assigned_name(node)
        if assigned is not None and assigned[0] == "PAIRS":
            return assigned[1]
    return None


def _plants_payload(tree: ast.Module) -> ast.AST | None:
    for node in tree.body:
        assigned = _assigned_name(node)
        if assigned is not None and assigned[0] == "PLANTS":
            return assigned[1]
    return None


def _extract_pair_elts(payload: ast.AST, source: str) -> list[dict[str, Any]]:
    if not isinstance(payload, (ast.List, ast.Tuple)) or not payload.elts:
        raise MsdRefusal(FINDING_SOURCE_NOT_PARSEABLE, f"{source} has no PAIRS/PLANTS list")
    rows: list[dict[str, Any]] = []
    for index, item in enumerate(payload.elts):
        if isinstance(item, (ast.Tuple, ast.List)):
            if len(item.elts) != 2:
                raise MsdRefusal(
                    FINDING_SOURCE_NOT_PARSEABLE, f"{source} PAIRS[{index}] is not a pair"
                )
            for side, node in (("adapt", item.elts[0]), ("freeze", item.elts[1])):
                where = f"{source} PAIRS[{index}].{side}"
                rows.append(_normalize_unified(_call_kwargs(node, where), where))
            continue
        if isinstance(item, ast.Call):
            where = f"{source} PAIRS[{index}]"
            rows.append(_normalize_unified(_call_kwargs(item, where), where))
            continue
        if isinstance(item, ast.Dict):
            where = f"{source} PLANTS[{index}]"
            rows.append(_normalize_unified(_const_eval(item), where))
            continue
        raise MsdRefusal(
            FINDING_SOURCE_NOT_PARSEABLE,
            f"{source} catalog[{index}] is not a pair, P()/dict() call, or object",
        )
    return rows


def _inferred_base(tree: ast.Module, mill_id: str) -> int:
    inferred: Any = None
    for node in tree.body:
        assigned = _assigned_name(node)
        if assigned is None:
            continue
        name, value = assigned
        if name in {"BASE", "START"}:
            inferred = _const_eval(value)
    if inferred is None:
        inferred = int(mill_id[len("msd_r") :])
    if not isinstance(inferred, int) or isinstance(inferred, bool) or inferred < 1:
        raise MsdRefusal(FINDING_PLANT_FIELD_INVALID, "BASE/START must be a positive int")
    return inferred


def plants_from_source(
    text: str,
    *,
    mill_id: str,
    source: str,
    base_round: int | None = None,
) -> tuple[dict[str, Any], ...]:
    """AST-extract leftover surfaces from mill source text. Never exec."""

    try:
        tree = ast.parse(text)
    except SyntaxError as exc:
        raise MsdRefusal(
            FINDING_SOURCE_NOT_PARSEABLE, f"{source} does not parse: {exc}"
        ) from exc
    if not isinstance(tree, ast.Module):
        raise MsdRefusal(FINDING_SOURCE_NOT_PARSEABLE, f"{source} is not a module")
    payload = _pairs_payload(tree) or _plants_payload(tree)
    if payload is None:
        raise MsdRefusal(FINDING_SOURCE_NOT_PARSEABLE, f"{source} has no PAIRS or PLANTS list")
    if not MILL_ID_RE.fullmatch(mill_id):
        raise MsdRefusal(FINDING_PLANT_FIELD_INVALID, f"mill_id {mill_id!r} is not msd_rNNN")
    base = _inferred_base(tree, mill_id) if base_round is None else base_round
    if not isinstance(base, int) or isinstance(base, bool) or base < 1:
        raise MsdRefusal(FINDING_PLANT_FIELD_INVALID, f"{source} BASE must be a positive int")
    raw_rows = _extract_pair_elts(payload, source)
    rows = []
    for raw in raw_rows:
        row = {
            "plant_id": f"{mill_id}:{raw['slug']}",
            "mill_id": mill_id,
            "source": source,
            "base_round": base,
        }
        row.update(raw)
        rows.append(row)
    return tuple(rows)


def _field(mapping: Any, key: str, kinds: type | tuple[type, ...], where: str) -> Any:
    if not isinstance(mapping, dict):
        raise MsdRefusal(FINDING_CATALOG_FIELD_INVALID, f"{where} must be an object")
    if key not in mapping:
        raise MsdRefusal(FINDING_CATALOG_FIELD_MISSING, f"{where}.{key} is missing")
    value = mapping[key]
    if isinstance(value, bool) and kinds is not bool:
        raise MsdRefusal(FINDING_CATALOG_FIELD_INVALID, f"{where}.{key} has the wrong type")
    if not isinstance(value, kinds):
        raise MsdRefusal(FINDING_CATALOG_FIELD_INVALID, f"{where}.{key} has the wrong type")
    return value


def _require_text(value: Any, where: str, code: str) -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise MsdRefusal(code, f"{where} must be a non-empty stripped string")
    return value


def _plant_from_row(row: Any, where: str) -> Plant:
    if not isinstance(row, dict):
        raise MsdRefusal(FINDING_PLANT_FIELD_INVALID, f"{where} must be an object")
    mill_id = _require_text(row.get("mill_id"), f"{where}.mill_id", FINDING_PLANT_FIELD_INVALID)
    slug = _require_text(row.get("slug"), f"{where}.slug", FINDING_PLANT_FIELD_INVALID)
    if not MILL_ID_RE.fullmatch(mill_id):
        raise MsdRefusal(FINDING_PLANT_FIELD_INVALID, f"{where}.mill_id is not msd_rNNN")
    if not SLUG_RE.fullmatch(slug):
        raise MsdRefusal(FINDING_PLANT_FIELD_INVALID, f"{where}.slug is not a plant slug")
    plant_id = _require_text(row.get("plant_id"), f"{where}.plant_id", FINDING_PLANT_FIELD_INVALID)
    expected = f"{mill_id}:{slug}"
    if plant_id != expected:
        raise MsdRefusal(FINDING_PLANT_FIELD_INVALID, f"{where}.plant_id must be {expected!r}")
    base_round = row.get("base_round")
    if not isinstance(base_round, int) or isinstance(base_round, bool) or base_round < 1:
        raise MsdRefusal(FINDING_PLANT_FIELD_INVALID, f"{where}.base_round must be a positive int")
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
        repo=fields["repo"],
        method=fields["method"],
        leftover=fields["leftover"],
        spec=fields["spec"],
        keep=fields["keep"],
        deadend=fields["deadend"],
        extra=fields["extra"],
        freeze_still=fields["freeze_still"],
        not_r=fields["not_r"],
        adapt_cmd=fields["adapt_cmd"],
        canon=fields["canon"],
        pfx=fields["pfx"],
        grep=fields["grep"],
        ticket=fields["ticket"],
        family=fields["family"],
        schema_note=fields["schema_note"],
        peer=fields["peer"],
    )


def _mill_from_row(row: Any, where: str) -> Mill:
    mill_id = _require_text(
        _field(row, "mill_id", str, where), f"{where}.mill_id", FINDING_CATALOG_FIELD_INVALID
    )
    if not MILL_ID_RE.fullmatch(mill_id):
        raise MsdRefusal(FINDING_CATALOG_FIELD_INVALID, f"{where}.mill_id is not msd_rNNN")
    base_round = _field(row, "base_round", int, where)
    if isinstance(base_round, bool) or base_round < 1:
        raise MsdRefusal(
            FINDING_CATALOG_FIELD_INVALID, f"{where}.base_round must be a positive int"
        )
    plant_count = _field(row, "plant_count", int, where)
    if isinstance(plant_count, bool) or plant_count < 1:
        raise MsdRefusal(
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
        raise MsdRefusal(FINDING_CATALOG_FILE_MISSING, f"{path} is unreadable: {exc}") from exc
    if not text.endswith("\n") or "\r" in text:
        raise MsdRefusal(FINDING_CATALOG_FIELD_INVALID, f"{path.name} must be LF-framed jsonl")
    rows = []
    for index, line in enumerate(text.splitlines(), start=1):
        if not line:
            raise MsdRefusal(FINDING_CATALOG_FIELD_INVALID, f"{path.name}:{index} is empty")
        try:
            rows.append(load_strict_json(line))
        except ValueError as exc:
            raise MsdRefusal(
                FINDING_CATALOG_FIELD_INVALID, f"{path.name}:{index} is not strict JSON"
            ) from exc
    return tuple(rows)


def _registry_factory_ids() -> set[str]:
    path = repo_root() / "config" / "FACTORY-REGISTRY.json"
    try:
        payload = load_strict_json(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise MsdRefusal(
            FINDING_FACTORY_NOT_REGISTERED, f"factory registry is unreadable: {exc}"
        ) from exc
    factories = payload.get("factories") if isinstance(payload, dict) else None
    if not isinstance(factories, list):
        raise MsdRefusal(FINDING_FACTORY_NOT_REGISTERED, "factory registry factories is not a list")
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
        raise MsdRefusal(FINDING_CATALOG_FILE_MISSING, f"{meta_path} is missing") from exc
    try:
        meta = load_strict_json(meta_text)
    except ValueError as exc:
        raise MsdRefusal(
            FINDING_CATALOG_FIELD_INVALID, f"{CATALOG_FILENAME} is not strict JSON"
        ) from exc
    catalog_id = _require_text(
        _field(meta, "catalog_id", str, CATALOG_FILENAME),
        f"{CATALOG_FILENAME}.catalog_id",
        FINDING_CATALOG_FIELD_INVALID,
    )
    fmt = _field(meta, "format", str, CATALOG_FILENAME)
    if fmt != CATALOG_FORMAT:
        raise MsdRefusal(
            FINDING_CATALOG_FIELD_INVALID,
            f"{CATALOG_FILENAME}.format must be {CATALOG_FORMAT}",
        )
    factory = _field(meta, "factory", str, CATALOG_FILENAME)
    if factory != FACTORY:
        raise MsdRefusal(
            FINDING_CATALOG_FIELD_INVALID, f"{CATALOG_FILENAME}.factory must be {FACTORY}"
        )
    prefix = _field(meta, "mill_prefix", str, CATALOG_FILENAME)
    if prefix != MILL_PREFIX:
        raise MsdRefusal(
            FINDING_CATALOG_FIELD_INVALID,
            f"{CATALOG_FILENAME}.mill_prefix must be {MILL_PREFIX}",
        )
    kind = _field(meta, "record_kind", str, CATALOG_FILENAME)
    if kind != RECORD_KIND:
        raise MsdRefusal(
            FINDING_CATALOG_FIELD_INVALID,
            f"{CATALOG_FILENAME}.record_kind must be {RECORD_KIND}",
        )
    quota = _field(meta, "quota_per_round", int, CATALOG_FILENAME)
    if isinstance(quota, bool) or quota != QUOTA_PER_ROUND:
        raise MsdRefusal(
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
        raise MsdRefusal(FINDING_CATALOG_FILE_MISSING, f"{plants_path} is missing") from exc
    digest = sha256_bytes(plants_bytes)
    if digest != plants_sha256:
        raise MsdRefusal(
            FINDING_CATALOG_SHA256_MISMATCH,
            f"{PLANTS_FILENAME} digest {digest} != catalog pin {plants_sha256}",
        )
    if factory not in _registry_factory_ids():
        raise MsdRefusal(FINDING_FACTORY_NOT_REGISTERED, f"{factory} is not a registry path_id")
    rows = _read_jsonl(plants_path)
    if len(rows) != plant_count:
        raise MsdRefusal(
            FINDING_CATALOG_FIELD_INVALID,
            f"{CATALOG_FILENAME}.plant_count is {plant_count}, file has {len(rows)}",
        )
    plants = tuple(
        _plant_from_row(row, f"{PLANTS_FILENAME}:{i}") for i, row in enumerate(rows, start=1)
    )
    seen: set[str] = set()
    for plant in plants:
        if plant.plant_id in seen:
            raise MsdRefusal(FINDING_PLANT_DUPLICATE_ID, f"duplicate plant_id {plant.plant_id}")
        seen.add(plant.plant_id)
    by_mill: dict[str, int] = {}
    for plant in plants:
        by_mill[plant.mill_id] = by_mill.get(plant.mill_id, 0) + 1
    mill_ids = {mill.mill_id for mill in mills}
    if mill_ids != set(by_mill):
        raise MsdRefusal(
            FINDING_CATALOG_FIELD_INVALID, "catalog mills do not match plant mill_id values"
        )
    for mill in mills:
        if by_mill[mill.mill_id] != mill.plant_count:
            raise MsdRefusal(
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
