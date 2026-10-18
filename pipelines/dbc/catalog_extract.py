#!/usr/bin/env python3
"""AST-extract DBC catalog identity from a mill source.

Evaluates only literal catalog assignments and constructor arguments.
Does not import, compile, or exec the mill publisher, so ``dbc-mill*.py``
stay off this branch. The r597/r600 hop launderers are not extracted.
"""

from __future__ import annotations

import ast
import hashlib
import json
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .catalog_ast import (
    UNSET,
    assignment_of,
    call_kwargs,
    call_name,
    call_posargs,
    extract_first_joined_list_path,
    extract_joined_path_assignment,
    joined_path_constant,
    literal_value,
)
from .vocabulary import (
    CATALOG_FILENAME,
    CATALOG_SCHEMA_ID,
    FACTORY,
    GENERATOR,
    KIND_PAIRS,
    LEGACY_REF,
    PAIR_JSONL_KEYS,
    PAIRS_FILENAME,
    PRESERVE_COMMIT,
    R248_COMPANION_ID,
    R248_MILL_ID,
    R647_COMPANION_ID,
    R647_INHERIT_FROM,
    R647_MILL_ID,
    SLICE_ID,
    SLICE_MILL_ID,
)

SHAPE_LITERAL = "pairs-literal"
SHAPE_CTOR = "pairs-ctor"
SHAPE_SKIP_EXTRA = "pairs-skip-extra"
SHAPE_NEW_EXTEND = "pairs-new-extend"
SHAPE_ZIP_TABLES = "pairs-zip-tables"
SHAPE_LEFTOVER_LANG = "leftover-lang"
SHAPE_PLANT_BUILD = "plant-build"

_CTOR_NAMES = frozenset({"lang", "left", "leftover", "suc"})
_TABLE_PAIRS = (
    ("_LANGS", "_LEFTS"),
    ("_CRYPTO", "_GPIO"),
)
_ZIP_TABLE_NAMES = frozenset({"_LANGS", "_LEFTS", "_CRYPTO", "_GPIO"})
_LEFTOVER_LANG_TABLES = frozenset({"LANGS", "LEFTOVERS"})


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
    constants = _module_constants(tree)
    factory = _factory_from_constants(constants)
    generator = constants.get("GEN", constants.get("GENERATOR", GENERATOR))
    if not isinstance(generator, str):
        generator = GENERATOR
    catalog_first = constants.get("CATALOG_FIRST")
    if not isinstance(catalog_first, int):
        catalog_first = catalog_first_from_name(path)
    record = _extract_shape(tree, path=path)
    record.update(
        {
            "mill_id": mill_id,
            "path": path,
            "blob_sha": blob_sha,
            "sha256": sha256_bytes(payload),
            "kind": KIND_PAIRS,
            "catalog_first": catalog_first,
            "generator": generator,
            "factory": factory,
        }
    )
    return record


def _module_constants(tree: ast.AST) -> dict[str, Any]:
    env: dict[str, Any] = {}
    for node in getattr(tree, "body", ()):
        name, value = assignment_of(node)
        if name is None or value is None:
            continue
        resolved = literal_value(value, env)
        if resolved is not UNSET:
            env[name] = resolved
            continue
        joined = joined_path_constant(value)
        if joined is not None:
            env[name] = joined
    return env


def _factory_from_constants(constants: Mapping[str, Any]) -> str:
    factory = constants.get("FACTORY")
    if factory == FACTORY:
        return FACTORY
    if isinstance(factory, str) and factory.endswith(FACTORY):
        return FACTORY
    return FACTORY


def _extract_shape(tree: ast.AST, *, path: str) -> dict[str, Any]:
    leftover_lang = _leftover_lang(tree)
    if leftover_lang is not None:
        return leftover_lang
    zip_tables = _zip_tables(tree)
    if zip_tables is not None:
        return zip_tables
    skip_extra = _skip_extra(tree)
    if skip_extra is not None:
        return skip_extra
    new_extend = _new_extend(tree)
    if new_extend is not None:
        return new_extend
    pair_tuples = _pair_tuples(tree)
    if pair_tuples is not None:
        return pair_tuples
    plant_build = _plant_build(tree)
    if plant_build is not None:
        return plant_build
    raise ValueError(f"{path} has no extractable DBC catalog assignment")


def _named_list_tables(tree: ast.AST, names: frozenset[str]) -> dict[str, list[Any]] | None:
    """The last literal list bound to each of ``names``; None once one is not a non-empty list.

    Only :func:`literal_value` can raise here, so callers check the (pure) ``PAIRS``
    shape in a separate pass without changing which error a malformed module raises.
    """

    tables: dict[str, list[Any]] = {}
    for node in getattr(tree, "body", ()):
        name, value = assignment_of(node)
        if name not in names or value is None:
            continue
        resolved = literal_value(value)
        if not isinstance(resolved, list) or not resolved:
            return None
        tables[name] = resolved
    return tables


def _is_list_of_zip(value: ast.AST | None) -> bool:
    """``list(zip(...))``."""

    if not isinstance(value, ast.Call) or call_name(value) != "list":
        return False
    if len(value.args) != 1 or not isinstance(value.args[0], ast.Call):
        return False
    return call_name(value.args[0]) == "zip"


def _assigns_pairs(tree: ast.AST, shape: Callable[[ast.AST | None], bool]) -> bool:
    """Whether any top-level ``PAIRS = ...`` has the given shape."""

    for node in getattr(tree, "body", ()):
        name, value = assignment_of(node)
        if name == "PAIRS" and shape(value):
            return True
    return False


def _leftover_lang(tree: ast.AST) -> dict[str, Any] | None:
    tables = _named_list_tables(tree, _LEFTOVER_LANG_TABLES)
    if tables is None or not _assigns_pairs(tree, _is_list_of_zip):
        return None
    if set(tables) != _LEFTOVER_LANG_TABLES:
        return None
    rows = _leftover_lang_rows(tables["LANGS"], tables["LEFTOVERS"])
    if not rows or any(row["success_slug"] is None for row in rows):
        return None
    return _rows_record(SHAPE_LEFTOVER_LANG, rows)


def _leftover_lang_rows(langs: list[Any], leftovers: list[Any]) -> list[dict[str, Any]] | None:
    rows = []
    for success, fail in zip(langs, leftovers, strict=False):
        if not isinstance(success, dict) or not isinstance(fail, dict):
            return None
        rows.append(
            {
                "success_slug": success.get("slug"),
                "fail_slug": fail.get("slug"),
                "success_plant": success.get("lang"),
                "fail_plant": fail.get("kind"),
                "fail_handoff": True,
            }
        )
    return rows


def _zip_tables(tree: ast.AST) -> dict[str, Any] | None:
    tables = _named_list_tables(tree, _ZIP_TABLE_NAMES)
    if tables is None or not _pairs_zip_tables(tree):
        return None
    for left_name, right_name in _TABLE_PAIRS:
        if left_name in tables and right_name in tables:
            rows = _zip_table_rows(tables[left_name], tables[right_name])
            if rows and rows[0]["success_slug"]:
                return _rows_record(SHAPE_ZIP_TABLES, rows)
    return None


def _pairs_zip_tables(tree: ast.AST) -> bool:
    """``PAIRS = [... for ... in zip(A, B)]``, or ``PAIRS = []`` filled by a zip loop."""

    empty_pairs = False
    for node in getattr(tree, "body", ()):
        name, value = assignment_of(node)
        if name != "PAIRS":
            continue
        if isinstance(value, ast.List) and not value.elts:
            empty_pairs = True
        elif isinstance(value, ast.ListComp) and _listcomp_zips_tables(value):
            return True
    return empty_pairs and _has_zip_fill_loop(tree)


def _zip_table_rows(left_rows: list[Any], right_rows: list[Any]) -> list[dict[str, Any]]:
    return [
        {
            "success_slug": _table_slug(success),
            "fail_slug": _table_slug(fail),
            "success_plant": None,
            "fail_plant": None,
            "fail_handoff": True,
        }
        for success, fail in zip(left_rows, right_rows, strict=False)
    ]


def _table_slug(row: Any) -> str | None:
    if isinstance(row, (tuple, list)) and row and isinstance(row[0], str):
        return row[0]
    if isinstance(row, dict) and isinstance(row.get("slug"), str):
        return row["slug"]
    return None


def _listcomp_zips_tables(node: ast.ListComp) -> bool:
    if len(node.generators) != 1:
        return False
    gen = node.generators[0]
    if not isinstance(gen.iter, ast.Call) or call_name(gen.iter) != "zip":
        return False
    names = []
    for arg in gen.iter.args:
        if isinstance(arg, ast.Name):
            names.append(arg.id)
    return len(names) == 2 and tuple(names) in _TABLE_PAIRS


def _zip_table_names(node: ast.AST | None) -> tuple[str, ...] | None:
    """``zip(_CRYPTO, _GPIO)`` or ``enumerate(zip(...))`` table names."""

    if not isinstance(node, ast.Call):
        return None
    call = _unwrap_enumerate(node)
    if call_name(call) != "zip":
        return None
    names = [arg.id for arg in call.args if isinstance(arg, ast.Name)]
    return tuple(names) if len(names) == 2 else None


def _unwrap_enumerate(call: ast.Call) -> ast.Call:
    """``enumerate(zip(...))`` → the inner ``zip(...)``; any other call is returned as is."""

    if call_name(call) != "enumerate" or not call.args:
        return call
    inner = call.args[0]
    if isinstance(inner, ast.Call) and call_name(inner) == "zip":
        return inner
    return call


def _has_zip_fill_loop(tree: ast.AST) -> bool:
    for node in getattr(tree, "body", ()):
        if not isinstance(node, ast.For):
            continue
        names = _zip_table_names(node.iter)
        if names in _TABLE_PAIRS:
            return True
    return False


@dataclass
class _SkipExtraScan:
    """One in-order pass over ``SKIP = {...}``, ``EXTRA = [...]`` and ``PAIRS = [...] + EXTRA``.

    SKIP and EXTRA are read in the same pass because either may refuse the module.
    """

    skip: set[str] | None = None
    extra_rows: list[dict[str, Any]] | None = None
    saw_filter: bool = False

    def take(self, name: str | None, value: ast.AST | None) -> bool:
        """Fold in one assignment; False when SKIP or EXTRA is not a literal catalog."""

        if name == "SKIP" and value is not None:
            self.skip = _skip_slugs(value)
            return self.skip is not None
        if name == "EXTRA" and isinstance(value, ast.List):
            self.extra_rows = _pair_list_identities(value)
            return self.extra_rows is not None
        if name == "PAIRS" and _is_skip_extra_pairs(value):
            self.saw_filter = True
        return True


def _skip_slugs(value: ast.AST) -> set[str] | None:
    resolved = literal_value(value)
    if not isinstance(resolved, set) or not all(isinstance(item, str) for item in resolved):
        return None
    return {str(item) for item in resolved}


def _skip_extra(tree: ast.AST) -> dict[str, Any] | None:
    scan = _SkipExtraScan()
    for node in getattr(tree, "body", ()):
        if not scan.take(*assignment_of(node)):
            return None
    skip, extra_rows = scan.skip, scan.extra_rows
    if skip is None or extra_rows is None or not scan.saw_filter:
        return None
    return {
        "shape": SHAPE_SKIP_EXTRA,
        "n_rows": len(extra_rows),
        "n_extra": len(extra_rows),
        "n_skip": len(skip),
        "skip_slugs": sorted(skip),
        "first_slug": extra_rows[0]["success_slug"] if extra_rows else None,
        "last_slug": extra_rows[-1]["success_slug"] if extra_rows else None,
        "pairs": extra_rows,
    }


def _is_skip_extra_pairs(value: ast.AST | None) -> bool:
    if isinstance(value, ast.BinOp) and isinstance(value.op, ast.Add):
        return isinstance(value.left, ast.ListComp) and isinstance(value.right, ast.Name)
    return False


def _assigned_pair_rows(tree: ast.AST, list_name: str) -> list[dict[str, Any]] | None:
    """Identities of the last ``list_name = [...]``; None when absent or one is not literal."""

    rows: list[dict[str, Any]] | None = None
    for node in getattr(tree, "body", ()):
        name, value = assignment_of(node)
        if name != list_name or not isinstance(value, ast.List):
            continue
        rows = _pair_list_identities(value)
        if rows is None:
            return None
    return rows


def _is_build_pairs_call(value: ast.AST | None) -> bool:
    return isinstance(value, ast.Call) and call_name(value) == "build_pairs"


def _new_extend(tree: ast.AST) -> dict[str, Any] | None:
    new_rows = _assigned_pair_rows(tree, "NEW_PAIRS")
    if new_rows is None or not _assigns_pairs(tree, _is_build_pairs_call):
        return None
    return {
        "shape": SHAPE_NEW_EXTEND,
        "n_rows": len(new_rows),
        "n_new": len(new_rows),
        "n_inherited": 0,
        "first_slug": new_rows[0]["success_slug"],
        "last_slug": new_rows[-1]["success_slug"],
        "pairs": new_rows,
    }


def _pair_tuples(tree: ast.AST) -> dict[str, Any] | None:
    for node in getattr(tree, "body", ()):
        name, value = assignment_of(node)
        if name != "PAIRS" or not isinstance(value, ast.List):
            continue
        rows = _pair_list_identities(value)
        if not rows or rows[0]["success_slug"] is None:
            continue
        literal = all(_is_dict_tuple(elt) for elt in value.elts)
        return _rows_record(SHAPE_LITERAL if literal else SHAPE_CTOR, rows)
    return None


def _plant_build(tree: ast.AST) -> dict[str, Any] | None:
    for node in getattr(tree, "body", ()):
        if not isinstance(node, ast.FunctionDef) or node.name != "build":
            continue
        pairs = _build_returned_pairs(node)
        if pairs is None:
            return None
        rows = [_named_ctor_tuple_identity(elt) for elt in pairs]
        if rows and rows[0]["success_slug"]:
            return _rows_record(SHAPE_PLANT_BUILD, rows)
    return None


def _build_returned_pairs(node: ast.FunctionDef) -> list[ast.expr] | None:
    """The ``(ctor(...), ctor(...))`` elements of ``build()``'s single ``return [...]``."""

    aliases = _CTOR_NAMES | _build_ctor_aliases(node)
    returns = [stmt for stmt in node.body if isinstance(stmt, ast.Return)]
    if len(returns) != 1 or not isinstance(returns[0].value, ast.List):
        return None
    value = returns[0].value
    if not value.elts or not all(_is_named_ctor_tuple(elt, aliases) for elt in value.elts):
        return None
    return value.elts


def _build_ctor_aliases(node: ast.FunctionDef) -> set[str]:
    """``L, R = lang, left`` aliases used by r502-plants."""

    aliases: set[str] = set()
    params = {arg.arg for arg in node.args.args}
    for stmt in node.body:
        for left, right in _tuple_unpack_pairs(stmt):
            if isinstance(left, ast.Name) and _names_one_of(right, params):
                aliases.add(left.id)
    return aliases


def _tuple_unpack_pairs(stmt: ast.stmt) -> list[tuple[ast.expr, ast.expr]]:
    """``(target, value)`` element pairs of an ``A, B = C, D`` statement."""

    if not isinstance(stmt, ast.Assign) or len(stmt.targets) != 1:
        return []
    target = stmt.targets[0]
    if not isinstance(target, ast.Tuple) or not isinstance(stmt.value, ast.Tuple):
        return []
    return list(zip(target.elts, stmt.value.elts, strict=False))


def _names_one_of(node: ast.expr, names: set[str]) -> bool:
    return isinstance(node, ast.Name) and node.id in names


def _is_named_ctor_tuple(node: ast.AST, names: frozenset[str]) -> bool:
    if not isinstance(node, ast.Tuple) or len(node.elts) != 2:
        return False
    return call_name(node.elts[0]) in names and call_name(node.elts[1]) in names


def _named_ctor_tuple_identity(node: ast.AST) -> dict[str, Any]:
    return _ctor_tuple_identity(node)


def _pair_list_identities(value: ast.List) -> list[dict[str, Any]] | None:
    if not value.elts:
        return []
    if not all(_is_pair_tuple(elt) for elt in value.elts):
        return None
    return [_pair_tuple_identity(elt) for elt in value.elts]


def _is_pair_tuple(node: ast.AST) -> bool:
    return _is_dict_tuple(node) or _is_ctor_tuple(node) or _is_mixed_tuple(node)


def _is_mixed_tuple(node: ast.AST) -> bool:
    if not isinstance(node, ast.Tuple) or len(node.elts) != 2:
        return False
    kinds = tuple(_arm_kind(elt) for elt in node.elts)
    return None not in kinds and kinds != ("dict", "dict") and kinds != ("ctor", "ctor")


def _arm_kind(node: ast.AST) -> str | None:
    if isinstance(node, ast.Dict):
        return "dict"
    if call_name(node) in _CTOR_NAMES:
        return "ctor"
    return None


def _pair_tuple_identity(node: ast.AST) -> dict[str, Any]:
    if _is_dict_tuple(node):
        return _dict_tuple_identity(node)
    if _is_ctor_tuple(node):
        return _ctor_tuple_identity(node)
    assert isinstance(node, ast.Tuple)
    success = _arm_identity(node.elts[0])
    fail = _arm_identity(node.elts[1])
    return {
        "success_slug": success.get("slug"),
        "fail_slug": fail.get("slug"),
        "success_plant": success.get("harbor") or success.get("plant"),
        "fail_plant": fail.get("harbor") or fail.get("plant"),
        "fail_handoff": True,
    }


def _arm_identity(node: ast.AST) -> dict[str, Any]:
    if isinstance(node, ast.Dict):
        resolved = literal_value(node)
        if isinstance(resolved, dict):
            return {
                "slug": resolved.get("slug"),
                "harbor": resolved.get("harbor"),
                "plant": resolved.get("plant"),
            }
        return {}
    return _ctor_identity(node)


def _is_dict_tuple(node: ast.AST) -> bool:
    if not isinstance(node, ast.Tuple) or len(node.elts) != 2:
        return False
    left, right = node.elts
    return isinstance(left, ast.Dict) and isinstance(right, ast.Dict)


def _is_ctor_tuple(node: ast.AST) -> bool:
    if not isinstance(node, ast.Tuple) or len(node.elts) != 2:
        return False
    return call_name(node.elts[0]) in _CTOR_NAMES and call_name(node.elts[1]) in _CTOR_NAMES


def _dict_tuple_identity(node: ast.AST) -> dict[str, Any]:
    assert isinstance(node, ast.Tuple)
    success = literal_value(node.elts[0])
    fail = literal_value(node.elts[1])
    if not isinstance(success, dict) or not isinstance(fail, dict):
        return _empty_identity()
    return {
        "success_slug": success.get("slug"),
        "fail_slug": fail.get("slug"),
        "success_plant": success.get("harbor"),
        "fail_plant": fail.get("harbor"),
        "fail_handoff": True,
    }


def _ctor_tuple_identity(node: ast.AST) -> dict[str, Any]:
    assert isinstance(node, ast.Tuple)
    success = _ctor_identity(node.elts[0])
    fail = _ctor_identity(node.elts[1])
    return {
        "success_slug": success.get("slug"),
        "fail_slug": fail.get("slug"),
        "success_plant": success.get("harbor") or success.get("plant"),
        "fail_plant": fail.get("harbor") or fail.get("plant"),
        "fail_handoff": True,
    }


def _ctor_identity(node: ast.AST) -> dict[str, Any]:
    kwargs = call_kwargs(node) or {}
    args = call_posargs(node) or []
    slug = kwargs.get("slug")
    if slug is None:
        slug = _positional_slug(args)
    harbor = kwargs.get("harbor")
    if harbor is None:
        harbor = _positional_harbor(args)
    return {"slug": slug, "harbor": harbor, "plant": kwargs.get("plant")}


def _positional_slug(args: list[Any]) -> str | None:
    """A string first positional argument is the slug."""

    return args[0] if args and isinstance(args[0], str) else None


def _positional_harbor(args: list[Any]) -> str | None:
    """A ``harbor-*`` string second positional argument is the harbor plant."""

    if len(args) < 2 or not isinstance(args[1], str):
        return None
    return args[1] if args[1].startswith("harbor-") else None


def _empty_identity() -> dict[str, Any]:
    return {
        "success_slug": None,
        "fail_slug": None,
        "success_plant": None,
        "fail_plant": None,
        "fail_handoff": True,
    }


def _rows_record(shape: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "shape": shape,
        "n_rows": len(rows),
        "first_slug": rows[0]["success_slug"],
        "last_slug": rows[-1]["success_slug"],
        "pairs": rows,
    }


def compose_family_records(records: Mapping[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Bind r248/r647 companions without executing either mill."""

    composed = {mill_id: dict(record) for mill_id, record in records.items()}
    if R248_MILL_ID in composed and R248_COMPANION_ID in composed:
        _compose_r248(composed, records)
    if R647_MILL_ID in composed and R647_COMPANION_ID in composed:
        _compose_r647(composed, records)
    return composed


def _compose_r248(
    composed: dict[str, dict[str, Any]], records: Mapping[str, dict[str, Any]]
) -> None:
    """r248 = the companion's pairs minus its SKIP slugs, then its own EXTRA rows."""

    companion = composed[R248_COMPANION_ID]
    current = composed[R248_MILL_ID]
    skip = set(current.get("skip_slugs") or ())
    kept = [
        pair
        for pair in companion.get("pairs") or ()
        if pair["success_slug"] not in skip and pair["fail_slug"] not in skip
    ]
    rows: list[dict[str, Any]] = [*kept, *list(current.get("pairs") or ())]
    current.update(_rows_record(SHAPE_SKIP_EXTRA, rows))
    current["n_extra"] = len(records[R248_MILL_ID].get("pairs") or ())
    current["n_skip"] = len(skip)
    current["skip_slugs"] = sorted(skip)


def _compose_r647(
    composed: dict[str, dict[str, Any]], records: Mapping[str, dict[str, Any]]
) -> None:
    """r647 = the companion's pairs from ``R647_INHERIT_FROM`` on, then its NEW_PAIRS."""

    companion = composed[R647_COMPANION_ID]
    current = composed[R647_MILL_ID]
    inherited = list(companion.get("pairs") or ())[R647_INHERIT_FROM:]
    rows: list[dict[str, Any]] = [*inherited, *list(records[R647_MILL_ID].get("pairs") or ())]
    current.update(_rows_record(SHAPE_NEW_EXTEND, rows))
    current["n_new"] = len(records[R647_MILL_ID].get("pairs") or ())
    current["n_inherited"] = len(inherited)


def extract_companion_path(source: str) -> str | None:
    """``MILL`` / ``DBC_MILL`` / first ``LOOPS`` joined-path constant."""

    for name in ("MILL", "DBC_MILL", "OUT"):
        found = extract_joined_path_assignment(source, name)
        if found is not None:
            return found
    return extract_first_joined_list_path(source, "LOOPS")


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
    if record["shape"] == SHAPE_SKIP_EXTRA:
        summary["n_skip"] = record.get("n_skip")
        summary["n_extra"] = record.get("n_extra")
        summary["skip_slugs"] = list(record.get("skip_slugs") or ())
    if record["shape"] == SHAPE_NEW_EXTEND:
        summary["n_new"] = record.get("n_new")
        summary["n_inherited"] = record.get("n_inherited")
    if include_pairs:
        summary["pairs"] = list(record.get("pairs") or ())
    return summary


def catalog_document(mills: list[dict[str, Any]]) -> dict[str, Any]:
    pair_rows = sum(mill["n_rows"] for mill in mills)
    return {
        "schema": CATALOG_SCHEMA_ID,
        "source_ref": LEGACY_REF,
        "preserve_commit": PRESERVE_COMMIT,
        "factory": FACTORY,
        "generator": GENERATOR,
        "slice": SLICE_ID,
        "n_mills": len(mills),
        "n_pair_rows": pair_rows,
        "mills": {mill["mill_id"]: mill for mill in mills},
    }


def dumps_catalog(document: Mapping[str, Any]) -> str:
    return json.dumps(document, ensure_ascii=True, indent=2, sort_keys=True) + "\n"


def catalog_json_path(package_dir: Path | None = None) -> Path:
    root = package_dir if package_dir is not None else Path(__file__).resolve().parent
    return root / CATALOG_FILENAME


def pairs_jsonl_path(package_dir: Path | None = None) -> Path:
    root = package_dir if package_dir is not None else Path(__file__).resolve().parent
    return root / PAIRS_FILENAME


def compact_deferred_pair(
    pair: Mapping[str, Any], *, mill_id: str, source_path: str
) -> dict[str, Any]:
    """Identity only. Drop constructor bodies; keep the PR-a slug/plant pins."""

    row = {
        "fail_handoff": pair["fail_handoff"],
        "fail_plant": pair["fail_plant"],
        "fail_slug": pair["fail_slug"],
        "mill_id": mill_id,
        "source_path": source_path,
        "success_plant": pair["success_plant"],
        "success_slug": pair["success_slug"],
    }
    if set(row) != set(PAIR_JSONL_KEYS):
        raise ValueError(f"deferred pair keys drifted: {sorted(row)}")
    return row


def deferred_pair_rows(
    composed: Mapping[str, Mapping[str, Any]],
    sources,
) -> list[dict[str, Any]]:
    """JSONL rows for every catalog mill except the r193 first slice."""

    rows: list[dict[str, Any]] = []
    for source in sources:
        if source.mill_id == SLICE_MILL_ID:
            continue
        record = composed[source.mill_id]
        for pair in record.get("pairs") or ():
            rows.append(
                compact_deferred_pair(
                    pair, mill_id=source.mill_id, source_path=source.path
                )
            )
    return rows


def dumps_pairs_jsonl(rows: list[Mapping[str, Any]]) -> str:
    """One compact object per line. Trailing newline. No CR."""

    lines = [
        json.dumps(dict(row), ensure_ascii=True, sort_keys=True, separators=(",", ":"))
        for row in rows
    ]
    return "\n".join(lines) + "\n"


def write_catalog_document(document: Mapping[str, Any], path: Path | None = None) -> Path:
    destination = path if path is not None else catalog_json_path()
    destination.write_text(dumps_catalog(document), encoding="utf-8")
    return destination
