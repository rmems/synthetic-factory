#!/usr/bin/env python3
"""K8S / CLI_SPEC catalog table extraction for :mod:`iac.catalog_extract`."""

from __future__ import annotations

import ast
from collections.abc import Mapping
from typing import Any

from .catalog_ast import assignment_of, call_kwargs, call_name, literal_value
from .catalog_extract import SHAPE_K8S_CLI_SPEC, SHAPE_K8S_FILE, _rows_record


def _literal_nonempty_list(value: ast.AST) -> list[Any] | None:
    resolved = literal_value(value)
    if isinstance(resolved, list) and resolved:
        return resolved
    return None


def _file_pair_row(kwargs: Mapping[str, Any]) -> dict[str, Any]:
    slug = kwargs["s"]
    gem = kwargs.get("g")
    return {
        "success_slug": slug,
        "fail_slug": slug.replace("-vs-old", "-old-leftover"),
        "success_plant": f"{gem}-prod" if isinstance(gem, str) else None,
        "fail_plant": f"{gem}-jobs" if isinstance(gem, str) else None,
        "fail_handoff": True,
    }


def _file_pair_table(value: ast.List) -> list[dict[str, Any]] | None:
    if not value.elts or not all(call_name(elt) == "file_pair" for elt in value.elts):
        return None
    rows: list[dict[str, Any]] = []
    for elt in value.elts:
        kwargs = call_kwargs(elt)
        if kwargs is None or "s" not in kwargs:
            return None
        rows.append(_file_pair_row(kwargs))
    return rows


def _assignment_values(tree: ast.AST) -> dict[str, ast.AST]:
    values: dict[str, ast.AST] = {}
    for node in getattr(tree, "body", ()):
        name, value = assignment_of(node)
        if name is not None and value is not None:
            values[name] = value
    return values


def _k8s_identity(row: Any) -> dict[str, Any]:
    if not isinstance(row, (tuple, list)) or len(row) < 2:
        return {
            "success_slug": None,
            "fail_slug": None,
            "success_plant": None,
            "fail_plant": None,
            "fail_handoff": True,
        }
    slug = row[0]
    gem = row[1]
    return {
        "success_slug": slug,
        "fail_slug": slug.replace("-vs-old", "-old-leftover") if isinstance(slug, str) else None,
        "success_plant": f"{gem}-prod" if isinstance(gem, str) else None,
        "fail_plant": f"{gem}-jobs" if isinstance(gem, str) else None,
        "fail_handoff": True,
    }


def _cli_spec_identity(row: Any) -> dict[str, Any]:
    if not isinstance(row, dict):
        return {
            "success_slug": None,
            "fail_slug": None,
            "success_plant": None,
            "fail_plant": None,
            "fail_handoff": True,
        }
    slug = row.get("s")
    gem = row.get("g")
    return {
        "success_slug": slug,
        "fail_slug": slug.replace("-vs-old", "-old-leftover") if isinstance(slug, str) else None,
        "success_plant": f"{gem}-prod" if isinstance(gem, str) else None,
        "fail_plant": f"{gem}-jobs" if isinstance(gem, str) else None,
        "fail_handoff": True,
    }


def _k8s_cli_bindings(
    tree: ast.AST,
) -> tuple[list[Any], list[Any] | None, list[dict[str, Any]] | None] | None:
    values = _assignment_values(tree)
    if "K8S" not in values:
        return None
    k8s = _literal_nonempty_list(values["K8S"])
    if k8s is None:
        return None
    cli_spec: list[Any] | None = None
    if "CLI_SPEC" in values:
        cli_spec = _literal_nonempty_list(values["CLI_SPEC"])
        if cli_spec is None:
            return None
    cli_rows: list[dict[str, Any]] | None = None
    cli_value = values.get("CLI")
    if isinstance(cli_value, ast.List):
        cli_rows = _file_pair_table(cli_value)
    return k8s, cli_spec, cli_rows


def _k8s_table_record(
    shape: str, k8s: list[Any], extra: list[dict[str, Any]]
) -> dict[str, Any] | None:
    rows = [_k8s_identity(row) for row in k8s] + extra
    return _rows_record(shape, rows)


def k8s_cli_tables(tree: ast.AST) -> dict[str, Any] | None:
    bindings = _k8s_cli_bindings(tree)
    if bindings is None:
        return None
    k8s, cli_spec, cli_rows = bindings
    if cli_spec is not None:
        extra = [_cli_spec_identity(row) for row in cli_spec]
        return _k8s_table_record(SHAPE_K8S_CLI_SPEC, k8s, extra)
    if cli_rows is not None:
        return _k8s_table_record(SHAPE_K8S_FILE, k8s, cli_rows)
    return None
