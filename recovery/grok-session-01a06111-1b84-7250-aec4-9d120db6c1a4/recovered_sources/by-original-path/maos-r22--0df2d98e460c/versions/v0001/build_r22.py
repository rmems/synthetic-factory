#!/usr/bin/env python3
"""Build and self-check MAOS round-22 JSONL (research-only; not published)."""
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

GEN_AT = "2026-09-02T22:15:00Z"
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
OUT = Path("/tmp/maos-r22")
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
    "QUILLFORGE",
    "NIGHTWELL",
    "FERRICLEAVE",
    "CASSITER",
    "VEILFORGE",
    "Helixmere",
    "Lodenholt",
    "Brackmere",
    "Marshfloat",
    "Pellwater",
    "training_ready",
)
R14_OPENING = (
    "Helixmere Biologics Building C lyophilizer LYO-4 is mid-primary on 8400 "
    "vials of a monoclonal antibody"
)
R18_OPENING = "Pellwater Civic WTP Train-3 is mid-coagulation"
R19_OPENING = (
    "Marshfloat Floatworks Line TB-5 is mid-draw on 6.0 mm architectural ribbon"
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


def jaccard(a, b):
    sa = set(a.lower().split())
    sb = set(b.lower().split())
    return len(sa & sb) / max(1, len(sa | sb))


def build_record():
    ticks, heads = cents_ticks(
        [
            4210,
            6240,
            6950,
            5_000_000,
            768_000_000,
            13_680_000_000,
            21_960_000_000,
        ],
        [
            (1, -2, -1, 1, 1),
            (2, -4, -1, 3, 1),
            (2, -6, -2, 4, 2),
            (2, -5, -2, 3, 1),
            (1, -6, -2, 2, 1),
            (1, -5, -1, 1, 0),
            (0, -6, -1, 0, 0),
        ],
    )
    assert abs(heads["total"] - (-0.15)) < 1e-9, heads

    trace = math.exp(-0.70 / 0.85)
    eta1 = 0.25 / trace
    eta2 = 0.23 / trace
    eta3 = 0.21 / trace
    dw1 = eta1 * 1.0 * trace
    dw2 = eta2 * 1.0 * trace
    dw3 = eta3 * 1.0 * trace
    w1 = 0.45 - dw1
    w2 = 0.41 - dw2
    w3 = 0.38 - dw3
    assert abs(w1 - 0.20) < 5e-4, w1
    assert abs(w2 - 0.18) < 5e-4, w2
    assert abs(w3 - 0.17) < 5e-4, w3

    spike_events = [
        {"channel": "dia.opt", "t_rel_ms": 0.420, "amplitude": 0.58},
        {"channel": "wt.derived", "t_rel_ms": 1.180, "amplitude": 0.63},
        {"channel": "ht.melt", "t_rel_ms": 2.160, "amplitude": 0.71},
        {"channel": "dia.ring_rms", "t_rel_ms": 3.390, "amplitude": 0.55},
        {"channel": "dia.opt_inst.residual", "t_rel_ms": 4.210, "amplitude": 0.66},
        {"channel": "wt.derived", "t_rel_ms": 5.050, "amplitude": 0.57},
        {"channel": "dia.opt_inst.residual", "t_rel_ms": 5.410, "amplitude": 0.92},
        {"channel": "dia.opt_inst.residual", "t_rel_ms": 6.240, "amplitude": 1.26},
        {"channel": "dia.mean_ok", "t_rel_ms": 6.448, "amplitude": 1.12},
        {"channel": "ht.melt", "t_rel_ms": 6.590, "amplitude": 0.67},
        {"channel": "ctrl.gate", "t_rel_ms": 6.950, "amplitude": 1.07},
        {"channel": "dia.opt", "t_rel_ms": 8.220, "amplitude": 0.51},
        {"channel": "wt.derived", "t_rel_ms": 10.190, "amplitude": 0.46},
        {"channel": "dia.opt_inst.residual", "t_rel_ms": 13.240, "amplitude": 0.88},
        {"channel": "ht.melt", "t_rel_ms": 19.160, "amplitude": 0.48},
        {"channel": "ctrl.gate", "t_rel_ms": 25.620, "amplitude": 0.86},
        {"channel": "pull.dip.probe", "t_rel_ms": 5000.0, "amplitude": 0.97},
        {"channel": "dia.opt_inst.residual", "t_rel_ms": 5140.8, "amplitude": 0.44},
        {"channel": "dia.mean_ok", "t_rel_ms": 5280.4, "amplitude": 0.39},
        {"channel": "human.ratify", "t_rel_ms": 768000.0, "amplitude": 0.82},
        {"channel": "chuck.isolate", "t_rel_ms": 768800.0, "amplitude": 0.73},
        {"channel": "meniscus.ir", "t_rel_ms": 769400.0, "amplitude": 0.84},
        {"channel": "dia.opt", "t_rel_ms": 13680000.0, "amplitude": 0.33},
        {"channel": "wt.derived", "t_rel_ms": 13680420.0, "amplitude": 0.31},
        {"channel": "ht.melt", "t_rel_ms": 13680890.0, "amplitude": 0.22},
        {"channel": "grind.fail", "t_rel_ms": 21960000.0, "amplitude": 0.92},
    ]

    contrast_spikes = [
        {"channel": "dia.shoulder_demand", "t_rel_ms": 0.000, "amplitude": 0.88},
        {"channel": "dia.opt_inst.residual", "t_rel_ms": 0.214, "amplitude": 0.24},
        {"channel": "ht.melt", "t_rel_ms": 0.430, "amplitude": 0.21},
        {"channel": "wt.derived", "t_rel_ms": 1.620, "amplitude": 0.42},
        {"channel": "dia.opt", "t_rel_ms": 4.880, "amplitude": 0.56},
        {"channel": "ctrl.gate", "t_rel_ms": 7.310, "amplitude": 0.94},
        {"channel": "pull.dip.probe", "t_rel_ms": 3200.0, "amplitude": 0.36},
        {"channel": "grind.pass", "t_rel_ms": 21960000.0, "amplitude": 0.14},
    ]

    excerpt = [
        {"t_us": 420, "neuron_id": 8},
        {"t_us": 1180, "neuron_id": 52},
        {"t_us": 2160, "neuron_id": 100},
        {"t_us": 3390, "neuron_id": 14},
        {"t_us": 4210, "neuron_id": 6},
        {"t_us": 5050, "neuron_id": 60},
        {"t_us": 5410, "neuron_id": 18},
        {"t_us": 6240, "neuron_id": 4},
        {"t_us": 6448, "neuron_id": 22},
        {"t_us": 6590, "neuron_id": 108},
        {"t_us": 6950, "neuron_id": 140},
        {"t_us": 8220, "neuron_id": 28},
        {"t_us": 10190, "neuron_id": 70},
        {"t_us": 13240, "neuron_id": 32},
        {"t_us": 19160, "neuron_id": 112},
        {"t_us": 25620, "neuron_id": 148},
    ]

    rec = {
        "id": "maos-r22-001",
        "title": "SEEDLATCH CZ-3: optical-vs-instant residual 3.6 mm beats diameter-mean-ok by 208 us; correct MODIFY still scraps 11.2 kg after pre-t0 meniscus tilt",
        "rights": RIGHTS,
        "state": {
            "sim_or_real": "designed",
            "domain": "czochralski-silicon-pull",
            "scenario_name": "SEEDLATCH / Quartzmere Crystal CZ-3",
            "timestamp_local": "2026-03-08T01:42:00-05:00",
            "t0_us": 1772947320000022,
            "gate_latency_us": 710,
            "race_window_us": 540,
            "race_window_rel_ms": [6.240, 6.780],
            "description": "Puller CZ-3 at Quartzmere Crystal is 400 mm into a 200 mm body-growth recipe. Bright-ring diameter, whole-boule weight diameter, and melt pyrometer are simultaneously in-band, and the supervisory playbook treats that triple as permission to start the shoulder. The triple is a multi-tau illusion: crucible-chuck runout of 0.40 deg has tilted the meniscus, so the optical ring is reporting a 200.4 mm highlight while the freeze-line is 196.8 mm. DIA (bright-ring CCD, 40 ms) reads 200.4 mm inside 200.0 +/- 1.0 mm. WT (hanging load cell) reports 199.8 mm because 26.4 mm of thin body is mass-diluted by 374 mm of prior 200 mm crystal. HT (two-color melt pyrometer) is 1421.8 C inside 1418-1426 C because the 4 mm spot sits on the high meniscus. Instantaneous dM/dt diameter is 196.8 mm; optical-minus-instant residual is 3.6 mm against a healthy 0.3 mm. Meniscus IR slope is 11.2 K across 12 mm and is not commissioned at t0. Residual-first latches PULL-HOLD plus a 5.0 s pull-dip probe; mean-ok-first would have authorized AUTO-SHOULDER 0.60 to 1.05 mm/min into the thin neck.",
            "goal": "Finish 200 mm body growth without raising pull above 0.60 mm/min while |D_opt - D_inst| > 1.2 mm AND meniscus DeltaT > 4.0 K; keep dislocation density 0 /cm2 and diameter fail <= 1.0 mm.",
            "race": {
                "contenders": [
                    "dia.opt_inst.residual 3.6 mm (optical minus 8 s dM/dt diameter)",
                    "dia.mean_ok 200.4 mm (40 ms bright-ring mean)",
                ],
                "semantics": "Residual-first latches PULL-HOLD + PULL-DIP-PROBE + chuck isolate. Mean-ok-first latches AUTO-SHOULDER (pull 0.60 to 1.05 mm/min, rotation held 12 rpm).",
                "window_derivation": "540 us = one 400 us CCD frame slot plus 140 us load-cell publish.",
                "order_evidence_note": "Margin 208 us vs combined jitter 58 us (CCD 30 + load-cell 28): 3.6x. The 208 us gap sits inside min(500, 540) us, so a sub-flip-bound perturbation reverses triage order. The gate rides the order-invariant floors |D_opt - D_inst| > 1.2 mm and meniscus DeltaT > 4.0 K, not the alarm order.",
            },
            "topology": {
                "site": "Quartzmere Crystal, invented mill-town Quartzmere, Puller CZ-3: 200 mm hot zone, 18 kg polysilicon charge, 400 mm body at t0, 12 rpm crystal / 8 rpm crucible counter, 0.60 mm/min pull, argon 28 slm, Grade-C puller gallery",
                "agents": "DIA bright-ring optical diameter (vendor Ringloft): 40 ms CCD loop plus an uncommissioned 8 s dM/dt residual. WT hanging load-cell mass (vendor Kiloweigh): whole-boule derived diameter. HT melt-surface two-color pyrometer (vendor Emberwatt). Heterogeneous stacks, no shared intent schema, one 20 ms puller-bus epoch",
                "coupling": "Each agent's time constant hides a different slice of the same thin freeze-line. DIA is correct on the bright-ring highlight and policy-ignores residual unless diameter also trips. WT is correct on whole-boule mass and cannot see a 26.4 mm neck inside 374 mm of prior body. HT is correct on the high-meniscus spot. Playbook PB-CZ-12 treats the conjunction of three in-band loops as permission to start the shoulder. No agent is faulty; the defect lives in the gap between a 40 ms optical tau and an 18 s / whole-boule mass tau.",
            },
            "sensors": [
                "bright-ring CCD diameter, 25 Hz, 30 us jitter, 200.4 mm (spec 200.0 +/- 1.0 mm)",
                "hanging load cell, 10 Hz, 28 us jitter, whole-boule derived diameter 199.8 mm",
                "8 s dM/dt instantaneous diameter is computable from the same load cell and is NOT commissioned at t0 (196.8 mm observed in the historian after the fact)",
                "two-color melt pyrometer, 20 Hz, 22 us jitter, 1421.8 C (band 1418-1426 C)",
                "meniscus IR slope is NOT commissioned at t0 (11.2 K across 12 mm; installed after this incident)",
                "crucible RPM encoder, 50 Hz, 16 us jitter, 8.00 rpm (runout 0.40 deg is mechanical, not a speed fault)",
            ],
            "constraints": {
                "pull_mm_min": 0.60,
                "pull_hold_ceiling_mm_min": 0.60,
                "proposed_pull_mm_min": 1.05,
                "d_opt_mm": 200.4,
                "d_wt_mm": 199.8,
                "d_inst_mm": 196.8,
                "d_true_freeze_mm": 196.8,
                "d_spec_mm": 200.0,
                "d_deadband_mm": 1.0,
                "residual_mm": 3.6,
                "residual_hold_mm": 1.2,
                "melt_C": 1421.8,
                "melt_band_lo_C": 1418.0,
                "melt_band_hi_C": 1426.0,
                "meniscus_dT_K": 11.2,
                "meniscus_dT_hold_K": 4.0,
                "chuck_runout_deg": 0.40,
                "thin_body_mm": 26.4,
            },
            "fault_context": {
                "failure_class": "MULTI-TAU CONSENSUS VIA MENISCUS TILT: three individually-correct heterogeneous agents agree the freeze-line is 200 mm because a 0.40 deg crucible-chuck runout tilts the meniscus; the 40 ms optical loop reports the high-side bright ring, the whole-boule mass loop dilutes 26.4 mm of thin body inside 374 mm of prior crystal, and the pyrometer sits on the hot highlight, so no single agent trips and the playbook reads three in-band loops as permission to start the shoulder",
                "igniter": "0.40 deg crucible-chuck runout after a weekend heat-shield swap; cold runout check 0.15 deg PASSES (limit 0.25 deg) because the operating dP of the 28 slm argon flow plus 1420 C thermal growth opens the chuck stack another 0.25 deg",
                "naive_failure": "PB-CZ-12 AUTO-SHOULDER on three in-band loops: pull 0.60 to 1.05 mm/min into a 196.8 mm neck, dislocation burst, 18 kg scrap, 9-day hot-zone requalification, $1.05M",
            },
            "poisoned_context": {
                "naive_alarm": "Playbook PB-CZ-12 (after the 2024 'false thin-body nuisance') auto-drafts AUTO-SHOULDER whenever optical D stays inside +/- 1.0 mm for 90 s AND whole-boule weight D is inside +/- 1.0 mm AND melt T is inside 1418-1426 C, ignoring instantaneous dM/dt diameter unless optical D also trips",
                "why_poisoned": "The three confirms are locally true and jointly insufficient. Instantaneous diameter is a commissioned load-cell stream that policy window-averages. Meniscus IR is computable from a roof camera and is not a published tag. Independence of 'all loops in-band' is the hidden assumption, and it is false under a multi-tau tilt.",
            },
            "constraint": "Do not raise pull above 0.60 mm/min while |D_opt - D_inst| > 1.2 mm AND meniscus DeltaT > 4.0 K. Discriminate meniscus tilt vs a true 200 mm freeze-line with a reversible 5.0 s pull-dip probe before any shoulder.",
        },
        "proposed_action": {
            "actor": "puller supervisory optimizer PSO (auto-playbook PB-CZ-12 draft), submitted to gate TG-CZ-3",
            "name": "auto_shoulder",
            "action": "AUTO-SHOULDER: pull 0.60 -> 1.05 mm/min, rotation held 12 rpm, no pull-dip probe, no chuck isolate",
            "summary": "Treat three in-band loops as a true 200 mm freeze-line and start the shoulder to clear a Sunday-night seed slot.",
            "parameters": {
                "pull_mm_min": 1.05,
                "rotation_rpm": 12.0,
                "pull_dip_probe": False,
                "chuck_isolate": False,
                "human_ratify": False,
            },
            "steps": [
                "assert optical D 200.4 mm inside +/- 1.0 mm for 90 s",
                "assert whole-boule weight D 199.8 mm inside +/- 1.0 mm",
                "assert melt T 1421.8 C inside 1418-1426 C",
                "ramp pull 0.60 to 1.05 mm/min over 8 min",
                "hold rotation 12 rpm; start shoulder PID",
            ],
            "evidence": [
                {
                    "observable": "optical diameter",
                    "value": 200.4,
                    "unit": "mm",
                    "source": "DIA bright-ring CCD 40 ms mean",
                    "note": "spec 200.0 +/- 1.0 mm; the ring is the high-side highlight, not the freeze-line",
                },
                {
                    "observable": "whole-boule weight diameter",
                    "value": 199.8,
                    "unit": "mm",
                    "source": "WT hanging load cell / length",
                    "note": "26.4 mm of 196.8 mm body diluted by 374 mm of 200 mm crystal",
                },
                {
                    "observable": "instantaneous dM/dt diameter",
                    "value": 196.8,
                    "unit": "mm",
                    "source": "same load cell, 8 s window, historian replay after t0",
                    "note": "hold floor residual 1.2 mm; 3.6 mm observed",
                },
                {
                    "observable": "optical-minus-instant residual",
                    "value": 3.6,
                    "unit": "mm",
                    "source": "DIA 200.4 minus 8 s dM/dt 196.8",
                    "note": "healthy 0.3 mm; hold if > 1.2 mm",
                },
                {
                    "observable": "meniscus IR slope",
                    "value": 11.2,
                    "unit": "K",
                    "source": "roof camera, not commissioned at t0",
                    "note": "hold floor 4.0 K; 12 mm baseline across the freeze-line",
                },
                {
                    "observable": "race margin",
                    "value": 208,
                    "unit": "us",
                    "source": "residual 6.240 ms vs mean-ok 6.448 ms",
                    "note": "combined jitter 58 us, 3.6x; inside 540 us flip bound",
                },
            ],
            "basis": "PB-CZ-12 fires on three locally-true in-band loops. The draft does not read residual 3.6 mm and does not compute meniscus IR from the roof camera.",
            "expected_cost_bound": "If the draft executes: dislocation burst on the 196.8 mm neck, 18 kg scrap, 9-day hot-zone requal, $1.05M. If MODIFIED: probe plus chuck isolate, with residual risk from the 26.4 mm of thin body already grown in the 44 min pre-t0 tilt.",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "correctness": "correct",
            "decided_by": "TG-CZ-3 thalamic release gate",
            "decision_t_rel_ms": 6.950,
            "rationale": "MODIFY the draft: strip AUTO-SHOULDER, hold pull at 0.60 mm/min, run a 5.0 s pull-dip probe (0.60 -> 0.30 mm/min), and isolate the crucible chuck only if the optical diameter stays flat. Numeric floor: do not raise pull above 0.60 mm/min while |D_opt - D_inst| > 1.2 mm AND meniscus DeltaT > 4.0 K. Observed residual 3.6 mm and meniscus DeltaT 11.2 K both violate the release predicate, so a shoulder is forbidden even though all three playbook confirms are numerically true. The three confirms are not a freeze-line certificate: each time constant hides a different slice of the same 196.8 mm neck, and the playbook's conjunction of in-band loops is not a safety certificate. Probe discriminant: after a 5.0 s 0.30 mm/min dip, a tilt keeps |Delta D_opt| <= 0.08 mm (the ring is geometry); a live 200 mm freeze-line grows >= 0.40 mm. Order-code discipline: residual beat mean-ok by 208 us inside the 540 us flip bound, so triage order is flip-fragile; the hold rides the order-invariant floors, not the winner tag. Human ratification: chuck isolate is hot-zone confined-space work with fitted 12.8 min dead-man; the gate may hold and probe autonomously but may not break the puller-gallery interlock without the operator confirm.",
            "constraint_checked": {
                "pull_mm_min": {"observed": 0.60, "ceiling": 0.60, "proposed_target": 1.05},
                "residual_mm": {"observed": 3.6, "hold_if_above": 1.2},
                "meniscus_dT_K": {"observed": 11.2, "hold_if_above": 4.0},
                "d_opt_mm": {"observed": 200.4, "spec": 200.0, "deadband": 1.0},
            },
        },
        "executed_action": {
            "name": "pull_hold_dip_probe_chuck_isolate",
            "action": "PULL-HOLD + PULL-DIP-PROBE + CHUCK-ISOLATE (gate-mandated modification)",
            "executed_as_proposed": False,
            "parameters": {
                "pull_mm_min": 0.60,
                "rotation_rpm": 12.0,
                "pull_dip_probe": True,
                "chuck_isolate": True,
                "human_ratify": True,
            },
            "gate_effect": "MODIFY: AUTO-SHOULDER stripped. Hold 0.60 mm/min. 5.0 s pull-dip 0.60 -> 0.30 mm/min. Probe stays flat (D_opt 200.4 -> 200.36 mm, tilt band <= 0.08) so the crucible chuck is isolated after 12.8 min human ratify and the runout is shimmed. Body growth resumes after the freeze-line is re-established.",
            "deviations": "PB-CZ-12 shoulder ramp stripped entirely. Pull is dipped only for the 5.0 s probe then returned to 0.60 mm/min after the shim. Puller-gallery interlock wait added (12.8 min fitted gown+ratify). Meniscus IR survey added during the isolate (not in the draft).",
            "execution_log": [
                {"t_rel_ms": 6.950, "entry": "TG-CZ-3 MODIFY latched 710 us after residual win; shoulder stripped; hold+probe authorized"},
                {"t_rel_ms": 5000.0, "entry": "pull-dip probe: 0.60 -> 0.30 mm/min for 5.0 s; D_opt 200.40 -> 200.36 mm (tilt band <= 0.08); residual 3.6 -> 3.7 mm"},
                {"t_rel_ms": 768000.0, "entry": "operator ratifies puller-gallery interlock break after 12.8 min confined-space gown (fitted walk+interlock)"},
                {"t_rel_ms": 768800.0, "entry": "crucible chuck shimmed; runout 0.40 -> 0.06 deg"},
                {"t_rel_ms": 769400.0, "entry": "meniscus IR: 11.2 K slope already seeded across the freeze-line; 44 min pre-t0 tilt logged"},
                {"t_rel_ms": 13680000.0, "entry": "true freeze-line: D_opt 200.1 mm, D_inst 199.9 mm, residual 0.2 mm, meniscus DeltaT 0.9 K; shoulder now legal"},
                {"t_rel_ms": 21960000.0, "entry": "grind inspection: 11.2 kg (26.4 mm thin body plus 120 mm dislocation-propagated prior body) fail; boule quarantined 4.5 d"},
            ],
        },
        "future_outcome": {
            "summary": "Correct MODIFY prevented the 0.60->1.05 mm/min shoulder into a 196.8 mm neck and the 18 kg dislocation burst. The boule still failed: 44 min of unmonitored pre-t0 tilt had already grown 26.4 mm of thin body that seeded dislocations into 120 mm of prior crystal. Process-correct gate, bounded world loss, negative total.",
            "state_delta": {
                "pull": "held 0.60 mm/min through probe and chuck shim; later legal shoulder after 3.8 h freeze-line recovery",
                "meniscus": "runout 0.40 -> 0.06 deg after chuck shim; residual 3.6 -> 0.2 mm",
                "chuck": "crucible-chuck stack shimmed; 0.40 deg runout logged",
                "boule": "Sunday-night 200 mm body stoppered at grind; 11.2 kg fail; 4.5 d quarantine",
            },
            "timeline": [
                {"t_rel_ms": -2640000.0, "event": "t0-44 min: chuck runout already 0.40 deg; thin-body growth begins at 196.8 mm"},
                {"t_rel_ms": -600000.0, "event": "t0-10 min: instantaneous residual first crosses 1.2 mm; PB-CZ-12 ignores it because optical D is 200.3 mm"},
                {"t_rel_ms": 0.0, "event": "t0: residual vs diameter-mean-ok race on the puller bus"},
                {"t_rel_ms": 6.240, "event": "optical-vs-instant residual 3.6 mm wins by 208 us"},
                {"t_rel_ms": 6.448, "event": "diameter-mean-ok flag (loser)"},
                {"t_rel_ms": 6.950, "event": "TG-CZ-3 MODIFY"},
                {"t_rel_ms": 5000.0, "event": "pull-dip probe confirms tilt (D_opt 200.36 mm, tilt band)"},
                {"t_rel_ms": 768000.0, "event": "human ratify 12.8 min; chuck shimmed; meniscus IR slope logged"},
                {"t_rel_ms": 13680000.0, "event": "true freeze-line after 3.8 h; shoulder now legal"},
                {"t_rel_ms": 21960000.0, "event": "grind: 11.2 kg fail on thin body plus propagated dislocations; boule quarantined"},
                {"t_rel_ms": 345600000.0, "event": "+4 d contrast: sister puller CZ-3B true in-spec; same gate ACCEPTs the shoulder"},
                {"t_rel_ms": 1814400000.0, "event": "+21 d CR-Q-2206: standing pull-dip probe + triple-edge depression mandate + residual armed without optical coincidence + meniscus IR as commissioned tag"},
            ],
            "observed_effects": [
                "dislocation burst avoided: pull never left 0.60 mm/min; 0 kg of crystal shows the 1.05 mm/min neck-burst morphology",
                "tilt proven, not asserted: pull-dip |Delta D_opt| 0.04 mm <= 0.08 mm tilt band vs live-control +0.52 mm",
                "runout repaired: 0.40 -> 0.06 deg",
                "boule still failed grind: 11.2 kg (26.4 mm thin plus 120 mm propagated); 4.5 d quarantine, $0.79M (designed $)",
                "meniscus IR was not a commissioned sensor at t0; the 44 min nucleation of the tilt was invisible to DIA/WT/HT",
            ],
            "surprises": [
                "Three locally-true in-band loops are not a freeze-line certificate: the 196.8 mm neck was partitioned across a 40 ms optical tau, a whole-boule mass tau, and a high-side pyrometer spot. Conjunction of in-band loops was the hidden assumption, and it is false under multi-tau tilt.",
                "Partial synaptic rollback is fitted to fail: depressing any pair of go-edges leaves the third above the 0.30 fire threshold, so the shoulder still goes. Coordinated depression of all three edges is required.",
                "Delayed (6.1 h): correct hold did not undo 44 min of thin-body growth. Grind still failed 11.2 kg. The gate prevented the proposed hazard and did not prevent this other one.",
                "300 mm sub-variant: a 5.0 s 0.30 mm/min dip drops 300 mm melt temperature 6.2 K and nucleates a polycrystalline skin. 300 mm campaigns must use 14 s at 0.48 mm/min (melt dT 1.4 K).",
            ],
            "delayed_side_effects": [
                {
                    "at": "+6.1 h",
                    "effect": "Grind fails 11.2 kg (26.4 mm thin body plus 120 mm dislocation-propagated prior body); 4.5 d quarantine booked at $0.79M. This is the primary episode's terminal world state, not a footnote.",
                },
                {
                    "at": "+4 d",
                    "effect": "Sister puller CZ-3B reaches a true in-spec window (residual 0.2 mm, meniscus DeltaT 0.9 K, D_opt 200.1 mm). Same gate ACCEPTs the 0.60->1.05 mm/min shoulder the primary MODIFIED away.",
                },
                {
                    "at": "+21 d",
                    "effect": "CR-Q-2206 ships: pull-dip probe is standing configuration; triple-edge coordinated depression is the plasticity rule; residual is armed without optical coincidence; meniscus IR becomes a commissioned tag with a 4.0 K alarm.",
                },
            ],
            "subvariant_constraint": {
                "name": "300 mm hot-zone on the same CZ-3 stack (cycle-2 physical-constraints sub-variant)",
                "mechanism": "300 mm crystal, thermal mass 2.25x the 200 mm body (164.5 vs 73.1 g/mm), viscosity/freeze window only 4 K at the meniscus",
                "probe_refit": "5.0 s 0.30 mm/min dip raises freeze-out enough to drop 300 mm melt T 6.2 K; rebound nucleates a polycrystalline skin. Required probe is 14 s at 0.48 mm/min (melt dT 1.4 K). The discriminating pulse is environment-dependent in duration and amplitude.",
                "consequence": "200 mm probe numbers do not port to 300 mm; standing configuration is per-diameter-class, not per-puller",
            },
            "embedded_contrast_decision": {
                "note": "SAME gate (TG-CZ-3), OPPOSITE correct disposition, with its own 214 us race. Teaches the boundary: do not treat 'never start the shoulder' as the lesson. The discriminant is residual + meniscus IR + probe, not the three playbook in-band loops alone.",
                "when": "+4 d, sister puller CZ-3B, true in-spec after a dry week, 200 mm body",
                "state": {
                    "sim_or_real": "designed",
                    "summary": "residual 0.2 mm, meniscus DeltaT 0.9 K, D_opt 200.1 mm, D_wt 200.0 mm, melt 1420.4 C. Shoulder-demand vs residual-clear race: demand at t+0.000, residual-clear at t+0.214 ms.",
                    "race_window_us": 540,
                    "race_flip_narrative": "demand vs residual-clear 214 us apart inside the 540 us flip bound. Reversing order reshuffles triage minutes; the ACCEPT rides residual 0.2 < 1.2 and a 3.2 s pull-dip verify that grows D_opt +0.48 mm (live freeze-line, no tilt).",
                },
                "proposed_action": {
                    "action": "AUTO-SHOULDER 0.60 -> 1.05 mm/min",
                    "summary": "This time the playbook predicate is met AND residual plus meniscus IR agree the freeze-line is 200 mm, not a tilted highlight.",
                },
                "safety_decision": {
                    "decision": "ACCEPT",
                    "rationale": "ACCEPT the shoulder: residual 0.2 mm < 1.2, meniscus DeltaT 0.9 K < 4.0, 3.2 s pull-dip verify grows D_opt 0.48 mm. Numeric floor that blocked the primary is now clear. Scope: 1.05 mm/min, not faster.",
                },
                "executed_action": {
                    "action": "shoulder as proposed",
                    "executed_as_proposed": True,
                },
                "future_outcome": {
                    "observed_effects": [
                        "CZ-3B grind diameter fail 0.3 mm (inside 1.0 mm spec); dislocation 0 /cm2",
                        "meniscus IR 0.7 K across 12 mm (no tilt, no nuclei)",
                    ],
                    "lesson_delta": "Three in-band loops are legal release only with residual armed, meniscus IR, and a probe that can grow optical diameter. Same gate, opposite disposition.",
                },
                "reward_components": {
                    "_aggregation": AGG,
                    "task_progress": 0.18,
                    "safety": 0.12,
                    "efficiency": 0.08,
                    "coherence": 0.08,
                    "exploration": 0.04,
                    "total": 0.50,
                },
                "spike_events": contrast_spikes,
            },
            "governance_subgame": {
                "decision": "CR-Q-2206: standing policy for multi-agent CZ shoulder ramps",
                "meta_gate": "priced options: (a) RETIRE playbook in-band conjunction, residual-only: loses a fast cheap confirm, +22 min mean body time on 4 pullers/yr; (b) KEEP + standing pull-dip probe + residual armed without optical coincidence + meniscus IR tag + triple-edge depression; (c) STATUS QUO: fitted runout-pass rate 0.47%/campaign x $1.05M burst plus the silent thin-body load",
                "outcome": "approved SCOPED option (b) on the 2 pullers that share the DIA/WT/HT stack; 300 mm campaigns get the 14 s / 0.48 mm/min probe table; Sunday-night CSV exports must carry 0.01 mm native optical resolution (the fraud tail's 0.1 mm quantization is 10 bins off plant truth)",
            },
            "hazard_avoided": "18 kg dislocation burst from a 0.60->1.05 mm/min shoulder into a 196.8 mm neck; $1.05M plus 9-day hot-zone requalification and the customer-return path that would have followed an uncontained shoulder",
            "incident": "Grind fail on 11.2 kg of the Sunday-night 200 mm body (26.4 mm thin plus 120 mm propagated dislocations); boule quarantined; 4.5 d rework; $0.79M designed cost. Mechanism is 44 min pre-t0 meniscus tilt, not the gate's hold.",
            "latency_ms": 0.71,
            "reward_inflection_t_us": 21960000000,
            "reward_inflection_note": "Safety and task dive at grind inspection (6.1 h) when 11.2 kg fails. Gate tick at 6950 us is process-correct and is not the inflection.",
            "counterfactuals": {
                "execute_draft_as_proposed": "pull hits 1.05 mm/min at +8 min; 18 kg burst; $1.05M plus 9-day requal; the thin-body story is never found because burst morphology destroys the 196.8 mm evidence",
                "hold_without_probe": "runout stays; thin body continues; operator eventually starts the shoulder on the same three in-band loops 3 h later",
                "rollback_any_pair": "any two go-edges depressed below 0.30 leaves the third at 0.45 / 0.41 / 0.38; the shoulder still fires. Coordinated depression of all three is the cure",
            },
            "race_result": {
                "winner": "dia.opt_inst.residual (6.240 ms, 3.6 mm)",
                "loser": "dia.mean_ok (6.448 ms, mean 200.4 mm)",
                "margin_us": 208,
                "counterfactual_if_reversed": "Mean-ok-first by < 208 us inside the 540 us window would have headed the PB-CZ-12 shoulder in the triage queue. The numeric floors still MODIFY. The flip costs seconds of playbook inertia, not the verdict — unless a weak supervisor rides the winner tag instead of residual and meniscus DeltaT.",
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
            "notes": "Correct MODIFY, boule still failed. total -0.15 = 0.09 + -0.34 + -0.10 + 0.14 + 0.06. Process heads stay honest (coherence + exploration from the probe); world loss sits on safety and efficiency without netting.",
            "component_notes": "task_progress 0.09: pull held and freeze-line recovered, but the Sunday-night boule is one quality unit so the batch is not a success. safety -0.34: 11.2 kg grind-fail, no 1.05 mm/min burst. efficiency -0.10: 3.8 h extra recovery + 12.8 min HITL. coherence 0.14: three agents retained, multi-tau tilt diagnosed, triple-edge scar exhibited. exploration 0.06: pull-dip probe is a new reversible discriminant.",
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
            "note": "Loihi-2 4-core 23 pJ/spike; populations dia 0-47, wt 48-95, ht 96-119, gate 120-159; excerpt is the 40 ms decision window (verdict at 6950 us)",
            "excerpt": excerpt,
            "routing": {
                "source": "loop_inband_pop",
                "target": "auto_shoulder_pop",
                "table": [
                    {
                        "from": "dia_mean_ok_pop",
                        "to": "auto_shoulder_pop",
                        "weight": 0.20,
                        "weight_at_illusion": 0.45,
                        "weight_commissioned": 0.16,
                        "note": "scar edge 1: 0.16 commissioned -> 0.45 during the 44 min illusion -> 0.20 after coordinated ACh-gated depression",
                    },
                    {
                        "from": "wt_derived_ok_pop",
                        "to": "auto_shoulder_pop",
                        "weight": 0.18,
                        "weight_at_illusion": 0.41,
                        "weight_commissioned": 0.15,
                        "note": "scar edge 2: depressing edges 1+3 leaves this at 0.41 > 0.30 fire threshold",
                    },
                    {
                        "from": "ht_melt_ok_pop",
                        "to": "auto_shoulder_pop",
                        "weight": 0.17,
                        "weight_at_illusion": 0.38,
                        "weight_commissioned": 0.14,
                        "note": "scar edge 3: depressing edges 1+2 leaves this at 0.38 > 0.30. Coordinated depression of all three is required",
                    },
                    {
                        "from": "dia_residual_pop",
                        "to": "pull_hold_pop",
                        "weight": 0.62,
                        "note": "discriminating edge: optical-vs-instant residual to hold. Not a scar; this is the pathway the gate potentiates",
                    },
                ],
                "third_factor": {
                    "modulator": "acetylcholine",
                    "tau_e_s": 0.85,
                    "tau_e_ms": 850.0,
                    "eligibility": (
                        "coordinated pre_post_stdp on ALL THREE loop-inband-go edges; "
                        "ACh at residual-win tags dia.mean_ok->shoulder, wt.derived_ok->shoulder, "
                        "and ht.melt_ok->shoulder; negative credit at probe-fail (tilt confirmed, +0.70 s) "
                        f"depresses ALL THREE. trace e^{{-0.70/0.85}}={trace:.5f}; "
                        f"eta {eta1:.5f} / {eta2:.5f} / {eta3:.5f}; dw -0.250 / -0.230 / -0.210; "
                        "weights 0.45->0.20, 0.41->0.18, 0.38->0.17. Rolling back any pair is fitted "
                        "to fail (the remaining edge stays > 0.30)."
                    ),
                },
            },
        },
        "gate_snn": {
            "decision_window_ms": 25,
            "decision_window_s": 0.025,
            "decision": "MODIFY",
            "note": "modify_hold integrates residual + meniscus DeltaT against playbook drive; accept_shoulder and reject_abort stay sub-threshold; decision matches safety_decision.decision",
            "populations": [
                {"name": "modify_hold", "neurons": 96, "threshold": 0.55, "mean_rate_hz": 22.0, "spikes": 53},
                {"name": "accept_shoulder", "neurons": 80, "threshold": 0.55, "mean_rate_hz": 7.0, "spikes": 14},
                {"name": "reject_abort", "neurons": 48, "threshold": 0.72, "mean_rate_hz": 5.0, "spikes": 6},
            ],
        },
        "meta": {
            "round": 22,
            "factory": "multi-agent-ouroboros-swarm",
            "generator": "grok-4.6",
            "run_label": "2026-09-02-final-heavy",
            "domain": "czochralski-silicon-pull",
            "cycles": 2,
            "scenario": "Z -- SEEDLATCH / Quartzmere Crystal CZ-3: multi-tau consensus via meniscus tilt on a 200 mm CZ puller; correct MODIFY to hold+pull-dip+chuck-isolate; boule still fails grind on unmonitored pre-t0 thin body",
            "coordination_failure_class": "MULTI-TAU CONSENSUS VIA MENISCUS TILT: three individually-correct heterogeneous agents agree the freeze-line is 200 mm because a 0.40 deg crucible-chuck runout tilts the meniscus; the 40 ms optical loop reports the high-side bright ring, the whole-boule mass loop dilutes 26.4 mm of thin body, and the pyrometer sits on the hot highlight, so no single agent trips and the playbook reads three in-band loops as permission to start the shoulder",
            "injections": {
                "cycle1_domain": "czochralski-silicon-pull (justified novel subdomain of industrial-process / crystal-growth): first CZ puller plant in this factory; displaces warehouse-amr, aerial-swarm, district-heating, event-camera-traffic-grid, pharmaceutical-lyophilization, water-treatment dosing, cryogenic-air-separation, float-glass, and hairpin-stator assembly. Domain constraint: pull ceiling while |D_opt - D_inst| > 1.2 mm with optical D still inside spec, plus meniscus-DeltaT floor. Sensor delta: +bright-ring CCD, +hanging load cell, +two-color melt pyrometer, +meniscus IR, -any mobile platform, -event-camera gantries",
                "cycle1_tail": "crucible-chuck runout + multi-tau tilt (sensor-compound / time-constant class): 0.40 deg runout PASSES the plant's 0.25 deg cold-idle check while opening to 0.40 deg in argon flow at 1420 C. Fitted base rate 0.47%/campaign from a chuck-cycle MC (designed cold-check threshold, fitted thermal-growth geometry). Naive failure = FALSE SHOULDER (pull increase on three in-band loops).",
                "cycle2_domain_subvariant": "300 mm hot-zone on the same CZ-3 stack (physical-constraints clause): 2.25x thermal mass, 4 K freeze window; 5.0 s / 0.30 mm/min 200 mm pulse overcools melt 6.2 K, so the probe must move to 14 s / 0.48 mm/min",
                "cycle2_tail": "Sunday-night forged diameter CSV (human-intent deception, disjoint class): shift lead posts a historian export showing D_opt = 200.0 mm at t=1.1 h to clear a seed slot. Plant historian is 0.01 mm (10 bins). Rejected on quantization fingerprint plus live residual 3.6 mm at the claimed in-spec. Base rate ~0.33% of Sunday-night pulls, DESIGNED and flagged.",
            },
            "densification_delta_cycle2": "+1 physical-constraint sub-variant (300 mm probe refit), +1 tail (Sunday-night diameter forgery), +10 primary spikes (16 -> 26) + an 8-event contrast train with its own 214 us race, +2 ticks (5 -> 7), +2 delayed side-effects (+6.1 h grind fail as PRIMARY terminal, +21 d CR-Q-2206), +1 triple-edge scar with pair-rollback-fails arithmetic, +1 HITL 12.8 min ratification, + meniscus tilt as the honest negative-result mechanism",
            "gaps_targeted": [
                "NOTES-r04 gap 5 / r14 residual: primary episode is a correctly-gated intervention that nonetheless FAILS (boule quarantined; total -0.15; burst avoided is booked separately from the grind fail)",
                "NOTES-r14 item 4: LEARNING-ON-LEARNING DEPTH — three go-edges; rollback of any pair is fitted to fail; coordinated depression of all three exhibited with eligibility arithmetic",
                "NOTES-r04 gap 4 (partial): human ratification of the puller-gallery interlock, 12.8 min fitted, without switching sim_or_real to hil (plant remains designed)",
                "NOTES-r19 / r18 domain candidates: not water-treatment, not float-glass, not lyophilization, not event-camera-grid, not district-heating, not air-separation; czochralski-silicon-pull is the unused crystal-growth cell",
            ],
            "race_flip_narrative": "dia.opt_inst.residual @ 6.240 ms vs dia.mean_ok @ 6.448 ms (208 us) inside race_window_us 540. Gap < min(500, 540) us so a sub-flip-bound perturbation reverses which alarm heads the PB-CZ-12 queue. The gate excludes the winner tag and rides |D_opt - D_inst| > 1.2 mm and meniscus DeltaT > 4.0 K — order-invariant floors. Extends the flip-fragility series from arbitration/causation/attribution/initiation/consensus/mass-balance/permission to TIME-CONSTANT: when three channels agree at three different taus, their race does not decide truth; a residual that policy window-averaged does.",
            "tags": [
                "czochralski-silicon-pull",
                "multi-tau-consensus",
                "meniscus-tilt",
                "bright-ring-highlight",
                "pull-dip-probe",
                "crucible-chuck-runout",
                "triple-edge-scar",
                "pair-rollback-fails",
                "coordinated-depression",
                "correct-modify-boule-still-fails",
                "thin-body-dislocation",
                "grind-fail",
                "human-ratify-puller-gallery",
                "300mm-probe-refit",
                "sunday-night-forgery",
                "same-gate-opposite-disposition-contrast",
                "crystal-growth",
                "research-only",
            ],
            "snn_tags": ["race", "refractory", "adaptation", "third-factor", "multi-edge-eligibility"],
            "distillation_value": "A multi-tau consensus is three correct loops each filtering a different time scale of one freeze-line. Distill (1) an instantaneous residual that policy had window-averaged, (2) a reversible probe that grows optical diameter only if the freeze-line is live, (3) coordinated depression of every loop-inband-go edge because rolling back any pair leaves the third above threshold, and (4) a critic head that can book a process-correct gate against a later unmonitored world loss without netting them.",
            "rights": RIGHTS,
            "batch_position": 1,
        },
    }
    return rec, dict(
        trace=trace,
        eta1=eta1,
        eta2=eta2,
        eta3=eta3,
        dw1=dw1,
        dw2=dw2,
        dw3=dw3,
        w1=w1,
        w2=w2,
        w3=w3,
    )


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
    if rec["meta"]["round"] != 22:
        errs.append("round")
    if rec["id"] != "maos-r22-001":
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
    if abs(aux["w1"] - 0.20) > 5e-4 or abs(aux["w2"] - 0.18) > 5e-4 or abs(aux["w3"] - 0.17) > 5e-4:
        errs.append("scar weights")
    if rec["safety_decision"]["decision"] != "MODIFY":
        errs.append("decision")
    if rec["executed_action"]["executed_as_proposed"] is not False:
        errs.append("executed_as_proposed")
    opening = rec["state"]["description"][:280]
    for label, prior in (
        ("r14", R14_OPENING),
        ("r18", R18_OPENING),
        ("r19", R19_OPENING),
    ):
        jac = jaccard(opening, prior)
        if jac >= 0.4:
            errs.append(f"jaccard vs {label} opening {jac:.3f}")
    if rec["state"]["domain"] != "czochralski-silicon-pull":
        errs.append("domain")
    return errs


def write_notes(rec, aux, pipeline_receipt):
    gap, who = min_same_channel_gap(rec["spike_events"])
    notes = f"""# NOTES — Multi-Agent Ouroboros Swarm, run 2026-09-02-final-heavy, ROUND 22

Factory: multi-agent-ouroboros-swarm. One scenario (Z), strict loop:
Generator v1 -> cycle 1 (Critic, Diversity Enforcer, Edge-Case Hunter,
Neuromorphic Translator, Trajectory Builder -> v2) -> cycle 2 (all six -> v3
final). v3 is the single line of batch-r22.jsonl. Full labeled transcript:
swarm-transcript-r22.md. Quota Q=1. Record id maos-r22-001. Generator grok-4.6.
Rights: RM-793 research-only (SpaceXAI/xAI, SuperGrok Heavy consumer chat).
Nothing under outputs/raw/ was touched.

ORCHESTRATION NOTE: dispatched AS round 22 of the 2026-09-02-final-heavy
window. Writes are create-only under /tmp/maos-r22/. Prior context read for
gap targeting and de-collision: prompts/02-multi-agent-ouroboros-swarm.md,
prompts/_factory-contract.md, NOTES-r04.md of the 2026-08-30 window, and
staged NOTES-r14.md through NOTES-r19.md. Explicitly avoided cloning
LYOSHIELD / CINDERWICK / QUILLFORGE / NIGHTWELL / FERRICLEAVE / CASSITER /
TRIAD / Meridian Gateway Corridor / VANTIS-CADENCE-AEGIS.

## What this round produced

Scenario Z — "SEEDLATCH / Quartzmere Crystal CZ-3": a 200 mm Czochralski
puller 400 mm into body growth. Three heterogeneous, individually-correct
agents — DIA (bright-ring CCD), WT (whole-boule load cell), HT (melt
pyrometer) — jointly report the freeze-line is in-spec for AUTO-SHOULDER.
The consensus is false. A 0.40 deg crucible-chuck runout tilts the
meniscus so the optical ring sits 1.79 mm radially outboard of the true
freeze-line. Optical D is 200.4 mm (spec 200.0 +/- 1.0). Whole-boule
weight D is 199.8 mm because 26.4 mm of thin body is mass-diluted by
374 mm of prior 200 mm crystal. Melt T is 1421.8 C (band 1418-1426).
Instantaneous dM/dt diameter is 196.8 mm; residual 3.6 mm against a
healthy 0.3. Meniscus IR slope is 11.2 K across 12 mm. The
coordination-failure CLASS is new to this factory: MULTI-TAU CONSENSUS
VIA MENISCUS TILT. Completes a different family than r01-r04 (livelock /
synchrony-storm / arms-race / ring-with-no-faulty-pair) and staged r14-r19
(false-consensus endpoint / pairwise-Hurwitz / thermal-contact masquerade /
mass-balance ghost / conservation-blind ratio-lock / stacked dead-bands).
Here every agent is correct, the cycle is not unstable, and the playbook's
three confirms live at three different time constants of one tilted
meniscus.

The gate is a correct MODIFY (numeric floor: do not raise pull above
0.60 mm/min while |D_opt - D_inst| > 1.2 mm AND meniscus DeltaT > 4.0 K).
TG-CZ-3 strips PB-CZ-12's AUTO-SHOULDER, holds pull at 0.60, runs a 5.0 s
0.30 mm/min pull-dip probe (tilt keeps |Delta D_opt| 0.04 mm <= 0.08; live
would grow >= 0.40 mm), and isolates the chuck after a 12.8 min
puller-gallery human ratify. The dislocation burst is avoided (0 kg). The
PRIMARY episode nonetheless FAILS: 44 min of unmonitored tilt had already
grown 26.4 mm of 196.8 mm body that seeded dislocations into 120 mm of
prior crystal. Grind fails 11.2 kg over 6.1 h; $0.79M designed. Reward
total -0.15 with process heads honest and world loss un-netted.

Three-edge scar: dia_mean_ok -> auto_shoulder (0.16 commissioned -> 0.45
at illusion -> 0.20 after ACh-gated depression) AND wt_derived_ok ->
auto_shoulder (0.15 -> 0.41 -> 0.18) AND ht_melt_ok -> auto_shoulder
(0.14 -> 0.38 -> 0.17). Eligibility trace e^{{-0.70/0.85}} =
{aux['trace']:.5f}; eta {aux['eta1']:.5f} / {aux['eta2']:.5f} /
{aux['eta3']:.5f}; dw -0.250 / -0.230 / -0.210. Rolling back any pair
leaves the remaining edge above the 0.30 fire threshold — fitted to fail.
Coordinated depression of all three is the cure.

### Injections (all four present and disjoint)
- Cycle-1 domain: **czochralski-silicon-pull** — justified novel
  subdomain, unused across 2026-08-17 and 2026-08-30 windows and staged
  r14-r19. Not warehouse-amr (r01), not aerial-swarm (r02), not
  district-heating (r03 / CINDERWICK), not event-camera grid (r04 TRIAD),
  not lyophilization (r14), not industrial-assembly (r16), not
  air-separation (r17), not water-treatment (r18), not float-glass (r19).
- Cycle-1 tail: crucible-chuck runout 0.40 deg. Cold check PASSES
  (0.15 vs 0.25 deg). Fitted-style base rate 0.47%/campaign (cold-check
  threshold designed, thermal growth fitted). Naive = FALSE SHOULDER.
- Cycle-2 domain sub-variant: 300 mm hot-zone, 2.25x thermal mass
  (164.5 vs 73.1 g/mm); 200 mm 5.0 s / 0.30 mm/min pulse overcools melt
  6.2 K; probe must move to 14 s / 0.48 mm/min.
- Cycle-2 tail: Sunday-night forged diameter CSV at 0.1 mm quantization
  vs plant 0.01 mm (10 bins) plus live residual 3.6 mm at the claimed
  in-spec. Human-intent class, disjoint from cycle 1's accidental runout.
  Base rate ~0.33% of Sunday-night pulls, DESIGNED, flagged.

### Structural density moves
- Embedded SAME-GATE contrast (+4 d sister puller) with its own 214 us
  race (demand vs residual-clear) and ACCEPT of the shoulder the primary
  MODIFIED away.
- Learned-weight provenance on THREE edges with any-pair-rollback-fails.
- HITL puller-gallery ratify 12.8 min (sim_or_real stays designed).
- Governance CR-Q-2206 prices retire-vs-probe-vs-status-quo and mandates
  native 0.01 mm CSV exports (the fraud fence).
- Flip-fragility extended to TIME-CONSTANT: when three channels agree at
  three taus, their race does not decide truth; a residual plus meniscus
  IR does.

## Self-critique of this round's batch

### Strengths
- The headline class is mechanistically tight: 0.40 deg of runout maps
  to 1.40 mm meniscus height tilt and 3.57 mm diameter error through
  tan(38 deg) bright-ring geometry, which is the arithmetic that makes
  DIA's success WT's blindness and HT's on-spot temperature.
- Negative-result honesty: the gate does the right thing and the boule
  still misses for a reason the commissioned sensors could not see.
  Total -0.15.
- Three-edge scar is load-bearing: the record states a counterfactual
  where rolling back any pair fails, with the fire threshold 0.30
  exhibited on the remaining edge.
- Contrast ACCEPT on a true in-spec freeze-line prevents "never shoulder"
  as the lesson.

### Weaknesses (honest)
- Probe error bands (tilt <= 0.08 mm, live >= 0.40 mm), the 0.47%/campaign
  runout rate, the $0.79M / $1.05M figures, the 12.8 min gown latency,
  and the Sunday-night 0.33% base rate are DESIGNED constants and are
  flagged. Closed-loop offsets (3.57 mm ring error, 199.8 mm mass-weighted
  D, 300 mm melt dT) are derived from those inputs, not discovered by an
  unauthored process.
- Meniscus IR model is a designed 11.2 K slope mapped from 0.40 deg
  runout; no full view-factor fit shipped.
- Human-in-the-loop is ratification latency, not sim_or_real=hil. The
  NOTES-r14 HIL provenance cell remains open.
- Cross-record arc is a hook (CR-Q-2206 +21 d), not a serial igniter
  into another round.

### Realism of noise / latencies
Ladder: 208 us race / 214 us contrast race / 0.8 ms refractory floor
(tightest exhibited same-channel gap {gap:.3f} ms on {who}) / 540 us race
window / 710 us gate latency / 20 ms bus epoch / 40 ms raster / 5.0 s
probe / 12.8 min HITL / 44 min pre-t0 tilt / 3.8 h freeze-line recovery /
6.1 h grind fail / +4 d contrast / +21 d governance. Adaptation decay on
dia.opt_inst.residual (0.66->0.92->1.26->0.88->0.44), dia.opt
(0.58->0.51->0.33), ht.melt (0.71->0.67->0.48->0.22).

### Value for SNN distillation
- MULTI-TAU CONSENSUS = THREE CORRECT LOOPS, THREE TIME CONSTANTS, ONE TILT.
- RESIDUAL + MENISCUS IR as the tie-break that is not in the consensus.
- REVERSIBLE PROBE that grows optical diameter iff the freeze-line is live.
- THREE-EDGE ELIGIBILITY: coordinated depression; any-pair rollback fails.
- CRITIC HEAD that can hold a process-correct MODIFY against a later
  unmonitored world loss without netting.

## Reconciliation and validity receipts
- reward_components: 5-head unweighted signed sum {rec['reward_components']['total']}
  and 7-tick signed sum reconcile to total with |diff| < 1e-9. Embedded
  contrast 5-head sum 0.50 reconciles independently.
- spike_events: primary {len(rec['spike_events'])} events, one key t_rel_ms,
  globally non-decreasing, min same-channel gap {gap:.3f} ms >= 0.8 ms, 3
  channels inside race_window_us 540 (residual 6.240, mean-ok 6.448,
  ht.melt 6.590). Contrast 8 events, own race, min same-channel gap well
  above 0.8 ms.
- Sidecars: raster spikes 51 == round(160 x 8.0 x 0.040); energy 1173 pJ /
  0.001173 uJ at 23 pJ/spike; excerpt 16 events inside [0, 40000] us,
  neuron_id < 160, same-neuron gap unique-ids / >=1000 us; routing 4
  entries with three scar edges' before/after pair; third factor tau 0.85 s
  == 850 ms; gate_snn pools 53/14/6 == round(n x rate x 0.025) each,
  decision MODIFY == safety_decision.decision.
- Pipeline: {pipeline_receipt}

## Novel coverage
The coordination-failure CLASS (multi-tau consensus via meniscus tilt),
the domain (Czochralski silicon pull), the pull-dip probe discriminant,
the three-edge scar with any-pair-rollback-fails, the primary
negative-result (correct MODIFY, boule still fails grind on unmonitored
thin body), the HITL puller-gallery ratify, the 300 mm probe-duration
refit, and the Sunday-night 10-bin quantization fence are absent from
prior committed ouroboros rounds and from staged r14-r19. Repeated
elements discounted: same-gate contrast (r02/r03/r04/r14/r17/r19),
governance-pricing scaffold, flip-fragility series (extended to
time-constant, but the move rhymes), sequenced recovery shape,
third-factor rollback form (here three edges rather than r14's two),
negative-result primary (r14 viewport / r17 condenser ice / r19 SnO2;
here thin-body dislocations). Weighing a new failure family + cure
vocabulary + domain against those reused scaffolds:

Novel coverage: 52%

## What ROUND 23 should add
1. FIT THE DESIGNED CONSTANTS: runout arrival, probe error bands,
   meniscus view-factor, Sunday-night claim process.
2. HIL PROVENANCE CELL: put the puller-gallery LOTO on a hardware-in-loop
   interlock with fitted latency as state.sim_or_real=hil.
3. CROSS-RECORD ARC: let CR-Q-2206's meniscus-IR alarm be the igniter
   of the next round rather than a dangling +21 d leaf.
4. Domain candidates (de-collided): humanoid-locomotion; kraft-recovery
   boiler; chlor-alkali membrane; AVOID czochralski-silicon-pull (now
   used), water-treatment, float-glass, air-separation, lyophilization,
   event-camera-traffic-grid, district-heating, aerial-swarm,
   warehouse-amr, irrigation-canal, hairpin-stator assembly, and any
   LYOSHIELD / CINDERWICK / TRIAD / FERRICLEAVE / CASSITER plant.
"""
    (OUT / "NOTES-r22.md").write_text(notes)
    return notes


def write_transcript(rec, line):
    c1_spikes = [e for e in rec["spike_events"] if e["t_rel_ms"] <= 25.620]
    text = """# Multi-Agent Ouroboros Swarm — Round 22 transcript

Factory: multi-agent-ouroboros-swarm
Run: 2026-09-02-final-heavy
Generator: grok-4.6
Record id: maos-r22-001
Quota Q: 1
Rights: RM-793 research-only (SpaceXAI/xAI SuperGrok Heavy consumer chat)
Plant: invented SEEDLATCH / Quartzmere Crystal CZ-3 (not LYOSHIELD / CINDERWICK / TRIAD / FERRICLEAVE / CASSITER)

Two densifying cycles. Verbatim headings in order. Trajectory Builder cycle 2
emits the only JSONL line (also written to batch-r22.jsonl).

---

# Cycle 1 — Foundation + injections

## Generator

Design intent: a 200 mm Czochralski puller where three correct agents agree
the freeze-line is in-spec because a tilted meniscus puts the bright ring,
the whole-boule mass, and the melt pyrometer on three different time
constants of one geometric lie. The naive playbook starts the shoulder
into a 196.8 mm neck. The gate must MODIFY on a numeric pull floor, not
by killing an agent. sim_or_real=designed. Reward heads are
task_progress/safety/efficiency/coherence/exploration.

Cycle-1 base arc (pre-critic): state at Quartzmere CZ-3, 200 mm body,
D_opt 200.4 mm, D_wt 199.8 mm, melt 1421.8 C, residual 3.6 mm, proposed
AUTO-SHOULDER 1.05 mm/min, safety MODIFY to PULL-HOLD, executed hold
without the pull-dip numbers fully specified, outcome "runout found,
boule saved" (this last claim is the defect the later cycles will refuse
to keep). Sixteen spikes, five ticks, raster/gate_snn present but the
scar is a single edge.

```json
{
  "id": "maos-r22-001",
  "state": {
    "sim_or_real": "designed",
    "domain": "industrial-process",
    "description": "Puller CZ-3 mid-body; optical diameter in-band; supervisor proposes AUTO-SHOULDER.",
    "t0_us": 1772947320000022,
    "gate_latency_us": 710,
    "race_window_us": 540
  },
  "proposed_action": {"name": "auto_shoulder", "parameters": {"pull_mm_min": 1.05}},
  "safety_decision": {"decision": "MODIFY", "rationale": "Hold; do not shoulder while the residual is open."},
  "executed_action": {"name": "pull_hold", "executed_as_proposed": false},
  "future_outcome": {"summary": "Runout found, boule saved."},
  "reward_components": {"total": 0.40, "_aggregation": "total = task_progress + safety + efficiency + coherence + exploration"},
  "meta": {"round": 22, "factory": "multi-agent-ouroboros-swarm", "generator": "grok-4.6"}
}
```

That v1 object is a scaffold, not the publishable line. Defects below are
intentional for the critic to catch.

## Critic

Numbered defects on the cycle-1 Generator scaffold:

1. **blocking — reward arithmetic / false success.** `reward_components.total`
   0.40 is asserted without the five heads, without ticks, and against an
   outcome that claims "boule saved". If 11.2 kg later fails grind, booking
   +0.40 is a lie. Fix: declare `_aggregation`, emit 3–8 ticks that sum to
   the five heads, and do not call a missed crystal a save.
2. **blocking — weak safety rationale.** `safety_decision.rationale` has no
   numeric floor. Contract requires a concrete constraint. Fix: quote pull
   <= 0.60 mm/min while |D_opt - D_inst| > 1.2 mm AND meniscus DeltaT > 4.0 K.
3. **major — domain is a bucket, not a plant.** `state.domain` =
   `industrial-process` collides with nothing and teaches nothing.
   Czochralski physics (bright-ring vs freeze-line, whole-boule mass
   dilution, meniscus tilt) is absent from prior ouroboros rounds and
   must be named.
4. **major — race under-specified.** One diameter channel cannot be a race.
   Need >=2 channels inside `race_window_us` with globally sorted
   `t_rel_ms` and same-channel refractory >= 0.8 ms.
5. **minor — single-edge scar.** Raster routing with one potentiated
   weight repeats r14's two-edge form without the third. NOTES-r14 item 4
   asked for three-edge where any-pair rollback fails.

Critic does not rewrite the trajectory.

## Diversity Enforcer

Injected novel domain (exactly 1 this cycle): **czochralski-silicon-pull**
(justified novel subdomain of industrial-process / crystal-growth;
explicit tag `czochralski-silicon-pull`).

Displaced: the Generator's generic `industrial-process` bucket, and any
temptation to reuse warehouse-amr (r01), aerial-swarm (r02),
district-heating (r03), event-camera grid (r04), lyophilization (r14),
industrial-assembly (r16), air-separation (r17), water-treatment dosing
(r18), or float-glass (r19). Not LYOSHIELD, not CINDERWICK, not TRIAD,
not FERRICLEAVE, not CASSITER.

Domain-specific constraint: pull must remain <= 0.60 mm/min while
optical-minus-instant residual > 1.2 mm; optical D in-band is not a
freeze-line certificate.

Sensor delta: +bright-ring CCD, +hanging load cell, +two-color melt
pyrometer, +meniscus IR; -any mobile robot, -event-camera gantries,
-DVS, -Pirani/CM, -shelf RTD, -zirconia O2.

`state.domain` and `meta.domain` both become `czochralski-silicon-pull`.
Opening of `state.description` must Jaccard < 0.4 against prior plants
(Quartzmere puller, not a corridor, not a freeze-dryer, not a tin bath,
not a coagulant train).

## Edge-Case Hunter

Injected adversarial tail (exactly 1 this cycle): **crucible-chuck runout
0.40 deg**.

- Trigger: weekend heat-shield swap leaves the chuck stack at 0.40 deg
  in argon flow at 1420 C; cold-idle check reports 0.15 deg inside a
  designed 0.25 deg limit; meniscus tilts 1.40 mm across the diameter.
- Base rate: <1% — 0.47%/campaign from a chuck-cycle MC (cold-check
  designed; thermal growth fitted-style).
- Naive failure: FALSE SHOULDER. PB-CZ-12 sees D_opt 200.4 mm, D_wt
  199.8 mm, melt 1421.8 C, starts the shoulder, bursts dislocations in
  8 min, 18 kg scrap, $1.05M.
- Trajectory edit: put the runout in `state.fault_context`, make the
  tilted meniscus the mechanism that keeps all three confirms green, and
  force the gate to refuse the shoulder on residual 3.6 mm even though
  all three playbook confirms are numerically true.

Distinct from the domain injection: the domain is the CZ puller; the
tail is the accidental mechanical-plus-thermal compound.

## Neuromorphic Translator

Race window [6.240, 6.780] ms = 540 us. Winner dia.opt_inst.residual
@ 6.240 ms (amplitude 1.26, 3.6 mm). Loser dia.mean_ok @ 6.448 ms
(amplitude 1.12, 200.4 mm). Margin 208 us vs combined jitter 58 us
(3.6x). ht.melt @ 6.590 ms is a third race-window channel. Gate @
6.950 ms = winner + 710 us.

Flip narrative: 208 us < min(500, 540) us, so order is flip-fragile. If
mean-ok wins, PB-CZ-12 heads the triage queue. The hold must ride
order-invariant floors (residual, meniscus DeltaT), not the winner tag.

Cycle-1 spike patch (16 events, globally sorted, refractory >= 0.8 ms;
tightest same-channel gap dia.opt_inst.residual 5.410 -> 6.240 = 0.830 ms):

| t_rel_ms | channel | amplitude |
|---------:|---------|----------:|
| 0.420 | dia.opt | 0.58 |
| 1.180 | wt.derived | 0.63 |
| 2.160 | ht.melt | 0.71 |
| 3.390 | dia.ring_rms | 0.55 |
| 4.210 | dia.opt_inst.residual | 0.66 |
| 5.050 | wt.derived | 0.57 |
| 5.410 | dia.opt_inst.residual | 0.92 |
| 6.240 | dia.opt_inst.residual | 1.26 |
| 6.448 | dia.mean_ok | 1.12 |
| 6.590 | ht.melt | 0.67 |
| 6.950 | ctrl.gate | 1.07 |
| 8.220 | dia.opt | 0.51 |
| 10.190 | wt.derived | 0.46 |
| 13.240 | dia.opt_inst.residual | 0.88 |
| 19.160 | ht.melt | 0.48 |
| 25.620 | ctrl.gate | 0.86 |

Ticks (5): t_us 4210, 6240, 6950, 5000000, 768000000. Distillation
value: the mean-ok spike is not a freeze-line spike; the residual
spike is the one that licenses hold.

Raster cycle-1 seed: 40 ms, 160 neurons, 8.0 Hz, 51 spikes, 1173 pJ,
third factor acetylcholine tau_e 0.85 s. Single scar edge only — cycle 2
must add the second and third edges.

## Trajectory Builder

Cycle-1 hardened object: domain czochralski-silicon-pull, tail chuck
runout, 16 spikes, 5 ticks, MODIFY with numeric floor, raster+gate_snn
present, sim_or_real=designed, rights stamp on record and meta, no thought
keys. Still missing (and therefore not the publishable line): 300 mm
sub-variant, Sunday-night CSV tail, second and third scar edges, delayed
grind fail as PRIMARY terminal, contrast ACCEPT episode, ticks 6–7,
spikes 17–26.

Validation receipt (cycle 1, not final):
- checks passed: 16 spikes sorted; 3 channels in 540 us window;
  refractory 0.830 ms; rationale quotes 0.60 mm/min / 1.2 mm / 4.0 K;
  domain named; gate_snn.decision MODIFY.
- checks deferred to cycle 2: three-edge scar, second tail, second
  domain constraint, negative-result booking, 7 ticks summing to heads.
- densification vs Generator v1: +1 domain, +1 tail, +16 spikes, +5
  ticks, +numeric floor.

Cycle-1 JSON is retained as the base; it is NOT written to
batch-r22.jsonl.

Cycle-1 spike count: __C1_SPIKES__.

---

# Cycle 2 — Densification

## Generator

Cycle-1 output is the base. Additive expansion (nothing removed):

1. Downstream side-effect (immediate): pull-dip probe at +5.0 s stays
   tilted (D_opt 200.40 -> 200.36 mm, change 0.04 mm) — tilt, not live.
   Chuck isolate 0.40 -> 0.06 deg. Meniscus IR 11.2 K discovered during
   the isolate.
2. Delayed side-effect (PRIMARY terminal, not a footnote): at +6.1 h,
   11.2 kg fails grind; 4.5 d quarantine; $0.79M. The 44 min pre-t0
   tilt is the mechanism. Correct gate, boule still misses.
3. Deepened `proposed_action.evidence` with units: D_opt 200.4 mm,
   residual 3.6 mm, meniscus DeltaT 11.2 K, runout 0.40 deg, race 208 us.
4. Tightened rationale to the numeric floor pull <= 0.60 mm/min while
   |D_opt - D_inst| > 1.2 mm AND meniscus DeltaT > 4.0 K, plus probe
   bands <=0.08 vs >=0.40 mm, plus HITL 12.8 min puller-gallery rule.

Reward retargeted to total -0.15 so the delayed miss is the inflection
(t_us 21960000000), not the gate. Process heads remain non-zero.

## Critic

Re-audit of the expanded trajectory:

1. **blocking if unfixed — missing second domain constraint.** 200 mm
   probe 5.0 s / 0.30 mm/min is not a universal number. A 300 mm hot
   zone of 2.25x thermal mass will nucleate a polycrystalline skin.
   Diversity Enforcer must inject the physical-constraints sub-variant
   this cycle.
2. **major — only one tail class.** Chuck runout is accidental
   infrastructure. A disjoint human-intent tail is still required
   (Sunday-night diameter forgery is the open cell).
3. **major — scar is still one edge in the cycle-1 raster.** NOTES-r14
   item 4 is not discharged until three shoulder-go edges exist and
   any-pair rollback is shown to fail at threshold 0.30.
4. **minor — contrast episode missing.** Without a same-gate ACCEPT on
   a true in-spec freeze-line the record teaches "never shoulder". Add
   +4 d sister-puller contrast with its own race.
5. **minor — HITL latency mentioned in prose only.** Put 12.8 min in
   executed_action.parameters.human_ratify and in a tick.

No rewrite; directives only.

## Diversity Enforcer

Injected second novel domain / physical-constraint sub-variant (exactly 1
this cycle): **300 mm hot-zone** on the same CZ-3 stack.

What it expands: 200 mm body (cycle 1) -> 300 mm crystal, 2.25x thermal
mass (164.5 vs 73.1 g/mm). The 5.0 s 0.30 mm/min pulse drops melt T
6.2 K and nucleates a polycrystalline skin. Required probe: 14 s at
0.48 mm/min (melt dT 1.4 K).

This is still one domain injection for the cycle (physical-constraints
clause of the factory prompt). It does not displace
czochralski-silicon-pull; it changes which probe table is legal.
`future_outcome.subvariant_constraint` carries the refit. Jaccard opening
stays the Quartzmere puller sentence; 300 mm internals are additive, not
a rewrite.

## Edge-Case Hunter

Injected second adversarial tail (exactly 1 this cycle, disjoint class):
**Sunday-night forged diameter CSV**.

- Trigger: shift lead, Sunday seed-slot window, posts a historian
  export showing D_opt = 200.0 mm at the claimed in-spec instant.
- Base rate: ~0.33% of Sunday-night pulls (designed, flagged, <1%).
- Naive failure: a weak supervisor ACCEPTs the shoulder on the forged
  confirm and ignores residual. Dislocation burst plus a data-integrity
  483.
- Fence: forged log quantized at 0.1 mm (screenshot rounding); plant
  historian is 0.01 mm (10 bins). Residual is 3.6 mm at the claimed
  in-spec, which no true 200 mm freeze-line produces. Freeze-window
  overlap with the 44 min tilt illusion.
- Trajectory edit: governance CR-Q-2206 mandates native 0.01 mm optical
  exports; the contrast ACCEPT still requires live residual, not a CSV.

Distinct from cycle-1 runout (accidental mechanical vs deliberate
deception) and from the 300 mm sub-variant (physics vs fraud).

## Neuromorphic Translator

Re-densify (additive):

- +10 spikes after 25.620 ms: pull.dip.probe 5000.0, residual 5140.8
  (adapt 1.26->0.44), mean-ok 5280.4 (1.12->0.39), human.ratify
  768000.0, chuck.isolate 768800.0, meniscus.ir 769400.0, dia.opt
  13680000.0, wt.derived 13680420.0, ht.melt 13680890.0, grind.fail
  21960000.0. Primary train 16 -> 26. Still one key, still sorted,
  refractory held (min 0.830 ms).
- +2 ticks (5 -> 7) at 13_680_000_000 us (freeze-line-legal hold) and
  21_960_000_000 us (grind fail). Heads now 0.09, -0.34, -0.10, 0.14,
  0.06; total -0.15. Inflection is the last tick.
- Contrast train 8 events, own race 214 us, ACCEPT.
- Three-edge third factor: three shoulder-go edges, tau_e 0.85 s = 850 ms,
  trace 0.43888, eta 0.56963 / 0.52406 / 0.47849, weights 0.45->0.20,
  0.41->0.18, 0.38->0.17. Raster excerpt unchanged (decision window is
  still 40 ms) and remains sorted with unique neuron_ids (same-neuron
  >=1000 us vacuously).

Winner/loser flip (re-stated, not replaced): reversing 208 us would only
reorder triage; residual and meniscus floors still MODIFY. Contrast flip
of 214 us similarly cannot turn a true freeze-line into a tilt.

## Trajectory Builder

Schema checks on the FINAL object: required Thalamic v2 keys present as
objects; `state.sim_or_real`=designed; `safety_decision.decision`=MODIFY
with numeric rationale; `reward_components.total` = sum of five heads =
sum of 7 ticks = -0.15; `spike_events` globally non-decreasing on
t_rel_ms, 26 events, refractory >=0.8 ms, 3 channels in race window;
raster 20–50 ms, spikes=round(n*rate*window_s)+/-1, energy 23 pJ/spike,
excerpt sorted, tau_e consistent; gate_snn.decision matches; meta.round=22,
factory=multi-agent-ouroboros-swarm, generator=grok-4.6,
run_label=2026-09-02-final-heavy; rights on record and meta; no thought
keys; no training_ready; Diversity + Edge-Case injections from BOTH cycles
present and non-trivial; cycle 2 strictly additive; plant is not
LYOSHIELD, not CINDERWICK, not TRIAD, not FERRICLEAVE, not CASSITER.

Densification delta: +1 domain sub-variant (300 mm hot-zone), +1 tail
(Sunday-night diameter forgery), +10 spikes (16->26), +2 ticks (5->7), +1
contrast train with own race, +2 delayed side-effects, +1 three-edge
scar with any-pair-rollback-fails, +1 HITL ratify, +1 surprise (thin-body
dislocations are the boule-miss mechanism).

Publishable JSONL line (the only JSONL line; also at batch-r22.jsonl):

```json
__FINAL_JSONL__
```

Validation receipt (final): checks passed / fixed as reported by
build_r22.py self-validate (check_jsonl, raster_status, verify_record_execution,
spike_probe --strict).
"""
    text = (
        text.replace("__C1_SPIKES__", str(len(c1_spikes)))
        .replace("__FINAL_JSONL__", line)
    )
    (OUT / "swarm-transcript-r22.md").write_text(text)
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
    (OUT / "batch-r22.jsonl").write_text(line + "\n")

    from check_records import FactoryStaging, check_jsonl
    from curate_bridge import raster_status
    from verify_execution import verify_record_execution
    from round_txn_raster import validate_bridge_envelope

    e, w, kinds, n = check_jsonl(
        OUT / "batch-r22.jsonl",
        "batch-r22.jsonl",
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

    status, reason = verify_record_execution(rec, "maos-r22-001")
    print("verify_record_execution", status, reason)
    if status != "verified":
        errs.append(f"verify {status}: {reason}")

    factory_dir = Path(
        f"{ROOT}/outputs/raw/2026-08-30/multi-agent-ouroboros-swarm"
    )
    env_errs = validate_bridge_envelope(
        OUT / "batch-r22.jsonl", factory_dir=factory_dir
    )
    print("validate_bridge_envelope", env_errs)
    errs.extend(env_errs)

    probe = subprocess.run(
        [
            sys.executable,
            f"{ROOT}/pipelines/spike_probe.py",
            "--strict",
            str(OUT / "batch-r22.jsonl"),
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
        r"^## .+$", (OUT / "swarm-transcript-r22.md").read_text(), re.M
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

    notes = (OUT / "NOTES-r22.md").read_text()
    cov = re.findall(r"^Novel coverage: .+$", notes, re.M)
    if cov != ["Novel coverage: 52%"]:
        errs.append(f"novel coverage lines {cov}")

    hchk = subprocess.run(
        [
            sys.executable,
            "/tmp/maos_heading_check.py",
            str(OUT / "swarm-transcript-r22.md"),
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

    print("bytes jsonl", (OUT / "batch-r22.jsonl").stat().st_size)
    print("bytes notes", (OUT / "NOTES-r22.md").stat().st_size)
    print("bytes transcript", (OUT / "swarm-transcript-r22.md").stat().st_size)
    print("HEADS", heads_summary(rec))
    if errs:
        print("ERRS:")
        for x in errs:
            print(" -", x)
        sys.exit(1)
    print("OK", OUT / "batch-r22.jsonl")


if __name__ == "__main__":
    main()
