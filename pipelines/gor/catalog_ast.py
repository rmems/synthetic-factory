#!/usr/bin/env python3
"""AST literal helpers for the GOR catalog extract.

Nothing here executes source. ``ast.parse`` is the only interpreter step.
"""

from __future__ import annotations

import ast
from collections.abc import Callable, Mapping, Sequence
from functools import partial
from typing import Any, TypeGuard

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

    Recursion stays here (``-x``, ``a + b``) and in the container readers, exactly
    one frame per ``-``/``+`` level; the predicates and readers chosen below do not
    call back into it.
    """

    bound = env or {}
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Name):
        return bound[node.id] if node.id in bound else UNSET
    if not isinstance(
        node, (ast.UnaryOp, ast.BinOp, ast.Tuple, ast.List, ast.Set, ast.Dict, ast.JoinedStr)
    ):
        return UNSET
    if _minus(node):
        return _negative_number(literal_value(node.operand, bound))
    if _plus(node):
        return _string_sum(literal_value(node.left, bound), literal_value(node.right, bound))
    return _read_container(node)(bound)


def _minus(node: ast.AST) -> TypeGuard[ast.UnaryOp]:
    return isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub)


def _plus(node: ast.AST) -> TypeGuard[ast.BinOp]:
    return isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add)


def _negative_number(operand: Any) -> Any:
    return UNSET if not isinstance(operand, (int, float)) else -operand


def _string_sum(left: Any, right: Any) -> Any:
    if not isinstance(left, str) or not isinstance(right, str):
        return UNSET
    return left + right


def _read_container(node: ast.AST) -> Callable[[Mapping[str, Any]], Any]:
    """Bind the reader for a sequence, dict, or f-string node; it does the recursing."""

    if isinstance(node, (ast.Tuple, ast.List, ast.Set)):
        ctor = tuple if isinstance(node, ast.Tuple) else set if isinstance(node, ast.Set) else list
        return partial(_sequence, node.elts, ctor=ctor)
    if isinstance(node, ast.JoinedStr):
        return partial(_joined_string, node)
    if isinstance(node, ast.Dict):
        return partial(_mapping, node)
    return _nothing


def _nothing(_bound: Mapping[str, Any]) -> Any:
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


def ctor_kwargs(node: ast.AST, env: Mapping[str, Any] | None = None) -> dict[str, Any] | None:
    """Arguments of a ``Name(...)`` catalog constructor when every value is a literal."""

    if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Name):
        return None
    if any(isinstance(arg, ast.Starred) for arg in node.args):
        return None
    if any(keyword.arg is None for keyword in node.keywords):
        return None
    name = node.func.id
    bound = env or {}
    return _ctor_values(node, name, bound)


def _ctor_values(node: ast.Call, name: str, bound: Mapping[str, Any]) -> dict[str, Any] | None:
    """Positional literals named by ``CTOR_POSARGS``, then the keyword literals."""

    out: dict[str, Any] = {}
    pos_names = CTOR_POSARGS.get(name)
    if node.args:
        if pos_names is None or len(node.args) > len(pos_names):
            return None
        for key, arg in zip(pos_names, node.args, strict=False):
            value = literal_value(arg, bound)
            if value is UNSET:
                return None
            out[key] = value
    return _with_keyword_values(node, bound, out)


def _with_keyword_values(
    node: ast.Call, bound: Mapping[str, Any], out: dict[str, Any]
) -> dict[str, Any] | None:
    for keyword in node.keywords:
        value = literal_value(keyword.value, bound)
        if keyword.arg is None or value is UNSET:
            return None
        out[keyword.arg] = value
    return out


def call_positional(node: ast.AST) -> list[ast.AST] | None:
    if not isinstance(node, ast.Call):
        return None
    if any(isinstance(arg, ast.Starred) for arg in node.args):
        return None
    return list(node.args)


def joined_path_constant(node: ast.AST) -> str | None:
    """``ROOT / "experiments" / "gor-mill-r946.py"`` → ``experiments/gor-mill-r946.py``."""

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
