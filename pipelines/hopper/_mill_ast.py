"""AST readers shared by the hopper mill catalogs.

Mill scripts are read only as text through ``ast.parse``; nothing here
imports or executes them.
"""

from __future__ import annotations

import ast
from collections.abc import Iterator
from typing import Any

from ._contract import FINDING_CATALOG_FIELD_INVALID, bind_import_twin, refuse

MODULE_CONSTANT_NAMES = frozenset({"FACTORY", "GEN", "CATALOG_FIRST"})

__all__ = ["MODULE_CONSTANT_NAMES", "literal_str", "module_constants"]


def literal_str(node: ast.AST, where: str) -> str:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    refuse(FINDING_CATALOG_FIELD_INVALID, f"{where} must be a string literal")


def _is_scalar(value: Any) -> bool:
    """A str or int value; ``bool`` is an int subclass and is not a scalar here."""

    return isinstance(value, (str, int)) and not isinstance(value, bool)


def _named_targets(node: ast.Assign) -> Iterator[str]:
    return (target.id for target in node.targets if isinstance(target, ast.Name))


def _constant_bindings(node: ast.stmt) -> list[tuple[str, Any]]:
    """``(name, value)`` for each constant name ``node`` binds to a str or int literal."""

    if not isinstance(node, ast.Assign):
        return []
    value = node.value
    if not isinstance(value, ast.Constant) or not _is_scalar(value.value):
        return []
    return [(name, value.value) for name in _named_targets(node) if name in MODULE_CONSTANT_NAMES]


def module_constants(tree: ast.Module) -> dict[str, Any]:
    """Top-level ``FACTORY`` / ``GEN`` / ``CATALOG_FIRST`` str or int literals."""

    found: dict[str, Any] = {}
    for node in tree.body:
        found.update(_constant_bindings(node))
    return found


bind_import_twin(__name__)
