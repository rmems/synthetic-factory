#!/usr/bin/env python3
"""AST literal helpers for the NTP catalog extract.

Nothing here executes source. ``ast.parse`` is the only interpreter step.
"""

from __future__ import annotations

import ast
import re
import warnings
from collections.abc import Callable, Mapping, Sequence
from typing import Any, TypeGuard

UNSET = object()

_MILL_NAME_RE = re.compile(r"ntp-mill-[A-Za-z0-9_.-]+\.py\Z")
_WAVE_TABLE_RE = re.compile(r"^S(\d+)\Z")


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
        return bound[node.id] if node.id in bound else UNSET
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
    """Evaluator and leading arguments for a container or f-string node.

    Any other node gets ``_unresolved``, so it stays ``UNSET``.
    """

    if isinstance(node, ast.Tuple):
        return _sequence, (node.elts, tuple)
    if isinstance(node, (ast.List, ast.Set)):
        return _sequence, (node.elts, list if isinstance(node, ast.List) else set)
    if isinstance(node, ast.Dict):
        return _mapping, (node,)
    if isinstance(node, ast.JoinedStr):
        return _joined_string, (node,)
    return _unresolved, ()


def _unresolved(_env: Mapping[str, Any]) -> Any:
    return UNSET


def _sequence(elts: Sequence[ast.AST], ctor, env: Mapping[str, Any]):
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
    if node.args:
        return None
    names = _keyword_names(node)
    if names is None:
        return None
    out: dict[str, Any] = {}
    for name, keyword in zip(names, node.keywords, strict=True):
        value = literal_value(keyword.value, env)
        if value is UNSET:
            return None
        out[name] = value
    return out


def _keyword_names(node: ast.Call) -> list[str] | None:
    """Keyword names in call order; ``None`` when the call unpacks ``**mapping``."""

    names: list[str] = []
    for keyword in node.keywords:
        if keyword.arg is None:
            return None
        names.append(keyword.arg)
    return names


def call_posargs(node: ast.AST, env: Mapping[str, Any] | None = None) -> list[Any] | None:
    """Positional arguments of a ``Name(...)`` call when every value is a literal."""

    if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Name):
        return None
    if node.keywords:
        return None
    values: list[Any] = []
    for arg in node.args:
        value = literal_value(arg, env)
        if value is UNSET:
            return None
        values.append(value)
    return values


def joined_path_constant(node: ast.AST) -> str | None:
    """``ROOT / "experiments/ntp-mill-r1326.py"`` → ``experiments/ntp-mill-r1326.py``."""

    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.Call) and call_name(node) == "str" and node.args:
        return joined_path_constant(node.args[0])
    if isinstance(node, ast.Name):
        return None
    if _is_division(node):
        left = joined_path_constant(node.left)
        return _joined_path(left, joined_path_constant(node.right))
    return None


def _is_division(node: ast.AST) -> TypeGuard[ast.BinOp]:
    return isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div)


def _joined_path(left: str | None, right: str | None) -> str | None:
    """``left/right``; an unresolved left keeps ``right``, an unresolved right is ``None``."""

    if right is None:
        return None
    if left is None:
        return right
    return f"{left}/{right}"


def experiments_mill_path(name: str) -> str | None:
    """Normalize ``ntp-mill-….py`` or ``experiments/ntp-mill-….py`` to a repo path."""

    filename = name.rsplit("/", 1)[-1]
    if not _MILL_NAME_RE.fullmatch(filename):
        return None
    return f"experiments/{filename}"


def parse_tree(source: str, *, filename: str = "<ntp>") -> ast.AST:
    """``ast.parse`` only. SyntaxWarnings from recovered mills are suppressed."""

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", SyntaxWarning)
        return ast.parse(source, filename=filename)


def extract_replace_mill_target(source: str) -> str | None:
    """Last ``.replace(..., "ntp-mill-….py")`` target from a loop wrapper."""

    tree = parse_tree(source)
    found: list[str] = []
    for node in ast.walk(tree):
        replacement = _replace_argument(node)
        if replacement is None:
            continue
        new = literal_value(replacement)
        if not isinstance(new, str):
            continue
        path = experiments_mill_path(new)
        if path is not None:
            found.append(path)
    return found[-1] if found else None


def _replace_argument(node: ast.AST) -> ast.AST | None:
    """The replacement argument of one ``x.replace(old, new)`` call, else ``None``."""

    if not isinstance(node, ast.Call):
        return None
    if not isinstance(node.func, ast.Attribute) or node.func.attr != "replace":
        return None
    if len(node.args) != 2:
        return None
    return node.args[1]


def extract_named_mill_path(source: str, name: str) -> str | None:
    """Mill path constant bound to ``MILL`` / ``GEN`` / ``NTP_GEN`` / ``OUT``."""

    tree = parse_tree(source)
    for node in getattr(tree, "body", ()):
        assigned, value = assignment_of(node)
        if assigned != name or value is None:
            continue
        for candidate in ast.walk(value):
            path = joined_path_constant(candidate)
            if path is None:
                continue
            mill = experiments_mill_path(path)
            if mill is not None:
                return mill
    return None


def extract_write_wave_mill(source: str) -> str | None:
    """First ``write_wave(N, …)`` / ``g.write_wave(N, …)`` → ``llllN`` mill path."""

    tree = parse_tree(source)
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not node.args:
            continue
        if not _is_write_wave(node.func):
            continue
        wave = literal_value(node.args[0])
        if isinstance(wave, int):
            return f"experiments/ntp-mill-unique-llll{wave}.py"
    return None


def _is_write_wave(func: ast.AST) -> bool:
    """``write_wave`` called bare or as an attribute (``g.write_wave``)."""

    if isinstance(func, ast.Name):
        return func.id == "write_wave"
    if isinstance(func, ast.Attribute):
        return func.attr == "write_wave"
    return False


def extract_first_wave_table_mill(source: str) -> str | None:
    """First ``S19 = […]`` table → ``experiments/ntp-mill-unique-llll19.py``."""

    tree = parse_tree(source)
    for node in getattr(tree, "body", ()):
        for name in assignment_names(node):
            match = _WAVE_TABLE_RE.fullmatch(name)
            if match is not None:
                return f"experiments/ntp-mill-unique-llll{match.group(1)}.py"
    return None


def extract_chain_loop_range(source: str) -> tuple[int, int] | None:
    """``for n in range(15, 27):`` → ``(15, 26)`` inclusive."""

    tree = parse_tree(source)
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or call_name(node) != "range":
            continue
        args = [literal_value(arg) for arg in node.args]
        if len(args) == 2 and all(isinstance(item, int) for item in args):
            start, stop = args
            return start, stop - 1
    return None
