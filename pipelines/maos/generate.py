#!/usr/bin/env python3
"""Replay compact MAOS identities into a brand-new destination.

Each record is a catalog replay of one recovered round identity. This module
does not publish a raw round and does not reconstruct rasters. Writers refuse
an existing destination and any path that names or aliases ``outputs/raw/``.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import catalog as cat
from ._contract import (
    FACTORY,
    GENERATOR,
    INTENDED_USE,
    LINEAR_ISSUE,
    PROJECT_TRAINING_POLICY,
    QUOTA_PER_ROUND,
    RECORD_KIND,
    RUN_LABEL,
    bind_import_twin,
    dumps_exact_json,
    is_under_raw,
    refuse,
    refuse_when,
    refuse_vendor_paths,
    require_round,
)

if __package__ and __package__.startswith("pipelines."):
    from ..run_writer import exclusive_run as _exclusive_run
else:
    from run_writer import exclusive_run as _exclusive_run

BATCH_PREFIX = "batch-r"
NOTES_PREFIX = "NOTES-r"
MANIFEST_FILENAME = "MANIFEST.json"
RUN_FORMAT = "maos-recover-run/1"

__all__ = [
    "BATCH_PREFIX",
    "MANIFEST_FILENAME",
    "NOTES_PREFIX",
    "RUN_FORMAT",
    "RunRequest",
    "notes_for",
    "record",
    "run",
]


@dataclass(frozen=True)
class RunRequest:
    round_n: int
    out_dir: Path


_check_destination, _write_run, _fsync_destination = _exclusive_run.bind(
    globals(), _exclusive_run.Guards(refuse, refuse_when, is_under_raw), refuse_vendor_paths
)


def record(plant: cat.Plant) -> dict[str, Any]:
    """One compact catalog-replay identity. Does not publish a raw round."""

    payload = {
        "id": plant.record_id,
        "title": plant.title,
        "state": {
            "sim_or_real": plant.sim_or_real,
            "domain": plant.domain,
            "scenario_name": plant.scenario,
        },
        "safety_decision": {
            "decision": plant.decision,
            "correctness": plant.decision_correctness,
        },
        "meta": {
            "factory": FACTORY,
            "round": plant.source_round,
            "generator": GENERATOR,
            "kind": RECORD_KIND,
            "run": RUN_LABEL,
            "linear_issue": LINEAR_ISSUE,
            "intended_use": INTENDED_USE,
            "project_training_policy": PROJECT_TRAINING_POLICY,
            "catalog_id": cat.CATALOG_ID,
            "spike_events": plant.spike_events,
            "raster_spikes": plant.raster_spikes,
            "source_key": plant.source_key,
        },
    }
    return payload


def notes_for(round_n: int, recs: list[dict[str, Any]], plants: tuple[cat.Plant, ...]) -> str:
    ids = [rec["id"] for rec in recs]
    lines = [
        f"# {FACTORY} — NOTES r{round_n}",
        "",
        f"Generator: {GENERATOR} · quota: {QUOTA_PER_ROUND}",
        f"Linear: {LINEAR_ISSUE} · intended_use: {INTENDED_USE} · "
        f"project_training_policy: {PROJECT_TRAINING_POLICY}",
        "",
        "Construction: catalog replay of one AST-extracted MAOS identity. "
        "This CLI never writes outputs/raw/ and never vendors mill or loop scripts.",
        "",
        "Records:",
        *[
            f"- `{rec['id']}` scenario=`{plant.scenario}` domain=`{plant.domain}`"
            for rec, plant in zip(recs, plants, strict=True)
        ],
        "",
        f"IDs: {ids}",
        "",
    ]
    return "\n".join(lines)


def _dump_line(payload: dict[str, Any]) -> str:
    return dumps_exact_json(payload, ensure_ascii=False, sort_keys=False)


def run(request: RunRequest) -> dict[str, Any]:
    """Write one recovered identity into a new directory. Never touches raw."""

    out_dir = Path(request.out_dir)
    _check_destination(out_dir)
    plants = cat.plants_for_round(require_round(request.round_n))
    recs = [record(plant) for plant in plants]
    summary = {
        "format": RUN_FORMAT,
        "catalog_id": cat.CATALOG_ID,
        "factory": FACTORY,
        "round": request.round_n,
        "records": len(recs),
        "ids": [rec["id"] for rec in recs],
        "destination": str(out_dir),
    }
    _write_run(
        out_dir,
        (
            (
                f"{BATCH_PREFIX}{request.round_n:02d}.jsonl",
                "".join(_dump_line(rec) + "\n" for rec in recs),
            ),
            (
                f"{NOTES_PREFIX}{request.round_n:02d}.md",
                notes_for(request.round_n, recs, plants),
            ),
            (
                MANIFEST_FILENAME,
                dumps_exact_json(summary, ensure_ascii=False, indent=2, sort_keys=True)
                + "\n",
            ),
        ),
    )
    return summary


bind_import_twin(__name__)
