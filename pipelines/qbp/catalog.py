#!/usr/bin/env python3
"""Pinned qbp leftover catalog: load and check.

Pair constructor args are AST-extracted from ``qbp-mill*.py`` (via the plants
path each mill names) on ``legacy-mill-lane``. Mill scripts are never vendored
or executed. Load raises and stops the run when the committed catalog drifts.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any, cast

from ._contract import (
    BAN,
    FACTORY,
    FAMILY_PREFIX,
    FINDING_CATALOG_BANNED,
    FINDING_CATALOG_DUPLICATE,
    FINDING_CATALOG_FIELD_INVALID,
    FINDING_CATALOG_FIELD_MISSING,
    FINDING_CATALOG_MILL,
    FINDING_CATALOG_NOT_AN_OBJECT,
    FINDING_CATALOG_PAIR_COUNT,
    FINDING_CATALOG_PLANT,
    FINDING_CATALOG_SCHEMA,
    FINDING_PAIRS_SHA_MISMATCH,
    GENERATOR,
    LEGACY_COMMIT,
    LEGACY_LANE,
    MILL_SOURCES,
    N_MILLS,
    N_PAIRS,
    SCHEMA_ID,
    bind_import_twin,
    default_catalog_path,
    default_pairs_path,
    load_pair_json,
    load_strict_json,
    refuse_first,
    refuse_when,
)
from .catalog_ast import ast_extract_catalog, ast_extract_mill, ast_extract_plants
from .catalog_ast import sha256_bytes, sha256_text
from .plants import BAD_ARG_NAMES, OK_ARG_NAMES, expand_bad, expand_ok

__all__ = [
    "Catalog",
    "Mill",
    "Pair",
    "ast_extract_catalog",
    "ast_extract_mill",
    "ast_extract_plants",
    "catalog_check",
    "load_catalog",
    "sha256_text",
]


@dataclass(frozen=True)
class Pair:
    mill_id: str
    round_n: int
    ok_args: Mapping[str, Any]
    bad_args: Mapping[str, Any]
    ok: Mapping[str, Any]
    bad: Mapping[str, Any]


@dataclass(frozen=True)
class Mill:
    mill_id: str
    path: str
    sha256: str
    plants: str
    plants_sha256: str
    catalog_first: int
    n_pairs: int


@dataclass(frozen=True)
class Catalog:
    path: Path
    pairs_path: Path
    family_prefix: str
    factory: str
    generator: str
    source: Mapping[str, Any]
    mills: tuple[Mill, ...]
    pairs: tuple[Pair, ...]
    pairs_sha256: str

    def pairs_for_mill(self, mill_id: str) -> tuple[Pair, ...]:
        selected = tuple(pair for pair in self.pairs if pair.mill_id == mill_id)
        refuse_when(not selected, FINDING_CATALOG_MILL, f"unknown mill {mill_id}")
        return selected


def _require_object(raw: object, where: str) -> dict[str, Any]:
    refuse_when(not isinstance(raw, dict), FINDING_CATALOG_NOT_AN_OBJECT, f"{where} must be an object")
    return cast(dict[str, Any], raw)


def _require_str(raw: object, where: str) -> str:
    refuse_when(not isinstance(raw, str) or not raw, FINDING_CATALOG_FIELD_INVALID, f"{where} must be a non-empty string")
    return cast(str, raw)


def _require_int(raw: object, where: str) -> int:
    refuse_when(not isinstance(raw, int) or isinstance(raw, bool), FINDING_CATALOG_FIELD_INVALID, f"{where} must be an integer")
    return cast(int, raw)


def _require_field(mapping: dict[str, Any], key: str, where: str) -> Any:
    refuse_when(key not in mapping, FINDING_CATALOG_FIELD_MISSING, f"{where}.{key} is missing")
    return mapping[key]


def _ctor_args(raw: object, names: tuple[str, ...], where: str) -> dict[str, Any]:
    row = _require_object(raw, where)
    out: dict[str, Any] = {name: _require_field(row, name, where) for name in names}
    if "extra_fix" in row:
        refuse_when(
            not isinstance(row["extra_fix"], dict),
            FINDING_CATALOG_FIELD_INVALID,
            f"{where}.extra_fix must be an object",
        )
        out["extra_fix"] = row["extra_fix"]
    _require_str(out["slug"], f"{where}.slug")
    return out


def _unique(name: str, values: list[str]) -> None:
    refuse_when(len(set(values)) != len(values), FINDING_CATALOG_DUPLICATE, f"duplicate {name}: {values}")


def _reject_banned(slug: str, where: str) -> None:
    refuse_when(slug in BAN, FINDING_CATALOG_BANNED, f"{where} slug is banned: {slug}")


def _validate_counts(document: Mapping[str, Any]) -> None:
    refuse_first(
        (
            (document.get("schema_id") != SCHEMA_ID, FINDING_CATALOG_SCHEMA, f"schema_id must be {SCHEMA_ID!r}"),
            (document.get("family_prefix") != FAMILY_PREFIX, FINDING_CATALOG_SCHEMA, f"family_prefix must be {FAMILY_PREFIX!r}"),
            (document.get("factory") != FACTORY, FINDING_CATALOG_SCHEMA, f"factory must be {FACTORY!r}"),
            (document.get("generator") != GENERATOR, FINDING_CATALOG_SCHEMA, f"generator must be {GENERATOR!r}"),
            (document.get("n_mills") != N_MILLS, FINDING_CATALOG_PAIR_COUNT, f"n_mills must be {N_MILLS}"),
            (document.get("n_pairs") != N_PAIRS, FINDING_CATALOG_PAIR_COUNT, f"n_pairs must be {N_PAIRS}"),
        )
    )


def _mill_pin_ok(item: dict[str, Any], pinned: tuple[Any, ...], index: int) -> None:
    mill_id, path, mill_sha, plants_path, plants_sha, catalog_first, n_pairs = pinned
    refuse_first(
        (
            (item.get("mill_id") != mill_id, FINDING_CATALOG_MILL, f"mills[{index}].mill_id must be {mill_id}"),
            (item.get("path") != path, FINDING_CATALOG_MILL, f"mills[{index}].path must be {path}"),
            (item.get("sha256") != mill_sha, FINDING_CATALOG_SCHEMA, f"mills[{index}].sha256 drifted"),
            (item.get("plants") != plants_path, FINDING_CATALOG_MILL, f"mills[{index}].plants drifted"),
            (item.get("plants_sha256") != plants_sha, FINDING_CATALOG_SCHEMA, f"mills[{index}].plants_sha256 drifted"),
            (item.get("catalog_first") != catalog_first, FINDING_CATALOG_SCHEMA, f"mills[{index}].catalog_first drifted"),
            (item.get("n_pairs") != n_pairs, FINDING_CATALOG_PAIR_COUNT, f"mills[{index}].n_pairs drifted"),
        )
    )


def _collect_pair(item: dict[str, Any], index: int, first: int, offset: int) -> tuple[str, dict[str, Any], dict[str, Any]]:
    mill_id = _require_str(_require_field(item, "mill_id", f"pairs[{index}]"), f"pairs[{index}].mill_id")
    round_n = _require_int(_require_field(item, "round", f"pairs[{index}]"), f"pairs[{index}].round")
    refuse_when(round_n != first + offset, FINDING_CATALOG_FIELD_INVALID, f"pairs[{index}].round must be {first + offset}")
    ok = _ctor_args(item.get("ok"), OK_ARG_NAMES, f"pairs[{index}].ok")
    bad = _ctor_args(item.get("bad"), BAD_ARG_NAMES, f"pairs[{index}].bad")
    return mill_id, ok, bad


@dataclass
class _Uniques:
    slugs: list[str]
    mods: list[str]
    domains: list[str]
    tickets: list[str]

    def add_pair(self, ok: dict[str, Any], bad: dict[str, Any], index: int) -> None:
        for plant, label in ((ok, "ok"), (bad, "bad")):
            slug = str(plant["slug"])
            _reject_banned(slug, f"pairs[{index}].{label}")
            self.slugs.append(slug)
            self.mods.append(str(plant["mod"]))
            self.domains.append(str(plant["domain"]))
        self.tickets.append(str(bad["ticket"]))
        plant_ok = expand_ok(ok)
        plant_bad = expand_bad(bad)
        refuse_when(plant_ok["first_old"] not in plant_ok["src_body"], FINDING_CATALOG_PLANT, f"pairs[{index}].ok first_old not in src_body")
        refuse_when(plant_bad["first_old"] not in plant_bad["src_body"], FINDING_CATALOG_PLANT, f"pairs[{index}].bad first_old not in src_body")


def _validate_document(meta: object, pair_rows: list[dict[str, Any]], digest: str) -> dict[str, Any]:
    document = _require_object(meta, "catalog")
    _validate_counts(document)
    refuse_when(
        document.get("pairs_sha256") != digest,
        FINDING_PAIRS_SHA_MISMATCH,
        f"pairs.jsonl sha256 {digest} != pinned {document.get('pairs_sha256')}",
    )
    mills_raw = _require_field(document, "mills", "catalog")
    refuse_when(
        not isinstance(mills_raw, list) or len(mills_raw) != N_MILLS,
        FINDING_CATALOG_PAIR_COUNT,
        "mills must list the six qbp-mill* extracts",
    )
    uniques = _Uniques(slugs=[], mods=[], tickets=[], domains=[])
    mill_ids: list[str] = []
    for index, (raw, pinned) in enumerate(zip(cast(list[Any], mills_raw), MILL_SOURCES, strict=True)):
        item = _require_object(raw, f"mills[{index}]")
        _mill_pin_ok(item, pinned, index)
        mill_ids.append(str(pinned[0]))
    refuse_when(len(pair_rows) != N_PAIRS, FINDING_CATALOG_PAIR_COUNT, f"need {N_PAIRS} pair rows, got {len(pair_rows)}")
    expected_windows = {row[0]: (row[5], row[6]) for row in MILL_SOURCES}
    seen: dict[str, int] = {mill_id: 0 for mill_id in mill_ids}
    for index, entry in enumerate(pair_rows):
        item = _require_object(entry, f"pairs[{index}]")
        mill_id = _require_str(_require_field(item, "mill_id", f"pairs[{index}]"), f"pairs[{index}].mill_id")
        refuse_when(mill_id not in expected_windows, FINDING_CATALOG_MILL, f"pairs[{index}] unknown mill {mill_id}")
        first, _window = expected_windows[mill_id]
        offset = seen[mill_id]
        mill_id, ok, bad = _collect_pair(item, index, first, offset)
        seen[mill_id] = offset + 1
        uniques.add_pair(ok, bad, index)
    refuse_when(
        seen != {mill_id: expected_windows[mill_id][1] for mill_id in mill_ids},
        FINDING_CATALOG_PAIR_COUNT,
        f"pair counts drifted: {seen}",
    )
    _unique("slugs", uniques.slugs)
    _unique("mods", uniques.mods)
    _unique("tickets", uniques.tickets)
    _unique("domains", uniques.domains)
    source = _require_object(_require_field(document, "source", "catalog"), "source")
    refuse_when(source.get("lane") != LEGACY_LANE, FINDING_CATALOG_SCHEMA, "source.lane drifted")
    refuse_when(source.get("commit") != LEGACY_COMMIT, FINDING_CATALOG_SCHEMA, "source.commit drifted")
    return document


def _read_pair_rows(path: Path) -> tuple[list[dict[str, Any]], str]:
    payload = path.read_bytes()
    rows = []
    for lineno, line in enumerate(payload.decode("utf-8").splitlines(), start=1):
        if not line:
            continue
        row = load_pair_json(line)
        refuse_when(not isinstance(row, dict), FINDING_CATALOG_NOT_AN_OBJECT, f"{path}:{lineno} is not an object")
        rows.append(row)
    return rows, sha256_bytes(payload)


def load_catalog(path: Path | None = None, *, root: Path | None = None) -> Catalog:
    catalog_path = (path or default_catalog_path(root)).resolve()
    pairs_path = default_pairs_path(catalog_path)
    refuse_when(not catalog_path.is_file(), FINDING_CATALOG_FIELD_MISSING, f"missing {catalog_path}")
    refuse_when(not pairs_path.is_file(), FINDING_CATALOG_FIELD_MISSING, f"missing {pairs_path}")
    pair_rows, digest = _read_pair_rows(pairs_path)
    document = _validate_document(load_strict_json(catalog_path.read_text(encoding="utf-8")), pair_rows, digest)
    mills = tuple(
        Mill(
            mill_id=str(item["mill_id"]),
            path=str(item["path"]),
            sha256=str(item["sha256"]),
            plants=str(item["plants"]),
            plants_sha256=str(item["plants_sha256"]),
            catalog_first=int(item["catalog_first"]),
            n_pairs=int(item["n_pairs"]),
        )
        for item in document["mills"]
    )
    pairs = tuple(
        Pair(
            mill_id=str(entry["mill_id"]),
            round_n=int(entry["round"]),
            ok_args=MappingProxyType(_ctor_args(entry["ok"], OK_ARG_NAMES, f"pairs[{index}].ok")),
            bad_args=MappingProxyType(_ctor_args(entry["bad"], BAD_ARG_NAMES, f"pairs[{index}].bad")),
            ok=MappingProxyType(expand_ok(entry["ok"])),
            bad=MappingProxyType(expand_bad(entry["bad"])),
        )
        for index, entry in enumerate(pair_rows)
    )
    return Catalog(
        path=catalog_path,
        pairs_path=pairs_path,
        family_prefix=FAMILY_PREFIX,
        factory=FACTORY,
        generator=GENERATOR,
        source=MappingProxyType(dict(document["source"])),
        mills=mills,
        pairs=pairs,
        pairs_sha256=digest,
    )


def catalog_check(path: Path | None = None, *, root: Path | None = None) -> Catalog:
    """Load the committed catalog and re-assert the leftover-mill contract."""

    catalog = load_catalog(path, root=root)
    refuse_when(len(catalog.mills) != N_MILLS, FINDING_CATALOG_PAIR_COUNT, "mill count drifted")
    refuse_when(len(catalog.pairs) != N_PAIRS, FINDING_CATALOG_PAIR_COUNT, "pair count drifted")
    return catalog


bind_import_twin(__name__)
