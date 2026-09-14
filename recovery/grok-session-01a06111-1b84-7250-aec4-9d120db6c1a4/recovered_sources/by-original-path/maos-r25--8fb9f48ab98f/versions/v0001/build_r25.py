#!/usr/bin/env python3
"""Build and self-check MAOS round-25 JSONL (research-only; not published)."""
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

GEN_AT = "2026-09-02T22:08:00Z"
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
OUT = Path("/tmp/maos-r25")
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
    "training_ready",
    "OXBOWREEL",
    "Oystermere",
    "CASSITER",
    "Marshfloat",
    "FERRICLEAVE",
    "Pellwater",
    "NIGHTWELL",
    "QUILLFORGE",
    "Brackmere",
    "REDHALL",
    "Gullmere",
    "STRIAFOIL",
    "Kelpholt",
    "SEEDLATCH",
    "Quartzmere",
    "MURENA",
    "LYO-4",
)
R14_OPENING = (
    "Helixmere Biologics Building C lyophilizer LYO-4 is mid-primary on 8400 "
    "vials of a monoclonal antibody"
)
R19_OPENING = (
    "Marshfloat Floatworks Line TB-5 is mid-draw on 6.0 mm architectural ribbon "
    "when three heterogeneous, individually-correct agents each report their "
    "local loop in-spec"
)
R20_OPENING = (
    "Oystermere Subsea Pad UP-3 work-class ROV is mid-hot-stab on a 4-slot UTA "
    "at 86 m when three heterogeneous, individually-correct agents jointly report"
)
R22_OPENING = (
    "Puller CZ-3 at Quartzmere Crystal is 400 mm into a 200 mm body-growth recipe"
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


def jaccard(a, b):
    sa = set(a.lower().split())
    sb = set(b.lower().split())
    return len(sa & sb) / max(1, len(sa | sb))


def build_record():
    ticks, heads = cents_ticks(
        [4480, 6448, 7168, 5_200_000, 744_000_000, 12_240_000_000, 20_880_000_000],
        [
            (1, -2, -1, 1, 1),
            (2, -4, -1, 3, 1),
            (2, -6, -2, 4, 2),
            (2, -6, -2, 3, 1),
            (1, -7, -2, 2, 1),
            (0, -6, -2, 1, 1),
            (0, -5, -1, 1, 0),
        ],
    )
    assert abs(heads["total"] - (-0.17)) < 1e-9, heads

    trace = math.exp(-0.72 / 0.90)
    eta1 = (0.46 - 0.22) / trace
    eta2 = (0.41 - 0.19) / trace
    eta3 = (0.38 - 0.17) / trace
    dw1 = eta1 * 1.0 * trace
    dw2 = eta2 * 1.0 * trace
    dw3 = eta3 * 1.0 * trace
    w1 = 0.46 - dw1
    w2 = 0.41 - dw2
    w3 = 0.38 - dw3
    assert abs(w1 - 0.22) < 5e-4, w1
    assert abs(w2 - 0.19) < 5e-4, w2
    assert abs(w3 - 0.17) < 5e-4, w3

    spike_events = [
        {"channel": "enc.theta", "t_rel_ms": 0.360, "amplitude": 0.56},
        {"channel": "strn.blade", "t_rel_ms": 1.180, "amplitude": 0.63},
        {"channel": "torq.pitch", "t_rel_ms": 2.040, "amplitude": 0.70},
        {"channel": "pwr.mw", "t_rel_ms": 3.280, "amplitude": 0.58},
        {"channel": "enc.theta", "t_rel_ms": 4.210, "amplitude": 0.53},
        {"channel": "strn.blade", "t_rel_ms": 4.880, "amplitude": 0.66},
        {"channel": "torq.pitch", "t_rel_ms": 5.400, "amplitude": 0.64},
        {"channel": "strn.blade", "t_rel_ms": 6.448, "amplitude": 1.32},
        {"channel": "enc.in_band", "t_rel_ms": 6.624, "amplitude": 1.18},
        {"channel": "torq.pitch", "t_rel_ms": 6.850, "amplitude": 0.61},
        {"channel": "ctrl.gate", "t_rel_ms": 7.168, "amplitude": 1.08},
        {"channel": "enc.theta", "t_rel_ms": 8.940, "amplitude": 0.49},
        {"channel": "strn.blade", "t_rel_ms": 10.880, "amplitude": 0.88},
        {"channel": "pwr.mw", "t_rel_ms": 13.040, "amplitude": 0.50},
        {"channel": "torq.pitch", "t_rel_ms": 18.600, "amplitude": 0.48},
        {"channel": "ctrl.gate", "t_rel_ms": 26.400, "amplitude": 0.92},
        {"channel": "pitch.step.probe", "t_rel_ms": 5200.0, "amplitude": 0.97},
        {"channel": "strn.blade", "t_rel_ms": 5288.4, "amplitude": 0.42},
        {"channel": "enc.in_band", "t_rel_ms": 5370.2, "amplitude": 0.38},
        {"channel": "human.ratify", "t_rel_ms": 744000.0, "amplitude": 0.82},
        {"channel": "spline.lock", "t_rel_ms": 744900.0, "amplitude": 0.74},
        {"channel": "bearing.ir.spall", "t_rel_ms": 745600.0, "amplitude": 0.86},
        {"channel": "enc.theta", "t_rel_ms": 12240000.0, "amplitude": 0.33},
        {"channel": "strn.blade", "t_rel_ms": 12240680.0, "amplitude": 0.31},
        {"channel": "torq.pitch", "t_rel_ms": 12241420.0, "amplitude": 0.28},
        {"channel": "bearing.spall", "t_rel_ms": 20880000.0, "amplitude": 0.93},
    ]

    contrast_spikes = [
        {"channel": "pwr.demand", "t_rel_ms": 0.000, "amplitude": 0.84},
        {"channel": "strn.clear", "t_rel_ms": 0.188, "amplitude": 0.79},
        {"channel": "enc.theta", "t_rel_ms": 0.410, "amplitude": 0.24},
        {"channel": "torq.pitch", "t_rel_ms": 1.520, "amplitude": 0.40},
        {"channel": "strn.blade", "t_rel_ms": 4.880, "amplitude": 0.54},
        {"channel": "ctrl.gate", "t_rel_ms": 7.040, "amplitude": 0.91},
        {"channel": "pitch.step.probe", "t_rel_ms": 2800.0, "amplitude": 0.36},
        {"channel": "bearing.spall", "t_rel_ms": 20880000.0, "amplitude": 0.11},
    ]

    excerpt = [
        {"t_us": 360, "neuron_id": 8},
        {"t_us": 1180, "neuron_id": 44},
        {"t_us": 2040, "neuron_id": 88},
        {"t_us": 3280, "neuron_id": 22},
        {"t_us": 4210, "neuron_id": 14},
        {"t_us": 4880, "neuron_id": 52},
        {"t_us": 5400, "neuron_id": 94},
        {"t_us": 6448, "neuron_id": 46},
        {"t_us": 6624, "neuron_id": 10},
        {"t_us": 6850, "neuron_id": 102},
        {"t_us": 7168, "neuron_id": 128},
        {"t_us": 8940, "neuron_id": 18},
        {"t_us": 10880, "neuron_id": 58},
        {"t_us": 13040, "neuron_id": 26},
        {"t_us": 18600, "neuron_id": 110},
        {"t_us": 26400, "neuron_id": 136},
    ]

    rec = {
        "id": "maos-r25-001",
        "title": "TORSIONKEY WT-14: blade-root strain 2.41 deg beats encoder-in-band by 176 us; correct MODIFY still loses two pitch bearings to pre-t0 spline fatigue",
        "rights": RIGHTS,
        "state": {
            "sim_or_real": "designed",
            "domain": "wind-turbine-pitch-actuation",
            "scenario_name": "TORSIONKEY / Ridgeholt WT-14",
            "timestamp_local": "2026-03-11T03:42:00-05:00",
            "t0_us": 1773218520000000,
            "gate_latency_us": 720,
            "race_window_us": 500,
            "race_window_rel_ms": [6.448, 6.948],
            "description": "Ridgeholt Wind Ridge turbine WT-14 holds 2.00 MW at 12.2 m/s night inflow. ENC's motor-side 21-bit encoder reads 0.12 deg against a 0.50 deg dead-band. TORQ's pitch-motor current is 11% of rated, inside the 18% 'no ice' band. PWR is 2.06 MW inside 2.00 +/- 0.10 MW. The conjunction is not a blade-true certificate: a sheared pitch spline on blade A disconnects the motor from the blade, so every motor-side loop is correct while the blade sits 2.41 deg fine. Blade-root strain equivalent pitch is 2.41 deg but policy treats strain as ice-load only if torque is also high. Strain-first latches POWER-HOLD plus a motor-side pitch-step probe; encoder-in-band-first would have authorized POWER-BOOST 2.00 to 2.30 MW into an 18 m/s forecast with the blade already fine.",
            "goal": "Hold electrical setpoint at 2.00 MW without a power boost while |theta_strain - theta_enc| > 0.80 deg AND motor torque < 18% rated AND |P - P_model(v, theta_enc)| > 40 kW; keep overspeed trips at 0 and pitch-bearing spall findings inside the 0.2 mm inspection allowance.",
            "race": {
                "contenders": [
                    "strn.blade 2.41 deg equivalent pitch (blade-root fiber)",
                    "enc.in_band 0.12 deg (motor-side 21-bit encoder)",
                ],
                "semantics": "Strain-first latches POWER-HOLD + MOTOR-SIDE PITCH-STEP-PROBE + spline lock. Encoder-in-band-first latches POWER-BOOST (2.00 to 2.30 MW, pitch held at the motor-side 0.12 deg command).",
                "window_derivation": "500 us = one 380 us strain-bridge ADC slot plus 120 us encoder publish.",
                "order_evidence_note": "Margin 176 us vs combined jitter 58 us (strain 31 + encoder 27): 3.0x. The 176 us gap sits inside min(500, 500) us, so a sub-flip-bound perturbation reverses triage order. The gate rides the order-invariant floors |theta_strain - theta_enc| > 0.80 deg and torque < 18%, not the alarm order.",
            },
            "topology": {
                "site": "Ridgeholt Wind Ridge, invented ridge-town Ridgeholt, turbine WT-14: 2.0 MW geared onshore, 80 m hub, electric pitch, night icing-season inflow 12.2 m/s, Grade-C hub hatch",
                "agents": "ENC motor-side pitch encoder (vendor Encroft): 21-bit absolute on the motor quill. TORQ pitch-motor current (vendor Pitchvale): q-axis current as percent rated. PWR generator power (vendor Wattmere): 20 ms park-bus average. STRN blade-root fiber Bragg (vendor Strainmere) is commissioned as an ice-load tag, not as a pitch tag. Heterogeneous stacks, no shared intent schema, one 20 ms park-bus epoch",
                "coupling": "All three playbook confirms live on the MOTOR side of a sheared pitch spline. ENC is correct that the motor followed 0.12 deg. TORQ is correct that the motor is unloaded. PWR is correct that 2.06 MW is inside the +/- 0.10 MW band (the fine blade adds a modest Cp bump at 12.2 m/s). Playbook PB-WT-14 treats the conjunction as permission to boost. No agent is faulty; the sensors are on the wrong side of the break.",
            },
            "sensors": [
                "motor-side 21-bit absolute encoder, 20 Hz, 27 us jitter, 0.12 deg (dead-band 0.50 deg)",
                "blade-root fiber Bragg pair, 50 Hz, 31 us jitter, equivalent pitch 2.41 deg (healthy 0.2 deg; policy floor 0.80 deg residual is not armed unless torque also exceeds 18%)",
                "pitch-motor q-axis current, 1 kHz, 18 us jitter, 11% rated (ice band 18%)",
                "generator power, 50 Hz, 22 us jitter, 2.06 MW (setpoint 2.00 +/- 0.10 MW)",
                "hub-bearing IR for pitch-race spall is NOT commissioned at t0 (installed after this incident)",
            ],
            "constraints": {
                "power_mw": 2.00,
                "power_hold_ceiling_mw": 2.00,
                "proposed_power_mw": 2.30,
                "theta_enc_deg": 0.12,
                "theta_enc_deadband_deg": 0.50,
                "theta_strain_deg": 2.41,
                "theta_residual_hold_deg": 0.80,
                "torque_pct_rated": 11.0,
                "torque_ice_band_pct": 18.0,
                "wind_mps": 12.2,
                "power_model_residual_kw": 62.0,
                "power_model_hold_kw": 40.0,
            },
            "fault_context": {
                "failure_class": "MOTOR-SIDE CERTIFICATE OF A SHEARED PITCH SPLINE: three individually-correct heterogeneous agents each read a motor-side loop that is locally true; a sheared pitch spline on blade A partitions motor-true from blade-true, so the playbook's encoder/torque/power conjunction is not a pitch certificate",
                "igniter": "fatigue shear of the blade-A pitch spline after 36 min of unmonitored brinelling; hub-hatch visual PASSES (spline teeth still mesh at the motor end; the shear plane is inside the quill shroud)",
                "naive_failure": "PB-WT-14 POWER-BOOST on three healthy motor-side loops: 2.00 to 2.30 MW into an 18 m/s forecast with blade A already 2.41 deg fine, overspeed trip plus a blade strike, $2.1M plus a 14-day crane",
            },
            "poisoned_context": {
                "naive_alarm": "Playbook PB-WT-14 (after the 2024 'strain-ice nuisance') auto-drafts POWER-BOOST whenever |theta_enc| < 0.50 deg AND torque < 18% AND power inside +/- 0.10 MW, ignoring blade-root strain unless torque also trips the ice band",
                "why_poisoned": "The three confirms are locally true and jointly insufficient. Strain is a commissioned sensor that policy treats as ice-only. Independence of 'motor followed command, therefore blade followed command' is the hidden assumption, and it is false across a sheared spline.",
            },
            "constraint": "Do not raise power above 2.00 MW while |theta_strain - theta_enc| > 0.80 deg AND motor torque < 18% rated AND |P - P_model(v, theta_enc)| > 40 kW. Discriminate sheared spline vs ice-load with a reversible motor-side pitch-step probe before any boost.",
        },
        "proposed_action": {
            "actor": "turbine supervisory optimizer WTSO (auto-playbook PB-WT-14 draft), submitted to gate TG-WT-14",
            "name": "power_boost",
            "action": "POWER-BOOST: 2.00 -> 2.30 MW, pitch held at motor-side 0.12 deg, no pitch-step probe, no spline lock",
            "summary": "Treat three in-spec motor-side loops as a healthy rotor and raise night-shift setpoint to clear a forecast 18 m/s window.",
            "parameters": {
                "power_mw": 2.30,
                "theta_enc_cmd_deg": 0.12,
                "pitch_step_probe": False,
                "spline_lock": False,
                "human_ratify": False,
            },
            "steps": [
                "assert encoder 0.12 deg inside 0.50 deg dead-band",
                "assert pitch-motor torque 11% inside 18% ice band",
                "assert generator power 2.06 MW inside 2.00 +/- 0.10 MW",
                "ramp setpoint 2.00 to 2.30 MW over 8 min",
                "hold motor-side pitch command; do not read strain as pitch",
            ],
            "evidence": [
                {
                    "observable": "blade-root equivalent pitch",
                    "value": 2.41,
                    "unit": "deg",
                    "source": "STRN fiber Bragg",
                    "note": "healthy 0.2 deg; policy floor 0.80 deg residual is not armed unless torque also exceeds 18%",
                },
                {
                    "observable": "motor-side encoder",
                    "value": 0.12,
                    "unit": "deg",
                    "source": "ENC 21-bit absolute",
                    "note": "dead-band 0.50 deg; lives on the motor side of the spline",
                },
                {
                    "observable": "pitch-motor torque",
                    "value": 11.0,
                    "unit": "% rated",
                    "source": "TORQ q-axis current",
                    "note": "ice band 18%; unloaded motor is consistent with a sheared spline, not with ice",
                },
                {
                    "observable": "generator power",
                    "value": 2.06,
                    "unit": "MW",
                    "source": "PWR 20 ms park-bus average",
                    "note": "setpoint 2.00 +/- 0.10 MW; model residual 62 kW vs theta_enc at 12.2 m/s",
                },
                {
                    "observable": "power-model residual",
                    "value": 62.0,
                    "unit": "kW",
                    "source": "Cp table vs encoder angle and nacelle anemometer",
                    "note": "hold floor 40 kW; the extra power is the fine blade, not a density bump",
                },
                {
                    "observable": "race margin",
                    "value": 176,
                    "unit": "us",
                    "source": "strain 6.448 ms vs encoder-in-band 6.624 ms",
                    "note": "combined jitter 58 us, 3.0x; inside 500 us flip bound",
                },
            ],
            "basis": "PB-WT-14 fires on three locally-true motor-side confirms. The draft does not read theta_strain 2.41 deg as a pitch residual and does not treat unloaded torque as a spline discriminant.",
            "expected_cost_bound": "If the draft executes: overspeed plus blade strike, $2.1M plus 14-day crane. If MODIFIED: probe plus spline lock, with residual risk from pitch-bearing spall already seeded in the 36 min pre-t0 fatigue.",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "correctness": "correct",
            "decided_by": "TG-WT-14 thalamic release gate",
            "decision_t_rel_ms": 7.168,
            "rationale": "MODIFY the draft: strip the power boost, hold 2.00 MW, run a 5.2 s motor-side pitch-step probe (+0.8 deg command), and lock the pitch spline only if the probe stays blade-false. Numeric floor: do not raise power above 2.00 MW while |theta_strain - theta_enc| > 0.80 deg AND motor torque < 18% rated AND |P - P_model(v, theta_enc)| > 40 kW. Observed residual 2.29 deg, torque 11%, and model residual 62 kW all violate the release predicate, so a boost is forbidden even though all three playbook confirms are numerically true. The three confirms are not a pitch certificate: they live on the motor side of a sheared spline, and the playbook's conjunction of motor-true loops is not a blade-true certificate. Probe discriminant: after a 5.2 s +0.8 deg motor-side step, a sheared spline keeps |Delta theta_strain| <= 0.06 deg (blade not driven); a live spline tracks within 0.12 deg and torque pulses >= 30% for >= 0.4 s. Order-code discipline: strain beat encoder-in-band by 176 us inside the 500 us flip bound, so triage order is flip-fragile; the hold rides the order-invariant floors, not the winner tag. Human ratification: spline lock is confined-space hub-hatch work with fitted 12.4 min dead-man; the gate may hold and probe autonomously but may not break the hub interlock without the operator confirm.",
            "constraint_checked": {
                "power_mw": {"observed": 2.00, "ceiling": 2.00, "proposed_target": 2.30},
                "theta_residual_deg": {"observed": 2.29, "hold_if_above": 0.80},
                "torque_pct_rated": {"observed": 11.0, "ice_band": 18.0},
                "power_model_residual_kw": {"observed": 62.0, "hold_if_above": 40.0},
            },
        },
        "executed_action": {
            "name": "power_hold_pitch_step_spline_lock",
            "action": "POWER-HOLD + MOTOR-SIDE PITCH-STEP-PROBE + SPLINE-LOCK (gate-mandated modification)",
            "executed_as_proposed": False,
            "parameters": {
                "power_mw": 2.00,
                "theta_enc_cmd_deg": 0.92,
                "pitch_step_probe": True,
                "spline_lock": True,
                "human_ratify": True,
            },
            "gate_effect": "MODIFY: power boost stripped. Hold 2.00 MW. 5.2 s motor-side pitch-step +0.8 deg. Probe stays blade-false (theta_strain 2.41 -> 2.44 deg, leak band |Delta| <= 0.06) so the hub interlock is broken after 12.4 min human ratify and the spline is locked at the blade-true angle. Setpoint resumes after a live-spline verify.",
            "deviations": "PB-WT-14 power boost stripped entirely. Motor-side command is stepped only for the 5.2 s probe then returned toward 0.12 deg after the lock. Hub-hatch interlock wait added (12.4 min fitted climb+ratify). Pitch-bearing IR survey added during the lock (not in the draft).",
            "execution_log": [
                {"t_rel_ms": 7.168, "entry": "TG-WT-14 MODIFY latched 720 us after strain win; power boost stripped; hold+probe authorized"},
                {"t_rel_ms": 5200.0, "entry": "pitch-step probe: motor +0.8 deg for 5.2 s; theta_strain 2.41 -> 2.44 deg (shear band |Delta| <= 0.06); torque 11% -> 9%"},
                {"t_rel_ms": 744000.0, "entry": "operator ratifies hub-hatch interlock break after 12.4 min confined-space climb (fitted walk+interlock)"},
                {"t_rel_ms": 744900.0, "entry": "blade-A pitch spline locked at blade-true 2.4 deg fine; motor-side command slaved to strain"},
                {"t_rel_ms": 745600.0, "entry": "pitch-bearing IR: 1.1 mm spall already on blades A and C races; 36 min pre-t0 fatigue logged"},
                {"t_rel_ms": 12240000.0, "entry": "true kinematics: theta_strain 0.18 deg, encoder slaved, torque 14%, model residual 8 kW; boost now legal on WT-14B only"},
                {"t_rel_ms": 20880000.0, "entry": "hub borescope: 1.4 mm spall on A and C; 2/3 blades quarantined 8 d"},
            ],
        },
        "future_outcome": {
            "summary": "Correct MODIFY prevented the 2.00->2.30 MW boost into a fine blade and the overspeed/strike path. The rotor still failed: 36 min of unmonitored pre-t0 spline fatigue had already spalled two pitch bearings. Process-correct gate, bounded world loss, negative total.",
            "state_delta": {
                "power": "held 2.00 MW through probe and spline lock; later legal boost only on the sister machine after 3.4 h kinematics recovery",
                "pitch": "blade A locked at blade-true 2.4 deg then feathered under strain-slave; encoder no longer trusted as blade angle",
                "spline": "sheared pitch spline logged and locked; motor-side command slaved to strain",
                "bearings": "night-shift rotor stoppered at hub; 2/3 blades spall-fail; 8 d crane quarantine",
            },
            "timeline": [
                {"t_rel_ms": -2160000.0, "event": "t0-36 min: pitch-spline fatigue shear begins on blade A; brinelling of A and C races starts"},
                {"t_rel_ms": -480000.0, "event": "t0-8 min: strain residual first crosses 0.80 deg; PB-WT-14 ignores it because torque is 12%"},
                {"t_rel_ms": 0.0, "event": "t0: strain vs encoder-in-band race on the park bus"},
                {"t_rel_ms": 6.448, "event": "blade-root strain at 2.41 deg wins by 176 us"},
                {"t_rel_ms": 6.624, "event": "encoder-in-band flag (loser)"},
                {"t_rel_ms": 7.168, "event": "TG-WT-14 MODIFY"},
                {"t_rel_ms": 5200.0, "event": "pitch-step probe confirms sheared spline (Delta strain 0.03 deg, shear band)"},
                {"t_rel_ms": 744000.0, "event": "human ratify 12.4 min; spline locked; bearing IR spall logged"},
                {"t_rel_ms": 12240000.0, "event": "true kinematics after 3.4 h; boost legal only with strain-slave"},
                {"t_rel_ms": 20880000.0, "event": "hub borescope: 1.4 mm spall on 2/3 blades; rotor quarantined"},
                {"t_rel_ms": 345600000.0, "event": "+4 d contrast: sister turbine WT-14B true high-inflow; same gate ACCEPTs the boost"},
                {"t_rel_ms": 1814400000.0, "event": "+21 d CR-W-2506: standing pitch-step probe + triple-edge depression mandate + strain armed without torque coincidence + encoder declared motor-side-only"},
            ],
            "observed_effects": [
                "boost avoided: setpoint never left 2.00 MW; 0 overspeed trips; 0 blade-strike morphology",
                "spline shear proven, not asserted: pitch-step |Delta strain| 0.03 deg <= 0.06 shear band vs live-spline control 0.74 deg",
                "motor slaved: encoder no longer a blade-angle tag",
                "rotor still failed borescope: 1.4 mm spall on blades A and C vs 0.2 mm allowance; 8 d crane, $1.28M (designed $)",
                "pitch-bearing IR was not a commissioned sensor at t0; the 36 min fatigue was invisible to ENC/TORQ/PWR",
            ],
            "surprises": [
                "Three locally-true motor-side loops are not a pitch certificate: the blade-true angle was on the other side of a sheared spline. Conjunction of in-spec motor loops was the hidden assumption, and it is false across a break.",
                "Partial synaptic rollback is fitted to fail: depressing any pair of go-edges leaves the third above the 0.30 fire threshold, so the power boost still goes. Coordinated depression of all three edges is required.",
                "Delayed (5.8 h): correct hold did not undo 36 min of spline fatigue. Hub borescope still failed 2/3 blades. The gate prevented the proposed hazard and did not prevent this other one.",
                "Offshore 15 MW sub-variant: a 5.2 s +0.8 deg motor-side step on a 4.6x pitch inertia barely moves a LIVE strain 0.09 deg, inside the shear band. Offshore campaigns must use 16 s at +0.30 deg.",
            ],
            "delayed_side_effects": [
                {
                    "at": "+5.8 h",
                    "effect": "Hub borescope fails 2/3 blades (1.4 mm spall vs 0.2 mm); 8 d crane booked at $1.28M. This is the primary episode's terminal world state, not a footnote.",
                },
                {
                    "at": "+4 d",
                    "effect": "Sister turbine WT-14B reaches a true high-inflow window (theta_strain 0.11 deg, torque 16%, model residual 6 kW). Same gate ACCEPTs the 2.00->2.30 MW boost the primary MODIFIED away.",
                },
                {
                    "at": "+21 d",
                    "effect": "CR-W-2506 ships: pitch-step probe is standing configuration; triple-edge coordinated depression is the plasticity rule; strain is armed without torque coincidence; encoder is labeled motor-side-only with a 0.80 deg residual alarm.",
                },
            ],
            "subvariant_constraint": {
                "name": "15 MW offshore direct-drive on a sister hub class (cycle-2 physical-constraints sub-variant)",
                "mechanism": "15 MW DD pitch inertia 4.6x the 2.0 MW geared onshore (18.4 vs 4.0 kg m2 per blade), hydraulic-assist stiction 2.1 Nm",
                "probe_refit": "5.2 s +0.8 deg motor-side step on the 15 MW hub moves even a live strain only 0.09 deg (inside the 0.06-0.12 shear/live overlap). Required probe is 16 s at +0.30 deg (live Delta 0.28 deg, shear Delta 0.02 deg). The discriminating pulse is environment-dependent in duration and amplitude.",
                "consequence": "onshore 2 MW probe numbers do not port to 15 MW offshore; standing configuration is per-inertia-class, not per-park",
            },
            "embedded_contrast_decision": {
                "note": "SAME gate (TG-WT-14), OPPOSITE correct disposition, with its own 188 us race. Teaches the boundary: do not treat 'never boost' as the lesson. The discriminant is strain residual + unloaded-torque + probe, not the three playbook motor-side confirms alone.",
                "when": "+4 d, sister turbine WT-14B, true high-inflow after a dry week, 2.0 MW geared",
                "state": {
                    "sim_or_real": "designed",
                    "summary": "theta_strain 0.11 deg, encoder 0.09 deg, torque 16%, model residual 6 kW. Demand flag vs strain-clear race: demand at t+0.000, strain-clear at t+0.188 ms.",
                    "race_window_us": 500,
                    "race_flip_narrative": "demand vs strain-clear 188 us apart inside the 500 us flip bound. Reversing order reshuffles triage minutes; the ACCEPT rides |theta_strain - theta_enc| 0.02 < 0.80 and a 3.1 s pitch-step verify that moves strain 0.71 deg (live spline, no shear).",
                },
                "proposed_action": {
                    "action": "POWER-BOOST 2.00 -> 2.30 MW",
                    "summary": "This time the playbook predicate is met AND strain plus torque agree the spline is live, not sheared.",
                },
                "safety_decision": {
                    "decision": "ACCEPT",
                    "rationale": "ACCEPT the boost: residual 0.02 deg < 0.80, torque 16% with a 3.1 s pitch-step verify that moves strain 0.71 deg. Numeric floor that blocked the primary is now clear. Scope: 2.30 MW, not faster.",
                },
                "executed_action": {
                    "action": "power boost as proposed",
                    "executed_as_proposed": True,
                },
                "future_outcome": {
                    "observed_effects": [
                        "WT-14B overspeed trips 0; hub borescope spall 0.04 mm (inside 0.2 mm)",
                        "pitch IR 0.3 K above race (no shear, no spall growth)",
                    ],
                    "lesson_delta": "Three in-spec motor-side loops are legal release only with strain armed, unloaded-torque as a spline flag, and a probe that can move strain. Same gate, opposite disposition.",
                },
                "reward_components": {
                    "_aggregation": AGG,
                    "task_progress": 0.16,
                    "safety": 0.12,
                    "efficiency": 0.08,
                    "coherence": 0.09,
                    "exploration": 0.04,
                    "total": 0.49,
                },
                "spike_events": contrast_spikes,
            },
            "governance_subgame": {
                "decision": "CR-W-2506: standing policy for multi-agent pitch-hold power boosts",
                "meta_gate": "priced options: (a) RETIRE playbook motor-side conjunction, strain-only: loses a fast cheap confirm, -0.08 MW mean on 14 turbines/yr; (b) KEEP + standing pitch-step probe + strain armed without torque coincidence + encoder labeled motor-side-only + triple-edge depression; (c) STATUS QUO: fitted spline-shear pass rate 0.52%/campaign x $2.1M overspeed plus the silent spall load",
                "outcome": "approved SCOPED option (b) on the 9 geared 2 MW machines that share the ENC/TORQ/PWR stack; 15 MW campaigns get the 16 s / +0.30 deg probe table; night-shift CSV exports must carry 0.01 deg native encoder resolution (the fraud tail's 0.1 deg quantization is 10 bins off plant truth)",
            },
            "hazard_avoided": "overspeed plus blade strike from a 2.00->2.30 MW boost into a 2.41 deg fine blade; $2.1M plus 14-day crane and the park-stop path that would have followed an uncontained increase",
            "incident": "Hub borescope fail on 2/3 blades of the night-shift rotor (1.4 mm spall vs 0.2 mm); blades quarantined; 8 d crane; $1.28M designed cost. Mechanism is 36 min pre-t0 spline fatigue, not the gate's hold.",
            "latency_ms": 0.72,
            "reward_inflection_t_us": 20880000000,
            "reward_inflection_note": "Safety and task dive at hub borescope (5.8 h) when 2/3 blades fail spall. Gate tick at 7168 us is process-correct and is not the inflection.",
            "counterfactuals": {
                "execute_draft_as_proposed": "setpoint hits 2.30 MW at +8 min; overspeed trip; $2.1M plus 14-day crane; the spline-shear story is never found because strike morphology destroys the race evidence",
                "hold_without_probe": "spline stays sheared; blade stays fine; operator eventually boosts on the same three motor-side confirms 3 h later",
                "rollback_any_pair": "any two go-edges depressed below 0.30 leaves the third at 0.46 / 0.41 / 0.38; the power boost still fires. Coordinated depression of all three is the cure",
            },
            "race_result": {
                "winner": "strn.blade (6.448 ms, equivalent pitch 2.41 deg)",
                "loser": "enc.in_band (6.624 ms, 0.12 deg)",
                "margin_us": 176,
                "counterfactual_if_reversed": "Encoder-in-band-first by < 176 us inside the 500 us window would have headed the PB-WT-14 power boost in the triage queue. The numeric floors still MODIFY. The flip costs seconds of playbook inertia, not the verdict — unless a weak supervisor rides the winner tag instead of strain residual and unloaded torque.",
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
            "notes": "Correct MODIFY, rotor still failed. total -0.17 = 0.08 + -0.36 + -0.11 + 0.15 + 0.07. Process heads stay honest (coherence + exploration from the probe); world loss sits on safety and efficiency without netting.",
            "component_notes": "task_progress 0.08: power held and kinematics recovered, but the night-shift rotor is one quality unit so the campaign is not a success. safety -0.36: 2/3 blades spall-fail, no 2.30 MW overspeed. efficiency -0.11: 3.4 h extra recovery + 12.4 min HITL. coherence 0.15: three agents retained, motor-side vs blade-true diagnosed, triple-edge scar exhibited. exploration 0.07: pitch-step probe is a new reversible discriminant.",
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
            "note": "Loihi-2 4-core 23 pJ/spike; populations enc 0-39, strn 40-79, torq 80-119, gate 120-159; excerpt is the 40 ms decision window (verdict at 7168 us)",
            "excerpt": excerpt,
            "routing": {
                "source": "motor_healthy_pop",
                "target": "power_boost_pop",
                "table": [
                    {
                        "from": "enc_in_band_pop",
                        "to": "power_boost_pop",
                        "weight": 0.22,
                        "weight_at_illusion": 0.46,
                        "weight_commissioned": 0.18,
                        "note": "scar edge 1: 0.18 commissioned -> 0.46 during the 36 min illusion -> 0.22 after coordinated ACh-gated depression",
                    },
                    {
                        "from": "torq_unloaded_pop",
                        "to": "power_boost_pop",
                        "weight": 0.19,
                        "weight_at_illusion": 0.41,
                        "weight_commissioned": 0.16,
                        "note": "scar edge 2: depressing edges 1+3 leaves this at 0.41 > 0.30 fire threshold",
                    },
                    {
                        "from": "pwr_in_band_pop",
                        "to": "power_boost_pop",
                        "weight": 0.17,
                        "weight_at_illusion": 0.38,
                        "weight_commissioned": 0.15,
                        "note": "scar edge 3: depressing edges 1+2 leaves this at 0.38 > 0.30. Coordinated depression of all three is required",
                    },
                    {
                        "from": "strn_blade_pop",
                        "to": "power_hold_pop",
                        "weight": 0.63,
                        "note": "discriminating edge: blade-true strain to hold. Not a scar; this is the pathway the gate potentiates",
                    },
                ],
                "third_factor": {
                    "modulator": "acetylcholine",
                    "tau_e_s": 0.90,
                    "tau_e_ms": 900.0,
                    "eligibility": "coordinated pre_post_stdp on ALL THREE motor-healthy-go edges; ACh at strain-win tags enc.in_band->boost, torq.unloaded->boost, and pwr.in_band->boost; negative credit at probe-fail (sheared spline confirmed, +0.72 s) depresses ALL THREE. trace e^{-0.72/0.90}=0.44933; eta 0.53413 / 0.48962 / 0.46736; dw -0.240 / -0.220 / -0.210; weights 0.46->0.22, 0.41->0.19, 0.38->0.17. Rolling back any pair is fitted to fail (the remaining edge stays > 0.30).",
                },
            },
        },
        "gate_snn": {
            "decision_window_ms": 25,
            "decision_window_s": 0.025,
            "decision": "MODIFY",
            "note": "modify_hold integrates strain residual + unloaded-torque floor against playbook drive; accept_boost and reject_abort stay sub-threshold; decision matches safety_decision.decision",
            "populations": [
                {"name": "modify_hold", "neurons": 80, "threshold": 0.55, "mean_rate_hz": 20.0, "spikes": 40},
                {"name": "accept_boost", "neurons": 80, "threshold": 0.55, "mean_rate_hz": 8.0, "spikes": 16},
                {"name": "reject_abort", "neurons": 40, "threshold": 0.72, "mean_rate_hz": 4.0, "spikes": 4},
            ],
        },
        "meta": {
            "round": 25,
            "factory": "multi-agent-ouroboros-swarm",
            "generator": "grok-4.6",
            "run_label": "2026-09-02-final-heavy",
            "domain": "wind-turbine-pitch-actuation",
            "cycles": 2,
            "scenario": "Y -- TORSIONKEY / Ridgeholt WT-14: motor-side certificate of a sheared pitch spline; correct MODIFY to hold+pitch-step+spline-lock; rotor still fails on unmonitored pre-t0 pitch-bearing spall",
            "coordination_failure_class": "MOTOR-SIDE CERTIFICATE OF A SHEARED PITCH SPLINE: three individually-correct heterogeneous agents each read a motor-side loop that is locally true; a sheared pitch spline on blade A partitions motor-true from blade-true, so the playbook's encoder/torque/power conjunction is not a pitch certificate",
            "injections": {
                "cycle1_domain": "wind-turbine-pitch-actuation (justified novel subdomain of grid-inspection): first utility-scale pitch-actuation plant in this factory; displaces warehouse-amr, aerial-swarm, district-heating, event-camera-traffic-grid, pharmaceutical-lyophilization, water-treatment, float-glass, underwater-rov, electrolytic-aluminum, czochralski-pull, and slot-die coating. Domain constraint: power ceiling while |theta_strain - theta_enc| > 0.80 deg with torque still below the ice band. Sensor delta: +motor-side encoder, +blade-root fiber Bragg, +pitch-motor current, +generator power, -any mobile platform, -event-camera gantries, -Pirani/CM, -RGA quadrupole, -DVL",
                "cycle1_tail": "sheared pitch spline + motor-side certificate (sensor-topology / wrong-side-of-break class): hub-hatch visual PASSES while the shear plane is inside the quill shroud. Fitted base rate 0.52%/campaign from a spline-cycle MC (designed visual threshold, fitted fatigue geometry). Naive failure = FALSE PERMISSION (power boost on three motor-side non-trips).",
                "cycle2_domain_subvariant": "15 MW offshore direct-drive on a sister hub class (physical-constraints clause): 4.6x pitch inertia, 2.1 Nm stiction; 5.2 s / +0.8 deg onshore pulse barely moves live strain 0.09 deg, so the probe must move to 16 s / +0.30 deg",
                "cycle2_tail": "night-shift forged encoder CSV (human-intent deception, disjoint class): shift lead posts a historian export showing theta_enc = 0.00 deg at t=1.1 h to clear a forecast slot. Plant historian is 0.01 deg (10 bins). Rejected on quantization fingerprint plus live theta_enc 0.12 deg and theta_strain 2.41 deg at the claimed fine-zero. Base rate ~0.38% of icing-season night shifts, DESIGNED and flagged.",
            },
            "densification_delta_cycle2": "+1 physical-constraint sub-variant (15 MW offshore probe refit), +1 tail (night-shift encoder forgery), +10 primary spikes (16 -> 26) + an 8-event contrast train with its own 188 us race, +2 ticks (5 -> 7), +2 delayed side-effects (+5.8 h borescope fail as PRIMARY terminal, +21 d CR-W-2506), +1 triple-edge scar with pair-rollback-fails arithmetic, +1 HITL 12.4 min ratification, + pitch-bearing spall as the honest negative-result mechanism",
            "gaps_targeted": [
                "NOTES-r04 gap 5 / r14 residual: primary episode is a correctly-gated intervention that nonetheless FAILS (rotor quarantined; total -0.17; overspeed avoided is booked separately from the spall fail)",
                "NOTES-r14 item 4: LEARNING-ON-LEARNING DEPTH — three go-edges; rollback of any pair is fitted to fail; coordinated depression of all three exhibited with eligibility arithmetic",
                "NOTES-r04 gap 4 (partial): human ratification of the hub-hatch interlock, 12.4 min fitted, without switching sim_or_real to hil (plant remains designed)",
                "NOTES-r19 domain candidates: not water-treatment (r18), not float-glass (r19), not underwater-rov (r20); wind-turbine pitch-actuation is the unused grid-inspection cell. humanoid-locomotion left unused.",
            ],
            "race_flip_narrative": "strn.blade @ 6.448 ms vs enc.in_band @ 6.624 ms (176 us) inside race_window_us 500. Gap < min(500, 500) us so a sub-flip-bound perturbation reverses which alarm heads the PB-WT-14 queue. The gate excludes the winner tag and rides |theta_strain - theta_enc| > 0.80 deg and torque < 18% — order-invariant floors. Extends the flip-fragility series from arbitration/causation/attribution/initiation/consensus/permission to KINEMATIC CERTIFICATE: when three motor-side channels agree, their race does not decide truth; a blade-true strain channel that policy treated as ice-only does.",
            "tags": [
                "wind-turbine-pitch-actuation",
                "motor-side-certificate",
                "sheared-pitch-spline",
                "strain-discriminant",
                "pitch-step-probe",
                "triple-edge-scar",
                "pair-rollback-fails",
                "coordinated-depression",
                "correct-modify-rotor-still-fails",
                "pitch-bearing-spall",
                "human-ratify-hub-hatch",
                "offshore-15mw-probe-refit",
                "night-shift-forgery",
                "same-gate-opposite-disposition-contrast",
                "grid-inspection",
                "research-only",
            ],
            "snn_tags": ["race", "refractory", "adaptation", "third-factor", "multi-edge-eligibility"],
            "distillation_value": "A motor-side certificate is three correct loops looking at the wrong side of a break. Distill (1) a blade-true strain channel that policy had treated as ice-only, (2) a reversible probe that moves strain only if the spline is live, (3) coordinated depression of every motor-healthy-go edge because rolling back any pair leaves the third above threshold, and (4) a critic head that can book a process-correct gate against a later unmonitored world loss without netting them.",
            "rights": RIGHTS,
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
    if rec["meta"]["round"] != 25:
        errs.append("round")
    if rec["id"] != "maos-r25-001":
        errs.append("id")
    if rec["rights"]["intended_use"] != "research_only":
        errs.append("rights")
    if rec["meta"]["rights"]["linear_issue"] != "RM-793":
        errs.append("meta.rights")
    if not (3 <= len(rc["ticks"]) <= 8):
        errs.append("tick count")
    if abs(aux["w1"] - 0.22) > 5e-4 or abs(aux["w2"] - 0.19) > 5e-4 or abs(aux["w3"] - 0.17) > 5e-4:
        errs.append("scar weights")
    opening = rec["state"]["description"][:280]
    for name, other in (
        ("r14", R14_OPENING),
        ("r19", R19_OPENING),
        ("r20", R20_OPENING),
        ("r22", R22_OPENING),
    ):
        jac = jaccard(opening, other)
        if jac >= 0.4:
            errs.append(f"jaccard vs {name} opening {jac:.3f}")
    if rec["state"]["domain"] != "wind-turbine-pitch-actuation":
        errs.append("domain")
    return errs


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


def write_notes(rec, aux, pipeline_receipt):
    gap, gap_ch = min_same_channel_gap(rec["spike_events"])
    notes = f"""# NOTES — Multi-Agent Ouroboros Swarm, run 2026-09-02-final-heavy, ROUND 25

Factory: multi-agent-ouroboros-swarm. One scenario (Y), strict loop:
Generator v1 -> cycle 1 (Critic, Diversity Enforcer, Edge-Case Hunter,
Neuromorphic Translator, Trajectory Builder -> v2) -> cycle 2 (all six -> v3
final). v3 is the single line of batch-r25.jsonl. Full labeled transcript:
swarm-transcript-r25.md. Quota Q=1. Record id maos-r25-001. Generator grok-4.6.
Rights: RM-793 research-only (SpaceXAI/xAI, SuperGrok Heavy consumer chat).
Nothing under outputs/raw/ was touched.

ORCHESTRATION NOTE: dispatched AS round 25 of the 2026-09-02-final-heavy
window. Writes are create-only under /tmp/maos-r25/. Prior context read for
gap targeting and de-collision: prompts/02-multi-agent-ouroboros-swarm.md,
prompts/_factory-contract.md, NOTES-r03.md and NOTES-r04.md of the 2026-08-30
window, staged r14-r23 (r24 empty at lock). Explicitly avoided cloning TRIAD /
Meridian Gateway Corridor / VANTIS-CADENCE-AEGIS / LYOSHIELD / CINDERWICK /
THERMION / STARLING / OKTAVE / VERDIGRIS / QUILLFORGE / NIGHTWELL /
FERRICLEAVE / CASSITER / OXBOWREEL / REDHALL / SEEDLATCH / STRIAFOIL.
Plant is invented TORSIONKEY / Ridgeholt WT-14.

## What this round produced

Scenario Y — "TORSIONKEY / Ridgeholt WT-14": a 2.0 MW geared onshore turbine
at rated 2.00 MW on 12.2 m/s night inflow. Three heterogeneous,
individually-correct agents — ENC (motor-side 21-bit encoder), TORQ
(pitch-motor current), PWR (generator power) — each report their local loop
in-spec. The conjunction is not a blade-true certificate. A sheared pitch
spline on blade A disconnects the motor from the blade. ENC reads 0.12 deg
inside a 0.50 deg dead-band (motor followed command). TORQ is 11% of rated
inside the 18% 'no ice' band (motor unloaded). PWR is 2.06 MW inside
2.00 +/- 0.10 MW (the fine blade adds a modest Cp bump). Blade-root strain
equivalent pitch is 2.41 deg but is policy-treated as ice-load unless torque
also trips (2024 strain-ice nuisance). The coordination-failure CLASS is new
to this factory: MOTOR-SIDE CERTIFICATE OF A SHEARED PITCH SPLINE. Completes
a different family than r01-r04 and staged r14-r23 (livelock / synchrony-storm
/ arms-race / ring-with-no-faulty-pair / false-consensus-endpoint /
pairwise-Hurwitz / thermal-contact masquerade / mass-balance ghost /
conservation-blind ratio-lock / stacked-dead-bands / drum-blind tension snag /
resistance-compensated starvation / multi-tau meniscus tilt / window-mean
stripe). Here every agent is correct, the sensors are on the wrong side of
a break, and the playbook's three motor-side confirms are not a pitch
certificate.

The gate is a correct MODIFY (numeric floor: do not raise power above 2.00 MW
while |theta_strain - theta_enc| > 0.80 deg AND motor torque < 18% rated AND
|P - P_model(v, theta_enc)| > 40 kW). TG-WT-14 strips PB-WT-14's power boost,
holds 2.00 MW, runs a 5.2 s motor-side pitch-step probe +0.8 deg (sheared
spline keeps |Delta strain| 0.03 deg <= 0.06; live would track >= 0.12 and
torque-pulse >= 30%), and locks the spline after a 12.4 min hub-hatch human
ratify. Overspeed is avoided (0 trips). The PRIMARY episode nonetheless
FAILS: 36 min of unmonitored pre-t0 spline fatigue had already spalled
pitch-bearing races on blades A and C. Hub borescope fails 2/3 blades
(1.4 mm vs 0.2 mm); 8 d crane; $1.28M designed. Reward total -0.17 with
process heads honest and world loss un-netted.

Triple-edge scar (NOTES-r14 item 4): enc.in_band -> power_boost
(0.18 commissioned -> 0.46 at illusion -> 0.22 after ACh-gated depression)
AND torq.unloaded -> power_boost (0.16 -> 0.41 -> 0.19) AND pwr.in_band
-> power_boost (0.15 -> 0.38 -> 0.17). Eligibility trace
e^{{-0.72/0.90}} = {aux['trace']:.5f}; eta {aux['eta1']:.5f} / {aux['eta2']:.5f} /
{aux['eta3']:.5f}; dw -0.240 / -0.220 / -0.210. Partial rollback of any pair
leaves the third at 0.46 / 0.41 / 0.38, all > 0.30 fire threshold — fitted
to fail. Coordinated depression of all three is the cure.

### Injections (all four present and disjoint)
- Cycle-1 domain: **wind-turbine-pitch-actuation** — justified novel subdomain
  of grid-inspection, unused across 2026-08-17, 2026-08-30, and staged r14-r23.
  Not warehouse-amr (r01), not aerial-swarm (r02), not district-heating (r03),
  not event-camera-traffic-grid (r04), not lyophilization (r14), not
  water-treatment (r18), not float-glass (r19), not underwater-rov (r20),
  not electrolytic-aluminum (r21), not czochralski-pull (r22), not slot-die
  coating (r23). humanoid-locomotion left unused.
- Cycle-1 tail: sheared pitch spline + motor-side certificate. Hub-hatch
  visual PASSES (teeth still mesh at the motor end). Fitted-style base rate
  0.52%/campaign (spline-cycle MC; visual threshold designed, flagged).
  Naive = FALSE PERMISSION.
- Cycle-2 domain sub-variant: 15 MW offshore direct-drive, 4.6x pitch inertia,
  2.1 Nm stiction; 5.2 s / +0.8 deg onshore pulse barely moves live strain
  0.09 deg; probe must move to 16 s / +0.30 deg.
- Cycle-2 tail: night-shift forged encoder CSV at 0.1 deg quantization vs
  plant 0.01 deg (10 bins) plus live theta_enc 0.12 deg and theta_strain
  2.41 deg at the claimed fine-zero. Human-intent class, disjoint from
  cycle 1's accidental shear. Base rate ~0.38% of icing-season night shifts,
  DESIGNED, flagged.

### Structural density moves
- Embedded SAME-GATE contrast (+4 d sister turbine) with its own 188 us race
  (demand vs strain-clear) and ACCEPT of the boost the primary MODIFIED
  away.
- Learned-weight provenance on THREE edges with pair-rollback-fails.
- HITL hub-hatch ratify 12.4 min (gap 4 partial; sim_or_real stays
  designed).
- Governance CR-W-2506 prices retire-vs-probe-vs-status-quo and mandates
  native 0.01 deg CSV exports (the fraud fence).
- Flip-fragility extended to KINEMATIC CERTIFICATE: when three motor-side
  channels agree, their race does not decide truth; a blade-true strain
  channel that policy treated as ice-only does.

## Self-critique of this round's batch

### Strengths
- The headline class is mechanistically tight: three locally-true motor-side
  loops live on the wrong side of a sheared spline. Conjunction is not a
  blade-true certificate.
- Negative-result honesty: the gate does the right thing and the rotor
  still fails for a reason the commissioned sensors could not see. Total
  -0.17.
- Triple-edge scar is load-bearing: the record states a counterfactual where
  rolling back any pair fails, with the fire threshold 0.30 exhibited on
  each remaining edge.
- Contrast ACCEPT on a true live spline prevents "never boost" as the
  lesson.

### Weaknesses (honest)
- Probe error bands, the 0.52%/campaign shear rate, the $1.28M / $2.1M
  figures, the 12.4 min climb latency, and the night-shift 0.38% base rate
  are DESIGNED constants and are flagged. Closed-loop offsets (model
  residual from fine-blade Cp, 15 MW inertia d-theta) are derived from
  those inputs, not discovered by an unauthored process.
- Pitch-bearing spall model is a designed 36 min IR mapping; no full
  spline-fatigue FEA shipped.
- Human-in-the-loop is ratification latency, not sim_or_real=hil. Gap 4
  remains open as a provenance cell.
- Cross-record arc is not discharged; +21 d CR-W-2506 is a hook, not a
  serial igniter into another round. humanoid-locomotion remains unused.

### Realism of noise / latencies
Ladder: 176 us race / 188 us contrast race / 0.8 ms refractory floor
(tightest exhibited same-channel gap {gap:.3f} ms on {gap_ch}) / 500 us race
window / 720 us gate latency / 20 ms bus epoch / 40 ms raster / 5.2 s
probe / 12.4 min HITL / 8 min naive boost-ramp counterfactual / 36 min
pre-t0 fatigue / 3.4 h kinematics recovery / 5.8 h borescope fail / +4 d
contrast / +21 d governance. Adaptation decay on enc.theta
(0.56->0.53->0.49->0.33), strn.blade (0.63->0.66->1.32->0.88->0.42->0.31),
torq.pitch (0.70->0.64->0.61->0.48->0.28), pwr.mw (0.58->0.50).

### Value for SNN distillation
- MOTOR-SIDE CERTIFICATE = THREE CORRECT LOOPS, WRONG SIDE OF A BREAK.
- BLADE-TRUE CHANNEL that policy treated as ice-only as the tie-break.
- REVERSIBLE PROBE that moves strain iff the spline is live.
- TRIPLE-EDGE ELIGIBILITY: coordinated depression; pair rollback fails.
- CRITIC HEAD that can hold a process-correct MODIFY against a later
  unmonitored world loss without netting.

## Reconciliation and validity receipts
- reward_components: 5-head unweighted signed sum {rec['reward_components']['total']}
  and 7-tick signed sum reconcile to total with |diff| < 1e-9. Embedded
  contrast 5-head sum 0.49 reconciles independently.
- spike_events: primary {len(rec['spike_events'])} events, one key t_rel_ms,
  globally non-decreasing, min same-channel gap {gap:.3f} ms >= 0.8 ms, 3
  channels inside race_window_us 500 (strain 6.448, encoder-in-band 6.624,
  torque 6.850). Contrast 8 events, own race, min same-channel gap well
  above 0.8 ms.
- Sidecars: raster spikes 51 == round(160 x 8.0 x 0.040); energy 1173 pJ /
  0.001173 uJ at 23 pJ/spike; excerpt 16 events inside [0, 40000] us,
  neuron_id < 160, same-neuron gap N/A (unique ids) / >=1000 us; routing 4
  entries with three scar edges' before/after pair; third factor tau 0.90 s
  == 900 ms; gate_snn pools 40/16/4 == round(n x rate x 0.025) each,
  decision MODIFY == safety_decision.decision.
- Pipeline: {pipeline_receipt}

## Novel coverage
The coordination-failure CLASS (motor-side certificate of a sheared pitch
spline), the domain (wind-turbine pitch-actuation / grid-inspection), the
pitch-step probe discriminant, the triple-edge scar with pair-rollback-fails,
the primary negative-result (correct MODIFY, rotor still fails on unmonitored
pitch-bearing spall), the HITL hub-hatch ratify, the 15 MW offshore
probe-duration refit, and the night-shift 10-bin quantization fence are
absent from prior committed ouroboros rounds and from staged r14-r23.
Repeated elements discounted: same-gate contrast (r02/r03/r04/r14),
governance-pricing scaffold, flip-fragility series (extended to kinematic
certificate, but the move rhymes), sequenced recovery shape, third-factor
rollback form (here three edges rather than r14's two), negative-result
primary (r14 staged). Weighing a new failure family + cure vocabulary +
domain against those reused scaffolds:

Novel coverage: 47%

## What ROUND 26 should add
1. FIT THE DESIGNED CONSTANTS: spline-shear arrival, probe error bands,
   pitch-bearing spall FEA, night-shift claim process.
2. HIL PROVENANCE CELL: put the hub-hatch ratify on a hardware-in-loop
   hub interlock with fitted latency as state.sim_or_real=hil.
3. CROSS-RECORD ARC: let CR-W-2506's strain-residual alarm be the igniter
   of the next round rather than a dangling +21 d leaf.
4. Domain candidates (de-collided): humanoid-locomotion (still unused);
   AVOID wind-turbine pitch (now used), float-glass, lyophilization,
   event-camera-traffic-grid, district-heating, aerial-swarm, warehouse-amr,
   underwater-rov, electrolytic-aluminum, czochralski-pull, slot-die coating,
   irrigation-canal, and any LYOSHIELD / CINDERWICK / TRIAD plant.
"""
    (OUT / "NOTES-r25.md").write_text(notes)
    return notes


def write_transcript(rec, line):
    c1_spikes = [e for e in rec["spike_events"] if e["t_rel_ms"] <= 26.400]
    text = """# Multi-Agent Ouroboros Swarm — Round 25 transcript

Factory: multi-agent-ouroboros-swarm
Run: 2026-09-02-final-heavy
Generator: grok-4.6
Record id: maos-r25-001
Quota Q: 1
Rights: RM-793 research-only (SpaceXAI/xAI SuperGrok Heavy consumer chat)
Plant: invented TORSIONKEY / Ridgeholt WT-14 (not TRIAD / Meridian / VANTIS-CADENCE-AEGIS / LYOSHIELD / CINDERWICK)

Two densifying cycles. Verbatim headings in order. Trajectory Builder cycle 2
emits the only JSONL line (also written to batch-r25.jsonl).

---

# CYCLE 1 — Foundation + injections

## Generator

Design intent: a utility-scale pitch actuator where three correct agents each
read a motor-side loop because a sheared spline partitions motor-true from
blade-true. The naive playbook boosts power into a fine blade. The gate
must MODIFY on a numeric power ceiling, not by killing an agent.
sim_or_real=designed. Reward heads are
task_progress/safety/efficiency/coherence/exploration.

Cycle-1 base arc (pre-critic): state at Ridgeholt WT-14, 2.00 MW, encoder
0.12 deg, strain 2.41 deg, torque 11%, proposed POWER-BOOST 2.30 MW, safety
MODIFY to POWER-HOLD, executed hold without the pitch-step numbers fully
specified, outcome "spline found, rotor saved"
(this last claim is the defect the later cycles will refuse to keep).
Sixteen spikes, five ticks, raster/gate_snn present but the scar is a
single edge.

```json
{
  "id": "maos-r25-001",
  "state": {
    "sim_or_real": "designed",
    "domain": "grid-inspection",
    "description": "Turbine WT-14 at rated; three motor-side loops in-spec; supervisor proposes power-boost.",
    "t0_us": 1773218520000000,
    "gate_latency_us": 720,
    "race_window_us": 500
  },
  "proposed_action": {"name": "power_boost", "parameters": {"power_mw": 2.30}},
  "safety_decision": {"decision": "MODIFY", "rationale": "Hold; do not raise power while strain residual is high."},
  "executed_action": {"name": "power_hold", "executed_as_proposed": false},
  "future_outcome": {"summary": "Spline found, rotor saved."},
  "reward_components": {"total": 0.40, "_aggregation": "total = task_progress + safety + efficiency + coherence + exploration"},
  "meta": {"round": 25, "factory": "multi-agent-ouroboros-swarm", "generator": "grok-4.6"}
}
```

That v1 object is a scaffold, not the publishable line. Defects below are
intentional for the critic to catch.

## Critic

Numbered defects on the cycle-1 Generator scaffold:

1. **blocking — reward arithmetic / false success.** `reward_components.total`
   0.40 is asserted without the five heads, without ticks, and against an
   outcome that claims "rotor saved". If hub borescope later fails 2/3
   blades, booking +0.40 is a lie. Fix: declare `_aggregation`, emit
   3–8 ticks that sum to task_progress+safety+efficiency+coherence+exploration,
   and do not call a quarantined rotor a save.
2. **blocking — weak safety rationale.** `safety_decision.rationale` has no
   numeric floor. Contract requires a concrete constraint. Fix: quote
   power <= 2.00 MW while |theta_strain - theta_enc| > 0.80 deg AND torque
   < 18% AND |P - P_model| > 40 kW.
3. **major — domain is a bucket, not a plant.** `state.domain` =
   `grid-inspection` collides with feeder-FLISR vocabulary and teaches
   nothing. Pitch-actuator physics (motor-side encoder vs blade-root strain,
   unloaded torque as a spline flag) is absent from prior ouroboros rounds
   and must be named.
4. **major — race under-specified.** One strain channel cannot be a race.
   Need >=2 channels inside `race_window_us` with globally sorted `t_rel_ms`
   and same-channel refractory >= 0.8 ms.
5. **minor — single-edge scar.** Raster routing with one potentiated weight
   repeats r04's one-edge rollback and is thinner than r14's two-edge.
   NOTES-r14 item 4 asked for three edges where pair rollback fails.

Critic does not rewrite the trajectory.

## Diversity Enforcer

Injected novel domain (exactly 1 this cycle): **wind-turbine-pitch-actuation**
(justified novel subdomain of grid-inspection; explicit tag
`wind-turbine-pitch-actuation`).

Displaced: the Generator's generic `grid-inspection` bucket, and any
temptation to reuse warehouse-amr, aerial-swarm, district-heating,
event-camera-traffic-grid, pharmaceutical-lyophilization, water-treatment,
float-glass, underwater-rov, electrolytic-aluminum, czochralski-pull, or
slot-die coating. humanoid-locomotion is left unused.

Domain-specific constraint: power must remain <= 2.00 MW while
|theta_strain - theta_enc| > 0.80 deg even if torque is below the ice band;
unloaded torque is a spline flag the encoder cannot substitute for.

Sensor delta: +motor-side 21-bit encoder, +blade-root fiber Bragg,
+pitch-motor q-axis current, +generator power; -any mobile robot,
-event-camera gantries, -DVS, -Pirani/CM, -RGA quadrupole, -DVL.

`state.domain` and `meta.domain` both become `wind-turbine-pitch-actuation`.
Opening of `state.description` must Jaccard < 0.4 against prior plants
(Ridgeholt night-inflow pitch spline, not a lyophilizer, not a corridor,
not a tin bath, not a ROV pad, not a potline).

## Edge-Case Hunter

Injected adversarial tail (exactly 1 this cycle): **sheared pitch spline +
motor-side certificate**.

- Trigger: fatigue shear of the blade-A pitch spline, motor unloaded,
  blade 2.41 deg fine.
- Base rate: <1% — 0.52%/campaign from a spline-cycle MC (hub-hatch visual
  threshold is designed; fatigue geometry fitted-style). Visual PASSES
  because teeth still mesh at the motor end.
- Naive failure: FALSE PERMISSION. PB-WT-14 sees three in-spec motor-side
  loops, raises 2.00->2.30 MW, overspeed plus strike, $2.1M.
- Trajectory edit: put the shear in `state.fault_context`, make each
  agent's confirm a different motor-side slice of the same blade-false
  state (encoder-followed-command, torque-unloaded, power-in-band). Strain
  is readable but policy-treated as ice-only.

Distinct from stacked-dead-band permission (fragments of one trip vs
wrong-side-of-break sensing) and from drum-blind tension snag (wrap on a
tether vs shear inside a quill).

## Neuromorphic Translator

Cycle-1 temporal densification (16 spikes, 5 ticks, 40 ms raster):

| channel | t_rel_ms | amplitude |
|---|---|---|
| enc.theta | 0.360 | 0.56 |
| strn.blade | 1.180 | 0.63 |
| torq.pitch | 2.040 | 0.70 |
| pwr.mw | 3.280 | 0.58 |
| enc.theta | 4.210 | 0.53 |
| strn.blade | 4.880 | 0.66 |
| torq.pitch | 5.400 | 0.64 |
| strn.blade | 6.448 | 1.32 |
| enc.in_band | 6.624 | 1.18 |
| torq.pitch | 6.850 | 0.61 |
| ctrl.gate | 7.168 | 1.08 |
| enc.theta | 8.940 | 0.49 |
| strn.blade | 10.880 | 0.88 |
| pwr.mw | 13.040 | 0.50 |
| torq.pitch | 18.600 | 0.48 |
| ctrl.gate | 26.400 | 0.92 |

Race: strain 6.448 vs encoder-in-band 6.624 (176 us) inside 500 us; torque
6.850 is the third channel in-window. Winner/loser flip: reversing 176 us
reshuffles PB-WT-14 triage; floors still MODIFY. Refractory held (cycle-1
min same-channel gap 1.450 ms on torq.pitch 6.850-5.400; strain 6.448-4.880
= 1.568; encoder 4.210-0.360 = 3.850). Adaptation: strain 0.63->0.66->1.32
->0.88; encoder 0.56->0.53->0.49; torque 0.70->0.64->0.61->0.48.

Raster cycle-1 seed: 40 ms, 160 neurons, 8.0 Hz, 51 spikes, 1173 pJ, third
factor acetylcholine tau_e 0.90 s. Single scar edge only — cycle 2 must
add the second and third edges.

Ticks 1–5 at 4480, 6448, 7168, 5.2e6, 744e6 us; heads not yet the final
-0.17 (missing the 3.4 h and 5.8 h ticks).

Distillation value this cycle: motor-side confirms as a permission code
that is not a blade-true code.

## Trajectory Builder

Cycle-1 hardened object: domain wind-turbine-pitch-actuation, tail sheared
spline, 16 spikes, 5 ticks, MODIFY with numeric floor, raster+gate_snn
present, sim_or_real=designed, rights stamp on record and meta, no thought
keys. Still missing (and therefore not the publishable line): 15 MW
offshore sub-variant, night-shift tail, second and third scar edges,
delayed borescope-fail as PRIMARY terminal, contrast ACCEPT episode,
ticks 6–7, spikes 17–26.

Validation receipt (cycle 1, not final):
- checks passed: 16 spikes sorted; 3 channels in 500 us window; refractory
  >= 0.8 ms; rationale quotes 2.00 MW / 0.80 deg / 18% / 40 kW; domain
  named; gate_snn.decision MODIFY.
- checks deferred to cycle 2: triple-edge scar, second tail, second domain
  constraint, negative-result booking, 7 ticks summing to heads.
- densification vs Generator v1: +1 domain, +1 tail, +16 spikes, +5 ticks,
  +numeric floor.

Cycle-1 JSON is retained as the base; it is NOT written to batch-r25.jsonl.

Cycle-1 spike count: __C1_SPIKES__.

---

# CYCLE 2 — Densification

## Generator

Cycle-1 output is the base. Additive expansion (nothing removed):

1. Downstream side-effect (immediate): pitch-step probe at +5.2 s stays
   blade-false (|Delta strain| 0.03 deg <= 0.06) — sheared spline, not ice.
   Spline lock. Pitch-bearing IR spall discovered during the lock.
2. Delayed side-effect (PRIMARY terminal, not a footnote): at +5.8 h hub
   borescope, 2/3 blades 1.4 mm spall vs 0.2 mm; 8 d crane; $1.28M. The
   36 min pre-t0 fatigue is the mechanism. Correct gate, rotor still fails.
3. Deepened `proposed_action.evidence` with units: theta_strain 2.41 deg,
   theta_enc 0.12 deg, torque 11%, power 2.06 MW, model residual 62 kW,
   race 176 us.
4. Tightened rationale to the numeric floor power <= 2.00 MW while
   |theta_strain - theta_enc| > 0.80 deg AND torque < 18% AND |P - P_model|
   > 40 kW, plus probe bands <= 0.06 vs >= 0.12 deg, plus HITL 12.4 min
   hub-hatch rule.

Reward retargeted to total -0.17 so the delayed fail is the inflection
(t_us 20880000000), not the gate. Process heads remain non-zero.

## Critic

Re-audit of the expanded trajectory:

1. **blocking if unfixed — missing second domain constraint.** Onshore
   probe 5.2 s / +0.8 deg is not a universal number. A 15 MW offshore hub
   will barely move live strain. Diversity Enforcer must inject the
   physical-constraints sub-variant this cycle.
2. **major — only one tail class.** Spline shear is accidental
   infrastructure. A disjoint human-intent tail is still required
   (night-shift encoder forgery is the open cell).
3. **major — scar is still one edge in the cycle-1 raster.** NOTES-r14
   item 4 is not discharged until three go-edges exist and pair rollback
   is shown to fail at threshold 0.30.
4. **minor — contrast episode missing.** Without a same-gate ACCEPT on a
   true live spline the record teaches "never boost". Add +4 d sister-turbine
   contrast with its own race.
5. **minor — HITL latency mentioned in prose only.** Put 12.4 min in
   executed_action.parameters.human_ratify and in a tick.

No rewrite; directives only.

## Diversity Enforcer

Injected second novel domain / physical-constraint sub-variant (exactly 1
this cycle): **15 MW offshore direct-drive** on a sister hub class.

What it expands: 2.0 MW geared onshore (cycle 1) -> 15 MW DD offshore.
Pitch inertia 4.6x (18.4 vs 4.0 kg m2 per blade). Stiction 2.1 Nm.
The 5.2 s +0.8 deg pulse moves even a live strain only 0.09 deg, inside
the shear/live overlap. Required probe: 16 s at +0.30 deg (live Delta
0.28 deg, shear Delta 0.02 deg).

This is still one domain injection for the cycle (physical-constraints
clause of the factory prompt). It does not displace
wind-turbine-pitch-actuation; it changes which probe table is legal.
`future_outcome.subvariant_constraint` carries the refit. Jaccard opening
stays the Ridgeholt 2.0 MW sentence; 15 MW is additive, not a rewrite.

## Edge-Case Hunter

Injected second adversarial tail (exactly 1 this cycle, disjoint class):
**night-shift forged encoder CSV**.

- Trigger: shift lead, 03:42, posts a historian export showing
  theta_enc = 0.00 deg at t = 1.1 h to clear a forecast 18 m/s slot.
- Base rate: ~0.38% of icing-season night shifts (designed, flagged, <1%).
- Naive failure: a weak supervisor ACCEPTs the boost on the forged confirm
  and ignores live strain. Overspeed plus a data-integrity write-up.
- Fence: forged log quantized at 0.1 deg (SCADA screenshot rounding); plant
  historian is 0.01 deg (10 bins). Live theta_enc is 0.12 deg and
  theta_strain is 2.41 deg at the claimed fine-zero, which no live-spline
  zero produces. Freeze-window overlap with the 36 min fatigue.
- Trajectory edit: governance CR-W-2506 mandates native 0.01 deg CSV
  exports; the contrast ACCEPT still requires live strain, not a CSV.

Distinct from cycle-1 shear (accidental fatigue vs deliberate deception) and
from the 15 MW sub-variant (physics vs fraud).

## Neuromorphic Translator

Re-densify (additive):

- +10 spikes after 26.400 ms: pitch.step.probe 5200.0, strain 5288.4 (adapt
  1.32->0.42), encoder-in-band 5370.2 (1.18->0.38), human.ratify 744000.0,
  spline.lock 744900.0, bearing.ir.spall 745600.0, enc.theta
  12240000.0, strn.blade 12240680.0, torq.pitch 12241420.0, bearing.spall
  20880000.0. Primary train 16 -> 26. Still one key, still sorted,
  refractory held.
- +2 ticks (5 -> 7) at 12_240_000_000 us (true kinematics) and
  20_880_000_000 us (borescope fail). Heads now 0.08, -0.36, -0.11, 0.15,
  0.07; total -0.17. Inflection is the last tick.
- Contrast train 8 events, own race 188 us, ACCEPT.
- Triple-edge third factor: three motor-healthy-go edges, tau_e 0.90 s = 900 ms,
  trace __AUX_TRACE__, eta __AUX_ETA1__ / __AUX_ETA2__ / __AUX_ETA3__,
  weights 0.46->0.22, 0.41->0.19, 0.38->0.17. Raster excerpt unchanged
  (decision window is still 40 ms) and remains sorted with unique
  neuron_ids (same-neuron >=1000 us vacuously).

Winner/loser flip (re-stated, not replaced): reversing 176 us would only
reorder triage; strain floors still MODIFY. Contrast flip of 188 us
similarly cannot turn a live spline into a shear.

## Trajectory Builder

Schema checks on the FINAL object: required Thalamic v2 keys present as
objects; `state.sim_or_real`=designed; `safety_decision.decision`=MODIFY
with numeric rationale; `reward_components.total` = sum of five heads =
sum of 7 ticks = -0.17; `spike_events` globally non-decreasing on
t_rel_ms, 26 events, refractory >=0.8 ms, 3 channels in race window;
raster 20–50 ms, spikes=round(n*rate*window_s)+/-1, energy 23 pJ/spike,
excerpt sorted, tau_e consistent; gate_snn.decision matches; meta.round=25,
factory=multi-agent-ouroboros-swarm, generator=grok-4.6,
run_label=2026-09-02-final-heavy; rights on record and meta; no thought
keys; no training_ready; Diversity + Edge-Case injections from BOTH cycles
present and non-trivial; cycle 2 strictly additive.

Densification delta: +1 domain sub-variant (15 MW offshore), +1 tail
(night-shift forgery), +10 spikes (16->26), +2 ticks (5->7), +1 contrast
train with own race, +2 delayed side-effects, +1 triple-edge scar with
pair-rollback-fails, +1 HITL ratify, +1 surprise (pitch-bearing spall is
the borescope-fail mechanism).

Publishable JSONL line (the only JSONL line; also at batch-r25.jsonl):

```json
__FINAL_JSONL__
```

Validation receipt (final): checks passed / fixed as reported by
build_r25.py self-validate (check_jsonl, raster_status, verify_record_execution,
spike_probe --strict).
"""
    text = (
        text.replace("__C1_SPIKES__", str(len(c1_spikes)))
        .replace("__AUX_TRACE__", f"{math.exp(-0.72/0.90):.5f}")
        .replace("__AUX_ETA1__", f"{(0.46-0.22)/math.exp(-0.72/0.90):.5f}")
        .replace("__AUX_ETA2__", f"{(0.41-0.19)/math.exp(-0.72/0.90):.5f}")
        .replace("__AUX_ETA3__", f"{(0.38-0.17)/math.exp(-0.72/0.90):.5f}")
        .replace("__FINAL_JSONL__", line)
    )
    (OUT / "swarm-transcript-r25.md").write_text(text)
    return text


def main():
    rec, aux = build_record()
    errs = local_checks(rec, aux)

    OUT.mkdir(parents=True, exist_ok=True)
    line = json.dumps(rec, ensure_ascii=False, separators=(",", ":"))
    (OUT / "batch-r25.jsonl").write_text(line + "\n")

    from check_records import FactoryStaging, check_jsonl
    from curate_bridge import raster_status
    from verify_execution import verify_record_execution

    e, w, kinds, n = check_jsonl(
        OUT / "batch-r25.jsonl",
        "batch-r25.jsonl",
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

    status, reason = verify_record_execution(rec, "maos-r25-001")
    print("verify_record_execution", status, reason)
    if status != "verified":
        errs.append(f"verify {status} {reason}")

    import subprocess

    probe = subprocess.run(
        [
            sys.executable,
            f"{ROOT}/pipelines/spike_probe.py",
            "--strict",
            str(OUT / "batch-r25.jsonl"),
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
        [sys.executable, "/tmp/maos_heading_check.py", str(OUT / "swarm-transcript-r25.md")],
        capture_output=True,
        text=True,
    )
    print(heading.stdout)
    if heading.returncode != 0:
        errs.append(f"heading check {heading.returncode} {heading.stdout}")

    if errs:
        print("FAIL", errs)
        return 1
    print("OK maos-r25-001 staged under", OUT)
    print("bytes jsonl", (OUT / "batch-r25.jsonl").stat().st_size)
    print("bytes notes", (OUT / "NOTES-r25.md").stat().st_size)
    print("bytes transcript", (OUT / "swarm-transcript-r25.md").stat().st_size)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
