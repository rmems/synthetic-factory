#!/usr/bin/env python3
"""AST-extract compact Archive B plant identities from ``mill_plants*.py``.

Reads only ``LIST.append((_ok(...), _fail(...), label))`` triples (``PAIRS``
on ``mill_plants.py``, ``MORE`` on ``mill_plants_b.py``). Does not import,
compile, or exec ``scripts/infra_as_code_mill`` publishers.
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

_PLANT_FIELD_TYPES = {"index": int, "fail_handoff": bool}


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def extract_archive_b_plants(
    source: str,
    *,
    path: str = PLANTS_SOURCE_PATH,
) -> dict[str, Any]:
    """Structured extract for ``scripts/infra_as_code_mill/mill_plants.py``."""

    return extract_ok_fail_label_plants(source, path=path, list_name="PAIRS")


def extract_archive_b_more_plants(
    source: str,
    *,
    path: str = "scripts/infra_as_code_mill/mill_plants_b.py",
) -> dict[str, Any]:
    """Structured extract for ``scripts/infra_as_code_mill/mill_plants_b.py``."""

    return extract_ok_fail_label_plants(source, path=path, list_name="MORE")


def extract_ok_fail_label_plants(
    source: str,
    *,
    path: str,
    list_name: str,
) -> dict[str, Any]:
    """Structured extract for ``LIST.append((_ok(...), _fail(...), label))`` triples."""

    payload = source.encode()
    tree = ast.parse(source, filename=path)
    rows = _append_triples(tree, list_name)
    if not rows:
        raise ValueError(f"{path} has no {list_name}.append ok/fail/label triples")
    return {
        "path": path,
        "sha256": sha256_bytes(payload),
        "shape": SHAPE_OK_FAIL_LABEL,
        "n_plants": len(rows),
        "first_slug": rows[0]["success_slug"],
        "last_slug": rows[-1]["success_slug"],
        "plants": rows,
    }


def archive_b_row(
    extract: Mapping[str, Any],
    *,
    ref: str,
    commit: str,
    blob_sha: str,
) -> dict[str, Any]:
    """CATALOG.json ``archive_b`` block from a plant extract plus its pin."""

    return {
        "ref": ref,
        "commit": commit,
        "path": extract["path"],
        "blob_sha": blob_sha,
        "sha256": extract["sha256"],
        "shape": extract["shape"],
        "n_plants": extract["n_plants"],
        "first_slug": extract["first_slug"],
        "last_slug": extract["last_slug"],
    }


def _append_triples(tree: ast.AST, list_name: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for node in getattr(tree, "body", ()):
        triple = _list_append_arg(node, list_name)
        if triple is None:
            continue
        row = _triple_row(len(rows), triple)
        if row is not None:
            rows.append(row)
    return rows


def _is_list_append(call: ast.Call, list_name: str) -> bool:
    func = call.func
    return (
        isinstance(func, ast.Attribute)
        and func.attr == "append"
        and isinstance(func.value, ast.Name)
        and func.value.id == list_name
    )


def _list_append_arg(node: ast.AST, list_name: str) -> ast.Tuple | None:
    if not isinstance(node, ast.Expr) or not isinstance(node.value, ast.Call):
        return None
    call = node.value
    if not _is_list_append(call, list_name):
        return None
    if len(call.args) != 1 or not isinstance(call.args[0], ast.Tuple):
        return None
    triple = call.args[0]
    return triple if len(triple.elts) == 3 else None


def _triple_row(index: int, triple: ast.Tuple) -> dict[str, Any] | None:
    ok_node, fail_node, label_node = triple.elts
    ok = call_kwargs(ok_node)
    fail = call_kwargs(fail_node)
    if ok is None or fail is None or ok.get("slug") is None:
        return None
    label = literal_value(label_node)
    if not isinstance(label, str):
        return None
    return _compact_row(index, ok, fail, label)


def _compact_row(
    index: int,
    ok: Mapping[str, Any],
    fail: Mapping[str, Any],
    label: str,
) -> dict[str, Any]:
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
    invalid = [
        key
        for key in PLANTS_COMPACT_KEYS
        if key not in row or type(row[key]) is not _PLANT_FIELD_TYPES.get(key, str)
    ]
    if invalid:
        raise ValueError(f"compact plant row has missing or invalid fields {invalid}")
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
