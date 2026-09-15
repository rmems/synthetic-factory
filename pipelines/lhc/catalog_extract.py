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


def _round_suffix(path: str) -> int | None:
    _, sep, tail = Path(path).stem.rpartition("-r")
    if not sep or not tail.isdigit():
        return None
    return int(tail)


def _scan_module_literals(tree: ast.AST) -> dict[str, Any]:
    env: dict[str, Any] = {}
    for stmt in ast.iter_child_nodes(tree):
        name, value = assignment_of(stmt)
        if name is None or value is None:
            continue
        resolved = literal_value(value, env)
        if resolved is not UNSET:
            env[name] = resolved
    return env


def _stamp_source(
    record: dict[str, Any],
    *,
    path: str,
    blob_sha: str,
    digest: str,
    constants: Mapping[str, Any],
) -> dict[str, Any]:
    first = constants.get("CATALOG_FIRST")
    if not isinstance(first, int):
        first = _round_suffix(path)
    record["mill_id"] = Path(path).stem
    record["path"] = path
    record["blob_sha"] = blob_sha
    record["sha256"] = digest
    record["kind"] = KIND_PAIRS
    record["catalog_first"] = first
    record["generator"] = constants.get("GEN", GENERATOR)
    record["factory"] = constants.get("FACTORY", FACTORY)
    used_from = constants.get("USED_FROM")
    if isinstance(used_from, int):
        record["used_from"] = used_from
    return record


def extract_mill_catalog(
    source: str,
    *,
    path: str,
    blob_sha: str = "",
) -> dict[str, Any]:
    """Structured catalog extract for one mill source file."""

    tree = ast.parse(source, filename=path)
    constants = _scan_module_literals(tree)
    record = _extract_shape(tree, path=path)
    return _stamp_source(
        record,
        path=path,
        blob_sha=blob_sha,
        digest=sha256_bytes(source.encode()),
        constants=constants,
    )


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
