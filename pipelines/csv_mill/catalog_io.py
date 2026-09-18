"""Pinned catalog loading orchestration."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable
from pathlib import Path
from typing import Any

from ._contract import (
    CATALOG_FILENAME,
    CATALOG_FORMAT,
    CsvRefusal,
    FACTORY,
    FINDING_CATALOG_FIELD_INVALID,
    FINDING_CATALOG_FILE_MISSING,
    FINDING_FACTORY_NOT_REGISTERED,
    FINDING_PLANTS_SHA_MISMATCH,
    MILL_PREFIX,
    PLANTS_FILENAME,
    QUOTA_PER_ROUND,
    RECORD_KIND,
    RECORD_PREFIX,
    bind_import_twin,
    load_strict_json,
)
from .catalog_models import Catalog, Mill, Plant
from .catalog_validation import (
    _claim_unique,
    _field,
    _mill_from_row,
    _plant_from_row,
    _read_jsonl,
    _registry_factory_ids,
    _require_text,
)


def _read_bytes(path: Path) -> bytes:
    try:
        return path.read_bytes()
    except OSError as exc:
        raise CsvRefusal(FINDING_CATALOG_FILE_MISSING, f"{path} is missing") from exc


def _read_metadata(path: Path) -> Any:
    payload = _read_bytes(path)
    try:
        return load_strict_json(payload.decode("utf-8"))
    except ValueError as exc:
        raise CsvRefusal(
            FINDING_CATALOG_FIELD_INVALID, f"{CATALOG_FILENAME} is not strict JSON"
        ) from exc


def _metadata(catalog_dir: Path) -> dict[str, Any]:
    meta = _read_metadata(catalog_dir / CATALOG_FILENAME)
    _require_text(
        _field(meta, "catalog_id", str, CATALOG_FILENAME),
        f"{CATALOG_FILENAME}.catalog_id",
        FINDING_CATALOG_FIELD_INVALID,
    )
    pins = {
        "format": CATALOG_FORMAT,
        "factory": FACTORY,
        "mill_prefix": MILL_PREFIX,
        "record_kind": RECORD_KIND,
        "record_prefix": RECORD_PREFIX,
        "quota_per_round": QUOTA_PER_ROUND,
    }
    for key, expected in pins.items():
        if _field(meta, key, type(expected), CATALOG_FILENAME) != expected:
            raise CsvRefusal(
                FINDING_CATALOG_FIELD_INVALID,
                f"{CATALOG_FILENAME}.{key} must be {expected}",
            )
    return meta


def _authenticated_plants(
    catalog_dir: Path, meta: dict[str, Any], sha256_bytes: Callable[[bytes], str]
) -> tuple[bytes, str]:
    pin = _field(meta, "plants_sha256", str, CATALOG_FILENAME)
    path = catalog_dir / PLANTS_FILENAME
    payload = _read_bytes(path)
    digest = sha256_bytes(payload)
    if digest != pin:
        raise CsvRefusal(
            FINDING_PLANTS_SHA_MISMATCH,
            f"{PLANTS_FILENAME} digest {digest} != catalog pin {pin}",
        )
    return payload, digest


def _pinned_plants(
    catalog_dir: Path, meta: dict[str, Any], sha256_bytes: Callable[[bytes], str]
) -> tuple[tuple[Plant, ...], str]:
    count = _field(meta, "plant_count", int, CATALOG_FILENAME)
    payload, digest = _authenticated_plants(catalog_dir, meta, sha256_bytes)
    path = catalog_dir / PLANTS_FILENAME
    rows = _read_jsonl(payload, path)
    if len(rows) != count:
        raise CsvRefusal(
            FINDING_CATALOG_FIELD_INVALID,
            f"{CATALOG_FILENAME}.plant_count is {count}, file has {len(rows)}",
        )
    plants = tuple(
        _plant_from_row(row, f"{PLANTS_FILENAME}:{i}") for i, row in enumerate(rows, start=1)
    )
    return plants, digest


def _group_plants(plants: tuple[Plant, ...]) -> dict[str, list[Plant]]:
    """Enforce global identity uniqueness while grouping plants by mill."""

    groups: dict[str, list[Plant]] = defaultdict(list)
    seen = {key: set() for key in ("plant_id", "slug", "fail", "ticket")}
    for plant in plants:
        for key, values in seen.items():
            _claim_unique(values, getattr(plant, key), f"duplicate {key}")
        groups[plant.mill_id].append(plant)
    return groups


def _check_mill_base(mill: Mill, plants: list[Plant]) -> None:
    for plant in plants:
        if plant.base_round != mill.base_round:
            raise CsvRefusal(
                FINDING_CATALOG_FIELD_INVALID, f"{plant.plant_id} base_round != mill base_round"
            )


def _check_mill(mill: Mill, plants: list[Plant]) -> None:
    if len(plants) != mill.plant_count:
        raise CsvRefusal(
            FINDING_CATALOG_FIELD_INVALID,
            f"{mill.mill_id} plant_count {mill.plant_count} != {len(plants)}",
        )
    _check_mill_base(mill, plants)
    if {plant.index for plant in plants} != set(range(mill.plant_count)):
        raise CsvRefusal(
            FINDING_CATALOG_FIELD_INVALID,
            f"{mill.mill_id} indices must be contiguous from zero",
        )


def _mill_rows(meta: dict[str, Any]) -> tuple[Mill, ...]:
    rows = _field(meta, "mills", list, CATALOG_FILENAME)
    mills = tuple(
        _mill_from_row(row, f"{CATALOG_FILENAME}.mills[{i}]") for i, row in enumerate(rows)
    )
    if len({mill.mill_id for mill in mills}) != len(mills):
        raise CsvRefusal(FINDING_CATALOG_FIELD_INVALID, "catalog contains duplicate mill_id rows")
    return mills


def _catalog_mills(meta: dict[str, Any], plants: tuple[Plant, ...]) -> tuple[Mill, ...]:
    mills = _mill_rows(meta)
    mill_ids = {mill.mill_id for mill in mills}
    groups = _group_plants(plants)
    if mill_ids != set(groups):
        raise CsvRefusal(
            FINDING_CATALOG_FIELD_INVALID, "catalog mills do not match plant mill_id values"
        )
    for mill in mills:
        _check_mill(mill, groups[mill.mill_id])
    return mills


def load_catalog(
    directory: Path | None, default_directory: Path, sha256_bytes: Callable[[bytes], str]
) -> Catalog:
    """Load a catalog directory and refuse unless every pin holds."""

    catalog_dir = Path(default_directory if directory is None else directory)
    meta = _metadata(catalog_dir)
    plants, digest = _pinned_plants(catalog_dir, meta, sha256_bytes)
    if meta["factory"] not in _registry_factory_ids():
        raise CsvRefusal(
            FINDING_FACTORY_NOT_REGISTERED, f"{meta['factory']} is not a registry path_id"
        )
    mills = _catalog_mills(meta, plants)
    return Catalog(
        catalog_id=meta["catalog_id"],
        directory=catalog_dir,
        factory=meta["factory"],
        plants_sha256=digest,
        plants=plants,
        mills=mills,
        meta=meta,
    )


bind_import_twin(__name__)
