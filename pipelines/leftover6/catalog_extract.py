#!/usr/bin/env python3
"""AST-extract leftover6 pair and plant catalogs.

Evaluates only literal assignments and ``dict`` / ``_row`` constructor calls.
Does not import, compile, or exec leftover6 mills.
"""

from __future__ import annotations

import ast
import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from ._contract import bind_import_twin

UNSET = object()


@dataclass(frozen=True)
class SourceContext:
    path: str
    blob_sha: str
    digest: str
    lines: int

GQL_PATH = "experiments/mill_gql_leftover6_r260.py"
SSL_PATH = "experiments/ssl_r164_leftover6_mill.py"
SBOX_PATH = "experiments/sbox-mill-plants-leftover6.py"

GQL_PAIR_FIELDS = (
    "slug",
    "fail",
    "surf",
    "naive",
    "bind",
    "drop",
    "plant",
    "file",
    "test",
    "field",
    "ticket",
)
SSL_PAIR_FIELDS = (
    "slug",
    "lslug",
    "stack",
    "lstack",
    "obj",
    "naive",
    "fix",
    "docs",
    "novel",
    "new_vs",
    "ticket",
)
SBOX_PLANT_FIELDS = (
    "family",
    "dump",
    "miss_dump",
    "secret",
    "pin",
    "pin_path",
    "pin_needle",
    "grep_hit",
    "distinct",
    "ext",
    "miss_ext",
    "live_bin",
    "inc",
    "over_slug",
    "miss_slug",
    "proc",
    "allow",
    "rotate",
)


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def assignment_of(node: ast.stmt) -> tuple[str | None, ast.AST | None]:
    if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
        return node.target.id, node.value
    if isinstance(node, ast.Assign) and len(node.targets) == 1:
        target = node.targets[0]
        if isinstance(target, ast.Name):
            return target.id, node.value
    return None, None


def literal_value(node: ast.AST, env: Mapping[str, Any] | None = None) -> Any:
    bound = env or {}
    value = _atomic_literal(node, bound)
    if value is not UNSET:
        return value
    return _compound_literal(node, bound)


def _atomic_literal(node: ast.AST, env: Mapping[str, Any]) -> Any:
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Name):
        return env[node.id] if node.id in env else UNSET
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        inner = literal_value(node.operand, env)
        return -inner if isinstance(inner, (int, float)) else UNSET
    return UNSET


def _compound_literal(node: ast.AST, env: Mapping[str, Any]) -> Any:
    if isinstance(node, (ast.Tuple, ast.List)):
        constructor = tuple if isinstance(node, ast.Tuple) else list
        return _sequence(node.elts, env, constructor)
    if isinstance(node, ast.Dict):
        return _mapping(node, env)
    if isinstance(node, ast.Call):
        return _literal_call(node, env)
    return UNSET


def _sequence(elts: list[ast.AST], env: Mapping[str, Any], ctor):
    values: list[Any] = []
    for elt in elts:
        item = literal_value(elt, env)
        if item is UNSET:
            return UNSET
        values.append(item)
    return ctor(values)


def _mapping(node: ast.Dict, env: Mapping[str, Any]) -> Any:
    out: dict[Any, Any] = {}
    for key_node, value_node in zip(node.keys, node.values, strict=True):
        if key_node is None:
            return UNSET
        key = literal_value(key_node, env)
        value = literal_value(value_node, env)
        if key is UNSET or value is UNSET:
            return UNSET
        try:
            if key in out:
                return UNSET
            out[key] = value
        except TypeError:
            return UNSET
    return out


def _literal_call(node: ast.Call, env: Mapping[str, Any]) -> Any:
    if not isinstance(node.func, ast.Name):
        return UNSET
    parsers = {"dict": _dict_call, "_row": _row_call}
    parser = parsers.get(node.func.id)
    return UNSET if parser is None else parser(node, env)


def _dict_call(node: ast.Call, env: Mapping[str, Any]) -> Any:
    if node.args or any(keyword.arg is None for keyword in node.keywords):
        return UNSET
    values: dict[str, Any] = {}
    for keyword in node.keywords:
        name = keyword.arg
        if name is None or name in values:
            return UNSET
        value = literal_value(keyword.value, env)
        if value is UNSET:
            return UNSET
        values[name] = value
    return values


def _row_call(node: ast.Call, env: Mapping[str, Any]) -> Any:
    if node.keywords or len(node.args) != len(SBOX_PLANT_FIELDS):
        return UNSET
    values = _sequence(node.args, env, list)
    return UNSET if values is UNSET else dict(zip(SBOX_PLANT_FIELDS, values, strict=True))


def module_constants(source: str, *, path: str) -> dict[str, Any]:
    tree = ast.parse(source, filename=path)
    env: dict[str, Any] = {}
    for node in tree.body:
        name, value = assignment_of(node)
        if name is None:
            _invalidate_names(env, _statement_names(node))
            continue
        if value is None:
            continue
        resolved = literal_value(value, env)
        if resolved is not UNSET:
            env[name] = resolved
        else:
            # Assignment is authoritative: never retain an earlier literal
            # after the source replaces it with an expression we refuse to run.
            _invalidate_names(env, _call_names(value))
            env.pop(name, None)
    return env


def _statement_names(node: ast.AST) -> list[str]:
    """Invalidate unsupported top-level uses without running publisher bodies."""
    scoped = _scope_names(node)
    if scoped is not None:
        return scoped
    if isinstance(node, ast.Name):
        return [node.id]
    if isinstance(node, ast.alias):
        return [node.asname or node.name.partition(".")[0]]
    return _child_names(node)


def _scope_names(node: ast.AST) -> list[str] | None:
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        expressions = [node.args, *node.decorator_list]
        return [node.name, *(name for expr in expressions for name in _statement_names(expr))]
    if isinstance(node, ast.ClassDef):
        return [node.name, *_child_names(node)]
    if isinstance(node, ast.Lambda):
        return _statement_names(node.args)
    return None


def _child_names(node: ast.AST) -> list[str]:
    return [name for child in ast.iter_child_nodes(node) for name in _statement_names(child)]


def _mutable_identities(value: Any) -> set[int]:
    if not isinstance(value, (dict, list, set, tuple)):
        return set()
    items = value.values() if isinstance(value, dict) else value
    identities = set() if isinstance(value, tuple) else {id(value)}
    for item in items:
        identities.update(_mutable_identities(item))
    return identities


def _call_names(node: ast.AST) -> list[str]:
    if isinstance(node, ast.Lambda):
        return _call_names(node.args)
    if isinstance(node, ast.Call):
        return _statement_names(node)
    return [name for child in ast.iter_child_nodes(node) for name in _call_names(child)]


def _invalidate_names(env: dict[str, Any], names: list[str]) -> None:
    """Invalidate aliases too when an unsupported operation touches mutable data."""
    affected = set().union(*(_mutable_identities(env.get(name)) for name in names))
    for name, value in tuple(env.items()):
        if name in names or affected.intersection(_mutable_identities(value)):
            env.pop(name)


def extract_source(source: str, *, path: str, blob_sha: str = "") -> dict[str, Any]:
    payload = source.encode()
    constants = module_constants(source, path=path)
    digest = sha256_bytes(payload)
    lines = source.count("\n")
    context = SourceContext(path, blob_sha, digest, lines)
    for suffix, builder in (("mill_gql_leftover6_r260.py", _gql_record), ("ssl_r164_leftover6_mill.py", _ssl_record), ("sbox-mill-plants-leftover6.py", _sbox_record)):
        if path.endswith(suffix):
            return builder(constants, context)
    raise ValueError(f"unsupported leftover6 source {path}")


def _require_str(value: Any, context: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{context} is not a non-empty string")
    return value


def _require_int(value: Any, context: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{context} is not an int")
    return value


def _gql_record(constants: Mapping[str, Any], context: SourceContext) -> dict[str, Any]:
    path, blob_sha, digest, lines = context.path, context.blob_sha, context.digest, context.lines
    pairs_raw = constants.get("PAIRS")
    rows = _mapping_rows(pairs_raw, GQL_PAIR_FIELDS, path=path, name="PAIRS")
    return {
        "kind": "gql-pairs",
        "shape": "dict-kwargs",
        "path": path,
        "blob_sha": blob_sha,
        "sha256": digest,
        "source_lines": lines,
        "factory": _require_str(constants.get("FAC"), f"{path} FAC"),
        "generator": _require_str(constants.get("GEN"), f"{path} GEN"),
        "catalog_first": 260,
        "n_rows": len(rows),
        "first_slug": rows[0]["slug"],
        "last_slug": rows[-1]["slug"],
        "rows": [
            {"kind": "gql-pairs", "round": 260 + index, **row} for index, row in enumerate(rows)
        ],
    }


def _ssl_record(constants: Mapping[str, Any], context: SourceContext) -> dict[str, Any]:
    path, blob_sha, digest, lines = context.path, context.blob_sha, context.digest, context.lines
    pairs_raw = constants.get("PAIRS")
    rows = _mapping_rows(pairs_raw, SSL_PAIR_FIELDS, path=path, name="PAIRS")
    n_rounds = _require_int(constants.get("N_ROUNDS"), f"{path} N_ROUNDS")
    start = _require_int(constants.get("START"), f"{path} START")
    if n_rounds != len(rows):
        raise ValueError(f"{path} N_ROUNDS={n_rounds} disagrees with {len(rows)} pairs")
    return {
        "kind": "ssl-pairs",
        "shape": "literal-dicts",
        "path": path,
        "blob_sha": blob_sha,
        "sha256": digest,
        "source_lines": lines,
        "factory": _require_str(constants.get("FACTORY"), f"{path} FACTORY"),
        "generator": _require_str(constants.get("GEN"), f"{path} GEN"),
        "catalog_first": start,
        "n_rows": len(rows),
        "first_slug": rows[0]["slug"],
        "last_slug": rows[-1]["slug"],
        "rows": [
            {"kind": "ssl-pairs", "round": start + index, **row} for index, row in enumerate(rows)
        ],
    }


def _sbox_record(constants: Mapping[str, Any], context: SourceContext) -> dict[str, Any]:
    path, blob_sha, digest, lines = context.path, context.blob_sha, context.digest, context.lines
    rows = _mapping_rows(constants.get("_ROWS"), SBOX_PLANT_FIELDS, path=path, name="_ROWS")
    first_inc = _require_int(rows[0]["inc"], f"{path} _ROWS[0].inc")
    return {
        "kind": "sbox-plants",
        "shape": "row-ctor",
        "path": path,
        "blob_sha": blob_sha,
        "sha256": digest,
        "source_lines": lines,
        "factory": "sandbox-refusal-factory",
        "generator": "grok-4.6",
        "catalog_first": first_inc,
        "n_rows": len(rows),
        "first_slug": rows[0]["family"],
        "last_slug": rows[-1]["family"],
        "rows": [{"kind": "sbox-plants", **row} for row in rows],
    }


def _mapping_rows(
    raw: Any,
    fields: tuple[str, ...],
    *,
    path: str,
    name: str,
) -> list[dict[str, Any]]:
    if not isinstance(raw, list) or not raw:
        raise ValueError(f"{path} {name} is not a non-empty literal list")
    return [_typed_mapping(item, fields, f"{path} {name}[{index}]")
            for index, item in enumerate(raw)]


def _typed_mapping(item: Any, fields: tuple[str, ...], context: str) -> dict[str, Any]:
    if not isinstance(item, dict):
        raise ValueError(f"{context} is not a literal mapping")
    if set(item) != set(fields):
        raise ValueError(f"{context} keys drifted from {fields}")
    return {field: _field_value(field, item[field], context) for field in fields}


def _field_value(field: str, value: Any, context: str) -> Any:
    checker = _require_int if field in {"inc", "novel"} else _require_str
    return checker(value, f"{context}.{field}")


def dumps_jsonl(rows: list[Mapping[str, Any]]) -> str:
    lines = [
        json.dumps(dict(row), ensure_ascii=True, sort_keys=True, separators=(",", ":"))
        for row in rows
    ]
    return "\n".join(lines) + "\n"


def dumps_header(document: Mapping[str, Any]) -> str:
    return json.dumps(document, ensure_ascii=True, indent=2, sort_keys=True) + "\n"


bind_import_twin(__name__)
