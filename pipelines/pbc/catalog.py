#!/usr/bin/env python3
"""Load the first-slice PBC catalog. Never imports leftover mill scripts."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import _contract
from ._contract import (
    CATALOG_FORMAT,
    CATALOG_ID,
    DEFAULT_PLAN_PATH,
    FACTORY,
    FAMILY,
    FULL_EPISODE_COUNT,
    FULL_MILL_COUNT,
    FULL_PAIR_COUNT,
    GENERATOR,
    PLAN_SCHEMA_ID,
    PLAN_SLICE,
    QUOTA,
    SLICE_PAIR_COUNT,
    SOURCE_COMMIT,
    SOURCE_REF,
    refuse_vendor_paths,
)

CATALOG_FILENAME = "CATALOG.json"
PLANTS_FILENAME = "plants.jsonl"


@dataclass(frozen=True)
class MillBurstSpec:
    mill_id: str
    source: str
    start_round: int
    n_rounds: int
    pair_count: int
    full_n_rounds: int

    @property
    def episodes(self) -> int:
        return self.n_rounds * QUOTA

    @property
    def end_round_inclusive(self) -> int:
        return self.start_round + self.n_rounds - 1


@dataclass(frozen=True)
class MillUsageBurstPlan:
    path: Path
    family_prefix: str
    factory: str
    slice: str
    label: str
    run_label: str
    quota_per_round: int
    mills: tuple[MillBurstSpec, ...]

    def counts(self) -> dict[str, int]:
        return {
            "mills": len(self.mills),
            "rounds": sum(m.n_rounds for m in self.mills),
            "pairs": sum(m.pair_count for m in self.mills),
            "episodes": sum(m.episodes for m in self.mills),
        }


@dataclass(frozen=True)
class PlantPair:
    mill_id: str
    catalog_first: int
    start: int
    full_n_rounds: int
    notes_extra: str
    notes_footer: str
    ok: dict[str, Any]
    bad: dict[str, Any]


@dataclass(frozen=True)
class PbcCatalog:
    catalog_id: str
    plants_sha256: str
    mills: tuple[MillBurstSpec, ...]
    pairs: tuple[PlantPair, ...]
    header: Mapping[str, Any]

    def mill(self, mill_id: str) -> PlantPair:
        for pair in self.pairs:
            if pair.mill_id == mill_id:
                return pair
        raise KeyError(f"unknown pbc burst mill {mill_id!r}")


class PlanValidationError(ValueError):
    """Raised when the committed plan disagrees with the first-slice catalog."""


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def default_catalog_dir() -> Path:
    return Path(__file__).resolve().parent


def _restore_plant(raw: Any, where: str) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raise PlanValidationError(f"{where} must be an object")
    plant = dict(raw)
    imports = plant.get("imports")
    if isinstance(imports, list):
        plant["imports"] = tuple(imports)
    return plant


def _read_jsonl(path: Path) -> tuple[Any, ...]:
    text = path.read_text(encoding="utf-8")
    if not text.endswith("\n") or "\r" in text:
        raise PlanValidationError(f"{path.name} must be LF-framed jsonl")
    rows = []
    for index, line in enumerate(text.splitlines(), start=1):
        if not line:
            raise PlanValidationError(f"{path.name}:{index} is empty")
        rows.append(json.loads(line))
    return tuple(rows)


def _pair_from_row(row: Any, where: str) -> PlantPair:
    if not isinstance(row, dict):
        raise PlanValidationError(f"{where} must be an object")
    mill_id = row.get("mill_id")
    if not isinstance(mill_id, str) or not mill_id.startswith("pbc_r"):
        raise PlanValidationError(f"{where}.mill_id is invalid")
    return PlantPair(
        mill_id=mill_id,
        catalog_first=int(row["catalog_first"]),
        start=int(row["start"]),
        full_n_rounds=int(row["full_n_rounds"]),
        notes_extra=str(row.get("notes_extra") or ""),
        notes_footer=str(row.get("notes_footer") or ""),
        ok=_restore_plant(row.get("ok"), f"{where}.ok"),
        bad=_restore_plant(row.get("bad"), f"{where}.bad"),
    )


def load_catalog(directory: Path | None = None) -> PbcCatalog:
    """Load ``CATALOG.json`` + compact ``plants.jsonl`` and refuse a digest drift."""

    root = default_catalog_dir() if directory is None else Path(directory)
    refuse_vendor_paths(root.iterdir())
    header_path = root / CATALOG_FILENAME
    plants_path = root / PLANTS_FILENAME
    header = json.loads(header_path.read_text(encoding="utf-8"))
    plants_raw = plants_path.read_bytes()
    digest = sha256_bytes(plants_raw)
    if header.get("catalog_id") != CATALOG_ID:
        raise PlanValidationError(f"catalog_id must be {CATALOG_ID!r}")
    if header.get("format") != CATALOG_FORMAT:
        raise PlanValidationError(f"format must be {CATALOG_FORMAT!r}")
    if header.get("family") != FAMILY or header.get("factory") != FACTORY:
        raise PlanValidationError("catalog family/factory drifted")
    if header.get("generator") != GENERATOR:
        raise PlanValidationError("catalog generator drifted")
    if header.get("plants_sha256") != digest:
        raise PlanValidationError("plants.jsonl digest differs from CATALOG.json")
    extract = header.get("extract")
    if not isinstance(extract, dict) or extract.get("exec") is not False:
        raise PlanValidationError("extract.exec must be false")
    if extract.get("method") != "ast.parse":
        raise PlanValidationError("extract.method must be ast.parse")
    if extract.get("source_commit") != SOURCE_COMMIT:
        raise PlanValidationError("extract.source_commit drifted")
    if extract.get("source_ref") != SOURCE_REF:
        raise PlanValidationError("extract.source_ref drifted")
    if extract.get("full_pair_count") != FULL_PAIR_COUNT:
        raise PlanValidationError("extract.full_pair_count drifted")
    rows = _read_jsonl(plants_path)
    pairs = tuple(_pair_from_row(row, f"{PLANTS_FILENAME}:{i}") for i, row in enumerate(rows, 1))
    if len(pairs) != SLICE_PAIR_COUNT or len(pairs) != header.get("row_count"):
        raise PlanValidationError("first-slice row_count drifted")
    mill_rows = header.get("mills")
    if not isinstance(mill_rows, list) or len(mill_rows) != FULL_MILL_COUNT:
        raise PlanValidationError("catalog mills must list the eight burst mills")
    mills = []
    for raw in mill_rows:
        mill_id = raw["mill_id"]
        pair = next(item for item in pairs if item.mill_id == mill_id)
        mills.append(
            MillBurstSpec(
                mill_id=mill_id,
                source=str(raw["source"]),
                start_round=int(raw["start_round"]),
                n_rounds=1,
                pair_count=1,
                full_n_rounds=int(raw["full_n_rounds"]),
            )
        )
        if pair.ok["slug"] != raw["first_ok_slug"] or pair.bad["slug"] != raw["first_bad_slug"]:
            raise PlanValidationError(f"{mill_id} first-slice slugs drifted")
        if pair.full_n_rounds != raw["full_n_rounds"]:
            raise PlanValidationError(f"{mill_id} full_n_rounds drifted")
    return PbcCatalog(
        catalog_id=CATALOG_ID,
        plants_sha256=digest,
        mills=tuple(mills),
        pairs=pairs,
        header=header,
    )


def _require_int(raw: object, field: str) -> int:
    if not isinstance(raw, int) or isinstance(raw, bool):
        raise PlanValidationError(f"{field} must be an integer, got {raw!r}")
    return raw


def _require_str(raw: object, field: str) -> str:
    if not isinstance(raw, str) or not raw:
        raise PlanValidationError(f"{field} must be a non-empty string, got {raw!r}")
    return raw


def load_mill_usage_burst_plan(
    path: Path | None = None,
    *,
    repo_root: Path | None = None,
    validate_plants: bool = True,
) -> MillUsageBurstPlan:
    """Load the first-slice burst plan and cross-check the compact catalog."""

    root = (repo_root or Path(__file__).resolve().parents[2]).resolve()
    plan_path = (path or root / DEFAULT_PLAN_PATH).resolve()
    raw = json.loads(plan_path.read_text(encoding="utf-8"))
    if raw.get("schema_id") != PLAN_SCHEMA_ID:
        raise PlanValidationError(f"schema_id must be {PLAN_SCHEMA_ID!r}")
    if raw.get("family_prefix") != FAMILY:
        raise PlanValidationError(f"family_prefix must be {FAMILY!r}")
    if raw.get("factory") != FACTORY:
        raise PlanValidationError(f"factory must be {FACTORY!r}")
    if raw.get("slice") != PLAN_SLICE:
        raise PlanValidationError(f"slice must be {PLAN_SLICE!r}")
    quota = _require_int(raw.get("quota_per_round"), "quota_per_round")
    if quota != QUOTA:
        raise PlanValidationError(f"quota_per_round must be {QUOTA}")
    mills_raw = raw.get("mills")
    if not isinstance(mills_raw, list) or not mills_raw:
        raise PlanValidationError("mills must be a non-empty list")
    mills = []
    for entry in mills_raw:
        mill_id = _require_str(entry.get("id"), "mills[].id")
        n_rounds = _require_int(entry.get("n_rounds"), "mills[].n_rounds")
        pair_count = _require_int(entry.get("pair_count"), "mills[].pair_count")
        if n_rounds != 1 or pair_count != 1:
            raise PlanValidationError(f"{mill_id}: first-slice n_rounds/pair_count must be 1")
        mills.append(
            MillBurstSpec(
                mill_id=mill_id,
                source=_require_str(entry.get("source"), "mills[].source"),
                start_round=_require_int(entry.get("start_round"), "mills[].start_round"),
                n_rounds=n_rounds,
                pair_count=pair_count,
                full_n_rounds=_require_int(entry.get("full_n_rounds"), "mills[].full_n_rounds"),
            )
        )
    plan = MillUsageBurstPlan(
        path=plan_path,
        family_prefix=FAMILY,
        factory=FACTORY,
        slice=PLAN_SLICE,
        label=_require_str(raw.get("label"), "label"),
        run_label=_require_str(raw.get("run_label"), "run_label"),
        quota_per_round=quota,
        mills=tuple(mills),
    )
    totals = raw.get("totals")
    if isinstance(totals, dict):
        for key, value in plan.counts().items():
            if totals.get(key) != value:
                raise PlanValidationError(f"totals.{key} is {totals.get(key)!r}, expected {value}")
        if totals.get("full_pairs") != FULL_PAIR_COUNT:
            raise PlanValidationError("totals.full_pairs drifted from the full extract")
        if totals.get("full_episodes") != FULL_EPISODE_COUNT:
            raise PlanValidationError("totals.full_episodes drifted from the full extract")
    if validate_plants:
        loaded = load_catalog()
        ids = [m.mill_id for m in plan.mills]
        if ids != [m.mill_id for m in loaded.mills]:
            raise PlanValidationError("plan mill order drifted from CATALOG.json")
        if plan.counts()["pairs"] != SLICE_PAIR_COUNT:
            raise PlanValidationError("plan first-slice pair count drifted")
    return plan


__all__ = [
    "CATALOG_FILENAME",
    "MillBurstSpec",
    "MillUsageBurstPlan",
    "PbcCatalog",
    "PLANTS_FILENAME",
    "PlanValidationError",
    "PlantPair",
    "default_catalog_dir",
    "load_catalog",
    "load_mill_usage_burst_plan",
    "sha256_bytes",
]

_contract.bind_import_twin(__name__)
