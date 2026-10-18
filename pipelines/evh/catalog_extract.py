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
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any, TypeGuard

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
    PAIRS_FILENAME,
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
# Unpack order of an ``add``/``add_row`` catalog row and of a ``RAW`` literal row.
_CATALOG_ROW_FIELDS = (
    "success_slug",
    "success_domain",
    "fail_slug",
    "fail_domain",
    "leftover_ok",
    "leftover_bad",
    "first_ok",
    "first_bad",
    "fix_ok",
    "fix_bad",
    "kind",
)
_RAW_ROW_FIELDS = (
    "success_slug",
    "success_domain",
    "leftover_ok",
    "first_ok",
    "fix_ok",
    "fail_slug",
    "fail_domain",
    "leftover_bad",
    "first_bad",
    "fix_bad",
    "kind",
)
# Defaults for a parameterless ``catalog()``: (dest, start_round, eval_pair offset).
_PLAIN_CATALOG_DEFAULTS = {
    SHAPE_FSTRING: ("mill_plants_aa", 1161, 680),
    SHAPE_ADD_TABLES: ("mill_plants_w", 801, 320),
}
PAIR_ROW_KEYS = (
    "dest",
    "fail_domain",
    "fail_plant",
    "fail_slug",
    "kind",
    "mill_id",
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
        return [_raw_catalog(tree, env, raw, path=path)]

    catalog_fn = function_named(tree, "catalog")
    if catalog_fn is None:
        return []

    emit_calls = _emit_calls(tree, dict(env))
    if emit_calls:
        return [_param_catalog(catalog_fn, env, emit, path=path) for emit in emit_calls]
    rows = _interpret_catalog(catalog_fn, env, {}, path=path)
    return [_plain_catalog(tree, env, rows, path=path)]


def _raw_catalog(
    tree: ast.AST,
    env: Mapping[str, Any],
    raw: list[Any],
    *,
    path: str,
) -> dict[str, Any]:
    planted = _plant_raw_rows(raw, env, _void_base(tree, default=72))
    dest = _destination_module(tree) or "mill_plants_x"
    return _catalog_record(
        SHAPE_RAW,
        planted,
        {
            "dest": dest,
            "start_round": catalog_first_from_name(path) or 927,
            "void_base": _void_base(tree, default=72),
            "offset": _eval_pair_offset(tree, default=446),
        },
    )


def _param_catalog(
    catalog_fn: ast.FunctionDef,
    env: Mapping[str, Any],
    emit: Mapping[str, Any],
    *,
    path: str,
) -> dict[str, Any]:
    bindings = {name: emit[name] for name in _CATALOG_PARAMS}
    rows = _interpret_catalog(catalog_fn, env, bindings, path=path)
    planted = _plant_catalog_rows(rows, env, emit["void_base"])
    return _catalog_record(
        SHAPE_PARAM,
        planted,
        {
            "dest": emit["mod"],
            "start_round": emit["start_round"],
            "void_base": emit["void_base"],
            "offset": emit["offset"],
        },
        params=bindings,
    )


def _plain_catalog(
    tree: ast.AST,
    env: Mapping[str, Any],
    rows: list[tuple[Any, ...]],
    *,
    path: str,
) -> dict[str, Any]:
    void_base = _void_base(tree, default=59 if "PLANTED_OK" in env else 96)
    planted = _plant_catalog_rows(rows, env, void_base)
    shape = SHAPE_FSTRING if "METS" in env else SHAPE_ADD_TABLES
    default_dest, default_start, default_offset = _PLAIN_CATALOG_DEFAULTS[shape]
    dest = _destination_module(tree) or default_dest
    start = catalog_first_from_name(path) or default_start
    offset = _eval_pair_offset(tree, default=default_offset)
    return _catalog_record(
        shape,
        planted,
        {"dest": dest, "start_round": start, "void_base": void_base, "offset": offset},
    )


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
    _exec_body(fn.body, local, rows, f"{path}:{fn.name}")
    return rows


def _exec_body(
    body: list[ast.stmt],
    env: dict[str, Any],
    rows: list[tuple[Any, ...]],
    ctx: str,
) -> Any:
    """Run one ``catalog()`` body; ``ctx`` is ``"<path>:<fn name>"``.

    Assignments, ``for`` loops, bare calls and ``return`` run here; nested defs and
    every other statement are skipped. Dispatching in this frame keeps a nested
    ``for`` at two frames per level (``_exec_body`` and ``_exec_for``).
    """

    for stmt in body:
        if isinstance(stmt, (ast.Assign, ast.AnnAssign)):
            _exec_assign(stmt, env, ctx)
        elif isinstance(stmt, ast.For):
            _exec_for(stmt, env, rows, ctx)
        elif isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
            _exec_call(stmt.value, env, rows, ctx)
        elif isinstance(stmt, ast.Return):
            return None if stmt.value is None else require(stmt.value, env, f"{ctx} return")
    return UNSET


def _exec_assign(stmt: ast.stmt, env: dict[str, Any], ctx: str) -> None:
    if isinstance(stmt, ast.AnnAssign):
        annotated = _annotated_binding(stmt)
        if annotated is not None:
            env[annotated[0]] = require(annotated[1], env, f"{ctx} assign")
        return
    if not isinstance(stmt, ast.Assign) or len(stmt.targets) != 1:
        raise ValueError(f"{ctx}: unsupported assignment")
    target = stmt.targets[0]
    value = require(stmt.value, env, f"{ctx} assign")
    if isinstance(target, ast.Name):
        env[target.id] = value
        return
    if isinstance(target, ast.Tuple) and isinstance(value, (tuple, list)):
        _unpack_names(target, value, env, ctx)
        return
    raise ValueError(f"{ctx}: unsupported assignment target")


def _annotated_binding(stmt: ast.AnnAssign) -> tuple[str, ast.expr] | None:
    """``(name, value)`` for ``name: T = value``; a bare annotation binds nothing."""

    if isinstance(stmt.target, ast.Name) and stmt.value is not None:
        return stmt.target.id, stmt.value
    return None


def _unpack_names(
    target: ast.Tuple,
    value: tuple[Any, ...] | list[Any],
    env: dict[str, Any],
    ctx: str,
) -> None:
    names = [elt.id for elt in target.elts if isinstance(elt, ast.Name)]
    if len(names) != len(value):
        raise ValueError(f"{ctx}: unpack length mismatch")
    for name, item in zip(names, value, strict=True):
        env[name] = item


def _exec_for(
    stmt: ast.For,
    env: dict[str, Any],
    rows: list[tuple[Any, ...]],
    ctx: str,
) -> None:
    for_ctx = f"{ctx}:for"
    iterable = require(stmt.iter, env, for_ctx)
    if not isinstance(iterable, (list, tuple)):
        raise ValueError(f"{for_ctx}: iter is not a sequence")
    for item in iterable:
        _bind_target(stmt.target, item, env, for_ctx)
        _exec_body(stmt.body, env, rows, ctx)


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
    return _plant_rows(map(_catalog_row_fields, rows), env, void_base)


def _plant_raw_rows(
    raw: list[Any],
    env: Mapping[str, Any],
    void_base: int,
) -> list[dict[str, Any]]:
    return _plant_rows(map(_raw_row_fields, raw), env, void_base)


def _catalog_row_fields(row: tuple[Any, ...]) -> dict[str, Any]:
    if len(row) != 11:
        raise ValueError(f"catalog row is not an 11-tuple: {len(row)}")
    return dict(zip(_CATALOG_ROW_FIELDS, row, strict=True))


def _raw_row_fields(row: Any) -> dict[str, Any]:
    if not isinstance(row, (tuple, list)) or len(row) != 11:
        raise ValueError("RAW row is not an 11-tuple")
    return dict(zip(_RAW_ROW_FIELDS, row, strict=True))


def _plant_rows(
    field_rows: Iterable[Mapping[str, Any]],
    env: Mapping[str, Any],
    void_base: int,
) -> list[dict[str, Any]]:
    """Name each row's plants; the name tables are checked before any row is."""

    ok_names, bad_names = _plant_name_tables(env)
    planted = []
    for index, fields in enumerate(field_rows):
        plant_n = void_base + index // 10
        planted.append(
            _pair_identity(
                fields,
                f"{ok_names[index % 10]}-{plant_n}",
                f"{bad_names[index % 10]}-{plant_n}",
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
    fields: Mapping[str, Any],
    ok_plant: Any,
    bad_plant: Any,
) -> dict[str, Any]:
    return {
        "success_slug": fields["success_slug"],
        "success_domain": fields["success_domain"],
        "fail_slug": fields["fail_slug"],
        "fail_domain": fields["fail_domain"],
        "success_plant": ok_plant,
        "fail_plant": bad_plant,
        "leftover_ok": fields["leftover_ok"],
        "leftover_bad": fields["leftover_bad"],
        "first_ok": fields["first_ok"],
        "first_bad": fields["first_bad"],
        "fix_ok": fields["fix_ok"],
        "fix_bad": fields["fix_bad"],
        "kind": fields["kind"],
    }


def _catalog_record(
    shape: str,
    pairs: list[dict[str, Any]],
    placement: Mapping[str, Any],
    *,
    params: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """``placement`` is where the mill emits the rows (``dest``, ``start_round``,
    ``void_base``, ``offset``); ``params`` are the ``catalog(tag, to, kw1, kw2, kw3)``
    bindings, if any."""

    if not pairs:
        raise ValueError(f"{placement['dest']} extracted zero pairs")
    record = {
        "dest": placement["dest"],
        "shape": shape,
        "n_rows": len(pairs),
        "first_slug": pairs[0]["success_slug"],
        "last_slug": pairs[-1]["success_slug"],
        "start_round": placement["start_round"],
        "void_base": placement["void_base"],
        "offset": placement["offset"],
        "pairs": pairs,
    }
    if params is not None and params["tag"] is not None:
        for key in _CATALOG_PARAMS:
            record[key] = params[key]
    return record


def _emit_calls(tree: ast.AST, env: dict[str, Any]) -> list[dict[str, Any]]:
    main = function_named(tree, "main")
    catalog_fn = function_named(tree, "catalog")
    if main is None or catalog_fn is None:
        return []
    local = dict(env)
    rebuilt: list[dict[str, Any]] = []
    for stmt in main.body:
        assigned, call = _statement_call(stmt)
        if not _is_emit_call(call):
            continue
        record = _emit_record(call, local)
        bindings = {name: record[name] for name in _CATALOG_PARAMS}
        rows = _interpret_catalog(catalog_fn, env, bindings, path="emit")
        if assigned is not None:
            local[assigned] = len(rows)
        rebuilt.append(record)
    return rebuilt


def _statement_call(stmt: ast.stmt) -> tuple[str | None, ast.Call | None]:
    """``(name, call)`` for ``name = f(...)``; ``(None, call)`` for ``f(...)``."""

    if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
        return None, stmt.value
    if not isinstance(stmt, ast.Assign) or len(stmt.targets) != 1:
        return None, None
    target = stmt.targets[0]
    if isinstance(target, ast.Name) and isinstance(stmt.value, ast.Call):
        return target.id, stmt.value
    return None, None


def _is_emit_call(call: ast.Call | None) -> TypeGuard[ast.Call]:
    if call is None or not isinstance(call.func, ast.Name):
        return False
    return call.func.id == "emit"


def _emit_record(call: ast.Call, env: Mapping[str, Any]) -> dict[str, Any]:
    args = [require(arg, env, "main:emit") for arg in call.args]
    if len(args) != len(_EMIT_FIELDS):
        raise ValueError("emit() does not have 10 positional arguments")
    return dict(zip(_EMIT_FIELDS, args, strict=True))


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
        offset = _eval_pair_call_offset(node)
        if offset is not None:
            return offset
    return default


def _eval_pair_call_offset(node: ast.AST) -> int | None:
    """``N`` from ``eval_pair(..., <expr> + N, <last>)``; else ``None``."""

    if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Name):
        return None
    if node.func.id != "eval_pair" or len(node.args) < 2:
        return None
    offset_node = node.args[-2]
    if not isinstance(offset_node, ast.BinOp) or not isinstance(offset_node.op, ast.Add):
        return None
    right = resolve(offset_node.right, {})
    return right if isinstance(right, int) else None


def _destination_module(tree: ast.AST) -> str | None:
    found = _assigned_path_stem(getattr(tree, "body", ()), "OUT")
    if found is not None:
        return found
    main = function_named(tree, "main")
    if main is None:
        return None
    return _assigned_path_stem(main.body, "dest")


def _assigned_path_stem(body: Iterable[ast.stmt], name: str) -> str | None:
    """Stem of the first non-empty joined-path constant assigned to ``name``."""

    for stmt in body:
        assigned, value = assignment_of(stmt)
        if assigned != name or value is None:
            continue
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


def compact_deferred_pair_row(
    mill_id: str,
    dest: str,
    pair: Mapping[str, Any],
) -> dict[str, Any]:
    """Flat JSONL identity. Do not nest dest objects or metric bodies."""

    row = compact_pair_identity(pair)
    row["dest"] = dest
    row["mill_id"] = mill_id
    return {key: row[key] for key in PAIR_ROW_KEYS}


def deferred_rows_from_extract(record: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for dest in record["catalogs"]:
        for pair in dest["pairs"]:
            rows.append(
                compact_deferred_pair_row(record["mill_id"], dest["dest"], pair)
            )
    return rows


def dumps_pairs_jsonl(rows: list[Mapping[str, Any]]) -> str:
    """One compact identity per line. Trailing newline. No CR."""

    lines = [
        json.dumps(row, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
        for row in rows
    ]
    return "\n".join(lines) + "\n"


def dumps_catalog(document: Mapping[str, Any]) -> str:
    """Pretty-print the catalog; pair identities stay one object per line."""

    return _encode(document, 0, key=None) + "\n"


def _encode(value: Any, level: int, key: str | None) -> str:
    # Recursion stays in this function (the comprehensions run in its frame), so a
    # nested dict or list level costs one frame; _encode_flat never recurses.
    pad = "  " * level
    flat = _encode_flat(value, pad, key)
    if flat is not None:
        return flat
    if isinstance(value, dict):
        parts = [
            f"{pad}  {json.dumps(item_key)}: {_encode(value[item_key], level + 1, item_key)}"
            for item_key in sorted(value)
        ]
        return "{\n" + ",\n".join(parts) + f"\n{pad}}}"
    lines = [f"{pad}  {_encode(item, level + 1, None)}" for item in value]
    return _bracketed(lines, pad)


def _encode_flat(value: Any, pad: str, key: str | None) -> str | None:
    """Scalars, empty containers, and a ``pairs`` list (one compact pair identity per
    line); ``None`` for a non-empty dict or list that needs ``_encode`` to recurse."""

    if not isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=True)
    if not value:
        return "{}" if isinstance(value, dict) else "[]"
    if isinstance(value, dict) or key != "pairs":
        return None
    lines = [
        f"{pad}  " + json.dumps(item, ensure_ascii=True, sort_keys=True, separators=(", ", ": "))
        for item in value
    ]
    return _bracketed(lines, pad)


def _bracketed(lines: list[str], pad: str) -> str:
    return "[\n" + ",\n".join(lines) + f"\n{pad}]"


def catalog_json_path(package_dir: Path | None = None) -> Path:
    root = package_dir if package_dir is not None else Path(__file__).resolve().parent
    return root / CATALOG_FILENAME


def pairs_jsonl_path(package_dir: Path | None = None) -> Path:
    root = package_dir if package_dir is not None else Path(__file__).resolve().parent
    return root / PAIRS_FILENAME


def write_catalog_document(document: Mapping[str, Any], path: Path | None = None) -> Path:
    destination = path if path is not None else catalog_json_path()
    destination.write_text(dumps_catalog(document), encoding="utf-8")
    return destination


def write_pairs_jsonl(
    rows: list[Mapping[str, Any]],
    path: Path | None = None,
) -> Path:
    destination = path if path is not None else pairs_jsonl_path()
    destination.write_text(dumps_pairs_jsonl(rows), encoding="utf-8")
    return destination
