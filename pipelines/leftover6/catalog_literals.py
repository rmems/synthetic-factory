#!/usr/bin/env python3
"""Literal AST values retain the syntax of reviewed catalog constructors."""

from __future__ import annotations

import ast
from collections.abc import Mapping
from typing import Any

from ._contract import bind_import_twin

UNSET = object()


class _LiteralMapping(dict):
    """Literal fields with their originating syntax retained for shape checks."""

    def __init__(self, shape, values=()):
        super().__init__(values)
        self.shape = shape


SBOX_PLANT_FIELDS = (
    "family",
    "dump",
    "miss_dump",
    "secret",
    "pin",
    "pin_path",
    "pin_needle",
    "grep_hit",
    "distinct",
    "ext",
    "miss_ext",
    "live_bin",
    "inc",
    "over_slug",
    "miss_slug",
    "proc",
    "allow",
    "rotate",
)


def literal_value(node: ast.AST, env: Mapping[str, Any] | None = None) -> Any:
    bound = env or {}
    value = _atomic_literal(node, bound)
    if value is not UNSET:
        return value
    return _compound_literal(node, bound)


def _atomic_literal(node: ast.AST, env: Mapping[str, Any]) -> Any:
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Name):
        return env.get(node.id, UNSET)
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        inner = literal_value(node.operand, env)
        return -inner if isinstance(inner, (int, float)) else UNSET
    return UNSET


def _compound_literal(node: ast.AST, env: Mapping[str, Any]) -> Any:
    if isinstance(node, (ast.Tuple, ast.List)):
        constructor = tuple if isinstance(node, ast.Tuple) else list
        return _sequence(node.elts, env, constructor)
    if isinstance(node, ast.Dict):
        return _mapping(node, env)
    if isinstance(node, ast.Call):
        return _literal_call(node, env)
    return UNSET


def _sequence(elts: list[ast.AST], env: Mapping[str, Any], ctor):
    values: list[Any] = []
    for elt in elts:
        item = literal_value(elt, env)
        if item is UNSET:
            return UNSET
        values.append(item)
    return ctor(values)


def _mapping(node: ast.Dict, env: Mapping[str, Any]) -> Any:
    out: dict[Any, Any] = _LiteralMapping("literal-dicts")
    for key_node, value_node in zip(node.keys, node.values, strict=True):
        if key_node is None:
            return UNSET
        key = literal_value(key_node, env)
        value = literal_value(value_node, env)
        if key is UNSET or value is UNSET:
            return UNSET
        try:
            if key in out:
                return UNSET
            out[key] = value
        except TypeError:
            return UNSET
    return out


def _literal_call(node: ast.Call, env: Mapping[str, Any]) -> Any:
    if not isinstance(node.func, ast.Name):
        return UNSET
    parsers = {"dict": _dict_call, "_row": _row_call}
    parser = parsers.get(node.func.id)
    return UNSET if parser is None else parser(node, env)


def _dict_call(node: ast.Call, env: Mapping[str, Any]) -> Any:
    if node.args:
        return UNSET
    values: dict[str, Any] = _LiteralMapping("dict-kwargs")
    for keyword in node.keywords:
        name = keyword.arg
        if name is None or name in values:
            return UNSET
        value = literal_value(keyword.value, env)
        if value is UNSET:
            return UNSET
        values[name] = value
    return values


def _row_call(node: ast.Call, env: Mapping[str, Any]) -> Any:
    if node.keywords or len(node.args) != len(SBOX_PLANT_FIELDS):
        return UNSET
    values = _sequence(node.args, env, list)
    return UNSET if values is UNSET else _LiteralMapping("row-ctor", zip(SBOX_PLANT_FIELDS, values, strict=True))


bind_import_twin(__name__)
