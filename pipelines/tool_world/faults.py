#!/usr/bin/env python3
"""Seeded fault schedules: which declared faults arm, and on which call they fire.

A task declares faults; the seed decides. Every declared fault consumes the
same draws whether or not it arms, so a later fault's schedule never shifts
when an earlier one is disarmed, and replay re-derives the identical schedule
from the identical seed. Firing is a function of the call history alone: the
``n``-th call matching a fault's selector fires it, whoever the solver is. A
selector key may be dotted (``params.name``) to reach into nested arguments.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from . import vocabulary as cv
from ._contract import bind_import_twin, rng

__all__ = ["FaultEngine", "FaultSpec", "ScheduledFault", "fault_spec_from_row", "schedule_faults"]


@dataclass(frozen=True)
class FaultSpec:
    """One declared fault: what it is, which calls it attaches to, how often it arms."""

    fault_id: str
    surface: str
    kind: str
    tool: str
    selector: Mapping[str, Any]
    occurrence: int
    min_occurrence: int
    max_occurrence: int
    probability_percent: int
    params: Mapping[str, Any]
    marker: str
    recovery: tuple[Mapping[str, Any], ...]
    retry: bool


@dataclass(frozen=True)
class ScheduledFault:
    spec: FaultSpec
    armed: bool
    occurrence: int

    @property
    def fault_id(self) -> str:
        return self.spec.fault_id


def _require(row: Mapping[str, Any], key: str, kind: type, where: str) -> Any:
    value = row.get(key)
    cv.refuse_when(
        not isinstance(value, kind) or (kind is int and isinstance(value, bool)),
        cv.FINDING_TASK_FIELD_INVALID,
        f"{where}: fault field {key!r} must be {kind.__name__}",
    )
    return value


def fault_spec_from_row(row: Any, where: str) -> FaultSpec:
    cv.refuse_when(
        not isinstance(row, Mapping),
        cv.FINDING_TASK_FIELD_INVALID,
        f"{where}: fault must be an object",
    )
    fault_id = _require(row, "id", str, where)
    occurrence = row.get("occurrence", 1)
    cv.refuse_when(
        not cv.is_genuine_int(occurrence) or occurrence < 0,
        cv.FINDING_TASK_FIELD_INVALID,
        f"{where}: occurrence must be a non-negative integer",
    )
    low = row.get("min_occurrence", 1)
    high = row.get("max_occurrence", low)
    cv.refuse_when(
        not (cv.is_genuine_int(low) and cv.is_genuine_int(high)) or not 1 <= low <= high,
        cv.FINDING_TASK_FIELD_INVALID,
        f"{where}: min_occurrence/max_occurrence must satisfy 1 <= min <= max",
    )
    percent = row.get("probability_percent", 100)
    cv.refuse_when(
        not cv.is_genuine_int(percent) or not 0 <= percent <= 100,
        cv.FINDING_TASK_FIELD_INVALID,
        f"{where}: probability_percent must be an integer in [0, 100]",
    )
    selector = row.get("selector", {})
    cv.refuse_when(
        not isinstance(selector, Mapping),
        cv.FINDING_TASK_FIELD_INVALID,
        f"{where}: selector must be an object",
    )
    recovery = row.get("recovery", [])
    cv.refuse_when(
        not isinstance(recovery, list) or any(not isinstance(item, Mapping) for item in recovery),
        cv.FINDING_TASK_FIELD_INVALID,
        f"{where}: recovery must be a list of actions",
    )
    return FaultSpec(
        fault_id=fault_id,
        surface=_require(row, "surface", str, where),
        kind=_require(row, "kind", str, where),
        tool=_require(row, "tool", str, where),
        selector=dict(selector),
        occurrence=occurrence,
        min_occurrence=low,
        max_occurrence=high,
        probability_percent=percent,
        params=dict(row.get("params") or {}),
        marker=_require(row, "marker", str, where),
        recovery=tuple(dict(item) for item in recovery),
        retry=bool(row.get("retry", True)),
    )


def schedule_faults(
    specs: tuple[FaultSpec, ...], stream: rng.DrawStream
) -> tuple[ScheduledFault, ...]:
    """Arm faults and fix their occurrence from the stream, consuming draws for every spec."""
    scheduled = []
    for spec in specs:
        armed = stream.chance(spec.probability_percent / 100)
        drawn = stream.randint(spec.min_occurrence, spec.max_occurrence)
        occurrence = spec.occurrence if spec.occurrence > 0 else drawn
        scheduled.append(ScheduledFault(spec, armed, occurrence))
    return tuple(scheduled)


def _lookup(args: Mapping[str, Any], dotted: str) -> Any:
    """``args["params"]["name"]`` for the selector key ``params.name``; None when absent."""
    value: Any = args
    for part in dotted.split("."):
        if not isinstance(value, Mapping) or part not in value:
            return None
        value = value[part]
    return value


def _selector_matches(selector: Mapping[str, Any], args: Mapping[str, Any]) -> bool:
    return all(_lookup(args, key) == value for key, value in selector.items())


class FaultEngine:
    """Count matching calls and hand back the fault that fires on this one, if any."""

    def __init__(self, scheduled: tuple[ScheduledFault, ...]) -> None:
        self._scheduled = scheduled
        self._counts = {entry.fault_id: 0 for entry in scheduled}
        self._fired: list[str] = []

    @property
    def scheduled(self) -> tuple[ScheduledFault, ...]:
        return self._scheduled

    @property
    def fired(self) -> tuple[str, ...]:
        return tuple(self._fired)

    def armed_ids(self) -> tuple[str, ...]:
        return tuple(entry.fault_id for entry in self._scheduled if entry.armed)

    def check(self, tool: str, args: Mapping[str, Any]) -> ScheduledFault | None:
        """Advance every matching counter; return the first armed fault reaching its occurrence."""
        firing = None
        for entry in self._scheduled:
            if entry.spec.tool != tool or not _selector_matches(entry.spec.selector, args):
                continue
            self._counts[entry.fault_id] += 1
            if firing is None and entry.armed and self._counts[entry.fault_id] == entry.occurrence:
                firing = entry
        if firing is not None:
            self._fired.append(firing.fault_id)
        return firing


bind_import_twin(__name__)
