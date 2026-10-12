#!/usr/bin/env python3
"""AST-extract Archive B plant pairs from ``mill_plants.py``.

Collects ``PAIRS.append((_ok(...), _bad(...)))`` nodes only. Does not import,
compile, or exec the mill publisher.
"""

from __future__ import annotations

import ast
import hashlib
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from .catalog_ast import UNSET, literal_value
from .vocabulary import OK_CALL, BAD_CALL, PLANTS_FILENAME, PLANTS_PAIR_COUNT

OK_SIDE = OK_CALL
BAD_SIDE = BAD_CALL


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _call_side(node: ast.AST) -> tuple[str, dict[str, Any]] | None:
    if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Name):
        return None
    name = node.func.id
    if name not in {OK_SIDE, BAD_SIDE}:
        return None
    if node.args:
        return None
    payload = _literal_keywords(node.keywords)
    if payload is None:
        return None
    payload["success"] = name == OK_SIDE
    return name, payload


def _literal_keywords(keywords: list[ast.keyword]) -> dict[str, Any] | None:
    """``key=literal`` keywords as a dict; ``None`` on ``**`` or a non-literal value."""

    payload: dict[str, Any] = {}
    for keyword in keywords:
        if keyword.arg is None:
            return None
        value = literal_value(keyword.value)
        if value is UNSET:
            return None
        payload[keyword.arg] = value
    return payload


def extract_plant_pairs(
    source: str,
    *,
    path: str,
    append_list: str = "PAIRS",
) -> list[dict[str, Any]]:
    """Return one record per ``PAIRS.append`` / ``MORE.append`` ok/bad tuple."""

    tree = ast.parse(source, filename=path)
    where = f"{path} {append_list}.append"
    pairs: list[dict[str, Any]] = []
    for node in tree.body:
        argument = _append_argument(node, append_list)
        if argument is not None:
            pairs.append(_plant_pair(argument, where))
    if not pairs:
        raise ValueError(f"{path} has no {append_list}.append plant pairs")
    return pairs


def _append_argument(node: ast.stmt, append_list: str) -> ast.expr | None:
    """The single argument of a top-level ``<append_list>.append(arg)`` statement."""

    call = node.value if isinstance(node, ast.Expr) else None
    if not isinstance(call, ast.Call) or len(call.args) != 1:
        return None
    if not _is_list_append(call.func, append_list):
        return None
    return call.args[0]


def _is_list_append(func: ast.expr, append_list: str) -> bool:
    """``func`` is the bound method ``<append_list>.append``."""

    if not isinstance(func, ast.Attribute) or func.attr != "append":
        return False
    return isinstance(func.value, ast.Name) and func.value.id == append_list


def _pair_sides(
    tup: ast.expr, where: str
) -> tuple[tuple[str, dict[str, Any]], tuple[str, dict[str, Any]]]:
    if not isinstance(tup, ast.Tuple) or len(tup.elts) != 2:
        raise ValueError(f"{where} is not an (_ok, _bad) tuple")
    ok_parsed = _call_side(tup.elts[0])
    bad_parsed = _call_side(tup.elts[1])
    if ok_parsed is None or bad_parsed is None:
        raise ValueError(f"{where} side is not _ok/_bad")
    return ok_parsed, bad_parsed


def _plant_pair(tup: ast.expr, where: str) -> dict[str, Any]:
    """One ``{"ok": ..., "bad": ...}`` pair from an ``(_ok(...), _bad(...))`` tuple."""

    (ok_name, ok), (bad_name, bad) = _pair_sides(tup, where)
    if (ok_name, bad_name) != (OK_SIDE, BAD_SIDE):
        raise ValueError(f"{where} order must be _ok then _bad")
    if "slug" not in ok or "slug" not in bad:
        raise ValueError(f"{where} missing slug")
    return {"ok": ok, "bad": bad}


def dumps_plants_jsonl(
    pairs: list[Mapping[str, Any]],
    *,
    mill_id: str,
    source: str,
    base_round: int,
) -> str:
    """One compact JSON object per pair. No pretty indent. Trailing LF."""

    lines: list[str] = []
    for index, pair in enumerate(pairs):
        ok = pair["ok"]
        bad = pair["bad"]
        slug = ok["slug"]
        record = {
            "i": index,
            "index": index,
            "base_round": base_round + index,
            "mill_id": mill_id,
            "plant_id": f"{mill_id}:{slug}",
            "source": source,
            "ok": ok,
            "bad": bad,
        }
        lines.append(json.dumps(record, ensure_ascii=True, separators=(",", ":")))
    return "\n".join(lines) + "\n"


def plants_jsonl_path(
    package_dir: Path | None = None,
    *,
    filename: str | None = None,
) -> Path:
    root = package_dir if package_dir is not None else Path(__file__).resolve().parent
    return root / (filename if filename is not None else PLANTS_FILENAME)


def extract_mill_plants_record(
    source: str,
    *,
    path: str,
    blob_sha: str,
    archive_commit: str,
    mill_id: str,
    catalog_first: int,
    append_list: str = "PAIRS",
    expected_pairs: int | None = None,
    plants_file: str | None = None,
) -> dict[str, Any]:
    payload = source.encode()
    pairs = extract_plant_pairs(source, path=path, append_list=append_list)
    want = expected_pairs if expected_pairs is not None else PLANTS_PAIR_COUNT
    if len(pairs) != want:
        raise ValueError(f"{path} expected {want} pairs, found {len(pairs)}")
    ok_slugs = [pair["ok"]["slug"] for pair in pairs]
    return {
        "mill_id": mill_id,
        "path": path,
        "archive_commit": archive_commit,
        "blob_sha": blob_sha,
        "sha256": sha256_bytes(payload),
        "kind": "plants",
        "shape": "ok-bad-pair",
        "catalog_first": catalog_first,
        "n_pairs": len(pairs),
        "first_ok_slug": ok_slugs[0],
        "last_ok_slug": ok_slugs[-1],
        "plants_file": plants_file if plants_file is not None else PLANTS_FILENAME,
    }
