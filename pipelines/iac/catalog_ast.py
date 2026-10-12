#!/usr/bin/env python3
"""AST literal helpers for the IAC catalog extract.

Nothing here executes source. ``ast.parse`` is the only interpreter step.
"""

from __future__ import annotations

import ast
from collections.abc import Callable, Mapping, Sequence
from functools import partial
from typing import Any, TypeGuard

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


# Nodes that can still resolve to a literal once constants and bound names are ruled out.
_COMPOSITE_NODES = (ast.UnaryOp, ast.BinOp, ast.Tuple, ast.List, ast.Set, ast.Dict, ast.JoinedStr)
# The container each sequence literal builds; ``ast.parse`` only yields these exact classes.
_SEQUENCE_TYPES: dict[type, type] = {ast.Tuple: tuple, ast.List: list, ast.Set: set}


def literal_value(node: ast.AST, env: Mapping[str, Any] | None = None) -> Any:
    """Resolve constants, names, containers, and constant f-strings; else ``UNSET``.

    ``-x`` and ``a + b`` recurse straight back into this function, and containers
    recurse through ``_sequence`` / ``_mapping`` / ``_joined_string``, so every
    nesting level costs the frames it always did. The helpers below never recurse.
    """

    bound = env or {}
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Name):
        return bound[node.id] if node.id in bound else UNSET
    if not isinstance(node, _COMPOSITE_NODES):
        return UNSET
    if _is_negation(node):
        return _negated(literal_value(node.operand, bound))
    if _is_concatenation(node):
        return _concatenated(literal_value(node.left, bound), literal_value(node.right, bound))
    return _container_reader(node)(bound)


def _is_negation(node: ast.AST) -> TypeGuard[ast.UnaryOp]:
    return isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub)


def _is_concatenation(node: ast.AST) -> TypeGuard[ast.BinOp]:
    return isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add)


def _negated(inner: Any) -> Any:
    return -inner if isinstance(inner, (int, float)) else UNSET


def _concatenated(left: Any, right: Any) -> Any:
    """``str + str`` of two resolved literals; anything else is ``UNSET``."""

    if isinstance(left, str) and isinstance(right, str):
        return left + right
    return UNSET


def _container_reader(node: ast.AST) -> Callable[[Mapping[str, Any]], Any]:
    """Pick the reader that resolves ``node`` against the bound names (no recursion here)."""

    if isinstance(node, (ast.Tuple, ast.List, ast.Set)):
        return partial(_sequence, node.elts, ctor=_SEQUENCE_TYPES[type(node)])
    if isinstance(node, ast.Dict):
        return partial(_mapping, node)
    if isinstance(node, ast.JoinedStr):
        return partial(_joined_string, node)
    return _unset


def _unset(_bound: Mapping[str, Any]) -> Any:
    """A unary operator other than ``-`` or a binary one other than ``+`` resolves to nothing."""

    return UNSET


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


def call_kwargs(node: ast.AST, env: Mapping[str, Any] | None = None) -> dict[str, Any] | None:
    """Keyword arguments of a ``Name(...)`` call when every value is a literal."""

    if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Name):
        return None
    if node.args or any(keyword.arg is None for keyword in node.keywords):
        return None
    return _literal_keywords(node, env)


def _literal_keywords(node: ast.Call, env: Mapping[str, Any] | None) -> dict[str, Any] | None:
    """Every keyword value as a literal, or None as soon as one is not."""

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
