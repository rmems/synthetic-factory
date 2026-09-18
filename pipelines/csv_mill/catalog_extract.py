"""Safe AST extraction for recovered CSV mill sources."""

from __future__ import annotations

import ast
from typing import Any

from ._contract import (
    CsvRefusal,
    FACTORY,
    FINDING_PLANT_FIELD_INVALID,
    FINDING_SOURCE_NOT_PARSEABLE,
    PAIR_KEYS,
    RECORD_PREFIX,
    bind_import_twin,
)

from .catalog_validation import (
    MILL_ID_RE,
    _claim_unique,
    _distinct_episode_slugs,
    _require_int,
    _require_text,
)


def _const_eval(node: ast.AST) -> Any:
    """Literal values only. Never exec, compile, or eval."""

    try:
        return ast.literal_eval(node)
    except (ValueError, TypeError, SyntaxError) as exc:
        raise CsvRefusal(
            FINDING_SOURCE_NOT_PARSEABLE,
            f"plant source is not a constant ({type(node).__name__})",
        ) from exc


def _assigned_name(node: ast.AST) -> tuple[str, ast.AST] | None:
    match node:
        case ast.Assign(targets=[ast.Name(id=name)], value=value):
            return name, value
        case ast.AnnAssign(target=ast.Name(id=name), value=ast.expr() as value):
            return name, value
    return None


def _dict_keywords(node: ast.AST, where: str) -> list[ast.keyword]:
    match node:
        case ast.Call(func=ast.Name(id="dict"), args=[], keywords=keywords):
            return keywords
    raise CsvRefusal(FINDING_SOURCE_NOT_PARSEABLE, f"{where} must be keyword-only dict()")


def _dict_call(node: ast.AST, where: str) -> dict[str, Any]:
    mapped: dict[str, Any] = {}
    for keyword in _dict_keywords(node, where):
        if keyword.arg is None:
            raise CsvRefusal(FINDING_SOURCE_NOT_PARSEABLE, f"{where} uses keyword unpacking")
        if keyword.arg in mapped:
            raise CsvRefusal(FINDING_SOURCE_NOT_PARSEABLE, f"{where} has duplicate keywords")
        mapped[keyword.arg] = _const_eval(keyword.value)
    return mapped


def _parse_source(text: str, source: str) -> ast.Module:
    try:
        return ast.parse(text)
    except SyntaxError as exc:
        raise CsvRefusal(FINDING_SOURCE_NOT_PARSEABLE, f"{source} does not parse: {exc}") from exc


def _source_assignments(text: str, source: str) -> dict[str, ast.AST]:
    """Collect the source pins and require one unambiguous assignment each."""

    tree = _parse_source(text, source)
    assignments: dict[str, ast.AST] = {}
    names = {"PAIRS", "CATALOG_FIRST", "FAC", "FACTORY", "PREFIX"}
    for node in tree.body:
        assigned = _assigned_name(node)
        if assigned is None or assigned[0] not in names:
            continue
        name, value = assigned
        # FAC and FACTORY are aliases for the same pin.
        name = "FACTORY" if name == "FAC" else name
        if name in assignments:
            raise CsvRefusal(FINDING_SOURCE_NOT_PARSEABLE, f"{source} repeats {name}")
        assignments[name] = value
    return assignments


def _source_pins(assignments: dict[str, ast.AST], source: str) -> None:
    for name, expected in (("FACTORY", FACTORY), ("PREFIX", RECORD_PREFIX)):
        if name not in assignments:
            raise CsvRefusal(FINDING_SOURCE_NOT_PARSEABLE, f"{source} is missing {name}")
        pin = assignments[name]
        if _const_eval(pin) != expected:
            raise CsvRefusal(FINDING_SOURCE_NOT_PARSEABLE, f"{source} {name} must be {expected}")


def _source_pairs(assignments: dict[str, ast.AST], source: str) -> list[ast.expr]:
    _source_pins(assignments, source)
    pairs = assignments.get("PAIRS")
    if not isinstance(pairs, ast.List) or not pairs.elts:
        raise CsvRefusal(FINDING_SOURCE_NOT_PARSEABLE, f"{source} has no PAIRS list")
    return pairs.elts


def _source_base(
    assignments: dict[str, ast.AST], mill_id: str, source: str, base_round: int | None
) -> int:
    if not MILL_ID_RE.fullmatch(mill_id):
        raise CsvRefusal(FINDING_PLANT_FIELD_INVALID, f"mill_id {mill_id!r} is not csv_rNNN")
    base = base_round
    if base is None and "CATALOG_FIRST" in assignments:
        base = _const_eval(assignments["CATALOG_FIRST"])
    if base is None:
        base = _suffix_round(mill_id)
    return _require_int(base, 1, f"{source} CATALOG_FIRST", FINDING_PLANT_FIELD_INVALID)


def _suffix_round(mill_id: str) -> int:
    try:
        return int(mill_id[len("csv_r") :])
    except ValueError as exc:
        raise CsvRefusal(FINDING_PLANT_FIELD_INVALID, "mill round suffix exceeds the integer limit") from exc


def _pair_keys(mapping: dict[str, Any], where: str) -> None:
    expected = set(PAIR_KEYS)
    missing = expected.difference(mapping)
    if missing:
        raise CsvRefusal(FINDING_SOURCE_NOT_PARSEABLE, f"{where} missing {min(missing)}")
    extra = set(mapping).difference(expected)
    if extra:
        raise CsvRefusal(FINDING_SOURCE_NOT_PARSEABLE, f"{where} has extra {min(extra)}")


def _pair_fields(item: ast.AST, where: str) -> dict[str, str]:
    mapping = _dict_call(item, where)
    _pair_keys(mapping, where)
    fields = {
        key: _require_text(mapping[key], f"{where}.{key}", FINDING_SOURCE_NOT_PARSEABLE)
        for key in PAIR_KEYS
    }
    _distinct_episode_slugs(fields, where)
    return fields


def plants_from_source(
    text: str,
    *,
    mill_id: str,
    source: str,
    base_round: int | None = None,
) -> tuple[dict[str, Any], ...]:
    """AST-extract ``PAIRS = [dict(...), ...]``. Never exec."""

    assignments = _source_assignments(text, source)
    pairs = _source_pairs(assignments, source)
    base = _source_base(assignments, mill_id, source, base_round)
    rows = []
    seen = {key: set() for key in ("slug", "fail", "ticket")}
    for index, item in enumerate(pairs):
        fields = _pair_fields(item, f"{source} PAIRS[{index}]")
        for key, values in seen.items():
            _claim_unique(values, fields[key], f"{source} duplicate {key}")
        rows.append(
            {
                "plant_id": f"{mill_id}:{fields['slug']}",
                "mill_id": mill_id,
                "source": source,
                "base_round": base,
                "index": index,
                **fields,
            }
        )
    return tuple(rows)


bind_import_twin(__name__)
