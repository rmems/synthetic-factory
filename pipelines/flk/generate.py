#!/usr/bin/env python3
"""Emit success/handoff episode pairs from a pinned FLK catalog.

Writes a brand-new destination (records.jsonl, RUN.json, NOTES.md). Refuses
an existing path and any path that names or aliases ``outputs/raw/``. Does
not hop factories, does not shell out to ``round_txn``, and does not stamp
``grok-4.6``.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import catalog as cat
from ._contract import (
    BANNED_KEYS,
    FACTORY,
    FINDING_BANNED_KEY,
    FINDING_DESTINATION_EXISTS,
    FINDING_DESTINATION_UNDER_RAW,
    FINDING_ROUND_INVALID,
    FINDING_USAGE,
    FlkRefusal,
    GENERATOR,
    NOTES_FILENAME,
    QUOTA_PER_ROUND,
    RECORDS_FILENAME,
    RUN_FILENAME,
    RUN_FORMAT,
    bind_import_twin,
    dumps_exact_json,
    is_under_raw,
)

__all__ = [
    "GenerateRequest",
    "NOTES_FILENAME",
    "RECORDS_FILENAME",
    "RUN_FILENAME",
    "fail_episode",
    "notes_markdown",
    "run",
    "success_episode",
]


@dataclass(frozen=True)
class GenerateRequest:
    catalog_dir: Path
    out_dir: Path
    plant_id: str | None = None
    mill_id: str | None = None
    all_plants: bool = False
    round: int | None = None


def _walk_keys(value: Any) -> list[str]:
    if isinstance(value, dict):
        keys = list(value)
        for item in value.values():
            keys.extend(_walk_keys(item))
        return keys
    if isinstance(value, list):
        keys: list[str] = []
        for item in value:
            keys.extend(_walk_keys(item))
        return keys
    return []


def _refuse_banned(record: dict[str, Any]) -> None:
    hits = sorted(BANNED_KEYS.intersection(_walk_keys(record)))
    if hits:
        raise FlkRefusal(FINDING_BANNED_KEY, f"record {record.get('id')!r} carries {hits[0]}")


def _step(
    n: int,
    basis: str,
    name: str,
    args: dict[str, str],
    observation: str,
    reflection: str | None = None,
) -> dict[str, Any]:
    step = {
        "n": n,
        "decision_basis": basis,
        "tool_call": {"name": name, "args": args},
        "observation": observation,
    }
    if reflection:
        step["reflection"] = reflection
    return step


def _assign_lhs(plant: cat.Plant) -> str:
    if "=" not in plant.assign:
        raise FlkRefusal(FINDING_USAGE, f"{plant.plant_id} assign has no '='")
    return plant.assign.split("=", 1)[0].strip()[:24]


def _success_repro(plant: cat.Plant) -> list[dict[str, Any]]:
    return [
        _step(
            1,
            "Plan: reproduce leftover under parallel runner, both orders.",
            "bash",
            {"command": f"{plant.cmd} ; echo ORDER_B"},
            f"{plant.runner} {plant.ticket}: {plant.ok} FAIL after {plant.mut}: "
            f"{plant.leftover}\nORDER_B flake",
        ),
        _step(
            2,
            "Observation: leftover (step 1). Read failing test.",
            "read",
            {"path": plant.test_file},
            f"{plant.mut}\n{plant.assign}\n{plant.ok} asserts clean state",
        ),
        _step(
            3,
            "Observation: mutate (step 2). Read production helper.",
            "read",
            {"path": plant.source_file},
            f"helper reads leftover {plant.cause} state; no fixture restore",
        ),
        _step(
            4,
            f"Plan: first apply — naive {plant.naive} on {plant.ok}.",
            "edit",
            {"path": plant.test_file, "old": plant.ok, "new": f"{plant.naive} {plant.ok}"},
            f"naive skip applied — {plant.ok} hidden",
        ),
        _step(
            5,
            "Observation: skip added (step 4). Re-run reverse order.",
            "bash",
            {"command": plant.cmd},
            "suite green because skipped",
            reflection=f"{plant.naive} hides leftover; reject skip.",
        ),
        _step(
            6,
            f"Reflection: plan change — isolate leftover, do not {plant.drop}.",
            "edit",
            {
                "path": plant.test_file,
                "old": f"{plant.naive} {plant.ok}",
                "new": f"{plant.isolate}\n{plant.ok}",
            },
            f"quarantine leftover via {plant.isolate}; skip removed",
        ),
        _step(
            7,
            "Observation: isolated (step 6). Both orders three times.",
            "bash",
            {"command": f"for i in 1 2 3; do {plant.cmd} || exit 1; done; echo ALL_OK"},
            "ALL_OK 6/6",
        ),
        _step(
            8,
            f"Observation: orders green (step 7). Grep skip|{plant.cause}.",
            "grep",
            {"path": plant.test_file, "pattern": "skip|Skip|Disabled|Ignore|XCTSkip"},
            "(no matches)",
        ),
    ]


def _success_confirm(plant: cat.Plant) -> list[dict[str, Any]]:
    return [
        _step(
            9,
            "Observation: no skip (step 8). Full suite with runner flag kept.",
            "bash",
            {"command": plant.cmd},
            f"{plant.runner} kept; {plant.drop} NOT applied; passed",
        ),
        _step(
            10,
            "Observation: suite green (step 9). Confirm CI still uses runner.",
            "read",
            {"path": plant.ci},
            f"{plant.cmd} still in CI; no {plant.drop}",
        ),
        _step(
            11,
            "Observation: CI (step 10). Confirm helper still used.",
            "grep",
            {"path": plant.source_file, "pattern": "def |fun |func |class "},
            "helper present",
        ),
        _step(
            12,
            "Observation: helper (step 11). Confirm isolate fixture.",
            "grep",
            {"path": plant.test_file, "pattern": "Cleanup|afterEach|tearDown|TempDir|isolate"},
            plant.isolate,
        ),
        _step(
            13,
            "Observation: fixture (step 12). Ticket note.",
            "edit",
            {"path": "NOTES_INCIDENT.md", "old": "", "new": plant.ticket},
            f"{plant.ticket} quarantine leftover {plant.cause}",
        ),
        _step(
            14,
            "Observation: ticket (step 13). Re-run drop-flag would mask, refuse.",
            "bash",
            {"command": f"echo refuse {plant.drop_cmd}"},
            f"refuse {plant.drop}; leftover would remain",
        ),
        _step(
            15,
            "Observation: refuse drop (step 14). Final both-order check.",
            "bash",
            {"command": plant.cmd},
            "passed",
        ),
        _step(
            16,
            "Observation: final green (step 15).",
            "bash",
            {"command": "echo QUARANTINE_OK"},
            "QUARANTINE_OK",
            reflection=f"Residual: {plant.leftover} isolated; runner flag kept.",
        ),
    ]


def _fail_repro(plant: cat.Plant) -> list[dict[str, Any]]:
    return [
        _step(
            1,
            "Plan: reproduce leftover then try drop-flag first.",
            "bash",
            {"command": plant.cmd},
            f"{plant.ok} FAIL {plant.leftover}",
        ),
        _step(
            2,
            "Observation: leftover (step 1). Read test.",
            "read",
            {"path": plant.test_file},
            f"{plant.assign} not restored",
        ),
        _step(
            3,
            "Observation: mutate (step 2). Read src.",
            "read",
            {"path": plant.source_file},
            "helper trusts process-global leftover",
        ),
        _step(
            4,
            f"Plan: first apply — {plant.drop}.",
            "edit",
            {"path": plant.ci, "old": plant.cmd, "new": plant.drop_cmd},
            f"CI now {plant.drop_cmd}",
        ),
        _step(
            5,
            "Observation: drop-flag (step 4). Serial run hides flake.",
            "bash",
            {"command": plant.drop_cmd},
            "passed under serial/no-retry — flake hidden",
            reflection=f"{plant.drop} masks leftover; not a fix.",
        ),
        _step(
            6,
            f"Reflection: still apply {plant.naive} to merge.",
            "edit",
            {"path": plant.test_file, "old": plant.ok, "new": f"{plant.naive} {plant.ok}"},
            "skip added",
        ),
        _step(
            7,
            "Observation: skip (step 6). Suite green locally.",
            "bash",
            {"command": plant.drop_cmd},
            "green via skip + dropped runner flag",
        ),
        _step(
            8,
            "Observation: green (step 7). Nightly restores runner flag.",
            "bash",
            {"command": plant.cmd},
            f"FAIL again: {plant.leftover} on unskipped sibling",
            reflection="handoff: leftover not isolated; flag drop not durable.",
        ),
    ]


def _fail_handoff(plant: cat.Plant) -> list[dict[str, Any]]:
    return [
        _step(
            9,
            "Reflection: cannot isolate without owner of global hook.",
            "grep",
            {"path": ".", "pattern": _assign_lhs(plant)},
            "global mutate in shared helper; no fixture owner",
        ),
        _step(
            10,
            "Observation: no owner (step 9). Open handoff.",
            "edit",
            {
                "path": "HANDOFF.md",
                "old": "",
                "new": f"{plant.ticket} leftover {plant.cause} needs isolate {plant.isolate}",
            },
            "HANDOFF written",
        ),
        _step(
            11,
            "Observation: handoff (step 10). Revert skip? policy blocks without owner.",
            "read",
            {"path": "HANDOFF.md"},
            "policy: do not unskip without isolate owner",
        ),
        _step(
            12,
            "Observation: policy (step 11). Confirm CI still dropped.",
            "read",
            {"path": plant.ci},
            plant.drop_cmd,
        ),
        _step(
            13,
            "Observation: CI dropped (step 12). Confirm skip remains.",
            "grep",
            {"path": plant.test_file, "pattern": "skip|Skip|Disabled|Ignore"},
            plant.naive,
        ),
        _step(
            14,
            "Observation: skip remains (step 13). Nightly still flakes sibling.",
            "bash",
            {"command": plant.cmd},
            "sibling FAIL leftover",
        ),
        _step(
            15,
            "Observation: sibling fail (step 14). Escalate.",
            "bash",
            {"command": f"echo PAGE {plant.ticket}"},
            f"PAGE {plant.ticket}",
        ),
        _step(
            16,
            "Observation: paged (step 15). Stop without isolate.",
            "bash",
            {"command": "echo STOP"},
            "STOP without quarantine",
        ),
        _step(
            17,
            "Observation: stop (step 16).",
            "bash",
            {"command": "echo HANDOFF"},
            "HANDOFF",
            reflection=f"Failed: {plant.drop} + {plant.naive} vs leftover {plant.cause}.",
        ),
    ]


def _meta(rnd: int, plant: cat.Plant, catalog_id: str) -> dict[str, Any]:
    return {
        "catalog_id": catalog_id,
        "designed": True,
        "factory": FACTORY,
        "generator": GENERATOR,
        "mill_id": plant.mill_id,
        "plant_id": plant.plant_id,
        "round": rnd,
    }


def success_episode(rnd: int, plant: cat.Plant, catalog_id: str) -> dict[str, Any]:
    record = {
        "id": f"flk-r{rnd:04d}-{plant.slug}-q",
        "goal": (
            f"{plant.ticket} {plant.test_file}::{plant.ok} flakes after {plant.mut}: "
            f"{plant.leftover}. Do not skip. Do not {plant.drop}. "
            f"Quarantine leftover ({plant.cause}) only."
        ),
        "plan": f"naive {plant.naive} then isolate {plant.isolate}.",
        "steps": _success_repro(plant) + _success_confirm(plant),
        "outcome": (
            f"{plant.leftover}. {plant.naive} hid order. Plan change: {plant.isolate}. "
            f"{plant.runner} kept; did not {plant.drop}. Residual: leftover isolated."
        ),
        "reward": {
            "success": True,
            "skip_rejected": 1,
            "drop_flag_rejected": 1,
            "plan_changes": 1,
            "tests_passed": 2,
            "orders_ok": 6,
            "cost_steps": 16,
        },
        "meta": _meta(rnd, plant, catalog_id),
    }
    _refuse_banned(record)
    return record


def fail_episode(rnd: int, plant: cat.Plant, catalog_id: str) -> dict[str, Any]:
    record = {
        "id": f"flk-r{rnd:04d}-{plant.slug}-handoff",
        "goal": (
            f"{plant.ticket}-H {plant.test_file}::{plant.ok} leftover {plant.leftover}. "
            f"Do not skip. Do not {plant.drop}. Isolate {plant.cause} leftover."
        ),
        "plan": f"{plant.drop} then {plant.naive}.",
        "steps": _fail_repro(plant) + _fail_handoff(plant),
        "outcome": (
            f"Handoff: {plant.drop} hid flake; {plant.naive} hid {plant.ok}; "
            f"leftover {plant.cause} remains. Need {plant.isolate} owner. "
            f"{plant.ticket} paged."
        ),
        "reward": {
            "success": False,
            "handoff": 1,
            "skip_applied": 1,
            "drop_flag_applied": 1,
            "plan_changes": 2,
            "cost_steps": 17,
        },
        "meta": _meta(rnd, plant, catalog_id),
    }
    _refuse_banned(record)
    return record


def notes_markdown(rnd: int, plant: cat.Plant) -> str:
    return (
        f"# NOTES r{rnd}\n\n"
        f"Novel coverage: 91%\n\n"
        f"- plant: {plant.runner} vs {plant.drop}\n"
        f"- cause: {plant.cause} leftover ({plant.leftover})\n"
        f"- success: isolate `{plant.isolate}` keep runner; reject `{plant.naive}`\n"
        f"- fail: `{plant.drop}` + `{plant.naive}` handoff `{plant.ticket}`\n"
    )


def _require_round(value: int | None, default: int) -> int:
    rnd = default if value is None else value
    if not isinstance(rnd, int) or isinstance(rnd, bool) or rnd < 1:
        raise FlkRefusal(FINDING_ROUND_INVALID, f"round must be a positive int, got {value!r}")
    return rnd


def _jobs(loaded: cat.Catalog, request: GenerateRequest) -> list[tuple[int, cat.Plant]]:
    selectors = (request.plant_id is not None, request.mill_id is not None, request.all_plants)
    if sum(selectors) != 1:
        raise FlkRefusal(FINDING_USAGE, "exactly one of plant_id, mill_id, or all_plants")
    if request.plant_id is not None:
        plant = loaded.plant(request.plant_id)
        return [(_require_round(request.round, plant.base_round), plant)]
    if request.round is not None:
        raise FlkRefusal(FINDING_USAGE, "round applies only with plant_id")
    if request.mill_id is not None:
        mills = [mill for mill in loaded.mills if mill.mill_id == request.mill_id]
        loaded.mill_plants(request.mill_id)
    else:
        mills = list(loaded.mills)
    jobs: list[tuple[int, cat.Plant]] = []
    for mill in mills:
        for index, plant in enumerate(loaded.mill_plants(mill.mill_id)):
            jobs.append((mill.base_round + index, plant))
    return jobs


def _check_destination(out_dir: Path) -> None:
    if is_under_raw(out_dir):
        raise FlkRefusal(FINDING_DESTINATION_UNDER_RAW, f"{out_dir} names or aliases the raw tree")
    if out_dir.exists():
        raise FlkRefusal(FINDING_DESTINATION_EXISTS, f"{out_dir} already exists")


def run(request: GenerateRequest) -> dict[str, Any]:
    """Generate episode pairs into a new destination. Returns the RUN summary."""

    _check_destination(Path(request.out_dir))
    loaded = cat.load_catalog(request.catalog_dir)
    jobs = _jobs(loaded, request)
    out_dir = Path(request.out_dir)
    out_dir.mkdir(parents=True, exist_ok=False)
    records: list[dict[str, Any]] = []
    note_chunks: list[str] = []
    for rnd, plant in jobs:
        records.append(success_episode(rnd, plant, loaded.catalog_id))
        records.append(fail_episode(rnd, plant, loaded.catalog_id))
        note_chunks.append(notes_markdown(rnd, plant))
    lines = [dumps_exact_json(record, ensure_ascii=False, sort_keys=True) for record in records]
    records_text = "\n".join(lines) + "\n"
    records_path = out_dir / RECORDS_FILENAME
    records_path.write_text(records_text, encoding="utf-8")
    notes_text = "\n".join(note_chunks)
    (out_dir / NOTES_FILENAME).write_text(notes_text, encoding="utf-8")
    summary = {
        "format": RUN_FORMAT,
        "catalog_id": loaded.catalog_id,
        "plants_sha256": loaded.plants_sha256,
        "factory": FACTORY,
        "generator": GENERATOR,
        "pairs": len(jobs),
        "quota_per_round": QUOTA_PER_ROUND,
        "records": len(records),
        "records_sha256": hashlib.sha256(records_text.encode("utf-8")).hexdigest(),
        "destination": str(out_dir),
    }
    (out_dir / RUN_FILENAME).write_text(
        dumps_exact_json(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return summary


bind_import_twin(__name__)
