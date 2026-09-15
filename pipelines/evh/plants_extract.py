#!/usr/bin/env python3
"""AST-extract Archive B/C leftover trajectory plants from ``mill_plants*.py``.

Reads only ``PAIRS.append((_ok(...), _bad(...)))`` module statements. Does not
import, compile, or exec ``scripts/eval_harness_unique_mill``.
"""

from __future__ import annotations

import ast
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from .catalog_extract import sha256_bytes
from .vocabulary import (
    ARCHIVE_B_PATH,
    LEFTOVER_PLANT_ROW_KEYS,
    LEFTOVER_PLANTS_B_FILENAME,
    LEFTOVER_PLANTS_FILENAME,
)

_PLANT_CALLS = frozenset({"_ok", "_bad"})
_SIDE_KEYS = ("slug", "domain", "kind")


def _literal_str(node: ast.AST, where: str) -> str:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    raise ValueError(f"{where}: expected str literal")


def _side_from_call(node: ast.AST, where: str) -> dict[str, str]:
    if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Name):
        raise ValueError(f"{where}: expected _ok/_bad(**kwargs)")
    if node.func.id not in _PLANT_CALLS or node.args:
        raise ValueError(f"{where}: expected _ok/_bad(**kwargs)")
    if any(kw.arg is None for kw in node.keywords):
        raise ValueError(f"{where}: kwargs must be named")
    side: dict[str, str] = {}
    for kw in node.keywords:
        assert kw.arg is not None
        if kw.arg not in _SIDE_KEYS:
            continue
        side[kw.arg] = _literal_str(kw.value, f"{where}.{kw.arg}")
    missing = [key for key in _SIDE_KEYS if key not in side]
    if missing:
        raise ValueError(f"{where} missing {missing}")
    return side


def extract_leftover_plant_pairs(
    source: str,
    *,
    path: str = ARCHIVE_B_PATH,
) -> list[dict[str, Any]]:
    """Return compact Archive B pair identities in source order."""

    tree = ast.parse(source, filename=path)
    rows: list[dict[str, Any]] = []
    index = 0
    for node in tree.body:
        if not isinstance(node, ast.Expr) or not isinstance(node.value, ast.Call):
            continue
        call = node.value
        if not isinstance(call.func, ast.Attribute):
            continue
        if call.func.attr != "append" or not isinstance(call.func.value, ast.Name):
            continue
        if call.func.value.id != "PAIRS" or len(call.args) != 1:
            continue
        payload = call.args[0]
        if not isinstance(payload, (ast.Tuple, ast.List)) or len(payload.elts) != 2:
            raise ValueError(f"{path}: PAIRS.append must receive (_ok, _bad)")
        ok = _side_from_call(payload.elts[0], f"PAIRS[{index}].ok")
        bad = _side_from_call(payload.elts[1], f"PAIRS[{index}].bad")
        rows.append(
            compact_leftover_plant_row(
                index,
                ok,
                bad,
                source=path,
            )
        )
        index += 1
    if not rows:
        raise ValueError(f"{path} has no PAIRS.append leftover plants")
    return rows


def compact_leftover_plant_row(
    index: int,
    ok: Mapping[str, str],
    bad: Mapping[str, str],
    *,
    source: str,
) -> dict[str, Any]:
    row = {
        "index": index,
        "ok_slug": ok["slug"],
        "ok_domain": ok["domain"],
        "ok_kind": ok["kind"],
        "bad_slug": bad["slug"],
        "bad_domain": bad["domain"],
        "bad_kind": bad["kind"],
        "source": source,
    }
    return {key: row[key] for key in LEFTOVER_PLANT_ROW_KEYS}


def dumps_leftover_plants_jsonl(rows: list[Mapping[str, Any]]) -> str:
    lines = [
        json.dumps(row, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
        for row in rows
    ]
    return "\n".join(lines) + "\n"


def leftover_plants_jsonl_path(package_dir: Path | None = None) -> Path:
    root = package_dir if package_dir is not None else Path(__file__).resolve().parent
    return root / LEFTOVER_PLANTS_FILENAME


def leftover_plants_b_jsonl_path(package_dir: Path | None = None) -> Path:
    root = package_dir if package_dir is not None else Path(__file__).resolve().parent
    return root / LEFTOVER_PLANTS_B_FILENAME
