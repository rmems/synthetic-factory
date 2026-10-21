"""Dry-run plan for the OpenRouter writer. ``network_calls`` stays zero."""

from __future__ import annotations

from . import vocabulary as cv
from ._contract import bind_import_twin
from .ollama import embedding_request
from .ollama import writer_request as secondary_request
from .openrouter import Choice, request_params, require_effort, snapshot_of, writer_request
from .provenance import actors_for, lineage_for
from .scenarios import Scenario, catalog
from .splits import load_family

__all__ = ["dry_run_plan"]


def _nonneg(value: object) -> bool:
    if isinstance(value, bool) or not isinstance(value, int):
        return False
    return value >= 0


def _in_range(count: int, limit: int) -> bool:
    if not _nonneg(count):
        return False
    if count < 1:
        return False
    return count <= limit


def _choose(count: int) -> tuple[Scenario, ...]:
    rows = catalog()
    if _in_range(count, len(rows)):
        return rows[:count]
    raise cv.FamilyError("count", f"count must be in 1..{len(rows)}")


def _default_choice(seed: int) -> Choice:
    return Choice(cv.WRITER_MODEL, cv.REASONING_EFFORT, seed, False)


def _require_flag(value: object) -> None:
    if isinstance(value, bool):
        return
    raise cv.FamilyError("writer.secondary", "secondary writer flag must be boolean")


def _require_same_seed(seed: int, writer_seed: object) -> None:
    if writer_seed == seed:
        return
    raise cv.FamilyError("seed", "writer seed must match the run seed")


def _require_choice(seed: int, choice: Choice) -> Choice:
    snapshot_of(choice.model)
    require_effort(choice.effort)
    _require_flag(choice.secondary)
    _require_same_seed(seed, choice.seed)
    return choice


def _checked(seed: int, choice: Choice | None) -> Choice:
    if not _nonneg(seed):
        raise cv.FamilyError("seed", "seed must be a non-negative integer")
    picked = _default_choice(seed) if choice is None else choice
    return _require_choice(seed, picked)


def _model_row(role: str, name: str, provider: str) -> dict:
    return {
        "role": role,
        "provider": provider,
        "name": name,
        "digest": None,
        "digest_state": "unresolved",
    }


def _writer_row(choice: Choice) -> dict:
    row = _model_row(cv.WRITER_ROLE, choice.model, cv.WRITER_PROVIDER)
    row["snapshot"] = snapshot_of(choice.model)
    row["reasoning_effort"] = choice.effort
    return row


def _models(choice: Choice) -> list[dict]:
    rows = [_writer_row(choice)]
    if choice.secondary:
        rows.append(_model_row(cv.SECONDARY_ROLE, cv.SECONDARY_WRITER_MODEL, cv.OLLAMA_PROVIDER))
    rows.append(_model_row(cv.DEDUP_ROLE, cv.DEDUP_MODEL, cv.OLLAMA_PROVIDER))
    return rows


def _scenario_row(scenario: Scenario, family, run_seed: int) -> dict:
    split = family.splits[scenario.scenario_id]
    excluded = scenario.task_id in family.excluded_task_ids
    return {
        "scenario_id": scenario.scenario_id,
        "task_id": scenario.task_id,
        "seed": scenario.seed,
        "run_seed": run_seed,
        "split": split,
        "held_out": split == cv.HELD_OUT,
        "train_export": split != cv.HELD_OUT and not excluded,
        "lineage": lineage_for(scenario, run_seed=run_seed, digest=family.config_sha256),
    }


def _writer_call(scenario: Scenario, choice: Choice) -> dict:
    prompt = f"plan-only task_id={scenario.task_id}"
    return {"role": cv.WRITER_ROLE, "request": writer_request(prompt, choice), "sent": False}


def _secondary_call(scenario: Scenario) -> dict:
    prompt = f"plan-only task_id={scenario.task_id}"
    return {"role": cv.SECONDARY_ROLE, "request": secondary_request(prompt), "sent": False}


def _dedup_call(scenario: Scenario) -> dict:
    return {
        "role": cv.DEDUP_ROLE,
        "request": embedding_request(scenario.task_id),
        "sent": False,
    }


def _one(scenario: Scenario, choice: Choice) -> list[dict]:
    calls = [_writer_call(scenario, choice)]
    if choice.secondary:
        calls.append(_secondary_call(scenario))
    calls.append(_dedup_call(scenario))
    return calls


def _calls(scenarios: tuple[Scenario, ...], choice: Choice) -> list[dict]:
    planned: list[dict] = []
    for scenario in scenarios:
        planned.extend(_one(scenario, choice))
    return planned


def _writer_actor(choice: Choice) -> dict:
    params = request_params(choice)
    return {
        "role": cv.WRITER_ROLE,
        "name": choice.model,
        "digest": None,
        "provider": cv.WRITER_PROVIDER,
        "model": params["model"],
        "snapshot": snapshot_of(choice.model),
        "reasoning_effort": choice.effort,
        "seed": params["seed"],
        "request_params": params,
    }


def _secondary_actor(seed: int) -> dict:
    return {
        "role": cv.SECONDARY_ROLE,
        "name": cv.SECONDARY_WRITER_MODEL,
        "digest": None,
        "provider": cv.OLLAMA_PROVIDER,
        "model": cv.SECONDARY_WRITER_MODEL,
        "snapshot": None,
        "reasoning_effort": None,
        "seed": seed,
        "request_params": {"model": cv.SECONDARY_WRITER_MODEL, "stream": False},
    }


def _actors(family, choice: Choice) -> list[dict]:
    actors = actors_for(family.config_sha256)
    actors.append(_writer_actor(choice))
    if choice.secondary:
        actors.append(_secondary_actor(choice.seed))
    actors.append({"role": cv.DEDUP_ROLE, "name": cv.DEDUP_MODEL, "digest": None})
    return actors


def _provenance(
    family,
    produced_at: str | None,
    scenarios: tuple[Scenario, ...],
    choice: Choice,
) -> dict:
    return {
        "produced_at": produced_at,
        "actors": _actors(family, choice),
        "lineage": {
            "run_seed": choice.seed,
            "builder": cv.BUILDER_NAME,
            "config_sha256": family.config_sha256,
            "parent_ids": [],
            "scenario_ids": [item.scenario_id for item in scenarios],
        },
    }


def dry_run_plan(
    *,
    seed: int,
    count: int,
    produced_at: str | None = None,
    choice: Choice | None = None,
) -> dict:
    """Describe the records a live run would build. No socket is opened."""

    picked = _checked(seed, choice)
    family = load_family()
    chosen = _choose(count)
    return {
        "dry_run": True,
        "records_written": 0,
        "network_calls": 0,
        "dataset": family.dataset,
        "family": cv.FAMILY,
        "run_seed": seed,
        "produced_at": produced_at,
        "models": _models(picked),
        "provenance": _provenance(family, produced_at, chosen, picked),
        "scenarios": [_scenario_row(item, family, seed) for item in chosen],
        "planned_calls": _calls(chosen, picked),
    }


bind_import_twin(__name__)
