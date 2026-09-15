#!/usr/bin/env python3
"""AST-extract LHC catalog identity from a mill source.

Parses only literals and constructor arguments (``ast.parse``). There is no
``exec`` / ``eval`` / ``compile``, so ``lhc-mill*.py`` stay off this branch.
"""

from __future__ import annotations

import ast
import hashlib
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from .catalog_ast import (
    UNSET,
    assignment_of,
    call_kwargs,
    call_name,
    call_positional_literals,
    constant_fields,
    literal_value,
    name_id,
    plants_subscript_key,
    tuple_target_names,
)
from .vocabulary import (
    CATALOG_FILENAME,
    CATALOG_SCHEMA_ID,
    FACTORY,
    GENERATOR,
    KIND_PAIRS,
    LEGACY_REF,
    PRESERVE_COMMIT,
    SLICE_ID,
    SLICE_MILL_ID,
)

SHAPE_PAIRS_NAMED = "pairs-named"
SHAPE_PLANTS_NAMED = "plants-named"
SHAPE_PLANTS_P_FN = "plants-p-fn"
SHAPE_PLANTS_MK_FN = "plants-mk-fn"
SHAPE_PAIRS_FN_PAIR = "pairs-fn-pair"

_PAIR_FIELDS = (
    "title",
    "success_key",
    "fail_key",
    "success_slug",
    "fail_slug",
    "success_plant",
    "fail_plant",
)


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def mill_id_for_path(path: str) -> str:
    return Path(path).stem


def catalog_first_from_name(path: str) -> int | None:
    stem = Path(path).stem
    marker = stem.rsplit("-r", 1)
    if len(marker) != 2 or not marker[1].isdigit():
        return None
    return int(marker[1])


def extract_mill_catalog(
    source: str,
    *,
    path: str,
    blob_sha: str = "",
) -> dict[str, Any]:
    """Structured catalog extract for one mill source file."""

    payload = source.encode()
    tree = ast.parse(source, filename=path)
    mill_id = mill_id_for_path(path)
    constants = _module_constants(tree)
    factory = constants.get("FACTORY", FACTORY)
    generator = constants.get("GEN", GENERATOR)
    catalog_first = constants.get("CATALOG_FIRST")
    if not isinstance(catalog_first, int):
        catalog_first = catalog_first_from_name(path)
    record = _extract_shape(tree, path=path)
    record.update(
        {
            "mill_id": mill_id,
            "path": path,
            "blob_sha": blob_sha,
            "sha256": sha256_bytes(payload),
            "kind": KIND_PAIRS,
            "catalog_first": catalog_first,
            "generator": generator,
            "factory": factory,
        }
    )
    used_from = constants.get("USED_FROM")
    if isinstance(used_from, int):
        record["used_from"] = used_from
    return record


def _module_constants(tree: ast.AST) -> dict[str, Any]:
    env: dict[str, Any] = {}
    for node in getattr(tree, "body", ()):
        name, value = assignment_of(node)
        if name is None or value is None:
            continue
        resolved = literal_value(value, env)
        if resolved is not UNSET:
            env[name] = resolved
    return env


def _extract_shape(tree: ast.AST, *, path: str) -> dict[str, Any]:
    plants, plant_ctor = _plants_table(tree)
    wrappers = _wrapper_keys(tree)
    expand_plants = _expand_function_plants(tree)
    named_pairs = _named_or_fn_pairs(tree, plants, wrappers, expand_plants)
    if named_pairs is not None:
        shape = _pairs_shape(plants, plant_ctor, named_pairs)
        return _rows_record(shape, named_pairs, n_plants=_plant_count(plants, expand_plants))
    leftover = _fn_pair_appends(tree)
    if leftover is not None:
        return _rows_record(SHAPE_PAIRS_FN_PAIR, leftover, n_plants=len(leftover) * 2)
    raise ValueError(f"{path} has no extractable LHC catalog assignment")


def _plant_count(plants: Mapping[str, Mapping[str, Any]], expand_plants: Mapping[str, Any]) -> int:
    if plants:
        return len(plants)
    return len(expand_plants)


def _pairs_shape(
    plants: Mapping[str, Any],
    plant_ctor: str | None,
    rows: list[dict[str, Any]],
) -> str:
    uses_fn = any(
        isinstance(row.get("_left_kind"), str) and row["_left_kind"] == "fn" for row in rows
    )
    if uses_fn and plant_ctor == "mk":
        return SHAPE_PLANTS_MK_FN
    if uses_fn and plant_ctor == "P":
        return SHAPE_PLANTS_P_FN
    if plants:
        return SHAPE_PLANTS_NAMED
    return SHAPE_PAIRS_NAMED


def _plants_table(tree: ast.AST) -> tuple[dict[str, dict[str, Any]], str | None]:
    for node in getattr(tree, "body", ()):
        name, value = assignment_of(node)
        if name != "PLANTS" or not isinstance(value, ast.Dict):
            continue
        table: dict[str, dict[str, Any]] = {}
        ctor: str | None = None
        for key_node, value_node in zip(value.keys, value.values, strict=True):
            key = literal_value(key_node)
            if not isinstance(key, str):
                return {}, None
            identity = _plant_ctor_identity(value_node)
            if identity is None:
                return {}, None
            table[key] = identity
            ctor = call_name(value_node)
        return table, ctor
    return {}, None


def _plant_ctor_identity(node: ast.AST) -> dict[str, Any] | None:
    ctor = call_name(node)
    if ctor == "P":
        kwargs = call_kwargs(node)
        args = call_positional_literals(node)
        if kwargs is None or "slug" not in kwargs or "plant" not in kwargs:
            return None
        ok = args[0] if args else kwargs.get("ok")
        return {"slug": kwargs["slug"], "plant": kwargs["plant"], "ok": ok, "key": None}
    if ctor == "mk":
        args = call_positional_literals(node)
        if args is None or len(args) < 3:
            return None
        return {"ok": args[0], "slug": args[1], "plant": args[2], "key": None}
    return None


def _wrapper_keys(tree: ast.AST) -> dict[str, str]:
    """``def poetry_extras(rnd): return plant_from(rnd, PLANTS['poetry'])``."""

    wrappers: dict[str, str] = {}
    for node in getattr(tree, "body", ()):
        if not isinstance(node, ast.FunctionDef):
            continue
        for child in ast.walk(node):
            key = plants_subscript_key(child)
            if key is not None:
                wrappers[node.name] = key
                break
    return wrappers


def _expand_function_plants(tree: ast.AST) -> dict[str, dict[str, Any]]:
    """``def pnpm_peer(rnd): return expand(rnd, {'slug': ..., 'plant': ...})``."""

    plants: dict[str, dict[str, Any]] = {}
    for node in getattr(tree, "body", ()):
        if not isinstance(node, ast.FunctionDef):
            continue
        identity = _expand_identity(node)
        if identity is not None:
            plants[node.name] = identity
    return plants


def _expand_identity(fn: ast.FunctionDef) -> dict[str, Any] | None:
    for child in ast.walk(fn):
        if call_name(child) != "expand" or not isinstance(child, ast.Call):
            continue
        if len(child.args) < 2:
            continue
        fields = constant_fields(child.args[1])
        if fields is None or "slug" not in fields or "plant" not in fields:
            continue
        return {
            "slug": fields["slug"],
            "plant": fields["plant"],
            "ok": fields.get("success"),
            "key": fn.name,
        }
    return None


def _named_or_fn_pairs(
    tree: ast.AST,
    plants: Mapping[str, Mapping[str, Any]],
    wrappers: Mapping[str, str],
    expand_plants: Mapping[str, Mapping[str, Any]],
) -> list[dict[str, Any]] | None:
    for node in getattr(tree, "body", ()):
        name, value = assignment_of(node)
        if name != "LHC_PAIRS" or not isinstance(value, ast.List) or not value.elts:
            continue
        rows: list[dict[str, Any]] = []
        for elt in value.elts:
            row = _lhc_pair_identity(elt, plants, wrappers, expand_plants)
            if row is None:
                return None
            rows.append(row)
        return rows
    return None


def _lhc_pair_identity(
    node: ast.AST,
    plants: Mapping[str, Mapping[str, Any]],
    wrappers: Mapping[str, str],
    expand_plants: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any] | None:
    if not isinstance(node, ast.Tuple) or len(node.elts) != 6:
        return None
    title = literal_value(node.elts[0])
    if not isinstance(title, str):
        return None
    left_key, left_kind = _side_key(node.elts[1])
    right_key, right_kind = _side_key(node.elts[2])
    if left_key is None or right_key is None:
        return None
    success = _resolve_side(left_key, plants, wrappers, expand_plants)
    fail = _resolve_side(right_key, plants, wrappers, expand_plants)
    if success is None or fail is None:
        return None
    return {
        "title": title,
        "success_key": left_key if left_kind == "fn" else wrappers.get(left_key, left_key),
        "fail_key": right_key if right_kind == "fn" else wrappers.get(right_key, right_key),
        "success_slug": success["slug"],
        "fail_slug": fail["slug"],
        "success_plant": success["plant"],
        "fail_plant": fail["plant"],
        "_left_kind": left_kind,
    }


def _side_key(node: ast.AST) -> tuple[str | None, str]:
    if call_name(node) == "fn":
        args = call_positional_literals(node)
        if args and isinstance(args[0], str):
            return args[0], "fn"
        return None, "fn"
    named = name_id(node)
    if named is not None:
        return named, "name"
    return None, "unknown"


def _resolve_side(
    key: str,
    plants: Mapping[str, Mapping[str, Any]],
    wrappers: Mapping[str, str],
    expand_plants: Mapping[str, Mapping[str, Any]],
) -> Mapping[str, Any] | None:
    if key in plants:
        return plants[key]
    wrapped = wrappers.get(key)
    if wrapped is not None and wrapped in plants:
        return plants[wrapped]
    if key in expand_plants:
        return expand_plants[key]
    return None


def _fn_pair_appends(tree: ast.AST) -> list[dict[str, Any]] | None:
    """``fa, fb = fn_pair(...)`` followed by ``PAIRS.append((title, fa, fb, ...))``."""

    pending: list[Any] | None = None
    rows: list[dict[str, Any]] = []
    saw_empty = False
    for node in getattr(tree, "body", ()):
        name, value = assignment_of(node)
        if name == "PAIRS" and isinstance(value, ast.List) and not value.elts:
            saw_empty = True
            continue
        targets = tuple_target_names(node)
        if targets == ("fa", "fb") and isinstance(node, ast.Assign):
            if call_name(node.value) != "fn_pair":
                return None
            args = call_positional_literals(node.value)
            if args is None or len(args) < 4:
                return None
            if not all(isinstance(item, str) for item in args[:4]):
                return None
            pending = args
            continue
        if not isinstance(node, ast.Expr) or not isinstance(node.value, ast.Call):
            continue
        call = node.value
        if not isinstance(call.func, ast.Attribute) or call.func.attr != "append":
            continue
        if name_id(call.func.value) != "PAIRS":
            continue
        if pending is None or len(call.args) != 1 or not isinstance(call.args[0], ast.Tuple):
            return None
        title = literal_value(call.args[0].elts[0]) if call.args[0].elts else UNSET
        if not isinstance(title, str):
            return None
        rows.append(
            {
                "title": title,
                "success_key": pending[2],
                "fail_key": pending[3],
                "success_slug": pending[0],
                "fail_slug": pending[1],
                "success_plant": pending[2],
                "fail_plant": pending[3],
                "_left_kind": "fn_pair",
            }
        )
        pending = None
    if not saw_empty or not rows:
        return None
    return rows


def _rows_record(shape: str, rows: list[dict[str, Any]], *, n_plants: int) -> dict[str, Any]:
    cleaned = [{field: row[field] for field in _PAIR_FIELDS} for row in rows]
    return {
        "shape": shape,
        "n_rows": len(cleaned),
        "n_plants": n_plants,
        "first_slug": cleaned[0]["success_slug"],
        "last_slug": cleaned[-1]["success_slug"],
        "pairs": cleaned,
    }


def mill_summary(record: Mapping[str, Any], *, include_pairs: bool) -> dict[str, Any]:
    """Catalog mill row: identity plus optional compact pair list."""

    summary = {
        "mill_id": record["mill_id"],
        "path": record["path"],
        "blob_sha": record["blob_sha"],
        "sha256": record["sha256"],
        "kind": record["kind"],
        "shape": record["shape"],
        "catalog_first": record["catalog_first"],
        "n_rows": record["n_rows"],
        "n_plants": record["n_plants"],
        "first_slug": record["first_slug"],
        "last_slug": record["last_slug"],
        "generator": record["generator"],
        "factory": record["factory"],
    }
    if "used_from" in record:
        summary["used_from"] = record["used_from"]
    if include_pairs:
        summary["pairs"] = list(record.get("pairs") or ())
    return summary


def catalog_document(mills: list[dict[str, Any]]) -> dict[str, Any]:
    pair_rows = sum(mill["n_rows"] for mill in mills)
    plant_rows = sum(mill["n_plants"] for mill in mills)
    return {
        "schema": CATALOG_SCHEMA_ID,
        "source_ref": LEGACY_REF,
        "preserve_commit": PRESERVE_COMMIT,
        "factory": FACTORY,
        "generator": GENERATOR,
        "slice": SLICE_ID,
        "n_mills": len(mills),
        "n_pair_rows": pair_rows,
        "n_plant_rows": plant_rows,
        "mills": {mill["mill_id"]: mill for mill in mills},
    }


def dumps_catalog(document: Mapping[str, Any]) -> str:
    return json.dumps(document, ensure_ascii=True, indent=2, sort_keys=True) + "\n"


def catalog_json_path(package_dir: Path | None = None) -> Path:
    root = package_dir if package_dir is not None else Path(__file__).resolve().parent
    return root / CATALOG_FILENAME


def write_catalog_document(document: Mapping[str, Any], path: Path | None = None) -> Path:
    destination = path if path is not None else catalog_json_path()
    destination.write_text(dumps_catalog(document), encoding="utf-8")
    return destination


def is_slice_mill(mill_id: str) -> bool:
    return mill_id == SLICE_MILL_ID
