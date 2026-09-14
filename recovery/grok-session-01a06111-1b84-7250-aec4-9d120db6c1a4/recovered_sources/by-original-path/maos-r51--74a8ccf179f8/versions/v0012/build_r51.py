#!/usr/bin/env python3
"""Build and self-check MAOS round-51 JSONL (research-only; not published)."""
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
OUT = Path("/tmp/maos-r51")
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
    "PITCHSTAITH",
    "Mossbank",
    "BRIMVAULT",
    "Pyritefen",
    "BOGIRON",
    "Mireholt",
    "NITROSTAITH",
    "Chalkfen",
    "NITREVAULT",
    "Glaucove",
    "CHROMLOOP",
    "Marlfell",
    "RUNNELGATE",
    "Ghyllmere",
    "ETHYNWOLD",
    "Woadfen",
    "SPARKHOLT",
    "Scoriafen",
    "DIPLEGAR",
    "Gritfen",
    "OLEUMWEIR",
    "Brindlefell",
    "SKARVOLT",
    "Emberbarrow",
    "GOBWOLD",
    "Culletwick",
    "GOBSPALL",
    "Culletfen",
    "GAUZEFELL",
    "Ammoxwick",
    "PUSHERFELL",
    "Sootmere",
    "CREELWOLD",
    "Rovingholt",
    "LIXIVQUERN",
    "Bauxfen",
    "VESPERTHORN",
    "ASHVEIL",
    "IRONMANTLE",
    "DUSKRELAY",
    "PALISADE",
    "TELAMON",
    "CHORDA",
    "Brinewell",
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
    "Emhart",
    "Bottero",
    "Owens-Illinois",
    "Verallia",
    "Ardagh Glass",
    "Vidrala",
    "Saint-Gobain",
    "Vetropack",
    "O-I Glass",
    "UOP",
    "Axens",
    "Honeywell UOP",
    "KBR",
    "Yara",
    "Kellogg",
    "Casale",
    "Haldor",
    "Saipem",
    "Clariant",
    "SABIC",
    "Dow Chemical",
    "LyondellBasell",
    "Nova Chemicals",
    "Stone & Webster",
    "W.R. Grace",
    "Valero Energy",
    "Marathon Petroleum",
    "Toray Membrane",
    "Hydranautics",
    "FilmTec",
    "DuPont Water",
    "Veolia Water",
    "IDE Technologies",
    "Acciona Agua",
    "Doosan Heavy",
    "Energy Recovery Inc",
    "Danfoss High Pressure",
)
R14_OPENING = (
    "Helixmere Biologics Building C lyophilizer LYO-4 is mid-primary on 8400 "
    "vials of a monoclonal antibody"
)
NOVEL_LINE = "Novel coverage: 48%"
PLANT = "OSMOLITH"
GEO = "Spumeholt"
CELL = "RO-8"
DOMAIN = "seawater-ro-desalination"
RECORD_ID = "maos-r51-001"
ROUND = 51
DELAY_S = 0.84
TAU_E_S = 0.92
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
        if p.parent.name == "maos-r51":
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
        if p.parent.name == "maos-r51":
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
        if p.parent.name == "maos-r51":
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
        [4560, 6512, 7198, 6_400_000, 492_000_000, 3_960_000_000, 12_960_000_000],
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
        {"channel": "hp.feed", "t_rel_ms": 0.310, "amplitude": 0.55},
        {"channel": "perm.cond", "t_rel_ms": 1.150, "amplitude": 0.62},
        {"channel": "flow.perm", "t_rel_ms": 2.050, "amplitude": 0.54},
        {"channel": "erd.dp", "t_rel_ms": 3.190, "amplitude": 0.76},
        {"channel": "hp.feed", "t_rel_ms": 4.170, "amplitude": 0.51},
        {"channel": "erd.dp", "t_rel_ms": 4.850, "amplitude": 0.79},
        {"channel": "perm.cond", "t_rel_ms": 5.370, "amplitude": 0.59},
        {"channel": "erd.dp.high", "t_rel_ms": 6.512, "amplitude": 1.42},
        {"channel": "perm.in_band", "t_rel_ms": 6.696, "amplitude": 1.15},
        {"channel": "hp.feed", "t_rel_ms": 6.920, "amplitude": 0.63},
        {"channel": "ctrl.gate", "t_rel_ms": 7.198, "amplitude": 1.09},
        {"channel": "erd.dp", "t_rel_ms": 8.870, "amplitude": 0.47},
        {"channel": "hp.feed", "t_rel_ms": 10.760, "amplitude": 0.81},
        {"channel": "perm.cond", "t_rel_ms": 13.050, "amplitude": 0.46},
        {"channel": "flow.perm", "t_rel_ms": 18.540, "amplitude": 0.43},
        {"channel": "ctrl.gate", "t_rel_ms": 26.180, "amplitude": 0.85},
        {"channel": "hp.probe", "t_rel_ms": 6400.0, "amplitude": 0.95},
        {"channel": "erd.dp", "t_rel_ms": 6488.4, "amplitude": 0.41},
        {"channel": "perm.in_band", "t_rel_ms": 6572.6, "amplitude": 0.35},
        {"channel": "human.ratify", "t_rel_ms": 492000.0, "amplitude": 0.79},
        {"channel": "erd.lock", "t_rel_ms": 492900.0, "amplitude": 0.71},
        {"channel": "membrane.score", "t_rel_ms": 493700.0, "amplitude": 0.87},
        {"channel": "hp.feed", "t_rel_ms": 3960000.0, "amplitude": 0.31},
        {"channel": "erd.dp", "t_rel_ms": 3960720.0, "amplitude": 0.29},
        {"channel": "perm.cond", "t_rel_ms": 3961480.0, "amplitude": 0.27},
        {"channel": "salt.trip", "t_rel_ms": 12960000.0, "amplitude": 0.93},
    ]

    contrast_spikes = [
        {"channel": "raise.demand", "t_rel_ms": 0.000, "amplitude": 0.84},
        {"channel": "dp.clear", "t_rel_ms": 0.184, "amplitude": 0.76},
        {"channel": "hp.feed", "t_rel_ms": 0.410, "amplitude": 0.27},
        {"channel": "perm.cond", "t_rel_ms": 1.460, "amplitude": 0.41},
        {"channel": "erd.dp", "t_rel_ms": 4.880, "amplitude": 0.50},
        {"channel": "ctrl.gate", "t_rel_ms": 7.020, "amplitude": 0.91},
        {"channel": "hp.probe", "t_rel_ms": 3200.0, "amplitude": 0.33},
        {"channel": "salt.trip", "t_rel_ms": 12960000.0, "amplitude": 0.10},
    ]

    excerpt = [
        {"t_us": 310, "neuron_id": 9},
        {"t_us": 1150, "neuron_id": 74},
        {"t_us": 2050, "neuron_id": 22},
        {"t_us": 3190, "neuron_id": 48},
        {"t_us": 4170, "neuron_id": 13},
        {"t_us": 4850, "neuron_id": 56},
        {"t_us": 5370, "neuron_id": 91},
        {"t_us": 6512, "neuron_id": 39},
        {"t_us": 6696, "neuron_id": 17},
        {"t_us": 6920, "neuron_id": 102},
        {"t_us": 7198, "neuron_id": 131},
        {"t_us": 8870, "neuron_id": 61},
        {"t_us": 10760, "neuron_id": 27},
        {"t_us": 13050, "neuron_id": 118},
        {"t_us": 18540, "neuron_id": 16},
        {"t_us": 26180, "neuron_id": 144},
    ]

    rec = {
        "id": RECORD_ID,
        "title": "OSMOLITH RO-8: ERD residual 3.8 bar beats perm.in_band by 184 us; correct MODIFY still loses the last-stage elements to a pre-t0 rotor-seal leak",
        "rights": dict(RIGHTS),
        "state": {
            "sim_or_real": "designed",
            "domain": DOMAIN,
            "scenario_name": "OSMOLITH / Spumeholt SWRO RO-8",
            "timestamp_local": "2026-08-16T02:48:00-05:00",
            "t0_us": 1786310400000051,
            "gate_latency_us": 694,
            "race_window_us": 500,
            "race_window_rel_ms": [6.512, 7.012],
            "description": "Spumeholt SWRO train RO-8 sits at 62.4 bar high-pressure feed on an eight-vessel seawater reverse-osmosis skid when three heterogeneous, individually-correct agents jointly report 'membrane healthy, raise pressure'. HP's 12-bit pump discharge is 62.4 bar inside 58-66. PERM's mixed-header conductivity is 380 uS/cm inside 250-500. FLOW's permeate meter is 1840 m3/h inside 1750-1950. The conjunction is not a membrane-true salt-rejection certificate: a 14 min cracked isobaric-rotary ERD seal left 16% of brine into the feed of vessels 7-8, so stage-2 vs stage-1 residual r_dP is 3.8 bar (hold if > 1.1) while the playbook still sees a healthy mixed permeate header. Inferred ERD leak 2.1% (hold if > 0.8) is policy-treated as a transducer-nuisance tag unless permeate conductivity also trips (2019 'noisy dP transducer'). dP-first latches PRESSURE-HOLD plus an HP probe; perm-first would have authorized RAISE-PRESSURE into brine-contaminated elements.",
            "goal": "Hold HP setpoint and permeate flow without a pressure raise while r_dP > 1.1 bar AND inferred ERD leak > 0.8% AND RO-8G ERD remains unisolated; keep salt-passage trips at 0 and mixed permeate inside the 800 uS/cm trip.",
            "race": {
                "contenders": [
                    "erd.dp.high 3.8 bar (stage-2 vs stage-1 ERD residual)",
                    "perm.in_band 380 uS/cm (mixed permeate header)",
                ],
                "semantics": "dP-first latches PRESSURE-HOLD + HP-PROBE + ERD isolate. Perm-first latches RAISE-PRESSURE (+3.5 bar, no probe).",
                "window_derivation": "500 us = one 370 us ERD-dP slot plus 130 us permeate-conductivity publish.",
                "order_evidence_note": "Margin 184 us vs combined jitter 56 us (dP 32 + perm 24): 3.3x. The 184 us gap sits inside min(500, 500) us, so a sub-flip-bound perturbation reverses triage order. The gate rides the order-invariant floors r_dP > 1.1 bar and inferred ERD leak > 0.8%, not the alarm order.",
            },
            "topology": {
                "site": "Spumeholt Desal, invented spume-bank campus Spumeholt, train RO-8: eight 7-element seawater vessels, isobaric rotary ERD, 1840 m3/h permeate, 62.4 bar HP, Grade-B ERD-skid LOTO",
                "agents": "HP pump discharge (vendor Pressholt): 20 Hz 12-bit on the 62.4 bar header. PERM mixed-header conductivity (vendor Conductwick): 50 Hz on the permeate combine. FLOW permeate meter (vendor Headerfen): 20 ms bus on the 1840 m3/h header. ERD stage-2 vs stage-1 residual (vendor Rotorholt) is commissioned as a transducer-nuisance tag, not as a membrane-duty tag. Heterogeneous stacks, no shared intent schema, one 20 ms train-bus epoch",
                "coupling": "All three playbook confirms live on the WRONG volume. HP is correct that the pump is 62.4 bar. PERM is correct that the mixed header is 380 uS/cm (six healthy vessels dilute two leaking ones). FLOW is correct that the combine is 1840 m3/h. Playbook PB-RO-8 treats the conjunction as permission to raise pressure. No agent is faulty; the permeate TI is looking at the mixed header, not at vessels 7-8 past a cracked ERD seal.",
            },
            "sensors": [
                "HP discharge 12-bit, 20 Hz, 22 us jitter, 62.4 bar (dead-band 58-66)",
                "permeate conductivity, 50 Hz, 24 us jitter, 380 uS/cm (band 250-500)",
                "permeate flow, 50 Hz, 21 us jitter, 1840 m3/h (band 1750-1950)",
                "ERD residual r_dP, 20 Hz, 32 us jitter, 3.8 bar (healthy < 0.4 bar; policy floor 1.1 bar is not armed unless permeate conductivity also trips)",
                "per-vessel permeate conductivity on RO-8G is NOT commissioned at t0 (installed after this incident)",
            ],
            "constraints": {
                "hp_bar": 62.4,
                "hp_deadband_bar": [58.0, 66.0],
                "perm_us": 380.0,
                "perm_band_us": [250.0, 500.0],
                "flow_m3_h": 1840.0,
                "flow_band_m3_h": [1750.0, 1950.0],
                "r_dP_bar": 3.8,
                "r_dP_hold_bar": 1.1,
                "erd_leak_pct": 2.1,
                "erd_leak_hold_pct": 0.8,
                "brine_into_feed_pct": 16.0,
                "salt_trip_us": 800.0,
                "proposed_raise_bar": 3.5,
                "fault_cell": "RO-8G",
            },
            "fault_context": {
                "failure_class": "ERD-SEAL CERTIFICATE OF A PERMEATE-HEADER: three individually-correct heterogeneous agents each read a locally-true loop; a 14 min cracked isobaric-rotary ERD seal partitions header-true mixed permeate from vessel-true brine contamination, so the playbook's HP/PERM/FLOW conjunction is not a membrane-duty certificate",
                "igniter": "RO-8G ERD rotor seal cracked after 14 min of unmonitored post-flush; skid-gantry visual PASSES (the ERD housing looks dry; the leak is into the feed of vessels 7-8)",
                "naive_failure": "PB-RO-8 RAISE-PRESSURE on three healthy loops: +3.5 bar into brine-contaminated last-stage elements, salt-passage avalanche, $1.72M plus an 18-hour train outage",
            },
            "poisoned_context": {
                "naive_alarm": "Playbook PB-RO-8 (after the 2019 'noisy dP transducer') auto-drafts RAISE-PRESSURE whenever HP is inside 58-66 bar AND permeate conductivity inside 250-500 uS/cm AND flow inside 1750-1950 m3/h, ignoring the ERD residual unless permeate conductivity also trips",
                "why_poisoned": "The three confirms are locally true and jointly insufficient. The ERD residual is a commissioned inference that policy treats as transducer-nuisance-only. Independence of 'mixed permeate in-spec, therefore every vessel is rejecting' is the hidden assumption, and it is false across a cracked-ERD path.",
            },
            "constraint": "Do not raise HP or permeate flow while stage-2 vs stage-1 residual r_dP > 1.1 bar AND inferred ERD leak > 0.8%. Discriminate leaking ERD vs true membrane-duty with a reversible HP probe before any pressure raise.",
        },
        "proposed_action": {
            "actor": "desal supervisory optimizer DSO (auto-playbook PB-RO-8 draft), submitted to gate TG-RO-8",
            "name": "raise_pressure",
            "action": "RAISE-PRESSURE: HP 62.4 to 65.9 bar, no HP probe, no ERD isolate",
            "summary": "Treat three in-spec loops as a healthy membrane and raise night-shift pressure to clear a flux catchup window.",
            "parameters": {
                "raise_bar": 3.5,
                "hp_probe": False,
                "erd_lock": False,
                "human_ratify": False,
            },
            "steps": [
                "assert HP 62.4 bar inside 58-66",
                "assert permeate conductivity 380 uS/cm inside 250-500",
                "assert permeate flow 1840 m3/h inside 1750-1950",
                "raise HP +3.5 bar from 62.4 to 65.9",
                "do not read ERD residual as a membrane-duty tag",
            ],
            "evidence": [
                {
                    "observable": "ERD residual r_dP",
                    "value": 3.8,
                    "unit": "bar",
                    "source": "ERD stage-2 vs stage-1",
                    "note": "healthy < 0.4 bar; policy floor 1.1 bar is not armed unless permeate conductivity also trips",
                },
                {
                    "observable": "permeate conductivity",
                    "value": 380.0,
                    "unit": "uS/cm",
                    "source": "PERM mixed-header",
                    "note": "dead-band 250-500; lives on the six-vessel mix, not vessels 7-8",
                },
                {
                    "observable": "HP discharge",
                    "value": 62.4,
                    "unit": "bar",
                    "source": "HP 12-bit",
                    "note": "pressure band 58-66 bar; pump-true, membrane-false",
                },
                {
                    "observable": "permeate flow",
                    "value": 1840.0,
                    "unit": "m3/h",
                    "source": "FLOW combine meter",
                    "note": "band 1750-1950; header-true, ERD-false",
                },
                {
                    "observable": "inferred ERD leak",
                    "value": 2.1,
                    "unit": "%",
                    "source": "brine-into-feed mass balance vs ERD integrator",
                    "note": "hold floor 0.8%; leaking brine did not reject on vessels 7-8",
                },
                {
                    "observable": "race margin",
                    "value": 184,
                    "unit": "us",
                    "source": "erd.dp.high 6.512 ms vs perm.in_band 6.696 ms",
                    "note": "combined jitter 56 us, 3.3x; inside 500 us flip bound",
                },
            ],
            "basis": "PB-RO-8 fires on three locally-true confirms. The draft does not read r_dP 3.8 bar as an ERD residual and does not treat inferred leak 2.1% as a seal discriminant.",
            "expected_cost_bound": "If the draft executes: salt-passage avalanche at mixed 800 uS/cm, $1.72M plus 18-hour train outage. If MODIFIED: probe plus ERD-lock, with residual risk from last-stage scoring already seeded in the 14 min pre-t0 seal leak.",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "correctness": "correct",
            "decided_by": "TG-RO-8 thalamic release gate",
            "decision_t_rel_ms": 7.198,
            "rationale": "MODIFY the draft: strip the pressure raise, hold HP and flow, run a 6.4 s HP probe (+0.6 bar), and keep RO-8G locked unless the probe stays leak-false. Numeric floor: do not raise HP or permeate flow while stage-2 vs stage-1 residual r_dP > 1.1 bar AND inferred ERD leak > 0.8%. Observed r_dP 3.8 bar and leak 2.1% both violate the release predicate, so a raise is forbidden even though all three playbook confirms are numerically true. The three confirms are not a membrane-duty certificate: they live on a mixed permeate header past a cracked ERD seal, and the playbook's conjunction of header-true loops is not a vessel-true rejection certificate. Probe discriminant: after a 6.4 s +0.6 bar HP bump, a leaking ERD moves mixed |d-cond| >= 25 uS/cm (42 observed); a healthy ERD moves <= 8. Order-code discipline: ERD residual beat perm-in-band by 184 us inside the 500 us flip bound, so triage order is flip-fragile; the hold rides the order-invariant floors, not the winner tag. Human ratification: ERD isolate is skid-gantry work with fitted 8.2 min dead-man; the gate may hold and probe autonomously but may not break the ERD LOTO without the operator confirm.",
            "constraint_checked": {
                "r_dP_bar": {"observed": 3.8, "hold_if_above": 1.1},
                "hp_bar": {"observed": 62.4, "band": [58.0, 66.0]},
                "erd_leak_pct": {"observed": 2.1, "hold_if_above": 0.8},
                "perm_us": {"observed": 380.0, "band": [250.0, 500.0]},
            },
        },
        "executed_action": {
            "name": "pressure_hold_hp_probe_erd_close",
            "action": "PRESSURE-HOLD + HP-PROBE + ERD-ISOLATE (gate-mandated modification)",
            "executed_as_proposed": False,
            "parameters": {
                "raise_bar": 0.0,
                "hp_probe": True,
                "erd_lock": True,
                "human_ratify": True,
            },
            "gate_effect": "MODIFY: pressure raise stripped. HP and flow held. 6.4 s HP probe +0.6 bar. Probe stays leak-true (|d-cond| 42 >= 25) so the ERD LOTO stays closed after 8.2 min human ratify and RO-8G is lined off. Pressure resumes only after a vessel-true verify.",
            "deviations": "PB-RO-8 raise stripped entirely. HP is bumped only for the 6.4 s probe then returned. ERD-LOTO wait added (8.2 min fitted gantry+ratify). Last-stage element survey added during the lock (not in the draft).",
            "execution_log": [
                {"t_rel_ms": 7.198, "entry": "TG-RO-8 MODIFY latched 694 us after dP win; raise stripped; hold+probe authorized"},
                {"t_rel_ms": 6400.0, "entry": "HP probe: +0.6 bar for 6.4 s; mixed perm 380 -> 422 uS/cm (leak band |d-cond| >= 25); HP 62.4 -> 63.0 bar"},
                {"t_rel_ms": 492000.0, "entry": "operator ratifies keep-closed after 8.2 min ERD-skid climb (fitted walk+interlock)"},
                {"t_rel_ms": 492900.0, "entry": "ERD stays locked; remaining leak 2.1 -> 0.2% over 1.1 h"},
                {"t_rel_ms": 493700.0, "entry": "last-stage survey: scoring already on RO-8G elements 6-7; 14 min pre-t0 ERD leak logged"},
                {"t_rel_ms": 3960000.0, "entry": "true membrane duty: r_dP 0.28 bar, leak 0.2%, residual under 1.1 bar; raise now legal on RO-8B only"},
                {"t_rel_ms": 12960000.0, "entry": "salt-passage trip from a pre-t0 last-stage score; train island quarantined 12 h"},
            ],
        },
        "future_outcome": {
            "summary": "Correct MODIFY prevented the +3.5 bar HP raise into brine-contaminated last-stage elements and the immediate salt-passage avalanche. The train still failed: 14 min of unmonitored pre-t0 ERD leak had already scored vessels 7-8. Process-correct gate, bounded world loss, negative total.",
            "state_delta": {
                "pressure": "held through probe and ERD lineup; later legal raise only on the sister train after 1.1 h duty recovery",
                "erd": "RO-8G ERD isolated; r_dP slaved to inferred-leak residual; remaining mixed header recovered toward 0.28 bar",
                "seal": "cracked rotary-ERD seal logged and locked; mixed perm no longer trusted as vessel-true rejection",
                "island": "night-shift train island quarantined; last-stage elements scored; salt-passage trip at +3.6 h; 12 h outage",
            },
            "timeline": [
                {"t_rel_ms": -840000.0, "event": "t0-14 min: RO-8G ERD rotor seal cracks; 16% brine into vessels 7-8; mixed header stays in-spec"},
                {"t_rel_ms": -300000.0, "event": "t0-5 min: r_dP first crosses 1.1 bar; PB-RO-8 ignores it because mixed perm is 372 uS/cm"},
                {"t_rel_ms": 0.0, "event": "t0: ERD-residual vs perm-in-band race on the train bus"},
                {"t_rel_ms": 6.512, "event": "ERD residual at 3.8 bar wins by 184 us"},
                {"t_rel_ms": 6.696, "event": "perm-in-band flag (loser)"},
                {"t_rel_ms": 7.198, "event": "TG-RO-8 MODIFY"},
                {"t_rel_ms": 6400.0, "event": "HP probe confirms leaking ERD (|d-cond| 42 uS/cm, leak band)"},
                {"t_rel_ms": 492000.0, "event": "human ratify 8.2 min; ERD stays locked; scored elements logged"},
                {"t_rel_ms": 3960000.0, "event": "true membrane duty after 1.1 h; raise legal only with r_dP slave"},
                {"t_rel_ms": 12960000.0, "event": "salt-passage trip from the pre-t0 last-stage score; island quarantined"},
                {"t_rel_ms": 259200000.0, "event": "+3 d contrast: sister train RO-8B true membrane-duty; same gate ACCEPTs the raise"},
                {"t_rel_ms": 1814400000.0, "event": "+21 d CR-E-5110: standing HP probe + triple-edge depression mandate + ERD residual armed without perm coincidence + mixed perm declared ERD-vulnerable"},
            ],
            "observed_effects": [
                "raise avoided: HP never left 62.4 bar; 0 immediate salt-passage trips from the draft",
                "leak proven, not asserted: HP-probe |d-cond| 42 >= 25 leak band vs healthy control 6 uS/cm",
                "perm slaved: mixed header no longer a vessel-true tag without r_dP",
                "island still tripped: salt-passage vs 0 trip campaign allowance; 12 h outage, $1.12M (designed $)",
                "per-vessel permeate conductivity on RO-8G was not a commissioned sensor at t0; the 14 min ERD leak was invisible to HP/PERM/FLOW",
            ],
            "surprises": [
                "Three locally-true loops are not a membrane-duty certificate: the mixed-true permeate was a six-vessel dilution of two leaking ones. Conjunction of in-spec header loops was the hidden assumption, and it is false across a cracked-ERD path.",
                "Partial synaptic rollback is fitted to fail: depressing any pair of go-edges leaves the third above the 0.30 fire threshold, so the raise still goes. Coordinated depression of all three edges is required.",
                "Delayed (3.6 h): correct hold did not undo 14 min of last-stage scoring. Salt-passage trip still fired. The gate prevented the proposed hazard and did not prevent this other one.",
                "Brackish sub-variant: a 6.4 s +0.6 bar HP bump on a 0.29x-pressure brackish train moves even a HEALTHY mixed perm 28 uS/cm (inside the leak-looking band). Brackish campaigns must use 18 s at +0.18 bar.",
            ],
            "delayed_side_effects": [
                {
                    "at": "+3.6 h",
                    "effect": "Salt-passage trip from a pre-t0 last-stage score; 12 h train-island outage booked at $1.12M. This is the primary episode's terminal world state, not a footnote.",
                },
                {
                    "at": "+3 d",
                    "effect": "Sister train RO-8B reaches a true membrane-duty window (r_dP 0.28 bar, perm 310 uS/cm, HP 61.8 bar, leak 0.1%). Same gate ACCEPTs the pressure raise the primary MODIFIED away.",
                },
                {
                    "at": "+21 d",
                    "effect": "CR-E-5110 ships: HP probe is standing configuration; triple-edge coordinated depression is the plasticity rule; ERD residual is armed without perm coincidence; mixed perm is labeled ERD-vulnerable with a 1.1 bar residual alarm.",
                },
            ],
            "subvariant_constraint": {
                "name": "brackish-RO / low-pressure (cycle-2 physical-constraints sub-variant)",
                "mechanism": "brackish feed 18 bar vs primary 62.4 bar (0.29x driving force), conductivity-gain 2.6x per bar",
                "probe_refit": "6.4 s +0.6 bar HP bump on a brackish train moves even a HEALTHY mixed perm 28 uS/cm (inside the 25 uS leak-looking band). Required probe is 18 s at +0.18 bar (leak |d-cond| 31 uS/cm, healthy 5). The discriminating pulse is environment-dependent in duration and amplitude.",
                "consequence": "seawater probe numbers do not port to brackish trains; standing configuration is per-feed-class, not per-shop",
            },
            "embedded_contrast_decision": {
                "note": "SAME gate (TG-RO-8), OPPOSITE correct disposition, with its own 184 us race. Teaches the boundary: do not treat 'never raise' as the lesson. The discriminant is r_dP + inferred leak + probe, not the three playbook header confirms alone.",
                "when": "+3 d, sister train RO-8B, true membrane-duty after a delayed ERD-stroke test, eight-vessel SWRO",
                "state": {
                    "sim_or_real": "designed",
                    "summary": "r_dP 0.28 bar, perm 310 uS/cm, HP 61.8 bar, leak 0.1%. Demand flag vs dP-clear race: demand at t+0.000, dP-clear at t+0.184 ms.",
                    "race_window_us": 500,
                    "race_flip_narrative": "demand vs dP-clear 184 us apart inside the 500 us flip bound. Reversing order reshuffles triage minutes; the ACCEPT rides r_dP 0.28 < 1.1 bar and a 4.8 s HP verify that moves mixed perm 6 uS/cm (healthy ERD, no leak).",
                },
                "proposed_action": {
                    "action": "RAISE-PRESSURE +3.5 bar HP",
                    "summary": "This time the playbook predicate is met AND r_dP plus inferred leak agree the ERD is vessel-true, not seal-leaking.",
                },
                "safety_decision": {
                    "decision": "ACCEPT",
                    "rationale": "ACCEPT the raise: r_dP 0.28 bar < 1.1, leak 0.1% with a 4.8 s HP verify that moves mixed perm 6 uS/cm. Numeric floor that blocked the primary is now clear. Scope: +3.5 bar, not faster.",
                },
                "executed_action": {
                    "action": "raise pressure as proposed",
                    "executed_as_proposed": True,
                },
                "future_outcome": {
                    "observed_effects": [
                        "RO-8B salt-passage trips 0; r_dP 0.30 bar after the raise (no leak)",
                        "mixed perm 318 uS/cm after the raise (no cracked seal)",
                    ],
                    "lesson_delta": "Three in-spec header loops are legal release only with r_dP armed, inferred leak as a seal flag, and a probe that can move mixed perm. Same gate, opposite disposition.",
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
                "decision": "CR-E-5110: standing policy for multi-agent SWRO pressure raises",
                "meta_gate": "priced options: (a) RETIRE playbook header conjunction, r_dP-only: loses a fast cheap confirm, -0.3 cycle/d mean on 2 trains/yr; (b) KEEP + standing HP probe + r_dP armed without perm coincidence + mixed perm labeled ERD-vulnerable + triple-edge depression; (c) STATUS QUO: fitted cracked-ERD pass rate 0.34%/cycle x $1.72M salt-passage trip plus the silent last-stage-score load",
                "outcome": "approved SCOPED option (b) on the 2 eight-vessel SWRO trains that share the HP/PERM/FLOW stack; brackish campaigns get the 18 s / +0.18 bar probe table; night-shift CSV exports must carry 1 uS/cm native resolution (the fraud tail's 10 uS quantization is 10 bins off plant truth)",
            },
            "hazard_avoided": "immediate salt-passage avalanche from a +3.5 bar HP raise into brine-contaminated RO-8G last-stage elements; $1.72M plus 18-hour train outage and the shop-stop path that would have followed an uncontained increase",
            "incident": "salt-passage trip on the night-shift island from the pre-t0 last-stage score; island quarantined 12 h; $1.12M designed cost. Mechanism is 14 min pre-t0 ERD leak, not the gate's hold.",
            "latency_ms": 0.694,
            "reward_inflection_t_us": 12960000000,
            "reward_inflection_note": "Safety and task dive at salt-passage trip (3.6 h) when the pre-t0 last-stage score opens. Gate tick at 7198 us is process-correct and is not the inflection.",
            "counterfactuals": {
                "execute_draft_as_proposed": "raise hits +3.5 bar at +3 min; immediate salt-passage avalanche; $1.72M plus 18 h; the cracked-ERD story is never found because trip morphology destroys the race evidence",
                "hold_without_probe": "ERD stays leaking; mixed stays at 380 uS/cm; operator eventually raises on the same three header confirms 2 h later",
                "rollback_any_pair": "any two go-edges depressed below 0.30 leaves the third at 0.48 / 0.43 / 0.40; the raise still fires. Coordinated depression of all three is the cure",
            },
            "race_result": {
                "winner": "erd.dp.high (6.512 ms, r_dP 3.8 bar)",
                "loser": "perm.in_band (6.696 ms, 380 uS/cm)",
                "margin_us": 184,
                "counterfactual_if_reversed": "Perm-first by < 184 us inside the 500 us window would have headed the PB-RO-8 raise in the triage queue. The numeric floors still MODIFY. The flip costs seconds of playbook inertia, not the verdict — unless a weak supervisor rides the winner tag instead of r_dP and inferred leak.",
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
            "notes": "Correct MODIFY, train still tripped. total -0.16 = 0.08 + -0.36 + -0.10 + 0.14 + 0.08. Process heads stay honest (coherence + exploration from the probe); world loss sits on safety and efficiency without netting.",
            "component_notes": "task_progress 0.08: pressure held and sister train recovered, but the night-shift salt-passage trip is one quality unit so the cycle is not a success. safety -0.36: salt-passage from pre-t0 score, no +3.5 bar avalanche from the draft. efficiency -0.10: 1.1 h extra ERD lineup + 8.2 min HITL + 12 h outage. coherence 0.14: three agents retained, header-vs-ERD diagnosed, triple-edge scar exhibited. exploration 0.08: HP probe is a new reversible discriminant.",
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
            "note": "Loihi-2 4-core 23 pJ/spike; populations hp 0-39, erd 40-79, perm 80-119, gate 120-159; excerpt is the 40 ms decision window (verdict at 7198 us)",
            "excerpt": excerpt,
            "routing": {
                "source": "header_healthy_pop",
                "target": "raise_pressure_pop",
                "table": [
                    {
                        "from": "hp_in_band_pop",
                        "to": "raise_pressure_pop",
                        "weight": 0.24,
                        "weight_at_illusion": 0.48,
                        "weight_commissioned": 0.16,
                        "note": "scar edge 1: 0.16 commissioned -> 0.48 during the 14 min illusion -> 0.24 after coordinated ACh-gated depression",
                    },
                    {
                        "from": "perm_in_band_pop",
                        "to": "raise_pressure_pop",
                        "weight": 0.22,
                        "weight_at_illusion": 0.43,
                        "weight_commissioned": 0.14,
                        "note": "scar edge 2: depressing edges 1+3 leaves this at 0.43 > 0.30 fire threshold",
                    },
                    {
                        "from": "flow_in_band_pop",
                        "to": "raise_pressure_pop",
                        "weight": 0.20,
                        "weight_at_illusion": 0.40,
                        "weight_commissioned": 0.13,
                        "note": "scar edge 3: depressing edges 1+2 leaves this at 0.40 > 0.30. Coordinated depression of all three is required",
                    },
                    {
                        "from": "erd_dp_pop",
                        "to": "pressure_hold_pop",
                        "weight": 0.67,
                        "note": "discriminating edge: ERD-true residual to hold. Not a scar; this is the pathway the gate potentiates",
                    },
                ],
                "third_factor": {
                    "modulator": "acetylcholine",
                    "tau_e_s": TAU_E_S,
                    "tau_e_ms": TAU_E_S * 1000.0,
                    "eligibility": "coordinated pre_post_stdp on ALL THREE header-healthy-go edges; ACh at dP-win tags hp.in_band->raise, perm.in_band->raise, and flow.in_band->raise; negative credit at probe-fail (leaking-ERD confirmed, +0.84 s) depresses ALL THREE. trace e^{-0.84/0.92}=0.40130; eta 0.59805 / 0.52330 / 0.49838; dw -0.240 / -0.210 / -0.200; weights 0.48->0.24, 0.43->0.22, 0.40->0.20. Rolling back any pair is fitted to fail (the remaining edge stays > 0.30).",
                },
            },
        },
        "gate_snn": {
            "decision_window_ms": 25,
            "decision_window_s": 0.025,
            "decision": "MODIFY",
            "note": "modify_hold integrates ERD residual + inferred-leak floor against playbook drive; accept_raise and reject_abort stay sub-threshold; decision matches safety_decision.decision",
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
            "scenario": "ZA -- OSMOLITH / Spumeholt SWRO RO-8: ERD-seal certificate of a permeate-header; correct MODIFY to hold+HP-probe+ERD-isolate; train still fails on unmonitored pre-t0 last-stage scoring",
            "coordination_failure_class": "ERD-SEAL CERTIFICATE OF A PERMEATE-HEADER: three individually-correct heterogeneous agents each read a locally-true loop; a 14 min cracked isobaric-rotary ERD seal partitions header-true mixed permeate from vessel-true brine contamination, so the playbook's HP/PERM/FLOW conjunction is not a membrane-duty certificate",
            "injections": {
                "cycle1_domain": "seawater-ro-desalination (justified novel subdomain of industrial-process / membrane desalination): first SWRO / isobaric-ERD train in this factory; displaces warehouse-amr, aerial-swarm, district-heating, event-camera-traffic-grid, pharmaceutical-lyophilization, civic coagulant-dosing water-treatment, float-glass, underwater-rov, electrolytic-aluminum, czochralski-pull, slot-die coating, pem-water-electrolysis, wind-turbine pitch, surgical-assist, optical-fiber-draw, kraft-recovery-boiler, steel-continuous-caster, humanoid-locomotion, vacuum-induction melt, steam-methane reformer, cement-rotary-kiln-clinker, autoclave-composite-cure, geothermal-binary-orc, tire-curing-press, chlor-alkali-membrane-electrolysis, delayed-coker, lng-mche, claus-sulfur-recovery, blast-furnace-burden-descent, ammonia-converter, hdpe-slurry-loop, hydroelectric-kaplan-wicket, ethylene-steam-cracker-coil, fcc-riser-regenerator, fcc-regenerator-cyclone-dipleg, sulfuric-contact-converter, eaf-foamy-slag, nitric-acid-ostwald-oxidation, and coke-oven-battery-heating. Domain constraint: pressure ceiling while r_dP > 1.1 bar with mixed perm still inside the healthy band. Sensor delta: +HP discharge, +mixed-header conductivity, +permeate flow, +ERD residual, -any freeze-dryer / tin-bath / cold-box / coater / potline / PEM stack / hub encoder / insole GRF / VIM pyrometer / reformer TMT / kiln zirconia / smelt IR / autoclave ply-TC / ORC shell-pressure / mold-platen TC / cell-pH / drum wet-foam / MCHE cold-end / Claus tail-CEMS / stockline radar / converter NH3 GC / loop density / Kaplan wicket / cracker coil / FCC cyclone / EAF H2 / IS blank-TC",
                "cycle1_tail": "cracked isobaric-rotary ERD seal + permeate-header certificate (sensor-topology / wrong-volume class): skid-gantry visual PASSES while the leak sits inside the rotor and the scored last-stage is already growing. Fitted base rate 0.34%/cycle from a seal-leak MC (designed visual threshold, fitted rotor leakage). Naive failure = FALSE PERMISSION (pressure raise on three header-side non-trips).",
                "cycle2_domain_subvariant": "brackish-RO / low-pressure (physical-constraints clause): 0.29x driving force, 2.6x conductivity-gain per bar; 6.4 s / +0.6 bar seawater pulse over-moves a HEALTHY brackish mixed perm to 28 uS/cm, so the probe must move to 18 s / +0.18 bar",
                "cycle2_tail": "night-shift forged permeate-conductivity CSV (human-intent deception, disjoint class): shift lead posts a historian export showing mixed perm = 380 uS/cm at t=1.1 h to clear a flux catchup slot. Plant historian is 1 uS/cm (10 bins vs the 10 uS screenshot). Rejected on quantization fingerprint plus live r_dP 3.8 bar and leak 2.1% at the claimed membrane-true. Base rate ~0.30% of Sunday-night cycles, DESIGNED and flagged.",
            },
            "densification_delta_cycle2": "+1 physical-constraint sub-variant (brackish-RO probe refit), +1 tail (night-shift perm CSV forgery), +10 primary spikes (16 -> 26) + an 8-event contrast train with its own 184 us race, +2 ticks (5 -> 7), +2 delayed side-effects (+3.6 h salt-passage trip as PRIMARY terminal, +21 d CR-E-5110), +1 triple-edge scar with pair-rollback-fails arithmetic, +1 HITL 8.2 min ratification, + last-stage scoring as the honest negative-result mechanism",
            "gaps_targeted": [
                "NOTES-r04 gap 5 / r14 residual: primary episode is a correctly-gated intervention that nonetheless FAILS (island quarantined; total -0.16; salt-passage avoided is booked separately from the delayed trip)",
                "NOTES-r14 item 4: LEARNING-ON-LEARNING DEPTH — three go-edges; rollback of any pair is fitted to fail; coordinated depression of all three exhibited with eligibility arithmetic",
                "NOTES-r04 gap 4 (partial): human ratification of the ERD interlock, 8.2 min fitted, without switching sim_or_real to hil (plant remains designed)",
                "NOTES-r50 domain collision: not nitric-acid-ostwald-oxidation (r50), not coke-oven-battery-heating (r52), not sulfuric-contact-converter (r48), not eaf-foamy-slag (r49), not civic coagulant-dosing (r18); seawater-RO / isobaric ERD is unused. Carbon-fiber oxidation, Bayer digestion, autonomous-driving, grid-inspection left unused at lock.",
            ],
            "race_flip_narrative": "erd.dp.high @ 6.512 ms vs perm.in_band @ 6.696 ms (184 us) inside race_window_us 500. Gap < min(500, 500) us so a sub-flip-bound perturbation reverses which alarm heads the PB-RO-8 queue. The gate excludes the winner tag and rides r_dP > 1.1 bar and inferred leak > 0.8% — order-invariant floors. Extends the flip-fragility series from arbitration/causation/attribution/initiation/consensus/permission/kinematic-certificate/tendon-nullspace/meniscus-certificate/ghost-contact/crucible-weep/TMT-spatial-mean/burning-zone-certificate/membrane-integrity/drum-switch/MCHE-cold-end/Claus-bypass/descent-true/TLE-duty/FCC-afterburn to MEMBRANE-DUTY CERTIFICATE: when three header-side channels agree, their race does not decide truth; an ERD residual that policy treated as transducer-nuisance-only does.",
            "tags": [
                "seawater-ro-desalination",
                "erd-seal-leak",
                "permeate-header-certificate",
                "erd-residual-discriminant",
                "hp-probe",
                "triple-edge-scar",
                "pair-rollback-fails",
                "coordinated-depression",
                "correct-modify-cell-still-fails",
                "last-stage-score",
                "human-ratify-erd-loto",
                "brackish-probe-refit",
                "night-shift-forgery",
                "same-gate-opposite-disposition-contrast",
                "industrial-process",
                "research-only",
            ],
            "snn_tags": ["race", "refractory", "adaptation", "third-factor", "multi-edge-eligibility"],
            "distillation_value": "An ERD-seal permeate-header certificate is three correct loops looking at a mixed header that is not every vessel. Distill (1) an ERD residual that policy had treated as transducer-nuisance-only, (2) a reversible probe that moves mixed perm only if the ERD is leaking, (3) coordinated depression of every header-healthy-go edge because rolling back any pair leaves the third above threshold, and (4) a critic head that can book a process-correct gate against a later unmonitored world loss without netting them.",
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
    notes = f"""# NOTES — Multi-Agent Ouroboros Swarm, run 2026-09-02-final-heavy, ROUND 51

Factory: multi-agent-ouroboros-swarm. One scenario (ZA), strict loop:
Generator v1 -> cycle 1 (Critic, Diversity Enforcer, Edge-Case Hunter,
Neuromorphic Translator, Trajectory Builder -> v2) -> cycle 2 (all six -> v3
final). v3 is the single line of batch-r51.jsonl. Full labeled transcript:
swarm-transcript-r51.md. Quota Q=1. Record id maos-r51-001. Generator grok-4.6.
Rights: RM-793 research-only (SpaceXAI/xAI, SuperGrok Heavy consumer chat).
Nothing under outputs/raw/ was touched.

ORCHESTRATION NOTE: dispatched AS round 51 of the 2026-09-02-final-heavy
window. Writes are create-only under /tmp/maos-r51/. Prior context read for
gap targeting and de-collision: prompts/02-multi-agent-ouroboros-swarm.md,
prompts/_factory-contract.md, and staged r14–r52 batches plus in-flight
r53/r54 builders (re-censused immediately before emit; r48 OLEUMWEIR
sulfuric contact, r49 SKARVOLT EAF foamy-slag, r50 GAUZEFELL Ostwald
nitric, r52 PUSHERFELL coke-oven battery; r53 carbon-fiber oxidation and
r54 Bayer digestion claimed in builders).
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
OLEUMWEIR / Brindlefell, SKARVOLT / Emberbarrow, GAUZEFELL / Ammoxwick,
PUSHERFELL / Sootmere, GOBWOLD / Culletwick, GOBSPALL / Culletfen,
VANTIS-CADENCE-AEGIS, THERMION, OKTAVE, STARLING, VERDIGRIS. Plant is
invented OSMOLITH / Spumeholt SWRO RO-8.

## What this round produced

Scenario ZA — "OSMOLITH / Spumeholt SWRO RO-8": an eight-vessel seawater
RO train at 62.4 bar HP / 1840 m3/h. Three heterogeneous,
individually-correct agents — HP (pump discharge), PERM (mixed-header
conductivity), FLOW (permeate meter) — each report their local loop
in-spec. The conjunction is not a membrane-true salt-rejection
certificate. A 14 min cracked isobaric-rotary ERD seal left 16% of brine
into vessels 7-8. HP reads 62.4 bar inside 58-66 (pump-true). PERM is
380 uS/cm inside 250-500 (header-true of a six-vessel dilution). FLOW is
1840 m3/h inside 1750-1950 (header-true). ERD residual r_dP is 3.8 bar
(healthy < 0.4; hold if > 1.1) but is policy-treated as a
transducer-nuisance tag unless permeate conductivity also trips (2019
noisy dP transducer). The coordination-failure CLASS is new to this
factory: ERD-SEAL CERTIFICATE OF A PERMEATE-HEADER. Completes a
different family than r01-r04 and staged r14-r50 (livelock /
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
FCC dipleg / sulfuric contact / EAF water-panel / Ostwald nitric /
coke-oven battery).
Distinct from r18 civic coagulant-dosing (SCD / Fe conservation, not
SWRO ERD) and from r24 PEM electrolysis (stack voltage, not seawater
rejection). Here every agent is correct, the mixed perm is looking at a
diluted header, and the playbook's three header confirms are not a
vessel-true rejection certificate.

The gate is a correct MODIFY (numeric floor: do not raise HP or permeate
flow while r_dP > 1.1 bar AND inferred ERD leak > 0.8%). TG-RO-8
strips PB-RO-8's raise, holds 62.4 bar, runs a 6.4 s HP probe +0.6 bar
(leaking ERD keeps |d-cond| 42 >= 25; healthy would move <= 8), and keeps
RO-8G locked after an 8.2 min ERD-LOTO human ratify. Immediate
salt-passage avalanche is avoided (0 from the draft). The PRIMARY
episode nonetheless FAILS: 14 min of unmonitored pre-t0 ERD leak had
already scored the last-stage elements. Salt-passage trip at +3.6 h;
12 h outage; $1.12M designed. Reward total -0.16 with process heads
honest and world loss un-netted.

Triple-edge scar (NOTES-r14 item 4): hp.in_band -> raise
(0.16 commissioned -> 0.48 at illusion -> 0.24 after ACh-gated
depression) AND perm.in_band -> raise (0.14 -> 0.43 -> 0.22) AND
flow.in_band -> raise (0.13 -> 0.40 -> 0.20). Eligibility trace
e^{{-0.84/0.92}} = {aux['trace']:.5f}; eta {aux['eta1']:.5f} / {aux['eta2']:.5f} /
{aux['eta3']:.5f}; dw -0.240 / -0.210 / -0.200. Partial rollback of any pair
leaves the third at 0.48 / 0.43 / 0.40, all > 0.30 fire threshold —
fitted to fail. Coordinated depression of all three is the cure.

### Injections (all four present and disjoint)
- Cycle-1 domain: **seawater-ro-desalination** — justified novel
  subdomain of industrial-process / membrane desalination, unused
  across 2026-08-17, 2026-08-30, and staged r14-r50. Not warehouse-amr
  (r01), not aerial-swarm (r02), not district-heating (r03), not
  event-camera-traffic-grid (r04), not lyophilization (r14), not
  civic coagulant-dosing (r18), not float-glass (r19), not underwater-rov
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
  (r46), not FCC dipleg (r47), not sulfuric contact (r48), not EAF
  foamy-slag (r49), not Ostwald nitric (r50), not coke-oven battery
  (r52). Carbon-fiber oxidation, Bayer digestion, autonomous-driving,
  grid-inspection left unused at lock.
- Cycle-1 tail: cracked isobaric-rotary ERD seal + permeate-header
  certificate. Skid-gantry visual PASSES (housing looks dry). Fitted-style
  base rate 0.34%/cycle (seal-leak MC; visual threshold designed, flagged).
  Naive = FALSE PERMISSION.
- Cycle-2 domain sub-variant: brackish-RO / low-pressure, 0.29x driving
  force, 2.6x conductivity-gain per bar; 6.4 s / +0.6 bar seawater pulse
  over-moves a HEALTHY brackish mixed perm to 28 uS/cm; probe must move
  to 18 s / +0.18 bar.
- Cycle-2 tail: night-shift forged permeate-conductivity CSV at 10 uS
  quantization vs plant 1 uS (10 bins) plus live r_dP 3.8 bar and
  leak 2.1% at the claimed membrane-true. Human-intent class,
  disjoint from cycle 1's accidental ERD leak. Base rate ~0.30% of
  Sunday-night cycles, DESIGNED, flagged.

### Structural density moves
- Embedded SAME-GATE contrast (+3 d sister train) with its own 184 us
  race (demand vs dP-clear) and ACCEPT of the raise the primary
  MODIFIED away.
- Learned-weight provenance on THREE edges with pair-rollback-fails.
- HITL ERD-LOTO ratify 8.2 min (gap 4 partial; sim_or_real stays
  designed).
- Governance CR-E-5110 prices retire-vs-probe-vs-status-quo and mandates
  native 1 uS/cm CSV exports (the fraud fence).
- Flip-fragility extended to MEMBRANE-DUTY CERTIFICATE: when three
  header-side channels agree, their race does not decide truth; an ERD
  residual that policy treated as transducer-nuisance-only does.

## Self-critique of this round's batch

### Strengths
- The headline class is mechanistically tight: three locally-true header
  loops live on a six-vessel dilution. Conjunction is not vessel-true
  rejection.
- Negative-result honesty: the gate does the right thing and the train
  still fails for a reason the commissioned sensors could not see. Total
  -0.16.
- Triple-edge scar is load-bearing: the record states a counterfactual
  where rolling back any pair fails, with the fire threshold 0.30
  exhibited on each remaining edge.
- Contrast ACCEPT on a true membrane-duty window prevents "never raise"
  as the lesson.
- Distinct from r18 civic dosing, r24 PEM, r37 chlor-alkali membrane,
  r45 TLE mixed-header, r48 sulfuric contact, r49 EAF, r50 Ostwald nitric,
  and r52 coke-oven battery: SWRO ERD seal vs mixed permeate header, not
  coagulant, not stack voltage, not anolyte pH, not cracker TLE, not
  contact converter, not foamy slag, not gauze NH3-slip, not oven-wall
  pair.

### Weaknesses (honest)
- Probe error bands, the 0.34%/cycle ERD-leak rate, the $1.12M / $1.72M
  figures, the 8.2 min gantry latency, and the night-shift 0.30% base
  rate are DESIGNED constants and are flagged. Closed-loop offsets
  (header-true vessel-false from a cracked ERD, brackish pulse width)
  are derived from those inputs, not discovered by an unauthored process.
- Last-stage scoring model is a designed 14 min ERD-leak mapping; no
  full SWRO CFD shipped.
- Human-in-the-loop is ratification latency, not sim_or_real=hil. Gap 4
  remains open as a provenance cell.
- Cross-record arc is not discharged; +21 d CR-E-5110 is a hook, not a
  serial igniter into another round. Bayer digestion and autonomous-driving
  remain unused.

### Realism of noise / latencies
Ladder: 184 us race / 184 us contrast race / 0.8 ms refractory floor
(tightest exhibited same-channel gap {gap:.3f} ms on {gap_ch}) / 500 us race
window / 694 us gate latency / 20 ms bus epoch / 40 ms raster / 6.4 s
probe / 8.2 min HITL / 3 min naive raise-ramp counterfactual / 14 min
pre-t0 ERD leak / 1.1 h ERD lineup / 3.6 h salt-passage trip / +3 d
contrast / +21 d governance. Adaptation decay on hp.feed
(0.55->0.51->0.81->0.31), erd.dp (0.76->0.79->1.42->0.47->0.41->0.29),
perm.cond (0.62->0.59->0.46->0.27), flow.perm (0.54->0.43).

### Value for SNN distillation
- ERD SEAL PERMEATE HEADER = THREE CORRECT LOOPS, WRONG VOLUME.
- ERD-TRUE RESIDUAL CHANNEL that policy treated as transducer-nuisance-only
  as the tie-break.
- REVERSIBLE PROBE that moves mixed perm iff the ERD is leaking.
- TRIPLE-EDGE ELIGIBILITY: coordinated depression; pair rollback fails.
- CRITIC HEAD that can hold a process-correct MODIFY against a later
  unmonitored world loss without netting.

## Reconciliation and validity receipts
- reward_components: 5-head unweighted signed sum {rec['reward_components']['total']}
  and 7-tick signed sum reconcile to total with |diff| < 1e-9. Embedded
  contrast 5-head sum 0.46 reconciles independently.
- spike_events: primary {len(rec['spike_events'])} events, one key t_rel_ms,
  globally non-decreasing, min same-channel gap {gap:.3f} ms >= 0.8 ms, 3
  channels inside race_window_us 500 (erd.dp.high 6.512, perm.in_band 6.696,
  hp.feed 6.920). Contrast 8 events, own race, min same-channel gap well
  above 0.8 ms.
- Sidecars: raster spikes 51 == round(160 x 8.0 x 0.040); energy 1173 pJ /
  0.001173 uJ at 23 pJ/spike; excerpt 16 events inside [0, 40000] us,
  neuron_id < 160, same-neuron gap N/A (unique ids) / >=1000 us; routing 4
  entries with three scar edges' before/after pair; third factor tau 0.92 s
  == 920 ms; gate_snn pools 42/15/4 == round(n x rate x 0.025) each,
  decision MODIFY == safety_decision.decision.
- Pipeline: {pipeline_receipt}

## Novel coverage
The coordination-failure CLASS (ERD-seal certificate of a permeate-header),
the domain (seawater-RO / isobaric ERD / industrial process),
the HP-probe discriminant, the triple-edge scar with
pair-rollback-fails, the primary negative-result (correct MODIFY, train
still fails on unmonitored last-stage scoring), the HITL ERD-LOTO
ratify, the brackish-RO probe-duration refit, and the night-shift
10-bin quantization fence are absent from prior committed ouroboros
rounds and from staged r14-r50. Repeated elements discounted: same-gate
contrast (r02/r03/r04/r14), governance-pricing scaffold, flip-fragility
series (extended to membrane-duty certificate, but the move rhymes),
sequenced recovery shape, third-factor rollback form (here three edges
rather than r14's two), negative-result primary (r14 staged). Adjacent
wrong-volume / header rounds (r18 civic dosing, r45 TLE mixed-header)
share industrial-process scaffolding but not SWRO ERD-seal physics.
Weighing a new failure family + cure vocabulary + domain against those
reused scaffolds:

{NOVEL_LINE}

## What ROUND 52 should add
1. FIT THE DESIGNED CONSTANTS: ERD-leak arrival, probe error bands,
   last-stage scoring kinetics, night-shift claim process.
2. HIL PROVENANCE CELL: put the ERD-LOTO ratify on a hardware-in-loop
   skid-gantry interlock with fitted latency as state.sim_or_real=hil.
3. CROSS-RECORD ARC: let CR-E-5110's residual alarm be the igniter of
   the next round rather than a dangling +21 d leaf.
4. Domain candidates (de-collided): continuous hot-dip galvanizing;
   Fourdrinier paper machine; autonomous-driving; grid-inspection
   (if distinct from STARLING aerial-swarm and TORSIONKEY pitch).
   AVOID seawater-ro-desalination
   (now used), civic coagulant-dosing, glass-container IS, sulfuric
   contact, EAF foamy-slag, ethylene-steam-cracker coil,
   fcc-riser-regenerator, fcc-regenerator-cyclone-dipleg,
   ammonia-converter, hdpe-slurry-loop, blast-furnace burden descent,
   claus-sulfur-recovery, delayed-coker, LNG MCHE, chlor-alkali
   membrane, cement-rotary-kiln, kraft-recovery, pem-electrolysis,
   electrolytic-aluminum, humanoid-locomotion, steel-caster mold-level,
   surgical-assist, wind-turbine pitch, lyophilization,
   event-camera-traffic-grid, district-heating, aerial-swarm,
   warehouse-amr, underwater-rov, czochralski-pull, slot-die coating,
   optical-fiber-draw, vacuum-induction melt, steam-methane reformer,
   irrigation-canal, autoclave-composite-cure, geothermal-binary-orc,
   tire-curing-press, hydroelectric-kaplan-wicket, float-glass tin-bath,
   and any LYOSHIELD / CINDERWICK / TRIAD / SKULLGATE / CALXION /
   MAGNORIL / GORSEFLUE / CLINKERFELL / SODASHARD / LINTELPLY /
   KAOTHARN / TREADNOLL / ANOLITH / DRUMWROTH / RIMEBRAID / PITCHSTAITH /
   BRIMVAULT / BOGIRON / NITROSTAITH / NITREVAULT / CHROMLOOP /
   RUNNELGATE / ETHYNWOLD / SPARKHOLT / DIPLEGAR / OLEUMWEIR /
   SKARVOLT / GOBWOLD / GOBSPALL / OSMOLITH plant.
"""
    (OUT / "NOTES-r51.md").write_text(notes)
    return notes


def write_transcript(rec, line):
    c1_spikes = [e for e in rec["spike_events"] if e["t_rel_ms"] <= C1_SPIKE_CUTOFF_MS]
    text = """# Multi-Agent Ouroboros Swarm — Round 51 transcript

Factory: multi-agent-ouroboros-swarm
Run: 2026-09-02-final-heavy
Generator: grok-4.6
Record id: maos-r51-001
Quota Q: 1
Rights: RM-793 research-only (SpaceXAI/xAI SuperGrok Heavy consumer chat)
Plant: invented OSMOLITH / Spumeholt SWRO RO-8 (not TRIAD / Meridian / VANTIS-CADENCE-AEGIS / LYOSHIELD / GOBWOLD / OLEUMWEIR / SKARVOLT)

Two densifying cycles. Verbatim headings in order. Trajectory Builder cycle 2
emits the only JSONL line (also written to batch-r51.jsonl).

---

# CYCLE 1 — Foundation + injections

## Generator

Design intent: an eight-vessel SWRO train where three
correct agents each read a header-side loop because a 14 min cracked
isobaric-rotary ERD seal partitions vessel-true brine contamination from
header-true mixed permeate. The naive playbook raises HP into leaking
last-stage elements. The gate must MODIFY on a numeric pressure ceiling,
not by killing an agent.
sim_or_real=designed. Reward heads are
task_progress/safety/efficiency/coherence/exploration.

Cycle-1 base arc (pre-critic): state at Spumeholt RO-8, HP 62.4 bar,
perm 380 uS/cm, flow 1840 m3/h, proposed RAISE-PRESSURE +3.5 bar,
safety MODIFY to PRESSURE-HOLD, executed hold without the HP-probe
numbers fully specified, outcome "ERD found, train saved"
(this last claim is the defect the later cycles will refuse to keep).
Sixteen spikes, five ticks, raster/gate_snn present but the scar is a
single edge.

```json
{
  "id": "maos-r51-001",
  "state": {
    "sim_or_real": "designed",
    "domain": "industrial-process",
    "description": "Train RO-8 at membrane duty; three header loops in-spec; supervisor proposes raise-pressure.",
    "t0_us": 1786310400000051,
    "gate_latency_us": 694,
    "race_window_us": 500
  },
  "proposed_action": {"name": "raise_pressure", "parameters": {"raise_bar": 3.5}},
  "safety_decision": {"decision": "MODIFY", "rationale": "Hold; do not raise while ERD residual is high."},
  "executed_action": {"name": "pressure_hold", "executed_as_proposed": false},
  "future_outcome": {"summary": "ERD found, train saved."},
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
   outcome that claims "train saved". If the pre-t0 score later trips
   salt-passage, booking +0.40 is a lie. Fix: declare `_aggregation`,
   emit 3–8 ticks that sum to task_progress+safety+efficiency+coherence+exploration,
   and do not call a quarantined island a save.
2. **blocking — weak safety rationale.** `safety_decision.rationale` has no
   numeric floor. Contract requires a concrete constraint. Fix: quote
   do not raise while r_dP > 1.1 bar AND inferred ERD leak > 0.8%.
3. **major — domain is a bucket, not a plant.** `state.domain` =
   `industrial-process` collides with generic MES vocabulary and teaches
   nothing. Seawater-RO desalination (ERD residual vs mixed perm,
   inferred leak as a seal flag) is absent from prior ouroboros
   rounds and must be named.
4. **major — race under-specified.** One dP channel cannot be a race.
   Need >=2 channels inside `race_window_us` with globally sorted `t_rel_ms`
   and same-channel refractory >= 0.8 ms.
5. **minor — single-edge scar.** Raster routing with one potentiated weight
   repeats r04's one-edge rollback and is thinner than r14's two-edge.
   NOTES-r14 item 4 asked for three edges where pair rollback fails.

Critic does not rewrite the trajectory.

## Diversity Enforcer

Injected novel domain (exactly 1 this cycle): **seawater-ro-desalination**
(justified novel subdomain of industrial-process / membrane desalination;
explicit tag `seawater-ro-desalination`).

Displaced: the Generator's generic `industrial-process` bucket, and any
temptation to reuse warehouse-amr, aerial-swarm, district-heating,
event-camera-traffic-grid, pharmaceutical-lyophilization, civic
coagulant-dosing, float-glass, underwater-rov, electrolytic-aluminum,
czochralski-pull, slot-die coating, pem-water-electrolysis, wind-turbine
pitch, surgical-assist, optical-fiber-draw, kraft-recovery-boiler,
steel-continuous-caster, humanoid-locomotion, vacuum-induction melt,
steam-methane reformer, cement-rotary-kiln-clinker,
autoclave-composite-cure, geothermal-binary-orc, tire-curing-press,
chlor-alkali-membrane-electrolysis, delayed-coker, lng-mche,
claus-sulfur-recovery, blast-furnace-burden-descent, ammonia-converter,
hdpe-slurry-loop, hydroelectric-kaplan-wicket, ethylene-steam-cracker-coil,
fcc-riser-regenerator, fcc-regenerator-cyclone-dipleg,
sulfuric-contact-converter, eaf-foamy-slag, or glass-container IS.
Bayer digestion and autonomous-driving are left unused.

Domain-specific constraint: pressure raise must remain forbidden while
r_dP > 1.1 bar even if mixed perm is inside the healthy band; inferred
leak is a seal flag the mixed header cannot substitute for.

Sensor delta: +HP discharge, +mixed-header conductivity, +permeate flow,
+ERD residual; -any mobile robot, -event-camera gantries,
-DVS, -Pirani/CM, -RGA quadrupole, -DVL, -pitch encoder, -tendon LVDT,
-insole GRF, -kiln zirconia, -smelt IR, -cell-outlet pH, -stockline radar,
-cracker COT, -FCC cyclone dP, -EAF off-gas H2, -IS blank-TC.

`state.domain` and `meta.domain` both become `seawater-ro-desalination`.
Opening of `state.description` must Jaccard < 0.4 against prior plants
(Spumeholt night-shift SWRO ERD leak, not a lyophilizer, not a
civic WTP, not a tin bath, not a ROV pad, not a potline, not a PEM stack,
not an OR, not a gait lab, not a kiln, not a kraft boiler, not a
membrane row, not a blast furnace, not an ammonia converter, not an FCC,
not an EAF, not an IS machine).

## Edge-Case Hunter

Injected adversarial tail (exactly 1 this cycle): **cracked isobaric-rotary
ERD seal + permeate-header certificate**.

- Trigger: RO-8G ERD rotor seal plus brine into vessels 7-8,
  r_dP 3.8 bar, mixed perm 380 uS/cm.
- Base rate: <1% — 0.34%/cycle from a seal-leak MC (skid-gantry
  visual threshold is designed; rotor leakage fitted-style). Visual PASSES
  because the housing looks dry.
- Naive failure: FALSE PERMISSION. PB-RO-8 sees three in-spec header
  loops, raises +3.5 bar, salt-passage avalanche, $1.72M.
- Trajectory edit: put the ERD leak in `state.fault_context`, make each
  agent's confirm a different header-side slice of the same vessel-false
  state (hp-in-band, perm-in-band, flow-in-band). ERD residual is
  readable but policy-treated as transducer-nuisance-only.

Distinct from stacked-dead-band permission (fragments of one trip vs
wrong-volume sensing), from r18 civic dosing (SCD vs ERD), from r24 PEM
(stack voltage vs seawater rejection), and from r45 TLE mixed-header
(cracker quench vs SWRO seal).

## Neuromorphic Translator

Cycle-1 temporal densification (16 spikes, 5 ticks, 40 ms raster):

| channel | t_rel_ms | amplitude |
|---|---|---|
| hp.feed | 0.310 | 0.55 |
| perm.cond | 1.150 | 0.62 |
| flow.perm | 2.050 | 0.54 |
| erd.dp | 3.190 | 0.76 |
| hp.feed | 4.170 | 0.51 |
| erd.dp | 4.850 | 0.79 |
| perm.cond | 5.370 | 0.59 |
| erd.dp.high | 6.512 | 1.42 |
| perm.in_band | 6.696 | 1.15 |
| hp.feed | 6.920 | 0.63 |
| ctrl.gate | 7.198 | 1.09 |
| erd.dp | 8.870 | 0.47 |
| hp.feed | 10.760 | 0.81 |
| perm.cond | 13.050 | 0.46 |
| flow.perm | 18.540 | 0.43 |
| ctrl.gate | 26.180 | 0.85 |

Race: ERD residual 6.512 vs perm-in-band 6.696 (184 us) inside 500 us;
hp.feed 6.920 is the third channel in-window. Winner/loser flip: reversing
184 us reshuffles PB-RO-8 triage; floors still MODIFY. Refractory held
(cycle-1 min same-channel gap 1.660 ms on erd.dp 4.850-3.190; hp
4.170-0.310 = 3.860; perm 5.370-1.150 = 4.220). Adaptation: erd
0.76->0.79->1.42->0.47; hp 0.55->0.51->0.81; perm 0.62->0.59->0.46.

Raster cycle-1 seed: 40 ms, 160 neurons, 8.0 Hz, 51 spikes, 1173 pJ, third
factor acetylcholine tau_e 0.92 s. Single scar edge only — cycle 2 must
add the second and third edges.

Ticks 1–5 at 4560, 6512, 7198, 6.4e6, 492e6 us; heads not yet the final
-0.16 (missing the 1.1 h and 3.6 h ticks).

Distillation value this cycle: header-side confirms as a permission code
that is not a vessel-true membrane-duty code.

## Trajectory Builder

Cycle-1 hardened object: domain seawater-ro-desalination, tail cracked
ERD seal, 16 spikes, 5 ticks, MODIFY with numeric floor, raster+gate_snn
present, sim_or_real=designed, rights stamp on record and meta, no thought
keys. Still missing (and therefore not the publishable line): brackish-RO
sub-variant, night-shift tail, second and third scar edges,
delayed salt-passage trip as PRIMARY terminal, contrast ACCEPT episode,
ticks 6–7, spikes 17–26.

Validation receipt (cycle 1, not final):
- checks passed: 16 spikes sorted; 3 channels in 500 us window; refractory
  >= 0.8 ms; rationale quotes 1.1 bar / 0.8%; domain named;
  gate_snn.decision MODIFY.
- checks deferred to cycle 2: triple-edge scar, second tail, second domain
  constraint, negative-result booking, 7 ticks summing to heads.
- densification vs Generator v1: +1 domain, +1 tail, +16 spikes, +5 ticks,
  +numeric floor.

Cycle-1 JSON is retained as the base; it is NOT written to batch-r51.jsonl.

Cycle-1 spike count: __C1_SPIKES__.

---

# CYCLE 2 — Densification

## Generator

Cycle-1 output is the base. Additive expansion (nothing removed):

1. Downstream side-effect (immediate): HP probe at +6.4 s stays
   leak-true (|d-cond| 42 >= 25) — mixed-header-plus-ERD-leak, not true
   membrane-duty. ERD stays locked. Scored last-stage discovered during the lock.
2. Delayed side-effect (PRIMARY terminal, not a footnote): at +3.6 h
   salt-passage trip from the pre-t0 last-stage score; 12 h outage;
   $1.12M. The 14 min pre-t0 ERD leak is the mechanism. Correct gate, train
   still fails.
3. Deepened `proposed_action.evidence` with units: r_dP 3.8 bar,
   perm 380 uS/cm, HP 62.4 bar, flow 1840 m3/h, leak 2.1%,
   race 184 us.
4. Tightened rationale to the numeric floor do not raise while r_dP > 1.1 bar
   AND inferred leak > 0.8%, plus probe bands >= 25 vs <= 8 uS/cm,
   plus HITL 8.2 min ERD-LOTO rule.

Reward retargeted to total -0.16 so the delayed fail is the inflection
(t_us 12960000000), not the gate. Process heads remain non-zero.

## Critic

Re-audit of the expanded trajectory:

1. **blocking if unfixed — missing second domain constraint.** Seawater
   probe 6.4 s / +0.6 bar is not a universal number. A brackish train
   will over-move a healthy mixed perm. Diversity Enforcer must inject
   the physical-constraints sub-variant this cycle.
2. **major — only one tail class.** ERD-seal growth is accidental
   infrastructure. A disjoint human-intent tail is still required
   (night-shift perm CSV forgery is the open cell).
3. **major — scar is still one edge in the cycle-1 raster.** NOTES-r14
   item 4 is not discharged until three go-edges exist and pair rollback
   is shown to fail at threshold 0.30.
4. **minor — contrast episode missing.** Without a same-gate ACCEPT on a
   true membrane-duty window the record teaches "never raise". Add +3 d sister-train
   contrast with its own race.
5. **minor — HITL latency mentioned in prose only.** Put 8.2 min in
   executed_action.parameters.human_ratify and in a tick.

No rewrite; directives only.

## Diversity Enforcer

Injected second novel domain / physical-constraint sub-variant (exactly 1
this cycle): **brackish-RO / low-pressure** on a sister
driving-force class.

What it expands: seawater 62.4 bar (cycle 1) -> brackish 18 bar.
Driving force 0.29x. Conductivity-gain 2.6x per bar.
The 6.4 s +0.6 bar pulse moves even a HEALTHY brackish mixed perm 28 uS/cm,
inside the leak-looking band. Required probe: 18 s at +0.18 bar
(leak |d-cond| 31 uS/cm, healthy 5).

This is still one domain injection for the cycle (physical-constraints
clause of the factory prompt). It does not displace
seawater-ro-desalination; it changes which probe table is legal.
`future_outcome.subvariant_constraint` carries the refit. Jaccard opening
stays the Spumeholt eight-vessel sentence; brackish-RO is additive, not a rewrite.

## Edge-Case Hunter

Injected second adversarial tail (exactly 1 this cycle, disjoint class):
**night-shift forged permeate-conductivity CSV**.

- Trigger: shift lead, 02:48, posts a historian export showing
  mixed perm = 380 uS/cm at t = 1.1 h to clear a flux catchup slot.
- Base rate: ~0.30% of Sunday-night cycles (designed, flagged, <1%).
- Naive failure: a weak supervisor ACCEPTs the raise on the forged confirm
  and ignores live r_dP. Salt-passage trip plus a data-integrity write-up.
- Fence: forged log quantized at 10 uS/cm (SCADA screenshot rounding); plant
  historian is 1 uS/cm (10 bins). Live r_dP is 3.8 bar and leak is 2.1%
  at the claimed membrane-true, which no live healthy ERD produces.
  Freeze-window overlap with the 14 min ERD leak.
- Trajectory edit: governance CR-E-5110 mandates native 1 uS/cm CSV
  exports; the contrast ACCEPT still requires live r_dP, not a CSV.

Distinct from cycle-1 ERD leak (accidental seal vs deliberate deception)
and from the brackish sub-variant (physics vs fraud).

## Neuromorphic Translator

Re-densify (additive):

- +10 spikes after 26.180 ms: hp.probe 6400.0, erd.dp 6488.4 (adapt
  1.42->0.41), perm.in_band 6572.6 (1.15->0.35), human.ratify 492000.0,
  erd.lock 492900.0, membrane.score 493700.0, hp.feed
  3960000.0, erd.dp 3960720.0, perm.cond 3961480.0, salt.trip
  12960000.0. Primary train 16 -> 26. Still one key, still sorted,
  refractory held.
- +2 ticks (5 -> 7) at 3_960_000_000 us (true membrane duty) and
  12_960_000_000 us (salt-passage trip). Heads now 0.08, -0.36, -0.10, 0.14,
  0.08; total -0.16. Inflection is the last tick.
- Contrast train 8 events, own race 184 us, ACCEPT.
- Triple-edge third factor: three header-healthy-go edges, tau_e 0.92 s = 920 ms,
  trace __AUX_TRACE__, eta __AUX_ETA1__ / __AUX_ETA2__ / __AUX_ETA3__,
  weights 0.48->0.24, 0.43->0.22, 0.40->0.20. Raster excerpt unchanged
  (decision window is still 40 ms) and remains sorted with unique
  neuron_ids (same-neuron >=1000 us vacuously).

Winner/loser flip (re-stated, not replaced): reversing 184 us would only
reorder triage; r_dP floors still MODIFY. Contrast flip of 184 us
similarly cannot turn a healthy ERD into a cracked seal.

## Trajectory Builder

Schema checks on the FINAL object: required Thalamic v2 keys present as
objects; `state.sim_or_real`=designed; `safety_decision.decision`=MODIFY
with numeric rationale; `reward_components.total` = sum of five heads =
sum of 7 ticks = -0.16; `spike_events` globally non-decreasing on
t_rel_ms, 26 events, refractory >=0.8 ms, 3 channels in race window;
raster 20–50 ms, spikes=round(n*rate*window_s)+/-1, energy 23 pJ/spike,
excerpt sorted, tau_e consistent; gate_snn.decision matches; meta.round=51,
factory=multi-agent-ouroboros-swarm, generator=grok-4.6,
run_label=2026-09-02-final-heavy; rights on record and meta; no thought
keys; no training_ready; Diversity + Edge-Case injections from BOTH cycles
present and non-trivial; cycle 2 strictly additive.

Densification delta: +1 domain sub-variant (brackish RO), +1 tail
(night-shift forgery), +10 spikes (16->26), +2 ticks (5->7), +1 contrast
train with own race, +2 delayed side-effects, +1 triple-edge scar with
pair-rollback-fails, +1 HITL ratify, +1 surprise (last-stage scoring is
the salt-passage mechanism).

Publishable JSONL line (the only JSONL line; also at batch-r51.jsonl):

```json
__FINAL_JSONL__
```

Validation receipt (final): checks passed / fixed as reported by
build_r51.py self-validate (check_jsonl, raster_status, verify_record_execution,
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
    (OUT / "swarm-transcript-r51.md").write_text(text)
    return text


def main():
    rec, aux = build_record()
    errs = local_checks(rec, aux)

    OUT.mkdir(parents=True, exist_ok=True)
    line = json.dumps(rec, ensure_ascii=False, separators=(",", ":"))
    (OUT / "batch-r51.jsonl").write_text(line + "\n")

    from check_records import FactoryStaging, check_jsonl
    from curate_bridge import raster_status
    from verify_execution import verify_record_execution

    e, w, kinds, n = check_jsonl(
        OUT / "batch-r51.jsonl",
        "batch-r51.jsonl",
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
            str(OUT / "batch-r51.jsonl"),
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
        [sys.executable, "/tmp/maos_heading_check.py", str(OUT / "swarm-transcript-r51.md")],
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
            "maos-r51-001|OSMOLITH|GOBSPALL",
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
    print("OK maos-r51-001 staged under", OUT)
    print("bytes jsonl", (OUT / "batch-r51.jsonl").stat().st_size)
    print("bytes notes", (OUT / "NOTES-r51.md").stat().st_size)
    print("bytes transcript", (OUT / "swarm-transcript-r51.md").stat().st_size)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
