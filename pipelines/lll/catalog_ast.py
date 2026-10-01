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


def _call_name(node: ast.AST) -> str | None:
    if not isinstance(node, ast.Call):
        return None
    func = node.func
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return func.attr
    return None


def _literal(node: ast.AST) -> Any:
    try:
        return ast.literal_eval(node)
    except (ValueError, TypeError, SyntaxError):
        return None


def _tuple_names(node: ast.AST) -> tuple[str, ...] | None:
    if not isinstance(node, ast.Assign) or len(node.targets) != 1:
        return None
    target = node.targets[0]
    if not isinstance(target, ast.Tuple):
        return None
    names: list[str] = []
    for elt in target.elts:
        if not isinstance(elt, ast.Name):
            return None
        names.append(elt.id)
    return tuple(names)


def _fn_pair_args(node: ast.Assign) -> list[str] | None:
    if _call_name(node.value) != "fn_pair":
        return None
    args = [_literal(item) for item in node.value.args]
    if len(args) < 4:
        return None
    head = args[:4]
    if not all(isinstance(item, str) and item for item in head):
        return None
    return cast(list[str], head)


def _is_pairs_append(call: ast.Call) -> bool:
    func = call.func
    if not isinstance(func, ast.Attribute) or func.attr != "append":
        return False
    return isinstance(func.value, ast.Name) and func.value.id == "PAIRS"


def _append_title(node: ast.AST) -> str | None:
    if not isinstance(node, ast.Expr) or not isinstance(node.value, ast.Call):
        return None
    call = node.value
    if not _is_pairs_append(call):
        return None
    if len(call.args) != 1 or not isinstance(call.args[0], ast.Tuple):
        return None
    if not call.args[0].elts:
        return None
    title = _literal(call.args[0].elts[0])
    return title if isinstance(title, str) and title else None


def extract_pairs(source: str, *, path: str) -> tuple[tuple[str, list[str]], ...]:
    """Yield ``(title, fn_pair_args)`` rows from a mill script. Never exec."""

    try:
        tree = ast.parse(source, filename=path)
    except SyntaxError as exc:
        raise LllRefusal(FINDING_SOURCE_NOT_PARSEABLE, f"{path} does not parse: {exc}") from exc
    pending: list[str] | None = None
    rows: list[tuple[str, list[str]]] = []
    for node in tree.body:
        names = _tuple_names(node)
        if names == ("fa", "fb") and isinstance(node, ast.Assign):
            pending = _fn_pair_args(node)
            refuse_when(
                pending is None,
                FINDING_SOURCE_NOT_PARSEABLE,
                f"{path} has a malformed fn_pair bind",
            )
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
