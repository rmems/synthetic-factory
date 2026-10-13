#!/usr/bin/env python3
"""AST literal helpers for the search catalog extract.

Nothing here executes source. ``ast.parse`` is the only interpreter step.
"""

from __future__ import annotations

import ast
from collections.abc import Callable, Mapping
from typing import Any

UNSET = object()


def _assignment(node: ast.stmt) -> tuple[list[ast.expr], ast.expr | None]:
    """``(targets, value)`` of an ``Assign`` or ``AnnAssign``; ``([], None)`` otherwise."""

    if isinstance(node, ast.AnnAssign):
        return [node.target], node.value
    if isinstance(node, ast.Assign):
        return node.targets, node.value
    return [], None


def assignment_of(node: ast.stmt) -> tuple[str | None, ast.AST | None]:
    """Return ``(name, value)`` for a simple ``NAME = value`` statement."""

    targets, value = _assignment(node)
    if len(targets) == 1 and isinstance(targets[0], ast.Name):
        return targets[0].id, value
    return None, None


def assignment_names(node: ast.stmt) -> tuple[str, ...]:
    targets, _ = _assignment(node)
    return tuple(target.id for target in targets if isinstance(target, ast.Name))


def literal_value(node: ast.AST, env: Mapping[str, Any] | None = None) -> Any:
    """Resolve constants, names, and literal containers; else ``UNSET``.

    The helpers add no recursion depth: a ``-`` operand recurses here
    directly, a container only through ``_sequence`` or ``_mapping``, and
    ``_negated`` / ``_container_builder`` never recurse.
    """

    bound = env or {}
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Name):
        return bound.get(node.id, UNSET)
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        return _negated(literal_value(node.operand, bound))
    build = _container_builder(node)
    return UNSET if build is None else build(node, bound)


def _negated(inner: Any) -> Any:
    return -inner if isinstance(inner, (int, float)) else UNSET


def _container_builder(node: ast.AST) -> Callable[[Any, Mapping[str, Any]], Any] | None:
    """``_sequence`` for a tuple, list or set literal, ``_mapping`` for a dict, else None."""

    if isinstance(node, (ast.Tuple, ast.List, ast.Set)):
        return _sequence
    if isinstance(node, ast.Dict):
        return _mapping
    return None


def _sequence_ctor(node: ast.Tuple | ast.List | ast.Set) -> Callable[[list[Any]], Any]:
    """``tuple`` / ``list`` / ``set`` for the literal's own container type."""

    if isinstance(node, ast.Tuple):
        return tuple
    if isinstance(node, ast.List):
        return list
    return set


def _sequence(node: ast.Tuple | ast.List | ast.Set, env: Mapping[str, Any]) -> Any:
    ctor = _sequence_ctor(node)
    values: list[Any] = []
    for elt in node.elts:
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


def module_docstring(tree: ast.AST) -> str:
    """The module's raw (uncleaned) docstring; ``""`` for no docstring or a non-module."""

    if not isinstance(tree, ast.Module):
        return ""
    return ast.get_docstring(tree, clean=False) or ""
