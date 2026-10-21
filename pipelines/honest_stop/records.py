"""Build one record by executing the scenario. ``verified_blocker`` is measured."""

from __future__ import annotations

from . import vocabulary as cv
from ._contract import bind_import_twin
from .measure import blocker_verified, claim_holds
from .provenance import actors_for, lineage_for
from .replay import Replay
from .scenarios import Scenario, by_id
from .splits import FamilyConfig, load_family
from .validate import validate_record
from .world import World, execute

__all__ = ["build_record"]


def _run_seed_ok(run_seed: object) -> bool:
    if isinstance(run_seed, bool):
        return False
    if not isinstance(run_seed, int):
        return False
    return run_seed >= 0


def _require_scenario(scenario_id: str) -> Scenario:
    scenario = by_id(scenario_id)
    if scenario is None:
        raise cv.FamilyError("scenario.unknown", scenario_id)
    return scenario


def _require_run_seed(run_seed: int) -> None:
    if _run_seed_ok(run_seed):
        return
    raise cv.FamilyError("seed", "run_seed must be a non-negative integer")


def _trajectory(scenario: Scenario) -> tuple[list[dict], tuple[str, ...], World]:
    world = scenario.world()
    steps = []
    observations = []
    for index, call in enumerate(scenario.tool_calls(), start=1):
        observation = execute(world, call["name"], dict(call["args"]))
        observations.append(observation)
        steps.append({"n": index, "tool_call": call, "observation": observation})
    return steps, tuple(observations), world


def _require_blocker(measured: object) -> bool:
    if measured is True:
        return True
    raise cv.FamilyError("scenario.blocker", "scenario did not verify a blocker")


def _require_false_claim(holds: object) -> None:
    if holds is False:
        return
    raise cv.FamilyError("scenario.counterfactual", "canonical counterfactual is not false")


def _record_body(
    scenario: Scenario,
    steps: list[dict],
    measured: bool,
    family: FamilyConfig,
    produced_at: str,
    run_seed: int,
) -> dict:
    return {
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


def _require_shape(record: dict) -> None:
    findings = validate_record(record)
    if not findings:
        return
    raise cv.FamilyError("record.invalid", " ".join(findings))


def build_record(scenario_id: str, *, produced_at: str, run_seed: int) -> dict:
    """Execute ``scenario_id`` and return one structurally valid record."""

    scenario = _require_scenario(scenario_id)
    _require_run_seed(run_seed)
    family = load_family()
    steps, observations, world = _trajectory(scenario)
    replayed = Replay(scenario, world, observations, None)
    measured = _require_blocker(blocker_verified(replayed))
    _require_false_claim(claim_holds(scenario.counterfactual, world, observations, scenario))
    record = _record_body(scenario, steps, measured, family, produced_at, run_seed)
    _require_shape(record)
    return record


bind_import_twin(__name__)
