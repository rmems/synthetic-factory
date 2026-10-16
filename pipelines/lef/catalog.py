#!/usr/bin/env python3
"""Load the committed leftover catalog extract and bind it to the source pins."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, NamedTuple

from .catalog_extract import catalog_json_path, rows_jsonl_path
from .plants_extract import plants_jsonl_path, sha256_bytes as plants_sha256_bytes
from .sources import (
    MILL_SOURCES,
    MillSource,
    catalog_sources,
    plant_sources,
    slug_sources,
)
from .vocabulary import (
    CATALOG_SCHEMA_ID,
    FACTORY,
    GENERATOR,
    KIND_PLANTS,
    KIND_STEMS,
    KIND_TABLES,
    PLANTS_B_FILENAME,
    PLANTS_B_PAIR_COUNT,
    PLANTS_FILENAME,
    PLANTS_PAIR_COUNT,
    PRESERVE_COMMIT,
    ROWS_FILENAME,
    SHAPE_STEMS,
    SHAPE_TABLES,
    SLICE_ID,
    SLICE_MILL_ID,
    TABLE_FIELDS,
    TABLE_NAMES,
)


@dataclass(frozen=True)
class MillCatalog:
    mill_id: str
    path: str
    blob_sha: str
    sha256: str
    kind: str
    shape: str
    catalog_first: int | None
    n_rows: int
    n_table_rows: int
    n_pair_slots: int
    first_slug: str
    last_slug: str
    generator: str
    factory: str
    banned_slugs: tuple[str, ...] | None = None
    banned_snippets: tuple[str, ...] | None = None
    banned_keys: tuple[str, ...] | None = None
    tables: Mapping[str, tuple[tuple[Any, ...], ...]] | None = None
    stems: tuple[tuple[Any, ...], ...] | None = None
    froms: tuple[Any, ...] | None = None
    canons: tuple[Any, ...] | None = None
    lims: tuple[tuple[Any, ...], ...] | None = None
    nums: Mapping[str, Mapping[str, Any]] | None = None


@dataclass(frozen=True)
class PlantPair:
    index: int
    base_round: int
    mill_id: str
    plant_id: str
    source: str
    ok: Mapping[str, Any]
    bad: Mapping[str, Any]


@dataclass(frozen=True)
class PlantsCatalog:
    mill_id: str
    path: str
    archive_commit: str
    blob_sha: str
    sha256: str
    kind: str
    shape: str
    catalog_first: int
    n_pairs: int
    first_ok_slug: str
    last_ok_slug: str
    plants_file: str
    plants_sha256: str
    pairs: tuple[PlantPair, ...]


@dataclass(frozen=True)
class SlugListing:
    mill_id: str
    path: str
    blob_sha: str
    sha256: str
    kind: str
    n_rows: int
    first_slug: str
    last_slug: str


@dataclass(frozen=True)
class LefCatalog:
    schema: str
    source_ref: str
    preserve_commit: str
    factory: str
    generator: str
    slice: str
    n_catalog_rows: int
    n_table_rows: int
    n_pair_slots: int
    slugs: SlugListing
    mills: Mapping[str, MillCatalog]
    plants: PlantsCatalog | None = None
    plants_b: PlantsCatalog | None = None


def load_catalog(path=None) -> LefCatalog:
    catalog_path = path if path is not None else catalog_json_path()
    document = json.loads(catalog_path.read_text(encoding="utf-8"))
    _check_header(document, catalog_path)
    mills = {mill_id: _mill_from_row(row) for mill_id, row in document["mills"].items()}
    tables_by_mill = _load_all_slice_tables(
        rows_jsonl_path(catalog_path.parent), mills
    )
    mills = {
        mill_id: replace(mill, tables=tables_by_mill[mill_id])
        for mill_id, mill in mills.items()
    }
    slugs = _slugs_from_row(document["slugs"])
    plants, plants_b = _load_archive_b_plants(document, catalog_path.parent)
    catalog = LefCatalog(
        schema=document["schema"],
        source_ref=document["source_ref"],
        preserve_commit=document["preserve_commit"],
        factory=document["factory"],
        generator=document["generator"],
        slice=document["slice"],
        n_catalog_rows=document["n_catalog_rows"],
        n_table_rows=document["n_table_rows"],
        n_pair_slots=document["n_pair_slots"],
        slugs=slugs,
        mills=mills,
        plants=plants,
        plants_b=plants_b,
    )
    _bind_sources(catalog)
    return catalog


def _check_header(document: Mapping[str, Any], catalog_path: Path) -> None:
    """Refuse a header whose identity drifted from the vocabulary pins."""

    if document.get("schema") != CATALOG_SCHEMA_ID:
        raise ValueError(f"{catalog_path} schema is not {CATALOG_SCHEMA_ID}")
    if document.get("preserve_commit") != PRESERVE_COMMIT:
        raise ValueError(f"{catalog_path} preserve_commit drifted from vocabulary")
    if document.get("factory") != FACTORY or document.get("generator") != GENERATOR:
        raise ValueError(f"{catalog_path} factory/generator drifted from vocabulary")
    if document.get("slice") != SLICE_ID:
        raise ValueError(f"{catalog_path} slice drifted from vocabulary")
    if document.get("slice_mill") != SLICE_MILL_ID:
        raise ValueError(f"{catalog_path} slice_mill drifted from vocabulary")
    if document.get("slice_rows_file") != ROWS_FILENAME:
        raise ValueError(f"{catalog_path} slice_rows_file drifted from vocabulary")


def _load_archive_b_plants(
    document: Mapping[str, Any], package_dir: Path
) -> tuple[PlantsCatalog | None, PlantsCatalog | None]:
    """The optional ``plants`` and ``plants_b`` slices, in that order."""

    plants_row = document.get("plants")
    plants = (
        _load_plants_catalog(plants_row, package_dir)
        if plants_row is not None
        else None
    )
    plants_b_row = document.get("plants_b")
    plants_b = (
        _load_plants_catalog(
            plants_b_row,
            package_dir,
            default_filename=PLANTS_B_FILENAME,
            pair_count=PLANTS_B_PAIR_COUNT,
        )
        if plants_b_row is not None
        else None
    )
    return plants, plants_b


def _tuple_or_none(value: Any) -> tuple[Any, ...] | None:
    return tuple(value) if value else None


def _rows_or_none(value: Any) -> tuple[tuple[Any, ...], ...] | None:
    return tuple(tuple(item) for item in value) if value else None


def _mill_from_row(row: Mapping[str, Any]) -> MillCatalog:
    tables = row.get("tables")
    return MillCatalog(
        mill_id=row["mill_id"],
        path=row["path"],
        blob_sha=row["blob_sha"],
        sha256=row["sha256"],
        kind=row["kind"],
        shape=row["shape"],
        catalog_first=row.get("catalog_first"),
        n_rows=row["n_rows"],
        n_table_rows=row["n_table_rows"],
        n_pair_slots=row["n_pair_slots"],
        first_slug=row["first_slug"],
        last_slug=row["last_slug"],
        generator=row["generator"],
        factory=row["factory"],
        banned_slugs=_tuple_or_none(row.get("banned_slugs")),
        banned_snippets=_tuple_or_none(row.get("banned_snippets")),
        banned_keys=_tuple_or_none(row.get("banned_keys")),
        tables=_tables_from_row(tables) if tables else None,
        stems=_rows_or_none(row.get("stems")),
        froms=_tuple_or_none(row.get("froms")),
        canons=_tuple_or_none(row.get("canons")),
        lims=_rows_or_none(row.get("lims")),
        nums=row.get("nums"),
    )


def _tables_from_row(
    tables: Mapping[str, Any],
) -> dict[str, tuple[tuple[Any, ...], ...]]:
    return {
        name: tuple(tuple(row) for row in tables.get(name) or ())
        for name in TABLE_NAMES
    }


def _read_lf_jsonl(path: Path, label: str) -> str:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ValueError(f"cannot load {label} {path}: {exc}") from exc
    if "\r" in text or not text.endswith("\n"):
        raise ValueError(f"{path.name} must be LF-framed jsonl")
    return text


def _json_line(line: str, where: str) -> Any:
    try:
        return json.loads(line)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{where} is not JSON: {exc}") from exc


def _slice_row(line: str, where: str, expected_index: int) -> dict[str, Any]:
    """One ``rows.jsonl`` line: the next index and every table at its arity."""

    if not line:
        raise ValueError(f"{where} is empty")
    row = _json_line(line, where)
    if not isinstance(row, dict) or row.get("i") != expected_index:
        raise ValueError(f"{where} index drifted from {expected_index}")
    for name in TABLE_NAMES:
        item = row.get(name)
        expect = len(TABLE_FIELDS[name])
        if not isinstance(item, list) or len(item) != expect:
            raise ValueError(f"{where} {name} arity drifted")
    return row


def _parse_slice_rows(path: Path) -> list[dict[str, Any]]:
    text = _read_lf_jsonl(path, "leftover slice")
    rows: list[dict[str, Any]] = []
    for index, line in enumerate(text.splitlines(), start=1):
        rows.append(_slice_row(line, f"{path.name}:{index}", len(rows)))
    if not rows:
        raise ValueError(f"{path.name} must contain at least one slice row")
    return rows


def _tables_from_parsed_rows(
    rows: list[dict[str, Any]],
) -> dict[str, tuple[tuple[Any, ...], ...]]:
    buckets: dict[str, list[tuple[Any, ...]]] = {name: [] for name in TABLE_NAMES}
    for row in rows:
        for name in TABLE_NAMES:
            buckets[name].append(tuple(row[name]))
    return {name: tuple(items) for name, items in buckets.items()}


def _load_all_slice_tables(
    path: Path,
    mills: Mapping[str, MillCatalog],
) -> dict[str, dict[str, tuple[tuple[Any, ...], ...]]]:
    rows = _parse_slice_rows(path)
    expected = sum(mills[source.mill_id].n_rows for source in catalog_sources())
    if len(rows) != expected:
        raise ValueError(f"{path.name} row count {len(rows)} != {expected}")
    offset = 0
    tables_by_mill: dict[str, dict[str, tuple[tuple[Any, ...], ...]]] = {}
    for source in catalog_sources():
        mill = mills[source.mill_id]
        chunk = rows[offset : offset + mill.n_rows]
        if len(chunk) != mill.n_rows:
            raise ValueError(f"{path.name} short partition for {source.mill_id}")
        tables_by_mill[source.mill_id] = _tables_from_parsed_rows(chunk)
        offset += mill.n_rows
    if offset != len(rows):
        raise ValueError(f"{path.name} has leftover rows after mill partitions")
    return tables_by_mill


def _plant_pair_row(line: str, where: str, expected_index: int) -> PlantPair:
    """One compact ``plants.jsonl`` line: the next index with ok/bad objects."""

    if not line:
        raise ValueError(f"{where} is empty")
    if line.startswith((" ", "\t")):
        raise ValueError(f"{where} must be compact jsonl")
    row = _json_line(line, where)
    if not isinstance(row, dict):
        raise ValueError(f"{where} is not an object")
    if row.get("i") != expected_index:
        raise ValueError(f"{where} index drifted from {expected_index}")
    ok = row.get("ok")
    bad = row.get("bad")
    if not isinstance(ok, dict) or not isinstance(bad, dict):
        raise ValueError(f"{where} missing ok/bad objects")
    return PlantPair(
        index=row["i"],
        base_round=row["base_round"],
        mill_id=row["mill_id"],
        plant_id=row["plant_id"],
        source=row["source"],
        ok=ok,
        bad=bad,
    )


def _parse_plants_jsonl(path: Path, *, expected: int) -> list[PlantPair]:
    text = _read_lf_jsonl(path, "plants slice")
    rows: list[PlantPair] = []
    for index, line in enumerate(text.splitlines(), start=1):
        rows.append(_plant_pair_row(line, f"{path.name}:{index}", len(rows)))
    if len(rows) != expected:
        raise ValueError(f"{path.name} row count {len(rows)} != {expected}")
    return rows


def _load_plants_catalog(
    row: Mapping[str, Any],
    package_dir: Path,
    *,
    default_filename: str = PLANTS_FILENAME,
    pair_count: int | None = None,
) -> PlantsCatalog:
    plants_file = row.get("plants_file", default_filename)
    path = plants_jsonl_path(package_dir, filename=plants_file)
    expected = row["n_pairs"]
    if pair_count is not None and expected != pair_count:
        raise ValueError(f"{plants_file} n_pairs drifted from vocabulary")
    pairs = tuple(_parse_plants_jsonl(path, expected=expected))
    digest = plants_sha256_bytes(path.read_bytes())
    pinned = row.get("plants_sha256")
    if pinned != digest:
        raise ValueError(f"{path.name} sha256 drifted from CATALOG.json plants_sha256")
    if pairs[0].ok["slug"] != row["first_ok_slug"]:
        raise ValueError(f"{plants_file} first_ok_slug drifted from jsonl")
    if pairs[-1].ok["slug"] != row["last_ok_slug"]:
        raise ValueError(f"{plants_file} last_ok_slug drifted from jsonl")
    return PlantsCatalog(
        mill_id=row["mill_id"],
        path=row["path"],
        archive_commit=row["archive_commit"],
        blob_sha=row["blob_sha"],
        sha256=row["sha256"],
        kind=row["kind"],
        shape=row["shape"],
        catalog_first=row["catalog_first"],
        n_pairs=row["n_pairs"],
        first_ok_slug=row["first_ok_slug"],
        last_ok_slug=row["last_ok_slug"],
        plants_file=plants_file,
        plants_sha256=digest,
        pairs=pairs,
    )


def _slugs_from_row(row: Mapping[str, Any]) -> SlugListing:
    return SlugListing(
        mill_id=row["mill_id"],
        path=row["path"],
        blob_sha=row["blob_sha"],
        sha256=row["sha256"],
        kind=row["kind"],
        n_rows=row["n_rows"],
        first_slug=row["first_slug"],
        last_slug=row["last_slug"],
    )


class _PlantSlot(NamedTuple):
    """How one Archive B slice names itself in refusals, and its pinned pair count."""

    label: str
    jsonl: str
    pair_count: int


def _bind_sources(catalog: LefCatalog) -> None:
    expected = {source.mill_id: source for source in catalog_sources()}
    if set(catalog.mills) != set(expected):
        raise ValueError(
            "catalog mills drifted from sources: "
            f"extra={sorted(set(catalog.mills) - set(expected))} "
            f"missing={sorted(set(expected) - set(catalog.mills))}"
        )
    if len(MILL_SOURCES) != 7:
        raise ValueError(f"expected 7 leftover sources, found {len(MILL_SOURCES)}")
    _bind_slug_pin(catalog.slugs)
    widths = 0
    for mill_id, mill in catalog.mills.items():
        _bind_mill(mill_id, mill, expected[mill_id])
        widths += mill.n_rows
    if catalog.n_catalog_rows != widths:
        raise ValueError("catalog n_catalog_rows drifted from mill widths")
    _bind_archive_b(catalog)


def _bind_archive_b(catalog: LefCatalog) -> None:
    plant_pins = {pin.mill_id: pin for pin in plant_sources()}
    if catalog.plants is not None:
        slot = _PlantSlot("plant", PLANTS_FILENAME, PLANTS_PAIR_COUNT)
        _bind_plants(catalog.plants, plant_pins, slot)
    if catalog.plants_b is not None:
        slot = _PlantSlot("plants_b", PLANTS_B_FILENAME, PLANTS_B_PAIR_COUNT)
        _bind_plants(catalog.plants_b, plant_pins, slot)


def _bind_slug_pin(slugs: SlugListing) -> None:
    slug_pins = slug_sources()
    if len(slug_pins) != 1:
        raise ValueError("expected one leftover used-slug listing pin")
    pin = slug_pins[0]
    if (slugs.path, slugs.blob_sha, slugs.mill_id) != (pin.path, pin.blob_sha, pin.mill_id):
        raise ValueError("used-slug listing pin disagrees with sources.py")


def _bind_mill(mill_id: str, mill: MillCatalog, source: MillSource) -> None:
    if mill.path != source.path or mill.blob_sha != source.blob_sha:
        raise ValueError(f"{mill_id} pin disagrees with sources.py")
    if mill.kind != source.kind:
        raise ValueError(f"{mill_id} kind disagrees with sources.py")
    if mill.n_rows * 6 != mill.n_table_rows:
        raise ValueError(f"{mill_id} n_table_rows does not match n_rows")
    if mill.n_rows * 3 != mill.n_pair_slots:
        raise ValueError(f"{mill_id} n_pair_slots does not match n_rows")
    _bind_mill_shape(mill_id, mill)
    _bind_mill_tables(mill_id, mill)


def _bind_mill_shape(mill_id: str, mill: MillCatalog) -> None:
    if mill.shape == SHAPE_TABLES:
        if mill.kind != KIND_TABLES:
            raise ValueError(f"{mill_id} tables shape must use kind=tables")
        return
    if mill.shape != SHAPE_STEMS:
        raise ValueError(f"{mill_id} has unknown shape {mill.shape!r}")
    if mill.kind != KIND_STEMS:
        raise ValueError(f"{mill_id} stems shape must use kind=stems")
    if mill.stems is not None:
        raise ValueError(f"{mill_id} must omit stems from the header")


def _bind_mill_tables(mill_id: str, mill: MillCatalog) -> None:
    """The slice rows bound to this mill: present, n_rows wide, first/last slugs pinned."""

    if mill.tables is None:
        raise ValueError(f"{mill_id} omitted tables")
    for name in TABLE_NAMES:
        if len(mill.tables[name]) != mill.n_rows:
            raise ValueError(f"{mill_id} {name} width drifted from n_rows")
    if mill.tables["CACHE_OK"][0][0] != mill.first_slug:
        raise ValueError(f"{mill_id} first_slug drifted from slice rows")
    if mill.tables["CACHE_OK"][-1][0] != mill.last_slug:
        raise ValueError(f"{mill_id} last_slug drifted from slice rows")


def _bind_plants(
    plants: PlantsCatalog, plant_pins: Mapping[str, MillSource], slot: _PlantSlot
) -> None:
    pin = plant_pins.get(plants.mill_id)
    if pin is None:
        raise ValueError(f"Archive B {slot.label} mill_id missing from sources.py")
    if plants.path != pin.path:
        raise ValueError(f"Archive B {slot.label} pin disagrees with sources.py")
    if plants.blob_sha != pin.blob_sha:
        raise ValueError(f"Archive B {slot.label} blob_sha disagrees with sources.py")
    if plants.kind != pin.kind or plants.kind != KIND_PLANTS:
        raise ValueError(f"Archive B {slot.label} kind disagrees with sources.py")
    if plants.n_pairs != slot.pair_count:
        raise ValueError(f"Archive B {slot.label} n_pairs drifted from vocabulary")
    if plants.plants_file != slot.jsonl:
        raise ValueError(f"Archive B {slot.label} plants_file drifted from {slot.jsonl}")
    if len(plants.pairs) != plants.n_pairs:
        raise ValueError(f"{slot.jsonl} width drifted from header n_pairs")


CATALOG = load_catalog() if catalog_json_path().exists() else None
