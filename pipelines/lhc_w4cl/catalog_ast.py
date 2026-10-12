#!/usr/bin/env python3
"""AST literal helpers for the LHC w4cl catalog extract.

Nothing here executes source. ``ast.parse`` is the only interpreter step.
"""

from __future__ import annotations

import ast
from collections.abc import Mapping, Sequence
from typing import Any

UNSET = object()


def assignment_of(node: ast.stmt) -> tuple[str | None, ast.AST | None]:
    """Return ``(name, value)`` for a simple ``NAME = value`` statement."""

    if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
        return node.target.id, node.value
    if isinstance(node, ast.Assign) and len(node.targets) == 1:
        target = node.targets[0]
        if isinstance(target, ast.Name):
            return target.id, node.value
    return None, None


def _bound_name(node: ast.Name, env: Mapping[str, Any]) -> Any:
    return env.get(node.id, UNSET)


def _negated(inner: Any) -> Any:
    return -inner if isinstance(inner, (int, float)) else UNSET


def _sequence_parts(node: ast.AST) -> tuple[list[ast.expr], type] | None:
    """A tuple or list literal's elements and its container type, else None."""

    if isinstance(node, ast.Tuple):
        return node.elts, tuple
    return (node.elts, list) if isinstance(node, ast.List) else None


def literal_value(node: ast.AST, env: Mapping[str, Any] | None = None) -> Any:
    """Resolve constants, names, and literal containers; else ``UNSET``."""

    bound = env or {}
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Name):
        return _bound_name(node, bound)
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        return _negated(literal_value(node.operand, bound))
    parts = _sequence_parts(node)
    if parts is not None:
        return _sequence(parts[0], bound, parts[1])
    return _mapping(node, bound) if isinstance(node, ast.Dict) else UNSET


def _sequence(elts: Sequence[ast.AST], env: Mapping[str, Any], ctor):
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


def named_call(node: ast.AST) -> ast.Call | None:
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
        return node
    return None


def call_name(node: ast.AST) -> str | None:
    call = named_call(node)
    if call is None or not isinstance(call.func, ast.Name):
        return None
    return call.func.id


def call_positional_literals(
    node: ast.AST, env: Mapping[str, Any] | None = None
) -> list[Any] | None:
    """Positional arguments of a ``Name(...)`` call when every value is a literal."""

    call = named_call(node)
    if call is None:
        return None
    values: list[Any] = []
    for arg in call.args:
        value = literal_value(arg, env)
        if value is UNSET:
            return None
        values.append(value)
    return values


def module_docstring(tree: ast.AST) -> str:
    if not isinstance(tree, ast.Module) or not tree.body:
        return ""
    first = tree.body[0]
    if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant):
        value = first.value.value
        return value if isinstance(value, str) else ""
    return ""
