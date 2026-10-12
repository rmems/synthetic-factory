#!/usr/bin/env python3
"""AST-extract the LHC w4cl plants-mk-fn catalog from one mill source.

Reads ``USED_FROM``, the ``PLANTS`` ``mk(...)`` table, and ``LHC_PAIRS``
``fn('key')`` sides. Does not import, compile, or exec the mill publisher.
"""

from __future__ import annotations

import ast
import hashlib
import json
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from .catalog_ast import (
    assignment_of,
    call_name,
    call_positional_literals,
    literal_value,
    module_docstring,
)
from .vocabulary import (
    CATALOG_FILENAME,
    CATALOG_SCHEMA_ID,
    FACTORY,
    FAMILY,
    GENERATOR,
    KIND_PAIRS,
    LEGACY_REF,
    PRESERVE_COMMIT,
    SHAPE_PLANTS_MK_FN,
    SLICE_ID,
)

PAIR_IDENTITY_KEYS = (
    "fail_key",
    "fail_plant",
    "fail_slug",
    "success_key",
    "success_plant",
    "success_slug",
    "title",
)
PLANT_IDENTITY_KEYS = ("key", "ok", "plant", "slug")
COMPACT_ARRAY_KEYS = frozenset({"pairs", "plants"})


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def mill_id_for_path(path: str) -> str:
    return Path(path).stem


def catalog_first_from_path(path: str) -> int:
    stem = Path(path).stem
    marker = stem.rsplit("-r", 1)
    if len(marker) != 2 or not marker[1].isdigit():
        raise ValueError(f"{path} mill id has no -rNNNN suffix")
    return int(marker[1])


def extract_mill_catalog(
    source: str,
    *,
    path: str,
    blob_sha: str = "",
) -> dict[str, Any]:
    """Structured catalog extract for the w4cl plants-mk-fn mill."""

    payload = source.encode()
    tree = ast.parse(source, filename=path)
    plants = _mk_plants(tree, path=path)
    pairs = _fn_pairs(tree, plants, path=path)
    used_from = _used_from(tree, path=path)
    return {
        "mill_id": mill_id_for_path(path),
        "path": path,
        "blob_sha": blob_sha,
        "sha256": sha256_bytes(payload),
        "kind": KIND_PAIRS,
        "shape": SHAPE_PLANTS_MK_FN,
        "catalog_first": catalog_first_from_path(path),
        "used_from": used_from,
        "n_rows": len(pairs),
        "n_plants": len(plants),
        "first_slug": pairs[0]["success_slug"],
        "last_slug": pairs[-1]["success_slug"],
        "generator": GENERATOR,
        "factory": FACTORY,
        "doc_first_line": _first_line(module_docstring(tree)),
        "plants": plants,
        "pairs": pairs,
    }


def _used_from(tree: ast.AST, *, path: str) -> int:
    for node in getattr(tree, "body", ()):
        name, value = assignment_of(node)
        if name != "USED_FROM" or value is None:
            continue
        resolved = literal_value(value)
        if isinstance(resolved, int):
            return resolved
        raise ValueError(f"{path} USED_FROM is not an int literal")
    raise ValueError(f"{path} USED_FROM assignment is missing")


def _assigned_value(tree: ast.AST, name: str, *, path: str) -> ast.AST | None:
    """Value of the first top-level ``name = ...`` (None for a bare annotation)."""

    for node in getattr(tree, "body", ()):
        assigned, value = assignment_of(node)
        if assigned == name:
            return value
    raise ValueError(f"{path} {name} assignment is missing")


def _mk_plants(tree: ast.AST, *, path: str) -> list[dict[str, Any]]:
    value = _assigned_value(tree, "PLANTS", path=path)
    if not isinstance(value, ast.Dict) or not value.keys:
        raise ValueError(f"{path} PLANTS is not a non-empty dict")
    entries = enumerate(zip(value.keys, value.values, strict=True))
    return [
        _mk_row(key_node, value_node, where=f"{path} PLANTS[{index}]")
        for index, (key_node, value_node) in entries
    ]


def _mk_row(key_node: ast.expr | None, value_node: ast.expr, *, where: str) -> dict[str, Any]:
    key = literal_value(key_node)
    identity = _mk_identity(value_node)
    if not _nonempty_text(key) or identity is None:
        raise ValueError(f"{where} is not a literal mk() plant")
    return {"key": key, **identity}


def _nonempty_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value)


def _literal_call_args(node: ast.AST, name: str) -> list[Any] | None:
    """Literal positional arguments of a ``name(...)`` call, else None."""

    return call_positional_literals(node) if call_name(node) == name else None


def _mk_identity(node: ast.AST) -> dict[str, Any] | None:
    args = _literal_call_args(node, "mk")
    if args is None or len(args) < 3:
        return None
    ok, slug, plant = args[0], args[1], args[2]
    if not isinstance(ok, bool) or not all(map(_nonempty_text, (slug, plant))):
        return None
    return {"ok": ok, "slug": slug, "plant": plant}


def _fn_pairs(
    tree: ast.AST, plants: Sequence[Mapping[str, Any]], *, path: str
) -> list[dict[str, Any]]:
    by_key = {row["key"]: row for row in plants}
    value = _assigned_value(tree, "LHC_PAIRS", path=path)
    if not isinstance(value, ast.List) or not value.elts:
        raise ValueError(f"{path} LHC_PAIRS is not a non-empty list")
    rows: list[dict[str, Any]] = []
    for index, elt in enumerate(value.elts):
        row = _pair_identity(elt, by_key)
        if row is None:
            raise ValueError(f"{path} LHC_PAIRS[{index}] is not a fn() identity pair")
        rows.append(row)
    return rows


def _pair_identity(
    node: ast.AST, plants: Mapping[str, Mapping[str, Any]]
) -> dict[str, Any] | None:
    if not isinstance(node, ast.Tuple) or len(node.elts) != 6:
        return None
    title = literal_value(node.elts[0])
    success = _keyed_plant(node.elts[1], plants)
    fail = _keyed_plant(node.elts[2], plants)
    if not isinstance(title, str) or not title:
        return None
    if success is None or fail is None:
        return None
    (success_key, success_plant), (fail_key, fail_plant) = success, fail
    return {
        "title": title,
        "success_key": success_key,
        "fail_key": fail_key,
        "success_slug": success_plant["slug"],
        "fail_slug": fail_plant["slug"],
        "success_plant": success_plant["plant"],
        "fail_plant": fail_plant["plant"],
    }


def _keyed_plant(
    node: ast.AST, plants: Mapping[str, Mapping[str, Any]]
) -> tuple[str, Mapping[str, Any]] | None:
    """``(key, plant)`` for a ``fn('key')`` side naming a catalogued plant, else None."""

    key = _fn_key(node)
    if key is None:
        return None
    plant = plants.get(key)
    return None if plant is None else (key, plant)


def _fn_key(node: ast.AST) -> str | None:
    args = _literal_call_args(node, "fn")
    if args is None or len(args) != 1 or not isinstance(args[0], str) or not args[0]:
        return None
    return args[0]


def _first_line(doc: str) -> str:
    for line in doc.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped
    return ""


def mill_summary(
    record: Mapping[str, Any],
    *,
    include_pairs: bool,
    include_plants: bool,
) -> dict[str, Any]:
    """Catalog mill row: identity plus optional compact pair/plant lists."""

    summary = {
        "mill_id": record["mill_id"],
        "path": record["path"],
        "blob_sha": record["blob_sha"],
        "sha256": record["sha256"],
        "kind": record["kind"],
        "shape": record["shape"],
        "catalog_first": record["catalog_first"],
        "used_from": record["used_from"],
        "n_rows": record["n_rows"],
        "n_plants": record["n_plants"],
        "first_slug": record["first_slug"],
        "last_slug": record["last_slug"],
        "generator": record["generator"],
        "factory": record["factory"],
        "doc_first_line": record["doc_first_line"],
    }
    if include_plants:
        summary["plants"] = [
            {key: row[key] for key in PLANT_IDENTITY_KEYS} for row in record["plants"]
        ]
    if include_pairs:
        summary["pairs"] = [
            {key: row[key] for key in PAIR_IDENTITY_KEYS} for row in record["pairs"]
        ]
    return summary


def catalog_document(mills: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "schema": CATALOG_SCHEMA_ID,
        "source_ref": LEGACY_REF,
        "preserve_commit": PRESERVE_COMMIT,
        "family": FAMILY,
        "factory": FACTORY,
        "generator": GENERATOR,
        "slice": SLICE_ID,
        "n_mills": len(mills),
        "n_pair_rows": sum(mill["n_rows"] for mill in mills),
        "n_plant_rows": sum(mill["n_plants"] for mill in mills),
        "mills": {mill["mill_id"]: mill for mill in mills},
    }


def dumps_catalog(document: Mapping[str, Any]) -> str:
    """Pretty-print the header; pair and plant identities stay one object per line."""

    return _encode(document, 0, key=None) + "\n"


def _encode(value: Any, level: int, key: str | None) -> str:
    """Nested containers recurse here directly, one frame per level as before.

    Empty containers and scalars are plain ``json.dumps``; the ``pairs`` and
    ``plants`` arrays keep one compact object per line.
    """

    pad = "  " * level
    if isinstance(value, dict) and value:
        parts = [
            f"{pad}  {json.dumps(item_key)}: {_encode(value[item_key], level + 1, item_key)}"
            for item_key in sorted(value)
        ]
        return "{\n" + ",\n".join(parts) + f"\n{pad}}}"
    if isinstance(value, list) and value:
        lines = (
            _compact_lines(value, pad)
            if key in COMPACT_ARRAY_KEYS
            else [f"{pad}  {_encode(item, level + 1, None)}" for item in value]
        )
        return "[\n" + ",\n".join(lines) + f"\n{pad}]"
    return json.dumps(value, ensure_ascii=True)


def _compact_lines(items: list[Any], pad: str) -> list[str]:
    return [
        f"{pad}  "
        + json.dumps(item, ensure_ascii=True, sort_keys=True, separators=(", ", ": "))
        for item in items
    ]


def catalog_json_path(package_dir: Path | None = None) -> Path:
    root = package_dir if package_dir is not None else Path(__file__).resolve().parent
    return root / CATALOG_FILENAME


def write_catalog_document(document: Mapping[str, Any], path: Path | None = None) -> Path:
    destination = path if path is not None else catalog_json_path()
    destination.write_text(dumps_catalog(document), encoding="utf-8")
    return destination
