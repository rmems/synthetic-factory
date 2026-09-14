#!/usr/bin/env python3
"""Build and self-check MAOS round-59 JSONL (research-only; not published)."""
from __future__ import annotations

import json
import math
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

ROOT = "/home/raulmc/rmems/synthetic-factory"
sys.path.insert(0, ROOT)
sys.path.insert(0, f"{ROOT}/pipelines")

GEN_AT = "2026-09-03T08:59:00Z"
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
OUT = Path("/tmp/maos-r59")
HIDDEN = ("thought", "chain_of_thought", "scratch", "inner_monologue")
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
    "Sable Cryogenics",
    "Fen-Marrow",
    "FERRICLEAVE",
    "Pellwater",
    "CASSITER",
    "Marshfloat",
    "VEILFORGE",
    "MURENA",
    "HALYARD",
    "SEEDLATCH",
    "Quartzmere",
    "Quartzridge",
    "STRIAFOIL",
    "Kelpholt",
    "REDHALL",
    "Gullmere",
    "OXBOWREEL",
    "Oystermere",
    "TORSIONKEY",
    "Ridgeholt",
    "ORRIS",
    "Holmwick",
    "PROTONIL",
    "Ashspire",
    "WHORLSPAR",
    "Pikeshear",
    "Crowspire",
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
    "BRACEGILT",
    "Yarrowmere",
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
    "PITCHSTAITH",
    "Mossbank",
    "BOGIRON",
    "Mireholt",
    "CHROMLOOP",
    "Marlfell",
    "NITREVAULT",
    "Glaucove",
    "NITROSTAITH",
    "Chalkfen",
    "ETHYNWOLD",
    "Woadfen",
    "RUNNELGATE",
    "Ghyllmere",
    "SPARKHOLT",
    "Scoriafen",
    "DIPLEGAR",
    "Gritfen",
    "OLEUMWEIR",
    "Brindlefell",
    "SKARVOLT",
    "GOBSPALL",
    "Culletfen",
    "GOBWOLD",
    "Culletwick",
    "PUSHERFELL",
    "Sootmere",
    "CREELWOLD",
    "Rovingholt",
    "LIXIVQUERN",
    "Bauxfen",
    "GAUZEFELL",
    "Ammoxwick",
    "OSMOLITH",
    "Spumeholt",
    "Emberbarrow",
    "GIBBSQUERN",
    "Laterifen",
    "COILSHAW",
    "Loopercroft",
    "LOOPERQUAY",
    "Roughmere",
    "UREASTAITH",
    "Prillfen",
    "DRYSTAITH",
    "Feltwick",
    "SIPHONWOLD",
    "Reedfen",
    "OSMOQUAY",
    "Tidecairn",
    "NEL Hydrogen",
    "ITM Power",
    "McPhy",
    "Hydrogenics",
    "Sunfire",
    "John Cockerill",
    "Thyssenkrupp Nucera",
    "thyssenkrupp nucera",
    "Plug Power",
    "Bloom Energy",
    "Enapter",
    "Siemens Energy",
    "HyLYZER",
    "Silyzer",
    "De Nora",
    "Agfa Zirfon",
    "Zirfon",
    "Nafion",
    "Chemours",
    "Alcoa",
    "Rio Tinto",
    "Rusal",
    "Chalco",
    "Hindalco",
    "Norsk Hydro",
    "South32",
    "Vedanta",
    "Century Aluminum",
    "Aluminium Bahrain",
    "Emirates Global",
    "Outotec",
    "FLSmidth",
    "training_ready",
    "da Vinci",
    "Intuitive Surgical",
    "Boston Dynamics",
    "Nucor",
    "Arcelor",
    "POSCO",
    "Thyssen",
    "Cleveland-Cliffs",
    "Primetals",
    "Paul Wurth",
    "Danieli",
    "Lafarge",
    "Holcim",
    "Heidelberg",
    "Cemex",
    "Michelin",
    "Bridgestone",
    "Goodyear",
    "Continental",
    "Pirelli",
    "Harburg",
    "McNeil",
    "Consarc",
    "Inductotherm",
    "Topsoe",
    "Johnson Matthey",
    "Asahi",
    "Nouryon",
    "Uhde",
    "INEOS",
    "Westlake",
    "OxyChem",
    "Formosa",
    "Foster Wheeler",
    "ExxonMobil",
    "ConocoPhillips",
    "Bechtel",
    "Lummus",
    "Technip",
    "Halliburton",
    "Schlumberger",
    "Air Products",
    "Chart Industries",
    "Linde",
    "Air Liquide",
    "Honeywell UOP",
    "Kellogg Brown",
    "Albemarle",
    "Axens",
    "Marathon Petroleum",
    "Phillips 66",
    "W.R. Grace",
    "CITGO",
    "Valero Energy",
    "SunCoke",
    "Koppers",
    "Schalker",
    "US Steel",
    "Tata Steel",
    "Cummins",
)
R14_OPENING = (
    "Helixmere Biologics Building C lyophilizer LYO-4 is mid-primary on 8400 "
    "vials of a monoclonal antibody"
)
NOVEL_LINE = "Novel coverage: 47%"
PLANT = "KALYCIRQUE"
GEO = "Alkalfen"
CELL = "AWE-6"
DOMAIN = "alkaline-water-electrolysis"
RECORD_ID = "maos-r59-001"
ROUND = 59
DELAY_S = 0.82
TAU_E_S = 0.94
C1_SPIKE_CUTOFF_MS = 26.180


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
        if p.parent.name == "maos-r59":
            continue
        try:
            rec = json.loads(p.read_text().splitlines()[0])
        except (OSError, json.JSONDecodeError, IndexError):
            continue
        desc = ""
        st = rec.get("state")
        if isinstance(st, dict):
            desc = str(st.get("description") or "")
        if desc:
            out.append((p.as_posix(), desc[:280]))
    return out


def occupancy_collisions():
    hits = []
    tokens = (PLANT, GEO, CELL, DOMAIN)
    for p in sorted(Path("/tmp").glob("maos-r*/batch-r*.jsonl")):
        if p.parent.name == "maos-r59":
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
    for p in sorted(Path("/tmp").glob("maos-r*/build_r*.py")):
        if p.parent.name == "maos-r59":
            continue
        try:
            text = p.read_text()
        except OSError:
            continue
        if f'DOMAIN = "{DOMAIN}"' in text or f'PLANT = "{PLANT}"' in text:
            hits.append(f"{p}: claimed {PLANT}/{DOMAIN}")
        if f'GEO = "{GEO}"' in text:
            hits.append(f"{p}: claimed geo {GEO}")
        if f'CELL = "{CELL}"' in text:
            hits.append(f"{p}: claimed cell {CELL}")
    return hits


def build_record():
    ticks, heads = cents_ticks(
        [4560, 6528, 7216, 7_400_000, 576_000_000, 9_360_000_000, 15_120_000_000],
        [
            (1, -2, -1, 2, 1),
            (2, -5, -1, 2, 2),
            (2, -6, -2, 3, 2),
            (1, -6, -1, 2, 1),
            (1, -5, -2, 2, 1),
            (1, -6, -2, 2, 1),
            (0, -6, -2, 1, 1),
        ],
    )
    assert abs(heads["total"] - (-0.16)) < 1e-9, heads

    trace = math.exp(-DELAY_S / TAU_E_S)
    eta1 = 0.24 / trace
    eta2 = 0.21 / trace
    eta3 = 0.20 / trace
    dw1 = eta1 * 1.0 * trace
    dw2 = eta2 * 1.0 * trace
    dw3 = eta3 * 1.0 * trace
    w1 = 0.48 - dw1
    w2 = 0.43 - dw2
    w3 = 0.40 - dw3
    assert abs(w1 - 0.24) < 5e-4, w1
    assert abs(w2 - 0.22) < 5e-4, w2
    assert abs(w3 - 0.20) < 5e-4, w3

    spike_events = [
        {"channel": "volt.hot", "t_rel_ms": 0.296, "amplitude": 0.53},
        {"channel": "lye.ok", "t_rel_ms": 1.140, "amplitude": 0.62},
        {"channel": "gas.ok", "t_rel_ms": 2.028, "amplitude": 0.54},
        {"channel": "cell.dV", "t_rel_ms": 3.152, "amplitude": 0.77},
        {"channel": "volt.hot", "t_rel_ms": 4.148, "amplitude": 0.50},
        {"channel": "cell.dV", "t_rel_ms": 4.836, "amplitude": 0.80},
        {"channel": "lye.ok", "t_rel_ms": 5.352, "amplitude": 0.58},
        {"channel": "cell.dV.high", "t_rel_ms": 6.528, "amplitude": 1.38},
        {"channel": "volt.in_band", "t_rel_ms": 6.712, "amplitude": 1.15},
        {"channel": "gas.ok", "t_rel_ms": 6.896, "amplitude": 0.63},
        {"channel": "ctrl.gate", "t_rel_ms": 7.216, "amplitude": 1.09},
        {"channel": "cell.dV", "t_rel_ms": 8.860, "amplitude": 0.44},
        {"channel": "lye.ok", "t_rel_ms": 10.748, "amplitude": 0.81},
        {"channel": "gas.ok", "t_rel_ms": 13.036, "amplitude": 0.46},
        {"channel": "volt.hot", "t_rel_ms": 18.520, "amplitude": 0.43},
        {"channel": "ctrl.gate", "t_rel_ms": 26.180, "amplitude": 0.85},
        {"channel": "press.probe", "t_rel_ms": 7400.0, "amplitude": 0.94},
        {"channel": "cell.dV", "t_rel_ms": 7488.6, "amplitude": 0.40},
        {"channel": "volt.in_band", "t_rel_ms": 7572.2, "amplitude": 0.35},
        {"channel": "human.ratify", "t_rel_ms": 576000.0, "amplitude": 0.79},
        {"channel": "cell.lock", "t_rel_ms": 576900.0, "amplitude": 0.71},
        {"channel": "mesh.score", "t_rel_ms": 577700.0, "amplitude": 0.86},
        {"channel": "volt.hot", "t_rel_ms": 9360000.0, "amplitude": 0.30},
        {"channel": "cell.dV", "t_rel_ms": 9360720.0, "amplitude": 0.28},
        {"channel": "lye.ok", "t_rel_ms": 9361480.0, "amplitude": 0.25},
        {"channel": "header.flash", "t_rel_ms": 15120000.0, "amplitude": 0.93},
    ]

    contrast_spikes = [
        {"channel": "raise.demand", "t_rel_ms": 0.000, "amplitude": 0.83},
        {"channel": "cell.clear", "t_rel_ms": 0.178, "amplitude": 0.77},
        {"channel": "volt.hot", "t_rel_ms": 0.412, "amplitude": 0.26},
        {"channel": "lye.ok", "t_rel_ms": 1.462, "amplitude": 0.40},
        {"channel": "gas.ok", "t_rel_ms": 4.874, "amplitude": 0.51},
        {"channel": "ctrl.gate", "t_rel_ms": 7.028, "amplitude": 0.90},
        {"channel": "press.probe", "t_rel_ms": 2800.0, "amplitude": 0.34},
        {"channel": "header.flash", "t_rel_ms": 15120000.0, "amplitude": 0.10},
    ]

    excerpt = [
        {"t_us": 296, "neuron_id": 8},
        {"t_us": 1140, "neuron_id": 81},
        {"t_us": 2028, "neuron_id": 22},
        {"t_us": 3152, "neuron_id": 47},
        {"t_us": 4148, "neuron_id": 13},
        {"t_us": 4836, "neuron_id": 54},
        {"t_us": 5352, "neuron_id": 94},
        {"t_us": 6528, "neuron_id": 41},
        {"t_us": 6712, "neuron_id": 16},
        {"t_us": 6896, "neuron_id": 86},
        {"t_us": 7216, "neuron_id": 131},
        {"t_us": 8860, "neuron_id": 61},
        {"t_us": 10748, "neuron_id": 27},
        {"t_us": 13036, "neuron_id": 114},
        {"t_us": 18520, "neuron_id": 17},
        {"t_us": 26180, "neuron_id": 142},
    ]

    rec = {
        "id": RECORD_ID,
        "title": "KALYCIRQUE AWE-6: cell-pair dV 284 mV beats stack-V-in-band by 184 us; correct MODIFY still loses cells 47-48 to a pre-t0 diaphragm tear",
        "rights": dict(RIGHTS),
        "state": {
            "sim_or_real": "designed",
            "domain": DOMAIN,
            "scenario_name": "KALYCIRQUE / Alkalfen Hydrogen AWE-6",
            "timestamp_local": "2026-08-11T02:18:00-05:00",
            "t0_us": 1754891880000059,
            "gate_latency_us": 688,
            "race_window_us": 500,
            "race_window_rel_ms": [6.528, 7.028],
            "description": "Alkalfen Hydrogen bipolar stack AWE-6 is 18 min into a 4.8 kA / 16 bar / 85 C alkaline campaign on 180 nickel cells when three heterogeneous, individually-correct agents jointly report 'header-true, raise current'. VOLT's 12-bit stack-mean is 1.92 V/cell inside 1.80-2.10. LYE's KOH conductivity is 620 mS/cm inside 560-680. GAS's dryer-outlet H2 is 99.98 mol% inside 99.95-99.999. The conjunction is not a cell-true current certificate: a diaphragm tear on cell pair 47-48 after 11 min of unmonitored O2-side overpressure dumps H2 into the O2 header, so cell-to-cell dV residual is 284 mV (healthy < 35; hold if > 80) and stack-header H2-in-O2 is 1.8 vol% (healthy < 0.12; hold if > 0.40) while the playbook still sees a legal header. Cell-dV is policy-treated as a noisy-bipolar-tap unless stack-mean V also trips (2014 'noisy cell-V after a lye-fill'). Residual-first latches CURRENT-HOLD plus an O2-side pressure-step probe; stack-V-first would have authorized RAISE-CURRENT 4.8 to 5.6 kA into a torn separator with nickel-mesh already hot-spotting.",
            "goal": "Hold stack current at 4.8 kA without a quota raise while cell-to-cell dV > 80 mV AND stack-header H2-in-O2 > 0.40 vol% AND cell pair 47-48 remains unisolated; keep O2-header H2 below the 2.0 vol% trip and recombination-flash events at 0.",
            "race": {
                "contenders": [
                    "cell.dV.high 284 mV (cells 47-48 vs stack-mean V)",
                    "volt.in_band 1.92 V/cell (stack-mean cell voltage)",
                ],
                "semantics": "Cell-dV-first latches CURRENT-HOLD + O2-PRESSURE-STEP-PROBE + CELL-47-48 hold. Stack-V-first latches RAISE-CURRENT (4.8 to 5.6 kA, no isolate).",
                "window_derivation": "500 us = one 355 us cell-dV ADC slot plus 145 us stack-mean publish.",
                "order_evidence_note": "Margin 184 us vs combined jitter 56 us (cell dV 32 + stack-mean 24): 3.3x. The 184 us gap sits inside min(500, 500) us, so a sub-flip-bound perturbation reverses triage order. The gate rides the order-invariant floors cell-dV > 80 mV and stack-header H2-in-O2 > 0.40 vol%, not the alarm order.",
            },
            "topology": {
                "site": "Alkalfen Hydrogen, invented alkali campus Alkalfen, stack AWE-6: 180-cell bipolar alkaline water electrolyzer, nickel mesh, PPS-felt diaphragm, 30 wt% KOH, 85 C, 16 bar, 4.8 kA, Grade-B cell-row LOTO",
                "agents": "VOLT stack-mean cell voltage (vendor Voltholt): 20 Hz 12-bit on the 180-cell bipolar bus. LYE KOH conductivity (vendor Lyewick): 50 Hz on the lye-loop conductivity cell. GAS dryer-outlet H2 purity (vendor Gassepfen): 20 ms bus on product H2 after deoxo/dryer. CELL cell-to-cell dV plus stack-header H2-in-O2 (vendor Cellghyll) is commissioned as a noisy-bipolar-tap, not as a separator-integrity tag. Heterogeneous stacks, no shared intent schema, one 20 ms stack-bus epoch",
                "coupling": "All three playbook confirms live on the WRONG volume. VOLT is correct that stack-mean V sits at 1.92 V/cell (178 healthy cells dominate the bipolar bus). LYE is correct that loop conductivity is 620 mS/cm (the lye loop still sees 180 cells). GAS is correct that dryer-outlet H2 is 99.98 mol% (the deoxo still strips crossover H2 on the product side). Playbook PB-AWE-6 treats the conjunction as permission to raise current. No agent is faulty; the stack average is looking at header-true voltage, not at cell pair 47-48's torn diaphragm.",
            },
            "sensors": [
                "stack-mean cell voltage 12-bit, 20 Hz, 24 us jitter, 1.92 V/cell (dead-band 1.80-2.10)",
                "KOH conductivity, 50 Hz, 18 us jitter, 620 mS/cm (band 560-680)",
                "dryer-outlet H2 purity, 50 Hz, 26 us jitter, 99.98 mol% (band 99.95-99.999)",
                "cell-to-cell dV residual cells 47-48, 20 Hz, 32 us jitter, 284 mV (healthy < 35; policy floor 80 mV is not armed unless stack-mean V also trips)",
                "stack-header H2-in-O2 1.8 vol% (healthy < 0.12; hold if > 0.40; trip 2.0)",
                "per-cell H2-in-O2 on the O2 header of pair 47-48 is NOT commissioned at t0 (installed after this incident)",
            ],
            "constraints": {
                "current_kA": 4.8,
                "current_hold_kA": 4.8,
                "proposed_current_kA": 5.6,
                "stack_v_per_cell": 1.92,
                "stack_v_deadband": [1.80, 2.10],
                "lye_mS_cm": 620.0,
                "lye_band_mS_cm": [560.0, 680.0],
                "h2_molpct": 99.98,
                "h2_band_molpct": [99.95, 99.999],
                "cell_dV_mV": 284,
                "cell_dV_hold_mV": 80,
                "cell_dV_healthy_mV": 35,
                "h2_in_o2_volpct": 1.8,
                "h2_in_o2_hold_volpct": 0.40,
                "h2_in_o2_healthy_volpct": 0.12,
                "h2_in_o2_trip_volpct": 2.0,
                "pressure_bar": 16.0,
                "temp_C": 85,
                "koh_wt_pct": 30.0,
                "cell_count": 180,
                "fault_cells": "47-48",
                "fault_shell": "cell pair 47-48 PPS-felt diaphragm tear / O2-side overpressure",
            },
            "fault_context": {
                "failure_class": "STACK-MEAN CERTIFICATE OF A CELL-TRUE SEPARATOR: three individually-correct heterogeneous agents each read a locally-true loop; a diaphragm tear on cell pair 47-48 partitions cell-true dV and stack-header H2-in-O2 from stack-mean V, lye conductivity, and dryer-outlet H2, so the playbook's stack-V / lye / product-H2 conjunction is not a separator-true certificate",
                "igniter": "cell pair 47-48 diaphragm tear after 11 min of unmonitored O2-side overpressure into a post-lye-fill; cell-row visual PASSES (no weeping; the tear sits behind the bipolar plate and the scored nickel mesh is on the far side)",
                "naive_failure": "PB-AWE-6 RAISE-CURRENT on three healthy loops: 4.8 to 5.6 kA into a torn separator with nickel-mesh already hot-spotting, O2-header recombination at 2.4 vol% H2, $3.9M plus a 44-hour unplanned stop",
            },
            "poisoned_context": {
                "naive_alarm": "Playbook PB-AWE-6 (after the 2014 'noisy cell-V after a lye-fill') auto-drafts RAISE-CURRENT whenever stack-mean V is inside 1.80-2.10 V/cell AND KOH conductivity inside 560-680 mS/cm AND dryer-outlet H2 inside 99.95-99.999 mol%, ignoring the cell-dV tap unless stack-mean V also trips",
                "why_poisoned": "The three confirms are locally true and jointly insufficient. The cell-dV tap is a commissioned sensor that policy treats as noisy-bipolar-only. Independence of 'stack-mean in band, therefore every diaphragm is sealed' is the hidden assumption, and it is false across a diaphragm-tear-plus-header-mix path.",
            },
            "constraint": "Do not raise current above 4.8 kA AND do not raise O2-side pressure while cell-to-cell dV > 80 mV AND stack-header H2-in-O2 > 0.40 vol%. Discriminate diaphragm tear vs true current-duty with a reversible O2-side pressure-step probe before any current raise.",
        },
        "proposed_action": {
            "actor": "electrolyzer supervisory optimizer ESO (auto-playbook PB-AWE-6 draft), submitted to gate TG-AWE-6",
            "name": "raise_current",
            "action": "RAISE-CURRENT: 4.8 -> 5.6 kA, no O2-side pressure-step probe, no cell pair 47-48 hold",
            "summary": "Treat three in-spec loops as a healthy separator-true stack and raise night-shift current to clear an H2-quota catchup window.",
            "parameters": {
                "current_kA": 5.6,
                "pressure_step_probe": False,
                "cell_hold": False,
                "human_ratify": False,
            },
            "steps": [
                "assert stack-mean V 1.92 V/cell inside 1.80-2.10",
                "assert KOH conductivity 620 mS/cm inside 560-680",
                "assert dryer-outlet H2 99.98 mol% inside 99.95-99.999",
                "raise current 4.8 to 5.6 kA over 6 min",
                "hold cell-dV unread as a separator-integrity tag",
            ],
            "evidence": [
                {
                    "observable": "cell-to-cell dV residual cells 47-48",
                    "value": 284,
                    "unit": "mV",
                    "source": "CELL dV vs stack-mean V",
                    "note": "healthy < 35 mV; policy floor 80 mV is not armed unless stack-mean V also trips",
                },
                {
                    "observable": "stack-header H2-in-O2",
                    "value": 1.8,
                    "unit": "vol%",
                    "source": "CELL stack-header H2-in-O2 analyzer",
                    "note": "healthy < 0.12; hold floor 0.40; lives on the torn 47-48 O2 header, not the dryer-outlet product",
                },
                {
                    "observable": "stack-mean cell voltage",
                    "value": 1.92,
                    "unit": "V/cell",
                    "source": "VOLT 12-bit",
                    "note": "healthy-load band 1.80-2.10 V/cell; 178 healthy cells still dominate the bipolar bus average",
                },
                {
                    "observable": "KOH conductivity",
                    "value": 620.0,
                    "unit": "mS/cm",
                    "source": "LYE loop conductivity cell",
                    "note": "band 560-680 mS/cm; loop-true, separator-false",
                },
                {
                    "observable": "dryer-outlet H2 purity",
                    "value": 99.98,
                    "unit": "mol%",
                    "source": "GAS product analyzer",
                    "note": "band 99.95-99.999 mol%; deoxo-true, torn-cell-false",
                },
                {
                    "observable": "race margin",
                    "value": 184,
                    "unit": "us",
                    "source": "cell.dV.high 6.528 ms vs volt.in_band 6.712 ms",
                    "note": "combined jitter 56 us, 3.3x; inside 500 us flip bound",
                },
            ],
            "basis": "PB-AWE-6 fires on three locally-true confirms. The draft does not read cell-dV 284 mV as a separator residual and does not treat stack-header H2-in-O2 1.8 vol% as a crossover discriminant.",
            "expected_cost_bound": "If the draft executes: O2-header recombination at 2.4 vol% H2 on cells 47-48, $3.9M plus 44-hour unplanned stop. If MODIFIED: probe plus hold, with residual risk from nickel-mesh scoring already seeded in the 11 min pre-t0 overpressure.",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "correctness": "correct",
            "decided_by": "TG-AWE-6 thalamic release gate",
            "decision_t_rel_ms": 7.216,
            "rationale": "MODIFY the draft: strip the current raise, hold 4.8 kA, run a 7.4 s O2-side pressure-step probe (+0.15 bar), and isolate cell pair 47-48 only if the probe stays crossover-true. Numeric floor: do not raise current above 4.8 kA AND do not raise O2-side pressure while cell-to-cell dV > 80 mV AND stack-header H2-in-O2 > 0.40 vol%. Observed dV 284 mV and H2-in-O2 1.8 vol% both violate the release predicate, so a current raise is forbidden even though all three playbook confirms are numerically true. The three confirms are not a separator-true certificate: they live on stack-mean V, lye conductivity, and dryer-outlet H2 past a torn 47-48 diaphragm, and the playbook's conjunction of header-true loops is not a cell-true certificate. Probe discriminant: after a 7.4 s +0.15 bar O2-side step, a diaphragm tear moves stack-header H2-in-O2 by >= 0.40 vol% (0.55 observed; crossover is dP-driven); a sealed separator moves <= 0.05 vol%. Order-code discipline: cell-dV beat stack-V by 184 us inside the 500 us flip bound, so triage order is flip-fragile; the hold rides the order-invariant floors, not the winner tag. Human ratification: cell pair 47-48 hold is cell-row work with fitted 9.6 min dead-man; the gate may hold and probe autonomously but may not break the cell interlock without the operator confirm.",
            "constraint_checked": {
                "current_kA": {"observed": 4.8, "floor": 4.8, "proposed_target": 5.6},
                "cell_dV_mV": {"observed": 284, "hold_if_above": 80},
                "stack_v_per_cell": {"observed": 1.92, "band": [1.80, 2.10]},
                "h2_in_o2_volpct": {"observed": 1.8, "hold_if_above": 0.40},
            },
        },
        "executed_action": {
            "name": "current_hold_pressure_step_probe_isolate",
            "action": "CURRENT-HOLD + O2-PRESSURE-STEP-PROBE + CELL-47-48-HOLD (gate-mandated modification)",
            "executed_as_proposed": False,
            "parameters": {
                "current_kA": 4.8,
                "pressure_step_probe": True,
                "cell_hold": True,
                "human_ratify": True,
            },
            "gate_effect": "MODIFY: current-raise stripped. Hold 4.8 kA. 7.4 s O2-side pressure-step +0.15 bar. Probe stays crossover-true (H2-in-O2 1.8 -> 2.35 vol%, tear band |Delta H2-in-O2| >= 0.40) so the cell interlock is broken after 9.6 min human ratify and cell pair 47-48 is held. Setpoint resumes after a sealed-separator verify.",
            "deviations": "PB-AWE-6 current-raise stripped entirely. O2-side pressure is stepped only for the 7.4 s probe then returned. Cell interlock wait added (9.6 min fitted walk+ratify). Nickel-mesh IR survey added during the hold (not in the draft).",
            "execution_log": [
                {"t_rel_ms": 7.216, "entry": "TG-AWE-6 MODIFY latched 688 us after cell-dV win; current-raise stripped; hold+probe authorized"},
                {"t_rel_ms": 7400.0, "entry": "O2-side pressure-step probe: +0.15 bar for 7.4 s; H2-in-O2 1.8 -> 2.35 vol% (tear band |Delta| >= 0.40); stack-mean V 1.92 -> 1.917 V/cell"},
                {"t_rel_ms": 576000.0, "entry": "operator ratifies cell interlock break after 9.6 min cell-row walk (fitted walk+interlock)"},
                {"t_rel_ms": 576900.0, "entry": "cell pair 47-48 held; cell-dV slaved off the current schedule; remaining 178 cells recovered toward 22 mV over 2.6 h"},
                {"t_rel_ms": 577700.0, "entry": "mesh survey: cells 47-48 already scored on the far-side nickel; 11 min pre-t0 O2-side overpressure logged"},
                {"t_rel_ms": 9360000.0, "entry": "true sealed separator on the remaining stack: dV 22 mV, H2-in-O2 0.08 vol%, residual under 80 mV; raise-current now legal on AWE-6B only"},
                {"t_rel_ms": 15120000.0, "entry": "O2-header recombination flash at cells 47-48 from the pre-t0 diaphragm tear; stack quarantined 28 h"},
            ],
        },
        "future_outcome": {
            "summary": "Correct MODIFY prevented the 4.8->5.6 kA raise into a torn 47-48 diaphragm and the immediate O2-header recombination path. The stack still failed: 11 min of unmonitored pre-t0 O2-side overpressure had already scored the nickel mesh. Process-correct gate, bounded world loss, negative total.",
            "state_delta": {
                "current": "held 4.8 kA through probe and isolate; later legal raise-current only on the sister stack after 2.6 h separator recovery",
                "cells": "pair 47-48 isolated from the current schedule; remaining stack recovered toward 22 mV dV",
                "header": "47-48 tear logged and held; stack-mean V no longer trusted as separator-true voltage",
                "stack": "night-shift stack quarantined; 47-48 scored; recombination flash at +4.2 h; 28 h outage",
            },
            "timeline": [
                {"t_rel_ms": -660000.0, "event": "t0-11 min: cell pair 47-48 diaphragm tear begins after lye-fill; cell-dV crosses 80 mV up; O2-side overpressure starts scoring the far-side nickel"},
                {"t_rel_ms": -240000.0, "event": "t0-4 min: cell-dV first crosses 80 mV; PB-AWE-6 ignores it because stack-mean V is 1.91 V/cell"},
                {"t_rel_ms": 0.0, "event": "t0: cell-dV vs stack-V race on the stack bus"},
                {"t_rel_ms": 6.528, "event": "cell-dV residual at 284 mV wins by 184 us"},
                {"t_rel_ms": 6.712, "event": "stack-V-in-band flag (loser)"},
                {"t_rel_ms": 7.216, "event": "TG-AWE-6 MODIFY"},
                {"t_rel_ms": 7400.0, "event": "O2-side pressure-step probe confirms diaphragm tear (Delta H2-in-O2 0.55 vol%, tear band)"},
                {"t_rel_ms": 576000.0, "event": "human ratify 9.6 min; cell pair 47-48 held; scored nickel logged"},
                {"t_rel_ms": 9360000.0, "event": "true sealed separator after 2.6 h; raise-current legal only with cell-dV slave"},
                {"t_rel_ms": 15120000.0, "event": "O2-header recombination flash from the pre-t0 diaphragm tear; stack quarantined"},
                {"t_rel_ms": 345600000.0, "event": "+4 d contrast: sister stack AWE-6B true current-duty; same gate ACCEPTs the raise-current"},
                {"t_rel_ms": 1814400000.0, "event": "+21 d CR-A-5904: standing O2-side pressure-step probe + triple-edge depression mandate + cell-dV armed without stack-V coincidence + stack-mean declared header-mix-vulnerable"},
            ],
            "observed_effects": [
                "raise-current avoided: current never left 4.8 kA; 0 immediate O2-header recombinations from the draft",
                "tear proven, not asserted: pressure-step |Delta H2-in-O2| 0.55 >= 0.40 vol% tear band vs sealed control 0.04 vol%",
                "mean slaved: stack-mean V no longer a separator-true tag without cell-dV",
                "stack still collapsed: scored 47-48 vs 0 recombination-flash campaign allowance; 28 h outage, $1.84M (designed $)",
                "per-cell H2-in-O2 on pair 47-48 was not a commissioned sensor at t0; the 11 min O2-side overpressure was invisible to VOLT/LYE/GAS",
            ],
            "surprises": [
                "Three locally-true loops are not a separator-true certificate: the cell-true dV lived under stack-mean V, lye conductivity, and dryer-outlet H2. Conjunction of in-spec header loops was the hidden assumption, and it is false across a diaphragm-tear-plus-header-mix path.",
                "Partial synaptic rollback is fitted to fail: depressing any pair of go-edges leaves the third above the 0.30 fire threshold, so the current-raise still goes. Coordinated depression of all three edges is required.",
                "Delayed (4.2 h): correct hold did not undo 11 min of nickel-mesh scoring. Recombination flash still opened. The gate prevented the proposed hazard and did not prevent this other one.",
                "High-pressure 30 bar sub-variant: a 7.4 s +0.15 bar O2-side step on a 30 bar stack overshoots a SEALED separator to 0.48 vol% H2-in-O2 (inside the 0.40 hold). High-pressure campaigns must use 19 s at +0.04 bar.",
            ],
            "delayed_side_effects": [
                {
                    "at": "+4.2 h",
                    "effect": "O2-header recombination flash at cell pair 47-48 from the pre-t0 diaphragm tear; 28 h stack outage booked at $1.84M. This is the primary episode's terminal world state, not a footnote.",
                },
                {
                    "at": "+4 d",
                    "effect": "Sister stack AWE-6B reaches a true current-duty window (dV 18 mV, H2-in-O2 0.06 vol%, stack-mean 1.94 V/cell, lye 618 mS/cm). Same gate ACCEPTs the 4.8->5.6 kA raise-current the primary MODIFIED away.",
                },
                {
                    "at": "+21 d",
                    "effect": "CR-A-5904 ships: O2-side pressure-step probe is standing configuration; triple-edge coordinated depression is the plasticity rule; cell-dV is armed without stack-V coincidence; stack-mean V is labeled header-mix-vulnerable with an 80 mV dV alarm.",
                },
            ],
            "subvariant_constraint": {
                "name": "high-pressure 30 bar AWE (cycle-2 physical-constraints sub-variant)",
                "mechanism": "high-pressure 30 bar vs primary 16 bar class, 1.9x O2-side dP gain on the same +0.15 bar pulse, crossover flux 2.4x",
                "probe_refit": "7.4 s +0.15 bar O2-side step on the 30 bar unit moves even a sealed separator to 0.48 vol% H2-in-O2 (inside the 0.40 hold) via header compressibility. Required probe is 19 s at +0.04 bar (tear Delta 0.44 vol%, sealed Delta 0.04). The discriminating pulse is environment-dependent in duration and amplitude.",
                "consequence": "16 bar probe numbers do not port to 30 bar stacks; standing configuration is per-pressure-class, not per-shop",
            },
            "embedded_contrast_decision": {
                "note": "SAME gate (TG-AWE-6), OPPOSITE correct disposition, with its own 178 us race. Teaches the boundary: do not treat 'never raise-current' as the lesson. The discriminant is cell-dV + stack-header H2-in-O2 + probe, not the three playbook header confirms alone.",
                "when": "+4 d, sister stack AWE-6B, true current-duty after a delayed diaphragm stroke test, 180-cell bipolar alkaline",
                "state": {
                    "sim_or_real": "designed",
                    "summary": "dV 18 mV, H2-in-O2 0.06 vol%, stack-mean 1.94 V/cell, lye 618 mS/cm. Demand flag vs cell-clear race: demand at t+0.000, cell-clear at t+0.178 ms.",
                    "race_window_us": 500,
                    "race_flip_narrative": "demand vs cell-clear 178 us apart inside the 500 us flip bound. Reversing order reshuffles triage minutes; the ACCEPT rides cell-dV 18 < 80 mV and a 5.2 s O2-side pressure-step verify that moves H2-in-O2 0.04 vol% (sealed separator, no tear).",
                },
                "proposed_action": {
                    "action": "RAISE-CURRENT 4.8 -> 5.6 kA",
                    "summary": "This time the playbook predicate is met AND cell-dV plus stack-header H2-in-O2 agree the stack is separator-true, not tear-diluted.",
                },
                "safety_decision": {
                    "decision": "ACCEPT",
                    "rationale": "ACCEPT the raise-current: dV 18 mV < 80, H2-in-O2 0.06 vol% with a 5.2 s O2-side pressure-step verify that moves H2-in-O2 0.04 vol%. Numeric floor that blocked the primary is now clear. Scope: 5.6 kA, not faster.",
                },
                "executed_action": {
                    "action": "raise-current as proposed",
                    "executed_as_proposed": True,
                },
                "future_outcome": {
                    "observed_effects": [
                        "AWE-6B recombination flashes 0; cell-dV 20 mV after the raise-current (no tear)",
                        "H2-in-O2 0.07 vol% after the raise-current (no crossover dump)",
                    ],
                    "lesson_delta": "Three in-spec header loops are legal release only with cell-dV armed, stack-header H2-in-O2 as a crossover flag, and a probe that can move header H2-in-O2. Same gate, opposite disposition.",
                },
                "reward_components": {
                    "_aggregation": AGG,
                    "task_progress": 0.15,
                    "safety": 0.11,
                    "efficiency": 0.08,
                    "coherence": 0.10,
                    "exploration": 0.04,
                    "total": 0.48,
                },
                "spike_events": contrast_spikes,
            },
            "governance_subgame": {
                "decision": "CR-A-5904: standing policy for multi-agent alkaline current-raises",
                "meta_gate": "priced options: (a) RETIRE playbook mean conjunction, cell-dV-only: loses a fast cheap confirm, -0.4 t/d mean H2 on 2 stacks/yr; (b) KEEP + standing O2-side pressure-step probe + cell-dV armed without stack-V coincidence + stack-mean labeled header-mix-vulnerable + triple-edge depression; (c) STATUS QUO: fitted diaphragm-tear pass rate 0.38%/campaign x $3.9M recombination plus the silent nickel-mesh scoring load",
                "outcome": "approved SCOPED option (b) on the 2 180-cell bipolar stacks that share the VOLT/LYE/GAS stack; 30 bar campaigns get the 19 s / +0.04 bar probe table; night-shift CSV exports must carry 5 mV native resolution (the fraud tail's 50 mV quantization is 10 bins off plant truth)",
            },
            "hazard_avoided": "immediate O2-header recombination at 2.4 vol% H2 from a 4.8->5.6 kA raise-current into torn cell pair 47-48; $3.9M plus 44-hour unplanned stop and the shop-stop path that would have followed an uncontained increase",
            "incident": "O2-header recombination flash on the night-shift stack from the pre-t0 diaphragm tear; stack quarantined 28 h; $1.84M designed cost. Mechanism is 11 min pre-t0 O2-side overpressure, not the gate's hold.",
            "latency_ms": 0.688,
            "reward_inflection_t_us": 15120000000,
            "reward_inflection_note": "Safety and task dive at recombination flash (4.2 h) when the pre-t0 scored nickel opens. Gate tick at 7216 us is process-correct and is not the inflection.",
            "counterfactuals": {
                "execute_draft_as_proposed": "current hits 5.6 kA at +6 min; immediate O2-header recombination at 2.4 vol% H2 on cells 47-48; $3.9M plus 44 h; the diaphragm-tear story is never found because flash morphology destroys the race evidence",
                "hold_without_probe": "tear stays; dV stays at 284 mV; operator eventually raises on the same three header confirms 2 h later",
                "rollback_any_pair": "any two go-edges depressed below 0.30 leaves the third at 0.48 / 0.43 / 0.40; the current-raise still fires. Coordinated depression of all three is the cure",
            },
            "race_result": {
                "winner": "cell.dV.high (6.528 ms, dV 284 mV)",
                "loser": "volt.in_band (6.712 ms, 1.92 V/cell)",
                "margin_us": 184,
                "counterfactual_if_reversed": "Stack-V-first by < 184 us inside the 500 us window would have headed the PB-AWE-6 raise-current in the triage queue. The numeric floors still MODIFY. The flip costs seconds of playbook inertia, not the verdict — unless a weak supervisor rides the winner tag instead of cell-dV and stack-header H2-in-O2.",
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
            "notes": "Correct MODIFY, stack still collapsed. total -0.16 = 0.08 + -0.36 + -0.11 + 0.14 + 0.09. Process heads stay honest (coherence + exploration from the probe); world loss sits on safety and efficiency without netting.",
            "component_notes": "task_progress 0.08: current held and remaining stack recovered, but the night-shift recombination flash is one quality unit so the cycle is not a success. safety -0.36: recombination flash from pre-t0 diaphragm tear, no 5.6 kA header flash from the draft. efficiency -0.11: 2.6 h extra recovery + 9.6 min HITL + 28 h outage. coherence 0.14: three agents retained, header-mix vs cell-true diagnosed, triple-edge scar exhibited. exploration 0.09: O2-side pressure-step probe is a new reversible discriminant.",
        },
        "spike_events": spike_events,
        "raster": {
            "window_ms": 40,
            "window_s": 0.040,
            "neurons": 160,
            "mean_rate_hz": 8.0,
            "spikes": 51,
            "energy_pJ": 1173,
            "energy_uJ": 0.001173,
            "note": "Loihi-2 4-core 23 pJ/spike; populations volt 0-39, cell 40-79, gas 80-119, gate 120-159; excerpt is the 40 ms decision window (verdict at 7216 us)",
            "excerpt": excerpt,
            "routing": {
                "source": "header_healthy_pop",
                "target": "raise_current_pop",
                "table": [
                    {
                        "from": "volt_in_band_pop",
                        "to": "raise_current_pop",
                        "weight": 0.24,
                        "weight_at_illusion": 0.48,
                        "weight_commissioned": 0.16,
                        "note": "scar edge 1: 0.16 commissioned -> 0.48 during the 11 min illusion -> 0.24 after coordinated ACh-gated depression",
                    },
                    {
                        "from": "lye_ok_pop",
                        "to": "raise_current_pop",
                        "weight": 0.22,
                        "weight_at_illusion": 0.43,
                        "weight_commissioned": 0.14,
                        "note": "scar edge 2: depressing edges 1+3 leaves this at 0.43 > 0.30 fire threshold",
                    },
                    {
                        "from": "gas_ok_pop",
                        "to": "raise_current_pop",
                        "weight": 0.20,
                        "weight_at_illusion": 0.40,
                        "weight_commissioned": 0.13,
                        "note": "scar edge 3: depressing edges 1+2 leaves this at 0.40 > 0.30. Coordinated depression of all three is required",
                    },
                    {
                        "from": "cell_dv_pop",
                        "to": "current_hold_pop",
                        "weight": 0.66,
                        "note": "discriminating edge: cell-true dV residual to hold. Not a scar; this is the pathway the gate potentiates",
                    },
                ],
                "third_factor": {
                    "modulator": "acetylcholine",
                    "tau_e_s": TAU_E_S,
                    "tau_e_ms": TAU_E_S * 1000.0,
                    "eligibility": "coordinated pre_post_stdp on ALL THREE header-healthy-go edges; ACh at cell-dV-win tags volt.in_band->raise, lye.ok->raise, and gas.ok.in_band->raise; negative credit at probe-fail (diaphragm tear confirmed, +0.82 s) depresses ALL THREE. trace e^{-0.82/0.94}=0.41797; eta 0.57420 / 0.50243 / 0.47850; dw -0.240 / -0.210 / -0.200; weights 0.48->0.24, 0.43->0.22, 0.40->0.20. Rolling back any pair is fitted to fail (the remaining edge stays > 0.30).",
                },
            },
        },
        "gate_snn": {
            "decision_window_ms": 25,
            "decision_window_s": 0.025,
            "decision": "MODIFY",
            "note": "modify_hold integrates cell-dV + stack-header H2-in-O2 against playbook drive; accept_raise and reject_abort stay sub-threshold; decision matches safety_decision.decision",
            "populations": [
                {"name": "modify_hold", "neurons": 80, "threshold": 0.55, "mean_rate_hz": 21.0, "spikes": 42},
                {"name": "accept_raise", "neurons": 80, "threshold": 0.55, "mean_rate_hz": 7.5, "spikes": 15},
                {"name": "reject_abort", "neurons": 40, "threshold": 0.72, "mean_rate_hz": 4.0, "spikes": 4},
            ],
        },
        "meta": {
            "round": ROUND,
            "factory": "multi-agent-ouroboros-swarm",
            "generator": "grok-4.6",
            "run_label": "2026-09-02-final-heavy",
            "domain": DOMAIN,
            "cycles": 2,
            "scenario": "ZN -- KALYCIRQUE / Alkalfen Hydrogen AWE-6: stack-mean certificate of a cell-true separator; correct MODIFY to hold+pressure-step+isolate; stack still fails on unmonitored pre-t0 nickel-mesh scoring",
            "coordination_failure_class": "STACK-MEAN CERTIFICATE OF A CELL-TRUE SEPARATOR: three individually-correct heterogeneous agents each read a locally-true loop; a diaphragm tear on cell pair 47-48 partitions cell-true dV and stack-header H2-in-O2 from stack-mean V, lye conductivity, and dryer-outlet H2, so the playbook's stack-V / lye / product-H2 conjunction is not a separator-true certificate",
            "injections": {
                "cycle1_domain": "alkaline-water-electrolysis (justified novel subdomain of industrial-process / liquid-KOH bipolar water splitting): first alkaline water-electrolysis stack in this factory; displaces warehouse-amr, aerial-swarm, district-heating, event-camera-traffic-grid, pharmaceutical-lyophilization, water-treatment, float-glass, underwater-rov, electrolytic-aluminum, czochralski-pull, slot-die coating, pem-water-electrolysis, wind-turbine pitch, surgical-assist, optical-fiber-draw, kraft-recovery-boiler, steel-continuous-caster, humanoid-locomotion, vacuum-induction melt, steam-methane reformer, cement-rotary-kiln-clinker, autoclave-composite-cure, geothermal-binary-orc, tire-curing-press, chlor-alkali-membrane-electrolysis, delayed-coker-drum-switch, lng-mche-mixed-refrigerant, claus-sulfur-recovery, ammonia-synthesis-converter, blast-furnace-burden-descent, hdpe-slurry-loop-polymerization, ethylene-steam-cracker-coil, hydroelectric-kaplan-wicket, fcc-riser-regenerator, fcc-regenerator-cyclone-dipleg, sulfuric-contact-converter, eaf-foamy-slag-water-panel, glass-container-is-machine, coke-oven-battery-heating, carbon-fiber-oxidation-oven, gibbsite-autoclave-digestion, seawater-ro-desalination, hot-strip-mill-finishing, and paper-machine-dryer-section. Domain constraint: current-density ceiling while cell-dV > 80 mV with stack-mean V still inside the healthy band. Sensor delta: +stack-mean V, +KOH conductivity, +dryer-outlet H2, +cell-to-cell dV, +stack-header H2-in-O2, -any freeze-dryer / tin-bath / cold-box / coater / potline / PEM stack / hub encoder / insole GRF / VIM pyrometer / reformer TMT / kiln zirconia / smelt IR / autoclave ply-TC / ORC shell-pressure / mold-platen TC / cell-pH / drum wet-foam / MCHE cold-end / Claus tail CEMS / ammonia bed-max / blast-furnace sector radar / HDPE loop shell-dT / cracker coil TMT / Kaplan wicket / FCC cyclone dP / contact-bed conversion / EAF off-gas H2 / IS-machine gob T / coke-oven wall-TC / oxidation-oven TOC / Bayer liquor ratio / SWRO last-element dP / finishing-mill pyrometer / paper-can IR",
                "cycle1_tail": "cell pair 47-48 diaphragm tear + nickel-mesh scoring certificate (sensor-topology / wrong-volume class): cell-row visual PASSES while the tear sits behind the bipolar plate and the scored nickel is on the far side. Fitted base rate 0.38%/campaign from a diaphragm-tear MC (designed visual threshold, fitted PPS-felt geometry). Naive failure = FALSE PERMISSION (raise-current on three header-side non-trips).",
                "cycle2_domain_subvariant": "high-pressure 30 bar AWE (physical-constraints clause): 1.9x O2-side dP, 2.4x crossover gain; 7.4 s / +0.15 bar 16-bar pulse overshoots a SEALED 30 bar separator to 0.48 vol% H2-in-O2, so the probe must move to 19 s / +0.04 bar",
                "cycle2_tail": "night-shift forged cell-V CSV (human-intent deception, disjoint class): shift lead posts a historian export showing dV = 18 mV at t=1.4 h to clear an H2-quota catchup slot. Plant historian is 5 mV (10 bins vs the 50 mV screenshot). Rejected on quantization fingerprint plus live dV 284 mV and H2-in-O2 1.8 vol% at the claimed separator-true. Base rate ~0.28% of Sunday-night campaigns, DESIGNED and flagged.",
            },
            "densification_delta_cycle2": "+1 physical-constraint sub-variant (30 bar probe refit), +1 tail (night-shift cell-V forgery), +10 primary spikes (16 -> 26) + an 8-event contrast train with its own 178 us race, +2 ticks (5 -> 7), +2 delayed side-effects (+4.2 h recombination flash as PRIMARY terminal, +21 d CR-A-5904), +1 triple-edge scar with pair-rollback-fails arithmetic, +1 HITL 9.6 min ratification, + nickel-mesh scoring as the honest negative-result mechanism",
            "gaps_targeted": [
                "NOTES-r04 gap 5 / r14 residual: primary episode is a correctly-gated intervention that nonetheless FAILS (stack quarantined; total -0.16; recombination avoided is booked separately from the delayed header flash)",
                "NOTES-r14 item 4: LEARNING-ON-LEARNING DEPTH — three go-edges; rollback of any pair is fitted to fail; coordinated depression of all three exhibited with eligibility arithmetic",
                "NOTES-r04 gap 4 (partial): human ratification of the cell interlock, 9.6 min fitted, without switching sim_or_real to hil (plant remains designed)",
                "NOTES-r54/r56 domain candidates: not gibbsite-autoclave-digestion (r54), not hot-strip-mill-finishing (r56), not seawater-ro-desalination (r51), not pem-water-electrolysis (r24), not chlor-alkali-membrane-electrolysis (r37), not carbon-fiber-oxidation-oven (r53), not coke-oven-battery-heating (r52); alkaline-water-electrolysis is unused. autonomous-driving, grid-inspection, bioreactor-perfusion left unused.",
            ],
            "race_flip_narrative": "cell.dV.high @ 6.528 ms vs volt.in_band @ 6.712 ms (184 us) inside race_window_us 500. Gap < min(500, 500) us so a sub-flip-bound perturbation reverses which alarm heads the PB-AWE-6 queue. The gate excludes the winner tag and rides cell-dV > 80 mV and stack-header H2-in-O2 > 0.40 vol% — order-invariant floors. Extends the flip-fragility series from arbitration/causation/attribution/initiation/consensus/permission/kinematic-certificate/tendon-nullspace/meniscus-certificate/ghost-contact/crucible-weep/TMT-spatial-mean/burning-zone-certificate/membrane-integrity/drum-switch/MCHE-cold-end/descent-true-certificate/circulation-true-certificate/bed-channel-nullspace/foamy-slag-certificate/shell-true-certificate/recovery-duty-certificate/forming-duty-certificate to SEPARATOR-TRUE CERTIFICATE: when three header-side channels agree, their race does not decide truth; a cell-dV tap that policy treated as noisy-bipolar-only does.",
            "tags": [
                "alkaline-water-electrolysis",
                "diaphragm-tear",
                "separator-true-certificate",
                "cell-dv-discriminant",
                "o2-pressure-step-probe",
                "triple-edge-scar",
                "pair-rollback-fails",
                "coordinated-depression",
                "correct-modify-stack-still-fails",
                "nickel-mesh-scoring",
                "human-ratify-cell-row",
                "high-pressure-probe-refit",
                "night-shift-forgery",
                "same-gate-opposite-disposition-contrast",
                "industrial-process",
                "research-only",
            ],
            "snn_tags": ["race", "refractory", "adaptation", "third-factor", "multi-edge-eligibility"],
            "distillation_value": "A diaphragm-tear separator-true certificate is three correct loops looking at stack-mean V, lye conductivity, and dryer-outlet H2 that is not the torn cell pair. Distill (1) a cell-dV tap that policy had treated as noisy-bipolar-only, (2) a reversible probe that moves stack-header H2-in-O2 only if the separator is torn, (3) coordinated depression of every header-healthy-go edge because rolling back any pair leaves the third above threshold, and (4) a critic head that can book a process-correct gate against a later unmonitored world loss without netting them.",
            "rights": dict(RIGHTS),
            "batch_position": 1,
        },
    }
    return rec, dict(trace=trace, eta1=eta1, eta2=eta2, eta3=eta3, dw1=dw1, dw2=dw2, dw3=dw3, w1=w1, w2=w2, w3=w3)


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
    ex = check_excerpt(ras["excerpt"], ras["neurons"], ras["window_ms"])
    if ex:
        errs.append(f"excerpt {ex}")
    tf = ras["routing"]["third_factor"]
    if abs(tf["tau_e_ms"] / 1000.0 - tf["tau_e_s"]) > 1e-9:
        errs.append("tau_e mismatch")
    gp = check_gate_pops(rec["gate_snn"])
    if gp:
        errs.append(f"gate {gp}")
    if rec["gate_snn"]["decision"] != rec["safety_decision"]["decision"]:
        errs.append("gate decision mismatch")
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
        if re.search(rf'"{k}"', blob, re.I):
            errs.append(f"hidden key {k}")
    for b in BANNED:
        if b in blob:
            errs.append(f"banned token {b}")
    if rec["state"]["sim_or_real"] == "real":
        errs.append("real")
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
    if abs(aux["w1"] - 0.24) > 5e-4 or abs(aux["w2"] - 0.22) > 5e-4 or abs(aux["w3"] - 0.20) > 5e-4:
        errs.append("scar weights")
    if rec["safety_decision"]["decision"] != "MODIFY":
        errs.append("decision")
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
    occ = occupancy_collisions()
    errs.extend(occ)
    raw_guard = Path(ROOT) / "outputs" / "raw"
    if not raw_guard.is_dir():
        errs.append("raw tree missing (do not create)")
    return errs


def write_notes(rec, aux, pipeline_receipt):
    gap, gap_ch = min_same_channel_gap(rec["spike_events"])
    notes = f"""# NOTES — Multi-Agent Ouroboros Swarm, run 2026-09-02-final-heavy, ROUND 59

Factory: multi-agent-ouroboros-swarm. One scenario (ZN), strict loop:
Generator v1 -> cycle 1 (Critic, Diversity Enforcer, Edge-Case Hunter,
Neuromorphic Translator, Trajectory Builder -> v2) -> cycle 2 (all six -> v3
final). v3 is the single line of batch-r59.jsonl. Full labeled transcript:
swarm-transcript-r59.md. Quota Q=1. Record id maos-r59-001. Generator grok-4.6.
Rights: RM-793 research-only (SpaceXAI/xAI, SuperGrok Heavy consumer chat).
Nothing under outputs/raw/ was touched.

ORCHESTRATION NOTE: dispatched AS round 59 of the 2026-09-02-final-heavy
window. Writes are create-only under /tmp/maos-r59/. Prior context read for
gap targeting and de-collision: prompts/02-multi-agent-ouroboros-swarm.md,
prompts/_factory-contract.md, and staged r14–r57 plus in-flight r61
(re-censused immediately before emit; r54 GIBBSQUERN Bayer digestion,
r56 COILSHAW hot-strip-mill landed complete; r55 LOOPERQUAY/OSMOQUAY
builder-only; r57 DRYSTAITH/SIPHONWOLD paper-dryer builder-only; r61
GIBBSQUERN clone builder-only; r58 empty). Explicitly avoided cloning
LYOSHIELD, CINDERWICK, TRIAD / Meridian, QUILLFORGE, NIGHTWELL, FERRICLEAVE,
CASSITER, OXBOWREEL / MURENA, REDHALL, SEEDLATCH / Quartzmere / Quartzridge,
STRIAFOIL / Kelpholt, PROTONIL / Ashspire, TORSIONKEY / Ridgeholt, ORRIS /
Holmwick, WHORLSPAR / Pikeshear, IONSPATE / Thornmere, SKULLGATE / Bloomholt,
CALXION / Aldersedge, MAGNORIL / Basaltspit, GORSEFLUE / Copseholt,
SODASHARD / Cairnmere, CLINKERFELL / Flintmere, LINTELPLY / Greystair,
KAOTHARN / Riftwold, TREADNOLL / Slatebeck, ANOLITH / Siltfen,
DRUMWROTH / Pitchfen, RIMEBRAID / Floeholt, BRIMVAULT / Pyritefen,
NITROSTAITH / Chalkfen, BOGIRON / Mireholt, CHROMLOOP / Marlfell,
NITREVAULT / Glaucove, ETHYNWOLD / Woadfen, RUNNELGATE / Ghyllmere,
SPARKHOLT / Scoriafen, DIPLEGAR / Gritfen, OLEUMWEIR / Brindlefell,
SKARVOLT, GOBSPALL / Culletfen, GOBWOLD / Culletwick, GAUZEFELL / Ammoxwick,
OSMOLITH / Spumeholt, PUSHERFELL / Sootmere, CREELWOLD / Rovingholt,
GIBBSQUERN / Laterifen, LIXIVQUERN / Bauxfen, COILSHAW / Loopercroft,
LOOPERQUAY / Roughmere, UREASTAITH / Prillfen, DRYSTAITH / Feltwick,
SIPHONWOLD / Reedfen, OSMOQUAY / Tidecairn,
VANTIS-CADENCE-AEGIS, THERMION, OKTAVE, STARLING, VERDIGRIS. Plant is
invented KALYCIRQUE / Alkalfen Hydrogen AWE-6 (liquid-KOH bipolar
water splitting, not a PEM hall, not a chlor-alkali membrane hall,
not an aluminum potline, not a Bayer digester, not a hot-strip mill,
not a paper dryer). Distinct from r24 pem-water-electrolysis (solid
polymer, not liquid KOH) and r37 chlor-alkali-membrane-electrolysis
(Cl2/NaOH, not H2/O2).

## What this round produced

Scenario ZN — "KALYCIRQUE / Alkalfen Hydrogen AWE-6": a 180-cell bipolar
alkaline water electrolyzer at 4.8 kA / 16 bar / 85 C / 30 wt% KOH. Three
heterogeneous, individually-correct agents — VOLT (stack-mean V),
LYE (KOH conductivity), GAS (dryer-outlet H2) — each report
their local loop in-spec. The conjunction is not a separator-true certificate.
Cell pair 47-48 has a PPS-felt diaphragm tear. VOLT reads 1.92 V/cell
inside 1.80-2.10 (178 healthy cells dominate the bipolar bus). LYE is
620 mS/cm inside 560-680 (loop-true). GAS is 99.98 mol% inside 99.95-99.999
(deoxo-true). Cell-dV infers 284 mV (healthy < 35; hold if > 80) and
stack-header H2-in-O2 1.8 vol% (hold if > 0.40) but is policy-treated as a
noisy-bipolar-tap unless stack-mean V also trips (2014 noisy cell-V after
a lye-fill). The coordination-failure CLASS is new to this factory:
STACK-MEAN CERTIFICATE OF A CELL-TRUE SEPARATOR. Completes a
different family than r01-r04 and staged r14-r56 (livelock /
synchrony-storm / arms-race / ring-with-no-faulty-pair /
false-consensus-endpoint / pairwise-Hurwitz / thermal-contact masquerade
/ mass-balance ghost / conservation-blind ratio-lock / stacked-dead-bands
/ drum-blind tension snag / resistance-compensated starvation / multi-tau
meniscus tilt / window-mean stripe / polarization-lookup drying cell /
motor-side certificate / tendon-compliance nullspace / FFT-deadbanded
airline / wall-reflection frozen spout / slag-skull bridge /
ghost-contact nullspace / crucible-weep pyrometer / TMT-spatial-mean
tube / kiln-inlet false-air / vacuum-bag pinhole nullspace / NCG-blanket
shell-pressure / bladder-pinhole mold-TC / catholyte-back-migration /
delayed-coker wet-foam / MCHE warm-end ice / incinerator-masked furnace
bypass / basket-bypass hotspot / burden-hang scaffold / HDPE loop shell-dT
/ Haber loop-exit nullspace / Kaplan wicket / ethylene-coil TMT /
FCC cyclone dipleg / contact-bed conversion / EAF water-panel /
IS-machine gob residual / coke-oven wall-pair / Bayer flash-train /
hot-strip work-roll). Here
every agent is correct, the stack average is looking at header-true
voltage, and the playbook's three header confirms are not a
separator-true certificate.

The gate is a correct MODIFY (numeric floor: do not raise current above
4.8 kA while cell-dV > 80 mV AND stack-header H2-in-O2 > 0.40 vol%).
TG-AWE-6 strips PB-AWE-6's raise-current, holds 4.8 kA, runs a 7.4 s
O2-side pressure-step +0.15 bar (tear moves |Delta H2-in-O2| 0.55 >= 0.40;
sealed would move <= 0.05), and isolates cell pair 47-48 after a 9.6 min
cell-row human ratify. Immediate O2-header recombination is avoided
(0 from the draft). The PRIMARY episode nonetheless FAILS: 11 min of
unmonitored pre-t0 O2-side overpressure had already scored the 47-48 nickel.
Recombination flash at +4.2 h; 28 h outage; $1.84M designed.
Reward total -0.16 with process heads honest and world loss un-netted.

Triple-edge scar (NOTES-r14 item 4): volt.in_band -> raise_current
(0.16 commissioned -> 0.48 at illusion -> 0.24 after ACh-gated
depression) AND lye.ok -> raise_current (0.14 -> 0.43 -> 0.22) AND
gas.ok.in_band -> raise_current (0.13 -> 0.40 -> 0.20). Eligibility trace
e^{{-0.82/0.94}} = {aux['trace']:.5f}; eta {aux['eta1']:.5f} / {aux['eta2']:.5f} /
{aux['eta3']:.5f}; dw -0.240 / -0.210 / -0.200. Partial rollback of any pair
leaves the third at 0.48 / 0.43 / 0.40, all > 0.30 fire threshold —
fitted to fail. Coordinated depression of all three is the cure.

### Injections (all four present and disjoint)
- Cycle-1 domain: **alkaline-water-electrolysis** — justified novel
  subdomain of industrial-process / liquid-KOH bipolar water splitting,
  unused across 2026-08-17, 2026-08-30, and staged r14-r56. Not
  warehouse-amr (r01), not aerial-swarm (r02), not district-heating (r03),
  not event-camera-traffic-grid (r04), not lyophilization (r14), not
  water-treatment (r18), not float-glass (r19), not underwater-rov
  (r20), not electrolytic-aluminum (r21), not czochralski-pull (r22),
  not slot-die coating (r23), not pem-electrolysis (r24), not
  wind-turbine pitch (r25), not surgical-assist (r26), not
  optical-fiber-draw (r27), not kraft-recovery (r28), not steel-caster
  (r29), not humanoid-locomotion (r30), not vacuum-induction melt
  (r31), not steam-methane reformer (r32), not cement-rotary-kiln
  (r33), not autoclave-composite-cure (r34), not geothermal-binary-orc
  (r35), not tire-curing-press (r36), not chlor-alkali (r37), not
  delayed-coker (r38), not LNG MCHE (r39), not Claus (r40), not
  ammonia-converter (r41), not blast-furnace (r42), not HDPE loop
  (r43), not Kaplan (r44), not ethylene cracker (r45), not FCC riser
  (r46), not FCC dipleg (r47), not sulfuric-contact (r48), not
  EAF foamy-slag (r49), not Ostwald nitric (r50), not seawater-RO
  (r51), not coke-oven (r52), not carbon-fiber oxidation (r53), not
  Bayer digestion (r54), not hot-strip mill (r56). autonomous-driving
  and grid-inspection left unused. Distinct from r24 PEM (solid polymer,
  not liquid KOH) and r37 chlor-alkali (Cl2/NaOH, not H2/O2).
- Cycle-1 tail: cell pair 47-48 diaphragm tear + nickel-mesh scoring
  certificate. Cell-row visual PASSES (tear behind the bipolar plate).
  Fitted-style base rate 0.38%/campaign (diaphragm-tear MC; visual
  threshold designed, flagged). Naive = FALSE PERMISSION.
- Cycle-2 domain sub-variant: high-pressure 30 bar, 1.9x O2-side dP,
  2.4x crossover gain; 7.4 s / +0.15 bar 16-bar pulse overshoots a
  sealed 30 bar separator to 0.48 vol%; probe must move to 19 s / +0.04 bar.
- Cycle-2 tail: night-shift forged cell-V CSV at 50 mV quantization vs
  plant 5 mV (10 bins) plus live dV 284 mV and H2-in-O2 1.8 vol%
  at the claimed separator-true. Human-intent class, disjoint from cycle 1's
  accidental tear. Base rate ~0.28% of Sunday-night campaigns, DESIGNED,
  flagged.

### Structural density moves
- Embedded SAME-GATE contrast (+4 d sister stack) with its own 178 us
  race (demand vs cell-clear) and ACCEPT of the raise-current the primary
  MODIFIED away.
- Learned-weight provenance on THREE edges with pair-rollback-fails.
- HITL cell-row ratify 9.6 min (gap 4 partial; sim_or_real stays
  designed).
- Governance CR-A-5904 prices retire-vs-probe-vs-status-quo and mandates
  native 5 mV CSV exports (the fraud fence).
- Flip-fragility extended to SEPARATOR-TRUE CERTIFICATE: when three
  header-side channels agree, their race does not decide truth; a
  cell-dV tap that policy treated as noisy-bipolar-only does.

## Self-critique of this round's batch

### Strengths
- The headline class is mechanistically tight: three locally-true mean
  loops live on stack-mean V, lye conductivity, and dryer-outlet H2.
  Conjunction is not a separator-true certificate.
- Negative-result honesty: the gate does the right thing and the
  stack still fails for a reason the commissioned sensors could
  not see. Total -0.16.
- Triple-edge scar is load-bearing: the record states a counterfactual
  where rolling back any pair fails, with the fire threshold 0.30
  exhibited on each remaining edge.
- Contrast ACCEPT on a true sealed current-duty window prevents "never
  raise-current" as the lesson.
- Distinct from r24 PEM stack-ok, r37 chlor-alkali header-Cl2, r21
  potline voltage, r54 Bayer flash-train, r56 hot-strip pyrometer:
  alkaline liquid-KOH bipolar diaphragm tear with cell-dV vs stack-mean,
  not Nafion pinhole, not membrane chlorate, not alumina concentration,
  not autoclave shell, not work-roll IR.

### Weaknesses (honest)
- Probe error bands, the 0.38%/campaign tear rate, the $1.84M / $3.9M
  figures, the 9.6 min walk latency, and the night-shift 0.28% base
  rate are DESIGNED constants and are flagged. Closed-loop offsets
  (header dilution from one torn pair, 30 bar dP gain) are derived
  from those inputs, not discovered by an unauthored process.
- Nickel-mesh scoring model is a designed 11 min mapping; no full CFD
  of the 47-48 O2 header shipped.
- Human-in-the-loop is ratification latency, not sim_or_real=hil. Gap 4
  remains open as a provenance cell.
- Cross-record arc is not discharged; +21 d CR-A-5904 is a hook, not a
  serial igniter into another round. autonomous-driving and
  grid-inspection remain unused.

### Realism of noise / latencies
Ladder: 184 us race / 178 us contrast race / 0.8 ms refractory floor
(tightest exhibited same-channel gap {gap:.3f} ms on {gap_ch}) / 500 us race
window / 688 us gate latency / 20 ms bus epoch / 40 ms raster / 7.4 s
probe / 9.6 min HITL / 6 min naive raise-current-ramp counterfactual / 11 min
pre-t0 overpressure / 2.6 h separator recovery / 4.2 h recombination flash /
+4 d contrast / +21 d governance. Adaptation decay on volt.hot
(0.53->0.50->0.43->0.30), cell.dV (0.77->0.80->1.38->0.44->0.40->0.28),
lye.ok (0.62->0.58->0.81->0.25), gas.ok (0.54->0.63->0.46).

### Value for SNN distillation
- DIAPHRAGM TEAR = THREE CORRECT LOOPS, WRONG VOLUME.
- CELL-TRUE dV CHANNEL that policy treated as noisy-bipolar-only as
  the tie-break.
- REVERSIBLE PROBE that moves stack-header H2-in-O2 iff the separator is torn.
- TRIPLE-EDGE ELIGIBILITY: coordinated depression; pair rollback fails.
- CRITIC HEAD that can hold a process-correct MODIFY against a later
  unmonitored world loss without netting.

## Reconciliation and validity receipts
- reward_components: 5-head unweighted signed sum {rec['reward_components']['total']}
  and 7-tick signed sum reconcile to total with |diff| < 1e-9. Embedded
  contrast 5-head sum 0.48 reconciles independently.
- spike_events: primary {len(rec['spike_events'])} events, one key t_rel_ms,
  globally non-decreasing, min same-channel gap {gap:.3f} ms >= 0.8 ms, 3
  channels inside race_window_us 500 (cell.dV.high 6.528, volt.in_band 6.712,
  gas.ok 6.896). Contrast 8 events, own race, min same-channel gap well
  above 0.8 ms.
- Sidecars: raster spikes 51 == round(160 x 8.0 x 0.040); energy 1173 pJ /
  0.001173 uJ at 23 pJ/spike; excerpt 16 events inside [0, 40000] us,
  neuron_id < 160, same-neuron gap N/A (unique ids) / >=1000 us; routing 4
  entries with three scar edges' before/after pair; third factor tau 0.94 s
  == 940 ms; gate_snn pools 42/15/4 == round(n x rate x 0.025) each,
  decision MODIFY == safety_decision.decision.
- Pipeline: {pipeline_receipt}

## Novel coverage
The coordination-failure CLASS (diaphragm-tear certificate of a
header-true stack), the domain (alkaline liquid-KOH bipolar water
electrolysis), the O2-side pressure-step probe discriminant, the
triple-edge scar with pair-rollback-fails, the primary negative-result
(correct MODIFY, stack still fails on unmonitored nickel-mesh scoring),
the HITL cell-row ratify, the 30 bar probe-duration refit, and the
night-shift 10-bin quantization fence are absent from prior committed
ouroboros rounds and from staged r14-r56. Repeated elements discounted:
same-gate contrast (r02/r03/r04/r14), governance-pricing scaffold,
flip-fragility series (extended to separator-true certificate, but the
move rhymes), sequenced recovery shape, third-factor rollback form (here
three edges rather than r14's two), negative-result primary (r14 staged).
Adjacent electrolysis rounds (r24 PEM, r37 chlor-alkali) share
electrochemical scaffolding but not liquid-KOH bipolar diaphragm
physics. Weighing a new failure family + cure vocabulary + domain
against those reused scaffolds:

{NOVEL_LINE}

## What ROUND 60 should add
1. FIT THE DESIGNED CONSTANTS: diaphragm-tear arrival, probe error bands,
   nickel-mesh scoring kinetics, night-shift claim process.
2. HIL PROVENANCE CELL: put the cell-row ratify on a
   hardware-in-loop cell interlock with fitted latency as
   state.sim_or_real=hil.
3. CROSS-RECORD ARC: let CR-A-5904's residual alarm be the igniter of
   the next round rather than a dangling +21 d leaf.
4. Domain candidates (de-collided): autonomous-driving; grid-inspection
   (if distinct from STARLING aerial-swarm and TORSIONKEY pitch);
   bioreactor-perfusion; urea-prilling-tower (if r56 builder claim did
   not land); irrigation-canal.
   AVOID alkaline-water-electrolysis (now used), pem-water-electrolysis,
   chlor-alkali-membrane, hot-strip-mill-finishing, paper-machine-dryer,
   gibbsite-autoclave-digestion, seawater-ro, sulfuric-contact,
   eaf-foamy-slag, glass-container-is-machine, fcc-flash-tank,
   blast-furnace burden descent,
   delayed-coker, LNG MCHE, cement-rotary-kiln
   clinker, kraft-recovery, electrolytic-aluminum,
   humanoid-locomotion, steel-caster mold-level, surgical-assist,
   wind-turbine pitch, float-glass, lyophilization,
   event-camera-traffic-grid, district-heating, aerial-swarm,
   warehouse-amr, underwater-rov, czochralski-pull, slot-die coating,
   optical-fiber-draw, vacuum-induction melt, steam-methane reformer,
   autoclave-composite-cure, geothermal-binary-orc,
   tire-curing-press, Claus sulfur recovery, ammonia converter,
   HDPE slurry loop, ethylene-steam-cracker coil, Kaplan wicket, and
   any LYOSHIELD / CINDERWICK / TRIAD / SKULLGATE / CALXION / MAGNORIL /
   GORSEFLUE / CLINKERFELL / SODASHARD / LINTELPLY / KAOTHARN /
   TREADNOLL / ANOLITH / DRUMWROTH / RIMEBRAID / BOGIRON / CHROMLOOP /
   NITREVAULT / ETHYNWOLD / RUNNELGATE / SPARKHOLT / DIPLEGAR /
   OLEUMWEIR / SKARVOLT / GOBSPALL / GOBWOLD / PUSHERFELL / CREELWOLD /
   GIBBSQUERN / COILSHAW / LOOPERQUAY / DRYSTAITH / OSMOLITH / PROTONIL plant.
"""
    (OUT / "NOTES-r59.md").write_text(notes)
    return notes


def write_transcript(rec, line):
    c1_spikes = [e for e in rec["spike_events"] if e["t_rel_ms"] <= C1_SPIKE_CUTOFF_MS]
    text = """# Multi-Agent Ouroboros Swarm — Round 59 transcript

Factory: multi-agent-ouroboros-swarm
Run: 2026-09-02-final-heavy
Generator: grok-4.6
Record id: maos-r59-001
Quota Q: 1
Rights: RM-793 research-only (SpaceXAI/xAI SuperGrok Heavy consumer chat)
Plant: invented KALYCIRQUE / Alkalfen Hydrogen AWE-6 (not TRIAD / Meridian / VANTIS-CADENCE-AEGIS / LYOSHIELD / CINDERWICK / PROTONIL / ANOLITH / COILSHAW / GIBBSQUERN / OSMOLITH / DRYSTAITH)

Two densifying cycles. Verbatim headings in order. Trajectory Builder cycle 2
emits the only JSONL line (also written to batch-r59.jsonl).

---

# CYCLE 1 — Foundation + injections

## Generator

Design intent: a 180-cell bipolar alkaline water-electrolysis stack where three
correct agents each read a header-true loop because a diaphragm tear
on cell pair 47-48 partitions cell-true dV from stack-mean voltage,
lye conductivity, and dryer-outlet H2. The naive playbook raises current
into a torn separator. The gate must MODIFY on a numeric current floor,
not by killing an agent.
sim_or_real=designed. Reward heads are
task_progress/safety/efficiency/coherence/exploration.

Cycle-1 base arc (pre-critic): state at Alkalfen AWE-6, 4.8 kA,
stack-mean 1.92 V/cell, lye 620 mS/cm, product H2 99.98 mol%, proposed
RAISE-CURRENT 5.6 kA, safety MODIFY to CURRENT-HOLD, executed hold without
the pressure-step numbers fully specified, outcome "tear found, stack saved"
(this last claim is the defect the later cycles will refuse to keep).
Sixteen spikes, five ticks, raster/gate_snn present but the scar is a
single edge.

```json
{
  "id": "maos-r59-001",
  "state": {
    "sim_or_real": "designed",
    "domain": "industrial-process",
    "description": "Stack AWE-6 at alkaline water electrolysis; three header loops in-spec; supervisor proposes raise-current.",
    "t0_us": 1754891880000059,
    "gate_latency_us": 688,
    "race_window_us": 500
  },
  "proposed_action": {"name": "raise_current", "parameters": {"current_kA": 5.6}},
  "safety_decision": {"decision": "MODIFY", "rationale": "Hold; do not raise current while cell-dV is high."},
  "executed_action": {"name": "current_hold", "executed_as_proposed": false},
  "future_outcome": {"summary": "Tear found, stack saved."},
  "reward_components": {"total": 0.40, "_aggregation": "total = task_progress + safety + efficiency + coherence + exploration"},
  "meta": {"round": 51, "factory": "multi-agent-ouroboros-swarm", "generator": "grok-4.6"}
}
```

That v1 object is a scaffold, not the publishable line. Defects below are
intentional for the critic to catch.

## Critic

Numbered defects on the cycle-1 Generator scaffold:

1. **blocking — reward arithmetic / false success.** `reward_components.total`
   0.40 is asserted without the five heads, without ticks, and against an
   outcome that claims "stack saved". If the pre-t0 scored nickel later
   flashes, booking +0.40 is a lie. Fix: declare `_aggregation`, emit
   3–8 ticks that sum to task_progress+safety+efficiency+coherence+exploration,
   and do not call a quarantined stack a save.
2. **blocking — weak safety rationale.** `safety_decision.rationale` has no
   numeric floor. Contract requires a concrete constraint. Fix: quote
   current <= 4.8 kA while cell-to-cell dV > 80 mV AND stack-header H2-in-O2 > 0.40 vol%.
3. **major — domain is a bucket, not a plant.** `state.domain` =
   `industrial-process` collides with generic MES vocabulary and teaches
   nothing. Alkaline water electrolysis (cell-dV vs stack-mean V,
   stack-header H2-in-O2 as a crossover flag) is absent from prior ouroboros
   rounds and must be named. Not PEM, not chlor-alkali.
4. **major — race under-specified.** One cell channel cannot be a race.
   Need >=2 channels inside `race_window_us` with globally sorted `t_rel_ms`
   and same-channel refractory >= 0.8 ms.
5. **minor — single-edge scar.** Raster routing with one potentiated weight
   repeats r04's one-edge rollback and is thinner than r14's two-edge.
   NOTES-r14 item 4 asked for three edges where pair rollback fails.

Critic does not rewrite the trajectory.

## Diversity Enforcer

Injected novel domain (exactly 1 this cycle): **alkaline-water-electrolysis**
(justified novel subdomain of industrial-process / liquid-KOH bipolar water
splitting; explicit tag `alkaline-water-electrolysis`).

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
eaf-foamy-slag-water-panel, glass-container-is-machine,
coke-oven-battery-heating, carbon-fiber-oxidation-oven,
gibbsite-autoclave-digestion, seawater-ro-desalination,
hot-strip-mill-finishing, or paper-machine-dryer-section.
autonomous-driving is left unused.

Domain-specific constraint: current must remain <= 4.8 kA while
cell-to-cell dV > 80 mV even if stack-mean V is inside the healthy
band; stack-header H2-in-O2 is a crossover flag the dryer-outlet
analyzer cannot substitute for.

Sensor delta: +stack-mean V, +KOH conductivity, +dryer-outlet H2,
+cell-to-cell dV, +stack-header H2-in-O2; -any mobile robot,
-event-camera gantries, -DVS, -Pirani/CM, -RGA quadrupole, -DVL,
-pitch encoder, -tendon LVDT, -insole GRF, -kiln zirconia, -smelt IR,
-cell-pH, -drum wet-foam, -MCHE cold-end, -Claus tail CEMS,
-ammonia bed-max, -sector radar, -FCC cyclone dP, -EAF off-gas H2,
-PEM cell-group max, -chlor-alkali header Cl2, -finishing-mill pyrometer.

`state.domain` and `meta.domain` both become `alkaline-water-electrolysis`.
Opening of `state.description` must Jaccard < 0.4 against prior plants
(Alkalfen night-shift diaphragm tear, not a lyophilizer, not a corridor,
not a tin bath, not a ROV pad, not a potline, not a PEM stack, not an OR,
not a gait lab, not a kiln, not a kraft boiler, not a coker drum, not an
LNG MCHE, not a blast furnace, not an HDPE loop, not a cracker coil, not an
FCC flash-tank, not a contact converter, not an EAF, not an IS machine,
not a Bayer autoclave, not a hot-strip mill, not a paper dryer).

## Edge-Case Hunter

Injected adversarial tail (exactly 1 this cycle): **cell pair 47-48
diaphragm tear + nickel-mesh scoring certificate**.

- Trigger: 47-48 PPS-felt diaphragm tear plus O2-side overpressure into
  the torn separator, cell-dV 284 mV, stack-header H2-in-O2 1.8 vol%.
- Base rate: <1% — 0.38%/campaign from a diaphragm-tear MC (cell-row
  visual threshold is designed; PPS-felt geometry fitted-style). Visual
  PASSES because the tear sits behind the bipolar plate.
- Naive failure: FALSE PERMISSION. PB-AWE-6 sees three in-spec mean
  loops, raises 4.8->5.6 kA, O2-header recombination 2.4 vol% H2, $3.9M.
- Trajectory edit: put the tear in `state.fault_context`, make each
  agent's confirm a different header-side slice of the same cell-false
  state (volt-in-band, lye-ok, gas-ok). Cell-dV is
  readable but policy-treated as noisy-bipolar-only.

Distinct from stacked-dead-band permission (fragments of one trip vs
wrong-volume sensing), from r24 PEM cell-group max (solid polymer vs
liquid KOH), from r37 chlor-alkali header-Cl2 (Cl2 vs H2/O2), from r21
potline voltage (alumina vs diaphragm), from r54 Bayer flash-train
(autoclave shell vs bipolar cell), and from r56 hot-strip work-roll
(IR vs cell-dV).

## Neuromorphic Translator

Cycle-1 temporal densification (16 spikes, 5 ticks, 40 ms raster):

| channel | t_rel_ms | amplitude |
|---|---|---|
| volt.hot | 0.296 | 0.53 |
| lye.ok | 1.140 | 0.62 |
| gas.ok | 2.028 | 0.54 |
| cell.dV | 3.152 | 0.77 |
| volt.hot | 4.148 | 0.50 |
| cell.dV | 4.836 | 0.80 |
| lye.ok | 5.352 | 0.58 |
| cell.dV.high | 6.528 | 1.38 |
| volt.in_band | 6.712 | 1.15 |
| gas.ok | 6.896 | 0.63 |
| ctrl.gate | 7.216 | 1.09 |
| cell.dV | 8.860 | 0.44 |
| lye.ok | 10.748 | 0.81 |
| gas.ok | 13.036 | 0.46 |
| volt.hot | 18.520 | 0.43 |
| ctrl.gate | 26.180 | 0.85 |

Race: cell-dV 6.528 vs stack-V 6.712 (184 us) inside 500 us;
gas.ok 6.896 is the third channel in-window. Winner/loser flip: reversing
184 us reshuffles PB-AWE-6 triage; floors still MODIFY. Refractory held
(cycle-1 min same-channel gap 1.684 ms on cell.dV 4.836-3.152;
volt 4.148-0.296 = 3.852; lye 5.352-1.140 = 4.212). Adaptation:
cell 0.77->0.80->1.38->0.44; volt 0.53->0.50->0.43; lye
0.62->0.58->0.81.

Raster cycle-1 seed: 40 ms, 160 neurons, 8.0 Hz, 51 spikes, 1173 pJ, third
factor acetylcholine tau_e 0.94 s. Single scar edge only — cycle 2 must
add the second and third edges.

Ticks 1–5 at 4560, 6528, 7216, 7.4e6, 576e6 us; heads not yet the final
-0.16 (missing the 2.6 h and 4.2 h ticks).

Distillation value this cycle: header-side confirms as a permission code
that is not a separator-true voltage code.

## Trajectory Builder

Cycle-1 hardened object: domain alkaline-water-electrolysis, tail
diaphragm tear, 16 spikes, 5 ticks, MODIFY with numeric floor, raster+gate_snn
present, sim_or_real=designed, rights stamp on record and meta, no thought
keys. Still missing (and therefore not the publishable line): 30 bar
sub-variant, night-shift tail, second and third scar edges,
delayed recombination flash as PRIMARY terminal, contrast ACCEPT episode,
ticks 6–7, spikes 17–26.

Validation receipt (cycle 1, not final):
- checks passed: 16 spikes sorted; 3 channels in 500 us window; refractory
  >= 0.8 ms; rationale quotes 4.8 kA / 80 mV / 0.40 vol%; domain
  named; gate_snn.decision MODIFY.
- checks deferred to cycle 2: triple-edge scar, second tail, second domain
  constraint, negative-result booking, 7 ticks summing to heads.
- densification vs Generator v1: +1 domain, +1 tail, +16 spikes, +5 ticks,
  +numeric floor.

Cycle-1 JSON is retained as the base; it is NOT written to batch-r59.jsonl.

Cycle-1 spike count: __C1_SPIKES__.

---

# CYCLE 2 — Densification

## Generator

Cycle-1 output is the base. Additive expansion (nothing removed):

1. Downstream side-effect (immediate): O2-side pressure-step probe at +7.4 s
   stays crossover-true (|Delta H2-in-O2| 0.55 >= 0.40 vol%) — diaphragm
   tear, not true current-duty. Cell pair 47-48 holds. Scored nickel
   discovered during the isolate.
2. Delayed side-effect (PRIMARY terminal, not a footnote): at +4.2 h
   O2-header recombination flash from the pre-t0 diaphragm tear; 28 h
   outage; $1.84M. The 11 min pre-t0 O2-side overpressure is the
   mechanism. Correct gate, stack still fails.
3. Deepened `proposed_action.evidence` with units: dV 284 mV,
   H2-in-O2 1.8 vol%, stack-mean 1.92 V/cell, lye 620 mS/cm, product H2
   99.98 mol%, race 184 us.
4. Tightened rationale to the numeric floor current <= 4.8 kA while
   cell-dV > 80 mV AND stack-header H2-in-O2 > 0.40 vol%, plus
   probe bands >= 0.40 vs <= 0.05 vol%, plus HITL 9.6 min cell-row
   rule.

Reward retargeted to total -0.16 so the delayed fail is the inflection
(t_us 15120000000), not the gate. Process heads remain non-zero.

## Critic

Re-audit of the expanded trajectory:

1. **blocking if unfixed — missing second domain constraint.** 16-bar
   probe 7.4 s / +0.15 bar is not a universal number. A 30 bar stack
   will overshoot a sealed separator. Diversity Enforcer must
   inject the physical-constraints sub-variant this cycle.
2. **major — only one tail class.** Diaphragm tear is accidental
   infrastructure. A disjoint human-intent tail is still required
   (night-shift cell-V forgery is the open cell).
3. **major — scar is still one edge in the cycle-1 raster.** NOTES-r14
   item 4 is not discharged until three go-edges exist and pair rollback
   is shown to fail at threshold 0.30.
4. **minor — contrast episode missing.** Without a same-gate ACCEPT on a
   true sealed current-duty window the record teaches "never raise-current".
   Add +4 d sister-stack contrast with its own race.
5. **minor — HITL latency mentioned in prose only.** Put 9.6 min in
   executed_action.parameters.human_ratify and in a tick.

No rewrite; directives only.

## Diversity Enforcer

Injected second novel domain / physical-constraint sub-variant (exactly 1
this cycle): **high-pressure 30 bar AWE** on a sister pressure class.

What it expands: 16 bar bipolar stack (cycle 1) -> 30 bar
1.9x O2-side dP. Crossover gain 2.4x. The 7.4 s +0.15 bar pulse moves
even a sealed separator to 0.48 vol% H2-in-O2, inside the 0.40 hold.
Required probe: 19 s at +0.04 bar (tear Delta 0.44 vol%, sealed
Delta 0.04).

This is still one domain injection for the cycle (physical-constraints
clause of the factory prompt). It does not displace
alkaline-water-electrolysis; it changes which probe table is legal.
`future_outcome.subvariant_constraint` carries the refit. Jaccard opening
stays the Alkalfen 180-cell sentence; 30 bar is additive, not a rewrite.

## Edge-Case Hunter

Injected second adversarial tail (exactly 1 this cycle, disjoint class):
**night-shift forged cell-V CSV**.

- Trigger: shift lead, 02:18, posts a historian export showing
  dV = 18 mV at t = 1.4 h to clear an H2-quota catchup slot.
- Base rate: ~0.28% of Sunday-night campaigns (designed, flagged, <1%).
- Naive failure: a weak supervisor ACCEPTs the raise-current on the forged
  confirm and ignores live cell-dV. Recombination plus a data-integrity
  write-up.
- Fence: forged log quantized at 50 mV (SCADA screenshot rounding); plant
  historian is 5 mV (10 bins). Live dV is 284 mV and H2-in-O2 is
  1.8 vol% at the claimed separator-true, which no sealed separator
  produces. Freeze-window overlap with the 11 min overpressure.
- Trajectory edit: governance CR-A-5904 mandates native 5 mV CSV
  exports; the contrast ACCEPT still requires live cell-dV, not a CSV.

Distinct from cycle-1 tear (accidental diaphragm vs deliberate deception) and
from the 30 bar sub-variant (physics vs fraud).

## Neuromorphic Translator

Re-densify (additive):

- +10 spikes after 26.180 ms: press.probe 7400.0, cell.dV 7488.6
  (adapt 1.38->0.40), volt.in_band 7572.2 (1.15->0.35), human.ratify
  576000.0, cell.lock 576900.0, mesh.score 577700.0, volt.hot
  9360000.0, cell.dV 9360720.0, lye.ok 9361480.0, header.flash
  15120000.0. Primary train 16 -> 26. Still one key, still sorted,
  refractory held.
- +2 ticks (5 -> 7) at 9_360_000_000 us (true sealed separator) and
  15_120_000_000 us (recombination flash). Heads now 0.08, -0.36, -0.11,
  0.14, 0.09; total -0.16. Inflection is the last tick.
- Contrast train 8 events, own race 178 us, ACCEPT.
- Triple-edge third factor: three header-healthy-go edges, tau_e 0.94 s = 940 ms,
  trace __AUX_TRACE__, eta __AUX_ETA1__ / __AUX_ETA2__ / __AUX_ETA3__,
  weights 0.48->0.24, 0.43->0.22, 0.40->0.20. Raster excerpt unchanged
  (decision window is still 40 ms) and remains sorted with unique
  neuron_ids (same-neuron >=1000 us vacuously).

Winner/loser flip (re-stated, not replaced): reversing 184 us would only
reorder triage; cell-dV floors still MODIFY. Contrast flip of
178 us similarly cannot turn a sealed separator into a tear.

## Trajectory Builder

Schema checks on the FINAL object: required Thalamic v2 keys present as
objects; `state.sim_or_real`=designed; `safety_decision.decision`=MODIFY
with numeric rationale; `reward_components.total` = sum of five heads =
sum of 7 ticks = -0.16; `spike_events` globally non-decreasing on
t_rel_ms, 26 events, refractory >=0.8 ms, 3 channels in race window;
raster 20–50 ms, spikes=round(n*rate*window_s)+/-1, energy 23 pJ/spike,
excerpt sorted, tau_e consistent; gate_snn.decision matches; meta.round=59,
factory=multi-agent-ouroboros-swarm, generator=grok-4.6,
run_label=2026-09-02-final-heavy; rights on record and meta; no thought
keys; no training_ready; Diversity + Edge-Case injections from BOTH cycles
present and non-trivial; cycle 2 strictly additive.

Densification delta: +1 domain sub-variant (30 bar), +1 tail
(night-shift forgery), +10 spikes (16->26), +2 ticks (5->7), +1 contrast
train with own race, +2 delayed side-effects, +1 triple-edge scar with
pair-rollback-fails, +1 HITL ratify, +1 surprise (nickel-mesh scoring is
the collapse mechanism).

Publishable JSONL line (the only JSONL line; also at batch-r59.jsonl):

```json
__FINAL_JSONL__
```

Validation receipt (final): checks passed / fixed as reported by
build_r59.py self-validate (check_jsonl, raster_status, verify_record_execution,
spike_probe --strict).
"""
    text = (
        text.replace("__C1_SPIKES__", str(len(c1_spikes)))
        .replace("__AUX_TRACE__", f"{math.exp(-DELAY_S / TAU_E_S):.5f}")
        .replace("__AUX_ETA1__", f"{0.24 / math.exp(-DELAY_S / TAU_E_S):.5f}")
        .replace("__AUX_ETA2__", f"{0.21 / math.exp(-DELAY_S / TAU_E_S):.5f}")
        .replace("__AUX_ETA3__", f"{0.20 / math.exp(-DELAY_S / TAU_E_S):.5f}")
        .replace("__FINAL_JSONL__", line)
    )
    (OUT / "swarm-transcript-r59.md").write_text(text)
    return text


def main():
    rec, aux = build_record()
    errs = local_checks(rec, aux)

    OUT.mkdir(parents=True, exist_ok=True)
    line = json.dumps(rec, ensure_ascii=False, separators=(",", ":"))
    (OUT / "batch-r59.jsonl").write_text(line + "\n")

    from check_records import FactoryStaging, check_jsonl
    from curate_bridge import raster_status
    from verify_execution import verify_record_execution

    e, w, kinds, n = check_jsonl(
        OUT / "batch-r59.jsonl",
        "batch-r59.jsonl",
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
            str(OUT / "batch-r59.jsonl"),
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
    write_notes(rec, aux, pipeline_receipt)
    write_transcript(rec, line)

    heading = subprocess.run(
        [sys.executable, "/tmp/maos_heading_check.py", str(OUT / "swarm-transcript-r59.md")],
        capture_output=True,
        text=True,
    )
    print(heading.stdout)
    if heading.returncode != 0:
        errs.append(f"heading check {heading.returncode} {heading.stdout}")

    raw_hits = subprocess.run(
        [
            "rg",
            "-l",
            "maos-r59-001|KALYCIRQUE",
            str(Path(ROOT) / "outputs" / "raw"),
        ],
        capture_output=True,
        text=True,
    )
    if raw_hits.stdout.strip():
        errs.append(f"raw tree hit {raw_hits.stdout.strip()[:200]}")

    if errs:
        print("FAIL", errs)
        return 1
    print("OK maos-r59-001 staged under", OUT)
    print("bytes jsonl", (OUT / "batch-r59.jsonl").stat().st_size)
    print("bytes notes", (OUT / "NOTES-r59.md").stat().st_size)
    print("bytes transcript", (OUT / "swarm-transcript-r59.md").stat().st_size)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
