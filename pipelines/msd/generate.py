#!/usr/bin/env python3
"""Emit success/handoff episode pairs from a pinned MSD catalog.

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
    DECISION_PREFIXES,
    FACTORY,
    FINDING_BANNED_KEY,
    FINDING_DESTINATION_EXISTS,
    FINDING_DESTINATION_UNDER_RAW,
    FINDING_ROUND_INVALID,
    FINDING_USAGE,
    GENERATOR,
    MsdRefusal,
    NOTES_FILENAME,
    NOVEL_COVERAGE,
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
        raise MsdRefusal(FINDING_BANNED_KEY, f"record {record.get('id')!r} carries {hits[0]}")


def _clip(text: str, limit: int = 240) -> str:
    compact = " ".join(text.split())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 1].rstrip() + "…"


def _step(
    n: int,
    basis: str,
    name: str,
    args: dict[str, str],
    observation: str,
    reflection: str | None = None,
) -> dict[str, Any]:
    clipped = _clip(basis)
    if not clipped.startswith(DECISION_PREFIXES):
        raise MsdRefusal(FINDING_USAGE, f"step {n} decision_basis lacks a reviewed prefix")
    step = {
        "n": n,
        "decision_basis": clipped,
        "tool_call": {"name": name, "args": args},
        "observation": observation,
    }
    if reflection:
        step["reflection"] = reflection
    return step


def _paths(plant: cat.Plant) -> dict[str, str]:
    pfx = plant.pfx
    return {
        "schema": f"spec/{pfx}.schema.json",
        "server": f"src/server/{pfx}.go",
        "host": f"src/host/continue/{pfx}.ts",
        "test_py": f"tests/contract/test_{pfx}_json.py",
        "canon": f"src/server/{pfx}_canon.go",
        "ticket": f"tickets/{plant.ticket}.md",
    }


def _extra_test(plant: cat.Plant) -> str:
    return f"test_extra_{plant.extra.replace(' ', '_')}_allowed"


def _canon_tail(plant: cat.Plant) -> str:
    name = plant.canon
    return name[5:] if name.startswith("Canon") else name


def _contract_obs(plant: cat.Plant, extra_test: str) -> str:
    test_py = _paths(plant)["test_py"]
    return f"{test_py}::test_{plant.pfx}_ok PASSED\n{test_py}::{extra_test} PASSED"


def _deadend_edit(path: str, spec: str, deadend: str) -> dict[str, str]:
    return {
        "path": path,
        "old": f"if missing({spec!r})",
        "new": f"// dead-end: {deadend}",
    }


def _wire_edit(path: str, deadend: str, canon: str) -> dict[str, str]:
    return {
        "path": path,
        "old": f"// dead-end: {deadend}",
        "new": f"m = {canon}(m)",
    }


def _canon_src(plant: cat.Plant) -> str:
    return (
        f"func {plant.canon}(in map[string]any) map[string]any {{\n"
        f"  // {plant.leftover} → {plant.spec}\n"
        f"  // keep {plant.keep}; do not {plant.deadend}\n"
        f"  return in\n"
        f"}}\n"
    )


def _success_steps(plant: cat.Plant) -> list[dict[str, Any]]:
    path = _paths(plant)
    leftover, spec, keep, deadend = plant.leftover, plant.spec, plant.keep, plant.deadend
    extra_test = _extra_test(plant)
    return [
        _step(
            1,
            f"Plan: locate Map {leftover} leftover → {spec}; keep {keep}.",
            "bash",
            {"command": "ls -la spec src/server src/host/continue tests | sed -n '1,50p'"},
            f"{path['schema']}  {path['server']}  {path['host']}  {path['test_py']}",
        ),
        _step(
            2,
            "Observation: files present (step 1). Grep the before/after tokens.",
            "grep",
            {"path": ".", "pattern": plant.grep},
            f"{path['schema']}: {plant.method} {spec} required; {leftover} leftover removed",
        ),
        _step(
            3,
            "Observation: drift confirmed (step 2). Read schema.",
            "read",
            {"path": path["schema"]},
            f"{spec}: required\n{plant.schema_note}\n# keep {keep}",
        ),
        _step(
            4,
            "Observation: schema closed (step 3). Diff versus origin/main.",
            "bash",
            {"command": f"git diff origin/main -- {path['schema']} {path['host']}"},
            f"- {leftover}\n+ {spec}\n# Continue still {plant.freeze_still}",
        ),
        _step(
            5,
            "Observation: spec new; host still old (step 4). Run contract tests.",
            "bash",
            {"command": f"pytest {path['test_py']} -q --tb=short"},
            _contract_obs(plant, extra_test),
            f"False-green: extra {plant.extra} dropped.",
        ),
        _step(
            6,
            "Observation: JSON pins reject the old shape (step 5). Run RPC golden.",
            "bash",
            {"command": f"go test ./tests/rpc -run {_canon_tail(plant)} -count=1 -v"},
            f"Test{_canon_tail(plant)}Map FAIL missing {spec}; "
            f"Test{_canon_tail(plant)}Keep PASS",
        ),
        _step(
            7,
            "Observation: old shape -32602 (step 6). Dead-end — apply the wrong compensation.",
            "edit",
            _deadend_edit(path["server"], spec, deadend),
            f"{deadend} applied. Golden wants {spec}.",
        ),
        _step(
            8,
            "Observation: dead-end applied (step 7). Re-run RPC.",
            "bash",
            {"command": f"go test ./tests/rpc -run {_canon_tail(plant)} -count=1"},
            f"Test{_canon_tail(plant)}Keep: got {deadend} want {spec}\nFAIL",
            f"Dead-end: Do not {deadend}. {plant.adapt_cmd}; keep {keep}.",
        ),
        _step(
            9,
            f"Reflection: revert dead-end (steps 7-8). {plant.adapt_cmd}; keep {keep}.",
            "write",
            {"path": path["canon"], "contents": _canon_src(plant)},
            f"wrote {plant.canon}: {leftover}→{spec}; {keep} kept.",
        ),
        _step(
            10,
            "Observation: canon written (step 9). Wire ingest.",
            "edit",
            _wire_edit(path["server"], deadend, plant.canon),
            f"ingest maps {plant.method}; {keep} remains.",
        ),
        _step(
            11,
            "Observation: wired (step 10). Flip the reject fixture.",
            "edit",
            {
                "path": path["test_py"],
                "old": "assert r.status_code == 400",
                "new": "assert r.status_code == 200",
            },
            f"{leftover} now mapped to {spec}; {keep} kept.",
        ),
        _step(
            12,
            "Observation: fixture flipped (step 11). Re-run contract + RPC.",
            "bash",
            {"command": f"pytest {path['test_py']} -q; go test ./tests/rpc ./src/server -count=1"},
            "pytest: 3 passed; Map PASS; Keep PASS; go: 6 passed",
        ),
        _step(
            13,
            "Observation: tests green (step 12). Confirm dead-end is gone.",
            "bash",
            {"command": f"rg -n {deadend!r} {path['server']} || echo 'no wipe'"},
            "no wipe",
        ),
        _step(
            14,
            "Observation: leftover gone (step 13). Extra-field still allowed.",
            "read",
            {"path": path["test_py"]},
            f"def {extra_test}  # additionalProperties leftover",
        ),
        _step(
            15,
            f"Observation: residual documented (step 14). Do not {deadend}.",
            "bash",
            {"command": f"rg -n '{plant.canon}' {path['canon']}"},
            f"{leftover} → {spec}; allowlist keeps {keep}",
        ),
        _step(
            16,
            "Observation: last check (step 15). Done.",
            "bash",
            {"command": f"pytest {path['test_py']} -q -k extra"},
            "1 passed",
            f"Residual: extra {plant.extra} isolated; {plant.adapt_cmd}.",
        ),
    ]


def _fail_steps(plant: cat.Plant) -> list[dict[str, Any]]:
    path = _paths(plant)
    leftover, spec, keep, deadend = plant.leftover, plant.spec, plant.keep, plant.deadend
    extra_test = _extra_test(plant)
    return [
        _step(
            1,
            f"Plan: locate Buffer {leftover} leftover→{spec}, host, and freeze ticket.",
            "bash",
            {"command": "ls -la spec src/server src/host/continue tests tickets | sed -n '1,50p'"},
            f"{path['schema']}  {path['host']}  {path['ticket']}",
        ),
        _step(
            2,
            "Observation: files present (step 1). Grep the before/after tokens.",
            "grep",
            {"path": ".", "pattern": plant.grep},
            f"{path['host']}: {plant.freeze_still}",
        ),
        _step(
            3,
            "Observation: drift confirmed (step 2). Read schema.",
            "read",
            {"path": path["schema"]},
            f"{plant.method} requires {spec}\n{plant.schema_note}",
        ),
        _step(
            4,
            "Observation: schema closed (step 3). Diff versus origin/main.",
            "bash",
            {"command": f"git diff origin/main -- {path['schema']} {path['host']}"},
            f"- {leftover}\n+ {spec}\n# Continue still {plant.freeze_still}",
        ),
        _step(
            5,
            "Observation: spec new; host still old (step 4). Run contract.",
            "bash",
            {"command": f"pytest {path['test_py']} -q --tb=short"},
            _contract_obs(plant, extra_test),
            f"False-green: extra {plant.extra} dropped.",
        ),
        _step(
            6,
            "Observation: JSON only tests the new shape (step 5). Run compensate golden.",
            "bash",
            {"command": f"go test ./tests/rpc -run {_canon_tail(plant)} -count=1 -v"},
            f"Test{_canon_tail(plant)}Buffer FAIL got old {leftover} want {spec}",
        ),
        _step(
            7,
            "Observation: old shape rejected (step 6). Dead-end — apply the wrong compensation.",
            "edit",
            _deadend_edit(path["server"], spec, deadend),
            f"{deadend} applied. Golden wants {spec}.",
        ),
        _step(
            8,
            "Observation: dead-end applied (step 7). Re-run golden.",
            "bash",
            {"command": f"go test ./tests/rpc -run {_canon_tail(plant)} -count=1"},
            f"Test{_canon_tail(plant)}Buffer: got {deadend} want {spec}\nFAIL",
            f"Dead-end: Do not {deadend}. {plant.adapt_cmd}; keep {keep}.",
        ),
        _step(
            9,
            f"Reflection: revert dead-end (steps 7-8). {plant.adapt_cmd}; keep {keep}.",
            "write",
            {"path": path["canon"], "contents": _canon_src(plant)},
            f"wrote {plant.canon}: {leftover}→{spec}; {keep} kept.",
        ),
        _step(
            10,
            "Observation: canon written (step 9). Read freeze ticket.",
            "read",
            {"path": path["ticket"]},
            f"# {plant.ticket} Continue {plant.method} still {plant.freeze_still}\nStatus: OPEN",
        ),
        _step(
            11,
            "Observation: host freeze still old shape (step 10). Wire server; leave Continue.",
            "edit",
            _wire_edit(path["server"], deadend, plant.canon),
            f"server maps {plant.method}; Continue left frozen.",
        ),
        _step(
            12,
            "Observation: wired (step 11). Re-run golden + contract.",
            "bash",
            {"command": f"go test ./tests/rpc ./src/server -count=1; pytest {path['test_py']} -q"},
            "Buffer PASS; pytest: 2 passed; go: 6 passed",
        ),
        _step(
            13,
            "Observation: tests green (step 12). Confirm host still old.",
            "bash",
            {"command": f"rg -n {spec!r} {path['host']} || true"},
            f"{path['host']}: {plant.freeze_still}",
        ),
        _step(
            14,
            "Observation: host still old (step 13). Do not edit freeze file.",
            "read",
            {"path": path["ticket"]},
            f"Blocked: Continue still {plant.freeze_still}.",
        ),
        _step(
            15,
            "Observation: ticket OPEN (step 14). Extra-field still 200.",
            "read",
            {"path": path["test_py"]},
            f"def {extra_test}  # additionalProperties leftover",
        ),
        _step(
            16,
            "Observation: residual documented (step 15). Host freeze remains.",
            "bash",
            {"command": f"rg -n '{plant.canon}' {path['canon']} {path['host']}"},
            f"{path['canon']}: {leftover}→{spec}\n"
            f"{path['host']}: still {plant.freeze_still} (freeze)",
        ),
        _step(
            17,
            f"Observation: ticket open (step 16). Do not {deadend}.",
            "bash",
            {"command": "echo HANDOFF"},
            "HANDOFF",
            f"Failed: host freeze still {plant.freeze_still}; extra {plant.extra}.",
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
        "id": f"msd-r{rnd:04d}-{plant.slug}-q",
        "goal": (
            f"{plant.repo} {plant.method} renamed {plant.leftover} leftover to {plant.spec} "
            f"(not {plant.not_r}). Continue still {plant.freeze_still}. JSON extra-field "
            f"tests stay green. {plant.adapt_cmd}; keep {plant.keep}; do not {plant.deadend}."
        ),
        "plan": (
            f"Prove {plant.leftover} leftover vs {plant.spec}, reject {plant.deadend}, "
            f"{plant.canon}, leave extra {plant.extra}."
        ),
        "steps": _success_steps(plant),
        "outcome": (
            f"Ingest {plant.canon} maps {plant.leftover} leftover to {plant.spec} and "
            f"keeps {plant.keep}. {plant.deadend} dead-end rejected. extra {plant.extra} "
            f"remains false-green. go 8/8, contract 4/4. Do not {plant.deadend}."
        ),
        "reward": {
            "success": True,
            "deadend_rejected": 1,
            "extra_false_green": 1,
            "tests_passed": 12,
            "cost_steps": 16,
        },
        "meta": _meta(rnd, plant, catalog_id),
    }
    _refuse_banned(record)
    return record


def fail_episode(rnd: int, plant: cat.Plant, catalog_id: str) -> dict[str, Any]:
    record = {
        "id": f"msd-r{rnd:04d}-{plant.slug}-handoff",
        "goal": (
            f"{plant.repo} {plant.method} now requires {plant.spec} (not {plant.not_r}). "
            f"Continue freeze still {plant.freeze_still}. JSON extra-field tests stay green. "
            f"{plant.adapt_cmd}; keep {plant.keep}; do not {plant.deadend}."
        ),
        "plan": (
            f"Prove {plant.leftover} leftover vs {plant.spec}, reject {plant.deadend}, "
            f"{plant.canon}, leave Continue on {plant.ticket} if freeze still "
            f"{plant.freeze_still}."
        ),
        "steps": _fail_steps(plant),
        "outcome": (
            f"Server {plant.canon} maps {plant.leftover} leftover to {plant.spec}. "
            f"{plant.deadend} rejected. Continue freeze still {plant.freeze_still} — "
            f"{plant.ticket} OPEN. extra {plant.extra} remains false-green. Host freeze "
            f"remains so partial. Do not {plant.deadend}."
        ),
        "reward": {
            "success": False,
            "handoff": 1,
            "host_frozen": 1,
            "extra_false_green": 1,
            "tests_passed": 8,
            "cost_steps": 17,
        },
        "meta": _meta(rnd, plant, catalog_id),
    }
    _refuse_banned(record)
    return record


def notes_markdown(rnd: int, plant: cat.Plant) -> str:
    return (
        f"# NOTES r{rnd}\n\n"
        f"Novel coverage: {NOVEL_COVERAGE}\n\n"
        f"- plant: {plant.repo} {plant.method} {plant.leftover} leftover→{plant.spec}\n"
        f"- family: {plant.family} (not {plant.not_r})\n"
        f"- success: {plant.canon} keep `{plant.keep}`; reject `{plant.deadend}`\n"
        f"- fail: Continue freeze still `{plant.freeze_still}` handoff `{plant.ticket}`\n"
    )


def _require_round(value: int | None, default: int) -> int:
    rnd = default if value is None else value
    if not isinstance(rnd, int) or isinstance(rnd, bool) or rnd < 1:
        raise MsdRefusal(FINDING_ROUND_INVALID, f"round must be a positive int, got {value!r}")
    return rnd


def _jobs(loaded: cat.Catalog, request: GenerateRequest) -> list[tuple[int, cat.Plant]]:
    selectors = (request.plant_id is not None, request.mill_id is not None, request.all_plants)
    if sum(selectors) != 1:
        raise MsdRefusal(FINDING_USAGE, "exactly one of plant_id, mill_id, or all_plants")
    if request.plant_id is not None:
        plant = loaded.plant(request.plant_id)
        return [(_require_round(request.round, plant.base_round), plant)]
    if request.round is not None:
        raise MsdRefusal(FINDING_USAGE, "round applies only with plant_id")
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
        raise MsdRefusal(FINDING_DESTINATION_UNDER_RAW, f"{out_dir} names or aliases the raw tree")
    if out_dir.exists():
        raise MsdRefusal(FINDING_DESTINATION_EXISTS, f"{out_dir} already exists")


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
