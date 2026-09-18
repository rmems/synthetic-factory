#!/usr/bin/env python3
"""AST-extract ACM catalog rows from a legacy mill tree.

Reads ``acm-mill*.py`` only as parse input. Never copies, writes, or execs
those files. Destination trees may not contain a vendored mill script.
``ast.parse`` is the only interpreter step.
"""

from __future__ import annotations

import ast
import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from . import _contract
from . import catalog as cat
from ._contract import VENDOR_PREFIX, refuse_vendor_paths

UNSET = object()
PLANT_CALLS = frozenset({"plant", "p", "ok", "bad"})
PLANT_FIELDS = (
    "slug", "domain", "success", "name", "stack", "field", "old", "new",
    "fail_err", "plan", "residual", "vs", "fetch1", "fetch1_ok", "fetch2",
    "fetch2_ok",
)
MILL_NAME_RE = re.compile(r"^acm-mill-.+\.py$")
KIND_MILL = "mill"
KIND_LOOP = "loop"
KIND_PLANTS = "plant-gen"
KIND_PAIRS = "mill-pairs"
KIND_GEN = "plant-gen"
KIND_BY_PREFIX = (
    (VENDOR_PREFIX, KIND_MILL),
    ("acm-pairs-", KIND_MILL),
    ("acm-loop-", KIND_LOOP),
    ("_gen_acm_plants_", KIND_PLANTS),
)

__all__ = ["extract_tree", "refuse_vendor_paths"]


def extract_tree(source_root: Path) -> dict[str, Any]:
    """Parse every ACM source file under ``source_root`` and merge pair rows."""

    records = _collect_records(source_root.resolve())
    return cat.catalog_payload(
        rows=_merge_rows(records),
        sources=sorted((item["source"] for item in records), key=lambda s: s["path"]),
        bans=_merged_bans(records),
        source_files=len(records),
    )


def assignment_of(node: ast.stmt) -> tuple[str | None, ast.AST | None]:
    """Return ``(name, value)`` for a simple ``NAME = value`` statement."""

    if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
        return node.target.id, node.value
    if isinstance(node, ast.Assign) and len(node.targets) == 1:
        target = node.targets[0]
        if isinstance(target, ast.Name):
            return target.id, node.value
    return None, None


def literal_value(node: ast.AST, env: Mapping[str, Any]) -> Any:
    """Resolve a constant, name, f-string, or string add; else ``UNSET``."""

    resolver = _LITERAL.get(type(node))
    return UNSET if resolver is None else resolver(node, env)


def _literal_constant(node: ast.Constant, _env: Mapping[str, Any]) -> Any:
    return node.value


def _literal_name(node: ast.Name, env: Mapping[str, Any]) -> Any:
    return env[node.id] if node.id in env else UNSET


def _literal_attr(node: ast.Attribute, env: Mapping[str, Any]) -> Any:
    return env[node.attr] if node.attr in env else UNSET


def _literal_joined(node: ast.JoinedStr, env: Mapping[str, Any]) -> Any:
    parts: list[str] = []
    for value in node.values:
        if isinstance(value, ast.Constant):
            parts.append("" if value.value is None else str(value.value))
            continue
        if not isinstance(value, ast.FormattedValue):
            return UNSET
        inner = literal_value(value.value, env)
        if inner is UNSET or not isinstance(inner, (str, int)):
            return UNSET
        parts.append(str(inner))
    return "".join(parts)


def _literal_add(node: ast.BinOp, env: Mapping[str, Any]) -> Any:
    if not isinstance(node.op, ast.Add):
        return UNSET
    left = literal_value(node.left, env)
    right = literal_value(node.right, env)
    if isinstance(left, str) and isinstance(right, str):
        return left + right
    return UNSET


_LITERAL = {
    ast.Constant: _literal_constant,
    ast.Name: _literal_name,
    ast.Attribute: _literal_attr,
    ast.JoinedStr: _literal_joined,
    ast.BinOp: _literal_add,
}


def module_env(tree: ast.AST) -> dict[str, Any]:
    """Collect module-level string/int/bool names used to join fetch URLs."""

    env: dict[str, Any] = {}
    statements = list(getattr(tree, "body", ()))
    for node in statements:
        name, value = assignment_of(node)
        if name is None or value is None:
            continue
        if isinstance(value, ast.Constant) and isinstance(value.value, (str, int, bool)):
            env[name] = value.value
    for node in statements:
        name, value = assignment_of(node)
        if name is None or value is None or name in env:
            continue
        resolved = literal_value(value, env)
        if resolved is not UNSET and isinstance(resolved, (str, int, bool)):
            env[name] = resolved
    return env


def string_tuple(node: ast.AST, env: Mapping[str, Any]) -> tuple[str, ...]:
    """Strings from a tuple literal; skip unresolved elts."""

    if not isinstance(node, (ast.Tuple, ast.List)):
        return ()
    values: list[str] = []
    for elt in node.elts:
        item = literal_value(elt, env)
        if isinstance(item, str):
            values.append(item)
    return tuple(values)


def plant_kwargs(node: ast.AST, env: Mapping[str, Any]) -> dict[str, Any] | None:
    """Keyword arguments of a ``plant`` / ``p`` / ``ok`` / ``bad`` call."""

    if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Name):
        return None
    if node.func.id not in PLANT_CALLS:
        return None
    out: dict[str, Any] = {}
    for keyword in node.keywords:
        if keyword.arg is None or keyword.arg not in PLANT_FIELDS:
            continue
        value = literal_value(keyword.value, env)
        if value is not UNSET:
            out[keyword.arg] = value
    if node.func.id == "ok":
        out.setdefault("success", True)
    elif node.func.id == "bad":
        out.setdefault("success", False)
    if not isinstance(out.get("slug"), str) or not out["slug"]:
        return None
    return out


def pair_elts(
    node: ast.AST, env: Mapping[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]] | None:
    """One ``(success_plant, fail_plant)`` tuple from a ``PAIRS`` list."""

    if not isinstance(node, ast.Tuple) or len(node.elts) != 2:
        return None
    success = plant_kwargs(node.elts[0], env)
    fail = plant_kwargs(node.elts[1], env)
    if success is None or fail is None:
        return None
    return success, fail


def _kind_of(name: str) -> str | None:
    if not name.endswith(".py"):
        return None
    for prefix, kind in KIND_BY_PREFIX:
        if name.startswith(prefix):
            return kind
    return None


def _catalog_id_for(name: str) -> str:
    stem = name[:-3] if name.endswith(".py") else name
    prefixes = ("acm-mill-", "acm-pairs-", "acm-loop-", "_gen_acm_plants_")
    for prefix in prefixes:
        if stem.startswith(prefix):
            rest = stem[len(prefix):]
            return f"plants-{rest}" if prefix.startswith("_gen_") else rest
    return stem


def _collect_records(root: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    shared_env: dict[str, Any] = {}
    for path in sorted(root.rglob("*.py")):
        if _kind_of(path.name) is None:
            continue
        record = _extract_file(root, path, shared_env)
        if record["source"]["kind"] == KIND_PLANTS:
            shared_env.update(record["env"])
        records.append(record)
    return records


def _extract_file(
    root: Path, path: Path, shared_env: dict[str, Any]
) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    tree = ast.parse(text, filename=str(path))
    env = dict(shared_env)
    env.update(module_env(tree))
    kind = _kind_of(path.name) or "unknown"
    rel = path.relative_to(root).as_posix()
    catalog_id = _catalog_id_for(path.name)
    pairs: list[cat.Pair] = []
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
) -> list[cat.Pair]:
    found: list[cat.Pair] = []
    for node in getattr(tree, "body", ()):
        name, value = assignment_of(node)
        if name != "PAIRS" or not isinstance(value, ast.List):
            continue
        for elt in value.elts:
            raw = pair_elts(elt, env)
            if raw is None:
                continue
            success, fail = raw
            found.append(
                cat.Pair(
                    catalog_id=catalog_id,
                    source=source,
                    kind=kind,
                    success=cat.plant_from_mapping(success),
                    fail=cat.plant_from_mapping(fail),
                )
            )
    return found


def _pairs_from_mills(tree: ast.AST, env: dict[str, Any], source: str) -> list[cat.Pair]:
    found: list[cat.Pair] = []
    for start, tuples in _mills_tables(tree, env).items():
        catalog_id = f"r{start}"
        for row in tuples:
            pair = _pair_from_mill_tuple(catalog_id, source, row)
            if pair is not None:
                found.append(pair)
    return found


def _pair_from_mill_tuple(
    catalog_id: str, source: str, row: tuple[str, ...]
) -> cat.Pair | None:
    if len(row) < 5:
        return None
    success_slug, fail_slug, field, old, new = row[:5]
    fail_err = f"{row[5]}: leftover" if len(row) > 5 else ""
    fetch1 = row[6] if len(row) > 6 else ""
    fetch2 = row[8] if len(row) > 8 else ""
    return cat.Pair(
        catalog_id=catalog_id,
        source=source,
        kind=KIND_GEN,
        success=cat.plant_from_mapping(
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
        fail=cat.plant_from_mapping({"slug": fail_slug, "field": field}, success=False),
    )


def _mills_tables(tree: ast.AST, env: dict[str, Any]) -> dict[int, list[tuple[str, ...]]]:
    tables: dict[int, list[tuple[str, ...]]] = {}
    for node in getattr(tree, "body", ()):
        name, value = assignment_of(node)
        if name == "MILLS" and isinstance(value, ast.Dict):
            tables.update(_mills_dict(value, env))
            continue
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target = node.targets[0]
        if not isinstance(target, ast.Subscript) or not isinstance(node.value, ast.List):
            continue
        key = literal_value(target.slice, env)
        if isinstance(key, int):
            tables[key] = _mill_tuple_rows(node.value, env)
    return tables


def _mills_dict(node: ast.Dict, env: dict[str, Any]) -> dict[int, list[tuple[str, ...]]]:
    tables: dict[int, list[tuple[str, ...]]] = {}
    for key_node, value_node in zip(node.keys, node.values, strict=True):
        if key_node is None:
            continue
        key = literal_value(key_node, env)
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
        resolved = literal_value(item, env)
        values.append(resolved if isinstance(resolved, str) else "")
    return values


def _loop_mill_names(tree: ast.AST) -> list[str]:
    names = [
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant)
        and isinstance(node.value, str)
        and MILL_NAME_RE.match(node.value)
    ]
    return sorted(set(names))


def _bans_from_tree(tree: ast.AST, env: dict[str, Any]) -> dict[str, list[str]]:
    bans = {"slug_needles": [], "blob_keys": []}
    for node in getattr(tree, "body", ()):
        name, value = assignment_of(node)
        if name == "BANNED_SLUG_NEEDLES" and value is not None:
            bans["slug_needles"].extend(string_tuple(value, env))
        elif name == "BANNED_BLOB" and value is not None:
            bans["blob_keys"].extend(string_tuple(value, env))
    return bans


def _merged_bans(records: list[dict[str, Any]]) -> dict[str, list[str]]:
    bans: dict[str, list[str]] = {"slug_needles": [], "blob_keys": []}
    for record in records:
        for key, values in record["bans"].items():
            bans.setdefault(key, []).extend(values)
    return {key: sorted(set(values)) for key, values in bans.items()}


def _merge_rows(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
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
                rows.append(cat.row_from_pair(pair))
    rows.sort(key=_row_sort_key)
    return rows


def _row_sort_key(row: dict[str, Any]) -> tuple[int, int | str, str]:
    catalog_id = str(row["catalog_id"])
    if catalog_id.startswith("g46-w") and catalog_id[5:].isdigit():
        return (0, int(catalog_id[5:]), row["success_slug"])
    if catalog_id.startswith("r") and catalog_id[1:].isdigit():
        return (1, int(catalog_id[1:]), row["success_slug"])
    if catalog_id.startswith("plants-r") and catalog_id[8:].isdigit():
        return (2, int(catalog_id[8:]), row["success_slug"])
    return (3, catalog_id, row["success_slug"])


_contract.bind_import_twin(__name__)
