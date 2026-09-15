#!/usr/bin/env python3
"""AST-extract NTP catalog identity from a mill source.

Evaluates only literal catalog assignments and constructor arguments.
Does not import, compile, or exec the mill publisher, so ``ntp-mill*.py``
stay off this branch.
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
    call_posargs,
    extract_chain_loop_range,
    extract_first_wave_table_mill,
    extract_named_mill_path,
    extract_replace_mill_target,
    extract_write_wave_mill,
    literal_value,
    parse_tree,
)
from .vocabulary import (
    CATALOG_FILENAME,
    CATALOG_SCHEMA_ID,
    FACTORY,
    GENERATOR,
    KIND_PAIRS,
    LEGACY_REF,
    PLANT_PREFIX,
    PRESERVE_COMMIT,
    SLICE_ID,
    SLICE_MILL_ID,
)

SHAPE_S_FROM = "s-from-l-from"
SHAPE_S_L_KW = "S-L-kwargs"

_S_FROM_SLUG = 1
_S_FROM_STEM = 2
_S_FROM_ARTIFACT = 4
_L_FROM_SLUG = 1
_L_FROM_STEM = 2
_L_FROM_LEFTOVER = 3


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
    tree = parse_tree(source, filename=path)
    mill_id = mill_id_for_path(path)
    constants = _module_constants(tree)
    factory = constants.get("FACTORY", FACTORY)
    generator = constants.get("GEN", GENERATOR)
    catalog_first = constants.get("START")
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
    s_from = _s_from_lists(tree)
    if s_from is not None:
        return s_from
    kwargs = _s_l_kwargs_lists(tree)
    if kwargs is not None:
        return kwargs
    raise ValueError(f"{path} has no extractable NTP catalog assignment")


def _s_from_lists(tree: ast.AST) -> dict[str, Any] | None:
    success_nodes, leftover_nodes = _named_lists(tree, "SUCCESS", "LEFTOVER")
    if success_nodes is None or leftover_nodes is None:
        return None
    if not success_nodes or not leftover_nodes:
        return None
    if not all(call_name(elt) == "s_from" for elt in success_nodes):
        return None
    if not all(call_name(elt) == "l_from" for elt in leftover_nodes):
        return None
    success = [_s_from_identity(elt) for elt in success_nodes]
    leftover = [_l_from_identity(elt) for elt in leftover_nodes]
    if any(row["slug"] is None for row in (*success, *leftover)):
        return None
    return _theme_record(SHAPE_S_FROM, success, leftover)


def _s_l_kwargs_lists(tree: ast.AST) -> dict[str, Any] | None:
    success_nodes, leftover_nodes = _named_lists(tree, "SUCCESS", "LEFTOVER")
    if success_nodes is None or leftover_nodes is None:
        return None
    if not success_nodes or not leftover_nodes:
        return None
    if not all(call_name(elt) == "S" for elt in success_nodes):
        return None
    if not all(call_name(elt) == "L" for elt in leftover_nodes):
        return None
    success = [_s_kwargs_identity(elt) for elt in success_nodes]
    leftover = [_l_kwargs_identity(elt) for elt in leftover_nodes]
    if any(row["slug"] is None for row in (*success, *leftover)):
        return None
    return _theme_record(SHAPE_S_L_KW, success, leftover)


def _named_lists(tree: ast.AST, *names: str) -> tuple[list[Any] | None, ...]:
    found: dict[str, list[Any]] = {}
    for node in getattr(tree, "body", ()):
        name, value = assignment_of(node)
        if name in names and value is not None and hasattr(value, "elts"):
            found[name] = list(value.elts)
    return tuple(found.get(name) for name in names)


def _s_from_identity(node: Any) -> dict[str, Any]:
    args = call_posargs(node)
    if args is None or len(args) < _S_FROM_ARTIFACT + 1:
        return {"slug": None, "stem": None, "plant": None, "artifact": None, "index": None}
    stem = args[_S_FROM_STEM]
    return {
        "index": args[0] if isinstance(args[0], int) else None,
        "slug": args[_S_FROM_SLUG] if isinstance(args[_S_FROM_SLUG], str) else None,
        "stem": stem if isinstance(stem, str) else None,
        "plant": f"{PLANT_PREFIX}{stem}" if isinstance(stem, str) else None,
        "artifact": args[_S_FROM_ARTIFACT] if isinstance(args[_S_FROM_ARTIFACT], str) else None,
    }


def _l_from_identity(node: Any) -> dict[str, Any]:
    args = call_posargs(node)
    if args is None or len(args) < _L_FROM_LEFTOVER + 1:
        return {"slug": None, "stem": None, "plant": None, "leftover": None, "index": None}
    stem = args[_L_FROM_STEM]
    leftover = args[_L_FROM_LEFTOVER]
    return {
        "index": args[0] if isinstance(args[0], int) else None,
        "slug": args[_L_FROM_SLUG] if isinstance(args[_L_FROM_SLUG], str) else None,
        "stem": stem if isinstance(stem, str) else None,
        "plant": f"{PLANT_PREFIX}{stem}" if isinstance(stem, str) else None,
        "leftover": leftover if isinstance(leftover, str) else None,
    }


def _s_kwargs_identity(node: Any) -> dict[str, Any]:
    kwargs = call_kwargs(node) or {}
    stem = kwargs.get("stem")
    return {
        "slug": kwargs.get("slug") if isinstance(kwargs.get("slug"), str) else None,
        "stem": stem if isinstance(stem, str) else None,
        "plant": f"{PLANT_PREFIX}{stem}" if isinstance(stem, str) else None,
        "artifact": kwargs.get("artifact") if isinstance(kwargs.get("artifact"), str) else None,
    }


def _l_kwargs_identity(node: Any) -> dict[str, Any]:
    kwargs = call_kwargs(node) or {}
    stem = kwargs.get("stem")
    leftover = kwargs.get("leftover")
    return {
        "slug": kwargs.get("slug") if isinstance(kwargs.get("slug"), str) else None,
        "stem": stem if isinstance(stem, str) else None,
        "plant": f"{PLANT_PREFIX}{stem}" if isinstance(stem, str) else None,
        "leftover": leftover if isinstance(leftover, str) else None,
    }


def _theme_record(
    shape: str,
    success: list[dict[str, Any]],
    leftover: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "shape": shape,
        "n_success": len(success),
        "n_leftover": len(leftover),
        "n_rows": len(success),
        "first_slug": success[0]["slug"],
        "last_slug": success[-1]["slug"],
        "first_leftover_slug": leftover[0]["slug"],
        "last_leftover_slug": leftover[-1]["slug"],
        "success": success,
        "leftover": leftover,
    }


def extract_companion_path(source: str) -> str | None:
    """Mill path a loop / plant-gen actually drives. Never follows host imports."""

    replace = extract_replace_mill_target(source)
    if replace is not None:
        return replace
    for name in ("MILL", "NTP_GEN", "GEN", "OUT"):
        found = extract_named_mill_path(source, name)
        if found is not None:
            return found
    wave = extract_write_wave_mill(source)
    if wave is not None:
        return wave
    return extract_first_wave_table_mill(source)


def extract_chain_bounds(source: str) -> tuple[int, int] | None:
    return extract_chain_loop_range(source)


def mill_summary(record: Mapping[str, Any], *, include_themes: bool) -> dict[str, Any]:
    """Catalog mill row: identity plus optional leftover-slice theme lists."""

    summary = {
        "mill_id": record["mill_id"],
        "path": record["path"],
        "blob_sha": record["blob_sha"],
        "sha256": record["sha256"],
        "kind": record["kind"],
        "shape": record["shape"],
        "catalog_first": record["catalog_first"],
        "n_rows": record["n_rows"],
        "n_success": record["n_success"],
        "n_leftover": record["n_leftover"],
        "first_slug": record["first_slug"],
        "last_slug": record["last_slug"],
        "first_leftover_slug": record["first_leftover_slug"],
        "last_leftover_slug": record["last_leftover_slug"],
        "generator": record["generator"],
        "factory": record["factory"],
    }
    if include_themes:
        summary["success"] = list(record.get("success") or ())
        summary["leftover"] = list(record.get("leftover") or ())
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
