#!/usr/bin/env python3
"""``LHC_PAIRS`` named/fn catalog rows for the LHC AST extract."""

from __future__ import annotations

import ast
from collections.abc import Mapping
from typing import Any

from .catalog_ast import (
    assignment_of,
    call_name,
    call_positional_literals,
    literal_value,
    name_id,
)

SHAPE_PAIRS_NAMED = "pairs-named"
SHAPE_PLANTS_NAMED = "plants-named"
SHAPE_PLANTS_P_FN = "plants-p-fn"
SHAPE_PLANTS_MK_FN = "plants-mk-fn"
SHAPE_PAIRS_FN_PAIR = "pairs-fn-pair"

_PAIR_FIELDS = (
    "title",
    "success_key",
    "fail_key",
    "success_slug",
    "fail_slug",
    "success_plant",
    "fail_plant",
)


def pairs_shape(
    plants: Mapping[str, Any],
    plant_ctor: str | None,
    rows: list[dict[str, Any]],
) -> str:
    uses_fn = any(row.get("_left_kind") == "fn" for row in rows)
    if uses_fn and plant_ctor == "mk":
        return SHAPE_PLANTS_MK_FN
    if uses_fn and plant_ctor == "P":
        return SHAPE_PLANTS_P_FN
    if plants:
        return SHAPE_PLANTS_NAMED
    return SHAPE_PAIRS_NAMED


def _clean_pair(row: Mapping[str, Any]) -> dict[str, Any]:
    return {field: row[field] for field in _PAIR_FIELDS}


def _first_success_slug(cleaned: list[Mapping[str, Any]]) -> str:
    return str(cleaned[0]["success_slug"])


def _last_success_slug(cleaned: list[Mapping[str, Any]]) -> str:
    return str(cleaned[-1]["success_slug"])


def rows_record(shape: str, rows: list[dict[str, Any]], *, n_plants: int) -> dict[str, Any]:
    cleaned = [_clean_pair(row) for row in rows]
    return {
        "shape": shape,
        "n_rows": len(cleaned),
        "n_plants": n_plants,
        "first_slug": _first_success_slug(cleaned),
        "last_slug": _last_success_slug(cleaned),
        "pairs": cleaned,
    }


def _lhc_pairs_elts(node: ast.AST) -> list[ast.AST] | None:
    name, value = assignment_of(node)
    if name != "LHC_PAIRS":
        return None
    if not isinstance(value, ast.List):
        return None
    if not value.elts:
        return None
    return value.elts


def _rows_from_elts(
    elts: list[ast.AST],
    plants: Mapping[str, Mapping[str, Any]],
    wrappers: Mapping[str, str],
    expand_plants: Mapping[str, Mapping[str, Any]],
) -> list[dict[str, Any]] | None:
    rows: list[dict[str, Any]] = []
    for elt in elts:
        row = _lhc_pair_identity(elt, plants, wrappers, expand_plants)
        if row is None:
            return None
        rows.append(row)
    return rows


def named_or_fn_pairs(
    tree: ast.AST,
    plants: Mapping[str, Mapping[str, Any]],
    wrappers: Mapping[str, str],
    expand_plants: Mapping[str, Mapping[str, Any]],
) -> list[dict[str, Any]] | None:
    for node in getattr(tree, "body", ()):
        elts = _lhc_pairs_elts(node)
        if elts is None:
            continue
        return _rows_from_elts(elts, plants, wrappers, expand_plants)
    return None


def _pair_title(node: ast.AST) -> str | None:
    if not isinstance(node, ast.Tuple) or len(node.elts) != 6:
        return None
    title = literal_value(node.elts[0])
    if isinstance(title, str):
        return title
    return None


def _side_identity(
    key: str,
    kind: str,
    wrappers: Mapping[str, str],
) -> str:
    if kind == "fn":
        return key
    return wrappers.get(key, key)


def _lhc_pair_identity(
    node: ast.AST,
    plants: Mapping[str, Mapping[str, Any]],
    wrappers: Mapping[str, str],
    expand_plants: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any] | None:
    title = _pair_title(node)
    if title is None or not isinstance(node, ast.Tuple):
        return None
    left_key, left_kind = _side_key(node.elts[1])
    right_key, right_kind = _side_key(node.elts[2])
    if left_key is None or right_key is None:
        return None
    success = _resolve_side(left_key, plants, wrappers, expand_plants)
    fail = _resolve_side(right_key, plants, wrappers, expand_plants)
    if success is None or fail is None:
        return None
    return {
        "title": title,
        "success_key": _side_identity(left_key, left_kind, wrappers),
        "fail_key": _side_identity(right_key, right_kind, wrappers),
        "success_slug": success["slug"],
        "fail_slug": fail["slug"],
        "success_plant": success["plant"],
        "fail_plant": fail["plant"],
        "_left_kind": left_kind,
    }


def _side_key(node: ast.AST) -> tuple[str | None, str]:
    if call_name(node) == "fn":
        args = call_positional_literals(node)
        if args and isinstance(args[0], str):
            return args[0], "fn"
        return None, "fn"
    named = name_id(node)
    if named is not None:
        return named, "name"
    return None, "unknown"


def _resolve_side(
    key: str,
    plants: Mapping[str, Mapping[str, Any]],
    wrappers: Mapping[str, str],
    expand_plants: Mapping[str, Mapping[str, Any]],
) -> Mapping[str, Any] | None:
    if key in plants:
        return plants[key]
    wrapped = wrappers.get(key)
    if wrapped is not None and wrapped in plants:
        return plants[wrapped]
    if key in expand_plants:
        return expand_plants[key]
    return None
