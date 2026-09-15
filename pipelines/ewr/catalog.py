#!/usr/bin/env python3
"""Pinned ewr leftover-event catalog: AST extract, load, and check.

The catalog lives at ``config/ewr/CATALOG.json`` with pair bodies in
``config/ewr/pairs.jsonl``. Legacy mills on ``legacy-mill-lane`` are never
vendored. Load raises and stops the run when the file drifts from the
reviewed contract.
"""

from __future__ import annotations

import hashlib
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any, cast

from . import catalog_ast as _ast
from ._contract import (
    BANNED_SLUG_TOKENS,
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
    LEGACY_MAPPING_MILL,
    LEGACY_MAPPING_MILL_SHA256,
    LEGACY_MILL,
    LEGACY_MILL_SHA256,
    LEGACY_PLANTS,
    LEGACY_PLANTS_SHA256,
    MAPPING_FIELDS,
    MILL_SOURCES,
    N_MAPPING_PAIRS,
    N_MILLS,
    N_PAIRS,
    N_PLANT_PAIRS,
    PAIRS_SHA256,
    PLANTS_MILL_ID,
    QUOTA_PER_ROUND,
    SCHEMA_ID,
    START_ROUND,
    MillPin,
    bind_import_twin,
    default_catalog_path,
    default_pairs_path,
    load_pair_json,
    load_strict_json,
    refuse,
    refuse_first,
    refuse_when,
)

SHARED_PLANT_FIELDS = (
    "slug",
    "goal",
    "plan",
    "mod",
    "test_fn",
    "src_body",
    "test_body",
    "grep_pat",
    "grep_hit",
    "fail_msg",
    "first_old",
    "first_new",
    "first_obs",
    "still_msg",
    "reread_obs",
    "plan_change",
    "fix_obs",
    "docs_url",
    "docs_ok",
    "docs_url2",
    "docs_ok2",
    "outcome",
    "domain",
    "stack",
    "seed",
    "residual",
)
OK_REQUIRED = SHARED_PLANT_FIELDS + ("fix_new", "coverage")
BAD_REQUIRED = SHARED_PLANT_FIELDS + ("ticket", "ticket_why", "coverage")

__all__ = [
    "Catalog",
    "MappingPair",
    "Pair",
    "ast_extract_catalog_rows",
    "ast_extract_mapping_pairs",
    "ast_extract_mill_constants",
    "ast_extract_plant_pairs",
    "catalog_check",
    "load_catalog",
    "sha256_text",
]

ast_extract_plant_pairs = _ast.ast_extract_plant_pairs
ast_extract_mill_constants = _ast.ast_extract_mill_constants
ast_extract_mapping_pairs = _ast.ast_extract_mapping_pairs
ast_extract_catalog_rows = _ast.ast_extract_catalog_rows
sha256_text = _ast.sha256_text


@dataclass(frozen=True)
class Pair:
    mill_id: str
    round_n: int
    ok: Mapping[str, Any]
    bad: Mapping[str, Any]


@dataclass(frozen=True)
class MappingPair:
    mill_id: str
    round_n: int
    mapping: Mapping[str, Any]


@dataclass(frozen=True)
class Mill:
    mill_id: str
    source_format: str
    path: str
    sha256: str
    plants: str | None
    plants_sha256: str | None
    catalog_first: int
    n_pairs: int


@dataclass(frozen=True)
class Catalog:
    path: Path
    pairs_path: Path
    family_prefix: str
    factory: str
    generator: str
    quota_per_round: int
    source: Mapping[str, Any]
    mills: tuple[Mill, ...]
    pairs: tuple[Pair, ...]
    mapping_pairs: tuple[MappingPair, ...]
    pairs_sha256: str

    @property
    def start_round(self) -> int:
        return START_ROUND

    @property
    def n_rounds(self) -> int:
        return N_PLANT_PAIRS

    def pair_for_round(self, round_n: int) -> Pair:
        for pair in self.pairs:
            if pair.round_n == round_n:
                return pair
        refuse(FINDING_CATALOG_FIELD_INVALID, f"no plant pair for round {round_n}")


def _require_object(raw: object, where: str) -> dict[str, Any]:
    refuse_when(
        not isinstance(raw, dict),
        FINDING_CATALOG_NOT_AN_OBJECT,
        f"{where} must be an object",
    )
    return cast(dict[str, Any], raw)


def _require_str(raw: object, where: str) -> str:
    refuse_when(
        not isinstance(raw, str) or not raw,
        FINDING_CATALOG_FIELD_INVALID,
        f"{where} must be a non-empty string",
    )
    return cast(str, raw)


def _require_int(raw: object, where: str) -> int:
    refuse_when(
        not isinstance(raw, int) or isinstance(raw, bool),
        FINDING_CATALOG_FIELD_INVALID,
        f"{where} must be an integer",
    )
    return cast(int, raw)


def _require_field(mapping: dict[str, Any], key: str, where: str) -> Any:
    refuse_when(key not in mapping, FINDING_CATALOG_FIELD_MISSING, f"{where}.{key} is missing")
    return mapping[key]


def _plant(raw: object, required: tuple[str, ...], where: str) -> Mapping[str, Any]:
    plant = _require_object(raw, where)
    for key in required:
        _require_field(plant, key, where)
        if key == "coverage":
            coverage = _require_int(plant[key], f"{where}.coverage")
            refuse_when(
                not 0 <= coverage <= 100,
                FINDING_CATALOG_FIELD_INVALID,
                f"{where}.coverage must be in 0..100",
            )
        else:
            _require_str(plant[key], f"{where}.{key}")
    first_old = plant["first_old"]
    src_body = plant["src_body"]
    refuse_when(
        not isinstance(first_old, str)
        or not isinstance(src_body, str)
        or first_old not in src_body,
        FINDING_CATALOG_PLANT,
        f"{where}: first_old is not in src_body",
    )
    return MappingProxyType(dict(plant))


def _mapping(raw: object, where: str) -> Mapping[str, Any]:
    row = _require_object(raw, where)
    for key in MAPPING_FIELDS:
        _require_str(_require_field(row, key, where), f"{where}.{key}")
    extra = set(row) - set(MAPPING_FIELDS)
    refuse_when(bool(extra), FINDING_CATALOG_PLANT, f"{where} unexpected keys {sorted(extra)}")
    return MappingProxyType(dict(row))


def _unique(name: str, values: list[str]) -> None:
    refuse_when(
        len(set(values)) != len(values),
        FINDING_CATALOG_DUPLICATE,
        f"duplicate {name}: {values}",
    )


def _reject_banned(slug: str, where: str) -> None:
    lowered = slug.lower()
    for token in BANNED_SLUG_TOKENS:
        refuse_when(
            token in lowered,
            FINDING_CATALOG_BANNED,
            f"{where} slug carries banned {token!r}",
        )


def _mill_pin_ok(item: dict[str, Any], pinned: MillPin, index: int) -> None:
    refuse_first(
        (
            (
                item.get("mill_id") != pinned.mill_id,
                FINDING_CATALOG_MILL,
                f"mills[{index}].mill_id must be {pinned.mill_id}",
            ),
            (
                item.get("source_format") != pinned.source_format,
                FINDING_CATALOG_MILL,
                f"mills[{index}].source_format must be {pinned.source_format}",
            ),
            (
                item.get("path") != pinned.mill_path,
                FINDING_CATALOG_MILL,
                f"mills[{index}].path must be {pinned.mill_path}",
            ),
            (
                item.get("sha256") != pinned.mill_sha256,
                FINDING_CATALOG_SCHEMA,
                f"mills[{index}].sha256 drifted",
            ),
            (
                item.get("catalog_first") != pinned.catalog_first,
                FINDING_CATALOG_SCHEMA,
                f"mills[{index}].catalog_first drifted",
            ),
            (
                item.get("n_pairs") != pinned.n_pairs,
                FINDING_CATALOG_PAIR_COUNT,
                f"mills[{index}].n_pairs drifted",
            ),
        )
    )
    if pinned.plants_path is None:
        refuse_when(
            item.get("plants") is not None or item.get("plants_sha256") is not None,
            FINDING_CATALOG_MILL,
            f"mills[{index}] must not carry plants pins",
        )
        return
    refuse_when(
        item.get("plants") != pinned.plants_path,
        FINDING_CATALOG_MILL,
        f"mills[{index}].plants drifted",
    )
    refuse_when(
        item.get("plants_sha256") != pinned.plants_sha256,
        FINDING_CATALOG_SCHEMA,
        f"mills[{index}].plants_sha256 drifted",
    )


def _validate_header(document: dict[str, Any], digest: str) -> None:
    refuse_first(
        (
            (document.get("schema_id") != SCHEMA_ID, FINDING_CATALOG_SCHEMA, f"schema_id must be {SCHEMA_ID!r}"),
            (document.get("family_prefix") != FAMILY_PREFIX, FINDING_CATALOG_SCHEMA, "family_prefix drifted"),
            (document.get("factory") != FACTORY, FINDING_CATALOG_SCHEMA, "factory drifted"),
            (document.get("generator") != GENERATOR, FINDING_CATALOG_SCHEMA, "generator drifted"),
            (document.get("n_mills") != N_MILLS, FINDING_CATALOG_PAIR_COUNT, f"n_mills must be {N_MILLS}"),
            (document.get("n_pairs") != N_PAIRS, FINDING_CATALOG_PAIR_COUNT, f"n_pairs must be {N_PAIRS}"),
            (
                document.get("n_plant_pairs") != N_PLANT_PAIRS,
                FINDING_CATALOG_PAIR_COUNT,
                f"n_plant_pairs must be {N_PLANT_PAIRS}",
            ),
            (
                document.get("n_mapping_pairs") != N_MAPPING_PAIRS,
                FINDING_CATALOG_PAIR_COUNT,
                f"n_mapping_pairs must be {N_MAPPING_PAIRS}",
            ),
            (
                document.get("quota_per_round") != QUOTA_PER_ROUND,
                FINDING_CATALOG_SCHEMA,
                f"quota_per_round must be {QUOTA_PER_ROUND}",
            ),
            (
                document.get("pairs_sha256") != digest,
                FINDING_PAIRS_SHA_MISMATCH,
                f"pairs.jsonl sha256 {digest} != pinned {document.get('pairs_sha256')}",
            ),
            (
                document.get("pairs_sha256") != PAIRS_SHA256,
                FINDING_CATALOG_SCHEMA,
                "pairs_sha256 drifted from the committed catalog",
            ),
        )
    )
    source = _require_object(_require_field(document, "source", "catalog"), "source")
    refuse_when(source.get("lane") != LEGACY_LANE, FINDING_CATALOG_SCHEMA, "source.lane drifted")
    refuse_when(source.get("commit") != LEGACY_COMMIT, FINDING_CATALOG_SCHEMA, "source.commit drifted")
    mills_raw = _require_field(document, "mills", "catalog")
    refuse_when(
        not isinstance(mills_raw, list) or len(mills_raw) != N_MILLS,
        FINDING_CATALOG_PAIR_COUNT,
        "mills must list both ewr extracts",
    )
    for index, (raw, pinned) in enumerate(zip(mills_raw, MILL_SOURCES, strict=True)):
        item = _require_object(raw, f"mills[{index}]")
        _mill_pin_ok(item, pinned, index)


def _read_pair_rows(path: Path) -> tuple[list[dict[str, Any]], str]:
    payload = path.read_bytes()
    rows: list[dict[str, Any]] = []
    for lineno, line in enumerate(payload.decode("utf-8").splitlines(), start=1):
        if not line:
            continue
        refuse_when(line[0] in " \t", FINDING_CATALOG_SCHEMA, f"{path}:{lineno} must not lead with whitespace")
        row = load_pair_json(line)
        refuse_when(
            not isinstance(row, dict),
            FINDING_CATALOG_NOT_AN_OBJECT,
            f"{path}:{lineno} is not an object",
        )
        rows.append(row)
    return rows, hashlib.sha256(payload).hexdigest()


def _validate_rows(pair_rows: list[dict[str, Any]]) -> tuple[tuple[Pair, ...], tuple[MappingPair, ...]]:
    refuse_when(len(pair_rows) != N_PAIRS, FINDING_CATALOG_PAIR_COUNT, f"need {N_PAIRS} rows, got {len(pair_rows)}")
    windows = {pin.mill_id: (pin.catalog_first, pin.n_pairs, pin.source_format) for pin in MILL_SOURCES}
    seen = {mill_id: 0 for mill_id in windows}
    slugs: list[str] = []
    mods: list[str] = []
    tickets: list[str] = []
    domains: list[str] = []
    plant_pairs: list[Pair] = []
    mapping_pairs: list[MappingPair] = []
    for index, entry in enumerate(pair_rows):
        item = _require_object(entry, f"pairs[{index}]")
        mill_id = _require_str(_require_field(item, "mill_id", f"pairs[{index}]"), f"pairs[{index}].mill_id")
        refuse_when(mill_id not in windows, FINDING_CATALOG_MILL, f"pairs[{index}] unknown mill {mill_id}")
        first, _count, source_format = windows[mill_id]
        offset = seen[mill_id]
        round_n = _require_int(_require_field(item, "round", f"pairs[{index}]"), f"pairs[{index}].round")
        refuse_when(
            round_n != first + offset,
            FINDING_CATALOG_FIELD_INVALID,
            f"pairs[{index}].round must be {first + offset}",
        )
        seen[mill_id] = offset + 1
        if source_format == "plants-v1":
            ok = _plant(item.get("ok"), OK_REQUIRED, f"pairs[{index}].ok")
            bad = _plant(item.get("bad"), BAD_REQUIRED, f"pairs[{index}].bad")
            for plant, label in ((ok, "ok"), (bad, "bad")):
                slug = str(plant["slug"])
                _reject_banned(slug, f"pairs[{index}].{label}")
                slugs.append(slug)
                mods.append(str(plant["mod"]))
                domains.append(str(plant["domain"]))
            tickets.append(str(bad["ticket"]))
            plant_pairs.append(Pair(mill_id=mill_id, round_n=round_n, ok=ok, bad=bad))
            continue
        if source_format == "mapping-v1":
            mapping = _mapping(_require_field(item, "mapping", f"pairs[{index}]"), f"pairs[{index}].mapping")
            slug = str(mapping["slug"])
            fail_slug = str(mapping["fail"])
            _reject_banned(slug, f"pairs[{index}].mapping.slug")
            _reject_banned(fail_slug, f"pairs[{index}].mapping.fail")
            slugs.extend((slug, fail_slug))
            mods.extend((str(mapping["mod"]), str(mapping["drop"])))
            domains.append(str(mapping["domain"]))
            tickets.append(str(mapping["ticket"]))
            mapping_pairs.append(MappingPair(mill_id=mill_id, round_n=round_n, mapping=mapping))
            continue
        refuse(FINDING_CATALOG_MILL, f"pairs[{index}] unsupported mill format {source_format!r}")
    refuse_when(
        seen != {mill_id: windows[mill_id][1] for mill_id in windows},
        FINDING_CATALOG_PAIR_COUNT,
        f"pair counts drifted: {seen}",
    )
    _unique("slugs", slugs)
    _unique("mods", mods)
    _unique("tickets", tickets)
    _unique("domains", domains)
    return tuple(plant_pairs), tuple(mapping_pairs)


def load_catalog(path: Path | None = None, *, root: Path | None = None) -> Catalog:
    catalog_path = (path or default_catalog_path(root)).resolve()
    pairs_path = default_pairs_path(catalog_path)
    refuse_when(not catalog_path.is_file(), FINDING_CATALOG_FIELD_MISSING, f"missing {catalog_path}")
    refuse_when(not pairs_path.is_file(), FINDING_CATALOG_FIELD_MISSING, f"missing {pairs_path}")
    pair_rows, digest = _read_pair_rows(pairs_path)
    document = _require_object(load_strict_json(catalog_path.read_text(encoding="utf-8")), "catalog")
    _validate_header(document, digest)
    plant_pairs, mapping_pairs = _validate_rows(pair_rows)
    mills = tuple(
        Mill(
            mill_id=str(item["mill_id"]),
            source_format=str(item["source_format"]),
            path=str(item["path"]),
            sha256=str(item["sha256"]),
            plants=str(item["plants"]) if item.get("plants") else None,
            plants_sha256=str(item["plants_sha256"]) if item.get("plants_sha256") else None,
            catalog_first=int(item["catalog_first"]),
            n_pairs=int(item["n_pairs"]),
        )
        for item in document["mills"]
    )
    return Catalog(
        path=catalog_path,
        pairs_path=pairs_path,
        family_prefix=FAMILY_PREFIX,
        factory=FACTORY,
        generator=GENERATOR,
        quota_per_round=QUOTA_PER_ROUND,
        source=MappingProxyType(dict(document["source"])),
        mills=mills,
        pairs=plant_pairs,
        mapping_pairs=mapping_pairs,
        pairs_sha256=digest,
    )


def catalog_check(path: Path | None = None, *, root: Path | None = None) -> Catalog:
    """Load the committed catalog and re-assert the leftover-event contract."""

    catalog = load_catalog(path, root=root)
    refuse_first(
        (
            (
                catalog.source.get("commit") != LEGACY_COMMIT,
                FINDING_CATALOG_SCHEMA,
                "source.commit drifted from the leftover mill family commit",
            ),
            (
                catalog.mills[0].path != LEGACY_MILL,
                FINDING_CATALOG_SCHEMA,
                "leftover3 mill path drifted",
            ),
            (
                catalog.mills[0].plants != LEGACY_PLANTS,
                FINDING_CATALOG_SCHEMA,
                "leftover3 plants path drifted",
            ),
            (
                catalog.mills[0].plants_sha256 != LEGACY_PLANTS_SHA256,
                FINDING_CATALOG_SCHEMA,
                "leftover3 plants_sha256 drifted",
            ),
            (
                catalog.mills[0].sha256 != LEGACY_MILL_SHA256,
                FINDING_CATALOG_SCHEMA,
                "leftover3 mill_sha256 drifted",
            ),
            (
                catalog.mills[1].path != LEGACY_MAPPING_MILL,
                FINDING_CATALOG_SCHEMA,
                "lll-r56 mill path drifted",
            ),
            (
                catalog.mills[1].sha256 != LEGACY_MAPPING_MILL_SHA256,
                FINDING_CATALOG_SCHEMA,
                "lll-r56 mill_sha256 drifted",
            ),
        )
    )
    refuse_when(len(catalog.pairs) != N_PLANT_PAIRS, FINDING_CATALOG_PAIR_COUNT, "plant pair count drifted")
    refuse_when(
        len(catalog.mapping_pairs) != N_MAPPING_PAIRS,
        FINDING_CATALOG_PAIR_COUNT,
        "mapping pair count drifted",
    )
    return catalog


bind_import_twin(__name__)
