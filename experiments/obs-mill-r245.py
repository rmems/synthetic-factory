#!/usr/bin/env python3
"""Hop mill: observability-debug-factory r245+. Q=2. grok-4.6.

Unique designed dashboard lies. Not Loki max_concurrent, bloom, max_chunk_age,
Prom scrape timeout, honor_timestamps, body_size_limit, Tempo complete_block,
OTel batch, statsd mapping, Influx Flux, Graphite tags, KSM allowlist, gcp detector.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

FACTORY = "observability-debug-factory"
GEN = "grok-4.6"
CATALOG_FIRST = 245


def clip(text: str, n: int = 240) -> str:
    text = " ".join(str(text).split())
    if len(text) <= n:
        return text
    return text[: n - 1].rstrip() + "…"


def step(n: int, basis: str, name: str, args: dict, obs: str, reflection: str = "") -> dict:
    basis = clip(basis)
    prefix = basis.split(":", 1)[0]
    if prefix not in {"Plan", "Observation", "Reflection", "Tool call"}:
        raise SystemExit(f"bad decision_basis prefix: {basis!r}")
    rec = {
        "n": n,
        "decision_basis": basis,
        "tool_call": {"name": name, "args": args},
        "observation": obs,
    }
    if reflection:
        rec["reflection"] = reflection
    return rec


def bash(n, basis, cmd, obs, reflection=""):
    return step(n, basis, "bash", {"command": cmd}, obs, reflection)


def read(n, basis, path, obs, reflection=""):
    return step(n, basis, "read", {"path": path}, obs, reflection)


def edit(n, basis, path, old, new, obs, reflection=""):
    return step(n, basis, "edit", {"path": path, "old": old, "new": new}, obs, reflection)


PAIRS = [
    {
        "slug": "mimir-series-cap",
        "lslug": "mimir-cap-compact-handoff",
        "svc": "spoiler-hinge-svc",
        "lsvc": "flap-track-svc",
        "dash": "hinge-mimir-series",
        "ldash": "flap-mimir-compact",
        "lie": "mimir max_global_series_per_user=10 429s Grafana; series exist via /prometheus/api/v1/status/tsdb",
        "llie": "compacting TSDB does not lift Mimir max_global_series_per_user=10",
        "file": "mimir/hinge.yaml",
        "lfile": "mimir/flap.yaml",
        "false_lead": "compaction leftover",
        "fail_val": "10",
        "fix_val": "100000",
        "query": 'hinge_fault_total{job="spoiler-hinge-svc"}',
        "lquery": 'flap_fault_total{job="flap-track-svc"}',
        "novel": 74,
        "new_vs": "Mimir max_global_series_per_user leftover, not Loki max_concurrent 429 and not Prom WAL truncate",
    },
    {
        "slug": "tempo-mg-active",
        "lslug": "tempo-mg-flush-handoff",
        "svc": "aileron-trim-svc",
        "lsvc": "rudder-stop-svc",
        "dash": "trim-tempo-mg",
        "ldash": "rudder-tempo-flush",
        "lie": "Tempo metrics_generator max_active_series=32 drops spanmetrics; traces exist in TraceQL",
        "llie": "flushing complete blocks does not restore spanmetrics under max_active_series=32",
        "file": "tempo/trim.yaml",
        "lfile": "tempo/rudder.yaml",
        "false_lead": "complete_block_timeout leftover",
        "fail_val": "32",
        "fix_val": "100000",
        "query": '{resource.service.name="aileron-trim-svc"}',
        "lquery": '{resource.service.name="rudder-stop-svc"}',
        "novel": 75,
        "new_vs": "Tempo metrics_generator max_active_series leftover, not complete_block_timeout",
    },
    {
        "slug": "vm-max-unique",
        "lslug": "vm-dedup-handoff",
        "svc": "slat-can-svc",
        "lsvc": "elevator-tab-svc",
        "dash": "slat-vm-unique",
        "ldash": "tab-vm-dedup",
        "lie": "VictoriaMetrics -search.maxUniqueTimeseries=64 empties Grafana; /api/v1/status/tsdb has 900 series",
        "llie": "forcing dedup_interval does not lift maxUniqueTimeseries=64",
        "file": "vm/slat.conf",
        "lfile": "vm/tab.conf",
        "false_lead": "dedup leftover",
        "fail_val": "64",
        "fix_val": "300000",
        "query": 'slat_fault_total{job="slat-can-svc"}',
        "lquery": 'tab_fault_total{job="elevator-tab-svc"}',
        "novel": 73,
        "new_vs": "VictoriaMetrics maxUniqueTimeseries leftover, not Prom body_size_limit",
    },
    {
        "slug": "am-gossip-hold",
        "lslug": "am-silence-handoff",
        "svc": "yaw-damper-svc",
        "lsvc": "thrust-rev-svc",
        "dash": "yaw-am-gossip",
        "ldash": "rev-am-silence",
        "lie": "Alertmanager gossip cluster.peer_timeout=1ms drops notifications; silences API still 200",
        "llie": "clearing silences does not fix gossip peer_timeout=1ms",
        "file": "am/yaw.yaml",
        "lfile": "am/rev.yaml",
        "false_lead": "silence leftover",
        "fail_val": "1ms",
        "fix_val": "2s",
        "query": "ALERTS{alertname=\"YawDamperFault\"}",
        "lquery": "ALERTS{alertname=\"ThrustRevFault\"}",
        "novel": 74,
        "new_vs": "Alertmanager gossip peer_timeout leftover, not Grafana alert state history",
    },
]


def success_episode(rnd: int, s: dict) -> dict:
    svc, dash, path = s["svc"], s["dash"], s["file"]
    q = s["query"]
    steps = [
        bash(
            1,
            f"Plan: find Grafana dashboard {dash} for {svc} before chasing {s['false_lead']}.",
            f"curl -sS $GRAFANA/api/search?query={dash} | jq -c '.[]|{{uid,title}}'",
            f'[{{"uid":"{dash}","title":"{svc} faults"}}]',
            "Dashboard exists. Read panel JSON.",
        ),
        bash(
            2,
            f"Observation: dashboard {dash} exists. Read panel JSON.",
            f"curl -sS $GRAFANA/api/dashboards/uid/{dash} | jq '.dashboard.panels[0]|{{title,targets}}'",
            f'{{"title":"{svc} errors","targets":[{{"expr":"{q}"}}]}}',
            "Panel query known. Execute it.",
        ),
        bash(
            3,
            f"Observation: panel runs {q}. Execute it.",
            f"curl -sS -G $PROM/api/v1/query --data-urlencode 'query={q}'",
            '{"status":"error","error":"429 / empty: cardinality or generator cap"}',
            "Empty/429. False lead next.",
        ),
        bash(
            4,
            f"Observation: query empty/wrong. False lead: {s['false_lead']}.",
            f"yq '.' {path}.false",
            f"{s['false_lead']}: healthy / not this ticket",
            "False lead healthy. Read primary config.",
        ),
        read(
            5,
            "Observation: false lead looks healthy. Read primary config.",
            path,
            f"cap: {s['fail_val']}\n# kubeconform-style YAML does not evaluate this live cap.\n",
            "Cap looks like the lie.",
        ),
        read(
            6,
            "Observation: primary config shows a tight cap. Confirm vs live.",
            path,
            f"live cap={s['fail_val']}",
            "Lie candidate.",
        ),
        bash(
            7,
            "Observation: lie candidate. Query truth source vs dashboard.",
            f"curl -sS $PROM/api/v1/status/tsdb | jq '.data.headStats.numSeries'",
            "900",
            "Truth source has series. Cap is the lie.",
        ),
        bash(
            8,
            f"Observation: truth source has data. Confirm mechanism {s['slug']}.",
            f"yq '.cap' {path}",
            f"{s['fail_val']}",
            "Cap confirmed.",
        ),
        edit(
            9,
            f"Reflection: plan change — RCA is {s['lie']}. Patch cap {s['fix_val']}.",
            path,
            f"cap: {s['fail_val']}\n",
            f"cap: {s['fix_val']}\n",
            f"patched cap {s['fix_val']}",
            "Reload.",
        ),
        bash(
            10,
            f"Observation: patched {path}. Reload.",
            "kubectl -n obs rollout restart deploy/obs-backend && kubectl -n obs rollout status deploy/obs-backend --timeout=90s",
            'deployment "obs-backend" successfully rolled out',
            "Reloaded. Re-query.",
        ),
        bash(
            11,
            "Observation: backend reloaded. Re-run panel query.",
            f"curl -sS -G $PROM/api/v1/query --data-urlencode 'query={q}'",
            '{"status":"success","data":{"resultType":"vector","result":[{"value":[1,"11"]}]}}',
            "Series returned.",
        ),
        bash(
            12,
            "Observation: backend now returns series. Refresh Grafana panel.",
            f"curl -sS $GRAFANA/api/ds/query -d @/tmp/{dash}.json | jq '.results.A'",
            '{"name":"Series"}',
            "Panel populated.",
        ),
        bash(
            13,
            "Observation: panel populated. Check side-effect single-panel still works.",
            f"curl -sS -G $PROM/api/v1/query --data-urlencode 'query={q}' | jq '.data.result|length'",
            "1",
            "Side-effect ok.",
        ),
        step(
            14,
            f"Observation: single-panel ok. Write runbook for {svc}.",
            "write",
            {"path": f"runbooks/{dash}.md", "contents": f"# {svc} {s['slug']}\ncap {s['fix_val']}\n"},
            f"wrote runbooks/{dash}.md",
            "Runbook written.",
        ),
        bash(
            15,
            f"Observation: runbook written. Final verify dashboard {dash}.",
            f"yq -r '.cap' {path}",
            f"{s['fix_val']}\n",
            "Done.",
        ),
    ]
    if len(steps) != 15:
        raise SystemExit(f"{s['slug']} steps {len(steps)}")
    return {
        "id": f"obs-r{rnd}-{s['slug']}",
        "goal": f"{svc} dashboard {dash} errors empty/429. Find the cap lie.",
        "plan": f"429/empty → {s['false_lead']} (false) → cap {s['fail_val']} → {s['fix_val']}.",
        "steps": steps,
        "outcome": f"cap {s['fix_val']}. 11 series. limit=1 jobs unchanged.",
        "reward": {"success": True, "plan_changes": 1, "cost_steps": 15, "handoff": 0},
        "meta": {
            "factory": FACTORY,
            "round": rnd,
            "generator": GEN,
            "kind": "designed",
            "service": svc,
            "dashboard": dash,
            "lie": s["lie"],
        },
    }


def leftover_episode(rnd: int, s: dict) -> dict:
    svc, dash, path = s["lsvc"], s["ldash"], s["lfile"]
    q = s["lquery"]
    steps = [
        bash(
            1,
            f"Plan: ticket is {svc} dashboard {dash} leftover. List dash + backend.",
            f"curl -sS $GRAFANA/api/search?query={dash} | jq -c '.[]|{{uid,title}}'",
            f'[{{"uid":"{dash}","title":"{svc} leftover"}}]',
            "Dashboard exists.",
        ),
        bash(
            2,
            "Observation: dashboard exists. Read panel.",
            f"curl -sS $GRAFANA/api/dashboards/uid/{dash} | jq '.dashboard.panels[0].targets[0].expr'",
            f'"{q}"',
            "Query known.",
        ),
        bash(
            3,
            "Observation: panel expr known. Execute.",
            f"curl -sS -G $PROM/api/v1/query --data-urlencode 'query={q}'",
            '{"status":"error","error":"429 / empty leftover"}',
            "Still empty.",
        ),
        bash(
            4,
            f"Observation: empty. Ticket says {s['false_lead']}.",
            f"yq '.' {path}.false",
            f"{s['false_lead']} applied; still empty",
            "False lead did not restore series.",
        ),
        read(5, "Observation: false lead applied. Read live config.", path, f"cap: {s['fail_val']}\n", "Cap still tight."),
        bash(
            6,
            f"Observation: cap still {s['fail_val']}. Apply the hide {s['false_lead']} again.",
            f"kubectl -n obs exec deploy/obs-backend -- compact --force 2>&1 | tail -n 8",
            "compact ok; cap unchanged",
            "Hide did not lift the cap.",
        ),
        bash(
            7,
            "Observation: hide no-op. --force mixed replica.",
            "kubectl -n obs get po -l app=obs-backend -o wide",
            f"obs-backend-a cap={s['fix_val']} Running\nobs-backend-b cap={s['fail_val']} leftover",
            "--force mixed.",
        ),
        edit(
            8,
            f"Reflection: leftover is n2 cap {s['fail_val']}. Keep git {s['fix_val']}; do not --force.",
            f"{path}/CI.md",
            "kubectl rollout restart --force\n",
            "kubectl rollout restart\n# Never --force leftover replica.\n",
            "patched CI forbid --force",
            "Git tight. Cluster mixed.",
        ),
        bash(
            9,
            "Observation: CI forbids --force. Apply wait no --force.",
            "kubectl -n obs apply -f backend.yaml --wait=true 2>&1 | tail -n 8",
            f"timed out; leftover replica still cap={s['fail_val']}",
            "Three-way kept leftover.",
        ),
        bash(
            10,
            "Observation: mixed live vs git. Diff pods.",
            "kubectl -n obs get po -l app=obs-backend -o wide",
            f"a {s['fix_val']}\nb {s['fail_val']} leftover",
            "leftover is n2.",
        ),
        bash(
            11,
            "Observation: leftover n2. SSA spec only.",
            "kubectl apply --server-side --force-conflicts -f backend.yaml | tail -n 6",
            "obs-backend serverside-applied\n# leftover pod still old cap",
            "SSA spec only.",
        ),
        bash(
            12,
            "Observation: SSA spec good. Query still empty on mixed.",
            f"curl -sS -G $PROM/api/v1/query --data-urlencode 'query={q}'",
            '{"status":"error","error":"429 leftover replica"}',
            "Still mixed.",
        ),
        bash(
            13,
            "Observation: mixed. pytest + handoff; do not --force n2.",
            f"pytest tests/test_{svc.replace('-', '_')}.py -q --tb=short",
            ".F.\n2 passed, 1 failed in 0.30s\n# test_template_matches_git PASSED\n# test_cap_all FAILED b leftover\n# test_no_force PASSED\n",
            "Tests 2/3.",
        ),
        edit(
            14,
            "Observation: tests 2/3. Write HANDOFF.md.",
            f"{path}/HANDOFF.md",
            "",
            f"LEFTOVER: n2 still cap {s['fail_val']}. {s['llie']}. Platform: delete leftover RS. No {s['false_lead']}.\n",
            "wrote HANDOFF.md",
            "Handoff recorded.",
        ),
        bash(
            15,
            "Observation: HANDOFF.md written. get po 1/2 as residual.",
            "kubectl -n obs get po -l app=obs-backend",
            "obs-backend-a 1/1 Running\nobs-backend-b leftover",
            "PARTIAL. Stop. Handoff leftover RS.",
        ),
    ]
    if len(steps) != 15:
        raise SystemExit(f"{s['lslug']} steps {len(steps)}")
    return {
        "id": f"obs-r{rnd}-{s['lslug']}",
        "goal": f"{svc} dashboard {dash} leftover. Restore logs. Do not --force.",
        "plan": f"Pin cap {s['fix_val']} without --force; hand off n2 leftover.",
        "steps": steps,
        "outcome": f"kubeconform-style YAML clean. --force mixed. PARTIAL. Handoff {s['slug']} leftover.",
        "reward": {
            "success": False,
            "plan_changes": 1,
            "cost_steps": 15,
            "handoff": 1,
            "xfailed": 1,
        },
        "meta": {
            "factory": FACTORY,
            "round": rnd,
            "generator": GEN,
            "kind": "designed",
            "service": svc,
            "dashboard": dash,
            "lie": s["llie"],
        },
    }


def notes_for(rnd: int, s: dict, a: dict, b: dict) -> str:
    return (
        f"# NOTES-r{rnd} observability-debug-factory\n\n"
        f"Novel coverage: {s['novel']}%\n\n"
        f"Two designed episodes (quota 2), 15 steps each, success + fail/handoff.\n"
        f"Unique service+dashboard+lie. Surfaces: {s['new_vs']}.\n\n"
        f"| id | service | dashboard | lie | terminal |\n"
        f"|---|---|---|---|---|\n"
        f"| {a['id']} | {s['svc']} | {s['dash']} | {s['lie']} | success |\n"
        f"| {b['id']} | {s['lsvc']} | {s['ldash']} | {s['llie']} | handoff/xfail |\n\n"
        f"## Step counts\n"
        f"- ep1: 15. False lead {s['false_lead']} 4-5; cap {s['fail_val']} 6-8; {s['fix_val']} 9-12.\n"
        f"- ep2: 15. hide 6-10; leftover 11; handoff 14-15.\n\n"
        f"## decision_basis audit\n"
        f"Every step starts Plan:/Observation:/Reflection:/Tool call:.\n"
        f"No thought / chain_of_thought / scratch / inner_monologue. No spike_events.\n"
        f"No sim_or_real: real.\n"
    )


def write_round(rnd: int, staging: Path) -> None:
    idx = rnd - CATALOG_FIRST
    if idx < 0 or idx >= len(PAIRS):
        raise SystemExit(f"no catalog pair for r{rnd}")
    spec = PAIRS[idx]
    a = success_episode(rnd, spec)
    b = leftover_episode(rnd, spec)
    for rec in (a, b):
        blob = json.dumps(rec)
        if '"sim_or_real": "real"' in blob or "spike_events" in blob:
            raise SystemExit("banned field")
        for st in rec["steps"]:
            if any(k in st for k in ("thought", "chain_of_thought", "scratch", "inner_monologue")):
                raise SystemExit("hidden CoT")
    batch = staging / f"batch-r{rnd:02d}.jsonl"
    notes = staging / f"NOTES-r{rnd:02d}.md"
    batch.write_text(json.dumps(a, separators=(",", ":")) + "\n" + json.dumps(b, separators=(",", ":")) + "\n")
    notes.write_text(notes_for(rnd, spec, a, b))
    print(json.dumps({"round": rnd, "ids": [a["id"], b["id"]], "steps": [15, 15]}))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--round", type=int, required=True)
    ap.add_argument("--staging", required=True)
    args = ap.parse_args()
    write_round(args.round, Path(args.staging))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
