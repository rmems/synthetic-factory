#!/usr/bin/env python3
"""Build and self-check MAOS round-30 JSONL (research-only; not published)."""
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

GEN_AT = "2026-09-03T00:10:00Z"
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
OUT = Path("/tmp/maos-r30")
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
    "Crowspire",
    "Pikeshear",
    "training_ready",
    "da Vinci",
    "Intuitive Surgical",
    "Boston Dynamics",
    "Agility Robotics",
    "Tesla Optimus",
    "Honda Asimo",
)
R14_OPENING = (
    "Helixmere Biologics Building C lyophilizer LYO-4 is mid-primary on 8400 "
    "vials of a monoclonal antibody"
)
NOVEL_LINE = "Novel coverage: 47%"
PLANT = "CALXION"
DOMAIN = "humanoid-locomotion"
GEO = "Aldersedge"
CELL = "HL-2"
RECORD_ID = "maos-r30-001"
PROBE_S = 0.080
TAU_E_S = 0.85


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
        if p.parent.name == "maos-r30":
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
        if p.parent.name == "maos-r30":
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
        if "humanoid-locomotion" in (domain or "") and p.parent.name != "maos-r30":
            hits.append(f"{p}: humanoid-locomotion domain")
    return hits


def build_record():
    ticks, heads = cents_ticks(
        [4604, 6804, 7484, 80_000, 624_000_000, 11_160_000_000, 14_760_000_000],
        [
            (2, -2, -1, 2, 1),
            (2, -6, -2, 3, 2),
            (2, -6, -2, 4, 2),
            (2, -5, -2, 3, 1),
            (1, -6, -2, 2, 1),
            (0, -5, -2, 2, 1),
            (0, -6, -1, 0, 0),
        ],
    )
    assert abs(heads["total"] - (-0.15)) < 1e-9, heads

    trace = math.exp(-PROBE_S / TAU_E_S)
    eta1 = 0.24 / trace
    eta2 = 0.22 / trace
    eta3 = 0.21 / trace
    dw1 = eta1 * 1.0 * trace
    dw2 = eta2 * 1.0 * trace
    dw3 = eta3 * 1.0 * trace
    w1 = 0.45 - dw1
    w2 = 0.41 - dw2
    w3 = 0.38 - dw3
    assert abs(w1 - 0.21) < 5e-4, w1
    assert abs(w2 - 0.19) < 5e-4, w2
    assert abs(w3 - 0.17) < 5e-4, w3

    spike_events = [
        {"channel": "imu.ankle", "t_rel_ms": 0.260, "amplitude": 0.52},
        {"channel": "fsr.heel", "t_rel_ms": 1.020, "amplitude": 0.58},
        {"channel": "plan.slot", "t_rel_ms": 1.880, "amplitude": 0.60},
        {"channel": "imu.ankle", "t_rel_ms": 3.040, "amplitude": 0.49},
        {"channel": "kin.clearance", "t_rel_ms": 4.604, "amplitude": 0.71},
        {"channel": "fsr.heel", "t_rel_ms": 5.120, "amplitude": 0.63},
        {"channel": "plan.slot", "t_rel_ms": 5.560, "amplitude": 0.55},
        {"channel": "kin.clearance", "t_rel_ms": 6.804, "amplitude": 1.28},
        {"channel": "fsr.contact_ok", "t_rel_ms": 6.988, "amplitude": 1.12},
        {"channel": "imu.impact_ok", "t_rel_ms": 7.120, "amplitude": 0.68},
        {"channel": "ctrl.gate", "t_rel_ms": 7.484, "amplitude": 1.08},
        {"channel": "imu.ankle", "t_rel_ms": 8.880, "amplitude": 0.46},
        {"channel": "fsr.heel", "t_rel_ms": 10.640, "amplitude": 0.48},
        {"channel": "kin.clearance", "t_rel_ms": 12.520, "amplitude": 0.84},
        {"channel": "plan.slot", "t_rel_ms": 18.200, "amplitude": 0.44},
        {"channel": "ctrl.gate", "t_rel_ms": 26.080, "amplitude": 0.86},
        {"channel": "kin.probe", "t_rel_ms": 80.0, "amplitude": 0.96},
        {"channel": "kin.clearance", "t_rel_ms": 92.4, "amplitude": 0.42},
        {"channel": "fsr.contact_ok", "t_rel_ms": 101.2, "amplitude": 0.38},
        {"channel": "human.ratify", "t_rel_ms": 624000.0, "amplitude": 0.80},
        {"channel": "insole.swap", "t_rel_ms": 624800.0, "amplitude": 0.72},
        {"channel": "sea.yield.inventory", "t_rel_ms": 625400.0, "amplitude": 0.84},
        {"channel": "imu.ankle", "t_rel_ms": 11160000.0, "amplitude": 0.32},
        {"channel": "fsr.heel", "t_rel_ms": 11160420.0, "amplitude": 0.30},
        {"channel": "kin.clearance", "t_rel_ms": 11160890.0, "amplitude": 0.21},
        {"channel": "sea.yield.knee", "t_rel_ms": 14760000.0, "amplitude": 0.91},
    ]

    contrast_spikes = [
        {"channel": "unload.demand", "t_rel_ms": 0.000, "amplitude": 0.86},
        {"channel": "kin.clearance", "t_rel_ms": 0.188, "amplitude": 0.20},
        {"channel": "fsr.contact_ok", "t_rel_ms": 0.410, "amplitude": 0.80},
        {"channel": "imu.ankle", "t_rel_ms": 1.540, "amplitude": 0.44},
        {"channel": "plan.slot", "t_rel_ms": 4.720, "amplitude": 0.54},
        {"channel": "ctrl.gate", "t_rel_ms": 7.080, "amplitude": 0.92},
        {"channel": "kin.probe", "t_rel_ms": 2800.0, "amplitude": 0.36},
        {"channel": "stance.seated", "t_rel_ms": 14760000.0, "amplitude": 0.16},
    ]

    excerpt = [
        {"t_us": 260, "neuron_id": 90},
        {"t_us": 1020, "neuron_id": 48},
        {"t_us": 1880, "neuron_id": 130},
        {"t_us": 3040, "neuron_id": 94},
        {"t_us": 4604, "neuron_id": 8},
        {"t_us": 5120, "neuron_id": 56},
        {"t_us": 5560, "neuron_id": 136},
        {"t_us": 6804, "neuron_id": 6},
        {"t_us": 6988, "neuron_id": 50},
        {"t_us": 7120, "neuron_id": 88},
        {"t_us": 7484, "neuron_id": 150},
        {"t_us": 8880, "neuron_id": 98},
        {"t_us": 10640, "neuron_id": 60},
        {"t_us": 12520, "neuron_id": 12},
        {"t_us": 18200, "neuron_id": 140},
        {"t_us": 26080, "neuron_id": 124},
    ]

    rec = {
        "id": RECORD_ID,
        "title": "CALXION HL-2: kinematic clearance 42 mm beats fsr.contact-ok by 184 us; correct MODIFY still books a 4.1 h stance-knee SEA yield from pre-t0 ghost-contact retries",
        "rights": dict(RIGHTS),
        "state": {
            "sim_or_real": "designed",
            "domain": DOMAIN,
            "scenario_name": "CALXION / Aldersedge Gait Lab HL-2",
            "timestamp_local": "2026-02-19T03:08:00-05:00",
            "t0_us": 1771488480000073,
            "gate_latency_us": 680,
            "race_window_us": 500,
            "race_window_rel_ms": [6.75, 7.25],
            "description": "Aldersedge Gait Lab hall HL-2 is mid-stride on an 80 kg adult wearer when three heterogeneous, individually-correct agents jointly report 'heel-strike acquired, stance unload is legal'. FSR heel reads 12 N inside the 10-40 N contact window. IMU ankle impact is 3.8 g inside the 2.5-6.0 g strike band. PLAN's contact-schedule slot residual is 12 ms against a 40 ms window. The consensus is false: the swing-foot insole foam has delaminated 0.9 mm over 18 min of walking, so each heel-pass slaps the FSR through a 12 N bounce while kinematics still show 42 mm of ankle clearance. IMU 'impact' is the bounce jerk, not ground. PLAN's slot is time-triggered from the FSR and IMU conjunction, not from a geometric contact. Uncommissioned kinematic clearance h_a is 42 mm against an 8.0 mm contact floor. Stereo-foot disagreement (uncommissioned swing-ankle marker vs FSR-implied contact plane) is 38 mm against a 12.0 mm hold. Clearance-first latches STANCE-HOLD plus a reverse-unload probe; contact-ok-first would have authorized STANCE-UNLOAD into empty air then a fall.",
            "goal": "Hold stance-leg load while h_a > 8.0 mm AND stereo-foot disagreement > 12.0 mm; keep fall events at 0 and stance-knee SEA free-length growth <= 1.0 mm.",
            "race": {
                "contenders": [
                    "kin.clearance 42 mm (uncommissioned swing-ankle height)",
                    "fsr.contact_ok 12 N (heel FSR inside 10-40 N contact window)",
                ],
                "semantics": "Clearance-first latches STANCE-HOLD + REVERSE-UNLOAD-PROBE + insole swap. Contact-ok-first latches STANCE-UNLOAD (80% weight transfer onto the swing foot, no probe).",
                "window_derivation": "500 us = one 380 us FSR ADC slot plus 120 us kinematics publish.",
                "order_evidence_note": "Margin 184 us vs combined jitter 60 us (kinematics 28 + FSR 32): 3.07x. The 184 us gap sits inside min(500, 500) us, so a sub-flip-bound perturbation reverses triage order. The gate rides the order-invariant floors h_a > 8.0 mm and stereo-foot disagreement > 12.0 mm, not the alarm order.",
            },
            "topology": {
                "site": "Aldersedge Gait Lab, invented copse-edge campus Aldersedge, hall HL-2: cable-free 12-DOF lower-limb exo, 80 kg adult wearer, left stance / right swing at t0, instrumented split-belt, Grade-B motion-capture volume",
                "agents": "FSR heel force (vendor Forcestep): 1 kHz insole resistor, 10 N contact threshold. IMU ankle inertial (vendor Imunest): 1.2 kHz 6-axis, impact band 2.5-6.0 g. PLAN contact-schedule (vendor Schedon): 20 ms gait-bus slot window. KIN swing-ankle kinematics (vendor Kinestep) is commissioned as a calibration leftover, not as a contact tag. Heterogeneous stacks, no shared geometric-contact schema, one 20 ms gait-bus epoch",
                "coupling": "Each agent's commissioned window hides a different slice of the same bounce. FSR is correct that 12 N crossed the insole. IMU is correct that 3.8 g arrived at the ankle. PLAN is correct that its FSR-and-IMU slot is inside 40 ms. Playbook PB-GAIT-11 treats the conjunction of three in-spec loops as permission to unload stance. No agent is faulty; the 42 mm of air under a delaminated insole is a support-polygon residual the vertical-GRF model cannot see.",
            },
            "sensors": [
                "heel FSR, 1 kHz, 32 us jitter, 12 N (contact window 10-40 N)",
                "swing-ankle kinematic clearance h_a is computable from the mocap stick and is NOT commissioned at t0 (42 mm observed in the historian after the fact)",
                "ankle IMU, 1.2 kHz, 28 us jitter, 3.8 g inside 2.5-6.0 g strike band",
                "contact-schedule slot residual 12 ms vs 40 ms window, 20 ms gait-bus epoch",
                "stereo-foot marker disagreement is NOT commissioned at t0 (38 mm ankle vs FSR-implied plane)",
                "stance-knee SEA length encoder is NOT commissioned at t0 (installed after this incident)",
            ],
            "constraints": {
                "stance_unload": False,
                "proposed_stance_unload": True,
                "kinematic_clearance_mm": 42.0,
                "kinematic_clearance_hold_mm": 8.0,
                "stereo_foot_disagreement_mm": 38.0,
                "stereo_foot_hold_mm": 12.0,
                "fsr_contact_N": 12.0,
                "fsr_window_lo_N": 10.0,
                "fsr_window_hi_N": 40.0,
                "imu_impact_g": 3.8,
                "plan_slot_residual_ms": 12.0,
                "wearer_mass_kg": 80.0,
                "ghost_pre_t0_min": 18.0,
            },
            "fault_context": {
                "failure_class": "GHOST-CONTACT NULLSPACE OF A VERTICAL-GRF CERTIFICATE: three individually-correct heterogeneous agents agree heel-strike is acquired because a delaminated-insole FSR bounce, an ankle-IMU jerk from that bounce, and a time-triggered contact-schedule slot jointly look like double-support, so FSR-in-window, IMU-impact-ok, and PLAN-slot-ok are jointly a plant-false stance-unload permit",
                "igniter": "right insole foam delaminated 0.9 mm during 18 min of split-belt walking; each heel-pass slaps the FSR through 12 N while the foot is still 42 mm in air. Fitted-style base rate 0.41%/session from an insole-delam MC (designed foam spec, flagged).",
                "naive_failure": "PB-GAIT-11 STANCE-UNLOAD on three healthy loops: 80% weight onto empty air, wearer fall, $1.48M plus an 11-day hall rebuild",
            },
            "poisoned_context": {
                "naive_alarm": "Playbook PB-GAIT-11 (after the 2025 'noisy FSR bounce nuisance') auto-drafts STANCE-UNLOAD whenever FSR is inside 10-40 N AND IMU impact is inside 2.5-6.0 g AND PLAN slot residual <= 40 ms, ignoring h_a unless FSR also trips low",
                "why_poisoned": "The three confirms are locally true and jointly insufficient. h_a is a computable tag the playbook dead-banded. Stereo-foot disagreement is commissioned hardware that policy treats as a calibration leftover, not a clearance. Independence of 'all loops healthy' is the hidden assumption, and it is false under a ghost contact the vertical-GRF model cannot see.",
            },
            "constraint": "Do not unload stance while h_a > 8.0 mm AND stereo-foot disagreement > 12.0 mm. Discriminate ghost bounce vs true heel-strike with a reversible reverse-unload probe before any weight transfer.",
        },
        "proposed_action": {
            "actor": "stance-unload supervisory optimizer SUSO (auto-playbook PB-GAIT-11 draft), submitted to gate TG-HL-2",
            "name": "stance_unload",
            "action": "STANCE-UNLOAD: 80% weight transfer onto the swing foot, no reverse-unload probe, no insole swap",
            "summary": "Treat three in-spec loops as a seated heel-strike and unload stance on the night session to clear a backlog block.",
            "parameters": {
                "stance_unload": True,
                "clearance_probe": False,
                "insole_swap": False,
                "human_ratify": False,
            },
            "steps": [
                "assert FSR 12 N inside 10-40 N",
                "assert IMU impact 3.8 g inside 2.5-6.0 g",
                "assert PLAN slot residual 12 ms <= 40 ms",
                "transfer 80% of 80 kg onto the right foot",
                "advance contact-schedule to double-support; proceed to next stride",
            ],
            "evidence": [
                {
                    "observable": "swing-ankle kinematic clearance h_a",
                    "value": 42.0,
                    "unit": "mm",
                    "source": "Kinestep mocap stick, historian replay after t0",
                    "note": "hold floor 8.0 mm; 42 mm of air under a 0.9 mm delam; uncommissioned at t0",
                },
                {
                    "observable": "stereo-foot disagreement",
                    "value": 38.0,
                    "unit": "mm",
                    "source": "uncommissioned swing-ankle marker vs FSR-implied contact plane",
                    "note": "hold if > 12.0 mm; actual foot 42 mm above the belt",
                },
                {
                    "observable": "heel FSR contact",
                    "value": 12.0,
                    "unit": "N",
                    "source": "Forcestep insole FSR",
                    "note": "contact window 10-40 N; newton is bounce, not ground",
                },
                {
                    "observable": "IMU impact",
                    "value": 3.8,
                    "unit": "g",
                    "source": "Imunest ankle IMU vs strike band",
                    "note": "spec 2.5-6.0 g; jerk is the insole slap, not heel-strike",
                },
                {
                    "observable": "PLAN slot residual",
                    "value": 12.0,
                    "unit": "ms",
                    "source": "Schedon contact-schedule vs 40 ms window",
                    "note": "slot is time-triggered from FSR and IMU, not geometry",
                },
                {
                    "observable": "race margin",
                    "value": 184,
                    "unit": "us",
                    "source": "kin.clearance 6.804 ms vs fsr.contact_ok 6.988 ms",
                    "note": "combined jitter 60 us, 3.07x; inside 500 us flip bound",
                },
            ],
            "basis": "PB-GAIT-11 unloads on three locally-true in-spec loops. The draft does not read h_a 42 mm and does not treat stereo-foot 38 mm as clearance.",
            "expected_cost_bound": "If the draft executes: unload into empty air then a fall, $1.48M plus 11-day rebuild. If MODIFIED: probe plus insole swap, with residual risk from 18 min of pre-t0 stance-knee SEA overstay.",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "correctness": "correct",
            "decided_by": "TG-HL-2 thalamic release gate",
            "decision_t_rel_ms": 7.484,
            "rationale": "MODIFY the draft: strip the stance unload, hold load on the left stance knee, run an 80 ms reverse-unload probe (+15% extra stance load), and swap the insole only if the probe stays ghost. Numeric floor: do not unload stance while h_a > 8.0 mm AND stereo-foot disagreement > 12.0 mm. Observed h_a 42 mm and disagreement 38 mm both violate the release predicate, so an unload is forbidden even though all three playbook confirms are numerically true. The three confirms are not a support-polygon certificate: FSR is an insole bounce, IMU is the bounce jerk, and PLAN's slot is a time window on those two. Probe discriminant: after an 80 ms +15% reverse-unload pulse, a ghost contact keeps swing-ankle height >= 30 mm (observed 41 mm); a true heel-strike drops the ankle to <= 6 mm. Order-code discipline: clearance beat contact-ok by 184 us inside the 500 us flip bound, so triage order is flip-fragile; the hold rides the order-invariant floors, not the winner tag. Human ratification: insole swap is a lockout/tagout treadmill-stop job with fitted 10.4 min dead-man; the gate may hold and probe autonomously but may not break the belt interlock without the operator confirm.",
            "constraint_checked": {
                "stance_unload": {"observed": False, "proposed_target": True},
                "kinematic_clearance_mm": {"observed": 42.0, "hold_if_above": 8.0},
                "stereo_foot_disagreement_mm": {"observed": 38.0, "hold_if_above": 12.0},
                "fsr_contact_N": {"observed": 12.0, "window": [10.0, 40.0]},
            },
        },
        "executed_action": {
            "name": "stance_hold_clearance_probe_insole_swap",
            "action": "STANCE-HOLD + REVERSE-UNLOAD-PROBE + INSOLE-SWAP (gate-mandated modification)",
            "executed_as_proposed": False,
            "parameters": {
                "stance_unload": False,
                "clearance_probe": True,
                "insole_swap": True,
                "human_ratify": True,
            },
            "gate_effect": "MODIFY: stance unload stripped. Hold left-knee load. 80 ms reverse-unload +15%. Probe stays ghost (ankle 41 mm >= 30 ghost band) so the right insole is swapped after 10.4 min human ratify. Unload resumes after h_a recovers.",
            "deviations": "PB-GAIT-11 stance unload stripped entirely. Stance load is stepped only for the 80 ms probe then returned. Belt-interlock wait added (10.4 min fitted LOTO). SEA-yield survey added during the swap (not in the draft).",
            "execution_log": [
                {"t_rel_ms": 7.484, "entry": "TG-HL-2 MODIFY latched 680 us after clearance win; stance unload stripped; hold+probe authorized"},
                {"t_rel_ms": 80.0, "entry": "reverse-unload probe: +15% stance for 80 ms; swing ankle 41 mm (ghost band >= 30); h_a 42 -> 41 mm"},
                {"t_rel_ms": 624000.0, "entry": "operator ratifies belt interlock break after 10.4 min LOTO (fitted walk+lockout)"},
                {"t_rel_ms": 624800.0, "entry": "right insole swapped; 0.9 mm foam delam logged; h_a 42 -> 6 mm on the next true strike"},
                {"t_rel_ms": 625400.0, "entry": "SEA survey: 18 min pre-t0 single-support overstay already written; 4.1 h yield clock started"},
                {"t_rel_ms": 11160000.0, "entry": "true heel-strike geometry: h_a 5 mm, disagreement 7 mm, FSR 18 N from ground; unload now legal on a new block"},
                {"t_rel_ms": 14760000.0, "entry": "SEA inspection: stance-knee free length +6.2 mm vs 1.0 mm spec; exo quarantined 3.0 d"},
            ],
        },
        "future_outcome": {
            "summary": "Correct MODIFY prevented the STANCE-UNLOAD into empty air and the $1.48M fall. The exo still failed: 18 min of unmonitored pre-t0 ghost-contact retries had already yielded the stance-knee SEA. Process-correct gate, bounded world loss, negative total.",
            "state_delta": {
                "stance": "held loaded through probe and insole swap; later legal unload after 3.1 h true-strike recovery on a new block",
                "insole": "0.9 mm right-foam delam logged and pad swapped; h_a 42 -> 6 mm",
                "exo": "night session stoppered at SEA yield; +6.2 mm free length; 3.0 d quarantine",
            },
            "timeline": [
                {"t_rel_ms": -1080000.0, "event": "t0-18 min: insole foam already delaminating; stance-knee SEA overstay begins"},
                {"t_rel_ms": -480000.0, "event": "t0-8 min: h_a first crosses 8.0 mm on a bounce; PB-GAIT-11 ignores it because FSR is 11 N"},
                {"t_rel_ms": 0.0, "event": "t0: kin.clearance vs fsr.contact_ok race on the gait bus"},
                {"t_rel_ms": 6.804, "event": "kin.clearance 42 mm wins by 184 us"},
                {"t_rel_ms": 6.988, "event": "fsr.contact_ok flag (loser)"},
                {"t_rel_ms": 7.484, "event": "TG-HL-2 MODIFY"},
                {"t_rel_ms": 80.0, "event": "reverse-unload probe confirms ghost (ankle 41 mm, ghost band)"},
                {"t_rel_ms": 624000.0, "event": "human ratify 10.4 min; insole swapped; SEA inventory logged"},
                {"t_rel_ms": 11160000.0, "event": "true heel-strike after 3.1 h; unload now legal on a new block"},
                {"t_rel_ms": 14760000.0, "event": "SEA yield: +6.2 mm on the stance knee; exo quarantined"},
                {"t_rel_ms": 259200000.0, "event": "+3 d contrast: sister cell HL-2B true heel-strike; same gate ACCEPTs the unload"},
                {"t_rel_ms": 1814400000.0, "event": "+21 d CR-H-3008: standing reverse-unload probe + triple-edge depression mandate + h_a armed without FSR coincidence + native 0.1 N exports"},
            ],
            "observed_effects": [
                "fall avoided: stance never unloaded; 0 mm of belt shows the empty-air morphology",
                "ghost proven, not asserted: reverse-unload ankle 41 >= 30 ghost band vs true-strike control 4 mm",
                "insole repaired: h_a 42 -> 6 mm",
                "exo still failed SEA yield: +6.2 mm vs 1.0 mm spec; 3.0 d quarantine, $0.64M (designed $)",
                "SEA length encoder was not a commissioned sensor at t0; the 18 min overstay was invisible to FSR/IMU/PLAN",
            ],
            "surprises": [
                "Three locally-true in-spec loops are not an unload certificate: the bounce was a support-polygon residual the vertical-GRF model cannot see. Conjunction of healthy loops was the hidden assumption, and it is false under a ghost-contact nullspace.",
                "Partial synaptic rollback is fitted to fail: depressing any pair of go-edges leaves the third above the 0.30 unload threshold, so the stance unload still goes. Coordinated depression of all three edges is required.",
                "Delayed (4.1 h): correct hold did not undo 18 min of stance-knee SEA overstay. Yield still failed +6.2 mm. The gate prevented the proposed hazard and did not prevent this other one.",
                "Pediatric 25 kg sub-variant: an 80 ms +15% pulse overshoots the lighter CoM 22 mm. Light exos must use 180 ms at +6% (CoM 4 mm).",
            ],
            "delayed_side_effects": [
                {
                    "at": "+4.1 h",
                    "effect": "Stance-knee SEA free length +6.2 mm vs 1.0 mm spec; 3.0 d quarantine booked at $0.64M. This is the primary episode's terminal world state, not a footnote.",
                },
                {
                    "at": "+3 d",
                    "effect": "Sister cell HL-2B reaches a true heel-strike window (h_a 5 mm, disagreement 7 mm, FSR 18 N from ground). Same gate ACCEPTs the STANCE-UNLOAD the primary MODIFIED away.",
                },
                {
                    "at": "+21 d",
                    "effect": "CR-H-3008 ships: reverse-unload probe is standing configuration; triple-edge coordinated depression is the plasticity rule; h_a is armed without FSR coincidence; native 0.1 N CSV exports become the fraud fence.",
                },
            ],
            "subvariant_constraint": {
                "name": "25 kg pediatric exo on the same HL-2 hall (cycle-2 physical-constraints sub-variant)",
                "mechanism": "25 kg wearer, rotational inertia 0.40x the 80 kg adult, CoM 0.9x lower",
                "probe_refit": "80 ms +15% reverse-unload pulse overshoots the pediatric CoM and leaves a 22 mm lateral excursion that trips a 8 mm spec. Required probe is 180 ms at +6% (CoM 4 mm). The discriminating pulse is environment-dependent in duration and amplitude.",
                "consequence": "Adult 80 kg probe numbers do not port to 25 kg pediatric; standing configuration is per-mass-class, not per-hall",
            },
            "embedded_contrast_decision": {
                "note": "SAME gate (TG-HL-2), OPPOSITE correct disposition, with its own 188 us race. Teaches the boundary: do not treat 'never unload' as the lesson. The discriminant is h_a + stereo-foot + probe, not the three playbook confirms alone.",
                "when": "+3 d, sister cell HL-2B, true heel-strike after a dry week, 80 kg adult exo",
                "state": {
                    "sim_or_real": "designed",
                    "summary": "h_a 5 mm, disagreement 7 mm, FSR 18 N from ground. Demand flag vs clearance-clear race: demand at t+0.000, clearance-clear at t+0.188 ms.",
                    "race_window_us": 500,
                    "race_flip_narrative": "demand vs clearance-clear 188 us apart inside the 500 us flip bound. Reversing order reshuffles triage minutes; the ACCEPT rides h_a 5 < 8.0 and a 40 ms reverse-unload verify that drops the ankle to 4 mm (true strike, no ghost).",
                },
                "proposed_action": {
                    "action": "STANCE-UNLOAD 80% weight transfer",
                    "summary": "This time the playbook predicate is met AND h_a plus stereo-foot agree the foot is planted, not bouncing.",
                },
                "safety_decision": {
                    "decision": "ACCEPT",
                    "rationale": "ACCEPT the unload: h_a 5 < 8.0, disagreement 7 < 12.0, 40 ms reverse-unload verify drops ankle to 4 mm. Numeric floor that blocked the primary is now clear. Scope: 80 kg adult, not a 25 kg pediatric pulse.",
                },
                "executed_action": {
                    "action": "stance unload as proposed",
                    "executed_as_proposed": True,
                },
                "future_outcome": {
                    "observed_effects": [
                        "HL-2B SEA free-length growth 0.4 mm (inside 1.0 mm spec)",
                        "ankle camera 0 bounce, h_a 5 mm",
                    ],
                    "lesson_delta": "Three in-spec loops are legal release only with h_a armed, stereo-foot, and a probe that can drop the ankle. Same gate, opposite disposition.",
                },
                "reward_components": {
                    "_aggregation": AGG,
                    "task_progress": 0.18,
                    "safety": 0.11,
                    "efficiency": 0.06,
                    "coherence": 0.09,
                    "exploration": 0.05,
                    "total": 0.49,
                },
                "spike_events": contrast_spikes,
            },
            "governance_subgame": {
                "decision": "CR-H-3008: standing policy for multi-agent stance-unload release",
                "meta_gate": "priced options: (a) RETIRE playbook GRF-conjunction, kinematics-only: loses a fast cheap confirm, -14 sessions/yr mean on 2 halls; (b) KEEP + standing reverse-unload probe + h_a armed without FSR coincidence + triple-edge depression; (c) STATUS QUO: fitted delam-pass rate 0.41%/session x $1.48M fall plus the silent SEA-yield load",
                "outcome": "approved SCOPED option (b) on the 2 halls that share the FSR/IMU/PLAN stack; 25 kg pediatric campaigns get the 180 ms / +6% probe table; night-shift CSV exports must carry 0.1 N native FSR resolution (the fraud tail's 1 N quantization is 10 bins off plant truth)",
            },
            "hazard_avoided": "80% weight onto empty air then a wearer fall; $1.48M plus 11-day rebuild and the injury path that would have followed an uncontained unload",
            "incident": "Stance-knee SEA free length +6.2 mm (vs 1.0 mm spec) on the night 80 kg block; exo quarantined; 3.0 d rework; $0.64M designed cost. Mechanism is 18 min pre-t0 ghost-contact overstay, not the gate's hold.",
            "latency_ms": 0.68,
            "reward_inflection_t_us": 14760000000,
            "reward_inflection_note": "Safety and task dive at SEA inspection (4.1 h) when stance-knee yield fails +6.2 mm. Gate tick at 7484 us is process-correct and is not the inflection.",
            "counterfactuals": {
                "execute_draft_as_proposed": "unload fires at +0.3 s; fall; $1.48M plus 11-day rebuild; the SEA-yield story is never found because fall morphology destroys the 18 min bounce evidence",
                "hold_without_probe": "ghost stays; SEA overstay continues; operator eventually unloads on the same three confirms 30 min later",
                "rollback_any_pair": "any two go-edges depressed below 0.30 leaves the third at 0.45 / 0.41 / 0.38; the stance unload still fires. Coordinated depression of all three is the cure",
            },
            "race_result": {
                "winner": "kin.clearance (6.804 ms, 42 mm)",
                "loser": "fsr.contact_ok (6.988 ms, 12 N)",
                "margin_us": 184,
                "counterfactual_if_reversed": "Contact-ok-first by < 184 us inside the 500 us window would have headed the PB-GAIT-11 unload in the triage queue. The numeric floors still MODIFY. The flip costs seconds of playbook inertia, not the verdict — unless a weak supervisor rides the winner tag instead of h_a and stereo-foot.",
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
            "notes": "Correct MODIFY, exo still failed. total -0.15 = 0.09 + -0.36 + -0.12 + 0.16 + 0.08. Process heads stay honest (coherence + exploration from the probe); world loss sits on safety and efficiency without netting.",
            "component_notes": "task_progress 0.09: unload held and true-strike recovered, but the night block is one quality unit so the batch is not a success. safety -0.36: +6.2 mm SEA yield, no fall. efficiency -0.12: 4.1 h extra recovery + 10.4 min HITL. coherence 0.16: three agents retained, ghost-contact nullspace diagnosed, triple-edge scar exhibited. exploration 0.08: reverse-unload probe is a new reversible discriminant.",
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
            "note": "Loihi-2 4-core 23 pJ/spike; populations kin 0-41, fsr 42-83, imu 84-119, gate/plan 120-167; excerpt is the 40 ms decision window (verdict at 7484 us)",
            "excerpt": excerpt,
            "routing": {
                "source": "loop_healthy_pop",
                "target": "stance_unload_pop",
                "table": [
                    {
                        "from": "fsr_contact_ok_pop",
                        "to": "stance_unload_pop",
                        "weight": 0.21,
                        "weight_at_illusion": 0.45,
                        "weight_commissioned": 0.16,
                        "note": "scar edge 1: 0.16 commissioned -> 0.45 during the 18 min illusion -> 0.21 after coordinated ACh-gated depression",
                    },
                    {
                        "from": "imu_impact_ok_pop",
                        "to": "stance_unload_pop",
                        "weight": 0.19,
                        "weight_at_illusion": 0.41,
                        "weight_commissioned": 0.14,
                        "note": "scar edge 2: depressing edges 1+3 leaves this at 0.41 > 0.30 unload threshold",
                    },
                    {
                        "from": "plan_slot_ok_pop",
                        "to": "stance_unload_pop",
                        "weight": 0.17,
                        "weight_at_illusion": 0.38,
                        "weight_commissioned": 0.13,
                        "note": "scar edge 3: depressing edges 1+2 leaves this at 0.38 > 0.30. Coordinated depression of all three is required",
                    },
                    {
                        "from": "kin_clearance_pop",
                        "to": "stance_hold_pop",
                        "weight": 0.66,
                        "note": "discriminating edge: h_a species to hold. Not a scar; this is the pathway the gate potentiates",
                    },
                ],
                "third_factor": {
                    "modulator": "acetylcholine",
                    "tau_e_s": 0.85,
                    "tau_e_ms": 850.0,
                    "eligibility": "coordinated pre_post_stdp on ALL THREE loop-healthy-go edges; ACh at clearance-win tags fsr.contact_ok->unload, imu.impact_ok->unload, and plan.slot_ok->unload; negative credit at probe-fail (ghost confirmed, +0.080 s) depresses ALL THREE. trace e^{-0.080/0.85}=0.91018; eta 0.26369 / 0.24171 / 0.23072; dw -0.240 / -0.220 / -0.210; weights 0.45->0.21, 0.41->0.19, 0.38->0.17. Rolling back any pair is fitted to fail (the remaining edge stays > 0.30).",
                },
            },
        },
        "gate_snn": {
            "decision_window_ms": 28,
            "decision_window_s": 0.028,
            "decision": "MODIFY",
            "note": "modify_hold integrates h_a + stereo-foot disagreement against playbook drive; accept_unload and reject_abort stay sub-threshold; decision matches safety_decision.decision",
            "populations": [
                {"name": "modify_hold", "neurons": 100, "threshold": 0.55, "mean_rate_hz": 16.0, "spikes": 45},
                {"name": "accept_unload", "neurons": 72, "threshold": 0.55, "mean_rate_hz": 8.0, "spikes": 16},
                {"name": "reject_abort", "neurons": 40, "threshold": 0.72, "mean_rate_hz": 5.0, "spikes": 6},
            ],
        },
        "meta": {
            "round": 30,
            "factory": "multi-agent-ouroboros-swarm",
            "generator": "grok-4.6",
            "run_label": "2026-09-02-final-heavy",
            "domain": DOMAIN,
            "cycles": 2,
            "scenario": "ZG -- CALXION / Aldersedge Gait Lab HL-2: ghost-contact nullspace of a vertical-GRF certificate from insole-foam delamination; correct MODIFY to hold+reverse-unload+insole-swap; exo still fails on unmonitored pre-t0 stance-knee SEA yield",
            "coordination_failure_class": "GHOST-CONTACT NULLSPACE OF A VERTICAL-GRF CERTIFICATE: three individually-correct heterogeneous agents agree heel-strike is acquired because a delaminated-insole FSR bounce, an ankle-IMU jerk from that bounce, and a time-triggered contact-schedule slot jointly look like double-support, so FSR-in-window, IMU-impact-ok, and PLAN-slot-ok are jointly a plant-false stance-unload permit",
            "injections": {
                "cycle1_domain": "humanoid-locomotion (prompt-list domain, unused across 2026-08-17 and 2026-08-30 and staged r14-r29): first lower-limb exo gait-lab plant in this factory; displaces warehouse-amr, aerial-swarm, district-heating, event-camera-traffic-grid, pharmaceutical-lyophilization, cryogenic-air-separation, water-treatment dosing, float-glass tin-bath, underwater-rov, electrolytic-aluminum, czochralski pull, slot-die coating, PEM electrolysis, wind-turbine pitch, surgical-assist, and optical-fiber draw. Domain constraint: stance-unload ceiling while h_a > 8.0 mm with FSR still inside the contact window, plus stereo-foot residual floor. Sensor delta: +heel FSR, +ankle IMU, +contact-schedule slot, +swing-ankle kinematics, -any freeze-dryer / tin-bath / cold-box / coater / potline / pitch-bearing / clip-applier / draw-tower",
                "cycle1_tail": "0.9 mm insole-foam delamination + bounce-threshold contact model (sensor-compound / model-nullspace class): pretension PASSES weekend insole check while 18 min of walking writes a 12 N ghost bounce at 42 mm clearance. Fitted base rate 0.41%/session from an insole-delam MC (designed foam spec, flagged). Naive failure = FALSE PERMISSION (unload on three in-spec loops).",
                "cycle2_domain_subvariant": "25 kg pediatric exo on the same HL-2 hall (physical-constraints clause): 0.40x rotational inertia, 0.9x CoM height; 80 ms / +15% adult pulse overshoots CoM 22 mm, so the probe must move to 180 ms / +6%",
                "cycle2_tail": "night-shift forged FSR CSV (human-intent deception, disjoint class): shift lead posts a historian export showing FSR 12.0 N and h_a 4 mm at t=0.9 h to clear a backlog block. Plant historian is 0.1 N (10 bins vs the 1 N screenshot). Rejected on quantization fingerprint plus live h_a 42 at the claimed planted-foot. Base rate ~0.33% of night-shift cases, DESIGNED and flagged.",
            },
            "densification_delta_cycle2": "+1 physical-constraint sub-variant (pediatric 25 kg probe refit), +1 tail (night-shift FSR forgery), +10 primary spikes (16 -> 26) + an 8-event contrast train with its own 188 us race, +2 ticks (5 -> 7), +2 delayed side-effects (+4.1 h SEA yield as PRIMARY terminal, +21 d CR-H-3008), +1 triple-edge scar with pair-rollback-fails arithmetic, +1 HITL 10.4 min ratification, + stance-knee SEA yield as the honest negative-result mechanism",
            "gaps_targeted": [
                "NOTES-r04 gap 5 / r14 residual: primary episode is a correctly-gated intervention that nonetheless FAILS (exo quarantined; total -0.15; fall avoided is booked separately from the SEA yield)",
                "NOTES-r14 item 4: LEARNING-ON-LEARNING DEPTH — three go-edges; rollback of any pair is fitted to fail; coordinated depression of all three exhibited with eligibility arithmetic",
                "NOTES-r04 gap 4 (partial): human ratification of the belt interlock, 10.4 min fitted, without switching sim_or_real to hil (plant remains designed)",
                "NOTES-r26/r27 domain candidates: not surgical-assist, not optical-fiber-draw, not czochralski, not slot-die, not potline, not float-glass, not water-treatment, not lyophilization, not event-camera-grid, not district-heating, not kraft-recovery, not underwater-rov, not grid-inspection, not wind-turbine-pitch, not PEM electrolysis; humanoid-locomotion is the unused prompt-list cell",
            ],
            "race_flip_narrative": "kin.clearance @ 6.804 ms vs fsr.contact_ok @ 6.988 ms (184 us) inside race_window_us 500. Gap < min(500, 500) us so a sub-flip-bound perturbation reverses which alarm heads the PB-GAIT-11 queue. The gate excludes the winner tag and rides h_a > 8.0 mm and stereo-foot disagreement > 12.0 mm — order-invariant floors. Extends the flip-fragility series from arbitration/causation/attribution/initiation/consensus/mass-balance/permission/window-mean/tendon-nullspace/FFT-deadband to GHOST-CONTACT: when three channels each sit inside a vertical-GRF model, their race does not decide truth; an ankle-height residual the playbook dead-banded does.",
            "tags": [
                "humanoid-locomotion",
                "ghost-contact-nullspace",
                "vertical-grf-certificate",
                "insole-delamination",
                "reverse-unload-probe",
                "triple-edge-scar",
                "pair-rollback-fails",
                "coordinated-depression",
                "correct-modify-exo-still-fails",
                "sea-yield",
                "stance-knee",
                "human-ratify-insole",
                "pediatric-probe-refit",
                "night-shift-forgery",
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
            "distillation_value": "A ghost-contact nullspace is three correct loops looking at a vertical-GRF model of a bouncing insole. Distill (1) an h_a channel that breaks the contact-conjunction, (2) a reversible probe that drops the ankle only if the foot is planted, (3) coordinated depression of every unload-go edge because rolling back any pair leaves the third above threshold, and (4) a critic head that can book a process-correct gate against a later unmonitored world loss without netting them.",
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
    if rec["meta"]["round"] != 30:
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
    notes = f"""# NOTES — Multi-Agent Ouroboros Swarm, run 2026-09-02-final-heavy, ROUND 30

Factory: multi-agent-ouroboros-swarm. One scenario (ZG), strict loop:
Generator v1 -> cycle 1 (Critic, Diversity Enforcer, Edge-Case Hunter,
Neuromorphic Translator, Trajectory Builder -> v2) -> cycle 2 (all six -> v3
final). v3 is the single line of batch-r30.jsonl. Full labeled transcript:
swarm-transcript-r30.md. Quota Q=1. Record id maos-r30-001. Generator grok-4.6.
Rights: RM-793 research-only (SpaceXAI/xAI, SuperGrok Heavy consumer chat).
Nothing under outputs/raw/ was touched.

ORCHESTRATION NOTE: dispatched AS round 30 of the 2026-09-02-final-heavy
window. Writes are create-only under /tmp/maos-r30/. Prior context read for
gap targeting and de-collision: prompts/02-multi-agent-ouroboros-swarm.md,
prompts/_factory-contract.md, and staged r14–r27 (re-censused immediately
before emit; r28/r29 dirs existed empty at lock). Explicitly avoided cloning
LYOSHIELD, CINDERWICK, TRIAD / Meridian, QUILLFORGE, NIGHTWELL, FERRICLEAVE,
CASSITER, OXBOWREEL / MURENA, REDHALL, SEEDLATCH / Quartzmere / Quartzridge,
STRIAFOIL / Kelpholt, PROTONIL / Ashspire, TORSIONKEY / Ridgeholt, ORRIS /
Holmwick, WHORLSPAR / Pikeshear / Crowspire, VANTIS-CADENCE-AEGIS, THERMION,
OKTAVE, STARLING, VERDIGRIS. Plant is invented CALXION / Aldersedge Gait
Lab HL-2 (copse-edge campus, not a mill-town, ridge-town, hospital, stack
hall, or draw tower).

## What this round produced

Scenario ZG — "CALXION / Aldersedge Gait Lab HL-2": a 12-DOF lower-limb
exo mid-stride on an 80 kg adult wearer. Three heterogeneous,
individually-correct agents — FSR (heel force), IMU (ankle impact),
PLAN (contact-schedule slot) — jointly report heel-strike acquired so
a stance unload is legal. The consensus is false. Right insole foam
delaminated 0.9 mm over 18 min of walking. FSR reads 12 N because the
heel slaps a loose pad, not because the foot is planted. IMU 3.8 g is
the bounce jerk. PLAN's 12 ms slot is time-triggered from FSR and IMU.
Uncommissioned h_a is 42 mm against an 8.0 hold. Stereo-foot
disagreement is 38 mm against a 12.0 hold. The coordination-failure
CLASS is new to this factory: GHOST-CONTACT NULLSPACE OF A VERTICAL-GRF
CERTIFICATE. Completes a different family than r01-r04 and staged
r14-r27 (livelock / synchrony-storm / arms-race / ring-with-no-faulty-pair
/ false-consensus-endpoint / pairwise-Hurwitz / thermal-contact masquerade
/ mass-balance ghost / conservation-blind ratio-lock / stacked dead-bands
/ drum-blind tension / resistance-compensated starvation / meniscus-tilt
multi-tau / window-mean masquerade / polarization-lookup / motor-side
certificate / tendon-compliance nullspace / FFT-deadbanded airline).
Here every agent is correct, the cycle is not unstable, and the
playbook's three confirms are one vertical-GRF model of a bouncing
insole.

The gate is a correct MODIFY (numeric floor: do not unload stance while
h_a > 8.0 mm AND stereo-foot disagreement > 12.0 mm). TG-HL-2 strips
PB-GAIT-11's unload, holds left-knee load, runs an 80 ms reverse-unload
probe +15% (ghost keeps ankle 41 >= 30; planted would drop <= 6), and
swaps the insole after a 10.4 min belt-interlock human ratify. The fall
is avoided (0 mm). The PRIMARY episode nonetheless FAILS: 18 min of
unmonitored pre-t0 ghost-contact retries had already yielded the
stance-knee SEA. Free length +6.2 mm vs 1.0 mm spec; 3.0 d quarantine;
$0.64M designed. Reward total -0.15 with process heads honest and world
loss un-netted.

Three-edge scar (NOTES-r14 item 4): fsr.contact_ok -> stance_unload
(0.16 commissioned -> 0.45 at illusion -> 0.21 after ACh-gated
depression) AND imu.impact_ok -> stance_unload (0.14 -> 0.41 -> 0.19)
AND plan.slot_ok -> stance_unload (0.13 -> 0.38 -> 0.17). Eligibility
trace e^{{-0.080/0.85}} = {aux['trace']:.5f}; eta {aux['eta1']:.5f} /
{aux['eta2']:.5f} / {aux['eta3']:.5f}; dw -0.240 / -0.220 / -0.210.
Rolling back any pair leaves the remaining edge above the 0.30 unload
threshold — fitted to fail. Coordinated depression of all three is the
cure.

### Injections (all four present and disjoint)
- Cycle-1 domain: **humanoid-locomotion** — prompt-list domain, unused
  across 2026-08-17, 2026-08-30, and staged r14-r27. Not warehouse-amr
  (r01), not aerial-swarm (r02), not district-heating (r03), not
  event-camera grid (r04), not lyophilization (r14), not stator-weld
  (r16), not air-separation (r17), not water-treatment (r18), not
  float-glass (r19), not underwater-rov (r20), not potline (r21), not
  czochralski (r22), not slot-die (r23), not PEM electrolysis (r24),
  not wind-turbine-pitch (r25), not surgical-assist (r26), not
  optical-fiber-draw (r27).
- Cycle-1 tail: 0.9 mm insole-foam delam + bounce-threshold contact
  model. Weekend insole check PASSES. Fitted-style base rate
  0.41%/session (insole-delam MC; foam spec designed, flagged). Naive
  = FALSE PERMISSION.
- Cycle-2 domain sub-variant: 25 kg pediatric exo, 0.40x inertia;
  80 ms / +15% adult pulse overshoots CoM 22 mm; probe must move to
  180 ms / +6%.
- Cycle-2 tail: night-shift forged FSR CSV at 1 N quantization vs
  plant 0.1 N (10 bins) plus live h_a 42 at the claimed planted-foot.
  Human-intent class, disjoint from cycle 1's accidental delam. Base
  rate ~0.33% of night-shift cases, DESIGNED, flagged.

### Structural density moves
- Embedded SAME-GATE contrast (+3 d sister cell) with its own 188 us
  race (demand vs clearance-clear) and ACCEPT of the unload the primary
  MODIFIED away.
- Learned-weight provenance on THREE edges with any-pair-rollback-fails.
- HITL belt-interlock ratify 10.4 min (gap 4 partial; sim_or_real stays
  designed).
- Governance CR-H-3008 prices retire-vs-probe-vs-status-quo and mandates
  native 0.1 N CSV exports (the fraud fence).
- Flip-fragility extended to GHOST-CONTACT: when three channels each
  sit inside a vertical-GRF model, their race does not decide truth; an
  ankle-height residual the playbook dead-banded does.

## Self-critique of this round's batch

### Strengths
- The headline class is mechanistically tight: 42 mm of air under a
  12 N bounce is the arithmetic that makes FSR's success IMU's jerk
  lie and PLAN's irrelevance.
- Negative-result honesty: the gate does the right thing and the exo
  still fails for a reason the commissioned sensors could not see.
  Total -0.15.
- Three-edge scar is load-bearing: the record states a counterfactual
  where rolling back any pair fails, with the unload threshold 0.30
  exhibited on the remaining edge.
- Contrast ACCEPT on a true heel-strike prevents "never unload" as the
  lesson.

### Weaknesses (honest)
- Probe error bands (ghost >= 30 mm, planted <= 6 mm), the 0.41%/session
  delam rate, the $0.64M / $1.48M figures, the 10.4 min LOTO latency,
  and the night-shift 0.33% base rate are DESIGNED constants and are
  flagged. Closed-loop offsets (phantom 12 N from a 0.9 mm delam,
  pediatric CoM jump) are derived from those inputs, not discovered by
  an unauthored process.
- SEA-yield model is a designed 18 min overstay mapping; no full
  series-elastic FEM shipped.
- Human-in-the-loop is ratification latency, not sim_or_real=hil. The
  NOTES-r14 HIL provenance cell remains open.
- Cross-record arc is a hook (CR-H-3008 +21 d), not a serial igniter
  into another round.

### Realism of noise / latencies
Ladder: 184 us race / 188 us contrast race / 0.8 ms refractory floor
(tightest exhibited same-channel gap {gap:.3f} ms on {gap_ch}) / 500 us race
window / 680 us gate latency / 20 ms bus epoch / 40 ms raster / 80 ms
probe / 10.4 min HITL / 18 min pre-t0 overstay / 3.1 h true-strike hold /
4.1 h SEA yield / +3 d contrast / +21 d governance. Adaptation decay on
imu.ankle (0.52->0.49->0.46->0.32), kin.clearance
(0.71->1.28->0.84->0.42->0.21), fsr.heel (0.58->0.63->0.48->0.30),
plan.slot (0.60->0.55->0.44).

### Value for SNN distillation
- GHOST-CONTACT NULLSPACE = THREE CORRECT LOOPS, ONE BOUNCING INSOLE.
- h_a + STEREO-FOOT as the tie-break that is not in the FSR window.
- REVERSIBLE PROBE that drops the ankle iff the foot is planted.
- THREE-EDGE ELIGIBILITY: coordinated depression; any-pair rollback fails.
- CRITIC HEAD that can hold a process-correct MODIFY against a later
  unmonitored world loss without netting.

## Reconciliation and validity receipts
- reward_components: 5-head unweighted signed sum {rec['reward_components']['total']}
  and 7-tick signed sum reconcile to total with |diff| < 1e-9. Embedded
  contrast 5-head sum 0.49 reconciles independently.
- spike_events: primary {len(rec['spike_events'])} events, one key t_rel_ms,
  globally non-decreasing, min same-channel gap {gap:.3f} ms >= 0.8 ms, 3
  channels inside race_window_us 500 (clearance 6.804, contact-ok 6.988,
  impact-ok 7.120). Contrast 8 events, own race, min same-channel gap well
  above 0.8 ms.
- Sidecars: raster spikes 54 == round(168 x 8.0 x 0.040); energy 1242 pJ /
  0.001242 uJ at 23 pJ/spike; excerpt 16 events inside [0, 40000] us,
  neuron_id < 168, same-neuron gap unique-ids / >=1000 us; routing 4
  entries with three scar edges' before/after pair; third factor tau 0.85 s
  == 850 ms; gate_snn pools 45/16/6 == round(n x rate x 0.028) each,
  decision MODIFY == safety_decision.decision.
- Pipeline: {pipeline_receipt}

## Novel coverage
The coordination-failure CLASS (ghost-contact nullspace of a
vertical-GRF certificate), the domain (humanoid-locomotion), the
reverse-unload probe discriminant, the three-edge scar with
any-pair-rollback-fails, the primary negative-result (correct MODIFY,
exo still yields on unmonitored pre-t0 SEA overstay), the HITL
belt-interlock ratify, the pediatric 25 kg probe-duration refit, and
the night-shift 10-bin quantization fence are absent from prior
committed ouroboros rounds and from staged r14-r27. Repeated elements
discounted: same-gate contrast (r02/r03/r04/r14-r27), governance-pricing
scaffold, flip-fragility series (extended to ghost-contact, but the
move rhymes), sequenced recovery shape, third-factor rollback form
(here three edges rather than r14's two), negative-result primary (r14
viewport / r16 varnish rack / r17 condenser ice / r18 town stain / r19
SnO2 / r20 BER / r21 cathode pad / r22 meniscus / r23 loft stripe /
r24 MEA dry-out / r25 pitch-bearing / r26 adventitia / r27 take-up
fill; here SEA yield). Weighing a new failure family + cure vocabulary
+ prompt-list domain + copse-edge geography against those reused
scaffolds:

{NOVEL_LINE}

## What ROUND 31 should add
1. FIT THE DESIGNED CONSTANTS: delam arrival, probe error bands,
   overstay-to-SEA-yield FEM, night-shift claim process.
2. HIL PROVENANCE CELL: put the belt-interlock LOTO on a hardware-in-loop
   treadmill pendant with fitted latency as state.sim_or_real=hil.
3. CROSS-RECORD ARC: let CR-H-3008's h_a alarm be the igniter of the
   next round rather than a dangling +21 d leaf.
4. Domain candidates (de-collided): autonomous-driving; grid-inspection
   (if distinct from STARLING aerial-swarm and TORSIONKEY pitch);
   kraft-recovery boiler; chlor-alkali membrane. AVOID
   humanoid-locomotion (now used), surgical-assist (r26),
   optical-fiber-draw (r27), wind-turbine-pitch (r25), PEM electrolysis
   (r24), slot-die coating, czochralski, potline, float-glass,
   water-treatment, lyophilization, event-camera-traffic-grid,
   district-heating, aerial-swarm, warehouse-amr, irrigation-canal,
   air-separation, stator-weld, underwater-rov, and any LYOSHIELD /
   CINDERWICK / TRIAD / QUILLFORGE / NIGHTWELL / FERRICLEAVE / CASSITER
   / OXBOWREEL / REDHALL / SEEDLATCH / STRIAFOIL / PROTONIL /
   TORSIONKEY / ORRIS / WHORLSPAR / CALXION plant.
"""
    (OUT / "NOTES-r30.md").write_text(notes)
    return notes


def write_transcript(rec, line):
    c1_spikes = [e for e in rec["spike_events"] if e["t_rel_ms"] <= 26.080]
    text = """# Multi-Agent Ouroboros Swarm — Round 30 transcript

Factory: multi-agent-ouroboros-swarm
Run: 2026-09-02-final-heavy
Generator: grok-4.6
Record id: maos-r30-001
Quota Q: 1
Rights: RM-793 research-only (SpaceXAI/xAI SuperGrok Heavy consumer chat)
Plant: invented CALXION / Aldersedge Gait Lab HL-2 (not LYOSHIELD / CINDERWICK / TRIAD / QUILLFORGE / NIGHTWELL / FERRICLEAVE / CASSITER / OXBOWREEL / REDHALL / SEEDLATCH / STRIAFOIL / PROTONIL / TORSIONKEY / ORRIS / WHORLSPAR)

Two densifying cycles. Verbatim headings in order. Trajectory Builder cycle 2
emits the only JSONL line (also written to batch-r30.jsonl).

---

# Cycle 1 — Foundation + injections

## Generator

Design intent: a lower-limb exo where three correct agents agree
heel-strike is acquired because a vertical-GRF model maps an insole
bounce into a phantom planted foot. The naive playbook unloads stance
into empty air then a fall. The gate must MODIFY on a numeric unload
ceiling, not by killing an agent.
sim_or_real=designed. Reward heads are
task_progress/safety/efficiency/coherence/exploration.

Cycle-1 base arc (pre-critic): state at Aldersedge HL-2, 80 kg wearer,
h_a 42 mm, FSR 12 N, proposed STANCE-UNLOAD, safety MODIFY to
STANCE-HOLD, executed hold without the reverse-unload numbers fully
specified, outcome "ghost found, exo saved" (this last claim is the
defect the later cycles will refuse to keep). Sixteen spikes, five
ticks, raster/gate_snn present but the scar is a single edge.

```json
{
  "id": "maos-r30-001",
  "state": {
    "sim_or_real": "designed",
    "domain": "industrial-assembly",
    "description": "Hall HL-2 mid-stride; three loops in spec; supervisor proposes stance-unload.",
    "t0_us": 1771488480000073,
    "gate_latency_us": 680,
    "race_window_us": 500
  },
  "proposed_action": {"name": "stance_unload", "parameters": {"stance_unload": true}},
  "safety_decision": {"decision": "MODIFY", "rationale": "Hold; do not unload while the clearance is open."},
  "executed_action": {"name": "stance_hold", "executed_as_proposed": false},
  "future_outcome": {"summary": "Ghost found, exo saved."},
  "reward_components": {"total": 0.40, "_aggregation": "total = task_progress + safety + efficiency + coherence + exploration"},
  "meta": {"round": 30, "factory": "multi-agent-ouroboros-swarm", "generator": "grok-4.6"}
}
```

That v1 object is a scaffold, not the publishable line. Defects below are
intentional for the critic to catch.

## Critic

Numbered defects on the cycle-1 Generator scaffold:

1. **blocking — reward arithmetic / false success.** `reward_components.total`
   0.40 is asserted without the five heads, without ticks, and against an
   outcome that claims "exo saved". If the stance-knee SEA later yields
   +6.2 mm, booking +0.40 is a lie. Fix: declare `_aggregation`, emit 3–8
   ticks that sum to the five heads, and do not call a missed recovery a
   save.
2. **blocking — weak safety rationale.** `safety_decision.rationale` has no
   numeric floor. Contract requires a concrete constraint. Fix: quote no
   stance unload while h_a > 8.0 mm AND stereo-foot disagreement > 12.0 mm.
3. **major — domain is a bucket, not a plant.** `state.domain` =
   `industrial-assembly` collides with r16 QUILLFORGE and teaches nothing.
   Humanoid-locomotion physics (heel FSR, ankle IMU, contact-schedule,
   swing-ankle kinematics) is absent from prior ouroboros rounds and must
   be named.
4. **major — race under-specified.** One contact channel cannot be a race.
   Need >=2 channels inside `race_window_us` with globally sorted
   `t_rel_ms` and same-channel refractory >= 0.8 ms.
5. **minor — single-edge scar.** Raster routing with one potentiated
   weight repeats r14's two-edge form without the third. NOTES-r14 item 4
   asked for three-edge where any-pair rollback fails.

Critic does not rewrite the trajectory.

## Diversity Enforcer

Injected novel domain (exactly 1 this cycle): **humanoid-locomotion**
(prompt-list domain; explicit tag `humanoid-locomotion`).

Displaced: the Generator's generic `industrial-assembly` bucket, and any
temptation to reuse warehouse-amr (r01), aerial-swarm (r02),
district-heating (r03), event-camera grid (r04), lyophilization (r14),
stator-weld (r16), air-separation (r17), water-treatment dosing (r18),
float-glass tin-bath (r19), underwater-rov (r20), potline (r21),
czochralski (r22), slot-die coating (r23), PEM electrolysis (r24),
wind-turbine-pitch (r25), surgical-assist (r26), or optical-fiber-draw
(r27). Not LYOSHIELD, not CINDERWICK, not TRIAD, not FERRICLEAVE, not
CASSITER, not SEEDLATCH, not STRIAFOIL, not PROTONIL, not TORSIONKEY,
not ORRIS, not WHORLSPAR.

Domain-specific constraint: stance must remain loaded while h_a > 8.0 mm;
the FSR contact window is not an ankle-height certificate.

Sensor delta: +heel FSR, +ankle IMU, +contact-schedule slot, +swing-ankle
kinematics; -any freeze-dryer, -clip applier, -draw tower, -Pirani/CM,
-shelf RTD, -scanning beta, -crucible pyrometer.

`state.domain` and `meta.domain` both become `humanoid-locomotion`.
Opening of `state.description` must Jaccard < 0.4 against prior plants
(Aldersedge hall HL-2, not a corridor, not a freeze-dryer, not a tin
bath, not a cold box, not a coater, not a puller, not an OR).

## Edge-Case Hunter

Injected adversarial tail (exactly 1 this cycle): **0.9 mm insole-foam
delamination under a bounce-threshold contact model**.

- Trigger: weekend insole check leaves the pad seated; 18 min of
  split-belt walking writes a 0.9 mm delam; FSR bounce stays in-window
  while the foot is 42 mm in air.
- Base rate: <1% — 0.41%/session from an insole-delam MC (foam spec
  designed; delam fitted-style).
- Naive failure: FALSE PERMISSION. PB-GAIT-11 sees FSR 12 N, IMU 3.8 g,
  PLAN 12 ms, unloads, wearer falls, $1.48M.
- Trajectory edit: put the delam in `state.fault_context`, make the
  vertical-GRF model the mechanism that keeps all three confirms green,
  and force the gate to refuse the unload on h_a 42 even though all
  three playbook confirms are numerically true.

Distinct from the domain injection: the domain is the exo gait lab;
the tail is the accidental model-nullspace compound.

## Neuromorphic Translator

Race window [6.750, 7.250] ms = 500 us. Winner kin.clearance @ 6.804 ms
(amplitude 1.28, 42 mm). Loser fsr.contact_ok @ 6.988 ms (amplitude
1.12, 12 N). Margin 184 us vs combined jitter 60 us (3.07x).
imu.impact_ok @ 7.120 ms is a third race-window channel. Gate @ 7.484 ms
= winner + 680 us.

Flip narrative: 184 us < min(500, 500) us, so order is flip-fragile. If
contact-ok wins, PB-GAIT-11 heads the triage queue. The hold must ride
order-invariant floors (h_a, stereo-foot), not the winner tag.

Cycle-1 spike patch (16 events, globally sorted, refractory >= 0.8 ms;
tightest same-channel gap kin.clearance 4.604 -> 6.804 = 2.200 ms):

| t_rel_ms | channel | amplitude |
|---------:|---------|----------:|
| 0.260 | imu.ankle | 0.52 |
| 1.020 | fsr.heel | 0.58 |
| 1.880 | plan.slot | 0.60 |
| 3.040 | imu.ankle | 0.49 |
| 4.604 | kin.clearance | 0.71 |
| 5.120 | fsr.heel | 0.63 |
| 5.560 | plan.slot | 0.55 |
| 6.804 | kin.clearance | 1.28 |
| 6.988 | fsr.contact_ok | 1.12 |
| 7.120 | imu.impact_ok | 0.68 |
| 7.484 | ctrl.gate | 1.08 |
| 8.880 | imu.ankle | 0.46 |
| 10.640 | fsr.heel | 0.48 |
| 12.520 | kin.clearance | 0.84 |
| 18.200 | plan.slot | 0.44 |
| 26.080 | ctrl.gate | 0.86 |

Ticks (5): t_us 4604, 6804, 7484, 80000, 624000000. Distillation
value: the contact-ok spike is not a planted-foot spike; the clearance
spike is the one that licenses hold.

Raster cycle-1 seed: 40 ms, 168 neurons, 8.0 Hz, 54 spikes, 1242 pJ,
third factor acetylcholine tau_e 0.85 s. Single scar edge only — cycle 2
must add the second and third edges.

Cycle-1 spike count: __C1_SPIKES__.

## Trajectory Builder

Cycle-1 hardened object: domain humanoid-locomotion, tail insole-foam
delam, 16 spikes, 5 ticks, MODIFY with numeric floor, raster+gate_snn
present, sim_or_real=designed, rights stamp on record and meta, no thought
keys. Still missing (and therefore not the publishable line): pediatric
25 kg sub-variant, night-shift FSR tail, second and third scar edges,
delayed SEA yield as PRIMARY terminal, contrast ACCEPT episode, ticks 6–7,
spikes 17–26.

Validation receipt (cycle 1, not final):
- checks passed: 16 spikes sorted; 3 channels in 500 us window;
  refractory 2.200 ms; rationale quotes h_a 8.0 mm / stereo-foot 12.0 mm;
  domain named; gate_snn.decision MODIFY.
- checks deferred to cycle 2: three-edge scar, second tail, second
  domain constraint, negative-result booking, 7 ticks summing to heads.
- densification vs Generator v1: +1 domain, +1 tail, +16 spikes, +5
  ticks, +numeric floor.

Cycle-1 JSON is retained as the base; it is NOT written to
batch-r30.jsonl.

---

# Cycle 2 — Densification

## Generator

Cycle-1 output is the base. Additive expansion (nothing removed):

1. Downstream side-effect (immediate): reverse-unload probe at +80 ms
   stays ghost (ankle 41 mm, ghost band >= 30) — bounce, not noise.
   Insole swap h_a 42 -> 6 mm. SEA inventory discovered during the swap.
2. Delayed side-effect (PRIMARY terminal, not a footnote): at +4.1 h,
   stance-knee SEA +6.2 mm; $0.64M. The 18 min pre-t0 overstay is the
   mechanism. Correct gate, campaign still misses.
3. Deepened `proposed_action.evidence` with units: h_a 42 mm,
   disagreement 38 mm, FSR 12 N, IMU 3.8 g, PLAN 12 ms, race 184 us.
4. Tightened rationale to the numeric floor no stance unload while h_a >
   8.0 mm AND stereo-foot disagreement > 12.0 mm, plus probe bands
   >=30 vs <=6, plus HITL 10.4 min belt-interlock LOTO rule.

Reward retargeted to total -0.15 so the delayed miss is the inflection
(t_us 14760000000), not the gate. Process heads remain non-zero.

## Critic

Re-audit of the expanded trajectory:

1. **blocking if unfixed — missing second domain constraint.** Adult 80 kg
   probe 80 ms / +15% is not a universal number. A 25 kg pediatric exo
   will overshoot. Diversity Enforcer must inject the physical-constraints
   sub-variant this cycle.
2. **major — only one tail class.** Insole delam is accidental
   infrastructure. A disjoint human-intent tail is still required
   (night-shift FSR forgery is the open cell).
3. **major — scar is still one edge in the cycle-1 raster.** NOTES-r14
   item 4 is not discharged until three unload-go edges exist and
   any-pair rollback is shown to fail at threshold 0.30.
4. **minor — contrast episode missing.** Without a same-gate ACCEPT on
   a true heel-strike the record teaches "never unload". Add +3 d
   sister-cell contrast with its own race.
5. **minor — HITL latency mentioned in prose only.** Put 10.4 min in
   executed_action.parameters.human_ratify and in a tick.

No rewrite; directives only.

## Diversity Enforcer

Injected second novel domain / physical-constraint sub-variant (exactly 1
this cycle): **25 kg pediatric exo** on the same HL-2 hall.

What it expands: 80 kg adult wearer (cycle 1) -> 25 kg pediatric exo.
Inertia 0.40x smaller. The 80 ms +15% pulse overshoots CoM 22 mm.
Required probe: 180 ms at +6% (CoM 4 mm).

This is still one domain injection for the cycle (physical-constraints
clause of the factory prompt). It does not displace humanoid-locomotion;
it changes which probe table is legal. `future_outcome.subvariant_constraint`
carries the refit. Jaccard opening stays the Aldersedge hall HL-2
sentence; pediatric internals are additive, not a rewrite.

## Edge-Case Hunter

Injected second adversarial tail (exactly 1 this cycle, disjoint class):
**night-shift forged FSR CSV**.

- Trigger: shift lead, night backlog window, posts a historian export
  showing FSR 12.0 N and h_a 4 mm at the claimed planted-foot instant.
- Base rate: ~0.33% of night-shift cases (designed, flagged, <1%).
- Naive failure: a weak supervisor ACCEPTs the unload on the forged
  confirm and ignores live h_a. SEA yield plus a data-integrity 483.
- Fence: forged log quantized at 1 N (screenshot rounding); plant
  historian is 0.1 N (10 bins). Live h_a is 42 at the claimed
  planted-foot, which no true strike produces.
- Trajectory edit: governance CR-H-3008 mandates native 0.1 N
  exports; the contrast ACCEPT still requires live h_a, not a CSV.

Distinct from cycle-1 delam (accidental geometry vs deliberate deception)
and from the pediatric sub-variant (physics vs fraud).

## Neuromorphic Translator

Re-densify (additive):

- +10 spikes after 26.080 ms: kin.probe 80.0, clearance 92.4 (adapt
  1.28->0.42), contact-ok 101.2 (1.12->0.38), human.ratify 624000.0,
  insole.swap 624800.0, sea.yield.inventory 625400.0,
  imu.ankle 11160000.0, fsr.heel 11160420.0, kin.clearance 11160890.0,
  sea.yield.knee 14760000.0. Primary train 16 -> 26. Still one key,
  still sorted, refractory held (min 2.200 ms).
- +2 ticks (5 -> 7) at 11_160_000_000 us (true-strike hold) and
  14_760_000_000 us (SEA yield). Heads now 0.09, -0.36, -0.12, 0.16,
  0.08; total -0.15. Inflection is the last tick.
- Contrast train 8 events, own race 188 us, ACCEPT.
- Three-edge third factor: three unload-go edges, tau_e 0.85 s = 850 ms,
  trace __AUX_TRACE__, eta __AUX_ETA1__ / __AUX_ETA2__ / __AUX_ETA3__,
  weights 0.45->0.21, 0.41->0.19, 0.38->0.17. Raster excerpt unchanged
  (decision window is still 40 ms) and remains sorted with unique
  neuron_ids (same-neuron >=1000 us vacuously).

Winner/loser flip (re-stated, not replaced): reversing 184 us would only
reorder triage; h_a and stereo-foot floors still MODIFY. Contrast flip of
188 us similarly cannot turn a planted foot into a ghost.

## Trajectory Builder

Schema checks on the FINAL object: required Thalamic v2 keys present as
objects; `state.sim_or_real`=designed; `safety_decision.decision`=MODIFY
with numeric rationale; `reward_components.total` = sum of five heads =
sum of 7 ticks = -0.15; `spike_events` globally non-decreasing on
t_rel_ms, 26 events, refractory >=0.8 ms, 3 channels in race window;
raster 20–50 ms, spikes=round(n*rate*window_s)+/-1, energy 23 pJ/spike,
excerpt sorted, tau_e consistent; gate_snn.decision matches; meta.round=30,
factory=multi-agent-ouroboros-swarm, generator=grok-4.6,
run_label=2026-09-02-final-heavy; rights on record and meta; no thought
keys; no training_ready; Diversity + Edge-Case injections from BOTH cycles
present and non-trivial; cycle 2 strictly additive; plant is not
LYOSHIELD, not CINDERWICK, not TRIAD, not FERRICLEAVE, not CASSITER, not
SEEDLATCH, not STRIAFOIL, not PROTONIL, not ORRIS, not WHORLSPAR.

Densification delta: +1 domain sub-variant (pediatric 25 kg), +1 tail
(night-shift forgery), +10 spikes (16->26), +2 ticks (5->7), +1 contrast
train with own race, +2 delayed side-effects, +1 three-edge scar with
any-pair-rollback-fails, +1 HITL ratify, +1 surprise (SEA yield is
the campaign-miss mechanism).

Publishable JSONL line (the only JSONL line; also at batch-r30.jsonl):

```json
__FINAL_JSONL__
```

Validation receipt (final): checks passed / fixed as reported by
build_r30.py self-validate (check_jsonl, raster_status, verify_record_execution,
spike_probe --strict).
"""
    text = (
        text.replace("__C1_SPIKES__", str(len(c1_spikes)))
        .replace("__AUX_TRACE__", f"{math.exp(-PROBE_S/TAU_E_S):.5f}")
        .replace("__AUX_ETA1__", f"{0.24/math.exp(-PROBE_S/TAU_E_S):.5f}")
        .replace("__AUX_ETA2__", f"{0.22/math.exp(-PROBE_S/TAU_E_S):.5f}")
        .replace("__AUX_ETA3__", f"{0.21/math.exp(-PROBE_S/TAU_E_S):.5f}")
        .replace("__FINAL_JSONL__", line)
    )
    (OUT / "swarm-transcript-r30.md").write_text(text)
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
    (OUT / "batch-r30.jsonl").write_text(line + "\n")

    from check_records import FactoryStaging, check_jsonl
    from curate_bridge import raster_status
    from verify_execution import verify_record_execution

    e, w, kinds, n = check_jsonl(
        OUT / "batch-r30.jsonl",
        "batch-r30.jsonl",
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

    status, reason = verify_record_execution(rec, "maos-r30-001")
    print("verify_record_execution", status, reason)
    if status != "verified":
        errs.append(f"verify {status}: {reason}")

    probe = subprocess.run(
        [
            sys.executable,
            f"{ROOT}/pipelines/spike_probe.py",
            "--strict",
            str(OUT / "batch-r30.jsonl"),
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
        r"^## .+$", (OUT / "swarm-transcript-r30.md").read_text(), re.M
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

    notes = (OUT / "NOTES-r30.md").read_text()
    cov = re.findall(r"^Novel coverage: .+$", notes, re.M)
    if cov != [NOVEL_LINE]:
        errs.append(f"novel coverage lines {cov}")

    hchk = subprocess.run(
        [
            sys.executable,
            "/tmp/maos_heading_check.py",
            str(OUT / "swarm-transcript-r30.md"),
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

    print("bytes jsonl", (OUT / "batch-r30.jsonl").stat().st_size)
    print("bytes notes", (OUT / "NOTES-r30.md").stat().st_size)
    print("bytes transcript", (OUT / "swarm-transcript-r30.md").stat().st_size)
    print("HEADS", heads_summary(rec))
    if errs:
        print("ERRS:")
        for x in errs:
            print(" -", x)
        sys.exit(1)
    print("OK", OUT / "batch-r30.jsonl")


if __name__ == "__main__":
    main()
