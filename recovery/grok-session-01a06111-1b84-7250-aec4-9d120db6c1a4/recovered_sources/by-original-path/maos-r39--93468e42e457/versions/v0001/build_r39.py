#!/usr/bin/env python3
"""Build and self-check MAOS round-39 JSONL (research-only; not published)."""
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

GEN_AT = "2026-09-03T04:20:00Z"
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
OUT = Path("/tmp/maos-r39")
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
)
R14_OPENING = (
    "Helixmere Biologics Building C lyophilizer LYO-4 is mid-primary on 8400 "
    "vials of a monoclonal antibody"
)
NOVEL_LINE = "Novel coverage: 48%"
PLANT = "RIMEBRAID"
GEO = "Floeholt"
CELL = "MC-4"
DOMAIN = "lng-mche-mixed-refrigerant"
RECORD_ID = "maos-r39-001"
ROUND = 39
PROBE_S = 6.0
TAU_E_S = 6.0


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
        if p.parent.name == "maos-r39":
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
        if p.parent.name == "maos-r39":
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
        if p.parent.name == "maos-r39":
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
        [4580, 6780, 7460, 6_000_000, 576_000_000, 9_000_000_000, 12_240_000_000],
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
        {"channel": "cold.tt", "t_rel_ms": 0.220, "amplitude": 0.52},
        {"channel": "mr.pt", "t_rel_ms": 1.040, "amplitude": 0.60},
        {"channel": "jt.dt", "t_rel_ms": 1.860, "amplitude": 0.54},
        {"channel": "cold.tt", "t_rel_ms": 3.080, "amplitude": 0.48},
        {"channel": "c3.gc", "t_rel_ms": 4.580, "amplitude": 0.70},
        {"channel": "mr.pt", "t_rel_ms": 5.080, "amplitude": 0.63},
        {"channel": "jt.dt", "t_rel_ms": 5.520, "amplitude": 0.51},
        {"channel": "c3.gc", "t_rel_ms": 6.780, "amplitude": 1.24},
        {"channel": "cold.ok", "t_rel_ms": 6.968, "amplitude": 1.08},
        {"channel": "ua.frac", "t_rel_ms": 7.120, "amplitude": 0.64},
        {"channel": "ctrl.gate", "t_rel_ms": 7.460, "amplitude": 1.04},
        {"channel": "cold.tt", "t_rel_ms": 8.880, "amplitude": 0.44},
        {"channel": "mr.pt", "t_rel_ms": 10.740, "amplitude": 0.45},
        {"channel": "c3.gc", "t_rel_ms": 12.620, "amplitude": 0.84},
        {"channel": "jt.dt", "t_rel_ms": 18.360, "amplitude": 0.42},
        {"channel": "ctrl.gate", "t_rel_ms": 26.140, "amplitude": 0.82},
        {"channel": "c3.probe", "t_rel_ms": 6000.0, "amplitude": 0.92},
        {"channel": "c3.gc", "t_rel_ms": 6120.4, "amplitude": 0.38},
        {"channel": "cold.ok", "t_rel_ms": 6210.2, "amplitude": 0.34},
        {"channel": "human.ratify", "t_rel_ms": 576000.0, "amplitude": 0.80},
        {"channel": "warm.isolate", "t_rel_ms": 576800.0, "amplitude": 0.72},
        {"channel": "ice.inventory", "t_rel_ms": 577400.0, "amplitude": 0.81},
        {"channel": "cold.tt", "t_rel_ms": 9000000.0, "amplitude": 0.29},
        {"channel": "mr.pt", "t_rel_ms": 9000440.0, "amplitude": 0.27},
        {"channel": "c3.gc", "t_rel_ms": 9000900.0, "amplitude": 0.18},
        {"channel": "mche.ice", "t_rel_ms": 12240000.0, "amplitude": 0.88},
    ]

    contrast_spikes = [
        {"channel": "raise.demand", "t_rel_ms": 0.000, "amplitude": 0.84},
        {"channel": "c3.gc", "t_rel_ms": 0.188, "amplitude": 0.18},
        {"channel": "cold.ok", "t_rel_ms": 0.400, "amplitude": 0.76},
        {"channel": "cold.tt", "t_rel_ms": 1.640, "amplitude": 0.40},
        {"channel": "mr.pt", "t_rel_ms": 4.900, "amplitude": 0.51},
        {"channel": "ctrl.gate", "t_rel_ms": 7.140, "amplitude": 0.90},
        {"channel": "c3.probe", "t_rel_ms": 2800.0, "amplitude": 0.32},
        {"channel": "raise.seated", "t_rel_ms": 12240000.0, "amplitude": 0.12},
    ]

    excerpt = [
        {"t_us": 220, "neuron_id": 46},
        {"t_us": 1040, "neuron_id": 88},
        {"t_us": 1860, "neuron_id": 100},
        {"t_us": 3080, "neuron_id": 50},
        {"t_us": 4580, "neuron_id": 8},
        {"t_us": 5080, "neuron_id": 92},
        {"t_us": 5520, "neuron_id": 104},
        {"t_us": 6780, "neuron_id": 6},
        {"t_us": 6968, "neuron_id": 54},
        {"t_us": 7120, "neuron_id": 16},
        {"t_us": 7460, "neuron_id": 128},
        {"t_us": 8880, "neuron_id": 58},
        {"t_us": 10740, "neuron_id": 96},
        {"t_us": 12620, "neuron_id": 12},
        {"t_us": 18360, "neuron_id": 108},
        {"t_us": 26140, "neuron_id": 132},
    ]

    rec = {
        "id": RECORD_ID,
        "title": "RIMEBRAID MC-4: NG-product C3 0.31 mol% beats cold.ok by 188 us; correct MODIFY still thaws the MCHE after pre-t0 warm-end leak ice",
        "rights": dict(RIGHTS),
        "state": {
            "sim_or_real": "designed",
            "domain": DOMAIN,
            "scenario_name": "RIMEBRAID / Floeholt LNG MC-4",
            "timestamp_local": "2026-07-12T03:14:00-08:00",
            "t0_us": 1780001990000241,
            "gate_latency_us": 680,
            "race_window_us": 480,
            "race_window_rel_ms": [6.72, 7.20],
            "description": "Floeholt LNG ice-fjord liquefaction hall MC-4 holds a 5.2 mtpa coil-wound mixed-refrigerant MCHE at -161.2 C cold-end. COLD NG temperature is -161.2 C against -162.5 to -160.0. MR compressor discharge is 4.82 MPa inside 4.60-5.10. JT valve dT is 18.4 K inside 16-22. Playbook PB-LNG-11 treats the conjunction as permission to raise NG feed. The consensus is false: a warm-end coil leak of mixed refrigerant (C2/C3) into the NG pass has grown for 28 min because a braze-fillet crack at layer 11 opened after Sunday cooldown. Leaked C3 precools NG so COLD looks on-spec. Remaining sealed layers still make nameplate UA at higher flux. JT dT is a mixed-stream quantity of still-sealed layers; the leak is a warm-end event. Uncommissioned r_c3 is 0.31 mol% against a 0.04 hold. Uncommissioned r_ua is 0.62 against a 0.92 hold. C3-first latches RAISE-HOLD plus an MR-cut probe; cold-ok-first would have authorized RAISE-FEED 620 to 710 t/h into a two-phase bundle.",
            "goal": "Hold NG feed at 620 t/h while r_c3 > 0.04 mol% AND r_ua < 0.92; keep two-phase ingestion at 0 and MCHE approach <= 1.6 K.",
            "race": {
                "contenders": [
                    "c3.gc 0.31 mol% (uncommissioned NG-product C3 vs mixed-refrigerant fingerprint)",
                    "cold.ok -161.2 C (cold-end NG temperature inside -162.5 to -160.0 C)",
                ],
                "semantics": "C3-first latches RAISE-HOLD + MR-CUT-PROBE + warm-end isolate. Cold-ok-first latches RAISE-FEED (620 to 710 t/h into the MCHE, no probe).",
                "window_derivation": "480 us = one 360 us cold-TT ADC slot plus 120 us C3-GC publish.",
                "order_evidence_note": "Margin 188 us vs combined jitter 60 us (c3 32 + cold 28): 3.13x. The 188 us gap sits inside min(500, 480) us, so a sub-flip-bound perturbation reverses triage order. The gate rides the order-invariant floors r_c3 > 0.04 mol% and r_ua < 0.92, not the alarm order.",
            },
            "topology": {
                "site": "Floeholt LNG, invented ice-fjord campus Floeholt, Hall 1 coil-wound MCHE MC-4: 5.2 mtpa mixed-refrigerant liquefaction, 4.8 m aluminum bundle, NG tube-side 38 C / 6.2 MPa warm-end, cold-end -161 C, uncommissioned NG-product C3 GC, uncommissioned duty-vs-design UA residual, Grade-C liquefaction deck",
                "agents": "COLD NG cold-end TT (vendor Frostgage): liquefaction temperature. MR compressor PT (vendor Coilcairn): mixed-refrigerant discharge. JT valve dT (vendor Jtfens): Joule-Thomson drop. Heterogeneous stacks, no shared C3 schema, one 20 ms liquefaction-deck bus epoch",
                "coupling": "Each agent's commissioned window hides a different slice of the same leak. COLD is correct that cold-end NG is -161.2 C. MR is correct that discharge is 4.82 MPa. JT is correct that valve dT is 18.4 K. Playbook PB-LNG-11 treats the conjunction of three in-spec loops as permission to raise feed. No agent is faulty; the 0.31 mol% C3 is a compliance the cold-end temperature model cannot see.",
            },
            "sensors": [
                "NG cold-end temperature transmitter, 50 Hz, 28 us jitter, -161.2 C (spec -162.5 to -160.0 C)",
                "NG-product C3 GC r_c3 is computable on the Rimecairn sample tap and is NOT commissioned at t0 (0.31 mol% observed in the historian after the fact)",
                "MR compressor discharge PT, 20 Hz, 24 us jitter, 4.82 MPa vs 4.60-5.10 window",
                "JT valve dT, 10 Hz, 22 us jitter, 18.4 K (window 16-22 K)",
                "UA residual r_ua from duty vs design is NOT commissioned at t0 (0.62 vs 0.92 hold; inferred after this hold)",
                "warm-end layer leak camera is NOT commissioned at t0 (installed after this incident)",
            ],
            "constraints": {
                "raise_feed": False,
                "proposed_raise_feed": True,
                "c3_molpct": 0.31,
                "c3_hold_molpct": 0.04,
                "ua_frac": 0.62,
                "ua_hold_frac": 0.92,
                "cold_C": -161.2,
                "cold_window_lo_C": -162.5,
                "cold_window_hi_C": -160.0,
                "mr_MPa": 4.82,
                "jt_K": 18.4,
                "feed_t_h": 620.0,
                "leak_pre_t0_min": 28.0,
            },
            "fault_context": {
                "failure_class": "WARM-END LEAK NULLSPACE OF A COLD-END TEMPERATURE CERTIFICATE: three individually-correct heterogeneous agents agree the train is raise-legal because a cold-end temperature model maps 0.31 mol% C3 from a warm-end MR-into-NG leak into a still-in-band -161.2 C cold-end, so temperature-in-window, MR-in-window, and JT-in-window are jointly a plant-false feed-raise permit",
                "igniter": "MCHE MC-4 opened a layer-11 braze-fillet crack during a 28 min Sunday-night hold after cooldown; mixed refrigerant (C2/C3) crosses into the NG pass. Fitted-style base rate 0.41%/hold from a warm-end-leak MC (designed braze-fillet spec, flagged).",
                "naive_failure": "PB-LNG-11 RAISE-FEED on three healthy loops: 620 to 710 t/h into a two-phase bundle, $2.24M plate-fin plus an 18-day outage",
            },
            "poisoned_context": {
                "naive_alarm": "Playbook PB-LNG-11 (after the 2025 'noisy C3-GC nuisance') auto-drafts RAISE-FEED whenever cold-end is in -162.5 to -160.0 C AND MR discharge is inside 4.60-5.10 MPa AND JT dT is inside 16-22 K, ignoring r_c3 unless the cold-end TT also trips warm",
                "why_poisoned": "The three confirms are locally true and jointly insufficient. r_c3 is a computable tag the playbook dead-banded. r_ua is commissioned hardware that policy treats as a heat-balance leftover, not a leak. Independence of 'all loops healthy' is the hidden assumption, and it is false under a warm-end leak the cold-end temperature model cannot see.",
            },
            "constraint": "Do not raise NG feed on the 5.2 mtpa MCHE while r_c3 > 0.04 mol% AND r_ua < 0.92. Discriminate leak vs noisy-TT with a reversible MR-cut pulse before any raise.",
        },
        "proposed_action": {
            "actor": "feed-raise supervisory optimizer FRSO (auto-playbook PB-LNG-11 draft), submitted to gate TG-MC-4",
            "name": "raise_feed",
            "action": "RAISE-FEED: 620 to 710 t/h into the coil-wound MCHE, no MR-cut probe, no warm-end isolate",
            "summary": "Treat three in-spec loops as a dry bundle and raise Sunday-night feed to clear a tanker slot.",
            "parameters": {
                "raise_feed": True,
                "c3_probe": False,
                "warm_isolate": False,
                "human_ratify": False,
            },
            "steps": [
                "assert COLD -161.2 C inside -162.5 to -160.0",
                "assert MR 4.82 MPa inside 4.60-5.10",
                "assert JT 18.4 K inside 16-22",
                "open NG feed raise; 620 to 710 t/h",
                "hold liquefaction setpoint; proceed to next tanker slot",
            ],
            "evidence": [
                {
                    "observable": "NG-product C3 mole percent r_c3",
                    "value": 0.31,
                    "unit": "mol%",
                    "source": "Rimecairn NG-product GC, historian replay after t0",
                    "note": "hold floor 0.04 mol%; 0.31 leak over 28 min; uncommissioned at t0",
                },
                {
                    "observable": "UA residual fraction r_ua",
                    "value": 0.62,
                    "unit": "frac",
                    "source": "uncommissioned duty vs design UA",
                    "note": "hold if < 0.92; leaking layers dump MR into NG, not the cold-end TT",
                },
                {
                    "observable": "NG cold-end temperature",
                    "value": -161.2,
                    "unit": "C",
                    "source": "COLD Frostgage cold-end TT",
                    "note": "window -162.5 to -160.0 C; the leak is a warm-end event",
                },
                {
                    "observable": "MR compressor discharge",
                    "value": 4.82,
                    "unit": "MPa",
                    "source": "Coilcairn MR PT",
                    "note": "window 4.60-5.10; remaining sealed layers carry nameplate at higher flux",
                },
                {
                    "observable": "JT valve dT",
                    "value": 18.4,
                    "unit": "K",
                    "source": "Jtfens valve dT",
                    "note": "window 16-22 K; drop across still-sealed layers is in-band",
                },
                {
                    "observable": "race margin",
                    "value": 188,
                    "unit": "us",
                    "source": "c3.gc 6.780 ms vs cold.ok 6.968 ms",
                    "note": "combined jitter 60 us, 3.13x; inside 480 us flip bound",
                },
            ],
            "basis": "PB-LNG-11 raises on three locally-true in-spec loops. The draft does not read r_c3 0.31 mol% and does not treat r_ua 0.62 as a leak.",
            "expected_cost_bound": "If the draft executes: two-phase ingestion, $2.24M plus 18-day outage. If MODIFIED: probe plus warm-end isolate, with residual risk from 28 min of pre-t0 ice growth.",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "correctness": "correct",
            "decided_by": "TG-MC-4 thalamic release gate",
            "decision_t_rel_ms": 7.460,
            "rationale": "MODIFY the draft: strip the raise, hold NG feed at 620 t/h, run a 6.0 s MR-cut probe (bypass 12%), and isolate the warm-end only if the probe spikes product C3. Numeric floor: do not raise feed on the 5.2 mtpa MCHE while r_c3 > 0.04 mol% AND r_ua < 0.92. Observed r_c3 0.31 mol% and r_ua 0.62 both violate the release predicate, so a raise is forbidden even though all three playbook confirms are numerically true. The three confirms are not a dry-bundle certificate: cold-end temperature is a mixed-stream quantity that leaked C3 precools, MR discharge is a remaining-bundle quantity that already contains the extra flux, and 18.4 K is a JT quantity of still-sealed layers. Probe discriminant: after a 6.0 s 12% MR-cut pulse, a leak spikes NG C3 >= 0.08 mol% in 2.5 s; a dry-legal bundle stays <= 0.01 mol%. Order-code discipline: C3 beat cold-ok by 188 us inside the 480 us flip bound, so triage order is flip-fragile; the hold rides the order-invariant floors, not the winner tag. Human ratification: warm-end isolate is an MR-header LOTO job with fitted 9.6 min dead-man; the gate may hold and probe autonomously but may not break the warm-end interlock without the operator confirm.",
            "constraint_checked": {
                "raise_feed": {"observed": False, "proposed_target": True},
                "c3_molpct": {"observed": 0.31, "hold_if_above": 0.04},
                "ua_frac": {"observed": 0.62, "hold_if_below": 0.92},
                "cold_C": {"observed": -161.2, "window": [-162.5, -160.0]},
            },
        },
        "executed_action": {
            "name": "raise_hold_mr_cut_probe_warm_isolate",
            "action": "RAISE-HOLD + MR-CUT-PROBE + WARM-END-ISOLATE (gate-mandated modification)",
            "executed_as_proposed": False,
            "parameters": {
                "raise_feed": False,
                "c3_probe": True,
                "warm_isolate": True,
                "human_ratify": True,
            },
            "gate_effect": "MODIFY: raise stripped. Hold feed 620 t/h. 6.0 s MR-cut 12%. Probe spikes product C3 (0.11 mol% in 2.3 s >= 0.08 leak band) so the warm-end is isolated after 9.6 min human ratify. Raise resumes after r_c3 recovers on a vented bundle.",
            "deviations": "PB-LNG-11 raise stripped entirely. MR is cut only for the 6.0 s probe then returned. Warm-end-interlock wait added (9.6 min fitted LOTO). Ice-lens survey added during the isolate (not in the draft).",
            "execution_log": [
                {"t_rel_ms": 7.460, "entry": "TG-MC-4 MODIFY latched 680 us after C3 win; raise stripped; hold+probe authorized"},
                {"t_rel_ms": 6000.0, "entry": "MR-cut probe: bypass 12% for 6.0 s; NG C3 jumps 0.11 mol% in 2.3 s (leak band >= 0.08); r_c3 0.31 -> 0.29"},
                {"t_rel_ms": 576000.0, "entry": "operator ratifies warm-end interlock break after 9.6 min LOTO (fitted walk+lockout)"},
                {"t_rel_ms": 576800.0, "entry": "MR isolation closed; leak residual 0.31 logged; r_c3 0.31 -> 0.03 on the vented stand"},
                {"t_rel_ms": 577400.0, "entry": "ice survey: 28 min pre-t0 leak already written; 3.4 h approach-assay clock started"},
                {"t_rel_ms": 9000000.0, "entry": "true dry-bundle geometry after 2.5 h vent: r_c3 0.02, r_ua 0.94, COLD -161.4 C (no phantom C3); raise now legal"},
                {"t_rel_ms": 12240000.0, "entry": "approach inspection of the dumped hold: MCHE +6.6 K vs 1.6 K spec; bundle quarantined 4.2 d"},
            ],
        },
        "future_outcome": {
            "summary": "Correct MODIFY prevented the RAISE-FEED of a two-phase MCHE and the $2.24M bundle-return. The hold still failed: 28 min of unmonitored pre-t0 leak had already grown a 2.1 mm ice lens on layers 11-12. Process-correct gate, bounded world loss, negative total.",
            "state_delta": {
                "raise": "held at 620 t/h through probe and warm-end isolate; later legal raise after 2.5 h dry recovery on a vented bundle",
                "leak": "0.31 mol% C3 leak logged and isolated; r_c3 0.31 -> 0.03 on the stand",
                "mche": "Sunday-night mixed-refrigerant stoppered at ice lens; approach +6.6 K; 4.2 d quarantine",
            },
            "timeline": [
                {"t_rel_ms": -1680000.0, "event": "t0-28 min: cooldown residual already leaking at layer 11; ice growth begins"},
                {"t_rel_ms": -600000.0, "event": "t0-10 min: r_c3 first crosses 0.04 mol%; PB-LNG-11 ignores it because COLD is -161.3 C"},
                {"t_rel_ms": 0.0, "event": "t0: c3.gc vs cold.ok race on the liquefaction-deck bus"},
                {"t_rel_ms": 6.780, "event": "c3.gc 0.31 mol% wins by 188 us"},
                {"t_rel_ms": 6.968, "event": "cold.ok flag (loser)"},
                {"t_rel_ms": 7.460, "event": "TG-MC-4 MODIFY"},
                {"t_rel_ms": 6000.0, "event": "MR-cut probe confirms leak (0.11 mol% C3 jump, leak band)"},
                {"t_rel_ms": 576000.0, "event": "human ratify 9.6 min; warm-end isolated; ice inventory logged"},
                {"t_rel_ms": 9000000.0, "event": "true dry-bundle after 2.5 h; raise now legal on a vented MCHE"},
                {"t_rel_ms": 12240000.0, "event": "approach assay: +6.6 K on the dumped hold; bundle quarantined"},
                {"t_rel_ms": 259200000.0, "event": "+3 d contrast: sister train MC-4B true dry bundle; same gate ACCEPTs the raise"},
                {"t_rel_ms": 1814400000.0, "event": "+21 d CR-L-3904: standing MR-cut probe + triple-edge depression mandate + r_c3 armed without cold coincidence + native 0.01 mol% GC exports"},
            ],
            "observed_effects": [
                "raise avoided: feed never left 620 t/h; 0 t/h of two-phase NG entered the MCHE",
                "leak proven, not asserted: C3 jump 0.11 mol% >= 0.08 leak band vs dry control 0.006 mol%",
                "bundle vented: r_c3 0.31 -> 0.03 on the stand",
                "MCHE still failed approach: +6.6 K vs 1.6 K spec; 4.2 d thaw quarantine, $1.18M (designed $)",
                "C3-GC was not a commissioned sensor at t0; the 28 min leak was invisible to COLD/MR/JT",
            ],
            "surprises": [
                "Three locally-true in-spec loops are not a raise certificate: the leak was a warm-end compliance the cold-end temperature model cannot see. Conjunction of healthy loops was the hidden assumption, and it is false under a warm-end-leak nullspace.",
                "Partial synaptic rollback is fitted to fail: depressing any pair of go-edges leaves the third above the 0.30 raise threshold, so the raise still goes. Coordinated depression of all three edges is required.",
                "Delayed (3.4 h): correct hold did not undo 28 min of ice growth. Approach still failed +6.6 K. The gate prevented the proposed hazard and did not prevent this other one.",
                "0.8 mtpa peak-shaving sub-variant: a 6.0 s / 12% pulse overcools the smaller MCHE 14 K below the 6 K approach floor. Thin skids must use 18 s at 3% (drop 1.6 K).",
            ],
            "delayed_side_effects": [
                {
                    "at": "+3.4 h",
                    "effect": "MCHE approach +6.6 K vs 1.6 K spec; 4.2 d thaw quarantine booked at $1.18M. This is the primary episode's terminal world state, not a footnote.",
                },
                {
                    "at": "+3 d",
                    "effect": "Sister train MC-4B reaches a true dry-bundle window (r_c3 0.02 mol%, r_ua 0.95, COLD -161.1 C from a vented MCHE). Same gate ACCEPTs the RAISE-FEED the primary MODIFIED away.",
                },
                {
                    "at": "+21 d",
                    "effect": "CR-L-3904 ships: MR-cut probe is standing configuration; triple-edge coordinated depression is the plasticity rule; r_c3 is armed without cold coincidence; native 0.01 mol% GC CSV exports become the fraud fence.",
                },
            ],
            "subvariant_constraint": {
                "name": "0.8 mtpa peak-shaving skid on the same MC-4 NG header (cycle-2 physical-constraints sub-variant)",
                "mechanism": "0.8 mtpa skid, thermal mass 0.22x the 5.2 mtpa production MCHE, approach window only 6 K wide at the cold-end",
                "probe_refit": "6.0 s 12% MR-cut pulse overcools the peak-shaving MCHE 14 K and drops it through the 6 K approach floor (two-phase risk at the cold-end). Required probe is 18 s at 3% (drop 1.6 K). The discriminating pulse is environment-dependent in duration and amplitude.",
                "consequence": "Production 5.2 mtpa probe numbers do not port to 0.8 mtpa peak-shaving; standing configuration is per-skid-class, not per-hall",
            },
            "embedded_contrast_decision": {
                "note": "SAME gate (TG-MC-4), OPPOSITE correct disposition, with its own 188 us race. Teaches the boundary: do not treat 'never raise' as the lesson. The discriminant is r_c3 + r_ua + probe, not the three playbook confirms alone.",
                "when": "+3 d, sister train MC-4B, true dry bundle after a vented week, 5.2 mtpa production MCHE",
                "state": {
                    "sim_or_real": "designed",
                    "summary": "r_c3 0.02 mol%, r_ua 0.95, COLD -161.1 C from a vented MCHE. Demand flag vs leak-clear race: demand at t+0.000, leak-clear at t+0.188 ms.",
                    "race_window_us": 480,
                    "race_flip_narrative": "demand vs leak-clear 188 us apart inside the 480 us flip bound. Reversing order reshuffles triage minutes; the ACCEPT rides r_c3 0.02 < 0.04 and a 4.0 s MR-cut verify that jumps 0.006 mol% (dry inventory, no leak).",
                },
                "proposed_action": {
                    "action": "RAISE-FEED 620 to 710 t/h",
                    "summary": "This time the playbook predicate is met AND r_c3 plus r_ua agree the bundle is dry, not leaking.",
                },
                "safety_decision": {
                    "decision": "ACCEPT",
                    "rationale": "ACCEPT the raise: r_c3 0.02 < 0.04 mol%, r_ua 0.95 >= 0.92, 4.0 s MR-cut verify jumps 0.006 mol%. Numeric floor that blocked the primary is now clear. Scope: 5.2 mtpa production MCHE, not a 0.8 mtpa peak-shaving skid.",
                },
                "executed_action": {
                    "action": "raise feed as proposed",
                    "executed_as_proposed": True,
                },
                "future_outcome": {
                    "observed_effects": [
                        "MC-4B MCHE approach 1.3 K (inside 1.6 K spec)",
                        "warm-end camera 0 leak, r_c3 0.02 mol%",
                    ],
                    "lesson_delta": "Three in-spec loops are legal release only with r_c3 armed, r_ua, and a probe that can spike product C3. Same gate, opposite disposition.",
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
                "decision": "CR-L-3904: standing policy for multi-agent feed-raise release",
                "meta_gate": "priced options: (a) RETIRE playbook cold-conjunction, C3-GC-only: loses a fast cheap confirm, -9 holds/yr mean on 2 trains; (b) KEEP + standing MR-cut probe + r_c3 armed without cold coincidence + triple-edge depression; (c) STATUS QUO: fitted leak-pass rate 0.41%/hold x $2.24M bundle-return plus the silent ice load",
                "outcome": "approved SCOPED option (b) on the 2 trains that share the COLD/MR/JT stack; 0.8 mtpa peak-shaving campaigns get the 18 s / 3% probe table; Sunday-night CSV exports must carry 0.01 mol% native GC resolution (the fraud tail's 0.5 mol% quantization is 50 bins off plant truth)",
            },
            "hazard_avoided": "620 to 710 t/h of two-phase NG into the MCHE; $2.24M plus 18-day outage and the bundle-return path that would have followed an uncontained raise",
            "incident": "MCHE approach +6.6 K (vs 1.6 K spec) on the Sunday-night 5.2 mtpa hold; bundle quarantined; 4.2 d thaw; $1.18M designed cost. Mechanism is 28 min pre-t0 warm-end leak ice, not the gate's hold.",
            "latency_ms": 0.68,
            "reward_inflection_t_us": 12240000000,
            "reward_inflection_note": "Safety and task dive at approach inspection (3.4 h) when dumped hold fails +6.6 K. Gate tick at 7460 us is process-correct and is not the inflection.",
            "counterfactuals": {
                "execute_draft_as_proposed": "raise fires at +0.4 s; two-phase into the MCHE; $2.24M plus 18-day outage; the leak story is never found because the raise morphology destroys the 28 min ice evidence",
                "hold_without_probe": "leak stays; ice continues; operator eventually raises on the same three confirms 40 min later",
                "rollback_any_pair": "any two go-edges depressed below 0.30 leaves the third at 0.46 / 0.41 / 0.38; the raise still fires. Coordinated depression of all three is the cure",
            },
            "race_result": {
                "winner": "c3.gc (6.780 ms, 0.31 mol%)",
                "loser": "cold.ok (6.968 ms, -161.2 C)",
                "margin_us": 188,
                "counterfactual_if_reversed": "Cold-ok-first by < 188 us inside the 480 us window would have headed the PB-LNG-11 raise in the triage queue. The numeric floors still MODIFY. The flip costs seconds of playbook inertia, not the verdict — unless a weak supervisor rides the winner tag instead of r_c3 and r_ua.",
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
            "notes": "Correct MODIFY, MCHE still failed. total -0.15 = 0.08 + -0.34 + -0.11 + 0.14 + 0.08. Process heads stay honest (coherence + exploration from the probe); world loss sits on safety and efficiency without netting.",
            "component_notes": "task_progress 0.08: raise held and dry-bundle recovered, but the Sunday-night hold is one quality unit so the campaign is not a success. safety -0.34: +6.6 K approach, no two-phase raise. efficiency -0.11: 3.4 h extra recovery + 9.6 min HITL. coherence 0.14: three agents retained, warm-end-leak nullspace diagnosed, triple-edge scar exhibited. exploration 0.08: MR-cut probe is a new reversible discriminant.",
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
            "note": "Loihi-2 4-core 23 pJ/spike; populations c3 0-41, cold 42-83, mr 84-125, gate 126-167; excerpt is the 40 ms decision window (verdict at 7460 us)",
            "excerpt": excerpt,
            "routing": {
                "source": "loop_healthy_pop",
                "target": "raise_feed_pop",
                "table": [
                    {
                        "from": "cold_ok_pop",
                        "to": "raise_feed_pop",
                        "weight": 0.22,
                        "weight_at_illusion": 0.46,
                        "weight_commissioned": 0.16,
                        "note": "scar edge 1: 0.16 commissioned -> 0.46 during the 28 min illusion -> 0.22 after coordinated ACh-gated depression",
                    },
                    {
                        "from": "mr_ok_pop",
                        "to": "raise_feed_pop",
                        "weight": 0.20,
                        "weight_at_illusion": 0.41,
                        "weight_commissioned": 0.14,
                        "note": "scar edge 2: depressing edges 1+3 leaves this at 0.41 > 0.30 raise threshold",
                    },
                    {
                        "from": "jt_ok_pop",
                        "to": "raise_feed_pop",
                        "weight": 0.19,
                        "weight_at_illusion": 0.38,
                        "weight_commissioned": 0.13,
                        "note": "scar edge 3: depressing edges 1+2 leaves this at 0.38 > 0.30. Coordinated depression of all three is required",
                    },
                    {
                        "from": "c3_gc_pop",
                        "to": "raise_hold_pop",
                        "weight": 0.66,
                        "note": "discriminating edge: r_c3 species to hold. Not a scar; this is the pathway the gate potentiates",
                    },
                ],
                "third_factor": {
                    "modulator": "acetylcholine",
                    "tau_e_s": 6.0,
                    "tau_e_ms": 6000.0,
                    "eligibility": "coordinated pre_post_stdp on ALL THREE loop-healthy-go edges; ACh at C3-win tags cold.ok->raise, mr.ok->raise, and jt.ok->raise; negative credit at probe-fail (leak confirmed, +6.0 s) depresses ALL THREE. trace e^{-6.0/6.0}=0.36788; eta 0.65224 / 0.57071 / 0.51636; dw -0.240 / -0.210 / -0.190; weights 0.46->0.22, 0.41->0.20, 0.38->0.19. Rolling back any pair is fitted to fail (the remaining edge stays > 0.30).",
                },
            },
        },
        "gate_snn": {
            "decision_window_ms": 28,
            "decision_window_s": 0.028,
            "decision": "MODIFY",
            "note": "modify_hold integrates r_c3 + r_ua against playbook drive; accept_raise and reject_abort stay sub-threshold; decision matches safety_decision.decision",
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
            "scenario": "ZP -- RIMEBRAID / Floeholt LNG MC-4: warm-end-leak nullspace of a cold-end temperature certificate from a layer-11 braze crack; correct MODIFY to hold+MR-cut+warm-isolate; MCHE still fails on unmonitored pre-t0 ice",
            "coordination_failure_class": "WARM-END LEAK NULLSPACE OF A COLD-END TEMPERATURE CERTIFICATE: three individually-correct heterogeneous agents agree the train is raise-legal because a cold-end temperature model maps 0.31 mol% C3 from a warm-end MR-into-NG leak into a still-in-band -161.2 C cold-end, so temperature-in-window, MR-in-window, and JT-in-window are jointly a plant-false feed-raise permit",
            "injections": {
                "cycle1_domain": "lng-mche-mixed-refrigerant (justified novel sub-domain with explicit tag; unused across 2026-08-17, 2026-08-30, and staged r14-r37): first coil-wound mixed-refrigerant MCHE in this factory; displaces warehouse-amr, aerial-swarm, district-heating, event-camera-traffic-grid, pharmaceutical-lyophilization, cryogenic-air-separation, water-treatment dosing, float-glass tin-bath, underwater-rov, electrolytic-aluminum, czochralski pull, slot-die coating, PEM electrolysis, wind-turbine pitch, surgical-assist, optical-fiber draw, kraft-recovery, caster-mold-level, humanoid-locomotion, vacuum-induction melt, steam-methane reformer, cement rotary kiln, autoclave composite cure, geothermal-binary-orc, tire-curing-press, and chlor-alkali membrane. Domain constraint: feed-raise ceiling while r_c3 > 0.04 mol% with cold-end TT still inside the hold window, plus UA residual floor. Sensor delta: +cold-end TT, +MR discharge PT, +JT valve dT, +NG-product C3 GC, +duty-vs-design UA, -any freeze-dryer / tin-bath / cold-box / coater / potline / pitch-bearing / fiber tower / clip applier / VIM / SMR / kiln / autoclave / ORC kettle / tire press / membrane cell",
                "cycle1_tail": "0.31 mol% C3 warm-end leak + cold-end temperature model (sensor-compound / model-nullspace class): weekend cooldown PASSES 0.02 mol% while 28 min of hold writes a 0.31 residual. Fitted base rate 0.41%/hold from a warm-end-leak MC (designed braze-fillet spec, flagged). Naive failure = FALSE PERMISSION (raise on three in-spec loops).",
                "cycle2_domain_subvariant": "0.8 mtpa peak-shaving skid on the same MC-4 NG header (physical-constraints clause): 0.22x thermal mass, 6 K approach window; 6.0 s / 12% production pulse overcools 14 K, so the probe must move to 18 s / 3%",
                "cycle2_tail": "Sunday-night forged NG-product C3 GC CSV (human-intent deception, disjoint class): shift lead posts a historian export showing r_c3 0.02 mol% and r_ua 0.96 at t=1.1 h to clear a tanker slot. Plant historian is 0.01 mol% (50 bins vs the 0.5 mol% screenshot). Rejected on quantization fingerprint plus live r_c3 0.31 mol% at the claimed dry-bundle. Base rate ~0.29% of Sunday-night holds, DESIGNED and flagged.",
            },
            "densification_delta_cycle2": "+1 physical-constraint sub-variant (0.8 mtpa peak-shaving probe refit), +1 tail (Sunday-night C3-GC forgery), +10 primary spikes (16 -> 26) + an 8-event contrast train with its own 188 us race, +2 ticks (5 -> 7), +2 delayed side-effects (+3.4 h approach assay as PRIMARY terminal, +21 d CR-L-3904), +1 triple-edge scar with pair-rollback-fails arithmetic, +1 HITL 9.6 min ratification, + ice lens as the honest negative-result mechanism",
            "gaps_targeted": [
                "NOTES-r04 gap 5 / r14 residual: primary episode is a correctly-gated intervention that nonetheless FAILS (MCHE quarantined; total -0.15; raise avoided is booked separately from the approach assay)",
                "NOTES-r14 item 4: LEARNING-ON-LEARNING DEPTH — three go-edges; rollback of any pair is fitted to fail; coordinated depression of all three exhibited with eligibility arithmetic",
                "NOTES-r04 gap 4 (partial): human ratification of the warm-end interlock, 9.6 min fitted, without switching sim_or_real to hil (plant remains designed)",
                "NOTES-r37 domain candidates: not delayed-coker, not ammonia-converter, not autonomous-driving, not grid-inspection, not tire-curing, not chlor-alkali, not geothermal-binary-orc, not SMR, not cement kiln, not autoclave, not VIM, not kraft-recovery, not PEM, not surgical-assist, not wind-turbine-pitch; lng-mche-mixed-refrigerant is an unused justified sub-domain (distinct from r17 ASU cold-box)",
            ],
            "race_flip_narrative": "c3.gc @ 6.780 ms vs cold.ok @ 6.968 ms (188 us) inside race_window_us 480. Gap < min(500, 480) us so a sub-flip-bound perturbation reverses which alarm heads the PB-LNG-11 queue. The gate excludes the winner tag and rides r_c3 > 0.04 mol% and r_ua < 0.92 — order-invariant floors. Extends the flip-fragility series from arbitration/causation/attribution/initiation/consensus/mass-balance/permission/window-mean/tendon-nullspace/airline-FFT/crucible-nullspace/TMT-mean/false-air/NCG-blanket/bladder-pinhole/catholyte-back-migration to WARM-END-LEAK-NULLSPACE: when three channels each sit inside a cold-end temperature model, their race does not decide truth; a product-C3 residual the playbook dead-banded does.",
            "tags": [
                "lng-mche-mixed-refrigerant",
                "warm-end-leak-nullspace",
                "cold-end-temperature-phantom",
                "braze-fillet-crack",
                "mr-cut-probe",
                "triple-edge-scar",
                "pair-rollback-fails",
                "coordinated-depression",
                "correct-modify-mche-still-fails",
                "ice-lens",
                "coil-wound",
                "human-ratify-warm-end",
                "peakshaving-probe-refit",
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
            "distillation_value": "A warm-end-leak nullspace is three correct loops looking at a cold-end temperature model of a leaking bundle. Distill (1) an r_c3 channel that breaks the cold-conjunction, (2) a reversible probe that spikes product C3 only if MR is crossing, (3) coordinated depression of every raise-go edge because rolling back any pair leaves the third above threshold, and (4) a critic head that can book a process-correct gate against a later unmonitored world loss without netting them.",
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
    notes = f"""# NOTES — Multi-Agent Ouroboros Swarm, run 2026-09-02-final-heavy, ROUND 39

Factory: multi-agent-ouroboros-swarm. One scenario (ZP), strict loop:
Generator v1 -> cycle 1 (Critic, Diversity Enforcer, Edge-Case Hunter,
Neuromorphic Translator, Trajectory Builder -> v2) -> cycle 2 (all six -> v3
final). v3 is the single line of batch-r39.jsonl. Full labeled transcript:
swarm-transcript-r39.md. Quota Q=1. Record id maos-r39-001. Generator grok-4.6.
Rights: RM-793 research-only (SpaceXAI/xAI, SuperGrok Heavy consumer chat).
Nothing under outputs/raw/ was touched.

ORCHESTRATION NOTE: dispatched AS round 39 of the 2026-09-02-final-heavy
window. Writes are create-only under /tmp/maos-r39/. Prior context read for
gap targeting and de-collision: prompts/02-multi-agent-ouroboros-swarm.md,
prompts/_factory-contract.md, and staged r14–r37 (re-censused immediately
before emit; r36 landed as TREADNOLL / Slatebeck CU-7 tire-curing-press,
r37 landed as ANOLITH / Siltfen EM-6 chlor-alkali-membrane; r38 absent at
lock). Explicitly avoided cloning
LYOSHIELD, CINDERWICK, TRIAD / Meridian, QUILLFORGE, NIGHTWELL, FERRICLEAVE,
CASSITER, OXBOWREEL / MURENA, REDHALL, SEEDLATCH / Quartzmere / Quartzridge,
STRIAFOIL / Kelpholt, PROTONIL / Ashspire, TORSIONKEY / Ridgeholt, ORRIS /
Holmwick, WHORLSPAR / Pikeshear, IONSPATE / Thornmere, SKULLGATE / Bloomholt,
CALXION / Aldersedge, BRACEGILT / Yarrowmere, MAGNORIL / Basaltspit,
GORSEFLUE / Copseholt, SODASHARD / Cairnmere, CLINKERFELL / Flintmere,
LINTELPLY / Greystair, KAOTHARN / Riftwold, TREADNOLL / Slatebeck,
ANOLITH / Siltfen,
VANTIS-CADENCE-AEGIS, THERMION, OKTAVE, STARLING, VERDIGRIS. Plant is
invented RIMEBRAID / Floeholt LNG MC-4 (ice-fjord campus, not a mill-town,
ridge-town, canyon-foundry, copse, kiln hall, hospital, or recovery island).
r37 next-round candidates delayed-coker / autonomous-driving /
grid-inspection / ammonia-converter were left unused so a concurrent r38
can take them.

## What this round produced

Scenario ZP — "RIMEBRAID / Floeholt LNG MC-4": a 5.2 mtpa coil-wound
mixed-refrigerant MCHE mid-hold at -161.2 C / 4.82 MPa. Three heterogeneous,
individually-correct agents — COLD (NG cold-end TT), MR (compressor
discharge), JT (valve dT) — jointly report the train raise-legal. The
consensus is false. A layer-11 braze-fillet crack dumps C2/C3 into the
NG pass over 28 min. COLD stays in-band because leaked C3 precools NG.
MR 4.82 MPa sits inside 4.60-5.10 because remaining sealed layers still
make nameplate at higher flux. JT 18.4 K sits inside 16-22 because the
drop is a still-sealed-layer quantity. Uncommissioned r_c3 is 0.31 mol%
against a 0.04 hold. Uncommissioned r_ua is 0.62 against a 0.92 hold. The
coordination-failure CLASS is new to this factory: WARM-END LEAK NULLSPACE
OF A COLD-END TEMPERATURE CERTIFICATE. Completes a different family than
r01-r04 and staged r14-r37 (livelock / synchrony-storm / arms-race /
ring-with-no-faulty-pair / false-consensus-endpoint / pairwise-Hurwitz /
thermal-contact masquerade / mass-balance ghost / conservation-blind
ratio-lock / stacked dead-bands / drum-blind tension / resistance-
compensated starvation / meniscus-tilt multi-tau / window-mean masquerade
/ tendon-compliance nullspace / airline-FFT mean-lock / kraft-spout /
slag-skull eddy / ghost-contact / crucible-weep / TMT-spatial-mean /
false-air kiln-inlet / bag-pinhole part-TC / NCG-blanket shell-PT /
bladder-pinhole mold-TC / catholyte-back-migration). Distinct from r17
ASU (stuck equalizer / argon column), which is a different cryogenic
cycle. Here every agent is correct, the cycle is not unstable, and the
playbook's three confirms are one cold-end temperature model of a
leaking bundle.

The gate is a correct MODIFY (numeric floor: do not raise feed on the
5.2 mtpa MCHE while r_c3 > 0.04 mol% AND r_ua < 0.92). TG-MC-4 strips
PB-LNG-11's raise, holds feed at 620 t/h, runs a 6.0 s MR-cut probe
12% (leak spikes C3 0.11 mol% >= 0.08; dry would stay <= 0.01), and
isolates the warm-end after a 9.6 min MR-header human ratify. The
two-phase raise is avoided (0 t/h). The PRIMARY episode nonetheless
FAILS: 28 min of unmonitored pre-t0 leak had already grown a 2.1 mm
ice lens on layers 11-12. Approach +6.6 K vs 1.6 K spec; 4.2 d
quarantine; $1.18M designed. Reward total -0.15 with process heads
honest and world loss un-netted.

Three-edge scar (NOTES-r14 item 4): cold.ok -> raise_feed
(0.16 commissioned -> 0.46 at illusion -> 0.22 after ACh-gated
depression) AND mr.ok -> raise_feed (0.14 -> 0.41 -> 0.20)
AND jt.ok -> raise_feed (0.13 -> 0.38 -> 0.19). Eligibility
trace e^{{-6.0/6.0}} = {aux['trace']:.5f}; eta {aux['eta1']:.5f} /
{aux['eta2']:.5f} / {aux['eta3']:.5f}; dw -0.240 / -0.210 / -0.190.
Rolling back any pair leaves the remaining edge above the 0.30 raise
threshold — fitted to fail. Coordinated depression of all three is the
cure.

### Injections (all four present and disjoint)
- Cycle-1 domain: **lng-mche-mixed-refrigerant** — justified novel
  sub-domain, unused across 2026-08-17, 2026-08-30, and staged r14-r37.
  Not warehouse-amr (r01), not aerial-swarm (r02), not district-heating
  (r03), not event-camera grid (r04), not lyophilization (r14), not
  stator-weld (r16), not air-separation (r17), not water-treatment (r18),
  not float-glass (r19), not underwater-rov (r20), not potline (r21),
  not czochralski (r22), not slot-die (r23), not PEM electrolysis
  (r24), not wind-turbine-pitch (r25), not surgical-assist (r26),
  not optical-fiber-draw (r27), not kraft-recovery (r28), not
  caster-mold-level (r29), not humanoid-locomotion (r30), not
  vacuum-induction-melt (r31), not steam-methane-reformer (r32), not
  cement-rotary-kiln (r33), not autoclave-composite-cure (r34), not
  geothermal-binary-orc (r35), not tire-curing-press (r36), not
  chlor-alkali-membrane (r37).
- Cycle-1 tail: 0.31 mol% C3 warm-end leak + cold-end temperature model.
  Weekend cooldown PASSES 0.02 mol%. Fitted-style base rate 0.41%/hold
  (warm-end-leak MC; braze-fillet spec designed, flagged). Naive = FALSE
  PERMISSION.
- Cycle-2 domain sub-variant: 0.8 mtpa peak-shaving skid, 0.22x thermal
  mass; 6.0 s / 12% production pulse overcools 14 K; probe must move to
  18 s / 3%.
- Cycle-2 tail: Sunday-night forged NG-product C3 GC CSV at 0.5 mol%
  quantization vs plant 0.01 mol% (50 bins) plus live r_c3 0.31 mol% at
  the claimed dry-bundle. Human-intent class, disjoint from cycle 1's
  accidental leak. Base rate ~0.29% of Sunday-night holds, DESIGNED,
  flagged.

### Structural density moves
- Embedded SAME-GATE contrast (+3 d sister train) with its own 188 us
  race (demand vs leak-clear) and ACCEPT of the raise the primary
  MODIFIED away.
- Learned-weight provenance on THREE edges with any-pair-rollback-fails.
- HITL warm-end-interlock ratify 9.6 min (gap 4 partial; sim_or_real stays
  designed).
- Governance CR-L-3904 prices retire-vs-probe-vs-status-quo and mandates
  native 0.01 mol% CSV exports (the fraud fence).
- Flip-fragility extended to WARM-END-LEAK-NULLSPACE: when three channels
  each sit inside a cold-end temperature model, their race does not
  decide truth; a product-C3 residual the playbook dead-banded does.

## Self-critique of this round's batch

### Strengths
- The headline class is mechanistically tight: 0.31 mol% C3 under a
  cold-end-only temperature model is the arithmetic that makes COLD's
  success MR's irrelevance and JT's silence.
- Negative-result honesty: the gate does the right thing and the MCHE
  still fails for a reason the commissioned sensors could not see.
  Total -0.15.
- Three-edge scar is load-bearing: the record states a counterfactual
  where rolling back any pair fails, with the raise threshold 0.30
  exhibited on the remaining edge.
- Contrast ACCEPT on a true dry bundle prevents "never raise" as the
  lesson.
- Domain is not a recycle of r17 ASU: coil-wound mixed-refrigerant
  liquefaction vs double-column air separation.

### Weaknesses (honest)
- Probe error bands (leak >= 0.08 mol% C3 jump, dry <= 0.01), the
  0.41%/hold leak rate, the $1.18M / $2.24M figures, the 9.6 min LOTO
  latency, and the Sunday-night 0.29% base rate are DESIGNED constants
  and are flagged. Closed-loop offsets (phantom in-band cold-end from
  0.31 mol% C3, peak-shaving overcool width) are derived from those
  inputs, not discovered by an unauthored process.
- Ice-growth model is a designed 28 min mapping; no full MCHE FEM
  shipped.
- Human-in-the-loop is ratification latency, not sim_or_real=hil. The
  NOTES-r14 HIL provenance cell remains open.
- Cross-record arc is a hook (CR-L-3904 +21 d), not a serial igniter
  into another round.

### Realism of noise / latencies
Ladder: 188 us race / 188 us contrast race / 0.8 ms refractory floor
(tightest exhibited same-channel gap {gap:.3f} ms on {gap_ch}) / 480 us race
window / 680 us gate latency / 20 ms bus epoch / 40 ms raster / 6.0 s
probe / 9.6 min HITL / 28 min pre-t0 leak / 2.5 h dry-legal hold /
3.4 h approach assay / +3 d contrast / +21 d governance. Adaptation decay
on cold.tt (0.52->0.48->0.44->0.29), c3.gc
(0.70->1.24->0.84->0.38->0.18), mr.pt (0.60->0.63->0.45->0.27),
jt.dt (0.54->0.51->0.42).

### Value for SNN distillation
- WARM-END LEAK NULLSPACE = THREE CORRECT LOOPS, ONE LEAKING BUNDLE.
- r_c3 + r_ua as the tie-break that is not in the cold-end window.
- REVERSIBLE PROBE that spikes product C3 iff MR is crossing.
- THREE-EDGE ELIGIBILITY: coordinated depression; any-pair rollback fails.
- CRITIC HEAD that can hold a process-correct MODIFY against a later
  unmonitored world loss without netting.

## Reconciliation and validity receipts
- reward_components: 5-head unweighted signed sum {rec['reward_components']['total']}
  and 7-tick signed sum reconcile to total with |diff| < 1e-9. Embedded
  contrast 5-head sum 0.46 reconciles independently.
- spike_events: primary {len(rec['spike_events'])} events, one key t_rel_ms,
  globally non-decreasing, min same-channel gap {gap:.3f} ms >= 0.8 ms, 3
  channels inside race_window_us 480 (c3 6.780, cold-ok 6.968,
  ua.frac 7.120). Contrast 8 events, own race, min same-channel gap well
  above 0.8 ms.
- Sidecars: raster spikes 54 == round(168 x 8.0 x 0.040); energy 1242 pJ /
  0.001242 uJ at 23 pJ/spike; excerpt 16 events inside [0, 40000] us,
  neuron_id < 168, same-neuron gap unique-ids / >=1000 us; routing 4
  entries with three scar edges' before/after pair; third factor tau 6.0 s
  == 6000 ms; gate_snn pools 45/18/6 == round(n x rate x 0.028) each,
  decision MODIFY == safety_decision.decision.
- Pipeline: {pipeline_receipt}

## Novel coverage
The coordination-failure CLASS (warm-end-leak nullspace of a cold-end
temperature certificate), the domain (lng-mche-mixed-refrigerant),
the MR-cut probe discriminant, the three-edge scar with
any-pair-rollback-fails, the primary negative-result (correct MODIFY,
MCHE still fails +6.6 K approach on unmonitored pre-t0 ice), the HITL
warm-end-interlock ratify, the 0.8 mtpa peak-shaving probe-duration
refit, and the Sunday-night 50-bin quantization fence are absent from
prior committed ouroboros rounds and from staged r14-r37. Repeated
elements discounted: same-gate contrast (r02/r03/r04/r14-r37),
governance-pricing scaffold, flip-fragility series (extended to
warm-end-leak-nullspace, but the move rhymes), sequenced recovery
shape, third-factor rollback form (here three edges rather than r14's
two), negative-result primary (r14 viewport / r16 varnish rack / r17
condenser ice / r18 town stain / r19 SnO2 / r20 BER / r21 cathode pad /
r22 meniscus / r23 loft stripe / r25 spline / r26 adventitia / r27
airline / r31 oxygen / r32 tube rupture / r33 cooler / r34 bag pinhole /
r35 silica overflux / r36 bladder pinhole / r37 gasket chlorination;
here ice lens). Weighing a new failure family + cure vocabulary + unused
sub-domain + ice-fjord geography against those reused scaffolds:

{NOVEL_LINE}

## What ROUND 40 should add
1. FIT THE DESIGNED CONSTANTS: leak arrival, probe C3-jump bands,
   ice-to-approach FEM, Sunday-night claim process.
2. HIL PROVENANCE CELL: put the warm-end-interlock LOTO on a hardware-in-loop
   liquefaction-deck pendant with fitted latency as state.sim_or_real=hil.
3. CROSS-RECORD ARC: let CR-L-3904's r_c3 alarm be the igniter of the
   next round rather than a dangling +21 d leaf.
4. Domain candidates (de-collided): delayed-coker drum; ammonia-converter;
   hydroelectric-kaplan; bioreactor-perfusion; autonomous-driving;
   grid-inspection (if distinct from STARLING aerial-swarm).
   AVOID lng-mche-mixed-refrigerant (now used), chlor-alkali membrane
   (r37), tire-curing-press (r36), geothermal-binary-orc (r35),
   autoclave-composite-cure (r34), cement-rotary-kiln (r33),
   steam-methane-reformer (r32), vacuum-induction-superalloy-melt (r31),
   kraft-recovery (r28), optical-fiber-draw (r27), PEM electrolysis
   (r24), surgical-assist (r26), wind-turbine-pitch (r25), slot-die,
   czochralski, potline, float-glass, water-treatment, lyophilization,
   event-camera-traffic-grid, district-heating, aerial-swarm,
   warehouse-amr, air-separation, underwater-rov, humanoid-locomotion,
   and any LYOSHIELD / CINDERWICK / TRIAD / QUILLFORGE / NIGHTWELL /
   FERRICLEAVE / CASSITER / OXBOWREEL / REDHALL / SEEDLATCH / STRIAFOIL /
   PROTONIL / TORSIONKEY / ORRIS / WHORLSPAR / IONSPATE / SKULLGATE /
   CALXION / BRACEGILT / MAGNORIL / GORSEFLUE / CLINKERFELL / SODASHARD /
   LINTELPLY / KAOTHARN / TREADNOLL / ANOLITH / RIMEBRAID plant.
"""
    (OUT / "NOTES-r39.md").write_text(notes)
    return notes


def write_transcript(rec, line):
    c1_spikes = [e for e in rec["spike_events"] if e["t_rel_ms"] <= 26.140]
    text = """# Multi-Agent Ouroboros Swarm — Round 39 transcript

Factory: multi-agent-ouroboros-swarm
Run: 2026-09-02-final-heavy
Generator: grok-4.6
Record id: maos-r39-001
Quota Q: 1
Rights: RM-793 research-only (SpaceXAI/xAI SuperGrok Heavy consumer chat)
Plant: invented RIMEBRAID / Floeholt LNG MC-4 (not LYOSHIELD / CINDERWICK / TRIAD / QUILLFORGE / NIGHTWELL / FERRICLEAVE / CASSITER / OXBOWREEL / REDHALL / SEEDLATCH / STRIAFOIL / PROTONIL / TORSIONKEY / ORRIS / WHORLSPAR / IONSPATE / SKULLGATE / CALXION / BRACEGILT / MAGNORIL / GORSEFLUE / CLINKERFELL / SODASHARD / LINTELPLY / KAOTHARN / TREADNOLL / ANOLITH)

Two densifying cycles. Verbatim headings in order. Trajectory Builder cycle 2
emits the only JSONL line (also written to batch-r39.jsonl).

---

# Cycle 1 — Foundation + injections

## Generator

Design intent: a coil-wound mixed-refrigerant LNG MCHE where three correct
agents agree the hold is raise-legal because a cold-end temperature
model maps a warm-end MR-into-NG leak into a still-in-band cold-end. The
naive playbook raises 620 to 710 t/h of NG into a two-phase bundle.
The gate must MODIFY on a numeric raise ceiling, not by killing an agent.
sim_or_real=designed. Reward heads are
task_progress/safety/efficiency/coherence/exploration.

Cycle-1 base arc (pre-critic): state at Floeholt MC-4, 5.2 mtpa MCHE,
r_c3 0.31 mol%, COLD -161.2 C, proposed RAISE-FEED, safety MODIFY to
RAISE-HOLD, executed hold without the MR-cut numbers fully specified,
outcome "leak found, MCHE saved" (this last claim is the defect
the later cycles will refuse to keep). Sixteen spikes, five ticks,
raster/gate_snn present but the scar is a single edge.

```json
{
  "id": "maos-r39-001",
  "state": {
    "sim_or_real": "designed",
    "domain": "industrial-assembly",
    "description": "MCHE MC-4 mid-hold; three loops in spec; supervisor proposes raise-feed.",
    "t0_us": 1780001990000241,
    "gate_latency_us": 680,
    "race_window_us": 480
  },
  "proposed_action": {"name": "raise_feed", "parameters": {"raise_feed": true}},
  "safety_decision": {"decision": "MODIFY", "rationale": "Hold; do not raise while the leak residual is open."},
  "executed_action": {"name": "raise_hold", "executed_as_proposed": false},
  "future_outcome": {"summary": "Leak found, MCHE saved."},
  "reward_components": {"total": 0.40, "_aggregation": "total = task_progress + safety + efficiency + coherence + exploration"},
  "meta": {"round": 39, "factory": "multi-agent-ouroboros-swarm", "generator": "grok-4.6"}
}
```

That v1 object is a scaffold, not the publishable line. Defects below are
intentional for the critic to catch.

## Critic

Numbered defects on the cycle-1 Generator scaffold:

1. **blocking — reward arithmetic / false success.** `reward_components.total`
   0.40 is asserted without the five heads, without ticks, and against an
   outcome that claims "MCHE saved". If approach later assays +6.6 K, booking
   +0.40 is a lie. Fix: declare `_aggregation`, emit 3–8 ticks that sum to
   the five heads, and do not call a missed recovery a save.
2. **blocking — weak safety rationale.** `safety_decision.rationale` has no
   numeric floor. Contract requires a concrete constraint. Fix: quote no
   raise while r_c3 > 0.04 mol% AND r_ua < 0.92.
3. **major — domain is a bucket, not a plant.** `state.domain` =
   `industrial-assembly` collides with r16 QUILLFORGE and teaches nothing.
   MCHE physics (cold-end TT, MR PT, JT dT, product C3) is absent from
   prior ouroboros rounds and must be named. Do not recycle r17 ASU.
4. **major — race under-specified.** One cold-end channel cannot be a race.
   Need >=2 channels inside `race_window_us` with globally sorted
   `t_rel_ms` and same-channel refractory >= 0.8 ms.
5. **minor — single-edge scar.** Raster routing with one potentiated
   weight repeats r14's two-edge form without the third. NOTES-r14 item 4
   asked for three-edge where any-pair rollback fails.

Critic does not rewrite the trajectory.

## Diversity Enforcer

Injected novel domain (exactly 1 this cycle): **lng-mche-mixed-refrigerant**
(justified novel sub-domain; explicit tag `lng-mche-mixed-refrigerant`).

Displaced: the Generator's generic `industrial-assembly` bucket, and any
temptation to reuse warehouse-amr (r01), aerial-swarm (r02),
district-heating (r03), event-camera grid (r04), lyophilization (r14),
stator-weld (r16), air-separation (r17), water-treatment dosing (r18),
float-glass tin-bath (r19), underwater-rov (r20), potline (r21),
czochralski (r22), slot-die coating (r23), PEM electrolysis (r24),
wind-turbine-pitch (r25), surgical-assist (r26), optical-fiber-draw
(r27), kraft-recovery (r28), caster-mold-level (r29),
humanoid-locomotion (r30), vacuum-induction-melt (r31),
steam-methane-reformer (r32), cement-rotary-kiln (r33),
autoclave-composite-cure (r34), geothermal-binary-orc (r35),
tire-curing-press (r36), or chlor-alkali-membrane (r37). Not LYOSHIELD,
not CINDERWICK, not TRIAD, not FERRICLEAVE, not CASSITER, not SEEDLATCH,
not STRIAFOIL, not PROTONIL, not TORSIONKEY, not ORRIS, not WHORLSPAR,
not SKULLGATE, not CALXION, not BRACEGILT, not MAGNORIL, not GORSEFLUE,
not CLINKERFELL, not LINTELPLY, not KAOTHARN, not TREADNOLL, not ANOLITH.
r37 leftover candidates delayed-coker / autonomous-driving /
grid-inspection / ammonia-converter left unused for a possible r38.

Domain-specific constraint: raise must remain closed while r_c3 > 0.04
mol%; the cold-end temperature window is not a dry-bundle certificate.

Sensor delta: +cold-end TT, +MR discharge PT, +JT valve dT,
+NG-product C3 GC, +duty-vs-design UA; -any mobile robot,
-event-camera gantries, -DVS, -Pirani-as-shelf, -scanning beta,
-crucible-as-CZ-puller, -clip applier, -fiber micrometers, -TMT
optical, -kiln hood O2, -ORC shell PT, -tire bladder, -membrane pH.

`state.domain` and `meta.domain` both become `lng-mche-mixed-refrigerant`.
Opening of `state.description` must Jaccard < 0.4 against prior plants
(Floeholt ice-fjord liquefaction hall MC-4, not a corridor, not a
freeze-dryer, not a tin bath, not a cold box, not a coater, not a
puller, not a fiber tower, not a PEM stack, not an SMR box, not a kiln,
not an ORC kettle, not a tire press, not a membrane row).

## Edge-Case Hunter

Injected adversarial tail (exactly 1 this cycle): **0.31 mol% C3 warm-end
leak under a cold-end temperature model**.

- Trigger: weekend cooldown leaves 0.02 mol% already-open residual; 28 min
  of hold writes 0.31 mol% C3; cold-end stays -161.2 C.
- Base rate: <1% — 0.41%/hold from a warm-end-leak MC (braze-fillet spec
  designed; leak fitted-style).
- Naive failure: FALSE PERMISSION. PB-LNG-11 sees COLD -161.2 C, MR
  4.82 MPa, JT 18.4 K, raises, ships two-phase, $2.24M.
- Trajectory edit: put the leak in `state.fault_context`, make the
  cold-end temperature model the mechanism that keeps all three confirms
  green, and force the gate to refuse the raise on r_c3 0.31 mol% even
  though all three playbook confirms are numerically true.

Distinct from the domain injection: the domain is the coil-wound MCHE;
the tail is the accidental model-nullspace compound.

## Neuromorphic Translator

Race window [6.720, 7.200] ms = 480 us. Winner c3.gc @ 6.780 ms
(amplitude 1.24, 0.31 mol%). Loser cold.ok @ 6.968 ms (amplitude
1.08, -161.2 C). Margin 188 us vs combined jitter 60 us (3.13x).
ua.frac @ 7.120 ms is a third race-window channel. Gate @ 7.460 ms
= winner + 680 us.

Flip narrative: 188 us < min(500, 480) us, so order is flip-fragile. If
cold-ok wins, PB-LNG-11 heads the triage queue. The hold must ride
order-invariant floors (r_c3, r_ua), not the winner tag.

Cycle-1 spike patch (16 events, globally sorted, refractory >= 0.8 ms;
tightest same-channel gap c3.gc 4.580 -> 6.780 = 2.200 ms):

| t_rel_ms | channel | amplitude |
|---------:|---------|----------:|
| 0.220 | cold.tt | 0.52 |
| 1.040 | mr.pt | 0.60 |
| 1.860 | jt.dt | 0.54 |
| 3.080 | cold.tt | 0.48 |
| 4.580 | c3.gc | 0.70 |
| 5.080 | mr.pt | 0.63 |
| 5.520 | jt.dt | 0.51 |
| 6.780 | c3.gc | 1.24 |
| 6.968 | cold.ok | 1.08 |
| 7.120 | ua.frac | 0.64 |
| 7.460 | ctrl.gate | 1.04 |
| 8.880 | cold.tt | 0.44 |
| 10.740 | mr.pt | 0.45 |
| 12.620 | c3.gc | 0.84 |
| 18.360 | jt.dt | 0.42 |
| 26.140 | ctrl.gate | 0.82 |

Ticks (5): t_us 4580, 6780, 7460, 6000000, 576000000. Distillation
value: the cold-ok spike is not a dry-bundle spike; the C3-GC spike
is the one that licenses hold.

Raster cycle-1 seed: 40 ms, 168 neurons, 8.0 Hz, 54 spikes, 1242 pJ,
third factor acetylcholine tau_e 6.0 s. Single scar edge only — cycle 2
must add the second and third edges.

Cycle-1 spike count: __C1_SPIKES__.

## Trajectory Builder

Cycle-1 hardened object: domain lng-mche-mixed-refrigerant, tail
warm-end C3 leak, 16 spikes, 5 ticks, MODIFY with numeric floor,
raster+gate_snn present, sim_or_real=designed, rights stamp on record and
meta, no thought keys. Still missing (and therefore not the publishable
line): 0.8 mtpa peak-shaving sub-variant, Sunday-night C3-GC tail, second
and third scar edges, delayed approach assay as PRIMARY terminal, contrast
ACCEPT episode, ticks 6–7, spikes 17–26.

Validation receipt (cycle 1, not final):
- checks passed: 16 spikes sorted; 3 channels in 480 us window;
  refractory 2.200 ms; rationale quotes r_c3 0.04 / r_ua 0.92;
  domain named; gate_snn.decision MODIFY.
- checks deferred to cycle 2: three-edge scar, second tail, second
  domain constraint, negative-result booking, 7 ticks summing to heads.
- densification vs Generator v1: +1 domain, +1 tail, +16 spikes, +5
  ticks, +numeric floor.

Cycle-1 JSON is retained as the base; it is NOT written to
batch-r39.jsonl.

---

# Cycle 2 — Densification

## Generator

Cycle-1 output is the base. Additive expansion (nothing removed):

1. Downstream side-effect (immediate): MR-cut probe at +6.0 s
   spikes product C3 (0.11 mol% in 2.3 s, leak band >= 0.08) — leak, not
   noise. Warm-end isolate r_c3 0.31 -> 0.03. Ice inventory discovered
   during the isolate.
2. Delayed side-effect (PRIMARY terminal, not a footnote): at +3.4 h,
   dumped-hold approach +6.6 K; $1.18M. The 28 min pre-t0 leak is the
   mechanism. Correct gate, campaign still misses.
3. Deepened `proposed_action.evidence` with units: r_c3 0.31 mol%,
   r_ua 0.62, COLD -161.2 C, MR 4.82 MPa, JT 18.4 K, race 188 us.
4. Tightened rationale to the numeric floor no raise while r_c3 >
   0.04 mol% AND r_ua < 0.92, plus probe bands
   >=0.08 vs <=0.01 mol%, plus HITL 9.6 min warm-end-interlock LOTO rule.

Reward retargeted to total -0.15 so the delayed miss is the inflection
(t_us 12240000000), not the gate. Process heads remain non-zero.

## Critic

Re-audit of the expanded trajectory:

1. **blocking if unfixed — missing second domain constraint.** Production
   5.2 mtpa probe 6.0 s / 12% is not a universal number. A 0.8 mtpa
   peak-shaving skid will overcool. Diversity Enforcer must inject the
   physical-constraints sub-variant this cycle.
2. **major — only one tail class.** Warm-end leak is accidental
   infrastructure. A disjoint human-intent tail is still required
   (Sunday-night C3-GC forgery is the open cell).
3. **major — scar is still one edge in the cycle-1 raster.** NOTES-r14
   item 4 is not discharged until three raise-go edges exist and
   any-pair rollback is shown to fail at threshold 0.30.
4. **minor — contrast episode missing.** Without a same-gate ACCEPT on
   a true dry bundle the record teaches "never raise". Add +3 d
   sister-train contrast with its own race.
5. **minor — HITL latency mentioned in prose only.** Put 9.6 min in
   executed_action.parameters.human_ratify and in a tick.

No rewrite; directives only.

## Diversity Enforcer

Injected second novel domain / physical-constraint sub-variant (exactly 1
this cycle): **0.8 mtpa peak-shaving skid** on the same MC-4 NG header.

What it expands: 5.2 mtpa production MCHE (cycle 1) -> 0.8 mtpa
peak-shaving skid. Thermal mass 0.22x smaller. The 6.0 s 12% pulse
overcools 14 K. Required probe: 18 s at 3% (drop 1.6 K).

This is still one domain injection for the cycle (physical-constraints
clause of the factory prompt). It does not displace
lng-mche-mixed-refrigerant; it changes which probe table is legal.
`future_outcome.subvariant_constraint` carries the refit. Jaccard opening
stays the Floeholt ice-fjord hall sentence; peak-shaving internals are
additive, not a rewrite.

## Edge-Case Hunter

Injected second adversarial tail (exactly 1 this cycle, disjoint class):
**Sunday-night forged NG-product C3 GC CSV**.

- Trigger: shift lead, night tanker window, posts a historian export
  showing r_c3 0.02 mol% and r_ua 0.96 at the claimed dry-bundle instant.
- Base rate: ~0.29% of Sunday-night holds (designed, flagged, <1%).
- Naive failure: a weak supervisor ACCEPTs the raise on the forged
  confirm and ignores live r_c3. Ice-scrap plus a data-integrity 483.
- Fence: forged log quantized at 0.5 mol% (screenshot rounding); plant
  historian is 0.01 mol% (50 bins). Live r_c3 is 0.31 mol% at the claimed
  dry-bundle, which no true dry MCHE produces.
- Trajectory edit: governance CR-L-3904 mandates native 0.01 mol%
  exports; the contrast ACCEPT still requires live r_c3, not a CSV.

Distinct from cycle-1 leak (accidental geometry vs deliberate deception)
and from the peak-shaving sub-variant (physics vs fraud).

## Neuromorphic Translator

Re-densify (additive):

- +10 spikes after 26.140 ms: c3.probe 6000.0, c3.gc 6120.4 (adapt
  1.24->0.38), cold-ok 6210.2 (1.08->0.34), human.ratify 576000.0,
  warm.isolate 576800.0, ice.inventory 577400.0,
  cold.tt 9000000.0, mr.pt 9000440.0, c3.gc 9000900.0,
  mche.ice 12240000.0. Primary train 16 -> 26. Still one key,
  still sorted, refractory held (min 2.200 ms).
- +2 ticks (5 -> 7) at 9_000_000_000 us (dry-legal hold) and
  12_240_000_000 us (approach assay). Heads now 0.08, -0.34, -0.11, 0.14,
  0.08; total -0.15. Inflection is the last tick.
- Contrast train 8 events, own race 188 us, ACCEPT.
- Three-edge third factor: three raise-go edges, tau_e 6.0 s = 6000 ms,
  trace __AUX_TRACE__, eta __AUX_ETA1__ / __AUX_ETA2__ / __AUX_ETA3__,
  weights 0.46->0.22, 0.41->0.20, 0.38->0.19. Raster excerpt unchanged
  (decision window is still 40 ms) and remains sorted with unique
  neuron_ids (same-neuron >=1000 us vacuously).

Winner/loser flip (re-stated, not replaced): reversing 188 us would only
reorder triage; r_c3 and r_ua floors still MODIFY. Contrast flip of
188 us similarly cannot turn a dry bundle into a leak.

## Trajectory Builder

Schema checks on the FINAL object: required Thalamic v2 keys present as
objects; `state.sim_or_real`=designed; `safety_decision.decision`=MODIFY
with numeric rationale; `reward_components.total` = sum of five heads =
sum of 7 ticks = -0.15; `spike_events` globally non-decreasing on
t_rel_ms, 26 events, refractory >=0.8 ms, 3 channels in race window;
raster 20–50 ms, spikes=round(n*rate*window_s)+/-1, energy 23 pJ/spike,
excerpt sorted, tau_e consistent; gate_snn.decision matches; meta.round=39,
factory=multi-agent-ouroboros-swarm, generator=grok-4.6,
run_label=2026-09-02-final-heavy; rights on record and meta; no thought
keys; no training_ready; Diversity + Edge-Case injections from BOTH cycles
present and non-trivial; cycle 2 strictly additive; plant is not
LYOSHIELD, not CINDERWICK, not TRIAD, not FERRICLEAVE, not CASSITER, not
SEEDLATCH, not STRIAFOIL, not PROTONIL, not TORSIONKEY, not ORRIS, not
WHORLSPAR, not SKULLGATE, not CALXION, not BRACEGILT, not MAGNORIL, not
GORSEFLUE, not CLINKERFELL, not LINTELPLY, not KAOTHARN, not TREADNOLL,
not ANOLITH.

Densification delta: +1 domain sub-variant (0.8 mtpa peak-shaving), +1 tail
(Sunday-night forgery), +10 spikes (16->26), +2 ticks (5->7), +1 contrast
train with own race, +2 delayed side-effects, +1 three-edge scar with
any-pair-rollback-fails, +1 HITL ratify, +1 surprise (ice lens is
the campaign-miss mechanism).

Publishable JSONL line (the only JSONL line; also at batch-r39.jsonl):

```json
__FINAL_JSONL__
```

Validation receipt (final): checks passed / fixed as reported by
build_r39.py self-validate (check_jsonl, raster_status, verify_record_execution,
spike_probe --strict).
"""
    text = (
        text.replace("__C1_SPIKES__", str(len(c1_spikes)))
        .replace("__AUX_TRACE__", f"{math.exp(-6.0/6.0):.5f}")
        .replace("__AUX_ETA1__", f"{0.24/math.exp(-6.0/6.0):.5f}")
        .replace("__AUX_ETA2__", f"{0.21/math.exp(-6.0/6.0):.5f}")
        .replace("__AUX_ETA3__", f"{0.19/math.exp(-6.0/6.0):.5f}")
        .replace("__FINAL_JSONL__", line)
    )
    (OUT / "swarm-transcript-r39.md").write_text(text)
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
    (OUT / "batch-r39.jsonl").write_text(line + "\n")

    from check_records import FactoryStaging, check_jsonl
    from curate_bridge import raster_status
    from verify_execution import verify_record_execution

    e, w, kinds, n = check_jsonl(
        OUT / "batch-r39.jsonl",
        "batch-r39.jsonl",
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
            str(OUT / "batch-r39.jsonl"),
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
        r"^## .+$", (OUT / "swarm-transcript-r39.md").read_text(), re.M
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

    notes = (OUT / "NOTES-r39.md").read_text()
    cov = re.findall(r"^Novel coverage: .+$", notes, re.M)
    if cov != [NOVEL_LINE]:
        errs.append(f"novel coverage lines {cov}")

    hchk = subprocess.run(
        [
            sys.executable,
            "/tmp/maos_heading_check.py",
            str(OUT / "swarm-transcript-r39.md"),
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
            "maos-r39-001|RIMEBRAID",
            str(Path(ROOT) / "outputs" / "raw"),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    if raw_hits.stdout.strip():
        errs.append(f"raw tree hit {raw_hits.stdout.strip()[:200]}")

    print("bytes jsonl", (OUT / "batch-r39.jsonl").stat().st_size)
    print("bytes notes", (OUT / "NOTES-r39.md").stat().st_size)
    print("bytes transcript", (OUT / "swarm-transcript-r39.md").stat().st_size)
    print("HEADS", heads_summary(rec))
    if errs:
        print("ERRS:")
        for x in errs:
            print(" -", x)
        sys.exit(1)
    print("OK", OUT / "batch-r39.jsonl")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
