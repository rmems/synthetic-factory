#!/usr/bin/env python3
"""``fn_pair`` / ``PAIRS.append`` identity for the LHC AST extract."""

from __future__ import annotations

import ast
from dataclasses import dataclass, field
from typing import Any

from .catalog_ast import (
    UNSET,
    assignment_of,
    call_name,
    call_positional_literals,
    literal_value,
    name_id,
    tuple_target_names,
)


def _is_empty_pairs_assign(node: ast.AST) -> bool:
    name, value = assignment_of(node)
    return name == "PAIRS" and isinstance(value, ast.List) and not value.elts


def _is_fa_fb_assign(node: ast.AST) -> bool:
    return tuple_target_names(node) == ("fa", "fb") and isinstance(node, ast.Assign)


def _fn_pair_args(node: ast.Assign) -> list[Any] | None:
    if call_name(node.value) != "fn_pair":
        return UNSET
    args = call_positional_literals(node.value)
    if args is None or len(args) < 4:
        return UNSET
    if not all(isinstance(item, str) for item in args[:4]):
        return UNSET
    return args


def _fn_pair_bind(node: ast.AST) -> list[Any] | None:
    """``fa, fb = fn_pair(...)`` literals, or ``UNSET`` when the bind is malformed."""

    if not _is_fa_fb_assign(node) or not isinstance(node, ast.Assign):
        return None
    return _fn_pair_args(node)


def _pairs_append_call(node: ast.AST) -> ast.Call | None:
    if not isinstance(node, ast.Expr) or not isinstance(node.value, ast.Call):
        return None
    call = node.value
    if not isinstance(call.func, ast.Attribute) or call.func.attr != "append":
        return None
    if name_id(call.func.value) != "PAIRS":
        return None
    return call


def _fn_pair_title(call: ast.Call) -> Any:
    if len(call.args) != 1 or not isinstance(call.args[0], ast.Tuple):
        return UNSET
    if not call.args[0].elts:
        return UNSET
    return literal_value(call.args[0].elts[0])


def _pairs_append_row(node: ast.AST, pending: list[Any] | None) -> dict[str, Any] | None:
    """``PAIRS.append((title, fa, fb, ...))`` identity, or ``UNSET`` if malformed."""

    call = _pairs_append_call(node)
    if call is None:
        return None
    title = _fn_pair_title(call)
    if pending is None or not isinstance(title, str):
        return UNSET
    return {
        "title": title,
        "success_key": pending[2],
        "fail_key": pending[3],
        "success_slug": pending[0],
        "fail_slug": pending[1],
        "success_plant": pending[2],
        "fail_plant": pending[3],
        "_left_kind": "fn_pair",
    }


@dataclass
class _FnPairState:
    pending: list[Any] | None = None
    rows: list[dict[str, Any]] = field(default_factory=list)
    saw_empty: bool = False
    rejected: bool = False


def _new_fn_pair_state() -> _FnPairState:
    return _FnPairState()


def _fn_pair_complete(state: _FnPairState) -> bool:
    return state.saw_empty and bool(state.rows)


def _mark_empty(state: _FnPairState) -> None:
    state.saw_empty = True


def _mark_rejected(state: _FnPairState) -> None:
    state.rejected = True


def _apply_fn_pair_node(state: _FnPairState, node: ast.AST) -> None:
    if _is_empty_pairs_assign(node):
        _mark_empty(state)
        return
    bind = _fn_pair_bind(node)
    if bind is UNSET:
        _mark_rejected(state)
        return
    if bind is not None:
        state.pending = bind
        return
    row = _pairs_append_row(node, state.pending)
    if row is UNSET:
        _mark_rejected(state)
        return
    if row is None:
        return
    state.rows.append(row)
    state.pending = None


def fn_pair_appends(tree: ast.AST) -> list[dict[str, Any]] | None:
    """``fa, fb = fn_pair(...)`` followed by ``PAIRS.append((title, fa, fb, ...))``."""

    state = _new_fn_pair_state()
    for node in getattr(tree, "body", ()):
        _apply_fn_pair_node(state, node)
        if state.rejected:
            return None
    if not _fn_pair_complete(state):
        return None
    return state.rows
