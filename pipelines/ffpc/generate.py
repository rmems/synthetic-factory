#!/usr/bin/env python3
"""Build designed FFPC preference pairs from the AST-extracted catalog.

Each pair keeps the same designed state and proposed action on both arms.
The rejected arm ACCEPTs on a proxy certificate; the chosen arm MODIFYs or
REJECTs from the extracted diagnosis. This module does not publish a raw
round. Writers refuse an existing destination and any path that names or
aliases ``outputs/raw/``.
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
RUN_FORMAT = "ffpc-recover-run/1"
CHOSEN_VERBS = ("MODIFY", "REJECT", "MODIFY")

__all__ = [
    "BATCH_PREFIX",
    "MANIFEST_FILENAME",
    "NOTES_PREFIX",
    "RUN_FORMAT",
    "RunRequest",
    "notes_for",
    "pair",
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


def _state(plant: cat.Plant) -> dict[str, Any]:
    domain = plant.domain or plant.failure_mode
    site = plant.site or plant.record_id
    return {
        "sim_or_real": plant.sim_or_real,
        "domain": domain,
        "episode_id": plant.record_id,
        "environment": {"site": site},
    }


def _decision_basis(plant: cat.Plant) -> str:
    return plant.failure_mode or plant.domain or plant.record_id


def _proposed(plant: cat.Plant) -> dict[str, Any]:
    return {
        "action": "keep_or_raise",
        "decision_basis": _decision_basis(plant),
        "arguments": {"site": plant.site or plant.record_id},
    }


def _reward_components(success: bool, total: float) -> dict[str, Any]:
    return {
        "safety": 0.8 if success else -0.8,
        "verification": 0.4 if success else -0.3,
        "task_progress": 0.35 if success else 0.2,
        "total": total,
    }


def _arm(
    plant: cat.Plant,
    *,
    side: str,
    decision: str,
    rationale: str,
    success: bool,
    total: float,
) -> dict[str, Any]:
    return {
        "id": f"{plant.record_id}-{side}",
        "state": _state(plant),
        "proposed_action": _proposed(plant),
        "safety_decision": {
            "decision": decision,
            "rationale": rationale,
            "evidence_checked": [_decision_basis(plant)],
        },
        "executed_action": {
            "action": "hold_and_prove" if side == "chosen" else "accept_as_proposed",
        },
        "future_outcome": {
            "success": success,
            "narrative": plant.root_cause or plant.goal or plant.domain,
        },
        "reward_components": _reward_components(success, total),
        "meta": {
            "factory": FACTORY,
            "round": plant.source_round,
            "generator": GENERATOR,
            "isolation": ISOLATION,
            "run": RUN_LABEL,
            "tags": ["preference_pair", side, RECORD_KIND],
        },
    }


def _chosen_rationale(plant: cat.Plant) -> str:
    return (
        f"A correct gate starts from the live trip, not {plant.failure_mode or 'a proxy'}. "
        f"{plant.root_cause or plant.goal or plant.domain}"
    )


def _rejected_rationale(plant: cat.Plant) -> str:
    return (
        f"The gate spent {plant.failure_mode or 'a proxy certificate'} as live process health "
        "and ACCEPTed the proposed keep-or-raise."
    )


def _critique(plant: cat.Plant, verb: str) -> str:
    return (
        f"Same designed state and proposed action on {plant.record_id}. "
        f"Rejected ACCEPTs because {plant.failure_mode or plant.domain}. "
        f"Chosen {verb}s from the extracted diagnosis. Isolation is {ISOLATION}."
    )


def _pair_goal(plant: cat.Plant) -> str:
    return plant.goal or (
        f"Gate the keep-or-raise at {plant.site or plant.record_id} "
        f"without spending a proxy certificate as a live trip."
    )


def _pair_meta(plant: cat.Plant) -> dict[str, Any]:
    return {
        "factory": FACTORY,
        "round": plant.source_round,
        "generator": GENERATOR,
        "isolation": ISOLATION,
        "kind": RECORD_KIND,
        "plant": "designed",
        "linear_issue": LINEAR_ISSUE,
        "intended_use": INTENDED_USE,
        "project_training_policy": PROJECT_TRAINING_POLICY,
        "run": RUN_LABEL,
        "sessions": {"a": "rejected+diagnosis", "b": "chosen from diagnosis only"},
        "failure_mode": plant.failure_mode,
        "source_name": plant.source_name,
    }


def pair(plant: cat.Plant) -> dict[str, Any]:
    """One designed same-state preference pair. Does not publish a raw round."""

    verb = CHOSEN_VERBS[plant.index - 1]
    chosen_rationale = _chosen_rationale(plant)
    rejected_rationale = _rejected_rationale(plant)
    critique = _critique(plant, verb)
    chosen_total = 1.55
    rejected_total = -0.9
    return {
        "id": plant.record_id,
        "goal": _pair_goal(plant),
        "chosen": _arm(
            plant,
            side="chosen",
            decision=verb,
            rationale=chosen_rationale,
            success=True,
            total=chosen_total,
        ),
        "rejected": _arm(
            plant,
            side="rejected",
            decision="ACCEPT",
            rationale=rejected_rationale,
            success=False,
            total=rejected_total,
        ),
        "critique": critique,
        "reward_delta": {
            "safety": 1.6,
            "verification": 0.7,
            "task_progress": 0.15,
            "total": 2.45,
        },
        "meta": _pair_meta(plant),
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
        "Construction: same-state preference pair. Session A writes rejected + diagnosis; "
        "Session B writes chosen from the diagnosis only. This CLI emits both arms into a "
        "brand-new destination and never writes outputs/raw/.",
        "",
        "Records:",
        *[
            (
                f"- `{rec['id']}` site=`{plant.site or plant.record_id}` "
                f"mode=`{plant.failure_mode or plant.domain}`"
            )
            for rec, plant in zip(recs, plants, strict=True)
        ],
        "",
        f"IDs: {ids}",
        "",
    ]
    return "\n".join(lines)


def _dump_line(record: dict[str, Any]) -> str:
    return dumps_exact_json(record, ensure_ascii=False, sort_keys=False)


def run(request: RunRequest) -> dict[str, Any]:
    """Write one recovered triple into a new directory. Never touches raw."""

    out_dir = Path(request.out_dir)
    _check_destination(out_dir)
    plants = cat.plants_for_round(require_round(request.round_n))
    recs = [pair(plant) for plant in plants]
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
