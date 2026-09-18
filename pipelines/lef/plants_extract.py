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
    payload: dict[str, Any] = {}
    for keyword in node.keywords:
        if keyword.arg is None:
            return None
        value = literal_value(keyword.value)
        if value is UNSET:
            return None
        payload[keyword.arg] = value
    payload["success"] = name == OK_SIDE
    return name, payload


def extract_plant_pairs(
    source: str,
    *,
    path: str,
    append_list: str = "PAIRS",
) -> list[dict[str, Any]]:
    """Return one record per ``PAIRS.append`` / ``MORE.append`` ok/bad tuple."""

    tree = ast.parse(source, filename=path)
    pairs: list[dict[str, Any]] = []
    for node in tree.body:
        if not isinstance(node, ast.Expr):
            continue
        call = node.value
        if not isinstance(call, ast.Call) or not isinstance(call.func, ast.Attribute):
            continue
        if call.func.attr != "append" or not isinstance(call.func.value, ast.Name):
            continue
        if call.func.value.id != append_list or len(call.args) != 1:
            continue
        tup = call.args[0]
        if not isinstance(tup, ast.Tuple) or len(tup.elts) != 2:
            raise ValueError(f"{path} {append_list}.append is not an (_ok, _bad) tuple")
        ok_parsed = _call_side(tup.elts[0])
        bad_parsed = _call_side(tup.elts[1])
        if ok_parsed is None or bad_parsed is None:
            raise ValueError(f"{path} {append_list}.append side is not _ok/_bad")
        ok_name, ok = ok_parsed
        bad_name, bad = bad_parsed
        if ok_name != OK_SIDE or bad_name != BAD_SIDE:
            raise ValueError(f"{path} {append_list}.append order must be _ok then _bad")
        if "slug" not in ok or "slug" not in bad:
            raise ValueError(f"{path} {append_list}.append missing slug")
        pairs.append({"ok": ok, "bad": bad})
    if not pairs:
        raise ValueError(f"{path} has no {append_list}.append plant pairs")
    return pairs


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
