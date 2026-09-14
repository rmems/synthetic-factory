"""Emit infra-as-code episodes (17-step success + 17-step leftover/handoff)."""

from __future__ import annotations

import json
from typing import Any

FACTORY = "infra-as-code-factory"
GENERATOR = "grok-4.6"
BANNED_KEYS = ("thought", "chain_of_thought", "scratch", "inner_monologue")
BANNED_SUB = (
    "cannot land the tofu pin",
    "InvalidParameterValueException",
    "InvalidParameterValue",
    "UnknownResourceException",
    "helm 2.5",
    "HarborCluster",
    "SparkApplication",
)
DB_PREFIXES = ("Plan:", "Observation:", "Reflection:", "Tool call:")
MAX_DB = 240


def _step(n: int, decision_basis: str, tool_call: dict, observation: str) -> dict:
    if len(decision_basis) > MAX_DB:
        raise ValueError(f"decision_basis {len(decision_basis)} > {MAX_DB}: {decision_basis[:80]}")
    if not decision_basis.startswith(DB_PREFIXES):
        raise ValueError(f"decision_basis prefix: {decision_basis[:40]}")
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


def _edit(path: str, old: str, new: str) -> dict:
    return {"name": "edit", "args": {"path": path, "old": old, "new": new}}


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
        for sub in BANNED_SUB:
            if sub in obj:
                raise ValueError(f"banned substring {sub!r} at {path}")


def _clip(text: str, label: str) -> str:
    if len(text) > MAX_DB:
        raise ValueError(f"{label} {len(text)} > {MAX_DB}: {text[:80]}")
    return text


def build_success(round_n: int, p: dict) -> dict:
    eid = f"iac-r{round_n}-{p['slug']}"
    test = p["test"]
    steps = [
        _step(
            1,
            _clip(f"Plan: ticket is {p['ticket']}. {p['s1_act']}", "s1"),
            _bash(p["s1_cmd"]),
            p["s1_obs"],
        ),
        _step(
            2,
            _clip(f"Observation: {p['s2_lead']}. Read {test}.", "s2"),
            _read(test),
            p["test_body"],
        ),
        _step(
            3,
            _clip(f"Observation: {p['s3_lead']}. Read {p['cfg']}.", "s3"),
            _read(p["cfg"]),
            p["cfg_body"],
        ),
        _step(
            4,
            _clip(f"Observation: {p['s4_lead']}. {p['s4_act']}", "s4"),
            _bash(p["s4_cmd"]),
            p["s4_obs"],
        ),
        _step(
            5,
            _clip(f"Observation: {p['s5_lead']}. {p['s5_act']}", "s5"),
            _bash(p["s5_cmd"]),
            p["s5_obs"],
        ),
        _step(
            6,
            _clip(f"Observation: {p['s6_lead']}. pytest {test}.", "s6"),
            _bash(f"pytest {test} -q --tb=line"),
            p["s6_obs"],
        ),
        _step(
            7,
            _clip(f"Observation: {p['s7_lead']}. First wrong: {p['wrong']}.", "s7"),
            _bash(p["wrong_cmd"]),
            p["wrong_obs"],
        ),
        _step(
            8,
            _clip(f"Observation: {p['s8_lead']}. {p['s8_act']}", "s8"),
            _bash(p["s8_cmd"]),
            p["s8_obs"],
        ),
        _step(
            9,
            _clip(f"Reflection: {p['plan_change']}", "s9"),
            _edit(p["ci"], p["ci_old"], p["ci_new"]),
            "patched CI.md",
        ),
        _step(
            10,
            _clip(f"Observation: CI.md patched. {p['s10_act']}", "s10"),
            _bash(p["fix_cmd"]),
            p["fix_obs"],
        ),
        _step(
            11,
            _clip(f"Observation: {p['s11_lead']}. pytest.", "s11"),
            _bash(f"pytest {test} -q"),
            p["pass_obs"],
        ),
        _step(
            12,
            _clip(f"Observation: 2/2. {p['s12_act']}", "s12"),
            _bash(p["s12_cmd"]),
            p["s12_obs"],
        ),
        _step(
            13,
            _clip(f"Observation: {p['s13_lead']}. leftover check.", "s13"),
            _bash(p["left_cmd"]),
            p["left_obs"],
        ),
        _step(
            14,
            _clip(f"Observation: residual {p['residual']}. {p['s14_act']}", "s14"),
            _bash(p["s14_cmd"]),
            p["s14_obs"],
        ),
        _step(
            15,
            _clip(f"Observation: {p['s15_lead']}. rg confirm.", "s15"),
            _bash(p["rg_cmd"]),
            p["rg_obs"],
        ),
        _step(
            16,
            _clip(f"Observation: {p['s16_lead']}. status.", "s16"),
            _bash(p["s16_cmd"]),
            p["s16_obs"],
        ),
        _step(
            17,
            _clip(f"Observation: {p['s17_lead']}. close-out.", "s17"),
            _bash(f"pytest {test} -q"),
            "..\n2 passed\n",
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
            "apply_fails": 1,
            "plan_changes": 1,
            "tests_passed": 2,
            "cost_steps": 17,
        },
        "meta": {"factory": FACTORY, "round": round_n, "generator": GENERATOR},
    }
    assert_clean(ep)
    return ep


def build_fail(round_n: int, p: dict) -> dict:
    eid = f"iac-r{round_n}-{p['slug']}"
    test = p["test"]
    steps = [
        _step(
            1,
            _clip(f"Plan: ticket is {p['ticket']}. {p['s1_act']}", "s1"),
            _bash(p["s1_cmd"]),
            p["s1_obs"],
        ),
        _step(
            2,
            _clip(f"Observation: {p['s2_lead']}. Read {test}.", "s2"),
            _read(test),
            p["test_body"],
        ),
        _step(
            3,
            _clip(f"Observation: {p['s3_lead']}. Read {p['cfg']}.", "s3"),
            _read(p["cfg"]),
            p["cfg_body"],
        ),
        _step(
            4,
            _clip(f"Observation: {p['s4_lead']}. {p['s4_act']}", "s4"),
            _bash(p["s4_cmd"]),
            p["s4_obs"],
        ),
        _step(
            5,
            _clip(f"Observation: {p['s5_lead']}. pytest {test}.", "s5"),
            _bash(f"pytest {test} -q --tb=line"),
            p["s5_obs"],
        ),
        _step(
            6,
            _clip(f"Observation: {p['s6_lead']}. First wrong: {p['wrong']}.", "s6"),
            _bash(p["wrong_cmd"]),
            p["wrong_obs"],
        ),
        _step(
            7,
            _clip(f"Reflection: handoff {p['handoff']}; do not {p['dont']}.", "s7"),
            _edit(p["ci"], p["ci_old"], p["ci_new"]),
            "patched CI.md handoff",
        ),
        _step(
            8,
            _clip(f"Observation: handoff written. leftover {p['left_name']}.", "s8"),
            _bash(p["left_cmd"]),
            p["left_obs"],
        ),
        _step(
            9,
            _clip(f"Observation: leftover still present. pytest residual.", "s9"),
            _bash(f"pytest {test} -q --tb=line"),
            p["resid_obs"],
        ),
        _step(
            10,
            _clip(f"Observation: 1/2. echo HANDOFF {p['handoff']}.", "s10"),
            _bash(f"echo HANDOFF {p['handoff_echo']}"),
            f"HANDOFF {p['handoff_echo']}\n",
        ),
        _step(
            11,
            _clip(f"Observation: handoff. {p['s11_act']}", "s11"),
            _bash(p["s11_cmd"]),
            p["s11_obs"],
        ),
        _step(
            12,
            _clip(f"Observation: {p['s12_lead']}. pytest residual.", "s12"),
            _bash(f"pytest {test} -q --tb=line"),
            p["resid_obs"],
        ),
        _step(
            13,
            _clip(f"Observation: 1/2 PARTIAL. {p['s13_act']}", "s13"),
            _bash(p["s13_cmd"]),
            p["s13_obs"],
        ),
        _step(
            14,
            _clip(f"Observation: leftover {p['left_name']} confirmed. stop apply.", "s14"),
            _bash(p["s14_cmd"]),
            p["s14_obs"],
        ),
        _step(
            15,
            _clip(f"Observation: {p['s15_lead']}. do not {p['dont']}.", "s15"),
            _bash(p["s15_cmd"]),
            p["s15_obs"],
        ),
        _step(
            16,
            _clip(f"Observation: {p['s16_lead']}. residual.", "s16"),
            _bash(p["s16_cmd"]),
            p["s16_obs"],
        ),
        _step(
            17,
            _clip(f"Observation: PARTIAL leftover {p['left_name']}. end.", "s17"),
            _bash(f"pytest {test} -q --tb=line"),
            p["resid_obs"],
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
            "apply_fails": 1,
            "plan_changes": 1,
            "tests_passed": 1,
            "tests_failed": 1,
            "handoff": 1,
            "cost_steps": 17,
        },
        "meta": {"factory": FACTORY, "round": round_n, "generator": GENERATOR},
    }
    assert_clean(ep)
    return ep


def notes_md(round_n: int, ok: dict, bad: dict, cov: int, extra: str) -> str:
    return (
        f"# NOTES-r{round_n} infra-as-code-factory\n\n"
        f"Novel coverage: {cov}%\n\n"
        f"Quota 2. Unique IaC drift/repair (not r78–r586 AWS×leftover-CRD catalog).\n"
        f"{extra}\n\n"
        f"| id | seed | clean-plan then fail | leftover | terminal |\n"
        f"|---|---|---|---|---|\n"
        f"| iac-r{round_n}-{ok['slug']} | {ok['seed']} | {ok['fail']} | {ok['left']} | {ok['term']} |\n"
        f"| iac-r{round_n}-{bad['slug']} | {bad['seed']} | {bad['fail']} | {bad['left']} | {bad['term']} |\n\n"
        f"## Step counts\n"
        f"- ep1: 17. {ok['arc']}\n"
        f"- ep2: 17. {bad['arc']}\n\n"
        f"## decision_basis audit\n"
        f"Plan:/Observation:/Reflection:/Tool call: ≤240. No hidden CoT. No spike_events.\n"
        f"No sim_or_real: real. Designed plants only. Distinct from r587–r658 "
        f"(state-mv, Bicep, ARM, SAM, CDKTF, Packer, Nomad, Pulumi ESC, CTS leftover).\n"
    )
