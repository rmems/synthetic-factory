#!/usr/bin/env python3
"""Build LRD leftover leftover leftover episodes from the AST-extracted catalog.

These are the ``steps_ok`` / ``steps_fail`` / ``rec_ok`` / ``rec_fail`` /
``notes`` builders from ``lrd_r157``, taking a typed :class:`catalog.Plant`.
Writes go to a brand-new destination and never to ``outputs/raw``. The
legacy ``txn`` / ``main`` publish path is not reproduced. Hopper exec is
refused.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import catalog as cat
from ._contract import (
    BANNED_ID_PREFIXES,
    BANNED_KEYS,
    FACTORY,
    SHAPE_LEGACY,
    FINDING_BANNED_ID,
    FINDING_BANNED_KEY,
    FINDING_DESTINATION_EXISTS,
    FINDING_DESTINATION_UNDER_RAW,
    FINDING_HOPPER_REFUSED,
    FINDING_ROUND_INVALID,
    FINDING_USAGE,
    GENERATOR,
    NOTES_FILENAME,
    NOVEL_COVERAGE,
    QUOTA_PER_ROUND,
    RECORDS_FILENAME,
    RUN_FILENAME,
    RUN_FORMAT,
    bind_import_twin,
    dumps_exact_json,
    is_under_raw,
    refuse,
    refuse_when,
)

__all__ = [
    "GenerateRequest",
    "NOTES_FILENAME",
    "RECORDS_FILENAME",
    "RUN_FILENAME",
    "fail_record",
    "notes_markdown",
    "pair_records",
    "run",
    "success_record",
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
    refuse_when(
        bool(hits),
        FINDING_BANNED_KEY,
        f"record {record.get('id')!r} carries {hits[0] if hits else ''}",
    )
    record_id = record.get("id")
    if isinstance(record_id, str):
        for prefix in BANNED_ID_PREFIXES:
            refuse_when(
                record_id.startswith(prefix),
                FINDING_BANNED_ID,
                f"record id {record_id!r} uses {prefix}",
            )


def _step(n: int, basis: str, name: str, args: dict[str, str], observation: str) -> dict[str, Any]:
    return {
        "n": n,
        "decision_basis": basis,
        "tool_call": {"name": name, "args": args},
        "observation": observation,
    }


def steps_ok(plant: cat.Plant) -> list[dict[str, Any]]:
    """Success trajectory from ``lrd_r157.steps_ok``. Sixteen steps."""

    d = plant.mod
    field = plant.field
    return [
        _step(
            1,
            (
                f"Plan: pay-api {plant.stack} leaked leftover leftover leftover "
                f"{field}. Inspect before mute."
            ),
            "bash",
            {"command": f"ls -la {d}/ && rg -n '{field}|redact' {d} | head -40"},
            f"{plant.conf} {field}\nkept",
        ),
        _step(2, "Observation: Run failing tests.",
              "bash", {"command": f"pytest tests/{d}/{plant.test} -q --tb=short"},
              f"FAIL test_no_{field}: leaked. FAIL test_keep_warn."),
        _step(3, "Observation: Read writer.",
              "read_file", {"path": f"{d}/{plant.conf}"}, plant.oldc[:200]),
        _step(4, "Observation: Read config.",
              "read_file", {"path": f"{d}/{plant.conf2}"}, plant.old2[:200]),
        _step(5, "Observation: Side metrics.",
              "bash", {"command": f"rg -n '{field}' metrics {d} | head"},
              f"{plant.conf} {field}\nkept"),
        _step(
            6,
            f"Observation: Fetch {plant.domain} runbook.",
            "bash",
            {
                "command": (
                    f"curl -sS https://runbooks.lake.example.invalid/{d}/{plant.slug}"
                )
            },
            "HTTP/2 502 Bad Gateway: runbooks.lake",
        ),
        _step(
            7,
            "Observation: 502 at step 6; retry.",
            "bash",
            {
                "command": (
                    f"sleep 2 && curl -sS https://runbooks.lake.example.invalid"
                    f"/{d}/{plant.slug} || cat fixtures/runbooks/{plant.slug}.md"
                )
            },
            f"cached: omit leftover leftover leftover {field}. mute blinds warn.",
        ),
        _step(
            8,
            "Observation: Metrics next.",
            "bash",
            {
                "command": (
                    f"curl -sS https://metrics.lake.example.invalid/api/v1/{d}/{plant.slug}"
                )
            },
            "HTTP/2 429 too many requests Retry-After: 2",
        ),
        _step(
            9,
            "Observation: 429 at step 8; retry.",
            "bash",
            {
                "command": (
                    f"sleep 2 && curl -sS https://metrics.lake.example.invalid"
                    f"/api/v1/{d}/{plant.slug}"
                )
            },
            f"{plant.conf} {field} | kept",
        ),
        _step(10, f"Observation: First closed patch: {plant.naive}.",
              "edit_file", {"path": f"{d}/{plant.conf2}", "old": plant.old2, "new": plant.new2},
              "1 replacement"),
        _step(11, "Observation: Re-test.",
              "bash", {"command": f"pytest tests/{d}/{plant.test} -q --tb=short"},
              "FAILED test_keep_warn: warn gone. leak would vanish for the wrong reason."),
        _step(
            12,
            (
                f"Reflection: Plan change: {plant.naive} is the wrong layer. "
                f"Redact leftover leftover leftover {field}."
            ),
            "read_file",
            {"path": f"{d}/{plant.conf}"},
            f"Need redact {field}. Restore warn.",
        ),
        _step(13, f"Observation: Redact leftover leftover leftover {field}; keep warn.",
              "edit_file", {"path": f"{d}/{plant.conf}", "old": plant.oldc, "new": plant.newc},
              "1 replacement; config restored"),
        _step(14, "Observation: Re-test.",
              "bash", {"command": f"pytest tests/{d}/{plant.test} -q --tb=short"},
              "PASS test_no_secret\nPASS test_keep_log\nPASS test_redact\n3 passed"),
        _step(15, "Observation: git diff --stat.",
              "bash", {"command": f"git diff --stat {d}/{plant.conf} {d}/{plant.conf2}"},
              f"{d}/{plant.conf} | 6 +++---\n{d}/{plant.conf2} | 2 +-"),
        _step(
            16,
            "Observation: Close comment. Distinct leftover leftover leftover plant.",
            "bash",
            {
                "command": (
                    f"echo '{plant.ticket} {plant.stack} redact. Residual: one path raw'"
                )
            },
            f"{plant.ticket} tests green residual one path raw",
        ),
    ]


def steps_fail(plant: cat.Plant) -> list[dict[str, Any]]:
    """Handoff trajectory from ``lrd_r157.steps_fail``. Seventeen steps."""

    d = plant.drop
    field = plant.field
    return [
        _step(
            1,
            (
                f"Plan: rewrite leftover leftover leftover dumped {field}. "
                f"User asked to disable {plant.stack}."
            ),
            "bash",
            {"command": f"ls -la {d}/"},
            f"{plant.conf2} present",
        ),
        _step(2, "Observation: failing tests include keep-warn.",
              "bash", {"command": f"pytest tests/{d}/{plant.test} -q --tb=short"},
              "FAIL leak. FAIL keep_warn."),
        _step(3, "Observation: README leftover leftover leftover says disable the logger.",
              "read_file", {"path": "README.md"}, f"README: {plant.naive} to stop leaks."),
        _step(4, "Observation: runbook forbids disable.",
              "read_file", {"path": f"docs/{plant.stack}-redact.md"},
              f"Redact {field}; do not {plant.naive}."),
        _step(5, "Observation: agent follows README anyway.",
              "read_file", {"path": f"{d}/{plant.conf2}"}, plant.old2[:200]),
        _step(
            6,
            "Observation: 502 runbook.",
            "bash",
            {
                "command": (
                    f"curl -sS https://runbooks.lake.example.invalid/{d}/{plant.fail}"
                )
            },
            "HTTP/2 502",
        ),
        _step(7, "Observation: retry fixture.",
              "bash", {"command": f"cat fixtures/runbooks/{plant.fail}.md"},
              f"do not {plant.naive}"),
        _step(
            8,
            "Observation: 429 metrics.",
            "bash",
            {
                "command": (
                    f"curl -sS https://metrics.lake.example.invalid/api/v1/{d}/{plant.fail}"
                )
            },
            "HTTP/2 429",
        ),
        _step(9, "Observation: retry metrics.",
              "bash", {"command": "sleep 2 && echo METRICS"}, "warn still required"),
        _step(10, f"Observation: apply {plant.naive}.",
              "edit_file", {"path": f"{d}/{plant.conf2}", "old": plant.old2, "new": plant.new2},
              "1 replacement"),
        _step(11, "Observation: re-test.",
              "bash", {"command": f"pytest tests/{d}/{plant.test} -q --tb=short"},
              "FAILED test_keep_warn"),
        _step(
            12,
            "Observation: agent writes handoff instead of redact.",
            "write_file",
            {
                "path": f"docs/incidents/{plant.fail}.md",
                "content": f"disabled {plant.stack}",
            },
            "handoff only",
        ),
        _step(13, "Observation: leak path still raw if logger is off.",
              "read_file", {"path": f"{d}/{plant.conf}"}, f"{field} still in writer"),
        _step(14, "Observation: warn tests still fail.",
              "bash", {"command": f"pytest tests/{d}/{plant.test} -q --tb=short"},
              "FAILED test_keep_warn 0 passed"),
        _step(15, "Observation: git diff shows disable only.",
              "bash", {"command": f"git diff --stat {d}"}, f"{d}/{plant.conf2} | disable"),
        _step(16, "Observation: close as failed handoff.",
              "bash", {"command": "echo FAIL_HANDOFF"}, "FAIL_HANDOFF"),
        _step(17, "Observation: residual leak if anyone re-enables logger.",
              "bash", {"command": "echo RESIDUAL_RAW"}, "RESIDUAL_RAW"),
    ]


def success_record(rnd: int, plant: cat.Plant, catalog_id: str) -> dict[str, Any]:
    st = steps_ok(plant)
    record = {
        "id": f"lrd-r{rnd}-{plant.slug}",
        "goal": (
            f"{plant.stack} pay-api dumped leftover leftover leftover {plant.field}. "
            f"Redact the field; do not {plant.naive} (that blinds warn)."
        ),
        "plan": (
            f"Prove {plant.field} dump. Try {plant.naive}; if warn tests fail, "
            f"redact {plant.field}."
        ),
        "outcome": (
            f"{plant.naive} blinded warn. {plant.stack} redact. Tests 3/3. "
            f"Residual one path still raw."
        ),
        "reward": {
            "success": True, "tests_passed": 3, "retries": 2, "duration_min": 12,
            "wasted_calls": 2, "cost_steps": len(st), "leaked": 168,
        },
        "steps": st,
        "meta": {
            "catalog_id": catalog_id,
            "designed": True,
            "domain": plant.domain,
            "factory": FACTORY,
            "generator": GENERATOR,
            "kind": "episode",
            "mill_id": plant.mill_id,
            "plant_id": plant.plant_id,
            "round": rnd,
            "seed": plant.slug,
            "sim_or_real": "designed",
            "stack": f"{plant.stack} leftover leftover leftover {plant.field} vs {plant.naive}",
        },
    }
    _refuse_banned(record)
    return record


def fail_record(rnd: int, plant: cat.Plant, catalog_id: str) -> dict[str, Any]:
    st = steps_fail(plant)
    record = {
        "id": f"lrd-r{rnd}-{plant.fail}",
        "goal": (
            f"{plant.stack} pay-api rewrite leftover leftover leftover dumped {plant.field}. "
            f"Do not disable {plant.stack}. Handoff only is a miss."
        ),
        "plan": "README leftover leftover leftover says disable. Agent should redact instead.",
        "outcome": f"Followed README {plant.naive}. Warn tests failed. Handoff only.",
        "reward": {
            "success": False, "tests_passed": 0, "retries": 1, "duration_min": 8,
            "wasted_calls": 3, "cost_steps": len(st), "leaked": 168,
        },
        "steps": st,
        "meta": {
            "catalog_id": catalog_id,
            "designed": True,
            "domain": plant.domain + "-handoff",
            "factory": FACTORY,
            "generator": GENERATOR,
            "kind": "episode",
            "mill_id": plant.mill_id,
            "plant_id": plant.plant_id,
            "round": rnd,
            "seed": plant.fail,
            "sim_or_real": "designed",
            "stack": f"{plant.stack} leftover leftover leftover {plant.field} vs disable",
        },
    }
    _refuse_banned(record)
    return record


def pair_records(rnd: int, plant: cat.Plant, catalog_id: str) -> list[dict[str, Any]]:
    refuse_when(
        plant.shape != SHAPE_LEGACY,
        FINDING_USAGE,
        f"generate supports legacy r157 plants only, not {plant.shape!r}",
    )
    return [success_record(rnd, plant, catalog_id), fail_record(rnd, plant, catalog_id)]


def notes_markdown(rnd: int, plant: cat.Plant) -> str:
    return (
        f"Round r{rnd} leftover leftover leftover {plant.stack} `{plant.field}` "
        f"vs `{plant.naive}`.\n"
        f"Novel coverage: {NOVEL_COVERAGE}\n"
        f"Pair: redact vs disable. README leftover leftover leftover vs leftover "
        f"leftover leftover runbook.\n"
        f"Residual: one path raw.\n"
    )


def _require_round(value: int | None, default: int) -> int:
    rnd = default if value is None else value
    refuse_when(
        not isinstance(rnd, int) or isinstance(rnd, bool) or rnd < 1,
        FINDING_ROUND_INVALID,
        f"round must be a positive int, got {value!r}",
    )
    return rnd


def _jobs(loaded: cat.Catalog, request: GenerateRequest) -> list[tuple[int, cat.Plant]]:
    selectors = (request.plant_id is not None, request.mill_id is not None, request.all_plants)
    refuse_when(
        sum(selectors) != 1,
        FINDING_USAGE,
        "exactly one of plant_id, mill_id, or all_plants",
    )
    if request.plant_id is not None:
        plant = loaded.plant(request.plant_id)
        return [(_require_round(request.round, plant.base_round), plant)]
    refuse_when(
        request.round is not None,
        FINDING_USAGE,
        "round applies only with plant_id",
    )
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
    refuse_when(
        is_under_raw(out_dir),
        FINDING_DESTINATION_UNDER_RAW,
        f"{out_dir} names or aliases the raw tree",
    )
    refuse_when(out_dir.exists(), FINDING_DESTINATION_EXISTS, f"{out_dir} already exists")


def refuse_hopper_exec(label: str) -> None:
    """Public seam: this package never execs dpr-lrd hoppers."""

    refuse(FINDING_HOPPER_REFUSED, f"{label}: hopper exec stays with dpr")


def run(request: GenerateRequest) -> dict[str, Any]:
    """Generate Q=2 episode pairs into a new destination. Returns the RUN summary."""

    _check_destination(Path(request.out_dir))
    loaded = cat.load_catalog(request.catalog_dir)
    jobs = _jobs(loaded, request)
    for _, plant in jobs:
        refuse_when(
            plant.shape != SHAPE_LEGACY,
            FINDING_USAGE,
            f"generate supports legacy r157 plants only, not {plant.shape!r}",
        )
    out_dir = Path(request.out_dir)
    out_dir.mkdir(parents=True, exist_ok=False)
    records: list[dict[str, Any]] = []
    note_chunks: list[str] = []
    for rnd, plant in jobs:
        pair = pair_records(rnd, plant, loaded.catalog_id)
        refuse_when(
            len(pair) != QUOTA_PER_ROUND,
            FINDING_USAGE,
            f"pair quota is {QUOTA_PER_ROUND}, got {len(pair)}",
        )
        records.extend(pair)
        note_chunks.append(notes_markdown(rnd, plant))
    lines = [dumps_exact_json(record, ensure_ascii=False, sort_keys=True) for record in records]
    records_text = "\n".join(lines) + "\n"
    (out_dir / RECORDS_FILENAME).write_text(records_text, encoding="utf-8")
    (out_dir / NOTES_FILENAME).write_text("\n".join(note_chunks), encoding="utf-8")
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
