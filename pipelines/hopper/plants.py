#!/usr/bin/env python3
"""Pinned hopper plant catalog: load, schema, uniqueness, START/PAIRS-by-factory.

``config/hopper/plants.jsonl`` holds 152 rows (76 success/handoff pairs) across
waves g46, g46b, g46c and g46d. Load raises (registry-style) rather than
excluding per row. ``_p`` is the plant constructor later families already call.
"""

from __future__ import annotations

import hashlib
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any

from ._contract import (
    FINDING_CATALOG_FIELD_INVALID,
    FINDING_CATALOG_FIELD_MISSING,
    FINDING_CATALOG_FILE_MISSING,
    FINDING_PLANT_DUPLICATE,
    FINDING_PLANT_FIELD_INVALID,
    FINDING_PLANT_FIELD_MISSING,
    FINDING_PLANTS_SHA_MISMATCH,
    FINDING_UNKNOWN_FACTORY,
    FINDING_UNKNOWN_WAVE,
    bind_import_twin,
    load_strict_json,
    refuse,
    refuse_first,
    refuse_when,
)

WAVES = ("g46", "g46b", "g46c", "g46d")
ROLES = ("success", "handoff")
CATALOG_FILENAME = "CATALOG.json"
PLANTS_FILENAME = "plants.jsonl"
DEFAULT_CATALOG_DIR = Path(__file__).resolve().parents[2] / "config" / "hopper"

CATALOG_META_KEYS = (
    "wave", "factory", "role", "pair", "prefix", "catalog_round", "published_round",
)
SHARED_PLANT_KEYS = (
    "slug", "goal", "plan", "mod", "test_fn", "src_body", "test_body", "grep_pat",
    "grep_hit", "fail_msg", "first_old", "first_new", "first_obs", "still_msg",
    "reread_obs", "plan_change", "fix_new", "fix_obs", "docs_url", "docs_ok",
    "docs_url2", "docs_ok2", "outcome", "domain", "stack", "seed", "residual",
    "coverage",
)
HANDOFF_PLANT_KEYS = SHARED_PLANT_KEYS + ("ticket", "ticket_why")
REQUIRED_CATALOG_FIELDS = (
    "catalog_id", "family", "schema", "generator", "plants_filename",
    "plants_sha256", "plants", "pairs", "waves", "prefixes", "cycle", "starts",
)

__all__ = [
    "CYCLE", "PAIRS", "PREFIX", "START", "Catalog", "WAVES", "_p", "all_pairs",
    "load_catalog", "pairs_by_factory", "start_by_factory",
]


def _p(**kwargs: Any) -> dict[str, Any]:
    """Identity plant constructor kept for qbp/wsr/ewr/cei/kcl catalogs."""
    return dict(kwargs)


def _as_int(value: Any, label: str) -> int:
    refuse_when(
        not isinstance(value, int) or isinstance(value, bool),
        FINDING_PLANT_FIELD_INVALID,
        f"{label} must be an int, got {type(value).__name__}",
    )
    return value


def _as_str(value: Any, label: str) -> str:
    refuse_when(
        not isinstance(value, str) or not value,
        FINDING_PLANT_FIELD_INVALID,
        f"{label} must be a non-empty string",
    )
    return value


def _require_keys(row: Mapping[str, Any], keys: tuple[str, ...], label: str) -> None:
    missing = [key for key in keys if key not in row]
    refuse_when(bool(missing), FINDING_PLANT_FIELD_MISSING, f"{label} missing {missing}")


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


@dataclass(frozen=True)
class PlantPair:
    wave: str
    factory: str
    prefix: str
    index: int
    catalog_round: int
    published_round: int
    ok: Mapping[str, Any]
    bad: Mapping[str, Any]


@dataclass(frozen=True)
class Catalog:
    directory: Path
    meta: Mapping[str, Any]
    plants_sha256: str
    pairs: tuple[PlantPair, ...]
    prefixes: Mapping[str, str]
    cycle: tuple[str, ...]
    starts_by_wave: Mapping[str, Mapping[str, int]]
    pairs_by_wave: Mapping[str, Mapping[str, tuple[PlantPair, ...]]]

    def pair_for_slug(self, slug: str) -> PlantPair:
        for pair in self.pairs:
            if pair.ok["slug"] == slug or pair.bad["slug"] == slug:
                return pair
        refuse("UNKNOWN_SLUG", f"no hopper plant with slug {slug!r}")


def _load_meta(directory: Path) -> tuple[dict[str, Any], bytes, str]:
    catalog_path = directory / CATALOG_FILENAME
    plants_path = directory / PLANTS_FILENAME
    refuse_first((
        (not catalog_path.is_file(), FINDING_CATALOG_FILE_MISSING, f"missing {catalog_path}"),
        (not plants_path.is_file(), FINDING_CATALOG_FILE_MISSING, f"missing {plants_path}"),
    ))
    meta = load_strict_json(catalog_path.read_text(encoding="utf-8"))
    refuse_when(not isinstance(meta, dict), FINDING_CATALOG_FIELD_INVALID, "CATALOG.json must be an object")
    missing = [key for key in REQUIRED_CATALOG_FIELDS if key not in meta]
    refuse_when(bool(missing), FINDING_CATALOG_FIELD_MISSING, f"CATALOG.json missing {missing}")
    refuse_when(
        meta.get("family") != "hopper" or meta.get("schema") != "hopper-plants-v1",
        FINDING_CATALOG_FIELD_INVALID,
        f"unexpected catalog identity {meta.get('family')!r}/{meta.get('schema')!r}",
    )
    plants_bytes = plants_path.read_bytes()
    digest = _sha256_bytes(plants_bytes)
    pinned = meta.get("plants_sha256")
    refuse_when(
        pinned != digest,
        FINDING_PLANTS_SHA_MISMATCH,
        f"plants.jsonl sha256 {digest} != pinned {pinned}",
    )
    return meta, plants_bytes, digest


def _row_from_line(line: str, lineno: int) -> dict[str, Any]:
    row = load_strict_json(line)
    refuse_when(not isinstance(row, dict), FINDING_PLANT_FIELD_INVALID, f"line {lineno} is not an object")
    _require_keys(row, CATALOG_META_KEYS, f"line {lineno}")
    wave = _as_str(row["wave"], f"line {lineno} wave")
    role = _as_str(row["role"], f"line {lineno} role")
    refuse_when(wave not in WAVES, FINDING_PLANT_FIELD_INVALID, f"line {lineno} unknown wave {wave!r}")
    refuse_when(role not in ROLES, FINDING_PLANT_FIELD_INVALID, f"line {lineno} unknown role {role!r}")
    keys = SHARED_PLANT_KEYS if role == "success" else HANDOFF_PLANT_KEYS
    _require_keys(row, keys, f"line {lineno} {row.get('slug')}")
    _as_str(row["slug"], f"line {lineno} slug")
    _as_int(row["pair"], f"line {lineno} pair")
    _as_int(row["catalog_round"], f"line {lineno} catalog_round")
    _as_int(row["published_round"], f"line {lineno} published_round")
    _as_int(row["coverage"], f"line {lineno} coverage")
    refuse_when(
        row["first_old"] not in row["src_body"],
        FINDING_PLANT_FIELD_INVALID,
        f"{row['slug']} first_old not in src_body",
    )
    return row


def _grouped_pairs(rows: list[dict[str, Any]]) -> list[PlantPair]:
    grouped: dict[tuple[str, str, int], dict[str, dict[str, Any]]] = {}
    for row in rows:
        key = (row["wave"], row["factory"], row["pair"])
        bucket = grouped.setdefault(key, {})
        refuse_when(row["role"] in bucket, FINDING_PLANT_DUPLICATE, f"duplicate {row['role']} at {key}")
        bucket[row["role"]] = row
    pairs: list[PlantPair] = []
    for (wave, factory, index), bucket in grouped.items():
        refuse_when(
            set(bucket) != {"success", "handoff"},
            FINDING_PLANT_FIELD_MISSING,
            f"{wave} {factory} pair {index} roles={sorted(bucket)}",
        )
        ok, bad = bucket["success"], bucket["handoff"]
        refuse_when(
            ok["prefix"] != bad["prefix"] or ok["published_round"] != bad["published_round"],
            FINDING_PLANT_FIELD_INVALID,
            f"{wave} {factory} pair {index} prefix/round mismatch",
        )
        pairs.append(PlantPair(
            wave=wave,
            factory=factory,
            prefix=ok["prefix"],
            index=index,
            catalog_round=ok["catalog_round"],
            published_round=ok["published_round"],
            ok=MappingProxyType(dict(ok)),
            bad=MappingProxyType(dict(bad)),
        ))
    pairs.sort(key=lambda item: (WAVES.index(item.wave), item.factory, item.index))
    return pairs


def _uniqueness(pairs: list[PlantPair]) -> None:
    slugs, mods, domains, tickets = [], [], [], []
    for pair in pairs:
        for plant in (pair.ok, pair.bad):
            slugs.append(plant["slug"])
            mods.append(plant["mod"])
            domains.append(plant["domain"])
        tickets.append(pair.bad["ticket"])
    for label, values in (
        ("slug", slugs), ("mod", mods), ("domain", domains), ("ticket", tickets),
    ):
        refuse_when(
            len(set(values)) != len(values),
            FINDING_PLANT_DUPLICATE,
            f"duplicate {label}s in hopper catalog",
        )


def _freeze_starts(raw: Any, prefixes: Mapping[str, str]) -> Mapping[str, Mapping[str, int]]:
    refuse_when(not isinstance(raw, dict), FINDING_CATALOG_FIELD_INVALID, "starts must be an object")
    frozen: dict[str, Mapping[str, int]] = {}
    for wave, table in raw.items():
        refuse_when(wave not in WAVES, FINDING_CATALOG_FIELD_INVALID, f"starts has unknown wave {wave!r}")
        refuse_when(not isinstance(table, dict), FINDING_CATALOG_FIELD_INVALID, f"starts.{wave} not an object")
        built: dict[str, int] = {}
        for factory, value in table.items():
            refuse_when(factory not in prefixes, FINDING_UNKNOWN_FACTORY, f"starts.{wave} factory {factory}")
            built[factory] = _as_int(value, f"starts.{wave}.{factory}")
        frozen[wave] = MappingProxyType(built)
    missing = [wave for wave in WAVES if wave not in frozen]
    refuse_when(bool(missing), FINDING_CATALOG_FIELD_MISSING, f"starts missing waves {missing}")
    return MappingProxyType(frozen)


def load_catalog(directory: Path | None = None) -> Catalog:
    catalog_dir = Path(directory) if directory is not None else DEFAULT_CATALOG_DIR
    meta, plants_bytes, digest = _load_meta(catalog_dir)
    rows = [
        _row_from_line(line, lineno)
        for lineno, line in enumerate(plants_bytes.decode("utf-8").splitlines(), start=1)
        if line
    ]
    refuse_when(
        len(rows) != meta["plants"],
        FINDING_CATALOG_FIELD_INVALID,
        f"plants.jsonl has {len(rows)} rows; CATALOG.json says {meta['plants']}",
    )
    prefixes = meta["prefixes"]
    refuse_when(not isinstance(prefixes, dict), FINDING_CATALOG_FIELD_INVALID, "prefixes must be an object")
    prefix_map = MappingProxyType({
        _as_str(factory, "prefix factory"): _as_str(prefix, f"prefix {factory}")
        for factory, prefix in prefixes.items()
    })
    cycle_raw = meta["cycle"]
    refuse_when(not isinstance(cycle_raw, list), FINDING_CATALOG_FIELD_INVALID, "cycle must be a list")
    cycle = tuple(_as_str(item, "cycle entry") for item in cycle_raw)
    pairs = _grouped_pairs(rows)
    refuse_when(
        len(pairs) != meta["pairs"],
        FINDING_CATALOG_FIELD_INVALID,
        f"grouped {len(pairs)} pairs; CATALOG.json says {meta['pairs']}",
    )
    _uniqueness(pairs)
    by_wave: dict[str, dict[str, list[PlantPair]]] = {wave: {} for wave in WAVES}
    for pair in pairs:
        refuse_when(
            prefix_map.get(pair.factory) != pair.prefix,
            FINDING_PLANT_FIELD_INVALID,
            f"{pair.factory} prefix {pair.prefix!r} != catalog {prefix_map.get(pair.factory)!r}",
        )
        by_wave[pair.wave].setdefault(pair.factory, []).append(pair)
    frozen_wave_pairs = MappingProxyType({
        wave: MappingProxyType({
            factory: tuple(items) for factory, items in factories.items()
        })
        for wave, factories in by_wave.items()
    })
    return Catalog(
        directory=catalog_dir,
        meta=MappingProxyType(dict(meta)),
        plants_sha256=digest,
        pairs=tuple(pairs),
        prefixes=prefix_map,
        cycle=cycle,
        starts_by_wave=_freeze_starts(meta["starts"], prefix_map),
        pairs_by_wave=frozen_wave_pairs,
    )


_CATALOG = load_catalog()


def start_by_factory(wave: str | None = None) -> Mapping[str, int]:
    """Per-factory START table. ``wave=None`` uses each factory's earliest catalog round."""
    if wave is None:
        return START
    refuse_when(wave not in WAVES, FINDING_UNKNOWN_WAVE, f"unknown hopper wave {wave!r}")
    return _CATALOG.starts_by_wave[wave]


def pairs_by_factory(wave: str | None = None) -> Mapping[str, tuple[tuple[Mapping[str, Any], Mapping[str, Any]], ...]]:
    """Per-factory PAIRS table. ``wave=None`` concatenates g46 → g46d."""
    if wave is None:
        return PAIRS
    refuse_when(wave not in WAVES, FINDING_UNKNOWN_WAVE, f"unknown hopper wave {wave!r}")
    return MappingProxyType({
        factory: tuple((item.ok, item.bad) for item in items)
        for factory, items in _CATALOG.pairs_by_wave[wave].items()
    })


def all_pairs(wave: str | None = None):
    """``(factory, ok, bad)`` rows, matching hopper_plants_g46.all_pairs."""
    table = pairs_by_factory(wave)
    for factory in CYCLE:
        for ok, bad in table.get(factory, ()):
            yield factory, ok, bad


def _merged_pairs() -> Mapping[str, tuple[tuple[Mapping[str, Any], Mapping[str, Any]], ...]]:
    table: dict[str, list[tuple[Mapping[str, Any], Mapping[str, Any]]]] = {name: [] for name in _CATALOG.cycle}
    for pair in _CATALOG.pairs:
        table.setdefault(pair.factory, []).append((pair.ok, pair.bad))
    return MappingProxyType({factory: tuple(items) for factory, items in table.items() if items})


def _merged_start() -> Mapping[str, int]:
    earliest: dict[str, int] = {}
    for pair in _CATALOG.pairs:
        current = earliest.get(pair.factory)
        if current is None or pair.catalog_round < current:
            earliest[pair.factory] = pair.catalog_round
    return MappingProxyType(earliest)


CYCLE = _CATALOG.cycle
PREFIX = _CATALOG.prefixes
PAIRS = _merged_pairs()
START = _merged_start()

bind_import_twin(__name__)
