#!/usr/bin/env python3
"""AST-extract sbox catalog rows. Never exec mill publishers.

``plants_from_source`` walks leftover mill text for:

* ``PLANTS = [{...}, ...]`` runtime-dump dicts (r359 / r375 / r391)
* ``_ROWS = [dict(...), ...]`` leftover-dict rows
* ``_ROWS = [_row(...), ...]`` leftover-row constructors

``ast.parse`` is the only interpreter step. ``exec`` / ``eval`` /
``compile`` / ``SourceFileLoader`` are not used.
"""

from __future__ import annotations

import ast
from collections.abc import Mapping
from typing import Any

from ._contract import (
    FINDING_AST_NOT_A_PLANT,
    FINDING_FIELD_INVALID,
    FINDING_FIELD_MISSING,
    FINDING_SOURCE_NOT_PARSEABLE,
    bind_import_twin,
    refuse,
    refuse_when,
    shown,
)

SHAPE_RUNTIME = "runtime-dump"
SHAPE_LEFTOVER_DICT = "leftover-dict"
SHAPE_LEFTOVER_ROW = "leftover-row"

RUNTIME_FIELDS = ("family", "ok", "over", "miss", "trigger", "vector")
LEFTOVER_FIELDS = ("family", "over_slug", "miss_slug", "inc", "proc")
ROW_PARAM_CORE = (
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

__all__ = [
    "LEFTOVER_FIELDS",
    "ROW_PARAM_CORE",
    "RUNTIME_FIELDS",
    "SHAPE_LEFTOVER_DICT",
    "SHAPE_LEFTOVER_ROW",
    "SHAPE_RUNTIME",
    "plants_from_source",
]


def _const_eval(node: ast.AST) -> Any:
    """Literal values, containers, and keyword-only ``dict(...)``. Never exec."""

    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        return -_const_eval(node.operand)
    if isinstance(node, ast.List):
        return [_const_eval(item) for item in node.elts]
    if isinstance(node, ast.Tuple):
        return tuple(_const_eval(item) for item in node.elts)
    if isinstance(node, ast.Dict):
        refuse_when(
            any(key is None for key in node.keys),
            FINDING_AST_NOT_A_PLANT,
            "plant source uses dict unpacking",
        )
        return {
            _const_eval(key): _const_eval(value)
            for key, value in zip(node.keys, node.values, strict=True)
        }
    if isinstance(node, ast.JoinedStr):
        return _joined_string(node)
    if isinstance(node, ast.Call):
        func = node.func
        if (
            isinstance(func, ast.Name)
            and func.id == "dict"
            and not node.args
            and all(keyword.arg is not None for keyword in node.keywords)
        ):
            return {keyword.arg: _const_eval(keyword.value) for keyword in node.keywords}
        refuse(
            FINDING_AST_NOT_A_PLANT,
            f"plant source uses a non-literal call ({type(node).__name__})",
        )
    refuse(
        FINDING_AST_NOT_A_PLANT,
        f"plant source is not a constant ({type(node).__name__})",
    )


def _joined_string(node: ast.JoinedStr) -> str:
    parts: list[str] = []
    for value in node.values:
        if isinstance(value, ast.Constant) and isinstance(value.value, str):
            parts.append(value.value)
            continue
        refuse(FINDING_AST_NOT_A_PLANT, "f-string plant field is not a constant")
    return "".join(parts)


def _assigned_name(node: ast.AST) -> tuple[str, ast.AST] | None:
    if isinstance(node, ast.Assign) and len(node.targets) == 1:
        target = node.targets[0]
        if isinstance(target, ast.Name):
            return target.id, node.value
    if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
        if node.value is not None:
            return node.target.id, node.value
    return None


def _row_params(tree: ast.Module) -> tuple[str, ...] | None:
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == "_row":
            return tuple(arg.arg for arg in node.args.args)
    return None


def _require_str(values: Mapping[str, Any], field: str, where: str) -> str:
    value = values.get(field)
    refuse_when(
        field not in values,
        FINDING_FIELD_MISSING,
        f"{where} missing {field}",
    )
    refuse_when(
        not isinstance(value, str) or not value,
        FINDING_FIELD_INVALID,
        f"{where}.{field} must be a non-empty string, got {shown(value)}",
    )
    return value


def _require_int(values: Mapping[str, Any], field: str, where: str) -> int:
    value = values.get(field)
    refuse_when(
        field not in values,
        FINDING_FIELD_MISSING,
        f"{where} missing {field}",
    )
    refuse_when(
        type(value) is not int,
        FINDING_FIELD_INVALID,
        f"{where}.{field} must be an int, got {shown(value)}",
    )
    return value


def _runtime_identity(values: Mapping[str, Any], where: str) -> dict[str, Any]:
    return {
        "shape": SHAPE_RUNTIME,
        **{field: _require_str(values, field, where) for field in RUNTIME_FIELDS},
    }


def _leftover_identity(values: Mapping[str, Any], shape: str, where: str) -> dict[str, Any]:
    return {
        "shape": shape,
        "family": _require_str(values, "family", where),
        "over_slug": _require_str(values, "over_slug", where),
        "miss_slug": _require_str(values, "miss_slug", where),
        "inc": _require_int(values, "inc", where),
        "proc": _require_str(values, "proc", where),
    }


def _identity_mapping(node: ast.Dict, where: str) -> dict[str, Any]:
    values: dict[str, Any] = {}
    for key_node, value_node in zip(node.keys, node.values, strict=True):
        if key_node is None:
            continue
        key = _const_eval(key_node)
        if key not in LEFTOVER_FIELDS:
            continue
        values[key] = _const_eval(value_node)
    return _leftover_identity(values, SHAPE_LEFTOVER_DICT, where)


def _identity_keywords(node: ast.Call, where: str) -> dict[str, Any]:
    """Literal identity kwargs only; skip non-literal companion fields."""

    refuse_when(
        not isinstance(node.func, ast.Name) or node.func.id != "dict",
        FINDING_AST_NOT_A_PLANT,
        f"{where} is not a dict() row",
    )
    values: dict[str, Any] = {}
    for keyword in node.keywords:
        if keyword.arg not in LEFTOVER_FIELDS:
            continue
        values[keyword.arg] = _const_eval(keyword.value)
    return _leftover_identity(values, SHAPE_LEFTOVER_DICT, where)


def _call_row(node: ast.Call, params: tuple[str, ...], where: str) -> dict[str, Any]:
    refuse_when(
        any(isinstance(arg, ast.Starred) for arg in node.args),
        FINDING_AST_NOT_A_PLANT,
        f"{where} uses starred arguments",
    )
    refuse_when(
        len(node.args) < len(ROW_PARAM_CORE),
        FINDING_AST_NOT_A_PLANT,
        f"{where} has {len(node.args)} args; need {len(ROW_PARAM_CORE)}",
    )
    values = {
        name: _const_eval(arg)
        for name, arg in zip(params[: len(node.args)], node.args, strict=False)
    }
    return _leftover_identity(values, SHAPE_LEFTOVER_ROW, where)


def _list_elts(node: ast.AST) -> list[ast.AST] | None:
    return node.elts if isinstance(node, ast.List) else None


def plants_from_source(text: str) -> tuple[dict[str, Any], ...]:
    """AST-extract catalog identity rows from mill source text. Never exec."""

    try:
        tree = ast.parse(text)
    except SyntaxError as exc:
        refuse(FINDING_SOURCE_NOT_PARSEABLE, f"mill source is not parseable: {exc}")
    if not isinstance(tree, ast.Module):
        refuse(FINDING_SOURCE_NOT_PARSEABLE, "mill source is not a module")

    params = _row_params(tree)
    assigned: dict[str, ast.AST] = {}
    for node in tree.body:
        bound = _assigned_name(node)
        if bound is not None:
            assigned[bound[0]] = bound[1]

    plants_node = assigned.get("PLANTS")
    elts = _list_elts(plants_node) if plants_node is not None else None
    if elts and isinstance(elts[0], ast.Dict):
        return tuple(
            _runtime_identity(_const_eval(elt), f"PLANTS[{index}]")
            for index, elt in enumerate(elts)
        )

    rows_node = assigned.get("_ROWS")
    row_elts = _list_elts(rows_node) if rows_node is not None else None
    if row_elts:
        first = row_elts[0]
        if isinstance(first, ast.Call) and isinstance(first.func, ast.Name):
            if first.func.id == "dict":
                return tuple(
                    _identity_keywords(elt, f"_ROWS[{index}]")
                    for index, elt in enumerate(row_elts)
                    if isinstance(elt, ast.Call)
                )
            if first.func.id == "_row":
                refuse_when(
                    params is None,
                    FINDING_AST_NOT_A_PLANT,
                    "_ROWS uses _row() but no def _row is in the module",
                )
                return tuple(
                    _call_row(elt, params, f"_ROWS[{index}]")
                    for index, elt in enumerate(row_elts)
                    if isinstance(elt, ast.Call)
                )
        if isinstance(first, ast.Dict):
            return tuple(
                _identity_mapping(elt, f"_ROWS[{index}]")
                for index, elt in enumerate(row_elts)
                if isinstance(elt, ast.Dict)
            )
    refuse(FINDING_AST_NOT_A_PLANT, "source has no PLANTS dict list or _ROWS catalog")


bind_import_twin(__name__)
