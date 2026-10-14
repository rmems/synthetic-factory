#!/usr/bin/env python3
"""AST-extract ``PAIRS`` / ``PLANTS`` catalogs from a CST mill source.

Evaluates only catalog constructor defs (``plant`` / ``ok`` / ``bad``) and
catalog assignments. Does not import or exec the mill publisher, so
``cst-mill*.py`` stay off this branch.
"""

from __future__ import annotations

import ast
import hashlib
import json
import re
import types
from collections.abc import Mapping
from pathlib import Path
from typing import Any, NamedTuple, TypeGuard

from .vocabulary import (
    CATALOG_ASSIGNMENT_NAMES,
    CATALOG_CONSTRUCTOR_NAMES,
    CATALOG_FILENAME,
    CATALOG_SCHEMA_ID,
    FACTORY,
    GENERATOR,
    LEGACY_REF,
    PAIR_FIELDS_15,
    PAIR_FIELDS_18,
    PLANT_ROW_KEYS,
    PRESERVE_COMMIT,
)

_ROUND_RE = re.compile(r"r(\d+)")
_SAFE_BUILTINS = {
    "dict": dict,
    "list": list,
    "tuple": tuple,
    "set": set,
    "frozenset": frozenset,
}

KIND_PAIRS = "pairs"
KIND_PLANTS = "plants"
KIND_LOOP = "loop"


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def mill_id_for_path(path: str) -> str:
    return Path(path).stem


def catalog_first_from_name(path: str) -> int | None:
    match = _ROUND_RE.search(Path(path).name)
    return int(match.group(1)) if match else None


def pair_fields_for_arity(arity: int) -> tuple[str, ...] | None:
    if arity == 15:
        return PAIR_FIELDS_15
    if arity == 18:
        return PAIR_FIELDS_18
    return None


def extract_catalog_namespace(source: str, *, filename: str = "<cst-mill>") -> dict[str, Any]:
    """Return catalog names bound from ``source`` without running mill I/O."""

    tree = ast.parse(source, filename=filename)
    namespace: dict[str, Any] = {}
    globals_ns: dict[str, Any] = {"__builtins__": _SAFE_BUILTINS}
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name in CATALOG_CONSTRUCTOR_NAMES:
            _define_constructor(node, filename, globals_ns)
            continue
        names = _assignment_names(node)
        if not names or not CATALOG_ASSIGNMENT_NAMES.intersection(names):
            continue
        _bind_catalog_assignment(node, namespace, globals_ns)
    return {name: namespace[name] for name in namespace if name in CATALOG_ASSIGNMENT_NAMES}


def _define_constructor(node: ast.FunctionDef, filename: str, globals_ns: dict[str, Any]) -> None:
    """Bind ``node`` into ``globals_ns`` the way a def statement would, without ``exec``."""

    module = ast.fix_missing_locations(ast.Module(body=[node], type_ignores=[]))
    code = compile(module, filename, "exec")
    function_code = next(
        item
        for item in code.co_consts
        if isinstance(item, types.CodeType) and item.co_name == node.name
    )
    defaults = tuple(_eval_expr(item, {}, globals_ns) for item in node.args.defaults)
    globals_ns[node.name] = types.FunctionType(
        function_code, globals_ns, node.name, defaults or None
    )


def _bind_catalog_assignment(
    node: ast.stmt, namespace: dict[str, Any], globals_ns: dict[str, Any]
) -> None:
    if isinstance(node, ast.Assign):
        value_node: ast.expr | None = node.value
    elif isinstance(node, ast.AnnAssign):
        value_node = node.value
    else:
        return
    if value_node is None:
        return
    value = _eval_expr(value_node, namespace, globals_ns)
    for name in _assignment_names(node):
        namespace[name] = value


def _lookup(name: str, namespace: dict[str, Any], globals_ns: dict[str, Any]) -> Any:
    if name in namespace:
        return namespace[name]
    if name in globals_ns and name != "__builtins__":
        return globals_ns[name]
    builtins = globals_ns.get("__builtins__")
    if isinstance(builtins, dict) and name in builtins:
        return builtins[name]
    raise NameError(name)


def _eval_expr(node: ast.expr, namespace: dict[str, Any], globals_ns: dict[str, Any]) -> Any:
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Name):
        return _lookup(node.id, namespace, globals_ns)
    if isinstance(node, ast.List):
        return [_eval_expr(item, namespace, globals_ns) for item in node.elts]
    if isinstance(node, ast.Tuple):
        return tuple(_eval_expr(item, namespace, globals_ns) for item in node.elts)
    if isinstance(node, ast.Dict):
        return _eval_dict(node, namespace, globals_ns)
    if isinstance(node, ast.Call):
        return _eval_call(node, namespace, globals_ns)
    raise ValueError(f"unsupported catalog expression: {type(node).__name__}")


def _eval_dict(
    node: ast.Dict, namespace: dict[str, Any], globals_ns: dict[str, Any]
) -> dict[Any, Any]:
    evaluated: dict[Any, Any] = {}
    for key, value in zip(node.keys, node.values, strict=True):
        if key is None:
            raise ValueError("unsupported catalog dict unpack")
        evaluated[_eval_expr(key, namespace, globals_ns)] = _eval_expr(value, namespace, globals_ns)
    return evaluated


def _eval_call(node: ast.Call, namespace: dict[str, Any], globals_ns: dict[str, Any]) -> Any:
    if not isinstance(node.func, ast.Name) or any(
        isinstance(arg, ast.Starred) for arg in node.args
    ):
        raise ValueError("unsupported catalog call")
    args = [_eval_expr(arg, namespace, globals_ns) for arg in node.args]
    kwargs: dict[str, Any] = {}
    for keyword in node.keywords:
        if keyword.arg is None:
            raise ValueError("unsupported catalog keyword unpack")
        kwargs[keyword.arg] = _eval_expr(keyword.value, namespace, globals_ns)
    func = _lookup(node.func.id, namespace, globals_ns)
    return func(*args, **kwargs)


def _assignment_names(node: ast.stmt) -> list[str]:
    if isinstance(node, ast.Assign):
        return [target.id for target in node.targets if isinstance(target, ast.Name)]
    if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
        return [node.target.id]
    return []


def _assigns_name(node: ast.stmt, name: str) -> TypeGuard[ast.Assign]:
    if not isinstance(node, ast.Assign):
        return False
    return any(isinstance(target, ast.Name) and target.id == name for target in node.targets)


def _joined_path_operand(value: ast.expr) -> str | None:
    if not isinstance(value, ast.BinOp) or not isinstance(value.op, ast.Div):
        return None
    if isinstance(value.right, ast.Constant) and isinstance(value.right.value, str):
        return value.right.value
    return None


def extract_joined_path_constant(source: str, name: str) -> str | None:
    """``NAME = <expr> / "relative/path"`` → the string operand, if that is the shape."""

    tree = ast.parse(source)
    for node in tree.body:
        if not _assigns_name(node, name):
            continue
        operand = _joined_path_operand(node.value)
        if operand is not None:
            return operand
    return None


def extract_mill_catalog(
    source: str,
    *,
    path: str,
    blob_sha: str = "",
) -> dict[str, Any]:
    """Structured catalog extract for one mill source file."""

    payload = source.encode()
    namespace = extract_catalog_namespace(source, filename=path)
    mill = _MillFile(path=path, mill_id=mill_id_for_path(path), blob_sha=blob_sha, payload=payload)
    named_first = catalog_first_from_name(path)
    if "PAIRS" in namespace:
        return _pairs_record(namespace, mill)
    if "PLANTS" in namespace:
        return _plants_record(namespace, mill, named_first=named_first)
    raise ValueError(f"{path} has no PAIRS or PLANTS catalog assignment")


class _MillFile(NamedTuple):
    """The mill source a catalog record describes: where it lives and its bytes."""

    path: str
    mill_id: str
    blob_sha: str
    payload: bytes


def _pairs_record(namespace: Mapping[str, Any], mill: _MillFile) -> dict[str, Any]:
    path, mill_id, blob_sha, payload = mill
    pairs = tuple(tuple(row) for row in namespace["PAIRS"])
    if not pairs:
        raise ValueError(f"{path}: PAIRS is empty")
    arities = {len(row) for row in pairs}
    if len(arities) != 1:
        raise ValueError(f"{path}: mixed PAIRS arities {sorted(arities)}")
    arity = arities.pop()
    fields = pair_fields_for_arity(arity)
    catalog_first = namespace.get("CATALOG_FIRST")
    if not isinstance(catalog_first, int):
        raise ValueError(f"{path}: CATALOG_FIRST must be an int")
    slug_index = 1
    return {
        "mill_id": mill_id,
        "path": path,
        "blob_sha": blob_sha,
        "sha256": sha256_bytes(payload),
        "kind": KIND_PAIRS,
        "catalog_first": catalog_first,
        "n_rows": len(pairs),
        "pair_arity": arity,
        "pair_fields": list(fields) if fields else None,
        "first_slug": pairs[0][slug_index],
        "last_slug": pairs[-1][slug_index],
        "generator": GENERATOR,
        "factory": FACTORY,
        "pairs": [list(row) for row in pairs],
    }


def _plants_record(
    namespace: Mapping[str, Any], mill: _MillFile, *, named_first: int | None
) -> dict[str, Any]:
    path, mill_id, blob_sha, payload = mill
    plants = tuple(namespace["PLANTS"])
    if not plants:
        raise ValueError(f"{path}: PLANTS is empty")
    for index, row in enumerate(plants):
        if not isinstance(row, dict):
            raise ValueError(f"{path}: PLANTS[{index}] is not a dict")
        missing = [key for key in PLANT_ROW_KEYS if key not in row]
        if missing:
            raise ValueError(f"{path}: PLANTS[{index}] missing {missing}")
    catalog_first = named_first
    max_rounds = namespace.get("MAX_ROUNDS")
    generator = namespace.get("GEN", GENERATOR)
    factory = namespace.get("FAC", FACTORY)
    return {
        "mill_id": mill_id,
        "path": path,
        "blob_sha": blob_sha,
        "sha256": sha256_bytes(payload),
        "kind": KIND_PLANTS,
        "catalog_first": catalog_first,
        "n_rows": len(plants),
        "max_rounds": max_rounds,
        "first_slug": plants[0]["slug_ok"],
        "last_slug": plants[-1]["slug_ok"],
        "generator": generator,
        "factory": factory,
        "plants": list(plants),
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
