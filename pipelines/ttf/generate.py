#!/usr/bin/env python3
"""Build designed TTF thalamic records from the AST-extracted catalog.

Each record carries the six thalamic keys from the committed identity slice.
This module does not publish a raw round. Writers refuse an existing
destination and any path that names or aliases ``outputs/raw/``.
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
)

if __package__ and __package__.startswith("pipelines."):
    from ..run_writer import exclusive_run as _exclusive_run
else:
    from run_writer import exclusive_run as _exclusive_run

BATCH_PREFIX = "batch-"
NOTES_PREFIX = "NOTES-"
MANIFEST_FILENAME = "MANIFEST.json"
RUN_FORMAT = "ttf-recover-run/1"

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
    slice_id: str
    out_dir: Path


def _check_destination(out_dir: Path) -> None:
    refuse_vendor_paths((out_dir,))
    _exclusive_run.check_destination(_GUARDS, out_dir)


_GUARDS = _exclusive_run.Guards(refuse, refuse_when, is_under_raw)
_fsync_destination = _exclusive_run.fsync_destination


def _write_run(out_dir: Path, files: tuple[tuple[str, str], ...]) -> None:
    """Create ``out_dir`` and its files exclusively; unlink a partial tree."""

    _exclusive_run.write_run(_GUARDS, out_dir, files, fsync=_fsync_destination)


def record(plant: cat.Plant, *, slice_id: str) -> dict[str, Any]:
    """One designed thalamic trajectory. Does not publish a raw round."""

    return {
        "id": plant.record_id,
        "state": {
            "sim_or_real": plant.sim_or_real,
            "domain": plant.domain,
            "episode_id": plant.record_id,
            "goal": plant.goal,
        },
        "proposed_action": {
            "name": plant.proposed_action,
            "action": plant.proposed_action,
        },
        "safety_decision": {
            "decision": plant.decision,
            "correctness": plant.correctness,
            "rationale": plant.rationale,
        },
        "executed_action": {
            "name": plant.executed_action,
            "action": plant.executed_action,
        },
        "future_outcome": {
            "summary": plant.outcome,
            "success": plant.correctness == "correct",
        },
        "reward_components": {
            "total": plant.reward_total,
            "notes": plant.reward_note,
        },
        "meta": {
            "factory": FACTORY,
            "round": slice_id,
            "generator": GENERATOR,
            "kind": RECORD_KIND,
            "plant": "designed",
            "linear_issue": LINEAR_ISSUE,
            "intended_use": INTENDED_USE,
            "project_training_policy": PROJECT_TRAINING_POLICY,
            "run": RUN_LABEL,
            "source_name": plant.source_name,
            "catalog_id": cat.CATALOG_ID,
            "title": plant.title,
        },
    }


def notes_for(
    slice_id: str,
    recs: list[dict[str, Any]],
    plants: tuple[cat.Plant, ...],
) -> str:
    ids = [rec["id"] for rec in recs]
    lines = [
        f"# {FACTORY} — NOTES {slice_id}",
        "",
        f"Generator: {GENERATOR} · slice: {slice_id} · quota: {QUOTA_PER_ROUND}",
        f"Linear: {LINEAR_ISSUE} · intended_use: {INTENDED_USE} · "
        f"project_training_policy: {PROJECT_TRAINING_POLICY}",
        "",
        "Construction: designed thalamic identities AST-extracted from "
        f"{plants[0].source_name if plants else 'catalog'}. This CLI emits "
        "records into a brand-new destination and never writes outputs/raw/.",
        "",
        "Records:",
        *[
            (
                f"- `{rec['id']}` domain=`{plant.domain}` "
                f"decision=`{plant.decision}` total=`{plant.reward_total}`"
            )
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
    """Write one recovered slice into a new directory. Never touches raw."""

    out_dir = Path(request.out_dir)
    slice_id = request.slice_id
    _check_destination(out_dir)
    plants = cat.plants_for_slice(slice_id)
    recs = [record(plant, slice_id=slice_id) for plant in plants]
    summary = {
        "format": RUN_FORMAT,
        "catalog_id": cat.CATALOG_ID,
        "factory": FACTORY,
        "slice": slice_id,
        "records": len(recs),
        "ids": [rec["id"] for rec in recs],
        "destination": str(out_dir),
    }
    _write_run(
        out_dir,
        (
            (
                f"{BATCH_PREFIX}{slice_id}.jsonl",
                "".join(_dump_line(rec) + "\n" for rec in recs),
            ),
            (
                f"{NOTES_PREFIX}{slice_id}.md",
                notes_for(slice_id, recs, plants),
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
