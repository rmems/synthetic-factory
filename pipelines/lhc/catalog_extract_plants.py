#!/usr/bin/env python3
"""Plant-table and expand-wrapper identity for the LHC AST extract."""

from __future__ import annotations

import ast
from collections.abc import Mapping
from typing import Any

from .catalog_ast import (
    assignment_of,
    call_kwargs,
    call_name,
    call_positional_literals,
    constant_fields,
    literal_value,
    plants_subscript_key,
)


def plants_context(
    tree: ast.AST,
) -> tuple[dict[str, dict[str, Any]], str | None, dict[str, str], dict[str, dict[str, Any]]]:
    """``PLANTS`` table, constructor name, wrapper keys, and expand() plants."""

    plants, ctor = _plants_table(tree)
    return plants, ctor, _wrapper_keys(tree), _expand_function_plants(tree)


def plant_count(
    plants: Mapping[str, Mapping[str, Any]], expand_plants: Mapping[str, Any]
) -> int:
    if plants:
        return len(plants)
    return len(expand_plants)


def _plants_from_dict(value: ast.Dict) -> tuple[dict[str, dict[str, Any]], str | None]:
    table: dict[str, dict[str, Any]] = {}
    ctor: str | None = None
    for key_node, value_node in zip(value.keys, value.values, strict=True):
        key = literal_value(key_node)
        identity = _plant_ctor_identity(value_node)
        if not isinstance(key, str) or identity is None:
            return {}, None
        table[key] = identity
        ctor = call_name(value_node)
    return table, ctor


def _plants_table(tree: ast.AST) -> tuple[dict[str, dict[str, Any]], str | None]:
    for node in getattr(tree, "body", ()):
        name, value = assignment_of(node)
        if name == "PLANTS" and isinstance(value, ast.Dict):
            return _plants_from_dict(value)
    return {}, None


def _p_identity(node: ast.AST) -> dict[str, Any] | None:
    kwargs = call_kwargs(node)
    args = call_positional_literals(node)
    missing = kwargs is None or "slug" not in kwargs or "plant" not in kwargs
    if missing:
        return None
    ok = args[0] if args else kwargs.get("ok")
    return {"slug": kwargs["slug"], "plant": kwargs["plant"], "ok": ok, "key": None}


def _mk_identity(node: ast.AST) -> dict[str, Any] | None:
    args = call_positional_literals(node)
    if args is None or len(args) < 3:
        return None
    return {"ok": args[0], "slug": args[1], "plant": args[2], "key": None}


def _plant_ctor_identity(node: ast.AST) -> dict[str, Any] | None:
    ctor = call_name(node)
    if ctor == "P":
        return _p_identity(node)
    if ctor == "mk":
        return _mk_identity(node)
    return None


def _wrapper_keys(tree: ast.AST) -> dict[str, str]:
    """``def poetry_extras(rnd): return plant_from(rnd, PLANTS['poetry'])``."""

    wrappers: dict[str, str] = {}
    for node in getattr(tree, "body", ()):
        if not isinstance(node, ast.FunctionDef):
            continue
        key = _first_plants_key(node)
        if key is not None:
            wrappers[node.name] = key
    return wrappers


def _first_plants_key(fn: ast.FunctionDef) -> str | None:
    for child in ast.walk(fn):
        key = plants_subscript_key(child)
        if key is not None:
            return key
    return None


def _expand_function_plants(tree: ast.AST) -> dict[str, dict[str, Any]]:
    """``def pnpm_peer(rnd): return expand(rnd, {'slug': ..., 'plant': ...})``."""

    plants: dict[str, dict[str, Any]] = {}
    for node in getattr(tree, "body", ()):
        if not isinstance(node, ast.FunctionDef):
            continue
        identity = _expand_identity(node)
        if identity is not None:
            plants[node.name] = identity
    return plants


def _expand_fields(child: ast.AST) -> dict[str, Any] | None:
    if call_name(child) != "expand" or not isinstance(child, ast.Call):
        return None
    if len(child.args) < 2:
        return None
    fields = constant_fields(child.args[1])
    if fields is None:
        return None
    if "slug" not in fields or "plant" not in fields:
        return None
    return fields


def _expand_identity(fn: ast.FunctionDef) -> dict[str, Any] | None:
    for child in ast.walk(fn):
        fields = _expand_fields(child)
        if fields is None:
            continue
        return {
            "slug": fields["slug"],
            "plant": fields["plant"],
            "ok": fields.get("success"),
            "key": fn.name,
        }
    return None
