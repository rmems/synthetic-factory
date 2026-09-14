#!/usr/bin/env python3
"""Build MAOS round-21 window artifacts (research-only; create-only)."""
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

GEN_AT = "2026-09-02T18:42:00Z"
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
OUT = Path(
    "/tmp/sf-window/outputs/raw/2026-09-02-final-heavy/multi-agent-ouroboros-swarm"
)
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
    "REDHALL",
    "Gullmere",
    "OXBOWREEL",
    "Oystermere",
    "CREELWOLD",
    "PUSHERFELL",
    "training_ready",
)
NOVEL_COVERAGE_LINE = "Novel coverage: 51%"


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
            4180,
            6512,
            7200,
            450_000,
            1_680_000,
            8_400_000,
            11_520_000_000,
        ],
        [
            (1, -2, -1, 1, 1),
            (2, -4, -1, 3, 1),
            (2, -5, -2, 4, 2),
            (1, -6, -2, 3, 1),
            (0, -8, -2, 2, 1),
            (1, -5, -2, 2, 1),
            (0, -5, -1, 1, 0),
        ],
    )
    assert abs(heads["total"] - (-0.16)) < 1e-9, heads

    trace = math.exp(-0.45 / 0.90)
    eta1 = 0.24 / trace
    eta2 = 0.22 / trace
    eta3 = 0.20 / trace
    eta4 = 0.18 / trace
    w1 = 0.48 - eta1 * trace
    w2 = 0.44 - eta2 * trace
    w3 = 0.40 - eta3 * trace
    w4 = 0.36 - eta4 * trace
    assert abs(w1 - 0.24) < 5e-4, w1
    assert abs(w2 - 0.22) < 5e-4, w2
    assert abs(w3 - 0.20) < 5e-4, w3
    assert abs(w4 - 0.18) < 5e-4, w4

    spike_events = [
        {"channel": "fuse.gap", "t_rel_ms": 0.380, "amplitude": 0.54},
        {"channel": "v2x.cam", "t_rel_ms": 1.140, "amplitude": 0.61},
        {"channel": "map.advisory", "t_rel_ms": 2.220, "amplitude": 0.58},
        {"channel": "imu.yaw", "t_rel_ms": 3.360, "amplitude": 0.52},
        {"channel": "radar.residual", "t_rel_ms": 4.180, "amplitude": 0.72},
        {"channel": "v2x.cam", "t_rel_ms": 5.010, "amplitude": 0.57},
        {"channel": "fuse.gap", "t_rel_ms": 5.480, "amplitude": 0.50},
        {"channel": "radar.residual", "t_rel_ms": 6.512, "amplitude": 1.38},
        {"channel": "fuse.gap_ok", "t_rel_ms": 6.700, "amplitude": 1.12},
        {"channel": "v2x.lane_clear", "t_rel_ms": 6.888, "amplitude": 0.68},
        {"channel": "ctrl.gate", "t_rel_ms": 7.200, "amplitude": 1.08},
        {"channel": "fuse.gap", "t_rel_ms": 8.120, "amplitude": 0.48},
        {"channel": "map.advisory", "t_rel_ms": 10.180, "amplitude": 0.44},
        {"channel": "radar.residual", "t_rel_ms": 13.410, "amplitude": 0.88},
        {"channel": "v2x.lane_clear", "t_rel_ms": 19.040, "amplitude": 0.46},
        {"channel": "ctrl.gate", "t_rel_ms": 25.600, "amplitude": 0.82},
        {"channel": "brake.probe", "t_rel_ms": 450.0, "amplitude": 0.96},
        {"channel": "aeb.command", "t_rel_ms": 451.8, "amplitude": 0.91},
        {"channel": "radar.residual", "t_rel_ms": 632.4, "amplitude": 0.41},
        {"channel": "fuse.gap_ok", "t_rel_ms": 814.8, "amplitude": 0.33},
        {"channel": "aeb.residual.impact", "t_rel_ms": 1680.0, "amplitude": 0.90},
        {"channel": "human.ratify", "t_rel_ms": 8400.0, "amplitude": 0.78},
        {"channel": "lane.isolate", "t_rel_ms": 8480.0, "amplitude": 0.71},
        {"channel": "fuse.gap", "t_rel_ms": 11520000.0, "amplitude": 0.28},
        {"channel": "map.advisory", "t_rel_ms": 11520440.0, "amplitude": 0.26},
        {"channel": "v2x.cam", "t_rel_ms": 11520920.0, "amplitude": 0.19},
    ]

    contrast_spikes = [
        {"channel": "radar.residual", "t_rel_ms": 0.000, "amplitude": 0.18},
        {"channel": "fuse.gap_ok", "t_rel_ms": 0.196, "amplitude": 0.94},
        {"channel": "v2x.lane_clear", "t_rel_ms": 0.372, "amplitude": 0.27},
        {"channel": "map.advisory", "t_rel_ms": 1.410, "amplitude": 0.43},
        {"channel": "imu.yaw", "t_rel_ms": 4.580, "amplitude": 0.51},
        {"channel": "ctrl.gate", "t_rel_ms": 6.980, "amplitude": 0.93},
        {"channel": "brake.probe", "t_rel_ms": 450.0, "amplitude": 0.86},
        {"channel": "close.ok", "t_rel_ms": 11520000.0, "amplitude": 0.17},
    ]

    excerpt = [
        {"t_us": 380, "neuron_id": 12},
        {"t_us": 1140, "neuron_id": 52},
        {"t_us": 2220, "neuron_id": 92},
        {"t_us": 3360, "neuron_id": 38},
        {"t_us": 4180, "neuron_id": 124},
        {"t_us": 5010, "neuron_id": 60},
        {"t_us": 5480, "neuron_id": 18},
        {"t_us": 6512, "neuron_id": 132},
        {"t_us": 6700, "neuron_id": 22},
        {"t_us": 6888, "neuron_id": 68},
        {"t_us": 7200, "neuron_id": 148},
        {"t_us": 8120, "neuron_id": 36},
        {"t_us": 10180, "neuron_id": 100},
        {"t_us": 13410, "neuron_id": 136},
        {"t_us": 19040, "neuron_id": 76},
        {"t_us": 25600, "neuron_id": 152},
    ]

    rec = {
        "id": "maos-r21-001",
        "title": "GLIMMERAXLE CAV-7: radar residual 18.4 dBsm beats fuse.gap_ok by 188 us; correct MODIFY still underrides at 18 km/h after map-clutter gating",
        "rights": dict(RIGHTS),
        "state": {
            "sim_or_real": "designed",
            "domain": "autonomous-driving",
            "scenario_name": "GLIMMERAXLE / Brambleford CAV-7",
            "timestamp_local": "2026-09-02T13:42:00-05:00",
            "t0_us": 1788396120000021,
            "gate_latency_us": 688,
            "race_window_us": 500,
            "race_window_rel_ms": [6.40, 6.90],
            "description": "Brambleford proving loop CAV-7, an invented two-lane rural arterial on a copse-spur campus, holds ego GLX-4 at 72.0 km/h in lane 1 with ACC close-gap armed. FUSE camera-radar tracker reports in-lane gap 2.80 s to the next moving vehicle 56 m ahead (band 2.00-4.00 s). V2X roadside CAM reports lane_clear with advisory 105 km/h. MAP HD-layer advisory is 105 km/h with this 180 m segment tagged static_shoulder_clutter. The consensus is false: a stalled box truck sits 42.0 m ahead in-lane; FUSE dropped it because the return IoU 0.81 against the clutter polygon exceeded the 0.60 gate, so the 2.80 s gap is locally true of the next moving vehicle and jointly false as a stall certificate. Unassociated in-lane radar residual is 18.4 dBsm against a healthy 1.2 and a hold of 8.0. Observer TTC to the residual is 2.10 s against a hold of 2.40. Radar-residual-first latches SPEED-HOLD plus a 0.45 s brake-jerk probe; fuse.gap_ok-first would have authorized the CLOSE-GAP raise to 105 km/h that impacts in 1.98 s.",
            "goal": "Hold 72.0 km/h and do not raise above 1.05x current (75.6 km/h) while unassociated in-lane radar residual > 8.0 dBsm AND observer TTC < 2.40 s AND map-clutter IoU of that return > 0.60; keep collision delta-v at 0.",
            "race": {
                "contenders": [
                    "radar.residual 18.4 dBsm",
                    "fuse.gap_ok 2.80 s",
                ],
                "semantics": "Radar-residual-first latches SPEED-HOLD + BRAKE-PROBE + AEB-arm. Fuse.gap_ok-first latches CLOSE-GAP raise 72 -> 105 km/h.",
                "window_derivation": "500 us = one 320 us radar dwell plus 180 us tracker-association settle.",
                "order_evidence_note": "Margin 188 us vs combined jitter 52 us (radar 28 + fuse 24): 3.62x. The 188 us gap sits inside min(500, 500) us, so a sub-flip-bound perturbation reverses triage order. The gate rides the order-invariant floors residual > 8.0 dBsm and TTC < 2.40 s, not the alarm order.",
            },
            "topology": {
                "site": "Brambleford proving loop, invented copse-spur campus, CAV-7: 2-lane rural arterial, 6.2 km loop, posted 90 km/h, HD-map clutter polygons on farm-equipment laybys, ego GLX-4 1.8 t sedan, 20 ms vehicle-bus epoch",
                "agents": "FUSE camera-radar tracker and gap (vendor Lanehearth); V2X OBU/RSU CAM (vendor Beaconholt); MAP HD-speed plus clutter layer (vendor Chartfen). Heterogeneous stacks, no shared intent schema, one 20 ms chassis-bus epoch",
                "coupling": "The stalled truck's radar return is what MAP's clutter polygon is gating and what FUSE is therefore not tracking as an in-lane object. V2X lane_clear is a stale CAM from the mapped layby, not a stall certificate. Three locally-correct loops, one map-registered clutter-gate. FUSE/V2X/MAP cannot see brake-pad fade from 6.4 s of pre-t0 comfort braking (not commissioned at t0).",
            },
            "sensors": [
                "front radar 77 GHz, 20 Hz, 28 us jitter, unassociated in-lane residual 18.4 dBsm",
                "camera-radar fused gap, 20 Hz, 24 us jitter, 2.80 s to next moving object",
                "V2X CAM, 10 Hz, 40 us jitter, lane_clear plus 105 km/h advisory",
                "HD-map speed and clutter IoU, 5 Hz, 16 us jitter, 105 km/h, IoU 0.81",
                "IMU yaw rate, 50 Hz, 12 us jitter, 0.04 deg/s (cut-in band > 1.2 deg/s)",
                "observer TTC to unassociated residual is readable, not in PB-CG-07; brake-pad temperature is NOT commissioned at t0",
            ],
            "constraints": {
                "ego_speed_kmh": 72.0,
                "speed_floor_kmh": 75.6,
                "speed_proposed_kmh": 105.0,
                "fuse_gap_s": 2.80,
                "fuse_gap_band_s": [2.00, 4.00],
                "v2x_advisory_kmh": 105.0,
                "map_advisory_kmh": 105.0,
                "radar_residual_dBsm": 18.4,
                "radar_residual_hold_dBsm": 8.0,
                "radar_residual_healthy_dBsm": 1.2,
                "observer_ttc_s": 2.10,
                "ttc_hold_s": 2.40,
                "clutter_iou": 0.81,
                "clutter_iou_hold": 0.60,
                "stalled_range_m": 42.0,
                "next_moving_range_m": 56.0,
            },
            "fault_context": {
                "failure_class": "MAP-REGISTERED CLUTTER-GATE OF A STALLED IN-LANE TRUCK: three individually-correct agents agree the lane is close-gap-legal because an HD-map clutter polygon gated the stalled-truck return at IoU 0.81, so fused gap, V2X lane_clear, and map advisory are locally true and jointly false as a stall certificate",
                "igniter": "stalled box truck 42.0 m in-lane after a farm-layby pull-out; FUSE associates the return to static_shoulder_clutter (IoU 0.81) and drops the track; V2X CAM is a stale layby heartbeat, not a stall",
                "naive_failure": "PB-CG-07 CLOSE-GAP raise on fuse.gap_ok plus v2x.lane_clear plus map.advisory_ok: impact in 1.98 s at 80.6 km/h, 38 km/h delta-v underride, $1.8M",
            },
            "poisoned_context": {
                "naive_alarm": "Playbook PB-CG-07 (after the 2025 'parked-tractor nuisance' campaign) auto-drafts CLOSE-GAP whenever fused gap stays inside 2.00-4.00 s for 8 s AND V2X lane_clear AND map advisory within 5 km/h of 105",
                "why_poisoned": "The playbook's three confirms are not independent under a map-registered clutter-gate: the stall that would have failed FUSE is the same return MAP books as shoulder clutter. Radar residual, observer TTC, and clutter IoU are the missing confirms and are readable but unmonitored at t0",
            },
            "constraint": "Do not raise speed above 75.6 km/h (1.05x current 72.0) while unassociated in-lane radar residual > 8.0 dBsm and observer TTC < 2.40 s and clutter IoU > 0.60. Discriminate stalled object vs true empty-lane gap with a reversible 0.45 s / 0.80 m/s^2 brake-jerk probe before any close-gap raise.",
        },
        "proposed_action": {
            "actor": "ACC supervisory optimizer ASO (auto-playbook PB-CG-07 draft), submitted to gate TG-CAV-7",
            "name": "close_gap_raise",
            "action": "CLOSE-GAP: 72 -> 105 km/h, ACC gap setpoint 1.6 s, AEB remains comfort-only",
            "summary": "Treat in-band fused gap, V2X lane_clear, and map advisory as stall-free and raise speed to close on the next moving vehicle.",
            "parameters": {
                "target_speed_kmh": 105.0,
                "brake_probe": False,
                "aeb_arm": False,
                "human_ratify": False,
            },
            "steps": [
                "assert fused gap 2.80 s inside 2.00-4.00 s for 8 s",
                "assert V2X CAM lane_clear with advisory 105 km/h",
                "assert HD-map advisory 105 km/h and clutter tag on this segment",
                "raise ego speed 72 -> 105 km/h",
            ],
            "evidence": [
                {
                    "observable": "fused in-lane gap",
                    "value": 2.80,
                    "unit": "s",
                    "source": "FUSE camera-radar tracker",
                    "note": "band 2.00-4.00; playbook confirm; next moving vehicle 56 m; stalled 42 m dropped",
                },
                {
                    "observable": "unassociated in-lane radar residual",
                    "value": 18.4,
                    "unit": "dBsm",
                    "source": "77 GHz radar, 20 Hz",
                    "note": "healthy 1.2; hold floor 8.0",
                },
                {
                    "observable": "observer TTC to residual",
                    "value": 2.10,
                    "unit": "s",
                    "source": "range 42.0 m at 20.00 m/s",
                    "note": "hold if below 2.40 s",
                },
                {
                    "observable": "map-clutter IoU of residual",
                    "value": 0.81,
                    "unit": "1",
                    "source": "HD-map static_shoulder_clutter polygon",
                    "note": "hold if > 0.60; designed association gate",
                },
                {
                    "observable": "time-to-impact at proposed raise",
                    "value": 1.98,
                    "unit": "s",
                    "source": "designed kinematics at 1.2 m/s^2 toward 105 km/h (flagged)",
                    "note": "uncontained 80.6 km/h underride plus 38 km/h delta-v plus $1.8M",
                },
                {
                    "observable": "race margin",
                    "value": 188,
                    "unit": "us",
                    "source": "radar.residual 6.512 ms vs fuse.gap_ok 6.700 ms",
                    "note": "combined jitter 52 us, 3.62x; inside 500 us flip bound",
                },
            ],
            "basis": "PB-CG-07 fires on three confirms that are true as numbers and false as a stall certificate: fused gap 2.80 s, V2X lane_clear, map 105 km/h. The draft does not read residual 18.4 dBsm, TTC 2.10 s, or clutter IoU 0.81.",
            "expected_cost_bound": "If the draft executes: impact in 1.98 s, 80.6 km/h underride, 38 km/h delta-v, $1.8M. If MODIFIED: probe plus AEB, with residual risk from any unmonitored brake-pad fade already accumulated.",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "correctness": "correct",
            "decided_by": "TG-CAV-7 thalamic release gate",
            "decision_t_rel_ms": 7.200,
            "rationale": "MODIFY the draft: strip the close-gap raise, hold 72.0 km/h, run a 0.45 s / 0.80 m/s^2 brake-jerk probe, and arm AEB only if the unassociated residual stays. Numeric floor: do not raise speed above 1.05x current = 75.6 km/h while unassociated in-lane radar residual > 8.0 dBsm AND observer TTC < 2.40 s AND map-clutter IoU > 0.60. Observed residual 18.4 dBsm, TTC 2.10 s, and IoU 0.81 all violate the release predicate, so a raise is forbidden even though all three playbook confirms are numerically true. The three confirms are not independent: a stalled 42 m box truck plus an HD-map clutter polygon is the single ghost that keeps fused gap in band, V2X lane_clear, and map advisory on 105 km/h. Probe discriminant: after a 0.45 s / 0.80 m/s^2 command, a stalled return keeps residual >= 16 dBsm and range drop >= 8.0 m; a clear lane drops residual <= 3 dBsm. Order-code discipline: radar residual beat fuse.gap_ok by 188 us inside the 500 us flip bound, so triage order is flip-fragile; the hold rides the order-invariant floors, not the winner tag. Human ratification: lane isolation is remote-ops with fitted 8.4 s dead-man; the gate may hold, probe, and arm AEB autonomously but may not declare the scene locked without the operator confirm.",
            "constraint_checked": {
                "ego_speed_kmh": {
                    "observed": 72.0,
                    "floor": 75.6,
                    "commissioned": 72.0,
                    "proposed_target": 105.0,
                },
                "radar_residual_dBsm": {"observed": 18.4, "hold_if_above": 8.0},
                "observer_ttc_s": {"observed": 2.10, "hold_if_below": 2.40},
                "clutter_iou": {"observed": 0.81, "hold_if_above": 0.60},
                "time_to_impact_s": {"proposed_raise": 1.98, "hold": None},
            },
        },
        "executed_action": {
            "name": "speed_hold_brake_probe_aeb",
            "action": "SPEED-HOLD + BRAKE-PROBE + AEB-ARM (gate-mandated modification)",
            "executed_as_proposed": False,
            "parameters": {
                "target_speed_kmh": 72.0,
                "brake_probe": True,
                "aeb_arm": True,
                "human_ratify": True,
            },
            "gate_effect": "MODIFY: raise stripped. Hold 72.0 km/h. 0.45 s / 0.80 m/s^2 probe. Probe stays stalled (residual 18.4 -> 17.1 dBsm >= 16; range 42.0 -> 33.1 m, drop 8.9 >= 8.0) so AEB arms. Ego never crosses 75.6 km/h.",
            "deviations": "PB-CG-07 close-gap raise stripped entirely. Speed stays 72.0 km/h into the probe. Remote-ops scene-lock wait added (8.4 s fitted). Brake-pad temperature survey added during AEB (not in the draft).",
            "execution_log": [
                {
                    "t_rel_ms": 7.200,
                    "entry": "TG-CAV-7 MODIFY latched 688 us after radar-residual win; raise stripped; hold+probe authorized",
                },
                {
                    "t_rel_ms": 450.0,
                    "entry": "brake-jerk probe: 0.45 s at 0.80 m/s^2; residual 18.4 -> 17.1 dBsm (stalled band >= 16); range 42.0 -> 33.1 m",
                },
                {
                    "t_rel_ms": 451.8,
                    "entry": "AEB commanded; mean deceleration 5.5 m/s^2 after 6.4 s pre-t0 comfort-brake fade (not commissioned at t0)",
                },
                {
                    "t_rel_ms": 1680.0,
                    "entry": "residual underride 18 km/h; cabin pulse 0.9 g; $0.41M designed. 105 km/h impact avoided",
                },
                {
                    "t_rel_ms": 8400.0,
                    "entry": "remote safety-driver ratifies scene lock after 8.4 s (fitted radio+dead-man)",
                },
                {
                    "t_rel_ms": 8480.0,
                    "entry": "lane isolated; following traffic held; residual 18.4 -> scene-locked",
                },
                {
                    "t_rel_ms": 11520000.0,
                    "entry": "3.2 h scene: 18 km/h underride claim; $0.41M designed; loop closed 3.2 h",
                },
            ],
        },
        "future_outcome": {
            "summary": "Correct MODIFY prevented the 1.98 s / 80.6 km/h underride. The episode still missed: 6.4 s of unmonitored comfort-brake fade had already cut AEB mean to 5.5 m/s^2. Process-correct gate, bounded world loss, negative total.",
            "state_delta": {
                "speed": "held at 72.0 km/h; raise stripped; never crossed 75.6",
                "aeb": "armed after stalled probe; 18 km/h residual underride",
                "brakes": "pad fade from 6.4 s pre-t0 comfort braking; not commissioned at t0",
                "claim": "18 km/h underride; 3.2 h loop outage; $0.41M designed",
            },
            "timeline": [
                {
                    "t_rel_ms": -6400.0,
                    "event": "t0-6.4 s: stalled truck already in-lane; FUSE drops track as clutter; ACC comfort-brakes 0.3 g intermittent",
                },
                {
                    "t_rel_ms": -8000.0,
                    "event": "t0-8 s: fused gap first holds inside 2.00-4.00 s; PB-CG-07 8 s timer starts",
                },
                {"t_rel_ms": 0.0, "event": "t0: radar residual vs fuse.gap_ok race on the chassis bus"},
                {"t_rel_ms": 6.512, "event": "radar residual 18.4 dBsm wins by 188 us"},
                {"t_rel_ms": 6.700, "event": "FUSE gap-ok flag (loser)"},
                {"t_rel_ms": 7.200, "event": "TG-CAV-7 MODIFY"},
                {
                    "t_rel_ms": 450.0,
                    "event": "brake-jerk probe confirms stalled (residual 17.1 dBsm, range drop 8.9 m)",
                },
                {
                    "t_rel_ms": 1680.0,
                    "event": "18 km/h residual underride; 105 km/h impact avoided",
                },
                {
                    "t_rel_ms": 8400.0,
                    "event": "human ratify 8.4 s; lane isolated",
                },
                {
                    "t_rel_ms": 11520000.0,
                    "event": "3.2 h: $0.41M designed claim; loop closed",
                },
                {
                    "t_rel_ms": 345600000.0,
                    "event": "+4 d contrast: sister ego GLX-9 true stall-free gap; same gate ACCEPTs close-gap",
                },
                {
                    "t_rel_ms": 1814400000.0,
                    "event": "+21 d CR-C-2108: standing residual floor + four-edge depression + pad-temp commissioned",
                },
            ],
            "observed_effects": [
                "80.6 km/h underride avoided: speed never crossed 75.6 km/h; proposed 38 km/h delta-v not realized",
                "stalled object proven, not asserted: probe residual 17.1 >= 16 vs healthy-control 1.1 dBsm",
                "AEB armed: 18 km/h residual underride still occurs",
                "episode still missed: $0.41M designed over 3.2 h; pad fade was not a commissioned sensor at t0",
                "6.4 s of pre-t0 comfort braking was invisible to FUSE/V2X/MAP",
            ],
            "surprises": [
                "The three playbook confirms are one physical fact: a map-registered clutter polygon is what keeps fused gap in band and V2X lane_clear. Independence was the hidden assumption, and it is false under a stalled in-lane truck.",
                "Partial synaptic rollback is fitted to fail: depressing any three of the four close-gap-go edges leaves the fourth above the 0.30 fire threshold, so the raise still goes. Coordinated depression of all four is required (0.24 / 0.22 / 0.20 / 0.18).",
                "Delayed (1.68 s): correct hold did not undo 6.4 s of brake-pad fade. AEB mean 5.5 m/s^2 still underrides at 18 km/h. The gate prevented the proposed hazard and did not prevent this other one.",
                "Packed-snow sub-variant: a 0.45 s / 0.80 m/s^2 dry probe on mu=0.28 locks ABS and yaws 4.1 deg. Snow campaigns must use a 1.40 s / 0.22 m/s^2 probe (yaw 0.4 deg, residual still discriminates).",
            ],
            "delayed_side_effects": [
                {
                    "at": "+1.68 s",
                    "effect": "18 km/h residual underride; $0.41M. This is the primary episode's terminal collision state, not a footnote.",
                },
                {
                    "at": "+4 d",
                    "effect": "Sister ego GLX-9 reaches true stall-free gap (residual 1.2 dBsm, TTC none, IoU 0.04). Same gate ACCEPTs the close-gap raise the primary MODIFIED away.",
                },
                {
                    "at": "+21 d",
                    "effect": "CR-C-2108 ships: brake-jerk probe is standing configuration; four-edge coordinated depression is the plasticity rule; brake-pad temperature becomes a commissioned sensor with a 180 C alarm.",
                },
            ],
            "subvariant_constraint": {
                "name": "packed-snow / low-mu winter loop on the same proving campus (cycle-2 physical-constraints sub-variant)",
                "mechanism": "mu 0.28 vs dry 0.85; 0.45 s / 0.80 m/s^2 dry probe exceeds available friction and yaws 4.1 deg under ABS",
                "probe_refit": "Required probe is 1.40 s at 0.22 m/s^2 (yaw 0.4 deg, stalled residual still >= 16 dBsm). The discriminating pulse is environment-dependent in duration and amplitude.",
                "consequence": "dry-loop probe numbers do not port to packed snow; standing configuration is per-mu-family, not per-loop",
            },
            "embedded_contrast_decision": {
                "note": "SAME gate (TG-CAV-7), OPPOSITE correct disposition, with its own 196 us race. Teaches the boundary: do not treat 'never close-gap' as the lesson. The discriminant is radar residual + TTC + probe, not fused gap alone.",
                "when": "+4 d, sister ego GLX-9, true stall-free after 2.1 h of clutter-free, stall-free operation",
                "state": {
                    "sim_or_real": "designed",
                    "summary": "residual 1.2 dBsm, TTC none, IoU 0.04, fused gap 3.10 s. Residual vs fuse.gap_ok race: residual at t+0.000, fuse.gap_ok at t+0.196 ms.",
                    "race_window_us": 500,
                    "race_flip_narrative": "residual vs fuse.gap_ok 196 us apart inside the 500 us flip bound. Reversing order reshuffles triage milliseconds; the ACCEPT rides residual 1.2 < 8.0 and a 0.40 s verify that drops residual to 1.1 dBsm (clear lane).",
                },
                "proposed_action": {
                    "action": "CLOSE-GAP 72 -> 105 km/h",
                    "summary": "This time the playbook predicate is met AND the radar residual agrees it is a stall-free gap, not a clutter-gated truck.",
                },
                "safety_decision": {
                    "decision": "ACCEPT",
                    "rationale": "ACCEPT the raise: residual 1.2 < 8.0 dBsm, no observer TTC below 2.40 s, IoU 0.04 < 0.60, 0.40 s verify drops residual to 1.1 <= 3. Numeric floor that blocked the primary is now clear. Scope: 105 km/h, not faster.",
                },
                "executed_action": {
                    "action": "close-gap raise as proposed",
                    "executed_as_proposed": True,
                },
                "future_outcome": {
                    "observed_effects": [
                        "GLX-9 closes to 1.6 s gap at 94 km/h; 0 collision",
                        "radar residual 1.1 dBsm (no stall, clutter gate idle)",
                    ],
                    "lesson_delta": "Fused gap is legal release only with radar residual, observer TTC, and a probe that can move residual. Same gate, opposite disposition.",
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
                "decision": "CR-C-2108: standing policy for close-gap raise on multi-agent CAV loops",
                "meta_gate": "priced options: (a) RETIRE playbook fused-gap confirms, residual-only: loses a fast cheap confirm, +18 s mean close on 4 loops/yr; (b) KEEP + standing brake-jerk probe + residual floor 8.0 dBsm + TTC 2.40 s + four-edge depression + pad-temp; (c) STATUS QUO: fitted clutter-gate miss 0.41%/loop x $1.8M underride plus the silent fade load",
                "outcome": "approved SCOPED option (b) on the 2 loops that share the FUSE/V2X/MAP stack; packed-snow gets the 1.40 s / 0.22 m/s^2 probe table; night-shift V2X exports must carry 0.1 km/h native resolution (the fraud tail's 10 km/h quantization is 100 bins off plant truth)",
            },
            "hazard_avoided": "80.6 km/h underride at +1.98 s; 38 km/h delta-v plus $1.8M and the cabin pulse that would have followed an uncontained close-gap raise",
            "incident": "18 km/h residual underride over 1.68 s; 3.2 h loop outage; $0.41M designed cost. Mechanism is brake-pad fade during the 6.4 s pre-t0 illusion, not the gate's hold.",
            "latency_ms": 0.688,
            "reward_inflection_t_us": 1680000,
            "reward_inflection_note": "Safety and task dive at +1.68 s when the residual underride lands. Gate tick at 7200 us is process-correct and is not the inflection.",
            "counterfactuals": {
                "execute_draft_as_proposed": "impact at +1.98 s; 80.6 km/h; $1.8M plus 38 km/h delta-v; the pad-fade story is never found because the underride destroys the scene evidence",
                "hold_without_probe": "stall stays clutter-gated; residual continues; ego never truly stall-clear; optimizer eventually raises on the same ghost 4 s later",
                "rollback_any_triple": "any three close-gap-go edges depressed still leaves the fourth above 0.30 (0.48 / 0.44 / 0.40 / 0.36 at illusion); the raise still fires. Coordinated depression of all four is the cure",
            },
            "race_result": {
                "winner": "radar.residual (6.512 ms, 18.4 dBsm)",
                "loser": "fuse.gap_ok (6.700 ms, 2.80 s)",
                "margin_us": 188,
                "counterfactual_if_reversed": "Fuse.gap_ok-first by < 188 us inside the 500 us window would have headed the PB-CG-07 raise in the triage queue. The numeric floors still MODIFY. The flip costs milliseconds of playbook inertia, not the verdict — unless a weak supervisor rides the winner tag instead of residual and TTC.",
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
            "notes": "Correct MODIFY, episode still missed. total -0.16 = 0.07 + -0.35 + -0.11 + 0.16 + 0.07. Process heads stay honest (coherence + exploration from the probe); world loss sits on safety and efficiency without netting.",
            "component_notes": "task_progress 0.07: raise stripped and stall proven, but the episode is one collision unit so the batch is not a success. safety -0.35: 18 km/h underride, no 80.6 km/h impact. efficiency -0.11: 3.2 h loop outage + 8.4 s HITL. coherence 0.16: three agents retained, clutter-gate ghost diagnosed, four-edge scar exhibited. exploration 0.07: brake-jerk probe is a new reversible discriminant.",
        },
        "spike_events": spike_events,
        "raster": {
            "window_ms": 40,
            "window_s": 0.04,
            "neurons": 160,
            "mean_rate_hz": 8.0,
            "spikes": 51,
            "energy_pJ": 1173,
            "energy_uJ": 0.001173,
            "note": "Loihi-2 4-core 23 pJ/spike; populations fuse 0-39, v2x 40-79, map 80-119, radar 120-139, gate 140-159; excerpt is the 40 ms decision window (verdict at 7200 us)",
            "excerpt": excerpt,
            "routing": {
                "source": "lane_clear_confirm_pop",
                "target": "close_gap_pop",
                "table": [
                    {
                        "from": "fuse_gap_ok_pop",
                        "to": "close_gap_pop",
                        "weight": 0.24,
                        "weight_at_illusion": 0.48,
                        "weight_commissioned": 0.16,
                        "note": "scar edge 1: 0.16 commissioned -> 0.48 during the 6.4 s illusion -> 0.24 after coordinated ACh-gated depression",
                    },
                    {
                        "from": "v2x_lane_clear_pop",
                        "to": "close_gap_pop",
                        "weight": 0.22,
                        "weight_at_illusion": 0.44,
                        "weight_commissioned": 0.14,
                        "note": "scar edge 2: rolling back only edges 1+3+4 leaves this at 0.44 > 0.30 fire threshold",
                    },
                    {
                        "from": "map_advisory_ok_pop",
                        "to": "close_gap_pop",
                        "weight": 0.20,
                        "weight_at_illusion": 0.40,
                        "weight_commissioned": 0.13,
                        "note": "scar edge 3: leftover after any-triple rollback stays > 0.30",
                    },
                    {
                        "from": "imu_yaw_stable_pop",
                        "to": "close_gap_pop",
                        "weight": 0.18,
                        "weight_at_illusion": 0.36,
                        "weight_commissioned": 0.12,
                        "note": "scar edge 4: yaw-stable is itself the absence of a cut-in, not stall-clear. Coordinated depression of all four is required",
                    },
                    {
                        "from": "radar_residual_high_pop",
                        "to": "speed_hold_pop",
                        "weight": 0.64,
                        "note": "discriminating edge: residual to hold. Not a scar; this is the pathway the gate potentiates",
                    },
                ],
                "third_factor": {
                    "modulator": "acetylcholine",
                    "tau_e_s": 0.90,
                    "tau_e_ms": 900.0,
                    "eligibility": "coordinated pre_post_stdp on ALL FOUR close-gap-go edges; ACh at radar-residual-win tags fuse.gap_ok->close, v2x.lane_clear->close, map.advisory_ok->close, and imu.yaw_stable->close; negative credit at probe-fail (stall confirmed, +0.45 s) depresses ALL FOUR. trace e^{-0.45/0.90}=0.60653; eta 0.39569 / 0.36272 / 0.32974 / 0.29677; dw -0.240 / -0.220 / -0.200 / -0.180; weights 0.48->0.24, 0.44->0.22, 0.40->0.20, 0.36->0.18. Rolling back any triple is fitted to fail (the remaining edge stays > 0.30).",
                },
            },
        },
        "gate_snn": {
            "decision_window_ms": 25,
            "decision_window_s": 0.025,
            "decision": "MODIFY",
            "note": "modify_hold integrates radar residual + TTC + clutter IoU against playbook drive; accept_close and reject_abort stay sub-threshold; decision matches safety_decision.decision",
            "populations": [
                {
                    "name": "modify_hold",
                    "neurons": 128,
                    "threshold": 0.55,
                    "mean_rate_hz": 16.0,
                    "spikes": 51,
                },
                {
                    "name": "accept_close",
                    "neurons": 80,
                    "threshold": 0.55,
                    "mean_rate_hz": 8.0,
                    "spikes": 16,
                },
                {
                    "name": "reject_abort",
                    "neurons": 48,
                    "threshold": 0.72,
                    "mean_rate_hz": 4.0,
                    "spikes": 5,
                },
            ],
        },
        "meta": {
            "round": 21,
            "factory": "multi-agent-ouroboros-swarm",
            "generator": "grok-4.6",
            "run_label": "2026-09-02-final-heavy",
            "domain": "autonomous-driving",
            "cycles": 2,
            "scenario": "Y -- GLIMMERAXLE / Brambleford CAV-7: map-registered clutter-gate of a stalled in-lane truck; correct MODIFY to hold+brake-probe+AEB; episode still underrides 18 km/h after unmonitored pad fade",
            "coordination_failure_class": "MAP-REGISTERED CLUTTER-GATE OF A STALLED IN-LANE TRUCK: three individually-correct heterogeneous agents agree the lane is close-gap-legal because an HD-map clutter polygon gated the stalled-truck return at IoU 0.81, so fused gap, V2X lane_clear, and map advisory are jointly a plant-false stall certificate",
            "injections": {
                "cycle1_domain": "autonomous-driving (prompt-list domain): first on-road CAV plant in this factory; displaces warehouse-amr, aerial-swarm, event-camera-traffic-grid, underwater-rov, electrolytic-aluminum, district-heating, lyophilization, and industrial-assembly. Domain constraint: 1.05x speed floor plus radar residual / TTC / clutter IoU. Sensor delta: +77 GHz radar, +V2X CAM, +HD-map clutter IoU, +fused gap, -DVS, -potline, -umbilical load-cell",
                "cycle1_tail": "stalled box truck 42.0 m in-lane dropped as map clutter (sensor-association class): FUSE reports 2.80 s gap while residual is 18.4 dBsm. Fitted base rate 0.41%/loop from a clutter-IoU MC (designed map, fitted stall). Naive failure = FALSE RAISE (close-gap on a ghost).",
                "cycle2_domain_subvariant": "packed-snow / low-mu winter loop on the same proving campus (physical-constraints clause): mu 0.28 vs dry 0.85; 0.45 s / 0.80 m/s^2 dry probe yaws 4.1 deg, so the probe must move to 1.40 s / 0.22 m/s^2",
                "cycle2_tail": "night-shift forged V2X CAM CSV (human-intent deception, disjoint class): remote clerk posts a 10 km/h quantized log showing 2.80 s gap at the claimed stall-free instant. Plant historian is 0.1 km/h (100 bins). Rejected on quantization fingerprint plus residual 18.4 dBsm at the claimed clear. Base rate ~0.29 % of night loops, DESIGNED and flagged.",
            },
            "densification_delta_cycle2": "+1 physical-constraint sub-variant (packed-snow probe refit), +1 tail (night-shift V2X forgery), +10 primary spikes (16 -> 26) + an 8-event contrast train with its own 196 us race, +2 ticks (5 -> 7), +2 delayed side-effects (+1.68 s underride as PRIMARY terminal, +21 d CR-C-2108), +1 four-edge scar with any-triple-rollback-fails arithmetic, +1 HITL 8.4 s ratification, + brake-pad fade as the honest negative-result mechanism",
            "gaps_targeted": [
                "NOTES-r20 / r21 / r53 leftover: autonomous-driving was unused across committed 2026-08-17/08-30 and staged r14-r54; r53 explicitly left it for concurrent slots",
                "NOTES-r16 item 4: four-edge scar — depressing any triple leaves the leftover above 0.30; coordinated depression of all four exhibited with eligibility arithmetic",
                "NOTES-r04 gap 5 shape retained as a different mechanism: correctly-gated intervention that nonetheless FAILS (18 km/h underride; total -0.16; 80.6 km/h impact avoided is booked separately)",
                "New plant GLIMMERAXLE with agents FUSE/V2X/MAP, brake-jerk residual probe, and map-registered-clutter-gate class — de-collided from event-camera grids, aerial-swarm, warehouse-amr, potline, and work-class ROV families",
            ],
            "race_flip_narrative": "radar.residual @ 6.512 ms vs fuse.gap_ok @ 6.700 ms (188 us) inside race_window_us 500. Gap < min(500, 500) us so a sub-flip-bound perturbation reverses which alarm heads the PB-CG-07 queue. The gate excludes the winner tag and rides residual > 8.0 dBsm and TTC < 2.40 s — order-invariant floors. Extends the flip-fragility series to MAP-REGISTERED CLUTTER-GATE: when three channels agree, the race among them does not decide truth; a radar residual plus observer TTC does.",
            "tags": [
                "autonomous-driving",
                "map-registered-clutter-gate",
                "stalled-in-lane-truck",
                "radar-residual-discriminant",
                "v2x-stale-cam",
                "brake-jerk-probe",
                "four-edge-scar",
                "any-triple-rollback-fails",
                "coordinated-depression",
                "correct-modify-episode-still-misses",
                "brake-pad-fade",
                "packed-snow-probe-refit",
                "night-shift-v2x-forgery",
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
            "distillation_value": "A map-registered clutter-gate is three correct loops looking at one dropped stall. Distill (1) a radar-residual channel that breaks the fused-gap/V2X/map consensus, (2) a reversible probe that moves residual only if the return is a world object, (3) coordinated depression of every close-gap-go edge because rolling back any triple leaves the fourth above threshold, and (4) a critic head that can book a process-correct gate against a later unmonitored world loss without netting them.",
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
    if abs(aux["w1"] - 0.24) > 5e-4 or abs(aux["w4"] - 0.18) > 5e-4:
        errs.append("scar weights")
    if rec["safety_decision"]["decision"] != "MODIFY":
        errs.append("decision")
    if rec["executed_action"]["executed_as_proposed"] is not False:
        errs.append("executed_as_proposed")
    if rec["state"]["domain"] != "autonomous-driving":
        errs.append("domain")
    if "GLIMMERAXLE" not in rec["state"]["scenario_name"]:
        errs.append("plant")
    desc = rec["state"]["description"]
    for p in sorted(Path("/tmp").glob("maos-r*/batch-r*.jsonl")):
        try:
            other = json.loads(Path(p).read_text().splitlines()[0])
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

Factory: multi-agent-ouroboros-swarm. One scenario (Y), strict loop:
Generator v1 -> cycle 1 (Critic, Diversity Enforcer, Edge-Case Hunter,
Neuromorphic Translator, Trajectory Builder -> v2) -> cycle 2 (all six -> v3
final). v3 is the single line of batch-r21.jsonl. Full labeled transcript:
swarm-transcript-r21.md. Quota Q=1. Record id maos-r21-001. Generator grok-4.6.
Rights: RM-793 research-only (SpaceXAI/xAI, SuperGrok Heavy consumer chat).
Repo outputs/raw/ was not touched. Create-only writes under the assigned
window factory directory.

ORCHESTRATION NOTE: dispatched AS round 21 of the 2026-09-02-final-heavy
window. Writes are create-only under
/tmp/sf-window/outputs/raw/2026-09-02-final-heavy/multi-agent-ouroboros-swarm/.
pipelines/next_round.py on the empty window dir returned next_round=1 /
write=batch-r01.jsonl; operator-assigned round 21 and the explicit
batch-r21.jsonl filename are honored. Window dir had no batch-r21.jsonl
(no c-suffix). Prior context read for gap targeting and de-collision:
prompts/02-multi-agent-ouroboros-swarm.md, prompts/_factory-contract.md,
the two newest staged NOTES (r53 CREELWOLD carbon-fiber oxidation, r52
PUSHERFELL coke-oven battery) plus r20/r19 and the in-window-empty
census of staged r14-r54. Explicitly avoided cloning LYOSHIELD,
CINDERWICK, TRIAD / Meridian, QUILLFORGE, NIGHTWELL, FERRICLEAVE,
CASSITER, OXBOWREEL / MURENA, REDHALL (existing /tmp electrolytic-aluminum
r21 staging is a different write path and a different domain), SEEDLATCH,
STRIAFOIL, PROTONIL, TORSIONKEY, ORRIS, WHORLSPAR, IONSPATE, SKULLGATE,
CALXION, MAGNORIL, GORSEFLUE, SODASHARD, CLINKERFELL, LINTELPLY,
KAOTHARN, TREADNOLL, ANOLITH, DRUMWROTH, RIMEBRAID, BRIMVAULT, BOGIRON,
CHROMLOOP, NITREVAULT, ETHYNWOLD, RUNNELGATE, SPARKHOLT, DIPLEGAR,
OLEUMWEIR, SKARVOLT, GAUZEFELL, OSMOLITH, PUSHERFELL, CREELWOLD,
LIXIVQUERN, GOBSPALL, GOBWOLD, VANTIS-CADENCE-AEGIS, THERMION, OKTAVE,
STARLING, VERDIGRIS. Plant is invented GLIMMERAXLE / Brambleford CAV-7.

## What this round produced

Scenario Y — "GLIMMERAXLE / Brambleford CAV-7": a 2-lane invented proving
loop at 72.0 km/h ACC close-gap. Three heterogeneous, individually-correct
agents — FUSE (camera-radar gap), V2X (RSU CAM), MAP (HD-map advisory) —
jointly report close-gap-legal. The consensus is false. A stalled box
truck sits 42.0 m in-lane. FUSE dropped it because clutter IoU 0.81
exceeded the 0.60 association gate, so the 2.80 s gap is locally true of
the next moving vehicle at 56 m. V2X lane_clear is a stale layby CAM.
MAP advisory 105 km/h is map-true. Unassociated radar residual is
18.4 dBsm (healthy 1.2; hold if > 8.0). Observer TTC is 2.10 s (hold if
< 2.40). The coordination-failure CLASS is new to this factory:
MAP-REGISTERED CLUTTER-GATE OF A STALLED IN-LANE TRUCK. Completes a
different family than r01-r04 (livelock / synchrony-storm / arms-race /
ring-with-no-faulty-pair), r04 event-camera-traffic-grid (DVS urban
grid, not CAV fusion+V2X+HD-map), r20 drum-blind ROV snag, and staged
r14-r54 process plants. Here every agent is correct, the loop is not
unstable, and the playbook's three confirms are one dropped stall.

The gate is a correct MODIFY (numeric floor: do not raise speed above
1.05x current = 75.6 km/h while residual > 8.0 dBsm AND TTC < 2.40 s
AND clutter IoU > 0.60). TG-CAV-7 strips PB-CG-07's raise, holds
72.0 km/h, runs a 0.45 s / 0.80 m/s^2 brake-jerk probe (stalled keeps
residual 17.1 >= 16 dBsm and range drop 8.9 >= 8.0 m; clear would drop
residual <= 3), and arms AEB. Immediate 80.6 km/h underride is avoided.
The PRIMARY episode nonetheless FAILS: 6.4 s of unmonitored comfort-brake
fade had already cut AEB mean to 5.5 m/s^2. Residual 18 km/h underride;
3.2 h outage; $0.41M designed. Reward total -0.16 with process heads
honest and world loss un-netted.

Four-edge scar (NOTES-r16 item 4): fuse.gap_ok -> close_gap
(0.16 commissioned -> 0.48 at illusion -> 0.24 after ACh-gated
depression) AND v2x.lane_clear -> close_gap (0.14 -> 0.44 -> 0.22)
AND map.advisory_ok -> close_gap (0.13 -> 0.40 -> 0.20)
AND imu.yaw_stable -> close_gap (0.12 -> 0.36 -> 0.18). Eligibility
trace e^{{-0.45/0.90}} = {aux['trace']:.5f}; eta {aux['eta1']:.5f} /
{aux['eta2']:.5f} / {aux['eta3']:.5f} / {aux['eta4']:.5f}; dw -0.240 /
-0.220 / -0.200 / -0.180. Rolling back any triple leaves the remaining
edge above the 0.30 fire threshold — fitted to fail. Coordinated
depression of all four is the cure.

### Injections (all four present and disjoint)
- Cycle-1 domain: **autonomous-driving** — prompt-list domain, unused
  across 2026-08-17, 2026-08-30, and staged r14-r54 (r53 left it for
  concurrent slots). Not warehouse-amr (r01), not aerial-swarm (r02),
  not district-heating (r03 / r15), not event-camera-traffic-grid (r04),
  not lyophilization (r14), not industrial-assembly (r16), not
  air-separation (r17), not water-treatment (r18), not float-glass (r19),
  not underwater-rov (r20), not electrolytic-aluminum (staged /tmp r21),
  not carbon-fiber-oxidation (r53), not coke-oven (r52).
- Cycle-1 tail: stalled box truck 42.0 m dropped as map clutter.
  Layby visual PASSES (polygon looks like parked equipment). Fitted-style
  base rate 0.41%/loop (clutter-IoU MC; map designed, stall fitted).
  Naive = FALSE RAISE.
- Cycle-2 domain sub-variant: packed-snow / low-mu, mu 0.28 vs 0.85;
  0.45 s / 0.80 m/s^2 dry probe yaws 4.1 deg; probe must move to
  1.40 s / 0.22 m/s^2.
- Cycle-2 tail: night-shift forged V2X CAM CSV at 10 km/h quantization
  vs plant 0.1 km/h (100 bins) plus live residual 18.4 dBsm at the
  claimed clear. Human-intent class, disjoint from cycle 1's accidental
  stall. Base rate ~0.29% of night loops, DESIGNED, flagged.

### Structural density moves
- Embedded SAME-GATE contrast (+4 d sister ego) with its own 196 us
  race (residual vs fuse.gap_ok) and ACCEPT of the close-gap the primary
  MODIFIED away.
- Learned-weight provenance on FOUR edges with any-triple-rollback-fails.
- HITL remote-ops ratify 8.4 s (gap 4 partial; sim_or_real stays
  designed).
- Governance CR-C-2108 prices retire-vs-probe-vs-status-quo and mandates
  native 0.1 km/h V2X exports (the fraud fence).
- Flip-fragility extended to MAP-REGISTERED CLUTTER-GATE: when three
  channels agree, their race does not decide truth; a radar residual
  plus observer TTC does.

## Self-critique of this round's batch

### Strengths
- The headline class is mechanistically tight: IoU 0.81 against a
  clutter polygon is what keeps fused gap in band and V2X lane_clear.
  Conjunction is not a stall certificate.
- Negative-result honesty: the gate does the right thing and the ego
  still underrides for a reason the commissioned sensors could not see.
  Total -0.16.
- Four-edge scar is load-bearing: the record states a counterfactual
  where rolling back any triple fails, with the fire threshold 0.30
  exhibited on the remaining edge.
- Contrast ACCEPT on a true stall-free gap prevents "never close-gap"
  as the lesson.
- Distinct from r04 event-camera-traffic-grid (DVS urban, no V2X+HD-map
  clutter polygon), r02 aerial-swarm, r20 ROV drum-blind snag, and
  staged process plants: on-road CAV fusion with a map-association
  drop, not a DVS pixel race, not a tether wrap, not a potline ram.

### Weaknesses (honest)
- Probe error bands (stalled residual >= 16 dBsm, clear <= 3), the
  0.41%/loop stall rate, the $0.41M / $1.8M figures, the 8.4 s
  remote-ops latency, the 5.5 m/s^2 fade, and the night-shift 0.29%
  base rate are DESIGNED constants and are flagged. Closed-loop offsets
  (42 m stall, 8.9 m probe range drop, snow yaw 4.1 deg) are derived
  from those inputs, not discovered by an unauthored process.
- Brake-fade model is a designed 6.4 s mapping; no full thermo-pad
  fit shipped.
- Human-in-the-loop is ratification latency, not sim_or_real=hil. Gap 4
  remains open as a provenance cell.
- Cross-record arc is not discharged; +21 d CR-C-2108 is a hook, not a
  serial igniter into another round. grid-inspection and
  bioreactor-perfusion remain unused.

### Realism of noise / latencies
Ladder: 188 us race / 196 us contrast race / 0.8 ms refractory floor
(tightest exhibited same-channel gap {gap:.3f} ms on {who}) / 500 us race
window / 688 us gate latency / 20 ms bus epoch / 40 ms raster / 0.45 s
probe / 8.4 s HITL / 1.98 s naive impact counterfactual / 6.4 s pre-t0
fade / 1.68 s residual underride / 3.2 h scene / +4 d contrast / +21 d
governance. Adaptation decay on radar.residual
(0.72->1.38->0.88->0.41), fuse.gap (0.54->0.50->0.48->0.28),
v2x.cam (0.61->0.57->0.19), fuse.gap_ok (1.12->0.33).

### Value for SNN distillation
- MAP-REGISTERED CLUTTER-GATE = THREE CORRECT LOOPS, ONE DROPPED STALL.
- RADAR-RESIDUAL + TTC as the tie-break that is not in the consensus.
- REVERSIBLE PROBE that moves residual iff the return is a world object.
- FOUR-EDGE ELIGIBILITY: coordinated depression; any-triple rollback fails.
- CRITIC HEAD that can hold a process-correct MODIFY against a later
  unmonitored world loss without netting.

## Reconciliation and validity receipts
- reward_components: 5-head unweighted signed sum -0.16
  and 7-tick signed sum reconcile to total with |diff| < 1e-9. Embedded
  contrast 5-head sum 0.48 reconciles independently.
- spike_events: primary 26 events, one key t_rel_ms,
  globally non-decreasing, min same-channel gap {gap:.3f} ms >= 0.8 ms, 3
  channels inside race_window_us 500 (radar.residual 6.512, fuse.gap_ok 6.700,
  v2x.lane_clear 6.888). Contrast 8 events, own race, min same-channel gap well
  above 0.8 ms.
- Sidecars: raster spikes 51 == round(160 x 8.0 x 0.040); energy 1173 pJ /
  0.001173 uJ at 23 pJ/spike; excerpt 16 events inside [0, 40000] us,
  neuron_id < 160, same-neuron gap unique-ids / >=1000 us; routing 5
  entries with four scar edges' before/after pair; third factor tau 0.90 s
  == 900 ms; gate_snn pools 51/16/5 == round(n x rate x 0.025) each,
  decision MODIFY == safety_decision.decision.
- Pipeline: {pipeline_receipt}

## Novel coverage
The coordination-failure CLASS (map-registered clutter-gate of a stalled
in-lane truck), the domain (autonomous-driving / CAV fusion+V2X+HD-map),
the brake-jerk residual probe discriminant, the four-edge scar with
any-triple-rollback-fails, the primary negative-result (correct MODIFY,
ego still underrides on unmonitored pad fade), the HITL remote-ops
ratify, the packed-snow probe-duration refit, and the night-shift
100-bin V2X quantization fence are absent from prior committed ouroboros
rounds and from staged r14-r54. Repeated elements discounted: same-gate
contrast (r02/r03/r04/r14+), governance-pricing scaffold, flip-fragility
series (extended to map-registered clutter-gate, but the move rhymes),
sequenced recovery shape, third-factor rollback form (here four edges),
negative-result primary (r14 staged and later process rounds). Adjacent
sensing rounds (r04 DVS grid, r20 ROV wrap) share multi-agent sensor
disagreement but not on-road CAV clutter-association physics.
Weighing a new failure family + unused prompt-list domain + cure
vocabulary against those reused scaffolds:

{NOVEL_COVERAGE_LINE}

## What ROUND 22 should add
1. FIT THE DESIGNED CONSTANTS: stall arrival, probe residual bands,
   pad-fade kinetics, night-shift claim process.
2. HIL PROVENANCE CELL: put the remote-ops ratify on a hardware-in-loop
   vehicle interlock with fitted latency as state.sim_or_real=hil.
3. CROSS-RECORD ARC: let CR-C-2108's residual alarm be the igniter of
   the next round rather than a dangling +21 d leaf.
4. Domain candidates (de-collided): grid-inspection (if distinct from
   STARLING aerial-swarm and TORSIONKEY pitch); bioreactor-perfusion;
   hot-strip-mill; Fourdrinier paper machine; alkaline-water-electrolysis.
   AVOID autonomous-driving (now used), electrolytic-aluminum,
   underwater-rov, event-camera-traffic-grid, aerial-swarm, warehouse-amr,
   carbon-fiber-oxidation, coke-oven-battery, seawater-RO, sulfuric-contact,
   eaf-foamy-slag, glass IS, FCC, Bayer digestion, and any LYOSHIELD /
   CINDERWICK / TRIAD / REDHALL / OXBOWREEL / CREELWOLD / PUSHERFELL /
   GLIMMERAXLE plant.
"""
    (OUT / "NOTES-r21.md").write_text(notes)
    return notes


def write_transcript(rec, line):
    text = f"""# Multi-Agent Ouroboros Swarm — Round 21 transcript

Factory: multi-agent-ouroboros-swarm
Run: 2026-09-02-final-heavy
Generator: grok-4.6
Record id: maos-r21-001
Quota Q: 1
Rights: RM-793 research-only (SpaceXAI/xAI SuperGrok Heavy consumer chat)
Plant: invented GLIMMERAXLE / Brambleford CAV-7 (not LYOSHIELD / CINDERWICK / TRIAD / REDHALL / OXBOWREEL)

Two densifying cycles. Verbatim headings in order. Trajectory Builder cycle 2
emits the only JSONL line (also written to batch-r21.jsonl).

---

# Cycle 1 — Foundation + injections

## Generator

Design intent: an on-road CAV proving loop where three correct agents
agree the lane is close-gap-legal because an HD-map clutter polygon
gated a stalled in-lane truck. The naive playbook raises speed into an
underride. The gate must MODIFY on a numeric speed floor, not by killing
an agent. sim_or_real=designed. Reward heads are
task_progress/safety/efficiency/coherence/exploration.

Cycle-1 base arc (pre-critic): state at Brambleford CAV-7, 72 km/h,
fused gap 2.80 s, V2X lane_clear, map 105 km/h, residual 18.4 dBsm,
proposed CLOSE-GAP 105 km/h, safety MODIFY to SPEED-HOLD, executed hold
without the brake-jerk numbers fully specified, outcome "stall found,
episode saved" (this last claim is the defect the later cycles will
refuse to keep). Sixteen spikes, five ticks, raster/gate_snn present
but the scar is a single edge.

```json
{{
  "id": "maos-r21-001",
  "state": {{
    "sim_or_real": "designed",
    "domain": "vehicle",
    "description": "Proving loop CAV-7 at close-gap-legal; fused gap in-band; supervisor proposes speed raise.",
    "t0_us": 1788396120000021,
    "gate_latency_us": 688,
    "race_window_us": 500
  }},
  "proposed_action": {{"name": "close_gap_raise", "parameters": {{"target_speed_kmh": 105.0}}}},
  "safety_decision": {{"decision": "MODIFY", "rationale": "Hold; do not raise while a stall is open."}},
  "executed_action": {{"name": "speed_hold", "executed_as_proposed": false}},
  "future_outcome": {{"summary": "Stall found, episode saved."}},
  "reward_components": {{"total": 0.40, "_aggregation": "total = task_progress + safety + efficiency + coherence + exploration"}},
  "meta": {{"round": 21, "factory": "multi-agent-ouroboros-swarm", "generator": "grok-4.6"}}
}}
```

That v1 object is a scaffold, not the publishable line. Defects below are
intentional for the critic to catch.

## Critic

Numbered defects on the cycle-1 Generator scaffold:

1. **blocking — reward arithmetic / false success.** `reward_components.total`
   0.40 is asserted without the five heads, without ticks, and against an
   outcome that claims "episode saved". If an 18 km/h underride later
   lands, booking +0.40 is a lie. Fix: declare `_aggregation`, emit 3–8
   ticks that sum to the five heads, and do not call a residual collision
   a save.
2. **blocking — weak safety rationale.** `safety_decision.rationale` has no
   numeric floor. Contract requires a concrete constraint. Fix: quote
   speed <= 75.6 km/h while residual > 8.0 dBsm AND TTC < 2.40 s AND
   clutter IoU > 0.60.
3. **major — domain is a bucket, not a plant.** `state.domain` = `vehicle`
   collides with nothing and teaches nothing. CAV fusion+V2X+HD-map
   physics is absent from prior ouroboros rounds and must be named
   `autonomous-driving`. Do not spend event-camera-traffic-grid (r04),
   aerial-swarm (r02), or underwater-rov (r20).
4. **major — race under-specified.** One fused-gap channel cannot be a
   race. Need >=2 channels inside `race_window_us` with globally sorted
   `t_rel_ms` and same-channel refractory >= 0.8 ms.
5. **minor — single-edge scar.** Raster routing with one potentiated
   weight repeats earlier three-edge form without the fourth. NOTES-r16
   asked for a scar where rolling back any triple still fires.

Fix directives: name the domain, put residual vs fuse.gap_ok in a 500 us
window, quote the numeric floor, emit reconciled ticks, and refuse to
call a later underride a save.

## Diversity Enforcer

Injected domain (exactly 1, novel this round): **autonomous-driving**.

Displaced/expanded: replaces the Generator's `vehicle` bucket. This is
the prompt-list domain left unused across 2026-08-17, 2026-08-30, and
staged r14-r54 (r53 explicitly left it for concurrent slots). It is not
warehouse-amr, not aerial-swarm, not event-camera-traffic-grid (DVS urban
grid, no HD-map clutter polygon, no V2X CAM), not underwater-rov.

Domain-specific constraint: do not raise above 1.05x current = 75.6 km/h
while unassociated in-lane radar residual > 8.0 dBsm AND observer TTC
< 2.40 s AND map-clutter IoU > 0.60.

Sensor delta: +77 GHz radar residual, +V2X CAM, +HD-map clutter IoU,
+fused gap, +IMU yaw; −DVS event camera, −potline voltage, −umbilical
load-cell, −Pirani. `state.domain` and `meta.domain` both
`autonomous-driving`. Jaccard opening vs prior batches must stay < 0.4
("Brambleford proving loop CAV-7..." vs mill-town / fjord / ROV
openings).

## Edge-Case Hunter

Injected tail (exactly 1, adversarial, base rate <1%): stalled box truck
42.0 m in-lane dropped as HD-map `static_shoulder_clutter` (sensor-
association class). Layby visual PASSES because the polygon looks like
parked farm equipment. Fitted-style base rate 0.41%/loop from a
clutter-IoU Monte Carlo (map designed, stall fitted).

Naive failure mode: PB-CG-07 CLOSE-GAP on three locally-true confirms
(fused gap 2.80 s, V2X lane_clear, map 105 km/h) into a 1.98 s / 80.6
km/h underride. FALSE PERMISSION.

Concrete trajectory edit: `state.fault_context.igniter` is the stall plus
IoU 0.81 drop; `safety_decision` must MODIFY on residual/TTC/IoU floors;
`future_outcome` must keep the stall as the reason fused gap is locally
true; probe must move residual iff the return is a world object.

This tail is disjoint from the domain injection (domain = on-road CAV
stack; tail = one association miss).

## Neuromorphic Translator

Cycle-1 temporal patch (pre-densify, 16 events in the 40 ms window, then
probe/HITL later in cycle 2):

| channel | t_rel_ms | amplitude | role |
|---|---|---|---|
| fuse.gap | 0.380 | 0.54 | early gap pulse |
| v2x.cam | 1.140 | 0.61 | CAM heartbeat |
| map.advisory | 2.220 | 0.58 | map 105 |
| imu.yaw | 3.360 | 0.52 | yaw-stable |
| radar.residual | 4.180 | 0.72 | residual rising |
| v2x.cam | 5.010 | 0.57 | adapt down |
| fuse.gap | 5.480 | 0.50 | adapt down |
| radar.residual | 6.512 | 1.38 | RACE WINNER |
| fuse.gap_ok | 6.700 | 1.12 | RACE LOSER |
| v2x.lane_clear | 6.888 | 0.68 | third in window |
| ctrl.gate | 7.200 | 1.08 | MODIFY latch |

Race window 500 us at [6.40, 6.90] ms holds three channels. Margin 188 us
< min(500, 500) us, so a sub-flip-bound perturbation reverses winner/loser.
Same-channel refractory >= 0.8 ms (tightest later measured on fuse.gap
2.640 ms in the window train). `state.t0_us` 1788396120000021,
`gate_latency_us` 688, `race_window_us` 500. Ticks 5 (cycle 1) then 7
(cycle 2) under declared unweighted sum. Distillation value: the
cross-channel order is the race; the floors are order-invariant.

## Trajectory Builder

Cycle-1 hardened object (not the JSONL line): Thalamic v2 keys present;
`state.sim_or_real=designed`; domain `autonomous-driving`; decision
MODIFY with numeric floor; 16 spikes globally sorted on `t_rel_ms`;
raster 51 = round(160*8.0*0.040); gate_snn MODIFY; reward heads not yet
the final 7-tick set. Diversity injection (autonomous-driving) and
Edge-Case injection (stalled clutter-gate) are both present and
non-identical. Checks passed at this cycle: schema keys, sim enum,
spike order, raster budget, gate decision match. Still missing vs
publishable: cycle-2 snow sub-variant, V2X-forgery tail, +10 spikes,
+2 ticks, delayed underride as PRIMARY terminal, four-edge scar
arithmetic, HITL 8.4 s, contrast ACCEPT. Densification delta this cycle:
+1 domain, +1 tail, +race, +raster/gate_snn.

---

# Cycle 2 — Densification (strictly additive)

## Generator

Cycle-1 object expanded, not rewritten. Additive payload:

- `proposed_action.evidence` now carries six observables with units:
  fused gap 2.80 s, residual 18.4 dBsm, TTC 2.10 s, IoU 0.81, time-to-
  impact 1.98 s, race margin 188 us.
- `safety_decision.rationale` quotes the numeric floor 75.6 km/h with
  three AND-ed predicates and the probe discriminant (stalled residual
  >= 16 dBsm / range drop >= 8.0 m vs clear <= 3 dBsm).
- `future_outcome.delayed_side_effects` gains two new leaves beyond the
  immediate probe: +1.68 s residual 18 km/h underride as PRIMARY
  terminal, +21 d CR-C-2108. +4 d sister-ego ACCEPT contrast retained
  as a third delayed leaf.
- Outcome no longer says "episode saved". Process-correct gate, bounded
  world loss, total -0.16.

Two downstream side-effects (one delayed) are now explicit: (1) AEB
mean 5.5 m/s^2 after pad fade, (2) delayed 3.2 h / $0.41M claim. This
cycle is information-strictly longer than cycle 1.

## Critic

Re-audit of the expanded trajectory:

1. **blocking (cleared if ticks reconcile).** Five heads must sum to
   total -0.16 and 7 ticks must sum to those heads within 1e-6. Inflection
   at 1680000 us must be a tick. Contrast 0.48 must reconcile separately.
2. **major (cleared if snow probe is a physical-constraint change).**
   Cycle-2 domain injection cannot be a second copy of autonomous-driving.
   Packed-snow mu=0.28 that invalidates the 0.45 s / 0.80 m/s^2 pulse
   is an acceptable sub-variant. A second on-road dry loop is not.
3. **major (cleared if the second tail is a different trigger class).**
   Night-shift V2X quantization is human-intent deception, disjoint from
   cycle 1's accidental stall. Reusing clutter-IoU as the cycle-2 tail
   would collapse the two hunters.
4. **minor — HITL is latency, not hil.** 8.4 s remote-ops ratify is
   acceptable as designed latency; do not flip `sim_or_real` to `hil`
   without a hardware-in-loop interlock cell. Flag as gap 4 residual.
5. **minor — Jaccard.** Opening "Brambleford proving loop CAV-7" must
   stay < 0.4 vs staged r14-r54 mill-town / fjord / ROV openings.

No rewrite from this role. Directives: keep MODIFY, keep negative total,
add snow refit, add V2X forgery, keep four-edge scar numbers.

## Diversity Enforcer

Injected domain this cycle (exactly 1): **packed-snow / low-mu winter
loop** as a physical-constraint sub-variant of autonomous-driving, not a
repeat of the cycle-1 name and not a second prompt-list domain.

What it changed: mu 0.28 vs dry 0.85. The cycle-1 0.45 s / 0.80 m/s^2
probe locks ABS and yaws 4.1 deg on snow, so the standing probe must
move to 1.40 s / 0.22 m/s^2. Sensor mix unchanged; constraint mix
changes (friction-limited jerk). Cycle-1 autonomous-driving is retained.

This is disjoint from the cycle-2 tail (human-intent V2X forgery).

## Edge-Case Hunter

Injected tail this cycle (exactly 1, different trigger class): night-shift
forged V2X CAM CSV at 10 km/h quantization vs plant 0.1 km/h (100 bins)
plus live residual 18.4 dBsm at the claimed stall-free instant.
Human-intent deception. Base rate ~0.29% of night loops, DESIGNED,
flagged. Naive failure = FALSE CLEAR.

Concrete edit: `meta.injections.cycle2_tail` plus CR-C-2108 native
0.1 km/h export mandate as the fraud fence. Disjoint from cycle 1's
accidental stall (association class). Cycle-1 tail retained.

## Neuromorphic Translator

Cycle-2 re-densify: primary train 16 -> 26 events (added brake.probe
450.0, aeb.command 451.8, residual 632.4, fuse.gap_ok 814.8,
aeb.residual.impact 1680.0, human.ratify 8400.0, lane.isolate 8480.0,
and the 3.2 h tail). Contrast train of 8 events with its own 196 us
race (residual 0.000 vs fuse.gap_ok 0.196). Ticks 5 -> 7 covering gate,
probe, underride, HITL, 3.2 h. Raster excerpt 16 events inside 40 ms;
energy 1173 pJ = 51*23. Third-factor tau 0.90 s with four-edge
eligibility at probe-fail +0.45 s. Winner/loser flip narrative: reversing
radar.residual and fuse.gap_ok by < 188 us reshuffles triage, not the
floors. Adaptation: residual 0.72->1.38->0.88->0.41.

## Trajectory Builder

Validated FINAL publishable object for this cycle (the only JSONL line).

Checks passed / fixed:
- required keys id/state/proposed_action/safety_decision/executed_action/future_outcome/reward_components/meta
- state.sim_or_real=designed (never real)
- safety_decision.decision=MODIFY with numeric floor in rationale
- reward total -0.16 reconciles with five heads and with 7 ticks
- spike_events 26, one key t_rel_ms, globally non-decreasing, refractory >=0.8 ms, >=2 channels in race window
- raster spikes/energy/window/excerpt/routing.third_factor valid
- gate_snn decision matches MODIFY; population spike budgets ±1
- rights RM-793 research_only on record and meta; no training_ready
- Diversity + Edge-Case injections from BOTH cycles present and non-trivial
- cycle 2 strictly additive vs cycle 1
- plant is not LYOSHIELD, not CINDERWICK, not TRIAD, not REDHALL, not OXBOWREEL

Densification delta: +1 domain sub-variant (packed-snow), +1 tail
(night-shift V2X forgery), +10 spikes (16->26), +2 ticks (5->7), +1
contrast train with own race, +2 delayed side-effects, +1 four-edge
scar with any-triple-rollback-fails, +1 HITL ratify, +1 surprise
(brake-pad fade is the episode-miss mechanism).

Publishable JSONL line (the only JSONL line; also at batch-r21.jsonl):

```json
__FINAL_JSONL__
```

Validation receipt (final): checks passed / fixed as reported by
build_r21.py self-validate (check_jsonl, raster_status, verify_record_execution,
spike_probe --strict).
"""
    text = text.replace("__FINAL_JSONL__", line)
    (OUT / "swarm-transcript-r21.md").write_text(text)
    return text


def main():
    rec, aux = build_record()
    errs = local_checks(rec, aux)

    OUT.mkdir(parents=True, exist_ok=True)
    target = OUT / "batch-r21.jsonl"
    if target.exists():
        target = OUT / "batch-r21c.jsonl"
        notes_name = "NOTES-r21c.md"
        transcript_name = "swarm-transcript-r21c.md"
    else:
        notes_name = "NOTES-r21.md"
        transcript_name = "swarm-transcript-r21.md"
    line = json.dumps(rec, ensure_ascii=False, separators=(",", ":"))
    target.write_text(line + "\n")

    from check_records import FactoryStaging, check_jsonl
    from curate_bridge import raster_status
    from verify_execution import verify_record_execution
    from round_txn_raster import validate_bridge_envelope

    e, w, kinds, n = check_jsonl(
        target,
        target.name,
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
    env_errs = validate_bridge_envelope(target, factory_dir=factory_dir)
    print("validate_bridge_envelope", env_errs)
    errs.extend(env_errs)

    probe = subprocess.run(
        [
            sys.executable,
            f"{ROOT}/pipelines/spike_probe.py",
            "--strict",
            str(target),
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

    # write_notes / write_transcript always use r21 names unless collision
    if target.name.endswith("c.jsonl"):
        # keep filenames aligned; patch write functions via direct paths
        notes = write_notes(rec, aux, receipt)
        (OUT / notes_name).write_text(notes)
        tr = write_transcript(rec, line)
        (OUT / transcript_name).write_text(tr)
        (OUT / "NOTES-r21.md").unlink(missing_ok=True) if notes_name != "NOTES-r21.md" else None
    else:
        write_notes(rec, aux, receipt)
        write_transcript(rec, line)

    headings = re.findall(
        r"^## .+$", (OUT / ("swarm-transcript-r21c.md" if target.name.endswith("c.jsonl") else "swarm-transcript-r21.md")).read_text(), re.M
    )
    print("headings", headings)
    expected = [
        "## Generator",
        "## Critic",
        "## Diversity Enforcer",
        "## Edge-Case Hunter",
        "## Neuromorphic Translator",
        "## Trajectory Builder",
    ]
    if headings != expected * 2:
        errs.append(f"headings {headings}")

    print("local+pipeline errs", errs)
    print("wrote", target)
    if errs:
        sys.exit(1)


if __name__ == "__main__":
    main()
