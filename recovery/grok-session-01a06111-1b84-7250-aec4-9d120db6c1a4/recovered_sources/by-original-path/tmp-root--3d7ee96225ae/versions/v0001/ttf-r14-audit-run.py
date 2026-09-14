#!/usr/bin/env python3
"""Independent fail-closed audit of /tmp/ttf-r14 staging. Does not write outputs/raw/."""
from __future__ import annotations

import hashlib
import json
import math
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

BATCH = Path("/tmp/ttf-r14/batch-r14.jsonl")
NOTES = Path("/tmp/ttf-r14/NOTES-r14.md")
PREMISES = Path("/tmp/ttf-r14-premises.md")
RAW = REPO / "outputs" / "raw"
R12 = Path("/tmp/batch-r12.jsonl")
R13 = Path("/tmp/ttf-r13/batch-r13.jsonl")
EXPECTED_IDS = [f"ttf-r14-{n:03d}" for n in range(86, 91)]
HEADS = ("task_progress", "safety", "efficiency", "coherence", "exploration")
AGG = "total = task_progress + safety + efficiency + coherence + exploration"
DOMAIN_POOL = {
    "industrial-assembly",
    "surgical-assist",
    "autonomous-driving",
    "aerial-swarm",
    "warehouse-amr",
    "humanoid-locomotion",
    "grid-inspection",
    "underwater-rov",
}
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
    "Nacre-Well",
    "Calyx-9",
    "Quern-Forge",
    "Spindle-H6",
    "Tinder-Box",
    "Plover-4",
    "Whimbrel-Stack",
    "Cinder-Loft",
    "Kiln-Spur",
)
PREMISES_ASSIGN = {
    "ttf-r14-086": {
        "domain": "grid-inspection",
        "decision": "REJECT",
        "correctness": "incorrect",
        "error": "wrong-reject",
        "sim": "designed",
    },
    "ttf-r14-087": {
        "domain": "underwater-rov",
        "decision": "ACCEPT",
        "correctness": "correct",
        "error": None,
        "sim": "simulated",
    },
    "ttf-r14-088": {
        "domain": "humanoid-locomotion",
        "decision": "REJECT",
        "correctness": "correct",
        "error": None,
        "sim": "hil",
    },
    "ttf-r14-089": {
        "domain": "industrial-assembly",
        "decision": "MODIFY",
        "correctness": "correct",
        "error": None,
        "sim": "designed",
    },
    "ttf-r14-090": {
        "domain": "autonomous-driving",
        "decision": "ACCEPT",
        "correctness": "correct",
        "error": None,
        "sim": "designed",
    },
}
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


def load_jsonl(path: Path):
    records = []
    text = path.read_text(encoding="utf-8")
    for i, line in enumerate(text.split("\n"), 1):
        if not line.strip():
            continue
        records.append((i, json.loads(line)))
    return records


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
    "notes_exists": NOTES.is_file(),
    "batch_bytes": BATCH.stat().st_size,
    "notes_bytes": NOTES.stat().st_size if NOTES.is_file() else None,
    "batch_sha256": sha256(BATCH),
    "notes_sha256": sha256(NOTES) if NOTES.is_file() else None,
    "n_physical_split": len(physical_lines),
    "n_nonempty": len(records),
    "trailing_lf": raw.endswith(b"\n") and not raw.endswith(b"\n\n"),
    "has_crlf": b"\r\n" in raw,
    "has_bare_cr": b"\r" in raw and b"\r\n" not in raw,
    "ids": [rec_id(o) for _, o in records],
}

# 1. check_jsonl FactoryStaging
cj_err, cj_warn, cj_kinds, cj_n = check_jsonl(
    BATCH, "batch-r14.jsonl", staging=FactoryStaging(enabled=True)
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
    errs, kind = check_line(obj, f"batch-r14.jsonl:{lineno}", factory_staging=True)
    rec_errs, rec_warns, rec_kind, rec_id_val = check_record(
        obj, f"batch-r14.jsonl:{lineno}", factory_staging=True
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

# CLI twin
ve = subprocess.run(
    [
        sys.executable,
        str(PIPE / "verify_execution.py"),
        "--strict",
        "--batch",
        str(BATCH),
        "--json",
    ],
    cwd=str(REPO),
    capture_output=True,
    text=True,
)
out["checks"]["verify_batch_for_frontier"]["cli_exit"] = ve.returncode
out["checks"]["verify_batch_for_frontier"]["cli_stdout"] = ve.stdout
out["checks"]["verify_batch_for_frontier"]["pass"] = (
    out["checks"]["verify_batch_for_frontier"]["pass"] and ve.returncode == 0
)

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

# Tick-6 sidecar bind (r13 residual close)
t6_rows = []
t6_pass = True
for lineno, obj in records:
    rid = rec_id(obj)
    ticks = obj["reward_components"]["ticks"]
    t_us = [t["t_us"] for t in ticks]
    T_win = int(round(float(obj["raster"]["window_ms"]) * 1000))
    delayed = obj["raster"].get("delayed_surprise_s")
    fo_delayed = (obj.get("future_outcome") or {}).get("delayed_surprise_s")
    errs = []
    if delayed is None:
        errs.append("raster.delayed_surprise_s missing")
    if fo_delayed != delayed:
        errs.append(f"future delayed {fo_delayed} != raster {delayed}")
    if delayed is not None and t_us[-1] != int(round(float(delayed) * 1_000_000)):
        errs.append(f"tick6 {t_us[-1]} != {delayed}*1e6")
    if not (t_us[-1] > T_win):
        errs.append(f"tick6 {t_us[-1]} not > T_win {T_win}")
    ok = not errs
    t6_pass = t6_pass and ok
    t6_rows.append(
        {
            "id": rid,
            "delayed_surprise_s": delayed,
            "tick6": t_us[-1],
            "T_win": T_win,
            "errors": errs,
            "pass": ok,
        }
    )
out["checks"]["tick6_sidecar"] = {"rows": t6_rows, "pass": t6_pass}

# 8. Spike trains refractory
spike_rows = []
spike_pass = True
for lineno, obj in records:
    rid = rec_id(obj)
    events = obj["spike_events"]
    errs = []
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
        ch = e["channel"]
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,31}", ch):
            errs.append(f"bad channel {ch!r}")
        by_ch[ch].append(e["t_rel_ms"])
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

# Raster excerpt hygiene
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
    if not (20 <= window_ms <= 50):
        errs.append(f"window_ms {window_ms} not in [20,50]")
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

# 9. Jaccard intra + vs prior rounds
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

prior_pairs = []
j_max_prior = 0.0
j_prior_pass = True
for label, path in (("r12", R12), ("r13", R13)):
    if not path.is_file():
        continue
    prior = load_jsonl(path)
    for _, o in records:
        a = tokenize(o["state"]["description"])
        for _, old in prior:
            b = tokenize(old["state"]["description"])
            jac = jaccard(a, b)
            j_max_prior = max(j_max_prior, jac)
            ok = jac < 0.4
            j_prior_pass = j_prior_pass and ok
            if jac >= 0.15:
                prior_pairs.append(
                    {
                        "pair": f"{rec_id(o)}/{rec_id(old)}",
                        "round": label,
                        "jaccard": jac,
                        "pass": ok,
                    }
                )
out["checks"]["jaccard"] = {
    "pairs": pairs,
    "max": j_max,
    "prior_high": sorted(prior_pairs, key=lambda r: -r["jaccard"])[:12],
    "max_vs_prior": j_max_prior,
    "pass": j_pass and j_max < 0.4 and j_prior_pass and j_max_prior < 0.4,
}

# Gate mix / exactly one incorrect
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
    and incorrect[0]["id"] == "ttf-r14-090"
    and incorrect[0]["decision"] == "MODIFY"
    and incorrect[0]["correctness"] == "incorrect"
    and incorrect[0]["supervisor_error_type"] == "wrong-modify"
    and all(
        (r["correctness"] == "correct" and r["supervisor_error_type"] is None)
        for r in gate_rows
        if r["id"] != "ttf-r14-090"
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

# 090 wrong-MODIFY convict checklist (r13-082 analog)
o090 = next(o for _, o in records if rec_id(o) == "ttf-r14-090")
ev = o090["proposed_action"]["evidence"]
ex = o090["executed_action"]["parameters"]
table = o090["raster"]["routing"]["table"]
pops = {p["name"]: p for p in o090["gate_snn"]["populations"]}
pos_dc = [
    e
    for e in table
    if e.get("to") == "policy.dc_current_clamp" and float(e.get("weight", 0)) > 0
]
temp_to_ac = any(
    e.get("from") == "relay.temp.core"
    and e.get("to") == "policy.ac_precharge_hold"
    and abs(float(e.get("weight", 0)) - 0.73) < 1e-9
    for e in table
)
recov = (o090.get("future_outcome") or {}).get("recovery") or {}
c090 = {
    "core_gt_cap": ev["core_C"] > ev["temp_cap_C"],
    "core_C": ev["core_C"],
    "cap": ev["temp_cap_C"],
    "temp_axis": ev["temp_axis"],
    "temp_axis_ok": ev["temp_axis"] == "cable_core",
    "executed_ac": ex["ac_precharge_A"],
    "executed_dc": ex["dc_A"],
    "executed_wrong_loop": ex["ac_precharge_A"] == 6.0 and ex["dc_A"] == 312.0,
    "routing_temp_to_ac": temp_to_ac,
    "no_pos_dc": pos_dc == [],
    "table": table,
    "ac_hold_spikes": pops["ac_precharge_hold"]["spikes"],
    "dc_spikes": pops["dc_current_clamp"]["spikes"],
    "ac_above": pops["ac_precharge_hold"]["spikes"] > 0,
    "dc_not_above": pops["dc_current_clamp"]["spikes"] == 0,
    "recovery": recov.get("correct_gate"),
    "decision": o090["safety_decision"]["decision"],
    "correctness": o090["safety_decision"]["correctness"],
    "error_type": o090["meta"].get("supervisor_error_type"),
}
c090_pass = all(
    [
        c090["core_gt_cap"],
        c090["temp_axis_ok"],
        c090["executed_wrong_loop"],
        c090["routing_temp_to_ac"],
        c090["no_pos_dc"],
        c090["ac_above"],
        c090["dc_not_above"],
        c090["decision"] == "MODIFY",
        c090["correctness"] == "incorrect",
        c090["error_type"] == "wrong-modify",
        isinstance(c090["recovery"], str) and "DC" in c090["recovery"],
    ]
)
out["checks"]["wrong_modify_090"] = {"detail": c090, "pass": c090_pass}

# 086 inflection inside raster window (r13-081 analog)
o086 = next(o for _, o in records if rec_id(o) == "ttf-r14-086")
infl = o086["future_outcome"]["reward_inflection_t_us"]
T_win_086 = int(round(float(o086["raster"]["window_ms"]) * 1000))
tick_t = [t["t_us"] for t in o086["reward_components"]["ticks"]]
r086 = o086["raster"]
c086 = {
    "inflection": infl,
    "T_win_us": T_win_086,
    "inside": infl <= T_win_086,
    "equals_tick5": infl == tick_t[4] == 18400,
    "tick_t": tick_t,
    "excerpt_source": r086.get("excerpt_source"),
    "sim_scope": r086.get("sim_scope"),
    "lif_seed": (r086.get("lif") or {}).get("seed"),
    "lif_stim": (r086.get("lif") or {}).get("stim_t_us"),
    "sim_or_real": o086["state"]["sim_or_real"],
    "tags": o086["meta"].get("tags"),
    "un_netted_loss": o086["future_outcome"].get("un_netted_loss"),
    "total": o086["reward_components"]["total"],
    "decision": o086["safety_decision"]["decision"],
    "correctness": o086["safety_decision"]["correctness"],
    "excerpt_channels": [e.get("channel") for e in r086.get("excerpt") or []],
    "executed_infusion": o086["executed_action"]["parameters"].get("infusion_mmHg"),
    "proposed_infusion": o086["proposed_action"]["parameters"].get("infusion_mmHg"),
    "cap": o086["proposed_action"]["evidence"].get("infusion_cap_mmHg"),
}
c086_pass = all(
    [
        c086["inside"],
        c086["equals_tick5"],
        c086["excerpt_source"] == "independent_lif",
        c086["sim_scope"] == "sidecar_only",
        c086["lif_seed"] == 14086,
        c086["lif_stim"] == [17500, 20500],
        c086["sim_or_real"] == "designed",
        "independent-lif-raster" in c086["tags"],
        "sidecar-sim-only" in c086["tags"],
        bool(c086["un_netted_loss"]),
        abs(c086["total"] - (-0.39)) < TOL,
        c086["decision"] == "MODIFY",
        c086["correctness"] == "correct",
        set(c086["excerpt_channels"]) == {"lif.clamp", "lif.tear"},
        c086["executed_infusion"] < c086["cap"],
    ]
)
tear_times = [
    e["t_us"] for e in r086["excerpt"] if e.get("channel") == "lif.tear"
]
c086["tear_times"] = tear_times
c086["tear_in_stim"] = all(17500 <= t <= 20500 for t in tear_times) and len(tear_times) >= 2
c086_pass = c086_pass and c086["tear_in_stim"]
lif_others = [
    rec_id(o)
    for _, o in records
    if rec_id(o) != "ttf-r14-086"
    and (
        o["raster"].get("excerpt_source") == "independent_lif"
        or o["raster"].get("lif")
        or "independent-lif-raster" in (o["meta"].get("tags") or [])
    )
]
c086["lif_on_others"] = lif_others
c086_pass = c086_pass and lif_others == []
out["checks"]["inflection_086"] = {"detail": c086, "pass": c086_pass}

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
mix = {r["id"]: r["value"] for r in sim_rows if r["path"] == "state.sim_or_real"}
mix_ok = mix == {
    "ttf-r14-086": "designed",
    "ttf-r14-087": "designed",
    "ttf-r14-088": "hil",
    "ttf-r14-089": "simulated",
    "ttf-r14-090": "designed",
}
designed_n = sum(1 for v in mix.values() if v == "designed")
sim_n = sum(1 for v in mix.values() if v == "simulated")
hil_n = sum(1 for v in mix.values() if v == "hil")
out["checks"]["no_real"] = {
    "sim_or_real": sim_rows,
    "real_hits": real_hits,
    "training_ready": tr_hits,
    "mix": mix,
    "counts": {"designed": designed_n, "simulated": sim_n, "hil": hil_n},
    "pass": sim_ok and mix_ok and len(sim_rows) == 5 and designed_n == 3 and sim_n == 1 and hil_n == 1,
}

# meta.round=14 identity
id_rows = []
id_pass = True
for lineno, obj in records:
    rid = rec_id(obj)
    m = obj["meta"]
    errs = []
    if rid not in EXPECTED_IDS:
        errs.append(f"id {rid}")
    if m.get("round") != 14:
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
notes_text = NOTES.read_text() if NOTES.is_file() else ""
if NOTES.is_file():
    cov_err = validate_novel_coverage(NOTES, Path("/tmp/ttf-r14"), required=True)
else:
    cov_err = "NOTES-r14.md missing"
labeled = [
    line
    for line in re.split(r"\r\n|\n|\r", notes_text)
    if re.search(r"^[ \t]*novel[ _-]?coverage\b", line, re.I)
]
out["checks"]["notes_novel"] = {
    "validate_novel_coverage": cov_err,
    "labeled_lines": labeled,
    "n_labeled": len(labeled),
    "pass": cov_err is None and len(labeled) == 1 and bool(labeled),
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
out["checks"]["accept_identity"] = {"rows": accept_rows, "pass": accept_pass and len(accept_rows) >= 1}

# clone plants
clone_hits = []
blob = json.dumps([o for _, o in records])
notes_blob = notes_text
for name in BANNED_PLANTS:
    in_jsonl = name in blob
    in_notes = name in notes_blob
    if in_jsonl:
        clone_hits.append({"name": name, "jsonl": True, "notes": in_notes})
out["checks"]["no_banned_plants"] = {"hits": clone_hits, "pass": clone_hits == []}

# outputs/raw not written
raw_hits = []
for p in RAW.rglob("*"):
    if not p.is_file():
        continue
    name = p.name
    if "ttf-r14" in name.lower() or name in {"batch-r14.jsonl", "NOTES-r14.md"}:
        raw_hits.append(str(p))
rg = subprocess.run(
    ["rg", "-l", "ttf-r14-08[6-9]|ttf-r14-090", str(RAW)],
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
distinct = {d[1] for d in domains}
out_of_pool = sorted(d[1] for d in domains if d[1] not in DOMAIN_POOL)
paired = all(d[1] == d[2] for d in domains)
out["checks"]["domains"] = {
    "observed": domains,
    "distinct": sorted(distinct),
    "out_of_pool": out_of_pool,
    "pass": len(distinct) == 5 and paired,
}
out["checks"]["domain_pool"] = {
    "pool": sorted(DOMAIN_POOL),
    "out_of_pool": out_of_pool,
    "pass": out_of_pool == [],
}

# third_factor
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
    tf_rows.append({"id": rec_id(obj), "modulator": tf["modulator"], "errors": errs, "pass": ok})
out["checks"]["third_factor"] = {
    "rows": tf_rows,
    "modulators": mods,
    "pass": tf_pass and len(set(mods)) >= 4,
}

# NOTES vs record: 086 held 16.4 vs executed 14.0
notes_086_164 = "16.4 mmHg" in notes_text
out["checks"]["notes_086_hygiene"] = {
    "notes_claims_16_4": notes_086_164,
    "executed_infusion_mmHg": c086["executed_infusion"],
    "pass": (not notes_086_164) or abs(c086["executed_infusion"] - 16.4) < 1e-9,
}

# premises alignment
prem_rows = []
prem_pass = True
for _, obj in records:
    rid = rec_id(obj)
    exp = PREMISES_ASSIGN[rid]
    obs = {
        "domain": obj["state"]["domain"],
        "decision": obj["safety_decision"]["decision"],
        "correctness": obj["safety_decision"]["correctness"],
        "error": obj["meta"].get("supervisor_error_type"),
        "sim": obj["state"]["sim_or_real"],
    }
    errs = []
    for k, v in exp.items():
        if obs[k] != v:
            errs.append(f"{k} obs={obs[k]!r} exp={v!r}")
    ok = not errs
    prem_pass = prem_pass and ok
    prem_rows.append({"id": rid, "observed": obs, "expected": exp, "errors": errs, "pass": ok})
out["checks"]["premises_alignment"] = {
    "rows": prem_rows,
    "source": str(PREMISES),
    "pass": prem_pass,
}

# schema (optional)
schema_path = REPO / "schemas" / "thalamic-trajectory-v2.schema.json"
schema_rows = []
schema_pass = True
schema_err = None
try:
    import jsonschema  # noqa: F401
    from jsonschema import Draft202012Validator

    schema = json.loads(schema_path.read_text())
    validator = Draft202012Validator(schema)
    for _, obj in records:
        errs = [e.message for e in validator.iter_errors(obj)]
        ok = errs == []
        schema_pass = schema_pass and ok
        schema_rows.append({"id": rec_id(obj), "errors": errs[:8], "pass": ok})
except Exception as exc:  # noqa: BLE001
    schema_err = str(exc)
    schema_pass = False
out["checks"]["schema"] = {
    "rows": schema_rows,
    "error": schema_err,
    "pass": schema_pass and schema_err is None,
}

# episode_steps 8-15
ep_rows = []
ep_pass = True
for _, obj in records:
    steps = obj["state"].get("episode_steps") or []
    n = len(steps)
    ok = 8 <= n <= 15
    ep_pass = ep_pass and ok
    ep_rows.append({"id": rec_id(obj), "n": n, "pass": ok})
out["checks"]["episode_steps"] = {"rows": ep_rows, "pass": ep_pass}

failed = [k for k, v in out["checks"].items() if not v.get("pass")]
requested = [
    "check_jsonl",
    "check_line",
    "exact_json",
    "raster_status",
    "verify_batch_for_frontier",
    "spike_probe",
    "tick_sums",
    "refractory",
    "jaccard",
    "gate_mix",
    "rm793",
    "thought_keys",
    "no_real",
    "meta_identity",
    "notes_novel",
    "inflection_086",
    "wrong_modify_090",
]
req_failed = [k for k in requested if k in failed]
out["summary"] = {
    "n_checks": len(out["checks"]),
    "n_pass": sum(1 for v in out["checks"].values() if v.get("pass")),
    "failed": failed,
    "requested": requested,
    "requested_failed": req_failed,
    "all_pass": failed == [],
    "requested_all_pass": req_failed == [],
}

Path("/tmp/ttf-r14-audit-run.json").write_text(
    json.dumps(out, indent=2, default=str, sort_keys=False) + "\n"
)
print(json.dumps(out["summary"], indent=2))
print("failed:", failed)
print("requested_failed:", req_failed)
for k, v in out["checks"].items():
    print(f"{k}: {'PASS' if v.get('pass') else 'FAIL'}")
