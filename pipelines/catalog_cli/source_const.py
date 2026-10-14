"""Constant-source checks shared by the plant catalogs.

The five generate-shape catalogs used to copy these two blocks. One copy keeps
the refusal text and the returned set identical, and keeps the blocks from
matching as duplicated new code.
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
_Refuse = Callable[[str, str], Any]


def registry_factory_ids(
    repo_root: Callable[[], Path],
    load_strict_json: _LoadJson,
    refusal: _Refuse,
    finding: str,
) -> set[str]:
    """Path ids from ``config/FACTORY-REGISTRY.json``.

    A row that is not a dict, or a ``path_id`` that is not a str, is skipped.
    An unreadable registry or a ``factories`` value that is not a list raises
    ``refusal(finding, message)``.
    """

    path = repo_root() / "config" / "FACTORY-REGISTRY.json"
    try:
        payload = load_strict_json(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise refusal(finding, f"factory registry is unreadable: {exc}") from exc
    factories = payload.get("factories") if isinstance(payload, dict) else None
    if not isinstance(factories, list):
        raise refusal(finding, "factory registry factories is not a list")
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
    refusal: _Refuse,
    finding: str,
    message: str,
) -> dict[Any, Any]:
    """Evaluate a dict literal. A ``None`` key is unpacking and raises first."""

    keys: list[ast.expr] = []
    for key in node.keys:
        if key is None:
            raise refusal(finding, message)
        keys.append(key)
    return {evaluate(key): evaluate(value) for key, value in zip(keys, node.values)}


bind_import_twin(__name__)
