#!/usr/bin/env python3
"""Emit payment-idempotency episodes (16-step success + 17-step fail/handoff)."""

from __future__ import annotations

import json
from typing import Any


FACTORY = "payment-idempotency-factory"
GENERATOR = "grok-4.6"
BANNED_KEYS = ("thought", "chain_of_thought", "scratch", "inner_monologue")


def _step(n: int, decision_basis: str, tool_call: dict, observation: str) -> dict:
    return {
        "n": n,
        "decision_basis": decision_basis,
        "tool_call": tool_call,
        "observation": observation,
    }


def _bash(command: str) -> dict:
    return {"name": "bash", "args": {"command": command}}


def _read(path: str) -> dict:
    return {"name": "read", "args": {"path": path}}


def _write(path: str, contents: str) -> dict:
    return {"name": "write", "args": {"path": path, "contents": contents}}


def _edit(path: str, old: str, new: str) -> dict:
    return {"name": "edit", "args": {"path": path, "old": old, "new": new}}


def _grep(path: str, pattern: str) -> dict:
    return {"name": "grep", "args": {"path": path, "pattern": pattern}}


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


def _mig(round_n: int, stem: str) -> str:
    return f"migrations/{10000 + round_n}_{stem}.sql"


def build_success(round_n: int, p: dict) -> dict:
    src, hook, test, test2 = p["src"], p["hook"], p["test"], p["test2"]
    mig = _mig(round_n, p["mig"])
    eid = f"pay-r{round_n}-{p['slug']}"
    steps = [
        _step(
            1,
            f"Plan: read {p['surface_read']} before {p['skip_pred']} skip.",
            _bash(f"rg -n '{p['rg']}' src tests | head -n 24"),
            p["rg_obs"],
        ),
        _step(
            2,
            f"Observation: {p['test_name']} exists (step 1). Read {src}.",
            _read(src),
            p["src_body"],
        ),
        _step(
            3,
            f"Observation: {p['obs3']} (step 2). Read {hook}.",
            _read(hook),
            p["hook_body"],
        ),
        _step(
            4,
            f"Observation: {p['obs4']} (step 3). Read tests.",
            _read(test),
            p["test_body"],
        ),
        _step(
            5,
            f"Observation: {p['obs5']} (step 4). Run.",
            _bash(f"pytest {test} -q --tb=short 2>&1 | tail -n 12"),
            p["fail_obs"],
        ),
        _step(
            6,
            f"Plan: first apply — skip {p['verb']} if {p['skip_pred']}.",
            _edit(src, p["skip_old"], p["skip_new"]),
            f"patched {p['skip_label']}",
        ),
        _step(
            7,
            f"Observation: {p['skip_label']} (step 6). {p['obs7']}",
            _bash(f"pytest {test} {test2} -q --tb=short 2>&1 | tail -n 10"),
            p["still_fail_obs"],
        ),
        _step(
            8,
            f"Reflection: plan change — {p['plan_change']}.",
            _write(src, p["rewrite_src"]),
            p["rewrite_src_obs"],
        ),
        _step(
            9,
            f"Observation: rewrite (step 8). {p.get('obs9', p.get('rewrite_hook_obs', 'hook rewritten'))}",
            _write(hook, p["rewrite_hook"]),
            p["rewrite_hook_obs"],
        ),
        _step(
            10,
            "Observation: handlers (step 9). DDL.",
            _write(mig, p["ddl"]),
            p["ddl_obs"],
        ),
        _step(
            11,
            "Observation: tables (step 10). Re-run.",
            _bash(
                f"psql \"$DATABASE_URL\" -f {mig} && pytest {test} -q --tb=short 2>&1 | tail -n 10"
            ),
            "CREATE TABLE\n2 passed in 0.20s",
        ),
        _step(
            12,
            "Observation: primary green (step 11). two entities both apply.",
            _read(test2),
            p["test2_body"],
        ),
        _step(
            13,
            "Observation: second entity (step 12). Run.",
            _bash(f"pytest {test2} -q --tb=short 2>&1 | tail -n 8"),
            "1 passed in 0.07s",
        ),
        _step(
            14,
            "Observation: extra contract (step 13). Suite.",
            _bash("pytest tests -q --tb=line 2>&1 | tail -n 8"),
            "8 passed in 0.49s",
        ),
        _step(
            15,
            "Observation: 8/8 (step 14). Confirm PK.",
            _bash(f"psql \"$DATABASE_URL\" -c \"select {p['pk']} from {p['table']}\""),
            p["psql_rows"],
        ),
        _step(
            16,
            f"Observation: rows (step 15). Residual: {p['residual']}.",
            _grep(src, p["grep_pat"]),
            p["grep_obs"],
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
            "plan_changes": 1,
            "tests_passed": 8,
            "cost_steps": 16,
        },
        "meta": {
            "factory": FACTORY,
            "round": round_n,
            "generator": GENERATOR,
        },
    }
    assert_clean(ep)
    if len(steps) != 16:
        raise ValueError(f"{eid} expected 16 steps")
    return ep


def build_fail(round_n: int, p: dict) -> dict:
    src, hook, test, test2, xfail = p["src"], p["hook"], p["test"], p["test2"], p["xfail"]
    mig = _mig(round_n, p["mig"])
    eid = f"pay-r{round_n}-{p['slug']}"
    steps = [
        _step(
            1,
            f"Plan: read {p['surface_read']} before {p['skip_pred']} skip.",
            _bash(f"rg -n '{p['rg']}' src tests | head -n 24"),
            p["rg_obs"],
        ),
        _step(
            2,
            f"Observation: {p['test_name']} exists (step 1). Read {src}.",
            _read(src),
            p["src_body"],
        ),
        _step(
            3,
            f"Observation: {p['obs3']} (step 2). Read {test}.",
            _read(test),
            p["test_body"],
        ),
        _step(
            4,
            f"Observation: tests: {p['obs4']} (step 3). Read tests.",
            _read(test),
            p["test_body_short"],
        ),
        _step(
            5,
            f"Observation: {p['obs5']} (step 4). Run.",
            _bash(f"pytest {test} -q --tb=short 2>&1 | tail -n 12"),
            p["fail_obs"],
        ),
        _step(
            6,
            f"Plan: first apply — skip {p['verb']} if {p['skip_pred']}.",
            _edit(src, p["skip_old"], p["skip_new"]),
            f"patched {p['skip_label']}",
        ),
        _step(
            7,
            f"Observation: {p['skip_label']} (step 6). {p['obs7']}",
            _bash(f"pytest {test} {test2} -q --tb=short 2>&1 | tail -n 10"),
            p["still_fail_obs"],
        ),
        _step(
            8,
            f"Reflection: plan change — {p['plan_change']}.",
            _write(src, p["rewrite_src"]),
            p["rewrite_src_obs"],
        ),
        _step(
            9,
            "Observation: rewrite (step 8). claim helper.",
            _write(hook, p["rewrite_hook"]),
            p["rewrite_hook_obs"],
        ),
        _step(
            10,
            "Observation: handlers (step 9). DDL.",
            _write(mig, p["ddl"]),
            p["ddl_obs"],
        ),
        _step(
            11,
            "Observation: tables (step 10). Re-run.",
            _bash(
                f"psql \"$DATABASE_URL\" -f {mig} && pytest {test} {test2} -q --tb=short 2>&1 | tail -n 10"
            ),
            "CREATE TABLE\n2 passed in 0.19s",
        ),
        _step(
            12,
            "Observation: primary+extra green (step 11). two entities.",
            _read(test2),
            p["test2_body"],
        ),
        _step(
            13,
            "Observation: second entity (step 12). Run.",
            _bash(f"pytest {test2} -q --tb=short 2>&1 | tail -n 8"),
            "1 passed in 0.07s",
        ),
        _step(
            14,
            "Observation: extra contract (step 13). Suite.",
            _bash("pytest tests -q --tb=line 2>&1 | tail -n 8"),
            "7 passed in 0.46s",
        ),
        _step(
            15,
            f"Observation: 7/8; {p['xfail_label']} (step 14). residual.",
            _read(xfail),
            p["xfail_body"],
        ),
        _step(
            16,
            "Observation: residual failing (step 15). Run then xfail.",
            _bash(f"pytest {xfail} -q --tb=short 2>&1 | tail -n 8"),
            p["xfail_fail_obs"],
        ),
        _step(
            17,
            "Observation: xfail handoff (step 16).",
            _edit(
                xfail,
                p["xfail_old"],
                p["xfail_new"],
            ),
            p["xfail_patch_obs"],
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
            "plan_changes": 1,
            "tests_passed": 7,
            "cost_steps": 17,
            "xfailed": 1,
            "handoff": 1,
        },
        "meta": {
            "factory": FACTORY,
            "round": round_n,
            "generator": GENERATOR,
        },
    }
    assert_clean(ep)
    if len(steps) != 17:
        raise ValueError(f"{eid} expected 17 steps")
    return ep


def notes_md(round_n: int, ok: dict, bad: dict, coverage: int) -> str:
    return (
        f"# NOTES-r{round_n:02d} payment-idempotency-factory\n\n"
        f"Novel coverage: {coverage}%\n\n"
        f"Two designed episodes (quota 2). Surfaces: {ok['surfaces']} vs {bad['surfaces']}.\n"
        f"Avoided {ok['avoided']}. This is {ok['this_is']}.\n\n"
        "| id | seed | first apply | plan change | terminal |\n"
        "|---|---|---|---|---|\n"
        f"| pay-r{round_n}-{ok['slug']} | {ok['seed']} | {ok['first_apply']} | {ok['plan_change']} | success 8/8 |\n"
        f"| pay-r{round_n}-{bad['slug']} | {bad['seed']} | {bad['first_apply']} | {bad['plan_change']} | handoff/xfail 7/8 |\n\n"
        "## Step counts\n"
        f"- ep1: 16. {ok['step_note']}\n"
        f"- ep2: 17. {bad['step_note']}\n\n"
        "## decision_basis audit\n"
        "Every step starts Plan:/Observation:/Reflection:/Tool call:.\n"
        "No thought / chain_of_thought / scratch / inner_monologue. No spike_events.\n"
        "No sim_or_real: real. Invented plant `till`.\n\n"
        "## Weaknesses / next\n"
        f"{bad['next_note']}\n"
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
    prefixes = ("Plan:", "Observation:", "Reflection:", "Tool call:")
    for ep in (ok_ep, bad_ep):
        for step in ep["steps"]:
            db = step["decision_basis"]
            if not db.startswith(prefixes):
                raise ValueError(f"{ep['id']} step {step['n']} bad decision_basis")
            if not step["observation"].strip():
                raise ValueError(f"{ep['id']} empty observation")
        assert_clean(ep)
