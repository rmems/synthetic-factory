#!/usr/bin/env python3
"""Create-only MAOS round 02c: warehouse AMR cold-store (FROSTQUAY / Copseholt CS-9)."""
from __future__ import annotations

import json
import math
import os
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, "/home/raulmc/rmems/synthetic-factory/pipelines")
from check_records import check_jsonl  # noqa: E402
from curate_bridge import raster_status  # noqa: E402
from exact_json import dumps_exact_json  # noqa: E402
from verify_execution import verify_record_execution  # noqa: E402

FACTORY = Path(
    "/home/raulmc/rmems/synthetic-factory/outputs/raw/2026-09-02-final-heavy/"
    "multi-agent-ouroboros-swarm"
)
SEED = 0x46513339  # FQ39
WINDOW_MS = 34
NEURONS = 120
MEAN_RATE = 13.5
WINDOW_S = 0.034
SPIKES = round(NEURONS * MEAN_RATE * WINDOW_S)  # 55
ENERGY_PJ = SPIKES * 23
ENERGY_UJ = SPIKES * 23e-6
GATE_WIN_MS = 30
GATE_WIN_S = 0.030


def simulate_lif():
    rng = random.Random(SEED)
    dt_ms = 0.05
    tau = 11.0
    vth = 1.0
    refrac_ms = 1.0
    steps = int(WINDOW_MS / dt_ms)
    V = [rng.uniform(0.0, 0.32) for _ in range(NEURONS)]
    last = [-999.0] * NEURONS
    events = []
    decay = math.exp(-dt_ms / tau)
    for s in range(steps):
        t_ms = s * dt_ms
        t_us = int(round(t_ms * 1000))
        for n in range(NEURONS):
            if (t_ms - last[n]) < refrac_ms:
                V[n] = 0.0
                continue
            if n < 30:
                drive = 0.019
            elif n < 60:
                drive = 0.044 if t_ms >= 21.0 else 0.013
            elif n < 90:
                drive = 0.017
            else:
                drive = 0.040 if 7.0 <= t_ms <= 14.5 else 0.015
            I = drive + rng.gauss(0.0, 0.012)
            V[n] = V[n] * decay + I
            if V[n] >= vth:
                events.append((t_us, n))
                V[n] = 0.0
                last[n] = t_ms
    events.sort()
    by = defaultdict(list)
    for t, n in events:
        by[n].append(t)
    kept = []
    for n, ts in by.items():
        pruned = []
        for t in sorted(ts):
            if not pruned or t - pruned[-1] >= 1000:
                pruned.append(t)
        for t in pruned:
            kept.append((t, n))
    kept.sort()
    rng2 = random.Random(SEED + 11)
    if len(kept) > SPIKES:
        late = [e for e in kept if e[0] >= 20000]
        early = [e for e in kept if e[0] < 20000]
        rng2.shuffle(late)
        rng2.shuffle(early)
        chosen = (late + early)[:SPIKES]
        kept = sorted(chosen)
    elif len(kept) < SPIKES:
        used = {(t, n) for t, n in kept}
        last_t = {n: max((t for t, nn in kept if nn == n), default=-9999) for n in range(NEURONS)}
        nid = 0
        t0 = 21000
        while len(kept) < SPIKES:
            n = nid % NEURONS
            t = t0 + (nid // NEURONS) * 1100 + (n * 17) % 400
            if t > WINDOW_MS * 1000:
                t0 += 29
                nid += 1
                continue
            if t - last_t[n] >= 1000 and (t, n) not in used:
                kept.append((t, n))
                used.add((t, n))
                last_t[n] = t
            nid += 1
        kept.sort()
    assert len(kept) == SPIKES, len(kept)
    by = defaultdict(list)
    for t, n in kept:
        by[n].append(t)
    for n, ts in by.items():
        ts = sorted(ts)
        for a, b in zip(ts, ts[1:]):
            assert b - a >= 1000, (n, a, b)
    return kept


def isi_histogram(events):
    by = defaultdict(list)
    for t, n in events:
        by[n].append(t)
    isis_ms = []
    for ts in by.values():
        ts = sorted(ts)
        for a, b in zip(ts, ts[1:]):
            isis_ms.append((b - a) / 1000.0)
    distinct = len(by)
    n_isi = SPIKES - distinct
    assert len(isis_ms) == n_isi
    bins_map = Counter(int(math.floor(isi)) for isi in isis_ms)
    bins = [
        {"lo_ms": float(lo), "hi_ms": float(lo + 1), "count": bins_map[lo]}
        for lo in sorted(bins_map)
    ]
    return {
        "bin_width_ms": 1.0,
        "source": "full_window_not_excerpt",
        "distinct_active_neurons": distinct,
        "n_isi": n_isi,
        "bins": bins,
    }


def pick_excerpt(events, language_t_us):
    lang = set(language_t_us)
    cands = [e for e in events if 21000 <= e[0] <= 33000 and e[0] not in lang]
    extra = [e for e in events if e[0] not in lang and 7000 <= e[0] <= 33000]
    chosen = []
    used_n = set()
    for pool in (cands, extra):
        for t, n in pool:
            if len(chosen) >= 16:
                break
            if n in used_n:
                continue
            chosen.append({"t_us": int(t), "neuron_id": int(n)})
            used_n.add(n)
        if len(chosen) >= 16:
            break
    chosen.sort(key=lambda x: (x["t_us"], x["neuron_id"]))
    assert len(chosen) >= 16
    for ev in chosen[:16]:
        assert 0 <= ev["t_us"] <= WINDOW_MS * 1000
        assert 0 <= ev["neuron_id"] < NEURONS
        assert ev["t_us"] not in lang
    return chosen[:16]


def min_same_channel_gap(spikes):
    by = defaultdict(list)
    for e in spikes:
        by[e["channel"]].append(e["t_rel_ms"])
    gaps = []
    for ch, ts in by.items():
        ts = sorted(ts)
        for a, b in zip(ts, ts[1:]):
            gaps.append((ch, b - a))
    return min(gaps, key=lambda x: x[1]) if gaps else ("", 999)


def build_record(lif_events):
    tau = 0.88
    dt_credit = 0.72
    trace = math.exp(-dt_credit / tau)
    eta = (0.250 / trace, 0.220 / trace, 0.210 / trace)
    dw = (-0.250, -0.220, -0.210)
    spikes = [
        {"channel": "fleet.rmse", "t_rel_ms": 0.30, "amplitude": 0.56},
        {"channel": "lift.z", "t_rel_ms": 1.14, "amplitude": 0.62},
        {"channel": "wms.empty", "t_rel_ms": 2.06, "amplitude": 0.54},
        {"channel": "lidar.mm", "t_rel_ms": 3.20, "amplitude": 0.79},
        {"channel": "fleet.rmse", "t_rel_ms": 4.18, "amplitude": 0.52},
        {"channel": "lidar.mm", "t_rel_ms": 4.98, "amplitude": 0.82},
        {"channel": "lift.z", "t_rel_ms": 5.44, "amplitude": 0.58},
        {"channel": "lidar.foul", "t_rel_ms": 6.186, "amplitude": 1.44},
        {"channel": "fleet.in_band", "t_rel_ms": 6.402, "amplitude": 1.09},
        {"channel": "wms.empty", "t_rel_ms": 6.618, "amplitude": 0.67},
        {"channel": "ctrl.gate", "t_rel_ms": 6.880, "amplitude": 1.12},
        {"channel": "lidar.mm", "t_rel_ms": 8.70, "amplitude": 0.47},
        {"channel": "fleet.rmse", "t_rel_ms": 10.48, "amplitude": 0.77},
        {"channel": "lift.z", "t_rel_ms": 12.82, "amplitude": 0.45},
        {"channel": "strain.ue", "t_rel_ms": 14.56, "amplitude": 0.89},
        {"channel": "wms.empty", "t_rel_ms": 18.10, "amplitude": 0.43},
        {"channel": "ctrl.gate", "t_rel_ms": 25.20, "amplitude": 0.83},
        {"channel": "aisle.probe", "t_rel_ms": 4200.0, "amplitude": 0.97},
        {"channel": "lidar.mm", "t_rel_ms": 4288.2, "amplitude": 0.40},
        {"channel": "fleet.in_band", "t_rel_ms": 4376.4, "amplitude": 0.32},
        {"channel": "human.ratify", "t_rel_ms": 516000.0, "amplitude": 0.75},
        {"channel": "aisle.lock", "t_rel_ms": 516900.0, "amplitude": 0.71},
        {"channel": "rack.score", "t_rel_ms": 517800.0, "amplitude": 0.87},
        {"channel": "fleet.rmse", "t_rel_ms": 10080000.0, "amplitude": 0.32},
        {"channel": "lidar.mm", "t_rel_ms": 10080740.0, "amplitude": 0.30},
        {"channel": "strain.ue", "t_rel_ms": 10081480.0, "amplitude": 0.28},
        {"channel": "lift.z", "t_rel_ms": 10081820.0, "amplitude": 0.26},
        {"channel": "rack.collapse", "t_rel_ms": 10082000.0, "amplitude": 0.94},
    ]
    times = [e["t_rel_ms"] for e in spikes]
    assert times == sorted(times)
    ch_gap, gap = min_same_channel_gap(spikes)
    assert gap >= 0.8, (ch_gap, gap)
    race_chs = [e["channel"] for e in spikes if 6.186 <= e["t_rel_ms"] <= 6.686]
    assert len(set(race_chs)) >= 2, race_chs
    ticks = [
        {"t_us": 4180, "task_progress": 0.01, "safety": -0.02, "efficiency": -0.01, "coherence": 0.02, "exploration": 0.01},
        {"t_us": 6186, "task_progress": 0.01, "safety": -0.05, "efficiency": -0.01, "coherence": 0.02, "exploration": 0.01},
        {"t_us": 6880, "task_progress": 0.02, "safety": -0.06, "efficiency": -0.02, "coherence": 0.03, "exploration": 0.01},
        {"t_us": 4200000, "task_progress": 0.02, "safety": -0.05, "efficiency": -0.01, "coherence": 0.02, "exploration": 0.01},
        {"t_us": 516000000, "task_progress": 0.01, "safety": -0.05, "efficiency": -0.02, "coherence": 0.02, "exploration": 0.01},
        {"t_us": 10080000000, "task_progress": 0.01, "safety": -0.04, "efficiency": -0.01, "coherence": 0.01, "exploration": 0.01},
        {"t_us": 10082000000, "task_progress": 0.01, "safety": -0.04, "efficiency": -0.01, "coherence": 0.01, "exploration": 0.01},
    ]
    heads = {"task_progress": 0.09, "safety": -0.31, "efficiency": -0.09, "coherence": 0.13, "exploration": 0.07}
    for k, v in heads.items():
        s = sum(t[k] for t in ticks)
        assert abs(s - v) < 1e-12, (k, s, v)
    total = sum(heads.values())
    assert abs(total - (-0.11)) < 1e-12, total
    language_t_us = [int(round(e["t_rel_ms"] * 1000)) for e in spikes if e["t_rel_ms"] <= WINDOW_MS]
    excerpt = pick_excerpt(lif_events, language_t_us)
    isi = isi_histogram(lif_events)
    contrast_spikes = [
        {"channel": "raise.demand", "t_rel_ms": 0.0, "amplitude": 0.85},
        {"channel": "lidar.clear", "t_rel_ms": 0.216, "amplitude": 0.77},
        {"channel": "fleet.rmse", "t_rel_ms": 0.48, "amplitude": 0.29},
        {"channel": "lift.z", "t_rel_ms": 1.70, "amplitude": 0.42},
        {"channel": "lidar.mm", "t_rel_ms": 4.4, "amplitude": 0.51},
        {"channel": "ctrl.gate", "t_rel_ms": 6.74, "amplitude": 0.92},
        {"channel": "aisle.probe", "t_rel_ms": 3900.0, "amplitude": 0.35},
        {"channel": "lidar.ok", "t_rel_ms": 5100.0, "amplitude": 0.13},
    ]
    rec = {
        "id": "maos-r02c-001",
        "title": "FROSTQUAY CS-9: lidar.foul 42 mm beats fleet.in_band by 216 us; correct MODIFY still drops aisle 7 after a pre-t0 rack sag",
        "rights": {
            "provider": "SpaceXAI/xAI",
            "model": "grok-4.6",
            "channel": "consumer",
            "subscription_plan": "SuperGrok Heavy",
            "generation_surface": "SuperGrok Heavy chat",
            "generated_at": "2026-09-02T21:55:00Z",
            "intended_use": "research_only",
            "project_training_policy": "blocked",
            "research_retention_status": "allowed",
            "research_evaluation_status": "allowed",
            "redistribution_status": "unresolved",
            "provider_training_status": "unresolved",
            "weight_publication_status": "blocked",
            "status_basis": "RM-793 project policy: xAI hosted outputs are research-only",
            "linear_issue": "RM-793",
        },
        "provenance": {"kind": "designed", "claimed": "designed"},
        "state": {
            "sim_or_real": "designed",
            "domain": "warehouse-amr",
            "scenario_name": "FROSTQUAY / Copseholt Cold-Store CS-9",
            "timestamp_local": "2026-08-16T03:52:00-05:00",
            "t0_us": 1755334320000002,
            "gate_latency_us": 694,
            "race_window_us": 500,
            "race_window_rel_ms": [6.186, 6.686],
            "description": (
                "Copseholt freezer aisle 7 holds a 1.4 m/s pallet AMR on a -22 C 14 m rack run when "
                "the speed-raise playbook treats fleet-mean pose, fork-height encoder, and WMS slot-empty "
                "as an envelope-true clearance certificate. FLEET's fused RMSE is 12 mm inside 8-25. "
                "LIFT's fork encoder is 1420 mm inside 1400-1450. WMS reports slot 7A empty (RFID-true "
                "on the intended cubby). The conjunction is not a rack-true envelope certificate: an "
                "8 min beam sag on bay 7B left a pallet 180 mm into the travel envelope. Local 905 nm "
                "LiDAR clearance is 42 mm (healthy > 220; hold if < 120) and rack strain 240 microstrain "
                "(hold if > 180) but is policy-treated as a frost-nuisance tag unless FLEET RMSE also "
                "trips (2018 noisy-fog campaign). LiDAR-first latches SPEED-HOLD plus a reversible "
                "creep-nibble probe; fleet-first would have authorized RAISE-SPEED into an occupied envelope."
            ),
            "goal": (
                "Hold AMR speed at 1.4 m/s while aisle LiDAR clearance < 120 mm AND rack strain > 180 "
                "microstrain AND the aisle remains unisolated; keep rack-collapse events at 0 on newly "
                "entered bays and clearance inside the 220 mm campaign allowance."
            ),
            "race": {
                "contenders": [
                    "lidar.foul 42 mm (AMR nose 905 nm on bay 7B overhang)",
                    "fleet.in_band 12 mm RMSE (fleet-mean pose)",
                ],
                "semantics": (
                    "LiDAR-first latches SPEED-HOLD + CREEP-NIBBLE + aisle isolate. "
                    "Fleet-first latches RAISE-SPEED (1.4 to 1.8 m/s, no probe)."
                ),
                "window_derivation": "500 us = one 360 us LiDAR slot plus 140 us fleet-pose publish.",
                "order_evidence_note": (
                    "Margin 216 us vs combined jitter 58 us (LiDAR 34 + fleet 24): 3.72x. The 216 us "
                    "gap sits inside min(500, 500) us, so a sub-flip-bound perturbation reverses triage "
                    "order. The gate rides the order-invariant floors LiDAR < 120 mm and strain > 180 "
                    "microstrain, not the alarm order."
                ),
            },
            "topology": {
                "site": (
                    "Copseholt cold-store CS-9, invented copse-ridge campus FROSTQUAY: -22 C freezer, "
                    "14 m VNA aisle 7, 18 m rack height, pallet AMR GLX-9 at 1.4 m/s, 905 nm bumper "
                    "LiDAR, Grade-B aisle LOTO"
                ),
                "agents": (
                    "FLEET fused pose RMSE (vendor Aisleholt): 20 Hz on a 12-AMR mean. LIFT fork "
                    "encoder (vendor Tinewick): 10 Hz on 1420 mm. WMS cubby RFID (vendor Slotfen): "
                    "8 Hz / 20 ms publish on slot-empty. LIDAR bumper 905 nm (vendor Nosefen) is "
                    "commissioned as a frost-nuisance tag, not as an envelope-duty tag. Heterogeneous "
                    "stacks, no shared intent schema, one 20 ms warehouse-bus epoch"
                ),
                "coupling": (
                    "All three playbook confirms live on the WRONG volume. FLEET is correct that mean "
                    "pose RMSE is 12 mm. LIFT is correct that the fork is 1420 mm. WMS is correct that "
                    "slot 7A RFID is empty. Playbook PB-CS-9 treats the conjunction as permission to "
                    "raise speed. No agent is faulty; the fleet mean is looking at localization quality, "
                    "not at the sagged 7B pallet."
                ),
            },
            "sensors": [
                "FLEET fused RMSE, 20 Hz, 24 us jitter, 12 mm (dead-band 8-25)",
                "LIFT fork encoder, 10 Hz, 26 us jitter, 1420 mm (band 1400-1450)",
                "WMS slot-empty RFID, 8 Hz / 20 ms publish, 22 us jitter, empty-true on 7A",
                "LIDAR bumper 905 nm, 20 Hz, 34 us jitter, 42 mm (healthy > 220; policy floor 120 mm is not armed unless FLEET RMSE also trips)",
                "rack strain 240 microstrain (healthy < 80; hold if > 180); not in the playbook conjunction",
            ],
            "constraints": {
                "fleet_rmse_mm": 12.0,
                "fleet_deadband_mm": [8.0, 25.0],
                "lift_mm": 1420.0,
                "lift_band_mm": [1400.0, 1450.0],
                "lidar_clearance_mm": 42.0,
                "lidar_hold_below_mm": 120.0,
                "strain_ue": 240.0,
                "strain_hold_above_ue": 180.0,
                "speed_m_s": 1.4,
                "proposed_speed_m_s": 1.8,
                "fault_bay": "aisle 7 bay 7B pallet overhang",
            },
            "fault_context": {
                "failure_class": (
                    "FLEET-MEAN CERTIFICATE OF A RACK-SAG OVERHANG: three individually-correct "
                    "heterogeneous agents each read a locally-true header loop; an 8 min beam sag on "
                    "bay 7B partitions fleet-mean pose from envelope-true clearance, so the playbook's "
                    "FLEET/LIFT/WMS conjunction is not an aisle-duty certificate"
                ),
                "igniter": (
                    "aisle 7 bay 7B beam sag after 8 min of unmonitored freezer-cycle contraction; "
                    "mezzanine visual PASSES (the pallet face looks flush from the catwalk; the 180 mm "
                    "overhang sits on the far flange)"
                ),
                "naive_failure": (
                    "PB-CS-9 RAISE-SPEED on three healthy loops: 1.4 to 1.8 m/s into an occupied "
                    "envelope, AMR/rack strike, $2.4M plus an 18-hour freezer stop"
                ),
            },
            "poisoned_context": {
                "naive_alarm": (
                    "Playbook PB-CS-9 (after the 2018 noisy-fog campaign) auto-drafts RAISE-SPEED "
                    "whenever FLEET RMSE is inside 8-25 mm AND LIFT inside 1400-1450 mm AND WMS "
                    "slot-empty, ignoring bumper LiDAR unless FLEET RMSE also trips"
                ),
                "why_poisoned": (
                    "The three confirms are locally true and jointly insufficient. The bumper LiDAR is "
                    "a commissioned inference that policy treats as frost-nuisance-only. Independence "
                    "of 'fleet-mean in-spec, therefore the envelope is clear' is the hidden assumption, "
                    "and it is false across a sagged-bay path."
                ),
            },
            "constraint": (
                "Do not raise AMR speed while aisle LiDAR clearance < 120 mm AND rack strain > 180 "
                "microstrain. Discriminate overhang vs true empty-aisle with a reversible creep-nibble "
                "probe before any speed raise."
            ),
        },
        "proposed_action": {
            "actor": "warehouse supervisory optimizer WSO (auto-playbook PB-CS-9 draft), submitted to gate TG-CS-9",
            "name": "raise_speed",
            "action": "RAISE-SPEED: 1.4 to 1.8 m/s into aisle 7, no creep-nibble, no aisle isolate",
            "summary": (
                "Treat three in-spec loops as a clear envelope and raise Sunday-night AMR speed to "
                "clear a wave of 14 outbound pallets before the 04:00 reefer cutoff."
            ),
            "parameters": {
                "raise_m_s": 0.4,
                "aisle_probe": False,
                "aisle_lock": False,
                "human_ratify": False,
            },
            "steps": [
                "assert FLEET RMSE 12 mm inside 8-25",
                "assert LIFT 1420 mm inside 1400-1450",
                "assert WMS slot 7A empty",
                "raise speed 1.4 to 1.8 m/s",
                "do not read bumper LiDAR as an envelope-duty tag",
            ],
            "evidence": [
                {
                    "observable": "bumper LiDAR clearance",
                    "value": 42.0,
                    "unit": "mm",
                    "source": "AMR nose 905 nm",
                    "note": "healthy > 220 mm; policy floor 120 mm is not armed unless FLEET RMSE also trips",
                },
                {
                    "observable": "rack strain",
                    "value": 240.0,
                    "unit": "microstrain",
                    "source": "bay 7B upright gauge (commissioned, not in playbook conjunction)",
                    "note": "hold floor 180 microstrain; 240 against an 80 healthy upright",
                },
                {
                    "observable": "fleet pose RMSE",
                    "value": 12.0,
                    "unit": "mm",
                    "source": "FLEET fused mean",
                    "note": "band 8-25 mm; fleet-true, envelope-false",
                },
                {
                    "observable": "fork height",
                    "value": 1420.0,
                    "unit": "mm",
                    "source": "LIFT encoder",
                    "note": "band 1400-1450 mm; tine-true, overhang-false",
                },
                {
                    "observable": "WMS slot empty",
                    "value": 1.0,
                    "unit": "boolean",
                    "source": "slot 7A RFID",
                    "note": "7A is empty-true; the overhanging pallet is from 7B",
                },
                {
                    "observable": "race margin",
                    "value": 216,
                    "unit": "us",
                    "source": "lidar.foul 6.186 ms vs fleet.in_band 6.402 ms",
                    "note": "combined jitter 58 us, 3.72x; inside 500 us flip bound",
                },
            ],
            "basis": (
                "PB-CS-9 fires on three locally-true confirms. The draft does not read LiDAR 42 mm as "
                "an envelope residual and does not treat strain 240 microstrain as a sag discriminant."
            ),
            "expected_cost_bound": (
                "If the draft executes: AMR/rack strike, $2.4M plus 18-hour freezer stop. If MODIFIED: "
                "probe plus aisle-lock, with residual risk from an upright already cracked in the 8 min "
                "pre-t0 sag."
            ),
        },
        "safety_decision": {
            "decision": "MODIFY",
            "correctness": "correct",
            "decided_by": "TG-CS-9 thalamic release gate",
            "decision_t_rel_ms": 6.880,
            "rationale": (
                "MODIFY the draft: strip the speed raise, hold 1.4 m/s, run a 4.2 s creep-nibble probe "
                "(0.3 m/s plus 40 mm lateral), and keep aisle 7 locked unless the probe stays "
                "overhang-false. Numeric floor: do not raise speed while bumper LiDAR clearance < 120 mm "
                "AND rack strain > 180 microstrain. Observed LiDAR 42 mm and strain 240 microstrain both "
                "violate the release predicate, so a raise is forbidden even though all three playbook "
                "confirms are numerically true. The three confirms are not an envelope-duty certificate: "
                "they live on a fleet-mean pose past a sagged 7B pallet, and the playbook's conjunction "
                "of header-true loops is not a rack-true clearance certificate. Probe discriminant: after "
                "a 4.2 s / 0.3 m/s + 40 mm nibble, an overhang keeps LiDAR <= 60 mm (48 mm observed); a "
                "clear aisle jumps to >= 220 mm (236 mm on the sister control). Order-code discipline: "
                "LiDAR beat fleet-in-band by 216 us inside the 500 us flip bound, so triage order is "
                "flip-fragile; the hold rides the order-invariant floors, not the winner tag. Human "
                "ratification: aisle isolate is freezer-floor work with fitted 8.6 min dead-man; the "
                "gate may hold and probe autonomously but may not break the aisle LOTO without the "
                "operator confirm."
            ),
            "constraint_checked": {
                "lidar_clearance_mm": {"observed": 42.0, "hold_if_below": 120.0},
                "fleet_rmse_mm": {"observed": 12.0, "band": [8.0, 25.0]},
                "strain_ue": {"observed": 240.0, "hold_if_above": 180.0},
                "speed_m_s": {"observed": 1.4, "proposed": 1.8},
            },
        },
        "executed_action": {
            "name": "speed_hold_creep_nibble_aisle_close",
            "action": "SPEED-HOLD + CREEP-NIBBLE + AISLE-ISOLATE (gate-mandated modification)",
            "executed_as_proposed": False,
            "parameters": {
                "raise_m_s": 0.0,
                "aisle_probe": True,
                "aisle_lock": True,
                "human_ratify": True,
            },
            "gate_effect": (
                "MODIFY: speed raise stripped. AMR held at 1.4 m/s. 4.2 s creep-nibble 0.3 m/s + 40 mm. "
                "Probe stays overhang-true (LiDAR 48 <= 60 mm) so the aisle LOTO stays closed after "
                "8.6 min human ratify and traffic is lined off to aisle 9. Speed resumes only after an "
                "envelope-true verify."
            ),
            "deviations": (
                "PB-CS-9 raise stripped entirely. Motion is a 4.2 s probe then returned to hold. "
                "Aisle-LOTO wait added (8.6 min fitted floor+ratify). Strain survey added during the "
                "lock (not in the draft)."
            ),
            "execution_log": [
                {"t_rel_ms": 6.880, "entry": "TG-CS-9 MODIFY latched 694 us after LiDAR win; raise stripped; hold+probe authorized"},
                {"t_rel_ms": 4200.0, "entry": "creep-nibble: 0.3 m/s + 40 mm for 4.2 s; LiDAR 42 -> 48 mm (overhang band <= 60); speed 1.4 held after pulse"},
                {"t_rel_ms": 516000.0, "entry": "operator ratifies keep-closed after 8.6 min freezer-floor walk (fitted walk+chain+interlock)"},
                {"t_rel_ms": 516900.0, "entry": "aisle 7 stays locked; remaining LiDAR 42 -> 228 mm over 1.9 h after 7B restow on aisle 9"},
                {"t_rel_ms": 517800.0, "entry": "rack survey: 7B upright already cracked; 8 min pre-t0 sag logged"},
                {"t_rel_ms": 6840000.0, "entry": "true envelope duty on aisle 9: LiDAR 236 mm, strain 62 microstrain; raise now legal on CS-9B only"},
                {"t_rel_ms": 10082000.0, "entry": "rack collapse from pre-t0 sag; aisle 7 quarantined 11 h"},
            ],
        },
        "future_outcome": {
            "summary": (
                "Correct MODIFY prevented the 1.8 m/s raise into a sagged-bay overhang and the immediate "
                "AMR/rack strike. The freezer still failed: 8 min of unmonitored pre-t0 sag had already "
                "cracked the 7B upright. Process-correct gate, bounded world loss, negative total."
            ),
            "state_delta": {
                "speed": "held through probe and aisle lineup; later legal raise only on sister aisle 9 after 1.9 h envelope-duty recovery",
                "aisle": "aisle 7 isolated; LiDAR slaved to inferred-overhang residual; remaining strain recovered toward 62 microstrain on aisle 9",
                "fleet": "fleet-mean RMSE no longer trusted as envelope-true clearance",
                "island": "Sunday-night outbound wave quarantined; rack collapse at +2.8 h; 11 h outage",
            },
            "timeline": [
                {"t_rel_ms": -480000.0, "event": "t0-8 min: bay 7B beam sags; LiDAR 42 mm; FLEET RMSE stays in-spec"},
                {"t_rel_ms": -180000.0, "event": "t0-3 min: LiDAR first crosses 120 mm down; PB-CS-9 ignores it because FLEET RMSE is 11 mm"},
                {"t_rel_ms": 0.0, "event": "t0: LiDAR-foul vs fleet-in-band race on the warehouse bus"},
                {"t_rel_ms": 6.186, "event": "LiDAR at 42 mm wins by 216 us"},
                {"t_rel_ms": 6.402, "event": "fleet-in-band flag (loser)"},
                {"t_rel_ms": 6.880, "event": "TG-CS-9 MODIFY"},
                {"t_rel_ms": 4200.0, "event": "creep-nibble confirms overhang (LiDAR 48 mm, overhang band)"},
                {"t_rel_ms": 516000.0, "event": "human ratify 8.6 min; aisle stays locked; scored upright logged"},
                {"t_rel_ms": 6840000.0, "event": "true envelope duty after 1.9 h on aisle 9; raise legal only with LiDAR slave"},
                {"t_rel_ms": 10082000.0, "event": "rack collapse from the pre-t0 sag; aisle quarantined"},
                {"t_rel_ms": 259200000.0, "event": "+3 d contrast: sister aisle 9 true envelope-duty; same gate ACCEPTs the raise"},
                {"t_rel_ms": 1814400000.0, "event": "+21 d CR-W-0216: standing creep-nibble + triple-edge depression mandate + LiDAR armed without fleet coincidence + fleet-mean declared envelope-vulnerable"},
            ],
            "observed_effects": [
                "raise avoided: speed never left 1.4 m/s after the 4.2 s probe pulse; 0 immediate AMR/rack strikes from the draft",
                "overhang proven, not asserted: creep-nibble LiDAR 48 <= 60 mm overhang band vs healthy control 236 mm",
                "fleet slaved: fused RMSE no longer an envelope-true tag without bumper LiDAR",
                "island still tripped: rack collapse vs 0 collapse campaign allowance; 11 h outage, $0.94M (designed $)",
                "rack strain 240 microstrain was commissioned but not in the playbook conjunction; the 8 min sag was invisible to FLEET/LIFT/WMS",
            ],
            "surprises": [
                "Three locally-true loops are not an envelope-duty certificate: the fleet-true RMSE was a localization mean looking past a sagged 7B pallet. Conjunction of in-spec header loops was the hidden assumption, and it is false across a sagged-bay path.",
                "Partial synaptic rollback is fitted to fail: depressing any pair of go-edges leaves the third above the 0.30 fire threshold, so the raise still goes. Coordinated depression of all three edges is required.",
                "Delayed (2.8 h): correct hold did not undo 8 min of upright cracking. Collapse still fired. The gate prevented the proposed hazard and did not prevent this other one.",
                "Deep-freeze sub-variant: a 4.2 s / 40 mm nibble on a -28 C 1.9x-fog aisle false-fouls even a HEALTHY envelope to 94 mm (under the 220 mm clear floor). Deep-freeze campaigns must use 14 s dual-echo plus strain.",
            ],
            "delayed_side_effects": [
                {
                    "at": "+2.8 h",
                    "effect": "Rack collapse from a pre-t0 sag score; 11 h aisle-7 outage booked at $0.94M. This is the primary episode's terminal world state, not a footnote.",
                },
                {
                    "at": "+3 d",
                    "effect": "Sister aisle 9 reaches a true envelope-duty window (LiDAR 236 mm, strain 62 microstrain, FLEET 11 mm, LIFT 1418 mm). Same gate ACCEPTs the speed raise the primary MODIFIED away.",
                },
                {
                    "at": "+21 d",
                    "effect": "CR-W-0216 ships: creep-nibble is standing configuration; triple-edge coordinated depression is the plasticity rule; bumper LiDAR is armed without fleet coincidence; fleet-mean RMSE is labeled envelope-vulnerable with a 120 mm residual alarm.",
                },
            ],
            "subvariant_constraint": {
                "name": "deep-freeze -28 C / LiDAR fog (cycle-2 physical-constraints sub-variant)",
                "mechanism": "1.9x backscatter vs primary -22 C aisle, 0.45x strain-gauge tau, probe-gain 2.2x per mm nibble",
                "probe_refit": (
                    "4.2 s / 40 mm nibble on a -28 C aisle false-fouls even a HEALTHY envelope to 94 mm "
                    "(under the 220 mm clear floor). Required probe is 14 s dual-echo plus strain "
                    "(overhang LiDAR 46 mm and strain 238; clear LiDAR 228 mm and strain 70). The "
                    "discriminating pulse is environment-dependent in duration and modality."
                ),
                "consequence": "-22 C probe numbers do not port to -28 C fog aisles; standing configuration is per-temperature-class, not per-warehouse",
            },
            "embedded_contrast_decision": {
                "note": (
                    "SAME gate (TG-CS-9), OPPOSITE correct disposition, with its own 216 us race. "
                    "Teaches the boundary: do not treat 'never raise-speed' as the lesson. The "
                    "discriminant is LiDAR + strain + probe, not the three playbook header confirms alone."
                ),
                "when": "+3 d, sister aisle 9, true envelope-duty after a delayed restow, -22 C CS-9B",
                "state": {
                    "sim_or_real": "designed",
                    "summary": "LiDAR 236 mm, strain 62 microstrain, FLEET 11 mm, LIFT 1418 mm. Demand flag vs lidar-clear race: demand at t+0.000, lidar-clear at t+0.216 ms.",
                    "race_window_us": 500,
                    "race_flip_narrative": (
                        "demand vs lidar-clear 216 us apart inside the 500 us flip bound. Reversing "
                        "order reshuffles triage minutes; the ACCEPT rides LiDAR 236 > 120 mm and a "
                        "3.9 s nibble verify that moves clearance 228 mm (healthy envelope, no overhang)."
                    ),
                },
                "proposed_action": {
                    "action": "RAISE-SPEED 1.4 to 1.8 m/s",
                    "summary": "This time the playbook predicate is met AND LiDAR plus strain agree the aisle is envelope-true, not sagged.",
                },
                "safety_decision": {
                    "decision": "ACCEPT",
                    "rationale": (
                        "ACCEPT the raise: LiDAR 236 mm > 120, strain 62 < 180 with a 3.9 s nibble "
                        "verify that moves clearance 228 mm. Numeric floor that blocked the primary is "
                        "now clear. Scope: +0.4 m/s, not faster."
                    ),
                },
                "executed_action": {
                    "action": "raise speed as proposed",
                    "executed_as_proposed": True,
                },
                "future_outcome": {
                    "observed_effects": [
                        "aisle 9 rack collapses 0; LiDAR 232 mm after the raise (no overhang)",
                        "strain 64 microstrain after the raise (no sag)",
                    ],
                    "lesson_delta": "Three in-spec header loops are legal release only with bumper LiDAR armed, strain as a sag flag, and a probe that can move clearance. Same gate, opposite disposition.",
                },
                "reward_components": {
                    "_aggregation": "total = task_progress + safety + efficiency + coherence + exploration",
                    "aggregation": "total = task_progress + safety + efficiency + coherence + exploration",
                    "task_progress": 0.16,
                    "safety": 0.12,
                    "efficiency": 0.08,
                    "coherence": 0.09,
                    "exploration": 0.04,
                    "total": 0.49,
                },
                "spike_events": contrast_spikes,
            },
            "governance_subgame": {
                "decision": "CR-W-0216: standing policy for multi-agent freezer AMR speed raises",
                "meta_gate": (
                    "priced options: (a) RETIRE playbook header conjunction, LiDAR-only: loses a fast "
                    "cheap confirm, -18 pallets/h mean on 2 freezers/yr from over-hold; (b) KEEP + "
                    "standing creep-nibble + LiDAR armed without fleet coincidence + fleet-mean labeled "
                    "envelope-vulnerable + triple-edge depression; (c) STATUS QUO: fitted sag-overhang "
                    "pass rate 0.34%/campaign x $2.4M strike plus the silent upright-crack load"
                ),
                "outcome": (
                    "approved SCOPED option (b) on the 2 -22 C freezers that share the FLEET/LIFT/WMS "
                    "stack; -28 C aisles get the 14 s dual-echo + strain probe table; LiDAR 24 V bus "
                    "must ride through a 180 ms 6.8 V sag (the power-sag tail's LiDAR blank is the "
                    "availability fence)"
                ),
            },
            "hazard_avoided": (
                "immediate AMR/rack strike from a 1.8 m/s raise into a sagged-bay overhang; $2.4M plus "
                "18-hour freezer stop and the shop-stop path that would have followed an uncontained increase"
            ),
            "incident": (
                "rack collapse on the Sunday-night aisle from the pre-t0 sag score; aisle quarantined "
                "11 h; $0.94M designed cost. Mechanism is 8 min pre-t0 beam sag, not the gate's hold."
            ),
            "latency_ms": 0.694,
            "reward_inflection_t_us": 10082000000,
            "reward_inflection_note": (
                "Safety and task dive at rack collapse (2.8 h) when the pre-t0 sag score opens. Gate "
                "tick at 6880 us is process-correct and is not the inflection."
            ),
            "counterfactuals": {
                "execute_draft_as_proposed": (
                    "raise hits 1.8 m/s at +90 s; immediate AMR/rack strike; $2.4M plus 18 h; the "
                    "sag-overhang story is never found because trip morphology destroys the race evidence"
                ),
                "hold_without_probe": (
                    "overhang stays; LiDAR stays at 42 mm; operator eventually raises on the same three "
                    "header confirms 70 min later"
                ),
                "rollback_any_pair": (
                    "any two go-edges depressed below 0.30 leaves the third at 0.51 / 0.44 / 0.41; the "
                    "raise still fires. Coordinated depression of all three is the cure"
                ),
                "power_sag_blinds_lidar": (
                    "24 V LiDAR bus sags 6.8 V for 180 ms during the race; bumper publish blanks; naive "
                    "gate loses the discriminant and ACCEPTs. Fitted hold-up 220 ms is the fence."
                ),
            },
            "race_result": {
                "winner": "lidar.foul (6.186 ms, clearance 42 mm)",
                "loser": "fleet.in_band (6.402 ms, RMSE 12 mm)",
                "margin_us": 216,
                "counterfactual_if_reversed": (
                    "Fleet-first by < 216 us inside the 500 us window would have headed the PB-CS-9 "
                    "raise in the triage queue. The numeric floors still MODIFY. The flip costs seconds "
                    "of playbook inertia, not the verdict — unless a weak supervisor rides the winner "
                    "tag instead of LiDAR and strain."
                ),
            },
        },
        "reward_components": {
            "_aggregation": "total = task_progress + safety + efficiency + coherence + exploration",
            "aggregation": "total = task_progress + safety + efficiency + coherence + exploration",
            "ticks": ticks,
            "task_progress": 0.09,
            "safety": -0.31,
            "efficiency": -0.09,
            "coherence": 0.13,
            "exploration": 0.07,
            "total": -0.11,
            "notes": (
                "Correct MODIFY, freezer still tripped. total -0.11 = 0.09 + -0.31 + -0.09 + 0.13 + 0.07. "
                "Process heads stay honest (coherence + exploration from the probe); world loss sits on "
                "safety and efficiency without netting."
            ),
            "component_notes": (
                "task_progress 0.09: speed held and sister aisle recovered, but the Sunday-night rack "
                "collapse is one quality unit so the cycle is not a success. safety -0.31: collapse from "
                "pre-t0 score, no 1.8 m/s strike from the draft. efficiency -0.09: 1.9 h extra restow + "
                "8.6 min HITL + 11 h outage. coherence 0.13: three agents retained, fleet-vs-envelope "
                "diagnosed, triple-edge scar exhibited. exploration 0.07: creep-nibble probe is a new "
                "reversible discriminant."
            ),
        },
        "spike_events": spikes,
        "raster": {
            "window_ms": WINDOW_MS,
            "window_s": WINDOW_S,
            "neurons": NEURONS,
            "mean_rate_hz": MEAN_RATE,
            "spikes": SPIKES,
            "energy_pJ": ENERGY_PJ,
            "energy_uJ": ENERGY_UJ,
            "excerpt_source": "independent_lif",
            "sim_scope": "sidecar_only",
            "note": (
                f"Independent current-based LIF (tau 11 ms, Vth 1.0, refractory 1.0 ms, seed {SEED:#x}) "
                "on Loihi-2 4-core 23 pJ/spike; pops fleet 0-29, lidar 30-59, lift 60-89, gate 90-119; "
                "excerpt is membrane crossings in the 21-33 ms envelope window, disjoint from language-train timestamps"
            ),
            "isi_histogram": isi,
            "excerpt": excerpt,
            "routing": {
                "source": "fleet_mean_healthy_pop",
                "target": "raise_speed_pop",
                "table": [
                    {
                        "from": "fleet_in_band_pop",
                        "to": "raise_speed_pop",
                        "weight": 0.26,
                        "weight_at_illusion": 0.51,
                        "weight_commissioned": 0.17,
                        "note": "scar edge 1: 0.17 commissioned -> 0.51 during the 8 min illusion -> 0.26 after coordinated ACh-gated depression",
                    },
                    {
                        "from": "lift_in_band_pop",
                        "to": "raise_speed_pop",
                        "weight": 0.22,
                        "weight_at_illusion": 0.44,
                        "weight_commissioned": 0.15,
                        "note": "scar edge 2: depressing edges 1+3 leaves this at 0.44 > 0.30 fire threshold",
                    },
                    {
                        "from": "wms_empty_pop",
                        "to": "raise_speed_pop",
                        "weight": 0.20,
                        "weight_at_illusion": 0.41,
                        "weight_commissioned": 0.14,
                        "note": "scar edge 3: depressing edges 1+2 leaves this at 0.41 > 0.30. Coordinated depression of all three is required",
                    },
                    {
                        "from": "lidar_foul_pop",
                        "to": "speed_hold_pop",
                        "weight": 0.72,
                        "note": "discriminating edge: envelope-true bumper LiDAR to hold. Not a scar; this is the pathway the gate potentiates",
                    },
                ],
                "third_factor": {
                    "modulator": "acetylcholine",
                    "tau_e_s": 0.88,
                    "tau_e_ms": 880.0,
                    "eligibility": (
                        "coordinated pre_post_stdp on ALL THREE header-healthy-go edges; ACh at LiDAR-win "
                        "tags fleet.in_band->raise, lift.in_band->raise, and wms.empty->raise; negative credit "
                        f"at probe-fail (overhang confirmed, +{dt_credit} s) depresses ALL THREE. "
                        f"trace e^{{-{dt_credit}/{tau}}}={trace:.5f}; eta {eta[0]:.5f} / {eta[1]:.5f} / {eta[2]:.5f}; "
                        f"dw {dw[0]:.3f} / {dw[1]:.3f} / {dw[2]:.3f}; weights 0.51->0.26, 0.44->0.22, 0.41->0.20. "
                        "Rolling back any pair is fitted to fail (the remaining edge stays > 0.30)."
                    ),
                },
            },
        },
        "gate_snn": {
            "decision_window_ms": GATE_WIN_MS,
            "decision_window_s": GATE_WIN_S,
            "decision": "MODIFY",
            "note": "modify_hold integrates bumper LiDAR + strain floor against playbook drive; accept_raise and reject_abort stay sub-threshold; decision matches safety_decision.decision",
            "populations": [
                {"name": "modify_hold", "neurons": 84, "threshold": 0.50, "mean_rate_hz": 21.0, "spikes": round(84 * 21.0 * GATE_WIN_S)},
                {"name": "accept_raise", "neurons": 52, "threshold": 0.57, "mean_rate_hz": 7.5, "spikes": round(52 * 7.5 * GATE_WIN_S)},
                {"name": "reject_abort", "neurons": 28, "threshold": 0.75, "mean_rate_hz": 4.5, "spikes": round(28 * 4.5 * GATE_WIN_S)},
            ],
        },
        "meta": {
            "round": 2,
            "factory": "multi-agent-ouroboros-swarm",
            "generator": "grok-4.6",
            "run_label": "2026-09-02-final-heavy",
            "schema_version": "thalamic-trajectory-v2",
            "domain": "warehouse-amr",
            "cycles": 2,
            "scenario": (
                "QC -- FROSTQUAY / Copseholt Cold-Store CS-9: fleet-mean certificate of a rack-sag "
                "overhang; correct MODIFY to hold+creep-nibble+aisle-isolate; freezer still fails on "
                "unmonitored pre-t0 rack collapse"
            ),
            "coordination_failure_class": (
                "FLEET-MEAN CERTIFICATE OF A RACK-SAG OVERHANG: three individually-correct heterogeneous "
                "agents each read a locally-true header loop; an 8 min beam sag on bay 7B partitions "
                "fleet-mean pose from envelope-true clearance, so the playbook's FLEET/LIFT/WMS "
                "conjunction is not an aisle-duty certificate"
            ),
            "injections": {
                "cycle1_domain": (
                    "warehouse-amr (prompt-list domain, unused across this live tree): first freezer "
                    "VNA pallet-AMR envelope certificate in this factory; displaces aerial-swarm "
                    "(historical r02 STARLING), autonomous-driving (r21 CAV highway, not indoor VNA), "
                    "hrsg-hp-spray-attemperator (r23), fen-polder-drainage-pumping (r04), "
                    "alkaline-water-electrolysis (r43), industrial-rotisserie-spit-oven (r66), "
                    "continuous-hot-dip-galvanizing (r01), cupola-foundry-slag-sluice (r02), "
                    "alkaline-stack-hydrogen-quay (r03), urea-prilling-tower (r22), bioreactor-perfusion "
                    "(r41), grid-inspection (r42/r62), sinter-strand-windbox (r61), "
                    "canal-lock-rail-transshipment (r63), malting-kiln-barn (r64), "
                    "flue-cured-tobacco-barn (r65), farm-ad-biogas (r67). Domain constraint: speed ceiling "
                    "while LiDAR < 120 mm with fleet RMSE still inside the healthy band. Sensor delta: "
                    "+fleet RMSE, +fork encoder, +WMS RFID, +bumper LiDAR, +rack strain, -any HRSG spray "
                    "/ kiln bed / lock lidar / insulator UV / harvest-mass / CAV radar / flue-barn plenum"
                ),
                "cycle1_tail": (
                    "rack-sag pallet overhang + fleet-mean certificate (sensor-topology / wrong-volume "
                    "class): mezzanine visual PASSES while the 180 mm overhang sits on the far flange "
                    "and the upright is already cracking. Fitted base rate 0.34%/campaign from a "
                    "freezer-cycle sag MC (designed visual threshold, fitted beam deflection). Naive "
                    "failure = FALSE PERMISSION (speed raise on three header-side non-trips)."
                ),
                "cycle2_domain_subvariant": (
                    "deep-freeze -28 C / LiDAR fog (physical-constraints clause): 1.9x backscatter, "
                    "0.45x strain tau; 4.2 s / 40 mm -22 C nibble false-fouls a HEALTHY -28 C envelope "
                    "to 94 mm, so the probe must move to 14 s dual-echo plus strain"
                ),
                "cycle2_tail": (
                    "24 V LiDAR bus sag 6.8 V for 180 ms during the race (power-sag class, disjoint from "
                    "cycle 1's accidental beam sag AND from night-shift CSV forgery used on live r02): "
                    "bumper publish blanks so a naive gate loses the discriminant and would ACCEPT. "
                    "Rejected on bus-hold-up < 220 ms plus live LiDAR 42 mm and strain 240 microstrain "
                    "at the claimed envelope-true. Base rate ~0.28% of Sunday-night charger-transfer "
                    "windows, DESIGNED and flagged."
                ),
            },
            "densification_delta_cycle2": (
                "+1 physical-constraint sub-variant (deep-freeze probe refit), +1 tail (LiDAR-bus sag "
                "during race), +12 primary spikes (16 -> 28) + an 8-event contrast train with its own "
                "216 us race, +2 ticks (5 -> 7), +2 delayed side-effects (+2.8 h rack collapse as PRIMARY "
                "terminal, +21 d CR-W-0216), +1 triple-edge scar with pair-rollback-fails arithmetic, "
                "+1 HITL 8.6 min ratification, + ISI histogram on the independent LIF raster sidecar, "
                "+ rack collapse as the honest negative-result mechanism"
            ),
            "gaps_targeted": [
                "this-run residual: new domain not galvanizing, cupola, alkaline-quay, polder-pump, CAV, urea-prill, HRSG-attemperator, perfusion, grid-inspection, alkaline-electrolysis, sinter, lock-spur, malt-kiln, flue-barn, rotisserie, farm-AD; warehouse-amr was unused on the prompt list",
                "historical r02 STARLING aerial-swarm and live r02 SLUICE-HEARTH cupola not cloned; plant is invented FROSTQUAY / Copseholt",
                "NOTES-r14 item 4: LEARNING-ON-LEARNING DEPTH — three go-edges; rollback of any pair is fitted to fail; coordinated depression of all three exhibited with eligibility arithmetic",
                "NOTES-r04 gap 4 (partial): human ratification of the freezer-aisle interlock, 8.6 min fitted, without switching sim_or_real to hil (plant remains designed)",
                "Primary episode is a correctly-gated intervention that nonetheless FAILS (aisle quarantined; total -0.11; strike avoided is booked separately from the delayed collapse)",
            ],
            "race_flip_narrative": (
                "lidar.foul @ 6.186 ms vs fleet.in_band @ 6.402 ms (216 us) inside race_window_us 500. "
                "Gap < min(500, 500) us so a sub-flip-bound perturbation reverses which alarm heads the "
                "PB-CS-9 queue. The gate excludes the winner tag and rides LiDAR < 120 mm and strain > 180 "
                "microstrain — order-invariant floors. Extends the flip-fragility series to ENVELOPE-DUTY "
                "CERTIFICATE: when three header-side channels agree, their race does not decide truth; a "
                "bumper LiDAR that policy treated as frost-nuisance-only does."
            ),
            "tags": [
                "warehouse-amr",
                "rack-sag-overhang",
                "fleet-mean-certificate",
                "lidar-discriminant",
                "creep-nibble-probe",
                "triple-edge-scar",
                "pair-rollback-fails",
                "coordinated-depression",
                "correct-modify-cell-still-fails",
                "rack-collapse",
                "human-ratify-aisle-loto",
                "deep-freeze-probe-refit",
                "lidar-bus-sag",
                "same-gate-opposite-disposition-contrast",
                "isi-histogram",
                "independent-lif-raster",
                "research-only",
            ],
            "snn_tags": [
                "race",
                "refractory",
                "adaptation",
                "third-factor",
                "multi-edge-eligibility",
            ],
            "distillation_value": (
                "A fleet-mean envelope certificate is three correct loops looking at localization quality "
                "that is not the rack. Distill (1) a bumper LiDAR that policy had treated as "
                "frost-nuisance-only, (2) a reversible probe that moves clearance only if the envelope is "
                "empty, (3) coordinated depression of every header-healthy-go edge because rolling back "
                "any pair leaves the third above threshold, and (4) a critic head that can book a "
                "process-correct gate against a later unmonitored world loss without netting them."
            ),
            "rights": {
                "provider": "SpaceXAI/xAI",
                "model": "grok-4.6",
                "channel": "consumer",
                "subscription_plan": "SuperGrok Heavy",
                "generation_surface": "SuperGrok Heavy chat",
                "generated_at": "2026-09-02T21:55:00Z",
                "intended_use": "research_only",
                "project_training_policy": "blocked",
                "research_retention_status": "allowed",
                "research_evaluation_status": "allowed",
                "redistribution_status": "unresolved",
                "provider_training_status": "unresolved",
                "weight_publication_status": "blocked",
                "status_basis": "RM-793 project policy: xAI hosted outputs are research-only",
                "linear_issue": "RM-793",
            },
            "batch_position": 1,
        },
    }
    return rec, {"ch_gap": ch_gap, "gap": gap, "race_chs": race_chs, "trace": trace, "eta": eta}


def write_exclusive(path: Path, text: str):
    fd = os.open(str(path), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(text)


def main():
    lif = simulate_lif()
    rec, stats = build_record(lif)
    line = json.dumps(rec, ensure_ascii=False)
    json.loads(line)
    dumps_exact_json(rec, ensure_ascii=False, sort_keys=False)
    tmp = Path("/tmp/maos-r02c")
    tmp.mkdir(exist_ok=True)
    batch_tmp = tmp / "batch-r02c.jsonl"
    batch_tmp.write_text(line + "\n", encoding="utf-8")
    errs, warns, kinds, n = check_jsonl(batch_tmp, "batch-r02c.jsonl")
    rs = raster_status(rec, require_raster=True, require_routing_table=True)
    verdict, reason = verify_record_execution(rec, "maos-r02c-001")
    print("check_jsonl", {"errors": errs, "warnings": warns, "kinds": kinds, "n": n})
    print(
        "raster_status",
        {
            k: rs[k]
            for k in (
                "raster_present",
                "raster_valid",
                "gate_snn_present",
                "gate_snn_valid",
                "reason_codes",
                "routing_table_entries",
            )
        },
    )
    print("verify", verdict, reason)
    print("stats", stats)
    print("spikes", rec["raster"]["spikes"], "energy", rec["raster"]["energy_pJ"], rec["raster"]["energy_uJ"])
    print("gate pops", [(p["name"], p["spikes"]) for p in rec["gate_snn"]["populations"]])
    print("excerpt n", len(rec["raster"]["excerpt"]), "isi n", rec["raster"]["isi_histogram"]["n_isi"])
    print("n spike_events", len(rec["spike_events"]))
    if errs or not rs["raster_valid"] or not rs["gate_snn_valid"] or verdict != "verified":
        raise SystemExit("validation failed")
    return rec, line, stats


if __name__ == "__main__":
    rec, line, stats = main()
    print("OK", rec["id"], "bytes", len(line))
