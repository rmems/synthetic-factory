#!/usr/bin/env python3
"""Emit designed CEI episode pairs from a pinned catalog.

Writes a brand-new destination (records.jsonl, RUN.json, NOTES.md). Refuses
an existing path and any path that names or aliases ``outputs/raw/``. Does
not hop factories, does not shell out to ``round_txn``, and does not stamp
``grok-4.6``. Episode shape matches hopper ``build_success`` / ``build_fail``
from the legacy lane (16-step success + 17-step handoff).
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
    DECISION_PREFIXES,
    FACTORY,
    FINDING_BANNED_ID,
    FINDING_BANNED_KEY,
    FINDING_DESTINATION_EXISTS,
    FINDING_DESTINATION_UNDER_RAW,
    FINDING_GOAL_INVALID,
    FINDING_ROUND_INVALID,
    FINDING_USAGE,
    GENERATOR,
    MILL_PREFIX,
    NOTES_FILENAME,
    QUOTA_PER_ROUND,
    RECORDS_FILENAME,
    RUN_FILENAME,
    RUN_FORMAT,
    CeiRefusal,
    bind_import_twin,
    dumps_exact_json,
    is_under_raw,
)

__all__ = [
    "GenerateRequest",
    "NOTES_FILENAME",
    "RECORDS_FILENAME",
    "RUN_FILENAME",
    "build_fail",
    "build_success",
    "notes_markdown",
    "pair_records",
    "run",
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
        raise CeiRefusal(FINDING_BANNED_KEY, f"record {record.get('id')!r} carries {hits[0]}")
    record_id = record.get("id")
    if isinstance(record_id, str):
        for prefix in BANNED_ID_PREFIXES:
            if record_id.startswith(prefix):
                raise CeiRefusal(FINDING_BANNED_ID, f"record id {record_id!r} uses {prefix}")
    if record.get("meta", {}).get("generator") == "grok-4.6":
        raise CeiRefusal(FINDING_BANNED_KEY, "record stamps grok-4.6")
    if record.get("meta", {}).get("sim_or_real") == "real":
        raise CeiRefusal(FINDING_BANNED_KEY, "record stamps sim_or_real real")


def _goal_ok(goal: str) -> None:
    lowered = goal.strip().lower()
    if not goal.strip() or lowered in {"x", "placeholder", "todo", "tbd", "fix it"}:
        raise CeiRefusal(FINDING_GOAL_INVALID, f"placeholder goal: {goal!r}")
    if "[variant" in lowered:
        raise CeiRefusal(FINDING_GOAL_INVALID, f"variant stamp in goal: {goal!r}")


def _step(
    n: int,
    decision_basis: str,
    tool_call: dict[str, Any],
    observation: str,
    reflection: str,
) -> dict[str, Any]:
    if not decision_basis.startswith(DECISION_PREFIXES):
        raise CeiRefusal(FINDING_USAGE, f"step {n} decision_basis prefix: {decision_basis!r}")
    if len(decision_basis) > 240:
        raise CeiRefusal(FINDING_USAGE, f"step {n} decision_basis {len(decision_basis)} > 240")
    if not observation.strip() or not reflection.strip():
        raise CeiRefusal(FINDING_USAGE, f"step {n} empty observation/reflection")
    return {
        "n": n,
        "decision_basis": decision_basis,
        "tool_call": tool_call,
        "observation": observation,
        "reflection": reflection,
    }


def _bash(command: str) -> dict[str, Any]:
    return {"name": "bash", "args": {"command": command}}


def _read(path: str) -> dict[str, Any]:
    return {"name": "read", "args": {"path": path}}


def _edit(path: str, old: str, new: str) -> dict[str, Any]:
    return {"name": "edit", "args": {"path": path, "old": old, "new": new}}


def _pytest(args: str) -> dict[str, Any]:
    return {"name": "pytest", "args": {"args": args}}


def _fetch(url: str) -> dict[str, Any]:
    return {"name": "fetch", "args": {"url": url}}


def _paths(side: cat.Side) -> tuple[str, str, str]:
    src = f"src/{side.mod}.py"
    test = f"tests/test_{side.mod}.py"
    cfg = f"{side.mod}/cfg.yml"
    return src, test, cfg


def _episode_id(round_n: int, slug: str) -> str:
    return f"{MILL_PREFIX}-r{round_n}-{slug}"


def _meta(round_n: int, side: cat.Side, catalog_id: str, plant: cat.Plant) -> dict[str, Any]:
    return {
        "catalog_id": catalog_id,
        "designed": True,
        "domain": side.domain,
        "factory": FACTORY,
        "generator": GENERATOR,
        "kind": "episode",
        "mill_id": plant.mill_id,
        "plant_id": plant.plant_id,
        "round": round_n,
        "seed": side.seed,
        "stack": side.stack,
    }


def build_success(
    round_n: int,
    side: cat.Side,
    catalog_id: str,
    plant: cat.Plant,
) -> dict[str, Any]:
    """16-step success episode. Hopper-faithful; generator is ``cei-mill``."""

    _goal_ok(side.goal)
    src, test, cfg = _paths(side)
    eid = _episode_id(round_n, side.slug)
    listing = f"{src} {cfg}\n{test}"
    pytest_args = f"{test} -q --tb=short"
    fail_obs = f"{test}::{side.test_fn} FAILED\nE   {side.fail_msg}"
    still_obs = f"{test}::{side.test_fn} FAILED\nE   {side.still_msg}"
    steps = [
        _step(
            1,
            f"Plan: list src {side.mod} and tests before touching conversion or config.",
            _bash(f"ls -la src {side.mod} tests | head -40"),
            listing,
            f"Tree shows {src} plus tests. Run the named failing target next.",
        ),
        _step(
            2,
            (
                "Observation: listing named the test files. "
                f"Run `{pytest_args}` to capture the failure."
            ),
            _pytest(pytest_args),
            fail_obs,
            f"Failure is at {test}::{side.test_fn}. Read that test before a one-line fix.",
        ),
        _step(
            3,
            f"Observation: {test}::{side.test_fn} is red. Read {test} around the assertion.",
            _read(test),
            side.test_body,
            "Test contract is visible. Search implementation symbols next.",
        ),
        _step(
            4,
            "Observation: test file imported the production helper. Grep those symbols.",
            _bash(f"rg -n '{side.grep_pat}' src {side.mod} tests"),
            side.grep_hit,
            f"Grep hit {src}. Read it before editing the first match.",
        ),
        _step(
            5,
            f"Observation: grep listed {src}. Read it before any patch.",
            _read(src),
            side.src_body,
            "First read done. Fetch vendor docs next; do not patch on a hunch yet.",
        ),
        _step(
            6,
            "Observation: local files are in. Need the changelog/registry before editing.",
            _fetch(side.docs_url),
            f"GET {side.docs_url}\nHTTP/1.1 502 Bad Gateway\nBad Gateway.",
            "Call failed with upstream gateway failure. Recover with backoff.",
        ),
        _step(
            7,
            (
                "Observation: the prior call returned an upstream gateway failure. "
                "Retry once with 2s backoff."
            ),
            _fetch(side.docs_url),
            (
                f"retry after 2s backoff; local vendor fixture\n"
                f"HTTP/1.1 200 OK\n{side.docs_ok}"
            ),
            "Degraded path used the local fixture. Continue with that content.",
        ),
        _step(
            8,
            "Observation: local files are in. Need the second remote document before editing.",
            _fetch(side.docs_url2),
            (
                f"GET {side.docs_url2}\nHTTP/1.1 429 Too Many Requests\n"
                "Retry-After: 5\nX-RateLimit-Remaining: 0"
            ),
            "Call failed with rate-limit status with Retry-After. Recover with backoff.",
        ),
        _step(
            9,
            (
                "Observation: the prior call returned rate-limit status with Retry-After. "
                "Sleep then retry."
            ),
            _fetch(side.docs_url2),
            f"sleep + jitter retry of the same URL\nHTTP/1.1 200 OK\n{side.docs_ok2}",
            "Retry succeeded. Resume the local debug plan with that document in hand.",
        ),
        _step(
            10,
            f"Observation: docs and source are in. Apply the first patch to {src}.",
            _edit(src, side.first_old, side.first_new),
            side.first_obs,
            "Patch applied. Re-run the failing test; do not assume green.",
        ),
        _step(
            11,
            f"Observation: edit wrote {src}. Re-run the same failing node.",
            _pytest(pytest_args),
            still_obs,
            "Still red after the first patch. Re-read the implementation; hypothesis is wrong.",
        ),
        _step(
            12,
            f"Observation: post-edit test still failed ({test}::{side.test_fn}). Re-read {src}.",
            _read(src),
            side.reread_obs,
            f"Plan change: {side.plan_change}",
        ),
        _step(
            13,
            f"Reflection: {side.plan_change}"[:240],
            _edit(src, side.first_new, side.fix_new),
            side.fix_obs,
            "Corrective patch applied. Run the original failing node again.",
        ),
        _step(
            14,
            "Observation: fix edit returned clean. Re-run the original failing test node.",
            _pytest(pytest_args),
            "1 passed in 0.16s",
            "Result recorded. Run one broader check before declaring the outcome.",
        ),
        _step(
            15,
            f"Observation: focused run finished. Run broader check `pytest {test} -q`.",
            _bash(f"pytest {test} -q"),
            "3 passed in 0.28s",
            "Broader check captured. Stop; residual risk belongs in the outcome text.",
        ),
        _step(
            16,
            (
                "Observation: broader check is on disk. "
                "Show the diff of patched files for the handoff note."
            ),
            _bash("git diff --stat | head -n 40"),
            f"diffstat for {side.slug}: {src} | 9 ++++++---. No other modified paths.",
            "Diff is the review artifact. No further edits.",
        ),
    ]
    record = {
        "id": eid,
        "goal": side.goal,
        "plan": side.plan,
        "steps": steps,
        "outcome": side.outcome,
        "reward": {
            "success": True,
            "tests_passed": 3,
            "retries": 2,
            "duration_min": 610,
            "wasted_calls": 180,
            "cost_steps": 16,
            "plan_changes": 1,
        },
        "meta": _meta(round_n, side, catalog_id, plant),
    }
    if len(steps) != 16:
        raise CeiRefusal(FINDING_USAGE, f"{eid} expected 16 steps")
    _refuse_banned(record)
    return record


def build_fail(
    round_n: int,
    side: cat.Side,
    catalog_id: str,
    plant: cat.Plant,
) -> dict[str, Any]:
    """17-step handoff episode. Hopper-faithful; generator is ``cei-mill``."""

    _goal_ok(side.goal)
    if not side.ticket:
        raise CeiRefusal(FINDING_USAGE, f"{side.slug} handoff missing ticket")
    src, test, cfg = _paths(side)
    eid = _episode_id(round_n, side.slug)
    ticket = side.ticket
    ticket_path = f"{side.mod}/handoff.md"
    listing = f"{src} {cfg}\n{test}"
    pytest_args = f"{test} -q --tb=short"
    fail_obs = f"{test}::{side.test_fn} FAILED\nE   {side.fail_msg}"
    still_obs = f"{test}::{side.test_fn} FAILED\nE   {side.still_msg}"
    steps = [
        _step(
            1,
            f"Plan: list src {side.mod} and tests before touching conversion or config.",
            _bash(f"ls -la src {side.mod} tests | head -40"),
            listing,
            f"Tree shows {src} plus tests. Run the named failing target next.",
        ),
        _step(
            2,
            (
                "Observation: listing named the test files. "
                f"Run `{pytest_args}` to capture the failure."
            ),
            _pytest(pytest_args),
            fail_obs,
            f"Failure is at {test}::{side.test_fn}. Read that test before a one-line fix.",
        ),
        _step(
            3,
            f"Observation: {test}::{side.test_fn} is red. Read {test} around the assertion.",
            _read(test),
            side.test_body,
            "Test contract is visible. Search implementation symbols next.",
        ),
        _step(
            4,
            "Observation: test file imported the production helper. Grep those symbols.",
            _bash(f"rg -n '{side.grep_pat}' src {side.mod} tests"),
            side.grep_hit,
            f"Grep hit {src}. Read it before editing the first match.",
        ),
        _step(
            5,
            f"Observation: grep listed {src}. Read it before any patch.",
            _read(src),
            side.src_body,
            "First read done. Fetch vendor docs next; do not patch on a hunch yet.",
        ),
        _step(
            6,
            "Observation: local files are in. Need the changelog/registry before editing.",
            _fetch(side.docs_url),
            (
                f"GET {side.docs_url}\nHTTP/1.1 429 Too Many Requests\n"
                "Retry-After: 6\nX-RateLimit-Remaining: 0"
            ),
            "Call failed with rate-limit status with Retry-After. Recover with backoff.",
        ),
        _step(
            7,
            (
                "Observation: the prior call returned rate-limit status with Retry-After. "
                "Sleep then retry."
            ),
            _fetch(side.docs_url),
            f"sleep + jitter retry of the same URL\nHTTP/1.1 200 OK\n{side.docs_ok}",
            "Retry succeeded. Continue with that document.",
        ),
        _step(
            8,
            "Observation: local files are in. Need the second remote document before editing.",
            _fetch(side.docs_url2),
            f"GET {side.docs_url2}\nHTTP/1.1 502 Bad Gateway\nBad Gateway.",
            "Call failed with upstream gateway failure. Recover with backoff.",
        ),
        _step(
            9,
            (
                "Observation: the prior call returned an upstream gateway failure. "
                "Retry once with 2s backoff."
            ),
            _fetch(side.docs_url2),
            (
                f"retry after 2s backoff; local vendor fixture\n"
                f"HTTP/1.1 200 OK\n{side.docs_ok2}"
            ),
            "Degraded path used the local fixture. Resume the local debug plan.",
        ),
        _step(
            10,
            f"Observation: docs and source are in. Apply the first patch to {src}.",
            _edit(src, side.first_old, side.first_new),
            side.first_obs,
            "Patch applied. Re-run the failing test; do not assume green.",
        ),
        _step(
            11,
            f"Observation: edit wrote {src}. Re-run the same failing node.",
            _pytest(pytest_args),
            still_obs,
            "Still red after the first patch. Re-read the implementation; hypothesis is wrong.",
        ),
        _step(
            12,
            f"Observation: post-edit test still failed ({test}::{side.test_fn}). Re-read {src}.",
            _read(src),
            side.reread_obs,
            f"Plan change: {side.plan_change}",
        ),
        _step(
            13,
            f"Reflection: {side.plan_change}"[:240],
            _edit(ticket_path, "", f"# {ticket} {side.ticket_why}"),
            side.fix_obs,
            "Handoff ticket written. Run the original failing node again.",
        ),
        _step(
            14,
            "Observation: handoff edit returned clean. Re-run the original failing test node.",
            _pytest(pytest_args),
            f"{test}::{side.test_fn} FAILED  # handoff: {ticket}\n1 failed",
            "Result recorded. Run one broader check before declaring the outcome.",
        ),
        _step(
            15,
            (
                "Observation: focused run finished. "
                f"Run broader check `pytest {test} -q; echo {ticket}`."
            ),
            _bash(f"pytest {test} -q; echo {ticket}"),
            f"1 failed, 2 passed\n{ticket}",
            "Broader check captured. Residual risk belongs in the outcome text.",
        ),
        _step(
            16,
            (
                "Observation: broader check is on disk. "
                "Show the diff of patched files for the handoff note."
            ),
            _bash("git diff --stat | head -n 40"),
            f"diffstat for {side.slug}: {src} | 8 +++++---. {ticket_path} added.",
            "Diff is the review artifact. Lint next.",
        ),
        _step(
            17,
            "Observation: diffstat listed the patched files. Run a linter on those paths only.",
            _bash("ruff check tests || true; echo lint-end"),
            "All checks passed!\nlint-end",
            "Lint clean. Episode complete.",
        ),
    ]
    record = {
        "id": eid,
        "goal": side.goal,
        "plan": side.plan,
        "steps": steps,
        "outcome": side.outcome,
        "reward": {
            "success": False,
            "tests_passed": 2,
            "retries": 2,
            "duration_min": 640,
            "wasted_calls": 210,
            "cost_steps": 17,
            "plan_changes": 1,
        },
        "meta": _meta(round_n, side, catalog_id, plant),
    }
    if len(steps) != 17:
        raise CeiRefusal(FINDING_USAGE, f"{eid} expected 17 steps")
    _refuse_banned(record)
    return record


def pair_records(round_n: int, plant: cat.Plant, catalog_id: str) -> list[dict[str, Any]]:
    ok = build_success(round_n, plant.ok, catalog_id, plant)
    bad = build_fail(round_n, plant.bad, catalog_id, plant)
    if ok["id"] == bad["id"]:
        raise CeiRefusal(FINDING_USAGE, "duplicate episode ids")
    return [ok, bad]


def notes_markdown(round_n: int, plant: cat.Plant, records: list[dict[str, Any]]) -> str:
    ok, bad = plant.ok, plant.bad
    ok_id, bad_id = records[0]["id"], records[1]["id"]
    cov = max(ok.coverage, bad.coverage)
    return (
        f"# {FACTORY} — NOTES r{round_n}\n\n"
        f"Novel coverage: {cov}%\n\n"
        f"## Episodes\n"
        f"- `{ok_id}`: 16 steps, success=True, domain={ok.domain}, seed={ok.seed}\n"
        f"  - 502 at step 6 recovered 7; 429 at step 8 recovered 9\n"
        f"  - plan change at step 12: {ok.plan_change}\n"
        f"  - edit→test→fail→re-read→fix at steps 10-13\n"
        f"- `{bad_id}`: 17 steps, success=False, domain={bad.domain}, seed={bad.seed}\n"
        f"  - 429 at step 6 recovered 7; 502 at step 8 recovered 9\n"
        f"  - plan change at step 12: {bad.plan_change}\n"
        f"  - edit→test→fail→re-read→fix at steps 10-13\n\n"
        f"## decision_basis audit\n"
        f"Every step has decision_basis starting with Plan:/Observation:/Reflection:/Tool call:, "
        f"length ≤240, no thought/chain_of_thought/scratch/inner_monologue keys, no spike_events, "
        f"no sim_or_real real. Generator {GENERATOR}. No [variant …] goal stamp.\n\n"
        f"## Mix\n"
        f"Success: ['{ok_id}']. Realistic failure/handoff: ['{bad_id}'].\n\n"
        f"## Residual\n"
        f"{ok.residual} {bad.residual}\n"
    )


def _require_round(value: int | None, default: int) -> int:
    rnd = default if value is None else value
    if not isinstance(rnd, int) or isinstance(rnd, bool) or rnd < 1:
        raise CeiRefusal(FINDING_ROUND_INVALID, f"round must be a positive int, got {value!r}")
    return rnd


def _jobs(loaded: cat.Catalog, request: GenerateRequest) -> list[tuple[int, cat.Plant]]:
    selectors = (request.plant_id is not None, request.mill_id is not None, request.all_plants)
    if sum(selectors) != 1:
        raise CeiRefusal(FINDING_USAGE, "exactly one of plant_id, mill_id, or all_plants")
    if request.plant_id is not None:
        plant = loaded.plant(request.plant_id)
        default = plant.base_round + plant.index
        return [(_require_round(request.round, default), plant)]
    if request.round is not None:
        raise CeiRefusal(FINDING_USAGE, "round applies only with plant_id")
    if request.mill_id is not None:
        plants = loaded.mill_plants(request.mill_id)
        mill = next(item for item in loaded.mills if item.mill_id == request.mill_id)
    else:
        plants = loaded.plants
        mill = loaded.mills[0]
    return [(mill.base_round + plant.index, plant) for plant in plants]


def _check_destination(out_dir: Path) -> None:
    if is_under_raw(out_dir):
        raise CeiRefusal(FINDING_DESTINATION_UNDER_RAW, f"{out_dir} names or aliases the raw tree")
    if out_dir.exists():
        raise CeiRefusal(FINDING_DESTINATION_EXISTS, f"{out_dir} already exists")


def run(request: GenerateRequest) -> dict[str, Any]:
    """Generate episode pairs into a new destination. Returns the RUN summary."""

    _check_destination(Path(request.out_dir))
    loaded = cat.load_catalog(request.catalog_dir)
    jobs = _jobs(loaded, request)
    out_dir = Path(request.out_dir)
    out_dir.mkdir(parents=True, exist_ok=False)
    records: list[dict[str, Any]] = []
    note_chunks: list[str] = []
    try:
        for rnd, plant in jobs:
            pair = pair_records(rnd, plant, loaded.catalog_id)
            if len(pair) != QUOTA_PER_ROUND:
                raise CeiRefusal(FINDING_USAGE, f"pair quota is {QUOTA_PER_ROUND}, got {len(pair)}")
            records.extend(pair)
            note_chunks.append(notes_markdown(rnd, plant, pair))
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
    except BaseException:
        for name in (RECORDS_FILENAME, NOTES_FILENAME, RUN_FILENAME):
            path = out_dir / name
            if path.exists():
                path.unlink()
        out_dir.rmdir()
        raise
    return summary


bind_import_twin(__name__)
