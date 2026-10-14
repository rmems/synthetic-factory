"""Constant-source checks shared by the plant catalogs.

The generate-shape catalogs used to copy these blocks. One copy keeps the
refusal text and the returned set identical.
"""

from __future__ import annotations

import ast
from collections.abc import Callable
from pathlib import Path
from typing import Any

if __name__.startswith("pipelines."):
    from ..oracle_grounded.import_twins import bind_import_twin
else:
    from oracle_grounded.import_twins import bind_import_twin

_LoadJson = Callable[[str], Any]
_Raise = Callable[..., Any]


def registry_factory_ids(
    repo_root: Callable[[], Path],
    load_strict_json: _LoadJson,
    refuse: Callable[[str], _Raise],
) -> set[str]:
    """Path ids from ``config/FACTORY-REGISTRY.json``.

    A row that is not a dict, or a ``path_id`` that is not a str, is skipped.
    ``refuse(message)`` must return the refusal exception for an unreadable
    registry or a ``factories`` value that is not a list.
    """

    path = repo_root() / "config" / "FACTORY-REGISTRY.json"
    try:
        payload = load_strict_json(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise refuse(f"factory registry is unreadable: {exc}") from exc
    factories = payload.get("factories") if isinstance(payload, dict) else None
    if not isinstance(factories, list):
        raise refuse("factory registry factories is not a list")
    ids: set[str] = set()
    for row in factories:
        if not isinstance(row, dict):
            continue
        path_id = row.get("path_id")
        if isinstance(path_id, str):
            ids.add(path_id)
    return ids


def const_dict(
    node: ast.Dict,
    evaluate: Callable[[ast.AST], Any],
    refuse: Callable[[], _Raise],
) -> dict[Any, Any]:
    """Evaluate a dict literal. A ``None`` key is unpacking and raises first."""

    keys: list[ast.expr] = []
    for key in node.keys:
        if key is None:
            raise refuse()
        keys.append(key)
    return {
        evaluate(key): evaluate(value) for key, value in zip(keys, node.values, strict=True)
    }


def plant_const_eval(node: ast.AST, refusal: _Raise, finding: str) -> Any:
    """Literal values only. Refuses calls, names, and starred dicts."""

    def evaluate(item: ast.AST) -> Any:
        return plant_const_eval(item, refusal, finding)

    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, (ast.List, ast.Tuple)):
        values = [evaluate(item) for item in node.elts]
        return values if isinstance(node, ast.List) else tuple(values)
    if isinstance(node, ast.Dict):
        return const_dict(
            node,
            evaluate,
            lambda: refusal(finding, "plant source uses dict unpacking"),
        )
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        return -evaluate(node.operand)
    raise refusal(
        finding,
        f"plant source is not a constant ({type(node).__name__})",
    )


bind_import_twin(__name__)
