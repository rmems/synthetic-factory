#!/usr/bin/env python3
"""AST-extract mac catalog rows. Never exec mill publishers.

``plants_from_source`` walks leftover mill text for:

* ``P(slug, goal, ...)`` plants (r3034 / leftover-r3038 / leftover-r3117)
* ``A(slug, process, metric, ..., spike, ...)`` plants (r3205+)
* ``SCEN = [dict(slug=..., goal=...), ...]`` leftover3 software-coord rows

``ast.parse`` is the only interpreter step.
"""

from __future__ import annotations

import ast
from typing import Any

from ._contract import (
    FINDING_AST_NOT_A_PLANT,
    FINDING_FIELD_INVALID,
    FINDING_SOURCE_NOT_PARSEABLE,
    bind_import_twin,
    refuse,
    refuse_when,
    shown,
)

SHAPE_P = "plant-p"
SHAPE_A = "plant-a"
SHAPE_SCEN = "leftover3-scen"

__all__ = [
    "SHAPE_A",
    "SHAPE_P",
    "SHAPE_SCEN",
    "plants_from_source",
]


def _const(node: ast.AST, where: str) -> Any:
    refuse_when(
        not isinstance(node, ast.Constant),
        FINDING_AST_NOT_A_PLANT,
        f"{where} is not a constant ({type(node).__name__})",
    )
    return node.value


def _require_str(value: Any, where: str) -> str:
    refuse_when(
        not isinstance(value, str) or not value,
        FINDING_FIELD_INVALID,
        f"{where} must be a non-empty string, got {shown(value)}",
    )
    return value


def _p_row(node: ast.Call, where: str) -> dict[str, Any] | None:
    if len(node.args) < 2:
        return None
    if not isinstance(node.args[0], ast.Constant) or not isinstance(node.args[1], ast.Constant):
        return None
    return {
        "shape": SHAPE_P,
        "slug": _require_str(_const(node.args[0], f"{where}.slug"), f"{where}.slug"),
        "goal": _require_str(_const(node.args[1], f"{where}.goal"), f"{where}.goal"),
    }


def _a_row(node: ast.Call, where: str) -> dict[str, Any] | None:
    if len(node.args) < 7:
        return None
    needed = (node.args[0], node.args[1], node.args[2], node.args[6])
    if any(not isinstance(arg, ast.Constant) for arg in needed):
        return None
    return {
        "shape": SHAPE_A,
        "slug": _require_str(_const(node.args[0], f"{where}.slug"), f"{where}.slug"),
        "process": _require_str(_const(node.args[1], f"{where}.process"), f"{where}.process"),
        "metric": _require_str(_const(node.args[2], f"{where}.metric"), f"{where}.metric"),
        "spike": _require_str(_const(node.args[6], f"{where}.spike"), f"{where}.spike"),
    }


def _scen_row(node: ast.Call, where: str) -> dict[str, Any] | None:
    if not isinstance(node.func, ast.Name) or node.func.id != "dict":
        return None
    values: dict[str, Any] = {}
    for keyword in node.keywords:
        if keyword.arg in {"slug", "goal"} and isinstance(keyword.value, ast.Constant):
            values[keyword.arg] = keyword.value.value
    if "slug" not in values or "goal" not in values:
        return None
    return {
        "shape": SHAPE_SCEN,
        "slug": _require_str(values["slug"], f"{where}.slug"),
        "goal": _require_str(values["goal"], f"{where}.goal"),
    }


def _assigned_name(node: ast.AST) -> tuple[str, ast.AST] | None:
    if isinstance(node, ast.Assign) and len(node.targets) == 1:
        target = node.targets[0]
        if isinstance(target, ast.Name):
            return target.id, node.value
    if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
        if node.value is not None:
            return node.target.id, node.value
    return None


class _CatalogVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.p_rows: list[dict[str, Any]] = []
        self.a_rows: list[dict[str, Any]] = []

    def visit_Call(self, node: ast.Call) -> None:
        if isinstance(node.func, ast.Name) and node.func.id == "P":
            row = _p_row(node, f"P() at line {node.lineno}")
            if row is not None:
                self.p_rows.append(row)
        elif isinstance(node.func, ast.Name) and node.func.id == "A":
            row = _a_row(node, f"A() at line {node.lineno}")
            if row is not None:
                self.a_rows.append(row)
        self.generic_visit(node)


def plants_from_source(text: str) -> tuple[dict[str, Any], ...]:
    """AST-extract catalog identity rows from mill source text. Never exec."""

    try:
        tree = ast.parse(text)
    except SyntaxError as exc:
        refuse(FINDING_SOURCE_NOT_PARSEABLE, f"mill source is not parseable: {exc}")
    if not isinstance(tree, ast.Module):
        refuse(FINDING_SOURCE_NOT_PARSEABLE, "mill source is not a module")

    scen: list[dict[str, Any]] = []
    for node in tree.body:
        bound = _assigned_name(node)
        if bound is None or bound[0] != "SCEN" or not isinstance(bound[1], ast.List):
            continue
        for index, elt in enumerate(bound[1].elts):
            if isinstance(elt, ast.Call):
                row = _scen_row(elt, f"SCEN[{index}]")
                if row is not None:
                    scen.append(row)
    if scen:
        return tuple(scen)

    visitor = _CatalogVisitor()
    visitor.visit(tree)
    if visitor.a_rows:
        return tuple(visitor.a_rows)
    if visitor.p_rows:
        return tuple(visitor.p_rows)
    refuse(FINDING_AST_NOT_A_PLANT, "source has no P(), A(), or SCEN catalog")


bind_import_twin(__name__)
