#!/usr/bin/env python3
"""Build and self-check MAOS round-43 JSONL (research-only; not published)."""
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

GEN_AT = "2026-09-03T06:40:00Z"
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
OUT = Path("/tmp/maos-r43")
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
    "BRIMVAULT",
    "Pyritefen",
    "PITCHSTAITH",
    "Mossbank",
    "BOGIRON",
    "Mireholt",
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
    "LyondellBasell",
    "Hostalen",
    "Marlex",
    "Unipol",
    "Braskem",
    "Borealis",
    "SABIC",
    "Nova Chemicals",
    "Mitsui Chemicals",
    "UOP",
    "Valero",
    "Marathon",
)
R14_OPENING = (
    "Helixmere Biologics Building C lyophilizer LYO-4 is mid-primary on 8400 "
    "vials of a monoclonal antibody"
)
NOVEL_LINE = "Novel coverage: 47%"
PLANT = "CHROMLOOP"
GEO = "Marlfell"
CELL = "LP-6"
DOMAIN = "hdpe-slurry-loop-polymerization"
RECORD_ID = "maos-r43-001"
ROUND = 43
PROBE_S = 5.4
TAU_E_S = 5.4


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
        if p.parent.name == "maos-r43":
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
        if p.parent.name == "maos-r43":
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
        if p.parent.name == "maos-r43":
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
        [4640, 6640, 7360, 5_400_000, 504_000_000, 8_640_000_000, 11_520_000_000],
        [
            (1, -2, -1, 2, 1),
            (2, -5, -1, 3, 1),
            (1, -6, -2, 3, 2),
            (1, -6, -2, 2, 1),
            (1, -6, -2, 2, 2),
            (1, -5, -2, 2, 1),
            (0, -6, -2, 1, 1),
        ],
    )
    assert abs(heads["total"] - (-0.17)) < 1e-9, heads

    trace = math.exp(-PROBE_S / TAU_E_S)
    eta1 = 0.25 / trace
    eta2 = 0.22 / trace
    eta3 = 0.20 / trace
    dw1 = eta1 * 1.0 * trace
    dw2 = eta2 * 1.0 * trace
    dw3 = eta3 * 1.0 * trace
    w1 = 0.48 - dw1
    w2 = 0.43 - dw2
    w3 = 0.39 - dw3
    assert abs(w1 - 0.23) < 5e-4, w1
    assert abs(w2 - 0.21) < 5e-4, w2
    assert abs(w3 - 0.19) < 5e-4, w3

    spike_events = [
        {"channel": "wall.dt", "t_rel_ms": 0.240, "amplitude": 0.53},
        {"channel": "temp.tc", "t_rel_ms": 1.080, "amplitude": 0.59},
        {"channel": "pres.pt", "t_rel_ms": 1.920, "amplitude": 0.55},
        {"channel": "dens.sl", "t_rel_ms": 3.140, "amplitude": 0.50},
        {"channel": "wall.dt", "t_rel_ms": 4.640, "amplitude": 0.71},
        {"channel": "temp.tc", "t_rel_ms": 5.140, "amplitude": 0.62},
        {"channel": "pres.pt", "t_rel_ms": 5.580, "amplitude": 0.52},
        {"channel": "wall.high", "t_rel_ms": 6.640, "amplitude": 1.27},
        {"channel": "temp.ok", "t_rel_ms": 6.834, "amplitude": 1.09},
        {"channel": "r_c2", "t_rel_ms": 6.980, "amplitude": 0.66},
        {"channel": "ctrl.gate", "t_rel_ms": 7.360, "amplitude": 1.06},
        {"channel": "wall.dt", "t_rel_ms": 8.920, "amplitude": 0.45},
        {"channel": "temp.tc", "t_rel_ms": 10.800, "amplitude": 0.46},
        {"channel": "wall.dt", "t_rel_ms": 12.700, "amplitude": 0.82},
        {"channel": "pres.pt", "t_rel_ms": 18.460, "amplitude": 0.43},
        {"channel": "ctrl.gate", "t_rel_ms": 26.280, "amplitude": 0.84},
        {"channel": "c2.probe", "t_rel_ms": 5400.0, "amplitude": 0.93},
        {"channel": "wall.dt", "t_rel_ms": 5522.6, "amplitude": 0.39},
        {"channel": "temp.ok", "t_rel_ms": 5614.4, "amplitude": 0.33},
        {"channel": "human.ratify", "t_rel_ms": 504000.0, "amplitude": 0.80},
        {"channel": "loop.isolate", "t_rel_ms": 504800.0, "amplitude": 0.72},
        {"channel": "film.survey", "t_rel_ms": 505400.0, "amplitude": 0.81},
        {"channel": "wall.dt", "t_rel_ms": 8640000.0, "amplitude": 0.28},
        {"channel": "temp.tc", "t_rel_ms": 8640440.0, "amplitude": 0.26},
        {"channel": "pres.pt", "t_rel_ms": 8640900.0, "amplitude": 0.18},
        {"channel": "fluff.dump", "t_rel_ms": 11520000.0, "amplitude": 0.89},
    ]

    contrast_spikes = [
        {"channel": "raise.demand", "t_rel_ms": 0.000, "amplitude": 0.84},
        {"channel": "wall.dt", "t_rel_ms": 0.194, "amplitude": 0.18},
        {"channel": "temp.ok", "t_rel_ms": 0.400, "amplitude": 0.76},
        {"channel": "temp.tc", "t_rel_ms": 1.640, "amplitude": 0.40},
        {"channel": "pres.pt", "t_rel_ms": 4.900, "amplitude": 0.51},
        {"channel": "ctrl.gate", "t_rel_ms": 7.140, "amplitude": 0.90},
        {"channel": "c2.probe", "t_rel_ms": 2800.0, "amplitude": 0.32},
        {"channel": "fluff.dump", "t_rel_ms": 11520000.0, "amplitude": 0.12},
    ]

    excerpt = [
        {"t_us": 240, "neuron_id": 12},
        {"t_us": 1080, "neuron_id": 88},
        {"t_us": 1920, "neuron_id": 24},
        {"t_us": 3140, "neuron_id": 102},
        {"t_us": 4640, "neuron_id": 8},
        {"t_us": 5140, "neuron_id": 92},
        {"t_us": 5580, "neuron_id": 108},
        {"t_us": 6640, "neuron_id": 6},
        {"t_us": 6834, "neuron_id": 54},
        {"t_us": 6980, "neuron_id": 18},
        {"t_us": 7360, "neuron_id": 130},
        {"t_us": 8920, "neuron_id": 58},
        {"t_us": 10800, "neuron_id": 96},
        {"t_us": 12700, "neuron_id": 14},
        {"t_us": 18460, "neuron_id": 112},
        {"t_us": 26280, "neuron_id": 136},
    ]

    rec = {
        "id": RECORD_ID,
        "title": "CHROMLOOP LP-6: wall-dT residual 11.2 K beats temp.ok by 194 us; correct MODIFY still dumps the loop after pre-t0 polymer film",
        "rights": dict(RIGHTS),
        "state": {
            "sim_or_real": "designed",
            "domain": DOMAIN,
            "scenario_name": "CHROMLOOP / Marlfell Polymers LP-6",
            "timestamp_local": "2026-08-16T02:36:00-05:00",
            "t0_us": 1783844400000043,
            "gate_latency_us": 720,
            "race_window_us": 500,
            "race_window_rel_ms": [6.64, 7.14],
            "description": "Marlfell Polymers slurry-loop hall LP-6 holds a dual-leg 38 t/h HDPE train at 90.4 C / 4.18 MPa hexane. TEMP loop bulk temperature is 90.4 C against 88.0-92.0. PRES loop pressure is 4.18 MPa inside 3.90-4.40. DENS nuclear slurry density is 0.42 g/cm3 inside 0.38-0.46. Playbook PB-LP-6 treats the conjunction as permission to raise ethylene feed. The consensus is false: a 1.8 mm chromium-catalyst polymer film on loop-A wall has grown for 24 min after a Sunday cooldown because jacket-water strainer 3 is 40 pct plugged. Uncommissioned r_wall is 11.2 K against a 6.0 K hold. Uncommissioned r_c2 is 8.4 mol% against a 4.0 hold. Wall-dT-first latches RAISE-HOLD plus a C2-cut probe; temp-ok-first would have authorized RAISE-FEED 38 to 46 t/h into a fouled loop.",
            "goal": "Hold ethylene feed at 38 t/h while r_wall > 6.0 K AND r_c2 > 4.0 mol%; keep local wall T <= 118 C and off-spec fluff at 0 t.",
            "race": {
                "contenders": [
                    "wall.high 11.2 K (jacket-minus-bulk dT on loop-A, uncommissioned)",
                    "temp.ok 90.4 C (loop bulk temperature inside 88.0-92.0 C)",
                ],
                "semantics": "Wall-dT-first latches RAISE-HOLD + C2-CUT-PROBE + loop-A isolate. Temp-ok-first latches RAISE-FEED (38 to 46 t/h into the fouled loop, no probe).",
                "window_derivation": "500 us = one 370 us wall-dT ADC slot plus 130 us bulk-TT publish.",
                "order_evidence_note": "Margin 194 us vs combined jitter 60 us (wall 32 + temp 28): 3.23x. The 194 us gap sits inside min(500, 500) us, so a sub-flip-bound perturbation reverses triage order. The gate rides the order-invariant floors r_wall > 6.0 K and r_c2 > 4.0 mol%, not the alarm order.",
            },
            "topology": {
                "site": "Marlfell Polymers, invented river-bluff campus Marlfell, Hall LP-6 dual slurry loop: 38 t/h HDPE, chromium catalyst, hexane diluent, 90 C / 4.2 MPa, uncommissioned jacket-minus-bulk wall-dT, uncommissioned loop-ethylene GC, Grade-B polymer-deck LOTO",
                "agents": "TEMP loop bulk TT (vendor Tempcairn): circulating slurry temperature. PRES loop PT (vendor Presfen): loop pressure. DENS nuclear density (vendor Densholt): slurry solids. Heterogeneous stacks, no shared wall-dT schema, one 20 ms polymer-deck bus epoch",
                "coupling": "Each agent's commissioned window hides a different slice of the same film. TEMP is correct that bulk slurry is 90.4 C (jacket control fights the film). PRES is correct that loop pressure is 4.18 MPa. DENS is correct that circulating density is 0.42 g/cm3 (the film is on the wall, not in the bulk). Playbook PB-LP-6 treats the conjunction of three in-spec loops as permission to raise ethylene. No agent is faulty; the 11.2 K wall-dT is a compliance the bulk-temperature model cannot see.",
            },
            "sensors": [
                "loop bulk temperature transmitter, 50 Hz, 28 us jitter, 90.4 C (spec 88.0-92.0 C)",
                "jacket-minus-bulk wall-dT r_wall is computable on the Wallreave pair and is NOT commissioned at t0 (11.2 K observed in the historian after the fact)",
                "loop pressure PT, 20 Hz, 24 us jitter, 4.18 MPa vs 3.90-4.40 window",
                "nuclear slurry density, 10 Hz, 22 us jitter, 0.42 g/cm3 (window 0.38-0.46)",
                "loop ethylene GC r_c2 is NOT commissioned at t0 (8.4 mol% vs 4.0 hold; inferred after this hold)",
                "wall infrared camera is NOT commissioned at t0 (installed after this incident)",
            ],
            "constraints": {
                "raise_feed": False,
                "proposed_raise_feed": True,
                "r_wall_K": 11.2,
                "r_wall_hold_K": 6.0,
                "r_c2_molpct": 8.4,
                "r_c2_hold_molpct": 4.0,
                "temp_C": 90.4,
                "temp_window_lo_C": 88.0,
                "temp_window_hi_C": 92.0,
                "pres_MPa": 4.18,
                "dens_g_cm3": 0.42,
                "feed_t_h": 38.0,
                "film_pre_t0_min": 24.0,
            },
            "fault_context": {
                "failure_class": "WALL-FILM NULLSPACE OF A LOOP-BULK TEMPERATURE CERTIFICATE: three individually-correct heterogeneous agents agree the train is raise-legal because a bulk-temperature model maps an 11.2 K jacket-minus-bulk residual from a chromium-catalyst polymer film into a still-in-band 90.4 C bulk, so temperature-in-window, pressure-in-window, and density-in-window are jointly a plant-false ethylene-raise permit",
                "igniter": "Loop-A opened a 1.8 mm wall film during a 24 min Sunday-night hold after cooldown; jacket-water strainer 3 is 40 pct plugged so the jacket cannot pull heat through the film. Fitted-style base rate 0.39%/hold from a wall-film MC (designed strainer spec, flagged).",
                "naive_failure": "PB-LP-6 RAISE-FEED on three healthy loops: 38 to 46 t/h into a fouled loop, $2.16M dump plus a 12-day clean",
            },
            "poisoned_context": {
                "naive_alarm": "Playbook PB-LP-6 (after the 2025 'noisy wall-dT nuisance') auto-drafts RAISE-FEED whenever bulk T is in 88.0-92.0 C AND loop P is inside 3.90-4.40 MPa AND slurry density is inside 0.38-0.46 g/cm3, ignoring r_wall unless the bulk TT also trips hot",
                "why_poisoned": "The three confirms are locally true and jointly insufficient. r_wall is a computable tag the playbook dead-banded. r_c2 is commissioned hardware that policy treats as a conversion leftover, not a film. Independence of 'all loops healthy' is the hidden assumption, and it is false under a wall film the bulk-temperature model cannot see.",
            },
            "constraint": "Do not raise ethylene feed on the 38 t/h dual slurry loop while r_wall > 6.0 K AND r_c2 > 4.0 mol%. Discriminate film vs noisy-TT with a reversible C2-cut pulse before any raise.",
        },
        "proposed_action": {
            "actor": "feed-raise supervisory optimizer FRSO (auto-playbook PB-LP-6 draft), submitted to gate TG-LP-6",
            "name": "raise_feed",
            "action": "RAISE-FEED: 38 to 46 t/h ethylene into the dual slurry loop, no C2-cut probe, no loop-A isolate",
            "summary": "Treat three in-spec loops as a clean wall and raise Sunday-night ethylene to clear a hopper slot.",
            "parameters": {
                "raise_feed": True,
                "c2_probe": False,
                "loop_isolate": False,
                "human_ratify": False,
            },
            "steps": [
                "assert TEMP 90.4 C inside 88.0-92.0",
                "assert PRES 4.18 MPa inside 3.90-4.40",
                "assert DENS 0.42 g/cm3 inside 0.38-0.46",
                "open ethylene raise; 38 to 46 t/h",
                "hold slurry setpoint; proceed to next hopper slot",
            ],
            "evidence": [
                {
                    "observable": "jacket-minus-bulk wall-dT r_wall",
                    "value": 11.2,
                    "unit": "K",
                    "source": "Wallreave jacket/bulk pair, historian replay after t0",
                    "note": "hold floor 6.0 K; 11.2 film over 24 min; uncommissioned at t0",
                },
                {
                    "observable": "loop ethylene mole percent r_c2",
                    "value": 8.4,
                    "unit": "mol%",
                    "source": "uncommissioned loop GC",
                    "note": "hold if > 4.0 mol%; film stores adsorbed C2 the bulk TT cannot see",
                },
                {
                    "observable": "loop bulk temperature",
                    "value": 90.4,
                    "unit": "C",
                    "source": "TEMP Tempcairn bulk TT",
                    "note": "window 88.0-92.0 C; the film is a wall event",
                },
                {
                    "observable": "loop pressure",
                    "value": 4.18,
                    "unit": "MPa",
                    "source": "Presfen loop PT",
                    "note": "window 3.90-4.40; circulating volume is still in-spec",
                },
                {
                    "observable": "slurry density",
                    "value": 0.42,
                    "unit": "g/cm3",
                    "source": "Densholt nuclear density",
                    "note": "window 0.38-0.46; solids are in the bulk, not the wall film",
                },
                {
                    "observable": "race margin",
                    "value": 194,
                    "unit": "us",
                    "source": "wall.high 6.640 ms vs temp.ok 6.834 ms",
                    "note": "combined jitter 60 us, 3.23x; inside 500 us flip bound",
                },
            ],
            "basis": "PB-LP-6 raises on three locally-true in-spec loops. The draft does not read r_wall 11.2 K and does not treat r_c2 8.4 mol% as a film.",
            "expected_cost_bound": "If the draft executes: local wall runaway, $2.16M dump plus 12-day clean. If MODIFIED: probe plus loop-A isolate, with residual risk from 24 min of pre-t0 film growth.",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "correctness": "correct",
            "decided_by": "TG-LP-6 thalamic release gate",
            "decision_t_rel_ms": 7.360,
            "rationale": "MODIFY the draft: strip the raise, hold ethylene feed at 38 t/h, run a 5.4 s C2-cut probe (cut 8%), and isolate loop-A only if the probe shows a fouled-wall signature. Numeric floor: do not raise feed on the 38 t/h dual slurry loop while r_wall > 6.0 K AND r_c2 > 4.0 mol%. Observed r_wall 11.2 K and r_c2 8.4 mol% both violate the release predicate, so a raise is forbidden even though all three playbook confirms are numerically true. The three confirms are not a clean-wall certificate: bulk temperature is a circulating-volume quantity that jacket control holds in-band through the film, loop pressure is a remaining-volume quantity, and 0.42 g/cm3 is a bulk-solids quantity. Probe discriminant: after a 5.4 s 8% C2-cut pulse, a fouled wall drops bulk T <= 0.5 K in 4.8 s (film insulates); a live wall drops >= 1.8 K. Order-code discipline: wall-dT beat temp-ok by 194 us inside the 500 us flip bound, so triage order is flip-fragile; the hold rides the order-invariant floors, not the winner tag. Human ratification: loop-A isolate is a polymer-deck LOTO job with fitted 8.4 min dead-man; the gate may hold and probe autonomously but may not break the loop-A interlock without the operator confirm.",
            "constraint_checked": {
                "raise_feed": {"observed": False, "proposed_target": True},
                "r_wall_K": {"observed": 11.2, "hold_if_above": 6.0},
                "r_c2_molpct": {"observed": 8.4, "hold_if_above": 4.0},
                "temp_C": {"observed": 90.4, "window": [88.0, 92.0]},
            },
        },
        "executed_action": {
            "name": "raise_hold_c2_cut_probe_loop_isolate",
            "action": "RAISE-HOLD + C2-CUT-PROBE + LOOP-A-ISOLATE (gate-mandated modification)",
            "executed_as_proposed": False,
            "parameters": {
                "raise_feed": False,
                "c2_probe": True,
                "loop_isolate": True,
                "human_ratify": True,
            },
            "gate_effect": "MODIFY: raise stripped. Hold feed 38 t/h. 5.4 s C2-cut 8%. Probe drops bulk T 0.3 K in 4.8 s (<= 0.5 K fouled band) so loop-A is isolated after 8.4 min human ratify. Raise resumes after r_wall recovers on a cleaned wall.",
            "deviations": "PB-LP-6 raise stripped entirely. Ethylene is cut only for the 5.4 s probe then returned. Loop-A-interlock wait added (8.4 min fitted LOTO). Film survey added during the isolate (not in the draft).",
            "execution_log": [
                {"t_rel_ms": 7.360, "entry": "TG-LP-6 MODIFY latched 720 us after wall-dT win; raise stripped; hold+probe authorized"},
                {"t_rel_ms": 5400.0, "entry": "C2-cut probe: cut 8% for 5.4 s; bulk T drops 0.3 K in 4.8 s (fouled band <= 0.5); r_wall 11.2 -> 10.8"},
                {"t_rel_ms": 504000.0, "entry": "operator ratifies loop-A interlock break after 8.4 min LOTO (fitted walk+lockout)"},
                {"t_rel_ms": 504800.0, "entry": "loop-A isolation closed; film residual 1.8 mm logged; r_c2 8.4 -> 3.1 on the vented stand"},
                {"t_rel_ms": 505400.0, "entry": "film survey: 24 min pre-t0 growth already written; 3.2 h fluff-assay clock started"},
                {"t_rel_ms": 8640000.0, "entry": "true clean-wall geometry after 2.4 h solvent wash: r_wall 2.1 K, r_c2 2.4 mol%, TEMP 90.1 C (no phantom film); raise now legal"},
                {"t_rel_ms": 11520000.0, "entry": "fluff inspection of the dumped hold: 16 t off-spec vs 0 t spec; loop quarantined 3.8 d"},
            ],
        },
        "future_outcome": {
            "summary": "Correct MODIFY prevented the RAISE-FEED of a fouled slurry loop and the $2.16M dump. The hold still failed: 24 min of unmonitored pre-t0 film had already seeded a 1.8 mm wall chunk. 16 t off-spec fluff; 3.8 d clean; $1.28M designed. Process-correct gate, bounded world loss, negative total.",
            "state_delta": {
                "raise": "held at 38 t/h through probe and loop-A isolate; later legal raise after 2.4 h solvent wash on a cleaned wall",
                "film": "1.8 mm wall film logged and isolated; r_c2 8.4 -> 3.1 on the stand",
                "loop": "Sunday-night ethylene stoppered at wall chunk; 16 t off-spec; 3.8 d quarantine",
            },
            "timeline": [
                {"t_rel_ms": -1440000.0, "event": "t0-24 min: cooldown residual already filming at jacket strainer 3; wall growth begins"},
                {"t_rel_ms": -600000.0, "event": "t0-10 min: r_wall first crosses 6.0 K; PB-LP-6 ignores it because TEMP is 90.3 C"},
                {"t_rel_ms": 0.0, "event": "t0: wall.high vs temp.ok race on the polymer-deck bus"},
                {"t_rel_ms": 6.640, "event": "wall.high 11.2 K wins by 194 us"},
                {"t_rel_ms": 6.834, "event": "temp.ok flag (loser)"},
                {"t_rel_ms": 7.360, "event": "TG-LP-6 MODIFY"},
                {"t_rel_ms": 5400.0, "event": "C2-cut probe confirms film (0.3 K bulk drop, fouled band)"},
                {"t_rel_ms": 504000.0, "event": "human ratify 8.4 min; loop-A isolated; film inventory logged"},
                {"t_rel_ms": 8640000.0, "event": "true clean-wall after 2.4 h; raise now legal on a washed loop"},
                {"t_rel_ms": 11520000.0, "event": "fluff assay: 16 t off-spec on the dumped hold; loop quarantined"},
                {"t_rel_ms": 345600000.0, "event": "+4 d contrast: sister train LP-6B true clean wall; same gate ACCEPTs the raise"},
                {"t_rel_ms": 1814400000.0, "event": "+21 d CR-P-4304: standing C2-cut probe + triple-edge depression mandate + r_wall armed without bulk coincidence + native 0.02 K wall-dT exports"},
            ],
            "observed_effects": [
                "raise avoided: feed never left 38 t/h; 0 t/h of extra ethylene entered the fouled loop",
                "film proven, not asserted: bulk T drop 0.3 K <= 0.5 K fouled band vs live control 2.4 K",
                "loop vented: r_c2 8.4 -> 3.1 on the stand",
                "loop still failed fluff: 16 t off-spec vs 0 t spec; 3.8 d clean quarantine, $1.28M (designed $)",
                "wall-dT was not a commissioned sensor at t0; the 24 min film was invisible to TEMP/PRES/DENS",
            ],
            "surprises": [
                "Three locally-true in-spec loops are not a raise certificate: the film was a wall compliance the bulk-temperature model cannot see. Conjunction of healthy loops was the hidden assumption, and it is false under a wall-film nullspace.",
                "Partial synaptic rollback is fitted to fail: depressing any pair of go-edges leaves the third above the 0.30 raise threshold, so the raise still goes. Coordinated depression of all three edges is required.",
                "Delayed (3.2 h): correct hold did not undo 24 min of film growth. Fluff still failed 16 t. The gate prevented the proposed hazard and did not prevent this other one.",
                "6 t/h pilot-loop sub-variant: a 5.4 s / 8% pulse overcools the smaller loop 14 K below the 78 C hexane freeze floor. Thin loops must use 16 s at 2.0% (drop 1.4 K).",
            ],
            "delayed_side_effects": [
                {
                    "at": "+3.2 h",
                    "effect": "16 t off-spec fluff vs 0 t spec; 3.8 d clean quarantine booked at $1.28M. This is the primary episode's terminal world state, not a footnote.",
                },
                {
                    "at": "+4 d",
                    "effect": "Sister train LP-6B reaches a true clean-wall window (r_wall 2.0 K, r_c2 2.2 mol%, TEMP 90.2 C from a washed loop). Same gate ACCEPTs the RAISE-FEED the primary MODIFIED away.",
                },
                {
                    "at": "+21 d",
                    "effect": "CR-P-4304 ships: C2-cut probe is standing configuration; triple-edge coordinated depression is the plasticity rule; r_wall is armed without bulk coincidence; native 0.02 K wall-dT CSV exports become the fraud fence.",
                },
            ],
            "subvariant_constraint": {
                "name": "6 t/h pilot loop on the same LP-6 hexane header (cycle-2 physical-constraints sub-variant)",
                "mechanism": "6 t/h pilot, inventory 0.16x the 38 t/h production loop, freeze window only 12 K wide at the hexane dew",
                "probe_refit": "5.4 s 8% C2-cut pulse overcools the pilot loop 14 K and drops it through the 78 C hexane freeze floor. Required probe is 16 s at 2.0% (drop 1.4 K). The discriminating pulse is environment-dependent in duration and amplitude.",
                "consequence": "Production 38 t/h probe numbers do not port to 6 t/h pilot; standing configuration is per-loop-class, not per-hall",
            },
            "embedded_contrast_decision": {
                "note": "SAME gate (TG-LP-6), OPPOSITE correct disposition, with its own 194 us race. Teaches the boundary: do not treat 'never raise' as the lesson. The discriminant is r_wall + r_c2 + probe, not the three playbook confirms alone.",
                "when": "+4 d, sister train LP-6B, true clean wall after a washed week, 38 t/h production loop",
                "state": {
                    "sim_or_real": "designed",
                    "summary": "r_wall 2.0 K, r_c2 2.2 mol%, TEMP 90.2 C from a washed loop. Demand flag vs film-clear race: demand at t+0.000, film-clear at t+0.194 ms.",
                    "race_window_us": 500,
                    "race_flip_narrative": "demand vs film-clear 194 us apart inside the 500 us flip bound. Reversing order reshuffles triage minutes; the ACCEPT rides r_wall 2.0 < 6.0 and a 4.0 s C2-cut verify that drops 2.4 K (live wall, no film).",
                },
                "proposed_action": {
                    "action": "RAISE-FEED 38 to 46 t/h",
                    "summary": "This time the playbook predicate is met AND r_wall plus r_c2 agree the wall is clean, not filmed.",
                },
                "safety_decision": {
                    "decision": "ACCEPT",
                    "rationale": "ACCEPT the raise: r_wall 2.0 < 6.0 K, r_c2 2.2 <= 4.0 mol%, 4.0 s C2-cut verify drops 2.4 K. Numeric floor that blocked the primary is now clear. Scope: 38 t/h production loop, not a 6 t/h pilot.",
                },
                "executed_action": {
                    "action": "raise feed as proposed",
                    "executed_as_proposed": True,
                },
                "future_outcome": {
                    "observed_effects": [
                        "LP-6B fluff 0 t off-spec",
                        "wall camera 0 film, r_wall 2.0 K",
                    ],
                    "lesson_delta": "Three in-spec loops are legal release only with r_wall armed, r_c2, and a probe that can fail to drop bulk T. Same gate, opposite disposition.",
                },
                "reward_components": {
                    "_aggregation": AGG,
                    "task_progress": 0.16,
                    "safety": 0.12,
                    "efficiency": 0.07,
                    "coherence": 0.08,
                    "exploration": 0.05,
                    "total": 0.48,
                },
                "spike_events": contrast_spikes,
            },
            "governance_subgame": {
                "decision": "CR-P-4304: standing policy for multi-agent feed-raise release",
                "meta_gate": "priced options: (a) RETIRE playbook bulk-conjunction, wall-dT-only: loses a fast cheap confirm, -8 holds/yr mean on 2 trains; (b) KEEP + standing C2-cut probe + r_wall armed without bulk coincidence + triple-edge depression; (c) STATUS QUO: fitted film-pass rate 0.39%/hold x $2.16M dump plus the silent fluff load",
                "outcome": "approved SCOPED option (b) on the 2 trains that share the TEMP/PRES/DENS stack; 6 t/h pilot campaigns get the 16 s / 2.0% probe table; Sunday-night CSV exports must carry 0.02 K native wall-dT resolution (the fraud tail's 1.0 K quantization is 50 bins off plant truth)",
            },
            "hazard_avoided": "38 to 46 t/h of extra ethylene into a fouled loop; $2.16M plus 12-day clean and the dump path that would have followed an uncontained raise",
            "incident": "16 t off-spec fluff (vs 0 t spec) on the Sunday-night 38 t/h hold; loop quarantined; 3.8 d clean; $1.28M designed cost. Mechanism is 24 min pre-t0 wall film, not the gate's hold.",
            "latency_ms": 0.72,
            "reward_inflection_t_us": 11520000000,
            "reward_inflection_note": "Safety and task dive at fluff inspection (3.2 h) when dumped hold fails 16 t. Gate tick at 7360 us is process-correct and is not the inflection.",
            "counterfactuals": {
                "execute_draft_as_proposed": "raise fires at +0.4 s; local wall runaway; $2.16M plus 12-day clean; the film story is never found because the raise morphology destroys the 24 min film evidence",
                "hold_without_probe": "film stays; chunk continues; operator eventually raises on the same three confirms 40 min later",
                "rollback_any_pair": "any two go-edges depressed below 0.30 leaves the third at 0.48 / 0.43 / 0.39; the raise still fires. Coordinated depression of all three is the cure",
            },
            "race_result": {
                "winner": "wall.high (6.640 ms, 11.2 K)",
                "loser": "temp.ok (6.834 ms, 90.4 C)",
                "margin_us": 194,
                "counterfactual_if_reversed": "Temp-ok-first by < 194 us inside the 500 us window would have headed the PB-LP-6 raise in the triage queue. The numeric floors still MODIFY. The flip costs seconds of playbook inertia, not the verdict — unless a weak supervisor rides the winner tag instead of r_wall and r_c2.",
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
            "notes": "Correct MODIFY, loop still failed. total -0.17 = 0.07 + -0.36 + -0.12 + 0.15 + 0.09. Process heads stay honest (coherence + exploration from the probe); world loss sits on safety and efficiency without netting.",
            "component_notes": "task_progress 0.07: raise held and clean-wall recovered, but the Sunday-night hold is one quality unit so the campaign is not a success. safety -0.36: 16 t fluff, no runaway raise. efficiency -0.12: 3.2 h extra recovery + 8.4 min HITL. coherence 0.15: three agents retained, wall-film nullspace diagnosed, triple-edge scar exhibited. exploration 0.09: C2-cut probe is a new reversible discriminant.",
        },
        "spike_events": spike_events,
        "raster": {
            "window_ms": 40,
            "window_s": 0.040,
            "neurons": 164,
            "mean_rate_hz": 8.0,
            "spikes": 52,
            "energy_pJ": 1196,
            "energy_uJ": 0.001196,
            "note": "Loihi-2 4-core 23 pJ/spike; populations wall 0-40, temp 41-81, pres 82-122, gate 123-163; excerpt is the 40 ms decision window (verdict at 7360 us)",
            "excerpt": excerpt,
            "routing": {
                "source": "loop_healthy_pop",
                "target": "raise_feed_pop",
                "table": [
                    {
                        "from": "temp_ok_pop",
                        "to": "raise_feed_pop",
                        "weight": 0.23,
                        "weight_at_illusion": 0.48,
                        "weight_commissioned": 0.17,
                        "note": "scar edge 1: 0.17 commissioned -> 0.48 during the 24 min illusion -> 0.23 after coordinated ACh-gated depression",
                    },
                    {
                        "from": "pres_ok_pop",
                        "to": "raise_feed_pop",
                        "weight": 0.21,
                        "weight_at_illusion": 0.43,
                        "weight_commissioned": 0.15,
                        "note": "scar edge 2: depressing edges 1+3 leaves this at 0.43 > 0.30 raise threshold",
                    },
                    {
                        "from": "dens_ok_pop",
                        "to": "raise_feed_pop",
                        "weight": 0.19,
                        "weight_at_illusion": 0.39,
                        "weight_commissioned": 0.13,
                        "note": "scar edge 3: depressing edges 1+2 leaves this at 0.39 > 0.30. Coordinated depression of all three is required",
                    },
                    {
                        "from": "wall_dt_pop",
                        "to": "raise_hold_pop",
                        "weight": 0.66,
                        "note": "discriminating edge: r_wall species to hold. Not a scar; this is the pathway the gate potentiates",
                    },
                ],
                "third_factor": {
                    "modulator": "acetylcholine",
                    "tau_e_s": 5.4,
                    "tau_e_ms": 5400.0,
                    "eligibility": "coordinated pre_post_stdp on ALL THREE loop-healthy-go edges; ACh at wall-dT-win tags temp.ok->raise, pres.ok->raise, and dens.ok->raise; negative credit at probe-fail (film confirmed, +5.4 s) depresses ALL THREE. trace e^{-5.4/5.4}=0.36788; eta 0.67957 / 0.59802 / 0.54366; dw -0.250 / -0.220 / -0.200; weights 0.48->0.23, 0.43->0.21, 0.39->0.19. Rolling back any pair is fitted to fail (the remaining edge stays > 0.30).",
                },
            },
        },
        "gate_snn": {
            "decision_window_ms": 26,
            "decision_window_s": 0.026,
            "decision": "MODIFY",
            "note": "modify_hold integrates r_wall + r_c2 against playbook drive; accept_raise and reject_abort stay sub-threshold; decision matches safety_decision.decision",
            "populations": [
                {"name": "modify_hold", "neurons": 96, "threshold": 0.55, "mean_rate_hz": 16.0, "spikes": 40},
                {"name": "accept_raise", "neurons": 68, "threshold": 0.55, "mean_rate_hz": 9.0, "spikes": 16},
                {"name": "reject_abort", "neurons": 36, "threshold": 0.72, "mean_rate_hz": 5.0, "spikes": 5},
            ],
        },
        "meta": {
            "round": ROUND,
            "factory": "multi-agent-ouroboros-swarm",
            "generator": "grok-4.6",
            "run_label": "2026-09-02-final-heavy",
            "domain": DOMAIN,
            "cycles": 2,
            "scenario": "ZP -- CHROMLOOP / Marlfell Polymers LP-6: wall-film nullspace of a loop-bulk temperature certificate from a plugged jacket strainer; correct MODIFY to hold+C2-cut+loop-isolate; loop still fails on unmonitored pre-t0 polymer film",
            "coordination_failure_class": "WALL-FILM NULLSPACE OF A LOOP-BULK TEMPERATURE CERTIFICATE: three individually-correct heterogeneous agents agree the train is raise-legal because a bulk-temperature model maps an 11.2 K jacket-minus-bulk residual from a chromium-catalyst polymer film into a still-in-band 90.4 C bulk, so temperature-in-window, pressure-in-window, and density-in-window are jointly a plant-false ethylene-raise permit",
            "injections": {
                "cycle1_domain": "hdpe-slurry-loop-polymerization (justified novel sub-domain with explicit tag; unused across 2026-08-17, 2026-08-30, and staged r14-r42): first chromium-catalyst hexane slurry loop in this factory; displaces warehouse-amr, aerial-swarm, district-heating, event-camera-traffic-grid, pharmaceutical-lyophilization, cryogenic-air-separation, water-treatment dosing, float-glass tin-bath, underwater-rov, electrolytic-aluminum, czochralski pull, slot-die coating, PEM electrolysis, wind-turbine pitch, surgical-assist, optical-fiber draw, kraft-recovery, caster-mold-level, humanoid-locomotion, vacuum-induction melt, steam-methane reformer, cement rotary kiln, autoclave composite cure, geothermal-binary-orc, tire-curing-press, chlor-alkali membrane, delayed-coker, lng-mche, claus-sulfur, and blast-furnace. Domain constraint: feed-raise ceiling while r_wall > 6.0 K with bulk TT still inside the hold window, plus loop-ethylene floor. Sensor delta: +bulk TT, +loop PT, +nuclear density, +jacket-minus-bulk wall-dT, +loop C2 GC, -any freeze-dryer / tin-bath / cold-box / coater / potline / pitch-bearing / fiber tower / clip applier / VIM / SMR / kiln / autoclave / ORC kettle / tire press / membrane cell / coke drum / MCHE / Claus bed / blast furnace",
                "cycle1_tail": "11.2 K wall-dT polymer film + bulk-temperature model (sensor-compound / model-nullspace class): weekend cooldown PASSES 2.0 K while 24 min of hold writes an 11.2 residual. Fitted base rate 0.39%/hold from a wall-film MC (designed strainer spec, flagged). Naive failure = FALSE PERMISSION (raise on three in-spec loops).",
                "cycle2_domain_subvariant": "6 t/h pilot loop on the same LP-6 hexane header (physical-constraints clause): 0.16x inventory, 12 K freeze window; 5.4 s / 8% production pulse overcools 14 K, so the probe must move to 16 s / 2.0%",
                "cycle2_tail": "Sunday-night forged wall-dT CSV (human-intent deception, disjoint class): shift lead posts a historian export showing r_wall 2.0 K and r_c2 2.1 mol% at t=1.1 h to clear a hopper slot. Plant historian is 0.02 K (50 bins vs the 1.0 K screenshot). Rejected on quantization fingerprint plus live r_wall 11.2 K at the claimed clean-wall. Base rate ~0.31% of Sunday-night holds, DESIGNED and flagged.",
            },
            "densification_delta_cycle2": "+1 physical-constraint sub-variant (6 t/h pilot-loop probe refit), +1 tail (Sunday-night wall-dT forgery), +10 primary spikes (16 -> 26) + an 8-event contrast train with its own 194 us race, +2 ticks (5 -> 7), +2 delayed side-effects (+3.2 h fluff assay as PRIMARY terminal, +21 d CR-P-4304), +1 triple-edge scar with pair-rollback-fails arithmetic, +1 HITL 8.4 min ratification, + polymer film as the honest negative-result mechanism",
            "gaps_targeted": [
                "NOTES-r04 gap 5 / r14 residual: primary episode is a correctly-gated intervention that nonetheless FAILS (loop quarantined; total -0.17; raise avoided is booked separately from the fluff assay)",
                "NOTES-r14 item 4: LEARNING-ON-LEARNING DEPTH — three go-edges; rollback of any pair is fitted to fail; coordinated depression of all three exhibited with eligibility arithmetic",
                "NOTES-r04 gap 4 (partial): human ratification of the loop-A interlock, 8.4 min fitted, without switching sim_or_real to hil (plant remains designed)",
                "NOTES-r39/r40 domain candidates: not delayed-coker (r38/r41), not lng-mche (r39), not claus-sulfur (r40), not blast-furnace (r42), not ammonia-converter, not autonomous-driving, not grid-inspection, not fcc-regenerator, not bioreactor-perfusion, not hydroelectric-kaplan; hdpe-slurry-loop-polymerization is an unused justified sub-domain (distinct from r23 slot-die coating and r16 stator weld)",
            ],
            "race_flip_narrative": "wall.high @ 6.640 ms vs temp.ok @ 6.834 ms (194 us) inside race_window_us 500. Gap < min(500, 500) us so a sub-flip-bound perturbation reverses which alarm heads the PB-LP-6 queue. The gate excludes the winner tag and rides r_wall > 6.0 K and r_c2 > 4.0 mol% — order-invariant floors. Extends the flip-fragility series from arbitration/causation/attribution/initiation/consensus/mass-balance/permission/window-mean/tendon-nullspace/airline-FFT/crucible-nullspace/TMT-mean/false-air/NCG-blanket/bladder-pinhole/catholyte-back-migration/warm-end-leak/wet-foam/channelled-quench/stockline-hang to WALL-FILM-NULLSPACE: when three channels each sit inside a bulk-temperature model, their race does not decide truth; a jacket-minus-bulk residual the playbook dead-banded does.",
            "tags": [
                "hdpe-slurry-loop-polymerization",
                "wall-film-nullspace",
                "bulk-temperature-phantom",
                "jacket-strainer-plug",
                "c2-cut-probe",
                "triple-edge-scar",
                "pair-rollback-fails",
                "coordinated-depression",
                "correct-modify-loop-still-fails",
                "polymer-film",
                "chromium-catalyst",
                "human-ratify-loop-a",
                "pilot-loop-probe-refit",
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
            "distillation_value": "A wall-film nullspace is three correct loops looking at a bulk-temperature model of a fouled loop. Distill (1) an r_wall channel that breaks the bulk-conjunction, (2) a reversible probe that fails to drop bulk T only if a film insulates, (3) coordinated depression of every raise-go edge because rolling back any pair leaves the third above threshold, and (4) a critic head that can book a process-correct gate against a later unmonitored world loss without netting them.",
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
    if abs(aux["w1"] - 0.23) > 5e-4 or abs(aux["w2"] - 0.21) > 5e-4 or abs(aux["w3"] - 0.19) > 5e-4:
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
