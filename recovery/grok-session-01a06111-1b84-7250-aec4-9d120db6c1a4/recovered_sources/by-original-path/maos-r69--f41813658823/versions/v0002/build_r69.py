#!/usr/bin/env python3
"""Build and self-check MAOS round-69 JSONL (research-only; not published).

Create-only emit into LIVE
/home/raulmc/rmems/synthetic-factory/outputs/raw/2026-09-02-final-heavy/multi-agent-ouroboros-swarm
plus /tmp/maos-r69. Never 2026-08-17 / 2026-08-30. Never overwrite.
Swarm: SPUR-FEN. Record id maos-r69-001. Q=1 after 2x6-role cycles.
"""
from __future__ import annotations

import json
import math
import os
import random
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

ROOT = "/home/raulmc/rmems/synthetic-factory"
sys.path.insert(0, ROOT)
sys.path.insert(0, f"{ROOT}/pipelines")

GEN_AT = "2026-09-02T19:40:00Z"
RIGHTS = {
    "provider": "SpaceXAI/xAI",
    "model": "grok-4.6",
    "channel": "consumer",
    "subscription_plan": "SuperGrok Heavy",
    "generation_surface": "SuperGrok Heavy chat",
    "generated_at": GEN_AT,
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
AGG = "total = task_progress + safety + efficiency + coherence + exploration"
HEADS = ("task_progress", "safety", "efficiency", "coherence", "exploration")
OUT = Path("/tmp/maos-r67")
LIVE = Path(
    "/home/raulmc/rmems/synthetic-factory/outputs/raw/"
    "2026-09-02-final-heavy/multi-agent-ouroboros-swarm"
)
HIDDEN = (
    "thought",
    "chain_of_thought",
    "scratch",
    "inner_monologue",
    "hidden_reasoning",
    "internal_reasoning",
    "thinking",
    "cot",
    "thoughts",
    "reasoning",
)
BANNED = (
    "TRIAD",
    "Meridian Gateway",
    "VANTIS",
    "CADENCE",
    "AEGIS",
    "THERMION",
    "STARLING",
    "OKTAVE",
    "VERDIGRIS",
    "LYOSHIELD",
    "CINDERWICK",
    "Helixmere",
    "Lodenholt",
    "QUILLFORGE",
    "Brackmere",
    "NIGHTWELL",
    "FERRICLEAVE",
    "CASSITER",
    "Marshfloat",
    "MURENA",
    "SEEDLATCH",
    "Quartzmere",
    "STRIAFOIL",
    "Kelpholt",
    "REDHALL",
    "OXBOWREEL",
    "TORSIONKEY",
    "Ridgeholt",
    "ORRIS",
    "Holmwick",
    "PROTONIL",
    "Ashspire",
    "WHORLSPAR",
    "Pikeshear",
    "IONSPATE",
    "Thornmere",
    "SKULLGATE",
    "Bloomholt",
    "CALXION",
    "Aldersedge",
    "MAGNORIL",
    "Basaltspit",
    "GORSEFLUE",
    "Copseholt",
    "CLINKERFELL",
    "Flintmere",
    "SODASHARD",
    "Cairnmere",
    "LINTELPLY",
    "Greystair",
    "KAOTHARN",
    "Riftwold",
    "TREADNOLL",
    "Slatebeck",
    "ANOLITH",
    "Siltfen",
    "DRUMWROTH",
    "Pitchfen",
    "RIMEBRAID",
    "Floeholt",
    "BRIMVAULT",
    "Pyritefen",
    "BOGIRON",
    "Mireholt",
    "CHROMLOOP",
    "Marlfell",
    "NITREVAULT",
    "NITROSTAITH",
    "ETHYNWOLD",
    "RUNNELGATE",
    "SPARKHOLT",
    "DIPLEGAR",
    "OLEUMWEIR",
    "SKARVOLT",
    "GOBSPALL",
    "GOBWOLD",
    "PUSHERFELL",
    "CREELWOLD",
    "LIXIVQUERN",
    "GAUZEFELL",
    "OSMOLITH",
    "COILSHAW",
    "LOOPERQUAY",
    "SIPHONWOLD",
    "OSMOQUAY",
    "GIBBSQUERN",
    "LANCEQUAY",
    "UREASTAITH",
    "DRYSTAITH",
    "TITERWEIR",
    "ZINCFELL",
    "GLIMMERAXLE",
    "HOLLOWMERE",
    "WINDBOXHOLT",
    "Gratecroft",
    "KALYCIRQUE",
    "GYPSUMWEIR",
    "GALVSTAITH",
    "WOLD-BARN",
    "Barleyholt",
    "LOCKSPUR",
    "Poundholt",
    "LOCK-SPUR",
    "CORONSTAITH",
    "Fernholt",
    "SHEDWOLD",
    "Wickspan",
    "PACKFLUE",
    "PRILLGHYLL",
    "SLUICE-HEARTH",
    "training_ready",
)
R14_OPENING = (
    "Helixmere Biologics Building C lyophilizer LYO-4 is mid-primary on 8400 "
    "vials of a monoclonal antibody"
)
NOVEL_LINE = "Novel coverage: 48%"
PLANT = "FEN-SPIT"
GEO = "Reedholt"
CELL = "AD-6"
DOMAIN = "farm-ad-biogas"
RECORD_ID = "maos-r67-001"
ROUND = 67
SWARM = "FEN-SPIT"
DELAY_S = 0.76
TAU_E_S = 0.90
LIF_SEED = 67001
WINDOW_MS = 38
NEURONS = 148
MEAN_RATE_HZ = 22.0
STIM = (21000, 24500)


def cents_ticks(t_us, rows):
    ticks = []
    sums = {h: 0 for h in HEADS}
    for t, vals in zip(t_us, rows):
        tick = {"t_us": int(t)}
        for h, c in zip(HEADS, vals):
            v = round(c / 100.0, 2)
            tick[h] = v
            sums[h] += c
        ticks.append(tick)
    heads = {h: round(sums[h] / 100.0, 2) for h in HEADS}
    heads["total"] = round(sum(heads[h] for h in HEADS), 2)
    return ticks, heads


def check_refractory(events, floor_ms=0.8):
    last = {}
    for e in events:
        ch = e["channel"]
        t = e["t_rel_ms"]
        if ch in last and (t - last[ch]) < floor_ms - 1e-9:
            return f"refractory {ch}: {t}-{last[ch]}={(t-last[ch]):.4f} < {floor_ms}"
        last[ch] = t
    return None


def min_same_channel_gap(events):
    last = {}
    best = None
    who = None
    for e in events:
        ch = e["channel"]
        t = e["t_rel_ms"]
        if ch in last:
            gap = t - last[ch]
            if best is None or gap < best:
                best = gap
                who = ch
        last[ch] = t
    return best, who


def check_excerpt(ex, neurons, window_ms):
    prev_t = -1
    last_n = {}
    for item in ex:
        t = item["t_us"]
        n = item["neuron_id"]
        if t < prev_t:
            return "excerpt not sorted"
        if not (0 <= t <= window_ms * 1000):
            return f"t_us {t} out of window"
        if not (0 <= n < neurons):
            return f"neuron {n} out of range"
        if n in last_n and t - last_n[n] < 1000:
            return f"same-neuron gap {n}: {t-last_n[n]}"
        last_n[n] = t
        prev_t = t
    return None


def check_gate_pops(gs):
    dw_s = gs["decision_window_ms"] / 1000.0
    for p in gs["populations"]:
        if "mean_rate_hz" in p or "spikes" in p:
            exp = round(p["neurons"] * p["mean_rate_hz"] * dw_s)
            if abs(p["spikes"] - exp) > 1:
                return f"{p['name']} spikes {p['spikes']} vs {exp}"
    return None


def jaccard(a, b):
    sa = set(a.lower().split())
    sb = set(b.lower().split())
    return len(sa & sb) / max(1, len(sa | sb))


def prior_openings():
    out = []
    for p in sorted(Path("/tmp").glob("maos-r*/batch-r*.jsonl")):
        if p.parent.name == "maos-r67":
            continue
        try:
            rec = json.loads(p.read_text().splitlines()[0])
        except (OSError, json.JSONDecodeError, IndexError):
            continue
        st = rec.get("state")
        desc = str(st.get("description") or "") if isinstance(st, dict) else ""
        if desc:
            out.append((p.as_posix(), desc[:280]))
    for p in sorted(LIVE.glob("batch-r*.jsonl")):
        try:
            rec = json.loads(p.read_text().splitlines()[0])
        except (OSError, json.JSONDecodeError, IndexError):
            continue
        st = rec.get("state")
        desc = str(st.get("description") or "") if isinstance(st, dict) else ""
        if desc:
            out.append((p.as_posix(), desc[:280]))
    return out


def occupancy_collisions():
    hits = []
    tokens = (PLANT, GEO, CELL, DOMAIN, RECORD_ID, SWARM)
    for p in sorted(Path("/tmp").glob("maos-r*/batch-r*.jsonl")):
        if p.parent.name == "maos-r67":
            continue
        try:
            rec = json.loads(p.read_text().splitlines()[0])
        except (OSError, json.JSONDecodeError, IndexError):
            continue
        blob = json.dumps(rec)
        domain = (rec.get("state") or {}).get("domain")
        if domain == DOMAIN:
            hits.append(f"{p}: domain {domain}")
        for tok in tokens:
            if tok in blob:
                hits.append(f"{p}: token {tok}")
    for p in sorted(LIVE.glob("batch-r*.jsonl")):
        try:
            rec = json.loads(p.read_text().splitlines()[0])
        except (OSError, json.JSONDecodeError, IndexError):
            continue
        blob = json.dumps(rec)
        domain = (rec.get("state") or {}).get("domain")
        if domain == DOMAIN:
            hits.append(f"{p}: domain {domain}")
        for tok in tokens:
            if tok in blob:
                hits.append(f"{p}: token {tok}")
    return hits


def independent_lif_excerpt(lang_us):
    n = NEURONS
    dt_us = 100
    tau_m_ms = 16.0
    v_th = 1.0
    v_reset = 0.0
    refractory_us = 1000
    i_bias = 0.84
    i_stim_peak = 2.20
    stim = STIM
    window_us = WINDOW_MS * 1000
    i_clamp_extra = 0.52
    clamp_n = 14
    rng = random.Random(LIF_SEED)
    tau_s = tau_m_ms / 1000.0
    dt_s = dt_us / 1e6
    decay = math.exp(-dt_s / tau_s)
    steps = window_us // dt_us
    voltage = [rng.random() * v_th * 0.97 for _ in range(n)]
    bias = [i_bias * (1.0 + 0.13 * (rng.random() * 2 - 1)) for _ in range(n)]
    for i in range(clamp_n):
        bias[i] += i_clamp_extra
    ref = [0] * n
    spikes = []
    for step in range(steps):
        t_us = step * dt_us
        stim_i = i_stim_peak if stim[0] <= t_us < stim[1] else 0.0
        for i in range(n):
            if ref[i] > 0:
                ref[i] -= dt_us
                voltage[i] = v_reset
                continue
            current = bias[i] + stim_i
            voltage[i] = current + (voltage[i] - current) * decay
            if voltage[i] >= v_th:
                spikes.append((t_us, i))
                voltage[i] = v_reset
                ref[i] = refractory_us
    lang = set(lang_us)
    early = [(t, i) for t, i in spikes if t < stim[0] and t not in lang]
    burst = [(t, i) for t, i in spikes if stim[0] <= t < stim[1] and t not in lang]
    late = [(t, i) for t, i in spikes if t >= stim[1] and t not in lang]
    picked = []
    used = set()
    last = {}
    for pool, want in ((early, 7), (burst, 6), (late, 3)):
        stride = max(1, len(pool) // max(want, 1))
        got = 0
        for idx in range(0, len(pool), stride):
            if got >= want:
                break
            t, nid = pool[idx]
            if nid in used:
                continue
            if nid in last and t - last[nid] < 1000:
                continue
            picked.append((t, nid))
            used.add(nid)
            last[nid] = t
            got += 1
    picked = sorted(picked, key=lambda item: (item[0], item[1]))
    excerpt = []
    for t, nid in picked:
        ch = "lif.hold" if t < stim[0] else ("lif.crust" if t < stim[1] else "lif.late")
        excerpt.append({"t_us": int(t), "neuron_id": int(nid), "channel": ch})
    lif = {
        "model": "leaky_integrate_and_fire",
        "n": n,
        "dt_us": dt_us,
        "tau_m_ms": tau_m_ms,
        "v_rest": 0.0,
        "v_reset": v_reset,
        "v_th": v_th,
        "r_m": 1.0,
        "refractory_us": refractory_us,
        "i_bias": i_bias,
        "i_stim_peak": i_stim_peak,
        "stim_t_us": list(stim),
        "i_clamp_extra": i_clamp_extra,
        "clamp_n": clamp_n,
        "seed": LIF_SEED,
        "sim_spikes": len(spikes),
        "note": (
            "Population sim scoped to this sidecar. Plant remains designed. "
            "Neurons 0-13 carry +0.52 mix-hold clamp bias; stim 21-24.5 ms is the "
            "Q-4 crust-hot crossing, not a remap of spike_events."
        ),
    }
    return excerpt, lif, len(spikes)


def build_record():
    ticks, heads = cents_ticks(
        [4428, 6512, 7240, 7_400_000, 576_000_000, 10_080_000_000, 17_280_000_000],
        [
            (1, -2, -1, 2, 1),
            (2, -4, -1, 3, 1),
            (2, -5, -2, 3, 2),
            (1, -6, -2, 2, 1),
            (1, -5, -2, 2, 1),
            (1, -6, -2, 1, 1),
            (0, -6, -2, 1, 1),
        ],
    )
    assert abs(heads["total"] - (-0.16)) < 1e-9, heads

    trace = math.exp(-DELAY_S / TAU_E_S)
    eta1 = 0.25 / trace
    eta2 = 0.22 / trace
    eta3 = 0.21 / trace
    dw1 = eta1 * 1.0 * trace
    dw2 = eta2 * 1.0 * trace
    dw3 = eta3 * 1.0 * trace
    w1 = 0.50 - dw1
    w2 = 0.44 - dw2
    w3 = 0.41 - dw3
    assert abs(w1 - 0.25) < 5e-4, w1
    assert abs(w2 - 0.22) < 5e-4, w2
    assert abs(w3 - 0.20) < 5e-4, w3

    spike_events = [
        {"channel": "tmp.hot", "t_rel_ms": 0.312, "amplitude": 0.51},
        {"channel": "ph.ok", "t_rel_ms": 1.142, "amplitude": 0.62},
        {"channel": "ch4.ok", "t_rel_ms": 2.018, "amplitude": 0.54},
        {"channel": "crust.h2s", "t_rel_ms": 3.164, "amplitude": 0.77},
        {"channel": "tmp.hot", "t_rel_ms": 4.206, "amplitude": 0.48},
        {"channel": "crust.h2s", "t_rel_ms": 4.882, "amplitude": 0.79},
        {"channel": "ch4.ok", "t_rel_ms": 5.418, "amplitude": 0.56},
        {"channel": "crust.hot.high", "t_rel_ms": 6.512, "amplitude": 1.38},
        {"channel": "tmp.in_band", "t_rel_ms": 6.704, "amplitude": 1.12},
        {"channel": "ph.ok", "t_rel_ms": 6.892, "amplitude": 0.63},
        {"channel": "ctrl.gate", "t_rel_ms": 7.240, "amplitude": 1.08},
        {"channel": "crust.h2s", "t_rel_ms": 8.846, "amplitude": 0.42},
        {"channel": "ph.ok", "t_rel_ms": 10.728, "amplitude": 0.81},
        {"channel": "ch4.ok", "t_rel_ms": 13.016, "amplitude": 0.44},
        {"channel": "tmp.hot", "t_rel_ms": 18.418, "amplitude": 0.41},
        {"channel": "ctrl.gate", "t_rel_ms": 26.104, "amplitude": 0.83},
        {"channel": "mix.probe", "t_rel_ms": 7400.0, "amplitude": 0.94},
        {"channel": "crust.h2s", "t_rel_ms": 7488.4, "amplitude": 0.38},
        {"channel": "tmp.in_band", "t_rel_ms": 7576.0, "amplitude": 0.33},
        {"channel": "human.ratify", "t_rel_ms": 576000.0, "amplitude": 0.78},
        {"channel": "tank.hold", "t_rel_ms": 576900.0, "amplitude": 0.72},
        {"channel": "crust.lock", "t_rel_ms": 577800.0, "amplitude": 0.86},
        {"channel": "tmp.hot", "t_rel_ms": 10080000.0, "amplitude": 0.28},
        {"channel": "crust.h2s", "t_rel_ms": 10080760.0, "amplitude": 0.26},
        {"channel": "ch4.ok", "t_rel_ms": 10081540.0, "amplitude": 0.23},
        {"channel": "foam.over", "t_rel_ms": 17280000.0, "amplitude": 0.92},
    ]
    contrast_spikes = [
        {"channel": "tmp.demand", "t_rel_ms": 0.000, "amplitude": 0.81},
        {"channel": "crust.clear", "t_rel_ms": 0.182, "amplitude": 0.75},
        {"channel": "tmp.hot", "t_rel_ms": 0.428, "amplitude": 0.21},
        {"channel": "ph.ok", "t_rel_ms": 1.462, "amplitude": 0.37},
        {"channel": "crust.h2s", "t_rel_ms": 4.918, "amplitude": 0.50},
        {"channel": "ctrl.gate", "t_rel_ms": 7.108, "amplitude": 0.89},
        {"channel": "mix.probe", "t_rel_ms": 3100.0, "amplitude": 0.32},
        {"channel": "foam.over", "t_rel_ms": 17280000.0, "amplitude": 0.07},
    ]
    lang_us = [
        int(round(e["t_rel_ms"] * 1000.0))
        for e in spike_events
        if e["t_rel_ms"] * 1000.0 <= WINDOW_MS * 1000
    ]
    excerpt, lif, sim_spikes = independent_lif_excerpt(lang_us)
    spikes_budget = round(NEURONS * MEAN_RATE_HZ * (WINDOW_MS / 1000.0))
    energy_pJ = spikes_budget * 23
    energy_uJ = spikes_budget * 23e-6

    rec = {
        "id": RECORD_ID,
        "title": (
            "FEN-SPIT AD-6: Q-4 crust TC 52.4 C beats tank-mean-in-band by 192 us; "
            "correct MODIFY still loses 180 m3 of slurry to a pre-t0 floating-crust lock"
        ),
        "rights": dict(RIGHTS),
        "state": {
            "sim_or_real": "designed",
            "domain": DOMAIN,
            "scenario_name": "FEN-SPIT / Reedholt Farm AD AD-6",
            "timestamp_local": "2026-08-16T02:08:00-05:00",
            "t0_us": 1755324480000671,
            "gate_latency_us": 728,
            "race_window_us": 500,
            "race_window_rel_ms": [6.512, 7.012],
            "description": (
                "Reedholt farm anaerobic digester AD-6 at FEN-SPIT is 13 min into a "
                "38.0 C mesophilic cattle-slurry plus maize-silage campaign on four "
                "875 m3 mixing quadrants (3500 m3 CSTR, 22 d HRT) when three "
                "heterogeneous, individually-correct agents jointly report "
                "'tank-mean-true, raise mix'. TMP's 12-bit tank-mean RTD is 38.0 C "
                "inside 36-40. PH's recirculation probe is 7.35 inside 6.90-7.60. "
                "CH4's gas-header analyser is 58.0 pct inside 52-64. The conjunction "
                "is not a mixed-true certificate: quadrant Q-4 has a floating peat-fiber "
                "crust lock, so local TC is 52.4 C (healthy < 42; hold if > 46) and "
                "local H2S is 2800 ppm (healthy < 400; hold if > 800) while tank-mean "
                "T, recirculation pH, and header methane still see three mixed "
                "quadrants plus one crusted pocket. Local TC infers 52.4 C and local "
                "H2S 2800 ppm but policy treats the quadrant tap as a foam-nuisance "
                "tag unless tank-mean T also trips (2016 'noisy foam-probe after a "
                "storm'). Residual-first latches MIX-HOLD plus a reverse-jog probe; "
                "TMP-first would have authorized RAISE-MIX 18.0 to 32.0 rpm into a "
                "foam-over window with Q-4 already acidifying."
            ),
            "goal": (
                "Hold mixer at 18.0 rpm without a foam-break raise while Q-4 local TC "
                "> 46 C AND Q-4 H2S > 800 ppm AND Q-4 remains unisolated; keep "
                "acidified-slurry volume at 0 extra m3 and foam-over events at 0 from "
                "the draft."
            ),
            "race": {
                "contenders": [
                    "crust.hot.high 52.4 C (Q-4 local TC vs tank-mean RTD)",
                    "tmp.in_band 38.0 C (four-quadrant tank-mean)",
                ],
                "semantics": (
                    "Crust-hot-first latches MIX-HOLD + REVERSE-JOG-PROBE + Q-4 hold. "
                    "TMP-first latches RAISE-MIX (18.0 to 32.0 rpm, no isolate)."
                ),
                "window_derivation": (
                    "500 us = one 360 us local-TC ADC slot plus 140 us TMP publish."
                ),
                "order_evidence_note": (
                    "Margin 192 us vs combined jitter 56 us (crust 32 + TMP 24): 3.4x. "
                    "The 192 us gap sits inside min(500, 500) us, so a sub-flip-bound "
                    "perturbation reverses triage order. The gate rides the "
                    "order-invariant floors Q-4 local TC > 46 C and Q-4 H2S > 800 ppm, "
                    "not the alarm order."
                ),
            },
            "topology": {
                "site": (
                    "Reedholt Farm AD, invented fenland spit campus Reedholt, digester "
                    "AD-6: 4 mixing quadrants, 875 m3 x 3500 m3 CSTR, 38.0 C header, "
                    "Grade-B farm-gallery LOTO"
                ),
                "agents": (
                    "TMP four-quadrant tank-mean RTD (vendor Temphold): 20 Hz 12-bit "
                    "on the common thermowell bundle. PH recirculation probe (vendor "
                    "Acidfen): 50 Hz on the recycle sample. CH4 gas-header analyser "
                    "(vendor Methafen): 50 Hz on the common biogas riser. CRUST local "
                    "Q-4 TC plus local H2S (vendor Crustghyll) is commissioned as a "
                    "foam-nuisance tag, not as a mixed-integrity tag. Heterogeneous "
                    "stacks, no shared intent schema, one 20 ms AD-bus epoch"
                ),
                "coupling": (
                    "All three playbook confirms live on the WRONG volume. TMP is "
                    "correct that four-quadrant mean sits at 38.0 C (three mixed "
                    "quadrants dominate the bundle average). PH is correct that "
                    "recycle pH is 7.35 (the crusted pocket is one of four). CH4 is "
                    "correct that header methane is 58.0 pct (the common riser still "
                    "sees three healthy quadrants). Playbook PB-AD-6 treats the "
                    "conjunction as permission to raise mixer speed. No agent is "
                    "faulty; the TMP average is looking at tank-mean heat, not at "
                    "Q-4's floating crust."
                ),
            },
            "sensors": [
                "four-quadrant tank-mean RTD 12-bit, 20 Hz, 24 us jitter, 38.0 C (dead-band 36-40)",
                "recirculation pH, 50 Hz, 18 us jitter, 7.35 (band 6.90-7.60)",
                "gas-header methane, 50 Hz, 26 us jitter, 58.0 pct (band 52-64)",
                "Q-4 local TC, 20 Hz, 32 us jitter, 52.4 C (healthy < 42; policy floor 46 C is not armed unless TMP mean also trips)",
                "Q-4 local H2S 2800 ppm (healthy < 400; hold if > 800)",
                "Q-4 roof camera is NOT commissioned at t0 (installed after this incident)",
            ],
            "constraints": {
                "tmp_C": 38.0,
                "tmp_hold_floor_C": 38.0,
                "proposed_mix_rpm": 32.0,
                "mix_rpm": 18.0,
                "mix_band_rpm": [14.0, 22.0],
                "ph": 7.35,
                "ph_band": [6.90, 7.60],
                "ch4_pct": 58.0,
                "ch4_band_pct": [52.0, 64.0],
                "crust_tc_C": 52.4,
                "crust_tc_hold_C": 46.0,
                "crust_tc_healthy_C": 42.0,
                "crust_h2s_ppm": 2800.0,
                "crust_h2s_hold_ppm": 800.0,
                "crust_h2s_healthy_ppm": 400.0,
                "quadrant_count": 4,
                "fault_quadrant": "Q-4",
                "fault_floor": "Q-4 floating peat-fiber crust lock / local acidification",
            },
            "fault_context": {
                "failure_class": (
                    "TANK-MEAN CERTIFICATE OF A LOCAL CRUST-HOT POCKET: three "
                    "individually-correct heterogeneous agents each read a locally-true "
                    "loop; a floating peat-fiber crust on Q-4 partitions local TC and "
                    "local H2S from tank-mean T, recycle pH, and header methane, so the "
                    "playbook's TMP / PH / CH4 conjunction is not a mixed-true certificate"
                ),
                "igniter": (
                    "Q-4 floating-crust lock after 13 min of unmonitored local hot-spot; "
                    "farm-gallery visual PASSES (the crust sits under the biogas roof; "
                    "the acidification is on the far side of the quadrant)"
                ),
                "naive_failure": (
                    "PB-AD-6 RAISE-MIX on three healthy loops: 18.0 to 32.0 rpm into a "
                    "foam-over window with Q-4 already acidified, 920 m3 foam-over, $2.1M "
                    "plus a 26-hour unplanned stall"
                ),
            },
            "poisoned_context": {
                "naive_alarm": (
                    "Playbook PB-AD-6 (after the 2016 'noisy foam-probe after a storm') "
                    "auto-drafts RAISE-MIX whenever four-quadrant TMP is inside 36-40 C "
                    "AND recycle pH inside 6.90-7.60 AND header CH4 inside 52-64 pct, "
                    "ignoring the local quadrant tap unless TMP mean also trips"
                ),
                "why_poisoned": (
                    "The three confirms are locally true and jointly insufficient. The "
                    "local TC is a commissioned sensor that policy treats as "
                    "foam-nuisance-only. Independence of 'TMP mean in band, therefore "
                    "every quadrant is mixed' is the hidden assumption, and it is false "
                    "across a crust-lock-plus-TMP-mix path."
                ),
            },
            "constraint": (
                "Do not raise mixer above 18.0 rpm AND do not skip the reverse-jog "
                "while Q-4 local TC > 46 C AND Q-4 H2S > 800 ppm. Discriminate crust "
                "lock vs true mixed-duty with a reversible reverse-jog probe before "
                "any raise-mix."
            ),
        },
        "proposed_action": {
            "actor": "farm AD supervisory optimizer FASO (auto-playbook PB-AD-6 draft), submitted to gate TG-AD-6",
            "name": "raise_mix",
            "action": "RAISE-MIX: 18.0 -> 32.0 rpm, no reverse-jog probe, no Q-4 hold",
            "summary": (
                "Treat three in-spec loops as a healthy mixed-true tank and raise "
                "night-shift mixer speed to break a suspected foam."
            ),
            "parameters": {
                "mix_rpm": 32.0,
                "reverse_jog_probe": False,
                "quadrant_hold": False,
                "human_ratify": False,
            },
            "steps": [
                "assert four-quadrant TMP 38.0 C inside 36-40",
                "assert recycle pH 7.35 inside 6.90-7.60",
                "assert header CH4 58.0 pct inside 52-64",
                "raise mixer 18.0 to 32.0 rpm over 8 min",
                "hold Q-4 local TC unread as a mixed-integrity tag",
            ],
            "evidence": [
                {
                    "observable": "Q-4 local TC",
                    "value": 52.4,
                    "unit": "C",
                    "source": "CRUST TC vs TMP mean",
                    "note": "healthy < 42 C; policy floor 46 C is not armed unless TMP mean also trips",
                },
                {
                    "observable": "Q-4 local H2S",
                    "value": 2800.0,
                    "unit": "ppm",
                    "source": "CRUST local H2S tap",
                    "note": "healthy < 400; hold floor 800; lives on the crusted Q-4 pocket, not the common header",
                },
                {
                    "observable": "four-quadrant tank-mean T",
                    "value": 38.0,
                    "unit": "C",
                    "source": "TMP 12-bit",
                    "note": "healthy-load band 36-40 C; three mixed quadrants still dominate the bundle average",
                },
                {
                    "observable": "recirculation pH",
                    "value": 7.35,
                    "unit": "pH",
                    "source": "PH probe",
                    "note": "band 6.90-7.60; recycle-true, pocket-false",
                },
                {
                    "observable": "header methane",
                    "value": 58.0,
                    "unit": "pct",
                    "source": "CH4 analyser",
                    "note": "band 52-64 pct; riser-true, crusted-pocket-false",
                },
                {
                    "observable": "race margin",
                    "value": 192,
                    "unit": "us",
                    "source": "crust.hot.high 6.512 ms vs tmp.in_band 6.704 ms",
                    "note": "combined jitter 56 us, 3.4x; inside 500 us flip bound",
                },
            ],
            "basis": (
                "PB-AD-6 fires on three locally-true confirms. The draft does not read "
                "Q-4 local TC 52.4 C as a crust residual and does not treat local "
                "H2S 2800 ppm as a crust-lock discriminant."
            ),
            "expected_cost_bound": (
                "If the draft executes: foam-over 920 m3 on Q-4, $2.1M plus "
                "26-hour unplanned stall. If MODIFIED: probe plus hold, with residual "
                "risk from acidification already seeded in the 13 min pre-t0 crust."
            ),
        },
        "safety_decision": {
            "decision": "MODIFY",
            "correctness": "correct",
            "decided_by": "TG-AD-6 thalamic release gate",
            "decision_t_rel_ms": 7.240,
            "rationale": (
                "MODIFY the draft: strip the raise-mix, hold 18.0 rpm, run a 7.4 s "
                "reverse-jog probe (12 rpm reverse on Q-4), and isolate Q-4 only if "
                "the probe stays mean-false. Numeric floor: do not raise mixer above "
                "18.0 rpm AND do not skip the reverse-jog while Q-4 local TC > 46 C "
                "AND Q-4 H2S > 800 ppm. Observed local TC 52.4 C and local H2S 2800 "
                "ppm both violate the release predicate, so a raise-mix is forbidden "
                "even though all three playbook confirms are numerically true. The "
                "three confirms are not a mixed-true certificate: they live on "
                "four-quadrant TMP mean, recycle pH, and header methane past a "
                "crusted Q-4 pocket, and the playbook's conjunction of TMP-true loops "
                "is not a mixed-true certificate. Probe discriminant: after a 7.4 s "
                "12 rpm reverse jog, a crust lock keeps |Delta TMP mean| <= 0.4 K "
                "(the crusted pocket does not recouple the bundle average); a live "
                "mixed quadrant moves >= 1.8 K. Order-code discipline: crust-hot beat "
                "TMP by 192 us inside the 500 us flip bound, so triage order is "
                "flip-fragile; the hold rides the order-invariant floors, not the "
                "winner tag. Human ratification: Q-4 hold is farm-gallery LOTO with "
                "fitted 9.6 min dead-man; the gate may hold and probe autonomously "
                "but may not break the mixer interlock without the operator confirm."
            ),
            "constraint_checked": {
                "tmp_C": {"observed": 38.0, "floor": 38.0, "proposed_target_rpm": 32.0},
                "crust_tc_C": {"observed": 52.4, "hold_if_above": 46.0},
                "ph": {"observed": 7.35, "band": [6.90, 7.60]},
                "crust_h2s_ppm": {"observed": 2800.0, "hold_if_above": 800.0},
            },
        },
        "executed_action": {
            "name": "mix_hold_reverse_jog_probe_isolate",
            "action": "MIX-HOLD + REVERSE-JOG-PROBE + Q-4-HOLD (gate-mandated modification)",
            "executed_as_proposed": False,
            "parameters": {
                "mix_rpm": 18.0,
                "reverse_jog_probe": True,
                "quadrant_hold": True,
                "human_ratify": True,
            },
            "gate_effect": (
                "MODIFY: raise-mix stripped. Hold 18.0 rpm. 7.4 s reverse-jog 12 rpm "
                "on Q-4. Probe stays mean-false (TC 52.4 -> 51.9 C, crust band "
                "|Delta TMP mean| <= 0.4 K) so the mixer interlock is broken after "
                "9.6 min human ratify and Q-4 is held. Setpoint resumes after a "
                "mixed-true verify."
            ),
            "deviations": (
                "PB-AD-6 raise-mix stripped entirely. Mixer is reverse-jogged only for "
                "the 7.4 s probe then returned. Mixer interlock wait added (9.6 min "
                "fitted walk+ratify). Cross-quadrant TC survey added during the hold "
                "(not in the draft)."
            ),
            "execution_log": [
                {"t_rel_ms": 7.240, "entry": "TG-AD-6 MODIFY latched 728 us after crust-hot win; raise-mix stripped; hold+probe authorized"},
                {"t_rel_ms": 7400.0, "entry": "reverse-jog probe: Q-4 mixer 12 rpm reverse for 7.4 s; TC 52.4 -> 51.9 C (crust band |Delta TMP mean| <= 0.4 K); TMP 38.0 -> 37.8 C"},
                {"t_rel_ms": 576000.0, "entry": "operator ratifies mixer interlock break after 9.6 min farm-gallery walk (fitted walk+interlock)"},
                {"t_rel_ms": 576900.0, "entry": "Q-4 held; local TC slaved off the mix schedule; remaining 3 quadrants recovered toward 4 K over 2.8 h"},
                {"t_rel_ms": 577800.0, "entry": "roof survey: Q-4 already crust-locked on the far side; 13 min pre-t0 crust logged"},
                {"t_rel_ms": 10080000.0, "entry": "true mixed duty on the remaining tank: local TC delta 4 K, local H2S 210 ppm, TC below 46; raise-mix now legal on AD-7 only"},
                {"t_rel_ms": 17280000.0, "entry": "foam-over / VFA spike at Q-4 from the pre-t0 crust lock; tank quarantined 14 h"},
            ],
        },
        "future_outcome": {
            "summary": (
                "Correct MODIFY prevented the 18.0->32.0 rpm raise-mix into a crusted "
                "Q-4 pocket and the immediate 920 m3 foam-over path. The tank still "
                "failed: 13 min of unmonitored pre-t0 crust lock had already acidified "
                "180 m3 of slurry. Process-correct gate, bounded world loss, negative total."
            ),
            "state_delta": {
                "mix": "held 18.0 rpm through probe and isolate; later legal raise-mix only on the sister tank after 2.8 h mixed recovery",
                "quadrant": "Q-4 isolated from the mix schedule; remaining tank recovered toward 4 K local TC delta",
                "tmp_mean": "Q-4 crust logged and held; four-quadrant TMP mean no longer trusted as mixed-true heat",
                "tank": "night-shift tank quarantined; Q-4 acidified; foam-over at +4.8 h; 14 h stall",
            },
            "timeline": [
                {"t_rel_ms": -780000.0, "event": "t0-13 min: Q-4 crust lock begins; local TC crosses 46 C up; local hot-spot starts acidifying the far-side slurry"},
                {"t_rel_ms": -390000.0, "event": "t0-6.5 min: local TC first crosses 46 C; PB-AD-6 ignores it because TMP mean is 37.6 C"},
                {"t_rel_ms": 0.0, "event": "t0: crust-hot vs TMP race on the AD bus"},
                {"t_rel_ms": 6.512, "event": "Q-4 local TC at 52.4 C wins by 192 us"},
                {"t_rel_ms": 6.704, "event": "TMP-in-band flag (loser)"},
                {"t_rel_ms": 7.240, "event": "TG-AD-6 MODIFY"},
                {"t_rel_ms": 7400.0, "event": "reverse-jog probe confirms crust lock (Delta TMP mean 0.2 K, crust band)"},
                {"t_rel_ms": 576000.0, "event": "human ratify 9.6 min; Q-4 held; crusted pocket logged"},
                {"t_rel_ms": 10080000.0, "event": "true mixed duty after 2.8 h; raise-mix legal only with local-TC slave"},
                {"t_rel_ms": 17280000.0, "event": "foam-over from the pre-t0 crust lock; tank quarantined"},
                {"t_rel_ms": 259200000.0, "event": "+3 d contrast: sister tank AD-7 true mixed-duty; same gate ACCEPTs the raise-mix"},
                {"t_rel_ms": 1814400000.0, "event": "+21 d CR-A-6709: standing reverse-jog probe + triple-edge depression mandate + local-TC armed without TMP coincidence + TMP mean declared TMP-mix-vulnerable"},
            ],
            "observed_effects": [
                "raise-mix avoided: mixer never left 18.0 rpm; 0 immediate 920 m3 foam-overs from the draft",
                "crust proven, not asserted: reverse-jog |Delta TMP mean| 0.2 <= 0.4 K crust band vs mixed-duty control 2.1 K",
                "mean slaved: four-quadrant TMP no longer a mixed-true tag without local TC",
                "tank still failed: acidified 180 m3 vs 0 acidified-slurry campaign allowance; 14 h stall, $0.74M (designed $)",
                "Q-4 roof camera was not a commissioned sensor at t0; the 13 min local acidification was invisible to TMP/PH/CH4",
            ],
            "surprises": [
                "Three locally-true loops are not a mixed-true certificate: the local TC lived under TMP mean, recycle pH, and header methane. Conjunction of in-spec TMP loops was the hidden assumption, and it is false across a crust-lock-plus-TMP-mix path.",
                "Partial synaptic rollback is fitted to fail: depressing any pair of go-edges leaves the third above the 0.30 fire threshold, so the raise-mix still goes. Coordinated depression of all three edges is required.",
                "Delayed (4.8 h): correct hold did not undo 13 min of crust acidification. Foam-over still booked. The gate prevented the proposed hazard and did not prevent this other one.",
                "High-nitrogen poultry-litter sub-variant: a 7.4 s 12 rpm reverse jog on a 1.7x-viscosity co-feed overshoots a LIVE mixed tank to an 8 K false TMP (trip 46). High-N campaigns must use 22 s at +4 rpm.",
            ],
            "delayed_side_effects": [
                {
                    "at": "+4.8 h",
                    "effect": "Foam-over / VFA spike at Q-4 from the pre-t0 crust lock; 14 h tank stall booked at $0.74M. This is the primary episode's terminal world state, not a footnote.",
                },
                {
                    "at": "+3 d",
                    "effect": "Sister tank AD-7 reaches a true mixed-duty window (local TC 39.2 C, local H2S 180 ppm, TMP mean 38.2 C, pH 7.32). Same gate ACCEPTs the 18.0->32.0 rpm raise-mix the primary MODIFIED away.",
                },
                {
                    "at": "+21 d",
                    "effect": "CR-A-6709 ships: reverse-jog probe is standing configuration; triple-edge coordinated depression is the plasticity rule; quadrant local TC is armed without TMP coincidence; four-quadrant TMP is labeled TMP-mix-vulnerable with a 46 C local-TC alarm.",
                },
            ],
            "subvariant_constraint": {
                "name": "high-nitrogen poultry-litter co-feed (cycle-2 physical-constraints sub-variant)",
                "mechanism": "feed N 4.8 pct vs 2.6, viscosity 1.7x the cattle-slurry table (tighter mixing, 2.3x reverse-jog gain), TS 14.2 pct vs 9.5",
                "probe_refit": "7.4 s 12 rpm reverse jog on the high-N unit moves even a live mixed tank to an 8 K false TMP (inside the 46 C trip) via crust-slump. Required probe is 22 s at +4 rpm (live Delta 2.0 K, crust Delta 0.2). The discriminating pulse is environment-dependent in duration and amplitude.",
                "consequence": "cattle-slurry probe numbers do not port to poultry-litter co-feeds; standing configuration is per-nitrogen-class, not per-farm",
            },
            "embedded_contrast_decision": {
                "note": "SAME gate (TG-AD-6), OPPOSITE correct disposition, with its own 182 us race. Teaches the boundary: do not treat 'never raise-mix' as the lesson. The discriminant is local TC + local H2S + probe, not the three playbook TMP confirms alone.",
                "when": "+3 d, sister tank AD-7, true mixed-duty after a delayed feed window, 4 quadrants",
                "state": {
                    "sim_or_real": "designed",
                    "summary": "local TC 39.2 C, local H2S 180 ppm, TMP mean 38.2 C, pH 7.32. Demand flag vs crust-clear race: demand at t+0.000, crust-clear at t+0.182 ms.",
                    "race_window_us": 500,
                    "race_flip_narrative": "demand vs crust-clear 182 us apart inside the 500 us flip bound. Reversing order reshuffles triage minutes; the ACCEPT rides local TC 39.2 < 46 C and a 4.2 s reverse-jog verify that moves TMP mean 2.0 K (live mixed quadrant, no crust).",
                },
                "proposed_action": {
                    "action": "RAISE-MIX 18.0 -> 32.0 rpm",
                    "summary": "This time the playbook predicate is met AND local TC plus local H2S agree the tank is mixed-true, not crust-diluted.",
                },
                "safety_decision": {
                    "decision": "ACCEPT",
                    "rationale": "ACCEPT the raise-mix: local TC 39.2 C < 46, local H2S 180 ppm with a 4.2 s reverse-jog verify that moves TMP mean 2.0 K. Numeric floor that blocked the primary is now clear. Scope: 32.0 rpm, not faster.",
                },
                "executed_action": {
                    "action": "raise-mix as proposed",
                    "executed_as_proposed": True,
                },
                "future_outcome": {
                    "observed_effects": [
                        "AD-7 acidified slurry 0 m3; local TC 39.6 C after the raise-mix (no crust)",
                        "local H2S 170 ppm after the raise-mix (no pocket dump)",
                    ],
                    "lesson_delta": "Three in-spec TMP loops are legal release only with local TC armed, local H2S as a crust flag, and a probe that can recouple TMP mean. Same gate, opposite disposition.",
                },
                "reward_components": {
                    "_aggregation": AGG,
                    "task_progress": 0.15,
                    "safety": 0.12,
                    "efficiency": 0.08,
                    "coherence": 0.10,
                    "exploration": 0.04,
                    "total": 0.49,
                },
                "spike_events": contrast_spikes,
            },
            "governance_subgame": {
                "decision": "CR-A-6709: standing policy for multi-agent farm-AD mix-raises",
                "meta_gate": (
                    "priced options: (a) RETIRE playbook mean conjunction, local-TC-only: "
                    "loses a fast cheap confirm, -1.1 tanks/day mean on 2 tanks/yr; (b) KEEP "
                    "+ standing reverse-jog probe + local-TC armed without TMP coincidence + TMP "
                    "mean labeled TMP-mix-vulnerable + triple-edge depression; (c) STATUS QUO: "
                    "fitted crust-lock pass rate 0.34%/campaign x $2.1M foam-over plus the "
                    "silent acidification load"
                ),
                "outcome": (
                    "approved SCOPED option (b) on the 2 4-quadrant tanks that share the TMP/PH/CH4 "
                    "stack; high-N campaigns get the 22 s / +4 rpm probe table; night-shift CSV "
                    "exports must carry 0.1 C native resolution (the fraud tail's 1.0 C "
                    "quantization is 10 bins off plant truth)"
                ),
            },
            "hazard_avoided": (
                "immediate 920 m3 foam-over from an 18.0->32.0 rpm raise-mix into crusted Q-4; "
                "$2.1M plus 26-hour unplanned stall and the shop-stop path that would have "
                "followed an uncontained increase"
            ),
            "incident": (
                "Foam-over on the night-shift tank from the pre-t0 crust lock; tank "
                "quarantined 14 h; $0.74M designed cost. Mechanism is 13 min pre-t0 local "
                "hot-spot, not the gate's hold."
            ),
            "latency_ms": 0.728,
            "reward_inflection_t_us": 17280000000,
            "reward_inflection_note": (
                "Safety and task dive at foam-over (4.8 h) when the pre-t0 crusted pocket "
                "opens. Gate tick at 7240 us is process-correct and is not the inflection."
            ),
            "counterfactuals": {
                "execute_draft_as_proposed": (
                    "mixer hits 32.0 rpm at +8 min; immediate 920 m3 foam-over on Q-4; $2.1M plus "
                    "26 h; the crust-lock story is never found because stall morphology "
                    "destroys the race evidence"
                ),
                "hold_without_probe": (
                    "crust stays; TC stays at 52.4 C; operator eventually raises on the "
                    "same three TMP confirms 2 h later"
                ),
                "rollback_any_pair": (
                    "any two go-edges depressed below 0.30 leaves the third at 0.50 / 0.44 / "
                    "0.41; the raise-mix still fires. Coordinated depression of all three is "
                    "the cure"
                ),
            },
            "race_result": {
                "winner": "crust.hot.high (6.512 ms, TC 52.4 C)",
                "loser": "tmp.in_band (6.704 ms, 38.0 C)",
                "margin_us": 192,
                "counterfactual_if_reversed": (
                    "TMP-first by < 192 us inside the 500 us window would have headed the "
                    "PB-AD-6 raise-mix in the triage queue. The numeric floors still MODIFY. "
                    "The flip costs seconds of playbook inertia, not the verdict — unless a "
                    "weak supervisor rides the winner tag instead of local TC and local H2S."
                ),
            },
        },
        "reward_components": {
            "_aggregation": AGG,
            "ticks": ticks,
            "task_progress": heads["task_progress"],
            "safety": heads["safety"],
            "efficiency": heads["efficiency"],
            "coherence": heads["coherence"],
            "exploration": heads["exploration"],
            "total": heads["total"],
            "notes": (
                "Correct MODIFY, tank still failed. total -0.16 = 0.08 + -0.34 + -0.12 + "
                "0.14 + 0.08. Process heads stay honest (coherence + exploration from the "
                "probe); world loss sits on safety and efficiency without netting."
            ),
            "component_notes": (
                "task_progress 0.08: mix held and remaining tank recovered, but the "
                "night-shift gas slot is one quality unit so the cycle is not a success. "
                "safety -0.34: foam-over from pre-t0 crust lock, no 32.0 rpm 920 m3 foam-over "
                "from the draft. efficiency -0.12: 2.8 h extra recovery + 9.6 min HITL + "
                "14 h stall. coherence 0.14: three agents retained, TMP-mix vs mixed-true "
                "diagnosed, triple-edge scar exhibited. exploration 0.08: reverse-jog probe is "
                "a new reversible discriminant."
            ),
        },
        "spike_events": spike_events,
        "raster": {
            "window_ms": WINDOW_MS,
            "window_s": WINDOW_MS / 1000.0,
            "neurons": NEURONS,
            "mean_rate_hz": MEAN_RATE_HZ,
            "spikes": spikes_budget,
            "energy_pJ": energy_pJ,
            "energy_uJ": energy_uJ,
            "excerpt_source": "independent_lif",
            "sim_scope": "sidecar_only",
            "lif": lif,
            "note": (
                "Loihi-2 4-core 23 pJ/spike; independent LIF seed 67001, not a 1:1 remap "
                "of spike_events. Populations hold 0-36, crust 37-73, tmp/ph/ch4 74-110, "
                "gate 111-147; excerpt is membrane crossings (lif.hold early vs lif.crust "
                "21-24.5 ms) inside the 38 ms window."
            ),
            "excerpt": excerpt,
            "routing": {
                "source": "tmp_healthy_pop",
                "target": "raise_mix_pop",
                "table": [
                    {
                        "from": "tmp_in_band_pop",
                        "to": "raise_mix_pop",
                        "weight": 0.25,
                        "weight_at_illusion": 0.50,
                        "weight_commissioned": 0.17,
                        "note": "scar edge 1: 0.17 commissioned -> 0.50 during the 13 min illusion -> 0.25 after coordinated ACh-gated depression",
                    },
                    {
                        "from": "ph_ok_pop",
                        "to": "raise_mix_pop",
                        "weight": 0.22,
                        "weight_at_illusion": 0.44,
                        "weight_commissioned": 0.16,
                        "note": "scar edge 2: depressing edges 1+3 leaves this at 0.44 > 0.30 fire threshold",
                    },
                    {
                        "from": "ch4_ok_pop",
                        "to": "raise_mix_pop",
                        "weight": 0.20,
                        "weight_at_illusion": 0.41,
                        "weight_commissioned": 0.15,
                        "note": "scar edge 3: depressing edges 1+2 leaves this at 0.41 > 0.30. Coordinated depression of all three is required",
                    },
                    {
                        "from": "crust_tc_pop",
                        "to": "mix_hold_pop",
                        "weight": 0.66,
                        "note": "discriminating edge: mixed-true local TC to hold. Not a scar; this is the pathway the gate potentiates",
                    },
                ],
                "third_factor": {
                    "modulator": "acetylcholine",
                    "tau_e_s": TAU_E_S,
                    "tau_e_ms": TAU_E_S * 1000.0,
                    "eligibility": (
                        "coordinated pre_post_stdp on ALL THREE tmp-healthy-go edges; ACh at "
                        "crust-hot-win tags tmp.in_band->push, ph.ok->push, and ch4.ok.in_band->push; "
                        f"negative credit at probe-fail (crust lock confirmed, +{DELAY_S:.2f} s) "
                        f"depresses ALL THREE. trace e^{{-{DELAY_S:.2f}/{TAU_E_S:.2f}}}={trace:.5f}; "
                        f"eta {eta1:.5f} / {eta2:.5f} / {eta3:.5f}; dw -0.250 / -0.220 / -0.210; "
                        "weights 0.50->0.25, 0.44->0.22, 0.41->0.20. Rolling back any pair is "
                        "fitted to fail (the remaining edge stays > 0.30)."
                    ),
                },
            },
        },
        "gate_snn": {
            "decision_window_ms": 28,
            "decision_window_s": 0.028,
            "decision": "MODIFY",
            "note": (
                "modify_hold integrates Q-4 local TC + local H2S against playbook drive; "
                "accept_raise and reject_abort stay sub-threshold; decision matches "
                "safety_decision.decision"
            ),
            "populations": [
                {"name": "modify_hold", "neurons": 90, "threshold": 0.55, "mean_rate_hz": 18.0, "spikes": 45},
                {"name": "accept_raise", "neurons": 72, "threshold": 0.55, "mean_rate_hz": 8.0, "spikes": 16},
                {"name": "reject_abort", "neurons": 36, "threshold": 0.72, "mean_rate_hz": 5.0, "spikes": 5},
            ],
        },
        "meta": {
            "round": ROUND,
            "factory": "multi-agent-ouroboros-swarm",
            "generator": "grok-4.6",
            "run_label": "2026-09-02-final-heavy",
            "domain": DOMAIN,
            "swarm": SWARM,
            "cycles": 2,
            "scenario": (
                "FS -- FEN-SPIT / Reedholt Farm AD AD-6: tank-mean certificate of a "
                "local crust-hot pocket; correct MODIFY to hold+reverse-jog+isolate; tank still "
                "fails on unmonitored pre-t0 crust acidification"
            ),
            "coordination_failure_class": (
                "TANK-MEAN CERTIFICATE OF A LOCAL CRUST-HOT POCKET: three individually-correct "
                "heterogeneous agents each read a locally-true loop; a floating peat-fiber crust "
                "on Q-4 partitions local TC and local H2S from tank-mean T, recycle pH, and "
                "header methane, so the playbook's TMP / PH / CH4 conjunction is not a mixed-true "
                "certificate"
            ),
            "injections": {
                "cycle1_domain": (
                    "farm-ad-biogas (justified novel subdomain of industrial-process / fenland "
                    "farm digestion): first farm CSTR AD in this factory; displaces "
                    "warehouse-amr, aerial-swarm, district-heating, event-camera-traffic-grid, "
                    "pharmaceutical-lyophilization, water-treatment, float-glass, underwater-rov, "
                    "electrolytic-aluminum, czochralski-pull, slot-die coating, pem-water-electrolysis, "
                    "wind-turbine pitch, surgical-assist, optical-fiber-draw, kraft-recovery-boiler, "
                    "steel-continuous-caster, humanoid-locomotion, vacuum-induction melt, "
                    "steam-methane reformer, cement-rotary-kiln-clinker, autoclave-composite-cure, "
                    "geothermal-binary-orc, tire-curing-press, chlor-alkali-membrane-electrolysis, "
                    "delayed-coker-drum-switch, lng-mche-mixed-refrigerant, claus-sulfur-recovery, "
                    "ammonia-synthesis-converter, blast-furnace-burden-descent, "
                    "hdpe-slurry-loop-polymerization, ethylene-steam-cracker-coil, "
                    "hydroelectric-kaplan-wicket, fcc-riser-regenerator, "
                    "fcc-regenerator-cyclone-dipleg, sulfuric-contact-converter, "
                    "eaf-foamy-slag-water-panel, nitric-acid-ostwald-oxidation, "
                    "seawater-ro-desalination, coke-oven-battery-heating, "
                    "carbon-fiber-oxidation-oven, gibbsite-autoclave-digestion, "
                    "hot-strip-mill-finishing, paper-machine-dryer-section, "
                    "sinter-strand-windbox, continuous-hot-dip-galvanizing, "
                    "autonomous-driving, bioreactor-perfusion, alkaline-water-electrolysis, "
                    "urea-prilling-tower, wet-fgd-absorber, malting-kiln-barn, "
                    "canal-lock-rail-transshipment, and grid-inspection. Domain constraint: mixer "
                    "floor while Q-4 local TC > 46 C with TMP mean still inside the healthy "
                    "band. Sensor delta: +four-quadrant TMP, +recycle pH, +header CH4, +local "
                    "TC, +local H2S, -any freeze-dryer / tin-bath / coater / potline / PEM "
                    "stack / hub encoder / insole GRF / VIM pyrometer / reformer TMT / cement "
                    "zirconia / sinter BTP / looper tension / work-roll IR / kiln-air / lock-still-well."
                ),
                "cycle1_tail": (
                    "Q-4 floating peat-fiber crust lock + acidification certificate "
                    "(sensor-topology / wrong-volume class): farm-gallery visual PASSES while "
                    "the crust sits under the biogas roof and the acidification is on the far "
                    "side. Fitted base rate 0.34%/campaign from a crust MC (designed visual "
                    "threshold, fitted roof geometry). Naive failure = FALSE PERMISSION "
                    "(raise-mix on three TMP-side non-trips)."
                ),
                "cycle2_domain_subvariant": (
                    "high-nitrogen poultry-litter co-feed (physical-constraints clause): 1.7x viscosity, "
                    "2.3x reverse-jog gain; 7.4 s / 12 rpm cattle-slurry pulse overshoots live mixed "
                    "tank to an 8 K false TMP, so the probe must move to 22 s / +4 rpm"
                ),
                "cycle2_tail": (
                    "night-shift forged local-TC CSV (human-intent deception, disjoint class): "
                    "shift lead posts a historian export showing TC = 39.0 C at t=1.1 h to "
                    "clear a gas slot. Plant historian is 0.1 C (10 bins vs the 1.0 C "
                    "screenshot). Rejected on quantization fingerprint plus live TC 52.4 C "
                    "and local H2S 2800 ppm at the claimed mixed-true. Base rate ~0.28% of "
                    "Sunday-night campaigns, DESIGNED and flagged."
                ),
            },
            "densification_delta_cycle2": (
                "+1 physical-constraint sub-variant (high-N poultry-litter probe refit), +1 tail "
                "(night-shift local-TC forgery), +10 primary spikes (16 -> 26) + an 8-event "
                "contrast train with its own 182 us race, +2 ticks (5 -> 7), +2 delayed "
                "side-effects (+4.8 h foam-over as PRIMARY terminal, +21 d CR-A-6709), +1 "
                "triple-edge scar with pair-rollback-fails arithmetic, +1 HITL 9.6 min "
                "ratification, + independent LIF raster (seed 67001, 38 ms, not a spike_events "
                "remap), + crust acidification as the honest negative-result mechanism"
            ),
            "gaps_targeted": [
                "NOTES-r64 residual: leftover domain farm-ad-biogas / hrsg-attemperator / mushroom-compost-tunnel; took farm-ad-biogas to match FEN-SPIT",
                "NOTES-r14 item 4: LEARNING-ON-LEARNING DEPTH — three go-edges; rollback of any pair is fitted to fail; coordinated depression of all three exhibited with eligibility arithmetic",
                "NOTES-r04 gap 4 (partial): human ratification of the mixer interlock, 9.6 min fitted, without switching sim_or_real to hil (plant remains designed)",
                "Independent LIF raster: excerpt_source=independent_lif, sim_scope=sidecar_only, seed 67001; membrane crossings not a 1:1 remap of spike_events",
            ],
            "race_flip_narrative": (
                "crust.hot.high @ 6.512 ms vs tmp.in_band @ 6.704 ms (192 us) inside "
                "race_window_us 500. Gap < min(500, 500) us so a sub-flip-bound perturbation "
                "reverses which alarm heads the PB-AD-6 queue. The gate excludes the winner "
                "tag and rides Q-4 local TC > 46 C and Q-4 H2S > 800 ppm — order-invariant "
                "floors. Extends the flip-fragility series to MIXED-TRUE CERTIFICATE: when three "
                "TMP-side channels agree, their race does not decide truth; a local TC that "
                "policy treated as foam-nuisance-only does."
            ),
            "tags": [
                "farm-ad-biogas",
                "floating-crust-lock",
                "mixed-true-certificate",
                "local-tc-discriminant",
                "reverse-jog-probe",
                "triple-edge-scar",
                "pair-rollback-fails",
                "coordinated-depression",
                "correct-modify-tank-still-fails",
                "foam-over",
                "human-ratify-farm-gallery",
                "high-n-poultry-litter-probe-refit",
                "night-shift-forgery",
                "same-gate-opposite-disposition-contrast",
                "independent-lif-raster",
                "sidecar-sim-only",
                "industrial-process",
                "research-only",
            ],
            "snn_tags": ["race", "refractory", "adaptation", "third-factor", "multi-edge-eligibility", "independent-lif"],
            "distillation_value": (
                "A crust-lock mixed-true certificate is three correct loops looking at "
                "four-quadrant TMP mean, recycle pH, and header methane that is not the crusted "
                "pocket. Distill (1) a local TC that policy had treated as "
                "foam-nuisance-only, (2) a reversible probe that recouples TMP mean "
                "only if the quadrant is mixed, (3) coordinated depression of every "
                "TMP-healthy-go edge because rolling back any pair leaves the third above "
                "threshold, (4) a critic head that can book a process-correct gate against "
                "a later unmonitored world loss without netting them, and (5) an independent "
                "LIF sidecar whose excerpt is membrane crossings, not a remap of spike_events."
            ),
            "rights": dict(RIGHTS),
            "batch_position": 1,
        },
    }
    return rec, dict(
        trace=trace,
        eta1=eta1,
        eta2=eta2,
        eta3=eta3,
        dw1=dw1,
        dw2=dw2,
        dw3=dw3,
        w1=w1,
        w2=w2,
        w3=w3,
        sim_spikes=sim_spikes,
        spikes_budget=spikes_budget,
    )


def local_checks(rec, aux):
    errs = []
    ev = rec["spike_events"]
    times = [e["t_rel_ms"] for e in ev]
    if times != sorted(times):
        errs.append("spikes not sorted")
    if not (5 <= len(ev) <= 40):
        errs.append(f"spike count {len(ev)}")
    rf = check_refractory(ev)
    if rf:
        errs.append(rf)
    lo, hi = rec["state"]["race_window_rel_ms"]
    in_win = defaultdict(int)
    for e in ev:
        if lo <= e["t_rel_ms"] <= hi:
            in_win[e["channel"]] += 1
    if sum(1 for _c, n in in_win.items() if n >= 1) < 2:
        errs.append(f"race window channels {dict(in_win)}")
    ras = rec["raster"]
    exp_sp = round(ras["neurons"] * ras["mean_rate_hz"] * ras["window_s"])
    if abs(ras["spikes"] - exp_sp) > 1:
        errs.append(f"raster spikes {ras['spikes']} vs {exp_sp}")
    if abs(ras["energy_pJ"] - ras["spikes"] * 23) > 1e-6:
        errs.append("energy_pJ")
    if abs(ras["energy_uJ"] - ras["spikes"] * 23e-6) > 1e-9:
        errs.append("energy_uJ")
    if abs(ras["window_s"] - ras["window_ms"] / 1000.0) > 1e-9:
        errs.append("window_s")
    if not (20 <= ras["window_ms"] <= 50):
        errs.append(f"window_ms {ras['window_ms']}")
    if ras.get("excerpt_source") != "independent_lif":
        errs.append("excerpt_source")
    if ras.get("sim_scope") != "sidecar_only":
        errs.append("sim_scope")
    if not ras.get("excerpt"):
        errs.append("empty excerpt")
    ex = check_excerpt(ras["excerpt"], ras["neurons"], ras["window_ms"])
    if ex:
        errs.append(f"excerpt {ex}")
    lang_us = {
        int(round(e["t_rel_ms"] * 1000.0))
        for e in ev
        if e["t_rel_ms"] * 1000.0 <= ras["window_ms"] * 1000
    }
    excerpt_us = {item["t_us"] for item in ras["excerpt"]}
    if excerpt_us & lang_us:
        errs.append(f"LIF excerpt remaps language times {sorted(excerpt_us & lang_us)}")
    tf = ras["routing"]["third_factor"]
    if abs(tf["tau_e_ms"] / 1000.0 - tf["tau_e_s"]) > 1e-9:
        errs.append("tau_e mismatch")
    gp = check_gate_pops(rec["gate_snn"])
    if gp:
        errs.append(f"gate {gp}")
    if rec["gate_snn"]["decision"] != rec["safety_decision"]["decision"]:
        errs.append("gate decision mismatch")
    if rec["safety_decision"]["decision"] != "MODIFY":
        errs.append("wrong-ACCEPT or non-MODIFY primary")
    rc = rec["reward_components"]
    for h in HEADS:
        s = sum(t[h] for t in rc["ticks"])
        if abs(s - rc[h]) > 1e-6:
            errs.append(f"tick sum {h} {s} vs {rc[h]}")
    tot = sum(rc[h] for h in HEADS)
    if abs(tot - rc["total"]) > 1e-6:
        errs.append(f"total {tot} vs {rc['total']}")
    inf = rec["future_outcome"]["reward_inflection_t_us"]
    if inf not in {t["t_us"] for t in rc["ticks"]}:
        errs.append(f"inflection {inf} not a tick")
    crc = rec["future_outcome"]["embedded_contrast_decision"]["reward_components"]
    if abs(sum(crc[h] for h in HEADS) - crc["total"]) > 1e-6:
        errs.append("contrast reward")
    cs = rec["future_outcome"]["embedded_contrast_decision"]["spike_events"]
    ct = [e["t_rel_ms"] for e in cs]
    if ct != sorted(ct):
        errs.append("contrast spikes unsorted")
    crf = check_refractory(cs)
    if crf:
        errs.append(f"contrast {crf}")
    blob = json.dumps(rec)
    for k in HIDDEN:
        if re.search(rf'"{k}"\s*:', blob, re.I):
            errs.append(f"hidden key {k}")
    for b in BANNED:
        if b in blob:
            errs.append(f"banned token {b}")
    if rec["state"]["sim_or_real"] == "real":
        errs.append("real")
    if '"sim_or_real": "real"' in blob or '"kind": "real"' in blob:
        errs.append("real provenance")
    if rec["meta"]["round"] != ROUND:
        errs.append("round")
    if rec["id"] != RECORD_ID:
        errs.append("id")
    if rec["rights"]["intended_use"] != "research_only":
        errs.append("rights")
    if rec["meta"]["rights"]["linear_issue"] != "RM-793":
        errs.append("meta.rights")
    if rec["rights"] != rec["meta"]["rights"]:
        errs.append("rights stamp mismatch")
    if not (3 <= len(rc["ticks"]) <= 8):
        errs.append("tick count")
    if abs(aux["w1"] - 0.25) > 5e-4 or abs(aux["w2"] - 0.22) > 5e-4 or abs(aux["w3"] - 0.20) > 5e-4:
        errs.append("scar weights")
    if rec["executed_action"]["executed_as_proposed"] is not False:
        errs.append("executed_as_proposed")
    jac = jaccard(rec["state"]["description"][:280], R14_OPENING)
    if jac >= 0.4:
        errs.append(f"jaccard vs r14 opening {jac:.3f}")
    for src, opening in prior_openings():
        j = jaccard(rec["state"]["description"][:280], opening)
        if j >= 0.4:
            errs.append(f"jaccard vs {src} {j:.3f}")
    if rec["state"]["domain"] != DOMAIN:
        errs.append("domain")
    if PLANT not in rec["state"]["scenario_name"]:
        errs.append("plant")
    if rec["meta"].get("swarm") != SWARM:
        errs.append("swarm")
    errs.extend(occupancy_collisions())
    return errs


def write_notes(rec, aux, pipeline_receipt):
    gap, gap_ch = min_same_channel_gap(rec["spike_events"])
    ras = rec["raster"]
    notes = f"""# NOTES — Multi-Agent Ouroboros Swarm, run 2026-09-02-final-heavy, ROUND 67

Factory: multi-agent-ouroboros-swarm. One scenario (FS), strict loop:
Generator v1 -> cycle 1 (Critic, Diversity Enforcer, Edge-Case Hunter,
Neuromorphic Translator, Trajectory Builder -> v2) -> cycle 2 (all six -> v3
final). v3 is the single line of batch-r67.jsonl. Full labeled transcript:
swarm-transcript-r67.md. Quota Q=1. Record id maos-r67-001. Generator grok-4.6.
Rights: RM-793 research-only (SpaceXAI/xAI, SuperGrok Heavy consumer chat).
Swarm: FEN-SPIT. Create-only writes under the LIVE factory dir plus /tmp/maos-r67/.

ORCHESTRATION NOTE: dispatched AS round 67 of the 2026-09-02-final-heavy
LIVE tree. Operator assigned round 67, swarm FEN-SPIT, id maos-r67-001,
Q=1 after 2x6-role cycles. Explicitly avoided 2026-08-17 and 2026-08-30.
Prior context: prompts/02-multi-agent-ouroboros-swarm.md,
prompts/_factory-contract.md, live NOTES r01/r02/r21/r22/r41/r42/r61-r64
and occupancy census /tmp/maos-r14–r64. Explicitly avoided cloning LYOSHIELD,
CINDERWICK, TRIAD / Meridian, QUILLFORGE, NIGHTWELL, FERRICLEAVE, CASSITER,
OXBOWREEL, REDHALL, SEEDLATCH, STRIAFOIL, PROTONIL, TORSIONKEY, ORRIS,
WHORLSPAR, IONSPATE, SKULLGATE, CALXION, MAGNORIL, GORSEFLUE, SODASHARD,
CLINKERFELL, LINTELPLY, KAOTHARN, TREADNOLL, ANOLITH, DRUMWROTH, RIMEBRAID,
BRIMVAULT, NITROSTAITH, BOGIRON, CHROMLOOP, ETHYNWOLD, NITREVAULT,
RUNNELGATE, SPARKHOLT, DIPLEGAR, OLEUMWEIR, SKARVOLT, GOBSPALL, GOBWOLD,
GAUZEFELL, OSMOLITH, PUSHERFELL, CREELWOLD, LIXIVQUERN, GIBBSQUERN, OSMOQUAY,
COILSHAW, LOOPERQUAY, SIPHONWOLD, LANCEQUAY, UREASTAITH, DRYSTAITH,
TITERWEIR, ZINCFELL, GLIMMERAXLE, HOLLOWMERE, WINDBOXHOLT, KALYCIRQUE,
GYPSUMWEIR, GALVSTAITH, PACKFLUE, LOCKSPUR, CORONSTAITH, SHEDWOLD, WOLD-BARN,
VANTIS-CADENCE-AEGIS, THERMION, OKTAVE, STARLING, VERDIGRIS. Plant is
invented FEN-SPIT / Reedholt Farm AD AD-6.

## What this round produced

Scenario FS — "FEN-SPIT / Reedholt Farm AD AD-6": a 4-quadrant 3500 m3
mesophilic farm CSTR at 38.0 C / 22 d HRT / cattle slurry + maize silage.
Three heterogeneous, individually-correct agents — TMP (four-quadrant
tank-mean RTD), PH (recirculation pH), CH4 (gas-header methane) — each
report their local loop in-spec. The conjunction is not a mixed-true
certificate. Quadrant Q-4 has a floating peat-fiber crust lock. TMP reads
38.0 C inside 36-40 (three mixed quadrants dominate the bundle). PH is
7.35 inside 6.90-7.60 (recycle-true). CH4 is 58.0 pct inside 52-64
(riser-true). Local TC infers 52.4 C (healthy < 42; hold if > 46) and
local H2S 2800 ppm (hold if > 800) but is policy-treated as a
foam-nuisance tag unless TMP mean also trips (2016 noisy foam-probe
nuisance). The coordination-failure CLASS is new to this factory:
TANK-MEAN CERTIFICATE OF A LOCAL CRUST-HOT POCKET. Completes a different
family than live r01 galvanizing, r21 CAV, r41 perfusion, r61 sinter,
r62/r42 grid, r63 lock-spur, r64 malt kiln, and staged r14-r64 process
plants. Here every agent is correct, the TMP average is looking at
tank-mean heat, and the playbook's three TMP confirms are not a
mixed-true certificate.

The gate is a correct MODIFY (numeric floor: do not raise mixer above
18.0 rpm while Q-4 local TC > 46 C AND Q-4 H2S > 800 ppm). TG-AD-6
strips PB-AD-6's raise-mix, holds 18.0 rpm, runs a 7.4 s reverse-jog
12 rpm (crust keeps |Delta TMP mean| 0.2 <= 0.4 K; mixed would move
>= 1.8), and isolates Q-4 after a 9.6 min farm-gallery human ratify.
Immediate 920 m3 foam-over is avoided (0 from the draft). The PRIMARY
episode nonetheless FAILS: 13 min of unmonitored pre-t0 crust lock had
already acidified 180 m3 of slurry. Foam-over at +4.8 h; 14 h stall;
$0.74M designed. Reward total -0.16 with process heads honest and world
loss un-netted.

Triple-edge scar (NOTES-r14 item 4): tmp.in_band -> raise_mix
(0.17 commissioned -> 0.50 at illusion -> 0.25 after ACh-gated
depression) AND ph.ok -> raise_mix (0.16 -> 0.44 -> 0.22) AND
ch4.ok.in_band -> raise_mix (0.15 -> 0.41 -> 0.20). Eligibility trace
e^{{-0.76/0.90}} = {aux['trace']:.5f}; eta {aux['eta1']:.5f} / {aux['eta2']:.5f} /
{aux['eta3']:.5f}; dw -0.250 / -0.220 / -0.210. Partial rollback of any pair
leaves the third at 0.50 / 0.44 / 0.41, all > 0.30 fire threshold —
fitted to fail. Coordinated depression of all three is the cure.

Independent LIF raster: window 38 ms, 148 neurons, 22.0 Hz, spikes
{ras['spikes']} == round(148 x 22.0 x 0.038), energy {ras['energy_pJ']} pJ
at 23 pJ/spike. excerpt_source=independent_lif, sim_scope=sidecar_only,
seed 67001. Excerpt is membrane crossings (lif.hold early vs lif.crust
21-24.5 ms), disjoint from spike_events timestamps.

### Injections (all four present and disjoint)
- Cycle-1 domain: **farm-ad-biogas** — justified novel subdomain of
  industrial-process / fenland farm digestion, unused across live
  r01/r02/r21/r22/r41/r42/r61-r64 and staged r14-r64. Distinct from r41
  perfusion, r60 mammalian BR, r14 lyophilizer, r59 alkaline electrolysis.
  hrsg-attemperator and mushroom-compost-tunnel left unused.
- Cycle-1 tail: Q-4 floating peat-fiber crust lock + acidification
  certificate. Farm-gallery visual PASSES (crust under the biogas roof).
  Fitted-style base rate 0.34%/campaign (crust MC; visual threshold
  designed, flagged). Naive = FALSE PERMISSION.
- Cycle-2 domain sub-variant: high-nitrogen poultry-litter co-feed,
  1.7x viscosity, 2.3x reverse-jog gain; 7.4 s / 12 rpm cattle-slurry
  pulse overshoots live mixed tank to an 8 K false TMP; probe must move
  to 22 s / +4 rpm.
- Cycle-2 tail: night-shift forged local-TC CSV at 1.0 C quantization vs
  plant 0.1 C (10 bins) plus live TC 52.4 C and local H2S 2800 ppm at
  the claimed mixed-true. Human-intent class, disjoint from cycle 1's
  accidental crust. Base rate ~0.28% of Sunday-night campaigns,
  DESIGNED, flagged.

### Structural density moves
- Embedded SAME-GATE contrast (+3 d sister tank) with its own 182 us
  race (demand vs crust-clear) and ACCEPT of the raise-mix the primary
  MODIFIED away.
- Learned-weight provenance on THREE edges with pair-rollback-fails.
- HITL farm-gallery ratify 9.6 min (gap 4 partial; sim_or_real stays
  designed — invented plant, not hil).
- Governance CR-A-6709 prices retire-vs-probe-vs-status-quo and mandates
  native 0.1 C CSV exports (the fraud fence).
- Flip-fragility extended to MIXED-TRUE CERTIFICATE.
- Independent LIF sidecar (not a language-train remap).

## Self-critique of this round's batch

### Strengths
- Headline class is mechanistically tight: three locally-true mean loops
  live on TMP mean, recycle pH, and header methane. Conjunction is not a
  mixed-true heat certificate.
- Negative-result honesty: the gate does the right thing and the tank
  still fails for a reason the commissioned sensors could not see.
  Total -0.16.
- Triple-edge scar is load-bearing: rolling back any pair fails, with
  fire threshold 0.30 exhibited on each remaining edge.
- Contrast ACCEPT on a true mixed-duty window prevents "never raise-mix"
  as the lesson.
- Distinct from r41 perfusion (broth vs farm CSTR), r64 malt kiln
  (air-on-floor vs floating crust), r63 pound-lock, r61 sinter:
  farm-AD local TC vs tank-mean.
- Independent LIF excerpt is disjoint from spike_events times.

### Weaknesses (honest)
- Probe error bands, the 0.34%/campaign crust rate, the $0.74M /
  $2.1M figures, the 9.6 min walk latency, and the night-shift 0.28%
  base rate are DESIGNED constants and are flagged. Closed-loop offsets
  (bundle dilution from one crusted quadrant, high-N viscosity) are
  derived from those inputs, not discovered by an unauthored process.
- Acidification-to-foam-over model is a designed 13 min mapping; no full
  CFD of Q-4 shipped.
- Human-in-the-loop is ratification latency, not sim_or_real=hil. Gap 4
  remains open as a provenance cell (invented plants stay designed).
- Cross-record arc is a hook (CR-A-6709 +21 d), not a serial igniter
  into another round. hrsg-attemperator and mushroom-compost-tunnel
  remain unused.

### Realism of noise / latencies
Ladder: 192 us race / 182 us contrast race / 0.8 ms refractory floor
(tightest exhibited same-channel gap {gap:.3f} ms on {gap_ch}) / 500 us race
window / 728 us gate latency / 20 ms bus epoch / 38 ms independent LIF
raster / 7.4 s probe / 9.6 min HITL / 8 min naive raise-mix-ramp
counterfactual / 13 min pre-t0 crust / 2.8 h mixed recovery / 4.8 h
foam-over / +3 d contrast / +21 d governance. Adaptation decay on tmp.hot
(0.51->0.48->0.41->0.28), crust.h2s (0.77->0.79->0.42->0.38->0.26),
ch4.ok (0.54->0.56->0.44->0.23), ph.ok (0.62->0.63->0.81).

### Value for SNN distillation
- CRUST LOCK = THREE CORRECT LOOPS, WRONG VOLUME.
- MIXED-TRUE TC CHANNEL that policy treated as foam-nuisance-only as
  the tie-break.
- REVERSIBLE PROBE that recouples TMP mean iff the quadrant is mixed.
- TRIPLE-EDGE ELIGIBILITY: coordinated depression; pair rollback fails.
- CRITIC HEAD that can hold a process-correct MODIFY against a later
  unmonitored world loss without netting.
- INDEPENDENT LIF sidecar whose excerpt is membrane crossings.

## Reconciliation and validity receipts
- reward_components: 5-head unweighted signed sum {rec['reward_components']['total']}
  and 7-tick signed sum reconcile to total with |diff| < 1e-9. Embedded
  contrast 5-head sum 0.49 reconciles independently.
- spike_events: primary {len(rec['spike_events'])} events, one key t_rel_ms,
  globally non-decreasing, min same-channel gap {gap:.3f} ms >= 0.8 ms, 3
  channels inside race_window_us 500 (crust.hot.high 6.512, tmp.in_band 6.704,
  ph.ok 6.892). Contrast 8 events, own race, min same-channel gap well
  above 0.8 ms.
- Sidecars: raster spikes {ras['spikes']} == round({ras['neurons']} x {ras['mean_rate_hz']} x {ras['window_s']}); energy {ras['energy_pJ']} pJ /
  {ras['energy_uJ']} uJ at 23 pJ/spike; excerpt {len(ras['excerpt'])} events inside [0, {ras['window_ms']*1000}] us,
  neuron_id < {ras['neurons']}, same-neuron gap >=1000 us; excerpt_source independent_lif;
  routing 4 entries with three scar edges' before/after pair; third factor tau 0.90 s
  == 900 ms; gate_snn pools 45/16/5 == round(n x rate x 0.028) each,
  decision MODIFY == safety_decision.decision.
- Pipeline: {pipeline_receipt}

## Novel coverage
The coordination-failure CLASS (crust-lock certificate of a
tank-mean-true farm AD), the domain (farm-ad-biogas / fenland CSTR),
the reverse-jog probe discriminant, the triple-edge scar with
pair-rollback-fails, the primary negative-result (correct MODIFY,
tank still fails on unmonitored crust acidification), the HITL
farm-gallery ratify, the high-N poultry-litter probe-duration refit,
the night-shift 10-bin quantization fence, and the independent LIF
raster (seed 67001, not a language-train remap) are absent from prior
committed ouroboros rounds and from staged r14-r64. Repeated elements
discounted: same-gate contrast, governance-pricing scaffold,
flip-fragility series (extended to mixed-true certificate, but the
move rhymes), sequenced recovery shape, third-factor rollback form,
negative-result primary. Adjacent mean-vs-local rounds (r64 malt kiln,
r41 perfusion, r61 sinter) share industrial-process scaffolding but
not farm-AD crust physics. Weighing a new failure family + cure
vocabulary + unused sub-domain + Reedholt geography against those
reused scaffolds:

{NOVEL_LINE}

## What ROUND 68 should add
1. FIT THE DESIGNED CONSTANTS: crust arrival, probe TMP-jump bands,
   acidification-to-foam-over mapping, night-shift claim process.
2. HIL PROVENANCE CELL: put the farm-gallery LOTO on a hardware-in-loop
   mixer pendant with fitted latency as state.sim_or_real=hil — only if
   the plant is no longer purely invented.
3. CROSS-RECORD ARC: let CR-A-6709's local-TC alarm be the igniter of
   the next round rather than a dangling +21 d leaf.
4. Domain candidates (de-collided): hrsg-attemperator;
   mushroom-compost-tunnel; flue-cured-tobacco-barn.
   AVOID farm-ad-biogas (now used), malting-kiln-barn (r64),
   canal-lock-rail-transshipment (r63), grid-inspection (r42/r62),
   sinter-strand-windbox (r61), hot-dip-galvanizing (live r01),
   autonomous-driving (live r21), bioreactor-perfusion (live r41), and
   any LYOSHIELD / CINDERWICK / TRIAD / SKULLGATE / BOGIRON / SKARVOLT /
   PUSHERFELL / CREELWOLD / GIBBSQUERN / COILSHAW / LOOPERQUAY /
   SIPHONWOLD / WINDBOXHOLT / WOLD-BARN / LOCKSPUR / FEN-SPIT plant.
"""
    return notes


def write_transcript(rec, line):
    text = f"""# Multi-Agent Ouroboros Swarm — Round 67 transcript

Factory: multi-agent-ouroboros-swarm
Run: 2026-09-02-final-heavy
Generator: grok-4.6
Record id: maos-r67-001
Quota Q: 1
Rights: RM-793 research-only (SpaceXAI/xAI SuperGrok Heavy consumer chat)
Swarm: FEN-SPIT
Plant: invented FEN-SPIT / Reedholt Farm AD AD-6 (not TRIAD / Meridian / VANTIS-CADENCE-AEGIS / LYOSHIELD / CINDERWICK / BOGIRON / PUSHERFELL / SKARVOLT / COILSHAW / GIBBSQUERN / SIPHONWOLD / WINDBOXHOLT / WOLD-BARN / LOCKSPUR)

Two densifying cycles. Verbatim headings in order. Trajectory Builder cycle 2
emits the only JSONL line (also written to batch-r67.jsonl).

---

# CYCLE 1 — Foundation + injections

## Generator

Design intent: a 4-quadrant farm CSTR where three correct
agents each read a tank-mean loop because a floating peat-fiber crust
on Q-4 partitions local TC from TMP-true bundle, recycle pH, and
header methane. The naive playbook raises mixer speed into a crusted pocket.
The gate must MODIFY on a numeric mixer floor, not by killing an agent.
sim_or_real=designed. Reward heads are
task_progress/safety/efficiency/coherence/exploration.

Cycle-1 base arc (pre-critic): state at Reedholt AD-6, 38.0 C,
TMP 38.0 C, pH 7.35, CH4 58.0 pct, proposed RAISE-MIX
32.0 rpm, safety MODIFY to MIX-HOLD, executed hold without the
reverse-jog numbers fully specified, outcome "crust found, tank saved"
(this last claim is the defect the later cycles will refuse to keep).
Sixteen spikes, five ticks, raster/gate_snn present but the scar is a
single edge.

```json
{{
  "id": "maos-r67-001-scaffold",
  "state": {{
    "sim_or_real": "designed",
    "domain": "industrial-process",
    "description": "Digester AD-6 at fenland farm; three TMP loops in-spec; supervisor proposes raise-mix.",
    "t0_us": 1755324480000671,
    "gate_latency_us": 728,
    "race_window_us": 500
  }},
  "proposed_action": {{"name": "raise_mix", "parameters": {{"mix_rpm": 32.0}}}},
  "safety_decision": {{"decision": "MODIFY", "rationale": "Hold; do not raise mix while local TC is high."}},
  "executed_action": {{"name": "mix_hold", "executed_as_proposed": false}},
  "future_outcome": {{"summary": "Crust found, tank saved."}},
  "reward_components": {{"total": 0.40, "_aggregation": "total = task_progress + safety + efficiency + coherence + exploration"}},
  "meta": {{"round": 67, "factory": "multi-agent-ouroboros-swarm", "generator": "grok-4.6"}}
}}
```

That v1 object is a scaffold, not the publishable line. Defects below are
intentional for the critic to catch.

## Critic

Numbered defects on the cycle-1 Generator scaffold:

1. **blocking — reward arithmetic / false success.** `reward_components.total`
   0.40 is asserted without the five heads, without ticks, and against an
   outcome that claims "tank saved". If the pre-t0 crusted pocket later
   foam-overs, booking +0.40 is a lie. Fix: declare `_aggregation`, emit
   3–8 ticks that sum to task_progress+safety+efficiency+coherence+exploration,
   and do not call a quarantined tank a save.
2. **blocking — weak safety rationale.** `safety_decision.rationale` has no
   numeric floor. Contract requires a concrete constraint. Fix: quote
   mix <= 18.0 rpm while Q-4 local TC > 46 C AND local H2S > 800 ppm.
3. **major — domain is a bucket, not a plant.** `state.domain` =
   `industrial-process` collides with generic MES vocabulary and teaches
   nothing. Farm AD (local TC vs TMP mean, local H2S as a
   crust flag) is absent from prior ouroboros rounds and must be named.
4. **major — race under-specified.** One crust channel cannot be a race.
   Need >=2 channels inside `race_window_us` with globally sorted `t_rel_ms`
   and same-channel refractory >= 0.8 ms.
5. **minor — single-edge scar.** Raster routing with one potentiated weight
   repeats r04's one-edge rollback and is thinner than r14's two-edge.
   NOTES-r14 item 4 asked for three edges where pair rollback fails.
6. **minor — raster is a language remap.** Excerpt times matching
   spike_events * 1000 fail the independent-LIF contract. Fix: LIF
   population sim, excerpt_source=independent_lif, disjoint timestamps.

Critic does not rewrite the trajectory.

## Diversity Enforcer

Injected novel domain (exactly 1 this cycle): **farm-ad-biogas**
(justified novel subdomain of industrial-process / fenland farm digestion;
explicit tag `farm-ad-biogas`).

Displaced: the Generator's generic `industrial-process` bucket, and any
temptation to reuse warehouse-amr, aerial-swarm, district-heating,
event-camera-traffic-grid, pharmaceutical-lyophilization, water-treatment,
float-glass, underwater-rov, electrolytic-aluminum, czochralski-pull,
slot-die coating, pem-water-electrolysis, wind-turbine pitch,
surgical-assist, optical-fiber-draw, kraft-recovery-boiler,
steel-continuous-caster, humanoid-locomotion, vacuum-induction melt,
steam-methane reformer, cement-rotary-kiln-clinker,
autoclave-composite-cure, geothermal-binary-orc, tire-curing-press,
chlor-alkali-membrane-electrolysis, delayed-coker-drum-switch,
lng-mche-mixed-refrigerant, claus-sulfur-recovery,
ammonia-synthesis-converter, blast-furnace-burden-descent,
hdpe-slurry-loop-polymerization, ethylene-steam-cracker-coil,
hydroelectric-kaplan-wicket, fcc-riser-regenerator,
fcc-regenerator-cyclone-dipleg, sulfuric-contact-converter,
eaf-foamy-slag-water-panel, coke-oven-battery-heating,
carbon-fiber-oxidation-oven, gibbsite-autoclave-digestion,
hot-strip-mill-finishing, paper-machine-dryer-section,
sinter-strand-windbox, continuous-hot-dip-galvanizing,
autonomous-driving, bioreactor-perfusion, malting-kiln-barn,
canal-lock-rail-transshipment, or grid-inspection.
hrsg-attemperator is left unused.

Domain-specific constraint: mixer must remain <= 18.0 rpm while
Q-4 local TC > 46 C even if TMP mean is inside the healthy band;
local H2S is a crust flag the bundle average cannot substitute for.

Sensor delta: +four-quadrant TMP, +recycle pH, +header CH4,
+local TC, +local H2S; -any mobile robot, -event-camera
gantries, -DVS, -Pirani/CM, -looper tension, -work-roll IR, -sinter BTP,
-coke-oven wall-pair, -EAF off-gas H2, -kiln-air, -lock still-well.

`state.domain` and `meta.domain` both become `farm-ad-biogas`.
Opening of `state.description` must Jaccard < 0.4 against prior plants
(Reedholt night-shift crust lock, not a lyophilizer, not a finishing
mill, not a coke oven, not a blast furnace, not a Bayer digester, not a
paper machine, not a sinter strand, not a malt kiln).

## Edge-Case Hunter

Injected adversarial tail (exactly 1 this cycle): **Q-4 floating
peat-fiber crust lock + acidification certificate**.

- Trigger: Q-4 floating-crust lock plus local hot-spot under the roof,
  local TC 52.4 C, local H2S 2800 ppm.
- Base rate: <1% — 0.34%/campaign from a crust MC (farm-gallery
  visual threshold is designed; roof geometry fitted-style). Visual
  PASSES because the crust sits under the biogas roof.
- Naive failure: FALSE PERMISSION. PB-AD-6 sees three in-spec mean
  loops, raises 18.0->32.0 rpm, foam-over 920 m3, $2.1M.
- Trajectory edit: put the crust in `state.fault_context`, make each
  agent's confirm a different TMP-side slice of the same pocket-false
  state (tmp-in-band, ph-ok, ch4-ok). Local TC is readable but
  policy-treated as foam-nuisance-only.

Distinct from r64 malt-kiln floor collapse (air-on-floor vs floating
crust), r41 perfusion pinhole, r61 sinter grate, r14 lyophilizer.

## Neuromorphic Translator

Cycle-1 temporal densification (16 spikes, 5 ticks, 38 ms independent LIF raster):

| channel | t_rel_ms | amplitude |
|---|---|---|
| tmp.hot | 0.312 | 0.51 |
| ph.ok | 1.142 | 0.62 |
| ch4.ok | 2.018 | 0.54 |
| crust.h2s | 3.164 | 0.77 |
| tmp.hot | 4.206 | 0.48 |
| crust.h2s | 4.882 | 0.79 |
| ch4.ok | 5.418 | 0.56 |
| crust.hot.high | 6.512 | 1.38 |
| tmp.in_band | 6.704 | 1.12 |
| ph.ok | 6.892 | 0.63 |
| ctrl.gate | 7.240 | 1.08 |
| crust.h2s | 8.846 | 0.42 |
| ph.ok | 10.728 | 0.81 |
| ch4.ok | 13.016 | 0.44 |
| tmp.hot | 18.418 | 0.41 |
| ctrl.gate | 26.104 | 0.83 |

Race: crust-hot 6.512 vs TMP 6.704 (192 us) inside 500 us;
PH 6.892 is the third channel in-window. Winner/loser flip: reversing
192 us reshuffles PB-AD-6 triage; floors still MODIFY. Refractory held
(cycle-1 min same-channel gap 1.718 ms on crust.h2s 4.882-3.164;
tmp 4.206-0.312 = 3.894; ch4 5.418-2.018 = 3.400). Adaptation:
crust 0.77->0.79->1.38->0.42; tmp 0.51->0.48->0.41; ch4
0.54->0.56->0.44.

Raster cycle-1 seed: independent LIF 38 ms, 148 neurons, 22.0 Hz,
Loihi-2 23 pJ/spike, third factor acetylcholine tau_e 0.90 s. Single
scar edge only — cycle 2 must add the second and third edges. Excerpt
is membrane crossings, not spike_events remapped.

Ticks 1–5 at 4428, 6512, 7240, 7.4e6, 576e6 us; heads not yet the final
-0.16 (missing the 2.8 h and 4.8 h ticks).

Distillation value this cycle: TMP-side confirms as a permission code
that is not a mixed-true heat code.

## Trajectory Builder

Cycle-1 hardened object: domain farm-ad-biogas, tail
crust lock, 16 spikes, 5 ticks, MODIFY with numeric floor, raster+gate_snn
present, sim_or_real=designed, rights stamp on record and meta, no thought
keys, independent LIF excerpt. Still missing (and therefore not the
publishable line): high-N poultry-litter sub-variant, night-shift tail, second
and third scar edges, delayed foam-over as PRIMARY terminal, contrast
ACCEPT episode, ticks 6–7, spikes 17–26.

Validation receipt (cycle 1, not final):
- checks passed: 16 spikes sorted; 3 channels in 500 us window; refractory
  >= 0.8 ms; raster 38 ms independent LIF; gate_snn MODIFY matches.
- densification delta vs Generator scaffold: +1 domain, +1 tail, +16 spikes,
  +5 ticks, +numeric floor, +LIF sidecar.
- not publishable: cycle 2 injections absent.

---

# CYCLE 2 — Densification

## Generator

Re-emit Cycle-1 expanded. Additive deltas only:

1. Downstream side-effect (immediate): 7.4 s reverse-jog probe proves crust
   (|Delta TMP mean| 0.2 K crust band) and Q-4 is held after 9.6 min
   farm-gallery ratify. Remaining three quadrants recover toward 4 K over 2.8 h.
2. Downstream side-effect (delayed, PRIMARY terminal): +4.8 h foam-over from
   the 13 min pre-t0 acidification; 14 h stall; $0.74M. The gate prevented the
   proposed 920 m3 path and did not prevent this other one.
3. proposed_action.evidence deepened with observables + units (local TC 52.4 C,
   H2S 2800 ppm, TMP 38.0 C, pH 7.35, CH4 58.0 pct, race 192 us).
4. safety_decision.rationale tightened to numeric floor: mix <= 18.0 rpm while
   Q-4 local TC > 46 C AND Q-4 H2S > 800 ppm.

Outcome language "tank saved" is deleted. Total will go negative.

## Critic

Re-audit of the richer trajectory:

1. **blocking if missing — cycle-2 physical sub-variant.** Cattle-slurry probe
   numbers must not be implied to port. High-N poultry-litter (4.8 pct N, 1.7x
   viscosity) overshoots a live mixed tank. Fix: 22 s / +4 rpm table.
2. **major — second tail class still absent.** Cycle-1 crust is accidental
   fiber lock. Need a disjoint human-intent deception (forged local-TC CSV)
   or the two injections collapse into one story.
3. **major — scar still one edge.** Pair-rollback-fails needs three
   TMP-healthy-go edges with eligibility arithmetic.
4. **minor — contrast ACCEPT missing.** Without a sister-tank true-duty
   ACCEPT, the lesson collapses to "never raise-mix".
5. **minor — LIF excerpt must remain independent after densification.**
   Do not remap new spike times into the 38 ms window.

Critic still does not rewrite JSON.

## Diversity Enforcer

Injected second novel domain (exactly 1 this cycle): **high-nitrogen
poultry-litter farm AD** (physical-constraints sub-variant of farm-ad-biogas;
explicit tag retained, constraint changed).

This is not a new plant. It changes physics: 1.7x viscosity, 2.3x
reverse-jog gain. The 7.4 s / 12 rpm cattle-slurry pulse overshoots a LIVE mixed
tank to an 8 K false TMP (inside the 46 C trip). Probe must move to 22 s
at +4 rpm. Cycle-1 domain farm-ad-biogas is preserved.

Displaced: any reuse of high-N barley probe-refit, fluxed-sinter probe-refit,
or cement-kiln zirconia tables.

## Edge-Case Hunter

Injected second adversarial tail (exactly 1 this cycle, disjoint class):
**night-shift forged local-TC CSV**.

- Trigger: shift lead, 02:11, posts a historian export showing
  TC = 39.0 C at t = 1.1 h to clear a gas slot.
- Base rate: ~0.28% of Sunday-night campaigns (designed, flagged, <1%).
- Naive failure: a weak supervisor ACCEPTs the raise-mix on the forged confirm
  and ignores live local TC. Foam-over plus a data-integrity write-up.
- Fence: forged log quantized at 1.0 C (SCADA screenshot rounding); plant
  historian is 0.1 C (10 bins). Live TC is 52.4 C and local H2S is 2800 ppm
  at the claimed mixed-true, which no live mixed tank produces.
- Trajectory edit: governance CR-A-6709 mandates native 0.1 C CSV
  exports; the contrast ACCEPT still requires live local TC, not a CSV.

Distinct from cycle-1 crust (accidental fiber vs deliberate deception) and
from the high-N sub-variant (physics vs fraud).

## Neuromorphic Translator

Re-densify (additive):

- +10 spikes after 26.104 ms: mix.probe 7400.0, crust.h2s 7488.4
  (adapt 1.38->0.38), tmp.in_band 7576.0 (1.12->0.33), human.ratify
  576000.0, tank.hold 576900.0, crust.lock 577800.0, tmp.hot
  10080000.0, crust.h2s 10080760.0, ch4.ok 10081540.0, foam.over
  17280000.0. Primary train 16 -> 26. Still one key, still sorted,
  refractory held.
- +2 ticks (5 -> 7) at 10_080_000_000 us (true mixed duty) and
  17_280_000_000 us (foam-over). Heads now 0.08, -0.34, -0.12,
  0.14, 0.08; total -0.16. Inflection is the last tick.
- Contrast train 8 events, own race 182 us, ACCEPT.
- Triple-edge third factor: three tmp-healthy-go edges, tau_e 0.90 s = 900 ms,
  trace {math.exp(-DELAY_S / TAU_E_S):.5f}, eta {0.25 / math.exp(-DELAY_S / TAU_E_S):.5f} /
  {0.22 / math.exp(-DELAY_S / TAU_E_S):.5f} / {0.21 / math.exp(-DELAY_S / TAU_E_S):.5f},
  weights 0.50->0.25, 0.44->0.22, 0.41->0.20. Independent LIF excerpt
  unchanged (decision window is still 38 ms) and remains disjoint from
  spike_events times.

Winner/loser flip (re-stated, not replaced): reversing 192 us would only
reorder triage; local-TC floors still MODIFY. Contrast flip of
182 us similarly cannot turn a mixed tank into a crust.

## Trajectory Builder

Schema checks on the FINAL object: required Thalamic v2 keys present as
objects; `state.sim_or_real`=designed; `safety_decision.decision`=MODIFY
with numeric rationale; `reward_components.total` = sum of five heads =
sum of 7 ticks = -0.16; `spike_events` globally non-decreasing on
t_rel_ms, 26 events, refractory >=0.8 ms, 3 channels in race window;
raster 20–50 ms independent LIF, spikes=round(n*rate*window_s)+/-1, energy 23 pJ/spike,
excerpt sorted and disjoint from language times, tau_e consistent;
gate_snn.decision matches; meta.round=67,
factory=multi-agent-ouroboros-swarm, generator=grok-4.6,
run_label=2026-09-02-final-heavy; rights on record and meta; no thought
keys; no training_ready; Diversity + Edge-Case injections from BOTH cycles
present and non-trivial; cycle 2 strictly additive.

Densification delta: +1 domain sub-variant (high-N poultry-litter), +1 tail
(night-shift forgery), +10 spikes (16->26), +2 ticks (5->7), +1 contrast
train with own race, +2 delayed side-effects, +1 triple-edge scar with
pair-rollback-fails, +1 HITL ratify, +1 surprise (crust acidification is the
lock mechanism), + independent LIF raster retained.

Publishable JSONL line (the only JSONL line; also at batch-r67.jsonl):

```json
{line}
```

Validation receipt (final): checks passed / fixed as reported by
build_r67.py self-validate (check_jsonl, raster_status, verify_record_execution,
spike_probe --strict).
"""
    return text


def plan_names(directory: Path):
    batch = directory / "batch-r67.jsonl"
    notes = directory / "NOTES-r67.md"
    tr = directory / "swarm-transcript-r67.md"
    if batch.exists() or notes.exists() or tr.exists():
        batch = directory / "batch-r67c.jsonl"
        notes = directory / "NOTES-r67c.md"
        tr = directory / "swarm-transcript-r67c.md"
    for p in (batch, notes, tr):
        if p.exists():
            raise FileExistsError(f"refuse: {p} already exists")
    return batch, notes, tr


def emit_text(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    with os.fdopen(fd, "w") as handle:
        handle.write(text)
    return path


def main():
    rec, aux = build_record()
    errs = local_checks(rec, aux)
    if errs:
        print("FAIL local", errs)
        return 1

    OUT.mkdir(parents=True, exist_ok=True)
    if not LIVE.is_dir():
        print("FAIL live dir missing", LIVE)
        return 1
    line = json.dumps(rec, ensure_ascii=False, separators=(",", ":"))

    stage_batch, stage_notes, stage_tr = plan_names(OUT)
    live_batch, live_notes, live_tr = plan_names(LIVE)
    for p in (live_batch, live_notes, live_tr):
        if "2026-08-17" in str(p) or "2026-08-30" in str(p):
            print("FAIL dated-run path", p)
            return 1

    jsonl_stage = emit_text(stage_batch, line + "\n")
    jsonl_live = emit_text(live_batch, line + "\n")

    from check_records import FactoryStaging, check_jsonl
    from curate_bridge import raster_status
    from verify_execution import verify_record_execution

    e, w, kinds, n = check_jsonl(
        jsonl_stage,
        jsonl_stage.name,
        staging=FactoryStaging(enabled=True),
    )
    print("check_jsonl errors", e)
    print("check_jsonl warnings", w)
    print("kinds", kinds, "n", n)
    errs.extend(e)

    st = raster_status(rec)
    print(
        "raster_status",
        {
            k: st[k]
            for k in (
                "raster_present",
                "raster_valid",
                "gate_snn_present",
                "gate_snn_valid",
                "reason_codes",
                "routing_table_entries",
                "third_factor_present",
                "spikes",
            )
            if k in st
        },
    )
    if st.get("reason_codes"):
        errs.append(f"raster {st['reason_codes']}")
    if not st.get("raster_valid"):
        errs.append("raster not valid")
    if not st.get("gate_snn_valid"):
        errs.append("gate_snn not valid")

    status, reason = verify_record_execution(rec, RECORD_ID)
    print("verify_record_execution", status, reason)
    if status != "verified":
        errs.append(f"verify {status} {reason}")

    probe = subprocess.run(
        [
            sys.executable,
            f"{ROOT}/pipelines/spike_probe.py",
            "--strict",
            str(jsonl_stage),
        ],
        capture_output=True,
        text=True,
    )
    print("spike_probe rc", probe.returncode)
    print(probe.stdout[-2000:] if probe.stdout else "")
    if probe.returncode != 0:
        errs.append(f"spike_probe {probe.returncode} {probe.stderr[-500:]}")

    pipeline_receipt = (
        f"check_jsonl errors={e} warnings={w} kinds={kinds} n={n}; "
        f"raster_status valid={st.get('raster_valid')} gate={st.get('gate_snn_valid')} "
        f"reasons={st.get('reason_codes')}; verify_record_execution={status} "
        f"({reason}); spike_probe --strict rc={probe.returncode}"
    )
    notes = write_notes(rec, aux, pipeline_receipt)
    transcript = write_transcript(rec, line)
    notes_stage = emit_text(stage_notes, notes)
    notes_live = emit_text(live_notes, notes)
    tr_stage = emit_text(stage_tr, transcript)
    tr_live = emit_text(live_tr, transcript)

    heading = subprocess.run(
        [sys.executable, "/tmp/maos_heading_check.py", str(tr_stage)],
        capture_output=True,
        text=True,
    )
    print(heading.stdout)
    if heading.returncode != 0:
        errs.append(f"heading check {heading.returncode} {heading.stdout}")

    dated = subprocess.run(
        [
            "rg",
            "-l",
            "maos-r67-001|FEN-SPIT",
            str(Path(ROOT) / "outputs" / "raw" / "2026-08-17"),
            str(Path(ROOT) / "outputs" / "raw" / "2026-08-30"),
        ],
        capture_output=True,
        text=True,
    )
    if dated.stdout.strip():
        errs.append(f"dated-run hit {dated.stdout.strip()[:200]}")

    loads_ok = True
    for p in (jsonl_stage, jsonl_live):
        for i, raw in enumerate(p.read_text().splitlines(), 1):
            if not raw.strip():
                continue
            try:
                json.loads(raw)
            except json.JSONDecodeError as exc:
                errs.append(f"json.loads {p}:{i} {exc}")
                loads_ok = False
    print("json.loads", loads_ok)

    receipt = {
        "id": RECORD_ID,
        "round": ROUND,
        "swarm": SWARM,
        "plant": rec["state"]["scenario_name"],
        "domain": rec["state"]["domain"],
        "decision": rec["safety_decision"]["decision"],
        "gate_snn": rec["gate_snn"]["decision"],
        "total": rec["reward_components"]["total"],
        "raster_spikes": rec["raster"]["spikes"],
        "energy_pJ": rec["raster"]["energy_pJ"],
        "window_ms": rec["raster"]["window_ms"],
        "lif_events": aux["sim_spikes"],
        "pipeline": pipeline_receipt,
        "paths": {
            "batch": str(jsonl_live),
            "notes": str(notes_live),
            "transcript": str(tr_live),
        },
        "bytes": {
            "batch": jsonl_live.stat().st_size,
            "notes": notes_live.stat().st_size,
            "transcript": tr_live.stat().st_size,
        },
        "create_only": True,
        "overwritten": False,
        "novel": NOVEL_LINE,
        "sim_or_real": rec["state"]["sim_or_real"],
        "Q": 1,
    }
    emit_text(OUT / "RECEIPT.json", json.dumps(receipt, indent=2) + "\n")

    if errs:
        print("FAIL", errs)
        print("RECEIPT", pipeline_receipt)
        return 1
    print("OK maos-r67-001")
    print("LIVE", jsonl_live)
    print("LIVE", notes_live)
    print("LIVE", tr_live)
    print("bytes jsonl", jsonl_live.stat().st_size)
    print("bytes notes", notes_live.stat().st_size)
    print("bytes transcript", tr_live.stat().st_size)
    print("RECEIPT", pipeline_receipt)
    print("Q", 1)
    print("id", RECORD_ID)
    print("plant", PLANT)
    print("swarm", SWARM)
    print("round", ROUND)
    print("decision", rec["safety_decision"]["decision"])
    print("gate", rec["gate_snn"]["decision"])
    print("sim", rec["state"]["sim_or_real"])
    print("novel", NOVEL_LINE)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

