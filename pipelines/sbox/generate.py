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
from collections.abc import Callable, Mapping, Sequence
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


def _dict_items(node: ast.Dict) -> list[tuple[ast.expr, ast.expr]]:
    """The key and value nodes of a dict literal; ``**`` unpacking refuses before any is read."""

    items: list[tuple[ast.expr, ast.expr]] = []
    for key, value in zip(node.keys, node.values, strict=True):
        if key is None:
            refuse(FINDING_AST_NOT_A_PLANT, "plant source uses dict unpacking")
        items.append((key, value))
    return items


def _is_keyword_dict_call(node: ast.Call) -> bool:
    """``dict(key=value, ...)``: the name ``dict`` called with named keywords only."""

    if not isinstance(node.func, ast.Name) or node.func.id != "dict":
        return False
    return not node.args and all(keyword.arg is not None for keyword in node.keywords)


def _negated(values: list[Any]) -> Any:
    return -values[0]


def _const_parts(node: ast.AST) -> tuple[Sequence[ast.AST], Callable[[list[Any]], Any]]:
    """A negation, a list or a keyword ``dict(...)`` as (child nodes, rebuild); others refuse.

    ``_const_eval`` evaluates the children itself, so a nesting level costs one frame.
    """

    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        return (node.operand,), _negated
    if isinstance(node, ast.List):
        return node.elts, list
    if not isinstance(node, ast.Call):
        refuse(
            FINDING_AST_NOT_A_PLANT,
            f"plant source is not a constant ({type(node).__name__})",
        )
    refuse_when(
        not _is_keyword_dict_call(node),
        FINDING_AST_NOT_A_PLANT,
        f"plant source uses a non-literal call ({type(node).__name__})",
    )
    names = [keyword.arg for keyword in node.keywords]
    return [keyword.value for keyword in node.keywords], lambda values: dict(zip(names, values))


def _const_eval(node: ast.AST) -> Any:
    """Literal values, containers, and keyword-only ``dict(...)``. Never exec."""

    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Tuple):
        return tuple(_const_eval(item) for item in node.elts)
    if isinstance(node, ast.Dict):
        return {_const_eval(key): _const_eval(value) for key, value in _dict_items(node)}
    if isinstance(node, ast.JoinedStr):
        return _joined_string(node)
    children, rebuild = _const_parts(node)
    return rebuild([_const_eval(child) for child in children])


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
        return None if node.value is None else (node.target.id, node.value)
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


def _list_elts(node: ast.AST) -> Sequence[ast.AST] | None:
    return node.elts if isinstance(node, ast.List) else None


def _names(node: ast.AST, name: str) -> bool:
    return isinstance(node, ast.Name) and node.id == name


def _rows_generator(node: ast.ListComp) -> ast.comprehension | None:
    """The one ``for r in _ROWS`` clause, with one condition, of ``[r for r in _ROWS if ...]``."""

    if len(node.generators) != 1 or not _names(node.elt, "r"):
        return None
    generator = node.generators[0]
    if not _names(generator.target, "r") or not _names(generator.iter, "_ROWS"):
        return None
    return generator if len(generator.ifs) == 1 else None


def _is_family_lookup(node: ast.AST) -> bool:
    """``r["family"]``."""

    if not isinstance(node, ast.Subscript) or not _names(node.value, "r"):
        return False
    return isinstance(node.slice, ast.Constant) and node.slice.value == "family"


def _family_neq_literal(test: ast.AST) -> str | None:
    """The string ``"slug"`` of ``r["family"] != "slug"``, else None."""

    if not isinstance(test, ast.Compare) or len(test.ops) != 1:
        return None
    if not isinstance(test.ops[0], ast.NotEq) or not _is_family_lookup(test.left):
        return None
    right = test.comparators[0]
    if isinstance(right, ast.Constant) and isinstance(right.value, str):
        return right.value
    return None


def _family_neq_filter(node: ast.ListComp) -> str | None:
    """``[r for r in _ROWS if r["family"] != "slug"]`` when the test is literal."""

    generator = _rows_generator(node)
    return None if generator is None else _family_neq_literal(generator.ifs[0])


def _dict_call_rows(elts: Sequence[ast.AST]) -> list[dict[str, Any]]:
    return [
        _identity_keywords(elt, f"_ROWS[{index}]")
        for index, elt in enumerate(elts)
        if isinstance(elt, ast.Call)
    ]


def _row_call_rows(elts: Sequence[ast.AST], params: tuple[str, ...] | None) -> list[dict[str, Any]]:
    if params is None:
        refuse(FINDING_AST_NOT_A_PLANT, "_ROWS uses _row() but no def _row is in the module")
    return [
        _call_row(elt, params, f"_ROWS[{index}]")
        for index, elt in enumerate(elts)
        if isinstance(elt, ast.Call)
    ]


def _dict_literal_rows(elts: Sequence[ast.AST]) -> list[dict[str, Any]]:
    return [
        _identity_mapping(elt, f"_ROWS[{index}]")
        for index, elt in enumerate(elts)
        if isinstance(elt, ast.Dict)
    ]


def _called_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
        return node.func.id
    return None


def _identities_from_row_elts(
    elts: Sequence[ast.AST],
    params: tuple[str, ...] | None,
) -> list[dict[str, Any]]:
    if not elts:
        return []
    first = elts[0]
    called = _called_name(first)
    if called == "dict":
        return _dict_call_rows(elts)
    if called == "_row":
        return _row_call_rows(elts, params)
    if isinstance(first, ast.Dict):
        return _dict_literal_rows(elts)
    refuse(FINDING_AST_NOT_A_PLANT, "_ROWS list shape is not dict(), _row(), or dict literals")


def _filtered_rows(value: ast.ListComp, rows: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
    excluded = _family_neq_filter(value)
    if excluded is None or rows is None:
        refuse(FINDING_AST_NOT_A_PLANT, "_ROWS filter is not a supported family exclusion")
    return [row for row in rows if row["family"] != excluded]


def _rows_from_module(tree: ast.Module, params: tuple[str, ...] | None) -> list[dict[str, Any]] | None:
    rows: list[dict[str, Any]] | None = None
    for node in tree.body:
        bound = _assigned_name(node)
        if bound is None or bound[0] != "_ROWS":
            continue
        value = bound[1]
        elts = _list_elts(value)
        if elts is not None:
            rows = _identities_from_row_elts(elts, params)
        elif isinstance(value, ast.ListComp):
            rows = _filtered_rows(value, rows)
    return rows


def _module_assignments(tree: ast.Module) -> dict[str, ast.AST]:
    assigned: dict[str, ast.AST] = {}
    for node in tree.body:
        bound = _assigned_name(node)
        if bound is not None:
            assigned[bound[0]] = bound[1]
    return assigned


def _runtime_plants(assigned: Mapping[str, ast.AST]) -> tuple[dict[str, Any], ...] | None:
    """Identity rows of a ``PLANTS = [{...}, ...]`` runtime dump, else None."""

    plants_node = assigned.get("PLANTS")
    elts = _list_elts(plants_node) if plants_node is not None else None
    if not elts or not isinstance(elts[0], ast.Dict):
        return None
    return tuple(
        _runtime_identity(_const_eval(elt), f"PLANTS[{index}]")
        for index, elt in enumerate(elts)
    )


def plants_from_source(text: str) -> tuple[dict[str, Any], ...]:
    """AST-extract catalog identity rows from mill source text. Never exec."""

    try:
        tree = ast.parse(text)
    except SyntaxError as exc:
        refuse(FINDING_SOURCE_NOT_PARSEABLE, f"mill source is not parseable: {exc}")
    if not isinstance(tree, ast.Module):
        refuse(FINDING_SOURCE_NOT_PARSEABLE, "mill source is not a module")

    params = _row_params(tree)
    runtime = _runtime_plants(_module_assignments(tree))
    if runtime is not None:
        return runtime

    rows = _rows_from_module(tree, params)
    if rows is not None:
        return tuple(rows)
    refuse(FINDING_AST_NOT_A_PLANT, "source has no PLANTS dict list or _ROWS catalog")


bind_import_twin(__name__)
