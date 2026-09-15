#!/usr/bin/env python3
"""AST-extract leftover mill catalogs from a mill source.

Walks literal catalog assignments, list-extend ``AugAssign`` nodes, and the
r968 ``STEMS`` / ``build_catalogs`` unpack. Does not import, compile, or exec
the mill publisher, so ``lef-mill*.py`` stay off this branch.
"""

from __future__ import annotations

import ast
import hashlib
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from .catalog_ast import (
    UNSET,
    assignment_of,
    call_name,
    extract_joined_path_assignment,
    literal_value,
    tuple_assignment_names,
)
from .vocabulary import (
    CATALOG_ASSIGNMENT_NAMES,
    CATALOG_FILENAME,
    CATALOG_SCHEMA_ID,
    FACTORY,
    GENERATOR,
    KIND_SLUGS,
    KIND_STEMS,
    KIND_TABLES,
    LEGACY_REF,
    NUMS_FORMULA,
    PAIR_BUCKETS,
    PRESERVE_COMMIT,
    SHAPE_STEMS,
    SHAPE_TABLES,
    SLICE_ID,
    TABLE_FIELDS,
    TABLE_NAMES,
)


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def mill_id_for_path(path: str) -> str:
    return Path(path).stem


def catalog_first_from_name(path: str) -> int | None:
    stem = Path(path).stem
    marker = stem.rsplit("-r", 1)
    if len(marker) != 2 or not marker[1].isdigit():
        return None
    return int(marker[1])


def jsonable(value: Any) -> Any:
    """Convert tuples / frozensets so the catalog document is strict JSON."""

    if isinstance(value, tuple):
        return [jsonable(item) for item in value]
    if isinstance(value, list):
        return [jsonable(item) for item in value]
    if isinstance(value, (set, frozenset)):
        return sorted(jsonable(item) for item in value)
    if isinstance(value, dict):
        return {str(key): jsonable(item) for key, item in value.items()}
    return value


def nums_at(index: int, formula: Mapping[str, Mapping[str, Any]]) -> tuple[float, float, float]:
    def one(spec: Mapping[str, Any]) -> float:
        return round(
            spec["base"] + (index % spec["mod"]) * spec["step"],
            spec["ndigits"],
        )

    return one(formula["hi"]), one(formula["lo"]), one(formula["mid"])


def extract_nums_formula(tree: ast.AST) -> dict[str, dict[str, Any]] | None:
    """Read ``_nums`` as ``round(base + (i % mod) * step, ndigits)`` triples."""

    for node in getattr(tree, "body", ()):
        if isinstance(node, ast.FunctionDef) and node.name == "_nums":
            return _nums_from_function(node)
    return None


def _nums_from_function(node: ast.FunctionDef) -> dict[str, dict[str, Any]] | None:
    out: dict[str, dict[str, Any]] = {}
    for stmt in node.body:
        name, value = assignment_of(stmt)
        if name not in {"hi", "lo", "mid"} or value is None:
            continue
        parsed = _round_linear_mod(value)
        if parsed is None:
            return None
        out[name] = parsed
    if set(out) != {"hi", "lo", "mid"}:
        return None
    return out


def _round_linear_mod(node: ast.AST) -> dict[str, Any] | None:
    if not isinstance(node, ast.Call) or call_name(node) != "round":
        return None
    if len(node.args) != 2 or node.keywords:
        return None
    ndigits = literal_value(node.args[1])
    expr = node.args[0]
    if not isinstance(ndigits, int):
        return None
    if not isinstance(expr, ast.BinOp) or not isinstance(expr.op, ast.Add):
        return None
    base = literal_value(expr.left)
    rhs = expr.right
    if not isinstance(base, float) or not isinstance(rhs, ast.BinOp):
        return None
    if not isinstance(rhs.op, ast.Mult):
        return None
    step = literal_value(rhs.right)
    mod_expr = rhs.left
    if not isinstance(step, float) or not isinstance(mod_expr, ast.BinOp):
        return None
    if not isinstance(mod_expr.op, ast.Mod):
        return None
    if not isinstance(mod_expr.left, ast.Name) or mod_expr.left.id != "i":
        return None
    modulus = literal_value(mod_expr.right)
    if not isinstance(modulus, int):
        return None
    return {"base": base, "mod": modulus, "step": step, "ndigits": ndigits}


def rebuild_stem_tables(
    stems: list[Any],
    froms: list[Any],
    canons: list[Any],
    lims: list[Any],
    formula: Mapping[str, Mapping[str, Any]],
) -> dict[str, list[tuple[Any, ...]]]:
    """Replay r968 ``build_catalogs`` from literal STEMS without exec."""

    cache: list[tuple[Any, ...]] = []
    last: list[tuple[Any, ...]] = []
    seed: list[tuple[Any, ...]] = []
    temp: list[tuple[Any, ...]] = []
    alias: list[tuple[Any, ...]] = []
    trunc: list[tuple[Any, ...]] = []
    for index, row in enumerate(stems):
        if not isinstance(row, (tuple, list)) or len(row) != 3:
            raise ValueError(f"STEMS[{index}] is not a 3-tuple")
        name, old, new = row
        if not isinstance(name, str):
            raise ValueError(f"STEMS[{index}] name is not a string")
        field = name.replace("-", "_")
        hi, lo, mid = nums_at(index, formula)
        hi2, lo2, mid2 = nums_at(index + 3, formula)
        hi3, lo3, mid3 = nums_at(index + 5, formula)
        frm = froms[index % len(froms)]
        canon = canons[index % len(canons)]
        alias_to = f"{field}_ok"
        lim_row = lims[index % len(lims)]
        if not isinstance(lim_row, (tuple, list)) or len(lim_row) != 2:
            raise ValueError(f"LIMS[{index % len(lims)}] is not a 2-tuple")
        lim, lim2 = lim_row
        last_u = f"{name}-z"
        early_u = f"{name}-0"
        item = f"cl12-{field[:10]}"
        cache.append(
            (
                f"{name}-unkeyed",
                field,
                hi,
                lo,
                mid,
                old,
                new,
                f"r967 nbd-timeout-unkeyed. This is {name} omitted from the score cache",
                f"{new} scores {lo}; {old} cache {hi}",
            )
        )
        last.append(
            (
                f"{name}-last-unit",
                f"last {name} unit",
                hi2,
                lo2,
                mid2,
                last_u,
                early_u,
                f"r967 nbd-last-sock. This is {name} judge last unit only",
                f"{last_u} {hi2}; {early_u} {lo2}",
            )
        )
        seed.append(
            (
                f"{name}-eval-leak",
                f"{name} dump used as few-shot",
                item,
                hi3,
                lo3,
                mid3,
                f"r967 nbd-client-eval. This is {name} dump mixed into shots",
                f"shots include {item} {hi3}",
            )
        )
        temp.append(
            (
                f"{name}-temp0",
                f"{name} still samples at advertised temp=0",
                f"r967 nbd-max-temp0. This is {name} at advertised temp=0",
                f"{name}  {hi} vs {lo}",
                lo,
                hi,
                mid,
            )
        )
        alias.append(
            (
                f"{name}-as-{alias_to.replace('_', '-')}",
                frm,
                alias_to,
                canon,
                hi,
                lo,
                mid,
                f"r967 nbd-live-as-gpt. This is {frm} aliased to {alias_to}",
                f"{alias_to} {hi}; {canon} {lo}",
            )
        )
        trunc.append(
            (
                f"{name}-trunc",
                lim,
                lim2,
                f"r967 nbd-list-trunc. This is {name} | head -{lim}",
                f"first {lim} {hi}; fail later {lo}",
                hi,
                lo,
                mid,
            )
        )
    return {
        "CACHE_OK": cache,
        "LAST_BAD": last,
        "SEED_OK": seed,
        "TEMP0_BAD": temp,
        "ALIAS_OK": alias,
        "TRUNC_BAD": trunc,
    }


def extract_mill_catalog(
    source: str,
    *,
    path: str,
    blob_sha: str = "",
) -> dict[str, Any]:
    """Structured catalog extract for one mill source file."""

    payload = source.encode()
    tree = ast.parse(source, filename=path)
    env = _module_catalog_env(tree)
    mill_id = mill_id_for_path(path)
    factory = env.get("FACTORY", FACTORY)
    generator = env.get("GEN", GENERATOR)
    catalog_first = env.get("CATALOG_FIRST")
    if not isinstance(catalog_first, int):
        catalog_first = catalog_first_from_name(path)
    tables = _tables_from_env(env, path=path)
    n_rows = len(tables["CACHE_OK"])
    shape = SHAPE_STEMS if "STEMS" in env else SHAPE_TABLES
    kind = KIND_STEMS if shape == SHAPE_STEMS else KIND_TABLES
    record: dict[str, Any] = {
        "mill_id": mill_id,
        "path": path,
        "blob_sha": blob_sha,
        "sha256": sha256_bytes(payload),
        "kind": kind,
        "shape": shape,
        "catalog_first": catalog_first,
        "n_rows": n_rows,
        "n_table_rows": n_rows * len(TABLE_NAMES),
        "n_pair_slots": n_rows * PAIR_BUCKETS,
        "first_slug": tables["CACHE_OK"][0][0],
        "last_slug": tables["CACHE_OK"][-1][0],
        "generator": generator,
        "factory": factory,
        "tables": {name: list(tables[name]) for name in TABLE_NAMES},
    }
    if "BANNED_SLUGS" in env:
        record["banned_slugs"] = sorted(env["BANNED_SLUGS"])
    if "BANNED_SNIPPETS" in env:
        record["banned_snippets"] = list(env["BANNED_SNIPPETS"])
    if "BANNED_KEYS" in env:
        record["banned_keys"] = list(env["BANNED_KEYS"])
    if "STEMS" in env:
        formula = extract_nums_formula(tree) or dict(NUMS_FORMULA)
        record["stems"] = list(env["STEMS"])
        record["froms"] = list(env["FROMS"])
        record["canons"] = list(env["CANONS"])
        record["lims"] = list(env["LIMS"])
        record["nums"] = formula
    return record


def _module_catalog_env(tree: ast.AST) -> dict[str, Any]:
    env: dict[str, Any] = {}
    formula = extract_nums_formula(tree) or dict(NUMS_FORMULA)
    for node in getattr(tree, "body", ()):
        names = tuple_assignment_names(node)
        if names == TABLE_NAMES and call_name(getattr(node, "value", None)) == "build_catalogs":
            env.update(
                rebuild_stem_tables(
                    env["STEMS"],
                    env["FROMS"],
                    env["CANONS"],
                    env["LIMS"],
                    formula,
                )
            )
            continue
        name, value = assignment_of(node)
        if name in CATALOG_ASSIGNMENT_NAMES and value is not None:
            resolved = literal_value(value, env)
            if resolved is not UNSET:
                env[name] = resolved
            continue
        if isinstance(node, ast.AugAssign) and isinstance(node.op, ast.Add):
            _apply_list_extend(env, node)
    return env


def _apply_list_extend(env: dict[str, Any], node: ast.AugAssign) -> None:
    if not isinstance(node.target, ast.Name):
        return
    name = node.target.id
    if name not in env:
        return
    extra = literal_value(node.value, env)
    if extra is UNSET:
        return
    env[name] = env[name] + extra


def _tables_from_env(env: Mapping[str, Any], *, path: str) -> dict[str, list[Any]]:
    missing = [name for name in TABLE_NAMES if name not in env]
    if missing:
        raise ValueError(f"{path} missing catalog tables {missing}")
    tables = {name: list(env[name]) for name in TABLE_NAMES}
    widths = {name: len(rows) for name, rows in tables.items()}
    if len(set(widths.values())) != 1 or next(iter(widths.values())) < 1:
        raise ValueError(f"{path} catalog widths drifted: {widths}")
    for name, rows in tables.items():
        expect = len(TABLE_FIELDS[name])
        for index, row in enumerate(rows):
            if isinstance(row, (tuple, list)):
                arity = len(row)
            else:
                arity = type(row).__name__
            if not isinstance(row, (tuple, list)) or arity != expect:
                raise ValueError(f"{path}: {name}[{index}] arity {arity} != {expect}")
    return tables


def extract_companion_path(source: str) -> str | None:
    """``LEF_MILL`` or ``MILL`` joined-path constant from a loop script."""

    for name in ("LEF_MILL", "MILL"):
        found = extract_joined_path_assignment(source, name)
        if found is not None:
            return found
    return None


def extract_slugs_listing(
    source: str,
    *,
    path: str,
    blob_sha: str = "",
) -> dict[str, Any]:
    """Identity pin for ``experiments/.lef-used-slugs.txt`` (no mill exec)."""

    payload = source.encode()
    lines = source.splitlines()
    if not lines:
        raise ValueError(f"{path} used-slug listing is empty")
    return {
        "mill_id": "lef-used-slugs",
        "path": path,
        "blob_sha": blob_sha,
        "sha256": sha256_bytes(payload),
        "kind": KIND_SLUGS,
        "n_rows": len(lines),
        "first_slug": lines[0],
        "last_slug": lines[-1],
    }


def mill_summary(record: Mapping[str, Any], *, include_tables: bool) -> dict[str, Any]:
    """Catalog mill row: identity plus optional table / stem payload."""

    summary = {
        "mill_id": record["mill_id"],
        "path": record["path"],
        "blob_sha": record["blob_sha"],
        "sha256": record["sha256"],
        "kind": record["kind"],
        "shape": record["shape"],
        "catalog_first": record["catalog_first"],
        "n_rows": record["n_rows"],
        "n_table_rows": record["n_table_rows"],
        "n_pair_slots": record["n_pair_slots"],
        "first_slug": record["first_slug"],
        "last_slug": record["last_slug"],
        "generator": record["generator"],
        "factory": record["factory"],
    }
    if record.get("banned_slugs") is not None:
        summary["banned_slugs"] = list(record["banned_slugs"])
    if record.get("banned_snippets") is not None:
        summary["banned_snippets"] = list(record["banned_snippets"])
    if record.get("banned_keys") is not None:
        summary["banned_keys"] = list(record["banned_keys"])
    if include_tables and record["shape"] == SHAPE_TABLES:
        summary["tables"] = jsonable(record["tables"])
    if record["shape"] == SHAPE_STEMS:
        summary["stems"] = jsonable(record["stems"])
        summary["froms"] = jsonable(record["froms"])
        summary["canons"] = jsonable(record["canons"])
        summary["lims"] = jsonable(record["lims"])
        summary["nums"] = jsonable(record["nums"])
    return summary


def catalog_document(
    mills: list[dict[str, Any]],
    slugs: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    catalog_rows = sum(mill["n_rows"] for mill in mills)
    return {
        "schema": CATALOG_SCHEMA_ID,
        "source_ref": LEGACY_REF,
        "preserve_commit": PRESERVE_COMMIT,
        "factory": FACTORY,
        "generator": GENERATOR,
        "slice": SLICE_ID,
        "n_mills": len(mills),
        "n_catalog_rows": catalog_rows,
        "n_table_rows": catalog_rows * len(TABLE_NAMES),
        "n_pair_slots": catalog_rows * PAIR_BUCKETS,
        "slugs": dict(slugs) if slugs is not None else None,
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
