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
from pathlib import Path
from typing import Any

UNSET = object()

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
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Name):
        return bound[node.id] if node.id in bound else UNSET
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        inner = literal_value(node.operand, bound)
        return -inner if isinstance(inner, (int, float)) else UNSET
    if isinstance(node, ast.Tuple):
        return _sequence(node.elts, bound, tuple)
    if isinstance(node, ast.List):
        return _sequence(node.elts, bound, list)
    if isinstance(node, ast.Dict):
        return _mapping(node, bound)
    if isinstance(node, ast.Call):
        return _literal_call(node, bound)
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
        out[key] = value
    return out


def _literal_call(node: ast.Call, env: Mapping[str, Any]) -> Any:
    if not isinstance(node.func, ast.Name):
        return UNSET
    name = node.func.id
    if name == "dict":
        if node.args:
            return UNSET
        out: dict[str, Any] = {}
        for keyword in node.keywords:
            if keyword.arg is None:
                return UNSET
            value = literal_value(keyword.value, env)
            if value is UNSET:
                return UNSET
            out[keyword.arg] = value
        return out
    if name == "_row":
        if node.keywords or len(node.args) != len(SBOX_PLANT_FIELDS):
            return UNSET
        values = _sequence(node.args, env, list)
        if values is UNSET:
            return UNSET
        return dict(zip(SBOX_PLANT_FIELDS, values, strict=True))
    return UNSET


def module_constants(source: str, *, path: str) -> dict[str, Any]:
    tree = ast.parse(source, filename=path)
    env: dict[str, Any] = {}
    for node in tree.body:
        name, value = assignment_of(node)
        if name is None or value is None:
            continue
        resolved = literal_value(value, env)
        if resolved is not UNSET:
            env[name] = resolved
        else:
            # Assignment is authoritative: never retain an earlier literal
            # after the source replaces it with an expression we refuse to run.
            env.pop(name, None)
    return env


def extract_source(source: str, *, path: str, blob_sha: str = "") -> dict[str, Any]:
    payload = source.encode()
    constants = module_constants(source, path=path)
    digest = sha256_bytes(payload)
    lines = source.count("\n")
    if path.endswith("mill_gql_leftover6_r260.py"):
        return _gql_record(constants, path=path, blob_sha=blob_sha, digest=digest, lines=lines)
    if path.endswith("ssl_r164_leftover6_mill.py"):
        return _ssl_record(constants, path=path, blob_sha=blob_sha, digest=digest, lines=lines)
    if path.endswith("sbox-mill-plants-leftover6.py"):
        return _sbox_record(constants, path=path, blob_sha=blob_sha, digest=digest, lines=lines)
    raise ValueError(f"unsupported leftover6 source {path}")


def _require_str(value: Any, context: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{context} is not a non-empty string")
    return value


def _require_int(value: Any, context: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{context} is not an int")
    return value


def _gql_record(
    constants: Mapping[str, Any],
    *,
    path: str,
    blob_sha: str,
    digest: str,
    lines: int,
) -> dict[str, Any]:
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


def _ssl_record(
    constants: Mapping[str, Any],
    *,
    path: str,
    blob_sha: str,
    digest: str,
    lines: int,
) -> dict[str, Any]:
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


def _sbox_record(
    constants: Mapping[str, Any],
    *,
    path: str,
    blob_sha: str,
    digest: str,
    lines: int,
) -> dict[str, Any]:
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
    rows: list[dict[str, Any]] = []
    for index, item in enumerate(raw):
        if not isinstance(item, dict):
            raise ValueError(f"{path} {name}[{index}] is not a literal mapping")
        if set(item) != set(fields):
            raise ValueError(f"{path} {name}[{index}] keys drifted from {fields}")
        row: dict[str, Any] = {}
        for field in fields:
            value = item[field]
            if field in {"inc", "novel"}:
                row[field] = _require_int(value, f"{path} {name}[{index}].{field}")
            else:
                row[field] = _require_str(value, f"{path} {name}[{index}].{field}")
        rows.append(row)
    return rows


def dumps_jsonl(rows: list[Mapping[str, Any]]) -> str:
    lines = [
        json.dumps(dict(row), ensure_ascii=True, sort_keys=True, separators=(",", ":"))
        for row in rows
    ]
    return "\n".join(lines) + "\n"


def dumps_header(document: Mapping[str, Any]) -> str:
    return json.dumps(document, ensure_ascii=True, indent=2, sort_keys=True) + "\n"
