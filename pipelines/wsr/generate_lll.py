#!/usr/bin/env python3
"""Build leftover leftover leftover (mapping-v1) episodes from catalog plants."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ._contract import (
    FACTORY,
    FAMILY_PREFIX,
    FINDING_GENERATE_GOAL,
    FINDING_GENERATE_HIDDEN,
    FINDING_GENERATE_SHAPE,
    GENERATOR,
    HANDOFF_STEPS,
    SUCCESS_STEPS,
    bind_import_twin,
    contains_hidden_reasoning_key,
    refuse_when,
)
from . import generate as gen

__all__ = [
    "build_fail",
    "build_pair",
    "build_success",
    "notes_md",
]

PLANT_KEYS = frozenset(
    {
        "slug",
        "fail",
        "mod",
        "drop",
        "stack",
        "idf",
        "evf",
        "naive",
        "bound",
        "dropk",
        "doc",
        "doc2",
        "domain",
        "ticket",
        "test_ok",
        "test_fail",
        "short",
        "dshort",
    }
)


def _db(kind: str, text: str) -> str:
    prefix = f"{kind}: "
    return (prefix + text)[:240]


def _episode_id(round_n: int, slug: str) -> str:
    return f"{FAMILY_PREFIX}-r{round_n:02d}-{slug}"


def build_success(round_n: int, plant: Mapping[str, Any]) -> dict[str, Any]:
    gen._goal_ok(
        f"Bind leftover leftover leftover {plant['stack']} {plant['idf']}; "
        f"do not raise {plant['naive']} to hide lag."
    )
    src = f"src/{plant['mod']}.py"
    cfg = f"{plant['mod']}/cfg.yml"
    test = f"tests/test_{plant['mod']}.py"
    idf, evf, naive = plant["idf"], plant["evf"], plant["naive"]
    steps = [
        gen._step(
            1,
            _db("Plan", f"list src {plant['short']} and tests before touching conversion or config."),
            gen._bash(f"ls -la src {plant['short']} tests | head -40"),
            f"{src} {cfg}\n{test}",
            f"Tree shows {src} plus tests. Run the named failing target next.",
        ),
        gen._step(
            2,
            _db("Observation", f"listing named the test files. Run `{test} -q --tb=short` to capture the failure."),
            gen._pytest(f"{test} -q --tb=short"),
            f"{test}::{plant['test_ok']} FAILED\nE   AssertionError: leftover leftover leftover stretched {naive}; {idf} unbounded",
            f"Failure is at {test}::{plant['test_ok']}. Read that test before a one-line fix.",
        ),
        gen._step(
            3,
            _db("Observation", f"{test}::{plant['test_ok']} is red. Read {test} around the assertion."),
            gen._read(test),
            f"def {plant['test_ok']}():\n    t = tune(True)\n    assert t.get({idf!r}) and {naive!r} not in t\n",
            "Test contract is visible. Search implementation symbols next.",
        ),
        gen._step(
            4,
            _db("Observation", "test file imported the production helper. Grep those symbols."),
            gen._bash(f"rg -n '{idf}|{naive}|leftover' src {plant['short']} tests"),
            f"{src}:2: return {{{naive!r}: 5}} if lag else {{}}",
            f"Grep hit {src}. Read it before editing the first match.",
        ),
        gen._step(
            5,
            _db("Observation", f"grep listed {src}. Read it before any patch."),
            gen._read(src),
            f"def tune(lag):\n    return {{{naive!r}: 5}} if lag else {{}}\n",
            "First read done. Fetch vendor docs next; do not patch on a hunch yet.",
        ),
        gen._step(
            6,
            _db("Observation", "local files are in. Need the changelog/registry before editing."),
            gen._fetch(str(plant["doc"])),
            f"GET {plant['doc']}\nHTTP/1.1 502 Bad Gateway\nBad Gateway.",
            "Call failed with upstream gateway failure. Recover with backoff.",
        ),
        gen._step(
            7,
            _db("Observation", "the prior call returned an upstream gateway failure. Retry once with 2s backoff."),
            gen._fetch(str(plant["doc"])),
            f"retry after 2s backoff; local vendor fixture\nHTTP/1.1 200 OK\nleftover leftover leftover {idf} binds resume; {naive} is a clock.",
            "Degraded path used the local fixture. Continue with that content.",
        ),
        gen._step(
            8,
            _db("Observation", "local files are in. Need the second remote document before editing."),
            gen._fetch(str(plant["doc2"])),
            f"GET {plant['doc2']}\nHTTP/1.1 429 Too Many Requests\nRetry-After: 5\nX-RateLimit-Remaining: 0",
            "Call failed with rate-limit status with Retry-After. Recover with backoff.",
        ),
        gen._step(
            9,
            _db("Observation", "the prior call returned rate-limit status with Retry-After. Sleep then retry."),
            gen._fetch(str(plant["doc2"])),
            f"sleep + jitter retry of the same URL\nHTTP/1.1 200 OK\nBind leftover leftover leftover {idf}, do not drop {plant['dropk']}.",
            "Retry succeeded. Resume the local debug plan with that document in hand.",
        ),
        gen._step(
            10,
            _db("Observation", f"docs and source are in. Apply the first patch to {src}."),
            gen._edit(src, f"    return {{{naive!r}: 5}} if lag else {{}}", f"    return {{{naive!r}: 30}} if lag else {{}}"),
            "patched 30 (still a timeout integer)",
            "Patch applied. Re-run the failing test; do not assume green.",
        ),
        gen._step(
            11,
            _db("Observation", f"edit wrote {src}. Re-run the same failing node."),
            gen._pytest(f"{test} -q --tb=short"),
            f"{test}::{plant['test_ok']} FAILED\nE   AssertionError: timeout integer cannot bind leftover leftover leftover {idf}",
            "Still red after the first patch. Re-read the implementation; hypothesis is wrong.",
        ),
        gen._step(
            12,
            _db("Observation", f"post-edit test still failed ({test}::{plant['test_ok']}). Re-read {src}."),
            gen._read(src),
            f"leftover leftover leftover is {idf}; {naive} is not the leftover leftover leftover bound",
            f"Plan change: bind leftover leftover leftover {idf} plus {evf}. {naive} is not a leftover leftover leftover bound.",
        ),
        gen._step(
            13,
            _db(
                "Reflection",
                f"bind leftover leftover leftover {idf} plus {evf}. {naive} is not a leftover leftover leftover bound.",
            ),
            gen._edit(
                src,
                f"    return {{{naive!r}: 30}} if lag else {{}}",
                f"    return {{{idf!r}: True, {evf!r}: True}} if lag else {{}}",
            ),
            f"patched leftover leftover leftover {idf}",
            "Corrective patch applied. Run the original failing node again.",
        ),
        gen._step(
            14,
            _db("Observation", "fix edit returned clean. Re-run the original failing test node."),
            gen._pytest(f"{test} -q --tb=short"),
            "1 passed in 0.16s",
            "Result recorded. Run one broader check before declaring the outcome.",
        ),
        gen._step(
            15,
            _db("Observation", f"focused run finished. Run broader check `pytest {test} -q`."),
            gen._bash(f"pytest {test} -q"),
            "3 passed in 0.28s",
            "Broader check captured. Stop; residual risk belongs in the outcome text.",
        ),
        gen._step(
            16,
            _db("Observation", "broader check is on disk. Show the diff of patched files for the handoff note."),
            gen._bash("git diff --stat | head -n 40"),
            f"diffstat for {plant['slug']}: {src} | 9 ++++++---. No other modified paths.",
            "Diff is the review artifact. No further edits.",
        ),
    ]
    eid = _episode_id(round_n, str(plant["slug"]))
    episode = {
        "id": eid,
        "goal": f"Bind leftover leftover leftover {plant['stack']} {idf}; do not raise {naive} to hide lag.",
        "plan": f"Read leftover leftover leftover-as-timeout, try 30s, then {idf} plus {evf}.",
        "steps": steps,
        "outcome": f"leftover leftover leftover {idf} bound. {naive} unused (success).",
        "reward": {
            "success": True,
            "tests_passed": 3,
            "retries": 2,
            "duration_min": 610,
            "wasted_calls": 180,
            "cost_steps": SUCCESS_STEPS,
            "plan_changes": 1,
        },
        "meta": {
            "factory": FACTORY,
            "round": round_n,
            "generator": GENERATOR,
            "kind": "episode",
            "seed": plant["slug"],
            "designed": True,
            "domain": plant["domain"],
            "stack": f"{plant['stack']} leftover leftover leftover {idf}",
        },
    }
    gen._assert_clean(episode)
    refuse_when(
        contains_hidden_reasoning_key(episode),
        FINDING_GENERATE_HIDDEN,
        f"{eid} hidden reasoning",
    )
    refuse_when(len(steps) != SUCCESS_STEPS, FINDING_GENERATE_SHAPE, f"{eid} expected {SUCCESS_STEPS} steps")
    return episode


def build_fail(round_n: int, plant: Mapping[str, Any]) -> dict[str, Any]:
    gen._goal_ok(
        f"Do not drop leftover leftover leftover {plant['stack']} {plant['dropk']} to hide {plant['idf']}."
    )
    src = f"src/{plant['drop']}.py"
    cfg = f"{plant['drop']}/cfg.yml"
    test = f"tests/test_{plant['drop']}.py"
    idf, evf, naive = plant["idf"], plant["evf"], plant["naive"]
    ticket = str(plant["ticket"])
    steps = [
        gen._step(
            1,
            _db("Plan", f"list src {plant['dshort']} and tests before touching conversion or config."),
            gen._bash(f"ls -la src {plant['dshort']} tests | head -40"),
            f"{src} {cfg}\n{test}",
            f"Tree shows {src} plus tests. Run the named failing target next.",
        ),
        gen._step(
            2,
            _db("Observation", f"listing named the test files. Run `{test} -q --tb=short` to capture the failure."),
            gen._pytest(f"{test} -q --tb=short"),
            f"{test}::{plant['test_fail']} FAILED\nE   AssertionError: leftover leftover leftover slept {naive}; drop {plant['dropk']} is not a leftover leftover leftover bind",
            f"Failure is at {test}::{plant['test_fail']}. Read that test before a one-line fix.",
        ),
        gen._step(
            3,
            _db("Observation", f"{test}::{plant['test_fail']} is red. Read {test} around the assertion."),
            gen._read(test),
            f"def {plant['test_fail']}():\n    assert {naive!r} not in tune(True)\n",
            "Test contract is visible. Search implementation symbols next.",
        ),
        gen._step(
            4,
            _db("Observation", "test file imported the production helper. Grep those symbols."),
            gen._bash(f"rg -n '{naive}|{plant['dropk']}|leftover' src {plant['dshort']} tests"),
            f"{src}:2: return {{{naive!r}: 5}} if blocked else {{}}",
            f"Grep hit {src}. Read it before editing the first match.",
        ),
        gen._step(
            5,
            _db("Observation", f"grep listed {src}. Read it before any patch."),
            gen._read(src),
            f"def tune(blocked):\n    return {{{naive!r}: 5}} if blocked else {{}}\n",
            "First read done. Fetch vendor docs next; do not patch on a hunch yet.",
        ),
        gen._step(
            6,
            _db("Observation", "local files are in. Need the changelog/registry before editing."),
            gen._fetch(str(plant["doc"])),
            f"GET {plant['doc']}\nHTTP/1.1 429 Too Many Requests\nRetry-After: 6\nX-RateLimit-Remaining: 0",
            "Call failed with rate-limit status with Retry-After. Recover with backoff.",
        ),
        gen._step(
            7,
            _db("Observation", "the prior call returned rate-limit status with Retry-After. Sleep then retry."),
            gen._fetch(str(plant["doc"])),
            f"sleep + jitter retry of the same URL\nHTTP/1.1 200 OK\nDropping {plant['dropk']} drops leftover leftover leftover; it does not bind {idf}.",
            "Retry succeeded. Continue with that document.",
        ),
        gen._step(
            8,
            _db("Observation", "local files are in. Need the second remote document before editing."),
            gen._fetch(str(plant["doc2"])),
            f"GET {plant['doc2']}\nHTTP/1.1 502 Bad Gateway\nBad Gateway.",
            "Call failed with upstream gateway failure. Recover with backoff.",
        ),
        gen._step(
            9,
            _db("Observation", "the prior call returned an upstream gateway failure. Retry once with 2s backoff."),
            gen._fetch(str(plant["doc2"])),
            f"retry after 2s backoff; local vendor fixture\nHTTP/1.1 200 OK\nTimeout cannot mint leftover leftover leftover; drop {plant['dropk']} is platform. Handoff {ticket}.",
            "Degraded path used the local fixture. Resume the local debug plan.",
        ),
        gen._step(
            10,
            _db("Observation", f"docs and source are in. Apply the first patch to {src}."),
            gen._edit(src, f"    return {{{naive!r}: 5}} if blocked else {{}}", f"    return {{{naive!r}: 0}} if blocked else {{}}"),
            "patched 0s (still a timeout integer)",
            "Patch applied. Re-run the failing test; do not assume green.",
        ),
        gen._step(
            11,
            _db("Observation", f"edit wrote {src}. Re-run the same failing node."),
            gen._pytest(f"{test} -q --tb=short"),
            f"{test}::{plant['test_fail']} FAILED\nE   AssertionError: timeout cannot mint leftover leftover leftover; dropping {plant['dropk']} is not a bind",
            "Still red after the first patch. Re-read the implementation; hypothesis is wrong.",
        ),
        gen._step(
            12,
            _db("Observation", f"post-edit test still failed ({test}::{plant['test_fail']}). Re-read {src}."),
            gen._read(src),
            f"dropping {plant['dropk']} destroys leftover leftover leftover; bind leftover leftover leftover is platform",
            f"Plan change: {plant['dropk']} drop is platform. Handoff {ticket}.",
        ),
        gen._step(
            13,
            _db("Reflection", f"{plant['dropk']} drop is platform. Handoff {ticket}."),
            gen._edit(
                f"{plant['drop']}/handoff.md",
                "",
                f"# {ticket} {plant['stack']} leftover leftover leftover {idf} owned by ws-plat",
            ),
            "ticket filed. still timeout-classed",
            "Handoff ticket written. Run the original failing node again.",
        ),
        gen._step(
            14,
            _db("Observation", "handoff edit returned clean. Re-run the original failing test node."),
            gen._pytest(f"{test} -q --tb=short"),
            f"{test}::{plant['test_fail']} FAILED  # handoff: {ticket}\n1 failed",
            "Result recorded. Run one broader check before declaring the outcome.",
        ),
        gen._step(
            15,
            _db("Observation", f"focused run finished. Run broader check `pytest {test} -q; echo {ticket}`."),
            gen._bash(f"pytest {test} -q; echo {ticket}"),
            f"1 failed, 2 passed\n{ticket}",
            "Broader check captured. Residual risk belongs in the outcome text.",
        ),
        gen._step(
            16,
            _db("Observation", "broader check is on disk. Show the diff of patched files for the handoff note."),
            gen._bash("git diff --stat | head -n 40"),
            f"diffstat for {plant['fail']}: {src} | 8 +++++---. {plant['drop']}/handoff.md added.",
            "Diff is the review artifact. Lint next.",
        ),
        gen._step(
            17,
            _db("Observation", "diffstat listed the patched files. Run a linter on those paths only."),
            gen._bash("ruff check tests || true; echo lint-end"),
            "All checks passed!\nlint-end",
            "Lint clean. Episode complete.",
        ),
    ]
    eid = _episode_id(round_n, str(plant["fail"]))
    episode = {
        "id": eid,
        "goal": f"Do not drop leftover leftover leftover {plant['stack']} {plant['dropk']} to hide {idf}.",
        "plan": f"Read leftover leftover leftover-as-timeout, try 0s, then hand off drop-{plant['dropk']}.",
        "steps": steps,
        "outcome": f"Still timeout-classed; leftover leftover leftover drop {plant['dropk']} is platform — handoff {ticket}.",
        "reward": {
            "success": False,
            "tests_passed": 2,
            "retries": 2,
            "duration_min": 640,
            "wasted_calls": 210,
            "cost_steps": HANDOFF_STEPS,
            "plan_changes": 1,
        },
        "meta": {
            "factory": FACTORY,
            "round": round_n,
            "generator": GENERATOR,
            "kind": "episode",
            "seed": plant["fail"],
            "designed": True,
            "domain": str(plant["domain"]).replace("vs", "drop-vs"),
            "stack": f"{plant['stack']} leftover leftover leftover drop {plant['dropk']}",
        },
    }
    gen._assert_clean(episode)
    refuse_when(
        contains_hidden_reasoning_key(episode),
        FINDING_GENERATE_HIDDEN,
        f"{eid} hidden reasoning",
    )
    refuse_when(len(steps) != HANDOFF_STEPS, FINDING_GENERATE_SHAPE, f"{eid} expected {HANDOFF_STEPS} steps")
    return episode


def notes_md(round_n: int, plant: Mapping[str, Any], ok_id: str, bad_id: str) -> str:
    return (
        f"# {FACTORY} — NOTES r{round_n:02d}\n\n"
        f"Novel coverage: leftover leftover leftover {plant['stack']} {plant['idf']} vs drop {plant['dropk']}. "
        f"Not r57–r88 clones. Not disruptor. Not chronicle. Not search-index.\n\n"
        f"## Episodes\n"
        f"- `{ok_id}`: 16 steps, success=True, domain={plant['domain']}, seed={plant['slug']}\n"
        f"- `{bad_id}`: 17 steps, success=False, domain=drop {plant['dropk']}, seed={plant['fail']}\n"
    )


def build_pair(round_n: int, plant: Mapping[str, Any]) -> gen.BuiltPair:
    ok_ep = build_success(round_n, plant)
    bad_ep = build_fail(round_n, plant)
    gen.validate_pair(ok_ep, bad_ep, round_n)
    notes = notes_md(round_n, plant, ok_ep["id"], bad_ep["id"])
    return gen.BuiltPair(round_n=round_n, ok=ok_ep, bad=bad_ep, notes=notes)


bind_import_twin(__name__)
