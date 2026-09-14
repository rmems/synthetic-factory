#!/usr/bin/env python3
"""Independent fail-closed audit of /tmp/ttf-r13 staging. Does not write outputs/raw/."""
from __future__ import annotations

import hashlib
import json
import math
import os
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path("/home/raulmc/rmems/synthetic-factory")
PIPE = REPO / "pipelines"
sys.path.insert(0, str(PIPE))

from check_records import (  # noqa: E402
    FactoryStaging,
    check_jsonl,
    check_provenance_publish,
    check_record,
    claims_real,
    walk_key,
)
from curate_bridge import raster_status  # noqa: E402
from exact_json import dumps_exact_json  # noqa: E402
from round_txn import validate_novel_coverage  # noqa: E402
from training_audit import hidden_thought_paths, is_hidden_thought_key  # noqa: E402
from validate_run import (  # noqa: E402
    HIDDEN_THOUGHT_KEYS,
    _hidden_thought_paths,
    _staging_hidden_thought_errors,
    check_line,
)
from verify_execution import verify_batch_for_frontier  # noqa: E402

BATCH = Path("/tmp/ttf-r13/batch-r13.jsonl")
NOTES = Path("/tmp/ttf-r13/NOTES-r13.md")
RAW = REPO / "outputs" / "raw"
EXPECTED_IDS = [f"ttf-r13-{n:03d}" for n in range(81, 86)]
HEADS = ("task_progress", "safety", "efficiency", "coherence", "exploration")
AGG = "total = task_progress + safety + efficiency + coherence + exploration"
RIGHTS_KEYS = (
    "provider",
    "model",
    "channel",
    "subscription_plan",
    "generation_surface",
    "generated_at",
    "intended_use",
    "project_training_policy",
    "research_retention_status",
    "research_evaluation_status",
    "redistribution_status",
    "provider_training_status",
    "weight_publication_status",
    "status_basis",
    "linear_issue",
)
RIGHTS_VALUES = {
    "provider": "SpaceXAI/xAI",
    "model": "grok-4.6",
    "channel": "consumer",
    "subscription_plan": "SuperGrok Heavy",
    "generation_surface": "SuperGrok Heavy chat",
    "intended_use": "research_only",
    "project_training_policy": "blocked",
    "research_retention_status": "allowed",
    "research_evaluation_status": "allowed",
    "redistribution_status": "unresolved",
    "provider_training_status": "unresolved",
    "weight_publication_status": "blocked",
    "status_basis": "RM-793 project policy: xAI hosted outputs are research-only",
    "linear_issue": "RM-793",
}
EXTRA_THOUGHT = (
    "thought",
    "thoughts",
    "reasoning",
    "chain_of_thought",
    "hidden_reasoning",
    "inner_monologue",
    "thinking",
    "cot",
    "scratch",
    "internal_reasoning",
)
BANNED_PLANTS = (
    "Marrow-Dock",
    "Vesper-Lattice",
    "Brine-Well",
    "Saddle-Arc",
    "Ashlar-Gait",
)
TOL = 1e-6
out: dict = {"checks": {}, "errors": []}


def rec_id(obj):
    return obj.get("id") or (obj.get("meta") or {}).get("id")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def walk_keys(value, path=""):
    if isinstance(value, dict):
        for k, v in value.items():
            child = f"{path}.{k}" if path else str(k)
            yield child, k, v
            yield from walk_keys(v, child)
    elif isinstance(value, list):
        for i, item in enumerate(value):
            yield from walk_keys(item, f"{path}[{i}]")


def tokenize(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def jaccard(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 0.0
    return len(a & b) / len(a | b)


raw = BATCH.read_bytes()
text = raw.decode("utf-8")
physical_lines = text.split("\n")
records = []
for i, line in enumerate(physical_lines, 1):
    if not line.strip():
        continue
    records.append((i, json.loads(line)))

out["artifacts"] = {
    "batch": str(BATCH),
    "notes": str(NOTES),
    "batch_bytes": BATCH.stat().st_size,
    "notes_bytes": NOTES.stat().st_size,
    "batch_sha256": sha256(BATCH),
    "notes_sha256": sha256(NOTES),
    "n_physical_split": len(physical_lines),
    "n_nonempty": len(records),
    "trailing_lf": raw.endswith(b"\n") and not raw.endswith(b"\n\n"),
    "has_crlf": b"\r\n" in raw,
    "has_bare_cr": b"\r" in raw and b"\r\n" not in raw,
    "ids": [rec_id(o) for _, o in records],
}

# 1. check_jsonl FactoryStaging
cj_err, cj_warn, cj_kinds, cj_n = check_jsonl(
    BATCH, "batch-r13.jsonl", staging=FactoryStaging(enabled=True)
)
out["checks"]["check_jsonl"] = {
    "errors": cj_err,
    "warnings": cj_warn,
    "kinds": cj_kinds,
    "records": cj_n,
    "pass": cj_err == [] and cj_warn == [] and cj_kinds == {"thalamic": 5} and cj_n == 5,
}

# 2. validate_run.check_line factory_staging + check_record
line_rows = []
line_pass = True
for lineno, obj in records:
    rid = rec_id(obj)
    errs, kind = check_line(obj, f"batch-r13.jsonl:{lineno}", factory_staging=True)
    rec_errs, rec_warns, rec_kind, rec_id_val = check_record(
        obj, f"batch-r13.jsonl:{lineno}", factory_staging=True
    )
    ok = errs == [] and rec_errs == [] and rec_warns == [] and kind == "thalamic"
    line_pass = line_pass and ok
    line_rows.append(
        {
            "id": rid,
            "kind": kind,
            "check_line_errors": errs,
            "check_record_errors": rec_errs,
            "check_record_warnings": rec_warns,
            "check_record_kind": rec_kind,
            "pass": ok,
        }
    )
out["checks"]["check_line"] = {"rows": line_rows, "pass": line_pass and len(line_rows) == 5}

# 3. dumps_exact_json
exact_rows = []
exact_pass = True
for lineno, obj in records:
    rid = rec_id(obj)
    try:
        dumps_exact_json(obj, ensure_ascii=False, sort_keys=False)
        exact_rows.append({"id": rid, "error": None, "pass": True})
    except (ValueError, RecursionError) as exc:
        exact_pass = False
        exact_rows.append({"id": rid, "error": str(exc), "pass": False})
out["checks"]["exact_json"] = {"rows": exact_rows, "pass": exact_pass}

# 4. raster_status
raster_rows = []
raster_pass = True
for lineno, obj in records:
    st = raster_status(obj)
    ok = (
        st.get("reason_codes") == []
        and st.get("gate_snn_present") is True
        and st.get("gate_snn_valid") is True
        and st.get("raster_valid") is True
        and int(st.get("routing_table_entries") or 0) >= 1
        and st.get("third_factor_present") is True
    )
    raster_pass = raster_pass and ok
    raster_rows.append(
        {
            "id": rec_id(obj),
            "reason_codes": st.get("reason_codes"),
            "gate_snn_present": st.get("gate_snn_present"),
            "gate_snn_valid": st.get("gate_snn_valid"),
            "routing_table_entries": st.get("routing_table_entries"),
            "third_factor_present": st.get("third_factor_present"),
            "raster_valid": st.get("raster_valid"),
            "spikes": st.get("spikes"),
            "pass": ok,
        }
    )
out["checks"]["raster_status"] = {"rows": raster_rows, "pass": raster_pass}

# 5. verify_batch_for_frontier strict
counts, findings, blocked = verify_batch_for_frontier(BATCH, strict=True)
out["checks"]["verify_batch_for_frontier"] = {
    "counts": counts,
    "findings": findings,
    "blocked": blocked,
    "pass": counts == {"verified": 5, "inconclusive": 0, "failed": 0, "total": 5}
    and blocked is False
    and findings == [],
}

# 6. spike_probe --strict
sp = subprocess.run(
    [sys.executable, str(PIPE / "spike_probe.py"), "--strict", str(BATCH)],
    cwd=str(REPO),
    capture_output=True,
    text=True,
)
try:
    sp_json = json.loads(sp.stdout)
except json.JSONDecodeError:
    sp_json = {"raw_stdout": sp.stdout}
out["checks"]["spike_probe"] = {
    "exit": sp.returncode,
    "stderr": sp.stderr,
    "summary": sp_json,
    "pass": sp.returncode == 0
    and not sp.stderr
    and sp_json.get("loaded") == 5
    and sp_json.get("unloadable") == 0
    and sp_json.get("input_errors") == 0
    and sp_json.get("problems") == []
    and sp_json.get("thalamic_records") == 5,
}

# 7. Reward tick sums
tick_rows = []
tick_pass = True
for lineno, obj in records:
    rid = rec_id(obj)
    rc = obj["reward_components"]
    ticks = rc.get("ticks") or []
    sums = {h: 0.0 for h in HEADS}
    t_us = []
    for t in ticks:
        t_us.append(t.get("t_us"))
        for h in HEADS:
            sums[h] += float(t.get(h) or 0.0)
    head_sum = sum(sums[h] for h in HEADS)
    total = float(rc.get("total"))
    infl = obj.get("future_outcome", {}).get("reward_inflection_t_us")
    errs = []
    if len(ticks) != 6:
        errs.append(f"ticks={len(ticks)} != 6")
    if rc.get("_aggregation") != AGG:
        errs.append(f"aggregation={rc.get('_aggregation')!r}")
    for h in HEADS:
        if abs(sums[h] - float(rc[h])) > TOL:
            errs.append(f"{h} tick-sum {sums[h]!r} != head {rc[h]!r}")
    if abs(head_sum - total) > TOL:
        errs.append(f"head-sum {head_sum!r} != total {total!r}")
    if infl not in t_us:
        errs.append(f"inflection {infl} not in ticks {t_us}")
    ok = not errs
    tick_pass = tick_pass and ok
    tick_rows.append(
        {
            "id": rid,
            "n_ticks": len(ticks),
            "sums": sums,
            "heads": {h: rc[h] for h in HEADS},
            "head_sum": head_sum,
            "total": total,
            "abs_delta": abs(head_sum - total),
            "t_us": t_us,
            "inflection": infl,
            "inflection_in_ticks": infl in t_us,
            "errors": errs,
            "pass": ok,
        }
    )
out["checks"]["tick_sums"] = {"rows": tick_rows, "pass": tick_pass}

# TTF-M6 lattice
lattice_rows = []
lattice_pass = True
for lineno, obj in records:
    rid = rec_id(obj)
    st = obj["state"]
    ticks = obj["reward_components"]["ticks"]
    t_us = [t["t_us"] for t in ticks]
    events = obj["spike_events"]
    # winner/loser from race narrative: first two channels in race window
    race = st["race_window_rel_ms"]
    t_win_us = round(min(e["t_rel_ms"] for e in events if race[0] <= e["t_rel_ms"] <= race[1] and e["channel"] != "ctrl.gate") * 1000)  # noqa: E501
    # Use declared race winner times from ticks[1], ticks[2] vs formula
    t_gate_us_formula = None
    # Prefer explicit: tick2 = winner from spike of primary sensor at race start-ish
    # Independent: tick formulas from plan using winner/loser spike times in window.
    in_win = [e for e in events if race[0] - 1e-9 <= e["t_rel_ms"] <= race[1] + 1e-9]
    channels_in = sorted({e["channel"] for e in in_win})
    # winner is earliest non-ctrl in window; loser second distinct channel
    ordered = sorted(in_win, key=lambda e: e["t_rel_ms"])
    win_e = next((e for e in ordered if e["channel"] != "ctrl.gate"), None)
    lose_e = next(
        (e for e in ordered if e["channel"] not in {win_e["channel"], "ctrl.gate"}), None
    )
    t_win = round(win_e["t_rel_ms"] * 1000)
    t_lose = round(lose_e["t_rel_ms"] * 1000)
    t_gate = t_win + int(st["gate_latency_us"])
    T_race = int(st["race_window_us"])
    T_win = int(round(float(obj["raster"]["window_ms"]) * 1000))
    tick1 = round(0.40 * t_win)
    if rid == "ttf-r13-081":
        tick5 = 22100
    else:
        tick5 = t_gate + T_race
    expected_prefix = [tick1, t_win, t_lose, t_gate, tick5]
    errs = []
    if t_us[:5] != expected_prefix:
        errs.append(f"prefix {t_us[:5]} != {expected_prefix}")
    if not (t_us[5] > T_win):
        errs.append(f"tick6 {t_us[5]} not > T_win {T_win}")
    ok = not errs
    lattice_pass = lattice_pass and ok
    lattice_rows.append(
        {
            "id": rid,
            "t_win": t_win,
            "t_lose": t_lose,
            "t_gate": t_gate,
            "T_race": T_race,
            "T_win": T_win,
            "expected_prefix": expected_prefix,
            "observed": t_us,
            "channels_in_window": channels_in,
            "errors": errs,
            "pass": ok,
        }
    )
out["checks"]["ttf_m6"] = {"rows": lattice_rows, "pass": lattice_pass}

# 8. Spike trains refractory
spike_rows = []
spike_pass = True
for lineno, obj in records:
    rid = rec_id(obj)
    events = obj["spike_events"]
    errs = []
    keys = set()
    for e in events:
        keys |= set(e)
    ts_keys = {k for k in keys if k.startswith("t_") or k in {"t", "time"}}
    # timestamp keys actually present besides channel
    present_t = set()
    for e in events:
        present_t |= {k for k in e if k != "channel"}
    times = [e.get("t_rel_ms") for e in events]
    if not all(isinstance(t, (int, float)) and math.isfinite(t) for t in times):
        errs.append("non-finite t_rel_ms")
    if any(t == 0 for t in times):
        errs.append("zero t_rel_ms")
    if times != sorted(times):
        errs.append("not globally non-decreasing")
    n = len(events)
    if not (5 <= n <= 40):
        errs.append(f"n={n} not in [5,40]")
    by_ch = defaultdict(list)
    for e in events:
        by_ch[e["channel"]].append(e["t_rel_ms"])
    min_gap = None
    min_ch = None
    for ch, ts in by_ch.items():
        for a, b in zip(ts, ts[1:]):
            gap = b - a
            if min_gap is None or gap < min_gap:
                min_gap = gap
                min_ch = ch
            if gap < 0.8 - 1e-12:
                errs.append(f"{ch} gap {gap} < 0.8")
    race = obj["state"]["race_window_rel_ms"]
    in_win_ch = sorted(
        {
            e["channel"]
            for e in events
            if race[0] - 1e-12 <= e["t_rel_ms"] <= race[1] + 1e-12
        }
    )
    if len(in_win_ch) < 2:
        errs.append(f"channels in window {in_win_ch}")
    ok = not errs
    spike_pass = spike_pass and ok
    spike_rows.append(
        {
            "id": rid,
            "n": n,
            "timestamp_keys_union": sorted(present_t),
            "min_same_ch_gap_ms": min_gap,
            "min_gap_channel": min_ch,
            "race_window_rel_ms": race,
            "channels_in_window": in_win_ch,
            "errors": errs,
            "pass": ok,
        }
    )
out["checks"]["refractory"] = {
    "rows": spike_rows,
    "pass": spike_pass and all(r["min_same_ch_gap_ms"] >= 0.8 for r in spike_rows),
}

# Raster excerpt same-neuron gap + independence
excerpt_rows = []
excerpt_pass = True
for lineno, obj in records:
    rid = rec_id(obj)
    r = obj["raster"]
    excerpt = r.get("excerpt") or []
    errs = []
    if not (8 <= len(excerpt) <= 16):
        errs.append(f"excerpt n={len(excerpt)} not in [8,16]")
    t_us = [e["t_us"] for e in excerpt]
    if t_us != sorted(t_us):
        errs.append("excerpt not sorted")
    window_us = int(round(float(r["window_ms"]) * 1000))
    by_n = defaultdict(list)
    for e in excerpt:
        nid = e["neuron_id"]
        if not (0 <= nid < r["neurons"]):
            errs.append(f"neuron_id {nid} out of range")
        if e["t_us"] < 0 or e["t_us"] > window_us:
            errs.append(f"t_us {e['t_us']} outside [0,{window_us}]")
        by_n[nid].append(e["t_us"])
    min_gap = None
    for nid, ts in by_n.items():
        for a, b in zip(ts, ts[1:]):
            gap = b - a
            if min_gap is None or gap < min_gap:
                min_gap = gap
            if gap < 1000:
                errs.append(f"neuron {nid} gap {gap} < 1000")
    spike_tus = {round(e["t_rel_ms"] * 1000) for e in obj["spike_events"]}
    excerpt_tus = set(t_us)
    overlap = sorted(spike_tus & excerpt_tus)
    ok = not errs
    excerpt_pass = excerpt_pass and ok
    excerpt_rows.append(
        {
            "id": rid,
            "n": len(excerpt),
            "min_same_neuron_gap_us": min_gap,
            "overlap_t_us_with_spike_events": overlap,
            "excerpt_source": r.get("excerpt_source"),
            "errors": errs,
            "pass": ok,
        }
    )
out["checks"]["excerpt"] = {"rows": excerpt_rows, "pass": excerpt_pass}

# Raster energy budgets
energy_rows = []
energy_pass = True
for lineno, obj in records:
    rid = rec_id(obj)
    r = obj["raster"]
    n = r["neurons"]
    rate = r["mean_rate_hz"]
    window_ms = r["window_ms"]
    window_s = r["window_s"]
    spikes = r["spikes"]
    expected = round(n * rate * window_s)
    errs = []
    if abs(window_s - window_ms / 1000) > 1e-9:
        errs.append("window_s != window_ms/1000")
    if abs(spikes - expected) > 1:
        errs.append(f"spikes {spikes} != round(n*rate*window_s) {expected}")
    if r["energy_pJ"] != spikes * 23:
        errs.append(f"energy_pJ {r['energy_pJ']} != {spikes*23}")
    if abs(r["energy_uJ"] - spikes * 23e-6) > 1e-15:
        errs.append(f"energy_uJ {r['energy_uJ']} != {spikes*23e-6}")
    ok = not errs
    energy_pass = energy_pass and ok
    energy_rows.append(
        {
            "id": rid,
            "n": n,
            "rate": rate,
            "window_ms": window_ms,
            "expected_spikes": expected,
            "spikes": spikes,
            "energy_pJ": r["energy_pJ"],
            "errors": errs,
            "pass": ok,
        }
    )
out["checks"]["raster_budget"] = {"rows": energy_rows, "pass": energy_pass}

# gate_snn decision + population budget
gs_rows = []
gs_pass = True
for lineno, obj in records:
    rid = rec_id(obj)
    gs = obj["gate_snn"]
    sd = obj["safety_decision"]["decision"]
    dw_ms = gs["decision_window_ms"]
    dw_s = dw_ms / 1000.0
    errs = []
    if gs["decision"].strip().upper() != sd.strip().upper():
        errs.append(f"gate_snn {gs['decision']} != safety {sd}")
    pops = []
    for p in gs["populations"]:
        rate = p.get("mean_rate_hz")
        spikes = p.get("spikes")
        neurons = p.get("neurons")
        if rate is None and spikes is None:
            pops.append({"name": p["name"], "budget": "absent", "delta": None})
            continue
        expected = round(neurons * rate * dw_s)
        delta = abs(spikes - expected)
        if delta > 1:
            errs.append(f"{p['name']} spikes {spikes} vs {expected} Δ={delta}")
        pops.append(
            {
                "name": p["name"],
                "neurons": neurons,
                "rate": rate,
                "spikes": spikes,
                "expected": expected,
                "delta": delta,
                "threshold": p.get("threshold"),
            }
        )
    ok = not errs
    gs_pass = gs_pass and ok
    gs_rows.append(
        {
            "id": rid,
            "decision": gs["decision"],
            "safety": sd,
            "decision_window_ms": dw_ms,
            "pops": pops,
            "errors": errs,
            "pass": ok,
        }
    )
out["checks"]["gate_snn"] = {"rows": gs_rows, "pass": gs_pass}

# 9. Jaccard
descs = [(rec_id(o), tokenize(o["state"]["description"])) for _, o in records]
pairs = []
j_max = 0.0
j_pass = True
for i in range(len(descs)):
    for j in range(i + 1, len(descs)):
        jac = jaccard(descs[i][1], descs[j][1])
        j_max = max(j_max, jac)
        ok = jac < 0.4
        j_pass = j_pass and ok
        pairs.append(
            {
                "pair": f"{descs[i][0][-3:]}–{descs[j][0][-3:]}",
                "jaccard": jac,
                "pass": ok,
            }
        )
out["checks"]["jaccard"] = {"pairs": pairs, "max": j_max, "pass": j_pass and j_max < 0.4}

# Gate mix / exactly one incorrect / 082 wrong-MODIFY
gate_rows = []
incorrect = []
for lineno, obj in records:
    rid = rec_id(obj)
    sd = obj["safety_decision"]
    err_type = obj["meta"].get("supervisor_error_type")
    row = {
        "id": rid,
        "decision": sd.get("decision"),
        "correctness": sd.get("correctness"),
        "supervisor_error_type": err_type,
    }
    gate_rows.append(row)
    if sd.get("correctness") == "incorrect" or err_type:
        incorrect.append(row)
gate_pass = (
    len(incorrect) == 1
    and incorrect[0]["id"] == "ttf-r13-082"
    and incorrect[0]["decision"] == "MODIFY"
    and incorrect[0]["correctness"] == "incorrect"
    and incorrect[0]["supervisor_error_type"] == "wrong-modify"
    and all(
        (r["correctness"] == "correct" and r["supervisor_error_type"] is None)
        for r in gate_rows
        if r["id"] != "ttf-r13-082"
    )
    and not any(
        r["decision"] == "ACCEPT" and r["correctness"] == "incorrect" for r in gate_rows
    )
)
out["checks"]["gate_mix"] = {
    "rows": gate_rows,
    "incorrect": incorrect,
    "pass": gate_pass,
}

# 082 wrong-MODIFY convict checklist
o082 = next(o for _, o in records if rec_id(o) == "ttf-r13-082")
ev = o082["proposed_action"]["evidence"]
ex = o082["executed_action"]["parameters"]
table = o082["raster"]["routing"]["table"]
pops = {p["name"]: p for p in o082["gate_snn"]["populations"]}
pos_j6 = [
    e
    for e in table
    if e.get("to") == "policy.j6_insert_clamp" and float(e.get("weight", 0)) > 0
]
ft_to_j2 = any(
    e.get("from") == "relay.ft.z"
    and e.get("to") == "policy.j2_hold"
    and abs(float(e.get("weight", 0)) - 0.71) < 1e-9
    for e in table
)
recov = (o082.get("future_outcome") or {}).get("recovery") or {}
c082 = {
    "fz_gt_cap": ev["fz_N"] > ev["insertion_cap_N"],
    "fz_N": ev["fz_N"],
    "cap": ev["insertion_cap_N"],
    "ft_axis": ev["ft_axis"],
    "ft_axis_ok": ev["ft_axis"] == "wrist_insert_z",
    "executed_j2": ex["j2_tau_Nm"],
    "executed_insert_z": ex["insert_z_N"],
    "executed_wrong_axis": ex["j2_tau_Nm"] == 35.0 and ex["insert_z_N"] == 48.2,
    "routing_ft_to_j2": ft_to_j2,
    "no_pos_j6": pos_j6 == [],
    "table": table,
    "j2_hold_spikes": pops["j2_hold"]["spikes"],
    "j6_spikes": pops["j6_insert_clamp"]["spikes"],
    "j2_above": pops["j2_hold"]["spikes"] > 0,
    "j6_not_above": pops["j6_insert_clamp"]["spikes"] == 0,
    "recovery": recov.get("correct_gate"),
    "decision": o082["safety_decision"]["decision"],
    "correctness": o082["safety_decision"]["correctness"],
    "error_type": o082["meta"].get("supervisor_error_type"),
}
c082_pass = all(
    [
        c082["fz_gt_cap"],
        c082["ft_axis_ok"],
        c082["executed_wrong_axis"],
        c082["routing_ft_to_j2"],
        c082["no_pos_j6"],
        c082["j2_above"],
        c082["j6_not_above"],
        c082["decision"] == "MODIFY",
        c082["correctness"] == "incorrect",
        c082["error_type"] == "wrong-modify",
        isinstance(c082["recovery"], str) and "J6" in c082["recovery"],
    ]
)
out["checks"]["wrong_modify_082"] = {"detail": c082, "pass": c082_pass}

# 081 inflection inside raster window
o081 = next(o for _, o in records if rec_id(o) == "ttf-r13-081")
infl = o081["future_outcome"]["reward_inflection_t_us"]
T_win_081 = int(round(float(o081["raster"]["window_ms"]) * 1000))
tick_t = [t["t_us"] for t in o081["reward_components"]["ticks"]]
r081 = o081["raster"]
c081 = {
    "inflection": infl,
    "T_win_us": T_win_081,
    "inside": infl <= T_win_081,
    "equals_tick5": infl == tick_t[4] == 22100,
    "tick_t": tick_t,
    "excerpt_source": r081.get("excerpt_source"),
    "sim_scope": r081.get("sim_scope"),
    "lif_seed": (r081.get("lif") or {}).get("seed"),
    "lif_stim": (r081.get("lif") or {}).get("stim_t_us"),
    "sim_or_real": o081["state"]["sim_or_real"],
    "tags": o081["meta"].get("tags"),
    "un_netted_loss": o081["future_outcome"].get("un_netted_loss"),
    "total": o081["reward_components"]["total"],
    "decision": o081["safety_decision"]["decision"],
    "correctness": o081["safety_decision"]["correctness"],
    "excerpt_channels": [e.get("channel") for e in r081.get("excerpt") or []],
}
c081_pass = all(
    [
        c081["inside"],
        c081["equals_tick5"],
        c081["excerpt_source"] == "independent_lif",
        c081["sim_scope"] == "sidecar_only",
        c081["lif_seed"] == 13081,
        c081["lif_stim"] == [21000, 24000],
        c081["sim_or_real"] == "designed",
        "independent-lif-raster" in c081["tags"],
        "sidecar-sim-only" in c081["tags"],
        bool(c081["un_netted_loss"]),
        abs(c081["total"] - (-0.42)) < TOL,
        c081["decision"] == "MODIFY",
        c081["correctness"] == "correct",
        set(c081["excerpt_channels"]) == {"lif.clamp", "lif.tear"},
    ]
)
# LIF burst cluster 21-24 ms
tear_times = [
    e["t_us"]
    for e in r081["excerpt"]
    if e.get("channel") == "lif.tear"
]
c081["tear_times"] = tear_times
c081["tear_in_stim"] = all(21000 <= t <= 24000 for t in tear_times) and len(tear_times) >= 2
c081_pass = c081_pass and c081["tear_in_stim"]
# only 081 has independent LIF labels
lif_others = [
    rec_id(o)
    for _, o in records
    if rec_id(o) != "ttf-r13-081"
    and (
        o["raster"].get("excerpt_source") == "independent_lif"
        or o["raster"].get("lif")
        or "independent-lif-raster" in (o["meta"].get("tags") or [])
    )
]
c081["lif_on_others"] = lif_others
c081_pass = c081_pass and lif_others == []
out["checks"]["inflection_081"] = {"detail": c081, "pass": c081_pass}

# Thought keys
thought_hits = []
for lineno, obj in records:
    rid = rec_id(obj)
    vr = _hidden_thought_paths(obj)
    staging_errs = _staging_hidden_thought_errors(obj, f"{rid}")
    ta = list(hidden_thought_paths(obj))
    extra = []
    for path, key, _ in walk_keys(obj):
        nk = re.sub(
            r"[^a-z0-9]+",
            "_",
            re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "_", str(key)).casefold(),
        ).strip("_")
        if nk in EXTRA_THOUGHT or is_hidden_thought_key(key) or nk in HIDDEN_THOUGHT_KEYS:
            extra.append(path)
    if vr or staging_errs or ta or extra:
        thought_hits.append(
            {
                "id": rid,
                "validate_run": vr,
                "staging_errors": staging_errs,
                "training_audit": ta,
                "extra": extra,
            }
        )
out["checks"]["thought_keys"] = {
    "hits": thought_hits,
    "scanned": sorted(set(HIDDEN_THOUGHT_KEYS) | set(EXTRA_THOUGHT)),
    "pass": thought_hits == [],
}

# no real / training_ready
real_hits = []
tr_hits = []
sim_rows = []
for lineno, obj in records:
    rid = rec_id(obj)
    for path, val in walk_key(obj, "sim_or_real"):
        sim_rows.append({"id": rid, "path": path, "value": val, "claims_real": claims_real(val)})
        if claims_real(val) or (isinstance(val, str) and val.strip().lower() == "real"):
            real_hits.append({"id": rid, "path": path, "value": val})
    for path, key, val in walk_keys(obj):
        if str(key) == "training_ready":
            tr_hits.append({"id": rid, "path": path, "value": val})
        if isinstance(val, str) and claims_real(val):
            real_hits.append({"id": rid, "path": path, "value": val, "via": "string"})
    pub = check_provenance_publish(obj, rid)
    if pub:
        real_hits.append({"id": rid, "provenance_publish": pub})
allowed = {"designed", "simulated", "hil"}
sim_ok = (
    all(r["value"] in allowed and not r["claims_real"] for r in sim_rows)
    and real_hits == []
    and tr_hits == []
)
# expected mix
mix = {r["id"]: r["value"] for r in sim_rows if r["path"] == "state.sim_or_real"}
mix_ok = mix == {
    "ttf-r13-081": "designed",
    "ttf-r13-082": "designed",
    "ttf-r13-083": "hil",
    "ttf-r13-084": "simulated",
    "ttf-r13-085": "designed",
}
out["checks"]["no_real"] = {
    "sim_or_real": sim_rows,
    "real_hits": real_hits,
    "training_ready": tr_hits,
    "mix": mix,
    "pass": sim_ok and mix_ok and len(sim_rows) == 5,
}

# meta.round=13 identity
id_rows = []
id_pass = True
for lineno, obj in records:
    rid = rec_id(obj)
    m = obj["meta"]
    errs = []
    if rid not in EXPECTED_IDS:
        errs.append(f"id {rid}")
    if m.get("round") != 13:
        errs.append(f"round {m.get('round')}")
    if m.get("factory") != "thalamic-trajectory-factory":
        errs.append(f"factory {m.get('factory')}")
    if m.get("generator") != "grok-4.6":
        errs.append(f"generator {m.get('generator')}")
    if m.get("run_label") != "2026-09-02-final-heavy":
        errs.append(f"run_label {m.get('run_label')}")
    if m.get("domain") != obj["state"].get("domain"):
        errs.append("domain mismatch")
    if m.get("snn_tags") != ["race", "refractory", "adaptation"]:
        errs.append(f"snn_tags {m.get('snn_tags')}")
    ok = not errs
    id_pass = id_pass and ok
    id_rows.append({"id": rid, "round": m.get("round"), "errors": errs, "pass": ok})
id_order_ok = [rec_id(o) for _, o in records] == EXPECTED_IDS
out["checks"]["meta_identity"] = {
    "rows": id_rows,
    "ids": [rec_id(o) for _, o in records],
    "expected": EXPECTED_IDS,
    "pass": id_pass and id_order_ok and len(records) == 5,
}

# RM-793
rights_rows = []
rights_pass = True
for lineno, obj in records:
    rid = rec_id(obj)
    rights = obj["meta"].get("rights") or {}
    errs = []
    keys = tuple(sorted(rights))
    if set(rights) != set(RIGHTS_KEYS):
        extra = sorted(set(rights) - set(RIGHTS_KEYS))
        missing = sorted(set(RIGHTS_KEYS) - set(rights))
        errs.append(f"key mismatch extra={extra} missing={missing}")
    for k, v in RIGHTS_VALUES.items():
        if rights.get(k) != v:
            errs.append(f"{k}={rights.get(k)!r} != {v!r}")
    ga = rights.get("generated_at")
    if not (isinstance(ga, str) and ga.endswith("Z")):
        errs.append(f"generated_at {ga!r}")
    ok = not errs
    rights_pass = rights_pass and ok
    rights_rows.append(
        {
            "id": rid,
            "n_keys": len(rights),
            "keys": sorted(rights),
            "generated_at": ga,
            "errors": errs,
            "pass": ok,
        }
    )
out["checks"]["rm793"] = {"rows": rights_rows, "pass": rights_pass}

# NOTES novel coverage
notes_text = NOTES.read_text()
cov_err = validate_novel_coverage(NOTES, Path("/tmp/ttf-r13"), required=True)
labeled = [
    line
    for line in re.split(r"\r\n|\n|\r", notes_text)
    if re.search(r"^[ \t]*novel[ _-]?coverage\b", line, re.I)
]
full = [line for line in labeled if re.fullmatch(
    r"[ \t]*novel[ _-]?coverage[ \t]*(?:\([^)\r\n]*\))?[ \t]*[:=]?[ \t]*([0-9]+(?:\.[0-9]+)?)[ \t]*%[ \t]*",
    line,
    re.I,
)]
out["checks"]["notes_novel"] = {
    "validate_novel_coverage": cov_err,
    "labeled_lines": labeled,
    "n_labeled": len(labeled),
    "pass": cov_err is None and labeled == ["Novel coverage: 24.0%"] and len(labeled) == 1,
}

# ACCEPT executed == proposed
accept_rows = []
accept_pass = True
for _, obj in records:
    if obj["safety_decision"]["decision"] != "ACCEPT":
        continue
    p = obj["proposed_action"]["parameters"]
    e = obj["executed_action"]["parameters"]
    ok = p == e
    accept_pass = accept_pass and ok
    accept_rows.append({"id": rec_id(obj), "proposed": p, "executed": e, "pass": ok})
out["checks"]["accept_identity"] = {"rows": accept_rows, "pass": accept_pass}

# clone plants
clone_hits = []
blob = json.dumps([o for _, o in records]) + notes_text
for name in BANNED_PLANTS:
    if name in blob:
        clone_hits.append(name)
out["checks"]["no_r12_plants"] = {"hits": clone_hits, "pass": clone_hits == []}

# outputs/raw not written
raw_hits = []
for p in RAW.rglob("*"):
    if not p.is_file():
        continue
    name = p.name
    if "r13" in name.lower() or "ttf-r13" in name:
        raw_hits.append(str(p))
# rg ids in outputs/raw
rg = subprocess.run(
    ["rg", "-l", "ttf-r13-08[1-5]", str(RAW)],
    capture_output=True,
    text=True,
)
raw_id_files = [ln for ln in rg.stdout.splitlines() if ln]
out["checks"]["no_outputs_raw"] = {
    "name_hits": raw_hits,
    "content_files": raw_id_files,
    "pass": raw_hits == [] and raw_id_files == [],
}

# domains
domains = [(rec_id(o), o["state"]["domain"], o["meta"]["domain"]) for _, o in records]
expected_domains = [
    ("ttf-r13-081", "surgical-assist", "surgical-assist"),
    ("ttf-r13-082", "industrial-assembly", "industrial-assembly"),
    ("ttf-r13-083", "autonomous-driving", "autonomous-driving"),
    ("ttf-r13-084", "aerial-swarm", "aerial-swarm"),
    ("ttf-r13-085", "warehouse-amr", "warehouse-amr"),
]
out["checks"]["domains"] = {
    "observed": domains,
    "pass": domains == expected_domains and len({d[1] for d in domains}) == 5,
}

# third_factor tau pair + modulator variety
tf_rows = []
tf_pass = True
mods = []
for _, obj in records:
    tf = obj["raster"]["routing"]["third_factor"]
    errs = []
    if abs(tf["tau_e_ms"] / 1000.0 - tf["tau_e_s"]) > 1e-12:
        errs.append("tau mismatch")
    if not tf.get("modulator"):
        errs.append("no modulator")
    if not tf.get("eligibility"):
        errs.append("no eligibility")
    ok = not errs
    tf_pass = tf_pass and ok
    mods.append(tf["modulator"])
    tf_rows.append({"id": rec_id(obj), "third_factor": tf, "errors": errs, "pass": ok})
out["checks"]["third_factor"] = {
    "rows": tf_rows,
    "modulators": mods,
    "pass": tf_pass and len(set(mods)) >= 4,
}

# totals vs NOTES
expected_totals = {
    "ttf-r13-081": -0.42,
    "ttf-r13-082": -0.68,
    "ttf-r13-083": 0.80,
    "ttf-r13-084": 1.02,
    "ttf-r13-085": 1.18,
}
tot_ok = all(
    abs(float(o["reward_components"]["total"]) - expected_totals[rec_id(o)]) < TOL
    for _, o in records
)
out["checks"]["declared_totals"] = {
    "observed": {rec_id(o): o["reward_components"]["total"] for _, o in records},
    "pass": tot_ok,
}

failed = [k for k, v in out["checks"].items() if not v.get("pass")]
out["summary"] = {
    "n_checks": len(out["checks"]),
    "n_pass": sum(1 for v in out["checks"].values() if v.get("pass")),
    "failed": failed,
    "all_pass": failed == [],
}

Path("/tmp/ttf-r13-audit-run.json").write_text(
    json.dumps(out, indent=2, default=str, sort_keys=False) + "\n"
)
print(json.dumps(out["summary"], indent=2))
print("failed:", failed)
for k, v in out["checks"].items():
    print(f"{k}: {'PASS' if v.get('pass') else 'FAIL'}")
