#!/usr/bin/env python3
"""Emit unique llm-eval-flakiness episodes (16-step success + 16-step partial)."""

from __future__ import annotations

import json
from typing import Any


FACTORY = "llm-eval-flakiness-factory"
GENERATOR = "grok-4.6"
BANNED_KEYS = ("thought", "chain_of_thought", "scratch", "inner_monologue")
DB_PREFIXES = ("Plan:", "Observation:", "Reflection:", "Tool call:")
BANNED_SNIPPETS = (
    "SKU-9",
    "combining mark",
    "U+0300",
    "U+1D17",
    "skip-as-1.0",
    "skip-as-one",
    "numpy.bool_",
    "numpy.int64",
)


def _step(n: int, decision_basis: str, tool_call: dict, observation: str) -> dict:
    db = decision_basis.strip()
    if not db.startswith(DB_PREFIXES):
        raise ValueError(f"step {n} decision_basis prefix: {db[:80]!r}")
    if len(db) > 240:
        raise ValueError(f"step {n} decision_basis {len(db)} > 240: {db}")
    if not observation or not str(observation).strip():
        raise ValueError(f"step {n} empty observation")
    return {
        "n": n,
        "decision_basis": db,
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
    elif isinstance(obj, str):
        for snippet in BANNED_SNIPPETS:
            if snippet in obj:
                raise ValueError(f"banned leftover snippet {snippet!r} at {path}")


def _eid(round_n: int, slug: str) -> str:
    return f"lef-r{round_n}-{slug}"


def build_success(round_n: int, p: dict) -> dict:
    src, helper, test, test2 = p["src"], p["helper"], p["test"], p["test2"]
    eid = _eid(round_n, p["slug"])
    steps = [
        _step(
            1,
            f"Plan: dump {p['dump']} before {p['first_apply']}.",
            _bash(
                f"rg -n '{p['rg']}' src tests goldens configs 2>/dev/null | head -n 36"
            ),
            p["rg_obs"],
        ),
        _step(
            2,
            f"Observation: {p['test_name']} exists (step 1). Read {test}.",
            _read(test),
            p["test_body"],
        ),
        _step(
            3,
            f"Observation: gate wants {p['gate_want']} (step 2). Run {test}.",
            _bash(f"pytest {test} -q --tb=short 2>&1 | tail -n 18"),
            p["fail_obs"],
        ),
        _step(
            4,
            f"Observation: {p['fail_short']} (step 3). Read {src}.",
            _read(src),
            p["src_body"],
        ),
        _step(
            5,
            f"Observation: {p['obs5']} (step 4). Reproduce the statistic.",
            _bash(p["stats_cmd"]),
            p["stats_obs"],
        ),
        _step(
            6,
            f"Plan: first apply — {p['first_apply']}.",
            _edit(src, p["wrong_old"], p["wrong_new"]),
            f"patched {p['wrong_label']}; still {p['wrong_still']}",
        ),
        _step(
            7,
            f"Observation: {p['wrong_label']} (step 6). Re-run {test}.",
            _bash(f"pytest {test} -q --tb=short 2>&1 | tail -n 14"),
            p["still_fail"],
        ),
        _step(
            8,
            f"Reflection: plan change after {p['first_apply']} — {p['plan_change']}.",
            _write(src, p["fix_src"]),
            p["rewrite_obs"],
        ),
        _step(
            9,
            f"Observation: rewrite (step 8). Write {helper}.",
            _write(helper, p["fix_helper"]),
            p["helper_obs"],
        ),
        _step(
            10,
            f"Observation: helper (step 9). Re-run {test}.",
            _bash(f"pytest {test} -q --tb=short 2>&1 | tail -n 10"),
            p["pass_obs"],
        ),
        _step(
            11,
            "Observation: gate green (step 10). Full suite.",
            _bash("pytest tests -q --tb=line 2>&1 | tail -n 10"),
            p["suite_ok"],
        ),
        _step(
            12,
            f"Observation: {p['suite_short']} (step 11). Read {test2}.",
            _read(test2),
            p["test2_body"],
        ),
        _step(
            13,
            f"Observation: second contract (step 12). Run {test2}.",
            _bash(f"pytest {test2} -q --tb=short 2>&1 | tail -n 8"),
            p["test2_pass"],
        ),
        _step(
            14,
            f"Observation: second green (step 13). Residual {p['residual']}.",
            _grep(p["residual_path"], p["residual_pat"]),
            p["residual_obs"],
        ),
        _step(
            15,
            f"Observation: residual out of ticket (step 14). Re-run {test}.",
            _bash(f"pytest {test} -q --tb=line 2>&1 | tail -n 4"),
            p["gate_again"],
        ),
        _step(
            16,
            f"Observation: still green (step 15). Confirm {p['confirm']}.",
            _read(src),
            p["final_obs"],
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
            "tests_passed": p["tests_passed"],
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
        raise ValueError(f"{eid} expected 16 steps, got {len(steps)}")
    return ep


def build_partial(round_n: int, p: dict) -> dict:
    src, helper, test = p["src"], p["helper"], p["test"]
    nightly, ntest = p["nightly"], p["nightly_test"]
    eid = _eid(round_n, p["slug"])
    steps = [
        _step(
            1,
            f"Plan: dump {p['dump']} before {p['first_apply']}.",
            _bash(
                f"rg -n '{p['rg']}' src tests goldens configs 2>/dev/null | head -n 36"
            ),
            p["rg_obs"],
        ),
        _step(
            2,
            f"Observation: {p['test_name']} exists (step 1). Read {test}.",
            _read(test),
            p["test_body"],
        ),
        _step(
            3,
            f"Observation: gate wants {p['gate_want']} (step 2). Run {test}.",
            _bash(f"pytest {test} -q --tb=short 2>&1 | tail -n 18"),
            p["fail_obs"],
        ),
        _step(
            4,
            f"Observation: {p['fail_short']} (step 3). Read {src}.",
            _read(src),
            p["src_body"],
        ),
        _step(
            5,
            f"Observation: {p['obs5']} (step 4). Reproduce the statistic.",
            _bash(p["stats_cmd"]),
            p["stats_obs"],
        ),
        _step(
            6,
            f"Plan: first apply — {p['first_apply']}.",
            _edit(src, p["wrong_old"], p["wrong_new"]),
            f"patched {p['wrong_label']}; still {p['wrong_still']}",
        ),
        _step(
            7,
            f"Observation: {p['wrong_label']} (step 6). Re-run {test}.",
            _bash(f"pytest {test} -q --tb=short 2>&1 | tail -n 14"),
            p["still_fail"],
        ),
        _step(
            8,
            f"Reflection: plan change after {p['first_apply']} — {p['plan_change']}.",
            _write(src, p["fix_src"]),
            p["rewrite_obs"],
        ),
        _step(
            9,
            f"Observation: rewrite (step 8). Write {helper}.",
            _write(helper, p["fix_helper"]),
            p["helper_obs"],
        ),
        _step(
            10,
            f"Observation: helper (step 9). Re-run {test}.",
            _bash(f"pytest {test} -q --tb=short 2>&1 | tail -n 10"),
            p["pass_obs"],
        ),
        _step(
            11,
            "Observation: gate green (step 10). Full suite.",
            _bash("pytest tests -q --tb=line 2>&1 | tail -n 12"),
            p["suite_fail"],
        ),
        _step(
            12,
            f"Observation: nightly leftover (step 11). Read {nightly}.",
            _read(nightly),
            p["nightly_body"],
        ),
        _step(
            13,
            "Observation: leftover confirmed (step 12). xfail nightly for merge.",
            _edit(ntest, p["xfail_old"], p["xfail_new"]),
            f"xfails {p['handoff']}",
        ),
        _step(
            14,
            f"Observation: nightly xfails (step 13). Re-run {test} + {ntest}.",
            _bash(f"pytest {test} {ntest} -q --tb=line 2>&1 | tail -n 6"),
            p["xfail_obs"],
        ),
        _step(
            15,
            f"Observation: merge gate green (step 14). Confirm leftover {nightly}.",
            _read(nightly),
            p["leftover_obs"],
        ),
        _step(
            16,
            f"Observation: leftover stands (step 15). Ticket is {p['test_name']}.",
            _bash(f"pytest {test} -q --tb=line 2>&1 | tail -n 4"),
            p["gate_again"],
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
            "tests_passed": p["tests_passed"],
            "xfailed": 1,
            "handoff": 1,
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
        raise ValueError(f"{eid} expected 16 steps, got {len(steps)}")
    return ep


def notes_md(round_n: int, ok: dict, bad: dict, coverage: int) -> str:
    prev = round_n - 1
    return (
        f"# NOTES-r{round_n} llm-eval-flakiness-factory\n\n"
        f"Novel coverage: {coverage}%\n\n"
        f"- IDs `lef-r{round_n}-*`. generator `grok-4.6`. Q=2.\n"
        f"- Step counts: {ok['slug']} 16, {bad['slug']} 16.\n"
        f"- Seeds: (1) {ok['seed']} (2) {bad['seed']}\n"
        f"- Distinct from lef r01–r{prev} ({ok['avoided']}; {bad['avoided']}).\n"
        f"- Mix: success ({ok['slug']}) + partial ({bad['slug']} nightly handoff).\n"
        f"- Ban: no unicode leftover (SKU-9 combining marks), no HTTP skip-as-1.0, "
        f"no r76–r612 coerce catalog clone, no r613–r628 agreement-metric clone, "
        f"no r629–r700 cache-omit/last-unit/seed-leak/temp0/rubric-alias/tool-trunc mill, "
        f"no r701–r727 2PL/CUSUM/Angoff/MMLU-redux/SWE-ftp/FActScore/PR-AUC/IOB2/"
        f"tau-passk/lost-middle/GAIA/XSTest/TOST/Cronbach/WE/CoNLL/Simpson clone.\n\n"
        f"## decision_basis audit\n"
        f"Every step starts Plan:/Observation:/Reflection:/Tool call:, ≤240 chars.\n"
        f"No thought / chain_of_thought / scratch / inner_monologue. No spike_events.\n"
        f"No sim_or_real: real.\n"
    )


def validate_pair(ok_ep: dict, bad_ep: dict, round_n: int) -> None:
    if ok_ep["reward"]["success"] is not True:
        raise ValueError("success episode must reward.success true")
    if bad_ep["reward"]["success"] is not False:
        raise ValueError("partial episode must reward.success false")
    if ok_ep["meta"]["round"] != round_n or bad_ep["meta"]["round"] != round_n:
        raise ValueError("meta.round mismatch")
    if ok_ep["id"] == bad_ep["id"]:
        raise ValueError("duplicate ids in pair")
    if len(ok_ep["steps"]) != 16 or len(bad_ep["steps"]) != 16:
        raise ValueError("both episodes need 16 steps")
    assert_clean(ok_ep)
    assert_clean(bad_ep)
