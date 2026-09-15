#!/usr/bin/env python3
"""AST-extract SSR catalog identity from a mill source.

Evaluates only literal catalog assignments and constructor keyword arguments.
Does not import, compile, or exec the mill publisher, so ``ssr-mill*.py``
stay off this branch.
"""

from __future__ import annotations

import ast
import hashlib
import json
import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from .catalog_ast import (
    UNSET,
    assignment_of,
    ctor_identity,
    extract_joined_path_assignment,
    literal_value,
    spec_from_file_name,
)
from .vocabulary import (
    CATALOG_FILENAME,
    CATALOG_SCHEMA_ID,
    DEFERRED_PAIR_KEYS,
    FACTORY,
    GENERATOR,
    KIND_FAST,
    KIND_LOOP,
    KIND_PAIRS,
    LEGACY_REF,
    PAIRS_FILENAME,
    PRESERVE_COMMIT,
    SLICE_ID,
    SLICE_MILL_ID,
    SOURCE_FILE_COUNT,
)

SHAPE_LITERAL = "pairs-literal"
SHAPE_PLANT = "pairs-plant"
SHAPE_S = "pairs-s"
SHAPE_ROWS = "rows-generated"
SHAPE_TAILS = "tails-generated"
SHAPE_FAST = "fast-runtime"
SHAPE_LOOP = "loop"
_ROUND_RE = re.compile(r"-r(\d+)")
_CATALOG_JSON_RE = re.compile(r"^\.?ssr-catalog-r\d+\.json$")


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def mill_id_for_path(path: str) -> str:
    return Path(path).stem


def catalog_first_from_name(path: str) -> int | None:
    match = _ROUND_RE.search(Path(path).stem)
    return int(match.group(1)) if match else None


def extract_mill_catalog(
    source: str,
    *,
    path: str,
    blob_sha: str = "",
) -> dict[str, Any]:
    """Structured catalog extract for one SSR source file."""

    payload = source.encode()
    tree = ast.parse(source, filename=path)
    mill_id = mill_id_for_path(path)
    constants = _module_constants(tree)
    factory = constants.get("FACTORY", FACTORY)
    generator = constants.get("GEN", constants.get("GENERATOR", GENERATOR))
    catalog_first = constants.get("CATALOG_FIRST")
    if not isinstance(catalog_first, int):
        catalog_first = catalog_first_from_name(path)
    kind = _kind_of(path)
    record = _extract_shape(tree, path=path, kind=kind)
    record.update(
        {
            "mill_id": mill_id,
            "path": path,
            "blob_sha": blob_sha,
            "sha256": sha256_bytes(payload),
            "kind": kind,
            "catalog_first": catalog_first,
            "generator": generator,
            "factory": factory,
            "exec_target": spec_from_file_name(tree),
            "companion_mill_path": extract_companion_path(source),
            "catalog_json": _catalog_json_name(tree),
        }
    )
    return record


def _kind_of(path: str) -> str:
    name = Path(path).name
    if name == "ssr_mill_fast.py":
        return KIND_FAST
    if name.startswith("ssr-loop-"):
        return KIND_LOOP
    return KIND_PAIRS


def _module_constants(tree: ast.AST) -> dict[str, Any]:
    env: dict[str, Any] = {}
    for node in getattr(tree, "body", ()):
        name, value = assignment_of(node)
        if name is None or value is None:
            continue
        resolved = literal_value(value, env)
        if resolved is not UNSET:
            env[name] = resolved
    return env


def _extract_shape(tree: ast.AST, *, path: str, kind: str) -> dict[str, Any]:
    if kind == KIND_FAST:
        return _empty_record(SHAPE_FAST)
    if kind == KIND_LOOP:
        return _empty_record(SHAPE_LOOP)
    literal = _literal_pairs(tree)
    if literal is not None:
        return literal
    ctor = _ctor_pairs(tree)
    if ctor is not None:
        return ctor
    rows = _rows_pairs(tree)
    if rows is not None:
        return rows
    tails = _tails_record(tree)
    if tails is not None:
        return tails
    raise ValueError(f"{path} has no extractable SSR catalog assignment")


def _empty_record(shape: str) -> dict[str, Any]:
    return {
        "shape": shape,
        "n_rows": 0,
        "first_slug": None,
        "last_slug": None,
        "pairs": [],
    }


def _literal_pairs(tree: ast.AST) -> dict[str, Any] | None:
    for node in getattr(tree, "body", ()):
        name, value = assignment_of(node)
        if name != "PAIRS" or not isinstance(value, ast.List) or not value.elts:
            continue
        if not all(_is_dict_pair(elt) for elt in value.elts):
            continue
        rows = []
        for elt in value.elts:
            assert isinstance(elt, ast.Tuple)
            success = literal_value(elt.elts[0])
            fail = literal_value(elt.elts[1])
            if not isinstance(success, dict) or not isinstance(fail, dict):
                return None
            rows.append(_pair_row(success, fail))
        if rows and rows[0]["success_slug"]:
            return _rows_record(SHAPE_LITERAL, rows)
    return None


def _ctor_pairs(tree: ast.AST) -> dict[str, Any] | None:
    for node in getattr(tree, "body", ()):
        name, value = assignment_of(node)
        if name != "PAIRS" or not isinstance(value, ast.List) or not value.elts:
            continue
        first = _ctor_pair(value.elts[0])
        if first is None:
            continue
        rows = []
        ctor_shape = SHAPE_S if _tuple_ctor_name(value.elts[0]) == "S" else SHAPE_PLANT
        for elt in value.elts:
            pair = _ctor_pair(elt)
            if pair is None:
                return None
            rows.append(pair)
        return _rows_record(ctor_shape, rows)
    return None


def _rows_pairs(tree: ast.AST) -> dict[str, Any] | None:
    for node in getattr(tree, "body", ()):
        name, value = assignment_of(node)
        if name != "ROWS" or not isinstance(value, ast.List) or not value.elts:
            continue
        resolved = literal_value(value)
        if not isinstance(resolved, list) or not resolved:
            return None
        plants: list[dict[str, str | None]] = []
        for item in resolved:
            if not isinstance(item, tuple) or len(item) < 2:
                return None
            scanner, tail = item[0], item[1]
            if not isinstance(scanner, str) or not isinstance(tail, str):
                return None
            plants.append({"slug": f"{scanner}-{tail}", "scanner": scanner})
        if len(plants) % 2:
            return None
        rows = [
            _pair_row(plants[index], plants[index + 1])
            for index in range(0, len(plants), 2)
        ]
        return _rows_record(SHAPE_ROWS, rows)
    return None


def _tails_record(tree: ast.AST) -> dict[str, Any] | None:
    tails: list[str] | None = None
    scanners: list[str] | None = None
    for node in getattr(tree, "body", ()):
        name, value = assignment_of(node)
        if name == "TAILS" and value is not None:
            resolved = literal_value(value)
            if isinstance(resolved, list) and resolved and all(
                isinstance(item, str) for item in resolved
            ):
                tails = [str(item) for item in resolved]
        if name == "SCAN" and isinstance(value, ast.Dict):
            resolved = literal_value(value)
            if isinstance(resolved, dict):
                scanners = [str(key) for key in resolved if isinstance(key, str)]
    if tails is None or len(tails) < 2:
        return None
    n_rows = len(tails) // 2
    last_success_tail = tails[-2]
    first_slug = None
    last_slug = None
    scanners = scanners or []
    if scanners:
        first_slug = _tail_slug(scanners, tails, 0)
        last_slug = _tail_slug(scanners, tails, len(tails) - 2)
    return {
        "shape": SHAPE_TAILS,
        "n_rows": n_rows,
        "n_tails": len(tails),
        "first_tail": tails[0],
        "last_tail": tails[-1],
        "last_success_tail": last_success_tail,
        "first_slug": first_slug,
        "last_slug": last_slug,
        "scanners": scanners,
        "tails": tails,
        "pairs": tail_pair_rows(scanners, tails),
    }


def _tail_slug(scanners: list[str], tails: list[str], index: int) -> str:
    return f"{scanners[index % len(scanners)]}-{tails[index]}-leftover"


def tail_pair_rows(scanners: list[str], tails: list[str]) -> list[dict[str, Any]]:
    """Pair successive generated leftover plants; does not exec the mill."""

    if not scanners or len(tails) < 2:
        return []
    n_rows = len(tails) // 2
    rows = []
    for index in range(n_rows):
        success_index = index * 2
        fail_index = success_index + 1
        success = {
            "scanner": scanners[success_index % len(scanners)],
            "slug": _tail_slug(scanners, tails, success_index),
        }
        fail = {
            "scanner": scanners[fail_index % len(scanners)],
            "slug": _tail_slug(scanners, tails, fail_index),
        }
        rows.append(_pair_row(success, fail))
    return rows


def _is_dict_pair(node: ast.AST) -> bool:
    if not isinstance(node, ast.Tuple) or len(node.elts) != 2:
        return False
    return all(isinstance(elt, ast.Dict) for elt in node.elts)


def _ctor_pair(node: ast.AST) -> dict[str, Any] | None:
    if not isinstance(node, ast.Tuple) or len(node.elts) != 2:
        return None
    success = ctor_identity(node.elts[0])
    fail = ctor_identity(node.elts[1])
    if success is None or fail is None:
        return None
    return _pair_row(success, fail)


def _tuple_ctor_name(node: ast.AST) -> str | None:
    if not isinstance(node, ast.Tuple) or not node.elts:
        return None
    func = node.elts[0]
    if isinstance(func, ast.Call) and isinstance(func.func, ast.Name):
        return func.func.id
    return None


def _pair_row(success: Mapping[str, Any], fail: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "fail_scanner": fail.get("scanner"),
        "fail_slug": fail.get("slug"),
        "success_scanner": success.get("scanner"),
        "success_slug": success.get("slug"),
    }


def _rows_record(shape: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "shape": shape,
        "n_rows": len(rows),
        "first_slug": rows[0]["success_slug"],
        "last_slug": rows[-1]["success_slug"],
        "pairs": rows,
    }


def extract_companion_path(source: str) -> str | None:
    """``MILL`` joined-path constant from a loop script."""

    return extract_joined_path_assignment(source, "MILL")


def _catalog_json_name(tree: ast.AST) -> str | None:
    for node in ast.walk(tree):
        if not isinstance(node, ast.Constant) or not isinstance(node.value, str):
            continue
        name = Path(node.value).name
        if _CATALOG_JSON_RE.match(name):
            return name
    return None


def mill_summary(record: Mapping[str, Any], *, include_pairs: bool) -> dict[str, Any]:
    """Catalog mill row: identity plus optional compact pair list."""

    summary = {
        "mill_id": record["mill_id"],
        "path": record["path"],
        "blob_sha": record["blob_sha"],
        "sha256": record["sha256"],
        "kind": record["kind"],
        "shape": record["shape"],
        "catalog_first": record["catalog_first"],
        "n_rows": record["n_rows"],
        "first_slug": record["first_slug"],
        "last_slug": record["last_slug"],
        "generator": record["generator"],
        "factory": record["factory"],
    }
    if record["shape"] == SHAPE_TAILS:
        summary["n_tails"] = record.get("n_tails")
        summary["first_tail"] = record.get("first_tail")
        summary["last_tail"] = record.get("last_tail")
        summary["last_success_tail"] = record.get("last_success_tail")
        if record.get("exec_target"):
            summary["exec_target"] = record["exec_target"]
    if include_pairs:
        summary["pairs"] = list(record.get("pairs") or ())
    return summary


def inherited_scanners(records: list[Mapping[str, Any]]) -> list[str]:
    """``SCAN`` keys from the latest mill that defined them as a literal dict."""

    found: list[str] = []
    for record in records:
        scanners = record.get("scanners")
        if isinstance(scanners, list) and scanners:
            found = [str(item) for item in scanners]
    return found


def summarize_catalog_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Apply inherited SCAN keys and keep pair rows only on the r181 slice."""

    scanners = inherited_scanners(records)
    mills = []
    for record in records:
        if record.get("kind") != KIND_PAIRS:
            continue
        filled = apply_inherited_scanners(record, scanners)
        mills.append(
            mill_summary(filled, include_pairs=filled["mill_id"] == SLICE_MILL_ID)
        )
    return mills


def catalog_document(mills: list[dict[str, Any]]) -> dict[str, Any]:
    pair_rows = sum(int(mill["n_rows"]) for mill in mills)
    return {
        "extract": {
            "exec": False,
            "method": "ast.parse",
            "source_commit": PRESERVE_COMMIT,
            "source_files": SOURCE_FILE_COUNT,
            "source_ref": LEGACY_REF,
        },
        "factory": FACTORY,
        "generator": GENERATOR,
        "mills": {mill["mill_id"]: mill for mill in mills},
        "n_mills": len(mills),
        "n_pair_rows": pair_rows,
        "preserve_commit": PRESERVE_COMMIT,
        "schema": CATALOG_SCHEMA_ID,
        "slice": SLICE_ID,
        "source_ref": LEGACY_REF,
    }


def dumps_catalog(document: Mapping[str, Any]) -> str:
    return json.dumps(document, ensure_ascii=True, indent=2, sort_keys=True) + "\n"


def catalog_json_path(package_dir: Path | None = None) -> Path:
    root = package_dir if package_dir is not None else Path(__file__).resolve().parent
    return root / CATALOG_FILENAME


def pairs_jsonl_path(package_dir: Path | None = None) -> Path:
    root = package_dir if package_dir is not None else Path(__file__).resolve().parent
    return root / PAIRS_FILENAME


def write_catalog_document(document: Mapping[str, Any], path: Path | None = None) -> Path:
    destination = path if path is not None else catalog_json_path()
    destination.write_text(dumps_catalog(document), encoding="utf-8")
    return destination


def compact_deferred_pair(record: Mapping[str, Any], pair: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "fail_scanner": pair["fail_scanner"],
        "fail_slug": pair["fail_slug"],
        "mill_id": record["mill_id"],
        "path": record["path"],
        "success_scanner": pair["success_scanner"],
        "success_slug": pair["success_slug"],
    }


def dumps_pairs_jsonl(rows: list[Mapping[str, Any]]) -> str:
    """One compact object per deferred pair. Trailing newline. No CR."""

    lines = [
        json.dumps(
            {key: row[key] for key in DEFERRED_PAIR_KEYS},
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
        )
        for row in rows
    ]
    return "\n".join(lines) + "\n"


def write_pairs_jsonl(rows: list[Mapping[str, Any]], path: Path | None = None) -> Path:
    destination = path if path is not None else pairs_jsonl_path()
    destination.write_text(dumps_pairs_jsonl(rows), encoding="utf-8")
    return destination


def deferred_pair_rows(
    records: list[dict[str, Any]],
    *,
    expected_rows: int | None = None,
) -> list[dict[str, Any]]:
    """Compact pair bodies for every mill except the committed r181 slice."""

    scanners = inherited_scanners(records)
    rows: list[dict[str, Any]] = []
    for record in records:
        if record.get("kind") != KIND_PAIRS or record["mill_id"] == SLICE_MILL_ID:
            continue
        filled = apply_inherited_scanners(record, scanners)
        pairs = list(filled.get("pairs") or ())
        if len(pairs) != filled["n_rows"]:
            raise ValueError(
                f"{filled['mill_id']} deferred pairs {len(pairs)} != n_rows {filled['n_rows']}"
            )
        rows.extend(compact_deferred_pair(filled, pair) for pair in pairs)
    if expected_rows is not None and len(rows) != expected_rows:
        raise ValueError(f"deferred pair rows {len(rows)} != pin {expected_rows}")
    return rows


def apply_inherited_scanners(
    record: dict[str, Any],
    scanners: list[str],
) -> dict[str, Any]:
    """Fill tails slugs from a parent mill's AST-extracted ``SCAN`` keys."""

    if record.get("shape") != SHAPE_TAILS:
        return record
    updated = dict(record)
    if not record.get("first_slug"):
        first_tail = record.get("first_tail")
        last_success_tail = record.get("last_success_tail")
        n_tails = record.get("n_tails")
        if scanners and isinstance(first_tail, str) and isinstance(n_tails, int):
            updated["first_slug"] = f"{scanners[0]}-{first_tail}-leftover"
            if isinstance(last_success_tail, str) and n_tails >= 2:
                last_index = n_tails - 2
                updated["last_slug"] = (
                    f"{scanners[last_index % len(scanners)]}-{last_success_tail}-leftover"
                )
    tails = record.get("tails")
    local = record.get("scanners")
    if isinstance(local, list) and local:
        chosen = [str(item) for item in local]
    else:
        chosen = list(scanners)
    if (
        chosen
        and isinstance(tails, list)
        and len(tails) >= 2
        and not updated.get("pairs")
    ):
        updated["pairs"] = tail_pair_rows(chosen, [str(item) for item in tails])
    return updated if updated != record else record
