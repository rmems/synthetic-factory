#!/usr/bin/env python3
"""Call and subscript helpers for the LHC AST extract."""

from __future__ import annotations

import ast
from collections.abc import Mapping
from typing import Any

from .catalog_ast_literals import UNSET, literal_value


def _named_call(node: ast.AST) -> ast.Call | None:
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
        return node
    return None


def _call_func_id(call: ast.Call) -> str | None:
    if isinstance(call.func, ast.Name):
        return call.func.id
    return None


def _keyword_name(keyword: ast.keyword) -> str | None:
    return keyword.arg


def call_name(node: ast.AST) -> str | None:
    call = _named_call(node)
    if call is None:
        return None
    return _call_func_id(call)


def call_kwargs(node: ast.AST, env: Mapping[str, Any] | None = None) -> dict[str, Any] | None:
    """Keyword arguments of a ``Name(...)`` call when every value is a literal."""

    call = _named_call(node)
    if call is None:
        return None
    if any(_keyword_name(keyword) is None for keyword in call.keywords):
        return None
    out: dict[str, Any] = {}
    for keyword in call.keywords:
        name = _keyword_name(keyword)
        value = literal_value(keyword.value, env)
        if name is None or value is UNSET:
            return None
        out[name] = value
    return out


def call_positional_literals(
    node: ast.AST, env: Mapping[str, Any] | None = None
) -> list[Any] | None:
    """Positional arguments of a ``Name(...)`` call when every value is a literal."""

    call = _named_call(node)
    if call is None:
        return None
    values: list[Any] = []
    for arg in call.args:
        value = literal_value(arg, env)
        if value is UNSET:
            return None
        values.append(value)
    return values


def name_id(node: ast.AST) -> str | None:
    return node.id if isinstance(node, ast.Name) else None


def _const_str(node: ast.AST | None) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _const_value(node: ast.AST | None) -> Any:
    if isinstance(node, ast.Constant):
        return node.value
    return UNSET


def constant_fields(node: ast.AST) -> dict[str, Any] | None:
    """Return constant string/number/bool fields from a dict; skip non-literals."""

    if not isinstance(node, ast.Dict):
        return None
    out: dict[str, Any] = {}
    for key_node, value_node in zip(node.keys, node.values, strict=True):
        key = _const_str(key_node)
        value = _const_value(value_node)
        if key is None or value is UNSET:
            continue
        out[key] = value
    return out


def _plants_name(node: ast.AST) -> bool:
    return isinstance(node, ast.Name) and node.id == "PLANTS"


def plants_subscript_key(node: ast.AST) -> str | None:
    """``PLANTS['poetry']`` → ``'poetry'``."""

    if not isinstance(node, ast.Subscript):
        return None
    if not _plants_name(node.value):
        return None
    return _const_str(node.slice)
