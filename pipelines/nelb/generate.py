#!/usr/bin/env python3
"""Build designed NELB bridge pairs from the AST-extracted catalog.

Each record is a compact ``bridge_pair``: a lead language-view trajectory,
a companion trajectory, and a two-event spike list. This module does not
re-run CUBA LIF rasters and does not publish a raw round. Writers refuse an
existing destination and any path that names or aliases ``outputs/raw/``.
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
    ISOLATION,
    LINEAR_ISSUE,
    PROJECT_TRAINING_POLICY,
    QUOTA_PER_ROUND,
    RECORD_KIND,
    RUN_LABEL,
    SNN_TAGS,
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
RUN_FORMAT = "nelb-plants-run/2"

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


def _check_destination(out_dir: Path) -> None:
    refuse_vendor_paths((out_dir,))
    _exclusive_run.check_destination(_GUARDS, out_dir)


_GUARDS = _exclusive_run.Guards(refuse, refuse_when, is_under_raw)
_fsync_destination = _exclusive_run.fsync_destination


def _write_run(out_dir: Path, files: tuple[tuple[str, str], ...]) -> None:
    """Create ``out_dir`` and its files exclusively; unlink a partial tree."""

    _exclusive_run.write_run(_GUARDS, out_dir, files, fsync=_fsync_destination)


def _state(plant: cat.Plant, *, side: str) -> dict[str, Any]:
    suffix = "" if side == "t1" else "-exec"
    return {
        "sim_or_real": plant.sim_or_real,
        "domain": plant.domain or plant.reconstruction,
        "episode_id": f"{plant.record_id}{suffix}",
        "setting": plant.site or plant.record_id,
    }


def _proposed(plant: cat.Plant, *, side: str) -> dict[str, Any]:
    if side == "t1":
        summary = f"keep-or-raise at {plant.site or plant.record_id} on a vendor last-good"
        basis = f"{plant.reconstruction or plant.domain} vendor channel is the only SoT"
    else:
        summary = f"cheap hold after the lead {plant.lead_decision} at {plant.site}"
        basis = "the lead gate already fired, so a wider trip is cheaper"
    return {
        "action": "keep_or_raise" if side == "t1" else "widen_trip",
        "summary": summary,
        "basis_claimed": basis,
    }


def _rationale(plant: cat.Plant, *, side: str, decision: str) -> str:
    if side == "t1":
        return (
            f"A correct NELB gate starts from {plant.formula or plant.reconstruction}, "
            f"not a vendor last-good. Lead {decision} at {plant.site or plant.record_id}."
        )
    return (
        f"Companion {decision} on {plant.companion_key}: the extracted diagnosis "
        f"keeps {plant.reconstruction or plant.domain} as the live interlock."
    )


def _reward_components(success: bool, total: float) -> dict[str, Any]:
    return {
        "safety": 0.8 if success else -0.8,
        "verification": 0.4 if success else -0.3,
        "task_progress": 0.35 if success else 0.2,
        "total": total,
    }


def _traj_meta(plant: cat.Plant, *, side: str) -> dict[str, Any]:
    return {
        "factory": FACTORY,
        "round": plant.source_round,
        "generator": GENERATOR,
        "isolation": ISOLATION,
        "run": RUN_LABEL,
        "tags": ["bridge_pair", side, RECORD_KIND],
    }


def _traj(plant: cat.Plant, *, side: str, decision: str) -> dict[str, Any]:
    rationale = _rationale(plant, side=side, decision=decision)
    narrative = plant.goal
    total = 1.55
    success = True
    return {
        "id": f"{plant.record_id}-{side}",
        "state": _state(plant, side=side),
        "proposed_action": _proposed(plant, side=side),
        "safety_decision": {
            "decision": decision,
            "rationale": rationale,
            "evidence_checked": [plant.reconstruction or plant.domain or plant.record_id],
        },
        "executed_action": {
            "action": "hold_and_prove" if decision != "ACCEPT" else "accept_as_proposed",
        },
        "future_outcome": {
            "success": success,
            "narrative": narrative,
        },
        "reward_components": _reward_components(success, total),
        "meta": _traj_meta(plant, side=side),
    }


def _spikes(plant: cat.Plant) -> list[dict[str, Any]]:
    """Two authored events. Not a LIF raster and not copied from a mill loop."""

    return [
        {
            "t_rel_ms": 0.0,
            "channel": f"{plant.record_id}.recon",
            "amplitude": 1.0,
            "note": plant.reconstruction or plant.domain,
        },
        {
            "t_rel_ms": 1.3,
            "channel": f"{plant.record_id}.lock",
            "amplitude": 1.0,
            "note": plant.formula or plant.lead_decision,
        },
    ]


def record(plant: cat.Plant) -> dict[str, Any]:
    """One designed bridge pair. Does not publish a raw round."""

    lead = _traj(plant, side="t1", decision=plant.lead_decision)
    companion = _traj(plant, side="t2", decision=plant.companion_decision)
    return {
        "id": plant.record_id,
        "spike_events": _spikes(plant),
        "language_view": {
            "description": plant.goal,
            "trajectory": lead,
            plant.companion_key: companion,
        },
        "bridge_notes": {
            "reconstruction": plant.reconstruction,
            "formula": plant.formula,
            "why_high_value": plant.goal,
        },
        "meta": {
            "factory": FACTORY,
            "round": plant.source_round,
            "generator": GENERATOR,
            "isolation": ISOLATION,
            "kind": RECORD_KIND,
            "plant": plant.sim_or_real,
            "linear_issue": LINEAR_ISSUE,
            "intended_use": INTENDED_USE,
            "project_training_policy": PROJECT_TRAINING_POLICY,
            "run": RUN_LABEL,
            "snn_tags": list(SNN_TAGS),
            "nelb": {"snn_tags": list(SNN_TAGS)},
            "source_name": plant.source_name,
            "failure_mode": plant.reconstruction,
        },
    }


def notes_for(round_n: int, recs: list[dict[str, Any]], plants: tuple[cat.Plant, ...]) -> str:
    ids = [rec["id"] for rec in recs]
    lines = [
        f"# {FACTORY} — NOTES r{round_n}",
        "",
        f"Generator: {GENERATOR} · isolation: {ISOLATION} · quota: {QUOTA_PER_ROUND}",
        f"Linear: {LINEAR_ISSUE} · intended_use: {INTENDED_USE} · "
        f"project_training_policy: {PROJECT_TRAINING_POLICY}",
        "",
        "Construction: compact bridge_pair from the AST-extracted plant catalog. "
        "This CLI emits both trajectories into a brand-new destination and "
        "never writes outputs/raw/. No CUBA LIF loop is replayed.",
        "",
        "Records:",
        *[
            (
                f"- `{rec['id']}` site=`{plant.site or plant.record_id}` "
                f"recon=`{plant.reconstruction or plant.domain}` "
                f"lead=`{plant.lead_decision}` companion=`{plant.companion_decision}`"
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
    """Write one recovered triple into a new directory. Never touches raw."""

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
