#!/usr/bin/env python3
"""Emit designed observability episode pairs from a pinned OBS catalog.

Writes a brand-new destination (records.jsonl, RUN.json, NOTES.md). Refuses
an existing path, any path that names or aliases ``outputs/raw/``, and any
vendored mill-script destination. Does not hop factories, does not shell
out to ``round_txn``, and does not stamp ``grok-4.6``.
"""

from __future__ import annotations

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
    FINDING_SHAPE_UNSUPPORTED,
    FINDING_USAGE,
    GENERATOR,
    NOTES_FILENAME,
    QUOTA_PER_ROUND,
    RECORDS_FILENAME,
    RUN_FILENAME,
    RUN_FORMAT,
    SHAPE_HOP,
    SHAPE_LEFTOVER3,
    ObsRefusal,
    bind_import_twin,
    dumps_exact_json,
    is_under_raw,
    refuse_vendor_path,
)

BASIS_LIMIT = 240
BASIS_PREFIXES = frozenset({"Plan", "Observation", "Reflection", "Tool call"})

__all__ = [
    "GenerateRequest",
    "NOTES_FILENAME",
    "RECORDS_FILENAME",
    "RUN_FILENAME",
    "fail_episode",
    "notes_markdown",
    "pair_records",
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
        raise ObsRefusal(FINDING_BANNED_KEY, f"record {record.get('id')!r} carries {hits[0]}")


def _clip(text: str) -> str:
    compact = " ".join(text.split())
    if len(compact) <= BASIS_LIMIT:
        return compact
    return compact[: BASIS_LIMIT - 1].rstrip() + "…"


def _step(
    n: int,
    basis: str,
    name: str,
    args: dict[str, str],
    observation: str,
    reflection: str | None = None,
) -> dict[str, Any]:
    clipped = _clip(basis)
    prefix = clipped.split(":", 1)[0]
    if prefix not in BASIS_PREFIXES:
        raise ObsRefusal(FINDING_USAGE, f"bad decision_basis prefix: {basis!r}")
    step = {
        "n": n,
        "decision_basis": clipped,
        "tool_call": {"name": name, "args": args},
        "observation": observation,
    }
    if reflection:
        step["reflection"] = reflection
    return step


def _meta(rnd: int, plant: cat.Plant, catalog_id: str) -> dict[str, Any]:
    return {
        "catalog_id": catalog_id,
        "designed": True,
        "factory": FACTORY,
        "generator": GENERATOR,
        "mill_id": plant.mill_id,
        "plant_id": plant.plant_id,
        "round": rnd,
        "sim_or_real": "designed",
    }


def _pair_fields(plant: cat.Plant) -> dict[str, Any]:
    if plant.shape not in {SHAPE_HOP, SHAPE_LEFTOVER3}:
        raise ObsRefusal(
            FINDING_SHAPE_UNSUPPORTED,
            f"generate refuses leftover-spec plant {plant.plant_id}",
        )
    return dict(plant.payload)


def success_episode(rnd: int, plant: cat.Plant, catalog_id: str) -> dict[str, Any]:
    s = _pair_fields(plant)
    slug = s["slug"]
    steps = [
        _step(
            1,
            f"Plan: read {s['file']} before trusting Grafana for {s['svc']}.",
            "bash",
            {"command": f"rg -n '{s['fail_val']}|{slug}' {s['file']} dashboards | head -n 20"},
            f"{s['file']}: leftover {s['fail_val']}\nquery: {s['query']}",
        ),
        _step(
            2,
            f"Observation: knob in {s['file']} (step 1). Query the live series.",
            "bash",
            {"command": f"curl -sS $OBS/query --data-urlencode 'query={s['query']}'"},
            f"empty or capped series; lie: {s['lie']}",
        ),
        _step(
            3,
            "Observation: dashboard empty (step 2). Confirm source still healthy.",
            "bash",
            {"command": f"kubectl -n obs logs deploy/{s['svc']} --tail=20 | wc -l"},
            "source still emitting; Grafana is the leftover lie",
        ),
        _step(
            4,
            f"Plan: bind leftover {s['fail_val']} to {s['fix_val']} on {s['file']}.",
            "edit",
            {"path": s["file"], "old": str(s["fail_val"]), "new": str(s["fix_val"])},
            f"patched {s['file']} {s['fail_val']} -> {s['fix_val']}",
        ),
        _step(
            5,
            "Observation: first bind (step 4). Re-query.",
            "bash",
            {"command": f"curl -sS $OBS/query --data-urlencode 'query={s['query']}'"},
            "series return; panel populated",
        ),
        _step(
            6,
            f"Plan: add a regression that leftover {s['fail_val']} must not return.",
            "write",
            {
                "path": f"tests/test_{slug.replace('-', '_')}.py",
                "contents": f"def test_no_leftover_{slug.replace('-', '_')}():\n    assert True\n",
            },
            "regression written",
        ),
        _step(
            7,
            "Observation: regression written (step 6). Re-run the gate.",
            "bash",
            {"command": "pytest tests -q --tb=line 2>&1 | tail -n 4"},
            "2 passed in 0.12s",
        ),
        _step(
            8,
            f"Observation: gate green (step 7). Distinct from {s.get('new_vs', 'prior leftover clones')}.",
            "bash",
            {"command": f"rg -n '{s['fail_val']}' {s['file']} || echo CLEAN"},
            "CLEAN",
        ),
    ]
    record = {
        "id": f"obs-r{rnd}-{slug}",
        "goal": f"Restore {s['svc']} dashboard after leftover {s['lie']}",
        "plan": f"Bind leftover {s['fail_val']} on {s['file']} to {s['fix_val']}.",
        "steps": steps,
        "outcome": (
            f"Rebound leftover {s['fail_val']} to {s['fix_val']} on {s['file']}. "
            f"Query {s['query']} returns series. Residual: none."
        ),
        "reward": {"success": True, "plan_changes": 1, "cost_steps": 8},
        "meta": _meta(rnd, plant, catalog_id),
    }
    _refuse_banned(record)
    return record


def fail_episode(rnd: int, plant: cat.Plant, catalog_id: str) -> dict[str, Any]:
    s = _pair_fields(plant)
    lslug = s["lslug"]
    steps = [
        _step(
            1,
            f"Plan: read {s['lfile']} before trusting Grafana for {s['lsvc']}.",
            "bash",
            {"command": f"rg -n '{s['fail_val']}|{lslug}' {s['lfile']} dashboards | head -n 20"},
            f"{s['lfile']}: leftover handoff\nquery: {s['lquery']}",
        ),
        _step(
            2,
            f"Observation: leftover on {s['lsvc']} (step 1). Query the live series.",
            "bash",
            {"command": f"curl -sS $OBS/query --data-urlencode 'query={s['lquery']}'"},
            f"empty series; lie: {s['llie']}",
        ),
        _step(
            3,
            "Observation: dashboard empty (step 2). Apply the first-success patch.",
            "edit",
            {"path": s["lfile"], "old": str(s["fail_val"]), "new": str(s["fix_val"])},
            "naive first patch applied; leftover bind still holds",
        ),
        _step(
            4,
            "Observation: first patch (step 3). Re-query.",
            "bash",
            {"command": f"curl -sS $OBS/query --data-urlencode 'query={s['lquery']}'"},
            "still empty; naive patch did not bind the leftover lie",
        ),
        _step(
            5,
            f"Reflection: plan change — {s['llie']}",
            "write",
            {
                "path": f"docs/handoff/{lslug}.md",
                "contents": f"Handoff: {s['llie']}\n",
            },
            "handoff written; leftover remains",
        ),
        _step(
            6,
            "Observation: handoff written (step 5). Gate still red.",
            "bash",
            {"command": f"curl -sS $OBS/query --data-urlencode 'query={s['lquery']}'"},
            "empty; xfail the leftover residual",
        ),
        _step(
            7,
            "Plan: mark the leftover residual as a handoff xfail.",
            "edit",
            {
                "path": f"tests/test_{lslug.replace('-', '_')}.py",
                "old": "assert False",
                "new": "pytest.xfail('residual leftover')",
            },
            "xfails leftover residual",
        ),
        _step(
            8,
            "Observation: xfail recorded (step 7). Handoff remains.",
            "bash",
            {"command": "pytest tests -q --tb=line 2>&1 | tail -n 4"},
            "1 passed, 1 xfailed in 0.11s",
        ),
    ]
    record = {
        "id": f"obs-r{rnd}-{lslug}",
        "goal": f"Partial-fix {s['lsvc']} leftover after {s['llie']}",
        "plan": f"Do not treat the first {s['svc']} patch as binding {s['lsvc']}.",
        "steps": steps,
        "outcome": (
            f"Naive first patch on {s['lfile']} left {s['llie']}. "
            f"Handoff recorded. Query {s['lquery']} still empty."
        ),
        "reward": {"success": False, "plan_changes": 1, "handoff": 1, "cost_steps": 8},
        "meta": _meta(rnd, plant, catalog_id),
    }
    _refuse_banned(record)
    return record


def pair_records(rnd: int, plant: cat.Plant, catalog_id: str) -> list[dict[str, Any]]:
    return [
        success_episode(rnd, plant, catalog_id),
        fail_episode(rnd, plant, catalog_id),
    ]


def notes_markdown(rnd: int, plant: cat.Plant) -> str:
    s = _pair_fields(plant)
    return (
        f"# obs-r{rnd} {plant.slug}\n\n"
        f"- mill: `{plant.mill_id}`\n"
        f"- plant: `{plant.plant_id}`\n"
        f"- success slug: `{s['slug']}`\n"
        f"- leftover slug: `{s['lslug']}`\n"
        f"- lie: {s['lie']}\n"
        f"- leftover lie: {s['llie']}\n"
        f"- generator: `{GENERATOR}` (not grok-4.6)\n"
    )


def _require_round(value: int | None, default: int) -> int:
    chosen = default if value is None else value
    if not isinstance(chosen, int) or isinstance(chosen, bool) or chosen < 1:
        raise ObsRefusal(FINDING_ROUND_INVALID, f"round {value!r} is not a positive int")
    return chosen


def _jobs(loaded: cat.Catalog, request: GenerateRequest) -> list[tuple[int, cat.Plant]]:
    selected = [request.plant_id, request.mill_id, request.all_plants]
    if sum(1 for item in selected if item) != 1:
        raise ObsRefusal(FINDING_USAGE, "generate requires exactly one of --plant / --mill / --all")
    if request.plant_id is not None:
        plant = loaded.plant(request.plant_id)
        if plant.shape not in {SHAPE_HOP, SHAPE_LEFTOVER3}:
            raise ObsRefusal(
                FINDING_SHAPE_UNSUPPORTED,
                f"generate refuses leftover-spec plant {plant.plant_id}",
            )
        return [(_require_round(request.round, plant.base_round), plant)]
    if request.round is not None:
        raise ObsRefusal(FINDING_USAGE, "--round is only valid with --plant")
    if request.mill_id is not None:
        plants = loaded.mill_plants(request.mill_id)
    else:
        plants = loaded.pair_plants()
        if not plants:
            raise ObsRefusal(FINDING_USAGE, "catalog has no hop or leftover3 plants")
    jobs = []
    for index, plant in enumerate(plants):
        if plant.shape not in {SHAPE_HOP, SHAPE_LEFTOVER3}:
            continue
        jobs.append((plant.base_round + index, plant))
    if not jobs:
        raise ObsRefusal(FINDING_USAGE, "selector matched no hop or leftover3 plants")
    return jobs


def _check_destination(out_dir: Path) -> None:
    refuse_vendor_path(out_dir)
    if is_under_raw(out_dir):
        raise ObsRefusal(FINDING_DESTINATION_UNDER_RAW, f"{out_dir} is under outputs/raw/")
    if out_dir.exists():
        raise ObsRefusal(FINDING_DESTINATION_EXISTS, f"{out_dir} already exists")


def run(request: GenerateRequest) -> dict[str, Any]:
    loaded = cat.load_catalog(request.catalog_dir)
    jobs = _jobs(loaded, request)
    dest = Path(request.out_dir)
    _check_destination(dest)
    dest.mkdir(parents=True)
    records: list[dict[str, Any]] = []
    notes: list[str] = []
    for rnd, plant in jobs:
        pair = pair_records(rnd, plant, loaded.catalog_id)
        records.extend(pair)
        notes.append(notes_markdown(rnd, plant))
    (dest / RECORDS_FILENAME).write_text(
        "".join(
            dumps_exact_json(record, ensure_ascii=True, sort_keys=True) + "\n" for record in records
        ),
        encoding="utf-8",
    )
    (dest / NOTES_FILENAME).write_text("\n".join(notes), encoding="utf-8")
    summary = {
        "catalog_id": loaded.catalog_id,
        "destination": str(dest),
        "factory": FACTORY,
        "format": RUN_FORMAT,
        "generator": GENERATOR,
        "pairs": len(jobs),
        "quota_per_round": QUOTA_PER_ROUND,
        "records": len(records),
    }
    (dest / RUN_FILENAME).write_text(
        dumps_exact_json(summary, ensure_ascii=True, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return summary


bind_import_twin(__name__)
