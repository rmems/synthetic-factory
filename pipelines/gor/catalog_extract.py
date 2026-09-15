#!/usr/bin/env python3
"""AST-extract GOR catalog identity from a mill source.

Evaluates only literal catalog assignments and constructor arguments.
Does not import, compile, or exec the mill publisher, so ``gor-mill*.py``
stay off this branch. Chained mills contribute the pairs declared in that
file (``PAIRS`` / ``NEW_PAIRS`` / ``MORE_PAIRS`` / ``MORE`` / ``add``), not
the inherited parent catalog.
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
    call_name,
    call_positional,
    ctor_kwargs,
    extract_joined_path_assignment,
    literal_value,
)
from .vocabulary import (
    CATALOG_FILENAME,
    CATALOG_SCHEMA_ID,
    FACTORY,
    GENERATOR,
    KIND_PAIRS,
    LEGACY_REF,
    PRESERVE_COMMIT,
    SHAPE_ADD,
    SHAPE_GITCFG,
    SHAPE_LEFTOVER_PLANT,
    SHAPE_LITERAL,
    SHAPE_PLANT,
    SHAPE_S_H,
    SLICE_ID,
    SLICE_MILL_ID,
)

_PAIR_LISTS = ("PAIRS", "NEW_PAIRS", "MORE_PAIRS", "MORE")


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
        catalog_first = constants.get("_CATALOG_START")
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
    listed = _listed_pairs(tree)
    if listed is not None:
        return listed
    added = _add_pairs(tree)
    if added is not None:
        return added
    raise ValueError(f"{path} has no extractable GOR catalog assignment")


def _listed_pairs(tree: ast.AST) -> dict[str, Any] | None:
    collected: list[dict[str, Any]] = []
    n_new = 0
    n_more = 0
    shape: str | None = None
    for node in getattr(tree, "body", ()):
        name, value = assignment_of(node)
        if name not in _PAIR_LISTS or not isinstance(value, ast.List):
            continue
        if not value.elts:
            continue
        rows: list[dict[str, Any]] = []
        for elt in value.elts:
            row = _pair_identity(elt)
            if row is None:
                return None
            rows.append(row)
        if not rows:
            continue
        found = _shape_for_element(value.elts[0])
        if found is None:
            return None
        if shape is None:
            shape = found
        elif shape != found and {shape, found} != {SHAPE_LEFTOVER_PLANT, SHAPE_PLANT}:
            # r1127 leftover_plant lists stay leftover; mixed plant+leftover
            # is leftover-plant (the later constructor wraps plant).
            shape = SHAPE_LEFTOVER_PLANT if "leftover" in (shape, found) else found
        collected.extend(rows)
        if name == "NEW_PAIRS":
            n_new += len(rows)
        elif name in {"MORE_PAIRS", "MORE"}:
            n_more += len(rows)
    if not collected or shape is None:
        return None
    record = _rows_record(shape, collected)
    if n_new or n_more:
        record["n_new"] = n_new
        record["n_more"] = n_more
    return record


def _add_pairs(tree: ast.AST) -> dict[str, Any] | None:
    rows: list[dict[str, Any]] = []
    for node in getattr(tree, "body", ()):
        if not isinstance(node, ast.Expr) or not isinstance(node.value, ast.Call):
            continue
        if call_name(node.value) != "add":
            continue
        args = call_positional(node.value)
        if args is None or len(args) != 2:
            return None
        row = _specs_identity(args[0], args[1])
        if row is None:
            return None
        rows.append(row)
    if not rows:
        return None
    return _rows_record(SHAPE_ADD, rows)


def _pair_identity(node: ast.AST) -> dict[str, Any] | None:
    if call_name(node) == "_pair":
        args = call_positional(node)
        if args is None or len(args) != 2:
            return None
        return _specs_identity(args[0], args[1])
    if isinstance(node, ast.Tuple) and len(node.elts) == 2:
        return _specs_identity(node.elts[0], node.elts[1])
    return None


def _specs_identity(success_node: ast.AST, fail_node: ast.AST) -> dict[str, Any] | None:
    success = _spec_identity(success_node)
    fail = _spec_identity(fail_node)
    if success is None or fail is None:
        return None
    if not isinstance(success.get("slug"), str) or not isinstance(fail.get("slug"), str):
        return None
    return {
        "success_slug": success["slug"],
        "fail_slug": fail["slug"],
        "success_marker": success.get("marker"),
        "fail_marker": fail.get("marker"),
        "success_stem": success.get("stem"),
        "fail_stem": fail.get("stem"),
        "fail_handoff": bool(fail.get("handoff")),
    }


def _spec_identity(node: ast.AST) -> dict[str, Any] | None:
    if isinstance(node, ast.Dict):
        resolved = literal_value(node)
        return resolved if isinstance(resolved, dict) else None
    kwargs = ctor_kwargs(node)
    return kwargs


def _shape_for_element(node: ast.AST) -> str | None:
    if call_name(node) == "_pair":
        args = call_positional(node)
        if args is None or not args:
            return None
        name = call_name(args[0])
        if name in {"gitcfg", "_cfg"}:
            return SHAPE_GITCFG
        if name in {"cmdplant", "_cmd", "leftover_plant"}:
            return SHAPE_LEFTOVER_PLANT
        if name == "plant":
            return SHAPE_PLANT
        return SHAPE_ADD
    if not isinstance(node, ast.Tuple) or len(node.elts) != 2:
        return None
    left = node.elts[0]
    if isinstance(left, ast.Dict):
        return SHAPE_LITERAL
    name = call_name(left)
    if name == "_S":
        return SHAPE_S_H
    if name == "plant":
        return SHAPE_PLANT
    if name == "leftover_plant":
        return SHAPE_LEFTOVER_PLANT
    if name in {"gitcfg", "_cfg"}:
        return SHAPE_GITCFG
    return None


def _rows_record(shape: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "shape": shape,
        "n_rows": len(rows),
        "first_slug": rows[0]["success_slug"],
        "last_slug": rows[-1]["success_slug"],
        "pairs": rows,
    }


def normalize_companion_path(path: str | None) -> str | None:
    if path is None:
        return None
    if "/" in path:
        return path
    if path.startswith("gor-mill-") and path.endswith(".py"):
        return f"experiments/{path}"
    return path


def extract_companion_path(source: str) -> str | None:
    """``MILL`` joined-path constant from a loop / plant-gen script."""

    found = extract_joined_path_assignment(source, "MILL")
    return normalize_companion_path(found)


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
        "first_slug": record["first_slug"],
        "last_slug": record["last_slug"],
        "generator": record["generator"],
        "factory": record["factory"],
    }
    if "n_new" in record:
        summary["n_new"] = record["n_new"]
        summary["n_more"] = record["n_more"]
    if include_pairs:
        summary["pairs"] = list(record.get("pairs") or ())
    return summary


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
