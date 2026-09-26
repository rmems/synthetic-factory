"""Strict catalog row, JSONL, and registry validation primitives."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from ._contract import (
    CsvRefusal,
    FINDING_CATALOG_FIELD_INVALID,
    FINDING_CATALOG_FIELD_MISSING,
    FINDING_FACTORY_NOT_REGISTERED,
    FINDING_PLANT_DUPLICATE,
    FINDING_PLANT_FIELD_INVALID,
    FINDING_PLANT_FIELD_MISSING,
    PAIR_KEYS,
    LEGACY_SOURCE,
    bind_import_twin,
    load_strict_json,
    dumps_exact_json,
    is_integer,
    json_integer_is_bounded,
    repo_root,
)

if __package__.startswith("pipelines."):
    from ..curate_identity_registry import IdentityCurationError, load_registry
    from ..strict_jsonl import strict_lf_jsonl_lines
else:
    from curate_identity_registry import IdentityCurationError, load_registry
    from strict_jsonl import strict_lf_jsonl_lines

from .catalog_models import Mill, Plant

MILL_ID_RE = re.compile(r"^csv_r\d+$", re.ASCII)
SLUG_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
TICKET_RE = re.compile(r"^[A-Z0-9]+(?:-[A-Z0-9]+)+$")


def _require_mapping(value: Any, where: str, code: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise CsvRefusal(code, f"{where} must be an object")
    return value


def _field(mapping: Any, key: str, kind: type, where: str) -> Any:
    mapping = _require_mapping(mapping, where, FINDING_CATALOG_FIELD_INVALID)
    if key not in mapping:
        raise CsvRefusal(FINDING_CATALOG_FIELD_MISSING, f"{where}.{key} is missing")
    value = mapping[key]
    # Booleans cannot satisfy integer pins.
    if not _field_type_matches(value, kind):
        raise CsvRefusal(FINDING_CATALOG_FIELD_INVALID, f"{where}.{key} has the wrong type")
    return value


def _field_type_matches(value: Any, kind: type) -> bool:
    return is_integer(value) if kind is int else isinstance(value, kind)


def _require_text(value: Any, where: str, code: str) -> str:
    if not isinstance(value, str):
        raise CsvRefusal(code, f"{where} must be a non-empty stripped string")
    if not value or value != value.strip():
        raise CsvRefusal(code, f"{where} must be a non-empty stripped string")
    try:
        value.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise CsvRefusal(code, f"{where} must contain Unicode scalar values") from exc
    return value


def _require_int(value: Any, minimum: int, where: str, code: str) -> int:
    if not is_integer(value):
        raise CsvRefusal(code, f"{where} must be an integer >= {minimum}")
    if value < minimum:
        raise CsvRefusal(code, f"{where} must be an integer >= {minimum}")
    _require_bounded_int(value, where, code)
    return value


def _require_bounded_int(value: int, where: str, code: str) -> None:
    if not json_integer_is_bounded(value):
        raise CsvRefusal(code, f"{where} exceeds the exact-JSON integer domain")


def _plant_field(row: dict[str, Any], key: str, where: str) -> Any:
    if key not in row:
        raise CsvRefusal(FINDING_PLANT_FIELD_MISSING, f"{where}.{key} is missing")
    return row[key]


def _plant_text_field(row: dict[str, Any], key: str, where: str) -> str:
    return _require_text(_plant_field(row, key, where), f"{where}.{key}", FINDING_PLANT_FIELD_INVALID)


def _plant_identity(row: dict[str, Any], where: str) -> tuple[str, str]:
    mill_id = _plant_text_field(row, "mill_id", where)
    if not MILL_ID_RE.fullmatch(mill_id):
        raise CsvRefusal(FINDING_PLANT_FIELD_INVALID, f"{where}.mill_id is not csv_rNNN")
    plant_id = _plant_text_field(row, "plant_id", where)
    expected = f"{mill_id}:{row['slug']}"
    if plant_id != expected:
        raise CsvRefusal(FINDING_PLANT_FIELD_INVALID, f"{where}.plant_id must be {expected!r}")
    return plant_id, mill_id


def _plant_pair_fields(row: dict[str, Any], where: str) -> dict[str, str]:
    fields = {
        key: _plant_text_field(row, key, where)
        for key in PAIR_KEYS
    }
    _require_pair_identifiers(fields, where)
    _distinct_episode_slugs(fields, where)
    return fields


def _require_pair_identifiers(fields: dict[str, str], where: str) -> None:
    for key, pattern in (("slug", SLUG_RE), ("fail", SLUG_RE), ("ticket", TICKET_RE)):
        if not pattern.fullmatch(fields[key]):
            raise CsvRefusal(FINDING_PLANT_FIELD_INVALID, f"{where}.{key} has invalid syntax")


def _distinct_episode_slugs(fields: dict[str, str], where: str) -> None:
    if fields["fail"] == fields["slug"]:
        raise CsvRefusal(FINDING_PLANT_FIELD_INVALID, f"{where} has colliding episode slugs")


def _plant_from_row(row: Any, where: str) -> Plant:
    row = _require_mapping(row, where, FINDING_PLANT_FIELD_INVALID)
    fields = _plant_pair_fields(row, where)
    plant_id, mill_id = _plant_identity(row, where)
    plant = Plant(
        plant_id=plant_id,
        mill_id=mill_id,
        source=_plant_text_field(row, "source", where),
        base_round=_require_int(
            _plant_field(row, "base_round", where), 1, f"{where}.base_round", FINDING_PLANT_FIELD_INVALID
        ),
        index=_require_int(_plant_field(row, "index", where), 0, f"{where}.index", FINDING_PLANT_FIELD_INVALID),
        **fields,
    )
    _require_bounded_int(
        plant.base_round + plant.index, f"{where}.effective_round", FINDING_PLANT_FIELD_INVALID
    )
    return plant


def _mill_positive_int(row: Any, key: str, where: str) -> int:
    value = _field(row, key, int, where)
    if value < 1:
        raise CsvRefusal(FINDING_CATALOG_FIELD_INVALID, f"{where}.{key} must be a positive int")
    _require_bounded_int(value, f"{where}.{key}", FINDING_CATALOG_FIELD_INVALID)
    return value


def _mill_from_row(row: Any, where: str) -> Mill:
    text_fields = {
        key: _require_text(
            _field(row, key, str, where), f"{where}.{key}", FINDING_CATALOG_FIELD_INVALID
        )
        for key in ("mill_id", "source")
    }
    if not MILL_ID_RE.fullmatch(text_fields["mill_id"]):
        raise CsvRefusal(FINDING_CATALOG_FIELD_INVALID, f"{where}.mill_id is not csv_rNNN")
    if text_fields["source"] != LEGACY_SOURCE:
        raise CsvRefusal(FINDING_CATALOG_FIELD_INVALID, f"{where}.source is not the pinned script")
    return Mill(
        **text_fields,
        base_round=_mill_round(row, text_fields["mill_id"], where),
        plant_count=_mill_positive_int(row, "plant_count", where),
    )


def _mill_round(row: Any, mill_id: str, where: str) -> int:
    base = _mill_positive_int(row, "base_round", where)
    return _require_mill_round(mill_id, base, FINDING_CATALOG_FIELD_INVALID)


def _require_mill_round(mill_id: str, base: int, code: str) -> int:
    if mill_id.removeprefix("csv_r").lstrip("0") != dumps_exact_json(base):
        raise CsvRefusal(code, "mill_id suffix must match base_round")
    return base


def _shown_claim(value: object) -> str:
    if is_integer(value):
        return dumps_exact_json(value)
    return str(value)


def _claim_unique(seen: set, value: object, detail: str) -> None:
    if value in seen:
        raise CsvRefusal(FINDING_PLANT_DUPLICATE, f"{detail} {_shown_claim(value)}")
    seen.add(value)


def _jsonl_row(line: str, where: str) -> Any:
    try:
        return load_strict_json(line)
    except (ValueError, RecursionError) as exc:
        raise CsvRefusal(FINDING_CATALOG_FIELD_INVALID, f"{where} is not strict JSON") from exc


def _read_jsonl(payload: bytes, path: Path) -> tuple[Any, ...]:
    """Parse the authenticated bytes using physical LF boundaries only."""

    if not payload:
        raise CsvRefusal(FINDING_CATALOG_FIELD_INVALID, f"{path.name} must be LF-framed jsonl")
    try:
        lines = strict_lf_jsonl_lines(payload, path.name)
    except ValueError as exc:
        raise CsvRefusal(FINDING_CATALOG_FIELD_INVALID, str(exc)) from exc
    return tuple(_jsonl_row(line, f"{path.name}:{i}") for i, line in enumerate(lines, 1))


def _registry_factory_ids() -> set[str]:
    path = repo_root() / "config" / "FACTORY-REGISTRY.json"
    try:
        registry = load_registry(path)
    except IdentityCurationError as exc:
        raise CsvRefusal(
            FINDING_FACTORY_NOT_REGISTERED, f"factory registry is unreadable: {exc}"
        ) from exc
    return set(registry.by_path_id)


bind_import_twin(__name__)
