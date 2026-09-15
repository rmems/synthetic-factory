#!/usr/bin/env python3
"""Load and validate the mill-usage-burst plan for slice A (``pbc``)."""

from __future__ import annotations

import importlib
import json
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Any

from . import vocabulary as pv
from .burst_registry import BURST_MILLS


@dataclass(frozen=True)
class MillBurstSpec:
    mill_id: str
    plants_module: str
    start_round: int
    n_rounds: int
    pair_count: int

    @property
    def episodes(self) -> int:
        return self.n_rounds * pv.QUOTA_PER_ROUND

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

    @property
    def mill_count(self) -> int:
        return len(self.mills)

    @property
    def round_count(self) -> int:
        return sum(m.n_rounds for m in self.mills)

    @property
    def pair_count(self) -> int:
        return sum(m.pair_count for m in self.mills)

    @property
    def episode_count(self) -> int:
        return sum(m.episodes for m in self.mills)

    def counts(self) -> dict[str, int]:
        return {
            "mills": self.mill_count,
            "rounds": self.round_count,
            "pairs": self.pair_count,
            "episodes": self.episode_count,
        }


class PlanValidationError(ValueError):
    """Raised when the committed plan disagrees with burst plants modules."""


def _require_int(raw: object, field: str) -> int:
    if not isinstance(raw, int) or isinstance(raw, bool):
        raise PlanValidationError(f"{field} must be an integer, got {raw!r}")
    return raw


def _require_str(raw: object, field: str) -> str:
    if not isinstance(raw, str) or not raw:
        raise PlanValidationError(f"{field} must be a non-empty string, got {raw!r}")
    return raw


def _parse_mill(entry: dict[str, Any]) -> MillBurstSpec:
    if not isinstance(entry, dict):
        raise PlanValidationError("each mills[] entry must be an object")
    mill_id = _require_str(entry.get("id"), "mills[].id")
    plants_module = _require_str(entry.get("plants_module"), "mills[].plants_module")
    start_round = _require_int(entry.get("start_round"), "mills[].start_round")
    n_rounds = _require_int(entry.get("n_rounds"), "mills[].n_rounds")
    pair_count = _require_int(entry.get("pair_count"), "mills[].pair_count")
    if n_rounds < 1:
        raise PlanValidationError(f"{mill_id}: n_rounds must be >= 1")
    if pair_count != n_rounds:
        raise PlanValidationError(
            f"{mill_id}: pair_count ({pair_count}) must equal n_rounds ({n_rounds})"
        )
    return MillBurstSpec(mill_id, plants_module, start_round, n_rounds, pair_count)


def _load_plants(module_name: str) -> ModuleType:
    try:
        return importlib.import_module(module_name)
    except ModuleNotFoundError as exc:
        raise PlanValidationError(f"plants module {module_name!r} not importable") from exc


def load_mill_usage_burst_plan(
    path: Path | None = None,
    *,
    repo_root: Path | None = None,
    validate_plants: bool = True,
) -> MillUsageBurstPlan:
    """Load ``config/mill-usage-burst-plan.pbc-a.json`` and cross-check plants modules."""

    root = (repo_root or Path(__file__).resolve().parents[2]).resolve()
    plan_path = (path or root / pv.DEFAULT_PLAN_PATH).resolve()
    raw = json.loads(plan_path.read_text(encoding="utf-8"))
    if raw.get("schema_id") != pv.PLAN_SCHEMA_ID:
        raise PlanValidationError(f"schema_id must be {pv.PLAN_SCHEMA_ID!r}")
    if raw.get("family_prefix") != pv.FAMILY_PREFIX:
        raise PlanValidationError(f"family_prefix must be {pv.FAMILY_PREFIX!r}")
    if raw.get("factory") != pv.FACTORY:
        raise PlanValidationError(f"factory must be {pv.FACTORY!r}")
    if raw.get("slice") != pv.PLAN_SLICE:
        raise PlanValidationError(f"slice must be {pv.PLAN_SLICE!r}")
    quota = _require_int(raw.get("quota_per_round"), "quota_per_round")
    if quota != pv.QUOTA_PER_ROUND:
        raise PlanValidationError(f"quota_per_round must be {pv.QUOTA_PER_ROUND}")
    mills_raw = raw.get("mills")
    if not isinstance(mills_raw, list) or not mills_raw:
        raise PlanValidationError("mills must be a non-empty list")
    mills = tuple(_parse_mill(entry) for entry in mills_raw)
    plan = MillUsageBurstPlan(
        path=plan_path,
        family_prefix=pv.FAMILY_PREFIX,
        factory=pv.FACTORY,
        slice=pv.PLAN_SLICE,
        label=_require_str(raw.get("label"), "label"),
        run_label=_require_str(raw.get("run_label"), "run_label"),
        quota_per_round=quota,
        mills=mills,
    )
    totals = raw.get("totals")
    if isinstance(totals, dict):
        for key, value in plan.counts().items():
            if totals.get(key) != value:
                raise PlanValidationError(
                    f"totals.{key} is {totals.get(key)!r}, expected {value}"
                )
    if validate_plants:
        _validate_plants(plan)
    return plan


def _validate_plants(plan: MillUsageBurstPlan) -> None:
    for spec in plan.mills:
        if spec.mill_id not in BURST_MILLS:
            raise PlanValidationError(f"{spec.mill_id}: not registered in burst_registry")
        mod = _load_plants(spec.plants_module)
        if getattr(mod, "MILL_ID", None) != spec.mill_id:
            raise PlanValidationError(
                f"{spec.mill_id}: module MILL_ID={getattr(mod, 'MILL_ID', None)!r}"
            )
        for name, expected in (
            ("START", spec.start_round),
            ("N_ROUNDS", spec.n_rounds),
        ):
            actual = getattr(mod, name, None)
            if actual != expected:
                raise PlanValidationError(
                    f"{spec.mill_id}: module {name}={actual!r}, plan expects {expected}"
                )
        pairs = getattr(mod, "PAIRS", None)
        if not isinstance(pairs, tuple) or len(pairs) != spec.pair_count:
            raise PlanValidationError(
                f"{spec.mill_id}: len(PAIRS)={len(pairs) if pairs else None!r}, "
                f"expected {spec.pair_count}"
            )
