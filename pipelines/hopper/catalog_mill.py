#!/usr/bin/env python3
"""AST-extract ssl hopper mills (tuple PAIRS) from legacy-mill-lane.

Mill scripts are read only as text through ``ast.parse``; they are never
imported or executed. Compact pair rows land in ``pairs.jsonl`` beside
``CATALOG.json`` under this package directory.
"""

from __future__ import annotations

import ast
import hashlib
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from ._contract import (
    FINDING_CATALOG_FIELD_INVALID,
    FINDING_CATALOG_FIELD_MISSING,
    FINDING_CATALOG_FILE_MISSING,
    FINDING_PLANTS_SHA_MISMATCH,
    bind_import_twin,
    load_strict_json,
    refuse,
    refuse_when,
)

CATALOG_FILENAME = "CATALOG.json"
PAIRS_FILENAME = "pairs.jsonl"
DEFAULT_MILL_CATALOG_DIR = Path(__file__).resolve().parent
SIDE_KEYS = ("slug", "stack", "unit", "wrong", "remedy", "ticket", "url", "path")
REQUIRED_HEADER_FIELDS = (
    "catalog_id",
    "family",
    "schema",
    "factory",
    "generator",
    "source_commit",
    "source_ref",
    "extraction",
    "pairs_filename",
    "pairs_sha256",
    "n_pair_rows_extracted",
    "n_pair_rows_committed",
    "mills",
)
MILL_SOURCE_PATHS = (
    "experiments/ssl-mill-r35.py",
    "experiments/ssl-mill-r112.py",
    "experiments/ssl-mill-r132.py",
)

__all__ = [
    "CATALOG_FILENAME",
    "DEFAULT_MILL_CATALOG_DIR",
    "MILL_SOURCE_PATHS",
    "PAIRS_FILENAME",
    "SIDE_KEYS",
    "ast_extract_mill_pairs",
    "catalog_mill_check",
    "load_mill_catalog",
    "sha256_bytes",
    "sha256_text",
]


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _literal_str(node: ast.AST, where: str) -> str:
    refuse_when(
        not isinstance(node, ast.Constant) or not isinstance(node.value, str),
        FINDING_CATALOG_FIELD_INVALID,
        f"{where} must be a string literal",
    )
    assert isinstance(node, ast.Constant)
    return node.value


def _side_tuple(node: ast.AST, where: str) -> dict[str, str]:
    refuse_when(
        not isinstance(node, ast.Tuple) or len(node.elts) != 8,
        FINDING_CATALOG_FIELD_INVALID,
        f"{where} must be an 8-tuple of string literals",
    )
    assert isinstance(node, ast.Tuple)
    values = [_literal_str(elt, f"{where}[{index}]") for index, elt in enumerate(node.elts)]
    return dict(zip(SIDE_KEYS, values, strict=True))


def _module_constants(tree: ast.Module) -> dict[str, Any]:
    found: dict[str, Any] = {}
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if not isinstance(target, ast.Name):
                continue
            name = target.id
            if name in {"FACTORY", "GEN", "CATALOG_FIRST"}:
                value = node.value
                if isinstance(value, ast.Constant) and isinstance(value.value, (str, int)):
                    if not isinstance(value.value, bool):
                        found[name] = value.value
    return found


def _pairs_list(tree: ast.Module) -> ast.List:
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "PAIRS":
                    refuse_when(
                        not isinstance(node.value, ast.List),
                        FINDING_CATALOG_FIELD_INVALID,
                        "PAIRS must be a list",
                    )
                    return node.value
    refuse(FINDING_CATALOG_FIELD_INVALID, "plants source has no PAIRS list")


def ast_extract_mill_pairs(source: str, *, source_path: str) -> tuple[dict[str, Any], ...]:
    """Return compact pair rows for one ssl-mill-r* module."""

    tree = ast.parse(source, filename=source_path)
    consts = _module_constants(tree)
    factory = consts.get("FACTORY", "ssl-cert-rotation-factory")
    generator = consts.get("GEN", "grok-4.6")
    catalog_first = consts.get("CATALOG_FIRST")
    refuse_when(
        not isinstance(catalog_first, int) or isinstance(catalog_first, bool),
        FINDING_CATALOG_FIELD_INVALID,
        f"{source_path} missing int CATALOG_FIRST",
    )
    mill_id = Path(source_path).stem
    pairs_node = _pairs_list(tree)
    rows: list[dict[str, Any]] = []
    for index, item in enumerate(pairs_node.elts):
        refuse_when(
            not isinstance(item, ast.Tuple) or len(item.elts) != 2,
            FINDING_CATALOG_FIELD_INVALID,
            f"{source_path} PAIRS[{index}] must be (ok, bad)",
        )
        assert isinstance(item, ast.Tuple)
        ok = _side_tuple(item.elts[0], f"{source_path} PAIRS[{index}].ok")
        bad = _side_tuple(item.elts[1], f"{source_path} PAIRS[{index}].bad")
        rows.append(
            {
                "mill_id": mill_id,
                "index": index,
                "round": catalog_first + index,
                "factory": factory,
                "generator": generator,
                "source": source_path,
                "ok": ok,
                "bad": bad,
            }
        )
    return tuple(rows)


def _require_keys(document: Mapping[str, Any], keys: tuple[str, ...], label: str) -> None:
    missing = [key for key in keys if key not in document]
    refuse_when(bool(missing), FINDING_CATALOG_FIELD_MISSING, f"{label} missing {missing}")


def load_mill_catalog(directory: Path | None = None) -> tuple[Mapping[str, Any], tuple[dict[str, Any], ...]]:
    root = directory or DEFAULT_MILL_CATALOG_DIR
    catalog_path = root / CATALOG_FILENAME
    pairs_path = root / PAIRS_FILENAME
    refuse_when(not catalog_path.is_file(), FINDING_CATALOG_FILE_MISSING, f"missing {catalog_path}")
    refuse_when(not pairs_path.is_file(), FINDING_CATALOG_FILE_MISSING, f"missing {pairs_path}")
    meta = load_strict_json(catalog_path.read_text(encoding="utf-8"))
    _require_keys(meta, REQUIRED_HEADER_FIELDS, CATALOG_FILENAME)
    payload = pairs_path.read_bytes()
    refuse_when(
        sha256_bytes(payload) != meta["pairs_sha256"],
        FINDING_PLANTS_SHA_MISMATCH,
        f"{pairs_path} sha256 drift",
    )
    rows: list[dict[str, Any]] = []
    for line_no, line in enumerate(payload.splitlines(), start=1):
        if not line:
            continue
        row = json.loads(line)
        rows.append(row)
    refuse_when(
        len(rows) != meta["n_pair_rows_committed"],
        FINDING_CATALOG_FIELD_INVALID,
        f"pair row count {len(rows)} != header {meta['n_pair_rows_committed']}",
    )
    return meta, tuple(rows)


def catalog_mill_check(directory: Path | None = None) -> Mapping[str, Any]:
    meta, rows = load_mill_catalog(directory)
    refuse_when(
        meta["n_pair_rows_extracted"] != meta["n_pair_rows_committed"],
        FINDING_CATALOG_FIELD_INVALID,
        "ssl hopper slice is rank-1 full extract",
    )
    slugs: set[str] = set()
    for row in rows:
        for side in ("ok", "bad"):
            slug = row[side]["slug"]
            refuse_when(slug in slugs, FINDING_CATALOG_FIELD_INVALID, f"duplicate slug {slug!r}")
            slugs.add(slug)
    return meta


bind_import_twin(__name__)
