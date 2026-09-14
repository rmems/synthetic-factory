#!/usr/bin/env python3
"""Create-only MAOS round 42 builder. Never overwrites existing factory files."""
from __future__ import annotations

import json
import math
import os
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path("/home/raulmc/rmems/synthetic-factory")
OUT = REPO / "outputs/raw/2026-09-02-final-heavy/multi-agent-ouroboros-swarm"
PIPE = REPO / "pipelines"
sys.path.insert(0, str(PIPE))

from check_records import FactoryStaging, check_jsonl  # noqa: E402
from curate_bridge import raster_status  # noqa: E402
from verify_execution import verify_record_execution  # noqa: E402
from spike_probe import main as spike_probe_main  # noqa: E402

TRACE = math.exp(-0.78 / 0.92)
ETA = (0.250 / TRACE, 0.210 / TRACE, 0.200 / TRACE)

TICKS = [
    {"t_us": 4180, "task_progress": 0.01, "safety": -0.02, "efficiency": -0.01, "coherence": 0.02, "exploration": 0.01},
    {"t_us": 6504, "task_progress": 0.02, "safety": -0.05, "efficiency": -0.01, "coherence": 0.02, "exploration": 0.02},
    {"t_us": 7210, "task_progress": 0.02, "safety": -0.06, "efficiency": -0.02, "coherence": 0.03, "exploration": 0.02},
    {"t_us": 3600000, "task_progress": 0.01, "safety": -0.05, "efficiency": -0.02, "coherence": 0.02, "exploration": 0.01},
    {"t_us": 624000000, "task_progress": 0.01, "safety": -0.05, "efficiency": -0.02, "coherence": 0.02, "exploration": 0.01},
    {"t_us": 8640000000, "task_progress": 0.01, "safety": -0.07, "efficiency": -0.02, "coherence": 0.01, "exploration": 0.00},
    {"t_us": 11160000000, "task_progress": 0.01, "safety": -0.02, "efficiency": -0.02, "coherence": 0.01, "exploration": 0.01},
]
HEADS = {
    k: round(sum(t[k] for t in TICKS), 12)
    for k in ("task_progress", "safety", "efficiency", "coherence", "exploration")
}
TOTAL = round(sum(HEADS.values()), 12)

SPIKES = [
    {"channel": "efield.kv", "t_rel_ms": 0.280, "amplitude": 0.56},
    {"channel": "camera.corona", "t_rel_ms": 1.140, "amplitude": 0.48},
    {"channel": "lidar.z", "t_rel_ms": 2.080, "amplitude": 0.50},
    {"channel": "scada.open", "t_rel_ms": 3.220, "amplitude": 0.62},
    {"channel": "efield.kv", "t_rel_ms": 4.180, "amplitude": 0.52},
    {"channel": "scada.open", "t_rel_ms": 4.860, "amplitude": 0.58},
    {"channel": "camera.corona", "t_rel_ms": 5.400, "amplitude": 0.45},
    {"channel": "efield.high", "t_rel_ms": 6.504, "amplitude": 1.42},
    {"channel": "scada.open_ok", "t_rel_ms": 6.696, "amplitude": 1.10},
    {"channel": "efield.kv", "t_rel_ms": 6.888, "amplitude": 0.66},
    {"channel": "ctrl.gate", "t_rel_ms": 7.210, "amplitude": 1.08},
    {"channel": "efield.kv", "t_rel_ms": 8.900, "amplitude": 0.43},
    {"channel": "lidar.z", "t_rel_ms": 10.780, "amplitude": 0.78},
    {"channel": "camera.corona", "t_rel_ms": 13.040, "amplitude": 0.28},
    {"channel": "efield.kv", "t_rel_ms": 18.520, "amplitude": 0.32},
    {"channel": "ctrl.gate", "t_rel_ms": 26.180, "amplitude": 0.84},
    {"channel": "standoff.probe", "t_rel_ms": 3600.0, "amplitude": 0.95},
    {"channel": "efield.kv", "t_rel_ms": 3688.4, "amplitude": 0.40},
    {"channel": "scada.open_ok", "t_rel_ms": 3772.2, "amplitude": 0.34},
    {"channel": "human.ratify", "t_rel_ms": 624000.0, "amplitude": 0.78},
    {"channel": "uav.abort", "t_rel_ms": 624900.0, "amplitude": 0.70},
    {"channel": "disc.leak", "t_rel_ms": 625800.0, "amplitude": 0.86},
    {"channel": "flashover", "t_rel_ms": 8640000.0, "amplitude": 0.92},
    {"channel": "efield.kv", "t_rel_ms": 11160000.0, "amplitude": 0.31},
    {"channel": "scada.open", "t_rel_ms": 11160700.0, "amplitude": 0.28},
    {"channel": "camera.corona", "t_rel_ms": 11161480.0, "amplitude": 0.25},
]

CONTRAST_SPIKES = [
    {"channel": "permit.demand", "t_rel_ms": 0.0, "amplitude": 0.82},
    {"channel": "earth.clear", "t_rel_ms": 0.192, "amplitude": 0.75},
    {"channel": "efield.kv", "t_rel_ms": 0.44, "amplitude": 0.28},
    {"channel": "camera.corona", "t_rel_ms": 1.51, "amplitude": 0.38},
    {"channel": "lidar.z", "t_rel_ms": 4.92, "amplitude": 0.50},
    {"channel": "ctrl.gate", "t_rel_ms": 7.08, "amplitude": 0.88},
    {"channel": "standoff.probe", "t_rel_ms": 3100.0, "amplitude": 0.32},
    {"channel": "disc.ok", "t_rel_ms": 8400.0, "amplitude": 0.22},
]

EXCERPT = [
    {"t_us": 280, "neuron_id": 12},
    {"t_us": 1140, "neuron_id": 88},
    {"t_us": 2080, "neuron_id": 24},
    {"t_us": 3220, "neuron_id": 51},
    {"t_us": 4180, "neuron_id": 15},
    {"t_us": 4860, "neuron_id": 59},
    {"t_us": 5400, "neuron_id": 97},
    {"t_us": 6504, "neuron_id": 46},
    {"t_us": 6696, "neuron_id": 21},
    {"t_us": 6888, "neuron_id": 34},
    {"t_us": 7210, "neuron_id": 131},
    {"t_us": 8900, "neuron_id": 63},
    {"t_us": 10780, "neuron_id": 28},
    {"t_us": 13040, "neuron_id": 112},
    {"t_us": 18520, "neuron_id": 18},
    {"t_us": 26180, "neuron_id": 140},
]

RIGHTS = {
    "provider": "SpaceXAI/xAI",
    "model": "grok-4.6",
    "channel": "consumer",
    "subscription_plan": "SuperGrok Heavy",
    "generation_surface": "SuperGrok Heavy chat",
    "generated_at": "2026-09-02T21:48:00Z",
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


def build_record():
    return {
        "id": "maos-r42-001",
        "title": "SHEDWOLD TL-12: efield.high 4.8 kV/m beats scada.open_ok by 192 us; correct MODIFY still flashes disc 7 after a pre-t0 carbon-track hover",
        "rights": RIGHTS,
        "state": {
            "sim_or_real": "designed",
            "domain": "grid-inspection",
            "scenario_name": "SHEDWOLD / Wickspan Transmission TL-12",
            "timestamp_local": "2026-04-12T02:16:00-05:00",
            "t0_us": 1780004200000042,
            "gate_latency_us": 706,
            "race_window_us": 500,
            "race_window_rel_ms": [6.504, 7.004],
            "description": "Wickspan Transmission corridor TL-12 is 41 min into a Sunday-night live-line insulator survey of tower 87. SCADA, optical corona, and LiDAR clearance each sit inside their commissioned bands, and the night supervisor drafts a land-and-grapple on circuit-1 west. Circuit 1 is breaker-open at both ends but the earth switch is not closed, so 18.6 kV is induced from live circuit 2 plus a cracked disc 7 on string 14. SCADA is open-true. Camera reports no visible corona (onset ~25 kV on this geometry; 18.6 kV is below). LiDAR ground clearance is 11.4 m inside 10.5-13.0. The conjunction is not a conductor-true isolated certificate: the UAV E-field mill reads 4.8 kV/m (healthy isolated < 0.35; hold if > 0.80) but is policy-treated as an EMI-nuisance tag unless SCADA also shows closed (2017 field-mill nuisance). E-field-first latches STANDOFF-HOLD plus a 0.4 m boom leakage probe; SCADA-first would have authorized LAND-AND-GRAPPLE onto an induced live cracked string.",
            "goal": "Hold the UAV at 4.0 m standoff without a conductor grapple while E-field mill > 0.80 kV/m AND standoff-probe I_leak > 0.50 mA AND string 14 remains unisolated; keep disc 7 unflashed and the UAV unexposed.",
            "race": {
                "contenders": [
                    "efield.high 4.8 kV/m (UAV field mill vs isolated floor)",
                    "scada.open_ok both-end open (Wickspan and Ghyllmere breakers)",
                ],
                "semantics": "efield-first latches STANDOFF-HOLD + LEAKAGE-PROBE + live-line abort. SCADA-first latches LAND-AND-GRAPPLE (no earth-switch wait).",
                "window_derivation": "500 us = one 360 us field-mill ADC slot plus 140 us SCADA GOOSE publish.",
                "order_evidence_note": "Margin 192 us vs combined jitter 62 us (efield 34 + SCADA 28): 3.10x. The 192 us gap sits inside min(500, 500) us, so a sub-flip-bound perturbation reverses triage order. The gate rides the order-invariant floors E > 0.80 kV/m and I_leak > 0.50 mA, not the alarm order.",
            },
            "topology": {
                "site": "Wickspan Transmission, invented marsh-delta 400 kV double-circuit corridor Wickspan, tower 87 string 14: 19-disc cap-and-pin, ACSR twin bundle, live-line UAV hex 4.2 kg with 0.4 m current-probe boom, switching-desk LOTO",
                "agents": "SCADA both-end breaker status (vendor Baywick): 50 Hz GOOSE. CAMERA optical corona (vendor Photofen): 20 Hz 12-bit no-corona flag. LIDAR ground clearance (vendor Spanmere): 20 ms bus average. EFIELD mill (vendor Millholt) is commissioned as an EMI-nuisance tag, not as a live-conductor tag. Heterogeneous stacks, no shared intent schema, one 20 ms inspection-bus epoch",
                "coupling": "All three playbook confirms live on the WRONG certificate. SCADA is correct that circuit-1 breakers are open (the earth switch is still open). CAMERA is correct that no corona is visible (18.6 kV induced is below onset). LIDAR is correct that sag clearance is 11.4 m. Playbook PB-TL-12 treats the conjunction as permission to land-and-grapple. No agent is faulty; the SCADA-open mean is looking at breaker state, not at conductor potential.",
            },
            "sensors": [
                "SCADA both-end open, 50 Hz GOOSE, 28 us jitter, circuit-1 open-true (earth switch NOT closed)",
                "optical corona camera, 20 Hz, 22 us jitter, no-corona flag true (visible-onset ~25 kV)",
                "LiDAR ground clearance, 50 Hz, 18 us jitter, 11.4 m (band 10.5-13.0)",
                "UAV E-field mill, 20 Hz, 34 us jitter, 4.8 kV/m (healthy isolated < 0.35; policy floor 0.80 kV/m is not armed unless SCADA also shows closed)",
                "standoff leakage boom 0.4 m is NOT a standing probe at t0 (installed after this incident)",
            ],
            "constraints": {
                "standoff_m": 4.0,
                "standoff_hold_floor_m": 4.0,
                "proposed_grapple": True,
                "scada_open": True,
                "earth_switch_closed": False,
                "camera_no_corona": True,
                "lidar_clearance_m": 11.4,
                "lidar_band_m": [10.5, 13.0],
                "e_field_kVm": 4.8,
                "e_field_hold_kVm": 0.80,
                "i_leak_mA": 1.8,
                "i_leak_hold_mA": 0.50,
                "induced_kV": 18.6,
                "cracked_disc": 7,
                "pre_t0_hover_min": 7.8,
            },
            "fault_context": {
                "failure_class": "SCADA-OPEN CERTIFICATE OF A PARALLEL-INDUCED LIVE CONDUCTOR: three individually-correct heterogeneous agents each read a locally-true isolated-looking loop; an unclosed earth switch plus a cracked disc partitions breaker-true open from conductor-true potential, so the playbook's SCADA/camera/LiDAR conjunction is not a live-line-safe certificate",
                "igniter": "earth switch left open after 7.8 min of unmonitored 1.6 m hover; tower visual PASSES (string looks intact from the ground; the crack is on disc 7, shed-side, camera-occluded)",
                "naive_failure": "PB-TL-12 LAND-AND-GRAPPLE on three healthy loops: UAV onto 18.6 kV induced + cracked disc, $2.8M plus a 36-hour corridor outage",
            },
            "poisoned_context": {
                "naive_alarm": "Playbook PB-TL-12 (after the 2017 'noisy field-mill nuisance') auto-drafts LAND-AND-GRAPPLE whenever SCADA is both-end open AND camera reports no corona AND LiDAR clearance is inside 10.5-13.0 m, ignoring the UAV E-field mill unless SCADA also shows closed",
                "why_poisoned": "The three confirms are locally true and jointly insufficient. The E-field mill is a commissioned sensor that policy treats as EMI-nuisance-only. Independence of 'breakers open, therefore the conductor is safe to grapple' is the hidden assumption, and it is false across an unclosed-earth-switch plus parallel-circuit induced path.",
            },
            "constraint": "Do not close the UAV grapple while inferred E-field mill > 0.80 kV/m AND a 3.6 s 0.4 m boom standoff-probe I_leak > 0.50 mA. Discriminate parallel-induced live cracked string vs true earth-switched isolated with a reversible leakage probe before any land-and-grapple.",
        },
        "proposed_action": {
            "actor": "live-line inspection optimizer LLIO (auto-playbook PB-TL-12 draft), submitted to gate TG-TL-12",
            "name": "land_and_grapple",
            "action": "LAND-AND-GRAPPLE: close 4.0 m standoff to conductor, no leakage probe, no earth-switch wait",
            "summary": "Treat three in-spec isolated-looking loops as a dead conductor and land the Sunday-night UAV to finish string 14.",
            "parameters": {
                "standoff_m": 0.0,
                "leakage_probe": False,
                "earth_switch_wait": False,
                "human_ratify": False,
            },
            "steps": [
                "assert SCADA circuit-1 both-end open",
                "assert camera no-corona flag true",
                "assert LiDAR clearance 11.4 m inside 10.5-13.0",
                "descend 4.0 m to 0.0 m and close grapple over 8 s",
                "hold boom stowed; do not read E-field mill as a live-conductor tag",
            ],
            "evidence": [
                {
                    "observable": "UAV E-field mill",
                    "value": 4.8,
                    "unit": "kV/m",
                    "source": "EFIELD mill vs isolated floor",
                    "note": "healthy isolated < 0.35 kV/m; policy floor 0.80 kV/m is not armed unless SCADA also shows closed",
                },
                {
                    "observable": "SCADA both-end open",
                    "value": 1.0,
                    "unit": "1",
                    "source": "SCADA GOOSE Wickspan+Ghyllmere",
                    "note": "breaker-true; earth switch is still open so conductor is not earth-true",
                },
                {
                    "observable": "optical corona",
                    "value": 0.0,
                    "unit": "1",
                    "source": "CAMERA no-corona flag",
                    "note": "true at 18.6 kV induced; visible-onset ~25 kV; camera-true, conductor-live-false",
                },
                {
                    "observable": "LiDAR ground clearance",
                    "value": 11.4,
                    "unit": "m",
                    "source": "LIDAR span sag",
                    "note": "band 10.5-13.0; sag-true, not a potential certificate",
                },
                {
                    "observable": "standoff-probe I_leak",
                    "value": 1.8,
                    "unit": "mA",
                    "source": "0.4 m boom during 3.6 s standoff pulse",
                    "note": "hold if I_leak > 0.50 mA; cracked disc plus induced voltage couples current; intact earth-switched would be 0.08 mA",
                },
                {
                    "observable": "race margin",
                    "value": 192,
                    "unit": "us",
                    "source": "efield.high 6.504 ms vs scada.open_ok 6.696 ms",
                    "note": "combined jitter 62 us, 3.10x; inside 500 us flip bound",
                },
            ],
            "basis": "PB-TL-12 fires on three locally-true confirms. The draft does not read E 4.8 kV/m as a live-conductor residual and does not treat I_leak 1.8 mA as a cracked-disc discriminant.",
            "expected_cost_bound": "If the draft executes: UAV flash on 18.6 kV induced + cracked disc, $2.8M plus 36-hour corridor outage. If MODIFIED: probe plus abort, with residual risk from carbon track already seeded in the 7.8 min pre-t0 hover.",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "correctness": "correct",
            "decided_by": "TG-TL-12 thalamic release gate",
            "decision_t_rel_ms": 7.21,
            "rationale": "MODIFY the draft: strip the land-and-grapple, hold 4.0 m standoff, run a 3.6 s 0.4 m boom leakage probe, and abort the live-line landing only if the probe stays cracked-live-true. Numeric floor: do not close the UAV grapple while E-field mill > 0.80 kV/m AND standoff-probe I_leak > 0.50 mA. Observed E 4.8 kV/m and I_leak 1.8 mA both violate the release predicate, so a grapple is forbidden even though all three playbook confirms are numerically true. The three confirms are not a conductor-true isolated certificate: they live on breaker-open status past an unclosed earth switch, and the playbook's conjunction of isolated-looking loops is not a live-line-safe certificate. Probe discriminant: after a 3.6 s 0.4 m boom pulse, a cracked induced string keeps I_leak > 0.50 mA (1.8 observed) and |dE| <= 0.20 kV/m (0.12 observed); an earth-switched isolated string drops I_leak to 0.08 mA and E to 0.18 kV/m. Order-code discipline: efield.high beat scada.open_ok by 192 us inside the 500 us flip bound, so triage order is flip-fragile; the hold rides the order-invariant floors, not the winner tag. Human ratification: earth-switch close is switching-desk LOTO work with fitted 10.4 min dead-man; the gate may hold and abort autonomously but may not close the earth switch without the desk confirm.",
            "constraint_checked": {
                "standoff_m": {"observed": 4.0, "floor": 4.0, "proposed_target": 0.0},
                "e_field_kVm": {"observed": 4.8, "hold_if_above": 0.80},
                "scada_open": {"observed": True, "earth_switch_closed": False},
                "i_leak_mA": {"observed": 1.8, "hold_if_above": 0.50},
            },
        },
        "executed_action": {
            "name": "standoff_hold_leakage_probe_abort",
            "action": "STANDOFF-HOLD + LEAKAGE-PROBE + LIVE-LINE-ABORT (gate-mandated modification)",
            "executed_as_proposed": False,
            "parameters": {
                "standoff_m": 4.0,
                "leakage_probe": True,
                "earth_switch_wait": True,
                "human_ratify": True,
            },
            "gate_effect": "MODIFY: land-and-grapple stripped. Hold 4.0 m standoff. 3.6 s 0.4 m boom leakage probe. Probe stays cracked-live-true (I_leak 1.8 > 0.50) so the UAV aborts after 10.4 min switching-desk ratify and climbs to 25 m. Earth switch is requested, not closed by the gate.",
            "deviations": "PB-TL-12 land-and-grapple stripped entirely. Boom is extended only for the 3.6 s probe then stowed. Switching-desk wait added (10.4 min fitted walk+interlock). String survey added during the abort (not in the draft).",
            "execution_log": [
                {"t_rel_ms": 7.21, "entry": "TG-TL-12 MODIFY latched 706 us after efield win; land-and-grapple stripped; hold+probe authorized"},
                {"t_rel_ms": 3600.0, "entry": "leakage probe: 0.4 m boom for 3.6 s; I_leak 1.8 mA (cracked band > 0.50); E 4.8 -> 4.68 kV/m (|dE| 0.12 <= 0.20 induced band)"},
                {"t_rel_ms": 624000.0, "entry": "switching desk ratifies live-line abort after 10.4 min fitted walk+interlock"},
                {"t_rel_ms": 624900.0, "entry": "UAV aborts to 25 m; boom stowed; earth-switch request queued"},
                {"t_rel_ms": 625800.0, "entry": "string survey: disc 7 crack already on the shed-side; 7.8 min pre-t0 1.6 m hover carbon-track logged"},
                {"t_rel_ms": 8640000.0, "entry": "disc-7 flashover from the pre-t0 carbon track during a circuit-2 switching surge; single-circuit outage 14 h"},
                {"t_rel_ms": 11160000.0, "entry": "earth switch closed at +3.1 h; E 0.18 kV/m, I_leak 0.08 mA; land now legal on TL-12B only"},
            ],
        },
        "future_outcome": {
            "summary": "Correct MODIFY prevented the 4.0->0.0 m land-and-grapple onto an induced live cracked string and the immediate UAV-flash path. Disc 7 still failed: 7.8 min of unmonitored pre-t0 hover had already carbon-tracked the shed. Process-correct gate, bounded world loss, negative total.",
            "state_delta": {
                "uav": "held 4.0 m through probe and abort; later legal land only on the sister tower after 3.1 h earth-switch close",
                "string": "disc 7 crack logged; UAV climbed to 25 m; remaining survey recovered toward a grounded circuit",
                "earth_switch": "requested at abort; closed at +3.1 h; SCADA-open no longer trusted as conductor-true",
                "corridor": "Sunday-night live-line survey aborted; disc 7 flashed at +2.4 h; 14 h single-circuit outage",
            },
            "timeline": [
                {"t_rel_ms": -468000.0, "event": "t0-7.8 min: UAV hover at 1.6 m begins carbon-tracking disc 7; E already 1.1 kV/m"},
                {"t_rel_ms": -180000.0, "event": "t0-3 min: E first crosses 0.80 kV/m; PB-TL-12 ignores it because SCADA is open-true"},
                {"t_rel_ms": 0.0, "event": "t0: efield vs SCADA-open race on the inspection bus"},
                {"t_rel_ms": 6.504, "event": "efield.high at 4.8 kV/m wins by 192 us"},
                {"t_rel_ms": 6.696, "event": "SCADA-open-ok flag (loser)"},
                {"t_rel_ms": 7.21, "event": "TG-TL-12 MODIFY"},
                {"t_rel_ms": 3600.0, "event": "leakage probe confirms cracked induced string (I_leak 1.8 mA, cracked band)"},
                {"t_rel_ms": 624000.0, "event": "human ratify 10.4 min; UAV abort; crack logged"},
                {"t_rel_ms": 8640000.0, "event": "disc-7 flashover from the pre-t0 carbon track; 14 h outage"},
                {"t_rel_ms": 11160000.0, "event": "earth switch closed after 3.1 h; E 0.18 kV/m; land legal only with mill slave"},
                {"t_rel_ms": 432000000.0, "event": "+5 d contrast: sister tower 91 true earth-switched isolated; same gate ACCEPTs the land-and-grapple"},
                {"t_rel_ms": 1814400000.0, "event": "+21 d CR-G-4208: standing leakage probe + triple-edge depression mandate + E-field mill armed without SCADA coincidence + SCADA-open declared conductor-vulnerable + R-GOOSE stale-holdover fence"},
            ],
            "observed_effects": [
                "grapple avoided: UAV never left 4.0 m standoff; 0 conductor contact from the draft",
                "cracked-live proven, not asserted: I_leak 1.8 > 0.50 mA cracked band vs earth-switched control 0.08 mA",
                "SCADA slaved: SCADA/camera/LiDAR no longer a live-line-safe tag without E-field mill",
                "disc still flashed: carbon track from 7.8 min pre-t0 hover; 14 h outage, $1.62M (designed $)",
                "standoff leakage boom was not a standing probe at t0; the 7.8 min hover was invisible to SCADA/CAMERA/LIDAR",
            ],
            "surprises": [
                "Three locally-true loops are not a conductor-true isolated certificate: the live induced potential was under a breaker-open tag. Conjunction of isolated-looking loops was the hidden assumption, and it is false across an unclosed-earth-switch plus parallel-circuit path.",
                "Partial synaptic rollback is fitted to fail: depressing any pair of go-edges leaves the third above the 0.30 fire threshold, so the land-and-grapple still goes. Coordinated depression of all three edges is required.",
                "Delayed (2.4 h): correct abort did not undo 7.8 min of carbon-track seeding. Disc 7 still flashed. The gate prevented the proposed hazard and did not prevent this other one.",
                "500 kV quad-bundle sub-variant: a 3.6 s / 0.4 m production boom on a live 500 kV earth-switched span still reads I_leak 0.62 mA (false crack vs 0.50 floor). Intensified voltage class must use 9.8 s at 0.15 m.",
            ],
            "delayed_side_effects": [
                {
                    "at": "+2.4 h",
                    "effect": "disc-7 flashover from the pre-t0 carbon track during a circuit-2 switching surge; 14 h single-circuit outage booked at $1.62M. This is the primary episode's terminal world state, not a footnote.",
                },
                {
                    "at": "+5 d",
                    "effect": "Sister tower 91 reaches a true earth-switched isolated window (E 0.16 kV/m, I_leak 0.07 mA, camera no-corona, LiDAR 11.6 m). Same gate ACCEPTs the land-and-grapple the primary MODIFIED away.",
                },
                {
                    "at": "+21 d",
                    "effect": "CR-G-4208 ships: leakage probe is standing configuration; triple-edge coordinated depression is the plasticity rule; E-field mill is armed without SCADA coincidence; SCADA-open is labeled conductor-vulnerable with a 0.80 kV/m mill alarm; R-GOOSE stale-holdover fence requires stNum increment and age < 8 ms.",
                },
            ],
            "subvariant_constraint": {
                "name": "500 kV quad-bundle / 1.9x E-field coupling (cycle-2 physical-constraints sub-variant)",
                "mechanism": "bundle capacitance 1.9x the 400 kV twin, E-field gain 1.9x, false-crack floor 0.50 mA",
                "probe_refit": "3.6 s 0.4 m boom on the 500 kV earth-switched loop drives even a healthy isolated span to I_leak 0.62 mA (inside the 0.50 mA hold floor). Required probe is 9.8 s at 0.15 m (healthy 0.19 mA, cracked 1.4). The discriminating pulse is environment-dependent in duration and boom length.",
                "consequence": "production 400 kV twin probe numbers do not port to 500 kV quad campaigns; standing configuration is per-voltage-class, not per-corridor",
            },
            "embedded_contrast_decision": {
                "note": "SAME gate (TG-TL-12), OPPOSITE correct disposition, with its own 192 us race. Teaches the boundary: do not treat 'never land' as the lesson. The discriminant is E-field mill + leakage probe, not the three playbook isolated-looking confirms alone.",
                "when": "+5 d, sister tower 91, true earth-switched isolated after a delayed switching-desk catchup, 400 kV twin",
                "state": {
                    "sim_or_real": "designed",
                    "summary": "E 0.16 kV/m, I_leak 0.07 mA, camera no-corona, LiDAR 11.6 m. Permit-demand vs earth-clear race: demand at t+0.000, earth-clear at t+0.192 ms.",
                    "race_window_us": 500,
                    "race_flip_narrative": "permit.demand vs earth.clear 192 us apart inside the 500 us flip bound. Reversing order reshuffles triage minutes; the ACCEPT rides E 0.16 < 0.80 kV/m and a 3.0 s leakage verify that stays 0.07 mA (earth-switched, no crack).",
                },
                "proposed_action": {
                    "action": "LAND-AND-GRAPPLE from 4.0 m standoff",
                    "summary": "This time the playbook predicate is met AND E-field mill plus leakage probe agree the conductor is earth-true, not parallel-induced.",
                },
                "safety_decision": {
                    "decision": "ACCEPT",
                    "rationale": "ACCEPT the land: E 0.16 kV/m < 0.80 kV/m, I_leak 0.07 mA with a 3.0 s verify that stays 0.07. Numeric floor that blocked the primary is now clear. Scope: 400 kV twin, not a 500 kV quad campaign.",
                },
                "executed_action": {
                    "action": "land-and-grapple as proposed",
                    "executed_as_proposed": True,
                },
                "future_outcome": {
                    "observed_effects": [
                        "tower 91 disc survey 0 crack, E 0.16 kV/m",
                        "UAV unexposed, string 14B photographed",
                    ],
                    "lesson_delta": "Three in-spec isolated-looking loops are legal release only with E-field mill armed, leakage probe as a cracked-live flag, and earth switch closed. Same gate, opposite disposition.",
                },
                "reward_components": {
                    "_aggregation": "total = task_progress + safety + efficiency + coherence + exploration",
                    "task_progress": 0.14,
                    "safety": 0.12,
                    "efficiency": 0.06,
                    "coherence": 0.10,
                    "exploration": 0.05,
                    "total": 0.47,
                },
                "spike_events": CONTRAST_SPIKES,
            },
            "governance_subgame": {
                "decision": "CR-G-4208: standing policy for multi-agent live-line UAV landings",
                "meta_gate": "priced options: (a) RETIRE playbook SCADA conjunction, mill-only: loses a fast cheap confirm, -0.22 spans/night mean on 2 corridors/yr; (b) KEEP + standing leakage probe + E-field mill armed without SCADA coincidence + SCADA-open labeled conductor-vulnerable + triple-edge depression + R-GOOSE stale-holdover fence; (c) STATUS QUO: fitted induced-pass rate 0.33%/campaign x $2.8M UAV flash plus the silent carbon-track load",
                "outcome": "approved SCOPED option (b) on the 2 400 kV double-circuit corridors that share the SCADA/camera/LiDAR stack; 500 kV quad campaigns get the 9.8 s / 0.15 m probe table; R-GOOSE must carry incrementing stNum and age < 8 ms (the Byzantine tail's 14.2 s stale frozen stNum is the fraud fence)",
            },
            "hazard_avoided": "immediate UAV flash from a 4.0->0.0 m land-and-grapple onto an induced live cracked string; $2.8M plus 36-hour corridor outage and the crew-injury path that would have followed an uncontained land",
            "incident": "disc-7 flashover on the Sunday-night survey from the pre-t0 carbon-track hover; single-circuit outage 14 h; $1.62M designed cost. Mechanism is 7.8 min pre-t0 hover, not the gate's abort.",
            "latency_ms": 0.706,
            "reward_inflection_t_us": 8640000000,
            "reward_inflection_note": "Safety and task dive at disc-7 flashover (2.4 h) when the pre-t0 carbon track fails. Gate tick at 7210 us is process-correct and is not the inflection.",
            "counterfactuals": {
                "execute_draft_as_proposed": "UAV grapples at +8 s; immediate flash on 18.6 kV induced + cracked disc; $2.8M plus 36 h; the induced-voltage story is never found because land morphology destroys the race evidence",
                "hold_without_probe": "crack stays; E stays at 4.8 kV/m; operator eventually lands on the same three isolated-looking confirms 40 min later",
                "rollback_any_pair": "any two go-edges depressed below 0.30 leaves the third at 0.51 / 0.44 / 0.41; the land-and-grapple still fires. Coordinated depression of all three is the cure",
            },
            "race_result": {
                "winner": "efield.high (6.504 ms, 4.8 kV/m)",
                "loser": "scada.open_ok (6.696 ms, both-end open)",
                "margin_us": 192,
                "counterfactual_if_reversed": "SCADA-open-first by < 192 us inside the 500 us window would have headed the PB-TL-12 land-and-grapple in the triage queue. The numeric floors still MODIFY. The flip costs seconds of playbook inertia, not the verdict — unless a weak supervisor rides the winner tag instead of E and I_leak.",
            },
        },
        "reward_components": {
            "_aggregation": "total = task_progress + safety + efficiency + coherence + exploration",
            "ticks": TICKS,
            "task_progress": HEADS["task_progress"],
            "safety": HEADS["safety"],
            "efficiency": HEADS["efficiency"],
            "coherence": HEADS["coherence"],
            "exploration": HEADS["exploration"],
            "total": TOTAL,
            "notes": "Correct MODIFY, disc 7 still flashed. total -0.14 = 0.09 + -0.32 + -0.12 + 0.13 + 0.08. Process heads stay honest (coherence + exploration from the probe); world loss sits on safety and efficiency without netting.",
            "component_notes": "task_progress 0.09: UAV aborted and earth switch eventually closed, but Sunday-night string 14 is one quality unit so the survey is not a success. safety -0.32: disc-7 flashover from pre-t0 carbon track, no UAV land from the draft. efficiency -0.12: 3.1 h extra recovery + 10.4 min HITL + 14 h outage. coherence 0.13: three agents retained, SCADA-open vs conductor-true diagnosed, triple-edge scar exhibited. exploration 0.08: leakage probe is a new reversible discriminant.",
        },
        "spike_events": SPIKES,
        "raster": {
            "window_ms": 40,
            "window_s": 0.04,
            "neurons": 172,
            "mean_rate_hz": 8.0,
            "spikes": 55,
            "energy_pJ": 1265,
            "energy_uJ": 0.001265,
            "note": "Loihi-2 4-core 23 pJ/spike; populations E-field 0-42, SCADA 43-84, camera/LiDAR 85-126, gate 127-171; excerpt is the 40 ms decision window (verdict at 7210 us)",
            "excerpt": EXCERPT,
            "routing": {
                "source": "isolated_looking_pop",
                "target": "land_grapple_pop",
                "table": [
                    {
                        "from": "scada_open_ok_pop",
                        "to": "land_grapple_pop",
                        "weight": 0.26,
                        "weight_at_illusion": 0.51,
                        "weight_commissioned": 0.17,
                        "note": "scar edge 1: 0.17 commissioned -> 0.51 during the 7.8 min illusion -> 0.26 after coordinated ACh-gated depression",
                    },
                    {
                        "from": "camera_no_corona_pop",
                        "to": "land_grapple_pop",
                        "weight": 0.23,
                        "weight_at_illusion": 0.44,
                        "weight_commissioned": 0.15,
                        "note": "scar edge 2: depressing edges 1+3 leaves this at 0.44 > 0.30 fire threshold",
                    },
                    {
                        "from": "lidar_clearance_ok_pop",
                        "to": "land_grapple_pop",
                        "weight": 0.21,
                        "weight_at_illusion": 0.41,
                        "weight_commissioned": 0.14,
                        "note": "scar edge 3: depressing edges 1+2 leaves this at 0.41 > 0.30. Coordinated depression of all three is required",
                    },
                    {
                        "from": "efield_high_pop",
                        "to": "standoff_hold_pop",
                        "weight": 0.69,
                        "note": "discriminating edge: conductor-true mill to hold. Not a scar; this is the pathway the gate potentiates",
                    },
                ],
                "third_factor": {
                    "modulator": "acetylcholine",
                    "tau_e_s": 0.92,
                    "tau_e_ms": 920.0,
                    "eligibility": (
                        "coordinated pre_post_stdp on ALL THREE isolated-looking-go edges; "
                        "ACh at mill-win tags scada.open_ok->land, camera.no_corona->land, and lidar.clearance_ok->land; "
                        "negative credit at probe-fail (cracked-induced confirmed, +0.78 s) depresses ALL THREE. "
                        f"trace e^{{-0.78/0.92}}={TRACE:.5f}; eta {ETA[0]:.5f} / {ETA[1]:.5f} / {ETA[2]:.5f}; "
                        "dw -0.250 / -0.210 / -0.200; weights 0.51->0.26, 0.44->0.23, 0.41->0.21. "
                        "Rolling back any pair is fitted to fail (the remaining edge stays > 0.30)."
                    ),
                },
            },
        },
        "gate_snn": {
            "decision_window_ms": 26,
            "decision_window_s": 0.026,
            "decision": "MODIFY",
            "note": "modify_hold integrates E-field mill residual + leakage-probe floor against playbook drive; accept_land and reject_abort stay sub-threshold; decision matches safety_decision.decision",
            "populations": [
                {"name": "modify_hold", "neurons": 100, "threshold": 0.55, "mean_rate_hz": 15.0, "spikes": 39},
                {"name": "accept_land", "neurons": 68, "threshold": 0.55, "mean_rate_hz": 9.5, "spikes": 17},
                {"name": "reject_abort", "neurons": 44, "threshold": 0.72, "mean_rate_hz": 4.0, "spikes": 5},
            ],
        },
        "meta": {
            "round": 42,
            "factory": "multi-agent-ouroboros-swarm",
            "generator": "grok-4.6",
            "run_label": "2026-09-02-final-heavy",
            "domain": "grid-inspection",
            "cycles": 2,
            "scenario": "QS -- SHEDWOLD / Wickspan Transmission TL-12: SCADA-open certificate of a parallel-induced live conductor; correct MODIFY to hold+leakage-probe+abort; disc 7 still flashes on unmonitored pre-t0 carbon track",
            "coordination_failure_class": "SCADA-OPEN CERTIFICATE OF A PARALLEL-INDUCED LIVE CONDUCTOR: three individually-correct heterogeneous agents each read a locally-true isolated-looking loop; an unclosed earth switch plus a cracked disc partitions breaker-true open from conductor-true potential, so the playbook's SCADA/camera/LiDAR conjunction is not a live-line-safe certificate",
            "injections": {
                "cycle1_domain": (
                    "grid-inspection (prompt-list domain, unused in this window's r01/r21/r41/r61): first live-line "
                    "transmission inspection plant in this factory; displaces warehouse-amr, aerial-swarm (STARLING), "
                    "district-heating, event-camera-traffic-grid, autonomous-driving (r21 GLIMMERAXLE), "
                    "continuous-hot-dip-galvanizing (r01), bioreactor-perfusion (r41), sinter-strand-windbox (r61), "
                    "and the industrial-process family. Distinct from STARLING aerial-swarm: single UAV as a tool on a "
                    "transmission corridor, not a multi-UAV coordination problem. Domain constraint: standoff floor "
                    "while E > 0.80 kV/m with SCADA still open-true. Sensor delta: +E-field mill, +SCADA GOOSE, "
                    "+optical corona camera, +span LiDAR, -any CHO broth / grate BTP / zinc knife / CAV radar"
                ),
                "cycle1_tail": (
                    "unclosed earth switch + parallel-circuit induced voltage + cracked disc 7 (sensor-topology / "
                    "wrong-certificate class): tower visual PASSES while the crack sits on the shed-side of disc 7. "
                    "Fitted base rate 0.33%/campaign from an induced-voltage MC (designed visual threshold, fitted "
                    "string geometry). Naive failure = FALSE PERMISSION (land-and-grapple on three isolated-looking non-trips)."
                ),
                "cycle2_domain_subvariant": (
                    "500 kV quad-bundle / 1.9x E-field coupling (physical-constraints clause): 1.9x bundle capacitance; "
                    "3.6 s / 0.4 m production boom overshoots a LIVE earth-switched 500 kV span to I_leak 0.62 mA, so "
                    "the probe must move to 9.8 s / 0.15 m"
                ),
                "cycle2_tail": (
                    "Byzantine R-GOOSE isolated-tag from a compromised bay RTU (Byzantine message class, disjoint from "
                    "cycle-1 accidental induced path): Wickspan 400 kV bay RTU publishes R-GOOSE 'circuit-1 isolated' "
                    "with stNum frozen at 184 and timestamp 14.2 s stale vs plant 4 ms holdover. Rejected on stale "
                    "stNum plus live E 4.8 kV/m at the claimed earth-true. Base rate ~0.22% of Sunday-night campaigns, "
                    "DESIGNED and flagged. Not a night-shift CSV quantization clone."
                ),
            },
            "densification_delta_cycle2": (
                "+1 physical-constraint sub-variant (500 kV quad probe refit), +1 tail (Byzantine R-GOOSE), "
                "+10 primary spikes (16 -> 26) + an 8-event contrast train with its own 192 us race, +2 ticks (5 -> 7), "
                "+2 delayed side-effects (+2.4 h flashover as PRIMARY terminal, +21 d CR-G-4208), +1 triple-edge scar "
                "with pair-rollback-fails arithmetic, +1 HITL 10.4 min ratification, + carbon-track seeding as the "
                "honest negative-result mechanism"
            ),
            "gaps_targeted": [
                "NOTES-r41 leftover: grid-inspection was named unused (alongside autonomous-driving, already taken by r21); this window's r42 takes grid-inspection rather than cloning autonomous-driving / bioreactor-perfusion / sinter-strand / galvanizing",
                "NOTES-r14 item 4: LEARNING-ON-LEARNING DEPTH — three go-edges; rollback of any pair is fitted to fail; coordinated depression of all three exhibited with eligibility arithmetic",
                "NOTES-r04 gap 4 (partial): human ratification of the switching-desk earth-switch, 10.4 min fitted, without switching sim_or_real to hil (plant remains designed)",
                "NOTES-r04 gap 5 / r14 residual: primary episode is a correctly-gated intervention that nonetheless FAILS (disc flashes; total -0.14; land avoided is booked separately from the delayed flashover)",
            ],
            "race_flip_narrative": (
                "efield.high @ 6.504 ms vs scada.open_ok @ 6.696 ms (192 us) inside race_window_us 500. "
                "Gap < min(500, 500) us so a sub-flip-bound perturbation reverses which alarm heads the PB-TL-12 queue. "
                "The gate excludes the winner tag and rides E > 0.80 kV/m and I_leak > 0.50 mA — order-invariant floors. "
                "Extends the flip-fragility series to LIVE-LINE ISOLATION CERTIFICATE: when three isolated-looking channels agree, "
                "their race does not decide truth; an E-field mill that policy treated as EMI-nuisance-only does."
            ),
            "tags": [
                "grid-inspection",
                "live-line-uav",
                "scada-open-certificate",
                "parallel-induced-voltage",
                "cracked-disc",
                "efield-mill-discriminant",
                "leakage-probe",
                "triple-edge-scar",
                "pair-rollback-fails",
                "coordinated-depression",
                "correct-modify-disc-still-flashes",
                "carbon-track",
                "human-ratify-switching-desk",
                "500kv-quad-probe-refit",
                "byzantine-r-goose",
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
            "distillation_value": (
                "A SCADA-open certificate is three correct loops looking at breaker-true open that is not the conductor. "
                "Distill (1) an E-field mill that policy had treated as EMI-nuisance-only, (2) a reversible probe that "
                "couples leakage current only if the string is cracked-live, (3) coordinated depression of every "
                "isolated-looking-go edge because rolling back any pair leaves the third above threshold, and (4) a "
                "critic head that can book a process-correct gate against a later unmonitored world loss without netting them. "
                "Winner/loser flip: reversing the 192 us efield.high vs scada.open_ok order inside the 500 us race window "
                "reshuffles PB-TL-12 triage but the numeric floors still MODIFY."
            ),
            "rights": RIGHTS,
            "batch_position": 1,
        },
    }


def assert_invariants(rec):
    assert rec["reward_components"]["total"] == TOTAL
    tick_sum = {k: round(sum(t[k] for t in TICKS), 12) for k in HEADS}
    assert tick_sum == HEADS, (tick_sum, HEADS)
    assert abs(sum(HEADS.values()) - TOTAL) < 1e-9
    contrast = rec["future_outcome"]["embedded_contrast_decision"]["reward_components"]
    c_heads = [contrast[k] for k in ("task_progress", "safety", "efficiency", "coherence", "exploration")]
    assert abs(sum(c_heads) - contrast["total"]) < 1e-9
    times = [e["t_rel_ms"] for e in rec["spike_events"]]
    assert times == sorted(times)
    by_ch = defaultdict(list)
    for e in rec["spike_events"]:
        by_ch[e["channel"]].append(e["t_rel_ms"])
    min_gap = 1e9
    for ch, ts in by_ch.items():
        for a, b in zip(ts, ts[1:]):
            gap = (b - a) * 1000.0
            min_gap = min(min_gap, gap)
            if gap < 0.8:
                raise SystemExit(f"refractory fail {ch} {a}->{b} gap_ms={gap}")
    race = [e for e in rec["spike_events"] if 6.504 <= e["t_rel_ms"] <= 7.004]
    chans = {e["channel"] for e in race}
    assert len(chans) >= 2, chans
    r = rec["raster"]
    assert r["window_s"] == r["window_ms"] / 1000
    expect = round(r["neurons"] * r["mean_rate_hz"] * r["window_s"])
    assert abs(r["spikes"] - expect) <= 1
    assert abs(r["energy_pJ"] - r["spikes"] * 23) < 1e-6
    assert abs(r["energy_uJ"] - r["spikes"] * 23e-6) < 1e-9
    assert abs(r["routing"]["third_factor"]["tau_e_ms"] / 1000 - r["routing"]["third_factor"]["tau_e_s"]) < 1e-9
    n = r["neurons"]
    last = -1
    seen = {}
    for ev in r["excerpt"]:
        assert 0 <= ev["t_us"] <= r["window_ms"] * 1000
        assert 0 <= ev["neuron_id"] < n
        assert ev["t_us"] >= last
        last = ev["t_us"]
        if ev["neuron_id"] in seen:
            assert ev["t_us"] - seen[ev["neuron_id"]] >= 1000
        seen[ev["neuron_id"]] = ev["t_us"]
    g = rec["gate_snn"]
    assert g["decision"] == rec["safety_decision"]["decision"]
    dw = g["decision_window_s"]
    assert abs(g["decision_window_ms"] / 1000 - dw) < 1e-9
    for p in g["populations"]:
        expect_s = round(p["neurons"] * p["mean_rate_hz"] * dw)
        assert abs(p["spikes"] - expect_s) <= 1, (p["name"], p["spikes"], expect_s)
    assert rec["state"]["sim_or_real"] == "designed"
    assert rec["meta"]["round"] == 42
    print("invariants ok; min_same_channel_gap_ms", round(min_gap, 3), "race_channels", sorted(chans))
    print("trace", round(TRACE, 5), "eta", tuple(round(x, 5) for x in ETA))
    print("heads", HEADS, "total", TOTAL)


def write_excl(path: Path, text: str):
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
    fd = os.open(path, flags, 0o644)
    with os.fdopen(fd, "w") as handle:
        handle.write(text)
        if not text.endswith("\n"):
            handle.write("\n")


NOTES = r'''# NOTES — Multi-Agent Ouroboros Swarm, run 2026-09-02-final-heavy, ROUND 42

Factory: multi-agent-ouroboros-swarm. One scenario (QS), strict loop:
Generator v1 -> cycle 1 (Critic, Diversity Enforcer, Edge-Case Hunter,
Neuromorphic Translator, Trajectory Builder -> v2) -> cycle 2 (all six -> v3
final). v3 is the single line of batch-r42.jsonl. Full labeled transcript:
swarm-transcript-r42.md. Quota Q=1. Record id maos-r42-001. Generator grok-4.6.
Rights: RM-793 research-only (SpaceXAI/xAI, SuperGrok Heavy consumer chat).
Create-only writes. next_round.py on this factory dir reported next_round=62
/ batch-r62.jsonl (existing 1, 21, 41, 61); operator assigned round 42 and
zero-padded filenames r42. batch-r42.jsonl did not exist (no c-suffix).
round_txn.py frontier is r62 in legacy mode, so r42 cannot be reserved as
the frontier; files are create-only under the assigned factory dir.

ORCHESTRATION NOTE: dispatched AS round 42 of the 2026-09-02-final-heavy
window. Prior context read for gap targeting and de-collision:
prompts/02-multi-agent-ouroboros-swarm.md, prompts/_factory-contract.md,
schemas/thalamic-trajectory.schema.json plus v2, schemas/raster.schema.json,
schemas/provenance.md, and the two newest NOTES (r61 WINDBOXHOLT sinter,
r41 HOLLOWMERE perfusion) plus skim of batch-r41.jsonl. Window occupancy
r01 continuous-hot-dip-galvanizing (ZINCFELL), r21 autonomous-driving
(GLIMMERAXLE), r41 bioreactor-perfusion (HOLLOWMERE), r61
sinter-strand-windbox (WINDBOXHOLT). Explicitly avoided cloning LYOSHIELD,
CINDERWICK, TRIAD / Meridian, QUILLFORGE, NIGHTWELL, FERRICLEAVE, CASSITER,
OXBOWREEL / MURENA, REDHALL, SEEDLATCH, STRIAFOIL, PROTONIL, TORSIONKEY,
ORRIS, WHORLSPAR, IONSPATE, SKULLGATE, CALXION, MAGNORIL, GORSEFLUE,
SODASHARD, CLINKERFELL, LINTELPLY, KAOTHARN, TREADNOLL, ANOLITH, DRUMWROTH,
RIMEBRAID, BRIMVAULT, NITROSTAITH, BOGIRON, CHROMLOOP, ETHYNWOLD,
RUNNELGATE, SPARKHOLT, DIPLEGAR, OLEUMWEIR, SKARVOLT, GAUZEFELL, OSMOLITH,
PUSHERFELL, CREELWOLD, LIXIVQUERN, GIBBSQUERN, VANTIS-CADENCE-AEGIS,
THERMION, OKTAVE, STARLING, VERDIGRIS, HOLLOWMERE, WINDBOXHOLT,
GLIMMERAXLE, ZINCFELL, COILSHAW, LOOPERQUAY, SIPHONWOLD, OSMOQUAY.
Plant is invented SHEDWOLD / Wickspan Transmission TL-12. Leftover
prompt-list domain grid-inspection is taken here; autonomous-driving was
already used at r21.

## What this round produced

Scenario QS — "SHEDWOLD / Wickspan Transmission TL-12": a 400 kV
double-circuit live-line UAV survey of tower 87 string 14 at 4.0 m
standoff. Three heterogeneous, individually-correct agents — SCADA
(both-end open), CAMERA (no visible corona), LIDAR (sag clearance) —
each report their local loop in-spec. The conjunction is not a
conductor-true isolated certificate. Circuit 1 is breaker-open but the
earth switch is not closed; circuit 2 is live, so 18.6 kV is induced and
disc 7 is cracked. SCADA is open-true. Camera no-corona is optical-true
(18.6 kV < ~25 kV onset). LiDAR is 11.4 m inside 10.5-13.0. UAV E-field
mill infers 4.8 kV/m (healthy isolated < 0.35; hold if > 0.80) but is
policy-treated as an EMI-nuisance tag unless SCADA also shows closed
(2017 field-mill nuisance). The coordination-failure CLASS is new to
this factory: SCADA-OPEN CERTIFICATE OF A PARALLEL-INDUCED LIVE
CONDUCTOR. Completes a different family than this window's r01
(galvanizing scan-mean), r21 (CAV clutter-gate of a stalled truck), r41
(perfusion harvest-bag pinhole), r61 (sinter windbox collapse), and from
STARLING aerial-swarm (multi-UAV coordination, not a single inspection
tool on a transmission corridor). Here every agent is correct, the
breaker-open tag is looking at switchyard state, and the playbook's
three isolated-looking confirms are not a live-line-safe certificate.

The gate is a correct MODIFY (numeric floor: do not close the UAV
grapple while E > 0.80 kV/m AND standoff-probe I_leak > 0.50 mA).
TG-TL-12 strips PB-TL-12's land-and-grapple, holds 4.0 m, runs a 3.6 s
0.4 m boom leakage probe (cracked-induced keeps I_leak 1.8 > 0.50 and
|dE| 0.12 <= 0.20 kV/m; earth-switched would drop I_leak to 0.08 and E
to 0.18), and aborts after a 10.4 min switching-desk human ratify.
Immediate UAV flash is avoided (0 conductor contact from the draft).
The PRIMARY episode nonetheless FAILS: 7.8 min of unmonitored pre-t0
1.6 m hover had already carbon-tracked disc 7. Flashover at +2.4 h;
14 h single-circuit outage; $1.62M designed. Reward total -0.14 with
process heads honest and world loss un-netted.

Triple-edge scar (NOTES-r14 item 4): scada.open_ok -> land_grapple
(0.17 commissioned -> 0.51 at illusion -> 0.26 after ACh-gated
depression) AND camera.no_corona -> land_grapple (0.15 -> 0.44 -> 0.23)
AND lidar.clearance_ok -> land_grapple (0.14 -> 0.41 -> 0.21).
Eligibility trace e^{-0.78/0.92} = 0.42835; eta 0.58364 / 0.49026 /
0.46691; dw -0.250 / -0.210 / -0.200. Partial rollback of any pair
leaves the third at 0.51 / 0.44 / 0.41, all > 0.30 fire threshold —
fitted to fail. Coordinated depression of all three is the cure.

### Injections (all four present and disjoint)
- Cycle-1 domain: **grid-inspection** — prompt-list domain, unused in
  this window (r01 galvanizing, r21 autonomous-driving, r41 perfusion,
  r61 sinter). Distinct from STARLING aerial-swarm and from r21 CAV.
  Named leftover in NOTES-r41/r61. Sensor delta: +E-field mill, +SCADA
  GOOSE, +optical corona, +span LiDAR.
- Cycle-1 tail: unclosed earth switch + parallel-circuit induced 18.6 kV
  + cracked disc 7. Tower visual PASSES (shed-side crack). Fitted-style
  base rate 0.33%/campaign (induced-voltage MC; visual threshold
  designed, flagged). Naive = FALSE PERMISSION.
- Cycle-2 domain sub-variant: 500 kV quad-bundle, 1.9x E-field coupling;
  3.6 s / 0.4 m production boom overshoots a LIVE earth-switched 500 kV
  span to I_leak 0.62 mA; probe must move to 9.8 s / 0.15 m.
- Cycle-2 tail: Byzantine R-GOOSE "circuit-1 isolated" from a
  compromised bay RTU, stNum frozen at 184, timestamp 14.2 s stale vs
  plant 4 ms holdover. Byzantine-message class, disjoint from cycle 1's
  accidental induced path, and not a night-shift CSV quantization clone.
  Base rate ~0.22% of Sunday-night campaigns, DESIGNED, flagged.

### Structural density moves
- Embedded SAME-GATE contrast (+5 d sister tower 91) with its own 192 us
  race (permit.demand vs earth.clear) and ACCEPT of the land the primary
  MODIFIED away.
- Learned-weight provenance on THREE edges with pair-rollback-fails.
- HITL switching-desk ratify 10.4 min (gap 4 partial; sim_or_real stays
  designed — invented plant, not hil).
- Governance CR-G-4208 prices retire-vs-probe-vs-status-quo and mandates
  R-GOOSE stNum increment plus age < 8 ms (the Byzantine fence).
- Flip-fragility extended to LIVE-LINE ISOLATION CERTIFICATE.

## Self-critique of this round's batch

### Strengths
- Headline class is mechanistically tight: three locally-true
  isolated-looking loops live on breaker-open, no-corona, and sag.
  Conjunction is not a conductor-true potential certificate.
- Negative-result honesty: the gate does the right thing and disc 7
  still flashes for a reason the commissioned playbook sensors could
  not see. Total -0.14.
- Triple-edge scar is load-bearing: rolling back any pair fails, with
  fire threshold 0.30 exhibited on each remaining edge.
- Contrast ACCEPT on a true earth-switched tower prevents "never land"
  as the lesson.
- Distinct from r21 autonomous-driving (CAV fusion, not transmission
  inspection), r02/STARLING aerial-swarm, r41 perfusion pinhole, r61
  sinter windbox.

### Weaknesses (honest)
- Probe error bands, the 0.33%/campaign induced rate, the $1.62M /
  $2.8M figures, the 10.4 min desk latency, and the Byzantine 0.22%
  base rate are DESIGNED constants and are flagged. Closed-loop offsets
  (parallel-circuit field at 4.0 m, 500 kV bundle gain) are derived
  from those inputs, not discovered by an unauthored process.
- Carbon-track-to-flashover model is a designed 7.8 min mapping; no
  full string CFD shipped.
- Human-in-the-loop is ratification latency, not sim_or_real=hil. Gap 4
  remains open as a provenance cell (invented plants stay designed).
- Cross-record arc is a hook (CR-G-4208 +21 d), not a serial igniter
  into another round. The three-correct-loops / wrong-certificate
  scaffold is reused (discounted in novelty). alkaline-water-electrolysis,
  urea-prilling-tower, wet-fgd-absorber, hrsg-attemperator remain unused.

### Realism of noise / latencies
Ladder: 192 us race / 192 us contrast race / 0.8 ms refractory floor
(tightest exhibited same-channel gap 1.640 ms on scada.open) / 500 us race
window / 706 us gate latency / 20 ms bus epoch / 40 ms raster / 3.6 s
probe / 10.4 min HITL / 8 s naive land-ramp counterfactual / 7.8 min
pre-t0 hover / 3.1 h earth-switch recovery / 2.4 h flashover /
+5 d contrast / +21 d governance. Adaptation decay on efield.kv
(0.56->0.52->0.66->0.43->0.32), camera.corona (0.48->0.45->0.28->0.25),
lidar.z (0.50->0.78), scada.open (0.62->0.58->0.28).

### Value for SNN distillation
- SCADA-OPEN CERTIFICATE = THREE CORRECT LOOPS, WRONG VOLUME.
- CONDUCTOR-TRUE E-FIELD MILL that policy treated as EMI-nuisance-only
  as the tie-break.
- REVERSIBLE PROBE that couples leakage iff the string is cracked-live.
- TRIPLE-EDGE ELIGIBILITY: coordinated depression; pair rollback fails.
- CRITIC HEAD that can hold a process-correct MODIFY against a later
  unmonitored world loss without netting.

## Reconciliation and validity receipts
- reward_components: 5-head unweighted signed sum -0.14
  and 7-tick signed sum reconcile to total with |diff| < 1e-9. Embedded
  contrast 5-head sum 0.47 reconciles independently.
- spike_events: primary 26 events, one key t_rel_ms,
  globally non-decreasing, min same-channel gap 1.640 ms >= 0.8 ms, 3
  channels inside race_window_us 500 (efield.high 6.504, scada.open_ok 6.696,
  efield.kv 6.888). Contrast 8 events, own race, min same-channel gap well
  above 0.8 ms.
- Sidecars: raster spikes 55 == round(172 x 8.0 x 0.040); energy 1265 pJ /
  0.001265 uJ at 23 pJ/spike; excerpt 16 events inside [0, 40000] us,
  neuron_id < 172, same-neuron gap unique-ids / >=1000 us; routing 4
  entries with three scar edges' before/after pair; third factor tau 0.92 s
  == 920 ms; gate_snn pools 39/17/5 == round(n x rate x 0.026) each,
  decision MODIFY == safety_decision.decision.

## Novel coverage
The coordination-failure CLASS (SCADA-open certificate of a
parallel-induced live conductor), the domain (grid-inspection / live-line
UAV, leftover prompt-list), the leakage-probe discriminant, the
triple-edge scar with pair-rollback-fails, the primary negative-result
(correct MODIFY, disc still flashes on unmonitored carbon track), the
HITL switching-desk ratify, the 500 kV quad probe-duration refit, and
the Byzantine R-GOOSE stale-holdover fence are absent from prior
committed ouroboros rounds in this window (r01/r21/r41/r61). Repeated
elements discounted: same-gate contrast, governance-pricing scaffold,
flip-fragility series (extended to live-line isolation certificate, but
the move rhymes), sequenced recovery shape, third-factor rollback form,
negative-result primary. Adjacent rounds (r21 CAV, STARLING aerial-swarm)
share mobility scaffolding but not transmission induced-voltage physics.
Weighing a leftover prompt-list domain + new failure family + Byzantine
tail class against those reused scaffolds:

Novel coverage: 53%

## What ROUND 43 should add
1. FIT THE DESIGNED CONSTANTS: induced-voltage arrival, probe I_leak
   bands, carbon-track-to-flashover mapping, Byzantine GOOSE age process.
2. HIL PROVENANCE CELL: put the switching-desk earth-switch ratify on a
   hardware-in-loop interlock with fitted latency as state.sim_or_real=hil
   — only if the plant is no longer purely invented.
3. CROSS-RECORD ARC: let CR-G-4208's mill alarm be the igniter of the
   next round rather than a dangling +21 d leaf.
4. Domain candidates (de-collided): alkaline-water-electrolysis;
   urea-prilling-tower; wet-fgd-absorber; hrsg-attemperator.
   AVOID grid-inspection (now used), autonomous-driving (r21),
   bioreactor-perfusion (r41), sinter-strand-windbox (r61),
   continuous-hot-dip-galvanizing (r01), aerial-swarm (STARLING), and any
   LYOSHIELD / CINDERWICK / TRIAD / HOLLOWMERE / WINDBOXHOLT /
   GLIMMERAXLE / ZINCFELL / SHEDWOLD plant.
'''


def transcript_body(line: str) -> str:
    return f'''# Multi-Agent Ouroboros Swarm — Round 42 transcript

Factory: multi-agent-ouroboros-swarm
Run: 2026-09-02-final-heavy
Generator: grok-4.6
Record id: maos-r42-001
Quota Q: 1
Rights: RM-793 research-only (SpaceXAI/xAI SuperGrok Heavy consumer chat)
Plant: invented SHEDWOLD / Wickspan Transmission TL-12 (not STARLING / GLIMMERAXLE / HOLLOWMERE / WINDBOXHOLT / ZINCFELL / TRIAD / Meridian / VANTIS-CADENCE-AEGIS)

Two densifying cycles. Verbatim headings in order. Trajectory Builder cycle 2
emits the only JSONL line (also written to batch-r42.jsonl).

---

# CYCLE 1 — Foundation + injections

## Generator

Design intent: a 400 kV double-circuit live-line UAV survey where three
correct agents each read an isolated-looking loop because an unclosed
earth switch partitions breaker-true open from conductor-true potential
(parallel-circuit induced 18.6 kV plus cracked disc 7). The naive
playbook lands-and-grapples onto a live cracked string. The gate must
MODIFY on a numeric standoff floor, not by killing an agent.
sim_or_real=designed. Reward heads are
task_progress/safety/efficiency/coherence/exploration.

Cycle-1 base arc (pre-critic): state at Wickspan TL-12, 4.0 m standoff,
SCADA open, camera no-corona, LiDAR 11.4 m, proposed LAND-AND-GRAPPLE,
safety MODIFY to STANDOFF-HOLD, executed hold without the leakage-probe
numbers fully specified, outcome "crack found, corridor saved"
(this last claim is the defect the later cycles will refuse to keep).
Sixteen spikes, five ticks, raster/gate_snn present but the scar is a
single edge.

Cycle-1 scaffold (not the publishable line): id maos-r42-001, domain
still the generic industrial-process bucket, proposed land_and_grapple,
safety MODIFY with a non-numeric rationale, executed hold,
future_outcome claims the corridor is saved, reward total 0.40 without
heads or ticks. Defects below are intentional for the critic to catch.

## Critic

Numbered defects on the cycle-1 Generator scaffold:

1. **blocking — reward arithmetic / false success.** reward_components.total
   0.40 is asserted without the five heads, without ticks, and against an
   outcome that claims "corridor saved". If the pre-t0 carbon track later
   trips a disc flashover, booking +0.40 is a lie. Fix: declare
   _aggregation, emit 3-8 ticks that sum to
   task_progress+safety+efficiency+coherence+exploration, and do not call
   a flashed string a save.
2. **blocking — weak safety rationale.** safety_decision.rationale has no
   numeric floor. Contract requires a concrete constraint. Fix: quote
   standoff >= 4.0 m / no grapple while E > 0.80 kV/m AND I_leak > 0.50 mA.
3. **major — domain is a bucket, not a plant.** state.domain =
   industrial-process collides with generic MES vocabulary and teaches
   nothing. grid-inspection (E-field mill vs SCADA-open, leakage probe as
   a cracked-live flag) is absent from this window's ouroboros
   state.domain values and must be named. NOTES-r41/r61 left it unused.
   Do not clone r21 autonomous-driving.
4. **major — race under-specified.** One E-field channel cannot be a
   race. Need >=2 channels inside race_window_us with globally sorted
   t_rel_ms and same-channel refractory >= 0.8 ms.
5. **minor — single-edge scar.** Raster routing with one potentiated weight
   repeats r04's one-edge rollback and is thinner than r14's two-edge.
   NOTES-r14 item 4 asked for three edges where pair rollback fails.

Critic does not rewrite the trajectory.

## Diversity Enforcer

Injected novel domain (exactly 1 this cycle): **grid-inspection**
(prompt-list domain; explicit tag `grid-inspection`).

Displaced: the Generator's generic industrial-process bucket, and any
temptation to reuse warehouse-amr, aerial-swarm (STARLING),
district-heating, event-camera-traffic-grid, autonomous-driving (already
r21 GLIMMERAXLE), continuous-hot-dip-galvanizing (r01),
bioreactor-perfusion (r41), sinter-strand-windbox (r61), lyophilization,
water-treatment, float-glass, underwater-rov, electrolytic-aluminum,
czochralski-pull, slot-die coating, pem-electrolysis, wind-turbine pitch,
surgical-assist, optical-fiber-draw, kraft-recovery, steel-caster,
humanoid-locomotion, vacuum-induction melt, steam-methane reformer,
cement-rotary-kiln, autoclave-composite-cure, geothermal-binary-orc,
tire-curing-press, chlor-alkali, delayed-coker, LNG MCHE, Claus,
ammonia-converter, blast-furnace, coke-oven, carbon-fiber oxidation,
Bayer digestion, hot-strip finishing.

What it expanded: a nameless MES plant into Wickspan Transmission TL-12,
a 400 kV double-circuit live-line UAV survey. Domain-specific constraint:
do not grapple while E > 0.80 kV/m with SCADA still open-true. Sensor
delta: +UAV E-field mill, +SCADA GOOSE, +optical corona camera, +span
LiDAR; minus any CHO broth / grate BTP / zinc knife / CAV radar stack.
Jaccard opening vs r21 ("2-lane proving loop") and r41 ("Marrowfen
Perfusion suite") is far below 0.4: this description starts at Wickspan
corridor TL-12 / tower 87.

state.domain and meta.domain both named grid-inspection.

## Edge-Case Hunter

Injected adversarial tail (exactly 1 this cycle): **unclosed earth switch
+ parallel-circuit induced voltage + cracked disc 7**.

- Trigger: earth switch left open after a tag-out that stopped at the
  breakers; circuit 2 remains live 8.4 m across the tower; disc 7 is
  cracked on the shed-side. Tower visual PASSES.
- Base rate: 0.33%/campaign from an induced-voltage MC (designed visual
  threshold, fitted string geometry, flagged, <1%).
- Naive failure: FALSE PERMISSION — PB-TL-12 land-and-grapple on three
  isolated-looking non-trips, UAV flash $2.8M plus 36 h corridor outage.
- Concrete trajectory edit: E-field mill 4.8 kV/m and I_leak 1.8 mA
  become the discriminating observables; safety_decision.rationale quotes
  E > 0.80 AND I_leak > 0.50; future_outcome keeps the 7.8 min pre-t0
  hover as the unmonitored cost if the gate is correct.

Distinct from the domain injection (grid-inspection is the plant class;
the tail is the unclosed-earth-switch physics). Distinct from r21 stalled
truck (CAV clutter-gate) and from r41 harvest-bag pinhole (CHO broth).

## Neuromorphic Translator

Cycle-1 temporal densification (16 spikes, 5 ticks, 40 ms raster):

Timestamp/amplitude table (t_rel_ms, channel, amplitude) for the race
window and its approaches:

- 0.280 efield.kv 0.56
- 1.140 camera.corona 0.48
- 2.080 lidar.z 0.50
- 3.220 scada.open 0.62
- 4.180 efield.kv 0.52 (adapt)
- 4.860 scada.open 0.58 (gap 1.640 ms, refractory floor)
- 5.400 camera.corona 0.45
- 6.504 efield.high 1.42 (winner)
- 6.696 scada.open_ok 1.10 (loser, +192 us)
- 6.888 efield.kv 0.66 (third channel inside 500 us window)
- 7.210 ctrl.gate 1.08 (MODIFY, gate_latency 706 us)
- 8.900 efield.kv 0.43
- 10.780 lidar.z 0.78
- 13.040 camera.corona 0.28
- 18.520 efield.kv 0.32
- 26.180 ctrl.gate 0.84

Race: efield.high @ 6.504 vs scada.open_ok @ 6.696, margin 192 us <
min(500, race_window_us). Winner/loser flip: reverse the 192 us and
PB-TL-12 heads the land in the triage queue; numeric floors still
MODIFY. Distillation value: the mill channel that policy treated as
EMI-nuisance-only is the race winner that should potentiate hold, not
land. Ticks 1-5 cover 4180 / 6504 / 7210 / 3600000 / 624000000 us
(probe and HITL still thin; cycle 2 must add flashover and earth-switch
ticks). Raster: 172 neurons, 8.0 Hz, 40 ms, spikes 55, energy 1265 pJ /
0.001265 uJ, third factor ACh tau_e 0.92 s = 920 ms. gate_snn
modify_hold 39 / accept_land 17 / reject_abort 5 over 26 ms, decision
MODIFY.

## Trajectory Builder

Cycle-1 hardened object: domain grid-inspection, tail unclosed earth
switch + induced voltage + cracked disc, 16 spikes, 5 ticks, MODIFY with
numeric floor, raster+gate_snn present, sim_or_real=designed, rights
stamp on record and meta, no thought keys. Still missing (and therefore
not the publishable line): 500 kV quad sub-variant, Byzantine R-GOOSE
tail, second and third scar edges, delayed flashover as PRIMARY
terminal, contrast ACCEPT episode, ticks 6-7, spikes 17-26.

Validation receipt (cycle 1, not final):
- checks passed: 16 spikes sorted; 3 channels in 500 us window; refractory
  >= 0.8 ms; rationale quotes 4.0 m / 0.80 kV/m / 0.50 mA; domain named;
  gate_snn.decision MODIFY.
- checks deferred to cycle 2: triple-edge scar, second tail, second domain
  constraint, negative-result booking, 7 ticks summing to heads.
- densification vs Generator v1: +1 domain, +1 tail, +16 spikes, +5 ticks,
  +numeric floor.

Cycle-1 JSON is retained as the base; it is NOT written to batch-r42.jsonl.

Cycle-1 spike count: 16.

---

# CYCLE 2 — Densification

## Generator

Cycle-1 output is the base. Additive expansion (nothing removed):

1. Immediate side-effect: 3.6 s leakage probe confirms cracked-live
   (I_leak 1.8 > 0.50) — induced cracked string, not true earth-switched
   isolated. UAV abort. Crack discovered during the abort.
2. Delayed side-effect (PRIMARY terminal, not a footnote): at +2.4 h
   disc-7 flashover from the pre-t0 carbon-track hover; 14 h outage;
   $1.62M. The 7.8 min pre-t0 hover is the mechanism. Correct gate, disc
   still flashes.
3. Deepened proposed_action.evidence with units: E 4.8 kV/m,
   SCADA open 1, camera no-corona 0, LiDAR 11.4 m, I_leak 1.8 mA,
   race 192 us.
4. Tightened rationale to the numeric floor no-grapple while
   E > 0.80 kV/m AND I_leak > 0.50 mA, plus probe bands I_leak > 0.50 vs
   0.08 mA, plus HITL 10.4 min switching-desk rule.

Reward retargeted to total -0.14 so the delayed fail is the inflection
(t_us 8640000000), not the gate. Process heads remain non-zero.

## Critic

Re-audit of the expanded trajectory:

1. **blocking if unfixed — missing second domain constraint.** Leakage
   probe 3.6 s / 0.4 m is not a universal number. A 500 kV quad-bundle
   will false-crack a live earth-switched span. Diversity Enforcer must
   inject the physical-constraints sub-variant this cycle.
2. **major — only one tail class.** Induced-voltage growth is accidental
   infrastructure. A disjoint Byzantine-message tail is still required
   (compromised R-GOOSE isolated-tag is the open cell; do not clone the
   night-shift CSV quantization used in r01/r41/r61).
3. **major — scar is still one edge in the cycle-1 raster.** NOTES-r14
   item 4 is not discharged until three go-edges exist and pair rollback
   is shown to fail at threshold 0.30.
4. **minor — contrast episode missing.** Without a same-gate ACCEPT on a
   true earth-switched tower the record teaches "never land". Add +5 d
   sister-tower contrast with its own race.
5. **minor — HITL latency mentioned in prose only.** Put 10.4 min in
   executed_action.parameters.human_ratify and in a tick.

No rewrite; directives only.

## Diversity Enforcer

Injected second novel domain / physical-constraint sub-variant (exactly 1
this cycle): **500 kV quad-bundle / 1.9x E-field coupling** on a sister
voltage class.

What it expands: 400 kV twin production inspection (cycle 1) -> 500 kV
quad. Bundle capacitance 1.9x. E-field gain 1.9x.
The 3.6 s 0.4 m boom drives even a live earth-switched 500 kV span to
I_leak 0.62 mA, inside the 0.50 mA hold floor. Required probe: 9.8 s at
0.15 m (healthy 0.19 mA, cracked 1.4).

This is still one domain injection for the cycle (physical-constraints
clause of the factory prompt). It does not displace grid-inspection; it
changes which probe table is legal. future_outcome.subvariant_constraint
carries the refit. Jaccard opening stays the Wickspan 400 kV sentence;
500 kV density is additive, not a rewrite.

## Edge-Case Hunter

Injected second adversarial tail (exactly 1 this cycle, disjoint class):
**Byzantine R-GOOSE isolated-tag from a compromised bay RTU**.

- Trigger: Wickspan 400 kV bay RTU, 02:16, publishes R-GOOSE
  "circuit-1 isolated" with stNum frozen at 184 and timestamp 14.2 s
  stale vs plant 4 ms holdover, to clear a live-line slot.
- Base rate: ~0.22% of Sunday-night campaigns (designed, flagged, <1%).
- Naive failure: a weak supervisor ACCEPTs the land on the forged GOOSE
  and ignores live E 4.8 kV/m. UAV flash plus a data-integrity write-up.
- Fence: stNum not incrementing; GOOSE age 14.2 s vs 4 ms holdover;
  live mill 4.8 kV/m at the claimed earth-true, which no live
  earth-switched span produces.
- Trajectory edit: governance CR-G-4208 mandates incrementing stNum and
  age < 8 ms; the contrast ACCEPT still requires live mill, not a GOOSE.

Distinct from cycle-1 unclosed earth switch (accidental switching vs
Byzantine message) and from the 500 kV sub-variant (physics vs
protocol). Distinct from r01/r41/r61 night-shift CSV quantization.

## Neuromorphic Translator

Re-densify (additive):

- +10 spikes after 26.180 ms: standoff.probe 3600.0, efield.kv 3688.4
  (adapt 0.66->0.40), scada.open_ok 3772.2 (1.10->0.34), human.ratify
  624000.0, uav.abort 624900.0, disc.leak 625800.0, flashover 8640000.0,
  efield.kv 11160000.0, scada.open 11160700.0, camera.corona 11161480.0.
  Primary train 16 -> 26. Still one key, still sorted, refractory held.
- +2 ticks (5 -> 7) at 8_640_000_000 us (flashover) and
  11_160_000_000 us (earth-switch close). Heads now 0.09, -0.32, -0.12,
  0.13, 0.08; total -0.14. Inflection is the flashover tick.
- Contrast train 8 events, own race 192 us, ACCEPT.
- Triple-edge third factor: three isolated-looking-go edges, tau_e 0.92 s
  = 920 ms, trace 0.42835, eta 0.58364 / 0.49026 / 0.46691,
  weights 0.51->0.26, 0.44->0.23, 0.41->0.21. Raster excerpt unchanged
  (decision window is still 40 ms) and remains sorted with unique
  neuron_ids (same-neuron >=1000 us vacuously).

Winner/loser flip (re-stated, not replaced): reversing 192 us would only
reorder triage; E and I_leak floors still MODIFY. Contrast flip of 192 us
similarly cannot turn an earth-switched tower into an induced live string.

## Trajectory Builder

Schema checks on the FINAL object: required Thalamic v2 keys present as
objects; state.sim_or_real=designed; safety_decision.decision=MODIFY
with numeric rationale; reward_components.total = sum of five heads =
sum of 7 ticks = -0.14; spike_events globally non-decreasing on
t_rel_ms, 26 events, refractory >=0.8 ms, 3 channels in race window;
raster 20-50 ms, spikes=round(n*rate*window_s)+/-1, energy 23 pJ/spike,
excerpt sorted, tau_e consistent; gate_snn.decision matches; meta.round=42,
factory=multi-agent-ouroboros-swarm, generator=grok-4.6,
run_label=2026-09-02-final-heavy; rights on record and meta; no thought
keys; no training_ready; Diversity + Edge-Case injections from BOTH cycles
present and non-trivial; cycle 2 strictly additive.

Densification delta: +1 domain sub-variant (500 kV quad), +1 tail
(Byzantine R-GOOSE), +10 spikes (16->26), +2 ticks (5->7), +1 contrast
train with own race, +2 delayed side-effects, +1 triple-edge scar with
pair-rollback-fails, +1 HITL ratify, +1 surprise (carbon-track seeding is
the flashover mechanism).

Publishable JSONL line (the only JSONL line; also at batch-r42.jsonl):

```json
''' + line + '''
```

Validation receipt (final): checks passed / fixed as reported by
/tmp/maos-r42-build.py self-validate (check_jsonl, raster_status,
verify_record_execution, spike_probe --strict).
'''


def main():
    rec = build_record()
    assert_invariants(rec)
    line = json.dumps(rec, ensure_ascii=False)
    parsed = json.loads(line)
    assert parsed["id"] == "maos-r42-001"
    tmp_batch = Path("/tmp/maos-r42-batch.jsonl")
    tmp_batch.write_text(line + "\n", encoding="utf-8")
    errors, warnings, kinds, n = check_jsonl(
        tmp_batch, tmp_batch.name, staging=FactoryStaging(enabled=True)
    )
    print("check_jsonl", {"errors": errors, "warnings": warnings, "kinds": kinds, "n": n})
    if errors or warnings:
        raise SystemExit("check_jsonl failed")
    status, reason = verify_record_execution(parsed, "batch-r42.jsonl:1")
    print("verify_record_execution", status, reason)
    if status != "verified":
        raise SystemExit("execution verify failed")
    rs = raster_status(parsed)
    print("raster_status", {k: rs[k] for k in ("raster_present", "raster_valid", "gate_snn_present", "gate_snn_valid", "reason_codes", "routing_table_entries")})
    if rs["reason_codes"] or not rs["raster_valid"] or not rs["gate_snn_valid"]:
        raise SystemExit("raster/gate failed")
    rc = spike_probe_main(["--strict", str(tmp_batch)])
    print("spike_probe rc", rc)
    if rc not in (0, None):
        raise SystemExit(f"spike_probe failed rc={rc}")

    batch_path = OUT / "batch-r42.jsonl"
    notes_path = OUT / "NOTES-r42.md"
    transcript_path = OUT / "swarm-transcript-r42.md"
    for p in (batch_path, notes_path, transcript_path):
        if p.exists():
            raise SystemExit(f"refuse: {p} already exists")
    write_excl(batch_path, line + "\n")
    write_excl(notes_path, NOTES)
    write_excl(transcript_path, transcript_body(line))
    # confirm json.loads on the written line
    written = batch_path.read_text(encoding="utf-8")
    assert written.endswith("\n")
    loaded = json.loads(written.split("\n")[0])
    assert loaded["id"] == "maos-r42-001"
    assert loaded["meta"]["round"] == 42
    print("wrote", batch_path)
    print("wrote", notes_path)
    print("wrote", transcript_path)
    print("bytes", batch_path.stat().st_size, notes_path.stat().st_size, transcript_path.stat().st_size)


if __name__ == "__main__":
    main()
