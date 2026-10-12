#!/usr/bin/env python3
"""AST literal helpers for the EVH catalog extract.

Nothing here executes source. ``ast.parse`` is the only interpreter step.
``resolve`` evaluates constants, names, containers, f-strings, integer
arithmetic, subscript/slice, and a closed set of ``str`` methods. Calls to
``exec``, ``eval``, ``compile``, ``runpy``, or anything else stay ``UNSET``.
"""

from __future__ import annotations

import ast
from collections.abc import Callable, Mapping
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
    for node_type, resolver in _RESOLVERS:
        if isinstance(node, node_type):
            return resolver(node, bound)
    return UNSET


def require(node: ast.AST, env: Mapping[str, Any], ctx: str) -> Any:
    value = resolve(node, env)
    if value is UNSET:
        lineno = getattr(node, "lineno", "?")
        raise ValueError(f"{ctx}: cannot resolve AST at line {lineno}")
    return value


def _constant(node: ast.Constant, _unused_env: Mapping[str, Any]) -> Any:
    """A literal needs no bindings; the ``env`` slot keeps the resolver-table signature."""

    return node.value


def _name(node: ast.Name, env: Mapping[str, Any]) -> Any:
    return env.get(node.id, UNSET)


def _unary(node: ast.UnaryOp, env: Mapping[str, Any]) -> Any:
    if not isinstance(node.op, ast.USub):
        return UNSET
    inner = resolve(node.operand, env)
    return -inner if isinstance(inner, (int, float)) else UNSET


def _tuple(node: ast.Tuple, env: Mapping[str, Any]) -> Any:
    return _sequence(node.elts, env, tuple)


def _list(node: ast.List, env: Mapping[str, Any]) -> Any:
    return _sequence(node.elts, env, list)


def _set(node: ast.Set, env: Mapping[str, Any]) -> Any:
    values = _sequence(node.elts, env, list)
    return set(values) if values is not UNSET else UNSET


def _sequence(elts: list[ast.expr], env: Mapping[str, Any], ctor):
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
        part = _joined_part(value, env)
        if part is UNSET:
            return UNSET
        parts.append(part)
    return "".join(parts)


def _joined_part(value: ast.AST, env: Mapping[str, Any]) -> Any:
    """One f-string piece: a str literal or a plain/``!s`` replacement field."""

    if isinstance(value, ast.Constant) and isinstance(value.value, str):
        return value.value
    if not isinstance(value, ast.FormattedValue):
        return UNSET
    if value.format_spec is not None or value.conversion not in (-1, 115):
        return UNSET
    inner = resolve(value.value, env)
    if inner is UNSET or not isinstance(inner, (str, int)):
        return UNSET
    return str(inner)


def _binop(node: ast.BinOp, env: Mapping[str, Any]) -> Any:
    left = resolve(node.left, env)
    right = resolve(node.right, env)
    if left is UNSET or right is UNSET:
        return UNSET
    if isinstance(node.op, ast.Add):
        return _add(left, right)
    return _int_op(node.op, left, right)


def _int_op(op: ast.operator, left: Any, right: Any) -> Any:
    """``-`` and ``//`` on two ints; any other operator or operand stays ``UNSET``."""

    if not isinstance(left, int) or not isinstance(right, int):
        return UNSET
    if isinstance(op, ast.Sub):
        return left - right
    return left // right if isinstance(op, ast.FloorDiv) else UNSET


def _add(left: Any, right: Any) -> Any:
    if isinstance(left, str) and isinstance(right, str):
        return left + right
    if isinstance(left, int) and isinstance(right, int):
        return left + right
    return UNSET


def _subscript(node: ast.Subscript, env: Mapping[str, Any]) -> Any:
    owner = resolve(node.value, env)
    if owner is UNSET:
        return UNSET
    slc = node.slice
    if isinstance(slc, ast.Slice):
        bounds = _slice_bounds(slc, env)
        if bounds is UNSET:
            return UNSET
        return _item(owner, slice(*bounds))
    index = resolve(slc, env)
    if index is UNSET:
        return UNSET
    return _item(owner, index)


def _item(owner: Any, index: Any) -> Any:
    try:
        return owner[index]
    except (TypeError, KeyError, IndexError):
        return UNSET


def _slice_value(node: ast.Slice, env: Mapping[str, Any]) -> Any:
    bounds = _slice_bounds(node, env)
    if bounds is UNSET:
        return UNSET
    return slice(*bounds)


def _slice_bounds(node: ast.Slice, env: Mapping[str, Any]) -> Any:
    """Resolve every present bound first, then refuse if any stayed ``UNSET``."""

    bounds = tuple(
        resolve(part, env) if part is not None else None
        for part in (node.lower, node.upper, node.step)
    )
    if any(bound is UNSET for bound in bounds):
        return UNSET
    return bounds


def _safe_call(node: ast.Call, env: Mapping[str, Any]) -> Any:
    name = call_name(node)
    if name in {"exec", "eval", "compile", "__import__"}:
        return UNSET
    if name == "pair":
        args = _call_args(node, env)
        return tuple(args) if args is not UNSET else UNSET
    return _str_call(node, env)


def _str_call(node: ast.Call, env: Mapping[str, Any]) -> Any:
    if not isinstance(node.func, ast.Attribute) or node.func.attr not in _STR_METHODS:
        return UNSET
    owner = resolve(node.func.value, env)
    if not isinstance(owner, str):
        return UNSET
    args = _call_args(node, env)
    if args is UNSET:
        return UNSET
    return _str_method(owner, node.func.attr, args)


def _call_args(node: ast.Call, env: Mapping[str, Any]) -> Any:
    """Positional args, all resolved before keywords are refused."""

    args = [resolve(arg, env) for arg in node.args]
    if node.keywords or any(item is UNSET for item in args):
        return UNSET
    return args


def _str_method(owner: str, attr: str, args: list[Any]) -> Any:
    if attr == "replace" and len(args) == 2:
        return _str_replace(owner, args)
    if args:
        return UNSET
    if attr == "title":
        return owner.title()
    return owner.upper() if attr == "upper" else UNSET


def _str_replace(owner: str, args: list[Any]) -> Any:
    if not all(isinstance(item, str) for item in args):
        return UNSET
    return owner.replace(args[0], args[1])


# Each resolver takes the node type it is paired with; ``resolve`` dispatches by isinstance.
_RESOLVERS: tuple[tuple[type[ast.AST], Callable[[Any, Mapping[str, Any]], Any]], ...] = (
    (ast.Constant, _constant),
    (ast.Name, _name),
    (ast.UnaryOp, _unary),
    (ast.Tuple, _tuple),
    (ast.List, _list),
    (ast.Set, _set),
    (ast.Dict, _mapping),
    (ast.JoinedStr, _joined_string),
    (ast.BinOp, _binop),
    (ast.Subscript, _subscript),
    (ast.Slice, _slice_value),
    (ast.Call, _safe_call),
)


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
