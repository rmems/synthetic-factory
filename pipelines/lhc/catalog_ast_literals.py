#!/usr/bin/env python3
"""Resolve AST literals for the LHC catalog extract.

Nothing here executes source. ``literal_value`` walks constants, names,
containers, and constant f-strings only.
"""

from __future__ import annotations

import ast
from collections.abc import Mapping
from typing import Any

UNSET = object()


def _literal_constant(node: ast.Constant, _env: Mapping[str, Any]) -> Any:
    return node.value


def _literal_name(node: ast.Name, env: Mapping[str, Any]) -> Any:
    return env[node.id] if node.id in env else UNSET


def _literal_tuple(node: ast.Tuple, env: Mapping[str, Any]) -> Any:
    return _sequence(node.elts, env, tuple)


def _literal_list(node: ast.List, env: Mapping[str, Any]) -> Any:
    return _sequence(node.elts, env, list)


def _literal_set(node: ast.Set, env: Mapping[str, Any]) -> Any:
    values = _sequence(node.elts, env, list)
    return set(values) if values is not UNSET else UNSET


def _literal_unary(node: ast.UnaryOp, env: Mapping[str, Any]) -> Any:
    if not isinstance(node.op, ast.USub):
        return UNSET
    inner = literal_value(node.operand, env)
    return -inner if isinstance(inner, (int, float)) else UNSET


def _literal_add(node: ast.BinOp, env: Mapping[str, Any]) -> Any:
    if not isinstance(node.op, ast.Add):
        return UNSET
    left = literal_value(node.left, env)
    right = literal_value(node.right, env)
    if isinstance(left, str) and isinstance(right, str):
        return left + right
    return UNSET


def _sequence(elts: list[ast.AST], env: Mapping[str, Any], ctor):
    values: list[Any] = []
    for elt in elts:
        item = literal_value(elt, env)
        if item is UNSET:
            return UNSET
        values.append(item)
    return ctor(values)


def _mapping(node: ast.Dict, env: Mapping[str, Any]) -> Any:
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


def _joined_string(node: ast.JoinedStr, env: Mapping[str, Any]) -> Any:
    parts: list[str] = []
    for value in node.values:
        if isinstance(value, ast.Constant) and isinstance(value.value, str):
            parts.append(value.value)
            continue
        if not isinstance(value, ast.FormattedValue):
            return UNSET
        inner = literal_value(value.value, env)
        if inner is UNSET or not isinstance(inner, (str, int)):
            return UNSET
        parts.append(str(inner))
    return "".join(parts)


_LITERAL_HANDLERS: dict[type[ast.AST], Any] = {
    ast.Constant: _literal_constant,
    ast.Name: _literal_name,
    ast.Tuple: _literal_tuple,
    ast.List: _literal_list,
    ast.Set: _literal_set,
    ast.Dict: _mapping,
    ast.JoinedStr: _joined_string,
    ast.UnaryOp: _literal_unary,
    ast.BinOp: _literal_add,
}


def literal_value(node: ast.AST, env: Mapping[str, Any] | None = None) -> Any:
    """Resolve constants, names, containers, and constant f-strings; else ``UNSET``."""

    handler = _LITERAL_HANDLERS.get(type(node))
    if handler is None:
        return UNSET
    return handler(node, env or {})
