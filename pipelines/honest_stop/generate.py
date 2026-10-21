"""Dry-run plan for the local Ollama generator. It does not call :func:`perform`."""

from __future__ import annotations

from . import vocabulary as cv
from ._contract import bind_import_twin
from .ollama import embedding_request, writer_request
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


def _models() -> list[dict]:
    return [
        {
            "role": cv.WRITER_ROLE,
            "name": cv.WRITER_MODEL,
            "digest": None,
            "digest_state": "unresolved",
        },
        {
            "role": cv.DEDUP_ROLE,
            "name": cv.DEDUP_MODEL,
            "digest": None,
            "digest_state": "unresolved",
        },
    ]


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


def _calls(scenarios: tuple[Scenario, ...]) -> list[dict]:
    planned = []
    for scenario in scenarios:
        prompt = f"plan-only task_id={scenario.task_id}"
        planned.append({"role": cv.WRITER_ROLE, "request": writer_request(prompt), "sent": False})
        planned.append(
            {"role": cv.DEDUP_ROLE, "request": embedding_request(scenario.task_id), "sent": False}
        )
    return planned


def _provenance(
    family, run_seed: int, produced_at: str | None, scenarios: tuple[Scenario, ...]
) -> dict:
    actors = actors_for(family.config_sha256)
    actors.extend(
        [
            {"role": cv.WRITER_ROLE, "name": cv.WRITER_MODEL, "digest": None},
            {"role": cv.DEDUP_ROLE, "name": cv.DEDUP_MODEL, "digest": None},
        ]
    )
    return {
        "produced_at": produced_at,
        "actors": actors,
        "lineage": {
            "run_seed": run_seed,
            "builder": cv.BUILDER_NAME,
            "config_sha256": family.config_sha256,
            "parent_ids": [],
            "scenario_ids": [item.scenario_id for item in scenarios],
        },
    }


def dry_run_plan(*, seed: int, count: int, produced_at: str | None = None) -> dict:
    """Describe the records a live run would build. ``network_calls`` stays zero."""

    if not _nonneg(seed):
        raise cv.FamilyError("seed", "seed must be a non-negative integer")
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
        "models": _models(),
        "provenance": _provenance(family, seed, produced_at, chosen),
        "scenarios": [_scenario_row(item, family, seed) for item in chosen],
        "planned_calls": _calls(chosen),
    }


bind_import_twin(__name__)
