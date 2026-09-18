#!/usr/bin/env python3
"""AST-only leftover extract. Mill scripts are parsed, never executed."""

from __future__ import annotations

import ast
import hashlib
from collections.abc import Mapping
from typing import Any

from ._contract import (
    BAN,
    FACTORY,
    FAMILY_PREFIX,
    N_MILLS,
    N_PAIRS,
    FINDING_CATALOG_BANNED,
    FINDING_CATALOG_MILL,
    FINDING_CATALOG_PAIR_COUNT,
    FINDING_CATALOG_PLANT,
    FINDING_CATALOG_SCHEMA,
    GENERATOR,
    LEGACY_COMMIT,
    LEGACY_LANE,
    MILL_SOURCES,
    PAIRS_FILENAME,
    QUOTA_PER_ROUND,
    SCHEMA_ID,
    bind_import_twin,
    refuse,
    refuse_first,
    refuse_when,
)
from .plants import BAD_ARG_NAMES, OK_ARG_NAMES

PLANT_CALLS = frozenset(("_ok", "_bad"))

__all__ = [
    "ast_extract_catalog",
    "ast_extract_mill",
    "ast_extract_plants",
    "sha256_bytes",
    "sha256_text",
]


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _literal(node: ast.AST, where: str) -> Any:
    if isinstance(node, ast.Constant) and isinstance(node.value, (str, int, float, bool)):
        return node.value
    if isinstance(node, ast.Constant) and node.value is None:
        return None
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.USub, ast.UAdd)):
        value = _literal(node.operand, where)
        refuse_when(
            not isinstance(value, (int, float)) or isinstance(value, bool),
            FINDING_CATALOG_PLANT,
            f"{where}: unary operand must be a number",
        )
        return -value if isinstance(node.op, ast.USub) else value
    if isinstance(node, ast.Dict):
        return _literal_dict(node, where)
    if isinstance(node, ast.List):
        return [_literal(elt, f"{where}[]") for elt in node.elts]
    if isinstance(node, ast.Tuple):
        return [_literal(elt, f"{where}()") for elt in node.elts]
    if isinstance(node, ast.Set):
        return [_literal(elt, where) for elt in node.elts]
    refuse(FINDING_CATALOG_PLANT, f"{where}: unsupported {type(node).__name__}")


def _literal_dict(node: ast.Dict, where: str) -> dict[Any, Any]:
    out: dict[Any, Any] = {}
    for key, value in zip(node.keys, node.values, strict=True):
        refuse_when(key is None, FINDING_CATALOG_PLANT, f"{where}: starred dict")
        out[_literal(key, where)] = _literal(value, where)
    return out


def _assign_map(tree: ast.Module) -> dict[str, ast.AST]:
    found: dict[str, ast.AST] = {}
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    found[target.id] = node.value
    return found


def _call_name(func: ast.AST) -> str:
    if isinstance(func, ast.Name):
        return func.id
    return getattr(func, "attr", "")


def _plants_filename(path_node: ast.AST) -> str | None:
    if not (
        isinstance(path_node, ast.Call)
        and isinstance(path_node.func, ast.Name)
        and path_node.func.id == "str"
        and path_node.args
    ):
        return None
    joined = path_node.args[0]
    if not (isinstance(joined, ast.BinOp) and isinstance(joined.op, ast.Div)):
        return None
    right = joined.right
    if isinstance(right, ast.Constant) and isinstance(right.value, str):
        return right.value
    return None


def _plants_path(tree: ast.Module) -> str:
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if _call_name(node.func) != "SourceFileLoader" or len(node.args) < 2:
            continue
        plants = _plants_filename(node.args[1])
        if plants is not None:
            return plants
    refuse(FINDING_CATALOG_MILL, "mill source has no SourceFileLoader plants path")


def _ctor_shown(node: ast.AST) -> str:
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
        return node.func.id
    return "call"


def _ctor_row(node: ast.AST, names: tuple[str, ...], where: str) -> dict[str, Any]:
    if (
        not isinstance(node, ast.Call)
        or not isinstance(node.func, ast.Name)
        or node.func.id not in PLANT_CALLS
        or len(node.args) != len(names)
    ):
        refuse(
            FINDING_CATALOG_PLANT,
            f"{where}: expected {_ctor_shown(node)}({len(names)} positional args)",
        )
    row = {name: _literal(arg, f"{where}.{name}") for name, arg in zip(names, node.args, strict=True)}
    for keyword in node.keywords:
        refuse_when(
            keyword.arg != "extra_fix",
            FINDING_CATALOG_PLANT,
            f"{where}: unexpected keyword {keyword.arg!r}",
        )
        row["extra_fix"] = _literal(keyword.value, f"{where}.extra_fix")
    return row


def ast_extract_mill(source: str) -> dict[str, Any]:
    """Return FACTORY/PREFIX/BAN and the plants filename from a mill module."""

    tree = ast.parse(source)
    assigns = _assign_map(tree)
    missing = [name for name in ("FACTORY", "PREFIX", "BAN") if name not in assigns]
    refuse_when(bool(missing), FINDING_CATALOG_MILL, f"mill source missing {missing}")
    factory = _literal(assigns["FACTORY"], "FACTORY")
    prefix = _literal(assigns["PREFIX"], "PREFIX")
    ban = _literal(assigns["BAN"], "BAN")
    refuse_when(
        factory != FACTORY or prefix != FAMILY_PREFIX,
        FINDING_CATALOG_SCHEMA,
        f"mill identity {factory!r}/{prefix!r} is not {FACTORY}/{FAMILY_PREFIX}",
    )
    refuse_when(set(ban) != set(BAN), FINDING_CATALOG_BANNED, f"mill BAN drifted: {ban}")
    plants = _plants_path(tree)
    return {
        "factory": factory,
        "prefix": prefix,
        "ban": sorted(BAN),
        "plants": f"experiments/{plants}",
    }


def _pair_item(item: ast.AST, index: int) -> tuple[ast.AST, ast.AST]:
    if not isinstance(item, (ast.Tuple, ast.List)) or len(item.elts) != 2:
        refuse(FINDING_CATALOG_PLANT, f"PAIRS[{index}] must be an (ok, bad) pair")
    return item.elts[0], item.elts[1]


def ast_extract_plants(source: str) -> dict[str, Any]:
    """Return CATALOG_FIRST and constructor-arg pairs from a plants module."""

    tree = ast.parse(source)
    assigns = _assign_map(tree)
    refuse_when(
        "CATALOG_FIRST" not in assigns or "PAIRS" not in assigns,
        FINDING_CATALOG_PLANT,
        "plants source missing CATALOG_FIRST/PAIRS",
    )
    first = _literal(assigns["CATALOG_FIRST"], "CATALOG_FIRST")
    refuse_when(
        not isinstance(first, int) or isinstance(first, bool),
        FINDING_CATALOG_PLANT,
        "CATALOG_FIRST must be an int",
    )
    payload = assigns["PAIRS"]
    refuse_when(not isinstance(payload, ast.List), FINDING_CATALOG_PLANT, "PAIRS must be a list")
    pairs: list[dict[str, Any]] = []
    for index, item in enumerate(payload.elts):
        ok_node, bad_node = _pair_item(item, index)
        pairs.append(
            {
                "round": first + index,
                "ok": _ctor_row(ok_node, OK_ARG_NAMES, f"PAIRS[{index}].ok"),
                "bad": _ctor_row(bad_node, BAD_ARG_NAMES, f"PAIRS[{index}].bad"),
            }
        )
    return {"catalog_first": first, "n_pairs": len(pairs), "pairs": pairs}


def ast_extract_catalog(
    mill_sources: Mapping[str, str],
    plants_sources: Mapping[str, str],
    *,
    commit: str = LEGACY_COMMIT,
) -> dict[str, Any]:
    """Build the catalog document from mill/plants source text (AST only)."""

    mills: list[dict[str, Any]] = []
    pairs: list[dict[str, Any]] = []
    for mill_id, path, mill_sha, plants_path, plants_sha, catalog_first, n_pairs in MILL_SOURCES:
        refuse_when(path not in mill_sources, FINDING_CATALOG_MILL, f"missing mill source {path}")
        refuse_when(
            plants_path not in plants_sources,
            FINDING_CATALOG_MILL,
            f"missing plants source {plants_path}",
        )
        mill_text = mill_sources[path]
        plants_text = plants_sources[plants_path]
        refuse_first(
            (
                (sha256_text(mill_text) != mill_sha, FINDING_CATALOG_SCHEMA, f"{path} sha256 drifted"),
                (
                    sha256_text(plants_text) != plants_sha,
                    FINDING_CATALOG_SCHEMA,
                    f"{plants_path} sha256 drifted",
                ),
            )
        )
        extracted_mill = ast_extract_mill(mill_text)
        refuse_when(
            extracted_mill["plants"] != plants_path,
            FINDING_CATALOG_MILL,
            f"{path} plants pointer {extracted_mill['plants']!r} != {plants_path!r}",
        )
        extracted_plants = ast_extract_plants(plants_text)
        refuse_when(
            extracted_plants["catalog_first"] != catalog_first
            or extracted_plants["n_pairs"] != n_pairs,
            FINDING_CATALOG_PAIR_COUNT,
            f"{path} catalog window {extracted_plants['catalog_first']}+{extracted_plants['n_pairs']}",
        )
        mills.append(
            {
                "mill_id": mill_id,
                "path": path,
                "sha256": mill_sha,
                "plants": plants_path,
                "plants_sha256": plants_sha,
                "catalog_first": catalog_first,
                "n_pairs": n_pairs,
                "ban": sorted(BAN),
            }
        )
        for row in extracted_plants["pairs"]:
            pairs.append({"mill_id": mill_id, **row})
    refuse_when(len(mills) != N_MILLS, FINDING_CATALOG_PAIR_COUNT, f"n_mills must be {N_MILLS}")
    refuse_when(len(pairs) != N_PAIRS, FINDING_CATALOG_PAIR_COUNT, f"n_pairs must be {N_PAIRS}")
    return {
        "schema_id": SCHEMA_ID,
        "family_prefix": FAMILY_PREFIX,
        "factory": FACTORY,
        "generator": GENERATOR,
        "quota_per_round": QUOTA_PER_ROUND,
        "n_mills": len(mills),
        "n_pairs": len(pairs),
        "pairs_filename": PAIRS_FILENAME,
        "source": {"lane": LEGACY_LANE, "commit": commit},
        "mills": mills,
        "pairs": pairs,
    }


bind_import_twin(__name__)
