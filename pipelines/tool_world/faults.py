#!/usr/bin/env python3
"""Seeded fault schedules: which declared faults arm, and on which call they fire.

A task declares faults; the seed decides. Every declared fault consumes the
same draws whether or not it arms, so a later fault's schedule never shifts
when an earlier one is disarmed, and replay re-derives the identical schedule
from the identical seed. Firing is a function of the call history alone: the
``n``-th call matching a fault's selector fires it, whoever the solver is. A
selector key may be dotted (``params.name``) to reach into nested arguments.

The scripted ``Action`` (a plan step or a recovery step) is parsed here too,
because a fault's recovery is a tuple of them and must be parsed at load, not
on the seeds where the fault happens to fire; ``pack`` re-exports it.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any

from . import vocabulary as cv
from ._contract import bind_import_twin, rng

__all__ = [
    "Action",
    "FaultEngine",
    "FaultSpec",
    "ScheduledFault",
    "action_from_row",
    "fault_spec_from_row",
    "schedule_faults",
]


@dataclass(frozen=True)
class Action:
    """One scripted step: the intent the basis cites and the call the solver makes."""

    intent: str
    tool_call: Mapping[str, Any]
    captures: Mapping[str, str]
    verification: bool
    confirmation: bool


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
    recovery: tuple[Action, ...]
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


def _require_str(row: Mapping[str, Any], key: str, where: str) -> str:
    value = row.get(key)
    cv.refuse_when(
        not isinstance(value, str) or not value.strip(),
        cv.FINDING_TASK_FIELD_INVALID,
        f"{where}: {key} must be a nonempty string",
    )
    return value


def _captures(row: Mapping[str, Any], where: str) -> dict[str, str]:
    """Capture regexes, each compiled at load and required to expose one group."""
    captures = row.get("captures", {})
    cv.refuse_when(
        not isinstance(captures, Mapping)
        or any(not isinstance(item, str) for item in captures.values()),
        cv.FINDING_TASK_FIELD_INVALID,
        f"{where}: captures must map names to regex strings",
    )
    for name, pattern in captures.items():
        try:
            compiled = re.compile(pattern)
        except re.error as exc:
            raise cv.ToolWorldRefusal(
                cv.FINDING_TASK_FIELD_INVALID,
                f"{where}: capture {name!r} is not a valid regex ({exc})",
            ) from exc
        cv.refuse_when(
            compiled.groups == 0,
            cv.FINDING_TASK_FIELD_INVALID,
            f"{where}: capture {name!r} needs a capturing group",
        )
    return dict(captures)


def action_from_row(row: Any, where: str) -> Action:
    """Parse one plan or recovery action row; an already-parsed ``Action`` passes through."""
    if isinstance(row, Action):
        return row
    cv.refuse_when(
        not isinstance(row, Mapping),
        cv.FINDING_TASK_FIELD_INVALID,
        f"{where}: action must be an object",
    )
    tool_call = row.get("tool_call")
    cv.refuse_when(
        not isinstance(tool_call, Mapping)
        or not isinstance(tool_call.get("name"), str)
        or not isinstance(tool_call.get("args"), Mapping),
        cv.FINDING_TASK_FIELD_INVALID,
        f"{where}: tool_call must carry a string name and an object args",
    )
    return Action(
        intent=_require_str(row, "intent", where),
        tool_call={"name": tool_call["name"], "args": dict(tool_call["args"])},
        captures=_captures(row, where),
        verification=_flag(row, "verification", False, where),
        confirmation=_flag(row, "confirmation", False, where),
    )


def _flag(row: Mapping[str, Any], key: str, default: bool, where: str) -> bool:
    """A declared boolean, never a coerced truthy value such as the string "false"."""
    value = row.get(key, default)
    cv.refuse_when(
        not isinstance(value, bool),
        cv.FINDING_TASK_FIELD_INVALID,
        f"{where}: {key} must be a boolean",
    )
    return value


def _params(row: Mapping[str, Any], where: str) -> dict[str, Any]:
    params = row.get("params", {})
    cv.refuse_when(
        not isinstance(params, Mapping),
        cv.FINDING_TASK_FIELD_INVALID,
        f"{where}: params must be an object",
    )
    return dict(params)


def _occurrences(row: Mapping[str, Any], where: str) -> tuple[int, int, int]:
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
    return occurrence, low, high


def _recovery(row: Mapping[str, Any], where: str) -> tuple[Action, ...]:
    recovery = row.get("recovery", [])
    cv.refuse_when(
        not isinstance(recovery, list) or any(not isinstance(item, Mapping) for item in recovery),
        cv.FINDING_TASK_FIELD_INVALID,
        f"{where}: recovery must be a list of actions",
    )
    return tuple(
        action_from_row(item, f"{where}.recovery[{index}]") for index, item in enumerate(recovery)
    )


def fault_spec_from_row(row: Any, where: str) -> FaultSpec:
    cv.refuse_when(
        not isinstance(row, Mapping),
        cv.FINDING_TASK_FIELD_INVALID,
        f"{where}: fault must be an object",
    )
    fault_id = _require(row, "id", str, where)
    occurrence, low, high = _occurrences(row, where)
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
        params=_params(row, where),
        marker=_require(row, "marker", str, where),
        recovery=_recovery(row, where),
        retry=_flag(row, "retry", True, where),
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


def _targets(spec: FaultSpec, tool: str, args: Mapping[str, Any]) -> bool:
    """The fault attaches to this call: its tool by name and its selector by argument."""
    return spec.tool == tool and _selector_matches(spec.selector, args)


def always_shows(_spec: FaultSpec) -> bool:
    """The default word on whether a call could show a fault's symptom: it could."""
    return True


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

    def _reached(self, entry: ScheduledFault) -> bool:
        """An armed fault fires on the call that brings its counter to its occurrence."""
        return entry.armed and self._counts[entry.fault_id] == entry.occurrence

    def check(
        self,
        tool: str,
        args: Mapping[str, Any],
        shows: Callable[[FaultSpec], bool] = always_shows,
    ) -> ScheduledFault | None:
        """Advance every matching counter; return the first armed fault reaching its occurrence.

        ``shows`` is the owning surface's word on whether this call could show a
        fault's symptom at all. A call that could not neither counts nor fires,
        so a fault is never recorded as fired without a visible symptom.
        """
        firing = None
        for entry in self._scheduled:
            if not _targets(entry.spec, tool, args) or not shows(entry.spec):
                continue
            self._counts[entry.fault_id] += 1
            if firing is None and self._reached(entry):
                firing = entry
        if firing is not None:
            self._fired.append(firing.fault_id)
        return firing


bind_import_twin(__name__)
