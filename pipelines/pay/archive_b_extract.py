#!/usr/bin/env python3
"""AST-extract Archive B pair bodies from ``mill_plants.py``. Never exec."""

from __future__ import annotations

import ast
from collections.abc import Mapping
from typing import Any

from ._contract import (
    FINDING_AST_NOT_A_PAIR,
    FINDING_PAIR_FIELD_MISSING,
    FINDING_SOURCE_NOT_PARSEABLE,
    SOURCE_PATH,
    bind_import_twin,
    refuse,
    refuse_when,
)

SIDE_REQUIRED = ("slug",)

__all__ = ["pairs_from_source"]


def _const_eval(node: ast.AST) -> Any:
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        return -_const_eval(node.operand)
    if isinstance(node, ast.JoinedStr):
        parts: list[str] = []
        for piece in node.values:
            if isinstance(piece, ast.Constant):
                parts.append(str(piece.value))
            elif isinstance(piece, ast.FormattedValue):
                parts.append(str(_const_eval(piece.value)))
        return "".join(parts)
    if isinstance(node, ast.List):
        return [_const_eval(item) for item in node.elts]
    if isinstance(node, ast.Tuple):
        return tuple(_const_eval(item) for item in node.elts)
    if isinstance(node, ast.Dict):
        refuse_when(
            any(key is None for key in node.keys),
            FINDING_AST_NOT_A_PAIR,
            f"{SOURCE_PATH} uses dict unpacking",
        )
        return {_const_eval(key): _const_eval(value) for key, value in zip(node.keys, node.values, strict=True)}
    if isinstance(node, ast.Call):
        func = node.func
        if (
            isinstance(func, ast.Name)
            and func.id in {"dict", "_ok", "_fail"}
            and not node.args
            and all(keyword.arg is not None for keyword in node.keywords)
        ):
            return {keyword.arg: _const_eval(keyword.value) for keyword in node.keywords}
    refuse(FINDING_AST_NOT_A_PAIR, f"{SOURCE_PATH} has non-literal plant fragment {ast.dump(node)[:80]}")


def _validate_side(
    side: Mapping[str, Any], *, role: str, index: int, source: str = SOURCE_PATH
) -> None:
    missing = [key for key in SIDE_REQUIRED if key not in side]
    if missing:
        refuse(
            FINDING_PAIR_FIELD_MISSING,
            f"{source} pair[{index}].{role} missing {missing[0]}",
        )


def pairs_from_source(text: str, *, source: str = SOURCE_PATH) -> tuple[dict[str, Any], ...]:
    """Return ``({"ok": ..., "fail": ...}, ...)`` from ``PAIRS.append`` calls."""

    try:
        tree = ast.parse(text, filename=source)
    except SyntaxError as exc:
        refuse(FINDING_SOURCE_NOT_PARSEABLE, f"{source} does not parse: {exc}")
    rows: list[dict[str, Any]] = []
    for node in tree.body:
        if not isinstance(node, ast.Expr) or not isinstance(node.value, ast.Call):
            continue
        call = node.value
        if not (isinstance(call.func, ast.Attribute) and call.func.attr == "append"):
            continue
        if not (isinstance(call.func.value, ast.Name) and call.func.value.id == "PAIRS"):
            continue
        refuse_when(
            len(call.args) != 1,
            FINDING_AST_NOT_A_PAIR,
            f"{source} PAIRS.append must take one tuple argument",
        )
        pair = _const_eval(call.args[0])
        refuse_when(
            not isinstance(pair, tuple) or len(pair) != 2,
            FINDING_AST_NOT_A_PAIR,
            f"{source} PAIRS.append expects (ok, fail) tuple",
        )
        ok, fail = pair
        refuse_when(
            not isinstance(ok, dict) or not isinstance(fail, dict),
            FINDING_AST_NOT_A_PAIR,
            f"{source} PAIRS.append sides must be dicts",
        )
        _validate_side(ok, role="ok", index=len(rows), source=source)
        _validate_side(fail, role="fail", index=len(rows), source=source)
        rows.append({"ok": ok, "fail": fail})
    refuse_when(not rows, FINDING_SOURCE_NOT_PARSEABLE, f"{source} has no PAIRS.append rows")
    return tuple(rows)


if __package__:
    bind_import_twin(__name__)
