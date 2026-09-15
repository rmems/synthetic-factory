#!/usr/bin/env python3
"""AST-extract leftover leftover leftover leftover leftover leftover pair rows.

``plants_from_source`` walks leftover mill text for
``PAIRS = [dict(slug=..., fail=..., ...), ...]``. Identity keys stay;
payload fields (``doc``, ``doc2``, ``stack``, ``test_ok``, ``test_fail``)
are dropped so the catalog stays slim.

``ast.parse`` is the only interpreter step. ``exec`` / ``eval`` /
``compile`` / ``SourceFileLoader`` are not used.
"""

from __future__ import annotations

import ast
from typing import Any

from ._contract import (
    FINDING_AST_NOT_A_PLANT,
    FINDING_FIELD_INVALID,
    FINDING_FIELD_MISSING,
    FINDING_SOURCE_NOT_PARSEABLE,
    IDENTITY_KEYS,
    bind_import_twin,
    refuse,
    refuse_when,
    shown,
)

SHAPE_PAIRS = "pairs-dict"

__all__ = [
    "SHAPE_PAIRS",
    "pairs_from_source",
    "plants_from_source",
]


def _const_eval(node: ast.AST, where: str) -> Any:
    """Literal values, containers, and ``str.replace`` on constants. Never exec."""

    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        return -_const_eval(node.operand, where)
    if isinstance(node, ast.List):
        return [_const_eval(item, f"{where}[]") for item in node.elts]
    if isinstance(node, ast.Tuple):
        return tuple(_const_eval(item, f"{where}()") for item in node.elts)
    if isinstance(node, ast.Dict):
        refuse_when(
            any(key is None for key in node.keys),
            FINDING_AST_NOT_A_PLANT,
            f"{where} uses dict unpacking",
        )
        return {
            _const_eval(key, f"{where}.key"): _const_eval(value, f"{where}.value")
            for key, value in zip(node.keys, node.values, strict=True)
        }
    if isinstance(node, ast.Call):
        func = node.func
        if (
            isinstance(func, ast.Name)
            and func.id == "dict"
            and not node.args
            and all(keyword.arg is not None for keyword in node.keywords)
        ):
            return {
                keyword.arg: _const_eval(keyword.value, f"{where}.{keyword.arg}")
                for keyword in node.keywords
            }
        if (
            isinstance(func, ast.Attribute)
            and func.attr == "replace"
            and not node.keywords
            and len(node.args) == 2
        ):
            base = _const_eval(func.value, f"{where}.replace")
            old = _const_eval(node.args[0], f"{where}.replace.old")
            new = _const_eval(node.args[1], f"{where}.replace.new")
            refuse_when(
                not isinstance(base, str) or not isinstance(old, str) or not isinstance(new, str),
                FINDING_FIELD_INVALID,
                f"{where} replace() is not all strings",
            )
            return base.replace(old, new)
        refuse(
            FINDING_AST_NOT_A_PLANT,
            f"{where} uses a non-literal call ({type(node).__name__})",
        )
    refuse(
        FINDING_AST_NOT_A_PLANT,
        f"{where} is not a constant ({type(node).__name__})",
    )


def _require_str(value: Any, where: str) -> str:
    refuse_when(
        not isinstance(value, str) or not value,
        FINDING_FIELD_INVALID,
        f"{where} must be a non-empty string, got {shown(value)}",
    )
    return value


def _pair_from_mapping(raw: dict[str, Any], where: str) -> dict[str, str]:
    missing = [key for key in IDENTITY_KEYS if key not in raw]
    if missing:
        refuse(FINDING_FIELD_MISSING, f"{where} missing {missing[0]}")
    return {key: _require_str(raw[key], f"{where}.{key}") for key in IDENTITY_KEYS}


def _pair_from_dict_call(node: ast.Call, where: str) -> dict[str, str]:
    refuse_when(
        not isinstance(node.func, ast.Name) or node.func.id != "dict" or node.args,
        FINDING_AST_NOT_A_PLANT,
        f"{where} is not dict()",
    )
    refuse_when(
        any(keyword.arg is None for keyword in node.keywords),
        FINDING_AST_NOT_A_PLANT,
        f"{where} uses starred dict()",
    )
    seen: set[str] = set()
    raw: dict[str, Any] = {}
    for keyword in node.keywords:
        assert keyword.arg is not None
        refuse_when(
            keyword.arg in seen,
            FINDING_FIELD_INVALID,
            f"{where} duplicate key {keyword.arg!r}",
        )
        seen.add(keyword.arg)
        raw[keyword.arg] = _const_eval(keyword.value, f"{where}.{keyword.arg}")
    return _pair_from_mapping(raw, where)


def pairs_from_source(source: str) -> tuple[dict[str, str], ...]:
    """Return identity-only leftover leftover leftover leftover leftover leftover pairs."""

    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        refuse(FINDING_SOURCE_NOT_PARSEABLE, f"mill source is not parseable: {exc}")
    if not isinstance(tree, ast.Module):
        refuse(FINDING_SOURCE_NOT_PARSEABLE, "mill source is not a module")
    for node in tree.body:
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target = node.targets[0]
        if not isinstance(target, ast.Name) or target.id != "PAIRS":
            continue
        refuse_when(
            not isinstance(node.value, ast.List),
            FINDING_AST_NOT_A_PLANT,
            "PAIRS is not a list",
        )
        rows: list[dict[str, str]] = []
        for index, elt in enumerate(node.value.elts):
            refuse_when(
                not isinstance(elt, ast.Call),
                FINDING_AST_NOT_A_PLANT,
                f"PAIRS[{index}] is not dict()",
            )
            rows.append(_pair_from_dict_call(elt, f"PAIRS[{index}]"))
        refuse_when(not rows, FINDING_AST_NOT_A_PLANT, "PAIRS is empty")
        return tuple(rows)
    refuse(FINDING_AST_NOT_A_PLANT, "PAIRS assignment not found")


def plants_from_source(source: str) -> tuple[dict[str, str], ...]:
    """Alias used by the catalog-check / extract CLI (pairs, not plants)."""

    return pairs_from_source(source)


bind_import_twin(__name__)
