#!/usr/bin/env python3
"""AST literal helpers for the GOR catalog extract.

Nothing here executes source. ``ast.parse`` is the only interpreter step.
"""

from __future__ import annotations

import ast
from collections.abc import Callable, Mapping
from functools import partial
from typing import Any

from .vocabulary import CTOR_POSARGS

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
    """Resolve constants, names, containers, and constant f-strings; else ``UNSET``.

    Unary minus and ``+`` recurse here directly. Containers and f-strings
    recurse through their one helper in ``_NESTED_LITERALS``, so every nesting
    level costs the same Python frames as before.
    """

    bound = env or {}
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        inner = literal_value(node.operand, bound)
        return -inner if isinstance(inner, (int, float)) else UNSET
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        return _concatenated(literal_value(node.left, bound), literal_value(node.right, bound))
    return _resolver_for(node)(node, bound)


def _resolver_for(node: ast.AST) -> Callable[[Any, Mapping[str, Any]], Any]:
    """The container or f-string resolver for ``node``; anything else is a leaf."""

    for node_type, resolve in _NESTED_LITERALS:
        if isinstance(node, node_type):
            return resolve
    return _leaf_value


def _leaf_value(node: ast.AST, env: Mapping[str, Any]) -> Any:
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Name):
        return env.get(node.id, UNSET)
    return UNSET


def _concatenated(left: Any, right: Any) -> Any:
    return left + right if isinstance(left, str) and isinstance(right, str) else UNSET


def _sequence(node: ast.Tuple | ast.List | ast.Set, env: Mapping[str, Any], ctor):
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


_NESTED_LITERALS: tuple[tuple[type[ast.AST], Callable[[Any, Mapping[str, Any]], Any]], ...] = (
    (ast.Tuple, partial(_sequence, ctor=tuple)),
    (ast.List, partial(_sequence, ctor=list)),
    (ast.Set, partial(_sequence, ctor=set)),
    (ast.Dict, _mapping),
    (ast.JoinedStr, _joined_string),
)


def call_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
        return node.func.id
    return None


def ctor_kwargs(node: ast.AST, env: Mapping[str, Any] | None = None) -> dict[str, Any] | None:
    """Arguments of a ``Name(...)`` catalog constructor when every value is a literal."""

    named = _named_arguments(node)
    if named is None:
        return None
    bound = env or {}
    out: dict[str, Any] = {}
    for key, arg in named:
        value = literal_value(arg, bound)
        if value is UNSET:
            return None
        out[key] = value
    return out


def _unpacks(node: ast.Call) -> bool:
    starred = any(isinstance(arg, ast.Starred) for arg in node.args)
    return starred or any(keyword.arg is None for keyword in node.keywords)


def _named_arguments(node: ast.AST) -> list[tuple[str, ast.expr]] | None:
    """``(name, value node)`` for each argument of a plain ``Name(...)`` call, positional first.

    None when ``node`` is not such a call, unpacks ``*args`` or ``**kwargs``, or
    passes more positional arguments than ``CTOR_POSARGS`` names for it.
    """

    if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Name):
        return None
    if _unpacks(node):
        return None
    pos_names = CTOR_POSARGS.get(node.func.id, ())
    if len(node.args) > len(pos_names):
        return None
    named = [(keyword.arg, keyword.value) for keyword in node.keywords if keyword.arg is not None]
    return [*zip(pos_names, node.args, strict=False), *named]


def call_positional(node: ast.AST) -> list[ast.AST] | None:
    if not isinstance(node, ast.Call):
        return None
    if any(isinstance(arg, ast.Starred) for arg in node.args):
        return None
    return list(node.args)


def joined_path_constant(node: ast.AST) -> str | None:
    """``ROOT / "experiments" / "gor-mill-r946.py"`` → ``experiments/gor-mill-r946.py``."""

    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
        return _joined_path(joined_path_constant(node.left), joined_path_constant(node.right))
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _joined_path(left: str | None, right: str | None) -> str | None:
    """A non-literal head such as ``ROOT`` drops out; a non-literal tail voids the path."""

    if right is None:
        return None
    return right if left is None else f"{left}/{right}"


def extract_joined_path_assignment(source: str, name: str) -> str | None:
    tree = ast.parse(source)
    for node in tree.body:
        assigned, value = assignment_of(node)
        if assigned == name and value is not None:
            return joined_path_constant(value)
    return None
