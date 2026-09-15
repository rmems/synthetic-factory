#!/usr/bin/env python3
"""Resolve AST literals for the LHC catalog extract.

``literal_value`` is a single match walker. It never executes source.
"""

from __future__ import annotations

import ast
from collections.abc import Mapping
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


def literal_value(node: ast.AST, env: Mapping[str, Any] | None = None) -> Any:
    """Resolve constants, names, containers, and constant f-strings; else ``UNSET``."""

    bindings = env or {}
    match node:
        case ast.Constant(value=value):
            return value
        case ast.Name(id=name) if name in bindings:
            return bindings[name]
        case ast.Tuple(elts=elts):
            items = _items(elts, bindings)
            return UNSET if items is UNSET else tuple(items)
        case ast.List(elts=elts):
            items = _items(elts, bindings)
            return UNSET if items is UNSET else list(items)
        case ast.Set(elts=elts):
            items = _items(elts, bindings)
            return UNSET if items is UNSET else set(items)
        case ast.Dict():
            return _dict(node, bindings)
        case ast.JoinedStr():
            return _joined(node, bindings)
        case ast.UnaryOp(op=ast.USub(), operand=inner):
            number = literal_value(inner, bindings)
            return -number if isinstance(number, (int, float)) else UNSET
        case ast.BinOp(op=ast.Add(), left=left, right=right):
            first = literal_value(left, bindings)
            second = literal_value(right, bindings)
            if isinstance(first, str) and isinstance(second, str):
                return first + second
            return UNSET
        case _:
            return UNSET
