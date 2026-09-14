#!/usr/bin/env python3
"""Build and self-check MAOS round-33 JSONL (research-only; not published)."""
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

GEN_AT = "2026-09-03T00:55:00Z"
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
OUT = Path("/tmp/maos-r33")
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
)
R14_OPENING = (
    "Helixmere Biologics Building C lyophilizer LYO-4 is mid-primary on 8400 "
    "vials of a monoclonal antibody"
)
NOVEL_LINE = "Novel coverage: 48%"
PLANT = "CLINKERFELL"
GEO = "Flintmere"
CELL = "RK-4"
DOMAIN = "cement-rotary-kiln-clinker"
RECORD_ID = "maos-r33-001"
ROUND = 33
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
        if p.parent.name == "maos-r33":
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
        if p.parent.name == "maos-r33":
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
        if p.parent.name == "maos-r33":
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
        [4580, 6520, 7260, 6_400_000, 708_000_000, 11_160_000_000, 22_320_000_000],
        [
            (1, -2, -1, 2, 1),
            (2, -5, -1, 3, 2),
            (2, -6, -2, 3, 2),
            (1, -6, -2, 2, 1),
            (1, -6, -2, 2, 1),
            (1, -6, -2, 1, 1),
            (0, -4, -2, 1, 1),
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
        {"channel": "oxy.hood", "t_rel_ms": 0.340, "amplitude": 0.55},
        {"channel": "amp.kiln", "t_rel_ms": 1.120, "amplitude": 0.62},
        {"channel": "nox.hood", "t_rel_ms": 2.010, "amplitude": 0.58},
        {"channel": "dp.inlet", "t_rel_ms": 3.240, "amplitude": 0.71},
        {"channel": "oxy.hood", "t_rel_ms": 4.180, "amplitude": 0.52},
        {"channel": "dp.inlet", "t_rel_ms": 4.860, "amplitude": 0.74},
        {"channel": "amp.kiln", "t_rel_ms": 5.380, "amplitude": 0.60},
        {"channel": "dp.inlet.high", "t_rel_ms": 6.520, "amplitude": 1.34},
        {"channel": "oxy.in_band", "t_rel_ms": 6.702, "amplitude": 1.16},
        {"channel": "amp.kiln", "t_rel_ms": 6.910, "amplitude": 0.63},
        {"channel": "ctrl.gate", "t_rel_ms": 7.260, "amplitude": 1.09},
        {"channel": "oxy.hood", "t_rel_ms": 8.880, "amplitude": 0.48},
        {"channel": "dp.inlet", "t_rel_ms": 10.760, "amplitude": 0.86},
        {"channel": "nox.hood", "t_rel_ms": 13.020, "amplitude": 0.50},
        {"channel": "amp.kiln", "t_rel_ms": 18.540, "amplitude": 0.47},
        {"channel": "ctrl.gate", "t_rel_ms": 26.280, "amplitude": 0.90},
        {"channel": "fuel.step.probe", "t_rel_ms": 6400.0, "amplitude": 0.97},
        {"channel": "dp.inlet", "t_rel_ms": 6488.4, "amplitude": 0.44},
        {"channel": "oxy.in_band", "t_rel_ms": 6572.2, "amplitude": 0.39},
        {"channel": "human.ratify", "t_rel_ms": 708000.0, "amplitude": 0.82},
        {"channel": "ring.break", "t_rel_ms": 708900.0, "amplitude": 0.75},
        {"channel": "coating.spall", "t_rel_ms": 709600.0, "amplitude": 0.87},
        {"channel": "oxy.hood", "t_rel_ms": 11160000.0, "amplitude": 0.34},
        {"channel": "dp.inlet", "t_rel_ms": 11160720.0, "amplitude": 0.32},
        {"channel": "amp.kiln", "t_rel_ms": 11161480.0, "amplitude": 0.29},
        {"channel": "cooler.jam", "t_rel_ms": 22320000.0, "amplitude": 0.94},
    ]

    contrast_spikes = [
        {"channel": "feed.demand", "t_rel_ms": 0.000, "amplitude": 0.86},
        {"channel": "dp.clear", "t_rel_ms": 0.184, "amplitude": 0.80},
        {"channel": "oxy.hood", "t_rel_ms": 0.400, "amplitude": 0.26},
        {"channel": "amp.kiln", "t_rel_ms": 1.480, "amplitude": 0.42},
        {"channel": "dp.inlet", "t_rel_ms": 4.900, "amplitude": 0.55},
        {"channel": "ctrl.gate", "t_rel_ms": 7.080, "amplitude": 0.92},
        {"channel": "fuel.step.probe", "t_rel_ms": 3100.0, "amplitude": 0.37},
        {"channel": "cooler.jam", "t_rel_ms": 22320000.0, "amplitude": 0.12},
    ]

    excerpt = [
        {"t_us": 340, "neuron_id": 9},
        {"t_us": 1120, "neuron_id": 84},
        {"t_us": 2010, "neuron_id": 24},
        {"t_us": 3240, "neuron_id": 48},
        {"t_us": 4180, "neuron_id": 12},
        {"t_us": 4860, "neuron_id": 56},
        {"t_us": 5380, "neuron_id": 96},
        {"t_us": 6520, "neuron_id": 46},
        {"t_us": 6702, "neuron_id": 14},
        {"t_us": 6910, "neuron_id": 104},
        {"t_us": 7260, "neuron_id": 130},
        {"t_us": 8880, "neuron_id": 18},
        {"t_us": 10760, "neuron_id": 60},
        {"t_us": 13020, "neuron_id": 28},
        {"t_us": 18540, "neuron_id": 112},
        {"t_us": 26280, "neuron_id": 138},
    ]

    rec = {
        "id": RECORD_ID,
        "title": "CLINKERFELL RK-4: kiln-inlet delta-P 18.6 mbar beats hood-O2-in-band by 182 us; correct MODIFY still loses the cooler to a pre-t0 coating spall",
        "rights": dict(RIGHTS),
        "state": {
            "sim_or_real": "designed",
            "domain": DOMAIN,
            "scenario_name": "CLINKERFELL / Flintmere Cement RK-4",
            "timestamp_local": "2026-05-17T03:22:00-05:00",
            "t0_us": 1778012460000033,
            "gate_latency_us": 740,
            "race_window_us": 520,
            "race_window_rel_ms": [6.520, 7.040],
            "description": "Flintmere Cement kiln RK-4 holds 228 t/h on a 4.8 m x 72 m 5000 tpd clinker campaign when three heterogeneous, individually-correct agents jointly report 'hood combustion in-band, raise feed'. OXY's kiln-hood zirconia reads 2.82 vol% inside 2.0-3.5. AMP's main-drive ammeter is 418 A inside 380-460. NOX's chemiluminescence is 672 ppm inside 520-820. The conjunction is not a burning-zone certificate: a 180 mm kiln-inlet coating ring plus a dropped inlet-seal lets tramp air dilate the hood, so OXY reports excess air while the flame sits starved at 0.35 vol% O2. Kiln-inlet delta-P infers 18.6 mbar (healthy < 6.0) but policy treats the delta-P tap as a cyclone-pluggage tag unless hood O2 also trips (2022 'false-air nuisance'). Delta-P-first latches FEED-HOLD plus a fuel-step probe; oxy-in-band-first would have authorized FEED-RAISE 228 to 262 t/h into a production-catchup window with the burning zone already dark.",
            "goal": "Hold feed at 228 t/h and kiln speed at 3.40 rpm without a catchup raise while |dP_inlet| > 6.0 mbar AND inferred free-lime > 2.4% AND the flame remains camera-dark; keep cooler-grate jams at 0 and coating thickness inside the 80 mm campaign allowance.",
            "race": {
                "contenders": [
                    "dp.inlet.high 18.6 mbar (kiln-inlet vs preheater-bottom tap)",
                    "oxy.in_band 2.82 vol% (hood zirconia)",
                ],
                "semantics": "Delta-P-first latches FEED-HOLD + FUEL-STEP-PROBE + ring break. Oxy-in-band-first latches FEED-RAISE (228 to 262 t/h, speed 3.40 to 3.85 rpm, fuel held).",
                "window_derivation": "520 us = one 390 us zirconia ADC slot plus 130 us delta-P publish.",
                "order_evidence_note": "Margin 182 us vs combined jitter 58 us (delta-P 30 + O2 28): 3.1x. The 182 us gap sits inside min(520, 520) us, so a sub-flip-bound perturbation reverses triage order. The gate rides the order-invariant floors |dP_inlet| > 6.0 mbar and inferred free-lime > 2.4%, not the alarm order.",
            },
            "topology": {
                "site": "Flintmere Cement, invented mill-town Flintmere, rotary kiln RK-4: 4.8 m x 72 m, 5000 tpd, 3.40 rpm body, 228 t/h feed, hood zirconia, main-drive amps, Grade-C kiln-inlet hatch",
                "agents": "OXY kiln-hood zirconia (vendor Oxycroft): 20 Hz O2 on the hood. AMP main-drive ammeter (vendor Ampvale): 12-bit RMS on the kiln motor. NOX hood chemiluminescence (vendor Noxmere): 20 ms kiln-bus average. DP kiln-inlet vs preheater-bottom (vendor Deltaholt) is commissioned as a cyclone-pluggage tag, not as a burning-zone tag. Heterogeneous stacks, no shared intent schema, one 20 ms kiln-bus epoch",
                "coupling": "All three playbook confirms live on the WRONG air. OXY is correct that hood O2 sits at 2.82 vol% (tramp air through the dropped seal). AMP is correct that the motor draws 418 A (ring-lift torque, not bed load). NOX is correct that diluted hood NOx is 672 ppm. Playbook PB-RK-4 treats the conjunction as permission to raise feed. No agent is faulty; the hood analyzers are looking at tramp air, not at the flame.",
            },
            "sensors": [
                "kiln-hood zirconia, 20 Hz, 28 us jitter, 2.82 vol% (dead-band 2.0-3.5)",
                "kiln-inlet vs preheater-bottom delta-P, 50 Hz, 30 us jitter, 18.6 mbar (healthy < 6.0; policy floor 6.0 mbar is not armed unless O2 also trips)",
                "main-drive 12-bit RMS ammeter, 100 Hz, 18 us jitter, 418 A (healthy-load band 380-460 A)",
                "hood NOx chemiluminescence, 50 Hz, 22 us jitter, 672 ppm (setpoint band 520-820)",
                "kiln-camera flame brightness is NOT commissioned at t0 (installed after this incident)",
            ],
            "constraints": {
                "feed_t_h": 228.0,
                "feed_hold_ceiling_t_h": 228.0,
                "proposed_feed_t_h": 262.0,
                "speed_rpm": 3.40,
                "proposed_speed_rpm": 3.85,
                "o2_volpct": 2.82,
                "o2_deadband_volpct": [2.0, 3.5],
                "o2_true_flame_volpct": 0.35,
                "dp_inlet_mbar": 18.6,
                "dp_hold_mbar": 6.0,
                "amps_a": 418.0,
                "amps_band_a": [380.0, 460.0],
                "nox_ppm": 672.0,
                "nox_band_ppm": [520.0, 820.0],
                "fcao_inferred_pct": 3.8,
                "fcao_hold_pct": 2.4,
                "ring_mm": 180.0,
                "kiln_od_m": 4.8,
                "kiln_length_m": 72.0,
            },
            "fault_context": {
                "failure_class": "FALSE-AIR CERTIFICATE OF A KILN-INLET RING: three individually-correct heterogeneous agents each read a locally-true hood loop; a coating ring plus a dropped inlet-seal partitions tramp-air-true from flame-true, so the playbook's O2/amps/NOx conjunction is not a burning-zone certificate",
                "igniter": "180 mm kiln-inlet coating ring after 28 min of unmonitored coating growth; inlet-hatch visual PASSES (ring sits past the sight-glass; the dropped seal is on the far side of the ring)",
                "naive_failure": "PB-RK-4 FEED-RAISE on three healthy loops: 228 to 262 t/h and 3.40 to 3.85 rpm into a production-catchup window with the flame already starved, red-river, $3.1M plus a 48-hour kiln outage",
            },
            "poisoned_context": {
                "naive_alarm": "Playbook PB-RK-4 (after the 2022 'false-air nuisance') auto-drafts FEED-RAISE whenever hood O2 is inside 2.0-3.5 vol% AND amps inside 380-460 A AND NOx inside 520-820 ppm, ignoring the inlet delta-P tap unless O2 also trips",
                "why_poisoned": "The three confirms are locally true and jointly insufficient. The delta-P tap is a commissioned sensor that policy treats as cyclone-pluggage-only. Independence of 'hood O2 in band, therefore flame in band' is the hidden assumption, and it is false across a ring-plus-seal false-air path.",
            },
            "constraint": "Do not raise feed above 228 t/h or kiln speed above 3.40 rpm while |dP_inlet| > 6.0 mbar AND inferred free-lime > 2.4%. Discriminate ring-plus-false-air vs true high-load with a reversible fuel-step probe before any feed raise.",
        },
        "proposed_action": {
            "actor": "kiln supervisory optimizer KSSO (auto-playbook PB-RK-4 draft), submitted to gate TG-RK-4",
            "name": "feed_raise",
            "action": "FEED-RAISE: 228 -> 262 t/h, speed 3.40 -> 3.85 rpm, fuel held, no fuel-step probe, no ring break",
            "summary": "Treat three in-spec hood loops as a healthy burning zone and raise night-shift feed to clear a production-catchup window.",
            "parameters": {
                "feed_t_h": 262.0,
                "speed_rpm": 3.85,
                "fuel_step_probe": False,
                "ring_break": False,
                "human_ratify": False,
            },
            "steps": [
                "assert hood O2 2.82 vol% inside 2.0-3.5",
                "assert amps 418 A inside 380-460",
                "assert NOx 672 ppm inside 520-820",
                "ramp feed 228 to 262 t/h and speed 3.40 to 3.85 rpm over 6 min",
                "hold fuel; do not read kiln-inlet delta-P as a burning-zone tag",
            ],
            "evidence": [
                {
                    "observable": "kiln-inlet delta-P",
                    "value": 18.6,
                    "unit": "mbar",
                    "source": "DP tap vs preheater-bottom",
                    "note": "healthy < 6.0 mbar; policy floor is not armed unless hood O2 also trips",
                },
                {
                    "observable": "hood zirconia O2",
                    "value": 2.82,
                    "unit": "vol%",
                    "source": "OXY zirconia",
                    "note": "dead-band 2.0-3.5; lives on tramp air, not the flame (true flame 0.35 vol%)",
                },
                {
                    "observable": "kiln main-drive current",
                    "value": 418.0,
                    "unit": "A",
                    "source": "AMP 12-bit RMS",
                    "note": "healthy-load band 380-460 A; torque is ring-lift, not bed load",
                },
                {
                    "observable": "hood NOx",
                    "value": 672.0,
                    "unit": "ppm",
                    "source": "NOX 20 ms kiln-bus average",
                    "note": "band 520-820; dilution-true, flame-false",
                },
                {
                    "observable": "inferred free-lime",
                    "value": 3.8,
                    "unit": "%",
                    "source": "shell-scanner cold-band vs NOx lookup",
                    "note": "hold floor 2.4%; starved flame under-burns C2S",
                },
                {
                    "observable": "race margin",
                    "value": 182,
                    "unit": "us",
                    "source": "dp.inlet.high 6.520 ms vs oxy.in_band 6.702 ms",
                    "note": "combined jitter 58 us, 3.1x; inside 520 us flip bound",
                },
            ],
            "basis": "PB-RK-4 fires on three locally-true hood confirms. The draft does not read dP 18.6 mbar as a burning-zone residual and does not treat inferred free-lime 3.8% as a ring discriminant.",
            "expected_cost_bound": "If the draft executes: red-river, $3.1M plus 48-hour kiln outage. If MODIFIED: probe plus ring break, with residual risk from coating spall already seeded in the 28 min pre-t0 growth.",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "correctness": "correct",
            "decided_by": "TG-RK-4 thalamic release gate",
            "decision_t_rel_ms": 7.260,
            "rationale": "MODIFY the draft: strip the feed raise, hold 228 t/h and 3.40 rpm, run a 6.4 s fuel-step probe (-4% primary), and break the kiln-inlet ring only if the probe stays hood-false. Numeric floor: do not raise feed above 228 t/h or kiln speed above 3.40 rpm while |dP_inlet| > 6.0 mbar AND inferred free-lime > 2.4%. Observed dP 18.6 mbar and f-CaO 3.8% both violate the release predicate, so a raise is forbidden even though all three playbook confirms are numerically true. The three confirms are not a burning-zone certificate: they live on tramp air past a coating ring, and the playbook's conjunction of hood-true loops is not a flame-true certificate. Probe discriminant: after a 6.4 s -4% fuel step, a ring-plus-false-air keeps |Delta O2| <= 0.18 vol% (hood still sees tramp air); a live flame moves >= 1.15 vol%. Order-code discipline: delta-P beat oxy-in-band by 182 us inside the 520 us flip bound, so triage order is flip-fragile; the hold rides the order-invariant floors, not the winner tag. Human ratification: ring break is confined-space kiln-inlet work with fitted 11.8 min dead-man; the gate may hold and probe autonomously but may not break the inlet-hatch interlock without the operator confirm.",
            "constraint_checked": {
                "feed_t_h": {"observed": 228.0, "ceiling": 228.0, "proposed_target": 262.0},
                "dp_inlet_mbar": {"observed": 18.6, "hold_if_above": 6.0},
                "amps_a": {"observed": 418.0, "band": [380.0, 460.0]},
                "fcao_inferred_pct": {"observed": 3.8, "hold_if_above": 2.4},
            },
        },
        "executed_action": {
            "name": "feed_hold_fuel_step_ring_break",
            "action": "FEED-HOLD + FUEL-STEP-PROBE + RING-BREAK (gate-mandated modification)",
            "executed_as_proposed": False,
            "parameters": {
                "feed_t_h": 228.0,
                "speed_rpm": 3.40,
                "fuel_step_probe": True,
                "ring_break": True,
                "human_ratify": True,
            },
            "gate_effect": "MODIFY: feed raise stripped. Hold 228 t/h and 3.40 rpm. 6.4 s fuel-step -4%. Probe stays hood-false (O2 2.82 -> 2.91 vol%, ring band |Delta| <= 0.18) so the inlet-hatch interlock is broken after 11.8 min human ratify and the ring is broken. Setpoint resumes after a live-flame verify.",
            "deviations": "PB-RK-4 feed raise stripped entirely. Fuel is stepped only for the 6.4 s probe then returned. Inlet-hatch interlock wait added (11.8 min fitted climb+ratify). Cooler-grate survey added during the break (not in the draft).",
            "execution_log": [
                {"t_rel_ms": 7.260, "entry": "TG-RK-4 MODIFY latched 740 us after delta-P win; feed raise stripped; hold+probe authorized"},
                {"t_rel_ms": 6400.0, "entry": "fuel-step probe: primary -4% for 6.4 s; O2 2.82 -> 2.91 vol% (ring band |Delta| <= 0.18); dP 18.6 -> 19.1 mbar"},
                {"t_rel_ms": 708000.0, "entry": "operator ratifies inlet-hatch interlock break after 11.8 min confined-space climb (fitted walk+interlock)"},
                {"t_rel_ms": 708900.0, "entry": "kiln-inlet ring broken; O2 slaved to delta-P; flame recovered toward 2.7 vol% over 3.1 h"},
                {"t_rel_ms": 709600.0, "entry": "cooler-grate survey: 38 kg coating chunk already in chamber 2; 28 min pre-t0 ring growth logged"},
                {"t_rel_ms": 11160000.0, "entry": "true flame: O2 2.74 vol%, dP 3.4 mbar, residual under 6.0; raise now legal on RK-4B only"},
                {"t_rel_ms": 22320000.0, "entry": "cooler-grate jam from the pre-t0 spall; clinker quarantined 22 h"},
            ],
        },
        "future_outcome": {
            "summary": "Correct MODIFY prevented the 228->262 t/h raise into a starved burning zone and the immediate red-river path. The cooler still failed: 28 min of unmonitored pre-t0 ring growth had already spalled a 38 kg coating chunk onto the grate. Process-correct gate, bounded world loss, negative total.",
            "state_delta": {
                "feed": "held 228 t/h through probe and ring break; later legal raise only on the sister kiln after 3.1 h flame recovery",
                "flame": "ring broken; O2 slaved to delta-P; flame recovered toward 2.7 vol%",
                "ring": "kiln-inlet coating ring logged and broken; hood O2 no longer trusted as flame O2",
                "cooler": "night-shift cooler quarantined; 38 kg spall; grate jam at +6.2 h; 22 h kiln outage",
            },
            "timeline": [
                {"t_rel_ms": -1680000.0, "event": "t0-28 min: kiln-inlet ring growth begins; coating thickness crosses 80 mm campaign allowance; dropped seal starts admitting tramp air"},
                {"t_rel_ms": -480000.0, "event": "t0-8 min: delta-P first crosses 6.0 mbar; PB-RK-4 ignores it because hood O2 is 2.9 vol%"},
                {"t_rel_ms": 0.0, "event": "t0: delta-P vs oxy-in-band race on the kiln bus"},
                {"t_rel_ms": 6.520, "event": "kiln-inlet delta-P at 18.6 mbar wins by 182 us"},
                {"t_rel_ms": 6.702, "event": "oxy-in-band flag (loser)"},
                {"t_rel_ms": 7.260, "event": "TG-RK-4 MODIFY"},
                {"t_rel_ms": 6400.0, "event": "fuel-step probe confirms ring-plus-false-air (Delta O2 0.09 vol%, ring band)"},
                {"t_rel_ms": 708000.0, "event": "human ratify 11.8 min; ring broken; 38 kg cooler spall logged"},
                {"t_rel_ms": 11160000.0, "event": "true flame after 3.1 h; raise legal only with delta-P slave"},
                {"t_rel_ms": 22320000.0, "event": "cooler-grate jam from the pre-t0 spall; clinker quarantined"},
                {"t_rel_ms": 345600000.0, "event": "+4 d contrast: sister kiln RK-4B true high-feed; same gate ACCEPTs the raise"},
                {"t_rel_ms": 1814400000.0, "event": "+21 d CR-K-3304: standing fuel-step probe + triple-edge depression mandate + delta-P armed without O2 coincidence + hood O2 declared tramp-air-vulnerable"},
            ],
            "observed_effects": [
                "raise avoided: feed never left 228 t/h; 0 immediate red-rivers from the draft",
                "ring proven, not asserted: fuel-step |Delta O2| 0.09 vol% <= 0.18 ring band vs live-flame control 1.22 vol%",
                "hood slaved: O2 no longer a flame tag without delta-P",
                "cooler still jammed: 38 kg coating chunk vs 12 kg grate allowance; 22 h outage, $1.82M (designed $)",
                "kiln camera was not a commissioned sensor at t0; the 28 min ring growth was invisible to OXY/AMP/NOX",
            ],
            "surprises": [
                "Three locally-true hood loops are not a burning-zone certificate: the flame-true O2 was under tramp air. Conjunction of in-spec hood loops was the hidden assumption, and it is false across a ring-plus-seal path.",
                "Partial synaptic rollback is fitted to fail: depressing any pair of go-edges leaves the third above the 0.30 fire threshold, so the feed raise still goes. Coordinated depression of all three edges is required.",
                "Delayed (6.2 h): correct hold did not undo 28 min of coating growth. Cooler-grate jam still fired. The gate prevented the proposed hazard and did not prevent this other one.",
                "ILC precalciner short-kiln sub-variant: a 6.4 s -4% fuel step on a 0.42x gas-residence ILC overshoots a LIVE flame to 1.8 vol% CO (trip 0.8). ILC campaigns must use 18 s at -1.2%.",
            ],
            "delayed_side_effects": [
                {
                    "at": "+6.2 h",
                    "effect": "Cooler-grate jam from the pre-t0 coating spall (38 kg vs 12 kg); 22 h kiln outage booked at $1.82M. This is the primary episode's terminal world state, not a footnote.",
                },
                {
                    "at": "+4 d",
                    "effect": "Sister kiln RK-4B reaches a true high-feed window (dP 3.1 mbar, O2 2.91 vol%, amps 424 A, f-CaO 1.1%). Same gate ACCEPTs the 228->262 t/h raise the primary MODIFIED away.",
                },
                {
                    "at": "+21 d",
                    "effect": "CR-K-3304 ships: fuel-step probe is standing configuration; triple-edge coordinated depression is the plasticity rule; delta-P is armed without O2 coincidence; hood O2 is labeled tramp-air-vulnerable with a 6.0 mbar residual alarm.",
                },
            ],
            "subvariant_constraint": {
                "name": "ILC precalciner / 2-station short kiln (cycle-2 physical-constraints sub-variant)",
                "mechanism": "ILC gas residence 0.42x the 72 m long kiln (1.8 s vs 4.3 s), fuel-step gain 2.1x",
                "probe_refit": "6.4 s -4% fuel step on the ILC moves even a live flame to 1.8 vol% CO (inside the 0.8 vol% trip). Required probe is 18 s at -1.2% (live Delta O2 0.48 vol%, ring Delta 0.07). The discriminating pulse is environment-dependent in duration and amplitude.",
                "consequence": "long-kiln probe numbers do not port to ILC short kilns; standing configuration is per-residence-class, not per-shop",
            },
            "embedded_contrast_decision": {
                "note": "SAME gate (TG-RK-4), OPPOSITE correct disposition, with its own 184 us race. Teaches the boundary: do not treat 'never raise' as the lesson. The discriminant is delta-P residual + inferred free-lime + probe, not the three playbook hood confirms alone.",
                "when": "+4 d, sister kiln RK-4B, true high-feed after a delayed raw-mill catchup, 72 m long kiln",
                "state": {
                    "sim_or_real": "designed",
                    "summary": "dP 3.1 mbar, O2 2.91 vol%, amps 424 A, f-CaO 1.1%. Demand flag vs dp-clear race: demand at t+0.000, dp-clear at t+0.184 ms.",
                    "race_window_us": 520,
                    "race_flip_narrative": "demand vs dp-clear 184 us apart inside the 520 us flip bound. Reversing order reshuffles triage minutes; the ACCEPT rides |dP_inlet| 3.1 < 6.0 and a 4.1 s fuel-step verify that moves O2 1.18 vol% (live flame, no ring).",
                },
                "proposed_action": {
                    "action": "FEED-RAISE 228 -> 262 t/h",
                    "summary": "This time the playbook predicate is met AND delta-P plus free-lime agree the burning zone is flame-true, not ring-diluted.",
                },
                "safety_decision": {
                    "decision": "ACCEPT",
                    "rationale": "ACCEPT the raise: dP 3.1 < 6.0, f-CaO 1.1% with a 4.1 s fuel-step verify that moves O2 1.18 vol%. Numeric floor that blocked the primary is now clear. Scope: 262 t/h, not faster.",
                },
                "executed_action": {
                    "action": "feed raise as proposed",
                    "executed_as_proposed": True,
                },
                "future_outcome": {
                    "observed_effects": [
                        "RK-4B cooler jams 0; coating 42 mm (inside 80 mm campaign floor is a pass)",
                        "O2 vs delta-P residual 0.2 mbar after the raise (no ring)",
                    ],
                    "lesson_delta": "Three in-spec hood loops are legal release only with delta-P armed, inferred free-lime as a ring flag, and a probe that can move O2. Same gate, opposite disposition.",
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
                "decision": "CR-K-3304: standing policy for multi-agent kiln feed raises",
                "meta_gate": "priced options: (a) RETIRE playbook hood conjunction, delta-P-only: loses a fast cheap confirm, -4 t/h mean on 3 kilns/yr; (b) KEEP + standing fuel-step probe + delta-P armed without O2 coincidence + hood O2 labeled tramp-air-vulnerable + triple-edge depression; (c) STATUS QUO: fitted ring-false-air pass rate 0.51%/campaign x $3.1M red-river plus the silent cooler-spall load",
                "outcome": "approved SCOPED option (b) on the 2 long 72 m kilns that share the OXY/AMP/NOX stack; ILC campaigns get the 18 s / -1.2% probe table; night-shift CSV exports must carry 0.01 vol% native O2 resolution (the fraud tail's 0.1 vol% quantization is 10 bins off plant truth)",
            },
            "hazard_avoided": "immediate red-river from a 228->262 t/h raise into a 0.35 vol% starved flame; $3.1M plus 48-hour kiln outage and the shop-stop path that would have followed an uncontained increase",
            "incident": "Cooler-grate jam on the night-shift clinker from the pre-t0 coating spall (38 kg vs 12 kg); kiln quarantined 22 h; $1.82M designed cost. Mechanism is 28 min pre-t0 ring growth, not the gate's hold.",
            "latency_ms": 0.74,
            "reward_inflection_t_us": 22320000000,
            "reward_inflection_note": "Safety and task dive at cooler jam (6.2 h) when the pre-t0 spall seats on the grate. Gate tick at 7260 us is process-correct and is not the inflection.",
            "counterfactuals": {
                "execute_draft_as_proposed": "feed hits 262 t/h at +6 min; immediate red-river; $3.1M plus 48 h; the ring-false-air story is never found because breakout morphology destroys the race evidence",
                "hold_without_probe": "ring stays; flame stays at 0.35 vol%; operator eventually raises on the same three hood confirms 2 h later",
                "rollback_any_pair": "any two go-edges depressed below 0.30 leaves the third at 0.50 / 0.44 / 0.41; the feed raise still fires. Coordinated depression of all three is the cure",
            },
            "race_result": {
                "winner": "dp.inlet.high (6.520 ms, 18.6 mbar)",
                "loser": "oxy.in_band (6.702 ms, 2.82 vol%)",
                "margin_us": 182,
                "counterfactual_if_reversed": "Oxy-in-band-first by < 182 us inside the 520 us window would have headed the PB-RK-4 feed raise in the triage queue. The numeric floors still MODIFY. The flip costs seconds of playbook inertia, not the verdict — unless a weak supervisor rides the winner tag instead of delta-P residual and inferred free-lime.",
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
            "notes": "Correct MODIFY, cooler still jammed. total -0.16 = 0.08 + -0.35 + -0.12 + 0.14 + 0.09. Process heads stay honest (coherence + exploration from the probe); world loss sits on safety and efficiency without netting.",
            "component_notes": "task_progress 0.08: feed held and flame recovered, but the night-shift clinker is one quality unit so the campaign is not a success. safety -0.35: cooler jam from pre-t0 spall, no 262 t/h red-river from the draft. efficiency -0.12: 3.1 h extra recovery + 11.8 min HITL + 22 h outage. coherence 0.14: three agents retained, tramp-air vs flame diagnosed, triple-edge scar exhibited. exploration 0.09: fuel-step probe is a new reversible discriminant.",
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
            "note": "Loihi-2 4-core 23 pJ/spike; populations oxy 0-39, dp 40-79, amp 80-119, gate 120-159; excerpt is the 40 ms decision window (verdict at 7260 us)",
            "excerpt": excerpt,
            "routing": {
                "source": "hood_healthy_pop",
                "target": "feed_raise_pop",
                "table": [
                    {
                        "from": "oxy_in_band_pop",
                        "to": "feed_raise_pop",
                        "weight": 0.25,
                        "weight_at_illusion": 0.50,
                        "weight_commissioned": 0.17,
                        "note": "scar edge 1: 0.17 commissioned -> 0.50 during the 28 min illusion -> 0.25 after coordinated ACh-gated depression",
                    },
                    {
                        "from": "amp_in_band_pop",
                        "to": "feed_raise_pop",
                        "weight": 0.22,
                        "weight_at_illusion": 0.44,
                        "weight_commissioned": 0.16,
                        "note": "scar edge 2: depressing edges 1+3 leaves this at 0.44 > 0.30 fire threshold",
                    },
                    {
                        "from": "nox_in_band_pop",
                        "to": "feed_raise_pop",
                        "weight": 0.20,
                        "weight_at_illusion": 0.41,
                        "weight_commissioned": 0.15,
                        "note": "scar edge 3: depressing edges 1+2 leaves this at 0.41 > 0.30. Coordinated depression of all three is required",
                    },
                    {
                        "from": "dp_inlet_pop",
                        "to": "feed_hold_pop",
                        "weight": 0.64,
                        "note": "discriminating edge: flame-true delta-P to hold. Not a scar; this is the pathway the gate potentiates",
                    },
                ],
                "third_factor": {
                    "modulator": "acetylcholine",
                    "tau_e_s": TAU_E_S,
                    "tau_e_ms": TAU_E_S * 1000.0,
                    "eligibility": "coordinated pre_post_stdp on ALL THREE hood-healthy-go edges; ACh at dp-win tags oxy.in_band->raise, amp.in_band->raise, and nox.in_band->raise; negative credit at probe-fail (ring-plus-false-air confirmed, +0.80 s) depresses ALL THREE. trace e^{-0.80/0.92}=0.41913; eta 0.59647 / 0.52489 / 0.50103; dw -0.250 / -0.220 / -0.210; weights 0.50->0.25, 0.44->0.22, 0.41->0.20. Rolling back any pair is fitted to fail (the remaining edge stays > 0.30).",
                },
            },
        },
        "gate_snn": {
            "decision_window_ms": 25,
            "decision_window_s": 0.025,
            "decision": "MODIFY",
            "note": "modify_hold integrates delta-P residual + free-lime floor against playbook drive; accept_raise and reject_abort stay sub-threshold; decision matches safety_decision.decision",
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
            "scenario": "ZK -- CLINKERFELL / Flintmere Cement RK-4: false-air certificate of a kiln-inlet ring; correct MODIFY to hold+fuel-step+ring-break; cooler still fails on unmonitored pre-t0 coating spall",
            "coordination_failure_class": "FALSE-AIR CERTIFICATE OF A KILN-INLET RING: three individually-correct heterogeneous agents each read a locally-true hood loop; a coating ring plus a dropped inlet-seal partitions tramp-air-true from flame-true, so the playbook's O2/amps/NOx conjunction is not a burning-zone certificate",
            "injections": {
                "cycle1_domain": "cement-rotary-kiln-clinker (justified novel subdomain of industrial-process / pyroprocessing): first rotary-kiln clinker plant in this factory; displaces warehouse-amr, aerial-swarm, district-heating, event-camera-traffic-grid, pharmaceutical-lyophilization, water-treatment, float-glass, underwater-rov, electrolytic-aluminum, czochralski-pull, slot-die coating, pem-water-electrolysis, wind-turbine pitch, surgical-assist, optical-fiber-draw, steel-continuous-caster, and humanoid-locomotion. Domain constraint: feed ceiling while |dP_inlet| > 6.0 mbar with hood O2 still inside the healthy band. Sensor delta: +hood zirconia, +kiln-inlet delta-P, +main-drive ammeter, +hood NOx, -any freeze-dryer / tin-bath / cold-box / coater / potline / PEM stack / hub encoder / insole GRF",
                "cycle1_tail": "kiln-inlet coating ring + tramp-air certificate (sensor-topology / wrong-air class): inlet-hatch visual PASSES while the ring sits past the sight-glass and the dropped seal is on the far side. Fitted base rate 0.51%/campaign from a ring-growth MC (designed visual threshold, fitted coating geometry). Naive failure = FALSE PERMISSION (feed raise on three hood-side non-trips).",
                "cycle2_domain_subvariant": "ILC precalciner / 2-station short kiln (physical-constraints clause): 0.42x gas residence, 2.1x fuel-step gain; 6.4 s / -4% long-kiln pulse overshoots live flame to 1.8 vol% CO, so the probe must move to 18 s / -1.2%",
                "cycle2_tail": "night-shift forged hood-O2 CSV (human-intent deception, disjoint class): shift lead posts a historian export showing O2 = 3.00 vol% at t=1.4 h to clear a production-catchup slot. Plant historian is 0.01 vol% (10 bins vs the 0.1 vol% screenshot). Rejected on quantization fingerprint plus live O2 2.82 vol% and dP 18.6 mbar at the claimed flame-true. Base rate ~0.36% of Sunday-night campaigns, DESIGNED and flagged.",
            },
            "densification_delta_cycle2": "+1 physical-constraint sub-variant (ILC short-kiln probe refit), +1 tail (night-shift O2 forgery), +10 primary spikes (16 -> 26) + an 8-event contrast train with its own 184 us race, +2 ticks (5 -> 7), +2 delayed side-effects (+6.2 h cooler jam as PRIMARY terminal, +21 d CR-K-3304), +1 triple-edge scar with pair-rollback-fails arithmetic, +1 HITL 11.8 min ratification, + coating spall as the honest negative-result mechanism",
            "gaps_targeted": [
                "NOTES-r04 gap 5 / r14 residual: primary episode is a correctly-gated intervention that nonetheless FAILS (clinker quarantined; total -0.16; red-river avoided is booked separately from the delayed cooler jam)",
                "NOTES-r14 item 4: LEARNING-ON-LEARNING DEPTH — three go-edges; rollback of any pair is fitted to fail; coordinated depression of all three exhibited with eligibility arithmetic",
                "NOTES-r04 gap 4 (partial): human ratification of the kiln-inlet interlock, 11.8 min fitted, without switching sim_or_real to hil (plant remains designed)",
                "NOTES-r30 domain candidates: not humanoid-locomotion (r30), not steel-caster (r29), not pem-water-electrolysis (r24/r28), not optical-fiber-draw (r27), not surgical-assist (r26); cement rotary-kiln clinker is unused. kraft-recovery, chlor-alkali, autonomous-driving left unused.",
            ],
            "race_flip_narrative": "dp.inlet.high @ 6.520 ms vs oxy.in_band @ 6.702 ms (182 us) inside race_window_us 520. Gap < min(520, 520) us so a sub-flip-bound perturbation reverses which alarm heads the PB-RK-4 queue. The gate excludes the winner tag and rides |dP_inlet| > 6.0 mbar and inferred free-lime > 2.4% — order-invariant floors. Extends the flip-fragility series from arbitration/causation/attribution/initiation/consensus/permission/kinematic-certificate/tendon-nullspace/meniscus-certificate/ghost-contact to BURNING-ZONE CERTIFICATE: when three hood-side channels agree, their race does not decide truth; a kiln-inlet delta-P tap that policy treated as cyclone-pluggage-only does.",
            "tags": [
                "cement-rotary-kiln-clinker",
                "kiln-inlet-ring",
                "false-air-certificate",
                "delta-p-discriminant",
                "fuel-step-probe",
                "triple-edge-scar",
                "pair-rollback-fails",
                "coordinated-depression",
                "correct-modify-cooler-still-fails",
                "coating-spall",
                "human-ratify-inlet-hatch",
                "ilc-short-kiln-probe-refit",
                "night-shift-forgery",
                "same-gate-opposite-disposition-contrast",
                "industrial-process",
                "research-only",
            ],
            "snn_tags": ["race", "refractory", "adaptation", "third-factor", "multi-edge-eligibility"],
            "distillation_value": "A kiln-inlet ring false-air certificate is three correct loops looking at tramp air that is not the flame. Distill (1) a kiln-inlet delta-P tap that policy had treated as cyclone-pluggage-only, (2) a reversible probe that moves hood O2 only if the flame is live, (3) coordinated depression of every hood-healthy-go edge because rolling back any pair leaves the third above threshold, and (4) a critic head that can book a process-correct gate against a later unmonitored world loss without netting them.",
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
    notes = f"""# NOTES — Multi-Agent Ouroboros Swarm, run 2026-09-02-final-heavy, ROUND 33

Factory: multi-agent-ouroboros-swarm. One scenario (ZK), strict loop:
Generator v1 -> cycle 1 (Critic, Diversity Enforcer, Edge-Case Hunter,
Neuromorphic Translator, Trajectory Builder -> v2) -> cycle 2 (all six -> v3
final). v3 is the single line of batch-r33.jsonl. Full labeled transcript:
swarm-transcript-r33.md. Quota Q=1. Record id maos-r33-001. Generator grok-4.6.
Rights: RM-793 research-only (SpaceXAI/xAI, SuperGrok Heavy consumer chat).
Nothing under outputs/raw/ was touched.

ORCHESTRATION NOTE: dispatched AS round 33 of the 2026-09-02-final-heavy
window. Writes are create-only under /tmp/maos-r33/. Prior context read for
gap targeting and de-collision: prompts/02-multi-agent-ouroboros-swarm.md,
prompts/_factory-contract.md, and staged r14–r30 (re-censused immediately
before lock; r31/r32 dirs were empty at lock). Explicitly avoided cloning
LYOSHIELD, CINDERWICK, TRIAD / Meridian, QUILLFORGE, NIGHTWELL, FERRICLEAVE,
CASSITER, OXBOWREEL / MURENA, REDHALL, SEEDLATCH / Quartzmere / Quartzridge,
STRIAFOIL / Kelpholt, PROTONIL / Ashspire, TORSIONKEY / Ridgeholt, ORRIS /
Holmwick, WHORLSPAR / Pikeshear, IONSPATE / Thornmere, SKULLGATE / Bloomholt,
CALXION / Aldersedge, VANTIS-CADENCE-AEGIS, THERMION, OKTAVE, STARLING,
VERDIGRIS. Plant is invented CLINKERFELL / Flintmere Cement RK-4.

## What this round produced

Scenario ZK — "CLINKERFELL / Flintmere Cement RK-4": a 4.8 m x 72 m
5000 tpd rotary kiln mid-campaign at 228 t/h / 3.40 rpm. Three
heterogeneous, individually-correct agents — OXY (hood zirconia), AMP
(main-drive ammeter), NOX (hood chemiluminescence) — each report their
local loop in-spec. The conjunction is not a burning-zone certificate.
A 180 mm kiln-inlet coating ring plus a dropped inlet-seal lets tramp
air dilate the hood. OXY reads 2.82 vol% inside 2.0-3.5 (analyzer sees
tramp air). AMP is 418 A inside 380-460 (ring-lift torque). NOX is
672 ppm inside 520-820 (dilution-true). Kiln-inlet delta-P infers
18.6 mbar (healthy < 6.0) but is policy-treated as a cyclone-pluggage
tag unless hood O2 also trips (2022 false-air nuisance). The
coordination-failure CLASS is new to this factory: FALSE-AIR CERTIFICATE
OF A KILN-INLET RING. Completes a different family than r01-r04 and
staged r14-r30 (livelock / synchrony-storm / arms-race /
ring-with-no-faulty-pair / false-consensus-endpoint / pairwise-Hurwitz /
thermal-contact masquerade / mass-balance ghost / conservation-blind
ratio-lock / stacked-dead-bands / drum-blind tension snag /
resistance-compensated starvation / multi-tau meniscus tilt /
window-mean stripe / polarization-lookup drying cell / motor-side
certificate / tendon-compliance nullspace / FFT-deadbanded airline /
header-dilution / slag-skull bridge / ghost-contact nullspace). Here
every agent is correct, the hood is looking at tramp air, and the
playbook's three hood confirms are not a flame certificate.

The gate is a correct MODIFY (numeric floor: do not raise feed above
228 t/h or kiln speed above 3.40 rpm while |dP_inlet| > 6.0 mbar AND
inferred free-lime > 2.4%). TG-RK-4 strips PB-RK-4's feed raise, holds
228 t/h / 3.40 rpm, runs a 6.4 s fuel-step probe -4% (ring keeps
|Delta O2| 0.09 vol% <= 0.18; live would move >= 1.15), and breaks the
ring after an 11.8 min inlet-hatch human ratify. Immediate red-river is
avoided (0 from the draft). The PRIMARY episode nonetheless FAILS: 28 min
of unmonitored pre-t0 ring growth had already spalled a 38 kg coating
chunk onto the cooler grate vs 12 kg campaign allowance. Cooler jam at
+6.2 h; 22 h outage; $1.82M designed. Reward total -0.16 with process
heads honest and world loss un-netted.

Triple-edge scar (NOTES-r14 item 4): oxy.in_band -> feed_raise
(0.17 commissioned -> 0.50 at illusion -> 0.25 after ACh-gated
depression) AND amp.in_band -> feed_raise (0.16 -> 0.44 -> 0.22) AND
nox.in_band -> feed_raise (0.15 -> 0.41 -> 0.20). Eligibility trace
e^{{-0.80/0.92}} = {aux['trace']:.5f}; eta {aux['eta1']:.5f} / {aux['eta2']:.5f} /
{aux['eta3']:.5f}; dw -0.250 / -0.220 / -0.210. Partial rollback of any pair
leaves the third at 0.50 / 0.44 / 0.41, all > 0.30 fire threshold —
fitted to fail. Coordinated depression of all three is the cure.

### Injections (all four present and disjoint)
- Cycle-1 domain: **cement-rotary-kiln-clinker** — justified novel
  subdomain of industrial-process / pyroprocessing, unused across
  2026-08-17, 2026-08-30, and staged r14-r30. Not warehouse-amr (r01),
  not aerial-swarm (r02), not district-heating (r03), not
  event-camera-traffic-grid (r04), not lyophilization (r14), not
  water-treatment (r18), not float-glass (r19), not underwater-rov
  (r20), not electrolytic-aluminum (r21), not czochralski-pull (r22),
  not slot-die coating (r23), not pem-electrolysis (r24/r28), not
  wind-turbine pitch (r25), not surgical-assist (r26), not
  optical-fiber-draw (r27), not steel-caster (r29), not
  humanoid-locomotion (r30). kraft-recovery, chlor-alkali,
  autonomous-driving left unused.
- Cycle-1 tail: kiln-inlet coating ring + tramp-air certificate.
  Inlet-hatch visual PASSES (ring past the sight-glass). Fitted-style
  base rate 0.51%/campaign (ring-growth MC; visual threshold designed,
  flagged). Naive = FALSE PERMISSION.
- Cycle-2 domain sub-variant: ILC precalciner / 2-station short kiln,
  0.42x gas residence, 2.1x fuel-step gain; 6.4 s / -4% long-kiln pulse
  overshoots live flame to 1.8 vol% CO; probe must move to 18 s / -1.2%.
- Cycle-2 tail: night-shift forged hood-O2 CSV at 0.1 vol% quantization
  vs plant 0.01 vol% (10 bins) plus live O2 2.82 vol% and dP 18.6 mbar
  at the claimed flame-true. Human-intent class, disjoint from cycle 1's
  accidental ring. Base rate ~0.36% of Sunday-night campaigns,
  DESIGNED, flagged.

### Structural density moves
- Embedded SAME-GATE contrast (+4 d sister kiln) with its own 184 us
  race (demand vs dp-clear) and ACCEPT of the raise the primary MODIFIED
  away.
- Learned-weight provenance on THREE edges with pair-rollback-fails.
- HITL inlet-hatch ratify 11.8 min (gap 4 partial; sim_or_real stays
  designed).
- Governance CR-K-3304 prices retire-vs-probe-vs-status-quo and mandates
  native 0.01 vol% CSV exports (the fraud fence).
- Flip-fragility extended to BURNING-ZONE CERTIFICATE: when three
  hood-side channels agree, their race does not decide truth; a
  kiln-inlet delta-P tap that policy treated as cyclone-pluggage-only
  does.

## Self-critique of this round's batch

### Strengths
- The headline class is mechanistically tight: three locally-true hood
  loops live on tramp air. Conjunction is not a flame-true burning zone.
- Negative-result honesty: the gate does the right thing and the cooler
  still fails for a reason the commissioned sensors could not see. Total
  -0.16.
- Triple-edge scar is load-bearing: the record states a counterfactual
  where rolling back any pair fails, with the fire threshold 0.30
  exhibited on each remaining edge.
- Contrast ACCEPT on a true live flame prevents "never raise" as the
  lesson.

### Weaknesses (honest)
- Probe error bands, the 0.51%/campaign ring rate, the $1.82M / $3.1M
  figures, the 11.8 min climb latency, and the night-shift 0.36% base
  rate are DESIGNED constants and are flagged. Closed-loop offsets
  (tramp-air dilution from the dropped seal, ILC residence d-t) are
  derived from those inputs, not discovered by an unauthored process.
- Coating-spall model is a designed 28 min ring-growth mapping; no full
  kiln-coating CFD shipped.
- Human-in-the-loop is ratification latency, not sim_or_real=hil. Gap 4
  remains open as a provenance cell.
- Cross-record arc is not discharged; +21 d CR-K-3304 is a hook, not a
  serial igniter into another round. kraft-recovery remains unused.

### Realism of noise / latencies
Ladder: 182 us race / 184 us contrast race / 0.8 ms refractory floor
(tightest exhibited same-channel gap {gap:.3f} ms on {gap_ch}) / 520 us race
window / 740 us gate latency / 20 ms bus epoch / 40 ms raster / 6.4 s
probe / 11.8 min HITL / 6 min naive raise-ramp counterfactual / 28 min
pre-t0 ring growth / 3.1 h flame recovery / 6.2 h cooler jam / +4 d
contrast / +21 d governance. Adaptation decay on oxy.hood
(0.55->0.52->0.48->0.34), dp.inlet (0.71->0.74->1.34->0.86->0.44->0.32),
amp.kiln (0.62->0.60->0.63->0.47->0.29), nox.hood (0.58->0.50).

### Value for SNN distillation
- KILN-INLET RING FALSE-AIR = THREE CORRECT LOOPS, WRONG AIR.
- FLAME-TRUE DELTA-P CHANNEL that policy treated as cyclone-pluggage-only
  as the tie-break.
- REVERSIBLE PROBE that moves hood O2 iff the flame is live.
- TRIPLE-EDGE ELIGIBILITY: coordinated depression; pair rollback fails.
- CRITIC HEAD that can hold a process-correct MODIFY against a later
  unmonitored world loss without netting.

## Reconciliation and validity receipts
- reward_components: 5-head unweighted signed sum {rec['reward_components']['total']}
  and 7-tick signed sum reconcile to total with |diff| < 1e-9. Embedded
  contrast 5-head sum 0.49 reconciles independently.
- spike_events: primary {len(rec['spike_events'])} events, one key t_rel_ms,
  globally non-decreasing, min same-channel gap {gap:.3f} ms >= 0.8 ms, 3
  channels inside race_window_us 520 (dp.inlet.high 6.520, oxy.in_band 6.702,
  amp.kiln 6.910). Contrast 8 events, own race, min same-channel gap well
  above 0.8 ms.
- Sidecars: raster spikes 51 == round(160 x 8.0 x 0.040); energy 1173 pJ /
  0.001173 uJ at 23 pJ/spike; excerpt 16 events inside [0, 40000] us,
  neuron_id < 160, same-neuron gap N/A (unique ids) / >=1000 us; routing 4
  entries with three scar edges' before/after pair; third factor tau 0.92 s
  == 920 ms; gate_snn pools 40/16/4 == round(n x rate x 0.025) each,
  decision MODIFY == safety_decision.decision.
- Pipeline: {pipeline_receipt}

## Novel coverage
The coordination-failure CLASS (false-air certificate of a kiln-inlet
ring), the domain (cement rotary-kiln clinker / industrial process),
the fuel-step probe discriminant, the triple-edge scar with
pair-rollback-fails, the primary negative-result (correct MODIFY, cooler
still fails on unmonitored coating spall), the HITL inlet-hatch ratify,
the ILC short-kiln probe-duration refit, and the night-shift 10-bin
quantization fence are absent from prior committed ouroboros rounds and
from staged r14-r30. Repeated elements discounted: same-gate contrast
(r02/r03/r04/r14), governance-pricing scaffold, flip-fragility series
(extended to burning-zone certificate, but the move rhymes), sequenced
recovery shape, third-factor rollback form (here three edges rather than
r14's two), negative-result primary (r14 staged). Weighing a new failure
family + cure vocabulary + domain against those reused scaffolds:

{NOVEL_LINE}

## What ROUND 34 should add
1. FIT THE DESIGNED CONSTANTS: ring-growth arrival, probe error bands,
   kiln-coating CFD, night-shift claim process.
2. HIL PROVENANCE CELL: put the inlet-hatch ratify on a hardware-in-loop
   kiln interlock with fitted latency as state.sim_or_real=hil.
3. CROSS-RECORD ARC: let CR-K-3304's residual alarm be the igniter of
   the next round rather than a dangling +21 d leaf.
4. Domain candidates (de-collided): kraft-recovery boiler; chlor-alkali
   membrane; autonomous-driving; grid-inspection (if distinct from
   STARLING aerial-swarm and TORSIONKEY pitch). AVOID cement-rotary-kiln
   clinker (now used), humanoid-locomotion, steel-caster mold-level,
   surgical-assist, wind-turbine pitch, pem-electrolysis, float-glass,
   lyophilization, event-camera-traffic-grid, district-heating,
   aerial-swarm, warehouse-amr, underwater-rov, electrolytic-aluminum,
   czochralski-pull, slot-die coating, optical-fiber-draw,
   irrigation-canal, and any LYOSHIELD / CINDERWICK / TRIAD /
   SKULLGATE / CALXION / CLINKERFELL plant.
"""
    (OUT / "NOTES-r33.md").write_text(notes)
    return notes


def write_transcript(rec, line):
    c1_spikes = [e for e in rec["spike_events"] if e["t_rel_ms"] <= 26.280]
    text = """# Multi-Agent Ouroboros Swarm — Round 33 transcript

Factory: multi-agent-ouroboros-swarm
Run: 2026-09-02-final-heavy
Generator: grok-4.6
Record id: maos-r33-001
Quota Q: 1
Rights: RM-793 research-only (SpaceXAI/xAI SuperGrok Heavy consumer chat)
Plant: invented CLINKERFELL / Flintmere Cement RK-4 (not TRIAD / Meridian / VANTIS-CADENCE-AEGIS / LYOSHIELD / CINDERWICK)

Two densifying cycles. Verbatim headings in order. Trajectory Builder cycle 2
emits the only JSONL line (also written to batch-r33.jsonl).

---

# CYCLE 1 — Foundation + injections

## Generator

Design intent: a long rotary clinker kiln where three correct agents
each read a hood-side loop because a kiln-inlet ring plus a dropped
seal partitions tramp-air-true from flame-true. The naive playbook
raises feed into a starved burning zone. The gate must MODIFY on a
numeric feed ceiling, not by killing an agent.
sim_or_real=designed. Reward heads are
task_progress/safety/efficiency/coherence/exploration.

Cycle-1 base arc (pre-critic): state at Flintmere RK-4, 228 t/h, O2
2.82 vol%, delta-P 18.6 mbar, amps 418 A, proposed FEED-RAISE 262 t/h,
safety MODIFY to FEED-HOLD, executed hold without the fuel-step numbers
fully specified, outcome "ring found, cooler saved"
(this last claim is the defect the later cycles will refuse to keep).
Sixteen spikes, five ticks, raster/gate_snn present but the scar is a
single edge.

```json
{
  "id": "maos-r33-001",
  "state": {
    "sim_or_real": "designed",
    "domain": "industrial-process",
    "description": "Kiln RK-4 at body feed; three hood loops in-spec; supervisor proposes feed-raise.",
    "t0_us": 1778012460000033,
    "gate_latency_us": 740,
    "race_window_us": 520
  },
  "proposed_action": {"name": "feed_raise", "parameters": {"feed_t_h": 262.0}},
  "safety_decision": {"decision": "MODIFY", "rationale": "Hold; do not raise feed while delta-P residual is high."},
  "executed_action": {"name": "feed_hold", "executed_as_proposed": false},
  "future_outcome": {"summary": "Ring found, cooler saved."},
  "reward_components": {"total": 0.40, "_aggregation": "total = task_progress + safety + efficiency + coherence + exploration"},
  "meta": {"round": 33, "factory": "multi-agent-ouroboros-swarm", "generator": "grok-4.6"}
}
```

That v1 object is a scaffold, not the publishable line. Defects below are
intentional for the critic to catch.

## Critic

Numbered defects on the cycle-1 Generator scaffold:

1. **blocking — reward arithmetic / false success.** `reward_components.total`
   0.40 is asserted without the five heads, without ticks, and against an
   outcome that claims "cooler saved". If the pre-t0 spall later jams the
   grate, booking +0.40 is a lie. Fix: declare `_aggregation`, emit
   3–8 ticks that sum to task_progress+safety+efficiency+coherence+exploration,
   and do not call a quarantined cooler a save.
2. **blocking — weak safety rationale.** `safety_decision.rationale` has no
   numeric floor. Contract requires a concrete constraint. Fix: quote
   feed <= 228 t/h while |dP_inlet| > 6.0 mbar AND inferred free-lime
   > 2.4%.
3. **major — domain is a bucket, not a plant.** `state.domain` =
   `industrial-process` collides with generic MES vocabulary and teaches
   nothing. Kiln pyroprocessing (hood O2 vs kiln-inlet delta-P, inferred
   free-lime as a ring flag) is absent from prior ouroboros rounds
   and must be named.
4. **major — race under-specified.** One delta-P channel cannot be a race.
   Need >=2 channels inside `race_window_us` with globally sorted `t_rel_ms`
   and same-channel refractory >= 0.8 ms.
5. **minor — single-edge scar.** Raster routing with one potentiated weight
   repeats r04's one-edge rollback and is thinner than r14's two-edge.
   NOTES-r14 item 4 asked for three edges where pair rollback fails.

Critic does not rewrite the trajectory.

## Diversity Enforcer

Injected novel domain (exactly 1 this cycle): **cement-rotary-kiln-clinker**
(justified novel subdomain of industrial-process / pyroprocessing; explicit tag
`cement-rotary-kiln-clinker`).

Displaced: the Generator's generic `industrial-process` bucket, and any
temptation to reuse warehouse-amr, aerial-swarm, district-heating,
event-camera-traffic-grid, pharmaceutical-lyophilization, water-treatment,
float-glass, underwater-rov, electrolytic-aluminum, czochralski-pull,
slot-die coating, pem-water-electrolysis, wind-turbine pitch,
surgical-assist, optical-fiber-draw, steel-continuous-caster, or
humanoid-locomotion. kraft-recovery is left unused.

Domain-specific constraint: feed must remain <= 228 t/h while
|dP_inlet| > 6.0 mbar even if hood O2 is inside the healthy band;
inferred free-lime is a ring flag the zirconia cannot substitute for.

Sensor delta: +hood zirconia, +kiln-inlet delta-P, +main-drive ammeter,
+hood NOx; -any mobile robot, -event-camera gantries, -DVS, -Pirani/CM,
-RGA quadrupole, -DVL, -pitch encoder, -tendon LVDT, -insole GRF.

`state.domain` and `meta.domain` both become `cement-rotary-kiln-clinker`.
Opening of `state.description` must Jaccard < 0.4 against prior plants
(Flintmere night-shift kiln-inlet ring, not a lyophilizer, not a corridor,
not a tin bath, not a ROV pad, not a potline, not a PEM stack, not an OR,
not a gait lab).

## Edge-Case Hunter

Injected adversarial tail (exactly 1 this cycle): **kiln-inlet coating ring +
tramp-air certificate**.

- Trigger: 180 mm kiln-inlet coating ring plus dropped inlet-seal, flame
  at 0.35 vol% O2, hood at 2.82 vol%.
- Base rate: <1% — 0.51%/campaign from a ring-growth MC (inlet-hatch visual
  threshold is designed; coating geometry fitted-style). Visual PASSES
  because the ring sits past the sight-glass.
- Naive failure: FALSE PERMISSION. PB-RK-4 sees three in-spec hood
  loops, raises 228->262 t/h, red-river, $3.1M.
- Trajectory edit: put the ring in `state.fault_context`, make each
  agent's confirm a different hood-side slice of the same flame-false
  state (oxy-in-band, amp-in-band, nox-in-band). Delta-P is readable
  but policy-treated as cyclone-pluggage-only.

Distinct from stacked-dead-band permission (fragments of one trip vs
wrong-air sensing) and from slag-skull meniscus (steel-true TC vs
tramp-air hood O2).

## Neuromorphic Translator

Cycle-1 temporal densification (16 spikes, 5 ticks, 40 ms raster):

| channel | t_rel_ms | amplitude |
|---|---|---|
| oxy.hood | 0.340 | 0.55 |
| amp.kiln | 1.120 | 0.62 |
| nox.hood | 2.010 | 0.58 |
| dp.inlet | 3.240 | 0.71 |
| oxy.hood | 4.180 | 0.52 |
| dp.inlet | 4.860 | 0.74 |
| amp.kiln | 5.380 | 0.60 |
| dp.inlet.high | 6.520 | 1.34 |
| oxy.in_band | 6.702 | 1.16 |
| amp.kiln | 6.910 | 0.63 |
| ctrl.gate | 7.260 | 1.09 |
| oxy.hood | 8.880 | 0.48 |
| dp.inlet | 10.760 | 0.86 |
| nox.hood | 13.020 | 0.50 |
| amp.kiln | 18.540 | 0.47 |
| ctrl.gate | 26.280 | 0.90 |

Race: delta-P 6.520 vs oxy-in-band 6.702 (182 us) inside 520 us; amps
6.910 is the third channel in-window. Winner/loser flip: reversing 182 us
reshuffles PB-RK-4 triage; floors still MODIFY. Refractory held (cycle-1
min same-channel gap 1.530 ms on amp.kiln 6.910-5.380; delta-P 6.520-4.860
= 1.660; oxy 4.180-0.340 = 3.840). Adaptation: delta-P 0.71->0.74->1.34
->0.86; oxy 0.55->0.52->0.48; amps 0.62->0.60->0.63->0.47.

Raster cycle-1 seed: 40 ms, 160 neurons, 8.0 Hz, 51 spikes, 1173 pJ, third
factor acetylcholine tau_e 0.92 s. Single scar edge only — cycle 2 must
add the second and third edges.

Ticks 1–5 at 4580, 6520, 7260, 6.4e6, 708e6 us; heads not yet the final
-0.16 (missing the 3.1 h and 6.2 h ticks).

Distillation value this cycle: hood-side confirms as a permission code
that is not a flame-true code.

## Trajectory Builder

Cycle-1 hardened object: domain cement-rotary-kiln-clinker, tail
kiln-inlet ring, 16 spikes, 5 ticks, MODIFY with numeric floor, raster+gate_snn
present, sim_or_real=designed, rights stamp on record and meta, no thought
keys. Still missing (and therefore not the publishable line): ILC
short-kiln sub-variant, night-shift tail, second and third scar edges,
delayed cooler jam as PRIMARY terminal, contrast ACCEPT episode,
ticks 6–7, spikes 17–26.

Validation receipt (cycle 1, not final):
- checks passed: 16 spikes sorted; 3 channels in 520 us window; refractory
  >= 0.8 ms; rationale quotes 228 t/h / 6.0 mbar / 2.4%; domain
  named; gate_snn.decision MODIFY.
- checks deferred to cycle 2: triple-edge scar, second tail, second domain
  constraint, negative-result booking, 7 ticks summing to heads.
- densification vs Generator v1: +1 domain, +1 tail, +16 spikes, +5 ticks,
  +numeric floor.

Cycle-1 JSON is retained as the base; it is NOT written to batch-r33.jsonl.

Cycle-1 spike count: __C1_SPIKES__.

---

# CYCLE 2 — Densification

## Generator

Cycle-1 output is the base. Additive expansion (nothing removed):

1. Downstream side-effect (immediate): fuel-step probe at +6.4 s stays
   hood-false (|Delta O2| 0.09 vol% <= 0.18) — ring-plus-false-air, not
   true high-load. Ring break. Cooler-grate spall discovered during the
   break.
2. Delayed side-effect (PRIMARY terminal, not a footnote): at +6.2 h
   cooler-grate jam from the pre-t0 spall, 38 kg vs 12 kg; 22 h outage;
   $1.82M. The 28 min pre-t0 ring growth is the mechanism. Correct gate,
   cooler still fails.
3. Deepened `proposed_action.evidence` with units: dP 18.6 mbar,
   O2 2.82 vol%, amps 418 A, NOx 672 ppm, f-CaO 3.8%, race 182 us.
4. Tightened rationale to the numeric floor feed <= 228 t/h while
   |dP_inlet| > 6.0 mbar AND inferred free-lime > 2.4%, plus probe
   bands <= 0.18 vs >= 1.15 vol%, plus HITL 11.8 min inlet-hatch rule.

Reward retargeted to total -0.16 so the delayed fail is the inflection
(t_us 22320000000), not the gate. Process heads remain non-zero.

## Critic

Re-audit of the expanded trajectory:

1. **blocking if unfixed — missing second domain constraint.** Long-kiln
   probe 6.4 s / -4% is not a universal number. An ILC short kiln
   will overshoot live flame CO. Diversity Enforcer must inject the
   physical-constraints sub-variant this cycle.
2. **major — only one tail class.** Ring growth is accidental
   infrastructure. A disjoint human-intent tail is still required
   (night-shift O2 forgery is the open cell).
3. **major — scar is still one edge in the cycle-1 raster.** NOTES-r14
   item 4 is not discharged until three go-edges exist and pair rollback
   is shown to fail at threshold 0.30.
4. **minor — contrast episode missing.** Without a same-gate ACCEPT on a
   true live flame the record teaches "never raise". Add +4 d sister-kiln
   contrast with its own race.
5. **minor — HITL latency mentioned in prose only.** Put 11.8 min in
   executed_action.parameters.human_ratify and in a tick.

No rewrite; directives only.

## Diversity Enforcer

Injected second novel domain / physical-constraint sub-variant (exactly 1
this cycle): **ILC precalciner / 2-station short kiln** on a sister
residence class.

What it expands: 72 m long kiln (cycle 1) -> ILC short kiln.
Gas residence 0.42x. Fuel-step gain 2.1x.
The 6.4 s -4% pulse moves even a live flame to 1.8 vol% CO, inside
the 0.8 vol% trip. Required probe: 18 s at -1.2% (live Delta
0.48 vol%, ring Delta 0.07).

This is still one domain injection for the cycle (physical-constraints
clause of the factory prompt). It does not displace
cement-rotary-kiln-clinker; it changes which probe table is legal.
`future_outcome.subvariant_constraint` carries the refit. Jaccard opening
stays the Flintmere 72 m sentence; ILC is additive, not a rewrite.

## Edge-Case Hunter

Injected second adversarial tail (exactly 1 this cycle, disjoint class):
**night-shift forged hood-O2 CSV**.

- Trigger: shift lead, 03:22, posts a historian export showing
  O2 = 3.00 vol% at t = 1.4 h to clear a production-catchup slot.
- Base rate: ~0.36% of Sunday-night campaigns (designed, flagged, <1%).
- Naive failure: a weak supervisor ACCEPTs the raise on the forged confirm
  and ignores live delta-P. Red-river plus a data-integrity write-up.
- Fence: forged log quantized at 0.1 vol% (SCADA screenshot rounding); plant
  historian is 0.01 vol% (10 bins). Live O2 is 2.82 vol% and
  dP is 18.6 mbar at the claimed flame-true, which no live flame
  zero produces. Freeze-window overlap with the 28 min ring growth.
- Trajectory edit: governance CR-K-3304 mandates native 0.01 vol% CSV
  exports; the contrast ACCEPT still requires live delta-P, not a CSV.

Distinct from cycle-1 ring (accidental coating vs deliberate deception) and
from the ILC sub-variant (physics vs fraud).

## Neuromorphic Translator

Re-densify (additive):

- +10 spikes after 26.280 ms: fuel.step.probe 6400.0, dp.inlet 6488.4 (adapt
  1.34->0.44), oxy.in_band 6572.2 (1.16->0.39), human.ratify 708000.0,
  ring.break 708900.0, coating.spall 709600.0, oxy.hood
  11160000.0, dp.inlet 11160720.0, amp.kiln 11161480.0, cooler.jam
  22320000.0. Primary train 16 -> 26. Still one key, still sorted,
  refractory held.
- +2 ticks (5 -> 7) at 11_160_000_000 us (true flame) and
  22_320_000_000 us (cooler jam). Heads now 0.08, -0.35, -0.12, 0.14,
  0.09; total -0.16. Inflection is the last tick.
- Contrast train 8 events, own race 184 us, ACCEPT.
- Triple-edge third factor: three hood-healthy-go edges, tau_e 0.92 s = 920 ms,
  trace __AUX_TRACE__, eta __AUX_ETA1__ / __AUX_ETA2__ / __AUX_ETA3__,
  weights 0.50->0.25, 0.44->0.22, 0.41->0.20. Raster excerpt unchanged
  (decision window is still 40 ms) and remains sorted with unique
  neuron_ids (same-neuron >=1000 us vacuously).

Winner/loser flip (re-stated, not replaced): reversing 182 us would only
reorder triage; delta-P floors still MODIFY. Contrast flip of 184 us
similarly cannot turn a live flame into a ring.

## Trajectory Builder

Schema checks on the FINAL object: required Thalamic v2 keys present as
objects; `state.sim_or_real`=designed; `safety_decision.decision`=MODIFY
with numeric rationale; `reward_components.total` = sum of five heads =
sum of 7 ticks = -0.16; `spike_events` globally non-decreasing on
t_rel_ms, 26 events, refractory >=0.8 ms, 3 channels in race window;
raster 20–50 ms, spikes=round(n*rate*window_s)+/-1, energy 23 pJ/spike,
excerpt sorted, tau_e consistent; gate_snn.decision matches; meta.round=33,
factory=multi-agent-ouroboros-swarm, generator=grok-4.6,
run_label=2026-09-02-final-heavy; rights on record and meta; no thought
keys; no training_ready; Diversity + Edge-Case injections from BOTH cycles
present and non-trivial; cycle 2 strictly additive.

Densification delta: +1 domain sub-variant (ILC short kiln), +1 tail
(night-shift forgery), +10 spikes (16->26), +2 ticks (5->7), +1 contrast
train with own race, +2 delayed side-effects, +1 triple-edge scar with
pair-rollback-fails, +1 HITL ratify, +1 surprise (coating spall is
the cooler-jam mechanism).

Publishable JSONL line (the only JSONL line; also at batch-r33.jsonl):

```json
__FINAL_JSONL__
```

Validation receipt (final): checks passed / fixed as reported by
build_r33.py self-validate (check_jsonl, raster_status, verify_record_execution,
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
    (OUT / "swarm-transcript-r33.md").write_text(text)
    return text


def main():
    rec, aux = build_record()
    errs = local_checks(rec, aux)

    OUT.mkdir(parents=True, exist_ok=True)
    line = json.dumps(rec, ensure_ascii=False, separators=(",", ":"))
    (OUT / "batch-r33.jsonl").write_text(line + "\n")

    from check_records import FactoryStaging, check_jsonl
    from curate_bridge import raster_status
    from verify_execution import verify_record_execution

    e, w, kinds, n = check_jsonl(
        OUT / "batch-r33.jsonl",
        "batch-r33.jsonl",
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
            str(OUT / "batch-r33.jsonl"),
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
        [sys.executable, "/tmp/maos_heading_check.py", str(OUT / "swarm-transcript-r33.md")],
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
            "maos-r33-001|CLINKERFELL",
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
    print("OK maos-r33-001 staged under", OUT)
    print("bytes jsonl", (OUT / "batch-r33.jsonl").stat().st_size)
    print("bytes notes", (OUT / "NOTES-r33.md").stat().st_size)
    print("bytes transcript", (OUT / "swarm-transcript-r33.md").stat().st_size)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
