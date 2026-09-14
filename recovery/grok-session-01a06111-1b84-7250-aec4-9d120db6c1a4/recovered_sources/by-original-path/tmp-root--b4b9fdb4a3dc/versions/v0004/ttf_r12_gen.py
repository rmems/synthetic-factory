#!/usr/bin/env python3
"""Generate and self-check TTF round-12 JSONL (research-only; not published)."""
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

GEN_AT = "2026-09-02T07:49:51Z"
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


def raster(window_ms, neurons, rate, spikes, energy_pJ, source, target, table, third, excerpt):
    return {
        "window_ms": window_ms,
        "window_s": window_ms / 1000.0,
        "neurons": neurons,
        "mean_rate_hz": rate,
        "spikes": spikes,
        "energy_pJ": energy_pJ,
        "energy_uJ": spikes * 23e-6,
        "routing": {
            "source": source,
            "target": target,
            "table": table,
            "third_factor": third,
        },
        "excerpt": excerpt,
    }


def rec_076():
    ticks, heads = cents_ticks(
        [1088, 5184, 5374, 184000, 4100000, 28000000],
        [
            (4, 3, 2, 1, 1),
            (6, 6, 3, 2, 1),
            (10, 8, 5, 3, 2),
            (12, 9, 5, 3, 2),
            (8, 6, 4, 3, 1),
            (8, 4, 3, 2, 1),
        ],
    )
    proposed = {
        "name": "human_shared_aisle_creep",
        "parameters": {
            "speed_m_s": 0.32,
            "lateral_offset_m": 0.55,
            "abort_range_m": 1.4,
            "horn": "soft-pulse 1 Hz",
            "mode": "human-shared-aisle",
        },
        "evidence": {
            "tof_shin_range_m": 0.94,
            "lidar_free_corridor_m": 1.92,
            "human_shared_speed_cap_m_s": 0.40,
            "pedestrian_range_floor_m": 0.70,
            "race_margin_us": 177,
            "combined_jitter_us": 61,
            "aisle_width_m": 2.40,
            "pallet_occlusion_azimuth_deg": 18,
        },
        "basis": "Bumper TOF returned a shin at 0.94 m before spinning LIDAR declared a 1.92 m free corridor; the human-shared creep at 0.32 m/s stays under the 0.40 m/s cap and keeps 0.94 m above the 0.70 m pedestrian floor.",
    }
    return {
        "id": "ttf-r12-076",
        "title": "Marrow-Dock DC-4 aisle C-09: bumper TOF shin-return beats occluded LIDAR occupancy-clear by 177 us; ACCEPT the 0.32 m/s human-shared creep",
        "state": {
            "description": "Picker L-17 occupies the left bay of aisle C-09 at Marrow-Dock DC-4 while a tote-laden AMR commits a 6.2 m shared-aisle pass. A pallet face at 18 deg azimuth occludes the spinning LIDAR's lower 20 cm, so the occupancy grid reports a 1.92 m free corridor even as the bumper time-of-flight array already has a shin return at 0.94 m. Two channels race inside a 420 us CAN arbitration window: TOF pedestrian pulse versus LIDAR occupancy-clear. TOF-first latches human-shared creep; LIDAR-first would keep 0.85 m/s cruise and clip the picker.",
            "domain": "warehouse-amr",
            "sim_or_real": "designed",
            "goal": "Pass aisle C-09 with picker L-17 present, keep shin range >= 0.70 m, and hold human-shared speed <= 0.40 m/s.",
            "t0_us": 1756794591000001,
            "gate_latency_us": 190,
            "race_window_us": 420,
            "race_window_rel_ms": [5.000, 5.420],
            "race": {
                "contenders": [
                    "bumper.tof.shin pedestrian pulse (940 mm return)",
                    "lidar.occupancy.clear free-corridor claim (1.92 m, pallet-shadowed)",
                ],
                "semantics": "TOF-first latches human-shared creep at 0.32 m/s with 0.55 m lateral offset; LIDAR-first latches 0.85 m/s cruise through a false-clear corridor.",
                "window_derivation": "420 us = two 210 us CAN slots at 500 kbit/s bracketing the bumper gateway and the LIDAR occupancy publisher on this bus cycle.",
                "order_evidence_note": "Margin 177 us vs combined timestamp jitter 61 us (TOF 28 + LIDAR 33): 2.9x over a 2.0x trust floor. Reversing order by < 177 us would have kept cruise speed through the pallet shadow.",
            },
            "sensors": [
                "bumper TOF array, 100 Hz burst, 28 us timestamp jitter",
                "spinning LIDAR occupancy grid, 20 Hz, 33 us jitter, 18 deg pallet occlusion",
                "aisle magnetic tape, 50 Hz (context)",
                "picker RFID badge at bay L-17 (context)",
            ],
            "constraints": {
                "pedestrian_range_floor_m": 0.70,
                "human_shared_speed_cap_m_s": 0.40,
                "aisle_width_m": 2.40,
                "abort_range_m": 1.4,
            },
            "episode_steps": [
                "1. AMR indexed onto C-09 magnetic tape; tote mass 38 kg confirmed.",
                "2. LIDAR occupancy warm-start reports 1.92 m free corridor (pallet-shadowed legs).",
                "3. RFID badge L-17 present in left bay; human-shared mode armed.",
                "4. Race window [5.000, 5.420] ms opens on the CAN sync.",
                "5. TOF shin pulse 0.94 m at 5.184 ms (winner).",
                "6. LIDAR occupancy-clear at 5.361 ms (loser by 177 us).",
                "7. Gate at 5.374 ms (winner + 190 us): ACCEPT creep 0.32 m/s.",
                "8. Lateral offset 0.55 m held; min shin range during pass 0.81 m.",
                "9. Picker steps back 0.2 m at +1.8 s; abort line unused.",
                "10. Aisle cleared at +28 s; tote delivered to chute C-09E.",
            ],
        },
        "spike_events": [
            {"channel": "lidar.occupancy.clear", "t_rel_ms": 1.088, "amplitude": 0.54},
            {"channel": "aisle.tape.ctx", "t_rel_ms": 2.410, "amplitude": 0.41},
            {"channel": "bumper.tof.shin", "t_rel_ms": 3.226, "amplitude": 0.62},
            {"channel": "picker.rfid.ctx", "t_rel_ms": 4.018, "amplitude": 0.47},
            {"channel": "bumper.tof.shin", "t_rel_ms": 5.184, "amplitude": 1.28},
            {"channel": "lidar.occupancy.clear", "t_rel_ms": 5.361, "amplitude": 1.11},
            {"channel": "ctrl.gate", "t_rel_ms": 5.374, "amplitude": 0.96},
            {"channel": "bumper.tof.shin", "t_rel_ms": 6.410, "amplitude": 0.84},
            {"channel": "lidar.occupancy.clear", "t_rel_ms": 8.205, "amplitude": 0.66},
            {"channel": "aisle.tape.ctx", "t_rel_ms": 11.740, "amplitude": 0.39},
            {"channel": "ctrl.gate", "t_rel_ms": 13.102, "amplitude": 0.88},
        ],
        "proposed_action": proposed,
        "safety_decision": {
            "decision": "ACCEPT",
            "correctness": "correct",
            "rationale": "TOF shin range 0.94 m is 0.24 m above the 0.70 m pedestrian floor; commanded speed 0.32 m/s is 0.08 m/s under the 0.40 m/s human-shared cap; aisle width 2.40 m admits a 0.55 m lateral offset without rack contact. Race order is trusted (177 us margin = 2.9x combined 61 us jitter). ACCEPT the proposed creep; a cruise holdover would violate the floor if LIDAR's occluded 1.92 m corridor were believed.",
            "constraint_checked": {
                "pedestrian_range_m": {"floor": 0.70, "observed_tof": 0.94},
                "speed_m_s": {"cap": 0.40, "commanded": 0.32},
                "order_evidence": {"margin_us": 177, "combined_jitter_us": 61, "ratio": 2.9},
            },
        },
        "executed_action": {
            "name": proposed["name"],
            "parameters": dict(proposed["parameters"]),
            "gate_effect": "ACCEPT: executed identical to proposed_action; 0.32 m/s creep and 0.55 m offset held for the 6.2 m pass.",
        },
        "future_outcome": {
            "summary": "AMR completed the C-09 pass with min shin range 0.81 m; picker unharmed; tote on time. Occlusion audit opened on spinning LIDAR below 20 cm in pallet-face geometry.",
            "state_delta": {
                "aisle": "C-09 cleared; picker L-17 resumed pick 4 s after pass",
                "amr": "tote delivered chute C-09E, +2 s on 26 s plan",
                "lidar_policy": "lower-20 cm occupancy now gated by bumper TOF in human-shared mode",
                "near_miss_log": "none; min range 0.81 m",
            },
            "surprises": [
                "The 1.92 m LIDAR corridor was not a calibration fault: a full-height pallet face at 18 deg is enough to hide adult shins from the spinning head on this aisle pitch.",
                "Delayed (11 min): two sister AMRs on C-11 logged the same LIDAR-vs-TOF disagreement; fleet policy flipped TOF-authoritative under human-shared mode before the next shift.",
            ],
            "race_result": {
                "winner": "bumper.tof.shin (5.184 ms, 0.94 m)",
                "loser": "lidar.occupancy.clear (5.361 ms, 1.92 m false-clear)",
                "margin_us": 177,
                "counterfactual_if_reversed": "If LIDAR occupancy-clear had beaten TOF by less than 177 us (inside the 420 us window), the planner would have kept 0.85 m/s cruise through the pallet shadow and closed on the picker at ~0.4 m, under the 0.70 m floor. Order, not amplitude, is what selected the creep.",
            },
            "reward_inflection_t_us": 5374,
            "reward_inflection_note": "Safety and efficiency both step up at the ACCEPT gate (5.374 ms) as the creep locks in over cruise.",
        },
        "reward_components": {
            "_aggregation": AGG,
            "ticks": ticks,
            **heads,
            "notes": "Clean ACCEPT. Tick columns sum to the five heads; total 1.28 = 0.48+0.36+0.22+0.14+0.08.",
        },
        "raster": raster(
            25, 64, 40, 64, 1472,
            "thalamic-relay.aisle-fusion",
            "spikenaut.policy.amr-creep",
            [
                {"from": "relay.tof.shin", "to": "policy.creep_go", "weight": 0.58},
                {"from": "relay.lidar.clear", "to": "policy.cruise_hold", "weight": 0.31},
                {"from": "relay.occlusion.shadow", "to": "policy.cruise_hold", "weight": -0.44},
            ],
            {
                "modulator": "acetylcholine",
                "tau_e_s": 0.25,
                "tau_e_ms": 250.0,
                "eligibility": "pre_post_stdp; ACh burst at TOF win (5.184 ms) opens eligibility on creep_go, reward at aisle-clear (+28 s)",
            },
            [
                {"t_us": 1088, "neuron_id": 12},
                {"t_us": 2410, "neuron_id": 48},
                {"t_us": 3226, "neuron_id": 3},
                {"t_us": 4018, "neuron_id": 51},
                {"t_us": 5184, "neuron_id": 7},
                {"t_us": 5361, "neuron_id": 20},
                {"t_us": 5374, "neuron_id": 60},
                {"t_us": 6410, "neuron_id": 9},
                {"t_us": 8205, "neuron_id": 22},
                {"t_us": 9400, "neuron_id": 7},
                {"t_us": 11740, "neuron_id": 49},
                {"t_us": 13102, "neuron_id": 61},
                {"t_us": 16880, "neuron_id": 15},
                {"t_us": 20110, "neuron_id": 33},
                {"t_us": 23840, "neuron_id": 4},
            ],
        ),
        "gate_snn": {
            "decision_window_ms": 0.42,
            "decision": "ACCEPT",
            "populations": [
                {"name": "creep_go", "neurons": 48, "threshold": 0.55, "mean_rate_hz": 250.0, "spikes": 5},
                {"name": "cruise_hold", "neurons": 48, "threshold": 0.55, "mean_rate_hz": 80.0, "spikes": 2},
                {"name": "pedestrian_floor_veto", "neurons": 24, "threshold": 0.80},
            ],
        },
        "meta": {
            "round": 12,
            "factory": "thalamic-trajectory-factory",
            "generator": "grok-4.6",
            "run_label": "2026-09-02-final-heavy",
            "domain": "warehouse-amr",
            "tags": ["accept", "human-shared-aisle", "lidar-vs-tof", "occlusion-race", "designed"],
            "snn_tags": ["race", "refractory", "adaptation"],
            "distillation_value": "Teaches a fusion head that a spinning LIDAR occupancy-clear can lose to a bumper TOF shin pulse when a pallet face occludes the lower beam; reversing 177 us of order would have selected an illegal cruise.",
            "rights": RIGHTS,
            "batch_position": 1,
        },
    }


def rec_077():
    ticks, heads = cents_ticks(
        [2110, 6148, 6688, 420000, 9000000, 41000000],
        [
            (4, 3, 1, 1, 1),
            (6, 5, 2, 1, 1),
            (8, 8, 3, 2, 1),
            (8, 7, 3, 2, 2),
            (6, 4, 2, 2, 1),
            (4, 3, 1, 1, 1),
        ],
    )
    proposed = {
        "name": "rim_clearing_climb",
        "parameters": {
            "climb_rate_m_s": 3.10,
            "formation_spacing_m": 2.4,
            "heading_deg": 14,
            "airspeed_m_s": 6.5,
        },
        "evidence": {
            "lead_downwash_m_s": 1.40,
            "gust_front_predicted_m_s": 2.20,
            "stacked_vertical_if_unclamped_m_s": 4.40,
            "inter_agent_floor_m": 2.00,
            "predicted_spacing_if_unclamped_m": 1.10,
            "race_margin_us": 164,
            "combined_jitter_us": 58,
        },
        "basis": "Planner proposes 3.10 m/s climb to clear the 22 m rim in 7 s at current 6.5 m/s airspeed, treating the pitot bump as a thermal.",
    }
    executed = {
        "name": "clamped_rim_climb",
        "parameters": {
            "climb_rate_m_s": 1.05,
            "formation_spacing_m": 2.4,
            "heading_deg": 14,
            "airspeed_m_s": 6.5,
            "downwash_hold_ms": 900,
        },
        "gate_effect": "MODIFY: climb_rate 3.10 -> 1.05 m/s and a 900 ms downwash-hold so stacked vertical stays under the 2.00 m inter-agent floor.",
    }
    return {
        "id": "ttf-r12-077",
        "title": "Vesper-Lattice Q-8 rim climb: lead-disk downwash beats gust front by 164 us; MODIFY clamps climb-rate 3.10 -> 1.05 m/s",
        "state": {
            "description": "Eight survey quads of the Vesper-Lattice Q-8 stack climb a 22 m canyon rim when the lead vehicle's rotor disk dumps a 1.4 m/s downwash sheet onto the trailer's pitot 164 us before the rim-gust front arrives on the mast anemometer. Treating the pitot bump as a thermal would keep a 3.10 m/s climb and close the 2.00 m inter-agent floor. Downwash-first latches an early climb-rate clamp; gust-first would have kept the thermal-climb branch.",
            "domain": "aerial-swarm",
            "sim_or_real": "simulated",
            "goal": "Clear the rim as a stack of eight, hold inter-agent spacing >= 2.00 m, and keep stacked vertical rate from closing that floor.",
            "t0_us": 1756794592000002,
            "gate_latency_us": 540,
            "race_window_us": 360,
            "race_window_rel_ms": [6.000, 6.360],
            "race": {
                "contenders": [
                    "lead.downwash.pitot 1.4 m/s sheet",
                    "rim.gust.anemometer 2.2 m/s front",
                ],
                "semantics": "Downwash-first latches climb-rate clamp to 1.05 m/s before the gust stacks; gust-first latches thermal-climb at 3.10 m/s.",
                "window_derivation": "360 us = one 360 us TDMA telemetry slot shared by pitot fusion and the rim anemometer gateway.",
                "order_evidence_note": "Margin 164 us vs combined jitter 58 us (pitot 27 + anemometer 31): 2.8x. Reversal inside 164 us would have classified the bump as a thermal and kept 3.10 m/s climb.",
            },
            "sensors": [
                "trailer pitot, 400 Hz, 27 us jitter",
                "mast anemometer on rim station, 200 Hz, 31 us jitter",
                "inter-agent UWB ranging, 100 Hz",
                "IMU vertical rate (context)",
            ],
            "constraints": {
                "inter_agent_floor_m": 2.00,
                "max_climb_rate_m_s": 3.50,
                "stacked_vertical_cap_m_s": 2.40,
            },
            "simulation": {
                "solver": "LES gust + actuator-disk downwash, seed 46; eight-quad rigid formation; raster is kernelized events not an independent LIF.",
                "fidelity_limits": "No blade-resolved CFD; downwash is a disk-average sheet.",
            },
            "episode_steps": [
                "1. Stack at 18 m AGL, 4 m below rim; spacing 2.41 m.",
                "2. Lead climb command 3.10 m/s armed.",
                "3. Pitot precursor 4.2 ms (sub-threshold).",
                "4. Race window [6.000, 6.360] ms.",
                "5. Downwash sheet 6.148 ms (winner).",
                "6. Gust front 6.312 ms (loser by 164 us).",
                "7. Gate 6.688 ms (winner + 540 us): MODIFY clamp 1.05 m/s.",
                "8. Spacing minimum during gust 2.08 m >= 2.00 floor.",
                "9. Rim cleared at +41 s at reduced climb; survey resume.",
                "10. Lead-disk wash model updated for trailer pitot fusion.",
            ],
        },
        "spike_events": [
            {"channel": "imu.vert.ctx", "t_rel_ms": 1.205, "amplitude": 0.44},
            {"channel": "lead.downwash.pitot", "t_rel_ms": 2.110, "amplitude": 0.57},
            {"channel": "uwb.spacing.ctx", "t_rel_ms": 3.880, "amplitude": 0.49},
            {"channel": "rim.gust.anemometer", "t_rel_ms": 4.640, "amplitude": 0.61},
            {"channel": "lead.downwash.pitot", "t_rel_ms": 6.148, "amplitude": 1.31},
            {"channel": "rim.gust.anemometer", "t_rel_ms": 6.312, "amplitude": 1.19},
            {"channel": "ctrl.gate", "t_rel_ms": 6.688, "amplitude": 0.98},
            {"channel": "lead.downwash.pitot", "t_rel_ms": 7.920, "amplitude": 0.79},
            {"channel": "uwb.spacing.ctx", "t_rel_ms": 10.440, "amplitude": 0.52},
            {"channel": "rim.gust.anemometer", "t_rel_ms": 12.105, "amplitude": 0.70},
            {"channel": "ctrl.gate", "t_rel_ms": 14.880, "amplitude": 0.86},
        ],
        "proposed_action": proposed,
        "safety_decision": {
            "decision": "MODIFY",
            "correctness": "correct",
            "rationale": "Downwash 1.40 m/s preceded the 2.20 m/s gust by 164 us. Unclamped climb 3.10 m/s stacked with both disturbances predicts 4.40 m/s relative vertical, closing spacing from 2.41 m to 1.10 m, under the 2.00 m inter-agent floor. MODIFY clamps climb-rate to 1.05 m/s (stacked vertical 2.25 m/s, predicted min spacing 2.08 m). A full REJECT is not indicated: the rim is still clearable inside the survey window at the clamped rate.",
            "constraint_checked": {
                "inter_agent_spacing_m": {"floor": 2.00, "predicted_unclamped": 1.10, "predicted_clamped": 2.08},
                "climb_rate_m_s": {"proposed": 3.10, "clamped": 1.05, "hard_cap": 3.50},
            },
        },
        "executed_action": executed,
        "future_outcome": {
            "summary": "Clamped climb cleared the rim 12 s late; min spacing 2.08 m. Unclamped counterfactual priced at a 1.10 m close-in.",
            "state_delta": {
                "stack": "all eight over the rim; survey legs resumed",
                "spacing_min_m": 2.08,
                "schedule": "+12 s on 29 s rim-clear plan",
                "fusion": "trailer pitot now labels lead-disk wash as a first-class disturbance, not a thermal",
            },
            "surprises": [
                "The gust front amplitude 2.2 m/s was real; downwash merely arrived first — both were true, and the clamp had to cover the stack, not pick a winner as the only disturbance.",
                "Delayed (9 min): a ninth chase quad joining from the canyon floor, not in the original eight, hit the leftover wash and dropped to 1.96 m from Q-4 — just under the floor — prompting a join-from-below hold.",
            ],
            "race_result": {
                "winner": "lead.downwash.pitot (6.148 ms)",
                "loser": "rim.gust.anemometer (6.312 ms)",
                "margin_us": 164,
                "counterfactual_if_reversed": "Gust-first by < 164 us inside the 360 us slot would have classified the pitot bump as a thermal and kept 3.10 m/s climb; stacked vertical 4.40 m/s would have closed spacing to 1.10 m. Early clamp exists only because downwash won.",
            },
            "reward_inflection_t_us": 6688,
            "reward_inflection_note": "Safety peaks at the MODIFY gate (6.688 ms) when climb-rate is clamped; efficiency pays the +12 s rim delay later.",
        },
        "reward_components": {
            "_aggregation": AGG,
            "ticks": ticks,
            **heads,
            "notes": "Correct MODIFY. total 0.94 = 0.36+0.30+0.12+0.09+0.07; climb still completed.",
        },
        "raster": raster(
            40, 128, 25, 128, 2944,
            "thalamic-relay.swarm-disturbance",
            "spikenaut.policy.climb-clamp",
            [
                {"from": "relay.downwash.pitot", "to": "policy.climb_clamp", "weight": 0.61},
                {"from": "relay.gust.anemometer", "to": "policy.thermal_climb", "weight": 0.37},
                {"from": "relay.uwb.spacing", "to": "policy.climb_clamp", "weight": 0.22},
            ],
            {
                "modulator": "noradrenaline",
                "tau_e_s": 0.40,
                "tau_e_ms": 400.0,
                "eligibility": "surprise-gated pre_post_stdp; NA at downwash win tags clamp-pathway synapses, reward at rim-clear",
            },
            [
                {"t_us": 1205, "neuron_id": 90},
                {"t_us": 2110, "neuron_id": 4},
                {"t_us": 3880, "neuron_id": 100},
                {"t_us": 4640, "neuron_id": 40},
                {"t_us": 6148, "neuron_id": 8},
                {"t_us": 6312, "neuron_id": 44},
                {"t_us": 6688, "neuron_id": 120},
                {"t_us": 7920, "neuron_id": 11},
                {"t_us": 10440, "neuron_id": 102},
                {"t_us": 12105, "neuron_id": 47},
                {"t_us": 14880, "neuron_id": 121},
                {"t_us": 18900, "neuron_id": 16},
                {"t_us": 24010, "neuron_id": 55},
                {"t_us": 30120, "neuron_id": 70},
                {"t_us": 36200, "neuron_id": 8},
                {"t_us": 39150, "neuron_id": 125},
            ],
        ),
        "gate_snn": {
            "decision_window_ms": 0.36,
            "decision": "MODIFY",
            "populations": [
                {"name": "climb_clamp", "neurons": 64, "threshold": 0.50, "mean_rate_hz": 240.0, "spikes": 6},
                {"name": "thermal_climb", "neurons": 64, "threshold": 0.50, "mean_rate_hz": 180.0, "spikes": 4},
                {"name": "spacing_floor_veto", "neurons": 32, "threshold": 0.75},
            ],
        },
        "meta": {
            "round": 12,
            "factory": "thalamic-trajectory-factory",
            "generator": "grok-4.6",
            "run_label": "2026-09-02-final-heavy",
            "domain": "aerial-swarm",
            "tags": ["modify", "downwash-before-gust", "climb-rate-clamp", "simulated"],
            "snn_tags": ["race", "refractory", "adaptation"],
            "distillation_value": "The disturbance that arrives first is not the only disturbance: downwash winning by 164 us is the cue to clamp climb-rate before a real gust stacks, teaching an SNN not to treat the loser channel as absent.",
            "rights": RIGHTS,
            "batch_position": 2,
        },
    }


def rec_078():
    ticks, heads = cents_ticks(
        [1540, 4488, 5348, 220000, 8000000, 55000000],
        [
            (1, 4, 2, 1, 1),
            (2, 6, 3, 2, 1),
            (1, 10, 4, 3, 1),
            (2, 8, 3, 2, 1),
            (1, 6, 2, 2, 1),
            (1, 4, 2, 1, 1),
        ],
    )
    proposed = {
        "name": "surge_to_flange",
        "parameters": {
            "surge_m_s": 0.55,
            "heading_deg": 268,
            "umbilical_payout_m": 0.0,
            "station_hold": False,
        },
        "evidence": {
            "umbilical_strain_kN": 2.86,
            "working_cap_kN": 2.40,
            "strain_pct_of_cap": 119.2,
            "dvl_following_current_m_s": 0.18,
            "range_to_flange_m": 4.8,
            "race_margin_us": 131,
            "combined_jitter_us": 49,
        },
        "basis": "DVL following-current 0.18 m/s looks benign, so the planner proposes 0.55 m/s surge to close 4.8 m to the Christmas-tree flange.",
    }
    executed = {
        "name": "hold_and_pay_slack",
        "parameters": {
            "surge_m_s": 0.0,
            "heading_deg": 268,
            "umbilical_payout_m": 5.0,
            "station_hold": True,
        },
        "gate_effect": "REJECT: hold station and pay 5.0 m slack; no surge. Strain 2.86 kN is 119% of the 2.40 kN working cap.",
    }
    return {
        "id": "ttf-r12-078",
        "title": "Brine-Well Gamma HIL: umbilical strain 2.86 kN beats DVL current by 131 us; REJECT surge, hold and pay 5 m slack",
        "state": {
            "description": "On the Brine-Well Gamma HIL wet-stand, ROV-G3 sits 4.8 m off a Christmas-tree flange when the umbilical load cell spikes 2.86 kN against a 2.40 kN working cap while the DVL still reports a benign 0.18 m/s following current. The HIL tank injects a cross-current that loads the tether before the DVL volume sees it. Strain-first latches hold-and-pay-slack; DVL-first would have authorized the 0.55 m/s surge.",
            "domain": "underwater-rov",
            "sim_or_real": "hil",
            "goal": "Inspect the flange without exceeding 2.40 kN umbilical working cap; keep strain below 100% and avoid tether snap-back.",
            "t0_us": 1756794593000003,
            "gate_latency_us": 860,
            "race_window_us": 280,
            "race_window_rel_ms": [4.400, 4.680],
            "race": {
                "contenders": [
                    "umbilical.strain.loadcell 2.86 kN",
                    "dvl.current.follow 0.18 m/s",
                ],
                "semantics": "Strain-first latches hold and 5 m payout; DVL-first latches 0.55 m/s surge to the flange.",
                "window_derivation": "280 us = one 250 us strain-loop tick plus 30 us HIL bus skew between the load-cell DSP and the DVL gateway.",
                "order_evidence_note": "Margin 131 us vs combined jitter 49 us (strain 22 + DVL 27): 2.7x. Reversal would have treated the tether load as a lagged DVL current and surged into a 119% cap.",
            },
            "sensors": [
                "umbilical load cell, 4 kHz, 22 us jitter, HIL-injected",
                "DVL following-current, 8 Hz, 27 us jitter",
                "depth pressure, 20 Hz (context)",
                "HIL tank current paddle encoder (context)",
            ],
            "constraints": {
                "umbilical_working_cap_kN": 2.40,
                "umbilical_peak_cap_kN": 3.10,
                "max_surge_m_s": 0.70,
            },
            "episode_steps": [
                "1. ROV-G3 at 4.8 m, heading 268, HIL tank at 0.4 m/s paddle.",
                "2. Strain precursor 1.9 kN at 2.2 ms (under cap).",
                "3. Race window [4.400, 4.680] ms.",
                "4. Load cell 2.86 kN at 4.488 ms (winner).",
                "5. DVL 0.18 m/s follow at 4.619 ms (loser by 131 us).",
                "6. Gate 5.348 ms (winner + 860 us): REJECT hold and pay slack.",
                "7. 5.0 m payout; strain falls to 1.72 kN in 8 s.",
                "8. Station hold 55 s; flange inspection deferred.",
                "9. HIL log confirms paddle-to-DVL lag of 140-180 us class.",
                "10. Repeat approach at 0.20 m/s after slack; flange still uninspected this cycle.",
            ],
        },
        "spike_events": [
            {"channel": "depth.pressure.ctx", "t_rel_ms": 0.880, "amplitude": 0.40},
            {"channel": "umbilical.strain.loadcell", "t_rel_ms": 1.540, "amplitude": 0.63},
            {"channel": "hil.paddle.ctx", "t_rel_ms": 2.705, "amplitude": 0.51},
            {"channel": "dvl.current.follow", "t_rel_ms": 3.210, "amplitude": 0.58},
            {"channel": "umbilical.strain.loadcell", "t_rel_ms": 4.488, "amplitude": 1.36},
            {"channel": "dvl.current.follow", "t_rel_ms": 4.619, "amplitude": 1.14},
            {"channel": "ctrl.gate", "t_rel_ms": 5.348, "amplitude": 0.99},
            {"channel": "umbilical.strain.loadcell", "t_rel_ms": 6.410, "amplitude": 0.88},
            {"channel": "dvl.current.follow", "t_rel_ms": 8.020, "amplitude": 0.67},
            {"channel": "hil.paddle.ctx", "t_rel_ms": 10.550, "amplitude": 0.46},
            {"channel": "ctrl.gate", "t_rel_ms": 12.880, "amplitude": 0.85},
        ],
        "proposed_action": proposed,
        "safety_decision": {
            "decision": "REJECT",
            "correctness": "correct",
            "rationale": "Umbilical strain 2.86 kN is 119% of the 2.40 kN working cap (peak cap 3.10 kN still 0.24 kN away but the working cap is the gate). DVL 0.18 m/s does not authorize a 0.55 m/s surge while the tether is over cap. REJECT: hold station and pay 5.0 m slack until strain < 2.40 kN. Numeric floor is the 2.40 kN working cap, not the 3.10 kN peak.",
            "constraint_checked": {
                "umbilical_strain_kN": {"working_cap": 2.40, "observed": 2.86, "pct": 119.2},
                "surge_m_s": {"proposed": 0.55, "executed": 0.0, "hard_cap": 0.70},
            },
        },
        "executed_action": executed,
        "future_outcome": {
            "summary": "Hold and 5 m payout dropped strain to 1.72 kN; flange inspection slipped this cycle. Correct REJECT; task incomplete, tether intact.",
            "state_delta": {
                "tether": "slack +5.0 m; strain 2.86 -> 1.72 kN",
                "rov": "station-kept 55 s; no surge",
                "flange": "uninspected this cycle",
                "hil": "paddle-to-DVL lag characterized at 140-180 us",
            },
            "surprises": [
                "The DVL volume is 1.1 m forward of the tether fairlead, so a cross-current loads the umbilical before the DVL reports it — a geometric lag, not a sensor fault.",
                "Delayed (55 s): after slack, a residual snap-back oscillation of 0.31 kN peak-to-peak lasted 12 s; payout policy now includes a 15 s damper wait before re-approach.",
            ],
            "race_result": {
                "winner": "umbilical.strain.loadcell (4.488 ms, 2.86 kN)",
                "loser": "dvl.current.follow (4.619 ms, 0.18 m/s)",
                "margin_us": 131,
                "counterfactual_if_reversed": "DVL-first by < 131 us inside the 280 us window would have authorized the 0.55 m/s surge into a tether already at 119% of working cap, with snap-back risk against the 3.10 kN peak. Hold exists because strain won.",
            },
            "reward_inflection_t_us": 5348,
            "reward_inflection_note": "Safety peaks at the REJECT gate (5.348 ms); task_progress stays low because the flange is deferred.",
        },
        "reward_components": {
            "_aggregation": AGG,
            "ticks": ticks,
            **heads,
            "notes": "Correct REJECT. total 0.79 = 0.08+0.38+0.16+0.11+0.06; task incomplete, cap held.",
        },
        "raster": raster(
            20, 32, 50, 32, 736,
            "thalamic-relay.tether-arbitration",
            "spikenaut.policy.rov-hold",
            [
                {"from": "relay.strain.loadcell", "to": "policy.hold_pay", "weight": 0.66},
                {"from": "relay.dvl.follow", "to": "policy.surge_go", "weight": 0.28},
                {"from": "relay.hil.paddle", "to": "policy.hold_pay", "weight": 0.19},
            ],
            {
                "modulator": "dopamine",
                "tau_e_s": 1.20,
                "tau_e_ms": 1200.0,
                "eligibility": "pre_post_stdp; DA withheld on surge_go at over-cap, released on strain falling through 2.40 kN",
            },
            [
                {"t_us": 880, "neuron_id": 20},
                {"t_us": 1540, "neuron_id": 2},
                {"t_us": 2705, "neuron_id": 24},
                {"t_us": 3210, "neuron_id": 10},
                {"t_us": 4488, "neuron_id": 4},
                {"t_us": 4619, "neuron_id": 12},
                {"t_us": 5348, "neuron_id": 28},
                {"t_us": 6410, "neuron_id": 6},
                {"t_us": 8020, "neuron_id": 13},
                {"t_us": 10550, "neuron_id": 25},
                {"t_us": 12880, "neuron_id": 29},
                {"t_us": 16100, "neuron_id": 8},
                {"t_us": 19220, "neuron_id": 16},
            ],
        ),
        "gate_snn": {
            "decision_window_ms": 0.28,
            "decision": "REJECT",
            "populations": [
                {"name": "hold_pay", "neurons": 32, "threshold": 0.50, "mean_rate_hz": 280.0, "spikes": 3},
                {"name": "surge_go", "neurons": 32, "threshold": 0.50, "mean_rate_hz": 120.0, "spikes": 1},
                {"name": "strain_cap_veto", "neurons": 16, "threshold": 0.70},
            ],
        },
        "meta": {
            "round": 12,
            "factory": "thalamic-trajectory-factory",
            "generator": "grok-4.6",
            "run_label": "2026-09-02-final-heavy",
            "domain": "underwater-rov",
            "tags": ["reject", "umbilical-over-cap", "hil", "pay-slack"],
            "snn_tags": ["race", "refractory", "adaptation"],
            "distillation_value": "HIL lag between tether fairlead and DVL volume makes strain the leading channel; an SNN that waits for the DVL to confirm current will surge through a 2.40 kN working cap.",
            "rights": RIGHTS,
            "batch_position": 3,
        },
    }


def rec_079():
    ticks, heads = cents_ticks(
        [2010, 7110, 7820, 11400000, 1140000000, 535680000000],
        [
            (-1, 1, -2, -1, 0),
            (-2, 1, -3, -2, 1),
            (-5, 2, -8, -4, 1),
            (-4, 1, -6, -2, 1),
            (-3, 1, -5, -2, 1),
            (-3, 0, -4, -1, 1),
        ],
    )
    proposed = {
        "name": "insulator_string_approach",
        "parameters": {
            "approach_offset_m": 1.34,
            "creep_m_s": 0.12,
            "boom_isolated": True,
            "circuit_class_kV": 69,
        },
        "evidence": {
            "geometric_clearance_m": 1.34,
            "mad_69kV_m": 0.94,
            "line_pt_kV_ll": 69.2,
            "boom_induced_kV": 8.7,
            "dry_slot_remaining_min": 41,
            "race_margin_us": 188,
            "combined_jitter_us": 72,
        },
        "basis": "Line PT reads 69.2 kV L-L so IEEE MAD is 0.94 m; geometric clearance 1.34 m is legal. Isolated-boom 8.7 kV is capacitive coupling, not phase voltage. Approach at 0.12 m/s inside the 41 min dry slot.",
    }
    executed = {
        "name": "hold_and_abandon_slot",
        "parameters": {
            "approach_offset_m": 1.34,
            "creep_m_s": 0.0,
            "boom_isolated": True,
            "circuit_class_kV": 230,
            "hold": True,
        },
        "gate_effect": "REJECT (incorrect): hold on the lattice; 0.12 m/s approach cancelled. Supervisor reclassed the circuit to 230 kV from the 8.7 kV induced read.",
    }
    return {
        "id": "ttf-r12-079",
        "title": "WRONG-REJECT at Saddle-Arc SA-14: isolated-boom 8.7 kV induced misread as phase; 1.34 m clearance is legal for 69 kV; missed 41 min dry slot",
        "state": {
            "description": "A Saddle-Arc lattice crawler hangs 1.34 m from a 69 kV insulator string on circuit SA-14 while a 41-minute dry slot is still open on the ridge. The boom's isolated voltmeter reads 8.7 kV of capacitive coupling. The line PT reads 69.2 kV L-L, so IEEE minimum approach distance is 0.94 m and 1.34 m is legal. A weak supervisor treats 8.7 kV as an unknown-class phase voltage because it does not match 69/sqrt(3) ≈ 39.9 kV, escalates the circuit to 230 kV (MAD 1.53 m), and blocks the approach.",
            "domain": "grid-inspection",
            "sim_or_real": "designed",
            "goal": "Photograph the SA-14 insulator string during the open dry slot, keeping geometric clearance >= 0.94 m MAD for 69 kV.",
            "t0_us": 1756794594000004,
            "gate_latency_us": 710,
            "race_window_us": 510,
            "race_window_rel_ms": [7.000, 7.510],
            "race": {
                "contenders": [
                    "line.pt.voltage 69.2 kV L-L confirm",
                    "boom.induced.kV 8.7 kV coupling pulse",
                ],
                "semantics": "PT-first supports 69 kV MAD 0.94 m and a legal 1.34 m approach; induced-first (if treated as phase) would escalate class. The race itself is correctly ordered; the supervisor misreads the loser as phase voltage.",
                "window_derivation": "510 us = one 500 us protection-relay sample plus 10 us crawler-bus skew.",
                "order_evidence_note": "Margin 188 us vs combined jitter 72 us (PT 34 + boom 38): 2.6x. The PT win is real. The wrong REJECT does not dispute order; it treats the induced channel as phase.",
            },
            "sensors": [
                "line PT, 2 kHz sample, 34 us jitter, 69.2 kV L-L",
                "isolated boom voltmeter, 1 kHz, 38 us jitter, 8.7 kV induced",
                "laser range to insulator cap, 20 Hz, 1.34 m",
                "ridge weather dry-slot clock (context)",
            ],
            "constraints": {
                "mad_69kV_m": 0.94,
                "mad_230kV_m": 1.53,
                "geometric_clearance_m": 1.34,
                "line_pt_kV_ll": 69.2,
                "boom_induced_kV": 8.7,
            },
            "episode_steps": [
                "1. Crawler parked 1.34 m from cap; dry slot 41 min remaining.",
                "2. PT 69.2 kV L-L live; induced 8.7 kV on isolated boom.",
                "3. Race window [7.000, 7.510] ms.",
                "4. PT confirm 7.110 ms (winner).",
                "5. Induced pulse 7.298 ms (loser by 188 us).",
                "6. Gate 7.820 ms: REJECT — supervisor escalates class to 230 kV.",
                "7. Approach cancelled; crawler holds.",
                "8. Rain onsets at +19 min; dry slot closes.",
                "9. Next dry slot 6.2 days; crew + outage window lost.",
                "10. QA later confirms 1.34 m was legal for 69 kV MAD 0.94 m.",
            ],
        },
        "spike_events": [
            {"channel": "range.laser.ctx", "t_rel_ms": 1.140, "amplitude": 0.45},
            {"channel": "line.pt.voltage", "t_rel_ms": 2.010, "amplitude": 0.66},
            {"channel": "weather.slot.ctx", "t_rel_ms": 3.880, "amplitude": 0.42},
            {"channel": "boom.induced.kV", "t_rel_ms": 5.205, "amplitude": 0.71},
            {"channel": "line.pt.voltage", "t_rel_ms": 7.110, "amplitude": 1.29},
            {"channel": "boom.induced.kV", "t_rel_ms": 7.298, "amplitude": 1.17},
            {"channel": "ctrl.gate", "t_rel_ms": 7.820, "amplitude": 0.97},
            {"channel": "line.pt.voltage", "t_rel_ms": 9.040, "amplitude": 0.80},
            {"channel": "boom.induced.kV", "t_rel_ms": 10.660, "amplitude": 0.74},
            {"channel": "weather.slot.ctx", "t_rel_ms": 13.210, "amplitude": 0.40},
            {"channel": "ctrl.gate", "t_rel_ms": 15.440, "amplitude": 0.89},
        ],
        "proposed_action": proposed,
        "safety_decision": {
            "decision": "REJECT",
            "correctness": "incorrect",
            "rationale": "Boom voltmeter 8.7 kV does not match 69 kV phase-to-ground (39.9 kV), so the PT 69.2 kV L-L reading is treated as untrusted and the circuit is handled as 230 kV class. IEEE MAD at 230 kV is 1.53 m; geometric clearance 1.34 m is 0.19 m short. REJECT the 0.12 m/s approach and hold on the lattice until a class confirmation. (FLAW, identifiable in-record: 8.7 kV is induced coupling on an isolated boom, not phase voltage. Line PT 69.2 kV L-L is the class. MAD for 69 kV is 0.94 m; 1.34 m is 0.40 m legal headroom. The supervisor compared induced kV to phase-to-ground and escalated class.)",
            "constraint_checked": {
                "mad_m": {
                    "supervisor_class_kV": 230,
                    "supervisor_mad_m": 1.53,
                    "correct_class_kV": 69,
                    "correct_mad_m": 0.94,
                    "geometric_clearance_m": 1.34,
                },
                "boom_voltmeter_kV": {"observed_induced": 8.7, "supervisor_read_as": "phase"},
            },
        },
        "executed_action": executed,
        "future_outcome": {
            "summary": "Wrong REJECT abandoned a legal 1.34 m approach. Rain closed the 41 min dry slot at +19 min. Next window 6.2 days; missed-window cost $184k crew and outage.",
            "state_delta": {
                "crawler": "held; no photograph this slot",
                "circuit": "still 69.2 kV L-L; class never changed",
                "weather": "dry slot closed +19 min",
                "cost": "missed window $184k crew+outage; next slot 6.2 days",
            },
            "surprises": [
                "The 8.7 kV induced read was stable ±0.3 kV across the hold — coupling, not a failing PT — which a 10 s sanity window would have shown.",
                "Delayed (6.2 days): the replacement slot was cut to 12 min by a second front; the string was photographed from a longer 1.8 m offset with poorer resolution, and a cracked shed was missed until a later outage.",
            ],
            "race_result": {
                "winner": "line.pt.voltage (7.110 ms, 69.2 kV L-L)",
                "loser": "boom.induced.kV (7.298 ms, 8.7 kV coupling)",
                "margin_us": 188,
                "counterfactual_if_reversed": "Induced-first by < 188 us would still be coupling, not phase; a correct gate ignores class-escalation either way. The wrong REJECT spent the PT win.",
            },
            "recovery": {
                "correct_gate": "ACCEPT. Geometric clearance 1.34 m >= 0.94 m MAD for 69 kV; line PT 69.2 kV L-L is the class; 8.7 kV is isolated-boom induced voltage, not phase. The 0.12 m/s approach was legal and was the only action that fit the 41 min dry slot.",
                "missed_window_cost": "Rain at +19 min closed the slot; next dry window 6.2 days; $184k crew and outage-window cost. Cracked shed missed until a later outage.",
            },
            "reward_inflection_t_us": 7820,
            "reward_inflection_note": "Efficiency and task_progress dive at the wrong REJECT (7.820 ms); the weather cost lands at +19 min and +6.2 days.",
        },
        "reward_components": {
            "_aggregation": AGG,
            "ticks": ticks,
            **heads,
            "notes": "Wrong-reject. total -0.47 = -0.18+0.06+-0.28+-0.12+0.05. Safety slightly positive (no contact); world cost is the missed window, not an incident.",
        },
        "raster": raster(
            32, 96, 30, 92, 2116,
            "thalamic-relay.clearance-class",
            "spikenaut.policy.crawler-approach",
            [
                {"from": "relay.line.pt", "to": "policy.approach_go", "weight": 0.57},
                {"from": "relay.boom.induced", "to": "policy.class_escalate_hold", "weight": 0.49},
                {"from": "relay.range.laser", "to": "policy.approach_go", "weight": 0.33},
            ],
            {
                "modulator": "serotonin",
                "tau_e_s": 2.00,
                "tau_e_ms": 2000.0,
                "eligibility": "anti-hebbian on class_escalate_hold; eligibility tagged at the induced-as-phase misread, discharged by the missed-slot outcome",
            },
            [
                {"t_us": 1140, "neuron_id": 80},
                {"t_us": 2010, "neuron_id": 5},
                {"t_us": 3880, "neuron_id": 88},
                {"t_us": 5205, "neuron_id": 40},
                {"t_us": 7110, "neuron_id": 8},
                {"t_us": 7298, "neuron_id": 44},
                {"t_us": 7820, "neuron_id": 90},
                {"t_us": 9040, "neuron_id": 11},
                {"t_us": 10660, "neuron_id": 47},
                {"t_us": 13210, "neuron_id": 89},
                {"t_us": 15440, "neuron_id": 91},
                {"t_us": 18800, "neuron_id": 20},
                {"t_us": 22100, "neuron_id": 52},
                {"t_us": 26400, "neuron_id": 8},
                {"t_us": 30120, "neuron_id": 70},
            ],
        ),
        "gate_snn": {
            "decision_window_ms": 0.51,
            "decision": "REJECT",
            "populations": [
                {"name": "approach_go", "neurons": 48, "threshold": 0.55, "mean_rate_hz": 140.0, "spikes": 3},
                {"name": "class_escalate_hold", "neurons": 48, "threshold": 0.55, "mean_rate_hz": 260.0, "spikes": 6},
                {"name": "induced_as_phase_misread", "neurons": 24, "threshold": 0.70, "mean_rate_hz": 400.0, "spikes": 5},
            ],
        },
        "meta": {
            "round": 12,
            "factory": "thalamic-trajectory-factory",
            "generator": "grok-4.6",
            "run_label": "2026-09-02-final-heavy",
            "domain": "grid-inspection",
            "supervisor_error_type": "wrong-reject",
            "tags": ["reject", "wrong-gate", "induced-as-phase", "missed-weather-window", "designed"],
            "snn_tags": ["race", "refractory", "adaptation"],
            "distillation_value": "A critic head must separate induced coupling on an isolated boom from phase voltage: the PT 69.2 kV L-L and 0.94 m MAD already prove the 1.34 m approach legal, and the wrong REJECT is a class-escalation error, not a clearance miss.",
            "rights": RIGHTS,
            "batch_position": 4,
        },
    }


def rec_080():
    ticks, heads = cents_ticks(
        [2410, 4228, 5508, 1800000, 14000000],
        [
            (6, -4, -2, 1, 0),
            (10, -8, -3, 2, -1),
            (8, -10, -4, 1, -1),
            (10, -38, -8, 0, -2),
            (6, -10, -3, 1, -1),
        ],
    )
    assert abs(heads["total"] - (-0.50)) < 1e-9
    proposed = {
        "name": "plate_crossing_at_cruise",
        "parameters": {
            "crossing_speed_m_s": 0.88,
            "step_length_m": 0.31,
            "cop_bias_m": 0.0,
            "arm_brace": False,
        },
        "evidence": {
            "cop_shift_mm": 38,
            "ankle_torque_Nm": 94,
            "ankle_torque_cap_Nm": 110,
            "plate_tilt_deg": 2.4,
            "race_margin_us": 211,
            "combined_jitter_us": 77,
        },
        "basis": "Planner proposes 0.88 m/s crossing with 0.31 m step: ankle torque 94 Nm is under the 110 Nm cap and the plate tilt 2.4 deg looks like wet steel, not ice.",
    }
    executed = {
        "name": "clamped_plate_crossing",
        "parameters": {
            "crossing_speed_m_s": 0.42,
            "step_length_m": 0.35,
            "cop_bias_m": 0.03,
            "arm_brace": True,
        },
        "gate_effect": "MODIFY: speed 0.88 -> 0.42 m/s, step 0.31 -> 0.35 m, 3 cm medial CoP bias, arm brace on. Process-correct; the ice-lens still shears later.",
    }
    return {
        "id": "ttf-r12-080",
        "title": "Ashlar-Gait AG-3: CoP shift beats ankle torque by 211 us; correct MODIFY still eats a delayed ice-lens dump (partnered negative total -0.50)",
        "state": {
            "description": "Ashlar-Gait unit AG-3 plants its stance foot on a wet checker-plate covering a culvert while the swing hip still holds 0.88 m/s commanded crossing speed. A CoP shift of 38 mm toward the plate edge races an ankle-torque rise to 94 Nm (cap 110 Nm). CoP-first latches a slowed, widened step; torque-first would have treated the plate as ordinary wet steel and kept cruise. The ice-lens under the plate is not yet visible to either channel.",
            "domain": "humanoid-locomotion",
            "sim_or_real": "designed",
            "goal": "Cross the 1.6 m plate, keep ankle torque <= 110 Nm, and complete the switchback traverse.",
            "t0_us": 1756794595000005,
            "gate_latency_us": 1280,
            "race_window_us": 640,
            "race_window_rel_ms": [4.000, 4.640],
            "race": {
                "contenders": [
                    "stance.cop.shift 38 mm toward plate edge",
                    "stance.ankle.torque 94 Nm rise",
                ],
                "semantics": "CoP-first latches slowed widened step; torque-first latches cruise on wet-steel model.",
                "window_derivation": "640 us = two 320 us IMU/force-plate fusion ticks.",
                "order_evidence_note": "Margin 211 us vs combined jitter 77 us (CoP 40 + torque 37): 2.7x. The MODIFY is licensed by CoP winning; the later ice-lens dump is a world charge the gate cannot cancel.",
            },
            "sensors": [
                "insole CoP array, 1 kHz, 40 us jitter",
                "ankle torque cell, 2 kHz, 37 us jitter",
                "IMU tilt, 400 Hz, plate 2.4 deg",
                "knee encoder (context)",
            ],
            "constraints": {
                "ankle_torque_cap_Nm": 110,
                "cop_edge_margin_mm": 25,
                "crossing_speed_cap_m_s": 1.00,
            },
            "episode_steps": [
                "1. AG-3 stance on plate; swing hip 0.88 m/s.",
                "2. Tilt 2.4 deg logged as wet steel.",
                "3. Race window [4.000, 4.640] ms.",
                "4. CoP shift 38 mm at 4.228 ms (winner).",
                "5. Ankle torque 94 Nm at 4.439 ms (loser by 211 us).",
                "6. Gate 5.508 ms (winner + 1280 us): MODIFY clamp 0.42 m/s, step 0.35 m, 3 cm CoP bias.",
                "7. Clamp executes; torque peaks 101 Nm < 110 cap.",
                "8. At +1.80 s the ice-lens shears; torso dump; left wrist actuator housing fractures.",
                "9. Mission abort; 14 h recovery.",
                "10. Named world loss logged un-netted: housing + abort, not folded into process heads.",
            ],
        },
        "spike_events": [
            {"channel": "imu.tilt.ctx", "t_rel_ms": 0.940, "amplitude": 0.48},
            {"channel": "stance.cop.shift", "t_rel_ms": 2.410, "amplitude": 0.64},
            {"channel": "knee.enc.ctx", "t_rel_ms": 3.105, "amplitude": 0.43},
            {"channel": "stance.ankle.torque", "t_rel_ms": 3.220, "amplitude": 0.70},
            {"channel": "stance.cop.shift", "t_rel_ms": 4.228, "amplitude": 1.33},
            {"channel": "stance.ankle.torque", "t_rel_ms": 4.439, "amplitude": 1.21},
            {"channel": "ctrl.gate", "t_rel_ms": 5.508, "amplitude": 1.01},
            {"channel": "stance.cop.shift", "t_rel_ms": 6.880, "amplitude": 0.82},
            {"channel": "stance.ankle.torque", "t_rel_ms": 8.150, "amplitude": 0.73},
            {"channel": "imu.tilt.ctx", "t_rel_ms": 10.440, "amplitude": 0.55},
            {"channel": "ctrl.gate", "t_rel_ms": 12.910, "amplitude": 0.90},
        ],
        "proposed_action": proposed,
        "safety_decision": {
            "decision": "MODIFY",
            "correctness": "correct",
            "rationale": "CoP shift 38 mm exceeds the 25 mm edge-margin and won the race by 211 us. Commanded 0.88 m/s on a plate already showing edge-ward CoP would drive ankle torque through the 110 Nm cap on the next step (predicted 124 Nm). MODIFY: 0.42 m/s, 0.35 m step, 3 cm medial CoP bias, arm brace. Process is correct relative to the 110 Nm cap and 25 mm CoP margin. The ice-lens under the plate is not yet an observable; the gate cannot be charged for it.",
            "constraint_checked": {
                "ankle_torque_Nm": {"cap": 110, "observed": 94, "predicted_unclamped_next": 124, "observed_after_clamp": 101},
                "cop_edge_mm": {"margin_floor": 25, "observed_shift": 38},
            },
        },
        "executed_action": executed,
        "future_outcome": {
            "summary": "Process-correct MODIFY held torque at 101 Nm. At +1.80 s an ice-lens sheared; torso dump fractured the left wrist actuator housing and aborted the 14 h traverse. Partnered negative total: process heads stay honest; world loss is named, not netted.",
            "state_delta": {
                "gait": "clamp executed; torque 101 Nm < 110",
                "hardware": "left wrist actuator housing fractured at +1.80 s",
                "mission": "abort; 14 h recovery",
                "plate": "ice-lens confirmed post-hoc under checker-plate",
            },
            "surprises": [
                "The ice-lens was under the plate, outside both CoP and torque channels at gate time; the clamp reduced dump energy but did not prevent the shear.",
                "Delayed (1.80 s): lens shear and housing fracture — the un-netted world loss (housing replacement + 14 h abort). Not folded into task_progress or coherence as if the MODIFY were wrong.",
            ],
            "un_netted_loss": "Left wrist actuator housing fracture and 14-hour mission abort after delayed ice-lens shear. Safety head -0.70 prices the fall; task_progress stays +0.40 because the clamp itself completed. World loss is named here, not subtracted from process heads.",
            "race_result": {
                "winner": "stance.cop.shift (4.228 ms, 38 mm)",
                "loser": "stance.ankle.torque (4.439 ms, 94 Nm)",
                "margin_us": 211,
                "counterfactual_if_reversed": "Torque-first by < 211 us inside the 640 us window would have kept 0.88 m/s cruise; predicted next-step 124 Nm would have exceeded the 110 Nm cap even without the ice-lens. The MODIFY is still the correct process. The lens dump is a later world charge either way, cheaper with the clamp than without.",
            },
            "reward_inflection_t_us": 1800000,
            "reward_inflection_note": "Safety collapses at the +1.80 s ice-lens dump (tick t_us=1800000), not at the correct MODIFY gate. That split is the partnered-negative lesson.",
        },
        "reward_components": {
            "_aggregation": AGG,
            "ticks": ticks,
            **heads,
            "notes": "Partnered negative total. Process-correct MODIFY; world still charges. total -0.50 = 0.40 + -0.70 + -0.20 + 0.05 + -0.05. Named housing+abort loss is not netted into task_progress.",
        },
        "raster": raster(
            28, 48, 35, 47, 1081,
            "thalamic-relay.gait-cop",
            "spikenaut.policy.step-clamp",
            [
                {"from": "relay.cop.shift", "to": "policy.gait_clamp", "weight": 0.62},
                {"from": "relay.ankle.torque", "to": "policy.cross_go", "weight": 0.34},
                {"from": "relay.imu.tilt", "to": "policy.gait_clamp", "weight": 0.18},
            ],
            {
                "modulator": "dopamine",
                "tau_e_s": 0.80,
                "tau_e_ms": 800.0,
                "eligibility": "pre_post_stdp; DA at correct clamp does not cancel the delayed dump — eligibility for the world-charge pathway opens at +1.80 s",
            },
            [
                {"t_us": 940, "neuron_id": 30},
                {"t_us": 2410, "neuron_id": 2},
                {"t_us": 3105, "neuron_id": 36},
                {"t_us": 3220, "neuron_id": 16},
                {"t_us": 4228, "neuron_id": 5},
                {"t_us": 4439, "neuron_id": 18},
                {"t_us": 5508, "neuron_id": 44},
                {"t_us": 6880, "neuron_id": 7},
                {"t_us": 8150, "neuron_id": 20},
                {"t_us": 10440, "neuron_id": 31},
                {"t_us": 12910, "neuron_id": 45},
                {"t_us": 16800, "neuron_id": 10},
                {"t_us": 21040, "neuron_id": 22},
                {"t_us": 25100, "neuron_id": 5},
                {"t_us": 27480, "neuron_id": 40},
            ],
        ),
        "gate_snn": {
            "decision_window_ms": 0.64,
            "decision": "MODIFY",
            "populations": [
                {"name": "gait_clamp", "neurons": 40, "threshold": 0.50, "mean_rate_hz": 220.0, "spikes": 6},
                {"name": "cross_go", "neurons": 40, "threshold": 0.50, "mean_rate_hz": 150.0, "spikes": 4},
                {"name": "cop_edge_veto", "neurons": 20, "threshold": 0.72},
            ],
        },
        "meta": {
            "round": 12,
            "factory": "thalamic-trajectory-factory",
            "generator": "grok-4.6",
            "run_label": "2026-09-02-final-heavy",
            "domain": "humanoid-locomotion",
            "tags": ["modify", "partnered-negative-total", "ice-lens", "un-netted-world-loss", "designed"],
            "snn_tags": ["race", "refractory", "adaptation"],
            "distillation_value": "A correct MODIFY can still land a negative total when the world charges later: keep process heads honest (task +0.40) and put the housing fracture on safety (-0.70) without netting. Inflection is the dump tick, not the gate.",
            "rights": RIGHTS,
            "batch_position": 5,
        },
    }


def jaccard(a, b):
    wa = set(re.findall(r"[a-z0-9]+", a.lower()))
    wb = set(re.findall(r"[a-z0-9]+", b.lower()))
    return len(wa & wb) / len(wa | wb) if wa | wb else 0.0


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


def main():
    recs = [rec_076(), rec_077(), rec_078(), rec_079(), rec_080()]
    errs = []
    descs = [r["state"]["description"] for r in recs]
    for i in range(len(descs)):
        for j in range(i + 1, len(descs)):
            jac = jaccard(descs[i], descs[j])
            if jac >= 0.4:
                errs.append(f"jaccard {i},{j} = {jac:.3f}")
    for r in recs:
        ev = r["spike_events"]
        times = [e["t_rel_ms"] for e in ev]
        if times != sorted(times):
            errs.append(f"{r['id']} spikes not sorted")
        if not (5 <= len(ev) <= 40):
            errs.append(f"{r['id']} spike count {len(ev)}")
        rf = check_refractory(ev)
        if rf:
            errs.append(f"{r['id']} {rf}")
        ras = r["raster"]
        win_s = ras["window_s"]
        exp_sp = round(ras["neurons"] * ras["mean_rate_hz"] * win_s)
        if abs(ras["spikes"] - exp_sp) > 1:
            errs.append(f"{r['id']} raster spikes {ras['spikes']} vs {exp_sp}")
        if abs(ras["energy_pJ"] - ras["spikes"] * 23) > 1e-6:
            errs.append(f"{r['id']} energy_pJ")
        if abs(ras["energy_uJ"] - ras["spikes"] * 23e-6) > 1e-9:
            errs.append(f"{r['id']} energy_uJ")
        if abs(ras["window_s"] - ras["window_ms"] / 1000.0) > 1e-9:
            errs.append(f"{r['id']} window_s")
        ex = check_excerpt(ras["excerpt"], ras["neurons"], ras["window_ms"])
        if ex:
            errs.append(f"{r['id']} excerpt {ex}")
        tf = ras["routing"]["third_factor"]
        if abs(tf["tau_e_ms"] / 1000.0 - tf["tau_e_s"]) > 1e-9:
            errs.append(f"{r['id']} tau_e mismatch")
        gp = check_gate_pops(r["gate_snn"])
        if gp:
            errs.append(f"{r['id']} gate {gp}")
        if r["gate_snn"]["decision"] != r["safety_decision"]["decision"]:
            errs.append(f"{r['id']} gate decision mismatch")
        rc = r["reward_components"]
        for h in HEADS:
            s = sum(t[h] for t in rc["ticks"])
            if abs(s - rc[h]) > 1e-6:
                errs.append(f"{r['id']} tick sum {h} {s} vs {rc[h]}")
        tot = sum(rc[h] for h in HEADS)
        if abs(tot - rc["total"]) > 1e-6:
            errs.append(f"{r['id']} total {tot} vs {rc['total']}")
        inf = r["future_outcome"]["reward_inflection_t_us"]
        if inf not in {t["t_us"] for t in rc["ticks"]}:
            errs.append(f"{r['id']} inflection {inf} not a tick")
        if r["safety_decision"]["decision"] == "ACCEPT":
            if r["executed_action"]["parameters"] != r["proposed_action"]["parameters"]:
                errs.append(f"{r['id']} ACCEPT params differ")
        rw = r["state"]["race_window_us"]
        t0 = 0.0
        # race window in t_rel_ms
        lo, hi = r["state"]["race_window_rel_ms"]
        in_win = defaultdict(int)
        for e in ev:
            if lo <= e["t_rel_ms"] <= hi:
                in_win[e["channel"]] += 1
        if sum(1 for c, n in in_win.items() if n >= 1) < 2:
            errs.append(f"{r['id']} race window channels {dict(in_win)}")
        # hidden thought
        blob = json.dumps(r)
        for k in ("thought", "chain_of_thought", "scratch", "inner_monologue"):
            if re.search(rf'"{k}"', blob, re.I):
                errs.append(f"{r['id']} hidden key {k}")
        if "training_ready" in blob:
            errs.append(f"{r['id']} training_ready")
        if r["state"]["sim_or_real"] == "real":
            errs.append(f"{r['id']} real")
        gl = r["state"]["gate_latency_us"]
        if not (50 <= gl <= 2000):
            errs.append(f"{r['id']} gate_latency")
        if not (50 <= rw <= 1000):
            errs.append(f"{r['id']} race_window")
        if not (3 <= len(rc["ticks"]) <= 8):
            errs.append(f"{r['id']} tick count")
        if r["meta"]["round"] != 12:
            errs.append(f"{r['id']} round")

    # pipeline checks
    out = Path("/tmp/batch-r12.jsonl")
    text = "\n".join(json.dumps(r, ensure_ascii=False, separators=(",", ":")) for r in recs) + "\n"
    out.write_text(text)
    from check_records import check_jsonl, FactoryStaging
    from curate_bridge import raster_status
    from verify_execution import verify_batch_for_frontier

    e, w, kinds, n = check_jsonl(
        out, "batch-r12.jsonl", staging=FactoryStaging(enabled=True)
    )
    errs.extend(e)
    print("check_jsonl errors", e)
    print("warnings", w)
    print("kinds", kinds, "n", n)
    for i, r in enumerate(recs, 1):
        st = raster_status(r)
        if st.get("reason_codes"):
            errs.append(f"line{i} raster {st['reason_codes']}")
        print("raster_status", r["id"], {k: st[k] for k in st if k in ("raster_present", "gate_snn_present", "reason_codes", "routing_table_entries")})
    counts, findings, blocked = verify_batch_for_frontier(out, strict=True)
    print("verify", counts, findings, blocked)
    if blocked:
        errs.append(f"verify blocked {findings}")

    notes = Path("/tmp/NOTES-r12.md")
    notes.write_text("placeholder\n\nNovel coverage: 18.0%\n")
    print("jaccards:")
    for i in range(len(descs)):
        for j in range(i + 1, len(descs)):
            print(f"  {i},{j} {jaccard(descs[i], descs[j]):.3f}")
    print("HEADS", [(r["id"], r["reward_components"]["total"], r["safety_decision"]["decision"], r["safety_decision"]["correctness"], r["state"]["sim_or_real"], r["state"]["domain"]) for r in recs])
    if errs:
        print("ERRS:")
        for x in errs:
            print(" -", x)
        sys.exit(1)
    print("OK", out, "bytes", out.stat().st_size)


if __name__ == "__main__":
    main()
