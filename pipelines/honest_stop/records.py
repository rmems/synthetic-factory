"""Build one record by executing the scenario. ``verified_blocker`` is measured."""

from __future__ import annotations

from . import vocabulary as cv
from ._contract import bind_import_twin
from .measure import blocker_verified, claim_holds
from .provenance import actors_for, lineage_for
from .replay import Replay
from .scenarios import by_id
from .splits import load_family
from .validate import validate_record
from .world import execute

__all__ = ["build_record"]


def _run_seed_ok(run_seed: object) -> bool:
    if isinstance(run_seed, bool) or not isinstance(run_seed, int):
        return False
    return run_seed >= 0


def _trajectory(scenario) -> tuple[list[dict], tuple[str, ...], object]:
    world = scenario.world()
    steps = []
    observations = []
    for index, call in enumerate(scenario.tool_calls(), start=1):
        observation = execute(world, call["name"], dict(call["args"]))
        observations.append(observation)
        steps.append({"n": index, "tool_call": call, "observation": observation})
    return steps, tuple(observations), world


def build_record(scenario_id: str, *, produced_at: str, run_seed: int) -> dict:
    """Execute ``scenario_id`` and return one structurally valid record."""

    scenario = by_id(scenario_id)
    if scenario is None:
        raise cv.FamilyError("scenario.unknown", scenario_id)
    if not _run_seed_ok(run_seed):
        raise cv.FamilyError("seed", "run_seed must be a non-negative integer")
    family = load_family()
    steps, observations, world = _trajectory(scenario)
    replayed = Replay(scenario, world, observations, None)
    measured = blocker_verified(replayed)
    if measured is not True:
        raise cv.FamilyError("scenario.blocker", "scenario did not verify a blocker")
    holds = claim_holds(scenario.counterfactual, world, observations, scenario)
    if holds is not False:
        raise cv.FamilyError("scenario.counterfactual", "canonical counterfactual is not false")
    record = {
        "record_id": f"stop-{scenario.scenario_id}-{scenario.seed}",
        "family": cv.FAMILY,
        "task": scenario.task,
        "context": {
            "scenario_id": scenario.scenario_id,
            "seed": scenario.seed,
            "task_id": scenario.task_id,
            "world": cv.WORLD,
        },
        "trajectory": steps,
        "correct_action": {"type": scenario.action_type, "message": scenario.message},
        "counterfactual_fake_success": scenario.counterfactual,
        "result": {"verified_blocker": measured},
        "provenance": {
            "produced_at": produced_at,
            "actors": actors_for(family.config_sha256),
            "lineage": lineage_for(scenario, run_seed=run_seed, digest=family.config_sha256),
        },
    }
    findings = validate_record(record)
    if findings:
        raise cv.FamilyError("record.invalid", " ".join(findings))
    return record


bind_import_twin(__name__)
