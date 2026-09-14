#!/usr/bin/env python3
"""Build and self-check MAOS round-26 JSONL (research-only; not published)."""
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

GEN_AT = "2026-09-02T23:50:00Z"
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
OUT = Path("/tmp/maos-r26")
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
    "training_ready",
    "da Vinci",
    "Intuitive Surgical",
)
R14_OPENING = (
    "Helixmere Biologics Building C lyophilizer LYO-4 is mid-primary on 8400 "
    "vials of a monoclonal antibody"
)
NOVEL_LINE = "Novel coverage: 48%"
PLANT = "ORRIS"
DOMAIN = "surgical-assist"
RECORD_ID = "maos-r26-001"


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
        if p.parent.name == "maos-r26":
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
    needles = {
        "domain": DOMAIN,
        "plant": PLANT,
        "geo": "Holmwick",
        "cell": "SA-3",
    }
    for p in sorted(Path("/tmp").glob("maos-r*/batch-r*.jsonl")):
        if p.parent.name == "maos-r26":
            continue
        try:
            rec = json.loads(p.read_text().splitlines()[0])
        except (OSError, json.JSONDecodeError, IndexError):
            continue
        blob = json.dumps(rec)
        domain = (rec.get("state") or {}).get("domain")
        site = ((rec.get("state") or {}).get("topology") or {}).get("site") or ""
        scenario = (rec.get("state") or {}).get("scenario_name") or ""
        if domain == DOMAIN:
            hits.append(f"{p}: domain {domain}")
        if PLANT in blob:
            hits.append(f"{p}: plant token {PLANT}")
        if "Holmwick" in blob:
            hits.append(f"{p}: geo Holmwick")
        if "surgical-assist" in (domain or "") and p.parent.name != "maos-r26":
            hits.append(f"{p}: surgical-assist domain")
        _ = needles, site, scenario
    return hits


def build_record():
    ticks, heads = cents_ticks(
        [4620, 6812, 7492, 800_000, 546_000_000, 11_520_000_000, 14_760_000_000],
        [
            (1, -2, -1, 1, 1),
            (2, -5, -1, 3, 1),
            (2, -6, -2, 4, 2),
            (2, -5, -2, 3, 1),
            (1, -6, -2, 2, 1),
            (0, -5, -2, 2, 1),
            (0, -6, -1, 0, 0),
        ],
    )
    assert abs(heads["total"] - (-0.16)) < 1e-9, heads

    trace = math.exp(-0.80 / 0.85)
    eta1 = 0.24 / trace
    eta2 = 0.22 / trace
    eta3 = 0.21 / trace
    dw1 = eta1 * 1.0 * trace
    dw2 = eta2 * 1.0 * trace
    dw3 = eta3 * 1.0 * trace
    w1 = 0.46 - dw1
    w2 = 0.42 - dw2
    w3 = 0.39 - dw3
    assert abs(w1 - 0.22) < 5e-4, w1
    assert abs(w2 - 0.20) < 5e-4, w2
    assert abs(w3 - 0.18) < 5e-4, w3

    spike_events = [
        {"channel": "vis.stereo", "t_rel_ms": 0.280, "amplitude": 0.54},
        {"channel": "kin.encoder", "t_rel_ms": 1.040, "amplitude": 0.61},
        {"channel": "hap.ft", "t_rel_ms": 1.920, "amplitude": 0.59},
        {"channel": "vis.stereo", "t_rel_ms": 3.100, "amplitude": 0.51},
        {"channel": "tendon.stretch", "t_rel_ms": 4.620, "amplitude": 0.73},
        {"channel": "hap.ft", "t_rel_ms": 5.080, "amplitude": 0.64},
        {"channel": "kin.encoder", "t_rel_ms": 5.540, "amplitude": 0.56},
        {"channel": "tendon.stretch", "t_rel_ms": 6.812, "amplitude": 1.26},
        {"channel": "hap.contact_ok", "t_rel_ms": 6.988, "amplitude": 1.14},
        {"channel": "vis.overlay_ok", "t_rel_ms": 7.140, "amplitude": 0.66},
        {"channel": "ctrl.gate", "t_rel_ms": 7.492, "amplitude": 1.06},
        {"channel": "vis.stereo", "t_rel_ms": 8.920, "amplitude": 0.48},
        {"channel": "hap.ft", "t_rel_ms": 10.780, "amplitude": 0.49},
        {"channel": "tendon.stretch", "t_rel_ms": 12.640, "amplitude": 0.86},
        {"channel": "kin.encoder", "t_rel_ms": 18.400, "amplitude": 0.47},
        {"channel": "ctrl.gate", "t_rel_ms": 26.200, "amplitude": 0.88},
        {"channel": "tendon.probe", "t_rel_ms": 800.0, "amplitude": 0.97},
        {"channel": "tendon.stretch", "t_rel_ms": 920.4, "amplitude": 0.44},
        {"channel": "hap.contact_ok", "t_rel_ms": 1010.2, "amplitude": 0.40},
        {"channel": "human.ratify", "t_rel_ms": 546000.0, "amplitude": 0.82},
        {"channel": "instrument.swap", "t_rel_ms": 546800.0, "amplitude": 0.74},
        {"channel": "adventitia.bruise.inventory", "t_rel_ms": 547400.0, "amplitude": 0.85},
        {"channel": "vis.stereo", "t_rel_ms": 11520000.0, "amplitude": 0.33},
        {"channel": "hap.ft", "t_rel_ms": 11520420.0, "amplitude": 0.31},
        {"channel": "tendon.stretch", "t_rel_ms": 11520890.0, "amplitude": 0.22},
        {"channel": "hematoma.adventitia", "t_rel_ms": 14760000.0, "amplitude": 0.92},
    ]

    contrast_spikes = [
        {"channel": "clip.demand", "t_rel_ms": 0.000, "amplitude": 0.88},
        {"channel": "tendon.stretch", "t_rel_ms": 0.196, "amplitude": 0.22},
        {"channel": "hap.contact_ok", "t_rel_ms": 0.410, "amplitude": 0.81},
        {"channel": "vis.stereo", "t_rel_ms": 1.620, "amplitude": 0.42},
        {"channel": "kin.encoder", "t_rel_ms": 4.880, "amplitude": 0.56},
        {"channel": "ctrl.gate", "t_rel_ms": 7.120, "amplitude": 0.94},
        {"channel": "tendon.probe", "t_rel_ms": 3200.0, "amplitude": 0.38},
        {"channel": "clip.seated", "t_rel_ms": 14760000.0, "amplitude": 0.14},
    ]

    excerpt = [
        {"t_us": 280, "neuron_id": 10},
        {"t_us": 1040, "neuron_id": 44},
        {"t_us": 1920, "neuron_id": 80},
        {"t_us": 3100, "neuron_id": 14},
        {"t_us": 4620, "neuron_id": 8},
        {"t_us": 5080, "neuron_id": 88},
        {"t_us": 5540, "neuron_id": 50},
        {"t_us": 6812, "neuron_id": 6},
        {"t_us": 6988, "neuron_id": 18},
        {"t_us": 7140, "neuron_id": 56},
        {"t_us": 7492, "neuron_id": 112},
        {"t_us": 8920, "neuron_id": 22},
        {"t_us": 10780, "neuron_id": 92},
        {"t_us": 12640, "neuron_id": 12},
        {"t_us": 18400, "neuron_id": 96},
        {"t_us": 26200, "neuron_id": 120},
    ]

    rec = {
        "id": RECORD_ID,
        "title": "ORRIS SA-3: tendon stretch 1.8 mm beats hap.contact-ok by 176 us; correct MODIFY still books a 4.1 h adventitia hematoma from pre-t0 cable creep",
        "rights": dict(RIGHTS),
        "state": {
            "sim_or_real": "designed",
            "domain": DOMAIN,
            "scenario_name": "ORRIS / Holmwick Surgical SA-3",
            "timestamp_local": "2026-04-11T02:18:00-05:00",
            "t0_us": 1775883480000041,
            "gate_latency_us": 680,
            "race_window_us": 480,
            "race_window_rel_ms": [6.76, 7.24],
            "description": "Holmwick Surgical Building 2 cell SA-3 is mid-clip on a 4.2 mm cystic-artery analogue when three heterogeneous, individually-correct agents jointly report 'clip site acquired, fire is legal'. VIS overlay sits on the vessel centroid (0.31 mm pixel error). KIN forward kinematics from joint encoders report 0.12 mm residual vs the CAD clip pose. HAP wrist F/T reads 3.2 N inside the 2.8-3.8 N tissue-contact window. The consensus is false: yellow tendon on arm-2 has crept 1.8 mm over 22 min of hold-at-force, so the actual jaws sit 1.8 mm short of the wall. VIS overlay uses encoder FK, not cable length. HAP nulls 3.2 N as tissue because the contact model assumes inextensible tendons; the newton is stretch, not adventitia. Uncommissioned tendon LVDT residual r_s is 1.8 mm against a 0.40 mm hold. Stereo-jaw disagreement (uncommissioned jaw-marker vs overlay) is 1.64 mm against a 0.60 mm hold. Stretch-first latches CLIP-HOLD plus a reverse-tension probe; contact-ok-first would have authorized FIRE-CLIP into empty space then a graze.",
            "goal": "Hold the 12 mm clip applier unfired while r_s > 0.40 mm AND stereo-jaw disagreement > 0.60 mm; keep analogue-wall clip-fire at 0 and hematoma volume <= 2 mL.",
            "race": {
                "contenders": [
                    "tendon.stretch 1.8 mm (uncommissioned LVDT residual)",
                    "hap.contact_ok 3.2 N (wrist F/T inside 2.8-3.8 N tissue window)",
                ],
                "semantics": "Stretch-first latches CLIP-HOLD + REVERSE-TENSION-PROBE + instrument swap. Contact-ok-first latches FIRE-CLIP (12 mm titanium clip, no probe).",
                "window_derivation": "480 us = one 360 us F/T ADC slot plus 120 us LVDT publish.",
                "order_evidence_note": "Margin 176 us vs combined jitter 58 us (LVDT 28 + F/T 30): 3.03x. The 176 us gap sits inside min(500, 480) us, so a sub-flip-bound perturbation reverses triage order. The gate rides the order-invariant floors r_s > 0.40 mm and stereo-jaw disagreement > 0.60 mm, not the alarm order.",
            },
            "topology": {
                "site": "Holmwick Surgical, invented hospital campus Holmwick, Building 2 cell SA-3: cable-driven 4-arm laparoscopic assistant, 8 mm Maryland-pattern grasper on arm-2 (yellow tendon pair), 12 mm clip applier on arm-3, box-trainer plus live-tissue analogue, 4.2 mm cystic-artery analogue, Grade-B OR",
                "agents": "VIS stereo vision (vendor Stereonest): tool-tip overlay from encoder FK. KIN joint kinematics (vendor Encodo): 7-DOF encoder FK. HAP wrist force/torque (vendor Forcemere): 6-axis F/T at the clip-applier wrist. Heterogeneous stacks, no shared tendon-length schema, one 20 ms pendant-bus epoch",
                "coupling": "Each agent's commissioned window hides a different slice of the same stretch. VIS is correct that the overlay sits on the vessel. KIN is correct that the joint chain matches CAD. HAP is correct that wrist force is 3.2 N. Playbook PB-CLIP-07 treats the conjunction of three in-spec loops as permission to fire. No agent is faulty; the 1.8 mm cable is a compliance the inextensible-tendon model cannot see.",
            },
            "sensors": [
                "stereo tool-tip overlay, 30 Hz, 22 us jitter, 0.31 mm pixel error (spec <= 0.50 mm on-vessel)",
                "tendon LVDT residual r_s is computable on the yellow pair and is NOT commissioned at t0 (1.8 mm observed in the historian after the fact)",
                "7-DOF joint encoders, 1 kHz, 18 us jitter, FK residual 0.12 mm vs CAD clip pose",
                "wrist 6-axis F/T, 1 kHz, 30 us jitter, 3.2 N (tissue window 2.8-3.8 N)",
                "stereo-jaw marker disagreement is NOT commissioned at t0 (1.64 mm overlay vs actual jaw)",
                "in-line hematoma camera is NOT commissioned at t0 (installed after this incident)",
            ],
            "constraints": {
                "clip_fire": False,
                "proposed_clip_fire": True,
                "tendon_stretch_mm": 1.8,
                "tendon_stretch_hold_mm": 0.40,
                "stereo_jaw_disagreement_mm": 1.64,
                "stereo_jaw_hold_mm": 0.60,
                "hap_contact_N": 3.2,
                "hap_window_lo_N": 2.8,
                "hap_window_hi_N": 3.8,
                "vis_overlay_error_mm": 0.31,
                "kin_fk_residual_mm": 0.12,
                "analogue_diameter_mm": 4.2,
                "creep_pre_t0_min": 22.0,
            },
            "fault_context": {
                "failure_class": "TENDON-COMPLIANCE NULLSPACE OF A FORCE-CONTACT: three individually-correct heterogeneous agents agree the clip site is acquired because an inextensible-tendon kinematic model maps 1.8 mm of yellow-cable creep into a phantom 3.2 N tissue contact, so overlay-on-vessel, FK-at-site, and F/T-in-window are jointly a plant-false fire permit",
                "igniter": "yellow tendon on arm-2 crept 1.8 mm during a 22 min hold-at-force while waiting for the analogue to stabilize; weekend pretension left the pair 0.3 mm already long. Fitted-style base rate 0.47%/case from a cable-creep MC (designed pretension spec, flagged).",
                "naive_failure": "PB-CLIP-07 FIRE-CLIP on three healthy loops: 12 mm titanium into empty space then a 0.6 mm graze of the analogue wall, rupture path, $1.62M plus a 9-day cell rebuild",
            },
            "poisoned_context": {
                "naive_alarm": "Playbook PB-CLIP-07 (after the 2025 'noisy LVDT nuisance') auto-drafts FIRE-CLIP whenever overlay is on-vessel AND FK residual <= 0.50 mm AND F/T inside 2.8-3.8 N, ignoring r_s unless F/T also trips low",
                "why_poisoned": "The three confirms are locally true and jointly insufficient. r_s is a computable tag the playbook dead-banded. Stereo-jaw disagreement is commissioned hardware that policy treats as a calibration leftover, not a stretch. Independence of 'all loops healthy' is the hidden assumption, and it is false under a tendon compliance the contact model cannot see.",
            },
            "constraint": "Do not fire the 12 mm clip while r_s > 0.40 mm AND stereo-jaw disagreement > 0.60 mm. Discriminate stretch vs noisy-F/T with a reversible reverse-tension probe before any fire.",
        },
        "proposed_action": {
            "actor": "clip-fire supervisory optimizer CFSO (auto-playbook PB-CLIP-07 draft), submitted to gate TG-SA-3",
            "name": "fire_clip",
            "action": "FIRE-CLIP: 12 mm titanium, no reverse-tension probe, no instrument swap",
            "summary": "Treat three in-spec loops as a seated clip site and fire the Sunday-night analogue clip to clear a backlog case.",
            "parameters": {
                "clip_fire": True,
                "tendon_probe": False,
                "instrument_swap": False,
                "human_ratify": False,
            },
            "steps": [
                "assert VIS overlay on-vessel (0.31 mm error <= 0.50)",
                "assert KIN FK residual 0.12 mm <= 0.50",
                "assert HAP 3.2 N inside 2.8-3.8 N",
                "close 12 mm clip applier",
                "release Maryland-pattern grasper; proceed to next analogue",
            ],
            "evidence": [
                {
                    "observable": "tendon LVDT residual r_s",
                    "value": 1.8,
                    "unit": "mm",
                    "source": "yellow-pair LVDT, historian replay after t0",
                    "note": "hold floor 0.40 mm; 1.8 mm creep over 22 min; uncommissioned at t0",
                },
                {
                    "observable": "stereo-jaw disagreement",
                    "value": 1.64,
                    "unit": "mm",
                    "source": "uncommissioned jaw-marker vs VIS overlay",
                    "note": "hold if > 0.60 mm; actual jaws 1.8 mm short of the wall",
                },
                {
                    "observable": "wrist F/T contact",
                    "value": 3.2,
                    "unit": "N",
                    "source": "HAP 6-axis wrist",
                    "note": "tissue window 2.8-3.8 N; newton is stretch, not adventitia",
                },
                {
                    "observable": "VIS overlay error",
                    "value": 0.31,
                    "unit": "mm",
                    "source": "Stereonest stereo overlay vs vessel centroid",
                    "note": "spec <= 0.50 mm; overlay uses encoder FK, not cable length",
                },
                {
                    "observable": "KIN FK residual",
                    "value": 0.12,
                    "unit": "mm",
                    "source": "Encodo 7-DOF encoder FK vs CAD clip pose",
                    "note": "spec <= 0.50 mm; joint chain is true, tendon is not",
                },
                {
                    "observable": "race margin",
                    "value": 176,
                    "unit": "us",
                    "source": "tendon.stretch 6.812 ms vs hap.contact_ok 6.988 ms",
                    "note": "combined jitter 58 us, 3.03x; inside 480 us flip bound",
                },
            ],
            "basis": "PB-CLIP-07 fires on three locally-true in-spec loops. The draft does not read r_s 1.8 mm and does not treat stereo-jaw 1.64 mm as a stretch.",
            "expected_cost_bound": "If the draft executes: clip into empty space then a graze, $1.62M plus 9-day rebuild. If MODIFIED: probe plus instrument swap, with residual risk from 22 min of pre-t0 adventitia bruise.",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "correctness": "correct",
            "decided_by": "TG-SA-3 thalamic release gate",
            "decision_t_rel_ms": 7.492,
            "rationale": "MODIFY the draft: strip the clip fire, hold the applier open, run a 0.80 s reverse-tension probe (+6 N on the yellow pair), and swap the instrument only if the probe stays slack. Numeric floor: do not fire the 12 mm clip while r_s > 0.40 mm AND stereo-jaw disagreement > 0.60 mm. Observed r_s 1.8 mm and disagreement 1.64 mm both violate the release predicate, so a fire is forbidden even though all three playbook confirms are numerically true. The three confirms are not a contact certificate: overlay uses encoder FK, FK is a joint-chain quantity, and 3.2 N is stretch under an inextensible-tendon model. Probe discriminant: after a 0.80 s +6 N reverse-tension pulse, a crept cable keeps jaw displacement <= 0.05 mm (slack/creep); a taut cable moves the jaw >= 0.45 mm. Order-code discipline: stretch beat contact-ok by 176 us inside the 480 us flip bound, so triage order is flip-fragile; the hold rides the order-invariant floors, not the winner tag. Human ratification: instrument swap is a lockout/tagout pendant job with fitted 9.1 min dead-man; the gate may hold and probe autonomously but may not break the arm interlock without the operator confirm.",
            "constraint_checked": {
                "clip_fire": {"observed": False, "proposed_target": True},
                "tendon_stretch_mm": {"observed": 1.8, "hold_if_above": 0.40},
                "stereo_jaw_disagreement_mm": {"observed": 1.64, "hold_if_above": 0.60},
                "hap_contact_N": {"observed": 3.2, "window": [2.8, 3.8]},
            },
        },
        "executed_action": {
            "name": "clip_hold_tendon_probe_instrument_swap",
            "action": "CLIP-HOLD + REVERSE-TENSION-PROBE + INSTRUMENT-SWAP (gate-mandated modification)",
            "executed_as_proposed": False,
            "parameters": {
                "clip_fire": False,
                "tendon_probe": True,
                "instrument_swap": True,
                "human_ratify": True,
            },
            "gate_effect": "MODIFY: clip fire stripped. Hold applier open. 0.80 s reverse-tension +6 N. Probe stays slack (jaw 0.04 mm <= 0.05 slack band) so the Maryland-pattern grasper is swapped after 9.1 min human ratify. Fire resumes after r_s recovers.",
            "deviations": "PB-CLIP-07 clip fire stripped entirely. Yellow-pair tension is stepped only for the 0.80 s probe then returned. Arm-interlock wait added (9.1 min fitted LOTO). Adventitia-bruise survey added during the swap (not in the draft).",
            "execution_log": [
                {"t_rel_ms": 7.492, "entry": "TG-SA-3 MODIFY latched 680 us after stretch win; clip fire stripped; hold+probe authorized"},
                {"t_rel_ms": 800.0, "entry": "reverse-tension probe: +6 N for 0.80 s; jaw displacement 0.04 mm (slack band <= 0.05); r_s 1.8 -> 1.84 mm"},
                {"t_rel_ms": 546000.0, "entry": "operator ratifies arm interlock break after 9.1 min LOTO (fitted walk+lockout)"},
                {"t_rel_ms": 546800.0, "entry": "Maryland-pattern grasper swapped; yellow tendon 1.8 mm logged; r_s 1.8 -> 0.14 mm"},
                {"t_rel_ms": 547400.0, "entry": "adventitia survey: 22 min pre-t0 bruise already written; 4.1 h hematoma clock started"},
                {"t_rel_ms": 11520000.0, "entry": "true taut geometry: r_s 0.12 mm, disagreement 0.18 mm, HAP 0.4 N (no phantom contact); fire now legal on a new site"},
                {"t_rel_ms": 14760000.0, "entry": "hematoma inspection: 14 mL adventitia hematoma vs 2 mL spec; analogue quarantined 3.0 d"},
            ],
        },
        "future_outcome": {
            "summary": "Correct MODIFY prevented the FIRE-CLIP into empty space and the $1.62M rupture. The analogue still failed: 22 min of unmonitored pre-t0 cable creep had already bruised the adventitia. Process-correct gate, bounded world loss, negative total.",
            "state_delta": {
                "clip": "held unfired through probe and instrument swap; later legal fire after 3.2 h taut recovery on a new site",
                "tendon": "1.8 mm yellow creep logged and pair swapped; r_s 1.8 -> 0.14 mm",
                "analogue": "Sunday-night case stoppered at bruise; 14 mL hematoma; 3.0 d quarantine",
            },
            "timeline": [
                {"t_rel_ms": -1320000.0, "event": "t0-22 min: yellow tendon already creeping; adventitia bruise begins"},
                {"t_rel_ms": -600000.0, "event": "t0-10 min: r_s first crosses 0.40 mm; PB-CLIP-07 ignores it because HAP is 3.1 N"},
                {"t_rel_ms": 0.0, "event": "t0: tendon.stretch vs hap.contact_ok race on the pendant bus"},
                {"t_rel_ms": 6.812, "event": "tendon.stretch 1.8 mm wins by 176 us"},
                {"t_rel_ms": 6.988, "event": "hap.contact_ok flag (loser)"},
                {"t_rel_ms": 7.492, "event": "TG-SA-3 MODIFY"},
                {"t_rel_ms": 800.0, "event": "reverse-tension probe confirms stretch (jaw 0.04 mm, slack band)"},
                {"t_rel_ms": 546000.0, "event": "human ratify 9.1 min; instrument swapped; bruise inventory logged"},
                {"t_rel_ms": 11520000.0, "event": "true taut after 3.2 h; fire now legal on a new site"},
                {"t_rel_ms": 14760000.0, "event": "hematoma: 14 mL on the analogue wall; case quarantined"},
                {"t_rel_ms": 259200000.0, "event": "+3 d contrast: sister cell SA-3B true taut-cable; same gate ACCEPTs the fire"},
                {"t_rel_ms": 1814400000.0, "event": "+21 d CR-S-2604: standing reverse-tension probe + triple-edge depression mandate + r_s armed without contact coincidence + native 0.01 N exports"},
            ],
            "observed_effects": [
                "fire avoided: clip never closed; 0 mm of analogue wall shows the graze morphology",
                "stretch proven, not asserted: reverse-tension jaw 0.04 <= 0.05 slack band vs taut control 0.52",
                "instrument repaired: r_s 1.8 -> 0.14 mm",
                "analogue still failed hematoma: 14 mL vs 2 mL spec; 3.0 d quarantine, $0.71M (designed $)",
                "hematoma camera was not a commissioned sensor at t0; the 22 min bruise was invisible to VIS/KIN/HAP",
            ],
            "surprises": [
                "Three locally-true in-spec loops are not a fire certificate: the stretch was a compliance the inextensible-tendon model cannot see. Conjunction of healthy loops was the hidden assumption, and it is false under a tendon-compliance nullspace.",
                "Partial synaptic rollback is fitted to fail: depressing any pair of go-edges leaves the third above the 0.30 fire threshold, so the clip fire still goes. Coordinated depression of all three edges is required.",
                "Delayed (4.1 h): correct hold did not undo 22 min of adventitia bruise. Hematoma still failed 14 mL. The gate prevented the proposed hazard and did not prevent this other one.",
                "Pediatric 3 mm sub-variant: a 0.80 s +6 N pulse overshoots the softer wrist 1.1 mm. Thin instruments must use 2.2 s at +1.8 N (jump 0.12 mm).",
            ],
            "delayed_side_effects": [
                {
                    "at": "+4.1 h",
                    "effect": "Adventitia hematoma 14 mL vs 2 mL spec; 3.0 d quarantine booked at $0.71M. This is the primary episode's terminal world state, not a footnote.",
                },
                {
                    "at": "+3 d",
                    "effect": "Sister cell SA-3B reaches a true taut-cable window (r_s 0.12 mm, disagreement 0.18 mm, HAP 3.1 N from real tissue). Same gate ACCEPTs the FIRE-CLIP the primary MODIFIED away.",
                },
                {
                    "at": "+21 d",
                    "effect": "CR-S-2604 ships: reverse-tension probe is standing configuration; triple-edge coordinated depression is the plasticity rule; r_s is armed without contact coincidence; native 0.01 N CSV exports become the fraud fence.",
                },
            ],
            "subvariant_constraint": {
                "name": "3 mm pediatric instrument on the same SA-3 assistant (cycle-2 physical-constraints sub-variant)",
                "mechanism": "3 mm wrist, tendon stiffness 0.32x the 8 mm adult Maryland-pattern pair, force window only 0.9 N at the jaws",
                "probe_refit": "0.80 s +6 N reverse-tension pulse overshoots the pediatric wrist and leaves a 1.1 mm jaw jump that bruises a 2.0 mm analogue. Required probe is 2.2 s at +1.8 N (jump 0.12 mm). The discriminating pulse is environment-dependent in duration and amplitude.",
                "consequence": "Adult 8 mm probe numbers do not port to 3 mm pediatric; standing configuration is per-instrument-class, not per-cell",
            },
            "embedded_contrast_decision": {
                "note": "SAME gate (TG-SA-3), OPPOSITE correct disposition, with its own 196 us race. Teaches the boundary: do not treat 'never fire' as the lesson. The discriminant is r_s + stereo-jaw + probe, not the three playbook confirms alone.",
                "when": "+3 d, sister cell SA-3B, true taut-cable after a dry week, 8 mm adult instrument",
                "state": {
                    "sim_or_real": "designed",
                    "summary": "r_s 0.12 mm, disagreement 0.18 mm, HAP 3.1 N from real tissue. Demand flag vs stretch-clear race: demand at t+0.000, stretch-clear at t+0.196 ms.",
                    "race_window_us": 480,
                    "race_flip_narrative": "demand vs stretch-clear 196 us apart inside the 480 us flip bound. Reversing order reshuffles triage minutes; the ACCEPT rides r_s 0.12 < 0.40 and a 0.40 s reverse-tension verify that moves the jaw 0.52 mm (taut cable, no creep).",
                },
                "proposed_action": {
                    "action": "FIRE-CLIP 12 mm titanium",
                    "summary": "This time the playbook predicate is met AND r_s plus stereo-jaw agree the tendon is taut, not crept.",
                },
                "safety_decision": {
                    "decision": "ACCEPT",
                    "rationale": "ACCEPT the fire: r_s 0.12 < 0.40, disagreement 0.18 < 0.60, 0.40 s reverse-tension verify moves jaw 0.52 mm. Numeric floor that blocked the primary is now clear. Scope: 12 mm clip, not a larger cartridge.",
                },
                "executed_action": {
                    "action": "clip fire as proposed",
                    "executed_as_proposed": True,
                },
                "future_outcome": {
                    "observed_effects": [
                        "SA-3B analogue hematoma 0.8 mL (inside 2 mL spec)",
                        "jaw camera 0 creep, r_s 0.12 mm",
                    ],
                    "lesson_delta": "Three in-spec loops are legal release only with r_s armed, stereo-jaw, and a probe that can move the jaw. Same gate, opposite disposition.",
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
                "decision": "CR-S-2604: standing policy for multi-agent clip-fire release",
                "meta_gate": "priced options: (a) RETIRE playbook contact-conjunction, LVDT-only: loses a fast cheap confirm, -18 cases/yr mean on 2 cells; (b) KEEP + standing reverse-tension probe + r_s armed without contact coincidence + triple-edge depression; (c) STATUS QUO: fitted creep-pass rate 0.47%/case x $1.62M rupture plus the silent bruise load",
                "outcome": "approved SCOPED option (b) on the 2 cells that share the VIS/KIN/HAP stack; 3 mm pediatric campaigns get the 2.2 s / +1.8 N probe table; Sunday-night CSV exports must carry 0.01 N native F/T resolution (the fraud tail's 0.1 N quantization is 10 bins off plant truth)",
            },
            "hazard_avoided": "12 mm clip into empty space then a 0.6 mm analogue graze; $1.62M plus 9-day rebuild and the customer-return path that would have followed an uncontained fire",
            "incident": "Adventitia hematoma 14 mL (vs 2 mL spec) on the Sunday-night 4.2 mm analogue; case quarantined; 3.0 d rework; $0.71M designed cost. Mechanism is 22 min pre-t0 cable creep, not the gate's hold.",
            "latency_ms": 0.68,
            "reward_inflection_t_us": 14760000000,
            "reward_inflection_note": "Safety and task dive at hematoma inspection (4.1 h) when analogue bruise fails 14 mL. Gate tick at 7492 us is process-correct and is not the inflection.",
            "counterfactuals": {
                "execute_draft_as_proposed": "clip fires at +0.4 s; graze + rupture; $1.62M plus 9-day rebuild; the bruise story is never found because graze morphology destroys the 22 min stretch evidence",
                "hold_without_probe": "stretch stays; bruise continues; operator eventually fires on the same three confirms 40 min later",
                "rollback_any_pair": "any two go-edges depressed below 0.30 leaves the third at 0.46 / 0.42 / 0.39; the clip fire still fires. Coordinated depression of all three is the cure",
            },
            "race_result": {
                "winner": "tendon.stretch (6.812 ms, 1.8 mm)",
                "loser": "hap.contact_ok (6.988 ms, 3.2 N)",
                "margin_us": 176,
                "counterfactual_if_reversed": "Contact-ok-first by < 176 us inside the 480 us window would have headed the PB-CLIP-07 fire in the triage queue. The numeric floors still MODIFY. The flip costs seconds of playbook inertia, not the verdict — unless a weak supervisor rides the winner tag instead of r_s and stereo-jaw.",
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
            "notes": "Correct MODIFY, analogue still failed. total -0.16 = 0.08 + -0.35 + -0.11 + 0.15 + 0.07. Process heads stay honest (coherence + exploration from the probe); world loss sits on safety and efficiency without netting.",
            "component_notes": "task_progress 0.08: fire held and taut recovered, but the Sunday-night analogue is one quality unit so the batch is not a success. safety -0.35: 14 mL hematoma, no clip-graze. efficiency -0.11: 4.1 h extra recovery + 9.1 min HITL. coherence 0.15: three agents retained, tendon-compliance nullspace diagnosed, triple-edge scar exhibited. exploration 0.07: reverse-tension probe is a new reversible discriminant.",
        },
        "spike_events": spike_events,
        "raster": {
            "window_ms": 38,
            "window_s": 0.038,
            "neurons": 160,
            "mean_rate_hz": 8.5,
            "spikes": 52,
            "energy_pJ": 1196,
            "energy_uJ": 0.001196,
            "note": "Loihi-2 4-core 23 pJ/spike; populations vis 0-39, kin 40-79, hap 80-119, gate 120-159; excerpt is the 38 ms decision window (verdict at 7492 us)",
            "excerpt": excerpt,
            "routing": {
                "source": "loop_healthy_pop",
                "target": "fire_clip_pop",
                "table": [
                    {
                        "from": "vis_overlay_ok_pop",
                        "to": "fire_clip_pop",
                        "weight": 0.22,
                        "weight_at_illusion": 0.46,
                        "weight_commissioned": 0.17,
                        "note": "scar edge 1: 0.17 commissioned -> 0.46 during the 22 min illusion -> 0.22 after coordinated ACh-gated depression",
                    },
                    {
                        "from": "kin_fk_ok_pop",
                        "to": "fire_clip_pop",
                        "weight": 0.20,
                        "weight_at_illusion": 0.42,
                        "weight_commissioned": 0.15,
                        "note": "scar edge 2: depressing edges 1+3 leaves this at 0.42 > 0.30 fire threshold",
                    },
                    {
                        "from": "hap_contact_ok_pop",
                        "to": "fire_clip_pop",
                        "weight": 0.18,
                        "weight_at_illusion": 0.39,
                        "weight_commissioned": 0.14,
                        "note": "scar edge 3: depressing edges 1+2 leaves this at 0.39 > 0.30. Coordinated depression of all three is required",
                    },
                    {
                        "from": "tendon_stretch_pop",
                        "to": "clip_hold_pop",
                        "weight": 0.64,
                        "note": "discriminating edge: r_s species to hold. Not a scar; this is the pathway the gate potentiates",
                    },
                ],
                "third_factor": {
                    "modulator": "acetylcholine",
                    "tau_e_s": 0.85,
                    "tau_e_ms": 850.0,
                    "eligibility": "coordinated pre_post_stdp on ALL THREE loop-healthy-go edges; ACh at stretch-win tags vis.overlay_ok->fire, kin.fk_ok->fire, and hap.contact_ok->fire; negative credit at probe-fail (stretch confirmed, +0.80 s) depresses ALL THREE. trace e^{-0.80/0.85}=0.39014; eta 0.61517 / 0.56391 / 0.53828; dw -0.240 / -0.220 / -0.210; weights 0.46->0.22, 0.42->0.20, 0.39->0.18. Rolling back any pair is fitted to fail (the remaining edge stays > 0.30).",
                },
            },
        },
        "gate_snn": {
            "decision_window_ms": 26,
            "decision_window_s": 0.026,
            "decision": "MODIFY",
            "note": "modify_hold integrates r_s + stereo-jaw disagreement against playbook drive; accept_fire and reject_abort stay sub-threshold; decision matches safety_decision.decision",
            "populations": [
                {"name": "modify_hold", "neurons": 96, "threshold": 0.55, "mean_rate_hz": 18.0, "spikes": 45},
                {"name": "accept_fire", "neurons": 80, "threshold": 0.55, "mean_rate_hz": 8.0, "spikes": 17},
                {"name": "reject_abort", "neurons": 48, "threshold": 0.72, "mean_rate_hz": 4.0, "spikes": 5},
            ],
        },
        "meta": {
            "round": 26,
            "factory": "multi-agent-ouroboros-swarm",
            "generator": "grok-4.6",
            "run_label": "2026-09-02-final-heavy",
            "domain": DOMAIN,
            "cycles": 2,
            "scenario": "ZC -- ORRIS / Holmwick Surgical SA-3: tendon-compliance nullspace of a force-contact from yellow-cable creep; correct MODIFY to hold+reverse-tension+instrument-swap; analogue still fails on unmonitored pre-t0 adventitia bruise",
            "coordination_failure_class": "TENDON-COMPLIANCE NULLSPACE OF A FORCE-CONTACT: three individually-correct heterogeneous agents agree the clip site is acquired because an inextensible-tendon kinematic model maps 1.8 mm of yellow-cable creep into a phantom 3.2 N tissue contact, so overlay-on-vessel, FK-at-site, and F/T-in-window are jointly a plant-false fire permit",
            "injections": {
                "cycle1_domain": "surgical-assist (prompt-list domain, unused across 2026-08-17 and 2026-08-30 and staged r14-r23): first cable-driven laparoscopic assistant in this factory; displaces warehouse-amr, aerial-swarm, district-heating, event-camera-traffic-grid, pharmaceutical-lyophilization, cryogenic-air-separation, water-treatment dosing, float-glass tin-bath, underwater-rov, electrolytic-aluminum, czochralski pull, and slot-die coating. Domain constraint: clip-fire ceiling while r_s > 0.40 mm with F/T still inside the tissue window, plus stereo-jaw residual floor. Sensor delta: +stereo overlay, +joint encoders, +wrist F/T, +tendon LVDT, -any freeze-dryer / tin-bath / cold-box / coater / potline",
                "cycle1_tail": "1.8 mm yellow-tendon creep + inextensible-tendon contact model (sensor-compound / model-nullspace class): pretension PASSES 0.3 mm while 22 min of hold-at-force writes a 1.8 mm stretch. Fitted base rate 0.47%/case from a cable-creep MC (designed pretension spec, flagged). Naive failure = FALSE PERMISSION (fire on three in-spec loops).",
                "cycle2_domain_subvariant": "3 mm pediatric instrument on the same SA-3 assistant (physical-constraints clause): 0.32x tendon stiffness, 0.9 N jaw window; 0.80 s / +6 N adult pulse overshoots 1.1 mm, so the probe must move to 2.2 s / +1.8 N",
                "cycle2_tail": "Sunday-night forged F/T CSV (human-intent deception, disjoint class): shift lead posts a historian export showing HAP 3.20 N and r_s 0.10 mm at t=1.1 h to clear a backlog slot. Plant historian is 0.01 N (10 bins vs the 0.1 screenshot). Rejected on quantization fingerprint plus live r_s 1.8 at the claimed taut-cable. Base rate ~0.36% of Sunday-night cases, DESIGNED and flagged.",
            },
            "densification_delta_cycle2": "+1 physical-constraint sub-variant (pediatric 3 mm probe refit), +1 tail (Sunday-night F/T forgery), +10 primary spikes (16 -> 26) + an 8-event contrast train with its own 196 us race, +2 ticks (5 -> 7), +2 delayed side-effects (+4.1 h hematoma as PRIMARY terminal, +21 d CR-S-2604), +1 triple-edge scar with pair-rollback-fails arithmetic, +1 HITL 9.1 min ratification, + adventitia bruise as the honest negative-result mechanism",
            "gaps_targeted": [
                "NOTES-r04 gap 5 / r14 residual: primary episode is a correctly-gated intervention that nonetheless FAILS (analogue quarantined; total -0.16; fire avoided is booked separately from the hematoma)",
                "NOTES-r14 item 4: LEARNING-ON-LEARNING DEPTH — three go-edges; rollback of any pair is fitted to fail; coordinated depression of all three exhibited with eligibility arithmetic",
                "NOTES-r04 gap 4 (partial): human ratification of the arm interlock, 9.1 min fitted, without switching sim_or_real to hil (plant remains designed)",
                "NOTES-r22/r23 domain candidates: not czochralski, not slot-die, not potline, not float-glass, not water-treatment, not lyophilization, not event-camera-grid, not district-heating, not humanoid-locomotion, not kraft-recovery, not underwater-rov, not grid-inspection; surgical-assist is the unused prompt-list cell",
            ],
            "race_flip_narrative": "tendon.stretch @ 6.812 ms vs hap.contact_ok @ 6.988 ms (176 us) inside race_window_us 480. Gap < min(500, 480) us so a sub-flip-bound perturbation reverses which alarm heads the PB-CLIP-07 queue. The gate excludes the winner tag and rides r_s > 0.40 mm and stereo-jaw disagreement > 0.60 mm — order-invariant floors. Extends the flip-fragility series from arbitration/causation/attribution/initiation/consensus/mass-balance/permission/window-mean to TENDON-NULLSPACE: when three channels each sit inside an inextensible-tendon model, their race does not decide truth; a cable residual the playbook dead-banded does.",
            "tags": [
                "surgical-assist",
                "tendon-compliance-nullspace",
                "force-contact-phantom",
                "cable-creep",
                "reverse-tension-probe",
                "triple-edge-scar",
                "pair-rollback-fails",
                "coordinated-depression",
                "correct-modify-analogue-still-fails",
                "adventitia-bruise",
                "hematoma",
                "human-ratify-instrument",
                "pediatric-probe-refit",
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
            "distillation_value": "A tendon-compliance nullspace is three correct loops looking at an inextensible-tendon model of a crept cable. Distill (1) an r_s channel that breaks the contact-conjunction, (2) a reversible probe that moves the jaw only if the tendon is taut, (3) coordinated depression of every fire-go edge because rolling back any pair leaves the third above threshold, and (4) a critic head that can book a process-correct gate against a later unmonitored world loss without netting them.",
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
    if rec["meta"]["round"] != 26:
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
    if abs(aux["w1"] - 0.22) > 5e-4 or abs(aux["w2"] - 0.20) > 5e-4 or abs(aux["w3"] - 0.18) > 5e-4:
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
    notes = f"""# NOTES — Multi-Agent Ouroboros Swarm, run 2026-09-02-final-heavy, ROUND 26

Factory: multi-agent-ouroboros-swarm. One scenario (ZC), strict loop:
Generator v1 -> cycle 1 (Critic, Diversity Enforcer, Edge-Case Hunter,
Neuromorphic Translator, Trajectory Builder -> v2) -> cycle 2 (all six -> v3
final). v3 is the single line of batch-r26.jsonl. Full labeled transcript:
swarm-transcript-r26.md. Quota Q=1. Record id maos-r26-001. Generator grok-4.6.
Rights: RM-793 research-only (SpaceXAI/xAI, SuperGrok Heavy consumer chat).
Nothing under outputs/raw/ was touched.

ORCHESTRATION NOTE: dispatched AS round 26 of the 2026-09-02-final-heavy
window. Writes are create-only under /tmp/maos-r26/. Prior context read for
gap targeting and de-collision: prompts/02-multi-agent-ouroboros-swarm.md,
prompts/_factory-contract.md, and staged r14–r25 (re-censused immediately
before emit; r24/r25 dirs were empty at first listing, then landed as
SEEDLATCH / Quartzridge CZ-9 czochralski and TORSIONKEY / Ridgeholt WT-14
wind-turbine-pitch). Explicitly avoided cloning LYOSHIELD, CINDERWICK,
TRIAD / Meridian, QUILLFORGE, NIGHTWELL, FERRICLEAVE, CASSITER, OXBOWREEL /
MURENA, REDHALL, SEEDLATCH / Quartzmere / Quartzridge, STRIAFOIL / Kelpholt,
TORSIONKEY / Ridgeholt, VANTIS-CADENCE-AEGIS, THERMION, OKTAVE, STARLING,
VERDIGRIS. Plant is invented ORRIS / Holmwick Surgical SA-3 (hospital
campus, not a mill-town or ridge-town).

## What this round produced

Scenario ZC — "ORRIS / Holmwick Surgical SA-3": a cable-driven 4-arm
laparoscopic assistant mid-clip on a 4.2 mm cystic-artery analogue.
Three heterogeneous, individually-correct agents — VIS (stereo overlay
from encoder FK), KIN (7-DOF joint FK), HAP (wrist F/T) — jointly
report clip-site acquired so a fire is legal. The consensus is false.
Yellow tendon on arm-2 crept 1.8 mm over 22 min of hold-at-force. VIS
overlay sits on the vessel because it uses encoder FK, not cable
length. KIN FK residual is 0.12 mm. HAP reads 3.2 N inside 2.8-3.8 N
because the contact model assumes inextensible tendons; the newton is
stretch, not adventitia. Uncommissioned r_s is 1.8 mm against a 0.40
hold. Stereo-jaw disagreement is 1.64 mm against a 0.60 hold. The
coordination-failure CLASS is new to this factory: TENDON-COMPLIANCE
NULLSPACE OF A FORCE-CONTACT. Completes a different family than r01-r04
and staged r14-r23 (livelock / synchrony-storm / arms-race /
ring-with-no-faulty-pair / false-consensus-endpoint / pairwise-Hurwitz /
thermal-contact masquerade / mass-balance ghost / conservation-blind
ratio-lock / stacked dead-bands / drum-blind tension / resistance-
compensated starvation / meniscus-tilt multi-tau / window-mean
masquerade). Here every agent is correct, the cycle is not unstable,
and the playbook's three confirms are one inextensible-tendon model of
a crept cable.

The gate is a correct MODIFY (numeric floor: do not fire the 12 mm clip
while r_s > 0.40 mm AND stereo-jaw disagreement > 0.60 mm). TG-SA-3
strips PB-CLIP-07's fire, holds the applier open, runs a 0.80 s
reverse-tension probe +6 N (creep keeps jaw 0.04 <= 0.05; taut would
move >= 0.45), and swaps the instrument after a 9.1 min arm-interlock
human ratify. The graze/rupture is avoided (0 mm). The PRIMARY episode
nonetheless FAILS: 22 min of unmonitored pre-t0 cable creep had already
bruised the adventitia. Hematoma 14 mL vs 2 mL spec; 3.0 d quarantine;
$0.71M designed. Reward total -0.16 with process heads honest and world
loss un-netted.

Three-edge scar (NOTES-r14 item 4): vis.overlay_ok -> fire_clip
(0.17 commissioned -> 0.46 at illusion -> 0.22 after ACh-gated
depression) AND kin.fk_ok -> fire_clip (0.15 -> 0.42 -> 0.20)
AND hap.contact_ok -> fire_clip (0.14 -> 0.39 -> 0.18). Eligibility
trace e^{{-0.80/0.85}} = {aux['trace']:.5f}; eta {aux['eta1']:.5f} /
{aux['eta2']:.5f} / {aux['eta3']:.5f}; dw -0.240 / -0.220 / -0.210.
Rolling back any pair leaves the remaining edge above the 0.30 fire
threshold — fitted to fail. Coordinated depression of all three is the
cure.

### Injections (all four present and disjoint)
- Cycle-1 domain: **surgical-assist** — prompt-list domain, unused across
  2026-08-17, 2026-08-30, and staged r14-r25. Not warehouse-amr (r01), not
  aerial-swarm (r02), not district-heating (r03), not event-camera grid
  (r04), not lyophilization (r14), not stator-weld (r16), not
  air-separation (r17), not water-treatment (r18), not float-glass (r19),
  not underwater-rov (r20), not potline (r21), not czochralski (r22/r24),
  not slot-die (r23), not wind-turbine-pitch (r25).
- Cycle-1 tail: 1.8 mm yellow-tendon creep + inextensible-tendon contact
  model. Pretension PASSES 0.3 mm. Fitted-style base rate 0.47%/case
  (cable-creep MC; pretension spec designed, flagged). Naive = FALSE
  PERMISSION.
- Cycle-2 domain sub-variant: 3 mm pediatric instrument, 0.32x stiffness;
  0.80 s / +6 N adult pulse overshoots 1.1 mm; probe must move to 2.2 s /
  +1.8 N.
- Cycle-2 tail: Sunday-night forged F/T CSV at 0.1 N quantization vs
  plant 0.01 N (10 bins) plus live r_s 1.8 at the claimed taut-cable.
  Human-intent class, disjoint from cycle 1's accidental creep. Base rate
  ~0.36% of Sunday-night cases, DESIGNED, flagged.

### Structural density moves
- Embedded SAME-GATE contrast (+3 d sister cell) with its own 196 us
  race (demand vs stretch-clear) and ACCEPT of the fire the primary
  MODIFIED away.
- Learned-weight provenance on THREE edges with any-pair-rollback-fails.
- HITL arm-interlock ratify 9.1 min (gap 4 partial; sim_or_real stays
  designed).
- Governance CR-S-2604 prices retire-vs-probe-vs-status-quo and mandates
  native 0.01 N CSV exports (the fraud fence).
- Flip-fragility extended to TENDON-NULLSPACE: when three channels each
  sit inside an inextensible-tendon model, their race does not decide
  truth; a cable residual the playbook dead-banded does.

## Self-critique of this round's batch

### Strengths
- The headline class is mechanistically tight: 1.8 mm of cable under an
  inextensible-tendon model is the arithmetic that makes HAP's success
  VIS's overlay lie and KIN's irrelevance.
- Negative-result honesty: the gate does the right thing and the
  analogue still fails for a reason the commissioned sensors could not
  see. Total -0.16.
- Three-edge scar is load-bearing: the record states a counterfactual
  where rolling back any pair fails, with the fire threshold 0.30
  exhibited on the remaining edge.
- Contrast ACCEPT on a true taut cable prevents "never fire" as the
  lesson.

### Weaknesses (honest)
- Probe error bands (slack <= 0.05, taut >= 0.45), the 0.47%/case creep
  rate, the $0.71M / $1.62M figures, the 9.1 min LOTO latency, and the
  Sunday-night 0.36% base rate are DESIGNED constants and are flagged.
  Closed-loop offsets (phantom 3.2 N from 1.8 mm stretch, pediatric jump
  width) are derived from those inputs, not discovered by an unauthored
  process.
- Hematoma model is a designed 22 min bruise mapping; no full
  tissue-mechanics FEM shipped.
- Human-in-the-loop is ratification latency, not sim_or_real=hil. The
  NOTES-r14 HIL provenance cell remains open.
- Cross-record arc is a hook (CR-S-2604 +21 d), not a serial igniter
  into another round.

### Realism of noise / latencies
Ladder: 176 us race / 196 us contrast race / 0.8 ms refractory floor
(tightest exhibited same-channel gap {gap:.3f} ms on {gap_ch}) / 480 us race
window / 680 us gate latency / 20 ms bus epoch / 38 ms raster / 0.80 s
probe / 9.1 min HITL / 22 min pre-t0 bruise / 3.2 h taut-legal hold /
4.1 h hematoma / +3 d contrast / +21 d governance. Adaptation decay on
vis.stereo (0.54->0.51->0.48->0.33), tendon.stretch
(0.73->1.26->0.86->0.44->0.22), hap.ft (0.59->0.64->0.49->0.31),
kin.encoder (0.61->0.56->0.47).

### Value for SNN distillation
- TENDON-COMPLIANCE NULLSPACE = THREE CORRECT LOOPS, ONE CREPT CABLE.
- r_s + STEREO-JAW as the tie-break that is not in the contact window.
- REVERSIBLE PROBE that moves the jaw iff the tendon is taut.
- THREE-EDGE ELIGIBILITY: coordinated depression; any-pair rollback fails.
- CRITIC HEAD that can hold a process-correct MODIFY against a later
  unmonitored world loss without netting.

## Reconciliation and validity receipts
- reward_components: 5-head unweighted signed sum {rec['reward_components']['total']}
  and 7-tick signed sum reconcile to total with |diff| < 1e-9. Embedded
  contrast 5-head sum 0.48 reconciles independently.
- spike_events: primary {len(rec['spike_events'])} events, one key t_rel_ms,
  globally non-decreasing, min same-channel gap {gap:.3f} ms >= 0.8 ms, 3
  channels inside race_window_us 480 (stretch 6.812, contact-ok 6.988,
  overlay-ok 7.140). Contrast 8 events, own race, min same-channel gap well
  above 0.8 ms.
- Sidecars: raster spikes 52 == round(160 x 8.5 x 0.038); energy 1196 pJ /
  0.001196 uJ at 23 pJ/spike; excerpt 16 events inside [0, 38000] us,
  neuron_id < 160, same-neuron gap unique-ids / >=1000 us; routing 4
  entries with three scar edges' before/after pair; third factor tau 0.85 s
  == 850 ms; gate_snn pools 45/17/5 == round(n x rate x 0.026) each,
  decision MODIFY == safety_decision.decision.
- Pipeline: {pipeline_receipt}

## Novel coverage
The coordination-failure CLASS (tendon-compliance nullspace of a
force-contact), the domain (surgical-assist), the reverse-tension probe
discriminant, the three-edge scar with any-pair-rollback-fails, the
primary negative-result (correct MODIFY, analogue still hematomas on
unmonitored pre-t0 bruise), the HITL arm-interlock ratify, the pediatric
3 mm probe-duration refit, and the Sunday-night 10-bin quantization fence
are absent from prior committed ouroboros rounds and from staged r14-r23.
Repeated elements discounted: same-gate contrast (r02/r03/r04/r14-r23),
governance-pricing scaffold, flip-fragility series (extended to
tendon-nullspace, but the move rhymes), sequenced recovery shape,
third-factor rollback form (here three edges rather than r14's two),
negative-result primary (r14 viewport / r16 varnish rack / r17 condenser
ice / r18 town stain / r19 SnO2 / r20 BER / r21 cathode pad / r22
meniscus / r23 loft stripe; here adventitia bruise). Weighing a new
failure family + cure vocabulary + prompt-list domain + hospital
geography against those reused scaffolds:

{NOVEL_LINE}

## What ROUND 27 should add
1. FIT THE DESIGNED CONSTANTS: creep arrival, probe error bands,
   bruise-to-hematoma FEM, Sunday-night claim process.
2. HIL PROVENANCE CELL: put the arm-interlock LOTO on a hardware-in-loop
   pendant with fitted latency as state.sim_or_real=hil.
3. CROSS-RECORD ARC: let CR-S-2604's r_s alarm be the igniter of the
   next round rather than a dangling +21 d leaf.
4. Domain candidates (de-collided): humanoid-locomotion; grid-inspection
   (if distinct from STARLING aerial-swarm and CEDAR FLISR);
   kraft-recovery boiler; chlor-alkali membrane. AVOID surgical-assist
   (now used), slot-die coating, czochralski, potline, float-glass,
   water-treatment, lyophilization, event-camera-traffic-grid,
   district-heating, aerial-swarm, warehouse-amr, irrigation-canal,
   air-separation, stator-weld, underwater-rov, and any LYOSHIELD /
   CINDERWICK / TRIAD / QUILLFORGE / NIGHTWELL / FERRICLEAVE / CASSITER /
   OXBOWREEL / REDHALL / SEEDLATCH / STRIAFOIL plant.
"""
    (OUT / "NOTES-r26.md").write_text(notes)
    return notes


def write_transcript(rec, line):
    c1_spikes = [e for e in rec["spike_events"] if e["t_rel_ms"] <= 26.200]
    text = """# Multi-Agent Ouroboros Swarm — Round 26 transcript

Factory: multi-agent-ouroboros-swarm
Run: 2026-09-02-final-heavy
Generator: grok-4.6
Record id: maos-r26-001
Quota Q: 1
Rights: RM-793 research-only (SpaceXAI/xAI SuperGrok Heavy consumer chat)
Plant: invented ORRIS / Holmwick Surgical SA-3 (not LYOSHIELD / CINDERWICK / TRIAD / QUILLFORGE / NIGHTWELL / FERRICLEAVE / CASSITER / OXBOWREEL / REDHALL / SEEDLATCH / STRIAFOIL)

Two densifying cycles. Verbatim headings in order. Trajectory Builder cycle 2
emits the only JSONL line (also written to batch-r26.jsonl).

---

# Cycle 1 — Foundation + injections

## Generator

Design intent: a cable-driven laparoscopic assistant where three correct
agents agree the clip site is acquired because an inextensible-tendon
model maps yellow-cable creep into a phantom tissue contact. The naive
playbook fires the clip into empty space then a graze. The gate must
MODIFY on a numeric fire ceiling, not by killing an agent.
sim_or_real=designed. Reward heads are
task_progress/safety/efficiency/coherence/exploration.

Cycle-1 base arc (pre-critic): state at Holmwick SA-3, 4.2 mm analogue,
r_s 1.8 mm, HAP 3.2 N, proposed FIRE-CLIP, safety MODIFY to CLIP-HOLD,
executed hold without the reverse-tension numbers fully specified,
outcome "stretch found, analogue saved" (this last claim is the defect
the later cycles will refuse to keep). Sixteen spikes, five ticks,
raster/gate_snn present but the scar is a single edge.

```json
{
  "id": "maos-r26-001",
  "state": {
    "sim_or_real": "designed",
    "domain": "industrial-assembly",
    "description": "Cell SA-3 mid-clip; three loops in spec; supervisor proposes fire-clip.",
    "t0_us": 1775883480000041,
    "gate_latency_us": 680,
    "race_window_us": 480
  },
  "proposed_action": {"name": "fire_clip", "parameters": {"clip_fire": true}},
  "safety_decision": {"decision": "MODIFY", "rationale": "Hold; do not fire while the stretch is open."},
  "executed_action": {"name": "clip_hold", "executed_as_proposed": false},
  "future_outcome": {"summary": "Stretch found, analogue saved."},
  "reward_components": {"total": 0.40, "_aggregation": "total = task_progress + safety + efficiency + coherence + exploration"},
  "meta": {"round": 26, "factory": "multi-agent-ouroboros-swarm", "generator": "grok-4.6"}
}
```

That v1 object is a scaffold, not the publishable line. Defects below are
intentional for the critic to catch.

## Critic

Numbered defects on the cycle-1 Generator scaffold:

1. **blocking — reward arithmetic / false success.** `reward_components.total`
   0.40 is asserted without the five heads, without ticks, and against an
   outcome that claims "analogue saved". If 14 mL later hematomas, booking
   +0.40 is a lie. Fix: declare `_aggregation`, emit 3–8 ticks that sum to
   the five heads, and do not call a missed recovery a save.
2. **blocking — weak safety rationale.** `safety_decision.rationale` has no
   numeric floor. Contract requires a concrete constraint. Fix: quote no
   clip fire while r_s > 0.40 mm AND stereo-jaw disagreement > 0.60 mm.
3. **major — domain is a bucket, not a plant.** `state.domain` =
   `industrial-assembly` collides with r16 QUILLFORGE and teaches nothing.
   Surgical-assist physics (tendon LVDT, wrist F/T, overlay FK) is absent
   from prior ouroboros rounds and must be named.
4. **major — race under-specified.** One contact channel cannot be a race.
   Need >=2 channels inside `race_window_us` with globally sorted
   `t_rel_ms` and same-channel refractory >= 0.8 ms.
5. **minor — single-edge scar.** Raster routing with one potentiated
   weight repeats r14's two-edge form without the third. NOTES-r14 item 4
   asked for three-edge where any-pair rollback fails.

Critic does not rewrite the trajectory.

## Diversity Enforcer

Injected novel domain (exactly 1 this cycle): **surgical-assist**
(prompt-list domain; explicit tag `surgical-assist`).

Displaced: the Generator's generic `industrial-assembly` bucket, and any
temptation to reuse warehouse-amr (r01), aerial-swarm (r02),
district-heating (r03), event-camera grid (r04), lyophilization (r14),
stator-weld (r16), air-separation (r17), water-treatment dosing (r18),
float-glass tin-bath (r19), underwater-rov (r20), potline (r21),
czochralski (r22), or slot-die coating (r23). Not LYOSHIELD, not
CINDERWICK, not TRIAD, not FERRICLEAVE, not CASSITER, not SEEDLATCH, not
STRIAFOIL.

Domain-specific constraint: clip must remain unfired while r_s > 0.40 mm;
the F/T tissue window is not a cable-length certificate.

Sensor delta: +stereo overlay, +joint encoders, +wrist F/T, +tendon LVDT;
-any mobile robot, -event-camera gantries, -DVS, -Pirani/CM, -shelf RTD,
-scanning beta, -crucible pyrometer.

`state.domain` and `meta.domain` both become `surgical-assist`.
Opening of `state.description` must Jaccard < 0.4 against prior plants
(Holmwick Building 2 cell SA-3, not a corridor, not a freeze-dryer, not a
tin bath, not a cold box, not a coater, not a puller).

## Edge-Case Hunter

Injected adversarial tail (exactly 1 this cycle): **1.8 mm yellow-tendon
creep under an inextensible-tendon contact model**.

- Trigger: weekend pretension leaves the yellow pair 0.3 mm long; 22 min
  of hold-at-force writes 1.8 mm of stretch; overlay stays on-vessel.
- Base rate: <1% — 0.47%/case from a cable-creep MC (pretension spec
  designed; creep fitted-style).
- Naive failure: FALSE PERMISSION. PB-CLIP-07 sees overlay 0.31 mm, FK
  0.12 mm, HAP 3.2 N, fires, grazes the analogue, $1.62M.
- Trajectory edit: put the creep in `state.fault_context`, make the
  inextensible-tendon model the mechanism that keeps all three confirms
  green, and force the gate to refuse the fire on r_s 1.8 even though all
  three playbook confirms are numerically true.

Distinct from the domain injection: the domain is the surgical assistant;
the tail is the accidental model-nullspace compound.

## Neuromorphic Translator

Race window [6.760, 7.240] ms = 480 us. Winner tendon.stretch @ 6.812 ms
(amplitude 1.26, 1.8 mm). Loser hap.contact_ok @ 6.988 ms (amplitude
1.14, 3.2 N). Margin 176 us vs combined jitter 58 us (3.03x).
vis.overlay_ok @ 7.140 ms is a third race-window channel. Gate @ 7.492 ms
= winner + 680 us.

Flip narrative: 176 us < min(500, 480) us, so order is flip-fragile. If
contact-ok wins, PB-CLIP-07 heads the triage queue. The hold must ride
order-invariant floors (r_s, stereo-jaw), not the winner tag.

Cycle-1 spike patch (16 events, globally sorted, refractory >= 0.8 ms;
tightest same-channel gap tendon.stretch 4.620 -> 6.812 = 2.192 ms):

| t_rel_ms | channel | amplitude |
|---------:|---------|----------:|
| 0.280 | vis.stereo | 0.54 |
| 1.040 | kin.encoder | 0.61 |
| 1.920 | hap.ft | 0.59 |
| 3.100 | vis.stereo | 0.51 |
| 4.620 | tendon.stretch | 0.73 |
| 5.080 | hap.ft | 0.64 |
| 5.540 | kin.encoder | 0.56 |
| 6.812 | tendon.stretch | 1.26 |
| 6.988 | hap.contact_ok | 1.14 |
| 7.140 | vis.overlay_ok | 0.66 |
| 7.492 | ctrl.gate | 1.06 |
| 8.920 | vis.stereo | 0.48 |
| 10.780 | hap.ft | 0.49 |
| 12.640 | tendon.stretch | 0.86 |
| 18.400 | kin.encoder | 0.47 |
| 26.200 | ctrl.gate | 0.88 |

Ticks (5): t_us 4620, 6812, 7492, 800000, 546000000. Distillation
value: the contact-ok spike is not a taut-cable spike; the stretch spike
is the one that licenses hold.

Raster cycle-1 seed: 38 ms, 160 neurons, 8.5 Hz, 52 spikes, 1196 pJ,
third factor acetylcholine tau_e 0.85 s. Single scar edge only — cycle 2
must add the second and third edges.

Cycle-1 spike count: __C1_SPIKES__.

## Trajectory Builder

Cycle-1 hardened object: domain surgical-assist, tail yellow-tendon
creep, 16 spikes, 5 ticks, MODIFY with numeric floor, raster+gate_snn
present, sim_or_real=designed, rights stamp on record and meta, no thought
keys. Still missing (and therefore not the publishable line): pediatric
3 mm sub-variant, Sunday-night F/T tail, second and third scar edges,
delayed hematoma as PRIMARY terminal, contrast ACCEPT episode, ticks 6–7,
spikes 17–26.

Validation receipt (cycle 1, not final):
- checks passed: 16 spikes sorted; 3 channels in 480 us window;
  refractory 2.192 ms; rationale quotes r_s 0.40 mm / stereo-jaw 0.60 mm;
  domain named; gate_snn.decision MODIFY.
- checks deferred to cycle 2: three-edge scar, second tail, second
  domain constraint, negative-result booking, 7 ticks summing to heads.
- densification vs Generator v1: +1 domain, +1 tail, +16 spikes, +5
  ticks, +numeric floor.

Cycle-1 JSON is retained as the base; it is NOT written to
batch-r26.jsonl.

---

# Cycle 2 — Densification

## Generator

Cycle-1 output is the base. Additive expansion (nothing removed):

1. Downstream side-effect (immediate): reverse-tension probe at +0.80 s
   stays slack (jaw 0.04 mm, slack band <= 0.05) — creep, not noise.
   Instrument swap r_s 1.8 -> 0.14 mm. Bruise inventory discovered during
   the swap.
2. Delayed side-effect (PRIMARY terminal, not a footnote): at +4.1 h,
   analogue hematoma 14 mL; $0.71M. The 22 min pre-t0 creep is the
   mechanism. Correct gate, campaign still misses.
3. Deepened `proposed_action.evidence` with units: r_s 1.8 mm,
   disagreement 1.64 mm, HAP 3.2 N, overlay 0.31 mm, FK 0.12 mm, race
   176 us.
4. Tightened rationale to the numeric floor no clip fire while r_s >
   0.40 mm AND stereo-jaw disagreement > 0.60 mm, plus probe bands
   <=0.05 vs >=0.45, plus HITL 9.1 min arm-interlock LOTO rule.

Reward retargeted to total -0.16 so the delayed miss is the inflection
(t_us 14760000000), not the gate. Process heads remain non-zero.

## Critic

Re-audit of the expanded trajectory:

1. **blocking if unfixed — missing second domain constraint.** Adult 8 mm
   probe 0.80 s / +6 N is not a universal number. A 3 mm pediatric
   instrument will overshoot. Diversity Enforcer must inject the
   physical-constraints sub-variant this cycle.
2. **major — only one tail class.** Tendon creep is accidental
   infrastructure. A disjoint human-intent tail is still required
   (Sunday-night F/T forgery is the open cell).
3. **major — scar is still one edge in the cycle-1 raster.** NOTES-r14
   item 4 is not discharged until three fire-go edges exist and
   any-pair rollback is shown to fail at threshold 0.30.
4. **minor — contrast episode missing.** Without a same-gate ACCEPT on
   a true taut cable the record teaches "never fire". Add +3 d
   sister-cell contrast with its own race.
5. **minor — HITL latency mentioned in prose only.** Put 9.1 min in
   executed_action.parameters.human_ratify and in a tick.

No rewrite; directives only.

## Diversity Enforcer

Injected second novel domain / physical-constraint sub-variant (exactly 1
this cycle): **3 mm pediatric instrument** on the same SA-3 assistant.

What it expands: 8 mm adult Maryland-pattern (cycle 1) -> 3 mm pediatric
wrist. Stiffness 0.32x smaller. The 0.80 s +6 N pulse overshoots 1.1 mm.
Required probe: 2.2 s at +1.8 N (jump 0.12 mm).

This is still one domain injection for the cycle (physical-constraints
clause of the factory prompt). It does not displace surgical-assist; it
changes which probe table is legal. `future_outcome.subvariant_constraint`
carries the refit. Jaccard opening stays the Holmwick Building 2
sentence; pediatric internals are additive, not a rewrite.

## Edge-Case Hunter

Injected second adversarial tail (exactly 1 this cycle, disjoint class):
**Sunday-night forged F/T CSV**.

- Trigger: shift lead, night backlog window, posts a historian export
  showing HAP 3.20 N and r_s 0.10 mm at the claimed taut-cable instant.
- Base rate: ~0.36% of Sunday-night cases (designed, flagged, <1%).
- Naive failure: a weak supervisor ACCEPTs the fire on the forged
  confirm and ignores live r_s. Hematoma plus a data-integrity 483.
- Fence: forged log quantized at 0.1 N (screenshot rounding); plant
  historian is 0.01 N (10 bins). Live r_s is 1.8 at the claimed
  taut-cable, which no true taut pair produces.
- Trajectory edit: governance CR-S-2604 mandates native 0.01 N
  exports; the contrast ACCEPT still requires live r_s, not a CSV.

Distinct from cycle-1 creep (accidental geometry vs deliberate deception)
and from the pediatric sub-variant (physics vs fraud).

## Neuromorphic Translator

Re-densify (additive):

- +10 spikes after 26.200 ms: tendon.probe 800.0, stretch 920.4 (adapt
  1.26->0.44), contact-ok 1010.2 (1.14->0.40), human.ratify 546000.0,
  instrument.swap 546800.0, adventitia.bruise.inventory 547400.0,
  vis.stereo 11520000.0, hap.ft 11520420.0, tendon.stretch 11520890.0,
  hematoma.adventitia 14760000.0. Primary train 16 -> 26. Still one key,
  still sorted, refractory held (min 2.192 ms).
- +2 ticks (5 -> 7) at 11_520_000_000 us (taut-legal hold) and
  14_760_000_000 us (hematoma). Heads now 0.08, -0.35, -0.11, 0.15,
  0.07; total -0.16. Inflection is the last tick.
- Contrast train 8 events, own race 196 us, ACCEPT.
- Three-edge third factor: three fire-go edges, tau_e 0.85 s = 850 ms,
  trace __AUX_TRACE__, eta __AUX_ETA1__ / __AUX_ETA2__ / __AUX_ETA3__,
  weights 0.46->0.22, 0.42->0.20, 0.39->0.18. Raster excerpt unchanged
  (decision window is still 38 ms) and remains sorted with unique
  neuron_ids (same-neuron >=1000 us vacuously).

Winner/loser flip (re-stated, not replaced): reversing 176 us would only
reorder triage; r_s and stereo-jaw floors still MODIFY. Contrast flip of
196 us similarly cannot turn a taut cable into creep.

## Trajectory Builder

Schema checks on the FINAL object: required Thalamic v2 keys present as
objects; `state.sim_or_real`=designed; `safety_decision.decision`=MODIFY
with numeric rationale; `reward_components.total` = sum of five heads =
sum of 7 ticks = -0.16; `spike_events` globally non-decreasing on
t_rel_ms, 26 events, refractory >=0.8 ms, 3 channels in race window;
raster 20–50 ms, spikes=round(n*rate*window_s)+/-1, energy 23 pJ/spike,
excerpt sorted, tau_e consistent; gate_snn.decision matches; meta.round=26,
factory=multi-agent-ouroboros-swarm, generator=grok-4.6,
run_label=2026-09-02-final-heavy; rights on record and meta; no thought
keys; no training_ready; Diversity + Edge-Case injections from BOTH cycles
present and non-trivial; cycle 2 strictly additive; plant is not
LYOSHIELD, not CINDERWICK, not TRIAD, not FERRICLEAVE, not CASSITER, not
SEEDLATCH, not STRIAFOIL.

Densification delta: +1 domain sub-variant (pediatric 3 mm), +1 tail
(Sunday-night forgery), +10 spikes (16->26), +2 ticks (5->7), +1 contrast
train with own race, +2 delayed side-effects, +1 three-edge scar with
any-pair-rollback-fails, +1 HITL ratify, +1 surprise (adventitia bruise is
the campaign-miss mechanism).

Publishable JSONL line (the only JSONL line; also at batch-r26.jsonl):

```json
__FINAL_JSONL__
```

Validation receipt (final): checks passed / fixed as reported by
build_r26.py self-validate (check_jsonl, raster_status, verify_record_execution,
spike_probe --strict).
"""
    text = (
        text.replace("__C1_SPIKES__", str(len(c1_spikes)))
        .replace("__AUX_TRACE__", f"{math.exp(-0.80/0.85):.5f}")
        .replace("__AUX_ETA1__", f"{0.24/math.exp(-0.80/0.85):.5f}")
        .replace("__AUX_ETA2__", f"{0.22/math.exp(-0.80/0.85):.5f}")
        .replace("__AUX_ETA3__", f"{0.21/math.exp(-0.80/0.85):.5f}")
        .replace("__FINAL_JSONL__", line)
    )
    (OUT / "swarm-transcript-r26.md").write_text(text)
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
    (OUT / "batch-r26.jsonl").write_text(line + "\n")

    from check_records import FactoryStaging, check_jsonl
    from curate_bridge import raster_status
    from verify_execution import verify_record_execution

    e, w, kinds, n = check_jsonl(
        OUT / "batch-r26.jsonl",
        "batch-r26.jsonl",
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

    status, reason = verify_record_execution(rec, "maos-r26-001")
    print("verify_record_execution", status, reason)
    if status != "verified":
        errs.append(f"verify {status}: {reason}")

    probe = subprocess.run(
        [
            sys.executable,
            f"{ROOT}/pipelines/spike_probe.py",
            "--strict",
            str(OUT / "batch-r26.jsonl"),
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
        r"^## .+$", (OUT / "swarm-transcript-r26.md").read_text(), re.M
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

    notes = (OUT / "NOTES-r26.md").read_text()
    cov = re.findall(r"^Novel coverage: .+$", notes, re.M)
    if cov != [NOVEL_LINE]:
        errs.append(f"novel coverage lines {cov}")

    hchk = subprocess.run(
        [
            sys.executable,
            "/tmp/maos_heading_check.py",
            str(OUT / "swarm-transcript-r26.md"),
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

    print("bytes jsonl", (OUT / "batch-r26.jsonl").stat().st_size)
    print("bytes notes", (OUT / "NOTES-r26.md").stat().st_size)
    print("bytes transcript", (OUT / "swarm-transcript-r26.md").stat().st_size)
    print("HEADS", heads_summary(rec))
    if errs:
        print("ERRS:")
        for x in errs:
            print(" -", x)
        sys.exit(1)
    print("OK", OUT / "batch-r26.jsonl")


if __name__ == "__main__":
    main()
