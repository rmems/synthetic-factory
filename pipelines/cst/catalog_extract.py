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
from collections.abc import Mapping
from pathlib import Path
from typing import Any

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
            exec(compile(ast.Module(body=[node], type_ignores=[]), filename, "exec"), globals_ns, namespace)
            globals_ns[node.name] = namespace[node.name]
            continue
        names = _assignment_names(node)
        if not names or not CATALOG_ASSIGNMENT_NAMES.intersection(names):
            continue
        exec(compile(ast.Module(body=[node], type_ignores=[]), filename, "exec"), globals_ns, namespace)
    return {name: namespace[name] for name in namespace if name in CATALOG_ASSIGNMENT_NAMES}


def _assignment_names(node: ast.stmt) -> list[str]:
    if isinstance(node, ast.Assign):
        return [target.id for target in node.targets if isinstance(target, ast.Name)]
    if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
        return [node.target.id]
    return []


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


def extract_mill_catalog(
    source: str,
    *,
    path: str,
    blob_sha: str = "",
) -> dict[str, Any]:
    """Structured catalog extract for one mill source file."""

    payload = source.encode()
    namespace = extract_catalog_namespace(source, filename=path)
    mill_id = mill_id_for_path(path)
    named_first = catalog_first_from_name(path)
    if "PAIRS" in namespace:
        return _pairs_record(namespace, path=path, mill_id=mill_id, blob_sha=blob_sha, payload=payload)
    if "PLANTS" in namespace:
        return _plants_record(
            namespace,
            path=path,
            mill_id=mill_id,
            blob_sha=blob_sha,
            payload=payload,
            named_first=named_first,
        )
    raise ValueError(f"{path} has no PAIRS or PLANTS catalog assignment")


def _pairs_record(
    namespace: Mapping[str, Any],
    *,
    path: str,
    mill_id: str,
    blob_sha: str,
    payload: bytes,
) -> dict[str, Any]:
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
    namespace: Mapping[str, Any],
    *,
    path: str,
    mill_id: str,
    blob_sha: str,
    payload: bytes,
    named_first: int | None,
) -> dict[str, Any]:
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
