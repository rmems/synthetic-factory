#!/usr/bin/env python3
"""AST-extract EVH catalog identity from a plant-gen source.

Evaluates only literal catalog assignments, closed ``str`` methods, and
``catalog`` / ``add`` / ``add_row`` / ``emit`` call graphs. Does not import,
compile, or exec the plant-gen or ``scripts/eval_harness_unique_mill``.
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
    extract_joined_path_assignment,
    function_named,
    joined_path_constant,
    require,
    resolve,
)
from .vocabulary import (
    CATALOG_FILENAME,
    CATALOG_SCHEMA_ID,
    FACTORY,
    GENERATOR,
    KIND_GEN,
    LEGACY_REF,
    PRESERVE_COMMIT,
    SHAPE_ADD_TABLES,
    SHAPE_FSTRING,
    SHAPE_PARAM,
    SHAPE_RAW,
    SLICE_ID,
)

_CATALOG_PARAMS = ("tag", "to", "kw1", "kw2", "kw3")
_EMIT_FIELDS = (
    "mod",
    "tag",
    "to",
    "kw1",
    "kw2",
    "kw3",
    "offset",
    "void_base",
    "start_round",
    "header",
)
PAIR_IDENTITY_KEYS = (
    "fail_domain",
    "fail_plant",
    "fail_slug",
    "kind",
    "success_domain",
    "success_plant",
    "success_slug",
)


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def mill_id_for_path(path: str) -> str:
    return Path(path).stem


def catalog_first_from_name(path: str) -> int | None:
    stem = Path(path).stem
    for sep in ("-r", "_r"):
        marker = stem.rsplit(sep, 1)
        if len(marker) == 2 and marker[1].isdigit():
            return int(marker[1])
    return None


def extract_companion_path(source: str) -> str | None:
    """``MILL`` or ``OUT`` joined-path constant from a loop / plant-gen script."""

    for name in ("MILL", "OUT"):
        found = extract_joined_path_assignment(source, name)
        if found is not None:
            return found
    return None


def extract_plant_catalog(
    source: str,
    *,
    path: str,
    blob_sha: str = "",
) -> dict[str, Any]:
    """Structured catalog extract for one EVH plant-gen source file."""

    payload = source.encode()
    tree = ast.parse(source, filename=path)
    mill_id = mill_id_for_path(path)
    env = _module_constants(tree)
    catalogs = _extract_catalogs(tree, env, path=path)
    if not catalogs:
        raise ValueError(f"{path} has no extractable EVH catalog")
    rows = sum(item["n_rows"] for item in catalogs)
    first = catalogs[0]
    last = catalogs[-1]
    return {
        "mill_id": mill_id,
        "path": path,
        "blob_sha": blob_sha,
        "sha256": sha256_bytes(payload),
        "kind": KIND_GEN,
        "shape": first["shape"],
        "catalog_first": catalog_first_from_name(path),
        "generator": GENERATOR,
        "factory": FACTORY,
        "n_rows": rows,
        "n_catalogs": len(catalogs),
        "first_slug": first["first_slug"],
        "last_slug": last["last_slug"],
        "catalogs": catalogs,
    }


def _module_constants(tree: ast.AST) -> dict[str, Any]:
    env: dict[str, Any] = {}
    for node in getattr(tree, "body", ()):
        name, value = assignment_of(node)
        if name is None or value is None:
            continue
        resolved = resolve(value, env)
        if resolved is not UNSET:
            env[name] = resolved
    return env


def _extract_catalogs(
    tree: ast.AST,
    env: Mapping[str, Any],
    *,
    path: str,
) -> list[dict[str, Any]]:
    raw = env.get("RAW")
    if isinstance(raw, list) and raw:
        planted = _plant_raw_rows(raw, env, _void_base(tree, default=72))
        dest = _destination_module(tree) or "mill_plants_x"
        return [
            _catalog_record(
                SHAPE_RAW,
                planted,
                dest=dest,
                start_round=catalog_first_from_name(path) or 927,
                void_base=_void_base(tree, default=72),
                offset=_eval_pair_offset(tree, default=446),
            )
        ]

    catalog_fn = function_named(tree, "catalog")
    if catalog_fn is None:
        return []

    emit_calls = _emit_calls(tree, dict(env))
    if emit_calls:
        catalogs = []
        for emit in emit_calls:
            bindings = {name: emit[name] for name in _CATALOG_PARAMS}
            rows = _interpret_catalog(catalog_fn, env, bindings, path=path)
            planted = _plant_catalog_rows(rows, env, emit["void_base"])
            catalogs.append(
                _catalog_record(
                    SHAPE_PARAM,
                    planted,
                    dest=emit["mod"],
                    start_round=emit["start_round"],
                    void_base=emit["void_base"],
                    offset=emit["offset"],
                    tag=emit["tag"],
                    to=emit["to"],
                    kw1=emit["kw1"],
                    kw2=emit["kw2"],
                    kw3=emit["kw3"],
                )
            )
        return catalogs

    rows = _interpret_catalog(catalog_fn, env, {}, path=path)
    void_base = _void_base(tree, default=59 if "PLANTED_OK" in env else 96)
    planted = _plant_catalog_rows(rows, env, void_base)
    shape = SHAPE_FSTRING if "METS" in env else SHAPE_ADD_TABLES
    dest = _destination_module(tree) or (
        "mill_plants_aa" if shape == SHAPE_FSTRING else "mill_plants_w"
    )
    start = catalog_first_from_name(path) or (1161 if shape == SHAPE_FSTRING else 801)
    offset = _eval_pair_offset(tree, default=680 if shape == SHAPE_FSTRING else 320)
    return [
        _catalog_record(
            shape,
            planted,
            dest=dest,
            start_round=start,
            void_base=void_base,
            offset=offset,
        )
    ]


def _interpret_catalog(
    fn: ast.FunctionDef,
    env: Mapping[str, Any],
    args: Mapping[str, Any],
    *,
    path: str,
) -> list[tuple[Any, ...]]:
    local = dict(env)
    local.update(args)
    rows: list[tuple[Any, ...]] = []
    _exec_body(fn.body, local, rows, path=path, fn_name=fn.name)
    return rows


def _exec_body(
    body: list[ast.stmt],
    env: dict[str, Any],
    rows: list[tuple[Any, ...]],
    *,
    path: str,
    fn_name: str,
) -> Any:
    ctx = f"{path}:{fn_name}"
    for stmt in body:
        if isinstance(stmt, ast.FunctionDef):
            continue
        if isinstance(stmt, (ast.Assign, ast.AnnAssign)):
            _exec_assign(stmt, env, ctx)
            continue
        if isinstance(stmt, ast.For):
            _exec_for(stmt, env, rows, path=path, fn_name=fn_name)
            continue
        if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
            _exec_call(stmt.value, env, rows, ctx)
            continue
        if isinstance(stmt, ast.Return):
            if stmt.value is None:
                return None
            return require(stmt.value, env, f"{ctx} return")
    return UNSET


def _exec_assign(stmt: ast.stmt, env: dict[str, Any], ctx: str) -> None:
    if isinstance(stmt, ast.AnnAssign):
        if isinstance(stmt.target, ast.Name) and stmt.value is not None:
            env[stmt.target.id] = require(stmt.value, env, f"{ctx} assign")
        return
    if not isinstance(stmt, ast.Assign) or len(stmt.targets) != 1:
        raise ValueError(f"{ctx}: unsupported assignment")
    target = stmt.targets[0]
    value = require(stmt.value, env, f"{ctx} assign")
    if isinstance(target, ast.Name):
        env[target.id] = value
        return
    if isinstance(target, ast.Tuple) and isinstance(value, (tuple, list)):
        names = [elt.id for elt in target.elts if isinstance(elt, ast.Name)]
        if len(names) != len(value):
            raise ValueError(f"{ctx}: unpack length mismatch")
        for name, item in zip(names, value, strict=True):
            env[name] = item
        return
    raise ValueError(f"{ctx}: unsupported assignment target")


def _exec_for(
    stmt: ast.For,
    env: dict[str, Any],
    rows: list[tuple[Any, ...]],
    *,
    path: str,
    fn_name: str,
) -> None:
    ctx = f"{path}:{fn_name}:for"
    iterable = require(stmt.iter, env, ctx)
    if not isinstance(iterable, (list, tuple)):
        raise ValueError(f"{ctx}: iter is not a sequence")
    for item in iterable:
        _bind_target(stmt.target, item, env, ctx)
        _exec_body(stmt.body, env, rows, path=path, fn_name=fn_name)


def _bind_target(target: ast.AST, value: Any, env: dict[str, Any], ctx: str) -> None:
    if isinstance(target, ast.Name):
        env[target.id] = value
        return
    if isinstance(target, ast.Tuple) and isinstance(value, (tuple, list)):
        if len(target.elts) != len(value):
            raise ValueError(f"{ctx}: for-unpack length mismatch")
        for elt, item in zip(target.elts, value, strict=True):
            _bind_target(elt, item, env, ctx)
        return
    raise ValueError(f"{ctx}: unsupported for-target")


def _exec_call(
    node: ast.Call,
    env: dict[str, Any],
    rows: list[tuple[Any, ...]],
    ctx: str,
) -> None:
    name = node.func.id if isinstance(node.func, ast.Name) else None
    if name not in {"add", "add_row"}:
        raise ValueError(f"{ctx}: unexpected call {name!r}")
    args = [require(arg, env, ctx) for arg in node.args]
    if name == "add_row":
        if not args:
            raise ValueError(f"{ctx}: add_row missing arguments")
        rows.append(tuple(args[1:]))
        return
    rows.append(tuple(args))


def _plant_catalog_rows(
    rows: list[tuple[Any, ...]],
    env: Mapping[str, Any],
    void_base: int,
) -> list[dict[str, Any]]:
    ok_names, bad_names = _plant_name_tables(env)
    planted = []
    for index, row in enumerate(rows):
        if len(row) != 11:
            raise ValueError(f"catalog row is not an 11-tuple: {len(row)}")
        ok_slug, ok_dom, bad_slug, bad_dom, lok, lbad, fok, fbad, xok, xbad, kind = row
        plant_n = void_base + index // 10
        planted.append(
            _pair_identity(
                ok_slug,
                ok_dom,
                bad_slug,
                bad_dom,
                f"{ok_names[index % 10]}-{plant_n}",
                f"{bad_names[index % 10]}-{plant_n}",
                lok,
                lbad,
                fok,
                fbad,
                xok,
                xbad,
                kind,
            )
        )
    return planted


def _plant_raw_rows(
    raw: list[Any],
    env: Mapping[str, Any],
    void_base: int,
) -> list[dict[str, Any]]:
    ok_names, bad_names = _plant_name_tables(env)
    planted = []
    for index, row in enumerate(raw):
        if not isinstance(row, (tuple, list)) or len(row) != 11:
            raise ValueError("RAW row is not an 11-tuple")
        ok_slug, ok_dom, lok, fok, xok, bad_slug, bad_dom, lbad, fbad, xbad, kind = row
        plant_n = void_base + index // 10
        planted.append(
            _pair_identity(
                ok_slug,
                ok_dom,
                bad_slug,
                bad_dom,
                f"{ok_names[index % 10]}-{plant_n}",
                f"{bad_names[index % 10]}-{plant_n}",
                lok,
                lbad,
                fok,
                fbad,
                xok,
                xbad,
                kind,
            )
        )
    return planted


def _plant_name_tables(env: Mapping[str, Any]) -> tuple[list[str], list[str]]:
    ok_names = env.get("POK") or env.get("PLANTED_OK")
    bad_names = env.get("PBAD") or env.get("PLANTED_BAD")
    if not isinstance(ok_names, list) or not isinstance(bad_names, list):
        raise ValueError("missing POK/PLANTED_OK plant name tables")
    if len(ok_names) != 10 or len(bad_names) != 10:
        raise ValueError("plant name tables must have 10 entries")
    return ok_names, bad_names


def _pair_identity(
    ok_slug: Any,
    ok_dom: Any,
    bad_slug: Any,
    bad_dom: Any,
    ok_plant: Any,
    bad_plant: Any,
    leftover_ok: Any,
    leftover_bad: Any,
    first_ok: Any,
    first_bad: Any,
    fix_ok: Any,
    fix_bad: Any,
    kind: Any,
) -> dict[str, Any]:
    return {
        "success_slug": ok_slug,
        "success_domain": ok_dom,
        "fail_slug": bad_slug,
        "fail_domain": bad_dom,
        "success_plant": ok_plant,
        "fail_plant": bad_plant,
        "leftover_ok": leftover_ok,
        "leftover_bad": leftover_bad,
        "first_ok": first_ok,
        "first_bad": first_bad,
        "fix_ok": fix_ok,
        "fix_bad": fix_bad,
        "kind": kind,
    }


def _catalog_record(
    shape: str,
    pairs: list[dict[str, Any]],
    *,
    dest: str,
    start_round: int,
    void_base: int,
    offset: int,
    tag: str | None = None,
    to: int | None = None,
    kw1: str | None = None,
    kw2: str | None = None,
    kw3: str | None = None,
) -> dict[str, Any]:
    if not pairs:
        raise ValueError(f"{dest} extracted zero pairs")
    record = {
        "dest": dest,
        "shape": shape,
        "n_rows": len(pairs),
        "first_slug": pairs[0]["success_slug"],
        "last_slug": pairs[-1]["success_slug"],
        "start_round": start_round,
        "void_base": void_base,
        "offset": offset,
        "pairs": pairs,
    }
    if tag is not None:
        record["tag"] = tag
        record["to"] = to
        record["kw1"] = kw1
        record["kw2"] = kw2
        record["kw3"] = kw3
    return record


def _emit_calls(tree: ast.AST, env: dict[str, Any]) -> list[dict[str, Any]]:
    main = function_named(tree, "main")
    catalog_fn = function_named(tree, "catalog")
    if main is None or catalog_fn is None:
        return []
    local = dict(env)
    rebuilt: list[dict[str, Any]] = []
    for stmt in main.body:
        call = None
        assigned = None
        if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1:
            if isinstance(stmt.targets[0], ast.Name) and isinstance(stmt.value, ast.Call):
                assigned = stmt.targets[0].id
                call = stmt.value
        elif isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
            call = stmt.value
        if call is None or not isinstance(call.func, ast.Name) or call.func.id != "emit":
            continue
        args = [require(arg, local, "main:emit") for arg in call.args]
        if len(args) != len(_EMIT_FIELDS):
            raise ValueError("emit() does not have 10 positional arguments")
        record = dict(zip(_EMIT_FIELDS, args, strict=True))
        bindings = {name: record[name] for name in _CATALOG_PARAMS}
        rows = _interpret_catalog(catalog_fn, env, bindings, path="emit")
        if assigned is not None:
            local[assigned] = len(rows)
        rebuilt.append(record)
    return rebuilt


def _void_base(tree: ast.AST, *, default: int) -> int:
    for fn_name in ("with_plants", "main"):
        fn = function_named(tree, fn_name)
        if fn is None:
            continue
        found = _void_base_from_body(fn.body)
        if found is not None:
            return found
    return default


def _void_base_from_body(body: list[ast.stmt]) -> int | None:
    for stmt in body:
        name, value = assignment_of(stmt)
        if name != "n" or value is None:
            continue
        if not isinstance(value, ast.BinOp) or not isinstance(value.op, ast.Add):
            continue
        left = resolve(value.left, {})
        if isinstance(left, int):
            return left
    return None


def _eval_pair_offset(tree: ast.AST, *, default: int) -> int:
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Name):
            continue
        if node.func.id != "eval_pair" or len(node.args) < 2:
            continue
        offset_node = node.args[-2]
        if isinstance(offset_node, ast.BinOp) and isinstance(offset_node.op, ast.Add):
            right = resolve(offset_node.right, {})
            if isinstance(right, int):
                return right
    return default


def _destination_module(tree: ast.AST) -> str | None:
    for node in getattr(tree, "body", ()):
        name, value = assignment_of(node)
        if name == "OUT" and value is not None:
            found = joined_path_constant(value)
            if found:
                return Path(found).stem
    main = function_named(tree, "main")
    if main is None:
        return None
    for stmt in main.body:
        name, value = assignment_of(stmt)
        if name == "dest" and value is not None:
            found = joined_path_constant(value)
            if found:
                return Path(found).stem
    return None


def mill_summary(record: Mapping[str, Any], *, include_pairs: bool) -> dict[str, Any]:
    catalogs = []
    for catalog in record["catalogs"]:
        item = {
            "dest": catalog["dest"],
            "shape": catalog["shape"],
            "n_rows": catalog["n_rows"],
            "first_slug": catalog["first_slug"],
            "last_slug": catalog["last_slug"],
            "start_round": catalog["start_round"],
            "void_base": catalog["void_base"],
            "offset": catalog["offset"],
        }
        for key in ("tag", "to", "kw1", "kw2", "kw3"):
            if key in catalog:
                item[key] = catalog[key]
        if include_pairs:
            item["pairs"] = [
                compact_pair_identity(pair) for pair in catalog.get("pairs") or ()
            ]
        catalogs.append(item)
    return {
        "mill_id": record["mill_id"],
        "path": record["path"],
        "blob_sha": record["blob_sha"],
        "sha256": record["sha256"],
        "kind": record["kind"],
        "shape": record["shape"],
        "catalog_first": record["catalog_first"],
        "n_rows": record["n_rows"],
        "n_catalogs": record["n_catalogs"],
        "first_slug": record["first_slug"],
        "last_slug": record["last_slug"],
        "generator": record["generator"],
        "factory": record["factory"],
        "catalogs": catalogs,
    }


def catalog_document(mills: list[dict[str, Any]]) -> dict[str, Any]:
    pair_rows = sum(mill["n_rows"] for mill in mills)
    return {
        "schema": CATALOG_SCHEMA_ID,
        "source_ref": LEGACY_REF,
        "preserve_commit": PRESERVE_COMMIT,
        "factory": FACTORY,
        "generator": GENERATOR,
        "slice": SLICE_ID,
        "n_mills": len(mills),
        "n_pair_rows": pair_rows,
        "mills": {mill["mill_id"]: mill for mill in mills},
    }


def compact_pair_identity(pair: Mapping[str, Any]) -> dict[str, Any]:
    """Keep r801 pair identity; drop leftover/first/fix metric bodies."""

    return {key: pair[key] for key in PAIR_IDENTITY_KEYS}


def dumps_catalog(document: Mapping[str, Any]) -> str:
    """Pretty-print the catalog; pair identities stay one object per line."""

    return _encode(document, 0, key=None) + "\n"


def _encode(value: Any, level: int, key: str | None) -> str:
    pad = "  " * level
    if isinstance(value, dict):
        if not value:
            return "{}"
        parts = [
            f"{pad}  {json.dumps(item_key)}: {_encode(value[item_key], level + 1, item_key)}"
            for item_key in sorted(value)
        ]
        return "{\n" + ",\n".join(parts) + f"\n{pad}}}"
    if isinstance(value, list):
        if not value:
            return "[]"
        if key == "pairs":
            lines = [
                f"{pad}  "
                + json.dumps(
                    item, ensure_ascii=True, sort_keys=True, separators=(", ", ": ")
                )
                for item in value
            ]
            return "[\n" + ",\n".join(lines) + f"\n{pad}]"
        lines = [f"{pad}  {_encode(item, level + 1, None)}" for item in value]
        return "[\n" + ",\n".join(lines) + f"\n{pad}]"
    return json.dumps(value, ensure_ascii=True)


def catalog_json_path(package_dir: Path | None = None) -> Path:
    root = package_dir if package_dir is not None else Path(__file__).resolve().parent
    return root / CATALOG_FILENAME


def write_catalog_document(document: Mapping[str, Any], path: Path | None = None) -> Path:
    destination = path if path is not None else catalog_json_path()
    destination.write_text(dumps_catalog(document), encoding="utf-8")
    return destination
