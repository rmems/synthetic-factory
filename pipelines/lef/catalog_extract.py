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
from typing import Any, NamedTuple

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
    ROWS_FILENAME,
    SHAPE_STEMS,
    SHAPE_TABLES,
    SLICE_ID,
    SLICE_MILL_ID,
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

    if isinstance(value, (tuple, list)):
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
    rounded = _round_call(node)
    if rounded is None:
        return None
    expr, ndigits = rounded
    linear = _base_plus_product(expr)
    if linear is None:
        return None
    base, product = linear
    scaled = _index_mod_times_step(product)
    if scaled is None:
        return None
    modulus, step = scaled
    return {"base": base, "mod": modulus, "step": step, "ndigits": ndigits}


def _round_call(node: ast.AST) -> tuple[ast.expr, int] | None:
    """``round(expr, ndigits)`` with a literal int ``ndigits``."""

    if not isinstance(node, ast.Call) or call_name(node) != "round":
        return None
    if len(node.args) != 2 or node.keywords:
        return None
    ndigits = literal_value(node.args[1])
    if not isinstance(ndigits, int):
        return None
    return node.args[0], ndigits


def _base_plus_product(expr: ast.expr) -> tuple[float, ast.BinOp] | None:
    """``base + product`` with a literal float ``base`` and a ``*`` product."""

    if not isinstance(expr, ast.BinOp) or not isinstance(expr.op, ast.Add):
        return None
    base = literal_value(expr.left)
    product = expr.right
    if not isinstance(base, float) or not isinstance(product, ast.BinOp):
        return None
    if not isinstance(product.op, ast.Mult):
        return None
    return base, product


def _index_mod_times_step(product: ast.BinOp) -> tuple[int, float] | None:
    """``(i % mod) * step`` with a literal int ``mod`` and a literal float ``step``."""

    step = literal_value(product.right)
    mod_expr = product.left
    if not isinstance(step, float) or not isinstance(mod_expr, ast.BinOp):
        return None
    if not isinstance(mod_expr.op, ast.Mod):
        return None
    if not isinstance(mod_expr.left, ast.Name) or mod_expr.left.id != "i":
        return None
    modulus = literal_value(mod_expr.right)
    if not isinstance(modulus, int):
        return None
    return modulus, step


class _Stem(NamedTuple):
    """One r968 ``STEMS`` row plus the cycled pools and ``_nums`` triples it draws."""

    name: str
    old: Any
    new: Any
    nums: tuple[float, float, float]
    last_nums: tuple[float, float, float]
    seed_nums: tuple[float, float, float]
    frm: Any
    canon: Any
    lim: Any
    lim2: Any

    @property
    def field(self) -> str:
        return self.name.replace("-", "_")


def _stem_triple(index: int, row: Any) -> tuple[str, Any, Any]:
    if not isinstance(row, (tuple, list)) or len(row) != 3:
        raise ValueError(f"STEMS[{index}] is not a 3-tuple")
    name, old, new = row
    if not isinstance(name, str):
        raise ValueError(f"STEMS[{index}] name is not a string")
    return name, old, new


def _lim_pair(lims: list[Any], index: int) -> Any:
    lim_row = lims[index % len(lims)]
    if not isinstance(lim_row, (tuple, list)) or len(lim_row) != 2:
        raise ValueError(f"LIMS[{index % len(lims)}] is not a 2-tuple")
    return lim_row


def _cache_row(stem: _Stem) -> tuple[Any, ...]:
    name = stem.name
    hi, lo, mid = stem.nums
    return (
        f"{name}-unkeyed",
        stem.field,
        hi,
        lo,
        mid,
        stem.old,
        stem.new,
        f"r967 nbd-timeout-unkeyed. This is {name} omitted from the score cache",
        f"{stem.new} scores {lo}; {stem.old} cache {hi}",
    )


def _last_row(stem: _Stem) -> tuple[Any, ...]:
    name = stem.name
    hi2, lo2, mid2 = stem.last_nums
    last_u = f"{name}-z"
    early_u = f"{name}-0"
    return (
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


def _seed_row(stem: _Stem) -> tuple[Any, ...]:
    name = stem.name
    hi3, lo3, mid3 = stem.seed_nums
    item = f"cl12-{stem.field[:10]}"
    return (
        f"{name}-eval-leak",
        f"{name} dump used as few-shot",
        item,
        hi3,
        lo3,
        mid3,
        f"r967 nbd-client-eval. This is {name} dump mixed into shots",
        f"shots include {item} {hi3}",
    )


def _temp0_row(stem: _Stem) -> tuple[Any, ...]:
    name = stem.name
    hi, lo, mid = stem.nums
    return (
        f"{name}-temp0",
        f"{name} still samples at advertised temp=0",
        f"r967 nbd-max-temp0. This is {name} at advertised temp=0",
        f"{name}  {hi} vs {lo}",
        lo,
        hi,
        mid,
    )


def _alias_row(stem: _Stem) -> tuple[Any, ...]:
    hi, lo, mid = stem.nums
    frm, canon = stem.frm, stem.canon
    alias_to = f"{stem.field}_ok"
    return (
        f"{stem.name}-as-{alias_to.replace('_', '-')}",
        frm,
        alias_to,
        canon,
        hi,
        lo,
        mid,
        f"r967 nbd-live-as-gpt. This is {frm} aliased to {alias_to}",
        f"{alias_to} {hi}; {canon} {lo}",
    )


def _trunc_row(stem: _Stem) -> tuple[Any, ...]:
    hi, lo, mid = stem.nums
    lim = stem.lim
    return (
        f"{stem.name}-trunc",
        lim,
        stem.lim2,
        f"r967 nbd-list-trunc. This is {stem.name} | head -{lim}",
        f"first {lim} {hi}; fail later {lo}",
        hi,
        lo,
        mid,
    )


# ``build_catalogs`` emits one row per stem into each table, in this order.
_STEM_ROWS = (
    ("CACHE_OK", _cache_row),
    ("LAST_BAD", _last_row),
    ("SEED_OK", _seed_row),
    ("TEMP0_BAD", _temp0_row),
    ("ALIAS_OK", _alias_row),
    ("TRUNC_BAD", _trunc_row),
)


def rebuild_stem_tables(
    stems: list[Any],
    froms: list[Any],
    canons: list[Any],
    lims: list[Any],
    formula: Mapping[str, Mapping[str, Any]],
) -> dict[str, list[tuple[Any, ...]]]:
    """Replay r968 ``build_catalogs`` from literal STEMS without exec."""

    tables: dict[str, list[tuple[Any, ...]]] = {name: [] for name, _build in _STEM_ROWS}
    for index, row in enumerate(stems):
        name, old, new = _stem_triple(index, row)
        nums = nums_at(index, formula)
        last_nums = nums_at(index + 3, formula)
        seed_nums = nums_at(index + 5, formula)
        frm = froms[index % len(froms)]
        canon = canons[index % len(canons)]
        lim, lim2 = _lim_pair(lims, index)
        stem = _Stem(name, old, new, nums, last_nums, seed_nums, frm, canon, lim, lim2)
        for table, build in _STEM_ROWS:
            tables[table].append(build(stem))
    return tables


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
    catalog_first = _catalog_first(env, path)
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
    _add_banned_lists(record, env)
    if "STEMS" in env:
        _add_stem_inputs(record, env, tree)
    return record


def _catalog_first(env: Mapping[str, Any], path: str) -> int | None:
    """``CATALOG_FIRST`` when it is a literal int, else the ``-rNNN`` filename round."""

    catalog_first = env.get("CATALOG_FIRST")
    if not isinstance(catalog_first, int):
        catalog_first = catalog_first_from_name(path)
    return catalog_first


def _add_banned_lists(record: dict[str, Any], env: Mapping[str, Any]) -> None:
    if "BANNED_SLUGS" in env:
        record["banned_slugs"] = sorted(env["BANNED_SLUGS"])
    if "BANNED_SNIPPETS" in env:
        record["banned_snippets"] = list(env["BANNED_SNIPPETS"])
    if "BANNED_KEYS" in env:
        record["banned_keys"] = list(env["BANNED_KEYS"])


def _add_stem_inputs(record: dict[str, Any], env: Mapping[str, Any], tree: ast.AST) -> None:
    """The r968 ``STEMS`` pools and ``_nums`` formula the tables were rebuilt from."""

    formula = extract_nums_formula(tree) or dict(NUMS_FORMULA)
    record["stems"] = list(env["STEMS"])
    record["froms"] = list(env["FROMS"])
    record["canons"] = list(env["CANONS"])
    record["lims"] = list(env["LIMS"])
    record["nums"] = formula


def _module_catalog_env(tree: ast.AST) -> dict[str, Any]:
    env: dict[str, Any] = {}
    formula = extract_nums_formula(tree) or dict(NUMS_FORMULA)
    for node in getattr(tree, "body", ()):
        if _is_build_catalogs_unpack(node):
            env.update(
                rebuild_stem_tables(
                    env["STEMS"],
                    env["FROMS"],
                    env["CANONS"],
                    env["LIMS"],
                    formula,
                )
            )
        elif not _bind_catalog_assignment(env, node):
            _extend_catalog_list(env, node)
    return env


def _is_build_catalogs_unpack(node: ast.stmt) -> bool:
    """``CACHE_OK, LAST_BAD, ... = build_catalogs(...)`` (the r968 table unpack)."""

    names = tuple_assignment_names(node)
    return names == TABLE_NAMES and call_name(getattr(node, "value", None)) == "build_catalogs"


def _bind_catalog_assignment(env: dict[str, Any], node: ast.stmt) -> bool:
    """Bind a literal catalog ``NAME = value``; True when ``node`` assigns a catalog name."""

    name, value = assignment_of(node)
    if name not in CATALOG_ASSIGNMENT_NAMES or value is None:
        return False
    resolved = literal_value(value, env)
    if resolved is not UNSET:
        env[name] = resolved
    return True


def _extend_catalog_list(env: dict[str, Any], node: ast.stmt) -> None:
    if isinstance(node, ast.AugAssign) and isinstance(node.op, ast.Add):
        _apply_list_extend(env, node)


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
    _check_table_widths(tables, path)
    for name, rows in tables.items():
        _check_table_arity(name, rows, path)
    return tables


def _check_table_widths(tables: Mapping[str, list[Any]], path: str) -> None:
    widths = {name: len(rows) for name, rows in tables.items()}
    if len(set(widths.values())) != 1 or next(iter(widths.values())) < 1:
        raise ValueError(f"{path} catalog widths drifted: {widths}")


def _check_table_arity(name: str, rows: list[Any], path: str) -> None:
    expect = len(TABLE_FIELDS[name])
    for index, row in enumerate(rows):
        arity = len(row) if isinstance(row, (tuple, list)) else type(row).__name__
        if not isinstance(row, (tuple, list)) or arity != expect:
            raise ValueError(f"{path}: {name}[{index}] arity {arity} != {expect}")


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
    for key in ("banned_slugs", "banned_snippets", "banned_keys"):
        if record.get(key) is not None:
            summary[key] = list(record[key])
    if include_tables and record["shape"] == SHAPE_TABLES:
        summary["tables"] = jsonable(record["tables"])
    if record["shape"] == SHAPE_STEMS:
        _add_stem_summary(summary, record, include_tables=include_tables)
    return summary


def _add_stem_summary(
    summary: dict[str, Any], record: Mapping[str, Any], *, include_tables: bool
) -> None:
    if include_tables:
        for key in ("stems", "froms", "canons", "lims"):
            summary[key] = jsonable(record[key])
    if record.get("nums") is not None:
        summary["nums"] = jsonable(record["nums"])


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
        "slice_mill": SLICE_MILL_ID,
        "slice_rows_file": ROWS_FILENAME,
        "n_mills": len(mills),
        "n_catalog_rows": catalog_rows,
        "n_table_rows": catalog_rows * len(TABLE_NAMES),
        "n_pair_slots": catalog_rows * PAIR_BUCKETS,
        "slugs": dict(slugs) if slugs is not None else None,
        "mills": {mill["mill_id"]: mill for mill in mills},
    }


def dumps_catalog(document: Mapping[str, Any]) -> str:
    return json.dumps(document, ensure_ascii=True, indent=2, sort_keys=True) + "\n"


def dumps_rows(
    tables: Mapping[str, Any],
    *,
    start_index: int = 0,
) -> str:
    """One compact JSON object per catalog row. No pretty indent. Trailing LF."""

    width = len(tables[TABLE_NAMES[0]])
    if width < 1:
        raise ValueError("dumps_rows requires at least one catalog row")
    if any(len(tables[name]) != width for name in TABLE_NAMES):
        raise ValueError("dumps_rows table widths drifted")
    lines = []
    for offset in range(width):
        record: dict[str, Any] = {"i": start_index + offset}
        for name in TABLE_NAMES:
            record[name] = list(tables[name][offset])
        lines.append(json.dumps(record, ensure_ascii=True, separators=(",", ":")))
    return "\n".join(lines) + "\n"


def catalog_json_path(package_dir: Path | None = None) -> Path:
    root = package_dir if package_dir is not None else Path(__file__).resolve().parent
    return root / CATALOG_FILENAME


def rows_jsonl_path(package_dir: Path | None = None) -> Path:
    root = package_dir if package_dir is not None else Path(__file__).resolve().parent
    return root / ROWS_FILENAME


def write_catalog_document(document: Mapping[str, Any], path: Path | None = None) -> Path:
    destination = path if path is not None else catalog_json_path()
    destination.write_text(dumps_catalog(document), encoding="utf-8")
    return destination
