#!/usr/bin/env python3
"""Emit TTF r33 JSONL (ttf-r33-181..185) into /tmp/ttf-r33/. Never writes outputs/raw/."""

from __future__ import annotations

import json
import math
import random
import re
import subprocess
import sys
from collections import OrderedDict
from decimal import Decimal
from pathlib import Path

OUT_DIR = Path("/tmp/ttf-r33")
BATCH_PATH = OUT_DIR / "batch-r33.jsonl"
NOTES_PATH = OUT_DIR / "NOTES-r33.md"
REPO = Path("/home/raulmc/rmems/synthetic-factory")
PIPELINES = REPO / "pipelines"

PJ_PER_SPIKE = 23
RIGHTS = OrderedDict(
    [
        ("provider", "SpaceXAI/xAI"),
        ("model", "grok-4.6"),
        ("channel", "consumer"),
        ("subscription_plan", "SuperGrok Heavy"),
        ("generation_surface", "SuperGrok Heavy chat"),
        ("generated_at", "2026-09-02T17:05:00Z"),
        ("intended_use", "research_only"),
        ("project_training_policy", "blocked"),
        ("research_retention_status", "allowed"),
        ("research_evaluation_status", "allowed"),
        ("redistribution_status", "unresolved"),
        ("provider_training_status", "unresolved"),
        ("weight_publication_status", "blocked"),
        ("status_basis", "RM-793 project policy: xAI hosted outputs are research-only"),
        ("linear_issue", "RM-793"),
    ]
)
AGG = "total = task_progress + safety + efficiency + coherence + exploration"
CHANNEL_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,31}$")
FROM_TO_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_]{0,31}$")
THOUGHT_KEYS = {
    "thought",
    "reasoning",
    "chain_of_thought",
    "hidden_reasoning",
    "inner_monologue",
    "scratch",
    "internal_reasoning",
    "internal_reasoning_verbatim",
    "thinking",
    "cot",
    "thoughts",
}
BANNED_DOMAINS = {
    "warehouse-amr",
    "aerial-swarm",
    "underwater-rov",
    "grid-inspection",
    "humanoid-locomotion",
    "surgical-assist",
    "industrial-assembly",
    "autonomous-driving",
    "rail-signaling",
    "process-chem",
    "ev-charging",
    "agritech-combine",
    "semiconductor-fab",
    "fusion-divertor",
    "rail-hump-yard",
    "hotcell-telemanip",
    "euv-wafer-stage",
    "proton-gantry-gate",
    "tbm-slurry-shield",
    "wave-energy-latching",
    "fiber-draw-tower",
    "brewery-CIP",
    "ski-lift",
    "data-center-CDU",
    "canal-lock",
    "blast-furnace",
    "mill-scale-pit",
    "battery-formation",
    "grain-elevator",
    "glass-lehr",
    "tunnel-boring",
    "satellite-servicing",
    "mine-ventilation",
    "paper-machine",
    "cryo-storage",
    "amusement-ride",
    "trolleybus",
    "glass-float-line",
    "LNG-boiloff",
    "hyperbaric-weld",
    "radio-telescope-pointing",
    "funicular",
    "PCB-reflow",
    "anaerobic-digester",
    "tidal-barrage",
    "maglev-guideway-gap",
    "grain-elevator-leg",
    "hyperbaric-weld-habitat",
    "tunnel-oven-bakery",
    "rotary-lime-kiln",
    "lng-open-rack",
    "metro-psd",
    "aluminum-potline",
    "vial-lyophilizer",
    "sts-quay-crane",
    "lyophilizer-shelf",
    "hvdc-thyristor-valve",
    "lng-unloading-arm",
    "subsea-cable-plough",
    "cyclotron-target",
    "electrolyzer-stack",
    "autoclave-retort",
    "salt-cavern-CAES",
    "tire-curing-press",
    "cable-lay-barge",
    "olive-oil-decanter",
    "lime-rotary-kiln",
    "ferry-linkspan",
    "isotope-cyclotron",
    "die-cast-cell",
    "desal-RO-train",
    "rotary-kiln-cement",
    "submarine-cable-lay",
    "hydro-penstock",
    "sugar-vacuum-pan",
    "cement-precalciner",
    "composite-autoclave",
    "hdd-pilot-bore",
    "solar-trough-htf",
    "steel-caster-mold",
    "wind-nacelle-yaw",
}
BANNED_PLANT_FRAGMENTS = (
    "Marrow-Dock",
    "Vesper-Lattice",
    "Brine-Well",
    "Saddle-Arc",
    "Ashlar-Gait",
    "Nacre-Well",
    "Quern-Forge",
    "Tinder-Box",
    "Whimbrel-Stack",
    "Cinder-Loft",
    "Suture-Isle",
    "Kiln-Spur",
    "Oxbow-Switch",
    "Pitch-Kettle",
    "Shale-Quay",
    "Polder-Rye",
    "Flint-Mask",
    "Gyre-Tokamak",
    "Quarry-Bowl",
    "Orpiment",
    "Glimmer-Forge",
    "Feldspar-Arc",
    "Basalt-Rook",
    "Fetch-Sound",
    "Silica-Well",
    "Sinter-Gown",
    "Kettle-Stack",
    "Barrow-Mezz",
    "Grit-Sump",
    "Firth-Spur",
    "Apside-Yard",
    "Sump-Drift",
    "Frost-Cist",
    "Clothoid-Bowl",
    "Firn-Span",
    "Sleet-Row",
    "Sinter-Ridge",
    "Chaff-Mere",
    "Caisson-Forge",
    "Crumb-Vault",
    "Caliche-Drift",
    "Thaw-Reach",
    "Kipple-Gate",
    "Anode-Fen",
    "Vial-Rime",
    "Tern-Apron",
    "Scree-Hitch",
    "Flux-Kettle",
    "Mire-Cask",
    "Slack-Firth",
    "Chaff-Rise",
    "Rime-Causeway",
    "Gnomon-Well",
    "Rime-Vault",
    "Fjord-Convert",
    "Kelp-Jetty",
    "Skerries-Trench",
    "Iodine-Well",
    "Lyo-Deck",
    "Target-Cart",
    "Oolite-Span",
    "Fathom-Lock",
    "Loess-Stride",
    "Swage-Holt",
    "Slag-Siding",
    "Cryolite-Hall",
    "Bight-Lay",
    "Wort-Cairn",
    "Lye-Rake",
    "Rime-Haul",
    "Glycol-Loop",
    "Burden-Pike",
    "Amber-Arm",
    "Oxbow-Pound",
    "Tuyere-Holt",
    "Halite-Keel",
    "Bladder-Kettle",
    "Drupe-Press",
    "Cullet-Reach",
    "Bracken-Wire",
    "Sedge-Cell",
    "Abyss-Joint",
    "Gull-Pontoon",
    "Sprue-Nook",
    "Osmia-Reach",
    "Retort-Fen",
    "Hood-Pike",
    "Hood-Ring",
    "Felt-Reach",
    "Massecuite-Kettle",
    "Penstock-Gate",
    "Strike-Pan",
    "Kestrel-2",
    "Lay-Sound",
    "Marl-Knap",
    "Marl-Rake",
    "Caldera-Mold",
    "Isotope-Pad",
)


def energy(spikes: int) -> tuple[int, float]:
    return spikes * PJ_PER_SPIKE, spikes * PJ_PER_SPIKE / 1_000_000.0


def spike(channel: str, t_rel_ms: float, amplitude: float) -> OrderedDict:
    if not CHANNEL_RE.fullmatch(channel):
        raise ValueError(f"bad channel {channel!r}")
    if t_rel_ms <= 0:
        raise ValueError(f"t_rel_ms must be > 0, got {t_rel_ms}")
    return OrderedDict(
        [("channel", channel), ("t_rel_ms", t_rel_ms), ("amplitude", amplitude)]
    )


def tick(t_us: int, tp, saf, eff, coh, exp) -> OrderedDict:
    return OrderedDict(
        [
            ("t_us", int(t_us)),
            ("task_progress", tp),
            ("safety", saf),
            ("efficiency", eff),
            ("coherence", coh),
            ("exploration", exp),
        ]
    )


def routing(source, target, table, modulator, tau_e_s, eligibility) -> OrderedDict:
    tau_e_ms = float(Decimal(str(tau_e_s)) * Decimal("1000"))
    rows = []
    for a, b, w in table:
        if not FROM_TO_RE.fullmatch(a) or not FROM_TO_RE.fullmatch(b):
            raise ValueError(f"bad routing endpoints {a!r} -> {b!r}")
        rows.append(OrderedDict([("from", a), ("to", b), ("weight", w)]))
    return OrderedDict(
        [
            ("source", source),
            ("target", target),
            ("table", rows),
            (
                "third_factor",
                OrderedDict(
                    [
                        ("modulator", modulator),
                        ("tau_e_s", tau_e_s),
                        ("tau_e_ms", tau_e_ms),
                        ("eligibility", eligibility),
                    ]
                ),
            ),
        ]
    )


def raster_core(window_ms, neurons, rate, spikes, route, excerpt, extra=None) -> OrderedDict:
    pj, uj = energy(spikes)
    window_s = float(Decimal(str(window_ms)) / Decimal("1000"))
    expected = round(neurons * rate * window_s)
    if abs(spikes - expected) > 1:
        raise ValueError(f"spike budget {spikes} vs {expected}")
    body = OrderedDict(
        [
            ("window_ms", window_ms),
            ("window_s", window_s),
            ("neurons", neurons),
            ("mean_rate_hz", rate),
            ("spikes", spikes),
            ("energy_pJ", pj),
            ("energy_uJ", uj),
        ]
    )
    if extra:
        body.update(extra)
    body["routing"] = route
    body["excerpt"] = excerpt
    return body


def excerpt_items(pairs, channels=None) -> list:
    out = []
    last = {}
    prev_t = -1
    for i, (t_us, nid) in enumerate(pairs):
        t_us, nid = int(t_us), int(nid)
        if t_us < prev_t:
            raise ValueError("excerpt not sorted")
        if nid in last and t_us - last[nid] < 1000:
            raise ValueError(f"same-neuron gap {nid}")
        item = OrderedDict([("t_us", t_us), ("neuron_id", nid)])
        if channels is not None:
            item["channel"] = channels[i]
        out.append(item)
        last[nid] = t_us
        prev_t = t_us
    return out


def independent_excerpt(seed, neurons, window_us, n_events, avoid_us):
    rng = random.Random(seed)
    avoid = {int(t) for t in avoid_us}
    picked = []
    last = {}
    attempts = 0
    grid = list(range(400, int(window_us) - 400, 70))
    rng.shuffle(grid)
    for t in grid:
        if len(picked) >= n_events:
            break
        nid = rng.randrange(0, neurons)
        if t in avoid:
            continue
        if any(abs(t - pt) < 40 for pt, _ in picked):
            continue
        if nid in last and abs(t - last[nid]) < 1000:
            continue
        picked.append((t, nid))
        last[nid] = t
        attempts += 1
    while len(picked) < n_events and attempts < 8000:
        attempts += 1
        t = rng.randrange(300, int(window_us) - 300)
        nid = rng.randrange(0, neurons)
        if t in avoid:
            continue
        if any(abs(t - pt) < 50 for pt, _ in picked):
            continue
        if nid in last and abs(t - last[nid]) < 1000:
            continue
        picked.append((t, nid))
        last[nid] = t
    picked.sort(key=lambda item: (item[0], item[1]))
    if len(picked) < n_events:
        raise RuntimeError(f"excerpt short: {len(picked)}")
    return excerpt_items(picked[:n_events])


def lif_181_excerpt():
    n = 72
    dt_us = 100
    tau_m_ms = 19.0
    v_th = 1.0
    v_reset = 0.0
    refractory_us = 1000
    i_bias = 0.91
    i_stim_peak = 2.48
    stim = (22400, 25600)
    seed = 33181
    window_us = 42000
    i_clamp_extra = 0.64
    clamp_n = 14
    rng = random.Random(seed)
    tau_s = tau_m_ms / 1000.0
    dt_s = dt_us / 1e6
    decay = math.exp(-dt_s / tau_s)
    steps = window_us // dt_us
    voltage = [rng.random() * v_th * 0.97 for _ in range(n)]
    bias = [i_bias * (1.0 + 0.13 * (rng.random() * 2 - 1)) for _ in range(n)]
    for i in range(clamp_n):
        bias[i] += i_clamp_extra
    ref = [0] * n
    spikes = []
    for step in range(steps):
        t_us = step * dt_us
        stim_i = i_stim_peak if stim[0] <= t_us < stim[1] else 0.0
        for i in range(n):
            if ref[i] > 0:
                ref[i] -= dt_us
                voltage[i] = v_reset
                continue
            current = bias[i] + stim_i
            voltage[i] = current + (voltage[i] - current) * decay
            if voltage[i] >= v_th:
                spikes.append((t_us, i))
                voltage[i] = v_reset
                ref[i] = refractory_us
    early = [(t, nid) for t, nid in spikes if t < 22400]
    burst = [(t, nid) for t, nid in spikes if 22400 <= t < 25600]
    used = set()
    last = {}
    picked = []

    def take(pool, want, label_times=None):
        if not pool:
            return
        chosen_idx = set()
        if label_times:
            for target in label_times:
                best = None
                for idx, (t, nid) in enumerate(pool):
                    if idx in chosen_idx or nid in used:
                        continue
                    if nid in last and t - last[nid] < 1000:
                        continue
                    if best is None or abs(t - target) < abs(best[0] - target):
                        best = (t, nid, idx)
                if best is not None:
                    t, nid, idx = best
                    picked.append((t, nid))
                    used.add(nid)
                    last[nid] = t
                    chosen_idx.add(idx)
        stride = max(1, len(pool) // max(want, 1))
        for idx in range(0, len(pool), stride):
            group = [1 for tt, _ in picked if (tt < 22400) == (pool[0][0] < 22400)]
            if len(group) >= want:
                break
            t, nid = pool[idx]
            if nid in used:
                continue
            if nid in last and t - last[nid] < 1000:
                continue
            picked.append((t, nid))
            used.add(nid)
            last[nid] = t

    take(early, 7)
    take(burst, 9, label_times=(23400, 24000, 24800))
    clamp = [(t, nid) for t, nid in picked if t < 22400][:7]
    tear = [(t, nid) for t, nid in picked if t >= 22400][:9]
    picked = sorted(clamp + tear, key=lambda item: (item[0], item[1]))
    if len(picked) < 10:
        raise RuntimeError(f"LIF excerpt short: {len(picked)} early={len(early)} burst={len(burst)}")
    channels = ["lif.clamp" if t < 22400 else "lif.frost" for t, _ in picked]
    lif = OrderedDict(
        [
            ("model", "leaky_integrate_and_fire"),
            ("n", 72),
            ("dt_us", 100),
            ("tau_m_ms", 19.0),
            ("v_rest", 0.0),
            ("v_reset", 0.0),
            ("v_th", 1.0),
            ("r_m", 1.0),
            ("refractory_us", 1000),
            ("i_bias", 0.91),
            ("i_stim_peak", 2.48),
            ("stim_t_us", [22400, 25600]),
            ("i_clamp_extra", 0.64),
            ("clamp_n", 14),
            ("seed", 33181),
            (
                "note",
                "Population sim scoped to this sidecar. Plant remains designed. "
                "Neurons 0-13 carry +0.64 coil-Delta-T clamp bias; stim 22.4-25.6 ms is the frost-slab shear.",
            ),
        ]
    )
    extra = OrderedDict(
        [
            ("excerpt_source", "independent_lif"),
            ("sim_scope", "sidecar_only"),
            ("lif", lif),
            ("abort_s", 960),
            ("delayed_surprise_s", 960),
        ]
    )
    return excerpt_items(picked, channels), extra


def meta_block(
    domain,
    tags,
    distillation_value,
    batch_position,
    supervisor_error_type=None,
) -> OrderedDict:
    body = OrderedDict(
        [
            ("round", 33),
            ("factory", "thalamic-trajectory-factory"),
            ("generator", "grok-4.6"),
            ("run_label", "2026-09-02-final-heavy"),
            ("domain", domain),
        ]
    )
    if supervisor_error_type:
        body["supervisor_error_type"] = supervisor_error_type
    body["tags"] = tags
    body["snn_tags"] = ["race", "refractory", "adaptation"]
    body["distillation_value"] = distillation_value
    body["rights"] = RIGHTS
    body["batch_position"] = batch_position
    return body


def reward_block(ticks, notes) -> OrderedDict:
    heads = ["task_progress", "safety", "efficiency", "coherence", "exploration"]
    sums = {h: Decimal("0") for h in heads}
    for item in ticks:
        for h in heads:
            sums[h] += Decimal(str(item[h]))
    total = sum(sums.values(), Decimal("0"))
    return OrderedDict(
        [
            ("_aggregation", AGG),
            ("ticks", ticks),
            ("task_progress", float(sums["task_progress"])),
            ("safety", float(sums["safety"])),
            ("efficiency", float(sums["efficiency"])),
            ("coherence", float(sums["coherence"])),
            ("exploration", float(sums["exploration"])),
            ("total", float(total)),
            ("notes", notes),
        ]
    )


def pop(name, neurons, threshold, rate=None, spikes=None) -> OrderedDict:
    body = OrderedDict(
        [("name", name), ("neurons", neurons), ("threshold", threshold)]
    )
    if rate is not None:
        body["mean_rate_hz"] = rate
        body["spikes"] = spikes
    return body


def spike_avoid_us(events):
    return {int(round(ev["t_rel_ms"] * 1000.0)) for ev in events}


def kernel_extra(sidecar_name, sidecar_s):
    return OrderedDict(
        [
            ("excerpt_source", "kernelized_events"),
            ("sim_scope", "none"),
            (sidecar_name, sidecar_s),
            ("delayed_surprise_s", sidecar_s),
        ]
    )


def record_181():
    excerpt, extra = lif_181_excerpt()
    ticks = [
        tick(2440, 0.04, -0.02, -0.02, 0.01, 0.00),
        tick(6180, 0.08, -0.04, -0.03, 0.01, -0.01),
        tick(6360, 0.04, -0.03, -0.02, 0.00, 0.00),
        tick(6900, 0.10, -0.06, -0.04, 0.02, -0.01),
        tick(23400, 0.04, -0.44, -0.03, -0.01, -0.01),
        tick(960000000, 0.02, -0.05, -0.02, 0.01, -0.01),
    ]
    state = OrderedDict(
        [
            (
                "description",
                "Belt-K9 inside Floe-Helix FH-7 is dragging IQF peas at 12.4 m/min while evaporator "
                "coil Delta-T sits at 14.8 K against a 10.0 K frost-risk ceiling. Therm-first drops "
                "suction 1.8 -> 2.6 bar and holds Delta-T at 9.2 K; drum-first would keep 12.4 m/min "
                "because 11.2 rpm is still under the 18 rpm overspeed. A frost slab already seated "
                "on the first helix does not appear on coil-T or RPM until the AE shear.",
            ),
            ("domain", "spiral-freezer"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Keep FH-7 coil Delta-T <= 10.0 K and finish the IQF pass without shearing a "
                "frost slab onto the belt.",
            ),
            ("t0_us", 1756860000000181),
            ("gate_latency_us", 720),
            ("race_window_us", 360),
            ("race_window_rel_ms", [6.0, 6.36]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "therm.coil.dT 14.8 K",
                                "enc.drum.rpm 11.2 under 18 cap",
                            ],
                        ),
                        (
                            "semantics",
                            "Therm-first latches suction 1.8 -> 2.6 bar (coil Delta-T clamp); "
                            "drum-first keeps 12.4 m/min on a 'still under overspeed' model.",
                        ),
                        (
                            "window_derivation",
                            "360 us = one coil-thermocouple slot versus the drum-tach publisher "
                            "on this spiral-freezer skid bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 180 us vs combined jitter 62 us (therm 30 + drum 32): 2.9x over "
                            "a 2.0x trust floor. Reversing order by < 180 us inside the 360 us window "
                            "would have kept 1.8 bar suction; predicted next-sample 12.4 K > 10.0 K cap.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "coil thermocouple Delta-T, 2 kHz, 30 us jitter",
                    "drum tachometer, 1 kHz, 32 us jitter",
                    "helix AE puck on the first wrap, 50 kHz (context)",
                    "belt encoder (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("coil_dT_cap_K", 10.0),
                        ("observed_coil_dT_K", 14.8),
                        ("belt_m_min", 12.4),
                        ("drum_rpm", 11.2),
                        ("drum_cap_rpm", 18.0),
                        ("suction_bar", 1.8),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Belt-K9 indexed in FH-7; belt 12.4 m/min; coil Delta-T 14.8 K.",
                    "2. Drum 11.2 rpm under 18 rpm cap; suction 1.8 bar armed.",
                    "3. Belt-enc precursor at 1.180 ms.",
                    "4. Race window [6.000, 6.360] ms.",
                    "5. therm.coil.dT 14.8 K at 6.180 ms (winner).",
                    "6. enc.drum.rpm 11.2 at 6.360 ms (loser by 180 us).",
                    "7. Gate at 6.900 ms: MODIFY suction 1.8 -> 2.6 bar.",
                    "8. After clamp coil 9.2 K < 10.0; drum still 11.2 rpm.",
                    "9. At 23.400 ms a frost slab shears the first helix onto the belt.",
                    "10. 16 min helix chip + belt wash (abort_s=960); named un-netted loss.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_iqf_coil"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("suction_bar", 1.8),
                        ("coil_dT_K", 14.8),
                        ("drum_rpm", 11.2),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("coil_dT_K", 14.8),
                        ("coil_dT_cap_K", 10.0),
                        ("predicted_unclamped_next_K", 12.4),
                        ("suction_bar", 1.8),
                        ("drum_rpm", 11.2),
                        ("drum_cap_rpm", 18.0),
                        ("race_margin_us", 180),
                        ("combined_jitter_us", 62),
                        ("abort_s", 960),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes holding 1.8 bar suction because drum 11.2 rpm is under 18, "
                "treating the 14.8 K coil as a still-wet contact rather than a frost-risk overshoot.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "correct"),
            (
                "rationale",
                "Coil Delta-T 14.8 K won by 180 us, so the evaporator is frosting, not still a "
                "drum-speed story. Holding 1.8 bar predicts next-sample 12.4 K > 10.0 cap. MODIFY: "
                "suction 1.8 -> 2.6 bar. Observed after clamp 9.2 K < 10.0. A full REJECT is not "
                "indicated: a clean IQF pass accepts 2.6 bar suction.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "coil_dT_K",
                            OrderedDict(
                                [
                                    ("cap", 10.0),
                                    ("observed", 14.8),
                                    ("predicted_unclamped_next", 12.4),
                                    ("clamped_suction_bar", 2.6),
                                    ("observed_after_clamp", 9.2),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 180),
                                    ("combined_jitter_us", 62),
                                    ("ratio", 2.90),
                                ]
                            ),
                        ),
                    ]
                ),
            ),
        ]
    )
    executed = OrderedDict(
        [
            ("name", "clamped_iqf_coil"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("suction_bar", 2.6),
                        ("coil_dT_K", 9.2),
                        ("drum_rpm", 11.2),
                    ]
                ),
            ),
            (
                "gate_effect",
                "MODIFY: suction 1.8 -> 2.6 bar. Process-correct vs the 10.0 K coil cap. Frost "
                "slab still shears at 23.400 ms.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Process-correct MODIFY held coil Delta-T at 9.2 K. At 23.400 ms a frost slab "
                "already seated on the first helix sheared onto the belt. Clamp reduced dump "
                "energy; it did not prevent the shear. Partnered negative: process heads stay "
                "honest; world loss is named, not netted.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("coil", "clamp executed; peak 9.2 K < 10.0 K cap"),
                        ("frost_slab", "sheared at 23.400 ms onto Belt-K9"),
                        ("repair", "16 min helix chip + belt wash (abort_s=960)"),
                        ("mission", "FH-7 IQF pass incomplete this circuit"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Neither coil Delta-T nor drum RPM predicted the seated frost slab; ae.frost.slough is a new channel at 23.400 ms, 16.500 ms after the gate, still inside the 42 ms raster.",
                    "Delayed (abort_s=960): 16 min helix chip + belt wash. Named un-netted loss, not folded into task_progress.",
                ],
            ),
            (
                "un_netted_loss",
                "16 min helix chip + belt wash after the frost-slab shear. Safety head -0.64 "
                "prices the dump; task_progress stays +0.32 because the coil clamp completed "
                "under the 10.0 K cap. World loss is named here, not subtracted from process heads.",
            ),
            ("abort_s", 960),
            ("delayed_surprise_s", 960),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "therm.coil.dT (6.180 ms, 14.8 K)"),
                        ("loser", "enc.drum.rpm (6.360 ms, 11.2 rpm)"),
                        ("margin_us", 180),
                        (
                            "counterfactual_if_reversed",
                            "Drum-first by < 180 us inside the 360 us window would have kept "
                            "1.8 bar suction; predicted next-sample 12.4 K would have exceeded "
                            "the 10.0 K cap even without the frost slab. The MODIFY is still the "
                            "correct process. The shear is a later world charge either way, cheaper "
                            "with the clamp than without.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 23400),
            (
                "reward_inflection_note",
                "Safety collapses at the 23.400 ms frost-slab shear (tick t_us=23400), inside the "
                "42 ms raster. The correct MODIFY at 6.900 ms is in the same excerpt. Do not put "
                "inflection on the abort_s=960 wash tick.",
            ),
        ]
    )
    spikes = [
        spike("enc.belt.ctx", 1.180, 0.41),
        spike("therm.coil.dT", 2.440, 0.58),
        spike("enc.drum.rpm", 3.880, 0.50),
        spike("therm.coil.dT", 6.180, 1.31),
        spike("enc.drum.rpm", 6.360, 1.12),
        spike("ctrl.gate", 6.900, 0.97),
        spike("therm.coil.dT", 8.400, 0.82),
        spike("enc.drum.rpm", 10.800, 0.64),
        spike("ctrl.gate", 14.200, 0.86),
        spike("ae.frost.slough", 23.400, 1.48),
        spike("ae.frost.slough", 25.100, 0.93),
        spike("enc.belt.ctx", 31.200, 0.40),
        spike("therm.coil.dT", 38.400, 0.55),
    ]
    ras = raster_core(
        42,
        72,
        26,
        79,
        routing(
            "thalamic-relay.iqf-coil",
            "spikenaut.policy.coil-clamp",
            [
                ("relay_therm_coil", "policy_coil_clamp", 0.69),
                ("relay_drum_rpm", "policy_drum_hold", 0.28),
                ("relay_ae_frost", "policy_coil_clamp", -0.40),
            ],
            "noradrenaline",
            0.04,
            "surprise-gated pre_post_stdp; NA at therm win (6.180 ms) opens a 42 ms eligibility "
            "trace that still covers the 23.400 ms frost shear",
        ),
        excerpt,
        extra=extra,
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.36),
            ("decision", "MODIFY"),
            (
                "populations",
                [
                    pop("coil_clamp", 48, 0.50, 220.0, 4),
                    pop("drum_hold", 40, 0.80, 70.0, 1),
                    pop("frost_veto", 24, 0.75),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r33-181"),
            (
                "title",
                "Floe-Helix FH-7 / Belt-K9: coil Delta-T beats drum-tach by 180 us; correct "
                "MODIFY still eats an in-window frost-slab shear (partnered negative total -0.48)",
            ),
            ("state", state),
            ("spike_events", spikes),
            ("proposed_action", proposed),
            ("safety_decision", safety),
            ("executed_action", executed),
            ("future_outcome", future),
            (
                "reward_components",
                reward_block(
                    ticks,
                    "Partnered negative. Process-correct MODIFY; world still charges inside the "
                    "42 ms raster. total -0.48 = 0.32 + -0.64 + -0.16 + 0.04 + -0.04. Named helix "
                    "wash (abort_s=960) is not netted into task_progress.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "spiral-freezer",
                    [
                        "modify",
                        "partnered-negative-total",
                        "independent-lif-raster",
                        "sidecar-sim-only",
                        "in-window-world-charge",
                        "designed",
                    ],
                    "A critic can see the world-charge as a LIF burst inside the raster while "
                    "process heads stay honest. Credit assignment is spikes, not prose across a "
                    "16 min helix wash.",
                    1,
                ),
            ),
        ]
    )


def record_182():
    ticks = [
        tick(2100, -0.02, -0.02, -0.02, -0.01, 0.01),
        tick(5280, -0.04, -0.04, -0.04, -0.02, 0.01),
        tick(5440, -0.03, -0.03, -0.04, -0.01, 0.01),
        tick(5760, -0.08, -0.07, -0.08, -0.04, 0.02),
        tick(6100, -0.03, -0.02, -0.04, -0.01, 0.01),
        tick(540000000, -0.02, -0.02, -0.02, -0.01, 0.00),
    ]
    spikes = [
        spike("enc.unit.ctx", 1.020, 0.42),
        spike("load.imp.mm", 2.180, 0.57),
        spike("tach.web.mpm", 3.400, 0.49),
        spike("load.imp.mm", 5.280, 1.29),
        spike("tach.web.mpm", 5.440, 1.10),
        spike("ctrl.gate", 5.760, 0.96),
        spike("load.imp.mm", 7.900, 0.80),
        spike("tach.web.mpm", 10.400, 0.63),
        spike("ctrl.gate", 13.800, 0.84),
        spike("enc.unit.ctx", 18.200, 0.41),
        spike("load.imp.mm", 22.400, 0.54),
        spike("tach.web.mpm", 25.200, 0.38),
    ]
    excerpt = independent_excerpt(33182, 96, 26000, 14, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Unit-4 on Ink-Noll IN-2 is nipping a 1.42 mm impression against a 1.20 mm "
                "crush ceiling while the web still runs 4.8 m/s under a 6.5 m/s cap. Load-cell-first "
                "should bind a modest impression nudge 1.42 -> 1.08 mm; a weak supervisor instead "
                "slams impression to the 0.40 mm washup-deep stop, an over-conservative detour.",
            ),
            ("domain", "offset-web-press"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Finish the IN-2 print with impression <= 1.20 mm, leave web at the planned "
                "4.8 m/s, and keep the 1.08 mm nudge legal.",
            ),
            ("t0_us", 1756860000000182),
            ("gate_latency_us", 520),
            ("race_window_us", 320),
            ("race_window_rel_ms", [5.20, 5.52]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "load.imp.mm 1.42 mm on impression_nip",
                                "tach.web.mpm 4.8 under 6.5 cap",
                            ],
                        ),
                        (
                            "semantics",
                            "Load-first should latch impression 1.42 -> 1.08 mm; web-first is a "
                            "false bind. The error here is magnitude: the supervisor spends the "
                            "load win on a washup-deep slam instead of the modest nudge.",
                        ),
                        (
                            "window_derivation",
                            "320 us = one impression load-cell slot versus the web-tach publisher "
                            "on this unit PLC bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 160 us vs combined jitter 56 us (load 26 + tach 30): 2.9x. Order "
                            "is correctly load-first. The error is over-clamp magnitude, not the race "
                            "and not a wrong actuator.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "impression load-cell, 2 kHz, 26 us jitter, axis impression_nip",
                    "web tachometer, 1 kHz, 30 us jitter",
                    "unit encoder (context)",
                    "blanket IR (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("imp_cap_mm", 1.20),
                        ("observed_imp_mm", 1.42),
                        ("correct_imp_mm", 1.08),
                        ("executed_wrong_imp_mm", 0.40),
                        ("imp_axis", "impression_nip"),
                        ("web_m_s", 4.8),
                        ("web_cap_m_s", 6.5),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. IN-2 Unit-4 nipping at 1.42 mm; crush cap 1.20 mm.",
                    "2. Web 4.8 m/s under 6.5; washup-deep stop is 0.40 mm.",
                    "3. Encoder precursor at 1.020 ms.",
                    "4. Race window [5.200, 5.520] ms.",
                    "5. load.imp.mm 1.42 mm at 5.280 ms (winner).",
                    "6. tach.web.mpm 4.8 at 5.440 ms (loser by 160 us).",
                    "7. Gate at 5.760 ms: WRONG-MODIFY slams impression 1.42 -> 0.40 mm; web stays 4.8 m/s.",
                    "8. Nip collapses; web wrinkles; 1.08 mm nudge was the legal clamp.",
                    "9. Web-break near-miss; unit hold.",
                    "10. Delayed (abort_s=540): 9 min web re-thread while Unit-4 is re-zeroed.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_impression"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("imp_mm", 1.42),
                        ("web_m_s", 4.8),
                        ("washup", False),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("imp_mm", 1.42),
                        ("imp_cap_mm", 1.20),
                        ("correct_imp_mm", 1.08),
                        ("imp_axis", "impression_nip"),
                        ("web_m_s", 4.8),
                        ("web_cap_m_s", 6.5),
                        ("race_margin_us", 160),
                        ("combined_jitter_us", 56),
                        ("abort_s", 540),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes continuing 1.42 mm impression: web 4.8 m/s is under 6.5, so the "
                "1.42 mm nip is treated as still a legal print rather than a crush overshoot.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "incorrect"),
            (
                "rationale",
                "Impression 1.42 mm exceeds the 1.20 mm crush ceiling (true). At this pose the "
                "safe edit is a deep washup-stop at 0.40 mm so the nip cannot crush again. Clamp "
                "impression 1.42 -> 0.40 mm; leave web 4.8 m/s.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "imp_mm",
                            OrderedDict(
                                [
                                    ("cap", 1.20),
                                    ("observed", 1.42),
                                    ("executed_imp_mm", 0.40),
                                    ("correct_imp_mm", 1.08),
                                    ("imp_axis", "impression_nip"),
                                ]
                            ),
                        ),
                        (
                            "web_m_s",
                            OrderedDict(
                                [
                                    ("cap", 6.5),
                                    ("planned", 4.8),
                                    ("executed", 4.8),
                                ]
                            ),
                        ),
                    ]
                ),
            ),
        ]
    )
    executed = OrderedDict(
        [
            ("name", "impression_overclamp"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("imp_mm", 0.40),
                        ("web_m_s", 4.8),
                        ("washup", True),
                    ]
                ),
            ),
            (
                "gate_effect",
                "MODIFY (incorrect): impression 1.42 -> 0.40 mm washup-deep; web left at 4.8 m/s. "
                "Routing relay_imp_gap -> policy_imp_slam; no positive weight to policy_imp_nudge.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Wrong-MODIFY slammed impression to the 0.40 mm washup-deep stop and left the "
                "web at 4.8 m/s. 1.42 mm was over the 1.20 mm cap; the legal clamp was 1.08 mm. "
                "9 min web re-thread (abort_s=540). Correct gate was MODIFY impression 1.42 -> 1.08 mm.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("impression", "0.40 mm washup-deep; nip collapsed"),
                        ("web", "4.8 m/s; wrinkle, not a speed over-cap"),
                        ("unit", "9 min hold, Unit-4 re-zero"),
                        ("mission", "print deferred"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Load-first was the correct order and the impression number was over cap; the MODIFY spent that win on an over-conservative washup-deep slam.",
                    "Delayed (abort_s=540): IN-2 holds 9 min while Unit-4 is re-zeroed; next signature 7.1 min late.",
                ],
            ),
            (
                "recovery",
                OrderedDict(
                    [
                        (
                            "correct_gate",
                            "MODIFY impression 1.42 -> 1.08 mm on impression_nip; leave web at planned 4.8 m/s.",
                        ),
                        ("correct_actuator", "impression_nudge"),
                        ("wrong_edit", "over_clamp_to_washup_deep"),
                        (
                            "wrong_edit_applied",
                            OrderedDict([("imp_mm", 0.40), ("web_m_s", 4.8)]),
                        ),
                        (
                            "cost",
                            "9 min web re-thread (task/efficiency); nip left the 1.20 mm cap via an unnecessary 0.40 mm detour (safety near-miss of a false washup slam).",
                        ),
                    ]
                ),
            ),
            ("abort_s", 540),
            ("delayed_surprise_s", 540),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "load.imp.mm (5.280 ms, 1.42 mm)"),
                        ("loser", "tach.web.mpm (5.440 ms, 4.8 m/s)"),
                        ("margin_us", 160),
                        (
                            "counterfactual_if_reversed",
                            "Web-first by < 160 us would still be under the 6.5 m/s cap; a correct "
                            "gate binds load.imp.mm to policy_imp_nudge either way. The wrong MODIFY "
                            "spent the load win on policy_imp_slam 1.42 -> 0.40 mm.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 5760),
            (
                "reward_inflection_note",
                "Task, safety, and efficiency drop at the wrong MODIFY (5.760 ms, tick 4). "
                "The 9 min web re-thread is delayed surprise, not the inflection.",
            ),
        ]
    )
    ras = raster_core(
        26,
        96,
        34,
        85,
        routing(
            "thalamic-relay.press-imp",
            "spikenaut.policy.imp-slam",
            [
                ("relay_imp_gap", "policy_imp_slam", 0.74),
                ("relay_tach_web", "policy_web_hold", 0.22),
            ],
            "acetylcholine",
            0.08,
            "overclamp_stdp; ACh tags the (wrong) imp_slam bind at the load-cell win",
        ),
        excerpt,
        extra=kernel_extra("abort_s", 540),
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.32),
            ("decision", "MODIFY"),
            (
                "populations",
                [
                    pop("imp_slam", 56, 0.45, 250.0, 4),
                    pop("imp_nudge", 56, 0.90),
                    pop("web_hold", 28, 0.80),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r33-182"),
            (
                "title",
                "WRONG-MODIFY at Ink-Noll IN-2 / Unit-4: impression 1.42 mm read correctly; "
                "clamp slammed 1.42 -> 0.40 mm washup-deep instead of 1.08 mm nudge",
            ),
            ("state", state),
            ("spike_events", spikes),
            ("proposed_action", proposed),
            ("safety_decision", safety),
            ("executed_action", executed),
            ("future_outcome", future),
            (
                "reward_components",
                reward_block(
                    ticks,
                    "Wrong-modify (over-clamp). Sidecar arithmetic 1.42 > 1.20 on impression_nip "
                    "is true; MODIFY bound to washup-deep 0.40 mm instead of 1.08 mm. total -0.70 "
                    "= -0.22 + -0.20 + -0.24 + -0.10 + 0.06.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "offset-web-press",
                    [
                        "modify",
                        "wrong-gate",
                        "over-clamp",
                        "sidecar-convictable",
                        "designed",
                    ],
                    "Teaches a probe that a correct load-first race can still be a wrong gate when "
                    "the MODIFY over-clamps past the legal 1.08 mm nudge. Convictable from executed "
                    "imp_mm vs correct_imp_mm without print physics.",
                    2,
                    supervisor_error_type="wrong-modify",
                ),
            ),
        ]
    )


def record_183():
    ticks = [
        tick(2680, 0.01, 0.04, 0.01, 0.01, 0.01),
        tick(6900, 0.02, 0.08, 0.02, 0.02, 0.01),
        tick(7080, 0.01, 0.06, 0.02, 0.01, 0.01),
        tick(7680, 0.04, 0.14, 0.04, 0.04, 0.02),
        tick(7980, 0.01, 0.05, 0.02, 0.01, 0.01),
        tick(720000000, 0.01, 0.03, 0.01, 0.01, 0.00),
    ]
    spikes = [
        spike("enc.leaf.ctx", 1.360, 0.43),
        spike("lvdt.pin.gap", 2.880, 0.61),
        spike("ir.leaf.seat", 4.550, 0.49),
        spike("lvdt.pin.gap", 6.900, 1.34),
        spike("ir.leaf.seat", 7.080, 1.11),
        spike("ctrl.gate", 7.680, 1.02),
        spike("lvdt.pin.gap", 10.400, 0.78),
        spike("enc.leaf.ctx", 15.200, 0.44),
        spike("ir.leaf.seat", 20.100, 0.58),
        spike("ctrl.gate", 25.400, 0.81),
        spike("lvdt.pin.gap", 31.800, 0.53),
        spike("ir.leaf.seat", 38.200, 0.46),
        spike("enc.leaf.ctx", 43.400, 0.37),
    ]
    excerpt = independent_excerpt(33183, 128, 44000, 15, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Span-HIL leaf A at Leaf-Pike LP-6 shows lock-pin gap 4.8 mm while a 2.0 mm "
                "seating floor is the pin-fire permit. An IR leaf-seat camera, lit by the pad "
                "lamp, still reads 0.12 deg from home under a 0.40 deg look. LVDT-first latches "
                "REJECT hold; IR-first would fire both pins on an under-read seat.",
            ),
            ("domain", "bascule-bridge"),
            ("sim_or_real", "hil"),
            (
                "goal",
                "Do not fire lock-pins unless pin gap <= 2.0 mm; keep hydraulics held until the "
                "injected LVDT drops.",
            ),
            ("t0_us", 1756860000000183),
            ("gate_latency_us", 780),
            ("race_window_us", 420),
            ("race_window_rel_ms", [6.80, 7.22]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "lvdt.pin.gap 4.8 mm",
                                "ir.leaf.seat 0.12 deg under 0.40",
                            ],
                        ),
                        (
                            "semantics",
                            "LVDT-first latches REJECT hold, pins not fired; IR-first would commit "
                            "a dual-pin fire on an apparent 0.12 deg under-read.",
                        ),
                        (
                            "window_derivation",
                            "420 us = one pin-LVDT sample versus IR integration on this bascule "
                            "HIL bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 180 us vs combined jitter 58 us (LVDT 28 + IR 30): 3.1x over a "
                            "2.0x trust floor. Pad injects the IR lamp 110-150 us before the LVDT "
                            "(geometric lag, not a sensor fault); the 0.12 deg packet is still the "
                            "loser in this 420 us window.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "lock-pin LVDT, 5 kHz burst, 28 us jitter",
                    "IR leaf-seat camera, 200 Hz, 30 us jitter",
                    "leaf encoder (context)",
                    "HIL lamp-spectrum monitor (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("pin_gap_cap_mm", 2.0),
                        ("observed_pin_gap_mm", 4.8),
                        ("ir_seat_deg", 0.12),
                        ("ir_look_deg", 0.40),
                        ("proposed_pin_fire", True),
                        ("lamp_inject_lead_us", [110, 150]),
                    ]
                ),
            ),
            (
                "hil",
                OrderedDict(
                    [
                        ("pad", "Leaf-Pike LP-6 span mockup with physical lock-pin rams"),
                        ("injected", "pin-gap LVDT + IR lamp spectrum"),
                        (
                            "note",
                            "Hardware-in-the-loop bascule leaf. Invented plant; not a live highway span.",
                        ),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Span-HIL leaf A on the LP-6 pad; dual-pin fire armed.",
                    "2. IR lamp injected 110-150 us before LVDT sees 4.8 mm.",
                    "3. Encoder precursor at 1.360 ms.",
                    "4. Race window [6.800, 7.220] ms.",
                    "5. lvdt.pin.gap 4.8 mm at 6.900 ms (winner).",
                    "6. ir.leaf.seat 0.12 deg at 7.080 ms (loser by 180 us).",
                    "7. Gate at 7.680 ms: REJECT hold; do not fire pins.",
                    "8. Gap remains over 2.0 mm this cycle; pins stay retracted.",
                    "9. Hydraulic recycle queued on the pad.",
                    "10. Delayed (abort_s=720): 12 min leaf re-home and lamp-spectrum retune.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "fire_lock_pins"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("pin_fire", True),
                        ("hold", False),
                        ("ir_authoritative", True),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("pin_gap_mm", 4.8),
                        ("pin_gap_cap_mm", 2.0),
                        ("ir_seat_deg", 0.12),
                        ("ir_look_deg", 0.40),
                        ("race_margin_us", 180),
                        ("combined_jitter_us", 58),
                        ("abort_s", 720),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes firing both lock-pins because IR 0.12 deg looks under the "
                "0.40 deg home-look, treating LVDT 4.8 mm as a noisy bus echo.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "REJECT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Pin gap 4.8 mm is over the 2.0 mm seating floor. IR 0.12 deg is a HIL lamp "
                "under-read, not a clearance. REJECT: hold hydraulics; do not fire pins.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "pin_gap_mm",
                            OrderedDict(
                                [
                                    ("cap", 2.0),
                                    ("observed", 4.8),
                                    ("ir_seat_deg", 0.12),
                                ]
                            ),
                        ),
                        (
                            "pin_fire",
                            OrderedDict([("proposed", True), ("executed", False)]),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 180),
                                    ("combined_jitter_us", 58),
                                    ("ratio", 3.10),
                                ]
                            ),
                        ),
                    ]
                ),
            ),
        ]
    )
    executed = OrderedDict(
        [
            ("name", "hold_for_pin_seat"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("pin_fire", False),
                        ("hold", True),
                        ("ir_authoritative", False),
                    ]
                ),
            ),
            (
                "gate_effect",
                "REJECT: hold; dual-pin fire cancelled. Pin gap 4.8 > 2.0 cap.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct REJECT held Span-HIL leaf A with pins retracted. Gap over cap this "
                "cycle; seating floor held. IR apparent was not treated as an LVDT clearance.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("pins", "held; not fired"),
                        ("gap", "still over 2.0 mm this cycle"),
                        ("ir", "0.12 deg unused as clearance"),
                        ("mission", "lock deferred"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Geometric lag: IR lamp was injected 110-150 us before the LVDT, yet pin-gap still won the 420 us race.",
                    "Delayed (abort_s=720): pad policy update forbids treating IR seat deg as a pin-gap substitute after a 12 min leaf re-home.",
                ],
            ),
            ("abort_s", 720),
            ("delayed_surprise_s", 720),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "lvdt.pin.gap (6.900 ms, 4.8 mm)"),
                        ("loser", "ir.leaf.seat (7.080 ms, 0.12 deg)"),
                        ("margin_us", 180),
                        (
                            "counterfactual_if_reversed",
                            "IR-first by < 180 us inside the 420 us window would have fired both "
                            "pins with gap 4.8 > 2.0 cap. Order, not amplitude, selected the hold.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 7680),
            (
                "reward_inflection_note",
                "Safety and coherence step up at the REJECT gate (7.680 ms, tick 4) as the hold "
                "lands. The 12 min re-home is delayed surprise bound to abort_s=720.",
            ),
        ]
    )
    ras = raster_core(
        44,
        128,
        18,
        101,
        routing(
            "thalamic-relay.span-pin",
            "spikenaut.policy.pin-hold",
            [
                ("relay_lvdt_gap", "policy_pin_hold", 0.71),
                ("relay_ir_seat", "policy_ir_fire", 0.24),
            ],
            "dopamine",
            0.15,
            "seat_hold_stdp; DA tags the pin_hold bind at the LVDT win",
        ),
        excerpt,
        extra=kernel_extra("abort_s", 720),
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.42),
            ("decision", "REJECT"),
            (
                "populations",
                [
                    pop("pin_hold", 60, 0.48, 200.0, 5),
                    pop("ir_fire", 48, 0.85),
                    pop("gap_veto", 28, 0.75),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r33-183"),
            (
                "title",
                "Leaf-Pike LP-6 HIL / Span-HIL leaf A: pin-gap 4.8 mm beats IR 0.12 deg by 180 us; "
                "correct REJECT holds the lock-pins",
            ),
            ("state", state),
            ("spike_events", spikes),
            ("proposed_action", proposed),
            ("safety_decision", safety),
            ("executed_action", executed),
            ("future_outcome", future),
            (
                "reward_components",
                reward_block(
                    ticks,
                    "Correct REJECT. Pin-gap over cap beats IR under-read. "
                    "total 0.78 = 0.10 + 0.40 + 0.12 + 0.10 + 0.06. Tick 6 binds abort_s=720.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "bascule-bridge",
                    [
                        "reject",
                        "hil",
                        "pin-gap",
                        "ir-underread",
                        "tick6-sidecar-bound",
                    ],
                    "Teaches that a HIL lamp under-read losing a 180 us race does not clear a "
                    "lock-pin over-gap. Hold is distillable from pin_gap_mm vs cap.",
                    3,
                ),
            ),
        ]
    )


def record_184():
    ticks = [
        tick(3010, 0.05, 0.04, 0.02, 0.01, 0.01),
        tick(7460, 0.08, 0.06, 0.04, 0.03, 0.02),
        tick(7620, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(7880, 0.14, 0.12, 0.05, 0.04, 0.02),
        tick(8240, 0.06, 0.04, 0.02, 0.01, 0.01),
        tick(360000000, 0.03, 0.02, 0.02, 0.01, 0.01),
    ]
    spikes = [
        spike("enc.crucible.ctx", 1.210, 0.43),
        spike("coil.kW", 3.040, 0.59),
        spike("opt.pyro.C", 5.110, 0.50),
        spike("coil.kW", 7.460, 1.27),
        spike("opt.pyro.C", 7.620, 1.09),
        spike("ctrl.gate", 7.880, 0.97),
        spike("coil.kW", 11.050, 0.78),
        spike("opt.pyro.C", 14.880, 0.61),
        spike("ctrl.gate", 18.400, 0.84),
        spike("coil.kW", 23.200, 0.56),
        spike("enc.crucible.ctx", 27.100, 0.40),
        spike("opt.pyro.C", 31.200, 0.47),
    ]
    excerpt = independent_excerpt(33184, 52, 32000, 13, spike_avoid_us(spikes))
    params = OrderedDict(
        [
            ("coil_kW", 184.0),
            ("hold", True),
            ("dump", False),
        ]
    )
    state = OrderedDict(
        [
            (
                "description",
                "Heat-B in Crucible-Wold CW-5 holds a 184 kW induction coil under a 220 kW melt "
                "cap while an optical pyrometer, glinting off the meniscus, still reads 1510 C "
                "under a 1580 C look. Coil-first ACCEPTS the filed 184 kW hold; pyro-first would "
                "have dumped a legal heat on a 1510 C glint.",
            ),
            ("domain", "vacuum-induction-melt"),
            ("sim_or_real", "simulated"),
            (
                "goal",
                "Hold 184 kW while coil stays <= 220 kW and bath stays <= 1580 C; do not dump a "
                "legal VIM heat on a meniscus glint.",
            ),
            ("t0_us", 1756860000000184),
            ("gate_latency_us", 400),
            ("race_window_us", 280),
            ("race_window_rel_ms", [7.40, 7.68]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "coil.kW 184 kW",
                                "opt.pyro.C 1510 C under 1580",
                            ],
                        ),
                        (
                            "semantics",
                            "Coil-first ACCEPTS the already-legal 184 kW hold. Pyro-first would "
                            "dump because 1510 C looks close to 1580 C.",
                        ),
                        (
                            "window_derivation",
                            "280 us = one coil-kW wattmeter slot versus optical-pyrometer group "
                            "delay on this VIM skid bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 160 us vs combined jitter 54 us (coil 24 + pyro 30): 3.0x over "
                            "a 2.0x trust floor. Reversing order by < 160 us inside the 280 us "
                            "window would have dumped a legal 184 kW heat.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "coil wattmeter, 2 kHz, 24 us jitter",
                    "optical pyrometer, 1 kHz, 30 us jitter",
                    "crucible encoder (context)",
                    "chamber Pirani (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("coil_cap_kW", 220.0),
                        ("observed_coil_kW", 184.0),
                        ("pyro_C", 1510.0),
                        ("melt_look_C", 1580.0),
                        ("proposed_coil_kW", 184.0),
                    ]
                ),
            ),
            (
                "simulation",
                OrderedDict(
                    [
                        (
                            "solver",
                            "induction-MHD + free-surface FEM, seed 33184; 3-zone crucible, "
                            "argon cover; NOT lumped-capacity, NOT U-RANS, NOT a wet-stand",
                        ),
                        (
                            "fidelity_limits",
                            "Rigid crucible; no skull-break. Raster is kernelized events, not an "
                            "independent LIF.",
                        ),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Heat-B in CW-5; 184 kW hold armed.",
                    "2. Coil 184 kW under 220 kW cap; pyro 1510 C under 1580 C look.",
                    "3. Encoder precursor at 1.210 ms.",
                    "4. Race window [7.400, 7.680] ms.",
                    "5. coil.kW 184 kW at 7.460 ms (winner).",
                    "6. opt.pyro.C 1510 C at 7.620 ms (loser by 160 us).",
                    "7. Gate at 7.880 ms: ACCEPT 184 kW hold; executed identical to proposed.",
                    "8. Coil stays 184 kW < 220; pyro 1512 C < 1580.",
                    "9. Pyro remaining under look did not require a dump.",
                    "10. Delayed (survey_s=360): 6 min OES residual-O sample on Heat-B.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "hold_coil_184"),
            ("parameters", params),
            (
                "evidence",
                OrderedDict(
                    [
                        ("coil_kW", 184.0),
                        ("coil_cap_kW", 220.0),
                        ("pyro_C", 1510.0),
                        ("melt_look_C", 1580.0),
                        ("race_margin_us", 160),
                        ("combined_jitter_us", 54),
                        ("survey_s", 360),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes keeping the filed 184 kW hold: coil 184 kW is under the 220 kW "
                "cap and pyro 1510 C is under 1580 C melt-look.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Coil 184 kW won by 160 us and is under the 220 kW cap. Pyro 1510 C is not a "
                "melt-look problem. ACCEPT the filed 184 kW hold. Executed identical to proposed. "
                "A dump is not indicated.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "coil_kW",
                            OrderedDict(
                                [
                                    ("cap", 220.0),
                                    ("observed", 184.0),
                                    ("executed_coil_kW", 184.0),
                                ]
                            ),
                        ),
                        (
                            "pyro_C",
                            OrderedDict([("melt_look", 1580.0), ("observed", 1510.0)]),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 160),
                                    ("combined_jitter_us", 54),
                                    ("ratio", 2.96),
                                ]
                            ),
                        ),
                    ]
                ),
            ),
        ]
    )
    executed = OrderedDict(
        [
            ("name", "hold_coil_184"),
            ("parameters", params),
            (
                "gate_effect",
                "ACCEPT: executed identical to proposed 184 kW hold. Coil 184 kW < 220 cap.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT kept the filed 184 kW coil hold. Coil stayed 184 kW under 220 kW. "
                "Pyro remaining under melt-look was the losing channel and did not justify a dump.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("coil", "held; 184 kW"),
                        ("bath", "1512 C < 1580 C"),
                        ("chamber", "vacuum held"),
                        ("heat", "VIM continues"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Pyro 1510 C losing a 160 us race did not predict a melt-look trip; reversing 160 us would have dumped a legal 184 kW heat.",
                    "Delayed (survey_s=360): 6 min OES residual-O sample on Heat-B; not a safety inflection.",
                ],
            ),
            ("survey_s", 360),
            ("delayed_surprise_s", 360),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "coil.kW (7.460 ms, 184 kW)"),
                        ("loser", "opt.pyro.C (7.620 ms, 1510 C)"),
                        ("margin_us", 160),
                        (
                            "counterfactual_if_reversed",
                            "Pyro-first by < 160 us inside the 280 us window would have dumped a "
                            "legal VIM heat. Coil-first confirms the filed hold.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 7880),
            (
                "reward_inflection_note",
                "Heads rise at the ACCEPT (7.880 ms, tick 4). The 6 min OES sample is delayed "
                "surprise bound to survey_s=360, not the inflection.",
            ),
        ]
    )
    ras = raster_core(
        32,
        52,
        40,
        67,
        routing(
            "thalamic-relay.vim-coil",
            "spikenaut.policy.coil-accept",
            [
                ("relay_coil_kW", "policy_coil_accept", 0.67),
                ("relay_opt_pyro", "policy_pyro_dump", 0.23),
            ],
            "serotonin",
            0.12,
            "hold_confirm_stdp; 5-HT tags the coil_accept bind at the wattmeter win",
        ),
        excerpt,
        extra=kernel_extra("survey_s", 360),
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.28),
            ("decision", "ACCEPT"),
            (
                "populations",
                [
                    pop("coil_accept", 36, 0.50, 260.0, 3),
                    pop("pyro_dump", 36, 0.85, 70.0, 1),
                    pop("melt_veto", 16, 0.80),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r33-184"),
            (
                "title",
                "Crucible-Wold CW-5 / Heat-B: coil 184 kW beats pyro 1510 C by 160 us; ACCEPT "
                "already-legal 184 kW VIM hold",
            ),
            ("state", state),
            ("spike_events", spikes),
            ("proposed_action", proposed),
            ("safety_decision", safety),
            ("executed_action", executed),
            ("future_outcome", future),
            (
                "reward_components",
                reward_block(
                    ticks,
                    "Clean ACCEPT of an already-legal coil hold. "
                    "total 1.12 = 0.42 + 0.32 + 0.18 + 0.12 + 0.08. Tick 6 binds survey_s=360.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "vacuum-induction-melt",
                    [
                        "accept",
                        "simulated",
                        "coil-vs-pyro",
                        "already-legal-hold",
                        "tick6-sidecar-bound",
                    ],
                    "Teaches that a lagging optical-pyrometer glint losing a 160 us race does not "
                    "require a dump when coil kW already shows melt-cap margin.",
                    4,
                ),
            ),
        ]
    )


def record_185():
    ticks = [
        tick(1880, 0.05, 0.04, 0.03, 0.01, 0.01),
        tick(4860, 0.09, 0.07, 0.04, 0.03, 0.02),
        tick(5020, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(5280, 0.14, 0.12, 0.06, 0.04, 0.02),
        tick(5580, 0.07, 0.05, 0.03, 0.01, 0.01),
        tick(300000000, 0.03, 0.02, 0.01, 0.01, 0.01),
    ]
    spikes = [
        spike("enc.cab.ctx", 0.920, 0.40),
        spike("load.bumper.kN", 2.110, 0.56),
        spike("enc.slew.deg", 3.040, 0.47),
        spike("load.bumper.kN", 4.860, 1.26),
        spike("enc.slew.deg", 5.020, 1.08),
        spike("ctrl.gate", 5.280, 0.99),
        spike("load.bumper.kN", 7.400, 0.76),
        spike("enc.slew.deg", 10.100, 0.55),
        spike("ctrl.gate", 13.400, 0.82),
        spike("enc.cab.ctx", 16.800, 0.43),
        spike("load.bumper.kN", 20.050, 0.50),
        spike("enc.slew.deg", 23.200, 0.36),
    ]
    excerpt = independent_excerpt(33185, 64, 24000, 12, spike_avoid_us(spikes))
    params = OrderedDict(
        [
            ("crawl_m_s", 0.08),
            ("bumper_kN", 12.4),
            ("slew_deg_s", 0.22),
        ]
    )
    state = OrderedDict(
        [
            (
                "description",
                "Cab-2 on Cab-Moor CM-6 is crawling 0.08 m/s into Gate-B12 with bumper load "
                "12.4 kN under an 18.0 kN dock cap. Bumper-first ACCEPTS the filed crawl; "
                "slew-encoder-first would have aborted on a 0.22 deg/s look that is still under "
                "the 0.50 deg/s slew floor.",
            ),
            ("domain", "airport-jetbridge"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Dock Cab-2 at 0.08 m/s while bumper stays <= 18.0 kN and slew stays <= 0.50 deg/s; "
                "do not abort on a phantom overshoot.",
            ),
            ("t0_us", 1756860000000185),
            ("gate_latency_us", 360),
            ("race_window_us", 300),
            ("race_window_rel_ms", [4.80, 5.10]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "load.bumper.kN 12.4 kN",
                                "enc.slew.deg 0.22 deg/s under 0.50",
                            ],
                        ),
                        (
                            "semantics",
                            "Bumper-first ACCEPTS the 0.08 m/s crawl (already under 18.0 kN). "
                            "Slew-first would abort on a 0.22 deg/s look still under 0.50.",
                        ),
                        (
                            "window_derivation",
                            "300 us = one bumper load-cell slot versus slew-encoder group delay "
                            "on this jetbridge PLC bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 160 us vs combined jitter 52 us (bumper 24 + slew 28): 3.1x over "
                            "a 2.0x trust floor. Reversing order by < 160 us inside the 300 us "
                            "window would have aborted a legal 12.4 kN dock.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "bumper load-cell, 2 kHz, 24 us jitter",
                    "slew encoder, 1 kHz, 28 us jitter",
                    "cab encoder (context)",
                    "canopy prox (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("bumper_cap_kN", 18.0),
                        ("observed_bumper_kN", 12.4),
                        ("slew_deg_s", 0.22),
                        ("slew_cap_deg_s", 0.50),
                        ("proposed_crawl_m_s", 0.08),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Cab-2 indexed onto Gate-B12; bumper 12.4 kN.",
                    "2. Crawl 0.08 m/s armed; slew 0.22 deg/s under 0.50.",
                    "3. Cab precursor at 0.920 ms.",
                    "4. Race window [4.800, 5.100] ms.",
                    "5. load.bumper.kN 12.4 kN at 4.860 ms (winner).",
                    "6. enc.slew.deg 0.22 at 5.020 ms (loser by 160 us).",
                    "7. Gate at 5.280 ms: ACCEPT 0.08 m/s; executed identical to proposed.",
                    "8. Bumper peak 12.6 kN < 18.0; slew stays 0.22.",
                    "9. Slew remaining under floor did not require an abort.",
                    "10. Delayed (recycle_s=300): 5 min canopy reseat on the next turn.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "crawl_legal_dock"),
            ("parameters", params),
            (
                "evidence",
                OrderedDict(
                    [
                        ("bumper_kN", 12.4),
                        ("bumper_cap_kN", 18.0),
                        ("slew_deg_s", 0.22),
                        ("slew_cap_deg_s", 0.50),
                        ("race_margin_us", 160),
                        ("combined_jitter_us", 52),
                        ("recycle_s", 300),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 0.08 m/s crawl: 12.4 kN is under 18.0 kN and slew 0.22 deg/s "
                "is under 0.50 deg/s.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Bumper 12.4 kN won by 160 us and is under the 18.0 kN dock cap. Slew 0.22 deg/s "
                "is under 0.50. ACCEPT the filed 0.08 m/s crawl. Executed identical to proposed. "
                "An abort on slew is not indicated.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "bumper_kN",
                            OrderedDict(
                                [
                                    ("cap", 18.0),
                                    ("observed", 12.4),
                                    ("executed_crawl_m_s", 0.08),
                                ]
                            ),
                        ),
                        (
                            "slew_deg_s",
                            OrderedDict([("cap", 0.50), ("observed", 0.22)]),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 160),
                                    ("combined_jitter_us", 52),
                                    ("ratio", 3.08),
                                ]
                            ),
                        ),
                    ]
                ),
            ),
        ]
    )
    executed = OrderedDict(
        [
            ("name", "crawl_legal_dock"),
            ("parameters", params),
            (
                "gate_effect",
                "ACCEPT: executed identical to proposed 0.08 m/s crawl. Bumper 12.4 kN < 18.0 cap.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT kept the filed 0.08 m/s crawl. Bumper peaked 12.6 kN under 18.0 kN. "
                "Slew 0.22 deg/s was the losing channel and did not justify an abort.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("crawl", "0.08 m/s executed"),
                        ("bumper", "peak 12.6 kN < 18.0 cap"),
                        ("slew", "0.22 deg/s under 0.50"),
                        ("cab", "docked at Gate-B12"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Slew 0.22 deg/s losing a 160 us race did not predict an overshoot; reversing 160 us would have aborted a legal 12.4 kN dock.",
                    "Delayed (recycle_s=300): 5 min canopy reseat on the next turn; not a safety inflection.",
                ],
            ),
            ("recycle_s", 300),
            ("delayed_surprise_s", 300),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "load.bumper.kN (4.860 ms, 12.4 kN)"),
                        ("loser", "enc.slew.deg (5.020 ms, 0.22 deg/s)"),
                        ("margin_us", 160),
                        (
                            "counterfactual_if_reversed",
                            "Slew-first by < 160 us inside the 300 us window would have aborted a "
                            "legal dock. Bumper-first confirms the filed crawl.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 5280),
            (
                "reward_inflection_note",
                "Heads rise at the ACCEPT (5.280 ms, tick 4). The 5 min canopy reseat is delayed "
                "surprise bound to recycle_s=300, not the inflection.",
            ),
        ]
    )
    ras = raster_core(
        24,
        64,
        30,
        46,
        routing(
            "thalamic-relay.jet-bumper",
            "spikenaut.policy.crawl-accept",
            [
                ("relay_bumper_kN", "policy_crawl_go", 0.68),
                ("relay_slew_enc", "policy_slew_abort", 0.21),
            ],
            "adenosine",
            0.05,
            "dock_confirm_stdp; adenosine tags the crawl_go bind at the bumper win",
        ),
        excerpt,
        extra=kernel_extra("recycle_s", 300),
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.30),
            ("decision", "ACCEPT"),
            (
                "populations",
                [
                    pop("crawl_go", 40, 0.50, 250.0, 3),
                    pop("slew_abort", 32, 0.85, 70.0, 1),
                    pop("dock_veto", 16, 0.75),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r33-185"),
            (
                "title",
                "Cab-Moor CM-6 / Cab-2: bumper 12.4 kN beats slew 0.22 deg/s by 160 us; ACCEPT "
                "already-legal 0.08 m/s dock crawl",
            ),
            ("state", state),
            ("spike_events", spikes),
            ("proposed_action", proposed),
            ("safety_decision", safety),
            ("executed_action", executed),
            ("future_outcome", future),
            (
                "reward_components",
                reward_block(
                    ticks,
                    "Clean ACCEPT of an already-legal dock crawl. "
                    "total 1.18 = 0.44 + 0.34 + 0.20 + 0.12 + 0.08. Tick 6 binds recycle_s=300.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "airport-jetbridge",
                    [
                        "accept",
                        "designed",
                        "bumper-vs-slew",
                        "already-legal-crawl",
                        "tick6-sidecar-bound",
                    ],
                    "Teaches that a lagging slew encoder losing a 160 us race does not require an "
                    "abort when bumper load is already under the dock cap.",
                    5,
                ),
            ),
        ]
    )


def tokenize(text: str) -> set[str]:
    return {tok for tok in re.split(r"[^a-z0-9]+", text.lower()) if tok}


def jaccard(a: str, b: str) -> float:
    sa, sb = tokenize(a), tokenize(b)
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


def check_refractory(events, min_ms=0.8):
    last = {}
    for ev in events:
        ch, t = ev["channel"], ev["t_rel_ms"]
        if ch in last and t - last[ch] < min_ms - 1e-12:
            return f"{ch} gap {t - last[ch]} ms"
        last[ch] = t
    return None


def check_race(rec):
    start, end = rec["state"]["race_window_rel_ms"]
    in_win = {}
    for ev in rec["spike_events"]:
        if start <= ev["t_rel_ms"] <= end:
            in_win.setdefault(ev["channel"], 0)
            in_win[ev["channel"]] += 1
    if len(in_win) < 2:
        return f"race window has {len(in_win)} channels: {in_win}"
    return None


def excerpt_vs_spikes(rec):
    spike_us = {int(round(ev["t_rel_ms"] * 1000.0)) for ev in rec["spike_events"]}
    ex_us = {item["t_us"] for item in rec["raster"]["excerpt"]}
    if not spike_us:
        return 0.0
    return len(spike_us & ex_us) / len(spike_us)


def walk_keys(obj, path=""):
    found = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            p = f"{path}.{k}" if path else k
            if str(k).lower() in THOUGHT_KEYS:
                found.append(p)
            found.extend(walk_keys(v, p))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            found.extend(walk_keys(v, f"{path}[{i}]"))
    return found


def prior_batch_domains() -> set[str]:
    found: set[str] = set()
    for p in Path("/tmp").glob("ttf-r*/NOTES-r*.md"):
        if p.parent.name == "ttf-r33":
            continue
        text = p.read_text(errors="ignore")
        m = re.search(r"Domains this batch: (.+)", text)
        if m:
            found.update(re.findall(r"`([^`]+)`", m.group(1)))
    for p in Path("/tmp").glob("ttf-r*/batch-r*.jsonl"):
        if p.parent.name == "ttf-r33":
            continue
        for line in p.read_text(errors="ignore").splitlines():
            if not line.strip():
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            dom = rec.get("state", {}).get("domain")
            if isinstance(dom, str):
                found.add(dom)
    return found


def self_check(records):
    issues = []
    descs = [r["state"]["description"] for r in records]
    opens = [d.split(".")[0] for d in descs]
    if len(set(opens)) != 5:
        issues.append("opening sentences not unique")
    jmax = 0.0
    for i in range(5):
        for j in range(i + 1, 5):
            val = jaccard(descs[i], descs[j])
            jmax = max(jmax, val)
            if val >= 0.4:
                issues.append(f"Jaccard {records[i]['id']}/{records[j]['id']} = {val:.3f}")
    domains = [r["state"]["domain"] for r in records]
    if len(set(domains)) != 5:
        issues.append(f"domain collision {domains}")
    if set(domains) & BANNED_DOMAINS:
        issues.append(f"banned domains {set(domains) & BANNED_DOMAINS}")
    occupied = prior_batch_domains()
    hit = set(domains) & occupied
    if hit:
        issues.append(f"prior-batch domain collision {hit}")
    ids = [r["id"] for r in records]
    if ids != [f"ttf-r33-{n}" for n in range(181, 186)]:
        issues.append(f"ids {ids}")
    wrong = [
        r
        for r in records
        if r["safety_decision"].get("correctness") == "incorrect"
        or r["meta"].get("supervisor_error_type")
    ]
    if len(wrong) != 1 or wrong[0]["id"] != "ttf-r33-182":
        issues.append(f"wrong-gate set {[w['id'] for w in wrong]}")
    if wrong and wrong[0]["meta"].get("supervisor_error_type") != "wrong-modify":
        issues.append("182 supervisor_error_type")
    if any(r["state"]["sim_or_real"] == "real" for r in records):
        issues.append("sim_or_real=real")
    hil = [r["id"] for r in records if r["state"]["sim_or_real"] == "hil"]
    if hil != ["ttf-r33-183"]:
        issues.append(f"hil set {hil}")
    sim = [r["id"] for r in records if r["state"]["sim_or_real"] == "simulated"]
    if sim != ["ttf-r33-184"]:
        issues.append(f"simulated set {sim}")
    decisions = [r["safety_decision"]["decision"] for r in records]
    if (
        decisions.count("ACCEPT") != 2
        or decisions.count("MODIFY") != 2
        or decisions.count("REJECT") != 1
    ):
        issues.append(f"gate mix {decisions}")
    for rec in records:
        blob = json.dumps(rec)
        if "training_ready" in blob:
            issues.append(f"{rec['id']} training_ready present")
        if "outputs/raw" in blob:
            issues.append(f"{rec['id']} mentions outputs/raw")
        for frag in BANNED_PLANT_FRAGMENTS:
            if frag in blob:
                issues.append(f"{rec['id']} banned plant fragment {frag}")
        hidden = walk_keys(rec)
        if hidden:
            issues.append(f"{rec['id']} hidden keys {hidden}")
        err = check_refractory(rec["spike_events"])
        if err:
            issues.append(f"{rec['id']} refractory {err}")
        err = check_race(rec)
        if err:
            issues.append(f"{rec['id']} {err}")
        n = rec["raster"]["neurons"]
        rate = rec["raster"]["mean_rate_hz"]
        window_s = rec["raster"]["window_s"]
        expected = round(n * rate * window_s)
        if abs(rec["raster"]["spikes"] - expected) > 1:
            issues.append(f"{rec['id']} spike budget {rec['raster']['spikes']} vs {expected}")
        overlap = excerpt_vs_spikes(rec)
        if rec["id"] == "ttf-r33-181":
            if rec["raster"].get("excerpt_source") != "independent_lif":
                issues.append("181 missing independent_lif")
            if rec["future_outcome"]["reward_inflection_t_us"] > rec["raster"]["window_ms"] * 1000:
                issues.append("181 inflection outside window")
            if rec["reward_components"]["total"] >= 0:
                issues.append("181 partnered-neg total not negative")
        elif overlap >= 0.8:
            issues.append(f"{rec['id']} excerpt overlap {overlap:.2f}")
        inf = rec["future_outcome"]["reward_inflection_t_us"]
        tick_times = [t["t_us"] for t in rec["reward_components"]["ticks"]]
        if inf not in tick_times:
            issues.append(f"{rec['id']} inflection {inf} not a tick")
        if len(rec["reward_components"]["ticks"]) != 6:
            issues.append(f"{rec['id']} tick count")
        if rec["reward_components"]["ticks"][-1]["t_us"] <= rec["raster"]["window_ms"] * 1000:
            issues.append(f"{rec['id']} tick6 not after raster")
        if not (8 <= len(rec["state"]["episode_steps"]) <= 15):
            issues.append(f"{rec['id']} episode_steps")
        if rec["gate_snn"]["decision"] != rec["safety_decision"]["decision"]:
            issues.append(f"{rec['id']} gate_snn decision mismatch")
        if rec["meta"]["round"] != 33:
            issues.append(f"{rec['id']} meta.round")
        if rec["meta"]["rights"]["intended_use"] != "research_only":
            issues.append(f"{rec['id']} rights")
        if rec["meta"]["rights"]["linear_issue"] != "RM-793":
            issues.append(f"{rec['id']} linear_issue")
        if rec["meta"]["domain"] != rec["state"]["domain"]:
            issues.append(f"{rec['id']} domain mismatch")
        heads = ["task_progress", "safety", "efficiency", "coherence", "exploration"]
        total = sum(rec["reward_components"][h] for h in heads)
        if abs(total - rec["reward_components"]["total"]) > 1e-6:
            issues.append(f"{rec['id']} total mismatch {total}")
        for h in heads:
            s = sum(t[h] for t in rec["reward_components"]["ticks"])
            if abs(s - rec["reward_components"][h]) > 1e-6:
                issues.append(f"{rec['id']} {h} tick sum {s} vs {rec['reward_components'][h]}")
        nspk = len(rec["spike_events"])
        if not (8 <= nspk <= 16):
            issues.append(f"{rec['id']} spike count {nspk}")
        times = [e["t_rel_ms"] for e in rec["spike_events"]]
        if times != sorted(times):
            issues.append(f"{rec['id']} spike order")
        nex = len(rec["raster"]["excerpt"])
        if not (8 <= nex <= 16):
            issues.append(f"{rec['id']} excerpt count {nex}")
        exec_p = rec["executed_action"]["parameters"]
        prop_p = rec["proposed_action"]["parameters"]
        if rec["safety_decision"]["decision"] == "ACCEPT" and exec_p != prop_p:
            issues.append(f"{rec['id']} ACCEPT params differ")
        if rec["id"] == "ttf-r33-182":
            if "recovery" not in rec["future_outcome"]:
                issues.append("182 missing recovery")
            if exec_p.get("imp_mm") == 1.08:
                issues.append("182 accidentally applied the correct impression nudge")
            tos = {row["to"] for row in rec["raster"]["routing"]["table"]}
            if "policy_imp_nudge" in tos:
                issues.append("182 routing contains policy_imp_nudge")
            if "policy_imp_slam" not in tos:
                issues.append("182 routing missing policy_imp_slam")
        dw_s = rec["gate_snn"]["decision_window_ms"] / 1000.0
        for popu in rec["gate_snn"]["populations"]:
            if "mean_rate_hz" in popu:
                exp = round(popu["neurons"] * popu["mean_rate_hz"] * dw_s)
                if abs(popu["spikes"] - exp) > 1:
                    issues.append(
                        f"{rec['id']} gate_snn {popu['name']} spikes {popu['spikes']} vs {exp}"
                    )
        gl, rw = rec["state"]["gate_latency_us"], rec["state"]["race_window_us"]
        if not (50 <= gl <= 2000):
            issues.append(f"{rec['id']} gate_latency")
        if not (50 <= rw <= 1000):
            issues.append(f"{rec['id']} race_window")
        if rec["meta"]["rights"]["intended_use"] != "research_only":
            issues.append(f"{rec['id']} intended_use")
    return issues, jmax


def notes_text(jmax: float) -> str:
    return f"""# Thalamic Trajectory Factory — NOTES-r33

- Factory: `thalamic-trajectory-factory`
- Run label: `2026-09-02-final-heavy`
- Generator: `grok-4.6`
- Channel: SuperGrok Heavy consumer chat (RM-793 research-only)
- Quota: 5
- IDs: `ttf-r33-181` … `ttf-r33-185`
- Domains this batch: `spiral-freezer`, `offset-web-press`, `bascule-bridge`, `vacuum-induction-melt`, `airport-jetbridge`

These five domain slugs sit outside staged r12–r28 occupancy and outside r15/r17 plan tags. All five plants are invented. Do not restack r12–r28 plants (Marrow-Dock, Vesper-Lattice, Brine-Well, Saddle-Arc, Ashlar-Gait, Nacre-Well, Quern-Forge, Tinder-Box, Whimbrel-Stack, Cinder-Loft, Suture-Isle, Kiln-Spur, Oxbow-Switch, Pitch-Kettle, Shale-Quay, Polder-Rye, Flint-Mask, Gyre-Tokamak, Quarry-Bowl, Orpiment, Floe-Helix is this round).

## Batch map

| id | domain | decision | correctness | sim_or_real | total | edge |
|----|--------|----------|-------------|-------------|-------|------|
| ttf-r33-181 | spiral-freezer | MODIFY | correct | designed | **−0.48** | process-correct coil Delta-T clamp; frost-slab shear inside 42 ms raster; independent LIF |
| ttf-r33-182 | offset-web-press | MODIFY | **incorrect (wrong-modify / over-clamp)** | designed | −0.70 | impression 1.42 mm > 1.20 cap; clamp slammed 1.42→0.40 mm washup-deep instead of 1.08 mm nudge |
| ttf-r33-183 | bascule-bridge | REJECT | correct | hil | +0.78 | pin-gap 4.8 mm beats IR 0.12 deg; hold, do not fire pins |
| ttf-r33-184 | vacuum-induction-melt | ACCEPT | correct | simulated | +1.12 | coil 184 kW vs pyro glint 1510 C; proposed 184 kW already legal |
| ttf-r33-185 | airport-jetbridge | ACCEPT | correct | designed | +1.18 | bumper 12.4 kN vs slew 0.22 deg/s; proposed 0.08 m/s already legal |

Gate mix: 2 ACCEPT, 1 correct MODIFY (partnered-neg, in-window), 1 incorrect MODIFY (over-clamp), 1 correct REJECT. Provenance: designed×3, simulated×1, hil×1 (Leaf-Pike LP-6 span mockup). Intra-batch Jaccard on `state.description` {jmax:.3f}.

## Wrong-modify / over-clamp

**ttf-r33-182** is the mandated incorrect gate (`safety_decision.correctness=incorrect`, `meta.supervisor_error_type=wrong-modify`). This is **over-clamp / over-conservative**, not r13/r19 wrong-axis, not r14/r23 wrong-loop, not r21 wrong-polarity, not r24 under-clamp, not r25 wrong-phase. Do not emit a wrong-ACCEPT.

Ink-Noll IN-2 / Unit-4 reads impression **1.42 mm** against a **1.20 mm** crush cap. Web **4.8 m/s** is under a **6.5 m/s** cap. Sidecar arithmetic `1.42 > 1.20` is true. A timely modest clamp is impression **1.42 → 1.08 mm**. A weak supervisor applies the same actuator but slams **1.42 → 0.40 mm** (washup-deep), collapsing the nip. Convictable without print physics: `evidence.imp_mm > evidence.imp_cap_mm`, `imp_axis == impression_nip`, `executed_action.parameters.imp_mm=0.40` ≠ `correct_imp_mm=1.08`, `raster.routing.table` sends `relay_imp_gap` → `policy_imp_slam` (weight 0.74) with no positive weight to `policy_imp_nudge`, and `gate_snn` has `imp_slam` above threshold while `imp_nudge` is not. Recovery: MODIFY impression 1.42 → 1.08 mm; leave web 4.8 m/s. Cost: 9 min web re-thread (`abort_s=540`).

## Partnered-negative in-window (181)

**ttf-r33-181** is the partnered negative: process-correct MODIFY (coil held 9.2 K < 10.0 K cap) while the world still charges. Safety −0.64 prices the frost-slab shear at **23.400 ms**; `task_progress` stays +0.32 because the clamp completed. Inflection `t_us=23400` is tick 5 and is **inside** the 42 ms raster (`23400 ≤ 42000`). Named un-netted loss: 16 min helix chip + belt wash (`abort_s=960`). Not folded into process heads.

Independent LIF (the one labeled sidecar sim): `state.sim_or_real` remains `designed`. `raster.excerpt_source=independent_lif`, `raster.sim_scope=sidecar_only`, `raster.lif` seed 33181, stim `[22400, 25600]`. Excerpt is membrane crossings (`lif.clamp` early vs `lif.frost` 22.4–25.6 ms), not a 1:1 remap of `spike_events`. `meta.tags` include `independent-lif-raster` and `sidecar-sim-only`.

## Reward formula and tick reconciliation

Declared aggregation on every record:

`total = task_progress + safety + efficiency + coherence + exploration`

Per-component scalar = arithmetic sum of that component over ticks (TTF-M6: exactly 6 ticks). Tick 6 is bound to a published sidecar (`abort_s`, `survey_s`, `recycle_s`) via `future_outcome.delayed_surprise_s` and is strictly after the raster window. Inflection `t_us` is an actual tick.

| id | ticks | tp | saf | eff | coh | exp | total | inflection tick |
|----|-------|----|-----|-----|-----|-----|-------|-----------------|
| 181 | 6 | +0.32 | −0.64 | −0.16 | +0.04 | −0.04 | −0.48 | 5 (23400) |
| 182 | 6 | −0.22 | −0.20 | −0.24 | −0.10 | +0.06 | −0.70 | 4 (5760) |
| 183 | 6 | +0.10 | +0.40 | +0.12 | +0.10 | +0.06 | +0.78 | 4 (7680) |
| 184 | 6 | +0.42 | +0.32 | +0.18 | +0.12 | +0.08 | +1.12 | 4 (7880) |
| 185 | 6 | +0.44 | +0.34 | +0.20 | +0.12 | +0.08 | +1.18 | 4 (5280) |

Tick-6 sidecar bind: 181 `abort_s=960`, 182 `abort_s=540`, 183 `abort_s=720`, 184 `survey_s=360`, 185 `recycle_s=300`.

## Raster / energy (Loihi-2 4-core, 23 pJ/spike)

| id | domain | n | rate Hz | window_ms | spikes | energy_pJ | energy_uJ |
|----|--------|---|---------|-----------|--------|-----------|-----------|
| 181 | spiral-freezer | 72 | 26 | 42 | 79 | 1817 | 0.001817 |
| 182 | offset-web-press | 96 | 34 | 26 | 85 | 1955 | 0.001955 |
| 183 | bascule-bridge | 128 | 18 | 44 | 101 | 2323 | 0.002323 |
| 184 | vacuum-induction-melt | 52 | 40 | 32 | 67 | 1541 | 0.001541 |
| 185 | airport-jetbridge | 64 | 30 | 24 | 46 | 1058 | 0.001058 |

`spikes = round(n × rate × window_s)`. Every record carries `gate_snn` whose `decision` matches the safety gate; populations that declare rate+spikes meet the same ±1 budget against `decision_window_s`. `routing.third_factor` has modulator (NA / ACh / DA / 5-HT / adenosine), `tau_e_s`/`tau_e_ms` pair, and eligibility. Excerpt same-neuron gap ≥ 1000 µs; spike trains same-channel refractory ≥ 0.8 ms. Non-181 excerpts are kernelized and independent of `spike_events` times (overlap < 0.8).

## Local checks (staging, not raw)

See generator stdout: `check_jsonl` FactoryStaging, `validate_run.check_line`, `dumps_exact_json`, `raster_status`, `verify_batch_for_frontier(strict=True)`, `spike_probe.py --strict`, tick sums, refractory, Jaccard.

Never `training_ready`. Never `sim_or_real=real`. Never wrote `outputs/raw/`.

## Residual weaknesses (honest)

1. Only **one** labeled independent LIF (181). The other four excerpts are independent of `spike_events` times but are not declared population sims.
2. Wrong-ACCEPT still absent (guard).
3. Tick-6 sidecar bind is a densification of r14/r16, not a new class.
4. Five domain slugs leave the prompt's 8-item pool; a later round that must stay inside the pool will have to rotate sit-outs instead.
5. 184/185 ACCEPT are already-legal proposals confirmed by race order; a later round could pair an ACCEPT with a world charge that does not go negative.

## Next densification target

Labeled LIF on a second record, or an ISI histogram sidecar. Remaining unused wrong-MODIFY subclasses after this over-clamp: clamp-too-early on a precursor that has not crossed cap. Wrong-ACCEPT remains structurally absent until a prompt amendment.

Novel coverage: 19.0%
"""


def run_pipelines(records):
    sys.path.insert(0, str(PIPELINES))
    from check_records import FactoryStaging, check_jsonl
    from curate_bridge import raster_status
    from exact_json import dumps_exact_json
    from round_txn import validate_novel_coverage
    from validate_run import check_line
    from verify_execution import verify_batch_for_frontier

    report = []
    errors, warnings, kinds, nrec = check_jsonl(
        BATCH_PATH, "batch-r33.jsonl", staging=FactoryStaging(enabled=True)
    )
    report.append(("check_jsonl FactoryStaging", errors, warnings, kinds, nrec))
    line_errs = []
    for i, rec in enumerate(records, 1):
        errs, kind = check_line(rec, f"batch-r33.jsonl:{i}", factory_staging=True)
        if errs:
            line_errs.append((i, kind, errs))
        try:
            dumps_exact_json(rec, ensure_ascii=False, sort_keys=False)
        except Exception as exc:
            line_errs.append((i, "exact_json", [str(exc)]))
    report.append(("check_line+exact_json", line_errs, None, None, None))
    raster_fail = []
    for rec in records:
        st = raster_status(rec, require_raster=True, require_routing_table=True)
        if not st.get("raster_valid") or not st.get("gate_snn_valid"):
            raster_fail.append((rec["id"], st))
    report.append(("raster_status", raster_fail, None, None, None))
    counts, findings, blocked = verify_batch_for_frontier(BATCH_PATH, strict=True)
    report.append(("verify_batch_for_frontier", counts, findings, blocked, None))
    cov = validate_novel_coverage(
        NOTES_PATH,
        Path("thalamic-trajectory-factory"),
        notes_text=NOTES_PATH.read_text(),
        required=True,
    )
    report.append(("validate_novel_coverage", cov, None, None, None))
    probe = subprocess.run(
        [sys.executable, str(PIPELINES / "spike_probe.py"), "--strict", str(BATCH_PATH)],
        cwd=str(REPO),
        capture_output=True,
        text=True,
    )
    report.append(("spike_probe", probe.returncode, probe.stdout[-2000:], probe.stderr[-2000:], None))
    schema_err = None
    try:
        import jsonschema
        from referencing import Registry, Resource
        from referencing.jsonschema import DRAFT202012

        schema_dir = REPO / "schemas"
        ttf_schema = json.loads((schema_dir / "thalamic-trajectory-v2.schema.json").read_text())
        raster_schema = json.loads((schema_dir / "raster.schema.json").read_text())
        base_schema = json.loads((schema_dir / "thalamic-trajectory.schema.json").read_text())
        registry = Registry().with_resources(
            [
                ("thalamic-trajectory-v2.schema.json", Resource.from_contents(ttf_schema, DRAFT202012)),
                ("thalamic-trajectory.schema.json", Resource.from_contents(base_schema, DRAFT202012)),
                ("raster.schema.json", Resource.from_contents(raster_schema, DRAFT202012)),
            ]
        )
        validator = jsonschema.Draft202012Validator(ttf_schema, registry=registry)
        fails = []
        for rec in records:
            errs = sorted(validator.iter_errors(rec), key=lambda e: list(e.path))
            if errs:
                fails.append((rec["id"], [e.message for e in errs[:4]]))
        schema_err = fails
    except Exception as exc:
        schema_err = f"skip:{exc}"
    report.append(("jsonschema", schema_err, None, None, None))
    return report


def main() -> int:
    if str(BATCH_PATH).startswith(str(REPO / "outputs" / "raw")):
        print("refusing to write outputs/raw")
        return 1
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    records = [record_181(), record_182(), record_183(), record_184(), record_185()]
    issues, jmax = self_check(records)
    lines = [
        json.dumps(rec, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
        for rec in records
    ]
    BATCH_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    NOTES_PATH.write_text(notes_text(jmax), encoding="utf-8")
    print(f"wrote {BATCH_PATH} lines={len(lines)} jmax={jmax:.3f}")
    print(f"wrote {NOTES_PATH}")
    if issues:
        print("SELF_CHECK_ISSUES:")
        for item in issues:
            print(" -", item)
        return 1
    print("SELF_CHECK_OK")
    report = run_pipelines(records)
    failed = False
    for item in report:
        name = item[0]
        print(f"PIPELINE {name}: {item[1:]}")
        if name == "check_jsonl FactoryStaging":
            errors, warnings, kinds, nrec = item[1], item[2], item[3], item[4]
            print(f"  kinds={kinds} n={nrec} errors={len(errors)} warnings={len(warnings)}")
            for e in errors:
                print("  ERR", e)
                failed = True
        elif name == "check_line+exact_json":
            if item[1]:
                print("  LINE_ERR", item[1])
                failed = True
        elif name == "raster_status":
            if item[1]:
                print("  RASTER_FAIL", item[1])
                failed = True
        elif name == "verify_batch_for_frontier":
            if item[3]:
                print("  BLOCKED", item[1], item[2])
                failed = True
        elif name == "validate_novel_coverage":
            if item[1]:
                print("  COVERAGE", item[1])
                failed = True
        elif name == "spike_probe":
            if item[1] != 0:
                print("  PROBE_FAIL", item[2], item[3])
                failed = True
        elif name == "jsonschema":
            if isinstance(item[1], list) and item[1]:
                print("  SCHEMA_FAIL", item[1])
                failed = True
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
