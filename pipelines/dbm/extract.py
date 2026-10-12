#!/usr/bin/env python3
"""AST-only extractors for dbm leftover mills. Never compile, exec, or eval them."""

from __future__ import annotations

import ast
import hashlib
from typing import Any

from ._contract import (
    CONSTRUCTORS,
    FACTORY,
    FINDING_CATALOG_FIELD_INVALID,
    FINDING_CATALOG_PLANT,
    GENERATOR,
    PLANT_KEYS,
    START_ROUND,
    bind_import_twin,
    refuse,
    refuse_when,
)

__all__ = [
    "ast_extract_gen_slugs",
    "ast_extract_leftover3_constants",
    "ast_extract_leftover3_plants",
    "ast_extract_mill_catalog",
    "sha256_text",
]


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _assigned_value(node: ast.stmt, name: str) -> ast.AST | None:
    """The value ``node`` binds to ``name`` (plain or annotated assignment), else None."""

    if isinstance(node, ast.Assign):
        names = [target.id for target in node.targets if isinstance(target, ast.Name)]
        return node.value if name in names else None
    if not isinstance(node, ast.AnnAssign) or not isinstance(node.target, ast.Name):
        return None
    return node.value if node.target.id == name else None


def _assignment(tree: ast.Module, name: str) -> ast.AST:
    for node in tree.body:
        value = _assigned_value(node, name)
        if value is not None:
            return value
    refuse(FINDING_CATALOG_PLANT, f"source has no {name} assignment")


def _str_or_int(node: ast.AST, where: str) -> str | int:
    refuse_when(
        not isinstance(node, ast.Constant)
        or not isinstance(node.value, (str, int))
        or isinstance(node.value, bool),
        FINDING_CATALOG_PLANT,
        f"{where}: values must be str or int literals",
    )
    assert isinstance(node, ast.Constant)
    return node.value


def _slug_literal(node: ast.AST, where: str) -> str:
    value = _str_or_int(node, where)
    refuse_when(
        not isinstance(value, str) or not value,
        FINDING_CATALOG_PLANT,
        f"{where}: slug must be a non-empty string",
    )
    assert isinstance(value, str)
    return value


def _is_pl_call(node: ast.AST) -> bool:
    """``pl(**kwargs)``: a call of the name ``pl`` with named keywords only."""

    if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Name):
        return False
    if node.func.id != "pl" or node.args:
        return False
    return all(keyword.arg is not None for keyword in node.keywords)


def _pl_text(keyword: ast.keyword, index: int, where: str) -> str:
    value = _str_or_int(keyword.value, f"{where}.{keyword.arg}#{index}")
    refuse_when(
        not isinstance(value, str) or not value,
        FINDING_CATALOG_PLANT,
        f"{where}.{keyword.arg} must be a non-empty string",
    )
    assert isinstance(value, str)
    return value


def _pl_kwargs(node: ast.AST, where: str) -> dict[str, str]:
    refuse_when(not _is_pl_call(node), FINDING_CATALOG_PLANT, f"{where}: expected pl(**kwargs)")
    assert isinstance(node, ast.Call)
    plant: dict[str, str] = {}
    for index, keyword in enumerate(node.keywords):
        assert keyword.arg is not None
        plant[keyword.arg] = _pl_text(keyword, index, where)
    missing = [key for key in PLANT_KEYS if key not in plant]
    refuse_when(bool(missing), FINDING_CATALOG_PLANT, f"{where} missing {missing}")
    extra = [key for key in plant if key not in PLANT_KEYS]
    refuse_when(bool(extra), FINDING_CATALOG_PLANT, f"{where} extra {extra}")
    return {key: plant[key] for key in PLANT_KEYS}


def ast_extract_leftover3_plants(source: str) -> tuple[dict[str, str], ...]:
    """Return leftover3 ``pl(**kwargs)`` plants from mill source text."""

    tree = ast.parse(source)
    payload = _assignment(tree, "PLANTS")
    refuse_when(
        not isinstance(payload, ast.List),
        FINDING_CATALOG_PLANT,
        "PLANTS must be a list of pl(...) calls",
    )
    assert isinstance(payload, ast.List)
    return tuple(
        _pl_kwargs(item, f"PLANTS[{index}]") for index, item in enumerate(payload.elts)
    )


_LEFTOVER3_CONSTANTS = ("FACTORY_SLUG", "GENERATOR", "START_ROUND")


def _leftover3_constant_values(tree: ast.Module) -> dict[str, str | int]:
    found: dict[str, str | int] = {}
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        names = [target.id for target in node.targets if isinstance(target, ast.Name)]
        for name in names:
            if name in _LEFTOVER3_CONSTANTS:
                found[name] = _str_or_int(node.value, name)
    return found


def ast_extract_leftover3_constants(source: str) -> dict[str, str | int]:
    """Return FACTORY_SLUG / GENERATOR / START_ROUND from leftover3 mill text."""

    found = _leftover3_constant_values(ast.parse(source))
    missing = [name for name in _LEFTOVER3_CONSTANTS if name not in found]
    refuse_when(bool(missing), FINDING_CATALOG_PLANT, f"leftover3 mill missing {missing}")
    refuse_when(
        found["FACTORY_SLUG"] != FACTORY,
        FINDING_CATALOG_FIELD_INVALID,
        f"FACTORY_SLUG must be {FACTORY!r}",
    )
    refuse_when(
        found["GENERATOR"] != GENERATOR,
        FINDING_CATALOG_FIELD_INVALID,
        f"GENERATOR must be {GENERATOR!r}",
    )
    refuse_when(
        found["START_ROUND"] != START_ROUND,
        FINDING_CATALOG_FIELD_INVALID,
        f"START_ROUND must be {START_ROUND}",
    )
    return found


def _slug_from_call(node: ast.AST, where: str) -> tuple[str, str]:
    refuse_when(
        not isinstance(node, ast.Call) or not isinstance(node.func, ast.Name),
        FINDING_CATALOG_PLANT,
        f"{where}: expected P/Q/R(...) call",
    )
    assert isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    refuse_when(
        node.func.id not in CONSTRUCTORS,
        FINDING_CATALOG_PLANT,
        f"{where}: constructor {node.func.id!r} is not a dbm plant constructor",
    )
    if node.args:
        return node.func.id, _slug_literal(node.args[0], f"{where}.slug")
    for keyword in node.keywords:
        if keyword.arg == "slug":
            return node.func.id, _slug_literal(keyword.value, f"{where}.slug")
    refuse(FINDING_CATALOG_PLANT, f"{where}: plant call has no slug")


def ast_extract_mill_catalog(source: str) -> dict[str, Any]:
    """Return constructor, CATALOG_FIRST, and pair slugs from a leftover mill."""

    tree = ast.parse(source)
    first_node = _assignment(tree, "CATALOG_FIRST")
    catalog_first = _str_or_int(first_node, "CATALOG_FIRST")
    refuse_when(
        not isinstance(catalog_first, int),
        FINDING_CATALOG_PLANT,
        "CATALOG_FIRST must be an int literal",
    )
    payload = _assignment(tree, "PAIRS")
    refuse_when(
        not isinstance(payload, ast.List),
        FINDING_CATALOG_PLANT,
        "PAIRS must be a list of (ok, bad) tuples",
    )
    assert isinstance(payload, ast.List)
    slugs: list[str] = []
    constructors: set[str] = set()
    for index, item in enumerate(payload.elts):
        refuse_when(
            not isinstance(item, (ast.Tuple, ast.List)) or len(item.elts) != 2,
            FINDING_CATALOG_PLANT,
            f"PAIRS[{index}] must be an (ok, bad) pair",
        )
        assert isinstance(item, (ast.Tuple, ast.List))
        for side, label in ((item.elts[0], "ok"), (item.elts[1], "bad")):
            constructor, slug = _slug_from_call(side, f"PAIRS[{index}].{label}")
            constructors.add(constructor)
            slugs.append(slug)
    refuse_when(
        len(constructors) != 1,
        FINDING_CATALOG_PLANT,
        f"PAIRS mixed constructors {sorted(constructors)}",
    )
    return {
        "catalog_first": catalog_first,
        "constructor": next(iter(constructors)),
        "pair_count": len(payload.elts),
        "plant_count": len(slugs),
        "slugs": tuple(slugs),
    }


def ast_extract_gen_slugs(source: str) -> tuple[str, ...]:
    """Return first-tuple slugs from ``_gen_dbm_plants_r1340.py``."""

    tree = ast.parse(source)
    payload = _assignment(tree, "PLANTS")
    refuse_when(
        not isinstance(payload, ast.List),
        FINDING_CATALOG_PLANT,
        "gen PLANTS must be a list of tuples",
    )
    assert isinstance(payload, ast.List)
    slugs: list[str] = []
    for index, item in enumerate(payload.elts):
        refuse_when(
            not isinstance(item, (ast.Tuple, ast.List)) or not item.elts,
            FINDING_CATALOG_PLANT,
            f"PLANTS[{index}] must be a non-empty tuple",
        )
        assert isinstance(item, (ast.Tuple, ast.List))
        slugs.append(_slug_literal(item.elts[0], f"PLANTS[{index}].slug"))
    return tuple(slugs)


bind_import_twin(__name__)
