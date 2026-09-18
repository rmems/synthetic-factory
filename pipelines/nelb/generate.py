#!/usr/bin/env python3
"""Build designed NELB bridge pairs from the AST-extracted catalog.

Each record is a compact ``bridge_pair``: a lead language-view trajectory,
a companion trajectory, and a two-event spike list. This module does not
re-run CUBA LIF rasters and does not publish a raw round. Writers refuse an
existing destination and any path that names or aliases ``outputs/raw/``.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import catalog as cat
from ._contract import (
    FACTORY,
    FINDING_DESTINATION_EXISTS,
    FINDING_DESTINATION_UNDER_RAW,
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
    refuse_when(
        is_under_raw(out_dir),
        FINDING_DESTINATION_UNDER_RAW,
        f"{out_dir} names or aliases the raw tree",
    )
    refuse_when(out_dir.exists(), FINDING_DESTINATION_EXISTS, f"{out_dir} already exists")


@dataclass(frozen=True)
class _CreatedFile:
    """A file this invocation created, addressed by its pinned parent."""

    parent_fd: int
    name: str


def _opened_path(fd: int, fallback: Path) -> Path:
    try:
        return Path(os.readlink(f"/proc/self/fd/{fd}"))
    except OSError:
        return fallback


def _refuse_raw_path(path: Path, origin: Path) -> None:
    refuse_when(
        is_under_raw(path),
        FINDING_DESTINATION_UNDER_RAW,
        f"{origin} names or aliases the raw tree",
    )


def _open_destination_parent(path: Path) -> int:
    flags = os.O_RDONLY | os.O_DIRECTORY | getattr(os, "O_NOFOLLOW", 0)
    return os.open(path.parent, flags)


def _refuse_opened_parent(parent_fd: int, destination: Path) -> None:
    opened = _opened_path(parent_fd, destination.parent)
    _refuse_raw_path(opened, destination)
    _refuse_raw_path(opened / destination.name, destination)


def _create_exclusive_file(
    parent_fd: int, name: str, payload: str, created: list[_CreatedFile]
) -> None:
    descriptor = os.open(
        name,
        os.O_WRONLY | os.O_CREAT | os.O_EXCL,
        0o644,
        dir_fd=parent_fd,
    )
    created.append(_CreatedFile(parent_fd, name))
    with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())


def _fsync_destination(dest_fd: int, parent_fd: int) -> None:
    os.fsync(dest_fd)
    os.fsync(parent_fd)


def _unlink_created(created: list[_CreatedFile]) -> None:
    for entry in created:
        try:
            os.unlink(entry.name, dir_fd=entry.parent_fd)
        except FileNotFoundError:
            pass


def _rmdir_created(parent_fd: int, name: str) -> None:
    try:
        os.rmdir(name, dir_fd=parent_fd)
    except OSError:
        pass


def _write_run(out_dir: Path, files: tuple[tuple[str, str], ...]) -> None:
    """Create ``out_dir`` and its files exclusively; unlink a partial tree."""

    out_dir.parent.mkdir(parents=True, exist_ok=True)
    parent_fd = _open_destination_parent(out_dir)
    dest_fd = -1
    created: list[_CreatedFile] = []
    created_dir = False
    try:
        _refuse_opened_parent(parent_fd, out_dir)
        try:
            os.mkdir(out_dir.name, dir_fd=parent_fd)
        except FileExistsError:
            refuse(FINDING_DESTINATION_EXISTS, f"{out_dir} already exists")
        created_dir = True
        dest_fd = os.open(
            out_dir.name,
            os.O_RDONLY | os.O_DIRECTORY | getattr(os, "O_NOFOLLOW", 0),
            dir_fd=parent_fd,
        )
        _refuse_raw_path(_opened_path(dest_fd, out_dir), out_dir)
        for name, payload in files:
            _create_exclusive_file(dest_fd, name, payload, created)
        _fsync_destination(dest_fd, parent_fd)
    except BaseException:
        # Not `Exception`: a Ctrl-C during the payload write or the fsync
        # would otherwise leave a half-written destination behind, and the
        # next run refuses to overwrite it.
        _unlink_created(created)
        if created_dir:
            _rmdir_created(parent_fd, out_dir.name)
        raise
    finally:
        if dest_fd >= 0:
            os.close(dest_fd)
        os.close(parent_fd)


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


def _traj(plant: cat.Plant, *, side: str, decision: str) -> dict[str, Any]:
    if side == "t1":
        rationale = (
            f"A correct NELB gate starts from {plant.formula or plant.reconstruction}, "
            f"not a vendor last-good. Lead {decision} at {plant.site or plant.record_id}."
        )
    else:
        rationale = (
            f"Companion {decision} on {plant.companion_key}: the extracted diagnosis "
            f"keeps {plant.reconstruction or plant.domain} as the live interlock."
        )
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
        "reward_components": {
            "safety": 0.8 if success else -0.8,
            "verification": 0.4 if success else -0.3,
            "task_progress": 0.35 if success else 0.2,
            "total": total,
        },
        "meta": {
            "factory": FACTORY,
            "round": plant.source_round,
            "generator": GENERATOR,
            "isolation": ISOLATION,
            "run": RUN_LABEL,
            "tags": ["bridge_pair", side, RECORD_KIND],
        },
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
