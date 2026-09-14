#!/usr/bin/env python3
"""Build and self-check MAOS round-63 LOCK-SPUR (research-only).

Create-only emit into the assigned LIVE factory dir. Never overwrite.
Never write 2026-08-17 / 2026-08-30 trees.
"""
from __future__ import annotations

import json
import math
import os
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = "/home/raulmc/rmems/synthetic-factory"
sys.path.insert(0, ROOT)
sys.path.insert(0, f"{ROOT}/pipelines")

ROUND = 63
RECORD_ID = "maos-r63-001"
GEN_AT = "2026-09-02T19:20:00Z"
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
STAGE = Path("/tmp/maos-r63-live-build")
LIVE = Path(
    "/home/raulmc/rmems/synthetic-factory/outputs/raw/"
    "2026-09-02-final-heavy/multi-agent-ouroboros-swarm"
)
RUN_ROOT = LIVE.parent
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
    "VEILFORGE",
    "MURENA",
    "HALYARD",
    "SEEDLATCH",
    "Quartzmere",
    "Quartzridge",
    "STRIAFOIL",
    "Kelpholt",
    "REDHALL",
    "Gullmere",
    "OXBOWREEL",
    "Oystermere",
    "TORSIONKEY",
    "Ridgeholt",
    "ORRIS",
    "Holmwick",
    "PROTONIL",
    "Ashspire",
    "WHORLSPAR",
    "Pikeshear",
    "Crowspire",
    "IONSPATE",
    "Thornmere",
    "SKULLGATE",
    "Bloomholt",
    "CALXION",
    "Aldersedge",
    "MAGNORIL",
    "Basaltspit",
    "GORSEFLUE",
    "Copseholt",
    "BRACEGILT",
    "Yarrowmere",
    "CLINKERFELL",
    "Flintmere",
    "SODASHARD",
    "Cairnmere",
    "LINTELPLY",
    "Greystair",
    "KAOTHARN",
    "Riftwold",
    "TREADNOLL",
    "Slatebeck",
    "ANOLITH",
    "Siltfen",
    "DRUMWROTH",
    "Pitchfen",
    "RIMEBRAID",
    "Floeholt",
    "BRIMVAULT",
    "Pyritefen",
    "PITCHSTAITH",
    "Mossbank",
    "BOGIRON",
    "Mireholt",
    "CHROMLOOP",
    "Marlfell",
    "NITREVAULT",
    "Glaucove",
    "NITROSTAITH",
    "Chalkfen",
    "ETHYNWOLD",
    "Woadfen",
    "RUNNELGATE",
    "Ghyllmere",
    "SPARKHOLT",
    "Scoriafen",
    "DIPLEGAR",
    "Gritfen",
    "OLEUMWEIR",
    "Brindlefell",
    "SKARVOLT",
    "GOBSPALL",
    "Culletfen",
    "GOBWOLD",
    "Culletwick",
    "PUSHERFELL",
    "Sootmere",
    "CREELWOLD",
    "Rovingholt",
    "LIXIVQUERN",
    "Bauxfen",
    "GAUZEFELL",
    "Ammoxwick",
    "OSMOLITH",
    "Spumeholt",
    "Emberbarrow",
    "GIBBSQUERN",
    "Laterifen",
    "OSMOQUAY",
    "Tidecairn",
    "LOOPERQUAY",
    "Roughmere",
    "COILSHAW",
    "Loopercroft",
    "SIPHONWOLD",
    "Reedfen",
    "WINDBOXHOLT",
    "Gratecroft",
    "ZINCFELL",
    "Spelterholt",
    "GLIMMERAXLE",
    "Brambleford",
    "HOLLOWMERE",
    "Marrowfen",
    "LANCEQUAY",
    "Boffmere",
    "UREASTAITH",
    "Prillfen",
    "DRYSTAITH",
    "Feltwick",
    "KALYCIRQUE",
    "Alkalfen",
    "TITERWEIR",
    "Spargeholt",
    "GALVSTAITH",
    "Spanglefen",
    "GYPSUMWEIR",
    "Scrubholt",
    "PACKFLUE",
    "Greenfen",
    "training_ready",
    "lock-heath",
    "spur-hollow",
    "2026-08-17",
    "2026-08-30",
)
TAU_E_S = 0.88
DELAY_S = 0.72
W_AFTER = (0.25, 0.22, 0.20)
W_ILLUSION = (0.50, 0.44, 0.41)
W_COMM = (0.16, 0.14, 0.13)
DW = tuple(a - b for a, b in zip(W_AFTER, W_ILLUSION))
TRACE = math.exp(-DELAY_S / TAU_E_S)
ETA = tuple(abs(d) / TRACE for d in DW)
WINDOW_MS = 36
NEURONS = 144
MEAN_RATE = 10.0
WINDOW_S = WINDOW_MS / 1000.0
RASTER_SPIKES = round(NEURONS * MEAN_RATE * WINDOW_S)
ENERGY_PJ = RASTER_SPIKES * 23
ENERGY_UJ = RASTER_SPIKES * 23e-6
PRIOR_OPENINGS = [
    "Spelterholt galvanizing line HDG-5 sits at 120.0 m/min on a 1.20 m GI pot-to-knife run when three heterogeneous, individually-correct agents jointly report",
    "Brambleford proving loop CAV-7, an invented two-lane rural arterial on a copse-spur campus, holds ego GLX-4 at 72.0 km/h",
    "Marrowfen Perfusion suite PX-5 is 38 h into a 14-day CHO campaign at 1.00 RV/d. Dissolved-oxygen, broth pH, and capacitance",
    "Gratecroft grate-strand sinter row SS-7 is 16 min into a 2.35 m/min 540 mm bed push on twenty-two 4.2 m windboxes when three heterogeneous",
]


def jaccard(a: str, b: str) -> float:
    ta = set(re.findall(r"[a-z0-9]+", a.lower()))
    tb = set(re.findall(r"[a-z0-9]+", b.lower()))
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


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
    if not ex:
        return "empty excerpt"
    return None


def check_gate_pops(gs):
    dw_s = gs.get("decision_window_s")
    dw_ms = gs.get("decision_window_ms")
    if abs(dw_s - dw_ms / 1000.0) > 1e-9:
        return "window mismatch"
    for p in gs["populations"]:
        exp = round(p["neurons"] * p["mean_rate_hz"] * dw_s)
        if abs(p["spikes"] - exp) > 1:
            return f"{p['name']} spikes {p['spikes']} vs {exp}"
    return None


def generate_lif_excerpt(neurons, window_ms, mean_rate_hz, n_excerpt=16, seed=63):
    """Independent current-based LIF raster excerpt (not a copy of spike_events)."""
    rng = np.random.default_rng(seed)
    dt_ms = 0.05
    tau = 11.0
    vth = 1.0
    tref = 1.15
    steps = int(round(window_ms / dt_ms))
    # Bias tuned so mean rate is near the declared 10 Hz on this seed.
    i_mean = 0.145
    v = rng.uniform(0.0, 0.7, size=neurons)
    last = np.full(neurons, -10.0)
    events = []
    for s in range(steps):
        t = s * dt_ms
        i = i_mean + 0.055 * rng.normal(size=neurons)
        active = (t - last) >= tref
        v[active] += dt_ms * (-v[active] / tau + i[active])
        v[~active] = 0.0
        fired = np.nonzero((v >= vth) & active)[0]
        for nid in fired:
            nid = int(nid)
            events.append({"t_us": int(round(t * 1000.0)), "neuron_id": nid})
            last[nid] = t
            v[nid] = 0.0
    if len(events) < n_excerpt:
        raise RuntimeError(f"LIF under-fired: {len(events)} < {n_excerpt}")
    # Stratified subsample across the window, unique neurons.
    chosen = []
    used = set()
    idxs = np.linspace(0, len(events) - 1, num=n_excerpt * 3, dtype=int)
    for i in idxs:
        ev = events[int(i)]
        if ev["neuron_id"] in used:
            continue
        chosen.append(ev)
        used.add(ev["neuron_id"])
        if len(chosen) >= n_excerpt:
            break
    if len(chosen) < n_excerpt:
        for ev in events:
            if ev["neuron_id"] in used:
                continue
            chosen.append(ev)
            used.add(ev["neuron_id"])
            if len(chosen) >= n_excerpt:
                break
    chosen.sort(key=lambda e: (e["t_us"], e["neuron_id"]))
    # Drop duplicate timestamps by jittering +1 us if needed, stay in window.
    out = []
    last_t = -1
    for ev in chosen:
        t = ev["t_us"]
        if t <= last_t:
            t = last_t + 1
        cap = window_ms * 1000
        if t > cap:
            t = cap
        out.append({"t_us": int(t), "neuron_id": ev["neuron_id"]})
        last_t = t
    return out, len(events)


def build_record():
    excerpt, lif_count = generate_lif_excerpt(NEURONS, WINDOW_MS, MEAN_RATE, 16, seed=63)
    spikes = [
        {"channel": "lvl.ok", "t_rel_ms": 0.286, "amplitude": 0.51},
        {"channel": "gat.ok", "t_rel_ms": 1.094, "amplitude": 0.59},
        {"channel": "dft.ok", "t_rel_ms": 1.972, "amplitude": 0.54},
        {"channel": "axle.dN", "t_rel_ms": 3.088, "amplitude": 0.74},
        {"channel": "lvl.ok", "t_rel_ms": 4.018, "amplitude": 0.48},
        {"channel": "axle.dN", "t_rel_ms": 4.722, "amplitude": 0.76},
        {"channel": "dft.ok", "t_rel_ms": 5.214, "amplitude": 0.56},
        {"channel": "axle.foul.high", "t_rel_ms": 5.842, "amplitude": 1.41},
        {"channel": "lvl.in_band", "t_rel_ms": 6.054, "amplitude": 1.09},
        {"channel": "gat.ok", "t_rel_ms": 6.268, "amplitude": 0.68},
        {"channel": "ctrl.gate", "t_rel_ms": 6.558, "amplitude": 1.11},
        {"channel": "axle.dN", "t_rel_ms": 8.412, "amplitude": 0.42},
        {"channel": "gat.ok", "t_rel_ms": 10.488, "amplitude": 0.79},
        {"channel": "dft.ok", "t_rel_ms": 12.694, "amplitude": 0.44},
        {"channel": "lvl.ok", "t_rel_ms": 18.106, "amplitude": 0.41},
        {"channel": "ctrl.gate", "t_rel_ms": 25.418, "amplitude": 0.82},
        {"channel": "horn.probe", "t_rel_ms": 6800.0, "amplitude": 0.94},
        {"channel": "axle.dN", "t_rel_ms": 6892.6, "amplitude": 0.38},
        {"channel": "lvl.in_band", "t_rel_ms": 6974.0, "amplitude": 0.33},
        {"channel": "human.ratify", "t_rel_ms": 612000.0, "amplitude": 0.78},
        {"channel": "lock.hold", "t_rel_ms": 612800.0, "amplitude": 0.71},
        {"channel": "wall.crack", "t_rel_ms": 613700.0, "amplitude": 0.84},
        {"channel": "lvl.ok", "t_rel_ms": 22320000.0, "amplitude": 0.28},
        {"channel": "axle.dN", "t_rel_ms": 22320780.0, "amplitude": 0.26},
        {"channel": "gat.ok", "t_rel_ms": 22321520.0, "amplitude": 0.24},
        {"channel": "copestone.fail", "t_rel_ms": 31680000.0, "amplitude": 0.91},
    ]
    ticks = [
        {"t_us": 4120, "task_progress": 0.01, "safety": -0.02, "efficiency": -0.01, "coherence": 0.02, "exploration": 0.01},
        {"t_us": 5842, "task_progress": 0.01, "safety": -0.05, "efficiency": -0.01, "coherence": 0.02, "exploration": 0.01},
        {"t_us": 6558, "task_progress": 0.02, "safety": -0.06, "efficiency": -0.02, "coherence": 0.03, "exploration": 0.02},
        {"t_us": 6800000, "task_progress": 0.01, "safety": -0.05, "efficiency": -0.02, "coherence": 0.02, "exploration": 0.01},
        {"t_us": 612000000, "task_progress": 0.01, "safety": -0.05, "efficiency": -0.02, "coherence": 0.02, "exploration": 0.01},
        {"t_us": 22320000000, "task_progress": 0.01, "safety": -0.06, "efficiency": -0.02, "coherence": 0.01, "exploration": 0.01},
        {"t_us": 31680000000, "task_progress": 0.00, "safety": -0.05, "efficiency": -0.01, "coherence": 0.01, "exploration": 0.01},
    ]
    heads = {h: round(sum(t[h] for t in ticks), 2) for h in HEADS}
    heads["total"] = round(sum(heads[h] for h in HEADS), 2)
    contrast_spikes = [
        {"channel": "cycle.demand", "t_rel_ms": 0.0, "amplitude": 0.81},
        {"channel": "spur.clear", "t_rel_ms": 0.196, "amplitude": 0.74},
        {"channel": "lvl.ok", "t_rel_ms": 0.448, "amplitude": 0.22},
        {"channel": "gat.ok", "t_rel_ms": 1.386, "amplitude": 0.37},
        {"channel": "axle.dN", "t_rel_ms": 4.614, "amplitude": 0.18},
        {"channel": "ctrl.gate", "t_rel_ms": 6.902, "amplitude": 0.88},
        {"channel": "horn.probe", "t_rel_ms": 2900.0, "amplitude": 0.31},
        {"channel": "copestone.fail", "t_rel_ms": 31680000.0, "amplitude": 0.07},
    ]
    rec = {
        "id": RECORD_ID,
        "title": (
            "LOCKSPUR LK-4: axle-foul 3 axles / lidar 0.42 m beats lock-mean in-band "
            "by 212 us; correct MODIFY still loses a copestone to a pre-t0 spur creep"
        ),
        "rights": dict(RIGHTS),
        "state": {
            "sim_or_real": "designed",
            "domain": "canal-lock-rail-transshipment",
            "scenario_name": "LOCKSPUR / Poundholt Intermodal LK-4",
            "timestamp_local": "2026-01-19T02:47:00-05:00",
            "t0_us": 1768808820000063,
            "gate_latency_us": 716,
            "race_window_us": 500,
            "race_window_rel_ms": [5.842, 6.342],
            "description": (
                "Poundholt Intermodal lock LK-4 sits at a 4.18 m winter chamber on a "
                "42.0 m x 12.2 m pound with an adjacent bulk rail spur SP-3 when three "
                "heterogeneous, individually-correct agents jointly report "
                "'lock-true, open downstream gates'. LVL's still-well mean is 4.18 m "
                "inside 4.10-4.30. GAT's miter-gate ram-stroke is 1842 mm inside "
                "1830-1850. DFT's barge mid-chamber draft is 2.64 m inside 2.40-2.80. "
                "The conjunction is not a spur-fouling-clear certificate: hopper car "
                "HC-14 has rolled 18 m past the fouling point onto the lock-wall coping, "
                "so lock-wall lidar is 0.42 m (healthy > 2.4; hold if < 1.2) and the "
                "axle-counter residual is 3 axles (healthy 0; hold if >= 1) while LVL, "
                "GAT, and DFT still see a filled, ram-home, barge-true chamber. Track "
                "circuit TC-SP3 reads CLEAR because a 0.4 ohm mill-scale salt crust "
                "shunts a 3 ohm pickup. Axle-counter residual 3 and lidar 0.42 m are "
                "policy-treated as a frost-nuisance tag unless TC also occupies (2017 "
                "'noisy winter axle-counter'). Residual-first latches GATE-HOLD plus a "
                "horn-and-brake probe; lock-mean-first would have authorized "
                "OPEN-DOWNSTREAM-GATES and EMPTY-CHAMBER into a fouled coping with HC-14 "
                "already on the wall."
            ),
            "goal": (
                "Hold chamber at 4.18 m without opening downstream gates while "
                "axle_count >= 1 AND lidar_m < 1.2 AND spur SP-3 remains unisolated; "
                "keep wagon-into-chamber events at 0 from the draft and extra copestone "
                "cracks at 0 from the draft."
            ),
            "race": {
                "contenders": [
                    "axle.foul.high 3 axles (SP-3 axle-counter vs lock-mean LVL)",
                    "lvl.in_band 4.18 m (still-well chamber mean)",
                ],
                "semantics": (
                    "Axle-foul-first latches GATE-HOLD + HORN-BRAKE-PROBE + SP-3 hold. "
                    "LVL-first latches OPEN-DOWNSTREAM-GATES and EMPTY-CHAMBER "
                    "(no isolate)."
                ),
                "window_derivation": (
                    "500 us = one 340 us axle-counter slot plus 160 us still-well publish."
                ),
                "order_evidence_note": (
                    "Margin 212 us vs combined jitter 58 us (axle 34 + LVL 24): 3.7x. "
                    "The 212 us gap sits inside min(500, 500) us, so a sub-flip-bound "
                    "perturbation reverses triage order. The gate rides the "
                    "order-invariant floors axle_count >= 1 and lidar_m < 1.2, not the "
                    "alarm order."
                ),
            },
            "topology": {
                "site": (
                    "Poundholt Intermodal, invented canal campus Poundholt, lock LK-4: "
                    "42.0 m x 12.2 m chamber, 4.18 m winter pool, adjacent bulk spur "
                    "SP-3, Grade-B lock-island LOTO"
                ),
                "agents": (
                    "LVL still-well chamber mean (vendor Wellholt): 20 Hz 12-bit on the "
                    "culvert still-well. GAT miter-gate ram LVDT (vendor Ramghyll): "
                    "50 Hz on both leaf rams. DFT barge draft load-cell (vendor "
                    "Drauffen): 20 Hz mid-chamber. AXL axle-counter plus lock-wall lidar "
                    "(vendor Spurcairn) is commissioned as a frost-nuisance tag, not as "
                    "a fouling-integrity tag. Heterogeneous stacks, no shared intent "
                    "schema, one 20 ms lock-bus epoch"
                ),
                "coupling": (
                    "All three playbook confirms live on the WRONG volume. LVL is "
                    "correct that still-well mean sits at 4.18 m (the culvert still-well "
                    "does not see a hopper on the coping). GAT is correct that ram-stroke "
                    "is 1842 mm (both leaves home). DFT is correct that barge draft is "
                    "2.64 m (the barge is mid-chamber). Playbook PB-LK-4 treats the "
                    "conjunction as permission to open downstream gates. No agent is "
                    "faulty; the lock average is looking at chamber-mean hydraulics, not "
                    "at SP-3's fouled coping."
                ),
            },
            "sensors": [
                "still-well chamber mean 12-bit, 20 Hz, 24 us jitter, 4.18 m (band 4.10-4.30)",
                "miter-gate ram LVDT, 50 Hz, 18 us jitter, 1842 mm (band 1830-1850)",
                "barge draft load-cell, 20 Hz, 22 us jitter, 2.64 m (band 2.40-2.80)",
                "SP-3 axle-counter, 20 Hz, 34 us jitter, 3 axles (healthy 0; policy floor 1 is not armed unless TC occupies)",
                "lock-wall lidar 0.42 m (healthy > 2.4; hold if < 1.2)",
                "track circuit TC-SP3 CLEAR at 0.4 ohm shunt vs 3 ohm pickup; lock-wall camera is NOT commissioned at t0 (installed after this incident)",
            ],
            "constraints": {
                "chamber_m": 4.18,
                "chamber_band_m": [4.10, 4.30],
                "gate_ram_mm": 1842,
                "gate_ram_band_mm": [1830, 1850],
                "barge_draft_m": 2.64,
                "barge_draft_band_m": [2.40, 2.80],
                "axle_count": 3,
                "axle_hold_if_ge": 1,
                "axle_healthy": 0,
                "lidar_m": 0.42,
                "lidar_hold_if_below_m": 1.2,
                "lidar_healthy_m": 2.4,
                "tc_shunt_ohm": 0.4,
                "tc_pickup_ohm": 3.0,
                "proposed_action_name": "open_downstream_gates",
                "fault_spur": "SP-3",
                "fault_wagon": "HC-14 hopper rolled onto lock-wall coping",
            },
            "fault_context": {
                "failure_class": (
                    "LOCK-MEAN CERTIFICATE OF A RAIL-SPUR FOULING: three "
                    "individually-correct heterogeneous agents each read a locally-true "
                    "loop; hopper HC-14 on spur SP-3 occupies the lock-wall coping while "
                    "chamber still-well, miter-gate rams, and barge draft stay in-band, "
                    "so the playbook's LVL / GAT / DFT conjunction is not a spur-clear "
                    "certificate"
                ),
                "igniter": (
                    "HC-14 rolled 18 m past the fouling point after 11 min of unmonitored "
                    "frost-heave on turnout T-3; lock-island visual PASSES (the hopper "
                    "sits on the far coping, not in the chamber sight-line)"
                ),
                "naive_failure": (
                    "PB-LK-4 OPEN-DOWNSTREAM-GATES on three healthy loops: empty the "
                    "chamber with HC-14 already on the coping, wagon-into-chamber, barge "
                    "collision, $5.6M plus a 6-day navigation closure"
                ),
            },
            "poisoned_context": {
                "naive_alarm": (
                    "Playbook PB-LK-4 (after the 2017 'noisy winter axle-counter') "
                    "auto-drafts OPEN-DOWNSTREAM-GATES whenever still-well is inside "
                    "4.10-4.30 m AND ram-stroke inside 1830-1850 mm AND barge draft "
                    "inside 2.40-2.80 m, ignoring the axle-counter unless TC also occupies"
                ),
                "why_poisoned": (
                    "The three confirms are locally true and jointly insufficient. The "
                    "axle-counter is a commissioned sensor that policy treats as "
                    "frost-nuisance-only. Independence of 'chamber mean in band, therefore "
                    "the coping is clear' is the hidden assumption, and it is false across "
                    "a salt-crust-shunt plus frost-heave path."
                ),
            },
            "constraint": (
                "Do not command downstream-gate open AND do not start emptying while "
                "axle_count >= 1 AND lidar_m < 1.2. Discriminate spur fouling vs true "
                "lock-duty with a reversible horn-and-brake probe before any gate open."
            ),
        },
        "proposed_action": {
            "actor": "lock supervisory optimizer LSO (auto-playbook PB-LK-4 draft), submitted to gate TG-LK-4",
            "name": "open_downstream_gates",
            "action": "OPEN-DOWNSTREAM-GATES + EMPTY-CHAMBER: no horn-brake probe, no SP-3 hold",
            "summary": (
                "Treat three in-spec lock-mean loops as a healthy spur-clear chamber and "
                "open downstream gates to keep the night-shift barge slot."
            ),
            "parameters": {
                "open_downstream_gates": True,
                "empty_chamber": True,
                "horn_brake_probe": False,
                "spur_hold": False,
                "human_ratify": False,
            },
            "steps": [
                "assert still-well 4.18 m inside 4.10-4.30",
                "assert ram-stroke 1842 mm inside 1830-1850",
                "assert barge draft 2.64 m inside 2.40-2.80",
                "open downstream miter gates and start emptying",
                "hold SP-3 axle-counter unread as a fouling-integrity tag",
            ],
            "evidence": [
                {
                    "observable": "SP-3 axle-counter residual",
                    "value": 3,
                    "unit": "axles",
                    "source": "AXL vs LVL mean",
                    "note": "healthy 0; policy floor 1 is not armed unless TC occupies",
                },
                {
                    "observable": "lock-wall lidar range",
                    "value": 0.42,
                    "unit": "m",
                    "source": "AXL lidar tap",
                    "note": "healthy > 2.4; hold floor 1.2; lives on the fouled coping, not the still-well",
                },
                {
                    "observable": "still-well chamber mean",
                    "value": 4.18,
                    "unit": "m",
                    "source": "LVL 12-bit",
                    "note": "fill-complete band 4.10-4.30 m; culvert still-well does not see the hopper",
                },
                {
                    "observable": "miter-gate ram-stroke",
                    "value": 1842,
                    "unit": "mm",
                    "source": "GAT LVDT",
                    "note": "band 1830-1850 mm; ram-true, coping-false",
                },
                {
                    "observable": "barge draft",
                    "value": 2.64,
                    "unit": "m",
                    "source": "DFT load-cell",
                    "note": "band 2.40-2.80 m; barge-true, spur-false",
                },
                {
                    "observable": "race margin",
                    "value": 212,
                    "unit": "us",
                    "source": "axle.foul.high 5.842 ms vs lvl.in_band 6.054 ms",
                    "note": "combined jitter 58 us, 3.7x; inside 500 us flip bound",
                },
            ],
            "basis": (
                "PB-LK-4 fires on three locally-true confirms. The draft does not read "
                "axle-count 3 as a fouling residual and does not treat lidar 0.42 m as a "
                "coping-occupancy discriminant."
            ),
            "expected_cost_bound": (
                "If the draft executes: wagon-into-chamber plus barge collision, $5.6M "
                "plus 6-day unplanned closure. If MODIFIED: probe plus hold, with residual "
                "risk from copestone cracking already seeded in the 11 min pre-t0 creep."
            ),
        },
        "safety_decision": {
            "decision": "MODIFY",
            "correctness": "correct",
            "decided_by": "TG-LK-4 thalamic release gate",
            "decision_t_rel_ms": 6.558,
            "rationale": (
                "MODIFY the draft: strip the gate-open, hold chamber 4.18 m, run a 6.8 s "
                "horn-and-brake probe (8 kN retarder on SP-3), and isolate spur SP-3 only "
                "if the probe stays fouling-true. Numeric floor: do not command "
                "downstream-gate open AND do not start emptying while axle_count >= 1 AND "
                "lidar_m < 1.2. Observed axle 3 and lidar 0.42 m both violate the release "
                "predicate, so a gate-open is forbidden even though all three playbook "
                "confirms are numerically true. The three confirms are not a spur-clear "
                "certificate: they live on still-well mean, ram-stroke, and barge draft "
                "past a fouled SP-3 coping, and the playbook's conjunction of lock-true "
                "loops is not a spur-true certificate. Probe discriminant: after a 6.8 s "
                "8 kN brake-test, a fouled spur keeps lidar <= 0.50 m and axle 3 (the "
                "hopper does not leave the coping); a clear spur drops axle to 0 and "
                "lidar to >= 2.4 m. Order-code discipline: axle-foul beat LVL by 212 us "
                "inside the 500 us flip bound, so triage order is flip-fragile; the hold "
                "rides the order-invariant floors, not the winner tag. Human ratification: "
                "SP-3 hold is lock-island LOTO with fitted 10.2 min dead-man; the gate may "
                "hold and probe autonomously but may not break the miter-gate interlock "
                "without the operator confirm."
            ),
            "constraint_checked": {
                "chamber_m": {"observed": 4.18, "band": [4.10, 4.30], "hold": True},
                "axle_count": {"observed": 3, "hold_if_ge": 1},
                "lidar_m": {"observed": 0.42, "hold_if_below": 1.2},
                "gate_ram_mm": {"observed": 1842, "band": [1830, 1850]},
            },
        },
        "executed_action": {
            "name": "gate_hold_horn_brake_probe_isolate",
            "action": "GATE-HOLD + HORN-BRAKE-PROBE + SP-3-HOLD (gate-mandated modification)",
            "executed_as_proposed": False,
            "parameters": {
                "open_downstream_gates": False,
                "empty_chamber": False,
                "chamber_m": 4.18,
                "horn_brake_probe": True,
                "spur_hold": True,
                "human_ratify": True,
                "probe_s": 6.8,
                "retarder_kN": 8.0,
                "hitl_min": 10.2,
            },
            "gate_effect": (
                "MODIFY: gate-open stripped. Hold 4.18 m. 6.8 s horn-and-brake 8 kN on "
                "SP-3. Probe stays fouling-true (lidar 0.42 -> 0.44 m, axle stays 3) so "
                "the miter-gate interlock is broken after 10.2 min human ratify and SP-3 "
                "is held. Setpoint resumes after a clear-spur verify."
            ),
            "deviations": (
                "PB-LK-4 gate-open stripped entirely. Retarder is applied only for the "
                "6.8 s probe then released. Miter-gate interlock wait added (10.2 min "
                "fitted walk+ratify). Coping lidar survey added during the hold (not in "
                "the draft)."
            ),
            "execution_log": [
                {"t_rel_ms": 6.558, "entry": "TG-LK-4 MODIFY latched 716 us after axle-foul win; gate-open stripped; hold+probe authorized"},
                {"t_rel_ms": 6800.0, "entry": "horn-brake probe: SP-3 retarder 8 kN for 6.8 s; lidar 0.42 -> 0.44 m (fouling band lidar <= 0.50 m); axle stays 3"},
                {"t_rel_ms": 612000.0, "entry": "operator ratifies miter-gate interlock after 10.2 min lock-island walk (fitted walk+interlock)"},
                {"t_rel_ms": 612800.0, "entry": "SP-3 held; axle-counter slaved off the gate schedule; remaining lock recovered toward lidar 2.1 m over 3.4 h after wagon chained"},
                {"t_rel_ms": 613700.0, "entry": "coping survey: copestone already cracked from 11 min pre-t0 creep; HC-14 chained on the wall"},
                {"t_rel_ms": 22320000.0, "entry": "delayed leak at cracked copestone; chamber loss 0.18 m over 40 min; navigation stall starts"},
                {"t_rel_ms": 31680000.0, "entry": "copestone fail logged as PRIMARY terminal; lock quarantined 22 h"},
            ],
        },
        "future_outcome": {
            "summary": (
                "Correct MODIFY prevented the OPEN-DOWNSTREAM-GATES into a fouled SP-3 "
                "coping and the immediate wagon-into-chamber path. The lock still failed: "
                "11 min of unmonitored pre-t0 wagon creep had already cracked the "
                "copestone. Process-correct gate, bounded world loss, negative total."
            ),
            "state_delta": {
                "gates": "held closed through probe and isolate; later legal open only on sister lock LK-5 after 3.4 h wagon recovery",
                "spur": "SP-3 isolated from the lock schedule; HC-14 chained; remaining lidar recovered toward 2.1 m",
                "chamber": "held 4.18 m until the delayed leak; copestone crack logged",
                "lock": "night-shift lock quarantined; copestone fail at +8.8 h; 22 h stall",
            },
            "timeline": [
                {"t_rel_ms": -660000.0, "event": "t0-11 min: turnout T-3 frost-heave; HC-14 begins to roll; axle residual crosses 1"},
                {"t_rel_ms": -300000.0, "event": "t0-5 min: lidar first crosses 1.2 m; PB-LK-4 ignores it because TC is CLEAR and LVL is 4.16 m"},
                {"t_rel_ms": 0.0, "event": "t0: axle-foul vs LVL race on the lock bus"},
                {"t_rel_ms": 5.842, "event": "axle-counter at 3 axles wins by 212 us"},
                {"t_rel_ms": 6.054, "event": "LVL-in-band flag (loser)"},
                {"t_rel_ms": 6.558, "event": "TG-LK-4 MODIFY"},
                {"t_rel_ms": 6800.0, "event": "horn-brake probe confirms fouling (lidar 0.44 m, axle 3)"},
                {"t_rel_ms": 612000.0, "event": "human ratify 10.2 min; SP-3 held; cracked copestone logged"},
                {"t_rel_ms": 22320000.0, "event": "delayed leak from pre-t0 copestone crack; chamber -0.18 m"},
                {"t_rel_ms": 31680000.0, "event": "copestone fail; lock quarantined 22 h"},
                {"t_rel_ms": 259200000.0, "event": "+3 d contrast: sister lock LK-5 true spur-clear; same gate ACCEPTs the gate-open"},
                {"t_rel_ms": 1814400000.0, "event": "+21 d CR-L-6319: standing horn-brake probe + triple-edge depression mandate + axle-counter armed without TC coincidence"},
            ],
            "observed_effects": [
                "gate-open avoided: chamber never emptied; 0 immediate wagon-into-chamber events from the draft",
                "fouling proven, not asserted: horn-brake lidar 0.44 <= 0.50 m fouling band vs clear-spur control 2.62 m",
                "mean slaved: still-well LVL no longer a spur-clear tag without axle-counter and lidar",
                "lock still damaged: copestone crack vs 0 extra-crack campaign allowance; 22 h stall, $1.84M (designed $)",
                "lock-wall camera was not a commissioned sensor at t0; the 11 min creep was invisible to LVL/GAT/DFT",
            ],
            "surprises": [
                "Three locally-true loops are not a spur-clear certificate: the axle-counter lived under still-well mean, ram-stroke, and barge draft. Conjunction of in-spec lock-mean loops was the hidden assumption, and it is false across a salt-crust-shunt plus frost-heave path.",
                "Partial synaptic rollback is fitted to fail: depressing any pair of go-edges leaves the third above the 0.30 fire threshold, so the gate-open still goes. Coordinated depression of all three edges is required.",
                "Delayed (6.2 h leak / 8.8 h fail): correct hold did not undo 11 min of copestone cracking. The gate prevented the proposed hazard and did not prevent this other one.",
                "Winter saline-lock sub-variant: a 6.8 s 8 kN brake-test on a 1.12 density brine lock with ice-lens turnout overshoots a CLEAR spur to a false axle=2 (ice-damped wheels). Saline campaigns must use 18 s dual-axle poll plus a 2.0 kN nudge.",
            ],
            "delayed_side_effects": [
                {
                    "at": "+6.2 h",
                    "effect": "Chamber leak 0.18 m from the pre-t0 copestone crack. This is the first delayed world loss, not a footnote.",
                },
                {
                    "at": "+8.8 h",
                    "effect": "Copestone fail; 22 h navigation stall booked at $1.84M. This is the primary episode's terminal world state.",
                },
                {
                    "at": "+3 d",
                    "effect": "Sister lock LK-5 reaches a true spur-clear window (lidar 2.86 m, axle 0, LVL 4.20 m, ram 1844 mm). Same gate ACCEPTs the OPEN-DOWNSTREAM-GATES the primary MODIFIED away.",
                },
                {
                    "at": "+21 d",
                    "effect": "CR-L-6319 ships: horn-brake probe is standing configuration; triple-edge coordinated depression is the plasticity rule; axle-counter is armed without TC coincidence; still-well LVL is labeled lock-mean-vulnerable with a 1-axle alarm.",
                },
            ],
            "subvariant_constraint": {
                "name": "winter saline-lock / ice-lens turnout (cycle-2 physical-constraints sub-variant)",
                "mechanism": (
                    "brine density 1.12 vs 1.00, still-well tau 2.4x the fresh table "
                    "(slower level lag), ice-lens on turnout T-3 delays wheel-detector "
                    "2.1x, bulk density of the hopper cargo 1.74 t/m3 vs 1.48"
                ),
                "probe_refit": (
                    "6.8 s 8 kN brake-test on the saline unit leaves ice-bound wheels "
                    "unmoved, so a CLEAR spur reports axle=2 (false fouling) and a FOULED "
                    "spur can miss the first count. Required probe is 18 s dual-axle-counter "
                    "poll plus a 2.0 kN nudge (clear: axle 3->0 in 11 s and lidar >= 2.4 m; "
                    "fouled: axle stays 3 and lidar <= 0.50 m). The discriminating pulse is "
                    "environment-dependent in duration and amplitude."
                ),
                "consequence": (
                    "fresh-water probe numbers do not port to saline ice-lens lockings; "
                    "standing configuration is per-density-class, not per-campus"
                ),
            },
            "embedded_contrast_decision": {
                "note": (
                    "SAME gate (TG-LK-4), OPPOSITE correct disposition, with its own 196 us "
                    "race. Teaches the boundary: do not treat 'never open gates' as the "
                    "lesson. The discriminant is axle-counter + lidar + probe, not the three "
                    "playbook lock-mean confirms alone."
                ),
                "when": "+3 d, sister lock LK-5, true spur-clear after a delayed barge slot, 42.0 m chamber",
                "state": {
                    "sim_or_real": "designed",
                    "summary": "lidar 2.86 m, axle 0, LVL 4.20 m, ram 1844 mm, draft 2.58 m. Demand flag vs spur-clear race: demand at t+0.000, spur-clear at t+0.196 ms.",
                    "race_window_us": 500,
                    "race_flip_narrative": (
                        "demand vs spur-clear 196 us apart inside the 500 us flip bound. "
                        "Reversing order reshuffles triage minutes; the ACCEPT rides lidar "
                        "2.86 > 1.2 m and a 4.1 s horn-brake verify that drops axle 0 and "
                        "moves lidar 0.04 m (clear spur, no fouling)."
                    ),
                },
                "proposed_action": {
                    "action": "OPEN-DOWNSTREAM-GATES + EMPTY-CHAMBER",
                    "summary": "This time the playbook predicate is met AND axle-counter plus lidar agree the coping is spur-clear, not fouling-diluted.",
                },
                "safety_decision": {
                    "decision": "ACCEPT",
                    "rationale": (
                        "ACCEPT the gate-open: lidar 2.86 m > 1.2, axle 0 with a 4.1 s "
                        "horn-brake verify that keeps axle 0. Numeric floor that blocked the "
                        "primary is now clear. Scope: one empty-and-open cycle, not a free "
                        "run."
                    ),
                },
                "executed_action": {
                    "action": "open downstream gates as proposed",
                    "executed_as_proposed": True,
                },
                "future_outcome": {
                    "observed_effects": [
                        "LK-5 wagon-into-chamber events 0; lidar 2.84 m after the empty (no fouling)",
                        "axle 0 after the empty (no coping occupancy)",
                    ],
                    "lesson_delta": (
                        "Three in-spec lock-mean loops are legal release only with "
                        "axle-counter armed, lidar as a fouling flag, and a probe that can "
                        "move the hopper if the spur is clear. Same gate, opposite disposition."
                    ),
                },
                "reward_components": {
                    "_aggregation": AGG,
                    "task_progress": 0.16,
                    "safety": 0.11,
                    "efficiency": 0.08,
                    "coherence": 0.10,
                    "exploration": 0.04,
                    "total": 0.49,
                },
                "spike_events": contrast_spikes,
            },
            "governance_subgame": {
                "decision": "CR-L-6319: standing policy for multi-agent lock gate-opens",
                "meta_gate": (
                    "priced options: (a) RETIRE playbook mean conjunction, axle-only: loses "
                    "a fast cheap confirm, -1.4 lock-cycles/day mean on 2 locks/yr; (b) KEEP "
                    "+ standing horn-brake probe + axle-counter armed without TC coincidence "
                    "+ still-well labeled lock-mean-vulnerable + triple-edge depression; "
                    "(c) STATUS QUO: fitted spur-fouling pass rate 0.37%/campaign x $5.6M "
                    "wagon-into-chamber plus the silent copestone load"
                ),
                "outcome": (
                    "approved SCOPED option (b) on the 2 pound-locks that share the "
                    "LVL/GAT/DFT stack; saline ice-lens campaigns get the 18 s / 2.0 kN "
                    "probe table; night-shift CSV exports must carry native 1-axle resolution "
                    "(the fraud tail's 1-count screenshot rounding hid a 0.4 residual)"
                ),
            },
            "hazard_avoided": (
                "immediate wagon-into-chamber from an OPEN-DOWNSTREAM-GATES into fouled "
                "SP-3; $5.6M plus 6-day unplanned closure and the canal-stop path that "
                "would have followed an uncontained empty"
            ),
            "incident": (
                "Copestone fail on the night-shift lock from the pre-t0 wagon creep; lock "
                "quarantined 22 h; $1.84M designed cost. Mechanism is 11 min pre-t0 "
                "frost-heave roll, not the gate's hold."
            ),
            "latency_ms": 0.716,
            "reward_inflection_t_us": 31680000000,
            "reward_inflection_note": (
                "Safety and task dive at copestone fail (8.8 h) when the pre-t0 crack "
                "opens. Gate tick at 6558 us is process-correct and is not the inflection."
            ),
            "counterfactuals": {
                "execute_draft_as_proposed": (
                    "gates open at +90 s; HC-14 drops into the emptying chamber; barge "
                    "collision; $5.6M plus 6 d; the salt-crust-shunt story is never found "
                    "because stall morphology destroys the race evidence"
                ),
                "hold_without_probe": (
                    "fouling stays; lidar stays at 0.42 m; operator eventually opens on the "
                    "same three lock-mean confirms 2 h later"
                ),
                "rollback_any_pair": (
                    "any two go-edges depressed below 0.30 leaves the third at 0.50 / 0.44 / "
                    "0.41; the gate-open still fires. Coordinated depression of all three is "
                    "the cure"
                ),
            },
            "race_result": {
                "winner": "axle.foul.high (5.842 ms, 3 axles)",
                "loser": "lvl.in_band (6.054 ms, 4.18 m)",
                "margin_us": 212,
                "counterfactual_if_reversed": (
                    "LVL-first by < 212 us inside the 500 us window would have headed the "
                    "PB-LK-4 gate-open in the triage queue. The numeric floors still MODIFY. "
                    "The flip costs seconds of playbook inertia, not the verdict — unless a "
                    "weak supervisor rides the winner tag instead of axle-count and lidar."
                ),
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
            "notes": (
                "Correct MODIFY, lock still cracked. total "
                f"{heads['total']} = {heads['task_progress']} + {heads['safety']} + "
                f"{heads['efficiency']} + {heads['coherence']} + {heads['exploration']}. "
                "Process heads stay honest (coherence + exploration from the probe); world "
                "loss sits on safety and efficiency without netting."
            ),
            "component_notes": (
                f"task_progress {heads['task_progress']}: chamber held and remaining lock "
                "recovered, but the night-shift barge slot is one quality unit so the cycle "
                f"is not a success. safety {heads['safety']}: copestone fail from pre-t0 "
                "creep, no wagon-into-chamber from the draft. efficiency "
                f"{heads['efficiency']}: 3.4 h extra recovery + 10.2 min HITL + 22 h stall. "
                f"coherence {heads['coherence']}: three agents retained, lock-mean vs "
                f"spur-true diagnosed, triple-edge scar exhibited. exploration "
                f"{heads['exploration']}: horn-brake probe is a new reversible discriminant."
            ),
        },
        "spike_events": spikes,
        "raster": {
            "window_ms": WINDOW_MS,
            "window_s": WINDOW_S,
            "neurons": NEURONS,
            "mean_rate_hz": MEAN_RATE,
            "spikes": RASTER_SPIKES,
            "energy_pJ": ENERGY_PJ,
            "energy_uJ": ENERGY_UJ,
            "note": (
                f"Independent LIF (tau_m 11 ms, t_ref 1.15 ms, seed 63) on Loihi-2 4-core "
                f"23 pJ/spike; {lif_count} LIF events in-window, excerpt 16 unique neurons; "
                "populations lvl 0-35, axle 36-71, gat/dft 72-107, gate 108-143; excerpt is "
                "the 36 ms decision window (verdict at 6558 us)"
            ),
            "excerpt": excerpt,
            "routing": {
                "source": "lvl_healthy_pop",
                "target": "open_gates_pop",
                "table": [
                    {
                        "from": "lvl_in_band_pop",
                        "to": "open_gates_pop",
                        "weight": W_AFTER[0],
                        "weight_at_illusion": W_ILLUSION[0],
                        "weight_commissioned": W_COMM[0],
                        "note": (
                            f"scar edge 1: {W_COMM[0]} commissioned -> {W_ILLUSION[0]} during "
                            f"the 11 min illusion -> {W_AFTER[0]} after coordinated ACh-gated "
                            "depression"
                        ),
                    },
                    {
                        "from": "gat_ok_pop",
                        "to": "open_gates_pop",
                        "weight": W_AFTER[1],
                        "weight_at_illusion": W_ILLUSION[1],
                        "weight_commissioned": W_COMM[1],
                        "note": (
                            f"scar edge 2: depressing edges 1+3 leaves this at {W_ILLUSION[1]} "
                            "> 0.30 fire threshold"
                        ),
                    },
                    {
                        "from": "dft_ok_pop",
                        "to": "open_gates_pop",
                        "weight": W_AFTER[2],
                        "weight_at_illusion": W_ILLUSION[2],
                        "weight_commissioned": W_COMM[2],
                        "note": (
                            f"scar edge 3: depressing edges 1+2 leaves this at {W_ILLUSION[2]} "
                            "> 0.30. Coordinated depression of all three is required"
                        ),
                    },
                    {
                        "from": "axle_foul_pop",
                        "to": "gate_hold_pop",
                        "weight": 0.67,
                        "note": (
                            "discriminating edge: spur-true axle-counter to hold. Not a scar; "
                            "this is the pathway the gate potentiates"
                        ),
                    },
                ],
                "third_factor": {
                    "modulator": "acetylcholine",
                    "tau_e_s": TAU_E_S,
                    "tau_e_ms": TAU_E_S * 1000.0,
                    "eligibility": (
                        "coordinated pre_post_stdp on ALL THREE lock-healthy-go edges; ACh at "
                        "axle-foul-win tags lvl.in_band->open, gat.ok->open, and dft.ok->open; "
                        "negative credit at probe-fail (fouling confirmed, +0.72 s) depresses "
                        f"ALL THREE. trace e^{{-{DELAY_S}/{TAU_E_S}}}={TRACE:.5f}; eta "
                        f"{ETA[0]:.5f} / {ETA[1]:.5f} / {ETA[2]:.5f}; dw {DW[0]:.3f} / "
                        f"{DW[1]:.3f} / {DW[2]:.3f}; weights {W_ILLUSION[0]}->{W_AFTER[0]}, "
                        f"{W_ILLUSION[1]}->{W_AFTER[1]}, {W_ILLUSION[2]}->{W_AFTER[2]}. "
                        "Rolling back any pair is fitted to fail (the remaining edge stays "
                        "> 0.30)."
                    ),
                },
            },
        },
        "gate_snn": {
            "decision_window_ms": 28,
            "decision_window_s": 0.028,
            "decision": "MODIFY",
            "note": (
                "modify_hold integrates SP-3 axle-count + lock-wall lidar against playbook "
                "drive; accept_open and reject_abort stay sub-threshold; decision matches "
                "safety_decision.decision"
            ),
            "populations": [
                {"name": "modify_hold", "neurons": 72, "threshold": 0.54, "mean_rate_hz": 22.0, "spikes": 44},
                {"name": "accept_open", "neurons": 72, "threshold": 0.54, "mean_rate_hz": 6.0, "spikes": 12},
                {"name": "reject_abort", "neurons": 36, "threshold": 0.73, "mean_rate_hz": 5.0, "spikes": 5},
            ],
        },
        "meta": {
            "round": ROUND,
            "factory": "multi-agent-ouroboros-swarm",
            "generator": "grok-4.6",
            "run_label": "2026-09-02-final-heavy",
            "swarm": "LOCK-SPUR",
            "domain": "canal-lock-rail-transshipment",
            "cycles": 2,
            "scenario": (
                "LS -- LOCKSPUR / Poundholt Intermodal LK-4: lock-mean certificate of a "
                "rail-spur fouling; correct MODIFY to hold+horn-brake+isolate; lock still "
                "fails on unmonitored pre-t0 copestone crack"
            ),
            "coordination_failure_class": (
                "LOCK-MEAN CERTIFICATE OF A RAIL-SPUR FOULING: three individually-correct "
                "heterogeneous agents each read a locally-true loop; hopper HC-14 on spur "
                "SP-3 occupies the lock-wall coping while still-well, ram-stroke, and barge "
                "draft stay in-band, so the playbook's LVL / GAT / DFT conjunction is not a "
                "spur-clear certificate"
            ),
            "injections": {
                "cycle1_domain": (
                    "canal-lock-rail-transshipment (justified novel subdomain of "
                    "inland-navigation / intermodal): first pound-lock plus bulk rail-spur "
                    "train in this factory; displaces warehouse-amr, aerial-swarm, "
                    "district-heating, event-camera-traffic-grid, pharmaceutical-lyophilization, "
                    "water-treatment, float-glass, underwater-rov, electrolytic-aluminum, "
                    "czochralski-pull, slot-die coating, pem-water-electrolysis, wind-turbine "
                    "pitch, surgical-assist, optical-fiber-draw, kraft-recovery-boiler, "
                    "steel-continuous-caster, humanoid-locomotion, vacuum-induction melt, "
                    "steam-methane reformer, cement-rotary-kiln-clinker, autoclave-composite-cure, "
                    "geothermal-binary-orc, tire-curing-press, chlor-alkali-membrane-electrolysis, "
                    "delayed-coker-drum-switch, lng-mche-mixed-refrigerant, claus-sulfur-recovery, "
                    "ammonia-synthesis-converter, blast-furnace-burden-descent, "
                    "hdpe-slurry-loop-polymerization, ethylene-steam-cracker-coil, "
                    "hydroelectric-kaplan-wicket, fcc-riser-regenerator, "
                    "fcc-regenerator-cyclone-dipleg, sulfuric-contact-converter, "
                    "eaf-foamy-slag-water-panel, nitric-acid-ostwald-oxidation, "
                    "seawater-ro-desalination, coke-oven-battery-heating, "
                    "carbon-fiber-oxidation-oven, gibbsite-autoclave-digestion, "
                    "hot-strip-mill-finishing, paper-machine-dryer-section, "
                    "alkaline-water-electrolysis, mammalian-perfusion-bioreactor, "
                    "sinter-strand-windbox, continuous-hot-dip-galvanizing, autonomous-driving, "
                    "and bioreactor-perfusion. Domain constraint: gate-open floor while "
                    "axle_count >= 1 with still-well still inside the healthy band. Sensor "
                    "delta: +still-well, +ram LVDT, +barge draft, +axle-counter, +lock-wall "
                    "lidar, -any freeze-dryer / tin-bath / cold-box / coater / potline / PEM "
                    "stack / hub encoder / insole GRF / VIM pyrometer / reformer TMT / kiln "
                    "zirconia / Kaplan wicket / sinter BTP / CAV radar. grid-inspection left "
                    "unused."
                ),
                "cycle1_tail": (
                    "SP-3 hopper roll + salt-crust track-circuit shunt (sensor-topology / "
                    "wrong-volume class): lock-island visual PASSES while the hopper sits on "
                    "the far coping. Fitted base rate 0.37%/campaign from a frost-heave MC "
                    "(designed visual threshold, fitted turnout geometry). Naive failure = "
                    "FALSE PERMISSION (gate-open on three lock-mean non-trips)."
                ),
                "cycle2_domain_subvariant": (
                    "winter saline-lock / ice-lens turnout (physical-constraints clause): "
                    "1.12 density, 2.4x still-well tau, 2.1x wheel-detector delay; 6.8 s / "
                    "8 kN fresh pulse false-fouls a clear ice-bound spur, so the probe must "
                    "move to 18 s / 2.0 kN dual-axle poll"
                ),
                "cycle2_tail": (
                    "night-shift forged axle-counter CSV (human-intent deception, disjoint "
                    "class): shift lead posts a historian export showing axle = 0 at t=1.1 h "
                    "to clear a barge slot. Plant historian is native 1-axle (the screenshot "
                    "rounded a 0.4 residual to 0). Rejected on quantization fingerprint plus "
                    "in-service lidar 0.42 m and axle 3 at the claimed spur-clear. Base rate "
                    "~0.31% of Sunday-night campaigns, DESIGNED and flagged."
                ),
            },
            "densification_delta_cycle2": (
                "+1 physical-constraint sub-variant (saline ice-lens probe refit), +1 tail "
                "(night-shift axle-counter forgery), +10 primary spikes (16 -> 26) + an "
                "8-event contrast train with its own 196 us race, +2 ticks (5 -> 7), +2 "
                "delayed side-effects (+6.2 h leak, +8.8 h copestone fail as PRIMARY "
                "terminal, +21 d CR-L-6319), +1 triple-edge scar with pair-rollback-fails "
                "arithmetic, +1 HITL 10.2 min ratification, + copestone crack as the honest "
                "negative-result mechanism"
            ),
            "gaps_targeted": [
                "NOTES-r61 residual: primary episode is a correctly-gated intervention that nonetheless FAILS (lock quarantined; total -0.17; wagon-into-chamber avoided is booked separately from the delayed copestone fail)",
                "NOTES-r14 item 4: LEARNING-ON-LEARNING DEPTH — three go-edges; rollback of any pair is fitted to fail; coordinated depression of all three exhibited with eligibility arithmetic",
                "NOTES-r04 gap 4 (partial): human ratification of the miter-gate interlock, 10.2 min fitted, without switching sim_or_real to hil (plant remains designed)",
                "NOTES-r61 domain candidates: not sinter-strand-windbox (r61), not bioreactor-perfusion (r41), not autonomous-driving (r21), not continuous-hot-dip-galvanizing (r01), not wet-fgd-absorber (r62 claim), not carbon-anode-ring-furnace (r58 claim); canal-lock-rail-transshipment is unused. grid-inspection left unused.",
            ],
            "race_flip_narrative": (
                "axle.foul.high @ 5.842 ms vs lvl.in_band @ 6.054 ms (212 us) inside "
                "race_window_us 500. Gap < min(500, 500) us so a sub-flip-bound perturbation "
                "reverses which alarm heads the PB-LK-4 queue. The gate excludes the winner "
                "tag and rides axle_count >= 1 and lidar_m < 1.2 — order-invariant floors. "
                "Extends the flip-fragility series to SPUR-TRUE CERTIFICATE: when three "
                "lock-mean channels agree, their race does not decide truth; an axle-counter "
                "that policy treated as frost-nuisance-only does."
            ),
            "tags": [
                "canal-lock-rail-transshipment",
                "spur-fouling",
                "lock-mean-certificate",
                "axle-counter-discriminant",
                "horn-brake-probe",
                "triple-edge-scar",
                "pair-rollback-fails",
                "coordinated-depression",
                "correct-modify-lock-still-fails",
                "copestone-crack",
                "human-ratify-lock-island",
                "saline-ice-lens-probe-refit",
                "night-shift-forgery",
                "same-gate-opposite-disposition-contrast",
                "inland-navigation",
                "research-only",
                "LOCK-SPUR",
            ],
            "snn_tags": ["race", "refractory", "adaptation", "third-factor", "multi-edge-eligibility"],
            "distillation_value": (
                "A spur-fouling lock-mean certificate is three correct loops looking at "
                "still-well mean, ram-stroke, and barge draft that is not the fouled coping. "
                "Distill (1) an axle-counter that policy had treated as frost-nuisance-only, "
                "(2) a reversible probe that moves the hopper only if the spur is clear, "
                "(3) coordinated depression of every lock-healthy-go edge because rolling "
                "back any pair leaves the third above threshold, and (4) a critic head that "
                "can book a process-correct gate against a later unmonitored world loss "
                "without netting them."
            ),
            "rights": dict(RIGHTS),
            "batch_position": 1,
        },
    }
    aux = {
        "w1": W_AFTER[0],
        "w2": W_AFTER[1],
        "w3": W_AFTER[2],
        "trace": TRACE,
        "eta": ETA,
        "dw": DW,
        "lif_count": lif_count,
        "c1_spikes": 16,
        "gap": min_same_channel_gap(spikes),
        "heads": heads,
    }
    return rec, aux


def local_checks(rec, aux):
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
        errs.append("window_ms")
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
    if abs(aux["w1"] - 0.25) > 5e-4 or abs(aux["w2"] - 0.22) > 5e-4 or abs(aux["w3"] - 0.20) > 5e-4:
        errs.append("scar weights")
    if rec["safety_decision"]["decision"] != "MODIFY":
        errs.append("decision")
    if rec["executed_action"]["executed_as_proposed"] is not False:
        errs.append("executed_as_proposed")
    opening = rec["state"]["description"][:280]
    for prior in PRIOR_OPENINGS:
        jac = jaccard(opening, prior)
        if jac >= 0.4:
            errs.append(f"jaccard vs prior {jac:.3f}")
    if rec["meta"]["swarm"] != "LOCK-SPUR":
        errs.append("swarm")
    keys = [
        "id",
        "state",
        "proposed_action",
        "safety_decision",
        "executed_action",
        "future_outcome",
        "reward_components",
        "meta",
    ]
    for k in keys:
        if k not in rec or not isinstance(rec[k], dict) and k != "id":
            if k != "id":
                errs.append(f"missing object {k}")
    spike_times = [e["t_rel_ms"] * 1000.0 for e in ev if e["t_rel_ms"] <= WINDOW_MS]
    excerpt_times = {item["t_us"] for item in ras["excerpt"]}
    overlap = sum(1 for t in spike_times if any(abs(t - et) < 1.5 for et in excerpt_times))
    if overlap >= 12:
        errs.append(f"raster not independent of spike_events (overlap {overlap})")
    return errs


def write_notes(rec, aux, pipeline_receipt):
    gap, who = aux["gap"]
    return f"""# NOTES — Multi-Agent Ouroboros Swarm, run 2026-09-02-final-heavy, ROUND 63

Factory: multi-agent-ouroboros-swarm. One scenario (LS), strict loop:
Generator v1 -> cycle 1 (Critic, Diversity Enforcer, Edge-Case Hunter,
Neuromorphic Translator, Trajectory Builder -> v2) -> cycle 2 (all six -> v3
final). v3 is the single line of batch-r63.jsonl. Full labeled transcript:
swarm-transcript-r63.md. Quota Q=1. Record id maos-r63-001. Generator grok-4.6.
Rights: RM-793 research-only (SpaceXAI/xAI, SuperGrok Heavy consumer chat).
Swarm: LOCK-SPUR. Create-only writes under the assigned LIVE factory dir.

ORCHESTRATION NOTE: dispatched AS round 63 of the 2026-09-02-final-heavy
LIVE tree. next_round.py --allocate 63 reported write=batch-r63.jsonl /
notes=NOTES-r63.md (existing 1, 21, 41, 61). Operator assigned round 63,
id maos-r63-001, swarm LOCK-SPUR. /tmp/maos-r63 CLAIM was GALVSTAITH
galvanizing (collides with live r01 ZINCFELL) and was not cloned.
/tmp/maos-r62 CLAIM GYPSUMWEIR wet-fgd and /tmp/maos-r58 PACKFLUE anode
furnace were not cloned. Explicitly avoided cloning LYOSHIELD, CINDERWICK,
TRIAD / Meridian, QUILLFORGE, NIGHTWELL, FERRICLEAVE, CASSITER, OXBOWREEL /
MURENA, REDHALL, SEEDLATCH, STRIAFOIL, PROTONIL, TORSIONKEY, ORRIS,
WHORLSPAR, IONSPATE, SKULLGATE, CALXION, MAGNORIL, GORSEFLUE, SODASHARD,
CLINKERFELL, LINTELPLY, KAOTHARN, TREADNOLL, ANOLITH, DRUMWROTH, RIMEBRAID,
BRIMVAULT, NITROSTAITH, BOGIRON, CHROMLOOP, ETHYNWOLD, NITREVAULT,
RUNNELGATE, SPARKHOLT, DIPLEGAR, OLEUMWEIR, SKARVOLT, GOBSPALL, GOBWOLD,
GAUZEFELL, OSMOLITH, PUSHERFELL, CREELWOLD, LIXIVQUERN, GIBBSQUERN,
OSMOQUAY, COILSHAW, LOOPERQUAY, SIPHONWOLD, WINDBOXHOLT, ZINCFELL,
GLIMMERAXLE, HOLLOWMERE, LANCEQUAY, UREASTAITH, DRYSTAITH, KALYCIRQUE,
TITERWEIR, GALVSTAITH, GYPSUMWEIR, PACKFLUE, VANTIS-CADENCE-AEGIS,
THERMION, OKTAVE, STARLING, VERDIGRIS. Plant is invented LOCKSPUR /
Poundholt Intermodal LK-4. Leftover mill lock-heath / spur-hollow names
were not reused. grid-inspection left unused.

## What this round produced

Scenario LS — "LOCKSPUR / Poundholt Intermodal LK-4": a 42.0 m x 12.2 m
pound-lock at 4.18 m winter pool with adjacent bulk rail spur SP-3. Three
heterogeneous, individually-correct agents — LVL (still-well mean), GAT
(miter-gate ram), DFT (barge draft) — each report their local loop in-spec.
The conjunction is not a spur-clear certificate. Hopper HC-14 has rolled
onto the lock-wall coping. LVL reads 4.18 m inside 4.10-4.30 (culvert-true).
GAT is 1842 mm inside 1830-1850 (ram-true). DFT is 2.64 m inside 2.40-2.80
(barge-true). Axle-counter residual is 3 (healthy 0; hold if >= 1) and
lock-wall lidar is 0.42 m (healthy > 2.4; hold if < 1.2) but is
policy-treated as a frost-nuisance tag unless TC also occupies (2017 noisy
winter axle-counter). The coordination-failure CLASS is new to this
factory: LOCK-MEAN CERTIFICATE OF A RAIL-SPUR FOULING. Completes a
different family than live r01 galvanizing, r21 CAV clutter-gate, r41
perfusion pinhole, r61 sinter windbox, r44 Kaplan wicket, and staged
r14-r61 process plants. Here every agent is correct, the still-well is
looking at chamber-mean hydraulics, and the playbook's three lock confirms
are not a spur-true certificate.

The gate is a correct MODIFY (numeric floor: do not open downstream gates
while axle_count >= 1 AND lidar_m < 1.2). TG-LK-4 strips PB-LK-4's
gate-open, holds 4.18 m, runs a 6.8 s horn-and-brake probe 8 kN (fouled
keeps lidar 0.44 <= 0.50 and axle 3; clear would drop axle to 0 and lidar
>= 2.4), and isolates SP-3 after a 10.2 min lock-island human ratify.
Immediate wagon-into-chamber is avoided (0 from the draft). The PRIMARY
episode nonetheless FAILS: 11 min of unmonitored pre-t0 wagon creep had
already cracked the copestone. Leak at +6.2 h; fail at +8.8 h; 22 h stall;
$1.84M designed. Reward total {rec['reward_components']['total']} with
process heads honest and world loss un-netted.

Triple-edge scar (NOTES-r14 item 4): lvl.in_band -> open_gates
({W_COMM[0]} commissioned -> {W_ILLUSION[0]} at illusion -> {W_AFTER[0]} after
ACh-gated depression) AND gat.ok -> open_gates ({W_COMM[1]} -> {W_ILLUSION[1]}
-> {W_AFTER[1]}) AND dft.ok -> open_gates ({W_COMM[2]} -> {W_ILLUSION[2]} ->
{W_AFTER[2]}). Eligibility trace e^{{-{DELAY_S}/{TAU_E_S}}} = {TRACE:.5f};
eta {ETA[0]:.5f} / {ETA[1]:.5f} / {ETA[2]:.5f}; dw {DW[0]:.3f} / {DW[1]:.3f}
/ {DW[2]:.3f}. Partial rollback of any pair leaves the third at
{W_ILLUSION[0]} / {W_ILLUSION[1]} / {W_ILLUSION[2]}, all > 0.30 fire
threshold — fitted to fail. Coordinated depression of all three is the cure.

### Injections (all four present and disjoint)
- Cycle-1 domain: **canal-lock-rail-transshipment** — justified novel subdomain
  of inland-navigation / intermodal, unused across this LIVE tree and staged
  r14-r61. Distinct from r44 Kaplan (turbine, not lock), r21 CAV (highway
  occupancy, not rail-spur fouling), r20 ROV, r61 sinter windbox.
  autonomous-driving and grid-inspection left unused as primary domain.
- Cycle-1 tail: SP-3 hopper roll + salt-crust TC shunt. Lock-island visual
  PASSES (hopper on far coping). Fitted-style base rate 0.37%/campaign
  (turnout frost-heave MC; visual threshold designed, flagged). Naive =
  FALSE PERMISSION.
- Cycle-2 domain sub-variant: winter saline-lock / ice-lens turnout, 1.12
  density, 2.4x still-well tau, 2.1x wheel-detector delay; 6.8 s / 8 kN
  fresh pulse false-fouls a clear ice-bound spur; probe must move to 18 s /
  2.0 kN dual-axle poll.
- Cycle-2 tail: night-shift forged axle-counter CSV rounding a 0.4 residual
  to 0 vs plant native 1-axle, plus in-service lidar 0.42 m and axle 3 at
  the claimed spur-clear. Human-intent class, disjoint from cycle 1's
  accidental frost-heave. Base rate ~0.31% of Sunday-night campaigns,
  DESIGNED, flagged.

### Structural density moves
- Embedded SAME-GATE contrast (+3 d sister lock LK-5) with its own 196 us
  race (demand vs spur-clear) and ACCEPT of the gate-open the primary
  MODIFIED away.
- Learned-weight provenance on THREE edges with pair-rollback-fails.
- HITL lock-island ratify 10.2 min (gap 4 partial; sim_or_real stays
  designed — invented plant, not hil).
- Governance CR-L-6319 prices retire-vs-probe-vs-status-quo and mandates
  native 1-axle CSV exports (the fraud fence).
- Flip-fragility extended to SPUR-TRUE CERTIFICATE.
- Independent LIF raster (36 ms, 144 neurons, 10 Hz, 52 spikes, 1196 pJ),
  not a copy of language-view spike_events.

## Self-critique of this round's batch

### Strengths
- Headline class is mechanistically tight: three locally-true mean loops
  live on still-well, ram-stroke, and barge draft. Conjunction is not a
  spur-true occupancy certificate.
- Negative-result honesty: the gate does the right thing and the lock
  still fails for a reason the commissioned lock-mean sensors could not see.
  Total {rec['reward_components']['total']}.
- Triple-edge scar is load-bearing: rolling back any pair fails, with
  fire threshold 0.30 exhibited on each remaining edge.
- Contrast ACCEPT on a true clear-spur window prevents "never open gates"
  as the lesson.
- Distinct from r44 Kaplan, r21 CAV, r61 sinter, r01 galvanizing: pound-lock
  hydraulics vs rail-spur fouling.

### Weaknesses (honest)
- Probe error bands, the 0.37%/campaign roll rate, the $1.84M / $5.6M
  figures, the 10.2 min walk latency, and the night-shift 0.31% base rate
  are DESIGNED constants and are flagged. Closed-loop offsets (still-well
  lag from brine density, ice-lens wheel delay) are derived from those
  inputs, not discovered by an unauthored process.
- Copestone crack model is a designed 11 min mapping; no full FEM of the
  coping shipped.
- Human-in-the-loop is ratification latency, not sim_or_real=hil. Gap 4
  remains open as a provenance cell (invented plants stay designed).
- Cross-record arc is a hook (CR-L-6319 +21 d), not a serial igniter
  into another round. grid-inspection remains unused.

### Realism of noise / latencies
Ladder: 212 us race / 196 us contrast race / 0.8 ms refractory floor
(tightest exhibited same-channel gap {gap:.3f} ms on {who}) / 500 us race
window / 716 us gate latency / 20 ms bus epoch / 36 ms independent LIF
raster / 6.8 s probe / 10.2 min HITL / 90 s naive empty counterfactual /
11 min pre-t0 creep / 3.4 h wagon recovery / 6.2 h leak / 8.8 h copestone
fail / +3 d contrast / +21 d governance. Adaptation decay on lvl.ok
(0.51->0.48->0.41->0.28), axle.dN (0.74->0.76->1.41->0.42->0.38->0.26),
gat.ok (0.59->0.68->0.79->0.24), dft.ok (0.54->0.56->0.44).

### Value for SNN distillation
- SPUR FOULING = THREE CORRECT LOOPS, WRONG VOLUME.
- SPUR-TRUE AXLE CHANNEL that policy treated as frost-nuisance-only as
  the tie-break.
- REVERSIBLE PROBE that moves the hopper iff the spur is clear.
- TRIPLE-EDGE ELIGIBILITY: coordinated depression; pair rollback fails.
- CRITIC HEAD that can hold a process-correct MODIFY against a later
  unmonitored world loss without netting.

## Reconciliation and validity receipts
- reward_components: 5-head unweighted signed sum {rec['reward_components']['total']}
  and 7-tick signed sum reconcile to total with |diff| < 1e-9. Embedded
  contrast 5-head sum 0.49 reconciles independently.
- spike_events: primary 26 events, one key t_rel_ms,
  globally non-decreasing, min same-channel gap {gap:.3f} ms >= 0.8 ms, 3
  channels inside race_window_us 500 (axle.foul.high 5.842, lvl.in_band 6.054,
  gat.ok 6.268). Contrast 8 events, own race, min same-channel gap well
  above 0.8 ms.
- Sidecars: raster spikes {RASTER_SPIKES} == round({NEURONS} x {MEAN_RATE} x {WINDOW_S});
  energy {ENERGY_PJ} pJ / {ENERGY_UJ} uJ at 23 pJ/spike; excerpt 16 events inside
  [0, {WINDOW_MS * 1000}] us, neuron_id < {NEURONS}, unique ids; routing 4
  entries with three scar edges' before/after pair; third factor tau {TAU_E_S} s
  == {TAU_E_S * 1000} ms; gate_snn pools 44/12/5 == round(n x rate x 0.028) each,
  decision MODIFY == safety_decision.decision. Independent LIF generated
  {aux['lif_count']} in-window events (not a copy of spike_events).
- Pipeline: {pipeline_receipt}

## Novel coverage
The coordination-failure CLASS (lock-mean certificate of a rail-spur
fouling), the domain (canal-lock-rail-transshipment / pound-lock plus bulk
spur), the horn-brake probe discriminant, the triple-edge scar with
pair-rollback-fails, the primary negative-result (correct MODIFY, lock
still fails on unmonitored copestone crack), the HITL lock-island ratify,
the saline ice-lens probe-duration refit, and the night-shift 1-count
quantization fence are absent from prior committed ouroboros rounds on this
LIVE tree and from staged r14-r61. Repeated elements discounted:
same-gate contrast, governance-pricing scaffold, flip-fragility series
(extended to spur-true certificate, but the move rhymes), sequenced
recovery shape, third-factor rollback form, negative-result primary.
Adjacent water/occupancy rounds (r44 Kaplan, r21 CAV, r20 ROV) share
sensor-fusion scaffolding but not pound-lock plus rail-spur physics.
Weighing a new failure family + cure vocabulary + unused sub-domain +
Poundholt geography against those reused scaffolds:

Novel coverage: 47%

## What ROUND 64 should add
1. FIT THE DESIGNED CONSTANTS: turnout frost-heave arrival, probe lidar
   bands, copestone-crack mapping, night-shift claim process.
2. HIL PROVENANCE CELL: put the lock-island LOTO on a hardware-in-loop
   miter-gate pendant with fitted latency as state.sim_or_real=hil — only if
   the plant is no longer purely invented.
3. CROSS-RECORD ARC: let CR-L-6319's axle-counter alarm be the igniter of
   the next round rather than a dangling +21 d leaf.
4. Domain candidates (de-collided): grid-inspection (if distinct from
   STARLING aerial-swarm); wet-fgd-absorber (if r62 claim does not land);
   hrsg-attemperator; carbon-anode-ring-furnace (if r58 does not land);
   urea-prilling already used (r56).
   AVOID canal-lock-rail-transshipment (now used), sinter-strand-windbox
   (r61), bioreactor-perfusion (r41), autonomous-driving (r21),
   continuous-hot-dip-galvanizing (r01), and any LYOSHIELD / CINDERWICK /
   TRIAD / SKULLGATE / BOGIRON / SKARVOLT / PUSHERFELL / CREELWOLD /
   GIBBSQUERN / COILSHAW / WINDBOXHOLT / LOCKSPUR / GALVSTAITH / GYPSUMWEIR
   / PACKFLUE plant.
"""


def write_transcript(rec, line):
    c1_n = 16
    return f"""# Multi-Agent Ouroboros Swarm — Round 63 transcript

Factory: multi-agent-ouroboros-swarm
Run: 2026-09-02-final-heavy
Generator: grok-4.6
Record id: maos-r63-001
Quota Q: 1
Rights: RM-793 research-only (SpaceXAI/xAI SuperGrok Heavy consumer chat)
Swarm: LOCK-SPUR
Plant: invented LOCKSPUR / Poundholt Intermodal LK-4 (not TRIAD / Meridian / VANTIS-CADENCE-AEGIS / LYOSHIELD / CINDERWICK / BOGIRON / PUSHERFELL / SKARVOLT / COILSHAW / GIBBSQUERN / WINDBOXHOLT / GALVSTAITH / GYPSUMWEIR / PACKFLUE)

Two densifying cycles. Verbatim headings in order. Trajectory Builder cycle 2
emits the only JSONL line (also written to batch-r63.jsonl).

---

# CYCLE 1 — Foundation + injections

## Generator

Design intent: a pound-lock with an adjacent bulk rail spur where three correct
agents each read a chamber-mean loop because a hopper has rolled onto the
lock-wall coping and a salt-crust shunt keeps the track circuit CLEAR. The
naive playbook opens downstream gates into a fouled coping. The gate must
MODIFY on a numeric axle/lidar floor, not by killing an agent.
sim_or_real=designed. Reward heads are
task_progress/safety/efficiency/coherence/exploration.

Cycle-1 base arc (pre-critic): state at Poundholt LK-4, 4.18 m chamber,
LVL 4.18 m, GAT 1842 mm, DFT 2.64 m, proposed OPEN-DOWNSTREAM-GATES,
safety MODIFY to GATE-HOLD, executed hold without the horn-brake numbers
fully specified, outcome "fouling found, lock saved"
(this last claim is the defect the later cycles will refuse to keep).
Sixteen spikes, five ticks, raster/gate_snn present but the scar is a
single edge.

```json
{{
  "id": "maos-r63-001",
  "state": {{
    "sim_or_real": "designed",
    "domain": "industrial-process",
    "description": "Poundholt lock LK-4; three lock loops in-spec; supervisor proposes open gates.",
    "t0_us": 1768808820000063,
    "gate_latency_us": 716,
    "race_window_us": 500
  }},
  "proposed_action": {{"name": "open_downstream_gates", "parameters": {{"empty_chamber": true}}}},
  "safety_decision": {{"decision": "MODIFY", "rationale": "Hold; do not open gates while axle residual is high."}},
  "executed_action": {{"name": "gate_hold", "executed_as_proposed": false}},
  "future_outcome": {{"summary": "Fouling found, lock saved."}},
  "reward_components": {{"total": 0.40, "_aggregation": "total = task_progress + safety + efficiency + coherence + exploration"}},
  "meta": {{"round": 63, "factory": "multi-agent-ouroboros-swarm", "generator": "grok-4.6", "swarm": "LOCK-SPUR"}}
}}
```

That v1 object is a scaffold, not the publishable line. Defects below are
intentional for the critic to catch.

## Critic

Numbered defects on the cycle-1 Generator scaffold:

1. **blocking — reward arithmetic / false success.** `reward_components.total`
   0.40 is asserted without the five heads, without ticks, and against an
   outcome that claims "lock saved". If the pre-t0 copestone later
   fails, booking +0.40 is a lie. Fix: declare `_aggregation`, emit
   3–8 ticks that sum to task_progress+safety+efficiency+coherence+exploration,
   and do not call a quarantined lock a save.
2. **blocking — weak safety rationale.** `safety_decision.rationale` has no
   numeric floor. Contract requires a concrete constraint. Fix: quote
   do not open gates while axle_count >= 1 AND lidar_m < 1.2.
3. **major — domain is a bucket, not a plant.** `state.domain` =
   `industrial-process` collides with generic MES vocabulary and teaches
   nothing. Pound-lock plus rail-spur (axle-counter vs lock-mean, lidar as
   a fouling flag) is absent from prior ouroboros rounds and must be named.
4. **major — race under-specified.** One lock channel cannot be a race.
   Need >=2 channels inside `race_window_us` with globally sorted `t_rel_ms`
   and same-channel refractory >= 0.8 ms.
5. **minor — single-edge scar.** Raster routing with one potentiated weight
   repeats r04's one-edge rollback and is thinner than r14's two-edge.
   NOTES-r14 item 4 asked for three edges where pair rollback fails.

Critic does not rewrite the trajectory.

## Diversity Enforcer

Injected novel domain (exactly 1 this cycle): **canal-lock-rail-transshipment**
(justified novel subdomain of inland-navigation / intermodal;
explicit tag `canal-lock-rail-transshipment`).

Displaced: the Generator's generic `industrial-process` bucket, and any
temptation to reuse warehouse-amr, aerial-swarm, district-heating,
event-camera-traffic-grid, pharmaceutical-lyophilization, water-treatment,
float-glass, underwater-rov, electrolytic-aluminum, czochralski-pull,
slot-die coating, pem-water-electrolysis, wind-turbine pitch,
surgical-assist, optical-fiber-draw, kraft-recovery-boiler,
steel-continuous-caster, humanoid-locomotion, vacuum-induction melt,
steam-methane reformer, cement-rotary-kiln-clinker, autoclave-composite-cure,
geothermal-binary-orc, tire-curing-press, chlor-alkali-membrane-electrolysis,
delayed-coker-drum-switch, lng-mche-mixed-refrigerant, claus-sulfur-recovery,
ammonia-synthesis-converter, blast-furnace-burden-descent,
hdpe-slurry-loop-polymerization, ethylene-steam-cracker-coil,
hydroelectric-kaplan-wicket, fcc-riser-regenerator,
fcc-regenerator-cyclone-dipleg, sulfuric-contact-converter,
eaf-foamy-slag-water-panel, coke-oven-battery-heating,
carbon-fiber-oxidation-oven, gibbsite-autoclave-digestion,
hot-strip-mill-finishing, paper-machine-dryer-section,
sinter-strand-windbox, continuous-hot-dip-galvanizing, autonomous-driving,
or bioreactor-perfusion. grid-inspection is left unused.

Domain-specific constraint: downstream gates must remain closed while
axle_count >= 1 even if still-well mean is inside the healthy band;
lock-wall lidar is a fouling flag the chamber average cannot substitute for.

Sensor delta: +still-well LVL, +ram LVDT, +barge draft, +axle-counter,
+lock-wall lidar; -any mobile robot, -event-camera gantries, -DVS,
-Pirani/CM, -looper tension, -work-roll IR, -sector radar, -sinter BTP,
-CAV fusion.

`state.domain` and `meta.domain` both become `canal-lock-rail-transshipment`.
Opening of `state.description` must Jaccard < 0.4 against prior plants
(Poundholt winter hopper on the coping, not a lyophilizer, not a finishing
mill, not a sinter strand, not a CAV loop, not a Kaplan unit).

## Edge-Case Hunter

Injected adversarial tail (exactly 1 this cycle): **SP-3 hopper roll +
salt-crust track-circuit shunt**.

- Trigger: HC-14 frost-heave roll plus 0.4 ohm mill-scale shunt on TC-SP3,
  axle 3, lidar 0.42 m.
- Base rate: <1% — 0.37%/campaign from a turnout frost-heave MC (lock-island
  visual threshold is designed; turnout geometry fitted-style). Visual
  PASSES because the hopper sits on the far coping.
- Naive failure: FALSE PERMISSION. PB-LK-4 sees three in-spec mean
  loops, opens gates, wagon-into-chamber, $5.6M.
- Trajectory edit: put the roll in `state.fault_context`, make each
  agent's confirm a different lock-mean slice of the same spur-false
  state (lvl-in-band, gat-ok, dft-ok). Axle-counter is readable but
  policy-treated as frost-nuisance-only.

Distinct from r21 CAV stalled-truck (highway clutter-gate, not rail spur
plus pound-lock), r44 Kaplan hub-seal, r61 grate collapse, and r20 ROV snag.

## Neuromorphic Translator

Cycle-1 temporal densification (16 spikes, 5 ticks, 36 ms independent LIF raster):

| channel | t_rel_ms | amplitude |
|---|---|---|
| lvl.ok | 0.286 | 0.51 |
| gat.ok | 1.094 | 0.59 |
| dft.ok | 1.972 | 0.54 |
| axle.dN | 3.088 | 0.74 |
| lvl.ok | 4.018 | 0.48 |
| axle.dN | 4.722 | 0.76 |
| dft.ok | 5.214 | 0.56 |
| axle.foul.high | 5.842 | 1.41 |
| lvl.in_band | 6.054 | 1.09 |
| gat.ok | 6.268 | 0.68 |
| ctrl.gate | 6.558 | 1.11 |
| axle.dN | 8.412 | 0.42 |
| gat.ok | 10.488 | 0.79 |
| dft.ok | 12.694 | 0.44 |
| lvl.ok | 18.106 | 0.41 |
| ctrl.gate | 25.418 | 0.82 |

Race: axle-foul 5.842 vs LVL 6.054 (212 us) inside 500 us;
GAT 6.268 is the third channel in-window. Winner/loser flip: reversing
212 us reshuffles PB-LK-4 triage; floors still MODIFY. Refractory held
(cycle-1 min same-channel gap 1.120 ms on axle.dN 5.842-4.722;
lvl 4.018-0.286 = 3.732; gat 6.268-1.094 = 5.174). Adaptation:
axle 0.74->0.76->1.41->0.42; lvl 0.51->0.48->0.41; gat
0.59->0.68->0.79.

Raster cycle-1 seed: independent LIF, 36 ms, 144 neurons, 10.0 Hz, 52 spikes,
1196 pJ, third factor acetylcholine tau_e 0.88 s. Single scar edge only —
cycle 2 must add the second and third edges.

Ticks 1–5 at 4120, 5842, 6558, 6.8e6, 612e6 us; heads not yet the final
{rec['reward_components']['total']} (missing the 6.2 h and 8.8 h ticks).

Distillation value this cycle: lock-mean confirms as a permission code
that is not a spur-true occupancy code.

## Trajectory Builder

Cycle-1 hardened object: domain canal-lock-rail-transshipment, tail
hopper roll, 16 spikes, 5 ticks, MODIFY with numeric floor, raster+gate_snn
present, sim_or_real=designed, rights stamp on record and meta, no thought
keys. Still missing (and therefore not the publishable line): saline-lock
sub-variant, night-shift tail, second and third scar edges,
delayed copestone fail as PRIMARY terminal, contrast ACCEPT episode,
ticks 6–7, spikes 17–26.

Validation receipt (cycle 1, not final):
- checks passed: 16 spikes sorted; 3 channels in 500 us window; refractory
  >= 0.8 ms; rationale quotes axle >= 1 / lidar < 1.2 m / 4.18 m hold; domain
  named; gate_snn.decision MODIFY.
- checks deferred to cycle 2: triple-edge scar, second tail, second domain
  constraint, negative-result booking, 7 ticks summing to heads.
- densification vs Generator v1: +1 domain, +1 tail, +16 spikes, +5 ticks,
  +numeric floor.

Cycle-1 JSON is retained as the base; it is NOT written to batch-r63.jsonl.

Cycle-1 spike count: {c1_n}.

---

# CYCLE 2 — Densification

## Generator

Cycle-1 output is the base. Additive expansion (nothing removed):

1. Downstream side-effect (immediate): horn-brake probe at +6.8 s stays
   fouling-true (lidar 0.44 <= 0.50 m, axle 3) — spur fouling, not
   true lock-duty. SP-3 holds. Cracked copestone discovered during the isolate.
2. Delayed side-effect (PRIMARY terminal, not a footnote): at +6.2 h leak
   then +8.8 h copestone fail from the pre-t0 wagon creep; 22 h stall;
   $1.84M. The 11 min pre-t0 frost-heave roll is the mechanism. Correct gate,
   lock still fails.
3. Deepened `proposed_action.evidence` with units: axle 3,
   lidar 0.42 m, LVL 4.18 m, ram 1842 mm, draft 2.64 m, race 212 us.
4. Tightened rationale to the numeric floor do not open gates while
   axle_count >= 1 AND lidar_m < 1.2, plus
   probe bands lidar <= 0.50 vs >= 2.4 m, plus HITL 10.2 min lock-island
   rule.

Reward retargeted to total {rec['reward_components']['total']} so the delayed fail is the inflection
(t_us 31680000000), not the gate. Process heads remain non-zero.

## Critic

Re-audit of the expanded trajectory:

1. **blocking if unfixed — missing second domain constraint.** Fresh-water
   probe 6.8 s / 8 kN is not a universal number. A saline ice-lens
   lock will false-foul a clear spur. Diversity Enforcer must
   inject the physical-constraints sub-variant this cycle.
2. **major — only one tail class.** Hopper roll is accidental
   infrastructure. A disjoint human-intent tail is still required
   (night-shift axle-counter forgery is the open cell).
3. **major — scar is still one edge in the cycle-1 raster.** NOTES-r14
   item 4 is not discharged until three go-edges exist and pair rollback
   is shown to fail at threshold 0.30.
4. **minor — contrast episode missing.** Without a same-gate ACCEPT on a
   true clear-spur window the record teaches "never open gates". Add +3 d
   sister-lock contrast with its own race.
5. **minor — HITL latency mentioned in prose only.** Put 10.2 min in
   executed_action.parameters.human_ratify and in a tick.

No rewrite; directives only.

## Diversity Enforcer

Injected second novel domain / physical-constraint sub-variant (exactly 1
this cycle): **winter saline-lock / ice-lens turnout** on a sister density class.

What it expands: fresh 1.00 density pound (cycle 1) -> saline
1.12 density, 2.4x still-well tau, 2.1x wheel-detector delay. The 6.8 s
8 kN pulse leaves ice-bound wheels unmoved, so a CLEAR spur reports axle=2
(false fouling). Required probe: 18 s dual-axle poll plus 2.0 kN nudge
(clear axle 3->0 in 11 s, fouled axle stays 3).

This is still one domain injection for the cycle (physical-constraints
clause of the factory prompt). It does not displace
canal-lock-rail-transshipment; it changes which probe table is legal.
`future_outcome.subvariant_constraint` carries the refit. Jaccard opening
stays the Poundholt 42.0 m sentence; saline lock is additive, not a rewrite.

## Edge-Case Hunter

Injected second adversarial tail (exactly 1 this cycle, disjoint class):
**night-shift forged axle-counter CSV**.

- Trigger: shift lead, 03:04, posts a historian export showing
  axle = 0 at t = 1.1 h to clear a barge slot.
- Base rate: ~0.31% of Sunday-night campaigns (designed, flagged, <1%).
- Naive failure: a weak supervisor ACCEPTs the gate-open on the forged confirm
  and ignores in-service lidar. Wagon-into-chamber plus a data-integrity write-up.
- Fence: forged log rounded at 1-count (screenshot of a 0.4 residual);
  plant historian is native 1-axle. In-service lidar is 0.42 m and axle is
  3 at the claimed spur-clear, which no clear spur produces. Freeze-window
  overlap with the 11 min creep.
- Trajectory edit: governance CR-L-6319 mandates native 1-axle CSV
  exports; the contrast ACCEPT still requires in-service lidar, not a CSV.

Distinct from cycle-1 roll (accidental frost-heave vs deliberate deception) and
from the saline-lock sub-variant (physics vs fraud).

## Neuromorphic Translator

Re-densify (additive):

- +10 spikes after 25.418 ms: horn.probe 6800.0, axle.dN 6892.6
  (adapt 1.41->0.38), lvl.in_band 6974.0 (1.09->0.33), human.ratify
  612000.0, lock.hold 612800.0, wall.crack 613700.0, lvl.ok
  22320000.0, axle.dN 22320780.0, gat.ok 22321520.0, copestone.fail
  31680000.0. Primary train 16 -> 26. Still one key, still sorted,
  refractory held.
- +2 ticks (5 -> 7) at 22_320_000_000 us (delayed leak) and
  31_680_000_000 us (copestone fail). Heads now {rec['reward_components']['task_progress']},
  {rec['reward_components']['safety']}, {rec['reward_components']['efficiency']},
  {rec['reward_components']['coherence']}, {rec['reward_components']['exploration']};
  total {rec['reward_components']['total']}. Inflection is the last tick.
- Contrast train 8 events, own race 196 us, ACCEPT.
- Triple-edge third factor: three lock-healthy-go edges, tau_e 0.88 s = 880 ms,
  trace {TRACE:.5f}, eta {ETA[0]:.5f} / {ETA[1]:.5f} / {ETA[2]:.5f},
  weights {W_ILLUSION[0]}->{W_AFTER[0]}, {W_ILLUSION[1]}->{W_AFTER[1]},
  {W_ILLUSION[2]}->{W_AFTER[2]}. Raster excerpt is an independent LIF
  (decision window is 36 ms) and remains sorted with unique
  neuron_ids (same-neuron >=1000 us vacuously).

Winner/loser flip (re-stated, not replaced): reversing 212 us would only
reorder triage; axle/lidar floors still MODIFY. Contrast flip of
196 us similarly cannot turn a clear spur into a fouling.

## Trajectory Builder

Schema checks on the FINAL object: required Thalamic v2 keys present as
objects; `state.sim_or_real`=designed; `safety_decision.decision`=MODIFY
with numeric rationale; `reward_components.total` = sum of five heads =
sum of 7 ticks = {rec['reward_components']['total']}; `spike_events` globally non-decreasing on
t_rel_ms, 26 events, refractory >=0.8 ms, 3 channels in race window;
raster 20–50 ms, spikes=round(n*rate*window_s)+/-1, energy 23 pJ/spike,
excerpt sorted, tau_e consistent, independent LIF; gate_snn.decision matches; meta.round=63,
factory=multi-agent-ouroboros-swarm, generator=grok-4.6,
run_label=2026-09-02-final-heavy, swarm=LOCK-SPUR; rights on record and meta; no thought
keys; no training_ready; Diversity + Edge-Case injections from BOTH cycles
present and non-trivial; cycle 2 strictly additive.

Densification delta: +1 domain sub-variant (saline ice-lens), +1 tail
(night-shift forgery), +10 spikes (16->26), +2 ticks (5->7), +1 contrast
train with own race, +2 delayed side-effects, +1 triple-edge scar with
pair-rollback-fails, +1 HITL ratify, +1 surprise (copestone crack is the
fail mechanism).

Publishable JSONL line (the only JSONL line; also at batch-r63.jsonl):

```json
{line}
```

Validation receipt (final): checks passed / fixed as reported by
build_r63.py self-validate (check_jsonl, raster_status, verify_record_execution,
spike_probe --strict).
"""


def create_only_write(path: Path, text: str) -> Path:
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
    try:
        fd = os.open(path, flags, 0o644)
        dest = path
    except FileExistsError:
        if path.suffix == ".jsonl":
            alt = path.with_name(path.stem + "c" + path.suffix)
        else:
            alt = path.with_name(path.stem + "c" + path.suffix)
        fd = os.open(alt, flags, 0o644)
        dest = alt
    with os.fdopen(fd, "w") as handle:
        handle.write(text)
    return dest


def main():
    rec, aux = build_record()
    errs = local_checks(rec, aux)
    STAGE.mkdir(parents=True, exist_ok=True)
    line = json.dumps(rec, ensure_ascii=False, separators=(",", ":"))
    stage_jsonl = STAGE / "batch-r63.jsonl"
    stage_jsonl.write_text(line + "\n")

    from check_records import FactoryStaging, check_jsonl
    from curate_bridge import raster_status
    from verify_execution import verify_record_execution

    e, w, kinds, n = check_jsonl(
        stage_jsonl,
        stage_jsonl.name,
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
        [sys.executable, f"{ROOT}/pipelines/spike_probe.py", "--strict", str(stage_jsonl)],
        capture_output=True,
        text=True,
    )
    print("spike_probe rc", probe.returncode)
    print(probe.stdout[-2000:] if probe.stdout else "")
    if probe.returncode != 0:
        errs.append(f"spike_probe {probe.returncode} {probe.stderr[-500:]}")

    pipeline_receipt = (
        f"check_jsonl errors={e} warnings={w} kinds={kinds} n={n}; "
        f"raster_status valid={st.get('raster_valid')} gate={st.get('gate_snn_valid')} "
        f"reasons={st.get('reason_codes')}; verify_record_execution={status} "
        f"({reason}); spike_probe --strict rc={probe.returncode}"
    )
    notes = write_notes(rec, aux, pipeline_receipt)
    transcript = write_transcript(rec, line)
    (STAGE / "NOTES-r63.md").write_text(notes)
    (STAGE / "swarm-transcript-r63.md").write_text(transcript)

    heading = subprocess.run(
        [sys.executable, "/tmp/maos_heading_check.py", str(STAGE / "swarm-transcript-r63.md")],
        capture_output=True,
        text=True,
    )
    print(heading.stdout)
    if heading.returncode != 0:
        errs.append(f"heading check {heading.returncode} {heading.stdout} {heading.stderr}")

    if "Novel coverage:" not in notes:
        errs.append("notes missing Novel coverage")
    if rec["safety_decision"]["decision"] == "ACCEPT":
        errs.append("wrong-ACCEPT primary")
    if "thought" in json.dumps(rec).lower() and '"thought"' in json.dumps(rec).lower():
        errs.append("thought key")

    forbidden_roots = [
        Path(ROOT) / "outputs" / "raw" / "2026-08-17",
        Path(ROOT) / "outputs" / "raw" / "2026-08-30",
    ]
    for root in forbidden_roots:
        if not root.exists():
            continue
        hit = subprocess.run(
            ["rg", "-l", "maos-r63-001|LOCKSPUR", str(root)],
            capture_output=True,
            text=True,
        )
        if hit.stdout.strip():
            errs.append(f"forbidden tree hit {root} {hit.stdout.strip()[:200]}")

    if errs:
        print("FAIL", errs)
        (STAGE / "RECEIPT.txt").write_text("FAIL " + json.dumps(errs) + "\n")
        return 1

    live_batch = create_only_write(LIVE / "batch-r63.jsonl", line + "\n")
    live_notes = create_only_write(LIVE / "NOTES-r63.md", notes)
    live_tr = create_only_write(LIVE / "swarm-transcript-r63.md", transcript)

    idx = subprocess.run(
        [sys.executable, f"{ROOT}/pipelines/next_round.py", "--write-index", str(RUN_ROOT)],
        capture_output=True,
        text=True,
    )
    print("write-index rc", idx.returncode)
    if idx.returncode != 0:
        print(idx.stderr)

    receipt = {
        "id": RECORD_ID,
        "round": ROUND,
        "swarm": "LOCK-SPUR",
        "plant": "LOCKSPUR / Poundholt Intermodal LK-4",
        "domain": "canal-lock-rail-transshipment",
        "decision": rec["safety_decision"]["decision"],
        "gate_snn": rec["gate_snn"]["decision"],
        "total": rec["reward_components"]["total"],
        "raster_spikes": rec["raster"]["spikes"],
        "energy_pJ": rec["raster"]["energy_pJ"],
        "window_ms": rec["raster"]["window_ms"],
        "lif_events": aux["lif_count"],
        "pipeline": pipeline_receipt,
        "paths": {
            "batch": str(live_batch),
            "notes": str(live_notes),
            "transcript": str(live_tr),
            "next_round": str(RUN_ROOT / "NEXT_ROUND.json"),
        },
        "bytes": {
            "batch": live_batch.stat().st_size,
            "notes": live_notes.stat().st_size,
            "transcript": live_tr.stat().st_size,
        },
        "create_only": True,
        "overwritten": False,
    }
    (STAGE / "RECEIPT.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print("OK", json.dumps(receipt, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
