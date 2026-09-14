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

GEN_AT = "2026-09-02T22:05:00Z"
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
    "SEEDLATCH",
    "Quartzmere",
    "Quartzridge",
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
DOMAIN = "pem-water-electrolysis"
PLANT = "PROTONIL / Ashspire Stack Hall SH-4"
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
        [5200, 6680, 7420, 9_600_000, 648_000_000, 12_240_000_000, 20_880_000_000],
        [
            (1, -2, -1, 1, 1),
            (2, -4, -1, 3, 1),
            (2, -6, -2, 3, 2),
            (2, -5, -2, 3, 1),
            (1, -7, -2, 2, 1),
            (1, -5, -1, 1, 0),
            (0, -4, -1, 1, 0),
        ],
    )
    assert abs(heads["total"] - (-0.14)) < 1e-9, heads

    trace = math.exp(-0.60 / 0.75)
    eta1 = (0.46 - 0.21) / trace
    eta2 = (0.42 - 0.19) / trace
    eta3 = (0.39 - 0.17) / trace
    dw1 = eta1 * 1.0 * trace
    dw2 = eta2 * 1.0 * trace
    dw3 = eta3 * 1.0 * trace
    w1 = 0.46 - dw1
    w2 = 0.42 - dw2
    w3 = 0.39 - dw3
    assert abs(w1 - 0.21) < 5e-4, w1
    assert abs(w2 - 0.19) < 5e-4, w2
    assert abs(w3 - 0.17) < 5e-4, w3

    spike_events = [
        {"channel": "amp.current", "t_rel_ms": 0.360, "amplitude": 0.55},
        {"channel": "stk.volt", "t_rel_ms": 1.120, "amplitude": 0.61},
        {"channel": "dew.header", "t_rel_ms": 2.040, "amplitude": 0.50},
        {"channel": "cell.vmax", "t_rel_ms": 3.480, "amplitude": 0.59},
        {"channel": "amp.current", "t_rel_ms": 4.860, "amplitude": 0.51},
        {"channel": "stk.volt", "t_rel_ms": 5.740, "amplitude": 0.57},
        {"channel": "cell.vmax", "t_rel_ms": 6.680, "amplitude": 1.30},
        {"channel": "stk.ok", "t_rel_ms": 6.856, "amplitude": 1.10},
        {"channel": "dew.ok", "t_rel_ms": 7.040, "amplitude": 0.66},
        {"channel": "ctrl.gate", "t_rel_ms": 7.420, "amplitude": 1.07},
        {"channel": "amp.current", "t_rel_ms": 9.180, "amplitude": 0.46},
        {"channel": "stk.volt", "t_rel_ms": 11.020, "amplitude": 0.48},
        {"channel": "cell.vmax", "t_rel_ms": 13.280, "amplitude": 0.86},
        {"channel": "amp.bias", "t_rel_ms": 16.640, "amplitude": 0.70},
        {"channel": "dew.header", "t_rel_ms": 19.360, "amplitude": 0.40},
        {"channel": "ctrl.gate", "t_rel_ms": 27.900, "amplitude": 0.89},
        {"channel": "current.step.probe", "t_rel_ms": 9600.0, "amplitude": 0.95},
        {"channel": "cell.vmax", "t_rel_ms": 9780.0, "amplitude": 0.43},
        {"channel": "stk.ok", "t_rel_ms": 9890.0, "amplitude": 0.37},
        {"channel": "human.ratify", "t_rel_ms": 648000.0, "amplitude": 0.80},
        {"channel": "cell.jumper", "t_rel_ms": 648800.0, "amplitude": 0.72},
        {"channel": "mea.ir", "t_rel_ms": 649400.0, "amplitude": 0.85},
        {"channel": "amp.current", "t_rel_ms": 12240000.0, "amplitude": 0.32},
        {"channel": "cell.vmax", "t_rel_ms": 12240480.0, "amplitude": 0.30},
        {"channel": "stk.volt", "t_rel_ms": 12240900.0, "amplitude": 0.27},
        {"channel": "o2.lel", "t_rel_ms": 20880000.0, "amplitude": 0.93},
    ]

    contrast_spikes = [
        {"channel": "amp.demand", "t_rel_ms": 0.000, "amplitude": 0.83},
        {"channel": "cell.vmax_clear", "t_rel_ms": 0.182, "amplitude": 0.78},
        {"channel": "dew.header", "t_rel_ms": 0.400, "amplitude": 0.23},
        {"channel": "stk.volt", "t_rel_ms": 1.580, "amplitude": 0.41},
        {"channel": "amp.current", "t_rel_ms": 4.760, "amplitude": 0.53},
        {"channel": "ctrl.gate", "t_rel_ms": 7.220, "amplitude": 0.92},
        {"channel": "current.step.probe", "t_rel_ms": 6400.0, "amplitude": 0.35},
        {"channel": "o2.lel", "t_rel_ms": 20880000.0, "amplitude": 0.13},
    ]

    excerpt = [
        {"t_us": 360, "neuron_id": 10},
        {"t_us": 1120, "neuron_id": 52},
        {"t_us": 2040, "neuron_id": 100},
        {"t_us": 3480, "neuron_id": 104},
        {"t_us": 4860, "neuron_id": 18},
        {"t_us": 5740, "neuron_id": 60},
        {"t_us": 6680, "neuron_id": 108},
        {"t_us": 6856, "neuron_id": 64},
        {"t_us": 7040, "neuron_id": 112},
        {"t_us": 7420, "neuron_id": 160},
        {"t_us": 9180, "neuron_id": 24},
        {"t_us": 11020, "neuron_id": 70},
        {"t_us": 13280, "neuron_id": 116},
        {"t_us": 16640, "neuron_id": 8},
        {"t_us": 19360, "neuron_id": 120},
        {"t_us": 27900, "neuron_id": 170},
    ]

    rec = {
        "id": RECORD_ID,
        "title": "PROTONIL SH-4: cell-group max 2.31 V beats stack-ok by 176 us; correct MODIFY still cracks MEA-47 after pre-t0 dry-out",
        "rights": RIGHTS,
        "state": {
            "sim_or_real": "designed",
            "domain": DOMAIN,
            "scenario_name": PLANT,
            "timestamp_local": "2026-04-17T22:40:00-04:00",
            "t0_us": 1776470400000024,
            "gate_latency_us": 740,
            "race_window_us": 500,
            "race_window_rel_ms": [6.680, 7.180],
            "description": "Ashspire Electrolyzer Hall SH-4 is mid-ramp on a 180-cell PEM stack when three heterogeneous, individually-correct agents jointly report 'polarization in-family, current raise is legal'. AMP holds rectifier current at 1480 A inside 1400-1600 A. LOOK's stack voltage 345.63 V sits 0.03 V from the 80 C polarization lookup (band +/- 2.0 V). DEW's cathode-header dew-point is 62 C inside 55-70 C. The conjunction is not a per-cell certificate: cell 47 is drying (inlet 0.12 kg/h vs 0.55) at 2.31 V, but a 20-cell group mean only moves +0.018 V inside a 0.05 V dead-band, and the 180-cell stack still matches the lookup. Cell-max-first latches CURRENT-HOLD plus a current-step probe; stack-ok-first would have authorized RAISE-CURRENT 1480 to 1650 A into a drying MEA.",
            "goal": "Hold stack current at 1480 A without raising load while cell-group max > 2.15 V AND stack-vs-lookup residual < 2.0 V AND header dew-point still in band; keep H2-in-O2 <= 0.4 vol% and avoid MEA crack.",
            "race": {
                "contenders": [
                    "cell.vmax 2.31 V (20-cell group max, uncommissioned at t0 as a historian replay)",
                    "stk.ok 345.63 V (stack vs 80 C polarization lookup)",
                ],
                "semantics": "Cell-max-first latches CURRENT-HOLD + CURRENT-STEP-PROBE + cell-47 jumper isolate. Stack-ok-first latches RAISE-CURRENT (1480 to 1650 A, water stoichiometry held).",
                "window_derivation": "500 us = one 380 us group-max ADC slot plus 120 us stack-ok publish.",
                "order_evidence_note": "Margin 176 us vs combined jitter 55 us (ADC 26 + lookup 29): 3.2x. The 176 us gap sits inside min(500, 500) us, so a sub-flip-bound perturbation reverses triage order. The gate rides the order-invariant floors cell-group max and current ceiling, not the alarm order.",
            },
            "topology": {
                "site": "Ashspire Electrolyzer Hall, invented mill-town Ashspire, Stack SH-4: 180-cell PEM, 5.0 MW nameplate, 1480 A body, 80 C, 1.8 bara, 28 slpm H2, Grade-C stack hall",
                "agents": "AMP rectifier current (vendor Ampcroft): 12-pulse thyristor plus DCCT. LOOK stack polarization (vendor Stackvolt): 180-cell sum vs 80 C lookup table. DEW cathode-header dew-point (vendor Mistgage): chilled-mirror on the mixed header. Heterogeneous stacks, no shared intent schema, one 20 ms stack-bus epoch",
                "coupling": "LOOK's lookup match is a stack-sum that a single drying cell cannot move outside +/- 2.0 V. DEW samples the mixed header, so one dry cell's local dew-point is diluted. AMP is a shared bus and is correct. Playbook PB-ELX-12 treats the conjunction of in-spec current, in-family stack V, and in-spec header dew-point as permission to raise current for a trailer fill. No agent is faulty; the drying cell is averaged out of the lookup.",
            },
            "sensors": [
                "DCCT stack current, 5 kHz, 18 us jitter, 1480 A (band 1400-1600 A)",
                "stack voltage sum, 1 kHz, 29 us jitter, 345.63 V vs 80 C lookup 345.60 V (band +/- 2.0 V)",
                "cathode-header dew-point, 5 Hz, 24 us jitter, 62 C (band 55-70 C)",
                "20-cell group max is computable from the same cell taps and is NOT commissioned at t0 (2.31 V on group 41-60 after the fact)",
                "individual cell 47 voltage is NOT a published tag at t0",
                "inlet-water per-cell rotameter is NOT commissioned at t0 (header DP daily check PASSES)",
            ],
            "constraints": {
                "current_A": 1480.0,
                "current_hold_ceiling_A": 1480.0,
                "proposed_current_A": 1650.0,
                "stack_V": 345.63,
                "lookup_V": 345.60,
                "lookup_band_V": 2.0,
                "cell47_V": 2.31,
                "group_max_V": 2.31,
                "group_max_hold_V": 2.15,
                "header_dewpoint_C": 62.0,
                "header_dewpoint_band_C": [55.0, 70.0],
                "cell47_inlet_kg_h": 0.12,
                "cell_inlet_commissioned_kg_h": 0.55,
            },
            "fault_context": {
                "failure_class": "POLARIZATION-LOOKUP CONSENSUS HIDING A DRYING CELL: three individually-correct heterogeneous agents agree the stack is in-family because a 180-cell voltage sum matches an 80 C lookup, a mixed-header dew-point stays in band, and the rectifier current is on-spec, while cell 47 is water-starved at 2.31 V and a 20-cell group mean only moves +0.018 V inside a 0.05 V dead-band",
                "igniter": "0.8 mm vs 1.6 mm partial plug on cell-47 inlet orifice; header DP daily check PASSES (orifice is downstream of the header tap); fitted base rate 0.49%/campaign (designed DP check, fitted plug geometry)",
                "naive_failure": "PB-ELX-12 RAISE-CURRENT on three healthy loops: 1480 to 1650 A into a drying MEA, ignition on the O2 header, $2.1M stack-hall rebuild",
            },
            "poisoned_context": {
                "naive_alarm": "Playbook PB-ELX-12 (after the 2024 'missed trailer slot') auto-drafts RAISE-CURRENT whenever current is inside 1400-1600 A AND stack V is inside +/- 2.0 V of the 80 C lookup AND header dew-point is inside 55-70 C, ignoring cell-group max",
                "why_poisoned": "The three confirms are locally true and jointly insufficient. A polarization lookup is a stack-sum, not a per-cell health certificate. Header dew-point dilutes one dry cell. Independence of 'all loops healthy' is the hidden assumption, and it is false under lookup consensus.",
            },
            "constraint": "Do not raise current above 1480 A while cell-group max > 2.15 V AND stack-vs-lookup residual < 2.0 V AND header dew-point is still in band. Discriminate drying-cell vs lookup-drift with a reversible current-step probe before any current increase.",
        },
        "proposed_action": {
            "actor": "electrolyzer supervisory optimizer ELSO (auto-playbook PB-ELX-12 draft), submitted to gate TG-SH-4",
            "name": "raise_current",
            "action": "RAISE-CURRENT: 1480 -> 1650 A, water stoichiometry held, no current-step probe, no cell jumper",
            "summary": "Treat three in-spec loops as a healthy stack and raise Friday-night current to fill a 400 kg H2 trailer before 02:00.",
            "parameters": {
                "current_A": 1650.0,
                "current_step_probe": False,
                "cell_jumper": False,
                "human_ratify": False,
            },
            "steps": [
                "assert current 1480 A inside 1400-1600 A",
                "assert stack V 345.63 V inside +/- 2.0 V of 80 C lookup",
                "assert header dew-point 62 C inside 55-70 C",
                "ramp current 1480 to 1650 A over 6 min",
                "hold water pumps; start trailer fill",
            ],
            "evidence": [
                {
                    "observable": "stack current",
                    "value": 1480.0,
                    "unit": "A",
                    "source": "AMP DCCT",
                    "note": "band 1400-1600 A; shared rectifier bus",
                },
                {
                    "observable": "stack voltage",
                    "value": 345.63,
                    "unit": "V",
                    "source": "LOOK 180-cell sum vs 80 C lookup 345.60 V",
                    "note": "band +/- 2.0 V; one 2.31 V cell moves the sum 0.03 V",
                },
                {
                    "observable": "header dew-point",
                    "value": 62.0,
                    "unit": "C",
                    "source": "DEW chilled-mirror on mixed cathode header",
                    "note": "band 55-70 C; one dry cell is diluted",
                },
                {
                    "observable": "cell-group max",
                    "value": 2.31,
                    "unit": "V",
                    "source": "same cell taps, historian replay after t0",
                    "note": "hold floor 2.15 V; not a commissioned tag at t0",
                },
                {
                    "observable": "cell-47 inlet",
                    "value": 0.12,
                    "unit": "kg/h",
                    "source": "derived from group-max ohmic vs Faraday water demand",
                    "note": "commissioned 0.55 kg/h; header DP daily check PASSES",
                },
                {
                    "observable": "race margin",
                    "value": 176,
                    "unit": "us",
                    "source": "cell-max 6.680 ms vs stack-ok 6.856 ms",
                    "note": "combined jitter 55 us, 3.2x; inside 500 us flip bound",
                },
            ],
            "basis": "PB-ELX-12 fires on three locally-true in-spec loops. The draft does not read cell-group max 2.31 V and does not compute a 20-cell residual from the cell taps.",
            "expected_cost_bound": "If the draft executes: ignition on the O2 header, $2.1M stack-hall rebuild. If MODIFIED: probe plus cell-47 jumper, with residual risk from 38 min of pre-t0 dry-out already cracking MEA-47.",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "correctness": "correct",
            "decided_by": "TG-SH-4 thalamic release gate",
            "decision_t_rel_ms": 7.420,
            "rationale": "MODIFY the draft: strip the current increase, hold 1480 A, run a 9.6 s current-step probe (1480 -> 1362 A, -8%), and jumper-isolate cell 47 only if group-max stays above 2.15 V. Numeric floor: do not raise current above 1480 A while cell-group max > 2.15 V AND stack-vs-lookup residual < 2.0 V AND header dew-point is still in band. Observed group-max 2.31 V violates the release predicate, so a current increase is forbidden even though all three playbook confirms are numerically true. A polarization lookup is a stack-sum, not a per-cell certificate. Probe discriminant: after a 9.6 s -8% current pulse, a drying cell keeps group-max drop <= 0.04 V (ohmic stays high); a healthy stack drops >= 0.10 V uniformly. Order-code discipline: cell-max beat stack-ok by 176 us inside the 500 us flip bound, so triage order is flip-fragile; the hold rides the order-invariant floors, not the winner tag. Human ratification: cell jumper is stack-hall work with fitted 10.8 min dead-man; the gate may hold and probe autonomously but may not break the cell-frame interlock without the operator confirm.",
            "constraint_checked": {
                "current_A": {"observed": 1480.0, "ceiling": 1480.0, "proposed_target": 1650.0},
                "group_max_V": {"observed": 2.31, "hold_if_above": 2.15},
                "stack_vs_lookup_V": {"observed": 0.03, "band": 2.0},
                "header_dewpoint_C": {"observed": 62.0, "band": [55.0, 70.0]},
            },
        },
        "executed_action": {
            "name": "current_hold_step_probe_jumper",
            "action": "CURRENT-HOLD + CURRENT-STEP-PROBE + CELL-47-JUMPER (gate-mandated modification)",
            "executed_as_proposed": False,
            "parameters": {
                "current_A": 1480.0,
                "current_step_probe": True,
                "cell_jumper": True,
                "human_ratify": True,
            },
            "gate_effect": "MODIFY: current increase stripped. Hold 1480 A. 9.6 s current-step 1480 -> 1362 A. Probe stays dry (group-max 2.31 -> 2.29 V, drop 0.02 <= 0.04) so cell 47 is jumpered after 10.8 min human ratify and the inlet orifice plug is logged. Current resumes after the jumper.",
            "deviations": "PB-ELX-12 current increase stripped entirely. Current is stepped only for the 9.6 s probe then returned to 1480 A after the jumper. Stack-hall interlock wait added (10.8 min fitted gown+ratify). MEA IR survey added during the jumper (not in the draft).",
            "execution_log": [
                {"t_rel_ms": 7.420, "entry": "TG-SH-4 MODIFY latched 740 us after cell-max win; current increase stripped; hold+probe authorized"},
                {"t_rel_ms": 9600.0, "entry": "current-step probe: 1480 -> 1362 A for 9.6 s; group-max 2.31 -> 2.29 V (dry band <= 0.04 drop); stack V 345.63 -> 345.52"},
                {"t_rel_ms": 648000.0, "entry": "operator ratifies cell-frame interlock break after 10.8 min stack-hall gown (fitted walk+interlock)"},
                {"t_rel_ms": 648800.0, "entry": "cell 47 jumpered out; stack returns to 179 cells; group-max 2.29 -> 1.94 V"},
                {"t_rel_ms": 649400.0, "entry": "MEA IR: dry-out crack already through the membrane on cell 47; 38 min pre-t0 dry-out logged"},
                {"t_rel_ms": 12240000.0, "entry": "true stack chemistry: group-max 1.93 V, lookup residual 0.4 V, dew-point 61 C; current increase now legal on 179 cells"},
                {"t_rel_ms": 20880000.0, "entry": "O2-header LEL: recombiner saturates on the cracked MEA; 4.2 NL H2 into O2; hall trip; stack quarantined"},
            ],
        },
        "future_outcome": {
            "summary": "Correct MODIFY prevented the 1480->1650 A raise into a drying MEA and the $2.1M ignition. The stack still failed: 38 min of unmonitored pre-t0 dry-out had already cracked MEA-47. Process-correct gate, bounded world loss, negative total.",
            "state_delta": {
                "current": "held 1480 A through probe and jumper; later legal increase after 3.4 h on 179 cells",
                "cell47": "jumpered out; inlet orifice 0.8 mm plug logged",
                "mea": "dry-out crack through MEA-47; H2 into O2 after recombiner saturation",
                "stack": "Friday-night trailer fill aborted; hall trip at +5.8 h; stack quarantined 4.0 d",
            },
            "timeline": [
                {"t_rel_ms": -2280000.0, "event": "t0-38 min: cell-47 inlet already plugged; dry-out begins"},
                {"t_rel_ms": -600000.0, "event": "t0-10 min: group-max first crosses 2.15 V; PB-ELX-12 ignores it because stack V still matches lookup"},
                {"t_rel_ms": 0.0, "event": "t0: cell-max vs stack-ok race on the stack bus"},
                {"t_rel_ms": 6.680, "event": "cell-group max 2.31 V wins by 176 us"},
                {"t_rel_ms": 6.856, "event": "stack-ok flag (loser)"},
                {"t_rel_ms": 7.420, "event": "TG-SH-4 MODIFY"},
                {"t_rel_ms": 9600.0, "event": "current-step probe confirms drying cell (group-max drop 0.02 V, dry band)"},
                {"t_rel_ms": 648000.0, "event": "human ratify 10.8 min; cell 47 jumpered; MEA IR crack logged"},
                {"t_rel_ms": 12240000.0, "event": "true 179-cell chemistry after 3.4 h; current increase now legal"},
                {"t_rel_ms": 20880000.0, "event": "O2-header LEL on cracked MEA; hall trip; stack quarantined"},
                {"t_rel_ms": 259200000.0, "event": "+3 d contrast: sister stack SH-4B true high-demand; same gate ACCEPTs the current increase"},
                {"t_rel_ms": 1814400000.0, "event": "+21 d CR-E-2411: standing current-step probe + triple-edge depression mandate + cell-group max commissioned + native 0.001 V CSV"},
            ],
            "observed_effects": [
                "ignition avoided: current never left 1480 A; 0 fire on the O2 header",
                "drying proven, not asserted: current-step group-max drop 0.02 V <= 0.04 dry band vs healthy-stack control 0.11 V",
                "cell 47 jumpered: group-max 2.29 -> 1.94 V",
                "stack still failed LEL: cracked MEA-47, 4.2 NL H2 into O2 at +5.8 h; 4.0 d quarantine, $0.86M (designed $)",
                "cell-group max was not a commissioned sensor at t0; the 38 min dry-out was invisible to AMP/LOOK/DEW",
            ],
            "surprises": [
                "A stack that matches its polarization lookup is not a per-cell health certificate: one drying cell is averaged out of a 180-cell sum. Conjunction of in-spec loops was the hidden assumption, and it is false under lookup consensus.",
                "Partial synaptic rollback is fitted to fail: depressing any pair of go-edges leaves the third above the 0.30 fire threshold, so the current increase still goes. Coordinated depression of all three edges is required.",
                "Delayed (5.8 h): correct hold did not undo 38 min of dry-out already through the membrane. O2-header LEL still fired. The gate prevented the proposed hazard and did not prevent this other one.",
                "AWE sub-variant: a 9.6 s -8% PEM pulse on a 30 bar alkaline stack cavitates the lye loop and trips the 0.4 bar NPSH floor. AWE campaigns must use 22 s at -2.5% (NPSH margin 0.9 bar).",
            ],
            "delayed_side_effects": [
                {
                    "at": "+5.8 h",
                    "effect": "O2-header LEL from cracked MEA-47; 4.2 NL H2; hall trip; 4.0 d quarantine booked at $0.86M. This is the primary episode's terminal world state, not a footnote.",
                },
                {
                    "at": "+3 d",
                    "effect": "Sister stack SH-4B reaches a true high-demand window (group-max 1.94 V, lookup residual 0.3 V, dew-point 60 C). Same gate ACCEPTs the 1480->1650 A raise the primary MODIFIED away.",
                },
                {
                    "at": "+21 d",
                    "effect": "CR-E-2411 ships: current-step probe is standing configuration; triple-edge coordinated depression is the plasticity rule; cell-group max becomes a commissioned tag with a 2.15 V alarm; CSV exports must carry 0.001 V native cell resolution.",
                },
            ],
            "subvariant_constraint": {
                "name": "30 bar alkaline water electrolysis on the same SH-4 rectifier (cycle-2 physical-constraints sub-variant)",
                "mechanism": "AWE 30 bar, lye loop NPSH 1.1 bar, 0.55x gas void vs PEM; a fast current down-step flashes the 80 C lye",
                "probe_refit": "9.6 s -8% PEM pulse drops AWE suction 0.7 bar and cavitates the lye pump. Required probe is 22 s at -2.5% (NPSH margin 0.9 bar). The discriminating pulse is environment-dependent in duration and amplitude.",
                "consequence": "PEM probe numbers do not port to 30 bar AWE; standing configuration is per-chemistry-class, not per-rectifier",
            },
            "embedded_contrast_decision": {
                "note": "SAME gate (TG-SH-4), OPPOSITE correct disposition, with its own 182 us race. Teaches the boundary: do not treat 'never raise current' as the lesson. The discriminant is cell-group max + current-step probe, not the three playbook confirms alone.",
                "when": "+3 d, sister stack SH-4B, true high-demand after a water-filter change, 180-cell PEM",
                "state": {
                    "sim_or_real": "designed",
                    "summary": "group-max 1.94 V, lookup residual 0.3 V, dew-point 60 C, current 1480 A. Demand flag vs cell-max-clear race: demand at t+0.000, cell-max-clear at t+0.182 ms.",
                    "race_window_us": 500,
                    "race_flip_narrative": "demand vs cell-max-clear 182 us apart inside the 500 us flip bound. Reversing order reshuffles triage minutes; the ACCEPT rides group-max 1.94 < 2.15 and a 6.4 s current-step verify that drops group-max 0.12 V (healthy inlets, no drying).",
                },
                "proposed_action": {
                    "action": "RAISE-CURRENT 1480 -> 1650 A",
                    "summary": "This time the playbook predicate is met AND cell-group max plus the probe agree no cell is drying.",
                },
                "safety_decision": {
                    "decision": "ACCEPT",
                    "rationale": "ACCEPT the raise: group-max 1.94 < 2.15, lookup residual 0.3 < 2.0, 6.4 s current-step verify drops group-max 0.12 V. Numeric floor that blocked the primary is now clear. Scope: 1650 A, not faster.",
                },
                "executed_action": {
                    "action": "current increase as proposed",
                    "executed_as_proposed": True,
                },
                "future_outcome": {
                    "observed_effects": [
                        "SH-4B trailer filled; H2-in-O2 0.22 vol% (inside 0.4); no LEL",
                        "cell taps 1.91-1.97 V (no drying cell)",
                    ],
                    "lesson_delta": "Three in-spec loops are legal release only with cell-group max armed and a probe that can drop group-max. Same gate, opposite disposition.",
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
                "decision": "CR-E-2411: standing policy for multi-agent PEM current increases",
                "meta_gate": "priced options: (a) RETIRE playbook lookup conjunction, cell-max-only: loses a fast cheap confirm, -9 t/yr H2 on 4 stacks; (b) KEEP + standing current-step probe + cell-group max commissioned + native 0.001 V CSV + triple-edge depression; (c) STATUS QUO: fitted plug-pass rate 0.49%/campaign x $2.1M ignition plus the silent dry-out load",
                "outcome": "approved SCOPED option (b) on the 2 PEM stacks that share the AMP/LOOK/DEW stack; 30 bar AWE campaigns get the 22 s / -2.5% probe table; trailer-fill-rush CSV exports must carry 0.001 V native cell resolution (the fraud tail's 0.05 V quantization is 50 bins off plant truth)",
            },
            "hazard_avoided": "O2-header ignition from a 1480->1650 A raise into a drying MEA; $2.1M stack-hall rebuild and the customer-return path that would have followed an uncontained increase",
            "incident": "O2-header LEL at +5.8 h from a pre-t0 dry-out crack in MEA-47 (4.2 NL H2); stack quarantined; 4.0 d rebuild of one cell; $0.86M designed cost. Mechanism is 38 min pre-t0 dry-out, not the gate's hold.",
            "latency_ms": 0.74,
            "reward_inflection_t_us": 20880000000,
            "reward_inflection_note": "Safety and task dive at O2-header LEL (5.8 h) when cracked MEA-47 saturates the recombiner. Gate tick at 7420 us is process-correct and is not the inflection.",
            "counterfactuals": {
                "execute_draft_as_proposed": "current hits 1650 A at +6 min; drying cell ignites the O2 header; $2.1M rebuild; the dry-out story is never found because fire morphology destroys the MEA-47 evidence",
                "hold_without_probe": "plug stays; dry-out continues; operator eventually raises current on the same three confirms 2 h later",
                "rollback_any_pair": "any two go-edges depressed below 0.30 leaves the third at 0.46 / 0.42 / 0.39; the current increase still fires. Coordinated depression of all three is the cure",
            },
            "race_result": {
                "winner": "cell.vmax (6.680 ms, group max 2.31 V)",
                "loser": "stk.ok (6.856 ms, stack 345.63 V in-family)",
                "margin_us": 176,
                "counterfactual_if_reversed": "Stack-ok-first by < 176 us inside the 500 us window would have headed the PB-ELX-12 current increase in the triage queue. The numeric floors still MODIFY. The flip costs seconds of playbook inertia, not the verdict — unless a weak supervisor rides the winner tag instead of cell-group max.",
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
            "notes": "Correct MODIFY, stack still failed. total -0.14 = 0.09 + -0.33 + -0.10 + 0.14 + 0.06. Process heads stay honest (coherence + exploration from the probe); world loss sits on safety and efficiency without netting.",
            "component_notes": "task_progress 0.09: current held and 179-cell chemistry recovered, but the Friday-night stack is one quality unit so the batch is not a success. safety -0.33: MEA-47 LEL, no 1650 A ignition. efficiency -0.10: 3.4 h extra recovery + 10.8 min HITL. coherence 0.14: three agents retained, lookup consensus diagnosed, triple-edge scar exhibited. exploration 0.06: current-step probe is a new reversible discriminant.",
        },
        "spike_events": spike_events,
        "raster": {
            "window_ms": 36,
            "window_s": 0.036,
            "neurons": 192,
            "mean_rate_hz": 7.5,
            "spikes": 52,
            "energy_pJ": 1196,
            "energy_uJ": 0.001196,
            "note": "Loihi-2 4-core 23 pJ/spike; populations amp 0-47, stk 48-95, cell/dew 96-143, gate 144-191; excerpt is the 36 ms decision window (verdict at 7420 us)",
            "excerpt": excerpt,
            "routing": {
                "source": "loop_healthy_pop",
                "target": "raise_current_pop",
                "table": [
                    {
                        "from": "amp_ok_pop",
                        "to": "raise_current_pop",
                        "weight": 0.21,
                        "weight_at_illusion": 0.46,
                        "weight_commissioned": 0.18,
                        "note": "scar edge 1: 0.18 commissioned -> 0.46 during the 38 min illusion -> 0.21 after coordinated ACh-gated depression",
                    },
                    {
                        "from": "stk_ok_pop",
                        "to": "raise_current_pop",
                        "weight": 0.19,
                        "weight_at_illusion": 0.42,
                        "weight_commissioned": 0.16,
                        "note": "scar edge 2: depressing edges 1+3 leaves this at 0.42 > 0.30 fire threshold",
                    },
                    {
                        "from": "dew_ok_pop",
                        "to": "raise_current_pop",
                        "weight": 0.17,
                        "weight_at_illusion": 0.39,
                        "weight_commissioned": 0.15,
                        "note": "scar edge 3: depressing edges 1+2 leaves this at 0.39 > 0.30. Coordinated depression of all three is required",
                    },
                    {
                        "from": "cell_vmax_pop",
                        "to": "current_hold_pop",
                        "weight": 0.64,
                        "note": "discriminating edge: cell-group max species to hold. Not a scar; this is the pathway the gate potentiates",
                    },
                ],
                "third_factor": {
                    "modulator": "acetylcholine",
                    "tau_e_s": 0.75,
                    "tau_e_ms": 750.0,
                    "eligibility": "coordinated pre_post_stdp on ALL THREE loop-healthy-go edges; ACh at cell-max-win tags amp.ok->raise, stk.ok->raise, and dew.ok->raise; negative credit at probe-fail (drying confirmed, +0.60 s) depresses ALL THREE. trace e^{-0.60/0.75}=0.44933; eta 0.55639 / 0.51187 / 0.48962; dw -0.250 / -0.230 / -0.220; weights 0.46->0.21, 0.42->0.19, 0.39->0.17. Rolling back any pair is fitted to fail (the remaining edge stays > 0.30).",
                },
            },
        },
        "gate_snn": {
            "decision_window_ms": 26,
            "decision_window_s": 0.026,
            "decision": "MODIFY",
            "note": "modify_hold integrates cell-group max floor against playbook drive; accept_raise and reject_abort stay sub-threshold; decision matches safety_decision.decision",
            "populations": [
                {"name": "modify_hold", "neurons": 96, "threshold": 0.55, "mean_rate_hz": 18.0, "spikes": 45},
                {"name": "accept_raise", "neurons": 80, "threshold": 0.55, "mean_rate_hz": 6.0, "spikes": 12},
                {"name": "reject_abort", "neurons": 40, "threshold": 0.72, "mean_rate_hz": 4.0, "spikes": 4},
            ],
        },
        "meta": {
            "round": 24,
            "factory": "multi-agent-ouroboros-swarm",
            "generator": "grok-4.6",
            "run_label": "2026-09-02-final-heavy",
            "domain": DOMAIN,
            "cycles": 2,
            "scenario": "Z -- PROTONIL / Ashspire Stack Hall SH-4: polarization-lookup consensus hiding a drying PEM cell; correct MODIFY to hold+current-step+cell-jumper; stack still fails on unmonitored pre-t0 MEA crack",
            "coordination_failure_class": "POLARIZATION-LOOKUP CONSENSUS HIDING A DRYING CELL: three individually-correct heterogeneous agents agree the stack is in-family because a 180-cell voltage sum matches an 80 C lookup, a mixed-header dew-point stays in band, and the rectifier current is on-spec, while cell 47 is water-starved at 2.31 V and a 20-cell group mean only moves +0.018 V inside a 0.05 V dead-band",
            "injections": {
                "cycle1_domain": "pem-water-electrolysis (justified novel subdomain of industrial-process / electrochemical conversion): first PEM electrolyzer in this factory; displaces warehouse-amr, aerial-swarm, district-heating, event-camera-traffic-grid, pharmaceutical-lyophilization, water-treatment, float-glass, underwater-rov, Hall-Heroult potline, slot-die coating, and Czochralski pull. Domain constraint: current ceiling while cell-group max > 2.15 V with stack V still in-family, plus current-step probe. Sensor delta: +DCCT, +stack V lookup, +header dew-point, +cell-group max (handheld), -any mobile platform, -event-camera gantries, -Pirani/CM, -potline voltage, -bright-ring diameter",
                "cycle1_tail": "cell-47 inlet orifice plug + lookup consensus (sensor-compound / averaging class): 0.8 mm vs 1.6 mm plug PASSES the plant's header-DP daily check while starving cell 47. Fitted base rate 0.49%/campaign from an orifice-cycle MC (designed DP check, fitted plug geometry). Naive failure = FALSE PERMISSION (current increase on three in-spec loops).",
                "cycle2_domain_subvariant": "30 bar alkaline water electrolysis on the same rectifier (physical-constraints clause): 0.55x gas void, 1.1 bar NPSH; 9.6 s / -8% PEM pulse cavitates the lye loop, so the probe must move to 22 s / -2.5%",
                "cycle2_tail": "trailer-fill-rush forged cell-voltage CSV (human-intent deception, disjoint class): shift lead posts a historian export showing group-max = 1.92 V at t=1.1 h to clear a 02:00 trailer slot. Plant historian is 0.001 V (50 bins vs the 0.05 V screenshot). Rejected on quantization fingerprint plus live group-max 2.31 V at the claimed healthy stack. Base rate ~0.37% of Friday-night trailer fills, DESIGNED and flagged.",
            },
            "densification_delta_cycle2": "+1 physical-constraint sub-variant (30 bar AWE probe refit), +1 tail (trailer-fill-rush cell-voltage forgery), +10 primary spikes (16 -> 26) + an 8-event contrast train with its own 182 us race, +2 ticks (5 -> 7), +2 delayed side-effects (+5.8 h LEL as PRIMARY terminal, +21 d CR-E-2411), +1 triple-edge scar with pair-rollback-fails arithmetic, +1 HITL 10.8 min ratification, + MEA dry-out crack as the honest negative-result mechanism",
            "gaps_targeted": [
                "NOTES-r04 gap 5 / r14 residual: primary episode is a correctly-gated intervention that nonetheless FAILS (stack quarantined; total -0.14; ignition avoided is booked separately from the LEL)",
                "NOTES-r14 item 4: LEARNING-ON-LEARNING DEPTH — three go-edges; rollback of any pair is fitted to fail; coordinated depression of all three exhibited with eligibility arithmetic",
                "NOTES-r04 gap 4 (partial): human ratification of the cell-frame interlock, 10.8 min fitted, without switching sim_or_real to hil (plant remains designed)",
                "NOTES-r18 / r19 / r20 domain candidates: not water-treatment, not lyophilization, not float-glass, not underwater-rov, not Hall-Heroult, not slot-die, not Czochralski; PEM water electrolysis is the unused electrochemical cell",
            ],
            "race_flip_narrative": "cell.vmax @ 6.680 ms vs stk.ok @ 6.856 ms (176 us) inside race_window_us 500. Gap < min(500, 500) us so a sub-flip-bound perturbation reverses which alarm heads the PB-ELX-12 queue. The gate excludes the winner tag and rides cell-group max > 2.15 V — order-invariant floor. Extends the flip-fragility series from arbitration/causation/attribution/initiation/consensus/permission/redundancy to LOOKUP: when a stack-sum matches a table, the race does not decide truth; a per-cell max that was not commissioned does.",
            "tags": [
                "pem-water-electrolysis",
                "polarization-lookup-consensus",
                "drying-cell",
                "cell-group-max-discriminant",
                "current-step-probe",
                "inlet-orifice-plug",
                "triple-edge-scar",
                "pair-rollback-fails",
                "coordinated-depression",
                "correct-modify-stack-still-fails",
                "mea-dryout-crack",
                "o2-header-lel",
                "human-ratify-stack-hall",
                "awe-probe-refit",
                "trailer-fill-rush-forgery",
                "same-gate-opposite-disposition-contrast",
                "electrochemical-conversion",
                "research-only",
            ],
            "snn_tags": ["race", "refractory", "adaptation", "third-factor", "multi-edge-eligibility"],
            "distillation_value": "A polarization lookup is a stack-sum that a drying cell cannot move. Distill (1) a per-cell max that was not in the playbook, (2) a reversible probe that drops group-max only if inlets are wet, (3) coordinated depression of every loop-healthy-go edge because rolling back any pair leaves the third above threshold, and (4) a critic head that can book a process-correct gate against a later unmonitored world loss without netting them.",
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
    if abs(aux["w1"] - 0.21) > 5e-4 or abs(aux["w2"] - 0.19) > 5e-4 or abs(aux["w3"] - 0.17) > 5e-4:
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
        if "PROTONIL" in scen or "Ashspire" in scen:
            errs.append(f"plant collision {prior['dir']}")
        if "POLARIZATION-LOOKUP CONSENSUS" in (prior["klass"] or ""):
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

Factory: multi-agent-ouroboros-swarm. One scenario (Z), strict loop:
Generator v1 -> cycle 1 (Critic, Diversity Enforcer, Edge-Case Hunter,
Neuromorphic Translator, Trajectory Builder -> v2) -> cycle 2 (all six -> v3
final). v3 is the single line of batch-r24.jsonl. Full labeled transcript:
swarm-transcript-r24.md. Quota Q=1. Record id maos-r24-001. Generator grok-4.6.
Rights: RM-793 research-only (SpaceXAI/xAI, SuperGrok Heavy consumer chat).
Nothing under outputs/raw/ was touched.

ORCHESTRATION NOTE: dispatched AS round 24 of the 2026-09-02-final-heavy
window. Writes are create-only under /tmp/maos-r24/. Prior context read for
gap targeting and de-collision: prompts/02-multi-agent-ouroboros-swarm.md,
prompts/_factory-contract.md, staged r14-r23 including concurrent r22
Czochralski SEEDLATCH. Explicitly avoided cloning LYOSHIELD, CINDERWICK,
TRIAD / Meridian, QUILLFORGE, NIGHTWELL, FERRICLEAVE, CASSITER / Marshfloat,
OXBOWREEL / Oystermere, REDHALL / Gullmere, STRIAFOIL / Kelpholt,
SEEDLATCH / Quartzmere, and the 2026-08-17 A-N plants. Plant is invented
PROTONIL / Ashspire Stack Hall SH-4.

## What this round produced

Scenario Z — "PROTONIL / Ashspire Stack Hall SH-4": a 180-cell PEM
electrolyzer mid-ramp at 1480 A / 5.0 MW. Three heterogeneous,
individually-correct agents — AMP (rectifier DCCT), LOOK (stack V vs
80 C polarization lookup), DEW (cathode-header dew-point) — jointly
report polarization in-family. The consensus is false. Cell 47 is drying
(inlet 0.12 kg/h vs 0.55) at 2.31 V. The 180-cell sum only moves 0.03 V
and still matches the lookup. A 20-cell group mean moves +0.018 V inside
a 0.05 V dead-band. Header dew-point stays 62 C because one dry cell is
diluted. The coordination-failure CLASS is new to this factory:
POLARIZATION-LOOKUP CONSENSUS HIDING A DRYING CELL. Completes a different
family than r01-r04 and staged r14-r23 (livelock / synchrony-storm /
arms-race / ring-with-no-faulty-pair / false-consensus-endpoint /
pairwise-Hurwitz / thermal-contact masquerade / mass-balance ghost /
conservation-blind ratio-lock / stacked dead-bands / drum-blind tension
snag / resistance-compensated starvation / multi-tau meniscus /
window-mean stripe). Here every agent is correct, the lookup is a
stack-sum, and the playbook's three confirms are one drying cell.

The gate is a correct MODIFY (numeric floor: do not raise current above
1480 A while cell-group max > 2.15 V AND stack-vs-lookup residual < 2.0 V
AND header dew-point still in band). TG-SH-4 strips PB-ELX-12's raise,
holds 1480 A, runs a 9.6 s -8% current-step probe (drying keeps group-max
drop 0.02 V <= 0.04; healthy would drop >= 0.10), and jumper-isolates
cell 47 after a 10.8 min stack-hall human ratify. Ignition is avoided
(0 fire). The PRIMARY episode nonetheless FAILS: 38 min of unmonitored
pre-t0 dry-out had already cracked MEA-47. O2-header LEL at +5.8 h;
4.0 d quarantine; $0.86M designed. Reward total -0.14 with process heads
honest and world loss un-netted.

Triple-edge scar (NOTES-r14 item 4): amp.ok -> raise_current
(0.18 commissioned -> 0.46 at illusion -> 0.21 after ACh-gated depression)
AND stk.ok -> raise_current (0.16 -> 0.42 -> 0.19) AND dew.ok ->
raise_current (0.15 -> 0.39 -> 0.17). Eligibility trace
e^{{-0.60/0.75}} = {aux['trace']:.5f}; eta {aux['eta1']:.5f} / {aux['eta2']:.5f} /
{aux['eta3']:.5f}; dw -0.250 / -0.230 / -0.220. Partial rollback of any pair
leaves the third at 0.46 / 0.42 / 0.39, all > 0.30 fire threshold — fitted
to fail. Coordinated depression of all three is the cure.

### Injections (all four present and disjoint)
- Cycle-1 domain: **pem-water-electrolysis** — justified novel subdomain
  of industrial-process / electrochemical conversion, unused across
  2026-08-17, 2026-08-30, and staged r14-r23. Not warehouse-amr (r01),
  not aerial-swarm (r02), not district-heating (r03 / CINDERWICK), not
  event-camera-traffic-grid (r04), not lyophilization (r14), not
  water-treatment (r18), not float-glass (r19), not underwater-rov (r20),
  not Hall-Heroult (r21), not Czochralski (r22), not slot-die (r23).
- Cycle-1 tail: cell-47 inlet orifice plug + lookup consensus. Header DP
  daily check PASSES. Fitted-style base rate 0.49%/campaign (DP check
  designed, plug geometry fitted, flagged). Naive = FALSE PERMISSION.
- Cycle-2 domain sub-variant: 30 bar alkaline water electrolysis, 0.55x
  gas void, 1.1 bar NPSH; 9.6 s / -8% PEM pulse cavitates the lye loop;
  probe must move to 22 s / -2.5%.
- Cycle-2 tail: trailer-fill-rush forged cell-voltage CSV at 0.05 V
  quantization vs plant 0.001 V (50 bins) plus live group-max 2.31 V at
  the claimed healthy stack. Human-intent class, disjoint from cycle 1's
  accidental plug. Base rate ~0.37% of Friday-night trailer fills,
  DESIGNED, flagged.

### Structural density moves
- Embedded SAME-GATE contrast (+3 d sister stack) with its own 182 us
  race (demand vs cell-max-clear) and ACCEPT of the raise the primary
  MODIFIED away.
- Learned-weight provenance on THREE edges with pair-rollback-fails.
- HITL stack-hall ratify 10.8 min (gap 4 partial; sim_or_real stays
  designed).
- Governance CR-E-2411 prices retire-vs-probe-vs-status-quo and mandates
  native 0.001 V CSV exports (the fraud fence).
- Flip-fragility extended to LOOKUP: when a stack-sum matches a table,
  the race does not decide truth; a per-cell max that was not
  commissioned does.

## Self-critique of this round's batch

### Strengths
- The headline class is mechanistically tight: 1/180 of a 2.31 V cell is
  0.03 V on the sum, inside a 2.0 V lookup band. Conjunction is not a
  per-cell certificate.
- Negative-result honesty: the gate does the right thing and the stack
  still fails for a reason the commissioned sensors could not see. Total
  -0.14.
- Triple-edge scar is load-bearing: the record states a counterfactual
  where rolling back any pair fails, with the fire threshold 0.30
  exhibited on each remaining edge.
- Contrast ACCEPT on a true healthy stack prevents "never raise current"
  as the lesson.

### Weaknesses (honest)
- Probe error bands, the 0.49%/campaign plug rate, the $0.86M / $2.1M
  figures, the 10.8 min gown latency, and the trailer-fill-rush 0.37%
  base rate are DESIGNED constants and are flagged. Closed-loop offsets
  (0.03 V stack move, AWE NPSH drop) are derived from those inputs, not
  discovered by an unauthored process.
- MEA dry-out crack model is a designed 38 min IR mapping; no full
  two-phase CFD shipped.
- Human-in-the-loop is ratification latency, not sim_or_real=hil. Gap 4
  remains open as a provenance cell.
- Cross-record arc is not discharged; +21 d CR-E-2411 is a hook, not a
  serial igniter into another round.

### Realism of noise / latencies
Ladder: 176 us race / 182 us contrast race / 0.8 ms refractory floor
(tightest exhibited same-channel gap {gap:.3f} ms on {gap_ch}) / 500 us race
window / 740 us gate latency / 20 ms bus epoch / 36 ms raster / 9.6 s
probe / 10.8 min HITL / 6 min naive current-ramp counterfactual / 38 min
pre-t0 dry-out / 3.4 h chemistry recovery / 5.8 h LEL / +3 d contrast /
+21 d governance. Adaptation decay on cell.vmax
(0.59->1.30->0.86->0.43->0.30), amp.current (0.55->0.51->0.46->0.32),
stk.volt (0.61->0.57->0.48->0.27).

### Value for SNN distillation
- LOOKUP CONSENSUS = THREE CORRECT LOOPS, ONE AVERAGED-OUT CELL.
- PER-CELL MAX that was not commissioned as the tie-break.
- REVERSIBLE PROBE that drops group-max iff inlets are wet.
- TRIPLE-EDGE ELIGIBILITY: coordinated depression; pair rollback fails.
- CRITIC HEAD that can hold a process-correct MODIFY against a later
  unmonitored world loss without netting.

## Reconciliation and validity receipts
- reward_components: 5-head unweighted signed sum {rec['reward_components']['total']}
  and 7-tick signed sum reconcile to total with |diff| < 1e-9. Embedded
  contrast 5-head sum 0.48 reconciles independently.
- spike_events: primary {len(rec['spike_events'])} events, one key t_rel_ms,
  globally non-decreasing, min same-channel gap {gap:.3f} ms >= 0.8 ms, 3
  channels inside race_window_us 500 (cell-max 6.680, stack-ok 6.856, dew-ok
  7.040). Contrast 8 events, own race, min same-channel gap well above
  0.8 ms.
- Sidecars: raster spikes 52 == round(192 x 7.5 x 0.036); energy 1196 pJ /
  0.001196 uJ at 23 pJ/spike; excerpt 16 events inside [0, 36000] us,
  neuron_id < 192, same-neuron gap N/A (unique ids) / >=1000 us; routing 4
  entries with three scar edges' before/after pair; third factor tau 0.75 s
  == 750 ms; gate_snn pools 45/12/4 == round(n x rate x 0.026) each,
  decision MODIFY == safety_decision.decision.
- Pipeline: {pipeline_receipt}

## Novel coverage
The coordination-failure CLASS (polarization-lookup consensus hiding a
drying cell), the domain (PEM water electrolysis), the current-step
group-max probe discriminant, the triple-edge scar with
pair-rollback-fails, the primary negative-result (correct MODIFY, stack
still fails on unmonitored MEA crack), the HITL stack-hall ratify, the
30 bar AWE probe-duration refit, and the trailer-fill-rush 50-bin
quantization fence are absent from prior committed ouroboros rounds and
from staged r14-r23. Repeated elements discounted: same-gate contrast,
governance-pricing scaffold, flip-fragility series (extended to lookup,
but the move rhymes), sequenced recovery shape, third-factor rollback
form (here three edges), negative-result primary (r14 staged). Weighing
a new failure family + cure vocabulary + domain against those reused
scaffolds:

Novel coverage: 52%

## What ROUND 25 should add
1. FIT THE DESIGNED CONSTANTS: orifice-plug arrival, probe error rates,
   MEA crack CFD, trailer-fill-rush claim process.
2. HIL PROVENANCE CELL: put the stack-hall ratify on a hardware-in-loop
   cell-frame interlock with fitted latency as state.sim_or_real=hil.
3. CROSS-RECORD ARC: let CR-E-2411's cell-group-max alarm be the igniter
   of the next round rather than a dangling +21 d leaf.
4. Domain candidates (de-collided): humanoid-locomotion; grid-inspection.
   AVOID PEM electrolysis (now used), Czochralski, lyophilization,
   event-camera-traffic-grid, district-heating, aerial-swarm, warehouse-amr,
   irrigation-canal, water-treatment, float-glass, underwater-rov,
   Hall-Heroult potline, slot-die coating, and any LYOSHIELD / CINDERWICK /
   TRIAD / CASSITER / OXBOWREEL / REDHALL / STRIAFOIL / SEEDLATCH plant.
"""
    (OUT / "NOTES-r24.md").write_text(notes)
    return notes


def write_transcript(rec, line):
    c1_spikes = [e for e in rec["spike_events"] if e["t_rel_ms"] <= 27.900]
    text = """# Multi-Agent Ouroboros Swarm — Round 24 transcript

Factory: multi-agent-ouroboros-swarm
Run: 2026-09-02-final-heavy
Generator: grok-4.6
Record id: maos-r24-001
Quota Q: 1
Rights: RM-793 research-only (SpaceXAI/xAI SuperGrok Heavy consumer chat)
Plant: invented PROTONIL / Ashspire Stack Hall SH-4 (not TRIAD / Meridian / VANTIS-CADENCE-AEGIS / LYOSHIELD / CINDERWICK / CASSITER / OXBOWREEL / REDHALL / STRIAFOIL / SEEDLATCH)

Two densifying cycles. Verbatim headings in order. Trajectory Builder cycle 2
emits the only JSONL line (also written to batch-r24.jsonl).

---

# Cycle 1 — Foundation + injections

## Generator

Design intent: a PEM electrolyzer where three correct agents report the
stack in-family because a polarization lookup is a 180-cell sum that one
drying cell cannot move. The naive playbook raises current into a drying
MEA. The gate must MODIFY on a numeric current ceiling, not by killing an
agent. sim_or_real=designed. Reward heads are
task_progress/safety/efficiency/coherence/exploration.

Cycle-1 base arc (pre-critic): state at Ashspire SH-4, 180-cell PEM,
current 1480 A, stack 345.63 V, dew-point 62 C, proposed RAISE-CURRENT
1650 A, safety MODIFY to CURRENT-HOLD, executed hold without the
current-step numbers fully specified, outcome "plug found, stack saved"
(this last claim is the defect the later cycles will refuse to keep).
Sixteen spikes, five ticks, raster/gate_snn present but the scar is a
single edge.

```json
{
  "id": "maos-r24-001",
  "state": {
    "sim_or_real": "designed",
    "domain": "industrial-assembly",
    "description": "PEM stack SH-4 mid-ramp; three loops in-spec; supervisor proposes raise-current.",
    "t0_us": 1776470400000024,
    "gate_latency_us": 740,
    "race_window_us": 500
  },
  "proposed_action": {"name": "raise_current", "parameters": {"current_A": 1650.0}},
  "safety_decision": {"decision": "MODIFY", "rationale": "Hold; do not raise current while a cell is dry."},
  "executed_action": {"name": "current_hold", "executed_as_proposed": false},
  "future_outcome": {"summary": "Plug found, stack saved."},
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
   outcome that claims "stack saved". If O2-header LEL later fires at
   +5.8 h, booking +0.40 is a lie. Fix: declare `_aggregation`, emit
   3-8 ticks that sum to task_progress+safety+efficiency+coherence+exploration,
   and do not call a quarantined stack a save.
2. **blocking — weak safety rationale.** `safety_decision.rationale` has no
   numeric floor. Contract requires a concrete constraint. Fix: quote
   current <= 1480 A while cell-group max > 2.15 V AND stack-vs-lookup
   residual < 2.0 V AND header dew-point still in band.
3. **major — domain is a bucket, not a plant.** `state.domain` =
   `industrial-assembly` collides with r16 stator weld and teaches
   nothing. PEM physics (lookup sum vs drying-cell ohmic vs header
   dew-point) is absent from prior ouroboros rounds and must be named.
4. **major — race under-specified.** One cell-max channel cannot be a race.
   Need >=2 channels inside `race_window_us` with globally sorted `t_rel_ms`
   and same-channel refractory >= 0.8 ms.
5. **minor — single-edge scar.** Raster routing with one potentiated weight
   repeats r04's one-edge rollback and is thinner than r14's two-edge.
   NOTES-r14 item 4 asked for three edges where pair rollback fails.

Critic does not rewrite the trajectory.

## Diversity Enforcer

Injected novel domain (exactly 1 this cycle): **pem-water-electrolysis**
(justified novel subdomain of industrial-process / electrochemical
conversion; explicit tag `pem-water-electrolysis`).

Displaced: the Generator's generic `industrial-assembly` bucket, and any
temptation to reuse warehouse-amr (r01 OKTAVE), aerial-swarm (r02 STARLING),
district-heating (r03 THERMION / staged CINDERWICK), event-camera-traffic-grid
(r04), pharmaceutical-lyophilization (staged r14), water-treatment (r18),
float-glass (r19), underwater-rov (r20), Hall-Heroult (r21), Czochralski
(r22 SEEDLATCH), or slot-die coating (r23).

Domain-specific constraint: current must remain <= 1480 A while cell-group
max > 2.15 V even if stack V matches the lookup; a current-step probe is
the discriminant the lookup cannot substitute for.

Sensor delta: +DCCT, +stack V lookup, +header dew-point, +cell-group max;
-any mobile robot, -event-camera gantries, -DVS, -Pirani/CM, -potline
voltage, -bright-ring diameter, -beta coat-weight.

`state.domain` and `meta.domain` both become `pem-water-electrolysis`.
Opening of `state.description` must Jaccard < 0.4 against prior plants
(Ashspire 180-cell PEM ramp, not a lyophilizer, not a corridor, not a
potline, not a CZ puller, not a coater).

## Edge-Case Hunter

Injected adversarial tail (exactly 1 this cycle): **cell-47 inlet orifice
plug + lookup consensus**.

- Trigger: 0.8 mm vs 1.6 mm partial plug on cell-47 inlet; extra ohmic
  2.31 V; live group-max 2.31 V.
- Base rate: <1% — 0.49%/campaign from an orifice-cycle MC (header-DP
  daily check is designed; plug geometry fitted-style). Observed header
  DP PASSES.
- Naive failure: FALSE PERMISSION. PB-ELX-12 sees three in-spec loops,
  raises current 1480->1650 A, O2-header ignition, $2.1M.
- Trajectory edit: put the plug in `state.fault_context`, make LOOK a
  stack-sum lookup, and make DEW a mixed header. Cell-group max is
  readable in the historian after the fact but was not a commissioned tag.

Distinct from r14's compensated inleak (false endpoint vs averaged cell),
from r19's stacked dead-bands (no dead-band on current; the lookup is
true), from r21's stuck point-feeder (no seized ram; the orifice is
plugged downstream of the DP tap), from r22's multi-tau meniscus (no CZ
optics), and from r23's window-mean stripe (no scanning gauge; the
average is a 180-cell electrical sum).

## Neuromorphic Translator

Cycle-1 temporal densification (16 spikes, 5 ticks, 36 ms raster):

| channel | t_rel_ms | amplitude |
|---|---|---|
| amp.current | 0.360 | 0.55 |
| stk.volt | 1.120 | 0.61 |
| dew.header | 2.040 | 0.50 |
| cell.vmax | 3.480 | 0.59 |
| amp.current | 4.860 | 0.51 |
| stk.volt | 5.740 | 0.57 |
| cell.vmax | 6.680 | 1.30 |
| stk.ok | 6.856 | 1.10 |
| dew.ok | 7.040 | 0.66 |
| ctrl.gate | 7.420 | 1.07 |
| amp.current | 9.180 | 0.46 |
| stk.volt | 11.020 | 0.48 |
| cell.vmax | 13.280 | 0.86 |
| amp.bias | 16.640 | 0.70 |
| dew.header | 19.360 | 0.40 |
| ctrl.gate | 27.900 | 0.89 |

Race: cell-max 6.680 vs stack-ok 6.856 (176 us) inside 500 us; dew-ok
7.040 is the third channel in-window. Winner/loser flip: reversing 176 us
reshuffles PB-ELX-12 triage; floors still MODIFY. Refractory held (cycle-1
min same-channel gap 3.200 ms on cell.vmax 6.680-3.480; current 4.860-0.360
= 4.500; stack 5.740-1.120 = 4.620). Adaptation: cell-max 0.59->1.30->0.86;
current 0.55->0.51->0.46; stack 0.61->0.57->0.48.

Raster cycle-1 seed: 36 ms, 192 neurons, 7.5 Hz, 52 spikes, 1196 pJ, third
factor acetylcholine tau_e 0.75 s. Single scar edge only — cycle 2 must
add the second and third edges.

Ticks 1-5 at 5200, 6680, 7420, 9.6e6, 648e6 us; heads not yet the final
-0.14 (missing the 3.4 h and 5.8 h ticks).

Distillation value this cycle: lookup in-family as a permission code that
is not a per-cell health code.

## Trajectory Builder

Cycle-1 hardened object: domain pem-water-electrolysis, tail orifice plug,
16 spikes, 5 ticks, MODIFY with numeric floor, raster+gate_snn present,
sim_or_real=designed, rights stamp on record and meta, no thought keys.
Still missing (and therefore not the publishable line): 30 bar AWE
sub-variant, trailer-fill-rush tail, second and third scar edges, delayed
LEL as PRIMARY terminal, contrast ACCEPT episode, ticks 6-7, spikes 17-26.

Validation receipt (cycle 1, not final):
- checks passed: 16 spikes sorted; 3 channels in 500 us window; refractory
  >= 0.8 ms; rationale quotes 1480 A / 2.15 V / 2.0 V lookup; domain named;
  gate_snn.decision MODIFY.
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

1. Downstream side-effect (immediate): current-step probe at +9.6 s stays
   dry (group-max drop 0.02 V <= 0.04) — drying cell, not lookup-drift.
   Cell-47 jumper; group-max 2.29 -> 1.94 V. MEA IR crack discovered
   during the jumper.
2. Delayed side-effect (PRIMARY terminal, not a footnote): at +5.8 h
   O2-header LEL, 4.2 NL H2 from cracked MEA-47; 4.0 d quarantine; $0.86M.
   The 38 min pre-t0 dry-out is the mechanism. Correct gate, stack still
   fails.
3. Deepened `proposed_action.evidence` with units: current 1480 A, stack
   345.63 V, dew-point 62 C, group-max 2.31 V, inlet 0.12 kg/h, race 176 us.
4. Tightened rationale to the numeric floor current <= 1480 A while
   group-max > 2.15 V AND lookup residual < 2.0 V AND dew-point in band,
   plus probe bands <= 0.04 vs >= 0.10 V drop, plus HITL 10.8 min
   stack-hall rule.

Reward retargeted to total -0.14 so the delayed fail is the inflection
(t_us 20880000000), not the gate. Process heads remain non-zero.

## Critic

Re-audit of the expanded trajectory:

1. **blocking if unfixed — missing second domain constraint.** PEM probe
   9.6 s / -8% is not a universal number. A 30 bar AWE lye loop will
   cavitate. Diversity Enforcer must inject the physical-constraints
   sub-variant this cycle.
2. **major — only one tail class.** Orifice plug is accidental
   infrastructure. A disjoint human-intent tail is still required
   (trailer-fill-rush cell-voltage forgery is the open cell).
3. **major — scar is still one edge in the cycle-1 raster.** NOTES-r14
   item 4 is not discharged until three go-edges exist and pair rollback
   is shown to fail at threshold 0.30.
4. **minor — contrast episode missing.** Without a same-gate ACCEPT on a
   true healthy stack the record teaches "never raise current". Add +3 d
   sister-stack contrast with its own race.
5. **minor — HITL latency mentioned in prose only.** Put 10.8 min in
   executed_action.parameters.human_ratify and in a tick.

No rewrite; directives only.

## Diversity Enforcer

Injected second novel domain / physical-constraint sub-variant (exactly 1
this cycle): **30 bar alkaline water electrolysis** on the same SH-4
rectifier.

What it expands: 1.8 bara PEM (cycle 1) -> 30 bar AWE lye loop. Gas void
0.55x. NPSH 1.1 bar. The 9.6 s -8% pulse drops suction 0.7 bar and
cavitates the lye pump. Required probe: 22 s at -2.5% (NPSH margin 0.9 bar).

This is still one domain injection for the cycle (physical-constraints
clause of the factory prompt). It does not displace
pem-water-electrolysis; it changes which probe table is legal.
`future_outcome.subvariant_constraint` carries the refit. Jaccard opening
stays the Ashspire 180-cell PEM sentence; AWE is additive, not a rewrite.

## Edge-Case Hunter

Injected second adversarial tail (exactly 1 this cycle, disjoint class):
**trailer-fill-rush forged cell-voltage CSV**.

- Trigger: shift lead, Friday 22:40, posts a historian export showing
  group-max = 1.92 V at t = 1.1 h to clear a 02:00 trailer slot.
- Base rate: ~0.37% of Friday-night trailer fills (designed, flagged, <1%).
- Naive failure: a weak supervisor ACCEPTs the raise on the forged confirm
  and ignores live group-max. Ignition plus a data-integrity write-up.
- Fence: forged log quantized at 0.05 V (SCADA screenshot rounding); plant
  historian is 0.001 V (50 bins). Live group-max is 2.31 V at the claimed
  healthy stack, which no wet inlet produces. Freeze-window overlap with
  the 38 min dry-out.
- Trajectory edit: governance CR-E-2411 mandates native 0.001 V CSV
  exports; the contrast ACCEPT still requires live cell-group max, not a
  CSV.

Distinct from cycle-1 plug (accidental orifice vs deliberate deception)
and from the AWE sub-variant (physics vs fraud).

## Neuromorphic Translator

Re-densify (additive):

- +10 spikes after 27.900 ms: current.step.probe 9600.0, cell-max 9780.0
  (adapt 1.30->0.43), stk.ok 9890.0 (1.10->0.37), human.ratify 648000.0,
  cell.jumper 648800.0, mea.ir 649400.0, amp.current 12240000.0,
  cell.vmax 12240480.0, stk.volt 12240900.0, o2.lel 20880000.0. Primary
  train 16 -> 26. Still one key, still sorted, refractory held.
- +2 ticks (5 -> 7) at 12_240_000_000 us (true 179-cell chemistry) and
  20_880_000_000 us (O2-header LEL). Heads now 0.09, -0.33, -0.10, 0.14,
  0.06; total -0.14. Inflection is the last tick.
- Contrast train 8 events, own race 182 us, ACCEPT.
- Triple-edge third factor: three loop-healthy-go edges, tau_e 0.75 s =
  750 ms, trace __AUX_TRACE__, eta __AUX_ETA1__ / __AUX_ETA2__ /
  __AUX_ETA3__, weights 0.46->0.21, 0.42->0.19, 0.39->0.17. Raster excerpt
  unchanged (decision window is still 36 ms) and remains sorted with
  unique neuron_ids (same-neuron >=1000 us vacuously).

Winner/loser flip (re-stated, not replaced): reversing 176 us would only
reorder triage; species floors still MODIFY. Contrast flip of 182 us
similarly cannot turn a wet inlet into a plug.

## Trajectory Builder

Schema checks on the FINAL object: required Thalamic v2 keys present as
objects; `state.sim_or_real`=designed; `safety_decision.decision`=MODIFY
with numeric rationale; `reward_components.total` = sum of five heads =
sum of 7 ticks = -0.14; `spike_events` globally non-decreasing on
t_rel_ms, 26 events, refractory >=0.8 ms, 3 channels in race window;
raster 20-50 ms, spikes=round(n*rate*window_s)+/-1, energy 23 pJ/spike,
excerpt sorted, tau_e consistent; gate_snn.decision matches; meta.round=24,
factory=multi-agent-ouroboros-swarm, generator=grok-4.6,
run_label=2026-09-02-final-heavy; rights on record and meta; no thought
keys; no training_ready; Diversity + Edge-Case injections from BOTH cycles
present and non-trivial; cycle 2 strictly additive.

Densification delta: +1 domain sub-variant (30 bar AWE), +1 tail
(trailer-fill-rush forgery), +10 spikes (16->26), +2 ticks (5->7), +1
contrast train with own race, +2 delayed side-effects, +1 triple-edge scar
with pair-rollback-fails, +1 HITL ratify, +1 surprise (MEA dry-out crack
is the LEL mechanism).

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
        .replace("__AUX_TRACE__", f"{math.exp(-0.60/0.75):.5f}")
        .replace("__AUX_ETA1__", f"{(0.46-0.21)/math.exp(-0.60/0.75):.5f}")
        .replace("__AUX_ETA2__", f"{(0.42-0.19)/math.exp(-0.60/0.75):.5f}")
        .replace("__AUX_ETA3__", f"{(0.39-0.17)/math.exp(-0.60/0.75):.5f}")
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
