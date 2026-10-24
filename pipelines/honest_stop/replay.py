"""Re-execute a record's tool calls against the scenario's fresh world."""

from __future__ import annotations

from dataclasses import dataclass

from . import vocabulary as cv
from ._contract import bind_import_twin
from .scenarios import Scenario, by_id
from .world import World, execute

__all__ = ["Replay", "replay_record"]


@dataclass
class Replay:
    """The world after the calls that matched, plus a code when replay stopped."""

    scenario: Scenario | None
    world: World | None
    observations: tuple[str, ...]
    code: str | None


def _context_code(record: dict, scenario: Scenario | None) -> str | None:
    if scenario is None:
        return "scenario.unknown"
    context = record["context"]
    if context["seed"] != scenario.seed:
        return "context.seed"
    if context["task_id"] != scenario.task_id:
        return "context.task_id"
    if context["world"] != cv.WORLD:
        return "context.world"
    return None


def _empty(scenario: Scenario | None, code: str) -> Replay:
    return Replay(scenario, None, (), code)


def _replay_steps(scenario: Scenario, steps: list, expected: tuple[dict, ...]) -> Replay:
    world = scenario.world()
    seen: list[str] = []
    for index, step in enumerate(steps):
        call = step["tool_call"]
        if call != expected[index]:
            return Replay(scenario, world, tuple(seen), "trajectory.tool_call")
        actual = execute(world, call["name"], dict(call["args"]))
        if actual != step["observation"]:
            return Replay(scenario, world, tuple(seen), "trajectory.observation_mismatch")
        seen.append(actual)
    return Replay(scenario, world, tuple(seen), None)


def replay_record(record: dict) -> Replay:
    """Execute the scenario's pinned calls. Observations must match the world exactly."""

    scenario = by_id(record["context"]["scenario_id"])
    code = _context_code(record, scenario)
    if code is not None or scenario is None:
        return _empty(scenario, code or "scenario.unknown")
    expected = scenario.tool_calls()
    if len(record["trajectory"]) != len(expected):
        return _empty(scenario, "trajectory.tool_call")
    return _replay_steps(scenario, record["trajectory"], expected)


bind_import_twin(__name__)
