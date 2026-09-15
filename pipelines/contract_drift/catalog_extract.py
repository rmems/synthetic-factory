#!/usr/bin/env python3
"""AST-extract ACM catalog rows from a legacy mill tree.

Reads ``acm-mill*.py`` only as parse input. Never copies, writes, or execs
those files. Destination trees may not contain a vendored mill script.
"""

from __future__ import annotations

import argparse
import ast
import re
from pathlib import Path
from typing import Any

from . import _contract
from . import catalog as cat
from . import catalog_ast as cx
from . import identity
from . import plants
from .identity import refuse_vendor_paths

MILL_NAME_RE = re.compile(r"^acm-mill-.+\.py$")
KIND_MILL = "mill"
KIND_LOOP = "loop"
KIND_PLANTS = "plant-gen"
KIND_PAIRS = "mill-pairs"
KIND_GEN = "plant-gen"

__all__ = ["extract_tree", "main", "refuse_vendor_paths"]


def extract_tree(source_root: Path) -> dict[str, Any]:
    """Parse every ACM source file under ``source_root`` and merge pair rows."""

    root = source_root.resolve()
    files = _acm_files(root)
    sources: list[dict[str, Any]] = []
    records: list[dict[str, Any]] = []
    bans = {"slug_needles": [], "blob_keys": []}
    shared_env: dict[str, Any] = {}
    for path in files:
        record = _extract_file(root, path, shared_env)
        if record["source"]["kind"] == KIND_PLANTS:
            shared_env.update(record["env"])
        records.append(record)
        sources.append(record["source"])
        _extend_bans(bans, record["bans"])
    # Published mill PAIRS win; plant-gen tables only fill unpublished gaps.
    rows: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for kind in (KIND_PAIRS, KIND_GEN):
        for record in records:
            for pair in record["pairs"]:
                if pair.kind != kind:
                    continue
                key = (pair.success.slug, pair.fail.slug)
                if key in seen:
                    continue
                seen.add(key)
                rows.append(plants.row_from_pair(pair))
    rows.sort(key=_row_sort_key)
    sources.sort(key=lambda item: item["path"])
    return cat.catalog_payload(
        rows=rows,
        sources=sources,
        bans={key: sorted(set(values)) for key, values in bans.items()},
        source_files=len(files),
    )


def _acm_files(root: Path) -> list[Path]:
    found: list[Path] = []
    for path in sorted(root.rglob("*.py")):
        if _kind_of(path.name) is not None:
            found.append(path)
    return found


def _kind_of(name: str) -> str | None:
    if not name.endswith(".py"):
        return None
    if name.startswith(identity.VENDOR_PREFIX):
        return KIND_MILL
    # Cleaned / fixture pair catalogs. Never a vendored mill script.
    if name.startswith("acm-pairs-"):
        return KIND_MILL
    if name.startswith("acm-loop-"):
        return KIND_LOOP
    if name.startswith("_gen_acm_plants_"):
        return KIND_PLANTS
    return None


def _catalog_id_for(name: str) -> str:
    stem = name[:-3] if name.endswith(".py") else name
    prefixes = ("acm-mill-", "acm-pairs-", "acm-loop-", "_gen_acm_plants_")
    for prefix in prefixes:
        if stem.startswith(prefix):
            rest = stem[len(prefix) :]
            return f"plants-{rest}" if prefix.startswith("_gen_") else rest
    return stem


def _extract_file(
    root: Path, path: Path, shared_env: dict[str, Any] | None = None
) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    tree = ast.parse(text, filename=str(path))
    env = dict(shared_env or {})
    env.update(cx.module_env(tree))
    kind = _kind_of(path.name) or "unknown"
    rel = path.relative_to(root).as_posix()
    catalog_id = _catalog_id_for(path.name)
    pairs: list[plants.Pair] = []
    if kind == KIND_MILL:
        pairs.extend(_pairs_from_tree(tree, env, catalog_id, rel, KIND_PAIRS))
    elif kind == KIND_PLANTS:
        pairs.extend(_pairs_from_mills(tree, env, rel))
    source = {
        "path": rel,
        "kind": kind,
        "catalog_id": catalog_id,
        "pair_count": len(pairs),
        "loop_mills": _loop_mill_names(tree) if kind == KIND_LOOP else [],
        "sha256": cat.sha256_text(text),
    }
    return {
        "source": source,
        "pairs": pairs,
        "bans": _bans_from_tree(tree, env),
        "env": env,
    }


def _pairs_from_tree(
    tree: ast.AST,
    env: dict[str, Any],
    catalog_id: str,
    source: str,
    kind: str,
) -> list[plants.Pair]:
    found: list[plants.Pair] = []
    for node in getattr(tree, "body", ()):
        name, value = cx.assignment_of(node)
        if name != "PAIRS" or not isinstance(value, ast.List):
            continue
        for elt in value.elts:
            raw = cx.pair_elts(elt, env)
            if raw is None:
                continue
            success, fail = raw
            found.append(
                plants.Pair(
                    catalog_id=catalog_id,
                    source=source,
                    kind=kind,
                    success=plants.plant_from_mapping(success),
                    fail=plants.plant_from_mapping(fail),
                )
            )
    return found


def _pairs_from_mills(tree: ast.AST, env: dict[str, Any], source: str) -> list[plants.Pair]:
    found: list[plants.Pair] = []
    for start, tuples in _mills_tables(tree, env).items():
        catalog_id = f"r{start}"
        for row in tuples:
            if len(row) < 5:
                continue
            success_slug, fail_slug, field, old, new = row[:5]
            fail_err = f"{row[5]}: leftover" if len(row) > 5 else ""
            fetch1 = row[6] if len(row) > 6 else ""
            fetch2 = row[8] if len(row) > 8 else ""
            found.append(
                plants.Pair(
                    catalog_id=catalog_id,
                    source=source,
                    kind=KIND_GEN,
                    success=plants.plant_from_mapping(
                        {
                            "slug": success_slug,
                            "field": field,
                            "old": old,
                            "new": new,
                            "fail_err": fail_err,
                            "fetch1": fetch1,
                            "fetch2": fetch2,
                        },
                        success=True,
                    ),
                    fail=plants.plant_from_mapping(
                        {"slug": fail_slug, "field": field},
                        success=False,
                    ),
                )
            )
    return found


def _mills_tables(tree: ast.AST, env: dict[str, Any]) -> dict[int, list[tuple[str, ...]]]:
    tables: dict[int, list[tuple[str, ...]]] = {}
    for node in getattr(tree, "body", ()):
        name, value = cx.assignment_of(node)
        if name == "MILLS" and isinstance(value, ast.Dict):
            tables.update(_mills_dict(value, env))
            continue
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target = node.targets[0]
        if not isinstance(target, ast.Subscript) or not isinstance(node.value, ast.List):
            continue
        key = cx.literal_value(target.slice, env)
        if isinstance(key, int):
            tables[key] = _mill_tuple_rows(node.value, env)
    return tables


def _mills_dict(node: ast.Dict, env: dict[str, Any]) -> dict[int, list[tuple[str, ...]]]:
    tables: dict[int, list[tuple[str, ...]]] = {}
    for key_node, value_node in zip(node.keys, node.values, strict=True):
        if key_node is None:
            continue
        key = cx.literal_value(key_node, env)
        if isinstance(key, int) and isinstance(value_node, ast.List):
            tables[key] = _mill_tuple_rows(value_node, env)
    return tables


def _mill_tuple_rows(node: ast.List, env: dict[str, Any]) -> list[tuple[str, ...]]:
    rows: list[tuple[str, ...]] = []
    for elt in node.elts:
        values = _mill_tuple_values(elt, env)
        if values and values[0] and values[1]:
            rows.append(tuple(values))
    return rows


def _mill_tuple_values(node: ast.AST, env: dict[str, Any]) -> list[str]:
    """A raw 10-tuple or a ``P(...)`` call that builds the same row."""

    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "P":
        items = node.args
    elif isinstance(node, ast.Tuple):
        items = node.elts
    else:
        return []
    values: list[str] = []
    for item in items:
        resolved = cx.literal_value(item, env)
        values.append(resolved if isinstance(resolved, str) else "")
    return values


def _loop_mill_names(tree: ast.AST) -> list[str]:
    names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            if MILL_NAME_RE.match(node.value):
                names.append(node.value)
    return sorted(set(names))


def _bans_from_tree(tree: ast.AST, env: dict[str, Any]) -> dict[str, list[str]]:
    bans = {"slug_needles": [], "blob_keys": []}
    for node in getattr(tree, "body", ()):
        name, value = cx.assignment_of(node)
        if name == "BANNED_SLUG_NEEDLES" and value is not None:
            bans["slug_needles"].extend(cx.string_tuple(value, env))
        elif name == "BANNED_BLOB" and value is not None:
            bans["blob_keys"].extend(cx.string_tuple(value, env))
    return bans


def _extend_bans(dst: dict[str, list[str]], src: dict[str, list[str]]) -> None:
    for key, values in src.items():
        dst.setdefault(key, []).extend(values)


def _row_sort_key(row: dict[str, Any]) -> tuple[int, int | str, str]:
    catalog_id = str(row["catalog_id"])
    if catalog_id.startswith("g46-w") and catalog_id[5:].isdigit():
        return (0, int(catalog_id[5:]), row["success_slug"])
    if catalog_id.startswith("r") and catalog_id[1:].isdigit():
        return (1, int(catalog_id[1:]), row["success_slug"])
    if catalog_id.startswith("plants-r") and catalog_id[8:].isdigit():
        return (2, int(catalog_id[8:]), row["success_slug"])
    return (3, catalog_id, row["success_slug"])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="AST-extract the ACM catalog")
    parser.add_argument("source", type=Path, help="legacy tree that holds the mill scripts")
    parser.add_argument("--write", type=Path, default=None, help="new catalog directory")
    args = parser.parse_args(argv)
    payload = extract_tree(args.source)
    if args.write is None:
        print(cat.dumps_catalog(payload), end="")
        return 0
    dest = args.write.resolve()
    dest.mkdir(parents=True, exist_ok=False)
    refuse_vendor_paths(dest.rglob("*") if dest.exists() else ())
    cat.write_catalog(dest, payload)
    refuse_vendor_paths(dest.rglob("*"))
    print(cat.dumps_catalog({"row_count": payload["row_count"], "path": str(dest)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

_contract.bind_import_twin(__name__)
