#!/usr/bin/env python3
"""16-step success + 17-step handoff episode builders.

One 12-step prefix is parameterised by noise order (502-then-429 vs
429-then-502). Reward numbers are constants, not measurements. ``dumps_episode``
keeps the mill's compact ``json.dumps`` so replay can match landed batches.
"""

from __future__ import annotations

import json
import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ._contract import (
    FINDING_DESTINATION_EXISTS,
    FINDING_DESTINATION_UNDER_RAW,
    FINDING_PAIR_INVALID,
    FINDING_PLANT_FIELD_MISSING,
    FINDING_RAW_ROOT_REQUIRED,
    bind_import_twin,
    is_under_raw,
    refuse_first,
    refuse_when,
)
from .notes import notes_md
from .plants import PREFIX

GENERATOR = "grok-4.6"
BANNED_KEYS = ("thought", "chain_of_thought", "scratch", "inner_monologue")
DB_PREFIXES = ("Plan:", "Observation:", "Reflection:", "Tool call:")
SUCCESS_REWARD = {
    "success": True, "tests_passed": 3, "retries": 2, "duration_min": 610,
    "wasted_calls": 180, "cost_steps": 16, "plan_changes": 1,
}
FAIL_REWARD = {
    "success": False, "tests_passed": 2, "retries": 2, "duration_min": 640,
    "wasted_calls": 210, "cost_steps": 17, "plan_changes": 1,
}

__all__ = [
    "GENERATOR", "assert_clean", "build_fail", "build_pair", "build_success",
    "dumps_episode", "emit_stage", "factory_dir", "set_raw_root", "validate_pair",
]

_RAW_ROOT: Path | None = None


def set_raw_root(path: Path | None) -> None:
    """Optional raw-tree root for ``factory_dir`` (never a repo-relative default)."""
    global _RAW_ROOT
    _RAW_ROOT = None if path is None else Path(path)


def factory_dir(factory: str, raw_root: Path | None = None) -> Path:
    root = raw_root if raw_root is not None else _RAW_ROOT
    if root is None:
        env = os.environ.get("HOPPER_RAW_ROOT")
        root = Path(env) if env else None
    refuse_when(
        root is None,
        FINDING_RAW_ROOT_REQUIRED,
        "factory_dir needs raw_root or HOPPER_RAW_ROOT",
    )
    return Path(root) / factory


def dumps_episode(ep: dict) -> str:
    return json.dumps(ep, ensure_ascii=True, separators=(",", ":"))


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
        for i, item in enumerate(obj):
            assert_clean(item, f"{path}[{i}]")


def _step(n: int, decision_basis: str, tool_call: dict, observation: str, reflection: str) -> dict:
    refuse_first((
        (not decision_basis.startswith(DB_PREFIXES), FINDING_PAIR_INVALID,
         f"step {n} decision_basis prefix: {decision_basis!r}"),
        (len(decision_basis) > 240, FINDING_PAIR_INVALID,
         f"step {n} decision_basis {len(decision_basis)} > 240"),
        (not observation.strip() or not reflection.strip(), FINDING_PAIR_INVALID,
         f"step {n} empty observation/reflection"),
    ))
    return {
        "n": n,
        "decision_basis": decision_basis,
        "tool_call": tool_call,
        "observation": observation,
        "reflection": reflection,
    }


def _bash(command: str) -> dict:
    return {"name": "bash", "args": {"command": command}}


def _read(path: str) -> dict:
    return {"name": "read", "args": {"path": path}}


def _edit(path: str, old: str, new: str) -> dict:
    return {"name": "edit", "args": {"path": path, "old": old, "new": new}}


def _pytest(args: str) -> dict:
    return {"name": "pytest", "args": {"args": args}}


def _fetch(url: str) -> dict:
    return {"name": "fetch", "args": {"url": url}}


def _paths(plant: Mapping) -> tuple[str, str, str]:
    src = f"src/{plant['mod']}.py"
    return src, f"tests/test_{plant['mod']}.py", f"{plant['mod']}/cfg.yml"


def _goal_ok(goal: str) -> None:
    text = goal.strip().lower()
    refuse_when(
        not goal.strip() or text in {"x", "placeholder", "todo", "tbd", "fix it"},
        FINDING_PAIR_INVALID,
        f"placeholder goal: {goal!r}",
    )
    refuse_when("[variant" in text, FINDING_PAIR_INVALID, f"variant stamp in goal: {goal!r}")


@dataclass(frozen=True)
class _Noise:
    url_key: str
    ok_key: str
    fail_status: str
    fail_reflection: str
    retry_lead: str
    retry_reflection: str
    retry_decision: str


_SUCCESS_NOISE = (
    _Noise(
        "docs_url", "docs_ok",
        "HTTP/1.1 502 Bad Gateway\nBad Gateway.",
        "Call failed with upstream gateway failure. Recover with backoff.",
        "retry after 2s backoff; local vendor fixture",
        "Degraded path used the local fixture. Continue with that content.",
        "Observation: the prior call returned an upstream gateway failure. Retry once with 2s backoff.",
    ),
    _Noise(
        "docs_url2", "docs_ok2",
        "HTTP/1.1 429 Too Many Requests\nRetry-After: 5\nX-RateLimit-Remaining: 0",
        "Call failed with rate-limit status with Retry-After. Recover with backoff.",
        "sleep + jitter retry of the same URL",
        "Retry succeeded. Resume the local debug plan with that document in hand.",
        "Observation: the prior call returned rate-limit status with Retry-After. Sleep then retry.",
    ),
)
_FAIL_NOISE = (
    _Noise(
        "docs_url", "docs_ok",
        "HTTP/1.1 429 Too Many Requests\nRetry-After: 6\nX-RateLimit-Remaining: 0",
        "Call failed with rate-limit status with Retry-After. Recover with backoff.",
        "sleep + jitter retry of the same URL",
        "Retry succeeded. Continue with that document.",
        "Observation: the prior call returned rate-limit status with Retry-After. Sleep then retry.",
    ),
    _Noise(
        "docs_url2", "docs_ok2",
        "HTTP/1.1 502 Bad Gateway\nBad Gateway.",
        "Call failed with upstream gateway failure. Recover with backoff.",
        "retry after 2s backoff; local vendor fixture",
        "Degraded path used the local fixture. Resume the local debug plan.",
        "Observation: the prior call returned an upstream gateway failure. Retry once with 2s backoff.",
    ),
)
_NEED = ("the changelog/registry", "the second remote document")


def _head_steps(plant: Mapping, src: str, test: str, cfg: str) -> list[dict]:
    listing = f"{src} {cfg}\n{test}"
    pytest_args = f"{test} -q --tb=short"
    fail_obs = f"{test}::{plant['test_fn']} FAILED\nE   {plant['fail_msg']}"
    return [
        _step(
            1,
            f"Plan: list src {plant['mod']} and tests before touching conversion or config.",
            _bash(f"ls -la src {plant['mod']} tests | head -40"),
            listing,
            f"Tree shows {src} plus tests. Run the named failing target next.",
        ),
        _step(
            2,
            f"Observation: listing named the test files. Run `{pytest_args}` to capture the failure.",
            _pytest(pytest_args),
            fail_obs,
            f"Failure is at {test}::{plant['test_fn']}. Read that test before a one-line fix.",
        ),
        _step(
            3,
            f"Observation: {test}::{plant['test_fn']} is red. Read {test} around the assertion.",
            _read(test),
            plant["test_body"],
            "Test contract is visible. Search implementation symbols next.",
        ),
        _step(
            4,
            "Observation: test file imported the production helper. Grep those symbols.",
            _bash(f"rg -n '{plant['grep_pat']}' src {plant['mod']} tests"),
            plant["grep_hit"],
            f"Grep hit {src}. Read it before editing the first match.",
        ),
        _step(
            5,
            f"Observation: grep listed {src}. Read it before any patch.",
            _read(src),
            plant["src_body"],
            "First read done. Fetch vendor docs next; do not patch on a hunch yet.",
        ),
    ]


def _noise_steps(plant: Mapping, first: _Noise, second: _Noise) -> list[dict]:
    steps = []
    number = 6
    for noise, need in ((first, _NEED[0]), (second, _NEED[1])):
        url = plant[noise.url_key]
        steps.append(_step(
            number,
            f"Observation: local files are in. Need {need} before editing.",
            _fetch(url),
            f"GET {url}\n{noise.fail_status}",
            noise.fail_reflection,
        ))
        steps.append(_step(
            number + 1,
            noise.retry_decision,
            _fetch(url),
            f"{noise.retry_lead}\nHTTP/1.1 200 OK\n{plant[noise.ok_key]}",
            noise.retry_reflection,
        ))
        number += 2
    return steps


def _mid_steps(plant: Mapping, src: str, test: str) -> list[dict]:
    pytest_args = f"{test} -q --tb=short"
    still_obs = f"{test}::{plant['test_fn']} FAILED\nE   {plant['still_msg']}"
    return [
        _step(
            10,
            f"Observation: docs and source are in. Apply the first patch to {src}.",
            _edit(src, plant["first_old"], plant["first_new"]),
            plant["first_obs"],
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
            f"Observation: post-edit test still failed ({test}::{plant['test_fn']}). Re-read {src}.",
            _read(src),
            plant["reread_obs"],
            f"Plan change: {plant['plan_change']}",
        ),
    ]


def _success_tail(plant: Mapping, src: str, test: str) -> list[dict]:
    return [
        _step(
            13,
            f"Reflection: {plant['plan_change']}"[:240],
            _edit(src, plant["first_new"], plant["fix_new"]),
            plant["fix_obs"],
            "Corrective patch applied. Run the original failing node again.",
        ),
        _step(
            14,
            "Observation: fix edit returned clean. Re-run the original failing test node.",
            _pytest(f"{test} -q --tb=short"),
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
            "Observation: broader check is on disk. Show the diff of patched files for the handoff note.",
            _bash("git diff --stat | head -n 40"),
            f"diffstat for {plant['slug']}: {src} | 9 ++++++---. No other modified paths.",
            "Diff is the review artifact. No further edits.",
        ),
    ]


def _fail_tail(plant: Mapping, src: str, test: str) -> list[dict]:
    ticket = plant["ticket"]
    ticket_path = f"{plant['mod']}/handoff.md"
    return [
        _step(
            13,
            f"Reflection: {plant['plan_change']}"[:240],
            _edit(ticket_path, "", f"# {ticket} {plant['ticket_why']}"),
            plant["fix_obs"],
            "Handoff ticket written. Run the original failing node again.",
        ),
        _step(
            14,
            "Observation: handoff edit returned clean. Re-run the original failing test node.",
            _pytest(f"{test} -q --tb=short"),
            f"{test}::{plant['test_fn']} FAILED  # handoff: {ticket}\n1 failed",
            "Result recorded. Run one broader check before declaring the outcome.",
        ),
        _step(
            15,
            f"Observation: focused run finished. Run broader check `pytest {test} -q; echo {ticket}`.",
            _bash(f"pytest {test} -q; echo {ticket}"),
            f"1 failed, 2 passed\n{ticket}",
            "Broader check captured. Residual risk belongs in the outcome text.",
        ),
        _step(
            16,
            "Observation: broader check is on disk. Show the diff of patched files for the handoff note.",
            _bash("git diff --stat | head -n 40"),
            f"diffstat for {plant['slug']}: {src} | 8 +++++---. {ticket_path} added.",
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


def _episode(
    factory: str,
    prefix: str,
    round_n: int,
    plant: Mapping,
    steps: list[dict],
    reward: dict,
) -> dict:
    _goal_ok(plant["goal"])
    eid = f"{prefix}-r{round_n}-{plant['slug']}"
    ep = {
        "id": eid,
        "goal": plant["goal"],
        "plan": plant["plan"],
        "steps": steps,
        "outcome": plant["outcome"],
        "reward": dict(reward),
        "meta": {
            "factory": factory,
            "round": round_n,
            "generator": GENERATOR,
            "kind": "episode",
            "seed": plant["seed"],
            "designed": True,
            "domain": plant["domain"],
            "stack": plant["stack"],
        },
    }
    assert_clean(ep)
    return ep


def build_success(factory: str, prefix: str, round_n: int, plant: Mapping) -> dict:
    src, test, cfg = _paths(plant)
    steps = (
        _head_steps(plant, src, test, cfg)
        + _noise_steps(plant, *_SUCCESS_NOISE)
        + _mid_steps(plant, src, test)
        + _success_tail(plant, src, test)
    )
    refuse_when(len(steps) != 16, FINDING_PAIR_INVALID, f"{plant.get('slug')} expected 16 steps")
    return _episode(factory, prefix, round_n, plant, steps, SUCCESS_REWARD)


def build_fail(factory: str, prefix: str, round_n: int, plant: Mapping) -> dict:
    refuse_when("ticket" not in plant, FINDING_PLANT_FIELD_MISSING, "handoff missing ticket")
    src, test, cfg = _paths(plant)
    steps = (
        _head_steps(plant, src, test, cfg)
        + _noise_steps(plant, *_FAIL_NOISE)
        + _mid_steps(plant, src, test)
        + _fail_tail(plant, src, test)
    )
    refuse_when(len(steps) != 17, FINDING_PAIR_INVALID, f"{plant.get('slug')} expected 17 steps")
    return _episode(factory, prefix, round_n, plant, steps, FAIL_REWARD)


def validate_pair(ok_ep: Mapping, bad_ep: Mapping, round_n: int) -> None:
    refuse_first((
        (ok_ep["reward"]["success"] is not True, FINDING_PAIR_INVALID, "first episode must succeed"),
        (bad_ep["reward"]["success"] is not False, FINDING_PAIR_INVALID, "second episode must fail/handoff"),
        (len(ok_ep["steps"]) != 16 or len(bad_ep["steps"]) != 17, FINDING_PAIR_INVALID,
         "shape must be 16-step success + 17-step fail"),
        (ok_ep["meta"]["round"] != round_n or bad_ep["meta"]["round"] != round_n,
         FINDING_PAIR_INVALID, "meta.round mismatch"),
        (ok_ep["meta"]["generator"] != GENERATOR or bad_ep["meta"]["generator"] != GENERATOR,
         FINDING_PAIR_INVALID, "generator"),
        (ok_ep["id"] == bad_ep["id"], FINDING_PAIR_INVALID, "duplicate episode ids"),
    ))
    for ep in (ok_ep, bad_ep):
        _goal_ok(ep["goal"])
        assert_clean(ep)


def build_pair(factory: str, round_n: int, ok: Mapping, bad: Mapping):
    prefix = PREFIX[factory] if factory in PREFIX else ok.get("prefix") or bad.get("prefix")
    refuse_when(not prefix, FINDING_PAIR_INVALID, f"no prefix for factory {factory}")
    ok_ep = build_success(factory, prefix, round_n, ok)
    bad_ep = build_fail(factory, prefix, round_n, bad)
    validate_pair(ok_ep, bad_ep, round_n)
    notes = notes_md(factory, round_n, ok, bad, ok_ep["id"], bad_ep["id"])
    refuse_when("Novel coverage:" not in notes, FINDING_PAIR_INVALID, "NOTES missing Novel coverage")
    return ok_ep, bad_ep, notes


def emit_stage(stage: Path, factory: str, round_n: int, ok: Mapping, bad: Mapping):
    stage = Path(stage)
    batch = stage / f"batch-r{round_n:02d}.jsonl"
    notes_path = stage / f"NOTES-r{round_n:02d}.md"
    refuse_first((
        (is_under_raw(stage) or is_under_raw(batch), FINDING_DESTINATION_UNDER_RAW,
         f"{stage} names or aliases the raw tree"),
        (batch.exists() or notes_path.exists(), FINDING_DESTINATION_EXISTS,
         f"{batch} or {notes_path} already exists"),
    ))
    ok_ep, bad_ep, notes = build_pair(factory, round_n, ok, bad)
    stage.mkdir(parents=True, exist_ok=True)
    batch.write_text(dumps_episode(ok_ep) + "\n" + dumps_episode(bad_ep) + "\n", encoding="utf-8")
    notes_path.write_text(notes, encoding="utf-8")
    return ok_ep["id"], bad_ep["id"]


bind_import_twin(__name__)
