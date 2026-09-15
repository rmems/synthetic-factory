#!/usr/bin/env python3
"""AST-extract compact Archive B plant identities from ``mill_plants.py``.

Reads only ``PAIRS.append((_ok(...), _fail(...), label))`` triples. Does not
import, compile, or exec ``scripts/infra_as_code_mill`` publishers.
"""

from __future__ import annotations

import ast
import hashlib
import json
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from .catalog_ast import call_kwargs, literal_value
from .vocabulary import PLANTS_COMPACT_KEYS, PLANTS_FILENAME, PLANTS_SOURCE_PATH

SHAPE_OK_FAIL_LABEL = "ok-fail-label"


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def extract_archive_b_plants(
    source: str,
    *,
    path: str = PLANTS_SOURCE_PATH,
) -> dict[str, Any]:
    """Structured extract for ``scripts/infra_as_code_mill/mill_plants.py``."""

    payload = source.encode()
    tree = ast.parse(source, filename=path)
    rows = _append_triples(tree)
    if not rows:
        raise ValueError(f"{path} has no PAIRS.append ok/fail/label triples")
    return {
        "path": path,
        "sha256": sha256_bytes(payload),
        "shape": SHAPE_OK_FAIL_LABEL,
        "n_plants": len(rows),
        "first_slug": rows[0]["success_slug"],
        "last_slug": rows[-1]["success_slug"],
        "plants": rows,
    }


def _append_triples(tree: ast.AST) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    index = 0
    for node in getattr(tree, "body", ()):
        if not isinstance(node, ast.Expr) or not isinstance(node.value, ast.Call):
            continue
        call = node.value
        if not isinstance(call.func, ast.Attribute) or call.func.attr != "append":
            continue
        if not isinstance(call.func.value, ast.Name) or call.func.value.id != "PAIRS":
            continue
        if len(call.args) != 1 or not isinstance(call.args[0], ast.Tuple):
            continue
        triple = call.args[0]
        if len(triple.elts) != 3:
            continue
        ok_node, fail_node, label_node = triple.elts
        ok = call_kwargs(ok_node)
        fail = call_kwargs(fail_node)
        if ok is None or fail is None or ok.get("slug") is None:
            continue
        label = literal_value(label_node)
        if not isinstance(label, str):
            continue
        rows.append(_compact_row(index, ok, fail, label))
        index += 1
    return rows


def _compact_row(index: int, ok: Mapping[str, Any], fail: Mapping[str, Any], label: str) -> dict[str, Any]:
    row = {
        "index": index,
        "success_slug": ok.get("slug"),
        "fail_slug": fail.get("slug"),
        "success_seed": ok.get("seed", ""),
        "fail_seed": fail.get("seed", ""),
        "scenario": label,
        "ticket": ok.get("ticket", ""),
        "test": ok.get("test", ""),
        "fail_handoff": bool(fail.get("handoff")),
    }
    missing = [key for key in PLANTS_COMPACT_KEYS if key not in row]
    if missing:
        raise ValueError(f"compact plant row missing {missing}")
    invalid = [
        key
        for key, value in row.items()
        if key in PLANTS_COMPACT_KEYS
        and not isinstance(value, (str, bool))
        and key != "index"
    ]
    if invalid:
        raise ValueError(f"compact plant row has invalid fields {invalid}")
    if type(row["index"]) is not int:
        raise ValueError("compact plant index must be int")
    return {key: row[key] for key in PLANTS_COMPACT_KEYS}


def dumps_plants_jsonl(rows: Sequence[Mapping[str, Any]]) -> str:
    lines = [json.dumps(dict(row), ensure_ascii=True, sort_keys=True) for row in rows]
    return "\n".join(lines) + "\n"


def plants_jsonl_path(package_dir: Path | None = None) -> Path:
    root = package_dir if package_dir is not None else Path(__file__).resolve().parent
    return root / PLANTS_FILENAME


def write_plants_jsonl(rows: Sequence[Mapping[str, Any]], path: Path | None = None) -> Path:
    destination = path if path is not None else plants_jsonl_path()
    destination.write_text(dumps_plants_jsonl(rows), encoding="utf-8")
    return destination
