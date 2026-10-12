#!/usr/bin/env python3
"""AST literal helpers for the IAC catalog extract.

Nothing here executes source. ``ast.parse`` is the only interpreter step.
"""

from __future__ import annotations

import ast
from collections.abc import Mapping
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


def assignment_names(node: ast.stmt) -> tuple[str, ...]:
    if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
        return (node.target.id,)
    if isinstance(node, ast.Assign):
        return tuple(target.id for target in node.targets if isinstance(target, ast.Name))
    return ()


def literal_value(node: ast.AST, env: Mapping[str, Any] | None = None) -> Any:
    """Resolve constants, names, containers, and constant f-strings; else ``UNSET``."""

    bound = env or {}
    for node_type, resolve in _LITERAL_RESOLVERS:
        if isinstance(node, node_type):
            return resolve(node, bound)
    return UNSET


def _constant(node: ast.Constant, env: Mapping[str, Any]) -> Any:
    return node.value


def _bound_name(node: ast.Name, env: Mapping[str, Any]) -> Any:
    return env.get(node.id, UNSET)


def _negated_number(node: ast.UnaryOp, env: Mapping[str, Any]) -> Any:
    if not isinstance(node.op, ast.USub):
        return UNSET
    inner = literal_value(node.operand, env)
    return -inner if isinstance(inner, (int, float)) else UNSET


def _tuple(node: ast.Tuple, env: Mapping[str, Any]) -> Any:
    return _sequence(node.elts, env, tuple)


def _list(node: ast.List, env: Mapping[str, Any]) -> Any:
    return _sequence(node.elts, env, list)


def _set(node: ast.Set, env: Mapping[str, Any]) -> Any:
    values = _sequence(node.elts, env, list)
    return set(values) if values is not UNSET else UNSET


def _concatenated_strings(node: ast.BinOp, env: Mapping[str, Any]) -> Any:
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


# Checked in this order; the first matching node type decides the value.
_LITERAL_RESOLVERS = (
    (ast.Constant, _constant),
    (ast.Name, _bound_name),
    (ast.UnaryOp, _negated_number),
    (ast.Tuple, _tuple),
    (ast.List, _list),
    (ast.Set, _set),
    (ast.Dict, _mapping),
    (ast.JoinedStr, _joined_string),
    (ast.BinOp, _concatenated_strings),
)


def call_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
        return node.func.id
    return None


def call_kwargs(node: ast.AST, env: Mapping[str, Any] | None = None) -> dict[str, Any] | None:
    """Keyword arguments of a ``Name(...)`` call when every value is a literal."""

    if call_name(node) is None:
        return None
    if node.args or any(keyword.arg is None for keyword in node.keywords):
        return None
    out: dict[str, Any] = {}
    for keyword in node.keywords:
        value = literal_value(keyword.value, env)
        if keyword.arg is None or value is UNSET:
            return None
        out[keyword.arg] = value
    return out


def joined_path_constant(node: ast.AST) -> str | None:
    """``ROOT / "experiments" / "iac-mill-r609.py"`` → ``experiments/iac-mill-r609.py``."""

    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.Name):
        return None
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
        left = joined_path_constant(node.left)
        right = joined_path_constant(node.right)
        if right is None:
            return None
        if left is None:
            return right
        return f"{left}/{right}"
    return None


def extract_joined_path_assignment(source: str, name: str) -> str | None:
    tree = ast.parse(source)
    for node in tree.body:
        assigned, value = assignment_of(node)
        if assigned == name and value is not None:
            return joined_path_constant(value)
    return None
