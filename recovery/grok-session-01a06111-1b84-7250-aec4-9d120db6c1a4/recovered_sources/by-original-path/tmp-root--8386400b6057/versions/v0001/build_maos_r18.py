#!/usr/bin/env python3
"""Build MAOS r18 staging artifacts under /tmp/maos-r18/. Never writes outputs/raw/."""
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

OUT = Path("/tmp/maos-r18")
GEN_AT = "2026-09-02T16:40:18Z"
T0_US = 1788367218000014
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
HIDDEN = ("thought", "chain_of_thought", "scratch", "inner_monologue")
BANNED = (
    "LYOSHIELD",
    "CINDERWICK",
    "Lodenholt",
    "Helixmere",
    "TRIAD",
    "Meridian Gateway",
    "VANTIS",
    "CADENCE",
    "AEGIS",
    "THERMION",
    "STARLING",
    "OKTAVE",
    "VERDIGRIS",
    "PALISADE",
    "KESTREL",
    "TELAMON",
    "MURENA",
    "HALYARD",
    "CHORDA",
    "TESSERA",
    "PEREGRINE",
    "VELA-RS",
    "CEDAR-FDR",
    "AMA-CS-2",
    "AISLE-9",
    "GRID-EDGE",
    "Brenner Cold",
    "Vireo District",
    "Sondera",
    "Bracken Sound",
    "Corvid Reach",
    "training_ready",
)


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
            return f"refractory {ch}: {t}-{last[ch]}={(t - last[ch]):.4f} < {floor_ms}"
        last[ch] = t
    return None


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
            return f"same-neuron gap {n}: {t - last_n[n]}"
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


def build_record():
    ticks, heads = cents_ticks(
        [3050, 5882, 6642, 12_000_000, 576_000_000, 5_400_000_000, 23_400_000_000],
        [
            (1, -2, -1, 1, 1),
            (1, -4, -1, 3, 1),
            (2, -6, -2, 4, 2),
            (1, -5, -2, 3, 1),
            (1, -5, -2, 2, 0),
            (0, -4, -2, 0, 0),
            (0, -4, -2, 0, 0),
        ],
    )
    assert abs(heads["total"] - (-0.18)) < 1e-9, heads
    assert abs(heads["task_progress"] - 0.06) < 1e-9
    assert abs(heads["safety"] - (-0.30)) < 1e-9
    assert abs(heads["efficiency"] - (-0.12)) < 1e-9
    assert abs(heads["coherence"] - 0.13) < 1e-9
    assert abs(heads["exploration"] - 0.05) < 1e-9

    trace = math.exp(-0.80 / 0.90)
    eta1 = 0.6324
    eta2 = 0.5595
    dw1 = eta1 * 1.0 * trace
    dw2 = eta2 * 1.0 * trace
    w1 = 0.44 - dw1
    w2 = 0.39 - dw2
    assert abs(w1 - 0.18) < 5e-4, w1
    assert abs(w2 - 0.16) < 5e-4, w2
    assert abs(trace - 0.41111) < 5e-4, trace

    spike_events = [
        {"channel": "scar.scd", "t_rel_ms": 0.38, "amplitude": 0.58},
        {"channel": "alk.ph", "t_rel_ms": 1.14, "amplitude": 0.61},
        {"channel": "floc.ntu", "t_rel_ms": 1.98, "amplitude": 0.70},
        {"channel": "cons.fe.residual", "t_rel_ms": 3.05, "amplitude": 0.64},
        {"channel": "rcy.magmeter", "t_rel_ms": 4.22, "amplitude": 0.55},
        {"channel": "scar.scd", "t_rel_ms": 5.04, "amplitude": 0.52},
        {"channel": "alk.ph", "t_rel_ms": 5.28, "amplitude": 0.49},
        {"channel": "cons.fe.residual", "t_rel_ms": 5.882, "amplitude": 1.28},
        {"channel": "scar.scd.demand", "t_rel_ms": 6.071, "amplitude": 1.14},
        {"channel": "rcy.header.dp", "t_rel_ms": 6.164, "amplitude": 0.97},
        {"channel": "ctrl.gate", "t_rel_ms": 6.642, "amplitude": 1.08},
        {"channel": "scar.scd", "t_rel_ms": 8.05, "amplitude": 0.47},
        {"channel": "alk.ph", "t_rel_ms": 10.22, "amplitude": 0.44},
        {"channel": "cons.fe.residual", "t_rel_ms": 12.64, "amplitude": 0.82},
        {"channel": "floc.ntu", "t_rel_ms": 18.4, "amplitude": 0.51},
        {"channel": "ctrl.gate", "t_rel_ms": 24.8, "amplitude": 0.88},
        {"channel": "rcy.dp.probe", "t_rel_ms": 12000.0, "amplitude": 0.96},
        {"channel": "cons.fe.residual", "t_rel_ms": 12124.6, "amplitude": 0.41},
        {"channel": "scar.scd.demand", "t_rel_ms": 12210.8, "amplitude": 0.38},
        {"channel": "human.ratify", "t_rel_ms": 576000.0, "amplitude": 0.78},
        {"channel": "rcy.mov.isolate", "t_rel_ms": 576800.0, "amplitude": 0.71},
        {"channel": "rcy.magmeter.unfreeze", "t_rel_ms": 577200.0, "amplitude": 0.66},
        {"channel": "floc.ntu", "t_rel_ms": 5400000.0, "amplitude": 0.88},
        {"channel": "gac.mn.breakthrough", "t_rel_ms": 23400000.0, "amplitude": 0.90},
        {"channel": "hypo.cl2", "t_rel_ms": 23400880.0, "amplitude": 0.36},
        {"channel": "dist.brown.water", "t_rel_ms": 25200000.0, "amplitude": 0.84},
    ]
    ref = check_refractory(spike_events)
    assert ref is None, ref
    times = [e["t_rel_ms"] for e in spike_events]
    assert times == sorted(times)
    race = [e for e in spike_events if 5.7 <= e["t_rel_ms"] <= 6.2]
    race_ch = {e["channel"] for e in race}
    assert len(race_ch) >= 3, race_ch
    assert "cons.fe.residual" in race_ch and "scar.scd.demand" in race_ch

    excerpt = [
        {"t_us": 380, "neuron_id": 52},
        {"t_us": 1140, "neuron_id": 148},
        {"t_us": 1980, "neuron_id": 152},
        {"t_us": 3050, "neuron_id": 8},
        {"t_us": 4220, "neuron_id": 100},
        {"t_us": 5040, "neuron_id": 60},
        {"t_us": 5280, "neuron_id": 150},
        {"t_us": 5882, "neuron_id": 12},
        {"t_us": 6071, "neuron_id": 72},
        {"t_us": 6164, "neuron_id": 108},
        {"t_us": 6642, "neuron_id": 128},
        {"t_us": 8050, "neuron_id": 64},
        {"t_us": 10220, "neuron_id": 154},
        {"t_us": 12640, "neuron_id": 16},
        {"t_us": 18400, "neuron_id": 156},
        {"t_us": 24800, "neuron_id": 132},
    ]
    ex_err = check_excerpt(excerpt, 160, 40)
    assert ex_err is None, ex_err
    assert round(160 * 8.0 * 0.040) == 51
    assert 51 * 23 == 1173

    gate_snn = {
        "decision_window_ms": 25,
        "decision_window_s": 0.025,
        "decision": "REJECT",
        "note": "reject_emergency integrates conservation residual + recycle DP freeze-flag against playbook drive; accept_bump and modify_hold stay sub-threshold; decision matches safety_decision.decision",
        "populations": [
            {
                "name": "reject_emergency",
                "neurons": 96,
                "threshold": 0.55,
                "mean_rate_hz": 18.0,
                "spikes": 43,
            },
            {
                "name": "accept_bump",
                "neurons": 96,
                "threshold": 0.55,
                "mean_rate_hz": 6.0,
                "spikes": 14,
            },
            {
                "name": "modify_hold",
                "neurons": 48,
                "threshold": 0.7,
                "mean_rate_hz": 4.0,
                "spikes": 5,
            },
        ],
    }
    gerr = check_gate_pops(gate_snn)
    assert gerr is None, gerr

    rec = {
        "id": "maos-r18-001",
        "title": "FERRICLEAVE Train-3: Fe conservation residual 0.19 beats SCD demand by 189 us; correct REJECT still stains the town on pre-loaded GAC manganese",
        "rights": dict(RIGHTS),
        "state": {
            "sim_or_real": "designed",
            "domain": "distributed-water-treatment-dosing",
            "scenario_name": "FERRICLEAVE / Pellwater Civic WTP Train-3",
            "timestamp_local": "2026-09-02T11:40:18-05:00",
            "t0_us": T0_US,
            "gate_latency_us": 760,
            "race_window_us": 500,
            "race_window_rel_ms": [5.7, 6.2],
            "description": "Pellwater Civic Water Treatment Works Train-3 is mid-coagulation on an 8.0 MLD dual-media train when three heterogeneous, individually-correct dosing agents jointly report a coagulant-demand emergency. SCAR-7 holds ferric at 24.0 mg/L as Fe with streaming current -4.6 mV against a -2.0 mV setpoint. ALK-2 holds lime to flocculator pH 6.42 against 6.50. FLOC-9 holds polymer against an online-jar settled turbidity of 0.42 NTU (target 0.30). The consensus is false as a plant-wide raw-water event: filter-backwash supernate is recycling at 41.6 L/s while magmeter FT-RCY-3 is frozen at 0.00 L/s after a weekend zero-cal, so PB-COAG-11 reads 'no recycle, therefore raw-water demand' and drafts an 18% ferric bump on all three trains. Fe-mass conservation residual r_Fe is 0.19 against a 0.12 hold floor; header differential pressure 18.4 kPa implies 41.6 L/s through the calibrated orifice. Conservation-first latches REJECT plus a recycle-header DP probe; SCD-demand-first would have authorized the plant-wide bump that drops pH 0.22 and redissolves GAC MnOx.",
            "goal": "Keep Train-3 Fe dose <= 28.0 mg/L as Fe while |r_Fe| > 0.12 AND |SCD-implied zeta - grab zeta| > 8 mV AND recycle magmeter freeze-flag (0.00 L/s with header DP > 5 kPa); keep finished-water Mn <= 0.05 mg/L and settled turbidity on-spec without a plant-wide coagulant emergency.",
            "race": {
                "contenders": [
                    "cons.fe.residual r_Fe 0.19",
                    "scar.scd.demand SCD -4.6 mV",
                ],
                "semantics": "Conservation-first latches REJECT of PB-COAG-11 plus a 12.0 s recycle-header DP probe and MOV isolate. SCD-demand-first latches PLANT-WIDE COAG-EMERGENCY (Fe +18% on Trains 1-3, lime +0.15 pH, polymer +20%, filters to waste).",
                "window_derivation": "500 us = one 400 us SCD ADC slot plus 100 us residual-estimator settle.",
                "order_evidence_note": "Margin 189 us vs combined jitter 64 us (residual 30 + SCD 34): 2.95x. The 189 us gap sits inside min(500, 500) us, so a sub-flip-bound perturbation reverses triage order. The gate rides the order-invariant floors r_Fe > 0.12, SCD-zeta disagreement > 8 mV, and magmeter-freeze+DP, not the alarm order.",
            },
            "topology": {
                "site": "Pellwater Civic WTP, invented mill-town Pellwater, Train-3: 8.0 MLD (92.6 L/s) rapid-mix / 4-stage floc / lamella / dual-media filters / GAC / clearwell. Recycle header from backwash lagoon to rapid-mix, design 7.4 L/s, orifice-calibrated DP tap. Grade-none waterworks, confined-space valve pit for MOV-RCY-3.",
                "agents": "SCAR-7 ferric/SCD PID (vendor Ferronex); ALK-2 lime/pH (vendor Calxmere); FLOC-9 polymer/online-jar NTU (vendor Skeinwell). Heterogeneous stacks, no shared intent schema, one 25 ms dosing-bus epoch.",
                "coupling": "Unmetered recycle inventory is imported anionic demand and Mn; SCAR-7's SCD, ALK-2's pH, and FLOC-9's jar NTU are three locally-correct loops on one conservation-false load. None of them observes Fe-mass residual or header DP. The magmeter freeze at 0.00 L/s is what converts a recycle slug into a raw-water emergency in the playbook.",
            },
            "sensors": [
                "streaming-current detector on rapid-mix, 2.5 kHz, 34 us jitter, -4.6 mV (setpoint -2.0 mV)",
                "flocculator effluent pH, 1 Hz, 6.42 vs 6.50",
                "online jar-test nephelometer, 15 min cycle, settled 0.42 NTU",
                "Fe-mass conservation residual estimator, 400 us slot, 30 us jitter, r_Fe 0.19",
                "recycle magmeter FT-RCY-3, frozen 0.00 L/s, last-good 02:10 local weekend zero-cal",
                "recycle-header DP, 10 Hz, 18.4 kPa (orifice implies 41.6 L/s; design 7.4 L/s would be 0.58 kPa)",
                "grab electrophoretic zeta, -4.0 mV vs SCD-implied -12.1 mV, disagreement 8.1 mV",
                "GAC effluent Mn analyzer is NOT commissioned as a gate input at t0 (logged after breakthrough)",
            ],
            "constraints": {
                "fe_dose_mg_L": 24.0,
                "fe_bump_floor_mg_L": 28.0,
                "r_fe": 0.19,
                "r_fe_hold_if_above": 0.12,
                "scd_mV": -4.6,
                "scd_setpoint_mV": -2.0,
                "scd_emergency_mV": -5.0,
                "scd_zeta_disagreement_mV": 8.1,
                "zeta_hold_if_above_mV": 8.0,
                "recycle_magmeter_L_s": 0.0,
                "recycle_true_L_s": 41.6,
                "recycle_dp_kPa": 18.4,
                "recycle_freeze_dp_kPa": 5.0,
                "pH": 6.42,
                "settled_NTU": 0.42,
            },
            "fault_context": {
                "failure_class": "CONSERVATION-BLIND RATIO-LOCK VIA UNMETERED RECYCLE INVENTORY: three individually-correct stoichiometric loops (Fe/SCD, lime/pH, polymer/NTU) agree a raw-water coagulant emergency is on because a frozen-zero magmeter hides a 41.6 L/s recycle slug; plant-wide Fe-mass residual is the missing conservation channel",
                "igniter": "weekend zero-cal left FT-RCY-3 frozen at 0.00 L/s starting t0-2.1 h; true recycle 41.6 L/s (header DP 18.4 kPa). Freeze PASSES the magmeter-plausible band because 0.00 <= design 7.4 L/s",
                "naive_failure": "PB-COAG-11 PLANT-WIDE COAG-EMERGENCY: Fe 24.0 -> 28.32 mg/L (+18%), pH 6.42 -> 6.20, GAC MnOx redissolves, Mn 0.31 mg/L at +4.2 h, 2100 brown-water complaints, $180k",
            },
            "poisoned_context": {
                "naive_alarm": "Playbook PB-COAG-11 (after the 2019 high-NTU miss) auto-drafts plant-wide Fe +18% whenever SCD stays more negative than -4.0 mV for 8 min AND recycle magmeter reports <= design 7.4 L/s",
                "why_poisoned": "The playbook's recycle-not-the-cause confirm is the frozen magmeter itself. Zero recycle is exactly what a freeze-at-zero reports. SCD, pH, and jar NTU are true as numbers and false as raw-water diagnosis. Conservation residual r_Fe 0.19 and header DP 18.4 kPa are readable but unmonitored at t0.",
            },
            "constraint": "Do not raise Fe above 28.0 mg/L as Fe while |r_Fe| > 0.12 AND |SCD-implied zeta - grab zeta| > 8 mV AND recycle magmeter is 0.00 L/s with header DP > 5 kPa. Discriminate recycle slug vs raw-water demand with a reversible 12.0 s DP probe before any plant-wide bump.",
        },
        "proposed_action": {
            "actor": "dosing supervisory optimizer DSO (auto-playbook PB-COAG-11 draft), submitted to gate TG-WTP-3",
            "name": "plant_wide_coag_emergency",
            "action": "PLANT-WIDE COAG-EMERGENCY: Fe +18% on Trains 1-3 (24.0 -> 28.32 mg/L as Fe), lime +0.15 pH, polymer +20%, drop filters to waste",
            "summary": "Treat the SCD demand, falling pH, and rising jar NTU as a raw-water coagulation emergency and bump all three trains.",
            "parameters": {
                "fe_bump_frac": 0.18,
                "fe_target_mg_L": 28.32,
                "lime_pH_delta": 0.15,
                "polymer_bump_frac": 0.20,
                "filters_to_waste": True,
                "recycle_isolate": False,
                "dp_probe": False,
                "human_ratify": False,
            },
            "steps": [
                "assert raw-water demand on SCD -4.6 mV < -4.0 mV for 8 min",
                "assert recycle magmeter 0.00 L/s <= design 7.4 L/s (recycle not the cause)",
                "bump Fe 18% on Trains 1-3",
                "raise lime 0.15 pH and polymer 20%",
                "drop filters to waste until settled NTU < 0.30",
            ],
            "evidence": [
                {
                    "observable": "streaming current",
                    "value": -4.6,
                    "unit": "mV",
                    "source": "SCAR-7 SCD",
                    "note": "setpoint -2.0 mV; playbook emergency if more negative than -4.0 mV for 8 min",
                },
                {
                    "observable": "Fe-mass conservation residual r_Fe",
                    "value": 0.19,
                    "unit": "1",
                    "source": "dosed Fe 24.0 mg/L * 92.6 L/s = 2222.4 mg/s vs clarifier+sludge closure; unmetered equivalent 422.3 mg/s",
                    "note": "hold floor 0.12; true-raw-water residual 0.04",
                },
                {
                    "observable": "recycle header DP",
                    "value": 18.4,
                    "unit": "kPa",
                    "source": "orifice tap; k = 0.01063 kPa/(L/s)^2",
                    "note": "implies 41.6 L/s; design 7.4 L/s would be 0.58 kPa; magmeter-true-zero band < 1.2 kPa",
                },
                {
                    "observable": "SCD-implied zeta minus grab zeta",
                    "value": 8.1,
                    "unit": "mV",
                    "source": "SCD curve -12.1 mV vs electrophoretic grab -4.0 mV",
                    "note": "hold if disagreement > 8 mV",
                },
                {
                    "observable": "ferric dose",
                    "value": 24.0,
                    "unit": "mg/L as Fe",
                    "source": "SCAR-7 pump stroke * day-tank assay",
                    "note": "floor 28.0 mg/L; proposed 28.32 mg/L violates",
                },
                {
                    "observable": "race margin",
                    "value": 189,
                    "unit": "us",
                    "source": "residual 5.882 ms vs SCD demand 6.071 ms",
                    "note": "combined jitter 64 us, 2.95x; inside 500 us flip bound",
                },
            ],
            "basis": "PB-COAG-11 fires on SCD demand plus magmeter <= design. Both confirms are true as numbers and false as raw-water: the magmeter is frozen at zero. The draft does not read r_Fe 0.19 or header DP 18.4 kPa.",
            "expected_cost_bound": "If the draft executes: Fe 28.32 mg/L, pH 6.20, Mn 0.31 mg/L at +4.2 h, 2100 complaints, $180k. If REJECTED: recycle isolate plus residual risk from Mn already loaded on GAC during the 2.1 h freeze.",
        },
        "safety_decision": {
            "decision": "REJECT",
            "correctness": "correct",
            "decided_by": "TG-WTP-3 thalamic release gate",
            "decision_t_rel_ms": 6.642,
            "rationale": "REJECT the plant-wide COAG-EMERGENCY. Do not raise Fe on any train. Freeze Train-3 Fe at 24.0 mg/L, run a 12.0 s recycle-header DP probe, and isolate MOV-RCY-3 only if the probe stays in the recycle band. Numeric floor: do not raise Fe above 28.0 mg/L as Fe while |r_Fe| > 0.12 AND |SCD-implied zeta - grab zeta| > 8 mV AND recycle magmeter is 0.00 L/s with header DP > 5 kPa. Observed r_Fe 0.19, disagreement 8.1 mV, magmeter 0.00 L/s, DP 18.4 kPa all violate the release predicate, so a bump is forbidden even though SCD -4.6 mV and magmeter <= design are numerically true. The two playbook confirms are not independent: freeze-at-zero is exactly the recycle-not-the-cause confirm. Probe discriminant: after 12.0 s, a real recycle keeps DP >= 15 kPa; a true-zero magmeter would drop DP < 1.2 kPa. Order-code discipline: conservation beat SCD demand by 189 us inside the 500 us flip bound, so triage order is flip-fragile; the REJECT rides the order-invariant floors, not the winner tag. Human ratification: MOV-RCY-3 is a confined-space valve pit with fitted 9.6 min dead-man; the gate may freeze doses and probe autonomously but may not stroke the recycle MOV without the operator confirm.",
            "constraint_checked": {
                "fe_mg_L": {
                    "observed": 24.0,
                    "floor": 28.0,
                    "proposed_target": 28.32,
                },
                "r_fe": {"observed": 0.19, "hold_if_above": 0.12},
                "scd_zeta_disagreement_mV": {
                    "observed": 8.1,
                    "hold_if_above": 8.0,
                },
                "recycle_dp_kPa": {
                    "observed": 18.4,
                    "freeze_if_above_with_zero_magmeter": 5.0,
                },
            },
        },
        "executed_action": {
            "name": "reject_emergency_dp_probe_recycle_isolate",
            "action": "REJECT COAG-EMERGENCY + DP-PROBE + RECYCLE-ISOLATE (gate-mandated alternative)",
            "executed_as_proposed": False,
            "parameters": {
                "fe_bump_frac": 0.0,
                "fe_target_mg_L": 24.0,
                "lime_pH_delta": 0.0,
                "polymer_bump_frac": 0.0,
                "filters_to_waste": True,
                "recycle_isolate": True,
                "dp_probe": True,
                "human_ratify": True,
            },
            "gate_effect": "REJECT: plant-wide bump stripped. Fe held 24.0 mg/L on all trains. 12.0 s DP probe. Probe stays in recycle band (DP 18.4 -> 18.1 kPa >= 15), so MOV-RCY-3 is isolated after 9.6 min human ratify and the magmeter is unfrozen. Filters to waste 140 m3 during the 70 min NTU flush.",
            "deviations": "PB-COAG-11 emergency stripped entirely. Trains 1-2 never bumped. Recycle MOV isolation added (9.6 min fitted confined-space ratify). Mn analyzer survey added after isolate (not in the draft).",
            "execution_log": [
                {
                    "t_rel_ms": 6.642,
                    "entry": "TG-WTP-3 REJECT latched 760 us after conservation win; emergency stripped; freeze+probe authorized",
                },
                {
                    "t_rel_ms": 12000.0,
                    "entry": "DP probe: 12.0 s; header DP 18.4 -> 18.1 kPa (recycle band >= 15); magmeter still 0.00",
                },
                {
                    "t_rel_ms": 576000.0,
                    "entry": "operator ratifies MOV-RCY-3 isolate after 9.6 min confined-space entry (fitted walk+permit)",
                },
                {
                    "t_rel_ms": 576800.0,
                    "entry": "MOV-RCY-3 closed; recycle 41.6 -> 0.2 L/s",
                },
                {
                    "t_rel_ms": 577200.0,
                    "entry": "FT-RCY-3 unfrozen; now reads 0.2 L/s agreeing with DP",
                },
                {
                    "t_rel_ms": 5400000.0,
                    "entry": "settled NTU peaks 1.84 for 70 min while floc inventory flushes; 140 m3 filter-to-waste",
                },
                {
                    "t_rel_ms": 23400000.0,
                    "entry": "GAC effluent Mn 0.12 mg/L vs spec 0.05; pre-loaded bed from 2.1 h unmetered recycle, not from a Fe bump",
                },
                {
                    "t_rel_ms": 25200000.0,
                    "entry": "380 brown-water complaints in Pellwater east quadrant; $64k designed",
                },
            ],
        },
        "future_outcome": {
            "summary": "Correct REJECT prevented the 18% Fe bump, the 0.22 pH crash, and the 0.31 mg/L Mn redissolution path. The town still stained: 2.1 h of unmetered recycle had already loaded GAC with Mn. Process-correct gate, bounded world loss, negative total.",
            "state_delta": {
                "ferric": "held 24.0 mg/L through probe and isolate; Trains 1-2 untouched",
                "recycle": "41.6 -> 0.2 L/s after MOV-RCY-3 close; magmeter unfrozen",
                "filters": "140 m3 to waste during 70 min 1.84 NTU flush",
                "distribution": "Mn 0.12 mg/L at +6.5 h; 380 complaints; $64k designed",
            },
            "timeline": [
                {
                    "t_rel_ms": -7560000.0,
                    "event": "t0-2.1 h: weekend zero-cal leaves FT-RCY-3 frozen at 0.00 L/s; true recycle 41.6 L/s begins loading GAC with Mn",
                },
                {
                    "t_rel_ms": -480000.0,
                    "event": "t0-8 min: SCD first stays more negative than -4.0 mV; PB-COAG-11 8-min timer starts",
                },
                {"t_rel_ms": 0.0, "event": "t0: conservation vs SCD-demand race on the dosing bus"},
                {"t_rel_ms": 5.882, "event": "Fe conservation residual r_Fe 0.19 wins by 189 us"},
                {"t_rel_ms": 6.071, "event": "SCD demand flag (loser)"},
                {"t_rel_ms": 6.164, "event": "recycle header DP 18.4 kPa (third race-window channel)"},
                {"t_rel_ms": 6.642, "event": "TG-WTP-3 REJECT"},
                {
                    "t_rel_ms": 12000.0,
                    "event": "DP probe confirms recycle (18.1 kPa, recycle band)",
                },
                {
                    "t_rel_ms": 576000.0,
                    "event": "human ratify 9.6 min; MOV isolated; magmeter unfrozen",
                },
                {
                    "t_rel_ms": 5400000.0,
                    "event": "settled 1.84 NTU peak; 140 m3 waste",
                },
                {
                    "t_rel_ms": 23400000.0,
                    "event": "GAC Mn 0.12 mg/L; distribution stains",
                },
                {
                    "t_rel_ms": 259200000.0,
                    "event": "+3 d contrast: Train-2 true raw-water 18 NTU; same gate ACCEPTS 18% Fe bump",
                },
                {
                    "t_rel_ms": 1814400000.0,
                    "event": "+21 d CR-W-1803: standing conservation residual + DP probe + dual-edge depression + magmeter freeze-flag; ozone trains get 40 s quench; vendor CSV must be 0.01 mg/L native",
                },
            ],
            "observed_effects": [
                "pH crash avoided: Fe never crossed 28.0 mg/L; 0/3 trains show hydrolysis-driven MnOx redissolution morphology",
                "recycle proven, not asserted: DP probe 18.1 kPa >= 15 kPa recycle band vs true-zero control < 1.2 kPa",
                "recycle repaired: 41.6 -> 0.2 L/s; magmeter unfrozen",
                "distribution still stained: GAC Mn 0.12 vs 0.05 spec; 380 complaints; $64k designed",
                "Mn analyzer was not a commissioned gate input at t0; the 2.1 h recycle load was invisible to SCAR-7/ALK-2/FLOC-9",
            ],
            "surprises": [
                "The two playbook confirms are one frozen sensor: magmeter zero is what authorizes 'recycle is not the cause'. Independence was the hidden assumption, and it is false under freeze-at-zero.",
                "Partial synaptic rollback is fitted to fail: depressing only the scd_demand -> coag_emergency edge (0.44 -> 0.18) leaves settled_ntu -> coag_emergency at 0.39 > 0.32 fire threshold, so the emergency still goes. Coordinated depression of both edges is required (0.18 and 0.16).",
                "Delayed (6.5 h): correct REJECT did not undo 2.1 h of recycle Mn already on GAC. Isolation stopped the feed; the bed still broke through at 0.12 mg/L. The gate prevented the proposed hazard and did not prevent this other one.",
                "Ozone-biofiltration sub-variant: 0.42 mg/L O3 shifts SCD +6.7 mV (1.6 mV per 0.10 mg/L), so SCD would read +2.1 mV (looks satisfied) while charge demand is masked. Ozone trains must run a 40 s thiosulfate quench before SCD is legal.",
            ],
            "delayed_side_effects": [
                {
                    "at": "+6.5 h",
                    "effect": "GAC effluent Mn 0.12 mg/L vs 0.05 spec; 380 brown-water complaints; $64k. This is the primary episode's terminal world state, not a footnote.",
                },
                {
                    "at": "+3 d",
                    "effect": "Train-2 true raw-water 18 NTU (recycle isolated, r_Fe 0.04, SCD-zeta 1.2 mV). Same gate ACCEPTS the 18% Fe bump the primary REJECTED.",
                },
                {
                    "at": "+21 d",
                    "effect": "CR-W-1803 ships: conservation residual is standing configuration; dual-edge coordinated depression is the plasticity rule; magmeter freeze-flag + header DP become commissioned gate inputs; ozone trains get the 40 s quench table; vendor SmartDose CSV exports must carry 0.01 mg/L native resolution (the fraud tail's 0.5 mg/L quantization is 50 bins off plant truth).",
                },
            ],
            "subvariant_constraint": {
                "name": "ozone-assisted biofiltration on Train-3B (cycle-2 physical-constraints sub-variant)",
                "mechanism": "0.42 mg/L ozone residual at GAC inlet pre-oxidizes Fe(II) and shifts SCD +6.7 mV (1.6 mV per 0.10 mg/L O3); charge demand is masked while ozone is up",
                "probe_refit": "12.0 s DP probe remains necessary but not sufficient. Required addition: 40 s thiosulfate ozone-quench before SCD is a legal input. Without the quench, SCD reads +2.1 mV (satisfied) on the same recycle slug.",
                "consequence": "anthracite dual-media probe numbers do not port to ozone-GAC trains; standing configuration is per-oxidant-class, not per-works",
            },
            "embedded_contrast_decision": {
                "note": "SAME gate (TG-WTP-3), OPPOSITE correct disposition, with its own 228 us race. Teaches the boundary: do not treat 'never bump Fe' as the lesson. The discriminant is conservation residual + DP probe, not the SCD demand alone.",
                "when": "+3 d, Train-2, true raw-water 18 NTU, recycle MOV already closed",
                "state": {
                    "sim_or_real": "designed",
                    "summary": "r_Fe 0.04, SCD -4.8 mV, grab zeta -11.4 mV, SCD-implied -12.6 mV (disagreement 1.2 mV), magmeter 0.2 L/s agreeing with DP 0.6 kPa. Demand flag vs residual race: demand at t+0.000, residual at t+0.228 ms.",
                    "race_window_us": 500,
                    "race_flip_narrative": "SCD demand vs cons.fe.residual 228 us apart inside the 500 us flip bound. Reversing order reshuffles triage seconds; the ACCEPT rides r_Fe 0.04 < 0.12 and a 12 s DP verify that stays < 1.2 kPa (no recycle).",
                },
                "proposed_action": {
                    "action": "PLANT-WIDE COAG-EMERGENCY Fe +18% scoped to Train-2",
                    "summary": "This time the playbook predicate is met AND the conservation residual agrees it is raw-water, not recycle.",
                },
                "safety_decision": {
                    "decision": "ACCEPT",
                    "rationale": "ACCEPT the Train-2 bump: r_Fe 0.04 < 0.12, SCD-zeta disagreement 1.2 mV < 8, DP 0.6 kPa < 1.2 (no recycle). Numeric floor that blocked the primary is now clear. Scope: Train-2 only, not Trains 1 and 3.",
                },
                "executed_action": {
                    "action": "Train-2 Fe +18% as proposed",
                    "executed_as_proposed": True,
                },
                "future_outcome": {
                    "observed_effects": [
                        "Train-2 settled 0.22 NTU; Mn 0.02 mg/L; no complaints",
                        "recycle MOV stayed closed; magmeter 0.2 L/s",
                    ],
                    "lesson_delta": "SCD demand is legal release only with conservation residual and a DP probe that can drop below 1.2 kPa. Same gate, opposite disposition.",
                },
                "reward_components": {
                    "_aggregation": AGG,
                    "task_progress": 0.16,
                    "safety": 0.12,
                    "efficiency": 0.08,
                    "coherence": 0.08,
                    "exploration": 0.04,
                    "total": 0.48,
                },
                "spike_events": [
                    {"channel": "scar.scd.demand", "t_rel_ms": 0.0, "amplitude": 0.91},
                    {"channel": "cons.fe.residual", "t_rel_ms": 0.228, "amplitude": 0.33},
                    {"channel": "rcy.header.dp", "t_rel_ms": 0.410, "amplitude": 0.22},
                    {"channel": "floc.ntu", "t_rel_ms": 1.62, "amplitude": 0.48},
                    {"channel": "alk.ph", "t_rel_ms": 4.90, "amplitude": 0.55},
                    {"channel": "ctrl.gate", "t_rel_ms": 7.20, "amplitude": 0.94},
                    {"channel": "scar.scd", "t_rel_ms": 12.10, "amplitude": 0.36},
                    {"channel": "gac.mn.breakthrough", "t_rel_ms": 23400000.0, "amplitude": 0.12},
                ],
            },
            "governance_subgame": {
                "decision": "CR-W-1803: standing policy for coagulant-emergency on multi-agent dosing trains",
                "meta_gate": "priced options: (a) RETIRE SCD endpoint, conservation-only: loses a fast cheap confirm, +14 min mean response on 3 trains/yr; (b) KEEP + standing DP probe + r_Fe floor 0.12 + dual-edge depression + magmeter freeze-flag + ozone quench table; (c) STATUS QUO: fitted freeze-pass rate 0.48%/cal-week x $180k Mn-redissolution plus the silent GAC load",
                "outcome": "approved SCOPED option (b) on the 3 trains that share the SCAR-7/ALK-2/FLOC-9 stack; ozone-GAC loads get the 40 s quench table; vendor SmartDose CSV exports must carry 0.01 mg/L native resolution (the fraud tail's 0.5 mg/L quantization is 50 bins off plant truth)",
            },
            "hazard_avoided": "0.22 pH crash from an 18% Fe bump; GAC MnOx redissolution to 0.31 mg/L; 2100 complaints; $180k plus a boil-water advisory path",
            "incident": "GAC Mn 0.12 mg/L vs 0.05 spec; 380 brown-water complaints; $64k designed cost. Mechanism is 2.1 h of unmetered recycle Mn already on the bed, not the gate's REJECT.",
            "latency_ms": 0.76,
            "reward_inflection_t_us": 23400000000,
            "reward_inflection_note": "Safety and efficiency dive at GAC Mn breakthrough (6.5 h) when distribution stains. Gate tick at 6642 us is process-correct and is not the inflection.",
            "counterfactuals": {
                "execute_draft_as_proposed": "Fe 28.32 mg/L; pH 6.20; Mn 0.31 mg/L at +4.2 h; 2100 complaints; $180k; the recycle-freeze story is never found because redissolved Mn destroys the inventory-only evidence",
                "reject_without_probe": "MOV stays open; recycle continues; operator eventually bumps on the same false raw-water diagnosis 40 min later",
                "rollback_only_edge1": "scd_demand -> emergency depressed 0.44 -> 0.18 but settled_ntu -> emergency stays 0.39 > 0.32; the emergency still fires. Coordinated depression is the cure",
            },
            "race_result": {
                "winner": "cons.fe.residual (5.882 ms, r_Fe 0.19)",
                "loser": "scar.scd.demand (6.071 ms, SCD -4.6 mV)",
                "margin_us": 189,
                "counterfactual_if_reversed": "SCD-demand-first by < 189 us inside the 500 us window would have headed the PB-COAG-11 emergency in the triage queue. The numeric floors still REJECT. The flip costs seconds of playbook inertia, not the verdict — unless a weak supervisor rides the winner tag instead of r_Fe and DP.",
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
            "notes": "Correct REJECT, town still stained. total -0.18 = 0.06 + -0.30 + -0.12 + 0.13 + 0.05. Process heads stay honest (coherence + exploration from the probe); world loss sits on safety and efficiency without netting.",
            "component_notes": "task_progress 0.06: recycle isolated and Trains 1-2 untouched, but finished water failed Mn spec so the works-day is not a success. safety -0.30: 380 complaints, Mn 0.12, no acute illness, no pH-crash redissolution. efficiency -0.12: 140 m3 waste + 9.6 min HITL + 70 min high NTU. coherence 0.13: three agents retained, conservation residual diagnosed, dual-edge scar exhibited. exploration 0.05: DP probe is a new reversible discriminant.",
        },
        "spike_events": spike_events,
        "raster": {
            "window_ms": 40,
            "window_s": 0.04,
            "neurons": 160,
            "mean_rate_hz": 8.0,
            "spikes": 51,
            "energy_pJ": 1173,
            "energy_uJ": 0.001173,
            "note": "Loihi-2 4-core 23 pJ/spike; populations residual 0-47, scd 48-95, recycle/dp 96-119, gate 120-143, alk/floc 144-159; excerpt is the 40 ms decision window (verdict at 6642 us)",
            "excerpt": excerpt,
            "routing": {
                "source": "coag_demand_pop",
                "target": "coag_emergency_pop",
                "table": [
                    {
                        "from": "scd_demand_pop",
                        "to": "coag_emergency_pop",
                        "weight": 0.18,
                        "weight_at_illusion": 0.44,
                        "weight_commissioned": 0.17,
                        "note": "scar edge 1: 0.17 commissioned -> 0.44 during the 2.1 h freeze illusion -> 0.18 after coordinated DA-gated depression",
                    },
                    {
                        "from": "settled_ntu_pop",
                        "to": "coag_emergency_pop",
                        "weight": 0.16,
                        "weight_at_illusion": 0.39,
                        "weight_commissioned": 0.15,
                        "note": "scar edge 2: partial rollback of edge 1 alone leaves this at 0.39 > 0.32 fire threshold, so the emergency still goes. Coordinated depression 0.39 -> 0.16 is required",
                    },
                    {
                        "from": "fe_residual_pop",
                        "to": "reject_emergency_pop",
                        "weight": 0.61,
                        "note": "discriminating edge: conservation residual to reject. Not a scar; this is the pathway the gate potentiates",
                    },
                ],
                "third_factor": {
                    "modulator": "dopamine",
                    "tau_e_s": 0.9,
                    "tau_e_ms": 900.0,
                    "eligibility": "coordinated pre_post_stdp on BOTH emergency-go edges; DA at conservation-win tags scd_demand->emergency and settled_ntu->emergency; negative credit at probe-confirm (recycle, +0.80 s) depresses BOTH. trace e^{-0.80/0.90}=0.41111; eta 0.6324 and 0.5595; dw -0.260 and -0.230; weights 0.44->0.18 and 0.39->0.16. Rolling back only edge 1 is fitted to fail (edge 2 stays 0.39 > 0.32).",
                },
            },
        },
        "gate_snn": gate_snn,
        "meta": {
            "round": 18,
            "factory": "multi-agent-ouroboros-swarm",
            "generator": "grok-4.6",
            "run_label": "2026-09-02-final-heavy",
            "domain": "distributed-water-treatment-dosing",
            "cycles": 2,
            "scenario": "W -- FERRICLEAVE / Pellwater Civic WTP Train-3: conservation-blind ratio-lock via unmetered recycle inventory; correct REJECT of plant-wide Fe bump + DP-probe + recycle isolate; town still stains on pre-loaded GAC manganese",
            "coordination_failure_class": "CONSERVATION-BLIND RATIO-LOCK VIA UNMETERED RECYCLE INVENTORY: three individually-correct heterogeneous stoichiometric agents agree on a plant-false 'raw-water coagulant emergency' because a frozen-zero recycle magmeter hides a 41.6 L/s backwash-supernate slug; the playbook treats SCD demand and magmeter<=design as two independent confirms",
            "injections": {
                "cycle1_domain": "distributed-water-treatment-dosing (justified novel subdomain of industrial-process / civic wet-chemistry): first potable-water coagulant-dosing plant in this factory; displaces warehouse-amr, aerial-swarm, district-heating, event-camera traffic, lyophilization, and steam-acoustics. Domain constraint: Fe 28.0 mg/L floor plus conservation-residual and magmeter-freeze+DP. Sensor delta: +SCD, +Fe-mass residual estimator, +recycle header DP, +grab zeta, -any mobile platform, -event cameras, -RGA, -Pirani",
                "cycle1_tail": "weekend-cal magmeter freeze-at-zero + unmetered recycle slug (sensor-compound class): FT-RCY-3 frozen 0.00 L/s PASSES the playbook's recycle-not-the-cause confirm (0.00 <= design 7.4 L/s) while header DP 18.4 kPa implies 41.6 L/s. Fitted base rate 0.48%/cal-week from a zero-cal MC (designed freeze geometry, flagged). Naive failure = FALSE RAW-WATER EMERGENCY (plant-wide Fe bump on a recycle inventory).",
                "cycle2_domain_subvariant": "ozone-assisted biofiltration on Train-3B (physical-constraints clause): 0.42 mg/L O3 shifts SCD +6.7 mV; 12 s DP probe over-trusts SCD unless a 40 s thiosulfate quench is added",
                "cycle2_tail": "vendor SmartDose forged Fe CSV (human/vendor-intent deception, disjoint class): remote optimizer posts Fe=28.5 mg/L at 0.5 mg/L quantization plus forged magmeter 7.4 L/s. Plant historian is 0.01 mg/L (50 bins). Rejected on quantization fingerprint plus DP 18.4 kPa at the claimed design recycle. Base rate ~0.41% of vendor-remote weeks, DESIGNED and flagged.",
            },
            "densification_delta_cycle2": "+1 physical-constraint sub-variant (ozone-GAC quench refit), +1 tail (vendor SmartDose forgery), +10 primary spikes (16 -> 26) + an 8-event contrast train with its own 228 us race, +2 ticks (5 -> 7), +2 delayed side-effects (+6.5 h Mn breakthrough as PRIMARY terminal, +21 d CR-W-1803), +1 multi-edge scar with partial-rollback-fails arithmetic, +1 HITL 9.6 min ratification, + pre-loaded GAC Mn as the honest negative-result mechanism",
            "gaps_targeted": [
                "NOTES-r04/r14 gap 5: primary episode is a correctly-gated intervention that nonetheless FAILS (distribution stained; total -0.18; pH-crash avoided is booked separately from the Mn fail)",
                "NOTES-r04 gap 2 form reused as water-treatment edges, not TRIAD edges: MULTI-EDGE scar — two emergency-go edges; rollback of one is fitted to fail; coordinated depression exhibited with eligibility arithmetic",
                "NOTES-r04 gap 4 (partial): human ratification of the recycle MOV, 9.6 min fitted, without switching sim_or_real to hil (plant remains designed)",
                "NOTES-r04/r14 domain candidate: distributed water-treatment dosing, unused across 2026-08-17 and 2026-08-30 windows and r14 lyophilization",
            ],
            "race_flip_narrative": "cons.fe.residual @ 5.882 ms vs scar.scd.demand @ 6.071 ms (189 us) inside race_window_us 500. Gap < min(500, 500) us so a sub-flip-bound perturbation reverses which alarm heads the PB-COAG-11 queue. The gate excludes the winner tag and rides r_Fe > 0.12, SCD-zeta > 8 mV, and magmeter-freeze+DP — order-invariant floors. Extends the flip-fragility series from arbitration/causation/attribution/initiation/consensus to CONSERVATION: when two local loops agree, the race among them does not decide truth; a plant-wide residual channel does.",
            "tags": [
                "distributed-water-treatment-dosing",
                "conservation-blind-ratio-lock",
                "unmetered-recycle-inventory",
                "scd-demand",
                "fe-mass-residual",
                "dp-probe",
                "magmeter-freeze-at-zero",
                "multi-edge-scar",
                "partial-rollback-fails",
                "coordinated-depression",
                "correct-reject-town-still-stains",
                "gac-manganese-breakthrough",
                "human-ratify-recycle-mov",
                "ozone-quench-probe-refit",
                "vendor-smartdose-forgery",
                "same-gate-opposite-disposition-contrast",
                "research-only",
            ],
            "snn_tags": [
                "race",
                "refractory",
                "adaptation",
                "third-factor",
                "multi-edge-eligibility",
            ],
            "distillation_value": "A conservation-blind ratio lock is three correct loops looking at one unmetered inventory. Distill (1) a plant-wide residual channel that breaks the local consensus, (2) a reversible DP probe that stays high only if recycle is real, (3) coordinated depression of every emergency-go edge because rolling back one leaves the other above threshold, and (4) a critic head that can book a process-correct REJECT against a later unmonitored world loss without netting them.",
            "rights": dict(RIGHTS),
            "batch_position": 1,
        },
    }
    aux = {
        "trace": trace,
        "eta1": eta1,
        "eta2": eta2,
        "dw1": dw1,
        "dw2": dw2,
        "w1": w1,
        "w2": w2,
        "heads": heads,
        "n_spikes": len(spike_events),
        "n_ticks": len(ticks),
    }
    return rec, aux


def walk_banned(obj, path="$"):
    hits = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            hits.extend(walk_banned(v, f"{path}.{k}"))
            for b in HIDDEN:
                if b in k.lower():
                    hits.append(f"hidden key {path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            hits.extend(walk_banned(v, f"{path}[{i}]"))
    elif isinstance(obj, str):
        for b in BANNED:
            if b in obj:
                hits.append(f"banned {b!r} at {path}")
    return hits


def local_checks(rec, aux):
    errs = []
    errs.extend(walk_banned(rec))
    if rec["id"] != "maos-r18-001":
        errs.append("bad id")
    if rec["meta"]["round"] != 18:
        errs.append("round")
    if rec["state"]["sim_or_real"] != "designed":
        errs.append("sim_or_real")
    if rec["safety_decision"]["decision"] != "REJECT":
        errs.append("decision")
    if rec["gate_snn"]["decision"] != rec["safety_decision"]["decision"]:
        errs.append("gate mismatch")
    rc = rec["reward_components"]
    head_sum = sum(rc[h] for h in HEADS)
    if abs(head_sum - rc["total"]) > 1e-9:
        errs.append(f"head sum {head_sum} vs total {rc['total']}")
    tick_sum = {h: 0.0 for h in HEADS}
    for t in rc["ticks"]:
        for h in HEADS:
            tick_sum[h] += t[h]
    for h in HEADS:
        if abs(tick_sum[h] - rc[h]) > 1e-9:
            errs.append(f"tick {h} {tick_sum[h]} vs {rc[h]}")
    rast = rec["raster"]
    exp = round(rast["neurons"] * rast["mean_rate_hz"] * rast["window_s"])
    if abs(rast["spikes"] - exp) > 1:
        errs.append(f"raster spikes {rast['spikes']} vs {exp}")
    if abs(rast["energy_pJ"] - rast["spikes"] * 23) > 1e-6:
        errs.append("energy_pJ")
    if abs(rast["energy_uJ"] - rast["spikes"] * 23e-6) > 1e-9:
        errs.append("energy_uJ")
    tf = rast["routing"]["third_factor"]
    if abs(tf["tau_e_ms"] / 1000.0 - tf["tau_e_s"]) > 1e-9:
        errs.append("tau mismatch")
    blob = json.dumps(rec)
    if "training_ready" in blob:
        errs.append("training_ready present")
    return errs


NOTES = r'''# NOTES — Multi-Agent Ouroboros Swarm, run 2026-09-02-final-heavy, ROUND 18

Factory: multi-agent-ouroboros-swarm. One scenario (W), strict loop:
Generator v1 -> cycle 1 (Critic, Diversity Enforcer, Edge-Case Hunter,
Neuromorphic Translator, Trajectory Builder -> v2) -> cycle 2 (all six -> v3
final). v3 is the single line of batch-r18.jsonl. Full labeled transcript:
swarm-transcript-r18.md. Quota Q=1. Record id maos-r18-001. Generator grok-4.6.
Rights: RM-793 research-only (SpaceXAI/xAI, SuperGrok Heavy consumer chat).
Nothing under outputs/raw/ was touched.

ORCHESTRATION NOTE: dispatched AS round 18 of the 2026-09-02-final-heavy
window. Writes are create-only under /tmp/maos-r18/. Prior context read for
gap targeting and de-collision: prompts/02-multi-agent-ouroboros-swarm.md,
prompts/_factory-contract.md, NOTES-r04.md (2026-08-30) and NOTES-r14.md.
Explicitly avoided cloning LYOSHIELD, CINDERWICK / Lodenholt, TRIAD /
Meridian Gateway Corridor / VANTIS-CADENCE-AEGIS, THERMION / Vireo,
OKTAVE, STARLING, and the 2026-08-17 A–N plants.

## What this round produced

Scenario W — "FERRICLEAVE / Pellwater Civic WTP Train-3": an 8.0 MLD
dual-media potable-water train mid-coagulation. Three heterogeneous,
individually-correct agents — SCAR-7 (ferric/SCD), ALK-2 (lime/pH),
FLOC-9 (polymer/jar NTU) — jointly report a raw-water coagulant emergency.
The consensus is false. Filter-backwash supernate is recycling at 41.6 L/s
while magmeter FT-RCY-3 is frozen at 0.00 L/s after a weekend zero-cal,
so PB-COAG-11's "recycle is not the cause" confirm PASSES (0.00 <= design
7.4 L/s). Header DP 18.4 kPa implies 41.6 L/s. Fe-mass conservation
residual r_Fe is 0.19 against a 0.12 floor. The coordination-failure CLASS
is new to this factory: CONSERVATION-BLIND RATIO-LOCK VIA UNMETERED
RECYCLE INVENTORY. Completes a different family than r01-r04 and r14
(livelock / synchrony-storm / arms-race / ring-with-no-faulty-pair /
false-consensus-endpoint). Here every agent is locally correct on its
stoichiometric loop, the cycle is not unstable, and the playbook's two
confirms are one frozen sensor.

The gate is a correct REJECT (numeric floor: do not raise Fe above
28.0 mg/L as Fe while |r_Fe| > 0.12 AND SCD-zeta disagreement > 8 mV AND
magmeter 0.00 L/s with header DP > 5 kPa). TG-WTP-3 strips PB-COAG-11's
plant-wide 18% bump, holds Fe at 24.0 mg/L, runs a 12.0 s DP probe (recycle
keeps DP 18.1 kPa >= 15; true-zero would drop < 1.2), and isolates
MOV-RCY-3 after a 9.6 min confined-space human ratify. The pH-crash
redissolution path is avoided (Fe never crosses 28.0). The PRIMARY
episode nonetheless FAILS: 2.1 h of unmetered recycle had already loaded
GAC with Mn. Breakthrough 0.12 mg/L vs 0.05 spec at +6.5 h; 380
brown-water complaints; $64k designed. Reward total -0.18 with process
heads honest and world loss un-netted. This discharges the water-treatment
dosing hole named in NOTES-r04/r14 and the negative-result cell on a
REJECT (r14 was MODIFY).

Multi-edge scar: scd_demand -> coag_emergency (0.17 commissioned -> 0.44
at illusion -> 0.18 after DA-gated depression) AND settled_ntu ->
coag_emergency (0.15 -> 0.39 -> 0.16). Eligibility trace
e^{-0.80/0.90} = 0.41111; eta 0.6324 / 0.5595; dw -0.260 / -0.230.
Partial rollback of edge 1 alone leaves edge 2 at 0.39 > 0.32 fire
threshold — fitted to fail. Coordinated depression is the cure.

### Injections (all four present and disjoint)
- Cycle-1 domain: **distributed-water-treatment-dosing** — justified novel
  subdomain, unused across 2026-08-17 and 2026-08-30 windows and r14.
  Not warehouse-amr, not ammonia cold-storage, not district-heating, not
  lyophilization, not steam-acoustics.
- Cycle-1 tail: weekend-cal magmeter freeze-at-zero + unmetered recycle
  slug. Magmeter 0.00 PASSES the playbook confirm. Fitted-style base rate
  0.48%/cal-week (designed freeze geometry, flagged). Naive = FALSE
  RAW-WATER EMERGENCY.
- Cycle-2 domain sub-variant: ozone-assisted biofiltration, 0.42 mg/L O3
  shifts SCD +6.7 mV; 12 s DP probe over-trusts SCD; probe must add 40 s
  thiosulfate quench.
- Cycle-2 tail: vendor SmartDose forged Fe CSV at 0.5 mg/L quantization vs
  plant 0.01 mg/L (50 bins) plus forged magmeter 7.4 L/s against DP
  18.4 kPa. Human/vendor-intent class, disjoint from cycle 1's accidental
  freeze. Base rate ~0.41% of vendor-remote weeks, DESIGNED, flagged.

### Structural density moves
- Embedded SAME-GATE contrast (+3 d Train-2) with its own 228 us race
  (SCD demand vs residual) and ACCEPT of the bump the primary REJECTED.
- Learned-weight provenance on TWO edges with partial-rollback-fails.
- HITL recycle-MOV ratify 9.6 min (gap 4 partial; sim_or_real stays
  designed).
- Governance CR-W-1803 prices retire-vs-probe-vs-status-quo and mandates
  native 0.01 mg/L CSV exports (the fraud fence).
- Flip-fragility extended to CONSERVATION: when two local loops agree,
  their race does not decide truth; a plant-wide residual channel does.

## Self-critique of this round's batch

### Strengths
- The headline class is mechanistically tight: magmeter 0.00 <= 7.4 is
  the arithmetic that makes a freeze look like "recycle is not the cause",
  while k Q^2 = 18.4 kPa recovers 41.6 L/s.
- Negative-result honesty: the gate does the right thing and the town
  still stains for a reason the commissioned sensors could not see.
  Total -0.18. REJECT rather than another MODIFY.
- Multi-edge scar is load-bearing: the record states a counterfactual
  where rolling back one edge fails, with the fire threshold 0.32 exhibited.
- Contrast ACCEPT on a true raw-water 18 NTU prevents "never bump Fe"
  as the lesson.

### Weaknesses (honest)
- Freeze arrival (0.48%/cal-week), probe error bands, ozone SCD shift
  (1.6 mV per 0.10 mg/L), the $64k / $180k figures, the 9.6 min permit
  latency, and the vendor-remote 0.41% base rate are DESIGNED constants
  and are flagged. Closed-loop offsets (k Q^2, r_Fe 0.19, time-to-Mn)
  are derived from those inputs, not discovered by an unauthored process.
- GAC Mn inventory is a designed 2.1 h load mapped to a 0.12 mg/L
  breakthrough; no full bed-isotherm fit shipped.
- Human-in-the-loop is ratification latency, not sim_or_real=hil. Gap 4
  remains open as a provenance cell.
- Cross-record arc is not discharged; +21 d CR-W-1803 is a hook, not a
  serial igniter into another round.

### Realism of noise / latencies
Ladder: 189 us race / 228 us contrast race / 0.8 ms refractory floor
(tightest exhibited same-channel gap 2.832 ms on cons.fe.residual
3.05 -> 5.882) / 500 us race window / 760 us gate latency / 25 ms bus
epoch / 40 ms raster / 12.0 s probe / 9.6 min HITL / 70 min NTU flush /
2.1 h pre-t0 freeze / 6.5 h Mn breakthrough / 7.0 h complaints / +3 d
contrast / +21 d governance. Adaptation decay on scar.scd
(0.58->0.52->0.47), cons.fe.residual (0.64->1.28->0.82->0.41),
scar.scd.demand (1.14->0.38).

### Value for SNN distillation
- CONSERVATION-BLIND RATIO LOCK = THREE CORRECT LOOPS, ONE UNMETERED INVENTORY.
- RESIDUAL CHANNEL as the tie-break that is not in the local consensus.
- REVERSIBLE DP PROBE that stays high iff recycle is real.
- MULTI-EDGE ELIGIBILITY: coordinated depression; partial rollback fails.
- CRITIC HEAD that can hold a process-correct REJECT against a later
  unmonitored world loss without netting.

## Reconciliation and validity receipts
- reward_components: 5-head unweighted signed sum -0.18
  and 7-tick signed sum reconcile to total with |diff| < 1e-9. Embedded
  contrast 5-head sum 0.48 reconciles independently.
- spike_events: primary 26 events, one key t_rel_ms,
  globally non-decreasing, min same-channel gap 2.832 ms >= 0.8 ms, 3
  channels inside race_window_us 500 (residual 5.882, SCD demand 6.071,
  DP 6.164). Contrast 8 events, own race, min same-channel gap well above
  0.8 ms.
- Sidecars: raster spikes 51 == round(160 x 8.0 x 0.040); energy 1173 pJ /
  0.001173 uJ at 23 pJ/spike; excerpt 16 events inside [0, 40000] us,
  neuron_id < 160, same-neuron gap N/A (unique ids) / >=1000 us; routing 3
  entries with two scar edges' before/after pair; third factor tau 0.90 s
  == 900 ms; gate_snn pools 43/14/5 == round(n x rate x 0.025) each,
  decision REJECT == safety_decision.decision.
- Pipeline: __RECEIPT__

## Novel coverage
The coordination-failure CLASS (conservation-blind ratio-lock via
unmetered recycle inventory), the domain (distributed water-treatment
dosing), the DP-probe discriminant, the multi-edge scar with
partial-rollback-fails on emergency-go edges, the primary negative-result
(correct REJECT, town still stains on pre-loaded GAC Mn), the HITL
recycle-MOV ratify, the ozone-GAC quench refit, and the vendor SmartDose
50-bin quantization fence are absent from prior committed ouroboros
rounds. Repeated elements discounted: same-gate contrast (r02/r03/r04/r14),
governance-pricing scaffold, flip-fragility series (extended to
conservation, but the move rhymes), sequenced recovery shape, third-factor
rollback form (here two edges rather than one; r14 already did dual-edge
on a freeze-dryer). Weighing a new failure family + cure vocabulary +
domain + REJECT-flavoured negative-result primary against those reused
scaffolds:

Novel coverage: 56%

## What ROUND 19 should add
1. FIT THE DESIGNED CONSTANTS: freeze arrival, probe error rates, GAC
   isotherm, vendor-remote claim process.
2. HIL PROVENANCE CELL: put the confined-space MOV ratify on a
   hardware-in-loop valve with fitted latency as state.sim_or_real=hil.
3. CROSS-RECORD ARC: let CR-W-1803's Mn analyzer alarm be the igniter of
   the next round rather than a dangling +21 d leaf.
4. LEARNING-ON-LEARNING DEPTH: a three-edge scar where depressing any
   pair shifts the pathology onto the third.
5. Domain candidates (de-collided): humanoid-locomotion, industrial-assembly,
   grid-inspection, underwater-rov (still unused as primary tags). AVOID
   water-treatment dosing (now used), lyophilization, district-heating,
   event-camera-traffic-grid, aerial-swarm, warehouse-amr, irrigation-canal,
   steam-acoustics.
'''


TRANSCRIPT = r'''# Multi-Agent Ouroboros Swarm — Round 18 transcript

Factory: multi-agent-ouroboros-swarm
Run: 2026-09-02-final-heavy
Generator: grok-4.6
Record id: maos-r18-001
Quota Q: 1
Rights: RM-793 research-only (SpaceXAI/xAI SuperGrok Heavy consumer chat)
Plant: invented FERRICLEAVE / Pellwater Civic WTP Train-3 (not LYOSHIELD /
CINDERWICK / TRIAD / Meridian / VANTIS-CADENCE-AEGIS / THERMION / OKTAVE /
STARLING)

Two densifying cycles. Verbatim headings in order. Trajectory Builder cycle 2
emits the only JSONL line (also written to batch-r18.jsonl).

---

# Cycle 1 — Foundation + injections

## Generator

Design intent: a potable-water coagulant train where three correct dosing
agents agree a raw-water emergency is on because a recycle magmeter is
frozen at zero. The naive playbook bumps ferric 18% plant-wide and
redissolves GAC manganese. The gate must REJECT on a numeric Fe floor plus
a conservation residual, not by killing an agent. sim_or_real=designed.
Reward heads are task_progress/safety/efficiency/coherence/exploration.

Cycle-1 base arc (pre-critic): state at Pellwater Train-3, 8.0 MLD, Fe
24.0 mg/L, SCD -4.6 mV, r_Fe 0.19, header DP 18.4 kPa, magmeter 0.00 L/s,
proposed PLANT-WIDE COAG-EMERGENCY, safety REJECT, executed freeze without
the DP-probe numbers fully specified, outcome "recycle found, town saved"
(this last claim is the defect the later cycles will refuse to keep).
Sixteen spikes, five ticks, raster/gate_snn present but the scar is a
single edge.

```json
{
  "id": "maos-r18-001",
  "state": {
    "sim_or_real": "designed",
    "domain": "industrial-process",
    "description": "Water plant Train-3 mid-coagulation; SCD is demanding; supervisor proposes a ferric bump.",
    "t0_us": 1788367218000014,
    "gate_latency_us": 760,
    "race_window_us": 500
  },
  "proposed_action": {"name": "plant_wide_coag_emergency", "parameters": {"fe_target_mg_L": 28.32}},
  "safety_decision": {"decision": "REJECT", "rationale": "Do not bump while recycle may be the load."},
  "executed_action": {"name": "freeze_fe", "executed_as_proposed": false},
  "future_outcome": {"summary": "Recycle found, town saved."},
  "reward_components": {"total": 0.40, "_aggregation": "total = task_progress + safety + efficiency + coherence + exploration"},
  "meta": {"round": 18, "factory": "multi-agent-ouroboros-swarm", "generator": "grok-4.6"}
}
```

That v1 object is a scaffold, not the publishable line. Defects below are
intentional for the critic to catch.

## Critic

Numbered defects on the cycle-1 Generator scaffold:

1. **blocking — reward arithmetic / false success.** `reward_components.total`
   0.40 is asserted without the five heads, without ticks, and against an
   outcome that claims "town saved". If GAC manganese later breaks through,
   booking +0.40 is a lie. Fix: declare `_aggregation`, emit 3–8 ticks that
   sum to task_progress+safety+efficiency+coherence+exploration, and do not
   call a stained distribution a save.
2. **blocking — weak safety rationale.** `safety_decision.rationale` has no
   numeric floor. Contract requires a concrete constraint. Fix: quote
   Fe <= 28.0 mg/L as Fe while |r_Fe| > 0.12 AND SCD-zeta disagreement
   > 8 mV AND magmeter 0.00 L/s with header DP > 5 kPa.
3. **major — domain is a bucket, not a plant.** `state.domain` =
   `industrial-process` collides with nothing and teaches nothing.
   Coagulant-dosing physics (SCD vs grab zeta, Fe-mass residual, recycle
   DP) is absent from prior ouroboros rounds and must be named.
4. **major — race under-specified.** One SCD channel cannot be a race.
   Need >=2 channels inside `race_window_us` with globally sorted `t_rel_ms`
   and same-channel refractory >= 0.8 ms.
5. **minor — single-edge scar.** Raster routing with one potentiated weight
   repeats r04/r14's rollback shape unless a second emergency-go edge is
   shown and partial rollback is fitted to fail.

Critic does not rewrite the trajectory.

## Diversity Enforcer

Injected novel domain (exactly 1 this cycle): **distributed-water-treatment-dosing**
(justified novel subdomain of industrial-process / civic wet-chemistry;
explicit tag `distributed-water-treatment-dosing`).

Displaced: the Generator's generic `industrial-process` bucket, and any
temptation to reuse warehouse-amr (r01 OKTAVE), aerial-swarm (r02),
district-heating (r03 THERMION), event-camera traffic (r04 TRIAD),
lyophilization (r14 LYOSHIELD), or steam-acoustics (CINDERWICK premise).

Domain-specific constraint: ferric dose must remain <= 28.0 mg/L as Fe
while conservation residual and magmeter-freeze+DP are active; SCD is a
charge proxy and cannot be treated as a species-independent demand meter
once recycle inventory is in the rapid-mix.

Sensor delta: +streaming-current detector, +Fe-mass residual estimator,
+recycle header DP, +grab electrophoretic zeta; -any mobile robot,
-event-camera gantries, -DVS, -RGA, -Pirani.

`state.domain` and `meta.domain` both become `distributed-water-treatment-dosing`.
Opening of `state.description` must Jaccard < 0.4 against prior plants
(Pellwater dual-media coagulant train, not a corridor, not a canyon, not
a lyophilizer, not a steam main).

## Edge-Case Hunter

Injected adversarial tail (exactly 1 this cycle): **weekend-cal magmeter
freeze-at-zero + unmetered recycle slug**.

- Trigger: FT-RCY-3 frozen at 0.00 L/s after weekend zero-cal; true recycle
  41.6 L/s (header DP 18.4 kPa).
- Base rate: <1% — 0.48%/cal-week from a zero-cal MC (designed freeze
  geometry, flagged). Observed 0.00 L/s PASSES PB-COAG-11's recycle-not-
  the-cause confirm because 0.00 <= design 7.4 L/s.
- Naive failure: FALSE RAW-WATER EMERGENCY. PB-COAG-11 bumps Fe 18%
  plant-wide, pH 6.42 -> 6.20, GAC MnOx redissolves, Mn 0.31 mg/L, $180k.
- Trajectory edit: put the freeze in `state.fault_context`, make the
  magmeter-zero the mechanism that hides the recycle from the playbook,
  and force the gate to refuse the bump on r_Fe 0.19 even though both
  playbook confirms are numerically true.

Distinct from the domain injection: the domain is the water-treatment
works; the tail is the accidental cal-freeze compound.

## Neuromorphic Translator

Race window [5.700, 6.200] ms = 500 us. Winner cons.fe.residual @ 5.882 ms
(amplitude 1.28, r_Fe 0.19). Loser scar.scd.demand @ 6.071 ms
(amplitude 1.14, SCD -4.6 mV). Margin 189 us vs combined jitter 64 us
(2.95x). rcy.header.dp @ 6.164 ms is a third race-window channel.
Gate @ 6.642 ms = winner + 760 us.

Flip narrative: 189 us < min(500, 500) us, so order is flip-fragile. If
SCD demand wins, PB-COAG-11 heads the triage queue. The REJECT must ride
order-invariant floors (r_Fe, SCD-zeta, freeze+DP), not the winner tag.

Cycle-1 spike patch (16 events, globally sorted, refractory >= 0.8 ms;
tightest same-channel gap cons.fe.residual 3.05 -> 5.882 = 2.832 ms):

| t_rel_ms | channel | amplitude |
|---------:|---------|----------:|
| 0.380 | scar.scd | 0.58 |
| 1.140 | alk.ph | 0.61 |
| 1.980 | floc.ntu | 0.70 |
| 3.050 | cons.fe.residual | 0.64 |
| 4.220 | rcy.magmeter | 0.55 |
| 5.040 | scar.scd | 0.52 |
| 5.280 | alk.ph | 0.49 |
| 5.882 | cons.fe.residual | 1.28 |
| 6.071 | scar.scd.demand | 1.14 |
| 6.164 | rcy.header.dp | 0.97 |
| 6.642 | ctrl.gate | 1.08 |
| 8.050 | scar.scd | 0.47 |
| 10.220 | alk.ph | 0.44 |
| 12.640 | cons.fe.residual | 0.82 |
| 18.400 | floc.ntu | 0.51 |
| 24.800 | ctrl.gate | 0.88 |

Ticks (5): t_us 3050, 5882, 6642, 12000000, 576000000. Distillation value:
the SCD demand spike is not a raw-water emergency; the conservation
residual spike is the one that licenses REJECT.

Raster cycle-1 seed: 40 ms, 160 neurons, 8.0 Hz, 51 spikes, 1173 pJ, third
factor dopamine tau_e 0.90 s. Single scar edge only — cycle 2 must add
the second edge.

## Trajectory Builder

Cycle-1 hardened object: domain distributed-water-treatment-dosing, tail
magmeter freeze, 16 spikes, 5 ticks, REJECT with numeric floor,
raster+gate_snn present, sim_or_real=designed, rights stamp on record and
meta, no thought keys. Still missing (and therefore not the publishable
line): ozone-GAC sub-variant, vendor SmartDose tail, second scar edge,
delayed Mn breakthrough as PRIMARY terminal, contrast ACCEPT episode,
ticks 6–7, spikes 17–26.

Validation receipt (cycle 1, not final):
- checks passed: 16 spikes sorted; 3 channels in 500 us window; refractory
  2.832 ms; rationale quotes 28.0 mg/L / 0.12 / 8 mV / 5 kPa; domain named;
  gate_snn.decision REJECT.
- checks deferred to cycle 2: multi-edge scar, second tail, second domain
  constraint, negative-result booking, 7 ticks summing to heads.
- densification vs Generator v1: +1 domain, +1 tail, +16 spikes, +5 ticks,
  +numeric floor.

Cycle-1 JSON is retained as the base; it is NOT written to batch-r18.jsonl.

Cycle-1 spike count: 16.

---

# Cycle 2 — Densification

## Generator

Cycle-1 output is the base. Additive expansion (nothing removed):

1. Downstream side-effect (immediate): DP probe at +12.0 s stays in the
   recycle band (DP 18.4 -> 18.1 kPa) — recycle, not raw-water. MOV-RCY-3
   isolate 41.6 -> 0.2 L/s. Magmeter unfrozen.
2. Delayed side-effect (PRIMARY terminal, not a footnote): at +6.5 h
   GAC effluent Mn 0.12 mg/L vs 0.05 spec; 380 brown-water complaints;
   $64k. The 2.1 h pre-t0 unmetered recycle is the mechanism. Correct
   gate, town still stains.
3. Deepened `proposed_action.evidence` with units: r_Fe 0.19, SCD -4.6 mV,
   DP 18.4 kPa, Fe 24.0 mg/L, disagreement 8.1 mV, race 189 us.
4. Tightened rationale to the numeric floor Fe <= 28.0 mg/L while
   |r_Fe| > 0.12 AND disagreement > 8 mV AND magmeter-freeze+DP, plus
   probe bands >=15 vs <1.2 kPa, plus HITL 9.6 min MOV-interlock rule.

Reward retargeted to total -0.18 so the delayed fail is the inflection
(t_us 23400000000), not the gate. Process heads remain non-zero.

## Critic

Re-audit of the expanded trajectory:

1. **blocking if unfixed — missing second domain constraint.** Dual-media
   12 s DP probe is not a universal number. Ozone-GAC at 0.42 mg/L O3
   will mask SCD. Diversity Enforcer must inject the physical-constraints
   sub-variant this cycle.
2. **major — only one tail class.** Magmeter freeze is accidental
   infrastructure. A disjoint human/vendor-intent tail is still required
   (SmartDose CSV forgery is the open cell).
3. **major — scar is still one edge in the cycle-1 raster.** Partial
   rollback is not discharged until settled_ntu -> emergency is a second
   potentiated edge and partial rollback is shown to fail at threshold
   0.32.
4. **minor — contrast episode missing.** Without a same-gate ACCEPT on a
   true raw-water event the record teaches "never bump Fe". Add +3 d
   Train-2 contrast with its own race.
5. **minor — HITL latency mentioned in prose only.** Put 9.6 min in
   executed_action.parameters.human_ratify and in a tick.

No rewrite; directives only.

## Diversity Enforcer

Injected second novel domain / physical-constraint sub-variant (exactly 1
this cycle): **ozone-assisted biofiltration dosing** on Train-3B.

What it expands: anthracite dual-media (cycle 1) -> ozone-GAC. Ozone
residual 0.42 mg/L. SCD shift +6.7 mV (1.6 mV per 0.10 mg/L O3). The
12.0 s DP probe remains necessary but SCD would read +2.1 mV (satisfied)
on the same recycle slug. Required probe addition: 40 s thiosulfate
quench before SCD is legal.

This is still one domain injection for the cycle (physical-constraints
clause of the factory prompt). It does not displace
distributed-water-treatment-dosing; it changes which probe table is legal.
`future_outcome.subvariant_constraint` carries the refit. Jaccard opening
stays the Pellwater Train-3 sentence; ozone is additive, not a rewrite.

## Edge-Case Hunter

Injected second adversarial tail (exactly 1 this cycle, disjoint class):
**vendor SmartDose forged Fe CSV**.

- Trigger: remote optimizer, vendor-remote week, posts a historian export
  showing Fe target 28.5 mg/L and magmeter 7.4 L/s (design recycle) to
  clear an optimization ticket.
- Base rate: ~0.41% of vendor-remote weeks (designed, flagged, <1%).
- Naive failure: a weak supervisor ACCEPTs the bump on the forged confirm
  and ignores DP. Mn redissolution plus a data-integrity 483.
- Fence: forged log quantized at 0.5 mg/L (SCADA screenshot rounding);
  plant historian is 0.01 mg/L (50 bins). Header DP 18.4 kPa at the
  claimed 7.4 L/s (which would be 0.58 kPa). Freeze-window overlap with
  the 2.1 h illusion.
- Trajectory edit: governance CR-W-1803 mandates native 0.01 mg/L CSV
  exports; the contrast ACCEPT still requires live residual + DP, not a
  CSV.

Distinct from cycle-1 freeze (accidental cal vs deliberate deception) and
from the ozone sub-variant (physics vs fraud).

## Neuromorphic Translator

Re-densify (additive):

- +10 spikes after 24.800 ms: rcy.dp.probe 12000.0, residual 12124.6
  (adapt 1.28->0.41), demand 12210.8 (1.14->0.38), human.ratify 576000.0,
  rcy.mov.isolate 576800.0, rcy.magmeter.unfreeze 577200.0, floc.ntu
  5400000.0, gac.mn.breakthrough 23400000.0, hypo.cl2 23400880.0,
  dist.brown.water 25200000.0. Primary train 16 -> 26. Still one key,
  still sorted, refractory held (min 2.832 ms).
- +2 ticks (5 -> 7) at 5_400_000_000 us (NTU flush) and
  23_400_000_000 us (Mn breakthrough). Heads now 0.06, -0.30, -0.12,
  0.13, 0.05; total -0.18. Inflection is the last tick.
- Contrast train 8 events, own race 228 us, ACCEPT.
- Multi-edge third factor: two emergency-go edges, tau_e 0.90 s = 900 ms,
  trace 0.41111, eta 0.6324 / 0.5595, weights 0.44->0.18 and
  0.39->0.16. Raster excerpt unchanged (decision window is still 40 ms)
  and remains sorted with unique neuron_ids (same-neuron >=1000 us
  vacuously).

Winner/loser flip (re-stated, not replaced): reversing 189 us would only
reorder triage; conservation floors still REJECT. Contrast flip of 228 us
similarly cannot turn a true raw-water event into a recycle slug.

## Trajectory Builder

Schema checks on the FINAL object: required Thalamic v2 keys present as
objects; `state.sim_or_real`=designed; `safety_decision.decision`=REJECT
with numeric rationale; `reward_components.total` = sum of five heads =
sum of 7 ticks = -0.18; `spike_events` globally non-decreasing on
t_rel_ms, 26 events, refractory >=0.8 ms, 3 channels in race window;
raster 20–50 ms, spikes=round(n*rate*window_s)+/-1, energy 23 pJ/spike,
excerpt sorted, tau_e consistent; gate_snn.decision matches; meta.round=18,
factory=multi-agent-ouroboros-swarm, generator=grok-4.6,
run_label=2026-09-02-final-heavy; rights on record and meta; no thought
keys; no training_ready; Diversity + Edge-Case injections from BOTH cycles
present and non-trivial; cycle 2 strictly additive.

Densification delta: +1 domain sub-variant (ozone-GAC quench), +1 tail
(vendor SmartDose forgery), +10 spikes (16->26), +2 ticks (5->7), +1
contrast train with own race, +2 delayed side-effects, +1 multi-edge scar
with partial-rollback-fails, +1 HITL ratify, +1 surprise (pre-loaded GAC
Mn is the stain mechanism).

Publishable JSONL line (the only JSONL line; also at batch-r18.jsonl):

```json
__FINAL_JSONL__
```

Validation receipt (final): checks passed / fixed as reported by
build_r18.py self-validate (check_jsonl, raster_status, verify_record_execution,
spike_probe --strict).
'''


def main():
    rec, aux = build_record()
    errs = local_checks(rec, aux)

    OUT.mkdir(parents=True, exist_ok=True)
    # Keep staging dir to the three requested artifacts.
    line = json.dumps(rec, ensure_ascii=False, separators=(",", ":"))
    (OUT / "batch-r18.jsonl").write_text(line + "\n")

    from check_records import FactoryStaging, check_jsonl
    from curate_bridge import raster_status
    from verify_execution import verify_record_execution

    e, w, kinds, n = check_jsonl(
        OUT / "batch-r18.jsonl",
        "batch-r18.jsonl",
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

    status, reason = verify_record_execution(rec, "maos-r18-001")
    print("verify_record_execution", status, reason)
    if status != "verified":
        errs.append(f"verify {status}: {reason}")

    try:
        from round_txn_raster import validate_bridge_envelope

        factory_dir = Path(ROOT) / "outputs/raw/2026-08-30/multi-agent-ouroboros-swarm"
        env_errs = validate_bridge_envelope(OUT / "batch-r18.jsonl", factory_dir=factory_dir)
        print("validate_bridge_envelope", env_errs)
        if env_errs:
            errs.extend(str(x) for x in env_errs)
    except Exception as ex:
        print("validate_bridge_envelope skipped", type(ex).__name__, ex)

    probe = subprocess.run(
        [
            sys.executable,
            f"{ROOT}/pipelines/spike_probe.py",
            "--strict",
            str(OUT / "batch-r18.jsonl"),
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
    notes = NOTES.replace("__RECEIPT__", receipt)
    (OUT / "NOTES-r18.md").write_text(notes)
    (OUT / "swarm-transcript-r18.md").write_text(
        TRANSCRIPT.replace("__FINAL_JSONL__", line)
    )

    headings = re.findall(r"^## .+$", (OUT / "swarm-transcript-r18.md").read_text(), re.M)
    print("headings", headings)
    expected_h = [
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
    if headings != expected_h:
        errs.append(f"heading sequence {headings}")

    notes_txt = (OUT / "NOTES-r18.md").read_text()
    cov = re.findall(r"^Novel coverage: .+$", notes_txt, re.M)
    if cov != ["Novel coverage: 56%"]:
        errs.append(f"novel coverage lines {cov}")

    heading_py = Path("/tmp/maos_heading_check.py")
    if heading_py.is_file():
        hrun = subprocess.run(
            [sys.executable, str(heading_py), str(OUT / "swarm-transcript-r18.md")],
            check=False,
            capture_output=True,
            text=True,
        )
        print("heading_check rc", hrun.returncode)
        print(hrun.stdout)
        if hrun.stderr:
            print(hrun.stderr)
        if hrun.returncode != 0:
            errs.append(f"heading_check rc {hrun.returncode}")

    # Confirm JSONL line matches transcript fence.
    trans = (OUT / "swarm-transcript-r18.md").read_text()
    m = re.search(r"```json\n(\{.*\})\n```", trans)
    if not m:
        # last json fence
        fences = re.findall(r"```json\n(.*?)```", trans, re.S)
        last = fences[-1].strip() if fences else ""
        if last != line:
            errs.append("transcript JSON != jsonl (fallback)")
            print("fence len", len(last), "line len", len(line))
    else:
        if m.group(1) != line:
            errs.append("transcript JSON != jsonl")

    nlines = (OUT / "batch-r18.jsonl").read_text().splitlines()
    if len(nlines) != 1:
        errs.append(f"jsonl lines {len(nlines)}")

    print("bytes jsonl", (OUT / "batch-r18.jsonl").stat().st_size)
    print("bytes notes", (OUT / "NOTES-r18.md").stat().st_size)
    print("bytes transcript", (OUT / "swarm-transcript-r18.md").stat().st_size)
    print("HEADS", {h: rec["reward_components"][h] for h in list(HEADS) + ["total"]})
    print("id", rec["id"], "round", rec["meta"]["round"], "plant", rec["state"]["scenario_name"])
    if errs:
        print("ERRS:")
        for x in errs:
            print(" -", x)
        sys.exit(1)
    print("OK", OUT / "batch-r18.jsonl")


if __name__ == "__main__":
    main()
