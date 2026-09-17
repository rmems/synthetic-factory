#!/usr/bin/env python3
"""AST literal helpers for the AZR catalog extract.

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


def call_kwargs(node: ast.AST, env: Mapping[str, Any] | None = None) -> dict[str, Any] | None:
    """Keyword arguments of a ``Name(...)`` call when every value is a literal."""

    if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Name):
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


def identity_kwargs(node: ast.AST) -> dict[str, Any] | None:
    """``dict(...)``, ``add(...)``, or ``add(dict(...))`` keyword identity."""

    if call_name(node) == "add":
        if node.args and not node.keywords and call_name(node.args[0]) == "dict":
            return call_kwargs(node.args[0])
        return call_kwargs(node)
    if call_name(node) == "dict":
        return call_kwargs(node)
    if isinstance(node, ast.Dict):
        resolved = literal_value(node)
        return resolved if isinstance(resolved, dict) else None
    return None


def joined_path_constant(node: ast.AST) -> str | None:
    """``ROOT / "experiments" / "azr-mill-r1181.py"`` → ``experiments/azr-mill-r1181.py``."""

    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.Name):
        return None
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
        if node.func.attr == "with_name" and node.args:
            name = joined_path_constant(node.args[0])
            return name
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


def normalize_experiments_path(path: str) -> str:
    name = path.replace("\\", "/").lstrip("./")
    if name.startswith("experiments/"):
        return name
    if "/" not in name and name.endswith(".py"):
        return f"experiments/{name}"
    return name


def extract_joined_path_assignment(source: str, name: str) -> str | None:
    tree = ast.parse(source)
    for node in tree.body:
        assigned, value = assignment_of(node)
        if assigned == name and value is not None:
            found = joined_path_constant(value)
            return normalize_experiments_path(found) if found else None
    return None


def extract_spec_paths(source: str) -> tuple[str, ...]:
    """``spec_from_file_location(..., PATH)`` string operands, normalized."""

    tree = ast.parse(source)
    paths: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if not isinstance(func, ast.Attribute) or func.attr != "spec_from_file_location":
            continue
        if len(node.args) < 2:
            continue
        found = joined_path_constant(node.args[1])
        if found:
            paths.append(normalize_experiments_path(found))
    return tuple(paths)


def tip_slug_asserts(tree: ast.AST) -> dict[str, str]:
    """``PAIRS[0][0]["slug"] != "tip"`` / ``PAIRS[0][1]["slug"] != "fail"``."""

    tips: dict[str, str] = {}
    for node in ast.walk(tree):
        if not isinstance(node, ast.Compare) or not node.ops:
            continue
        if not isinstance(node.ops[0], ast.NotEq):
            continue
        if not isinstance(node.comparators[0], ast.Constant):
            continue
        slug = node.comparators[0].value
        if not isinstance(slug, str):
            continue
        left = node.left
        if not isinstance(left, ast.Subscript) or not isinstance(left.slice, ast.Constant):
            continue
        if left.slice.value != "slug":
            continue
        inner = left.value
        if not isinstance(inner, ast.Subscript) or not isinstance(inner.slice, ast.Constant):
            continue
        index = inner.slice.value
        if index == 0:
            tips["success"] = slug
        elif index == 1:
            tips["fail"] = slug
    return tips


def function_named(tree: ast.AST, name: str) -> ast.FunctionDef | None:
    for node in getattr(tree, "body", ()):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    return None


def add_identities(func: ast.AST) -> list[dict[str, Any]]:
    """``add(dict(...))`` / ``add(slug=..., plant=...)`` rows inside ``func``."""

    rows: list[dict[str, Any]] = []
    for node in ast.walk(func):
        if call_name(node) != "add":
            continue
        kwargs = identity_kwargs(node)
        if kwargs and "slug" in kwargs:
            rows.append(kwargs)
    return rows
