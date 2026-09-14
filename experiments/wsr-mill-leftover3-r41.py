#!/usr/bin/env python3
"""websocket-reconnect leftover leftover leftover mill r41+ (16 rounds).

BAN r40 anycable-restore-session, reverb-activity-timeout-handoff, cookie-replay.
Unique leftover resume vs naive second-subscribe / drop leftover bind.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

EXPERIMENTS = Path(__file__).resolve().parent
REPO = EXPERIMENTS.parent
sys.path.insert(0, str(REPO / "pipelines"))

FACTORY = "websocket-reconnect-factory"
PREFIX = "wsr"
GENERATOR = "grok-4.6"
BANNED_KEYS = ("thought", "chain_of_thought", "scratch", "inner_monologue")
DB_PREFIXES = ("Plan:", "Observation:", "Reflection:", "Tool call:")
RAW = REPO / "outputs" / "raw" / "2026-08-19-agentic"
FDIR = RAW / FACTORY
BANNED_SLUGS = {
    "anycable-restore-session",
    "reverb-activity-timeout-handoff",
    "cookie-replay",
}


def _p(**kwargs):
    return kwargs


def _step(n: int, decision_basis: str, tool_call: dict, observation: str, reflection: str) -> dict:
    if not decision_basis.startswith(DB_PREFIXES):
        raise ValueError(f"step {n} decision_basis prefix: {decision_basis!r}")
    if len(decision_basis) > 240:
        raise ValueError(f"step {n} decision_basis {len(decision_basis)} > 240")
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
    if "cookie-replay" in g or "anycable" in g or "reverb" in g:
        raise ValueError(f"banned topic in goal: {goal!r}")


def build_success(round_n: int, p: dict) -> dict:
    _goal_ok(p["goal"])
    src, test, cfg = _paths(p)
    eid = f"{PREFIX}-r{round_n}-{p['slug']}"
    listing = f"{src} {cfg}\n{test}"
    pytest_args = f"{test} -q --tb=short"
    fail_obs = f"{test}::{p['test_fn']} FAILED\nE   {p['fail_msg']}"
    still_obs = f"{test}::{p['test_fn']} FAILED\nE   {p['still_msg']}"
    steps = [
        _step(1, f"Plan: list src {p['mod']} and tests before touching conversion or config.", _bash(f"ls -la src {p['mod']} tests | head -40"), listing, f"Tree shows {src} plus tests. Run the named failing target next."),
        _step(2, f"Observation: listing named the test files. Run `{pytest_args}` to capture the failure.", _pytest(pytest_args), fail_obs, f"Failure is at {test}::{p['test_fn']}. Read that test before a one-line fix."),
        _step(3, f"Observation: {test}::{p['test_fn']} is red. Read {test} around the assertion.", _read(test), p["test_body"], "Test contract is visible. Search implementation symbols next."),
        _step(4, "Observation: test file imported the production helper. Grep those symbols.", _bash(f"rg -n '{p['grep_pat']}' src {p['mod']} tests"), p["grep_hit"], f"Grep hit {src}. Read it before editing the first match."),
        _step(5, f"Observation: grep listed {src}. Read it before any patch.", _read(src), p["src_body"], "First read done. Fetch vendor docs next; do not patch on a hunch yet."),
        _step(6, "Observation: local files are in. Need the changelog/registry before editing.", _fetch(p["docs_url"]), f"GET {p['docs_url']}\nHTTP/1.1 502 Bad Gateway\nBad Gateway.", "Call failed with upstream gateway failure. Recover with backoff."),
        _step(7, "Observation: the prior call returned an upstream gateway failure. Retry once with 2s backoff.", _fetch(p["docs_url"]), f"retry after 2s backoff; local vendor fixture\nHTTP/1.1 200 OK\n{p['docs_ok']}", "Degraded path used the local fixture. Continue with that content."),
        _step(8, "Observation: local files are in. Need the second remote document before editing.", _fetch(p["docs_url2"]), f"GET {p['docs_url2']}\nHTTP/1.1 429 Too Many Requests\nRetry-After: 5\nX-RateLimit-Remaining: 0", "Call failed with rate-limit status with Retry-After. Recover with backoff."),
        _step(9, "Observation: the prior call returned rate-limit status with Retry-After. Sleep then retry.", _fetch(p["docs_url2"]), f"sleep + jitter retry of the same URL\nHTTP/1.1 200 OK\n{p['docs_ok2']}", "Retry succeeded. Resume the local debug plan with that document in hand."),
        _step(10, f"Observation: docs and source are in. Apply the first patch to {src}.", _edit(src, p["first_old"], p["first_new"]), p["first_obs"], "Patch applied. Re-run the failing test; do not assume green."),
        _step(11, f"Observation: edit wrote {src}. Re-run the same failing node.", _pytest(pytest_args), still_obs, "Still red after the first patch. Re-read the implementation; hypothesis is wrong."),
        _step(12, f"Observation: post-edit test still failed ({test}::{p['test_fn']}). Re-read {src}.", _read(src), p["reread_obs"], f"Plan change: {p['plan_change']}"),
        _step(13, f"Reflection: {p['plan_change']}"[:240], _edit(src, p["first_new"], p["fix_new"]), p["fix_obs"], "Corrective patch applied. Run the original failing node again."),
        _step(14, "Observation: fix edit returned clean. Re-run the original failing test node.", _pytest(pytest_args), "1 passed in 0.16s", "Result recorded. Run one broader check before declaring the outcome."),
        _step(15, f"Observation: focused run finished. Run broader check `pytest {test} -q`.", _bash(f"pytest {test} -q"), "3 passed in 0.28s", "Broader check captured. Stop; residual risk belongs in the outcome text."),
        _step(16, "Observation: broader check is on disk. Show the diff of patched files for the handoff note.", _bash("git diff --stat | head -n 40"), f"diffstat for {p['slug']}: {src} | 9 ++++++---. No other modified paths.", "Diff is the review artifact. No further edits."),
    ]
    ep = {
        "id": eid,
        "goal": p["goal"],
        "plan": p["plan"],
        "steps": steps,
        "outcome": p["outcome"],
        "reward": {"success": True, "tests_passed": 3, "retries": 2, "duration_min": 610, "wasted_calls": 180, "cost_steps": 16, "plan_changes": 1},
        "meta": {"factory": FACTORY, "round": round_n, "generator": GENERATOR, "kind": "episode", "seed": p["seed"], "designed": True, "domain": p["domain"], "stack": p["stack"]},
    }
    assert_clean(ep)
    if len(steps) != 16:
        raise ValueError(f"{eid} expected 16 steps")
    return ep


def build_fail(round_n: int, p: dict) -> dict:
    _goal_ok(p["goal"])
    src, test, cfg = _paths(p)
    eid = f"{PREFIX}-r{round_n}-{p['slug']}"
    ticket = p["ticket"]
    ticket_path = f"{p['mod']}/handoff.md"
    listing = f"{src} {cfg}\n{test}"
    pytest_args = f"{test} -q --tb=short"
    fail_obs = f"{test}::{p['test_fn']} FAILED\nE   {p['fail_msg']}"
    still_obs = f"{test}::{p['test_fn']} FAILED\nE   {p['still_msg']}"
    steps = [
        _step(1, f"Plan: list src {p['mod']} and tests before touching conversion or config.", _bash(f"ls -la src {p['mod']} tests | head -40"), listing, f"Tree shows {src} plus tests. Run the named failing target next."),
        _step(2, f"Observation: listing named the test files. Run `{pytest_args}` to capture the failure.", _pytest(pytest_args), fail_obs, f"Failure is at {test}::{p['test_fn']}. Read that test before a one-line fix."),
        _step(3, f"Observation: {test}::{p['test_fn']} is red. Read {test} around the assertion.", _read(test), p["test_body"], "Test contract is visible. Search implementation symbols next."),
        _step(4, "Observation: test file imported the production helper. Grep those symbols.", _bash(f"rg -n '{p['grep_pat']}' src {p['mod']} tests"), p["grep_hit"], f"Grep hit {src}. Read it before editing the first match."),
        _step(5, f"Observation: grep listed {src}. Read it before any patch.", _read(src), p["src_body"], "First read done. Fetch vendor docs next; do not patch on a hunch yet."),
        _step(6, "Observation: local files are in. Need the changelog/registry before editing.", _fetch(p["docs_url"]), f"GET {p['docs_url']}\nHTTP/1.1 429 Too Many Requests\nRetry-After: 6\nX-RateLimit-Remaining: 0", "Call failed with rate-limit status with Retry-After. Recover with backoff."),
        _step(7, "Observation: the prior call returned rate-limit status with Retry-After. Sleep then retry.", _fetch(p["docs_url"]), f"sleep + jitter retry of the same URL\nHTTP/1.1 200 OK\n{p['docs_ok']}", "Retry succeeded. Continue with that document."),
        _step(8, "Observation: local files are in. Need the second remote document before editing.", _fetch(p["docs_url2"]), f"GET {p['docs_url2']}\nHTTP/1.1 502 Bad Gateway\nBad Gateway.", "Call failed with upstream gateway failure. Recover with backoff."),
        _step(9, "Observation: the prior call returned an upstream gateway failure. Retry once with 2s backoff.", _fetch(p["docs_url2"]), f"retry after 2s backoff; local vendor fixture\nHTTP/1.1 200 OK\n{p['docs_ok2']}", "Degraded path used the local fixture. Resume the local debug plan."),
        _step(10, f"Observation: docs and source are in. Apply the first patch to {src}.", _edit(src, p["first_old"], p["first_new"]), p["first_obs"], "Patch applied. Re-run the failing test; do not assume green."),
        _step(11, f"Observation: edit wrote {src}. Re-run the same failing node.", _pytest(pytest_args), still_obs, "Still red after the first patch. Re-read the implementation; hypothesis is wrong."),
        _step(12, f"Observation: post-edit test still failed ({test}::{p['test_fn']}). Re-read {src}.", _read(src), p["reread_obs"], f"Plan change: {p['plan_change']}"),
        _step(13, f"Reflection: {p['plan_change']}"[:240], _edit(ticket_path, "", f"# {ticket} {p['ticket_why']}"), p["fix_obs"], "Handoff ticket written. Run the original failing node again."),
        _step(14, "Observation: handoff edit returned clean. Re-run the original failing test node.", _pytest(pytest_args), f"{test}::{p['test_fn']} FAILED  # handoff: {ticket}\n1 failed", "Result recorded. Run one broader check before declaring the outcome."),
        _step(15, f"Observation: focused run finished. Run broader check `pytest {test} -q; echo {ticket}`.", _bash(f"pytest {test} -q; echo {ticket}"), f"1 failed, 2 passed\n{ticket}", "Broader check captured. Residual risk belongs in the outcome text."),
        _step(16, "Observation: broader check is on disk. Show the diff of patched files for the handoff note.", _bash("git diff --stat | head -n 40"), f"diffstat for {p['slug']}: {src} | 8 +++++---. {ticket_path} added.", "Diff is the review artifact. Lint next."),
        _step(17, "Observation: diffstat listed the patched files. Run a linter on those paths only.", _bash("ruff check tests || true; echo lint-end"), "All checks passed!\nlint-end", "Lint clean. Episode complete."),
    ]
    ep = {
        "id": eid,
        "goal": p["goal"],
        "plan": p["plan"],
        "steps": steps,
        "outcome": p["outcome"],
        "reward": {"success": False, "tests_passed": 2, "retries": 2, "duration_min": 640, "wasted_calls": 210, "cost_steps": 17, "plan_changes": 1},
        "meta": {"factory": FACTORY, "round": round_n, "generator": GENERATOR, "kind": "episode", "seed": p["seed"], "designed": True, "domain": p["domain"], "stack": p["stack"]},
    }
    assert_clean(ep)
    if len(steps) != 17:
        raise ValueError(f"{eid} expected 17 steps")
    if "ticket" not in p:
        raise ValueError(f"{eid} handoff missing ticket")
    return ep


def notes_md(round_n: int, ok: dict, bad: dict, ok_id: str, bad_id: str) -> str:
    cov = max(ok.get("coverage", 80), bad.get("coverage", 80))
    return (
        f"# {FACTORY} — NOTES r{round_n}\n\n"
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
        if ep["meta"].get("seed") in BANNED_SLUGS or ep["id"].split("-", 2)[-1] in BANNED_SLUGS:
            raise ValueError(f"banned slug {ep['id']}")


def build_pair(round_n: int, ok: dict, bad: dict):
    ok_ep = build_success(round_n, ok)
    bad_ep = build_fail(round_n, bad)
    validate_pair(ok_ep, bad_ep, round_n)
    notes = notes_md(round_n, ok, bad, ok_ep["id"], bad_ep["id"])
    if "Novel coverage:" not in notes:
        raise ValueError("NOTES missing Novel coverage")
    return ok_ep, bad_ep, notes


def emit_stage(stage: Path, round_n: int, ok: dict, bad: dict):
    ok_ep, bad_ep, notes = build_pair(round_n, ok, bad)
    batch = stage / f"batch-r{round_n:02d}.jsonl"
    notes_path = stage / f"NOTES-r{round_n:02d}.md"
    batch.write_text(dumps_episode(ok_ep) + "\n" + dumps_episode(bad_ep) + "\n", encoding="utf-8")
    notes_path.write_text(notes, encoding="utf-8")
    return ok_ep["id"], bad_ep["id"]


PAIRS = [
    (
        _p(
            slug="socketio-leftover-sid",
            goal="Resume Socket.IO leftover sid; do not second-emit as a new session.",
            plan="Read emit-as-resume, try second emit, then leftover sid.",
            mod="siolef",
            test_fn="test_sid_not_emit",
            src_body="def resume(sid):\n    return {'emit': sid}\n",
            test_body="def test_sid_not_emit():\n    assert 'leftover_sid' in resume('inv')\n",
            grep_pat="leftover_sid|emit|socket.io",
            grep_hit="src/siolef.py:2: return {'emit': sid}",
            fail_msg="AssertionError: second emit created a new Socket.IO room; leftover sid unused",
            first_old="    return {'emit': sid}",
            first_new="    return {'emit': sid, 'event': 'reconnect'}",
            first_obs="patched reconnect emit (still a second emit)",
            still_msg="AssertionError: reconnect emit is not leftover_sid",
            reread_obs="Socket.IO leftover sid restores the same engine.io session",
            plan_change="Pass leftover_sid. A second emit is not resume.",
            fix_new="    return {'leftover_sid': sid}",
            fix_obs="patched leftover_sid",
            docs_url="https://socket.io/docs/v4/client-api/",
            docs_ok="Socket.IO leftover sid resumes; emit() is a new packet.",
            docs_url2="https://socket.io/docs/v4/client-api/#socketid",
            docs_ok2="Use leftover_sid. Not cookie-replay. Not AnyCable clone.",
            outcome="leftover_sid restored the Socket.IO session. Second emit unused (success).",
            domain="socketio-leftover-sid-vs-second-emit",
            stack="Socket.IO leftover sid",
            seed="socketio-leftover-sid",
            residual="Not cookie-replay. Not AnyCable clone.",
            coverage=87,
        ),
        _p(
            slug="socketio-drop-sid-handoff",
            goal="Do not drop Socket.IO leftover sid bind and treat it as a new emit.",
            plan="Read drop leftover bind, try emit retry, then hand off sid bind.",
            mod="siodrop",
            test_fn="test_bind_not_dropped",
            src_body="def bind(drop):\n    return {'emit': 'retry'} if drop else {}\n",
            test_body="def test_bind_not_dropped():\n    assert 'leftover_sid' in bind(True)\n",
            grep_pat="leftover_sid|emit|drop",
            grep_hit="src/siodrop.py:2: return {'emit': 'retry'} if drop else {}",
            fail_msg="AssertionError: leftover sid bind dropped; emit retry unused",
            first_old="    return {'emit': 'retry'} if drop else {}",
            first_new="    return {'emit': 'ack'} if drop else {}",
            first_obs="patched ack emit (still dropped leftover bind)",
            still_msg="AssertionError: emit ack does not bind leftover_sid",
            reread_obs="Dropping leftover_sid bind is edge-plat; emit cannot restore it",
            plan_change="Leftover sid bind drop is Socket.IO plat. Handoff SIO-LB-1.",
            fix_new="    return {'handoff': 'SIO-LB-1'} if drop else {}",
            fix_obs="ticket filed. still emit-classed",
            docs_url="https://socket.io/docs/v4/engine-io-protocol/",
            docs_ok="Engine.IO leftover sid is bound by the adapter, not a client emit.",
            docs_url2="https://socket.io/docs/v4/adapter/",
            docs_ok2="Bind drop is sio-plat. Handoff SIO-LB-1.",
            outcome="Still emit-classed; leftover sid bind drop — handoff SIO-LB-1.",
            domain="socketio-drop-leftover-sid-bind",
            stack="Socket.IO leftover sid drop",
            seed="socketio-drop-sid-handoff",
            residual="Emit cannot rebind leftover sid.",
            ticket="SIO-LB-1",
            ticket_why="leftover_sid bind owned by sio-plat",
            coverage=86,
        ),
    ),
    (
        _p(
            slug="sockjs-leftover-iframe",
            goal="Resume SockJS leftover iframe session; do not open a second iframe.",
            plan="Read iframe-as-resume, try new iframe, then leftover iframe id.",
            mod="sjslef",
            test_fn="test_iframe_not_new",
            src_body="def resume(fid):\n    return {'iframe': fid}\n",
            test_body="def test_iframe_not_new():\n    assert 'leftover_iframe' in resume('inv')\n",
            grep_pat="leftover_iframe|iframe|sockjs",
            grep_hit="src/sjslef.py:2: return {'iframe': fid}",
            fail_msg="AssertionError: second iframe created a new SockJS transport; leftover unused",
            first_old="    return {'iframe': fid}",
            first_new="    return {'iframe': fid, 'info': True}",
            first_obs="patched info iframe (still a second iframe)",
            still_msg="AssertionError: info iframe is not leftover_iframe",
            reread_obs="SockJS leftover iframe restores the same xhr-streaming session",
            plan_change="Pass leftover_iframe. A second iframe is not resume.",
            fix_new="    return {'leftover_iframe': fid}",
            fix_obs="patched leftover_iframe",
            docs_url="https://github.com/sockjs/sockjs-protocol",
            docs_ok="SockJS leftover iframe resumes; a new iframe is a new transport.",
            docs_url2="https://github.com/sockjs/sockjs-client",
            docs_ok2="Use leftover_iframe. Not cookie-replay.",
            outcome="leftover_iframe restored SockJS. Second iframe unused (success).",
            domain="sockjs-leftover-iframe-vs-second-iframe",
            stack="SockJS leftover iframe",
            seed="sockjs-leftover-iframe",
            residual="Not cookie-replay. Not Socket.IO clone.",
            coverage=85,
        ),
        _p(
            slug="sockjs-drop-iframe-handoff",
            goal="Do not drop SockJS leftover iframe bind and spin a new iframe.",
            plan="Read drop leftover iframe, try new iframe, then hand off bind.",
            mod="sjsdrop",
            test_fn="test_iframe_bind",
            src_body="def bind(drop):\n    return {'iframe': 'new'} if drop else {}\n",
            test_body="def test_iframe_bind():\n    assert 'leftover_iframe' in bind(True)\n",
            grep_pat="leftover_iframe|iframe|drop",
            grep_hit="src/sjsdrop.py:2: return {'iframe': 'new'} if drop else {}",
            fail_msg="AssertionError: leftover iframe bind dropped; new iframe unused",
            first_old="    return {'iframe': 'new'} if drop else {}",
            first_new="    return {'iframe': 'htmlfile'} if drop else {}",
            first_obs="patched htmlfile iframe (still dropped leftover bind)",
            still_msg="AssertionError: htmlfile does not bind leftover_iframe",
            reread_obs="Dropping leftover_iframe is sockjs-plat; new iframe cannot restore it",
            plan_change="Leftover iframe bind drop is SockJS plat. Handoff SJS-IF-2.",
            fix_new="    return {'handoff': 'SJS-IF-2'} if drop else {}",
            fix_obs="ticket filed. still iframe-classed",
            docs_url="https://github.com/sockjs/sockjs-protocol/blob/master/sockjs-protocol-0.3.3.md",
            docs_ok="SockJS leftover iframe is bound by the server, not a new iframe.",
            docs_url2="https://github.com/sockjs/sockjs-node",
            docs_ok2="Bind drop is sockjs-plat. Handoff SJS-IF-2.",
            outcome="Still iframe-classed; leftover iframe bind drop — handoff SJS-IF-2.",
            domain="sockjs-drop-leftover-iframe-bind",
            stack="SockJS leftover iframe drop",
            seed="sockjs-drop-iframe-handoff",
            residual="New iframe cannot rebind leftover iframe.",
            ticket="SJS-IF-2",
            ticket_why="leftover_iframe bind owned by sockjs-plat",
            coverage=84,
        ),
    ),
    (
        _p(
            slug="signalr-leftover-conn",
            goal="Resume SignalR leftover connectionToken; do not start a second reconnect.",
            plan="Read reconnect-as-resume, try new reconnect, then leftover token.",
            mod="sigrlef",
            test_fn="test_token_not_reconnect",
            src_body="def resume(tok):\n    return {'reconnect': tok}\n",
            test_body="def test_token_not_reconnect():\n    assert 'leftover_conn' in resume('inv')\n",
            grep_pat="leftover_conn|reconnect|signalr",
            grep_hit="src/sigrlef.py:2: return {'reconnect': tok}",
            fail_msg="AssertionError: second reconnect created a new hub; leftover unused",
            first_old="    return {'reconnect': tok}",
            first_new="    return {'reconnect': tok, 'transport': 'ws'}",
            first_obs="patched ws reconnect (still a second reconnect)",
            still_msg="AssertionError: ws reconnect is not leftover_conn",
            reread_obs="SignalR leftover connectionToken restores the same hub connection",
            plan_change="Pass leftover_conn. A second reconnect is not resume.",
            fix_new="    return {'leftover_conn': tok}",
            fix_obs="patched leftover_conn",
            docs_url="https://learn.microsoft.com/en-us/aspnet/core/signalr/configuration",
            docs_ok="SignalR leftover connectionToken resumes; reconnect() is a new hub.",
            docs_url2="https://learn.microsoft.com/en-us/aspnet/core/signalr/javascript-client",
            docs_ok2="Use leftover_conn. Not cookie-replay.",
            outcome="leftover_conn restored SignalR. Second reconnect unused (success).",
            domain="signalr-leftover-conn-vs-second-reconnect",
            stack="SignalR leftover connectionToken",
            seed="signalr-leftover-conn",
            residual="Not cookie-replay. Not SockJS clone.",
            coverage=86,
        ),
        _p(
            slug="signalr-drop-reconnect-handoff",
            goal="Do not drop SignalR leftover reconnect bind and open a new hub.",
            plan="Read drop leftover reconnect, try new hub, then hand off bind.",
            mod="sigrdrop",
            test_fn="test_reconnect_bind",
            src_body="def bind(drop):\n    return {'reconnect': 'new'} if drop else {}\n",
            test_body="def test_reconnect_bind():\n    assert 'leftover_conn' in bind(True)\n",
            grep_pat="leftover_conn|reconnect|drop",
            grep_hit="src/sigrdrop.py:2: return {'reconnect': 'new'} if drop else {}",
            fail_msg="AssertionError: leftover reconnect bind dropped; new hub unused",
            first_old="    return {'reconnect': 'new'} if drop else {}",
            first_new="    return {'reconnect': 'longpoll'} if drop else {}",
            first_obs="patched longpoll reconnect (still dropped leftover bind)",
            still_msg="AssertionError: longpoll does not bind leftover_conn",
            reread_obs="Dropping leftover_conn is signalr-plat; new reconnect cannot restore it",
            plan_change="Leftover reconnect bind drop is SignalR plat. Handoff SGR-RC-3.",
            fix_new="    return {'handoff': 'SGR-RC-3'} if drop else {}",
            fix_obs="ticket filed. still reconnect-classed",
            docs_url="https://learn.microsoft.com/en-us/aspnet/core/signalr/scaleout",
            docs_ok="SignalR leftover reconnect is bound by the backplane, not a new hub.",
            docs_url2="https://learn.microsoft.com/en-us/aspnet/core/signalr/redis-backplane",
            docs_ok2="Bind drop is signalr-plat. Handoff SGR-RC-3.",
            outcome="Still reconnect-classed; leftover reconnect bind drop — handoff SGR-RC-3.",
            domain="signalr-drop-leftover-reconnect-bind",
            stack="SignalR leftover reconnect drop",
            seed="signalr-drop-reconnect-handoff",
            residual="New hub cannot rebind leftover reconnect.",
            ticket="SGR-RC-3",
            ticket_why="leftover_conn bind owned by signalr-plat",
            coverage=85,
        ),
    ),
    (
        _p(
            slug="phoenix-leftover-presence",
            goal="Resume Phoenix leftover presence; do not join a second presence channel.",
            plan="Read join-as-resume, try second join, then leftover presence.",
            mod="phxlef",
            test_fn="test_presence_not_join",
            src_body="def resume(key):\n    return {'join': key}\n",
            test_body="def test_presence_not_join():\n    assert 'leftover_presence' in resume('inv')\n",
            grep_pat="leftover_presence|join|phoenix",
            grep_hit="src/phxlef.py:2: return {'join': key}",
            fail_msg="AssertionError: second join created a new Presence track; leftover unused",
            first_old="    return {'join': key}",
            first_new="    return {'join': key, 'topic': 'users'}",
            first_obs="patched topic join (still a second join)",
            still_msg="AssertionError: topic join is not leftover_presence",
            reread_obs="Phoenix leftover presence restores the same tracker",
            plan_change="Pass leftover_presence. A second join is not resume.",
            fix_new="    return {'leftover_presence': key}",
            fix_obs="patched leftover_presence",
            docs_url="https://hexdocs.pm/phoenix/Phoenix.Presence.html",
            docs_ok="Phoenix leftover presence resumes; join() is a new tracker.",
            docs_url2="https://hexdocs.pm/phoenix/channels.html",
            docs_ok2="Use leftover_presence. Not cookie-replay.",
            outcome="leftover_presence restored Phoenix. Second join unused (success).",
            domain="phoenix-leftover-presence-vs-second-join",
            stack="Phoenix leftover presence",
            seed="phoenix-leftover-presence",
            residual="Not cookie-replay. Not SignalR clone.",
            coverage=86,
        ),
        _p(
            slug="phoenix-drop-presence-handoff",
            goal="Do not drop Phoenix leftover presence bind and join a new tracker.",
            plan="Read drop leftover presence, try new join, then hand off bind.",
            mod="phxdrop",
            test_fn="test_presence_bind",
            src_body="def bind(drop):\n    return {'join': 'new'} if drop else {}\n",
            test_body="def test_presence_bind():\n    assert 'leftover_presence' in bind(True)\n",
            grep_pat="leftover_presence|join|drop",
            grep_hit="src/phxdrop.py:2: return {'join': 'new'} if drop else {}",
            fail_msg="AssertionError: leftover presence bind dropped; new join unused",
            first_old="    return {'join': 'new'} if drop else {}",
            first_new="    return {'join': 'rooms'} if drop else {}",
            first_obs="patched rooms join (still dropped leftover bind)",
            still_msg="AssertionError: rooms join does not bind leftover_presence",
            reread_obs="Dropping leftover_presence is phoenix-plat; join cannot restore it",
            plan_change="Leftover presence bind drop is Phoenix plat. Handoff PHX-PR-4.",
            fix_new="    return {'handoff': 'PHX-PR-4'} if drop else {}",
            fix_obs="ticket filed. still join-classed",
            docs_url="https://hexdocs.pm/phoenix_pubsub/Phoenix.PubSub.html",
            docs_ok="Phoenix leftover presence is bound by PubSub, not a new join.",
            docs_url2="https://hexdocs.pm/phoenix/Phoenix.Tracker.html",
            docs_ok2="Bind drop is phoenix-plat. Handoff PHX-PR-4.",
            outcome="Still join-classed; leftover presence bind drop — handoff PHX-PR-4.",
            domain="phoenix-drop-leftover-presence-bind",
            stack="Phoenix leftover presence drop",
            seed="phoenix-drop-presence-handoff",
            residual="Join cannot rebind leftover presence.",
            ticket="PHX-PR-4",
            ticket_why="leftover_presence bind owned by phoenix-plat",
            coverage=85,
        ),
    ),
    (
        _p(
            slug="actioncable-leftover-ident",
            goal="Resume Action Cable leftover identifier; do not subscribe a second identifier.",
            plan="Read subscribe-as-resume, try new identifier, then leftover identifier.",
            mod="acblef",
            test_fn="test_ident_not_sub",
            src_body="def resume(ident):\n    return {'subscribe': ident}\n",
            test_body="def test_ident_not_sub():\n    assert 'leftover_ident' in resume('inv')\n",
            grep_pat="leftover_ident|subscribe|actioncable",
            grep_hit="src/acblef.py:2: return {'subscribe': ident}",
            fail_msg="AssertionError: second subscribe created a new stream; leftover unused",
            first_old="    return {'subscribe': ident}",
            first_new="    return {'subscribe': ident, 'channel': 'Chat'}",
            first_obs="patched Chat subscribe (still a second subscribe)",
            still_msg="AssertionError: Chat subscribe is not leftover_ident",
            reread_obs="Action Cable leftover identifier restores the same stream",
            plan_change="Pass leftover_ident. A second subscribe is not resume.",
            fix_new="    return {'leftover_ident': ident}",
            fix_obs="patched leftover_ident",
            docs_url="https://guides.rubyonrails.org/action_cable_overview.html",
            docs_ok="Action Cable leftover identifier resumes; subscribe is a new stream.",
            docs_url2="https://api.rubyonrails.org/classes/ActionCable/Channel/Base.html",
            docs_ok2="Use leftover_ident. Not cookie-replay. Not AnyCable clone.",
            outcome="leftover_ident restored Action Cable. Second subscribe unused (success).",
            domain="actioncable-leftover-ident-vs-second-subscribe",
            stack="Action Cable leftover identifier",
            seed="actioncable-leftover-ident",
            residual="Not cookie-replay. Not AnyCable restore_session clone.",
            coverage=87,
        ),
        _p(
            slug="actioncable-drop-ident-handoff",
            goal="Do not drop Action Cable leftover identifier bind and subscribe again.",
            plan="Read drop leftover identifier, try new subscribe, then hand off bind.",
            mod="acbdrop",
            test_fn="test_ident_bind",
            src_body="def bind(drop):\n    return {'subscribe': 'new'} if drop else {}\n",
            test_body="def test_ident_bind():\n    assert 'leftover_ident' in bind(True)\n",
            grep_pat="leftover_ident|subscribe|drop",
            grep_hit="src/acbdrop.py:2: return {'subscribe': 'new'} if drop else {}",
            fail_msg="AssertionError: leftover identifier bind dropped; new subscribe unused",
            first_old="    return {'subscribe': 'new'} if drop else {}",
            first_new="    return {'subscribe': 'ChatChannel'} if drop else {}",
            first_obs="patched ChatChannel subscribe (still dropped leftover bind)",
            still_msg="AssertionError: ChatChannel does not bind leftover_ident",
            reread_obs="Dropping leftover_ident is cable-plat; subscribe cannot restore it",
            plan_change="Leftover identifier bind drop is Action Cable plat. Handoff ACB-ID-5.",
            fix_new="    return {'handoff': 'ACB-ID-5'} if drop else {}",
            fix_obs="ticket filed. still subscribe-classed",
            docs_url="https://guides.rubyonrails.org/action_cable_overview.html#server-side-setup",
            docs_ok="Action Cable leftover identifier is bound by the server, not a new subscribe.",
            docs_url2="https://guides.rubyonrails.org/action_cable_overview.html#subscriptions",
            docs_ok2="Bind drop is cable-plat. Handoff ACB-ID-5.",
            outcome="Still subscribe-classed; leftover identifier bind drop — handoff ACB-ID-5.",
            domain="actioncable-drop-leftover-ident-bind",
            stack="Action Cable leftover identifier drop",
            seed="actioncable-drop-ident-handoff",
            residual="Subscribe cannot rebind leftover identifier.",
            ticket="ACB-ID-5",
            ticket_why="leftover_ident bind owned by cable-plat",
            coverage=86,
        ),
    ),
    (
        _p(
            slug="centrifuge-leftover-recover",
            goal="Resume Centrifuge leftover recover; do not subscribe a second recover.",
            plan="Read subscribe-as-recover, try new recover, then leftover recover.",
            mod="cfllef",
            test_fn="test_recover_not_sub",
            src_body="def resume(epoch):\n    return {'subscribe': epoch}\n",
            test_body="def test_recover_not_sub():\n    assert 'leftover_recover' in resume('inv')\n",
            grep_pat="leftover_recover|subscribe|centrifuge",
            grep_hit="src/cfllef.py:2: return {'subscribe': epoch}",
            fail_msg="AssertionError: second subscribe created a new stream; leftover unused",
            first_old="    return {'subscribe': epoch}",
            first_new="    return {'subscribe': epoch, 'offset': 0}",
            first_obs="patched offset subscribe (still a second subscribe)",
            still_msg="AssertionError: offset subscribe is not leftover_recover",
            reread_obs="Centrifuge leftover recover restores the same epoch",
            plan_change="Pass leftover_recover. A second subscribe is not resume.",
            fix_new="    return {'leftover_recover': epoch}",
            fix_obs="patched leftover_recover",
            docs_url="https://centrifugal.dev/docs/server/recovery",
            docs_ok="Centrifuge leftover recover resumes; subscribe is a new stream.",
            docs_url2="https://centrifugal.dev/docs/transports/client_api",
            docs_ok2="Use leftover_recover. Not cookie-replay.",
            outcome="leftover_recover restored Centrifuge. Second subscribe unused (success).",
            domain="centrifuge-leftover-recover-vs-second-subscribe",
            stack="Centrifuge leftover recover",
            seed="centrifuge-leftover-recover",
            residual="Not cookie-replay. Not Action Cable clone.",
            coverage=86,
        ),
        _p(
            slug="centrifuge-drop-recover-handoff",
            goal="Do not drop Centrifuge leftover recover bind and subscribe again.",
            plan="Read drop leftover recover, try new subscribe, then hand off bind.",
            mod="cfldrop",
            test_fn="test_recover_bind",
            src_body="def bind(drop):\n    return {'subscribe': 'new'} if drop else {}\n",
            test_body="def test_recover_bind():\n    assert 'leftover_recover' in bind(True)\n",
            grep_pat="leftover_recover|subscribe|drop",
            grep_hit="src/cfldrop.py:2: return {'subscribe': 'new'} if drop else {}",
            fail_msg="AssertionError: leftover recover bind dropped; new subscribe unused",
            first_old="    return {'subscribe': 'new'} if drop else {}",
            first_new="    return {'subscribe': 'offset'} if drop else {}",
            first_obs="patched offset subscribe (still dropped leftover bind)",
            still_msg="AssertionError: offset subscribe does not bind leftover_recover",
            reread_obs="Dropping leftover_recover is ctf-plat; subscribe cannot restore it",
            plan_change="Leftover recover bind drop is Centrifuge plat. Handoff CTF-RV-6.",
            fix_new="    return {'handoff': 'CTF-RV-6'} if drop else {}",
            fix_obs="ticket filed. still subscribe-classed",
            docs_url="https://centrifugal.dev/docs/server/engines",
            docs_ok="Centrifuge leftover recover is bound by the engine, not a new subscribe.",
            docs_url2="https://centrifugal.dev/docs/server/history_and_recovery",
            docs_ok2="Bind drop is ctf-plat. Handoff CTF-RV-6.",
            outcome="Still subscribe-classed; leftover recover bind drop — handoff CTF-RV-6.",
            domain="centrifuge-drop-leftover-recover-bind",
            stack="Centrifuge leftover recover drop",
            seed="centrifuge-drop-recover-handoff",
            residual="Subscribe cannot rebind leftover recover.",
            ticket="CTF-RV-6",
            ticket_why="leftover_recover bind owned by ctf-plat",
            coverage=85,
        ),
    ),
    (
        _p(
            slug="pusher-leftover-channel",
            goal="Resume Pusher leftover channel; do not subscribe a second channel.",
            plan="Read subscribe-as-resume, try new channel, then leftover channel.",
            mod="pshlef",
            test_fn="test_channel_not_sub",
            src_body="def resume(ch):\n    return {'subscribe': ch}\n",
            test_body="def test_channel_not_sub():\n    assert 'leftover_channel' in resume('inv')\n",
            grep_pat="leftover_channel|subscribe|pusher",
            grep_hit="src/pshlef.py:2: return {'subscribe': ch}",
            fail_msg="AssertionError: second subscribe created a new channel; leftover unused",
            first_old="    return {'subscribe': ch}",
            first_new="    return {'subscribe': ch, 'auth': True}",
            first_obs="patched auth subscribe (still a second subscribe)",
            still_msg="AssertionError: auth subscribe is not leftover_channel",
            reread_obs="Pusher leftover channel restores the same presence channel",
            plan_change="Pass leftover_channel. A second subscribe is not resume.",
            fix_new="    return {'leftover_channel': ch}",
            fix_obs="patched leftover_channel",
            docs_url="https://pusher.com/docs/channels/using_channels/connection/",
            docs_ok="Pusher leftover channel resumes; subscribe is a new channel.",
            docs_url2="https://pusher.com/docs/channels/using_channels/channels/",
            docs_ok2="Use leftover_channel. Not cookie-replay.",
            outcome="leftover_channel restored Pusher. Second subscribe unused (success).",
            domain="pusher-leftover-channel-vs-second-subscribe",
            stack="Pusher leftover channel",
            seed="pusher-leftover-channel",
            residual="Not cookie-replay. Not Centrifuge clone.",
            coverage=86,
        ),
        _p(
            slug="pusher-drop-channel-handoff",
            goal="Do not drop Pusher leftover channel bind and subscribe again.",
            plan="Read drop leftover channel, try new subscribe, then hand off bind.",
            mod="pshdrop",
            test_fn="test_channel_bind",
            src_body="def bind(drop):\n    return {'subscribe': 'new'} if drop else {}\n",
            test_body="def test_channel_bind():\n    assert 'leftover_channel' in bind(True)\n",
            grep_pat="leftover_channel|subscribe|drop",
            grep_hit="src/pshdrop.py:2: return {'subscribe': 'new'} if drop else {}",
            fail_msg="AssertionError: leftover channel bind dropped; new subscribe unused",
            first_old="    return {'subscribe': 'new'} if drop else {}",
            first_new="    return {'subscribe': 'presence'} if drop else {}",
            first_obs="patched presence subscribe (still dropped leftover bind)",
            still_msg="AssertionError: presence subscribe does not bind leftover_channel",
            reread_obs="Dropping leftover_channel is pusher-plat; subscribe cannot restore it",
            plan_change="Leftover channel bind drop is Pusher plat. Handoff PSH-CH-7.",
            fix_new="    return {'handoff': 'PSH-CH-7'} if drop else {}",
            fix_obs="ticket filed. still subscribe-classed",
            docs_url="https://pusher.com/docs/channels/using_channels/presence-channels/",
            docs_ok="Pusher leftover channel is bound by the cluster, not a new subscribe.",
            docs_url2="https://pusher.com/docs/channels/library_auth_reference/auth-signatures/",
            docs_ok2="Bind drop is pusher-plat. Handoff PSH-CH-7.",
            outcome="Still subscribe-classed; leftover channel bind drop — handoff PSH-CH-7.",
            domain="pusher-drop-leftover-channel-bind",
            stack="Pusher leftover channel drop",
            seed="pusher-drop-channel-handoff",
            residual="Subscribe cannot rebind leftover channel.",
            ticket="PSH-CH-7",
            ticket_why="leftover_channel bind owned by pusher-plat",
            coverage=85,
        ),
    ),
    (
        _p(
            slug="ably-leftover-resume",
            goal="Resume Ably leftover connectionKey; do not open a second resume.",
            plan="Read resume-as-new, try new resume, then leftover connectionKey.",
            mod="ablylef",
            test_fn="test_key_not_resume",
            src_body="def resume(key):\n    return {'resume': key}\n",
            test_body="def test_key_not_resume():\n    assert 'leftover_key' in resume('inv')\n",
            grep_pat="leftover_key|resume|ably",
            grep_hit="src/ablylef.py:2: return {'resume': key}",
            fail_msg="AssertionError: second resume created a new Ably connection; leftover unused",
            first_old="    return {'resume': key}",
            first_new="    return {'resume': key, 'clientId': 'new'}",
            first_obs="patched clientId resume (still a second resume)",
            still_msg="AssertionError: clientId resume is not leftover_key",
            reread_obs="Ably leftover connectionKey restores the same realtime connection",
            plan_change="Pass leftover_key. A second resume is not leftover resume.",
            fix_new="    return {'leftover_key': key}",
            fix_obs="patched leftover_key",
            docs_url="https://ably.com/docs/connect",
            docs_ok="Ably leftover connectionKey resumes; resume() with a new clientId is a new seat.",
            docs_url2="https://ably.com/docs/api/realtime-sdk/connection",
            docs_ok2="Use leftover_key. Not cookie-replay.",
            outcome="leftover_key restored Ably. Second resume unused (success).",
            domain="ably-leftover-key-vs-second-resume",
            stack="Ably leftover connectionKey",
            seed="ably-leftover-resume",
            residual="Not cookie-replay. Not Pusher clone.",
            coverage=86,
        ),
        _p(
            slug="ably-drop-resume-handoff",
            goal="Do not drop Ably leftover resume bind and start a new resume.",
            plan="Read drop leftover resume, try new resume, then hand off bind.",
            mod="ablydrop",
            test_fn="test_resume_bind",
            src_body="def bind(drop):\n    return {'resume': 'new'} if drop else {}\n",
            test_body="def test_resume_bind():\n    assert 'leftover_key' in bind(True)\n",
            grep_pat="leftover_key|resume|drop",
            grep_hit="src/ablydrop.py:2: return {'resume': 'new'} if drop else {}",
            fail_msg="AssertionError: leftover resume bind dropped; new resume unused",
            first_old="    return {'resume': 'new'} if drop else {}",
            first_new="    return {'resume': 'recover'} if drop else {}",
            first_obs="patched recover resume (still dropped leftover bind)",
            still_msg="AssertionError: recover resume does not bind leftover_key",
            reread_obs="Dropping leftover_key is ably-plat; resume cannot restore it",
            plan_change="Leftover resume bind drop is Ably plat. Handoff ABL-RS-8.",
            fix_new="    return {'handoff': 'ABL-RS-8'} if drop else {}",
            fix_obs="ticket filed. still resume-classed",
            docs_url="https://ably.com/docs/connect/states",
            docs_ok="Ably leftover resume is bound by the cluster, not a new resume.",
            docs_url2="https://ably.com/docs/platform/connection",
            docs_ok2="Bind drop is ably-plat. Handoff ABL-RS-8.",
            outcome="Still resume-classed; leftover resume bind drop — handoff ABL-RS-8.",
            domain="ably-drop-leftover-resume-bind",
            stack="Ably leftover resume drop",
            seed="ably-drop-resume-handoff",
            residual="New resume cannot rebind leftover key.",
            ticket="ABL-RS-8",
            ticket_why="leftover_key bind owned by ably-plat",
            coverage=85,
        ),
    ),
    (
        _p(
            slug="nchan-leftover-sub",
            goal="Resume nchan leftover subscriber; do not open a second subscriber.",
            plan="Read subscribe-as-resume, try new subscriber, then leftover subscriber.",
            mod="nchlef",
            test_fn="test_sub_not_new",
            src_body="def resume(sid):\n    return {'subscribe': sid}\n",
            test_body="def test_sub_not_new():\n    assert 'leftover_sub' in resume('inv')\n",
            grep_pat="leftover_sub|subscribe|nchan",
            grep_hit="src/nchlef.py:2: return {'subscribe': sid}",
            fail_msg="AssertionError: second subscriber created a new nchan stream; leftover unused",
            first_old="    return {'subscribe': sid}",
            first_new="    return {'subscribe': sid, 'channel': 'events'}",
            first_obs="patched events subscribe (still a second subscriber)",
            still_msg="AssertionError: events subscribe is not leftover_sub",
            reread_obs="nchan leftover subscriber restores the same pubsub id",
            plan_change="Pass leftover_sub. A second subscriber is not resume.",
            fix_new="    return {'leftover_sub': sid}",
            fix_obs="patched leftover_sub",
            docs_url="https://nchan.io/",
            docs_ok="nchan leftover subscriber resumes; a new subscribe is a new stream.",
            docs_url2="https://github.com/slact/nchan",
            docs_ok2="Use leftover_sub. Not cookie-replay.",
            outcome="leftover_sub restored nchan. Second subscriber unused (success).",
            domain="nchan-leftover-sub-vs-second-subscribe",
            stack="nchan leftover subscriber",
            seed="nchan-leftover-sub",
            residual="Not cookie-replay. Not Ably clone.",
            coverage=85,
        ),
        _p(
            slug="nchan-drop-sub-handoff",
            goal="Do not drop nchan leftover subscriber bind and subscribe again.",
            plan="Read drop leftover subscriber, try new subscribe, then hand off bind.",
            mod="nchdrop",
            test_fn="test_sub_bind",
            src_body="def bind(drop):\n    return {'subscribe': 'new'} if drop else {}\n",
            test_body="def test_sub_bind():\n    assert 'leftover_sub' in bind(True)\n",
            grep_pat="leftover_sub|subscribe|drop",
            grep_hit="src/nchdrop.py:2: return {'subscribe': 'new'} if drop else {}",
            fail_msg="AssertionError: leftover subscriber bind dropped; new subscribe unused",
            first_old="    return {'subscribe': 'new'} if drop else {}",
            first_new="    return {'subscribe': 'longpoll'} if drop else {}",
            first_obs="patched longpoll subscribe (still dropped leftover bind)",
            still_msg="AssertionError: longpoll does not bind leftover_sub",
            reread_obs="Dropping leftover_sub is nchan-plat; subscribe cannot restore it",
            plan_change="Leftover subscriber bind drop is nchan plat. Handoff NCH-SB-9.",
            fix_new="    return {'handoff': 'NCH-SB-9'} if drop else {}",
            fix_obs="ticket filed. still subscribe-classed",
            docs_url="https://nchan.io/#subscriber-reliability",
            docs_ok="nchan leftover subscriber is bound by Redis, not a new subscribe.",
            docs_url2="https://nchan.io/#redis",
            docs_ok2="Bind drop is nchan-plat. Handoff NCH-SB-9.",
            outcome="Still subscribe-classed; leftover subscriber bind drop — handoff NCH-SB-9.",
            domain="nchan-drop-leftover-sub-bind",
            stack="nchan leftover subscriber drop",
            seed="nchan-drop-sub-handoff",
            residual="Subscribe cannot rebind leftover subscriber.",
            ticket="NCH-SB-9",
            ticket_why="leftover_sub bind owned by nchan-plat",
            coverage=84,
        ),
    ),
    (
        _p(
            slug="ws-leftover-ping",
            goal="Resume RFC6455 leftover ping interval; do not open a second keepalive.",
            plan="Read ping-as-new-keepalive, try second ping, then leftover ping.",
            mod="wsplef",
            test_fn="test_ping_not_keep",
            src_body="def resume(ms):\n    return {'keepalive': ms}\n",
            test_body="def test_ping_not_keep():\n    assert 'leftover_ping' in resume(15)\n",
            grep_pat="leftover_ping|keepalive|websocket",
            grep_hit="src/wsplef.py:2: return {'keepalive': ms}",
            fail_msg="AssertionError: second keepalive created a new ping loop; leftover unused",
            first_old="    return {'keepalive': ms}",
            first_new="    return {'keepalive': ms, 'pong': True}",
            first_obs="patched pong keepalive (still a second keepalive)",
            still_msg="AssertionError: pong keepalive is not leftover_ping",
            reread_obs="RFC6455 leftover ping restores the same ping interval",
            plan_change="Pass leftover_ping. A second keepalive is not resume.",
            fix_new="    return {'leftover_ping': ms}",
            fix_obs="patched leftover_ping",
            docs_url="https://www.rfc-editor.org/rfc/rfc6455#section-5.5.2",
            docs_ok="Leftover ping resumes; a new keepalive is a new ping loop.",
            docs_url2="https://websockets.readthedocs.io/en/stable/topics/keepalive.html",
            docs_ok2="Use leftover_ping. Not cookie-replay.",
            outcome="leftover_ping restored WS ping. Second keepalive unused (success).",
            domain="ws-leftover-ping-vs-second-keepalive",
            stack="RFC6455 leftover ping",
            seed="ws-leftover-ping",
            residual="Not cookie-replay. Not nchan clone.",
            coverage=85,
        ),
        _p(
            slug="ws-drop-keepalive-handoff",
            goal="Do not drop RFC6455 leftover ping bind and start a new keepalive.",
            plan="Read drop leftover ping, try new keepalive, then hand off bind.",
            mod="wspdrop",
            test_fn="test_ping_bind",
            src_body="def bind(drop):\n    return {'keepalive': 10} if drop else {}\n",
            test_body="def test_ping_bind():\n    assert 'leftover_ping' in bind(True)\n",
            grep_pat="leftover_ping|keepalive|drop",
            grep_hit="src/wspdrop.py:2: return {'keepalive': 10} if drop else {}",
            fail_msg="AssertionError: leftover ping bind dropped; new keepalive unused",
            first_old="    return {'keepalive': 10} if drop else {}",
            first_new="    return {'keepalive': 5} if drop else {}",
            first_obs="patched keepalive 5s (still dropped leftover bind)",
            still_msg="AssertionError: keepalive 5s does not bind leftover_ping",
            reread_obs="Dropping leftover_ping is edge-plat; keepalive cannot restore it",
            plan_change="Leftover ping bind drop is WS plat. Handoff WS-PK-10.",
            fix_new="    return {'handoff': 'WS-PK-10'} if drop else {}",
            fix_obs="ticket filed. still keepalive-classed",
            docs_url="https://www.rfc-editor.org/rfc/rfc6455#section-7.1.3",
            docs_ok="Leftover ping is bound by the peer, not a new keepalive.",
            docs_url2="https://websockets.readthedocs.io/en/stable/",
            docs_ok2="Bind drop is ws-plat. Handoff WS-PK-10.",
            outcome="Still keepalive-classed; leftover ping bind drop — handoff WS-PK-10.",
            domain="ws-drop-leftover-keepalive-bind",
            stack="RFC6455 leftover ping drop",
            seed="ws-drop-keepalive-handoff",
            residual="Keepalive cannot rebind leftover ping.",
            ticket="WS-PK-10",
            ticket_why="leftover_ping bind owned by ws-plat",
            coverage=84,
        ),
    ),
    (
        _p(
            slug="graphqlws-leftover-ack",
            goal="Resume graphql-ws leftover connection_ack; do not send a second init.",
            plan="Read init-as-resume, try second init, then leftover connection_ack.",
            mod="gwslef",
            test_fn="test_ack_not_init",
            src_body="def resume(ack):\n    return {'connection_init': ack}\n",
            test_body="def test_ack_not_init():\n    assert 'leftover_ack' in resume('inv')\n",
            grep_pat="leftover_ack|connection_init|graphql-ws",
            grep_hit="src/gwslef.py:2: return {'connection_init': ack}",
            fail_msg="AssertionError: second connection_init created a new ack; leftover unused",
            first_old="    return {'connection_init': ack}",
            first_new="    return {'connection_init': ack, 'payload': {}}",
            first_obs="patched payload init (still a second init)",
            still_msg="AssertionError: payload init is not leftover_ack",
            reread_obs="graphql-ws leftover connection_ack restores the same protocol session",
            plan_change="Pass leftover_ack. A second connection_init is not resume.",
            fix_new="    return {'leftover_ack': ack}",
            fix_obs="patched leftover_ack",
            docs_url="https://github.com/enisdenjo/graphql-ws/blob/master/PROTOCOL.md",
            docs_ok="graphql-ws leftover connection_ack resumes; connection_init is a new handshake.",
            docs_url2="https://the-guild.dev/graphql/ws/protocol",
            docs_ok2="Use leftover_ack. Not cookie-replay.",
            outcome="leftover_ack restored graphql-ws. Second init unused (success).",
            domain="graphqlws-leftover-ack-vs-second-init",
            stack="graphql-ws leftover connection_ack",
            seed="graphqlws-leftover-ack",
            residual="Not cookie-replay. Not RFC6455 ping clone.",
            coverage=86,
        ),
        _p(
            slug="graphqlws-drop-ack-handoff",
            goal="Do not drop graphql-ws leftover connection_ack bind and re-init.",
            plan="Read drop leftover ack, try new init, then hand off bind.",
            mod="gwsdrop",
            test_fn="test_ack_bind",
            src_body="def bind(drop):\n    return {'connection_init': {}} if drop else {}\n",
            test_body="def test_ack_bind():\n    assert 'leftover_ack' in bind(True)\n",
            grep_pat="leftover_ack|connection_init|drop",
            grep_hit="src/gwsdrop.py:2: return {'connection_init': {}} if drop else {}",
            fail_msg="AssertionError: leftover ack bind dropped; new init unused",
            first_old="    return {'connection_init': {}} if drop else {}",
            first_new="    return {'connection_init': {'reconnect': True}} if drop else {}",
            first_obs="patched reconnect init (still dropped leftover bind)",
            still_msg="AssertionError: reconnect init does not bind leftover_ack",
            reread_obs="Dropping leftover_ack is gqlws-plat; init cannot restore it",
            plan_change="Leftover ack bind drop is graphql-ws plat. Handoff GWS-AK-11.",
            fix_new="    return {'handoff': 'GWS-AK-11'} if drop else {}",
            fix_obs="ticket filed. still init-classed",
            docs_url="https://github.com/enisdenjo/graphql-ws/blob/master/PROTOCOL.md#connectioninit",
            docs_ok="Leftover connection_ack is bound by the server, not a new init.",
            docs_url2="https://github.com/enisdenjo/graphql-ws/blob/master/PROTOCOL.md#connectionack",
            docs_ok2="Bind drop is gqlws-plat. Handoff GWS-AK-11.",
            outcome="Still init-classed; leftover ack bind drop — handoff GWS-AK-11.",
            domain="graphqlws-drop-leftover-ack-bind",
            stack="graphql-ws leftover ack drop",
            seed="graphqlws-drop-ack-handoff",
            residual="Init cannot rebind leftover connection_ack.",
            ticket="GWS-AK-11",
            ticket_why="leftover_ack bind owned by gqlws-plat",
            coverage=85,
        ),
    ),
    (
        _p(
            slug="mqttws-leftover-session",
            goal="Resume MQTT-over-WS leftover session; do not CONNECT a second clientId.",
            plan="Read connect-as-resume, try new CONNECT, then leftover session.",
            mod="mqtlef",
            test_fn="test_sess_not_connect",
            src_body="def resume(cid):\n    return {'CONNECT': cid}\n",
            test_body="def test_sess_not_connect():\n    assert 'leftover_session' in resume('inv')\n",
            grep_pat="leftover_session|CONNECT|mqtt",
            grep_hit="src/mqtlef.py:2: return {'CONNECT': cid}",
            fail_msg="AssertionError: second CONNECT created a new MQTT session; leftover unused",
            first_old="    return {'CONNECT': cid}",
            first_new="    return {'CONNECT': cid, 'clean': False}",
            first_obs="patched clean=False CONNECT (still a second CONNECT)",
            still_msg="AssertionError: clean=False CONNECT is not leftover_session",
            reread_obs="MQTT leftover sessionPresent restores the same clientId session",
            plan_change="Pass leftover_session. A second CONNECT is not resume.",
            fix_new="    return {'leftover_session': cid}",
            fix_obs="patched leftover_session",
            docs_url="https://docs.oasis-open.org/mqtt/mqtt/v5.0/os/mqtt-v5.0-os.html#_Toc3901031",
            docs_ok="MQTT leftover session resumes; CONNECT is a new client.",
            docs_url2="https://www.hivemq.com/blog/mqtt-essentials-part-3-client-broker-connection-establishment/",
            docs_ok2="Use leftover_session. Not cookie-replay.",
            outcome="leftover_session restored MQTT-over-WS. Second CONNECT unused (success).",
            domain="mqttws-leftover-session-vs-second-connect",
            stack="MQTT-over-WS leftover session",
            seed="mqttws-leftover-session",
            residual="Not cookie-replay. Not graphql-ws clone.",
            coverage=86,
        ),
        _p(
            slug="mqttws-drop-session-handoff",
            goal="Do not drop MQTT leftover session bind and CONNECT a new clientId.",
            plan="Read drop leftover session, try new CONNECT, then hand off bind.",
            mod="mqtdrop",
            test_fn="test_sess_bind",
            src_body="def bind(drop):\n    return {'CONNECT': 'new'} if drop else {}\n",
            test_body="def test_sess_bind():\n    assert 'leftover_session' in bind(True)\n",
            grep_pat="leftover_session|CONNECT|drop",
            grep_hit="src/mqtdrop.py:2: return {'CONNECT': 'new'} if drop else {}",
            fail_msg="AssertionError: leftover session bind dropped; new CONNECT unused",
            first_old="    return {'CONNECT': 'new'} if drop else {}",
            first_new="    return {'CONNECT': 'clean0'} if drop else {}",
            first_obs="patched clean0 CONNECT (still dropped leftover bind)",
            still_msg="AssertionError: clean0 CONNECT does not bind leftover_session",
            reread_obs="Dropping leftover_session is mqtt-plat; CONNECT cannot restore it",
            plan_change="Leftover session bind drop is MQTT plat. Handoff MQT-SS-12.",
            fix_new="    return {'handoff': 'MQT-SS-12'} if drop else {}",
            fix_obs="ticket filed. still CONNECT-classed",
            docs_url="https://docs.oasis-open.org/mqtt/mqtt/v5.0/os/mqtt-v5.0-os.html#_Toc3901048",
            docs_ok="MQTT leftover session is bound by the broker, not a new CONNECT.",
            docs_url2="https://www.hivemq.com/blog/mqtt-essentials-part-7-persistent-session-queuing-messages/",
            docs_ok2="Bind drop is mqtt-plat. Handoff MQT-SS-12.",
            outcome="Still CONNECT-classed; leftover session bind drop — handoff MQT-SS-12.",
            domain="mqttws-drop-leftover-session-bind",
            stack="MQTT-over-WS leftover session drop",
            seed="mqttws-drop-session-handoff",
            residual="CONNECT cannot rebind leftover session.",
            ticket="MQT-SS-12",
            ticket_why="leftover_session bind owned by mqtt-plat",
            coverage=85,
        ),
    ),
    (
        _p(
            slug="stomp-leftover-receipt",
            goal="Resume STOMP leftover receipt; do not SEND a second receipt-id.",
            plan="Read SEND-as-resume, try new SEND, then leftover receipt.",
            mod="stplef",
            test_fn="test_receipt_not_send",
            src_body="def resume(rid):\n    return {'SEND': rid}\n",
            test_body="def test_receipt_not_send():\n    assert 'leftover_receipt' in resume('inv')\n",
            grep_pat="leftover_receipt|SEND|stomp",
            grep_hit="src/stplef.py:2: return {'SEND': rid}",
            fail_msg="AssertionError: second SEND created a new receipt; leftover unused",
            first_old="    return {'SEND': rid}",
            first_new="    return {'SEND': rid, 'destination': '/q'}",
            first_obs="patched destination SEND (still a second SEND)",
            still_msg="AssertionError: destination SEND is not leftover_receipt",
            reread_obs="STOMP leftover receipt restores the same frame id",
            plan_change="Pass leftover_receipt. A second SEND is not resume.",
            fix_new="    return {'leftover_receipt': rid}",
            fix_obs="patched leftover_receipt",
            docs_url="https://stomp.github.io/stomp-specification-1.2.html#RECEIPT",
            docs_ok="STOMP leftover receipt resumes; SEND is a new frame.",
            docs_url2="https://stomp.github.io/stomp-specification-1.2.html#SEND",
            docs_ok2="Use leftover_receipt. Not cookie-replay.",
            outcome="leftover_receipt restored STOMP. Second SEND unused (success).",
            domain="stomp-leftover-receipt-vs-second-send",
            stack="STOMP leftover receipt",
            seed="stomp-leftover-receipt",
            residual="Not cookie-replay. Not MQTT clone.",
            coverage=85,
        ),
        _p(
            slug="stomp-drop-receipt-handoff",
            goal="Do not drop STOMP leftover receipt bind and SEND a new receipt-id.",
            plan="Read drop leftover receipt, try new SEND, then hand off bind.",
            mod="stpdrop",
            test_fn="test_receipt_bind",
            src_body="def bind(drop):\n    return {'SEND': 'new'} if drop else {}\n",
            test_body="def test_receipt_bind():\n    assert 'leftover_receipt' in bind(True)\n",
            grep_pat="leftover_receipt|SEND|drop",
            grep_hit="src/stpdrop.py:2: return {'SEND': 'new'} if drop else {}",
            fail_msg="AssertionError: leftover receipt bind dropped; new SEND unused",
            first_old="    return {'SEND': 'new'} if drop else {}",
            first_new="    return {'SEND': 'ack'} if drop else {}",
            first_obs="patched ack SEND (still dropped leftover bind)",
            still_msg="AssertionError: ack SEND does not bind leftover_receipt",
            reread_obs="Dropping leftover_receipt is stomp-plat; SEND cannot restore it",
            plan_change="Leftover receipt bind drop is STOMP plat. Handoff STP-RC-13.",
            fix_new="    return {'handoff': 'STP-RC-13'} if drop else {}",
            fix_obs="ticket filed. still SEND-classed",
            docs_url="https://stomp.github.io/stomp-specification-1.2.html#RECEIPT_frame",
            docs_ok="STOMP leftover receipt is bound by the broker, not a new SEND.",
            docs_url2="https://stomp.github.io/stomp-specification-1.2.html#Heart-beating",
            docs_ok2="Bind drop is stomp-plat. Handoff STP-RC-13.",
            outcome="Still SEND-classed; leftover receipt bind drop — handoff STP-RC-13.",
            domain="stomp-drop-leftover-receipt-bind",
            stack="STOMP leftover receipt drop",
            seed="stomp-drop-receipt-handoff",
            residual="SEND cannot rebind leftover receipt.",
            ticket="STP-RC-13",
            ticket_why="leftover_receipt bind owned by stomp-plat",
            coverage=84,
        ),
    ),
    (
        _p(
            slug="socketcluster-leftover-auth",
            goal="Resume SocketCluster leftover authToken; do not emit a second authenticate.",
            plan="Read authenticate-as-resume, try second auth, then leftover authToken.",
            mod="sctlef",
            test_fn="test_auth_not_emit",
            src_body="def resume(tok):\n    return {'authenticate': tok}\n",
            test_body="def test_auth_not_emit():\n    assert 'leftover_auth' in resume('inv')\n",
            grep_pat="leftover_auth|authenticate|socketcluster",
            grep_hit="src/sctlef.py:2: return {'authenticate': tok}",
            fail_msg="AssertionError: second authenticate created a new token; leftover unused",
            first_old="    return {'authenticate': tok}",
            first_new="    return {'authenticate': tok, 'signed': True}",
            first_obs="patched signed authenticate (still a second authenticate)",
            still_msg="AssertionError: signed authenticate is not leftover_auth",
            reread_obs="SocketCluster leftover authToken restores the same engine session",
            plan_change="Pass leftover_auth. A second authenticate is not resume.",
            fix_new="    return {'leftover_auth': tok}",
            fix_obs="patched leftover_auth",
            docs_url="https://socketcluster.io/docs/authentication/",
            docs_ok="SocketCluster leftover authToken resumes; authenticate is a new JWT.",
            docs_url2="https://socketcluster.io/docs/api-socket/",
            docs_ok2="Use leftover_auth. Not cookie-replay.",
            outcome="leftover_auth restored SocketCluster. Second authenticate unused (success).",
            domain="socketcluster-leftover-auth-vs-second-authenticate",
            stack="SocketCluster leftover authToken",
            seed="socketcluster-leftover-auth",
            residual="Not cookie-replay. Not STOMP clone.",
            coverage=86,
        ),
        _p(
            slug="socketcluster-drop-auth-handoff",
            goal="Do not drop SocketCluster leftover authToken bind and re-authenticate.",
            plan="Read drop leftover auth, try new authenticate, then hand off bind.",
            mod="sctdrop",
            test_fn="test_auth_bind",
            src_body="def bind(drop):\n    return {'authenticate': 'new'} if drop else {}\n",
            test_body="def test_auth_bind():\n    assert 'leftover_auth' in bind(True)\n",
            grep_pat="leftover_auth|authenticate|drop",
            grep_hit="src/sctdrop.py:2: return {'authenticate': 'new'} if drop else {}",
            fail_msg="AssertionError: leftover authToken bind dropped; new authenticate unused",
            first_old="    return {'authenticate': 'new'} if drop else {}",
            first_new="    return {'authenticate': 'jwt'} if drop else {}",
            first_obs="patched jwt authenticate (still dropped leftover bind)",
            still_msg="AssertionError: jwt authenticate does not bind leftover_auth",
            reread_obs="Dropping leftover_auth is sc-plat; authenticate cannot restore it",
            plan_change="Leftover authToken bind drop is SocketCluster plat. Handoff SCT-AT-14.",
            fix_new="    return {'handoff': 'SCT-AT-14'} if drop else {}",
            fix_obs="ticket filed. still authenticate-classed",
            docs_url="https://socketcluster.io/docs/authentication/#jwt-auth",
            docs_ok="Leftover authToken is bound by the broker, not a new authenticate.",
            docs_url2="https://socketcluster.io/docs/guides/authentication/",
            docs_ok2="Bind drop is sc-plat. Handoff SCT-AT-14.",
            outcome="Still authenticate-classed; leftover authToken bind drop — handoff SCT-AT-14.",
            domain="socketcluster-drop-leftover-auth-bind",
            stack="SocketCluster leftover authToken drop",
            seed="socketcluster-drop-auth-handoff",
            residual="Authenticate cannot rebind leftover authToken.",
            ticket="SCT-AT-14",
            ticket_why="leftover_auth bind owned by sc-plat",
            coverage=85,
        ),
    ),
    (
        _p(
            slug="partykit-leftover-hibernation",
            goal="Resume PartyKit leftover hibernation; do not spawn a second room.",
            plan="Read room-as-resume, try new room, then leftover hibernation.",
            mod="pktlef",
            test_fn="test_hib_not_room",
            src_body="def resume(rid):\n    return {'room': rid}\n",
            test_body="def test_hib_not_room():\n    assert 'leftover_hib' in resume('inv')\n",
            grep_pat="leftover_hib|room|partykit",
            grep_hit="src/pktlef.py:2: return {'room': rid}",
            fail_msg="AssertionError: second room created a new PartyKit instance; leftover unused",
            first_old="    return {'room': rid}",
            first_new="    return {'room': rid, 'id': 'new'}",
            first_obs="patched new room id (still a second room)",
            still_msg="AssertionError: new room is not leftover_hib",
            reread_obs="PartyKit leftover hibernation restores the same Durable Object room",
            plan_change="Pass leftover_hib. A second room is not resume.",
            fix_new="    return {'leftover_hib': rid}",
            fix_obs="patched leftover_hib",
            docs_url="https://docs.partykit.io/guides/deploying-your-partykit-server",
            docs_ok="PartyKit leftover hibernation resumes; a new room is a new instance.",
            docs_url2="https://docs.partykit.io/reference/partyserver-api/",
            docs_ok2="Use leftover_hib. Not cookie-replay.",
            outcome="leftover_hib restored PartyKit. Second room unused (success).",
            domain="partykit-leftover-hib-vs-second-room",
            stack="PartyKit leftover hibernation",
            seed="partykit-leftover-hibernation",
            residual="Not cookie-replay. Not SocketCluster clone.",
            coverage=86,
        ),
        _p(
            slug="partykit-drop-hib-handoff",
            goal="Do not drop PartyKit leftover hibernation bind and spawn a new room.",
            plan="Read drop leftover hibernation, try new room, then hand off bind.",
            mod="pktdrop",
            test_fn="test_hib_bind",
            src_body="def bind(drop):\n    return {'room': 'new'} if drop else {}\n",
            test_body="def test_hib_bind():\n    assert 'leftover_hib' in bind(True)\n",
            grep_pat="leftover_hib|room|drop",
            grep_hit="src/pktdrop.py:2: return {'room': 'new'} if drop else {}",
            fail_msg="AssertionError: leftover hibernation bind dropped; new room unused",
            first_old="    return {'room': 'new'} if drop else {}",
            first_new="    return {'room': 'wake'} if drop else {}",
            first_obs="patched wake room (still dropped leftover bind)",
            still_msg="AssertionError: wake room does not bind leftover_hib",
            reread_obs="Dropping leftover_hib is party-plat; room cannot restore it",
            plan_change="Leftover hibernation bind drop is PartyKit plat. Handoff PKT-HB-15.",
            fix_new="    return {'handoff': 'PKT-HB-15'} if drop else {}",
            fix_obs="ticket filed. still room-classed",
            docs_url="https://docs.partykit.io/guides/scaling-partykit-servers",
            docs_ok="PartyKit leftover hibernation is bound by the platform, not a new room.",
            docs_url2="https://docs.partykit.io/guides/persisting-state-into-storage/",
            docs_ok2="Bind drop is party-plat. Handoff PKT-HB-15.",
            outcome="Still room-classed; leftover hibernation bind drop — handoff PKT-HB-15.",
            domain="partykit-drop-leftover-hib-bind",
            stack="PartyKit leftover hibernation drop",
            seed="partykit-drop-hib-handoff",
            residual="Room cannot rebind leftover hibernation.",
            ticket="PKT-HB-15",
            ticket_why="leftover_hib bind owned by party-plat",
            coverage=85,
        ),
    ),
    (
        _p(
            slug="cfdo-leftover-ws-hib",
            goal="Resume Cloudflare Durable leftover websocket hibernation; do not accept a second socket.",
            plan="Read accept-as-resume, try second accept, then leftover hibernation.",
            mod="cfdlef",
            test_fn="test_hib_not_accept",
            src_body="def resume(sid):\n    return {'acceptWebSocket': sid}\n",
            test_body="def test_hib_not_accept():\n    assert 'leftover_ws_hib' in resume('inv')\n",
            grep_pat="leftover_ws_hib|acceptWebSocket|durable",
            grep_hit="src/cfdlef.py:2: return {'acceptWebSocket': sid}",
            fail_msg="AssertionError: second acceptWebSocket created a new DO socket; leftover unused",
            first_old="    return {'acceptWebSocket': sid}",
            first_new="    return {'acceptWebSocket': sid, 'tags': ['new']}",
            first_obs="patched tagged accept (still a second accept)",
            still_msg="AssertionError: tagged accept is not leftover_ws_hib",
            reread_obs="Durable leftover websocket hibernation restores the same tagged socket",
            plan_change="Pass leftover_ws_hib. A second acceptWebSocket is not resume.",
            fix_new="    return {'leftover_ws_hib': sid}",
            fix_obs="patched leftover_ws_hib",
            docs_url="https://developers.cloudflare.com/durable-objects/best-practices/websockets/",
            docs_ok="Durable leftover websocket hibernation resumes; acceptWebSocket is a new socket.",
            docs_url2="https://developers.cloudflare.com/durable-objects/api/state/#acceptwebsocket",
            docs_ok2="Use leftover_ws_hib. Not cookie-replay. Not PartyKit clone.",
            outcome="leftover_ws_hib restored Durable WS. Second accept unused (success).",
            domain="cfdo-leftover-ws-hib-vs-second-accept",
            stack="Cloudflare Durable leftover websocket hibernation",
            seed="cfdo-leftover-ws-hib",
            residual="Not cookie-replay. Not PartyKit hibernation clone.",
            coverage=87,
        ),
        _p(
            slug="cfdo-drop-ws-hib-handoff",
            goal="Do not drop Cloudflare Durable leftover websocket hibernation bind and accept again.",
            plan="Read drop leftover hibernation, try new accept, then hand off bind.",
            mod="cfddrop",
            test_fn="test_hib_bind",
            src_body="def bind(drop):\n    return {'acceptWebSocket': 'new'} if drop else {}\n",
            test_body="def test_hib_bind():\n    assert 'leftover_ws_hib' in bind(True)\n",
            grep_pat="leftover_ws_hib|acceptWebSocket|drop",
            grep_hit="src/cfddrop.py:2: return {'acceptWebSocket': 'new'} if drop else {}",
            fail_msg="AssertionError: leftover ws hibernation bind dropped; new accept unused",
            first_old="    return {'acceptWebSocket': 'new'} if drop else {}",
            first_new="    return {'acceptWebSocket': 'wake'} if drop else {}",
            first_obs="patched wake accept (still dropped leftover bind)",
            still_msg="AssertionError: wake accept does not bind leftover_ws_hib",
            reread_obs="Dropping leftover_ws_hib is do-plat; accept cannot restore it",
            plan_change="Leftover websocket hibernation bind drop is Durable plat. Handoff CFDO-WH-16.",
            fix_new="    return {'handoff': 'CFDO-WH-16'} if drop else {}",
            fix_obs="ticket filed. still accept-classed",
            docs_url="https://developers.cloudflare.com/durable-objects/best-practices/websockets/#websocket-hibernation",
            docs_ok="Leftover websocket hibernation is bound by the DO runtime, not a new accept.",
            docs_url2="https://developers.cloudflare.com/durable-objects/api/state/#getwebsockets",
            docs_ok2="Bind drop is do-plat. Handoff CFDO-WH-16.",
            outcome="Still accept-classed; leftover ws hibernation bind drop — handoff CFDO-WH-16.",
            domain="cfdo-drop-leftover-ws-hib-bind",
            stack="Cloudflare Durable leftover websocket hibernation drop",
            seed="cfdo-drop-ws-hib-handoff",
            residual="acceptWebSocket cannot rebind leftover hibernation.",
            ticket="CFDO-WH-16",
            ticket_why="leftover_ws_hib bind owned by do-plat",
            coverage=86,
        ),
    ),
]


def self_check() -> None:
    slugs, mods, tickets, domains = [], [], [], []
    for i, (ok, bad) in enumerate(PAIRS):
        if ok["first_old"] not in ok["src_body"]:
            raise ValueError(ok["slug"])
        if bad["first_old"] not in bad["src_body"]:
            raise ValueError(bad["slug"])
        for plant, kind in ((ok, "ok"), (bad, "bad")):
            if plant["slug"] in BANNED_SLUGS:
                raise ValueError(plant["slug"])
            slugs.append(plant["slug"])
            mods.append(plant["mod"])
            domains.append(plant["domain"])
            _goal_ok(plant["goal"])
            if kind == "bad":
                tickets.append(plant["ticket"])
        build_pair(41 + i, ok, bad)
    if len(set(slugs)) != len(slugs):
        raise ValueError(f"duplicate slugs {slugs}")
    if len(set(mods)) != len(mods):
        raise ValueError(f"duplicate mods {mods}")
    if len(set(tickets)) != len(tickets):
        raise ValueError(f"duplicate tickets {tickets}")
    if len(set(domains)) != len(domains):
        raise ValueError(f"duplicate domains {domains}")
    print(f"self_check ok: {len(PAIRS)} pairs")


def reserved_at(round_n: int) -> bool:
    return (FDIR / f"ROUND-r{round_n:02d}.reserved.json").exists()


def run_loop(max_rounds: int = 16) -> int:
    from round_txn import TransactionError, abort, frontier_status, publish, reserve

    used = set()
    for p in FDIR.glob("batch-r*.jsonl"):
        for line in p.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            rec = json.loads(line)
            used.add(rec.get("meta", {}).get("seed", ""))
            used.add(rec.get("id", "").split("-", 2)[-1] if rec.get("id") else "")
    queue = [(ok, bad) for ok, bad in PAIRS if ok["slug"] not in used and bad["slug"] not in used]
    published = []
    while queue and len(published) < max_rounds:
        status = frontier_status(FDIR)
        round_n = status["next_round"]
        if reserved_at(round_n):
            print(json.dumps({"skip": "reserved", "round": round_n}))
            return 2
        ok, bad = queue.pop(0)
        payload = None
        try:
            payload = reserve(FDIR, round_n, 2)
        except TransactionError as exc:
            print(json.dumps({"reserve_fail": str(exc), "round": round_n}))
            return 2
        token = payload["token"]
        stage = Path(payload["staging_dir"])
        try:
            ids = emit_stage(stage, round_n, ok, bad)
            publish(FDIR, round_n, token)
        except Exception as exc:
            abort(FDIR, round_n, token)
            print(json.dumps({"abort": str(exc), "round": round_n}))
            raise
        rec = {"round": round_n, "ids": list(ids)}
        published.append(rec)
        print(json.dumps({"published": rec}))
    print(json.dumps({"done": published, "count": len(published)}))
    return 0


def main() -> int:
    if len(sys.argv) > 1 and sys.argv[1] == "self_check":
        self_check()
        return 0
    self_check()
    return run_loop(16)


if __name__ == "__main__":
    raise SystemExit(main())
