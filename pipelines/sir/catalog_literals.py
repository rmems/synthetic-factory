"""Literal-only value decoding shared by SIR binding and extraction."""

from __future__ import annotations

import ast
from collections.abc import Iterable, Mapping
from typing import Any

if __name__.startswith("pipelines."):
    from ..oracle_grounded.import_twins import bind_import_twin
else:
    from oracle_grounded.import_twins import bind_import_twin

UNSET = object()


def source_payload(source: str, *, path: str) -> bytes:
    """Bind parsing and hashing to text whose encoding cannot be overridden."""
    if type(source) is not str or type(path) is not str:
        raise ValueError("catalog source and path must be plain strings")
    return source.encode("utf-8")


def validated_tree(source):
    """Check compiler constraints, then discard code without executing it."""
    try:
        tree = ast.parse(source, filename="<catalog-source>")
        compile(tree, "<catalog-source>", "exec", dont_inherit=True)
    except (SyntaxError, RecursionError) as exc:
        raise ValueError(f"catalog source is not valid Python: {exc}") from exc
    return tree


def literal_value(node: ast.AST | None, env: Mapping[str, Any] | None = None) -> Any:
    """Resolve constants, names, and literal containers; else ``UNSET``."""

    bound = env or {}
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Name):
        return bound.get(node.id, UNSET)
    if isinstance(node, ast.UnaryOp):
        return _negative_number(node, bound)
    return _container_value(node, bound)


def _negative_number(node: ast.UnaryOp, bound: Mapping[str, Any]) -> Any:
    if not isinstance(node.op, ast.USub):
        return UNSET
    inner = literal_value(node.operand, bound)
    return -inner if isinstance(inner, (int, float)) else UNSET


def _container_value(node: ast.AST | None, bound: Mapping[str, Any]) -> Any:
    constructors = {ast.Tuple: tuple, ast.List: list, ast.Set: set}
    constructor = constructors.get(type(node))
    if constructor is not None:
        return _sequence(node.elts, bound, constructor)
    if isinstance(node, ast.Dict):
        return _mapping(node, bound)
    return UNSET


def _sequence(elts: Iterable[ast.AST | None], env: Mapping[str, Any], ctor):
    values: list[Any] = []
    for elt in elts:
        item = literal_value(elt, env)
        if item is UNSET:
            return UNSET
        values.append(item)
    return ctor(values)


def _mapping(node: ast.Dict, env: Mapping[str, Any]) -> Any:
    out: dict[Any, Any] = {}
    for nodes in zip(node.keys, node.values, strict=True):
        pair = _sequence(nodes, env, tuple)
        if pair is UNSET:
            return UNSET
        key, value = pair
        out[key] = value
    return out


def module_docstring(tree: ast.AST) -> str:
    if not isinstance(tree, ast.Module):
        return ""
    return ast.get_docstring(tree, clean=False) or ""

bind_import_twin(__name__)
