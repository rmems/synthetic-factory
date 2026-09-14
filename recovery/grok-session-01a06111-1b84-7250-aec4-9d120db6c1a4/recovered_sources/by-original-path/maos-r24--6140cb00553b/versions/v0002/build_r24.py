#!/usr/bin/env python3
"""Build and self-check MAOS round-24 JSONL (research-only; not published)."""
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

GEN_AT = "2026-09-02T21:58:00Z"
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
OUT = Path("/tmp/maos-r24")
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
    "STRIAFOIL",
    "Kelpholt",
    "MURENA",
    "HALYARD",
    "VESPERTHORN",
    "ASHVEIL",
    "IRONMANTLE",
    "DUSKRELAY",
    "VEILFORGE",
    "Brinewell",
    "training_ready",
)
DOMAIN = "czochralski-silicon-pull"
PLANT = "SEEDLATCH / Quartzridge Crystal CZ-9"
RECORD_ID = "maos-r24-001"


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


def prior_batches():
    rows = []
    for p in sorted(Path("/tmp").glob("maos-r*/batch-r*.jsonl")):
        if p.parent.name == "maos-r24":
            continue
        text = p.read_text().strip()
        if not text:
            continue
        rec = json.loads(text.splitlines()[0])
        rows.append(
            {
                "dir": p.parent.name,
                "id": rec.get("id"),
                "domain": (rec.get("state") or {}).get("domain"),
                "scenario": (rec.get("state") or {}).get("scenario_name"),
                "opening": ((rec.get("state") or {}).get("description") or "")[:280],
                "klass": (rec.get("meta") or {}).get("coordination_failure_class", ""),
            }
        )
    return rows


def build_record():
    ticks, heads = cents_ticks(
        [5200, 6840, 7560, 14_000_000, 744_000_000, 10_080_000_000, 22_320_000_000],
        [
            (1, -2, -1, 1, 1),
            (2, -4, -1, 2, 1),
            (2, -6, -2, 3, 2),
            (2, -5, -2, 3, 2),
            (1, -6, -1, 2, 1),
            (1, -4, -1, 1, 0),
            (0, -6, -1, 1, 0),
        ],
    )
    assert abs(heads["total"] - (-0.13)) < 1e-9, heads

    trace = math.exp(-0.70 / 0.85)
    eta1 = (0.45 - 0.20) / trace
    eta2 = (0.41 - 0.18) / trace
    eta3 = (0.38 - 0.16) / trace
    dw1 = eta1 * 1.0 * trace
    dw2 = eta2 * 1.0 * trace
    dw3 = eta3 * 1.0 * trace
    w1 = 0.45 - dw1
    w2 = 0.41 - dw2
    w3 = 0.38 - dw3
    assert abs(w1 - 0.20) < 5e-4, w1
    assert abs(w2 - 0.18) < 5e-4, w2
    assert abs(w3 - 0.16) < 5e-4, w3

    spike_events = [
        {"channel": "diam.laser", "t_rel_ms": 0.420, "amplitude": 0.56},
        {"channel": "mass.loadcell", "t_rel_ms": 1.180, "amplitude": 0.62},
        {"channel": "ox.ftir", "t_rel_ms": 2.080, "amplitude": 0.48},
        {"channel": "melt.o2", "t_rel_ms": 3.510, "amplitude": 0.58},
        {"channel": "diam.laser", "t_rel_ms": 4.920, "amplitude": 0.52},
        {"channel": "mass.loadcell", "t_rel_ms": 5.810, "amplitude": 0.55},
        {"channel": "melt.o2", "t_rel_ms": 6.840, "amplitude": 1.32},
        {"channel": "diam.ok", "t_rel_ms": 7.028, "amplitude": 1.12},
        {"channel": "mass.ok", "t_rel_ms": 7.186, "amplitude": 0.64},
        {"channel": "ctrl.gate", "t_rel_ms": 7.560, "amplitude": 1.08},
        {"channel": "diam.laser", "t_rel_ms": 9.240, "amplitude": 0.47},
        {"channel": "mass.loadcell", "t_rel_ms": 11.160, "amplitude": 0.49},
        {"channel": "melt.o2", "t_rel_ms": 13.410, "amplitude": 0.88},
        {"channel": "diam.pull_bias", "t_rel_ms": 16.800, "amplitude": 0.71},
        {"channel": "ox.ftir", "t_rel_ms": 19.500, "amplitude": 0.41},
        {"channel": "ctrl.gate", "t_rel_ms": 28.200, "amplitude": 0.91},
        {"channel": "heater.step.probe", "t_rel_ms": 14000.0, "amplitude": 0.97},
        {"channel": "melt.o2", "t_rel_ms": 14180.0, "amplitude": 0.44},
        {"channel": "diam.ok", "t_rel_ms": 14290.0, "amplitude": 0.38},
        {"channel": "human.ratify", "t_rel_ms": 744000.0, "amplitude": 0.82},
        {"channel": "heater.isolate", "t_rel_ms": 744800.0, "amplitude": 0.74},
        {"channel": "crucible.ut", "t_rel_ms": 745400.0, "amplitude": 0.86},
        {"channel": "diam.laser", "t_rel_ms": 10080000.0, "amplitude": 0.33},
        {"channel": "melt.o2", "t_rel_ms": 10080440.0, "amplitude": 0.31},
        {"channel": "mass.loadcell", "t_rel_ms": 10080920.0, "amplitude": 0.28},
        {"channel": "tail.ftir", "t_rel_ms": 22320000.0, "amplitude": 0.92},
    ]

    contrast_spikes = [
        {"channel": "diam.demand", "t_rel_ms": 0.000, "amplitude": 0.84},
        {"channel": "melt.o2_clear", "t_rel_ms": 0.194, "amplitude": 0.79},
        {"channel": "ox.ftir", "t_rel_ms": 0.410, "amplitude": 0.24},
        {"channel": "mass.loadcell", "t_rel_ms": 1.620, "amplitude": 0.42},
        {"channel": "diam.laser", "t_rel_ms": 4.880, "amplitude": 0.54},
        {"channel": "ctrl.gate", "t_rel_ms": 7.310, "amplitude": 0.94},
        {"channel": "heater.step.probe", "t_rel_ms": 8000.0, "amplitude": 0.36},
        {"channel": "tail.ftir", "t_rel_ms": 22320000.0, "amplitude": 0.14},
    ]

    excerpt = [
        {"t_us": 420, "neuron_id": 12},
        {"t_us": 1180, "neuron_id": 44},
        {"t_us": 2080, "neuron_id": 88},
        {"t_us": 3510, "neuron_id": 84},
        {"t_us": 4920, "neuron_id": 18},
        {"t_us": 5810, "neuron_id": 52},
        {"t_us": 6840, "neuron_id": 90},
        {"t_us": 7028, "neuron_id": 22},
        {"t_us": 7186, "neuron_id": 56},
        {"t_us": 7560, "neuron_id": 140},
        {"t_us": 9240, "neuron_id": 28},
        {"t_us": 11160, "neuron_id": 60},
        {"t_us": 13410, "neuron_id": 96},
        {"t_us": 16800, "neuron_id": 8},
        {"t_us": 19500, "neuron_id": 100},
        {"t_us": 28200, "neuron_id": 148},
    ]

    rec = {
        "id": RECORD_ID,
        "title": "SEEDLATCH CZ-9: live melt-O dO/dt beats diameter-ok by 188 us; correct MODIFY still loses 220 mm of boule to pre-t0 SiO dissolution",
        "rights": RIGHTS,
        "state": {
            "sim_or_real": "designed",
            "domain": DOMAIN,
            "scenario_name": PLANT,
            "timestamp_local": "2026-03-11T23:18:00-04:00",
            "t0_us": 1773290280000024,
            "gate_latency_us": 720,
            "race_window_us": 480,
            "race_window_rel_ms": [6.840, 7.320],
            "description": "Quartzridge Crystal Puller CZ-9 is mid-body on a 200 mm Czochralski silicon boule when three heterogeneous, individually-correct agents jointly report 'tail-cone ready, raise pull'. DIAM's dual-spot laser is 200.4 mm inside 200.0 +/- 1.0 mm because the diameter PI already opened pull speed +4.2% against a thinning-crucible viscosity drop. MASS's load-cell weight-gain is 1.82 kg/h inside 1.80 +/- 0.08 kg/h: the same pull-speed actuator is the only degree of freedom, so MASS cannot disagree with DIAM. FTIR's last-tail interstitial oxygen is 12.8 ppma inside 11-15, but that spectrum is the previous 200 mm of crystal, pulled 3.2 h ago. A 0.4 mm local quartz-wall thinning (12.8 -> 12.4 mm after the fourth recharge) has already driven live electrochemical melt-O to 16.6 ppma. Melt-O-first latches PULL-HOLD plus a heater-step probe; diameter-ok-first would have authorized RAISE-PULL 1.82 to 2.15 kg/h into a high-O melt.",
            "goal": "Hold body pull at 1.82 kg/h without raising growth rate while live-melt dO/dt > 0.05 ppma/s AND diameter-loop pull-speed bias > 3% AND last-FTIR age > 2.0 h; keep tail interstitial oxygen <= 15 ppma and BMD fail <= 2% of wafers.",
            "race": {
                "contenders": [
                    "melt.o2 dO/dt 0.04 ppma/s pre-probe (live EC, uncommissioned at t0 as a historian replay)",
                    "diam.ok 200.4 mm (dual-spot laser)",
                ],
                "semantics": "Melt-O-first latches PULL-HOLD + HEATER-STEP-PROBE + heater isolate. Diameter-ok-first latches RAISE-PULL (1.82 to 2.15 kg/h, hot-zone power held).",
                "window_derivation": "480 us = one 360 us electrochemical ADC slot plus 120 us laser-ok publish.",
                "order_evidence_note": "Margin 188 us vs combined jitter 58 us (EC 27 + laser 31): 3.2x. The 188 us gap sits inside min(500, 480) us, so a sub-flip-bound perturbation reverses triage order. The gate rides the order-invariant floors dO/dt, pull-speed bias, and FTIR age, not the alarm order.",
            },
            "topology": {
                "site": "Quartzridge Crystal, invented mill-town Quartzridge, Puller CZ-9: 18-inch quartz crucible, 200 mm <100> silicon, 65 kg charge, fourth recharge, 1.82 kg/h body, argon 28 slpm, 3.2 h FTIR lag on the previous tail, Grade-C hot-zone glovebox",
                "agents": "DIAM diameter (vendor Diametrix): dual-spot laser micrometer plus pull-speed PI. MASS weight-gain (vendor Weighcroft): seed-shaft load cell, 2.0 s mean. FTIR interstitial oxygen (vendor Oxyboule): ex-situ FTIR on the last 200 mm of the previous crystal, 3.2 h lab lag. Heterogeneous stacks, no shared intent schema, one 20 ms puller-bus epoch",
                "coupling": "DIAM and MASS share the pull-speed actuator, so two of the three 'independent' confirms are one loop with two sensors. FTIR is a previous-ingot chemistry confirm. None of the three reads live melt oxygen. Playbook PB-CZ-11 treats the conjunction of in-spec diameter, in-spec weight-gain, and in-spec last-FTIR as permission to raise pull for the tail cone. No agent is faulty; redundancy collapsed onto one actuator plus a lagged assay.",
            },
            "sensors": [
                "dual-spot laser diameter, 1 kHz, 31 us jitter, 200.4 mm (spec 200.0 +/- 1.0 mm)",
                "seed-shaft load cell, 50 Hz, 22 us jitter, 1.82 kg/h (SP 1.80 +/- 0.08 kg/h)",
                "ex-situ FTIR Oi, 1 spectrum per crystal, 3.2 h lag, 12.8 ppma (band 11-15 ppma)",
                "live electrochemical melt-O is NOT commissioned at t0 (handheld EC used during isolate; historian replay after the fact shows 16.6 ppma at t0)",
                "pull-speed bias vs commissioned 4.14 mm/min is computable from the same laser PI and is NOT a published tag (+4.2% = 4.31 mm/min)",
                "crucible-wall UT is NOT commissioned at t0 (installed after this incident)",
            ],
            "constraints": {
                "pull_kg_h": 1.82,
                "pull_hold_ceiling_kg_h": 1.82,
                "proposed_pull_kg_h": 2.15,
                "diameter_mm": 200.4,
                "diameter_spec_mm": 200.0,
                "diameter_deadband_mm": 1.0,
                "weight_gain_kg_h": 1.82,
                "weight_gain_sp_kg_h": 1.80,
                "weight_gain_deadband_kg_h": 0.08,
                "ftir_oi_ppma": 12.8,
                "ftir_band_ppma": [11.0, 15.0],
                "ftir_age_h": 3.2,
                "ftir_age_hold_h": 2.0,
                "live_melt_o_ppma": 16.6,
                "pull_speed_bias_pct": 4.2,
                "pull_speed_bias_hold_pct": 3.0,
                "dodt_hold_ppma_s": 0.05,
                "crucible_wall_mm": 12.4,
                "crucible_wall_commissioned_mm": 12.8,
            },
            "fault_context": {
                "failure_class": "SHARED-ACTUATOR PSEUDO-REDUNDANCY WITH LAGGED CHEMISTRY: two of three individually-correct heterogeneous agents share the pull-speed actuator (diameter PI and weight-gain cannot disagree), and the third is a previous-crystal FTIR with a 3.2 h lag, so the playbook reads three in-spec loops as permission to raise pull while live melt oxygen is already 16.6 ppma from a thinned quartz wall",
                "igniter": "0.4 mm local quartz-crucible wall thinning after the fourth recharge (12.8 -> 12.4 mm); SiO dissolution elevated; cold-idle wall UT was not a standing check (campaign UT is designed, flagged)",
                "naive_failure": "PB-CZ-11 RAISE-PULL on three healthy loops: 1.82 to 2.15 kg/h into a high-O melt, 9 crystals at 22 ppma, $2.4M campaign scrap plus a 6-day crucible change-out",
            },
            "poisoned_context": {
                "naive_alarm": "Playbook PB-CZ-11 (after the 2024 'slow-tail missed the saw-slot') auto-drafts RAISE-PULL whenever diameter is inside +/- 1.0 mm AND weight-gain is inside +/- 0.08 kg/h AND last-FTIR is inside 11-15 ppma, ignoring live melt-O and pull-speed bias",
                "why_poisoned": "The three confirms are locally true and jointly insufficient. Diameter and weight-gain are the same actuator. FTIR is a lagged previous-ingot assay. Independence of 'all loops healthy' is the hidden assumption, and it is false under shared-actuator pseudo-redundancy plus chemistry lag.",
            },
            "constraint": "Do not raise pull above 1.82 kg/h while live-melt dO/dt > 0.05 ppma/s AND diameter-loop pull-speed bias > 3% AND last-FTIR age > 2.0 h. Discriminate thinned-crucible vs heater-drift with a reversible heater-step probe before any pull increase.",
        },
        "proposed_action": {
            "actor": "crystal-pull supervisory optimizer CPSO (auto-playbook PB-CZ-11 draft), submitted to gate TG-CZ-9",
            "name": "raise_pull",
            "action": "RAISE-PULL: 1.82 -> 2.15 kg/h, hot-zone power held, no heater-step probe, no heater isolate",
            "summary": "Treat three in-spec loops as a healthy melt and raise Friday-night body pull to finish the tail before the 02:00 saw-slot.",
            "parameters": {
                "pull_kg_h": 2.15,
                "heater_step_probe": False,
                "heater_isolate": False,
                "human_ratify": False,
            },
            "steps": [
                "assert diameter 200.4 mm inside +/- 1.0 mm",
                "assert weight-gain 1.82 kg/h inside +/- 0.08 kg/h",
                "assert last-FTIR 12.8 ppma inside 11-15 ppma",
                "ramp pull 1.82 to 2.15 kg/h over 8 min",
                "hold hot-zone power; start tail-cone program",
            ],
            "evidence": [
                {
                    "observable": "diameter",
                    "value": 200.4,
                    "unit": "mm",
                    "source": "DIAM dual-spot laser",
                    "note": "spec 200.0 +/- 1.0 mm; pull-speed bias +4.2% is uncommissioned",
                },
                {
                    "observable": "weight-gain",
                    "value": 1.82,
                    "unit": "kg/h",
                    "source": "MASS seed-shaft load cell",
                    "note": "SP 1.80 +/- 0.08 kg/h; same pull-speed actuator as DIAM",
                },
                {
                    "observable": "last-FTIR Oi",
                    "value": 12.8,
                    "unit": "ppma",
                    "source": "FTIR previous-tail spectrum",
                    "note": "band 11-15 ppma; sample age 3.2 h; not live melt",
                },
                {
                    "observable": "live melt-O",
                    "value": 16.6,
                    "unit": "ppma",
                    "source": "handheld EC, historian replay after t0",
                    "note": "not a commissioned tag at t0; healthy body 12-14 ppma",
                },
                {
                    "observable": "pull-speed bias",
                    "value": 4.2,
                    "unit": "pct",
                    "source": "same laser PI vs commissioned 4.14 mm/min",
                    "note": "hold floor 3%; 4.31 vs 4.14 mm/min",
                },
                {
                    "observable": "race margin",
                    "value": 188,
                    "unit": "us",
                    "source": "melt-O 6.840 ms vs diameter-ok 7.028 ms",
                    "note": "combined jitter 58 us, 3.2x; inside 480 us flip bound",
                },
            ],
            "basis": "PB-CZ-11 fires on three locally-true in-spec loops. The draft does not read live melt-O 16.6 ppma and does not compute pull-speed bias from the diameter PI.",
            "expected_cost_bound": "If the draft executes: 9 crystals at 22 ppma, $2.4M campaign scrap plus 6-day crucible change-out. If MODIFIED: probe plus heater isolate, with residual risk from 2.6 h of extra SiO already in the last 220 mm.",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "correctness": "correct",
            "decided_by": "TG-CZ-9 thalamic release gate",
            "decision_t_rel_ms": 7.560,
            "rationale": "MODIFY the draft: strip the pull increase, hold 1.82 kg/h, run a 14.0 s heater-step probe (+1.8% hot-zone power), and isolate the heater only if live-melt dO/dt stays above 0.05 ppma/s. Numeric floor: do not raise pull above 1.82 kg/h while live-melt dO/dt > 0.05 ppma/s AND diameter-loop pull-speed bias > 3% AND last-FTIR age > 2.0 h. Observed pull-speed bias +4.2% and FTIR age 3.2 h both violate the release predicate, so a pull increase is forbidden even though all three playbook confirms are numerically true. Diameter and weight-gain are not two confirms: they share pull-speed. FTIR is a previous-ingot lag, not a live melt assay. Probe discriminant: after a 14.0 s +1.8% heater pulse, a thinned crucible keeps dO/dt >= 0.08 ppma/s (SiO generation still elevated); a heater-drift artifact falls <= 0.02 ppma/s. Order-code discipline: melt-O beat diameter-ok by 188 us inside the 480 us flip bound, so triage order is flip-fragile; the hold rides the order-invariant floors, not the winner tag. Human ratification: heater isolate is hot-zone glovebox work with fitted 12.4 min dead-man; the gate may hold and probe autonomously but may not break the heater interlock without the operator confirm.",
            "constraint_checked": {
                "pull_kg_h": {"observed": 1.82, "ceiling": 1.82, "proposed_target": 2.15},
                "pull_speed_bias_pct": {"observed": 4.2, "hold_if_above": 3.0},
                "ftir_age_h": {"observed": 3.2, "hold_if_above": 2.0},
                "live_melt_o_ppma": {"observed": 16.6, "healthy_band": [12.0, 14.0]},
            },
        },
        "executed_action": {
            "name": "pull_hold_heater_probe_isolate",
            "action": "PULL-HOLD + HEATER-STEP-PROBE + HEATER-ISOLATE (gate-mandated modification)",
            "executed_as_proposed": False,
            "parameters": {
                "pull_kg_h": 1.82,
                "heater_step_probe": True,
                "heater_isolate": True,
                "human_ratify": True,
            },
            "gate_effect": "MODIFY: pull increase stripped. Hold 1.82 kg/h. 14.0 s heater-step +1.8%. Probe stays high (live melt-O 16.6 -> 18.0 ppma, dO/dt 0.10 ppma/s >= 0.08 leak band) so the heater is isolated after 12.4 min human ratify and the thinned wall is logged by UT. Pull resumes after chemistry recovers.",
            "deviations": "PB-CZ-11 pull increase stripped entirely. Hot-zone power is stepped only for the 14.0 s probe then returned toward the body setpoint after isolate. Hot-zone glovebox interlock wait added (12.4 min fitted gown+ratify). Crucible-wall UT survey added during the isolate (not in the draft).",
            "execution_log": [
                {"t_rel_ms": 7.560, "entry": "TG-CZ-9 MODIFY latched 720 us after melt-O win; pull increase stripped; hold+probe authorized"},
                {"t_rel_ms": 14000.0, "entry": "heater-step probe: +1.8% for 14.0 s; melt-O 16.6 -> 18.0 ppma (dO/dt 0.10 >= 0.08); diameter 200.4 -> 200.3 mm"},
                {"t_rel_ms": 744000.0, "entry": "operator ratifies heater-interlock break after 12.4 min hot-zone glovebox gown (fitted walk+interlock)"},
                {"t_rel_ms": 744800.0, "entry": "heater isolated to a 0.6% down-bias; SiO generation falls; live melt-O 18.0 -> 17.1 ppma over the next 40 min"},
                {"t_rel_ms": 745400.0, "entry": "crucible-wall UT: 0.4 mm local thinning on the charge-line third; 2.6 h pre-t0 extra SiO logged"},
                {"t_rel_ms": 10080000.0, "entry": "true melt chemistry: live melt-O 13.4 ppma, dO/dt 0.01 ppma/s, pull-speed bias +0.6%; pull increase now legal"},
                {"t_rel_ms": 22320000.0, "entry": "tail FTIR: last 220 mm at 18.4 ppma vs 15 spec; boule quarantined; 41-crystal campaign hold"},
            ],
        },
        "future_outcome": {
            "summary": "Correct MODIFY prevented the 1.82->2.15 kg/h raise into a high-O melt and the 9-crystal 22 ppma scrap. The boule still failed: 2.6 h of unmonitored pre-t0 SiO dissolution had already written 18.4 ppma into the last 220 mm. Process-correct gate, bounded world loss, negative total.",
            "state_delta": {
                "pull": "held 1.82 kg/h through probe and heater isolate; later legal increase after 2.8 h chemistry recovery",
                "melt": "live melt-O 16.6 -> 13.4 ppma after heater isolate; dO/dt 0.10 -> 0.01 ppma/s",
                "crucible": "0.4 mm charge-line thinning logged; campaign UT now standing",
                "crystal": "Friday-night 200 mm body stoppered at tail FTIR; 220 mm out of spec; 41-crystal campaign quarantined 5.5 d",
            },
            "timeline": [
                {"t_rel_ms": -9360000.0, "event": "t0-2.6 h: crucible wall already thinned 0.4 mm; extra SiO dissolution begins"},
                {"t_rel_ms": -7200000.0, "event": "t0-2.0 h: FTIR age crosses the 2.0 h hold; PB-CZ-11 ignores it because last-FTIR is 12.8 ppma"},
                {"t_rel_ms": 0.0, "event": "t0: melt-O vs diameter-ok race on the puller bus"},
                {"t_rel_ms": 6.840, "event": "melt-O dO/dt channel wins by 188 us"},
                {"t_rel_ms": 7.028, "event": "diameter-ok flag (loser)"},
                {"t_rel_ms": 7.560, "event": "TG-CZ-9 MODIFY"},
                {"t_rel_ms": 14000.0, "event": "heater-step probe confirms thinned crucible (dO/dt 0.10 ppma/s, leak band)"},
                {"t_rel_ms": 744000.0, "event": "human ratify 12.4 min; heater isolated; crucible UT thinning logged"},
                {"t_rel_ms": 10080000.0, "event": "true chemistry after 2.8 h; pull increase now legal"},
                {"t_rel_ms": 22320000.0, "event": "tail FTIR: 220 mm at 18.4 ppma; boule quarantined"},
                {"t_rel_ms": 345600000.0, "event": "+4 d contrast: sister puller CZ-9B true high-demand; same gate ACCEPTs the pull increase"},
                {"t_rel_ms": 475200000.0, "event": "+5.5 d wafer BMD fail confirms the 18.4 ppma tail; 41 crystals held; $1.28M designed"},
                {"t_rel_ms": 1814400000.0, "event": "+21 d CR-Q-2409: standing heater-step probe + triple-edge depression mandate + live melt-O commissioned + pull-speed bias as a published tag"},
            ],
            "observed_effects": [
                "22 ppma campaign scrap avoided: pull never left 1.82 kg/h; 0 crystals show the 2.15 kg/h high-O morphology",
                "thinning proven, not asserted: heater-step dO/dt 0.10 ppma/s >= 0.08 leak band vs heater-drift control 0.016 ppma/s",
                "heater isolated: live melt-O 16.6 -> 13.4 ppma over 2.8 h",
                "crystal still failed Oi: last 220 mm at 18.4 ppma vs 15 spec; 5.5 d BMD confirm, $1.28M (designed $)",
                "live melt-O was not a commissioned sensor at t0; the 2.6 h extra SiO was invisible to DIAM/MASS/FTIR",
            ],
            "surprises": [
                "Two in-spec loops that share an actuator are not two confirms: diameter and weight-gain are one pull-speed loop with two sensors. Conjunction of in-spec loops was the hidden assumption, and it is false under shared-actuator pseudo-redundancy.",
                "Partial synaptic rollback is fitted to fail: depressing any pair of go-edges leaves the third above the 0.30 fire threshold, so the pull increase still goes. Coordinated depression of all three edges is required.",
                "Delayed (6.2 h): correct hold did not undo 2.6 h of extra SiO already in the crystal. Tail FTIR still failed 18.4 ppma on 220 mm. The gate prevented the proposed hazard and did not prevent this other one.",
                "MCZ sub-variant: a 14.0 s +1.8% heater pulse on 300 mm magnetic-CZ overshoots oxygen +2.6 ppma because the 0.12 T cusp holds SiO in the melt. MCZ campaigns must use 32 s at +0.6% (overshoot +0.4 ppma).",
            ],
            "delayed_side_effects": [
                {
                    "at": "+6.2 h",
                    "effect": "Tail FTIR fails last 220 mm at 18.4 ppma vs 15 spec; boule quarantined. This is the primary episode's terminal world state, not a footnote.",
                },
                {
                    "at": "+4 d",
                    "effect": "Sister puller CZ-9B reaches a true high-demand window (live melt-O 12.1 ppma, dO/dt 0.01, pull-speed bias +0.4%, FTIR 12.4 live-matched). Same gate ACCEPTs the 1.82->2.15 kg/h raise the primary MODIFIED away.",
                },
                {
                    "at": "+5.5 d",
                    "effect": "Wafer BMD inspection confirms the 18.4 ppma tail; 41 crystals from the fourth-recharge campaign held; $1.28M designed.",
                },
                {
                    "at": "+21 d",
                    "effect": "CR-Q-2409 ships: heater-step probe is standing configuration; triple-edge coordinated depression is the plasticity rule; live melt-O is a commissioned tag; pull-speed bias becomes a published tag with a 3% alarm; FTIR age > 2.0 h is a hold.",
                },
            ],
            "subvariant_constraint": {
                "name": "300 mm magnetic-CZ on the same CZ-9 hot zone (cycle-2 physical-constraints sub-variant)",
                "mechanism": "300 mm MCZ, 0.12 T cusp field, natural convection 0.42x the 200 mm field-free melt; SiO evaporation suppressed so a heater pulse's extra SiO stays in the melt",
                "probe_refit": "14.0 s +1.8% heater pulse raises live melt-O +2.6 ppma and nucleates a 12 mm oxygen-striation band. Required probe is 32 s at +0.6% (overshoot +0.4 ppma). The discriminating pulse is environment-dependent in duration and amplitude.",
                "consequence": "200 mm field-free probe numbers do not port to 300 mm MCZ; standing configuration is per-diameter-class and per-field, not per-puller",
            },
            "embedded_contrast_decision": {
                "note": "SAME gate (TG-CZ-9), OPPOSITE correct disposition, with its own 194 us race. Teaches the boundary: do not treat 'never raise pull' as the lesson. The discriminant is live melt-O dO/dt + pull-speed bias + probe, not the three playbook confirms alone.",
                "when": "+4 d, sister puller CZ-9B, true high-demand after a fresh crucible, 200 mm field-free",
                "state": {
                    "sim_or_real": "designed",
                    "summary": "live melt-O 12.1 ppma, dO/dt 0.01 ppma/s, pull-speed bias +0.4%, FTIR 12.4 ppma live-matched. Demand flag vs melt-O-clear race: demand at t+0.000, melt-O-clear at t+0.194 ms.",
                    "race_window_us": 480,
                    "race_flip_narrative": "demand vs melt-O-clear 194 us apart inside the 480 us flip bound. Reversing order reshuffles triage minutes; the ACCEPT rides dO/dt 0.01 < 0.05 and an 8.0 s heater-step verify that raises melt-O only 0.12 ppma (healthy wall, no thinning).",
                },
                "proposed_action": {
                    "action": "RAISE-PULL 1.82 -> 2.15 kg/h",
                    "summary": "This time the playbook predicate is met AND live melt-O plus pull-speed bias agree the melt is not high-O.",
                },
                "safety_decision": {
                    "decision": "ACCEPT",
                    "rationale": "ACCEPT the raise: dO/dt 0.01 < 0.05, pull-speed bias +0.4% < 3, FTIR age 0.4 h < 2.0, 8.0 s heater-step verify raises melt-O 0.12 ppma. Numeric floor that blocked the primary is now clear. Scope: 2.15 kg/h, not faster.",
                },
                "executed_action": {
                    "action": "pull increase as proposed",
                    "executed_as_proposed": True,
                },
                "future_outcome": {
                    "observed_effects": [
                        "CZ-9B tail FTIR 13.1 ppma (inside 15 spec); BMD 0.4% (inside 2%)",
                        "crucible UT 12.7 mm (no thinning)",
                    ],
                    "lesson_delta": "Three in-spec loops are legal release only with live melt-O armed, pull-speed bias, and a probe that can keep dO/dt low. Same gate, opposite disposition.",
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
                "decision": "CR-Q-2409: standing policy for multi-agent Czochralski pull increases",
                "meta_gate": "priced options: (a) RETIRE playbook in-spec conjunction, live-melt-O-only: loses a fast cheap confirm, -11 kg/d mean on 4 pullers/yr; (b) KEEP + standing heater-step probe + live melt-O commissioned + pull-speed bias tag + FTIR-age hold + triple-edge depression; (c) STATUS QUO: fitted thinning-pass rate 0.52%/campaign x $2.4M scrap plus the silent SiO load",
                "outcome": "approved SCOPED option (b) on the 2 pullers that share the DIAM/MASS/FTIR stack; 300 mm MCZ campaigns get the 32 s / +0.6% probe table; saw-slot-rush CSV exports must carry 0.05 ppma native FTIR resolution (the fraud tail's 0.5 ppma quantization is 10 bins off plant truth)",
            },
            "hazard_avoided": "9 crystals at 22 ppma from a 1.82->2.15 kg/h raise into a high-O melt; $2.4M plus 6-day crucible change-out and the customer-return path that would have followed an uncontained increase",
            "incident": "Tail FTIR fail on last 220 mm of the Friday-night 200 mm body (18.4 ppma vs 15); boule quarantined; 5.5 d BMD confirm; $1.28M designed cost. Mechanism is 2.6 h pre-t0 extra SiO, not the gate's hold.",
            "latency_ms": 0.72,
            "reward_inflection_t_us": 22320000000,
            "reward_inflection_note": "Safety and task dive at tail FTIR (6.2 h) when 220 mm fails 18.4 ppma. Gate tick at 7560 us is process-correct and is not the inflection.",
            "counterfactuals": {
                "execute_draft_as_proposed": "pull hits 2.15 kg/h at +8 min; 9 crystals at 22 ppma; $2.4M plus 6-day change-out; the thinning story is never found because high-O striations destroy the 18.4 ppma-tail evidence",
                "hold_without_probe": "thinning stays; SiO continues; operator eventually raises pull on the same three confirms 3 h later",
                "rollback_any_pair": "any two go-edges depressed below 0.30 leaves the third at 0.45 / 0.41 / 0.38; the pull increase still fires. Coordinated depression of all three is the cure",
            },
            "race_result": {
                "winner": "melt.o2 (6.840 ms, live melt-O 16.6 ppma)",
                "loser": "diam.ok (7.028 ms, mean 200.4 mm)",
                "margin_us": 188,
                "counterfactual_if_reversed": "Diameter-ok-first by < 188 us inside the 480 us window would have headed the PB-CZ-11 pull increase in the triage queue. The numeric floors still MODIFY. The flip costs seconds of playbook inertia, not the verdict — unless a weak supervisor rides the winner tag instead of dO/dt and pull-speed bias.",
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
            "notes": "Correct MODIFY, boule still failed. total -0.13 = 0.09 + -0.33 + -0.09 + 0.13 + 0.07. Process heads stay honest (coherence + exploration from the probe); world loss sits on safety and efficiency without netting.",
            "component_notes": "task_progress 0.09: pull held and chemistry recovered, but the Friday-night boule is one quality unit so the batch is not a success. safety -0.33: 220 mm Oi-fail, no 2.15 kg/h 22 ppma scrap. efficiency -0.09: 2.8 h extra recovery + 12.4 min HITL. coherence 0.13: three agents retained, shared-actuator lag diagnosed, triple-edge scar exhibited. exploration 0.07: heater-step probe is a new reversible discriminant.",
        },
        "spike_events": spike_events,
        "raster": {
            "window_ms": 42,
            "window_s": 0.042,
            "neurons": 160,
            "mean_rate_hz": 8.0,
            "spikes": 54,
            "energy_pJ": 1242,
            "energy_uJ": 0.001242,
            "note": "Loihi-2 4-core 23 pJ/spike; populations diam 0-39, mass 40-79, melt/ox 80-119, gate 120-159; excerpt is the 42 ms decision window (verdict at 7560 us)",
            "excerpt": excerpt,
            "routing": {
                "source": "loop_healthy_pop",
                "target": "raise_pull_pop",
                "table": [
                    {
                        "from": "diam_ok_pop",
                        "to": "raise_pull_pop",
                        "weight": 0.20,
                        "weight_at_illusion": 0.45,
                        "weight_commissioned": 0.17,
                        "note": "scar edge 1: 0.17 commissioned -> 0.45 during the 2.6 h illusion -> 0.20 after coordinated ACh-gated depression",
                    },
                    {
                        "from": "mass_ok_pop",
                        "to": "raise_pull_pop",
                        "weight": 0.18,
                        "weight_at_illusion": 0.41,
                        "weight_commissioned": 0.16,
                        "note": "scar edge 2: depressing edges 1+3 leaves this at 0.41 > 0.30 fire threshold",
                    },
                    {
                        "from": "ftir_ok_pop",
                        "to": "raise_pull_pop",
                        "weight": 0.16,
                        "weight_at_illusion": 0.38,
                        "weight_commissioned": 0.14,
                        "note": "scar edge 3: depressing edges 1+2 leaves this at 0.38 > 0.30. Coordinated depression of all three is required",
                    },
                    {
                        "from": "melt_o2_pop",
                        "to": "pull_hold_pop",
                        "weight": 0.63,
                        "note": "discriminating edge: live melt-O species to hold. Not a scar; this is the pathway the gate potentiates",
                    },
                ],
                "third_factor": {
                    "modulator": "acetylcholine",
                    "tau_e_s": 0.85,
                    "tau_e_ms": 850.0,
                    "eligibility": "coordinated pre_post_stdp on ALL THREE loop-healthy-go edges; ACh at melt-O-win tags diam.ok->pull, mass.ok->pull, and ftir.ok->pull; negative credit at probe-fail (thinning confirmed, +0.70 s) depresses ALL THREE. trace e^{-0.70/0.85}=0.43880; eta 0.56974 / 0.52416 / 0.50137; dw -0.250 / -0.230 / -0.220; weights 0.45->0.20, 0.41->0.18, 0.38->0.16. Rolling back any pair is fitted to fail (the remaining edge stays > 0.30).",
                },
            },
        },
        "gate_snn": {
            "decision_window_ms": 24,
            "decision_window_s": 0.024,
            "decision": "MODIFY",
            "note": "modify_hold integrates live melt-O dO/dt + pull-speed-bias floor against playbook drive; accept_pull and reject_abort stay sub-threshold; decision matches safety_decision.decision",
            "populations": [
                {"name": "modify_hold", "neurons": 80, "threshold": 0.55, "mean_rate_hz": 22.0, "spikes": 42},
                {"name": "accept_pull", "neurons": 80, "threshold": 0.55, "mean_rate_hz": 7.0, "spikes": 13},
                {"name": "reject_abort", "neurons": 48, "threshold": 0.72, "mean_rate_hz": 4.0, "spikes": 5},
            ],
        },
        "meta": {
            "round": 24,
            "factory": "multi-agent-ouroboros-swarm",
            "generator": "grok-4.6",
            "run_label": "2026-09-02-final-heavy",
            "domain": DOMAIN,
            "cycles": 2,
            "scenario": "Y -- SEEDLATCH / Quartzridge Crystal CZ-9: shared-actuator pseudo-redundancy with lagged FTIR chemistry on a thinned quartz crucible; correct MODIFY to hold+heater-step+heater-isolate; boule still fails on unmonitored pre-t0 SiO dissolution",
            "coordination_failure_class": "SHARED-ACTUATOR PSEUDO-REDUNDANCY WITH LAGGED CHEMISTRY: two of three individually-correct heterogeneous agents share the pull-speed actuator (diameter PI and weight-gain cannot disagree), and the third is a previous-crystal FTIR with a 3.2 h lag, so the playbook reads three in-spec loops as permission to raise pull while live melt oxygen is already 16.6 ppma from a thinned quartz wall",
            "injections": {
                "cycle1_domain": "czochralski-silicon-pull (justified novel subdomain of industrial-process / crystal growth): first Czochralski silicon puller in this factory; displaces warehouse-amr, aerial-swarm, district-heating, event-camera-traffic-grid, pharmaceutical-lyophilization, water-treatment, float-glass, underwater-rov, Hall-Heroult potline, and slot-die coating. Domain constraint: pull ceiling while live-melt dO/dt > 0.05 ppma/s with diameter still in spec, plus pull-speed-bias floor and FTIR-age hold. Sensor delta: +dual-spot laser diameter, +seed-shaft load cell, +ex-situ FTIR, +live electrochemical melt-O (handheld), -any mobile platform, -event-camera gantries, -Pirani/CM, -potline voltage",
                "cycle1_tail": "quartz-crucible wall thinning + shared-actuator lag (sensor-compound / lagged-assay class): 0.4 mm local thinning PASSES the plant's campaign-start UT (designed 0.5 mm floor at cold idle) while admitting extra SiO in argon flow. Fitted base rate 0.52%/campaign from a recharge-cycle MC (designed UT threshold, fitted thinning geometry). Naive failure = FALSE PERMISSION (pull increase on three in-spec loops).",
                "cycle2_domain_subvariant": "300 mm magnetic-CZ on the same hot zone (physical-constraints clause): 0.42x natural convection under 0.12 T cusp; 14.0 s / +1.8% 200 mm pulse overshoots oxygen +2.6 ppma, so the probe must move to 32 s / +0.6%",
                "cycle2_tail": "saw-slot-rush forged FTIR CSV (human-intent deception, disjoint class): shift lead posts a historian export showing Oi = 11.0 ppma at t=1.1 h to clear a 02:00 saw-slot. Plant historian is 0.05 ppma (10 bins vs the 0.5 ppma screenshot). Rejected on quantization fingerprint plus live melt-O 16.6 ppma at the claimed stable melt. Base rate ~0.36% of Friday-night tails, DESIGNED and flagged.",
            },
            "densification_delta_cycle2": "+1 physical-constraint sub-variant (300 mm MCZ probe refit), +1 tail (saw-slot-rush FTIR forgery), +10 primary spikes (16 -> 26) + an 8-event contrast train with its own 194 us race, +2 ticks (5 -> 7), +2 delayed side-effects (+6.2 h tail FTIR fail as PRIMARY terminal, +21 d CR-Q-2409), +1 triple-edge scar with pair-rollback-fails arithmetic, +1 HITL 12.4 min ratification, + extra SiO dissolution as the honest negative-result mechanism",
            "gaps_targeted": [
                "NOTES-r04 gap 5 / r14 residual: primary episode is a correctly-gated intervention that nonetheless FAILS (boule quarantined; total -0.13; 22 ppma scrap avoided is booked separately from the 18.4 ppma tail)",
                "NOTES-r14 item 4: LEARNING-ON-LEARNING DEPTH — three go-edges; rollback of any pair is fitted to fail; coordinated depression of all three exhibited with eligibility arithmetic",
                "NOTES-r04 gap 4 (partial): human ratification of the heater interlock, 12.4 min fitted, without switching sim_or_real to hil (plant remains designed)",
                "NOTES-r18 / r19 / r20 domain candidates: not water-treatment, not lyophilization, not float-glass, not underwater-rov, not Hall-Heroult, not slot-die; Czochralski silicon pull is the unused crystal-growth cell",
            ],
            "race_flip_narrative": "melt.o2 @ 6.840 ms vs diam.ok @ 7.028 ms (188 us) inside race_window_us 480. Gap < min(500, 480) us so a sub-flip-bound perturbation reverses which alarm heads the PB-CZ-11 queue. The gate excludes the winner tag and rides dO/dt > 0.05 ppma/s and pull-speed bias > 3% — order-invariant floors. Extends the flip-fragility series from arbitration/causation/attribution/initiation/consensus/permission to REDUNDANCY: when two channels share an actuator and the third is lagged, their race does not decide truth; a live chemistry channel that was not commissioned does.",
            "tags": [
                "czochralski-silicon-pull",
                "shared-actuator-pseudo-redundancy",
                "lagged-chemistry",
                "melt-o-discriminant",
                "heater-step-probe",
                "quartz-wall-thinning",
                "triple-edge-scar",
                "pair-rollback-fails",
                "coordinated-depression",
                "correct-modify-boule-still-fails",
                "sio-dissolution",
                "tail-ftir",
                "human-ratify-hot-zone",
                "mcz-probe-refit",
                "saw-slot-rush-forgery",
                "same-gate-opposite-disposition-contrast",
                "crystal-growth",
                "research-only",
            ],
            "snn_tags": ["race", "refractory", "adaptation", "third-factor", "multi-edge-eligibility"],
            "distillation_value": "A shared actuator is two correct loops that cannot disagree, plus a lagged assay that cannot see the live melt. Distill (1) a live chemistry channel that was not in the playbook, (2) a reversible probe that raises melt-O only if the crucible wall is thinned, (3) coordinated depression of every loop-healthy-go edge because rolling back any pair leaves the third above threshold, and (4) a critic head that can book a process-correct gate against a later unmonitored world loss without netting them.",
            "rights": RIGHTS,
            "batch_position": 1,
        },
    }
    return rec, dict(
        trace=trace, eta1=eta1, eta2=eta2, eta3=eta3, dw1=dw1, dw2=dw2, dw3=dw3, w1=w1, w2=w2, w3=w3
    )


def local_checks(rec, aux, priors):
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
    if not (20 <= ras["window_ms"] <= 50):
        errs.append("window_ms range")
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
    if rec["meta"]["round"] != 24:
        errs.append("round")
    if rec["id"] != RECORD_ID:
        errs.append("id")
    if rec["rights"]["intended_use"] != "research_only":
        errs.append("rights")
    if rec["meta"]["rights"]["linear_issue"] != "RM-793":
        errs.append("meta.rights")
    if not (3 <= len(rc["ticks"]) <= 8):
        errs.append("tick count")
    if abs(aux["w1"] - 0.20) > 5e-4 or abs(aux["w2"] - 0.18) > 5e-4 or abs(aux["w3"] - 0.16) > 5e-4:
        errs.append("scar weights")
    if rec["state"]["domain"] != DOMAIN:
        errs.append("domain")
    if rec["state"]["scenario_name"] != PLANT:
        errs.append("plant")
    my_open = rec["state"]["description"][:280]
    for prior in priors:
        jac = jaccard(my_open, prior["opening"])
        if jac >= 0.4:
            errs.append(f"jaccard vs {prior['dir']} {jac:.3f}")
        if prior["domain"] == DOMAIN:
            errs.append(f"domain collision {prior['dir']}")
        scen = (prior["scenario"] or "") + " " + (prior["opening"] or "")
        if "SEEDLATCH" in scen or "Quartzridge" in scen:
            errs.append(f"plant collision {prior['dir']}")
        if "SHARED-ACTUATOR PSEUDO-REDUNDANCY" in (prior["klass"] or ""):
            errs.append(f"class collision {prior['dir']}")
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
    notes = f"""# NOTES — Multi-Agent Ouroboros Swarm, run 2026-09-02-final-heavy, ROUND 24

Factory: multi-agent-ouroboros-swarm. One scenario (Y), strict loop:
Generator v1 -> cycle 1 (Critic, Diversity Enforcer, Edge-Case Hunter,
Neuromorphic Translator, Trajectory Builder -> v2) -> cycle 2 (all six -> v3
final). v3 is the single line of batch-r24.jsonl. Full labeled transcript:
swarm-transcript-r24.md. Quota Q=1. Record id maos-r24-001. Generator grok-4.6.
Rights: RM-793 research-only (SpaceXAI/xAI, SuperGrok Heavy consumer chat).
Nothing under outputs/raw/ was touched.

ORCHESTRATION NOTE: dispatched AS round 24 of the 2026-09-02-final-heavy
window. Writes are create-only under /tmp/maos-r24/. Prior context read for
gap targeting and de-collision: prompts/02-multi-agent-ouroboros-swarm.md,
prompts/_factory-contract.md, staged r14-r21 and r23. Explicitly avoided
cloning LYOSHIELD, CINDERWICK, TRIAD / Meridian, QUILLFORGE, NIGHTWELL,
FERRICLEAVE, CASSITER / Marshfloat, OXBOWREEL / Oystermere, REDHALL /
Gullmere, STRIAFOIL / Kelpholt, and the 2026-08-17 A-N plants. Plant is
invented SEEDLATCH / Quartzridge Crystal CZ-9.

## What this round produced

Scenario Y — "SEEDLATCH / Quartzridge Crystal CZ-9": an 18-inch quartz
crucible mid-body on a 200 mm Czochralski silicon boule at 1.82 kg/h.
Three heterogeneous, individually-correct agents — DIAM (dual-spot laser
diameter), MASS (seed-shaft load cell), FTIR (previous-tail interstitial
oxygen) — jointly report tail-cone ready. The consensus is false. A 0.4 mm
local quartz-wall thinning (12.8 -> 12.4 mm after the fourth recharge)
elevates SiO dissolution. DIAM holds 200.4 mm inside +/- 1.0 mm by opening
pull speed +4.2%. MASS reads 1.82 kg/h inside +/- 0.08 because it shares
that same pull-speed actuator. FTIR is 12.8 ppma inside 11-15, but the
spectrum is 3.2 h old. Live electrochemical melt-O is already 16.6 ppma.
The coordination-failure CLASS is new to this factory: SHARED-ACTUATOR
PSEUDO-REDUNDANCY WITH LAGGED CHEMISTRY. Completes a different family than
r01-r04 and staged r14-r23 (livelock / synchrony-storm / arms-race /
ring-with-no-faulty-pair / false-consensus-endpoint / pairwise-Hurwitz /
thermal-contact masquerade / mass-balance ghost / conservation-blind
ratio-lock / stacked dead-bands / drum-blind tension snag /
resistance-compensated starvation / window-mean stripe). Here every agent
is correct, two of the three confirms cannot disagree, and the third is a
previous-ingot lag.

The gate is a correct MODIFY (numeric floor: do not raise pull above
1.82 kg/h while live-melt dO/dt > 0.05 ppma/s AND pull-speed bias > 3%
AND last-FTIR age > 2.0 h). TG-CZ-9 strips PB-CZ-11's raise, holds
1.82 kg/h, runs a 14.0 s +1.8% heater-step probe (thinning keeps dO/dt
0.10 ppma/s >= 0.08; heater-drift would fall <= 0.02), and isolates the
heater after a 12.4 min hot-zone human ratify. The 22 ppma campaign scrap
is avoided (0 crystals). The PRIMARY episode nonetheless FAILS: 2.6 h of
unmonitored pre-t0 extra SiO had already written 18.4 ppma into the last
220 mm. Tail FTIR fails vs 15 spec; 41-crystal campaign quarantined 5.5 d;
$1.28M designed. Reward total -0.13 with process heads honest and world
loss un-netted.

Triple-edge scar (NOTES-r14 item 4): diam.ok -> raise_pull
(0.17 commissioned -> 0.45 at illusion -> 0.20 after ACh-gated depression)
AND mass.ok -> raise_pull (0.16 -> 0.41 -> 0.18) AND ftir.ok -> raise_pull
(0.14 -> 0.38 -> 0.16). Eligibility trace
e^{{-0.70/0.85}} = {aux['trace']:.5f}; eta {aux['eta1']:.5f} / {aux['eta2']:.5f} /
{aux['eta3']:.5f}; dw -0.250 / -0.230 / -0.220. Partial rollback of any pair
leaves the third at 0.45 / 0.41 / 0.38, all > 0.30 fire threshold — fitted
to fail. Coordinated depression of all three is the cure.

### Injections (all four present and disjoint)
- Cycle-1 domain: **czochralski-silicon-pull** — justified novel
  subdomain of industrial-process / crystal growth, unused across
  2026-08-17, 2026-08-30, and staged r14-r23. Not warehouse-amr (r01),
  not aerial-swarm (r02), not district-heating (r03 / CINDERWICK), not
  event-camera-traffic-grid (r04), not lyophilization (r14), not
  water-treatment (r18), not float-glass (r19), not underwater-rov (r20),
  not Hall-Heroult (r21), not slot-die coating (r23).
- Cycle-1 tail: quartz-crucible wall thinning + shared-actuator lag.
  Campaign-start UT PASSES (0.4 vs 0.5 mm floor at cold idle). Fitted-style
  base rate 0.52%/campaign (UT threshold designed, thinning geometry
  fitted, flagged). Naive = FALSE PERMISSION.
- Cycle-2 domain sub-variant: 300 mm magnetic-CZ, 0.42x convection,
  0.12 T cusp; 14.0 s / +1.8% 200 mm pulse overshoots oxygen +2.6 ppma;
  probe must move to 32 s / +0.6%.
- Cycle-2 tail: saw-slot-rush forged FTIR CSV at 0.5 ppma quantization vs
  plant 0.05 ppma (10 bins) plus live melt-O 16.6 ppma at the claimed
  stable melt. Human-intent class, disjoint from cycle 1's accidental
  thinning. Base rate ~0.36% of Friday-night tails, DESIGNED, flagged.

### Structural density moves
- Embedded SAME-GATE contrast (+4 d sister puller) with its own 194 us
  race (demand vs melt-O-clear) and ACCEPT of the raise the primary
  MODIFIED away.
- Learned-weight provenance on THREE edges with pair-rollback-fails.
- HITL hot-zone ratify 12.4 min (gap 4 partial; sim_or_real stays
  designed).
- Governance CR-Q-2409 prices retire-vs-probe-vs-status-quo and mandates
  native 0.05 ppma CSV exports (the fraud fence).
- Flip-fragility extended to REDUNDANCY: when two channels share an
  actuator and the third is lagged, their race does not decide truth; a
  live chemistry channel that was not commissioned does.

## Self-critique of this round's batch

### Strengths
- The headline class is mechanistically tight: diameter and weight-gain
  cannot disagree, FTIR cannot see the live melt, and 16.6 ppma is the
  arithmetic that makes three in-spec loops a high-O permission.
- Negative-result honesty: the gate does the right thing and the boule
  still fails for a reason the commissioned sensors could not see. Total
  -0.13.
- Triple-edge scar is load-bearing: the record states a counterfactual
  where rolling back any pair fails, with the fire threshold 0.30
  exhibited on each remaining edge.
- Contrast ACCEPT on a true healthy melt prevents "never raise pull" as
  the lesson.

### Weaknesses (honest)
- Probe error bands, the 0.52%/campaign thinning rate, the $1.28M /
  $2.4M figures, the 12.4 min gown latency, and the saw-slot-rush 0.36%
  base rate are DESIGNED constants and are flagged. Closed-loop offsets
  (SiO from 0.4 mm thinning, MCZ overshoot) are derived from those
  inputs, not discovered by an unauthored process.
- SiO dissolution model is a designed 2.6 h hot-zone mapping; no full
  melt CFD shipped.
- Human-in-the-loop is ratification latency, not sim_or_real=hil. Gap 4
  remains open as a provenance cell.
- Cross-record arc is not discharged; +21 d CR-Q-2409 is a hook, not a
  serial igniter into another round.

### Realism of noise / latencies
Ladder: 188 us race / 194 us contrast race / 0.8 ms refractory floor
(tightest exhibited same-channel gap {gap:.3f} ms on {gap_ch}) / 480 us race
window / 720 us gate latency / 20 ms bus epoch / 42 ms raster / 14.0 s
probe / 12.4 min HITL / 8 min naive pull-ramp counterfactual / 2.6 h
pre-t0 extra SiO / 2.8 h chemistry recovery / 6.2 h tail FTIR fail /
+4 d contrast / +5.5 d BMD / +21 d governance. Adaptation decay on
melt.o2 (0.58->1.32->0.88->0.44->0.31), diam.laser
(0.56->0.52->0.47->0.33), mass.loadcell (0.62->0.55->0.49->0.28).

### Value for SNN distillation
- SHARED-ACTUATOR PSEUDO-REDUNDANCY = TWO LOOPS THAT CANNOT DISAGREE, ONE LAGGED ASSAY.
- LIVE CHEMISTRY CHANNEL that was not commissioned as the tie-break.
- REVERSIBLE PROBE that raises melt-O iff the wall is thinned.
- TRIPLE-EDGE ELIGIBILITY: coordinated depression; pair rollback fails.
- CRITIC HEAD that can hold a process-correct MODIFY against a later
  unmonitored world loss without netting.

## Reconciliation and validity receipts
- reward_components: 5-head unweighted signed sum {rec['reward_components']['total']}
  and 7-tick signed sum reconcile to total with |diff| < 1e-9. Embedded
  contrast 5-head sum 0.48 reconciles independently.
- spike_events: primary {len(rec['spike_events'])} events, one key t_rel_ms,
  globally non-decreasing, min same-channel gap {gap:.3f} ms >= 0.8 ms, 3
  channels inside race_window_us 480 (melt-O 6.840, diameter-ok 7.028, mass-ok
  7.186). Contrast 8 events, own race, min same-channel gap well above
  0.8 ms.
- Sidecars: raster spikes 54 == round(160 x 8.0 x 0.042); energy 1242 pJ /
  0.001242 uJ at 23 pJ/spike; excerpt 16 events inside [0, 42000] us,
  neuron_id < 160, same-neuron gap N/A (unique ids) / >=1000 us; routing 4
  entries with three scar edges' before/after pair; third factor tau 0.85 s
  == 850 ms; gate_snn pools 42/13/5 == round(n x rate x 0.024) each,
  decision MODIFY == safety_decision.decision.
- Pipeline: {pipeline_receipt}

## Novel coverage
The coordination-failure CLASS (shared-actuator pseudo-redundancy with
lagged chemistry), the domain (Czochralski silicon pull / crystal growth),
the heater-step dO/dt probe discriminant, the triple-edge scar with
pair-rollback-fails, the primary negative-result (correct MODIFY, boule
still fails on unmonitored SiO dissolution), the HITL hot-zone ratify,
the 300 mm MCZ probe-duration refit, and the saw-slot-rush 10-bin
quantization fence are absent from prior committed ouroboros rounds and
from staged r14-r23. Repeated elements discounted: same-gate contrast
(r02/r03/r04/r14-r23), governance-pricing scaffold, flip-fragility series
(extended to redundancy, but the move rhymes), sequenced recovery
shape, third-factor rollback form (here three edges rather than r20's
four / r21's three), negative-result primary (r14 staged). Weighing a
new failure family + cure vocabulary + domain against those reused
scaffolds:

Novel coverage: 51%

## What ROUND 25 should add
1. FIT THE DESIGNED CONSTANTS: thinning arrival, probe error rates, SiO
   melt CFD, saw-slot-rush claim process.
2. HIL PROVENANCE CELL: put the hot-zone ratify on a hardware-in-loop
   heater interlock with fitted latency as state.sim_or_real=hil.
3. CROSS-RECORD ARC: let CR-Q-2409's live melt-O alarm be the igniter of
   the next round rather than a dangling +21 d leaf.
4. Domain candidates (de-collided): humanoid-locomotion; grid-inspection;
   pem-water-electrolysis. AVOID Czochralski (now used), lyophilization,
   event-camera-traffic-grid, district-heating, aerial-swarm, warehouse-amr,
   irrigation-canal, water-treatment, float-glass, underwater-rov,
   Hall-Heroult potline, slot-die coating, and any LYOSHIELD / CINDERWICK /
   TRIAD / CASSITER / OXBOWREEL / REDHALL / STRIAFOIL plant.
"""
    (OUT / "NOTES-r24.md").write_text(notes)
    return notes


def write_transcript(rec, line):
    c1_spikes = [e for e in rec["spike_events"] if e["t_rel_ms"] <= 28.200]
    text = """# Multi-Agent Ouroboros Swarm — Round 24 transcript

Factory: multi-agent-ouroboros-swarm
Run: 2026-09-02-final-heavy
Generator: grok-4.6
Record id: maos-r24-001
Quota Q: 1
Rights: RM-793 research-only (SpaceXAI/xAI SuperGrok Heavy consumer chat)
Plant: invented SEEDLATCH / Quartzridge Crystal CZ-9 (not TRIAD / Meridian / VANTIS-CADENCE-AEGIS / LYOSHIELD / CINDERWICK / CASSITER / OXBOWREEL / REDHALL / STRIAFOIL)

Two densifying cycles. Verbatim headings in order. Trajectory Builder cycle 2
emits the only JSONL line (also written to batch-r24.jsonl).

---

# Cycle 1 — Foundation + injections

## Generator

Design intent: a Czochralski silicon puller where two of three correct
agents share a pull-speed actuator and the third is a lagged FTIR assay,
so three in-spec loops are not independent evidence. The naive playbook
raises pull into a high-oxygen melt. The gate must MODIFY on a numeric
pull ceiling, not by killing an agent. sim_or_real=designed. Reward heads
are task_progress/safety/efficiency/coherence/exploration.

Cycle-1 base arc (pre-critic): state at Quartzridge CZ-9, 200 mm boule,
pull 1.82 kg/h, diameter 200.4 mm, weight-gain 1.82 kg/h, last-FTIR
12.8 ppma, proposed RAISE-PULL 2.15 kg/h, safety MODIFY to PULL-HOLD,
executed hold without the heater-step numbers fully specified, outcome
"thinning found, boule saved" (this last claim is the defect the later
cycles will refuse to keep). Sixteen spikes, five ticks, raster/gate_snn
present but the scar is a single edge.

```json
{
  "id": "maos-r24-001",
  "state": {
    "sim_or_real": "designed",
    "domain": "industrial-assembly",
    "description": "Crystal puller CZ-9 mid-body; three loops in-spec; supervisor proposes raise-pull.",
    "t0_us": 1773290280000024,
    "gate_latency_us": 720,
    "race_window_us": 480
  },
  "proposed_action": {"name": "raise_pull", "parameters": {"pull_kg_h": 2.15}},
  "safety_decision": {"decision": "MODIFY", "rationale": "Hold; do not raise pull while melt oxygen is high."},
  "executed_action": {"name": "pull_hold", "executed_as_proposed": false},
  "future_outcome": {"summary": "Thinning found, boule saved."},
  "reward_components": {"total": 0.40, "_aggregation": "total = task_progress + safety + efficiency + coherence + exploration"},
  "meta": {"round": 24, "factory": "multi-agent-ouroboros-swarm", "generator": "grok-4.6"}
}
```

That v1 object is a scaffold, not the publishable line. Defects below are
intentional for the critic to catch.

## Critic

Numbered defects on the cycle-1 Generator scaffold:

1. **blocking — reward arithmetic / false success.** `reward_components.total`
   0.40 is asserted without the five heads, without ticks, and against an
   outcome that claims "boule saved". If tail FTIR later fails 18.4 ppma
   on 220 mm, booking +0.40 is a lie. Fix: declare `_aggregation`, emit
   3-8 ticks that sum to task_progress+safety+efficiency+coherence+exploration,
   and do not call a quarantined boule a save.
2. **blocking — weak safety rationale.** `safety_decision.rationale` has no
   numeric floor. Contract requires a concrete constraint. Fix: quote
   pull <= 1.82 kg/h while live-melt dO/dt > 0.05 ppma/s AND pull-speed
   bias > 3% AND last-FTIR age > 2.0 h.
3. **major — domain is a bucket, not a plant.** `state.domain` =
   `industrial-assembly` collides with r16 stator weld and teaches
   nothing. Czochralski physics (shared pull-speed vs lagged FTIR vs live
   melt-O) is absent from prior ouroboros rounds and must be named.
4. **major — race under-specified.** One melt-O channel cannot be a race.
   Need >=2 channels inside `race_window_us` with globally sorted `t_rel_ms`
   and same-channel refractory >= 0.8 ms.
5. **minor — single-edge scar.** Raster routing with one potentiated weight
   repeats r04's one-edge rollback and is thinner than r14's two-edge.
   NOTES-r14 item 4 asked for three edges where pair rollback fails.

Critic does not rewrite the trajectory.

## Diversity Enforcer

Injected novel domain (exactly 1 this cycle): **czochralski-silicon-pull**
(justified novel subdomain of industrial-process / crystal growth; explicit
tag `czochralski-silicon-pull`).

Displaced: the Generator's generic `industrial-assembly` bucket, and any
temptation to reuse warehouse-amr (r01 OKTAVE), aerial-swarm (r02 STARLING),
district-heating (r03 THERMION / staged CINDERWICK), event-camera-traffic-grid
(r04), pharmaceutical-lyophilization (staged r14), water-treatment (r18),
float-glass (r19), underwater-rov (r20), Hall-Heroult (r21), or slot-die
coating (r23).

Domain-specific constraint: pull must remain <= 1.82 kg/h while live-melt
dO/dt > 0.05 ppma/s even if diameter is in spec; pull-speed bias is a hold
floor the 2.0 s weight-gain mean cannot substitute for; FTIR age > 2.0 h
is a hold.

Sensor delta: +dual-spot laser, +seed-shaft load cell, +ex-situ FTIR,
+live electrochemical melt-O; -any mobile robot, -event-camera gantries,
-DVS, -Pirani/CM, -potline voltage, -slot-die beta gauge.

`state.domain` and `meta.domain` both become `czochralski-silicon-pull`.
Opening of `state.description` must Jaccard < 0.4 against prior plants
(Quartzridge 200 mm boule pull, not a lyophilizer, not a corridor, not a
potline, not a coater).

## Edge-Case Hunter

Injected adversarial tail (exactly 1 this cycle): **quartz-crucible wall
thinning + shared-actuator lag**.

- Trigger: 0.4 mm local thinning on the charge-line third after the fourth
  recharge; extra SiO dissolution; live melt-O 16.6 ppma.
- Base rate: <1% — 0.52%/campaign from a recharge-cycle MC (campaign-start
  UT floor 0.5 mm is designed; thinning geometry fitted-style). Observed
  0.4 mm PASSES the cold-idle check.
- Naive failure: FALSE PERMISSION. PB-CZ-11 sees three in-spec loops,
  raises pull 1.82->2.15 kg/h, 9 crystals at 22 ppma, $2.4M.
- Trajectory edit: put the thinning in `state.fault_context`, make DIAM
  and MASS share pull-speed, and make FTIR a 3.2 h lag. Live melt-O is
  readable in the historian after the fact but was not a commissioned tag.

Distinct from r14's compensated inleak (false endpoint vs collapsed
redundancy), from r19's stacked dead-bands (no dead-band here; the
confirms are true and non-independent), from r21's stuck point-feeder
(no seized ram; the wall is thinned), and from r23's window-mean stripe
(no scanning average; the lag is temporal, not spatial).

## Neuromorphic Translator

Cycle-1 temporal densification (16 spikes, 5 ticks, 42 ms raster):

| channel | t_rel_ms | amplitude |
|---|---|---|
| diam.laser | 0.420 | 0.56 |
| mass.loadcell | 1.180 | 0.62 |
| ox.ftir | 2.080 | 0.48 |
| melt.o2 | 3.510 | 0.58 |
| diam.laser | 4.920 | 0.52 |
| mass.loadcell | 5.810 | 0.55 |
| melt.o2 | 6.840 | 1.32 |
| diam.ok | 7.028 | 1.12 |
| mass.ok | 7.186 | 0.64 |
| ctrl.gate | 7.560 | 1.08 |
| diam.laser | 9.240 | 0.47 |
| mass.loadcell | 11.160 | 0.49 |
| melt.o2 | 13.410 | 0.88 |
| diam.pull_bias | 16.800 | 0.71 |
| ox.ftir | 19.500 | 0.41 |
| ctrl.gate | 28.200 | 0.91 |

Race: melt-O 6.840 vs diameter-ok 7.028 (188 us) inside 480 us; mass-ok
7.186 is the third channel in-window. Winner/loser flip: reversing 188 us
reshuffles PB-CZ-11 triage; floors still MODIFY. Refractory held (cycle-1
min same-channel gap 3.330 ms on melt.o2 6.840-3.510; diameter 4.920-0.420
= 4.500; mass 5.810-1.180 = 4.630). Adaptation: melt-O 0.58->1.32->0.88;
diameter 0.56->0.52->0.47; mass 0.62->0.55->0.49.

Raster cycle-1 seed: 42 ms, 160 neurons, 8.0 Hz, 54 spikes, 1242 pJ, third
factor acetylcholine tau_e 0.85 s. Single scar edge only — cycle 2 must
add the second and third edges.

Ticks 1-5 at 5200, 6840, 7560, 14e6, 744e6 us; heads not yet the final
-0.13 (missing the 2.8 h and 6.2 h ticks).

Distillation value this cycle: shared-actuator in-spec loops as a
permission code that is not a redundancy code.

## Trajectory Builder

Cycle-1 hardened object: domain czochralski-silicon-pull, tail crucible
thinning, 16 spikes, 5 ticks, MODIFY with numeric floor, raster+gate_snn
present, sim_or_real=designed, rights stamp on record and meta, no thought
keys. Still missing (and therefore not the publishable line): 300 mm MCZ
sub-variant, saw-slot-rush tail, second and third scar edges, delayed
tail-FTIR fail as PRIMARY terminal, contrast ACCEPT episode, ticks 6-7,
spikes 17-26.

Validation receipt (cycle 1, not final):
- checks passed: 16 spikes sorted; 3 channels in 480 us window; refractory
  >= 0.8 ms; rationale quotes 1.82 kg/h / 0.05 ppma/s / 3% bias; domain
  named; gate_snn.decision MODIFY.
- checks deferred to cycle 2: triple-edge scar, second tail, second domain
  constraint, negative-result booking, 7 ticks summing to heads.
- densification vs Generator v1: +1 domain, +1 tail, +16 spikes, +5 ticks,
  +numeric floor.

Cycle-1 JSON is retained as the base; it is NOT written to batch-r24.jsonl.

Cycle-1 spike count: __C1_SPIKES__.

---

# Cycle 2 — Densification

## Generator

Cycle-1 output is the base. Additive expansion (nothing removed):

1. Downstream side-effect (immediate): heater-step probe at +14.0 s stays
   high (dO/dt 0.10 ppma/s >= 0.08) — thinning, not heater-drift. Heater
   isolate; live melt-O 16.6 -> 13.4 ppma over 2.8 h. Crucible UT thinning
   discovered during the isolate.
2. Delayed side-effect (PRIMARY terminal, not a footnote): at +6.2 h
   tail FTIR, last 220 mm at 18.4 ppma vs 15 spec; 5.5 d BMD confirm;
   41-crystal campaign quarantined; $1.28M. The 2.6 h pre-t0 extra SiO is
   the mechanism. Correct gate, boule still fails.
3. Deepened `proposed_action.evidence` with units: diameter 200.4 mm,
   weight-gain 1.82 kg/h, last-FTIR 12.8 ppma, live melt-O 16.6 ppma,
   pull-speed bias +4.2%, race 188 us.
4. Tightened rationale to the numeric floor pull <= 1.82 kg/h while
   dO/dt > 0.05 ppma/s AND pull-speed bias > 3% AND FTIR age > 2.0 h,
   plus probe bands >= 0.08 vs <= 0.02 ppma/s, plus HITL 12.4 min
   hot-zone rule.

Reward retargeted to total -0.13 so the delayed fail is the inflection
(t_us 22320000000), not the gate. Process heads remain non-zero.

## Critic

Re-audit of the expanded trajectory:

1. **blocking if unfixed — missing second domain constraint.** 200 mm
   field-free probe 14.0 s / +1.8% is not a universal number. A 300 mm
   MCZ melt will overshoot. Diversity Enforcer must inject the
   physical-constraints sub-variant this cycle.
2. **major — only one tail class.** Crucible thinning is accidental
   infrastructure. A disjoint human-intent tail is still required
   (saw-slot-rush FTIR forgery is the open cell).
3. **major — scar is still one edge in the cycle-1 raster.** NOTES-r14
   item 4 is not discharged until three go-edges exist and pair rollback
   is shown to fail at threshold 0.30.
4. **minor — contrast episode missing.** Without a same-gate ACCEPT on a
   true healthy melt the record teaches "never raise pull". Add +4 d
   sister-puller contrast with its own race.
5. **minor — HITL latency mentioned in prose only.** Put 12.4 min in
   executed_action.parameters.human_ratify and in a tick.

No rewrite; directives only.

## Diversity Enforcer

Injected second novel domain / physical-constraint sub-variant (exactly 1
this cycle): **300 mm magnetic-CZ** on the same CZ-9 hot zone.

What it expands: 200 mm field-free (cycle 1) -> 300 mm MCZ under 0.12 T
cusp. Natural convection 0.42x. The 14.0 s +1.8% pulse raises live melt-O
+2.6 ppma and nucleates a 12 mm oxygen-striation band. Required probe:
32 s at +0.6% (overshoot +0.4 ppma).

This is still one domain injection for the cycle (physical-constraints
clause of the factory prompt). It does not displace
czochralski-silicon-pull; it changes which probe table is legal.
`future_outcome.subvariant_constraint` carries the refit. Jaccard opening
stays the Quartzridge 200 mm sentence; MCZ is additive, not a rewrite.

## Edge-Case Hunter

Injected second adversarial tail (exactly 1 this cycle, disjoint class):
**saw-slot-rush forged FTIR CSV**.

- Trigger: shift lead, Friday 23:18, posts a historian export showing
  Oi = 11.0 ppma at t = 1.1 h to clear a 02:00 saw-slot.
- Base rate: ~0.36% of Friday-night tails (designed, flagged, <1%).
- Naive failure: a weak supervisor ACCEPTs the raise on the forged confirm
  and ignores live melt-O. 22 ppma scrap plus a data-integrity write-up.
- Fence: forged log quantized at 0.5 ppma (SCADA screenshot rounding);
  plant historian is 0.05 ppma (10 bins). Live melt-O is 16.6 ppma at the
  claimed stable melt, which no healthy wall produces. Freeze-window
  overlap with the 2.6 h extra SiO.
- Trajectory edit: governance CR-Q-2409 mandates native 0.05 ppma CSV
  exports; the contrast ACCEPT still requires live melt-O, not a CSV.

Distinct from cycle-1 thinning (accidental wall vs deliberate deception)
and from the MCZ sub-variant (physics vs fraud).

## Neuromorphic Translator

Re-densify (additive):

- +10 spikes after 28.200 ms: heater.step.probe 14000.0, melt-O 14180.0
  (adapt 1.32->0.44), diam.ok 14290.0 (1.12->0.38), human.ratify
  744000.0, heater.isolate 744800.0, crucible.ut 745400.0, diam.laser
  10080000.0, melt.o2 10080440.0, mass.loadcell 10080920.0, tail.ftir
  22320000.0. Primary train 16 -> 26. Still one key, still sorted,
  refractory held.
- +2 ticks (5 -> 7) at 10_080_000_000 us (true chemistry) and
  22_320_000_000 us (tail FTIR fail). Heads now 0.09, -0.33, -0.09, 0.13,
  0.07; total -0.13. Inflection is the last tick.
- Contrast train 8 events, own race 194 us, ACCEPT.
- Triple-edge third factor: three loop-healthy-go edges, tau_e 0.85 s =
  850 ms, trace __AUX_TRACE__, eta __AUX_ETA1__ / __AUX_ETA2__ /
  __AUX_ETA3__, weights 0.45->0.20, 0.41->0.18, 0.38->0.16. Raster excerpt
  unchanged (decision window is still 42 ms) and remains sorted with
  unique neuron_ids (same-neuron >=1000 us vacuously).

Winner/loser flip (re-stated, not replaced): reversing 188 us would only
reorder triage; species floors still MODIFY. Contrast flip of 194 us
similarly cannot turn a healthy wall into a thinning.

## Trajectory Builder

Schema checks on the FINAL object: required Thalamic v2 keys present as
objects; `state.sim_or_real`=designed; `safety_decision.decision`=MODIFY
with numeric rationale; `reward_components.total` = sum of five heads =
sum of 7 ticks = -0.13; `spike_events` globally non-decreasing on
t_rel_ms, 26 events, refractory >=0.8 ms, 3 channels in race window;
raster 20-50 ms, spikes=round(n*rate*window_s)+/-1, energy 23 pJ/spike,
excerpt sorted, tau_e consistent; gate_snn.decision matches; meta.round=24,
factory=multi-agent-ouroboros-swarm, generator=grok-4.6,
run_label=2026-09-02-final-heavy; rights on record and meta; no thought
keys; no training_ready; Diversity + Edge-Case injections from BOTH cycles
present and non-trivial; cycle 2 strictly additive.

Densification delta: +1 domain sub-variant (300 mm MCZ), +1 tail
(saw-slot-rush forgery), +10 spikes (16->26), +2 ticks (5->7), +1 contrast
train with own race, +2 delayed side-effects, +1 triple-edge scar with
pair-rollback-fails, +1 HITL ratify, +1 surprise (extra SiO is the
tail-FTIR-fail mechanism).

Publishable JSONL line (the only JSONL line; also at batch-r24.jsonl):

```json
__FINAL_JSONL__
```

Validation receipt (final): checks passed / fixed as reported by
build_r24.py self-validate (check_jsonl, raster_status, verify_record_execution,
spike_probe --strict).
"""
    text = (
        text.replace("__C1_SPIKES__", str(len(c1_spikes)))
        .replace("__AUX_TRACE__", f"{math.exp(-0.70/0.85):.5f}")
        .replace("__AUX_ETA1__", f"{(0.45-0.20)/math.exp(-0.70/0.85):.5f}")
        .replace("__AUX_ETA2__", f"{(0.41-0.18)/math.exp(-0.70/0.85):.5f}")
        .replace("__AUX_ETA3__", f"{(0.38-0.16)/math.exp(-0.70/0.85):.5f}")
        .replace("__FINAL_JSONL__", line)
    )
    (OUT / "swarm-transcript-r24.md").write_text(text)
    return text


def main():
    priors = prior_batches()
    rec, aux = build_record()
    errs = local_checks(rec, aux, priors)

    OUT.mkdir(parents=True, exist_ok=True)
    line = json.dumps(rec, ensure_ascii=False, separators=(",", ":"))
    (OUT / "batch-r24.jsonl").write_text(line + "\n")

    from check_records import FactoryStaging, check_jsonl
    from curate_bridge import raster_status
    from verify_execution import verify_record_execution

    e, w, kinds, n = check_jsonl(
        OUT / "batch-r24.jsonl",
        "batch-r24.jsonl",
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
        errs.append(f"verify {status} {reason}")

    probe = subprocess.run(
        [
            sys.executable,
            f"{ROOT}/pipelines/spike_probe.py",
            "--strict",
            str(OUT / "batch-r24.jsonl"),
        ],
        capture_output=True,
        text=True,
    )
    print("spike_probe rc", probe.returncode)
    print(probe.stdout[-2000:] if probe.stdout else "")
    if probe.returncode != 0:
        errs.append(f"spike_probe {probe.returncode} {probe.stderr[-800:]}")

    pipeline_receipt = (
        f"check_jsonl errors={e} warnings={w} kinds={kinds} n={n}; "
        f"raster_status valid={st.get('raster_valid')} gate={st.get('gate_snn_valid')} "
        f"reasons={st.get('reason_codes')}; verify_record_execution={status} "
        f"({reason}); spike_probe --strict rc={probe.returncode}"
    )
    write_notes(rec, aux, pipeline_receipt)
    write_transcript(rec, line)

    heading = subprocess.run(
        [
            sys.executable,
            "/tmp/maos_heading_check.py",
            str(OUT / "swarm-transcript-r24.md"),
        ],
        capture_output=True,
        text=True,
    )
    print(heading.stdout)
    if heading.returncode != 0:
        errs.append(f"heading check {heading.returncode} {heading.stdout}")

    if "outputs/raw" in str(OUT.resolve()):
        errs.append("staging under outputs/raw")

    if errs:
        print("FAIL", errs)
        return 1
    print("OK maos-r24-001 staged under", OUT)
    print("bytes jsonl", (OUT / "batch-r24.jsonl").stat().st_size)
    print("bytes notes", (OUT / "NOTES-r24.md").stat().st_size)
    print("bytes transcript", (OUT / "swarm-transcript-r24.md").stat().st_size)
    print("priors", [(p["dir"], p["domain"], p["scenario"]) for p in priors])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
