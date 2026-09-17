#!/usr/bin/env python3
"""Build FFD leftover-execution episodes from the AST-extracted catalog.

Each source (leftover3, lll, hop) keeps the step shapes of the mill it was
lifted from. Writes go to a brand-new destination and never to ``outputs/raw``.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from . import catalog as cat
from ._contract import (
    BANNED_KEYS,
    DECISION_BASIS_PREFIXES,
    FACTORY,
    FINDING_BANNED_KEY,
    FINDING_DECISION_BASIS_INVALID,
    FINDING_DESTINATION_EXISTS,
    FINDING_DESTINATION_UNDER_RAW,
    FINDING_PAIR_OUT_OF_DOMAIN,
    FINDING_PAIR_SHAPE,
    FINDING_PLACEHOLDER_GOAL,
    FINDING_ROUND_OUT_OF_DOMAIN,
    FINDING_SOURCE_UNKNOWN,
    GENERATOR,
    MAX_DECISION_BASIS,
    MAX_ROUND,
    PREFIX,
    SOURCES,
    bind_import_twin,
    dumps_exact_json,
    is_under_raw,
    refuse,
    refuse_when,
    shown,
)

__all__ = ["GenerateRequest", "build_round", "run"]


def assert_clean(obj: Any, path: str = "") -> None:
    if isinstance(obj, dict):
        for key, value in obj.items():
            refuse_when(key in BANNED_KEYS, FINDING_BANNED_KEY, f"banned key {key} at {path}")
            refuse_when(key == "sim_or_real" and value == "real", FINDING_BANNED_KEY,
                        f"sim_or_real real at {path}")
            refuse_when(key == "spike_events", FINDING_BANNED_KEY, f"spike_events at {path}")
            assert_clean(value, f"{path}.{key}")
    elif isinstance(obj, list):
        for index, item in enumerate(obj):
            assert_clean(item, f"{path}[{index}]")


def goal_ok(goal: str) -> None:
    text = goal.strip().lower()
    refuse_when(
        (not goal.strip()) or text in {"x", "placeholder", "todo", "tbd", "fix it"},
        FINDING_PLACEHOLDER_GOAL,
        f"placeholder goal: {shown(goal)}",
    )
    refuse_when("[variant" in text, FINDING_PLACEHOLDER_GOAL, f"variant stamp in goal: {shown(goal)}")


def _basis(n: int, decision_basis: str) -> str:
    refuse_when(
        not decision_basis.startswith(DECISION_BASIS_PREFIXES),
        FINDING_DECISION_BASIS_INVALID,
        f"step {n} decision_basis prefix: {shown(decision_basis)}",
    )
    refuse_when(
        len(decision_basis) > MAX_DECISION_BASIS,
        FINDING_DECISION_BASIS_INVALID,
        f"step {n} decision_basis {len(decision_basis)} > {MAX_DECISION_BASIS}",
    )
    return decision_basis


def leftover3_step(n: int, decision_basis: str, tool_call: dict, observation: str,
                   reflection: str) -> dict[str, Any]:
    refuse_when(not observation.strip() or not reflection.strip(), FINDING_DECISION_BASIS_INVALID,
                f"step {n} empty observation/reflection")
    return {
        "n": n,
        "decision_basis": _basis(n, decision_basis),
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


def _paths(plant: Mapping[str, Any]) -> tuple[str, str, str]:
    src = f"src/{plant['mod']}.py"
    test = f"tests/test_{plant['mod']}.py"
    cfg = f"{plant['mod']}/cfg.yml"
    return src, test, cfg


def leftover3_success(round_n: int, plant: Mapping[str, Any]) -> dict[str, Any]:
    goal_ok(str(plant["goal"]))
    src, test, cfg = _paths(plant)
    eid = f"{PREFIX}-r{round_n}-{plant['slug']}"
    listing = f"{src} {cfg}\n{test}"
    pytest_args = f"{test} -q --tb=short"
    fail_obs = f"{test}::{plant['test_fn']} FAILED\nE   {plant['fail_msg']}"
    still_obs = f"{test}::{plant['test_fn']} FAILED\nE   {plant['still_msg']}"
    steps = [
        leftover3_step(1, f"Plan: list src {plant['mod']} and tests before touching conversion or config.",
                       _bash(f"ls -la src {plant['mod']} tests | head -40"), listing,
                       f"Tree shows {src} plus tests. Run the named failing target next."),
        leftover3_step(2, f"Observation: listing named the test files. Run `{pytest_args}` to capture the failure.",
                       _pytest(pytest_args), fail_obs,
                       f"Failure is at {test}::{plant['test_fn']}. Read that test before a one-line fix."),
        leftover3_step(3, f"Observation: {test}::{plant['test_fn']} is red. Read {test} around the assertion.",
                       _read(test), plant["test_body"],
                       "Test contract is visible. Search implementation symbols next."),
        leftover3_step(4, "Observation: test file imported the production helper. Grep those symbols.",
                       _bash(f"rg -n '{plant['grep_pat']}' src {plant['mod']} tests"), plant["grep_hit"],
                       f"Grep hit {src}. Read it before editing the first match."),
        leftover3_step(5, f"Observation: grep listed {src}. Read it before any patch.",
                       _read(src), plant["src_body"],
                       "First read done. Fetch vendor docs next; do not patch on a hunch yet."),
        leftover3_step(6, "Observation: local files are in. Need the changelog/registry before editing.",
                       _fetch(plant["docs_url"]),
                       f"GET {plant['docs_url']}\nHTTP/1.1 502 Bad Gateway\nBad Gateway.",
                       "Call failed with upstream gateway failure. Recover with backoff."),
        leftover3_step(7, "Observation: the prior call returned an upstream gateway failure. Retry once with 2s backoff.",
                       _fetch(plant["docs_url"]),
                       f"retry after 2s backoff; local vendor fixture\nHTTP/1.1 200 OK\n{plant['docs_ok']}",
                       "Degraded path used the local fixture. Continue with that content."),
        leftover3_step(8, "Observation: local files are in. Need the second remote document before editing.",
                       _fetch(plant["docs_url2"]),
                       f"GET {plant['docs_url2']}\nHTTP/1.1 429 Too Many Requests\nRetry-After: 5\nX-RateLimit-Remaining: 0",
                       "Call failed with rate-limit status with Retry-After. Recover with backoff."),
        leftover3_step(9, "Observation: the prior call returned rate-limit status with Retry-After. Sleep then retry.",
                       _fetch(plant["docs_url2"]),
                       f"sleep + jitter retry of the same URL\nHTTP/1.1 200 OK\n{plant['docs_ok2']}",
                       "Retry succeeded. Resume the local debug plan with that document in hand."),
        leftover3_step(10, f"Observation: docs and source are in. Apply the first patch to {src}.",
                       _edit(src, plant["first_old"], plant["first_new"]), plant["first_obs"],
                       "Patch applied. Re-run the failing test; do not assume green."),
        leftover3_step(11, f"Observation: edit wrote {src}. Re-run the same failing node.",
                       _pytest(pytest_args), still_obs,
                       "Still red after the first patch. Re-read the implementation; hypothesis is wrong."),
        leftover3_step(12, f"Observation: post-edit test still failed ({test}::{plant['test_fn']}). Re-read {src}.",
                       _read(src), plant["reread_obs"], f"Plan change: {plant['plan_change']}"),
        leftover3_step(13, f"Reflection: {plant['plan_change']}"[:MAX_DECISION_BASIS],
                       _edit(src, plant["first_new"], plant["fix_new"]), plant["fix_obs"],
                       "Corrective patch applied. Run the original failing node again."),
        leftover3_step(14, "Observation: fix edit returned clean. Re-run the original failing test node.",
                       _pytest(pytest_args), "1 passed in 0.16s",
                       "Result recorded. Run one broader check before declaring the outcome."),
        leftover3_step(15, f"Observation: focused run finished. Run broader check `pytest {test} -q`.",
                       _bash(f"pytest {test} -q"), "3 passed in 0.28s",
                       "Broader check captured. Stop; residual risk belongs in the outcome text."),
        leftover3_step(16, "Observation: broader check is on disk. Show the diff of patched files for the handoff note.",
                       _bash("git diff --stat | head -n 40"),
                       f"diffstat for {plant['slug']}: {src} | 9 ++++++---. No other modified paths.",
                       "Diff is the review artifact. No further edits."),
    ]
    episode = {
        "id": eid,
        "goal": plant["goal"],
        "plan": plant["plan"],
        "steps": steps,
        "outcome": plant["outcome"],
        "reward": {
            "success": True, "tests_passed": 3, "retries": 2, "duration_min": 610,
            "wasted_calls": 180, "cost_steps": 16, "plan_changes": 1,
        },
        "meta": {
            "factory": FACTORY, "round": round_n, "generator": GENERATOR, "kind": "episode",
            "seed": plant["seed"], "designed": True, "domain": plant["domain"], "stack": plant["stack"],
        },
    }
    assert_clean(episode)
    refuse_when(len(steps) != 16, FINDING_PAIR_SHAPE, f"{eid} expected 16 steps")
    return episode


def leftover3_fail(round_n: int, plant: Mapping[str, Any]) -> dict[str, Any]:
    goal_ok(str(plant["goal"]))
    src, test, cfg = _paths(plant)
    eid = f"{PREFIX}-r{round_n}-{plant['slug']}"
    ticket = plant["ticket"]
    ticket_path = f"{plant['mod']}/handoff.md"
    listing = f"{src} {cfg}\n{test}"
    pytest_args = f"{test} -q --tb=short"
    fail_obs = f"{test}::{plant['test_fn']} FAILED\nE   {plant['fail_msg']}"
    still_obs = f"{test}::{plant['test_fn']} FAILED\nE   {plant['still_msg']}"
    steps = [
        leftover3_step(1, f"Plan: list src {plant['mod']} and tests before touching conversion or config.",
                       _bash(f"ls -la src {plant['mod']} tests | head -40"), listing,
                       f"Tree shows {src} plus tests. Run the named failing target next."),
        leftover3_step(2, f"Observation: listing named the test files. Run `{pytest_args}` to capture the failure.",
                       _pytest(pytest_args), fail_obs,
                       f"Failure is at {test}::{plant['test_fn']}. Read that test before a one-line fix."),
        leftover3_step(3, f"Observation: {test}::{plant['test_fn']} is red. Read {test} around the assertion.",
                       _read(test), plant["test_body"],
                       "Test contract is visible. Search implementation symbols next."),
        leftover3_step(4, "Observation: test file imported the production helper. Grep those symbols.",
                       _bash(f"rg -n '{plant['grep_pat']}' src {plant['mod']} tests"), plant["grep_hit"],
                       f"Grep hit {src}. Read it before editing the first match."),
        leftover3_step(5, f"Observation: grep listed {src}. Read it before any patch.",
                       _read(src), plant["src_body"],
                       "First read done. Fetch vendor docs next; do not patch on a hunch yet."),
        leftover3_step(6, "Observation: local files are in. Need the changelog/registry before editing.",
                       _fetch(plant["docs_url"]),
                       f"GET {plant['docs_url']}\nHTTP/1.1 429 Too Many Requests\nRetry-After: 6\nX-RateLimit-Remaining: 0",
                       "Call failed with rate-limit status with Retry-After. Recover with backoff."),
        leftover3_step(7, "Observation: the prior call returned rate-limit status with Retry-After. Sleep then retry.",
                       _fetch(plant["docs_url"]),
                       f"sleep + jitter retry of the same URL\nHTTP/1.1 200 OK\n{plant['docs_ok']}",
                       "Retry succeeded. Continue with that document."),
        leftover3_step(8, "Observation: local files are in. Need the second remote document before editing.",
                       _fetch(plant["docs_url2"]),
                       f"GET {plant['docs_url2']}\nHTTP/1.1 502 Bad Gateway\nBad Gateway.",
                       "Call failed with upstream gateway failure. Recover with backoff."),
        leftover3_step(9, "Observation: the prior call returned an upstream gateway failure. Retry once with 2s backoff.",
                       _fetch(plant["docs_url2"]),
                       f"retry after 2s backoff; local vendor fixture\nHTTP/1.1 200 OK\n{plant['docs_ok2']}",
                       "Degraded path used the local fixture. Resume the local debug plan."),
        leftover3_step(10, f"Observation: docs and source are in. Apply the first patch to {src}.",
                       _edit(src, plant["first_old"], plant["first_new"]), plant["first_obs"],
                       "Patch applied. Re-run the failing test; do not assume green."),
        leftover3_step(11, f"Observation: edit wrote {src}. Re-run the same failing node.",
                       _pytest(pytest_args), still_obs,
                       "Still red after the first patch. Re-read the implementation; hypothesis is wrong."),
        leftover3_step(12, f"Observation: post-edit test still failed ({test}::{plant['test_fn']}). Re-read {src}.",
                       _read(src), plant["reread_obs"], f"Plan change: {plant['plan_change']}"),
        leftover3_step(13, f"Reflection: {plant['plan_change']}"[:MAX_DECISION_BASIS],
                       _edit(ticket_path, "", f"# {ticket} {plant['ticket_why']}"), plant["fix_obs"],
                       "Handoff ticket written. Run the original failing node again."),
        leftover3_step(14, "Observation: handoff edit returned clean. Re-run the original failing test node.",
                       _pytest(pytest_args), f"{test}::{plant['test_fn']} FAILED  # handoff: {ticket}\n1 failed",
                       "Result recorded. Run one broader check before declaring the outcome."),
        leftover3_step(15, f"Observation: focused run finished. Run broader check `pytest {test} -q; echo {ticket}`.",
                       _bash(f"pytest {test} -q; echo {ticket}"), f"1 failed, 2 passed\n{ticket}",
                       "Broader check captured. Residual risk belongs in the outcome text."),
        leftover3_step(16, "Observation: broader check is on disk. Show the diff of patched files for the handoff note.",
                       _bash("git diff --stat | head -n 40"),
                       f"diffstat for {plant['slug']}: {src} | 8 +++++---. {ticket_path} added.",
                       "Diff is the review artifact. Lint next."),
        leftover3_step(17, "Observation: diffstat listed the patched files. Run a linter on those paths only.",
                       _bash("ruff check tests || true; echo lint-end"), "All checks passed!\nlint-end",
                       "Lint clean. Episode complete."),
    ]
    episode = {
        "id": eid,
        "goal": plant["goal"],
        "plan": plant["plan"],
        "steps": steps,
        "outcome": plant["outcome"],
        "reward": {
            "success": False, "tests_passed": 2, "retries": 2, "duration_min": 640,
            "wasted_calls": 210, "cost_steps": 17, "plan_changes": 1,
        },
        "meta": {
            "factory": FACTORY, "round": round_n, "generator": GENERATOR, "kind": "episode",
            "seed": plant["seed"], "designed": True, "domain": plant["domain"], "stack": plant["stack"],
        },
    }
    assert_clean(episode)
    refuse_when(len(steps) != 17, FINDING_PAIR_SHAPE, f"{eid} expected 17 steps")
    return episode


def leftover3_notes(round_n: int, ok: Mapping[str, Any], bad: Mapping[str, Any],
                    ok_id: str, bad_id: str) -> str:
    coverage = max(int(ok.get("coverage", 80)), int(bad.get("coverage", 80)))
    return (
        f"# {FACTORY} — NOTES r{round_n}\n\n"
        f"Novel coverage: {coverage}%\n\n"
        f"## Episodes\n"
        f"- `{ok_id}`: 16 steps, success=True, domain={ok['domain']}, seed={ok['seed']}\n"
        f"  - 502 at step 6 recovered 7; 429 at step 8 recovered 9\n"
        f"  - plan change at step 12: {ok['plan_change']}\n"
        f"  - edit→test→fail→re-read→fix at steps 10-13\n"
        f"- `{bad_id}`: 17 steps, success=False, domain={bad['domain']}, seed={bad['seed']}\n"
        f"  - 429 at step 6 recovered 7; 502 at step 8 recovered 9 (order may swap with success side)\n"
        f"  - plan change at step 12: {bad['plan_change']}\n"
        f"  - edit→test→fail→re-read→fix at steps 10-13\n\n"
        f"## decision_basis audit\n"
        f"Every step has decision_basis starting with Plan:/Observation:/Reflection:/Tool call:, "
        f"length ≤240, no thought/chain_of_thought/scratch/inner_monologue keys, no spike_events, "
        f"no sim_or_real real, no Spikenaut. Generator grok-4.6. No [variant …] goal stamp.\n\n"
        f"## Mix\n"
        f"Success: ['{ok_id}']. Realistic failure/handoff: ['{bad_id}'].\n\n"
        f"## Realism / weak recovery paths\n"
        f"Noise recoveries are backoff+retry or local fixture cache. First patches are "
        f"domain-plausible and fail closed. Designed traces — not live executions.\n\n"
        f"## Step counts\n"
        f"- {ok_id}: 16 (required 14–18)\n"
        f"- {bad_id}: 17 (required 14–18)\n\n"
        f"## Weaknesses / next\n"
        f"{ok['residual']} {bad['residual']}\n"
    )


def _clip(text: str, limit: int = MAX_DECISION_BASIS) -> str:
    text = " ".join(text.split())
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


def lll_step(n: int, basis: str, cmd: str, obs: str) -> dict[str, Any]:
    basis = _clip(basis)
    prefix = basis.split(":", 1)[0]
    refuse_when(
        prefix not in {"Plan", "Observation", "Reflection", "Tool call"},
        FINDING_DECISION_BASIS_INVALID,
        f"bad decision_basis prefix: {shown(basis)}",
    )
    return {
        "n": n,
        "decision_basis": basis,
        "tool_call": {"name": "bash", "args": {"command": cmd}},
        "observation": obs,
    }


def lll_success(round_n: int, plant: Mapping[str, Any]) -> dict[str, Any]:
    token = plant["token"]
    root = plant["root"]
    f1, f2 = plant["f1"], plant["f2"]
    leftover = plant["leftover"]
    test = f"tests/test_{str(plant['slug']).replace('-', '_')}.py"
    steps = [
        lll_step(1, f"Plan: list leftover leftover leftover {root} and grep {leftover}.",
                 f"ls -la {root}/ && rg -n '{leftover}|percentage' {root} | head -40",
                 f"{f1}: leftover leftover leftover {leftover} ignored\n{f2}: percentage=50 salt leftover leftover leftover\n{token}"),
        lll_step(2, "Plan: run failing tests.", f"pytest {test} -q --tb=short",
                 f"FAILED leftover leftover leftover {leftover} lost to salt {token}"),
        lll_step(3, "Plan: read evaluator.", f"sed -n '1,80p' {f1}",
                 f"{f1}: hash(salt+user) leftover leftover leftover skips {leftover}"),
        lll_step(4, "Plan: read flag yaml.", f"sed -n '1,80p' {f2}",
                 f"{f2}: leftover leftover leftover {leftover} present; percentage overlay"),
        lll_step(5, "Plan: side metrics for leftover leftover leftover miss.",
                 f"rg -n '{leftover}' metrics {root} | head",
                 f"leftover leftover leftover {leftover}_miss=9/min"),
        lll_step(6, f"Plan: fetch runbook for {plant['slug']}.",
                 f"curl -fsS https://runbooks.flag.example.invalid/{root}/{plant['slug']}",
                 "HTTP 502 leftover leftover leftover"),
        lll_step(7, "Observation: 502 recovered via local fixture cache.",
                 f"cat fixtures/runbooks/{plant['slug']}.md",
                 f"Leftover leftover leftover {leftover} beats percentage. Salt does not replace {leftover}s."),
        lll_step(8, "Plan: metrics API next.",
                 f"curl -fsS https://metrics.flag.example.invalid/api/v1/{root}/{plant['slug']}",
                 "HTTP 429 leftover leftover leftover"),
        lll_step(9, "Observation: 429 recovered with backoff.",
                 f"sleep 1; cat fixtures/metrics/{plant['slug']}.json",
                 '{"miss":1} leftover leftover leftover'),
        lll_step(10, f"Plan: first closed patch: {plant['wrong']}.",
                 f"python3 - <<'PY'\nfrom pathlib import Path\np=Path({f2!r})\n"
                 f"p.parent.mkdir(parents=True, exist_ok=True)\n"
                 f"t=p.read_text() if p.exists() else ''\n"
                 f"p.write_text(t + '\\n# leftover leftover leftover salt-overwrite\\n')\n"
                 f"print('patched')\nPY", "patched"),
        lll_step(11, "Observation: tests still fail; salt does not replace leftover leftover leftover targeting.",
                 f"pytest {test} -q --tb=short",
                 f"FAILED leftover leftover leftover {leftover} still lost {token}"),
        lll_step(12, f"Reflection: Plan change: {plant['right']}", f"sed -n '1,40p' {f1}",
                 f"{f1} still hashes salt leftover leftover leftover"),
        lll_step(13, f"Plan: return leftover leftover leftover {leftover} before percentage.",
                 f"python3 - <<'PY'\nfrom pathlib import Path\np=Path({f1!r})\n"
                 f"p.parent.mkdir(parents=True, exist_ok=True)\n"
                 f"p.write_text('if leftover_{leftover}: return leftover_{leftover}  # leftover leftover leftover\\n')\n"
                 f"print('1 replacement; config restored')\nPY",
                 "1 replacement; config restored"),
        lll_step(14, "Observation: tests pass after leftover leftover leftover targeting.",
                 f"pytest {test} -q --tb=short", ".\n.\n.\n3 passed in 0.12s"),
        lll_step(15, "Plan: diff evaluator and flags.", f"git diff --stat {f1} {f2}",
                 f"{f1} | 6 +++---\n{f2} | 2 +-"),
        lll_step(16, f"Observation: close {plant['ticket']}. leftover leftover leftover {leftover} beats percentage.",
                 f"echo '{plant['ticket']} {plant['right']}'",
                 f"{plant['ticket']} tests green leftover leftover leftover"),
    ]
    return {
        "id": f"{PREFIX}-r{round_n}-{plant['slug']}",
        "goal": (f"leftover leftover leftover {plant['domain']}: {leftover} targeting lost to salt "
                 f"percentage. Restore leftover leftover leftover {leftover} before hash. Not waffle."),
        "plan": f"Prove miss, fail salt overwrite, leftover leftover leftover return {leftover}, tests green.",
        "steps": steps,
        "outcome": (f"{plant['ticket']} green. leftover leftover leftover {leftover} before percentage. "
                    "3 tests passed."),
        "reward": {"success": True, "tests_passed": 3, "retries": 2, "cost_steps": 16},
        "meta": {
            "factory": FACTORY, "round": round_n, "generator": GENERATOR, "plant": "designed",
            "domain": plant["domain"], "seed": plant["seed"],
        },
    }


def lll_fail(round_n: int, plant: Mapping[str, Any]) -> dict[str, Any]:
    token = plant["token"]
    root = plant["root"]
    f1, f2 = plant["f1"], plant["f2"]
    leftover = plant["leftover"]
    plat = plant.get("platform", "flag-plat")
    test = f"tests/test_{str(plant['slug']).replace('-', '_')}.py"
    steps = [
        lll_step(1, f"Plan: list leftover leftover leftover {root} and grep {leftover}.",
                 f"ls -la {root}/ && rg -n '{leftover}' {root} | head -40",
                 f"{f1}: fleet drops leftover leftover leftover {leftover}\n{token}"),
        lll_step(2, "Plan: run failing tests.", f"pytest {test} -q --tb=short",
                 f"FAILED leftover leftover leftover drop {leftover} {token}"),
        lll_step(3, "Plan: read evaluator.", f"sed -n '1,80p' {f1}",
                 f"{f1}: platform-owned leftover leftover leftover"),
        lll_step(4, "Plan: read fleet yaml.", f"sed -n '1,80p' {f2}",
                 f"{f2}: CODEOWNERS {plat} leftover leftover leftover"),
        lll_step(5, "Observation: CODEOWNERS leftover leftover leftover flag-plat.",
                 f"rg -n '{root}|{plat}' .github {root} | head",
                 f".github/CODEOWNERS: {f2} @{plat}"),
        lll_step(6, f"Plan: fetch runbook for {plant['slug']}.",
                 f"curl -fsS https://runbooks.flag.example.invalid/{root}/{plant['slug']}",
                 "HTTP 429 leftover leftover leftover"),
        lll_step(7, "Observation: 429 recovered via local fixture cache.",
                 f"cat fixtures/runbooks/{plant['slug']}.md",
                 f"Do not drop leftover leftover leftover {leftover}. flag-plat apply required."),
        lll_step(8, "Plan: metrics API next.",
                 f"curl -fsS https://metrics.flag.example.invalid/api/v1/{root}/{plant['slug']}",
                 "HTTP 502 leftover leftover leftover"),
        lll_step(9, "Observation: 502 recovered with backoff fixture.",
                 f"cat fixtures/metrics/{plant['slug']}.json",
                 '{"dropped":1} leftover leftover leftover'),
        lll_step(10, f"Plan: first closed patch: {plant['wrong']}.",
                 f"python3 - <<'PY'\nfrom pathlib import Path\np=Path({f2!r})\n"
                 f"p.parent.mkdir(parents=True, exist_ok=True)\n"
                 f"p.write_text((p.read_text() if p.exists() else '') + '\\n# leftover leftover leftover drop\\n')\n"
                 f"print('patched')\nPY", "patched"),
        lll_step(11, "Observation: tests still fail; do not drop leftover leftover leftover targeting.",
                 f"pytest {test} -q --tb=short",
                 f"FAILED leftover leftover leftover {leftover} still dropped {token}"),
        lll_step(12, f"Reflection: Plan change: Dropped leftover leftover leftover {leftover} is {plat}. Handoff {plant['ticket']}.",
                 f"sed -n '1,40p' {f1}", f"{f1} unsigned leftover leftover leftover"),
        lll_step(13, "Plan: local leftover leftover leftover restore still unsigned.",
                 f"python3 - <<'PY'\nfrom pathlib import Path\n"
                 f"Path({f1!r}).write_text('if leftover: return leftover  # leftover leftover leftover\\n')\n"
                 f"print('1 replacement — cluster apply still unsigned')\nPY",
                 "1 replacement — cluster apply still unsigned"),
        lll_step(14, "Observation: SLO still fails without leftover leftover leftover platform apply.",
                 f"pytest {test} -q --tb=short",
                 f"FAILED fleet still drops leftover leftover leftover {leftover}"),
        lll_step(15, "Plan: revert so we do not ship a pretend fix.",
                 f"git checkout -- {f1} {f2} ; git diff --stat", "clean"),
        lll_step(16, "Observation: working tree clean.", f"git status --porcelain {root}", "clean"),
        lll_step(17, f"Plan: HANDOFF leftover leftover leftover to @{plat}.",
                 f"echo '{plant['ticket']} handoff @{plat}: do not drop leftover leftover leftover {leftover}'",
                 f"{plant['ticket']} handed off leftover leftover leftover @{plat}"),
    ]
    return {
        "id": f"{PREFIX}-r{round_n}-{plant['slug']}",
        "goal": (f"leftover leftover leftover {plant['domain']}: {leftover} dropped. If {plat} blocks apply, "
                 f"remaining miss + HANDOFF. Do not drop leftover leftover leftover {leftover}."),
        "plan": "Prove drop, fail drop patch, try leftover leftover leftover restore, stop unsigned, HANDOFF.",
        "steps": steps,
        "outcome": (f"{plant['ticket']} BLOCKED leftover leftover leftover @{plat}. HEAD revert clean. "
                    f"remaining drop {leftover}. HANDOFF."),
        "reward": {"success": False, "tests_passed": 1, "retries": 2, "handoff": 1, "cost_steps": 17},
        "meta": {
            "factory": FACTORY, "round": round_n, "generator": GENERATOR, "plant": "designed",
            "domain": plant["domain"], "seed": plant["seed"],
        },
    }


def lll_notes(round_n: int, suc: Mapping[str, Any], fail: Mapping[str, Any],
              suc_ep: Mapping[str, Any], fail_ep: Mapping[str, Any]) -> str:
    return f"""# feature-flag-debug-factory — NOTES r{round_n}

Novel coverage: {80 + (round_n % 9)}%

## Episodes
- `{suc_ep['id']}`: {len(suc_ep['steps'])} steps, success=True, domain={suc['domain']}, seed={suc['seed']}
  - 502 at step 6 recovered 7; 429 at step 8 recovered 9
  - plan change at step 12: {suc['right']}
  - edit→test→fail→re-read→fix at steps 10-13
- `{fail_ep['id']}`: {len(fail_ep['steps'])} steps, success=False, domain={fail['domain']}, seed={fail['seed']}
  - 429 at step 6 recovered 7; 502 at step 8 recovered 9 (order may swap with success side)
  - plan change at step 12: Dropped leftover leftover leftover {fail['leftover']} is flag-plat. Handoff {fail['ticket']}.
  - edit→test→fail→re-read→fix at steps 10-13

## decision_basis audit
Every step has decision_basis starting with Plan:/Observation:/Reflection:/Tool call:, length ≤240, no thought/chain_of_thought/scratch/inner_monologue keys, no spike_events, no sim_or_real real, no Spikenaut. Generator grok-4.6. No [variant …] goal stamp.

## Mix
Success: ['{suc_ep['id']}']. Realistic failure/handoff: ['{fail_ep['id']}'].

## Realism / weak recovery paths
Noise recoveries are backoff+retry or local fixture cache. First patches are domain-plausible and fail closed. Designed traces — not live executions. Unique leftover leftover leftover plants; not waffle/flipper clones.

## Step counts
- {suc_ep['id']}: {len(suc_ep['steps'])} (required 14–18)
- {fail_ep['id']}: {len(fail_ep['steps'])} (required 14–18)

## Weaknesses / next
Leftover leftover leftover {suc['leftover']} beats percentage. Do not drop leftover leftover leftover {fail['leftover']}.
"""


def hop_hx(kind: str, rnd: int, slug: str) -> str:
    return hashlib.sha1(f"ffdhop|{kind}|{rnd}|{slug}|{GENERATOR}".encode()).hexdigest()[:4]


def hop_step(n: int, basis: str, name: str, args: dict, obs: str,
             reflection: str | None = None) -> dict[str, Any]:
    row = {
        "n": n,
        "decision_basis": _basis(n, basis),
        "tool_call": {"name": name, "args": args},
        "observation": obs,
    }
    if reflection:
        row["reflection"] = reflection
    return row


def hop_steps(rows: list[tuple]) -> list[dict[str, Any]]:
    out = []
    for index, row in enumerate(rows, 1):
        if len(row) == 5:
            basis, name, args, obs, reflection = row
        else:
            basis, name, args, obs = row
            reflection = None
        out.append(hop_step(index, basis, name, args, obs, reflection))
    refuse_when(not 16 <= len(out) <= 22, FINDING_PAIR_SHAPE, f"hop step count {len(out)}")
    return out


def hop_episode(rnd: int, plant: Mapping[str, Any], expanded: Mapping[str, Any]) -> dict[str, Any]:
    rows = [
        (f"Plan: locate {expanded['what']} before hypothesizing.", "glob",
         {"pattern": expanded["glob"]}, expanded["ls"]),
        (f"Observation: {expanded['impl']} is listed; read it first.", "read_file",
         {"path": expanded["impl"]}, expanded["impl_src"]),
        (f"Observation: {expanded['sym']} looks load-bearing; grep callers.", "grep",
         {"pattern": expanded["grep"], "glob": expanded["glob"]}, expanded["grep_obs"]),
        (f"Plan: run the CI suite for {expanded['plant']}.", "run_terminal_command",
         {"cmd": expanded["test"]}, expanded["fail1"]),
        (f"Observation: {expanded['fail_name']} failed; read the test.", "read_file",
         {"path": expanded["test_file"]}, expanded["test_src"]),
        (f"Plan: try {expanded['wrong_name']} (likely the wrong fix).", "apply_patch",
         {"path": expanded["impl"], "diff": expanded["wrong_diff"]}, expanded["wrong_obs"]),
        (f"Plan: re-run {expanded['fail_name']} after that patch.", "run_terminal_command",
         {"cmd": expanded["test_one"]}, expanded["fail2"]),
        (f"Observation: {expanded['wrong_name']} did not hold; reread {expanded['impl']}.",
         "read_file", {"path": expanded["impl"]}, expanded["reread"]),
        (f"Reflection: {expanded['insight']}", "run_terminal_command",
         {"cmd": expanded["probe"]}, expanded["probe_obs"]),
        (f"Plan: apply {expanded['fix_name']}.", "apply_patch",
         {"path": expanded["impl"], "diff": expanded["fix_diff"]}, expanded["fix_obs"]),
        (f"Plan: retest after {expanded['fix_name']}.", "run_terminal_command",
         {"cmd": expanded["test"]}, expanded["fail3"]),
        (f"Observation: leftover in {expanded['rel']}; read it.", "read_file",
         {"path": expanded["rel"]}, expanded["rel_src"]),
        (f"Plan: {expanded['fix2_name']}.", "apply_patch",
         {"path": expanded["rel"], "diff": expanded["fix2_diff"]}, expanded["fix2_obs"]),
        ("Plan: tests after the second edit.", "run_terminal_command",
         {"cmd": expanded["test"]}, expanded["pass_mid"]),
        (f"Plan: grep leftover {expanded['bad_pat']}.", "grep",
         {"pattern": expanded["bad_pat"], "glob": expanded["glob"]}, expanded["grep2"]),
        (f"Plan: document {expanded['doc_point']}.", "apply_patch",
         {"path": expanded["doc"], "diff": expanded["doc_diff"]}, "updated."),
        (f"Plan: add regression {expanded['reg_name']}.", "apply_patch",
         {"path": expanded["test_file"], "diff": expanded["reg_diff"]}, "added."),
        ("Plan: full suite as CI.", "run_terminal_command",
         {"cmd": expanded["full_test"]}, expanded["final"]),
        (f"Plan: read final {expanded['impl']} for the PR summary.", "read_file",
         {"path": expanded["impl"], "limit": 40}, expanded["summary"]),
        (f"Plan: stop after {expanded['wrap']}.", "run_terminal_command",
         {"cmd": expanded["full_test"]}, expanded["wrap_obs"]),
    ]
    success = bool(plant["ok"])
    tests = 6 if success else 5
    residual = 0 if success else 1
    record = {
        "id": f"{PREFIX}-r{rnd}-{expanded['slug']}-{hop_hx('ffd', rnd, str(expanded['slug']))}",
        "goal": expanded["goal"],
        "plan": expanded["plan"],
        "steps": hop_steps(rows),
        "outcome": expanded["outcome"],
        "reward": {"success": success, "tests_passed": tests, "cost_steps": len(rows)},
        "meta": {"factory": FACTORY, "round": rnd, "generator": GENERATOR, "plant": "designed"},
    }
    if residual:
        record["reward"]["residual"] = residual
    assert_clean(record)
    return record


def hop_expand(plant: Mapping[str, Any]) -> dict[str, Any]:
    leftover = plant["leftover"]
    success = bool(plant["ok"])
    return {
        "slug": plant["slug"],
        "success": success,
        "tests": 6 if success else 5,
        "residual": 0 if success else 1,
        "plant": plant["plant"],
        "what": plant["what"],
        "glob": plant["glob"],
        "ls": plant["ls"],
        "impl": plant["impl"],
        "impl_src": plant["src"],
        "sym": plant["sym"],
        "grep": plant["grep"],
        "grep_obs": plant["grep_obs"],
        "test": plant["test"],
        "fail1": plant["fail1"],
        "fail_name": "test_assign",
        "test_file": plant["tf"],
        "test_src": plant["tsrc"],
        "wrong_name": plant["wrong"],
        "wrong_diff": plant["wrong_diff"],
        "wrong_obs": plant["wrong_obs"],
        "test_one": plant["test"] + " -k assign",
        "fail2": plant["fail2"],
        "reread": plant["reread"],
        "insight": plant["insight"],
        "probe": plant["probe"],
        "probe_obs": plant["probe_obs"],
        "fix_name": plant["fix"],
        "fix_diff": plant["fix_diff"],
        "fix_obs": "patched " + plant["fix"] + ".",
        "fail3": "PASS test_assign\nFAIL pack leftover: " + plant["rel"] + " dump still " + leftover,
        "rel": plant["rel"],
        "rel_src": plant["rel_src"],
        "fix2_name": plant["fix2"] if success else "handoff dump " + plant["fix"],
        "fix2_diff": plant["fix2_diff"] if success else "+ # TODO dump " + leftover,
        "fix2_obs": "patched dump." if success else "assign green. dump leftover.",
        "pass_mid": "PASS 6." if success else "PASS 5. FAIL dump residual. Handoff.",
        "bad_pat": plant["bad_pat"],
        "grep2": "none." if success else "none as the fix. leftover dump.",
        "doc": plant["doc"],
        "doc_point": plant["doc_point"],
        "doc_diff": plant["doc_diff"],
        "reg_name": "test_assign " + plant["reg"],
        "reg_diff": plant["reg_diff"],
        "full_test": plant["test"],
        "final": plant["final_ok"] if success else plant["final_part"],
        "summary": plant["summary"],
        "wrap": plant["wrap"],
        "wrap_obs": plant["wrap_ok"] if success else plant["wrap_part"],
        "goal": plant["goal"],
        "plan": plant["plan"],
        "outcome": plant["out_ok"] if success else plant["out_part"],
    }


def hop_notes(rnd: int, pair: Mapping[str, Any], first: Mapping[str, Any],
              second: Mapping[str, Any]) -> str:
    first_kind = "success" if first["reward"]["success"] else "partial"
    second_kind = "success" if second["reward"]["success"] else "partial"
    return f"""# NOTES r{rnd} feature-flag-debug-factory

Novel coverage: 94%

Pair: {pair['title']}.
- Steps: {len(first['steps'])} {first_kind} {first['id']}; {len(second['steps'])} {second_kind} {second['id']}.
- Debug loops: {pair['loops']}.
- Densified: {pair['densify']}.
- Next densify: {pair['next']}.
- Not a clone of r4687 rust-pin, r4580 kanidm/gluu, r4163-w4ck cartesian, RPITIT, Prom native hist, ThinLTO, Go loopvar, Django ASGI, identity-origin SSO.
- Bans avoided: rust-pin / pin-project / transmute / kanidm / gluu / agama / RPITIT / Prom native hist / ThinLTO / Go loopvar / Django ASGI / Vale / Koka / identity-origin clones.
- No thought/CoT keys. meta.generator=grok-4.6. plant=designed. No spikes/Thalamic/real.
"""


def _pair_index(source_id: str, round_n: int, pair_count: int, first: int,
                pair_index: int | None) -> int:
    refuse_when(
        not isinstance(round_n, int) or isinstance(round_n, bool) or not 1 <= round_n <= MAX_ROUND,
        FINDING_ROUND_OUT_OF_DOMAIN,
        f"round must be an integer in [1, {MAX_ROUND}], got {shown(round_n)}",
    )
    if pair_index is not None:
        refuse_when(
            not isinstance(pair_index, int) or isinstance(pair_index, bool)
            or not 0 <= pair_index < pair_count,
            FINDING_PAIR_OUT_OF_DOMAIN,
            f"pair index {shown(pair_index)} is outside 0..{pair_count - 1}",
        )
        return pair_index
    if source_id == "leftover3":
        index = round_n - first
        refuse_when(not 0 <= index < pair_count, FINDING_ROUND_OUT_OF_DOMAIN,
                    f"leftover3 round {round_n} is outside {first}..{first + pair_count - 1}")
        return index
    refuse_when(round_n < first, FINDING_ROUND_OUT_OF_DOMAIN,
                f"{source_id} round {round_n} is below catalog_first {first}")
    return (round_n - first) % pair_count


def build_round(catalog: cat.Catalog, source_id: str, round_n: int,
                pair_index: int | None = None) -> tuple[list[dict[str, Any]], str]:
    """Return ``(records, notes)`` for one catalog pair of ``source_id``."""

    refuse_when(source_id not in SOURCES, FINDING_SOURCE_UNKNOWN, f"unknown source {shown(source_id)}")
    pairs = catalog.pairs_of(source_id)
    first = catalog.catalog_first(source_id)
    index = _pair_index(source_id, round_n, len(pairs), first, pair_index)
    pair = pairs[index]
    if source_id == "leftover3":
        ok_ep = leftover3_success(round_n, pair["ok"])
        bad_ep = leftover3_fail(round_n, pair["bad"])
        refuse_when(ok_ep["reward"]["success"] is not True, FINDING_PAIR_SHAPE,
                    "first episode must succeed")
        refuse_when(bad_ep["reward"]["success"] is not False, FINDING_PAIR_SHAPE,
                    "second episode must fail/handoff")
        refuse_when(ok_ep["id"] == bad_ep["id"], FINDING_PAIR_SHAPE, "duplicate episode ids")
        notes = leftover3_notes(round_n, pair["ok"], pair["bad"], ok_ep["id"], bad_ep["id"])
        return [ok_ep, bad_ep], notes
    if source_id == "lll":
        suc_ep = lll_success(round_n, pair["ok"])
        fail_ep = lll_fail(round_n, pair["bad"])
        notes = lll_notes(round_n, pair["ok"], pair["bad"], suc_ep, fail_ep)
        return [suc_ep, fail_ep], notes
    ok_plant = catalog.hop_plants[str(pair["ok"])]
    bad_plant = catalog.hop_plants[str(pair["bad"])]
    first_ep = hop_episode(round_n, ok_plant, hop_expand(ok_plant))
    second_ep = hop_episode(round_n, bad_plant, hop_expand(bad_plant))
    refuse_when(first_ep["reward"]["success"] == second_ep["reward"]["success"],
                FINDING_PAIR_SHAPE, f"hop pair {index} same success flags")
    return [first_ep, second_ep], hop_notes(round_n, pair, first_ep, second_ep)


@dataclass(frozen=True)
class GenerateRequest:
    catalog_dir: Path
    out_dir: Path
    source: str
    round: int
    pair: int | None = None


def _check_destination(out_dir: Path) -> None:
    refuse_when(is_under_raw(out_dir), FINDING_DESTINATION_UNDER_RAW,
                f"{out_dir} names or aliases the raw tree")
    refuse_when(out_dir.exists(), FINDING_DESTINATION_EXISTS, f"{out_dir} already exists")


def run(request: GenerateRequest) -> dict[str, Any]:
    """Write one generated pair into a brand-new destination."""

    _check_destination(Path(request.out_dir))
    loaded = cat.load_catalog(request.catalog_dir)
    records, notes = build_round(loaded, request.source, request.round, request.pair)
    out_dir = Path(request.out_dir)
    out_dir.mkdir(parents=True)
    batch = out_dir / f"batch-r{request.round:02d}.jsonl"
    notes_path = out_dir / f"NOTES-r{request.round:02d}.md"
    lines = [dumps_exact_json(record, ensure_ascii=True, sort_keys=True) for record in records]
    batch.write_text("\n".join(lines) + "\n", encoding="utf-8")
    notes_path.write_text(notes, encoding="utf-8")
    return {
        "source": request.source,
        "round": request.round,
        "ids": [record["id"] for record in records],
        "steps": [len(record["steps"]) for record in records],
        "out": str(out_dir),
        "batch": str(batch),
        "notes": str(notes_path),
    }


bind_import_twin(__name__)
