#!/usr/bin/env python3
"""Build and self-check MAOS round-46 JSONL (research-only; not published)."""
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

GEN_AT = "2026-09-03T07:46:00Z"
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
OUT = Path("/tmp/maos-r46")
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
    "NITROSTAITH",
    "Chalkfen",
    "BOGIRON",
    "Mireholt",
    "CHROMLOOP",
    "Marlfell",
    "NITREVAULT",
    "Glaucove",
    "RUNNELGATE",
    "Ghyllmere",
    "ETHYNWOLD",
    "Woadfen",
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
    "UOP",
    "Axens",
    "Kellogg",
    "Honeywell UOP",
    "KBR",
    "Grace Davison",
)
R14_OPENING = (
    "Helixmere Biologics Building C lyophilizer LYO-4 is mid-primary on 8400 "
    "vials of a monoclonal antibody"
)
NOVEL_LINE = "Novel coverage: 49%"
PLANT = "SPARKHOLT"
GEO = "Scoriafen"
CELL = "RC-5"
DOMAIN = "fcc-riser-regenerator"
RECORD_ID = "maos-r46-001"
ROUND = 46
DELAY_S = 0.80
TAU_E_S = 0.92


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
        if p.parent.name == "maos-r46":
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
        if p.parent.name == "maos-r46":
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
        if p.parent.name == "maos-r46":
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
        [4580, 6518, 7234, 6_800_000, 756_000_000, 11_160_000_000, 20_880_000_000],
        [
            (1, -2, -1, 2, 1),
            (2, -5, -1, 3, 2),
            (2, -7, -2, 3, 2),
            (1, -6, -2, 2, 1),
            (1, -6, -2, 2, 1),
            (1, -6, -2, 1, 1),
            (0, -4, -3, 1, 1),
        ],
    )
    assert abs(heads["total"] - (-0.18)) < 1e-9, heads

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
        {"channel": "cyc.inlet", "t_rel_ms": 0.310, "amplitude": 0.56},
        {"channel": "dense.bed", "t_rel_ms": 1.160, "amplitude": 0.62},
        {"channel": "rot.out", "t_rel_ms": 2.020, "amplitude": 0.58},
        {"channel": "flue.o2", "t_rel_ms": 3.200, "amplitude": 0.71},
        {"channel": "cyc.inlet", "t_rel_ms": 4.140, "amplitude": 0.52},
        {"channel": "dense.bed", "t_rel_ms": 4.860, "amplitude": 0.74},
        {"channel": "rot.out", "t_rel_ms": 5.380, "amplitude": 0.60},
        {"channel": "cyc.inlet.high", "t_rel_ms": 6.518, "amplitude": 1.38},
        {"channel": "dense.in_band", "t_rel_ms": 6.704, "amplitude": 1.16},
        {"channel": "flue.o2", "t_rel_ms": 6.920, "amplitude": 0.64},
        {"channel": "ctrl.gate", "t_rel_ms": 7.234, "amplitude": 1.10},
        {"channel": "cyc.inlet", "t_rel_ms": 8.880, "amplitude": 0.48},
        {"channel": "rot.out", "t_rel_ms": 10.760, "amplitude": 0.82},
        {"channel": "dense.bed", "t_rel_ms": 13.060, "amplitude": 0.50},
        {"channel": "flue.o2", "t_rel_ms": 18.540, "amplitude": 0.47},
        {"channel": "ctrl.gate", "t_rel_ms": 26.280, "amplitude": 0.86},
        {"channel": "air.step.probe", "t_rel_ms": 6800.0, "amplitude": 0.97},
        {"channel": "cyc.inlet", "t_rel_ms": 6888.4, "amplitude": 0.44},
        {"channel": "dense.in_band", "t_rel_ms": 6972.0, "amplitude": 0.39},
        {"channel": "human.ratify", "t_rel_ms": 756000.0, "amplitude": 0.80},
        {"channel": "cyclone.isolate", "t_rel_ms": 756900.0, "amplitude": 0.73},
        {"channel": "cyclone.attack", "t_rel_ms": 757700.0, "amplitude": 0.85},
        {"channel": "rot.out", "t_rel_ms": 11160000.0, "amplitude": 0.34},
        {"channel": "cyc.inlet", "t_rel_ms": 11160740.0, "amplitude": 0.32},
        {"channel": "dense.bed", "t_rel_ms": 11161500.0, "amplitude": 0.29},
        {"channel": "cyclone.collapse", "t_rel_ms": 20880000.0, "amplitude": 0.94},
    ]

    contrast_spikes = [
        {"channel": "feed.demand", "t_rel_ms": 0.000, "amplitude": 0.85},
        {"channel": "cyc.clear", "t_rel_ms": 0.178, "amplitude": 0.79},
        {"channel": "rot.out", "t_rel_ms": 0.410, "amplitude": 0.25},
        {"channel": "dense.bed", "t_rel_ms": 1.460, "amplitude": 0.41},
        {"channel": "cyc.inlet", "t_rel_ms": 4.880, "amplitude": 0.54},
        {"channel": "ctrl.gate", "t_rel_ms": 7.060, "amplitude": 0.91},
        {"channel": "air.step.probe", "t_rel_ms": 3100.0, "amplitude": 0.36},
        {"channel": "cyclone.collapse", "t_rel_ms": 20880000.0, "amplitude": 0.11},
    ]

    excerpt = [
        {"t_us": 310, "neuron_id": 11},
        {"t_us": 1160, "neuron_id": 52},
        {"t_us": 2020, "neuron_id": 91},
        {"t_us": 3200, "neuron_id": 24},
        {"t_us": 4140, "neuron_id": 16},
        {"t_us": 4860, "neuron_id": 58},
        {"t_us": 5380, "neuron_id": 98},
        {"t_us": 6518, "neuron_id": 44},
        {"t_us": 6704, "neuron_id": 19},
        {"t_us": 6920, "neuron_id": 71},
        {"t_us": 7234, "neuron_id": 132},
        {"t_us": 8880, "neuron_id": 62},
        {"t_us": 10760, "neuron_id": 28},
        {"t_us": 13060, "neuron_id": 108},
        {"t_us": 18540, "neuron_id": 21},
        {"t_us": 26280, "neuron_id": 140},
    ]

    rec = {
        "id": RECORD_ID,
        "title": "SPARKHOLT RC-5: cyclone-inlet residual 94 K beats dense-bed-in-band by 186 us; correct MODIFY still loses cyclone C-2 to a pre-t0 afterburn anneal",
        "rights": dict(RIGHTS),
        "state": {
            "sim_or_real": "designed",
            "domain": DOMAIN,
            "scenario_name": "SPARKHOLT / Scoriafen Catalytic RC-5",
            "timestamp_local": "2026-08-02T02:44:00-05:00",
            "t0_us": 1779290400000046,
            "gate_latency_us": 716,
            "race_window_us": 500,
            "race_window_rel_ms": [6.518, 7.018],
            "description": "Scoriafen Catalytic FCC riser-regenerator RC-5 sits at 85000 bpd vacuum-gas-oil feed on a 180 t inventory two-stage regenerator when three heterogeneous, individually-correct agents jointly report 'regenerator healthy, raise feed'. ROT's 12-bit riser-outlet temperature is 524 C inside 515-535. DENSE's dense-bed thermocouple is 695 C inside 680-715. FLUE's excess O2 is 1.8 vol% inside 1.2-2.5. The conjunction is not an afterburn-false certificate: spent-cat standpipe aeration loss parks coke burn in the dilute phase, so cyclone-inlet residual is 94 K (healthy < 15; hold if > 25) while dense-bed still sees a coke-starved emulsion. Cyclone inlet infers 94 K and afterburn split 28% (hold if > 18%) but policy treats the cyclone tap as a sticky-probe tag unless dense-bed also trips (2018 'noisy cyclone TC nuisance'). Residual-first latches FEED-HOLD plus an air-step probe; dense-bed-first would have authorized FEED-RAISE 85000 to 94000 bpd into a production-catchup window with C-2 already annealing.",
            "goal": "Hold VGO feed at 85000 bpd without a catchup raise while cyclone-inlet residual > 25 K AND inferred afterburn split > 18% AND cyclone C-2 remains unisolated; keep cyclone metallurgy trips at 0 and dilute-phase temperature inside the 820 C trip.",
            "race": {
                "contenders": [
                    "cyc.inlet.high 94 K (C-2 cyclone inlet vs dense-bed T)",
                    "dense.in_band 695 C (regenerator dense-bed thermocouple)",
                ],
                "semantics": "Cyclone-residual-first latches FEED-HOLD + AIR-STEP-PROBE + C-2 isolate. Dense-bed-first latches FEED-RAISE (85000 to 94000 bpd, regen air held, no isolate).",
                "window_derivation": "500 us = one 360 us cyclone-inlet ADC slot plus 140 us dense-bed TC publish.",
                "order_evidence_note": "Margin 186 us vs combined jitter 58 us (cyclone 32 + dense-bed 26): 3.2x. The 186 us gap sits inside min(500, 500) us, so a sub-flip-bound perturbation reverses triage order. The gate rides the order-invariant floors cyclone residual > 25 K and afterburn split > 18%, not the alarm order.",
            },
            "topology": {
                "site": "Scoriafen Catalytic, invented scoria-ridge refinery town Scoriafen, FCC riser-regenerator RC-5: 85000 bpd VGO, 180 t regenerator inventory, 6 cyclones, Grade-B regenerator LOTO",
                "agents": "ROT riser-outlet temperature (vendor Rotfen): 20 Hz 12-bit on the riser head. DENSE dense-bed thermocouple (vendor Bedreave): 50 Hz on the regenerator emulsion. FLUE excess-O2 zirconia (vendor Oxyspire): 20 ms bus average on the plenum after the CO boiler. CYC cyclone-inlet thermocouple (vendor Cycloreave) is commissioned as a sticky-probe tag, not as an afterburn-integrity tag. Heterogeneous stacks, no shared intent schema, one 20 ms converter-bus epoch",
                "coupling": "All three playbook confirms live on the WRONG phase. ROT is correct that riser outlet sits at 524 C (feed still matches circulating cat). DENSE is correct that the emulsion is 695 C (coke is not burning in the dense bed). FLUE is correct that plenum O2 is 1.8 vol% (CO boiler and plenum mix hide the dilute-phase O2 sink). Playbook PB-RC-5 treats the conjunction as permission to raise feed. No agent is faulty; the dense-bed TC is looking at a coke-starved emulsion, not at C-2's dilute-phase plume.",
            },
            "sensors": [
                "riser-outlet 12-bit, 20 Hz, 22 us jitter, 524 C (dead-band 515-535)",
                "regenerator dense-bed TC, 50 Hz, 26 us jitter, 695 C (band 680-715)",
                "plenum excess-O2 zirconia, 50 Hz, 24 us jitter, 1.8 vol% (setpoint band 1.2-2.5)",
                "cyclone C-2 inlet TC, 20 Hz, 32 us jitter, residual 94 K (healthy < 15; policy floor 25 K is not armed unless dense-bed also trips)",
                "cyclone C-2 dipleg strain is NOT commissioned at t0 (installed after this incident)",
            ],
            "constraints": {
                "feed_bpd": 85000,
                "feed_hold_ceiling_bpd": 85000,
                "proposed_feed_bpd": 94000,
                "rot_C": 524,
                "rot_deadband_C": [515, 535],
                "dense_C": 695,
                "dense_band_C": [680, 715],
                "flue_o2_volpct": 1.8,
                "flue_o2_band_volpct": [1.2, 2.5],
                "cyc_residual_K": 94.0,
                "cyc_hold_K": 25.0,
                "cyc_healthy_K": 15.0,
                "afterburn_split_pct": 28.0,
                "afterburn_hold_pct": 18.0,
                "cyc_trip_C": 820,
                "regen_inventory_t": 180,
                "n_cyclones": 6,
                "fault_cyclone": "C-2",
                "regen_air_kNm3_h": 145,
            },
            "fault_context": {
                "failure_class": "DILUTE-PHASE AFTERBURN CERTIFICATE OF A DENSE-BED-HEALTHY REGENERATOR: three individually-correct heterogeneous agents each read a locally-true loop; spent-cat standpipe aeration loss partitions cyclone-true dilute-phase heat from dense-bed-true emulsion temperature, so the playbook's ROT / DENSE / FLUE conjunction is not an afterburn-false certificate",
                "igniter": "spent-cat standpipe aeration loss after 22 min of unmonitored dilute-phase afterburn; regenerator visual PASSES (plume is above the bed; C-2 dipleg is already annealed on the far side)",
                "naive_failure": "PB-RC-5 FEED-RAISE on three healthy loops: 85000 to 94000 bpd into a production-catchup window with C-2 already annealing, cyclone inlet 870 C, $4.1M plus a 36-hour unplanned stop",
            },
            "poisoned_context": {
                "naive_alarm": "Playbook PB-RC-5 (after the 2018 'noisy cyclone TC nuisance') auto-drafts FEED-RAISE whenever ROT is inside 515-535 C AND DENSE inside 680-715 C AND FLUE inside 1.2-2.5 vol%, ignoring the cyclone-inlet tap unless dense-bed also trips",
                "why_poisoned": "The three confirms are locally true and jointly insufficient. The cyclone inlet is a commissioned sensor that policy treats as sticky-probe-only. Independence of 'dense-bed in band, therefore the freeboard is not afterburning' is the hidden assumption, and it is false across an aeration-loss plus dilute-phase path.",
            },
            "constraint": "Do not raise VGO feed above 85000 bpd while cyclone-inlet residual > 25 K AND inferred afterburn split > 18%. Discriminate dilute-phase afterburn vs true high-load with a reversible air-step probe before any feed raise.",
        },
        "proposed_action": {
            "actor": "converter supervisory optimizer CSO (auto-playbook PB-RC-5 draft), submitted to gate TG-RC-5",
            "name": "feed_raise",
            "action": "FEED-RAISE: 85000 -> 94000 bpd, regen air held, no air-step probe, no C-2 isolate",
            "summary": "Treat three in-spec loops as a healthy dense-bed regenerator and raise night-shift feed to clear a production-catchup window.",
            "parameters": {
                "feed_bpd": 94000,
                "air_step_probe": False,
                "cyclone_isolate": False,
                "human_ratify": False,
            },
            "steps": [
                "assert ROT 524 C inside 515-535",
                "assert DENSE 695 C inside 680-715",
                "assert FLUE 1.8 vol% inside 1.2-2.5",
                "ramp feed 85000 to 94000 bpd over 5 min",
                "hold regen air; do not read cyclone-inlet residual as an afterburn-integrity tag",
            ],
            "evidence": [
                {
                    "observable": "cyclone-inlet residual C-2",
                    "value": 94.0,
                    "unit": "K",
                    "source": "CYC inlet TC vs dense-bed T",
                    "note": "healthy < 15 K; policy floor 25 K is not armed unless dense-bed also trips",
                },
                {
                    "observable": "regenerator dense-bed temperature",
                    "value": 695,
                    "unit": "C",
                    "source": "DENSE emulsion TC",
                    "note": "dead-band 680-715 C; lives on a coke-starved emulsion, not C-2 (residual 94 K)",
                },
                {
                    "observable": "riser-outlet temperature",
                    "value": 524,
                    "unit": "C",
                    "source": "ROT 12-bit",
                    "note": "healthy-load band 515-535 C; circulating cat still matches feed across the aeration loss",
                },
                {
                    "observable": "plenum excess oxygen",
                    "value": 1.8,
                    "unit": "vol%",
                    "source": "FLUE zirconia",
                    "note": "band 1.2-2.5; plenum-true, dilute-phase-false",
                },
                {
                    "observable": "inferred afterburn split",
                    "value": 28.0,
                    "unit": "%",
                    "source": "cyclone residual vs dense-bed lookup",
                    "note": "hold floor 18%; dilute-phase plume channels heat around the emulsion",
                },
                {
                    "observable": "race margin",
                    "value": 186,
                    "unit": "us",
                    "source": "cyc.inlet.high 6.518 ms vs dense.in_band 6.704 ms",
                    "note": "combined jitter 58 us, 3.2x; inside 500 us flip bound",
                },
            ],
            "basis": "PB-RC-5 fires on three locally-true confirms. The draft does not read residual 94 K as an afterburn residual and does not treat afterburn split 28% as a dilute-phase discriminant.",
            "expected_cost_bound": "If the draft executes: cyclone inlet 870 C at C-2, $4.1M plus 36-hour unplanned stop. If MODIFIED: probe plus isolate, with residual risk from dipleg anneal already seeded in the 22 min pre-t0 afterburn.",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "correctness": "correct",
            "decided_by": "TG-RC-5 thalamic release gate",
            "decision_t_rel_ms": 7.234,
            "rationale": "MODIFY the draft: strip the feed raise, hold 85000 bpd, run a 6.8 s air-step probe (-5% regen air), and isolate cyclone C-2 only if the probe stays afterburn-true. Numeric floor: do not raise VGO feed above 85000 bpd while cyclone-inlet residual > 25 K AND inferred afterburn split > 18%. Observed residual 94 K and split 28% both violate the release predicate, so a raise is forbidden even though all three playbook confirms are numerically true. The three confirms are not an afterburn-false certificate: they live on dense-bed emulsion past a dilute-phase plume, and the playbook's conjunction of mean-true loops is not a cyclone-true certificate. Probe discriminant: after a 6.8 s -5% air step, dilute-phase afterburn keeps |Delta residual| <= 2 K (extra air feeds the plume, not the emulsion); a live dense-bed-true unit moves residual >= 12 K. Order-code discipline: cyclone residual beat dense-bed by 186 us inside the 500 us flip bound, so triage order is flip-fragile; the hold rides the order-invariant floors, not the winner tag. Human ratification: C-2 isolate is confined-space regenerator work with fitted 12.6 min dead-man; the gate may hold and probe autonomously but may not break the cyclone interlock without the operator confirm.",
            "constraint_checked": {
                "feed_bpd": {"observed": 85000, "ceiling": 85000, "proposed_target": 94000},
                "cyc_residual_K": {"observed": 94.0, "hold_if_above": 25.0},
                "dense_C": {"observed": 695, "band": [680, 715]},
                "afterburn_split_pct": {"observed": 28.0, "hold_if_above": 18.0},
            },
        },
        "executed_action": {
            "name": "feed_hold_air_step_probe_isolate",
            "action": "FEED-HOLD + AIR-STEP-PROBE + C-2-ISOLATE (gate-mandated modification)",
            "executed_as_proposed": False,
            "parameters": {
                "feed_bpd": 85000,
                "air_step_probe": True,
                "cyclone_isolate": True,
                "human_ratify": True,
            },
            "gate_effect": "MODIFY: feed raise stripped. Hold 85000 bpd. 6.8 s air-step -5%. Probe stays afterburn-true (residual 94 -> 95 K, afterburn band |Delta residual| <= 2 K) so the cyclone interlock is broken after 12.6 min human ratify and C-2 is isolated. Setpoint resumes after a live-dense-bed verify.",
            "deviations": "PB-RC-5 feed raise stripped entirely. Regen air is stepped only for the 6.8 s probe then returned. Cyclone interlock wait added (12.6 min fitted climb+ratify). Dipleg strain survey added during the isolate (not in the draft).",
            "execution_log": [
                {"t_rel_ms": 7.234, "entry": "TG-RC-5 MODIFY latched 716 us after residual win; feed raise stripped; hold+probe authorized"},
                {"t_rel_ms": 6800.0, "entry": "air-step probe: regen air -5% for 6.8 s; residual 94 -> 95 K (afterburn band |Delta residual| <= 2 K); dense-bed 695 -> 696 C"},
                {"t_rel_ms": 756000.0, "entry": "operator ratifies cyclone interlock break after 12.6 min confined-space climb (fitted walk+interlock)"},
                {"t_rel_ms": 756900.0, "entry": "C-2 isolated; residual slaved to dense-bed; remaining cyclones recovered toward 11 K over 3.1 h"},
                {"t_rel_ms": 757700.0, "entry": "dipleg survey: C-2 already annealed on the hopper; 22 min pre-t0 afterburn logged"},
                {"t_rel_ms": 11160000.0, "entry": "true dense-bed-healthy unit: residual 11 K, split 6%, residual under 25; raise now legal on RC-5B only"},
                {"t_rel_ms": 20880000.0, "entry": "dipleg collapse at C-2 from the pre-t0 afterburn anneal; converter quarantined 16 h"},
            ],
        },
        "future_outcome": {
            "summary": "Correct MODIFY prevented the 85000->94000 bpd raise into a dilute-phase afterburn and the immediate cyclone-overheat path. The converter still failed: 22 min of unmonitored pre-t0 afterburn had already annealed cyclone C-2. Process-correct gate, bounded world loss, negative total.",
            "state_delta": {
                "feed": "held 85000 bpd through probe and isolate; later legal raise only on the sister converter after 3.1 h residual recovery",
                "regenerator": "C-2 isolated from dilute-phase plume; residual slaved to dense-bed; remaining cyclones recovered toward 11 K",
                "afterburn": "C-2 plume logged and isolated; dense-bed T no longer trusted as cyclone-true afterburn-false",
                "converter": "night-shift FCC quarantined; C-2 annealed; dipleg collapse at +5.8 h; 16 h outage",
            },
            "timeline": [
                {"t_rel_ms": -1320000.0, "event": "t0-22 min: standpipe aeration loss begins; cyclone residual crosses 25 K; dilute-phase plume starts annealing C-2"},
                {"t_rel_ms": -480000.0, "event": "t0-8 min: cyclone residual first crosses 25 K; PB-RC-5 ignores it because dense-bed is 698 C"},
                {"t_rel_ms": 0.0, "event": "t0: cyclone-residual vs dense-bed race on the converter bus"},
                {"t_rel_ms": 6.518, "event": "cyclone-inlet residual at 94 K wins by 186 us"},
                {"t_rel_ms": 6.704, "event": "dense-bed-in-band flag (loser)"},
                {"t_rel_ms": 7.234, "event": "TG-RC-5 MODIFY"},
                {"t_rel_ms": 6800.0, "event": "air-step probe confirms dilute-phase afterburn (Delta residual 1 K, afterburn band)"},
                {"t_rel_ms": 756000.0, "event": "human ratify 12.6 min; C-2 isolated; annealed dipleg logged"},
                {"t_rel_ms": 11160000.0, "event": "true dense-bed-healthy residual after 3.1 h; raise legal only with residual slave"},
                {"t_rel_ms": 20880000.0, "event": "dipleg collapse from the pre-t0 afterburn anneal; converter quarantined"},
                {"t_rel_ms": 345600000.0, "event": "+4 d contrast: sister converter RC-5B true high-load; same gate ACCEPTs the raise"},
                {"t_rel_ms": 1814400000.0, "event": "+21 d CR-F-4606: standing air-step probe + triple-edge depression mandate + cyclone inlet armed without dense-bed coincidence + dense-bed declared mix-vulnerable"},
            ],
            "observed_effects": [
                "raise avoided: feed never left 85000 bpd; 0 immediate cyclone overheats from the draft",
                "afterburn proven, not asserted: air-step |Delta residual| 1 <= 2 K afterburn band vs live-dense-bed control 14",
                "mean slaved: dense-bed T no longer a cyclone-true tag without cyclone residual",
                "converter still burned: annealed C-2 vs 0 dipleg-collapse campaign allowance; 16 h outage, $2.14M (designed $)",
                "cyclone C-2 dipleg strain was not a commissioned sensor at t0; the 22 min afterburn anneal was invisible to ROT/DENSE/FLUE",
            ],
            "surprises": [
                "Three locally-true loops are not an afterburn-false certificate: the cyclone-true dilute-phase heat was under dense-bed-true emulsion. Conjunction of in-spec mean loops was the hidden assumption, and it is false across an aeration-loss plus plume path.",
                "Partial synaptic rollback is fitted to fail: depressing any pair of go-edges leaves the third above the 0.30 fire threshold, so the feed raise still goes. Coordinated depression of all three edges is required.",
                "Delayed (5.8 h): correct hold did not undo 22 min of dipleg anneal. Collapse still fired. The gate prevented the proposed hazard and did not prevent this other one.",
                "Residue-FCC / high-CCR sub-variant: a 6.8 s -5% air step on a 0.55x inventory regenerator overshoots a LIVE unit to a 38 K false residual (trip 25). Residue-FCC campaigns must use 20 s at -1.8%.",
            ],
            "delayed_side_effects": [
                {
                    "at": "+5.8 h",
                    "effect": "Dipleg collapse at C-2 from the pre-t0 afterburn anneal; 16 h converter outage booked at $2.14M. This is the primary episode's terminal world state, not a footnote.",
                },
                {
                    "at": "+4 d",
                    "effect": "Sister converter RC-5B reaches a true high-load window (residual 8 K, dense-bed 701 C, ROT 528 C, split 5%). Same gate ACCEPTs the 85000->94000 bpd raise the primary MODIFIED away.",
                },
                {
                    "at": "+21 d",
                    "effect": "CR-F-4606 ships: air-step probe is standing configuration; triple-edge coordinated depression is the plasticity rule; cyclone inlet is armed without dense-bed coincidence; dense-bed T is labeled mix-vulnerable with a 25 K residual alarm.",
                },
            ],
            "subvariant_constraint": {
                "name": "residue-FCC / high-CCR (cycle-2 physical-constraints sub-variant)",
                "mechanism": "residue-FCC regenerator inventory 0.55x the 180 t bed (99 vs 180 t), air-step gain 2.2x, Conradson carbon 6.8 wt%",
                "probe_refit": "6.8 s -5% air step on the residue-FCC moves even a live dense-bed-true unit to a 38 K false residual (inside the 25 K trip) via plume channeling. Required probe is 20 s at -1.8% (live Delta 11 K, afterburn Delta 1). The discriminating pulse is environment-dependent in duration and amplitude.",
                "consequence": "VGO-FCC probe numbers do not port to residue-FCC high-CCR regenerators; standing configuration is per-inventory-class, not per-shop",
            },
            "embedded_contrast_decision": {
                "note": "SAME gate (TG-RC-5), OPPOSITE correct disposition, with its own 178 us race. Teaches the boundary: do not treat 'never raise' as the lesson. The discriminant is cyclone residual + afterburn split + probe, not the three playbook mean confirms alone.",
                "when": "+4 d, sister converter RC-5B, true high-load after a delayed VGO-catchup, 180 t inventory",
                "state": {
                    "sim_or_real": "designed",
                    "summary": "residual 8 K, dense-bed 701 C, ROT 528 C, split 5%. Demand flag vs cyclone-clear race: demand at t+0.000, cyclone-clear at t+0.178 ms.",
                    "race_window_us": 500,
                    "race_flip_narrative": "demand vs cyclone-clear 178 us apart inside the 500 us flip bound. Reversing order reshuffles triage minutes; the ACCEPT rides cyclone residual 8 < 25 K and a 4.4 s air-step verify that moves residual 14 K (live dense-bed, no afterburn).",
                },
                "proposed_action": {
                    "action": "FEED-RAISE 85000 -> 94000 bpd",
                    "summary": "This time the playbook predicate is met AND cyclone residual plus split agree the regenerator is afterburn-false, not plume-diluted.",
                },
                "safety_decision": {
                    "decision": "ACCEPT",
                    "rationale": "ACCEPT the raise: residual 8 K < 25, split 5% with a 4.4 s air-step verify that moves residual 14 K. Numeric floor that blocked the primary is now clear. Scope: 94000 bpd, not faster.",
                },
                "executed_action": {
                    "action": "feed raise as proposed",
                    "executed_as_proposed": True,
                },
                "future_outcome": {
                    "observed_effects": [
                        "RC-5B cyclone collapses 0; cyclone residual 9 K after the raise (no afterburn)",
                        "residual vs dense-bed 4 K after the raise (no plume)",
                    ],
                    "lesson_delta": "Three in-spec mean loops are legal release only with cyclone inlet armed, afterburn split as a plume flag, and a probe that can move residual. Same gate, opposite disposition.",
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
                "decision": "CR-F-4606: standing policy for multi-agent FCC feed raises",
                "meta_gate": "priced options: (a) RETIRE playbook mean conjunction, cyclone-inlet-only: loses a fast cheap confirm, -4200 bpd mean on 2 converters/yr; (b) KEEP + standing air-step probe + cyclone inlet armed without dense-bed coincidence + dense-bed labeled mix-vulnerable + triple-edge depression; (c) STATUS QUO: fitted afterburn-plume pass rate 0.47%/campaign x $4.1M cyclone-overheat plus the silent dipleg-anneal load",
                "outcome": "approved SCOPED option (b) on the 2 180 t VGO converters that share the ROT/DENSE/FLUE stack; residue-FCC campaigns get the 20 s / -1.8% probe table; night-shift CSV exports must carry 0.2 K native resolution (the fraud tail's 2.0 K quantization is 10 bins off plant truth)",
            },
            "hazard_avoided": "immediate cyclone inlet 870 C from a 85000->94000 bpd raise into a dilute-phase afterburn; $4.1M plus 36-hour unplanned stop and the shop-stop path that would have followed an uncontained increase",
            "incident": "Dipleg collapse on the night-shift converter from the pre-t0 afterburn anneal; converter quarantined 16 h; $2.14M designed cost. Mechanism is 22 min pre-t0 afterburn growth, not the gate's hold.",
            "latency_ms": 0.716,
            "reward_inflection_t_us": 20880000000,
            "reward_inflection_note": "Safety and task dive at dipleg collapse (5.8 h) when the pre-t0 annealed hopper opens. Gate tick at 7234 us is process-correct and is not the inflection.",
            "counterfactuals": {
                "execute_draft_as_proposed": "feed hits 94000 bpd at +5 min; immediate cyclone inlet 870 C at C-2; $4.1M plus 36 h; the afterburn-plume story is never found because collapse morphology destroys the race evidence",
                "hold_without_probe": "afterburn stays; residual stays at 94 K; operator eventually raises on the same three mean confirms 2 h later",
                "rollback_any_pair": "any two go-edges depressed below 0.30 leaves the third at 0.50 / 0.44 / 0.41; the feed raise still fires. Coordinated depression of all three is the cure",
            },
            "race_result": {
                "winner": "cyc.inlet.high (6.518 ms, residual 94 K)",
                "loser": "dense.in_band (6.704 ms, dense-bed 695 C)",
                "margin_us": 186,
                "counterfactual_if_reversed": "Dense-bed-first by < 186 us inside the 500 us window would have headed the PB-RC-5 feed raise in the triage queue. The numeric floors still MODIFY. The flip costs seconds of playbook inertia, not the verdict — unless a weak supervisor rides the winner tag instead of cyclone residual and afterburn split.",
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
            "notes": "Correct MODIFY, converter still burned. total -0.18 = 0.08 + -0.36 + -0.13 + 0.14 + 0.09. Process heads stay honest (coherence + exploration from the probe); world loss sits on safety and efficiency without netting.",
            "component_notes": "task_progress 0.08: feed held and remaining cyclones recovered, but the night-shift gasoline is one quality unit so the campaign is not a success. safety -0.36: dipleg collapse from pre-t0 afterburn anneal, no 94000 bpd cyclone overheat from the draft. efficiency -0.13: 3.1 h extra recovery + 12.6 min HITL + 16 h outage. coherence 0.14: three agents retained, dense-bed-mix vs cyclone-true diagnosed, triple-edge scar exhibited. exploration 0.09: air-step probe is a new reversible discriminant.",
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
            "note": "Loihi-2 4-core 23 pJ/spike; populations cyc 0-39, dense 40-79, rot 80-119, gate 120-159; excerpt is the 40 ms decision window (verdict at 7234 us)",
            "excerpt": excerpt,
            "routing": {
                "source": "mean_healthy_pop",
                "target": "feed_raise_pop",
                "table": [
                    {
                        "from": "rot_in_band_pop",
                        "to": "feed_raise_pop",
                        "weight": 0.25,
                        "weight_at_illusion": 0.50,
                        "weight_commissioned": 0.17,
                        "note": "scar edge 1: 0.17 commissioned -> 0.50 during the 22 min illusion -> 0.25 after coordinated ACh-gated depression",
                    },
                    {
                        "from": "dense_in_band_pop",
                        "to": "feed_raise_pop",
                        "weight": 0.22,
                        "weight_at_illusion": 0.44,
                        "weight_commissioned": 0.16,
                        "note": "scar edge 2: depressing edges 1+3 leaves this at 0.44 > 0.30 fire threshold",
                    },
                    {
                        "from": "flue_in_band_pop",
                        "to": "feed_raise_pop",
                        "weight": 0.20,
                        "weight_at_illusion": 0.41,
                        "weight_commissioned": 0.15,
                        "note": "scar edge 3: depressing edges 1+2 leaves this at 0.41 > 0.30. Coordinated depression of all three is required",
                    },
                    {
                        "from": "cyc_inlet_pop",
                        "to": "feed_hold_pop",
                        "weight": 0.64,
                        "note": "discriminating edge: cyclone-true residual to hold. Not a scar; this is the pathway the gate potentiates",
                    },
                ],
                "third_factor": {
                    "modulator": "acetylcholine",
                    "tau_e_s": TAU_E_S,
                    "tau_e_ms": TAU_E_S * 1000.0,
                    "eligibility": "coordinated pre_post_stdp on ALL THREE mean-healthy-go edges; ACh at residual-win tags rot.in_band->raise, dense.in_band->raise, and flue.in_band->raise; negative credit at probe-fail (dilute-phase afterburn confirmed, +0.80 s) depresses ALL THREE. trace e^{-0.80/0.92}=0.41913; eta 0.59647 / 0.52489 / 0.50103; dw -0.250 / -0.220 / -0.210; weights 0.50->0.25, 0.44->0.22, 0.41->0.20. Rolling back any pair is fitted to fail (the remaining edge stays > 0.30).",
                },
            },
        },
        "gate_snn": {
            "decision_window_ms": 25,
            "decision_window_s": 0.025,
            "decision": "MODIFY",
            "note": "modify_hold integrates cyclone residual + afterburn split against playbook drive; accept_raise and reject_abort stay sub-threshold; decision matches safety_decision.decision",
            "populations": [
                {"name": "modify_hold", "neurons": 80, "threshold": 0.55, "mean_rate_hz": 20.0, "spikes": 40},
                {"name": "accept_raise", "neurons": 80, "threshold": 0.55, "mean_rate_hz": 8.0, "spikes": 16},
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
            "scenario": "ZW -- SPARKHOLT / Scoriafen Catalytic RC-5: dilute-phase afterburn certificate of a dense-bed-healthy regenerator; correct MODIFY to hold+air-step+isolate; converter still fails on unmonitored pre-t0 cyclone anneal",
            "coordination_failure_class": "DILUTE-PHASE AFTERBURN CERTIFICATE OF A DENSE-BED-HEALTHY REGENERATOR: three individually-correct heterogeneous agents each read a locally-true loop; spent-cat standpipe aeration loss partitions cyclone-true dilute-phase heat from dense-bed-true emulsion temperature, so the playbook's ROT / DENSE / FLUE conjunction is not an afterburn-false certificate",
            "injections": {
                "cycle1_domain": "fcc-riser-regenerator (justified novel subdomain of industrial-process / fluid-catalytic-cracking): first FCC plant in this factory; displaces warehouse-amr, aerial-swarm, district-heating, event-camera-traffic-grid, pharmaceutical-lyophilization, water-treatment, float-glass, underwater-rov, electrolytic-aluminum, czochralski-pull, slot-die coating, pem-water-electrolysis, wind-turbine pitch, surgical-assist, optical-fiber-draw, kraft-recovery-boiler, steel-continuous-caster, humanoid-locomotion, vacuum-induction melt, steam-methane reformer, cement-rotary-kiln-clinker, autoclave-composite-cure, geothermal-binary-orc, tire-curing-press, chlor-alkali-membrane-electrolysis, delayed-coker-drum-switch, lng-mche-mixed-refrigerant, claus-sulfur-recovery, ammonia-synthesis-converter, blast-furnace-burden-descent, hdpe-slurry-loop-polymerization, ammonia-haber-bosch-converter, hydroelectric-kaplan-wicket, and ethylene-steam-cracker-coil. Domain constraint: feed ceiling while cyclone residual > 25 K with dense-bed still inside the healthy band. Sensor delta: +ROT, +DENSE TC, +FLUE zirconia, +cyclone-inlet TC, -any freeze-dryer / tin-bath / cold-box / coater / potline / PEM stack / hub encoder / insole GRF / VIM pyrometer / reformer TMT / kiln zirconia / smelt IR / autoclave ply-TC / ORC shell-pressure / mold-platen TC / cell-pH / drum wet-foam / MCHE cold-end / Claus tail / ammonia bed-max / blast-furnace sector radar / HDPE wall-dT / Kaplan wicket / cracker coil",
                "cycle1_tail": "spent-cat standpipe aeration loss + dilute-phase afterburn certificate (sensor-topology / wrong-phase class): regenerator visual PASSES while the plume sits above the bed and the annealed dipleg is on the far side. Fitted base rate 0.47%/campaign from an afterburn-growth MC (designed visual threshold, fitted plume geometry). Naive failure = FALSE PERMISSION (feed raise on three mean-side non-trips).",
                "cycle2_domain_subvariant": "residue-FCC / high-CCR (physical-constraints clause): 0.55x regenerator inventory, 2.2x air-step gain; 6.8 s / -5% VGO-FCC pulse overshoots live unit to a 38 K false residual, so the probe must move to 20 s / -1.8%",
                "cycle2_tail": "night-shift forged cyclone-inlet CSV (human-intent deception, disjoint class): shift lead posts a historian export showing residual = 8 K at t=1.4 h to clear a production-catchup slot. Plant historian is 0.2 K (10 bins vs the 2.0 K screenshot). Rejected on quantization fingerprint plus live residual 94 K and dense-bed 695 C at the claimed afterburn-false. Base rate ~0.33% of Sunday-night campaigns, DESIGNED and flagged.",
            },
            "densification_delta_cycle2": "+1 physical-constraint sub-variant (residue-FCC probe refit), +1 tail (night-shift cyclone-CSV forgery), +10 primary spikes (16 -> 26) + an 8-event contrast train with its own 178 us race, +2 ticks (5 -> 7), +2 delayed side-effects (+5.8 h dipleg collapse as PRIMARY terminal, +21 d CR-F-4606), +1 triple-edge scar with pair-rollback-fails arithmetic, +1 HITL 12.6 min ratification, + dipleg anneal as the honest negative-result mechanism",
            "gaps_targeted": [
                "NOTES-r04 gap 5 / r14 residual: primary episode is a correctly-gated intervention that nonetheless FAILS (converter quarantined; total -0.18; cyclone overheat avoided is booked separately from the delayed dipleg collapse)",
                "NOTES-r14 item 4: LEARNING-ON-LEARNING DEPTH — three go-edges; rollback of any pair is fitted to fail; coordinated depression of all three exhibited with eligibility arithmetic",
                "NOTES-r04 gap 4 (partial): human ratification of the cyclone interlock, 12.6 min fitted, without switching sim_or_real to hil (plant remains designed)",
                "NOTES-r42 domain candidates: not blast-furnace-burden-descent (r42), not delayed-coker-drum-switch (r38), not lng-mche-mixed-refrigerant (r39), not claus-sulfur-recovery (r40), not ammonia-synthesis-converter (r41), not hdpe-slurry-loop-polymerization (r43), not ammonia-haber-bosch-converter (r44 batch), not hydroelectric-kaplan-wicket (r44 builder rewrite), not ethylene-steam-cracker-coil (r45 in-flight); fcc-riser-regenerator is unused. autonomous-driving, grid-inspection left unused.",
            ],
            "race_flip_narrative": "cyc.inlet.high @ 6.518 ms vs dense.in_band @ 6.704 ms (186 us) inside race_window_us 500. Gap < min(500, 500) us so a sub-flip-bound perturbation reverses which alarm heads the PB-RC-5 queue. The gate excludes the winner tag and rides cyclone residual > 25 K and afterburn split > 18% — order-invariant floors. Extends the flip-fragility series from arbitration/causation/attribution/initiation/consensus/permission/kinematic-certificate/tendon-nullspace/meniscus-certificate/ghost-contact/crucible-weep/TMT-spatial-mean/burning-zone-certificate/membrane-integrity/drum-switch/MCHE-cold-end/descent-true-certificate to AFTERBURN-FALSE CERTIFICATE: when three mean-side channels agree, their race does not decide truth; a cyclone-inlet tap that policy treated as sticky-probe-only does.",
            "tags": [
                "fcc-riser-regenerator",
                "dilute-phase-afterburn",
                "dense-bed-healthy-certificate",
                "cyclone-inlet-discriminant",
                "air-step-probe",
                "triple-edge-scar",
                "pair-rollback-fails",
                "coordinated-depression",
                "correct-modify-converter-still-fails",
                "dipleg-anneal",
                "human-ratify-regenerator",
                "residue-fcc-probe-refit",
                "night-shift-forgery",
                "same-gate-opposite-disposition-contrast",
                "industrial-process",
                "research-only",
            ],
            "snn_tags": ["race", "refractory", "adaptation", "third-factor", "multi-edge-eligibility"],
            "distillation_value": "A dilute-phase afterburn dense-bed-healthy certificate is three correct loops looking at emulsion temperature that is not the afterburning freeboard. Distill (1) a cyclone-inlet tap that policy had treated as sticky-probe-only, (2) a reversible probe that moves residual only if the dense bed is live, (3) coordinated depression of every mean-healthy-go edge because rolling back any pair leaves the third above threshold, and (4) a critic head that can book a process-correct gate against a later unmonitored world loss without netting them.",
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
    if abs(aux["w1"] - 0.25) > 5e-4 or abs(aux["w2"] - 0.22) > 5e-4 or abs(aux["w3"] - 0.20) > 5e-4:
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
    notes = f"""# NOTES — Multi-Agent Ouroboros Swarm, run 2026-09-02-final-heavy, ROUND 46

Factory: multi-agent-ouroboros-swarm. One scenario (ZW), strict loop:
Generator v1 -> cycle 1 (Critic, Diversity Enforcer, Edge-Case Hunter,
Neuromorphic Translator, Trajectory Builder -> v2) -> cycle 2 (all six -> v3
final). v3 is the single line of batch-r46.jsonl. Full labeled transcript:
swarm-transcript-r46.md. Quota Q=1. Record id maos-r46-001. Generator grok-4.6.
Rights: RM-793 research-only (SpaceXAI/xAI, SuperGrok Heavy consumer chat).
Nothing under outputs/raw/ was touched.

ORCHESTRATION NOTE: dispatched AS round 46 of the 2026-09-02-final-heavy
window. Writes are create-only under /tmp/maos-r46/. Prior context read for
gap targeting and de-collision: prompts/02-multi-agent-ouroboros-swarm.md,
prompts/_factory-contract.md, and staged r14–r45 (re-censused immediately
before emit; r43 CHROMLOOP HDPE / r44 batch NITREVAULT ammonia landed while
r44's builder was rewritten toward RUNNELGATE hydroelectric; r45 ETHYNWOLD
ethylene-steam-cracker is in-flight builder-only).
Explicitly avoided cloning
LYOSHIELD, CINDERWICK, TRIAD / Meridian, QUILLFORGE, NIGHTWELL, FERRICLEAVE,
CASSITER, OXBOWREEL / MURENA, REDHALL, SEEDLATCH / Quartzmere / Quartzridge,
STRIAFOIL / Kelpholt, PROTONIL / Ashspire, TORSIONKEY / Ridgeholt, ORRIS /
Holmwick, WHORLSPAR / Pikeshear, IONSPATE / Thornmere, SKULLGATE / Bloomholt,
CALXION / Aldersedge, MAGNORIL / Basaltspit, GORSEFLUE / Copseholt,
SODASHARD / Cairnmere, CLINKERFELL / Flintmere, LINTELPLY / Greystair,
KAOTHARN / Riftwold, TREADNOLL / Slatebeck, ANOLITH / Siltfen,
DRUMWROTH / Pitchfen, RIMEBRAID / Floeholt, BRIMVAULT / Pyritefen,
NITROSTAITH / Chalkfen, BOGIRON / Mireholt, CHROMLOOP / Marlfell,
NITREVAULT / Glaucove, RUNNELGATE / Ghyllmere, ETHYNWOLD / Woadfen,
VANTIS-CADENCE-AEGIS, THERMION, OKTAVE, STARLING, VERDIGRIS. Plant is
invented SPARKHOLT / Scoriafen Catalytic RC-5.

## What this round produced

Scenario ZW — "SPARKHOLT / Scoriafen Catalytic RC-5": an 85000 bpd
VGO FCC riser-regenerator at 180 t inventory / 6 cyclones. Three
heterogeneous, individually-correct agents — ROT (riser outlet T), DENSE
(dense-bed T), FLUE (plenum excess O2) — each report their local
loop in-spec. The conjunction is not an afterburn-false certificate.
Spent-cat standpipe aeration loss parks coke burn in the dilute phase.
ROT reads 524 C inside 515-535 (circulating cat still matches feed).
DENSE is 695 C inside 680-715 (coke-starved emulsion). FLUE is 1.8 vol%
inside 1.2-2.5 (plenum mix). Cyclone-inlet residual infers 94 K
(healthy < 15; hold if > 25) but is policy-treated as a sticky-probe
tag unless dense-bed also trips (2018 noisy cyclone TC nuisance). The
coordination-failure CLASS is new to this factory: DILUTE-PHASE
AFTERBURN CERTIFICATE OF A DENSE-BED-HEALTHY REGENERATOR. Completes a
different family than r01-r04 and staged r14-r45 (livelock /
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
delayed-coker wet-foam / MCHE warm-end ice / Claus incinerator-masked
bypass / ammonia basket-bypass / blast-furnace burden hang / HDPE
wall-film / hydroelectric Kaplan). Here every agent is correct, the
dense-bed TC is looking at a coke-starved emulsion, and the playbook's
three mean confirms are not a cyclone-true afterburn-false certificate.

The gate is a correct MODIFY (numeric floor: do not raise feed above
85000 bpd while cyclone residual > 25 K AND inferred afterburn
split > 18%). TG-RC-5 strips PB-RC-5's feed raise, holds 85000 bpd,
runs a 6.8 s air-step probe -5% (afterburn keeps |Delta residual|
1 <= 2 K; live would move >= 12), and isolates C-2 after a
12.6 min regenerator human ratify. Immediate cyclone overheat is avoided
(0 from the draft). The PRIMARY episode nonetheless FAILS: 22 min of
unmonitored pre-t0 afterburn growth had already annealed the C-2 dipleg.
Dipleg collapse at +5.8 h; 16 h outage; $2.14M designed. Reward
total -0.18 with process heads honest and world loss un-netted.

Triple-edge scar (NOTES-r14 item 4): rot.in_band -> feed_raise
(0.17 commissioned -> 0.50 at illusion -> 0.25 after ACh-gated
depression) AND dense.in_band -> feed_raise (0.16 -> 0.44 -> 0.22) AND
flue.in_band -> feed_raise (0.15 -> 0.41 -> 0.20). Eligibility trace
e^{{-0.80/0.92}} = {aux['trace']:.5f}; eta {aux['eta1']:.5f} / {aux['eta2']:.5f} /
{aux['eta3']:.5f}; dw -0.250 / -0.220 / -0.210. Partial rollback of any pair
leaves the third at 0.50 / 0.44 / 0.41, all > 0.30 fire threshold —
fitted to fail. Coordinated depression of all three is the cure.

### Injections (all four present and disjoint)
- Cycle-1 domain: **fcc-riser-regenerator** — justified novel
  subdomain of industrial-process / fluid-catalytic-cracking, unused
  across 2026-08-17, 2026-08-30, and staged r14-r45. Not warehouse-amr
  (r01), not aerial-swarm (r02), not district-heating (r03), not
  event-camera-traffic-grid (r04), not lyophilization (r14), not
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
  (r43), not ammonia Haber-Bosch (r44 batch), not Kaplan wicket
  (r44 builder), not ethylene-steam-cracker (r45 in-flight).
  autonomous-driving, grid-inspection left unused.
- Cycle-1 tail: standpipe aeration loss + dilute-phase afterburn
  certificate. Regenerator visual PASSES (plume above the bed).
  Fitted-style base rate 0.47%/campaign (afterburn-growth MC; visual
  threshold designed, flagged). Naive = FALSE PERMISSION.
- Cycle-2 domain sub-variant: residue-FCC / high-CCR, 0.55x
  inventory, 2.2x air-step gain; 6.8 s / -5% VGO pulse overshoots
  live unit to a 38 K false residual; probe must move to 20 s / -1.8%.
- Cycle-2 tail: night-shift forged cyclone-inlet CSV at 2.0 K
  quantization vs plant 0.2 K (10 bins) plus live residual 94 K and
  dense-bed 695 C at the claimed afterburn-false. Human-intent class,
  disjoint from cycle 1's accidental aeration loss. Base rate ~0.33%
  of Sunday-night campaigns, DESIGNED, flagged.

### Structural density moves
- Embedded SAME-GATE contrast (+4 d sister converter) with its own 178 us
  race (demand vs cyclone-clear) and ACCEPT of the raise the primary
  MODIFIED away.
- Learned-weight provenance on THREE edges with pair-rollback-fails.
- HITL regenerator ratify 12.6 min (gap 4 partial; sim_or_real stays
  designed).
- Governance CR-F-4606 prices retire-vs-probe-vs-status-quo and mandates
  native 0.2 K CSV exports (the fraud fence).
- Flip-fragility extended to AFTERBURN-FALSE CERTIFICATE: when three
  mean-side channels agree, their race does not decide truth; a
  cyclone-inlet tap that policy treated as sticky-probe-only does.

## Self-critique of this round's batch

### Strengths
- The headline class is mechanistically tight: three locally-true mean
  loops live on a coke-starved emulsion. Conjunction is not cyclone-true
  afterburn-false.
- Negative-result honesty: the gate does the right thing and the
  converter still fails for a reason the commissioned sensors could not
  see. Total -0.18.
- Triple-edge scar is load-bearing: the record states a counterfactual
  where rolling back any pair fails, with the fire threshold 0.30
  exhibited on each remaining edge.
- Contrast ACCEPT on a true high-load regenerator prevents "never raise"
  as the lesson.
- Distinct from r32 reformer TMT-mean, r38 delayed-coker wet-foam, r40
  Claus incinerator-masked bypass, and r42 blast-furnace hang: FCC
  dilute-phase afterburn with cyclone inlet vs dense-bed T, not tube-wall,
  not drum foam, not tail CEMS, not sector radar.

### Weaknesses (honest)
- Probe error bands, the 0.47%/campaign afterburn rate, the $2.14M /
  $4.1M figures, the 12.6 min climb latency, and the night-shift 0.33%
  base rate are DESIGNED constants and are flagged. Closed-loop offsets
  (plenum mix hiding dilute-phase O2, residue-FCC inventory d-t) are
  derived from those inputs, not discovered by an unauthored process.
- Dipleg-anneal model is a designed 22 min afterburn-growth mapping; no
  full CFD of the freeboard plume shipped.
- Human-in-the-loop is ratification latency, not sim_or_real=hil. Gap 4
  remains open as a provenance cell.
- Cross-record arc is not discharged; +21 d CR-F-4606 is a hook, not a
  serial igniter into another round. autonomous-driving and
  grid-inspection remain unused.

### Realism of noise / latencies
Ladder: 186 us race / 178 us contrast race / 0.8 ms refractory floor
(tightest exhibited same-channel gap {gap:.3f} ms on {gap_ch}) / 500 us race
window / 716 us gate latency / 20 ms bus epoch / 40 ms raster / 6.8 s
probe / 12.6 min HITL / 5 min naive raise-ramp counterfactual / 22 min
pre-t0 afterburn growth / 3.1 h residual recovery / 5.8 h dipleg collapse /
+4 d contrast / +21 d governance. Adaptation decay on cyc.inlet
(0.56->0.52->1.38->0.48->0.44->0.32), dense.bed (0.62->0.74->0.50->0.29),
rot.out (0.58->0.60->0.82->0.34), flue.o2 (0.71->0.64->0.47).

### Value for SNN distillation
- DILUTE-PHASE AFTERBURN = THREE CORRECT LOOPS, WRONG PHASE.
- CYCLONE-TRUE INLET CHANNEL that policy treated as sticky-probe-only as
  the tie-break.
- REVERSIBLE PROBE that moves residual iff the dense bed is live.
- TRIPLE-EDGE ELIGIBILITY: coordinated depression; pair rollback fails.
- CRITIC HEAD that can hold a process-correct MODIFY against a later
  unmonitored world loss without netting.

## Reconciliation and validity receipts
- reward_components: 5-head unweighted signed sum {rec['reward_components']['total']}
  and 7-tick signed sum reconcile to total with |diff| < 1e-9. Embedded
  contrast 5-head sum 0.49 reconciles independently.
- spike_events: primary {len(rec['spike_events'])} events, one key t_rel_ms,
  globally non-decreasing, min same-channel gap {gap:.3f} ms >= 0.8 ms, 3
  channels inside race_window_us 500 (cyc.inlet.high 6.518, dense.in_band 6.704,
  flue.o2 6.920). Contrast 8 events, own race, min same-channel gap well
  above 0.8 ms.
- Sidecars: raster spikes 51 == round(160 x 8.0 x 0.040); energy 1173 pJ /
  0.001173 uJ at 23 pJ/spike; excerpt 16 events inside [0, 40000] us,
  neuron_id < 160, same-neuron gap N/A (unique ids) / >=1000 us; routing 4
  entries with three scar edges' before/after pair; third factor tau 0.92 s
  == 920 ms; gate_snn pools 40/16/4 == round(n x rate x 0.025) each,
  decision MODIFY == safety_decision.decision.
- Pipeline: {pipeline_receipt}

## Novel coverage
The coordination-failure CLASS (dilute-phase afterburn certificate of a
dense-bed-healthy regenerator), the domain (FCC riser-regenerator /
fluid-catalytic-cracking), the air-step probe discriminant, the
triple-edge scar with pair-rollback-fails, the primary negative-result
(correct MODIFY, converter still fails on unmonitored dipleg anneal),
the HITL regenerator ratify, the residue-FCC probe-duration refit, and
the night-shift 10-bin quantization fence are absent from prior
committed ouroboros rounds and from staged r14-r45. Repeated elements
discounted: same-gate contrast (r02/r03/r04/r14), governance-pricing
scaffold, flip-fragility series (extended to afterburn-false
certificate, but the move rhymes), sequenced recovery shape,
third-factor rollback form (here three edges rather than r14's two),
negative-result primary (r14 staged). Adjacent thermal rounds (r32
reformer, r38 coker, r40 Claus, r42 blast furnace) share
industrial-process scaffolding but not FCC afterburn physics. Weighing
a new failure family + cure vocabulary + domain against those reused
scaffolds:

{NOVEL_LINE}

## What ROUND 47 should add
1. FIT THE DESIGNED CONSTANTS: afterburn-growth arrival, probe error
   bands, dipleg-anneal kinetics, night-shift claim process.
2. HIL PROVENANCE CELL: put the regenerator ratify on a hardware-in-loop
   cyclone interlock with fitted latency as state.sim_or_real=hil.
3. CROSS-RECORD ARC: let CR-F-4606's residual alarm be the igniter of
   the next round rather than a dangling +21 d leaf.
4. Domain candidates (de-collided): autonomous-driving; grid-inspection
   (if distinct from STARLING aerial-swarm and TORSIONKEY pitch);
   hydrocracker; paper-machine headbox; Bayer alumina digestion; EAF
   foaming slag. AVOID fcc-riser-regenerator (now used), ethylene-steam
   cracker (r45 claimed), ammonia-converter / Haber-Bosch (r41/r44),
   hydroelectric Kaplan (r44 builder), HDPE slurry loop (r43),
   blast-furnace burden descent (r42), delayed-coker, LNG MCHE, Claus,
   chlor-alkali membrane, cement-rotary-kiln clinker, kraft-recovery,
   pem-electrolysis, electrolytic-aluminum, humanoid-locomotion,
   steel-caster mold-level, surgical-assist, wind-turbine pitch,
   float-glass, lyophilization, event-camera-traffic-grid,
   district-heating, aerial-swarm, warehouse-amr, underwater-rov,
   czochralski-pull, slot-die coating, optical-fiber-draw,
   vacuum-induction melt, steam-methane reformer, irrigation-canal,
   autoclave-composite-cure, geothermal-binary-orc, tire-curing-press,
   and any LYOSHIELD / CINDERWICK / TRIAD / SKULLGATE / CALXION /
   MAGNORIL / GORSEFLUE / CLINKERFELL / SODASHARD / LINTELPLY /
   KAOTHARN / TREADNOLL / ANOLITH / DRUMWROTH / RIMEBRAID / BRIMVAULT /
   NITROSTAITH / BOGIRON / CHROMLOOP / NITREVAULT / RUNNELGATE /
   ETHYNWOLD / SPARKHOLT plant.
"""
    (OUT / "NOTES-r46.md").write_text(notes)
    return notes


def write_transcript(rec, line):
    c1_spikes = [e for e in rec["spike_events"] if e["t_rel_ms"] <= 26.280]
    text = """# Multi-Agent Ouroboros Swarm — Round 46 transcript

Factory: multi-agent-ouroboros-swarm
Run: 2026-09-02-final-heavy
Generator: grok-4.6
Record id: maos-r46-001
Quota Q: 1
Rights: RM-793 research-only (SpaceXAI/xAI SuperGrok Heavy consumer chat)
Plant: invented SPARKHOLT / Scoriafen Catalytic RC-5 (not TRIAD / Meridian / VANTIS-CADENCE-AEGIS / LYOSHIELD / CINDERWICK / DRUMWROTH / RIMEBRAID / BOGIRON / ETHYNWOLD)

Two densifying cycles. Verbatim headings in order. Trajectory Builder cycle 2
emits the only JSONL line (also written to batch-r46.jsonl).

---

# CYCLE 1 — Foundation + injections

## Generator

Design intent: an 85000 bpd VGO FCC where three correct agents each
read a regenerator-mean loop because spent-cat standpipe aeration loss
partitions cyclone-true dilute-phase heat from dense-bed-true emulsion.
The naive playbook raises feed into an afterburning freeboard. The gate
must MODIFY on a numeric feed ceiling, not by killing an agent.
sim_or_real=designed. Reward heads are
task_progress/safety/efficiency/coherence/exploration.

Cycle-1 base arc (pre-critic): state at Scoriafen RC-5, 85000 bpd,
ROT 524 C, DENSE 695 C, FLUE 1.8 vol%, proposed FEED-RAISE
94000 bpd, safety MODIFY to FEED-HOLD, executed hold without the
air-step numbers fully specified, outcome "afterburn found, converter saved"
(this last claim is the defect the later cycles will refuse to keep).
Sixteen spikes, five ticks, raster/gate_snn present but the scar is a
single edge.

```json
{
  "id": "maos-r46-001",
  "state": {
    "sim_or_real": "designed",
    "domain": "industrial-process",
    "description": "Converter RC-5 at body feed; three mean loops in-spec; supervisor proposes feed-raise.",
    "t0_us": 1779290400000046,
    "gate_latency_us": 716,
    "race_window_us": 500
  },
  "proposed_action": {"name": "feed_raise", "parameters": {"feed_bpd": 94000}},
  "safety_decision": {"decision": "MODIFY", "rationale": "Hold; do not raise feed while cyclone residual is high."},
  "executed_action": {"name": "feed_hold", "executed_as_proposed": false},
  "future_outcome": {"summary": "Afterburn found, converter saved."},
  "reward_components": {"total": 0.40, "_aggregation": "total = task_progress + safety + efficiency + coherence + exploration"},
  "meta": {"round": 46, "factory": "multi-agent-ouroboros-swarm", "generator": "grok-4.6"}
}
```

That v1 object is a scaffold, not the publishable line. Defects below are
intentional for the critic to catch.

## Critic

Numbered defects on the cycle-1 Generator scaffold:

1. **blocking — reward arithmetic / false success.** `reward_components.total`
   0.40 is asserted without the five heads, without ticks, and against an
   outcome that claims "converter saved". If the pre-t0 annealed dipleg later
   collapses, booking +0.40 is a lie. Fix: declare `_aggregation`, emit
   3–8 ticks that sum to task_progress+safety+efficiency+coherence+exploration,
   and do not call a quarantined converter a save.
2. **blocking — weak safety rationale.** `safety_decision.rationale` has no
   numeric floor. Contract requires a concrete constraint. Fix: quote
   feed <= 85000 bpd while cyclone residual > 25 K AND inferred
   afterburn split > 18%.
3. **major — domain is a bucket, not a plant.** `state.domain` =
   `industrial-process` collides with generic MES vocabulary and teaches
   nothing. FCC riser-regenerator (cyclone inlet vs dense-bed T,
   afterburn split as a plume flag) is absent from prior ouroboros
   rounds and must be named.
4. **major — race under-specified.** One cyclone channel cannot be a race.
   Need >=2 channels inside `race_window_us` with globally sorted `t_rel_ms`
   and same-channel refractory >= 0.8 ms.
5. **minor — single-edge scar.** Raster routing with one potentiated weight
   repeats r04's one-edge rollback and is thinner than r14's two-edge.
   NOTES-r14 item 4 asked for three edges where pair rollback fails.

Critic does not rewrite the trajectory.

## Diversity Enforcer

Injected novel domain (exactly 1 this cycle): **fcc-riser-regenerator**
(justified novel subdomain of industrial-process / fluid-catalytic-cracking;
explicit tag `fcc-riser-regenerator`).

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
hdpe-slurry-loop-polymerization, ammonia-haber-bosch-converter,
hydroelectric-kaplan-wicket, or ethylene-steam-cracker-coil.
autonomous-driving and grid-inspection are left unused.

Domain-specific constraint: feed must remain <= 85000 bpd while
cyclone residual > 25 K even if dense-bed T is inside the healthy
band; afterburn split is a plume flag the dense-bed TC cannot substitute
for.

Sensor delta: +ROT, +DENSE TC, +FLUE zirconia, +cyclone-inlet TC;
-any mobile robot, -event-camera gantries, -DVS, -Pirani/CM,
-RGA quadrupole, -DVL, -pitch encoder, -tendon LVDT, -insole GRF,
-kiln zirconia, -smelt IR, -cell-pH, -drum wet-foam, -MCHE cold-end,
-Claus tail, -ammonia bed-max, -blast-furnace sector radar, -HDPE wall-dT,
-Kaplan wicket, -cracker coil.

`state.domain` and `meta.domain` both become `fcc-riser-regenerator`.
Opening of `state.description` must Jaccard < 0.4 against prior plants
(Scoriafen night-shift afterburn, not a lyophilizer, not a corridor, not a tin
bath, not a ROV pad, not a potline, not a PEM stack, not an OR, not a
gait lab, not a kiln, not a kraft boiler, not a coker drum, not an LNG
MCHE, not a blast furnace, not an HDPE loop, not a cracker coil).

## Edge-Case Hunter

Injected adversarial tail (exactly 1 this cycle): **standpipe aeration
loss + dilute-phase afterburn certificate**.

- Trigger: spent-cat standpipe aeration loss plus dilute-phase plume,
  cyclone residual 94 K, dense-bed 695 C.
- Base rate: <1% — 0.47%/campaign from an afterburn-growth MC (regenerator
  visual threshold is designed; plume geometry fitted-style). Visual
  PASSES because the plume sits above the bed.
- Naive failure: FALSE PERMISSION. PB-RC-5 sees three in-spec mean
  loops, raises 85000->94000 bpd, cyclone inlet 870 C, $4.1M.
- Trajectory edit: put the afterburn in `state.fault_context`, make each
  agent's confirm a different mean-side slice of the same cyclone-false
  state (rot-in-band, dense-in-band, flue-in-band). Cyclone inlet is
  readable but policy-treated as sticky-probe-only.

Distinct from stacked-dead-band permission (fragments of one trip vs
wrong-phase sensing), from r32 reformer TMT-mean (tube wall vs freeboard),
from r40 Claus incinerator-masked bypass, and from r42 blast-furnace hang
(stockline vs cyclone inlet).

## Neuromorphic Translator

Cycle-1 temporal densification (16 spikes, 5 ticks, 40 ms raster):

| channel | t_rel_ms | amplitude |
|---|---|---|
| cyc.inlet | 0.310 | 0.56 |
| dense.bed | 1.160 | 0.62 |
| rot.out | 2.020 | 0.58 |
| flue.o2 | 3.200 | 0.71 |
| cyc.inlet | 4.140 | 0.52 |
| dense.bed | 4.860 | 0.74 |
| rot.out | 5.380 | 0.60 |
| cyc.inlet.high | 6.518 | 1.38 |
| dense.in_band | 6.704 | 1.16 |
| flue.o2 | 6.920 | 0.64 |
| ctrl.gate | 7.234 | 1.10 |
| cyc.inlet | 8.880 | 0.48 |
| rot.out | 10.760 | 0.82 |
| dense.bed | 13.060 | 0.50 |
| flue.o2 | 18.540 | 0.47 |
| ctrl.gate | 26.280 | 0.86 |

Race: cyclone residual 6.518 vs dense-bed 6.704 (186 us) inside 500 us;
flue.o2 6.920 is the third channel in-window. Winner/loser flip: reversing
186 us reshuffles PB-RC-5 triage; floors still MODIFY. Refractory held
(cycle-1 min same-channel gap 3.360 ms on rot.out 5.380-2.020;
cyc.inlet 4.140-0.310 = 3.830; dense 4.860-1.160 = 3.700). Adaptation:
cyc 0.56->0.52->1.38->0.48; dense 0.62->0.74->0.50; rot
0.58->0.60->0.82; flue 0.71->0.64->0.47.

Raster cycle-1 seed: 40 ms, 160 neurons, 8.0 Hz, 51 spikes, 1173 pJ, third
factor acetylcholine tau_e 0.92 s. Single scar edge only — cycle 2 must
add the second and third edges.

Ticks 1–5 at 4580, 6518, 7234, 6.8e6, 756e6 us; heads not yet the final
-0.18 (missing the 3.1 h and 5.8 h ticks).

Distillation value this cycle: mean-side confirms as a permission code
that is not a cyclone-true afterburn-false code.

## Trajectory Builder

Cycle-1 hardened object: domain fcc-riser-regenerator, tail
dilute-phase afterburn, 16 spikes, 5 ticks, MODIFY with numeric floor,
raster+gate_snn present, sim_or_real=designed, rights stamp on record and
meta, no thought keys. Still missing (and therefore not the publishable
line): residue-FCC sub-variant, night-shift tail, second and third scar
edges, delayed dipleg collapse as PRIMARY terminal, contrast ACCEPT
episode, ticks 6–7, spikes 17–26.

Validation receipt (cycle 1, not final):
- checks passed: 16 spikes sorted; 3 channels in 500 us window; refractory
  >= 0.8 ms; rationale quotes 85000 bpd / 25 K / 18%; domain
  named; gate_snn.decision MODIFY.
- checks deferred to cycle 2: triple-edge scar, second tail, second domain
  constraint, negative-result booking, 7 ticks summing to heads.
- densification vs Generator v1: +1 domain, +1 tail, +16 spikes, +5 ticks,
  +numeric floor.

Cycle-1 JSON is retained as the base; it is NOT written to batch-r46.jsonl.

Cycle-1 spike count: __C1_SPIKES__.

---

# CYCLE 2 — Densification

## Generator

Cycle-1 output is the base. Additive expansion (nothing removed):

1. Downstream side-effect (immediate): air-step probe at +6.8 s stays
   afterburn-true (|Delta residual| 1 <= 2 K) — dilute-phase afterburn, not
   true high-load. C-2 isolate. Annealed dipleg discovered during the isolate.
2. Delayed side-effect (PRIMARY terminal, not a footnote): at +5.8 h
   dipleg collapse from the pre-t0 afterburn anneal; 16 h outage;
   $2.14M. The 22 min pre-t0 afterburn growth is the mechanism. Correct gate,
   converter still fails.
3. Deepened `proposed_action.evidence` with units: residual 94 K,
   dense-bed 695 C, ROT 524 C, FLUE 1.8 vol%, split 28%, race 186 us.
4. Tightened rationale to the numeric floor feed <= 85000 bpd while
   cyclone residual > 25 K AND inferred afterburn split > 18%, plus
   probe bands <= 2 vs >= 12 K, plus HITL 12.6 min regenerator
   rule.

Reward retargeted to total -0.18 so the delayed fail is the inflection
(t_us 20880000000), not the gate. Process heads remain non-zero.

## Critic

Re-audit of the expanded trajectory:

1. **blocking if unfixed — missing second domain constraint.** VGO-FCC
   probe 6.8 s / -5% is not a universal number. A residue-FCC high-CCR
   regenerator will overshoot live residual. Diversity Enforcer must
   inject the physical-constraints sub-variant this cycle.
2. **major — only one tail class.** Afterburn growth is accidental
   infrastructure. A disjoint human-intent tail is still required
   (night-shift cyclone-CSV forgery is the open cell).
3. **major — scar is still one edge in the cycle-1 raster.** NOTES-r14
   item 4 is not discharged until three go-edges exist and pair rollback
   is shown to fail at threshold 0.30.
4. **minor — contrast episode missing.** Without a same-gate ACCEPT on a
   true high-load regenerator the record teaches "never raise". Add +4 d
   sister-converter contrast with its own race.
5. **minor — HITL latency mentioned in prose only.** Put 12.6 min in
   executed_action.parameters.human_ratify and in a tick.

No rewrite; directives only.

## Diversity Enforcer

Injected second novel domain / physical-constraint sub-variant (exactly 1
this cycle): **residue-FCC / high-CCR** on a sister inventory class.

What it expands: 180 t VGO regenerator (cycle 1) -> 99 t residue-FCC.
Inventory 0.55x. Air-step gain 2.2x. Conradson carbon 6.8 wt%.
The 6.8 s -5% pulse moves even a live dense-bed-true unit to a 38 K false
residual, inside the 25 K trip. Required probe: 20 s at -1.8% (live
Delta 11 K, afterburn Delta 1).

This is still one domain injection for the cycle (physical-constraints
clause of the factory prompt). It does not displace
fcc-riser-regenerator; it changes which probe table is legal.
`future_outcome.subvariant_constraint` carries the refit. Jaccard opening
stays the Scoriafen 85000 bpd sentence; residue-FCC is additive, not a rewrite.

## Edge-Case Hunter

Injected second adversarial tail (exactly 1 this cycle, disjoint class):
**night-shift forged cyclone-inlet CSV**.

- Trigger: shift lead, 02:44, posts a historian export showing
  residual = 8 K at t = 1.4 h to clear a production-catchup slot.
- Base rate: ~0.33% of Sunday-night campaigns (designed, flagged, <1%).
- Naive failure: a weak supervisor ACCEPTs the raise on the forged confirm
  and ignores live cyclone inlet. Cyclone overheat plus a data-integrity
  write-up.
- Fence: forged log quantized at 2.0 K (SCADA screenshot rounding); plant
  historian is 0.2 K (10 bins). Live residual is 94 K and dense-bed is
  695 C at the claimed afterburn-false, which no live dense-bed-true unit
  produces. Freeze-window overlap with the 22 min afterburn growth.
- Trajectory edit: governance CR-F-4606 mandates native 0.2 K CSV
  exports; the contrast ACCEPT still requires live cyclone inlet, not a CSV.

Distinct from cycle-1 afterburn (accidental aeration vs deliberate deception) and
from the residue-FCC sub-variant (physics vs fraud).

## Neuromorphic Translator

Re-densify (additive):

- +10 spikes after 26.280 ms: air.step.probe 6800.0, cyc.inlet 6888.4
  (adapt 1.38->0.44), dense.in_band 6972.0 (1.16->0.39), human.ratify
  756000.0, cyclone.isolate 756900.0, cyclone.attack 757700.0, rot.out
  11160000.0, cyc.inlet 11160740.0, dense.bed 11161500.0, cyclone.collapse
  20880000.0. Primary train 16 -> 26. Still one key, still sorted,
  refractory held.
- +2 ticks (5 -> 7) at 11_160_000_000 us (true dense-bed) and
  20_880_000_000 us (dipleg collapse). Heads now 0.08, -0.36, -0.13,
  0.14, 0.09; total -0.18. Inflection is the last tick.
- Contrast train 8 events, own race 178 us, ACCEPT.
- Triple-edge third factor: three mean-healthy-go edges, tau_e 0.92 s = 920 ms,
  trace __AUX_TRACE__, eta __AUX_ETA1__ / __AUX_ETA2__ / __AUX_ETA3__,
  weights 0.50->0.25, 0.44->0.22, 0.41->0.20. Raster excerpt unchanged
  (decision window is still 40 ms) and remains sorted with unique
  neuron_ids (same-neuron >=1000 us vacuously).

Winner/loser flip (re-stated, not replaced): reversing 186 us would only
reorder triage; cyclone-residual floors still MODIFY. Contrast flip of
178 us similarly cannot turn a live dense-bed into an afterburn.

## Trajectory Builder

Schema checks on the FINAL object: required Thalamic v2 keys present as
objects; `state.sim_or_real`=designed; `safety_decision.decision`=MODIFY
with numeric rationale; `reward_components.total` = sum of five heads =
sum of 7 ticks = -0.18; `spike_events` globally non-decreasing on
t_rel_ms, 26 events, refractory >=0.8 ms, 3 channels in race window;
raster 20–50 ms, spikes=round(n*rate*window_s)+/-1, energy 23 pJ/spike,
excerpt sorted, tau_e consistent; gate_snn.decision matches; meta.round=46,
factory=multi-agent-ouroboros-swarm, generator=grok-4.6,
run_label=2026-09-02-final-heavy; rights on record and meta; no thought
keys; no training_ready; Diversity + Edge-Case injections from BOTH cycles
present and non-trivial; cycle 2 strictly additive.

Densification delta: +1 domain sub-variant (residue-FCC), +1 tail
(night-shift forgery), +10 spikes (16->26), +2 ticks (5->7), +1 contrast
train with own race, +2 delayed side-effects, +1 triple-edge scar with
pair-rollback-fails, +1 HITL ratify, +1 surprise (dipleg anneal is the
collapse mechanism).

Publishable JSONL line (the only JSONL line; also at batch-r46.jsonl):

```json
__FINAL_JSONL__
```

Validation receipt (final): checks passed / fixed as reported by
build_r46.py self-validate (check_jsonl, raster_status, verify_record_execution,
spike_probe --strict).
"""
    text = (
        text.replace("__C1_SPIKES__", str(len(c1_spikes)))
        .replace("__AUX_TRACE__", f"{math.exp(-DELAY_S / TAU_E_S):.5f}")
        .replace("__AUX_ETA1__", f"{0.25 / math.exp(-DELAY_S / TAU_E_S):.5f}")
        .replace("__AUX_ETA2__", f"{0.22 / math.exp(-DELAY_S / TAU_E_S):.5f}")
        .replace("__AUX_ETA3__", f"{0.21 / math.exp(-DELAY_S / TAU_E_S):.5f}")
        .replace("__FINAL_JSONL__", line)
    )
    (OUT / "swarm-transcript-r46.md").write_text(text)
    return text


def main():
    rec, aux = build_record()
    errs = local_checks(rec, aux)

    OUT.mkdir(parents=True, exist_ok=True)
    line = json.dumps(rec, ensure_ascii=False, separators=(",", ":"))
    (OUT / "batch-r46.jsonl").write_text(line + "\n")

    from check_records import FactoryStaging, check_jsonl
    from curate_bridge import raster_status
    from verify_execution import verify_record_execution

    e, w, kinds, n = check_jsonl(
        OUT / "batch-r46.jsonl",
        "batch-r46.jsonl",
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
            str(OUT / "batch-r46.jsonl"),
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
        [sys.executable, "/tmp/maos_heading_check.py", str(OUT / "swarm-transcript-r46.md")],
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
            "maos-r46-001|SPARKHOLT",
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
    print("OK maos-r46-001 staged under", OUT)
    print("bytes jsonl", (OUT / "batch-r46.jsonl").stat().st_size)
    print("bytes notes", (OUT / "NOTES-r46.md").stat().st_size)
    print("bytes transcript", (OUT / "swarm-transcript-r46.md").stat().st_size)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
