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
from typing import Any, NamedTuple

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
    LEFTOVER3_SHAPE,
    MILL_PREFIX,
    NOTES_FILENAME,
    NOVEL_COVERAGE_OK,
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
    "build_leftover3_fail",
    "build_leftover3_success",
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


class _Workspace(NamedTuple):
    """The files one episode works in, as both side shapes present them."""

    mod: str
    src: str
    test: str
    test_fn: str
    test_body: str
    grep_command: str
    grep_hit: str
    src_body: str
    fail_msg: str
    still_msg: str

    @property
    def pytest_args(self) -> str:
        return f"{self.test} -q --tb=short"

    @property
    def node(self) -> str:
        return f"{self.test}::{self.test_fn}"


def _hop_workspace(side: cat.Side) -> _Workspace:
    src, test, _cfg = _paths(side)
    return _Workspace(
        mod=side.mod,
        src=src,
        test=test,
        test_fn=side.test_fn,
        test_body=side.test_body,
        grep_command=f"rg -n '{side.grep_pat}' src {side.mod} tests",
        grep_hit=side.grep_hit,
        src_body=side.src_body,
        fail_msg=side.fail_msg,
        still_msg=side.still_msg,
    )


def _investigation_steps(ws: _Workspace) -> list[dict[str, Any]]:
    """Steps 1-5: list the tree, reproduce the failure, read the test, grep, read the source."""

    return [
        _step(
            1,
            f"Plan: list src {ws.mod} and tests before touching conversion or config.",
            _bash(f"ls -la src {ws.mod} tests | head -40"),
            f"{ws.src} {ws.mod}/cfg.yml\n{ws.test}",
            f"Tree shows {ws.src} plus tests. Run the named failing target next.",
        ),
        _step(
            2,
            (
                "Observation: listing named the test files. "
                f"Run `{ws.pytest_args}` to capture the failure."
            ),
            _pytest(ws.pytest_args),
            f"{ws.node} FAILED\nE   {ws.fail_msg}",
            f"Failure is at {ws.node}. Read that test before a one-line fix.",
        ),
        _step(
            3,
            f"Observation: {ws.node} is red. Read {ws.test} around the assertion.",
            _read(ws.test),
            ws.test_body,
            "Test contract is visible. Search implementation symbols next.",
        ),
        _step(
            4,
            "Observation: test file imported the production helper. Grep those symbols.",
            _bash(ws.grep_command),
            ws.grep_hit,
            f"Grep hit {ws.src}. Read it before editing the first match.",
        ),
        _step(
            5,
            f"Observation: grep listed {ws.src}. Read it before any patch.",
            _read(ws.src),
            ws.src_body,
            "First read done. Fetch vendor docs next; do not patch on a hunch yet.",
        ),
    ]


# Docs fetches sit at steps 6-7 and 8-9; what the agent says depends on which pair it is.
_DOCS_NEED = {
    6: "Observation: local files are in. Need the changelog/registry before editing.",
    8: "Observation: local files are in. Need the second remote document before editing.",
}
_GATEWAY_RESUME = {
    6: "Degraded path used the local fixture. Continue with that content.",
    8: "Degraded path used the local fixture. Resume the local debug plan.",
}
_RATE_LIMIT_RETRY_AFTER = {6: 6, 8: 5}
_RATE_LIMIT_RESUME = {
    6: "Retry succeeded. Continue with that document.",
    8: "Retry succeeded. Resume the local debug plan with that document in hand.",
}


def _gateway_recovery_steps(n: int, url: str, doc: str) -> list[dict[str, Any]]:
    """Step ``n`` fetches ``url`` into a 502; step ``n + 1`` recovers it with backoff."""

    return [
        _step(
            n,
            _DOCS_NEED[n],
            _fetch(url),
            f"GET {url}\nHTTP/1.1 502 Bad Gateway\nBad Gateway.",
            "Call failed with upstream gateway failure. Recover with backoff.",
        ),
        _step(
            n + 1,
            (
                "Observation: the prior call returned an upstream gateway failure. "
                "Retry once with 2s backoff."
            ),
            _fetch(url),
            f"retry after 2s backoff; local vendor fixture\nHTTP/1.1 200 OK\n{doc}",
            _GATEWAY_RESUME[n],
        ),
    ]


def _rate_limit_recovery_steps(n: int, url: str, doc: str) -> list[dict[str, Any]]:
    """Step ``n`` fetches ``url`` into a 429; step ``n + 1`` sleeps and retries it."""

    return [
        _step(
            n,
            _DOCS_NEED[n],
            _fetch(url),
            (
                f"GET {url}\nHTTP/1.1 429 Too Many Requests\n"
                f"Retry-After: {_RATE_LIMIT_RETRY_AFTER[n]}\nX-RateLimit-Remaining: 0"
            ),
            "Call failed with rate-limit status with Retry-After. Recover with backoff.",
        ),
        _step(
            n + 1,
            (
                "Observation: the prior call returned rate-limit status with Retry-After. "
                "Sleep then retry."
            ),
            _fetch(url),
            f"sleep + jitter retry of the same URL\nHTTP/1.1 200 OK\n{doc}",
            _RATE_LIMIT_RESUME[n],
        ),
    ]


def _first_patch_step(ws: _Workspace, patch: dict[str, Any], observation: str) -> dict[str, Any]:
    return _step(
        10,
        f"Observation: docs and source are in. Apply the first patch to {ws.src}.",
        patch,
        observation,
        "Patch applied. Re-run the failing test; do not assume green.",
    )


def _still_red_step(ws: _Workspace) -> dict[str, Any]:
    return _step(
        11,
        f"Observation: edit wrote {ws.src}. Re-run the same failing node.",
        _pytest(ws.pytest_args),
        f"{ws.node} FAILED\nE   {ws.still_msg}",
        "Still red after the first patch. Re-read the implementation; hypothesis is wrong.",
    )


def _reread_step(ws: _Workspace, observation: str, reflection: str) -> dict[str, Any]:
    return _step(
        12,
        f"Observation: post-edit test still failed ({ws.node}). Re-read {ws.src}.",
        _read(ws.src),
        observation,
        reflection,
    )


def _corrective_patch_step(
    plan_change: str, patch: dict[str, Any], observation: str
) -> dict[str, Any]:
    return _step(
        13,
        f"Reflection: {plan_change}"[:240],
        patch,
        observation,
        "Corrective patch applied. Run the original failing node again.",
    )


def _verified_fix_steps(ws: _Workspace, slug: str) -> list[dict[str, Any]]:
    """Steps 14-16 of a success episode: green node, broader check, diffstat."""

    return [
        _step(
            14,
            "Observation: fix edit returned clean. Re-run the original failing test node.",
            _pytest(ws.pytest_args),
            "1 passed in 0.16s",
            "Result recorded. Run one broader check before declaring the outcome.",
        ),
        _step(
            15,
            f"Observation: focused run finished. Run broader check `pytest {ws.test} -q`.",
            _bash(f"pytest {ws.test} -q"),
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
            f"diffstat for {slug}: {ws.src} | 9 ++++++---. No other modified paths.",
            "Diff is the review artifact. No further edits.",
        ),
    ]


def _handoff_ticket_step(
    ws: _Workspace, plan_change: str, ticket_line: str, observation: str
) -> dict[str, Any]:
    return _step(
        13,
        f"Reflection: {plan_change}"[:240],
        _edit(f"{ws.mod}/handoff.md", "", ticket_line),
        observation,
        "Handoff ticket written. Run the original failing node again.",
    )


def _handoff_close_steps(ws: _Workspace, slug: str, ticket: str) -> list[dict[str, Any]]:
    """Steps 14-17 of a handoff episode: still red with the ticket, diffstat, lint."""

    ticket_path = f"{ws.mod}/handoff.md"
    return [
        _step(
            14,
            "Observation: handoff edit returned clean. Re-run the original failing test node.",
            _pytest(ws.pytest_args),
            f"{ws.node} FAILED  # handoff: {ticket}\n1 failed",
            "Result recorded. Run one broader check before declaring the outcome.",
        ),
        _step(
            15,
            (
                "Observation: focused run finished. "
                f"Run broader check `pytest {ws.test} -q; echo {ticket}`."
            ),
            _bash(f"pytest {ws.test} -q; echo {ticket}"),
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
            f"diffstat for {slug}: {ws.src} | 8 +++++---. {ticket_path} added.",
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


def _success_reward() -> dict[str, Any]:
    return {
        "success": True,
        "tests_passed": 3,
        "retries": 2,
        "duration_min": 610,
        "wasted_calls": 180,
        "cost_steps": 16,
        "plan_changes": 1,
    }


def _handoff_reward() -> dict[str, Any]:
    return {
        "success": False,
        "tests_passed": 2,
        "retries": 2,
        "duration_min": 640,
        "wasted_calls": 210,
        "cost_steps": 17,
        "plan_changes": 1,
    }


def _checked_episode(record: dict[str, Any], expected_steps: int) -> dict[str, Any]:
    if len(record["steps"]) != expected_steps:
        raise CeiRefusal(FINDING_USAGE, f"{record['id']} expected {expected_steps} steps")
    _refuse_banned(record)
    return record


def build_success(
    round_n: int,
    side: cat.Side,
    catalog_id: str,
    plant: cat.Plant,
) -> dict[str, Any]:
    """16-step success episode. Hopper-faithful; generator is ``cei-mill``."""

    _goal_ok(side.goal)
    ws = _hop_workspace(side)
    steps = [
        *_investigation_steps(ws),
        *_gateway_recovery_steps(6, side.docs_url, side.docs_ok),
        *_rate_limit_recovery_steps(8, side.docs_url2, side.docs_ok2),
        _first_patch_step(ws, _edit(ws.src, side.first_old, side.first_new), side.first_obs),
        _still_red_step(ws),
        _reread_step(ws, side.reread_obs, f"Plan change: {side.plan_change}"),
        _corrective_patch_step(
            side.plan_change, _edit(ws.src, side.first_new, side.fix_new), side.fix_obs
        ),
        *_verified_fix_steps(ws, side.slug),
    ]
    record = {
        "id": _episode_id(round_n, side.slug),
        "goal": side.goal,
        "plan": side.plan,
        "steps": steps,
        "outcome": side.outcome,
        "reward": _success_reward(),
        "meta": _meta(round_n, side, catalog_id, plant),
    }
    return _checked_episode(record, 16)


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
    ws = _hop_workspace(side)
    ticket = side.ticket
    steps = [
        *_investigation_steps(ws),
        *_rate_limit_recovery_steps(6, side.docs_url, side.docs_ok),
        *_gateway_recovery_steps(8, side.docs_url2, side.docs_ok2),
        _first_patch_step(ws, _edit(ws.src, side.first_old, side.first_new), side.first_obs),
        _still_red_step(ws),
        _reread_step(ws, side.reread_obs, f"Plan change: {side.plan_change}"),
        _handoff_ticket_step(ws, side.plan_change, f"# {ticket} {side.ticket_why}", side.fix_obs),
        *_handoff_close_steps(ws, side.slug, ticket),
    ]
    record = {
        "id": _episode_id(round_n, side.slug),
        "goal": side.goal,
        "plan": side.plan,
        "steps": steps,
        "outcome": side.outcome,
        "reward": _handoff_reward(),
        "meta": _meta(round_n, side, catalog_id, plant),
    }
    return _checked_episode(record, 17)


def _leftover3_paths(side: cat.Leftover3Side) -> tuple[str, str]:
    return f"src/{side.mod}.py", f"tests/test_{side.mod}.py"


def _leftover3_workspace(side: cat.Leftover3Side) -> _Workspace:
    src, test = _leftover3_paths(side)
    return _Workspace(
        mod=side.mod,
        src=src,
        test=test,
        test_fn=side.test,
        test_body=f"def {side.test}():\n    assert drop('{side.file}') binds leftover\n",
        grep_command=f"rg -n 'unlink|remove|{side.file}|leftover' src {side.mod} tests",
        grep_hit=f"{src}:2: return {side.wrong}",
        src_body=f"def drop(path):\n    return {side.wrong}\n",
        fail_msg=side.fail1,
        still_msg=side.fail2,
    )


def build_leftover3_success(
    round_n: int,
    side: cat.Leftover3Side,
    catalog_id: str,
    plant: cat.Plant,
) -> dict[str, Any]:
    """16-step leftover leftover leftover success. Hopper-faithful; generator is ``cei-mill``."""

    _goal_ok(side.goal)
    ws = _leftover3_workspace(side)
    first_new = f"    return {side.wrong2}"
    steps = [
        *_investigation_steps(ws),
        *_gateway_recovery_steps(6, side.url, side.doc),
        *_rate_limit_recovery_steps(8, side.url2, side.doc2),
        _first_patch_step(
            ws,
            _edit(ws.src, f"    return {side.wrong}", first_new),
            f"patched naive {side.wrong2} (still unlink, not leftover bind)",
        ),
        _still_red_step(ws),
        _reread_step(ws, f"{side.leftover} still present after {side.naive}", side.chg),
        _corrective_patch_step(
            side.chg,
            _edit(ws.src, first_new, "    return bind_leftover(path)"),
            f"patched bind leftover then drop ({side.fix})",
        ),
        *_verified_fix_steps(ws, side.slug),
    ]
    record = {
        "id": _episode_id(round_n, side.slug),
        "goal": side.goal,
        "plan": side.plan,
        "steps": steps,
        "outcome": side.outcome,
        "reward": _success_reward(),
        "meta": _leftover3_meta(round_n, side, catalog_id, plant),
    }
    return _checked_episode(record, 16)


def build_leftover3_fail(
    round_n: int,
    side: cat.Leftover3Side,
    catalog_id: str,
    plant: cat.Plant,
) -> dict[str, Any]:
    """17-step leftover leftover leftover handoff. Hopper-faithful; generator is ``cei-mill``."""

    _goal_ok(side.goal)
    if not side.ticket:
        raise CeiRefusal(FINDING_USAGE, f"{side.slug} handoff missing ticket")
    ws = _leftover3_workspace(side)
    ticket = side.ticket
    steps = [
        *_investigation_steps(ws),
        *_rate_limit_recovery_steps(6, side.url, side.doc),
        *_gateway_recovery_steps(8, side.url2, side.doc2),
        _first_patch_step(
            ws,
            _edit(
                ws.src,
                f"    return {side.wrong}",
                "    return open(path, encoding='utf-8').read().split(',')",
            ),
            "patched text split (still not leftover bind)",
        ),
        _still_red_step(ws),
        _reread_step(ws, f"{side.leftover} remains; need platform reader", side.chg),
        _handoff_ticket_step(
            ws,
            side.chg,
            f"# {ticket} leftover ingest owned by platform",
            "ticket filed. still leftover after naive drop",
        ),
        *_handoff_close_steps(ws, side.slug, ticket),
    ]
    record = {
        "id": _episode_id(round_n, side.slug),
        "goal": side.goal,
        "plan": side.plan,
        "steps": steps,
        "outcome": side.outcome,
        "reward": _handoff_reward(),
        "meta": _leftover3_meta(round_n, side, catalog_id, plant),
    }
    return _checked_episode(record, 17)


def _leftover3_meta(
    round_n: int, side: cat.Leftover3Side, catalog_id: str, plant: cat.Plant
) -> dict[str, Any]:
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
        "seed": side.slug,
        "stack": side.stack,
    }


def pair_records(round_n: int, plant: cat.Plant, catalog_id: str) -> list[dict[str, Any]]:
    if plant.shape == LEFTOVER3_SHAPE:
        if not isinstance(plant.ok, cat.Leftover3Side) or not isinstance(
            plant.bad, cat.Leftover3Side
        ):
            raise CeiRefusal(FINDING_USAGE, f"{plant.plant_id} leftover leftover leftover sides")
        ok = build_leftover3_success(round_n, plant.ok, catalog_id, plant)
        bad = build_leftover3_fail(round_n, plant.bad, catalog_id, plant)
    else:
        if not isinstance(plant.ok, cat.Side) or not isinstance(plant.bad, cat.Side):
            raise CeiRefusal(FINDING_USAGE, f"{plant.plant_id} hop-mill sides")
        ok = build_success(round_n, plant.ok, catalog_id, plant)
        bad = build_fail(round_n, plant.bad, catalog_id, plant)
    if ok["id"] == bad["id"]:
        raise CeiRefusal(FINDING_USAGE, "duplicate episode ids")
    return [ok, bad]


def leftover3_notes_markdown(
    round_n: int, plant: cat.Plant, records: list[dict[str, Any]]
) -> str:
    ok, bad = plant.ok, plant.bad
    if not isinstance(ok, cat.Leftover3Side) or not isinstance(bad, cat.Leftover3Side):
        raise CeiRefusal(FINDING_USAGE, f"{plant.plant_id} leftover leftover leftover notes")
    ok_id, bad_id = records[0]["id"], records[1]["id"]
    return (
        f"# {FACTORY} — NOTES r{round_n}\n\n"
        f"Novel coverage: {NOVEL_COVERAGE_OK}%\n\n"
        f"## Episodes\n"
        f"- `{ok_id}`: 16 steps, success=True, domain={ok.domain}, seed={ok.slug}\n"
        f"  - 502 at step 6 recovered 7; 429 at step 8 recovered 9\n"
        f"  - plan change at step 12: {ok.chg}\n"
        f"  - leftover leftover leftover bind sidecar vs naive unlink\n"
        f"- `{bad_id}`: 17 steps, success=False, domain={bad.domain}, seed={bad.slug}\n"
        f"  - 429 at step 6 recovered 7; 502 at step 8 recovered 9\n"
        f"  - plan change at step 12: {bad.chg}\n"
        f"  - leftover leftover leftover handoff {bad.ticket}\n\n"
        f"## decision_basis audit\n"
        f"Every step has decision_basis starting with Plan:/Observation:/Reflection:/Tool call:, "
        f"length ≤240, no thought/chain_of_thought/scratch/inner_monologue keys, no spike_events, "
        f"no sim_or_real real. Generator {GENERATOR}. No [variant …] goal stamp.\n\n"
        f"## Mix\n"
        f"Success: ['{ok_id}']. Realistic failure/handoff: ['{bad_id}'].\n\n"
        f"## Residual\n"
        f"leftover leftover leftover bind sidecar vs naive unlink. {ok.leftover} {bad.leftover}\n"
    )


def notes_markdown(round_n: int, plant: cat.Plant, records: list[dict[str, Any]]) -> str:
    if plant.shape == LEFTOVER3_SHAPE:
        return leftover3_notes_markdown(round_n, plant, records)
    ok, bad = plant.ok, plant.bad
    if not isinstance(ok, cat.Side) or not isinstance(bad, cat.Side):
        raise CeiRefusal(FINDING_USAGE, f"{plant.plant_id} hop-mill notes")
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
    else:
        plants = loaded.plants
    return [(plant.base_round + plant.index, plant) for plant in plants]


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
