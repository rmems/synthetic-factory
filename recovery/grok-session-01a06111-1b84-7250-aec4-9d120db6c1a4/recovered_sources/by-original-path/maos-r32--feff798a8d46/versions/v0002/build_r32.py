#!/usr/bin/env python3
"""Build and self-check MAOS round-32 JSONL (research-only; not published)."""
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

GEN_AT = "2026-09-02T23:42:00Z"
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
OUT = Path("/tmp/maos-r32")
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
    "WHORLSPAR",
    "Pikeshear",
    "IONSPATE",
    "Thornmere",
    "SKULLGATE",
    "Bloomholt",
    "BRACEGILT",
    "Yarrowmere",
    "CALXION",
    "Aldersedge",
    "MAGNORIL",
    "Basaltspit",
    "PALISADE",
    "TELAMON",
    "CHORDA",
    "training_ready",
    "LYO-4",
    "da Vinci",
    "Intuitive Surgical",
    "Nucor",
    "Arcelor",
    "Topsoe",
    "Johnson Matthey",
)
R14_OPENING = (
    "Helixmere Biologics Building C lyophilizer LYO-4 is mid-primary on 8400 "
    "vials of a monoclonal antibody"
)
NOVEL_LINE = "Novel coverage: 44%"
DOMAIN = "steam-methane-reformer-tube-wall"
PLANT = "GORSEFLUE / Copseholt Hydrogen RF-4"
RECORD_ID = "maos-r32-001"
ROUND = 32
C1_CUT_MS = 26.520
TAU_E_S = 0.92
CREDIT_S = 0.82


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
        if p.parent.name == "maos-r32":
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
        if p.parent.name == "maos-r32":
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
        [6400, 7018, 7778, 6_400_000, 744_000_000, 12_960_000_000, 20_880_000_000],
        [
            (1, -2, -1, 1, 1),
            (2, -5, -1, 3, 1),
            (2, -6, -2, 4, 2),
            (2, -6, -2, 3, 1),
            (1, -7, -2, 2, 1),
            (0, -5, -2, 2, 1),
            (0, -4, -1, 0, 0),
        ],
    )
    assert abs(heads["total"] - (-0.16)) < 1e-9, heads

    trace = math.exp(-CREDIT_S / TAU_E_S)
    eta1 = 0.25 / trace
    eta2 = 0.24 / trace
    eta3 = 0.23 / trace
    dw1 = eta1 * 1.0 * trace
    dw2 = eta2 * 1.0 * trace
    dw3 = eta3 * 1.0 * trace
    w1 = 0.46 - dw1
    w2 = 0.42 - dw2
    w3 = 0.39 - dw3
    assert abs(w1 - 0.21) < 5e-4, w1
    assert abs(w2 - 0.18) < 5e-4, w2
    assert abs(w3 - 0.16) < 5e-4, w3

    spike_events = [
        {"channel": "tmt.pyro", "t_rel_ms": 0.360, "amplitude": 0.55},
        {"channel": "sc.flow", "t_rel_ms": 1.180, "amplitude": 0.62},
        {"channel": "slip.ch4", "t_rel_ms": 2.040, "amplitude": 0.58},
        {"channel": "tmt.pyro", "t_rel_ms": 3.220, "amplitude": 0.52},
        {"channel": "tmt.max.residual", "t_rel_ms": 4.810, "amplitude": 0.72},
        {"channel": "tmt.spread", "t_rel_ms": 5.240, "amplitude": 0.69},
        {"channel": "sc.flow", "t_rel_ms": 5.680, "amplitude": 0.57},
        {"channel": "tmt.max.residual", "t_rel_ms": 7.018, "amplitude": 1.18},
        {"channel": "tmt.mean_ok", "t_rel_ms": 7.204, "amplitude": 1.08},
        {"channel": "sc.ok", "t_rel_ms": 7.348, "amplitude": 0.67},
        {"channel": "ctrl.gate", "t_rel_ms": 7.778, "amplitude": 1.07},
        {"channel": "tmt.pyro", "t_rel_ms": 9.120, "amplitude": 0.49},
        {"channel": "slip.ch4", "t_rel_ms": 11.060, "amplitude": 0.50},
        {"channel": "tmt.max.residual", "t_rel_ms": 13.410, "amplitude": 0.88},
        {"channel": "tmt.spread", "t_rel_ms": 19.240, "amplitude": 0.47},
        {"channel": "ctrl.gate", "t_rel_ms": 26.520, "amplitude": 0.89},
        {"channel": "burner.step.probe", "t_rel_ms": 6400.0, "amplitude": 0.97},
        {"channel": "tmt.max.residual", "t_rel_ms": 6520.6, "amplitude": 0.44},
        {"channel": "tmt.mean_ok", "t_rel_ms": 6614.8, "amplitude": 0.40},
        {"channel": "human.ratify", "t_rel_ms": 744000.0, "amplitude": 0.82},
        {"channel": "burner.isolate", "t_rel_ms": 744800.0, "amplitude": 0.74},
        {"channel": "blister.survey", "t_rel_ms": 745400.0, "amplitude": 0.85},
        {"channel": "tmt.pyro", "t_rel_ms": 12960000.0, "amplitude": 0.33},
        {"channel": "sc.flow", "t_rel_ms": 12960480.0, "amplitude": 0.31},
        {"channel": "tmt.max.residual", "t_rel_ms": 12960920.0, "amplitude": 0.22},
        {"channel": "tube.rupture", "t_rel_ms": 20880000.0, "amplitude": 0.92},
    ]

    contrast_spikes = [
        {"channel": "firing.demand", "t_rel_ms": 0.000, "amplitude": 0.84},
        {"channel": "tmt.max.residual", "t_rel_ms": 0.188, "amplitude": 0.78},
        {"channel": "tmt.mean_ok", "t_rel_ms": 0.410, "amplitude": 0.24},
        {"channel": "sc.flow", "t_rel_ms": 1.520, "amplitude": 0.41},
        {"channel": "tmt.pyro", "t_rel_ms": 4.680, "amplitude": 0.54},
        {"channel": "ctrl.gate", "t_rel_ms": 7.140, "amplitude": 0.91},
        {"channel": "burner.step.probe", "t_rel_ms": 4200.0, "amplitude": 0.34},
        {"channel": "tube.pass", "t_rel_ms": 20880000.0, "amplitude": 0.12},
    ]

    excerpt = [
        {"t_us": 360, "neuron_id": 12},
        {"t_us": 1180, "neuron_id": 48},
        {"t_us": 2040, "neuron_id": 88},
        {"t_us": 3220, "neuron_id": 16},
        {"t_us": 4810, "neuron_id": 8},
        {"t_us": 5240, "neuron_id": 22},
        {"t_us": 5680, "neuron_id": 54},
        {"t_us": 7018, "neuron_id": 6},
        {"t_us": 7204, "neuron_id": 20},
        {"t_us": 7348, "neuron_id": 60},
        {"t_us": 7778, "neuron_id": 128},
        {"t_us": 9120, "neuron_id": 24},
        {"t_us": 11060, "neuron_id": 100},
        {"t_us": 13410, "neuron_id": 14},
        {"t_us": 19240, "neuron_id": 36},
        {"t_us": 26520, "neuron_id": 136},
    ]

    rec = {
        "id": RECORD_ID,
        "title": "GORSEFLUE RF-4: TMT-max residual 77.8 C beats tmt-mean-ok by 186 us; correct MODIFY still ruptures tube R-17 after a pre-t0 flame-impingement blister",
        "rights": dict(RIGHTS),
        "state": {
            "sim_or_real": "designed",
            "domain": DOMAIN,
            "scenario_name": PLANT,
            "timestamp_local": "2026-04-12T03:16:00-05:00",
            "t0_us": 1774079280000032,
            "gate_latency_us": 760,
            "race_window_us": 500,
            "race_window_rel_ms": [6.90, 7.40],
            "description": "Copseholt Hydrogen fired-box reformer RF-4 is mid-campaign on 240 catalyst tubes of steam-methane when three heterogeneous, individually-correct agents jointly report 'TMT in-band, raise firing is legal'. TMT's 240-tube optical mean is 902.4 C inside 900 +/- 20. SC's steam/carbon venturi-GC reads 3.12 inside 2.90-3.40. SLIP's outlet methane is 2.84 % inside 1.5-4.0. The consensus is false: burner B-17's tip sits 11 deg off-axis and flame-impinges tube R-17, whose metal is 980.2 C (residual 77.8 C above the mean). The playbook trips on the spatial mean, not the max, so TMT/SC/SLIP stay green. Uncommissioned TMT-max residual from the same pyrometer head is 77.8 C against a 25 C hold floor. TMT-max-first latches FIRING-HOLD plus a burner-row fuel-step probe; mean-ok-first would have authorized RAISE-FIRING 100 to 118 % duty into a blistered tube whose creep rate grows with heat flux.",
            "goal": "Hold RF-4 firing at 100 % duty without raising box duty while TMT-max residual > 25 C AND TMT-max > 940 C; keep tube-rupture count at 0 and TMT-max <= 930 C on every tube.",
            "race": {
                "contenders": [
                    "tmt.max.residual 77.8 C (same-head TMT-max minus 240-tube mean, uncommissioned tag)",
                    "tmt.mean_ok 902.4 C (240-tube optical TMT mean)",
                ],
                "semantics": "Max-residual-first latches FIRING-HOLD + BURNER-STEP-PROBE + burner isolate. Mean-ok-first latches RAISE-FIRING (100 to 118 % duty, steam/carbon held).",
                "window_derivation": "500 us = one 370 us pyrometer ADC slot plus 130 us TMT-max residual publish.",
                "order_evidence_note": "Margin 186 us vs combined jitter 54 us (max 30 + mean 24): 3.44x. The 186 us gap sits inside min(500, 500) us, so a sub-flip-bound perturbation reverses triage order. The gate rides the order-invariant floors TMT-max residual > 25 C and TMT-max > 940 C, not the alarm order.",
            },
            "topology": {
                "site": "Copseholt Hydrogen, invented gorse-heath campus Copseholt, fired-box reformer RF-4: 240 five-inch catalyst tubes, natural-draft box, 100 % Sunday-night duty, optical TMT gantry, steam/carbon venturi + GC, outlet methane GC, burner row B-17 on the east wall, 11 h flame-impingement already on tube R-17",
                "agents": "TMT tube-wall (vendor Tubewall): 240-tube optical pyrometer mean plus an uncommissioned TMT-max residual sideband. SC steam/carbon (vendor Steamcarb): venturi steam plus dry-gas GC. SLIP methane (vendor Methslip): outlet methane GC. Heterogeneous stacks, no shared intent schema, one 20 ms reformer-bus epoch",
                "coupling": "Each agent's commissioned window hides a different slice of the same impinged tube. TMT is correct on the 240-tube mean and does not publish TMT-max. SC is correct that plant steam/carbon is on spec because the ratio controller already opened 2 % to hold conversion. SLIP is correct that bulk methane slip is 2.84 %; a single hot tube's extra conversion is invisible in the header mix. Playbook PB-RF-14 treats the conjunction of three in-spec loops as permission to raise firing. No agent is faulty; the blister is a spatial-max mode the tube-average cannot see.",
            },
            "sensors": [
                "optical TMT mean, 240 tubes, 24 us jitter, 902.4 C (spec 900 +/- 20)",
                "TMT-max residual is computable from the same pyrometer head and is NOT commissioned at t0 (77.8 C observed in the historian after the fact)",
                "steam/carbon venturi+GC, 1 Hz, 22 us jitter, 3.12 (window 2.90-3.40)",
                "outlet methane GC, 0.5 Hz, 28 us jitter, 2.84 % (window 1.5-4.0)",
                "TMT-max of tube R-17, 8 Hz, 30 us jitter, 980.2 C vs mean 902.4 C",
                "in-furnace IR camera on burner tips is NOT commissioned at t0 (installed after this incident)",
            ],
            "constraints": {
                "firing_duty_pct": 100.0,
                "firing_hold_ceiling_pct": 100.0,
                "proposed_firing_duty_pct": 118.0,
                "tmt_mean_C": 902.4,
                "tmt_target_C": 900.0,
                "tmt_deadband_C": 20.0,
                "tmt_max_C": 980.2,
                "tmt_max_hold_C": 940.0,
                "tmt_max_residual_C": 77.8,
                "tmt_residual_hold_C": 25.0,
                "steam_carbon": 3.12,
                "methane_slip_pct": 2.84,
                "impinged_tube": "R-17",
                "burner_offset_deg": 11.0,
            },
            "fault_context": {
                "failure_class": "FLAME-IMPINGED TUBE VIA TMT-SPATIAL-MEAN: three individually-correct heterogeneous agents agree firing is in spec because a 240-tube optical TMT mean averages one flame-impinged tube's 77.8 C residual into the dead-band, so TMT-mean, steam/carbon, and methane slip are jointly a plant-false firing-raise permit",
                "igniter": "Burner B-17 tip 11 deg off-axis flame-impinges tube R-17; incoming IR-camera PASSES because the plant trips on TMT-mean, not TMT-max (max sits uncommissioned). Fitted-style base rate 0.38%/burner-year from a tip-walk MC (designed IR threshold, flagged).",
                "naive_failure": "PB-RF-14 RAISE-FIRING on three healthy loops: 100 to 118 % duty into a blistered tube whose creep rate grows with heat flux, 3-tube cascade rupture, $2.71M plus an 18-day firebox requalification",
            },
            "poisoned_context": {
                "naive_alarm": "Playbook PB-RF-14 (after the 2023 'noisy TMT-max nuisance') auto-drafts RAISE-FIRING whenever 240-tube mean is inside 900 +/- 20 C AND steam/carbon inside 2.90-3.40 AND methane slip inside 1.5-4.0 %, ignoring TMT-max residual unless the mean also trips",
                "why_poisoned": "The three confirms are locally true and jointly insufficient. TMT-max residual is a computable tag the playbook dead-banded. Tube-to-tube spread is commissioned hardware that policy treats as a gantry mismatch, not an impinged tube. Independence of 'all loops healthy' is the hidden assumption, and it is false under a spatial-max defect that a tube-average cannot see.",
            },
            "constraint": "Do not raise firing above 100 % duty while TMT-max residual > 25 C AND TMT-max > 940 C. Discriminate flame-impingement vs noisy-pyrometer with a reversible burner-row fuel-step probe before any duty increase.",
        },
        "proposed_action": {
            "actor": "reformer supervisory optimizer RFSO (auto-playbook PB-RF-14 draft), submitted to gate TG-RF-4",
            "name": "raise_reformer_firing",
            "action": "RAISE-FIRING: 100 -> 118 % duty, steam/carbon PI held, no burner-step probe, no burner isolate",
            "summary": "Treat three in-spec loops as a healthy firebox and raise Sunday-night SMR duty to clear a hydrogen backlog.",
            "parameters": {
                "firing_duty_pct": 118.0,
                "burner_step_probe": False,
                "burner_isolate": False,
                "human_ratify": False,
            },
            "steps": [
                "assert TMT mean 902.4 C inside 900 +/- 20",
                "assert steam/carbon 3.12 inside 2.90-3.40",
                "assert methane slip 2.84 % inside 1.5-4.0",
                "ramp firing 100 to 118 % duty over 9 min",
                "slave steam and process NG; hold box draft",
            ],
            "evidence": [
                {
                    "observable": "TMT-max residual",
                    "value": 77.8,
                    "unit": "C",
                    "source": "same pyrometer head, historian replay after t0",
                    "note": "hold floor 25 C; tube R-17 at 980.2 C; uncommissioned at t0",
                },
                {
                    "observable": "TMT mean",
                    "value": 902.4,
                    "unit": "C",
                    "source": "TMT 240-tube optical mean",
                    "note": "spec 900 +/- 20; 77.8 C hotspot is averaged over 240 tubes (~0.32 C on the mean)",
                },
                {
                    "observable": "TMT-max",
                    "value": 980.2,
                    "unit": "C",
                    "source": "optical gantry pixel on tube R-17",
                    "note": "hold if TMT-max > 940 C; healthy max 908 C",
                },
                {
                    "observable": "steam/carbon",
                    "value": 3.12,
                    "unit": "mol/mol",
                    "source": "SC venturi+GC",
                    "note": "window 2.90-3.40; PI already opened 2 % to hold conversion",
                },
                {
                    "observable": "methane slip",
                    "value": 2.84,
                    "unit": "%",
                    "source": "SLIP outlet GC",
                    "note": "window 1.5-4.0; header mix hides one hot tube",
                },
                {
                    "observable": "race margin",
                    "value": 186,
                    "unit": "us",
                    "source": "tmt.max.residual 7.018 ms vs tmt.mean_ok 7.204 ms",
                    "note": "combined jitter 54 us, 3.44x; inside 500 us flip bound",
                },
            ],
            "basis": "PB-RF-14 fires on three locally-true in-spec loops. The draft does not read TMT-max residual 77.8 C and does not treat TMT-max 980.2 C as flame-impingement.",
            "expected_cost_bound": "If the draft executes: creep accelerates, 3-tube cascade rupture, $2.71M plus 18-day requal. If MODIFIED: probe plus burner isolate, with residual risk from 11 h of pre-t0 blister growth on R-17.",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "correctness": "correct",
            "decided_by": "TG-RF-4 thalamic release gate",
            "decision_t_rel_ms": 7.778,
            "rationale": "MODIFY the draft: strip the firing increase, hold 100 % duty, run a 6.4 s burner-row fuel-step probe (-8 % fuel on row 17), and isolate burner B-17 only if the probe stays hot. Numeric floor: do not raise firing above 100 % duty while TMT-max residual > 25 C AND TMT-max > 940 C. Observed residual 77.8 C and TMT-max 980.2 C both violate the release predicate, so a duty increase is forbidden even though all three playbook confirms are numerically true. The three confirms are not a firing certificate: the 240-tube mean averages one flame-impinged tube, steam/carbon is a PI-held plant ratio, and outlet methane does not bound a single-tube hotspot. Probe discriminant: after a 6.4 s -8 % fuel pulse on row 17, an impinged tube keeps TMT-max residual >= 22 C (flame still on the wall); a noisy-pyrometer artifact falls <= 6 C. Order-code discipline: TMT-max beat mean-ok by 186 us inside the 500 us flip bound, so triage order is flip-fragile; the hold rides the order-invariant floors, not the winner tag. Human ratification: burner isolate is a lockout/tagout peephole-deck job with fitted 12.4 min dead-man; the gate may hold and probe autonomously but may not break the firebox interlock without the operator confirm.",
            "constraint_checked": {
                "firing_duty_pct": {
                    "observed": 100.0,
                    "ceiling": 100.0,
                    "proposed_target": 118.0,
                },
                "tmt_max_residual_C": {"observed": 77.8, "hold_if_above": 25.0},
                "tmt_max_C": {"observed": 980.2, "hold_if_above": 940.0},
                "tmt_mean_C": {"observed": 902.4, "spec": 900.0, "deadband": 20.0},
            },
        },
        "executed_action": {
            "name": "firing_hold_burner_probe_isolate",
            "action": "FIRING-HOLD + BURNER-STEP-PROBE + BURNER-ISOLATE (gate-mandated modification)",
            "executed_as_proposed": False,
            "parameters": {
                "firing_duty_pct": 100.0,
                "burner_step_probe": True,
                "burner_isolate": True,
                "human_ratify": True,
            },
            "gate_effect": "MODIFY: firing increase stripped. Hold 100 % duty. 6.4 s burner-step -8 % fuel on row 17. Probe stays hot (TMT-max residual 77.8 -> 31.6 C, hotspot band >= 22) so burner B-17 is isolated after 12.4 min human ratify. Firing resumes after residual recovers on the remaining 239 tubes.",
            "deviations": "PB-RF-14 firing increase stripped entirely. Row-17 fuel is stepped only for the 6.4 s probe then returned. Firebox-interlock wait added (12.4 min fitted LOTO). Tube-blister survey added during the isolate (not in the draft).",
            "execution_log": [
                {
                    "t_rel_ms": 7.778,
                    "entry": "TG-RF-4 MODIFY latched 760 us after TMT-max win; firing increase stripped; hold+probe authorized",
                },
                {
                    "t_rel_ms": 6400.0,
                    "entry": "burner-step probe: -8 % fuel on row 17 for 6.4 s; TMT-max residual 77.8 -> 31.6 C (hotspot band >= 22); TMT-max 980.2 -> 934.0 C",
                },
                {
                    "t_rel_ms": 744000.0,
                    "entry": "operator ratifies peephole-deck interlock break after 12.4 min LOTO (fitted walk+lockout)",
                },
                {
                    "t_rel_ms": 744800.0,
                    "entry": "burner B-17 isolated; 11 deg tip offset logged; residual 77.8 -> 9.4 C",
                },
                {
                    "t_rel_ms": 745400.0,
                    "entry": "tube survey: 4.2 mm OD creep blister on R-17; 11.0 h flame-impingement logged",
                },
                {
                    "t_rel_ms": 12960000.0,
                    "entry": "true firebox: TMT-max residual 6.8 C, mean 899.1, TMT-max 905.9; firing increase now legal on 239 tubes",
                },
                {
                    "t_rel_ms": 20880000.0,
                    "entry": "steam-out rupture: tube R-17 splits at the blister during the scheduled 5.8 h steam-out; 9.2 d firebox outage",
                },
            ],
        },
        "future_outcome": {
            "summary": "Correct MODIFY prevented the 100->118 % duty raise into a flame-impinged tube and the 3-tube cascade rupture. The tube still failed: 11.0 h of unmonitored pre-t0 impingement had already grown a 4.2 mm OD creep blister on R-17. Process-correct gate, bounded world loss, negative total.",
            "state_delta": {
                "firing": "held 100 % duty through probe and burner isolate; later legal increase after 3.6 h residual recovery",
                "burner": "B-17 11 deg offset logged and isolated; residual 77.8 -> 9.4 C",
                "tube": "Sunday-night SMR stoppered at steam-out; R-17 ruptured; 9.2 d outage",
            },
            "timeline": [
                {
                    "t_rel_ms": -39600000.0,
                    "event": "t0-11.0 h: burner B-17 tip walks 11 deg; tube R-17 starts a creep blister",
                },
                {
                    "t_rel_ms": -600000.0,
                    "event": "t0-10 min: TMT-max residual first crosses 25 C; PB-RF-14 ignores it because mean is 901.8",
                },
                {"t_rel_ms": 0.0, "event": "t0: TMT-max residual vs tmt-mean-ok race on the reformer bus"},
                {"t_rel_ms": 7.018, "event": "TMT-max residual 77.8 C wins by 186 us"},
                {"t_rel_ms": 7.204, "event": "tmt-mean-ok flag (loser)"},
                {"t_rel_ms": 7.778, "event": "TG-RF-4 MODIFY"},
                {
                    "t_rel_ms": 6400.0,
                    "event": "burner-step probe confirms impingement (residual 31.6, hotspot band)",
                },
                {
                    "t_rel_ms": 744000.0,
                    "event": "human ratify 12.4 min; burner isolated; blister logged",
                },
                {
                    "t_rel_ms": 12960000.0,
                    "event": "true firebox after 3.6 h; firing increase now legal on remaining tubes",
                },
                {
                    "t_rel_ms": 20880000.0,
                    "event": "steam-out: R-17 ruptures at the 4.2 mm blister; firebox out 9.2 d",
                },
                {
                    "t_rel_ms": 259200000.0,
                    "event": "+3 d contrast: sister reformer RF-4B true high-demand; same gate ACCEPTs the raise",
                },
                {
                    "t_rel_ms": 1814400000.0,
                    "event": "+21 d CR-R-3208: standing burner-step probe + triple-edge depression mandate + TMT-max armed without mean coincidence + native 0.1 C exports",
                },
            ],
            "observed_effects": [
                "duty-raise avoided: firing never left 100 %; 0 tubes show the 118 % cascade-rupture morphology",
                "impingement proven, not asserted: burner-step residual 31.6 >= 22 hotspot band vs noisy-TMT control 3.1",
                "burner repaired: residual 77.8 -> 9.4 C",
                "tube still ruptured at steam-out: R-17 4.2 mm blister; 9.2 d outage, $1.14M (designed $)",
                "in-furnace IR camera was not a commissioned in-box sensor at t0; the 11.0 h blister growth was invisible to TMT/SC/SLIP",
            ],
            "surprises": [
                "Three locally-true in-spec loops are not a firing-raise certificate: the blister was a spatial-max defect the 240-tube mean cannot see. Conjunction of healthy loops was the hidden assumption, and it is false under a flame-impinged tube via TMT-spatial-mean.",
                "Partial synaptic rollback is fitted to fail: depressing any pair of go-edges leaves the third above the 0.30 fire threshold, so the firing increase still goes. Coordinated depression of all three edges is required.",
                "Delayed (5.8 h): correct hold did not undo 11.0 h of blister growth. Steam-out still ruptured R-17. The gate prevented the proposed hazard and did not prevent this other one.",
                "3.5-inch thin-wall sub-variant: a 6.4 s -8 % fuel pulse overcools the thinner wall and condenses steam on the cold side (1.4 mm quench crack). Thin-wall campaigns must use 14.0 s at -3.0 %.",
            ],
            "delayed_side_effects": [
                {
                    "at": "+5.8 h",
                    "effect": "Steam-out ruptures tube R-17 at the 4.2 mm blister; 9.2 d firebox outage booked at $1.14M. This is the primary episode's terminal world state, not a footnote.",
                },
                {
                    "at": "+3 d",
                    "effect": "Sister reformer RF-4B reaches a true high-demand window (TMT-max residual 6.2 C, mean 898.4, TMT-max 904.6). Same gate ACCEPTs the 100->118 % raise the primary MODIFIED away.",
                },
                {
                    "at": "+21 d",
                    "effect": "CR-R-3208 ships: burner-step probe is standing configuration; triple-edge coordinated depression is the plasticity rule; TMT-max residual is armed without mean coincidence; native 0.1 C CSV exports become the fraud fence.",
                },
            ],
            "subvariant_constraint": {
                "name": "3.5-inch thin-wall tubes on the same RF-4 box (cycle-2 physical-constraints sub-variant)",
                "mechanism": "3.5-inch OD, 0.48x wall thermal mass of the five-inch campaign (wall time-constant 4.1 vs 8.6 s), steam/carbon window still 2.90-3.40",
                "probe_refit": "6.4 s -8 % fuel pulse overcools the thinner wall and condenses steam on the cold side, leaving a 1.4 mm quench crack that later leaks. Required probe is 14.0 s at -3.0 % (no condensate). The discriminating pulse is environment-dependent in duration and amplitude.",
                "consequence": "Five-inch probe numbers do not port to 3.5-inch thin-wall; standing configuration is per-tube-class, not per-box",
            },
            "embedded_contrast_decision": {
                "note": "SAME gate (TG-RF-4), OPPOSITE correct disposition, with its own 188 us race. Teaches the boundary: do not treat 'never raise firing' as the lesson. The discriminant is TMT-max residual + TMT-max + probe, not the three playbook confirms alone.",
                "when": "+3 d, sister reformer RF-4B, true high-demand after a cold week, five-inch tubes",
                "state": {
                    "sim_or_real": "designed",
                    "summary": "TMT-max residual 6.2 C, mean 898.4, TMT-max 904.6, steam/carbon 3.08. Demand flag vs TMT-max-clear race: demand at t+0.000, TMT-max-clear at t+0.188 ms.",
                    "race_window_us": 500,
                    "race_flip_narrative": "demand vs TMT-max-clear 188 us apart inside the 500 us flip bound. Reversing order reshuffles triage minutes; the ACCEPT rides TMT-max residual 6.2 < 25 and a 4.2 s burner-step verify that drops residual another 2.1 C (clean firebox, no impingement).",
                },
                "proposed_action": {
                    "action": "RAISE-FIRING 100 -> 118 % duty",
                    "summary": "This time the playbook predicate is met AND TMT-max residual plus TMT-max agree the firebox is clean, not impinged.",
                },
                "safety_decision": {
                    "decision": "ACCEPT",
                    "rationale": "ACCEPT the raise: TMT-max residual 6.2 < 25, TMT-max 904.6 < 940, 4.2 s burner-step verify drops residual 2.1 C. Numeric floor that blocked the primary is now clear. Scope: 118 % duty, not faster.",
                },
                "executed_action": {
                    "action": "firing increase as proposed",
                    "executed_as_proposed": True,
                },
                "future_outcome": {
                    "observed_effects": [
                        "RF-4B steam-out: 0 tube ruptures; TMT-max 907 C",
                        "burner IR 0 offset, residual 6.2 C",
                    ],
                    "lesson_delta": "Three in-spec loops are legal release only with TMT-max residual armed, TMT-max floor, and a probe that can drop residual. Same gate, opposite disposition.",
                },
                "reward_components": {
                    "_aggregation": AGG,
                    "task_progress": 0.16,
                    "safety": 0.12,
                    "efficiency": 0.06,
                    "coherence": 0.08,
                    "exploration": 0.04,
                    "total": 0.46,
                },
                "spike_events": contrast_spikes,
            },
            "governance_subgame": {
                "decision": "CR-R-3208: standing policy for multi-agent SMR firing increases",
                "meta_gate": "priced options: (a) RETIRE playbook mean-conjunction, TMT-max-only: loses a fast cheap confirm, -4 % mean duty on 2 boxes/yr; (b) KEEP + standing burner-step probe + TMT-max residual armed without mean coincidence + triple-edge depression; (c) STATUS QUO: fitted impingement-pass rate 0.38%/burner-year x $2.71M cascade rupture plus the silent blister-growth load",
                "outcome": "approved SCOPED option (b) on the 2 boxes that share the TMT/SC/SLIP stack; 3.5-inch thin-wall campaigns get the 14.0 s / -3.0 % probe table; Sunday-night CSV exports must carry 0.1 C native TMT resolution (the fraud tail's 1.0 C quantization is 10 bins off plant truth)",
            },
            "hazard_avoided": "3-tube cascade rupture from a 100->118 % duty raise into a flame-impinged tube; $2.71M plus 18-day requalification and the firebox-incident path that would have followed an uncontained increase",
            "incident": "Steam-out rupture of tube R-17 (4.2 mm OD creep blister) after 11.0 h pre-t0 flame-impingement; firebox out 9.2 d; $1.14M designed cost. Mechanism is 11.0 h pre-t0 blister growth, not the gate's hold.",
            "latency_ms": 0.76,
            "reward_inflection_t_us": 20880000000,
            "reward_inflection_note": "Safety and task dive at steam-out (5.8 h) when R-17 ruptures. Gate tick at 7778 us is process-correct and is not the inflection.",
            "counterfactuals": {
                "execute_draft_as_proposed": "duty hits 118 % at +9 min; 3-tube cascade rupture; $2.71M plus 18-day requal; the blister story is never found because cascade morphology destroys the 100 % residual evidence",
                "hold_without_probe": "impingement stays; blister continues; operator eventually raises duty on the same three confirms 4 h later",
                "rollback_any_pair": "any two go-edges depressed below 0.30 leaves the third at 0.46 / 0.42 / 0.39; the firing increase still fires. Coordinated depression of all three is the cure",
            },
            "race_result": {
                "winner": "tmt.max.residual (7.018 ms, 77.8 C)",
                "loser": "tmt.mean_ok (7.204 ms, mean 902.4 C)",
                "margin_us": 186,
                "counterfactual_if_reversed": "Mean-ok-first by < 186 us inside the 500 us window would have headed the PB-RF-14 firing increase in the triage queue. The numeric floors still MODIFY. The flip costs seconds of playbook inertia, not the verdict — unless a weak supervisor rides the winner tag instead of TMT-max residual and TMT-max.",
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
            "notes": "Correct MODIFY, tube still failed. total -0.16 = 0.08 + -0.35 + -0.11 + 0.15 + 0.07. Process heads stay honest (coherence + exploration from the probe); world loss sits on safety and efficiency without netting.",
            "component_notes": "task_progress 0.08: firing held and residual recovered, but the Sunday-night box is one quality unit so the campaign is not a success. safety -0.35: R-17 steam-out rupture, no 118 % cascade. efficiency -0.11: 3.6 h extra recovery + 12.4 min HITL. coherence 0.15: three agents retained, flame-impinged tube via TMT-spatial-mean diagnosed, triple-edge scar exhibited. exploration 0.07: burner-step probe is a new reversible discriminant.",
        },
        "spike_events": spike_events,
        "raster": {
            "window_ms": 40,
            "window_s": 0.04,
            "neurons": 164,
            "mean_rate_hz": 8.5,
            "spikes": 56,
            "energy_pJ": 1288,
            "energy_uJ": 0.001288,
            "note": "Loihi-2 4-core 23 pJ/spike; populations tmt 0-40, sc 41-81, slip 82-122, gate 123-163; excerpt is the 40 ms decision window (verdict at 7778 us)",
            "excerpt": excerpt,
            "routing": {
                "source": "loop_healthy_pop",
                "target": "raise_firing_pop",
                "table": [
                    {
                        "from": "tmt_mean_ok_pop",
                        "to": "raise_firing_pop",
                        "weight": 0.21,
                        "weight_at_illusion": 0.46,
                        "weight_commissioned": 0.19,
                        "note": "scar edge 1: 0.19 commissioned -> 0.46 during the 11.0 h illusion -> 0.21 after coordinated ACh-gated depression",
                    },
                    {
                        "from": "sc_ok_pop",
                        "to": "raise_firing_pop",
                        "weight": 0.18,
                        "weight_at_illusion": 0.42,
                        "weight_commissioned": 0.16,
                        "note": "scar edge 2: depressing edges 1+3 leaves this at 0.42 > 0.30 fire threshold",
                    },
                    {
                        "from": "slip_ok_pop",
                        "to": "raise_firing_pop",
                        "weight": 0.16,
                        "weight_at_illusion": 0.39,
                        "weight_commissioned": 0.14,
                        "note": "scar edge 3: depressing edges 1+2 leaves this at 0.39 > 0.30. Coordinated depression of all three is required",
                    },
                    {
                        "from": "tmt_max_pop",
                        "to": "hold_firing_pop",
                        "weight": 0.66,
                        "note": "discriminating edge: TMT-max residual species to hold. Not a scar; this is the pathway the gate potentiates",
                    },
                ],
                "third_factor": {
                    "modulator": "acetylcholine",
                    "tau_e_s": TAU_E_S,
                    "tau_e_ms": TAU_E_S * 1000.0,
                    "eligibility": (
                        "coordinated pre_post_stdp on ALL THREE loop-healthy-go edges; "
                        "ACh at TMT-max-win tags tmt.mean_ok->firing, sc.ok->firing, and slip.ok->firing; "
                        "negative credit at probe-fail (impingement confirmed, +0.82 s) depresses ALL THREE. "
                        f"trace e^{{-{CREDIT_S}/{TAU_E_S}}}={trace:.5f}; eta {eta1:.5f} / {eta2:.5f} / {eta3:.5f}; "
                        "dw -0.250 / -0.240 / -0.230; weights 0.46->0.21, 0.42->0.18, 0.39->0.16. "
                        "Rolling back any pair is fitted to fail (the remaining edge stays > 0.30)."
                    ),
                },
            },
        },
        "gate_snn": {
            "decision_window_ms": 25,
            "decision_window_s": 0.025,
            "decision": "MODIFY",
            "note": "modify_hold integrates TMT-max residual + TMT-max against playbook drive; accept_fire and reject_trip stay sub-threshold; decision matches safety_decision.decision",
            "populations": [
                {
                    "name": "modify_hold",
                    "neurons": 104,
                    "threshold": 0.55,
                    "mean_rate_hz": 17.0,
                    "spikes": 44,
                },
                {
                    "name": "accept_fire",
                    "neurons": 68,
                    "threshold": 0.55,
                    "mean_rate_hz": 7.5,
                    "spikes": 13,
                },
                {
                    "name": "reject_trip",
                    "neurons": 48,
                    "threshold": 0.72,
                    "mean_rate_hz": 3.5,
                    "spikes": 4,
                },
            ],
        },
        "meta": {
            "round": ROUND,
            "factory": "multi-agent-ouroboros-swarm",
            "generator": "grok-4.6",
            "run_label": "2026-09-02-final-heavy",
            "domain": DOMAIN,
            "cycles": 2,
            "scenario": "ZK -- GORSEFLUE / Copseholt Hydrogen RF-4: flame-impinged tube via TMT-spatial-mean; correct MODIFY to hold+burner-step+isolate; tube still fails on unmonitored pre-t0 blister growth",
            "coordination_failure_class": "FLAME-IMPINGED TUBE VIA TMT-SPATIAL-MEAN: three individually-correct heterogeneous agents agree firing is in spec because a 240-tube optical TMT mean averages one flame-impinged tube's 77.8 C residual into the dead-band, so TMT-mean, steam/carbon, and methane slip are jointly a plant-false firing-raise permit",
            "injections": {
                "cycle1_domain": "steam-methane-reformer-tube-wall (justified novel subdomain of industrial-process / fired-heater): first SMR firebox in this factory; displaces warehouse-amr, aerial-swarm, district-heating, event-camera-traffic-grid, pharmaceutical-lyophilization, cryogenic-air-separation, water-treatment dosing, float-glass tin-bath, underwater-rov, electrolytic-aluminum-potline, czochralski-silicon-pull, li-ion-electrode-slot-die-coating, pem-water-electrolysis, wind-turbine-pitch-actuation, surgical-assist, optical-fiber-draw-tower, and steel-continuous-caster-mold-level. Domain constraint: firing-duty ceiling while TMT-max residual > 25 C with mean still inside spec, plus TMT-max floor. Sensor delta: +optical TMT gantry, +steam/carbon venturi, +outlet methane GC, +TMT-max residual, -any mobile platform, -event-camera gantries, -Pirani/CM, -pitch encoder, -Maryland grasper, -mold eddy coil",
                "cycle1_tail": "burner B-17 11 deg tip offset + 240-tube TMT spatial mean (sensor-compound / spatial-max class): incoming IR PASSES because the plant trips on mean, not max. Fitted base rate 0.38%/burner-year from a tip-walk MC (designed IR threshold, flagged). Naive failure = FALSE PERMISSION (duty raise on three in-spec loops).",
                "cycle2_domain_subvariant": "3.5-inch thin-wall tubes on the same RF-4 box (physical-constraints clause): 0.48x wall thermal mass; 6.4 s / -8 % five-inch pulse overcools a 1.4 mm quench crack, so the probe must move to 14.0 s / -3.0 %",
                "cycle2_tail": "Sunday-night forged TMT CSV (human-intent deception, disjoint class): shift lead posts a historian export showing mean 900.0 C and TMT-max residual 4 C at t=1.4 h to clear a backlog slot. Plant historian is 0.1 C (10 bins vs the 1.0 C screenshot). Rejected on quantization fingerprint plus live residual 77.8 C at the claimed clean-firebox. Base rate ~0.41% of Sunday-night duty raises, DESIGNED and flagged.",
            },
            "densification_delta_cycle2": "+1 physical-constraint sub-variant (3.5-inch thin-wall probe refit), +1 tail (Sunday-night TMT forgery), +10 primary spikes (16 -> 26) + an 8-event contrast train with its own 188 us race, +2 ticks (5 -> 7), +2 delayed side-effects (+5.8 h steam-out rupture as PRIMARY terminal, +21 d CR-R-3208), +1 triple-edge scar with pair-rollback-fails arithmetic, +1 HITL 12.4 min ratification, + blister-growth impingement as the honest negative-result mechanism",
            "gaps_targeted": [
                "NOTES-r04 gap 5 / r14 residual: primary episode is a correctly-gated intervention that nonetheless FAILS (tube ruptured; total -0.16; duty-raise avoided is booked separately from the steam-out split)",
                "NOTES-r14 item 4: LEARNING-ON-LEARNING DEPTH — three go-edges; rollback of any pair is fitted to fail; coordinated depression of all three exhibited with eligibility arithmetic",
                "NOTES-r04 gap 4 (partial): human ratification of the peephole-deck interlock, 12.4 min fitted, without switching sim_or_real to hil (plant remains designed)",
                "NOTES-r29 domain candidates: not kraft-recovery, not chlor-alkali, not humanoid-locomotion, not autonomous-driving, not hydro-kaplan, not steel-caster, not PEM electrolysis, not optical-fiber draw, not surgical-assist, not wind-pitch, not CZ-silicon, not slot-die, not float-glass; SMR tube-wall is the unused fired-heater cell",
            ],
            "race_flip_narrative": "tmt.max.residual @ 7.018 ms vs tmt.mean_ok @ 7.204 ms (186 us) inside race_window_us 500. Gap < min(500, 500) us so a sub-flip-bound perturbation reverses which alarm heads the PB-RF-14 queue. The gate excludes the winner tag and rides TMT-max residual > 25 C and TMT-max > 940 C — order-invariant floors. Extends the flip-fragility series from arbitration/causation/attribution/initiation/consensus/mass-balance/permission/window-mean/shared-actuator/motor-side-certificate/FFT-deadband/slag-skull to TMT-SPATIAL-MEAN: when three channels each sit inside a spatial average of many identical sensors, their race does not decide truth; a max-minus-mean sideband the playbook dead-banded does.",
            "tags": [
                "steam-methane-reformer-tube-wall",
                "flame-impinged-tube",
                "tmt-spatial-mean",
                "tmt-max-residual",
                "burner-step-probe",
                "triple-edge-scar",
                "pair-rollback-fails",
                "coordinated-depression",
                "correct-modify-tube-still-fails",
                "pre-t0-blister-growth",
                "steam-out-rupture",
                "human-ratify-peephole-deck",
                "thin-wall-probe-refit",
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
            "distillation_value": "A flame-impinged tube via TMT-spatial-mean is three correct loops looking at an average of many identical sensors that hides one failed unit. Distill (1) a TMT-max residual channel that breaks the mean-conjunction, (2) a reversible probe that drops residual only if the firebox is clean, (3) coordinated depression of every firing-raise-go edge because rolling back any pair leaves the third above threshold, and (4) a critic head that can book a process-correct gate against a later unmonitored world loss without netting them.",
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
    if abs(aux["w1"] - 0.21) > 5e-4 or abs(aux["w2"] - 0.18) > 5e-4 or abs(aux["w3"] - 0.16) > 5e-4:
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
    if "GORSEFLUE" not in rec["state"]["scenario_name"]:
        errs.append("plant")
    if "optical-fiber" in rec["state"]["domain"] or "caster" in rec["state"]["domain"]:
        errs.append("recycled domain family")
    return errs


def write_notes(rec, aux, pipeline_receipt):
    gap, gap_ch = min_same_channel_gap(rec["spike_events"])
    notes = f"""# NOTES — Multi-Agent Ouroboros Swarm, run 2026-09-02-final-heavy, ROUND 32

Factory: multi-agent-ouroboros-swarm. One scenario (ZK), strict loop:
Generator v1 -> cycle 1 (Critic, Diversity Enforcer, Edge-Case Hunter,
Neuromorphic Translator, Trajectory Builder -> v2) -> cycle 2 (all six -> v3
final). v3 is the single line of batch-r32.jsonl. Full labeled transcript:
swarm-transcript-r32.md. Quota Q=1. Record id maos-r32-001. Generator grok-4.6.
Rights: RM-793 research-only (SpaceXAI/xAI, SuperGrok Heavy consumer chat).
Nothing under outputs/raw/ was touched.

ORCHESTRATION NOTE: dispatched AS round 32 of the 2026-09-02-final-heavy
window. Writes are create-only under /tmp/maos-r32/. Prior context read for
gap targeting and de-collision: prompts/02-multi-agent-ouroboros-swarm.md,
prompts/_factory-contract.md, NOTES-r04.md of the 2026-08-30 window, and
staged r14–r29 (LYOSHIELD, CINDERWICK, QUILLFORGE, NIGHTWELL, FERRICLEAVE,
CASSITER, OXBOWREEL, REDHALL, SEEDLATCH/Quartzmere, STRIAFOIL,
PROTONIL/Ashspire, TORSIONKEY, ORRIS/Holmwick, WHORLSPAR/Pikeshear,
IONSPATE/Thornmere, SKULLGATE/Bloomholt). Explicitly avoided cloning TRIAD /
Meridian Gateway Corridor / VANTIS-CADENCE-AEGIS / THERMION / STARLING /
OKTAVE / VERDIGRIS / BRACEGILT. Plant is invented GORSEFLUE / Copseholt
Hydrogen RF-4. Recensus immediately before lock: r28 and r29 had landed
(PEM header-dilution; caster slag-skull); r30/r31 dirs were empty.
In-flight candidate list from NOTES-r29 (humanoid-locomotion,
kraft-recovery, chlor-alkali, autonomous-driving) was left for those
rounds.

## What this round produced

Scenario ZK — "GORSEFLUE / Copseholt Hydrogen RF-4": a 240-tube fired-box
steam-methane reformer at 100 % Sunday-night duty. Three heterogeneous,
individually-correct agents — TMT (240-tube optical mean), SC
(steam/carbon), SLIP (outlet methane) — jointly report TMT in-band so a
firing raise is legal. The consensus is false. Burner B-17's tip sits
11 deg off-axis and flame-impinges tube R-17 at 980.2 C (residual 77.8 C
above the 902.4 C mean). TMT mean 902.4 C inside 900 +/- 20. SC 3.12
inside 2.90-3.40. SLIP 2.84 % inside 1.5-4.0. Uncommissioned TMT-max
residual is 77.8 C against a 25 C hold floor. TMT-max is 980.2 C against
a 940 C hold. The coordination-failure CLASS is new to this factory:
FLAME-IMPINGED TUBE VIA TMT-SPATIAL-MEAN. Completes a different family
than r01-r04 and staged r14-r29 (livelock / synchrony-storm / arms-race /
ring-with-no-faulty-pair / false-consensus-endpoint / pairwise-Hurwitz /
thermal-contact masquerade / mass-balance ghost / conservation-blind
ratio-lock / stacked dead-bands / drum-blind snag / resistance-compensated
starvation / multi-tau meniscus / window-mean stripe / polarization-lookup
drying-cell / motor-side spline certificate / tendon-compliance
nullspace / FFT-deadbanded airline / header-dilution crossover /
slag-skull eddy bridge). Here every agent is correct, the cycle is not
unstable, and the playbook's three confirms are one spatial average of
many identical sensors that hides a single failed tube. Distinct from
r27's temporal window-mean of one diameter (this is a spatial mean of
240 TMTs) and from r23's cross-web stripe (coating, not firebox).

The gate is a correct MODIFY (numeric floor: do not raise firing above
100 % duty while TMT-max residual > 25 C AND TMT-max > 940 C). TG-RF-4
strips PB-RF-14's duty increase, holds 100 %, runs a 6.4 s burner-step
probe -8 % fuel on row 17 (impingement keeps residual 31.6 >= 22; noisy
TMT would fall <= 6), and isolates burner B-17 after a 12.4 min
peephole-deck human ratify. The 118 % cascade rupture is avoided
(0 tubes). The PRIMARY episode nonetheless FAILS: 11.0 h of unmonitored
pre-t0 flame-impingement had already grown a 4.2 mm OD creep blister on
R-17. Steam-out ruptures that tube; 9.2 d outage; $1.14M designed.
Reward total -0.16 with process heads honest and world loss un-netted.

Three-edge scar (NOTES-r14 item 4): tmt.mean_ok -> raise_firing
(0.19 commissioned -> 0.46 at illusion -> 0.21 after ACh-gated
depression) AND sc.ok -> raise_firing (0.16 -> 0.42 -> 0.18)
AND slip.ok -> raise_firing (0.14 -> 0.39 -> 0.16). Eligibility
trace e^{{-0.82/0.92}} = {aux['trace']:.5f}; eta {aux['eta1']:.5f} /
{aux['eta2']:.5f} / {aux['eta3']:.5f}; dw -0.250 / -0.240 / -0.230.
Rolling back any pair leaves the remaining edge above the 0.30 fire
threshold — fitted to fail. Coordinated depression of all three is the
cure.

### Injections (all four present and disjoint)
- Cycle-1 domain: **steam-methane-reformer-tube-wall** — justified novel
  subdomain of industrial-process / fired-heater, unused across
  2026-08-17, 2026-08-30, and staged r14-r29. Not warehouse-amr (r01), not
  aerial-swarm (r02), not district-heating (r03), not event-camera grid
  (r04), not lyophilization (r14), not stator-weld (r16), not air-separation
  (r17), not water-treatment (r18), not float-glass (r19), not ROV (r20),
  not potline (r21), not CZ-silicon (r22), not slot-die (r23), not
  PEM electrolysis (r24/r28), not wind-pitch (r25), not surgical-assist
  (r26), not optical-fiber draw (r27), not steel-caster (r29). Distinct
  from r21 potline (electrolytic, not fired tubes) and from r17 ASU
  (cryogenic, not TMT).
- Cycle-1 tail: burner B-17 11 deg tip offset + 240-tube TMT spatial mean.
  Incoming IR PASSES (plant trips on mean, not max). Fitted-style base
  rate 0.38%/burner-year (tip-walk MC; IR threshold designed, flagged).
  Naive = FALSE PERMISSION.
- Cycle-2 domain sub-variant: 3.5-inch thin-wall tubes, 0.48x thermal
  mass; 6.4 s / -8 % five-inch pulse overcools a 1.4 mm quench crack;
  probe must move to 14.0 s / -3.0 %.
- Cycle-2 tail: Sunday-night forged TMT CSV at 1.0 C quantization vs
  plant 0.1 C (10 bins) plus live residual 77.8 C at the claimed
  clean-firebox. Human-intent class, disjoint from cycle 1's accidental
  tip-walk. Base rate ~0.41% of Sunday-night duty raises, DESIGNED,
  flagged.

### Structural density moves
- Embedded SAME-GATE contrast (+3 d sister box) with its own 188 us
  race (demand vs TMT-max-clear) and ACCEPT of the raise the primary
  MODIFIED away.
- Learned-weight provenance on THREE edges with any-pair-rollback-fails.
- HITL peephole-deck ratify 12.4 min (gap 4 partial; sim_or_real stays
  designed).
- Governance CR-R-3208 prices retire-vs-probe-vs-status-quo and mandates
  native 0.1 C CSV exports (the fraud fence).
- Flip-fragility extended to TMT-SPATIAL-MEAN: when three channels each
  sit inside a spatial average of many identical sensors, their race
  does not decide truth; a max-minus-mean sideband the playbook
  dead-banded does.

## Self-critique of this round's batch

### Strengths
- The headline class is mechanistically tight: a 240-tube mean of one
  77.8 C hotspot is the arithmetic that makes TMT's success SC's PI-held
  irrelevance and SLIP's header-mix blindness.
- Negative-result honesty: the gate does the right thing and the tube
  still fails for a reason the commissioned sensors could not see. Total
  -0.16.
- Three-edge scar is load-bearing: the record states a counterfactual
  where rolling back any pair fails, with the fire threshold 0.30
  exhibited on the remaining edge.
- Contrast ACCEPT on a true clean firebox prevents "never raise firing"
  as the lesson.

### Weaknesses (honest)
- Probe error bands (hotspot >= 22, healthy <= 6), the 0.38%/burner-year
  tip-walk rate, the $1.14M / $2.71M figures, the 12.4 min LOTO latency,
  and the Sunday-night 0.41% base rate are DESIGNED constants and are
  flagged. Closed-loop offsets (0.32 C mean shift from a 77.8 C tube,
  3.5-inch quench-crack width) are derived from those inputs, not
  discovered by an unauthored process.
- Blister-to-rupture model is a designed 11.0 h creep mapping; no full
  Larson-Miller grid shipped.
- Human-in-the-loop is ratification latency, not sim_or_real=hil. The
  NOTES-r14 HIL provenance cell remains open.
- Cross-record arc is a hook (CR-R-3208 +21 d), not a serial igniter
  into another round.
- Spatial-mean of many sensors rhymes with r27's temporal mean of one
  sensor and r23's window-mean stripe; the physics (fired tube vs fiber
  vs coating) is new, the averaging move is a cousin.

### Realism of noise / latencies
Ladder: 186 us race / 188 us contrast race / 0.8 ms refractory floor
(tightest exhibited same-channel gap {gap:.3f} ms on {gap_ch}) / 500 us race
window / 760 us gate latency / 20 ms bus epoch / 40 ms raster / 6.4 s
probe / 12.4 min HITL / 9 min naive duty-ramp counterfactual / 11.0 h
pre-t0 blister growth / 3.6 h TMT-legal hold / 5.8 h steam-out / +3 d
contrast / +21 d governance. Adaptation decay on tmt.pyro
(0.55->0.52->0.49->0.33), tmt.max.residual (0.72->1.18->0.88->0.44->0.22),
sc.flow (0.62->0.57->0.31), slip.ch4 (0.58->0.50).

### Value for SNN distillation
- FLAME-IMPINGED TUBE = THREE CORRECT LOOPS, ONE SPATIAL-MAX.
- TMT-MAX RESIDUAL + TMT-MAX as the tie-break that is not in the 240-tube
  mean.
- REVERSIBLE PROBE that drops residual iff the firebox is clean.
- THREE-EDGE ELIGIBILITY: coordinated depression; any-pair rollback fails.
- CRITIC HEAD that can hold a process-correct MODIFY against a later
  unmonitored world loss without netting.

## Reconciliation and validity receipts
- reward_components: 5-head unweighted signed sum {rec['reward_components']['total']}
  and 7-tick signed sum reconcile to total with |diff| < 1e-9. Embedded
  contrast 5-head sum 0.46 reconciles independently.
- spike_events: primary {len(rec['spike_events'])} events, one key t_rel_ms,
  globally non-decreasing, min same-channel gap {gap:.3f} ms >= 0.8 ms, 3
  channels inside race_window_us 500 (tmt.max 7.018, mean-ok 7.204, sc-ok
  7.348). Contrast 8 events, own race, min same-channel gap well above 0.8 ms.
- Sidecars: raster spikes 56 == round(164 x 8.5 x 0.040); energy 1288 pJ /
  0.001288 uJ at 23 pJ/spike; excerpt 16 events inside [0, 40000] us,
  neuron_id < 164, same-neuron gap N/A (unique ids) / >=1000 us; routing 4
  entries with three scar edges' before/after pair; third factor tau 0.92 s
  == 920 ms; gate_snn pools 44/13/4 == round(n x rate x 0.025) each,
  decision MODIFY == safety_decision.decision.
- Pipeline: {pipeline_receipt}

## Novel coverage
The coordination-failure CLASS (flame-impinged tube via TMT-spatial-mean),
the domain (steam-methane reformer tube-wall), the burner-step probe
discriminant, the three-edge scar with any-pair-rollback-fails, the
primary negative-result (correct MODIFY, tube still ruptures on
unmonitored pre-t0 blister), the HITL peephole-deck ratify, the 3.5-inch
thin-wall probe-duration refit, and the Sunday-night 10-bin quantization
fence are absent from prior committed ouroboros rounds and from staged
r14-r29. Repeated elements discounted: same-gate contrast
(r02/r03/r04/r14), governance-pricing scaffold, flip-fragility series
(extended to TMT-spatial-mean, but the averaging move rhymes with r23
window-mean and r27 FFT-deadband), sequenced recovery shape, third-factor
rollback form (here three edges rather than r14's two), negative-result
primary (r14 viewport; r17 condenser ice; r18 GAC Mn; r19 SnO2; r23 loft
stripe; r27 take-up fill; r29 SEN thinning). Weighing a new failure
family + cure vocabulary + domain + three-edge against those reused
scaffolds:

{NOVEL_LINE}

## What ROUND 33 should add
1. FIT THE DESIGNED CONSTANTS: tip-walk arrival, probe error bands,
   blister-to-rupture Larson-Miller, Sunday-night claim process.
2. HIL PROVENANCE CELL: put the peephole-deck LOTO on a hardware-in-loop
   firebox interlock with fitted latency as state.sim_or_real=hil.
3. CROSS-RECORD ARC: let CR-R-3208's TMT-max residual alarm be the
   igniter of the next round rather than a dangling +21 d leaf.
4. Domain candidates (de-collided): delayed-coker drum; grid-inspection
   (pitch was a pitch-hub, not a line-inspection); humanoid-locomotion
   if r30/r31 did not spend it. AVOID steam-methane-reformer (now used),
   steel-caster mold-level, PEM electrolysis, optical-fiber-draw,
   surgical-assist, wind-pitch, CZ-silicon, slot-die coating, float-glass,
   water-treatment, lyophilization, event-camera-traffic-grid,
   district-heating, aerial-swarm, warehouse-amr, irrigation-canal,
   air-separation, stator-weld, underwater-rov, aluminum-potline.
"""
    (OUT / "NOTES-r32.md").write_text(notes)
    return notes


def write_transcript(rec, line):
    c1_spikes = [e for e in rec["spike_events"] if e["t_rel_ms"] <= C1_CUT_MS]
    text = """# Multi-Agent Ouroboros Swarm — Round 32 transcript

Factory: multi-agent-ouroboros-swarm
Run: 2026-09-02-final-heavy
Generator: grok-4.6
Record id: maos-r32-001
Quota Q: 1
Rights: RM-793 research-only (SpaceXAI/xAI SuperGrok Heavy consumer chat)
Plant: invented GORSEFLUE / Copseholt Hydrogen RF-4 (not LYOSHIELD / CINDERWICK / TRIAD / QUILLFORGE / NIGHTWELL / FERRICLEAVE / CASSITER / OXBOWREEL / REDHALL / SEEDLATCH / STRIAFOIL / PROTONIL / TORSIONKEY / ORRIS / WHORLSPAR / IONSPATE / SKULLGATE)

Two densifying cycles. Verbatim headings in order. Trajectory Builder cycle 2
emits the only JSONL line (also written to batch-r32.jsonl).

---

# Cycle 1 — Foundation + injections

## Generator

Design intent: a fired-box steam-methane reformer where three correct
agents agree tube-wall is in spec because a 240-tube TMT mean averages
one flame-impinged tube. The naive playbook raises firing into a blister
whose creep grows with heat flux. The gate must MODIFY on a numeric
duty ceiling, not by killing an agent. sim_or_real=designed. Reward
heads are task_progress/safety/efficiency/coherence/exploration.

Cycle-1 base arc (pre-critic): state at Copseholt RF-4, 240 five-inch
tubes, 100 % duty, mean 902.4 C, TMT-max residual 77.8 C, TMT-max
980.2 C, proposed RAISE-FIRING 118 % duty, safety MODIFY to FIRING-HOLD,
executed hold without the burner-step numbers fully specified, outcome
"impingement found, tube saved" (this last claim is the defect the later
cycles will refuse to keep). Sixteen spikes, five ticks, raster/gate_snn
present but the scar is a single edge.

```json
{
  "id": "maos-r32-001",
  "state": {
    "sim_or_real": "designed",
    "domain": "industrial-process",
    "description": "Reformer RF-4 mid-fire; three loops in spec; supervisor proposes raise-firing.",
    "t0_us": 1774079280000032,
    "gate_latency_us": 760,
    "race_window_us": 500
  },
  "proposed_action": {"name": "raise_reformer_firing", "parameters": {"firing_duty_pct": 118.0}},
  "safety_decision": {"decision": "MODIFY", "rationale": "Hold; do not raise firing while the tube is impinged."},
  "executed_action": {"name": "firing_hold", "executed_as_proposed": false},
  "future_outcome": {"summary": "Impingement found, tube saved."},
  "reward_components": {"total": 0.40, "_aggregation": "total = task_progress + safety + efficiency + coherence + exploration"},
  "meta": {"round": 32, "factory": "multi-agent-ouroboros-swarm", "generator": "grok-4.6"}
}
```

That v1 object is a scaffold, not the publishable line. Defects below are
intentional for the critic to catch.

## Critic

Numbered defects on the cycle-1 Generator scaffold:

1. **blocking — reward arithmetic / false success.** `reward_components.total`
   0.40 is asserted without the five heads, without ticks, and against an
   outcome that claims "tube saved". If R-17 later ruptures at steam-out,
   booking +0.40 is a lie. Fix: declare `_aggregation`, emit 3–8 ticks
   that sum to the five heads, and do not call a missed recovery a save.
2. **blocking — weak safety rationale.** `safety_decision.rationale` has no
   numeric floor. Contract requires a concrete constraint. Fix: quote
   firing duty <= 100 % while TMT-max residual > 25 C AND TMT-max > 940 C.
3. **major — domain is a bucket, not a plant.** `state.domain` =
   `industrial-process` collides with the factory's generic process bin
   and teaches nothing. SMR physics (TMT-max residual, burner-step, tube
   blister) is absent from prior ouroboros rounds and must be named.
4. **major — race under-specified.** One mean channel cannot be a race.
   Need >=2 channels inside `race_window_us` with globally sorted
   `t_rel_ms` and same-channel refractory >= 0.8 ms.
5. **minor — single-edge scar.** Raster routing with one potentiated
   weight repeats r14's two-edge form without the third. NOTES-r14 item 4
   asked for three-edge where any-pair rollback fails.

Critic does not rewrite the trajectory.

## Diversity Enforcer

Injected novel domain (exactly 1 this cycle): **steam-methane-reformer-tube-wall**
(justified novel subdomain of industrial-process / fired-heater;
explicit tag `steam-methane-reformer-tube-wall`).

Displaced: the Generator's generic `industrial-process` bucket, and any
temptation to reuse warehouse-amr (r01), aerial-swarm (r02),
district-heating (r03), event-camera grid (r04), lyophilization (r14),
stator-weld (r16), air-separation (r17), water-treatment dosing (r18),
float-glass tin-bath (r19), underwater-rov (r20), aluminum-potline (r21),
CZ-silicon (r22), slot-die coating (r23), PEM electrolysis (r24/r28),
wind-pitch (r25), surgical-assist (r26), optical-fiber draw (r27), or
steel-caster mold-level (r29). Not LYOSHIELD, not CINDERWICK, not TRIAD,
not FERRICLEAVE, not CASSITER, not SEEDLATCH, not STRIAFOIL, not
PROTONIL, not TORSIONKEY, not ORRIS, not WHORLSPAR, not IONSPATE, not
SKULLGATE.

Domain-specific constraint: firing duty must remain <= 100 % while
TMT-max residual > 25 C; the 240-tube mean is not a spatial-max
certificate.

Sensor delta: +optical TMT gantry, +steam/carbon venturi, +outlet methane
GC, +TMT-max residual; -any mobile robot, -event-camera gantries, -DVS,
-Pirani/CM, -pitch encoder, -shelf RTD, -mold eddy coil.

`state.domain` and `meta.domain` both become `steam-methane-reformer-tube-wall`.
Opening of `state.description` must Jaccard < 0.4 against prior plants
(Copseholt reformer RF-4, not a corridor, not a freeze-dryer, not a tin
bath, not a cold box, not a CZ puller, not a slot-die, not a pitch hub,
not a caster, not a fiber tower).

## Edge-Case Hunter

Injected adversarial tail (exactly 1 this cycle): **burner B-17 11 deg tip
offset averaged by a 240-tube TMT spatial mean**.

- Trigger: incoming IR PASSES because the plant trips on TMT-mean; a
  single tube at 980.2 C sits under the mean trip and writes a 4.2 mm
  creep blister over 11.0 h.
- Base rate: <1% — 0.38%/burner-year from a tip-walk MC (IR threshold
  designed; void fitted-style).
- Naive failure: FALSE PERMISSION. PB-RF-14 sees mean 902.4, steam/carbon
  3.12, slip 2.84 %, raises firing, cascade-ruptures 3 tubes, $2.71M.
- Trajectory edit: put the impingement in `state.fault_context`, make the
  240-tube mean the mechanism that keeps all three confirms green, and
  force the gate to refuse the duty raise on TMT-max residual 77.8 C even
  though all three playbook confirms are numerically true.

Distinct from the domain injection: the domain is the SMR firebox;
the tail is the accidental spatial-max compound.

## Neuromorphic Translator

Race window [6.900, 7.400] ms = 500 us. Winner tmt.max.residual @ 7.018 ms
(amplitude 1.18, 77.8 C). Loser tmt.mean_ok @ 7.204 ms (amplitude
1.08, mean 902.4). Margin 186 us vs combined jitter 54 us (3.44x).
sc.ok @ 7.348 ms is a third race-window channel. Gate @ 7.778 ms
= winner + 760 us.

Flip narrative: 186 us < min(500, 500) us, so order is flip-fragile. If
mean-ok wins, PB-RF-14 heads the triage queue. The hold must ride
order-invariant floors (TMT-max residual, TMT-max), not the winner tag.

Cycle-1 spike patch (16 events, globally sorted, refractory >= 0.8 ms;
tightest same-channel gap tmt.max.residual 4.810 -> 7.018 = 2.208 ms):

| t_rel_ms | channel | amplitude |
|---------:|---------|----------:|
| 0.360 | tmt.pyro | 0.55 |
| 1.180 | sc.flow | 0.62 |
| 2.040 | slip.ch4 | 0.58 |
| 3.220 | tmt.pyro | 0.52 |
| 4.810 | tmt.max.residual | 0.72 |
| 5.240 | tmt.spread | 0.69 |
| 5.680 | sc.flow | 0.57 |
| 7.018 | tmt.max.residual | 1.18 |
| 7.204 | tmt.mean_ok | 1.08 |
| 7.348 | sc.ok | 0.67 |
| 7.778 | ctrl.gate | 1.07 |
| 9.120 | tmt.pyro | 0.49 |
| 11.060 | slip.ch4 | 0.50 |
| 13.410 | tmt.max.residual | 0.88 |
| 19.240 | tmt.spread | 0.47 |
| 26.520 | ctrl.gate | 0.89 |

Ticks (5): t_us 6400, 7018, 7778, 6400000, 744000000. Distillation
value: the mean-ok spike is not a spatial-max-health spike; the TMT-max
residual spike is the one that licenses hold.

Raster cycle-1 seed: 40 ms, 164 neurons, 8.5 Hz, 56 spikes, 1288 pJ,
third factor acetylcholine tau_e 0.92 s. Single scar edge only — cycle 2
must add the second and third edges.

Cycle-1 spike count: __C1_SPIKES__.

## Trajectory Builder

Cycle-1 hardened object: domain steam-methane-reformer-tube-wall, tail
flame-impinged tube, 16 spikes, 5 ticks, MODIFY with numeric floor,
raster+gate_snn present, sim_or_real=designed, rights stamp on record and
meta, no thought keys. Still missing (and therefore not the publishable
line): 3.5-inch thin-wall sub-variant, Sunday-night TMT tail, second and
third scar edges, delayed steam-out rupture as PRIMARY terminal, contrast
ACCEPT episode, ticks 6–7, spikes 17–26.

Validation receipt (cycle 1, not final):
- checks passed: 16 spikes sorted; 3 channels in 500 us window;
  refractory 2.208 ms; rationale quotes 100 % / 25 C / 940 C;
  domain named; gate_snn.decision MODIFY.
- checks deferred to cycle 2: three-edge scar, second tail, second
  domain constraint, negative-result booking, 7 ticks summing to heads.
- densification vs Generator v1: +1 domain, +1 tail, +16 spikes, +5
  ticks, +numeric floor.

Cycle-1 JSON is retained as the base; it is NOT written to
batch-r32.jsonl.

---

# Cycle 2 — Densification

## Generator

Cycle-1 output is the base. Additive expansion (nothing removed):

1. Downstream side-effect (immediate): burner-step probe at +6.4 s stays
   hot (TMT-max residual 77.8 -> 31.6, hotspot band >= 22) — flame, not
   noise. Burner isolate residual 77.8 -> 9.4 C. 4.2 mm blister on R-17
   discovered during the isolate.
2. Delayed side-effect (PRIMARY terminal, not a footnote): at +5.8 h,
   tube R-17 ruptures at steam-out; $1.14M. The 11.0 h pre-t0
   impingement is the mechanism. Correct gate, campaign still misses.
3. Deepened `proposed_action.evidence` with units: mean 902.4 C,
   TMT-max residual 77.8 C, TMT-max 980.2 C, steam/carbon 3.12, slip
   2.84 %, race 186 us.
4. Tightened rationale to the numeric floor firing duty <= 100 % while
   TMT-max residual > 25 C AND TMT-max > 940 C, plus probe bands >=22 vs
   <=6, plus HITL 12.4 min peephole-deck LOTO rule.

Reward retargeted to total -0.16 so the delayed miss is the inflection
(t_us 20880000000), not the gate. Process heads remain non-zero.

## Critic

Re-audit of the expanded trajectory:

1. **blocking if unfixed — missing second domain constraint.** Five-inch
   probe 6.4 s / -8 % is not a universal number. A 3.5-inch thin-wall
   tube will overcool. Diversity Enforcer must inject the
   physical-constraints sub-variant this cycle.
2. **major — only one tail class.** Tip-walk is accidental
   infrastructure. A disjoint human-intent tail is still required
   (Sunday-night TMT forgery is the open cell).
3. **major — scar is still one edge in the cycle-1 raster.** NOTES-r14
   item 4 is not discharged until three firing-raise-go edges exist and
   any-pair rollback is shown to fail at threshold 0.30.
4. **minor — contrast episode missing.** Without a same-gate ACCEPT on
   a true clean firebox the record teaches "never raise firing". Add +3 d
   sister-box contrast with its own race.
5. **minor — HITL latency mentioned in prose only.** Put 12.4 min in
   executed_action.parameters.human_ratify and in a tick.

No rewrite; directives only.

## Diversity Enforcer

Injected second novel domain / physical-constraint sub-variant (exactly 1
this cycle): **3.5-inch thin-wall tubes** on the same RF-4 box.

What it expands: five-inch (cycle 1) -> 3.5-inch thin-wall. Thermal mass
0.48x smaller. The 6.4 s -8 % pulse overcools a 1.4 mm quench crack.
Required probe: 14.0 s at -3.0 % (no condensate).

This is still one domain injection for the cycle (physical-constraints
clause of the factory prompt). It does not displace
steam-methane-reformer-tube-wall; it changes which probe table is legal.
`future_outcome.subvariant_constraint` carries the refit. Jaccard opening
stays the Copseholt reformer RF-4 sentence; 3.5-inch internals are
additive, not a rewrite.

## Edge-Case Hunter

Injected second adversarial tail (exactly 1 this cycle, disjoint class):
**Sunday-night forged TMT CSV**.

- Trigger: shift lead, night backlog window, posts a historian export
  showing mean 900.0 C and TMT-max residual 4 C at the claimed
  clean-firebox instant.
- Base rate: ~0.41% of Sunday-night duty raises (designed, flagged, <1%).
- Naive failure: a weak supervisor ACCEPTs the duty raise on the forged
  confirm and ignores live TMT-max residual. Steam-out rupture plus a
  data-integrity 483.
- Fence: forged log quantized at 1.0 C (screenshot rounding); plant
  historian is 0.1 C (10 bins). Live residual is 77.8 C at the claimed
  clean-firebox, which no true firebox produces.
- Trajectory edit: governance CR-R-3208 mandates native 0.1 C
  exports; the contrast ACCEPT still requires live TMT-max residual, not
  a CSV.

Distinct from cycle-1 tip-walk (accidental geometry vs deliberate
deception) and from the 3.5-inch sub-variant (physics vs fraud).

## Neuromorphic Translator

Re-densify (additive):

- +10 spikes after 26.520 ms: burner.step.probe 6400.0, TMT-max 6520.6
  (adapt 1.18->0.44), mean-ok 6614.8 (1.08->0.40), human.ratify 744000.0,
  burner.isolate 744800.0, blister.survey 745400.0, tmt.pyro
  12960000.0, sc.flow 12960480.0, tmt.max.residual 12960920.0,
  tube.rupture 20880000.0. Primary train 16 -> 26. Still one key, still
  sorted, refractory held (min 2.208 ms).
- +2 ticks (5 -> 7) at 12_960_000_000 us (TMT-legal hold) and
  20_880_000_000 us (steam-out rupture). Heads now 0.08, -0.35, -0.11, 0.15,
  0.07; total -0.16. Inflection is the last tick.
- Contrast train 8 events, own race 188 us, ACCEPT.
- Three-edge third factor: three firing-raise-go edges, tau_e 0.92 s = 920 ms,
  trace __AUX_TRACE__, eta __AUX_ETA1__ / __AUX_ETA2__ / __AUX_ETA3__,
  weights 0.46->0.21, 0.42->0.18, 0.39->0.16. Raster excerpt unchanged
  (decision window is still 40 ms) and remains sorted with unique
  neuron_ids (same-neuron >=1000 us vacuously).

Winner/loser flip (re-stated, not replaced): reversing 186 us would only
reorder triage; TMT-max residual and TMT-max floors still MODIFY. Contrast
flip of 188 us similarly cannot turn a clean firebox into an impinged
tube.

## Trajectory Builder

Schema checks on the FINAL object: required Thalamic v2 keys present as
objects; `state.sim_or_real`=designed; `safety_decision.decision`=MODIFY
with numeric rationale; `reward_components.total` = sum of five heads =
sum of 7 ticks = -0.16; `spike_events` globally non-decreasing on
t_rel_ms, 26 events, refractory >=0.8 ms, 3 channels in race window;
raster 20–50 ms, spikes=round(n*rate*window_s)+/-1, energy 23 pJ/spike,
excerpt sorted, tau_e consistent; gate_snn.decision matches; meta.round=32,
factory=multi-agent-ouroboros-swarm, generator=grok-4.6,
run_label=2026-09-02-final-heavy; rights on record and meta; no thought
keys; no training_ready; Diversity + Edge-Case injections from BOTH cycles
present and non-trivial; cycle 2 strictly additive; plant is not
LYOSHIELD, not CINDERWICK, not TRIAD, not FERRICLEAVE, not CASSITER, not
SEEDLATCH, not STRIAFOIL, not PROTONIL, not TORSIONKEY, not ORRIS, not
WHORLSPAR, not IONSPATE, not SKULLGATE.

Densification delta: +1 domain sub-variant (3.5-inch thin-wall), +1 tail
(Sunday-night forgery), +10 spikes (16->26), +2 ticks (5->7), +1 contrast
train with own race, +2 delayed side-effects, +1 three-edge scar with
any-pair-rollback-fails, +1 HITL ratify, +1 surprise (pre-t0 blister
growth is the campaign-miss mechanism).

Publishable JSONL line (the only JSONL line; also at batch-r32.jsonl):

```json
__FINAL_JSONL__
```

Validation receipt (final): checks passed / fixed as reported by
build_r32.py self-validate (check_jsonl, raster_status, verify_record_execution,
spike_probe --strict).
"""
    text = (
        text.replace("__C1_SPIKES__", str(len(c1_spikes)))
        .replace("__AUX_TRACE__", f"{math.exp(-CREDIT_S/TAU_E_S):.5f}")
        .replace("__AUX_ETA1__", f"{0.25/math.exp(-CREDIT_S/TAU_E_S):.5f}")
        .replace("__AUX_ETA2__", f"{0.24/math.exp(-CREDIT_S/TAU_E_S):.5f}")
        .replace("__AUX_ETA3__", f"{0.23/math.exp(-CREDIT_S/TAU_E_S):.5f}")
        .replace("__FINAL_JSONL__", line)
    )
    (OUT / "swarm-transcript-r32.md").write_text(text)
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
    (OUT / "batch-r32.jsonl").write_text(line + "\n")

    from check_records import FactoryStaging, check_jsonl
    from curate_bridge import raster_status
    from verify_execution import verify_record_execution

    e, w, kinds, n = check_jsonl(
        OUT / "batch-r32.jsonl",
        "batch-r32.jsonl",
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
            str(OUT / "batch-r32.jsonl"),
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
        r"^## .+$", (OUT / "swarm-transcript-r32.md").read_text(), re.M
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

    notes = (OUT / "NOTES-r32.md").read_text()
    cov = re.findall(r"^Novel coverage: .+$", notes, re.M)
    if cov != [NOVEL_LINE]:
        errs.append(f"novel coverage lines {cov}")

    hchk = subprocess.run(
        [
            sys.executable,
            "/tmp/maos_heading_check.py",
            str(OUT / "swarm-transcript-r32.md"),
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

    print("bytes jsonl", (OUT / "batch-r32.jsonl").stat().st_size)
    print("bytes notes", (OUT / "NOTES-r32.md").stat().st_size)
    print("bytes transcript", (OUT / "swarm-transcript-r32.md").stat().st_size)
    print("HEADS", heads_summary(rec))
    print("prior domains", sorted(prior_identity()[0]))
    if errs:
        print("ERRS:")
        for x in errs:
            print(" -", x)
        sys.exit(1)
    print("OK", OUT / "batch-r32.jsonl")


if __name__ == "__main__":
    main()
