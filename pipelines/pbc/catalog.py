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
    DEFERRED_MILL_IDS,
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


def _check_header_identity(header: Mapping[str, Any], digest: str) -> None:
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


def _check_extract(extract: Any) -> None:
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


def _committed_pairs(plants_path: Path, header: Mapping[str, Any]) -> tuple[PlantPair, ...]:
    rows = _read_jsonl(plants_path)
    pairs = tuple(_pair_from_row(row, f"{PLANTS_FILENAME}:{i}") for i, row in enumerate(rows, 1))
    if len(pairs) != SLICE_PAIR_COUNT or len(pairs) != header.get("row_count"):
        raise PlanValidationError("committed row_count drifted")
    return pairs


def _catalog_spec(raw: Mapping[str, Any], mill_id: Any, n_committed: int) -> MillBurstSpec:
    return MillBurstSpec(
        mill_id=mill_id,
        source=str(raw["source"]),
        start_round=int(raw["start_round"]),
        n_rounds=n_committed,
        pair_count=n_committed,
        full_n_rounds=int(raw["full_n_rounds"]),
    )


def _catalog_mill(raw: Mapping[str, Any], by_mill: dict[str, list[PlantPair]]) -> MillBurstSpec:
    mill_id = raw["mill_id"]
    deferred = bool(raw.get("deferred")) or mill_id in DEFERRED_MILL_IDS
    if deferred:
        if by_mill.get(mill_id):
            raise PlanValidationError(f"{mill_id} is deferred but has committed pairs")
        return _catalog_spec(raw, mill_id, 0)
    mill_pairs = by_mill.get(mill_id)
    if not mill_pairs:
        raise PlanValidationError(f"{mill_id} has no committed pairs")
    first = mill_pairs[0]
    spec = _catalog_spec(raw, mill_id, len(mill_pairs))
    if first.ok["slug"] != raw["first_ok_slug"] or first.bad["slug"] != raw["first_bad_slug"]:
        raise PlanValidationError(f"{mill_id} first-pair slugs drifted")
    if first.full_n_rounds != raw["full_n_rounds"]:
        raise PlanValidationError(f"{mill_id} full_n_rounds drifted")
    return spec


def _catalog_mills(mill_rows: Any, pairs: tuple[PlantPair, ...]) -> tuple[MillBurstSpec, ...]:
    by_mill: dict[str, list[PlantPair]] = {}
    for pair in pairs:
        by_mill.setdefault(pair.mill_id, []).append(pair)
    if not isinstance(mill_rows, list) or len(mill_rows) != FULL_MILL_COUNT:
        raise PlanValidationError("catalog mills must list the eight burst mills")
    return tuple(_catalog_mill(raw, by_mill) for raw in mill_rows)


def load_catalog(directory: Path | None = None) -> PbcCatalog:
    """Load ``CATALOG.json`` + compact ``plants.jsonl`` and refuse a digest drift."""

    root = default_catalog_dir() if directory is None else Path(directory)
    refuse_vendor_paths(root.iterdir())
    header_path = root / CATALOG_FILENAME
    plants_path = root / PLANTS_FILENAME
    header = json.loads(header_path.read_text(encoding="utf-8"))
    plants_raw = plants_path.read_bytes()
    digest = sha256_bytes(plants_raw)
    _check_header_identity(header, digest)
    extract = header.get("extract")
    _check_extract(extract)
    pairs = _committed_pairs(plants_path, header)
    extract_deferred = extract.get("deferred_mills")
    if extract_deferred != sorted(DEFERRED_MILL_IDS):
        raise PlanValidationError("extract.deferred_mills drifted")
    return PbcCatalog(
        catalog_id=CATALOG_ID,
        plants_sha256=digest,
        mills=_catalog_mills(header.get("mills"), pairs),
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


def _check_plan_identity(raw: Mapping[str, Any]) -> int:
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
    return quota


def _plan_mill(entry: Mapping[str, Any]) -> MillBurstSpec:
    mill_id = _require_str(entry.get("id"), "mills[].id")
    if mill_id in DEFERRED_MILL_IDS:
        raise PlanValidationError(f"{mill_id} must be listed under deferred_mills, not mills")
    n_rounds = _require_int(entry.get("n_rounds"), "mills[].n_rounds")
    pair_count = _require_int(entry.get("pair_count"), "mills[].pair_count")
    if n_rounds < 1 or pair_count != n_rounds:
        raise PlanValidationError(f"{mill_id}: pair_count must equal n_rounds")
    return MillBurstSpec(
        mill_id=mill_id,
        source=_require_str(entry.get("source"), "mills[].source"),
        start_round=_require_int(entry.get("start_round"), "mills[].start_round"),
        n_rounds=n_rounds,
        pair_count=pair_count,
        full_n_rounds=_require_int(entry.get("full_n_rounds"), "mills[].full_n_rounds"),
    )


def _plan_mills(mills_raw: Any) -> tuple[MillBurstSpec, ...]:
    if not isinstance(mills_raw, list) or not mills_raw:
        raise PlanValidationError("mills must be a non-empty list")
    return tuple(_plan_mill(entry) for entry in mills_raw)


def _check_plan_deferred(deferred_raw: Any) -> None:
    if not isinstance(deferred_raw, list):
        raise PlanValidationError("deferred_mills must be a list")
    deferred_ids = []
    for entry in deferred_raw:
        mill_id = _require_str(entry.get("id"), "deferred_mills[].id")
        if mill_id not in DEFERRED_MILL_IDS:
            raise PlanValidationError(f"unexpected deferred mill {mill_id!r}")
        deferred_ids.append(mill_id)
    if set(deferred_ids) != set(DEFERRED_MILL_IDS):
        raise PlanValidationError("deferred_mills must cover every deferred catalog mill")


def _check_plan_totals(totals: Any, plan: MillUsageBurstPlan) -> None:
    if not isinstance(totals, dict):
        return
    for key, value in plan.counts().items():
        if totals.get(key) != value:
            raise PlanValidationError(f"totals.{key} is {totals.get(key)!r}, expected {value}")
    if totals.get("deferred_mills") != len(DEFERRED_MILL_IDS):
        raise PlanValidationError("totals.deferred_mills drifted")
    if totals.get("full_pairs") != FULL_PAIR_COUNT:
        raise PlanValidationError("totals.full_pairs drifted from the full extract")
    if totals.get("full_episodes") != FULL_EPISODE_COUNT:
        raise PlanValidationError("totals.full_episodes drifted from the full extract")


def _active_catalog_mills() -> list[MillBurstSpec]:
    loaded = load_catalog()
    return [m for m in loaded.mills if m.mill_id not in DEFERRED_MILL_IDS]


def _check_plan_against_catalog(plan: MillUsageBurstPlan) -> None:
    active_loaded = _active_catalog_mills()
    ids = [m.mill_id for m in plan.mills]
    if ids != [m.mill_id for m in active_loaded]:
        raise PlanValidationError("plan mill order drifted from committed CATALOG mills")
    for plan_mill, cat_mill in zip(plan.mills, active_loaded, strict=True):
        if plan_mill.n_rounds != cat_mill.n_rounds or plan_mill.pair_count != cat_mill.pair_count:
            raise PlanValidationError(f"{plan_mill.mill_id} committed pair counts drifted")
    if plan.counts()["pairs"] != SLICE_PAIR_COUNT:
        raise PlanValidationError("plan committed pair count drifted")


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
    quota = _check_plan_identity(raw)
    mills = _plan_mills(raw.get("mills"))
    _check_plan_deferred(raw.get("deferred_mills"))
    plan = MillUsageBurstPlan(
        path=plan_path,
        family_prefix=FAMILY,
        factory=FACTORY,
        slice=PLAN_SLICE,
        label=_require_str(raw.get("label"), "label"),
        run_label=_require_str(raw.get("run_label"), "run_label"),
        quota_per_round=quota,
        mills=mills,
    )
    _check_plan_totals(raw.get("totals"), plan)
    if validate_plants:
        _check_plan_against_catalog(plan)
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
