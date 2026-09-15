#!/usr/bin/env python3
"""AST-extract LHC catalog identity from a mill source.

Parses only literals and constructor arguments (``ast.parse``). There is no
``exec`` / ``eval`` / ``compile``, so ``lhc-mill*.py`` stay off this branch.
Plant tables live in :mod:`lhc.catalog_extract_plants`; pair rows live in
:mod:`lhc.catalog_extract_pairs`.
"""

from __future__ import annotations

import ast
import hashlib
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from .catalog_ast import UNSET, assignment_of, literal_value
from .catalog_extract_fn_pair import fn_pair_appends
from .catalog_extract_pairs import (
    SHAPE_PAIRS_FN_PAIR,
    SHAPE_PAIRS_NAMED,
    SHAPE_PLANTS_MK_FN,
    SHAPE_PLANTS_NAMED,
    SHAPE_PLANTS_P_FN,
    named_or_fn_pairs,
    pairs_shape,
    rows_record,
)
from .catalog_extract_plants import plant_count, plants_context
from .vocabulary import (
    CATALOG_SCHEMA_ID,
    FACTORY,
    GENERATOR,
    KIND_PAIRS,
    LEGACY_REF,
    PRESERVE_COMMIT,
    SLICE_ID,
    SLICE_MILL_ID,
)

__all__ = (
    "SHAPE_PAIRS_FN_PAIR",
    "SHAPE_PAIRS_NAMED",
    "SHAPE_PLANTS_MK_FN",
    "SHAPE_PLANTS_NAMED",
    "SHAPE_PLANTS_P_FN",
    "catalog_document",
    "extract_mill_catalog",
    "is_slice_mill",
    "mill_summary",
    "sha256_bytes",
)


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
    used_from = constants.get("USED_FROM")
    if isinstance(used_from, int):
        record["used_from"] = used_from
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
    plants, plant_ctor, wrappers, expand_plants = plants_context(tree)
    named_pairs = named_or_fn_pairs(tree, plants, wrappers, expand_plants)
    if named_pairs is not None:
        shape = pairs_shape(plants, plant_ctor, named_pairs)
        return rows_record(shape, named_pairs, n_plants=plant_count(plants, expand_plants))
    leftover = fn_pair_appends(tree)
    if leftover is not None:
        return rows_record(SHAPE_PAIRS_FN_PAIR, leftover, n_plants=len(leftover) * 2)
    raise ValueError(f"{path} has no extractable LHC catalog assignment")


_COUNT_FIELDS = (
    "catalog_first",
    "first_slug",
    "last_slug",
    "n_plants",
    "n_rows",
    "shape",
)


def mill_summary(record: Mapping[str, Any], *, include_pairs: bool) -> dict[str, Any]:
    """Count row plus optional w4x pair identities. Pins live in ``sources``."""

    summary = {"mill_id": record["mill_id"]}
    summary.update({field: record[field] for field in _COUNT_FIELDS})
    if include_pairs:
        summary["pairs"] = list(record.get("pairs") or ())
    return summary


def catalog_document(mills: list[dict[str, Any]]) -> dict[str, Any]:
    pair_rows = sum(mill["n_rows"] for mill in mills)
    plant_rows = sum(mill["n_plants"] for mill in mills)
    table = {}
    for mill in mills:
        table[mill["mill_id"]] = {
            key: value for key, value in mill.items() if key != "mill_id"
        }
    return {
        "schema": CATALOG_SCHEMA_ID,
        "source_ref": LEGACY_REF,
        "preserve_commit": PRESERVE_COMMIT,
        "factory": FACTORY,
        "generator": GENERATOR,
        "slice": SLICE_ID,
        "n_mills": len(mills),
        "n_pair_rows": pair_rows,
        "n_plant_rows": plant_rows,
        "mills": table,
    }


def is_slice_mill(mill_id: str) -> bool:
    return mill_id == SLICE_MILL_ID
