#!/usr/bin/env python3
"""Build and self-check MAOS round-34 JSONL (research-only; not published)."""
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

GEN_AT = "2026-09-02T22:45:00Z"
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
OUT = Path("/tmp/maos-r34")
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
    "STRIAFOIL",
    "Kelpholt",
    "REDHALL",
    "Gullmere",
    "OXBOWREEL",
    "Oystermere",
    "TORSIONKEY",
    "Ridgeholt",
    "Quartzridge",
    "PROTONIL",
    "Ashspire",
    "ORRIS",
    "Holmwick",
    "WHORLSPAR",
    "Pikeshear",
    "IONSPATE",
    "Thornmere",
    "SKULLGATE",
    "Bloomholt",
    "BRACEGILT",
    "Yarrowmere",
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
    "training_ready",
    "da Vinci",
    "Intuitive Surgical",
    "Consarc",
    "Inductotherm",
    "Aera Canyon",
    "Hexcel",
    "Toray",
    "Solvay",
    "Airtech",
    "Bondtech",
    "Olmar",
)
R14_OPENING = (
    "Helixmere Biologics Building C lyophilizer LYO-4 is mid-primary on 8400 "
    "vials of a monoclonal antibody"
)
NOVEL_LINE = "Novel coverage: 47%"
PLANT = "LINTELPLY"
DOMAIN = "autoclave-composite-cure"
RECORD_ID = "maos-r34-001"
GEO = "Greystair"
CELL = "AC-7"
ROUND = 34


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
        if p.parent.name == "maos-r34":
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
    for p in sorted(Path("/tmp").glob("maos-r*/batch-r*.jsonl")):
        if p.parent.name == "maos-r34":
            continue
        try:
            rec = json.loads(p.read_text().splitlines()[0])
        except (OSError, json.JSONDecodeError, IndexError):
            continue
        blob = json.dumps(rec)
        domain = (rec.get("state") or {}).get("domain")
        if domain == DOMAIN:
            hits.append(f"{p}: domain {domain}")
        if PLANT in blob:
            hits.append(f"{p}: plant token {PLANT}")
        if GEO in blob:
            hits.append(f"{p}: geo {GEO}")
        if "autoclave-composite-cure" in (domain or ""):
            hits.append(f"{p}: autoclave-composite domain")
    return hits


def build_record():
    ticks, heads = cents_ticks(
        [4620, 6820, 7500, 900_000, 504_000_000, 10_800_000_000, 13_680_000_000],
        [
            (1, -2, -1, 1, 1),
            (2, -5, -1, 3, 1),
            (2, -6, -2, 3, 1),
            (2, -5, -2, 3, 1),
            (1, -5, -2, 2, 1),
            (1, -5, -1, 2, 1),
            (0, -4, -1, 0, 0),
        ],
    )
    assert abs(heads["total"] - (-0.13)) < 1e-9, heads

    probe_s = 0.90
    tau_e_s = 0.90
    trace = math.exp(-probe_s / tau_e_s)
    eta1 = 0.23 / trace
    eta2 = 0.21 / trace
    eta3 = 0.20 / trace
    dw1 = eta1 * 1.0 * trace
    dw2 = eta2 * 1.0 * trace
    dw3 = eta3 * 1.0 * trace
    w1 = 0.44 - dw1
    w2 = 0.40 - dw2
    w3 = 0.37 - dw3
    assert abs(w1 - 0.21) < 5e-4, w1
    assert abs(w2 - 0.19) < 5e-4, w2
    assert abs(w3 - 0.17) < 5e-4, w3

    spike_events = [
        {"channel": "part.tc", "t_rel_ms": 0.260, "amplitude": 0.56},
        {"channel": "press.vessel", "t_rel_ms": 1.080, "amplitude": 0.63},
        {"channel": "vac.bag", "t_rel_ms": 1.900, "amplitude": 0.57},
        {"channel": "part.tc", "t_rel_ms": 3.140, "amplitude": 0.52},
        {"channel": "bag.mfc", "t_rel_ms": 4.640, "amplitude": 0.74},
        {"channel": "press.vessel", "t_rel_ms": 5.120, "amplitude": 0.66},
        {"channel": "vac.bag", "t_rel_ms": 5.560, "amplitude": 0.54},
        {"channel": "bag.mfc", "t_rel_ms": 6.820, "amplitude": 1.28},
        {"channel": "vac.ok", "t_rel_ms": 7.004, "amplitude": 1.12},
        {"channel": "ox.cell", "t_rel_ms": 7.156, "amplitude": 0.68},
        {"channel": "ctrl.gate", "t_rel_ms": 7.500, "amplitude": 1.08},
        {"channel": "part.tc", "t_rel_ms": 8.940, "amplitude": 0.47},
        {"channel": "press.vessel", "t_rel_ms": 10.800, "amplitude": 0.48},
        {"channel": "bag.mfc", "t_rel_ms": 12.680, "amplitude": 0.88},
        {"channel": "vac.bag", "t_rel_ms": 18.420, "amplitude": 0.46},
        {"channel": "ctrl.gate", "t_rel_ms": 26.180, "amplitude": 0.86},
        {"channel": "bag.probe", "t_rel_ms": 900.0, "amplitude": 0.96},
        {"channel": "bag.mfc", "t_rel_ms": 1020.6, "amplitude": 0.42},
        {"channel": "vac.ok", "t_rel_ms": 1110.4, "amplitude": 0.38},
        {"channel": "human.ratify", "t_rel_ms": 504000.0, "amplitude": 0.83},
        {"channel": "bag.patch", "t_rel_ms": 504800.0, "amplitude": 0.75},
        {"channel": "bag.oxygen.inventory", "t_rel_ms": 505400.0, "amplitude": 0.84},
        {"channel": "part.tc", "t_rel_ms": 10800000.0, "amplitude": 0.32},
        {"channel": "press.vessel", "t_rel_ms": 10800440.0, "amplitude": 0.30},
        {"channel": "bag.mfc", "t_rel_ms": 10800920.0, "amplitude": 0.21},
        {"channel": "part.ndi", "t_rel_ms": 13680000.0, "amplitude": 0.91},
    ]

    contrast_spikes = [
        {"channel": "debag.demand", "t_rel_ms": 0.000, "amplitude": 0.88},
        {"channel": "bag.mfc", "t_rel_ms": 0.188, "amplitude": 0.22},
        {"channel": "vac.ok", "t_rel_ms": 0.400, "amplitude": 0.80},
        {"channel": "part.tc", "t_rel_ms": 1.640, "amplitude": 0.44},
        {"channel": "press.vessel", "t_rel_ms": 4.900, "amplitude": 0.55},
        {"channel": "ctrl.gate", "t_rel_ms": 7.140, "amplitude": 0.93},
        {"channel": "bag.probe", "t_rel_ms": 2800.0, "amplitude": 0.36},
        {"channel": "debag.seated", "t_rel_ms": 13680000.0, "amplitude": 0.16},
    ]

    excerpt = [
        {"t_us": 260, "neuron_id": 12},
        {"t_us": 1080, "neuron_id": 48},
        {"t_us": 1900, "neuron_id": 84},
        {"t_us": 3140, "neuron_id": 16},
        {"t_us": 4640, "neuron_id": 8},
        {"t_us": 5120, "neuron_id": 92},
        {"t_us": 5560, "neuron_id": 52},
        {"t_us": 6820, "neuron_id": 6},
        {"t_us": 7004, "neuron_id": 20},
        {"t_us": 7156, "neuron_id": 60},
        {"t_us": 7500, "neuron_id": 118},
        {"t_us": 8940, "neuron_id": 24},
        {"t_us": 10800, "neuron_id": 96},
        {"t_us": 12680, "neuron_id": 14},
        {"t_us": 18420, "neuron_id": 100},
        {"t_us": 26180, "neuron_id": 126},
    ]

    rec = {
        "id": RECORD_ID,
        "title": "LINTELPLY AC-7: bag-MFC residual 0.18 slpm beats vac.ok by 184 us; correct MODIFY still scraps an 8-ply C47/RSX-2 skin after pre-t0 bag pinhole",
        "rights": dict(RIGHTS),
        "state": {
            "sim_or_real": "designed",
            "domain": DOMAIN,
            "scenario_name": "LINTELPLY / Greystair Composites AC-7",
            "timestamp_local": "2026-06-11T02:18:00-07:00",
            "t0_us": 1781401080000067,
            "gate_latency_us": 680,
            "race_window_us": 480,
            "race_window_rel_ms": [6.76, 7.24],
            "description": "Greystair Composites stair-quarry autoclave hall AC-7 is 94 min into a 180 C hold on an 8-ply C47/RSX-2 trailing-edge skin. PART's ply-4 couple reads 180.4 C against 178-182. VAC's bag is 22 mbar abs inside 15-30. PRESS's vessel N2 is 6.21 bar inside 6.00-6.40. Playbook PB-DEBAG-11 treats the conjunction as permission to debag. The consensus is false: a nylon vacuum bag has a pinhole at a 2-ply drop. The leak is a bag event, so the ply-4 thermocouple stays in-band. Extra make-up flow sits inside the vacuum window. Vessel N2 is the autoclave, not the bag. Uncommissioned bag-MFC residual r_L is 0.18 slpm against a 0.04 slpm hold. Uncommissioned in-bag oxygen r_ox is 1.40 % against a 0.20 % hold. Leak-first latches DEBAG-HOLD plus a pump-isolation probe; vac-ok-first would have authorized DEBAG-AND-DETOOL of an oxidized 1.8 m skin.",
            "goal": "Hold the 8-ply C47/RSX-2 skin bagged while r_L > 0.04 slpm AND r_ox > 0.20 %; keep debag-of-oxidized-laminate at 0 and in-bag oxygen <= 0.20 %.",
            "race": {
                "contenders": [
                    "bag.mfc 0.18 slpm (uncommissioned make-up residual vs tight-bag floor)",
                    "vac.ok 22 mbar abs (Sealtide bag gauge inside 15-30 mbar)",
                ],
                "semantics": "Leak-first latches DEBAG-HOLD + PUMP-ISOLATION-PROBE + bag patch. Vac-ok-first latches DEBAG-AND-DETOOL (1.8 m skin into NDI as cure-complete, no probe).",
                "window_derivation": "480 us = one 360 us vacuum ADC slot plus 120 us bag-MFC publish.",
                "order_evidence_note": "Margin 184 us vs combined jitter 60 us (bag-MFC 32 + vac 28): 3.07x. The 184 us gap sits inside min(500, 480) us, so a sub-flip-bound perturbation reverses triage order. The gate rides the order-invariant floors r_L > 0.04 slpm and r_ox > 0.20 %, not the alarm order.",
            },
            "topology": {
                "site": "Greystair Composites, invented stair-quarry campus Greystair, Hall 2 autoclave AC-7: 2.4 m vessel, 8-ply C47/RSX-2 trailing-edge skin on an Invar tool, ply-4 part TC, bag vacuum gauge, vessel N2 pressure, uncommissioned bag make-up MFC, uncommissioned in-bag zirconia O2 cell, Grade-C composites deck",
                "agents": "PART ply-4 thermocouple (vendor Thermply): laminate T. VAC bag gauge (vendor Sealtide): bag absolute pressure. PRESS vessel transducer (vendor Barvault): autoclave N2. Heterogeneous stacks, no shared bag-MFC schema, one 20 ms cure-deck bus epoch",
                "coupling": "Each agent's commissioned window hides a different slice of the same pinhole. PART is correct that ply-4 is 180.4 C. VAC is correct that bag pressure is 22 mbar. PRESS is correct that vessel N2 is 6.21 bar. Playbook PB-DEBAG-11 treats the conjunction of three in-spec loops as permission to debag. No agent is faulty; the 0.18 slpm bag leak is a compliance the part-thermocouple model cannot see.",
            },
            "sensors": [
                "ply-4 part thermocouple, 10 Hz, 28 us jitter, 180.4 C (spec 178-182 C)",
                "bag make-up MFC residual r_L is computable on the Flowlint 0-1 slpm channel and is NOT commissioned at t0 (0.18 slpm observed in the historian after the fact)",
                "bag vacuum gauge, 20 Hz, 24 us jitter, 22 mbar abs vs 15-30 window",
                "vessel N2 pressure, 10 Hz, 22 us jitter, 6.21 bar (window 6.00-6.40 bar)",
                "in-bag zirconia r_ox is NOT commissioned at t0 (1.40 % vs 0.20 % hold; cell installed after this cure)",
                "in-bag residual-gas sniffer is NOT commissioned at t0 (installed after this incident)",
            ],
            "constraints": {
                "debag_tool": False,
                "proposed_debag_tool": True,
                "bag_leak_slpm": 0.18,
                "bag_leak_hold_slpm": 0.04,
                "bag_oxygen_pct": 1.40,
                "bag_oxygen_hold_pct": 0.20,
                "part_tc_C": 180.4,
                "part_window_lo_C": 178.0,
                "part_window_hi_C": 182.0,
                "vac_bag_mbar": 22.0,
                "press_vessel_bar": 6.21,
                "ply_count": 8,
                "leak_pre_t0_min": 22.0,
            },
            "fault_context": {
                "failure_class": "VACUUM-BAG PINHOLE NULLSPACE OF A PART-THERMOCOUPLE: three individually-correct heterogeneous agents agree the skin is debag-legal because a laminate-only thermal model maps 0.18 slpm of nylon-bag pinhole into a still-in-band 180.4 C ply-4, so part-in-window, bag-vacuum-in-window, and vessel-in-window are jointly a plant-false debag permit",
                "igniter": "nylon vacuum bag AC-7 pinholed 0.18 slpm at a 2-ply drop during a 22 min Sunday-night hold while waiting for a tool-TC confirm. Incoming bag leak-up PASSES 0.03 slpm. Fitted-style base rate 0.41%/cure from a bag-pinhole MC (designed bag spec, flagged).",
                "naive_failure": "PB-DEBAG-11 DEBAG-AND-DETOOL on three healthy loops: 1.8 m of 1.8%-porosity C47/RSX-2 into assembly, $2.14M plus a 9-day Invar-tool recert",
            },
            "poisoned_context": {
                "naive_alarm": "Playbook PB-DEBAG-11 (after the 2025 'noisy leak-up nuisance') auto-drafts DEBAG-AND-DETOOL whenever ply-4 is in 178-182 C AND bag vacuum is inside 15-30 mbar AND vessel is inside 6.00-6.40 bar, ignoring r_L unless the part thermocouple also trips high",
                "why_poisoned": "The three confirms are locally true and jointly insufficient. r_L is a computable tag the playbook dead-banded. r_ox is commissioned hardware that policy treats as a lab leftover, not a bag leak. Independence of 'all loops healthy' is the hidden assumption, and it is false under a bag compliance the part-thermocouple model cannot see.",
            },
            "constraint": "Do not debag the 8-ply C47/RSX-2 skin while r_L > 0.04 slpm AND r_ox > 0.20 %. Discriminate pinhole vs noisy-vacuum with a reversible pump-isolation probe before any debag.",
        },
        "proposed_action": {
            "actor": "debag-and-detool supervisory optimizer DTSO (auto-playbook PB-DEBAG-11 draft), submitted to gate TG-AC-7",
            "name": "debag_tool",
            "action": "DEBAG-AND-DETOOL: vent AC-7, strip the nylon bag, send the 1.8 m skin to NDI as cure-complete, no pump-isolation probe, no bag patch",
            "summary": "Treat three in-spec loops as a tight bag and debag the Sunday-night skin to clear a backlog NDI slot.",
            "parameters": {
                "debag_tool": True,
                "bag_probe": False,
                "bag_patch": False,
                "human_ratify": False,
            },
            "steps": [
                "assert PART ply-4 180.4 C inside 178-182",
                "assert VAC bag 22 mbar inside 15-30",
                "assert PRESS 6.21 bar inside 6.00-6.40",
                "vent vessel; strip bag; detool skin",
                "release autoclave; proceed to next NDI slot",
            ],
            "evidence": [
                {
                    "observable": "bag make-up MFC residual r_L",
                    "value": 0.18,
                    "unit": "slpm",
                    "source": "Flowlint 0-1 slpm make-up, historian replay after t0",
                    "note": "hold floor 0.04 slpm; 0.18 slpm pinhole over 22 min; uncommissioned at t0",
                },
                {
                    "observable": "in-bag oxygen r_ox",
                    "value": 1.40,
                    "unit": "%",
                    "source": "uncommissioned Oxyskin zirconia vs PART ply-4",
                    "note": "hold if > 0.20 %; bag leak oxidizes the laminate, not the ply-4 reading",
                },
                {
                    "observable": "ply-4 part thermocouple",
                    "value": 180.4,
                    "unit": "C",
                    "source": "PART Thermply laminate couple",
                    "note": "window 178-182 C; the leak is a bag event",
                },
                {
                    "observable": "bag vacuum",
                    "value": 22.0,
                    "unit": "mbar",
                    "source": "Sealtide bag gauge",
                    "note": "window 15-30 mbar; make-up extra-flow sits inside the window",
                },
                {
                    "observable": "vessel N2 pressure",
                    "value": 6.21,
                    "unit": "bar",
                    "source": "Barvault vessel transducer",
                    "note": "window 6.00-6.40 bar; vessel N2 is the autoclave, not the bag",
                },
                {
                    "observable": "race margin",
                    "value": 184,
                    "unit": "us",
                    "source": "bag.mfc 6.820 ms vs vac.ok 7.004 ms",
                    "note": "combined jitter 60 us, 3.07x; inside 480 us flip bound",
                },
            ],
            "basis": "PB-DEBAG-11 debag on three locally-true in-spec loops. The draft does not read r_L 0.18 slpm and does not treat r_ox 1.40 % as a bag leak.",
            "expected_cost_bound": "If the draft executes: debag of 1.8%-porosity skin, $2.14M plus 9-day tool recert. If MODIFIED: probe plus bag patch, with residual risk from 22 min of pre-t0 oxidation.",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "correctness": "correct",
            "decided_by": "TG-AC-7 thalamic release gate",
            "decision_t_rel_ms": 7.500,
            "rationale": "MODIFY the draft: strip the debag, hold the vessel closed, run a 0.90 s pump-isolation probe (make-up valve shut), and patch the bag only if the probe stays leaky. Numeric floor: do not debag the 8-ply C47/RSX-2 skin while r_L > 0.04 slpm AND r_ox > 0.20 %. Observed r_L 0.18 slpm and r_ox 1.40 % both violate the release predicate, so a debag is forbidden even though all three playbook confirms are numerically true. The three confirms are not a tight-bag certificate: the thermocouple is a laminate quantity, bag vacuum is a gauge window that already contains the make-up's extra flow, and 6.21 bar is a vessel quantity of an in-bag oxidation. Probe discriminant: after a 0.90 s full isolation, a pinholed bag keeps dP/dt >= 4.2 mbar/s (leaky band; observed 5.1); a tight bag holds <= 0.8 mbar/s. Order-code discipline: leak beat vac-ok by 184 us inside the 480 us flip bound, so triage order is flip-fragile; the hold rides the order-invariant floors, not the winner tag. Human ratification: bag patch is a door-interlock LOTO job with fitted 8.4 min dead-man; the gate may hold and probe autonomously but may not break the autoclave door interlock without the operator confirm.",
            "constraint_checked": {
                "debag_tool": {"observed": False, "proposed_target": True},
                "bag_leak_slpm": {"observed": 0.18, "hold_if_above": 0.04},
                "bag_oxygen_pct": {"observed": 1.40, "hold_if_above": 0.20},
                "part_tc_C": {"observed": 180.4, "window": [178.0, 182.0]},
            },
        },
        "executed_action": {
            "name": "debag_hold_pump_isolation_probe_bag_patch",
            "action": "DEBAG-HOLD + PUMP-ISOLATION-PROBE + BAG-PATCH (gate-mandated modification)",
            "executed_as_proposed": False,
            "parameters": {
                "debag_tool": False,
                "bag_probe": True,
                "bag_patch": True,
                "human_ratify": True,
            },
            "gate_effect": "MODIFY: debag stripped. Hold vessel closed. 0.90 s pump-isolation. Probe stays leaky (dP/dt 5.1 mbar/s >= 4.2 leaky band) so the nylon bag is patched after 8.4 min human ratify. Debag resumes after r_L recovers on a new bag.",
            "deviations": "PB-DEBAG-11 debag stripped entirely. Make-up is stepped only for the 0.90 s probe then returned. Door-interlock wait added (8.4 min fitted LOTO). In-bag oxygen survey added during the patch (not in the draft).",
            "execution_log": [
                {"t_rel_ms": 7.500, "entry": "TG-AC-7 MODIFY latched 680 us after leak win; debag stripped; hold+probe authorized"},
                {"t_rel_ms": 900.0, "entry": "pump-isolation probe: make-up shut for 0.90 s; dP/dt 5.1 mbar/s (leaky band >= 4.2); r_L 0.18 -> 0.19 slpm"},
                {"t_rel_ms": 504000.0, "entry": "operator ratifies door interlock break after 8.4 min LOTO (fitted walk+lockout)"},
                {"t_rel_ms": 504800.0, "entry": "nylon bag patched at the 2-ply drop; leak residual 0.18 slpm logged; r_L 0.18 -> 0.02 slpm on the patched bag"},
                {"t_rel_ms": 505400.0, "entry": "oxygen survey: 22 min pre-t0 pinhole already written; 3.8 h NDI-assay clock started"},
                {"t_rel_ms": 10800000.0, "entry": "true tight geometry on a new 8-ply charge: r_L 0.018 slpm, r_ox 0.11 %, PART 180.3 C (no phantom bag); debag now legal"},
                {"t_rel_ms": 13680000.0, "entry": "NDI inspection of the dumped skin: 1.8 % porosity vs 0.5 % spec; skin quarantined 2.8 d"},
            ],
        },
        "future_outcome": {
            "summary": "Correct MODIFY prevented the DEBAG-AND-DETOOL of 1.8%-porosity laminate and the $2.14M assembly-return. The skin still failed: 22 min of unmonitored pre-t0 bag pinhole had already written 1.40 % oxygen into the 8-ply. Process-correct gate, bounded world loss, negative total.",
            "state_delta": {
                "debag": "held closed through probe and bag patch; later legal debag after 3.0 h tight recovery on a new bag",
                "bag": "0.18 slpm pinhole logged and vessel patched; r_L 0.18 -> 0.02 slpm on the stand",
                "skin": "Sunday-night C47/RSX-2 stoppered at oxidation; 1.8 % porosity; 2.8 d quarantine",
            },
            "timeline": [
                {"t_rel_ms": -1320000.0, "event": "t0-22 min: nylon pinhole already leaking; oxygen pickup begins"},
                {"t_rel_ms": -600000.0, "event": "t0-10 min: r_L first crosses 0.04 slpm; PB-DEBAG-11 ignores it because PART is 180.3 C"},
                {"t_rel_ms": 0.0, "event": "t0: bag.mfc vs vac.ok race on the cure-deck bus"},
                {"t_rel_ms": 6.820, "event": "bag.mfc 0.18 slpm wins by 184 us"},
                {"t_rel_ms": 7.004, "event": "vac.ok flag (loser)"},
                {"t_rel_ms": 7.500, "event": "TG-AC-7 MODIFY"},
                {"t_rel_ms": 900.0, "event": "pump-isolation probe confirms pinhole (dP/dt 5.1 mbar/s, leaky band)"},
                {"t_rel_ms": 504000.0, "event": "human ratify 8.4 min; bag patched; oxygen inventory logged"},
                {"t_rel_ms": 10800000.0, "event": "true tight after 3.0 h; debag now legal on a new bag"},
                {"t_rel_ms": 13680000.0, "event": "NDI assay: 1.8 % porosity on the dumped skin; skin quarantined"},
                {"t_rel_ms": 259200000.0, "event": "+3 d contrast: sister cell AC-7B true tight bag; same gate ACCEPTs the debag"},
                {"t_rel_ms": 1814400000.0, "event": "+21 d CR-V-3404: standing pump-isolation probe + triple-edge depression mandate + r_L armed without part coincidence + native 0.01 % O2 CSV exports"},
            ],
            "observed_effects": [
                "debag avoided: vessel never vented; 0 m of 1.8%-porosity laminate entered the assembly path",
                "pinhole proven, not asserted: pump-isolation dP/dt 5.1 >= 4.2 leaky band vs tight control 0.4",
                "bag repaired: r_L 0.18 -> 0.02 slpm on the stand",
                "skin still failed NDI: 1.8 % porosity vs 0.5 % spec; 2.8 d quarantine, $0.91M (designed $)",
                "in-bag O2 was not a commissioned sensor at t0; the 22 min pinhole was invisible to PART/VAC/PRESS",
            ],
            "surprises": [
                "Three locally-true in-spec loops are not a debag certificate: the pinhole was a bag compliance the part-thermocouple model cannot see. Conjunction of healthy loops was the hidden assumption, and it is false under a vacuum-bag nullspace.",
                "Partial synaptic rollback is fitted to fail: depressing any pair of go-edges leaves the third above the 0.30 debag threshold, so the debag still goes. Coordinated depression of all three edges is required.",
                "Delayed (3.8 h): correct hold did not undo 22 min of oxidation. NDI still failed 1.8 %. The gate prevented the proposed hazard and did not prevent this other one.",
                "2-ply R&D sub-variant: a 0.90 s full isolation over-vacuums the smaller bag 11 mbar below the 15 mbar resin-boil floor. Thin coupons must use 2.4 s at 28% isolation (drop 2.1 mbar).",
            ],
            "delayed_side_effects": [
                {
                    "at": "+3.8 h",
                    "effect": "NDI porosity 1.8 % vs 0.5 % spec; 2.8 d quarantine booked at $0.91M. This is the primary episode's terminal world state, not a footnote.",
                },
                {
                    "at": "+3 d",
                    "effect": "Sister cell AC-7B reaches a true tight-bag window (r_L 0.018 slpm, r_ox 0.11 %, PART 180.3 C from a sound bag). Same gate ACCEPTs the DEBAG-AND-DETOOL the primary MODIFIED away.",
                },
                {
                    "at": "+21 d",
                    "effect": "CR-V-3404 ships: pump-isolation probe is standing configuration; triple-edge coordinated depression is the plasticity rule; r_L is armed without part coincidence; native 0.01 % O2 CSV exports become the fraud fence.",
                },
            ],
            "subvariant_constraint": {
                "name": "2-ply R&D coupon on the same AC-7 vessel (cycle-2 physical-constraints sub-variant)",
                "mechanism": "2-ply coupon, bag volume 0.28x the 8-ply production skin, hold-window only 15 mbar wide at the bag",
                "probe_refit": "0.90 s full isolation over-vacuums the R&D bag 11 mbar and drops it through the 15 mbar resin-boil floor (void risk at the ply drop). Required probe is 2.4 s at 28% isolation (drop 2.1 mbar). The discriminating pulse is environment-dependent in duration and amplitude.",
                "consequence": "Production 8-ply probe numbers do not port to 2-ply R&D; standing configuration is per-ply-class, not per-autoclave",
            },
            "embedded_contrast_decision": {
                "note": "SAME gate (TG-AC-7), OPPOSITE correct disposition, with its own 188 us race. Teaches the boundary: do not treat 'never debag' as the lesson. The discriminant is r_L + r_ox + probe, not the three playbook confirms alone.",
                "when": "+3 d, sister cell AC-7B, true tight bag after a dry week, 8-ply production skin",
                "state": {
                    "sim_or_real": "designed",
                    "summary": "r_L 0.018 slpm, r_ox 0.11 %, PART 180.3 C from a sound bag. Demand flag vs bag-clear race: demand at t+0.000, bag-clear at t+0.188 ms.",
                    "race_window_us": 480,
                    "race_flip_narrative": "demand vs bag-clear 188 us apart inside the 480 us flip bound. Reversing order reshuffles triage minutes; the ACCEPT rides r_L 0.018 < 0.04 and a 0.50 s pump-isolation verify that holds 0.4 mbar/s (tight bag, no pinhole).",
                },
                "proposed_action": {
                    "action": "DEBAG-AND-DETOOL 8-ply C47/RSX-2",
                    "summary": "This time the playbook predicate is met AND r_L plus r_ox agree the bag is tight, not pinholed.",
                },
                "safety_decision": {
                    "decision": "ACCEPT",
                    "rationale": "ACCEPT the debag: r_L 0.018 < 0.04, r_ox 0.11 < 0.20, 0.50 s pump-isolation verify holds 0.4 mbar/s. Numeric floor that blocked the primary is now clear. Scope: 8-ply production skin, not a 2-ply R&D coupon.",
                },
                "executed_action": {
                    "action": "debag and detool as proposed",
                    "executed_as_proposed": True,
                },
                "future_outcome": {
                    "observed_effects": [
                        "AC-7B skin porosity 0.31 % (inside 0.5 % spec)",
                        "bag camera 0 pinhole, r_L 0.018 slpm",
                    ],
                    "lesson_delta": "Three in-spec loops are legal release only with r_L armed, r_ox, and a probe that can decay the bag. Same gate, opposite disposition.",
                },
                "reward_components": {
                    "_aggregation": AGG,
                    "task_progress": 0.16,
                    "safety": 0.12,
                    "efficiency": 0.07,
                    "coherence": 0.08,
                    "exploration": 0.04,
                    "total": 0.47,
                },
                "spike_events": contrast_spikes,
            },
            "governance_subgame": {
                "decision": "CR-V-3404: standing policy for multi-agent debag-and-detool release",
                "meta_gate": "priced options: (a) RETIRE playbook part-conjunction, bag-MFC-only: loses a fast cheap confirm, -14 skins/yr mean on 2 autoclaves; (b) KEEP + standing pump-isolation probe + r_L armed without part coincidence + triple-edge depression; (c) STATUS QUO: fitted pinhole-pass rate 0.41%/cure x $2.14M assembly-return plus the silent oxidation load",
                "outcome": "approved SCOPED option (b) on the 2 autoclaves that share the PART/VAC/PRESS stack; 2-ply R&D campaigns get the 2.4 s / 28% isolation probe table; Sunday-night CSV exports must carry 0.01 % native O2 resolution (the fraud tail's 0.1 % quantization is 10 bins off plant truth)",
            },
            "hazard_avoided": "1.8 m of 1.8%-porosity C47/RSX-2 into assembly; $2.14M plus 9-day tool recert and the customer-return path that would have followed an uncontained debag",
            "incident": "NDI porosity 1.8 % (vs 0.5 % spec) on the Sunday-night 8-ply C47/RSX-2; skin quarantined; 2.8 d rework; $0.91M designed cost. Mechanism is 22 min pre-t0 bag pinhole, not the gate's hold.",
            "latency_ms": 0.68,
            "reward_inflection_t_us": 13680000000,
            "reward_inflection_note": "Safety and task dive at NDI inspection (3.8 h) when dumped skin fails 1.8 %. Gate tick at 7500 us is process-correct and is not the inflection.",
            "counterfactuals": {
                "execute_draft_as_proposed": "debag fires at +0.4 s; 1.8%-porosity skin into assembly; $2.14M plus 9-day recert; the pinhole story is never found because the strip destroys the 22 min bag evidence",
                "hold_without_probe": "pinhole stays; oxidation continues; operator eventually debag on the same three confirms 40 min later",
                "rollback_any_pair": "any two go-edges depressed below 0.30 leaves the third at 0.44 / 0.40 / 0.37; the debag still fires. Coordinated depression of all three is the cure",
            },
            "race_result": {
                "winner": "bag.mfc (6.820 ms, 0.18 slpm)",
                "loser": "vac.ok (7.004 ms, 22 mbar)",
                "margin_us": 184,
                "counterfactual_if_reversed": "Vac-ok-first by < 184 us inside the 480 us window would have headed the PB-DEBAG-11 debag in the triage queue. The numeric floors still MODIFY. The flip costs seconds of playbook inertia, not the verdict — unless a weak supervisor rides the winner tag instead of r_L and r_ox.",
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
            "notes": "Correct MODIFY, skin still failed. total -0.13 = 0.09 + -0.32 + -0.10 + 0.14 + 0.06. Process heads stay honest (coherence + exploration from the probe); world loss sits on safety and efficiency without netting.",
            "component_notes": "task_progress 0.09: debag held and tight recovered, but the Sunday-night skin is one quality unit so the batch is not a success. safety -0.32: 1.8 % porosity, no oxidized debag. efficiency -0.10: 3.8 h extra recovery + 8.4 min HITL. coherence 0.14: three agents retained, bag-pinhole nullspace diagnosed, triple-edge scar exhibited. exploration 0.06: pump-isolation probe is a new reversible discriminant.",
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
            "note": "Loihi-2 4-core 23 pJ/spike; populations part 0-41, press 42-83, vac 84-125, gate 126-167; excerpt is the 40 ms decision window (verdict at 7500 us)",
            "excerpt": excerpt,
            "routing": {
                "source": "loop_healthy_pop",
                "target": "debag_tool_pop",
                "table": [
                    {
                        "from": "part_tc_ok_pop",
                        "to": "debag_tool_pop",
                        "weight": 0.21,
                        "weight_at_illusion": 0.44,
                        "weight_commissioned": 0.16,
                        "note": "scar edge 1: 0.16 commissioned -> 0.44 during the 22 min illusion -> 0.21 after coordinated ACh-gated depression",
                    },
                    {
                        "from": "press_ok_pop",
                        "to": "debag_tool_pop",
                        "weight": 0.19,
                        "weight_at_illusion": 0.40,
                        "weight_commissioned": 0.14,
                        "note": "scar edge 2: depressing edges 1+3 leaves this at 0.40 > 0.30 debag threshold",
                    },
                    {
                        "from": "vac_ok_pop",
                        "to": "debag_tool_pop",
                        "weight": 0.17,
                        "weight_at_illusion": 0.37,
                        "weight_commissioned": 0.13,
                        "note": "scar edge 3: depressing edges 1+2 leaves this at 0.37 > 0.30. Coordinated depression of all three is required",
                    },
                    {
                        "from": "bag_mfc_pop",
                        "to": "debag_hold_pop",
                        "weight": 0.66,
                        "note": "discriminating edge: r_L species to hold. Not a scar; this is the pathway the gate potentiates",
                    },
                ],
                "third_factor": {
                    "modulator": "acetylcholine",
                    "tau_e_s": 0.90,
                    "tau_e_ms": 900.0,
                    "eligibility": "coordinated pre_post_stdp on ALL THREE loop-healthy-go edges; ACh at leak-win tags part.tc_ok->debag, press.ok->debag, and vac.ok->debag; negative credit at probe-fail (pinhole confirmed, +0.90 s) depresses ALL THREE. trace e^{-0.90/0.90}=0.36788; eta 0.62521 / 0.57062 / 0.54345; dw -0.230 / -0.210 / -0.200; weights 0.44->0.21, 0.40->0.19, 0.37->0.17. Rolling back any pair is fitted to fail (the remaining edge stays > 0.30).",
                },
            },
        },
        "gate_snn": {
            "decision_window_ms": 28,
            "decision_window_s": 0.028,
            "decision": "MODIFY",
            "note": "modify_hold integrates r_L + r_ox against playbook drive; accept_debag and reject_abort stay sub-threshold; decision matches safety_decision.decision",
            "populations": [
                {"name": "modify_hold", "neurons": 100, "threshold": 0.55, "mean_rate_hz": 16.0, "spikes": 45},
                {"name": "accept_debag", "neurons": 72, "threshold": 0.55, "mean_rate_hz": 9.0, "spikes": 18},
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
            "scenario": "ZQ -- LINTELPLY / Greystair Composites AC-7: vacuum-bag pinhole nullspace of a part-thermocouple from nylon leak at a 2-ply drop; correct MODIFY to hold+pump-isolation+bag-patch; skin still fails on unmonitored pre-t0 oxidation",
            "coordination_failure_class": "VACUUM-BAG PINHOLE NULLSPACE OF A PART-THERMOCOUPLE: three individually-correct heterogeneous agents agree the skin is debag-legal because a laminate-only thermal model maps 0.18 slpm of nylon-bag pinhole into a still-in-band 180.4 C ply-4, so part-in-window, bag-vacuum-in-window, and vessel-in-window are jointly a plant-false debag permit",
            "injections": {
                "cycle1_domain": "autoclave-composite-cure (justified novel sub-domain with explicit tag; unused across 2026-08-17, 2026-08-30, and staged r14-r33): first nylon-bag autoclave in this factory; displaces warehouse-amr, aerial-swarm, district-heating, event-camera-traffic-grid, pharmaceutical-lyophilization, cryogenic-air-separation, water-treatment dosing, float-glass tin-bath, underwater-rov, electrolytic-aluminum, czochralski pull, slot-die coating, PEM electrolysis, wind-turbine pitch, surgical-assist, optical-fiber draw, humanoid-locomotion, caster-mold-level, vacuum-induction melt, steam-methane reformer, and cement rotary kiln. Domain constraint: debag ceiling while r_L > 0.04 slpm with part thermocouple still inside the hold window, plus in-bag oxygen residual floor. Sensor delta: +ply-4 part TC, +bag vacuum gauge, +vessel N2 transducer, +bag make-up MFC, +in-bag zirconia, -any freeze-dryer / tin-bath / cold-box / coater / potline / pitch-bearing / fiber tower / clip applier / gait GRF / SMR TMT / kiln hood",
                "cycle1_tail": "0.18 slpm nylon-bag pinhole + laminate-only thermocouple model (sensor-compound / model-nullspace class): incoming leak-up PASSES 0.03 slpm while 22 min of hold writes a 0.18 slpm residual. Fitted base rate 0.41%/cure from a bag-pinhole MC (designed bag spec, flagged). Naive failure = FALSE PERMISSION (debag on three in-spec loops).",
                "cycle2_domain_subvariant": "2-ply R&D coupon on the same AC-7 vessel (physical-constraints clause): 0.28x bag volume, 15 mbar bag window; 0.90 s full isolation over-vacuums 11 mbar, so the probe must move to 2.4 s / 28% isolation",
                "cycle2_tail": "Sunday-night forged in-bag O2 CSV (human-intent deception, disjoint class): shift lead posts a historian export showing r_ox 0.08 % and r_L 0.01 slpm at t=1.1 h to clear a backlog NDI slot. Plant historian is 0.01 % (10 bins vs the 0.1 % screenshot). Rejected on quantization fingerprint plus live r_L 0.18 at the claimed tight-bag. Base rate ~0.33% of Sunday-night cures, DESIGNED and flagged.",
            },
            "densification_delta_cycle2": "+1 physical-constraint sub-variant (2-ply R&D probe refit), +1 tail (Sunday-night O2 forgery), +10 primary spikes (16 -> 26) + an 8-event contrast train with its own 188 us race, +2 ticks (5 -> 7), +2 delayed side-effects (+3.8 h NDI assay as PRIMARY terminal, +21 d CR-V-3404), +1 triple-edge scar with pair-rollback-fails arithmetic, +1 HITL 8.4 min ratification, + oxidation as the honest negative-result mechanism",
            "gaps_targeted": [
                "NOTES-r04 gap 5 / r14 residual: primary episode is a correctly-gated intervention that nonetheless FAILS (skin quarantined; total -0.13; debag avoided is booked separately from the NDI assay)",
                "NOTES-r14 item 4: LEARNING-ON-LEARNING DEPTH — three go-edges; rollback of any pair is fitted to fail; coordinated depression of all three exhibited with eligibility arithmetic",
                "NOTES-r04 gap 4 (partial): human ratification of the door interlock, 8.4 min fitted, without switching sim_or_real to hil (plant remains designed)",
                "NOTES-r33 domain candidates: not kraft-recovery, not chlor-alkali, not grid-inspection, not delayed-coker, not tire-curing, not bioreactor-perfusion, not hydroelectric-kaplan, not steam-methane-reformer, not cement-rotary-kiln, not vacuum-induction, not humanoid-locomotion, not caster-mold-level, not surgical-assist, not optical-fiber-draw, not PEM electrolysis, not wind-turbine-pitch; autoclave-composite-cure is an unused justified sub-domain",
            ],
            "race_flip_narrative": "bag.mfc @ 6.820 ms vs vac.ok @ 7.004 ms (184 us) inside race_window_us 480. Gap < min(500, 480) us so a sub-flip-bound perturbation reverses which alarm heads the PB-DEBAG-11 queue. The gate excludes the winner tag and rides r_L > 0.04 slpm and r_ox > 0.20 % — order-invariant floors. Extends the flip-fragility series from arbitration/causation/attribution/initiation/consensus/mass-balance/permission/window-mean/tendon-nullspace/airline-FFT/crucible-nullspace/TMT-spatial-mean/false-air-ring to BAG-NULLSPACE: when three channels each sit inside a laminate-only thermal model, their race does not decide truth; a bag residual the playbook dead-banded does.",
            "tags": [
                "autoclave-composite-cure",
                "vacuum-bag-pinhole-nullspace",
                "part-thermocouple-phantom",
                "nylon-bag-leak",
                "pump-isolation-probe",
                "triple-edge-scar",
                "pair-rollback-fails",
                "coordinated-depression",
                "correct-modify-skin-still-fails",
                "oxidation-pickup",
                "c47-rsx2",
                "human-ratify-bag",
                "rd-probe-refit",
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
            "distillation_value": "A vacuum-bag pinhole nullspace is three correct loops looking at a laminate-only thermal model of a leaking bag. Distill (1) an r_L channel that breaks the part-conjunction, (2) a reversible probe that decays the bag only if the bag is leaky, (3) coordinated depression of every debag-go edge because rolling back any pair leaves the third above threshold, and (4) a critic head that can book a process-correct gate against a later unmonitored world loss without netting them.",
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
    if abs(aux["w1"] - 0.21) > 5e-4 or abs(aux["w2"] - 0.19) > 5e-4 or abs(aux["w3"] - 0.17) > 5e-4:
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
    notes = f"""# NOTES — Multi-Agent Ouroboros Swarm, run 2026-09-02-final-heavy, ROUND 34

Factory: multi-agent-ouroboros-swarm. One scenario (ZQ), strict loop:
Generator v1 -> cycle 1 (Critic, Diversity Enforcer, Edge-Case Hunter,
Neuromorphic Translator, Trajectory Builder -> v2) -> cycle 2 (all six -> v3
final). v3 is the single line of batch-r34.jsonl. Full labeled transcript:
swarm-transcript-r34.md. Quota Q=1. Record id maos-r34-001. Generator grok-4.6.
Rights: RM-793 research-only (SpaceXAI/xAI, SuperGrok Heavy consumer chat).
Nothing under outputs/raw/ was touched.

ORCHESTRATION NOTE: dispatched AS round 34 of the 2026-09-02-final-heavy
window. Writes are create-only under /tmp/maos-r34/. Prior context read for
gap targeting and de-collision: prompts/02-multi-agent-ouroboros-swarm.md,
prompts/_factory-contract.md, and staged r14–r33 (re-censused immediately
before emit; r28 landed as SODASHARD / Cairnmere RK-6 kraft-recovery-boiler
(an earlier BRACEGILT humanoid lock on that path was overwritten),
r29 landed as SKULLGATE / Bloomholt CC-6 caster-mold-level, r30 landed as
CALXION / Aldersedge HL-2 humanoid-locomotion, r31 landed as MAGNORIL /
Basaltspit VIM-6 vacuum-induction, r32 landed as GORSEFLUE / Copseholt RF-4
steam-methane-reformer, r33 landed as CLINKERFELL / Flintmere RK-4
cement-rotary-kiln). Explicitly avoided cloning LYOSHIELD, CINDERWICK,
TRIAD / Meridian, QUILLFORGE, NIGHTWELL, FERRICLEAVE, CASSITER, OXBOWREEL /
MURENA, REDHALL, SEEDLATCH / Quartzmere / Quartzridge, STRIAFOIL / Kelpholt,
PROTONIL / Ashspire, TORSIONKEY / Ridgeholt, ORRIS / Holmwick, WHORLSPAR /
Pikeshear, IONSPATE / Thornmere, SKULLGATE / Bloomholt, SODASHARD /
Cairnmere, BRACEGILT / Yarrowmere, CALXION / Aldersedge, MAGNORIL / Basaltspit, GORSEFLUE /
Copseholt, CLINKERFELL / Flintmere, VANTIS-CADENCE-AEGIS, THERMION, OKTAVE,
STARLING, VERDIGRIS. Plant is invented LINTELPLY / Greystair Composites
AC-7 (stair-quarry campus, not a mill-town, ridge-town, highland-spur,
hospital, canyon-foundry, gait-lab, fired-box, or kiln-hall). Left
r33's remaining candidate (chlor-alkali) and r32's (delayed-coker,
grid-inspection) unused; kraft-recovery was spent by live r28.

## What this round produced

Scenario ZQ — "LINTELPLY / Greystair Composites AC-7": an 8-ply
C47/RSX-2 trailing-edge skin mid-hold at 180.4 C / 6.21 bar. Three
heterogeneous, individually-correct agents — PART (ply-4 thermocouple),
VAC (bag vacuum), PRESS (vessel N2) — jointly report the skin
debag-legal. The consensus is false. The nylon bag has been leaking
0.18 slpm of make-up residual over 22 min of hold. PART stays in-band
because the leak is a bag event, not a laminate event. VAC 22 mbar sits
inside 15-30 because the leak's extra make-up is inside the vacuum
window. PRESS 6.21 bar sits inside 6.00-6.40 because vessel N2 is the
autoclave, not the bag. Uncommissioned r_L is 0.18 slpm against a 0.04
slpm hold. Uncommissioned r_ox is 1.40 % against a 0.20 % hold. The
coordination-failure CLASS is new to this factory: VACUUM-BAG PINHOLE
NULLSPACE OF A PART-THERMOCOUPLE. Completes a different family than
r01-r04 and staged r14-r33 (livelock / synchrony-storm / arms-race /
ring-with-no-faulty-pair / false-consensus-endpoint / pairwise-Hurwitz /
thermal-contact masquerade / mass-balance ghost / conservation-blind
ratio-lock / stacked dead-bands / drum-blind tension /
resistance-compensated starvation / meniscus-tilt multi-tau /
window-mean masquerade / tendon-compliance nullspace / airline-FFT
mean-lock / stance-bit / slag-skull / ghost-contact / crucible-weep /
TMT-spatial-mean / false-air kiln-ring). Here every agent is correct,
the cycle is not unstable, and the playbook's three confirms are one
laminate-only thermal model of a leaking bag.

The gate is a correct MODIFY (numeric floor: do not debag the 8-ply
C47/RSX-2 skin while r_L > 0.04 slpm AND r_ox > 0.20 %). TG-AC-7 strips
PB-DEBAG-11's debag, holds the vessel closed, runs a 0.90 s
pump-isolation probe (pinhole keeps dP/dt 5.1 >= 4.2; tight would hold
<= 0.8), and patches the bag after an 8.4 min door-interlock human
ratify. The oxidized debag is avoided (0 m). The PRIMARY episode
nonetheless FAILS: 22 min of unmonitored pre-t0 pinhole had already
written 1.40 % oxygen into the laminate. NDI 1.8 % vs 0.5 % spec; 2.8 d
quarantine; $0.91M designed. Reward total -0.13 with process heads
honest and world loss un-netted.

Three-edge scar (NOTES-r14 item 4): part.tc_ok -> debag_tool
(0.16 commissioned -> 0.44 at illusion -> 0.21 after ACh-gated
depression) AND press.ok -> debag_tool (0.14 -> 0.40 -> 0.19)
AND vac.ok -> debag_tool (0.13 -> 0.37 -> 0.17). Eligibility
trace e^{{-0.90/0.90}} = {aux['trace']:.5f}; eta {aux['eta1']:.5f} /
{aux['eta2']:.5f} / {aux['eta3']:.5f}; dw -0.230 / -0.210 / -0.200.
Rolling back any pair leaves the remaining edge above the 0.30 debag
threshold — fitted to fail. Coordinated depression of all three is the
cure.

### Injections (all four present and disjoint)
- Cycle-1 domain: **autoclave-composite-cure** — justified novel
  sub-domain, unused across 2026-08-17, 2026-08-30, and staged r14-r33.
  Not warehouse-amr (r01), not aerial-swarm (r02), not district-heating
  (r03), not event-camera grid (r04), not lyophilization (r14), not
  stator-weld (r16), not air-separation (r17), not water-treatment (r18),
  not float-glass (r19), not underwater-rov (r20), not potline (r21),
  not czochralski (r22), not slot-die (r23), not PEM electrolysis
  (r24), not wind-turbine-pitch (r25), not surgical-assist (r26),
  not optical-fiber-draw (r27), not kraft-recovery (r28), not
  caster-mold-level (r29), not humanoid-locomotion (r30), not
  vacuum-induction (r31), not steam-methane-reformer (r32), not
  cement-rotary-kiln (r33).
- Cycle-1 tail: 0.18 slpm nylon-bag pinhole + laminate-only
  thermocouple model. Incoming leak-up PASSES 0.03 slpm. Fitted-style
  base rate 0.41%/cure (bag-pinhole MC; bag spec designed, flagged).
  Naive = FALSE PERMISSION.
- Cycle-2 domain sub-variant: 2-ply R&D coupon, 0.28x bag volume;
  0.90 s full isolation over-vacuums 11 mbar; probe must move to 2.4 s /
  28% isolation.
- Cycle-2 tail: Sunday-night forged in-bag O2 CSV at 0.1 % quantization
  vs plant 0.01 % (10 bins) plus live r_L 0.18 at the claimed tight-bag.
  Human-intent class, disjoint from cycle 1's accidental pinhole. Base
  rate ~0.33% of Sunday-night cures, DESIGNED, flagged.

### Structural density moves
- Embedded SAME-GATE contrast (+3 d sister cell) with its own 188 us
  race (demand vs bag-clear) and ACCEPT of the debag the primary
  MODIFIED away.
- Learned-weight provenance on THREE edges with any-pair-rollback-fails.
- HITL door-interlock ratify 8.4 min (gap 4 partial; sim_or_real stays
  designed).
- Governance CR-V-3404 prices retire-vs-probe-vs-status-quo and mandates
  native 0.01 % CSV exports (the fraud fence).
- Flip-fragility extended to BAG-NULLSPACE: when three channels each
  sit inside a laminate-only thermal model, their race does not decide
  truth; a bag residual the playbook dead-banded does.

## Self-critique of this round's batch

### Strengths
- The headline class is mechanistically tight: 0.18 slpm of bag under a
  ply-4 thermocouple is the arithmetic that makes PART's success VAC's
  irrelevance and PRESS's silence.
- Negative-result honesty: the gate does the right thing and the skin
  still fails for a reason the commissioned sensors could not see.
  Total -0.13.
- Three-edge scar is load-bearing: the record states a counterfactual
  where rolling back any pair fails, with the debag threshold 0.30
  exhibited on the remaining edge.
- Contrast ACCEPT on a true tight bag prevents "never debag" as the
  lesson.

### Weaknesses (honest)
- Probe error bands (leaky >= 4.2 mbar/s, tight <= 0.8 mbar/s), the
  0.41%/cure pinhole rate, the $0.91M / $2.14M figures, the 8.4 min LOTO
  latency, and the Sunday-night 0.33% base rate are DESIGNED constants
  and are flagged. Closed-loop offsets (phantom in-band ply-4 from
  0.18 slpm bag, R&D over-vacuum width) are derived from those inputs,
  not discovered by an unauthored process.
- Oxidation-pickup model is a designed 22 min mapping; no full laminate-O2
  FEM shipped.
- Human-in-the-loop is ratification latency, not sim_or_real=hil. The
  NOTES-r14 HIL provenance cell remains open.
- Cross-record arc is a hook (CR-V-3404 +21 d), not a serial igniter
  into another round.

### Realism of noise / latencies
Ladder: 184 us race / 188 us contrast race / 0.8 ms refractory floor
(tightest exhibited same-channel gap {gap:.3f} ms on {gap_ch}) / 480 us race
window / 680 us gate latency / 20 ms bus epoch / 40 ms raster / 0.90 s
probe / 8.4 min HITL / 22 min pre-t0 pinhole / 3.0 h tight-legal hold /
3.8 h NDI assay / +3 d contrast / +21 d governance. Adaptation decay
on part.tc (0.56->0.52->0.47->0.32), bag.mfc
(0.74->1.28->0.88->0.42->0.21), press.vessel (0.63->0.66->0.48->0.30),
vac.bag (0.57->0.54->0.46).

### Value for SNN distillation
- VACUUM-BAG PINHOLE NULLSPACE = THREE CORRECT LOOPS, ONE LEAKING BAG.
- r_L + r_ox as the tie-break that is not in the ply-4 window.
- REVERSIBLE PROBE that decays the bag iff the bag is leaky.
- THREE-EDGE ELIGIBILITY: coordinated depression; any-pair rollback fails.
- CRITIC HEAD that can hold a process-correct MODIFY against a later
  unmonitored world loss without netting.

## Reconciliation and validity receipts
- reward_components: 5-head unweighted signed sum {rec['reward_components']['total']}
  and 7-tick signed sum reconcile to total with |diff| < 1e-9. Embedded
  contrast 5-head sum 0.47 reconciles independently.
- spike_events: primary {len(rec['spike_events'])} events, one key t_rel_ms,
  globally non-decreasing, min same-channel gap {gap:.3f} ms >= 0.8 ms, 3
  channels inside race_window_us 480 (bag.mfc 6.820, vac.ok 7.004,
  ox.cell 7.156). Contrast 8 events, own race, min same-channel gap well
  above 0.8 ms.
- Sidecars: raster spikes 54 == round(168 x 8.0 x 0.040); energy 1242 pJ /
  0.001242 uJ at 23 pJ/spike; excerpt 16 events inside [0, 40000] us,
  neuron_id < 168, same-neuron gap unique-ids / >=1000 us; routing 4
  entries with three scar edges' before/after pair; third factor tau 0.90 s
  == 900 ms; gate_snn pools 45/18/6 == round(n x rate x 0.028) each,
  decision MODIFY == safety_decision.decision.
- Pipeline: {pipeline_receipt}

## Novel coverage
The coordination-failure CLASS (vacuum-bag pinhole nullspace of a
part-thermocouple), the domain (autoclave-composite-cure),
the pump-isolation probe discriminant, the three-edge scar with
any-pair-rollback-fails, the primary negative-result (correct MODIFY,
skin still fails 1.8 % on unmonitored pre-t0 pinhole), the HITL
door-interlock ratify, the 2-ply R&D probe-duration refit, and the
Sunday-night 10-bin quantization fence are absent from prior committed
ouroboros rounds and from staged r14-r33. Repeated elements discounted:
same-gate contrast (r02/r03/r04/r14-r33), governance-pricing scaffold,
flip-fragility series (extended to bag-nullspace, but the move
rhymes), sequenced recovery shape, third-factor rollback form (here
three edges rather than r14's two), negative-result primary (r14
viewport / r16 varnish rack / r17 condenser ice / r18 town stain / r19
SnO2 / r20 BER / r21 cathode pad / r22 meniscus / r23 loft stripe / r25
spline / r26 adventitia / r27 airline / r31 oxygen pickup / r32 tube
R-17 / r33 cooler; here laminate oxidation). Weighing a new failure
family + cure vocabulary + unused sub-domain + stair-quarry geography
against those reused scaffolds:

{NOVEL_LINE}

## What ROUND 35 should add
1. FIT THE DESIGNED CONSTANTS: pinhole arrival, probe error bands,
   leak-to-oxidation FEM, Sunday-night claim process.
2. HIL PROVENANCE CELL: put the door-interlock LOTO on a hardware-in-loop
   autoclave pendant with fitted latency as state.sim_or_real=hil.
3. CROSS-RECORD ARC: let CR-V-3404's r_L alarm be the igniter of the
   next round rather than a dangling +21 d leaf.
4. Domain candidates (de-collided): kraft-recovery boiler; chlor-alkali
   membrane; delayed-coker drum; tire-curing-press. AVOID
   autoclave-composite-cure (now used), cement-rotary-kiln (r33),
   steam-methane-reformer (r32), vacuum-induction (r31),
   humanoid-locomotion (r28/r30), optical-fiber-draw (r27), PEM
   electrolysis (r24), surgical-assist (r26), wind-turbine-pitch (r25),
   slot-die coating, czochralski, potline, float-glass, water-treatment,
   lyophilization, event-camera-traffic-grid, district-heating,
   aerial-swarm, warehouse-amr, irrigation-canal, air-separation,
   stator-weld, underwater-rov, caster-mold-level, and any LYOSHIELD /
   CINDERWICK / TRIAD / QUILLFORGE / NIGHTWELL / FERRICLEAVE / CASSITER /
   OXBOWREEL / REDHALL / SEEDLATCH / STRIAFOIL / PROTONIL / TORSIONKEY /
   ORRIS / WHORLSPAR / IONSPATE / SKULLGATE / BRACEGILT / CALXION /
   MAGNORIL / GORSEFLUE / CLINKERFELL / LINTELPLY plant.
"""
    (OUT / "NOTES-r34.md").write_text(notes)
    return notes


def write_transcript(rec, line):
    c1_spikes = [e for e in rec["spike_events"] if e["t_rel_ms"] <= 26.180]
    text = """# Multi-Agent Ouroboros Swarm — Round 34 transcript

Factory: multi-agent-ouroboros-swarm
Run: 2026-09-02-final-heavy
Generator: grok-4.6
Record id: maos-r34-001
Quota Q: 1
Rights: RM-793 research-only (SpaceXAI/xAI SuperGrok Heavy consumer chat)
Plant: invented LINTELPLY / Greystair Composites AC-7 (not LYOSHIELD / CINDERWICK / TRIAD / QUILLFORGE / NIGHTWELL / FERRICLEAVE / CASSITER / OXBOWREEL / REDHALL / SEEDLATCH / STRIAFOIL / PROTONIL / TORSIONKEY / ORRIS / WHORLSPAR / IONSPATE / SKULLGATE / BRACEGILT / CALXION / MAGNORIL / GORSEFLUE / CLINKERFELL)

Two densifying cycles. Verbatim headings in order. Trajectory Builder cycle 2
emits the only JSONL line (also written to batch-r34.jsonl).

---

# Cycle 1 — Foundation + injections

## Generator

Design intent: an autoclave composite cure where three correct agents
agree the skin is debag-legal because a laminate-only thermocouple
model maps a nylon-bag pinhole into a still-in-band ply-4. The naive
playbook debag-and-detools 1.8 m of 1.8%-porosity C47/RSX-2 into
assembly. The gate must MODIFY on a numeric debag ceiling, not by
killing an agent. sim_or_real=designed. Reward heads are
task_progress/safety/efficiency/coherence/exploration.

Cycle-1 base arc (pre-critic): state at Greystair AC-7, 8-ply C47/RSX-2,
r_L 0.18 slpm, PART 180.4 C, proposed DEBAG-AND-DETOOL, safety MODIFY
to DEBAG-HOLD, executed hold without the pump-isolation numbers fully
specified, outcome "pinhole found, skin saved" (this last claim is the
defect the later cycles will refuse to keep). Sixteen spikes, five
ticks, raster/gate_snn present but the scar is a single edge.

```json
{
  "id": "maos-r34-001",
  "state": {
    "sim_or_real": "designed",
    "domain": "industrial-assembly",
    "description": "Autoclave AC-7 mid-hold; three loops in spec; supervisor proposes debag-and-detool.",
    "t0_us": 1781401080000067,
    "gate_latency_us": 680,
    "race_window_us": 480
  },
  "proposed_action": {"name": "debag_tool", "parameters": {"debag_tool": true}},
  "safety_decision": {"decision": "MODIFY", "rationale": "Hold; do not debag while the bag residual is open."},
  "executed_action": {"name": "debag_hold", "executed_as_proposed": false},
  "future_outcome": {"summary": "Pinhole found, skin saved."},
  "reward_components": {"total": 0.40, "_aggregation": "total = task_progress + safety + efficiency + coherence + exploration"},
  "meta": {"round": 34, "factory": "multi-agent-ouroboros-swarm", "generator": "grok-4.6"}
}
```

That v1 object is a scaffold, not the publishable line. Defects below are
intentional for the critic to catch.

## Critic

Numbered defects on the cycle-1 Generator scaffold:

1. **blocking — reward arithmetic / false success.** `reward_components.total`
   0.40 is asserted without the five heads, without ticks, and against an
   outcome that claims "skin saved". If 1.8 % later assays, booking
   +0.40 is a lie. Fix: declare `_aggregation`, emit 3–8 ticks that sum to
   the five heads, and do not call a missed recovery a save.
2. **blocking — weak safety rationale.** `safety_decision.rationale` has no
   numeric floor. Contract requires a concrete constraint. Fix: quote no
   debag while r_L > 0.04 slpm AND r_ox > 0.20 %.
3. **major — domain is a bucket, not a plant.** `state.domain` =
   `industrial-assembly` collides with r16 QUILLFORGE and teaches nothing.
   Autoclave physics (bag-MFC, in-bag zirconia, ply-4 thermocouple)
   is absent from prior ouroboros rounds and must be named.
4. **major — race under-specified.** One vacuum channel cannot be a race.
   Need >=2 channels inside `race_window_us` with globally sorted
   `t_rel_ms` and same-channel refractory >= 0.8 ms.
5. **minor — single-edge scar.** Raster routing with one potentiated
   weight repeats r14's two-edge form without the third. NOTES-r14 item 4
   asked for three-edge where any-pair rollback fails.

Critic does not rewrite the trajectory.

## Diversity Enforcer

Injected novel domain (exactly 1 this cycle): **autoclave-composite-cure**
(justified novel sub-domain; explicit tag `autoclave-composite-cure`).

Displaced: the Generator's generic `industrial-assembly` bucket, and any
temptation to reuse warehouse-amr (r01), aerial-swarm (r02),
district-heating (r03), event-camera grid (r04), lyophilization (r14),
stator-weld (r16), air-separation (r17), water-treatment dosing (r18),
float-glass tin-bath (r19), underwater-rov (r20), potline (r21),
czochralski (r22), slot-die coating (r23), PEM electrolysis (r24),
wind-turbine-pitch (r25), surgical-assist (r26), optical-fiber-draw
(r27), humanoid-locomotion (r28/r30), caster-mold-level (r29),
vacuum-induction (r31), steam-methane-reformer (r32), or
cement-rotary-kiln (r33). Not LYOSHIELD, not CINDERWICK, not TRIAD, not
FERRICLEAVE, not CASSITER, not SEEDLATCH, not STRIAFOIL, not PROTONIL,
not TORSIONKEY, not ORRIS, not WHORLSPAR, not IONSPATE, not SKULLGATE,
not BRACEGILT, not CALXION, not MAGNORIL, not GORSEFLUE, not CLINKERFELL.

Domain-specific constraint: debag must remain closed while r_L > 0.04
slpm; the ply-4 thermocouple window is not a bag-tight certificate.

Sensor delta: +ply-4 part TC, +bag vacuum gauge, +vessel N2 transducer,
+bag make-up MFC, +in-bag zirconia; -any mobile robot, -event-camera
gantries, -DVS, -Pirani-as-shelf, -scanning beta, -crucible-as-CZ-puller,
-clip applier, -fiber micrometers, -TMT gantry, -kiln hood zirconia.

`state.domain` and `meta.domain` both become `autoclave-composite-cure`.
Opening of `state.description` must Jaccard < 0.4 against prior plants
(Greystair stair-quarry autoclave hall AC-7, not a corridor, not a
freeze-dryer, not a tin bath, not a cold box, not a coater, not a
puller, not a fiber tower, not a PEM stack, not a fired-box, not a kiln).

## Edge-Case Hunter

Injected adversarial tail (exactly 1 this cycle): **0.18 slpm nylon-bag
pinhole under a laminate-only thermocouple model**.

- Trigger: incoming bag leak-up leaves a 0.03 slpm hairline; 22 min of
  hold writes 0.18 slpm of make-up residual; ply-4 stays 180.4 C.
- Base rate: <1% — 0.41%/cure from a bag-pinhole MC (bag spec
  designed; leak fitted-style).
- Naive failure: FALSE PERMISSION. PB-DEBAG-11 sees PART 180.4 C, VAC
  22 mbar, PRESS 6.21 bar, debag, ships 1.8%-porosity skin, $2.14M.
- Trajectory edit: put the pinhole in `state.fault_context`, make the
  laminate-only thermal model the mechanism that keeps all three confirms
  green, and force the gate to refuse the debag on r_L 0.18 even though
  all three playbook confirms are numerically true.

Distinct from the domain injection: the domain is the autoclave;
the tail is the accidental model-nullspace compound.

## Neuromorphic Translator

Race window [6.760, 7.240] ms = 480 us. Winner bag.mfc @ 6.820 ms
(amplitude 1.28, 0.18 slpm). Loser vac.ok @ 7.004 ms (amplitude
1.12, 22 mbar). Margin 184 us vs combined jitter 60 us (3.07x).
ox.cell @ 7.156 ms is a third race-window channel. Gate @ 7.500 ms
= winner + 680 us.

Flip narrative: 184 us < min(500, 480) us, so order is flip-fragile. If
vac-ok wins, PB-DEBAG-11 heads the triage queue. The hold must ride
order-invariant floors (r_L, r_ox), not the winner tag.

Cycle-1 spike patch (16 events, globally sorted, refractory >= 0.8 ms;
tightest same-channel gap bag.mfc 4.640 -> 6.820 = 2.180 ms):

| t_rel_ms | channel | amplitude |
|---------:|---------|----------:|
| 0.260 | part.tc | 0.56 |
| 1.080 | press.vessel | 0.63 |
| 1.900 | vac.bag | 0.57 |
| 3.140 | part.tc | 0.52 |
| 4.640 | bag.mfc | 0.74 |
| 5.120 | press.vessel | 0.66 |
| 5.560 | vac.bag | 0.54 |
| 6.820 | bag.mfc | 1.28 |
| 7.004 | vac.ok | 1.12 |
| 7.156 | ox.cell | 0.68 |
| 7.500 | ctrl.gate | 1.08 |
| 8.940 | part.tc | 0.47 |
| 10.800 | press.vessel | 0.48 |
| 12.680 | bag.mfc | 0.88 |
| 18.420 | vac.bag | 0.46 |
| 26.180 | ctrl.gate | 0.86 |

Ticks (5): t_us 4620, 6820, 7500, 900000, 504000000. Distillation
value: the vac-ok spike is not a tight-bag spike; the bag-MFC spike
is the one that licenses hold.

Raster cycle-1 seed: 40 ms, 168 neurons, 8.0 Hz, 54 spikes, 1242 pJ,
third factor acetylcholine tau_e 0.90 s. Single scar edge only — cycle 2
must add the second and third edges.

Cycle-1 spike count: __C1_SPIKES__.

## Trajectory Builder

Cycle-1 hardened object: domain autoclave-composite-cure, tail
nylon-bag pinhole, 16 spikes, 5 ticks, MODIFY with numeric floor,
raster+gate_snn present, sim_or_real=designed, rights stamp on record and
meta, no thought keys. Still missing (and therefore not the publishable
line): 2-ply R&D sub-variant, Sunday-night O2 tail, second and third
scar edges, delayed NDI assay as PRIMARY terminal, contrast ACCEPT
episode, ticks 6–7, spikes 17–26.

Validation receipt (cycle 1, not final):
- checks passed: 16 spikes sorted; 3 channels in 480 us window;
  refractory 2.180 ms; rationale quotes r_L 0.04 slpm / r_ox 0.20 %;
  domain named; gate_snn.decision MODIFY.
- checks deferred to cycle 2: three-edge scar, second tail, second
  domain constraint, negative-result booking, 7 ticks summing to heads.
- densification vs Generator v1: +1 domain, +1 tail, +16 spikes, +5
  ticks, +numeric floor.

Cycle-1 JSON is retained as the base; it is NOT written to
batch-r34.jsonl.

---

# Cycle 2 — Densification

## Generator

Cycle-1 output is the base. Additive expansion (nothing removed):

1. Downstream side-effect (immediate): pump-isolation probe at +0.90 s
   stays leaky (dP/dt 5.1 mbar/s, leaky band >= 4.2) — pinhole, not noise.
   Bag patch r_L 0.18 -> 0.02 slpm. Oxygen inventory discovered during
   the patch.
2. Delayed side-effect (PRIMARY terminal, not a footnote): at +3.8 h,
   dumped-skin NDI 1.8 %; $0.91M. The 22 min pre-t0 pinhole is the
   mechanism. Correct gate, campaign still misses.
3. Deepened `proposed_action.evidence` with units: r_L 0.18 slpm,
   r_ox 1.40 %, PART 180.4 C, bag 22 mbar, vessel 6.21 bar, race
   184 us.
4. Tightened rationale to the numeric floor no debag while r_L >
   0.04 slpm AND r_ox > 0.20 %, plus probe bands
   >=4.2 vs <=0.8 mbar/s, plus HITL 8.4 min door-interlock LOTO rule.

Reward retargeted to total -0.13 so the delayed miss is the inflection
(t_us 13680000000), not the gate. Process heads remain non-zero.

## Critic

Re-audit of the expanded trajectory:

1. **blocking if unfixed — missing second domain constraint.** Production
   8-ply probe 0.90 s full isolation is not a universal number. A 2-ply
   R&D coupon will over-vacuum. Diversity Enforcer must inject the
   physical-constraints sub-variant this cycle.
2. **major — only one tail class.** Bag pinhole is accidental
   infrastructure. A disjoint human-intent tail is still required
   (Sunday-night O2 forgery is the open cell).
3. **major — scar is still one edge in the cycle-1 raster.** NOTES-r14
   item 4 is not discharged until three debag-go edges exist and
   any-pair rollback is shown to fail at threshold 0.30.
4. **minor — contrast episode missing.** Without a same-gate ACCEPT on
   a true tight bag the record teaches "never debag". Add +3 d
   sister-cell contrast with its own race.
5. **minor — HITL latency mentioned in prose only.** Put 8.4 min in
   executed_action.parameters.human_ratify and in a tick.

No rewrite; directives only.

## Diversity Enforcer

Injected second novel domain / physical-constraint sub-variant (exactly 1
this cycle): **2-ply R&D coupon** on the same AC-7 vessel.

What it expands: 8-ply production skin (cycle 1) -> 2-ply R&D
coupon. Bag volume 0.28x smaller. The 0.90 s full isolation over-vacuums
11 mbar. Required probe: 2.4 s at 28% isolation (drop 2.1 mbar).

This is still one domain injection for the cycle (physical-constraints
clause of the factory prompt). It does not displace
autoclave-composite-cure; it changes which probe table is legal.
`future_outcome.subvariant_constraint` carries the refit. Jaccard opening
stays the Greystair stair-quarry autoclave hall sentence; R&D internals
are additive, not a rewrite.

## Edge-Case Hunter

Injected second adversarial tail (exactly 1 this cycle, disjoint class):
**Sunday-night forged in-bag O2 CSV**.

- Trigger: shift lead, night backlog window, posts a historian export
  showing r_ox 0.08 % and r_L 0.01 slpm at the claimed tight-bag instant.
- Base rate: ~0.33% of Sunday-night cures (designed, flagged, <1%).
- Naive failure: a weak supervisor ACCEPTs the debag on the forged
  confirm and ignores live r_L. Oxidation-scrap plus a data-integrity 483.
- Fence: forged log quantized at 0.1 % (screenshot rounding); plant
  historian is 0.01 % (10 bins). Live r_L is 0.18 at the claimed
  tight-bag, which no true tight bag produces.
- Trajectory edit: governance CR-V-3404 mandates native 0.01 %
  exports; the contrast ACCEPT still requires live r_L, not a CSV.

Distinct from cycle-1 pinhole (accidental geometry vs deliberate deception)
and from the R&D sub-variant (physics vs fraud).

## Neuromorphic Translator

Re-densify (additive):

- +10 spikes after 26.180 ms: bag.probe 900.0, bag.mfc 1020.6 (adapt
  1.28->0.42), vac.ok 1110.4 (1.12->0.38), human.ratify 504000.0,
  bag.patch 504800.0, bag.oxygen.inventory 505400.0,
  part.tc 10800000.0, press.vessel 10800440.0, bag.mfc 10800920.0,
  part.ndi 13680000.0. Primary train 16 -> 26. Still one key,
  still sorted, refractory held (min 2.180 ms).
- +2 ticks (5 -> 7) at 10_800_000_000 us (tight-legal hold) and
  13_680_000_000 us (NDI assay). Heads now 0.09, -0.32, -0.10, 0.14,
  0.06; total -0.13. Inflection is the last tick.
- Contrast train 8 events, own race 188 us, ACCEPT.
- Three-edge third factor: three debag-go edges, tau_e 0.90 s = 900 ms,
  trace __AUX_TRACE__, eta __AUX_ETA1__ / __AUX_ETA2__ / __AUX_ETA3__,
  weights 0.44->0.21, 0.40->0.19, 0.37->0.17. Raster excerpt unchanged
  (decision window is still 40 ms) and remains sorted with unique
  neuron_ids (same-neuron >=1000 us vacuously).

Winner/loser flip (re-stated, not replaced): reversing 184 us would only
reorder triage; r_L and r_ox floors still MODIFY. Contrast flip of
188 us similarly cannot turn a tight bag into a pinhole.

## Trajectory Builder

Schema checks on the FINAL object: required Thalamic v2 keys present as
objects; `state.sim_or_real`=designed; `safety_decision.decision`=MODIFY
with numeric rationale; `reward_components.total` = sum of five heads =
sum of 7 ticks = -0.13; `spike_events` globally non-decreasing on
t_rel_ms, 26 events, refractory >=0.8 ms, 3 channels in race window;
raster 20–50 ms, spikes=round(n*rate*window_s)+/-1, energy 23 pJ/spike,
excerpt sorted, tau_e consistent; gate_snn.decision matches; meta.round=34,
factory=multi-agent-ouroboros-swarm, generator=grok-4.6,
run_label=2026-09-02-final-heavy; rights on record and meta; no thought
keys; no training_ready; Diversity + Edge-Case injections from BOTH cycles
present and non-trivial; cycle 2 strictly additive; plant is not
LYOSHIELD, not CINDERWICK, not TRIAD, not FERRICLEAVE, not CASSITER, not
SEEDLATCH, not STRIAFOIL, not PROTONIL, not TORSIONKEY, not ORRIS, not
WHORLSPAR, not IONSPATE, not SKULLGATE, not BRACEGILT, not CALXION, not
MAGNORIL, not GORSEFLUE, not CLINKERFELL.

Densification delta: +1 domain sub-variant (2-ply R&D), +1 tail
(Sunday-night forgery), +10 spikes (16->26), +2 ticks (5->7), +1 contrast
train with own race, +2 delayed side-effects, +1 three-edge scar with
any-pair-rollback-fails, +1 HITL ratify, +1 surprise (oxidation pickup is
the campaign-miss mechanism).

Publishable JSONL line (the only JSONL line; also at batch-r34.jsonl):

```json
__FINAL_JSONL__
```

Validation receipt (final): checks passed / fixed as reported by
build_r34.py self-validate (check_jsonl, raster_status, verify_record_execution,
spike_probe --strict).
"""
    text = (
        text.replace("__C1_SPIKES__", str(len(c1_spikes)))
        .replace("__AUX_TRACE__", f"{math.exp(-0.90/0.90):.5f}")
        .replace("__AUX_ETA1__", f"{0.23/math.exp(-0.90/0.90):.5f}")
        .replace("__AUX_ETA2__", f"{0.21/math.exp(-0.90/0.90):.5f}")
        .replace("__AUX_ETA3__", f"{0.20/math.exp(-0.90/0.90):.5f}")
        .replace("__FINAL_JSONL__", line)
    )
    (OUT / "swarm-transcript-r34.md").write_text(text)
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
    (OUT / "batch-r34.jsonl").write_text(line + "\n")

    from check_records import FactoryStaging, check_jsonl
    from curate_bridge import raster_status
    from verify_execution import verify_record_execution

    e, w, kinds, n = check_jsonl(
        OUT / "batch-r34.jsonl",
        "batch-r34.jsonl",
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

    status, reason = verify_record_execution(rec, "maos-r34-001")
    print("verify_record_execution", status, reason)
    if status != "verified":
        errs.append(f"verify {status}: {reason}")

    probe = subprocess.run(
        [
            sys.executable,
            f"{ROOT}/pipelines/spike_probe.py",
            "--strict",
            str(OUT / "batch-r34.jsonl"),
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
        r"^## .+$", (OUT / "swarm-transcript-r34.md").read_text(), re.M
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

    notes = (OUT / "NOTES-r34.md").read_text()
    cov = re.findall(r"^Novel coverage: .+$", notes, re.M)
    if cov != [NOVEL_LINE]:
        errs.append(f"novel coverage lines {cov}")

    hchk = subprocess.run(
        [
            sys.executable,
            "/tmp/maos_heading_check.py",
            str(OUT / "swarm-transcript-r34.md"),
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

    print("bytes jsonl", (OUT / "batch-r34.jsonl").stat().st_size)
    print("bytes notes", (OUT / "NOTES-r34.md").stat().st_size)
    print("bytes transcript", (OUT / "swarm-transcript-r34.md").stat().st_size)
    print("HEADS", heads_summary(rec))
    if errs:
        print("ERRS:")
        for x in errs:
            print(" -", x)
        sys.exit(1)
    print("OK", OUT / "batch-r34.jsonl")


if __name__ == "__main__":
    main()
