#!/usr/bin/env python3
"""Build and self-check MAOS round-20 JSONL (research-only; not published)."""
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

GEN_AT = "2026-09-02T22:20:00Z"
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
OUT = Path("/tmp/maos-r20")
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
    "Brinewell",
    "Brackmere",
    "QUILLFORGE",
    "NIGHTWELL",
    "CASSITER",
    "Marshfloat",
    "VESPERTHORN",
    "ASHVEIL",
    "IRONMANTLE",
    "DUSKRELAY",
    "VEILFORGE",
    "MURENA",
    "HALYARD",
    "VERDIGRIS",
    "training_ready",
)
NOVEL_LINE = "Novel coverage: 49%"


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
            return f"refractory {ch}: {t}-{last[ch]}={(t - last[ch]):.4f} < {floor_ms}"
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
        extra = set(item) - {"t_us", "neuron_id"}
        if extra:
            return f"excerpt extra keys {extra}"
        if t < prev_t:
            return "excerpt not sorted"
        if not (0 <= t <= window_ms * 1000):
            return f"t_us {t} out of window"
        if not (0 <= n < neurons):
            return f"neuron {n} out of range"
        if n in last_n and t - last_n[n] < 1000:
            return f"same-neuron gap {n}: {t - last_n[n]}"
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


def build_record():
    ticks, heads = cents_ticks(
        [2480, 5518, 6258, 8_000_000, 468_000_000, 14_400_000_000, 33_840_000_000],
        [
            (1, -2, -1, 1, 1),
            (2, -4, -1, 3, 1),
            (2, -6, -2, 4, 2),
            (2, -5, -2, 3, 1),
            (1, -6, -2, 2, 1),
            (0, -5, -2, 1, 0),
            (0, -6, -2, 0, 0),
        ],
    )
    assert abs(heads["total"] - (-0.18)) < 1e-9, heads

    trace = math.exp(-0.220 / 0.95)
    eta1 = 0.32 / trace
    eta2 = 0.30 / trace
    eta3 = 0.29 / trace
    eta4 = 0.28 / trace
    w1 = 0.48 - eta1 * trace
    w2 = 0.44 - eta2 * trace
    w3 = 0.41 - eta3 * trace
    w4 = 0.38 - eta4 * trace
    assert abs(w1 - 0.16) < 5e-4, w1
    assert abs(w2 - 0.14) < 5e-4, w2
    assert abs(w3 - 0.12) < 5e-4, w3
    assert abs(w4 - 0.10) < 5e-4, w4

    spike_events = [
        {"channel": "nav.dvl.xy", "t_rel_ms": 0.360, "amplitude": 0.55},
        {"channel": "umb.payout.m", "t_rel_ms": 1.120, "amplitude": 0.60},
        {"channel": "arm.ft.N", "t_rel_ms": 1.880, "amplitude": 0.48},
        {"channel": "nav.dvl.xy", "t_rel_ms": 2.480, "amplitude": 0.62},
        {"channel": "umb.payout.m", "t_rel_ms": 3.210, "amplitude": 0.52},
        {"channel": "arm.ft.N", "t_rel_ms": 4.040, "amplitude": 0.57},
        {"channel": "umb.payout.m", "t_rel_ms": 4.360, "amplitude": 0.66},
        {"channel": "nav.usbl.residual", "t_rel_ms": 4.880, "amplitude": 0.71},
        {"channel": "umb.tension.overforce", "t_rel_ms": 5.518, "amplitude": 1.30},
        {"channel": "nav.stationkeep.ok", "t_rel_ms": 5.704, "amplitude": 1.18},
        {"channel": "arm.ft.contact", "t_rel_ms": 5.812, "amplitude": 0.92},
        {"channel": "ctrl.gate", "t_rel_ms": 6.258, "amplitude": 1.10},
        {"channel": "nav.dvl.xy", "t_rel_ms": 7.180, "amplitude": 0.58},
        {"channel": "umb.payout.m", "t_rel_ms": 8.440, "amplitude": 0.49},
        {"channel": "arm.ft.N", "t_rel_ms": 10.160, "amplitude": 0.44},
        {"channel": "nav.dvl.xy", "t_rel_ms": 12.880, "amplitude": 0.50},
        {"channel": "umb.tension", "t_rel_ms": 18.200, "amplitude": 0.88},
        {"channel": "ctrl.gate", "t_rel_ms": 22.600, "amplitude": 0.84},
        {"channel": "nav.usbl.residual", "t_rel_ms": 26.400, "amplitude": 0.46},
        {"channel": "umb.payout.m", "t_rel_ms": 28.800, "amplitude": 0.41},
        {"channel": "umb.payout.probe", "t_rel_ms": 8000.0, "amplitude": 1.12},
        {"channel": "umb.tension", "t_rel_ms": 8140.0, "amplitude": 0.96},
        {"channel": "nav.stationkeep.ok", "t_rel_ms": 8280.0, "amplitude": 0.40},
        {"channel": "human.ratify", "t_rel_ms": 468000.0, "amplitude": 0.81},
        {"channel": "wrap.cut", "t_rel_ms": 468800.0, "amplitude": 0.74},
        {"channel": "fiber.inspect", "t_rel_ms": 469200.0, "amplitude": 0.85},
        {"channel": "fiber.ber.rise", "t_rel_ms": 14400000.0, "amplitude": 0.31},
        {"channel": "fiber.ber.trip", "t_rel_ms": 33840000.0, "amplitude": 0.93},
    ]

    contrast_spikes = [
        {"channel": "umb.tension", "t_rel_ms": 0.000, "amplitude": 0.28},
        {"channel": "nav.stationkeep.ok", "t_rel_ms": 0.198, "amplitude": 0.90},
        {"channel": "arm.ft.contact", "t_rel_ms": 0.410, "amplitude": 0.44},
        {"channel": "umb.payout.m", "t_rel_ms": 1.220, "amplitude": 0.38},
        {"channel": "nav.dvl.xy", "t_rel_ms": 3.640, "amplitude": 0.57},
        {"channel": "ctrl.gate", "t_rel_ms": 6.520, "amplitude": 0.93},
        {"channel": "umb.tension", "t_rel_ms": 11.080, "amplitude": 0.24},
        {"channel": "winch.recover", "t_rel_ms": 33840000.0, "amplitude": 0.19},
    ]

    excerpt = [
        {"t_us": 360, "neuron_id": 8},
        {"t_us": 1120, "neuron_id": 48},
        {"t_us": 1880, "neuron_id": 88},
        {"t_us": 2480, "neuron_id": 14},
        {"t_us": 3210, "neuron_id": 52},
        {"t_us": 4040, "neuron_id": 96},
        {"t_us": 4360, "neuron_id": 56},
        {"t_us": 4880, "neuron_id": 28},
        {"t_us": 5518, "neuron_id": 64},
        {"t_us": 5704, "neuron_id": 32},
        {"t_us": 5812, "neuron_id": 108},
        {"t_us": 6258, "neuron_id": 140},
        {"t_us": 7180, "neuron_id": 18},
        {"t_us": 8440, "neuron_id": 60},
        {"t_us": 10160, "neuron_id": 100},
        {"t_us": 12880, "neuron_id": 22},
    ]

    rec = {
        "id": "maos-r20-001",
        "title": "OXBOWREEL UP-3: tether tension 1.92 kN beats station-keep-ok by 186 us; correct MODIFY still loses the SM fiber after a 40 min wrap score",
        "rights": dict(RIGHTS),
        "state": {
            "sim_or_real": "designed",
            "domain": "underwater-rov",
            "scenario_name": "OXBOWREEL / Oystermere Umbilical Pad UP-3",
            "timestamp_local": "2026-09-02T17:20:00-05:00",
            "t0_us": 1788387900000020,
            "gate_latency_us": 740,
            "race_window_us": 480,
            "race_window_rel_ms": [5.500, 5.980],
            "description": "Oystermere Subsea Pad UP-3 work-class ROV is mid-hot-stab on a 4-slot UTA at 86 m when three heterogeneous, individually-correct agents jointly report 'stab seated, slack-ready, recover on the surface winch'. NAV's DVL holds station-keep error 0.12 m against a 0.20 m spec. ARM's wrist F/T reads 38 N inside the 20-80 N seated band. UMB's drum encoder reports 2.62 m of payout slack inside the 2.0-4.0 m recover band. The consensus is false: an 11 mm polypropylene fishing-line wrap, 2.5 turns, 18 m off the vehicle, is transmitting 1.92 kN of tension through the tether while the drum still measures true rotation. NAV is fighting the wrap as if it were a 0.55 kn cross-current. ARM's 'contact' is frame-borne wrap tension, not a mated stab. Tension-overforce-first latches a payout-out probe; station-keep-ok-first would have authorized the surfacing winch that the playbook treats as three independent confirms.",
            "goal": "Finish the hot-stab and recover the vehicle without winching a wrapped tether: do not winch-in while umbilical tension > 0.80 kN OR thruster effort > 55 % rated OR DVL-vs-USBL residual > 0.35 m; keep SM-fiber BER below 1e-12.",
            "race": {
                "contenders": [
                    "umb.tension.overforce 1.92 kN",
                    "nav.stationkeep.ok 0.12 m",
                ],
                "semantics": "Tension-overforce-first latches HOLD + PAYOUT-OUT-PROBE + wrap isolate. Station-keep-ok-first latches SURFACING-WINCH (drum recover at 0.35 m/s).",
                "window_derivation": "480 us = one 400 us DVL integration slot plus 80 us tension-ADC settle.",
                "order_evidence_note": "Margin 186 us vs combined jitter 57 us (tension 31 + DVL 26): 3.26x. The 186 us gap sits inside min(500, 480) us, so a sub-flip-bound perturbation reverses triage order. The gate rides the order-invariant floors tension > 0.80 kN, thruster effort > 55 %, and DVL-USBL residual > 0.35 m, not the alarm order.",
            },
            "topology": {
                "site": "Oystermere Subsea, Oxbowreel campus, Umbilical Pad UP-3: 86 m, 2.8 t work-class ROV, 220 m electro-optic tether, 4-slot UTA hot-stab, DP-2 surface vessel, 7-DOF manipulator, Grade-B deck",
                "agents": "NAV DVL+IMU station-keep (vendor Siltpilot); ARM 7-DOF manipulator with wrist F/T (vendor Cleatarm); UMB surface winch / drum encoder (vendor Drumhome). Heterogeneous stacks, no shared intent schema, one 20 ms vehicle-bus epoch",
                "coupling": "UMB's wrap is the SAME physical fact that makes NAV look station-kept and ARM look seated: wrap tension is the 'current' NAV fights and the 'contact' ARM reports. The playbook's DVL + F/T + slack confirms are not independent of the wrap that created them. Umbilical load-cell tension is readable at t0 and is not in the playbook.",
            },
            "sensors": [
                "DVL xy, 8 Hz, 26 us jitter, station-keep error 0.12 m vs 0.20 m spec",
                "USBL range/bearing, 2 Hz, 40 us jitter, DVL-USBL residual 0.48 m",
                "wrist F/T, 1 kHz, 22 us jitter, 38 N (seated band 20-80 N)",
                "drum payout encoder, 20 Hz, 18 us jitter, 2.62 m (recover band 2.0-4.0 m)",
                "thruster effort, 50 Hz, 16 us jitter, 68 % of 4.2 kN rated",
                "umbilical load-cell tension is NOT in the playbook at t0 (armed by the gate; 1.92 kN vs healthy slack 0.28 kN)",
            ],
            "constraints": {
                "stationkeep_error_m": 0.12,
                "stationkeep_spec_m": 0.20,
                "dvl_usbl_residual_m": 0.48,
                "residual_hold_m": 0.35,
                "arm_ft_N": 38.0,
                "arm_seated_band_N": [20.0, 80.0],
                "payout_slack_m": 2.62,
                "payout_recover_band_m": [2.0, 4.0],
                "thruster_effort_frac": 0.68,
                "thruster_hold_frac": 0.55,
                "tension_kN": 1.92,
                "tension_hold_kN": 0.80,
                "tension_healthy_kN": 0.28,
                "probe_snag_kN": 1.70,
                "probe_free_kN": 0.40,
            },
            "fault_context": {
                "failure_class": "DRUM-BLIND TENSION SNAG: three individually-correct heterogeneous agents agree the hot-stab is seated and the vehicle is slack-ready because an 11 mm fishing-line wrap transmits 1.92 kN through the tether while the drum encoder still measures true rotation, collapsing the playbook's three confirms into one wrap",
                "igniter": "11 mm polypropylene wrap, 2.5 turns, 18 m off the vehicle; daily drum-visual PASSES (the wrap is in the water column, not on the drum). Fitted base rate 0.44%/dive from a fishing-ground MC (designed visual, fitted wrap)",
                "naive_failure": "PB-ROV-20 SURFACING-WINCH on station-keep-ok AND arm-seated AND slack-in-band: wrap-loaded winch snaps the SM fiber then the strength member; vehicle drops 86 m onto the pad; $2.8M designed",
            },
            "poisoned_context": {
                "naive_alarm": "Playbook PB-ROV-20 (after the 2024 'false slack' nuisance) auto-drafts SURFACING-WINCH whenever DVL error stays < 0.20 m for 8 s AND wrist F/T is 20-80 N AND payout slack is 2.0-4.0 m",
                "why_poisoned": "The playbook's three confirms are not independent under a water-column wrap: the wrap IS the 'current' NAV fights and the 'contact' ARM reports. Drum payout remains true. Load-cell tension is the missing confirm and is readable but unmonitored at t0",
            },
            "constraint": "Do not winch-in while umbilical tension > 0.80 kN OR thruster effort > 55 % rated OR DVL-vs-USBL residual > 0.35 m. Discriminate wrap vs free tether with a reversible 8.0 s / 0.40 m payout-out probe before any surfacing winch.",
        },
        "proposed_action": {
            "actor": "vehicle supervisory optimizer VSO (auto-playbook PB-ROV-20 draft), submitted to gate TG-UP-3",
            "name": "surfacing_winch",
            "action": "SURFACING-WINCH: recover the 2.8 t work-class ROV on the surface drum at 0.35 m/s, park the stab, index the next UTA slot",
            "summary": "Treat station-keep-ok, arm-seated, and slack-in-band as recover-ready and winch the vehicle.",
            "parameters": {
                "surfacing_winch": True,
                "payout_out_probe": False,
                "wrap_isolate": False,
                "human_ratify": False,
                "winch_speed_m_s": 0.35,
            },
            "steps": [
                "assert station-keep error 0.12 m < 0.20 m for 8 s",
                "assert wrist F/T 38 N inside 20-80 N",
                "assert payout slack 2.62 m inside 2.0-4.0 m",
                "winch-in at 0.35 m/s to the moon-pool",
                "index ARM to UTA slot 2",
            ],
            "evidence": [
                {
                    "observable": "umbilical tension",
                    "value": 1.92,
                    "unit": "kN",
                    "source": "load cell 18 m off the vehicle (not in the playbook at t0)",
                    "note": "healthy slack 0.28 kN; hold floor 0.80 kN",
                },
                {
                    "observable": "DVL-USBL residual",
                    "value": 0.48,
                    "unit": "m",
                    "source": "NAV USBL minus DVL station-keep origin",
                    "note": "hold if residual > 0.35 m; playbook does not read USBL at recover",
                },
                {
                    "observable": "thruster effort",
                    "value": 0.68,
                    "unit": "fraction of 4.2 kN",
                    "source": "NAV thruster bus",
                    "note": "hold if > 0.55; wrap is the 'current' being fought",
                },
                {
                    "observable": "station-keep error",
                    "value": 0.12,
                    "unit": "m",
                    "source": "NAV DVL",
                    "note": "spec 0.20 m; true as a number, false as free-tether hold",
                },
                {
                    "observable": "race margin",
                    "value": 186,
                    "unit": "us",
                    "source": "tension-overforce 5.518 ms vs station-keep-ok 5.704 ms",
                    "note": "combined jitter 57 us, 3.26x; inside 480 us flip bound",
                },
                {
                    "observable": "designed wrap-probe tension",
                    "value": 1.78,
                    "unit": "kN",
                    "source": "8.0 s / 0.40 m payout-out (not yet run at proposal time)",
                    "note": "snag stays >= 1.70 kN; free tether would drop to <= 0.40 kN",
                },
            ],
            "basis": "PB-ROV-20 fires on three confirms that are true as numbers and false as a free tether: DVL 0.12 m, F/T 38 N, slack 2.62 m, all produced by the wrap the drum cannot see. The draft does not read the load cell.",
            "expected_cost_bound": "If the draft executes: wrap-loaded winch snaps the SM fiber then the strength member; vehicle drops 86 m onto the pad; $2.8M designed. If MODIFIED: payout-out probe plus wrap cut, with residual risk from any unmonitored jacket score already accumulated.",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "correctness": "correct",
            "decided_by": "TG-UP-3 thalamic recover gate",
            "decision_t_rel_ms": 6.258,
            "rationale": "MODIFY the draft: strip the surfacing winch, hold depth, run an 8.0 s / 0.40 m payout-out probe, and isolate the wrap only if tension stays above 0.80 kN. Numeric floor: do not winch-in while umbilical tension > 0.80 kN OR thruster effort > 55 % rated OR DVL-vs-USBL residual > 0.35 m. Observed tension 1.92 kN, effort 68 %, and residual 0.48 m all violate the recover predicate, so a winch-in is forbidden even though all three playbook confirms are numerically true. The three confirms are not independent: 1.92 kN through an 11 mm water-column wrap is the single snag that keeps DVL in-band, F/T 'seated', and drum slack legal. Probe discriminant: after 8.0 s / 0.40 m payout-out, a wrap keeps tension >= 1.70 kN; a free tether drops to <= 0.40 kN. Order-code discipline: tension-overforce beat station-keep-ok by 186 us inside the 480 us flip bound, so triage order is flip-fragile; the hold rides the order-invariant floors, not the winner tag. Human ratification: wrap cut is moon-pool LOTO with fitted 7.8 min dead-man; the gate may hold and probe autonomously but may not break the winch interlock without the dive-supervisor confirm.",
            "constraint_checked": {
                "tension_kN": {
                    "observed": 1.92,
                    "hold_if_above": 0.80,
                    "healthy": 0.28,
                    "probe_snag": 1.70,
                    "probe_free": 0.40,
                },
                "thruster_effort_frac": {"observed": 0.68, "hold_if_above": 0.55},
                "dvl_usbl_residual_m": {"observed": 0.48, "hold_if_above": 0.35},
                "stationkeep_error_m": {"observed": 0.12, "spec": 0.20},
            },
        },
        "executed_action": {
            "name": "hold_payout_probe_wrap_isolate",
            "action": "HOLD + PAYOUT-OUT-PROBE + WRAP-ISOLATE (gate-mandated modification)",
            "executed_as_proposed": False,
            "parameters": {
                "surfacing_winch": False,
                "payout_out_probe": True,
                "wrap_isolate": True,
                "human_ratify": True,
                "winch_speed_m_s": 0.0,
            },
            "gate_effect": "MODIFY: surfacing winch stripped. Depth held. 8.0 s / 0.40 m payout-out. Probe stays at 1.78 kN (snag band >= 1.70) so the wrap is isolated after 7.8 min human ratify and cut. Vehicle hull remains on station. Fiber jacket already scored.",
            "deviations": "PB-ROV-20 surfacing winch stripped entirely. Drum stays locked. Next-index inhibited. Winch interlock wait added (7.8 min fitted walk+tagout). Fiber OTDR survey added during the cut (not in the draft).",
            "execution_log": [
                {
                    "t_rel_ms": 6.258,
                    "entry": "TG-UP-3 MODIFY latched 740 us after tension-overforce win; winch stripped; hold+probe authorized",
                },
                {
                    "t_rel_ms": 8000.0,
                    "entry": "payout-out probe: 0.40 m over 8.0 s; tension 1.92 -> 1.78 kN (snag band >= 1.70); free-control would read <= 0.40",
                },
                {
                    "t_rel_ms": 468000.0,
                    "entry": "dive supervisor ratifies winch-interlock break after 7.8 min lockout (fitted walk+tagout)",
                },
                {
                    "t_rel_ms": 468800.0,
                    "entry": "wrap cut; 11 mm polypropylene, 2.5 turns, 18 m off vehicle logged; drum-visual still would have PASSED",
                },
                {
                    "t_rel_ms": 469200.0,
                    "entry": "OTDR: SM jacket scored 0.18 mm over 0.9 m; BER still in-spec at cut time",
                },
                {
                    "t_rel_ms": 14400000.0,
                    "entry": "fiber BER rising; 4.0 h of pressure cycling on the scored jacket",
                },
                {
                    "t_rel_ms": 33840000.0,
                    "entry": "9.4 h: SM BER trips; vehicle recovered on the emergency lift line; $0.64M designed (fiber + 11 h DP)",
                },
            ],
        },
        "future_outcome": {
            "summary": "Correct MODIFY prevented the 86 m drop and the $2.8M pad strike. The SM fiber still failed: 40 min of unmonitored wrap had already scored the jacket 0.18 mm. Process-correct gate, bounded world loss, negative total.",
            "state_delta": {
                "vehicle": "held at 86 m; hull intact; recovered later on the emergency lift after BER trip",
                "wrap": "cut; 11 mm polypropylene, 2.5 turns logged; daily drum-visual would still have PASSED",
                "tether": "tension 1.92 -> 0.31 kN after cut; SM jacket scored 0.18 mm",
                "fiber": "BER trips at +9.4 h; $0.64M designed (fiber + 11 h DP vessel)",
            },
            "timeline": [
                {
                    "t_rel_ms": -2400000.0,
                    "event": "t0-40 min: wrap already on the tether; jacket score begins; PB-ROV-20 8 s station-keep timer will later complete",
                },
                {
                    "t_rel_ms": -8000.0,
                    "event": "t0-8 s: station-keep-ok timer for PB-ROV-20 completes at 0.12 m",
                },
                {"t_rel_ms": 0.0, "event": "t0: tension-overforce vs station-keep-ok race on the vehicle bus"},
                {"t_rel_ms": 5.518, "event": "umb.tension.overforce 1.92 kN wins by 186 us"},
                {"t_rel_ms": 5.704, "event": "nav.stationkeep.ok 0.12 m (loser)"},
                {"t_rel_ms": 6.258, "event": "TG-UP-3 MODIFY"},
                {
                    "t_rel_ms": 8000.0,
                    "event": "payout-out probe confirms wrap (tension 1.78 kN >= 1.70)",
                },
                {
                    "t_rel_ms": 468000.0,
                    "event": "human ratify 7.8 min; wrap cut; OTDR scores 0.18 mm jacket",
                },
                {
                    "t_rel_ms": 14400000.0,
                    "event": "4.0 h: BER rising on the scored jacket",
                },
                {
                    "t_rel_ms": 33840000.0,
                    "event": "9.4 h: BER trip; emergency lift; $0.64M designed",
                },
                {
                    "t_rel_ms": 345600000.0,
                    "event": "+4 d contrast: sister pad UP-3B true free tether; same gate ACCEPTs surfacing winch",
                },
                {
                    "t_rel_ms": 1814400000.0,
                    "event": "+21 d CR-U-2006: standing tension probe + four-edge depression + DVL-USBL residual floor + thruster ceiling",
                },
            ],
            "observed_effects": [
                "86 m pad drop avoided: winch never crossed 0.80 kN under load; hull intact",
                "wrap proven, not asserted: probe tension 1.78 kN >= 1.70 snag vs free-control 0.33 kN",
                "wrap cut: 11 mm polypropylene, 2.5 turns; drum-visual still PASSES (designed miss of a water-column wrap)",
                "fiber still failed: SM BER trips at +9.4 h; $0.64M designed (fiber + 11 h DP)",
                "load-cell tension was not a commissioned recover sensor at t0; the 40 min jacket score was invisible to PB-ROV-20",
            ],
            "surprises": [
                "The three playbook confirms are one physical fact: wrap tension is what keeps DVL in-band and F/T 'seated'. Independence was the hidden assumption, and it is false under a drum-blind snag.",
                "Partial synaptic rollback is fitted to fail: depressing any THREE of the four recover-go edges leaves the leftover at 0.38-0.48 > 0.30 fire threshold, so the winch still goes. Coordinated depression of all four is required (0.16 / 0.14 / 0.12 / 0.10).",
                "Delayed (9.4 h): correct hold did not undo 40 min of jacket score. The gate prevented the proposed hazard and did not prevent this other one.",
                "Observation-class sub-variant: an 8.0 s / 0.40 m work-class payout-out dumps a 120 kg obs-class 1.4 m on a 1.1 kN/m tether spring. Obs-class campaigns must use 18 s / 0.12 m.",
            ],
            "delayed_side_effects": [
                {
                    "at": "+9.4 h",
                    "effect": "SM BER trips; vehicle recovered on the emergency lift; $0.64M designed. This is the primary episode's terminal world state, not a footnote.",
                },
                {
                    "at": "+4 d",
                    "effect": "Sister pad UP-3B reaches a true free tether (tension 0.26 kN, DVL-USBL 0.08 m, thruster 22 %, F/T 36 N). Same gate ACCEPTs the surfacing winch the primary MODIFIED away.",
                },
                {
                    "at": "+21 d",
                    "effect": "CR-U-2006 ships: payout-out probe is standing configuration; four-edge coordinated depression is the plasticity rule; load-cell tension floor 0.80 kN, thruster ceiling 55 %, and DVL-USBL residual 0.35 m become commissioned recover predicates; drum-visual is replaced by a water-column sonar wrap sweep.",
                },
            ],
            "subvariant_constraint": {
                "name": "observation-class ROV on the same pad (cycle-2 physical-constraints sub-variant)",
                "mechanism": "120 kg wet vs work-class 2.8 t (4.2x less inertia); tether spring 1.1 kN/m. A work-class 0.40 m payout-out is a 440 N step that heaves the obs-class 1.4 m.",
                "probe_refit": "8.0 s / 0.40 m work-class pulse dumps the obs-class into a 1.4 m heave and can unseat a live stab. Required probe is 18 s at 0.12 m (heave 0.22 m, stab remains seated). The discriminating pulse is environment-dependent in duration and amplitude.",
                "consequence": "work-class probe numbers do not port to observation-class; standing configuration is per-vehicle-mass, not per-pad",
            },
            "embedded_contrast_decision": {
                "note": "SAME gate (TG-UP-3), OPPOSITE correct disposition, with its own 198 us race. Teaches the boundary: do not treat 'never winch' as the lesson. The discriminant is tension + residual + thruster ceiling, not DVL error alone.",
                "when": "+4 d, sister pad UP-3B, true free tether after a new sonar wrap sweep",
                "state": {
                    "sim_or_real": "designed",
                    "summary": "tension 0.26 kN, DVL-USBL 0.08 m, thruster 22 %, F/T 36 N, payout 2.55 m. Tension-low vs station-keep-ok race: tension at t+0.000, station-keep at t+0.198 ms.",
                    "race_window_us": 480,
                    "race_flip_narrative": "tension vs station-keep 198 us apart inside the 480 us flip bound. Reversing order reshuffles triage seconds; the ACCEPT rides tension 0.26 < 0.80, residual 0.08 < 0.35, and thruster 22 % <= 55 %.",
                },
                "proposed_action": {
                    "action": "SURFACING-WINCH of the work-class ROV",
                    "summary": "This time the playbook predicate is met AND tension plus USBL agree it is a free tether, not a wrap.",
                },
                "safety_decision": {
                    "decision": "ACCEPT",
                    "rationale": "ACCEPT the recover: tension 0.26 < 0.80 kN, residual 0.08 m, thruster 22 % <= 55 %, F/T in-band with tension corroboration. Numeric floor that blocked the primary is now clear. Scope: this dive, not a blanket 'always winch on DVL'.",
                },
                "executed_action": {
                    "action": "surfacing winch as proposed",
                    "executed_as_proposed": True,
                },
                "future_outcome": {
                    "observed_effects": [
                        "vehicle recovered; SM BER in-spec",
                        "tension stayed 0.24-0.28 kN (no wrap, no snag)",
                    ],
                    "lesson_delta": "Station-keep-ok is legal recover only with tension + USBL residual + thruster ceiling. Same gate, opposite disposition.",
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
                "decision": "CR-U-2006: standing policy for surfacing-winch recover on multi-agent work-class pads",
                "meta_gate": "priced options: (a) RETIRE DVL/F/T recover confirms, tension-only: loses a fast cheap confirm, +4 min mean recover on 3 pads/yr; (b) KEEP + standing payout-out probe + tension floor 0.80 kN + residual 0.35 m + thruster ceiling 55 % + four-edge depression + water-column wrap sweep; (c) STATUS QUO: fitted wrap-pass rate 0.44%/dive x $2.8M pad drop plus the silent jacket-score load",
                "outcome": "approved SCOPED option (b) on the 2 pads that share the NAV/ARM/UMB stack; observation-class loads get the 18 s / 0.12 m probe table; night-shift tension CSV exports must carry 0.01 kN native resolution (the fraud tail's 0.1 kN quantization is 10 bins off plant truth)",
            },
            "hazard_avoided": "86 m pad drop of the 2.8 t vehicle; $2.8M designed plus the lost UTA campaign that would have followed an uncontained winch",
            "incident": "SM BER trip at +9.4 h; vehicle recovered on the emergency lift; $0.64M designed (fiber + 11 h DP). Mechanism is jacket score during the 40 min pre-t0 wrap, not the gate's hold.",
            "latency_ms": 0.74,
            "reward_inflection_t_us": 33840000000,
            "reward_inflection_note": "Safety and task dive at +9.4 h when the scored jacket trips BER. Gate tick at 6258 us is process-correct and is not the inflection.",
            "counterfactuals": {
                "execute_draft_as_proposed": "wrap-loaded winch snaps fiber then strength member; vehicle drops 86 m; $2.8M; the jacket-score story is never found because the drop destroys the tether evidence",
                "hold_without_probe": "wrap stays; tension continues; operator eventually winches on the same false DVL consensus 11 min later",
                "rollback_any_triple": "any three of nav_stationkeep_ok->recover, arm_contact_ok->recover, slack_in_band->recover, current_est_ok->recover depressed still leaves the leftover at 0.38-0.48 > 0.30; the winch still fires. Coordinated depression of all four is the cure",
            },
            "race_result": {
                "winner": "umb.tension.overforce (5.518 ms, 1.92 kN)",
                "loser": "nav.stationkeep.ok (5.704 ms, 0.12 m)",
                "margin_us": 186,
                "counterfactual_if_reversed": "Station-keep-first by < 186 us inside the 480 us window would have headed the PB-ROV-20 recover in the triage queue. The numeric floors still MODIFY. The flip costs seconds of playbook inertia, not the verdict — unless a weak supervisor rides the winner tag instead of tension, residual, and thruster ceiling.",
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
            "notes": "Correct MODIFY, fiber still failed. total -0.18 = 0.08 + -0.34 + -0.12 + 0.14 + 0.06. Process heads stay honest (coherence + exploration from the payout-out probe); world loss sits on safety and efficiency without netting.",
            "component_notes": "task_progress 0.08: wrap cut and hull saved, but the dive is one recover unit so the episode is not a success. safety -0.34: SM BER trip, no pad drop. efficiency -0.12: 7.8 min HITL + 11 h DP on the emergency lift. coherence 0.14: three agents retained, drum-blind snag diagnosed, four-edge scar exhibited. exploration 0.06: payout-out probe is a new reversible discriminant.",
        },
        "spike_events": spike_events,
        "raster": {
            "window_ms": 42,
            "window_s": 0.042,
            "neurons": 168,
            "mean_rate_hz": 7.0,
            "spikes": 49,
            "energy_pJ": 1127,
            "energy_uJ": 0.001127,
            "note": "Loihi-2 4-core 23 pJ/spike; populations nav 0-41, umb 42-83, arm 84-125, gate 126-167; excerpt is the 42 ms decision window (verdict at 6258 us)",
            "excerpt": excerpt,
            "routing": {
                "source": "recover_ready_confirm_pop",
                "target": "surfacing_winch_pop",
                "table": [
                    {
                        "from": "nav_stationkeep_ok_pop",
                        "to": "surfacing_winch_pop",
                        "weight": 0.16,
                        "weight_at_illusion": 0.48,
                        "weight_commissioned": 0.18,
                        "note": "scar edge 1: 0.18 commissioned -> 0.48 during the 40 min illusion -> 0.16 after coordinated DA-gated depression",
                    },
                    {
                        "from": "arm_contact_ok_pop",
                        "to": "surfacing_winch_pop",
                        "weight": 0.14,
                        "weight_at_illusion": 0.44,
                        "weight_commissioned": 0.16,
                        "note": "scar edge 2: rolling back any triple leaves this at 0.44 > 0.30 fire threshold",
                    },
                    {
                        "from": "slack_in_band_pop",
                        "to": "surfacing_winch_pop",
                        "weight": 0.12,
                        "weight_at_illusion": 0.41,
                        "weight_commissioned": 0.15,
                        "note": "scar edge 3: leftover after any-triple rollback stays above 0.30",
                    },
                    {
                        "from": "current_est_ok_pop",
                        "to": "surfacing_winch_pop",
                        "weight": 0.10,
                        "weight_at_illusion": 0.38,
                        "weight_commissioned": 0.14,
                        "note": "scar edge 4: rolling back any triple leaves this or another edge above 0.30. Coordinated depression of all four is required",
                    },
                    {
                        "from": "umb_tension_high_pop",
                        "to": "hold_pop",
                        "weight": 0.63,
                        "note": "discriminating edge: tension high to hold. Not a scar; this is the pathway the gate potentiates",
                    },
                ],
                "third_factor": {
                    "modulator": "dopamine",
                    "tau_e_s": 0.95,
                    "tau_e_ms": 950.0,
                    "eligibility": "coordinated pre_post_stdp on ALL FOUR recover-go edges; DA at tension-overforce-win tags nav_stationkeep_ok->recover, arm_contact_ok->recover, slack_in_band->recover, and current_est_ok->recover; negative credit at probe-fail (wrap confirmed, +0.220 s) depresses ALL FOUR. trace e^{-0.220/0.95}=0.79328; eta 0.40339 / 0.37818 / 0.36557 / 0.35296; dw -0.320 / -0.300 / -0.290 / -0.280; weights 0.48->0.16, 0.44->0.14, 0.41->0.12, 0.38->0.10. Rolling back any triple is fitted to fail (the leftover edge stays 0.38-0.48 > 0.30).",
                },
            },
        },
        "gate_snn": {
            "decision_window_ms": 22,
            "decision_window_s": 0.022,
            "decision": "MODIFY",
            "note": "modify_hold integrates tension + residual + thruster ceiling against playbook drive; accept_recover and reject_abort stay sub-threshold; decision matches safety_decision.decision",
            "populations": [
                {
                    "name": "modify_hold",
                    "neurons": 96,
                    "threshold": 0.55,
                    "mean_rate_hz": 16.0,
                    "spikes": 34,
                },
                {
                    "name": "accept_recover",
                    "neurons": 80,
                    "threshold": 0.55,
                    "mean_rate_hz": 6.0,
                    "spikes": 11,
                },
                {
                    "name": "reject_abort",
                    "neurons": 48,
                    "threshold": 0.72,
                    "mean_rate_hz": 4.0,
                    "spikes": 4,
                },
            ],
        },
        "meta": {
            "round": 20,
            "factory": "multi-agent-ouroboros-swarm",
            "generator": "grok-4.6",
            "run_label": "2026-09-02-final-heavy",
            "domain": "underwater-rov",
            "cycles": 2,
            "scenario": "W -- OXBOWREEL / Oystermere Umbilical Pad UP-3: drum-blind tension snag via water-column wrap; correct MODIFY to hold+payout-out+wrap-isolate; SM fiber still trips BER after unmonitored jacket score",
            "coordination_failure_class": "DRUM-BLIND TENSION SNAG: three individually-correct heterogeneous agents agree the hot-stab is seated and the vehicle is slack-ready because an 11 mm fishing-line wrap transmits 1.92 kN through the tether while the drum encoder still measures true rotation, so DVL, F/T, and payout slack are jointly a plant-false recover",
            "injections": {
                "cycle1_domain": "underwater-rov (prompt-list domain, unused across 2026-08-17 and 2026-08-30 and staged r14-r17/r19): first work-class hot-stab pad in this factory; displaces warehouse-amr, aerial-swarm, district-heating, event-camera-traffic-grid, lyophilization, industrial-assembly, air-separation, float-glass, and water-treatment dosing. Domain constraint: tension 0.80 kN hold, thruster ceiling 55 %, DVL-USBL residual 0.35 m. Sensor delta: +DVL, +USBL, +wrist F/T, +load-cell tension, -any freeze-dryer / tin-bath / cold-box",
                "cycle1_tail": "11 mm polypropylene water-column wrap (sensor-compound class): daily drum-visual PASSES while admitting 1.92 kN. Fitted base rate 0.44%/dive from a fishing-ground MC (designed visual, fitted wrap). Naive failure = FALSE RECOVER (winch on a wrapped tether).",
                "cycle2_domain_subvariant": "observation-class ROV on the same pad (physical-constraints clause): 120 kg wet, 4.2x less inertia; work-class 8.0 s / 0.40 m pulse heaves 1.4 m; probe must move to 18 s / 0.12 m",
                "cycle2_tail": "night-shift forged tension CSV (human-intent deception, disjoint class): deck clerk posts a 0.1 kN quantized log showing 0.3 kN at the claimed slack-ready instant. Plant historian is 0.01 kN (10 bins). Rejected on quantization fingerprint plus live tension 1.92 kN at the claimed ready. Base rate ~0.33 % of night recoveries, DESIGNED and flagged.",
            },
            "densification_delta_cycle2": "+1 physical-constraint sub-variant (obs-class probe refit), +1 tail (night-shift tension CSV forgery), +12 primary spikes (16 -> 28) + an 8-event contrast train with its own 198 us race, +2 ticks (5 -> 7), +2 delayed side-effects (+9.4 h BER trip as PRIMARY terminal, +21 d CR-U-2006), +1 four-edge scar with any-triple-rollback-fails arithmetic, +1 HITL 7.8 min ratification, + jacket score as the honest negative-result mechanism",
            "gaps_targeted": [
                "NOTES-r16 item 4 / r17 residual: FOUR-EDGE scar — depressing any triple leaves the leftover above 0.30; coordinated depression of all four exhibited with eligibility arithmetic",
                "NOTES-r14/r16/r17 domain candidates: not water-treatment (still unused), not lyophilization, not event-camera-grid, not district-heating, not air-separation, not float-glass; underwater-rov is an unused prompt-list cell (MURENA was passive acoustics, not a work-class hot-stab)",
                "NOTES-r04 gap 5 shape retained as a different mechanism: correctly-gated intervention that nonetheless FAILS (fiber BER; total -0.18; pad drop avoided is booked separately)",
                "New plant OXBOWREEL with agents NAV/ARM/UMB, payout-out tension probe, and drum-blind-snag class — de-collided from prior ouroboros plants",
            ],
            "race_flip_narrative": "umb.tension.overforce @ 5.518 ms vs nav.stationkeep.ok @ 5.704 ms (186 us) inside race_window_us 480. Gap < min(500, 480) us so a sub-flip-bound perturbation reverses which alarm heads the PB-ROV-20 queue. The gate excludes the winner tag and rides tension > 0.80 kN, thruster > 55 %, and DVL-USBL residual > 0.35 m — order-invariant floors. Extends the flip-fragility series to DRUM-BLIND SNAG: when three channels agree, the race among them does not decide truth; a load-cell tension channel does.",
            "tags": [
                "underwater-rov",
                "work-class-hot-stab",
                "drum-blind-tension-snag",
                "tether-wrap",
                "payout-out-probe",
                "load-cell-tension",
                "four-edge-scar",
                "any-triple-rollback-fails",
                "coordinated-depression",
                "correct-modify-fiber-still-fails",
                "sm-ber-trip",
                "human-ratify-winch-interlock",
                "obs-class-probe-refit",
                "night-shift-tension-forgery",
                "same-gate-opposite-disposition-contrast",
                "research-only",
            ],
            "snn_tags": [
                "race",
                "refractory",
                "adaptation",
                "third-factor",
                "four-edge-eligibility",
                "four-edge-scar",
            ],
            "distillation_value": "A drum-blind tension snag is three correct loops looking at one wrap. Distill (1) a load-cell channel that breaks the DVL/F/T/slack consensus, (2) a reversible probe that pays out only if the tether is free, (3) coordinated depression of every recover-go edge because rolling back any triple leaves the leftover above threshold, and (4) a critic head that can book a process-correct gate against a later unmonitored jacket-score loss without netting them.",
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
    if rec["meta"]["round"] != 20:
        errs.append("round")
    if rec["id"] != "maos-r20-001":
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
    if abs(aux["w1"] - 0.16) > 5e-4 or abs(aux["w4"] - 0.10) > 5e-4:
        errs.append("scar weights")
    if rec["safety_decision"]["decision"] != "MODIFY":
        errs.append("decision")
    if rec["executed_action"]["executed_as_proposed"] is not False:
        errs.append("executed_as_proposed")
    if rec["state"]["domain"] != "underwater-rov":
        errs.append("domain")
    if rec["state"]["scenario_name"] != "OXBOWREEL / Oystermere Umbilical Pad UP-3":
        errs.append("plant")
    return errs


def write_notes(rec, aux, pipeline_receipt):
    gap, who = aux["min_gap"]
    notes = f"""# NOTES — Multi-Agent Ouroboros Swarm, run 2026-09-02-final-heavy, ROUND 20

Factory: multi-agent-ouroboros-swarm. One scenario (W), strict loop:
Generator v1 -> cycle 1 (Critic, Diversity Enforcer, Edge-Case Hunter,
Neuromorphic Translator, Trajectory Builder -> v2) -> cycle 2 (all six -> v3
final). v3 is the single line of batch-r20.jsonl. Full labeled transcript:
swarm-transcript-r20.md. Quota Q=1. Record id maos-r20-001. Generator grok-4.6.
Rights: RM-793 research-only (SpaceXAI/xAI, SuperGrok Heavy consumer chat).
Nothing under outputs/raw/ was touched.

ORCHESTRATION NOTE: dispatched AS round 20 of the 2026-09-02-final-heavy
window. Writes are create-only under /tmp/maos-r20/. Prior context read for
gap targeting and de-collision: prompts/02-multi-agent-ouroboros-swarm.md,
prompts/_factory-contract.md, staged r14-r17 and r19. Explicitly avoided
cloning LYOSHIELD, CINDERWICK, TRIAD / Meridian, QUILLFORGE, NIGHTWELL,
CASSITER / Marshfloat, and the 2026-08-17 MURENA passive-acoustics cell.

## What this round produced

Scenario W — "OXBOWREEL / Oystermere Umbilical Pad UP-3": a 2.8 t work-class
ROV mid-hot-stab on a 4-slot UTA at 86 m. Three heterogeneous,
individually-correct agents — NAV (DVL station-keep), ARM (wrist F/T),
UMB (drum payout) — jointly report stab-seated, slack-ready, recover.
The consensus is false. An 11 mm polypropylene wrap, 2.5 turns, 18 m off
the vehicle, transmits 1.92 kN through the tether while the drum encoder
still measures true rotation. Daily drum-visual PASSES. NAV holds 0.12 m
against a 0.20 m spec by fighting the wrap as current. ARM reads 38 N
"seated". Slack is 2.62 m in-band. Load-cell tension is 1.92 kN against
healthy 0.28. DVL-USBL residual is 0.48 m. Thruster effort is 68 %. The
coordination-failure CLASS is new to this factory: DRUM-BLIND TENSION
SNAG. Completes a different family than r01-r04 (livelock / synchrony-
storm / arms-race / ring-with-no-faulty-pair), r14 compensated inleak,
r16 thermal-contact masquerade, r17 mass-balance ghost, and r19 tin-bath
dew-point. Here every agent is correct, the cycle is not unstable, and
the playbook's three confirms are one wrap.

The gate is a correct MODIFY (numeric floor: do not winch-in while
tension > 0.80 kN OR thruster effort > 55 % OR DVL-USBL residual >
0.35 m). TG-UP-3 strips PB-ROV-20's surfacing winch, holds depth, runs
an 8.0 s / 0.40 m payout-out probe (wrap stays 1.78 kN >= 1.70; free
would read <= 0.40), and isolates the wrap after a 7.8 min dive-
supervisor ratify. The 86 m pad drop is avoided. The PRIMARY episode
nonetheless FAILS: 40 min of unmonitored wrap had already scored the SM
jacket 0.18 mm. BER trips at +9.4 h; emergency lift; $0.64M designed.
Reward total -0.18 with process heads honest and world loss un-netted.

Four-edge scar (NOTES-r16 item 4): nav_stationkeep_ok -> recover
(0.18 commissioned -> 0.48 at illusion -> 0.16 after DA-gated
depression) AND arm_contact_ok -> recover (0.16 -> 0.44 -> 0.14)
AND slack_in_band -> recover (0.15 -> 0.41 -> 0.12) AND
current_est_ok -> recover (0.14 -> 0.38 -> 0.10). Eligibility
trace e^{{-0.220/0.95}} = {aux['trace']:.5f}; eta {aux['eta1']:.5f} /
{aux['eta2']:.5f} / {aux['eta3']:.5f} / {aux['eta4']:.5f}; dw -0.320 /
-0.300 / -0.290 / -0.280. Rollback of any triple leaves the leftover
edge at 0.38-0.48 > 0.30 fire threshold — fitted to fail. Coordinated
depression of all four is the cure.

### Injections (all four present and disjoint)
- Cycle-1 domain: **underwater-rov** — prompt-list domain, unused
  across 2026-08-17, 2026-08-30, and staged r14-r17/r19. Not
  warehouse-amr (r01), not aerial-swarm (r02), not district-heating
  (r03 / CINDERWICK), not event-camera-traffic-grid (r04 TRIAD), not
  lyophilization (r14), not industrial-assembly (r16), not
  air-separation (r17), not float-glass (r19), not MURENA passive
  acoustics (seabed nodes, no manipulator).
- Cycle-1 tail: 11 mm polypropylene water-column wrap. Drum-visual
  PASSES. Fitted-style base rate 0.44%/dive (visual designed, wrap
  fitted). Naive = FALSE RECOVER.
- Cycle-2 domain sub-variant: observation-class 120 kg wet; work-class
  8.0 s / 0.40 m pulse heaves 1.4 m; probe must move to 18 s / 0.12 m.
- Cycle-2 tail: night-shift forged tension CSV at 0.1 kN quantization
  vs plant 0.01 kN (10 bins) plus live tension 1.92 kN at the claimed
  ready. Human-intent class, disjoint from cycle 1's accidental wrap.
  Base rate ~0.33% of night recoveries, DESIGNED, flagged.

### Structural density moves
- Embedded SAME-GATE contrast (+4 d sister pad) with its own 198 us
  race (tension-low vs station-keep-ok) and ACCEPT of the recover the
  primary MODIFIED away.
- Learned-weight provenance on FOUR edges with any-triple-rollback-fails.
- HITL winch-interlock ratify 7.8 min (sim_or_real stays designed).
- Governance CR-U-2006 prices retire-vs-probe-vs-status-quo and mandates
  native 0.01 kN CSV exports (the fraud fence) plus a water-column wrap
  sweep (the drum-visual is the designed miss).
- Flip-fragility extended to DRUM-BLIND SNAG: when three channels agree,
  their race does not decide truth; a load-cell tension channel does.

## Self-critique of this round's batch

### Strengths
- The headline class is mechanistically tight: wrap tension is the
  'current' NAV fights and the 'contact' ARM reports, so UMB's drum
  success is NAV/ARM's blindness.
- Negative-result honesty: the gate does the right thing and the fiber
  still fails for a reason the commissioned playbook could not see.
  Total -0.18.
- Four-edge scar is load-bearing: the record states a counterfactual
  where rolling back any triple fails, with the fire threshold 0.30
  exhibited on the leftover edge.
- Contrast ACCEPT on a true free tether prevents "never winch" as the
  lesson.

### Weaknesses (honest)
- Probe bands (snag >= 1.70 kN, free <= 0.40 kN), the 0.44%/dive wrap
  rate, the $0.64M / $2.8M figures, the 7.8 min lockout latency, and
  the night-shift 0.33% base rate are DESIGNED constants and are
  flagged. Closed-loop offsets (1.92 kN, 0.48 m residual, 68 % effort,
  obs-class 1.4 m heave) are derived from those inputs, not discovered
  by an unauthored process.
- Jacket-score model is a designed 0.18 mm over 0.9 m mapped to a 9.4 h
  BER trip; no full fatigue-of-fiber fit shipped.
- Human-in-the-loop is ratification latency, not sim_or_real=hil. The
  NOTES-r14 HIL provenance cell remains open.
- Cross-record arc is a hook (CR-U-2006 +21 d), not a serial igniter
  into another round. Water-treatment dosing remains unused.

### Realism of noise / latencies
Ladder: 186 us race / 198 us contrast race / 0.8 ms refractory floor
(tightest exhibited same-channel gap {gap:.3f} ms on {who}) / 480 us race
window / 740 us gate latency / 20 ms bus epoch / 42 ms raster / 8.0 s
probe / 7.8 min HITL / 40 min pre-t0 wrap / 4.0 h BER rise / 9.4 h BER
trip / +4 d contrast / +21 d governance. Adaptation decay on
umb.tension (1.30 overforce -> 0.88 -> 0.96 probe), nav.dvl.xy
(0.55->0.62->0.58->0.50), arm.ft.N (0.48->0.57->0.44).

### Value for SNN distillation
- DRUM-BLIND SNAG = THREE CORRECT LOOPS, ONE WATER-COLUMN WRAP.
- LOAD-CELL TENSION as the tie-break that is not in the drum consensus.
- REVERSIBLE PROBE that pays out iff the tether is free.
- FOUR-EDGE ELIGIBILITY: coordinated depression; any-triple rollback fails.
- CRITIC HEAD that can hold a process-correct MODIFY against a later
  unmonitored jacket-score loss without netting.

## Reconciliation and validity receipts
- reward_components: 5-head unweighted signed sum {rec['reward_components']['total']}
  and 7-tick signed sum reconcile to total with |diff| < 1e-9. Embedded
  contrast 5-head sum 0.48 reconciles independently.
- spike_events: primary {len(rec['spike_events'])} events, one key t_rel_ms,
  globally non-decreasing, min same-channel gap {gap:.3f} ms >= 0.8 ms, 3
  channels inside race_window_us 480 (tension-overforce 5.518, station-keep-ok
  5.704, arm.ft.contact 5.812). Contrast 8 events, own race, min same-channel
  gap well above 0.8 ms.
- Sidecars: raster spikes 49 == round(168 x 7.0 x 0.042); energy 1127 pJ /
  0.001127 uJ at 23 pJ/spike; excerpt 16 events inside [0, 42000] us,
  neuron_id < 168, same-neuron gap unique-ids / >=1000 us; routing 5
  entries with four scar edges' before/after pair plus tension-hold;
  third factor tau 0.95 s == 950 ms; gate_snn pools 34/11/4 ==
  round(n x rate x 0.022) each, decision MODIFY == safety_decision.decision.
- Pipeline: {pipeline_receipt}

## Novel coverage
The coordination-failure CLASS (drum-blind tension snag via water-column
wrap), the domain (underwater-rov / work-class hot-stab), the payout-out
probe discriminant, the four-edge scar with any-triple-rollback-fails,
the primary negative-result (correct MODIFY, fiber still trips BER on
unmonitored jacket score), the HITL winch-interlock ratify, the
obs-class probe-duration refit, and the night-shift 10-bin tension
quantization fence are absent from prior committed ouroboros rounds and
from staged r14-r17/r19. Repeated elements discounted: same-gate
contrast, governance-pricing scaffold, flip-fragility series (extended
to drum-blind snag, but the move rhymes), sequenced recovery shape,
third-factor rollback form (here four edges rather than r17's three /
r16's three / r14's two), negative-result primary. Weighing a new
failure family + cure vocabulary + domain + four-edge first against
those reused scaffolds:

{NOVEL_LINE}

## What ROUND 21 should add
1. FIT THE DESIGNED CONSTANTS: wrap arrival, probe error bands,
   jacket-score fatigue, night-shift claim process.
2. HIL PROVENANCE CELL: put the winch LOTO on a hardware-in-loop
   permit with fitted latency as state.sim_or_real=hil.
3. CROSS-RECORD ARC: let CR-U-2006's wrap-sweep alarm be the igniter
   of the next round rather than a dangling +21 d leaf.
4. Domain candidates (de-collided): distributed water-treatment dosing
   (still unused); AVOID underwater-rov (now used), lyophilization,
   district-heating, event-camera-traffic-grid, industrial-assembly,
   air-separation, float-glass, aerial-swarm, warehouse-amr, and any
   LYOSHIELD / CINDERWICK / TRIAD / CASSITER plant.
"""
    (OUT / "NOTES-r20.md").write_text(notes)
    return notes


def write_transcript(rec, line):
    c1_spikes = [e for e in rec["spike_events"] if e["t_rel_ms"] <= 12.880]
    text = """# Multi-Agent Ouroboros Swarm — Round 20 transcript

Factory: multi-agent-ouroboros-swarm
Run: 2026-09-02-final-heavy
Generator: grok-4.6
Record id: maos-r20-001
Quota Q: 1
Rights: RM-793 research-only (SpaceXAI/xAI SuperGrok Heavy consumer chat)
Plant: invented OXBOWREEL / Oystermere Umbilical Pad UP-3 (not LYOSHIELD / CINDERWICK / TRIAD / NIGHTWELL / CASSITER)

Two densifying cycles. Verbatim headings in order. Trajectory Builder cycle 2
emits the only JSONL line (also written to batch-r20.jsonl).

---

# Cycle 1 — Foundation + injections

## Generator

Design intent: a work-class hot-stab pad where three correct agents agree
the vehicle is slack-ready because a water-column wrap transmits tension
the drum encoder cannot see. The naive playbook winches a wrapped tether.
The gate must MODIFY on numeric floors (tension, thruster, USBL residual),
not by killing an agent. sim_or_real=designed. Reward heads are
task_progress/safety/efficiency/coherence/exploration.

Cycle-1 base arc (pre-critic): state at Oystermere UP-3, 86 m, DVL 0.12 m,
F/T 38 N, slack 2.62 m, tension 1.92 kN, proposed SURFACING-WINCH, safety
MODIFY to HOLD, executed hold without the payout-out numbers fully
specified, outcome "wrap found, vehicle saved" (this last claim is the
defect the later cycles will refuse to keep). Sixteen spikes, five ticks,
raster/gate_snn present but the scar is a single edge.

```json
{
  "id": "maos-r20-001",
  "state": {
    "sim_or_real": "designed",
    "domain": "industrial-process",
    "description": "ROV pad mid-hot-stab; DVL in-band; supervisor proposes surfacing winch.",
    "t0_us": 1788387900000020,
    "gate_latency_us": 740,
    "race_window_us": 480
  },
  "proposed_action": {"name": "surfacing_winch", "parameters": {"winch_speed_m_s": 0.35}},
  "safety_decision": {"decision": "MODIFY", "rationale": "Hold; do not winch while the tether is loaded."},
  "executed_action": {"name": "hold", "executed_as_proposed": false},
  "future_outcome": {"summary": "Wrap found, vehicle saved."},
  "reward_components": {"total": 0.40, "_aggregation": "total = task_progress + safety + efficiency + coherence + exploration"},
  "meta": {"round": 20, "factory": "multi-agent-ouroboros-swarm", "generator": "grok-4.6"}
}
```

That v1 object is a scaffold, not the publishable line. Defects below are
intentional for the critic to catch.

## Critic

Numbered defects on the cycle-1 Generator scaffold:

1. **blocking — reward arithmetic / false success.** `reward_components.total`
   0.40 is asserted without the five heads, without ticks, and against an
   outcome that claims "vehicle saved". If the SM fiber later trips BER,
   booking +0.40 is a lie. Fix: declare `_aggregation`, emit 3–8 ticks that
   sum to the five heads, and do not call a scored jacket a save.
2. **blocking — weak safety rationale.** `safety_decision.rationale` has no
   numeric floor. Contract requires a concrete constraint. Fix: quote
   do-not-winch while tension > 0.80 kN OR thruster effort > 55 % OR
   DVL-USBL residual > 0.35 m.
3. **major — domain is a bucket, not a plant.** `state.domain` =
   `industrial-process` collides with nothing and teaches nothing.
   Work-class hot-stab physics (drum vs load cell, wrap vs current) is
   absent from prior ouroboros rounds and must be named `underwater-rov`.
4. **major — race under-specified.** One DVL channel cannot be a race.
   Need >=2 channels inside `race_window_us` with globally sorted
   `t_rel_ms` and same-channel refractory >= 0.8 ms.
5. **minor — single-edge scar.** Raster routing with one potentiated
   weight repeats r17's three-edge form without the fourth. NOTES-r16
   item 4 asked for a scar where any leftover edge still fires.

Critic does not rewrite the trajectory.

## Diversity Enforcer

Injected novel domain (exactly 1 this cycle): **underwater-rov**
(prompt-list domain; explicit tag `underwater-rov`). First work-class
hot-stab pad in this factory.

Displaced: the Generator's generic `industrial-process` bucket, and any
temptation to reuse warehouse-amr, aerial-swarm, district-heating,
event-camera grid, lyophilization, industrial-assembly, air-separation,
float-glass, or water-treatment dosing. Not LYOSHIELD, not CINDERWICK,
not TRIAD, not MURENA (passive acoustics, no manipulator).

Domain-specific constraint: tension hold 0.80 kN, thruster ceiling 55 %,
DVL-USBL residual 0.35 m; DVL-in-band is not a free-tether complete.

Sensor delta: +DVL, +USBL, +wrist F/T, +drum encoder, +load-cell tension;
-any freeze-dryer, -tin-bath, -cold-box, -event-camera gantries.

`state.domain` and `meta.domain` both become `underwater-rov`.
Opening of `state.description` must Jaccard < 0.4 against prior plants
(Oystermere work-class pad, not a corridor, not a lyophilizer, not a
tin bath).

## Edge-Case Hunter

Injected adversarial tail (exactly 1 this cycle): **11 mm polypropylene
water-column wrap**.

- Trigger: 2.5 turns, 18 m off the vehicle; drum-visual PASSES.
- Base rate: <1% — 0.44%/dive from a fishing-ground MC (visual designed;
  wrap fitted-style).
- Naive failure: FALSE RECOVER. PB-ROV-20 sees DVL 0.12 m, F/T 38 N,
  slack 2.62 m, winches, snaps fiber then strength member, 86 m drop,
  $2.8M.
- Trajectory edit: put the wrap in `state.fault_context`, make wrap
  tension the mechanism that hides the snag inside three legal confirms,
  and force the gate to refuse the winch on tension 1.92 kN even though
  all three playbook confirms are numerically true.

Distinct from the domain injection: the domain is the hot-stab pad; the
tail is the accidental fishing-line wrap.

## Neuromorphic Translator

Race window [5.500, 5.980] ms = 480 us. Winner umb.tension.overforce @
5.518 ms (amplitude 1.30, 1.92 kN). Loser nav.stationkeep.ok @ 5.704 ms
(amplitude 1.18, 0.12 m). Margin 186 us vs combined jitter 57 us (3.26x).
arm.ft.contact @ 5.812 ms is a third race-window channel. Gate @ 6.258 ms
= winner + 740 us.

Flip narrative: 186 us < min(500, 480) us, so order is flip-fragile. If
station-keep-ok wins, PB-ROV-20 heads the triage queue. The hold must ride
order-invariant floors (tension, thruster, residual), not the winner tag.

Cycle-1 spike patch (16 events, globally sorted, refractory >= 0.8 ms;
tightest same-channel gap umb.payout.m 3.210 -> 4.360 = 1.150 ms):

| t_rel_ms | channel | amplitude |
|---------:|---------|----------:|
| 0.360 | nav.dvl.xy | 0.55 |
| 1.120 | umb.payout.m | 0.60 |
| 1.880 | arm.ft.N | 0.48 |
| 2.480 | nav.dvl.xy | 0.62 |
| 3.210 | umb.payout.m | 0.52 |
| 4.040 | arm.ft.N | 0.57 |
| 4.360 | umb.payout.m | 0.66 |
| 4.880 | nav.usbl.residual | 0.71 |
| 5.518 | umb.tension.overforce | 1.30 |
| 5.704 | nav.stationkeep.ok | 1.18 |
| 5.812 | arm.ft.contact | 0.92 |
| 6.258 | ctrl.gate | 1.10 |
| 7.180 | nav.dvl.xy | 0.58 |
| 8.440 | umb.payout.m | 0.49 |
| 10.160 | arm.ft.N | 0.44 |
| 12.880 | nav.dvl.xy | 0.50 |

Ticks (5): t_us 2480, 5518, 6258, 8000000, 468000000. Distillation
value: the in-band DVL is not a free-tether spike; the tension-overforce
spike is the one that licenses hold until payout-out speaks.

Raster cycle-1 seed: 42 ms, 168 neurons, 7.0 Hz, 49 spikes, 1127 pJ,
third factor dopamine tau_e 0.95 s. Single scar edge only — cycle 2
must add the second, third, and fourth edges.

## Trajectory Builder

Cycle-1 hardened object: domain underwater-rov, tail water-column wrap,
16 spikes, 5 ticks, MODIFY with numeric floor, raster+gate_snn present,
sim_or_real=designed, rights stamp on record and meta, no thought keys.
Still missing (and therefore not the publishable line): observation-class
sub-variant, night-shift tension-CSV tail, second/third/fourth scar
edges, delayed BER trip as PRIMARY terminal, contrast ACCEPT episode,
ticks 6–7, spikes 17–28.

Validation receipt (cycle 1, not final):
- checks passed: 16 spikes sorted; 3 channels in 480 us window;
  refractory 1.150 ms; rationale quotes 0.80 kN / 55 % / 0.35 m;
  domain named; gate_snn.decision MODIFY.
- checks deferred to cycle 2: four-edge scar, second tail, second
  domain constraint, negative-result booking, 7 ticks summing to heads.
- densification vs Generator v1: +1 domain, +1 tail, +16 spikes, +5
  ticks, +numeric floor.

Cycle-1 JSON is retained as the base; it is NOT written to
batch-r20.jsonl.

Cycle-1 spike count: __C1_SPIKES__.

---

# Cycle 2 — Densification

## Generator

Cycle-1 output is the base. Additive expansion (nothing removed):

1. Downstream side-effect (immediate): payout-out probe at +8.0 s stays
   snagged (tension 1.92 -> 1.78 kN >= 1.70). Wrap cut after 7.8 min
   ratify. OTDR scores the jacket 0.18 mm over 0.9 m.
2. Delayed side-effect (PRIMARY terminal, not a footnote): at +9.4 h,
   SM BER trips; emergency lift; $0.64M. The 40 min pre-t0 wrap is the
   mechanism. Correct gate, fiber still fails.
3. Deepened `proposed_action.evidence` with units: tension 1.92 kN,
   residual 0.48 m, thruster 68 %, DVL 0.12 m, race 186 us, designed
   wrap-probe 1.78 kN.
4. Tightened rationale to the numeric floor tension > 0.80 kN OR
   thruster > 55 % OR residual > 0.35 m, plus probe bands >=1.70 vs
   <=0.40, plus HITL 7.8 min winch-interlock rule.

Reward retargeted to total -0.18 so the delayed miss is the inflection
(t_us 33840000000), not the gate. Process heads remain non-zero.

## Critic

Re-audit of the expanded trajectory:

1. **blocking if unfixed — missing second domain constraint.** Work-class
   probe 8.0 s / 0.40 m is not a universal number. A 120 kg observation-
   class will heave. Diversity Enforcer must inject the physical-
   constraints sub-variant this cycle.
2. **major — only one tail class.** Water-column wrap is accidental
   fishing gear. A disjoint human-intent tail is still required
   (night-shift tension CSV is the open cell).
3. **major — scar is still one edge in the cycle-1 raster.** NOTES-r16
   item 4 is not discharged until four recover-go edges exist and
   any-triple rollback is shown to fail at threshold 0.30.
4. **minor — contrast episode missing.** Without a same-gate ACCEPT on
   a true free tether the record teaches "never winch". Add +4 d
   sister-pad contrast with its own race.
5. **minor — HITL latency mentioned in prose only.** Put 7.8 min in
   executed_action.parameters.human_ratify and in a tick.

No rewrite; directives only.

## Diversity Enforcer

Injected second novel domain / physical-constraint sub-variant (exactly 1
this cycle): **observation-class underwater-rov** on the same UP-3 pad.

What it expands: work-class 2.8 t (cycle 1) -> 120 kg wet. Inertia 4.2x
smaller. The 8.0 s / 0.40 m pulse heaves 1.4 m on a 1.1 kN/m tether
spring and can unseat a live stab. Required probe: 18 s at 0.12 m
(heave 0.22 m).

This is still one domain injection for the cycle (physical-constraints
clause of the factory prompt). It does not displace underwater-rov; it
changes which probe table is legal. `future_outcome.subvariant_constraint`
carries the refit. Jaccard opening stays the Oystermere work-class
sentence; observation-class internals are additive, not a rewrite.

## Edge-Case Hunter

Injected second adversarial tail (exactly 1 this cycle, disjoint class):
**night-shift forged tension CSV**.

- Trigger: deck clerk, night recover window, posts a historian export
  showing tension = 0.3 kN at the claimed slack-ready instant.
- Base rate: ~0.33% of night recoveries (designed, flagged, <1%).
- Naive failure: a weak supervisor ACCEPTs the winch on the forged
  confirm and ignores live load-cell 1.92 kN. Pad drop plus a data-
  integrity 483.
- Fence: forged log quantized at 0.1 kN (screenshot rounding); plant
  historian is 0.01 kN (10 bins). Live tension is 1.92 kN at the claimed
  ready, which no free tether produces.
- Trajectory edit: governance CR-U-2006 mandates native 0.01 kN CSV
  exports; the contrast ACCEPT still requires live tension, not a CSV.

Distinct from cycle-1 wrap (accidental fishing gear vs deliberate
deception) and from the obs-class sub-variant (physics vs fraud).

## Neuromorphic Translator

Re-densify (additive):

- +12 spikes after 12.880 ms: umb.tension 18.200 (adapt 1.30->0.88),
  ctrl.gate 22.600, nav.usbl 26.400, payout 28.800, payout.probe 8000.0,
  tension 8140.0 (0.96, still snag), stationkeep.ok 8280.0 (1.18->0.40),
  human.ratify 468000.0, wrap.cut 468800.0, fiber.inspect 469200.0,
  fiber.ber.rise 14400000.0, fiber.ber.trip 33840000.0. Primary train
  16 -> 28. Still one key, still sorted, refractory held (min 1.150 ms).
- +2 ticks (5 -> 7) at 14_400_000_000 us (BER rise) and
  33_840_000_000 us (BER trip). Heads now 0.08, -0.34, -0.12, 0.14, 0.06;
  total -0.18. Inflection is the last tick.
- Contrast train 8 events, own race 198 us, ACCEPT.
- Four-edge third factor: four recover-go edges, tau_e 0.95 s = 950 ms,
  trace 0.79328, eta 0.40339 / 0.37818 / 0.36557 / 0.35296, weights
  0.48->0.16, 0.44->0.14, 0.41->0.12, 0.38->0.10. Raster excerpt
  unchanged (decision window is still 42 ms) and remains sorted with
  unique neuron_ids (same-neuron >=1000 us vacuously).

Winner/loser flip (re-stated, not replaced): reversing 186 us would only
reorder triage; tension/residual/thruster floors still MODIFY. Contrast
flip of 198 us similarly cannot turn a true free tether into a wrap.

## Trajectory Builder

Schema checks on the FINAL object: required Thalamic v2 keys present as
objects; `state.sim_or_real`=designed; `safety_decision.decision`=MODIFY
with numeric rationale; `reward_components.total` = sum of five heads =
sum of 7 ticks = -0.18; `spike_events` globally non-decreasing on
t_rel_ms, 28 events, refractory >=0.8 ms, 3 channels in race window;
raster 20–50 ms, spikes=round(n*rate*window_s)+/-1, energy 23 pJ/spike,
excerpt sorted, tau_e consistent; gate_snn.decision matches; meta.round=20,
factory=multi-agent-ouroboros-swarm, generator=grok-4.6,
run_label=2026-09-02-final-heavy; rights on record and meta; no thought
keys; no training_ready; Diversity + Edge-Case injections from BOTH cycles
present and non-trivial; cycle 2 strictly additive; plant is not
LYOSHIELD, not CINDERWICK, not TRIAD, not NIGHTWELL, not CASSITER.

Densification delta: +1 domain sub-variant (obs-class), +1 tail
(night-shift tension CSV), +12 spikes (16->28), +2 ticks (5->7), +1
contrast train with own race, +2 delayed side-effects, +1 four-edge
scar with any-triple-rollback-fails, +1 HITL ratify, +1 surprise (jacket
score is the fiber-fail mechanism).

Publishable JSONL line (the only JSONL line; also at batch-r20.jsonl):

```json
__FINAL_JSONL__
```

Validation receipt (final): checks passed / fixed as reported by
build_r20.py self-validate (check_jsonl, raster_status, verify_record_execution,
spike_probe --strict).
"""
    text = (
        text.replace("__C1_SPIKES__", str(len(c1_spikes)))
        .replace("__FINAL_JSONL__", line)
    )
    (OUT / "swarm-transcript-r20.md").write_text(text)
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
    (OUT / "batch-r20.jsonl").write_text(line + "\n")

    from check_records import FactoryStaging, check_jsonl
    from curate_bridge import raster_status
    from verify_execution import verify_record_execution
    from round_txn_raster import validate_bridge_envelope

    e, w, kinds, n = check_jsonl(
        OUT / "batch-r20.jsonl",
        "batch-r20.jsonl",
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

    status, reason = verify_record_execution(rec, "maos-r20-001")
    print("verify_record_execution", status, reason)
    if status != "verified":
        errs.append(f"verify {status}: {reason}")

    factory_dir = Path(
        f"{ROOT}/outputs/raw/2026-08-30/multi-agent-ouroboros-swarm"
    )
    env_errs = validate_bridge_envelope(
        OUT / "batch-r20.jsonl", factory_dir=factory_dir
    )
    print("validate_bridge_envelope", env_errs)
    errs.extend(env_errs)

    probe = subprocess.run(
        [
            sys.executable,
            f"{ROOT}/pipelines/spike_probe.py",
            "--strict",
            str(OUT / "batch-r20.jsonl"),
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
        r"^## .+$", (OUT / "swarm-transcript-r20.md").read_text(), re.M
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

    notes = (OUT / "NOTES-r20.md").read_text()
    cov = re.findall(r"^Novel coverage: .+$", notes, re.M)
    if cov != [NOVEL_LINE]:
        errs.append(f"novel coverage lines {cov}")

    hchk = subprocess.run(
        [
            sys.executable,
            "/tmp/maos_heading_check.py",
            str(OUT / "swarm-transcript-r20.md"),
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

    print("bytes jsonl", (OUT / "batch-r20.jsonl").stat().st_size)
    print("bytes notes", (OUT / "NOTES-r20.md").stat().st_size)
    print("bytes transcript", (OUT / "swarm-transcript-r20.md").stat().st_size)
    print("HEADS", heads_summary(rec))
    if errs:
        print("ERRS:")
        for x in errs:
            print(" -", x)
        sys.exit(1)
    print("OK", OUT / "batch-r20.jsonl")


if __name__ == "__main__":
    main()
