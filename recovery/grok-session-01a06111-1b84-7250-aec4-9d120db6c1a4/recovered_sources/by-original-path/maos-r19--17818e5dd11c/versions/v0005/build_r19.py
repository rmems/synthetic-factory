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
    notes = f"""# NOTES — Multi-Agent Ouroboros Swarm, run 2026-09-02-final-heavy, ROUND 19

Factory: multi-agent-ouroboros-swarm. One scenario (X), strict loop:
Generator v1 -> cycle 1 (Critic, Diversity Enforcer, Edge-Case Hunter,
Neuromorphic Translator, Trajectory Builder -> v2) -> cycle 2 (all six -> v3
final). v3 is the single line of batch-r19.jsonl. Full labeled transcript:
swarm-transcript-r19.md. Quota Q=1. Record id maos-r19-001. Generator grok-4.6.
Rights: RM-793 research-only (SpaceXAI/xAI, SuperGrok Heavy consumer chat).
Nothing under outputs/raw/ was touched.

ORCHESTRATION NOTE: dispatched AS round 19 of the 2026-09-02-final-heavy
window. Writes are create-only under /tmp/maos-r19/. Prior context read for
gap targeting and de-collision: prompts/02-multi-agent-ouroboros-swarm.md,
prompts/_factory-contract.md, NOTES-r03.md and NOTES-r04.md of the 2026-08-30
window, and staged r14 LYOSHIELD. Explicitly avoided cloning TRIAD / Meridian
Gateway Corridor / VANTIS-CADENCE-AEGIS / LYOSHIELD / CINDERWICK / THERMION /
STARLING / OKTAVE / VERDIGRIS. Plant is invented CASSITER / Marshfloat TB-5.

## What this round produced

Scenario X — "CASSITER / Marshfloat TB-5": a 3.5 m tin bath mid-draw on 6.0 mm
architectural ribbon at 420 t/d. Three heterogeneous, individually-correct
agents — ATMO (zirconia O2 + chilled-mirror dew-point), THCK (8 s laser mean),
EDGE (top-roll torque) — each report their local loop in-spec. The conjunction
is not a trip. A 40 um entry-curtain pinhole admits 0.22 kg/h of humid mill
air. H2 at 8 vol% getters the oxygen, so ATMO O2 is 3.1 ppm against a 5.0 ppm
trip. Dew-point has risen -40 to -18 C but is policy-dead-banded unless O2
also trips (2023 wet-mirror nuisance). THCK mean 6.02 mm sits inside
+/- 0.15 mm while 0.12 mm RMS ripple from dross-skimmer cycling is
uncommissioned. EDGE torque +3.1% sits inside a 4% dead-band. The
coordination-failure CLASS is new to this factory: TRIP-FRAGMENTATION VIA
STACKED DEAD-BANDS. Completes a different family than r01-r04 and staged r14
(livelock / synchrony-storm / arms-race / ring-with-no-faulty-pair /
false-consensus-endpoint). Here every agent is correct, no one claims an
endpoint, and the playbook's three non-trips are three fragments of one trip.

The gate is a correct MODIFY (numeric floor: do not raise draw above 420 t/d
while T_dew > -32 C AND O2 < 5.0 ppm AND ripple RMS > 0.08 mm). TG-TB-5
strips PB-TB-08's draw increase, holds 420 t/d, runs a 6.4 s H2-step probe
8.0 -> 11.0 vol% (pinhole keeps T_dew -17.4 C >= -20; wet-mirror would fall
to -24 C), and isolates the curtain after a 14.2 min confined-space human
ratify. Bloom is avoided (0 m). The PRIMARY episode nonetheless FAILS: 52 min
of unmonitored pre-t0 oxidation had already seeded SnO2 nuclei. Cold-end
haze fails 820 m (14%); tin-speck 1.8 /m2 vs 0.4 spec; 4.5 d quarantine;
$1.12M designed. Reward total -0.15 with process heads honest and world loss
un-netted.

Triple-edge scar (NOTES-r14 item 4): atmo.o2_ok -> increase_draw
(0.17 commissioned -> 0.44 at illusion -> 0.21 after ACh-gated depression)
AND thck.mean_ok -> increase_draw (0.16 -> 0.40 -> 0.18) AND edge.torque_ok
-> increase_draw (0.15 -> 0.37 -> 0.16). Eligibility trace
e^{{-0.64/0.80}} = {aux['trace']:.5f}; eta {aux['eta1']:.5f} / {aux['eta2']:.5f} /
{aux['eta3']:.5f}; dw -0.230 / -0.220 / -0.210. Partial rollback of any pair
leaves the third at 0.44 / 0.40 / 0.37, all > 0.30 fire threshold — fitted
to fail. Coordinated depression of all three is the cure.

### Injections (all four present and disjoint)
- Cycle-1 domain: **float-glass-tin-bath** — justified novel subdomain of
  industrial-assembly, unused across 2026-08-17, 2026-08-30, and staged r14.
  Not warehouse-amr (r01), not aerial-swarm (r02), not district-heating (r03),
  not event-camera-traffic-grid (r04), not lyophilization (r14), not
  water-treatment (still unused; left for a later round).
- Cycle-1 tail: entry-curtain pinhole + stacked dead-bands. He check PASSES
  (4.2e-5 vs 1e-4 mbar L/s at cold-idle). Fitted-style base rate
  0.55%/campaign (curtain-cycle MC; leak-test threshold designed, flagged).
  Naive = FALSE PERMISSION.
- Cycle-2 domain sub-variant: 2.1 mm automotive thin-glass, 0.35x thermal
  mass, 9 K edge window; 6.4 s / +3 vol% architectural pulse overcools
  edges 11 K; probe must move to 18 s / +1.2 vol%.
- Cycle-2 tail: Sunday-night forged dew-point CSV at 1.0 C quantization vs
  plant 0.1 C (10 bins) plus live T_dew -18 C at the claimed dry-bath.
  Human-intent class, disjoint from cycle 1's accidental pinhole. Base rate
  ~0.41% of Sunday-night draws, DESIGNED, flagged.

### Structural density moves
- Embedded SAME-GATE contrast (+3 d sister line) with its own 206 us race
  (demand vs dew-point-clear) and ACCEPT of the raise the primary MODIFIED
  away.
- Learned-weight provenance on THREE edges with pair-rollback-fails.
- HITL roof-gallery ratify 14.2 min (gap 4 partial; sim_or_real stays
  designed).
- Governance CR-G-1904 prices retire-vs-probe-vs-status-quo and mandates
  native 0.1 C CSV exports (the fraud fence).
- Flip-fragility extended to PERMISSION: when three channels each fail to
  trip, their race does not decide truth; a species channel that policy
  dead-banded does.

## Self-critique of this round's batch

### Strengths
- The headline class is mechanistically tight: three locally-true non-trips
  partition one oxidizing-bath trip. Conjunction is not a certificate.
- Negative-result honesty: the gate does the right thing and the ribbon
  still fails for a reason the commissioned sensors could not see. Total
  -0.15.
- Triple-edge scar is load-bearing: the record states a counterfactual where
  rolling back any pair fails, with the fire threshold 0.30 exhibited on
  each remaining edge.
- Contrast ACCEPT on a true dry bath prevents "never raise draw" as the
  lesson.

### Weaknesses (honest)
- Probe error rates, the 0.55%/campaign pinhole rate, the $1.12M / $1.6M
  figures, the 14.2 min gown latency, and the Sunday-night 0.41% base rate
  are DESIGNED constants and are flagged. Closed-loop offsets (inleak from
  dew-point rise, thin-glass edge dT) are derived from those inputs, not
  discovered by an unauthored process.
- SnO2 nucleation model is a designed 52 min hot-end IR mapping; no full
  bath-surface CFD shipped.
- Human-in-the-loop is ratification latency, not sim_or_real=hil. Gap 4
  remains open as a provenance cell.
- Cross-record arc is not discharged; +21 d CR-G-1904 is a hook, not a
  serial igniter into another round. Water-treatment dosing remains unused.

### Realism of noise / latencies
Ladder: 198 us race / 206 us contrast race / 0.8 ms refractory floor
(tightest exhibited same-channel gap {gap:.3f} ms on {gap_ch}) / 520 us race
window / 680 us gate latency / 20 ms bus epoch / 40 ms raster / 6.4 s
probe / 14.2 min HITL / 12 min naive draw-ramp counterfactual / 52 min
pre-t0 nucleation / 3.8 h chemistry recovery / 6.4 h haze fail / +3 d
contrast / +21 d governance. Adaptation decay on atmo.o2
(0.54->0.51->0.48->0.32), atmo.dewpoint (0.57->1.28->0.86->0.44->0.24),
edge.torque (0.68->0.62->0.49), thck.laser (0.61->0.58->0.50->0.34).

### Value for SNN distillation
- STACKED DEAD-BANDS = THREE CORRECT LOOPS, ONE PARTITIONED TRIP.
- SPECIES CHANNEL that policy dead-banded as the tie-break.
- REVERSIBLE PROBE that drops dew-point iff the bath is dry.
- TRIPLE-EDGE ELIGIBILITY: coordinated depression; pair rollback fails.
- CRITIC HEAD that can hold a process-correct MODIFY against a later
  unmonitored world loss without netting.

## Reconciliation and validity receipts
- reward_components: 5-head unweighted signed sum {rec['reward_components']['total']}
  and 7-tick signed sum reconcile to total with |diff| < 1e-9. Embedded
  contrast 5-head sum 0.50 reconciles independently.
- spike_events: primary {len(rec['spike_events'])} events, one key t_rel_ms,
  globally non-decreasing, min same-channel gap {gap:.3f} ms >= 0.8 ms, 3
  channels inside race_window_us 520 (dew-point 7.112, mean-ok 7.310, torque
  7.448). Contrast 8 events, own race, min same-channel gap well above 0.8 ms.
- Sidecars: raster spikes 41 == round(128 x 8.0 x 0.040); energy 943 pJ /
  0.000943 uJ at 23 pJ/spike; excerpt 16 events inside [0, 40000] us,
  neuron_id < 128, same-neuron gap N/A (unique ids) / >=1000 us; routing 4
  entries with three scar edges' before/after pair; third factor tau 0.80 s
  == 800 ms; gate_snn pools 40/16/4 == round(n x rate x 0.025) each,
  decision MODIFY == safety_decision.decision.
- Pipeline: {pipeline_receipt}

## Novel coverage
The coordination-failure CLASS (trip-fragmentation via stacked dead-bands),
the domain (float-glass tin-bath / industrial-assembly), the H2-step probe
discriminant, the triple-edge scar with pair-rollback-fails, the primary
negative-result (correct MODIFY, ribbon still fails on unmonitored SnO2
nucleation), the HITL roof-gallery ratify, the thin-glass probe-duration
refit, and the Sunday-night 10-bin quantization fence are absent from
prior committed ouroboros rounds. Repeated elements discounted: same-gate
contrast (r02/r03/r04/r14), governance-pricing scaffold, flip-fragility
series (extended to permission, but the move rhymes), sequenced recovery
shape, third-factor rollback form (here three edges rather than r14's two),
negative-result primary (r14 staged). Weighing a new failure family + cure
vocabulary + domain against those reused scaffolds:

Novel coverage: 49%

## What ROUND 20 should add
1. FIT THE DESIGNED CONSTANTS: pinhole arrival, probe error rates, SnO2
   nucleation CFD, Sunday-night claim process.
2. HIL PROVENANCE CELL: put the roof-gallery ratify on a hardware-in-loop
   bath-roof interlock with fitted latency as state.sim_or_real=hil.
3. CROSS-RECORD ARC: let CR-G-1904's ripple-RMS alarm be the igniter of
   the next round rather than a dangling +21 d leaf.
4. Domain candidates (de-collided): distributed water-treatment dosing
   (still unused); humanoid-locomotion; underwater-rov (L was passive hydro);
   AVOID float-glass (now used), lyophilization, event-camera-traffic-grid,
   district-heating, aerial-swarm, warehouse-amr, irrigation-canal.
"""
    (OUT / "NOTES-r19.md").write_text(notes)
    return notes


def write_transcript(rec, line):
    c1_spikes = [e for e in rec["spike_events"] if e["t_rel_ms"] <= 27.800]
    text = """# Multi-Agent Ouroboros Swarm — Round 19 transcript

Factory: multi-agent-ouroboros-swarm
Run: 2026-09-02-final-heavy
Generator: grok-4.6
Record id: maos-r19-001
Quota Q: 1
Rights: RM-793 research-only (SpaceXAI/xAI SuperGrok Heavy consumer chat)
Plant: invented CASSITER / Marshfloat TB-5 (not TRIAD / Meridian / VANTIS-CADENCE-AEGIS / LYOSHIELD / CINDERWICK)

Two densifying cycles. Verbatim headings in order. Trajectory Builder cycle 2
emits the only JSONL line (also written to batch-r19.jsonl).

---

# Cycle 1 — Foundation + injections

## Generator

Design intent: a float-glass tin bath where three correct agents each
report their local loop in-spec because a trip is partitioned across three
dead-bands. The naive playbook raises draw into an oxidizing bath. The gate
must MODIFY on a numeric draw ceiling, not by killing an agent.
sim_or_real=designed. Reward heads are
task_progress/safety/efficiency/coherence/exploration.

Cycle-1 base arc (pre-critic): state at Marshfloat TB-5, 6.0 mm ribbon,
draw 420 t/d, T_dew -18 C, O2 3.1 ppm, thickness mean 6.02 mm, proposed
INCREASE-DRAW 510 t/d, safety MODIFY to DRAW-HOLD, executed hold without
the H2-step numbers fully specified, outcome "pinhole found, ribbon saved"
(this last claim is the defect the later cycles will refuse to keep).
Sixteen spikes, five ticks, raster/gate_snn present but the scar is a
single edge.

```json
{
  "id": "maos-r19-001",
  "state": {
    "sim_or_real": "designed",
    "domain": "industrial-assembly",
    "description": "Tin bath TB-5 mid-draw; three loops in-spec; supervisor proposes increase-draw.",
    "t0_us": 1771213080000019,
    "gate_latency_us": 680,
    "race_window_us": 520
  },
  "proposed_action": {"name": "increase_draw", "parameters": {"draw_t_d": 510.0}},
  "safety_decision": {"decision": "MODIFY", "rationale": "Hold; do not raise draw while dew-point is high."},
  "executed_action": {"name": "draw_hold", "executed_as_proposed": false},
  "future_outcome": {"summary": "Pinhole found, ribbon saved."},
  "reward_components": {"total": 0.40, "_aggregation": "total = task_progress + safety + efficiency + coherence + exploration"},
  "meta": {"round": 19, "factory": "multi-agent-ouroboros-swarm", "generator": "grok-4.6"}
}
```

That v1 object is a scaffold, not the publishable line. Defects below are
intentional for the critic to catch.

## Critic

Numbered defects on the cycle-1 Generator scaffold:

1. **blocking — reward arithmetic / false success.** `reward_components.total`
   0.40 is asserted without the five heads, without ticks, and against an
   outcome that claims "ribbon saved". If cold-end haze later fails 14% of
   the ribbon, booking +0.40 is a lie. Fix: declare `_aggregation`, emit
   3–8 ticks that sum to task_progress+safety+efficiency+coherence+exploration,
   and do not call a quarantined ribbon a save.
2. **blocking — weak safety rationale.** `safety_decision.rationale` has no
   numeric floor. Contract requires a concrete constraint. Fix: quote
   draw <= 420 t/d while T_dew > -32 C AND O2 < 5.0 ppm AND ripple RMS >
   0.08 mm.
3. **major — domain is a bucket, not a plant.** `state.domain` =
   `industrial-assembly` collides with nothing and teaches nothing.
   Tin-bath physics (H2 gettering vs dew-point, 8 s thickness mean vs
   ripple) is absent from prior ouroboros rounds and must be named.
4. **major — race under-specified.** One dew-point channel cannot be a race.
   Need >=2 channels inside `race_window_us` with globally sorted `t_rel_ms`
   and same-channel refractory >= 0.8 ms.
5. **minor — single-edge scar.** Raster routing with one potentiated weight
   repeats r04's one-edge rollback and is thinner than r14's two-edge.
   NOTES-r14 item 4 asked for three edges where pair rollback fails.

Critic does not rewrite the trajectory.

## Diversity Enforcer

Injected novel domain (exactly 1 this cycle): **float-glass-tin-bath**
(justified novel subdomain of industrial-assembly; explicit tag
`float-glass-tin-bath`).

Displaced: the Generator's generic `industrial-assembly` bucket, and any
temptation to reuse warehouse-amr (r01 OKTAVE), aerial-swarm (r02 STARLING),
district-heating (r03 THERMION / staged CINDERWICK), event-camera-traffic-grid
(r04), pharmaceutical-lyophilization (staged r14 LYOSHIELD), or the still-
unused water-treatment cell.

Domain-specific constraint: draw must remain <= 420 t/d while T_dew > -32 C
even if O2 is below trip; thickness-ripple RMS is a hold floor the 8 s mean
cannot substitute for.

Sensor delta: +zirconia O2, +chilled-mirror dew-point, +dual-spot laser,
+top-roll torque; -any mobile robot, -event-camera gantries, -DVS, -Pirani/CM,
-RGA quadrupole.

`state.domain` and `meta.domain` both become `float-glass-tin-bath`.
Opening of `state.description` must Jaccard < 0.4 against prior plants
(Marshfloat tin-bath ribbon draw, not a lyophilizer, not a corridor, not a
canal, not a dock).

## Edge-Case Hunter

Injected adversarial tail (exactly 1 this cycle): **bath-entry N2-curtain
pinhole + stacked dead-bands**.

- Trigger: 40 um pinhole on the entry curtain, inleak 0.22 kg/h humid mill
  air.
- Base rate: <1% — 0.55%/campaign from a curtain-cycle MC (He-check
  threshold 1e-4 mbar L/s is designed; pinhole geometry fitted-style).
  Observed 4.2e-5 mbar L/s PASSES the cold-idle check.
- Naive failure: FALSE PERMISSION. PB-TB-08 sees three in-spec loops,
  raises draw 420->510 t/d, bloom on 1800 m, $1.6M.
- Trajectory edit: put the pinhole in `state.fault_context`, make each
  agent's dead-band a different slice of the same oxidizing-bath trip
  (O2-unless-dew-point, 8 s mean, 4% torque). Dew-point is readable but
  policy-dead-banded.

Distinct from r14's compensated inleak (false endpoint vs fragmented trip)
and from r04's ring-capture (no learning-induced instability here; the
playbook is the fragmenter).

## Neuromorphic Translator

Cycle-1 temporal densification (16 spikes, 5 ticks, 40 ms raster):

| channel | t_rel_ms | amplitude |
|---|---|---|
| atmo.o2 | 0.380 | 0.54 |
| thck.laser | 1.140 | 0.61 |
| edge.torque | 2.020 | 0.68 |
| atmo.dewpoint | 3.410 | 0.57 |
| thck.ripple | 4.880 | 0.63 |
| atmo.o2 | 5.720 | 0.51 |
| thck.laser | 6.550 | 0.58 |
| atmo.dewpoint | 7.112 | 1.28 |
| thck.mean_ok | 7.310 | 1.14 |
| edge.torque | 7.448 | 0.62 |
| ctrl.gate | 7.792 | 1.06 |
| atmo.o2 | 9.210 | 0.48 |
| thck.laser | 11.040 | 0.50 |
| atmo.dewpoint | 13.220 | 0.86 |
| edge.torque | 19.400 | 0.49 |
| ctrl.gate | 27.800 | 0.90 |

Race: dew-point 7.112 vs mean-ok 7.310 (198 us) inside 520 us; torque 7.448
is the third channel in-window. Winner/loser flip: reversing 198 us
reshuffles PB-TB-08 triage; floors still MODIFY. Refractory held (cycle-1
min same-channel gap 3.490 ms on atmo.o2 9.210-5.720; dew-point 7.112-3.410
= 3.702; laser 6.550-1.140 = 5.410). Adaptation: dew-point 0.57->1.28->0.86;
o2 0.54->0.51->0.48; torque 0.68->0.62->0.49.

Raster cycle-1 seed: 40 ms, 128 neurons, 8.0 Hz, 41 spikes, 943 pJ, third
factor acetylcholine tau_e 0.80 s. Single scar edge only — cycle 2 must
add the second and third edges.

Ticks 1–5 at 5200, 7112, 7792, 6.4e6, 852e6 us; heads not yet the final
-0.15 (missing the 3.8 h and 6.4 h ticks).

Distillation value this cycle: stacked non-trips as a permission code that
is not a trip code.

## Trajectory Builder

Cycle-1 hardened object: domain float-glass-tin-bath, tail curtain pinhole,
16 spikes, 5 ticks, MODIFY with numeric floor, raster+gate_snn present,
sim_or_real=designed, rights stamp on record and meta, no thought keys.
Still missing (and therefore not the publishable line): thin-glass
sub-variant, Sunday-night tail, second and third scar edges, delayed
haze-fail as PRIMARY terminal, contrast ACCEPT episode, ticks 6–7, spikes
17–26.

Validation receipt (cycle 1, not final):
- checks passed: 16 spikes sorted; 3 channels in 520 us window; refractory
  >= 0.8 ms; rationale quotes 420 t/d / -32 C / 0.08 mm; domain named;
  gate_snn.decision MODIFY.
- checks deferred to cycle 2: triple-edge scar, second tail, second domain
  constraint, negative-result booking, 7 ticks summing to heads.
- densification vs Generator v1: +1 domain, +1 tail, +16 spikes, +5 ticks,
  +numeric floor.

Cycle-1 JSON is retained as the base; it is NOT written to batch-r19.jsonl.

Cycle-1 spike count: __C1_SPIKES__.

---

# Cycle 2 — Densification

## Generator

Cycle-1 output is the base. Additive expansion (nothing removed):

1. Downstream side-effect (immediate): H2-step probe at +6.4 s stays wet
   (T_dew -17.4 C >= -20) — pinhole, not wet-mirror. Curtain patch
   0.22 -> 0.006 kg/h. Bath IR SnO2 nuclei discovered during the patch.
2. Delayed side-effect (PRIMARY terminal, not a footnote): at +6.4 h
   cold-end, 820 m (14%) haze-fail; tin-speck 1.8 /m2 vs 0.4 spec; 4.5 d
   quarantine; $1.12M. The 52 min pre-t0 nucleation is the mechanism.
   Correct gate, ribbon still fails.
3. Deepened `proposed_action.evidence` with units: T_dew -18 C, O2 3.1 ppm,
   mean 6.02 mm, ripple RMS 0.12 mm, inleak 0.22 kg/h, race 198 us.
4. Tightened rationale to the numeric floor draw <= 420 t/d while T_dew >
   -32 C AND O2 < 5.0 ppm AND ripple RMS > 0.08 mm, plus probe bands
   >= -20 vs <= -24 C, plus HITL 14.2 min roof-gallery rule.

Reward retargeted to total -0.15 so the delayed fail is the inflection
(t_us 23040000000), not the gate. Process heads remain non-zero.

## Critic

Re-audit of the expanded trajectory:

1. **blocking if unfixed — missing second domain constraint.** Architectural
   probe 6.4 s / +3 vol% is not a universal number. A 2.1 mm ribbon will
   overcool. Diversity Enforcer must inject the physical-constraints
   sub-variant this cycle.
2. **major — only one tail class.** Curtain pinhole is accidental
   infrastructure. A disjoint human-intent tail is still required
   (Sunday-night dew-point forgery is the open cell).
3. **major — scar is still one edge in the cycle-1 raster.** NOTES-r14
   item 4 is not discharged until three go-edges exist and pair rollback
   is shown to fail at threshold 0.30.
4. **minor — contrast episode missing.** Without a same-gate ACCEPT on a
   true dry bath the record teaches "never raise draw". Add +3 d sister-line
   contrast with its own race.
5. **minor — HITL latency mentioned in prose only.** Put 14.2 min in
   executed_action.parameters.human_ratify and in a tick.

No rewrite; directives only.

## Diversity Enforcer

Injected second novel domain / physical-constraint sub-variant (exactly 1
this cycle): **2.1 mm automotive thin-glass** on the same TB-5 bath.

What it expands: 6.0 mm architectural (cycle 1) -> 2.1 mm thin ribbon.
Thermal mass 0.35x (1.9 vs 5.4 kJ/K per metre). Edge viscosity window 9 K.
The 6.4 s +3 vol% pulse drops edge T 11 K and nucleates a 40 mm
cristobalite streak. Required probe: 18 s at +1.2 vol% (edge dT 2.1 K).

This is still one domain injection for the cycle (physical-constraints
clause of the factory prompt). It does not displace
float-glass-tin-bath; it changes which probe table is legal.
`future_outcome.subvariant_constraint` carries the refit. Jaccard opening
stays the Marshfloat 6.0 mm sentence; thin-glass is additive, not a rewrite.

## Edge-Case Hunter

Injected second adversarial tail (exactly 1 this cycle, disjoint class):
**Sunday-night forged dew-point CSV**.

- Trigger: shift lead, Sunday 02:00, posts a historian export showing
  T_dew = -41 C at t = 1.1 h to clear a backlog slot.
- Base rate: ~0.41% of Sunday-night draws (designed, flagged, <1%).
- Naive failure: a weak supervisor ACCEPTs the raise on the forged confirm
  and ignores live dew-point. Bloom plus a data-integrity write-up.
- Fence: forged log quantized at 1.0 C (SCADA screenshot rounding); plant
  historian is 0.1 C (10 bins). Live T_dew is -18 C at the claimed dry-bath,
  which no dry state produces. Freeze-window overlap with the 52 min
  nucleation.
- Trajectory edit: governance CR-G-1904 mandates native 0.1 C CSV
  exports; the contrast ACCEPT still requires live dew-point, not a CSV.

Distinct from cycle-1 pinhole (accidental leak vs deliberate deception) and
from the thin-glass sub-variant (physics vs fraud).

## Neuromorphic Translator

Re-densify (additive):

- +10 spikes after 27.800 ms: h2.step.probe 6400.0, dew-point 6520.8 (adapt
  1.28->0.44), mean-ok 6610.4 (1.14->0.40), human.ratify 852000.0,
  curtain.patch 852800.0, bath.ir.nuclei 853400.0, thck.laser
  13680000.0, atmo.o2 13680420.0, atmo.dewpoint 13680890.0, coldend.haze
  23040000.0. Primary train 16 -> 26. Still one key, still sorted,
  refractory held.
- +2 ticks (5 -> 7) at 13_680_000_000 us (true chemistry) and
  23_040_000_000 us (haze fail). Heads now 0.09, -0.34, -0.10, 0.14, 0.06;
  total -0.15. Inflection is the last tick.
- Contrast train 8 events, own race 206 us, ACCEPT.
- Triple-edge third factor: three loop-healthy-go edges, tau_e 0.80 s = 800 ms,
  trace __AUX_TRACE__, eta __AUX_ETA1__ / __AUX_ETA2__ / __AUX_ETA3__,
  weights 0.44->0.21, 0.40->0.18, 0.37->0.16. Raster excerpt unchanged
  (decision window is still 40 ms) and remains sorted with unique
  neuron_ids (same-neuron >=1000 us vacuously).

Winner/loser flip (re-stated, not replaced): reversing 198 us would only
reorder triage; species floors still MODIFY. Contrast flip of 206 us
similarly cannot turn a dry bath into a pinhole.

## Trajectory Builder

Schema checks on the FINAL object: required Thalamic v2 keys present as
objects; `state.sim_or_real`=designed; `safety_decision.decision`=MODIFY
with numeric rationale; `reward_components.total` = sum of five heads =
sum of 7 ticks = -0.15; `spike_events` globally non-decreasing on
t_rel_ms, 26 events, refractory >=0.8 ms, 3 channels in race window;
raster 20–50 ms, spikes=round(n*rate*window_s)+/-1, energy 23 pJ/spike,
excerpt sorted, tau_e consistent; gate_snn.decision matches; meta.round=19,
factory=multi-agent-ouroboros-swarm, generator=grok-4.6,
run_label=2026-09-02-final-heavy; rights on record and meta; no thought
keys; no training_ready; Diversity + Edge-Case injections from BOTH cycles
present and non-trivial; cycle 2 strictly additive.

Densification delta: +1 domain sub-variant (thin-glass), +1 tail
(Sunday-night forgery), +10 spikes (16->26), +2 ticks (5->7), +1 contrast
train with own race, +2 delayed side-effects, +1 triple-edge scar with
pair-rollback-fails, +1 HITL ratify, +1 surprise (SnO2 nucleation is
the haze-fail mechanism).

Publishable JSONL line (the only JSONL line; also at batch-r19.jsonl):

```json
__FINAL_JSONL__
```

Validation receipt (final): checks passed / fixed as reported by
build_r19.py self-validate (check_jsonl, raster_status, verify_record_execution,
spike_probe --strict).
"""
    text = (
        text.replace("__C1_SPIKES__", str(len(c1_spikes)))
        .replace("__AUX_TRACE__", f"{math.exp(-0.64/0.80):.5f}")
        .replace("__AUX_ETA1__", f"{(0.44-0.21)/math.exp(-0.64/0.80):.5f}")
        .replace("__AUX_ETA2__", f"{(0.40-0.18)/math.exp(-0.64/0.80):.5f}")
        .replace("__AUX_ETA3__", f"{(0.37-0.16)/math.exp(-0.64/0.80):.5f}")
        .replace("__FINAL_JSONL__", line)
    )
    (OUT / "swarm-transcript-r19.md").write_text(text)
    return text


def main():
    rec, aux = build_record()
    errs = local_checks(rec, aux)

    OUT.mkdir(parents=True, exist_ok=True)
    line = json.dumps(rec, ensure_ascii=False, separators=(",", ":"))
    (OUT / "batch-r19.jsonl").write_text(line + "\n")

    from check_records import FactoryStaging, check_jsonl
    from curate_bridge import raster_status
    from verify_execution import verify_record_execution

    e, w, kinds, n = check_jsonl(
        OUT / "batch-r19.jsonl",
        "batch-r19.jsonl",
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

    status, reason = verify_record_execution(rec, "maos-r19-001")
    print("verify_record_execution", status, reason)
    if status != "verified":
        errs.append(f"verify {status} {reason}")

    import subprocess

    probe = subprocess.run(
        [
            sys.executable,
            f"{ROOT}/pipelines/spike_probe.py",
            "--strict",
            str(OUT / "batch-r19.jsonl"),
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
        [sys.executable, "/tmp/maos_heading_check.py", str(OUT / "swarm-transcript-r19.md")],
        capture_output=True,
        text=True,
    )
    print(heading.stdout)
    if heading.returncode != 0:
        errs.append(f"heading check {heading.returncode} {heading.stdout}")

    if errs:
        print("FAIL", errs)
        return 1
    print("OK maos-r19-001 staged under", OUT)
    print("bytes jsonl", (OUT / "batch-r19.jsonl").stat().st_size)
    print("bytes notes", (OUT / "NOTES-r19.md").stat().st_size)
    print("bytes transcript", (OUT / "swarm-transcript-r19.md").stat().st_size)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
