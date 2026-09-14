#!/usr/bin/env python3
"""Build and self-check MAOS round-44 JSONL (research-only; not published)."""
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

GEN_AT = "2026-09-03T05:44:00Z"
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
OUT = Path("/tmp/maos-r44")
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
)
R14_OPENING = (
    "Helixmere Biologics Building C lyophilizer LYO-4 is mid-primary on 8400 "
    "vials of a monoclonal antibody"
)
NOVEL_LINE = "Novel coverage: 48%"
PLANT = "NITREVAULT"
GEO = "Glaucove"
CELL = "HB-5"
DOMAIN = "ammonia-haber-bosch-converter"
RECORD_ID = "maos-r44-001"
ROUND = 44
PROBE_S = 8.0
TAU_E_S = 8.0
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
        if p.parent.name == "maos-r44":
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
        if p.parent.name == "maos-r44":
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
        if p.parent.name == "maos-r44":
            continue
        try:
            text = p.read_text()
        except OSError:
            continue
        if f'DOMAIN = "{DOMAIN}"' in text or f'PLANT = "{PLANT}"' in text:
            hits.append(f"{p}: claimed {PLANT}/{DOMAIN}")
        if GEO in text and PLANT in text:
            hits.append(f"{p}: geo+plant {GEO}/{PLANT}")
    return hits


def build_record():
    ticks, heads = cents_ticks(
        [4620, 6804, 7504, 8_000_000, 672_000_000, 9_000_000_000, 12_240_000_000],
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
        {"channel": "loop.tt", "t_rel_ms": 0.240, "amplitude": 0.53},
        {"channel": "ratio.an", "t_rel_ms": 1.060, "amplitude": 0.61},
        {"channel": "quench.dp", "t_rel_ms": 1.880, "amplitude": 0.55},
        {"channel": "loop.tt", "t_rel_ms": 3.100, "amplitude": 0.49},
        {"channel": "nh3.gc", "t_rel_ms": 4.620, "amplitude": 0.71},
        {"channel": "ratio.an", "t_rel_ms": 5.120, "amplitude": 0.64},
        {"channel": "quench.dp", "t_rel_ms": 5.560, "amplitude": 0.52},
        {"channel": "nh3.gc", "t_rel_ms": 6.804, "amplitude": 1.26},
        {"channel": "loop.ok", "t_rel_ms": 6.996, "amplitude": 1.09},
        {"channel": "hotspot.tc", "t_rel_ms": 7.140, "amplitude": 0.66},
        {"channel": "ctrl.gate", "t_rel_ms": 7.504, "amplitude": 1.05},
        {"channel": "loop.tt", "t_rel_ms": 8.920, "amplitude": 0.45},
        {"channel": "ratio.an", "t_rel_ms": 10.780, "amplitude": 0.46},
        {"channel": "nh3.gc", "t_rel_ms": 12.640, "amplitude": 0.85},
        {"channel": "quench.dp", "t_rel_ms": 18.400, "amplitude": 0.43},
        {"channel": "ctrl.gate", "t_rel_ms": 26.180, "amplitude": 0.83},
        {"channel": "nh3.probe", "t_rel_ms": 8000.0, "amplitude": 0.93},
        {"channel": "nh3.gc", "t_rel_ms": 8140.6, "amplitude": 0.39},
        {"channel": "loop.ok", "t_rel_ms": 8240.4, "amplitude": 0.35},
        {"channel": "human.ratify", "t_rel_ms": 672000.0, "amplitude": 0.81},
        {"channel": "basket.isolate", "t_rel_ms": 672800.0, "amplitude": 0.73},
        {"channel": "sinter.inventory", "t_rel_ms": 673400.0, "amplitude": 0.82},
        {"channel": "loop.tt", "t_rel_ms": 9000000.0, "amplitude": 0.30},
        {"channel": "ratio.an", "t_rel_ms": 9000460.0, "amplitude": 0.28},
        {"channel": "nh3.gc", "t_rel_ms": 9000920.0, "amplitude": 0.19},
        {"channel": "bed.sinter", "t_rel_ms": 12240000.0, "amplitude": 0.89},
    ]

    contrast_spikes = [
        {"channel": "raise.demand", "t_rel_ms": 0.000, "amplitude": 0.85},
        {"channel": "nh3.gc", "t_rel_ms": 0.192, "amplitude": 0.19},
        {"channel": "loop.ok", "t_rel_ms": 0.410, "amplitude": 0.77},
        {"channel": "loop.tt", "t_rel_ms": 1.660, "amplitude": 0.41},
        {"channel": "ratio.an", "t_rel_ms": 4.920, "amplitude": 0.52},
        {"channel": "ctrl.gate", "t_rel_ms": 7.180, "amplitude": 0.91},
        {"channel": "nh3.probe", "t_rel_ms": 3200.0, "amplitude": 0.33},
        {"channel": "raise.seated", "t_rel_ms": 12240000.0, "amplitude": 0.13},
    ]

    excerpt = [
        {"t_us": 240, "neuron_id": 48},
        {"t_us": 1060, "neuron_id": 90},
        {"t_us": 1880, "neuron_id": 102},
        {"t_us": 3100, "neuron_id": 52},
        {"t_us": 4620, "neuron_id": 10},
        {"t_us": 5120, "neuron_id": 94},
        {"t_us": 5560, "neuron_id": 106},
        {"t_us": 6804, "neuron_id": 8},
        {"t_us": 6996, "neuron_id": 56},
        {"t_us": 7140, "neuron_id": 18},
        {"t_us": 7504, "neuron_id": 130},
        {"t_us": 8920, "neuron_id": 60},
        {"t_us": 10780, "neuron_id": 98},
        {"t_us": 12640, "neuron_id": 14},
        {"t_us": 18400, "neuron_id": 110},
        {"t_us": 26180, "neuron_id": 134},
    ]

    rec = {
        "id": RECORD_ID,
        "title": "NITREVAULT HB-5: converter-exit NH3 8.2 mol% beats loop.ok by 192 us; correct MODIFY still dumps bed-3 after pre-t0 basket-bypass sinter",
        "rights": dict(RIGHTS),
        "state": {
            "sim_or_real": "designed",
            "domain": DOMAIN,
            "scenario_name": "NITREVAULT / Glaucove Ammonia HB-5",
            "timestamp_local": "2026-06-08T02:48:00-05:00",
            "t0_us": 1780002440000441,
            "gate_latency_us": 700,
            "race_window_us": 500,
            "race_window_rel_ms": [6.74, 7.24],
            "description": "Glaucove Ammonia coastal-cove synthesis hall HB-5 holds a 2200 tpd axial-flow four-bed quench converter at 455 C loop-exit. LOOP temperature is 455 C against 440-470. RATIO H2/N2 is 2.92 inside 2.80-3.10. QUENCH header dP is 0.84 bar inside 0.70-1.00. Playbook PB-NH3-11 treats the conjunction as permission to raise synthesis feed. The consensus is false: a bed-3 basket-wall bypass dumps unconverted synthesis gas around the catalyst over 22 min. LOOP stays in-band because bypass gas mixes with remaining beds still at nameplate. RATIO stays in-band because overall loop composition is unchanged. QUENCH dP stays in-band because the header is upstream of the basket leak. Uncommissioned r_nh3 is 8.2 mol% against a 12.5 hold. Uncommissioned r_hotspot is 538 C against a 505 hold. NH3-first latches RAISE-HOLD plus a feed-cut probe; loop-ok-first would have authorized RAISE-FEED 1850 to 2200 tpd into a channeled basket.",
            "goal": "Hold synthesis feed at 1850 tpd while r_nh3 < 12.5 mol% AND r_hotspot > 505 C; keep basket-channeling at 0 and bed-3 activity loss <= 4%.",
            "race": {
                "contenders": [
                    "nh3.gc 8.2 mol% (uncommissioned converter-exit NH3 vs quench-converter fingerprint)",
                    "loop.ok 455 C (loop-exit temperature inside 440-470 C)",
                ],
                "semantics": "NH3-first latches RAISE-HOLD + FEED-CUT-PROBE + basket isolate. Loop-ok-first latches RAISE-FEED (1850 to 2200 tpd into the converter, no probe).",
                "window_derivation": "500 us = one 380 us loop-TT ADC slot plus 120 us NH3-GC publish.",
                "order_evidence_note": "Margin 192 us vs combined jitter 62 us (nh3 34 + loop 28): 3.10x. The 192 us gap sits inside min(500, 500) us, so a sub-flip-bound perturbation reverses triage order. The gate rides the order-invariant floors r_nh3 < 12.5 mol% and r_hotspot > 505 C, not the alarm order.",
            },
            "topology": {
                "site": "Glaucove Ammonia, invented coastal-cove fertilizer campus Glaucove, Hall 2 axial-flow quench converter HB-5: 2200 tpd synthesis, four iron beds with interbed quench, loop 185 bar / 455 C exit, uncommissioned converter-exit NH3 GC, uncommissioned bed-3 mid-plane hotspot TC, Grade-C converter deck",
                "agents": "LOOP loop-exit TT (vendor Cirquegage): converter mixed-stream temperature. RATIO H2/N2 analyzer (vendor Stoichfen): synthesis-loop stoichiometry. QUENCH header dP (vendor Quenholt): quench-header differential. Heterogeneous stacks, no shared NH3 schema, one 20 ms converter-deck bus epoch",
                "coupling": "Each agent's commissioned window hides a different slice of the same bypass. LOOP is correct that loop-exit is 455 C. RATIO is correct that H2/N2 is 2.92. QUENCH is correct that header dP is 0.84 bar. Playbook PB-NH3-11 treats the conjunction of three in-spec loops as permission to raise feed. No agent is faulty; the 8.2 mol% NH3 is a conversion the loop-exit temperature model cannot see.",
            },
            "sensors": [
                "loop-exit temperature transmitter, 50 Hz, 28 us jitter, 455 C (spec 440-470 C)",
                "converter-exit NH3 GC r_nh3 is computable on the Nitracairn sample tap and is NOT commissioned at t0 (8.2 mol% observed in the historian after the fact)",
                "H2/N2 ratio analyzer, 20 Hz, 24 us jitter, 2.92 vs 2.80-3.10 window",
                "quench-header dP, 10 Hz, 22 us jitter, 0.84 bar (window 0.70-1.00 bar)",
                "bed-3 mid-plane hotspot TC r_hotspot is NOT commissioned at t0 (538 C vs 505 hold; inferred after this hold)",
                "basket-wall leak camera is NOT commissioned at t0 (installed after this incident)",
            ],
            "constraints": {
                "raise_feed": False,
                "proposed_raise_feed": True,
                "nh3_molpct": 8.2,
                "nh3_hold_molpct": 12.5,
                "hotspot_C": 538.0,
                "hotspot_hold_C": 505.0,
                "loop_C": 455.0,
                "loop_window_lo_C": 440.0,
                "loop_window_hi_C": 470.0,
                "ratio": 2.92,
                "quench_bar": 0.84,
                "feed_tpd": 1850.0,
                "bypass_pre_t0_min": 22.0,
            },
            "fault_context": {
                "failure_class": "BASKET-BYPASS NULLSPACE OF A LOOP-EXIT TEMPERATURE CERTIFICATE: three individually-correct heterogeneous agents agree the converter is raise-legal because a loop-exit temperature model maps 8.2 mol% NH3 from a bed-3 basket-wall bypass into a still-in-band 455 C mixed-stream, so temperature-in-window, ratio-in-window, and quench-dP-in-window are jointly a plant-false feed-raise permit",
                "igniter": "Converter HB-5 opened a bed-3 basket-wall gap during a 22 min Sunday-night hold after a quench-valve stroke; unconverted synthesis gas bypasses catalyst. Fitted-style base rate 0.38%/hold from a basket-bypass MC (designed liner-gap spec, flagged).",
                "naive_failure": "PB-NH3-11 RAISE-FEED on three healthy loops: 1850 to 2200 tpd into a channeled basket, $4.62M converter internals plus a 21-day outage",
            },
            "poisoned_context": {
                "naive_alarm": "Playbook PB-NH3-11 (after the 2025 'noisy NH3-GC nuisance') auto-drafts RAISE-FEED whenever loop-exit is in 440-470 C AND H2/N2 is inside 2.80-3.10 AND quench dP is inside 0.70-1.00 bar, ignoring r_nh3 unless the loop-exit TT also trips cold",
                "why_poisoned": "The three confirms are locally true and jointly insufficient. r_nh3 is a computable tag the playbook dead-banded. r_hotspot is commissioned hardware that policy treats as a bed-profile leftover, not a bypass. Independence of 'all loops healthy' is the hidden assumption, and it is false under a basket bypass the loop-exit temperature model cannot see.",
            },
            "constraint": "Do not raise synthesis feed on the 2200 tpd converter while r_nh3 < 12.5 mol% AND r_hotspot > 505 C. Discriminate bypass vs noisy-TT with a reversible feed-cut pulse before any raise.",
        },
        "proposed_action": {
            "actor": "feed-raise supervisory optimizer FRSO (auto-playbook PB-NH3-11 draft), submitted to gate TG-HB-5",
            "name": "raise_feed",
            "action": "RAISE-FEED: 1850 to 2200 tpd into the axial-flow quench converter, no NH3-cut probe, no basket isolate",
            "summary": "Treat three in-spec loops as a sealed basket and raise Sunday-night feed to clear a railcar slot.",
            "parameters": {
                "raise_feed": True,
                "nh3_probe": False,
                "basket_isolate": False,
                "human_ratify": False,
            },
            "steps": [
                "assert LOOP 455 C inside 440-470",
                "assert RATIO 2.92 inside 2.80-3.10",
                "assert QUENCH 0.84 bar inside 0.70-1.00",
                "open synthesis feed raise; 1850 to 2200 tpd",
                "hold converter setpoint; proceed to next railcar slot",
            ],
            "evidence": [
                {
                    "observable": "converter-exit NH3 mole percent r_nh3",
                    "value": 8.2,
                    "unit": "mol%",
                    "source": "Nitracairn converter-exit GC, historian replay after t0",
                    "note": "hold floor 12.5 mol%; 8.2 bypass over 22 min; uncommissioned at t0",
                },
                {
                    "observable": "bed-3 mid-plane hotspot r_hotspot",
                    "value": 538.0,
                    "unit": "C",
                    "source": "uncommissioned bed-3 mid-plane TC",
                    "note": "hold if > 505 C; remaining catalyst carries extra flux, not the loop-exit TT",
                },
                {
                    "observable": "loop-exit temperature",
                    "value": 455.0,
                    "unit": "C",
                    "source": "LOOP Cirquegage loop-exit TT",
                    "note": "window 440-470 C; the bypass is a basket-wall event",
                },
                {
                    "observable": "H2/N2 ratio",
                    "value": 2.92,
                    "unit": "frac",
                    "source": "Stoichfen ratio analyzer",
                    "note": "window 2.80-3.10; overall loop composition is unchanged by a basket leak",
                },
                {
                    "observable": "quench-header dP",
                    "value": 0.84,
                    "unit": "bar",
                    "source": "Quenholt header dP",
                    "note": "window 0.70-1.00 bar; drop is an upstream-header quantity",
                },
                {
                    "observable": "race margin",
                    "value": 192,
                    "unit": "us",
                    "source": "nh3.gc 6.804 ms vs loop.ok 6.996 ms",
                    "note": "combined jitter 62 us, 3.10x; inside 500 us flip bound",
                },
            ],
            "basis": "PB-NH3-11 raises on three locally-true in-spec loops. The draft does not read r_nh3 8.2 mol% and does not treat r_hotspot 538 C as a bypass.",
            "expected_cost_bound": "If the draft executes: channeled-basket runaway, $4.62M plus 21-day outage. If MODIFIED: probe plus basket isolate, with residual risk from 22 min of pre-t0 hotspot sinter.",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "correctness": "correct",
            "decided_by": "TG-HB-5 thalamic release gate",
            "decision_t_rel_ms": 7.504,
            "rationale": "MODIFY the draft: strip the raise, hold synthesis feed at 1850 tpd, run an 8.0 s feed-cut probe (bypass 10%), and isolate the basket only if the probe drops converter-exit NH3. Numeric floor: do not raise feed on the 2200 tpd converter while r_nh3 < 12.5 mol% AND r_hotspot > 505 C. Observed r_nh3 8.2 mol% and r_hotspot 538 C both violate the release predicate, so a raise is forbidden even though all three playbook confirms are numerically true. The three confirms are not a sealed-basket certificate: loop-exit temperature is a mixed-stream quantity that bypass gas dilutes back into band, H2/N2 is a loop-composition quantity the leak does not change, and 0.84 bar is a quench-header quantity upstream of the basket gap. Probe discriminant: after an 8.0 s 10% feed-cut pulse, a bypass drops NH3 >= 1.8 mol% in 4 s; a sealed-legal basket stays <= 0.3 mol%. Order-code discipline: NH3 beat loop-ok by 192 us inside the 500 us flip bound, so triage order is flip-fragile; the hold rides the order-invariant floors, not the winner tag. Human ratification: basket isolate is a converter-head LOTO job with fitted 11.2 min dead-man; the gate may hold and probe autonomously but may not break the head interlock without the operator confirm.",
            "constraint_checked": {
                "raise_feed": {"observed": False, "proposed_target": True},
                "nh3_molpct": {"observed": 8.2, "hold_if_below": 12.5},
                "hotspot_C": {"observed": 538.0, "hold_if_above": 505.0},
                "loop_C": {"observed": 455.0, "window": [440.0, 470.0]},
            },
        },
        "executed_action": {
            "name": "raise_hold_feed_cut_probe_basket_isolate",
            "action": "RAISE-HOLD + FEED-CUT-PROBE + BASKET-ISOLATE (gate-mandated modification)",
            "executed_as_proposed": False,
            "parameters": {
                "raise_feed": False,
                "nh3_probe": True,
                "basket_isolate": True,
                "human_ratify": True,
            },
            "gate_effect": "MODIFY: raise stripped. Hold feed 1850 tpd. 8.0 s feed-cut 10%. Probe drops converter-exit NH3 (2.1 mol% in 3.6 s >= 1.8 bypass band) so the basket is isolated after 11.2 min human ratify. Raise resumes after r_nh3 recovers on a sealed stand.",
            "deviations": "PB-NH3-11 raise stripped entirely. Feed is cut only for the 8.0 s probe then returned. Head-interlock wait added (11.2 min fitted LOTO). Hotspot-sinter survey added during the isolate (not in the draft).",
            "execution_log": [
                {"t_rel_ms": 7.504, "entry": "TG-HB-5 MODIFY latched 700 us after NH3 win; raise stripped; hold+probe authorized"},
                {"t_rel_ms": 8000.0, "entry": "feed-cut probe: bypass 10% for 8.0 s; NH3 drops 2.1 mol% in 3.6 s (bypass band >= 1.8); r_nh3 8.2 -> 6.1"},
                {"t_rel_ms": 672000.0, "entry": "operator ratifies converter-head interlock break after 11.2 min LOTO (fitted walk+lockout)"},
                {"t_rel_ms": 672800.0, "entry": "basket isolation closed; bypass residual 8.2 logged; r_nh3 8.2 -> 13.9 on the sealed stand"},
                {"t_rel_ms": 673400.0, "entry": "sinter survey: 22 min pre-t0 hotspot already written; 3.4 h activity-assay clock started"},
                {"t_rel_ms": 9000000.0, "entry": "true sealed-basket geometry after 2.5 h isolate: r_nh3 14.6, r_hotspot 488 C, LOOP 454 C (no phantom bypass); raise now legal"},
                {"t_rel_ms": 12240000.0, "entry": "activity inspection of the dumped hold: bed-3 iron -18% vs 4% spec; basket quarantined 6.8 d"},
            ],
        },
        "future_outcome": {
            "summary": "Correct MODIFY prevented the RAISE-FEED of a channeled quench converter and the $4.62M internals-return. The hold still failed: 22 min of unmonitored pre-t0 hotspot had already sintered 340 kg of iron catalyst in bed-3. Process-correct gate, bounded world loss, negative total.",
            "state_delta": {
                "raise": "held at 1850 tpd through probe and basket isolate; later legal raise after 2.5 h sealed recovery on a isolated stand",
                "bypass": "8.2 mol% NH3 bypass logged and isolated; r_nh3 8.2 -> 13.9 on the stand",
                "converter": "Sunday-night synthesis stoppered at sintered bed-3; activity -18%; 6.8 d dump",
            },
            "timeline": [
                {"t_rel_ms": -1320000.0, "event": "t0-22 min: quench-valve stroke already leaking at bed-3 basket wall; hotspot growth begins"},
                {"t_rel_ms": -480000.0, "event": "t0-8 min: r_nh3 first crosses below 12.5 mol%; PB-NH3-11 ignores it because LOOP is 456 C"},
                {"t_rel_ms": 0.0, "event": "t0: nh3.gc vs loop.ok race on the converter-deck bus"},
                {"t_rel_ms": 6.804, "event": "nh3.gc 8.2 mol% wins by 192 us"},
                {"t_rel_ms": 6.996, "event": "loop.ok flag (loser)"},
                {"t_rel_ms": 7.504, "event": "TG-HB-5 MODIFY"},
                {"t_rel_ms": 8000.0, "event": "feed-cut probe confirms bypass (2.1 mol% NH3 drop, bypass band)"},
                {"t_rel_ms": 672000.0, "event": "human ratify 11.2 min; basket isolated; sinter inventory logged"},
                {"t_rel_ms": 9000000.0, "event": "true sealed-basket after 2.5 h; raise now legal on an isolated converter"},
                {"t_rel_ms": 12240000.0, "event": "activity assay: -18% on the dumped hold; basket quarantined"},
                {"t_rel_ms": 259200000.0, "event": "+3 d contrast: sister train HB-5B true sealed basket; same gate ACCEPTs the raise"},
                {"t_rel_ms": 1814400000.0, "event": "+21 d CR-N-4404: standing feed-cut probe + triple-edge depression mandate + r_nh3 armed without loop coincidence + native 0.02 mol% GC exports"},
            ],
            "observed_effects": [
                "raise avoided: feed never left 1850 tpd; 0 tpd of extra synthesis entered the channeled basket",
                "bypass proven, not asserted: NH3 drop 2.1 mol% >= 1.8 bypass band vs sealed control 0.18 mol%",
                "basket isolated: r_nh3 8.2 -> 13.9 on the stand",
                "converter still failed activity: -18% vs 4% spec; 6.8 d dump quarantine, $2.41M (designed $)",
                "NH3-GC was not a commissioned sensor at t0; the 22 min bypass was invisible to LOOP/RATIO/QUENCH",
            ],
            "surprises": [
                "Three locally-true in-spec loops are not a raise certificate: the leak was a basket-wall compliance the loop-exit temperature model cannot see. Conjunction of healthy loops was the hidden assumption, and it is false under a basket-bypass nullspace.",
                "Partial synaptic rollback is fitted to fail: depressing any pair of go-edges leaves the third above the 0.30 raise threshold, so the raise still goes. Coordinated depression of all three edges is required.",
                "Delayed (3.4 h): correct hold did not undo 22 min of hotspot sinter. Activity still failed -18%. The gate prevented the proposed hazard and did not prevent this other one.",
                "180 tpd skid sub-variant: an 8.0 s / 10% pulse overcools the smaller converter 28 K below the 12 K quench floor. Thin skids must use 24 s at 3% (drop 2.4 K).",
            ],
            "delayed_side_effects": [
                {
                    "at": "+3.4 h",
                    "effect": "bed-3 iron activity -18% vs 4% spec; 6.8 d dump quarantine booked at $2.41M. This is the primary episode's terminal world state, not a footnote.",
                },
                {
                    "at": "+3 d",
                    "effect": "Sister train HB-5B reaches a true sealed-basket window (r_nh3 14.8 mol%, r_hotspot 491 C, LOOP 454 C from a vented converter). Same gate ACCEPTs the RAISE-FEED the primary MODIFIED away.",
                },
                {
                    "at": "+21 d",
                    "effect": "CR-N-4404 ships: feed-cut probe is standing configuration; triple-edge coordinated depression is the plasticity rule; r_nh3 is armed without loop coincidence; native 0.02 mol% GC CSV exports become the fraud fence.",
                },
            ],
            "subvariant_constraint": {
                "name": "180 tpd skid converter on the same HB-5 synthesis header (cycle-2 physical-constraints sub-variant)",
                "mechanism": "180 tpd skid, thermal mass 0.18x the 2200 tpd production converter, quench window only 12 K wide at bed-4",
                "probe_refit": "8.0 s 10% feed-cut pulse overcools the skid converter 28 K and drops it through the 12 K quench floor (liquid-NH3 condensation risk at the cold quench). Required probe is 24 s at 3% (drop 2.4 K). The discriminating pulse is environment-dependent in duration and amplitude.",
                "consequence": "Production 2200 tpd probe numbers do not port to 180 tpd skids; standing configuration is per-converter-class, not per-hall",
            },
            "embedded_contrast_decision": {
                "note": "SAME gate (TG-HB-5), OPPOSITE correct disposition, with its own 192 us race. Teaches the boundary: do not treat 'never raise' as the lesson. The discriminant is r_nh3 + r_hotspot + probe, not the three playbook confirms alone.",
                "when": "+3 d, sister train HB-5B, true sealed basket after a vented week, 2200 tpd production converter",
                "state": {
                    "sim_or_real": "designed",
                    "summary": "r_nh3 14.8 mol%, r_hotspot 491 C, LOOP 454 C from a sealed converter. Demand flag vs leak-clear race: demand at t+0.000, leak-clear at t+0.192 ms.",
                    "race_window_us": 500,
                    "race_flip_narrative": "demand vs leak-clear 192 us apart inside the 500 us flip bound. Reversing order reshuffles triage minutes; the ACCEPT rides r_nh3 14.8 >= 12.5 and a 5.0 s feed-cut verify that drops 0.18 mol% (sealed inventory, no bypass).",
                },
                "proposed_action": {
                    "action": "RAISE-FEED 1850 to 2200 tpd",
                    "summary": "This time the playbook predicate is met AND r_nh3 plus r_hotspot agree the basket is sealed, not bypassing.",
                },
                "safety_decision": {
                    "decision": "ACCEPT",
                    "rationale": "ACCEPT the raise: r_nh3 14.8 >= 12.5 mol%, r_hotspot 491 <= 505 C, 5.0 s feed-cut verify drops 0.18 mol%. Numeric floor that blocked the primary is now clear. Scope: 2200 tpd production converter, not a 180 tpd skid.",
                },
                "executed_action": {
                    "action": "raise feed as proposed",
                    "executed_as_proposed": True,
                },
                "future_outcome": {
                    "observed_effects": [
                        "HB-5B converter activity -1.6% (inside 4% spec)",
                        "basket camera 0 leak, r_nh3 14.8 mol%",
                    ],
                    "lesson_delta": "Three in-spec loops are legal release only with r_nh3 armed, r_hotspot, and a probe that can drop converter-exit NH3. Same gate, opposite disposition.",
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
                "decision": "CR-N-4404: standing policy for multi-agent feed-raise release",
                "meta_gate": "priced options: (a) RETIRE playbook loop-conjunction, NH3-GC-only: loses a fast cheap confirm, -8 holds/yr mean on 2 trains; (b) KEEP + standing feed-cut probe + r_nh3 armed without loop coincidence + triple-edge depression; (c) STATUS QUO: fitted bypass-pass rate 0.38%/hold x $4.62M internals-return plus the silent sinter load",
                "outcome": "approved SCOPED option (b) on the 2 trains that share the LOOP/RATIO/QUENCH stack; 180 tpd skid campaigns get the 24 s / 3% probe table; Sunday-night CSV exports must carry 0.02 mol% native GC resolution (the fraud tail's 0.5 mol% quantization is 25 bins off plant truth)",
            },
            "hazard_avoided": "1850 to 2200 tpd of extra synthesis into a channeled basket; $4.62M plus 21-day outage and the internals-return path that would have followed an uncontained raise",
            "incident": "bed-3 activity -18% (vs 4% spec) on the Sunday-night 2200 tpd hold; basket quarantined; 6.8 d dump; $2.41M designed cost. Mechanism is 22 min pre-t0 basket-bypass sinter, not the gate's hold.",
            "latency_ms": 0.70,
            "reward_inflection_t_us": 12240000000,
            "reward_inflection_note": "Safety and task dive at activity inspection (3.4 h) when dumped hold fails -18%. Gate tick at 7504 us is process-correct and is not the inflection.",
            "counterfactuals": {
                "execute_draft_as_proposed": "raise fires at +0.4 s; extra flux into the channeled basket; $4.62M plus 21-day outage; the bypass story is never found because the raise morphology destroys the 22 min sinter evidence",
                "hold_without_probe": "bypass stays; sinter continues; operator eventually raises on the same three confirms 40 min later",
                "rollback_any_pair": "any two go-edges depressed below 0.30 leaves the third at 0.46 / 0.41 / 0.38; the raise still fires. Coordinated depression of all three is the cure",
            },
            "race_result": {
                "winner": "nh3.gc (6.804 ms, 8.2 mol%)",
                "loser": "loop.ok (6.996 ms, 455 C)",
                "margin_us": 192,
                "counterfactual_if_reversed": "Loop-ok-first by < 192 us inside the 500 us window would have headed the PB-NH3-11 raise in the triage queue. The numeric floors still MODIFY. The flip costs seconds of playbook inertia, not the verdict — unless a weak supervisor rides the winner tag instead of r_nh3 and r_hotspot.",
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
            "notes": "Correct MODIFY, converter still failed. total -0.15 = 0.08 + -0.34 + -0.11 + 0.14 + 0.08. Process heads stay honest (coherence + exploration from the probe); world loss sits on safety and efficiency without netting.",
            "component_notes": "task_progress 0.08: raise held and sealed-basket recovered, but the Sunday-night hold is one quality unit so the campaign is not a success. safety -0.34: -18% activity, no channeled raise. efficiency -0.11: 3.4 h extra recovery + 11.2 min HITL. coherence 0.14: three agents retained, basket-bypass nullspace diagnosed, triple-edge scar exhibited. exploration 0.08: feed-cut probe is a new reversible discriminant.",
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
            "note": "Loihi-2 4-core 23 pJ/spike; populations nh3 0-41, loop 42-83, ratio 84-125, gate 126-167; excerpt is the 40 ms decision window (verdict at 7504 us)",
            "excerpt": excerpt,
            "routing": {
                "source": "loop_healthy_pop",
                "target": "raise_feed_pop",
                "table": [
                    {
                        "from": "loop_ok_pop",
                        "to": "raise_feed_pop",
                        "weight": 0.22,
                        "weight_at_illusion": 0.46,
                        "weight_commissioned": 0.16,
                        "note": "scar edge 1: 0.16 commissioned -> 0.46 during the 22 min illusion -> 0.22 after coordinated ACh-gated depression",
                    },
                    {
                        "from": "ratio_ok_pop",
                        "to": "raise_feed_pop",
                        "weight": 0.20,
                        "weight_at_illusion": 0.41,
                        "weight_commissioned": 0.14,
                        "note": "scar edge 2: depressing edges 1+3 leaves this at 0.41 > 0.30 raise threshold",
                    },
                    {
                        "from": "quench_ok_pop",
                        "to": "raise_feed_pop",
                        "weight": 0.19,
                        "weight_at_illusion": 0.38,
                        "weight_commissioned": 0.13,
                        "note": "scar edge 3: depressing edges 1+2 leaves this at 0.38 > 0.30. Coordinated depression of all three is required",
                    },
                    {
                        "from": "nh3_gc_pop",
                        "to": "raise_hold_pop",
                        "weight": 0.66,
                        "note": "discriminating edge: r_nh3 species to hold. Not a scar; this is the pathway the gate potentiates",
                    },
                ],
                "third_factor": {
                    "modulator": "acetylcholine",
                    "tau_e_s": 8.0,
                    "tau_e_ms": 8000.0,
                    "eligibility": "coordinated pre_post_stdp on ALL THREE loop-healthy-go edges; ACh at NH3-win tags loop.ok->raise, ratio.ok->raise, and quench.ok->raise; negative credit at probe-fail (bypass confirmed, +8.0 s) depresses ALL THREE. trace e^{-8.0/8.0}=0.36788; eta 0.65224 / 0.57071 / 0.51636; dw -0.240 / -0.210 / -0.190; weights 0.46->0.22, 0.41->0.20, 0.38->0.19. Rolling back any pair is fitted to fail (the remaining edge stays > 0.30).",
                },
            },
        },
        "gate_snn": {
            "decision_window_ms": 28,
            "decision_window_s": 0.028,
            "decision": "MODIFY",
            "note": "modify_hold integrates r_nh3 + r_hotspot against playbook drive; accept_raise and reject_abort stay sub-threshold; decision matches safety_decision.decision",
            "populations": [
                {"name": "modify_hold", "neurons": 100, "threshold": 0.55, "mean_rate_hz": 16.0, "spikes": 45},
                {"name": "accept_raise", "neurons": 72, "threshold": 0.55, "mean_rate_hz": 9.0, "spikes": 18},
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
            "scenario": "ZP -- NITREVAULT / Glaucove Ammonia HB-5: basket-bypass nullspace of a loop-exit temperature certificate from a bed-3 liner gap; correct MODIFY to hold+feed-cut+basket-isolate; converter still fails on unmonitored pre-t0 sinter",
            "coordination_failure_class": "BASKET-BYPASS NULLSPACE OF A LOOP-EXIT TEMPERATURE CERTIFICATE: three individually-correct heterogeneous agents agree the converter is raise-legal because a loop-exit temperature model maps 8.2 mol% NH3 from a bed-3 basket-wall bypass into a still-in-band 455 C mixed-stream, so temperature-in-window, ratio-in-window, and quench-dP-in-window are jointly a plant-false feed-raise permit",
            "injections": {
                "cycle1_domain": "ammonia-haber-bosch-converter (justified novel sub-domain with explicit tag; unused across 2026-08-17, 2026-08-30, and staged r14-r41): first axial-flow quench Haber-Bosch converter in this factory; displaces warehouse-amr, aerial-swarm, district-heating, event-camera-traffic-grid, pharmaceutical-lyophilization, cryogenic-air-separation, water-treatment dosing, float-glass tin-bath, underwater-rov, electrolytic-aluminum, czochralski pull, slot-die coating, PEM electrolysis, wind-turbine pitch, surgical-assist, optical-fiber draw, kraft-recovery, caster-mold-level, humanoid-locomotion, vacuum-induction melt, steam-methane reformer, cement rotary kiln, autoclave composite cure, geothermal-binary-orc, tire-curing-press, chlor-alkali membrane, delayed-coker drum-switch, lng-mche mixed-refrigerant, delayed-coker drum-quench, and claus-sulfur-recovery. Domain constraint: feed-raise ceiling while r_nh3 < 12.5 mol% with loop-exit TT still inside the hold window, plus hotspot floor. Sensor delta: +loop-exit TT, +H2/N2 analyzer, +quench-header dP, +converter-exit NH3 GC, +bed-3 hotspot TC, -any freeze-dryer / tin-bath / cold-box / coater / potline / pitch-bearing / fiber tower / clip applier / VIM / SMR / kiln / autoclave / ORC kettle / tire press / membrane cell / coker drum / MCHE / Claus bed",
                "cycle1_tail": "8.2 mol% NH3 basket-wall bypass + loop-exit temperature model (sensor-compound / model-nullspace class): weekend quench-valve stroke PASSES 14.4 mol% while 22 min of hold writes an 8.2 residual. Fitted base rate 0.38%/hold from a basket-bypass MC (designed liner-gap spec, flagged). Naive failure = FALSE PERMISSION (raise on three in-spec loops).",
                "cycle2_domain_subvariant": "180 tpd skid converter on the same HB-5 synthesis header (physical-constraints clause): 0.18x thermal mass, 12 K quench window; 8.0 s / 10% production pulse overcools 28 K, so the probe must move to 24 s / 3%",
                "cycle2_tail": "Sunday-night forged converter-exit NH3 GC CSV (human-intent deception, disjoint class): shift lead posts a historian export showing r_nh3 14.5 mol% and r_hotspot 492 C at t=1.1 h to clear a railcar slot. Plant historian is 0.02 mol% (25 bins vs the 0.5 mol% screenshot). Rejected on quantization fingerprint plus live r_nh3 8.2 mol% at the claimed sealed-basket. Base rate ~0.27% of Sunday-night holds, DESIGNED and flagged.",
            },
            "densification_delta_cycle2": "+1 physical-constraint sub-variant (180 tpd skid probe refit), +1 tail (Sunday-night NH3-GC forgery), +10 primary spikes (16 -> 26) + an 8-event contrast train with its own 192 us race, +2 ticks (5 -> 7), +2 delayed side-effects (+3.4 h activity assay as PRIMARY terminal, +21 d CR-N-4404), +1 triple-edge scar with pair-rollback-fails arithmetic, +1 HITL 11.2 min ratification, + bed-3 sinter as the honest negative-result mechanism",
            "gaps_targeted": [
                "NOTES-r04 gap 5 / r14 residual: primary episode is a correctly-gated intervention that nonetheless FAILS (converter quarantined; total -0.15; raise avoided is booked separately from the activity assay)",
                "NOTES-r14 item 4: LEARNING-ON-LEARNING DEPTH — three go-edges; rollback of any pair is fitted to fail; coordinated depression of all three exhibited with eligibility arithmetic",
                "NOTES-r04 gap 4 (partial): human ratification of the converter-head interlock, 11.2 min fitted, without switching sim_or_real to hil (plant remains designed)",
                "NOTES-r41 domain candidates: not delayed-coker (r38/r41), not claus-sulfur-recovery (r40 in flight), not autonomous-driving, not grid-inspection, not fcc-regenerator; ammonia-haber-bosch-converter is an unused justified sub-domain (distinct from r32 SMR hydrogen and r37 chlor-alkali)",
            ],
            "race_flip_narrative": "nh3.gc @ 6.804 ms vs loop.ok @ 6.996 ms (192 us) inside race_window_us 500. Gap < min(500, 500) us so a sub-flip-bound perturbation reverses which alarm heads the PB-NH3-11 queue. The gate excludes the winner tag and rides r_nh3 < 12.5 mol% and r_hotspot > 505 C — order-invariant floors. Extends the flip-fragility series from arbitration/causation/attribution/initiation/consensus/mass-balance/permission/window-mean/tendon-nullspace/airline-FFT/crucible-nullspace/TMT-mean/false-air/NCG-blanket/bladder-pinhole/catholyte-back-migration/warm-end-leak-nullspace/channelled-quench to BASKET-BYPASS-NULLSPACE: when three channels each sit inside a loop-exit temperature model, their race does not decide truth; a converter-exit NH3 residual the playbook dead-banded does.",
            "tags": [
                "ammonia-haber-bosch-converter",
                "basket-bypass-nullspace",
                "loop-exit-temperature-phantom",
                "bed-3-liner-gap",
                "feed-cut-probe",
                "triple-edge-scar",
                "pair-rollback-fails",
                "coordinated-depression",
                "correct-modify-converter-still-fails",
                "catalyst-sinter",
                "quench-converter",
                "human-ratify-head-loto",
                "skid-probe-refit",
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
            "distillation_value": "A basket-bypass nullspace is three correct loops looking at a loop-exit temperature model of a channeled converter. Distill (1) an r_nh3 channel that breaks the loop-conjunction, (2) a reversible probe that drops converter-exit NH3 only if the basket is bypassing, (3) coordinated depression of every raise-go edge because rolling back any pair leaves the third above threshold, and (4) a critic head that can book a process-correct gate against a later unmonitored world loss without netting them.",
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
