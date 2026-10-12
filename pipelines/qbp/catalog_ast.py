#!/usr/bin/env python3
"""AST-only leftover extract. Mill scripts are parsed, never executed."""

from __future__ import annotations

import ast
import hashlib
from collections.abc import Mapping
from typing import Any, NoReturn

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


def _unsupported(node: ast.AST, where: str) -> NoReturn:
    refuse(FINDING_CATALOG_PLANT, f"{where}: unsupported {type(node).__name__}")


def _constant_literal(node: ast.Constant, where: str) -> Any:
    value = node.value
    if not isinstance(value, (str, int, float, bool)) and value is not None:
        _unsupported(node, where)
    return value


def _signed_literal(node: ast.UnaryOp, where: str) -> Any:
    value = _literal(node.operand, where)
    refuse_when(
        not isinstance(value, (int, float)) or isinstance(value, bool),
        FINDING_CATALOG_PLANT,
        f"{where}: unary operand must be a number",
    )
    return -value if isinstance(node.op, ast.USub) else value


def _sequence_literal(node: ast.AST, where: str) -> list[Any]:
    if isinstance(node, ast.List):
        return [_literal(elt, f"{where}[]") for elt in node.elts]
    if isinstance(node, ast.Tuple):
        return [_literal(elt, f"{where}()") for elt in node.elts]
    if not isinstance(node, ast.Set):
        _unsupported(node, where)
    return [_literal(elt, where) for elt in node.elts]


def _literal(node: ast.AST, where: str) -> Any:
    if isinstance(node, ast.Constant):
        return _constant_literal(node, where)
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.USub, ast.UAdd)):
        return _signed_literal(node, where)
    if isinstance(node, ast.Dict):
        return _literal_dict(node, where)
    return _sequence_literal(node, where)


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


def _str_call_argument(path_node: ast.AST) -> ast.AST | None:
    """The first argument of a ``str(...)`` call, if ``path_node`` is one."""
    if not isinstance(path_node, ast.Call) or not isinstance(path_node.func, ast.Name):
        return None
    if path_node.func.id != "str" or not path_node.args:
        return None
    return path_node.args[0]


def _plants_filename(path_node: ast.AST) -> str | None:
    joined = _str_call_argument(path_node)
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


def _pinned_texts(
    source: tuple[Any, ...], mill_sources: Mapping[str, str], plants_sources: Mapping[str, str]
) -> tuple[str, str]:
    """The mill and plants texts for one pinned source, refused when absent or drifted."""
    _mill_id, path, mill_sha, plants_path, plants_sha, _first, _n_pairs = source
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
    return mill_text, plants_text


def _mill_pair_rows(
    source: tuple[Any, ...], mill_text: str, plants_text: str
) -> list[dict[str, Any]]:
    """AST-extract one mill's plants pointer and pairs; refuse a drifted pointer or window."""
    mill_id, path, _mill_sha, plants_path, _plants_sha, catalog_first, n_pairs = source
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
    return [{"mill_id": mill_id, **row} for row in extracted_plants["pairs"]]


def _mill_entry(source: tuple[Any, ...]) -> dict[str, Any]:
    mill_id, path, mill_sha, plants_path, plants_sha, catalog_first, n_pairs = source
    return {
        "mill_id": mill_id,
        "path": path,
        "sha256": mill_sha,
        "plants": plants_path,
        "plants_sha256": plants_sha,
        "catalog_first": catalog_first,
        "n_pairs": n_pairs,
        "ban": sorted(BAN),
    }


def ast_extract_catalog(
    mill_sources: Mapping[str, str],
    plants_sources: Mapping[str, str],
    *,
    commit: str = LEGACY_COMMIT,
) -> dict[str, Any]:
    """Build the catalog document from mill/plants source text (AST only)."""

    mills: list[dict[str, Any]] = []
    pairs: list[dict[str, Any]] = []
    for source in MILL_SOURCES:
        mill_text, plants_text = _pinned_texts(source, mill_sources, plants_sources)
        rows = _mill_pair_rows(source, mill_text, plants_text)
        mills.append(_mill_entry(source))
        pairs.extend(rows)
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
