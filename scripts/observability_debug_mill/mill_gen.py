#!/usr/bin/env python3
"""Emit observability-debug episodes (15-step success + 15-step fail/handoff)."""

from __future__ import annotations

import json
from typing import Any

FACTORY = "observability-debug-factory"
GENERATOR = "grok-4.6"
BANNED_KEYS = ("thought", "chain_of_thought", "scratch", "inner_monologue")
DB_PREFIXES = ("Plan:", "Observation:", "Reflection:", "Tool call:")


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


def build_success(round_n: int, p: dict) -> dict:
    eid = f"obs-r{round_n}-{p['slug']}"
    dash = p["dashboard_uid"]
    svc = p["service"]
    steps = [
        _step(
            1,
            f"Plan: find Grafana dashboard {dash} for {svc} before chasing {p['false_lead']}.",
            _bash(p["search_cmd"]),
            p["obs1"],
        ),
        _step(
            2,
            f"Observation: dashboard {dash} exists (step 1). Read panel JSON.",
            _bash(p["dash_cmd"]),
            p["obs2"],
        ),
        _step(
            3,
            f"Observation: panel '{p['panel']}' runs {p['query']} (step 2). Execute the telemetry metric query.",
            _bash(p["query_cmd"]),
            p["obs3"],
        ),
        _step(
            4,
            f"Observation: query empty/wrong (step 3). False lead: {p['false_lead']}.",
            _bash(p["false_cmd"]),
            p["obs4"],
        ),
        _step(
            5,
            f"Observation: {p['false_lead']} looks healthy (step 4). Read {p['config_path']}.",
            _read(p["config_path"]),
            p["obs5"],
        ),
        _step(
            6,
            f"Observation: primary config does not explain the empty panel (step 5). Read {p['lie_path']}.",
            _read(p["lie_path"]),
            p["obs6"],
        ),
        _step(
            7,
            f"Observation: lie candidate in {p['lie_path']} (step 6). Query truth source {p['truth_name']}.",
            _bash(p["truth_cmd"]),
            p["obs7"],
        ),
        _step(
            8,
            f"Observation: {p['truth_name']} has the missing data (step 7). Confirm mechanism {p['lie']}.",
            _bash(p["confirm_cmd"]),
            p["obs8"],
        ),
        _step(
            9,
            f"Reflection: plan change — RCA is {p['lie']}, not {p['false_lead']}. Repair/fix {p['lie_path']}.",
            _edit(p["lie_path"], p["patch_old"], p["patch_new"]),
            p["obs9"],
        ),
        _step(
            10,
            f"Observation: patched {p['lie_path']} (step 9). Reload {p['reload_name']}.",
            _bash(p["reload_cmd"]),
            p["obs10"],
        ),
        _step(
            11,
            f"Observation: {p['reload_name']} reloaded (step 10). Re-run {p['query']}.",
            _bash(p["requery_cmd"]),
            p["obs11"],
        ),
        _step(
            12,
            f"Observation: backend now returns series (step 11). Refresh Grafana panel {p['panel']}.",
            _bash(p["grafana_ok_cmd"]),
            p["obs12"],
        ),
        _step(
            13,
            f"Observation: panel populated (step 12). Check side effect {p['side']}.",
            _bash(p["side_cmd"]),
            p["obs13"],
        ),
        _step(
            14,
            f"Observation: {p['side']} ok (step 13). Write runbook for {svc}.",
            _write(p["runbook_path"], p["runbook"]),
            p["obs14"],
        ),
        _step(
            15,
            f"Observation: runbook written (step 14). Final verify dashboard {dash}.",
            _bash(p["final_cmd"]),
            p["obs15"],
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
            "cost_steps": 15,
            "handoff": 0,
        },
        "meta": {
            "factory": FACTORY,
            "round": round_n,
            "generator": GENERATOR,
            "kind": "designed",
            "service": svc,
            "dashboard": dash,
            "lie": p["lie"],
        },
    }
    assert_clean(ep)
    if len(steps) != 15:
        raise ValueError(f"{eid} expected 15 steps")
    return ep


def build_fail(round_n: int, p: dict) -> dict:
    eid = f"obs-r{round_n}-{p['slug']}"
    dash = p["dashboard_uid"]
    svc = p["service"]
    steps = [
        _step(
            1,
            f"Plan: debug empty {dash} for {svc}; start at {p['false_lead']}.",
            _bash(p["search_cmd"]),
            p["obs1"],
        ),
        _step(
            2,
            f"Observation: dashboard {dash} found (step 1). Read panel JSON.",
            _bash(p["dash_cmd"]),
            p["obs2"],
        ),
        _step(
            3,
            f"Observation: panel '{p['panel']}' query {p['query']} (step 2). Execute the telemetry metric query.",
            _bash(p["query_cmd"]),
            p["obs3"],
        ),
        _step(
            4,
            f"Observation: empty (step 3). Treat {p['false_lead']} as RCA.",
            _bash(p["false_cmd"]),
            p["obs4"],
        ),
        _step(
            5,
            f"Observation: {p['false_lead']} still looks plausible (step 4). Read {p['config_path']}.",
            _read(p["config_path"]),
            p["obs5"],
        ),
        _step(
            6,
            f"Observation: {p['config_path']} matches the false lead (step 5). Skip {p['lie_path']}.",
            _read(p["wrong_path"]),
            p["obs6"],
        ),
        _step(
            7,
            f"Observation: {p['wrong_path']} looks like a knob (step 6). Patch it.",
            _edit(p["wrong_path"], p["wrong_old"], p["wrong_new"]),
            p["obs7"],
        ),
        _step(
            8,
            f"Observation: wrong patch applied (step 7). Reload {p['reload_name']}.",
            _bash(p["reload_cmd"]),
            p["obs8"],
        ),
        _step(
            9,
            f"Observation: reloaded (step 8). Re-query {p['query']}.",
            _bash(p["requery_cmd"]),
            p["obs9"],
        ),
        _step(
            10,
            f"Observation: still empty (step 9). Double down on {p['false_lead']}.",
            _edit(p["wrong_path"], p["wrong2_old"], p["wrong2_new"]),
            p["obs10"],
        ),
        _step(
            11,
            f"Observation: second wrong patch (step 10). Re-query again.",
            _bash(p["requery_cmd"]),
            p["obs11"],
        ),
        _step(
            12,
            f"Observation: still empty (step 11). Late read of {p['lie_path']}.",
            _read(p["lie_path"]),
            p["obs12"],
        ),
        _step(
            13,
            f"Observation: actual lie is {p['lie']} (step 12). Attempt the correct patch.",
            _bash(p["denied_cmd"]),
            p["obs13"],
        ),
        _step(
            14,
            f"Observation: cannot apply correct patch (step 13). Open handoff {p['ticket']}.",
            _write(p["ticket_path"], p["ticket_body"]),
            p["obs14"],
        ),
        _step(
            15,
            f"Observation: handoff filed (step 14). Mark {p['xfail']} and stop; verification did not pass.",
            _bash(p["xfail_cmd"]),
            p["obs15"],
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
            "cost_steps": 15,
            "handoff": 1,
            "xfailed": 1,
        },
        "meta": {
            "factory": FACTORY,
            "round": round_n,
            "generator": GENERATOR,
            "kind": "designed",
            "service": svc,
            "dashboard": dash,
            "lie": p["lie"],
        },
    }
    assert_clean(ep)
    if len(steps) != 15:
        raise ValueError(f"{eid} expected 15 steps")
    return ep


def notes_md(round_n: int, ok: dict, bad: dict, coverage: int) -> str:
    return (
        f"# NOTES-r{round_n:02d} observability-debug-factory\n\n"
        f"Novel coverage: {coverage}%\n\n"
        "Two designed episodes (quota 2), 15 steps each, success + fail/handoff.\n"
        f"Unique service+dashboard+lie. Surfaces: {ok['surfaces']} vs {bad['surfaces']}.\n"
        f"Avoided {ok['avoided']}. This is {ok['this_is']}.\n\n"
        "| id | service | dashboard | lie | terminal |\n"
        "|---|---|---|---|---|\n"
        f"| obs-r{round_n}-{ok['slug']} | {ok['service']} | {ok['dashboard_uid']} | {ok['lie']} | success |\n"
        f"| obs-r{round_n}-{bad['slug']} | {bad['service']} | {bad['dashboard_uid']} | {bad['lie']} | handoff/xfail |\n\n"
        "## Step counts\n"
        f"- ep1: 15. {ok['step_note']}\n"
        f"- ep2: 15. {bad['step_note']}\n\n"
        "## decision_basis audit\n"
        "Every step starts Plan:/Observation:/Reflection:/Tool call:.\n"
        "No thought / chain_of_thought / scratch / inner_monologue. No spike_events.\n"
        "No sim_or_real: real. Invented plant `designed`.\n\n"
        "## Ban (do not clone r109–r190)\n"
        "Prom remote_write queue, Grafana unified+legacy dual-eval, Tempo metrics-generator "
        "missing dim, Loki SM allowlist, OTel tail decision_wait, Pyroscope eBPF+Java pprof mix, "
        "AM inhibit, Mimir max_label_names_per_series, Thanos compact overlap, VM dedup interval, "
        "OTTL truncate_all, provisioned dashboard uid collision, TSDB retention.size vs time, "
        "godeltaprof+heap double count, Loki line_format drop, tailsampling cache eviction, "
        "Grafana SQL expr stale uid. Also r159–r190: IRM vs AM, Prom agent vs server, "
        "VictoriaLogs vs Loki, Sentry vs Tempo, DD tid/inferred/UST, native vs classic hist, "
        "Grafana Incident vs IRM, ClickHouse SQL vs Tempo table, Faro session, Beyla+javaagent, "
        "NR spanId, Elastic txn.name, Refinery dynsample, Jaeger empty cassandra, Adaptive Metrics, "
        "Alloy relabel, Loki bloom/pattern, k8sattributes overwrite, Tempo MG filter, "
        "pyro max_profile_size/musl, IRM heartbeat, OTel routing/connector names.\n\n"
        "## Weaknesses / next\n"
        f"{bad['next_note']}\n"
    )


def validate_pair(ok_ep: dict, bad_ep: dict, round_n: int) -> None:
    if ok_ep["reward"]["success"] is not True:
        raise ValueError("first episode must succeed")
    if bad_ep["reward"]["success"] is not False:
        raise ValueError("second episode must fail/handoff")
    if len(ok_ep["steps"]) != 15 or len(bad_ep["steps"]) != 15:
        raise ValueError("shape must be 15-step success + 15-step fail")
    if ok_ep["meta"]["round"] != round_n or bad_ep["meta"]["round"] != round_n:
        raise ValueError("meta.round mismatch")
    if ok_ep["meta"]["generator"] != GENERATOR:
        raise ValueError("generator")
    if ok_ep["id"] == bad_ep["id"]:
        raise ValueError("duplicate ids in pair")
    if ok_ep["meta"]["service"] == bad_ep["meta"]["service"]:
        raise ValueError("services must be unique in pair")
    if ok_ep["meta"]["dashboard"] == bad_ep["meta"]["dashboard"]:
        raise ValueError("dashboards must be unique in pair")
    for ep in (ok_ep, bad_ep):
        for step in ep["steps"]:
            db = step["decision_basis"]
            if not db.startswith(DB_PREFIXES):
                raise ValueError(f"{ep['id']} step {step['n']} bad decision_basis")
            if not step["observation"].strip():
                raise ValueError(f"{ep['id']} empty observation")
        assert_clean(ep)
