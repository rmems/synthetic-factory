#!/usr/bin/env python3
"""AST literal helpers for the SSR catalog extract.

Nothing here executes source. ``ast.parse`` is the only interpreter step.
"""

from __future__ import annotations

import ast
from collections.abc import Callable, Mapping, Sequence
from typing import Any, TypeGuard

UNSET = object()
PAIR_CTORS = frozenset({"plant", "S"})


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
    """Resolve constants, names, containers, and constant f-strings; else ``UNSET``.

    The helpers below only classify or combine and every recursive call is made here,
    so a ``-x`` or ``a + b`` level costs one frame and a container or f-string level two.
    """

    bound = env or {}
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Name):
        return bound.get(node.id, UNSET)
    if _is_negation(node):
        return _negated(literal_value(node.operand, bound))
    if _is_concatenation(node):
        left = literal_value(node.left, bound)
        return _concatenated(left, literal_value(node.right, bound))
    evaluate, args = _compound_step(node)
    return evaluate(*args, bound)


def _is_negation(node: ast.AST) -> TypeGuard[ast.UnaryOp]:
    return isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub)


def _is_concatenation(node: ast.AST) -> TypeGuard[ast.BinOp]:
    return isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add)


def _negated(inner: Any) -> Any:
    """``-inner`` for a resolved number; anything else stays ``UNSET``."""

    return -inner if isinstance(inner, (int, float)) else UNSET


def _concatenated(left: Any, right: Any) -> Any:
    """``left + right`` for two resolved strings; anything else stays ``UNSET``."""

    if isinstance(left, str) and isinstance(right, str):
        return left + right
    return UNSET


def _compound_step(node: ast.AST) -> tuple[Callable[..., Any], tuple[Any, ...]]:
    """``(evaluator, leading arguments)`` for a dict, f-string, set, tuple or list node.

    Never recurses itself; every other node maps to ``_unresolved`` and stays ``UNSET``.
    """

    if isinstance(node, ast.Dict):
        return _mapping, (node,)
    if isinstance(node, ast.JoinedStr):
        return _joined_string, (node,)
    if isinstance(node, ast.Set):
        return _sequence, (node.elts, set)
    if isinstance(node, (ast.Tuple, ast.List)):
        return _sequence, (node.elts, tuple if isinstance(node, ast.Tuple) else list)
    return _unresolved, ()


def _unresolved(_env: Mapping[str, Any]) -> Any:
    return UNSET


def _sequence(elts: Sequence[ast.expr], ctor, env: Mapping[str, Any]):
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


def const_keyword(node: ast.AST, name: str) -> str | None:
    """String constant keyword ``name`` on a ``Name(...)`` call, else ``None``."""

    if not isinstance(node, ast.Call):
        return None
    for keyword in node.keywords:
        if keyword.arg != name:
            continue
        if isinstance(keyword.value, ast.Constant) and isinstance(keyword.value.value, str):
            return keyword.value.value
    return None


def ctor_identity(node: ast.AST) -> dict[str, str | None] | None:
    """``slug`` / ``scanner`` from a ``plant(...)`` or ``S(...)`` call."""

    name = call_name(node)
    if name not in PAIR_CTORS or not isinstance(node, ast.Call):
        return None
    slug = const_keyword(node, "slug")
    scanner = const_keyword(node, "scanner")
    if name == "S":
        if slug is None:
            slug = _str_arg(node, 0)
        if scanner is None:
            scanner = _str_arg(node, 1)
    if not slug:
        return None
    return {"slug": slug, "scanner": scanner}


def _str_arg(node: ast.Call, index: int) -> str | None:
    """String constant positional argument ``index``, else ``None``."""

    if index >= len(node.args):
        return None
    arg = node.args[index]
    if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
        return arg.value
    return None


def joined_path_constant(node: ast.AST) -> str | None:
    """``ROOT / "experiments" / "ssr-mill-r181.py"`` → ``experiments/ssr-mill-r181.py``."""

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


def spec_from_file_name(tree: ast.AST) -> str | None:
    """Filename passed to ``importlib.util.spec_from_file_location``."""

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        if node.func.attr != "spec_from_file_location" or len(node.args) < 2:
            continue
        found = joined_path_constant(node.args[1])
        if found:
            return found
    return None
