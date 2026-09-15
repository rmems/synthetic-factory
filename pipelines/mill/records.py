#!/usr/bin/env python3
"""Assemble one mill success/fail episode pair from a plant.

Prose is family-owned. Leftover mill leftover-token spam is not copied.
Ids use the mill prefix; meta names this family's factory and generator.
"""

from __future__ import annotations

from typing import Any

from . import catalog as cat
from . import vocabulary as cv
from ._contract import bind_import_twin

__all__ = ["fail_episode", "notes", "success_episode"]


def _db(kind: str, text: str) -> str:
    basis = f"{kind}: {text}"
    cv.refuse_when(
        not basis.startswith(cv.DB_PREFIXES),
        cv.FINDING_DECISION_BASIS_INVALID,
        f"decision_basis must start with {cv.DB_PREFIXES}, got {cv.shown(basis[:40])}",
    )
    cv.refuse_when(
        len(basis) > cv.MAX_DECISION_BASIS,
        cv.FINDING_DECISION_BASIS_INVALID,
        f"decision_basis length {len(basis)} exceeds {cv.MAX_DECISION_BASIS}",
    )
    return basis


def _step(n: int, kind: str, text: str, tool: dict[str, Any], observation: str, reflection: str) -> dict[str, Any]:
    return {
        "n": n,
        "decision_basis": _db(kind, text),
        "tool_call": tool,
        "observation": observation,
        "reflection": reflection,
    }


def _bash(command: str) -> dict[str, Any]:
    return {"name": "bash", "args": {"command": command}}


def _read(path: str) -> dict[str, Any]:
    return {"name": "read", "args": {"path": path}}


def _edit(path: str, old: str, new: str) -> dict[str, Any]:
    return {"name": "edit", "args": {"path": path, "old": old, "new": new}}


def _fetch(url: str) -> dict[str, Any]:
    return {"name": "fetch", "args": {"url": url}}


def _pytest(args: str) -> dict[str, Any]:
    return {"name": "pytest", "args": {"args": args}}


def _meta(round_n: int, seed: str, domain: str, stack: str) -> dict[str, Any]:
    return {
        "factory": cv.FACTORY_ID,
        "round": round_n,
        "generator": cv.GENERATOR_NAME,
        "generator_version": cv.GENERATOR_VERSION,
        "generator_kind": cv.GENERATOR_KIND,
        "kind": cv.RECORD_KIND,
        "seed": seed,
        "designed": True,
        "domain": domain,
        "stack": stack,
    }


def _domain(plant: cat.Plant, *, dropped: bool) -> str:
    infix = "drop" if dropped else "plus"
    return f"{plant.short}-{plant.identity_field}-{infix}-{plant.event_field}"


def success_episode(round_n: int, plant: cat.Plant) -> dict[str, Any]:
    """16-step success: naive key, identity-only miss, then (identity, event) bind."""
    src = f"src/{plant.module}.py"
    test = f"tests/test_{plant.module}.py"
    idf, evf, naive = plant.identity_field, plant.event_field, plant.naive_field
    naive_return = f"    return ev[{naive!r}]"
    half = f"    return ev.get({idf!r}) or ev[{naive!r}]"
    bound = f"    return (ev[{idf!r}], ev[{evf!r}])"
    steps = [
        _step(1, cv.DB_PLAN, f"list src {plant.short} and tests before touching conversion or config.",
              _bash(f"ls -la src {plant.short} tests | head -40"),
              f"{src} {plant.module}/cfg.yml\n{test}",
              f"Tree shows {src} plus tests. Run the named failing target next."),
        _step(2, cv.DB_OBSERVATION, f"listing named the test files. Run `{test} -q --tb=short`.",
              _pytest(f"{test} -q --tb=short"),
              f"{test}::{plant.test_ok} FAILED\nE   AssertionError: {naive} PK collapsed retry events",
              f"Failure is at {test}::{plant.test_ok}. Read that test before a one-line fix."),
        _step(3, cv.DB_OBSERVATION, f"{test}::{plant.test_ok} is red. Read {test} around the assertion.",
              _read(test),
              f"def {plant.test_ok}():\n    assert pk({{{idf!r}: 'm1', {evf!r}: 'open', {naive!r}: 'a@b'}}) == ('m1', 'open')\n",
              "Test contract is visible. Search implementation symbols next."),
        _step(4, cv.DB_OBSERVATION, "test file imported the production helper. Grep those symbols.",
              _bash(f"rg -n '{idf}|{evf}|{naive}' src {plant.short} tests"),
              f"{src}:2: return ev[{naive!r}]",
              f"Grep hit {src}. Read it before editing the first match."),
        _step(5, cv.DB_OBSERVATION, f"grep listed {src}. Read it before any patch.",
              _read(src), f"def pk(ev):\n{naive_return}\n",
              "First read done. Fetch vendor docs next; do not patch on a hunch yet."),
        _step(6, cv.DB_OBSERVATION, "local files are in. Need the changelog/registry before editing.",
              _fetch(plant.docs[0]), f"GET {plant.docs[0]}\nHTTP/1.1 502 Bad Gateway\nBad Gateway.",
              "Call failed with upstream gateway failure. Recover with backoff."),
        _step(7, cv.DB_OBSERVATION, "the prior call returned an upstream gateway failure. Retry once with 2s backoff.",
              _fetch(plant.docs[0]),
              f"retry after 2s backoff; local vendor fixture\nHTTP/1.1 200 OK\n{plant.provider} events unique on {idf} plus {evf}, not {naive}.",
              "Degraded path used the local fixture. Continue with that content."),
        _step(8, cv.DB_OBSERVATION, "local files are in. Need the second remote document before editing.",
              _fetch(plant.docs[1]),
              f"GET {plant.docs[1]}\nHTTP/1.1 429 Too Many Requests\nRetry-After: 5\nX-RateLimit-Remaining: 0",
              "Call failed with rate-limit status with Retry-After. Recover with backoff."),
        _step(9, cv.DB_OBSERVATION, "the prior call returned rate-limit status with Retry-After. Sleep then retry.",
              _fetch(plant.docs[1]),
              f"sleep + jitter retry of the same URL\nHTTP/1.1 200 OK\nDo not drop {evf}.",
              "Retry succeeded. Resume the local debug plan with that document in hand."),
        _step(10, cv.DB_OBSERVATION, f"docs and source are in. Apply the first patch to {src}.",
              _edit(src, naive_return, half),
              f"patched {idf} (dropped {evf}; retries collide)",
              "Patch applied. Re-run the failing test; do not assume green."),
        _step(11, cv.DB_OBSERVATION, f"edit wrote {src}. Re-run the same failing node.",
              _pytest(f"{test} -q --tb=short"),
              f"{test}::{plant.test_ok} FAILED\nE   AssertionError: id without {evf} still collides",
              "Still red after the first patch. Re-read the implementation; hypothesis is wrong."),
        _step(12, cv.DB_OBSERVATION, f"post-edit test still failed ({test}::{plant.test_ok}). Re-read {src}.",
              _read(src), f"{plant.provider} PK is ({idf}, {evf}); {naive} is the recipient",
              f"Plan change: bind ({idf}, {evf}). {naive} is not PK."),
        _step(13, cv.DB_REFLECTION, f"Bind ({idf}, {evf}). {naive} is not PK.",
              _edit(src, half, bound), f"patched ({idf}, {evf})",
              "Corrective patch applied. Run the original failing node again."),
        _step(14, cv.DB_OBSERVATION, "fix edit returned clean. Re-run the original failing test node.",
              _pytest(f"{test} -q --tb=short"), "1 passed in 0.16s",
              "Result recorded. Run one broader check before declaring the outcome."),
        _step(15, cv.DB_OBSERVATION, f"focused run finished. Run broader check `pytest {test} -q`.",
              _bash(f"pytest {test} -q"), "3 passed in 0.28s",
              "Broader check captured. Stop; residual risk belongs in the outcome text."),
        _step(16, cv.DB_OBSERVATION, "broader check is on disk. Show the diff of patched files for the handoff note.",
              _bash("git diff --stat | head -n 40"),
              f"diffstat for {plant.plant_id}: {src} | 9 ++++++---. No other modified paths.",
              "Diff is the review artifact. No further edits."),
    ]
    cv.refuse_when(len(steps) != cv.SUCCESS_STEPS, cv.FINDING_STEP_COUNT_INVALID, "success step count drifted")
    return {
        "id": cv.record_id(round_n, plant.plant_id),
        "goal": f"Dedupe {plant.provider} events on ({idf}, {evf}), not {naive}.",
        "plan": f"Read {naive}-as-pk, try {idf} only, then bind ({idf}, {evf}).",
        "steps": steps,
        "outcome": f"Bound ({idf}, {evf}). {naive} unused (success).",
        "reward": {
            "success": True, "tests_passed": 3, "retries": 2, "duration_min": 610,
            "wasted_calls": 180, "cost_steps": cv.SUCCESS_STEPS, "plan_changes": 1,
        },
        "meta": _meta(round_n, plant.plant_id, _domain(plant, dropped=False), f"{plant.provider} identity-bind"),
    }


def fail_episode(round_n: int, plant: cat.Plant) -> dict[str, Any]:
    """17-step handoff: dropping the event field stays red; ticket the grain."""
    src = f"src/{plant.drop_module}.py"
    test = f"tests/test_{plant.drop_module}.py"
    idf, evf, naive = plant.identity_field, plant.event_field, plant.naive_field
    naive_return = f"    return ev[{naive!r}]"
    half = f"    return ev.get({idf!r})"
    steps = [
        _step(1, cv.DB_PLAN, f"list src {plant.dshort} and tests before touching conversion or config.",
              _bash(f"ls -la src {plant.dshort} tests | head -40"),
              f"{src} {plant.drop_module}/cfg.yml\n{test}",
              f"Tree shows {src} plus tests. Run the named failing target next."),
        _step(2, cv.DB_OBSERVATION, f"listing named the test files. Run `{test} -q --tb=short`.",
              _pytest(f"{test} -q --tb=short"),
              f"{test}::{plant.test_fail} FAILED\nE   AssertionError: dropped {evf}; {naive}-as-key collapsed bounce",
              f"Failure is at {test}::{plant.test_fail}. Read that test before a one-line fix."),
        _step(3, cv.DB_OBSERVATION, f"{test}::{plant.test_fail} is red. Read {test} around the assertion.",
              _read(test),
              f"def {plant.test_fail}():\n    assert pk({{{idf!r}: 'm1', {evf!r}: 'bounce', {naive!r}: 'a@b'}}) != ev_{naive}_only()\n",
              "Test contract is visible. Search implementation symbols next."),
        _step(4, cv.DB_OBSERVATION, "test file imported the production helper. Grep those symbols.",
              _bash(f"rg -n '{evf}|{naive}|drop' src {plant.dshort} tests"),
              f"{src}:2: return ev[{naive!r}]",
              f"Grep hit {src}. Read it before editing the first match."),
        _step(5, cv.DB_OBSERVATION, f"grep listed {src}. Read it before any patch.",
              _read(src), f"def pk(ev):\n{naive_return}\n",
              "First read done. Fetch vendor docs next; do not patch on a hunch yet."),
        _step(6, cv.DB_OBSERVATION, "local files are in. Need the changelog/registry before editing.",
              _fetch(plant.docs[0]),
              f"GET {plant.docs[0]}\nHTTP/1.1 429 Too Many Requests\nRetry-After: 6\nX-RateLimit-Remaining: 0",
              "Call failed with rate-limit status with Retry-After. Recover with backoff."),
        _step(7, cv.DB_OBSERVATION, "the prior call returned rate-limit status with Retry-After. Sleep then retry.",
              _fetch(plant.docs[0]),
              f"sleep + jitter retry of the same URL\nHTTP/1.1 200 OK\n{evf} is event grain; dropping it is not a recipient key.",
              "Retry succeeded. Continue with that document."),
        _step(8, cv.DB_OBSERVATION, "local files are in. Need the second remote document before editing.",
              _fetch(plant.docs[1]), f"GET {plant.docs[1]}\nHTTP/1.1 502 Bad Gateway\nBad Gateway.",
              "Call failed with upstream gateway failure. Recover with backoff."),
        _step(9, cv.DB_OBSERVATION, "the prior call returned an upstream gateway failure. Retry once with 2s backoff.",
              _fetch(plant.docs[1]),
              f"retry after 2s backoff; local vendor fixture\nHTTP/1.1 200 OK\nHandoff {plant.ticket}.",
              "Degraded path used the local fixture. Resume the local debug plan."),
        _step(10, cv.DB_OBSERVATION, f"docs and source are in. Apply the first patch to {src}.",
              _edit(src, naive_return, half), f"patched {idf} (still dropped {evf})",
              "Patch applied. Re-run the failing test; do not assume green."),
        _step(11, cv.DB_OBSERVATION, f"edit wrote {src}. Re-run the same failing node.",
              _pytest(f"{test} -q --tb=short"),
              f"{test}::{plant.test_fail} FAILED\nE   AssertionError: dropping {evf} still collapses types",
              "Still red after the first patch. Re-read the implementation; hypothesis is wrong."),
        _step(12, cv.DB_OBSERVATION, f"post-edit test still failed ({test}::{plant.test_fail}). Re-read {src}.",
              _read(src), f"Dropped {evf} is platform grain; cannot bind {naive}-as-key",
              f"Plan change: dropped {evf} is ESP-plat. Handoff {plant.ticket}."),
        _step(13, cv.DB_REFLECTION, f"Dropped {evf} is ESP-plat. Handoff {plant.ticket}.",
              _edit(f"{plant.drop_module}/handoff.md", "", f"# {plant.ticket} {plant.provider} {evf} grain"),
              f"ticket filed. still drop-{evf}",
              "Handoff ticket written. Run the original failing node again."),
        _step(14, cv.DB_OBSERVATION, "handoff edit returned clean. Re-run the original failing test node.",
              _pytest(f"{test} -q --tb=short"),
              f"{test}::{plant.test_fail} FAILED  # handoff: {plant.ticket}\n1 failed",
              "Result recorded. Run one broader check before declaring the outcome."),
        _step(15, cv.DB_OBSERVATION, f"focused run finished. Run broader check `pytest {test} -q; echo {plant.ticket}`.",
              _bash(f"pytest {test} -q; echo {plant.ticket}"),
              f"1 failed, 2 passed\n{plant.ticket}",
              "Broader check captured. Residual risk belongs in the outcome text."),
        _step(16, cv.DB_OBSERVATION, "broader check is on disk. Show the diff of patched files for the handoff note.",
              _bash("git diff --stat | head -n 40"),
              f"diffstat for {plant.fail_id}: {src} | 8 +++++---. {plant.drop_module}/handoff.md added.",
              "Diff is the review artifact. Lint next."),
        _step(17, cv.DB_OBSERVATION, "diffstat listed the patched files. Run a linter on those paths only.",
              _bash("ruff check tests || true; echo lint-end"), "All checks passed!\nlint-end",
              "Lint clean. Episode complete."),
    ]
    cv.refuse_when(len(steps) != cv.FAIL_STEPS, cv.FINDING_STEP_COUNT_INVALID, "fail step count drifted")
    return {
        "id": cv.record_id(round_n, plant.fail_id),
        "goal": f"Do not drop {plant.provider} {evf} when binding the id.",
        "plan": f"Read drop-{evf}, try {naive}, then hand off dropped {evf} grain.",
        "steps": steps,
        "outcome": f"Still drop-{evf}; {evf} grain is {plant.provider} — handoff {plant.ticket}.",
        "reward": {
            "success": False, "tests_passed": 2, "retries": 2, "duration_min": 640,
            "wasted_calls": 210, "cost_steps": cv.FAIL_STEPS, "plan_changes": 1,
        },
        "meta": _meta(round_n, plant.fail_id, _domain(plant, dropped=True), f"{plant.provider} identity-bind"),
    }


def notes(round_n: int, plant: cat.Plant) -> str:
    """Operator notes for one pair. Novel coverage is a real field pair, not leftover tokens."""
    ok = cv.record_id(round_n, plant.plant_id)
    bad = cv.record_id(round_n, plant.fail_id)
    return (
        f"# {cv.FACTORY_ID} — NOTES r{round_n:02d}\n\n"
        f"Novel coverage: {plant.provider} ({plant.identity_field}, {plant.event_field}) "
        f"vs drop {plant.event_field}.\n\n"
        f"## Episodes\n"
        f"- `{ok}`: {cv.SUCCESS_STEPS} steps, success=True, seed={plant.plant_id}\n"
        f"  - 502 at step 6 recovered 7; 429 at step 8 recovered 9\n"
        f"  - plan change at step 12: bind ({plant.identity_field}, {plant.event_field})\n"
        f"- `{bad}`: {cv.FAIL_STEPS} steps, success=False, seed={plant.fail_id}\n"
        f"  - 429 at step 6 recovered 7; 502 at step 8 recovered 9\n"
        f"  - plan change at step 12: handoff {plant.ticket}\n"
    )


bind_import_twin(__name__)
