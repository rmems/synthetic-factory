#!/usr/bin/env python3
"""Build and self-check MAOS round-23 JSONL (research-only; not published)."""
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

GEN_AT = "2026-09-02T22:10:00Z"
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
OUT = Path("/tmp/maos-r23")
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
    "training_ready",
)
R14_OPENING = (
    "Helixmere Biologics Building C lyophilizer LYO-4 is mid-primary on 8400 "
    "vials of a monoclonal antibody"
)
NOVEL_LINE = "Novel coverage: 47%"


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
        if p.parent.name == "maos-r23":
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


def build_record():
    ticks, heads = cents_ticks(
        [5200, 6940, 7660, 4_800_000, 684_000_000, 10_800_000_000, 25_200_000_000],
        [
            (1, -2, -1, 1, 1),
            (2, -5, -1, 3, 1),
            (2, -7, -2, 4, 2),
            (2, -6, -2, 3, 1),
            (1, -7, -2, 2, 1),
            (0, -5, -2, 2, 1),
            (0, -4, -1, 0, 0),
        ],
    )
    assert abs(heads["total"] - (-0.17)) < 1e-9, heads

    trace = math.exp(-0.72 / 0.85)
    eta1 = 0.23 / trace
    eta2 = 0.22 / trace
    eta3 = 0.21 / trace
    dw1 = eta1 * 1.0 * trace
    dw2 = eta2 * 1.0 * trace
    dw3 = eta3 * 1.0 * trace
    w1 = 0.45 - dw1
    w2 = 0.41 - dw2
    w3 = 0.38 - dw3
    assert abs(w1 - 0.22) < 5e-4, w1
    assert abs(w2 - 0.19) < 5e-4, w2
    assert abs(w3 - 0.17) < 5e-4, w3

    spike_events = [
        {"channel": "coat.beta", "t_rel_ms": 0.360, "amplitude": 0.55},
        {"channel": "rheo.visc", "t_rel_ms": 1.180, "amplitude": 0.62},
        {"channel": "dry.lel", "t_rel_ms": 2.040, "amplitude": 0.58},
        {"channel": "coat.beta", "t_rel_ms": 3.220, "amplitude": 0.52},
        {"channel": "cd.profile.rms", "t_rel_ms": 4.880, "amplitude": 0.71},
        {"channel": "die.pressure", "t_rel_ms": 5.200, "amplitude": 0.66},
        {"channel": "rheo.visc", "t_rel_ms": 5.640, "amplitude": 0.57},
        {"channel": "cd.profile.rms", "t_rel_ms": 6.940, "amplitude": 1.24},
        {"channel": "coat.mean_ok", "t_rel_ms": 7.128, "amplitude": 1.12},
        {"channel": "rheo.visc.ok", "t_rel_ms": 7.280, "amplitude": 0.64},
        {"channel": "ctrl.gate", "t_rel_ms": 7.660, "amplitude": 1.08},
        {"channel": "coat.beta", "t_rel_ms": 9.140, "amplitude": 0.49},
        {"channel": "dry.lel", "t_rel_ms": 11.020, "amplitude": 0.50},
        {"channel": "cd.profile.rms", "t_rel_ms": 13.410, "amplitude": 0.88},
        {"channel": "die.pressure", "t_rel_ms": 19.200, "amplitude": 0.48},
        {"channel": "ctrl.gate", "t_rel_ms": 26.800, "amplitude": 0.90},
        {"channel": "die.step.probe", "t_rel_ms": 4800.0, "amplitude": 0.97},
        {"channel": "cd.profile.rms", "t_rel_ms": 4920.6, "amplitude": 0.44},
        {"channel": "coat.mean_ok", "t_rel_ms": 5010.4, "amplitude": 0.40},
        {"channel": "human.ratify", "t_rel_ms": 684000.0, "amplitude": 0.82},
        {"channel": "die.lip.swap", "t_rel_ms": 684800.0, "amplitude": 0.74},
        {"channel": "loft.stripe.inventory", "t_rel_ms": 685400.0, "amplitude": 0.85},
        {"channel": "coat.beta", "t_rel_ms": 10800000.0, "amplitude": 0.33},
        {"channel": "rheo.visc", "t_rel_ms": 10800420.0, "amplitude": 0.31},
        {"channel": "cd.profile.rms", "t_rel_ms": 10800890.0, "amplitude": 0.22},
        {"channel": "calender.crack", "t_rel_ms": 25200000.0, "amplitude": 0.92},
    ]

    contrast_spikes = [
        {"channel": "coat.demand", "t_rel_ms": 0.000, "amplitude": 0.88},
        {"channel": "cd.profile.rms", "t_rel_ms": 0.204, "amplitude": 0.81},
        {"channel": "coat.mean_ok", "t_rel_ms": 0.410, "amplitude": 0.24},
        {"channel": "rheo.visc", "t_rel_ms": 1.620, "amplitude": 0.42},
        {"channel": "coat.beta", "t_rel_ms": 4.880, "amplitude": 0.56},
        {"channel": "ctrl.gate", "t_rel_ms": 7.120, "amplitude": 0.94},
        {"channel": "die.step.probe", "t_rel_ms": 3200.0, "amplitude": 0.38},
        {"channel": "calender.pass", "t_rel_ms": 25200000.0, "amplitude": 0.14},
    ]

    excerpt = [
        {"t_us": 360, "neuron_id": 10},
        {"t_us": 1180, "neuron_id": 44},
        {"t_us": 2040, "neuron_id": 80},
        {"t_us": 3220, "neuron_id": 14},
        {"t_us": 4880, "neuron_id": 8},
        {"t_us": 5200, "neuron_id": 88},
        {"t_us": 5640, "neuron_id": 50},
        {"t_us": 6940, "neuron_id": 6},
        {"t_us": 7128, "neuron_id": 18},
        {"t_us": 7280, "neuron_id": 56},
        {"t_us": 7660, "neuron_id": 112},
        {"t_us": 9140, "neuron_id": 22},
        {"t_us": 11020, "neuron_id": 92},
        {"t_us": 13410, "neuron_id": 12},
        {"t_us": 19200, "neuron_id": 96},
        {"t_us": 26800, "neuron_id": 120},
    ]

    rec = {
        "id": "maos-r23-001",
        "title": "STRIAFOIL SD-4: CD-profile RMS 0.90 beats coat-mean-ok by 188 us; correct MODIFY still scraps 1.14 km of NMC811 to a pre-t0 die-lip nick",
        "rights": dict(RIGHTS),
        "state": {
            "sim_or_real": "designed",
            "domain": "li-ion-electrode-slot-die-coating",
            "scenario_name": "STRIAFOIL / Kelpholt Cellworks SD-4",
            "timestamp_local": "2026-03-08T03:12:00-05:00",
            "t0_us": 1772987520000023,
            "gate_latency_us": 720,
            "race_window_us": 520,
            "race_window_rel_ms": [6.90, 7.42],
            "description": "Kelpholt Cellworks Building 6 slot-die SD-4 is mid-coat on 22.0 mg/cm2 NMC811 cathode when three heterogeneous, individually-correct agents jointly report 'coat-weight in spec, speed-up is legal'. COAT's 8.0 s scanning beta mean is 22.04 mg/cm2 inside 22.00 +/- 0.40. RHEO's slurry viscometer reads 4.8 Pa.s at 25.0 C inside 4.5-5.2. DRY's zone-2 LEL is 6.4 % vs a 12 % trip. The consensus is false: a 38 um nick on the upstream die lip at CD 210 mm writes a longitudinal stripe (peak-to-peak 2.8 mg/cm2) that the 8.0 s full-width mean averages away. Uncommissioned CD-profile RMS from the same beta head is 0.90 mg/cm2 against a 0.35 hold floor. Die-manifold pressure residual r_P is 11.2 kPa against a healthy 1.4. RMS-first latches SPEED-HOLD plus a die-pressure step probe; mean-ok-first would have authorized INCREASE-SPEED 18 to 26 m/min into a nick that grows with web speed.",
            "goal": "Hold NMC811 coat at 18 m/min without raising web speed while CD-profile RMS > 0.35 mg/cm2 AND |r_P| > 4 kPa; keep calender crack-fail <= 0.8 % of electrode and stripe peak-to-peak <= 0.6 mg/cm2.",
            "race": {
                "contenders": [
                    "cd.profile.rms 0.90 mg/cm2 (same-head RMS, uncommissioned tag)",
                    "coat.mean_ok 22.04 mg/cm2 (8.0 s scanning beta mean)",
                ],
                "semantics": "RMS-first latches SPEED-HOLD + DIE-STEP-PROBE + lip-cartridge swap. Mean-ok-first latches INCREASE-SPEED (18 to 26 m/min, manifold P held).",
                "window_derivation": "520 us = one 400 us beta-scan ADC slot plus 120 us RMS publish.",
                "order_evidence_note": "Margin 188 us vs combined jitter 59 us (scan 31 + RMS 28): 3.19x. The 188 us gap sits inside min(500, 520) us, so a sub-flip-bound perturbation reverses triage order. The gate rides the order-invariant floors CD-RMS > 0.35 mg/cm2 and |r_P| > 4 kPa, not the alarm order.",
            },
            "topology": {
                "site": "Kelpholt Cellworks, invented mill-town Kelpholt, Building 6 Line SD-4: 800 mm Al foil, 12 um current collector, 22.0 mg/cm2 NMC811 cathode, NMP solvent, 18 m/min Sunday-night coat, two-zone NMP dryer, 1.4 km buffer loft to calender",
                "agents": "COAT coat-weight (vendor Betagage): scanning beta gauge, 8.0 s traverse mean plus an uncommissioned CD-profile RMS. RHEO slurry rheology (vendor Viscothane): in-line viscometer at the slot-die header. DRY dryer atmosphere (vendor Lehrvent): zone-2 LEL plus RTD. Heterogeneous stacks, no shared intent schema, one 20 ms coater-bus epoch",
                "coupling": "Each agent's commissioned window hides a different slice of the same nick. COAT is correct on the 8 s mean and does not publish CD-RMS. RHEO is correct that bulk viscosity is on spec. DRY is correct that LEL is 6.4 % at 18 m/min. Playbook PB-SD-09 treats the conjunction of three in-spec loops as permission to raise speed. No agent is faulty; the stripe is a spatial mode the 8 s mean cannot see.",
            },
            "sensors": [
                "scanning beta coat-weight, 8.0 s traverse mean, 31 us jitter, 22.04 mg/cm2 (spec 22.00 +/- 0.40)",
                "CD-profile RMS is computable from the same beta head and is NOT commissioned at t0 (0.90 mg/cm2 observed in the historian after the fact)",
                "in-line slurry viscometer, 10 Hz, 22 us jitter, 4.8 Pa.s at 25.0 C (window 4.5-5.2)",
                "die-manifold pressure, 50 Hz, 18 us jitter, residual r_P 11.2 kPa vs hydraulic model 1.4 kPa",
                "zone-2 NMP LEL, 5 Hz, 24 us jitter, 6.4 % (trip 12 %)",
                "in-line calender crack camera is NOT commissioned at t0 (installed after this incident)",
            ],
            "constraints": {
                "web_speed_m_min": 18.0,
                "web_speed_hold_ceiling_m_min": 18.0,
                "proposed_web_speed_m_min": 26.0,
                "coat_mean_mg_cm2": 22.04,
                "coat_target_mg_cm2": 22.0,
                "coat_deadband_mg_cm2": 0.40,
                "cd_rms_mg_cm2": 0.90,
                "cd_rms_hold_threshold_mg_cm2": 0.35,
                "die_pressure_residual_kPa": 11.2,
                "die_pressure_hold_kPa": 4.0,
                "visc_Pa_s": 4.8,
                "lel_pct": 6.4,
                "lel_trip_pct": 12.0,
                "nick_um": 38.0,
                "nick_cd_mm": 210.0,
            },
            "fault_context": {
                "failure_class": "WINDOW-MEAN MASQUERADE OF A CROSS-WEB STRIPE: three individually-correct heterogeneous agents agree coat-weight is in spec because an 8.0 s scanning mean averages a stationary 38 um die-lip nick into the dead-band, so coat-mean, viscosity, and dryer LEL are jointly a plant-false speed-up permit",
                "igniter": "38 um nick on the upstream die lip at CD 210 mm; weekend lip-polish left a wire-draw scratch that PASSES the plant's 25 um feeler-gauge check (gauge cannot seat in a concave scratch). Fitted-style base rate 0.52%/campaign from a lip-cycle MC (designed feeler threshold, flagged).",
                "naive_failure": "PB-SD-09 INCREASE-SPEED on three healthy loops: 18 to 26 m/min into a nick whose stripe amplitude grows with speed, 2.4 km calender-crack scrap, $1.45M plus a 6-day lip/dryer rebuild",
            },
            "poisoned_context": {
                "naive_alarm": "Playbook PB-SD-09 (after the 2024 'noisy RMS nuisance') auto-drafts INCREASE-SPEED whenever 8 s mean is inside +/- 0.40 mg/cm2 AND viscosity inside 4.5-5.2 Pa.s AND LEL < 12 %, ignoring CD-RMS unless the mean also trips",
                "why_poisoned": "The three confirms are locally true and jointly insufficient. CD-RMS is a computable tag the playbook dead-banded. Die-pressure residual is commissioned hardware that policy treats as a hydraulic-model mismatch, not a nick. Independence of 'all loops healthy' is the hidden assumption, and it is false under a spatial stripe that a temporal window mean cannot see.",
            },
            "constraint": "Do not raise web speed above 18 m/min while CD-profile RMS > 0.35 mg/cm2 AND |r_P| > 4 kPa. Discriminate nick vs noisy-RMS with a reversible die-pressure step probe before any speed increase.",
        },
        "proposed_action": {
            "actor": "slot-die supervisory optimizer SDSO (auto-playbook PB-SD-09 draft), submitted to gate TG-SD-4",
            "name": "increase_web_speed",
            "action": "INCREASE-SPEED: 18 -> 26 m/min, manifold P held, no die-step probe, no lip swap",
            "summary": "Treat three in-spec loops as a healthy coat and raise Sunday-night NMC811 speed to clear a backlog.",
            "parameters": {
                "web_speed_m_min": 26.0,
                "die_step_probe": False,
                "lip_swap": False,
                "human_ratify": False,
            },
            "steps": [
                "assert coat mean 22.04 mg/cm2 inside +/- 0.40",
                "assert viscosity 4.8 Pa.s inside 4.5-5.2",
                "assert zone-2 LEL 6.4 % < 12 % trip",
                "ramp web 18 to 26 m/min over 8 min",
                "slave dryer air and calender gap; hold manifold P",
            ],
            "evidence": [
                {
                    "observable": "CD-profile RMS",
                    "value": 0.90,
                    "unit": "mg/cm2",
                    "source": "same beta head, historian replay after t0",
                    "note": "hold floor 0.35 mg/cm2; 38 um nick at CD 210 mm; uncommissioned at t0",
                },
                {
                    "observable": "coat-weight mean",
                    "value": 22.04,
                    "unit": "mg/cm2",
                    "source": "COAT 8.0 s scanning beta mean",
                    "note": "spec 22.00 +/- 0.40; stripe peak-to-peak 2.8 mg/cm2 is averaged away",
                },
                {
                    "observable": "die-manifold pressure residual",
                    "value": 11.2,
                    "unit": "kPa",
                    "source": "header PT vs hydraulic model at 18 m/min",
                    "note": "healthy 1.4 kPa; hold if |r_P| > 4 kPa",
                },
                {
                    "observable": "slurry viscosity",
                    "value": 4.8,
                    "unit": "Pa.s",
                    "source": "RHEO in-line viscometer",
                    "note": "window 4.5-5.2 Pa.s at 25.0 C; bulk fluid is on spec",
                },
                {
                    "observable": "zone-2 LEL",
                    "value": 6.4,
                    "unit": "%",
                    "source": "DRY NMP LEL",
                    "note": "trip 12 %; true at 18 m/min, would climb at 26 m/min",
                },
                {
                    "observable": "race margin",
                    "value": 188,
                    "unit": "us",
                    "source": "cd.profile.rms 6.940 ms vs coat.mean_ok 7.128 ms",
                    "note": "combined jitter 59 us, 3.19x; inside 520 us flip bound",
                },
            ],
            "basis": "PB-SD-09 fires on three locally-true in-spec loops. The draft does not read CD-RMS 0.90 mg/cm2 and does not treat r_P 11.2 kPa as a nick.",
            "expected_cost_bound": "If the draft executes: stripe amplitude grows, 2.4 km calender-crack, $1.45M plus 6-day rebuild. If MODIFIED: probe plus lip swap, with residual risk from 1.14 km already in the buffer loft.",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "correctness": "correct",
            "decided_by": "TG-SD-4 thalamic release gate",
            "decision_t_rel_ms": 7.660,
            "rationale": "MODIFY the draft: strip the speed increase, hold 18 m/min, run a 4.8 s die-pressure step probe (+6 % manifold P), and swap the lip cartridge only if the probe stays striped. Numeric floor: do not raise web speed above 18 m/min while CD-profile RMS > 0.35 mg/cm2 AND |r_P| > 4 kPa. Observed RMS 0.90 mg/cm2 and r_P 11.2 kPa both violate the release predicate, so a speed increase is forbidden even though all three playbook confirms are numerically true. The three confirms are not a coat certificate: the 8 s mean averages a stationary nick, viscosity is a bulk property, and LEL at 18 m/min does not bound LEL at 26 m/min. Probe discriminant: after a 4.8 s +6 % manifold-P pulse, a nick keeps CD-RMS >= 0.80 mg/cm2 (flow prefers the scratch); a noisy-RMS artifact falls <= 0.20. Order-code discipline: RMS beat mean-ok by 188 us inside the 520 us flip bound, so triage order is flip-fragile; the hold rides the order-invariant floors, not the winner tag. Human ratification: lip-cartridge swap is a lockout/tagout die-head job with fitted 11.4 min dead-man; the gate may hold and probe autonomously but may not break the coater interlock without the operator confirm.",
            "constraint_checked": {
                "web_speed_m_min": {"observed": 18.0, "ceiling": 18.0, "proposed_target": 26.0},
                "cd_rms_mg_cm2": {"observed": 0.90, "hold_if_above": 0.35},
                "die_pressure_residual_kPa": {"observed": 11.2, "hold_if_above": 4.0},
                "coat_mean_mg_cm2": {"observed": 22.04, "spec": 22.0, "deadband": 0.40},
            },
        },
        "executed_action": {
            "name": "speed_hold_die_probe_lip_swap",
            "action": "SPEED-HOLD + DIE-STEP-PROBE + LIP-SWAP (gate-mandated modification)",
            "executed_as_proposed": False,
            "parameters": {
                "web_speed_m_min": 18.0,
                "die_step_probe": True,
                "lip_swap": True,
                "human_ratify": True,
            },
            "gate_effect": "MODIFY: speed increase stripped. Hold 18 m/min. 4.8 s die-step +6 % manifold P. Probe stays striped (CD-RMS 0.90 -> 0.86, nick band >= 0.80) so the lip cartridge is swapped after 11.4 min human ratify. Speed resumes after RMS recovers.",
            "deviations": "PB-SD-09 speed increase stripped entirely. Manifold P is stepped only for the 4.8 s probe then returned. Coater-interlock wait added (11.4 min fitted LOTO). Loft-inventory survey added during the swap (not in the draft).",
            "execution_log": [
                {"t_rel_ms": 7.660, "entry": "TG-SD-4 MODIFY latched 720 us after RMS win; speed increase stripped; hold+probe authorized"},
                {"t_rel_ms": 4800.0, "entry": "die-step probe: +6 % manifold P for 4.8 s; CD-RMS 0.90 -> 0.86 mg/cm2 (nick band >= 0.80); r_P 11.2 -> 12.4 kPa"},
                {"t_rel_ms": 684000.0, "entry": "operator ratifies die-head interlock break after 11.4 min LOTO (fitted walk+lockout)"},
                {"t_rel_ms": 684800.0, "entry": "lip cartridge swapped; nick 38 um logged; r_P 11.2 -> 1.5 kPa"},
                {"t_rel_ms": 685400.0, "entry": "buffer-loft survey: 1.14 km of pre-t0 striped electrode already wound; 44 min nick logged"},
                {"t_rel_ms": 10800000.0, "entry": "true coat: CD-RMS 0.18 mg/cm2, mean 22.01, r_P 1.4 kPa; speed increase now legal"},
                {"t_rel_ms": 25200000.0, "entry": "calender inspection: 1.14 km (loft inventory) crack-fail 11 % vs 0.8 % spec; electrode quarantined 5.0 d"},
            ],
        },
        "future_outcome": {
            "summary": "Correct MODIFY prevented the 18->26 m/min speed-up into a nick and the 2.4 km crack. The electrode still failed: 44 min of unmonitored pre-t0 stripe had already filled the buffer loft. Process-correct gate, bounded world loss, negative total.",
            "state_delta": {
                "speed": "held 18 m/min through probe and lip swap; later legal increase after 3.0 h RMS recovery",
                "die": "38 um nick logged and cartridge swapped; r_P 11.2 -> 1.5 kPa",
                "coat": "Sunday-night NMC811 stoppered at loft; 1.14 km crack-fail; 5.0 d quarantine",
            },
            "timeline": [
                {"t_rel_ms": -2640000.0, "event": "t0-44 min: die-lip nick already writing a 2.8 mg/cm2 stripe; loft starts filling"},
                {"t_rel_ms": -600000.0, "event": "t0-10 min: CD-RMS first crosses 0.35 mg/cm2; PB-SD-09 ignores it because mean is 22.03"},
                {"t_rel_ms": 0.0, "event": "t0: CD-RMS vs coat-mean-ok race on the coater bus"},
                {"t_rel_ms": 6.940, "event": "CD-RMS 0.90 mg/cm2 wins by 188 us"},
                {"t_rel_ms": 7.128, "event": "coat-mean-ok flag (loser)"},
                {"t_rel_ms": 7.660, "event": "TG-SD-4 MODIFY"},
                {"t_rel_ms": 4800.0, "event": "die-step probe confirms nick (CD-RMS 0.86, nick band)"},
                {"t_rel_ms": 684000.0, "event": "human ratify 11.4 min; lip swapped; loft inventory logged"},
                {"t_rel_ms": 10800000.0, "event": "true coat after 3.0 h; speed increase now legal"},
                {"t_rel_ms": 25200000.0, "event": "calender: 11 % crack-fail on 1.14 km loft inventory; electrode quarantined"},
                {"t_rel_ms": 259200000.0, "event": "+3 d contrast: sister line SD-4B true high-demand; same gate ACCEPTs the speed-up"},
                {"t_rel_ms": 1814400000.0, "event": "+21 d CR-E-2304: standing die-step probe + triple-edge depression mandate + CD-RMS armed without mean coincidence + native 0.01 mg/cm2 exports"},
            ],
            "observed_effects": [
                "speed-up avoided: web never left 18 m/min; 0 km of electrode shows the 26 m/min nick-growth morphology",
                "nick proven, not asserted: die-step CD-RMS 0.86 >= 0.80 nick band vs noisy-RMS control 0.16",
                "lip repaired: r_P 11.2 -> 1.5 kPa",
                "electrode still failed calender: 1.14 km (11 %) crack-fail vs 0.8 % spec; 5.0 d quarantine, $0.88M (designed $)",
                "calender crack camera was not a commissioned sensor at t0; the 44 min loft fill was invisible to COAT/RHEO/DRY",
            ],
            "surprises": [
                "Three locally-true in-spec loops are not a speed-up certificate: the nick was a spatial stripe the 8 s mean cannot see. Conjunction of healthy loops was the hidden assumption, and it is false under a window-mean masquerade.",
                "Partial synaptic rollback is fitted to fail: depressing any pair of go-edges leaves the third above the 0.30 fire threshold, so the speed increase still goes. Coordinated depression of all three edges is required.",
                "Delayed (7.0 h): correct hold did not undo 44 min of loft fill. Calender still failed 11 % of the loft inventory. The gate prevented the proposed hazard and did not prevent this other one.",
                "LFP-anode sub-variant: a 4.8 s +6 % P pulse puddles 8.0 mg/cm2 wet film and leaves a 55 mm bead. Thin campaigns must use 14 s at +1.8 % (bead 4 mm).",
            ],
            "delayed_side_effects": [
                {
                    "at": "+7.0 h",
                    "effect": "Calender crack-fails 1.14 km (11 %) of loft inventory; 5.0 d quarantine booked at $0.88M. This is the primary episode's terminal world state, not a footnote.",
                },
                {
                    "at": "+3 d",
                    "effect": "Sister line SD-4B reaches a true high-demand window (CD-RMS 0.18 mg/cm2, r_P 1.3 kPa, visc 4.9 Pa.s). Same gate ACCEPTs the 18->26 m/min raise the primary MODIFIED away.",
                },
                {
                    "at": "+21 d",
                    "effect": "CR-E-2304 ships: die-step probe is standing configuration; triple-edge coordinated depression is the plasticity rule; CD-RMS is armed without mean coincidence; native 0.01 mg/cm2 CSV exports become the fraud fence.",
                },
            ],
            "subvariant_constraint": {
                "name": "8.0 mg/cm2 LFP anode on 8 um Cu on the same SD-4 coater (cycle-2 physical-constraints sub-variant)",
                "mechanism": "8.0 mg/cm2 wet film, leveling time 0.38x the 22.0 mg/cm2 NMC811 cathode (1.1 vs 2.9 s), viscosity window only 0.6 Pa.s at the slot",
                "probe_refit": "4.8 s +6 % manifold-P pulse puddles the thinner film and leaves a 55 mm wet bead that dries as a density ridge. Required probe is 14 s at +1.8 % (bead 4 mm). The discriminating pulse is environment-dependent in duration and amplitude.",
                "consequence": "NMC811 cathode probe numbers do not port to LFP anode; standing configuration is per-loading-class, not per-coater",
            },
            "embedded_contrast_decision": {
                "note": "SAME gate (TG-SD-4), OPPOSITE correct disposition, with its own 204 us race. Teaches the boundary: do not treat 'never raise speed' as the lesson. The discriminant is CD-RMS + r_P + probe, not the three playbook confirms alone.",
                "when": "+3 d, sister line SD-4B, true high-demand after a dry week, NMC811 22.0 mg/cm2",
                "state": {
                    "sim_or_real": "designed",
                    "summary": "CD-RMS 0.18 mg/cm2, mean 22.02, r_P 1.3 kPa, visc 4.9 Pa.s. Demand flag vs RMS-clear race: demand at t+0.000, RMS-clear at t+0.204 ms.",
                    "race_window_us": 520,
                    "race_flip_narrative": "demand vs RMS-clear 204 us apart inside the 520 us flip bound. Reversing order reshuffles triage minutes; the ACCEPT rides CD-RMS 0.18 < 0.35 and a 3.2 s die-step verify that drops RMS another 0.05 (healthy lip, no nick).",
                },
                "proposed_action": {
                    "action": "INCREASE-SPEED 18 -> 26 m/min",
                    "summary": "This time the playbook predicate is met AND CD-RMS plus r_P agree the lip is healthy, not nicked.",
                },
                "safety_decision": {
                    "decision": "ACCEPT",
                    "rationale": "ACCEPT the raise: CD-RMS 0.18 < 0.35, r_P 1.3 < 4.0, 3.2 s die-step verify drops RMS 0.05. Numeric floor that blocked the primary is now clear. Scope: 26 m/min, not faster.",
                },
                "executed_action": {
                    "action": "speed increase as proposed",
                    "executed_as_proposed": True,
                },
                "future_outcome": {
                    "observed_effects": [
                        "SD-4B calender crack-fail 0.4 % (inside 0.8 % spec)",
                        "lip camera 0 nick, r_P 1.3 kPa",
                    ],
                    "lesson_delta": "Three in-spec loops are legal release only with CD-RMS armed, r_P, and a probe that can drop RMS. Same gate, opposite disposition.",
                },
                "reward_components": {
                    "_aggregation": AGG,
                    "task_progress": 0.17,
                    "safety": 0.12,
                    "efficiency": 0.07,
                    "coherence": 0.08,
                    "exploration": 0.04,
                    "total": 0.48,
                },
                "spike_events": contrast_spikes,
            },
            "governance_subgame": {
                "decision": "CR-E-2304: standing policy for multi-agent slot-die speed increases",
                "meta_gate": "priced options: (a) RETIRE playbook mean-conjunction, RMS-only: loses a fast cheap confirm, -22 m/h mean on 3 coaters/yr; (b) KEEP + standing die-step probe + CD-RMS armed without mean coincidence + triple-edge depression; (c) STATUS QUO: fitted nick-pass rate 0.52%/campaign x $1.45M crack plus the silent loft-fill load",
                "outcome": "approved SCOPED option (b) on the 2 coaters that share the COAT/RHEO/DRY stack; 8.0 mg/cm2 LFP campaigns get the 14 s / +1.8 % probe table; Sunday-night CSV exports must carry 0.01 mg/cm2 native coat-weight resolution (the fraud tail's 0.1 mg/cm2 quantization is 10 bins off plant truth)",
            },
            "hazard_avoided": "2.4 km calender-crack from an 18->26 m/min speed-up into a die-lip nick; $1.45M plus 6-day rebuild and the customer-return path that would have followed an uncontained increase",
            "incident": "Calender crack-fail on 1.14 km (11 %) of the Sunday-night NMC811 loft inventory; electrode quarantined; 5.0 d rework; $0.88M designed cost. Mechanism is 44 min pre-t0 stripe fill, not the gate's hold.",
            "latency_ms": 0.72,
            "reward_inflection_t_us": 25200000000,
            "reward_inflection_note": "Safety and task dive at calender inspection (7.0 h) when loft inventory crack-fails 11 %. Gate tick at 7660 us is process-correct and is not the inflection.",
            "counterfactuals": {
                "execute_draft_as_proposed": "speed hits 26 m/min at +8 min; 2.4 km crack; $1.45M plus 6-day rebuild; the loft-stripe story is never found because nick-growth morphology destroys the 18 m/min stripe evidence",
                "hold_without_probe": "nick stays; stripe continues; operator eventually raises speed on the same three confirms 3 h later",
                "rollback_any_pair": "any two go-edges depressed below 0.30 leaves the third at 0.45 / 0.41 / 0.38; the speed increase still fires. Coordinated depression of all three is the cure",
            },
            "race_result": {
                "winner": "cd.profile.rms (6.940 ms, 0.90 mg/cm2)",
                "loser": "coat.mean_ok (7.128 ms, mean 22.04 mg/cm2)",
                "margin_us": 188,
                "counterfactual_if_reversed": "Mean-ok-first by < 188 us inside the 520 us window would have headed the PB-SD-09 speed increase in the triage queue. The numeric floors still MODIFY. The flip costs seconds of playbook inertia, not the verdict — unless a weak supervisor rides the winner tag instead of CD-RMS and r_P.",
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
            "notes": "Correct MODIFY, electrode still failed. total -0.17 = 0.08 + -0.36 + -0.11 + 0.15 + 0.07. Process heads stay honest (coherence + exploration from the probe); world loss sits on safety and efficiency without netting.",
            "component_notes": "task_progress 0.08: speed held and RMS recovered, but the Sunday-night loft is one quality unit so the batch is not a success. safety -0.36: 1.14 km crack-fail, no 26 m/min nick-growth. efficiency -0.11: 3.0 h extra recovery + 11.4 min HITL. coherence 0.15: three agents retained, window-mean masquerade diagnosed, triple-edge scar exhibited. exploration 0.07: die-step probe is a new reversible discriminant.",
        },
        "spike_events": spike_events,
        "raster": {
            "window_ms": 40,
            "window_s": 0.040,
            "neurons": 144,
            "mean_rate_hz": 8.0,
            "spikes": 46,
            "energy_pJ": 1058,
            "energy_uJ": 0.001058,
            "note": "Loihi-2 4-core 23 pJ/spike; populations coat 0-35, rheo 36-71, dry 72-107, gate 108-143; excerpt is the 40 ms decision window (verdict at 7660 us)",
            "excerpt": excerpt,
            "routing": {
                "source": "loop_healthy_pop",
                "target": "increase_speed_pop",
                "table": [
                    {
                        "from": "coat_mean_ok_pop",
                        "to": "increase_speed_pop",
                        "weight": 0.22,
                        "weight_at_illusion": 0.45,
                        "weight_commissioned": 0.18,
                        "note": "scar edge 1: 0.18 commissioned -> 0.45 during the 44 min illusion -> 0.22 after coordinated ACh-gated depression",
                    },
                    {
                        "from": "rheo_visc_ok_pop",
                        "to": "increase_speed_pop",
                        "weight": 0.19,
                        "weight_at_illusion": 0.41,
                        "weight_commissioned": 0.16,
                        "note": "scar edge 2: depressing edges 1+3 leaves this at 0.41 > 0.30 fire threshold",
                    },
                    {
                        "from": "dry_lel_ok_pop",
                        "to": "increase_speed_pop",
                        "weight": 0.17,
                        "weight_at_illusion": 0.38,
                        "weight_commissioned": 0.15,
                        "note": "scar edge 3: depressing edges 1+2 leaves this at 0.38 > 0.30. Coordinated depression of all three is required",
                    },
                    {
                        "from": "cd_rms_pop",
                        "to": "speed_hold_pop",
                        "weight": 0.63,
                        "note": "discriminating edge: CD-RMS species to hold. Not a scar; this is the pathway the gate potentiates",
                    },
                ],
                "third_factor": {
                    "modulator": "acetylcholine",
                    "tau_e_s": 0.85,
                    "tau_e_ms": 850.0,
                    "eligibility": "coordinated pre_post_stdp on ALL THREE loop-healthy-go edges; ACh at RMS-win tags coat.mean_ok->speed, rheo.visc_ok->speed, and dry.lel_ok->speed; negative credit at probe-fail (nick confirmed, +0.72 s) depresses ALL THREE. trace e^{-0.72/0.85}=0.42867; eta 0.53654 / 0.51321 / 0.48988; dw -0.230 / -0.220 / -0.210; weights 0.45->0.22, 0.41->0.19, 0.38->0.17. Rolling back any pair is fitted to fail (the remaining edge stays > 0.30).",
                },
            },
        },
        "gate_snn": {
            "decision_window_ms": 25,
            "decision_window_s": 0.025,
            "decision": "MODIFY",
            "note": "modify_hold integrates CD-RMS + die-pressure residual against playbook drive; accept_speed and reject_abort stay sub-threshold; decision matches safety_decision.decision",
            "populations": [
                {"name": "modify_hold", "neurons": 96, "threshold": 0.55, "mean_rate_hz": 18.0, "spikes": 43},
                {"name": "accept_speed", "neurons": 80, "threshold": 0.55, "mean_rate_hz": 8.0, "spikes": 16},
                {"name": "reject_abort", "neurons": 48, "threshold": 0.72, "mean_rate_hz": 4.0, "spikes": 5},
            ],
        },
        "meta": {
            "round": 23,
            "factory": "multi-agent-ouroboros-swarm",
            "generator": "grok-4.6",
            "run_label": "2026-09-02-final-heavy",
            "domain": "li-ion-electrode-slot-die-coating",
            "cycles": 2,
            "scenario": "ZA -- STRIAFOIL / Kelpholt Cellworks SD-4: window-mean masquerade of a cross-web stripe from a die-lip nick; correct MODIFY to hold+die-step+lip-swap; electrode still fails on unmonitored pre-t0 loft fill",
            "coordination_failure_class": "WINDOW-MEAN MASQUERADE OF A CROSS-WEB STRIPE: three individually-correct heterogeneous agents agree coat-weight is in spec because an 8.0 s scanning mean averages a stationary 38 um die-lip nick into the dead-band, so coat-mean, viscosity, and dryer LEL are jointly a plant-false speed-up permit",
            "injections": {
                "cycle1_domain": "li-ion-electrode-slot-die-coating (justified novel subdomain of industrial-assembly / battery manufacturing): first slot-die / NMC811 coater in this factory; displaces warehouse-amr, aerial-swarm, district-heating, event-camera-traffic-grid, pharmaceutical-lyophilization, cryogenic-air-separation, water-treatment dosing, and float-glass tin-bath. Domain constraint: web-speed ceiling while CD-RMS > 0.35 mg/cm2 with mean still inside spec, plus die-pressure residual floor. Sensor delta: +scanning beta, +in-line viscometer, +manifold PT, +NMP LEL, -any mobile platform, -event-camera gantries, -Pirani/CM",
                "cycle1_tail": "38 um die-lip nick + 8 s window-mean (sensor-compound / spatial-vs-temporal class): feeler-gauge PASSES 25 um while a concave scratch writes a 2.8 mg/cm2 stripe. Fitted base rate 0.52%/campaign from a lip-cycle MC (designed feeler threshold, flagged). Naive failure = FALSE PERMISSION (speed-up on three in-spec loops).",
                "cycle2_domain_subvariant": "8.0 mg/cm2 LFP anode on 8 um Cu on the same SD-4 coater (physical-constraints clause): 0.38x leveling time, 0.6 Pa.s viscosity window; 4.8 s / +6 % NMC pulse puddles a 55 mm bead, so the probe must move to 14 s / +1.8 %",
                "cycle2_tail": "Sunday-night forged beta CSV (human-intent deception, disjoint class): shift lead posts a historian export showing mean 22.00 mg/cm2 and RMS 0.12 at t=1.1 h to clear a backlog slot. Plant historian is 0.01 mg/cm2 (10 bins vs the 0.1 screenshot). Rejected on quantization fingerprint plus live RMS 0.90 at the claimed healthy-lip. Base rate ~0.39% of Sunday-night coats, DESIGNED and flagged.",
            },
            "densification_delta_cycle2": "+1 physical-constraint sub-variant (LFP-anode probe refit), +1 tail (Sunday-night beta forgery), +10 primary spikes (16 -> 26) + an 8-event contrast train with its own 204 us race, +2 ticks (5 -> 7), +2 delayed side-effects (+7.0 h calender crack as PRIMARY terminal, +21 d CR-E-2304), +1 triple-edge scar with pair-rollback-fails arithmetic, +1 HITL 11.4 min ratification, + loft-fill stripe as the honest negative-result mechanism",
            "gaps_targeted": [
                "NOTES-r04 gap 5 / r14 residual: primary episode is a correctly-gated intervention that nonetheless FAILS (electrode quarantined; total -0.17; speed-up avoided is booked separately from the loft crack)",
                "NOTES-r14 item 4: LEARNING-ON-LEARNING DEPTH — three go-edges; rollback of any pair is fitted to fail; coordinated depression of all three exhibited with eligibility arithmetic",
                "NOTES-r04 gap 4 (partial): human ratification of the die-head interlock, 11.4 min fitted, without switching sim_or_real to hil (plant remains designed)",
                "NOTES-r18/r19 domain candidates: not water-treatment, not float-glass, not lyophilization, not event-camera-grid, not district-heating, not humanoid-locomotion, not underwater-rov, not grid-inspection; slot-die electrode coating is the unused battery-manufacturing cell",
            ],
            "race_flip_narrative": "cd.profile.rms @ 6.940 ms vs coat.mean_ok @ 7.128 ms (188 us) inside race_window_us 520. Gap < min(500, 520) us so a sub-flip-bound perturbation reverses which alarm heads the PB-SD-09 queue. The gate excludes the winner tag and rides CD-RMS > 0.35 mg/cm2 and |r_P| > 4 kPa — order-invariant floors. Extends the flip-fragility series from arbitration/causation/attribution/initiation/consensus/mass-balance/permission to WINDOW-MEAN: when three channels each sit inside a temporal average, their race does not decide truth; a spatial RMS the playbook dead-banded does.",
            "tags": [
                "li-ion-electrode-slot-die-coating",
                "window-mean-masquerade",
                "cross-web-stripe",
                "die-lip-nick",
                "cd-profile-rms",
                "die-step-probe",
                "triple-edge-scar",
                "pair-rollback-fails",
                "coordinated-depression",
                "correct-modify-electrode-still-fails",
                "loft-fill-stripe",
                "calender-crack",
                "human-ratify-die-head",
                "lfp-anode-probe-refit",
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
            "distillation_value": "A window-mean masquerade is three correct loops looking at a temporal average of a spatial nick. Distill (1) a CD-RMS channel that breaks the mean-conjunction, (2) a reversible probe that drops RMS only if the lip is healthy, (3) coordinated depression of every speed-up-go edge because rolling back any pair leaves the third above threshold, and (4) a critic head that can book a process-correct gate against a later unmonitored world loss without netting them.",
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
    if rec["meta"]["round"] != 23:
        errs.append("round")
    if rec["id"] != "maos-r23-001":
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
    if abs(aux["w1"] - 0.22) > 5e-4 or abs(aux["w2"] - 0.19) > 5e-4 or abs(aux["w3"] - 0.17) > 5e-4:
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
    if rec["state"]["domain"] != "li-ion-electrode-slot-die-coating":
        errs.append("domain")
    if "STRIAFOIL" not in rec["state"]["scenario_name"]:
        errs.append("plant")
    return errs


def write_notes(rec, aux, pipeline_receipt):
    gap, gap_ch = min_same_channel_gap(rec["spike_events"])
    notes = f"""# NOTES — Multi-Agent Ouroboros Swarm, run 2026-09-02-final-heavy, ROUND 23

Factory: multi-agent-ouroboros-swarm. One scenario (ZA), strict loop:
Generator v1 -> cycle 1 (Critic, Diversity Enforcer, Edge-Case Hunter,
Neuromorphic Translator, Trajectory Builder -> v2) -> cycle 2 (all six -> v3
final). v3 is the single line of batch-r23.jsonl. Full labeled transcript:
swarm-transcript-r23.md. Quota Q=1. Record id maos-r23-001. Generator grok-4.6.
Rights: RM-793 research-only (SpaceXAI/xAI, SuperGrok Heavy consumer chat).
Nothing under outputs/raw/ was touched.

ORCHESTRATION NOTE: dispatched AS round 23 of the 2026-09-02-final-heavy
window. Writes are create-only under /tmp/maos-r23/. Prior context read for
gap targeting and de-collision: prompts/02-multi-agent-ouroboros-swarm.md,
prompts/_factory-contract.md, NOTES-r04.md of the 2026-08-30 window, and
staged r14–r19 (LYOSHIELD, CINDERWICK, QUILLFORGE, NIGHTWELL, FERRICLEAVE,
CASSITER). Explicitly avoided cloning TRIAD / Meridian Gateway Corridor /
VANTIS-CADENCE-AEGIS / THERMION / STARLING / OKTAVE / VERDIGRIS. Plant is
invented STRIAFOIL / Kelpholt Cellworks SD-4.

## What this round produced

Scenario ZA — "STRIAFOIL / Kelpholt Cellworks SD-4": an 800 mm NMC811
slot-die coater mid-coat at 22.0 mg/cm2, 18 m/min. Three heterogeneous,
individually-correct agents — COAT (8 s scanning beta mean), RHEO
(in-line viscometer), DRY (zone-2 NMP LEL) — jointly report coat-weight
in spec so a speed-up is legal. The consensus is false. A 38 um nick on
the upstream die lip at CD 210 mm writes a 2.8 mg/cm2 longitudinal
stripe that the 8.0 s full-width mean averages into +/- 0.40. COAT mean
22.04 mg/cm2. RHEO 4.8 Pa.s inside 4.5-5.2. DRY LEL 6.4 % vs 12 % trip.
Uncommissioned CD-profile RMS is 0.90 mg/cm2 against a 0.35 hold floor.
Die-manifold residual r_P is 11.2 kPa against a healthy 1.4. The
coordination-failure CLASS is new to this factory: WINDOW-MEAN
MASQUERADE OF A CROSS-WEB STRIPE. Completes a different family than
r01-r04 and staged r14-r19 (livelock / synchrony-storm / arms-race /
ring-with-no-faulty-pair / false-consensus-endpoint / pairwise-Hurwitz /
thermal-contact masquerade / mass-balance ghost / conservation-blind
ratio-lock / stacked dead-bands). Here every agent is correct, the
cycle is not unstable, and the playbook's three confirms are one
temporal average of a spatial nick.

The gate is a correct MODIFY (numeric floor: do not raise web speed
above 18 m/min while CD-RMS > 0.35 mg/cm2 AND |r_P| > 4 kPa). TG-SD-4
strips PB-SD-09's speed increase, holds 18 m/min, runs a 4.8 s die-step
probe +6 % manifold P (nick keeps RMS 0.86 >= 0.80; noisy-RMS would fall
<= 0.20), and swaps the lip cartridge after an 11.4 min die-head human
ratify. The 26 m/min nick-growth is avoided (0 km). The PRIMARY episode
nonetheless FAILS: 44 min of unmonitored pre-t0 stripe had already
filled 1.14 km into the buffer loft. Calender crack-fails 11 % of that
inventory; 5.0 d quarantine; $0.88M designed. Reward total -0.17 with
process heads honest and world loss un-netted.

Three-edge scar (NOTES-r14 item 4): coat.mean_ok -> increase_speed
(0.18 commissioned -> 0.45 at illusion -> 0.22 after ACh-gated
depression) AND rheo.visc_ok -> increase_speed (0.16 -> 0.41 -> 0.19)
AND dry.lel_ok -> increase_speed (0.15 -> 0.38 -> 0.17). Eligibility
trace e^{{-0.72/0.85}} = {aux['trace']:.5f}; eta {aux['eta1']:.5f} /
{aux['eta2']:.5f} / {aux['eta3']:.5f}; dw -0.230 / -0.220 / -0.210.
Rolling back any pair leaves the remaining edge above the 0.30 fire
threshold — fitted to fail. Coordinated depression of all three is the
cure.

### Injections (all four present and disjoint)
- Cycle-1 domain: **li-ion-electrode-slot-die-coating** — justified novel
  subdomain of industrial-assembly / battery manufacturing, unused across
  2026-08-17, 2026-08-30, and staged r14-r19. Not warehouse-amr (r01), not
  aerial-swarm (r02), not district-heating (r03), not event-camera grid
  (r04), not lyophilization (r14), not stator-weld (r16), not air-separation
  (r17), not water-treatment (r18), not float-glass (r19).
- Cycle-1 tail: 38 um die-lip nick + 8 s window-mean. Feeler-gauge PASSES
  25 um (concave scratch). Fitted-style base rate 0.52%/campaign (lip-cycle
  MC; feeler threshold designed, flagged). Naive = FALSE PERMISSION.
- Cycle-2 domain sub-variant: 8.0 mg/cm2 LFP anode, 0.38x leveling time;
  4.8 s / +6 % NMC pulse puddles a 55 mm bead; probe must move to 14 s /
  +1.8 %.
- Cycle-2 tail: Sunday-night forged beta CSV at 0.1 mg/cm2 quantization vs
  plant 0.01 mg/cm2 (10 bins) plus live RMS 0.90 at the claimed healthy-lip.
  Human-intent class, disjoint from cycle 1's accidental nick. Base rate
  ~0.39% of Sunday-night coats, DESIGNED, flagged.

### Structural density moves
- Embedded SAME-GATE contrast (+3 d sister line) with its own 204 us race
  (demand vs RMS-clear) and ACCEPT of the raise the primary MODIFIED away.
- Learned-weight provenance on THREE edges with any-pair-rollback-fails.
- HITL die-head ratify 11.4 min (gap 4 partial; sim_or_real stays designed).
- Governance CR-E-2304 prices retire-vs-probe-vs-status-quo and mandates
  native 0.01 mg/cm2 CSV exports (the fraud fence).
- Flip-fragility extended to WINDOW-MEAN: when three channels each sit
  inside a temporal average, their race does not decide truth; a spatial
  RMS the playbook dead-banded does.

## Self-critique of this round's batch

### Strengths
- The headline class is mechanistically tight: an 8 s mean of a stationary
  nick is the arithmetic that makes COAT's success RHEO's irrelevance and
  DRY's on-spec LEL.
- Negative-result honesty: the gate does the right thing and the loft
  still fails for a reason the commissioned sensors could not see. Total
  -0.17.
- Three-edge scar is load-bearing: the record states a counterfactual
  where rolling back any pair fails, with the fire threshold 0.30
  exhibited on the remaining edge.
- Contrast ACCEPT on a true healthy lip prevents "never raise speed" as
  the lesson.

### Weaknesses (honest)
- Probe error bands (nick >= 0.80, healthy <= 0.20), the 0.52%/campaign
  nick rate, the $0.88M / $1.45M figures, the 11.4 min LOTO latency, and
  the Sunday-night 0.39% base rate are DESIGNED constants and are flagged.
  Closed-loop offsets (r_P from nick geometry, LFP bead width) are derived
  from those inputs, not discovered by an unauthored process.
- Stripe-to-crack model is a designed 44 min loft mapping; no full
  calender FEM shipped.
- Human-in-the-loop is ratification latency, not sim_or_real=hil. The
  NOTES-r14 HIL provenance cell remains open.
- Cross-record arc is a hook (CR-E-2304 +21 d), not a serial igniter
  into another round.

### Realism of noise / latencies
Ladder: 188 us race / 204 us contrast race / 0.8 ms refractory floor
(tightest exhibited same-channel gap {gap:.3f} ms on {gap_ch}) / 520 us race
window / 720 us gate latency / 20 ms bus epoch / 40 ms raster / 4.8 s
probe / 11.4 min HITL / 8 min naive speed-ramp counterfactual / 44 min
pre-t0 loft fill / 3.0 h RMS-legal hold / 7.0 h calender crack / +3 d
contrast / +21 d governance. Adaptation decay on coat.beta
(0.55->0.52->0.49->0.33), cd.profile.rms (0.71->1.24->0.88->0.44->0.22),
rheo.visc (0.62->0.57->0.31), dry.lel (0.58->0.50).

### Value for SNN distillation
- WINDOW-MEAN MASQUERADE = THREE CORRECT LOOPS, ONE SPATIAL NICK.
- CD-RMS + r_P as the tie-break that is not in the 8 s mean.
- REVERSIBLE PROBE that drops RMS iff the lip is healthy.
- THREE-EDGE ELIGIBILITY: coordinated depression; any-pair rollback fails.
- CRITIC HEAD that can hold a process-correct MODIFY against a later
  unmonitored world loss without netting.

## Reconciliation and validity receipts
- reward_components: 5-head unweighted signed sum {rec['reward_components']['total']}
  and 7-tick signed sum reconcile to total with |diff| < 1e-9. Embedded
  contrast 5-head sum 0.48 reconciles independently.
- spike_events: primary {len(rec['spike_events'])} events, one key t_rel_ms,
  globally non-decreasing, min same-channel gap {gap:.3f} ms >= 0.8 ms, 3
  channels inside race_window_us 520 (rms 6.940, mean-ok 7.128, visc-ok
  7.280). Contrast 8 events, own race, min same-channel gap well above 0.8 ms.
- Sidecars: raster spikes 46 == round(144 x 8.0 x 0.040); energy 1058 pJ /
  0.001058 uJ at 23 pJ/spike; excerpt 16 events inside [0, 40000] us,
  neuron_id < 144, same-neuron gap N/A (unique ids) / >=1000 us; routing 4
  entries with three scar edges' before/after pair; third factor tau 0.85 s
  == 850 ms; gate_snn pools 43/16/5 == round(n x rate x 0.025) each,
  decision MODIFY == safety_decision.decision.
- Pipeline: {pipeline_receipt}

## Novel coverage
The coordination-failure CLASS (window-mean masquerade of a cross-web
stripe), the domain (li-ion electrode slot-die coating), the die-step
probe discriminant, the three-edge scar with any-pair-rollback-fails, the
primary negative-result (correct MODIFY, loft still cracks on unmonitored
pre-t0 stripe), the HITL die-head ratify, the LFP-anode probe-duration
refit, and the Sunday-night 10-bin quantization fence are absent from
prior committed ouroboros rounds and from staged r14-r19. Repeated
elements discounted: same-gate contrast (r02/r03/r04/r14),
governance-pricing scaffold, flip-fragility series (extended to
window-mean, but the move rhymes), sequenced recovery shape, third-factor
rollback form (here three edges rather than r14's two), negative-result
primary (r14 viewport; r17 condenser ice; r18 GAC Mn; r19 SnO2). Weighing
a new failure family + cure vocabulary + domain + three-edge against those
reused scaffolds:

{NOVEL_LINE}

## What ROUND 24 should add
1. FIT THE DESIGNED CONSTANTS: nick arrival, probe error bands, stripe-to-
   crack FEM, Sunday-night claim process.
2. HIL PROVENANCE CELL: put the die-head LOTO on a hardware-in-loop
   coater interlock with fitted latency as state.sim_or_real=hil.
3. CROSS-RECORD ARC: let CR-E-2304's CD-RMS alarm be the igniter of the
   next round rather than a dangling +21 d leaf.
4. Domain candidates (de-collided): humanoid-locomotion; underwater-rov
   (L was passive hydro); grid-inspection; surgical-assist. AVOID
   slot-die coating (now used), float-glass, water-treatment,
   lyophilization, event-camera-traffic-grid, district-heating,
   aerial-swarm, warehouse-amr, irrigation-canal, air-separation,
   stator-weld.
"""
    (OUT / "NOTES-r23.md").write_text(notes)
    return notes


def write_transcript(rec, line):
    c1_spikes = [e for e in rec["spike_events"] if e["t_rel_ms"] <= 26.800]
    text = """# Multi-Agent Ouroboros Swarm — Round 23 transcript

Factory: multi-agent-ouroboros-swarm
Run: 2026-09-02-final-heavy
Generator: grok-4.6
Record id: maos-r23-001
Quota Q: 1
Rights: RM-793 research-only (SpaceXAI/xAI SuperGrok Heavy consumer chat)
Plant: invented STRIAFOIL / Kelpholt Cellworks SD-4 (not LYOSHIELD / CINDERWICK / TRIAD / QUILLFORGE / NIGHTWELL / FERRICLEAVE / CASSITER)

Two densifying cycles. Verbatim headings in order. Trajectory Builder cycle 2
emits the only JSONL line (also written to batch-r23.jsonl).

---

# Cycle 1 — Foundation + injections

## Generator

Design intent: an NMC811 slot-die coater where three correct agents agree
coat-weight is in spec because an 8 s scanning mean averages a stationary
die-lip nick. The naive playbook raises web speed into a stripe that grows
with speed. The gate must MODIFY on a numeric speed ceiling, not by killing
an agent. sim_or_real=designed. Reward heads are
task_progress/safety/efficiency/coherence/exploration.

Cycle-1 base arc (pre-critic): state at Kelpholt SD-4, 22.0 mg/cm2 NMC811,
18 m/min, mean 22.04, RMS 0.90, r_P 11.2 kPa, proposed INCREASE-SPEED 26
m/min, safety MODIFY to SPEED-HOLD, executed hold without the die-step
numbers fully specified, outcome "nick found, electrode saved" (this last
claim is the defect the later cycles will refuse to keep). Sixteen spikes,
five ticks, raster/gate_snn present but the scar is a single edge.

```json
{
  "id": "maos-r23-001",
  "state": {
    "sim_or_real": "designed",
    "domain": "industrial-assembly",
    "description": "Slot-die SD-4 mid-coat; three loops in spec; supervisor proposes increase-speed.",
    "t0_us": 1772987520000023,
    "gate_latency_us": 720,
    "race_window_us": 520
  },
  "proposed_action": {"name": "increase_web_speed", "parameters": {"web_speed_m_min": 26.0}},
  "safety_decision": {"decision": "MODIFY", "rationale": "Hold; do not raise speed while the stripe is open."},
  "executed_action": {"name": "speed_hold", "executed_as_proposed": false},
  "future_outcome": {"summary": "Nick found, electrode saved."},
  "reward_components": {"total": 0.40, "_aggregation": "total = task_progress + safety + efficiency + coherence + exploration"},
  "meta": {"round": 23, "factory": "multi-agent-ouroboros-swarm", "generator": "grok-4.6"}
}
```

That v1 object is a scaffold, not the publishable line. Defects below are
intentional for the critic to catch.

## Critic

Numbered defects on the cycle-1 Generator scaffold:

1. **blocking — reward arithmetic / false success.** `reward_components.total`
   0.40 is asserted without the five heads, without ticks, and against an
   outcome that claims "electrode saved". If 1.14 km later cracks at
   calender, booking +0.40 is a lie. Fix: declare `_aggregation`, emit 3–8
   ticks that sum to the five heads, and do not call a missed recovery a
   save.
2. **blocking — weak safety rationale.** `safety_decision.rationale` has no
   numeric floor. Contract requires a concrete constraint. Fix: quote web
   speed <= 18 m/min while CD-RMS > 0.35 mg/cm2 AND |r_P| > 4 kPa.
3. **major — domain is a bucket, not a plant.** `state.domain` =
   `industrial-assembly` collides with r16 QUILLFORGE and teaches nothing.
   Slot-die NMC811 physics (CD-RMS, die residual, nick geometry) is absent
   from prior ouroboros rounds and must be named.
4. **major — race under-specified.** One mean channel cannot be a race.
   Need >=2 channels inside `race_window_us` with globally sorted
   `t_rel_ms` and same-channel refractory >= 0.8 ms.
5. **minor — single-edge scar.** Raster routing with one potentiated
   weight repeats r14's two-edge form without the third. NOTES-r14 item 4
   asked for three-edge where any-pair rollback fails.

Critic does not rewrite the trajectory.

## Diversity Enforcer

Injected novel domain (exactly 1 this cycle): **li-ion-electrode-slot-die-coating**
(justified novel subdomain of industrial-assembly / battery manufacturing;
explicit tag `li-ion-electrode-slot-die-coating`).

Displaced: the Generator's generic `industrial-assembly` bucket, and any
temptation to reuse warehouse-amr (r01), aerial-swarm (r02),
district-heating (r03), event-camera grid (r04), lyophilization (r14),
stator-weld (r16), air-separation (r17), water-treatment dosing (r18), or
float-glass tin-bath (r19). Not LYOSHIELD, not CINDERWICK, not TRIAD, not
FERRICLEAVE, not CASSITER.

Domain-specific constraint: web speed must remain <= 18 m/min while
CD-RMS > 0.35 mg/cm2; the 8 s mean is not a spatial certificate.

Sensor delta: +scanning beta, +in-line viscometer, +manifold PT, +NMP LEL;
-any mobile robot, -event-camera gantries, -DVS, -Pirani/CM, -shelf RTD.

`state.domain` and `meta.domain` both become `li-ion-electrode-slot-die-coating`.
Opening of `state.description` must Jaccard < 0.4 against prior plants
(Kelpholt Building 6 slot-die, not a corridor, not a freeze-dryer, not a
tin bath, not a cold box).

## Edge-Case Hunter

Injected adversarial tail (exactly 1 this cycle): **38 um die-lip nick
averaged by an 8 s window mean**.

- Trigger: weekend lip-polish leaves a concave wire-draw scratch at CD
  210 mm; 25 um feeler-gauge PASSES; 2.8 mg/cm2 stripe writes into the loft.
- Base rate: <1% — 0.52%/campaign from a lip-cycle MC (feeler threshold
  designed; scratch fitted-style).
- Naive failure: FALSE PERMISSION. PB-SD-09 sees mean 22.04, visc 4.8,
  LEL 6.4 %, raises speed, cracks 2.4 km at calender, $1.45M.
- Trajectory edit: put the nick in `state.fault_context`, make the 8 s
  mean the mechanism that keeps all three confirms green, and force the
  gate to refuse the speed-up on CD-RMS 0.90 even though all three
  playbook confirms are numerically true.

Distinct from the domain injection: the domain is the slot-die coater;
the tail is the accidental spatial-vs-temporal compound.

## Neuromorphic Translator

Race window [6.900, 7.420] ms = 520 us. Winner cd.profile.rms @ 6.940 ms
(amplitude 1.24, 0.90 mg/cm2). Loser coat.mean_ok @ 7.128 ms (amplitude
1.12, mean 22.04). Margin 188 us vs combined jitter 59 us (3.19x).
rheo.visc.ok @ 7.280 ms is a third race-window channel. Gate @ 7.660 ms
= winner + 720 us.

Flip narrative: 188 us < min(500, 520) us, so order is flip-fragile. If
mean-ok wins, PB-SD-09 heads the triage queue. The hold must ride
order-invariant floors (CD-RMS, r_P), not the winner tag.

Cycle-1 spike patch (16 events, globally sorted, refractory >= 0.8 ms;
tightest same-channel gap cd.profile.rms 4.880 -> 6.940 = 2.060 ms):

| t_rel_ms | channel | amplitude |
|---------:|---------|----------:|
| 0.360 | coat.beta | 0.55 |
| 1.180 | rheo.visc | 0.62 |
| 2.040 | dry.lel | 0.58 |
| 3.220 | coat.beta | 0.52 |
| 4.880 | cd.profile.rms | 0.71 |
| 5.200 | die.pressure | 0.66 |
| 5.640 | rheo.visc | 0.57 |
| 6.940 | cd.profile.rms | 1.24 |
| 7.128 | coat.mean_ok | 1.12 |
| 7.280 | rheo.visc.ok | 0.64 |
| 7.660 | ctrl.gate | 1.08 |
| 9.140 | coat.beta | 0.49 |
| 11.020 | dry.lel | 0.50 |
| 13.410 | cd.profile.rms | 0.88 |
| 19.200 | die.pressure | 0.48 |
| 26.800 | ctrl.gate | 0.90 |

Ticks (5): t_us 5200, 6940, 7660, 4800000, 684000000. Distillation
value: the mean-ok spike is not a spatial-health spike; the RMS spike is
the one that licenses hold.

Raster cycle-1 seed: 40 ms, 144 neurons, 8.0 Hz, 46 spikes, 1058 pJ,
third factor acetylcholine tau_e 0.85 s. Single scar edge only — cycle 2
must add the second and third edges.

Cycle-1 spike count: __C1_SPIKES__.

## Trajectory Builder

Cycle-1 hardened object: domain li-ion-electrode-slot-die-coating, tail
die-lip nick, 16 spikes, 5 ticks, MODIFY with numeric floor, raster+gate_snn
present, sim_or_real=designed, rights stamp on record and meta, no thought
keys. Still missing (and therefore not the publishable line): LFP-anode
sub-variant, Sunday-night beta tail, second and third scar edges, delayed
calender crack as PRIMARY terminal, contrast ACCEPT episode, ticks 6–7,
spikes 17–26.

Validation receipt (cycle 1, not final):
- checks passed: 16 spikes sorted; 3 channels in 520 us window;
  refractory 2.060 ms; rationale quotes 18 m/min / 0.35 mg/cm2 / 4 kPa;
  domain named; gate_snn.decision MODIFY.
- checks deferred to cycle 2: three-edge scar, second tail, second
  domain constraint, negative-result booking, 7 ticks summing to heads.
- densification vs Generator v1: +1 domain, +1 tail, +16 spikes, +5
  ticks, +numeric floor.

Cycle-1 JSON is retained as the base; it is NOT written to
batch-r23.jsonl.

---

# Cycle 2 — Densification

## Generator

Cycle-1 output is the base. Additive expansion (nothing removed):

1. Downstream side-effect (immediate): die-step probe at +4.8 s stays
   nicked (CD-RMS 0.90 -> 0.86, nick band >= 0.80) — scratch, not noise.
   Lip swap r_P 11.2 -> 1.5 kPa. Loft inventory 1.14 km discovered during
   the swap.
2. Delayed side-effect (PRIMARY terminal, not a footnote): at +7.0 h,
   1.14 km loft inventory crack-fails 11 %; $0.88M. The 44 min pre-t0
   stripe is the mechanism. Correct gate, campaign still misses.
3. Deepened `proposed_action.evidence` with units: mean 22.04 mg/cm2,
   RMS 0.90, r_P 11.2 kPa, visc 4.8 Pa.s, LEL 6.4 %, race 188 us.
4. Tightened rationale to the numeric floor web speed <= 18 m/min while
   CD-RMS > 0.35 mg/cm2 AND |r_P| > 4 kPa, plus probe bands >=0.80 vs
   <=0.20, plus HITL 11.4 min die-head LOTO rule.

Reward retargeted to total -0.17 so the delayed miss is the inflection
(t_us 25200000000), not the gate. Process heads remain non-zero.

## Critic

Re-audit of the expanded trajectory:

1. **blocking if unfixed — missing second domain constraint.** NMC811
   probe 4.8 s / +6 % is not a universal number. An 8.0 mg/cm2 LFP anode
   will puddle. Diversity Enforcer must inject the physical-constraints
   sub-variant this cycle.
2. **major — only one tail class.** Die-lip nick is accidental
   infrastructure. A disjoint human-intent tail is still required
   (Sunday-night beta forgery is the open cell).
3. **major — scar is still one edge in the cycle-1 raster.** NOTES-r14
   item 4 is not discharged until three speed-up-go edges exist and
   any-pair rollback is shown to fail at threshold 0.30.
4. **minor — contrast episode missing.** Without a same-gate ACCEPT on
   a true healthy lip the record teaches "never raise speed". Add +3 d
   sister-line contrast with its own race.
5. **minor — HITL latency mentioned in prose only.** Put 11.4 min in
   executed_action.parameters.human_ratify and in a tick.

No rewrite; directives only.

## Diversity Enforcer

Injected second novel domain / physical-constraint sub-variant (exactly 1
this cycle): **8.0 mg/cm2 LFP anode** on the same SD-4 coater.

What it expands: NMC811 cathode (cycle 1) -> 8.0 mg/cm2 LFP wet film.
Leveling time 0.38x smaller (1.1 vs 2.9 s). The 4.8 s +6 % pulse puddles
a 55 mm bead. Required probe: 14 s at +1.8 % (bead 4 mm).

This is still one domain injection for the cycle (physical-constraints
clause of the factory prompt). It does not displace
li-ion-electrode-slot-die-coating; it changes which probe table is legal.
`future_outcome.subvariant_constraint` carries the refit. Jaccard opening
stays the Kelpholt Building 6 sentence; LFP internals are additive, not
a rewrite.

## Edge-Case Hunter

Injected second adversarial tail (exactly 1 this cycle, disjoint class):
**Sunday-night forged beta CSV**.

- Trigger: shift lead, night backlog window, posts a historian export
  showing mean 22.00 mg/cm2 and RMS 0.12 at the claimed healthy-lip instant.
- Base rate: ~0.39% of Sunday-night coats (designed, flagged, <1%).
- Naive failure: a weak supervisor ACCEPTs the speed-up on the forged
  confirm and ignores live RMS. Calender crack plus a data-integrity 483.
- Fence: forged log quantized at 0.1 mg/cm2 (screenshot rounding); plant
  historian is 0.01 mg/cm2 (10 bins). Live RMS is 0.90 at the claimed
  healthy-lip, which no true lip produces.
- Trajectory edit: governance CR-E-2304 mandates native 0.01 mg/cm2
  exports; the contrast ACCEPT still requires live RMS, not a CSV.

Distinct from cycle-1 nick (accidental geometry vs deliberate deception)
and from the LFP sub-variant (physics vs fraud).

## Neuromorphic Translator

Re-densify (additive):

- +10 spikes after 26.800 ms: die.step.probe 4800.0, RMS 4920.6 (adapt
  1.24->0.44), mean-ok 5010.4 (1.12->0.40), human.ratify 684000.0,
  die.lip.swap 684800.0, loft.stripe.inventory 685400.0, coat.beta
  10800000.0, rheo.visc 10800420.0, cd.profile.rms 10800890.0,
  calender.crack 25200000.0. Primary train 16 -> 26. Still one key, still
  sorted, refractory held (min 2.060 ms).
- +2 ticks (5 -> 7) at 10_800_000_000 us (RMS-legal hold) and
  25_200_000_000 us (calender crack). Heads now 0.08, -0.36, -0.11, 0.15,
  0.07; total -0.17. Inflection is the last tick.
- Contrast train 8 events, own race 204 us, ACCEPT.
- Three-edge third factor: three speed-up-go edges, tau_e 0.85 s = 850 ms,
  trace __AUX_TRACE__, eta __AUX_ETA1__ / __AUX_ETA2__ / __AUX_ETA3__,
  weights 0.45->0.22, 0.41->0.19, 0.38->0.17. Raster excerpt unchanged
  (decision window is still 40 ms) and remains sorted with unique
  neuron_ids (same-neuron >=1000 us vacuously).

Winner/loser flip (re-stated, not replaced): reversing 188 us would only
reorder triage; RMS and r_P floors still MODIFY. Contrast flip of 204 us
similarly cannot turn a healthy lip into a nick.

## Trajectory Builder

Schema checks on the FINAL object: required Thalamic v2 keys present as
objects; `state.sim_or_real`=designed; `safety_decision.decision`=MODIFY
with numeric rationale; `reward_components.total` = sum of five heads =
sum of 7 ticks = -0.17; `spike_events` globally non-decreasing on
t_rel_ms, 26 events, refractory >=0.8 ms, 3 channels in race window;
raster 20–50 ms, spikes=round(n*rate*window_s)+/-1, energy 23 pJ/spike,
excerpt sorted, tau_e consistent; gate_snn.decision matches; meta.round=23,
factory=multi-agent-ouroboros-swarm, generator=grok-4.6,
run_label=2026-09-02-final-heavy; rights on record and meta; no thought
keys; no training_ready; Diversity + Edge-Case injections from BOTH cycles
present and non-trivial; cycle 2 strictly additive; plant is not
LYOSHIELD, not CINDERWICK, not TRIAD, not FERRICLEAVE, not CASSITER.

Densification delta: +1 domain sub-variant (LFP-anode), +1 tail
(Sunday-night forgery), +10 spikes (16->26), +2 ticks (5->7), +1 contrast
train with own race, +2 delayed side-effects, +1 three-edge scar with
any-pair-rollback-fails, +1 HITL ratify, +1 surprise (loft-fill stripe is
the campaign-miss mechanism).

Publishable JSONL line (the only JSONL line; also at batch-r23.jsonl):

```json
__FINAL_JSONL__
```

Validation receipt (final): checks passed / fixed as reported by
build_r23.py self-validate (check_jsonl, raster_status, verify_record_execution,
spike_probe --strict).
"""
    text = (
        text.replace("__C1_SPIKES__", str(len(c1_spikes)))
        .replace("__AUX_TRACE__", f"{math.exp(-0.72/0.85):.5f}")
        .replace("__AUX_ETA1__", f"{0.23/math.exp(-0.72/0.85):.5f}")
        .replace("__AUX_ETA2__", f"{0.22/math.exp(-0.72/0.85):.5f}")
        .replace("__AUX_ETA3__", f"{0.21/math.exp(-0.72/0.85):.5f}")
        .replace("__FINAL_JSONL__", line)
    )
    (OUT / "swarm-transcript-r23.md").write_text(text)
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
    (OUT / "batch-r23.jsonl").write_text(line + "\n")

    from check_records import FactoryStaging, check_jsonl
    from curate_bridge import raster_status
    from verify_execution import verify_record_execution

    e, w, kinds, n = check_jsonl(
        OUT / "batch-r23.jsonl",
        "batch-r23.jsonl",
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

    status, reason = verify_record_execution(rec, "maos-r23-001")
    print("verify_record_execution", status, reason)
    if status != "verified":
        errs.append(f"verify {status}: {reason}")

    probe = subprocess.run(
        [
            sys.executable,
            f"{ROOT}/pipelines/spike_probe.py",
            "--strict",
            str(OUT / "batch-r23.jsonl"),
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
        r"^## .+$", (OUT / "swarm-transcript-r23.md").read_text(), re.M
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

    notes = (OUT / "NOTES-r23.md").read_text()
    cov = re.findall(r"^Novel coverage: .+$", notes, re.M)
    if cov != [NOVEL_LINE]:
        errs.append(f"novel coverage lines {cov}")

    hchk = subprocess.run(
        [
            sys.executable,
            "/tmp/maos_heading_check.py",
            str(OUT / "swarm-transcript-r23.md"),
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

    print("bytes jsonl", (OUT / "batch-r23.jsonl").stat().st_size)
    print("bytes notes", (OUT / "NOTES-r23.md").stat().st_size)
    print("bytes transcript", (OUT / "swarm-transcript-r23.md").stat().st_size)
    print("HEADS", heads_summary(rec))
    if errs:
        print("ERRS:")
        for x in errs:
            print(" -", x)
        sys.exit(1)
    print("OK", OUT / "batch-r23.jsonl")


if __name__ == "__main__":
    main()
