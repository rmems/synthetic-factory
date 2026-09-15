#!/usr/bin/env python3
"""AST-extract AMC catalog identity from a mill source.

Walks ``PAIRS`` / ``NEW`` / ``CATALOG`` / GC-TOOL-NBACK-DOOR tables.
Does not import, compile, or exec the mill publisher, so ``amc-mill*.py``
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
    call_kwargs,
    call_name,
    call_posargs,
    extract_joined_path_assignment,
    literal_value,
    module_literals,
)
from .vocabulary import (
    CATALOG_FILENAME,
    CATALOG_SCHEMA_ID,
    FACTORY,
    GENERATOR,
    KIND_LEFTOVER,
    KIND_PAIRS,
    L_CTOR,
    LEGACY_REF,
    P_CTOR,
    PAIR_CTOR_NAMES,
    PREFIX_MILL_ID,
    PREFIX_SLICE,
    PRESERVE_COMMIT,
    SHAPE_FAIL_SUCC,
    SHAPE_FS,
    SHAPE_L,
    SHAPE_LEFTOVER,
    SHAPE_P,
    SHAPE_PREFIX_NEW,
    SHAPE_TABLE_ZIP,
)

_ROUND_RE = re.compile(r"r(\d+)")


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def mill_id_for_path(path: str) -> str:
    return Path(path).stem


def catalog_first_from_name(path: str) -> int | None:
    match = _ROUND_RE.search(Path(path).stem)
    return int(match.group(1)) if match else None


def extract_companion_path(source: str) -> str | None:
    """``MILL_PATH`` joined-path constant from a loop script."""

    return extract_joined_path_assignment(source, "MILL_PATH")


def extract_mill_catalog(
    source: str,
    *,
    path: str,
    blob_sha: str = "",
) -> dict[str, Any]:
    """Structured catalog extract for one mill source file."""

    payload = source.encode()
    tree = ast.parse(source, filename=path)
    mill_id = mill_id_for_path(path)
    constants = module_literals(tree)
    factory = constants.get("FACTORY", FACTORY)
    generator = constants.get("GEN", GENERATOR)
    catalog_first = constants.get("CATALOG_FIRST")
    if not isinstance(catalog_first, int):
        catalog_first = catalog_first_from_name(path)
    record = _extract_shape(tree, path=path, constants=constants)
    record.update(
        {
            "mill_id": mill_id,
            "path": path,
            "blob_sha": blob_sha,
            "sha256": sha256_bytes(payload),
            "catalog_first": catalog_first,
            "generator": generator,
            "factory": factory,
        }
    )
    if "max_rounds" not in record and isinstance(constants.get("MAX_ROUNDS"), int):
        record["max_rounds"] = constants["MAX_ROUNDS"]
    return record


def _extract_shape(tree: ast.AST, *, path: str, constants: Mapping[str, Any]) -> dict[str, Any]:
    leftover = _leftover_catalog(tree)
    if leftover is not None:
        return leftover
    prefix_new = _prefix_new(tree)
    if prefix_new is not None:
        return prefix_new
    table_zip = _table_zip(tree, constants=constants)
    if table_zip is not None:
        return table_zip
    literal = _literal_pairs(tree)
    if literal is not None:
        return literal
    raise ValueError(f"{path} has no extractable AMC catalog assignment")


def _assignments(tree: ast.AST) -> dict[str, ast.AST]:
    found: dict[str, ast.AST] = {}
    for node in getattr(tree, "body", ()):
        name, value = assignment_of(node)
        if name is not None and value is not None:
            found[name] = value
    return found


def _leftover_catalog(tree: ast.AST) -> dict[str, Any] | None:
    assigns = _assignments(tree)
    if "CATALOG" not in assigns or "PAIRS" in assigns:
        return None
    rows_lit = literal_value(assigns["CATALOG"])
    if not isinstance(rows_lit, list) or not rows_lit:
        return None
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(rows_lit):
        if not isinstance(row, dict) or "slug" not in row or "fail" not in row:
            raise ValueError(f"CATALOG[{index}] is not a leftover identity dict")
        rows.append(
            {
                "success_slug": row["slug"],
                "fail_slug": row["fail"],
                "mod": row.get("mod"),
                "token": row.get("token"),
            }
        )
    return _rows_record(SHAPE_LEFTOVER, KIND_LEFTOVER, rows, slug_key="success_slug")


def _prefix_new(tree: ast.AST) -> dict[str, Any] | None:
    assigns = _assignments(tree)
    pairs_node = assigns.get("PAIRS")
    new_node = assigns.get("NEW")
    slice_n = _prefix_slice_length(pairs_node)
    if slice_n is None or new_node is None:
        return None
    new_rows = _pair_list(new_node, where="NEW")
    if new_rows is None:
        return None
    return {
        "kind": KIND_PAIRS,
        "shape": SHAPE_PREFIX_NEW,
        "n_rows": slice_n + len(new_rows),
        "n_prefix": slice_n,
        "n_new": len(new_rows),
        "prefix_mill": PREFIX_MILL_ID,
        "first_slug": new_rows[0]["fail_slug"],
        "last_slug": new_rows[-1]["fail_slug"],
        "pairs": new_rows,
    }


def _prefix_slice_length(node: ast.AST | None) -> int | None:
    """``list(<name>.PAIRS[:N]) + NEW`` → ``N``."""

    if node is None or not isinstance(node, ast.BinOp) or not isinstance(node.op, ast.Add):
        return None
    if not isinstance(node.right, ast.Name) or node.right.id != "NEW":
        return None
    left = node.left
    if not isinstance(left, ast.Call) or call_name(left) != "list" or len(left.args) != 1:
        return None
    sub = left.args[0]
    if not isinstance(sub, ast.Subscript) or not isinstance(sub.slice, ast.Slice):
        return None
    upper = sub.slice.upper
    if not isinstance(upper, ast.Constant) or not isinstance(upper.value, int):
        return None
    if sub.slice.lower is not None or sub.slice.step is not None:
        return None
    if upper.value != PREFIX_SLICE:
        return None
    return upper.value


def _table_zip(tree: ast.AST, *, constants: Mapping[str, Any]) -> dict[str, Any] | None:
    assigns = _assignments(tree)
    pairs_node = assigns.get("PAIRS")
    if not isinstance(pairs_node, ast.Call) or call_name(pairs_node) != "_build_pairs":
        return None
    required = ("GC", "TOOL", "NBACK", "DOOR")
    if any(name not in constants for name in required):
        return None
    rows = zip_table_pairs(
        constants["GC"],
        constants["TOOL"],
        constants["NBACK"],
        constants["DOOR"],
    )
    return _rows_record(SHAPE_TABLE_ZIP, KIND_PAIRS, rows)


def zip_table_pairs(
    gc: list[Any],
    tool: list[Any],
    nback: list[Any],
    door: list[Any],
) -> list[dict[str, Any]]:
    """Rebuild r424's group-interleaved catalog from the four tables."""

    gc_pairs = [_table_slugs(stem) for stem, _noun, _attr in gc]
    tool_pairs = [_table_slugs(f"tool-result-{codec}") for codec, _noun in tool]
    nback_pairs = [_table_slugs(f"nback-{kind}-lure") for kind, _lag, _attr in nback]
    door_pairs = [_table_slugs(f"doorway-{place}") for place, _noun, _attr in door]
    groups = (gc_pairs, tool_pairs, nback_pairs, door_pairs)
    nmax = max(len(group) for group in groups)
    out: list[dict[str, Any]] = []
    for index in range(nmax):
        for group in groups:
            if index < len(group):
                out.append(group[index])
    return out


def _table_slugs(stem: str) -> dict[str, Any]:
    return {
        "fail_slug": f"{stem}-drops-pin",
        "success_slug": f"{stem}-pin-kept",
    }


def _literal_pairs(tree: ast.AST) -> dict[str, Any] | None:
    assigns = _assignments(tree)
    pairs_node = assigns.get("PAIRS")
    if pairs_node is None:
        return None
    rows = _pair_list(pairs_node, where="PAIRS")
    if rows is None:
        return None
    ctors = {(row["fail_ctor"], row["success_ctor"]) for row in rows}
    if ctors == {("F", "S")}:
        shape = SHAPE_FS
    elif ctors == {("fail", "succ")}:
        shape = SHAPE_FAIL_SUCC
    elif ctors == {(L_CTOR, L_CTOR)}:
        shape = SHAPE_L
    elif ctors == {(P_CTOR, P_CTOR)}:
        shape = SHAPE_P
    else:
        raise ValueError(f"PAIRS has mixed constructor shapes {sorted(ctors)}")
    compact = [_compact_pair(row) for row in rows]
    return _rows_record(shape, KIND_PAIRS, compact)


def _pair_list(node: ast.AST, *, where: str) -> list[dict[str, Any]] | None:
    if not isinstance(node, ast.List) or not node.elts:
        return None
    rows: list[dict[str, Any]] = []
    for index, elt in enumerate(node.elts):
        if not isinstance(elt, (ast.Tuple, ast.List)) or len(elt.elts) != 2:
            return None
        fail = _ctor_identity(elt.elts[0], where=f"{where}[{index}].fail")
        success = _ctor_identity(elt.elts[1], where=f"{where}[{index}].success")
        if fail is None or success is None:
            return None
        rows.append(
            {
                "fail_slug": fail["slug"],
                "success_slug": success["slug"],
                "fail_leftover": fail.get("leftover"),
                "success_leftover": success.get("leftover"),
                "fail_ctor": fail["ctor"],
                "success_ctor": success["ctor"],
            }
        )
    return rows


def _ctor_identity(node: ast.AST, *, where: str) -> dict[str, Any] | None:
    name = call_name(node)
    if name not in PAIR_CTOR_NAMES:
        return None
    kwargs = call_kwargs(node) or {}
    args = call_posargs(node) or []
    slug: Any = kwargs.get("slug")
    leftover: Any = kwargs.get("leftover")
    if name == P_CTOR and len(args) >= 6:
        slug = args[0]
        leftover = args[5]
    elif name == L_CTOR and slug is None and len(args) >= 8:
        slug = args[0]
        leftover = args[7]
    if not isinstance(slug, str):
        raise ValueError(f"{where}: {name}() has no string slug")
    identity: dict[str, Any] = {"ctor": name, "slug": slug}
    if isinstance(leftover, str):
        identity["leftover"] = leftover
    return identity


def _compact_pair(row: Mapping[str, Any]) -> dict[str, Any]:
    compact = {
        "fail_slug": row["fail_slug"],
        "success_slug": row["success_slug"],
    }
    if row.get("fail_leftover"):
        compact["fail_leftover"] = row["fail_leftover"]
    if row.get("success_leftover"):
        compact["success_leftover"] = row["success_leftover"]
    return compact


def _rows_record(
    shape: str,
    kind: str,
    rows: list[dict[str, Any]],
    *,
    slug_key: str = "fail_slug",
) -> dict[str, Any]:
    return {
        "kind": kind,
        "shape": shape,
        "n_rows": len(rows),
        "first_slug": rows[0][slug_key],
        "last_slug": rows[-1][slug_key],
        "pairs": rows,
    }


def compose_family(records: Mapping[str, Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Apply the r280 prefix slice, then return mill summaries."""

    composed: list[dict[str, Any]] = []
    for mill_id, record in records.items():
        if record.get("shape") != SHAPE_PREFIX_NEW:
            composed.append(mill_summary(record, include_pairs=True))
            continue
        prefix_id = record["prefix_mill"]
        if prefix_id not in records:
            raise ValueError(f"{mill_id} prefix mill {prefix_id} was not extracted")
        prefix_pairs = list(records[prefix_id]["pairs"][: record["n_prefix"]])
        pairs = prefix_pairs + list(record["pairs"])
        merged = dict(record)
        merged["pairs"] = pairs
        merged["n_rows"] = len(pairs)
        merged["first_slug"] = pairs[0]["fail_slug"]
        merged["last_slug"] = pairs[-1]["fail_slug"]
        composed.append(mill_summary(merged, include_pairs=True))
    return composed


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
    if record.get("max_rounds") is not None:
        summary["max_rounds"] = record["max_rounds"]
    if record["shape"] == SHAPE_PREFIX_NEW:
        summary["n_prefix"] = record["n_prefix"]
        summary["n_new"] = record["n_new"]
        summary["prefix_mill"] = record["prefix_mill"]
    if include_pairs:
        summary["pairs"] = [_public_pair(row) for row in record.get("pairs") or ()]
    return summary


def _public_pair(row: Mapping[str, Any]) -> dict[str, Any]:
    public = {key: row[key] for key in row if key not in {"fail_ctor", "success_ctor"}}
    return public


def catalog_document(mills: list[dict[str, Any]]) -> dict[str, Any]:
    pair_rows = sum(mill["n_rows"] for mill in mills)
    return {
        "schema": CATALOG_SCHEMA_ID,
        "source_ref": LEGACY_REF,
        "preserve_commit": PRESERVE_COMMIT,
        "factory": FACTORY,
        "generator": GENERATOR,
        "n_mills": len(mills),
        "n_pair_rows": pair_rows,
        "mills": {mill["mill_id"]: mill for mill in mills},
    }


def dumps_catalog(document: Mapping[str, Any]) -> str:
    return json.dumps(document, ensure_ascii=True, indent=2, sort_keys=True) + "\n"


def catalog_json_path(package_dir: Path | None = None) -> Path:
    root = package_dir if package_dir is not None else Path(__file__).resolve().parent
    return root / CATALOG_FILENAME


def write_catalog_document(document: Mapping[str, Any], path: Path | None = None) -> Path:
    destination = path if path is not None else catalog_json_path()
    destination.write_text(dumps_catalog(document), encoding="utf-8")
    return destination
