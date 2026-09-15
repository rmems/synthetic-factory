#!/usr/bin/env python3
"""AST literal and call helpers for the ACM catalog extract.

Nothing here executes source. ``ast.parse`` is the only interpreter step.
"""

from __future__ import annotations

import ast
from collections.abc import Mapping
from typing import Any

from . import _contract

UNSET = object()
PLANT_CALLS = frozenset({"plant", "p", "ok", "bad"})
PLANT_FIELDS = (
    "slug",
    "domain",
    "success",
    "name",
    "stack",
    "field",
    "old",
    "new",
    "fail_err",
    "plan",
    "residual",
    "vs",
    "fetch1",
    "fetch1_ok",
    "fetch2",
    "fetch2_ok",
)


def assignment_of(node: ast.stmt) -> tuple[str | None, ast.AST | None]:
    """Return ``(name, value)`` for a simple ``NAME = value`` statement."""

    if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
        return node.target.id, node.value
    if isinstance(node, ast.Assign) and len(node.targets) == 1:
        target = node.targets[0]
        if isinstance(target, ast.Name):
            return target.id, node.value
    return None, None


def literal_value(node: ast.AST, env: Mapping[str, Any]) -> Any:
    """Resolve a constant, name, f-string, or string add; else ``UNSET``."""

    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Name):
        return env[node.id] if node.id in env else UNSET
    if isinstance(node, ast.Attribute) and node.attr in env:
        return env[node.attr]
    if isinstance(node, ast.JoinedStr):
        return _joined_string(node, env)
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        left = literal_value(node.left, env)
        right = literal_value(node.right, env)
        if isinstance(left, str) and isinstance(right, str):
            return left + right
    return UNSET


def _joined_string(node: ast.JoinedStr, env: Mapping[str, Any]) -> Any:
    parts: list[str] = []
    for value in node.values:
        if isinstance(value, ast.Constant):
            parts.append("" if value.value is None else str(value.value))
            continue
        if not isinstance(value, ast.FormattedValue):
            return UNSET
        inner = literal_value(value.value, env)
        if inner is UNSET or not isinstance(inner, (str, int)):
            return UNSET
        parts.append(str(inner))
    return "".join(parts)


def module_env(tree: ast.AST) -> dict[str, Any]:
    """Collect module-level string/int/bool names used to join fetch URLs."""

    env: dict[str, Any] = {}
    statements = list(getattr(tree, "body", ()))
    for node in statements:
        name, value = assignment_of(node)
        if name is None or value is None:
            continue
        if isinstance(value, ast.Constant) and isinstance(value.value, (str, int, bool)):
            env[name] = value.value
    for node in statements:
        name, value = assignment_of(node)
        if name is None or value is None or name in env:
            continue
        resolved = literal_value(value, env)
        if resolved is not UNSET and isinstance(resolved, (str, int, bool)):
            env[name] = resolved
    return env


def string_tuple(node: ast.AST, env: Mapping[str, Any]) -> tuple[str, ...]:
    """Strings from a tuple literal; skip unresolved elts."""

    if not isinstance(node, (ast.Tuple, ast.List)):
        return ()
    values: list[str] = []
    for elt in node.elts:
        item = literal_value(elt, env)
        if isinstance(item, str):
            values.append(item)
    return tuple(values)


def plant_kwargs(node: ast.AST, env: Mapping[str, Any]) -> dict[str, Any] | None:
    """Keyword arguments of a ``plant`` / ``p`` / ``ok`` / ``bad`` call."""

    if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Name):
        return None
    if node.func.id not in PLANT_CALLS:
        return None
    out: dict[str, Any] = {}
    for keyword in node.keywords:
        if keyword.arg is None or keyword.arg not in PLANT_FIELDS:
            continue
        value = literal_value(keyword.value, env)
        if value is not UNSET:
            out[keyword.arg] = value
    if node.func.id == "ok":
        out.setdefault("success", True)
    elif node.func.id == "bad":
        out.setdefault("success", False)
    if not isinstance(out.get("slug"), str) or not out["slug"]:
        return None
    return out


def pair_elts(
    node: ast.AST, env: Mapping[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]] | None:
    """One ``(success_plant, fail_plant)`` tuple from a ``PAIRS`` list."""

    if not isinstance(node, ast.Tuple) or len(node.elts) != 2:
        return None
    success = plant_kwargs(node.elts[0], env)
    fail = plant_kwargs(node.elts[1], env)
    if success is None or fail is None:
        return None
    return success, fail


_contract.bind_import_twin(__name__)
