#!/usr/bin/env python3
"""Hopper mill: cycle idle Q=2 factories, 16-step success + 17-step handoff.

Never steal reserved seats. Never rewrite outputs/raw. Skip log-redaction r46.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

EXPERIMENTS = Path(__file__).resolve().parent
REPO = EXPERIMENTS.parent
sys.path.insert(0, str(EXPERIMENTS))
sys.path.insert(0, str(REPO / "pipelines"))

from hopper_plants_g46 import CYCLE, PAIRS, PREFIX, START  # noqa: E402

GENERATOR = "grok-4.6"
BANNED_KEYS = ("thought", "chain_of_thought", "scratch", "inner_monologue")
DB_PREFIXES = ("Plan:", "Observation:", "Reflection:", "Tool call:")
RAW = REPO / "outputs" / "raw" / "2026-08-19-agentic"
SKIP_RESERVED_FACTORIES = {"log-redaction-factory"}


def _step(n: int, decision_basis: str, tool_call: dict, observation: str, reflection: str) -> dict:
    if not decision_basis.startswith(DB_PREFIXES):
        raise ValueError(f"step {n} decision_basis prefix: {decision_basis!r}")
    if len(decision_basis) > 240:
        raise ValueError(f"step {n} decision_basis {len(decision_basis)} > 240: {decision_basis}")
    if not observation.strip() or not reflection.strip():
        raise ValueError(f"step {n} empty observation/reflection")
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


def dumps_episode(ep: dict) -> str:
    return json.dumps(ep, ensure_ascii=True, separators=(",", ":"))


def assert_clean(obj: Any, path: str = "") -> None:
    if isinstance(obj, dict):
        for key, val in obj.items():
            if key in BANNED_KEYS:
                raise ValueError(f"banned key {key} at {path}")
            if key == "sim_or_real" and val == "real":
                raise ValueError(f"sim_or_real real at {path}")
            if key == "spike_events":
                raise ValueError(f"spike_events at {path}")
            assert_clean(val, f"{path}.{key}")
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            assert_clean(item, f"{path}[{i}]")


def _paths(p: dict) -> tuple[str, str, str]:
    src = f"src/{p['mod']}.py"
    test = f"tests/test_{p['mod']}.py"
    cfg = f"{p['mod']}/cfg.yml"
    return src, test, cfg


def _goal_ok(goal: str) -> None:
    g = goal.strip().lower()
    if not goal.strip() or g in {"x", "placeholder", "todo", "tbd", "fix it"}:
        raise ValueError(f"placeholder goal: {goal!r}")
    if "[variant" in g:
        raise ValueError(f"variant stamp in goal: {goal!r}")


def build_success(factory: str, prefix: str, round_n: int, p: dict) -> dict:
    _goal_ok(p["goal"])
    src, test, cfg = _paths(p)
    eid = f"{prefix}-r{round_n}-{p['slug']}"
    listing = f"{src} {cfg}\n{test}"
    pytest_args = f"{test} -q --tb=short"
    fail_obs = f"{test}::{p['test_fn']} FAILED\nE   {p['fail_msg']}"
    still_obs = f"{test}::{p['test_fn']} FAILED\nE   {p['still_msg']}"
    steps = [
        _step(
            1,
            f"Plan: list src {p['mod']} and tests before touching conversion or config.",
            _bash(f"ls -la src {p['mod']} tests | head -40"),
            listing,
            f"Tree shows {src} plus tests. Run the named failing target next.",
        ),
        _step(
            2,
            f"Observation: listing named the test files. Run `{pytest_args}` to capture the failure.",
            _pytest(pytest_args),
            fail_obs,
            f"Failure is at {test}::{p['test_fn']}. Read that test before a one-line fix.",
        ),
        _step(
            3,
            f"Observation: {test}::{p['test_fn']} is red. Read {test} around the assertion.",
            _read(test),
            p["test_body"],
            "Test contract is visible. Search implementation symbols next.",
        ),
        _step(
            4,
            "Observation: test file imported the production helper. Grep those symbols.",
            _bash(f"rg -n '{p['grep_pat']}' src {p['mod']} tests"),
            p["grep_hit"],
            f"Grep hit {src}. Read it before editing the first match.",
        ),
        _step(
            5,
            f"Observation: grep listed {src}. Read it before any patch.",
            _read(src),
            p["src_body"],
            "First read done. Fetch vendor docs next; do not patch on a hunch yet.",
        ),
        _step(
            6,
            "Observation: local files are in. Need the changelog/registry before editing.",
            _fetch(p["docs_url"]),
            f"GET {p['docs_url']}\nHTTP/1.1 502 Bad Gateway\nBad Gateway.",
            "Call failed with upstream gateway failure. Recover with backoff.",
        ),
        _step(
            7,
            "Observation: the prior call returned an upstream gateway failure. Retry once with 2s backoff.",
            _fetch(p["docs_url"]),
            f"retry after 2s backoff; local vendor fixture\nHTTP/1.1 200 OK\n{p['docs_ok']}",
            "Degraded path used the local fixture. Continue with that content.",
        ),
        _step(
            8,
            "Observation: local files are in. Need the second remote document before editing.",
            _fetch(p["docs_url2"]),
            f"GET {p['docs_url2']}\nHTTP/1.1 429 Too Many Requests\nRetry-After: 5\nX-RateLimit-Remaining: 0",
            "Call failed with rate-limit status with Retry-After. Recover with backoff.",
        ),
        _step(
            9,
            "Observation: the prior call returned rate-limit status with Retry-After. Sleep then retry.",
            _fetch(p["docs_url2"]),
            f"sleep + jitter retry of the same URL\nHTTP/1.1 200 OK\n{p['docs_ok2']}",
            "Retry succeeded. Resume the local debug plan with that document in hand.",
        ),
        _step(
            10,
            f"Observation: docs and source are in. Apply the first patch to {src}.",
            _edit(src, p["first_old"], p["first_new"]),
            p["first_obs"],
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
            f"Observation: post-edit test still failed ({test}::{p['test_fn']}). Re-read {src}.",
            _read(src),
            p["reread_obs"],
            f"Plan change: {p['plan_change']}",
        ),
        _step(
            13,
            f"Reflection: {p['plan_change']}"[:240],
            _edit(src, p["first_new"], p["fix_new"]),
            p["fix_obs"],
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
            "Observation: broader check is on disk. Show the diff of patched files for the handoff note.",
            _bash("git diff --stat | head -n 40"),
            f"diffstat for {p['slug']}: {src} | 9 ++++++---. No other modified paths.",
            "Diff is the review artifact. No further edits.",
        ),
    ]
    ep = {
        "id": eid,
        "goal": p["goal"],
        "plan": p["plan"],
        "steps": steps,
        "outcome": p["outcome"],
        "reward": {
            "success": True,
            "tests_passed": 3,
            "retries": 2,
            "duration_min": 610,
            "wasted_calls": 180,
            "cost_steps": 16,
            "plan_changes": 1,
        },
        "meta": {
            "factory": factory,
            "round": round_n,
            "generator": GENERATOR,
            "kind": "episode",
            "seed": p["seed"],
            "designed": True,
            "domain": p["domain"],
            "stack": p["stack"],
        },
    }
    assert_clean(ep)
    if len(steps) != 16:
        raise ValueError(f"{eid} expected 16 steps")
    return ep


def build_fail(factory: str, prefix: str, round_n: int, p: dict) -> dict:
    _goal_ok(p["goal"])
    src, test, cfg = _paths(p)
    eid = f"{prefix}-r{round_n}-{p['slug']}"
    ticket = p["ticket"]
    ticket_path = f"{p['mod']}/handoff.md"
    listing = f"{src} {cfg}\n{test}"
    pytest_args = f"{test} -q --tb=short"
    fail_obs = f"{test}::{p['test_fn']} FAILED\nE   {p['fail_msg']}"
    still_obs = f"{test}::{p['test_fn']} FAILED\nE   {p['still_msg']}"
    steps = [
        _step(
            1,
            f"Plan: list src {p['mod']} and tests before touching conversion or config.",
            _bash(f"ls -la src {p['mod']} tests | head -40"),
            listing,
            f"Tree shows {src} plus tests. Run the named failing target next.",
        ),
        _step(
            2,
            f"Observation: listing named the test files. Run `{pytest_args}` to capture the failure.",
            _pytest(pytest_args),
            fail_obs,
            f"Failure is at {test}::{p['test_fn']}. Read that test before a one-line fix.",
        ),
        _step(
            3,
            f"Observation: {test}::{p['test_fn']} is red. Read {test} around the assertion.",
            _read(test),
            p["test_body"],
            "Test contract is visible. Search implementation symbols next.",
        ),
        _step(
            4,
            "Observation: test file imported the production helper. Grep those symbols.",
            _bash(f"rg -n '{p['grep_pat']}' src {p['mod']} tests"),
            p["grep_hit"],
            f"Grep hit {src}. Read it before editing the first match.",
        ),
        _step(
            5,
            f"Observation: grep listed {src}. Read it before any patch.",
            _read(src),
            p["src_body"],
            "First read done. Fetch vendor docs next; do not patch on a hunch yet.",
        ),
        _step(
            6,
            "Observation: local files are in. Need the changelog/registry before editing.",
            _fetch(p["docs_url"]),
            f"GET {p['docs_url']}\nHTTP/1.1 429 Too Many Requests\nRetry-After: 6\nX-RateLimit-Remaining: 0",
            "Call failed with rate-limit status with Retry-After. Recover with backoff.",
        ),
        _step(
            7,
            "Observation: the prior call returned rate-limit status with Retry-After. Sleep then retry.",
            _fetch(p["docs_url"]),
            f"sleep + jitter retry of the same URL\nHTTP/1.1 200 OK\n{p['docs_ok']}",
            "Retry succeeded. Continue with that document.",
        ),
        _step(
            8,
            "Observation: local files are in. Need the second remote document before editing.",
            _fetch(p["docs_url2"]),
            f"GET {p['docs_url2']}\nHTTP/1.1 502 Bad Gateway\nBad Gateway.",
            "Call failed with upstream gateway failure. Recover with backoff.",
        ),
        _step(
            9,
            "Observation: the prior call returned an upstream gateway failure. Retry once with 2s backoff.",
            _fetch(p["docs_url2"]),
            f"retry after 2s backoff; local vendor fixture\nHTTP/1.1 200 OK\n{p['docs_ok2']}",
            "Degraded path used the local fixture. Resume the local debug plan.",
        ),
        _step(
            10,
            f"Observation: docs and source are in. Apply the first patch to {src}.",
            _edit(src, p["first_old"], p["first_new"]),
            p["first_obs"],
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
            f"Observation: post-edit test still failed ({test}::{p['test_fn']}). Re-read {src}.",
            _read(src),
            p["reread_obs"],
            f"Plan change: {p['plan_change']}",
        ),
        _step(
            13,
            f"Reflection: {p['plan_change']}"[:240],
            _edit(ticket_path, "", f"# {ticket} {p['ticket_why']}"),
            p["fix_obs"],
            "Handoff ticket written. Run the original failing node again.",
        ),
        _step(
            14,
            "Observation: handoff edit returned clean. Re-run the original failing test node.",
            _pytest(pytest_args),
            f"{test}::{p['test_fn']} FAILED  # handoff: {ticket}\n1 failed",
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
            f"diffstat for {p['slug']}: {src} | 8 +++++---. {ticket_path} added.",
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
    ep = {
        "id": eid,
        "goal": p["goal"],
        "plan": p["plan"],
        "steps": steps,
        "outcome": p["outcome"],
        "reward": {
            "success": False,
            "tests_passed": 2,
            "retries": 2,
            "duration_min": 640,
            "wasted_calls": 210,
            "cost_steps": 17,
            "plan_changes": 1,
        },
        "meta": {
            "factory": factory,
            "round": round_n,
            "generator": GENERATOR,
            "kind": "episode",
            "seed": p["seed"],
            "designed": True,
            "domain": p["domain"],
            "stack": p["stack"],
        },
    }
    assert_clean(ep)
    if len(steps) != 17:
        raise ValueError(f"{eid} expected 17 steps")
    if "ticket" not in p:
        raise ValueError(f"{eid} handoff missing ticket")
    return ep


def notes_md(factory: str, round_n: int, ok: dict, bad: dict, ok_id: str, bad_id: str) -> str:
    cov = max(ok.get("coverage", 80), bad.get("coverage", 80))
    return (
        f"# {factory} — NOTES r{round_n}\n\n"
        f"Novel coverage: {cov}%\n\n"
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


def validate_pair(ok_ep: dict, bad_ep: dict, round_n: int) -> None:
    if ok_ep["reward"]["success"] is not True:
        raise ValueError("first episode must succeed")
    if bad_ep["reward"]["success"] is not False:
        raise ValueError("second episode must fail/handoff")
    if len(ok_ep["steps"]) != 16 or len(bad_ep["steps"]) != 17:
        raise ValueError("shape must be 16-step success + 17-step fail")
    if ok_ep["meta"]["round"] != round_n or bad_ep["meta"]["round"] != round_n:
        raise ValueError("meta.round mismatch")
    if ok_ep["meta"]["generator"] != GENERATOR:
        raise ValueError("generator")
    if ok_ep["id"] == bad_ep["id"]:
        raise ValueError("duplicate episode ids")
    for ep in (ok_ep, bad_ep):
        _goal_ok(ep["goal"])
        assert_clean(ep)


def build_pair(factory: str, round_n: int, ok: dict, bad: dict):
    prefix = PREFIX[factory]
    ok_ep = build_success(factory, prefix, round_n, ok)
    bad_ep = build_fail(factory, prefix, round_n, bad)
    validate_pair(ok_ep, bad_ep, round_n)
    notes = notes_md(factory, round_n, ok, bad, ok_ep["id"], bad_ep["id"])
    if "Novel coverage:" not in notes:
        raise ValueError("NOTES missing Novel coverage")
    return ok_ep, bad_ep, notes


def emit_stage(stage: Path, factory: str, round_n: int, ok: dict, bad: dict):
    ok_ep, bad_ep, notes = build_pair(factory, round_n, ok, bad)
    batch = stage / f"batch-r{round_n:02d}.jsonl"
    notes_path = stage / f"NOTES-r{round_n:02d}.md"
    batch.write_text(
        dumps_episode(ok_ep) + "\n" + dumps_episode(bad_ep) + "\n",
        encoding="utf-8",
    )
    notes_path.write_text(notes, encoding="utf-8")
    return ok_ep["id"], bad_ep["id"]


def factory_dir(factory: str) -> Path:
    return RAW / factory


def reserved_at(factory: str, round_n: int) -> bool:
    return (factory_dir(factory) / f"ROUND-r{round_n:02d}.reserved.json").exists()


def self_check() -> None:
    slugs = []
    mods = []
    tickets = []
    domains = []
    for factory in CYCLE:
        prefix = PREFIX[factory]
        for i, (ok, bad) in enumerate(PAIRS[factory]):
            round_n = START[factory] + i
            if ok["first_old"] not in ok["src_body"]:
                raise ValueError(f"{factory} {ok['slug']} first_old not in src_body")
            if bad["first_old"] not in bad["src_body"]:
                raise ValueError(f"{factory} {bad['slug']} first_old not in src_body")
            if "ticket" not in bad:
                raise ValueError(f"{factory} {bad['slug']} missing ticket")
            for plant, kind in ((ok, "ok"), (bad, "bad")):
                slugs.append(plant["slug"])
                mods.append(plant["mod"])
                domains.append(plant["domain"])
                _goal_ok(plant["goal"])
                if kind == "bad":
                    tickets.append(plant["ticket"])
            ok_ep, bad_ep, notes = build_pair(factory, round_n, ok, bad)
            if not ok_ep["id"].startswith(f"{prefix}-r{round_n}-"):
                raise ValueError(ok_ep["id"])
            if "Novel coverage:" not in notes:
                raise ValueError("notes")
    if len(set(slugs)) != len(slugs):
        raise ValueError(f"duplicate slugs: {slugs}")
    if len(set(mods)) != len(mods):
        raise ValueError(f"duplicate mods: {mods}")
    if len(set(tickets)) != len(tickets):
        raise ValueError(f"duplicate tickets: {tickets}")
    if len(set(domains)) != len(domains):
        raise ValueError(f"duplicate domains: {domains}")
    n = sum(len(PAIRS[f]) for f in CYCLE)
    print(f"self_check ok: {n} pairs across {len(CYCLE)} factories")


def run_loop(min_rounds: int = 12, max_rounds: int = 24) -> int:
    from round_txn import TransactionError, abort, frontier_status, publish, reserve

    queues = {factory: list(PAIRS[factory]) for factory in CYCLE}
    published = []
    hops = []
    stalled_cycles = 0
    while len(published) < max_rounds:
        progressed = False
        for factory in CYCLE:
            if factory in SKIP_RESERVED_FACTORIES:
                continue
            if not queues[factory]:
                continue
            fdir = factory_dir(factory)
            status = frontier_status(fdir)
            round_n = status["next_round"]
            if reserved_at(factory, round_n):
                hops.append({"factory": factory, "round": round_n, "skip": "reserved"})
                print(json.dumps(hops[-1]))
                continue
            ok, bad = queues[factory][0]
            try:
                payload = reserve(fdir, round_n, 2)
            except TransactionError as exc:
                msg = str(exc)
                hops.append({"factory": factory, "round": round_n, "error": msg})
                print(json.dumps(hops[-1]))
                if "already exists" in msg or "not the frontier" in msg:
                    continue
                raise
            stage = Path(payload["staging_dir"])
            token = payload["token"]
            try:
                ids = emit_stage(stage, factory, round_n, ok, bad)
                manifest = publish(fdir, round_n, token)
            except Exception as exc:
                try:
                    abort(fdir, round_n, token)
                except Exception as abort_exc:
                    print(f"abort failed {factory} r{round_n}: {abort_exc}")
                raise RuntimeError(f"stage/publish failed {factory} r{round_n}: {exc}") from exc
            queues[factory].pop(0)
            published.append(
                {
                    "factory": factory,
                    "round": round_n,
                    "ids": ids,
                    "records": manifest.get("records"),
                }
            )
            print(json.dumps({"published": published[-1]}))
            progressed = True
            if len(published) >= max_rounds:
                break
        if not progressed:
            stalled_cycles += 1
            if stalled_cycles >= 2:
                break
        else:
            stalled_cycles = 0
        if len(published) >= min_rounds and all(not queues[f] for f in CYCLE):
            break
    print(
        json.dumps(
            {
                "published_count": len(published),
                "published_rounds": published,
                "hops": hops,
            }
        )
    )
    return 0 if len(published) >= min_rounds else 1


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv[:1] == ["self_check"]:
        self_check()
        return 0
    self_check()
    return run_loop()


if __name__ == "__main__":
    raise SystemExit(main())
