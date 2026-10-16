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
from functools import partial
from typing import Any, TypeGuard

UNSET = object()

_REPLACE = "replace"
_STR_METHODS = frozenset({_REPLACE, "title", "upper"})


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
    """Resolve a closed set of literal AST forms; else ``UNSET``.

    Constants, names and ``-x`` are handled here and every resolver in
    ``_RESOLVERS`` calls ``resolve`` directly, so a ``-x`` level costs one frame and
    any other nesting level two, as before the resolvers were split out.
    """

    bound = env or {}
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Name):
        return bound.get(node.id, UNSET)
    if _is_negation(node):
        return _negated(resolve(node.operand, bound))
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


def _is_negation(node: ast.AST) -> TypeGuard[ast.UnaryOp]:
    return isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub)


def _negated(inner: Any) -> Any:
    """``-inner`` for a resolved number; anything else stays ``UNSET``."""

    return -inner if isinstance(inner, (int, float)) else UNSET


def _sequence(
    node: ast.Tuple | ast.List | ast.Set, env: Mapping[str, Any], *, ctor: Callable[[list[Any]], Any]
) -> Any:
    values: list[Any] = []
    for elt in node.elts:
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
        piece = _joined_piece(value)
        part = _field_text(resolve(piece, env)) if isinstance(piece, ast.AST) else piece
        if part is UNSET:
            return UNSET
        parts.append(part)
    return "".join(parts)


def _joined_piece(value: ast.AST) -> Any:
    """One f-string piece: its str literal, the expression of a plain/``!s`` field, or
    ``UNSET`` for anything else. The caller resolves the expression itself."""

    if isinstance(value, ast.Constant) and isinstance(value.value, str):
        return value.value
    if not isinstance(value, ast.FormattedValue):
        return UNSET
    if value.format_spec is not None or value.conversion not in (-1, 115):
        return UNSET
    return value.value


def _field_text(inner: Any) -> Any:
    """``str(inner)`` for a resolved str or int field; anything else stays ``UNSET``."""

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
        bounds = _bounds_or_unset(
            [resolve(part, env) if part is not None else None for part in _slice_parts(slc)]
        )
        return UNSET if bounds is UNSET else _item(owner, slice(*bounds))
    index = resolve(slc, env)
    return UNSET if index is UNSET else _item(owner, index)


def _item(owner: Any, index: Any) -> Any:
    try:
        return owner[index]
    except (TypeError, KeyError, IndexError):
        return UNSET


def _slice_value(node: ast.Slice, env: Mapping[str, Any]) -> Any:
    bounds = _bounds_or_unset(
        [resolve(part, env) if part is not None else None for part in _slice_parts(node)]
    )
    return UNSET if bounds is UNSET else slice(*bounds)


def _slice_parts(node: ast.Slice) -> tuple[ast.expr | None, ast.expr | None, ast.expr | None]:
    return node.lower, node.upper, node.step


def _bounds_or_unset(bounds: list[Any]) -> Any:
    """Every present bound is resolved first; any that stayed ``UNSET`` refuses them all.

    ``UNSET`` is a private sentinel and resolved values are builtins, so ``in`` is the
    identity test, without a generator frame below the deepest ``resolve``.
    """

    if UNSET in bounds:
        return UNSET
    return tuple(bounds)


def _safe_call(node: ast.Call, env: Mapping[str, Any]) -> Any:
    name = call_name(node)
    if name in {"exec", "eval", "compile", "__import__"}:
        return UNSET
    if name == "pair":
        return _pair_tuple(_checked_args(node, [resolve(arg, env) for arg in node.args]))
    method = _str_method_target(node)
    if method is None:
        return UNSET
    owner = resolve(method.value, env)
    if not isinstance(owner, str):
        return UNSET
    args = _checked_args(node, [resolve(arg, env) for arg in node.args])
    return UNSET if args is UNSET else _str_method(owner, method.attr, args)


def _str_method_target(node: ast.Call) -> ast.Attribute | None:
    """``owner.method`` when ``method`` is one of the closed set of ``str`` methods."""

    func = node.func
    if isinstance(func, ast.Attribute) and func.attr in _STR_METHODS:
        return func
    return None


def _checked_args(node: ast.Call, args: list[Any]) -> Any:
    """Positional args, all resolved before keywords are refused."""

    if node.keywords or UNSET in args:
        return UNSET
    return args


def _pair_tuple(args: Any) -> Any:
    return UNSET if args is UNSET else tuple(args)


def _str_method(owner: str, attr: str, args: list[Any]) -> Any:
    """``replace`` with two strs, or ``title`` / ``upper`` with no args; else ``UNSET``."""

    if attr == _REPLACE and len(args) == 2:
        both_str = isinstance(args[0], str) and isinstance(args[1], str)
        return owner.replace(args[0], args[1]) if both_str else UNSET
    if args or attr == _REPLACE:
        return UNSET
    return owner.title() if attr == "title" else owner.upper()


# Each resolver takes the node type it is paired with; ``resolve`` dispatches by isinstance.
# The sequence ctors are bound with ``partial`` (a C callable, so no extra Python frame).
_RESOLVERS: tuple[tuple[type[ast.AST], Callable[[Any, Mapping[str, Any]], Any]], ...] = (
    (ast.Tuple, partial(_sequence, ctor=tuple)),
    (ast.List, partial(_sequence, ctor=list)),
    (ast.Set, partial(_sequence, ctor=set)),
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
