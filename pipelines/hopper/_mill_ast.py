"""AST readers shared by the hopper mill catalogs.

Mill scripts are read only as text through ``ast.parse``; nothing here
imports or executes them.
"""

from __future__ import annotations

import ast
from collections.abc import Iterator
from typing import Any

from ._contract import FINDING_CATALOG_FIELD_INVALID, bind_import_twin, refuse_when

MODULE_CONSTANT_NAMES = frozenset({"FACTORY", "GEN", "CATALOG_FIRST"})

__all__ = ["MODULE_CONSTANT_NAMES", "literal_str", "module_constants"]


def literal_str(node: ast.AST, where: str) -> str:
    refuse_when(
        not isinstance(node, ast.Constant) or not isinstance(node.value, str),
        FINDING_CATALOG_FIELD_INVALID,
        f"{where} must be a string literal",
    )
    assert isinstance(node, ast.Constant)
    return node.value


def _is_scalar(value: Any) -> bool:
    """A str or int value; ``bool`` is an int subclass and is not a scalar here."""

    return isinstance(value, (str, int)) and not isinstance(value, bool)


def _named_targets(node: ast.Assign) -> Iterator[str]:
    return (target.id for target in node.targets if isinstance(target, ast.Name))


def module_constants(tree: ast.Module) -> dict[str, Any]:
    """Top-level ``FACTORY`` / ``GEN`` / ``CATALOG_FIRST`` str or int literals."""

    found: dict[str, Any] = {}
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        value = node.value
        if not isinstance(value, ast.Constant) or not _is_scalar(value.value):
            continue
        for name in _named_targets(node):
            if name in MODULE_CONSTANT_NAMES:
                found[name] = value.value
    return found


bind_import_twin(__name__)
