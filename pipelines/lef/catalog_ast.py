#!/usr/bin/env python3
"""AST literal helpers for the leftover mill catalog extract.

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
        return tuple(
            target.id for target in node.targets if isinstance(target, ast.Name)
        )
    return ()


def tuple_assignment_names(node: ast.stmt) -> tuple[str, ...]:
    """Names in ``A, B, C = ...`` when every target is a plain name."""

    if not isinstance(node, ast.Assign) or len(node.targets) != 1:
        return ()
    target = node.targets[0]
    if not isinstance(target, ast.Tuple):
        return ()
    names: list[str] = []
    for elt in target.elts:
        if not isinstance(elt, ast.Name):
            return ()
        names.append(elt.id)
    return tuple(names)


def literal_value(node: ast.AST, env: Mapping[str, Any] | None = None) -> Any:
    """Resolve constants, names, containers, and frozenset calls; else ``UNSET``."""

    bound = env or {}
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Name):
        return bound[node.id] if node.id in bound else UNSET
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        inner = literal_value(node.operand, bound)
        return -inner if isinstance(inner, (int, float)) else UNSET
    if isinstance(node, ast.Tuple):
        return _sequence(node.elts, bound, tuple)
    if isinstance(node, ast.List):
        return _sequence(node.elts, bound, list)
    if isinstance(node, ast.Set):
        values = _sequence(node.elts, bound, list)
        return set(values) if values is not UNSET else UNSET
    if isinstance(node, ast.Dict):
        return _mapping(node, bound)
    if isinstance(node, ast.JoinedStr):
        return _joined_string(node, bound)
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        left = literal_value(node.left, bound)
        right = literal_value(node.right, bound)
        if isinstance(left, str) and isinstance(right, str):
            return left + right
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
        return _safe_call(node, bound)
    return UNSET


def _safe_call(node: ast.Call, env: Mapping[str, Any]) -> Any:
    if node.func.id != "frozenset" or len(node.args) != 1 or node.keywords:
        return UNSET
    inner = literal_value(node.args[0], env)
    if isinstance(inner, (set, list, tuple, frozenset)):
        return frozenset(inner)
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


def call_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
        return node.func.id
    return None


def joined_path_constant(node: ast.AST) -> str | None:
    """``ROOT / "experiments" / "lef-mill-r629.py"`` → ``experiments/lef-mill-r629.py``."""

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
