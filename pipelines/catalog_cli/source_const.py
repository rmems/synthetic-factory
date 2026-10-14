"""Constant-source checks shared by the plant catalogs.

The generate-shape catalogs used to copy these blocks. One copy keeps the
refusal text and the returned set identical.
"""

from __future__ import annotations

import ast
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

if __name__.startswith("pipelines."):
    from ..oracle_grounded.import_twins import bind_import_twin
else:
    from oracle_grounded.import_twins import bind_import_twin

_LoadJson = Callable[[str], Any]


def _read_registry(
    path: Path,
    load_strict_json: _LoadJson,
    refuse: Callable[[str], BaseException],
) -> Any:
    try:
        return load_strict_json(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise refuse(f"factory registry is unreadable: {exc}") from exc


def _factory_list(payload: Any, refuse: Callable[[str], BaseException]) -> list[Any]:
    factories = payload.get("factories") if isinstance(payload, dict) else None
    if not isinstance(factories, list):
        raise refuse("factory registry factories is not a list")
    return factories


def _path_id(row: Any) -> str | None:
    if not isinstance(row, dict):
        return None
    path_id = row.get("path_id")
    if isinstance(path_id, str):
        return path_id
    return None


def registry_factory_ids(
    repo_root: Callable[[], Path],
    load_strict_json: _LoadJson,
    refuse: Callable[[str], BaseException],
) -> set[str]:
    """Path ids from ``config/FACTORY-REGISTRY.json``.

    A row that is not a dict, or a ``path_id`` that is not a str, is skipped.
    ``refuse(message)`` must return the refusal exception for an unreadable
    registry or a ``factories`` value that is not a list.
    """

    path = repo_root() / "config" / "FACTORY-REGISTRY.json"
    payload = _read_registry(path, load_strict_json, refuse)
    ids: set[str] = set()
    for row in _factory_list(payload, refuse):
        path_id = _path_id(row)
        if path_id is not None:
            ids.add(path_id)
    return ids


def _present_keys(node: ast.Dict, refuse: Callable[[], BaseException]) -> list[ast.expr]:
    keys: list[ast.expr] = []
    for key in node.keys:
        if key is None:
            raise refuse()
        keys.append(key)
    return keys


def const_dict(
    node: ast.Dict,
    evaluate: Callable[[ast.AST], Any],
    refuse: Callable[[], BaseException],
) -> dict[Any, Any]:
    """Evaluate a dict literal. A ``None`` key is unpacking and raises first."""

    keys = _present_keys(node, refuse)
    return {
        evaluate(key): evaluate(value) for key, value in zip(keys, node.values, strict=True)
    }


def _sequence_const(
    node: ast.List | ast.Tuple,
    evaluate: Callable[[ast.AST], Any],
) -> list[Any] | tuple[Any, ...]:
    values = [evaluate(item) for item in node.elts]
    if isinstance(node, ast.List):
        return values
    return tuple(values)


def _unary_fold(node: ast.AST, evaluate: Callable[[ast.AST], Any]) -> tuple[Any] | None:
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        return (-evaluate(node.operand),)
    return None


def _folded_const(
    node: ast.AST,
    refusal: Callable[..., BaseException],
    finding: str,
) -> tuple[Any] | None:
    def evaluate(item: ast.AST) -> Any:
        return plant_const_eval(item, refusal, finding)

    if isinstance(node, ast.Constant):
        return (node.value,)
    if isinstance(node, (ast.List, ast.Tuple)):
        return (_sequence_const(node, evaluate),)
    if isinstance(node, ast.Dict):
        return (
            const_dict(
                node,
                evaluate,
                lambda: refusal(finding, "plant source uses dict unpacking"),
            ),
        )
    return _unary_fold(node, evaluate)


def plant_const_eval(node: ast.AST, refusal: Callable[..., BaseException], finding: str) -> Any:
    """Literal values only. Refuses calls, names, and starred dicts."""

    folded = _folded_const(node, refusal, finding)
    if folded is None:
        raise refusal(
            finding,
            f"plant source is not a constant ({type(node).__name__})",
        )
    return folded[0]


def _base_from_mill(base: Any, mill_id: str, prefix: str) -> Any:
    if base is None:
        return int(mill_id[len(prefix) :])
    return base


def _reject_bool(resolved: Any, refuse: Callable[[], BaseException]) -> Any:
    if isinstance(resolved, bool) or not isinstance(resolved, int):
        raise refuse()
    return resolved


def _reject_nonpositive(resolved: int, refuse: Callable[[], BaseException]) -> int:
    if resolved < 1:
        raise refuse()
    return resolved


def require_positive_base(
    base: Any,
    mill_id: str,
    prefix: str,
    refuse: Callable[[], BaseException],
) -> int:
    """Use ``base``, or the numeric tail of ``mill_id``. ``refuse()`` has the message."""

    resolved = _reject_bool(_base_from_mill(base, mill_id, prefix), refuse)
    return _reject_nonpositive(resolved, refuse)


def _first_missing(raw: Mapping[str, Any], keys: tuple[str, ...]) -> str | None:
    for key in keys:
        if key not in raw:
            return key
    return None


def _row_object(
    raw: Any,
    where: tuple[str, str, int],
    refuse_parse: Callable[[str], BaseException],
) -> Mapping[str, Any]:
    source, label, index = where
    if not isinstance(raw, dict):
        raise refuse_parse(f"{source} {label}[{index}] is not an object")
    return raw


def _filled_row(
    raw: Mapping[str, Any],
    keys: tuple[str, ...],
    identity: Mapping[str, Any],
) -> dict[str, Any]:
    mill_id = identity["mill_id"]
    row = {
        "plant_id": f"{mill_id}:{raw['slug']}",
        "mill_id": mill_id,
        "source": identity["source"],
        "base_round": identity["base_round"],
    }
    row.update({key: raw[key] for key in keys})
    return row


def _one_row(
    raw: Any,
    keys: tuple[str, ...],
    index: int,
    packed: tuple[
        Mapping[str, Any],
        tuple[Callable[[str], BaseException], Callable[[str], BaseException]],
    ],
) -> dict[str, Any]:
    identity, refusals = packed
    refuse_parse, refuse_missing = refusals
    source = identity["source"]
    label = identity["label"]
    parsed = _row_object(raw, (source, label, index), refuse_parse)
    missing = _first_missing(parsed, keys)
    if missing is not None:
        raise refuse_missing(f"{source} {label}[{index}] missing {missing}")
    return _filled_row(parsed, keys, identity)


def keyed_plant_rows(
    raw_plants: list[Any],
    keys: tuple[str, ...],
    identity: Mapping[str, Any],
    refusals: tuple[Callable[[str], BaseException], Callable[[str], BaseException]],
) -> tuple[dict[str, Any], ...]:
    """One row per dict. ``refusals`` is ``(parse, missing)`` and each returns an exception."""

    rows: list[dict[str, Any]] = []
    for index, raw in enumerate(raw_plants):
        rows.append(_one_row(raw, keys, index, (identity, refusals)))
    return tuple(rows)


bind_import_twin(__name__)
