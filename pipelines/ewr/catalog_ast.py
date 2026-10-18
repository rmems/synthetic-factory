#!/usr/bin/env python3
"""AST-only ewr leftover extract. Mill scripts are parsed, never executed."""

from __future__ import annotations

import ast
import hashlib
from collections.abc import Iterator, Mapping
from typing import Any

from ._contract import (
    FACTORY,
    FINDING_CATALOG_MILL,
    FINDING_CATALOG_PAIR_COUNT,
    FINDING_CATALOG_PLANT,
    FINDING_CATALOG_SCHEMA,
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
_DICT_CALLS = frozenset(("dict",))
_MILL_CONSTANT_NAMES = ("FACTORY", "START", "N")

__all__ = [
    "ast_extract_catalog_rows",
    "ast_extract_mapping_pairs",
    "ast_extract_mill_constants",
    "ast_extract_plant_pairs",
    "sha256_text",
]


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _str_constant(node: ast.AST) -> str | None:
    """Return the value of a string literal node, or None for anything else."""

    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _plain_literal(node: ast.AST) -> str | int | None:
    """Return the value of a str or non-bool int literal node, or None for anything else."""

    if not isinstance(node, ast.Constant):
        return None
    value = node.value
    if isinstance(value, bool) or not isinstance(value, (str, int)):
        return None
    return value


def _replace_receiver(func: ast.expr) -> str | None:
    """Return "base" when ``func`` is ``"base".replace``, or None for anything else."""

    if not isinstance(func, ast.Attribute) or func.attr != "replace":
        return None
    return _str_constant(func.value)


def _str_constant_pair(args: list[ast.expr]) -> tuple[str, str] | None:
    """Return the two values when ``args`` is exactly two string literals, or None."""

    if len(args) != 2:
        return None
    old, new = _str_constant(args[0]), _str_constant(args[1])
    if old is None or new is None:
        return None
    return old, new


def _literal_replace_args(node: ast.AST) -> tuple[str, str, str] | None:
    """Return (base, old, new) for ``"base".replace("old", "new")`` with only string literals."""

    if not isinstance(node, ast.Call):
        return None
    base = _replace_receiver(node.func)
    pair = _str_constant_pair(node.args)
    if base is None or pair is None:
        return None
    return base, pair[0], pair[1]


def _literal(node: ast.AST, where: str) -> str | int:
    plain = _plain_literal(node)
    if plain is not None:
        return plain
    replace = _literal_replace_args(node)
    if replace is not None:
        base, old, new = replace
        return base.replace(old, new)
    refuse(FINDING_CATALOG_PLANT, f"{where}: plant values must be str or int literals")


def _is_kwargs_call(node: ast.AST, names: frozenset[str]) -> bool:
    """True for ``name(**kwargs)`` where ``name`` is in ``names`` and every argument is keyword."""

    if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Name):
        return False
    return (
        node.func.id in names
        and not node.args
        and all(kw.arg is not None for kw in node.keywords)
    )


def _call_kwargs(node: ast.AST, where: str) -> dict[str, str | int]:
    refuse_when(
        not _is_kwargs_call(node, PLANT_CALLS),
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


def _constant_assignments(
    tree: ast.Module, wanted: tuple[str, ...]
) -> Iterator[tuple[str, ast.expr]]:
    """Yield ``(name, value)`` for every top-level ``name = value`` target in ``wanted``."""

    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id in wanted:
                yield target.id, node.value


def ast_extract_mill_constants(source: str) -> dict[str, str | int]:
    """Return FACTORY/START/N from a mill module, via AST only."""

    tree = ast.parse(source)
    found: dict[str, str | int] = {}
    for name, value in _constant_assignments(tree, _MILL_CONSTANT_NAMES):
        found[name] = _literal(value, name)
    missing = [name for name in _MILL_CONSTANT_NAMES if name not in found]
    refuse_when(bool(missing), FINDING_CATALOG_PLANT, f"mill source missing {missing}")
    return found


def _mapping_dict(node: ast.AST, where: str) -> dict[str, str | int]:
    refuse_when(
        not _is_kwargs_call(node, _DICT_CALLS),
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
    if pin.legacy_first is None:
        refuse(FINDING_CATALOG_MILL, f"{pin.mill_id} missing legacy_first")
    start_index = pin.catalog_first - pin.legacy_first
    end_index = start_index + pin.n_pairs
    refuse_when(
        start_index < 0 or end_index > len(rows),
        FINDING_CATALOG_PAIR_COUNT,
        f"{pin.mill_id} slice [{start_index}:{end_index}] out of range for {len(rows)} rows",
    )
    return rows[start_index:end_index]


def _check_mill_constants(
    constants: Mapping[str, str | int],
    plant_pairs: tuple[tuple[dict[str, str | int], dict[str, str | int]], ...],
) -> None:
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


def _check_leftover_pins(plants_sha: str, mill_sha: str) -> None:
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


def _plant_rows(
    plant_pairs: tuple[tuple[dict[str, str | int], dict[str, str | int]], ...],
) -> list[dict[str, Any]]:
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
    return rows


def _mapping_source(pin: MillPin, sources_by_path: Mapping[str, str]) -> str:
    source = sources_by_path.get(pin.mill_path)
    if source is not None:
        return source
    refuse(FINDING_CATALOG_MILL, f"missing mapping source for {pin.mill_path}")


def _mapping_pin_rows(pin: MillPin, source: str) -> list[dict[str, Any]]:
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
    return [
        {
            "mill_id": pin.mill_id,
            "round": pin.catalog_first + offset,
            "mapping": mapping,
        }
        for offset, mapping in enumerate(mapping_rows)
    ]


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
    _check_mill_constants(constants, plant_pairs)
    plants_sha = plants_sha256 or sha256_text(plants_source)
    mill_sha = mill_sha256 or sha256_text(mill_source)
    _check_leftover_pins(plants_sha, mill_sha)
    rows = _plant_rows(plant_pairs)
    for pin in MILL_SOURCES[1:]:
        if pin.source_format != "mapping-v1":
            continue
        rows.extend(_mapping_pin_rows(pin, _mapping_source(pin, mapping_sources_by_path)))
    _ = commit
    return rows


bind_import_twin(__name__)
