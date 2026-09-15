#!/usr/bin/env python3
"""Build designed TTF thalamic records from the AST-extracted catalog.

Each record carries the six thalamic keys from the r02c identity slice.
This module does not publish a raw round. Writers refuse an existing
destination and any path that names or aliases ``outputs/raw/``.
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
    LINEAR_ISSUE,
    PROJECT_TRAINING_POLICY,
    QUOTA_PER_ROUND,
    RECORD_KIND,
    RUN_LABEL,
    SLICE_ID,
    bind_import_twin,
    dumps_exact_json,
    is_under_raw,
    refuse,
    refuse_when,
    refuse_vendor_paths,
    require_round,
)

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


def record(plant: cat.Plant) -> dict[str, Any]:
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
            "round": SLICE_ID,
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


def notes_for(round_n: int, recs: list[dict[str, Any]], plants: tuple[cat.Plant, ...]) -> str:
    ids = [rec["id"] for rec in recs]
    lines = [
        f"# {FACTORY} — NOTES {SLICE_ID}",
        "",
        f"Generator: {GENERATOR} · slice: {SLICE_ID} · quota: {QUOTA_PER_ROUND}",
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
    _check_destination(out_dir)
    plants = cat.plants_for_round(require_round(request.round_n))
    recs = [record(plant) for plant in plants]
    summary = {
        "format": RUN_FORMAT,
        "catalog_id": cat.CATALOG_ID,
        "factory": FACTORY,
        "round": request.round_n,
        "slice": SLICE_ID,
        "records": len(recs),
        "ids": [rec["id"] for rec in recs],
        "destination": str(out_dir),
    }
    _write_run(
        out_dir,
        (
            (
                f"{BATCH_PREFIX}{SLICE_ID}.jsonl",
                "".join(_dump_line(rec) + "\n" for rec in recs),
            ),
            (
                f"{NOTES_PREFIX}{SLICE_ID}.md",
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
