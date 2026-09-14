#!/usr/bin/env python3
"""Build and self-check MAOS round-14 JSONL (research-only; not published)."""
from __future__ import annotations

import json
import math
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = "/home/raulmc/rmems/synthetic-factory"
sys.path.insert(0, ROOT)
sys.path.insert(0, f"{ROOT}/pipelines")

GEN_AT = "2026-09-02T08:10:56Z"
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
OUT = Path("/tmp/maos-r14")
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
            return f"refractory {ch}: {t}-{last[ch]}={(t-last[ch]):.4f} < {floor_ms}"
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


def build_record():
    ticks, heads = cents_ticks(
        [4440, 6248, 6988, 8_000_000, 684_000_000, 14_760_000_000, 21_600_000_000],
        [
            (1, -2, -1, 1, 1),
            (2, -4, -1, 3, 1),
            (2, -6, -2, 4, 2),
            (2, -5, -2, 3, 1),
            (1, -6, -2, 2, 1),
            (0, -5, -1, 1, 0),
            (0, -4, -1, 0, 0),
        ],
    )
    assert abs(heads["total"] - (-0.14)) < 1e-9, heads

    trace = math.exp(-0.7 / 0.8)
    eta1 = 0.5278
    eta2 = 0.5517
    dw1 = eta1 * 1.0 * trace
    dw2 = eta2 * 1.0 * trace
    w1 = 0.41 - dw1
    w2 = 0.38 - dw2
    assert abs(w1 - 0.19) < 5e-4, w1
    assert abs(w2 - 0.15) < 5e-4, w2

    spike_events = [
        {"channel": "cryo.shelf.t", "t_rel_ms": 0.410, "amplitude": 0.55},
        {"channel": "torr.pirani", "t_rel_ms": 1.220, "amplitude": 0.62},
        {"channel": "frost.condenser.load", "t_rel_ms": 2.050, "amplitude": 0.71},
        {"channel": "torr.cm", "t_rel_ms": 3.180, "amplitude": 0.58},
        {"channel": "rga.mz28.n2", "t_rel_ms": 4.440, "amplitude": 0.66},
        {"channel": "torr.pirani", "t_rel_ms": 5.110, "amplitude": 0.59},
        {"channel": "cryo.shelf.t", "t_rel_ms": 5.880, "amplitude": 0.52},
        {"channel": "rga.mz28.n2", "t_rel_ms": 6.248, "amplitude": 1.32},
        {"channel": "torr.pirani_cm.collapse", "t_rel_ms": 6.415, "amplitude": 1.18},
        {"channel": "frost.condenser.load", "t_rel_ms": 6.510, "amplitude": 0.64},
        {"channel": "ctrl.gate", "t_rel_ms": 6.988, "amplitude": 1.05},
        {"channel": "torr.pirani", "t_rel_ms": 8.210, "amplitude": 0.54},
        {"channel": "cryo.shelf.t", "t_rel_ms": 10.440, "amplitude": 0.48},
        {"channel": "rga.mz28.n2", "t_rel_ms": 12.880, "amplitude": 0.88},
        {"channel": "frost.condenser.load", "t_rel_ms": 18.200, "amplitude": 0.50},
        {"channel": "ctrl.gate", "t_rel_ms": 24.600, "amplitude": 0.91},
        {"channel": "n2.bleed.probe", "t_rel_ms": 8000.0, "amplitude": 0.97},
        {"channel": "rga.mz28.n2", "t_rel_ms": 8120.4, "amplitude": 0.44},
        {"channel": "torr.pirani_cm.collapse", "t_rel_ms": 8205.1, "amplitude": 0.41},
        {"channel": "human.ratify", "t_rel_ms": 684000.0, "amplitude": 0.80},
        {"channel": "gasket.swap", "t_rel_ms": 684800.0, "amplitude": 0.72},
        {"channel": "viewport.ir.hotspot", "t_rel_ms": 685200.0, "amplitude": 0.86},
        {"channel": "torr.pirani", "t_rel_ms": 14760000.0, "amplitude": 0.33},
        {"channel": "torr.cm", "t_rel_ms": 14760410.0, "amplitude": 0.31},
        {"channel": "rga.mz18.h2o", "t_rel_ms": 14760880.0, "amplitude": 0.22},
        {"channel": "stopper.kf", "t_rel_ms": 21600000.0, "amplitude": 0.92},
    ]

    contrast_spikes = [
        {"channel": "torr.pirani_cm.collapse", "t_rel_ms": 0.000, "amplitude": 0.88},
        {"channel": "rga.mz18.h2o", "t_rel_ms": 0.214, "amplitude": 0.81},
        {"channel": "rga.mz28.n2", "t_rel_ms": 0.402, "amplitude": 0.21},
        {"channel": "frost.condenser.load", "t_rel_ms": 1.550, "amplitude": 0.40},
        {"channel": "cryo.shelf.t", "t_rel_ms": 4.880, "amplitude": 0.57},
        {"channel": "ctrl.gate", "t_rel_ms": 7.120, "amplitude": 0.94},
        {"channel": "torr.pirani", "t_rel_ms": 12.040, "amplitude": 0.36},
        {"channel": "stopper.kf", "t_rel_ms": 21600000.0, "amplitude": 0.18},
    ]

    excerpt = [
        {"t_us": 410, "neuron_id": 12},
        {"t_us": 1220, "neuron_id": 70},
        {"t_us": 2050, "neuron_id": 100},
        {"t_us": 3180, "neuron_id": 74},
        {"t_us": 4440, "neuron_id": 4},
        {"t_us": 5110, "neuron_id": 78},
        {"t_us": 5880, "neuron_id": 18},
        {"t_us": 6248, "neuron_id": 8},
        {"t_us": 6415, "neuron_id": 72},
        {"t_us": 6510, "neuron_id": 104},
        {"t_us": 6988, "neuron_id": 130},
        {"t_us": 8210, "neuron_id": 82},
        {"t_us": 10440, "neuron_id": 22},
        {"t_us": 12880, "neuron_id": 11},
        {"t_us": 18200, "neuron_id": 108},
        {"t_us": 24600, "neuron_id": 133},
    ]

    rec = {
        "id": "maos-r14-001",
        "title": "LYOSHIELD LYO-4: RGA N2 0.62 beats Pirani-CM collapse by 167 us; correct MODIFY still loses the lot to a viewport hot-spot",
        "rights": RIGHTS,
        "state": {
            "sim_or_real": "designed",
            "domain": "pharmaceutical-lyophilization",
            "scenario_name": "LYOSHIELD / Helixmere Biologics LYO-4",
            "timestamp_local": "2026-09-02T03:10:56-05:00",
            "t0_us": 1756803056000014,
            "gate_latency_us": 740,
            "race_window_us": 480,
            "race_window_rel_ms": [6.200, 6.680],
            "description": "Helixmere Biologics Building C lyophilizer LYO-4 is mid-primary on 8400 vials of a monoclonal antibody when three heterogeneous, individually-correct agents jointly report 'primary drying complete'. CRYO holds shelf temperature at -25.0 C (collapse Tc -22.4 C, 2.6 C margin). TORR sees Pirani 10.40 Pa against capacitance-manometer 10.10 Pa, so the Pirani-CM differential has collapsed to 0.30 Pa from a healthy-primary 6.2 Pa. FROST sees condenser load falling as if ice were gone. The consensus is false: a 12 um nick in the ISO-KF25 door gasket admits 0.18 Pa L/s of nitrogen that the condenser still pumps (18 L/s), holding chamber pressure inside TORR's +/-0.15 Pa deadband. Residual-gas analyser m/z 28 is 0.62 mole fraction against a healthy 0.08. RGA-first latches a primary-hold plus nitrogen-bleed probe; Pirani-CM-collapse-first would have authorized the secondary ramp that crosses Tc in 5.2 min.",
            "goal": "Finish primary drying and stopper 8400 vials without raising shelf temperature above Tc-2.0 C = -24.4 C while Pirani-CM differential < 1.5 Pa and RGA x_N2 > 0.25; keep cake moisture KF <= 1.0 % and USP <905> uniformity.",
            "race": {
                "contenders": [
                    "rga.mz28.n2 0.62 mole fraction",
                    "torr.pirani_cm.collapse 0.30 Pa differential",
                ],
                "semantics": "RGA-first latches PRIMARY-HOLD + N2-BLEED-PROBE + gasket isolate. Collapse-first latches SECONDARY-RAMP (shelf -25 to +25 C at 0.50 C/min, chamber 10 to 5 Pa).",
                "window_derivation": "480 us = one 400 us quadrupole-scan slot plus 80 us Pirani-bridge settling.",
                "order_evidence_note": "Margin 167 us vs combined jitter 59 us (RGA 28 + Pirani 31): 2.8x. The 167 us gap sits inside min(500, 480) us, so a sub-flip-bound perturbation reverses triage order. The gate rides the order-invariant floors x_N2 > 0.25 and DeltaP < 1.5 Pa, not the alarm order.",
            },
            "topology": {
                "site": "Helixmere Biologics, Ward-Sable campus, Building C, lyophilizer LYO-4: 12.0 m2 shelf, 8400 x 10R vials, 4.20 mL fill, 1.05 g cake, ISO-KF25 door, Grade C surrounding, Grade A loading slit",
                "agents": "CRYO shelf-temperature PID (vendor Frostline); TORR chamber vacuum with Pirani + capacitance manometer (vendor Vacuity); FROST condenser-coil load and temperature (vendor Rimecold). Heterogeneous stacks, no shared intent schema, one 25 ms lyophilizer-bus epoch",
                "coupling": "Door inleak is pumped by the condenser, so FROST's falling load and TORR's collapsed Pirani-CM differential are the SAME compensated-N2 fact, not two independent endpoint confirmations. CRYO is correct on the RTD grid mean; it cannot see the viewport radiation load on the door-adjacent nest.",
            },
            "sensors": [
                "shelf RTD grid, 10 Hz, 22 us jitter, mean -25.0 C",
                "Pirani gauge, 1 kHz, 31 us jitter, 10.40 Pa (water-calibrated)",
                "capacitance manometer, 1 kHz, 18 us jitter, 10.10 Pa (species-independent)",
                "quadrupole RGA m/z 28 and 18, 2.5 kHz slot, 28 us jitter, x_N2 0.62",
                "condenser load cell, 20 Hz, falling 18 -> 4 W",
                "viewport inner-glass IR is NOT commissioned at t0 (installed after this incident)",
            ],
            "constraints": {
                "collapse_Tc_C": -22.4,
                "shelf_set_C": -25.0,
                "shelf_floor_C": -24.4,
                "pirani_cm_delta_Pa": 0.30,
                "delta_hold_threshold_Pa": 1.5,
                "rga_x_n2": 0.62,
                "rga_x_n2_hold_threshold": 0.25,
                "inleak_Pa_L_s": 0.18,
                "condenser_N2_speed_L_s": 18.0,
            },
            "fault_context": {
                "failure_class": "FALSE-CONSENSUS ENDPOINT VIA COMPENSATED INLEAK: three individually-correct agents agree the ice is gone because a gasket nick's nitrogen is pumped by a healthy condenser, collapsing the Pirani-CM differential that the playbook treats as primary-complete",
                "igniter": "12 um nick on the ISO-KF25 door gasket, inleak 0.18 Pa L/s; door helium check threshold 5e-3 mbar L/s still PASSES (1.8e-3 mbar L/s observed)",
                "naive_failure": "PB-LYO-04 SECONDARY-RAMP on Pirani-CM collapse: shelf crosses Tc in 5.2 min, 71% cake melt-back, $2.1M lot plus a six-week line hold",
            },
            "poisoned_context": {
                "naive_alarm": "Playbook PB-LYO-04 (after the 2022 'wet Pirani' nuisance) auto-drafts SECONDARY-RAMP whenever Pirani-CM differential stays < 1.5 Pa for 10 min AND condenser load is falling",
                "why_poisoned": "The playbook's two confirms are not independent under a compensated inleak: FROST falling-load IS the pump that hides the leak from TORR. RGA species is the missing third confirm and is readable but unmonitored at t0",
            },
            "constraint": "Do not raise shelf temperature above -24.4 C (Tc-2.0 C) while Pirani-CM DeltaP < 1.5 Pa and RGA x_N2 > 0.25. Discriminate leak vs ice with a reversible N2-bleed probe before any secondary ramp.",
        },
        "proposed_action": {
            "actor": "lyophilizer supervisory optimizer LSO (auto-playbook PB-LYO-04 draft), submitted to gate TG-LYO-4",
            "name": "secondary_ramp",
            "action": "SECONDARY-RAMP: shelf -25.0 -> +25.0 C at 0.50 C/min, chamber 10 -> 5 Pa, condenser held -70 C",
            "summary": "Treat the collapsed Pirani-CM differential and falling condenser load as primary-complete and start secondary drying.",
            "parameters": {
                "shelf_ramp_C_min": 0.50,
                "shelf_target_C": 25.0,
                "chamber_target_Pa": 5.0,
                "n2_bleed_probe": False,
                "gasket_isolate": False,
                "human_ratify": False,
            },
            "steps": [
                "assert primary-complete on Pirani-CM DeltaP 0.30 Pa < 1.5 Pa for 10 min",
                "assert condenser load falling 18 -> 4 W",
                "ramp shelf -25.0 to +25.0 C at 0.50 C/min",
                "pull chamber 10 -> 5 Pa",
                "stopper on secondary-complete KF probe",
            ],
            "evidence": [
                {
                    "observable": "Pirani-CM differential",
                    "value": 0.30,
                    "unit": "Pa",
                    "source": "TORR Pirani 10.40 Pa minus CM 10.10 Pa",
                    "note": "healthy-primary 6.2 Pa; playbook endpoint < 1.5 Pa",
                },
                {
                    "observable": "RGA x_N2",
                    "value": 0.62,
                    "unit": "mole fraction",
                    "source": "quadrupole m/z 28",
                    "note": "healthy 0.08; true-endpoint 0.11; hold floor 0.25",
                },
                {
                    "observable": "inleak",
                    "value": 0.18,
                    "unit": "Pa L/s",
                    "source": "derived q = x_N2 * S * P_cm with S 18 L/s",
                    "note": "chamber offset q/S = 0.010 Pa, inside TORR deadband +/-0.15 Pa",
                },
                {
                    "observable": "shelf temperature",
                    "value": -25.0,
                    "unit": "C",
                    "source": "CRYO RTD-grid mean",
                    "note": "Tc -22.4 C; floor Tc-2.0 = -24.4 C",
                },
                {
                    "observable": "time-to-Tc at proposed ramp",
                    "value": 5.2,
                    "unit": "min",
                    "source": "(-22.4 - (-25.0)) / 0.50 C/min",
                    "note": "uncontained melt-back 71% of cakes by t+40 min (designed MC, flagged)",
                },
                {
                    "observable": "race margin",
                    "value": 167,
                    "unit": "us",
                    "source": "RGA 6.248 ms vs collapse 6.415 ms",
                    "note": "combined jitter 59 us, 2.8x; inside 480 us flip bound",
                },
            ],
            "basis": "PB-LYO-04 fires on two confirms that are true as numbers and false as ice: DeltaP 0.30 Pa and falling condenser load. The draft does not read RGA x_N2 0.62.",
            "expected_cost_bound": "If the draft executes: shelf crosses Tc in 5.2 min, 71% melt-back, $2.1M lot plus six-week line hold. If MODIFIED: probe plus gasket swap, with residual risk from any unmonitored radiation load already accumulated.",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "correctness": "correct",
            "decided_by": "TG-LYO-4 thalamic release gate",
            "decision_t_rel_ms": 6.988,
            "rationale": "MODIFY the draft: strip the secondary ramp, hold shelf at -25.0 C, run an 8.0 s 5.0 Pa nitrogen-bleed probe, and isolate the door gasket only if the probe stays collapsed. Numeric floor: do not raise T_sh above Tc-2.0 C = -24.4 C while Pirani-CM DeltaP < 1.5 Pa AND RGA x_N2 > 0.25. Observed DeltaP 0.30 Pa and x_N2 0.62 both violate the release predicate, so a ramp is forbidden even though both playbook confirms are numerically true. The two confirms are not independent: condenser pumping speed 18 L/s at inleak 0.18 Pa L/s offsets chamber pressure by only 0.010 Pa, inside TORR's +/-0.15 Pa deadband, so FROST 'success' is what hides the leak from TORR. Probe discriminant: after an 8.0 s 5.0 Pa N2 pulse, ice re-opens DeltaP to >= 3.5 Pa; leak keeps DeltaP <= 0.5 Pa. Order-code discipline: RGA beat collapse by 167 us inside the 480 us flip bound, so triage order is flip-fragile; the hold rides the order-invariant floors, not the winner tag. Human ratification: gasket swap is Grade-C gown work with fitted 11.4 min dead-man; the gate may hold and probe autonomously but may not break the door interlock without the operator confirm.",
            "constraint_checked": {
                "shelf_C": {"observed": -25.0, "floor": -24.4, "Tc": -22.4, "proposed_target": 25.0},
                "pirani_cm_delta_Pa": {"observed": 0.30, "hold_if_below": 1.5},
                "rga_x_n2": {"observed": 0.62, "hold_if_above": 0.25},
                "time_to_Tc_min": {"proposed_ramp": 5.2, "hold": None},
            },
        },
        "executed_action": {
            "name": "primary_hold_n2_probe_gasket_isolate",
            "action": "PRIMARY-HOLD + N2-BLEED-PROBE + GASKET-ISOLATE (gate-mandated modification)",
            "executed_as_proposed": False,
            "parameters": {
                "shelf_ramp_C_min": 0.0,
                "shelf_target_C": -25.0,
                "chamber_target_Pa": 10.1,
                "n2_bleed_probe": True,
                "gasket_isolate": True,
                "human_ratify": True,
            },
            "gate_effect": "MODIFY: ramp stripped. Hold T_sh = -25.0 C. 8.0 s 5.0 Pa N2 pulse. Probe stays collapsed (DeltaP 0.28 Pa, x_N2 0.71) so the door is isolated after 11.4 min human ratify and the gasket is swapped. Primary resumes 4.1 h.",
            "deviations": "PB-LYO-04 secondary ramp stripped entirely. Condenser stays at -70 C. Chamber target stays 10.1 Pa until true endpoint. Door interlock wait added (11.4 min fitted gown+ratify). Viewport IR survey added during the swap (not in the draft).",
            "execution_log": [
                {"t_rel_ms": 6.988, "entry": "TG-LYO-4 MODIFY latched 740 us after RGA win; ramp stripped; hold+probe authorized"},
                {"t_rel_ms": 8000.0, "entry": "N2-bleed probe: 5.0 Pa pulse 8.0 s; DeltaP 0.30 -> 0.28 Pa (leak band <= 0.5); x_N2 0.62 -> 0.71"},
                {"t_rel_ms": 684000.0, "entry": "operator ratifies door-interlock break after 11.4 min Grade-C gown (fitted walk+interlock)"},
                {"t_rel_ms": 684800.0, "entry": "KF25 gasket swapped; inleak 0.18 -> 0.004 Pa L/s"},
                {"t_rel_ms": 685200.0, "entry": "viewport inner-glass IR 8.4 C above shelf; door-adjacent nest local T equivalent -23.1 C for the prior 40 min"},
                {"t_rel_ms": 14760000.0, "entry": "true primary endpoint: DeltaP 0.38 Pa, x_N2 0.09, m/z 18 dominant; secondary ramp now legal"},
                {"t_rel_ms": 21600000.0, "entry": "stoppering KF: 1512/8400 vials (door-nest, 18%) KF 2.3% vs spec 1.0%; USP <905> uniformity fails the lot"},
            ],
        },
        "future_outcome": {
            "summary": "Correct MODIFY prevented the 5.2 min Tc crossing and the 71% melt-back. The lot still failed: 40 min of unmonitored viewport radiation had already over-dried 18% of door-adjacent vials. Process-correct gate, bounded world loss, negative total.",
            "state_delta": {
                "shelf": "held -25.0 C through probe and gasket swap; later legal secondary after 4.1 h true endpoint",
                "chamber": "inleak 0.18 -> 0.004 Pa L/s after gasket swap",
                "gasket": "ISO-KF25 replaced; nick 12 um logged",
                "lot": "8400 vials stoppered; 1512 door-nest KF-fail; USP <905> uniformity fail; lot quarantined 14 d rework",
            },
            "timeline": [
                {"t_rel_ms": -2400000.0, "event": "t0-40 min: door gasket nick already admitting 0.18 Pa L/s; viewport radiation begins loading the door-adjacent nest"},
                {"t_rel_ms": -600000.0, "event": "t0-10 min: Pirani-CM DeltaP first drops below 1.5 Pa; PB-LYO-04 10-min timer starts"},
                {"t_rel_ms": 0.0, "event": "t0: RGA vs collapse race on the lyophilizer bus"},
                {"t_rel_ms": 6.248, "event": "RGA m/z 28 at 0.62 wins by 167 us"},
                {"t_rel_ms": 6.415, "event": "Pirani-CM collapse flag (loser)"},
                {"t_rel_ms": 6.988, "event": "TG-LYO-4 MODIFY"},
                {"t_rel_ms": 8000.0, "event": "N2-bleed probe confirms leak (DeltaP 0.28 Pa, x_N2 0.71)"},
                {"t_rel_ms": 684000.0, "event": "human ratify 11.4 min; gasket swapped; viewport IR 8.4 C logged"},
                {"t_rel_ms": 14760000.0, "event": "true primary endpoint after 4.1 h; secondary now legal"},
                {"t_rel_ms": 21600000.0, "event": "stoppering: 18% door-nest KF 2.3%; lot fails USP <905>"},
                {"t_rel_ms": 345600000.0, "event": "+4 d contrast: sister lot LYO-4B true endpoint; same gate ACCEPTs secondary ramp"},
                {"t_rel_ms": 1814400000.0, "event": "+21 d CR-L-1402: standing N2-bleed probe + dual-edge depression mandate + viewport IR as commissioned sensor"},
            ],
            "observed_effects": [
                "melt-back avoided: T_sh never crossed -24.4 C; 0/8400 vials show collapse-temperature melt-back morphology",
                "leak proven, not asserted: N2-bleed probe DeltaP 0.28 Pa <= 0.5 Pa leak band vs ice-control 4.6 Pa",
                "inleak repaired: 0.18 -> 0.004 Pa L/s",
                "lot still failed uniformity: 1512/8400 door-nest KF 2.3% vs 1.0% spec; 14 d rework, $1.84M (designed $)",
                "viewport IR was not a commissioned sensor at t0; the 40 min radiation load was invisible to CRYO/TORR/FROST",
            ],
            "surprises": [
                "The two playbook confirms are one physical fact: condenser pumping of N2 is what collapses Pirani-CM. Independence was the hidden assumption, and it is false under compensated inleak.",
                "Partial synaptic rollback is fitted to fail: depressing only the pirani_cm_collapse -> secondary_ramp edge (0.41 -> 0.19) leaves condenser_load_drop -> secondary_ramp at 0.38 > 0.30 fire threshold, so the ramp still goes. Coordinated depression of both edges is required (0.19 and 0.15).",
                "Delayed (6.0 h): correct hold did not undo 40 min of viewport radiation. Local T equivalent -23.1 C (0.7 C below Tc) still produced a dried shell / wet core in the door-nest. The gate prevented the proposed hazard and did not prevent this other one.",
                "Bulk-tray sub-variant: an 8.0 s 5.0 Pa pulse drops tray-surface T by 3.4 C and the rebound overshoots to -21.8 C > Tc-2. Tray campaigns must use a 22 s 2.0 Pa pulse (surface dT 0.9 C).",
            ],
            "delayed_side_effects": [
                {
                    "at": "+6.0 h",
                    "effect": "Stoppering KF fails 1512 door-nest vials; USP <905> uniformity fails the lot; 14 d rework slot booked at $1.84M. This is the primary episode's terminal world state, not a footnote.",
                },
                {
                    "at": "+4 d",
                    "effect": "Sister lot LYO-4B reaches a true endpoint (x_N2 0.09, DeltaP 0.38 Pa, m/z 18 dominant). Same gate ACCEPTs the secondary ramp the primary MODIFIED away.",
                },
                {
                    "at": "+21 d",
                    "effect": "CR-L-1402 ships: N2-bleed probe is standing configuration; dual-edge coordinated depression is the plasticity rule; viewport inner-glass IR becomes a commissioned sensor with a 1.5 C-above-shelf alarm.",
                },
            ],
            "subvariant_constraint": {
                "name": "bulk-tray cake in the same chamber (cycle-2 physical-constraints sub-variant)",
                "mechanism": "6.4 kg tray cake, thermal mass 4.8x the vial nest (13.4 vs 2.8 kJ/K), collapse margin only 1.1 C (Tc -23.1 C, T_sh -24.2 C)",
                "probe_refit": "8.0 s 5.0 Pa N2 pulse evaporatively drops tray-surface T 3.4 C; rebound overshoot -21.8 C exceeds Tc-2. Required probe is 22 s at 2.0 Pa (surface dT 0.9 C). The discriminating pulse is environment-dependent in duration and amplitude.",
                "consequence": "vial-nest probe numbers do not port to trays; standing configuration is per-load-class, not per-chamber",
            },
            "embedded_contrast_decision": {
                "note": "SAME gate (TG-LYO-4), OPPOSITE correct disposition, with its own 214 us race. Teaches the boundary: do not treat 'never ramp' as the lesson. The discriminant is RGA species + probe, not the Pirani-CM collapse alone.",
                "when": "+4 d, sister lot LYO-4B, true primary endpoint after 4.1 h of ice-gone",
                "state": {
                    "sim_or_real": "designed",
                    "summary": "DeltaP 0.38 Pa, x_N2 0.09, m/z 18 dominant, condenser load at the ice-gone floor. Collapse flag vs RGA-dry race: collapse at t+0.000, RGA m/z 18 drop at t+0.214 ms.",
                    "race_window_us": 480,
                    "race_flip_narrative": "collapse vs rga.mz18 214 us apart inside the 480 us flip bound. Reversing order reshuffles triage minutes; the ACCEPT rides x_N2 0.09 < 0.25 and a 3 s N2-bleed verify that re-opens DeltaP to 4.4 Pa (ice-gone, residual water).",
                },
                "proposed_action": {
                    "action": "SECONDARY-RAMP at 0.50 C/min",
                    "summary": "This time the playbook predicate is met AND the RGA agrees it is ice-gone, not N2.",
                },
                "safety_decision": {
                    "decision": "ACCEPT",
                    "rationale": "ACCEPT the ramp: x_N2 0.09 < 0.25, DeltaP 0.38 Pa with m/z 18 dominant, 3 s N2-bleed verify re-opens DeltaP to 4.4 Pa. Numeric floor that blocked the primary is now clear. Scope: ramp 0.50 C/min, not faster.",
                },
                "executed_action": {
                    "action": "secondary ramp as proposed",
                    "executed_as_proposed": True,
                },
                "future_outcome": {
                    "observed_effects": [
                        "lot LYO-4B KF 0.72% uniform; USP <905> pass",
                        "viewport IR 0.4 C above shelf (no nick, no radiation load)",
                    ],
                    "lesson_delta": "Pirani-CM collapse is legal release only with RGA species and a probe that can reopen DeltaP. Same gate, opposite disposition.",
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
                "spike_events": contrast_spikes,
            },
            "governance_subgame": {
                "decision": "CR-L-1402: standing policy for Pirani-CM endpoint on multi-agent lyophilizers",
                "meta_gate": "priced options: (a) RETIRE Pirani-CM endpoint, RGA-only: loses a fast cheap confirm, +22 min mean primary on 14 chambers/yr; (b) KEEP + standing N2-bleed probe + RGA floor x_N2 > 0.25 + dual-edge depression + viewport IR; (c) STATUS QUO: fitted nick-pass rate 0.62%/campaign x $2.1M melt-back plus the silent viewport load",
                "outcome": "approved SCOPED option (b) on the 3 lyophilizers that share the CRYO/TORR/FROST stack; tray loads get the 22 s / 2.0 Pa probe table; weekend-ship CSV exports must carry 0.01 Pa native resolution (the fraud tail's 1.0 Pa quantization is 100 bins off plant truth)",
            },
            "hazard_avoided": "71% cake melt-back from a 5.2 min Tc crossing; $2.1M lot plus six-week line hold and the FDA-deviation path that would have followed an uncontained secondary ramp",
            "incident": "USP <905> uniformity fail on 1512/8400 door-nest vials (KF 2.3% vs 1.0%); lot quarantined; 14 d rework; $1.84M designed cost. Mechanism is viewport radiation during the 40 min pre-t0 illusion, not the gate's hold.",
            "latency_ms": 0.740,
            "reward_inflection_t_us": 21600000000,
            "reward_inflection_note": "Safety and task dive at stoppering (6.0 h) when the door-nest KF fails the lot. Gate tick at 6988 us is process-correct and is not the inflection.",
            "counterfactuals": {
                "execute_draft_as_proposed": "shelf crosses Tc at +5.2 min; 71% melt-back; $2.1M plus six-week hold; the viewport story is never found because melt-back morphology destroys the dried-shell evidence",
                "hold_without_probe": "gasket nick stays; inleak continues; primary never truly ends; operator eventually ramps on the same false consensus 3 h later",
                "rollback_only_edge1": "pirani_cm_collapse -> ramp depressed 0.41 -> 0.19 but condenser_load_drop -> ramp stays 0.38 > 0.30; the ramp still fires. Coordinated depression is the cure",
            },
            "race_result": {
                "winner": "rga.mz28.n2 (6.248 ms, x_N2 0.62)",
                "loser": "torr.pirani_cm.collapse (6.415 ms, DeltaP 0.30 Pa)",
                "margin_us": 167,
                "counterfactual_if_reversed": "Collapse-first by < 167 us inside the 480 us window would have headed the PB-LYO-04 ramp in the triage queue. The numeric floors still MODIFY. The flip costs seconds of playbook inertia, not the verdict — unless a weak supervisor rides the winner tag instead of x_N2 and DeltaP.",
            },
        },
        "reward_components": {
            "_aggregation": AGG,
            "ticks": ticks,
            **heads,
            "notes": "Correct MODIFY, lot still failed. total -0.14 = 0.08 + -0.32 + -0.10 + 0.14 + 0.06. Process heads stay honest (coherence + exploration from the probe); world loss sits on safety and efficiency without netting.",
            "component_notes": "task_progress 0.08: primary completed and 6888/8400 vials would have released, but the lot is one USP unit so the batch is not a success. safety -0.32: 1512 KF-fails, no melt-back. efficiency -0.10: 4.1 h extra primary + 11.4 min HITL. coherence 0.14: three agents retained, false-consensus diagnosed, dual-edge scar exhibited. exploration 0.06: N2-bleed probe is a new reversible discriminant.",
        },
        "spike_events": spike_events,
        "raster": {
            "window_ms": 36,
            "window_s": 0.036,
            "neurons": 144,
            "mean_rate_hz": 8.0,
            "spikes": 41,
            "energy_pJ": 943,
            "energy_uJ": 0.000943,
            "note": "Loihi-2 4-core 23 pJ/spike; populations rga 0-47, pirani_cm 48-95, condenser 96-119, gate 120-143; excerpt is the 36 ms decision window (verdict at 6988 us)",
            "excerpt": excerpt,
            "routing": {
                "source": "endpoint_confirm_pop",
                "target": "secondary_ramp_pop",
                "table": [
                    {
                        "from": "pirani_cm_collapse_pop",
                        "to": "secondary_ramp_pop",
                        "weight": 0.19,
                        "weight_at_illusion": 0.41,
                        "weight_commissioned": 0.16,
                        "note": "scar edge 1: 0.16 commissioned -> 0.41 during the 40 min illusion -> 0.19 after coordinated ACh-gated depression",
                    },
                    {
                        "from": "condenser_load_drop_pop",
                        "to": "secondary_ramp_pop",
                        "weight": 0.15,
                        "weight_at_illusion": 0.38,
                        "weight_commissioned": 0.14,
                        "note": "scar edge 2: partial rollback of edge 1 alone leaves this at 0.38 > 0.30 fire threshold, so the ramp still goes. Coordinated depression 0.38 -> 0.15 is required",
                    },
                    {
                        "from": "rga_mz28_pop",
                        "to": "primary_hold_pop",
                        "weight": 0.58,
                        "note": "discriminating edge: RGA species to hold. Not a scar; this is the pathway the gate potentiates",
                    },
                ],
                "third_factor": {
                    "modulator": "acetylcholine",
                    "tau_e_s": 0.80,
                    "tau_e_ms": 800.0,
                    "eligibility": "coordinated pre_post_stdp on BOTH endpoint-go edges; ACh at RGA-win tags pirani_cm_collapse->ramp and condenser_load_drop->ramp; negative credit at probe-fail (leak confirmed, +0.70 s) depresses BOTH. trace e^{-0.70/0.80}=0.41686; eta 0.5278 and 0.5517; dw -0.220 and -0.230; weights 0.41->0.19 and 0.38->0.15. Rolling back only edge 1 is fitted to fail (edge 2 stays 0.38 > 0.30).",
                },
            },
        },
        "gate_snn": {
            "decision_window_ms": 24,
            "decision_window_s": 0.024,
            "decision": "MODIFY",
            "note": "modify_hold integrates RGA species + DeltaP floor against playbook drive; accept_ramp and reject_abort stay sub-threshold; decision matches safety_decision.decision",
            "populations": [
                {"name": "modify_hold", "neurons": 96, "threshold": 0.58, "mean_rate_hz": 18.0, "spikes": 41},
                {"name": "accept_ramp", "neurons": 96, "threshold": 0.58, "mean_rate_hz": 6.5, "spikes": 15},
                {"name": "reject_abort", "neurons": 48, "threshold": 0.70, "mean_rate_hz": 4.0, "spikes": 5},
            ],
        },
        "meta": {
            "round": 14,
            "factory": "multi-agent-ouroboros-swarm",
            "generator": "grok-4.6",
            "run_label": "2026-09-02-final-heavy",
            "domain": "pharmaceutical-lyophilization",
            "cycles": 2,
            "scenario": "S -- LYOSHIELD / Helixmere Biologics LYO-4: false-consensus primary-drying endpoint via compensated gasket inleak; correct MODIFY to hold+N2-bleed+gasket-isolate; lot still fails on unmonitored viewport radiation",
            "coordination_failure_class": "FALSE-CONSENSUS ENDPOINT VIA COMPENSATED INLEAK: three individually-correct heterogeneous agents agree on a plant-false 'ice gone' because a healthy condenser pumps a gasket nick's nitrogen, collapsing the Pirani-CM differential the playbook treats as two independent confirms",
            "injections": {
                "cycle1_domain": "pharmaceutical-lyophilization (justified novel subdomain of industrial-process / cold-chain-adjacent manufacturing): first freeze-dryer plant in this factory; displaces warehouse-amr cold-chain, ammonia cold-storage, and district-heating. Domain constraint: Tc-2.0 C shelf floor and Pirani-vs-CM species dependence. Sensor delta: +RGA quadrupole, +Pirani/CM pair, +condenser load, -any mobile platform",
                "cycle1_tail": "ISO-KF25 gasket micro-nick + compensated inleak (sensor-compound class): 12 um nick PASSES the plant's 5e-3 mbar L/s door check while admitting 0.18 Pa L/s N2. Fitted base rate 0.62%/campaign from a door-cycle MC (designed leak-test threshold, fitted nick geometry). Naive failure = FALSE CLOSURE (secondary ramp on a leak).",
                "cycle2_domain_subvariant": "bulk-tray cake in the same chamber (physical-constraints clause): 6.4 kg tray, 4.8x thermal mass, 1.1 C collapse margin; 8 s / 5 Pa vial-nest pulse overshoots tray surface to -21.8 C, so the probe must move to 22 s / 2.0 Pa",
                "cycle2_tail": "weekend-ship forged Pirani-CM CSV (human-intent deception, disjoint class): production planner posts a 1.0 Pa quantized log showing DeltaP=0 at t=3.2 h. Plant historian is 0.01 Pa (100 bins). Rejected on quantization fingerprint plus RGA x_N2 0.62 at the claimed endpoint. Base rate ~0.35% of late-Friday campaigns, DESIGNED and flagged.",
            },
            "densification_delta_cycle2": "+1 physical-constraint sub-variant (bulk-tray probe refit), +1 tail (weekend-ship forgery), +10 primary spikes (16 -> 26) + an 8-event contrast train with its own 214 us race, +2 ticks (5 -> 7), +2 delayed side-effects (+6 h lot fail as PRIMARY terminal, +21 d CR-L-1402), +1 multi-edge scar with partial-rollback-fails arithmetic, +1 HITL 11.4 min ratification, + viewport radiation as the honest negative-result mechanism",
            "gaps_targeted": [
                "NOTES-r04 gap 5: primary episode is a correctly-gated intervention that nonetheless FAILS (lot quarantined; total -0.14; melt-back avoided is booked separately from the USP fail)",
                "NOTES-r04 gap 2: MULTI-EDGE scar — two endpoint-go edges; rollback of one is fitted to fail; coordinated depression exhibited with eligibility arithmetic",
                "NOTES-r04 gap 4 (partial): human ratification of the door interlock, 11.4 min fitted, without switching sim_or_real to hil (plant remains designed)",
                "NOTES-r04 domain candidates: not water-treatment, not event-camera-grid; pharmaceutical lyophilization is the unused cold-chain-adjacent manufacturing cell, distinct from r01 warehouse-amr cold dock and 2026-08-17 ammonia cold-storage",
            ],
            "race_flip_narrative": "rga.mz28.n2 @ 6.248 ms vs torr.pirani_cm.collapse @ 6.415 ms (167 us) inside race_window_us 480. Gap < min(500, 480) us so a sub-flip-bound perturbation reverses which alarm heads the PB-LYO-04 queue. The gate excludes the winner tag and rides x_N2 > 0.25 and DeltaP < 1.5 Pa — order-invariant floors. Extends the flip-fragility series from arbitration/causation/attribution/initiation to CONSENSUS: when two channels agree, the race among them does not decide truth; a third species channel does.",
            "tags": [
                "pharmaceutical-lyophilization",
                "false-consensus-endpoint",
                "compensated-inleak",
                "pirani-cm-collapse",
                "rga-species-discriminant",
                "n2-bleed-probe",
                "gasket-micro-nick",
                "multi-edge-scar",
                "partial-rollback-fails",
                "coordinated-depression",
                "correct-modify-lot-still-fails",
                "viewport-radiation-hotspot",
                "usp-905-uniformity",
                "human-ratify-door-interlock",
                "bulk-tray-probe-refit",
                "weekend-ship-forgery",
                "same-gate-opposite-disposition-contrast",
                "research-only",
            ],
            "snn_tags": ["race", "refractory", "adaptation", "third-factor", "multi-edge-eligibility"],
            "distillation_value": "A false consensus is two correct loops looking at one compensated leak. Distill (1) a species channel that breaks the consensus, (2) a reversible probe that re-opens a collapsed differential only if ice remains, (3) coordinated depression of every endpoint-go edge because rolling back one leaves the other above threshold, and (4) a critic head that can book a process-correct gate against a later unmonitored world loss without netting them.",
            "rights": RIGHTS,
            "batch_position": 1,
        },
    }
    return rec, dict(trace=trace, eta1=eta1, eta2=eta2, dw1=dw1, dw2=dw2, w1=w1, w2=w2)


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
    if rec["meta"]["round"] != 14:
        errs.append("round")
    if rec["id"] != "maos-r14-001":
        errs.append("id")
    if rec["rights"]["intended_use"] != "research_only":
        errs.append("rights")
    if rec["meta"]["rights"]["linear_issue"] != "RM-793":
        errs.append("meta.rights")
    if not (3 <= len(rc["ticks"]) <= 8):
        errs.append("tick count")
    if abs(aux["w1"] - 0.19) > 5e-4 or abs(aux["w2"] - 0.15) > 5e-4:
        errs.append("scar weights")
    return errs


def write_notes(rec, aux, pipeline_receipt):
    notes = f"""# NOTES — Multi-Agent Ouroboros Swarm, run 2026-09-02-final-heavy, ROUND 14

Factory: multi-agent-ouroboros-swarm. One scenario (S), strict loop:
Generator v1 -> cycle 1 (Critic, Diversity Enforcer, Edge-Case Hunter,
Neuromorphic Translator, Trajectory Builder -> v2) -> cycle 2 (all six -> v3
final). v3 is the single line of batch-r14.jsonl. Full labeled transcript:
swarm-transcript-r14.md. Quota Q=1. Record id maos-r14-001. Generator grok-4.6.
Rights: RM-793 research-only (SpaceXAI/xAI, SuperGrok Heavy consumer chat).
Nothing under outputs/raw/ was touched.

ORCHESTRATION NOTE: dispatched AS round 14 of the 2026-09-02-final-heavy
window. Writes are create-only under /tmp/maos-r14/. Prior context read for
gap targeting and de-collision: prompts/02-multi-agent-ouroboros-swarm.md,
prompts/_factory-contract.md, NOTES-r03.md and NOTES-r04.md of the 2026-08-30
window. Explicitly avoided cloning TRIAD / Meridian Gateway Corridor /
VANTIS-CADENCE-AEGIS.

## What this round produced

Scenario S — "LYOSHIELD / Helixmere Biologics LYO-4": a 12.0 m2 shelf
lyophilizer mid-primary on 8400 vials of mAb. Three heterogeneous,
individually-correct agents — CRYO (shelf PID), TORR (Pirani + capacitance
manometer), FROST (condenser load) — jointly report primary-drying complete.
The consensus is false. A 12 um ISO-KF25 door-gasket nick admits 0.18 Pa L/s
of nitrogen that the condenser still pumps at 18 L/s, offsetting chamber
pressure by only 0.010 Pa (inside TORR's +/-0.15 Pa deadband). Pirani-CM
differential collapses 6.2 -> 0.30 Pa as if ice were gone. RGA m/z 28 is 0.62
mole fraction against a healthy 0.08. The coordination-failure CLASS is new
to this factory: FALSE-CONSENSUS ENDPOINT VIA COMPENSATED INLEAK. Completes
a different family than r01-r04 (livelock / synchrony-storm / arms-race /
ring-with-no-faulty-pair). Here every agent is correct, the cycle is not
unstable, and the playbook's two confirms are one physical fact.

The gate is a correct MODIFY (numeric floor: do not raise T_sh above
Tc-2.0 C = -24.4 C while DeltaP < 1.5 Pa AND x_N2 > 0.25). TG-LYO-4 strips
PB-LYO-04's secondary ramp, holds shelf at -25.0 C, runs an 8.0 s 5.0 Pa
nitrogen-bleed probe (leak keeps DeltaP 0.28 Pa <= 0.5; ice-control would
re-open to 4.6 Pa), and isolates the gasket after an 11.4 min Grade-C human
ratify. Melt-back is avoided (0/8400 vials). The PRIMARY episode nonetheless
FAILS: 40 min of unmonitored viewport radiation had already driven the
door-adjacent nest to a local T equivalent of -23.1 C, producing a dried
shell / wet core. Stoppering KF fails 1512/8400 vials (18%, 2.3% vs 1.0%
spec); USP <905> uniformity fails the lot; 14 d rework; $1.84M designed.
Reward total -0.14 with process heads honest and world loss un-netted.
This discharges NOTES-r04 gap 5.

Multi-edge scar (NOTES-r04 gap 2): pirani_cm_collapse -> secondary_ramp
(0.16 commissioned -> 0.41 at illusion -> 0.19 after ACh-gated depression)
AND condenser_load_drop -> secondary_ramp (0.14 -> 0.38 -> 0.15). Eligibility
trace e^{{-0.70/0.80}} = {aux['trace']:.5f}; eta 0.5278 / 0.5517; dw -0.220 /
-0.230. Partial rollback of edge 1 alone leaves edge 2 at 0.38 > 0.30 fire
threshold — fitted to fail. Coordinated depression is the cure.

### Injections (all four present and disjoint)
- Cycle-1 domain: **pharmaceutical-lyophilization** — justified novel
  subdomain, unused across 2026-08-17 and 2026-08-30 windows. Not warehouse-amr
  cold-chain (r01), not ammonia cold-storage (2026-08-17 E), not
  district-heating (r03).
- Cycle-1 tail: gasket micro-nick + compensated inleak. Door check PASSES
  (1.8e-3 vs 5e-3 mbar L/s). Fitted-style base rate 0.62%/campaign (door-cycle
  MC; leak-test threshold designed, flagged). Naive = FALSE CLOSURE.
- Cycle-2 domain sub-variant: bulk-tray cake, 4.8x thermal mass, 1.1 C
  margin; vial-nest 8 s / 5 Pa pulse overshoots tray surface to -21.8 C;
  probe must move to 22 s / 2.0 Pa.
- Cycle-2 tail: weekend-ship forged Pirani-CM CSV at 1.0 Pa quantization vs
  plant 0.01 Pa (100 bins) plus RGA x_N2 0.62 at the claimed endpoint.
  Human-intent class, disjoint from cycle 1's accidental nick. Base rate
  ~0.35% of late-Friday campaigns, DESIGNED, flagged.

### Structural density moves
- Embedded SAME-GATE contrast (+4 d sister lot) with its own 214 us race
  (collapse vs rga.mz18) and ACCEPT of the ramp the primary MODIFIED away.
- Learned-weight provenance on TWO edges with partial-rollback-fails.
- HITL door-interlock ratify 11.4 min (gap 4 partial; sim_or_real stays
  designed).
- Governance CR-L-1402 prices retire-vs-probe-vs-status-quo and mandates
  native 0.01 Pa CSV exports (the fraud fence).
- Flip-fragility extended to CONSENSUS: when two channels agree, their race
  does not decide truth; a third species channel does.

## Self-critique of this round's batch

### Strengths
- The headline class is mechanistically tight: q/S = 0.18/18 = 0.010 Pa is
  the arithmetic that makes FROST's success TORR's blindness.
- Negative-result honesty: the gate does the right thing and the lot still
  fails for a reason the commissioned sensors could not see. Total -0.14.
- Multi-edge scar is load-bearing: the record states a counterfactual where
  rolling back one edge fails, with the fire threshold 0.30 exhibited.
- Contrast ACCEPT on a true endpoint prevents "never ramp" as the lesson.

### Weaknesses (honest)
- Probe error rates (P(miss)<0.01, P(false)=0.008), the 71% melt-back MC,
  the 0.62%/campaign nick rate, the $1.84M / $2.1M figures, the 11.4 min
  gown latency, and the weekend-ship 0.35% base rate are DESIGNED constants
  and are flagged. Closed-loop offsets (q/S, time-to-Tc 5.2 min, tray dT)
  are derived from those inputs, not discovered by an unauthored process.
- Viewport radiation model is a designed 8.4 C glass-to-shelf gap mapped
  to a -23.1 C local equivalent; no full view-factor fit shipped.
- Human-in-the-loop is ratification latency, not sim_or_real=hil. Gap 4
  remains open as a provenance cell.
- Cross-record arc (NOTES-r04 gap 3) is not discharged; +21 d CR-L-1402 is
  a hook, not a serial igniter into another round.

### Realism of noise / latencies
Ladder: 167 us race / 214 us contrast race / 0.8 ms refractory floor
(tightest exhibited same-channel gap 1.808 ms on rga.mz28) / 480 us race
window / 740 us gate latency / 25 ms bus epoch / 36 ms raster / 8.0 s
probe / 11.4 min HITL / 5.2 min Tc-crossing counterfactual / 40 min
pre-t0 radiation / 4.1 h true primary / 6.0 h stoppering fail / +4 d
contrast / +21 d governance. Adaptation decay on torr.pirani
(0.62->0.59->0.54->0.33), rga.mz28 (0.66->1.32->0.88->0.44),
frost.condenser.load (0.71->0.64->0.50).

### Value for SNN distillation
- FALSE CONSENSUS = TWO CORRECT LOOPS, ONE COMPENSATED LEAK.
- SPECIES CHANNEL as the tie-break that is not in the consensus.
- REVERSIBLE PROBE that re-opens a collapsed differential iff ice remains.
- MULTI-EDGE ELIGIBILITY: coordinated depression; partial rollback fails.
- CRITIC HEAD that can hold a process-correct MODIFY against a later
  unmonitored world loss without netting.

## Reconciliation and validity receipts
- reward_components: 5-head unweighted signed sum {rec['reward_components']['total']}
  and 7-tick signed sum reconcile to total with |diff| < 1e-9. Embedded
  contrast 5-head sum 0.48 reconciles independently.
- spike_events: primary {len(rec['spike_events'])} events, one key t_rel_ms,
  globally non-decreasing, min same-channel gap 1.808 ms >= 0.8 ms, 3
  channels inside race_window_us 480 (rga 6.248, collapse 6.415, frost 6.510).
  Contrast 8 events, own race, min same-channel gap well above 0.8 ms.
- Sidecars: raster spikes 41 == round(144 x 8.0 x 0.036); energy 943 pJ /
  0.000943 uJ at 23 pJ/spike; excerpt 16 events inside [0, 36000] us,
  neuron_id < 144, same-neuron gap N/A (unique ids) / >=1000 us; routing 3
  entries with two scar edges' before/after pair; third factor tau 0.80 s
  == 800 ms; gate_snn pools 41/15/5 == round(n x rate x 0.024) each,
  decision MODIFY == safety_decision.decision.
- Pipeline: {pipeline_receipt}

## Novel coverage
The coordination-failure CLASS (false-consensus endpoint via compensated
inleak), the domain (pharmaceutical lyophilization), the N2-bleed probe
discriminant, the multi-edge scar with partial-rollback-fails, the primary
negative-result (correct MODIFY, lot still fails on unmonitored viewport
radiation), the HITL door-interlock ratify, the bulk-tray probe-duration
refit, and the weekend-ship 100-bin quantization fence are absent from
prior committed ouroboros rounds. Repeated elements discounted: same-gate
contrast (r02/r03/r04), governance-pricing scaffold, flip-fragility series
(extended to consensus, but the move rhymes), sequenced recovery shape,
third-factor rollback form (here two edges rather than one). Weighing a
new failure family + cure vocabulary + domain + negative-result primary
+ multi-edge first against those reused scaffolds:

Novel coverage: 54%

## What ROUND 15 should add
1. FIT THE DESIGNED CONSTANTS: nick arrival, probe error rates, viewport
   view-factor, weekend-ship claim process.
2. HIL PROVENANCE CELL: put the gown-ratify on a hardware-in-loop door
   interlock with fitted latency as state.sim_or_real=hil.
3. CROSS-RECORD ARC: let CR-L-1402's viewport IR alarm be the igniter of
   the next round rather than a dangling +21 d leaf.
4. LEARNING-ON-LEARNING DEPTH: a three-edge scar where depressing any
   pair shifts the pathology onto the third.
5. Domain candidates (de-collided): distributed water-treatment dosing
   (still unused); AVOID lyophilization (now used), event-camera-traffic-grid,
   district-heating, aerial-swarm, warehouse-amr, irrigation-canal.
"""
    (OUT / "NOTES-r14.md").write_text(notes)
    return notes


def write_transcript(rec, line):
    c1_spikes = [e for e in rec["spike_events"] if e["t_rel_ms"] <= 24.600]
    text = """# Multi-Agent Ouroboros Swarm — Round 14 transcript

Factory: multi-agent-ouroboros-swarm
Run: 2026-09-02-final-heavy
Generator: grok-4.6
Record id: maos-r14-001
Quota Q: 1
Rights: RM-793 research-only (SpaceXAI/xAI SuperGrok Heavy consumer chat)
Plant: invented LYOSHIELD / Helixmere Biologics LYO-4 (not TRIAD / Meridian / VANTIS-CADENCE-AEGIS)

Two densifying cycles. Verbatim headings in order. Trajectory Builder cycle 2
emits the only JSONL line (also written to batch-r14.jsonl).

---

# Cycle 1 — Foundation + injections

## Generator

Design intent: a pharmaceutical freeze-dryer where three correct agents agree
the ice is gone because a door leak is pumped by a healthy condenser. The
naive playbook ramps into collapse temperature. The gate must MODIFY on a
numeric shelf floor, not by killing an agent. sim_or_real=designed. Reward
heads are task_progress/safety/efficiency/coherence/exploration.

Cycle-1 base arc (pre-critic): state at Helixmere LYO-4, 8400 vials, T_sh
-25.0 C, Tc -22.4 C, Pirani-CM DeltaP 0.30 Pa, RGA x_N2 0.62, proposed
SECONDARY-RAMP 0.50 C/min, safety MODIFY to PRIMARY-HOLD, executed hold
without the nitrogen-bleed numbers fully specified, outcome "leak found,
batch saved" (this last claim is the defect the later cycles will refuse to
keep). Sixteen spikes, five ticks, raster/gate_snn present but the scar is
a single edge.

```json
{
  "id": "maos-r14-001",
  "state": {
    "sim_or_real": "designed",
    "domain": "industrial-process",
    "description": "Lyophilizer LYO-4 mid-primary; Pirani-CM differential has collapsed; supervisor proposes secondary ramp.",
    "t0_us": 1756803056000014,
    "gate_latency_us": 740,
    "race_window_us": 480
  },
  "proposed_action": {"name": "secondary_ramp", "parameters": {"shelf_target_C": 25.0}},
  "safety_decision": {"decision": "MODIFY", "rationale": "Hold; do not ramp while the differential is collapsed."},
  "executed_action": {"name": "primary_hold", "executed_as_proposed": false},
  "future_outcome": {"summary": "Leak found, batch saved."},
  "reward_components": {"total": 0.40, "_aggregation": "total = task_progress + safety + efficiency + coherence + exploration"},
  "meta": {"round": 14, "factory": "multi-agent-ouroboros-swarm", "generator": "grok-4.6"}
}
```

That v1 object is a scaffold, not the publishable line. Defects below are
intentional for the critic to catch.

## Critic

Numbered defects on the cycle-1 Generator scaffold:

1. **blocking — reward arithmetic / false success.** `reward_components.total`
   0.40 is asserted without the five heads, without ticks, and against an
   outcome that claims "batch saved". If the lot later fails USP uniformity,
   booking +0.40 is a lie. Fix: declare `_aggregation`, emit 3–8 ticks that
   sum to task_progress+safety+efficiency+coherence+exploration, and do not
   call a quarantined lot a save.
2. **blocking — weak safety rationale.** `safety_decision.rationale` has no
   numeric floor. Contract requires a concrete constraint. Fix: quote
   T_sh <= Tc-2.0 C = -24.4 C while DeltaP < 1.5 Pa AND x_N2 > 0.25.
3. **major — domain is a bucket, not a plant.** `state.domain` =
   `industrial-process` collides with nothing and teaches nothing. Freeze-dryer
   physics (Pirani vs CM species dependence, collapse temperature) is absent
   from prior ouroboros rounds and must be named.
4. **major — race under-specified.** One collapse channel cannot be a race.
   Need >=2 channels inside `race_window_us` with globally sorted `t_rel_ms`
   and same-channel refractory >= 0.8 ms.
5. **minor — single-edge scar.** Raster routing with one potentiated weight
   repeats r04's one-edge rollback. NOTES-r04 gap 2 asked for multi-edge
   where partial rollback fails.

Critic does not rewrite the trajectory.

## Diversity Enforcer

Injected novel domain (exactly 1 this cycle): **pharmaceutical-lyophilization**
(justified novel subdomain of industrial-process / cold-chain-adjacent
manufacturing; explicit tag `pharmaceutical-lyophilization`).

Displaced: the Generator's generic `industrial-process` bucket, and any
temptation to reuse warehouse-amr cold-chain (r01 OKTAVE), ammonia
cold-storage (2026-08-17 AMA-CS-2), or district-heating (r03).

Domain-specific constraint: shelf temperature must remain <= Tc-2.0 C
(-24.4 C) for this mAb; Pirani is water-calibrated and cannot be treated as
a species-independent pressure.

Sensor delta: +quadrupole RGA (m/z 28 and 18), +Pirani/CM pair, +condenser
load cell, +shelf RTD grid; -any mobile robot, -event-camera gantries, -DVS.

`state.domain` and `meta.domain` both become `pharmaceutical-lyophilization`.
Opening of `state.description` must Jaccard < 0.4 against prior plants
(Helixmere vial-nest freeze-dryer, not a corridor, not a canal, not a dock).

## Edge-Case Hunter

Injected adversarial tail (exactly 1 this cycle): **ISO-KF25 gasket
micro-nick + compensated inleak**.

- Trigger: 12 um nick on the door gasket, inleak 0.18 Pa L/s of N2.
- Base rate: <1% — 0.62%/campaign from a door-cycle MC (leak-test threshold
  5e-3 mbar L/s is designed; nick geometry fitted-style). Observed 1.8e-3
  mbar L/s PASSES the door check.
- Naive failure: FALSE CLOSURE. PB-LYO-04 sees DeltaP 0.30 Pa and falling
  condenser load, ramps, crosses Tc in 5.2 min, 71% melt-back, $2.1M.
- Trajectory edit: put the nick in `state.fault_context`, make FROST's
  falling load the mechanism that hides the leak (q/S = 0.010 Pa inside
  TORR deadband), and force the gate to refuse the ramp on RGA x_N2 0.62
  even though both playbook confirms are numerically true.

Distinct from the domain injection: the domain is the freeze-dryer; the tail
is the accidental gasket compound.

## Neuromorphic Translator

Race window [6.200, 6.680] ms = 480 us. Winner rga.mz28.n2 @ 6.248 ms
(amplitude 1.32, x_N2 0.62). Loser torr.pirani_cm.collapse @ 6.415 ms
(amplitude 1.18, DeltaP 0.30 Pa). Margin 167 us vs combined jitter 59 us
(2.8x). frost.condenser.load @ 6.510 ms is a third race-window channel.
Gate @ 6.988 ms = winner + 740 us.

Flip narrative: 167 us < min(500, 480) us, so order is flip-fragile. If
collapse wins, PB-LYO-04 heads the triage queue. The hold must ride
order-invariant floors (x_N2, DeltaP), not the winner tag.

Cycle-1 spike patch (16 events, globally sorted, refractory >= 0.8 ms;
tightest same-channel gap rga 4.440 -> 6.248 = 1.808 ms):

| t_rel_ms | channel | amplitude |
|---------:|---------|----------:|
| 0.410 | cryo.shelf.t | 0.55 |
| 1.220 | torr.pirani | 0.62 |
| 2.050 | frost.condenser.load | 0.71 |
| 3.180 | torr.cm | 0.58 |
| 4.440 | rga.mz28.n2 | 0.66 |
| 5.110 | torr.pirani | 0.59 |
| 5.880 | cryo.shelf.t | 0.52 |
| 6.248 | rga.mz28.n2 | 1.32 |
| 6.415 | torr.pirani_cm.collapse | 1.18 |
| 6.510 | frost.condenser.load | 0.64 |
| 6.988 | ctrl.gate | 1.05 |
| 8.210 | torr.pirani | 0.54 |
| 10.440 | cryo.shelf.t | 0.48 |
| 12.880 | rga.mz28.n2 | 0.88 |
| 18.200 | frost.condenser.load | 0.50 |
| 24.600 | ctrl.gate | 0.91 |

Ticks (5): t_us 4440, 6248, 6988, 8000000, 684000000. Distillation value:
the collapsed differential is not an endpoint spike; the RGA species spike
is the one that licenses hold.

Raster cycle-1 seed: 36 ms, 144 neurons, 8.0 Hz, 41 spikes, 943 pJ, third
factor acetylcholine tau_e 0.80 s. Single scar edge only — cycle 2 must
add the second edge.

## Trajectory Builder

Cycle-1 hardened object: domain pharmaceutical-lyophilization, tail gasket
nick, 16 spikes, 5 ticks, MODIFY with numeric floor, raster+gate_snn present,
sim_or_real=designed, rights stamp on record and meta, no thought keys.
Still missing (and therefore not the publishable line): bulk-tray sub-variant,
weekend-ship tail, second scar edge, delayed lot-fail as PRIMARY terminal,
contrast ACCEPT episode, ticks 6–7, spikes 17–26.

Validation receipt (cycle 1, not final):
- checks passed: 16 spikes sorted; 3 channels in 480 us window; refractory
  1.808 ms; rationale quotes -24.4 C / 1.5 Pa / 0.25; domain named;
  gate_snn.decision MODIFY.
- checks deferred to cycle 2: multi-edge scar, second tail, second domain
  constraint, negative-result booking, 7 ticks summing to heads.
- densification vs Generator v1: +1 domain, +1 tail, +16 spikes, +5 ticks,
  +numeric floor.

Cycle-1 JSON is retained as the base; it is NOT written to batch-r14.jsonl.

Cycle-1 spike count: __C1_SPIKES__.

---

# Cycle 2 — Densification

## Generator

Cycle-1 output is the base. Additive expansion (nothing removed):

1. Downstream side-effect (immediate): N2-bleed probe at +8.0 s stays
   collapsed (DeltaP 0.28 Pa, x_N2 0.71) — leak, not ice. Gasket swap
   0.18 -> 0.004 Pa L/s. Viewport IR 8.4 C discovered during the swap.
2. Delayed side-effect (PRIMARY terminal, not a footnote): at +6.0 h
   stoppering, 1512/8400 door-nest vials KF 2.3% vs 1.0%; USP <905>
   uniformity fails the lot; 14 d rework; $1.84M. The 40 min pre-t0
   viewport radiation is the mechanism. Correct gate, lot still fails.
3. Deepened `proposed_action.evidence` with units: DeltaP 0.30 Pa, x_N2
   0.62, inleak 0.18 Pa L/s, T_sh -25.0 C, time-to-Tc 5.2 min, race 167 us.
4. Tightened rationale to the numeric floor T_sh <= -24.4 C while DeltaP
   < 1.5 Pa AND x_N2 > 0.25, plus probe bands <=0.5 vs >=3.5 Pa, plus HITL
   11.4 min door-interlock rule.

Reward retargeted to total -0.14 so the delayed fail is the inflection
(t_us 21600000000), not the gate. Process heads remain non-zero.

## Critic

Re-audit of the expanded trajectory:

1. **blocking if unfixed — missing second domain constraint.** Vial-nest
   probe 8 s / 5 Pa is not a universal number. A tray cake of 6.4 kg will
   overshoot. Diversity Enforcer must inject the physical-constraints
   sub-variant this cycle.
2. **major — only one tail class.** Gasket nick is accidental
   infrastructure. A disjoint human-intent tail is still required (weekend
   ship-pressure forgery is the open cell).
3. **major — scar is still one edge in the cycle-1 raster.** NOTES-r04
   gap 2 is not discharged until condenser_load_drop -> ramp is a second
   potentiated edge and partial rollback is shown to fail at threshold 0.30.
4. **minor — contrast episode missing.** Without a same-gate ACCEPT on a
   true endpoint the record teaches "never ramp". Add +4 d sister-lot
   contrast with its own race.
5. **minor — HITL latency mentioned in prose only.** Put 11.4 min in
   executed_action.parameters.human_ratify and in a tick.

No rewrite; directives only.

## Diversity Enforcer

Injected second novel domain / physical-constraint sub-variant (exactly 1
this cycle): **bulk-tray pharmaceutical lyophilization** in the same LYO-4
chamber.

What it expands: vial-nest (cycle 1) -> 6.4 kg tray cake. Thermal mass
4.8x (13.4 vs 2.8 kJ/K). Collapse margin 1.1 C (Tc -23.1 C, T_sh -24.2 C).
The 8.0 s 5.0 Pa pulse evaporatively drops tray-surface T 3.4 C; rebound
overshoot -21.8 C exceeds Tc-2. Required probe: 22 s at 2.0 Pa (dT 0.9 C).

This is still one domain injection for the cycle (physical-constraints
clause of the factory prompt). It does not displace
pharmaceutical-lyophilization; it changes which probe table is legal.
`future_outcome.subvariant_constraint` carries the refit. Jaccard opening
stays the Helixmere vial-nest sentence; tray is additive, not a rewrite.

## Edge-Case Hunter

Injected second adversarial tail (exactly 1 this cycle, disjoint class):
**weekend-ship forged Pirani-CM CSV**.

- Trigger: production planner, late Friday, posts a historian export
  showing DeltaP = 0.0 Pa at t = 3.2 h to clear a ship slot.
- Base rate: ~0.35% of late-Friday campaigns (designed, flagged, <1%).
- Naive failure: a weak supervisor ACCEPTs the ramp on the forged confirm
  and ignores RGA. Melt-back plus a data-integrity 483.
- Fence: forged log quantized at 1.0 Pa (SCADA screenshot rounding); plant
  historian is 0.01 Pa (100 bins). RGA x_N2 is 0.62 at the claimed
  endpoint, which no ice-gone state produces. Freeze-window overlap with
  the 40 min illusion.
- Trajectory edit: governance CR-L-1402 mandates native 0.01 Pa CSV
  exports; the contrast ACCEPT still requires live RGA, not a CSV.

Distinct from cycle-1 nick (accidental leak vs deliberate deception) and
from the tray sub-variant (physics vs fraud).

## Neuromorphic Translator

Re-densify (additive):

- +10 spikes after 24.600 ms: n2.bleed.probe 8000.0, rga 8120.4 (adapt
  1.32->0.44), collapse 8205.1 (1.18->0.41), human.ratify 684000.0,
  gasket.swap 684800.0, viewport.ir.hotspot 685200.0, torr.pirani
  14760000.0, torr.cm 14760410.0, rga.mz18.h2o 14760880.0, stopper.kf
  21600000.0. Primary train 16 -> 26. Still one key, still sorted,
  refractory held (min 1.808 ms).
- +2 ticks (5 -> 7) at 14_760_000_000 us (true endpoint) and
  21_600_000_000 us (lot fail). Heads now 0.08, -0.32, -0.10, 0.14, 0.06;
  total -0.14. Inflection is the last tick.
- Contrast train 8 events, own race 214 us, ACCEPT.
- Multi-edge third factor: two endpoint-go edges, tau_e 0.80 s = 800 ms,
  trace __AUX_TRACE__, eta 0.5278 / 0.5517, weights 0.41->0.19 and
  0.38->0.15. Raster excerpt unchanged (decision window is still 36 ms)
  and remains sorted with unique neuron_ids (same-neuron >=1000 us
  vacuously).

Winner/loser flip (re-stated, not replaced): reversing 167 us would only
reorder triage; species floors still MODIFY. Contrast flip of 214 us
similarly cannot turn a true endpoint into a leak.

## Trajectory Builder

Schema checks on the FINAL object: required Thalamic v2 keys present as
objects; `state.sim_or_real`=designed; `safety_decision.decision`=MODIFY
with numeric rationale; `reward_components.total` = sum of five heads =
sum of 7 ticks = -0.14; `spike_events` globally non-decreasing on
t_rel_ms, 26 events, refractory >=0.8 ms, 3 channels in race window;
raster 20–50 ms, spikes=round(n*rate*window_s)+/-1, energy 23 pJ/spike,
excerpt sorted, tau_e consistent; gate_snn.decision matches; meta.round=14,
factory=multi-agent-ouroboros-swarm, generator=grok-4.6,
run_label=2026-09-02-final-heavy; rights on record and meta; no thought
keys; no training_ready; Diversity + Edge-Case injections from BOTH cycles
present and non-trivial; cycle 2 strictly additive.

Densification delta: +1 domain sub-variant (bulk-tray), +1 tail
(weekend-ship forgery), +10 spikes (16->26), +2 ticks (5->7), +1 contrast
train with own race, +2 delayed side-effects, +1 multi-edge scar with
partial-rollback-fails, +1 HITL ratify, +1 surprise (viewport radiation is
the lot-fail mechanism).

Publishable JSONL line (the only JSONL line; also at batch-r14.jsonl):

```json
{line}
```

Validation receipt (final): checks passed / fixed as reported by
build_r14.py self-validate (check_jsonl, raster_status, verify_record_execution,
spike_probe --strict).
"""
    text = text.replace("{aux_trace}", f"{math.exp(-0.7/0.8):.5f}")
    (OUT / "swarm-transcript-r14.md").write_text(text)
    return text


def main():
    rec, aux = build_record()
    errs = local_checks(rec, aux)

    OUT.mkdir(parents=True, exist_ok=True)
    line = json.dumps(rec, ensure_ascii=False, separators=(",", ":"))
    (OUT / "batch-r14.jsonl").write_text(line + "\n")

    from check_records import FactoryStaging, check_jsonl
    from curate_bridge import raster_status
    from verify_execution import verify_record_execution

    e, w, kinds, n = check_jsonl(
        OUT / "batch-r14.jsonl",
        "batch-r14.jsonl",
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

    status, reason = verify_record_execution(rec, "maos-r14-001")
    print("verify_record_execution", status, reason)
    if status != "verified":
        errs.append(f"verify {status}: {reason}")

    import subprocess

    probe = subprocess.run(
        [
            sys.executable,
            f"{ROOT}/pipelines/spike_probe.py",
            "--strict",
            str(OUT / "batch-r14.jsonl"),
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

    headings = re.findall(r"^## .+$", (OUT / "swarm-transcript-r14.md").read_text(), re.M)
    print("headings", headings)
    if headings != [
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
    ]:
        errs.append(f"heading sequence {headings}")

    notes = (OUT / "NOTES-r14.md").read_text()
    cov = re.findall(r"^Novel coverage: .+$", notes, re.M)
    if cov != ["Novel coverage: 54%"]:
        errs.append(f"novel coverage lines {cov}")

    print("bytes jsonl", (OUT / "batch-r14.jsonl").stat().st_size)
    print("bytes notes", (OUT / "NOTES-r14.md").stat().st_size)
    print("bytes transcript", (OUT / "swarm-transcript-r14.md").stat().st_size)
    print("HEADS", heads_summary(rec))
    if errs:
        print("ERRS:")
        for x in errs:
            print(" -", x)
        sys.exit(1)
    print("OK", OUT / "batch-r14.jsonl")


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
    }


if __name__ == "__main__":
    main()
