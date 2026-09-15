#!/usr/bin/env python3
"""AST-extract ``CATALOG`` / ``PAIRS`` from a DPR mill source.

Reads mill text through :func:`ast.parse` only. Constructor calls
(``OK`` / ``FAIL`` / ``okp`` / ``failp``) are lowered to literals; the mill
publisher, ``round_txn``, and hopper scripts are never imported or executed.
"""

from __future__ import annotations

import ast
import hashlib
import json
import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from .vocabulary import (
    CATALOG_ASSIGNMENT_NAMES,
    CATALOG_FILENAME,
    CATALOG_SCHEMA_ID,
    FACTORY,
    GENERATOR,
    HOPPER_NAME_NEEDLES,
    KIND_GEN,
    KIND_HOPPER,
    KIND_LOOP,
    KIND_PAIRS,
    KIND_PLANTS,
    LEGACY_REF,
    LEFTOVER_PLANT_KEYS,
    PAIR_CTOR_NAMES,
    PRESERVE_COMMIT,
)

_ROUND_RE = re.compile(r"r(\d+)")


class DprExtractError(ValueError):
    """A mill source is not a constant catalog (or is an excluded hopper)."""


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def mill_id_for_path(path: str) -> str:
    return Path(path).stem


def catalog_first_from_name(path: str) -> int | None:
    match = _ROUND_RE.search(Path(path).name)
    return int(match.group(1)) if match else None


def is_hopper_path(path: str) -> bool:
    name = Path(path).name.lower()
    return any(needle in name for needle in HOPPER_NAME_NEEDLES)


def _jsonable(value: Any) -> Any:
    if isinstance(value, tuple):
        return [_jsonable(item) for item in value]
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {key: _jsonable(item) for key, item in value.items()}
    return value


def _const_eval(node: ast.AST) -> Any:
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.List):
        return [_const_eval(item) for item in node.elts]
    if isinstance(node, ast.Tuple):
        return [_const_eval(item) for item in node.elts]
    if isinstance(node, ast.Set):
        return [_const_eval(item) for item in node.elts]
    if isinstance(node, ast.Dict):
        if any(key is None for key in node.keys):
            raise DprExtractError("catalog dict uses unpacking")
        return {
            _const_eval(key): _const_eval(value)
            for key, value in zip(node.keys, node.values)
        }
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        return -_const_eval(node.operand)
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.UAdd):
        return +_const_eval(node.operand)
    raise DprExtractError(f"catalog node is not a constant ({type(node).__name__})")


def _assignment_names(node: ast.stmt) -> list[str]:
    if isinstance(node, ast.Assign):
        return [target.id for target in node.targets if isinstance(target, ast.Name)]
    if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
        return [node.target.id]
    return []


def _assignment_value(node: ast.stmt) -> ast.AST | None:
    if isinstance(node, ast.Assign):
        return node.value
    if isinstance(node, ast.AnnAssign):
        return node.value
    return None


def extract_catalog_nodes(source: str, *, filename: str = "<dpr-mill>") -> dict[str, ast.AST]:
    """Top-level catalog assignments as AST nodes. Never evaluates them."""

    try:
        tree = ast.parse(source, filename=filename)
    except SyntaxError as exc:
        raise DprExtractError(f"{filename} does not parse: {exc}") from exc
    found: dict[str, ast.AST] = {}
    for node in tree.body:
        names = _assignment_names(node)
        value = _assignment_value(node)
        if value is None:
            continue
        for name in names:
            if name in CATALOG_ASSIGNMENT_NAMES:
                found[name] = value
    return found


def _literal_or_none(node: ast.AST) -> Any | None:
    try:
        return _const_eval(node)
    except DprExtractError:
        return None


def _extract_ctor(node: ast.AST) -> dict[str, Any]:
    if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Name):
        raise DprExtractError(f"pair side is not a constructor call ({type(node).__name__})")
    ctor = node.func.id
    if ctor not in PAIR_CTOR_NAMES:
        raise DprExtractError(f"pair side uses unknown constructor {ctor!r}")
    if any(isinstance(arg, ast.Starred) for arg in node.args):
        raise DprExtractError(f"{ctor}() uses starred arguments")
    if any(keyword.arg is None for keyword in node.keywords):
        raise DprExtractError(f"{ctor}() uses keyword unpacking")
    row: dict[str, Any] = {"ctor": ctor}
    if node.args:
        row["args"] = [_const_eval(arg) for arg in node.args]
    if node.keywords:
        row["kwargs"] = {keyword.arg: _const_eval(keyword.value) for keyword in node.keywords}
    if "args" not in row and "kwargs" not in row:
        raise DprExtractError(f"{ctor}() has no arguments")
    return row


def _ctor_slug(side: Mapping[str, Any]) -> str:
    kwargs = side.get("kwargs")
    if isinstance(kwargs, dict) and isinstance(kwargs.get("slug"), str) and kwargs["slug"]:
        return kwargs["slug"]
    args = side.get("args")
    if isinstance(args, list) and args and isinstance(args[0], str) and args[0]:
        return args[0]
    raise DprExtractError("pair side has no slug")


def _pair_from_tuple(node: ast.AST) -> dict[str, Any]:
    if not isinstance(node, ast.Tuple) or len(node.elts) != 2:
        raise DprExtractError("PAIRS row is not an (ok, fail) tuple")
    ok = _extract_ctor(node.elts[0])
    fail = _extract_ctor(node.elts[1])
    return {
        "ok": ok,
        "fail": fail,
        "slug": _ctor_slug(ok),
        "fail_slug": _ctor_slug(fail),
    }


def _list_rows(node: ast.AST) -> list[ast.AST]:
    if not isinstance(node, ast.List):
        raise DprExtractError("catalog assignment is not a list literal")
    return list(node.elts)


def _catalog_list_name(nodes: Mapping[str, ast.AST]) -> str:
    for name in ("NEW_PAIRS", "MORE", "PAIRS", "CATALOG"):
        value = nodes.get(name)
        if value is None:
            continue
        if name == "PAIRS" and not isinstance(value, ast.List):
            continue
        if isinstance(value, ast.List):
            return name
    raise DprExtractError("source has no list-literal CATALOG / PAIRS / NEW_PAIRS / MORE")


def extract_joined_path_constant(source: str, name: str) -> str | None:
    """``NAME = <expr> / "relative/path"`` → the string operand, if that is the shape."""

    tree = ast.parse(source)
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if not any(isinstance(target, ast.Name) and target.id == name for target in node.targets):
            continue
        value = node.value
        if isinstance(value, ast.BinOp) and isinstance(value.op, ast.Div):
            if isinstance(value.right, ast.Constant) and isinstance(value.right.value, str):
                return value.right.value
    return None


def extract_call_path_constant(source: str, name: str) -> str | None:
    """``NAME = Path("/tmp/dpr_mill_rNNNN.py")`` → the string operand."""

    tree = ast.parse(source)
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if not any(isinstance(target, ast.Name) and target.id == name for target in node.targets):
            continue
        value = node.value
        if (
            isinstance(value, ast.Call)
            and isinstance(value.func, ast.Name)
            and value.func.id == "Path"
            and len(value.args) == 1
            and isinstance(value.args[0], ast.Constant)
            and isinstance(value.args[0].value, str)
        ):
            return value.args[0].value
    return None


def _refuse_hopper(path: str) -> None:
    if is_hopper_path(path):
        raise DprExtractError(f"{path} is an lrd hopper; excluded from the dpr catalog")


def extract_mill_catalog(
    source: str,
    *,
    path: str,
    blob_sha: str = "",
) -> dict[str, Any]:
    """Structured catalog extract for one mill source file. Never execs."""

    _refuse_hopper(path)
    payload = source.encode()
    nodes = extract_catalog_nodes(source, filename=path)
    mill_id = mill_id_for_path(path)
    named_first = catalog_first_from_name(path)
    list_name = _catalog_list_name(nodes)
    if list_name == "CATALOG":
        return _plants_record(
            nodes,
            path=path,
            mill_id=mill_id,
            blob_sha=blob_sha,
            payload=payload,
            named_first=named_first,
        )
    return _pairs_record(
        nodes,
        list_name=list_name,
        path=path,
        mill_id=mill_id,
        blob_sha=blob_sha,
        payload=payload,
        named_first=named_first,
    )


def _optional_int(nodes: Mapping[str, ast.AST], name: str) -> int | None:
    node = nodes.get(name)
    if node is None:
        return None
    value = _literal_or_none(node)
    if type(value) is int:
        return value
    return None


def _optional_text(nodes: Mapping[str, ast.AST], name: str) -> str | None:
    node = nodes.get(name)
    if node is None:
        return None
    value = _literal_or_none(node)
    return value if isinstance(value, str) and value else None


def _plants_record(
    nodes: Mapping[str, ast.AST],
    *,
    path: str,
    mill_id: str,
    blob_sha: str,
    payload: bytes,
    named_first: int | None,
) -> dict[str, Any]:
    plants = [_jsonable(_const_eval(item)) for item in _list_rows(nodes["CATALOG"])]
    if not plants:
        raise DprExtractError(f"{path}: CATALOG is empty")
    for index, row in enumerate(plants):
        if not isinstance(row, dict):
            raise DprExtractError(f"{path}: CATALOG[{index}] is not a dict")
        missing = [key for key in LEFTOVER_PLANT_KEYS if key not in row]
        if missing:
            raise DprExtractError(f"{path}: CATALOG[{index}] missing {missing}")
        if not isinstance(row["slug"], str) or not row["slug"]:
            raise DprExtractError(f"{path}: CATALOG[{index}].slug is empty")
    factory = _optional_text(nodes, "FACTORY") or FACTORY
    generator = _optional_text(nodes, "GEN") or _optional_text(nodes, "GENERATOR") or GENERATOR
    return {
        "mill_id": mill_id,
        "path": path,
        "blob_sha": blob_sha,
        "sha256": sha256_bytes(payload),
        "kind": KIND_PLANTS,
        "catalog_first": named_first,
        "n_rows": len(plants),
        "max_rounds": _optional_int(nodes, "MAX_ROUNDS"),
        "first_slug": plants[0]["slug"],
        "last_slug": plants[-1]["slug"],
        "generator": generator,
        "factory": factory,
        "plants": plants,
    }


def _pairs_record(
    nodes: Mapping[str, ast.AST],
    *,
    list_name: str,
    path: str,
    mill_id: str,
    blob_sha: str,
    payload: bytes,
    named_first: int | None,
) -> dict[str, Any]:
    pairs = [_jsonable(_pair_from_tuple(item)) for item in _list_rows(nodes[list_name])]
    if not pairs:
        raise DprExtractError(f"{path}: {list_name} is empty")
    catalog_first = _optional_int(nodes, "START") or named_first
    generator = _optional_text(nodes, "GENERATOR") or GENERATOR
    return {
        "mill_id": mill_id,
        "path": path,
        "blob_sha": blob_sha,
        "sha256": sha256_bytes(payload),
        "kind": KIND_PAIRS,
        "list_name": list_name,
        "catalog_first": catalog_first,
        "n_rows": len(pairs),
        "first_slug": pairs[0]["slug"],
        "last_slug": pairs[-1]["slug"],
        "generator": generator,
        "factory": FACTORY,
        "pairs": pairs,
    }


def catalog_document(mills: list[dict[str, Any]]) -> dict[str, Any]:
    pair_rows = sum(mill["n_rows"] for mill in mills if mill["kind"] == KIND_PAIRS)
    plant_rows = sum(mill["n_rows"] for mill in mills if mill["kind"] == KIND_PLANTS)
    return {
        "schema": CATALOG_SCHEMA_ID,
        "source_ref": LEGACY_REF,
        "preserve_commit": PRESERVE_COMMIT,
        "factory": FACTORY,
        "generator": GENERATOR,
        "n_mills": len(mills),
        "n_pair_rows": pair_rows,
        "n_plant_rows": plant_rows,
        "excluded_kinds": [KIND_HOPPER, KIND_LOOP, KIND_GEN],
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
