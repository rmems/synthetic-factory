#!/usr/bin/env python3
"""Build designed PKG episode pairs from the AST-extracted catalog.

Each round emits one success attestation episode and one leftover-fail
episode (quota 2). This module does not publish a raw round. Writers refuse
an existing destination and any path that names or aliases ``outputs/raw/``.
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
    FINDING_PAIR_INVALID,
    GENERATOR,
    INTENDED_USE,
    PROJECT_TRAINING_POLICY,
    QUOTA_PER_ROUND,
    RECORD_KIND,
    bind_import_twin,
    dumps_exact_json,
    is_under_raw,
    refuse,
    refuse_first,
    refuse_vendor_paths,
    refuse_when,
    require_round,
)

BATCH_PREFIX = "batch-r"
NOTES_PREFIX = "NOTES-r"
MANIFEST_FILENAME = "MANIFEST.json"
RUN_FORMAT = "pkg-r163-run/1"
BANNED_KEYS = ("thought", "chain_of_thought", "scratch", "inner_monologue")
STEP_PREFIXES = ("Plan:", "Observation:", "Reflection:")
OK_REWARD = {
    "success": True,
    "sign_fails": 1,
    "plan_changes": 1,
    "cost_steps": 12,
}
FAIL_REWARD = {
    "success": False,
    "sign_fails": 1,
    "plan_changes": 1,
    "cost_steps": 12,
}

__all__ = [
    "BATCH_PREFIX",
    "MANIFEST_FILENAME",
    "NOTES_PREFIX",
    "RUN_FORMAT",
    "RunRequest",
    "assert_clean",
    "episode",
    "notes_for",
    "run",
]


@dataclass(frozen=True)
class RunRequest:
    round_n: int
    out_dir: Path


def assert_clean(obj: Any, path: str = "") -> None:
    if isinstance(obj, dict):
        for key, val in obj.items():
            refuse_when(key in BANNED_KEYS, FINDING_PAIR_INVALID, f"banned key {key} at {path}")
            refuse_when(
                key == "sim_or_real" and val == "real",
                FINDING_PAIR_INVALID,
                f"sim_or_real real at {path}",
            )
            refuse_when(key == "spike_events", FINDING_PAIR_INVALID, f"spike_events at {path}")
            assert_clean(val, f"{path}.{key}")
    elif isinstance(obj, list):
        for index, item in enumerate(obj):
            assert_clean(item, f"{path}[{index}]")


def designed_goal(plant: cat.Plant) -> str:
    if plant.goal.strip():
        return plant.goal
    leftover = f" Leave leftover {plant.leftover}." if plant.leftover else ""
    return f"Ship {plant.plant} so {plant.seed}.{leftover}"


def designed_plan(plant: cat.Plant) -> str:
    if plant.plan.strip():
        return plant.plan
    return f"{plant.first}; then {plant.change}"


def designed_outcome(plant: cat.Plant) -> str:
    return plant.term


def _step(n: int, decision_basis: str, observation: str, reflection: str) -> dict[str, Any]:
    refuse_first(
        (
            (
                not decision_basis.startswith(STEP_PREFIXES),
                FINDING_PAIR_INVALID,
                f"step {n} decision_basis prefix: {decision_basis!r}",
            ),
            (
                not observation.strip() or not reflection.strip(),
                FINDING_PAIR_INVALID,
                f"step {n} empty observation/reflection",
            ),
        )
    )
    return {
        "n": n,
        "decision_basis": decision_basis,
        "observation": observation,
        "reflection": reflection,
    }


def _steps(plant: cat.Plant) -> list[dict[str, Any]]:
    leftover = plant.leftover or plant.term
    return [
        _step(1, "Plan: inspect published artifact and attestation before rewriting identity.",
              f"{plant.plant} seed={plant.seed}", "Inspect first; do not spend a leftover pointer."),
        _step(2, "Observation: plant identity and seed are designed, not measured.",
              plant.seed, "Designed seed is the load-bearing mismatch."),
        _step(3, "Observation: leftover consumer pointer is still live.",
              leftover, "A leftover pointer is not a lockfile pin."),
        _step(4, "Plan: first apply follows the extracted first-apply token.",
              plant.first, "First apply is expected to fail closed."),
        _step(5, "Observation: first apply failed on the designed identity mismatch.",
              plant.first, "Do not unpublish or overwrite the same version."),
        _step(6, "Observation: published bytes are still GET-able after the refused replace.",
              leftover, "Immutability of the published artifact holds."),
        _step(7, "Reflection: plan change uses the extracted change token.",
              plant.change, "Retarget identity; leave the leftover consumer."),
        _step(8, "Observation: policy or publisher retargeted to the live identity.",
              plant.change, "Next publish/attest uses the corrected identity."),
        _step(9, "Observation: designed verify after the plan change.",
              plant.term, "Terminal is designed, not a live registry read."),
        _step(10, "Observation: leftover residual is still recorded.",
              leftover, "Residual leftover is in-scope for the fail arm."),
        _step(11, "Plan: stop without mutating the already-published version.",
              plant.slug, "Next version only; no yank of the leftover."),
        _step(12, "Reflection: terminal outcome is the extracted term.",
              plant.term, "Designed pair; demoted digest/lock-yank twins stay out."),
    ]


def episode(plant: cat.Plant) -> dict[str, Any]:
    """One designed episode. Does not publish a raw round."""

    rec = {
        "id": plant.record_id,
        "goal": designed_goal(plant),
        "plan": designed_plan(plant),
        "steps": _steps(plant),
        "outcome": designed_outcome(plant),
        "reward": dict(OK_REWARD if plant.role == "ok" else FAIL_REWARD),
        "meta": {
            "factory": FACTORY,
            "round": plant.source_round,
            "generator": GENERATOR,
            "kind": RECORD_KIND,
            "role": plant.role,
            "builder": plant.kind,
            "plant": plant.plant,
            "seed": plant.seed,
            "designed": True,
            "intended_use": INTENDED_USE,
            "project_training_policy": PROJECT_TRAINING_POLICY,
            "source_name": plant.source_name,
        },
    }
    refuse_when(not rec["goal"].strip(), FINDING_PAIR_INVALID, f"{plant.record_id} missing goal")
    refuse_when(len(rec["steps"]) != 12, FINDING_PAIR_INVALID, f"{plant.record_id} needs 12 steps")
    assert_clean(rec)
    return rec


def notes_for(round_n: int, recs: list[dict[str, Any]], plants: tuple[cat.Plant, ...]) -> str:
    lines = [
        f"# {FACTORY} — NOTES r{round_n}",
        "",
        f"Generator: {GENERATOR} · quota: {QUOTA_PER_ROUND} designed episodes.",
        f"intended_use: {INTENDED_USE} · project_training_policy: {PROJECT_TRAINING_POLICY}",
        "",
        "Pkg catalog r163–r196 (r163/r181 mill extracts). Avoided demoted",
        "r98–r162 digest/lock-yank, attest-wave, leftover3, licrep, and pkgs.",
        "This CLI never writes",
        "outputs/raw/ and does not vendor mill or loop scripts.",
        "",
        "Records:",
        *[
            f"- `{rec['id']}` role={plant.role} kind={plant.kind} seed=`{plant.seed}`"
            for rec, plant in zip(recs, plants, strict=True)
        ],
        "",
        f"IDs: {[rec['id'] for rec in recs]}",
        "",
    ]
    return "\n".join(lines)


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
        _unlink_created(created)
        if created_dir:
            _rmdir_created(parent_fd, out_dir.name)
        raise
    finally:
        if dest_fd >= 0:
            os.close(dest_fd)
        os.close(parent_fd)


def _dump_line(record: dict[str, Any]) -> str:
    return dumps_exact_json(record, ensure_ascii=False, sort_keys=False)


def run(request: RunRequest) -> dict[str, Any]:
    """Write one recovered pair into a new directory. Never touches raw."""

    out_dir = Path(request.out_dir)
    _check_destination(out_dir)
    plants = cat.plants_for_round(require_round(request.round_n))
    recs = [episode(plant) for plant in plants]
    refuse_when(
        recs[0]["reward"]["success"] is not True or recs[1]["reward"]["success"] is not False,
        FINDING_PAIR_INVALID,
        "pair must be success then leftover-fail",
    )
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
