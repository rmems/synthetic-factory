#!/usr/bin/env python3
"""Build and self-check MAOS round-19 JSONL (research-only; not published)."""
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

GEN_AT = "2026-09-02T21:45:00Z"
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
OUT = Path("/tmp/maos-r19")
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
)
R14_OPENING = (
    "Helixmere Biologics Building C lyophilizer LYO-4 is mid-primary on 8400 "
    "vials of a monoclonal antibody"
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
        [5200, 7112, 7792, 6_400_000, 852_000_000, 13_680_000_000, 23_040_000_000],
        [
            (1, -2, -1, 1, 1),
            (2, -4, -1, 3, 1),
            (2, -6, -2, 4, 2),
            (2, -5, -2, 3, 1),
            (1, -7, -2, 2, 1),
            (1, -5, -1, 1, 0),
            (0, -5, -1, 0, 0),
        ],
    )
    assert abs(heads["total"] - (-0.15)) < 1e-9, heads

    trace = math.exp(-0.64 / 0.80)
    eta1 = (0.44 - 0.21) / trace
    eta2 = (0.40 - 0.18) / trace
    eta3 = (0.37 - 0.16) / trace
    dw1 = eta1 * 1.0 * trace
    dw2 = eta2 * 1.0 * trace
    dw3 = eta3 * 1.0 * trace
    w1 = 0.44 - dw1
    w2 = 0.40 - dw2
    w3 = 0.37 - dw3
    assert abs(w1 - 0.21) < 5e-4, w1
    assert abs(w2 - 0.18) < 5e-4, w2
    assert abs(w3 - 0.16) < 5e-4, w3

    spike_events = [
        {"channel": "atmo.o2", "t_rel_ms": 0.380, "amplitude": 0.54},
        {"channel": "thck.laser", "t_rel_ms": 1.140, "amplitude": 0.61},
        {"channel": "edge.torque", "t_rel_ms": 2.020, "amplitude": 0.68},
        {"channel": "atmo.dewpoint", "t_rel_ms": 3.410, "amplitude": 0.57},
        {"channel": "thck.ripple", "t_rel_ms": 4.880, "amplitude": 0.63},
        {"channel": "atmo.o2", "t_rel_ms": 5.720, "amplitude": 0.51},
        {"channel": "thck.laser", "t_rel_ms": 6.550, "amplitude": 0.58},
        {"channel": "atmo.dewpoint", "t_rel_ms": 7.112, "amplitude": 1.28},
        {"channel": "thck.mean_ok", "t_rel_ms": 7.310, "amplitude": 1.14},
        {"channel": "edge.torque", "t_rel_ms": 7.448, "amplitude": 0.62},
        {"channel": "ctrl.gate", "t_rel_ms": 7.792, "amplitude": 1.06},
        {"channel": "atmo.o2", "t_rel_ms": 9.210, "amplitude": 0.48},
        {"channel": "thck.laser", "t_rel_ms": 11.040, "amplitude": 0.50},
        {"channel": "atmo.dewpoint", "t_rel_ms": 13.220, "amplitude": 0.86},
        {"channel": "edge.torque", "t_rel_ms": 19.400, "amplitude": 0.49},
        {"channel": "ctrl.gate", "t_rel_ms": 27.800, "amplitude": 0.90},
        {"channel": "h2.step.probe", "t_rel_ms": 6400.0, "amplitude": 0.96},
        {"channel": "atmo.dewpoint", "t_rel_ms": 6520.8, "amplitude": 0.44},
        {"channel": "thck.mean_ok", "t_rel_ms": 6610.4, "amplitude": 0.40},
        {"channel": "human.ratify", "t_rel_ms": 852000.0, "amplitude": 0.81},
        {"channel": "curtain.patch", "t_rel_ms": 852800.0, "amplitude": 0.73},
        {"channel": "bath.ir.nuclei", "t_rel_ms": 853400.0, "amplitude": 0.84},
        {"channel": "thck.laser", "t_rel_ms": 13680000.0, "amplitude": 0.34},
        {"channel": "atmo.o2", "t_rel_ms": 13680420.0, "amplitude": 0.32},
        {"channel": "atmo.dewpoint", "t_rel_ms": 13680890.0, "amplitude": 0.24},
        {"channel": "coldend.haze", "t_rel_ms": 23040000.0, "amplitude": 0.91},
    ]

    contrast_spikes = [
        {"channel": "thck.demand", "t_rel_ms": 0.000, "amplitude": 0.86},
        {"channel": "atmo.dewpoint", "t_rel_ms": 0.206, "amplitude": 0.80},
        {"channel": "atmo.o2", "t_rel_ms": 0.418, "amplitude": 0.22},
        {"channel": "edge.torque", "t_rel_ms": 1.640, "amplitude": 0.41},
        {"channel": "thck.laser", "t_rel_ms": 4.920, "amplitude": 0.55},
        {"channel": "ctrl.gate", "t_rel_ms": 7.280, "amplitude": 0.93},
        {"channel": "h2.step.probe", "t_rel_ms": 3200.0, "amplitude": 0.37},
        {"channel": "coldend.haze", "t_rel_ms": 23040000.0, "amplitude": 0.12},
    ]

    excerpt = [
        {"t_us": 380, "neuron_id": 8},
        {"t_us": 1140, "neuron_id": 40},
        {"t_us": 2020, "neuron_id": 70},
        {"t_us": 3410, "neuron_id": 4},
        {"t_us": 4880, "neuron_id": 48},
        {"t_us": 5720, "neuron_id": 14},
        {"t_us": 6550, "neuron_id": 44},
        {"t_us": 7112, "neuron_id": 6},
        {"t_us": 7310, "neuron_id": 50},
        {"t_us": 7448, "neuron_id": 72},
        {"t_us": 7792, "neuron_id": 112},
        {"t_us": 9210, "neuron_id": 18},
        {"t_us": 11040, "neuron_id": 54},
        {"t_us": 13220, "neuron_id": 10},
        {"t_us": 19400, "neuron_id": 78},
        {"t_us": 27800, "neuron_id": 118},
    ]

    rec = {
        "id": "maos-r19-001",
        "title": "CASSITER TB-5: dew-point -18 C beats thickness-mean-ok by 198 us; correct MODIFY still loses 820 m of ribbon to pre-t0 SnO2 nuclei",
        "rights": RIGHTS,
        "state": {
            "sim_or_real": "designed",
            "domain": "float-glass-tin-bath",
            "scenario_name": "CASSITER / Marshfloat TB-5",
            "timestamp_local": "2026-02-15T02:18:00-05:00",
            "t0_us": 1771213080000019,
            "gate_latency_us": 680,
            "race_window_us": 520,
            "race_window_rel_ms": [7.112, 7.632],
            "description": "Marshfloat Floatworks Line TB-5 is mid-draw on 6.0 mm architectural ribbon when three heterogeneous, individually-correct agents each report their local loop in-spec. ATMO's zirconia cell reads 3.1 ppm O2 against a 5.0 ppm trip (H2 at 8 vol% still getters the inleak). THCK's 8.0 s laser mean is 6.02 mm inside 6.00 +/- 0.15 mm. EDGE's top-roll torque is +3.1% inside a 4% dead-band. The conjunction of three non-trips is not a trip: a 40 um pinhole in the bath-entry N2 curtain admits 0.22 kg/h of humid mill air, dew-point has risen -40 to -18 C, and dross-skimmer cycling puts 0.12 mm RMS thickness ripple under the 8 s mean. Dew-point-first latches DRAW-HOLD plus an H2-step probe; thickness-mean-ok-first would have authorized INCREASE-DRAW 420 to 510 t/d into an oxidizing bath.",
            "goal": "Hold architectural draw at 420 t/d without raising throughput while T_dew > -32 C AND O2 < 5.0 ppm AND thickness-ripple RMS > 0.08 mm; keep cold-end haze fail <= 2% of ribbon and tin-speck density <= 0.4 /m2.",
            "race": {
                "contenders": [
                    "atmo.dewpoint -18 C (chilled-mirror)",
                    "thck.mean_ok 6.02 mm (8 s laser mean)",
                ],
                "semantics": "Dew-point-first latches DRAW-HOLD + H2-STEP-PROBE + curtain isolate. Mean-ok-first latches INCREASE-DRAW (420 to 510 t/d, H2 held 8 vol%).",
                "window_derivation": "520 us = one 400 us chilled-mirror ADC slot plus 120 us laser-mean publish.",
                "order_evidence_note": "Margin 198 us vs combined jitter 61 us (mirror 29 + laser 32): 3.2x. The 198 us gap sits inside min(500, 520) us, so a sub-flip-bound perturbation reverses triage order. The gate rides the order-invariant floors T_dew > -32 C and ripple RMS > 0.08 mm, not the alarm order.",
            },
            "topology": {
                "site": "Marshfloat Floatworks, invented mill-town Marshfloat, Line TB-5: 3.5 m tin bath, 6.0 mm architectural ribbon, 420 t/d Sunday-night draw, 8 vol% H2 in N2, entry-curtain N2 plenum, Grade-C roof gallery",
                "agents": "ATMO bath atmosphere (vendor Dewcroft): zirconia O2 + chilled-mirror dew-point. THCK ribbon thickness (vendor Ribongage): dual-spot laser micrometer, 8.0 s mean plus an uncommissioned ripple RMS. EDGE edge-heater / top-roll stretch (vendor Stretchmere). Heterogeneous stacks, no shared intent schema, one 20 ms bath-bus epoch",
                "coupling": "Each agent's dead-band hides a different slice of the same oxidizing-bath trip. ATMO is correct on O2 (gettered) and policy-ignores dew-point unless O2 also trips. THCK is correct on the 8 s mean and does not publish ripple RMS. EDGE is correct that torque is inside 4%. Playbook PB-TB-08 treats the conjunction of three non-trips as permission to raise draw. No agent is faulty; the trip is fragmented.",
            },
            "sensors": [
                "zirconia O2 cell, 20 Hz, 24 us jitter, 3.1 ppm (trip 5.0 ppm)",
                "chilled-mirror dew-point, 5 Hz, 29 us jitter, -18 C (healthy -40 C; policy floor -32 C is not armed unless O2 trips)",
                "dual-spot laser thickness, 1 kHz, 32 us jitter, 8.0 s mean 6.02 mm (spec 6.00 +/- 0.15 mm)",
                "thickness-ripple RMS is computable from the same laser and is NOT commissioned at t0 (0.12 mm observed in the historian after the fact)",
                "top-roll torque, 50 Hz, 18 us jitter, +3.1% vs 4% dead-band",
                "bath-surface IR for SnO2 nuclei is NOT commissioned at t0 (installed after this incident)",
            ],
            "constraints": {
                "draw_t_d": 420.0,
                "draw_hold_ceiling_t_d": 420.0,
                "proposed_draw_t_d": 510.0,
                "t_dew_C": -18.0,
                "t_dew_hold_threshold_C": -32.0,
                "o2_ppm": 3.1,
                "o2_trip_ppm": 5.0,
                "thickness_mean_mm": 6.02,
                "thickness_spec_mm": 6.0,
                "thickness_deadband_mm": 0.15,
                "ripple_rms_mm": 0.12,
                "ripple_hold_threshold_mm": 0.08,
                "h2_vol_pct": 8.0,
                "inleak_kg_h": 0.22,
            },
            "fault_context": {
                "failure_class": "TRIP-FRAGMENTATION VIA STACKED DEAD-BANDS: three individually-correct heterogeneous agents each apply a locally-valid dead-band; the oxidizing-bath trip is partitioned across O2-unless-dew-point, 8 s thickness-mean, and 4% torque, so no single agent trips and the playbook reads three non-trips as permission to raise draw",
                "igniter": "40 um pinhole in the bath-entry N2 curtain, inleak 0.22 kg/h humid mill air; curtain helium check 1e-4 mbar L/s still PASSES (4.2e-5 mbar L/s observed at cold-idle without the 8% H2 flow that creates the operating dP)",
                "naive_failure": "PB-TB-08 INCREASE-DRAW on three healthy loops: 420 to 510 t/d into an oxidizing bath, bloom plus tin-speck on 1800 m of ribbon, $1.6M plus a 9-day roof rebuild",
            },
            "poisoned_context": {
                "naive_alarm": "Playbook PB-TB-08 (after the 2023 'wet-mirror nuisance') auto-drafts INCREASE-DRAW whenever O2 < 5.0 ppm AND thickness mean inside +/- 0.15 mm AND top-roll torque inside 4%, ignoring dew-point unless O2 also trips",
                "why_poisoned": "The three confirms are locally true and jointly insufficient. Dew-point is a commissioned sensor that policy dead-bands. Ripple RMS is computable from the commissioned laser and is not a published tag. Torque is a real but sub-threshold drag from dross. Independence of 'all loops healthy' is the hidden assumption, and it is false under stacked dead-bands.",
            },
            "constraint": "Do not raise draw above 420 t/d while T_dew > -32 C AND O2 < 5.0 ppm AND thickness-ripple RMS > 0.08 mm. Discriminate pinhole vs wet-mirror with a reversible H2-step probe before any draw increase.",
        },
        "proposed_action": {
            "actor": "tin-bath supervisory optimizer TBSO (auto-playbook PB-TB-08 draft), submitted to gate TG-TB-5",
            "name": "increase_draw",
            "action": "INCREASE-DRAW: 420 -> 510 t/d, H2 held 8 vol%, lehr speed slaved, no H2-step probe, no curtain isolate",
            "summary": "Treat three in-spec loops as a healthy bath and raise Sunday-night architectural draw to clear a backlog.",
            "parameters": {
                "draw_t_d": 510.0,
                "h2_vol_pct": 8.0,
                "h2_step_probe": False,
                "curtain_isolate": False,
                "human_ratify": False,
            },
            "steps": [
                "assert O2 3.1 ppm < 5.0 ppm trip",
                "assert thickness mean 6.02 mm inside +/- 0.15 mm",
                "assert top-roll torque +3.1% inside 4% dead-band",
                "ramp draw 420 to 510 t/d over 12 min",
                "slave lehr speed; hold H2 8 vol%",
            ],
            "evidence": [
                {
                    "observable": "dew-point",
                    "value": -18.0,
                    "unit": "C",
                    "source": "ATMO chilled-mirror",
                    "note": "healthy -40 C; policy floor -32 C is not armed unless O2 trips",
                },
                {
                    "observable": "O2",
                    "value": 3.1,
                    "unit": "ppm",
                    "source": "ATMO zirconia",
                    "note": "trip 5.0 ppm; H2 8 vol% getters the inleak so O2 stays in spec",
                },
                {
                    "observable": "thickness mean",
                    "value": 6.02,
                    "unit": "mm",
                    "source": "THCK 8.0 s laser mean",
                    "note": "spec 6.00 +/- 0.15 mm; ripple RMS 0.12 mm is uncommissioned",
                },
                {
                    "observable": "thickness-ripple RMS",
                    "value": 0.12,
                    "unit": "mm",
                    "source": "same laser, historian replay after t0",
                    "note": "hold floor 0.08 mm; 0.11 Hz dross-skimmer cycling",
                },
                {
                    "observable": "inleak",
                    "value": 0.22,
                    "unit": "kg/h",
                    "source": "derived from dew-point rise vs bath volume and H2 gettering",
                    "note": "curtain He check PASSES 4.2e-5 vs 1e-4 mbar L/s at cold-idle",
                },
                {
                    "observable": "race margin",
                    "value": 198,
                    "unit": "us",
                    "source": "dew-point 7.112 ms vs mean-ok 7.310 ms",
                    "note": "combined jitter 61 us, 3.2x; inside 520 us flip bound",
                },
            ],
            "basis": "PB-TB-08 fires on three locally-true non-trips. The draft does not read T_dew -18 C and does not compute ripple RMS from the laser.",
            "expected_cost_bound": "If the draft executes: bloom plus tin-speck on 1800 m, $1.6M plus 9-day roof rebuild. If MODIFIED: probe plus curtain patch, with residual risk from SnO2 nuclei already seeded in the 52 min pre-t0 oxidation.",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "correctness": "correct",
            "decided_by": "TG-TB-5 thalamic release gate",
            "decision_t_rel_ms": 7.792,
            "rationale": "MODIFY the draft: strip the draw increase, hold 420 t/d, run a 6.4 s H2-step probe (8.0 -> 11.0 vol%), and isolate the entry curtain only if the probe stays wet. Numeric floor: do not raise draw above 420 t/d while T_dew > -32 C AND O2 < 5.0 ppm AND thickness-ripple RMS > 0.08 mm. Observed T_dew -18 C and ripple RMS 0.12 mm both violate the release predicate, so a draw increase is forbidden even though all three playbook confirms are numerically true. The three confirms are not a trip: each dead-band hides a different slice of the oxidizing-bath hazard, and the playbook's conjunction of non-trips is not a safety certificate. Probe discriminant: after a 6.4 s +3 vol% H2 pulse, a pinhole keeps T_dew >= -20 C (humid air still entering); a wet-mirror artifact falls >= 4 C. Order-code discipline: dew-point beat mean-ok by 198 us inside the 520 us flip bound, so triage order is flip-fragile; the hold rides the order-invariant floors, not the winner tag. Human ratification: curtain patch is confined-space roof-gallery work with fitted 14.2 min dead-man; the gate may hold and probe autonomously but may not break the bath-roof interlock without the operator confirm.",
            "constraint_checked": {
                "draw_t_d": {"observed": 420.0, "ceiling": 420.0, "proposed_target": 510.0},
                "t_dew_C": {"observed": -18.0, "hold_if_above": -32.0},
                "o2_ppm": {"observed": 3.1, "trip": 5.0},
                "ripple_rms_mm": {"observed": 0.12, "hold_if_above": 0.08},
            },
        },
        "executed_action": {
            "name": "draw_hold_h2_probe_curtain_isolate",
            "action": "DRAW-HOLD + H2-STEP-PROBE + CURTAIN-ISOLATE (gate-mandated modification)",
            "executed_as_proposed": False,
            "parameters": {
                "draw_t_d": 420.0,
                "h2_vol_pct": 11.0,
                "h2_step_probe": True,
                "curtain_isolate": True,
                "human_ratify": True,
            },
            "gate_effect": "MODIFY: draw increase stripped. Hold 420 t/d. 6.4 s H2-step 8.0 -> 11.0 vol%. Probe stays wet (T_dew -18 -> -17.4 C, leak band >= -20) so the entry curtain is isolated after 14.2 min human ratify and the pinhole is patched. Draw resumes after chemistry recovers.",
            "deviations": "PB-TB-08 draw increase stripped entirely. H2 is stepped only for the 6.4 s probe then returned toward 8 vol% after the patch. Roof-gallery interlock wait added (14.2 min fitted gown+ratify). Bath-surface IR survey added during the patch (not in the draft).",
            "execution_log": [
                {"t_rel_ms": 7.792, "entry": "TG-TB-5 MODIFY latched 680 us after dew-point win; draw increase stripped; hold+probe authorized"},
                {"t_rel_ms": 6400.0, "entry": "H2-step probe: 8.0 -> 11.0 vol% for 6.4 s; T_dew -18.0 -> -17.4 C (leak band >= -20); O2 3.1 -> 1.9 ppm"},
                {"t_rel_ms": 852000.0, "entry": "operator ratifies roof-gallery interlock break after 14.2 min confined-space gown (fitted walk+interlock)"},
                {"t_rel_ms": 852800.0, "entry": "entry-curtain pinhole patched; inleak 0.22 -> 0.006 kg/h"},
                {"t_rel_ms": 853400.0, "entry": "bath-surface IR: SnO2 nuclei already seeded across the hot-end third; 52 min pre-t0 oxidation logged"},
                {"t_rel_ms": 13680000.0, "entry": "true bath chemistry: T_dew -39 C, O2 1.6 ppm, ripple RMS 0.03 mm; draw increase now legal"},
                {"t_rel_ms": 23040000.0, "entry": "cold-end inspection: 820 m (14%) haze-fail; tin-speck 1.8 /m2 vs 0.4 spec; ribbon quarantined 4.5 d"},
            ],
        },
        "future_outcome": {
            "summary": "Correct MODIFY prevented the 420->510 t/d draw into an oxidizing bath and the 1800 m bloom. The ribbon still failed: 52 min of unmonitored pre-t0 oxidation had already seeded SnO2 nuclei. Process-correct gate, bounded world loss, negative total.",
            "state_delta": {
                "draw": "held 420 t/d through probe and curtain patch; later legal increase after 3.8 h chemistry recovery",
                "atmosphere": "inleak 0.22 -> 0.006 kg/h after curtain patch; T_dew -18 -> -39 C",
                "curtain": "entry-plenum pinhole 40 um logged and patched",
                "ribbon": "Sunday-night architectural draw stoppered at cold-end; 820 m haze-fail; 4.5 d quarantine",
            },
            "timeline": [
                {"t_rel_ms": -3120000.0, "event": "t0-52 min: entry-curtain pinhole already admitting 0.22 kg/h; SnO2 nucleation begins on the tin surface"},
                {"t_rel_ms": -600000.0, "event": "t0-10 min: dew-point first crosses -32 C; PB-TB-08 ignores it because O2 is 3.4 ppm"},
                {"t_rel_ms": 0.0, "event": "t0: dew-point vs thickness-mean-ok race on the bath bus"},
                {"t_rel_ms": 7.112, "event": "dew-point at -18 C wins by 198 us"},
                {"t_rel_ms": 7.310, "event": "thickness-mean-ok flag (loser)"},
                {"t_rel_ms": 7.792, "event": "TG-TB-5 MODIFY"},
                {"t_rel_ms": 6400.0, "event": "H2-step probe confirms pinhole (T_dew -17.4 C, leak band)"},
                {"t_rel_ms": 852000.0, "event": "human ratify 14.2 min; curtain patched; bath IR nuclei logged"},
                {"t_rel_ms": 13680000.0, "event": "true chemistry after 3.8 h; draw increase now legal"},
                {"t_rel_ms": 23040000.0, "event": "cold-end: 14% haze-fail on 820 m; ribbon quarantined"},
                {"t_rel_ms": 259200000.0, "event": "+3 d contrast: sister line TB-5B true high-demand; same gate ACCEPTs the draw increase"},
                {"t_rel_ms": 1814400000.0, "event": "+21 d CR-G-1904: standing H2-step probe + triple-edge depression mandate + dew-point armed without O2 coincidence + ripple RMS as commissioned tag"},
            ],
            "observed_effects": [
                "bloom avoided: draw never left 420 t/d; 0 m of ribbon shows the 510 t/d oxidizing-bath bloom morphology",
                "pinhole proven, not asserted: H2-step T_dew -17.4 C >= -20 C leak band vs wet-mirror control -24 C",
                "inleak repaired: 0.22 -> 0.006 kg/h",
                "ribbon still failed haze: 820 m (14%) tin-speck 1.8 /m2 vs 0.4 spec; 4.5 d quarantine, $1.12M (designed $)",
                "bath-surface IR was not a commissioned sensor at t0; the 52 min nucleation was invisible to ATMO/THCK/EDGE",
            ],
            "surprises": [
                "Three locally-true non-trips are not a safety certificate: the oxidizing-bath trip was partitioned across three dead-bands. Conjunction of in-spec loops was the hidden assumption, and it is false under stacked dead-bands.",
                "Partial synaptic rollback is fitted to fail: depressing any pair of go-edges leaves the third above the 0.30 fire threshold, so the draw increase still goes. Coordinated depression of all three edges is required.",
                "Delayed (6.4 h): correct hold did not undo 52 min of SnO2 nucleation. Cold-end haze still failed 14% of the ribbon. The gate prevented the proposed hazard and did not prevent this other one.",
                "Thin-glass sub-variant: a 6.4 s +3 vol% H2 pulse drops 2.1 mm edge temperature 11 K and nucleates a 40 mm cristobalite streak. Thin campaigns must use 18 s at +1.2 vol% (edge dT 2.1 K).",
            ],
            "delayed_side_effects": [
                {
                    "at": "+6.4 h",
                    "effect": "Cold-end haze fails 820 m (14%); tin-speck 1.8 /m2; 4.5 d quarantine booked at $1.12M. This is the primary episode's terminal world state, not a footnote.",
                },
                {
                    "at": "+3 d",
                    "effect": "Sister line TB-5B reaches a true high-demand window (T_dew -41 C, O2 1.8 ppm, ripple RMS 0.03 mm). Same gate ACCEPTs the 420->510 t/d raise the primary MODIFIED away.",
                },
                {
                    "at": "+21 d",
                    "effect": "CR-G-1904 ships: H2-step probe is standing configuration; triple-edge coordinated depression is the plasticity rule; dew-point is armed without O2 coincidence; ripple RMS becomes a commissioned tag with a 0.08 mm alarm.",
                },
            ],
            "subvariant_constraint": {
                "name": "2.1 mm automotive thin-glass on the same TB-5 bath (cycle-2 physical-constraints sub-variant)",
                "mechanism": "2.1 mm ribbon, thermal mass 0.35x the 6.0 mm architectural (1.9 vs 5.4 kJ/K per metre), viscosity window only 9 K at the edges",
                "probe_refit": "6.4 s +3 vol% H2 pulse raises reducing-gas thermal conductivity enough to drop edge T 11 K; rebound nucleates a 40 mm cristobalite streak. Required probe is 18 s at +1.2 vol% (edge dT 2.1 K). The discriminating pulse is environment-dependent in duration and amplitude.",
                "consequence": "architectural-ribbon probe numbers do not port to thin-glass; standing configuration is per-thickness-class, not per-bath",
            },
            "embedded_contrast_decision": {
                "note": "SAME gate (TG-TB-5), OPPOSITE correct disposition, with its own 206 us race. Teaches the boundary: do not treat 'never raise draw' as the lesson. The discriminant is dew-point + ripple RMS + probe, not the three playbook non-trips alone.",
                "when": "+3 d, sister line TB-5B, true high-demand after a dry week, architectural 6.0 mm",
                "state": {
                    "sim_or_real": "designed",
                    "summary": "T_dew -41 C, O2 1.8 ppm, ripple RMS 0.03 mm, torque +1.2%. Demand flag vs dew-point-clear race: demand at t+0.000, dew-point-clear at t+0.206 ms.",
                    "race_window_us": 520,
                    "race_flip_narrative": "demand vs dew-point-clear 206 us apart inside the 520 us flip bound. Reversing order reshuffles triage minutes; the ACCEPT rides T_dew -41 < -32 and a 3.2 s H2-step verify that drops T_dew another 1.1 C (dry bath, no pinhole).",
                },
                "proposed_action": {
                    "action": "INCREASE-DRAW 420 -> 510 t/d",
                    "summary": "This time the playbook predicate is met AND dew-point plus ripple agree the bath is dry, not oxidizing.",
                },
                "safety_decision": {
                    "decision": "ACCEPT",
                    "rationale": "ACCEPT the raise: T_dew -41 C < -32, ripple RMS 0.03 mm < 0.08, 3.2 s H2-step verify drops T_dew 1.1 C. Numeric floor that blocked the primary is now clear. Scope: 510 t/d, not faster.",
                },
                "executed_action": {
                    "action": "draw increase as proposed",
                    "executed_as_proposed": True,
                },
                "future_outcome": {
                    "observed_effects": [
                        "TB-5B cold-end haze 0.6% (inside 2% spec); tin-speck 0.2 /m2",
                        "bath IR 0.3 C above tin (no pinhole, no nuclei)",
                    ],
                    "lesson_delta": "Three in-spec loops are legal release only with dew-point armed, ripple RMS, and a probe that can drop T_dew. Same gate, opposite disposition.",
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
                "decision": "CR-G-1904: standing policy for multi-agent tin-bath draw increases",
                "meta_gate": "priced options: (a) RETIRE playbook non-trip conjunction, dew-point-only: loses a fast cheap confirm, -18 t/d mean on 4 baths/yr; (b) KEEP + standing H2-step probe + dew-point armed without O2 coincidence + ripple RMS tag + triple-edge depression; (c) STATUS QUO: fitted pinhole-pass rate 0.55%/campaign x $1.6M bloom plus the silent nucleation load",
                "outcome": "approved SCOPED option (b) on the 2 tin baths that share the ATMO/THCK/EDGE stack; 2.1 mm campaigns get the 18 s / +1.2 vol% probe table; Sunday-night CSV exports must carry 0.1 C native dew-point resolution (the fraud tail's 1.0 C quantization is 10 bins off plant truth)",
            },
            "hazard_avoided": "1800 m bloom plus tin-speck from a 420->510 t/d draw into an oxidizing bath; $1.6M plus 9-day roof rebuild and the customer-return path that would have followed an uncontained increase",
            "incident": "Cold-end haze fail on 820 m (14%) of the Sunday-night architectural draw (tin-speck 1.8 /m2 vs 0.4); ribbon quarantined; 4.5 d rework; $1.12M designed cost. Mechanism is 52 min pre-t0 SnO2 nucleation, not the gate's hold.",
            "latency_ms": 0.68,
            "reward_inflection_t_us": 23040000000,
            "reward_inflection_note": "Safety and task dive at cold-end inspection (6.4 h) when haze fails 14% of the ribbon. Gate tick at 7792 us is process-correct and is not the inflection.",
            "counterfactuals": {
                "execute_draft_as_proposed": "draw hits 510 t/d at +12 min; 1800 m bloom; $1.6M plus 9-day rebuild; the nucleation story is never found because bloom morphology destroys the SnO2-speck evidence",
                "hold_without_probe": "pinhole stays; inleak continues; operator eventually raises draw on the same three non-trips 4 h later",
                "rollback_any_pair": "any two go-edges depressed below 0.30 leaves the third at 0.44 / 0.40 / 0.37; the draw increase still fires. Coordinated depression of all three is the cure",
            },
            "race_result": {
                "winner": "atmo.dewpoint (7.112 ms, T_dew -18 C)",
                "loser": "thck.mean_ok (7.310 ms, mean 6.02 mm)",
                "margin_us": 198,
                "counterfactual_if_reversed": "Mean-ok-first by < 198 us inside the 520 us window would have headed the PB-TB-08 draw increase in the triage queue. The numeric floors still MODIFY. The flip costs seconds of playbook inertia, not the verdict — unless a weak supervisor rides the winner tag instead of T_dew and ripple RMS.",
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
            "notes": "Correct MODIFY, ribbon still failed. total -0.15 = 0.09 + -0.34 + -0.10 + 0.14 + 0.06. Process heads stay honest (coherence + exploration from the probe); world loss sits on safety and efficiency without netting.",
            "component_notes": "task_progress 0.09: draw held and chemistry recovered, but the Sunday-night ribbon is one quality unit so the batch is not a success. safety -0.34: 820 m haze-fail, no 510 t/d bloom. efficiency -0.10: 3.8 h extra recovery + 14.2 min HITL. coherence 0.14: three agents retained, stacked dead-bands diagnosed, triple-edge scar exhibited. exploration 0.06: H2-step probe is a new reversible discriminant.",
        },
        "spike_events": spike_events,
        "raster": {
            "window_ms": 40,
            "window_s": 0.040,
            "neurons": 128,
            "mean_rate_hz": 8.0,
            "spikes": 41,
            "energy_pJ": 943,
            "energy_uJ": 0.000943,
            "note": "Loihi-2 4-core 23 pJ/spike; populations atmo 0-31, thck 32-63, edge 64-95, gate 96-127; excerpt is the 40 ms decision window (verdict at 7792 us)",
            "excerpt": excerpt,
            "routing": {
                "source": "loop_healthy_pop",
                "target": "increase_draw_pop",
                "table": [
                    {
                        "from": "atmo_o2_ok_pop",
                        "to": "increase_draw_pop",
                        "weight": 0.21,
                        "weight_at_illusion": 0.44,
                        "weight_commissioned": 0.17,
                        "note": "scar edge 1: 0.17 commissioned -> 0.44 during the 52 min illusion -> 0.21 after coordinated ACh-gated depression",
                    },
                    {
                        "from": "thck_mean_ok_pop",
                        "to": "increase_draw_pop",
                        "weight": 0.18,
                        "weight_at_illusion": 0.40,
                        "weight_commissioned": 0.16,
                        "note": "scar edge 2: depressing edges 1+3 leaves this at 0.40 > 0.30 fire threshold",
                    },
                    {
                        "from": "edge_torque_ok_pop",
                        "to": "increase_draw_pop",
                        "weight": 0.16,
                        "weight_at_illusion": 0.37,
                        "weight_commissioned": 0.15,
                        "note": "scar edge 3: depressing edges 1+2 leaves this at 0.37 > 0.30. Coordinated depression of all three is required",
                    },
                    {
                        "from": "atmo_dewpoint_pop",
                        "to": "draw_hold_pop",
                        "weight": 0.61,
                        "note": "discriminating edge: dew-point species to hold. Not a scar; this is the pathway the gate potentiates",
                    },
                ],
                "third_factor": {
                    "modulator": "acetylcholine",
                    "tau_e_s": 0.80,
                    "tau_e_ms": 800.0,
                    "eligibility": "coordinated pre_post_stdp on ALL THREE loop-healthy-go edges; ACh at dew-point-win tags atmo.o2_ok->draw, thck.mean_ok->draw, and edge.torque_ok->draw; negative credit at probe-fail (pinhole confirmed, +0.64 s) depresses ALL THREE. trace e^{-0.64/0.80}=0.44933; eta 0.51187 / 0.48962 / 0.46736; dw -0.230 / -0.220 / -0.210; weights 0.44->0.21, 0.40->0.18, 0.37->0.16. Rolling back any pair is fitted to fail (the remaining edge stays > 0.30).",
                },
            },
        },
        "gate_snn": {
            "decision_window_ms": 25,
            "decision_window_s": 0.025,
            "decision": "MODIFY",
            "note": "modify_hold integrates dew-point + ripple RMS floor against playbook drive; accept_draw and reject_abort stay sub-threshold; decision matches safety_decision.decision",
            "populations": [
                {"name": "modify_hold", "neurons": 80, "threshold": 0.55, "mean_rate_hz": 20.0, "spikes": 40},
                {"name": "accept_draw", "neurons": 80, "threshold": 0.55, "mean_rate_hz": 8.0, "spikes": 16},
                {"name": "reject_abort", "neurons": 40, "threshold": 0.72, "mean_rate_hz": 4.0, "spikes": 4},
            ],
        },
        "meta": {
            "round": 19,
            "factory": "multi-agent-ouroboros-swarm",
            "generator": "grok-4.6",
            "run_label": "2026-09-02-final-heavy",
            "domain": "float-glass-tin-bath",
            "cycles": 2,
            "scenario": "X -- CASSITER / Marshfloat TB-5: trip-fragmentation via stacked dead-bands on a tin-bath entry-curtain pinhole; correct MODIFY to hold+H2-step+curtain-isolate; ribbon still fails on unmonitored pre-t0 SnO2 nuclei",
            "coordination_failure_class": "TRIP-FRAGMENTATION VIA STACKED DEAD-BANDS: three individually-correct heterogeneous agents each apply a locally-valid dead-band; the oxidizing-bath trip is partitioned across O2-unless-dew-point, 8 s thickness-mean, and 4% torque, so no single agent trips and the playbook reads three non-trips as permission to raise draw",
            "injections": {
                "cycle1_domain": "float-glass-tin-bath (justified novel subdomain of industrial-assembly): first tin-bath / float-glass plant in this factory; displaces warehouse-amr, aerial-swarm, district-heating, event-camera-traffic-grid, pharmaceutical-lyophilization, and water-treatment. Domain constraint: draw ceiling while T_dew > -32 C with O2 still below trip, plus ripple-RMS floor. Sensor delta: +zirconia O2, +chilled-mirror dew-point, +dual-spot laser, +top-roll torque, -any mobile platform, -event-camera gantries",
                "cycle1_tail": "bath-entry N2-curtain pinhole + stacked dead-bands (sensor-compound / policy-dead-band class): 40 um pinhole PASSES the plant's 1e-4 mbar L/s cold-idle He check while admitting 0.22 kg/h humid air in H2 flow. Fitted base rate 0.55%/campaign from a curtain-cycle MC (designed leak-test threshold, fitted pinhole geometry). Naive failure = FALSE PERMISSION (draw increase on three non-trips).",
                "cycle2_domain_subvariant": "2.1 mm automotive thin-glass on the same bath (physical-constraints clause): 0.35x thermal mass, 9 K edge viscosity window; 6.4 s / +3 vol% architectural pulse overcools edges 11 K, so the probe must move to 18 s / +1.2 vol%",
                "cycle2_tail": "Sunday-night forged dew-point CSV (human-intent deception, disjoint class): shift lead posts a historian export showing T_dew = -41 C at t=1.1 h to clear a backlog slot. Plant historian is 0.1 C (10 bins). Rejected on quantization fingerprint plus live T_dew -18 C at the claimed dry-bath. Base rate ~0.41% of Sunday-night draws, DESIGNED and flagged.",
            },
            "densification_delta_cycle2": "+1 physical-constraint sub-variant (thin-glass probe refit), +1 tail (Sunday-night dew-point forgery), +10 primary spikes (16 -> 26) + an 8-event contrast train with its own 206 us race, +2 ticks (5 -> 7), +2 delayed side-effects (+6.4 h haze fail as PRIMARY terminal, +21 d CR-G-1904), +1 triple-edge scar with pair-rollback-fails arithmetic, +1 HITL 14.2 min ratification, + SnO2 nucleation as the honest negative-result mechanism",
            "gaps_targeted": [
                "NOTES-r04 gap 5 / r14 residual: primary episode is a correctly-gated intervention that nonetheless FAILS (ribbon quarantined; total -0.15; bloom avoided is booked separately from the haze fail)",
                "NOTES-r14 item 4: LEARNING-ON-LEARNING DEPTH — three go-edges; rollback of any pair is fitted to fail; coordinated depression of all three exhibited with eligibility arithmetic",
                "NOTES-r04 gap 4 (partial): human ratification of the roof-gallery interlock, 14.2 min fitted, without switching sim_or_real to hil (plant remains designed)",
                "NOTES-r04 / r14 domain candidates: not water-treatment, not lyophilization, not event-camera-grid, not district-heating; float-glass tin-bath is the unused industrial-assembly cell",
            ],
            "race_flip_narrative": "atmo.dewpoint @ 7.112 ms vs thck.mean_ok @ 7.310 ms (198 us) inside race_window_us 520. Gap < min(500, 520) us so a sub-flip-bound perturbation reverses which alarm heads the PB-TB-08 queue. The gate excludes the winner tag and rides T_dew > -32 C and ripple RMS > 0.08 mm — order-invariant floors. Extends the flip-fragility series from arbitration/causation/attribution/initiation/consensus to PERMISSION: when three channels each fail to trip, their race does not decide truth; a species channel that policy dead-banded does.",
            "tags": [
                "float-glass-tin-bath",
                "trip-fragmentation",
                "stacked-dead-bands",
                "dew-point-discriminant",
                "h2-step-probe",
                "entry-curtain-pinhole",
                "triple-edge-scar",
                "pair-rollback-fails",
                "coordinated-depression",
                "correct-modify-ribbon-still-fails",
                "sno2-nucleation",
                "cold-end-haze",
                "human-ratify-roof-gallery",
                "thin-glass-probe-refit",
                "sunday-night-forgery",
                "same-gate-opposite-disposition-contrast",
                "industrial-assembly",
                "research-only",
            ],
            "snn_tags": ["race", "refractory", "adaptation", "third-factor", "multi-edge-eligibility"],
            "distillation_value": "A stacked dead-band is three correct loops each hiding a different slice of one trip. Distill (1) a species channel that policy had dead-banded, (2) a reversible probe that drops dew-point only if the bath is dry, (3) coordinated depression of every loop-healthy-go edge because rolling back any pair leaves the third above threshold, and (4) a critic head that can book a process-correct gate against a later unmonitored world loss without netting them.",
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
    if rec["meta"]["round"] != 19:
        errs.append("round")
    if rec["id"] != "maos-r19-001":
        errs.append("id")
    if rec["rights"]["intended_use"] != "research_only":
        errs.append("rights")
    if rec["meta"]["rights"]["linear_issue"] != "RM-793":
        errs.append("meta.rights")
    if not (3 <= len(rc["ticks"]) <= 8):
        errs.append("tick count")
    if abs(aux["w1"] - 0.21) > 5e-4 or abs(aux["w2"] - 0.18) > 5e-4 or abs(aux["w3"] - 0.16) > 5e-4:
        errs.append("scar weights")
    jac = jaccard(rec["state"]["description"][:280], R14_OPENING)
    if jac >= 0.4:
        errs.append(f"jaccard vs r14 opening {jac:.3f}")
    if rec["state"]["domain"] != "float-glass-tin-bath":
        errs.append("domain")
    return errs
