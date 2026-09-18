#!/usr/bin/env python3
"""AST-only ewr leftover extract. Mill scripts are parsed, never executed."""

from __future__ import annotations

import ast
import hashlib
from collections.abc import Mapping
from typing import Any

from ._contract import (
    FACTORY,
    FAMILY_PREFIX,
    FINDING_CATALOG_MILL,
    FINDING_CATALOG_PAIR_COUNT,
    FINDING_CATALOG_PLANT,
    FINDING_CATALOG_SCHEMA,
    GENERATOR,
    LEGACY_COMMIT,
    MAPPING_FIELDS,
    MILL_SOURCES,
    MillPin,
    N_PLANT_PAIRS,
    PLANTS_MILL_ID,
    START_ROUND,
    bind_import_twin,
    refuse,
    refuse_first,
    refuse_when,
)

PLANT_CALLS = frozenset(("_ok", "_bad", "_p"))

__all__ = [
    "ast_extract_catalog_rows",
    "ast_extract_mapping_pairs",
    "ast_extract_mill_constants",
    "ast_extract_plant_pairs",
    "sha256_text",
]


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _literal(node: ast.AST, where: str) -> str | int:
    if isinstance(node, ast.Constant) and isinstance(node.value, (str, int)) and not isinstance(
        node.value, bool
    ):
        return node.value
    if (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "replace"
        and isinstance(node.func.value, ast.Constant)
        and isinstance(node.func.value.value, str)
        and len(node.args) == 2
        and all(isinstance(arg, ast.Constant) and isinstance(arg.value, str) for arg in node.args)
    ):
        base = node.func.value.value
        return base.replace(node.args[0].value, node.args[1].value)
    refuse(FINDING_CATALOG_PLANT, f"{where}: plant values must be str or int literals")


def _call_kwargs(node: ast.AST, where: str) -> dict[str, str | int]:
    refuse_when(
        not isinstance(node, ast.Call)
        or not isinstance(node.func, ast.Name)
        or node.func.id not in PLANT_CALLS
        or node.args
        or any(kw.arg is None for kw in node.keywords),
        FINDING_CATALOG_PLANT,
        f"{where}: expected _ok/_bad/_p(**kwargs)",
    )
    assert isinstance(node, ast.Call)
    plant: dict[str, str | int] = {}
    for index, kw in enumerate(node.keywords):
        assert kw.arg is not None
        plant[kw.arg] = _literal(kw.value, f"{where}.{kw.arg}#{index}")
    return plant


def _pairs_node(tree: ast.Module) -> ast.AST:
    for node in tree.body:
        if isinstance(node, ast.Assign):
            names = [t.id for t in node.targets if isinstance(t, ast.Name)]
            if "PAIRS" in names:
                return node.value
    refuse(FINDING_CATALOG_PLANT, "plants source has no PAIRS assignment")


def ast_extract_plant_pairs(source: str) -> tuple[tuple[dict[str, str | int], dict[str, str | int]], ...]:
    """Return leftover-event (ok, bad) pairs from a plants module, via AST only."""

    tree = ast.parse(source)
    payload = _pairs_node(tree)
    refuse_when(
        not isinstance(payload, (ast.List, ast.Tuple)),
        FINDING_CATALOG_PLANT,
        "PAIRS must be a list or tuple of (ok, bad) tuples",
    )
    assert isinstance(payload, (ast.List, ast.Tuple))
    pairs: list[tuple[dict[str, str | int], dict[str, str | int]]] = []
    for index, item in enumerate(payload.elts):
        refuse_when(
            not isinstance(item, (ast.Tuple, ast.List)) or len(item.elts) != 2,
            FINDING_CATALOG_PLANT,
            f"PAIRS[{index}] must be an (ok, bad) pair",
        )
        assert isinstance(item, (ast.Tuple, ast.List))
        ok = _call_kwargs(item.elts[0], f"PAIRS[{index}].ok")
        bad = _call_kwargs(item.elts[1], f"PAIRS[{index}].bad")
        pairs.append((ok, bad))
    return tuple(pairs)


def ast_extract_mill_constants(source: str) -> dict[str, str | int]:
    """Return FACTORY/START/N from a mill module, via AST only."""

    tree = ast.parse(source)
    found: dict[str, str | int] = {}
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        names = [t.id for t in node.targets if isinstance(t, ast.Name)]
        for name in names:
            if name in {"FACTORY", "START", "N"}:
                found[name] = _literal(node.value, name)
    missing = [name for name in ("FACTORY", "START", "N") if name not in found]
    refuse_when(bool(missing), FINDING_CATALOG_PLANT, f"mill source missing {missing}")
    return found


def _mapping_dict(node: ast.AST, where: str) -> dict[str, str | int]:
    refuse_when(
        not isinstance(node, ast.Call)
        or not isinstance(node.func, ast.Name)
        or node.func.id != "dict"
        or node.args
        or any(kw.arg is None for kw in node.keywords),
        FINDING_CATALOG_PLANT,
        f"{where}: expected dict(**kwargs)",
    )
    assert isinstance(node, ast.Call)
    row: dict[str, str | int] = {}
    for kw in node.keywords:
        assert kw.arg is not None
        row[kw.arg] = _literal(kw.value, f"{where}.{kw.arg}")
    missing = [key for key in MAPPING_FIELDS if key not in row]
    refuse_when(bool(missing), FINDING_CATALOG_PLANT, f"{where} missing {missing}")
    extra = set(row) - set(MAPPING_FIELDS)
    refuse_when(bool(extra), FINDING_CATALOG_PLANT, f"{where} unexpected keys {sorted(extra)}")
    return row


def ast_extract_mapping_pairs(source: str) -> tuple[dict[str, str | int], ...]:
    """Return dict(**kwargs) mapping rows from an lll mill module, via AST only."""

    tree = ast.parse(source)
    payload = _pairs_node(tree)
    refuse_when(
        not isinstance(payload, ast.List),
        FINDING_CATALOG_PLANT,
        "PAIRS must be a list of dict(...) rows",
    )
    assert isinstance(payload, ast.List)
    rows: list[dict[str, str | int]] = []
    for index, item in enumerate(payload.elts):
        rows.append(_mapping_dict(item, f"PAIRS[{index}]"))
    return tuple(rows)


def _mapping_slice(
    pin: MillPin, rows: tuple[dict[str, str | int], ...]
) -> tuple[dict[str, str | int], ...]:
    refuse_when(
        pin.legacy_first is None,
        FINDING_CATALOG_MILL,
        f"{pin.mill_id} missing legacy_first",
    )
    start_index = pin.catalog_first - pin.legacy_first
    end_index = start_index + pin.n_pairs
    refuse_when(
        start_index < 0 or end_index > len(rows),
        FINDING_CATALOG_PAIR_COUNT,
        f"{pin.mill_id} slice [{start_index}:{end_index}] out of range for {len(rows)} rows",
    )
    return rows[start_index:end_index]


def ast_extract_catalog_rows(
    plants_source: str,
    mill_source: str,
    mapping_sources_by_path: Mapping[str, str],
    *,
    plants_sha256: str | None = None,
    mill_sha256: str | None = None,
    commit: str = LEGACY_COMMIT,
) -> list[dict[str, Any]]:
    """Build compact JSONL row dicts for every committed ewr mill pin."""

    constants = ast_extract_mill_constants(mill_source)
    plant_pairs = ast_extract_plant_pairs(plants_source)
    refuse_first(
        (
            (
                constants["FACTORY"] != FACTORY,
                FINDING_CATALOG_SCHEMA,
                f"mill FACTORY must be {FACTORY!r}",
            ),
            (
                constants["START"] != START_ROUND,
                FINDING_CATALOG_SCHEMA,
                f"mill START must be {START_ROUND}",
            ),
            (
                constants["N"] != N_PLANT_PAIRS or len(plant_pairs) != N_PLANT_PAIRS,
                FINDING_CATALOG_PAIR_COUNT,
                f"need {N_PLANT_PAIRS} plant pairs, got {len(plant_pairs)}",
            ),
        )
    )
    plants_sha = plants_sha256 or sha256_text(plants_source)
    mill_sha = mill_sha256 or sha256_text(mill_source)
    pinned_plants = MILL_SOURCES[0]
    refuse_first(
        (
            (
                plants_sha != pinned_plants.plants_sha256,
                FINDING_CATALOG_SCHEMA,
                "plants_sha256 drifted from the pinned leftover plants bytes",
            ),
            (
                mill_sha != pinned_plants.mill_sha256,
                FINDING_CATALOG_SCHEMA,
                "mill_sha256 drifted from the pinned leftover mill bytes",
            ),
        )
    )
    rows: list[dict[str, Any]] = []
    for index, (ok, bad) in enumerate(plant_pairs):
        rows.append(
            {
                "mill_id": PLANTS_MILL_ID,
                "round": START_ROUND + index,
                "ok": ok,
                "bad": bad,
            }
        )
    for pin in MILL_SOURCES[1:]:
        if pin.source_format != "mapping-v1":
            continue
        source = mapping_sources_by_path.get(pin.mill_path)
        refuse_when(
            source is None,
            FINDING_CATALOG_MILL,
            f"missing mapping source for {pin.mill_path}",
        )
        assert source is not None
        mapping_sha = sha256_text(source)
        refuse_when(
            mapping_sha != pin.mill_sha256,
            FINDING_CATALOG_SCHEMA,
            f"{pin.mill_id} mill_sha256 drifted from pinned bytes",
        )
        mapping_rows = _mapping_slice(pin, ast_extract_mapping_pairs(source))
        refuse_when(
            len(mapping_rows) != pin.n_pairs,
            FINDING_CATALOG_PAIR_COUNT,
            f"{pin.mill_id} expected {pin.n_pairs} mapping rows, got {len(mapping_rows)}",
        )
        for offset, mapping in enumerate(mapping_rows):
            rows.append(
                {
                    "mill_id": pin.mill_id,
                    "round": pin.catalog_first + offset,
                    "mapping": mapping,
                }
            )
    _ = commit
    return rows


bind_import_twin(__name__)
