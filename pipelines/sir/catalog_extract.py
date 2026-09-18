#!/usr/bin/env python3
"""AST-extract sir mill catalog identity from a mill source.

Evaluates only literal catalog assignments (``FACTORY``, ``GEN``,
``CATALOG_FIRST``, ``N_ROUNDS``, ``HOP``, ``PAIRS``). Records a
``SourceFileLoader`` sibling path when that filename is a string literal.
Does not import, compile, or exec leftover / loop publishers, so those
scripts stay off this branch.
"""

from __future__ import annotations

import ast
import hashlib
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from .catalog_ast import UNSET, assignment_names, assignment_of, literal_value, module_docstring
from .vocabulary import (
    CATALOG_FILENAME,
    CATALOG_SCHEMA_ID,
    FACTORY,
    GENERATOR,
    KIND_CATALOG_PAIRS,
    KIND_LEFTOVER_PAIRS,
    LEGACY_REF,
    PAIR_FIELD_ORDER,
    PAIRS_FILENAME,
    PRESERVE_COMMIT,
    SHAPE_PAIR_6TUPLES,
    SLICE_ID,
)


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def mill_id_for_path(path: str) -> str:
    return Path(path).stem


def mill_kind_for_id(mill_id: str) -> str:
    return KIND_LEFTOVER_PAIRS if "leftover" in mill_id else KIND_CATALOG_PAIRS


def extract_mill_catalog(
    source: str,
    *,
    path: str,
    blob_sha: str = "",
) -> dict[str, Any]:
    """Structured catalog extract for one sir mill source file."""

    payload = source.encode()
    tree = ast.parse(source, filename=path)
    mill_id = mill_id_for_path(path)
    constants = _module_constants(tree)
    factory = _required_string(constants.get("FACTORY", FACTORY), f"{path} FACTORY")
    generator = _required_string(constants.get("GEN", GENERATOR), f"{path} GEN")
    catalog_first = _catalog_first(constants, path)
    hops = _optional_factory_list(constants.get("HOP", UNSET), path=path)
    rows = _pair_rows(constants.get("PAIRS"), path=path, mill_id=mill_id)
    n_rounds = _round_count(constants.get("N_ROUNDS"), len(rows), path)
    return {
        "mill_id": mill_id,
        "path": path,
        "blob_sha": blob_sha,
        "sha256": sha256_bytes(payload),
        "kind": mill_kind_for_id(mill_id),
        "shape": SHAPE_PAIR_6TUPLES,
        "catalog_first": catalog_first,
        "n_rounds": n_rounds,
        "n_rows": len(rows),
        "n_hops": len(hops),
        "first_slug": rows[0]["success_slug"],
        "last_slug": rows[-1]["success_slug"],
        "generator": generator,
        "factory": factory,
        "hops": list(hops),
        "loads_sibling": _literal_sibling_path(tree),
        "source_lines": len(source.splitlines()),
        "doc_first_line": _first_line(module_docstring(tree)),
        "pairs": rows,
    }


def _module_constants(tree: ast.AST) -> dict[str, Any]:
    env: dict[str, Any] = {}
    for node in getattr(tree, "body", ()):
        name, value = assignment_of(node)
        if name is None:
            for assigned in assignment_names(node):
                env.pop(assigned, None)
        elif value is not None:
            _bind_literal(env, name, value)
    return env


def _bind_literal(env: dict[str, Any], name: str, value: ast.AST) -> None:
    resolved = literal_value(value, env)
    if resolved is UNSET:
        env.pop(name, None)
    else:
        env[name] = resolved


def _required_string(value: Any, where: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{where} is not a non-empty string")
    return value


def _catalog_first(constants: Mapping[str, Any], path: str) -> int:
    value = constants.get("CATALOG_FIRST")
    if not isinstance(value, int):
        raise ValueError(f"{path} CATALOG_FIRST is not an int")
    return value


def _round_count(value: Any, n_pairs: int, path: str) -> int:
    if value is None:
        return n_pairs
    if not isinstance(value, int) or value < 1:
        raise ValueError(f"{path} N_ROUNDS is not a positive int")
    if value != n_pairs:
        raise ValueError(f"{path} N_ROUNDS={value} disagrees with {n_pairs} pairs")
    return value


def _optional_factory_list(value: Any, *, path: str) -> list[str]:
    if value is UNSET or value is None:
        return []
    if not isinstance(value, list):
        raise ValueError(f"{path} HOP is not a literal list of factory slugs")
    if not all(_is_factory_slug(item) for item in value):
        raise ValueError(f"{path} HOP is not a literal list of factory slugs")
    return list(value)


def _is_factory_slug(value: Any) -> bool:
    return isinstance(value, str) and value.endswith("-factory")


def _pair_rows(pairs_raw: Any, *, path: str, mill_id: str) -> list[dict[str, Any]]:
    if not isinstance(pairs_raw, list) or not pairs_raw:
        raise ValueError(f"{path} PAIRS is not a non-empty literal list")
    return [
        _pair_row(pair, mill_id, f"{path} PAIRS[{index}]") for index, pair in enumerate(pairs_raw)
    ]


def _pair_row(pair: Any, mill_id: str, where: str) -> dict[str, Any]:
    if not isinstance(pair, (tuple, list)) or len(pair) != 2:
        raise ValueError(f"{where} is not a 2-tuple")
    success, fail = pair
    if not _is_six_strings(success) or not _is_six_strings(fail):
        raise ValueError(f"{where} arms are not 6-string tuples")
    return {
        "mill_id": mill_id,
        "success_slug": success[0],
        "fail_slug": fail[0],
        "success_engine": success[1],
        "fail_engine": fail[1],
        "success_wrong": success[2],
        "fail_wrong": fail[2],
        "success_fix": success[3],
        "fail_leftover": fail[3],
        "success_ticket": success[4],
        "fail_ticket": fail[4],
        "success_url": success[5],
        "fail_url": fail[5],
        "fail_handoff": True,
    }


def _is_six_strings(arm: Any) -> bool:
    return (
        isinstance(arm, (tuple, list))
        and len(arm) == 6
        and all(isinstance(item, str) and item for item in arm)
    )


def _literal_sibling_path(tree: ast.AST) -> str:
    """Return ``experiments/<file>`` when SourceFileLoader is given a .py literal."""

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not _is_source_file_loader(node.func):
            continue
        filename = _first_py_constant(node)
        if filename:
            name = Path(filename).name
            return f"experiments/{name}"
    return ""


def _is_source_file_loader(func: ast.AST) -> bool:
    if isinstance(func, ast.Name):
        return func.id == "SourceFileLoader"
    return isinstance(func, ast.Attribute) and func.attr == "SourceFileLoader"


def _first_py_constant(node: ast.AST) -> str:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value if node.value.endswith(".py") else ""
    if isinstance(node, ast.Call):
        for arg in node.args:
            found = _first_py_constant(arg)
            if found:
                return found
        return ""
    if isinstance(node, ast.BinOp):
        return _first_py_constant(node.right) or _first_py_constant(node.left)
    return ""


def _first_line(doc: str) -> str:
    for line in doc.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped
    return ""


def mill_summary(record: Mapping[str, Any]) -> dict[str, Any]:
    """Catalog mill row: identity only. Pair bodies live in JSONL."""

    return {
        "mill_id": record["mill_id"],
        "path": record["path"],
        "blob_sha": record["blob_sha"],
        "sha256": record["sha256"],
        "kind": record["kind"],
        "shape": record["shape"],
        "catalog_first": record["catalog_first"],
        "n_rounds": record["n_rounds"],
        "n_rows": record["n_rows"],
        "n_hops": record["n_hops"],
        "first_slug": record["first_slug"],
        "last_slug": record["last_slug"],
        "generator": record["generator"],
        "factory": record["factory"],
        "hops": list(record["hops"]),
        "loads_sibling": record.get("loads_sibling", ""),
        "source_lines": record["source_lines"],
        "doc_first_line": record["doc_first_line"],
    }


def catalog_document(mills: list[dict[str, Any]]) -> dict[str, Any]:
    pair_rows = sum(mill["n_rows"] for mill in mills)
    return {
        "schema": CATALOG_SCHEMA_ID,
        "family": "sir",
        "source_ref": LEGACY_REF,
        "preserve_commit": PRESERVE_COMMIT,
        "factory": FACTORY,
        "generator": GENERATOR,
        "slice": SLICE_ID,
        "extraction": (
            "AST literals only; leftover mill / loop publishers were never imported or executed"
        ),
        "n_mills": len(mills),
        "n_pair_rows": pair_rows,
        "n_source_files": len(mills),
        "mills": {mill["mill_id"]: mill_summary(mill) for mill in mills},
    }


def dumps_catalog(document: Mapping[str, Any]) -> str:
    return json.dumps(document, ensure_ascii=True, indent=2, sort_keys=True) + "\n"


def dumps_pair_row(row: Mapping[str, Any]) -> str:
    payload = {key: row[key] for key in PAIR_FIELD_ORDER}
    return json.dumps(payload, ensure_ascii=True, separators=(",", ":"))


def dumps_pairs(mills: list[dict[str, Any]]) -> str:
    lines = [dumps_pair_row(row) for mill in mills for row in mill["pairs"]]
    return "\n".join(lines) + "\n"


def catalog_json_path(package_dir: Path | None = None) -> Path:
    root = package_dir if package_dir is not None else Path(__file__).resolve().parent
    return root / CATALOG_FILENAME


def pairs_jsonl_path(package_dir: Path | None = None) -> Path:
    root = package_dir if package_dir is not None else Path(__file__).resolve().parent
    return root / PAIRS_FILENAME


def write_catalog_files(mills: list[dict[str, Any]], package_dir: Path | None = None) -> None:
    catalog_json_path(package_dir).write_text(
        dumps_catalog(catalog_document(mills)), encoding="utf-8"
    )
    pairs_jsonl_path(package_dir).write_text(dumps_pairs(mills), encoding="utf-8")
