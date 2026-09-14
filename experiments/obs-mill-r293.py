#!/usr/bin/env python3
"""observability-debug-factory mill r293+. Q=2. grok-4.6.

Unique designed service+dashboard+lie. BAN r292 tempo-max-bytes-per-tag-values /
tempo-tagbytes-enable-search-not-cap and r163–r291 clones.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
import importlib.util

_spec = importlib.util.spec_from_file_location(
    "obs_mill_plants_r293", HERE / "obs-mill-plants-r293.py"
)
_plants = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(_plants)
_spec2 = importlib.util.spec_from_file_location(
    "obs_mill_plants_r341", HERE / "obs-mill-plants-r341.py"
)
_plants2 = importlib.util.module_from_spec(_spec2)
assert _spec2.loader is not None
_spec2.loader.exec_module(_plants2)
PAIRS = _plants.PAIRS + _plants2.PAIRS

FACTORY = "observability-debug-factory"
GEN = "grok-4.6"
CATALOG_FIRST = 293
FACTORY_DIR = HERE.parent / "outputs" / "raw" / "2026-08-19-agentic" / FACTORY
BANNED = ("thought", "chain_of_thought", "scratch", "inner_monologue")
DB_PREFIXES = ("Plan:", "Observation:", "Reflection:", "Tool call:")


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


def write_file(n, basis, path, contents, obs, reflection=""):
    return step(n, basis, "write", {"path": path, "contents": contents}, obs, reflection)


KIND_HOST = {
    "tempo": "$TEMPO",
    "loki": "$LOKI",
    "prom": "$PROM",
    "mimir": "$MIMIR",
    "otel": "$PROM",
    "vm": "$VM",
    "thanos": "$THANOS",
    "pyro": "$PYRO",
    "grafana": "$GRAFANA",
    "ch": "$CLICKHOUSE",
    "am": "$AM",
}


def exec_cmd(s: dict, query: str) -> str:
    host = KIND_HOST.get(s["kind"], "$PROM")
    path = s["exec_path"]
    kind = s["kind"]
    if kind in {"tempo"} and path == "/api/search":
        return f"curl -sS -G {host}/api/search --data-urlencode 'q={query}' | jq '{{n:(.traces|length),error}}'"
    if kind == "loki":
        return (
            f"curl -sS -G {host}{path} --data-urlencode 'query={query}' "
            f"--data-urlencode 'limit=30' --data-urlencode 'start=-15m'"
        )
    if kind == "pyro":
        return f"curl -sS -G {host}{path} --data-urlencode 'query={query}' | jq '.flamebearer.names|length'"
    if kind == "ch":
        return f"clickhouse-client -q {query!r}"
    if kind == "grafana" and path == "/api/ds/query":
        return f"curl -sS {host}/api/ds/query -d @/tmp/{s['dash']}.json | jq '.message // .results.A'"
    if kind == "am":
        return f"curl -sS {host}{path} | jq 'length'"
    if kind == "grafana" and "alertmanager" in path:
        return f"curl -sS {host}{path} | jq 'length'"
    return f"curl -sS -G {host}{path} --data-urlencode 'query={query}'"


def success_episode(rnd: int, s: dict) -> dict:
    svc, dash, path = s["svc"], s["dash"], s["file"]
    q = s["query"]
    ns, deploy = s["ns"], s["deploy"]
    steps = [
        bash(
            1,
            f"Plan: find Grafana dashboard {dash} for {svc} before chasing {s['false_lead']}.",
            f"curl -sS $GRAFANA/api/search?query={dash} | jq -c '.[]|{{uid,title}}'",
            f'[{{"uid":"{dash}","title":"{s["panel"]}"}}]',
            "Dashboard exists. Read panel JSON.",
        ),
        bash(
            2,
            f"Observation: dashboard {dash} exists (step 1). Read panel JSON.",
            f"curl -sS $GRAFANA/api/dashboards/uid/{dash} | jq '.dashboard.panels[0]|{{title,targets}}'",
            f'{{"title":"{s["panel"]}","targets":[{{"expr":"{q}"}}]}}',
            "Panel query known. Execute it.",
        ),
        bash(
            3,
            f"Observation: panel '{s['panel']}' runs {q} (step 2). Execute it.",
            exec_cmd(s, q),
            s["exec_obs"],
            f"Empty/wrong: {s['exec_err']}. False lead next.",
        ),
        bash(
            4,
            f"Observation: query empty/wrong (step 3). False lead: {s['false_lead']}.",
            f"yq '{s['false_yq']}' {s['false_file']}",
            s["false_obs"],
            "False lead looks healthy. Read it.",
        ),
        read(
            5,
            f"Observation: {s['false_lead']} looks healthy (step 4). Read {s['false_file']}.",
            s["false_file"],
            s["false_read"],
            "False lead is not the ticket. Read primary config.",
        ),
        read(
            6,
            f"Observation: primary false lead does not explain the empty panel (step 5). Read {path}.",
            path,
            s["fail_line"],
            "Lie candidate in primary config.",
        ),
        bash(
            7,
            f"Observation: lie candidate in {path} (step 6). Query truth source vs dashboard.",
            s["truth_cmd"],
            s["truth_obs"],
            "Truth source has the missing data.",
        ),
        bash(
            8,
            f"Observation: truth source has data (step 7). Confirm mechanism {s['lie']}.",
            f"yq '{s['yq']}' {path}",
            s["confirm_obs"],
            "Cap/flag confirmed as the lie.",
        ),
        edit(
            9,
            f"Reflection: plan change — RCA is {s['lie']}, not {s['false_lead']}. Patch {path}.",
            path,
            s["fail_line"],
            s["fix_line"],
            f"patched {s['yq'].split('.')[-1]} {s['fix_val']}",
            "Reload.",
        ),
        bash(
            10,
            f"Observation: patched {path} (step 9). Reload {ns}-{deploy}.",
            f"kubectl -n {ns} rollout restart deploy/{deploy} && kubectl -n {ns} rollout status deploy/{deploy} --timeout=90s",
            f'deployment "{deploy}" successfully rolled out',
            "Reloaded. Re-query.",
        ),
        bash(
            11,
            f"Observation: {ns}-{deploy} reloaded (step 10). Re-run {q}.",
            exec_cmd(s, q),
            s["exec_ok"],
            "Backend now returns data.",
        ),
        bash(
            12,
            f"Observation: backend now returns series (step 11). Refresh Grafana panel {s['panel']}.",
            f"curl -sS $GRAFANA/api/ds/query -d @/tmp/{dash}.json | jq '.results.A.frames[0].schema // .results.A'",
            s["grafana_obs"],
            "Panel populated.",
        ),
        bash(
            13,
            f"Observation: panel populated (step 12). Check side-effect {s['side_svc']} still works.",
            f"curl -sS $GRAFANA/api/search?query={s['side_svc']} | jq 'length'",
            s["side_obs"],
            "Side-effect ok.",
        ),
        write_file(
            14,
            f"Observation: side-effect {s['side_svc']} ok (step 13). Write runbook for {svc}.",
            f"runbooks/{dash}.md",
            f"# {svc} {s['slug']}\n{s['fail_line']} was the lie. Fix {s['fix_line']}. Not {s['false_lead']}.\n",
            f"wrote runbooks/{dash}.md",
            "Runbook written.",
        ),
        bash(
            15,
            f"Observation: runbook written (step 14). Final verify dashboard {dash}.",
            f"yq '{s['yq']}' {path}",
            f"{s['fix_val']}\n",
            "Done.",
        ),
    ]
    if len(steps) != 15:
        raise SystemExit(f"{s['slug']} steps {len(steps)}")
    return {
        "id": f"obs-r{rnd}-{s['slug']}",
        "goal": f"{svc} dashboard {dash} {s['panel']} empty/wrong. Find the lie.",
        "plan": f"Empty → {s['false_lead']} (false) → {s['fail_val']} → {s['fix_val']}.",
        "steps": steps,
        "outcome": f"{s['yq'].split('.')[-1]} {s['fix_val']}. Panel populated. {s['side_svc']} unchanged.",
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
    ns, deploy = s["ns"], s["deploy"]
    ticket = f"OBS-{5400 + rnd}"
    xmod = dash.replace("-", "_")
    steps = [
        bash(
            1,
            f"Plan: debug empty {dash} for {svc}; start at {s['false_lead']}.",
            f"curl -sS $GRAFANA/api/search?query={dash} | jq -c '.[]|{{uid,title}}'",
            f'[{{"uid":"{dash}","title":"{s["lpanel"]}"}}]',
            "Dashboard exists.",
        ),
        bash(
            2,
            f"Observation: dashboard {dash} found (step 1). Read panel JSON.",
            f"curl -sS $GRAFANA/api/dashboards/uid/{dash} | jq '.dashboard.panels[0]'",
            f'{{"title":"{s["lpanel"]}","targets":[{{"expr":"{q}"}}]}}',
            "Query known.",
        ),
        bash(
            3,
            f"Observation: panel '{s['lpanel']}' query {q} (step 2). Execute it.",
            exec_cmd(s, q),
            s["exec_obs"],
            "Still empty.",
        ),
        bash(
            4,
            f"Observation: empty (step 3). Treat {s['false_lead']} as RCA.",
            f"yq '{s['false_yq']}' {s['lfalse_file']}",
            s["false_obs"].split("#")[0].strip() + "  # treated as leftover",
            "False lead still looks plausible.",
        ),
        read(
            5,
            f"Observation: {s['false_lead']} still looks plausible (step 4). Read {s['lfalse_file']}.",
            s["lfalse_file"],
            f"treated as {s['false_lead']}",
            "Skip primary config.",
        ),
        read(
            6,
            f"Observation: {s['lfalse_file']} matches the false lead (step 5). Skip {path}.",
            s["lfalse_file"],
            s["lfalse_file"],
            "Patch the hide.",
        ),
        edit(
            7,
            f"Observation: {s['lfalse_file']} looks like a knob (step 6). Patch it.",
            s["lfalse_file"],
            s["false_old"],
            s["false_new"],
            s["false_patch"],
            "Reload.",
        ),
        bash(
            8,
            f"Observation: wrong patch applied (step 7). Reload {ns}-{deploy}.",
            f"kubectl -n {ns} rollout restart deploy/{deploy} && kubectl -n {ns} rollout status deploy/{deploy} --timeout=90s",
            f'deployment "{deploy}" successfully rolled out',
            "Reloaded. Re-query.",
        ),
        bash(
            9,
            f"Observation: reloaded (step 8). Re-query {q}.",
            exec_cmd(s, q),
            s["exec_obs"],
            "Still empty after hide.",
        ),
        edit(
            10,
            f"Observation: still empty (step 9). Double down on {s['false_lead']}.",
            s["lfalse_file"],
            s["false2_old"],
            s["false2_new"],
            s["false2_patch"],
            "Second wrong patch.",
        ),
        bash(
            11,
            "Observation: second wrong patch (step 10). Re-query again.",
            exec_cmd(s, q),
            s["exec_obs"],
            "Still empty.",
        ),
        read(
            12,
            f"Observation: still empty (step 11). Late read of {path}.",
            path,
            f"{path} {s['fail_line']}; truth still {s['truth_obs']}",
            "Actual lie found late.",
        ),
        bash(
            13,
            f"Observation: actual lie is {s['llie']} (step 12). Attempt the correct patch.",
            f"kubectl -n {ns} auth can-i patch configmap/{dash} --as=sre-bot",
            "no",
            "No RBAC for the real fix.",
        ),
        write_file(
            14,
            f"Observation: cannot apply correct patch (step 13). Open handoff {ticket}.",
            f"tickets/{ticket}.md",
            f"{ticket}: {svc} still empty. {s['false_lead']} leftover. {s['llie']}. Need {s['fix_val']}. No RBAC.\n",
            f"wrote tickets/{ticket}.md",
            "Handoff recorded.",
        ),
        bash(
            15,
            f"Observation: handoff filed (step 14). Mark tests/test_{xmod}.py and stop.",
            f"printf '%s\\n' '@pytest.mark.xfail(reason=\"{ticket}\")\\ndef test_{s['lslug'].replace('-', '_')}():\\n    assert False' > tests/test_{xmod}.py",
            f"xfail tests/test_{xmod}.py",
            "PARTIAL. Stop.",
        ),
    ]
    if len(steps) != 15:
        raise SystemExit(f"{s['lslug']} steps {len(steps)}")
    return {
        "id": f"obs-r{rnd}-{s['lslug']}",
        "goal": f"{svc} dashboard {dash} {s['lpanel']} empty. Restore data.",
        "plan": f"Apply {s['false_lead']} leftover. Handoff real lie.",
        "steps": steps,
        "outcome": f"{s['false_lead']} applied; still empty. Late {s['fail_line']}. Handoff {ticket}.",
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
        f"Unique service+dashboard+lie. Surfaces: {s['new_vs']}.\n"
        f"Avoided r292 tempo-max-bytes-per-tag-values / tempo-tagbytes-enable-search-not-cap "
        f"and r163–r291 clones.\n\n"
        f"| id | service | dashboard | lie | terminal |\n"
        f"|---|---|---|---|---|\n"
        f"| {a['id']} | {s['svc']} | {s['dash']} | {s['lie']} | success |\n"
        f"| {b['id']} | {s['lsvc']} | {s['ldash']} | {s['llie']} | handoff/xfail |\n\n"
        f"## Step counts\n"
        f"- ep1: 15. False lead {s['false_lead']} 4-5; {s['fail_val']} 6-8; {s['fix_val']} 9-12.\n"
        f"- ep2: 15. hide 6-10; still empty 11; late {s['fail_line']} 12; handoff 14-15.\n\n"
        f"## decision_basis audit\n"
        f"Every step starts Plan:/Observation:/Reflection:/Tool call:.\n"
        f"No thought / chain_of_thought / scratch / inner_monologue. No spike_events.\n"
        f"No sim_or_real: real. Invented plant `designed`.\n"
    )


def used_catalog() -> tuple[set[str], set[str], set[str]]:
    svcs, dashes, slugs = set(), set(), set()
    if not FACTORY_DIR.is_dir():
        return svcs, dashes, slugs
    for notes in FACTORY_DIR.glob("NOTES-r*.md"):
        for line in notes.read_text().splitlines():
            if not line.startswith("| obs-r"):
                continue
            parts = [x.strip() for x in line.strip("|").split("|")]
            slugs.add(parts[0])
            if len(parts) > 1:
                svcs.add(parts[1])
            if len(parts) > 2:
                dashes.add(parts[2])
    return svcs, dashes, slugs


def assert_unique(s: dict) -> None:
    svcs, dashes, slugs = used_catalog()
    collisions = []
    for slug in (s["slug"], s["lslug"]):
        for old in slugs:
            if old.endswith("-" + slug):
                collisions.append(old)
    for name in (s["svc"], s["lsvc"]):
        if name in svcs:
            collisions.append(f"svc:{name}")
    for name in (s["dash"], s["ldash"]):
        if name in dashes:
            collisions.append(f"dash:{name}")
    if collisions:
        raise SystemExit(f"uniqueness collision: {collisions}")


def assert_clean(obj) -> None:
    if isinstance(obj, dict):
        for key, val in obj.items():
            if key in BANNED:
                raise SystemExit(f"banned key {key}")
            if key == "sim_or_real" and val == "real":
                raise SystemExit("sim_or_real real")
            if key == "spike_events":
                raise SystemExit("spike_events")
            assert_clean(val)
    elif isinstance(obj, list):
        for item in obj:
            assert_clean(item)


def write_round(rnd: int, staging: Path) -> None:
    idx = rnd - CATALOG_FIRST
    if idx < 0 or idx >= len(PAIRS):
        raise SystemExit(f"no catalog pair for r{rnd}")
    spec = PAIRS[idx]
    assert_unique(spec)
    a = success_episode(rnd, spec)
    b = leftover_episode(rnd, spec)
    for rec in (a, b):
        assert_clean(rec)
        blob = json.dumps(rec)
        if '"sim_or_real": "real"' in blob or "spike_events" in blob:
            raise SystemExit("banned field")
        for st in rec["steps"]:
            if any(k in st for k in BANNED):
                raise SystemExit("hidden CoT")
            if not st["decision_basis"].startswith(DB_PREFIXES):
                raise SystemExit(f"bad prefix {st['decision_basis']!r}")
    batch = staging / f"batch-r{rnd:02d}.jsonl"
    notes = staging / f"NOTES-r{rnd:02d}.md"
    batch.write_text(json.dumps(a, separators=(",", ":")) + "\n" + json.dumps(b, separators=(",", ":")) + "\n")
    notes.write_text(notes_for(rnd, spec, a, b))
    print(json.dumps({"round": rnd, "ids": [a["id"], b["id"]], "steps": [15, 15], "novel": spec["novel"]}))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--round", type=int, required=True)
    ap.add_argument("--staging", required=True)
    args = ap.parse_args()
    write_round(args.round, Path(args.staging))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
