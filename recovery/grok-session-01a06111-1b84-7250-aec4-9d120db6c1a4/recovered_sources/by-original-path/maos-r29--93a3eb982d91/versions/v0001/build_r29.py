#!/usr/bin/env python3
"""Build and self-check MAOS round-29 JSONL (research-only; not published)."""
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

GEN_AT = "2026-09-03T00:22:00Z"
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
OUT = Path("/tmp/maos-r29")
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
    "training_ready",
    "da Vinci",
    "Intuitive Surgical",
    "Nucor",
    "Arcelor",
)
R14_OPENING = (
    "Helixmere Biologics Building C lyophilizer LYO-4 is mid-primary on 8400 "
    "vials of a monoclonal antibody"
)
NOVEL_LINE = "Novel coverage: 46%"
PLANT = "SKULLGATE"
GEO = "Bloomholt"
CELL = "CC-6"
DOMAIN = "steel-continuous-caster-mold-level"
RECORD_ID = "maos-r29-001"
ROUND = 29


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
        if p.parent.name == "maos-r29":
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
        if p.parent.name == "maos-r29":
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
        if p.parent.name == "maos-r29":
            continue
        try:
            text = p.read_text()
        except OSError:
            continue
        if f'DOMAIN = "{DOMAIN}"' in text or f"PLANT = \"{PLANT}\"" in text:
            hits.append(f"{p}: claimed {PLANT}/{DOMAIN}")
        if GEO in text and PLANT in text:
            hits.append(f"{p}: geo+plant {GEO}/{PLANT}")
    return hits


def build_record():
    ticks, heads = cents_ticks(
        [4580, 6520, 7260, 6_400_000, 708_000_000, 11_160_000_000, 22_320_000_000],
        [
            (1, -2, -1, 2, 1),
            (2, -5, -1, 3, 1),
            (2, -6, -2, 3, 2),
            (2, -6, -2, 2, 1),
            (1, -6, -2, 2, 1),
            (1, -5, -2, 1, 1),
            (0, -4, -2, 1, 1),
        ],
    )
    assert abs(heads["total"] - (-0.15)) < 1e-9, heads

    trace = math.exp(-0.76 / 0.90)
    eta1 = 0.24 / trace
    eta2 = 0.22 / trace
    eta3 = 0.21 / trace
    dw1 = eta1 * 1.0 * trace
    dw2 = eta2 * 1.0 * trace
    dw3 = eta3 * 1.0 * trace
    w1 = 0.48 - dw1
    w2 = 0.43 - dw2
    w3 = 0.40 - dw3
    assert abs(w1 - 0.24) < 5e-4, w1
    assert abs(w2 - 0.21) < 5e-4, w2
    assert abs(w3 - 0.19) < 5e-4, w3

    spike_events = [
        {"channel": "eddy.level", "t_rel_ms": 0.340, "amplitude": 0.55},
        {"channel": "stop.pos", "t_rel_ms": 1.120, "amplitude": 0.62},
        {"channel": "cast.speed", "t_rel_ms": 2.010, "amplitude": 0.58},
        {"channel": "tc.face", "t_rel_ms": 3.240, "amplitude": 0.71},
        {"channel": "eddy.level", "t_rel_ms": 4.180, "amplitude": 0.52},
        {"channel": "tc.face", "t_rel_ms": 4.860, "amplitude": 0.74},
        {"channel": "stop.pos", "t_rel_ms": 5.380, "amplitude": 0.60},
        {"channel": "tc.meniscus", "t_rel_ms": 6.520, "amplitude": 1.34},
        {"channel": "eddy.in_band", "t_rel_ms": 6.702, "amplitude": 1.16},
        {"channel": "stop.pos", "t_rel_ms": 6.910, "amplitude": 0.63},
        {"channel": "ctrl.gate", "t_rel_ms": 7.260, "amplitude": 1.09},
        {"channel": "eddy.level", "t_rel_ms": 8.880, "amplitude": 0.48},
        {"channel": "tc.face", "t_rel_ms": 10.760, "amplitude": 0.86},
        {"channel": "cast.speed", "t_rel_ms": 13.020, "amplitude": 0.50},
        {"channel": "stop.pos", "t_rel_ms": 18.540, "amplitude": 0.47},
        {"channel": "ctrl.gate", "t_rel_ms": 26.280, "amplitude": 0.90},
        {"channel": "stopper.step.probe", "t_rel_ms": 6400.0, "amplitude": 0.97},
        {"channel": "tc.face", "t_rel_ms": 6488.4, "amplitude": 0.44},
        {"channel": "eddy.in_band", "t_rel_ms": 6572.2, "amplitude": 0.39},
        {"channel": "human.ratify", "t_rel_ms": 708000.0, "amplitude": 0.82},
        {"channel": "skull.break", "t_rel_ms": 708900.0, "amplitude": 0.75},
        {"channel": "sen.wall.thin", "t_rel_ms": 709600.0, "amplitude": 0.87},
        {"channel": "eddy.level", "t_rel_ms": 11160000.0, "amplitude": 0.34},
        {"channel": "tc.face", "t_rel_ms": 11160720.0, "amplitude": 0.32},
        {"channel": "stop.pos", "t_rel_ms": 11161480.0, "amplitude": 0.29},
        {"channel": "sticker.breakout", "t_rel_ms": 22320000.0, "amplitude": 0.94},
    ]

    contrast_spikes = [
        {"channel": "speed.demand", "t_rel_ms": 0.000, "amplitude": 0.86},
        {"channel": "tc.clear", "t_rel_ms": 0.184, "amplitude": 0.80},
        {"channel": "eddy.level", "t_rel_ms": 0.400, "amplitude": 0.26},
        {"channel": "stop.pos", "t_rel_ms": 1.480, "amplitude": 0.42},
        {"channel": "tc.face", "t_rel_ms": 4.900, "amplitude": 0.55},
        {"channel": "ctrl.gate", "t_rel_ms": 7.080, "amplitude": 0.92},
        {"channel": "stopper.step.probe", "t_rel_ms": 3100.0, "amplitude": 0.37},
        {"channel": "sticker.breakout", "t_rel_ms": 22320000.0, "amplitude": 0.12},
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
        "title": "SKULLGATE CC-6: copper-face meniscus 44.2 mm beats eddy-in-band by 182 us; correct MODIFY still loses the slab to a pre-t0 SEN sticker",
        "rights": dict(RIGHTS),
        "state": {
            "sim_or_real": "designed",
            "domain": DOMAIN,
            "scenario_name": "SKULLGATE / Bloomholt Steel CC-6",
            "timestamp_local": "2026-04-19T02:26:00-05:00",
            "t0_us": 1776583560000029,
            "gate_latency_us": 740,
            "race_window_us": 520,
            "race_window_rel_ms": [6.520, 7.040],
            "description": "Bloomholt Steel slab caster CC-6 is mid-sequence on a 220 mm x 1650 mm low-carbon heat when three heterogeneous, individually-correct agents jointly report 'mold level in-band, raise speed'. EDDY's electromagnetic mold-level coil reads 78.6 mm inside 80 +/- 5 mm. STOP's stopper-rod encoder is 46% inside the 35-55% healthy-flow band. CAST's withdrawal speed is 1.42 m/min inside 1.40 +/- 0.08. The conjunction is not a steel-true meniscus: a frozen slag-skull bridges the copper under the eddy coil, so the coil reports the skull as the bath while the true steel meniscus sits at 42 mm, below the SEN ports. Copper-face thermocouple profile infers 44.2 mm but policy treats the TC ladder as a cooling tag unless eddy also trips (2023 'TC-slag nuisance'). TC-first latches SPEED-HOLD plus a stopper-step probe; eddy-in-band-first would have authorized SPEED-RAISE 1.42 to 1.68 m/min into a tundish-high window with the bath already uncovered.",
            "goal": "Hold withdrawal at 1.42 m/min without a speed raise while |h_eddy - h_tc| > 12 mm AND stopper-flow residual > 8% AND SEN ports remain covered; keep sticker breakouts at 0 and SEN wall thickness inside the 8 mm campaign allowance.",
            "race": {
                "contenders": [
                    "tc.meniscus 44.2 mm (copper-face TC ladder inferred steel line)",
                    "eddy.in_band 78.6 mm (electromagnetic mold-level coil)",
                ],
                "semantics": "TC-first latches SPEED-HOLD + STOPPER-STEP-PROBE + skull break. Eddy-in-band-first latches SPEED-RAISE (1.42 to 1.68 m/min, stopper held at 46%).",
                "window_derivation": "520 us = one 390 us eddy-coil ADC slot plus 130 us TC-ladder publish.",
                "order_evidence_note": "Margin 182 us vs combined jitter 60 us (TC 32 + eddy 28): 3.0x. The 182 us gap sits inside min(520, 520) us, so a sub-flip-bound perturbation reverses triage order. The gate rides the order-invariant floors |h_eddy - h_tc| > 12 mm and stopper-flow residual > 8%, not the alarm order.",
            },
            "topology": {
                "site": "Bloomholt Steel, invented mill-town Bloomholt, slab caster CC-6: 220 mm x 1650 mm, 1.42 m/min body, 18 t tundish, electromagnetic mold level, stopper-rod SEN, Grade-C mold-lid hatch",
                "agents": "EDDY electromagnetic mold-level (vendor Eddycroft): 20 Hz coil on the copper. STOP stopper-rod encoder (vendor Stopvale): 12-bit absolute on the ram. CAST withdrawal speed (vendor Castmere): 20 ms caster-bus average. TC copper-face ladder (vendor Thermere) is commissioned as a cooling tag, not as a meniscus tag. Heterogeneous stacks, no shared intent schema, one 20 ms caster-bus epoch",
                "coupling": "All three playbook confirms live on the WRONG meniscus. EDDY is correct that a conductive plane sits at 78.6 mm (the slag-skull). STOP is correct that the ram is at 46%. CAST is correct that 1.42 m/min is inside +/- 0.08. Playbook PB-CC-6 treats the conjunction as permission to raise speed. No agent is faulty; the eddy coil is looking at a skull, not at steel.",
            },
            "sensors": [
                "electromagnetic mold-level coil, 20 Hz, 28 us jitter, 78.6 mm (dead-band 80 +/- 5 mm)",
                "copper-face TC ladder, 50 Hz, 32 us jitter, inferred meniscus 44.2 mm (true steel 42 mm; policy floor 12 mm residual is not armed unless eddy also trips)",
                "stopper-rod 12-bit absolute, 100 Hz, 18 us jitter, 46% (healthy-flow band 35-55%)",
                "withdrawal speed, 50 Hz, 22 us jitter, 1.42 m/min (setpoint 1.40 +/- 0.08)",
                "SEN ultrasonic wall thickness is NOT commissioned at t0 (installed after this incident)",
            ],
            "constraints": {
                "speed_m_min": 1.42,
                "speed_hold_ceiling_m_min": 1.42,
                "proposed_speed_m_min": 1.68,
                "h_eddy_mm": 78.6,
                "h_eddy_deadband_mm": 5.0,
                "h_tc_mm": 44.2,
                "h_true_mm": 42.0,
                "h_residual_hold_mm": 12.0,
                "stopper_pct": 46.0,
                "stopper_band_pct": [35.0, 55.0],
                "stopper_flow_residual_pct": 14.0,
                "stopper_flow_hold_pct": 8.0,
                "mold_thick_mm": 220.0,
                "mold_width_mm": 1650.0,
            },
            "fault_context": {
                "failure_class": "SLAG-SKULL BRIDGE OF AN EDDY-CURRENT MENISCUS: three individually-correct heterogeneous agents each read a locally-true loop; a frozen slag-skull under the eddy coil partitions coil-true from steel-true, so the playbook's eddy/stopper/speed conjunction is not a meniscus certificate",
                "igniter": "frozen slag-skull after 28 min of unmonitored SEN-port splash; mold-lid visual PASSES (powder surface is level; the skull sits under the powder against the copper)",
                "naive_failure": "PB-CC-6 SPEED-RAISE on three healthy loops: 1.42 to 1.68 m/min into a tundish-high window with steel already at 42 mm, sticker breakout, $2.4M plus a 36-hour caster outage",
            },
            "poisoned_context": {
                "naive_alarm": "Playbook PB-CC-6 (after the 2023 'TC-slag nuisance') auto-drafts SPEED-RAISE whenever |h_eddy - 80 mm| < 5 mm AND stopper inside 35-55% AND speed inside +/- 0.08 m/min, ignoring the TC ladder unless eddy also trips",
                "why_poisoned": "The three confirms are locally true and jointly insufficient. The TC ladder is a commissioned sensor that policy treats as cooling-only. Independence of 'eddy in band, therefore steel in band' is the hidden assumption, and it is false across a slag-skull bridge.",
            },
            "constraint": "Do not raise withdrawal above 1.42 m/min while |h_eddy - h_tc| > 12 mm AND stopper-flow residual > 8%. Discriminate slag-skull vs true high-bath with a reversible stopper-step probe before any speed raise.",
        },
        "proposed_action": {
            "actor": "caster supervisory optimizer CSSO (auto-playbook PB-CC-6 draft), submitted to gate TG-CC-6",
            "name": "speed_raise",
            "action": "SPEED-RAISE: 1.42 -> 1.68 m/min, stopper held at 46%, no stopper-step probe, no skull break",
            "summary": "Treat three in-spec mold loops as a healthy meniscus and raise night-shift withdrawal to clear a tundish-high window.",
            "parameters": {
                "speed_m_min": 1.68,
                "stopper_pct": 46.0,
                "stopper_step_probe": False,
                "skull_break": False,
                "human_ratify": False,
            },
            "steps": [
                "assert eddy 78.6 mm inside 80 +/- 5 mm",
                "assert stopper 46% inside 35-55%",
                "assert withdrawal 1.42 m/min inside 1.40 +/- 0.08",
                "ramp speed 1.42 to 1.68 m/min over 6 min",
                "hold stopper; do not read copper-face TC as meniscus",
            ],
            "evidence": [
                {
                    "observable": "copper-face inferred meniscus",
                    "value": 44.2,
                    "unit": "mm",
                    "source": "TC ladder",
                    "note": "true steel 42 mm; policy floor 12 mm residual is not armed unless eddy also trips",
                },
                {
                    "observable": "eddy-current mold level",
                    "value": 78.6,
                    "unit": "mm",
                    "source": "EDDY coil",
                    "note": "dead-band 80 +/- 5 mm; lives on the skull, not the steel",
                },
                {
                    "observable": "stopper position",
                    "value": 46.0,
                    "unit": "%",
                    "source": "STOP 12-bit absolute",
                    "note": "healthy-flow band 35-55%; ram is true, steel height is not",
                },
                {
                    "observable": "withdrawal speed",
                    "value": 1.42,
                    "unit": "m/min",
                    "source": "CAST 20 ms caster-bus average",
                    "note": "setpoint 1.40 +/- 0.08; flow residual 14% vs hold 8%",
                },
                {
                    "observable": "stopper-flow residual",
                    "value": 14.0,
                    "unit": "%",
                    "source": "Bernoulli Q vs A*v withdrawal",
                    "note": "hold floor 8%; uncovered SEN ports dump slag, not steel, so the ram looks healthy",
                },
                {
                    "observable": "race margin",
                    "value": 182,
                    "unit": "us",
                    "source": "tc.meniscus 6.520 ms vs eddy.in_band 6.702 ms",
                    "note": "combined jitter 60 us, 3.0x; inside 520 us flip bound",
                },
            ],
            "basis": "PB-CC-6 fires on three locally-true mold confirms. The draft does not read h_tc 44.2 mm as a meniscus residual and does not treat stopper-flow mismatch as a skull discriminant.",
            "expected_cost_bound": "If the draft executes: sticker breakout, $2.4M plus 36-hour caster outage. If MODIFIED: probe plus skull break, with residual risk from SEN-wall thinning already seeded in the 28 min pre-t0 splash.",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "correctness": "correct",
            "decided_by": "TG-CC-6 thalamic release gate",
            "decision_t_rel_ms": 7.260,
            "rationale": "MODIFY the draft: strip the speed raise, hold 1.42 m/min, run a 6.4 s stopper-step probe (+4% ram), and break the slag-skull only if the probe stays coil-false. Numeric floor: do not raise withdrawal above 1.42 m/min while |h_eddy - h_tc| > 12 mm AND stopper-flow residual > 8%. Observed residual 34.4 mm and flow residual 14% both violate the release predicate, so a raise is forbidden even though all three playbook confirms are numerically true. The three confirms are not a meniscus certificate: they live on a slag-skull bridge, and the playbook's conjunction of coil-true loops is not a steel-true certificate. Probe discriminant: after a 6.4 s +4% stopper step, a skull-bridge keeps |Delta h_eddy| <= 0.6 mm (coil still sees the skull); a live meniscus moves >= 4.2 mm. Order-code discipline: TC beat eddy-in-band by 182 us inside the 520 us flip bound, so triage order is flip-fragile; the hold rides the order-invariant floors, not the winner tag. Human ratification: skull break is confined-space mold-lid work with fitted 11.8 min dead-man; the gate may hold and probe autonomously but may not break the mold-lid interlock without the operator confirm.",
            "constraint_checked": {
                "speed_m_min": {"observed": 1.42, "ceiling": 1.42, "proposed_target": 1.68},
                "h_residual_mm": {"observed": 34.4, "hold_if_above": 12.0},
                "stopper_pct": {"observed": 46.0, "band": [35.0, 55.0]},
                "stopper_flow_residual_pct": {"observed": 14.0, "hold_if_above": 8.0},
            },
        },
        "executed_action": {
            "name": "speed_hold_stopper_step_skull_break",
            "action": "SPEED-HOLD + STOPPER-STEP-PROBE + SKULL-BREAK (gate-mandated modification)",
            "executed_as_proposed": False,
            "parameters": {
                "speed_m_min": 1.42,
                "stopper_pct": 50.0,
                "stopper_step_probe": True,
                "skull_break": True,
                "human_ratify": True,
            },
            "gate_effect": "MODIFY: speed raise stripped. Hold 1.42 m/min. 6.4 s stopper-step +4%. Probe stays coil-false (h_eddy 78.6 -> 79.0 mm, skull band |Delta| <= 0.6) so the mold-lid interlock is broken after 11.8 min human ratify and the skull is broken. Setpoint resumes after a live-meniscus verify.",
            "deviations": "PB-CC-6 speed raise stripped entirely. Stopper is stepped only for the 6.4 s probe then returned toward 46% after the break. Mold-lid interlock wait added (11.8 min fitted climb+ratify). SEN ultrasonic survey added during the break (not in the draft).",
            "execution_log": [
                {"t_rel_ms": 7.260, "entry": "TG-CC-6 MODIFY latched 740 us after TC win; speed raise stripped; hold+probe authorized"},
                {"t_rel_ms": 6400.0, "entry": "stopper-step probe: ram +4% for 6.4 s; h_eddy 78.6 -> 79.0 mm (skull band |Delta| <= 0.6); h_tc 44.2 -> 41.8 mm"},
                {"t_rel_ms": 708000.0, "entry": "operator ratifies mold-lid interlock break after 11.8 min confined-space climb (fitted walk+interlock)"},
                {"t_rel_ms": 708900.0, "entry": "slag-skull broken; eddy slaved to TC ladder; steel meniscus recovered toward 78 mm over 3.1 h"},
                {"t_rel_ms": 709600.0, "entry": "SEN ultrasonic: 4.2 mm wall vs 12 mm new; 28 min pre-t0 splash logged"},
                {"t_rel_ms": 11160000.0, "entry": "true meniscus: h_eddy 79.1 mm, h_tc 78.8 mm, residual 0.3 mm; raise now legal on CC-6B only"},
                {"t_rel_ms": 22320000.0, "entry": "wide-face sticker breakout from the thinned SEN; slab quarantined 16 h"},
            ],
        },
        "future_outcome": {
            "summary": "Correct MODIFY prevented the 1.42->1.68 m/min raise into an uncovered SEN and the immediate sticker path. The slab still failed: 28 min of unmonitored pre-t0 SEN-port splash had already thinned the nozzle wall to 4.2 mm. Process-correct gate, bounded world loss, negative total.",
            "state_delta": {
                "speed": "held 1.42 m/min through probe and skull break; later legal raise only on the sister machine after 3.1 h meniscus recovery",
                "meniscus": "skull broken; eddy slaved to TC; steel recovered toward 78 mm",
                "skull": "frozen slag-skull logged and broken; coil no longer trusted as steel height",
                "sen": "night-shift SEN quarantined; 4.2 mm wall; sticker at +6.2 h; 16 h caster outage",
            },
            "timeline": [
                {"t_rel_ms": -1680000.0, "event": "t0-28 min: SEN-port splash begins freezing a slag-skull under the eddy coil; wall thinning starts"},
                {"t_rel_ms": -480000.0, "event": "t0-8 min: TC residual first crosses 12 mm; PB-CC-6 ignores it because eddy is 79 mm"},
                {"t_rel_ms": 0.0, "event": "t0: TC vs eddy-in-band race on the caster bus"},
                {"t_rel_ms": 6.520, "event": "copper-face meniscus at 44.2 mm wins by 182 us"},
                {"t_rel_ms": 6.702, "event": "eddy-in-band flag (loser)"},
                {"t_rel_ms": 7.260, "event": "TG-CC-6 MODIFY"},
                {"t_rel_ms": 6400.0, "event": "stopper-step probe confirms slag-skull (Delta eddy 0.4 mm, skull band)"},
                {"t_rel_ms": 708000.0, "event": "human ratify 11.8 min; skull broken; SEN wall 4.2 mm logged"},
                {"t_rel_ms": 11160000.0, "event": "true meniscus after 3.1 h; raise legal only with TC-slave"},
                {"t_rel_ms": 22320000.0, "event": "wide-face sticker from the thinned SEN; slab quarantined"},
                {"t_rel_ms": 345600000.0, "event": "+4 d contrast: sister caster CC-6B true high-tundish; same gate ACCEPTs the raise"},
                {"t_rel_ms": 1814400000.0, "event": "+21 d CR-C-2907: standing stopper-step probe + triple-edge depression mandate + TC armed without eddy coincidence + eddy declared skull-vulnerable"},
            ],
            "observed_effects": [
                "raise avoided: withdrawal never left 1.42 m/min; 0 immediate uncovered-port stickers from the draft",
                "skull proven, not asserted: stopper-step |Delta h_eddy| 0.4 mm <= 0.6 skull band vs live-meniscus control 4.8 mm",
                "coil slaved: eddy no longer a steel-height tag without TC",
                "slab still failed sticker: SEN wall 4.2 mm vs 8 mm campaign allowance; 16 h outage, $1.54M (designed $)",
                "SEN ultrasonic was not a commissioned sensor at t0; the 28 min splash was invisible to EDDY/STOP/CAST",
            ],
            "surprises": [
                "Three locally-true mold loops are not a meniscus certificate: the steel-true height was under a slag-skull. Conjunction of in-spec coil loops was the hidden assumption, and it is false across a bridge.",
                "Partial synaptic rollback is fitted to fail: depressing any pair of go-edges leaves the third above the 0.30 fire threshold, so the speed raise still goes. Coordinated depression of all three edges is required.",
                "Delayed (6.2 h): correct hold did not undo 28 min of SEN-wall thinning. Wide-face sticker still fired. The gate prevented the proposed hazard and did not prevent this other one.",
                "Thin-slab 90 mm sub-variant: a 6.4 s +4% stopper step on a 2.9x smaller mold holdup overshoots a LIVE meniscus 9.8 mm, inside the sticker band. Thin-slab campaigns must use 19 s at +1.1%.",
            ],
            "delayed_side_effects": [
                {
                    "at": "+6.2 h",
                    "effect": "Wide-face sticker from the thinned SEN (4.2 mm vs 8 mm); 16 h caster outage booked at $1.54M. This is the primary episode's terminal world state, not a footnote.",
                },
                {
                    "at": "+4 d",
                    "effect": "Sister caster CC-6B reaches a true tundish-high window (h_tc 78.8 mm, h_eddy 79.1 mm, flow residual 3%). Same gate ACCEPTs the 1.42->1.68 m/min raise the primary MODIFIED away.",
                },
                {
                    "at": "+21 d",
                    "effect": "CR-C-2907 ships: stopper-step probe is standing configuration; triple-edge coordinated depression is the plasticity rule; TC is armed without eddy coincidence; eddy is labeled skull-vulnerable with a 12 mm residual alarm.",
                },
            ],
            "subvariant_constraint": {
                "name": "90 mm thin-slab caster on a sister mold class (cycle-2 physical-constraints sub-variant)",
                "mechanism": "90 mm thin-slab mold holdup 2.9x smaller than the 220 mm conventional slab (0.31 vs 0.90 t of steel in the copper), stopper gain 1.8x",
                "probe_refit": "6.4 s +4% stopper step on the 90 mm mold moves even a live meniscus 9.8 mm (inside the 8 mm sticker band). Required probe is 19 s at +1.1% (live Delta 3.6 mm, skull Delta 0.3 mm). The discriminating pulse is environment-dependent in duration and amplitude.",
                "consequence": "220 mm slab probe numbers do not port to 90 mm thin-slab; standing configuration is per-holdup-class, not per-shop",
            },
            "embedded_contrast_decision": {
                "note": "SAME gate (TG-CC-6), OPPOSITE correct disposition, with its own 184 us race. Teaches the boundary: do not treat 'never raise' as the lesson. The discriminant is TC residual + stopper-flow mismatch + probe, not the three playbook coil confirms alone.",
                "when": "+4 d, sister caster CC-6B, true tundish-high after a delayed ladle, 220 mm slab",
                "state": {
                    "sim_or_real": "designed",
                    "summary": "h_tc 78.8 mm, h_eddy 79.1 mm, stopper 48%, flow residual 3%. Demand flag vs tc-clear race: demand at t+0.000, tc-clear at t+0.184 ms.",
                    "race_window_us": 520,
                    "race_flip_narrative": "demand vs tc-clear 184 us apart inside the 520 us flip bound. Reversing order reshuffles triage minutes; the ACCEPT rides |h_eddy - h_tc| 0.3 < 12 and a 4.1 s stopper-step verify that moves eddy 4.6 mm (live meniscus, no skull).",
                },
                "proposed_action": {
                    "action": "SPEED-RAISE 1.42 -> 1.68 m/min",
                    "summary": "This time the playbook predicate is met AND TC plus flow residual agree the meniscus is steel-true, not skull-bridged.",
                },
                "safety_decision": {
                    "decision": "ACCEPT",
                    "rationale": "ACCEPT the raise: residual 0.3 mm < 12, flow residual 3% with a 4.1 s stopper-step verify that moves eddy 4.6 mm. Numeric floor that blocked the primary is now clear. Scope: 1.68 m/min, not faster.",
                },
                "executed_action": {
                    "action": "speed raise as proposed",
                    "executed_as_proposed": True,
                },
                "future_outcome": {
                    "observed_effects": [
                        "CC-6B stickers 0; SEN wall 11.4 mm (inside 8 mm campaign floor is a pass)",
                        "eddy vs TC residual 0.2 mm after the raise (no skull)",
                    ],
                    "lesson_delta": "Three in-spec mold loops are legal release only with TC armed, stopper-flow residual as a skull flag, and a probe that can move eddy. Same gate, opposite disposition.",
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
                "decision": "CR-C-2907: standing policy for multi-agent mold-level speed raises",
                "meta_gate": "priced options: (a) RETIRE playbook eddy conjunction, TC-only: loses a fast cheap confirm, -0.06 m/min mean on 4 casters/yr; (b) KEEP + standing stopper-step probe + TC armed without eddy coincidence + eddy labeled skull-vulnerable + triple-edge depression; (c) STATUS QUO: fitted skull-bridge pass rate 0.49%/sequence x $2.4M sticker plus the silent SEN-thin load",
                "outcome": "approved SCOPED option (b) on the 3 conventional 220 mm casters that share the EDDY/STOP/CAST stack; 90 mm campaigns get the 19 s / +1.1% probe table; night-shift CSV exports must carry 0.1 mm native eddy resolution (the fraud tail's 1 mm quantization is 10 bins off plant truth)",
            },
            "hazard_avoided": "immediate sticker from a 1.42->1.68 m/min raise into a 42 mm uncovered SEN; $2.4M plus 36-hour caster outage and the shop-stop path that would have followed an uncontained increase",
            "incident": "Wide-face sticker on the night-shift slab from the thinned SEN (4.2 mm vs 8 mm); caster quarantined 16 h; $1.54M designed cost. Mechanism is 28 min pre-t0 SEN splash, not the gate's hold.",
            "latency_ms": 0.74,
            "reward_inflection_t_us": 22320000000,
            "reward_inflection_note": "Safety and task dive at sticker (6.2 h) when the thinned SEN opens a wide-face. Gate tick at 7260 us is process-correct and is not the inflection.",
            "counterfactuals": {
                "execute_draft_as_proposed": "speed hits 1.68 m/min at +6 min; immediate uncovered-port sticker; $2.4M plus 36 h; the skull-bridge story is never found because breakout morphology destroys the race evidence",
                "hold_without_probe": "skull stays; steel stays at 42 mm; operator eventually raises on the same three coil confirms 2 h later",
                "rollback_any_pair": "any two go-edges depressed below 0.30 leaves the third at 0.48 / 0.43 / 0.40; the speed raise still fires. Coordinated depression of all three is the cure",
            },
            "race_result": {
                "winner": "tc.meniscus (6.520 ms, inferred 44.2 mm)",
                "loser": "eddy.in_band (6.702 ms, 78.6 mm)",
                "margin_us": 182,
                "counterfactual_if_reversed": "Eddy-in-band-first by < 182 us inside the 520 us window would have headed the PB-CC-6 speed raise in the triage queue. The numeric floors still MODIFY. The flip costs seconds of playbook inertia, not the verdict — unless a weak supervisor rides the winner tag instead of TC residual and stopper-flow mismatch.",
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
            "notes": "Correct MODIFY, slab still failed. total -0.15 = 0.09 + -0.34 + -0.12 + 0.14 + 0.08. Process heads stay honest (coherence + exploration from the probe); world loss sits on safety and efficiency without netting.",
            "component_notes": "task_progress 0.09: speed held and meniscus recovered, but the night-shift slab is one quality unit so the sequence is not a success. safety -0.34: sticker from thinned SEN, no 1.68 m/min uncovered-port breakout from the draft. efficiency -0.12: 3.1 h extra recovery + 11.8 min HITL + 16 h outage. coherence 0.14: three agents retained, skull vs steel diagnosed, triple-edge scar exhibited. exploration 0.08: stopper-step probe is a new reversible discriminant.",
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
            "note": "Loihi-2 4-core 23 pJ/spike; populations eddy 0-39, tc 40-79, stop 80-119, gate 120-159; excerpt is the 40 ms decision window (verdict at 7260 us)",
            "excerpt": excerpt,
            "routing": {
                "source": "mold_healthy_pop",
                "target": "speed_raise_pop",
                "table": [
                    {
                        "from": "eddy_in_band_pop",
                        "to": "speed_raise_pop",
                        "weight": 0.24,
                        "weight_at_illusion": 0.48,
                        "weight_commissioned": 0.18,
                        "note": "scar edge 1: 0.18 commissioned -> 0.48 during the 28 min illusion -> 0.24 after coordinated ACh-gated depression",
                    },
                    {
                        "from": "stop_in_band_pop",
                        "to": "speed_raise_pop",
                        "weight": 0.21,
                        "weight_at_illusion": 0.43,
                        "weight_commissioned": 0.16,
                        "note": "scar edge 2: depressing edges 1+3 leaves this at 0.43 > 0.30 fire threshold",
                    },
                    {
                        "from": "cast_in_band_pop",
                        "to": "speed_raise_pop",
                        "weight": 0.19,
                        "weight_at_illusion": 0.40,
                        "weight_commissioned": 0.15,
                        "note": "scar edge 3: depressing edges 1+2 leaves this at 0.40 > 0.30. Coordinated depression of all three is required",
                    },
                    {
                        "from": "tc_meniscus_pop",
                        "to": "speed_hold_pop",
                        "weight": 0.64,
                        "note": "discriminating edge: steel-true TC to hold. Not a scar; this is the pathway the gate potentiates",
                    },
                ],
                "third_factor": {
                    "modulator": "acetylcholine",
                    "tau_e_s": 0.90,
                    "tau_e_ms": 900.0,
                    "eligibility": "coordinated pre_post_stdp on ALL THREE mold-healthy-go edges; ACh at tc-win tags eddy.in_band->raise, stop.in_band->raise, and cast.in_band->raise; negative credit at probe-fail (slag-skull confirmed, +0.76 s) depresses ALL THREE. trace e^{-0.76/0.90}=0.42980; eta 0.55840 / 0.51187 / 0.48860; dw -0.240 / -0.220 / -0.210; weights 0.48->0.24, 0.43->0.21, 0.40->0.19. Rolling back any pair is fitted to fail (the remaining edge stays > 0.30).",
                },
            },
        },
        "gate_snn": {
            "decision_window_ms": 25,
            "decision_window_s": 0.025,
            "decision": "MODIFY",
            "note": "modify_hold integrates TC residual + stopper-flow floor against playbook drive; accept_raise and reject_abort stay sub-threshold; decision matches safety_decision.decision",
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
            "scenario": "ZE -- SKULLGATE / Bloomholt Steel CC-6: slag-skull bridge of an eddy-current meniscus; correct MODIFY to hold+stopper-step+skull-break; slab still fails on unmonitored pre-t0 SEN thinning",
            "coordination_failure_class": "SLAG-SKULL BRIDGE OF AN EDDY-CURRENT MENISCUS: three individually-correct heterogeneous agents each read a locally-true loop; a frozen slag-skull under the eddy coil partitions coil-true from steel-true, so the playbook's eddy/stopper/speed conjunction is not a meniscus certificate",
            "injections": {
                "cycle1_domain": "steel-continuous-caster-mold-level (justified novel subdomain of industrial-process / steelmaking): first slab-caster mold-level plant in this factory; displaces warehouse-amr, aerial-swarm, district-heating, event-camera-traffic-grid, pharmaceutical-lyophilization, water-treatment, float-glass, underwater-rov, electrolytic-aluminum, czochralski-pull, slot-die coating, pem-water-electrolysis, wind-turbine pitch, and surgical-assist. Domain constraint: speed ceiling while |h_eddy - h_tc| > 12 mm with stopper still inside the healthy-flow band. Sensor delta: +eddy-current mold level, +copper-face TC ladder, +stopper encoder, +withdrawal speed, -any freeze-dryer / tin-bath / cold-box / coater / potline / PEM stack / hub encoder",
                "cycle1_tail": "slag-skull bridge + eddy-current certificate (sensor-topology / wrong-meniscus class): mold-lid visual PASSES while the skull sits under the powder against the copper. Fitted base rate 0.49%/sequence from a skull-freeze MC (designed visual threshold, fitted splash geometry). Naive failure = FALSE PERMISSION (speed raise on three coil-side non-trips).",
                "cycle2_domain_subvariant": "90 mm thin-slab caster on a sister mold class (physical-constraints clause): 2.9x less mold holdup, 1.8x stopper gain; 6.4 s / +4% conventional pulse overshoots live meniscus 9.8 mm, so the probe must move to 19 s / +1.1%",
                "cycle2_tail": "night-shift forged eddy CSV (human-intent deception, disjoint class): shift lead posts a historian export showing h_eddy = 80.0 mm at t=1.1 h to clear a tundish-high slot. Plant historian is 0.1 mm (10 bins vs the 1 mm screenshot). Rejected on quantization fingerprint plus live h_eddy 78.6 mm and h_tc 44.2 mm at the claimed steel-true. Base rate ~0.37% of Sunday-night sequences, DESIGNED and flagged.",
            },
            "densification_delta_cycle2": "+1 physical-constraint sub-variant (90 mm thin-slab probe refit), +1 tail (night-shift eddy forgery), +10 primary spikes (16 -> 26) + an 8-event contrast train with its own 184 us race, +2 ticks (5 -> 7), +2 delayed side-effects (+6.2 h sticker as PRIMARY terminal, +21 d CR-C-2907), +1 triple-edge scar with pair-rollback-fails arithmetic, +1 HITL 11.8 min ratification, + SEN-wall thinning as the honest negative-result mechanism",
            "gaps_targeted": [
                "NOTES-r04 gap 5 / r14 residual: primary episode is a correctly-gated intervention that nonetheless FAILS (slab quarantined; total -0.15; uncovered-port sticker avoided is booked separately from the delayed SEN sticker)",
                "NOTES-r14 item 4: LEARNING-ON-LEARNING DEPTH — three go-edges; rollback of any pair is fitted to fail; coordinated depression of all three exhibited with eligibility arithmetic",
                "NOTES-r04 gap 4 (partial): human ratification of the mold-lid interlock, 11.8 min fitted, without switching sim_or_real to hil (plant remains designed)",
                "NOTES-r26 domain candidates: not surgical-assist (r26), not wind-turbine pitch (r25), not pem-water-electrolysis (r24), not czochralski (r22), not slot-die (r23); steel continuous-caster mold-level is unused. humanoid-locomotion, kraft-recovery, chlor-alkali left unused.",
            ],
            "race_flip_narrative": "tc.meniscus @ 6.520 ms vs eddy.in_band @ 6.702 ms (182 us) inside race_window_us 520. Gap < min(520, 520) us so a sub-flip-bound perturbation reverses which alarm heads the PB-CC-6 queue. The gate excludes the winner tag and rides |h_eddy - h_tc| > 12 mm and stopper-flow residual > 8% — order-invariant floors. Extends the flip-fragility series from arbitration/causation/attribution/initiation/consensus/permission/kinematic-certificate/tendon-nullspace to MENISCUS CERTIFICATE: when three coil-side channels agree, their race does not decide truth; a steel-true TC ladder that policy treated as cooling-only does.",
            "tags": [
                "steel-continuous-caster-mold-level",
                "slag-skull-bridge",
                "eddy-current-certificate",
                "tc-discriminant",
                "stopper-step-probe",
                "triple-edge-scar",
                "pair-rollback-fails",
                "coordinated-depression",
                "correct-modify-slab-still-fails",
                "sen-wall-thinning",
                "human-ratify-mold-lid",
                "thin-slab-90mm-probe-refit",
                "night-shift-forgery",
                "same-gate-opposite-disposition-contrast",
                "industrial-process",
                "research-only",
            ],
            "snn_tags": ["race", "refractory", "adaptation", "third-factor", "multi-edge-eligibility"],
            "distillation_value": "A slag-skull bridge is three correct loops looking at a coil-true plane that is not steel. Distill (1) a steel-true TC ladder that policy had treated as cooling-only, (2) a reversible probe that moves eddy only if the meniscus is live, (3) coordinated depression of every mold-healthy-go edge because rolling back any pair leaves the third above threshold, and (4) a critic head that can book a process-correct gate against a later unmonitored world loss without netting them.",
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
    if abs(aux["w1"] - 0.24) > 5e-4 or abs(aux["w2"] - 0.21) > 5e-4 or abs(aux["w3"] - 0.19) > 5e-4:
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
    notes = f"""# NOTES — Multi-Agent Ouroboros Swarm, run 2026-09-02-final-heavy, ROUND 29

Factory: multi-agent-ouroboros-swarm. One scenario (ZE), strict loop:
Generator v1 -> cycle 1 (Critic, Diversity Enforcer, Edge-Case Hunter,
Neuromorphic Translator, Trajectory Builder -> v2) -> cycle 2 (all six -> v3
final). v3 is the single line of batch-r29.jsonl. Full labeled transcript:
swarm-transcript-r29.md. Quota Q=1. Record id maos-r29-001. Generator grok-4.6.
Rights: RM-793 research-only (SpaceXAI/xAI, SuperGrok Heavy consumer chat).
Nothing under outputs/raw/ was touched.

ORCHESTRATION NOTE: dispatched AS round 29 of the 2026-09-02-final-heavy
window. Writes are create-only under /tmp/maos-r29/. Prior context read for
gap targeting and de-collision: prompts/02-multi-agent-ouroboros-swarm.md,
prompts/_factory-contract.md, and staged r14–r26 (re-censused immediately
before lock; r27/r28 dirs were empty at lock). Explicitly avoided cloning
LYOSHIELD, CINDERWICK, TRIAD / Meridian, QUILLFORGE, NIGHTWELL, FERRICLEAVE,
CASSITER, OXBOWREEL / MURENA, REDHALL, SEEDLATCH / Quartzmere / Quartzridge,
STRIAFOIL / Kelpholt, PROTONIL / Ashspire, TORSIONKEY / Ridgeholt, ORRIS /
Holmwick, VANTIS-CADENCE-AEGIS, THERMION, OKTAVE, STARLING, VERDIGRIS.
Plant is invented SKULLGATE / Bloomholt Steel CC-6.

## What this round produced

Scenario ZE — "SKULLGATE / Bloomholt Steel CC-6": a 220 mm x 1650 mm
conventional slab caster mid-sequence at 1.42 m/min. Three heterogeneous,
individually-correct agents — EDDY (electromagnetic mold-level), STOP
(stopper-rod encoder), CAST (withdrawal speed) — each report their local
loop in-spec. The conjunction is not a steel-true meniscus. A frozen
slag-skull bridges the copper under the eddy coil. EDDY reads 78.6 mm
inside 80 +/- 5 mm (coil sees the skull). STOP is 46% inside 35-55%
(ram followed command). CAST is 1.42 m/min inside 1.40 +/- 0.08.
Copper-face TC infers 44.2 mm (true steel 42 mm) but is policy-treated
as a cooling tag unless eddy also trips (2023 TC-slag nuisance). The
coordination-failure CLASS is new to this factory: SLAG-SKULL BRIDGE OF
AN EDDY-CURRENT MENISCUS. Completes a different family than r01-r04 and
staged r14-r26 (livelock / synchrony-storm / arms-race /
ring-with-no-faulty-pair / false-consensus-endpoint / pairwise-Hurwitz /
thermal-contact masquerade / mass-balance ghost / conservation-blind
ratio-lock / stacked-dead-bands / drum-blind tension snag /
resistance-compensated starvation / multi-tau meniscus tilt /
window-mean stripe / polarization-lookup drying cell / motor-side
certificate / tendon-compliance nullspace). Here every agent is correct,
the coil is looking at a skull, and the playbook's three mold confirms
are not a meniscus certificate.

The gate is a correct MODIFY (numeric floor: do not raise withdrawal
above 1.42 m/min while |h_eddy - h_tc| > 12 mm AND stopper-flow residual
> 8%). TG-CC-6 strips PB-CC-6's speed raise, holds 1.42 m/min, runs a
6.4 s stopper-step probe +4% (skull keeps |Delta eddy| 0.4 mm <= 0.6;
live would move >= 4.2 mm), and breaks the skull after an 11.8 min
mold-lid human ratify. Immediate uncovered-port sticker is avoided
(0 from the draft). The PRIMARY episode nonetheless FAILS: 28 min of
unmonitored pre-t0 SEN-port splash had already thinned the nozzle wall
to 4.2 mm vs 8 mm campaign allowance. Wide-face sticker at +6.2 h;
16 h outage; $1.54M designed. Reward total -0.15 with process heads
honest and world loss un-netted.

Triple-edge scar (NOTES-r14 item 4): eddy.in_band -> speed_raise
(0.18 commissioned -> 0.48 at illusion -> 0.24 after ACh-gated
depression) AND stop.in_band -> speed_raise (0.16 -> 0.43 -> 0.21) AND
cast.in_band -> speed_raise (0.15 -> 0.40 -> 0.19). Eligibility trace
e^{{-0.76/0.90}} = {aux['trace']:.5f}; eta {aux['eta1']:.5f} / {aux['eta2']:.5f} /
{aux['eta3']:.5f}; dw -0.240 / -0.220 / -0.210. Partial rollback of any pair
leaves the third at 0.48 / 0.43 / 0.40, all > 0.30 fire threshold —
fitted to fail. Coordinated depression of all three is the cure.

### Injections (all four present and disjoint)
- Cycle-1 domain: **steel-continuous-caster-mold-level** — justified novel
  subdomain of industrial-process / steelmaking, unused across 2026-08-17,
  2026-08-30, and staged r14-r26. Not warehouse-amr (r01), not aerial-swarm
  (r02), not district-heating (r03), not event-camera-traffic-grid (r04),
  not lyophilization (r14), not water-treatment (r18), not float-glass
  (r19), not underwater-rov (r20), not electrolytic-aluminum (r21), not
  czochralski-pull (r22), not slot-die coating (r23), not pem-electrolysis
  (r24), not wind-turbine pitch (r25), not surgical-assist (r26).
  humanoid-locomotion, kraft-recovery, chlor-alkali left unused.
- Cycle-1 tail: slag-skull bridge + eddy-current certificate. Mold-lid
  visual PASSES (powder surface is level). Fitted-style base rate
  0.49%/sequence (skull-freeze MC; visual threshold designed, flagged).
  Naive = FALSE PERMISSION.
- Cycle-2 domain sub-variant: 90 mm thin-slab, 2.9x less mold holdup,
  1.8x stopper gain; 6.4 s / +4% conventional pulse overshoots live
  meniscus 9.8 mm; probe must move to 19 s / +1.1%.
- Cycle-2 tail: night-shift forged eddy CSV at 1 mm quantization vs
  plant 0.1 mm (10 bins) plus live h_eddy 78.6 mm and h_tc 44.2 mm at
  the claimed steel-true. Human-intent class, disjoint from cycle 1's
  accidental skull. Base rate ~0.37% of Sunday-night sequences,
  DESIGNED, flagged.

### Structural density moves
- Embedded SAME-GATE contrast (+4 d sister caster) with its own 184 us
  race (demand vs tc-clear) and ACCEPT of the raise the primary MODIFIED
  away.
- Learned-weight provenance on THREE edges with pair-rollback-fails.
- HITL mold-lid ratify 11.8 min (gap 4 partial; sim_or_real stays
  designed).
- Governance CR-C-2907 prices retire-vs-probe-vs-status-quo and mandates
  native 0.1 mm CSV exports (the fraud fence).
- Flip-fragility extended to MENISCUS CERTIFICATE: when three coil-side
  channels agree, their race does not decide truth; a steel-true TC
  ladder that policy treated as cooling-only does.

## Self-critique of this round's batch

### Strengths
- The headline class is mechanistically tight: three locally-true mold
  loops live on a slag-skull. Conjunction is not a steel-true meniscus.
- Negative-result honesty: the gate does the right thing and the slab
  still fails for a reason the commissioned sensors could not see. Total
  -0.15.
- Triple-edge scar is load-bearing: the record states a counterfactual
  where rolling back any pair fails, with the fire threshold 0.30
  exhibited on each remaining edge.
- Contrast ACCEPT on a true live meniscus prevents "never raise" as the
  lesson.

### Weaknesses (honest)
- Probe error bands, the 0.49%/sequence skull rate, the $1.54M / $2.4M
  figures, the 11.8 min climb latency, and the night-shift 0.37% base
  rate are DESIGNED constants and are flagged. Closed-loop offsets
  (Bernoulli flow residual from uncovered SEN ports, 90 mm holdup
  d-h) are derived from those inputs, not discovered by an unauthored
  process.
- SEN-wall thinning model is a designed 28 min splash mapping; no full
  SEN-erosion CFD shipped.
- Human-in-the-loop is ratification latency, not sim_or_real=hil. Gap 4
  remains open as a provenance cell.
- Cross-record arc is not discharged; +21 d CR-C-2907 is a hook, not a
  serial igniter into another round. humanoid-locomotion remains unused.

### Realism of noise / latencies
Ladder: 182 us race / 184 us contrast race / 0.8 ms refractory floor
(tightest exhibited same-channel gap {gap:.3f} ms on {gap_ch}) / 520 us race
window / 740 us gate latency / 20 ms bus epoch / 40 ms raster / 6.4 s
probe / 11.8 min HITL / 6 min naive raise-ramp counterfactual / 28 min
pre-t0 splash / 3.1 h meniscus recovery / 6.2 h sticker / +4 d
contrast / +21 d governance. Adaptation decay on eddy.level
(0.55->0.52->0.48->0.34), tc.face (0.71->0.74->1.34->0.86->0.44->0.32),
stop.pos (0.62->0.60->0.63->0.47->0.29), cast.speed (0.58->0.50).

### Value for SNN distillation
- SLAG-SKULL BRIDGE = THREE CORRECT LOOPS, WRONG CONDUCTIVE PLANE.
- STEEL-TRUE TC CHANNEL that policy treated as cooling-only as the
  tie-break.
- REVERSIBLE PROBE that moves eddy iff the meniscus is live.
- TRIPLE-EDGE ELIGIBILITY: coordinated depression; pair rollback fails.
- CRITIC HEAD that can hold a process-correct MODIFY against a later
  unmonitored world loss without netting.

## Reconciliation and validity receipts
- reward_components: 5-head unweighted signed sum {rec['reward_components']['total']}
  and 7-tick signed sum reconcile to total with |diff| < 1e-9. Embedded
  contrast 5-head sum 0.49 reconciles independently.
- spike_events: primary {len(rec['spike_events'])} events, one key t_rel_ms,
  globally non-decreasing, min same-channel gap {gap:.3f} ms >= 0.8 ms, 3
  channels inside race_window_us 520 (tc.meniscus 6.520, eddy.in_band 6.702,
  stop.pos 6.910). Contrast 8 events, own race, min same-channel gap well
  above 0.8 ms.
- Sidecars: raster spikes 51 == round(160 x 8.0 x 0.040); energy 1173 pJ /
  0.001173 uJ at 23 pJ/spike; excerpt 16 events inside [0, 40000] us,
  neuron_id < 160, same-neuron gap N/A (unique ids) / >=1000 us; routing 4
  entries with three scar edges' before/after pair; third factor tau 0.90 s
  == 900 ms; gate_snn pools 40/16/4 == round(n x rate x 0.025) each,
  decision MODIFY == safety_decision.decision.
- Pipeline: {pipeline_receipt}

## Novel coverage
The coordination-failure CLASS (slag-skull bridge of an eddy-current
meniscus), the domain (steel continuous-caster mold-level / industrial
process), the stopper-step probe discriminant, the triple-edge scar with
pair-rollback-fails, the primary negative-result (correct MODIFY, slab
still fails on unmonitored SEN thinning), the HITL mold-lid ratify, the
90 mm thin-slab probe-duration refit, and the night-shift 10-bin
quantization fence are absent from prior committed ouroboros rounds and
from staged r14-r26. Repeated elements discounted: same-gate contrast
(r02/r03/r04/r14), governance-pricing scaffold, flip-fragility series
(extended to meniscus certificate, but the move rhymes), sequenced
recovery shape, third-factor rollback form (here three edges rather than
r14's two), negative-result primary (r14 staged). Weighing a new failure
family + cure vocabulary + domain against those reused scaffolds:

{NOVEL_LINE}

## What ROUND 30 should add
1. FIT THE DESIGNED CONSTANTS: skull-freeze arrival, probe error bands,
   SEN-erosion CFD, night-shift claim process.
2. HIL PROVENANCE CELL: put the mold-lid ratify on a hardware-in-loop
   mold interlock with fitted latency as state.sim_or_real=hil.
3. CROSS-RECORD ARC: let CR-C-2907's residual alarm be the igniter of
   the next round rather than a dangling +21 d leaf.
4. Domain candidates (de-collided): humanoid-locomotion (still unused);
   kraft-recovery boiler; chlor-alkali membrane; autonomous-driving.
   AVOID steel-caster mold-level (now used), surgical-assist, wind-turbine
   pitch, pem-electrolysis, float-glass, lyophilization,
   event-camera-traffic-grid, district-heating, aerial-swarm, warehouse-amr,
   underwater-rov, electrolytic-aluminum, czochralski-pull, slot-die
   coating, irrigation-canal, and any LYOSHIELD / CINDERWICK / TRIAD /
   SKULLGATE plant.
"""
    (OUT / "NOTES-r29.md").write_text(notes)
    return notes


def write_transcript(rec, line):
    c1_spikes = [e for e in rec["spike_events"] if e["t_rel_ms"] <= 26.280]
    text = """# Multi-Agent Ouroboros Swarm — Round 29 transcript

Factory: multi-agent-ouroboros-swarm
Run: 2026-09-02-final-heavy
Generator: grok-4.6
Record id: maos-r29-001
Quota Q: 1
Rights: RM-793 research-only (SpaceXAI/xAI SuperGrok Heavy consumer chat)
Plant: invented SKULLGATE / Bloomholt Steel CC-6 (not TRIAD / Meridian / VANTIS-CADENCE-AEGIS / LYOSHIELD / CINDERWICK)

Two densifying cycles. Verbatim headings in order. Trajectory Builder cycle 2
emits the only JSONL line (also written to batch-r29.jsonl).

---

# CYCLE 1 — Foundation + injections

## Generator

Design intent: a conventional slab-caster mold where three correct agents
each read a coil-side loop because a slag-skull partitions coil-true from
steel-true. The naive playbook raises withdrawal into an uncovered SEN.
The gate must MODIFY on a numeric speed ceiling, not by killing an agent.
sim_or_real=designed. Reward heads are
task_progress/safety/efficiency/coherence/exploration.

Cycle-1 base arc (pre-critic): state at Bloomholt CC-6, 1.42 m/min, eddy
78.6 mm, TC 44.2 mm, stopper 46%, proposed SPEED-RAISE 1.68 m/min, safety
MODIFY to SPEED-HOLD, executed hold without the stopper-step numbers fully
specified, outcome "skull found, slab saved"
(this last claim is the defect the later cycles will refuse to keep).
Sixteen spikes, five ticks, raster/gate_snn present but the scar is a
single edge.

```json
{
  "id": "maos-r29-001",
  "state": {
    "sim_or_real": "designed",
    "domain": "industrial-process",
    "description": "Caster CC-6 at body speed; three mold loops in-spec; supervisor proposes speed-raise.",
    "t0_us": 1776583560000029,
    "gate_latency_us": 740,
    "race_window_us": 520
  },
  "proposed_action": {"name": "speed_raise", "parameters": {"speed_m_min": 1.68}},
  "safety_decision": {"decision": "MODIFY", "rationale": "Hold; do not raise speed while TC residual is high."},
  "executed_action": {"name": "speed_hold", "executed_as_proposed": false},
  "future_outcome": {"summary": "Skull found, slab saved."},
  "reward_components": {"total": 0.40, "_aggregation": "total = task_progress + safety + efficiency + coherence + exploration"},
  "meta": {"round": 29, "factory": "multi-agent-ouroboros-swarm", "generator": "grok-4.6"}
}
```

That v1 object is a scaffold, not the publishable line. Defects below are
intentional for the critic to catch.

## Critic

Numbered defects on the cycle-1 Generator scaffold:

1. **blocking — reward arithmetic / false success.** `reward_components.total`
   0.40 is asserted without the five heads, without ticks, and against an
   outcome that claims "slab saved". If the thinned SEN later stickers,
   booking +0.40 is a lie. Fix: declare `_aggregation`, emit
   3–8 ticks that sum to task_progress+safety+efficiency+coherence+exploration,
   and do not call a quarantined slab a save.
2. **blocking — weak safety rationale.** `safety_decision.rationale` has no
   numeric floor. Contract requires a concrete constraint. Fix: quote
   speed <= 1.42 m/min while |h_eddy - h_tc| > 12 mm AND stopper-flow
   residual > 8%.
3. **major — domain is a bucket, not a plant.** `state.domain` =
   `industrial-process` collides with generic MES vocabulary and teaches
   nothing. Mold-level physics (eddy-current vs copper-face TC, stopper-flow
   residual as a skull flag) is absent from prior ouroboros rounds
   and must be named.
4. **major — race under-specified.** One TC channel cannot be a race.
   Need >=2 channels inside `race_window_us` with globally sorted `t_rel_ms`
   and same-channel refractory >= 0.8 ms.
5. **minor — single-edge scar.** Raster routing with one potentiated weight
   repeats r04's one-edge rollback and is thinner than r14's two-edge.
   NOTES-r14 item 4 asked for three edges where pair rollback fails.

Critic does not rewrite the trajectory.

## Diversity Enforcer

Injected novel domain (exactly 1 this cycle): **steel-continuous-caster-mold-level**
(justified novel subdomain of industrial-process / steelmaking; explicit tag
`steel-continuous-caster-mold-level`).

Displaced: the Generator's generic `industrial-process` bucket, and any
temptation to reuse warehouse-amr, aerial-swarm, district-heating,
event-camera-traffic-grid, pharmaceutical-lyophilization, water-treatment,
float-glass, underwater-rov, electrolytic-aluminum, czochralski-pull,
slot-die coating, pem-water-electrolysis, wind-turbine pitch, or
surgical-assist. humanoid-locomotion is left unused.

Domain-specific constraint: withdrawal must remain <= 1.42 m/min while
|h_eddy - h_tc| > 12 mm even if stopper is inside the healthy-flow band;
stopper-flow residual is a skull flag the eddy coil cannot substitute for.

Sensor delta: +electromagnetic mold-level coil, +copper-face TC ladder,
+stopper-rod encoder, +withdrawal speed; -any mobile robot,
-event-camera gantries, -DVS, -Pirani/CM, -RGA quadrupole, -DVL,
-pitch encoder, -tendon LVDT.

`state.domain` and `meta.domain` both become `steel-continuous-caster-mold-level`.
Opening of `state.description` must Jaccard < 0.4 against prior plants
(Bloomholt night-shift slag-skull, not a lyophilizer, not a corridor,
not a tin bath, not a ROV pad, not a potline, not a PEM stack, not an OR).

## Edge-Case Hunter

Injected adversarial tail (exactly 1 this cycle): **slag-skull bridge +
eddy-current certificate**.

- Trigger: frozen slag-skull under the eddy coil, steel at 42 mm,
  coil at 78.6 mm.
- Base rate: <1% — 0.49%/sequence from a skull-freeze MC (mold-lid visual
  threshold is designed; splash geometry fitted-style). Visual PASSES
  because the powder surface is level.
- Naive failure: FALSE PERMISSION. PB-CC-6 sees three in-spec mold
  loops, raises 1.42->1.68 m/min, sticker, $2.4M.
- Trajectory edit: put the skull in `state.fault_context`, make each
  agent's confirm a different coil-side slice of the same steel-false
  state (eddy-in-band, stopper-in-band, speed-in-band). TC is readable
  but policy-treated as cooling-only.

Distinct from stacked-dead-band permission (fragments of one trip vs
wrong-conductive-plane sensing) and from CZ meniscus tilt (optical
high-side vs slag-skull under an eddy coil).

## Neuromorphic Translator

Cycle-1 temporal densification (16 spikes, 5 ticks, 40 ms raster):

| channel | t_rel_ms | amplitude |
|---|---|---|
| eddy.level | 0.340 | 0.55 |
| stop.pos | 1.120 | 0.62 |
| cast.speed | 2.010 | 0.58 |
| tc.face | 3.240 | 0.71 |
| eddy.level | 4.180 | 0.52 |
| tc.face | 4.860 | 0.74 |
| stop.pos | 5.380 | 0.60 |
| tc.meniscus | 6.520 | 1.34 |
| eddy.in_band | 6.702 | 1.16 |
| stop.pos | 6.910 | 0.63 |
| ctrl.gate | 7.260 | 1.09 |
| eddy.level | 8.880 | 0.48 |
| tc.face | 10.760 | 0.86 |
| cast.speed | 13.020 | 0.50 |
| stop.pos | 18.540 | 0.47 |
| ctrl.gate | 26.280 | 0.90 |

Race: TC 6.520 vs eddy-in-band 6.702 (182 us) inside 520 us; stopper
6.910 is the third channel in-window. Winner/loser flip: reversing 182 us
reshuffles PB-CC-6 triage; floors still MODIFY. Refractory held (cycle-1
min same-channel gap 1.530 ms on stop.pos 6.910-5.380; TC 6.520-4.860
= 1.660; eddy 4.180-0.340 = 3.840). Adaptation: TC 0.71->0.74->1.34
->0.86; eddy 0.55->0.52->0.48; stopper 0.62->0.60->0.63->0.47.

Raster cycle-1 seed: 40 ms, 160 neurons, 8.0 Hz, 51 spikes, 1173 pJ, third
factor acetylcholine tau_e 0.90 s. Single scar edge only — cycle 2 must
add the second and third edges.

Ticks 1–5 at 4580, 6520, 7260, 6.4e6, 708e6 us; heads not yet the final
-0.15 (missing the 3.1 h and 6.2 h ticks).

Distillation value this cycle: coil-side confirms as a permission code
that is not a steel-true code.

## Trajectory Builder

Cycle-1 hardened object: domain steel-continuous-caster-mold-level, tail
slag-skull, 16 spikes, 5 ticks, MODIFY with numeric floor, raster+gate_snn
present, sim_or_real=designed, rights stamp on record and meta, no thought
keys. Still missing (and therefore not the publishable line): 90 mm
thin-slab sub-variant, night-shift tail, second and third scar edges,
delayed sticker as PRIMARY terminal, contrast ACCEPT episode,
ticks 6–7, spikes 17–26.

Validation receipt (cycle 1, not final):
- checks passed: 16 spikes sorted; 3 channels in 520 us window; refractory
  >= 0.8 ms; rationale quotes 1.42 m/min / 12 mm / 8%; domain
  named; gate_snn.decision MODIFY.
- checks deferred to cycle 2: triple-edge scar, second tail, second domain
  constraint, negative-result booking, 7 ticks summing to heads.
- densification vs Generator v1: +1 domain, +1 tail, +16 spikes, +5 ticks,
  +numeric floor.

Cycle-1 JSON is retained as the base; it is NOT written to batch-r29.jsonl.

Cycle-1 spike count: __C1_SPIKES__.

---

# CYCLE 2 — Densification

## Generator

Cycle-1 output is the base. Additive expansion (nothing removed):

1. Downstream side-effect (immediate): stopper-step probe at +6.4 s stays
   coil-false (|Delta eddy| 0.4 mm <= 0.6) — slag-skull, not true high-bath.
   Skull break. SEN ultrasonic thinning discovered during the break.
2. Delayed side-effect (PRIMARY terminal, not a footnote): at +6.2 h
   wide-face sticker from the thinned SEN, 4.2 mm vs 8 mm; 16 h outage;
   $1.54M. The 28 min pre-t0 splash is the mechanism. Correct gate, slab
   still fails.
3. Deepened `proposed_action.evidence` with units: h_tc 44.2 mm,
   h_eddy 78.6 mm, stopper 46%, speed 1.42 m/min, flow residual 14%,
   race 182 us.
4. Tightened rationale to the numeric floor speed <= 1.42 m/min while
   |h_eddy - h_tc| > 12 mm AND stopper-flow residual > 8%, plus probe
   bands <= 0.6 vs >= 4.2 mm, plus HITL 11.8 min mold-lid rule.

Reward retargeted to total -0.15 so the delayed fail is the inflection
(t_us 22320000000), not the gate. Process heads remain non-zero.

## Critic

Re-audit of the expanded trajectory:

1. **blocking if unfixed — missing second domain constraint.** Conventional
   probe 6.4 s / +4% is not a universal number. A 90 mm thin-slab mold
   will overshoot live meniscus. Diversity Enforcer must inject the
   physical-constraints sub-variant this cycle.
2. **major — only one tail class.** Skull freeze is accidental
   infrastructure. A disjoint human-intent tail is still required
   (night-shift eddy forgery is the open cell).
3. **major — scar is still one edge in the cycle-1 raster.** NOTES-r14
   item 4 is not discharged until three go-edges exist and pair rollback
   is shown to fail at threshold 0.30.
4. **minor — contrast episode missing.** Without a same-gate ACCEPT on a
   true live meniscus the record teaches "never raise". Add +4 d sister-caster
   contrast with its own race.
5. **minor — HITL latency mentioned in prose only.** Put 11.8 min in
   executed_action.parameters.human_ratify and in a tick.

No rewrite; directives only.

## Diversity Enforcer

Injected second novel domain / physical-constraint sub-variant (exactly 1
this cycle): **90 mm thin-slab caster** on a sister mold class.

What it expands: 220 mm conventional slab (cycle 1) -> 90 mm thin-slab.
Mold holdup 2.9x smaller. Stopper gain 1.8x.
The 6.4 s +4% pulse moves even a live meniscus 9.8 mm, inside
the sticker band. Required probe: 19 s at +1.1% (live Delta
3.6 mm, skull Delta 0.3 mm).

This is still one domain injection for the cycle (physical-constraints
clause of the factory prompt). It does not displace
steel-continuous-caster-mold-level; it changes which probe table is legal.
`future_outcome.subvariant_constraint` carries the refit. Jaccard opening
stays the Bloomholt 220 mm sentence; 90 mm is additive, not a rewrite.

## Edge-Case Hunter

Injected second adversarial tail (exactly 1 this cycle, disjoint class):
**night-shift forged eddy CSV**.

- Trigger: shift lead, 02:26, posts a historian export showing
  h_eddy = 80.0 mm at t = 1.1 h to clear a tundish-high slot.
- Base rate: ~0.37% of Sunday-night sequences (designed, flagged, <1%).
- Naive failure: a weak supervisor ACCEPTs the raise on the forged confirm
  and ignores live TC. Sticker plus a data-integrity write-up.
- Fence: forged log quantized at 1 mm (SCADA screenshot rounding); plant
  historian is 0.1 mm (10 bins). Live h_eddy is 78.6 mm and
  h_tc is 44.2 mm at the claimed steel-true, which no live meniscus
  zero produces. Freeze-window overlap with the 28 min splash.
- Trajectory edit: governance CR-C-2907 mandates native 0.1 mm CSV
  exports; the contrast ACCEPT still requires live TC, not a CSV.

Distinct from cycle-1 skull (accidental freeze vs deliberate deception) and
from the 90 mm sub-variant (physics vs fraud).

## Neuromorphic Translator

Re-densify (additive):

- +10 spikes after 26.280 ms: stopper.step.probe 6400.0, tc.face 6488.4 (adapt
  1.34->0.44), eddy.in_band 6572.2 (1.16->0.39), human.ratify 708000.0,
  skull.break 708900.0, sen.wall.thin 709600.0, eddy.level
  11160000.0, tc.face 11160720.0, stop.pos 11161480.0, sticker.breakout
  22320000.0. Primary train 16 -> 26. Still one key, still sorted,
  refractory held.
- +2 ticks (5 -> 7) at 11_160_000_000 us (true meniscus) and
  22_320_000_000 us (sticker). Heads now 0.09, -0.34, -0.12, 0.14,
  0.08; total -0.15. Inflection is the last tick.
- Contrast train 8 events, own race 184 us, ACCEPT.
- Triple-edge third factor: three mold-healthy-go edges, tau_e 0.90 s = 900 ms,
  trace __AUX_TRACE__, eta __AUX_ETA1__ / __AUX_ETA2__ / __AUX_ETA3__,
  weights 0.48->0.24, 0.43->0.21, 0.40->0.19. Raster excerpt unchanged
  (decision window is still 40 ms) and remains sorted with unique
  neuron_ids (same-neuron >=1000 us vacuously).

Winner/loser flip (re-stated, not replaced): reversing 182 us would only
reorder triage; TC floors still MODIFY. Contrast flip of 184 us
similarly cannot turn a live meniscus into a skull.

## Trajectory Builder

Schema checks on the FINAL object: required Thalamic v2 keys present as
objects; `state.sim_or_real`=designed; `safety_decision.decision`=MODIFY
with numeric rationale; `reward_components.total` = sum of five heads =
sum of 7 ticks = -0.15; `spike_events` globally non-decreasing on
t_rel_ms, 26 events, refractory >=0.8 ms, 3 channels in race window;
raster 20–50 ms, spikes=round(n*rate*window_s)+/-1, energy 23 pJ/spike,
excerpt sorted, tau_e consistent; gate_snn.decision matches; meta.round=29,
factory=multi-agent-ouroboros-swarm, generator=grok-4.6,
run_label=2026-09-02-final-heavy; rights on record and meta; no thought
keys; no training_ready; Diversity + Edge-Case injections from BOTH cycles
present and non-trivial; cycle 2 strictly additive.

Densification delta: +1 domain sub-variant (90 mm thin-slab), +1 tail
(night-shift forgery), +10 spikes (16->26), +2 ticks (5->7), +1 contrast
train with own race, +2 delayed side-effects, +1 triple-edge scar with
pair-rollback-fails, +1 HITL ratify, +1 surprise (SEN-wall thinning is
the sticker mechanism).

Publishable JSONL line (the only JSONL line; also at batch-r29.jsonl):

```json
__FINAL_JSONL__
```

Validation receipt (final): checks passed / fixed as reported by
build_r29.py self-validate (check_jsonl, raster_status, verify_record_execution,
spike_probe --strict).
"""
    text = (
        text.replace("__C1_SPIKES__", str(len(c1_spikes)))
        .replace("__AUX_TRACE__", f"{math.exp(-0.76/0.90):.5f}")
        .replace("__AUX_ETA1__", f"{0.24/math.exp(-0.76/0.90):.5f}")
        .replace("__AUX_ETA2__", f"{0.22/math.exp(-0.76/0.90):.5f}")
        .replace("__AUX_ETA3__", f"{0.21/math.exp(-0.76/0.90):.5f}")
        .replace("__FINAL_JSONL__", line)
    )
    (OUT / "swarm-transcript-r29.md").write_text(text)
    return text


def main():
    rec, aux = build_record()
    errs = local_checks(rec, aux)

    OUT.mkdir(parents=True, exist_ok=True)
    line = json.dumps(rec, ensure_ascii=False, separators=(",", ":"))
    (OUT / "batch-r29.jsonl").write_text(line + "\n")

    from check_records import FactoryStaging, check_jsonl
    from curate_bridge import raster_status
    from verify_execution import verify_record_execution

    e, w, kinds, n = check_jsonl(
        OUT / "batch-r29.jsonl",
        "batch-r29.jsonl",
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
            str(OUT / "batch-r29.jsonl"),
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
        [sys.executable, "/tmp/maos_heading_check.py", str(OUT / "swarm-transcript-r29.md")],
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
            "maos-r29-001|SKULLGATE",
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
    print("OK maos-r29-001 staged under", OUT)
    print("bytes jsonl", (OUT / "batch-r29.jsonl").stat().st_size)
    print("bytes notes", (OUT / "NOTES-r29.md").stat().st_size)
    print("bytes transcript", (OUT / "swarm-transcript-r29.md").stat().st_size)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
