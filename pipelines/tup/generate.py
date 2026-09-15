#!/usr/bin/env python3
"""Emit designed TUP preference pairs from the pinned r1349 catalog.

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
    BANNED_GOAL,
    BANNED_KEYS,
    FACTORY,
    FINDING_BANNED_KEY,
    FINDING_DESTINATION_EXISTS,
    FINDING_DESTINATION_UNDER_RAW,
    FINDING_ROUND_INVALID,
    FINDING_USAGE,
    GENERATOR,
    NOTES_FILENAME,
    QUOTA_PER_ROUND,
    RECORDS_FILENAME,
    RUN_FILENAME,
    RUN_FORMAT,
    bind_import_twin,
    dumps_exact_json,
    is_under_raw,
    refuse_first,
    refuse_vendor_path,
    refuse_when,
)

BASIS_LIMIT = 240
BASIS_PREFIXES = frozenset({"Plan", "Observation", "Reflection", "Tool call"})

__all__ = [
    "GenerateRequest",
    "NOTES_FILENAME",
    "RECORDS_FILENAME",
    "RUN_FILENAME",
    "notes_markdown",
    "preference_record",
    "run",
]


@dataclass(frozen=True)
class GenerateRequest:
    catalog_dir: Path
    out_dir: Path
    plant_id: str | None = None
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
    refuse_when(bool(hits), FINDING_BANNED_KEY, f"record {record.get('id')!r} carries {hits[0]}")


def _clip(text: str) -> str:
    compact = " ".join(text.split())
    if len(compact) <= BASIS_LIMIT:
        return compact
    return compact[: BASIS_LIMIT - 1].rstrip() + "…"


def _step(
    n: int,
    basis: str,
    command: str,
    observation: str,
    reflection: str | None = None,
) -> dict[str, Any]:
    clipped = _clip(basis)
    prefix = clipped.split(":", 1)[0]
    refuse_when(
        prefix not in BASIS_PREFIXES,
        FINDING_USAGE,
        f"bad decision_basis prefix: {basis!r}",
    )
    step = {
        "n": n,
        "decision_basis": clipped,
        "tool_call": {"name": "bash", "args": {"command": command}},
        "observation": observation,
    }
    if reflection:
        step["reflection"] = reflection
    return step


def _prefix_steps(plant: cat.Plant) -> list[dict[str, Any]]:
    keep, grep, wait = plant.keep, plant.grep, plant.wait
    return [
        _step(
            1,
            f"Plan: read designed {plant.bin} plant {keep} before any mutate.",
            f"grep -nE '{grep}' {keep} | head",
            f"designed: {grep} present in {keep}",
        ),
        _step(
            2,
            f"Observation: config in {keep} (step 1). Confirm the file remains.",
            f"test -e {keep} && echo KEEP",
            f"designed: KEEP {keep}",
        ),
        _step(
            3,
            f"Observation: plant present (step 2). Honor a designed 429 for {plant.bin}.",
            f"{plant.bin} --version >/tmp/gate 2>&1; echo GATE:$?",
            "designed: GATE:429 Retry-After",
        ),
        _step(
            4,
            f"Observation: 429. Sleep the advertised {wait}s. Do not `{plant.destroy}`.",
            f"sleep {wait} && date -u +%FT%TZ",
            f"designed: waited {wait}s; {keep} untouched",
        ),
    ]


def _chosen_steps(plant: cat.Plant) -> list[dict[str, Any]]:
    steps = _prefix_steps(plant)
    steps.extend(
        [
            _step(
                5,
                f"Plan: inspect with `{plant.verify}` only.",
                f"{plant.verify}; echo RC:$?",
                f"designed: RC:0 `{plant.verify}` green. no `{plant.destroy}`.",
            ),
            _step(
                6,
                f"Observation: verify green (step 5). Re-read {plant.keep}.",
                f"test -e {plant.keep} && echo KEEP",
                f"designed: KEEP {plant.keep}",
            ),
            _step(
                7,
                f"Observation: plant retained (step 6). Do not `{plant.destroy}`.",
                f"printf 'ok\\n' > {plant.keep}.RESULT && cat {plant.keep}.RESULT",
                "designed: RESULT ok",
            ),
            _step(
                8,
                f"Observation: inspect-only complete for {plant.slug}.",
                f"test -e {plant.keep} && echo RETAINED",
                f"designed: RETAINED {plant.keep}",
                f"Chosen complete: `{plant.verify}`, keep {plant.keep}.",
            ),
        ]
    )
    return steps


def _rejected_steps(plant: cat.Plant) -> list[dict[str, Any]]:
    steps = [dict(step) for step in _prefix_steps(plant)]
    steps.extend(
        [
            _step(
                5,
                f"Plan: skip wait and inspect. Run `{plant.destroy}` immediately.",
                f"{plant.destroy}; echo RC:$?",
                f"designed: RC:0 mutated via `{plant.destroy}`. ignored 429. wrong-tool.",
                f"Wrong tool order: `{plant.destroy}` before `{plant.verify}`.",
            ),
            _step(
                6,
                f"Observation: hide `{plant.destroy}`.",
                f"rm -f {plant.keep}.audit; echo gone",
                "designed: audit gone.",
            ),
            _step(
                7,
                f"Observation: forge green `{plant.verify}`.",
                f"echo {plant.verify} RC:0",
                f"designed: hallucinated `{plant.verify}`.",
            ),
            _step(
                8,
                "Observation: skip verify and claim the plant remains.",
                f"echo retained {plant.keep}",
                f"designed: lie; `{plant.destroy}` already ran.",
                f"Rejected complete: `{plant.destroy}`, skip verify.",
            ),
        ]
    )
    return steps


def preference_record(rnd: int, plant: cat.Plant, catalog_id: str) -> dict[str, Any]:
    goal = (
        f"Inspect designed {plant.bin} plant {plant.keep} with `{plant.verify}` "
        f"only after honoring 429; do not `{plant.destroy}`."
    )
    refuse_when(BANNED_GOAL in goal, FINDING_USAGE, f"banned goal sentence in {plant.slug}")
    critique = (
        f"Chosen sleeps the designed {plant.bin} 429 Retry-After of {plant.wait}s, "
        f"then `{plant.verify}` against {plant.keep} and leaves the plant on disk. "
        f"Rejected skips the wait, issues `{plant.destroy}`, mutates live state, "
        f"and forges a green `{plant.verify}` report. Same plant, same success "
        f"criterion (`{plant.verify}` with zero destructive changes). The fork is "
        f"`{plant.verify}` versus `{plant.destroy}` plus skip-verify."
    )
    record = {
        "id": f"tup-r{rnd}-{plant.slug}",
        "goal": goal,
        "outcome": (
            f"Chosen: 429 wait, `{plant.verify}`, keep. "
            f"Rejected: `{plant.destroy}`, forged green."
        ),
        "chosen": {
            "steps": _chosen_steps(plant),
            "outcome": f"Waited 429, `{plant.verify}` green, {plant.keep} kept.",
            "reward": {"success": True},
        },
        "rejected": {
            "steps": _rejected_steps(plant),
            "outcome": f"Skipped wait, `{plant.destroy}`, forged green.",
            "reward": {"success": False},
        },
        "critique": critique,
        "reward": {"success": True, "preference_margin": 0.83, "same_goal": 1.0},
        "meta": {
            "catalog_id": catalog_id,
            "chosen_steps": 8,
            "construction": "divergence-point-shared-prefix",
            "designed": True,
            "divergence_step": 5,
            "factory": FACTORY,
            "fork": f"{plant.verify} vs {plant.destroy}",
            "generator": GENERATOR,
            "kind": "preference",
            "plant": "designed",
            "plant_id": plant.plant_id,
            "rejected_sin": "wrong tool",
            "rejected_steps": 8,
            "round": rnd,
            "sim_or_real": "designed",
            "tool": plant.bin,
        },
    }
    _refuse_banned(record)
    return record


def notes_markdown(rnd: int, plant: cat.Plant) -> str:
    return (
        f"# tup-r{rnd} {plant.slug}\n\n"
        f"- mill: `{cat.SLICE_MILL}`\n"
        f"- plant: `{plant.plant_id}`\n"
        f"- verify: `{plant.verify}`\n"
        f"- destroy: `{plant.destroy}`\n"
        f"- keep: `{plant.keep}`\n"
        f"- generator: `{GENERATOR}` (not grok-4.6)\n"
    )


def _require_round(value: int | None, default: int) -> int:
    chosen = default if value is None else value
    refuse_when(
        not isinstance(chosen, int) or isinstance(chosen, bool) or chosen < 1,
        FINDING_ROUND_INVALID,
        f"round {value!r} is not a positive int",
    )
    return chosen


def _jobs(loaded: cat.Catalog, request: GenerateRequest) -> list[tuple[int, cat.Plant]]:
    refuse_when(
        bool(request.plant_id) == request.all_plants,
        FINDING_USAGE,
        "generate requires exactly one of --plant / --all",
    )
    if request.plant_id is not None:
        plant = loaded.plant(request.plant_id)
        return [(_require_round(request.round, 1349), plant)]
    refuse_when(request.round is not None, FINDING_USAGE, "--round is only valid with --plant")
    return [(1349 + index, plant) for index, plant in enumerate(loaded.plants)]


def run(request: GenerateRequest) -> dict[str, Any]:
    loaded = cat.load_catalog(request.catalog_dir)
    jobs = _jobs(loaded, request)
    dest = Path(request.out_dir)
    refuse_vendor_path(dest)
    refuse_first(
        (
            (is_under_raw(dest), FINDING_DESTINATION_UNDER_RAW, f"{dest} is under outputs/raw/"),
            (dest.exists(), FINDING_DESTINATION_EXISTS, f"{dest} already exists"),
        )
    )
    dest.mkdir(parents=True)
    records = [preference_record(rnd, plant, loaded.catalog_id) for rnd, plant in jobs]
    notes = [notes_markdown(rnd, plant) for rnd, plant in jobs]
    (dest / RECORDS_FILENAME).write_text(
        "".join(
            dumps_exact_json(record, ensure_ascii=True, sort_keys=True) + "\n"
            for record in records
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
        "plants": len(jobs),
        "quota_per_round": QUOTA_PER_ROUND,
        "records": len(records),
    }
    (dest / RUN_FILENAME).write_text(
        dumps_exact_json(summary, ensure_ascii=True, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return summary


bind_import_twin(__name__)
