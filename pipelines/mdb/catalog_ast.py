#!/usr/bin/env python3
"""AST literal helpers for the MDB catalog extract.

Nothing here executes source. ``ast.parse`` is the only interpreter step.
"""

from __future__ import annotations

import ast
from collections.abc import Callable, Mapping, Sequence
from functools import partial
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


def literal_value(node: ast.AST, env: Mapping[str, Any] | None = None) -> Any:
    """Resolve constants, names, containers, and constant f-strings; else ``UNSET``.

    Only this function and the container readers it calls recurse, so a nesting
    level costs one frame for ``-``/``+`` and two for a container, as it always did;
    matching a pattern never calls a Python helper, so leaves cost nothing extra.
    """

    bound = env or {}
    resolved: Any = UNSET
    match node:
        case ast.Name(id=name) if name in bound:
            resolved = bound[name]
        case ast.Constant():
            resolved = node.value
        case ast.BinOp(op=ast.Add(), left=left, right=right):
            resolved = _text_sum(literal_value(left, bound), literal_value(right, bound))
        case ast.UnaryOp(op=ast.USub(), operand=operand):
            resolved = _negative(literal_value(operand, bound))
        case ast.Dict() | ast.JoinedStr() | ast.Tuple() | ast.List() | ast.Set():
            resolved = _reader_for(node)(bound)
    return resolved


def _text_sum(left: Any, right: Any) -> Any:
    both_text = isinstance(left, str) and isinstance(right, str)
    return left + right if both_text else UNSET


def _negative(value: Any) -> Any:
    """A negated int or float; any other operand has no literal value."""

    if isinstance(value, (int, float)):
        return -value
    return UNSET


def _reader_for(
    node: ast.Dict | ast.JoinedStr | ast.Tuple | ast.List | ast.Set,
) -> Callable[[Mapping[str, Any]], Any]:
    """The non-recursive choice of reader for a container or f-string node."""

    if isinstance(node, ast.Dict):
        return partial(_mapping, node)
    if isinstance(node, ast.JoinedStr):
        return partial(_joined_string, node)
    if isinstance(node, ast.Tuple):
        return partial(_sequence, node.elts, ctor=tuple)
    return partial(_sequence, node.elts, ctor=set if isinstance(node, ast.Set) else list)


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


def call_posargs(node: ast.AST, env: Mapping[str, Any] | None = None) -> list[Any] | None:
    """Positional arguments of a ``Name(...)`` call when every value is a literal."""

    if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Name):
        return None
    out: list[Any] = []
    for arg in node.args:
        value = literal_value(arg, env)
        if value is UNSET:
            return None
        out.append(value)
    return out


def joined_path_constant(node: ast.AST) -> str | None:
    """``ROOT / "experiments" / "mdb-mill-r709.py"`` → ``experiments/mdb-mill-r709.py``."""

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


def with_name_path(node: ast.AST) -> str | None:
    """``Path(__file__).with_name("mdb-mill-r776.py")`` → ``experiments/mdb-mill-r776.py``."""

    if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
        return None
    if node.func.attr != "with_name" or len(node.args) != 1:
        return None
    name = literal_value(node.args[0])
    if isinstance(name, str) and name.endswith(".py"):
        return f"experiments/{name}"
    return None


def extract_source_path(source: str, names: tuple[str, ...]) -> str | None:
    tree = ast.parse(source)
    for node in tree.body:
        assigned, value = assignment_of(node)
        if assigned in names and value is not None:
            found = joined_path_constant(value) or with_name_path(value)
            if found is not None:
                return found
    return None
