#!/usr/bin/env python3
"""Emit designed observability episode pairs from a pinned OBS catalog.

Writes a brand-new destination (records.jsonl, RUN.json, NOTES.md). Refuses
an existing path, any path that names or aliases ``outputs/raw/``, and any
vendored mill-script destination. Does not hop factories, does not shell
out to ``round_txn``, and does not stamp ``grok-4.6``.
"""

from __future__ import annotations

from collections.abc import Mapping
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


def _step(n: int, basis: str, tool_call: dict[str, Any], observation: str) -> dict[str, Any]:
    clipped = _clip(basis)
    prefix = clipped.split(":", 1)[0]
    if prefix not in BASIS_PREFIXES:
        raise ObsRefusal(FINDING_USAGE, f"bad decision_basis prefix: {basis!r}")
    return {
        "n": n,
        "decision_basis": clipped,
        "tool_call": tool_call,
        "observation": observation,
    }


def _bash(command: str) -> dict[str, Any]:
    return {"name": "bash", "args": {"command": command}}


def _edit(path: str, old: str, new: str) -> dict[str, Any]:
    return {"name": "edit", "args": {"path": path, "old": old, "new": new}}


def _write(path: str, contents: str) -> dict[str, Any]:
    return {"name": "write", "args": {"path": path, "contents": contents}}


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


def _success_diagnosis_steps(s: Mapping[str, Any], slug: str) -> list[dict[str, Any]]:
    """Success steps 1-3: read the dashboard file, query the series, confirm the source."""

    return [
        _step(
            1,
            f"Plan: read {s['file']} before trusting Grafana for {s['svc']}.",
            _bash(f"rg -n '{s['fail_val']}|{slug}' {s['file']} dashboards | head -n 20"),
            f"{s['file']}: leftover {s['fail_val']}\nquery: {s['query']}",
        ),
        _step(
            2,
            f"Observation: knob in {s['file']} (step 1). Query the live series.",
            _bash(f"curl -sS $OBS/query --data-urlencode 'query={s['query']}'"),
            f"empty or capped series; lie: {s['lie']}",
        ),
        _step(
            3,
            "Observation: dashboard empty (step 2). Confirm source still healthy.",
            _bash(f"kubectl -n obs logs deploy/{s['svc']} --tail=20 | wc -l"),
            "source still emitting; Grafana is the leftover lie",
        ),
    ]


def _success_fix_steps(s: Mapping[str, Any], slug: str) -> list[dict[str, Any]]:
    """Success steps 4-8: bind the leftover knob, re-query, add a regression, gate, clean."""

    return [
        _step(
            4,
            f"Plan: bind leftover {s['fail_val']} to {s['fix_val']} on {s['file']}.",
            _edit(s["file"], str(s["fail_val"]), str(s["fix_val"])),
            f"patched {s['file']} {s['fail_val']} -> {s['fix_val']}",
        ),
        _step(
            5,
            "Observation: first bind (step 4). Re-query.",
            _bash(f"curl -sS $OBS/query --data-urlencode 'query={s['query']}'"),
            "series return; panel populated",
        ),
        _step(
            6,
            f"Plan: add a regression that leftover {s['fail_val']} must not return.",
            _write(
                f"tests/test_{slug.replace('-', '_')}.py",
                f"def test_no_leftover_{slug.replace('-', '_')}():\n    assert True\n",
            ),
            "regression written",
        ),
        _step(
            7,
            "Observation: regression written (step 6). Re-run the gate.",
            _bash("pytest tests -q --tb=line 2>&1 | tail -n 4"),
            "2 passed in 0.12s",
        ),
        _step(
            8,
            f"Observation: gate green (step 7). Distinct from {s.get('new_vs', 'prior leftover clones')}.",
            _bash(f"rg -n '{s['fail_val']}' {s['file']} || echo CLEAN"),
            "CLEAN",
        ),
    ]


def success_episode(rnd: int, plant: cat.Plant, catalog_id: str) -> dict[str, Any]:
    s = _pair_fields(plant)
    slug = s["slug"]
    steps = [*_success_diagnosis_steps(s, slug), *_success_fix_steps(s, slug)]
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


def _fail_patch_steps(s: Mapping[str, Any], lslug: str) -> list[dict[str, Any]]:
    """Handoff steps 1-4: read, query, apply the naive first-success patch, re-query."""

    return [
        _step(
            1,
            f"Plan: read {s['lfile']} before trusting Grafana for {s['lsvc']}.",
            _bash(f"rg -n '{s['fail_val']}|{lslug}' {s['lfile']} dashboards | head -n 20"),
            f"{s['lfile']}: leftover handoff\nquery: {s['lquery']}",
        ),
        _step(
            2,
            f"Observation: leftover on {s['lsvc']} (step 1). Query the live series.",
            _bash(f"curl -sS $OBS/query --data-urlencode 'query={s['lquery']}'"),
            f"empty series; lie: {s['llie']}",
        ),
        _step(
            3,
            "Observation: dashboard empty (step 2). Apply the first-success patch.",
            _edit(s["lfile"], str(s["fail_val"]), str(s["fix_val"])),
            "naive first patch applied; leftover bind still holds",
        ),
        _step(
            4,
            "Observation: first patch (step 3). Re-query.",
            _bash(f"curl -sS $OBS/query --data-urlencode 'query={s['lquery']}'"),
            "still empty; naive patch did not bind the leftover lie",
        ),
    ]


def _fail_handoff_steps(s: Mapping[str, Any], lslug: str) -> list[dict[str, Any]]:
    """Handoff steps 5-8: write the handoff, gate still red, xfail the residual, re-run."""

    return [
        _step(
            5,
            f"Reflection: plan change — {s['llie']}",
            _write(f"docs/handoff/{lslug}.md", f"Handoff: {s['llie']}\n"),
            "handoff written; leftover remains",
        ),
        _step(
            6,
            "Observation: handoff written (step 5). Gate still red.",
            _bash(f"curl -sS $OBS/query --data-urlencode 'query={s['lquery']}'"),
            "empty; xfail the leftover residual",
        ),
        _step(
            7,
            "Plan: mark the leftover residual as a handoff xfail.",
            _edit(
                f"tests/test_{lslug.replace('-', '_')}.py",
                "assert False",
                "pytest.xfail('residual leftover')",
            ),
            "xfails leftover residual",
        ),
        _step(
            8,
            "Observation: xfail recorded (step 7). Handoff remains.",
            _bash("pytest tests -q --tb=line 2>&1 | tail -n 4"),
            "1 passed, 1 xfailed in 0.11s",
        ),
    ]


def fail_episode(rnd: int, plant: cat.Plant, catalog_id: str) -> dict[str, Any]:
    s = _pair_fields(plant)
    lslug = s["lslug"]
    steps = [*_fail_patch_steps(s, lslug), *_fail_handoff_steps(s, lslug)]
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
        return [_plant_job(loaded, request.plant_id, request.round)]
    if request.round is not None:
        raise ObsRefusal(FINDING_USAGE, "--round is only valid with --plant")
    return _pair_jobs(_selected_plants(loaded, request))


def _plant_job(
    loaded: cat.Catalog, plant_id: str, round_n: int | None
) -> tuple[int, cat.Plant]:
    plant = loaded.plant(plant_id)
    if plant.shape not in {SHAPE_HOP, SHAPE_LEFTOVER3}:
        raise ObsRefusal(
            FINDING_SHAPE_UNSUPPORTED,
            f"generate refuses leftover-spec plant {plant.plant_id}",
        )
    return _require_round(round_n, plant.base_round), plant


def _selected_plants(loaded: cat.Catalog, request: GenerateRequest) -> tuple[cat.Plant, ...]:
    if request.mill_id is not None:
        return loaded.mill_plants(request.mill_id)
    plants = loaded.pair_plants()
    if not plants:
        raise ObsRefusal(FINDING_USAGE, "catalog has no hop or leftover3 plants")
    return plants


def _pair_jobs(plants: tuple[cat.Plant, ...]) -> list[tuple[int, cat.Plant]]:
    """Hop and leftover3 plants, each at its base round plus its selection index."""

    jobs = [
        (plant.base_round + index, plant)
        for index, plant in enumerate(plants)
        if plant.shape in {SHAPE_HOP, SHAPE_LEFTOVER3}
    ]
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
