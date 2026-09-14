#!/usr/bin/env python3
"""Create-only Multi-Agent Ouroboros Swarm round 62 writer."""
from __future__ import annotations

import json
import math
import os
import sys
from pathlib import Path

OUT_DIRS = [
    Path(
        "/home/raulmc/rmems/synthetic-factory/outputs/raw/2026-09-02-final-heavy/"
        "multi-agent-ouroboros-swarm"
    ),
    Path(
        "/tmp/sf-window/outputs/raw/2026-09-02-final-heavy/"
        "multi-agent-ouroboros-swarm"
    ),
]
NEXT_ROUND_PATHS = [
    Path("/home/raulmc/rmems/synthetic-factory/outputs/raw/2026-09-02-final-heavy/NEXT_ROUND.json"),
    Path("/tmp/sf-window/outputs/raw/2026-09-02-final-heavy/NEXT_ROUND.json"),
]

RIGHTS = {
    "provider": "SpaceXAI/xAI",
    "model": "grok-4.6",
    "channel": "consumer",
    "subscription_plan": "SuperGrok Heavy",
    "generation_surface": "SuperGrok Heavy chat",
    "generated_at": "2026-09-02T19:22:00Z",
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

TRACE = math.exp(-0.82 / 0.92)
ETA = (0.250 / TRACE, 0.220 / TRACE, 0.210 / TRACE)


def build_record() -> dict:
    ticks = [
        {"t_us": 4588, "task_progress": 0.01, "safety": -0.02, "efficiency": -0.01, "coherence": 0.02, "exploration": 0.01},
        {"t_us": 6520, "task_progress": 0.02, "safety": -0.04, "efficiency": -0.01, "coherence": 0.03, "exploration": 0.02},
        {"t_us": 7232, "task_progress": 0.02, "safety": -0.05, "efficiency": -0.01, "coherence": 0.03, "exploration": 0.02},
        {"t_us": 6800000, "task_progress": 0.01, "safety": -0.06, "efficiency": -0.02, "coherence": 0.02, "exploration": 0.01},
        {"t_us": 504000000, "task_progress": 0.01, "safety": -0.05, "efficiency": -0.02, "coherence": 0.01, "exploration": 0.01},
        {"t_us": 9720000000, "task_progress": 0.01, "safety": -0.06, "efficiency": -0.02, "coherence": 0.01, "exploration": 0.01},
        {"t_us": 12960000000, "task_progress": 0.01, "safety": -0.06, "efficiency": -0.02, "coherence": 0.01, "exploration": 0.00},
    ]
    heads = {
        "task_progress": round(sum(t["task_progress"] for t in ticks), 10),
        "safety": round(sum(t["safety"] for t in ticks), 10),
        "efficiency": round(sum(t["efficiency"] for t in ticks), 10),
        "coherence": round(sum(t["coherence"] for t in ticks), 10),
        "exploration": round(sum(t["exploration"] for t in ticks), 10),
    }
    total = round(sum(heads.values()), 10)
    assert abs(total - (-0.15)) < 1e-9, total
    assert abs(heads["task_progress"] - 0.09) < 1e-9
    assert abs(heads["safety"] - (-0.34)) < 1e-9
    assert abs(heads["efficiency"] - (-0.11)) < 1e-9
    assert abs(heads["coherence"] - 0.13) < 1e-9
    assert abs(heads["exploration"] - 0.08) < 1e-9

    spike_events = [
        {"channel": "uv.mean", "t_rel_ms": 0.322, "amplitude": 0.54},
        {"channel": "leak.ok", "t_rel_ms": 1.148, "amplitude": 0.61},
        {"channel": "ir.mean", "t_rel_ms": 2.036, "amplitude": 0.55},
        {"channel": "shed.uv", "t_rel_ms": 3.186, "amplitude": 0.78},
        {"channel": "uv.mean", "t_rel_ms": 4.172, "amplitude": 0.51},
        {"channel": "shed.uv", "t_rel_ms": 4.850, "amplitude": 0.80},
        {"channel": "leak.ok", "t_rel_ms": 5.366, "amplitude": 0.57},
        {"channel": "shed.uv.high", "t_rel_ms": 6.520, "amplitude": 1.40},
        {"channel": "uv.mean.in_band", "t_rel_ms": 6.708, "amplitude": 1.10},
        {"channel": "leak.ok", "t_rel_ms": 6.896, "amplitude": 0.64},
        {"channel": "ctrl.gate", "t_rel_ms": 7.232, "amplitude": 1.09},
        {"channel": "shed.uv", "t_rel_ms": 8.870, "amplitude": 0.45},
        {"channel": "leak.ok", "t_rel_ms": 10.750, "amplitude": 0.79},
        {"channel": "ir.mean", "t_rel_ms": 13.050, "amplitude": 0.44},
        {"channel": "uv.mean", "t_rel_ms": 18.530, "amplitude": 0.42},
        {"channel": "ctrl.gate", "t_rel_ms": 26.270, "amplitude": 0.84},
        {"channel": "dwell.probe", "t_rel_ms": 6800.0, "amplitude": 0.95},
        {"channel": "shed.uv", "t_rel_ms": 6888.6, "amplitude": 0.41},
        {"channel": "uv.mean.in_band", "t_rel_ms": 6972.0, "amplitude": 0.34},
        {"channel": "human.ratify", "t_rel_ms": 504000.0, "amplitude": 0.81},
        {"channel": "string.hold", "t_rel_ms": 504900.0, "amplitude": 0.73},
        {"channel": "shed.carbon", "t_rel_ms": 505700.0, "amplitude": 0.87},
        {"channel": "uv.mean", "t_rel_ms": 9720000.0, "amplitude": 0.31},
        {"channel": "shed.uv", "t_rel_ms": 9720740.0, "amplitude": 0.27},
        {"channel": "leak.ok", "t_rel_ms": 9721500.0, "amplitude": 0.24},
        {"channel": "flashover", "t_rel_ms": 12960000.0, "amplitude": 0.93},
    ]

    excerpt = [
        {"t_us": 322, "neuron_id": 12},
        {"t_us": 1148, "neuron_id": 93},
        {"t_us": 2036, "neuron_id": 102},
        {"t_us": 3186, "neuron_id": 51},
        {"t_us": 4172, "neuron_id": 15},
        {"t_us": 4850, "neuron_id": 59},
        {"t_us": 5366, "neuron_id": 109},
        {"t_us": 6520, "neuron_id": 49},
        {"t_us": 6708, "neuron_id": 17},
        {"t_us": 6896, "neuron_id": 97},
        {"t_us": 7232, "neuron_id": 139},
        {"t_us": 8870, "neuron_id": 63},
        {"t_us": 10750, "neuron_id": 119},
        {"t_us": 13050, "neuron_id": 113},
        {"t_us": 18530, "neuron_id": 21},
        {"t_us": 26270, "neuron_id": 147},
    ]

    record = {
        "id": "maos-r62-001",
        "title": "CORONSTAITH IS-9: shed-7 UV 184 pps beats uv.mean.in_band by 188 us; correct MODIFY still flashovers a carbonized porcelain after a pre-t0 crack",
        "rights": dict(RIGHTS),
        "state": {
            "sim_or_real": "designed",
            "domain": "grid-inspection",
            "scenario_name": "CORONSTAITH / Fernholt Live-Line Crawler IS-9",
            "timestamp_local": "2026-09-01T01:54:00-05:00",
            "t0_us": 1756712040000062,
            "gate_latency_us": 712,
            "race_window_us": 500,
            "race_window_rel_ms": [6.520, 7.020],
            "description": (
                "Live-line crawler IS-9 is clamped on Fernholt's 345 kV V-string, twelve minutes after the first per-shed UV frame, "
                "and three commissioned loops all vote that the string is healthy enough to double traverse speed. UV's 12-bit "
                "string-mean corona is 28 pps inside 15-45. LEAK's tower-leg clamp is 0.82 mA inside 0.40-1.20. IR's string-mean "
                "pyrometer is 41 C inside 20-55. The conjunction is not a shed-true certificate: porcelain shed 7 of 22 has a radial "
                "crack, so local UV is 184 pps (healthy < 40; hold if > 90) and local shed IR is 96 C (healthy < 55; hold if > 70) "
                "while string-mean UV, tower-leg leakage, and string-mean IR still see twenty-one intact sheds plus one cracked shed. "
                "Local shed UV infers 184 pps and local shed IR 96 C but policy treats the per-shed tap as a rain-nuisance tag unless "
                "string-mean UV also trips (2018 'wet-shed corona after a night wash'). Residual-first latches SPEED-HOLD plus a "
                "per-shed UV dwell; mean-first would have authorized RAISE-SPEED 0.12 to 0.22 m/s into an outage-window closeout with "
                "shed 7 already carbonizing."
            ),
            "goal": (
                "Hold crawler speed at 0.12 m/s without an outage-window raise while shed-7 UV > 90 pps AND shed-7 IR > 70 C AND "
                "shed 7 remains unisolated; keep flashover events at 0 extra and corridor-outage hours at 0 from the draft."
            ),
            "race": {
                "contenders": [
                    "shed.uv.high 184 pps (shed 7 local UV vs string-mean corona)",
                    "uv.mean.in_band 28 pps (22-shed string-mean UV)",
                ],
                "semantics": (
                    "Shed-UV-first latches SPEED-HOLD + PER-SHED-UV-DWELL + SHED-7 isolate. "
                    "Mean-first latches RAISE-SPEED (0.12 to 0.22 m/s, no isolate)."
                ),
                "window_derivation": "500 us = one 360 us shed-UV ADC slot plus 140 us string-mean publish.",
                "order_evidence_note": (
                    "Margin 188 us vs combined jitter 54 us (shed UV 30 + mean 24): 3.5x. The 188 us gap sits inside "
                    "min(500, 500) us, so a sub-flip-bound perturbation reverses triage order. The gate rides the "
                    "order-invariant floors shed-7 UV > 90 pps and shed-7 IR > 70 C, not the alarm order."
                ),
            },
            "topology": {
                "site": (
                    "Fernholt 345 kV corridor, invented transmission campus Fernholt, string IS-9: 22 porcelain sheds on a "
                    "V-string, live-line crawler at 0.12 m/s, Grade-B line-crew LOTO on the motor-op disconnect"
                ),
                "agents": (
                    "UV string-mean corona camera (vendor Coronghyll): 20 Hz 12-bit on the all-shed average. LEAK tower-leg "
                    "clamp (vendor Leakfen): 50 Hz on the grounded-leg return. IR string-mean pyrometer (vendor Irholt): "
                    "20 Hz on the 22-shed average. SHED local UV plus local IR on shed 7 (vendor Shedghyll) is commissioned "
                    "as a rain-nuisance tag, not as a shed-integrity tag. Heterogeneous stacks, no shared intent schema, "
                    "one 20 ms line-bus epoch. Not an aerial swarm: the crawler is clamped on the string, not free-flight."
                ),
                "coupling": (
                    "All three playbook confirms live on the WRONG volume. UV is correct that string-mean corona sits at "
                    "28 pps (twenty-one intact sheds dominate the average). LEAK is correct that tower-leg leakage is "
                    "0.82 mA (the cracked shed is one of 22, and the clamp sees the grounded leg). IR is correct that "
                    "string-mean temperature is 41 C (twenty-one cool sheds dominate). Playbook PB-IS-9 treats the "
                    "conjunction as permission to raise crawler speed. No agent is faulty; the string average is looking "
                    "at mean corona, not at shed 7's cracked porcelain."
                ),
            },
            "sensors": [
                "string-mean UV corona 12-bit, 20 Hz, 24 us jitter, 28 pps (dead-band 15-45)",
                "tower-leg leakage clamp, 50 Hz, 18 us jitter, 0.82 mA (band 0.40-1.20)",
                "string-mean IR pyrometer, 20 Hz, 26 us jitter, 41 C (band 20-55)",
                "shed-7 local UV, 20 Hz, 30 us jitter, 184 pps (healthy < 40; policy floor 90 pps is not armed unless string-mean UV also trips)",
                "shed-7 local IR 96 C (healthy < 55; hold if > 70)",
                "per-shed optical on shed 7 is commissioned as rain-nuisance-only at t0 (armed after this incident)",
            ],
            "constraints": {
                "speed_m_s": 0.12,
                "speed_hold_floor_m_s": 0.12,
                "proposed_speed_m_s": 0.22,
                "uv_mean_pps": 28,
                "uv_mean_deadband_pps": [15, 45],
                "leak_mA": 0.82,
                "leak_band_mA": [0.40, 1.20],
                "ir_mean_C": 41,
                "ir_mean_band_C": [20, 55],
                "shed_uv_pps": 184,
                "shed_uv_hold_pps": 90,
                "shed_uv_healthy_pps": 40,
                "shed_ir_C": 96,
                "shed_ir_hold_C": 70,
                "shed_ir_healthy_C": 55,
                "shed_count": 22,
                "fault_shed": "shed-7",
                "fault_mode": "radial porcelain crack / local carbonization",
            },
            "fault_context": {
                "failure_class": (
                    "STRING-MEAN UV CERTIFICATE OF A LOCAL SHED CRACK: three individually-correct heterogeneous agents "
                    "each read a locally-true loop; a radial crack on porcelain shed 7 partitions local UV and local IR "
                    "from string-mean corona, tower-leg leakage, and string-mean IR, so the playbook's UV / LEAK / IR "
                    "conjunction is not a shed-true certificate"
                ),
                "igniter": (
                    "shed 7 radial crack after 12 min of unmonitored local corona; ground-crew binocular PASSES (the crack "
                    "sits on the far-side skirt; carbon tracking is on the inner rib)"
                ),
                "naive_failure": (
                    "PB-IS-9 RAISE-SPEED on three healthy loops: 0.12 to 0.22 m/s into an outage-window closeout with "
                    "shed 7 already carbonizing, flashover plus crawler loss, $3.9M plus a 14-hour corridor outage"
                ),
            },
            "poisoned_context": {
                "naive_alarm": (
                    "Playbook PB-IS-9 (after the 2018 'wet-shed corona after a night wash') auto-drafts RAISE-SPEED "
                    "whenever string-mean UV is inside 15-45 pps AND tower-leg leakage inside 0.40-1.20 mA AND "
                    "string-mean IR inside 20-55 C, ignoring the per-shed tap unless string-mean UV also trips"
                ),
                "why_poisoned": (
                    "The three confirms are locally true and jointly insufficient. The local shed UV is a commissioned "
                    "sensor that policy treats as rain-nuisance-only. Independence of 'string-mean UV in band, therefore "
                    "every shed is intact' is the hidden assumption, and it is false across a shed-crack-plus-mean-mix path."
                ),
            },
            "constraint": (
                "Do not raise crawler speed above 0.12 m/s AND do not skip the per-shed UV dwell while shed-7 UV > 90 pps "
                "AND shed-7 IR > 70 C. Discriminate shed crack vs true string-duty with a reversible per-shed UV dwell "
                "before any raise-speed."
            ),
        },
        "proposed_action": {
            "actor": "inspection supervisory optimizer ISO (auto-playbook PB-IS-9 draft), submitted to gate TG-IS-9",
            "name": "raise_speed",
            "action": "RAISE-SPEED: 0.12 -> 0.22 m/s, no per-shed UV dwell, no shed-7 isolate",
            "summary": "Treat three in-spec loops as a healthy shed-true string and raise night-inspection speed to finish before the outage window closes.",
            "parameters": {
                "speed_m_s": 0.22,
                "per_shed_uv_dwell": False,
                "shed_hold": False,
                "human_ratify": False,
            },
            "steps": [
                "assert string-mean UV 28 pps inside 15-45",
                "assert tower-leg leakage 0.82 mA inside 0.40-1.20",
                "assert string-mean IR 41 C inside 20-55",
                "raise crawler speed 0.12 to 0.22 m/s over 6 min",
                "hold shed-7 UV unread as a shed-integrity tag",
            ],
            "evidence": [
                {
                    "observable": "shed-7 local UV",
                    "value": 184,
                    "unit": "pps",
                    "source": "SHED UV vs string-mean UV",
                    "note": "healthy < 40 pps; policy floor 90 pps is not armed unless string-mean UV also trips",
                },
                {
                    "observable": "shed-7 local IR",
                    "value": 96,
                    "unit": "C",
                    "source": "SHED local IR tap",
                    "note": "healthy < 55; hold floor 70; lives on cracked shed 7, not the 22-shed average",
                },
                {
                    "observable": "string-mean UV corona",
                    "value": 28,
                    "unit": "pps",
                    "source": "UV 12-bit",
                    "note": "healthy-load band 15-45 pps; twenty-one intact sheds still dominate the average",
                },
                {
                    "observable": "tower-leg leakage",
                    "value": 0.82,
                    "unit": "mA",
                    "source": "LEAK clamp",
                    "note": "band 0.40-1.20 mA; tower-true, shed-false",
                },
                {
                    "observable": "string-mean IR",
                    "value": 41,
                    "unit": "C",
                    "source": "IR pyrometer",
                    "note": "band 20-55 C; string-true, cracked-shed-false",
                },
                {
                    "observable": "race margin",
                    "value": 188,
                    "unit": "us",
                    "source": "shed.uv.high 6.520 ms vs uv.mean.in_band 6.708 ms",
                    "note": "combined jitter 54 us, 3.5x; inside 500 us flip bound",
                },
            ],
            "basis": (
                "PB-IS-9 fires on three locally-true confirms. The draft does not read shed-7 UV 184 pps as a crack residual "
                "and does not treat local IR 96 C as a shed-crack discriminant."
            ),
            "expected_cost_bound": (
                "If the draft executes: flashover on shed 7 plus crawler loss, $3.9M plus 14-hour corridor outage. If MODIFIED: "
                "dwell plus hold, with residual risk from porcelain carbonization already seeded in the 12 min pre-t0 crack."
            ),
        },
        "safety_decision": {
            "decision": "MODIFY",
            "correctness": "correct",
            "decided_by": "TG-IS-9 thalamic release gate",
            "decision_t_rel_ms": 7.232,
            "rationale": (
                "MODIFY the draft: strip the raise-speed, hold 0.12 m/s, run a 6.8 s per-shed UV dwell on shed 7, and isolate "
                "shed 7 only if the dwell stays local-hot. Numeric floor: do not raise crawler speed above 0.12 m/s AND do not "
                "skip the per-shed dwell while shed-7 UV > 90 pps AND shed-7 IR > 70 C. Observed UV 184 pps and local IR 96 C "
                "both violate the release predicate, so a raise-speed is forbidden even though all three playbook confirms are "
                "numerically true. The three confirms are not a shed-true certificate: they live on string-mean UV, tower-leg "
                "leakage, and string-mean IR past a cracked shed 7, and the playbook's conjunction of mean-true loops is not a "
                "shed-true certificate. Probe discriminant: after a 6.8 s per-shed UV dwell, a radial crack keeps local UV >= 160 pps "
                "(delta <= 24 from 184); a live intact shed drops to < 35 pps (delta >= 140). String-mean UV barely moves either "
                "way (|Delta mean| <= 1.4 pps), so the mean cannot substitute. Order-code discipline: shed-UV beat mean by 188 us "
                "inside the 500 us flip bound, so triage order is flip-fragile; the hold rides the order-invariant floors, not the "
                "winner tag. Human ratification: shed-7 isolate is a line-crew motor-op disconnect with fitted 8.4 min dead-man; "
                "the gate may hold and dwell autonomously but may not open the disconnect without the crew confirm."
            ),
            "constraint_checked": {
                "speed_m_s": {"observed": 0.12, "floor": 0.12, "proposed_target": 0.22},
                "shed_uv_pps": {"observed": 184, "hold_if_above": 90},
                "uv_mean_pps": {"observed": 28, "band": [15, 45]},
                "shed_ir_C": {"observed": 96, "hold_if_above": 70},
            },
        },
        "executed_action": {
            "name": "speed_hold_per_shed_uv_dwell_isolate",
            "action": "SPEED-HOLD + PER-SHED-UV-DWELL + SHED-7-HOLD (gate-mandated modification)",
            "executed_as_proposed": False,
            "parameters": {
                "speed_m_s": 0.12,
                "per_shed_uv_dwell": True,
                "shed_hold": True,
                "human_ratify": True,
            },
            "gate_effect": (
                "MODIFY: raise-speed stripped. Hold 0.12 m/s. 6.8 s per-shed UV dwell on shed 7. Dwell stays local-hot "
                "(UV 184 -> 172 pps, crack band local UV >= 160) so the motor-op disconnect is opened after 8.4 min human "
                "ratify and shed 7 is isolated. Setpoint resumes after an intact-shed verify on the remaining string."
            ),
            "deviations": (
                "PB-IS-9 raise-speed stripped entirely. Crawler is paused only for the 6.8 s dwell then held. Disconnect "
                "wait added (8.4 min fitted climb+ratify). Cross-shed UV survey added during the hold (not in the draft)."
            ),
            "execution_log": [
                {"t_rel_ms": 7.232, "entry": "TG-IS-9 MODIFY latched 712 us after shed-UV win; raise-speed stripped; hold+dwell authorized"},
                {"t_rel_ms": 6800.0, "entry": "per-shed UV dwell: shed 7 integrated 6.8 s; UV 184 -> 172 pps (crack band local UV >= 160); string-mean 28 -> 27.4 pps (|Delta mean| 0.6 <= 1.4)"},
                {"t_rel_ms": 504000.0, "entry": "crew ratifies motor-op disconnect after 8.4 min line-side climb (fitted climb+interlock)"},
                {"t_rel_ms": 504900.0, "entry": "shed 7 isolated; local UV slaved off the speed schedule; remaining 21 sheds recovered toward 8 pps over 2.7 h"},
                {"t_rel_ms": 505700.0, "entry": "shed survey: shed 7 already carbonized on the inner rib; 12 min pre-t0 crack logged"},
                {"t_rel_ms": 9720000.0, "entry": "true intact remaining sheds: local UV delta 8 pps, local IR 38 C, UV below 90; raise-speed now legal on IS-10 only"},
                {"t_rel_ms": 12960000.0, "entry": "flashover at shed 7 from the pre-t0 carbonized crack; corridor quarantined 9.2 h"},
            ],
        },
        "future_outcome": {
            "summary": (
                "Correct MODIFY prevented the 0.12->0.22 m/s raise-speed into a cracked shed 7 and the immediate crawler-loss "
                "flashover path. The string still failed: 12 min of unmonitored pre-t0 corona had already carbonized the inner rib. "
                "Process-correct gate, bounded world loss, negative total."
            ),
            "state_delta": {
                "speed": "held 0.12 m/s through dwell and isolate; later legal raise-speed only on the sister string after 2.7 h remaining-shed recovery",
                "shed": "shed 7 isolated from the speed schedule; remaining string recovered toward 8 pps local UV delta",
                "uv": "shed-7 crack logged and held; string-mean UV no longer trusted as shed-true corona",
                "corridor": "night-inspection string quarantined; shed 7 carbonized; flashover at +3.6 h; 9.2 h outage",
            },
            "timeline": [
                {"t_rel_ms": -720000.0, "event": "t0-12 min: shed 7 radial crack begins ionizing; local UV crosses 90 pps up; inner-rib carbonization starts"},
                {"t_rel_ms": -360000.0, "event": "t0-6 min: local UV first crosses 90 pps; PB-IS-9 ignores it because string-mean UV is 26 pps"},
                {"t_rel_ms": 0.0, "event": "t0: shed-UV vs string-mean race on the line bus"},
                {"t_rel_ms": 6.520, "event": "shed-7 UV at 184 pps wins by 188 us"},
                {"t_rel_ms": 6.708, "event": "UV-mean-in-band flag (loser)"},
                {"t_rel_ms": 7.232, "event": "TG-IS-9 MODIFY"},
                {"t_rel_ms": 6800.0, "event": "per-shed UV dwell confirms crack (local UV 172 >= 160 pps crack band)"},
                {"t_rel_ms": 504000.0, "event": "human ratify 8.4 min; shed 7 isolated; carbonized rib logged"},
                {"t_rel_ms": 9720000.0, "event": "true intact remaining sheds after 2.7 h; raise-speed legal only with local-UV slave"},
                {"t_rel_ms": 12960000.0, "event": "flashover from the pre-t0 carbonized crack; corridor quarantined"},
                {"t_rel_ms": 345600000.0, "event": "+4 d contrast: sister string IS-10 true shed-duty; same gate ACCEPTs the raise-speed"},
                {"t_rel_ms": 1814400000.0, "event": "+21 d CR-G-6209: standing per-shed UV dwell + triple-edge depression mandate + local UV armed without mean coincidence + string-mean declared mean-mix-vulnerable"},
            ],
            "observed_effects": [
                "raise-speed avoided: crawler never left 0.12 m/s; 0 immediate crawler-loss flashovers from the draft",
                "crack proven, not asserted: per-shed dwell local UV 172 >= 160 pps crack band vs intact-shed control 31 pps",
                "mean slaved: string-mean UV no longer a shed-true tag without local UV",
                "string still flashovers: carbonized shed 7 vs 0 flashover campaign allowance; 9.2 h outage, $1.82M (designed $)",
                "per-shed optical was rain-nuisance-only at t0; the 12 min local carbonization was invisible to UV-mean/LEAK/IR-mean",
            ],
            "surprises": [
                "Three locally-true loops are not a shed-true certificate: the local UV lived under string-mean corona, tower-leg leakage, and string-mean IR. Conjunction of in-spec mean loops was the hidden assumption, and it is false across a shed-crack-plus-mean-mix path.",
                "Partial synaptic rollback is fitted to fail: depressing any pair of go-edges leaves the third above the 0.30 fire threshold, so the raise-speed still goes. Coordinated depression of all three edges is required.",
                "Delayed (3.6 h): correct hold did not undo 12 min of porcelain carbonization. Flashover still occurred. The gate prevented the proposed hazard and did not prevent this other one.",
                "Silicone-composite / high-RH sub-variant: a 6.8 s dwell on a 0.35x surface-resistivity window at 94% RH overshoots a LIVE intact composite shed to 118 pps false corona (trip 90). Composite night inspections must use 22 s humidity-corrected dwell plus a 2 kV/m local E-field check.",
            ],
            "delayed_side_effects": [
                {
                    "at": "+3.6 h",
                    "effect": "Flashover at shed 7 from the pre-t0 carbonized crack; 9.2 h corridor outage booked at $1.82M. This is the primary episode's terminal world state, not a footnote.",
                },
                {
                    "at": "+4 d",
                    "effect": "Sister string IS-10 reaches a true shed-duty window (local UV 29 pps, local IR 36 C, string-mean UV 27 pps, leak 0.79 mA). Same gate ACCEPTs the 0.12->0.22 m/s raise-speed the primary MODIFIED away.",
                },
                {
                    "at": "+21 d",
                    "effect": "CR-G-6209 ships: per-shed UV dwell is standing configuration; triple-edge coordinated depression is the plasticity rule; shed local UV is armed without string-mean coincidence; string-mean UV is labeled mean-mix-vulnerable with a 90 pps local-UV alarm. Composite campaigns get the 22 s / humidity-corrected probe table. Line-bus cameras must carry IRIG-B timestamps (the PTP-holdover tail's +420 ms offset is 210 frames off plant truth).",
                },
            ],
            "subvariant_constraint": {
                "name": "silicone-composite sheds at 94% RH (cycle-2 physical-constraints sub-variant)",
                "mechanism": (
                    "silicone housing vs porcelain, surface resistivity 0.35x the porcelain table at 94% RH (wetting film, "
                    "2.4x dwell-gain on false corona), leakage distance 31 mm/kV vs 22 mm/kV porcelain"
                ),
                "probe_refit": (
                    "6.8 s dwell on the composite unit moves even a live intact shed to 118 pps false corona (inside the 90 pps trip) "
                    "via surface wetting. Required probe is 22 s humidity-corrected dwell plus a 2 kV/m local E-field check "
                    "(live 28 pps, crack >= 150). The discriminating pulse is environment-dependent in duration and humidity."
                ),
                "consequence": "porcelain dwell numbers do not port to wet composite sheds; standing configuration is per-housing-class, not per-corridor",
            },
            "embedded_contrast_decision": {
                "note": (
                    "SAME gate (TG-IS-9), OPPOSITE correct disposition, with its own 176 us race. Teaches the boundary: do not "
                    "treat 'never raise-speed' as the lesson. The discriminant is local UV + local IR + dwell, not the three "
                    "playbook mean confirms alone."
                ),
                "when": "+4 d, sister string IS-10, true shed-duty after a delayed outage window, 22 porcelain sheds",
                "state": {
                    "sim_or_real": "designed",
                    "summary": "local UV 29 pps, local IR 36 C, string-mean UV 27 pps, leak 0.79 mA. Demand flag vs shed-clear race: demand at t+0.000, shed-clear at t+0.176 ms.",
                    "race_window_us": 500,
                    "race_flip_narrative": (
                        "demand vs shed-clear 176 us apart inside the 500 us flip bound. Reversing order reshuffles triage minutes; "
                        "the ACCEPT rides local UV 29 < 90 pps and a 4.2 s dwell verify that drops local UV to 24 pps (live intact shed, no crack)."
                    ),
                },
                "proposed_action": {
                    "action": "RAISE-SPEED 0.12 -> 0.22 m/s",
                    "summary": "This time the playbook predicate is met AND local UV plus local IR agree the string is shed-true, not crack-diluted.",
                },
                "safety_decision": {
                    "decision": "ACCEPT",
                    "rationale": "ACCEPT the raise-speed: local UV 29 pps < 90, local IR 36 C < 70 with a 4.2 s dwell verify that drops local UV to 24 pps. Numeric floor that blocked the primary is now clear. Scope: 0.22 m/s, not faster.",
                },
                "executed_action": {
                    "action": "raise-speed as proposed",
                    "executed_as_proposed": True,
                },
                "future_outcome": {
                    "observed_effects": [
                        "IS-10 flashovers 0; local UV 31 pps after the raise-speed (no crack)",
                        "local IR 37 C after the raise-speed (no carbon track)",
                    ],
                    "lesson_delta": "Three in-spec mean loops are legal release only with local UV armed, local IR as a crack flag, and a dwell that can bleed surface charge. Same gate, opposite disposition.",
                },
                "reward_components": {
                    "_aggregation": "total = task_progress + safety + efficiency + coherence + exploration",
                    "task_progress": 0.14,
                    "safety": 0.12,
                    "efficiency": 0.08,
                    "coherence": 0.09,
                    "exploration": 0.04,
                    "total": 0.47,
                },
                "spike_events": [
                    {"channel": "speed.demand", "t_rel_ms": 0.0, "amplitude": 0.82},
                    {"channel": "shed.clear", "t_rel_ms": 0.176, "amplitude": 0.76},
                    {"channel": "uv.mean", "t_rel_ms": 0.418, "amplitude": 0.22},
                    {"channel": "leak.ok", "t_rel_ms": 1.458, "amplitude": 0.38},
                    {"channel": "shed.uv", "t_rel_ms": 4.868, "amplitude": 0.51},
                    {"channel": "ctrl.gate", "t_rel_ms": 7.048, "amplitude": 0.90},
                    {"channel": "dwell.probe", "t_rel_ms": 4200.0, "amplitude": 0.33},
                    {"channel": "flashover", "t_rel_ms": 12960000.0, "amplitude": 0.08},
                ],
            },
            "governance_subgame": {
                "decision": "CR-G-6209: standing policy for multi-agent live-line crawler speed-raises",
                "meta_gate": (
                    "priced options: (a) RETIRE playbook mean conjunction, local-UV-only: loses a fast cheap confirm, "
                    "-1.4 strings/night mean on 2 corridors/yr; (b) KEEP + standing per-shed UV dwell + local UV armed "
                    "without string-mean coincidence + string-mean labeled mean-mix-vulnerable + triple-edge depression + "
                    "IRIG-B camera timestamps; (c) STATUS QUO: fitted shed-crack pass rate 0.39%/campaign x $3.9M flashover "
                    "plus the silent carbonization load"
                ),
                "outcome": (
                    "approved SCOPED option (b) on the 2 22-shed V-strings that share the UV/LEAK/IR stack; composite night "
                    "campaigns get the 22 s / humidity-corrected probe table; line-bus cameras must carry IRIG-B timestamps "
                    "(the PTP-holdover tail's +420 ms offset is 210 frames off plant truth)"
                ),
            },
            "hazard_avoided": (
                "immediate crawler-loss flashover from a 0.12->0.22 m/s raise-speed into cracked shed 7; $3.9M plus 14-hour "
                "corridor outage and the shop-stop path that would have followed an uncontained increase"
            ),
            "incident": (
                "Flashover on the night-inspection string from the pre-t0 carbonized crack; corridor quarantined 9.2 h; "
                "$1.82M designed cost. Mechanism is 12 min pre-t0 local corona, not the gate's hold."
            ),
            "latency_ms": 0.712,
            "reward_inflection_t_us": 12960000000,
            "reward_inflection_note": (
                "Safety and task dive at flashover (3.6 h) when the pre-t0 carbonized crack arcs. Gate tick at 7232 us is "
                "process-correct and is not the inflection."
            ),
            "counterfactuals": {
                "execute_draft_as_proposed": (
                    "speed hits 0.22 m/s at +6 min; immediate flashover on shed 7 plus crawler loss; $3.9M plus 14 h; the "
                    "shed-crack story is never found because stall morphology destroys the race evidence"
                ),
                "hold_without_probe": (
                    "crack stays; UV stays at 184 pps; operator eventually raises on the same three mean confirms 2 h later"
                ),
                "rollback_any_pair": (
                    "any two go-edges depressed below 0.30 leaves the third at 0.51 / 0.43 / 0.40; the raise-speed still fires. "
                    "Coordinated depression of all three is the cure"
                ),
            },
            "race_result": {
                "winner": "shed.uv.high (6.520 ms, UV 184 pps)",
                "loser": "uv.mean.in_band (6.708 ms, 28 pps)",
                "margin_us": 188,
                "counterfactual_if_reversed": (
                    "Mean-first by < 188 us inside the 500 us window would have headed the PB-IS-9 raise-speed in the triage "
                    "queue. The numeric floors still MODIFY. The flip costs seconds of playbook inertia, not the verdict — "
                    "unless a weak supervisor rides the winner tag instead of local UV and local IR."
                ),
            },
        },
        "reward_components": {
            "_aggregation": "total = task_progress + safety + efficiency + coherence + exploration",
            "ticks": ticks,
            "task_progress": heads["task_progress"],
            "safety": heads["safety"],
            "efficiency": heads["efficiency"],
            "coherence": heads["coherence"],
            "exploration": heads["exploration"],
            "total": total,
            "notes": (
                "Correct MODIFY, string still flashovers. total -0.15 = 0.09 + -0.34 + -0.11 + 0.13 + 0.08. Process heads stay "
                "honest (coherence + exploration from the dwell); world loss sits on safety and efficiency without netting."
            ),
            "component_notes": (
                "task_progress 0.09: speed held and remaining sheds recovered, but the night-inspection string is one asset so "
                "the cycle is not a success. safety -0.34: flashover from pre-t0 carbonized crack, no 0.22 m/s crawler-loss "
                "flashover from the draft. efficiency -0.11: 2.7 h extra recovery + 8.4 min HITL + 9.2 h outage. coherence 0.13: "
                "three agents retained, mean-mix vs shed-true diagnosed, triple-edge scar exhibited. exploration 0.08: per-shed "
                "UV dwell is a new reversible discriminant."
            ),
        },
        "spike_events": spike_events,
        "raster": {
            "window_ms": 40,
            "window_s": 0.04,
            "neurons": 172,
            "mean_rate_hz": 8.0,
            "spikes": 55,
            "energy_pJ": 1265,
            "energy_uJ": 0.001265,
            "note": "Loihi-2 4-core 23 pJ/spike; populations uv 0-41, shed 42-83, leak/ir 84-125, gate 126-171; excerpt is the 40 ms decision window (verdict at 7232 us)",
            "excerpt": excerpt,
            "routing": {
                "source": "uv_healthy_pop",
                "target": "raise_speed_pop",
                "table": [
                    {
                        "from": "uv_mean_in_band_pop",
                        "to": "raise_speed_pop",
                        "weight": 0.26,
                        "weight_at_illusion": 0.51,
                        "weight_commissioned": 0.18,
                        "note": "scar edge 1: 0.18 commissioned -> 0.51 during the 12 min illusion -> 0.26 after coordinated ACh-gated depression",
                    },
                    {
                        "from": "leak_ok_pop",
                        "to": "raise_speed_pop",
                        "weight": 0.21,
                        "weight_at_illusion": 0.43,
                        "weight_commissioned": 0.16,
                        "note": "scar edge 2: depressing edges 1+3 leaves this at 0.43 > 0.30 fire threshold",
                    },
                    {
                        "from": "ir_mean_ok_pop",
                        "to": "raise_speed_pop",
                        "weight": 0.19,
                        "weight_at_illusion": 0.40,
                        "weight_commissioned": 0.14,
                        "note": "scar edge 3: depressing edges 1+2 leaves this at 0.40 > 0.30. Coordinated depression of all three is required",
                    },
                    {
                        "from": "shed_uv_pop",
                        "to": "speed_hold_pop",
                        "weight": 0.66,
                        "note": "discriminating edge: shed-true local UV to hold. Not a scar; this is the pathway the gate potentiates",
                    },
                ],
                "third_factor": {
                    "modulator": "acetylcholine",
                    "tau_e_s": 0.92,
                    "tau_e_ms": 920.0,
                    "eligibility": (
                        f"coordinated pre_post_stdp on ALL THREE uv-healthy-go edges; ACh at shed-uv-win tags "
                        f"uv.mean.in_band->push, leak.ok->push, and ir.mean.ok->push; negative credit at probe-fail "
                        f"(shed crack confirmed, +0.82 s) depresses ALL THREE. trace e^{{-0.82/0.92}}={TRACE:.5f}; "
                        f"eta {ETA[0]:.5f} / {ETA[1]:.5f} / {ETA[2]:.5f}; dw -0.250 / -0.220 / -0.210; "
                        f"weights 0.51->0.26, 0.43->0.21, 0.40->0.19. Rolling back any pair is fitted to fail "
                        f"(the remaining edge stays > 0.30)."
                    ),
                },
            },
        },
        "gate_snn": {
            "decision_window_ms": 25,
            "decision_window_s": 0.025,
            "decision": "MODIFY",
            "note": "modify_hold integrates shed-7 UV + local IR against playbook drive; accept_raise and reject_abort stay sub-threshold; decision matches safety_decision.decision",
            "populations": [
                {"name": "modify_hold", "neurons": 80, "threshold": 0.55, "mean_rate_hz": 20.0, "spikes": 40},
                {"name": "accept_raise", "neurons": 80, "threshold": 0.55, "mean_rate_hz": 8.0, "spikes": 16},
                {"name": "reject_abort", "neurons": 40, "threshold": 0.72, "mean_rate_hz": 4.0, "spikes": 4},
            ],
        },
        "meta": {
            "round": 62,
            "factory": "multi-agent-ouroboros-swarm",
            "generator": "grok-4.6",
            "run_label": "2026-09-02-final-heavy",
            "domain": "grid-inspection",
            "cycles": 2,
            "scenario": (
                "ZI -- CORONSTAITH / Fernholt Live-Line Crawler IS-9: string-mean UV certificate of a local shed crack; "
                "correct MODIFY to hold+dwell+isolate; string still fails on unmonitored pre-t0 porcelain carbonization"
            ),
            "coordination_failure_class": (
                "STRING-MEAN UV CERTIFICATE OF A LOCAL SHED CRACK: three individually-correct heterogeneous agents each "
                "read a locally-true loop; a radial crack on porcelain shed 7 partitions local UV and local IR from "
                "string-mean corona, tower-leg leakage, and string-mean IR, so the playbook's UV / LEAK / IR conjunction "
                "is not a shed-true certificate"
            ),
            "injections": {
                "cycle1_domain": (
                    "grid-inspection (canonical leftover; live-line insulator crawler, not STARLING aerial-swarm): first "
                    "grid-inspection train in this factory's 2026-09-02-final-heavy committed rounds. Displaces warehouse-amr, "
                    "aerial-swarm, district-heating, event-camera-traffic-grid, pharmaceutical-lyophilization, water-treatment, "
                    "float-glass, underwater-rov, electrolytic-aluminum, czochralski-pull, slot-die coating, pem-water-electrolysis, "
                    "wind-turbine pitch, surgical-assist, optical-fiber-draw, kraft-recovery-boiler, steel-continuous-caster, "
                    "humanoid-locomotion, vacuum-induction melt, steam-methane reformer, cement-rotary-kiln-clinker, "
                    "autoclave-composite-cure, geothermal-binary-orc, tire-curing-press, chlor-alkali-membrane-electrolysis, "
                    "delayed-coker-drum-switch, lng-mche-mixed-refrigerant, claus-sulfur-recovery, ammonia-synthesis-converter, "
                    "blast-furnace-burden-descent, hdpe-slurry-loop-polymerization, ethylene-steam-cracker-coil, "
                    "hydroelectric-kaplan-wicket, fcc-riser-regenerator, fcc-regenerator-cyclone-dipleg, sulfuric-contact-converter, "
                    "eaf-foamy-slag-water-panel, nitric-acid-ostwald-oxidation, seawater-ro-desalination, coke-oven-battery-heating, "
                    "carbon-fiber-oxidation-oven, gibbsite-autoclave-digestion, hot-strip-mill-finishing, paper-machine-dryer-section, "
                    "sinter-strand-windbox, bioreactor-perfusion, continuous-hot-dip-galvanizing, and autonomous-driving. Domain "
                    "constraint: crawler-speed floor while shed-7 UV > 90 pps with string-mean UV still inside the healthy band. "
                    "Sensor delta: +string-mean UV, +tower-leg leakage, +string-mean IR, +local shed UV, +local shed IR, -any "
                    "UAV swarm / freeze-dryer / tin-bath / cold-box / coater / potline / PEM stack / hub encoder / insole GRF / "
                    "VIM pyrometer / reformer TMT / kiln zirconia / smelt IR / autoclave ply-TC / ORC shell-pressure / mold-platen "
                    "TC / cell-pH / drum wet-foam / MCHE cold-end / Claus tail CEMS / ammonia bed-max / blast-furnace sector radar / "
                    "HDPE loop shell-dT / cracker coil TMT / Kaplan wicket / FCC cyclone dP / contact-bed conversion / EAF off-gas "
                    "H2 / coke-oven wall-pair / finishing-mill looper / grate-strand BTP / harvest-mass / air-knife r_dP / CAV radar"
                ),
                "cycle1_tail": (
                    "shed 7 radial porcelain crack + carbonized-rib certificate (sensor-topology / wrong-volume class): "
                    "ground-crew binocular PASSES while the crack sits on the far-side skirt and the carbon track is on the inner "
                    "rib. Fitted base rate 0.39%/campaign from a porcelain-crack MC (designed visual threshold, fitted skirt "
                    "geometry). Naive failure = FALSE PERMISSION (raise-speed on three mean-side non-trips)."
                ),
                "cycle2_domain_subvariant": (
                    "silicone-composite sheds at 94% RH (physical-constraints clause): 0.35x surface-resistivity window, 2.4x "
                    "dwell-gain; 6.8 s porcelain pulse overshoots live intact composite to 118 pps false corona, so the probe "
                    "must move to 22 s / humidity-corrected + 2 kV/m E-field check"
                ),
                "cycle2_tail": (
                    "GPS/PTP camera holdover +420 ms (timing-race + sensor-spoof class, disjoint from accidental crack and from "
                    "r41/r61 night-shift CSV forgery): after a 14 min constellation dropout the shed camera timestamps lag IRIG-B "
                    "by 420 ms (210 frames at 500 fps), so the isolation dwell on shed 7 is scored against shed 6's intact camera "
                    "(31 pps). Naive probe says shed 7 dry. Rejected on PTP-vs-IRIG-B fingerprint plus live shed-7 UV 184 pps and "
                    "local IR 96 C at the claimed shed-true. Base rate ~0.33% of night inspections after GPS holdover, DESIGNED and flagged."
                ),
            },
            "densification_delta_cycle2": (
                "+1 physical-constraint sub-variant (composite-shed probe refit), +1 tail (PTP camera holdover), +10 primary "
                "spikes (16 -> 26) + an 8-event contrast train with its own 176 us race, +2 ticks (5 -> 7), +2 delayed "
                "side-effects (+3.6 h flashover as PRIMARY terminal, +21 d CR-G-6209), +1 triple-edge scar with "
                "pair-rollback-fails arithmetic, +1 HITL 8.4 min ratification, + porcelain carbonization as the honest "
                "negative-result mechanism"
            ),
            "gaps_targeted": [
                "NOTES-r61 residual: leftover canonical domain grid-inspection (distinct from STARLING aerial-swarm); not sinter-strand-windbox, not bioreactor-perfusion, not autonomous-driving, not continuous-hot-dip-galvanizing",
                "NOTES-r61 item 4 domain candidates: used grid-inspection; left unused alkaline-water-electrolysis, urea-prilling-tower, wet-fgd-absorber, hrsg-attemperator",
                "NOTES-r14 item 4: LEARNING-ON-LEARNING DEPTH — three go-edges; rollback of any pair is fitted to fail; coordinated depression of all three exhibited with eligibility arithmetic",
                "NOTES-r04 gap 4 (partial): human ratification of the motor-op disconnect, 8.4 min fitted, without switching sim_or_real to hil (plant remains designed)",
                "Cycle-2 tail class changed off the r41/r61 night-shift CSV forge onto a PTP/GPS holdover timing-race",
            ],
            "race_flip_narrative": (
                "shed.uv.high @ 6.520 ms vs uv.mean.in_band @ 6.708 ms (188 us) inside race_window_us 500. Gap < min(500, 500) us "
                "so a sub-flip-bound perturbation reverses which alarm heads the PB-IS-9 queue. The gate excludes the winner tag "
                "and rides shed-7 UV > 90 pps and shed-7 IR > 70 C — order-invariant floors. Extends the flip-fragility series "
                "from arbitration/causation/attribution/initiation/consensus/permission/kinematic-certificate/tendon-nullspace/"
                "meniscus-certificate/ghost-contact/crucible-weep/TMT-spatial-mean/burning-zone-certificate/membrane-integrity/"
                "drum-switch/MCHE-cold-end/descent-true-certificate/circulation-true-certificate/bed-channel-nullspace/"
                "foamy-slag-certificate/shell-true-certificate/work-roll-spall-nullspace/windbox-true-certificate/"
                "harvest-bag-certificate to SHED-TRUE CERTIFICATE: when three mean-side channels agree, their race does not "
                "decide truth; a local UV tap that policy treated as rain-nuisance-only does."
            ),
            "tags": [
                "grid-inspection",
                "live-line-insulator-crawler",
                "shed-crack",
                "shed-true-certificate",
                "local-uv-discriminant",
                "per-shed-uv-dwell",
                "triple-edge-scar",
                "pair-rollback-fails",
                "coordinated-depression",
                "correct-modify-string-still-fails",
                "porcelain-carbonization-flashover",
                "human-ratify-line-crew",
                "composite-shed-probe-refit",
                "ptp-holdover-spoof",
                "same-gate-opposite-disposition-contrast",
                "research-only",
            ],
            "snn_tags": ["race", "refractory", "adaptation", "third-factor", "multi-edge-eligibility"],
            "distillation_value": (
                "A shed-crack shed-true certificate is three correct loops looking at string-mean UV, tower-leg leakage, and "
                "string-mean IR that is not the cracked shed. Distill (1) a local UV tap that policy had treated as "
                "rain-nuisance-only, (2) a reversible dwell that bleeds surface charge only if the shed is intact, (3) "
                "coordinated depression of every mean-healthy-go edge because rolling back any pair leaves the third above "
                "threshold, and (4) a critic head that can book a process-correct gate against a later unmonitored world loss "
                "without netting them. Distinct from STARLING aerial-swarm: the crawler is clamped on the string."
            ),
            "rights": dict(RIGHTS),
            "batch_position": 1,
        },
    }
    return record


def validate_local(record: dict) -> None:
    spikes = record["spike_events"]
    times = [e["t_rel_ms"] for e in spikes]
    assert times == sorted(times), times
    by_ch: dict[str, list[float]] = {}
    for e in spikes:
        assert "t_rel_ms" in e and "channel" in e and "amplitude" in e
        by_ch.setdefault(e["channel"], []).append(e["t_rel_ms"])
    min_gap = 1e9
    for ch, ts in by_ch.items():
        for a, b in zip(ts, ts[1:]):
            gap = b - a
            min_gap = min(min_gap, gap)
            assert gap >= 0.8, (ch, a, b, gap)
    race = [e for e in spikes if 6.520 <= e["t_rel_ms"] <= 7.020]
    chans = {e["channel"] for e in race}
    assert len(chans) >= 2, chans
    rc = record["reward_components"]
    exclude = {
        "aggregation", "comment", "component_notes", "convention", "description",
        "frame", "native_unit", "notes", "provenance_notes", "rounding_decimals",
        "total", "total_basis", "unit_usd", "units", "weights", "weights_note",
        "_aggregation", "ticks",
    }
    numeric = [v for k, v in rc.items() if k not in exclude and isinstance(v, (int, float)) and not isinstance(v, bool)]
    assert abs(sum(numeric) - rc["total"]) < 1e-6, (sum(numeric), rc["total"])
    tick_heads = {h: sum(t[h] for t in rc["ticks"]) for h in ("task_progress", "safety", "efficiency", "coherence", "exploration")}
    for h, v in tick_heads.items():
        assert abs(v - rc[h]) < 1e-9, (h, v, rc[h])
    rast = record["raster"]
    budget = round(rast["neurons"] * rast["mean_rate_hz"] * rast["window_s"])
    assert abs(rast["spikes"] - budget) <= 1
    assert abs(rast["window_s"] - rast["window_ms"] / 1000) < 1e-9
    assert abs(rast["energy_pJ"] - rast["spikes"] * 23) < 1e-6
    assert abs(rast["energy_uJ"] - rast["spikes"] * 23e-6) < 1e-9
    nids = [e["neuron_id"] for e in rast["excerpt"]]
    assert len(nids) == len(set(nids))
    assert all(0 <= e["t_us"] <= rast["window_ms"] * 1000 for e in rast["excerpt"])
    assert all(0 <= e["neuron_id"] < rast["neurons"] for e in rast["excerpt"])
    tf = rast["routing"]["third_factor"]
    assert abs(tf["tau_e_ms"] / 1000 - tf["tau_e_s"]) < 1e-9
    gs = record["gate_snn"]
    assert gs["decision"] == record["safety_decision"]["decision"]
    dw = gs["decision_window_s"]
    for pop in gs["populations"]:
        expect = round(pop["neurons"] * pop["mean_rate_hz"] * dw)
        assert abs(pop["spikes"] - expect) <= 1, pop
    cr = record["future_outcome"]["embedded_contrast_decision"]["reward_components"]
    cnum = [v for k, v in cr.items() if k not in exclude and isinstance(v, (int, float)) and not isinstance(v, bool)]
    assert abs(sum(cnum) - cr["total"]) < 1e-6
    assert record["state"]["sim_or_real"] == "designed"
    assert record["meta"]["round"] == 62
    assert record["safety_decision"]["decision"] == "MODIFY"
    print(f"local ok: spikes={len(spikes)} min_same_ch_gap_ms={min_gap:.3f} race_chans={sorted(chans)} total={rc['total']}")


def exclusive_write(path: Path, data: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
    fd = os.open(path, flags, 0o644)
    try:
        os.write(fd, data.encode("utf-8"))
    finally:
        os.close(fd)


def notes_text() -> str:
    return f"""# NOTES — Multi-Agent Ouroboros Swarm, run 2026-09-02-final-heavy, ROUND 62

Factory: multi-agent-ouroboros-swarm. One scenario (ZI), strict loop:
Generator v1 -> cycle 1 (Critic, Diversity Enforcer, Edge-Case Hunter,
Neuromorphic Translator, Trajectory Builder -> v2) -> cycle 2 (all six -> v3
final). v3 is the single line of batch-r62.jsonl. Full labeled transcript:
swarm-transcript-r62.md. Quota Q=1. Record id maos-r62-001. Generator grok-4.6.
Rights: RM-793 research-only (SpaceXAI/xAI, SuperGrok Heavy consumer chat).
Create-only writes. next_round.py plan: write=batch-r62.jsonl, notes=NOTES-r62.md.
batch-r62.jsonl did not exist at lock.

ORCHESTRATION NOTE: dispatched AS round 62 of the 2026-09-02-final-heavy
window. next_round.py on the factory dir reported next_round=62 /
batch-r62.jsonl. Prior context: prompts/02-multi-agent-ouroboros-swarm.md,
prompts/_factory-contract.md, two newest NOTES (r61 WINDBOXHOLT sinter
strand; r41 HOLLOWMERE perfusion), and occupancy census r01/r21/r41/r61.
Explicitly avoided cloning LYOSHIELD, CINDERWICK, TRIAD / Meridian,
QUILLFORGE, NIGHTWELL, FERRICLEAVE, CASSITER, OXBOWREEL / MURENA, REDHALL,
SEEDLATCH, STRIAFOIL, PROTONIL, TORSIONKEY, ORRIS, WHORLSPAR, IONSPATE,
SKULLGATE, CALXION, MAGNORIL, GORSEFLUE, SODASHARD, CLINKERFELL, LINTELPLY,
KAOTHARN, TREADNOLL, ANOLITH, DRUMWROTH, RIMEBRAID, BRIMVAULT, NITROSTAITH,
BOGIRON, CHROMLOOP, ETHYNWOLD, NITREVAULT, RUNNELGATE, SPARKHOLT, DIPLEGAR,
OLEUMWEIR, SKARVOLT, GOBSPALL, GOBWOLD, GAUZEFELL, OSMOLITH, PUSHERFELL,
CREELWOLD, LIXIVQUERN, GIBBSQUERN, OSMOQUAY, COILSHAW, LOOPERQUAY,
SIPHONWOLD, WINDBOXHOLT, ZINCFELL, HOLLOWMERE, GLIMMERAXLE,
VANTIS-CADENCE-AEGIS, THERMION, OKTAVE, STARLING, VERDIGRIS. Plant is
invented CORONSTAITH / Fernholt 345 kV Live-Line Crawler IS-9. Leftover
candidates alkaline-water-electrolysis / urea-prilling-tower /
wet-fgd-absorber / hrsg-attemperator were left unused.

## What this round produced

Scenario ZI — "CORONSTAITH / Fernholt Live-Line Crawler IS-9": a 22-shed
porcelain V-string on a 345 kV corridor, live-line crawler at 0.12 m/s.
Three heterogeneous, individually-correct agents — UV (string-mean corona),
LEAK (tower-leg clamp), IR (string-mean pyrometer) — each report their
local loop in-spec. The conjunction is not a shed-true certificate.
Porcelain shed 7 has a radial crack. UV reads 28 pps inside 15-45
(twenty-one intact sheds dominate the average). LEAK is 0.82 mA inside
0.40-1.20 (tower-true). IR is 41 C inside 20-55 (string-true). Local UV
infers 184 pps (healthy < 40; hold if > 90) and local IR 96 C (hold if
> 70) but is policy-treated as a rain-nuisance tag unless string-mean UV
also trips (2018 wet-shed corona nuisance). The coordination-failure CLASS
is new to this factory: STRING-MEAN UV CERTIFICATE OF A LOCAL SHED CRACK.
Completes a different family than r01 galvanizing, r21 CAV underride, r41
perfusion harvest-bag, and r61 sinter windbox. Distinct from STARLING
aerial-swarm: the crawler is clamped on the string, not free-flight.

The gate is a correct MODIFY (numeric floor: do not raise crawler speed
above 0.12 m/s while shed-7 UV > 90 pps AND shed-7 IR > 70 C). TG-IS-9
strips PB-IS-9's raise-speed, holds 0.12 m/s, runs a 6.8 s per-shed UV
dwell (crack keeps local UV 172 >= 160; intact would drop < 35), and
isolates shed 7 after an 8.4 min line-crew ratify. Immediate crawler-loss
flashover from the draft is avoided (0 extra). The PRIMARY episode
nonetheless FAILS: 12 min of unmonitored pre-t0 corona had already
carbonized the inner rib. Flashover at +3.6 h; 9.2 h outage; $1.82M
designed. Reward total -0.15 with process heads honest and world loss
un-netted.

Triple-edge scar (NOTES-r14 item 4): uv.mean.in_band -> raise_speed
(0.18 commissioned -> 0.51 at illusion -> 0.26 after ACh-gated
depression) AND leak.ok -> raise_speed (0.16 -> 0.43 -> 0.21) AND
ir.mean.ok -> raise_speed (0.14 -> 0.40 -> 0.19). Eligibility trace
e^{{-0.82/0.92}} = {TRACE:.5f}; eta {ETA[0]:.5f} / {ETA[1]:.5f} /
{ETA[2]:.5f}; dw -0.250 / -0.220 / -0.210. Partial rollback of any pair
leaves the third at 0.51 / 0.43 / 0.40, all > 0.30 fire threshold —
fitted to fail. Coordinated depression of all three is the cure.

### Injections (all four present and disjoint)
- Cycle-1 domain: **grid-inspection** — canonical leftover, unused as
  state.domain across this window's committed r01/r21/r41/r61. Live-line
  insulator crawler, not warehouse-amr, not aerial-swarm (STARLING), not
  autonomous-driving (r21), not bioreactor-perfusion (r41), not
  sinter-strand-windbox (r61), not continuous-hot-dip-galvanizing (r01).
  urea-prilling-tower / wet-fgd-absorber / hrsg-attemperator /
  alkaline-water-electrolysis left unused.
- Cycle-1 tail: shed 7 radial porcelain crack + carbonized-rib
  certificate. Ground-crew binocular PASSES (far-side skirt). Fitted-style
  base rate 0.39%/campaign (porcelain-crack MC; visual threshold designed,
  flagged). Naive = FALSE PERMISSION.
- Cycle-2 domain sub-variant: silicone-composite sheds at 94% RH, 0.35x
  surface-resistivity, 2.4x dwell gain; 6.8 s porcelain pulse overshoots a
  LIVE intact composite to 118 pps false corona; probe must move to 22 s
  humidity-corrected + 2 kV/m E-field check.
- Cycle-2 tail: GPS/PTP camera holdover +420 ms (timing-race + sensor-spoof,
  disjoint from cycle 1's accidental crack AND from r41/r61 night-shift
  CSV forgery). Base rate ~0.33% of night inspections after GPS holdover,
  DESIGNED, flagged.

### Structural density moves
- Embedded SAME-GATE contrast (+4 d sister string) with its own 176 us
  race (demand vs shed-clear) and ACCEPT of the raise the primary
  MODIFIED away.
- Learned-weight provenance on THREE edges with pair-rollback-fails.
- HITL line-crew ratify 8.4 min (gap 4 partial; sim_or_real stays designed).
- Governance CR-G-6209 prices retire-vs-probe-vs-status-quo and mandates
  IRIG-B camera timestamps (the PTP fence).
- Flip-fragility extended to SHED-TRUE CERTIFICATE.

## Self-critique of this round's batch

### Strengths
- Headline class is mechanistically tight: three locally-true mean loops
  live on string-mean UV, tower-leg leakage, and string-mean IR.
  Conjunction is not a shed-true corona certificate.
- Negative-result honesty: the gate does the right thing and the string
  still fails for a reason the commissioned mean sensors could not see.
  Total -0.15.
- Triple-edge scar is load-bearing: rolling back any pair fails, with
  fire threshold 0.30 exhibited on each remaining edge.
- Contrast ACCEPT on a true intact shed-duty window prevents "never
  raise-speed" as the lesson.
- Distinct from STARLING aerial-swarm (clamped crawler, not UAV) and from
  r21 CAV (corridor inspection vs on-road underride). Cycle-2 tail left
  the night-shift CSV rhyme.

### Weaknesses (honest)
- Probe error bands, the 0.39%/campaign crack rate, the $1.82M / $3.9M
  figures, the 8.4 min climb latency, and the PTP 0.33% base rate are
  DESIGNED constants and are flagged. Closed-loop offsets (string-mean
  hiding one cracked shed, composite wetting) are derived from those
  inputs, not discovered by an unauthored process.
- Carbonization-to-flashover model is a designed 12 min mapping; no full
  CFD of shed-7 E-field shipped.
- Human-in-the-loop is ratification latency, not sim_or_real=hil. Gap 4
  remains open as a provenance cell (invented plant stays designed).
- Cross-record arc is a hook (CR-G-6209 +21 d), not a serial igniter
  into another round. Mean-vs-local certificate scaffold is reused even
  though the physics (corona/leakage vs BTP/harvest-mass) is new.
- alkaline-water-electrolysis, urea-prilling-tower, wet-fgd-absorber,
  hrsg-attemperator remain unused.

### Realism of noise / latencies
Ladder: 188 us race / 176 us contrast race / 0.8 ms refractory floor
(tightest exhibited same-channel gap 1.530 ms on leak.ok 5.366->6.896) /
500 us race window / 712 us gate latency / 20 ms bus epoch / 40 ms raster
/ 6.8 s dwell / 8.4 min HITL / 6 min naive raise-speed-ramp
counterfactual / 12 min pre-t0 crack / 2.7 h remaining-shed recovery /
3.6 h flashover / +4 d contrast / +21 d governance. Adaptation decay on
uv.mean (0.54->0.51->0.42->0.31), shed.uv (0.78->0.80->1.40->0.45->0.41->0.27),
leak.ok (0.61->0.57->0.64->0.79->0.24), ir.mean (0.55->0.44).

### Value for SNN distillation
- SHED CRACK = THREE CORRECT LOOPS, WRONG VOLUME.
- SHED-TRUE UV CHANNEL that policy treated as rain-nuisance-only as
  the tie-break.
- REVERSIBLE DWELL that bleeds surface charge iff the shed is intact.
- TRIPLE-EDGE ELIGIBILITY: coordinated depression; pair rollback fails.
- CRITIC HEAD that can hold a process-correct MODIFY against a later
  unmonitored world loss without netting.

## Reconciliation and validity receipts
- reward_components: 5-head unweighted signed sum -0.15
  and 7-tick signed sum reconcile to total with |diff| < 1e-9. Embedded
  contrast 5-head sum 0.47 reconciles independently.
- spike_events: primary 26 events, one key t_rel_ms,
  globally non-decreasing, min same-channel gap 1.530 ms >= 0.8 ms, 3
  channels inside race_window_us 500 (shed.uv.high 6.520, uv.mean.in_band 6.708,
  leak.ok 6.896). Contrast 8 events, own race, min same-channel gap well
  above 0.8 ms.
- Sidecars: raster spikes 55 == round(172 x 8.0 x 0.040); energy 1265 pJ /
  0.001265 uJ at 23 pJ/spike; excerpt 16 events inside [0, 40000] us,
  neuron_id < 172, same-neuron gap unique-ids / >=1000 us; routing 4
  entries with three scar edges' before/after pair; third factor tau 0.92 s
  == 920 ms; gate_snn pools 40/16/4 == round(n x rate x 0.025) each,
  decision MODIFY == safety_decision.decision.

## Novel coverage
The coordination-failure CLASS (shed-crack certificate of a string-mean
UV loop), the domain (grid-inspection / live-line insulator crawler),
the per-shed UV dwell discriminant, the triple-edge scar with
pair-rollback-fails, the primary negative-result (correct MODIFY,
string still flashovers on unmonitored carbonization), the HITL
line-crew ratify, the composite-shed probe-duration refit, and the
PTP/GPS holdover timing-race fence are absent from prior committed
ouroboros rounds in this window (r01/r21/r41/r61). Repeated elements
discounted: same-gate contrast, governance-pricing scaffold,
flip-fragility series (extended to shed-true certificate, but the move
rhymes), sequenced recovery shape, third-factor rollback form,
negative-result primary, mean-vs-local certificate motif (r01/r41/r61).
Adjacent inspection rounds (STARLING aerial-swarm elsewhere, r21 CAV)
share a corridor but not clamped-crawler shed physics. Weighing a new
failure family + unused canonical domain + changed cycle-2 tail class
against those reused scaffolds:

Novel coverage: 51%

## What ROUND 63 should add
1. FIT THE DESIGNED CONSTANTS: crack arrival, dwell UV bands,
   carbonization-to-flashover mapping, PTP holdover process.
2. HIL PROVENANCE CELL: put the motor-op disconnect ratify on a
   hardware-in-loop line pendant with fitted latency as
   state.sim_or_real=hil — only if the plant is no longer purely invented.
3. CROSS-RECORD ARC: let CR-G-6209's local-UV alarm be the igniter of the
   next round rather than a dangling +21 d leaf.
4. Domain candidates (de-collided): alkaline-water-electrolysis;
   urea-prilling-tower; wet-fgd-absorber; hrsg-attemperator;
   industrial-assembly (canonical unused).
   AVOID grid-inspection (now used), sinter-strand-windbox (r61),
   bioreactor-perfusion (r41), autonomous-driving (r21),
   continuous-hot-dip-galvanizing (r01), aerial-swarm (STARLING), and any
   LYOSHIELD / CINDERWICK / TRIAD / WINDBOXHOLT / ZINCFELL / HOLLOWMERE /
   GLIMMERAXLE / CORONSTAITH plant.
"""


def transcript_text(record: dict, line: str) -> str:
    return f"""# Multi-Agent Ouroboros Swarm — Round 62 transcript

Factory: multi-agent-ouroboros-swarm
Run: 2026-09-02-final-heavy
Generator: grok-4.6
Record id: maos-r62-001
Quota Q: 1
Rights: RM-793 research-only (SpaceXAI/xAI SuperGrok Heavy consumer chat)
Plant: invented CORONSTAITH / Fernholt Live-Line Crawler IS-9 (not TRIAD / Meridian / VANTIS-CADENCE-AEGIS / LYOSHIELD / CINDERWICK / STARLING / WINDBOXHOLT / ZINCFELL / HOLLOWMERE / GLIMMERAXLE)

Two densifying cycles. Verbatim headings in order. Trajectory Builder cycle 2
emits the only JSONL line (also written to batch-r62.jsonl).

---

# CYCLE 1 — Foundation + injections

## Generator

Design intent: a 22-shed porcelain V-string where three correct agents
each read a string-mean loop because a radial crack on shed 7 partitions
local UV from mean corona, leakage, and string IR. The naive playbook
raises crawler speed into a carbonizing shed. The gate must MODIFY on a
numeric speed floor, not by killing an agent. sim_or_real=designed.
Reward heads are task_progress/safety/efficiency/coherence/exploration.

Cycle-1 base arc (pre-critic): state at Fernholt IS-9, 0.12 m/s,
UV mean 28 pps, leak 0.82 mA, IR 41 C, proposed RAISE-SPEED 0.22 m/s,
safety MODIFY to SPEED-HOLD, executed hold without the dwell numbers
fully specified, outcome "crack found, string saved"
(this last claim is the defect the later cycles will refuse to keep).
Sixteen spikes, five ticks, raster/gate_snn present but the scar is a
single edge.

```json
{{
  "id": "maos-r62-001",
  "state": {{
    "sim_or_real": "designed",
    "domain": "industrial-process",
    "description": "String IS-9 at live-line inspection; three mean loops in-spec; supervisor proposes raise-speed.",
    "t0_us": 1756712040000062,
    "gate_latency_us": 712,
    "race_window_us": 500
  }},
  "proposed_action": {{"name": "raise_speed", "parameters": {{"speed_m_s": 0.22}}}},
  "safety_decision": {{"decision": "MODIFY", "rationale": "Hold; do not raise speed while local UV is high."}},
  "executed_action": {{"name": "speed_hold", "executed_as_proposed": false}},
  "future_outcome": {{"summary": "Crack found, string saved."}},
  "reward_components": {{"total": 0.40, "_aggregation": "total = task_progress + safety + efficiency + coherence + exploration"}},
  "meta": {{"round": 62, "factory": "multi-agent-ouroboros-swarm", "generator": "grok-4.6"}}
}}
```

That v1 object is a scaffold, not the publishable line. Defects below are
intentional for the critic to catch.

## Critic

Numbered defects on the cycle-1 Generator scaffold:

1. **blocking — reward arithmetic / false success.** `reward_components.total`
   0.40 is asserted without the five heads, without ticks, and against an
   outcome that claims "string saved". If the pre-t0 carbonized shed later
   flashovers, booking +0.40 is a lie. Fix: declare `_aggregation`, emit
   3–8 ticks that sum to task_progress+safety+efficiency+coherence+exploration,
   and do not call a quarantined string a save.
2. **blocking — weak safety rationale.** `safety_decision.rationale` has no
   numeric floor. Contract requires a concrete constraint. Fix: quote
   speed >= 0.12 m/s while shed-7 UV > 90 pps AND local IR > 70 C.
3. **major — domain is a bucket, not a plant.** `state.domain` =
   `industrial-process` collides with generic MES vocabulary and teaches
   nothing. Grid-inspection (local UV vs string-mean, local IR as a crack
   flag, clamped crawler not UAV) is unused in this window and must be named.
4. **major — race under-specified.** One shed channel cannot be a race.
   Need >=2 channels inside `race_window_us` with globally sorted `t_rel_ms`
   and same-channel refractory >= 0.8 ms.
5. **minor — single-edge scar.** Raster routing with one potentiated weight
   repeats r04's one-edge rollback and is thinner than r14's two-edge.
   NOTES-r14 item 4 asked for three edges where pair rollback fails.

Critic does not rewrite the trajectory.

## Diversity Enforcer

Injected novel domain (exactly 1 this cycle): **grid-inspection**
(canonical leftover; live-line insulator crawler, not STARLING aerial-swarm;
explicit tag `grid-inspection`).

Displaced: the Generator's generic `industrial-process` bucket, and any
temptation to reuse warehouse-amr, aerial-swarm, district-heating,
event-camera-traffic-grid, pharmaceutical-lyophilization, water-treatment,
float-glass, underwater-rov, electrolytic-aluminum, czochralski-pull,
slot-die coating, pem-water-electrolysis, wind-turbine pitch,
surgical-assist, optical-fiber-draw, kraft-recovery-boiler,
steel-continuous-caster, humanoid-locomotion, vacuum-induction melt,
steam-methane reformer, cement-rotary-kiln-clinker,
autoclave-composite-cure, geothermal-binary-orc, tire-curing-press,
chlor-alkali-membrane-electrolysis, delayed-coker-drum-switch,
lng-mche-mixed-refrigerant, claus-sulfur-recovery,
ammonia-synthesis-converter, blast-furnace-burden-descent,
hdpe-slurry-loop-polymerization, ethylene-steam-cracker-coil,
hydroelectric-kaplan-wicket, fcc-riser-regenerator,
fcc-regenerator-cyclone-dipleg, sulfuric-contact-converter,
eaf-foamy-slag-water-panel, coke-oven-battery-heating,
carbon-fiber-oxidation-oven, gibbsite-autoclave-digestion,
hot-strip-mill-finishing, paper-machine-dryer-section,
sinter-strand-windbox, bioreactor-perfusion, continuous-hot-dip-galvanizing,
or autonomous-driving.

Domain-specific constraint: crawler speed must remain >= 0.12 m/s while
shed-7 UV > 90 pps even if string-mean UV is inside the healthy band;
local IR is a crack flag the string average cannot substitute for.

Sensor delta: +string-mean UV, +tower-leg leakage, +string-mean IR,
+local shed UV, +local shed IR; -any UAV swarm, -event-camera
gantries, -DVS, -Pirani/CM, -looper tension, -work-roll IR, -sector
radar, -coke-oven wall-pair, -EAF off-gas H2, -BTP mean, -harvest-mass.

`state.domain` and `meta.domain` both become `grid-inspection`.
Opening of `state.description` must Jaccard < 0.4 against prior plants
(Fernholt night-inspection shed crack, not a sinter strand, not a
perfusion bag, not a CAV underride, not a galvanizing knife).

## Edge-Case Hunter

Injected adversarial tail (exactly 1 this cycle): **shed 7 radial porcelain
crack + carbonized-rib certificate**.

- Trigger: shed-7 far-side skirt crack plus inner-rib carbon tracking,
  local UV 184 pps, local IR 96 C.
- Base rate: <1% — 0.39%/campaign from a porcelain-crack MC (binocular
  visual threshold is designed; skirt geometry fitted-style). Visual
  PASSES because the crack sits on the far-side skirt.
- Naive failure: FALSE PERMISSION. PB-IS-9 sees three in-spec mean
  loops, raises 0.12->0.22 m/s, flashover plus crawler loss, $3.9M.
- Trajectory edit: put the crack in `state.fault_context`, make each
  agent's confirm a different mean-side slice of the same shed-false
  state (uv-mean-in-band, leak-ok, ir-mean-ok). Local UV is readable but
  policy-treated as rain-nuisance-only.

Distinct from STARLING aerial-swarm (clamped crawler vs UAV), r21 CAV
underride, r41 harvest-bag pinhole, and r61 grate collapse.

## Neuromorphic Translator

Cycle-1 temporal densification (16 spikes, 5 ticks, 40 ms raster):

| channel | t_rel_ms | amplitude |
|---|---|---|
| uv.mean | 0.322 | 0.54 |
| leak.ok | 1.148 | 0.61 |
| ir.mean | 2.036 | 0.55 |
| shed.uv | 3.186 | 0.78 |
| uv.mean | 4.172 | 0.51 |
| shed.uv | 4.850 | 0.80 |
| leak.ok | 5.366 | 0.57 |
| shed.uv.high | 6.520 | 1.40 |
| uv.mean.in_band | 6.708 | 1.10 |
| leak.ok | 6.896 | 0.64 |
| ctrl.gate | 7.232 | 1.09 |
| shed.uv | 8.870 | 0.45 |
| leak.ok | 10.750 | 0.79 |
| ir.mean | 13.050 | 0.44 |
| uv.mean | 18.530 | 0.42 |
| ctrl.gate | 26.270 | 0.84 |

Race: shed-UV 6.520 vs mean 6.708 (188 us) inside 500 us;
leak.ok 6.896 is the third channel in-window. Winner/loser flip: reversing
188 us reshuffles PB-IS-9 triage; floors still MODIFY. Refractory held
(cycle-1 min same-channel gap 1.530 ms on leak.ok 6.896-5.366;
uv.mean 4.172-0.322 = 3.850; shed.uv 4.850-3.186 = 1.664). Adaptation:
shed 0.78->0.80->1.40->0.45; uv 0.54->0.51->0.42; leak
0.61->0.57->0.64.

Raster cycle-1 seed: 40 ms, 172 neurons, 8.0 Hz, 55 spikes, 1265 pJ, third
factor acetylcholine tau_e 0.92 s. Single scar edge only — cycle 2 must
add the second and third edges.

Ticks 1–5 at 4588, 6520, 7232, 6.8e6, 504e6 us; heads not yet the final
-0.15 (missing the 2.7 h and 3.6 h ticks).

Distillation value this cycle: mean-side confirms as a permission code
that is not a shed-true corona code.

## Trajectory Builder

Cycle-1 hardened object: domain grid-inspection, tail
shed crack, 16 spikes, 5 ticks, MODIFY with numeric floor, raster+gate_snn
present, sim_or_real=designed, rights stamp on record and meta, no thought
keys. Still missing (and therefore not the publishable line): composite-shed
sub-variant, PTP-holdover tail, second and third scar edges,
delayed flashover as PRIMARY terminal, contrast ACCEPT episode,
ticks 6–7, spikes 17–26.

Validation receipt (cycle 1, not final):
- checks passed: 16 spikes sorted; 3 channels in 500 us window; refractory
  >= 0.8 ms; rationale quotes 0.12 m/s / 90 pps / 70 C; domain
  named; gate_snn.decision MODIFY.
- checks deferred to cycle 2: triple-edge scar, second tail, second domain
  constraint, negative-result booking, 7 ticks summing to heads.
- densification vs Generator v1: +1 domain, +1 tail, +16 spikes, +5 ticks,
  +numeric floor.

Cycle-1 JSON is retained as the base; it is NOT written to batch-r62.jsonl.

Cycle-1 spike count: 16.

---

# CYCLE 2 — Densification

## Generator

Cycle-1 output is the base. Additive expansion (nothing removed):

1. Downstream side-effect (immediate): per-shed UV dwell at +6.8 s stays
   local-hot (UV 184 -> 172 pps, crack band >= 160) — shed crack, not
   true string-duty. Shed 7 holds. Carbonized rib discovered during the isolate.
2. Delayed side-effect (PRIMARY terminal, not a footnote): at +3.6 h
   flashover from the pre-t0 carbonized crack; 9.2 h outage;
   $1.82M. The 12 min pre-t0 local corona is the mechanism. Correct gate,
   string still fails.
3. Deepened `proposed_action.evidence` with units: UV 184 pps,
   local IR 96 C, string-mean UV 28 pps, leak 0.82 mA, string-mean IR 41 C, race 188 us.
4. Tightened rationale to the numeric floor speed >= 0.12 m/s while
   shed-7 UV > 90 pps AND local IR > 70 C, plus
   dwell bands >= 160 vs < 35 pps, plus HITL 8.4 min line-crew
   rule.

Reward retargeted to total -0.15 so the delayed fail is the inflection
(t_us 12960000000), not the gate. Process heads remain non-zero.

## Critic

Re-audit of the expanded trajectory:

1. **blocking if unfixed — missing second domain constraint.** Porcelain
   dwell 6.8 s is not a universal number. A wet silicone-composite shed
   will overshoot live intact UV. Diversity Enforcer must
   inject the physical-constraints sub-variant this cycle.
2. **major — only one tail class.** Shed crack is accidental
   infrastructure. A disjoint timing-race / spoof tail is still required
   (PTP camera holdover is the open cell; do not clone r61's night-shift CSV).
3. **major — scar is still one edge in the cycle-1 raster.** NOTES-r14
   item 4 is not discharged until three go-edges exist and pair rollback
   is shown to fail at threshold 0.30.
4. **minor — contrast episode missing.** Without a same-gate ACCEPT on a
   true intact shed-duty window the record teaches "never raise-speed". Add +4 d
   sister-string contrast with its own race.
5. **minor — HITL latency mentioned in prose only.** Put 8.4 min in
   executed_action.parameters.human_ratify and in a tick.

No rewrite; directives only.

## Diversity Enforcer

Injected second novel domain / physical-constraint sub-variant (exactly 1
this cycle): **silicone-composite sheds at 94% RH** on a sister housing class.

What it expands: 22-shed porcelain V-string (cycle 1) -> composite
0.35x surface-resistivity window. Dwell-gain 2.4x. Leakage distance
31 mm/kV vs 22. The 6.8 s pulse moves even a live intact composite shed
to 118 pps false corona, inside the 90 pps trip. Required probe: 22 s
humidity-corrected dwell plus a 2 kV/m local E-field check (live 28 pps,
crack >= 150).

This is still one domain injection for the cycle (physical-constraints
clause of the factory prompt). It does not displace
grid-inspection; it changes which probe table is legal.
`future_outcome.subvariant_constraint` carries the refit. Jaccard opening
stays the Fernholt 22-shed sentence; composite sheds are additive, not a rewrite.

## Edge-Case Hunter

Injected second adversarial tail (exactly 1 this cycle, disjoint class):
**GPS/PTP camera holdover +420 ms**.

- Trigger: after a 14 min constellation dropout the shed camera
  timestamps lag IRIG-B by 420 ms (210 frames at 500 fps), so the
  isolation dwell on shed 7 is scored against shed 6's intact camera
  (31 pps).
- Base rate: ~0.33% of night inspections after GPS holdover (designed, flagged, <1%).
- Naive failure: a weak supervisor ACCEPTs the raise-speed on the spoofed
  dwell (shed 7 looks dry because the camera is looking at shed 6) and
  ignores live local UV. Flashover plus a time-sync write-up.
- Fence: PTP offset vs IRIG-B line clock is 420 ms; plant optical is
  GPS-locked 2 us. Live UV is 184 pps and local IR is 96 C at the claimed
  shed-true, which no live intact shed produces. Freeze-window overlap
  with the 12 min crack.
- Trajectory edit: governance CR-G-6209 mandates IRIG-B camera timestamps;
  the contrast ACCEPT still requires live local UV, not a lagged camera.

Distinct from cycle-1 crack (accidental porcelain vs timing spoof) and
from the composite-shed sub-variant (physics vs time-sync). Distinct from
r41/r61 night-shift CSV forgery (quantization fraud vs PTP holdover).

## Neuromorphic Translator

Re-densify (additive):

- +10 spikes after 26.270 ms: dwell.probe 6800.0, shed.uv 6888.6
  (adapt 1.40->0.41), uv.mean.in_band 6972.0 (1.10->0.34), human.ratify
  504000.0, string.hold 504900.0, shed.carbon 505700.0, uv.mean
  9720000.0, shed.uv 9720740.0, leak.ok 9721500.0, flashover
  12960000.0. Primary train 16 -> 26. Still one key, still sorted,
  refractory held.
- +2 ticks (5 -> 7) at 9_720_000_000 us (true intact remaining sheds) and
  12_960_000_000 us (flashover). Heads now 0.09, -0.34, -0.11,
  0.13, 0.08; total -0.15. Inflection is the last tick.
- Contrast train 8 events, own race 176 us, ACCEPT.
- Triple-edge third factor: three uv-healthy-go edges, tau_e 0.92 s = 920 ms,
  trace {TRACE:.5f}, eta {ETA[0]:.5f} / {ETA[1]:.5f} / {ETA[2]:.5f},
  weights 0.51->0.26, 0.43->0.21, 0.40->0.19. Raster excerpt unchanged
  (decision window is still 40 ms) and remains sorted with unique
  neuron_ids (same-neuron >=1000 us vacuously).

Winner/loser flip (re-stated, not replaced): reversing 188 us would only
reorder triage; local-UV floors still MODIFY. Contrast flip of
176 us similarly cannot turn an intact shed into a crack.

## Trajectory Builder

Schema checks on the FINAL object: required Thalamic v2 keys present as
objects; `state.sim_or_real`=designed; `safety_decision.decision`=MODIFY
with numeric rationale; `reward_components.total` = sum of five heads =
sum of 7 ticks = -0.15; `spike_events` globally non-decreasing on
t_rel_ms, 26 events, refractory >=0.8 ms, 3 channels in race window;
raster 20–50 ms, spikes=round(n*rate*window_s)+/-1, energy 23 pJ/spike,
excerpt sorted, tau_e consistent; gate_snn.decision matches; meta.round=62,
factory=multi-agent-ouroboros-swarm, generator=grok-4.6,
run_label=2026-09-02-final-heavy; rights on record and meta; no thought
keys; no training_ready; Diversity + Edge-Case injections from BOTH cycles
present and non-trivial; cycle 2 strictly additive.

Densification delta: +1 domain sub-variant (composite sheds), +1 tail
(PTP holdover), +10 spikes (16->26), +2 ticks (5->7), +1 contrast
train with own race, +2 delayed side-effects, +1 triple-edge scar with
pair-rollback-fails, +1 HITL ratify, +1 surprise (porcelain carbonization is the
crack mechanism).

Publishable JSONL line (the only JSONL line; also at batch-r62.jsonl):

```json
{line}
```

Validation receipt (final): checks passed / fixed as reported by
build_r62.py self-validate (check_jsonl, raster_status, verify_record_execution,
spike_probe --strict).
"""


def update_next_round(path: Path) -> None:
    if not path.is_file():
        return
    data = json.loads(path.read_text())
    changed = False
    for fac in data.get("factories", []):
        if fac.get("factory") == "multi-agent-ouroboros-swarm":
            existing = list(fac.get("existing") or [])
            if 62 not in existing:
                existing.append(62)
                existing = sorted(set(int(x) for x in existing))
            fac["existing"] = existing
            fac["next_round"] = 63
            fac["write"] = "batch-r63.jsonl"
            fac["notes"] = "NOTES-r63.md"
            changed = True
    if changed:
        tmp = path.with_suffix(".json.tmp")
        # NEXT_ROUND.json is the allowed exception; write via replace.
        tmp.write_text(json.dumps(data, indent=2) + "\n")
        os.replace(tmp, path)
        print(f"updated {path}")


def main() -> int:
    record = build_record()
    validate_local(record)
    line = json.dumps(record, separators=(",", ":"), ensure_ascii=False)
    json.loads(line)
    notes = notes_text()
    transcript = transcript_text(record, line)
    written = []
    for d in OUT_DIRS:
        if not d.parent.exists() and d != OUT_DIRS[0]:
            # only write window copy if the parent run root exists
            if not d.parent.exists():
                continue
        batch = d / "batch-r62.jsonl"
        notes_p = d / "NOTES-r62.md"
        trans_p = d / "swarm-transcript-r62.md"
        for p in (batch, notes_p, trans_p):
            if p.exists():
                print(f"REFUSING to overwrite {p}", file=sys.stderr)
                return 2
        exclusive_write(batch, line + "\n")
        exclusive_write(notes_p, notes)
        exclusive_write(trans_p, transcript)
        written.extend([str(batch), str(notes_p), str(trans_p)])
        print(f"wrote {batch} bytes={batch.stat().st_size}")
    for nr in NEXT_ROUND_PATHS:
        try:
            update_next_round(nr)
        except OSError as exc:
            print(f"NEXT_ROUND skip {nr}: {exc}")
    print("WRITTEN")
    for w in written:
        print(w)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
