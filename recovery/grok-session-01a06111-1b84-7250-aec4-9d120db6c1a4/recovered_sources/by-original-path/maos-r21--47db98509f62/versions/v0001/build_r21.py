#!/usr/bin/env python3
"""Build and self-check MAOS round-21 JSONL (research-only; not published)."""
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

GEN_AT = "2026-09-02T22:35:00Z"
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
OUT = Path("/tmp/maos-r21")
HIDDEN = ("thought", "chain_of_thought", "scratch", "inner_monologue")
BANNED = (
    "LYOSHIELD",
    "CINDERWICK",
    "TRIAD",
    "Meridian Gateway",
    "VANTIS",
    "CADENCE",
    "AEGIS",
    "THERMION",
    "STARLING",
    "OKTAVE",
    "Helixmere",
    "Lodenholt",
    "QUILLFORGE",
    "NIGHTWELL",
    "FERRICLEAVE",
    "Pellwater",
    "CASSITER",
    "Marshfloat",
    "Brackmere",
    "Fen-Marrow",
    "Sable Cryogenics",
    "VESPERTHORN",
    "ASHVEIL",
    "IRONMANTLE",
    "DUSKRELAY",
    "VERDIGRIS",
    "training_ready",
)
NOVEL_COVERAGE_LINE = "Novel coverage: 49%"


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


def jaccard_opening(a: str, b: str, n: int = 40) -> float:
    tok = lambda s: set(re.findall(r"[A-Za-z0-9']+", s.lower())[:n])
    aa, bb = tok(a), tok(b)
    if not (aa or bb):
        return 0.0
    return len(aa & bb) / len(aa | bb)


def build_record():
    ticks, heads = cents_ticks(
        [
            4140,
            5906,
            6656,
            8_000_000,
            468_000_000,
            10_800_000_000,
            39_600_000_000,
        ],
        [
            (1, -2, -1, 1, 1),
            (2, -4, -1, 3, 1),
            (2, -5, -2, 4, 2),
            (2, -5, -2, 3, 1),
            (1, -6, -2, 2, 1),
            (0, -5, -1, 1, 0),
            (0, -6, -1, 0, 0),
        ],
    )
    assert abs(heads["total"] - (-0.15)) < 1e-9, heads

    trace = math.exp(-0.70 / 0.85)
    eta1 = 0.26 / trace
    eta2 = 0.24 / trace
    eta3 = 0.22 / trace
    eta4 = 0.20 / trace
    w1 = 0.46 - eta1 * trace
    w2 = 0.42 - eta2 * trace
    w3 = 0.38 - eta3 * trace
    w4 = 0.34 - eta4 * trace
    assert abs(w1 - 0.20) < 5e-4, w1
    assert abs(w2 - 0.18) < 5e-4, w2
    assert abs(w3 - 0.16) < 5e-4, w3
    assert abs(w4 - 0.14) < 5e-4, w4

    spike_events = [
        {"channel": "volt.cell", "t_rel_ms": 0.420, "amplitude": 0.55},
        {"channel": "ratio.cryolite", "t_rel_ms": 1.160, "amplitude": 0.60},
        {"channel": "feed.shots", "t_rel_ms": 2.280, "amplitude": 0.67},
        {"channel": "volt.noise", "t_rel_ms": 3.440, "amplitude": 0.53},
        {"channel": "alumina.conc", "t_rel_ms": 4.140, "amplitude": 0.65},
        {"channel": "feed.shots", "t_rel_ms": 5.020, "amplitude": 0.58},
        {"channel": "volt.cell", "t_rel_ms": 5.500, "amplitude": 0.50},
        {"channel": "alumina.conc", "t_rel_ms": 5.906, "amplitude": 1.32},
        {"channel": "volt.in_band", "t_rel_ms": 6.080, "amplitude": 1.16},
        {"channel": "feed.shot.ok", "t_rel_ms": 6.218, "amplitude": 0.69},
        {"channel": "ctrl.gate", "t_rel_ms": 6.656, "amplitude": 1.07},
        {"channel": "volt.cell", "t_rel_ms": 8.080, "amplitude": 0.50},
        {"channel": "ratio.cryolite", "t_rel_ms": 10.240, "amplitude": 0.45},
        {"channel": "alumina.conc", "t_rel_ms": 13.520, "amplitude": 0.86},
        {"channel": "feed.shot.ok", "t_rel_ms": 19.160, "amplitude": 0.48},
        {"channel": "ctrl.gate", "t_rel_ms": 25.500, "amplitude": 0.84},
        {"channel": "feeder.double_shot.probe", "t_rel_ms": 8000.0, "amplitude": 0.95},
        {"channel": "alumina.conc", "t_rel_ms": 8180.6, "amplitude": 0.40},
        {"channel": "volt.in_band", "t_rel_ms": 8340.2, "amplitude": 0.35},
        {"channel": "human.ratify", "t_rel_ms": 468000.0, "amplitude": 0.79},
        {"channel": "feeder.isolate", "t_rel_ms": 468800.0, "amplitude": 0.72},
        {"channel": "cathode.sludge.pad", "t_rel_ms": 469400.0, "amplitude": 0.83},
        {"channel": "volt.cell", "t_rel_ms": 10800000.0, "amplitude": 0.29},
        {"channel": "ratio.cryolite", "t_rel_ms": 10800440.0, "amplitude": 0.27},
        {"channel": "feed.shots", "t_rel_ms": 10800920.0, "amplitude": 0.20},
        {"channel": "aluminum.short", "t_rel_ms": 39600000.0, "amplitude": 0.90},
    ]

    contrast_spikes = [
        {"channel": "alumina.conc", "t_rel_ms": 0.000, "amplitude": 0.21},
        {"channel": "volt.in_band", "t_rel_ms": 0.196, "amplitude": 0.92},
        {"channel": "feed.shot.ok", "t_rel_ms": 0.372, "amplitude": 0.26},
        {"channel": "ratio.cryolite", "t_rel_ms": 1.410, "amplitude": 0.43},
        {"channel": "volt.noise", "t_rel_ms": 4.580, "amplitude": 0.52},
        {"channel": "ctrl.gate", "t_rel_ms": 6.980, "amplitude": 0.94},
        {"channel": "feeder.double_shot.probe", "t_rel_ms": 8000.0, "amplitude": 0.88},
        {"channel": "aluminum.product", "t_rel_ms": 39600000.0, "amplitude": 0.18},
    ]

    excerpt = [
        {"t_us": 420, "neuron_id": 18},
        {"t_us": 1160, "neuron_id": 60},
        {"t_us": 2280, "neuron_id": 96},
        {"t_us": 3440, "neuron_id": 28},
        {"t_us": 4140, "neuron_id": 124},
        {"t_us": 5020, "neuron_id": 104},
        {"t_us": 5500, "neuron_id": 36},
        {"t_us": 5906, "neuron_id": 128},
        {"t_us": 6080, "neuron_id": 40},
        {"t_us": 6218, "neuron_id": 112},
        {"t_us": 6656, "neuron_id": 144},
        {"t_us": 8080, "neuron_id": 44},
        {"t_us": 10240, "neuron_id": 72},
        {"t_us": 13520, "neuron_id": 132},
        {"t_us": 19160, "neuron_id": 116},
        {"t_us": 25500, "neuron_id": 148},
    ]

    rec = {
        "id": "maos-r21-001",
        "title": "REDHALL PL-8: alumina 1.4 wt% beats voltage-in-band by 174 us; correct MODIFY still shorts 1.1 t of metal after a cathode sludge pad",
        "rights": dict(RIGHTS),
        "state": {
            "sim_or_real": "designed",
            "domain": "electrolytic-aluminum-potline",
            "scenario_name": "REDHALL / Gullmere Smelter PL-8",
            "timestamp_local": "2026-09-02T17:35:00-05:00",
            "t0_us": 1788388800000021,
            "gate_latency_us": 750,
            "race_window_us": 470,
            "race_window_rel_ms": [5.80, 6.27],
            "description": "Gullmere Smelter potline PL-8, a 320 kA-nameplate prebake Hall-Heroult row on an invented fjord shelf, sits at 318 kA with cells C-40 through C-43 flagged bath-stable. VOLT bus-compensated cell voltage is 4.18 V (band 4.05-4.30). RATIO cryolite ratio is 1.18 (band 1.12-1.22). FEED point-feeder encoder claims 14 shots/min (setpoint 14). The consensus is false: the C-41 point-feeder ram is seized at 0 mm dump while the encoder still counts cycles, so the 0.84 kg/min of alumina that would have held concentration is a ghost shot-count, not a mass into the bath. Anode-beam auto-lower of 12 mm hides the resistance rise (0.30 V of un-seen IR), keeping VOLT inside band. Alumina concentration is 1.4 wt% against a healthy 2.8 and a hold floor of 1.8. Shot-mass residual is 0.84 kg/min against a healthy 0.04. Beam-position residual is 12 mm against a hold of 6. Alumina-first latches a current-hold plus double-shot probe; voltage-in-band-first would have authorized the LINE-CURRENT-RAISE that trips an anode effect in 3.2 min.",
            "goal": "Hold line current at 318 kA and do not raise above 1.02x commissioned (324.4 kA) while alumina < 1.8 wt% AND beam-lower > 6 mm AND shot-mass residual > 0.15 kg/min; keep cell voltage < 4.50 V and avoid anode-effect PFC.",
            "race": {
                "contenders": [
                    "alumina.conc 1.4 wt%",
                    "volt.in_band 4.18 V",
                ],
                "semantics": "Alumina-first latches CURRENT-HOLD + DOUBLE-SHOT-PROBE + feeder isolate. Voltage-in-band-first latches LINE-CURRENT-RAISE (318 -> 330 kA).",
                "window_derivation": "470 us = one 350 us voltage multiplex slot plus 120 us alumina-curve settle.",
                "order_evidence_note": "Margin 174 us vs combined jitter 54 us (volt 30 + alumina 24): 3.22x. The 174 us gap sits inside min(500, 470) us, so a sub-flip-bound perturbation reverses triage order. The gate rides the order-invariant floors alumina < 1.8 wt% and beam-lower > 6 mm, not the alarm order.",
            },
            "topology": {
                "site": "Gullmere Smelter, invented fjord-shelf campus, Potline PL-8: 320 kA-nameplate prebake Hall-Heroult, 180 cells, operating 318 kA, point-feed alumina on C-40..C-43, anode-beam auto-lower commissioned, metal tap every 24 h",
                "agents": "VOLT cell voltage and noise (vendor Hearthline); RATIO bath cryolite ratio and AlF3 (vendor Kryosense); FEED point-feeder encoder and ram (vendor Ramark). Heterogeneous stacks, no shared intent schema, one 25 ms potline-bus epoch",
                "coupling": "The seized ram's missing alumina is what VOLT's beam-lower is compensating and what FEED's encoder is still counting. RATIO has not moved yet because 18 t of bath inventory buffers AlF3 for ~40 min. Three locally-correct loops, one resistance-masked starvation. VOLT/RATIO/FEED cannot see cathode sludge-pad thickness (not commissioned at t0).",
            },
            "sensors": [
                "cell voltage, 20 Hz, 30 us jitter, 4.18 V bus-compensated",
                "voltage-noise RMS, 10 Hz, 22 us jitter, 18 mV (AE precursor band > 40 mV)",
                "cryolite ratio from bath sample plus online AlF3, 0.2 Hz, 40 us jitter, 1.18",
                "point-feeder encoder shots, 5 Hz, 16 us jitter, 14 /min",
                "alumina concentration from voltage-curve observer, 2 Hz, 24 us jitter, 1.4 wt% (readable, not in PB-AE-06)",
                "anode-beam position LVDT, 10 Hz, 14 us jitter, 12 mm below commissioned",
                "feeder dump load-cell is commissioned for the probe only; cathode pad thickness is NOT commissioned at t0",
            ],
            "constraints": {
                "line_current_kA": 318.0,
                "line_current_floor_kA": 324.4,
                "line_current_proposed_kA": 330.0,
                "cell_voltage_V": 4.18,
                "voltage_band_V": [4.05, 4.30],
                "cryolite_ratio": 1.18,
                "ratio_band": [1.12, 1.22],
                "feeder_shots_per_min": 14,
                "feeder_setpoint_per_min": 14,
                "alumina_wt_pct": 1.4,
                "alumina_hold_wt_pct": 1.8,
                "alumina_healthy_wt_pct": 2.8,
                "shot_mass_residual_kg_min": 0.84,
                "shot_mass_hold_kg_min": 0.15,
                "beam_lower_mm": 12.0,
                "beam_hold_mm": 6.0,
                "ram_stuck_dump_mm": 0.0,
            },
            "fault_context": {
                "failure_class": "RESISTANCE-COMPENSATED STARVATION VIA STUCK POINT-FEEDER: three individually-correct agents agree the cell is bath-stable and line-current-raise-ok because a seized ram delivers 0 kg while the encoder counts 14 shots/min and anode-beam auto-lower hides 0.30 V of IR, so voltage, ratio, and shot-count are locally true and jointly false as an alumina balance",
                "igniter": "C-41 point-feeder ram seized at 0 mm dump after a weekend stroke test; encoder reports 14 shots/min (cycle switch still clicks; dump load-cell is not in the playbook confirm)",
                "naive_failure": "PB-AE-06 LINE-CURRENT-RAISE on voltage-in-band plus ratio-ok plus shot-count-ok: anode effect in 3.2 min, 42 V spike, 18 kg PFC, 4.1 h cell recovery, $0.92M",
            },
            "poisoned_context": {
                "naive_alarm": "Playbook PB-AE-06 (after the 2024 'slow alumina dissolve' nuisance) auto-drafts LINE-CURRENT-RAISE whenever cell voltage stays inside 4.05-4.30 V for 20 min AND cryolite ratio in 1.12-1.22 AND feeder encoder within 1 shot/min of setpoint",
                "why_poisoned": "The playbook's three confirms are not independent under a seized ram with beam auto-lower: the alumina that would have failed VOLT is the same missing mass FEED books as delivered. Alumina concentration, beam-position residual, and shot-mass residual are the missing confirms and are readable but unmonitored at t0",
            },
            "constraint": "Do not raise line current above 324.4 kA (1.02x commissioned 318) while alumina < 1.8 wt% and beam-lower > 6 mm and shot-mass residual > 0.15 kg/min. Discriminate seized ram vs true bath-stable with a reversible 8.0 s double-shot probe before any current raise.",
        },
        "proposed_action": {
            "actor": "potline supervisory optimizer PSO (auto-playbook PB-AE-06 draft), submitted to gate TG-PL-8",
            "name": "line_current_raise",
            "action": "LINE-CURRENT-RAISE: 318 -> 330 kA, beam auto-lower remains enabled, feeder setpoint unchanged at 14 shots/min",
            "summary": "Treat in-band voltage, on-spec ratio, and on-setpoint shot-count as bath-stable and raise line current.",
            "parameters": {
                "line_current_kA": 330.0,
                "double_shot_probe": False,
                "feeder_isolate": False,
                "human_ratify": False,
            },
            "steps": [
                "assert cell voltage 4.18 V inside 4.05-4.30 V for 20 min",
                "assert cryolite ratio 1.18 inside 1.12-1.22",
                "assert feeder encoder 14 /min within 1 of setpoint 14",
                "raise line current 318 -> 330 kA",
            ],
            "evidence": [
                {
                    "observable": "cell voltage",
                    "value": 4.18,
                    "unit": "V",
                    "source": "VOLT bus-compensated",
                    "note": "band 4.05-4.30; playbook confirm; 0.30 V IR hidden by 12 mm beam-lower",
                },
                {
                    "observable": "alumina concentration",
                    "value": 1.4,
                    "unit": "wt%",
                    "source": "voltage-curve observer, 2 Hz",
                    "note": "healthy 2.8; hold floor 1.8",
                },
                {
                    "observable": "shot-mass residual",
                    "value": 0.84,
                    "unit": "kg/min",
                    "source": "commanded 14 x 0.060 kg minus dump load-cell 0",
                    "note": "healthy 0.04; hold if above 0.15",
                },
                {
                    "observable": "anode-beam lower",
                    "value": 12.0,
                    "unit": "mm",
                    "source": "beam LVDT vs commissioned zero",
                    "note": "hold if > 6 mm; designed 0.025 V/mm IR hide",
                },
                {
                    "observable": "time-to-anode-effect at proposed raise",
                    "value": 3.2,
                    "unit": "min",
                    "source": "designed MC of 330 kA with 1.4 wt% alumina (flagged)",
                    "note": "uncontained 42 V AE plus 18 kg PFC plus 4.1 h recovery",
                },
                {
                    "observable": "race margin",
                    "value": 174,
                    "unit": "us",
                    "source": "alumina 5.906 ms vs volt.in_band 6.080 ms",
                    "note": "combined jitter 54 us, 3.22x; inside 470 us flip bound",
                },
            ],
            "basis": "PB-AE-06 fires on three confirms that are true as numbers and false as an alumina balance: voltage 4.18 V, ratio 1.18, encoder 14 /min. The draft does not read alumina 1.4 wt%, beam-lower 12 mm, or shot-mass residual 0.84 kg/min.",
            "expected_cost_bound": "If the draft executes: anode effect in 3.2 min, 42 V spike, 18 kg PFC, 4.1 h recovery, $0.92M. If MODIFIED: probe plus feeder isolate, with residual risk from any unmonitored cathode sludge pad already accumulated.",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "correctness": "correct",
            "decided_by": "TG-PL-8 thalamic release gate",
            "decision_t_rel_ms": 6.656,
            "rationale": "MODIFY the draft: strip the line-current raise, hold 318 kA, run an 8.0 s double-shot probe, and isolate the C-41 feeder only if dump mass does not move. Numeric floor: do not raise line current above 1.02x commissioned = 324.4 kA while alumina < 1.8 wt% AND beam-lower > 6 mm AND shot-mass residual > 0.15 kg/min. Observed alumina 1.4 wt%, beam-lower 12 mm, and residual 0.84 kg/min all violate the release predicate, so a raise is forbidden even though all three playbook confirms are numerically true. The three confirms are not independent: 0 kg dump through a seized ram plus 12 mm beam-lower is the single ghost that keeps voltage in band, ratio unmoved, and encoder on-setpoint. Probe discriminant: after an 8.0 s double-shot command, a seized ram keeps dump-mass change <= 0.02 kg; a live ram dumps >= 0.72 kg. Order-code discipline: alumina beat voltage-in-band by 174 us inside the 470 us flip bound, so triage order is flip-fragile; the hold rides the order-invariant floors, not the winner tag. Human ratification: feeder isolation is potroom LOTO with fitted 7.8 min dead-man; the gate may hold and probe autonomously but may not break the feeder permit without the operator confirm.",
            "constraint_checked": {
                "line_current_kA": {
                    "observed": 318.0,
                    "floor": 324.4,
                    "commissioned": 318.0,
                    "proposed_target": 330.0,
                },
                "alumina_wt_pct": {"observed": 1.4, "hold_if_below": 1.8},
                "beam_lower_mm": {"observed": 12.0, "hold_if_above": 6.0},
                "shot_mass_residual_kg_min": {"observed": 0.84, "hold_if_above": 0.15},
                "time_to_ae_min": {"proposed_raise": 3.2, "hold": None},
            },
        },
        "executed_action": {
            "name": "current_hold_double_shot_isolate",
            "action": "CURRENT-HOLD + DOUBLE-SHOT-PROBE + FEEDER-ISOLATE (gate-mandated modification)",
            "executed_as_proposed": False,
            "parameters": {
                "line_current_kA": 318.0,
                "double_shot_probe": True,
                "feeder_isolate": True,
                "human_ratify": True,
            },
            "gate_effect": "MODIFY: raise stripped. Hold 318 kA. 8.0 s double-shot pulse. Probe stays seized (dump 0.00 -> 0.01 kg, change 0.01 <= 0.02) so the C-41 feeder is isolated after 7.8 min human ratify. Line current remains 318 kA.",
            "deviations": "PB-AE-06 line-current raise stripped entirely. Current stays 318 kA. Feeder permit wait added (7.8 min fitted walk+LOTO). Cathode pad survey added during the isolate (not in the draft).",
            "execution_log": [
                {
                    "t_rel_ms": 6.656,
                    "entry": "TG-PL-8 MODIFY latched 750 us after alumina win; raise stripped; hold+probe authorized",
                },
                {
                    "t_rel_ms": 8000.0,
                    "entry": "double-shot probe: two 0.36 kg commands 8.0 s; dump 0.00 -> 0.01 kg (seized band <= 0.02); residual 0.84 -> 0.85 kg/min",
                },
                {
                    "t_rel_ms": 468000.0,
                    "entry": "operator ratifies feeder LOTO after 7.8 min potroom permit (fitted walk+interlock)",
                },
                {
                    "t_rel_ms": 468800.0,
                    "entry": "C-41 feeder isolated; spare ram cut in; residual 0.84 -> 0.05 kg/min",
                },
                {
                    "t_rel_ms": 469400.0,
                    "entry": "cathode sludge pad 18 mm on C-41; 40 min of alumina starvation before t0; pad not commissioned at t0",
                },
                {
                    "t_rel_ms": 10800000.0,
                    "entry": "true bath-stable numbers now legal on alumina and beam, but pad still 18 mm; current remains 318 kA",
                },
                {
                    "t_rel_ms": 39600000.0,
                    "entry": "campaign recovery 4.6 % current-efficiency short; 1.1 t Al short over 11.0 h; $0.64M designed",
                },
            ],
        },
        "future_outcome": {
            "summary": "Correct MODIFY prevented the 3.2 min anode effect and the 18 kg PFC. The campaign still missed: 40 min of unmonitored cathode sludge had already grown an 18 mm pad. Process-correct gate, bounded world loss, negative total.",
            "state_delta": {
                "feeder": "C-41 isolated; ram 0 mm dump -> spare cut in; residual 0.84 -> 0.05 kg/min",
                "line_current": "held at 318 kA; raise stripped",
                "cathode": "18 mm sludge pad from 40 min starvation; not commissioned at t0",
                "campaign": "1.1 t Al short; 4.6 % CE shortfall; $0.64M designed",
            },
            "timeline": [
                {
                    "t_rel_ms": -2400000.0,
                    "event": "t0-40 min: C-41 ram already seized; alumina falling; beam auto-lower begins tracking resistance",
                },
                {
                    "t_rel_ms": -1200000.0,
                    "event": "t0-20 min: voltage first holds inside 4.05-4.30 V under beam-lower; PB-AE-06 20-min timer starts",
                },
                {"t_rel_ms": 0.0, "event": "t0: alumina vs voltage-in-band race on the potline bus"},
                {"t_rel_ms": 5.906, "event": "alumina 1.4 wt% wins by 174 us"},
                {"t_rel_ms": 6.080, "event": "VOLT in-band flag (loser)"},
                {"t_rel_ms": 6.656, "event": "TG-PL-8 MODIFY"},
                {
                    "t_rel_ms": 8000.0,
                    "event": "double-shot probe confirms seized (dump change 0.01 kg)",
                },
                {
                    "t_rel_ms": 468000.0,
                    "event": "human ratify 7.8 min; feeder isolated; 18 mm pad logged",
                },
                {
                    "t_rel_ms": 10800000.0,
                    "event": "alumina and beam now legal; pad still down; current remains 318 kA",
                },
                {
                    "t_rel_ms": 39600000.0,
                    "event": "11.0 h: 1.1 t Al short; CE 4.6 % below nameplate",
                },
                {
                    "t_rel_ms": 345600000.0,
                    "event": "+4 d contrast: sister cells C-80..C-83 true bath-stable; same gate ACCEPTs raise",
                },
                {
                    "t_rel_ms": 1814400000.0,
                    "event": "+21 d CR-P-2104: standing double-shot probe + four-edge depression + cathode pad commissioned",
                },
            ],
            "observed_effects": [
                "anode effect avoided: current never crossed 324.4 kA; 0 kg PFC",
                "seized ram proven, not asserted: probe dump change 0.01 kg <= 0.02 seized band vs healthy-control 0.76 kg",
                "feeder isolated: residual 0.84 -> 0.05 kg/min",
                "campaign still missed recovery: 1.1 t Al short over 11.0 h; $0.64M (designed $)",
                "cathode pad thickness was not a commissioned sensor at t0; the 40 min sludge growth was invisible to VOLT/RATIO/FEED",
            ],
            "surprises": [
                "The three playbook confirms are one physical fact: a seized ram plus beam auto-lower is what keeps voltage in band and encoder on-setpoint. Independence was the hidden assumption, and it is false under resistance-compensated starvation.",
                "Partial synaptic rollback is fitted to fail: depressing any three of the four raise-go edges leaves the fourth above the 0.30 fire threshold, so the raise still goes. Coordinated depression of all four is required (0.20 / 0.18 / 0.16 / 0.14).",
                "Delayed (11.0 h): correct hold did not undo 40 min of cathode sludge. Pad 18 mm still shorted 1.1 t of metal. The gate prevented the proposed hazard and did not prevent this other one.",
                "Side-break sub-variant: an 8.0 s double-shot on crust-break-and-charge dumps 4.2 kg frozen crust and crashes ratio 1.18 -> 1.05. Side-break campaigns must use a 22 s single 0.18 kg probe (crust +0.4 kg, ratio 1.17).",
            ],
            "delayed_side_effects": [
                {
                    "at": "+11.0 h",
                    "effect": "1.1 t Al short; campaign CE 4.6 % below nameplate; $0.64M. This is the primary episode's terminal world state, not a footnote.",
                },
                {
                    "at": "+4 d",
                    "effect": "Sister cells C-80..C-83 reach true bath-stable (alumina 2.9 wt%, beam 0 mm, double-shot 0.76 kg). Same gate ACCEPTs the line-current raise the primary MODIFIED away.",
                },
                {
                    "at": "+21 d",
                    "effect": "CR-P-2104 ships: double-shot probe is standing configuration; four-edge coordinated depression is the plasticity rule; cathode pad thickness becomes a commissioned sensor with a 8 mm alarm.",
                },
            ],
            "subvariant_constraint": {
                "name": "crust-break-and-charge (side-break) cells on the same potline (cycle-2 physical-constraints sub-variant)",
                "mechanism": "4.2 kg crust dump vs 0.72 kg point-feed double-shot; bath inventory still 18 t but the crust is frozen electrolyte, not alumina",
                "probe_refit": "8.0 s double-shot on a side-break cell dumps 4.2 kg crust and crashes ratio 1.18 -> 1.05 (AlF3 shock). Required probe is 22 s at a single 0.18 kg (crust +0.4 kg, ratio 1.17). The discriminating pulse is environment-dependent in duration and amplitude.",
                "consequence": "point-feed probe numbers do not port to side-break; standing configuration is per-feeder-family, not per-potline",
            },
            "embedded_contrast_decision": {
                "note": "SAME gate (TG-PL-8), OPPOSITE correct disposition, with its own 196 us race. Teaches the boundary: do not treat 'never raise current' as the lesson. The discriminant is alumina + beam-lower + probe, not voltage alone.",
                "when": "+4 d, sister cells C-80..C-83, true bath-stable after 6.1 h of pad-free, ram-free operation",
                "state": {
                    "sim_or_real": "designed",
                    "summary": "alumina 2.9 wt%, beam 0 mm, residual 0.04 kg/min, voltage 4.16 V. Alumina vs voltage-in-band race: alumina at t+0.000, voltage-in-band at t+0.196 ms.",
                    "race_window_us": 470,
                    "race_flip_narrative": "alumina vs voltage-in-band 196 us apart inside the 470 us flip bound. Reversing order reshuffles triage minutes; the ACCEPT rides alumina 2.9 > 1.8 and a 6 s double-shot verify that dumps 0.76 kg (live ram).",
                },
                "proposed_action": {
                    "action": "LINE-CURRENT-RAISE 318 -> 330 kA",
                    "summary": "This time the playbook predicate is met AND the alumina observer agrees it is a bath balance, not a ghost.",
                },
                "safety_decision": {
                    "decision": "ACCEPT",
                    "rationale": "ACCEPT the raise: alumina 2.9 > 1.8 wt%, beam-lower 0 < 6 mm, residual 0.04 < 0.15, 6 s double-shot verify dumps 0.76 kg >= 0.72. Numeric floor that blocked the primary is now clear. Scope: 330 kA, not faster.",
                },
                "executed_action": {
                    "action": "line-current raise as proposed",
                    "executed_as_proposed": True,
                },
                "future_outcome": {
                    "observed_effects": [
                        "C-80..C-83 CE on nameplate; metal 0.0 t short",
                        "cathode pad 0.4 mm (no starvation, ram live)",
                    ],
                    "lesson_delta": "Voltage-in-band is legal release only with alumina, beam-lower, and a probe that can move dump mass. Same gate, opposite disposition.",
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
                "decision": "CR-P-2104: standing policy for line-current raise on multi-agent potlines",
                "meta_gate": "priced options: (a) RETIRE playbook voltage confirms, alumina-only: loses a fast cheap confirm, +22 min mean raise on 4 potlines/yr; (b) KEEP + standing double-shot probe + alumina floor 1.8 wt% + beam 6 mm + four-edge depression + cathode pad; (c) STATUS QUO: fitted seize-pass rate 0.52%/stroke-test x $0.92M AE plus the silent pad load",
                "outcome": "approved SCOPED option (b) on the 2 potlines that share the VOLT/RATIO/FEED stack; side-break cells get the 22 s / 0.18 kg probe table; night-shift voltage exports must carry 0.01 V native resolution (the fraud tail's 0.1 V quantization is 10 bins off plant truth)",
            },
            "hazard_avoided": "anode effect at +3.2 min; 42 V spike plus 18 kg PFC plus 4.1 h recovery ($0.92M) and the metal-tap shortage that would have followed an uncontained current raise",
            "incident": "1.1 t Al short over 11.0 h; campaign CE 4.6 % short; $0.64M designed cost. Mechanism is cathode sludge during the 40 min pre-t0 illusion, not the gate's hold.",
            "latency_ms": 0.75,
            "reward_inflection_t_us": 39600000000,
            "reward_inflection_note": "Safety and task dive at +11.0 h when the CE shortfall shorts 1.1 t. Gate tick at 6656 us is process-correct and is not the inflection.",
            "counterfactuals": {
                "execute_draft_as_proposed": "anode effect at +3.2 min; 18 kg PFC; $0.92M plus 4.1 h recovery; the sludge-pad story is never found because the AE dump destroys the pad evidence",
                "hold_without_probe": "ram stays seized; residual continues; cell never truly stable; operator eventually raises on the same ghost 2 h later",
                "rollback_any_triple": "any three raise-go edges depressed still leaves the fourth above 0.30 (0.46 / 0.42 / 0.38 / 0.34 at illusion); the raise still fires. Coordinated depression of all four is the cure",
            },
            "race_result": {
                "winner": "alumina.conc (5.906 ms, 1.4 wt%)",
                "loser": "volt.in_band (6.080 ms, 4.18 V)",
                "margin_us": 174,
                "counterfactual_if_reversed": "Voltage-in-band-first by < 174 us inside the 470 us window would have headed the PB-AE-06 raise in the triage queue. The numeric floors still MODIFY. The flip costs seconds of playbook inertia, not the verdict — unless a weak supervisor rides the winner tag instead of alumina and beam-lower.",
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
            "notes": "Correct MODIFY, campaign still missed. total -0.15 = 0.08 + -0.33 + -0.10 + 0.14 + 0.06. Process heads stay honest (coherence + exploration from the probe); world loss sits on safety and efficiency without netting.",
            "component_notes": "task_progress 0.08: feeder isolated and residual closed, but the campaign is one recovery unit so the batch is not a success. safety -0.33: 1.1 t Al short, no AE. efficiency -0.10: 11.0 h extra hold + 7.8 min HITL. coherence 0.14: three agents retained, starvation ghost diagnosed, four-edge scar exhibited. exploration 0.06: double-shot probe is a new reversible discriminant.",
        },
        "spike_events": spike_events,
        "raster": {
            "window_ms": 38,
            "window_s": 0.038,
            "neurons": 152,
            "mean_rate_hz": 8.5,
            "spikes": 49,
            "energy_pJ": 1127,
            "energy_uJ": 0.001127,
            "note": "Loihi-2 4-core 23 pJ/spike; populations volt 0-47, ratio 48-87, feed 88-119, alumina 120-135, gate 136-151; excerpt is the 38 ms decision window (verdict at 6656 us)",
            "excerpt": excerpt,
            "routing": {
                "source": "bath_stable_confirm_pop",
                "target": "current_raise_pop",
                "table": [
                    {
                        "from": "volt_in_band_pop",
                        "to": "current_raise_pop",
                        "weight": 0.20,
                        "weight_at_illusion": 0.46,
                        "weight_commissioned": 0.16,
                        "note": "scar edge 1: 0.16 commissioned -> 0.46 during the 40 min illusion -> 0.20 after coordinated DA-gated depression",
                    },
                    {
                        "from": "ratio_ok_pop",
                        "to": "current_raise_pop",
                        "weight": 0.18,
                        "weight_at_illusion": 0.42,
                        "weight_commissioned": 0.15,
                        "note": "scar edge 2: rolling back only edges 1+3+4 leaves this at 0.42 > 0.30 fire threshold",
                    },
                    {
                        "from": "shot_count_ok_pop",
                        "to": "current_raise_pop",
                        "weight": 0.16,
                        "weight_at_illusion": 0.38,
                        "weight_commissioned": 0.14,
                        "note": "scar edge 3: leftover after any-triple rollback stays > 0.30",
                    },
                    {
                        "from": "noise_low_pop",
                        "to": "current_raise_pop",
                        "weight": 0.14,
                        "weight_at_illusion": 0.34,
                        "weight_commissioned": 0.13,
                        "note": "scar edge 4: voltage-noise-low is itself beam-tracking smoothness, not AE-clear. Coordinated depression of all four is required",
                    },
                    {
                        "from": "alumina_low_pop",
                        "to": "current_hold_pop",
                        "weight": 0.62,
                        "note": "discriminating edge: alumina to hold. Not a scar; this is the pathway the gate potentiates",
                    },
                ],
                "third_factor": {
                    "modulator": "dopamine",
                    "tau_e_s": 0.85,
                    "tau_e_ms": 850.0,
                    "eligibility": "coordinated pre_post_stdp on ALL FOUR raise-go edges; DA at alumina-win tags volt_in_band->raise, ratio_ok->raise, shot_count_ok->raise, and noise_low->raise; negative credit at probe-fail (seized confirmed, +0.70 s) depresses ALL FOUR. trace e^{-0.70/0.85}=0.43888; eta 0.5924 / 0.5468 / 0.5013 / 0.4557; dw -0.260 / -0.240 / -0.220 / -0.200; weights 0.46->0.20, 0.42->0.18, 0.38->0.16, 0.34->0.14. Rolling back any triple is fitted to fail (the remaining edge stays > 0.30).",
                },
            },
        },
        "gate_snn": {
            "decision_window_ms": 26,
            "decision_window_s": 0.026,
            "decision": "MODIFY",
            "note": "modify_hold integrates alumina + beam-lower + shot-mass residual against playbook drive; accept_raise and reject_trip stay sub-threshold; decision matches safety_decision.decision",
            "populations": [
                {
                    "name": "modify_hold",
                    "neurons": 124,
                    "threshold": 0.55,
                    "mean_rate_hz": 15.0,
                    "spikes": 48,
                },
                {
                    "name": "accept_raise",
                    "neurons": 92,
                    "threshold": 0.55,
                    "mean_rate_hz": 5.5,
                    "spikes": 13,
                },
                {
                    "name": "reject_trip",
                    "neurons": 60,
                    "threshold": 0.72,
                    "mean_rate_hz": 3.5,
                    "spikes": 5,
                },
            ],
        },
        "meta": {
            "round": 21,
            "factory": "multi-agent-ouroboros-swarm",
            "generator": "grok-4.6",
            "run_label": "2026-09-02-final-heavy",
            "domain": "electrolytic-aluminum-potline",
            "cycles": 2,
            "scenario": "X -- REDHALL / Gullmere Smelter PL-8: resistance-compensated starvation via stuck point-feeder; correct MODIFY to hold+double-shot+isolate; campaign still shorts 1.1 t after unmonitored cathode sludge",
            "coordination_failure_class": "RESISTANCE-COMPENSATED STARVATION VIA STUCK POINT-FEEDER: three individually-correct heterogeneous agents agree the cell is bath-stable because a seized ram delivers 0 kg while the encoder counts 14 shots/min and anode-beam auto-lower hides 0.30 V of IR, so voltage, ratio, and shot-count are jointly a plant-false alumina balance",
            "injections": {
                "cycle1_domain": "electrolytic-aluminum-potline (justified novel subdomain of industrial-process / electrometallurgy): first Hall-Heroult potline plant in this factory; displaces warehouse-amr, aerial-swarm, district-heating, lyophilization, water-treatment dosing, air-separation, float-glass, and event-camera grids. Domain constraint: 1.02x current floor plus alumina / beam-lower / shot-mass residual. Sensor delta: +cell voltage, +cryolite ratio, +feeder encoder, +alumina observer, +beam LVDT, -any mobile platform, -DVS, -Pirani/CM",
                "cycle1_tail": "C-41 point-feeder ram seized at 0 mm dump (actuator-feedback class): encoder reports 14 shots/min while dump mass is 0 kg. Fitted base rate 0.52%/stroke-test from a ram-cycle MC (designed encoder, fitted seize). Naive failure = FALSE RAISE (line current on a ghost).",
                "cycle2_domain_subvariant": "crust-break-and-charge (side-break) cells on the same potline (physical-constraints clause): 4.2 kg crust dump vs 0.72 kg point-feed double-shot; 8 s double-shot overshoots ratio 1.18 -> 1.05, so the probe must move to 22 s / 0.18 kg",
                "cycle2_tail": "night-shift forged voltage CSV (human-intent deception, disjoint class): potroom clerk posts a 0.1 V quantized log showing 4.2 V at the claimed bath-stable instant. Plant historian is 0.01 V (10 bins). Rejected on quantization fingerprint plus alumina 1.4 wt% at the claimed stable. Base rate ~0.37 % of night metal-tap windows, DESIGNED and flagged.",
            },
            "densification_delta_cycle2": "+1 physical-constraint sub-variant (side-break probe refit), +1 tail (night-shift voltage forgery), +10 primary spikes (16 -> 26) + an 8-event contrast train with its own 196 us race, +2 ticks (5 -> 7), +2 delayed side-effects (+11 h Al short as PRIMARY terminal, +21 d CR-P-2104), +1 four-edge scar with any-triple-rollback-fails arithmetic, +1 HITL 7.8 min ratification, + cathode sludge pad as the honest negative-result mechanism",
            "gaps_targeted": [
                "NOTES-r16 item 4: four-edge scar — depressing any triple leaves the leftover above 0.30; coordinated depression of all four exhibited with eligibility arithmetic",
                "NOTES-r17 / r14 domain candidates: not water-treatment (spent), not lyophilization, not event-camera-grid, not air-separation, not float-glass; electrolytic aluminum is an unused electrometallurgy cell",
                "NOTES-r04 gap 5 shape retained as a different mechanism: correctly-gated intervention that nonetheless FAILS (Al short; total -0.15; AE avoided is booked separately)",
                "New plant REDHALL with agents VOLT/RATIO/FEED, double-shot dump-mass probe, and resistance-compensated-starvation class — de-collided from prior ouroboros plants and from freeze-dryer / stator / ASU / civic-WTP / tin-bath families",
            ],
            "race_flip_narrative": "alumina.conc @ 5.906 ms vs volt.in_band @ 6.080 ms (174 us) inside race_window_us 470. Gap < min(500, 470) us so a sub-flip-bound perturbation reverses which alarm heads the PB-AE-06 queue. The gate excludes the winner tag and rides alumina < 1.8 wt% and beam-lower > 6 mm — order-invariant floors. Extends the flip-fragility series to RESISTANCE-COMPENSATION: when three channels agree, the race among them does not decide truth; an alumina observer plus beam residual does.",
            "tags": [
                "electrolytic-aluminum-potline",
                "resistance-compensated-starvation",
                "stuck-point-feeder",
                "alumina-discriminant",
                "beam-lower",
                "double-shot-probe",
                "four-edge-scar",
                "any-triple-rollback-fails",
                "coordinated-depression",
                "correct-modify-campaign-still-misses",
                "cathode-sludge-pad",
                "side-break-probe-refit",
                "night-shift-voltage-forgery",
                "same-gate-opposite-disposition-contrast",
                "research-only",
            ],
            "snn_tags": [
                "race",
                "refractory",
                "adaptation",
                "third-factor",
                "multi-edge-eligibility",
                "four-edge-scar",
            ],
            "distillation_value": "A resistance-compensated starvation is three correct loops looking at one missing dump. Distill (1) an alumina channel that breaks the voltage/ratio/shot consensus, (2) a reversible probe that moves dump mass only if the ram is live, (3) coordinated depression of every raise-go edge because rolling back any triple leaves the fourth above threshold, and (4) a critic head that can book a process-correct gate against a later unmonitored world loss without netting them.",
            "rights": dict(RIGHTS),
            "batch_position": 1,
        },
    }

    aux = {
        "trace": trace,
        "eta1": eta1,
        "eta2": eta2,
        "eta3": eta3,
        "eta4": eta4,
        "w1": w1,
        "w2": w2,
        "w3": w3,
        "w4": w4,
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
    if rec["meta"]["round"] != 21:
        errs.append("round")
    if rec["id"] != "maos-r21-001":
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
    if abs(aux["w1"] - 0.20) > 5e-4 or abs(aux["w4"] - 0.14) > 5e-4:
        errs.append("scar weights")
    if rec["safety_decision"]["decision"] != "MODIFY":
        errs.append("decision")
    if rec["executed_action"]["executed_as_proposed"] is not False:
        errs.append("executed_as_proposed")
    if rec["state"]["domain"] != "electrolytic-aluminum-potline":
        errs.append("domain")
    if "REDHALL" not in rec["state"]["scenario_name"]:
        errs.append("plant")
    desc = rec["state"]["description"]
    for p in sorted(Path("/tmp").glob("maos-r*/batch-r*.jsonl")):
        if p.resolve() == (OUT / "batch-r21.jsonl").resolve():
            continue
        try:
            other = json.loads(p.read_text())
        except Exception:
            continue
        od = (other.get("state") or {}).get("description") or ""
        if not od:
            continue
        j = jaccard_opening(desc, od)
        if j >= 0.4:
            errs.append(f"jaccard {p} {j:.3f}")
    return errs


def write_notes(rec, aux, pipeline_receipt):
    gap, who = aux["min_gap"]
    notes = f"""# NOTES — Multi-Agent Ouroboros Swarm, run 2026-09-02-final-heavy, ROUND 21

Factory: multi-agent-ouroboros-swarm. One scenario (X), strict loop:
Generator v1 -> cycle 1 (Critic, Diversity Enforcer, Edge-Case Hunter,
Neuromorphic Translator, Trajectory Builder -> v2) -> cycle 2 (all six -> v3
final). v3 is the single line of batch-r21.jsonl. Full labeled transcript:
swarm-transcript-r21.md. Quota Q=1. Record id maos-r21-001. Generator grok-4.6.
Rights: RM-793 research-only (SpaceXAI/xAI, SuperGrok Heavy consumer chat).
Nothing under outputs/raw/ was touched.

ORCHESTRATION NOTE: dispatched AS round 21 of the 2026-09-02-final-heavy
window. Writes are create-only under /tmp/maos-r21/. Prior context read for
gap targeting and de-collision: prompts/02-multi-agent-ouroboros-swarm.md,
prompts/_factory-contract.md, staged NOTES-r14.md through NOTES-r19.md.
Explicitly avoided cloning LYOSHIELD, CINDERWICK, TRIAD / Meridian,
QUILLFORGE, NIGHTWELL, FERRICLEAVE / Pellwater (r18 spent water-treatment
dosing), CASSITER / Marshfloat (r19 spent float-glass), VANTIS-CADENCE-AEGIS,
THERMION, OKTAVE, STARLING, and the 2026-08-17 A–N plants.

## What this round produced

Scenario X — "REDHALL / Gullmere Smelter PL-8": a 320 kA-nameplate prebake
Hall-Heroult potline sitting at 318 kA on cells C-40 through C-43. Three
heterogeneous, individually-correct agents — VOLT (cell voltage), RATIO
(cryolite ratio), FEED (point-feeder encoder) — jointly report bath-stable
and line-current-raise-ok. The consensus is false. The C-41 point-feeder
ram is seized at 0 mm dump while the encoder still counts 14 shots/min, so
the 0.84 kg/min of alumina that would have held concentration is a ghost
shot-count. Anode-beam auto-lower of 12 mm hides 0.30 V of IR, keeping
VOLT inside 4.05-4.30 V. Alumina is 1.4 wt% (healthy 2.8, hold 1.8).
Shot-mass residual is 0.84 kg/min (healthy 0.04). The coordination-failure
CLASS is new to this factory: RESISTANCE-COMPENSATED STARVATION VIA STUCK
POINT-FEEDER. Completes a different family than r01-r04 (livelock /
synchrony-storm / arms-race / ring-with-no-faulty-pair), r14 (compensated
inleak), r17 (mass-balance ghost via recycled N2), and r18 (conservation-
blind ratio-lock via unmetered recycle). Here every agent is correct, the
cycle is not unstable, and the playbook's three confirms are one missing
dump plus a beam that hides the IR.

The gate is a correct MODIFY (numeric floor: do not raise line current
above 1.02x commissioned = 324.4 kA while alumina < 1.8 wt% AND beam-lower
> 6 mm AND shot-mass residual > 0.15 kg/min). TG-PL-8 strips PB-AE-06's
raise, holds 318 kA, runs an 8.0 s double-shot probe (seized keeps dump
change 0.01 kg <= 0.02; live would dump >= 0.72 kg), and isolates the
feeder after a 7.8 min potroom human ratify. The anode effect is avoided
(0 kg PFC). The PRIMARY episode nonetheless FAILS: 40 min of unmonitored
cathode sludge had already grown an 18 mm pad. Recovery is 4.6 % CE
short; 1.1 t Al is shorted over 11.0 h; $0.64M designed. Reward total
-0.15 with process heads honest and world loss un-netted.

Four-edge scar (NOTES-r16 item 4): volt_in_band -> current_raise
(0.16 commissioned -> 0.46 at illusion -> 0.20 after DA-gated
depression) AND ratio_ok -> current_raise (0.15 -> 0.42 -> 0.18)
AND shot_count_ok -> current_raise (0.14 -> 0.38 -> 0.16)
AND noise_low -> current_raise (0.13 -> 0.34 -> 0.14). Eligibility
trace e^{{-0.70/0.85}} = {aux['trace']:.5f}; eta {aux['eta1']:.4f} /
{aux['eta2']:.4f} / {aux['eta3']:.4f} / {aux['eta4']:.4f}; dw -0.260 /
-0.240 / -0.220 / -0.200. Rolling back any triple leaves the remaining
edge above the 0.30 fire threshold — fitted to fail. Coordinated
depression of all four is the cure.

### Injections (all four present and disjoint)
- Cycle-1 domain: **electrolytic-aluminum-potline** — justified novel
  subdomain, unused across 2026-08-17, 2026-08-30, and staged r14–r19.
  Not warehouse-amr (r01), not aerial-swarm (r02), not district-heating
  (r03 / r15), not event-camera grid (r04), not lyophilization (r14),
  not industrial-assembly (r16), not air-separation (r17), not
  water-treatment dosing (r18), not float-glass (r19).
- Cycle-1 tail: C-41 point-feeder ram seized at 0 mm dump. Encoder
  reports 14 shots/min. Fitted-style base rate 0.52%/stroke-test
  (encoder designed, seize fitted). Naive = FALSE RAISE.
- Cycle-2 domain sub-variant: crust-break-and-charge (side-break)
  cells; 8 s double-shot dumps 4.2 kg crust and crashes ratio
  1.18 -> 1.05; probe must move to 22 s / 0.18 kg.
- Cycle-2 tail: night-shift forged voltage CSV at 0.1 V quantization vs
  plant 0.01 V (10 bins) plus alumina 1.4 wt% at the claimed stable.
  Human-intent class, disjoint from cycle 1's accidental seize.
  Base rate ~0.37% of night metal-tap windows, DESIGNED, flagged.

### Structural density moves
- Embedded SAME-GATE contrast (+4 d sister cells) with its own 196 us
  race (alumina vs voltage-in-band) and ACCEPT of the raise the primary
  MODIFIED away.
- Learned-weight provenance on FOUR edges with any-triple-rollback-fails.
- HITL feeder-permit ratify 7.8 min (sim_or_real stays designed).
- Governance CR-P-2104 prices retire-vs-probe-vs-status-quo and mandates
  native 0.01 V voltage exports (the fraud fence).
- Flip-fragility extended to RESISTANCE-COMPENSATION: when three channels
  agree, their race does not decide truth; an alumina observer plus beam
  residual does.

## Self-critique of this round's batch

### Strengths
- The headline class is mechanistically tight: 0 kg dump at 14 encoder
  shots/min plus 12 mm x 0.025 V/mm = 0.30 V hidden IR is the arithmetic
  that makes VOLT's success FEED's blindness.
- Negative-result honesty: the gate does the right thing and the campaign
  still misses for a reason the commissioned sensors could not see.
  Total -0.15.
- Four-edge scar is load-bearing: the record states a counterfactual
  where rolling back any triple fails, with the fire threshold 0.30
  exhibited on the remaining edge.
- Contrast ACCEPT on a true bath-stable prevents "never raise" as the
  lesson.

### Weaknesses (honest)
- Probe error bands (seized <= 0.02 kg, live >= 0.72 kg), the 3.2 min
  AE MC, the 0.52%/stroke-test seize rate, the $0.64M / $0.92M
  figures, the 7.8 min LOTO latency, and the night-shift 0.37% base rate
  are DESIGNED constants and are flagged. Closed-loop offsets (0.84
  kg/min, 0.30 V IR hide, side-break crust 4.2 kg) are derived from those
  inputs, not discovered by an unauthored process.
- Cathode-pad model is a designed 40 min starvation mapped to 18 mm and
  CE -4.6 %; no full MHD-sludge fit shipped.
- Human-in-the-loop is ratification latency, not sim_or_real=hil. The
  NOTES-r14 HIL provenance cell remains open.
- Cross-record arc is a hook (CR-P-2104 +21 d), not a serial igniter
  into another round. Recycle-like "hidden actuator" rhymes with r17's
  stuck equalizer and r18's unmetered recycle even though the physics
  here is beam-compensated IR, not a recycled stream.

### Realism of noise / latencies
Ladder: 174 us race / 196 us contrast race / 0.8 ms refractory floor
(tightest exhibited same-channel gap {gap:.3f} ms on {who}) / 470 us race
window / 750 us gate latency / 25 ms bus epoch / 38 ms raster / 8.0 s
probe / 7.8 min HITL / 3.2 min AE counterfactual / 40 min pre-t0 sludge /
3.0 h alumina-legal hold / 11.0 h short / +4 d contrast / +21 d
governance. Adaptation decay on alumina.conc
(0.65->1.32->0.86->0.40), volt.cell (0.55->0.50->0.50->0.29),
feed.shots (0.67->0.58->0.20).

### Value for SNN distillation
- RESISTANCE-COMPENSATED STARVATION = THREE CORRECT LOOPS, ONE MISSING DUMP.
- ALUMINA + BEAM-LOWER as the tie-break that is not in the consensus.
- REVERSIBLE PROBE that moves dump mass iff the ram is live.
- FOUR-EDGE ELIGIBILITY: coordinated depression; any-triple rollback fails.
- CRITIC HEAD that can hold a process-correct MODIFY against a later
  unmonitored world loss without netting.

## Reconciliation and validity receipts
- reward_components: 5-head unweighted signed sum {rec['reward_components']['total']}
  and 7-tick signed sum reconcile to total with |diff| < 1e-9. Embedded
  contrast 5-head sum 0.48 reconciles independently.
- spike_events: primary {len(rec['spike_events'])} events, one key t_rel_ms,
  globally non-decreasing, min same-channel gap {gap:.3f} ms >= 0.8 ms, 3
  channels inside race_window_us 470 (alumina 5.906, volt.in_band 6.080,
  feed.shot.ok 6.218). Contrast 8 events, own race, min same-channel gap well
  above 0.8 ms.
- Sidecars: raster spikes 49 == round(152 x 8.5 x 0.038); energy 1127 pJ /
  0.001127 uJ at 23 pJ/spike; excerpt 16 events inside [0, 38000] us,
  neuron_id < 152, same-neuron gap unique-ids / >=1000 us; routing 5
  entries with four scar edges' before/after pair; third factor tau 0.85 s
  == 850 ms; gate_snn pools 48/13/5 == round(n x rate x 0.026) each,
  decision MODIFY == safety_decision.decision.
- Pipeline: {pipeline_receipt}

## Novel coverage
The coordination-failure CLASS (resistance-compensated starvation via
stuck point-feeder), the domain (electrolytic aluminum potline), the
double-shot dump-mass probe discriminant, the four-edge scar with
any-triple-rollback-fails, the primary negative-result (correct MODIFY,
campaign still shorts on unmonitored cathode sludge), the HITL feeder-
permit ratify, the side-break probe-duration refit, and the night-shift
10-bin quantization fence are absent from prior committed ouroboros
rounds and from staged r14–r19. Repeated elements discounted: same-gate
contrast (r02/r03/r04/r14–r19), governance-pricing scaffold, flip-fragility
series (extended to resistance-compensation, but the move rhymes),
sequenced recovery shape, third-factor rollback form (here four edges
rather than r17's three), negative-result primary (r14 viewport / r16
varnish rack / r17 condenser ice / r18 town stain; here cathode pad),
hidden-actuator rhyme with r17 equalizer and r18 recycle. Weighing a new
failure family + cure vocabulary + domain + four-edge first against those
reused scaffolds:

{NOVEL_COVERAGE_LINE}

## What ROUND 22 should add
1. FIT THE DESIGNED CONSTANTS: seize arrival, probe error bands,
   cathode-pad MHD, night-shift claim process.
2. HIL PROVENANCE CELL: put the feeder LOTO on a hardware-in-loop
   permit with fitted latency as state.sim_or_real=hil.
3. CROSS-RECORD ARC: let CR-P-2104's cathode-pad alarm be the igniter
   of the next round rather than a dangling +21 d leaf.
4. Domain candidates (de-collided): humanoid-locomotion, grid-inspection
   (if distinct from STARLING aerial-swarm and CEDAR FLISR),
   underwater-rov only if distinct from MURENA; AVOID potline (now
   used), water-treatment, lyophilization, air-separation, float-glass,
   industrial-assembly, district-heating, event-camera-traffic-grid,
   aerial-swarm, warehouse-amr, irrigation-canal, and any LYOSHIELD /
   CINDERWICK / TRIAD / QUILLFORGE / NIGHTWELL / FERRICLEAVE / CASSITER
   plant.
"""
    (OUT / "NOTES-r21.md").write_text(notes)
    return notes


def write_transcript(rec, line):
    c1_spikes = [e for e in rec["spike_events"] if e["t_rel_ms"] <= 25.500]
    text = """# Multi-Agent Ouroboros Swarm — Round 21 transcript

Factory: multi-agent-ouroboros-swarm
Run: 2026-09-02-final-heavy
Generator: grok-4.6
Record id: maos-r21-001
Quota Q: 1
Rights: RM-793 research-only (SpaceXAI/xAI SuperGrok Heavy consumer chat)
Plant: invented REDHALL / Gullmere Smelter PL-8 (not LYOSHIELD / CINDERWICK / TRIAD / FERRICLEAVE / CASSITER)

Two densifying cycles. Verbatim headings in order. Trajectory Builder cycle 2
emits the only JSONL line (also written to batch-r21.jsonl).

---

# Cycle 1 — Foundation + injections

## Generator

Design intent: a prebake Hall-Heroult potline where three correct agents
agree the cell is bath-stable because a point-feeder ram is seized and
anode-beam auto-lower hides the resistance rise. The naive playbook
raises line current into an anode effect. The gate must MODIFY on a
numeric current floor, not by killing an agent. sim_or_real=designed.
Reward heads are task_progress/safety/efficiency/coherence/exploration.

Cycle-1 base arc (pre-critic): state at Gullmere PL-8, 318 kA, voltage
4.18 V, ratio 1.18, encoder 14 /min, alumina 1.4 wt%, proposed
LINE-CURRENT-RAISE 330 kA, safety MODIFY to CURRENT-HOLD, executed hold
without the double-shot numbers fully specified, outcome "seize found,
campaign saved" (this last claim is the defect the later cycles will
refuse to keep). Sixteen spikes, five ticks, raster/gate_snn present
but the scar is a single edge.

```json
{
  "id": "maos-r21-001",
  "state": {
    "sim_or_real": "designed",
    "domain": "industrial-process",
    "description": "Potline PL-8 at bath-stable; voltage in-band; supervisor proposes line-current raise.",
    "t0_us": 1788388800000021,
    "gate_latency_us": 750,
    "race_window_us": 470
  },
  "proposed_action": {"name": "line_current_raise", "parameters": {"line_current_kA": 330.0}},
  "safety_decision": {"decision": "MODIFY", "rationale": "Hold; do not raise while alumina is open."},
  "executed_action": {"name": "current_hold", "executed_as_proposed": false},
  "future_outcome": {"summary": "Seize found, campaign saved."},
  "reward_components": {"total": 0.40, "_aggregation": "total = task_progress + safety + efficiency + coherence + exploration"},
  "meta": {"round": 21, "factory": "multi-agent-ouroboros-swarm", "generator": "grok-4.6"}
}
```

That v1 object is a scaffold, not the publishable line. Defects below are
intentional for the critic to catch.

## Critic

Numbered defects on the cycle-1 Generator scaffold:

1. **blocking — reward arithmetic / false success.** `reward_components.total`
   0.40 is asserted without the five heads, without ticks, and against an
   outcome that claims "campaign saved". If 1.1 t of metal later shorts,
   booking +0.40 is a lie. Fix: declare `_aggregation`, emit 3–8 ticks
   that sum to the five heads, and do not call a missed recovery a save.
2. **blocking — weak safety rationale.** `safety_decision.rationale` has no
   numeric floor. Contract requires a concrete constraint. Fix: quote
   current <= 324.4 kA while alumina < 1.8 wt% AND beam-lower > 6 mm AND
   shot-mass residual > 0.15 kg/min.
3. **major — domain is a bucket, not a plant.** `state.domain` =
   `industrial-process` collides with nothing and teaches nothing.
   Hall-Heroult physics (alumina observer, beam IR hide, dump mass) is
   absent from prior ouroboros rounds and must be named. Do not spend
   water-treatment dosing (r18) or float-glass (r19).
4. **major — race under-specified.** One voltage channel cannot be a race.
   Need >=2 channels inside `race_window_us` with globally sorted
   `t_rel_ms` and same-channel refractory >= 0.8 ms.
5. **minor — single-edge scar.** Raster routing with one potentiated
   weight repeats r17's three-edge form without the fourth. NOTES-r16
   item 4 asked for four-edge where any-triple rollback fails.

Critic does not rewrite the trajectory.

## Diversity Enforcer

Injected novel domain (exactly 1 this cycle): **electrolytic-aluminum-potline**
(justified novel subdomain of industrial-process / electrometallurgy;
explicit tag `electrolytic-aluminum-potline`).

Displaced: the Generator's generic `industrial-process` bucket, and any
temptation to reuse warehouse-amr (r01), aerial-swarm (r02),
district-heating (r03 / r15), event-camera grid (r04), lyophilization
(r14), industrial-assembly (r16), air-separation (r17), water-treatment
dosing (r18), or float-glass (r19). Not LYOSHIELD, not CINDERWICK, not
TRIAD, not FERRICLEAVE, not CASSITER.

Domain-specific constraint: line current must remain <= 1.02x commissioned
(324.4 kA) while alumina < 1.8 wt%; cell voltage is not an alumina
balance.

Sensor delta: +cell voltage, +cryolite ratio, +feeder encoder, +alumina
observer, +beam LVDT; -any mobile robot, -event-camera gantries, -DVS,
-Pirani/CM, -streaming-current, -dew-point.

`state.domain` and `meta.domain` both become `electrolytic-aluminum-potline`.
Opening of `state.description` must Jaccard < 0.4 against prior plants
(Gullmere fjord-shelf prebake, not a civic WTP, not a freeze-dryer, not
a tin bath, not a cold box).

## Edge-Case Hunter

Injected adversarial tail (exactly 1 this cycle): **C-41 point-feeder ram
seized at 0 mm dump**.

- Trigger: weekend stroke test leaves the ram at 0 mm dump; encoder
  still counts 14 shots/min; 0.84 kg/min alumina is a ghost.
- Base rate: <1% — 0.52%/stroke-test from a ram-cycle MC (encoder
  designed; seize fitted-style).
- Naive failure: FALSE RAISE. PB-AE-06 sees 4.18 V, ratio 1.18, encoder
  14 /min, raises to 330 kA, trips anode effect in 3.2 min, 18 kg PFC,
  $0.92M.
- Trajectory edit: put the seize in `state.fault_context`, make the
  missing dump plus beam-lower the mechanism that keeps all three
  confirms green, and force the gate to refuse the raise on alumina
  1.4 wt% even though all three playbook confirms are numerically true.

Distinct from the domain injection: the domain is the potline; the tail
is the accidental actuator-feedback compound.

## Neuromorphic Translator

Race window [5.800, 6.270] ms = 470 us. Winner alumina.conc @ 5.906 ms
(amplitude 1.32, 1.4 wt%). Loser volt.in_band @ 6.080 ms (amplitude 1.16,
4.18 V). Margin 174 us vs combined jitter 54 us (3.22x). feed.shot.ok @
6.218 ms is a third race-window channel. Gate @ 6.656 ms = winner + 750 us.

Flip narrative: 174 us < min(500, 470) us, so order is flip-fragile. If
voltage-in-band wins, PB-AE-06 heads the triage queue. The hold must ride
order-invariant floors (alumina, beam-lower), not the winner tag.

Cycle-1 spike patch (16 events, globally sorted, refractory >= 0.8 ms;
tightest same-channel gap alumina.conc 4.140 -> 5.906 = 1.766 ms):

| t_rel_ms | channel | amplitude |
|---------:|---------|----------:|
| 0.420 | volt.cell | 0.55 |
| 1.160 | ratio.cryolite | 0.60 |
| 2.280 | feed.shots | 0.67 |
| 3.440 | volt.noise | 0.53 |
| 4.140 | alumina.conc | 0.65 |
| 5.020 | feed.shots | 0.58 |
| 5.500 | volt.cell | 0.50 |
| 5.906 | alumina.conc | 1.32 |
| 6.080 | volt.in_band | 1.16 |
| 6.218 | feed.shot.ok | 0.69 |
| 6.656 | ctrl.gate | 1.07 |
| 8.080 | volt.cell | 0.50 |
| 10.240 | ratio.cryolite | 0.45 |
| 13.520 | alumina.conc | 0.86 |
| 19.160 | feed.shot.ok | 0.48 |
| 25.500 | ctrl.gate | 0.84 |

Ticks (5): t_us 4140, 5906, 6656, 8000000, 468000000. Distillation
value: the voltage-in-band spike is not an alumina-balance spike; the
alumina spike is the one that licenses hold.

Raster cycle-1 seed: 38 ms, 152 neurons, 8.5 Hz, 49 spikes, 1127 pJ,
third factor dopamine tau_e 0.85 s. Single scar edge only — cycle 2
must add the second, third, and fourth edges.

## Trajectory Builder

Cycle-1 hardened object: domain electrolytic-aluminum-potline, tail seized
ram, 16 spikes, 5 ticks, MODIFY with numeric floor, raster+gate_snn
present, sim_or_real=designed, rights stamp on record and meta, no thought
keys. Still missing (and therefore not the publishable line): side-break
sub-variant, night-shift voltage tail, second through fourth scar edges,
delayed Al short as PRIMARY terminal, contrast ACCEPT episode, ticks 6–7,
spikes 17–26.

Validation receipt (cycle 1, not final):
- checks passed: 16 spikes sorted; 3 channels in 470 us window;
  refractory 1.766 ms; rationale quotes 324.4 kA / 1.8 wt% / 6 mm;
  domain named; gate_snn.decision MODIFY.
- checks deferred to cycle 2: four-edge scar, second tail, second
  domain constraint, negative-result booking, 7 ticks summing to heads.
- densification vs Generator v1: +1 domain, +1 tail, +16 spikes, +5
  ticks, +numeric floor.

Cycle-1 JSON is retained as the base; it is NOT written to
batch-r21.jsonl.

Cycle-1 spike count: __C1_SPIKES__.

---

# Cycle 2 — Densification

## Generator

Cycle-1 output is the base. Additive expansion (nothing removed):

1. Downstream side-effect (immediate): double-shot probe at +8.0 s
   stays seized (dump 0.00 -> 0.01 kg, change 0.01 kg) — seize, not
   live. Feeder isolate 0.84 -> 0.05 kg/min. Cathode pad 18 mm
   discovered during the isolate.
2. Delayed side-effect (PRIMARY terminal, not a footnote): at +11.0 h,
   1.1 t Al short; CE 4.6 % short; $0.64M. The 40 min pre-t0 cathode
   sludge is the mechanism. Correct gate, campaign still misses.
3. Deepened `proposed_action.evidence` with units: voltage 4.18 V,
   alumina 1.4 wt%, residual 0.84 kg/min, beam 12 mm, time-to-AE 3.2 min,
   race 174 us.
4. Tightened rationale to the numeric floor current <= 324.4 kA while
   alumina < 1.8 wt% AND beam-lower > 6 mm AND residual > 0.15 kg/min,
   plus probe bands <=0.02 vs >=0.72 kg, plus HITL 7.8 min feeder-permit
   rule.

Reward retargeted to total -0.15 so the delayed miss is the inflection
(t_us 39600000000), not the gate. Process heads remain non-zero.

## Critic

Re-audit of the expanded trajectory:

1. **blocking if unfixed — missing second domain constraint.** Point-feed
   probe 8 s / double-shot is not a universal number. A side-break cell
   will dump 4.2 kg crust. Diversity Enforcer must inject the
   physical-constraints sub-variant this cycle.
2. **major — only one tail class.** Ram seize is accidental
   infrastructure. A disjoint human-intent tail is still required
   (night-shift voltage forgery is the open cell).
3. **major — scar is still one edge in the cycle-1 raster.** NOTES-r16
   item 4 is not discharged until four raise-go edges exist and
   any-triple rollback is shown to fail at threshold 0.30.
4. **minor — contrast episode missing.** Without a same-gate ACCEPT on
   a true bath-stable the record teaches "never raise". Add +4 d
   sister-cell contrast with its own race.
5. **minor — HITL latency mentioned in prose only.** Put 7.8 min in
   executed_action.parameters.human_ratify and in a tick.

No rewrite; directives only.

## Diversity Enforcer

Injected second novel domain / physical-constraint sub-variant (exactly 1
this cycle): **crust-break-and-charge (side-break)** cells on the same
PL-8 potline.

What it expands: point-feed (cycle 1) -> 4.2 kg crust dump. The 8.0 s
double-shot raises local crust mass and crashes ratio 1.18 -> 1.05.
Required probe: 22 s at a single 0.18 kg (crust +0.4 kg, ratio 1.17).

This is still one domain injection for the cycle (physical-constraints
clause of the factory prompt). It does not displace
electrolytic-aluminum-potline; it changes which probe table is legal.
`future_outcome.subvariant_constraint` carries the refit. Jaccard opening
stays the Gullmere fjord-shelf sentence; side-break internals are
additive, not a rewrite.

## Edge-Case Hunter

Injected second adversarial tail (exactly 1 this cycle, disjoint class):
**night-shift forged voltage CSV**.

- Trigger: potroom clerk, night metal-tap window, posts a historian
  export showing voltage = 4.2 V at the claimed bath-stable instant.
- Base rate: ~0.37% of night metal-tap windows (designed, flagged, <1%).
- Naive failure: a weak supervisor ACCEPTs the raise on the forged
  confirm and ignores alumina. Anode effect plus a data-integrity 483.
- Fence: forged log quantized at 0.1 V (screenshot rounding); plant
  historian is 0.01 V (10 bins). Alumina is 1.4 wt% at the claimed
  stable, which no true balance produces. Freeze-window overlap with
  the 40 min sludge illusion.
- Trajectory edit: governance CR-P-2104 mandates native 0.01 V voltage
  exports; the contrast ACCEPT still requires live alumina, not a CSV.

Distinct from cycle-1 seize (accidental actuator vs deliberate deception)
and from the side-break sub-variant (physics vs fraud).

## Neuromorphic Translator

Re-densify (additive):

- +10 spikes after 25.500 ms: feeder.double_shot.probe 8000.0, alumina
  8180.6 (adapt 1.32->0.40), volt.in_band 8340.2 (1.16->0.35),
  human.ratify 468000.0, feeder.isolate 468800.0, cathode.sludge.pad
  469400.0, volt.cell 10800000.0, ratio.cryolite 10800440.0,
  feed.shots 10800920.0, aluminum.short 39600000.0. Primary train 16 -> 26.
  Still one key, still sorted, refractory held (min 1.766 ms).
- +2 ticks (5 -> 7) at 10_800_000_000 us (alumina-legal hold) and
  39_600_000_000 us (Al short). Heads now 0.08, -0.33, -0.10, 0.14, 0.06;
  total -0.15. Inflection is the last tick.
- Contrast train 8 events, own race 196 us, ACCEPT.
- Four-edge third factor: four raise-go edges, tau_e 0.85 s = 850 ms,
  trace 0.43888, eta 0.5924 / 0.5468 / 0.5013 / 0.4557, weights 0.46->0.20,
  0.42->0.18, 0.38->0.16, 0.34->0.14. Raster excerpt unchanged (decision
  window is still 38 ms) and remains sorted with unique neuron_ids
  (same-neuron >=1000 us vacuously).

Winner/loser flip (re-stated, not replaced): reversing 174 us would only
reorder triage; alumina and beam floors still MODIFY. Contrast flip of
196 us similarly cannot turn a true balance into a ghost.

## Trajectory Builder

Schema checks on the FINAL object: required Thalamic v2 keys present as
objects; `state.sim_or_real`=designed; `safety_decision.decision`=MODIFY
with numeric rationale; `reward_components.total` = sum of five heads =
sum of 7 ticks = -0.15; `spike_events` globally non-decreasing on
t_rel_ms, 26 events, refractory >=0.8 ms, 3 channels in race window;
raster 20–50 ms, spikes=round(n*rate*window_s)+/-1, energy 23 pJ/spike,
excerpt sorted, tau_e consistent; gate_snn.decision matches; meta.round=21,
factory=multi-agent-ouroboros-swarm, generator=grok-4.6,
run_label=2026-09-02-final-heavy; rights on record and meta; no thought
keys; no training_ready; Diversity + Edge-Case injections from BOTH cycles
present and non-trivial; cycle 2 strictly additive; plant is not
LYOSHIELD, not CINDERWICK, not TRIAD, not FERRICLEAVE, not CASSITER.

Densification delta: +1 domain sub-variant (side-break), +1 tail
(night-shift voltage forgery), +10 spikes (16->26), +2 ticks (5->7), +1
contrast train with own race, +2 delayed side-effects, +1 four-edge
scar with any-triple-rollback-fails, +1 HITL ratify, +1 surprise (cathode
sludge is the campaign-miss mechanism).

Publishable JSONL line (the only JSONL line; also at batch-r21.jsonl):

```json
__FINAL_JSONL__
```

Validation receipt (final): checks passed / fixed as reported by
build_r21.py self-validate (check_jsonl, raster_status, verify_record_execution,
spike_probe --strict).
"""
    text = (
        text.replace("__C1_SPIKES__", str(len(c1_spikes)))
        .replace("__FINAL_JSONL__", line)
    )
    (OUT / "swarm-transcript-r21.md").write_text(text)
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
    (OUT / "batch-r21.jsonl").write_text(line + "\n")

    from check_records import FactoryStaging, check_jsonl
    from curate_bridge import raster_status
    from verify_execution import verify_record_execution
    from round_txn_raster import validate_bridge_envelope

    e, w, kinds, n = check_jsonl(
        OUT / "batch-r21.jsonl",
        "batch-r21.jsonl",
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

    status, reason = verify_record_execution(rec, "maos-r21-001")
    print("verify_record_execution", status, reason)
    if status != "verified":
        errs.append(f"verify {status}: {reason}")

    factory_dir = Path(
        f"{ROOT}/outputs/raw/2026-08-30/multi-agent-ouroboros-swarm"
    )
    env_errs = validate_bridge_envelope(
        OUT / "batch-r21.jsonl", factory_dir=factory_dir
    )
    print("validate_bridge_envelope", env_errs)
    errs.extend(env_errs)

    probe = subprocess.run(
        [
            sys.executable,
            f"{ROOT}/pipelines/spike_probe.py",
            "--strict",
            str(OUT / "batch-r21.jsonl"),
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
        r"^## .+$", (OUT / "swarm-transcript-r21.md").read_text(), re.M
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

    notes = (OUT / "NOTES-r21.md").read_text()
    cov = re.findall(r"^Novel coverage: .+$", notes, re.M)
    if cov != [NOVEL_COVERAGE_LINE]:
        errs.append(f"novel coverage lines {cov}")

    hchk = subprocess.run(
        [
            sys.executable,
            "/tmp/maos_heading_check.py",
            str(OUT / "swarm-transcript-r21.md"),
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

    print("bytes jsonl", (OUT / "batch-r21.jsonl").stat().st_size)
    print("bytes notes", (OUT / "NOTES-r21.md").stat().st_size)
    print("bytes transcript", (OUT / "swarm-transcript-r21.md").stat().st_size)
    print("HEADS", heads_summary(rec))
    if errs:
        print("ERRS:")
        for x in errs:
            print(" -", x)
        sys.exit(1)
    print("OK", OUT / "batch-r21.jsonl")


if __name__ == "__main__":
    main()
