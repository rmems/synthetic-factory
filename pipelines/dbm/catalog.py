#!/usr/bin/env python3
"""Pinned dbm leftover3 plants and sequential leftover-mill identities.

The leftover3 catalog lives at ``config/dbm/leftover3.json``. Sequential mill
pins live at ``config/dbm/mills.json``. Both were AST-extracted from
``origin/legacy-mill-lane``; leftover mill scripts are never vendored.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any

from ._contract import (
    ENGINES,
    FACTORY,
    FAMILY_PREFIX,
    FINDING_CATALOG_DUPLICATE,
    FINDING_CATALOG_ENGINE,
    FINDING_CATALOG_FIELD_INVALID,
    FINDING_CATALOG_FIELD_MISSING,
    FINDING_CATALOG_NOT_AN_OBJECT,
    FINDING_CATALOG_PAIR_COUNT,
    FINDING_CATALOG_PLANT,
    FINDING_CATALOG_SCHEMA,
    GENERATOR,
    LEGACY_COMMIT,
    LEGACY_LANE,
    LEGACY_LEFTOVER3,
    LEGACY_LEFTOVER3_SHA256,
    LEGACY_PLANTS_GEN,
    LEGACY_PLANTS_GEN_SHA256,
    MILL_COUNT,
    MILL_PAIRS,
    MILL_PLANTS,
    N_PAIRS,
    PLANT_KEYS,
    QUOTA_PER_ROUND,
    SCHEMA_LEFTOVER3,
    SCHEMA_MILLS,
    START_ROUND,
    bind_import_twin,
    leftover3_path,
    load_strict_json,
    mills_path,
    refuse,
    refuse_first,
    refuse_when,
)

__all__ = [
    "Catalog",
    "Leftover3",
    "MillPin",
    "Pair",
    "catalog_check",
    "load_leftover3",
    "load_mills",
]


@dataclass(frozen=True)
class Pair:
    round_n: int
    ok: Mapping[str, str]
    bad: Mapping[str, str]


@dataclass(frozen=True)
class Leftover3:
    path: Path
    factory: str
    generator: str
    start_round: int
    n_pairs: int
    quota_per_round: int
    source: Mapping[str, Any]
    plants: tuple[Mapping[str, str], ...]
    pairs: tuple[Pair, ...]

    def pair_for_round(self, round_n: int) -> Pair:
        for pair in self.pairs:
            if pair.round_n == round_n:
                return pair
        refuse(FINDING_CATALOG_FIELD_INVALID, f"no leftover3 pair for round {round_n}")


@dataclass(frozen=True)
class MillPin:
    path: str
    sha256: str
    catalog_first: int
    constructor: str
    pair_count: int
    plant_count: int
    slugs: tuple[str, ...]


@dataclass(frozen=True)
class Catalog:
    leftover3: Leftover3
    mills: tuple[MillPin, ...]
    source: Mapping[str, Any]


def _require_object(raw: object, where: str) -> dict[str, Any]:
    refuse_when(
        not isinstance(raw, dict),
        FINDING_CATALOG_NOT_AN_OBJECT,
        f"{where} must be an object",
    )
    assert isinstance(raw, dict)
    return raw


def _require_str(raw: object, where: str) -> str:
    refuse_when(
        not isinstance(raw, str) or not raw,
        FINDING_CATALOG_FIELD_INVALID,
        f"{where} must be a non-empty string",
    )
    assert isinstance(raw, str)
    return raw


def _require_int(raw: object, where: str) -> int:
    refuse_when(
        not isinstance(raw, int) or isinstance(raw, bool),
        FINDING_CATALOG_FIELD_INVALID,
        f"{where} must be an integer",
    )
    assert isinstance(raw, int)
    return raw


def _require_field(mapping: dict[str, Any], key: str, where: str) -> Any:
    refuse_when(key not in mapping, FINDING_CATALOG_FIELD_MISSING, f"{where}.{key} is missing")
    return mapping[key]


def _unique(name: str, values: list[str]) -> None:
    refuse_when(len(set(values)) != len(values), FINDING_CATALOG_DUPLICATE, f"duplicate {name}")


def _plant(raw: object, where: str) -> Mapping[str, str]:
    plant = _require_object(raw, where)
    record: dict[str, str] = {}
    for key in PLANT_KEYS:
        record[key] = _require_str(_require_field(plant, key, where), f"{where}.{key}")
    extra = [key for key in plant if key not in PLANT_KEYS]
    refuse_when(bool(extra), FINDING_CATALOG_PLANT, f"{where} extra {extra}")
    refuse_when(
        record["engine"] not in ENGINES,
        FINDING_CATALOG_ENGINE,
        f"{where}: unknown engine {record['engine']!r}",
    )
    return MappingProxyType(record)


def _validate_leftover3(raw: object) -> dict[str, Any]:
    document = _require_object(raw, "leftover3")
    refuse_first(
        (
            (
                document.get("schema_id") != SCHEMA_LEFTOVER3,
                FINDING_CATALOG_SCHEMA,
                f"schema_id must be {SCHEMA_LEFTOVER3!r}",
            ),
            (
                document.get("family_prefix") != FAMILY_PREFIX,
                FINDING_CATALOG_SCHEMA,
                f"family_prefix must be {FAMILY_PREFIX!r}",
            ),
            (
                document.get("factory") != FACTORY,
                FINDING_CATALOG_SCHEMA,
                f"factory must be {FACTORY!r}",
            ),
            (
                document.get("generator") != GENERATOR,
                FINDING_CATALOG_SCHEMA,
                f"generator must be {GENERATOR!r}",
            ),
        )
    )
    start = _require_int(_require_field(document, "start_round", "leftover3"), "start_round")
    n_pairs = _require_int(_require_field(document, "n_pairs", "leftover3"), "n_pairs")
    quota = _require_int(
        _require_field(document, "quota_per_round", "leftover3"),
        "quota_per_round",
    )
    refuse_first(
        (
            (start != START_ROUND, FINDING_CATALOG_SCHEMA, f"start_round must be {START_ROUND}"),
            (n_pairs != N_PAIRS, FINDING_CATALOG_SCHEMA, f"n_pairs must be {N_PAIRS}"),
            (
                quota != QUOTA_PER_ROUND,
                FINDING_CATALOG_SCHEMA,
                f"quota_per_round must be {QUOTA_PER_ROUND}",
            ),
        )
    )
    plants_raw = _require_field(document, "plants", "leftover3")
    refuse_when(
        not isinstance(plants_raw, list),
        FINDING_CATALOG_FIELD_INVALID,
        "plants must be a list",
    )
    assert isinstance(plants_raw, list)
    refuse_when(
        len(plants_raw) != N_PAIRS * 2,
        FINDING_CATALOG_PAIR_COUNT,
        f"need {N_PAIRS * 2} leftover3 plants, got {len(plants_raw)}",
    )
    slugs, plants, tables, leftovers, surfaces = [], [], [], [], []
    for index, entry in enumerate(plants_raw):
        plant = _plant(entry, f"plants[{index}]")
        slugs.append(plant["slug"])
        plants.append(plant["plant"])
        tables.append(plant["table"])
        leftovers.extend((plant["leftover"], plant["leftover2"]))
        surfaces.append(plant["surface"])
    _unique("slugs", slugs)
    _unique("plants", plants)
    _unique("tables", tables)
    _unique("leftovers", leftovers)
    _unique("surfaces", surfaces)
    source = _require_object(_require_field(document, "source", "leftover3"), "source")
    refuse_first(
        (
            (
                source.get("lane") != LEGACY_LANE,
                FINDING_CATALOG_SCHEMA,
                "source.lane drifted from legacy-mill-lane",
            ),
            (
                source.get("commit") != LEGACY_COMMIT,
                FINDING_CATALOG_SCHEMA,
                "source.commit drifted from the leftover mill family commit",
            ),
            (
                source.get("mill") != LEGACY_LEFTOVER3,
                FINDING_CATALOG_SCHEMA,
                "source.mill drifted from the leftover3 mill path",
            ),
            (
                source.get("mill_sha256") != LEGACY_LEFTOVER3_SHA256,
                FINDING_CATALOG_SCHEMA,
                "source.mill_sha256 drifted from the leftover3 mill bytes",
            ),
        )
    )
    return document


def _validate_mills(raw: object) -> dict[str, Any]:
    document = _require_object(raw, "mills")
    refuse_first(
        (
            (
                document.get("schema_id") != SCHEMA_MILLS,
                FINDING_CATALOG_SCHEMA,
                f"schema_id must be {SCHEMA_MILLS!r}",
            ),
            (
                document.get("family_prefix") != FAMILY_PREFIX,
                FINDING_CATALOG_SCHEMA,
                f"family_prefix must be {FAMILY_PREFIX!r}",
            ),
            (
                document.get("factory") != FACTORY,
                FINDING_CATALOG_SCHEMA,
                f"factory must be {FACTORY!r}",
            ),
            (
                document.get("generator") != GENERATOR,
                FINDING_CATALOG_SCHEMA,
                f"generator must be {GENERATOR!r}",
            ),
        )
    )
    mills_raw = _require_field(document, "mills", "mills")
    refuse_when(
        not isinstance(mills_raw, list),
        FINDING_CATALOG_FIELD_INVALID,
        "mills must be a list",
    )
    assert isinstance(mills_raw, list)
    refuse_when(
        len(mills_raw) != MILL_COUNT,
        FINDING_CATALOG_PAIR_COUNT,
        f"need {MILL_COUNT} leftover mills, got {len(mills_raw)}",
    )
    slugs: list[str] = []
    pair_total = 0
    for index, entry in enumerate(mills_raw):
        item = _require_object(entry, f"mills[{index}]")
        path = _require_str(item.get("path"), f"mills[{index}].path")
        refuse_when(
            "dbm-mill-" not in path or not path.endswith(".py"),
            FINDING_CATALOG_FIELD_INVALID,
            f"mills[{index}].path is not a dbm leftover mill",
        )
        _require_str(item.get("sha256"), f"mills[{index}].sha256")
        _require_int(item.get("catalog_first"), f"mills[{index}].catalog_first")
        constructor = _require_str(item.get("constructor"), f"mills[{index}].constructor")
        refuse_when(
            constructor not in {"P", "Q", "R"},
            FINDING_CATALOG_FIELD_INVALID,
            f"mills[{index}].constructor must be P, Q, or R",
        )
        pair_count = _require_int(item.get("pair_count"), f"mills[{index}].pair_count")
        plant_count = _require_int(item.get("plant_count"), f"mills[{index}].plant_count")
        refuse_when(
            plant_count != pair_count * 2,
            FINDING_CATALOG_PAIR_COUNT,
            f"mills[{index}] plant_count must be 2 * pair_count",
        )
        pair_total += pair_count
        slugs_raw = _require_field(item, "slugs", f"mills[{index}]")
        refuse_when(
            not isinstance(slugs_raw, list) or len(slugs_raw) != plant_count,
            FINDING_CATALOG_PAIR_COUNT,
            f"mills[{index}].slugs must have {plant_count} entries",
        )
        assert isinstance(slugs_raw, list)
        for slug_index, slug in enumerate(slugs_raw):
            slugs.append(_require_str(slug, f"mills[{index}].slugs[{slug_index}]"))
    refuse_when(
        pair_total != MILL_PAIRS,
        FINDING_CATALOG_PAIR_COUNT,
        f"need {MILL_PAIRS} sequential pairs, got {pair_total}",
    )
    refuse_when(
        len(slugs) != MILL_PLANTS,
        FINDING_CATALOG_PAIR_COUNT,
        f"need {MILL_PLANTS} sequential plants, got {len(slugs)}",
    )
    _unique("sequential slugs", slugs)
    source = _require_object(_require_field(document, "source", "mills"), "mills.source")
    refuse_first(
        (
            (
                source.get("lane") != LEGACY_LANE,
                FINDING_CATALOG_SCHEMA,
                "mills.source.lane drifted from legacy-mill-lane",
            ),
            (
                source.get("commit") != LEGACY_COMMIT,
                FINDING_CATALOG_SCHEMA,
                "mills.source.commit drifted from the leftover mill family commit",
            ),
            (
                source.get("plants_gen") != LEGACY_PLANTS_GEN,
                FINDING_CATALOG_SCHEMA,
                "mills.source.plants_gen drifted from the r1340 plant generator",
            ),
            (
                source.get("plants_gen_sha256") != LEGACY_PLANTS_GEN_SHA256,
                FINDING_CATALOG_SCHEMA,
                "mills.source.plants_gen_sha256 drifted from the r1340 generator bytes",
            ),
        )
    )
    return document


def load_leftover3(path: Path | None = None, *, root: Path | None = None) -> Leftover3:
    catalog_path = (path or leftover3_path(root)).resolve()
    document = _validate_leftover3(load_strict_json(catalog_path.read_text(encoding="utf-8")))
    plants = tuple(
        _plant(entry, f"plants[{index}]") for index, entry in enumerate(document["plants"])
    )
    pairs = tuple(
        Pair(
            round_n=START_ROUND + index,
            ok=plants[index * 2],
            bad=plants[index * 2 + 1],
        )
        for index in range(N_PAIRS)
    )
    return Leftover3(
        path=catalog_path,
        factory=FACTORY,
        generator=GENERATOR,
        start_round=START_ROUND,
        n_pairs=N_PAIRS,
        quota_per_round=QUOTA_PER_ROUND,
        source=MappingProxyType(dict(document["source"])),
        plants=plants,
        pairs=pairs,
    )


def load_mills(path: Path | None = None, *, root: Path | None = None) -> tuple[MillPin, ...]:
    catalog_path = (path or mills_path(root)).resolve()
    document = _validate_mills(load_strict_json(catalog_path.read_text(encoding="utf-8")))
    pins = []
    for entry in document["mills"]:
        pins.append(
            MillPin(
                path=str(entry["path"]),
                sha256=str(entry["sha256"]),
                catalog_first=int(entry["catalog_first"]),
                constructor=str(entry["constructor"]),
                pair_count=int(entry["pair_count"]),
                plant_count=int(entry["plant_count"]),
                slugs=tuple(str(slug) for slug in entry["slugs"]),
            )
        )
    return tuple(pins)


def catalog_check(
    leftover3_file: Path | None = None,
    mills_file: Path | None = None,
    *,
    root: Path | None = None,
) -> Catalog:
    leftover3 = load_leftover3(leftover3_file, root=root)
    mills = load_mills(mills_file, root=root)
    leftover3_slugs = [plant["slug"] for plant in leftover3.plants]
    sequential = [slug for pin in mills for slug in pin.slugs]
    overlap = sorted(set(leftover3_slugs).intersection(sequential))
    refuse_when(
        bool(overlap),
        FINDING_CATALOG_DUPLICATE,
        f"leftover3 slugs collide with sequential leftover mills: {overlap}",
    )
    source = MappingProxyType(
        {
            "leftover3": dict(leftover3.source),
            "mills": {
                "lane": LEGACY_LANE,
                "commit": LEGACY_COMMIT,
                "plants_gen": LEGACY_PLANTS_GEN,
                "plants_gen_sha256": LEGACY_PLANTS_GEN_SHA256,
                "mill_count": len(mills),
                "pair_count": sum(pin.pair_count for pin in mills),
                "plant_count": sum(pin.plant_count for pin in mills),
            },
        }
    )
    return Catalog(leftover3=leftover3, mills=mills, source=source)


bind_import_twin(__name__)
