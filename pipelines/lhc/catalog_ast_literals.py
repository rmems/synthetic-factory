#!/usr/bin/env python3
"""Resolve AST literals for the LHC catalog extract.

``literal_value`` dispatches by node type. It never executes source.
"""

from __future__ import annotations

import ast
from collections.abc import Callable, Mapping
from typing import Any

UNSET = object()


def _items(nodes: list[ast.AST], env: Mapping[str, Any]) -> list[Any] | object:
    resolved: list[Any] = []
    for node in nodes:
        item = literal_value(node, env)
        if item is UNSET:
            return UNSET
        resolved.append(item)
    return resolved


def _joined(node: ast.JoinedStr, env: Mapping[str, Any]) -> Any:
    chunks: list[str] = []
    for part in node.values:
        match part:
            case ast.Constant(value=text) if isinstance(text, str):
                chunks.append(text)
            case ast.FormattedValue(value=inner):
                piece = literal_value(inner, env)
                if piece is UNSET or not isinstance(piece, (str, int)):
                    return UNSET
                chunks.append(str(piece))
            case _:
                return UNSET
    return "".join(chunks)


def _dict(node: ast.Dict, env: Mapping[str, Any]) -> Any:
    out: dict[Any, Any] = {}
    for key_node, value_node in zip(node.keys, node.values, strict=True):
        if key_node is None:
            return UNSET
        key = literal_value(key_node, env)
        value = literal_value(value_node, env)
        if key is UNSET or value is UNSET:
            return UNSET
        out[key] = value
    return out


def _constant(node: ast.Constant, _env: Mapping[str, Any]) -> Any:
    return node.value


def _name(node: ast.Name, env: Mapping[str, Any]) -> Any:
    return env[node.id] if node.id in env else UNSET


def _tuple_literal(node: ast.Tuple, env: Mapping[str, Any]) -> Any:
    items = _items(node.elts, env)
    return UNSET if items is UNSET else tuple(items)


def _list_literal(node: ast.List, env: Mapping[str, Any]) -> Any:
    items = _items(node.elts, env)
    return UNSET if items is UNSET else list(items)


def _set_literal(node: ast.Set, env: Mapping[str, Any]) -> Any:
    items = _items(node.elts, env)
    return UNSET if items is UNSET else set(items)


def _unary(node: ast.UnaryOp, env: Mapping[str, Any]) -> Any:
    if not isinstance(node.op, ast.USub):
        return UNSET
    number = literal_value(node.operand, env)
    return -number if isinstance(number, (int, float)) else UNSET


def _add(node: ast.BinOp, env: Mapping[str, Any]) -> Any:
    if not isinstance(node.op, ast.Add):
        return UNSET
    first = literal_value(node.left, env)
    second = literal_value(node.right, env)
    concat = isinstance(first, str) and isinstance(second, str)
    return first + second if concat else UNSET


_HANDLERS: dict[type[ast.AST], Callable[[Any, Mapping[str, Any]], Any]] = {
    ast.Constant: _constant,
    ast.Name: _name,
    ast.Tuple: _tuple_literal,
    ast.List: _list_literal,
    ast.Set: _set_literal,
    ast.Dict: _dict,
    ast.JoinedStr: _joined,
    ast.UnaryOp: _unary,
    ast.BinOp: _add,
}


def literal_value(node: ast.AST, env: Mapping[str, Any] | None = None) -> Any:
    """Resolve constants, names, containers, and constant f-strings; else ``UNSET``."""

    handler = _HANDLERS.get(type(node))
    if handler is None:
        return UNSET
    return handler(node, env or {})
