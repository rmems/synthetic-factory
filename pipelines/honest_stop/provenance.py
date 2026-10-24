"""Provenance for a builder-produced record: actors, digest, seed, lineage."""

from __future__ import annotations

from . import vocabulary as cv
from ._contract import bind_import_twin
from .scenarios import Scenario

__all__ = ["actors_for", "lineage_for"]


def actors_for(digest: str) -> list[dict[str, str]]:
    """The scenario builder is the actor that produced an infrastructure record."""

    return [
        {"role": cv.BUILDER_ROLE, "name": cv.BUILDER_NAME, "digest": digest},
    ]


def lineage_for(scenario: Scenario, *, run_seed: int, digest: str) -> dict:
    """Lineage names the scenario, both seeds, and the family-file digest."""

    return {
        "scenario_id": scenario.scenario_id,
        "seed": scenario.seed,
        "run_seed": run_seed,
        "builder": cv.BUILDER_NAME,
        "config_sha256": digest,
        "parent_ids": [],
    }


bind_import_twin(__name__)
