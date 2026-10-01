#!/usr/bin/env python3
"""AST-only leftover leftover leftover extract. Mill scripts are parsed, never executed."""

from __future__ import annotations

import ast
from typing import Any, cast

from ._contract import (
    FINDING_SOURCE_NOT_PARSEABLE,
    LllRefusal,
    bind_import_twin,
    refuse_when,
)

__all__ = ["extract_pairs"]


def _literal(node: ast.AST) -> Any:
    try:
        return ast.literal_eval(node)
    except (ValueError, TypeError, SyntaxError):
        return None


def _call_name(node: ast.AST) -> str | None:
    func = node.func if isinstance(node, ast.Call) else None
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return func.attr
    return None


def _assign_tuple(node: ast.AST) -> list[ast.expr] | None:
    if not isinstance(node, ast.Assign) or len(node.targets) != 1:
        return None
    target = node.targets[0]
    return target.elts if isinstance(target, ast.Tuple) else None


def _tuple_names(node: ast.AST) -> tuple[str, ...] | None:
    elts = _assign_tuple(node)
    if elts is None or not all(isinstance(elt, ast.Name) for elt in elts):
        return None
    return tuple(elt.id for elt in elts)


def _is_str_quad(items: list[Any]) -> bool:
    return len(items) == 4 and all(isinstance(item, str) and item for item in items)


def _fn_pair_args(node: ast.Assign) -> list[str] | None:
    if _call_name(node.value) != "fn_pair":
        return None
    head = [_literal(item) for item in node.value.args][:4]
    return cast(list[str], head) if _is_str_quad(head) else None


def _is_pairs_append(func: ast.expr) -> bool:
    return (
        isinstance(func, ast.Attribute)
        and func.attr == "append"
        and isinstance(func.value, ast.Name)
        and func.value.id == "PAIRS"
    )


def _pairs_tuple(call: ast.Call) -> list[ast.expr] | None:
    if not _is_pairs_append(call.func) or len(call.args) != 1:
        return None
    arg = call.args[0]
    return arg.elts if isinstance(arg, ast.Tuple) else None


def _append_title(node: ast.AST) -> str | None:
    call = node.value if isinstance(node, ast.Expr) else None
    elts = _pairs_tuple(call) if isinstance(call, ast.Call) else None
    title = _literal(elts[0]) if elts else None
    return title if isinstance(title, str) and title else None


def _parse(source: str, path: str) -> ast.Module:
    try:
        return ast.parse(source, filename=path)
    except SyntaxError as exc:
        raise LllRefusal(FINDING_SOURCE_NOT_PARSEABLE, f"{path} does not parse: {exc}") from exc


def _bind_args(node: ast.AST, path: str) -> list[str] | None:
    if _tuple_names(node) != ("fa", "fb") or not isinstance(node, ast.Assign):
        return None
    args = _fn_pair_args(node)
    refuse_when(
        args is None,
        FINDING_SOURCE_NOT_PARSEABLE,
        f"{path} has a malformed fn_pair bind",
    )
    return args


def extract_pairs(source: str, *, path: str) -> tuple[tuple[str, list[str]], ...]:
    """Yield ``(title, fn_pair_args)`` rows from a mill script. Never exec."""

    pending: list[str] | None = None
    rows: list[tuple[str, list[str]]] = []
    for node in _parse(source, path).body:
        bound = _bind_args(node, path)
        if bound is not None:
            pending = bound
            continue
        title = _append_title(node)
        if title is None:
            continue
        refuse_when(
            pending is None,
            FINDING_SOURCE_NOT_PARSEABLE,
            f"{path} appends a leftover leftover leftover pair without fn_pair",
        )
        rows.append((title, cast(list[str], pending)))
        pending = None
    refuse_when(
        pending is not None,
        FINDING_SOURCE_NOT_PARSEABLE,
        f"{path} has a leftover leftover leftover fn_pair without PAIRS.append",
    )
    refuse_when(
        not rows,
        FINDING_SOURCE_NOT_PARSEABLE,
        f"{path} has no leftover leftover leftover pairs",
    )
    return tuple(rows)


bind_import_twin(__name__)
