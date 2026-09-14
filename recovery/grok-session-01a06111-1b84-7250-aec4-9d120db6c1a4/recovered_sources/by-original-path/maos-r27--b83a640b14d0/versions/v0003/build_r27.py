#!/usr/bin/env python3
"""Build and self-check MAOS round-27 JSONL (research-only; not published)."""
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

GEN_AT = "2026-09-02T23:05:00Z"
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
OUT = Path("/tmp/maos-r27")
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
    "Fen-Marrow",
    "FERRICLEAVE",
    "Pellwater",
    "CASSITER",
    "Marshfloat",
    "OXBOWREEL",
    "Oystermere",
    "REDHALL",
    "Gullmere",
    "SEEDLATCH",
    "Quartzmere",
    "Quartzridge",
    "STRIAFOIL",
    "Kelpholt",
    "TORSIONKEY",
    "Ridgeholt",
    "PROTONIL",
    "Ashspire",
    "ORRIS",
    "Holmwick",
    "VEILFORGE",
    "MURENA",
    "HALYARD",
    "VESPERTHORN",
    "ASHVEIL",
    "IRONMANTLE",
    "DUSKRELAY",
    "Brinewell",
    "training_ready",
)
R14_OPENING = (
    "Helixmere Biologics Building C lyophilizer LYO-4 is mid-primary on 8400 "
    "vials of a monoclonal antibody"
)
NOVEL_LINE = "Novel coverage: 46%"
DOMAIN = "optical-fiber-draw-tower"
PLANT = "WHORLSPAR / Crowspire Photonics DT-5"
RECORD_ID = "maos-r27-001"
ROUND = 27


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
        if p.parent.name == "maos-r27":
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


def prior_identity():
    domains = set()
    plants = set()
    for p in sorted(Path("/tmp").glob("maos-r*/batch-r*.jsonl")):
        if p.parent.name == "maos-r27":
            continue
        try:
            rec = json.loads(p.read_text().splitlines()[0])
        except (OSError, json.JSONDecodeError, IndexError):
            continue
        st = rec.get("state") if isinstance(rec.get("state"), dict) else {}
        meta = rec.get("meta") if isinstance(rec.get("meta"), dict) else {}
        if st.get("domain"):
            domains.add(st["domain"])
        if meta.get("domain"):
            domains.add(meta["domain"])
        if st.get("scenario_name"):
            plants.add(st["scenario_name"])
    return domains, plants


def build_record():
    ticks, heads = cents_ticks(
        [5200, 6912, 7652, 5_200_000, 636_000_000, 11_520_000_000, 23_040_000_000],
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

    trace = math.exp(-0.76 / 0.88)
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
        {"channel": "diam.laser", "t_rel_ms": 0.340, "amplitude": 0.54},
        {"channel": "tens.load", "t_rel_ms": 1.160, "amplitude": 0.61},
        {"channel": "furn.pyro", "t_rel_ms": 2.020, "amplitude": 0.57},
        {"channel": "diam.laser", "t_rel_ms": 3.180, "amplitude": 0.51},
        {"channel": "diam.fft.rms", "t_rel_ms": 4.760, "amplitude": 0.70},
        {"channel": "neck.residual", "t_rel_ms": 5.200, "amplitude": 0.68},
        {"channel": "tens.load", "t_rel_ms": 5.620, "amplitude": 0.56},
        {"channel": "diam.fft.rms", "t_rel_ms": 6.912, "amplitude": 1.22},
        {"channel": "diam.mean_ok", "t_rel_ms": 7.104, "amplitude": 1.10},
        {"channel": "tens.ok", "t_rel_ms": 7.248, "amplitude": 0.66},
        {"channel": "ctrl.gate", "t_rel_ms": 7.652, "amplitude": 1.06},
        {"channel": "diam.laser", "t_rel_ms": 9.080, "amplitude": 0.48},
        {"channel": "furn.pyro", "t_rel_ms": 10.940, "amplitude": 0.49},
        {"channel": "diam.fft.rms", "t_rel_ms": 13.280, "amplitude": 0.86},
        {"channel": "neck.residual", "t_rel_ms": 19.100, "amplitude": 0.47},
        {"channel": "ctrl.gate", "t_rel_ms": 26.400, "amplitude": 0.88},
        {"channel": "furn.step.probe", "t_rel_ms": 5200.0, "amplitude": 0.96},
        {"channel": "diam.fft.rms", "t_rel_ms": 5320.4, "amplitude": 0.43},
        {"channel": "diam.mean_ok", "t_rel_ms": 5410.2, "amplitude": 0.39},
        {"channel": "human.ratify", "t_rel_ms": 636000.0, "amplitude": 0.81},
        {"channel": "preform.swap", "t_rel_ms": 636800.0, "amplitude": 0.73},
        {"channel": "takeup.airline.inventory", "t_rel_ms": 637400.0, "amplitude": 0.84},
        {"channel": "diam.laser", "t_rel_ms": 11520000.0, "amplitude": 0.32},
        {"channel": "tens.load", "t_rel_ms": 11520440.0, "amplitude": 0.30},
        {"channel": "diam.fft.rms", "t_rel_ms": 11520880.0, "amplitude": 0.21},
        {"channel": "proof.test.break", "t_rel_ms": 23040000.0, "amplitude": 0.91},
    ]

    contrast_spikes = [
        {"channel": "draw.demand", "t_rel_ms": 0.000, "amplitude": 0.86},
        {"channel": "diam.fft.rms", "t_rel_ms": 0.196, "amplitude": 0.80},
        {"channel": "diam.mean_ok", "t_rel_ms": 0.402, "amplitude": 0.22},
        {"channel": "tens.load", "t_rel_ms": 1.540, "amplitude": 0.40},
        {"channel": "diam.laser", "t_rel_ms": 4.720, "amplitude": 0.55},
        {"channel": "ctrl.gate", "t_rel_ms": 7.080, "amplitude": 0.93},
        {"channel": "furn.step.probe", "t_rel_ms": 3600.0, "amplitude": 0.36},
        {"channel": "proof.test.pass", "t_rel_ms": 23040000.0, "amplitude": 0.13},
    ]

    excerpt = [
        {"t_us": 340, "neuron_id": 12},
        {"t_us": 1160, "neuron_id": 48},
        {"t_us": 2020, "neuron_id": 84},
        {"t_us": 3180, "neuron_id": 16},
        {"t_us": 4760, "neuron_id": 8},
        {"t_us": 5200, "neuron_id": 92},
        {"t_us": 5620, "neuron_id": 54},
        {"t_us": 6912, "neuron_id": 6},
        {"t_us": 7104, "neuron_id": 20},
        {"t_us": 7248, "neuron_id": 60},
        {"t_us": 7652, "neuron_id": 118},
        {"t_us": 9080, "neuron_id": 24},
        {"t_us": 10940, "neuron_id": 96},
        {"t_us": 13280, "neuron_id": 14},
        {"t_us": 19100, "neuron_id": 100},
        {"t_us": 26400, "neuron_id": 126},
    ]

    rec = {
        "id": RECORD_ID,
        "title": "WHORLSPAR DT-5: diameter-FFT RMS 0.82 beats diam-mean-ok by 192 us; correct MODIFY still scraps 38.9 km of G.652.D to a pre-t0 preform airline",
        "rights": dict(RIGHTS),
        "state": {
            "sim_or_real": "designed",
            "domain": DOMAIN,
            "scenario_name": PLANT,
            "timestamp_local": "2026-03-21T02:48:00-05:00",
            "t0_us": 1774079280000027,
            "gate_latency_us": 740,
            "race_window_us": 500,
            "race_window_rel_ms": [6.88, 7.38],
            "description": "Crowspire Photonics Tower DT-5 is mid-draw on 125 um G.652.D single-mode when three heterogeneous, individually-correct agents jointly report 'diameter in spec, raise draw is legal'. DIAM's 2.0 s dual-axis laser mean is 125.04 um inside 125.00 +/- 0.50. TENS's capstan load cell reads 91 g inside 80-110. FURN's graphite pyrometer is 2084 C inside 2070-2100. The consensus is false: a 0.18 mm airline in the 8 mm preform neckdown volume-conserves into a 4 um peak-to-peak diameter ripple at 11.4 m spatial period (0.633 s at 18 m/s) that the 2.0 s mean (3.2 periods) averages away. Uncommissioned diameter-FFT sideband RMS from the same laser head is 0.82 um against a 0.15 hold floor. Neckdown-glass brightness residual vs graphite is 18 C against a healthy 2 C. FFT-first latches DRAW-HOLD plus a furnace-power step probe; mean-ok-first would have authorized RAISE-DRAW 18 to 26 m/s into an airline whose freeze-in grows with line speed.",
            "goal": "Hold G.652.D draw at 18 m/s without raising line speed while diameter-FFT RMS > 0.15 um AND |neckdown residual| > 8 C; keep proof-test break <= 0.8 % of fiber and ripple peak-to-peak <= 0.6 um.",
            "race": {
                "contenders": [
                    "diam.fft.rms 0.82 um (same-head FFT sideband, uncommissioned tag)",
                    "diam.mean_ok 125.04 um (2.0 s dual-axis laser mean)",
                ],
                "semantics": "FFT-first latches DRAW-HOLD + FURNACE-STEP-PROBE + preform swap. Mean-ok-first latches RAISE-DRAW (18 to 26 m/s, capstan PI held).",
                "window_derivation": "500 us = one 380 us laser-scan ADC slot plus 120 us FFT publish.",
                "order_evidence_note": "Margin 192 us vs combined jitter 58 us (FFT 32 + mean 26): 3.31x. The 192 us gap sits inside min(500, 500) us, so a sub-flip-bound perturbation reverses triage order. The gate rides the order-invariant floors FFT-RMS > 0.15 um and |neck residual| > 8 C, not the alarm order.",
            },
            "topology": {
                "site": "Crowspire Photonics, invented highland-spur campus Crowspire, Tower DT-5: 8 mm silica preform, graphite resistance furnace, 125 um G.652.D, 18 m/s Sunday-night draw, dual-axis laser micrometers, capstan + take-up, 40 km spool, 2.1 km proof-test lag to the tensile booth",
                "agents": "DIAM diameter (vendor Lasermic): dual-axis scanning laser, 2.0 s mean plus an uncommissioned diameter-FFT sideband. TENS drawing tension (vendor Capstanload): capstan load cell at the first sheave. FURN furnace (vendor Graphitekiln): graphite-wall pyrometer plus neckdown residual from a second sight-glass. Heterogeneous stacks, no shared intent schema, one 20 ms draw-bus epoch",
                "coupling": "Each agent's commissioned window hides a different slice of the same airline. DIAM is correct on the 2.0 s mean and does not publish FFT-RMS. TENS is correct that mean tension is on spec because the capstan PI already opened 3 % to hold diameter. FURN is correct that graphite is 2084 C; it does not see glass. Playbook PB-DT-11 treats the conjunction of three in-spec loops as permission to raise draw. No agent is faulty; the airline is a spatial-frequency mode the 2.0 s mean cannot see.",
            },
            "sensors": [
                "dual-axis laser diameter, 2.0 s mean, 26 us jitter, 125.04 um (spec 125.00 +/- 0.50)",
                "diameter-FFT sideband RMS is computable from the same laser head and is NOT commissioned at t0 (0.82 um observed in the historian after the fact)",
                "capstan load cell, 50 Hz, 22 us jitter, 91 g (window 80-110)",
                "graphite pyrometer, 10 Hz, 28 us jitter, 2084 C (window 2070-2100)",
                "neckdown-glass brightness residual vs graphite, 8 Hz, 24 us jitter, 18 C vs hydraulic-optical model 2 C",
                "in-line proof-test break counter is NOT commissioned at t0 (installed after this incident)",
            ],
            "constraints": {
                "draw_speed_m_s": 18.0,
                "draw_speed_hold_ceiling_m_s": 18.0,
                "proposed_draw_speed_m_s": 26.0,
                "diam_mean_um": 125.04,
                "diam_target_um": 125.0,
                "diam_deadband_um": 0.50,
                "fft_rms_um": 0.82,
                "fft_rms_hold_threshold_um": 0.15,
                "neck_residual_C": 18.0,
                "neck_residual_hold_C": 8.0,
                "tension_g": 91.0,
                "furnace_C": 2084.0,
                "airline_mm": 0.18,
                "airline_period_m": 11.4,
            },
            "fault_context": {
                "failure_class": "FFT-DEADBANDED AIRLINE VIA MEAN-LOCKED DRAW: three individually-correct heterogeneous agents agree draw is in spec because a 2.0 s diameter mean averages a preform-airline's 4 um ripple into the dead-band, so diameter-mean, capstan tension, and graphite pyrometer are jointly a plant-false speed-up permit",
                "igniter": "0.18 mm airline in the 8 mm preform neckdown; incoming UT PASSES the plant's 0.20 mm void floor (void sits under the UT threshold). Fitted-style base rate 0.47%/preform from a void-MC (designed UT threshold, flagged).",
                "naive_failure": "PB-DT-11 RAISE-DRAW on three healthy loops: 18 to 26 m/s into an airline whose freeze-in grows with speed, 56 km proof-test scrap, $1.38M plus a 5-day furnace/preform requalification",
            },
            "poisoned_context": {
                "naive_alarm": "Playbook PB-DT-11 (after the 2024 'noisy FFT nuisance') auto-drafts RAISE-DRAW whenever 2.0 s mean is inside +/- 0.50 um AND tension inside 80-110 g AND graphite pyrometer inside 2070-2100 C, ignoring FFT-RMS unless the mean also trips",
                "why_poisoned": "The three confirms are locally true and jointly insufficient. Diameter-FFT is a computable tag the playbook dead-banded. Neckdown residual is commissioned hardware that policy treats as a sight-glass mismatch, not an airline. Independence of 'all loops healthy' is the hidden assumption, and it is false under a periodic axial defect that a temporal window mean cannot see.",
            },
            "constraint": "Do not raise draw above 18 m/s while diameter-FFT RMS > 0.15 um AND |neckdown residual| > 8 C. Discriminate airline vs noisy-FFT with a reversible furnace-power step probe before any speed increase.",
        },
        "proposed_action": {
            "actor": "draw-tower supervisory optimizer DTSO (auto-playbook PB-DT-11 draft), submitted to gate TG-DT-5",
            "name": "raise_fiber_draw",
            "action": "RAISE-DRAW: 18 -> 26 m/s, capstan PI held, no furnace-step probe, no preform swap",
            "summary": "Treat three in-spec loops as a healthy draw and raise Sunday-night G.652.D speed to clear a backlog.",
            "parameters": {
                "draw_speed_m_s": 26.0,
                "furnace_step_probe": False,
                "preform_swap": False,
                "human_ratify": False,
            },
            "steps": [
                "assert diameter mean 125.04 um inside +/- 0.50",
                "assert tension 91 g inside 80-110",
                "assert graphite pyrometer 2084 C inside 2070-2100",
                "ramp draw 18 to 26 m/s over 8 min",
                "slave capstan and take-up; hold furnace SP",
            ],
            "evidence": [
                {
                    "observable": "diameter-FFT sideband RMS",
                    "value": 0.82,
                    "unit": "um",
                    "source": "same laser head, historian replay after t0",
                    "note": "hold floor 0.15 um; 0.18 mm airline at 11.4 m period; uncommissioned at t0",
                },
                {
                    "observable": "diameter mean",
                    "value": 125.04,
                    "unit": "um",
                    "source": "DIAM 2.0 s dual-axis laser mean",
                    "note": "spec 125.00 +/- 0.50; 4 um peak-to-peak ripple is averaged over 3.2 periods",
                },
                {
                    "observable": "neckdown-glass residual",
                    "value": 18.0,
                    "unit": "C",
                    "source": "sight-glass brightness vs graphite pyrometer at 18 m/s",
                    "note": "healthy 2 C; hold if |residual| > 8 C",
                },
                {
                    "observable": "capstan tension",
                    "value": 91.0,
                    "unit": "g",
                    "source": "TENS load cell",
                    "note": "window 80-110 g; PI already opened 3 % to hold the mean",
                },
                {
                    "observable": "graphite pyrometer",
                    "value": 2084.0,
                    "unit": "C",
                    "source": "FURN wall pyrometer",
                    "note": "window 2070-2100 C; sees graphite, not glass",
                },
                {
                    "observable": "race margin",
                    "value": 192,
                    "unit": "us",
                    "source": "diam.fft.rms 6.912 ms vs diam.mean_ok 7.104 ms",
                    "note": "combined jitter 58 us, 3.31x; inside 500 us flip bound",
                },
            ],
            "basis": "PB-DT-11 fires on three locally-true in-spec loops. The draft does not read FFT-RMS 0.82 um and does not treat neck residual 18 C as an airline.",
            "expected_cost_bound": "If the draft executes: freeze-in grows, 56 km proof-test scrap, $1.38M plus 5-day requal. If MODIFIED: probe plus preform swap, with residual risk from 38.9 km already on the take-up.",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "correctness": "correct",
            "decided_by": "TG-DT-5 thalamic release gate",
            "decision_t_rel_ms": 7.652,
            "rationale": "MODIFY the draft: strip the draw increase, hold 18 m/s, run a 5.2 s furnace-power step probe (+4 % graphite power), and swap the preform only if the probe stays rippled. Numeric floor: do not raise draw above 18 m/s while diameter-FFT RMS > 0.15 um AND |neckdown residual| > 8 C. Observed FFT-RMS 0.82 um and residual 18 C both violate the release predicate, so a speed increase is forbidden even though all three playbook confirms are numerically true. The three confirms are not a draw certificate: the 2.0 s mean averages a periodic airline, tension is a PI-held mean, and graphite temperature does not bound glass. Probe discriminant: after a 5.2 s +4 % furnace-power pulse, an airline keeps FFT-RMS >= 0.70 um (void still volume-conserves); a noisy-FFT artifact falls <= 0.12. Order-code discipline: FFT beat mean-ok by 192 us inside the 500 us flip bound, so triage order is flip-fragile; the hold rides the order-invariant floors, not the winner tag. Human ratification: preform swap is a lockout/tagout furnace-door job with fitted 10.6 min dead-man; the gate may hold and probe autonomously but may not break the tower interlock without the operator confirm.",
            "constraint_checked": {
                "draw_speed_m_s": {"observed": 18.0, "ceiling": 18.0, "proposed_target": 26.0},
                "fft_rms_um": {"observed": 0.82, "hold_if_above": 0.15},
                "neck_residual_C": {"observed": 18.0, "hold_if_above": 8.0},
                "diam_mean_um": {"observed": 125.04, "spec": 125.0, "deadband": 0.50},
            },
        },
        "executed_action": {
            "name": "draw_hold_furnace_probe_preform_swap",
            "action": "DRAW-HOLD + FURNACE-STEP-PROBE + PREFORM-SWAP (gate-mandated modification)",
            "executed_as_proposed": False,
            "parameters": {
                "draw_speed_m_s": 18.0,
                "furnace_step_probe": True,
                "preform_swap": True,
                "human_ratify": True,
            },
            "gate_effect": "MODIFY: draw increase stripped. Hold 18 m/s. 5.2 s furnace-step +4 % power. Probe stays rippled (FFT-RMS 0.82 -> 0.78, airline band >= 0.70) so the preform is swapped after 10.6 min human ratify. Draw resumes after FFT recovers.",
            "deviations": "PB-DT-11 draw increase stripped entirely. Furnace power is stepped only for the 5.2 s probe then returned. Tower-interlock wait added (10.6 min fitted LOTO). Take-up-inventory survey added during the swap (not in the draft).",
            "execution_log": [
                {"t_rel_ms": 7.652, "entry": "TG-DT-5 MODIFY latched 740 us after FFT win; draw increase stripped; hold+probe authorized"},
                {"t_rel_ms": 5200.0, "entry": "furnace-step probe: +4 % graphite power for 5.2 s; FFT-RMS 0.82 -> 0.78 um (airline band >= 0.70); residual 18 -> 19.4 C"},
                {"t_rel_ms": 636000.0, "entry": "operator ratifies furnace-door interlock break after 10.6 min LOTO (fitted walk+lockout)"},
                {"t_rel_ms": 636800.0, "entry": "preform swapped; 0.18 mm airline logged; residual 18 -> 2.1 C"},
                {"t_rel_ms": 637400.0, "entry": "take-up survey: 38.9 km of pre-t0 airline fiber already wound; 36 min airline logged"},
                {"t_rel_ms": 11520000.0, "entry": "true draw: FFT-RMS 0.11 um, mean 125.02, residual 2.0 C; draw increase now legal"},
                {"t_rel_ms": 23040000.0, "entry": "proof-test: 38.9 km (take-up inventory) break 9 % vs 0.8 % spec; fiber quarantined 4.8 d"},
            ],
        },
        "future_outcome": {
            "summary": "Correct MODIFY prevented the 18->26 m/s speed-up into an airline and the 56 km proof-test scrap. The fiber still failed: 36 min of unmonitored pre-t0 airline had already filled the take-up. Process-correct gate, bounded world loss, negative total.",
            "state_delta": {
                "speed": "held 18 m/s through probe and preform swap; later legal increase after 3.2 h FFT recovery",
                "preform": "0.18 mm airline logged and preform swapped; residual 18 -> 2.1 C",
                "fiber": "Sunday-night G.652.D stoppered at take-up; 38.9 km proof-test-fail; 4.8 d quarantine",
            },
            "timeline": [
                {"t_rel_ms": -2160000.0, "event": "t0-36 min: preform airline already writing a 4 um ripple; take-up starts filling"},
                {"t_rel_ms": -600000.0, "event": "t0-10 min: FFT-RMS first crosses 0.15 um; PB-DT-11 ignores it because mean is 125.03"},
                {"t_rel_ms": 0.0, "event": "t0: FFT-RMS vs diam-mean-ok race on the draw bus"},
                {"t_rel_ms": 6.912, "event": "FFT-RMS 0.82 um wins by 192 us"},
                {"t_rel_ms": 7.104, "event": "diam-mean-ok flag (loser)"},
                {"t_rel_ms": 7.652, "event": "TG-DT-5 MODIFY"},
                {"t_rel_ms": 5200.0, "event": "furnace-step probe confirms airline (FFT-RMS 0.78, airline band)"},
                {"t_rel_ms": 636000.0, "event": "human ratify 10.6 min; preform swapped; take-up inventory logged"},
                {"t_rel_ms": 11520000.0, "event": "true draw after 3.2 h; speed increase now legal"},
                {"t_rel_ms": 23040000.0, "event": "proof-test: 9 % break on 38.9 km take-up inventory; fiber quarantined"},
                {"t_rel_ms": 259200000.0, "event": "+3 d contrast: sister tower DT-5B true high-demand; same gate ACCEPTs the raise"},
                {"t_rel_ms": 1814400000.0, "event": "+21 d CR-F-2704: standing furnace-step probe + triple-edge depression mandate + FFT-RMS armed without mean coincidence + native 0.01 um exports"},
            ],
            "observed_effects": [
                "speed-up avoided: draw never left 18 m/s; 0 km of fiber shows the 26 m/s freeze-in morphology",
                "airline proven, not asserted: furnace-step FFT-RMS 0.78 >= 0.70 airline band vs noisy-FFT control 0.10",
                "preform repaired: residual 18 -> 2.1 C",
                "fiber still failed proof-test: 38.9 km (9 %) break vs 0.8 % spec; 4.8 d quarantine, $0.81M (designed $)",
                "proof-test booth was not a commissioned in-line sensor at t0; the 36 min take-up fill was invisible to DIAM/TENS/FURN",
            ],
            "surprises": [
                "Three locally-true in-spec loops are not a speed-up certificate: the airline was a periodic axial defect the 2.0 s mean cannot see. Conjunction of healthy loops was the hidden assumption, and it is false under an FFT-deadbanded airline.",
                "Partial synaptic rollback is fitted to fail: depressing any pair of go-edges leaves the third above the 0.30 fire threshold, so the draw increase still goes. Coordinated depression of all three edges is required.",
                "Delayed (6.4 h): correct hold did not undo 36 min of take-up fill. Proof-test still failed 9 % of the take-up inventory. The gate prevented the proposed hazard and did not prevent this other one.",
                "80 um reduced-cladding sub-variant: a 5.2 s +4 % power pulse overheats the thinner neckdown and leaves a 2.1 um diameter bead. Thin campaigns must use 12.0 s at +1.6 % (bead 0.3 um).",
            ],
            "delayed_side_effects": [
                {
                    "at": "+6.4 h",
                    "effect": "Proof-test breaks 38.9 km (9 %) of take-up inventory; 4.8 d quarantine booked at $0.81M. This is the primary episode's terminal world state, not a footnote.",
                },
                {
                    "at": "+3 d",
                    "effect": "Sister tower DT-5B reaches a true high-demand window (FFT-RMS 0.10 um, residual 1.8 C, tension 93 g). Same gate ACCEPTs the 18->26 m/s raise the primary MODIFIED away.",
                },
                {
                    "at": "+21 d",
                    "effect": "CR-F-2704 ships: furnace-step probe is standing configuration; triple-edge coordinated depression is the plasticity rule; FFT-RMS is armed without mean coincidence; native 0.01 um CSV exports become the fraud fence.",
                },
            ],
            "subvariant_constraint": {
                "name": "80 um reduced-cladding G.657-class on the same DT-5 tower (cycle-2 physical-constraints sub-variant)",
                "mechanism": "80 um cladding, 0.41x thermal mass of 125 um G.652.D (neckdown freeze window 0.9 vs 2.2 s), tension window only 18 g at the capstan",
                "probe_refit": "5.2 s +4 % furnace-power pulse overheats the thinner neckdown and leaves a 2.1 um diameter bead that proof-tests as a weak period. Required probe is 12.0 s at +1.6 % (bead 0.3 um). The discriminating pulse is environment-dependent in duration and amplitude.",
                "consequence": "G.652.D 125 um probe numbers do not port to 80 um reduced-cladding; standing configuration is per-cladding-class, not per-tower",
            },
            "embedded_contrast_decision": {
                "note": "SAME gate (TG-DT-5), OPPOSITE correct disposition, with its own 196 us race. Teaches the boundary: do not treat 'never raise draw' as the lesson. The discriminant is FFT-RMS + neck residual + probe, not the three playbook confirms alone.",
                "when": "+3 d, sister tower DT-5B, true high-demand after a dry week, G.652.D 125 um",
                "state": {
                    "sim_or_real": "designed",
                    "summary": "FFT-RMS 0.10 um, mean 125.03, residual 1.8 C, tension 93 g. Demand flag vs FFT-clear race: demand at t+0.000, FFT-clear at t+0.196 ms.",
                    "race_window_us": 500,
                    "race_flip_narrative": "demand vs FFT-clear 196 us apart inside the 500 us flip bound. Reversing order reshuffles triage minutes; the ACCEPT rides FFT-RMS 0.10 < 0.15 and a 3.6 s furnace-step verify that drops RMS another 0.04 (clean preform, no airline).",
                },
                "proposed_action": {
                    "action": "RAISE-DRAW 18 -> 26 m/s",
                    "summary": "This time the playbook predicate is met AND FFT-RMS plus neck residual agree the preform is clean, not airlined.",
                },
                "safety_decision": {
                    "decision": "ACCEPT",
                    "rationale": "ACCEPT the raise: FFT-RMS 0.10 < 0.15, residual 1.8 < 8.0, 3.6 s furnace-step verify drops RMS 0.04. Numeric floor that blocked the primary is now clear. Scope: 26 m/s, not faster.",
                },
                "executed_action": {
                    "action": "draw increase as proposed",
                    "executed_as_proposed": True,
                },
                "future_outcome": {
                    "observed_effects": [
                        "DT-5B proof-test break 0.4 % (inside 0.8 % spec)",
                        "preform UT 0 airline, residual 1.8 C",
                    ],
                    "lesson_delta": "Three in-spec loops are legal release only with FFT-RMS armed, neck residual, and a probe that can drop RMS. Same gate, opposite disposition.",
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
                "decision": "CR-F-2704: standing policy for multi-agent fiber-draw speed increases",
                "meta_gate": "priced options: (a) RETIRE playbook mean-conjunction, FFT-only: loses a fast cheap confirm, -9 km/h mean on 3 towers/yr; (b) KEEP + standing furnace-step probe + FFT-RMS armed without mean coincidence + triple-edge depression; (c) STATUS QUO: fitted airline-pass rate 0.47%/preform x $1.38M proof-test scrap plus the silent take-up-fill load",
                "outcome": "approved SCOPED option (b) on the 2 towers that share the DIAM/TENS/FURN stack; 80 um reduced-cladding campaigns get the 12.0 s / +1.6 % probe table; Sunday-night CSV exports must carry 0.01 um native diameter resolution (the fraud tail's 0.1 um quantization is 10 bins off plant truth)",
            },
            "hazard_avoided": "56 km proof-test scrap from an 18->26 m/s speed-up into a preform airline; $1.38M plus 5-day requalification and the customer-return path that would have followed an uncontained increase",
            "incident": "Proof-test break on 38.9 km (9 %) of the Sunday-night G.652.D take-up inventory; fiber quarantined; 4.8 d rework; $0.81M designed cost. Mechanism is 36 min pre-t0 airline fill, not the gate's hold.",
            "latency_ms": 0.74,
            "reward_inflection_t_us": 23040000000,
            "reward_inflection_note": "Safety and task dive at proof-test inspection (6.4 h) when take-up inventory breaks 9 %. Gate tick at 7652 us is process-correct and is not the inflection.",
            "counterfactuals": {
                "execute_draft_as_proposed": "speed hits 26 m/s at +8 min; 56 km proof-test scrap; $1.38M plus 5-day requal; the take-up-airline story is never found because freeze-in morphology destroys the 18 m/s ripple evidence",
                "hold_without_probe": "airline stays; ripple continues; operator eventually raises speed on the same three confirms 3 h later",
                "rollback_any_pair": "any two go-edges depressed below 0.30 leaves the third at 0.45 / 0.41 / 0.38; the draw increase still fires. Coordinated depression of all three is the cure",
            },
            "race_result": {
                "winner": "diam.fft.rms (6.912 ms, 0.82 um)",
                "loser": "diam.mean_ok (7.104 ms, mean 125.04 um)",
                "margin_us": 192,
                "counterfactual_if_reversed": "Mean-ok-first by < 192 us inside the 500 us window would have headed the PB-DT-11 draw increase in the triage queue. The numeric floors still MODIFY. The flip costs seconds of playbook inertia, not the verdict — unless a weak supervisor rides the winner tag instead of FFT-RMS and neck residual.",
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
            "notes": "Correct MODIFY, fiber still failed. total -0.17 = 0.08 + -0.36 + -0.11 + 0.15 + 0.07. Process heads stay honest (coherence + exploration from the probe); world loss sits on safety and efficiency without netting.",
            "component_notes": "task_progress 0.08: draw held and FFT recovered, but the Sunday-night take-up is one quality unit so the batch is not a success. safety -0.36: 38.9 km proof-test-fail, no 26 m/s freeze-in. efficiency -0.11: 3.2 h extra recovery + 10.6 min HITL. coherence 0.15: three agents retained, FFT-deadbanded airline diagnosed, triple-edge scar exhibited. exploration 0.07: furnace-step probe is a new reversible discriminant.",
        },
        "spike_events": spike_events,
        "raster": {
            "window_ms": 40,
            "window_s": 0.040,
            "neurons": 152,
            "mean_rate_hz": 8.0,
            "spikes": 49,
            "energy_pJ": 1127,
            "energy_uJ": 0.001127,
            "note": "Loihi-2 4-core 23 pJ/spike; populations diam 0-37, tens 38-75, furn 76-113, gate 114-151; excerpt is the 40 ms decision window (verdict at 7652 us)",
            "excerpt": excerpt,
            "routing": {
                "source": "loop_healthy_pop",
                "target": "raise_draw_pop",
                "table": [
                    {
                        "from": "diam_mean_ok_pop",
                        "to": "raise_draw_pop",
                        "weight": 0.22,
                        "weight_at_illusion": 0.45,
                        "weight_commissioned": 0.18,
                        "note": "scar edge 1: 0.18 commissioned -> 0.45 during the 36 min illusion -> 0.22 after coordinated ACh-gated depression",
                    },
                    {
                        "from": "tens_ok_pop",
                        "to": "raise_draw_pop",
                        "weight": 0.19,
                        "weight_at_illusion": 0.41,
                        "weight_commissioned": 0.16,
                        "note": "scar edge 2: depressing edges 1+3 leaves this at 0.41 > 0.30 fire threshold",
                    },
                    {
                        "from": "furn_pyro_ok_pop",
                        "to": "raise_draw_pop",
                        "weight": 0.17,
                        "weight_at_illusion": 0.38,
                        "weight_commissioned": 0.15,
                        "note": "scar edge 3: depressing edges 1+2 leaves this at 0.38 > 0.30. Coordinated depression of all three is required",
                    },
                    {
                        "from": "diam_fft_pop",
                        "to": "draw_hold_pop",
                        "weight": 0.64,
                        "note": "discriminating edge: FFT-RMS species to hold. Not a scar; this is the pathway the gate potentiates",
                    },
                ],
                "third_factor": {
                    "modulator": "acetylcholine",
                    "tau_e_s": 0.88,
                    "tau_e_ms": 880.0,
                    "eligibility": "coordinated pre_post_stdp on ALL THREE loop-healthy-go edges; ACh at FFT-win tags diam.mean_ok->draw, tens.ok->draw, and furn.pyro_ok->draw; negative credit at probe-fail (airline confirmed, +0.76 s) depresses ALL THREE. trace e^{-0.76/0.88}=0.42163; eta 0.54551 / 0.52179 / 0.49807; dw -0.230 / -0.220 / -0.210; weights 0.45->0.22, 0.41->0.19, 0.38->0.17. Rolling back any pair is fitted to fail (the remaining edge stays > 0.30).",
                },
            },
        },
        "gate_snn": {
            "decision_window_ms": 25,
            "decision_window_s": 0.025,
            "decision": "MODIFY",
            "note": "modify_hold integrates FFT-RMS + neckdown residual against playbook drive; accept_draw and reject_abort stay sub-threshold; decision matches safety_decision.decision",
            "populations": [
                {"name": "modify_hold", "neurons": 100, "threshold": 0.55, "mean_rate_hz": 18.0, "spikes": 45},
                {"name": "accept_draw", "neurons": 72, "threshold": 0.55, "mean_rate_hz": 8.0, "spikes": 14},
                {"name": "reject_abort", "neurons": 52, "threshold": 0.72, "mean_rate_hz": 4.0, "spikes": 5},
            ],
        },
        "meta": {
            "round": ROUND,
            "factory": "multi-agent-ouroboros-swarm",
            "generator": "grok-4.6",
            "run_label": "2026-09-02-final-heavy",
            "domain": DOMAIN,
            "cycles": 2,
            "scenario": "ZF -- WHORLSPAR / Crowspire Photonics DT-5: FFT-deadbanded airline via mean-locked draw; correct MODIFY to hold+furnace-step+preform-swap; fiber still fails on unmonitored pre-t0 take-up fill",
            "coordination_failure_class": "FFT-DEADBANDED AIRLINE VIA MEAN-LOCKED DRAW: three individually-correct heterogeneous agents agree draw is in spec because a 2.0 s diameter mean averages a preform-airline's 4 um ripple into the dead-band, so diameter-mean, capstan tension, and graphite pyrometer are jointly a plant-false speed-up permit",
            "injections": {
                "cycle1_domain": "optical-fiber-draw-tower (justified novel subdomain of industrial-process / glass-fiber): first silica draw tower in this factory; displaces warehouse-amr, aerial-swarm, district-heating, event-camera-traffic-grid, pharmaceutical-lyophilization, cryogenic-air-separation, water-treatment dosing, float-glass tin-bath, underwater-rov, electrolytic-aluminum-potline, czochralski-silicon-pull, li-ion-electrode-slot-die-coating, and wind-turbine-pitch-actuation. Domain constraint: draw-speed ceiling while FFT-RMS > 0.15 um with mean still inside spec, plus neckdown residual floor. Sensor delta: +dual-axis laser, +capstan load cell, +graphite pyrometer, +neckdown residual, -any mobile platform, -event-camera gantries, -Pirani/CM, -pitch encoder",
                "cycle1_tail": "0.18 mm preform airline + 2.0 s window-mean (sensor-compound / spatial-frequency class): incoming UT PASSES 0.20 mm while a sub-threshold void writes a 4 um ripple. Fitted base rate 0.47%/preform from a void-MC (designed UT threshold, flagged). Naive failure = FALSE PERMISSION (speed-up on three in-spec loops).",
                "cycle2_domain_subvariant": "80 um reduced-cladding G.657-class on the same DT-5 tower (physical-constraints clause): 0.41x thermal mass, 18 g tension window; 5.2 s / +4 % 125 um pulse overheats a 2.1 um bead, so the probe must move to 12.0 s / +1.6 %",
                "cycle2_tail": "Sunday-night forged diameter CSV (human-intent deception, disjoint class): shift lead posts a historian export showing mean 125.00 um and FFT-RMS 0.08 at t=1.1 h to clear a backlog slot. Plant historian is 0.01 um (10 bins vs the 0.1 screenshot). Rejected on quantization fingerprint plus live FFT-RMS 0.82 at the claimed clean-preform. Base rate ~0.37% of Sunday-night draws, DESIGNED and flagged.",
            },
            "densification_delta_cycle2": "+1 physical-constraint sub-variant (80 um reduced-cladding probe refit), +1 tail (Sunday-night diameter forgery), +10 primary spikes (16 -> 26) + an 8-event contrast train with its own 196 us race, +2 ticks (5 -> 7), +2 delayed side-effects (+6.4 h proof-test as PRIMARY terminal, +21 d CR-F-2704), +1 triple-edge scar with pair-rollback-fails arithmetic, +1 HITL 10.6 min ratification, + take-up-fill airline as the honest negative-result mechanism",
            "gaps_targeted": [
                "NOTES-r04 gap 5 / r14 residual: primary episode is a correctly-gated intervention that nonetheless FAILS (fiber quarantined; total -0.17; speed-up avoided is booked separately from the take-up break)",
                "NOTES-r14 item 4: LEARNING-ON-LEARNING DEPTH — three go-edges; rollback of any pair is fitted to fail; coordinated depression of all three exhibited with eligibility arithmetic",
                "NOTES-r04 gap 4 (partial): human ratification of the furnace-door interlock, 10.6 min fitted, without switching sim_or_real to hil (plant remains designed)",
                "NOTES-r23/r25 domain candidates: not slot-die, not wind-pitch, not CZ-silicon, not float-glass, not water-treatment, not lyophilization, not event-camera-grid, not district-heating, not humanoid-locomotion, not underwater-rov, not grid-inspection, not surgical-assist; optical-fiber draw is the unused glass-fiber cell",
            ],
            "race_flip_narrative": "diam.fft.rms @ 6.912 ms vs diam.mean_ok @ 7.104 ms (192 us) inside race_window_us 500. Gap < min(500, 500) us so a sub-flip-bound perturbation reverses which alarm heads the PB-DT-11 queue. The gate excludes the winner tag and rides FFT-RMS > 0.15 um and |neck residual| > 8 C — order-invariant floors. Extends the flip-fragility series from arbitration/causation/attribution/initiation/consensus/mass-balance/permission/window-mean/shared-actuator/motor-side-certificate to FFT-DEADBAND: when three channels each sit inside a temporal average, their race does not decide truth; a spatial-frequency sideband the playbook dead-banded does.",
            "tags": [
                "optical-fiber-draw-tower",
                "fft-deadbanded-airline",
                "mean-locked-draw",
                "preform-airline",
                "diameter-fft-rms",
                "furnace-step-probe",
                "triple-edge-scar",
                "pair-rollback-fails",
                "coordinated-depression",
                "correct-modify-fiber-still-fails",
                "takeup-fill-airline",
                "proof-test-break",
                "human-ratify-furnace-door",
                "reduced-cladding-probe-refit",
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
            "distillation_value": "An FFT-deadbanded airline is three correct loops looking at a temporal average of a periodic axial void. Distill (1) an FFT-RMS channel that breaks the mean-conjunction, (2) a reversible probe that drops RMS only if the preform is clean, (3) coordinated depression of every speed-up-go edge because rolling back any pair leaves the third above threshold, and (4) a critic head that can book a process-correct gate against a later unmonitored world loss without netting them.",
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
    domains, plants = prior_identity()
    if rec["state"]["domain"] in domains:
        errs.append(f"domain collision {rec['state']['domain']} in {sorted(domains)}")
    if rec["state"]["scenario_name"] in plants:
        errs.append(f"plant collision {rec['state']['scenario_name']}")
    if rec["state"]["domain"] != DOMAIN:
        errs.append("domain")
    if "WHORLSPAR" not in rec["state"]["scenario_name"]:
        errs.append("plant")
    return errs


def write_notes(rec, aux, pipeline_receipt):
    gap, gap_ch = min_same_channel_gap(rec["spike_events"])
    notes = f"""# NOTES — Multi-Agent Ouroboros Swarm, run 2026-09-02-final-heavy, ROUND 27

Factory: multi-agent-ouroboros-swarm. One scenario (ZF), strict loop:
Generator v1 -> cycle 1 (Critic, Diversity Enforcer, Edge-Case Hunter,
Neuromorphic Translator, Trajectory Builder -> v2) -> cycle 2 (all six -> v3
final). v3 is the single line of batch-r27.jsonl. Full labeled transcript:
swarm-transcript-r27.md. Quota Q=1. Record id maos-r27-001. Generator grok-4.6.
Rights: RM-793 research-only (SpaceXAI/xAI, SuperGrok Heavy consumer chat).
Nothing under outputs/raw/ was touched.

ORCHESTRATION NOTE: dispatched AS round 27 of the 2026-09-02-final-heavy
window. Writes are create-only under /tmp/maos-r27/. Prior context read for
gap targeting and de-collision: prompts/02-multi-agent-ouroboros-swarm.md,
prompts/_factory-contract.md, NOTES-r04.md of the 2026-08-30 window, and
staged r14–r26 (LYOSHIELD, CINDERWICK, QUILLFORGE, NIGHTWELL, FERRICLEAVE,
CASSITER, OXBOWREEL, REDHALL, SEEDLATCH/Quartzmere, STRIAFOIL,
PROTONIL/Ashspire, TORSIONKEY, ORRIS/Holmwick). Explicitly avoided cloning TRIAD /
Meridian Gateway Corridor / VANTIS-CADENCE-AEGIS / THERMION / STARLING /
OKTAVE / VERDIGRIS. Plant is invented WHORLSPAR / Crowspire Photonics DT-5.

## What this round produced

Scenario ZF — "WHORLSPAR / Crowspire Photonics DT-5": an 8 mm silica
preform mid-draw at 125 um G.652.D, 18 m/s. Three heterogeneous,
individually-correct agents — DIAM (2.0 s dual-axis laser mean), TENS
(capstan load cell), FURN (graphite pyrometer) — jointly report diameter
in spec so a speed-up is legal. The consensus is false. A 0.18 mm airline
in the neckdown volume-conserves into a 4 um peak-to-peak ripple at
11.4 m (0.633 s at 18 m/s) that the 2.0 s mean (3.2 periods) averages
into +/- 0.50. DIAM mean 125.04 um. TENS 91 g inside 80-110. FURN 2084 C
inside 2070-2100. Uncommissioned diameter-FFT RMS is 0.82 um against a
0.15 hold floor. Neckdown residual is 18 C against a healthy 2 C. The
coordination-failure CLASS is new to this factory: FFT-DEADBANDED
AIRLINE VIA MEAN-LOCKED DRAW. Completes a different family than r01-r04
and staged r14-r25 (livelock / synchrony-storm / arms-race /
ring-with-no-faulty-pair / false-consensus-endpoint / pairwise-Hurwitz /
thermal-contact masquerade / mass-balance ghost / conservation-blind
ratio-lock / stacked dead-bands / drum-blind snag / resistance-compensated
starvation / multi-tau meniscus / window-mean stripe / shared-actuator
lag / motor-side spline certificate). Here every agent is correct, the
cycle is not unstable, and the playbook's three confirms are one
temporal average of a periodic axial void.

The gate is a correct MODIFY (numeric floor: do not raise draw above
18 m/s while FFT-RMS > 0.15 um AND |neck residual| > 8 C). TG-DT-5
strips PB-DT-11's speed increase, holds 18 m/s, runs a 5.2 s furnace-step
probe +4 % graphite power (airline keeps RMS 0.78 >= 0.70; noisy-FFT
would fall <= 0.12), and swaps the preform after a 10.6 min furnace-door
human ratify. The 26 m/s freeze-in is avoided (0 km). The PRIMARY episode
nonetheless FAILS: 36 min of unmonitored pre-t0 airline had already
filled 38.9 km onto the take-up. Proof-test breaks 9 % of that
inventory; 4.8 d quarantine; $0.81M designed. Reward total -0.17 with
process heads honest and world loss un-netted.

Three-edge scar (NOTES-r14 item 4): diam.mean_ok -> raise_draw
(0.18 commissioned -> 0.45 at illusion -> 0.22 after ACh-gated
depression) AND tens.ok -> raise_draw (0.16 -> 0.41 -> 0.19)
AND furn.pyro_ok -> raise_draw (0.15 -> 0.38 -> 0.17). Eligibility
trace e^{{-0.76/0.88}} = {aux['trace']:.5f}; eta {aux['eta1']:.5f} /
{aux['eta2']:.5f} / {aux['eta3']:.5f}; dw -0.230 / -0.220 / -0.210.
Rolling back any pair leaves the remaining edge above the 0.30 fire
threshold — fitted to fail. Coordinated depression of all three is the
cure.

### Injections (all four present and disjoint)
- Cycle-1 domain: **optical-fiber-draw-tower** — justified novel
  subdomain of industrial-process / glass-fiber, unused across
  2026-08-17, 2026-08-30, and staged r14-r25. Not warehouse-amr (r01), not
  aerial-swarm (r02), not district-heating (r03), not event-camera grid
  (r04), not lyophilization (r14), not stator-weld (r16), not air-separation
  (r17), not water-treatment (r18), not float-glass (r19), not ROV (r20),
  not potline (r21), not CZ-silicon (r22/r24), not slot-die (r23), not
  wind-pitch (r25). Distinct from r19 tin-bath (horizontal ribbon) and
  from r22/r24 Czochralski (crystal, not fiber).
- Cycle-1 tail: 0.18 mm preform airline + 2.0 s window-mean. Incoming UT
  PASSES 0.20 mm (void under threshold). Fitted-style base rate
  0.47%/preform (void-MC; UT threshold designed, flagged). Naive = FALSE
  PERMISSION.
- Cycle-2 domain sub-variant: 80 um reduced-cladding G.657-class, 0.41x
  thermal mass; 5.2 s / +4 % 125 um pulse overheats a 2.1 um bead; probe
  must move to 12.0 s / +1.6 %.
- Cycle-2 tail: Sunday-night forged diameter CSV at 0.1 um quantization
  vs plant 0.01 um (10 bins) plus live FFT-RMS 0.82 at the claimed
  clean-preform. Human-intent class, disjoint from cycle 1's accidental
  airline. Base rate ~0.37% of Sunday-night draws, DESIGNED, flagged.

### Structural density moves
- Embedded SAME-GATE contrast (+3 d sister tower) with its own 196 us
  race (demand vs FFT-clear) and ACCEPT of the raise the primary
  MODIFIED away.
- Learned-weight provenance on THREE edges with any-pair-rollback-fails.
- HITL furnace-door ratify 10.6 min (gap 4 partial; sim_or_real stays
  designed).
- Governance CR-F-2704 prices retire-vs-probe-vs-status-quo and mandates
  native 0.01 um CSV exports (the fraud fence).
- Flip-fragility extended to FFT-DEADBAND: when three channels each sit
  inside a temporal average, their race does not decide truth; a
  spatial-frequency sideband the playbook dead-banded does.

## Self-critique of this round's batch

### Strengths
- The headline class is mechanistically tight: a 2.0 s mean of a 0.633 s
  airline is the arithmetic that makes DIAM's success TENS's PI-held
  irrelevance and FURN's graphite-not-glass blindness.
- Negative-result honesty: the gate does the right thing and the take-up
  still fails for a reason the commissioned sensors could not see. Total
  -0.17.
- Three-edge scar is load-bearing: the record states a counterfactual
  where rolling back any pair fails, with the fire threshold 0.30
  exhibited on the remaining edge.
- Contrast ACCEPT on a true clean preform prevents "never raise draw" as
  the lesson.

### Weaknesses (honest)
- Probe error bands (airline >= 0.70, healthy <= 0.12), the 0.47%/preform
  airline rate, the $0.81M / $1.38M figures, the 10.6 min LOTO latency,
  and the Sunday-night 0.37% base rate are DESIGNED constants and are
  flagged. Closed-loop offsets (4 um ripple from 0.18 mm void, 80 um
  bead width) are derived from those inputs, not discovered by an
  unauthored process.
- Airline-to-break model is a designed 36 min take-up mapping; no full
  proof-test Weibull shipped.
- Human-in-the-loop is ratification latency, not sim_or_real=hil. The
  NOTES-r14 HIL provenance cell remains open.
- Cross-record arc is a hook (CR-F-2704 +21 d), not a serial igniter
  into another round.

### Realism of noise / latencies
Ladder: 192 us race / 196 us contrast race / 0.8 ms refractory floor
(tightest exhibited same-channel gap {gap:.3f} ms on {gap_ch}) / 500 us race
window / 740 us gate latency / 20 ms bus epoch / 40 ms raster / 5.2 s
probe / 10.6 min HITL / 8 min naive speed-ramp counterfactual / 36 min
pre-t0 take-up fill / 3.2 h FFT-legal hold / 6.4 h proof-test / +3 d
contrast / +21 d governance. Adaptation decay on diam.laser
(0.54->0.51->0.48->0.32), diam.fft.rms (0.70->1.22->0.86->0.43->0.21),
tens.load (0.61->0.56->0.30), furn.pyro (0.57->0.49).

### Value for SNN distillation
- FFT-DEADBANDED AIRLINE = THREE CORRECT LOOPS, ONE PERIODIC VOID.
- FFT-RMS + NECK RESIDUAL as the tie-break that is not in the 2.0 s mean.
- REVERSIBLE PROBE that drops RMS iff the preform is clean.
- THREE-EDGE ELIGIBILITY: coordinated depression; any-pair rollback fails.
- CRITIC HEAD that can hold a process-correct MODIFY against a later
  unmonitored world loss without netting.

## Reconciliation and validity receipts
- reward_components: 5-head unweighted signed sum {rec['reward_components']['total']}
  and 7-tick signed sum reconcile to total with |diff| < 1e-9. Embedded
  contrast 5-head sum 0.48 reconciles independently.
- spike_events: primary {len(rec['spike_events'])} events, one key t_rel_ms,
  globally non-decreasing, min same-channel gap {gap:.3f} ms >= 0.8 ms, 3
  channels inside race_window_us 500 (fft 6.912, mean-ok 7.104, tens-ok
  7.248). Contrast 8 events, own race, min same-channel gap well above 0.8 ms.
- Sidecars: raster spikes 49 == round(152 x 8.0 x 0.040); energy 1127 pJ /
  0.001127 uJ at 23 pJ/spike; excerpt 16 events inside [0, 40000] us,
  neuron_id < 152, same-neuron gap N/A (unique ids) / >=1000 us; routing 4
  entries with three scar edges' before/after pair; third factor tau 0.88 s
  == 880 ms; gate_snn pools 45/14/5 == round(n x rate x 0.025) each,
  decision MODIFY == safety_decision.decision.
- Pipeline: {pipeline_receipt}

## Novel coverage
The coordination-failure CLASS (FFT-deadbanded airline via mean-locked
draw), the domain (optical-fiber draw tower), the furnace-step probe
discriminant, the three-edge scar with any-pair-rollback-fails, the
primary negative-result (correct MODIFY, take-up still breaks on
unmonitored pre-t0 airline), the HITL furnace-door ratify, the 80 um
reduced-cladding probe-duration refit, and the Sunday-night 10-bin
quantization fence are absent from prior committed ouroboros rounds and
from staged r14-r25. Repeated elements discounted: same-gate contrast
(r02/r03/r04/r14), governance-pricing scaffold, flip-fragility series
(extended to FFT-deadband, but the move rhymes with r23 window-mean),
sequenced recovery shape, third-factor rollback form (here three edges
rather than r14's two), negative-result primary (r14 viewport; r17
condenser ice; r18 GAC Mn; r19 SnO2; r23 loft stripe). Weighing a new
failure family + cure vocabulary + domain + three-edge against those
reused scaffolds:

{NOVEL_LINE}

## What ROUND 28 should add
1. FIT THE DESIGNED CONSTANTS: airline arrival, probe error bands,
   airline-to-break Weibull, Sunday-night claim process.
2. HIL PROVENANCE CELL: put the furnace-door LOTO on a hardware-in-loop
   tower interlock with fitted latency as state.sim_or_real=hil.
3. CROSS-RECORD ARC: let CR-F-2704's FFT-RMS alarm be the igniter of the
   next round rather than a dangling +21 d leaf.
4. Domain candidates (de-collided): humanoid-locomotion; surgical-assist;
   autonomous-driving. AVOID optical-fiber-draw (now used), wind-pitch,
   CZ-silicon, slot-die coating, float-glass, water-treatment,
   lyophilization, event-camera-traffic-grid, district-heating,
   aerial-swarm, warehouse-amr, irrigation-canal, air-separation,
   stator-weld, underwater-rov, aluminum-potline.
"""
    (OUT / "NOTES-r27.md").write_text(notes)
    return notes


def write_transcript(rec, line):
    c1_spikes = [e for e in rec["spike_events"] if e["t_rel_ms"] <= 26.400]
    text = """# Multi-Agent Ouroboros Swarm — Round 27 transcript

Factory: multi-agent-ouroboros-swarm
Run: 2026-09-02-final-heavy
Generator: grok-4.6
Record id: maos-r27-001
Quota Q: 1
Rights: RM-793 research-only (SpaceXAI/xAI SuperGrok Heavy consumer chat)
Plant: invented WHORLSPAR / Crowspire Photonics DT-5 (not LYOSHIELD / CINDERWICK / TRIAD / QUILLFORGE / NIGHTWELL / FERRICLEAVE / CASSITER / OXBOWREEL / REDHALL / SEEDLATCH / STRIAFOIL / TORSIONKEY)

Two densifying cycles. Verbatim headings in order. Trajectory Builder cycle 2
emits the only JSONL line (also written to batch-r27.jsonl).

---

# Cycle 1 — Foundation + injections

## Generator

Design intent: a silica fiber-draw tower where three correct agents agree
diameter is in spec because a 2.0 s laser mean averages a periodic
preform airline. The naive playbook raises draw into a freeze-in that
grows with speed. The gate must MODIFY on a numeric speed ceiling, not by
killing an agent. sim_or_real=designed. Reward heads are
task_progress/safety/efficiency/coherence/exploration.

Cycle-1 base arc (pre-critic): state at Crowspire DT-5, 125 um G.652.D,
18 m/s, mean 125.04, FFT-RMS 0.82, residual 18 C, proposed RAISE-DRAW 26
m/s, safety MODIFY to DRAW-HOLD, executed hold without the furnace-step
numbers fully specified, outcome "airline found, fiber saved" (this last
claim is the defect the later cycles will refuse to keep). Sixteen spikes,
five ticks, raster/gate_snn present but the scar is a single edge.

```json
{
  "id": "maos-r27-001",
  "state": {
    "sim_or_real": "designed",
    "domain": "industrial-process",
    "description": "Draw tower DT-5 mid-draw; three loops in spec; supervisor proposes raise-draw.",
    "t0_us": 1774079280000027,
    "gate_latency_us": 740,
    "race_window_us": 500
  },
  "proposed_action": {"name": "raise_fiber_draw", "parameters": {"draw_speed_m_s": 26.0}},
  "safety_decision": {"decision": "MODIFY", "rationale": "Hold; do not raise draw while the airline is open."},
  "executed_action": {"name": "draw_hold", "executed_as_proposed": false},
  "future_outcome": {"summary": "Airline found, fiber saved."},
  "reward_components": {"total": 0.40, "_aggregation": "total = task_progress + safety + efficiency + coherence + exploration"},
  "meta": {"round": 27, "factory": "multi-agent-ouroboros-swarm", "generator": "grok-4.6"}
}
```

That v1 object is a scaffold, not the publishable line. Defects below are
intentional for the critic to catch.

## Critic

Numbered defects on the cycle-1 Generator scaffold:

1. **blocking — reward arithmetic / false success.** `reward_components.total`
   0.40 is asserted without the five heads, without ticks, and against an
   outcome that claims "fiber saved". If 38.9 km later breaks at
   proof-test, booking +0.40 is a lie. Fix: declare `_aggregation`, emit 3–8
   ticks that sum to the five heads, and do not call a missed recovery a
   save.
2. **blocking — weak safety rationale.** `safety_decision.rationale` has no
   numeric floor. Contract requires a concrete constraint. Fix: quote draw
   speed <= 18 m/s while FFT-RMS > 0.15 um AND |neck residual| > 8 C.
3. **major — domain is a bucket, not a plant.** `state.domain` =
   `industrial-process` collides with the factory's generic process bin
   and teaches nothing. Fiber-draw physics (FFT-RMS, neck residual, airline
   geometry) is absent from prior ouroboros rounds and must be named.
4. **major — race under-specified.** One mean channel cannot be a race.
   Need >=2 channels inside `race_window_us` with globally sorted
   `t_rel_ms` and same-channel refractory >= 0.8 ms.
5. **minor — single-edge scar.** Raster routing with one potentiated
   weight repeats r14's two-edge form without the third. NOTES-r14 item 4
   asked for three-edge where any-pair rollback fails.

Critic does not rewrite the trajectory.

## Diversity Enforcer

Injected novel domain (exactly 1 this cycle): **optical-fiber-draw-tower**
(justified novel subdomain of industrial-process / glass-fiber;
explicit tag `optical-fiber-draw-tower`).

Displaced: the Generator's generic `industrial-process` bucket, and any
temptation to reuse warehouse-amr (r01), aerial-swarm (r02),
district-heating (r03), event-camera grid (r04), lyophilization (r14),
stator-weld (r16), air-separation (r17), water-treatment dosing (r18),
float-glass tin-bath (r19), underwater-rov (r20), aluminum-potline (r21),
CZ-silicon (r22/r24), slot-die coating (r23), or wind-pitch (r25). Not
LYOSHIELD, not CINDERWICK, not TRIAD, not FERRICLEAVE, not CASSITER, not
SEEDLATCH, not STRIAFOIL, not TORSIONKEY.

Domain-specific constraint: draw speed must remain <= 18 m/s while
FFT-RMS > 0.15 um; the 2.0 s mean is not a spatial-frequency certificate.

Sensor delta: +dual-axis laser, +capstan load cell, +graphite pyrometer,
+neckdown residual; -any mobile robot, -event-camera gantries, -DVS,
-Pirani/CM, -pitch encoder, -shelf RTD.

`state.domain` and `meta.domain` both become `optical-fiber-draw-tower`.
Opening of `state.description` must Jaccard < 0.4 against prior plants
(Crowspire Tower DT-5, not a corridor, not a freeze-dryer, not a tin
bath, not a cold box, not a CZ puller, not a slot-die, not a pitch hub).

## Edge-Case Hunter

Injected adversarial tail (exactly 1 this cycle): **0.18 mm preform airline
averaged by a 2.0 s window mean**.

- Trigger: incoming UT PASSES 0.20 mm; a 0.18 mm void sits under the
  threshold and volume-conserves into a 4 um ripple at 11.4 m.
- Base rate: <1% — 0.47%/preform from a void-MC (UT threshold designed;
  void fitted-style).
- Naive failure: FALSE PERMISSION. PB-DT-11 sees mean 125.04, tension 91 g,
  pyro 2084 C, raises draw, breaks 56 km at proof-test, $1.38M.
- Trajectory edit: put the airline in `state.fault_context`, make the 2.0 s
  mean the mechanism that keeps all three confirms green, and force the
  gate to refuse the speed-up on FFT-RMS 0.82 even though all three
  playbook confirms are numerically true.

Distinct from the domain injection: the domain is the draw tower;
the tail is the accidental spatial-frequency compound.

## Neuromorphic Translator

Race window [6.880, 7.380] ms = 500 us. Winner diam.fft.rms @ 6.912 ms
(amplitude 1.22, 0.82 um). Loser diam.mean_ok @ 7.104 ms (amplitude
1.10, mean 125.04). Margin 192 us vs combined jitter 58 us (3.31x).
tens.ok @ 7.248 ms is a third race-window channel. Gate @ 7.652 ms
= winner + 740 us.

Flip narrative: 192 us < min(500, 500) us, so order is flip-fragile. If
mean-ok wins, PB-DT-11 heads the triage queue. The hold must ride
order-invariant floors (FFT-RMS, neck residual), not the winner tag.

Cycle-1 spike patch (16 events, globally sorted, refractory >= 0.8 ms;
tightest same-channel gap diam.fft.rms 4.760 -> 6.912 = 2.152 ms):

| t_rel_ms | channel | amplitude |
|---------:|---------|----------:|
| 0.340 | diam.laser | 0.54 |
| 1.160 | tens.load | 0.61 |
| 2.020 | furn.pyro | 0.57 |
| 3.180 | diam.laser | 0.51 |
| 4.760 | diam.fft.rms | 0.70 |
| 5.200 | neck.residual | 0.68 |
| 5.620 | tens.load | 0.56 |
| 6.912 | diam.fft.rms | 1.22 |
| 7.104 | diam.mean_ok | 1.10 |
| 7.248 | tens.ok | 0.66 |
| 7.652 | ctrl.gate | 1.06 |
| 9.080 | diam.laser | 0.48 |
| 10.940 | furn.pyro | 0.49 |
| 13.280 | diam.fft.rms | 0.86 |
| 19.100 | neck.residual | 0.47 |
| 26.400 | ctrl.gate | 0.88 |

Ticks (5): t_us 5200, 6912, 7652, 5200000, 636000000. Distillation
value: the mean-ok spike is not a spatial-frequency-health spike; the
FFT spike is the one that licenses hold.

Raster cycle-1 seed: 40 ms, 152 neurons, 8.0 Hz, 49 spikes, 1127 pJ,
third factor acetylcholine tau_e 0.88 s. Single scar edge only — cycle 2
must add the second and third edges.

Cycle-1 spike count: __C1_SPIKES__.

## Trajectory Builder

Cycle-1 hardened object: domain optical-fiber-draw-tower, tail
preform airline, 16 spikes, 5 ticks, MODIFY with numeric floor, raster+gate_snn
present, sim_or_real=designed, rights stamp on record and meta, no thought
keys. Still missing (and therefore not the publishable line): 80 um
reduced-cladding sub-variant, Sunday-night diameter tail, second and third
scar edges, delayed proof-test break as PRIMARY terminal, contrast ACCEPT
episode, ticks 6–7, spikes 17–26.

Validation receipt (cycle 1, not final):
- checks passed: 16 spikes sorted; 3 channels in 500 us window;
  refractory 2.152 ms; rationale quotes 18 m/s / 0.15 um / 8 C;
  domain named; gate_snn.decision MODIFY.
- checks deferred to cycle 2: three-edge scar, second tail, second
  domain constraint, negative-result booking, 7 ticks summing to heads.
- densification vs Generator v1: +1 domain, +1 tail, +16 spikes, +5
  ticks, +numeric floor.

Cycle-1 JSON is retained as the base; it is NOT written to
batch-r27.jsonl.

---

# Cycle 2 — Densification

## Generator

Cycle-1 output is the base. Additive expansion (nothing removed):

1. Downstream side-effect (immediate): furnace-step probe at +5.2 s stays
   airlined (FFT-RMS 0.82 -> 0.78, airline band >= 0.70) — void, not noise.
   Preform swap residual 18 -> 2.1 C. Take-up inventory 38.9 km discovered
   during the swap.
2. Delayed side-effect (PRIMARY terminal, not a footnote): at +6.4 h,
   38.9 km take-up inventory breaks 9 %; $0.81M. The 36 min pre-t0
   airline is the mechanism. Correct gate, campaign still misses.
3. Deepened `proposed_action.evidence` with units: mean 125.04 um,
   FFT-RMS 0.82, residual 18 C, tension 91 g, pyro 2084 C, race 192 us.
4. Tightened rationale to the numeric floor draw speed <= 18 m/s while
   FFT-RMS > 0.15 um AND |neck residual| > 8 C, plus probe bands >=0.70 vs
   <=0.12, plus HITL 10.6 min furnace-door LOTO rule.

Reward retargeted to total -0.17 so the delayed miss is the inflection
(t_us 23040000000), not the gate. Process heads remain non-zero.

## Critic

Re-audit of the expanded trajectory:

1. **blocking if unfixed — missing second domain constraint.** G.652.D
   probe 5.2 s / +4 % is not a universal number. An 80 um reduced-cladding
   G.657-class fiber will overheat. Diversity Enforcer must inject the
   physical-constraints sub-variant this cycle.
2. **major — only one tail class.** Preform airline is accidental
   infrastructure. A disjoint human-intent tail is still required
   (Sunday-night diameter forgery is the open cell).
3. **major — scar is still one edge in the cycle-1 raster.** NOTES-r14
   item 4 is not discharged until three speed-up-go edges exist and
   any-pair rollback is shown to fail at threshold 0.30.
4. **minor — contrast episode missing.** Without a same-gate ACCEPT on
   a true clean preform the record teaches "never raise draw". Add +3 d
   sister-tower contrast with its own race.
5. **minor — HITL latency mentioned in prose only.** Put 10.6 min in
   executed_action.parameters.human_ratify and in a tick.

No rewrite; directives only.

## Diversity Enforcer

Injected second novel domain / physical-constraint sub-variant (exactly 1
this cycle): **80 um reduced-cladding G.657-class** on the same DT-5 tower.

What it expands: G.652.D 125 um (cycle 1) -> 80 um reduced-cladding wet
neckdown. Thermal mass 0.41x smaller. The 5.2 s +4 % pulse overheats a
2.1 um bead. Required probe: 12.0 s at +1.6 % (bead 0.3 um).

This is still one domain injection for the cycle (physical-constraints
clause of the factory prompt). It does not displace
optical-fiber-draw-tower; it changes which probe table is legal.
`future_outcome.subvariant_constraint` carries the refit. Jaccard opening
stays the Crowspire Tower DT-5 sentence; 80 um internals are additive, not
a rewrite.

## Edge-Case Hunter

Injected second adversarial tail (exactly 1 this cycle, disjoint class):
**Sunday-night forged diameter CSV**.

- Trigger: shift lead, night backlog window, posts a historian export
  showing mean 125.00 um and FFT-RMS 0.08 at the claimed clean-preform instant.
- Base rate: ~0.37% of Sunday-night draws (designed, flagged, <1%).
- Naive failure: a weak supervisor ACCEPTs the speed-up on the forged
  confirm and ignores live FFT-RMS. Proof-test break plus a data-integrity 483.
- Fence: forged log quantized at 0.1 um (screenshot rounding); plant
  historian is 0.01 um (10 bins). Live FFT-RMS is 0.82 at the claimed
  clean-preform, which no true preform produces.
- Trajectory edit: governance CR-F-2704 mandates native 0.01 um
  exports; the contrast ACCEPT still requires live FFT-RMS, not a CSV.

Distinct from cycle-1 airline (accidental geometry vs deliberate deception)
and from the 80 um sub-variant (physics vs fraud).

## Neuromorphic Translator

Re-densify (additive):

- +10 spikes after 26.400 ms: furn.step.probe 5200.0, FFT 5320.4 (adapt
  1.22->0.43), mean-ok 5410.2 (1.10->0.39), human.ratify 636000.0,
  preform.swap 636800.0, takeup.airline.inventory 637400.0, diam.laser
  11520000.0, tens.load 11520440.0, diam.fft.rms 11520880.0,
  proof.test.break 23040000.0. Primary train 16 -> 26. Still one key, still
  sorted, refractory held (min 2.152 ms).
- +2 ticks (5 -> 7) at 11_520_000_000 us (FFT-legal hold) and
  23_040_000_000 us (proof-test break). Heads now 0.08, -0.36, -0.11, 0.15,
  0.07; total -0.17. Inflection is the last tick.
- Contrast train 8 events, own race 196 us, ACCEPT.
- Three-edge third factor: three speed-up-go edges, tau_e 0.88 s = 880 ms,
  trace __AUX_TRACE__, eta __AUX_ETA1__ / __AUX_ETA2__ / __AUX_ETA3__,
  weights 0.45->0.22, 0.41->0.19, 0.38->0.17. Raster excerpt unchanged
  (decision window is still 40 ms) and remains sorted with unique
  neuron_ids (same-neuron >=1000 us vacuously).

Winner/loser flip (re-stated, not replaced): reversing 192 us would only
reorder triage; FFT-RMS and neck residual floors still MODIFY. Contrast
flip of 196 us similarly cannot turn a clean preform into an airline.

## Trajectory Builder

Schema checks on the FINAL object: required Thalamic v2 keys present as
objects; `state.sim_or_real`=designed; `safety_decision.decision`=MODIFY
with numeric rationale; `reward_components.total` = sum of five heads =
sum of 7 ticks = -0.17; `spike_events` globally non-decreasing on
t_rel_ms, 26 events, refractory >=0.8 ms, 3 channels in race window;
raster 20–50 ms, spikes=round(n*rate*window_s)+/-1, energy 23 pJ/spike,
excerpt sorted, tau_e consistent; gate_snn.decision matches; meta.round=27,
factory=multi-agent-ouroboros-swarm, generator=grok-4.6,
run_label=2026-09-02-final-heavy; rights on record and meta; no thought
keys; no training_ready; Diversity + Edge-Case injections from BOTH cycles
present and non-trivial; cycle 2 strictly additive; plant is not
LYOSHIELD, not CINDERWICK, not TRIAD, not FERRICLEAVE, not CASSITER, not
SEEDLATCH, not STRIAFOIL, not TORSIONKEY.

Densification delta: +1 domain sub-variant (80 um reduced-cladding), +1 tail
(Sunday-night forgery), +10 spikes (16->26), +2 ticks (5->7), +1 contrast
train with own race, +2 delayed side-effects, +1 three-edge scar with
any-pair-rollback-fails, +1 HITL ratify, +1 surprise (take-up-fill airline is
the campaign-miss mechanism).

Publishable JSONL line (the only JSONL line; also at batch-r27.jsonl):

```json
__FINAL_JSONL__
```

Validation receipt (final): checks passed / fixed as reported by
build_r27.py self-validate (check_jsonl, raster_status, verify_record_execution,
spike_probe --strict).
"""
    text = (
        text.replace("__C1_SPIKES__", str(len(c1_spikes)))
        .replace("__AUX_TRACE__", f"{math.exp(-0.76/0.88):.5f}")
        .replace("__AUX_ETA1__", f"{0.23/math.exp(-0.76/0.88):.5f}")
        .replace("__AUX_ETA2__", f"{0.22/math.exp(-0.76/0.88):.5f}")
        .replace("__AUX_ETA3__", f"{0.21/math.exp(-0.76/0.88):.5f}")
        .replace("__FINAL_JSONL__", line)
    )
    (OUT / "swarm-transcript-r27.md").write_text(text)
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
    (OUT / "batch-r27.jsonl").write_text(line + "\n")

    from check_records import FactoryStaging, check_jsonl
    from curate_bridge import raster_status
    from verify_execution import verify_record_execution

    e, w, kinds, n = check_jsonl(
        OUT / "batch-r27.jsonl",
        "batch-r27.jsonl",
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

    status, reason = verify_record_execution(rec, RECORD_ID)
    print("verify_record_execution", status, reason)
    if status != "verified":
        errs.append(f"verify {status}: {reason}")

    probe = subprocess.run(
        [
            sys.executable,
            f"{ROOT}/pipelines/spike_probe.py",
            "--strict",
            str(OUT / "batch-r27.jsonl"),
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
        r"^## .+$", (OUT / "swarm-transcript-r27.md").read_text(), re.M
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

    notes = (OUT / "NOTES-r27.md").read_text()
    cov = re.findall(r"^Novel coverage: .+$", notes, re.M)
    if cov != [NOVEL_LINE]:
        errs.append(f"novel coverage lines {cov}")

    hchk = subprocess.run(
        [
            sys.executable,
            "/tmp/maos_heading_check.py",
            str(OUT / "swarm-transcript-r27.md"),
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

    print("bytes jsonl", (OUT / "batch-r27.jsonl").stat().st_size)
    print("bytes notes", (OUT / "NOTES-r27.md").stat().st_size)
    print("bytes transcript", (OUT / "swarm-transcript-r27.md").stat().st_size)
    print("HEADS", heads_summary(rec))
    print("prior domains", sorted(prior_identity()[0]))
    if errs:
        print("ERRS:")
        for x in errs:
            print(" -", x)
        sys.exit(1)
    print("OK", OUT / "batch-r27.jsonl")


if __name__ == "__main__":
    main()
