#!/usr/bin/env python3
"""AST-extract MDB catalog identity from a mill source.

Evaluates only literal catalog assignments and constructor positional
arguments. Does not import, compile, or exec the mill publisher, so
``mdb-mill*.py`` stay off this branch.
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
    call_posargs,
    extract_source_path,
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
    SLICE_ID,
    SLICE_MILL_ID,
)

SHAPE_LITERAL = "pairs-literal"
SHAPE_P_CTOR = "pairs-p-ctor"
SHAPE_TOOLS = "tools-make"
SHAPE_RAW = "raw-expand"
SHAPE_R_CTOR = "raw-r-ctor"
SHAPE_SLUGS = "slugs-row"

P_SLUG = 0
P_PLANT = 1
P_FAIL = 6
R_PKG = 0
R_EXT = 1
R_LEFTOVER = 2
COMPANION_NAMES = ("MILL", "OUT", "MDB_MILL")


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
    rebuilt = _literal_pairs(tree)
    if rebuilt is not None:
        return rebuilt
    p_ctor = _p_ctor_pairs(tree)
    if p_ctor is not None:
        return p_ctor
    slugs = _slugs_pairs(tree)
    if slugs is not None:
        return slugs
    r_ctor = _r_ctor_pairs(tree)
    if r_ctor is not None:
        return r_ctor
    raw = _raw_pairs(tree)
    if raw is not None:
        return raw
    tools = _tools_pairs(tree)
    if tools is not None:
        return tools
    raise ValueError(f"{path} has no extractable MDB catalog assignment")


def _literal_pairs(tree: ast.AST) -> dict[str, Any] | None:
    for node in getattr(tree, "body", ()):
        name, value = assignment_of(node)
        if name != "PAIRS" or not isinstance(value, ast.List) or not value.elts:
            continue
        rows: list[dict[str, Any]] = []
        for elt in value.elts:
            row = _literal_pair_identity(elt)
            if row is None:
                rows = []
                break
            rows.append(row)
        if rows:
            return _rows_record(SHAPE_LITERAL, rows)
    return None


def _literal_pair_identity(node: ast.AST) -> dict[str, Any] | None:
    resolved = literal_value(node)
    if not isinstance(resolved, (tuple, list)) or len(resolved) != 2:
        return None
    success, fail = resolved
    if not isinstance(success, dict) or not isinstance(fail, dict):
        return None
    success_slug = success.get("slug")
    fail_slug = fail.get("slug")
    if not isinstance(success_slug, str) or not isinstance(fail_slug, str):
        return None
    return {
        "success_slug": success_slug,
        "fail_slug": fail_slug,
        "success_plant": success.get("plant") if isinstance(success.get("plant"), str) else None,
        "fail_plant": fail.get("plant") if isinstance(fail.get("plant"), str) else None,
        "fail": bool(fail.get("fail", True)),
    }


def _p_ctor_pairs(tree: ast.AST) -> dict[str, Any] | None:
    for node in getattr(tree, "body", ()):
        name, value = assignment_of(node)
        if name != "PAIRS" or not isinstance(value, ast.List) or not value.elts:
            continue
        if not all(_is_p_tuple(elt) for elt in value.elts):
            continue
        rows = []
        for elt in value.elts:
            row = _p_pair_identity(elt)
            if row is None:
                return None
            rows.append(row)
        return _rows_record(SHAPE_P_CTOR, rows)
    return None


def _is_p_tuple(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.Tuple)
        and len(node.elts) == 2
        and call_name(node.elts[0]) == "P"
        and call_name(node.elts[1]) == "P"
    )


def _p_pair_identity(node: ast.AST) -> dict[str, Any] | None:
    assert isinstance(node, ast.Tuple)
    success = call_posargs(node.elts[0])
    fail = call_posargs(node.elts[1])
    if success is None or fail is None:
        return None
    if len(success) <= P_PLANT or len(fail) <= P_PLANT:
        return None
    if not isinstance(success[P_SLUG], str) or not isinstance(fail[P_SLUG], str):
        return None
    fail_flag = fail[P_FAIL] if len(fail) > P_FAIL else True
    return {
        "success_slug": success[P_SLUG],
        "fail_slug": fail[P_SLUG],
        "success_plant": success[P_PLANT] if isinstance(success[P_PLANT], str) else None,
        "fail_plant": fail[P_PLANT] if isinstance(fail[P_PLANT], str) else None,
        "fail": bool(fail_flag),
    }


def _slugs_pairs(tree: ast.AST) -> dict[str, Any] | None:
    for node in getattr(tree, "body", ()):
        name, value = assignment_of(node)
        if name != "SLUGS" or value is None:
            continue
        resolved = literal_value(value)
        if not isinstance(resolved, list) or not resolved:
            return None
        if not all(isinstance(item, str) for item in resolved):
            return None
        return _slug_rows(SHAPE_SLUGS, [str(item) for item in resolved])
    return None


def _r_ctor_pairs(tree: ast.AST) -> dict[str, Any] | None:
    for node in getattr(tree, "body", ()):
        name, value = assignment_of(node)
        if name != "RAW" or not isinstance(value, ast.List) or not value.elts:
            continue
        if not all(call_name(elt) == "R" for elt in value.elts):
            continue
        slugs: list[str] = []
        for elt in value.elts:
            args = call_posargs(elt)
            if args is None or len(args) < 3:
                return None
            pkg, ext, leftover = args[R_PKG], args[R_EXT], args[R_LEFTOVER]
            if not isinstance(pkg, str) or not isinstance(ext, str) or not isinstance(leftover, str):
                return None
            slugs.append(f"{pkg}-{ext}-leftover-{leftover}")
        return _slug_rows(SHAPE_R_CTOR, slugs)
    return None


def _raw_pairs(tree: ast.AST) -> dict[str, Any] | None:
    for node in getattr(tree, "body", ()):
        name, value = assignment_of(node)
        if name != "RAW" or value is None:
            continue
        resolved = literal_value(value)
        if not isinstance(resolved, list) or not resolved:
            continue
        slugs: list[str] = []
        for row in resolved:
            if not isinstance(row, (tuple, list)) or not row or not isinstance(row[0], str):
                return None
            slugs.append(row[0])
        return _slug_rows(SHAPE_RAW, slugs)
    return None


def _tools_pairs(tree: ast.AST) -> dict[str, Any] | None:
    for node in getattr(tree, "body", ()):
        name, value = assignment_of(node)
        if name != "TOOLS" or value is None:
            continue
        resolved = literal_value(value)
        if not isinstance(resolved, list) or not resolved:
            continue
        slugs: list[str] = []
        for row in resolved:
            if not isinstance(row, (tuple, list)) or not row or not isinstance(row[0], str):
                return None
            slugs.append(row[0])
        return _slug_rows(SHAPE_TOOLS, slugs)
    return None


def _slug_rows(shape: str, slugs: list[str]) -> dict[str, Any] | None:
    if len(slugs) < 2 or len(slugs) % 2 != 0:
        return None
    rows = [
        {
            "success_slug": slugs[index],
            "fail_slug": slugs[index + 1],
            "success_plant": None,
            "fail_plant": None,
            "fail": True,
        }
        for index in range(0, len(slugs), 2)
    ]
    return _rows_record(shape, rows)


def _rows_record(shape: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "shape": shape,
        "n_rows": len(rows),
        "first_slug": rows[0]["success_slug"],
        "last_slug": rows[-1]["success_slug"],
        "pairs": rows,
    }


def extract_companion_path(source: str) -> str | None:
    """``MILL`` / ``OUT`` / ``MDB_MILL`` joined-path constant from a loop or gen."""

    return extract_source_path(source, COMPANION_NAMES)


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
