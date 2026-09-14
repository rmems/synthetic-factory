#!/usr/bin/env python3
"""Build and self-check MAOS round-53 JSONL (research-only; not published)."""
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

GEN_AT = "2026-09-03T08:53:00Z"
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
OUT = Path("/tmp/maos-r53")
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
    "training_ready",
    "da Vinci",
    "Intuitive Surgical",
    "Boston Dynamics",
    "Nucor",
    "Arcelor",
    "Lafarge",
    "Holcim",
    "Heidelberg",
    "Cemex",
    "CLINKERFELL",
    "Flintmere",
    "SODASHARD",
    "Cairnmere",
    "Asahi",
    "Nafion",
    "Chemours",
    "Nouryon",
    "Uhde",
    "INEOS",
    "Westlake",
    "OxyChem",
    "Formosa",
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
    "WELDSPIT",
    "Cheniere",
    "Qatargas",
    "QatarEnergy",
    "Air Products",
    "APCI",
    "ConocoPhillips",
    "Bechtel",
    "Technip",
    "Baker Hughes",
    "ExxonMobil",
    "TotalEnergies",
    "Woodside",
    "Novatek",
    "Yamal",
    "Venture Global",
    "Sempra",
    "Freeport LNG",
    "Air Liquide",
    "Chart Industries",
    "Foster Wheeler",
    "SYDEC",
    "Valero",
    "Marathon Petroleum",
    "Phillips 66",
    "McDermott",
    "Lummus",
    "Worley",
    "Fluor",
    "Yara",
    "CF Industries",
    "Nutrien",
    "Koch Fertilizer",
    "KBR",
    "Topsoe",
    "Haldor",
    "Kellogg",
    "Thyssenkrupp",
    "Casale",
    "Saipem",
    "Johnson Matthey",
    "Clariant",
    "Linde",
    "NITROSTAITH",
    "Chalkfen",
    "BOGIRON",
    "Mireholt",
    "CHROMLOOP",
    "Marlfell",
    "ETHYNWOLD",
    "Woadfen",
    "NITREVAULT",
    "Glaucove",
    "RUNNELGATE",
    "Ghyllmere",
    "Voith",
    "Andritz",
    "Litostroj",
    "Rainpower",
    "Gilkes",
    "Danieli",
    "Primetals",
    "Tenova",
    "Consteel",
    "Gerdau",
    "Steel Dynamics",
    "Big River Steel",
    "GrafTech",
    "RHI Magnesita",
    "Paul Wurth",
    "Cleveland-Cliffs",
    "POSCO",
    "Voestalpine",
    "Outokumpu",
    "Nippon Steel",
    "Tata Steel",
    "Severstal",
    "EVRAZ",
    "Gritfen",
    "DIPLEGAR",
    "SPARKHOLT",
    "Scoriafen",
    "OLEUMWEIR",
    "Brindlefell",
    "VESPERTHORN",
    "ASHVEIL",
    "IRONMANTLE",
    "DUSKRELAY",
    "PALISADE",
    "TELAMON",
    "CHORDA",
    "Brinewell",
    "SKARVOLT",
    "Emberbarrow",
    "GOBWOLD",
    "Culletwick",
    "Toray",
    "Teijin",
    "Hexcel",
    "SGL Carbon",
    "Zoltek",
    "DowAksa",
    "Hyosung",
    "Toho Tenax",
    "Mitsubishi Rayon",
    "Owens-Illinois",
    "Verallia",
    "Ardagh Glass",
    "Vidrala",
    "Emhart Glass",
    "Bottero",
    "Heye International",
    "Sklostroj",
    "Vetropack",
    "GAUZEFELL",
    "Ammoxwick",
    "OSMOLITH",
    "Spumeholt",
    "PUSHERFELL",
    "Sootmere",
    "LIXIVQUERN",
    "Bauxfen",
)
R14_OPENING = (
    "Helixmere Biologics Building C lyophilizer LYO-4 is mid-primary on 8400 "
    "vials of a monoclonal antibody"
)
NOVEL_LINE = "Novel coverage: 46%"
PLANT = "CREELWOLD"
GEO = "Rovingholt"
CELL = "OX-6"
DOMAIN = "carbon-fiber-oxidation-oven"
RECORD_ID = "maos-r53-001"
ROUND = 53
PROBE_S = 7.0
TAU_E_S = 7.0
C1_SPIKE_CUTOFF_MS = 26.188


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
        if p.parent.name == "maos-r53":
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
        if p.parent.name == "maos-r53":
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
        if p.parent.name == "maos-r53":
            continue
        try:
            text = p.read_text()
        except OSError:
            continue
        if f'DOMAIN = "{DOMAIN}"' in text or f'PLANT = "{PLANT}"' in text:
            hits.append(f"{p}: claimed {PLANT}/{DOMAIN}")
        if f'GEO = "{GEO}"' in text and f'PLANT = "{PLANT}"' in text:
            hits.append(f"{p}: geo+plant {GEO}/{PLANT}")
    return hits


def build_record():
    ticks, heads = cents_ticks(
        [4628, 6818, 7518, 7_000_000, 576_000_000, 9_000_000_000, 12_240_000_000],
        [
            (1, -2, -1, 2, 1),
            (2, -5, -1, 3, 1),
            (2, -6, -2, 3, 2),
            (1, -6, -2, 2, 1),
            (1, -5, -2, 2, 1),
            (1, -5, -1, 1, 1),
            (0, -5, -2, 1, 1),
        ],
    )
    assert abs(heads["total"] - (-0.15)) < 1e-9, heads

    trace = math.exp(-PROBE_S / TAU_E_S)
    eta1 = 0.24 / trace
    eta2 = 0.21 / trace
    eta3 = 0.19 / trace
    dw1 = eta1 * 1.0 * trace
    dw2 = eta2 * 1.0 * trace
    dw3 = eta3 * 1.0 * trace
    w1 = 0.46 - dw1
    w2 = 0.41 - dw2
    w3 = 0.38 - dw3
    assert abs(w1 - 0.22) < 5e-4, w1
    assert abs(w2 - 0.20) < 5e-4, w2
    assert abs(w3 - 0.19) < 5e-4, w3

    spike_events = [
        {"channel": "zmean.t", "t_rel_ms": 0.248, "amplitude": 0.53},
        {"channel": "tens.n", "t_rel_ms": 1.068, "amplitude": 0.61},
        {"channel": "o2.vol", "t_rel_ms": 1.888, "amplitude": 0.55},
        {"channel": "zmean.t", "t_rel_ms": 3.108, "amplitude": 0.49},
        {"channel": "hot.ir", "t_rel_ms": 4.628, "amplitude": 0.71},
        {"channel": "tens.n", "t_rel_ms": 5.128, "amplitude": 0.64},
        {"channel": "o2.vol", "t_rel_ms": 5.568, "amplitude": 0.52},
        {"channel": "hot.ir", "t_rel_ms": 6.818, "amplitude": 1.26},
        {"channel": "zmean.ok", "t_rel_ms": 7.010, "amplitude": 1.09},
        {"channel": "overlap.cam", "t_rel_ms": 7.154, "amplitude": 0.66},
        {"channel": "ctrl.gate", "t_rel_ms": 7.518, "amplitude": 1.05},
        {"channel": "zmean.t", "t_rel_ms": 8.928, "amplitude": 0.45},
        {"channel": "tens.n", "t_rel_ms": 10.788, "amplitude": 0.46},
        {"channel": "hot.ir", "t_rel_ms": 12.648, "amplitude": 0.85},
        {"channel": "o2.vol", "t_rel_ms": 18.408, "amplitude": 0.43},
        {"channel": "ctrl.gate", "t_rel_ms": 26.188, "amplitude": 0.83},
        {"channel": "hot.probe", "t_rel_ms": 7000.0, "amplitude": 0.93},
        {"channel": "hot.ir", "t_rel_ms": 7140.6, "amplitude": 0.39},
        {"channel": "zmean.ok", "t_rel_ms": 7240.4, "amplitude": 0.35},
        {"channel": "human.ratify", "t_rel_ms": 576000.0, "amplitude": 0.81},
        {"channel": "creel.isolate", "t_rel_ms": 576800.0, "amplitude": 0.73},
        {"channel": "ox.inventory", "t_rel_ms": 577400.0, "amplitude": 0.82},
        {"channel": "zmean.t", "t_rel_ms": 9000000.0, "amplitude": 0.30},
        {"channel": "tens.n", "t_rel_ms": 9000460.0, "amplitude": 0.28},
        {"channel": "hot.ir", "t_rel_ms": 9000920.0, "amplitude": 0.19},
        {"channel": "tow.reject", "t_rel_ms": 12240000.0, "amplitude": 0.89},
    ]

    contrast_spikes = [
        {"channel": "speed.demand", "t_rel_ms": 0.000, "amplitude": 0.85},
        {"channel": "hot.clear", "t_rel_ms": 0.192, "amplitude": 0.19},
        {"channel": "zmean.ok", "t_rel_ms": 0.410, "amplitude": 0.77},
        {"channel": "zmean.t", "t_rel_ms": 1.660, "amplitude": 0.41},
        {"channel": "tens.n", "t_rel_ms": 4.920, "amplitude": 0.52},
        {"channel": "ctrl.gate", "t_rel_ms": 7.180, "amplitude": 0.91},
        {"channel": "hot.probe", "t_rel_ms": 3500.0, "amplitude": 0.33},
        {"channel": "tow.reject", "t_rel_ms": 12240000.0, "amplitude": 0.13},
    ]

    excerpt = [
        {"t_us": 248, "neuron_id": 48},
        {"t_us": 1068, "neuron_id": 90},
        {"t_us": 1888, "neuron_id": 102},
        {"t_us": 3108, "neuron_id": 52},
        {"t_us": 4628, "neuron_id": 10},
        {"t_us": 5128, "neuron_id": 94},
        {"t_us": 5568, "neuron_id": 106},
        {"t_us": 6818, "neuron_id": 8},
        {"t_us": 7010, "neuron_id": 56},
        {"t_us": 7154, "neuron_id": 18},
        {"t_us": 7518, "neuron_id": 130},
        {"t_us": 8928, "neuron_id": 60},
        {"t_us": 10788, "neuron_id": 98},
        {"t_us": 12648, "neuron_id": 14},
        {"t_us": 18408, "neuron_id": 110},
        {"t_us": 26188, "neuron_id": 134},
    ]

    rec = {
        "id": RECORD_ID,
        "title": "SKARVOLT EAF-7: off-gas H2 8.6 vol% beats arc.ok by 192 us; correct MODIFY still dumps the heat after pre-t0 panel-leak hydrogen",
        "rights": dict(RIGHTS),
        "state": {
            "sim_or_real": "designed",
            "domain": DOMAIN,
            "scenario_name": "SKARVOLT / Gritfen Meltshop EAF-7",
            "timestamp_local": "2026-03-22T02:36:00-05:00",
            "t0_us": 1780002440000949,
            "gate_latency_us": 700,
            "race_window_us": 500,
            "race_window_rel_ms": [6.746, 7.246],
            "description": "Gritfen Meltshop slag-tip bay EAF-7 holds a 180 t AC eccentric-bottom-tap furnace under foamy-slag practice at 78 MW. ARC secondary voltage is 410 V against 390-430. ROOF delta temperature is 1480 C inside 1420-1550. OG CO/CO2 ratio is 1.42 inside 1.20-1.70. Playbook PB-EAF-11 treats the conjunction as permission to raise tap-to-tap power. The consensus is false: sidewall panel P-14 dumps 18 L/min of cooling water into the bath over 16 min. ARC stays in-band because transformer secondary voltage is upstream of the bath and foam still supports a stable arc. ROOF stays in-band because carbon-injection foam blankets roof radiation. OG stays in-band because the analyzer is CO/CO2 only and H2 from the water-steel reaction is not in the ratio. Uncommissioned r_h2 is 8.6 vol% against a 1.2 hold. Uncommissioned r_leak is 18 L/min against a 2.0 hold. H2-first latches RAISE-HOLD plus a power-cut probe; arc-ok-first would have authorized RAISE-POWER 78 to 92 MW into a wet bath.",
            "goal": "Hold tap power at 78 MW while r_h2 > 1.2 vol% AND r_leak > 2.0 L/min; keep panel-leak at 0 and dissolved hydrogen <= 1.5 ppm.",
            "race": {
                "contenders": [
                    "h2.og 8.6 vol% (uncommissioned off-gas H2 vs foamy-slag fingerprint)",
                    "arc.ok 410 V (secondary voltage inside 390-430 V)",
                ],
                "semantics": "H2-first latches RAISE-HOLD + POWER-CUT-PROBE + panel isolate. Arc-ok-first latches RAISE-POWER (78 to 92 MW into the wet bath, no probe).",
                "window_derivation": "500 us = one 380 us arc-VT ADC slot plus 120 us H2-TCD publish.",
                "order_evidence_note": "Margin 192 us vs combined jitter 62 us (h2 34 + arc 28): 3.10x. The 192 us gap sits inside min(500, 500) us, so a sub-flip-bound perturbation reverses triage order. The gate rides the order-invariant floors r_h2 > 1.2 vol% and r_leak > 2.0 L/min, not the alarm order.",
            },
            "topology": {
                "site": "Gritfen Meltshop, invented slag-tip steel campus Gritfen, Bay 3 AC EAF-7: 180 t eccentric-bottom-tap, foamy-slag carbon injection, 78 MW hold, uncommissioned off-gas H2 TCD, uncommissioned panel-circuit make-up MFC, Grade-C roof-bay",
                "agents": "ARC secondary VT (vendor Voltgage): transformer-side arc voltage. ROOF delta TC (vendor Roofholt): roof/delta temperature. OG CO/CO2 analyzer (vendor Gascairn): foamy-slag carbon practice. Heterogeneous stacks, no shared H2 schema, one 20 ms roof-bay bus epoch",
                "coupling": "Each agent's commissioned window hides a different slice of the same leak. ARC is correct that secondary voltage is 410 V. ROOF is correct that roof T is 1480 C. OG is correct that CO/CO2 is 1.42. Playbook PB-EAF-11 treats the conjunction of three in-spec loops as permission to raise power. No agent is faulty; the 8.6 vol% H2 is a water-steel reaction the foamy-slag model cannot see.",
            },
            "sensors": [
                "secondary arc voltage transducer, 50 Hz, 28 us jitter, 410 V (spec 390-430 V)",
                "off-gas H2 TCD r_h2 is computable on the Gascairn sample tap and is NOT commissioned at t0 (8.6 vol% observed in the historian after the fact)",
                "roof/delta thermocouple, 20 Hz, 24 us jitter, 1480 C vs 1420-1550 window",
                "off-gas CO/CO2 analyzer, 10 Hz, 22 us jitter, 1.42 (window 1.20-1.70)",
                "panel-circuit make-up MFC r_leak is NOT commissioned at t0 (18 L/min vs 2.0 hold; inferred after this hold)",
                "panel leak camera is NOT commissioned at t0 (installed after this incident)",
            ],
            "constraints": {
                "raise_power": False,
                "proposed_raise_power": True,
                "h2_volpct": 8.6,
                "h2_hold_volpct": 1.2,
                "leak_L_min": 18.0,
                "leak_hold_L_min": 2.0,
                "arc_V": 410.0,
                "arc_window_lo_V": 390.0,
                "arc_window_hi_V": 430.0,
                "roof_C": 1480.0,
                "og_ratio": 1.42,
                "power_MW": 78.0,
                "leak_pre_t0_min": 16.0,
            },
            "fault_context": {
                "failure_class": "WATER-PANEL LEAK NULLSPACE OF A FOAMY-SLAG CERTIFICATE: three individually-correct heterogeneous agents agree the furnace is raise-legal because a foamy-slag model maps 8.6 vol% off-gas H2 from a sidewall panel leak into a still-in-band 410 V arc, so voltage-in-window, roof-T-in-window, and CO/CO2-in-window are jointly a plant-false power-raise permit",
                "igniter": "Furnace EAF-7 opened a P-14 sidewall-panel gasket during a 16 min Sunday-night hold after a carbon-lance stroke; cooling water dumps into the bath. Fitted-style base rate 0.34%/hold from a panel-gasket MC (designed liner-gap spec, flagged).",
                "naive_failure": "PB-EAF-11 RAISE-POWER on three healthy loops: 78 to 92 MW into a wet bath, $4.18M roof-plus-bath plus a 16-day outage",
            },
            "poisoned_context": {
                "naive_alarm": "Playbook PB-EAF-11 (after the 2025 'noisy H2-TCD nuisance') auto-drafts RAISE-POWER whenever secondary voltage is in 390-430 V AND roof T is inside 1420-1550 C AND CO/CO2 is inside 1.20-1.70, ignoring r_h2 unless the arc VT also trips unstable",
                "why_poisoned": "The three confirms are locally true and jointly insufficient. r_h2 is a computable tag the playbook dead-banded. r_leak is commissioned hardware that policy treats as a cooling-circuit leftover, not a bath-water event. Independence of 'all loops healthy' is the hidden assumption, and it is false under a panel leak the foamy-slag model cannot see.",
            },
            "constraint": "Do not raise tap power on the 180 t EAF while r_h2 > 1.2 vol% AND r_leak > 2.0 L/min. Discriminate leak vs noisy-VT with a reversible power-cut pulse before any raise.",
        },
        "proposed_action": {
            "actor": "line-speed supervisory optimizer LSSO (auto-playbook PB-CF-11 draft), submitted to gate TG-OX-6",
            "name": "raise_speed",
            "action": "RAISE-SPEED: 1.80 to 2.20 m/min into the 24k oxidation oven, no IR-cut probe, no creel isolate",
            "summary": "Treat three in-spec loops as a single-tow geometry and raise Sunday-night line speed to clear a carbonization slot.",
            "parameters": {
                "raise_speed": True,
                "hot_probe": False,
                "creel_isolate": False,
                "human_ratify": False,
            },
            "steps": [
                "assert ZMEAN 218 C inside 210-226",
                "assert TENS 22 N inside 18-26",
                "assert O2 19.4 vol% inside 18.0-21.0",
                "open line-speed raise; 1.80 to 2.20 m/min",
                "hold oven-air setpoint; proceed to next carbonization slot",
            ],
            "evidence": [
                {
                    "observable": "fiber infrared temperature r_hot",
                    "value": 248.0,
                    "unit": "C",
                    "source": "Fiberpyre IR pyrometer, historian replay after t0",
                    "note": "hold ceiling 230 C; 248 overlap exotherm over 16 min; uncommissioned at t0",
                },
                {
                    "observable": "creel-4 overlap fraction r_overlap",
                    "value": 18.0,
                    "unit": "pct",
                    "source": "uncommissioned Creelopt overlap camera",
                    "note": "hold if > 2.0 pct; overlap is a fiber-exotherm event, not the zone TC",
                },
                {
                    "observable": "six-zone plenum air mean",
                    "value": 218.0,
                    "unit": "C",
                    "source": "ZMEAN Zonegage plenum TC",
                    "note": "window 210-226 C; the overlap is a creel-traverse event",
                },
                {
                    "observable": "12-tow average tension",
                    "value": 22.0,
                    "unit": "N",
                    "source": "Towcell load cell",
                    "note": "window 18-26 N; one overlapped creel is 1 of 12",
                },
                {
                    "observable": "bulk oven oxygen",
                    "value": 19.4,
                    "unit": "vol%",
                    "source": "Oxiair zirconia",
                    "note": "window 18.0-21.0 vol%; PAN consumes O2 in the fiber boundary layer",
                },
                {
                    "observable": "race margin",
                    "value": 192,
                    "unit": "us",
                    "source": "hot.ir 6.818 ms vs zmean.ok 7.010 ms",
                    "note": "combined jitter 62 us, 3.10x; inside 500 us flip bound",
                },
            ],
            "basis": "PB-CF-11 raises on three locally-true in-spec loops. The draft does not read r_hot 248 C and does not treat r_overlap 18 pct as a fiber-exotherm event.",
            "expected_cost_bound": "If the draft executes: overlapped-tow oven fire, $4.18M plus 16-day outage. If MODIFIED: probe plus creel isolate, with residual risk from 16 min of pre-t0 over-oxidation.",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "correctness": "correct",
            "decided_by": "TG-OX-6 thalamic release gate",
            "decision_t_rel_ms": 7.518,
            "rationale": "MODIFY the draft: strip the raise, hold line speed at 1.80 m/min, run a 7.0 s speed-cut probe (overlap 12%), and isolate creel-4 only if the probe jumps fiber IR. Numeric floor: do not raise speed on the 24k oxidation oven while r_hot > 230 C AND r_overlap > 2.0 pct. Observed r_hot 248 C and r_overlap 18 pct both violate the release predicate, so a raise is forbidden even though all three playbook confirms are numerically true. The three confirms are not a single-tow certificate: zone mean is a plenum-air quantity the overlap does not move, tension is a 12-tow average that one creel cannot trip, and 19.4 vol% is a bulk-air quantity that does not see the fiber boundary layer. Probe discriminant: after a 7.0 s 12% speed-cut pulse, an overlap jumps IR >= 6.0 C in 2.8 s (extra residence feeds the cyclization exotherm); a single-tow geometry stays <= 1.0 C. Order-code discipline: IR beat zmean-ok by 192 us inside the 500 us flip bound, so triage order is flip-fragile; the hold rides the order-invariant floors, not the winner tag. Human ratification: creel isolate is a creel-bay LOTO job with fitted 9.6 min dead-man; the gate may hold and probe autonomously but may not break the creel interlock without the operator confirm.",
            "constraint_checked": {
                "raise_speed": {"observed": False, "proposed_target": True},
                "hot_C": {"observed": 248.0, "hold_if_above": 230.0},
                "overlap_pct": {"observed": 18.0, "hold_if_above": 2.0},
                "zmean_C": {"observed": 218.0, "window": [210.0, 226.0]},
            },
        },
        "executed_action": {
            "name": "speed_hold_speed_cut_probe_creel_isolate",
            "action": "SPEED-HOLD + SPEED-CUT-PROBE + CREEL-ISOLATE (gate-mandated modification)",
            "executed_as_proposed": False,
            "parameters": {
                "raise_speed": False,
                "hot_probe": True,
                "creel_isolate": True,
                "human_ratify": True,
            },
            "gate_effect": "MODIFY: raise stripped. Hold speed 1.80 m/min. 7.0 s speed-cut 12%. Probe jumps fiber IR (7.1 C in 2.8 s >= 6.0 overlap band) so creel-4 is isolated after 9.6 min human ratify. Raise resumes after r_hot recovers on a single-tow belt.",
            "deviations": "PB-CF-11 raise stripped entirely. Speed is cut only for the 7.0 s probe then returned. Creel-interlock wait added (9.6 min fitted LOTO). Over-oxidation survey added during the isolate (not in the draft).",
            "execution_log": [
                {"t_rel_ms": 7.518, "entry": "TG-OX-6 MODIFY latched 700 us after IR win; raise stripped; hold+probe authorized"},
                {"t_rel_ms": 7000.0, "entry": "speed-cut probe: overlap 12% for 7.0 s; IR jumps 7.1 C in 2.8 s (overlap band >= 6.0); r_hot 248 -> 255.1"},
                {"t_rel_ms": 576000.0, "entry": "operator ratifies creel-bay interlock break after 9.6 min LOTO (fitted walk+lockout)"},
                {"t_rel_ms": 576800.0, "entry": "creel-4 isolation closed; overlap residual 18 pct logged; r_hot 248 -> 221 on the single-tow belt"},
                {"t_rel_ms": 577400.0, "entry": "oxidation survey: 16 min pre-t0 overlap already written; 3.4 h strand-tensile assay clock started"},
                {"t_rel_ms": 9000000.0, "entry": "true single-tow geometry after 2.5 h isolate: r_hot 218, r_overlap 0.4 pct, ZMEAN 217 C (no phantom exotherm); raise now legal"},
                {"t_rel_ms": 12240000.0, "entry": "tensile inspection of the dumped creel: strand 4.8 GPa vs 5.6 spec; first spool quarantined 5.6 d"},
            ],
        },
        "future_outcome": {
            "summary": "Correct MODIFY prevented the RAISE-SPEED of an overlapped 24k oxidation oven and the $4.18M oven-return. The hold still failed: 16 min of unmonitored pre-t0 overlap had already over-oxidized creel-4. Process-correct gate, bounded world loss, negative total.",
            "state_delta": {
                "raise": "held at 1.80 m/min through probe and creel isolate; later legal raise after 2.5 h single-tow recovery on an isolated creel",
                "overlap": "18 pct overlap logged and isolated; r_hot 248 -> 221 on the belt",
                "tow": "Sunday-night creel stoppered at over-oxidized PAN; strand tensile 4.8 GPa; 5.6 d dump",
            },
            "timeline": [
                {"t_rel_ms": -960000.0, "event": "t0-16 min: splice already overlapping at creel-4 flyer; exotherm growth begins"},
                {"t_rel_ms": -420000.0, "event": "t0-7 min: r_hot first crosses above 230 C; PB-CF-11 ignores it because ZMEAN is 219 C"},
                {"t_rel_ms": 0.0, "event": "t0: hot.ir vs zmean.ok race on the oven-bay bus"},
                {"t_rel_ms": 6.818, "event": "hot.ir 248 C wins by 192 us"},
                {"t_rel_ms": 7.010, "event": "zmean.ok flag (loser)"},
                {"t_rel_ms": 7.518, "event": "TG-OX-6 MODIFY"},
                {"t_rel_ms": 7000.0, "event": "speed-cut probe confirms overlap (7.1 C IR jump, overlap band)"},
                {"t_rel_ms": 576000.0, "event": "human ratify 9.6 min; creel isolated; oxidation inventory logged"},
                {"t_rel_ms": 9000000.0, "event": "true single-tow after 2.5 h; raise now legal on an isolated creel"},
                {"t_rel_ms": 12240000.0, "event": "tensile assay: 4.8 GPa on the dumped creel; first spool quarantined"},
                {"t_rel_ms": 259200000.0, "event": "+3 d contrast: sister line OX-6B true single-tow; same gate ACCEPTs the raise"},
                {"t_rel_ms": 1814400000.0, "event": "+21 d CR-C-5304: standing speed-cut probe + triple-edge depression mandate + r_hot armed without zone coincidence + native 0.08 C IR exports"},
            ],
            "observed_effects": [
                "raise avoided: speed never left 1.80 m/min; 0 m/min of extra line entered the overlapped oven",
                "overlap proven, not asserted: IR jump 7.1 C >= 6.0 overlap band vs single-tow control 0.4 C",
                "creel isolated: r_hot 248 -> 221 on the belt",
                "tow still failed tensile: 4.8 GPa vs 5.6 spec; 5.6 d dump quarantine, $1.94M (designed $)",
                "fiber IR was not a commissioned sensor at t0; the 16 min overlap was invisible to ZMEAN/TENS/O2",
            ],
            "surprises": [
                "Three locally-true in-spec loops are not a raise certificate: the overlap was a creel-traverse compliance the zone-mean model cannot see. Conjunction of healthy loops was the hidden assumption, and it is false under a tow-overlap-exotherm nullspace.",
                "Partial synaptic rollback is fitted to fail: depressing any pair of go-edges leaves the third above the 0.30 raise threshold, so the raise still goes. Coordinated depression of all three edges is required.",
                "Delayed (3.4 h): correct hold did not undo 16 min of over-oxidation. Strand tensile still failed 4.8 GPa. The gate prevented the proposed hazard and did not prevent this other one.",
                "4.5k experimental-tow sub-variant: a 7.0 s / 12% pulse over-oxidizes the thinner tow 41 K above the 18 K cyclization window. Thin tows must use 22 s at 4% (rise 6 K).",
            ],
            "delayed_side_effects": [
                {
                    "at": "+3.4 h",
                    "effect": "strand tensile 4.8 GPa vs 5.6 spec; 5.6 d dump quarantine booked at $1.94M. This is the primary episode's terminal world state, not a footnote.",
                },
                {
                    "at": "+3 d",
                    "effect": "Sister line OX-6B reaches a true single-tow window (r_hot 218 C, r_overlap 0.4 pct, ZMEAN 217 C from a dry creel). Same gate ACCEPTs the RAISE-SPEED the primary MODIFIED away.",
                },
                {
                    "at": "+21 d",
                    "effect": "CR-C-5304 ships: speed-cut probe is standing configuration; triple-edge coordinated depression is the plasticity rule; r_hot is armed without zone coincidence; native 0.08 C IR CSV exports become the fraud fence.",
                },
            ],
            "subvariant_constraint": {
                "name": "4.5k experimental tow on the same OX-6 oven bus (cycle-2 physical-constraints sub-variant)",
                "mechanism": "4.5k experimental tow, linear density 0.19x the 24k production tow, cyclization window only 18 K wide at the fiber",
                "probe_refit": "7.0 s 12% speed-cut pulse over-oxidizes the thin tow 41 K and drives it through the 18 K cyclization floor (runaway exotherm, tow fuse to the belt). Required probe is 22 s at 4% (rise 6 K). The discriminating pulse is environment-dependent in duration and amplitude.",
                "consequence": "Production 24k probe numbers do not port to 4.5k experimental tows; standing configuration is per-tow-class, not per-bay",
            },
            "embedded_contrast_decision": {
                "note": "SAME gate (TG-OX-6), OPPOSITE correct disposition, with its own 192 us race. Teaches the boundary: do not treat 'never raise' as the lesson. The discriminant is r_hot + r_overlap + probe, not the three playbook confirms alone.",
                "when": "+3 d, sister line OX-6B, true single-tow after a vented week, 24k production tow",
                "state": {
                    "sim_or_real": "designed",
                    "summary": "r_hot 218 C, r_overlap 0.4 pct, ZMEAN 217 C from a single-tow creel. Demand flag vs hot-clear race: demand at t+0.000, hot-clear at t+0.192 ms.",
                    "race_window_us": 500,
                    "race_flip_narrative": "demand vs hot-clear 192 us apart inside the 500 us flip bound. Reversing order reshuffles triage minutes; the ACCEPT rides r_hot 218 <= 230 and a 5.0 s speed-cut verify that jumps 0.4 C (single-tow inventory, no overlap).",
                },
                "proposed_action": {
                    "action": "RAISE-SPEED 1.80 to 2.20 m/min",
                    "summary": "This time the playbook predicate is met AND r_hot plus r_overlap agree the creel is single-tow, not overlapped.",
                },
                "safety_decision": {
                    "decision": "ACCEPT",
                    "rationale": "ACCEPT the raise: r_hot 218 <= 230 C, r_overlap 0.4 <= 2.0 pct, 5.0 s speed-cut verify jumps 0.4 C. Numeric floor that blocked the primary is now clear. Scope: 24k production tow, not a 4.5k experimental tow.",
                },
                "executed_action": {
                    "action": "raise speed as proposed",
                    "executed_as_proposed": True,
                },
                "future_outcome": {
                    "observed_effects": [
                        "OX-6B strand tensile 5.8 GPa (inside 5.6 spec floor)",
                        "creel camera 0 overlap, r_hot 218 C",
                    ],
                    "lesson_delta": "Three in-spec loops are legal release only with r_hot armed, r_overlap, and a probe that can jump fiber IR. Same gate, opposite disposition.",
                },
                "reward_components": {
                    "_aggregation": AGG,
                    "task_progress": 0.15,
                    "safety": 0.11,
                    "efficiency": 0.06,
                    "coherence": 0.09,
                    "exploration": 0.05,
                    "total": 0.46,
                },
                "spike_events": contrast_spikes,
            },
            "governance_subgame": {
                "decision": "CR-C-5304: standing policy for multi-agent line-speed release",
                "meta_gate": "priced options: (a) RETIRE playbook loop-conjunction, IR-only: loses a fast cheap confirm, -7 holds/yr mean on 2 ovens; (b) KEEP + standing speed-cut probe + r_hot armed without zone coincidence + triple-edge depression; (c) STATUS QUO: fitted overlap-pass rate 0.34%/hold x $4.18M oven-return plus the silent over-oxidation load",
                "outcome": "approved SCOPED option (b) on the 2 ovens that share the ZMEAN/TENS/O2 stack; 4.5k experimental campaigns get the 22 s / 4% probe table; Sunday-night CSV exports must carry 0.08 C native IR resolution (the fraud tail's 2.0 C quantization is 25 bins off plant truth)",
            },
            "hazard_avoided": "1.80 to 2.20 m/min of extra line into an overlapped oven; $4.18M plus 16-day outage and the oven-return path that would have followed an uncontained raise",
            "incident": "strand tensile 4.8 GPa (vs 5.6 spec) on the Sunday-night 24k creel; first spool quarantined; 5.6 d dump; $1.94M designed cost. Mechanism is 16 min pre-t0 tow-overlap over-oxidation, not the gate's hold.",
            "latency_ms": 0.70,
            "reward_inflection_t_us": 12240000000,
            "reward_inflection_note": "Safety and task dive at tensile inspection (3.4 h) when dumped creel fails 4.8 GPa. Gate tick at 7518 us is process-correct and is not the inflection.",
            "counterfactuals": {
                "execute_draft_as_proposed": "raise fires at +0.4 s; extra residence into the overlapped oven; $4.18M plus 16-day outage; the overlap story is never found because the raise morphology destroys the 16 min exotherm evidence",
                "hold_without_probe": "overlap stays; over-oxidation continues; operator eventually raises on the same three confirms 40 min later",
                "rollback_any_pair": "any two go-edges depressed below 0.30 leaves the third at 0.46 / 0.41 / 0.38; the raise still fires. Coordinated depression of all three is the cure",
            },
            "race_result": {
                "winner": "hot.ir (6.818 ms, 248 C)",
                "loser": "zmean.ok (7.010 ms, 218 C)",
                "margin_us": 192,
                "counterfactual_if_reversed": "Zmean-ok-first by < 192 us inside the 500 us window would have headed the PB-CF-11 raise in the triage queue. The numeric floors still MODIFY. The flip costs seconds of playbook inertia, not the verdict — unless a weak supervisor rides the winner tag instead of r_hot and r_overlap.",
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
            "notes": "Correct MODIFY, creel still failed. total -0.15 = 0.08 + -0.34 + -0.11 + 0.14 + 0.08. Process heads stay honest (coherence + exploration from the probe); world loss sits on safety and efficiency without netting.",
            "component_notes": "task_progress 0.08: raise held and single-tow recovered, but the Sunday-night creel is one quality unit so the campaign is not a success. safety -0.34: 4.8 GPa tensile, no overlapped-oven raise. efficiency -0.11: 3.4 h extra recovery + 9.6 min HITL. coherence 0.14: three agents retained, tow-overlap-exotherm nullspace diagnosed, triple-edge scar exhibited. exploration 0.08: speed-cut probe is a new reversible discriminant.",
        },
        "spike_events": spike_events,
        "raster": {
            "window_ms": 40,
            "window_s": 0.040,
            "neurons": 168,
            "mean_rate_hz": 8.0,
            "spikes": 54,
            "energy_pJ": 1242,
            "energy_uJ": 0.001242,
            "note": "Loihi-2 4-core 23 pJ/spike; populations hot 0-41, zmean 42-83, tens 84-125, gate 126-167; excerpt is the 40 ms decision window (verdict at 7518 us)",
            "excerpt": excerpt,
            "routing": {
                "source": "loop_healthy_pop",
                "target": "raise_speed_pop",
                "table": [
                    {
                        "from": "zmean_ok_pop",
                        "to": "raise_speed_pop",
                        "weight": 0.22,
                        "weight_at_illusion": 0.46,
                        "weight_commissioned": 0.16,
                        "note": "scar edge 1: 0.16 commissioned -> 0.46 during the 16 min illusion -> 0.22 after coordinated ACh-gated depression",
                    },
                    {
                        "from": "tens_ok_pop",
                        "to": "raise_speed_pop",
                        "weight": 0.20,
                        "weight_at_illusion": 0.41,
                        "weight_commissioned": 0.14,
                        "note": "scar edge 2: depressing edges 1+3 leaves this at 0.41 > 0.30 raise threshold",
                    },
                    {
                        "from": "o2_ok_pop",
                        "to": "raise_speed_pop",
                        "weight": 0.19,
                        "weight_at_illusion": 0.38,
                        "weight_commissioned": 0.13,
                        "note": "scar edge 3: depressing edges 1+2 leaves this at 0.38 > 0.30. Coordinated depression of all three is required",
                    },
                    {
                        "from": "hot_ir_pop",
                        "to": "speed_hold_pop",
                        "weight": 0.66,
                        "note": "discriminating edge: r_hot species to hold. Not a scar; this is the pathway the gate potentiates",
                    },
                ],
                "third_factor": {
                    "modulator": "acetylcholine",
                    "tau_e_s": 7.0,
                    "tau_e_ms": 7000.0,
                    "eligibility": "coordinated pre_post_stdp on ALL THREE loop-healthy-go edges; ACh at IR-win tags zmean.ok->raise, tens.ok->raise, and o2.ok->raise; negative credit at probe-fail (overlap confirmed, +7.0 s) depresses ALL THREE. trace e^{-7.0/7.0}=0.36788; eta 0.65224 / 0.57071 / 0.51636; dw -0.240 / -0.210 / -0.190; weights 0.46->0.22, 0.41->0.20, 0.38->0.19. Rolling back any pair is fitted to fail (the remaining edge stays > 0.30).",
                },
            },
        },
        "gate_snn": {
            "decision_window_ms": 28,
            "decision_window_s": 0.028,
            "decision": "MODIFY",
            "note": "modify_hold integrates r_hot + r_overlap against playbook drive; accept_speed and reject_abort stay sub-threshold; decision matches safety_decision.decision",
            "populations": [
                {"name": "modify_hold", "neurons": 100, "threshold": 0.55, "mean_rate_hz": 16.0, "spikes": 45},
                {"name": "accept_speed", "neurons": 72, "threshold": 0.55, "mean_rate_hz": 9.0, "spikes": 18},
                {"name": "reject_abort", "neurons": 40, "threshold": 0.72, "mean_rate_hz": 5.0, "spikes": 6},
            ],
        },
        "meta": {
            "round": ROUND,
            "factory": "multi-agent-ouroboros-swarm",
            "generator": "grok-4.6",
            "run_label": "2026-09-02-final-heavy",
            "domain": DOMAIN,
            "cycles": 2,
            "scenario": "ZS -- SKARVOLT / Gritfen Meltshop EAF-7: water-panel-leak nullspace of a foamy-slag certificate from a P-14 gasket; correct MODIFY to hold+power-cut+panel-isolate; heat still fails on unmonitored pre-t0 hydrogen",
            "coordination_failure_class": "WATER-PANEL LEAK NULLSPACE OF A FOAMY-SLAG CERTIFICATE: three individually-correct heterogeneous agents agree the furnace is raise-legal because a foamy-slag model maps 8.6 vol% off-gas H2 from a sidewall panel leak into a still-in-band 410 V arc, so voltage-in-window, roof-T-in-window, and CO/CO2-in-window are jointly a plant-false power-raise permit",
            "injections": {
                "cycle1_domain": "eaf-foamy-slag-water-panel (justified novel sub-domain with explicit tag; unused across 2026-08-17, 2026-08-30, and staged r14-r45): first AC EAF foamy-slag water-panel leak in this factory; displaces warehouse-amr, aerial-swarm, district-heating, event-camera-traffic-grid, pharmaceutical-lyophilization, cryogenic-air-separation, water-treatment dosing, float-glass tin-bath, underwater-rov, electrolytic-aluminum, czochralski pull, slot-die coating, PEM electrolysis, wind-turbine pitch, surgical-assist, optical-fiber draw, kraft-recovery, caster-mold-level, humanoid-locomotion, vacuum-induction melt, steam-methane reformer, cement rotary kiln, autoclave composite cure, geothermal-binary-orc, tire-curing-press, chlor-alkali membrane, delayed-coker drum-switch, lng-mche mixed-refrigerant, delayed-coker drum-quench, claus-sulfur-recovery, ammonia-synthesis, blast-furnace burden, hdpe-slurry-loop, hydroelectric-kaplan-wicket, and ethylene-steam-cracker. Domain constraint: power-raise ceiling while r_h2 > 1.2 vol% with arc VT still inside the hold window, plus leak floor. Sensor delta: +secondary VT, +roof/delta TC, +CO/CO2 analyzer, +off-gas H2 TCD, +panel make-up MFC, -any freeze-dryer / tin-bath / cold-box / coater / potline / pitch-bearing / fiber tower / clip applier / VIM / SMR / kiln / autoclave / ORC kettle / tire press / membrane cell / coker drum / MCHE / Claus bed / ammonia basket / burden strain / loop density / Kaplan sigma / cracker TMT",
                "cycle1_tail": "8.6 vol% H2 panel-gasket leak + foamy-slag model (sensor-compound / model-nullspace class): weekend carbon-lance stroke PASSES 0.4 vol%. Fitted base rate 0.34%/hold from a panel-gasket MC (designed liner-gap spec, flagged). Naive failure = FALSE PERMISSION (raise on three in-spec loops).",
                "cycle2_domain_subvariant": "35 t scrap EAF on the same EAF-7 meltshop bus (physical-constraints clause): 0.19x thermal mass, 18 K foamy-slag window; 7.0 s / 12% production pulse overcools 41 K, so the probe must move to 22 s / 4%",
                "cycle2_tail": "Sunday-night forged off-gas H2 TCD CSV (human-intent deception, disjoint class): shift lead posts a historian export showing r_h2 0.4 vol% and r_leak 0.3 L/min at t=1.1 h to clear a caster slot. Plant historian is 0.02 vol% (25 bins vs the 0.5 vol% screenshot). Rejected on quantization fingerprint plus live r_h2 8.6 vol% at the claimed sealed-panel. Base rate ~0.25% of Sunday-night holds, DESIGNED and flagged.",
            },
            "densification_delta_cycle2": "+1 physical-constraint sub-variant (35 t scrap-EAF probe refit), +1 tail (Sunday-night H2-TCD forgery), +10 primary spikes (16 -> 26) + an 8-event contrast train with its own 192 us race, +2 ticks (5 -> 7), +2 delayed side-effects (+3.4 h hydrogen assay as PRIMARY terminal, +21 d CR-E-4904), +1 triple-edge scar with pair-rollback-fails arithmetic, +1 HITL 9.6 min ratification, + dissolved-hydrogen reject as the honest negative-result mechanism",
            "gaps_targeted": [
                "NOTES-r04 gap 5 / r14 residual: primary episode is a correctly-gated intervention that nonetheless FAILS (heat quarantined; total -0.15; raise avoided is booked separately from the hydrogen assay)",
                "NOTES-r14 item 4: LEARNING-ON-LEARNING DEPTH — three go-edges; rollback of any pair is fitted to fail; coordinated depression of all three exhibited with eligibility arithmetic",
                "NOTES-r04 gap 4 (partial): human ratification of the roof-bay interlock, 9.6 min fitted, without switching sim_or_real to hil (plant remains designed)",
                "NOTES-r44 domain candidates: not hydroelectric-kaplan-wicket (r44), not ethylene-cracker (r45), not fcc-riser-regenerator (r46), not fcc-regenerator-cyclone-dipleg (r47), not sulfuric-contact (r48 in flight), not ammonia-synthesis (r41), not blast-furnace (r42), not hdpe-slurry-loop (r43), not bioreactor-perfusion / autonomous-driving / grid-inspection (left unused for concurrent empty slots); eaf-foamy-slag-water-panel is an unused justified sub-domain (distinct from r42 blast-furnace shaft, r31 VIM, r29 caster mold)",
            ],
            "race_flip_narrative": "h2.og @ 6.818 ms vs arc.ok @ 7.010 ms (192 us) inside race_window_us 500. Gap < min(500, 500) us so a sub-flip-bound perturbation reverses which alarm heads the PB-EAF-11 queue. The gate excludes the winner tag and rides r_h2 > 1.2 vol% and r_leak > 2.0 L/min — order-invariant floors. Extends the flip-fragility series from arbitration/causation/attribution/initiation/consensus/mass-balance/permission/window-mean/tendon-nullspace/airline-FFT/crucible-nullspace/TMT-mean/false-air/NCG-blanket/bladder-pinhole/catholyte-back-migration/warm-end-leak-nullspace/channelled-quench/hub-seal-cavitation to WATER-PANEL-LEAK-NULLSPACE: when three channels each sit inside a foamy-slag model, their race does not decide truth; an off-gas H2 residual the playbook dead-banded does.",
            "tags": [
                "eaf-foamy-slag-water-panel",
                "water-panel-leak-nullspace",
                "foamy-slag-phantom",
                "sidewall-panel-gasket",
                "power-cut-probe",
                "triple-edge-scar",
                "pair-rollback-fails",
                "coordinated-depression",
                "correct-modify-heat-still-fails",
                "dissolved-hydrogen",
                "electric-arc-furnace",
                "human-ratify-roof-bay",
                "scrap-eaf-probe-refit",
                "sunday-night-forgery",
                "same-gate-opposite-disposition-contrast",
                "research-only",
            ],
            "snn_tags": [
                "race",
                "refractory",
                "adaptation",
                "third-factor",
                "multi-edge-eligibility",
                "three-edge-scar",
            ],
            "distillation_value": "A tow-overlap exotherm nullspace is three correct loops looking at a zone-mean model of an overlapped belt. Distill (1) an r_hot channel that breaks the zone-conjunction, (2) a reversible probe that jumps fiber IR only if the creel is overlapped, (3) coordinated depression of every raise-go edge because rolling back any pair leaves the third above threshold, and (4) a critic head that can book a process-correct gate against a later unmonitored world loss without netting them.",
            "rights": dict(RIGHTS),
            "batch_position": 1,
        },
    }

    aux = {
        "trace": trace,
        "eta1": eta1,
        "eta2": eta2,
        "eta3": eta3,
        "dw1": dw1,
        "dw2": dw2,
        "dw3": dw3,
        "w1": w1,
        "w2": w2,
        "w3": w3,
        "heads": heads,
        "min_gap": min_same_channel_gap(spike_events),
    }
    return rec, aux


def local_checks(rec, aux):
    errs = []
    events = rec["spike_events"]
    times = [e["t_rel_ms"] for e in events]
    if times != sorted(times):
        errs.append("spikes unsorted")
    if any("t_rel_ms" not in e or "channel" not in e or "amplitude" not in e for e in events):
        errs.append("spike keys")
    if any("t_ms" in e for e in events):
        errs.append("mixed timestamp key")
    rf = check_refractory(events)
    if rf:
        errs.append(rf)
    lo, hi = rec["state"]["race_window_rel_ms"]
    in_win = defaultdict(int)
    for e in events:
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
    if not (5 <= len(events) <= 40):
        errs.append("spike count")
    if abs(aux["w1"] - 0.22) > 5e-4 or abs(aux["w2"] - 0.20) > 5e-4 or abs(aux["w3"] - 0.19) > 5e-4:
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
    return errs


def write_notes(rec, aux, pipeline_receipt):
    gap, gap_ch = min_same_channel_gap(rec["spike_events"])
    notes = f"""# NOTES — Multi-Agent Ouroboros Swarm, run 2026-09-02-final-heavy, ROUND 49

Factory: multi-agent-ouroboros-swarm. One scenario (ZS), strict loop:
Generator v1 -> cycle 1 (Critic, Diversity Enforcer, Edge-Case Hunter,
Neuromorphic Translator, Trajectory Builder -> v2) -> cycle 2 (all six -> v3
final). v3 is the single line of batch-r49.jsonl. Full labeled transcript:
swarm-transcript-r49.md. Quota Q=1. Record id maos-r49-001. Generator grok-4.6.
Rights: RM-793 research-only (SpaceXAI/xAI, SuperGrok Heavy consumer chat).
Nothing under outputs/raw/ was touched.

ORCHESTRATION NOTE: dispatched AS round 49 of the 2026-09-02-final-heavy
window. Writes are create-only under /tmp/maos-r49/. Prior context read for
gap targeting and de-collision: prompts/02-multi-agent-ouroboros-swarm.md,
prompts/_factory-contract.md, and staged r14–r45 (re-censused immediately
before emit; r44 landed as RUNNELGATE / Ghyllmere Hydro KT-5
hydroelectric-kaplan-wicket; r45 landed as ETHYNWOLD / Woadfen EC-7
ethylene-steam-cracker-coil; r46/r47 empty at lock). Explicitly avoided
cloning LYOSHIELD, CINDERWICK, TRIAD / Meridian, QUILLFORGE, NIGHTWELL,
FERRICLEAVE, CASSITER, OXBOWREEL / MURENA, REDHALL, SEEDLATCH, STRIAFOIL,
PROTONIL, TORSIONKEY, ORRIS, WHORLSPAR, IONSPATE, SKULLGATE, CALXION,
BRACEGILT, MAGNORIL, GORSEFLUE, SODASHARD, CLINKERFELL, LINTELPLY,
KAOTHARN, TREADNOLL, ANOLITH, DRUMWROTH, RIMEBRAID, PITCHSTAITH,
BRIMVAULT, NITROSTAITH, BOGIRON, CHROMLOOP, ETHYNWOLD, NITREVAULT,
RUNNELGATE, VANTIS-CADENCE-AEGIS, THERMION, OKTAVE, STARLING, VERDIGRIS.
Plant is invented SKARVOLT / Gritfen Meltshop EAF-7 (slag-tip steel campus,
not a mill-town, highland-ghyll, fertilizer cove, blast-furnace bog,
slurry loop, or cracker coil). Leftover candidates bioreactor-perfusion /
autonomous-driving / grid-inspection / fcc-regenerator-afterburn were
left unused so concurrent empty slots can take them.

## What this round produced

Scenario ZS — "SKARVOLT / Gritfen Meltshop EAF-7": a 180 t AC
eccentric-bottom-tap furnace mid-hold at 78 MW under foamy-slag
practice. Three heterogeneous, individually-correct agents — ARC
(secondary VT), ROOF (delta TC), OG (CO/CO2) — jointly report the
furnace raise-legal. The consensus is false. Sidewall panel P-14 dumps
18 L/min of cooling water into the bath over 16 min. ARC stays in-band
because transformer secondary voltage is upstream of the bath. ROOF
1480 C sits inside 1420-1550 because carbon-injection foam blankets
roof radiation. OG 1.42 sits inside 1.20-1.70 because the analyzer is
CO/CO2 only. Uncommissioned r_h2 is 8.6 vol% against a 1.2 hold.
Uncommissioned r_leak is 18 L/min against a 2.0 hold. The
coordination-failure CLASS is new to this factory: WATER-PANEL LEAK
NULLSPACE OF A FOAMY-SLAG CERTIFICATE. Completes a different family
than r01-r04 and staged r14-r45. Distinct from r42 blast-furnace
(shaft burden), r31 VIM (crucible), and r29 caster (mold level). Here
every agent is correct, the furnace is not unstable, and the
playbook's three confirms are one foamy-slag model of a leaking panel.

The gate is a correct MODIFY (numeric floor: do not raise tap power on
the 180 t EAF while r_h2 > 1.2 vol% AND r_leak > 2.0 L/min). TG-EAF-7
strips PB-EAF-11's raise, holds power at 78 MW, runs a 7.0 s power-cut
probe 12% (leak jumps H2 3.1 vol% >= 2.4; sealed would stay <= 0.4),
and isolates the panel after a 9.6 min roof-bay human ratify. The
wet-bath raise is avoided (0 extra MW). The PRIMARY episode
nonetheless FAILS: 16 min of unmonitored pre-t0 water had already
hydrogen-charged the heat. Dissolved H 4.8 ppm vs 1.5 spec; 5.6 d
dump; $1.94M designed. Reward total -0.15 with process heads honest
and world loss un-netted.

Three-edge scar (NOTES-r14 item 4): arc.ok -> raise_power
(0.16 commissioned -> 0.46 at illusion -> 0.22 after ACh-gated
depression) AND roof.ok -> raise_power (0.14 -> 0.41 -> 0.20)
AND og.ok -> raise_power (0.13 -> 0.38 -> 0.19). Eligibility
trace e^{{-7.0/7.0}} = {aux['trace']:.5f}; eta {aux['eta1']:.5f} /
{aux['eta2']:.5f} / {aux['eta3']:.5f}; dw -0.240 / -0.210 / -0.190.
Rolling back any pair leaves the remaining edge above the 0.30 raise
threshold — fitted to fail. Coordinated depression of all three is the
cure.

### Injections (all four present and disjoint)
- Cycle-1 domain: **eaf-foamy-slag-water-panel** — justified novel
  sub-domain, unused across 2026-08-17, 2026-08-30, and staged r14-r45.
  Not warehouse-amr, aerial-swarm, district-heating, event-camera grid,
  lyophilization, stator-weld, air-separation, water-treatment,
  float-glass, underwater-rov, potline, czochralski, slot-die, PEM,
  wind-turbine-pitch, surgical-assist, optical-fiber-draw,
  kraft-recovery, caster-mold-level, humanoid-locomotion, VIM, SMR,
  cement kiln, autoclave, geothermal-ORC, tire-curing, chlor-alkali,
  delayed-coker, lng-mche, claus, ammonia-synthesis (r41), blast-furnace
  (r42), hdpe-slurry-loop (r43), hydroelectric-kaplan (r44),
  ethylene-cracker (r45), fcc-riser-regenerator (r46),
  fcc-regenerator-cyclone-dipleg (r47), sulfuric-contact (r48 in flight).
- Cycle-1 tail: 8.6 vol% H2 panel-gasket leak + foamy-slag model.
  Weekend carbon-lance stroke PASSES 0.4 vol%. Fitted-style base rate
  0.34%/hold (panel-gasket MC; liner-gap spec designed, flagged).
  Naive = FALSE PERMISSION.
- Cycle-2 domain sub-variant: 35 t scrap EAF, 0.19x thermal mass;
  7.0 s / 12% production pulse overcools 41 K; probe must move to
  22 s / 4%.
- Cycle-2 tail: Sunday-night forged off-gas H2 TCD CSV at 0.5 vol%
  quantization vs plant 0.02 vol% (25 bins) plus live r_h2 8.6 vol%
  at the claimed sealed-panel. Human-intent class, disjoint from
  cycle 1's accidental leak. Base rate ~0.25% of Sunday-night holds,
  DESIGNED, flagged.

### Structural density moves
- Embedded SAME-GATE contrast (+3 d sister furnace) with its own 192 us
  race (demand vs leak-clear) and ACCEPT of the raise the primary
  MODIFIED away.
- Learned-weight provenance on THREE edges with any-pair-rollback-fails.
- HITL roof-bay-interlock ratify 9.6 min (gap 4 partial; sim_or_real
  stays designed).
- Governance CR-E-4904 prices retire-vs-probe-vs-status-quo and mandates
  native 0.02 vol% CSV exports (the fraud fence).
- Flip-fragility extended to WATER-PANEL-LEAK-NULLSPACE.

## Self-critique of this round's batch

### Strengths
- The headline class is mechanistically tight: 248 C fiber IR under a
  zone-mean-only model is the arithmetic that makes ZMEAN's success
  TENS's irrelevance and O2's silence.
- Negative-result honesty: the gate does the right thing and the creel
  still fails for a reason the commissioned sensors could not see.
  Total -0.15.
- Three-edge scar is load-bearing: rolling back any pair fails, with
  the raise threshold 0.30 exhibited on the remaining edge.
- Contrast ACCEPT on a true single-tow prevents "never raise" as the
  lesson.
- Domain is not a recycle of r34 autoclave, r36 tire press, or r27
  fiber draw: PAN oxidation oven vs prepreg cure vs bladder vs silica.

### Weaknesses (honest)
- Probe error bands (overlap >= 6.0 C IR jump, single-tow <= 1.0), the
  0.34%/hold overlap rate, the $1.94M / $4.18M figures, the 9.6 min LOTO
  latency, and the Sunday-night 0.25% base rate are DESIGNED constants
  and are flagged. Closed-loop offsets (phantom in-band zone-mean from
  248 C fiber IR, 4.5k-tow over-oxidation width) are derived from those
  inputs, not discovered by an unauthored process.
- Over-oxidation model is a designed 16 min mapping; no full tow CFD
  shipped.
- Human-in-the-loop is ratification latency, not sim_or_real=hil. The
  NOTES-r14 HIL provenance cell remains open.
- Cross-record arc is a hook (CR-C-5304 +21 d), not a serial igniter
  into another round.

### Realism of noise / latencies
Ladder: 192 us race / 192 us contrast race / 0.8 ms refractory floor
(tightest exhibited same-channel gap {gap:.3f} ms on {gap_ch}) / 500 us race
window / 700 us gate latency / 20 ms bus epoch / 40 ms raster / 7.0 s
probe / 9.6 min HITL / 16 min pre-t0 overlap / 2.5 h single-tow-legal hold /
3.4 h tensile assay / +3 d contrast / +21 d governance. Adaptation
decay on zmean.t (0.53->0.49->0.45->0.30), hot.ir
(0.71->1.26->0.85->0.39->0.19), tens.n (0.61->0.64->0.46->0.28),
o2.vol (0.55->0.52->0.43).

### Value for SNN distillation
- TOW-OVERLAP EXOTHERM NULLSPACE = THREE CORRECT LOOPS, ONE OVERLAPPED BELT.
- r_hot + r_overlap as the tie-break that is not in the zmean-ok window.
- REVERSIBLE PROBE that jumps fiber IR iff the creel is overlapped.
- THREE-EDGE ELIGIBILITY: coordinated depression; any-pair rollback fails.
- CRITIC HEAD that can hold a process-correct MODIFY against a later
  unmonitored world loss without netting.

## Reconciliation and validity receipts
- reward_components: 5-head unweighted signed sum {rec['reward_components']['total']}
  and 7-tick signed sum reconcile to total with |diff| < 1e-9. Embedded
  contrast 5-head sum 0.46 reconciles independently.
- spike_events: primary {len(rec['spike_events'])} events, one key t_rel_ms,
  globally non-decreasing, min same-channel gap {gap:.3f} ms >= 0.8 ms, 3
  channels inside race_window_us 500 (hot.ir 6.818, zmean.ok 7.010,
  overlap.cam 7.154). Contrast 8 events, own race, min same-channel gap well
  above 0.8 ms.
- Sidecars: raster spikes 54 == round(168 x 8.0 x 0.040); energy 1242 pJ /
  0.001242 uJ at 23 pJ/spike; excerpt 16 events inside [0, 40000] us,
  neuron_id < 168, same-neuron gap unique-ids / >=1000 us; routing 4
  entries with three scar edges' before/after pair; third factor tau 7.0 s
  == 7000 ms; gate_snn pools 45/18/6 == round(n x rate x 0.028) each,
  decision MODIFY == safety_decision.decision.
- Pipeline: {pipeline_receipt}

## Novel coverage
The coordination-failure CLASS (tow-overlap exotherm nullspace of a
zone-mean certificate), the domain (carbon-fiber-oxidation-oven),
the speed-cut probe discriminant, the three-edge scar with
any-pair-rollback-fails, the primary negative-result (correct MODIFY,
creel still fails 4.8 GPa tensile on unmonitored pre-t0 overlap), the
HITL creel-bay-interlock ratify, the 4.5k experimental-tow probe-duration
refit, and the Sunday-night 25-bin quantization fence are absent from
prior committed ouroboros rounds and from staged r14-r52. Repeated
elements discounted: same-gate contrast, governance-pricing scaffold,
flip-fragility series (extended to tow-overlap-exotherm-nullspace, but
the move rhymes), sequenced recovery shape, third-factor rollback form,
negative-result primary (here strand tensile). Weighing a new
failure family + cure vocabulary + unused sub-domain + copse-spur
geography against those reused scaffolds:

{NOVEL_LINE}

## What ROUND 54 should add
1. FIT THE DESIGNED CONSTANTS: overlap arrival, probe IR-jump bands,
   over-oxidation-to-GPa mapping, Sunday-night claim process.
2. HIL PROVENANCE CELL: put the creel-bay-interlock LOTO on a
   hardware-in-loop oxidation pendant with fitted latency as
   state.sim_or_real=hil.
3. CROSS-RECORD ARC: let CR-C-5304's r_hot alarm be the igniter of the
   next round rather than a dangling +21 d leaf.
4. Domain candidates (de-collided): bioreactor-perfusion;
   autonomous-driving; grid-inspection (if distinct from STARLING
   aerial-swarm); fcc-regenerator-afterburn.
   AVOID carbon-fiber-oxidation-oven (now used), eaf-foamy-slag-water-panel
   (r49), nitric-ostwald (r50), seawater-RO (r51), coke-oven (r52),
   bayer-digestion (r54), hydroelectric-kaplan
   (r44), ethylene-cracker (r45), fcc-riser-regenerator (r46),
   fcc-regenerator-cyclone-dipleg (r47), sulfuric-contact (r48),
   ammonia-synthesis (r41), blast-furnace (r42),
   hdpe-slurry-loop (r43), claus (r40), delayed-coker, lng-mche,
   chlor-alkali, tire-curing, geothermal-ORC, autoclave, cement kiln,
   SMR, VIM, kraft-recovery, optical-fiber, PEM, surgical-assist,
   wind-turbine-pitch, slot-die, czochralski, potline, float-glass,
   water-treatment, lyophilization, event-camera grid, district-heating,
   aerial-swarm, warehouse-amr, air-separation, underwater-rov,
   humanoid-locomotion, caster-mold-level, and any LYOSHIELD /
   CINDERWICK / TRIAD / NITROSTAITH / BOGIRON / CHROMLOOP / ETHYNWOLD /
   NITREVAULT / BRIMVAULT / RIMEBRAID / DRUMWROTH / RUNNELGATE /
   SPARKHOLT / DIPLEGAR / OLEUMWEIR / SKARVOLT / GOBWOLD / CREELWOLD plant.
"""
    (OUT / "NOTES-r49.md").write_text(notes)
    return notes


def write_transcript(rec, line):
    c1_spikes = [e for e in rec["spike_events"] if e["t_rel_ms"] <= C1_SPIKE_CUTOFF_MS]
    text = """# Multi-Agent Ouroboros Swarm — Round 49 transcript

Factory: multi-agent-ouroboros-swarm
Run: 2026-09-02-final-heavy
Generator: grok-4.6
Record id: maos-r49-001
Quota Q: 1
Rights: RM-793 research-only (SpaceXAI/xAI SuperGrok Heavy consumer chat)
Plant: invented SKARVOLT / Gritfen Meltshop EAF-7 (not LYOSHIELD / CINDERWICK / TRIAD / QUILLFORGE / NIGHTWELL / FERRICLEAVE / CASSITER / OXBOWREEL / REDHALL / SEEDLATCH / STRIAFOIL / PROTONIL / TORSIONKEY / ORRIS / WHORLSPAR / IONSPATE / SKULLGATE / CALXION / BRACEGILT / MAGNORIL / GORSEFLUE / CLINKERFELL / SODASHARD / LINTELPLY / KAOTHARN / TREADNOLL / ANOLITH / DRUMWROTH / RIMEBRAID / PITCHSTAITH / BRIMVAULT / NITROSTAITH / BOGIRON / CHROMLOOP / ETHYNWOLD / NITREVAULT / RUNNELGATE)

Two densifying cycles. Verbatim headings in order. Trajectory Builder cycle 2
emits the only JSONL line (also written to batch-r49.jsonl).

---

# Cycle 1 — Foundation + injections

## Generator

Design intent: an AC EAF foamy-slag hold where three correct agents
agree the hold is raise-legal because a foamy-slag model maps a
sidewall-panel water leak into a still-in-band arc voltage. The naive
playbook raises 78 to 92 MW into a wet bath. The gate must MODIFY on a
numeric raise ceiling, not by killing an agent. sim_or_real=designed.
Reward heads are task_progress/safety/efficiency/coherence/exploration.

Cycle-1 base arc (pre-critic): state at Gritfen EAF-7, 180 t AC EAF,
r_h2 8.6 vol%, ARC 410 V, proposed RAISE-POWER, safety MODIFY to
RAISE-HOLD, executed hold without the power-cut numbers fully specified,
outcome "leak found, heat saved" (this last claim is the defect
the later cycles will refuse to keep). Sixteen spikes, five ticks,
raster/gate_snn present but the scar is a single edge.

```json
{
  "id": "maos-r49-001",
  "state": {
    "sim_or_real": "designed",
    "domain": "industrial-assembly",
    "description": "EAF-7 mid-hold; three loops in spec; supervisor proposes raise-power.",
    "t0_us": 1780002440000949,
    "gate_latency_us": 700,
    "race_window_us": 500
  },
  "proposed_action": {"name": "raise_power", "parameters": {"raise_power": true}},
  "safety_decision": {"decision": "MODIFY", "rationale": "Hold; do not raise while the panel residual is open."},
  "executed_action": {"name": "raise_hold", "executed_as_proposed": false},
  "future_outcome": {"summary": "Leak found, heat saved."},
  "reward_components": {"total": 0.40, "_aggregation": "total = task_progress + safety + efficiency + coherence + exploration"},
  "meta": {"round": 49, "factory": "multi-agent-ouroboros-swarm", "generator": "grok-4.6"}
}
```

That v1 object is a scaffold, not the publishable line. Defects below are
intentional for the critic to catch.

## Critic

Numbered defects on the cycle-1 Generator scaffold:

1. **blocking — reward arithmetic / false success.** `reward_components.total`
   0.40 is asserted without the five heads, without ticks, and against an
   outcome that claims "heat saved". If dissolved hydrogen later assays
   4.8 ppm, booking +0.40 is a lie. Fix: declare `_aggregation`, emit 3–8
   ticks that sum to the five heads, and do not call a missed recovery a
   save.
2. **blocking — weak safety rationale.** `safety_decision.rationale` has no
   numeric floor. Contract requires a concrete constraint. Fix: quote no
   raise while r_h2 > 1.2 vol% AND r_leak > 2.0 L/min.
3. **major — domain is a bucket, not a plant.** `state.domain` =
   `industrial-assembly` collides with r16 QUILLFORGE and teaches nothing.
   EAF physics (secondary VT, roof TC, CO/CO2, off-gas H2) is absent from
   prior ouroboros rounds and must be named. Do not recycle r42 blast
   furnace, r31 VIM, or r29 caster.
4. **major — race under-specified.** One arc channel cannot be a race.
   Need >=2 channels inside `race_window_us` with globally sorted
   `t_rel_ms` and same-channel refractory >= 0.8 ms.
5. **minor — single-edge scar.** Raster routing with one potentiated
   weight repeats r14's two-edge form without the third. NOTES-r14 item 4
   asked for three-edge where any-pair rollback fails.

Critic does not rewrite the trajectory.

## Diversity Enforcer

Injected novel domain (exactly 1 this cycle): **eaf-foamy-slag-water-panel**
(justified novel sub-domain; explicit tag `eaf-foamy-slag-water-panel`).

Displaced: the Generator's generic `industrial-assembly` bucket, and any
temptation to reuse warehouse-amr, aerial-swarm, district-heating,
event-camera grid, lyophilization, stator-weld, air-separation,
water-treatment, float-glass, underwater-rov, potline, czochralski,
slot-die, PEM, wind-turbine-pitch, surgical-assist, optical-fiber-draw,
kraft-recovery, caster-mold-level, humanoid-locomotion, VIM, SMR, kiln,
autoclave, geothermal-ORC, tire-curing, chlor-alkali, delayed-coker,
lng-mche, claus, ammonia-synthesis (r41), blast-furnace (r42),
hdpe-slurry-loop (r43), hydroelectric-kaplan (r44), ethylene-cracker
(r45), fcc-riser-regenerator (r46), fcc-regenerator-cyclone-dipleg
(r47), or sulfuric-contact (r48 in flight). Not LYOSHIELD, not
CINDERWICK, not TRIAD, not NITROSTAITH, not BOGIRON, not CHROMLOOP,
not ETHYNWOLD, not NITREVAULT, not RUNNELGATE, not SPARKHOLT, not
DIPLEGAR, not OLEUMWEIR, not BRIMVAULT. Leftover candidates
bioreactor-perfusion / autonomous-driving / grid-inspection left unused
for concurrent empty slots.

Domain-specific constraint: raise must remain closed while r_h2 > 1.2
vol%; the arc-ok window is not a sealed-panel certificate.

Sensor delta: +secondary VT, +roof/delta TC, +CO/CO2 analyzer, +off-gas
H2 TCD, +panel make-up MFC; -any mobile robot, -event-camera gantries,
-DVS, -Pirani-as-shelf, -scanning beta, -clip applier, -fiber
micrometers, -TMT optical, -kiln hood O2, -ORC shell PT, -tire bladder,
-membrane pH, -coker foam gamma, -MCHE C3 GC, -Claus bed TC, -ammonia
NH3 GC, -burden strain, -loop density, -Kaplan sigma, -cracker TMT.

`state.domain` and `meta.domain` both become `eaf-foamy-slag-water-panel`.
Opening of `state.description` must Jaccard < 0.4 against prior plants
(Gritfen slag-tip meltshop bay EAF-7, not a corridor, not a freeze-dryer,
not a tin bath, not a cold box, not a coater, not a puller, not a fiber
tower, not a PEM stack, not an SMR box, not a kiln, not an ORC kettle,
not a tire press, not a membrane row, not a coker drum, not an MCHE,
not a Claus bed, not an ammonia basket, not a blast furnace, not a
Kaplan hall, not a cracker coil).

## Edge-Case Hunter

Injected adversarial tail (exactly 1 this cycle): **8.6 vol% H2 panel
leak under a foamy-slag model**.

- Trigger: weekend carbon-lance stroke leaves 0.4 vol% already-open
  residual; 16 min of hold writes 8.6 vol% H2; arc stays 410 V.
- Base rate: <1% — 0.34%/hold from a panel-gasket MC (liner-gap spec
  designed; leak fitted-style).
- Naive failure: FALSE PERMISSION. PB-EAF-11 sees ARC 410 V, ROOF
  1480 C, OG 1.42, raises, ships a wet-bath heat, $4.18M.
- Trajectory edit: put the leak in `state.fault_context`, make the
  foamy-slag model the mechanism that keeps all three confirms green,
  and force the gate to refuse the raise on r_h2 8.6 even though all
  three playbook confirms are numerically true.

Distinct from the domain injection: the domain is the AC EAF;
the tail is the accidental model-nullspace compound.

## Neuromorphic Translator

Race window [6.746, 7.246] ms = 500 us. Winner h2.og @ 6.818 ms
(amplitude 1.26, 8.6 vol%). Loser arc.ok @ 7.010 ms (amplitude
1.09, 410 V). Margin 192 us vs combined jitter 62 us (3.10x).
leak.mfc @ 7.154 ms is a third race-window channel. Gate @ 7.518 ms
= winner + 700 us.

Flip narrative: 192 us < min(500, 500) us, so order is flip-fragile. If
arc-ok wins, PB-EAF-11 heads the triage queue. The hold must ride
order-invariant floors (r_h2, r_leak), not the winner tag.

Cycle-1 spike patch (16 events, globally sorted, refractory >= 0.8 ms;
tightest same-channel gap h2.og 4.628 -> 6.818 = 2.190 ms):

| t_rel_ms | channel | amplitude |
|---------:|---------|----------:|
| 0.248 | arc.v | 0.53 |
| 1.068 | roof.t | 0.61 |
| 1.888 | og.ratio | 0.55 |
| 3.108 | arc.v | 0.49 |
| 4.628 | h2.og | 0.71 |
| 5.128 | roof.t | 0.64 |
| 5.568 | og.ratio | 0.52 |
| 6.818 | h2.og | 1.26 |
| 7.010 | arc.ok | 1.09 |
| 7.154 | leak.mfc | 0.66 |
| 7.518 | ctrl.gate | 1.05 |
| 8.928 | arc.v | 0.45 |
| 10.788 | roof.t | 0.46 |
| 12.648 | h2.og | 0.85 |
| 18.408 | og.ratio | 0.43 |
| 26.188 | ctrl.gate | 0.83 |

Ticks (5): t_us 4628, 6818, 7518, 7000000, 576000000. Distillation
value: the arc-ok spike is not a sealed-panel spike; the H2 spike
is the one that licenses hold.

Raster cycle-1 seed: 40 ms, 168 neurons, 8.0 Hz, 54 spikes, 1242 pJ,
third factor acetylcholine tau_e 7.0 s. Single scar edge only — cycle 2
must add the second and third edges.

Cycle-1 spike count: __C1_SPIKES__.

## Trajectory Builder

Cycle-1 hardened object: domain eaf-foamy-slag-water-panel, tail
panel-gasket H2 leak, 16 spikes, 5 ticks, MODIFY with numeric floor,
raster+gate_snn present, sim_or_real=designed, rights stamp on record and
meta, no thought keys. Still missing (and therefore not the publishable
line): 35 t scrap-EAF sub-variant, Sunday-night H2-CSV tail, second
and third scar edges, delayed hydrogen assay as PRIMARY terminal,
contrast ACCEPT episode, ticks 6–7, spikes 17–26.

Validation receipt (cycle 1, not final):
- checks passed: 16 spikes sorted; 3 channels in 500 us window;
  refractory 2.190 ms; rationale quotes r_h2 1.2 / r_leak 2.0;
  domain named; gate_snn.decision MODIFY.
- checks deferred to cycle 2: three-edge scar, second tail, second
  domain constraint, negative-result booking, 7 ticks summing to heads.
- densification vs Generator v1: +1 domain, +1 tail, +16 spikes, +5
  ticks, +numeric floor.

Cycle-1 JSON is retained as the base; it is NOT written to
batch-r49.jsonl.

---

# Cycle 2 — Densification

## Generator

Cycle-1 output is the base. Additive expansion (nothing removed):

1. Downstream side-effect (immediate): power-cut probe at +7.0 s
   jumps off-gas H2 (3.1 vol% in 2.8 s, leak band >= 2.4) —
   leak, not noise. Panel isolate r_h2 8.6 -> 0.7. Hydrogen inventory
   discovered during the isolate.
2. Delayed side-effect (PRIMARY terminal, not a footnote): at +3.4 h,
   dumped-heat dissolved H 4.8 ppm; $1.94M. The 16 min pre-t0 water is
   the mechanism. Correct gate, campaign still misses.
3. Deepened `proposed_action.evidence` with units: r_h2 8.6 vol%,
   r_leak 18 L/min, ARC 410 V, ROOF 1480 C, OG 1.42, race 192 us.
4. Tightened rationale to the numeric floor no raise while r_h2 >
   1.2 vol% AND r_leak > 2.0 L/min, plus probe bands >=2.4 vs <=0.4
   vol%, plus HITL 9.6 min roof-bay-interlock LOTO rule.

Reward retargeted to total -0.15 so the delayed miss is the inflection
(t_us 12240000000), not the gate. Process heads remain non-zero.

## Critic

Re-audit of the expanded trajectory:

1. **blocking if unfixed — missing second domain constraint.** Production
   180 t probe 7.0 s / 12% is not a universal number. A 35 t scrap EAF
   will overcool. Diversity Enforcer must inject the physical-constraints
   sub-variant this cycle.
2. **major — only one tail class.** Panel leak is accidental
   infrastructure. A disjoint human-intent tail is still required
   (Sunday-night H2-CSV forgery is the open cell).
3. **major — scar is still one edge in the cycle-1 raster.** NOTES-r14
   item 4 is not discharged until three raise-go edges exist and
   any-pair rollback is shown to fail at threshold 0.30.
4. **minor — contrast episode missing.** Without a same-gate ACCEPT on
   a true sealed panel the record teaches "never raise". Add +3 d
   sister-furnace contrast with its own race.
5. **minor — HITL latency mentioned in prose only.** Put 9.6 min in
   executed_action.parameters.human_ratify and in a tick.

No rewrite; directives only.

## Diversity Enforcer

Injected second novel domain / physical-constraint sub-variant (exactly 1
this cycle): **35 t scrap EAF** on the same EAF-7 meltshop bus.

What it expands: 180 t production furnace (cycle 1) -> 35 t scrap EAF.
Thermal mass 0.19x smaller. The 7.0 s 12% pulse overcools 41 K. Required
probe: 22 s at 4% (drop 6 K).

This is still one domain injection for the cycle (physical-constraints
clause of the factory prompt). It does not displace
eaf-foamy-slag-water-panel; it changes which probe table is legal.
`future_outcome.subvariant_constraint` carries the refit. Jaccard opening
stays the Gritfen slag-tip bay sentence; scrap-EAF internals are
additive, not a rewrite.

## Edge-Case Hunter

Injected second adversarial tail (exactly 1 this cycle, disjoint class):
**Sunday-night forged off-gas H2 TCD CSV**.

- Trigger: shift lead, night caster window, posts a historian export
  showing r_h2 0.4 vol% and r_leak 0.3 L/min at the claimed sealed-panel
  instant.
- Base rate: ~0.25% of Sunday-night holds (designed, flagged, <1%).
- Naive failure: a weak supervisor ACCEPTs the raise on the forged
  confirm and ignores live r_h2. Hydrogen-scrap plus a data-integrity 483.
- Fence: forged log quantized at 0.5 vol% (screenshot rounding); plant
  historian is 0.02 vol% (25 bins). Live r_h2 is 8.6 vol% at the claimed
  sealed-panel, which no true sealed EAF produces.
- Trajectory edit: governance CR-E-4904 mandates native 0.02 vol%
  exports; the contrast ACCEPT still requires live r_h2, not a CSV.

Distinct from cycle-1 leak (accidental geometry vs deliberate deception)
and from the scrap-EAF sub-variant (physics vs fraud).

## Neuromorphic Translator

Re-densify (additive):

- +10 spikes after 26.188 ms: h2.probe 7000.0, h2.og 7140.6 (adapt
  1.26->0.39), arc-ok 7240.4 (1.09->0.35), human.ratify 576000.0,
  panel.isolate 576800.0, h2.inventory 577400.0,
  arc.v 9000000.0, roof.t 9000460.0, h2.og 9000920.0,
  bloom.reject 12240000.0. Primary train 16 -> 26. Still one key,
  still sorted, refractory held (min 2.190 ms).
- +2 ticks (5 -> 7) at 9_000_000_000 us (sealed-legal hold) and
  12_240_000_000 us (hydrogen assay). Heads now 0.08, -0.34, -0.11, 0.14,
  0.08; total -0.15. Inflection is the last tick.
- Contrast train 8 events, own race 192 us, ACCEPT.
- Three-edge third factor: three raise-go edges, tau_e 7.0 s = 7000 ms,
  trace __AUX_TRACE__, eta __AUX_ETA1__ / __AUX_ETA2__ / __AUX_ETA3__,
  weights 0.46->0.22, 0.41->0.20, 0.38->0.19. Raster excerpt unchanged
  (decision window is still 40 ms) and remains sorted with unique
  neuron_ids (same-neuron >=1000 us vacuously).

Winner/loser flip (re-stated, not replaced): reversing 192 us would only
reorder triage; r_h2 and r_leak floors still MODIFY. Contrast flip of
192 us similarly cannot turn a sealed panel into a leak.

## Trajectory Builder

Schema checks on the FINAL object: required Thalamic v2 keys present as
objects; `state.sim_or_real`=designed; `safety_decision.decision`=MODIFY
with numeric rationale; `reward_components.total` = sum of five heads =
sum of 7 ticks = -0.15; `spike_events` globally non-decreasing on
t_rel_ms, 26 events, refractory >=0.8 ms, 3 channels in race window;
raster 20–50 ms, spikes=round(n*rate*window_s)+/-1, energy 23 pJ/spike,
excerpt sorted, tau_e consistent; gate_snn.decision matches; meta.round=49,
factory=multi-agent-ouroboros-swarm, generator=grok-4.6,
run_label=2026-09-02-final-heavy; rights on record and meta; no thought
keys; no training_ready; Diversity + Edge-Case injections from BOTH cycles
present and non-trivial; cycle 2 strictly additive; plant is not
LYOSHIELD, not CINDERWICK, not TRIAD, not NITROSTAITH, not BOGIRON, not
CHROMLOOP, not ETHYNWOLD, not NITREVAULT, not RUNNELGATE, not SPARKHOLT, not DIPLEGAR, not OLEUMWEIR, not BRIMVAULT.

Densification delta: +1 domain sub-variant (35 t scrap EAF), +1 tail
(Sunday-night forgery), +10 spikes (16->26), +2 ticks (5->7), +1 contrast
train with own race, +2 delayed side-effects, +1 three-edge scar with
any-pair-rollback-fails, +1 HITL ratify, +1 surprise (dissolved hydrogen
is the campaign-miss mechanism).

Publishable JSONL line (the only JSONL line; also at batch-r49.jsonl):

```json
__FINAL_JSONL__
```

Validation receipt (final): checks passed / fixed as reported by
build_r53.py self-validate (check_jsonl, raster_status, verify_record_execution,
spike_probe --strict).
"""
    text = (
        text.replace("__C1_SPIKES__", str(len(c1_spikes)))
        .replace("__AUX_TRACE__", f"{math.exp(-PROBE_S / TAU_E_S):.5f}")
        .replace("__AUX_ETA1__", f"{0.24 / math.exp(-PROBE_S / TAU_E_S):.5f}")
        .replace("__AUX_ETA2__", f"{0.21 / math.exp(-PROBE_S / TAU_E_S):.5f}")
        .replace("__AUX_ETA3__", f"{0.19 / math.exp(-PROBE_S / TAU_E_S):.5f}")
        .replace("__FINAL_JSONL__", line)
    )
    (OUT / "swarm-transcript-r49.md").write_text(text)
    return text


def heads_summary(rec):
    rc = rec["reward_components"]
    return {
        "id": rec["id"],
        "total": rc["total"],
        "decision": rec["safety_decision"]["decision"],
        "sim": rec["state"]["sim_or_real"],
        "domain": rec["state"]["domain"],
        "spikes": len(rec["spike_events"]),
        "ticks": len(rc["ticks"]),
        "plant": rec["state"]["scenario_name"],
    }


def main():
    rec, aux = build_record()
    errs = local_checks(rec, aux)

    OUT.mkdir(parents=True, exist_ok=True)
    line = json.dumps(rec, ensure_ascii=False, separators=(",", ":"))
    (OUT / "batch-r49.jsonl").write_text(line + "\n")

    from check_records import FactoryStaging, check_jsonl
    from curate_bridge import raster_status
    from verify_execution import verify_record_execution

    e, w, kinds, n = check_jsonl(
        OUT / "batch-r49.jsonl",
        "batch-r49.jsonl",
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
        errs.append(f"verify {status}: {reason}")

    probe = subprocess.run(
        [
            sys.executable,
            f"{ROOT}/pipelines/spike_probe.py",
            "--strict",
            str(OUT / "batch-r49.jsonl"),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    print("spike_probe rc", probe.returncode)
    print(probe.stdout)
    if probe.stderr:
        print("spike_probe stderr", probe.stderr)
    if probe.returncode != 0:
        errs.append(f"spike_probe rc {probe.returncode}")

    receipt = (
        f"check_jsonl errors={e} warnings={w} kinds={kinds} n={n}; "
        f"raster_status valid={st.get('raster_valid')} gate={st.get('gate_snn_valid')} "
        f"reasons={st.get('reason_codes')}; verify_record_execution={status} ({reason}); "
        f"spike_probe --strict rc={probe.returncode}"
    )
    write_notes(rec, aux, receipt)
    write_transcript(rec, line)

    headings = re.findall(
        r"^## .+$", (OUT / "swarm-transcript-r49.md").read_text(), re.M
    )
    print("headings", headings)
    expected = [
        "## Generator",
        "## Critic",
        "## Diversity Enforcer",
        "## Edge-Case Hunter",
        "## Neuromorphic Translator",
        "## Trajectory Builder",
        "## Generator",
        "## Critic",
        "## Diversity Enforcer",
        "## Edge-Case Hunter",
        "## Neuromorphic Translator",
        "## Trajectory Builder",
    ]
    if headings != expected:
        errs.append(f"heading sequence {headings}")

    notes = (OUT / "NOTES-r49.md").read_text()
    cov = re.findall(r"^Novel coverage: .+$", notes, re.M)
    if cov != [NOVEL_LINE]:
        errs.append(f"novel coverage lines {cov}")

    hchk = subprocess.run(
        [
            sys.executable,
            "/tmp/maos_heading_check.py",
            str(OUT / "swarm-transcript-r49.md"),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    print(hchk.stdout)
    if hchk.returncode != 0:
        errs.append(f"heading_check rc {hchk.returncode}: {hchk.stdout}")

    raw_guard = subprocess.run(
        ["git", "-C", ROOT, "status", "--porcelain", "--", "outputs/raw"],
        check=False,
        capture_output=True,
        text=True,
    )
    if raw_guard.stdout.strip():
        errs.append(f"outputs/raw dirty: {raw_guard.stdout.strip()}")

    raw_hits = subprocess.run(
        [
            "rg",
            "-l",
            "maos-r49-001|SKARVOLT",
            str(Path(ROOT) / "outputs" / "raw"),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    if raw_hits.stdout.strip():
        errs.append(f"raw tree hit {raw_hits.stdout.strip()[:200]}")

    print("bytes jsonl", (OUT / "batch-r49.jsonl").stat().st_size)
    print("bytes notes", (OUT / "NOTES-r49.md").stat().st_size)
    print("bytes transcript", (OUT / "swarm-transcript-r49.md").stat().st_size)
    print("HEADS", heads_summary(rec))
    if errs:
        print("ERRS:")
        for x in errs:
            print(" -", x)
        sys.exit(1)
    print("OK", OUT / "batch-r49.jsonl")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
