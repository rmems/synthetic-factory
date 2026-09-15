#!/usr/bin/env python3
"""AST helpers for the AMC catalog extract.

``ast.parse`` and ``ast.literal_eval`` are the only interpreter steps.
Nothing here imports, compiles, or execs a mill publisher.
"""

from __future__ import annotations

import ast
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


def literal_value(node: ast.AST) -> Any:
    """``ast.literal_eval`` wrapper that returns ``UNSET`` for non-literals."""

    try:
        return ast.literal_eval(node)
    except (ValueError, TypeError, SyntaxError, MemoryError):
        return UNSET


def call_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
        return node.func.id
    return None


def call_kwargs(node: ast.AST) -> dict[str, Any] | None:
    """Keyword arguments of a ``Name(...)`` call when every value is a literal."""

    if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Name):
        return None
    if any(keyword.arg is None for keyword in node.keywords):
        return None
    out: dict[str, Any] = {}
    for keyword in node.keywords:
        value = literal_value(keyword.value)
        if keyword.arg is None or value is UNSET:
            return None
        out[keyword.arg] = value
    return out


def call_posargs(node: ast.AST) -> list[Any] | None:
    """Positional arguments of a ``Name(...)`` call when every value is a literal."""

    if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Name):
        return None
    values: list[Any] = []
    for arg in node.args:
        value = literal_value(arg)
        if value is UNSET:
            return None
        values.append(value)
    return values


def joined_path_constant(node: ast.AST) -> str | None:
    """``REPO / "experiments/amc-mill-r170.py"`` → the string operand(s)."""

    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.Call) and call_name(node) == "str" and node.args:
        return joined_path_constant(node.args[0])
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


def module_literals(tree: ast.AST) -> dict[str, Any]:
    """Top-level ``NAME = <literal>`` bindings only."""

    env: dict[str, Any] = {}
    for node in getattr(tree, "body", ()):
        name, value = assignment_of(node)
        if name is None or value is None:
            continue
        resolved = literal_value(value)
        if resolved is not UNSET:
            env[name] = resolved
    return env
