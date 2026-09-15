#!/usr/bin/env python3
"""AST literal helpers for the EVH catalog extract.

Nothing here executes source. ``ast.parse`` is the only interpreter step.
``resolve`` evaluates constants, names, containers, f-strings, integer
arithmetic, subscript/slice, and a closed set of ``str`` methods. Calls to
``exec``, ``eval``, ``compile``, ``runpy``, or anything else stay ``UNSET``.
"""

from __future__ import annotations

import ast
from collections.abc import Mapping
from typing import Any

UNSET = object()

_STR_METHODS = frozenset({"replace", "title", "upper"})


def assignment_of(node: ast.stmt) -> tuple[str | None, ast.AST | None]:
    """Return ``(name, value)`` for a simple ``NAME = value`` statement."""

    if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
        return node.target.id, node.value
    if isinstance(node, ast.Assign) and len(node.targets) == 1:
        target = node.targets[0]
        if isinstance(target, ast.Name):
            return target.id, node.value
    return None, None


def call_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
        return node.func.id
    return None


def resolve(node: ast.AST, env: Mapping[str, Any] | None = None) -> Any:
    """Resolve a closed set of literal AST forms; else ``UNSET``."""

    bound = env or {}
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Name):
        return bound[node.id] if node.id in bound else UNSET
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        inner = resolve(node.operand, bound)
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
    if isinstance(node, ast.BinOp):
        return _binop(node, bound)
    if isinstance(node, ast.Subscript):
        return _subscript(node, bound)
    if isinstance(node, ast.Slice):
        return _slice_value(node, bound)
    if isinstance(node, ast.Call):
        return _safe_call(node, bound)
    return UNSET


def require(node: ast.AST, env: Mapping[str, Any], ctx: str) -> Any:
    value = resolve(node, env)
    if value is UNSET:
        lineno = getattr(node, "lineno", "?")
        raise ValueError(f"{ctx}: cannot resolve AST at line {lineno}")
    return value


def _sequence(elts: list[ast.AST], env: Mapping[str, Any], ctor):
    values: list[Any] = []
    for elt in elts:
        item = resolve(elt, env)
        if item is UNSET:
            return UNSET
        values.append(item)
    return ctor(values)


def _mapping(node: ast.Dict, env: Mapping[str, Any]) -> Any:
    out: dict[Any, Any] = {}
    for key_node, value_node in zip(node.keys, node.values, strict=True):
        if key_node is None:
            return UNSET
        key = resolve(key_node, env)
        value = resolve(value_node, env)
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
        if value.format_spec is not None:
            return UNSET
        if value.conversion not in (-1, 115):
            return UNSET
        inner = resolve(value.value, env)
        if inner is UNSET or not isinstance(inner, (str, int)):
            return UNSET
        parts.append(str(inner))
    return "".join(parts)


def _binop(node: ast.BinOp, env: Mapping[str, Any]) -> Any:
    left = resolve(node.left, env)
    right = resolve(node.right, env)
    if left is UNSET or right is UNSET:
        return UNSET
    if isinstance(node.op, ast.Add):
        if isinstance(left, str) and isinstance(right, str):
            return left + right
        if isinstance(left, int) and isinstance(right, int):
            return left + right
        return UNSET
    if isinstance(node.op, ast.Sub) and isinstance(left, int) and isinstance(right, int):
        return left - right
    if (
        isinstance(node.op, ast.FloorDiv)
        and isinstance(left, int)
        and isinstance(right, int)
    ):
        return left // right
    return UNSET


def _subscript(node: ast.Subscript, env: Mapping[str, Any]) -> Any:
    owner = resolve(node.value, env)
    if owner is UNSET:
        return UNSET
    slc = node.slice
    if isinstance(slc, ast.Slice):
        start = resolve(slc.lower, env) if slc.lower is not None else None
        stop = resolve(slc.upper, env) if slc.upper is not None else None
        step = resolve(slc.step, env) if slc.step is not None else None
        if slc.lower is not None and start is UNSET:
            return UNSET
        if slc.upper is not None and stop is UNSET:
            return UNSET
        if slc.step is not None and step is UNSET:
            return UNSET
        try:
            return owner[start:stop:step]
        except (TypeError, KeyError, IndexError):
            return UNSET
    index = resolve(slc, env)
    if index is UNSET:
        return UNSET
    try:
        return owner[index]
    except (TypeError, KeyError, IndexError):
        return UNSET


def _slice_value(node: ast.Slice, env: Mapping[str, Any]) -> Any:
    start = resolve(node.lower, env) if node.lower is not None else None
    stop = resolve(node.upper, env) if node.upper is not None else None
    step = resolve(node.step, env) if node.step is not None else None
    if node.lower is not None and start is UNSET:
        return UNSET
    if node.upper is not None and stop is UNSET:
        return UNSET
    if node.step is not None and step is UNSET:
        return UNSET
    return slice(start, stop, step)


def _safe_call(node: ast.Call, env: Mapping[str, Any]) -> Any:
    name = call_name(node)
    if name in {"exec", "eval", "compile", "__import__"}:
        return UNSET
    if name == "pair":
        args = [resolve(arg, env) for arg in node.args]
        if node.keywords or any(item is UNSET for item in args):
            return UNSET
        return tuple(args)
    if not isinstance(node.func, ast.Attribute):
        return UNSET
    if node.func.attr not in _STR_METHODS:
        return UNSET
    owner = resolve(node.func.value, env)
    if not isinstance(owner, str):
        return UNSET
    args = [resolve(arg, env) for arg in node.args]
    if node.keywords or any(item is UNSET for item in args):
        return UNSET
    if node.func.attr == "replace" and len(args) == 2:
        if not all(isinstance(item, str) for item in args):
            return UNSET
        return owner.replace(args[0], args[1])
    if node.func.attr == "title" and not args:
        return owner.title()
    if node.func.attr == "upper" and not args:
        return owner.upper()
    return UNSET


def joined_path_constant(node: ast.AST) -> str | None:
    """``ROOT / "scripts" / "eval_harness_unique_mill"`` → directory path."""

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


def function_named(tree: ast.AST, name: str) -> ast.FunctionDef | None:
    for node in getattr(tree, "body", ()):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    return None
