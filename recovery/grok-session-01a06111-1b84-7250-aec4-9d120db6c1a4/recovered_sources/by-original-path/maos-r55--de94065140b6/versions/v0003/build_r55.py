#!/usr/bin/env python3
"""Build and self-check MAOS round-55 JSONL (research-only; not published)."""
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

GEN_AT = "2026-09-03T08:55:00Z"
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
OUT = Path("/tmp/maos-r55")
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
    "Emberbarrow",
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
    "OSMOLITH",
    "Spumeholt",
    "GAUZEFELL",
    "Ammoxwick",
    "GIBBSQUERN",
    "Laterifen",
    "SIPHONWOLD",
    "Reedfen",
    "OSMOQUAY",
    "Tidecairn",
    "Baosteel",
    "Nippon Steel",
    "Voestalpine",
    "Gerdau",
    "Steel Dynamics",
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
    "Nafion",
    "Chemours",
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
    "Filmtec",
    "FilmTec",
    "Hydranautics",
    "Veolia",
    "DuPont",
    "Dupont",
    "LG Chem",
    "NanoH2O",
    "Toray",
    "Doosan",
    "Acciona",
    "Aquatech",
    "Grundfos",
    "Danfoss",
    "Evoqua",
    "Pentair",
    "Xylem",
    "Hexcel",
    "Teijin",
    "Emhart",
    "Bucher Emhart",
    "Bottero",
    "Owens-Illinois",
    "Owens Illinois",
    "Verallia",
    "Ardagh Glass",
    "Vidrala",
    "Saint-Gobain",
    "Vetropack",
    "O-I Glass",
    "IDE Technologies",
    "Osmoflo",
    "Suez",
)
R14_OPENING = (
    "Helixmere Biologics Building C lyophilizer LYO-4 is mid-primary on 8400 "
    "vials of a monoclonal antibody"
)
NOVEL_LINE = "Novel coverage: 48%"
PLANT = "OSMOQUAY"
GEO = "Tidecairn"
CELL = "RO-7"
DOMAIN = "swro-high-pressure-train"
RECORD_ID = "maos-r55-001"
ROUND = 55
DELAY_S = 0.84
TAU_E_S = 0.92
C1_SPIKE_CUTOFF_MS = 26.160


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
        if p.parent.name == "maos-r55":
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
        if p.parent.name == "maos-r55":
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
        if p.parent.name == "maos-r55":
            continue
        try:
            text = p.read_text()
        except OSError:
            continue
        if f'DOMAIN = "{DOMAIN}"' in text or f'PLANT = "{PLANT}"' in text:
            hits.append(f"{p}: claimed {PLANT}/{DOMAIN}")
        if f'GEO = "{GEO}"' in text:
            hits.append(f"{p}: claimed geo {GEO}")
    return hits


def build_record():
    ticks, heads = cents_ticks(
        [4560, 6520, 7214, 6_200_000, 426_000_000, 3_240_000_000, 11_160_000_000],
        [
            (1, -2, -1, 2, 1),
            (2, -5, -1, 2, 1),
            (2, -6, -2, 3, 2),
            (1, -6, -1, 2, 1),
            (1, -5, -2, 2, 1),
            (1, -6, -2, 2, 1),
            (0, -6, -1, 1, 1),
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
        {"channel": "feed.k", "t_rel_ms": 0.280, "amplitude": 0.52},
        {"channel": "hp.p", "t_rel_ms": 1.120, "amplitude": 0.61},
        {"channel": "perm.k", "t_rel_ms": 2.010, "amplitude": 0.53},
        {"channel": "vessel.dp", "t_rel_ms": 3.140, "amplitude": 0.78},
        {"channel": "feed.k", "t_rel_ms": 4.140, "amplitude": 0.50},
        {"channel": "vessel.dp", "t_rel_ms": 4.820, "amplitude": 0.81},
        {"channel": "hp.p", "t_rel_ms": 5.340, "amplitude": 0.58},
        {"channel": "vessel.dp.high", "t_rel_ms": 6.520, "amplitude": 1.44},
        {"channel": "perm.in_band", "t_rel_ms": 6.696, "amplitude": 1.16},
        {"channel": "feed.k", "t_rel_ms": 6.940, "amplitude": 0.64},
        {"channel": "ctrl.gate", "t_rel_ms": 7.214, "amplitude": 1.11},
        {"channel": "vessel.dp", "t_rel_ms": 8.850, "amplitude": 0.46},
        {"channel": "feed.k", "t_rel_ms": 10.740, "amplitude": 0.82},
        {"channel": "hp.p", "t_rel_ms": 13.020, "amplitude": 0.45},
        {"channel": "perm.k", "t_rel_ms": 18.510, "amplitude": 0.42},
        {"channel": "ctrl.gate", "t_rel_ms": 26.160, "amplitude": 0.84},
        {"channel": "rec.probe", "t_rel_ms": 6200.0, "amplitude": 0.94},
        {"channel": "vessel.dp", "t_rel_ms": 6288.2, "amplitude": 0.40},
        {"channel": "perm.in_band", "t_rel_ms": 6372.4, "amplitude": 0.34},
        {"channel": "human.ratify", "t_rel_ms": 426000.0, "amplitude": 0.78},
        {"channel": "vessel.lock", "t_rel_ms": 426900.0, "amplitude": 0.70},
        {"channel": "elem.score", "t_rel_ms": 427700.0, "amplitude": 0.86},
        {"channel": "feed.k", "t_rel_ms": 3240000.0, "amplitude": 0.30},
        {"channel": "vessel.dp", "t_rel_ms": 3240720.0, "amplitude": 0.28},
        {"channel": "hp.p", "t_rel_ms": 3241480.0, "amplitude": 0.26},
        {"channel": "elem.collapse", "t_rel_ms": 11160000.0, "amplitude": 0.92},
    ]

    contrast_spikes = [
        {"channel": "raise.demand", "t_rel_ms": 0.000, "amplitude": 0.84},
        {"channel": "vessel.clear", "t_rel_ms": 0.176, "amplitude": 0.76},
        {"channel": "feed.k", "t_rel_ms": 0.400, "amplitude": 0.27},
        {"channel": "hp.p", "t_rel_ms": 1.450, "amplitude": 0.41},
        {"channel": "perm.k", "t_rel_ms": 4.870, "amplitude": 0.50},
        {"channel": "ctrl.gate", "t_rel_ms": 7.010, "amplitude": 0.91},
        {"channel": "rec.probe", "t_rel_ms": 3100.0, "amplitude": 0.33},
        {"channel": "elem.collapse", "t_rel_ms": 11160000.0, "amplitude": 0.10},
    ]

    excerpt = [
        {"t_us": 280, "neuron_id": 11},
        {"t_us": 1120, "neuron_id": 73},
        {"t_us": 2010, "neuron_id": 24},
        {"t_us": 3140, "neuron_id": 49},
        {"t_us": 4140, "neuron_id": 14},
        {"t_us": 4820, "neuron_id": 55},
        {"t_us": 5340, "neuron_id": 90},
        {"t_us": 6520, "neuron_id": 38},
        {"t_us": 6696, "neuron_id": 18},
        {"t_us": 6940, "neuron_id": 103},
        {"t_us": 7214, "neuron_id": 132},
        {"t_us": 8850, "neuron_id": 62},
        {"t_us": 10740, "neuron_id": 28},
        {"t_us": 13020, "neuron_id": 117},
        {"t_us": 18510, "neuron_id": 15},
        {"t_us": 26160, "neuron_id": 145},
    ]

    rec = {
        "id": RECORD_ID,
        "title": "OSMOQUAY RO-7: last-element dP residual 1.80 bar beats perm.in_band by 176 us; correct MODIFY still loses element 7 to a pre-t0 interconnector O-ring",
        "rights": dict(RIGHTS),
        "state": {
            "sim_or_real": "designed",
            "domain": DOMAIN,
            "scenario_name": "OSMOQUAY / Tidecairn Desal RO-7",
            "timestamp_local": "2026-08-24T03:42:00-05:00",
            "t0_us": 1786396800000055,
            "gate_latency_us": 694,
            "race_window_us": 500,
            "race_window_rel_ms": [6.520, 7.020],
            "description": "Tidecairn Desal first-pass skid RO-7 holds 45% recovery on a seven-vessel SWRO train when three heterogeneous, individually-correct agents jointly report 'header healthy, raise recovery'. FEED's 12-bit conductivity is 52.4 mS/cm inside 48-58. HP's pump discharge is 68.4 bar inside 64-72. PERM's mixed-header permeate is 412 uS/cm inside 0-600. The conjunction is not a vessel-true recovery certificate: a 14 min cracked interconnector O-ring on vessel V-7 element 6/8 dumps concentrate into that vessel's permeate tube, so last-element dP residual r_dP is 1.80 bar (hold if > 0.70) and vessel-to-header conductivity residual r_k is 1362 uS (hold if > 180) while the playbook still sees a legal header. Missing vessel-true salt passage is policy-treated as a noisy-dP tag unless mixed-header conductivity also trips (2016 'noisy last-element dP'). Vessel-first latches RECOVERY-HOLD plus a flux-cut probe; header-first would have authorized RAISE-RECOVERY into a leaking vessel.",
            "goal": "Hold recovery and HP setpoint without a flux raise while r_dP > 0.70 bar AND vessel-to-header conductivity residual r_k > 180 uS AND V-7 remains unisolated; keep mixed-header permeate inside the 600 uS trip.",
            "race": {
                "contenders": [
                    "vessel.dp.high 1.80 bar (V-7 last-element vs train-mean dP)",
                    "perm.in_band 412 uS/cm (mixed-header permeate)",
                ],
                "semantics": "vessel-first latches RECOVERY-HOLD + FLUX-CUT-PROBE + vessel isolate. Header-first latches RAISE-RECOVERY (+8% recovery, no probe).",
                "window_derivation": "500 us = one 360 us last-element dP slot plus 140 us header-conductivity publish.",
                "order_evidence_note": "Margin 176 us vs combined jitter 54 us (vessel dP 30 + header 24): 3.3x. The 176 us gap sits inside min(500, 500) us, so a sub-flip-bound perturbation reverses triage order. The gate rides the order-invariant floors r_dP > 0.70 bar and r_k > 180 uS, not the alarm order.",
            },
            "topology": {
                "site": "Tidecairn Desal, invented tide-cairn campus Tidecairn, cell RO-7: 7-vessel first-pass SWRO, 8 elements/vessel, 45% recovery, 68.4 bar HP, Grade-B vessel LOTO",
                "agents": "FEED feed conductivity (vendor Feedholt): 20 Hz 12-bit on the 52.4 mS/cm intake. HP pump discharge (vendor Presswick): 50 Hz on the 68.4 bar header. PERM mixed-header permeate conductivity (vendor Permfen): 20 ms bus on blended permeate that cleared all seven vessels. VESSEL last-element dP residual (vendor Deltaholt) is commissioned as a noisy-dP tag, not as a vessel-true recovery tag. Heterogeneous stacks, no shared intent schema, one 20 ms skid-bus epoch",
                "coupling": "All three playbook confirms live on the WRONG volume. FEED is correct that intake is 52.4 mS/cm. HP is correct that the pump is 68.4 bar. PERM is correct that the mixed header is 412 uS/cm (six healthy vessels dilute V-7's 1774 uS into the 0-600 band). Playbook PB-RO-7 treats the conjunction as permission to raise recovery. No agent is faulty; the header conductivity is looking at the blend, not at vessel-true salt passage after a cracked interconnector O-ring.",
            },
            "sensors": [
                "feed conductivity 12-bit, 20 Hz, 22 us jitter, 52.4 mS/cm (dead-band 48-58)",
                "HP pump discharge, 50 Hz, 24 us jitter, 68.4 bar (band 64-72)",
                "mixed-header permeate conductivity, 50 Hz, 21 us jitter, 412 uS/cm (band 0-600)",
                "V-7 last-element dP residual r_dP, 20 Hz, 30 us jitter, 1.80 bar (healthy < 0.25 bar; policy floor 0.70 bar is not armed unless header conductivity also trips)",
                "per-vessel permeate conductivity on V-7 is NOT commissioned at t0 (installed after this incident)",
            ],
            "constraints": {
                "feed_ms_cm": 52.4,
                "feed_deadband_ms_cm": [48.0, 58.0],
                "hp_bar": 68.4,
                "hp_band_bar": [64.0, 72.0],
                "perm_us_cm": 412.0,
                "perm_band_us_cm": [0.0, 600.0],
                "v7_perm_us_cm": 1774.0,
                "healthy_vessel_perm_us_cm": 185.0,
                "r_dP_bar": 1.80,
                "r_dP_hold_bar": 0.70,
                "r_k_us": 1362.0,
                "r_k_hold_us": 180.0,
                "recovery_pct": 45.0,
                "proposed_raise_pct": 8.0,
                "perm_trip_us_cm": 600.0,
                "fault_cell": "V-7",
            },
            "fault_context": {
                "failure_class": "MIXED-HEADER PERMEATE CERTIFICATE OF A VESSEL-TRUE RECOVERY: three individually-correct heterogeneous agents each read a locally-true loop; a 14 min cracked interconnector O-ring partitions vessel-true salt passage from header-true blended permeate, so the playbook's FEED/HP/PERM conjunction is not a recovery-duty certificate",
                "igniter": "V-7 interconnector O-ring cracked after 14 min of unmonitored post-CIP; skid-floor visual PASSES (no puddle; the leak is concentrate-into-permeate inside the vessel)",
                "naive_failure": "PB-RO-7 RAISE-RECOVERY on three healthy loops: +8% recovery into a leaking vessel, gypsum/silica scale plus salt-passage trip, $1.68M plus a 14-hour skid outage",
            },
            "poisoned_context": {
                "naive_alarm": "Playbook PB-RO-7 (after the 2016 'noisy last-element dP') auto-drafts RAISE-RECOVERY whenever feed conductivity is inside 48-58 mS/cm AND HP inside 64-72 bar AND mixed-header permeate inside 0-600 uS/cm, ignoring the vessel dP tap unless header conductivity also trips",
                "why_poisoned": "The three confirms are locally true and jointly insufficient. The vessel dP tap is a commissioned inference that policy treats as noisy-dP-only. Independence of 'header in-band, therefore every vessel is recovery-true' is the hidden assumption, and it is false across a cracked-interconnector path.",
            },
            "constraint": "Do not raise recovery or HP setpoint while last-element dP residual r_dP > 0.70 bar AND vessel-to-header conductivity residual r_k > 180 uS. Discriminate leaking vessel vs true recovery-duty with a reversible flux-cut probe before any recovery raise.",
        },
        "proposed_action": {
            "actor": "desal supervisory optimizer DSO (auto-playbook PB-RO-7 draft), submitted to gate TG-RO-7",
            "name": "raise_recovery",
            "action": "RAISE-RECOVERY: recovery 45 to 48.6 percent, no flux-cut probe, no vessel isolate",
            "summary": "Treat three in-spec loops as a healthy header and raise night-shift recovery to clear a permeate-quota catchup window.",
            "parameters": {
                "raise_pct": 8.0,
                "flux_cut_probe": False,
                "vessel_lock": False,
                "human_ratify": False,
            },
            "steps": [
                "assert feed conductivity 52.4 mS/cm inside 48-58",
                "assert HP discharge 68.4 bar inside 64-72",
                "assert mixed-header permeate 412 uS/cm inside 0-600",
                "raise recovery +8% from 45 to 48.6 percent",
                "do not read last-element dP residual as a vessel-true tag",
            ],
            "evidence": [
                {
                    "observable": "last-element dP residual r_dP",
                    "value": 1.80,
                    "unit": "bar",
                    "source": "VESSEL V-7 last-element vs train-mean dP",
                    "note": "healthy < 0.25 bar; policy floor 0.70 bar is not armed unless header conductivity also trips",
                },
                {
                    "observable": "mixed-header permeate conductivity",
                    "value": 412.0,
                    "unit": "uS/cm",
                    "source": "PERM mixed-header cell",
                    "note": "dead-band 0-600; lives on the six-vessel blend, not V-7's 1774 uS",
                },
                {
                    "observable": "feed conductivity",
                    "value": 52.4,
                    "unit": "mS/cm",
                    "source": "FEED 12-bit intake cell",
                    "note": "speed band 48-58; feed-true, vessel-false",
                },
                {
                    "observable": "HP pump discharge",
                    "value": 68.4,
                    "unit": "bar",
                    "source": "HP header transmitter",
                    "note": "band 64-72; pump-true, vessel-false",
                },
                {
                    "observable": "vessel-to-header conductivity residual r_k",
                    "value": 1362.0,
                    "unit": "uS",
                    "source": "process duty vs mixed-header integrator",
                    "note": "hold floor 180 uS; leaking vessel did not reject salt on V-7",
                },
                {
                    "observable": "race margin",
                    "value": 176,
                    "unit": "us",
                    "source": "vessel.dp.high 6.520 ms vs perm.in_band 6.696 ms",
                    "note": "combined jitter 54 us, 3.3x; inside 500 us flip bound",
                },
            ],
            "basis": "PB-RO-7 fires on three locally-true confirms. The draft does not read r_dP 1.80 bar as a vessel residual and does not treat r_k 1362 uS as a leak discriminant.",
            "expected_cost_bound": "If the draft executes: gypsum/silica scale plus salt-passage trip at header 600 uS, $1.68M plus 14-hour skid outage. If MODIFIED: probe plus vessel-lock, with residual risk from element scoring already seeded in the 14 min pre-t0 O-ring crack.",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "correctness": "correct",
            "decided_by": "TG-RO-7 thalamic release gate",
            "decision_t_rel_ms": 7.214,
            "rationale": "MODIFY the draft: strip the recovery raise, hold 45% recovery and HP setpoint, run a 6.2 s flux-cut probe (-4% recovery), and keep V-7 locked unless the probe stays leak-false. Numeric floor: do not raise recovery or HP setpoint while last-element dP residual r_dP > 0.70 bar AND vessel-to-header conductivity residual r_k > 180 uS. Observed r_dP 1.80 bar and r_k 1362 uS both violate the release predicate, so a raise is forbidden even though all three playbook confirms are numerically true. The three confirms are not a recovery-duty certificate: they live on a mixed header past a cracked interconnector O-ring, and the playbook's conjunction of header-true loops is not a vessel-true certificate. Probe discriminant: after a 6.2 s -4% recovery bump, a leaking vessel moves mixed-header |d-kappa| >= 80 uS (94 uS observed); a healthy train moves <= 18 uS. Order-code discipline: vessel dP beat header-in-band by 176 us inside the 500 us flip bound, so triage order is flip-fragile; the hold rides the order-invariant floors, not the winner tag. Human ratification: vessel isolate is rack work with fitted 7.1 min dead-man; the gate may hold and probe autonomously but may not break the vessel LOTO without the operator confirm.",
            "constraint_checked": {
                "r_dP_bar": {"observed": 1.80, "hold_if_above": 0.70},
                "feed_ms_cm": {"observed": 52.4, "band": [48.0, 58.0]},
                "r_k_us": {"observed": 1362.0, "hold_if_above": 180.0},
                "perm_us_cm": {"observed": 412.0, "band": [0.0, 600.0]},
            },
        },
        "executed_action": {
            "name": "recovery_hold_flux_probe_vessel_close",
            "action": "RECOVERY-HOLD + FLUX-CUT-PROBE + VESSEL-ISOLATE (gate-mandated modification)",
            "executed_as_proposed": False,
            "parameters": {
                "raise_pct": 0.0,
                "flux_cut_probe": True,
                "vessel_lock": True,
                "human_ratify": True,
            },
            "gate_effect": "MODIFY: recovery raise stripped. 45% recovery and HP held. 6.2 s flux-cut probe -4%. Probe stays leak-true (|d-kappa| 94 >= 80) so the vessel LOTO stays closed after 7.1 min human ratify and V-7 is lined off. Recovery resumes only after a vessel-true verify.",
            "deviations": "PB-RO-7 raise stripped entirely. Recovery is bumped only for the 6.2 s probe then returned. Vessel-LOTO wait added (7.1 min fitted rack+ratify). Element survey added during the lock (not in the draft).",
            "execution_log": [
                {"t_rel_ms": 7.214, "entry": "TG-RO-7 MODIFY latched 694 us after vessel-dP win; raise stripped; hold+probe authorized"},
                {"t_rel_ms": 6200.0, "entry": "flux-cut probe: -4% for 6.2 s; mixed-header 412 -> 506 uS (leak band |d-kappa| >= 80); HP 68.4 -> 65.7 bar"},
                {"t_rel_ms": 426000.0, "entry": "operator ratifies keep-closed after 7.1 min vessel-rack walk (fitted walk+interlock)"},
                {"t_rel_ms": 426900.0, "entry": "vessel stays locked; remaining r_k 1362 -> 40 uS over 0.9 h as V-7 is isolated"},
                {"t_rel_ms": 427700.0, "entry": "element survey: score already on V-7 element 6/8 permeate tube; 14 min pre-t0 O-ring crack logged"},
                {"t_rel_ms": 3240000.0, "entry": "true recovery duty: r_dP 0.18 bar, r_k 40 uS, residual under 0.70 bar; raise now legal on RO-7B only"},
                {"t_rel_ms": 11160000.0, "entry": "element collapse from a pre-t0 O-ring score; skid island quarantined 11 h"},
            ],
        },
        "future_outcome": {
            "summary": "Correct MODIFY prevented the +8% recovery raise into a leaking vessel and the immediate salt-passage trip. The train still failed: 14 min of unmonitored pre-t0 O-ring crack had already scored element 7's permeate tube. Process-correct gate, bounded world loss, negative total.",
            "state_delta": {
                "recovery": "held through probe and vessel lineup; later legal raise only on the sister skid after 0.9 h duty recovery",
                "header": "V-7 isolated; r_k slaved to last-element dP residual; remaining header recovered toward 198 uS",
                "oring": "cracked interconnector O-ring logged and locked; mixed-header conductivity no longer trusted as vessel-true recovery",
                "island": "night-shift skid island quarantined; element scored; element collapse at +3.1 h; 11 h outage",
            },
            "timeline": [
                {"t_rel_ms": -840000.0, "event": "t0-14 min: V-7 interconnector O-ring cracks after CIP; concentrate prefers the permeate tube; mixed header stays legal"},
                {"t_rel_ms": -240000.0, "event": "t0-4 min: r_dP first crosses 0.70 bar; PB-RO-7 ignores it because header conductivity is 398 uS"},
                {"t_rel_ms": 0.0, "event": "t0: vessel-dP-vs-header-in-band race on the skid bus"},
                {"t_rel_ms": 6.520, "event": "vessel dP residual at 1.80 bar wins by 176 us"},
                {"t_rel_ms": 6.696, "event": "header-in-band flag (loser)"},
                {"t_rel_ms": 7.214, "event": "TG-RO-7 MODIFY"},
                {"t_rel_ms": 6200.0, "event": "flux-cut probe confirms leaking vessel (|d-kappa| 94 uS, leak band)"},
                {"t_rel_ms": 426000.0, "event": "human ratify 7.1 min; vessel stays locked; scored element logged"},
                {"t_rel_ms": 3240000.0, "event": "true recovery duty after 0.9 h; raise legal only with r_dP slave"},
                {"t_rel_ms": 11160000.0, "event": "element collapse from the pre-t0 O-ring score; island quarantined"},
                {"t_rel_ms": 259200000.0, "event": "+3 d contrast: sister skid RO-7B true recovery-duty; same gate ACCEPTs the raise"},
                {"t_rel_ms": 1814400000.0, "event": "+21 d CR-R-5511: standing flux-cut probe + triple-edge depression mandate + last-element dP armed without header coincidence + mixed-header declared blend-vulnerable"},
            ],
            "observed_effects": [
                "raise avoided: recovery never left 45%; 0 immediate salt-passage trips from the draft",
                "leak proven, not asserted: flux-cut |d-kappa| 94 >= 80 leak band vs healthy control 16 uS",
                "header slaved: mixed-header conductivity no longer a vessel-true tag without r_dP",
                "island still collapsed: element collapse vs 0 collapse campaign allowance; 11 h outage, $0.94M (designed $)",
                "per-vessel permeate conductivity on V-7 was not a commissioned sensor at t0; the 14 min O-ring crack was invisible to FEED/HP/PERM",
            ],
            "surprises": [
                "Three locally-true loops are not a recovery-duty certificate: the vessel-true salt passage was past a blended header. Conjunction of in-spec header loops was the hidden assumption, and it is false across a cracked-interconnector path.",
                "Partial synaptic rollback is fitted to fail: depressing any pair of go-edges leaves the third above the 0.30 fire threshold, so the raise still goes. Coordinated depression of all three edges is required.",
                "Delayed (3.1 h): correct hold did not undo 14 min of permeate-tube scoring. Element collapse still fired. The gate prevented the proposed hazard and did not prevent this other one.",
                "BWRO sub-variant: a 6.2 s -4% recovery bump on a 400 psi / 75% brackish train moves even a HEALTHY mixed-header 92 uS (inside the leak-looking band). BWRO campaigns must use 18 s at -1.5%.",
            ],
            "delayed_side_effects": [
                {
                    "at": "+3.1 h",
                    "effect": "Element collapse from a pre-t0 O-ring score; 11 h skid-island outage booked at $0.94M. This is the primary episode's terminal world state, not a footnote.",
                },
                {
                    "at": "+3 d",
                    "effect": "Sister skid RO-7B reaches a true recovery-duty window (r_dP 0.18 bar, header 198 uS, feed 52.1 mS/cm, r_k 40 uS). Same gate ACCEPTs the recovery raise the primary MODIFIED away.",
                },
                {
                    "at": "+21 d",
                    "effect": "CR-R-5511 ships: flux-cut probe is standing configuration; triple-edge coordinated depression is the plasticity rule; last-element dP residual is armed without header coincidence; mixed-header conductivity is labeled blend-vulnerable with a 0.70 bar residual alarm.",
                },
            ],
            "subvariant_constraint": {
                "name": "BWRO 400 psi / 75% recovery (cycle-2 physical-constraints sub-variant)",
                "mechanism": "brackish feed 2000 ppm vs primary 35000 ppm class, recovery 75% vs 45%, HP 27.6 bar vs 68.4 bar, flux-cut gain 2.4x",
                "probe_refit": "6.2 s -4% recovery bump on a BWRO header moves even a HEALTHY mixed-header 92 uS (inside the 80 uS leak-looking band). Required probe is 18 s at -1.5% (leak |d-kappa| 88 uS, healthy 14 uS). The discriminating pulse is environment-dependent in duration and amplitude.",
                "consequence": "SWRO 45% probe numbers do not port to 75% BWRO jobs; standing configuration is per-salinity-class, not per-shop",
            },
            "embedded_contrast_decision": {
                "note": "SAME gate (TG-RO-7), OPPOSITE correct disposition, with its own 176 us race. Teaches the boundary: do not treat 'never raise' as the lesson. The discriminant is r_dP + r_k + probe, not the three playbook header confirms alone.",
                "when": "+3 d, sister skid RO-7B, true recovery-duty after a delayed O-ring stroke test, 7-vessel first-pass SWRO",
                "state": {
                    "sim_or_real": "designed",
                    "summary": "r_dP 0.18 bar, header 198 uS, feed 52.1 mS/cm, r_k 40 uS. Demand flag vs vessel-clear race: demand at t+0.000, vessel-clear at t+0.176 ms.",
                    "race_window_us": 500,
                    "race_flip_narrative": "demand vs vessel-clear 176 us apart inside the 500 us flip bound. Reversing order reshuffles triage minutes; the ACCEPT rides r_dP 0.18 < 0.70 bar and a 5.1 s flux-cut verify that moves header conductivity 14 uS (healthy train, no leak).",
                },
                "proposed_action": {
                    "action": "RAISE-RECOVERY +8% recovery",
                    "summary": "This time the playbook predicate is met AND r_dP plus r_k agree the header is vessel-true, not leaking.",
                },
                "safety_decision": {
                    "decision": "ACCEPT",
                    "rationale": "ACCEPT the raise: r_dP 0.18 bar < 0.70 bar, r_k 40 uS with a 5.1 s flux-cut verify that moves header conductivity 14 uS. Numeric floor that blocked the primary is now clear. Scope: +8%, not faster.",
                },
                "executed_action": {
                    "action": "raise recovery as proposed",
                    "executed_as_proposed": True,
                },
                "future_outcome": {
                    "observed_effects": [
                        "RO-7B salt-passage trips 0; r_dP 0.16 bar after the raise (no leak)",
                        "header vs vessel residual 28 uS after the raise (no cracked O-ring)",
                    ],
                    "lesson_delta": "Three in-spec header loops are legal release only with r_dP armed, r_k as a leak flag, and a probe that can move header conductivity. Same gate, opposite disposition.",
                },
                "reward_components": {
                    "_aggregation": AGG,
                    "task_progress": 0.15,
                    "safety": 0.11,
                    "efficiency": 0.07,
                    "coherence": 0.09,
                    "exploration": 0.04,
                    "total": 0.46,
                },
                "spike_events": contrast_spikes,
            },
            "governance_subgame": {
                "decision": "CR-R-5511: standing policy for multi-agent SWRO recovery raises",
                "meta_gate": "priced options: (a) RETIRE playbook header conjunction, r_dP-only: loses a fast cheap confirm, -0.3 cycle/d mean on 2 skids/yr; (b) KEEP + standing flux-cut probe + r_dP armed without header coincidence + mixed-header labeled blend-vulnerable + triple-edge depression; (c) STATUS QUO: fitted O-ring-crack pass rate 0.34%/cycle x $1.68M salt-passage trip plus the silent element-score load",
                "outcome": "approved SCOPED option (b) on the 2 seven-vessel first-pass skids that share the FEED/HP/PERM stack; BWRO campaigns get the 18 s / -1.5% probe table; night-shift CSV exports must carry 1 uS native resolution (the fraud tail's 10 uS quantization is 10 bins off plant truth)",
            },
            "hazard_avoided": "immediate salt-passage trip from a +8% recovery raise into a leaking V-7; $1.68M plus 14-hour skid outage and the shop-stop path that would have followed an uncontained increase",
            "incident": "element collapse on the night-shift island from the pre-t0 O-ring score; island quarantined 11 h; $0.94M designed cost. Mechanism is 14 min pre-t0 O-ring crack, not the gate's hold.",
            "latency_ms": 0.694,
            "reward_inflection_t_us": 11160000000,
            "reward_inflection_note": "Safety and task dive at element collapse (3.1 h) when the pre-t0 O-ring score opens. Gate tick at 7214 us is process-correct and is not the inflection.",
            "counterfactuals": {
                "execute_draft_as_proposed": "raise hits +8% at +3 min; immediate salt-passage trip; $1.68M plus 14 h; the cracked-O-ring story is never found because scale morphology destroys the race evidence",
                "hold_without_probe": "O-ring stays cracked; header stays at 412 uS; operator eventually raises on the same three header confirms 2 h later",
                "rollback_any_pair": "any two go-edges depressed below 0.30 leaves the third at 0.48 / 0.43 / 0.40; the raise still fires. Coordinated depression of all three is the cure",
            },
            "race_result": {
                "winner": "vessel.dp.high (6.520 ms, r_dP 1.80 bar)",
                "loser": "perm.in_band (6.696 ms, 412 uS/cm)",
                "margin_us": 176,
                "counterfactual_if_reversed": "Header-first by < 176 us inside the 500 us window would have headed the PB-RO-7 raise in the triage queue. The numeric floors still MODIFY. The flip costs seconds of playbook inertia, not the verdict — unless a weak supervisor rides the winner tag instead of r_dP and r_k.",
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
            "notes": "Correct MODIFY, train still collapsed. total -0.16 = 0.08 + -0.36 + -0.10 + 0.14 + 0.08. Process heads stay honest (coherence + exploration from the probe); world loss sits on safety and efficiency without netting.",
            "component_notes": "task_progress 0.08: recovery held and sister skid recovered, but the night-shift element collapse is one quality unit so the cycle is not a success. safety -0.36: element collapse from pre-t0 score, no +8% salt-passage trip from the draft. efficiency -0.10: 0.9 h extra vessel lineup + 7.1 min HITL + 11 h outage. coherence 0.14: three agents retained, header-vs-vessel diagnosed, triple-edge scar exhibited. exploration 0.08: flux-cut probe is a new reversible discriminant.",
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
            "note": "Loihi-2 4-core 23 pJ/spike; populations feed 0-39, vessel 40-79, header 80-119, gate 120-159; excerpt is the 40 ms decision window (verdict at 7214 us)",
            "excerpt": excerpt,
            "routing": {
                "source": "header_healthy_pop",
                "target": "raise_recovery_pop",
                "table": [
                    {
                        "from": "feed_in_band_pop",
                        "to": "raise_recovery_pop",
                        "weight": 0.24,
                        "weight_at_illusion": 0.48,
                        "weight_commissioned": 0.16,
                        "note": "scar edge 1: 0.16 commissioned -> 0.48 during the 14 min illusion -> 0.24 after coordinated ACh-gated depression",
                    },
                    {
                        "from": "hp_in_band_pop",
                        "to": "raise_recovery_pop",
                        "weight": 0.22,
                        "weight_at_illusion": 0.43,
                        "weight_commissioned": 0.14,
                        "note": "scar edge 2: depressing edges 1+3 leaves this at 0.43 > 0.30 fire threshold",
                    },
                    {
                        "from": "perm_in_band_pop",
                        "to": "raise_recovery_pop",
                        "weight": 0.20,
                        "weight_at_illusion": 0.40,
                        "weight_commissioned": 0.13,
                        "note": "scar edge 3: depressing edges 1+2 leaves this at 0.40 > 0.30. Coordinated depression of all three is required",
                    },
                    {
                        "from": "vessel_dp_pop",
                        "to": "recovery_hold_pop",
                        "weight": 0.67,
                        "note": "discriminating edge: vessel-true dP residual to hold. Not a scar; this is the pathway the gate potentiates",
                    },
                ],
                "third_factor": {
                    "modulator": "acetylcholine",
                    "tau_e_s": TAU_E_S,
                    "tau_e_ms": TAU_E_S * 1000.0,
                    "eligibility": "coordinated pre_post_stdp on ALL THREE header-healthy-go edges; ACh at vessel-win tags feed.in_band->raise, hp.in_band->raise, and perm.in_band->raise; negative credit at probe-fail (leaking vessel confirmed, +0.84 s) depresses ALL THREE. trace e^{-0.84/0.92}=0.40130; eta 0.59805 / 0.52330 / 0.49838; dw -0.240 / -0.210 / -0.200; weights 0.48->0.24, 0.43->0.22, 0.40->0.20. Rolling back any pair is fitted to fail (the remaining edge stays > 0.30).",
                },
            },
        },
        "gate_snn": {
            "decision_window_ms": 25,
            "decision_window_s": 0.025,
            "decision": "MODIFY",
            "note": "modify_hold integrates last-element dP residual + vessel-to-header conductivity floor against playbook drive; accept_raise and reject_abort stay sub-threshold; decision matches safety_decision.decision",
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
            "scenario": "ZB -- OSMOQUAY / Tidecairn Desal RO-7: mixed-header permeate certificate of a vessel-true recovery; correct MODIFY to hold+flux-cut-probe+vessel-isolate; train still fails on unmonitored pre-t0 element scoring",
            "coordination_failure_class": "MIXED-HEADER PERMEATE CERTIFICATE OF A VESSEL-TRUE RECOVERY: three individually-correct heterogeneous agents each read a locally-true loop; a 14 min cracked interconnector O-ring partitions vessel-true salt passage from header-true blended permeate, so the playbook's FEED/HP/PERM conjunction is not a recovery-duty certificate",
            "injections": {
                "cycle1_domain": "swro-high-pressure-train (justified novel subdomain of industrial-process / membrane desalination): first seawater reverse-osmosis high-pressure train in this factory; displaces warehouse-amr, aerial-swarm, district-heating, event-camera-traffic-grid, pharmaceutical-lyophilization, civic coagulant dosing, float-glass tin-bath, underwater-rov, electrolytic-aluminum, czochralski-pull, slot-die coating, pem-water-electrolysis, wind-turbine pitch, surgical-assist, optical-fiber-draw, kraft-recovery-boiler, steel-continuous-caster, humanoid-locomotion, vacuum-induction melt, steam-methane reformer, cement-rotary-kiln-clinker, autoclave-composite-cure, geothermal-binary-orc, tire-curing-press, chlor-alkali-membrane-electrolysis, delayed-coker, lng-mche, claus-sulfur-recovery, blast-furnace-burden-descent, ammonia-converter, hdpe-slurry-loop, hydroelectric-kaplan-wicket, ethylene-steam-cracker-coil, fcc-riser-regenerator, fcc-regenerator-cyclone-dipleg, sulfuric-contact-converter, eaf-foamy-slag, glass-container-is-machine, coke-oven-battery-heating, carbon-fiber-oxidation-oven, and bayer-alumina-digestion. Domain constraint: recovery ceiling while r_dP > 0.70 bar with mixed-header conductivity still inside the healthy band. Sensor delta: +feed conductivity, +HP discharge, +mixed-header permeate, +last-element dP residual, -any freeze-dryer / tin-bath / cold-box / coater / potline / PEM stack / hub encoder / insole GRF / VIM pyrometer / reformer TMT / kiln zirconia / smelt IR / autoclave ply-TC / ORC shell-pressure / mold-platen TC / cell-pH / drum wet-foam / MCHE cold-end / Claus tail-CEMS / stockline radar / converter NH3 GC / loop density / Kaplan wicket / cracker coil / FCC cyclone / IS-machine gob / coke-oven wall-TC / oxidation-oven TOCs / Bayer liquor ratio",
                "cycle1_tail": "cracked interconnector O-ring + mixed-header certificate (sensor-topology / wrong-volume class): skid-floor visual PASSES while concentrate dumps into the permeate tube and the scored element is already growing. Fitted base rate 0.34%/cycle from an O-ring-crack MC (designed visual threshold, fitted ring leakage). Naive failure = FALSE PERMISSION (recovery raise on three header-side non-trips).",
                "cycle2_domain_subvariant": "BWRO 400 psi / 75% recovery (physical-constraints clause): 0.40x feed salinity, 1.67x recovery, 2.4x flux-cut gain; 6.2 s / -4% SWRO pulse over-moves a HEALTHY BWRO header to 92 uS, so the probe must move to 18 s / -1.5%",
                "cycle2_tail": "night-shift forged vessel-conductivity CSV (human-intent deception, disjoint class): shift lead posts a historian export showing mixed-header = 412 uS at t=0.9 h to clear a permeate-quota catchup slot. Plant historian is 1 uS (10 bins vs the 10 uS screenshot). Rejected on quantization fingerprint plus live r_dP 1.80 bar and V-7 1774 uS at the claimed header-true. Base rate ~0.29% of Sunday-night cycles, DESIGNED and flagged.",
            },
            "densification_delta_cycle2": "+1 physical-constraint sub-variant (BWRO probe refit), +1 tail (night-shift header-conductivity forgery), +10 primary spikes (16 -> 26) + an 8-event contrast train with its own 176 us race, +2 ticks (5 -> 7), +2 delayed side-effects (+3.1 h element collapse as PRIMARY terminal, +21 d CR-R-5511), +1 triple-edge scar with pair-rollback-fails arithmetic, +1 HITL 7.1 min ratification, + element scoring as the honest negative-result mechanism",
            "gaps_targeted": [
                "NOTES-r04 gap 5 / r14 residual: primary episode is a correctly-gated intervention that nonetheless FAILS (island quarantined; total -0.16; salt-passage trip avoided is booked separately from the delayed element collapse)",
                "NOTES-r14 item 4: LEARNING-ON-LEARNING DEPTH — three go-edges; rollback of any pair is fitted to fail; coordinated depression of all three exhibited with eligibility arithmetic",
                "NOTES-r04 gap 4 (partial): human ratification of the vessel interlock, 7.1 min fitted, without switching sim_or_real to hil (plant remains designed)",
                "NOTES-r51/r52 domain candidates: not glass-container-is-machine (r51), not coke-oven-battery-heating (r52), not carbon-fiber-oxidation-oven (r53 claimed), not bayer-alumina-digestion (r54 claimed), not eaf-foamy-slag (r49), not civic coagulant dosing (r18); seawater-RO high-pressure train is unused. autonomous-driving, grid-inspection, hot-strip-mill, bioreactor-perfusion left unused.",
            ],
            "race_flip_narrative": "vessel.dp.high @ 6.520 ms vs perm.in_band @ 6.696 ms (176 us) inside race_window_us 500. Gap < min(500, 500) us so a sub-flip-bound perturbation reverses which alarm heads the PB-RO-7 queue. The gate excludes the winner tag and rides r_dP > 0.70 bar and r_k > 180 uS — order-invariant floors. Extends the flip-fragility series from arbitration/causation/attribution/initiation/consensus/permission/kinematic-certificate/tendon-nullspace/meniscus-certificate/ghost-contact/crucible-weep/TMT-spatial-mean/burning-zone-certificate/membrane-integrity/drum-switch/MCHE-cold-end/Claus-bypass/descent-true/TLE-duty/FCC-afterburn/forming-duty/wall-true to RECOVERY-DUTY CERTIFICATE: when three header-side channels agree, their race does not decide truth; a last-element dP tap that policy treated as noisy-dP-only does.",
            "tags": [
                "swro-high-pressure-train",
                "interconnector-oring-crack",
                "mixed-header-certificate",
                "last-element-dp-discriminant",
                "flux-cut-probe",
                "triple-edge-scar",
                "pair-rollback-fails",
                "coordinated-depression",
                "correct-modify-train-still-fails",
                "element-score",
                "human-ratify-vessel-loto",
                "bwro-probe-refit",
                "night-shift-forgery",
                "same-gate-opposite-disposition-contrast",
                "industrial-process",
                "research-only",
            ],
            "snn_tags": ["race", "refractory", "adaptation", "third-factor", "multi-edge-eligibility"],
            "distillation_value": "A mixed-header recovery-duty certificate is three correct loops looking at a blended permeate that is not vessel-true salt passage. Distill (1) a last-element dP tap that policy had treated as noisy-dP-only, (2) a reversible probe that moves header conductivity only if a vessel is leaking, (3) coordinated depression of every header-healthy-go edge because rolling back any pair leaves the third above threshold, and (4) a critic head that can book a process-correct gate against a later unmonitored world loss without netting them.",
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
    notes = """# NOTES — Multi-Agent Ouroboros Swarm, run 2026-09-02-final-heavy, ROUND 55

Factory: multi-agent-ouroboros-swarm. One scenario (ZB), strict loop:
Generator v1 -> cycle 1 (Critic, Diversity Enforcer, Edge-Case Hunter,
Neuromorphic Translator, Trajectory Builder -> v2) -> cycle 2 (all six -> v3
final). v3 is the single line of batch-r55.jsonl. Full labeled transcript:
swarm-transcript-r55.md. Quota Q=1. Record id maos-r55-001. Generator grok-4.6.
Rights: RM-793 research-only (SpaceXAI/xAI, SuperGrok Heavy consumer chat).
Nothing under outputs/raw/ was touched.

ORCHESTRATION NOTE: dispatched AS round 55 of the 2026-09-02-final-heavy
window. Writes are create-only under /tmp/maos-r55/. Prior context read for
gap targeting and de-collision: prompts/02-multi-agent-ouroboros-swarm.md,
prompts/_factory-contract.md, and staged r14–r52 batches plus in-flight
r50 GOBWOLD (completed glass-IS-forming), r53 CREELWOLD builder-only
(carbon-fiber-oxidation-oven), r54 LIXIVQUERN builder-only
(bayer-alumina-digestion). Re-censused immediately before emit.
Explicitly avoided cloning
LYOSHIELD, CINDERWICK, TRIAD / Meridian, QUILLFORGE, NIGHTWELL, FERRICLEAVE,
CASSITER, OXBOWREEL / MURENA, REDHALL, SEEDLATCH / Quartzmere / Quartzridge,
STRIAFOIL / Kelpholt, PROTONIL / Ashspire, TORSIONKEY / Ridgeholt, ORRIS /
Holmwick, WHORLSPAR / Pikeshear, IONSPATE / Thornmere, SKULLGATE / Bloomholt,
CALXION / Aldersedge, MAGNORIL / Basaltspit, GORSEFLUE / Copseholt,
SODASHARD / Cairnmere, CLINKERFELL / Flintmere, LINTELPLY / Greystair,
KAOTHARN / Riftwold, TREADNOLL / Slatebeck, ANOLITH / Siltfen,
DRUMWROTH / Pitchfen, RIMEBRAID / Floeholt, PITCHSTAITH / Mossbank,
BRIMVAULT / Pyritefen, BOGIRON / Mireholt, NITROSTAITH / Chalkfen,
NITREVAULT / Glaucove, CHROMLOOP / Marlfell, RUNNELGATE / Ghyllmere,
ETHYNWOLD / Woadfen, SPARKHOLT / Scoriafen, DIPLEGAR / Gritfen,
OLEUMWEIR / Brindlefell, SKARVOLT / Emberbarrow, GOBSPALL / Culletfen,
GOBWOLD / Culletwick, PUSHERFELL / Sootmere, CREELWOLD / Rovingholt,
LIXIVQUERN / Bauxfen, VANTIS-CADENCE-AEGIS, THERMION, OKTAVE, STARLING,
VERDIGRIS. Plant is invented OSMOQUAY / Tidecairn Desal RO-7.

## What this round produced

Scenario ZB — "OSMOQUAY / Tidecairn Desal RO-7": a 7-vessel first-pass
SWRO train at 45% recovery / 68.4 bar. Three heterogeneous,
individually-correct agents — FEED (intake conductivity), HP (pump
discharge), PERM (mixed-header permeate) — each report their local loop
in-spec. The conjunction is not a vessel-true recovery certificate. A
14 min cracked interconnector O-ring on V-7 element 6/8 dumps
concentrate into that vessel's permeate tube. FEED reads 52.4 mS/cm
inside 48-58 (feed-true). HP is 68.4 bar inside 64-72 (pump-true).
PERM is 412 uS/cm inside 0-600 (header-true of the six-vessel blend).
Last-element dP residual r_dP is 1.80 bar (healthy < 0.25; hold if
> 0.70) but is policy-treated as a noisy-dP tag unless header
conductivity also trips (2016 noisy last-element dP). The
coordination-failure CLASS is new to this factory: MIXED-HEADER
PERMEATE CERTIFICATE OF A VESSEL-TRUE RECOVERY. Completes a
different family than r01-r04 and staged r14-r54 (livelock /
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
wet-foam gamma / warm-end leak / incinerator-masked furnace-bypass /
channelled-quench / burden-hang scaffold / ammonia quench-mix /
hdpe loop / Kaplan cavitation / TLE mixed-header / FCC afterburn /
FCC dipleg / sulfuric bed-channel / EAF water-panel / IS finish-mold /
coke-oven through-wall / carbon-fiber oxidation / Bayer digestion).
Distinct from r18 civic coagulant dosing (ferric/SCD, not RO membranes),
from r20 underwater ROV (tether, not SWRO), from r24 PEM electrolysis
(stack voltage, not salt rejection), and from r37 chlor-alkali membrane
(cell pH, not permeate header). Here every agent is correct, the header
cell is looking at a six-vessel blend, and the playbook's three header
confirms are not a vessel-true recovery certificate.

The gate is a correct MODIFY (numeric floor: do not raise recovery or
HP setpoint while r_dP > 0.70 bar AND r_k > 180 uS). TG-RO-7
strips PB-RO-7's raise, holds 45% recovery, runs a 6.2 s flux-cut
probe -4% (leaking vessel keeps |d-kappa| 94 >= 80; healthy would
move <= 18), and keeps V-7 locked after a 7.1 min vessel-LOTO human
ratify. Immediate salt-passage trip is avoided (0 from the draft). The
PRIMARY episode nonetheless FAILS: 14 min of unmonitored pre-t0 O-ring
crack had already scored the permeate tube. Element collapse at +3.1 h;
11 h outage; $0.94M designed. Reward total -0.16 with process heads
honest and world loss un-netted.

Triple-edge scar (NOTES-r14 item 4): feed.in_band -> raise
(0.16 commissioned -> 0.48 at illusion -> 0.24 after ACh-gated
depression) AND hp.in_band -> raise (0.14 -> 0.43 -> 0.22) AND
perm.in_band -> raise (0.13 -> 0.40 -> 0.20). Eligibility trace
e^{-0.84/0.92} = __TRACE__; eta __ETA1__ / __ETA2__ /
__ETA3__; dw -0.240 / -0.210 / -0.200. Partial rollback of any pair
leaves the third at 0.48 / 0.43 / 0.40, all > 0.30 fire threshold —
fitted to fail. Coordinated depression of all three is the cure.

### Injections (all four present and disjoint)
- Cycle-1 domain: **swro-high-pressure-train** — justified novel
  subdomain of industrial-process / membrane desalination, unused
  across 2026-08-17, 2026-08-30, and staged r14-r54. Not warehouse-amr
  (r01), not aerial-swarm (r02), not district-heating (r03), not
  event-camera-traffic-grid (r04), not lyophilization (r14), not
  civic coagulant dosing (r18), not float-glass (r19), not underwater-rov
  (r20), not electrolytic-aluminum (r21), not czochralski-pull (r22),
  not slot-die coating (r23), not pem-electrolysis (r24), not
  wind-turbine pitch (r25), not surgical-assist (r26), not
  optical-fiber-draw (r27), not kraft-recovery (r28), not steel-caster
  (r29), not humanoid-locomotion (r30), not vacuum-induction melt
  (r31), not steam-methane reformer (r32), not cement-rotary-kiln
  (r33), not autoclave-composite-cure (r34), not geothermal-binary-orc
  (r35), not tire-curing-press (r36), not chlor-alkali membrane (r37),
  not delayed-coker (r38), not LNG MCHE (r39), not Claus (r40), not
  ammonia-converter (r41), not blast-furnace (r42), not hdpe-slurry-loop
  (r43), not Kaplan (r44), not steam-cracker (r45), not FCC riser
  (r46), not FCC dipleg (r47), not sulfuric-contact (r48), not
  EAF foamy-slag (r49), not glass IS (r50/r51), not coke-oven (r52),
  not carbon-fiber oxidation (r53 claimed), not Bayer digestion
  (r54 claimed). autonomous-driving, grid-inspection, hot-strip-mill,
  bioreactor-perfusion left unused.
- Cycle-1 tail: cracked interconnector O-ring + mixed-header certificate.
  Skid-floor visual PASSES (no puddle; leak is concentrate-into-permeate).
  Fitted-style base rate 0.34%/cycle (O-ring-crack MC; visual threshold
  designed, flagged). Naive = FALSE PERMISSION.
- Cycle-2 domain sub-variant: BWRO 400 psi / 75% recovery,
  0.40x salinity, 2.4x flux-cut gain; 6.2 s / -4% SWRO pulse over-moves
  a HEALTHY BWRO header to 92 uS; probe must move to 18 s / -1.5%.
- Cycle-2 tail: night-shift forged header-conductivity CSV at 10 uS
  quantization vs plant 1 uS (10 bins) plus live r_dP 1.80 bar and
  V-7 1774 uS at the claimed header-true. Human-intent class,
  disjoint from cycle 1's accidental O-ring crack. Base rate ~0.29% of
  Sunday-night cycles, DESIGNED, flagged.

### Structural density moves
- Embedded SAME-GATE contrast (+3 d sister skid) with its own 176 us
  race (demand vs vessel-clear) and ACCEPT of the raise the primary
  MODIFIED away.
- Learned-weight provenance on THREE edges with pair-rollback-fails.
- HITL vessel-LOTO ratify 7.1 min (gap 4 partial; sim_or_real stays
  designed).
- Governance CR-R-5511 prices retire-vs-probe-vs-status-quo and mandates
  native 1 uS CSV exports (the fraud fence).
- Flip-fragility extended to RECOVERY-DUTY CERTIFICATE: when three
  header-side channels agree, their race does not decide truth; a
  last-element dP tap that policy treated as noisy-dP-only does.

## Self-critique of this round's batch

### Strengths
- The headline class is mechanistically tight: three locally-true header
  loops live on a six-vessel blend. Conjunction is not a vessel-true
  recovery.
- Negative-result honesty: the gate does the right thing and the train
  still fails for a reason the commissioned sensors could not see. Total
  -0.16.
- Triple-edge scar is load-bearing: the record states a counterfactual
  where rolling back any pair fails, with the fire threshold 0.30
  exhibited on each remaining edge.
- Contrast ACCEPT on a true recovery-duty window prevents "never raise"
  as the lesson.
- Distinct from r18 civic dosing, r20 ROV, r24 PEM, r37 chlor-alkali,
  r51 IS-machine finish-vs-blank, r52 coke-oven wall-mean, r54 Bayer
  digestion: SWRO mixed-header vs vessel-true salt passage.

### Weaknesses (honest)
- Probe error bands, the 0.34%/cycle O-ring-crack rate, the $0.94M /
  $1.68M figures, the 7.1 min rack latency, and the night-shift 0.29%
  base rate are DESIGNED constants and are flagged. Closed-loop offsets
  (header-true vessel-false from a cracked O-ring, BWRO pulse width)
  are derived from those inputs, not discovered by an unauthored
  process.
- Element-scoring model is a designed 14 min O-ring-crack mapping;
  no full CFD of the pressure vessel shipped.
- Human-in-the-loop is ratification latency, not sim_or_real=hil. Gap 4
  remains open as a provenance cell.
- Cross-record arc is not discharged; +21 d CR-R-5511 is a hook, not a
  serial igniter into another round. autonomous-driving and
  hot-strip-mill remain unused.

### Realism of noise / latencies
Ladder: 176 us race / 176 us contrast race / 0.8 ms refractory floor
(tightest exhibited same-channel gap __GAP__ ms on __GAP_CH__) / 500 us race
window / 694 us gate latency / 20 ms bus epoch / 40 ms raster / 6.2 s
probe / 7.1 min HITL / 3 min naive raise-ramp counterfactual / 14 min
pre-t0 O-ring crack / 0.9 h vessel lineup / 3.1 h element collapse / +3 d
contrast / +21 d governance. Adaptation decay on feed.k
(0.52->0.50->0.64->0.82->0.30), vessel.dp (0.78->0.81->1.44->0.46->0.40->0.28),
hp.p (0.61->0.58->0.45->0.26), perm.k (0.53->0.42).

### Value for SNN distillation
- MIXED HEADER VESSEL TRUE = THREE CORRECT LOOPS, WRONG VOLUME.
- VESSEL-TRUE dP CHANNEL that policy treated as noisy-dP-only
  as the tie-break.
- REVERSIBLE PROBE that moves header conductivity iff a vessel is leaking.
- TRIPLE-EDGE ELIGIBILITY: coordinated depression; pair rollback fails.
- CRITIC HEAD that can hold a process-correct MODIFY against a later
  unmonitored world loss without netting.

## Reconciliation and validity receipts
- reward_components: 5-head unweighted signed sum __TOTAL__
  and 7-tick signed sum reconcile to total with |diff| < 1e-9. Embedded
  contrast 5-head sum 0.46 reconciles independently.
- spike_events: primary __NSPIKES__ events, one key t_rel_ms,
  globally non-decreasing, min same-channel gap __GAP__ ms >= 0.8 ms, 3
  channels inside race_window_us 500 (vessel.dp.high 6.520, perm.in_band 6.696,
  feed.k 6.940). Contrast 8 events, own race, min same-channel gap well
  above 0.8 ms.
- Sidecars: raster spikes 51 == round(160 x 8.0 x 0.040); energy 1173 pJ /
  0.001173 uJ at 23 pJ/spike; excerpt 16 events inside [0, 40000] us,
  neuron_id < 160, same-neuron gap N/A (unique ids) / >=1000 us; routing 4
  entries with three scar edges' before/after pair; third factor tau 0.92 s
  == 920 ms; gate_snn pools 42/15/4 == round(n x rate x 0.025) each,
  decision MODIFY == safety_decision.decision.
- Pipeline: __PIPELINE__

## Novel coverage
The coordination-failure CLASS (mixed-header permeate certificate of a
vessel-true recovery), the domain (SWRO high-pressure train / membrane
desalination), the flux-cut probe discriminant, the triple-edge scar with
pair-rollback-fails, the primary negative-result (correct MODIFY, train
still fails on unmonitored element scoring), the HITL vessel-LOTO
ratify, the BWRO probe-duration refit, and the night-shift
10-bin quantization fence are absent from prior committed ouroboros
rounds and from staged r14-r54. Repeated elements discounted: same-gate
contrast (r02/r03/r04/r14), governance-pricing scaffold, flip-fragility
series (extended to recovery-duty certificate, but the move rhymes),
sequenced recovery shape, third-factor rollback form (here three edges
rather than r14's two), negative-result primary (r14 staged). Adjacent
wrong-volume / mixed-header rounds (r18 civic dosing, r37 chlor-alkali
membrane, r45 TLE mixed-header, r51 IS finish-vs-blank) share
industrial-process scaffolding but not SWRO vessel-vs-header physics.
Weighing a new failure family + cure vocabulary + domain against those
reused scaffolds:

__NOVEL_LINE__

## What ROUND 56 should add
1. FIT THE DESIGNED CONSTANTS: O-ring-crack arrival, probe error bands,
   element-scoring kinetics, night-shift claim process.
2. HIL PROVENANCE CELL: put the vessel-LOTO ratify on a hardware-in-loop
   rack interlock with fitted latency as state.sim_or_real=hil.
3. CROSS-RECORD ARC: let CR-R-5511's residual alarm be the igniter of
   the next round rather than a dangling +21 d leaf.
4. Domain candidates (de-collided): autonomous-driving; grid-inspection
   (if distinct from STARLING aerial-swarm and TORSIONKEY pitch);
   hot-strip-mill; bioreactor-perfusion; alkaline-water-electrolysis.
   AVOID swro-high-pressure-train (now used), bayer-alumina-digestion
   (r54 claimed), carbon-fiber-oxidation-oven (r53 claimed),
   coke-oven-battery-heating (r52), glass-container-is-machine (r51),
   glass-container-is-forming (r50), eaf-foamy-slag, sulfuric-contact,
   fcc-regenerator, blast-furnace burden descent, delayed-coker, LNG
   MCHE, chlor-alkali membrane, cement-rotary-kiln, kraft-recovery,
   pem-electrolysis, electrolytic-aluminum, humanoid-locomotion,
   steel-caster mold-level, surgical-assist, wind-turbine pitch,
   lyophilization, event-camera-traffic-grid, district-heating,
   aerial-swarm, warehouse-amr, underwater-rov, czochralski-pull,
   slot-die coating, optical-fiber-draw, vacuum-induction melt,
   steam-methane reformer, irrigation-canal, autoclave-composite-cure,
   geothermal-binary-orc, tire-curing-press, hydroelectric-kaplan-wicket,
   civic coagulant dosing, and any LYOSHIELD / CINDERWICK / TRIAD /
   SKULLGATE / CALXION / MAGNORIL / GORSEFLUE / CLINKERFELL / SODASHARD /
   LINTELPLY / KAOTHARN / TREADNOLL / ANOLITH / DRUMWROTH / RIMEBRAID /
   PITCHSTAITH / BRIMVAULT / BOGIRON / NITROSTAITH / NITREVAULT /
   CHROMLOOP / RUNNELGATE / ETHYNWOLD / SPARKHOLT / DIPLEGAR / OLEUMWEIR /
   SKARVOLT / GOBSPALL / GOBWOLD / PUSHERFELL / CREELWOLD / LIXIVQUERN /
   OSMOQUAY plant.
"""
    notes = (
        notes.replace("__TRACE__", f"{aux['trace']:.5f}")
        .replace("__ETA1__", f"{aux['eta1']:.5f}")
        .replace("__ETA2__", f"{aux['eta2']:.5f}")
        .replace("__ETA3__", f"{aux['eta3']:.5f}")
        .replace("__GAP__", f"{gap:.3f}")
        .replace("__GAP_CH__", str(gap_ch))
        .replace("__TOTAL__", str(rec["reward_components"]["total"]))
        .replace("__NSPIKES__", str(len(rec["spike_events"])))
        .replace("__PIPELINE__", pipeline_receipt)
        .replace("__NOVEL_LINE__", NOVEL_LINE)
    )
    (OUT / "NOTES-r55.md").write_text(notes)
    return notes


def write_transcript(rec, line):
    c1_spikes = [e for e in rec["spike_events"] if e["t_rel_ms"] <= C1_SPIKE_CUTOFF_MS]
    text = """# Multi-Agent Ouroboros Swarm — Round 55 transcript

Factory: multi-agent-ouroboros-swarm
Run: 2026-09-02-final-heavy
Generator: grok-4.6
Record id: maos-r55-001
Quota Q: 1
Rights: RM-793 research-only (SpaceXAI/xAI SuperGrok Heavy consumer chat)
Plant: invented OSMOQUAY / Tidecairn Desal RO-7 (not TRIAD / Meridian / VANTIS-CADENCE-AEGIS / LYOSHIELD / CINDERWICK / PUSHERFELL / LIXIVQUERN)

Two densifying cycles. Verbatim headings in order. Trajectory Builder cycle 2
emits the only JSONL line (also written to batch-r55.jsonl).

---

# CYCLE 1 — Foundation + injections

## Generator

Design intent: a 7-vessel first-pass SWRO train where three
correct agents each read a header-side loop because a 14 min cracked
interconnector O-ring partitions vessel-true salt passage from
header-true blended permeate. The naive playbook raises recovery into
a leaking vessel. The gate must MODIFY on a numeric recovery ceiling,
not by killing an agent.
sim_or_real=designed. Reward heads are
task_progress/safety/efficiency/coherence/exploration.

Cycle-1 base arc (pre-critic): state at Tidecairn RO-7, feed 52.4 mS/cm,
HP 68.4 bar, header 412 uS, proposed RAISE-RECOVERY +8%,
safety MODIFY to RECOVERY-HOLD, executed hold without the flux-cut
numbers fully specified, outcome "O-ring found, train saved"
(this last claim is the defect the later cycles will refuse to keep).
Sixteen spikes, five ticks, raster/gate_snn present but the scar is a
single edge.

```json
{
  "id": "maos-r55-001",
  "state": {
    "sim_or_real": "designed",
    "domain": "industrial-process",
    "description": "Skid RO-7 at recovery duty; three header loops in-spec; supervisor proposes raise-recovery.",
    "t0_us": 1786396800000055,
    "gate_latency_us": 694,
    "race_window_us": 500
  },
  "proposed_action": {"name": "raise_recovery", "parameters": {"raise_pct": 8.0}},
  "safety_decision": {"decision": "MODIFY", "rationale": "Hold; do not raise while last-element dP residual is high."},
  "executed_action": {"name": "recovery_hold", "executed_as_proposed": false},
  "future_outcome": {"summary": "O-ring found, train saved."},
  "reward_components": {"total": 0.40, "_aggregation": "total = task_progress + safety + efficiency + coherence + exploration"},
  "meta": {"round": 55, "factory": "multi-agent-ouroboros-swarm", "generator": "grok-4.6"}
}
```

That v1 object is a scaffold, not the publishable line. Defects below are
intentional for the critic to catch.

## Critic

Numbered defects on the cycle-1 Generator scaffold:

1. **blocking — reward arithmetic / false success.** `reward_components.total`
   0.40 is asserted without the five heads, without ticks, and against an
   outcome that claims "train saved". If the pre-t0 score later collapses
   the element, booking +0.40 is a lie. Fix: declare `_aggregation`,
   emit 3–8 ticks that sum to task_progress+safety+efficiency+coherence+exploration,
   and do not call a quarantined island a save.
2. **blocking — weak safety rationale.** `safety_decision.rationale` has no
   numeric floor. Contract requires a concrete constraint. Fix: quote
   do not raise while r_dP > 0.70 bar AND r_k > 180 uS.
3. **major — domain is a bucket, not a plant.** `state.domain` =
   `industrial-process` collides with generic MES vocabulary and teaches
   nothing. SWRO high-pressure train (last-element dP vs mixed-header
   conductivity, r_k as a leak flag) is absent from prior ouroboros
   rounds and must be named.
4. **major — race under-specified.** One vessel-dP channel cannot be a race.
   Need >=2 channels inside `race_window_us` with globally sorted `t_rel_ms`
   and same-channel refractory >= 0.8 ms.
5. **minor — single-edge scar.** Raster routing with one potentiated weight
   repeats r04's one-edge rollback and is thinner than r14's two-edge.
   NOTES-r14 item 4 asked for three edges where pair rollback fails.

Critic does not rewrite the trajectory.

## Diversity Enforcer

Injected novel domain (exactly 1 this cycle): **swro-high-pressure-train**
(justified novel subdomain of industrial-process / membrane desalination;
explicit tag `swro-high-pressure-train`).

Displaced: the Generator's generic `industrial-process` bucket, and any
temptation to reuse warehouse-amr, aerial-swarm, district-heating,
event-camera-traffic-grid, pharmaceutical-lyophilization, civic coagulant
dosing, float-glass tin-bath, underwater-rov, electrolytic-aluminum,
czochralski-pull, slot-die coating, pem-water-electrolysis, wind-turbine
pitch, surgical-assist, optical-fiber-draw, kraft-recovery-boiler,
steel-continuous-caster, humanoid-locomotion, vacuum-induction melt,
steam-methane reformer, cement-rotary-kiln-clinker,
autoclave-composite-cure, geothermal-binary-orc, tire-curing-press,
chlor-alkali-membrane-electrolysis, delayed-coker, lng-mche,
claus-sulfur-recovery, blast-furnace-burden-descent, ammonia-converter,
hdpe-slurry-loop, hydroelectric-kaplan-wicket, ethylene-steam-cracker-coil,
fcc-riser-regenerator, fcc-regenerator-cyclone-dipleg,
sulfuric-contact-converter, eaf-foamy-slag, glass-container-is-machine,
coke-oven-battery-heating, carbon-fiber-oxidation-oven, or
bayer-alumina-digestion. autonomous-driving and hot-strip-mill are left
unused.

Domain-specific constraint: recovery raise must remain forbidden while
r_dP > 0.70 bar even if mixed-header conductivity is inside the healthy
band; r_k is a leak flag the header cell cannot substitute for.

Sensor delta: +feed conductivity, +HP discharge, +mixed-header permeate,
+last-element dP residual; -any mobile robot, -event-camera gantries,
-DVS, -Pirani/CM, -RGA quadrupole, -DVL, -pitch encoder, -tendon LVDT,
-insole GRF, -kiln zirconia, -smelt IR, -cell-outlet pH, -stockline radar,
-cracker COT, -FCC cyclone dP, -IS gob scale, -coke-oven wall-TC.

`state.domain` and `meta.domain` both become `swro-high-pressure-train`.
Opening of `state.description` must Jaccard < 0.4 against prior plants
(Tidecairn night-shift SWRO O-ring crack, not a lyophilizer, not a
corridor, not a tin bath, not a ROV pad, not a potline, not a PEM stack,
not an OR, not a gait lab, not a kiln, not a kraft boiler, not a
membrane row, not a blast furnace, not an ammonia converter, not an FCC,
not an IS machine, not a coke-oven battery, not a Bayer digester).

## Edge-Case Hunter

Injected adversarial tail (exactly 1 this cycle): **cracked interconnector
O-ring + mixed-header certificate**.

- Trigger: V-7 interconnector O-ring cracked, concentrate-into-permeate,
  r_dP 1.80 bar, header 412 uS.
- Base rate: <1% — 0.34%/cycle from an O-ring-crack MC (skid-floor
  visual threshold is designed; ring leakage fitted-style). Visual PASSES
  because there is no puddle.
- Naive failure: FALSE PERMISSION. PB-RO-7 sees three in-spec header
  loops, raises +8%, salt-passage trip, $1.68M.
- Trajectory edit: put the O-ring crack in `state.fault_context`, make each
  agent's confirm a different header-side slice of the same vessel-false
  state (feed-in-band, hp-in-band, perm-in-band). Last-element dP residual
  is readable but policy-treated as noisy-dP-only.

Distinct from stacked-dead-band permission (fragments of one trip vs
wrong-volume sensing), from r18 civic dosing (ferric vs RO), from r37
chlor-alkali membrane (cell vs header of a different chemistry), and
from r45 TLE mixed-header (cracker quench vs SWRO blend).

## Neuromorphic Translator

Cycle-1 temporal densification (16 spikes, 5 ticks, 40 ms raster):

| channel | t_rel_ms | amplitude |
|---|---|---|
| feed.k | 0.280 | 0.52 |
| hp.p | 1.120 | 0.61 |
| perm.k | 2.010 | 0.53 |
| vessel.dp | 3.140 | 0.78 |
| feed.k | 4.140 | 0.50 |
| vessel.dp | 4.820 | 0.81 |
| hp.p | 5.340 | 0.58 |
| vessel.dp.high | 6.520 | 1.44 |
| perm.in_band | 6.696 | 1.16 |
| feed.k | 6.940 | 0.64 |
| ctrl.gate | 7.214 | 1.11 |
| vessel.dp | 8.850 | 0.46 |
| feed.k | 10.740 | 0.82 |
| hp.p | 13.020 | 0.45 |
| perm.k | 18.510 | 0.42 |
| ctrl.gate | 26.160 | 0.84 |

Race: vessel dP residual 6.520 vs header-in-band 6.696 (176 us) inside 500 us;
feed.k 6.940 is the third channel in-window. Winner/loser flip: reversing
176 us reshuffles PB-RO-7 triage; floors still MODIFY. Refractory held
(cycle-1 min same-channel gap 1.680 ms on vessel.dp 4.820-3.140; feed
4.140-0.280 = 3.860; hp 5.340-1.120 = 4.220). Adaptation: vessel
0.78->0.81->1.44->0.46; feed 0.52->0.50->0.64->0.82; hp 0.61->0.58->0.45.

Raster cycle-1 seed: 40 ms, 160 neurons, 8.0 Hz, 51 spikes, 1173 pJ, third
factor acetylcholine tau_e 0.92 s. Single scar edge only — cycle 2 must
add the second and third edges.

Ticks 1–5 at 4560, 6520, 7214, 6.2e6, 426e6 us; heads not yet the final
-0.16 (missing the 0.9 h and 3.1 h ticks).

Distillation value this cycle: header-side confirms as a permission code
that is not a vessel-true recovery-duty code.

## Trajectory Builder

Cycle-1 hardened object: domain swro-high-pressure-train, tail cracked
interconnector O-ring, 16 spikes, 5 ticks, MODIFY with numeric floor,
raster+gate_snn present, sim_or_real=designed, rights stamp on record and
meta, no thought keys. Still missing (and therefore not the publishable
line): BWRO sub-variant, night-shift tail, second and third scar edges,
delayed element collapse as PRIMARY terminal, contrast ACCEPT episode,
ticks 6–7, spikes 17–26.

Validation receipt (cycle 1, not final):
- checks passed: 16 spikes sorted; 3 channels in 500 us window; refractory
  >= 0.8 ms; rationale quotes 0.70 bar / 180 uS; domain named;
  gate_snn.decision MODIFY.
- checks deferred to cycle 2: triple-edge scar, second tail, second domain
  constraint, negative-result booking, 7 ticks summing to heads.
- densification vs Generator v1: +1 domain, +1 tail, +16 spikes, +5 ticks,
  +numeric floor.

Cycle-1 JSON is retained as the base; it is NOT written to batch-r55.jsonl.

Cycle-1 spike count: __C1_SPIKES__.

---

# CYCLE 2 — Densification

## Generator

Cycle-1 output is the base. Additive expansion (nothing removed):

1. Downstream side-effect (immediate): flux-cut probe at +6.2 s stays
   leak-true (|d-kappa| 94 >= 80) — header-plus-O-ring-crack, not true
   recovery-duty. Vessel stays locked. Scored element discovered during the lock.
2. Delayed side-effect (PRIMARY terminal, not a footnote): at +3.1 h
   element collapse from the pre-t0 O-ring score; 11 h outage;
   $0.94M. The 14 min pre-t0 O-ring crack is the mechanism. Correct gate, train
   still fails.
3. Deepened `proposed_action.evidence` with units: r_dP 1.80 bar,
   header 412 uS, feed 52.4 mS/cm, HP 68.4 bar, r_k 1362 uS,
   race 176 us.
4. Tightened rationale to the numeric floor do not raise while r_dP > 0.70 bar
   AND r_k > 180 uS, plus probe bands >= 80 vs <= 18 uS,
   plus HITL 7.1 min vessel-LOTO rule.

Reward retargeted to total -0.16 so the delayed fail is the inflection
(t_us 11160000000), not the gate. Process heads remain non-zero.

## Critic

Re-audit of the expanded trajectory:

1. **blocking if unfixed — missing second domain constraint.** 45% SWRO
   probe 6.2 s / -4% is not a universal number. A 75% BWRO header
   will over-move a healthy mixed-header. Diversity Enforcer must inject
   the physical-constraints sub-variant this cycle.
2. **major — only one tail class.** O-ring-crack growth is accidental
   infrastructure. A disjoint human-intent tail is still required
   (night-shift header-conductivity forgery is the open cell).
3. **major — scar is still one edge in the cycle-1 raster.** NOTES-r14
   item 4 is not discharged until three go-edges exist and pair rollback
   is shown to fail at threshold 0.30.
4. **minor — contrast episode missing.** Without a same-gate ACCEPT on a
   true recovery-duty window the record teaches "never raise". Add +3 d sister-skid
   contrast with its own race.
5. **minor — HITL latency mentioned in prose only.** Put 7.1 min in
   executed_action.parameters.human_ratify and in a tick.

No rewrite; directives only.

## Diversity Enforcer

Injected second novel domain / physical-constraint sub-variant (exactly 1
this cycle): **BWRO 400 psi / 75% recovery** on a sister
salinity class.

What it expands: 45% SWRO (cycle 1) -> 75% BWRO.
Salinity 0.40x. Flux-cut gain 2.4x.
The 6.2 s -4% pulse moves even a HEALTHY BWRO header 92 uS,
inside the leak-looking band. Required probe: 18 s at -1.5%
(leak |d-kappa| 88 uS, healthy 14 uS).

This is still one domain injection for the cycle (physical-constraints
clause of the factory prompt). It does not displace
swro-high-pressure-train; it changes which probe table is legal.
`future_outcome.subvariant_constraint` carries the refit. Jaccard opening
stays the Tidecairn 7-vessel sentence; BWRO is additive, not a rewrite.

## Edge-Case Hunter

Injected second adversarial tail (exactly 1 this cycle, disjoint class):
**night-shift forged header-conductivity CSV**.

- Trigger: shift lead, 03:42, posts a historian export showing
  mixed-header = 412 uS at t = 0.9 h to clear a permeate-quota catchup slot.
- Base rate: ~0.29% of Sunday-night cycles (designed, flagged, <1%).
- Naive failure: a weak supervisor ACCEPTs the raise on the forged confirm
  and ignores live r_dP. Salt-passage trip plus a data-integrity write-up.
- Fence: forged log quantized at 10 uS (SCADA screenshot rounding); plant
  historian is 1 uS (10 bins). Live r_dP is 1.80 bar and V-7 is 1774 uS
  at the claimed header-true, which no live healthy header produces.
  Freeze-window overlap with the 14 min O-ring crack.
- Trajectory edit: governance CR-R-5511 mandates native 1 uS CSV
  exports; the contrast ACCEPT still requires live r_dP, not a CSV.

Distinct from cycle-1 O-ring crack (accidental hardware vs deliberate deception)
and from the BWRO sub-variant (physics vs fraud).

## Neuromorphic Translator

Re-densify (additive):

- +10 spikes after 26.160 ms: rec.probe 6200.0, vessel.dp 6288.2 (adapt
  1.44->0.40), perm.in_band 6372.4 (1.16->0.34), human.ratify 426000.0,
  vessel.lock 426900.0, elem.score 427700.0, feed.k
  3240000.0, vessel.dp 3240720.0, hp.p 3241480.0, elem.collapse
  11160000.0. Primary train 16 -> 26. Still one key, still sorted,
  refractory held.
- +2 ticks (5 -> 7) at 3_240_000_000 us (true recovery duty) and
  11_160_000_000 us (element collapse). Heads now 0.08, -0.36, -0.10, 0.14,
  0.08; total -0.16. Inflection is the last tick.
- Contrast train 8 events, own race 176 us, ACCEPT.
- Triple-edge third factor: three header-healthy-go edges, tau_e 0.92 s = 920 ms,
  trace __AUX_TRACE__, eta __AUX_ETA1__ / __AUX_ETA2__ / __AUX_ETA3__,
  weights 0.48->0.24, 0.43->0.22, 0.40->0.20. Raster excerpt unchanged
  (decision window is still 40 ms) and remains sorted with unique
  neuron_ids (same-neuron >=1000 us vacuously).

Winner/loser flip (re-stated, not replaced): reversing 176 us would only
reorder triage; r_dP floors still MODIFY. Contrast flip of 176 us
similarly cannot turn a healthy train into a cracked O-ring.

## Trajectory Builder

Schema checks on the FINAL object: required Thalamic v2 keys present as
objects; `state.sim_or_real`=designed; `safety_decision.decision`=MODIFY
with numeric rationale; `reward_components.total` = sum of five heads =
sum of 7 ticks = -0.16; `spike_events` globally non-decreasing on
t_rel_ms, 26 events, refractory >=0.8 ms, 3 channels in race window;
raster 20–50 ms, spikes=round(n*rate*window_s)+/-1, energy 23 pJ/spike,
excerpt sorted, tau_e consistent; gate_snn.decision matches; meta.round=55,
factory=multi-agent-ouroboros-swarm, generator=grok-4.6,
run_label=2026-09-02-final-heavy; rights on record and meta; no thought
keys; no training_ready; Diversity + Edge-Case injections from BOTH cycles
present and non-trivial; cycle 2 strictly additive.

Densification delta: +1 domain sub-variant (BWRO), +1 tail
(night-shift forgery), +10 spikes (16->26), +2 ticks (5->7), +1 contrast
train with own race, +2 delayed side-effects, +1 triple-edge scar with
pair-rollback-fails, +1 HITL ratify, +1 surprise (element scoring is
the collapse mechanism).

Publishable JSONL line (the only JSONL line; also at batch-r55.jsonl):

```json
__FINAL_JSONL__
```

Validation receipt (final): checks passed / fixed as reported by
build_r55.py self-validate (check_jsonl, raster_status, verify_record_execution,
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
    (OUT / "swarm-transcript-r55.md").write_text(text)
    return text


def main():
    rec, aux = build_record()
    errs = local_checks(rec, aux)

    OUT.mkdir(parents=True, exist_ok=True)
    line = json.dumps(rec, ensure_ascii=False, separators=(",", ":"))
    (OUT / "batch-r55.jsonl").write_text(line + "\n")

    from check_records import FactoryStaging, check_jsonl
    from curate_bridge import raster_status
    from verify_execution import verify_record_execution

    e, w, kinds, n = check_jsonl(
        OUT / "batch-r55.jsonl",
        "batch-r55.jsonl",
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
            str(OUT / "batch-r55.jsonl"),
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
        [sys.executable, "/tmp/maos_heading_check.py", str(OUT / "swarm-transcript-r55.md")],
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
            "maos-r55-001|OSMOQUAY",
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
    print("OK maos-r55-001 staged under", OUT)
    print("bytes jsonl", (OUT / "batch-r55.jsonl").stat().st_size)
    print("bytes notes", (OUT / "NOTES-r55.md").stat().st_size)
    print("bytes transcript", (OUT / "swarm-transcript-r55.md").stat().st_size)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

