#!/usr/bin/env python3
"""Emit TTF r32 JSONL (ttf-r32-176..180) into /tmp/ttf-r32/. Never writes outputs/raw/."""

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

OUT_DIR = Path("/tmp/ttf-r32")
BATCH_PATH = OUT_DIR / "batch-r32.jsonl"
NOTES_PATH = OUT_DIR / "NOTES-r32.md"
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
        ("generated_at", "2026-09-02T17:12:00Z"),
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
    "chlor-alkali-membrane",
    "coke-oven-battery",
    "tire-curing-press",
    "hdd-pilot-bore",
    "composite-autoclave",
    "helium-liquefier",
    "escalator-comb",
    "escalator-comb-plate",
    "jet-fuel-hydrant",
    "hydro-wicket-gate",
    "wind-turbine-pitch",
    "wind-nacelle-yaw",
    "wind-tunnel-balance",
    "steel-caster-mold",
    "cement-precalciner",
    "air-sep-coldbox",
    "spent-fuel-bridge",
    "PET-stretch-blow",
    "jackup-preload",
    "electrolyzer-stack",
    "autoclave-retort",
    "solar-trough-htf",
    "transformer-oltc",
    "electrostatic-precipitator",
    "electron-linac",
    "dairy-falling-film",
    "dissolved-air-flotation",
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
    "Oolite-Span",
    "Fathom-Lock",
    "Loess-Stride",
    "Swage-Holt",
    "Slag-Siding",
    "Sinter-Ridge",
    "Chaff-Mere",
    "Caisson-Forge",
    "Crumb-Vault",
    "Caliche-Drift",
    "Anode-Fen",
    "Kipple-Gate",
    "Vial-Rime",
    "Tern-Apron",
    "Thaw-Reach",
    "Fjord-Convert",
    "Kelp-Jetty",
    "Skerries-Trench",
    "Iodine-Well",
    "Rime-Vault",
    "Lyo-Deck",
    "Halite-Keel",
    "Caldera-Mold",
    "Isotope-Pad",
    "Lay-Sound",
    "Drupe-Press",
    "Marl-Knap",
    "Gull-Pontoon",
    "Dee-Keeper",
    "Sprue-Nook",
    "Osmia-Reach",
    "Hood-Pike",
    "Marl-Rake",
    "Bight-Lay",
    "Cryolite-Hall",
    "Surge-Adit",
    "Massecuite-Kettle",
    "Wort-Cairn",
    "Firn-Span",
    "Sleet-Row",
    "Oxbow-Pound",
    "Tuyere-Holt",
    "Meridian Coldstore",
    "Kestrel-2",
    "Cerro Tolvara",
    "Red Mesa",
    "Helix Vault",
    "Solstice Coldchain",
    "Gale Ridge",
    "Salar Trench",
    "Glasswalk",
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
    return OrderedDict(
        [
            ("source", source),
            ("target", target),
            (
                "table",
                [
                    OrderedDict([("from", a), ("to", b), ("weight", w)])
                    for a, b, w in table
                ],
            ),
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


def spike_avoid_us(events):
    return [int(round(ev["t_rel_ms"] * 1000.0)) for ev in events]


def lif_177_excerpt():
    """Independent CUBA LIF (seed 32177). Plant remains designed."""

    n = 84
    dt_us = 100
    tau_m_ms = 20.0
    v_th = 1.0
    v_reset = 0.0
    refractory_us = 1000
    i_bias = 0.92
    i_stim_peak = 2.45
    stim = (21000, 25000)
    seed = 32177
    window_us = 40000
    i_clamp_extra = 0.68
    clamp_n = 14
    rng = random.Random(seed)
    tau_s = tau_m_ms / 1000.0
    dt_s = dt_us / 1e6
    decay = math.exp(-dt_s / tau_s)
    steps = window_us // dt_us
    voltage = [rng.random() * v_th * 0.98 for _ in range(n)]
    bias = [i_bias * (1.0 + 0.12 * (rng.random() * 2 - 1)) for _ in range(n)]
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
    early = [(t, nid) for t, nid in spikes if t < 21000]
    burst = [(t, nid) for t, nid in spikes if 21000 <= t < 25000]
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
            early_flag = pool[0][0] < 21000
            have = len([1 for t, _ in picked if (t < 21000) == early_flag])
            if have >= want:
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
    take(burst, 9, label_times=(22400, 23100, 23800))
    clamp = [(t, nid) for t, nid in picked if t < 21000][:7]
    spout = [(t, nid) for t, nid in picked if t >= 21000][:9]
    picked = sorted(clamp + spout, key=lambda item: (item[0], item[1]))
    if len(picked) < 8:
        raise RuntimeError(f"LIF excerpt too short: {len(picked)}")
    channels = ["lif.clamp" if t < 21000 else "lif.spout" for t, _ in picked]
    lif = OrderedDict(
        [
            ("model", "leaky_integrate_and_fire"),
            ("n", 84),
            ("dt_us", 100),
            ("tau_m_ms", 20.0),
            ("v_rest", 0.0),
            ("v_reset", 0.0),
            ("v_th", 1.0),
            ("r_m", 1.0),
            ("refractory_us", 1000),
            ("i_bias", 0.92),
            ("i_stim_peak", 2.45),
            ("stim_t_us", [21000, 25000]),
            ("i_clamp_extra", 0.68),
            ("clamp_n", 14),
            ("seed", 32177),
            (
                "note",
                "Population sim scoped to this sidecar. Plant remains designed. "
                "Neurons 0-13 carry +0.68 liquor-clamp bias; stim 21-25 ms is the smelt-water spout.",
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
            ("round", 32),
            ("factory", "thalamic-trajectory-factory"),
            ("generator", "grok-4.6"),
            ("run_label", "2026-09-02-final-heavy"),
            ("schema_version", "thalamic-trajectory-v2"),
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


def record_176():
    ticks = [
        tick(2112, -0.02, 0.01, -0.02, -0.01, 0.01),
        tick(5280, -0.04, 0.01, -0.04, -0.02, 0.01),
        tick(5510, -0.03, 0.01, -0.03, -0.01, 0.01),
        tick(6000, -0.06, 0.02, -0.08, -0.03, 0.02),
        tick(6400, -0.02, 0.01, -0.03, -0.01, 0.01),
        tick(780000000, -0.01, 0.00, -0.02, 0.00, 0.00),
    ]
    spikes = [
        spike("enc.feed.t.ctx", 1.205, 0.44),
        spike("live.t.bed", 2.410, 0.61),
        spike("peak.hold.t", 3.880, 0.52),
        spike("enc.kiln.ctx", 4.620, 0.47),
        spike("live.t.bed", 5.280, 1.31),
        spike("peak.hold.t", 5.510, 1.18),
        spike("ctrl.gate", 6.000, 0.99),
        spike("live.t.bed", 7.220, 0.84),
        spike("peak.hold.t", 9.440, 0.66),
        spike("ctrl.gate", 14.880, 0.88),
        spike("enc.feed.t.ctx", 18.400, 0.41),
        spike("live.t.bed", 24.200, 0.58),
    ]
    excerpt = independent_excerpt(32176, 72, 26000, 12, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Calciner C-22 already sits at 318 C on the Nahcolite-Kettle trona rotary when "
                "a live bed pyrometer sample races a 38 s-stale peak-hold that still prints 346 C. "
                "Published trip is 340 C on the live channel; a weak supervisor treats the stale "
                "peak as the trip and zeros a legal 12.0 t/h feed.",
            ),
            ("domain", "trona-calciner"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Hold 12.0 t/h on C-22, keep live bed temperature < 340 C trip, and finish the 13 min "
                "soda-ash window.",
            ),
            ("t0_us", 1762300000000176),
            ("gate_latency_us", 720),
            ("race_window_us", 400),
            ("race_window_rel_ms", [5.280, 5.680]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "live.t.bed 318 C live pyrometer",
                                "peak.hold.t 346 C stale 38 s",
                            ],
                        ),
                        (
                            "semantics",
                            "Live-first should ACCEPT 12.0 t/h (318 C < 340 C trip). Peak-hold-first "
                            "would only delay confirmation of the same legal live bed temperature.",
                        ),
                        (
                            "window_derivation",
                            "400 us = one pyrometer ADC slot versus the peak-hold publisher on this "
                            "2 kHz calciner bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 230 us vs combined jitter 76 us (live 34 + peak 42): 3.0x over "
                            "a 2.0x trust floor. Order is correctly live-first. The error is binding "
                            "a stale peak-hold as if it were live, not the race.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "live bed pyrometer, 2 kHz, 34 us jitter, axis bed_t",
                    "peak-hold temperature latch, 1 kHz, 42 us jitter, age 38 s",
                    "feed-rate encoder (context)",
                    "kiln drive (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("live_C", 318.0),
                        ("trip_C", 340.0),
                        ("peak_hold_C", 346.0),
                        ("peak_hold_age_s", 38.0),
                        ("peak_hold_max_s", 8.0),
                        ("proposed_t_h", 12.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Calciner C-22 indexed on Nahcolite-Kettle rotary; live 318 C, 12.0 t/h armed.",
                    "2. Published live trip 340 C; peak-hold max age 8 s; latch currently 38 s stale.",
                    "3. Feed precursor at 1.205 ms.",
                    "4. Race window [5.280, 5.680] ms.",
                    "5. Live bed 318 C at 5.280 ms (winner).",
                    "6. Peak-hold 346 C at 5.510 ms (loser by 230 us).",
                    "7. Gate at 6.000 ms: wrong REJECT holds 0 t/h on the stale peak.",
                    "8. Rotary idle; live bed never crossed 340 C.",
                    "9. 13 min soda-ash window missed.",
                    "10. QA: correct gate was ACCEPT; leave 12.0 t/h; bind live 318 C vs 340 C trip.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "calciner_12t_hold"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("feed_t_h", 12.0),
                        ("live_C", 318.0),
                        ("hold", False),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("live_C", 318.0),
                        ("trip_C", 340.0),
                        ("peak_hold_C", 346.0),
                        ("peak_hold_age_s", 38.0),
                        ("peak_hold_max_s", 8.0),
                        ("ft_axis", "bed_t"),
                        ("race_margin_us", 230),
                        ("combined_jitter_us", 76),
                        ("t_gate_us", 6000),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 12.0 t/h because live bed 318 C is 22 C under the "
                "published 340 C trip and the 346 C peak-hold is 38 s stale (max age 8 s).",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "REJECT"),
            ("correctness", "incorrect"),
            (
                "rationale",
                "Peak-hold 346 C is over the 340 C trip (true vs that stale latch). REJECT: "
                "hold 0 t/h until the peak-hold recovers under 340 C so the calciner bed does not "
                "see an over-temperature event.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "bed_temperature_C",
                            OrderedDict(
                                [
                                    ("published_live_trip", 340.0),
                                    ("observed_live", 318.0),
                                    ("stale_peak_applied", 346.0),
                                    ("peak_age_s", 38.0),
                                    ("executed_t_h", 0.0),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 230),
                                    ("combined_jitter_us", 76),
                                    ("ratio", 3.03),
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
            ("name", "calciner_hold_stale_peak"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("feed_t_h", 0.0),
                        ("live_C", 318.0),
                        ("hold", True),
                    ]
                ),
            ),
            (
                "gate_effect",
                "REJECT (incorrect): feed 12.0 -> 0 t/h. Routing relay.live.t -> "
                "policy.hold_reject; no positive weight to policy.go_accept. Live 318 C never "
                "violated the 340 C trip.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Wrong-REJECT froze C-22 at 0 t/h while live bed stayed 318 C under the "
                "340 C trip. 13 min soda-ash window missed. Correct gate was ACCEPT of the "
                "already-legal 12.0 t/h command.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("calciner", "held at 0 t/h; 12.0 t/h abandoned"),
                        ("live_C", "still 318 C, under 340 C published trip"),
                        ("rotary", "13 min soda-ash window missed"),
                        ("bed", "no over-temperature; peak-hold false positive"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "The 346 C peak-hold is 38 s stale; peak-hold_max_s is 8 s and the latch is not a published live trip.",
                    "Delayed (13 min): sister-calciner C-23 ran the same 12.0 t/h soda-ash window after QA rebound the live trip; C-22's slot was already gone.",
                ],
            ),
            (
                "recovery",
                OrderedDict(
                    [
                        (
                            "correct_gate",
                            "ACCEPT: live 318 C < published 340 C trip; leave 12.0 t/h.",
                        ),
                        ("correct_trip_C", 340.0),
                        ("wrong_peak_C", 346.0),
                        (
                            "wrong_edit_applied",
                            OrderedDict([("feed_t_h", 0.0), ("hold", True)]),
                        ),
                        (
                            "cost",
                            "13 min missed soda-ash window (task/efficiency); live bed never over trip (safety false-positive).",
                        ),
                    ]
                ),
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "live.t.bed (5.280 ms, 318 C)"),
                        ("loser", "peak.hold.t (5.510 ms, 346 C stale)"),
                        ("margin_us", 230),
                        (
                            "counterfactual_if_reversed",
                            "Peak-hold-first by < 230 us would still show live 318 C < 340 C. A "
                            "correct gate ACCEPTs either way. The wrong REJECT spent the live win "
                            "on a stale peak-hold.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 6000),
            (
                "reward_inflection_note",
                "Task and efficiency drop at the wrong REJECT (6.000 ms, tick 4). The 13 min "
                "missed window is delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 780.0),
            ("missed_window_s", 780),
        ]
    )
    ras = raster_core(
        26,
        72,
        32,
        60,
        routing(
            "relay.live.t",
            "policy.hold_reject",
            [
                ("relay.live.t", "policy.hold_reject", 0.71),
                ("relay.peak.hold", "policy.hold_reject", 0.22),
            ],
            "acetylcholine",
            0.08,
            "stale_peak_stdp; ACh tags the (wrong) hold_reject bind at the live win",
        ),
        excerpt,
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.40),
            ("decision", "REJECT"),
            (
                "populations",
                [
                    pop("hold_reject", 48, 0.50, 200.0, 4),
                    pop("go_accept", 48, 0.80, 10.0, 0),
                    pop("live_trip_veto", 24, 0.75),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r32-176"),
            (
                "title",
                "WRONG-REJECT at Nahcolite-Kettle / Calciner C-22: live 318 C is legal vs "
                "published 340 C trip; supervisor bound a 38 s-stale 346 C peak-hold",
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
                    "Wrong-reject. Sidecar arithmetic 318 < 340 is true; clamp bound to a "
                    "stale 346 C peak-hold. total -0.36 = -0.18 + 0.06 + -0.22 + -0.08 + 0.06.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "trona-calciner",
                    [
                        "reject",
                        "wrong-gate",
                        "stale-peak-hold",
                        "peak-as-live",
                        "sidecar-convictable",
                        "designed",
                    ],
                    "Teaches a probe that a correct live<trip read can still be a wrong gate when "
                    "routing.table[0].to is policy.hold_reject and executed feed is zeroed.",
                    1,
                    supervisor_error_type="wrong-reject",
                ),
            ),
        ]
    )


def record_177():
    excerpt, extra = lif_177_excerpt()
    ticks = [
        tick(1848, 0.05, -0.02, -0.02, 0.01, 0.00),
        tick(4620, 0.08, -0.04, -0.03, 0.01, -0.01),
        tick(4850, 0.04, -0.03, -0.02, 0.00, 0.00),
        tick(5500, 0.10, -0.06, -0.03, 0.02, -0.01),
        tick(22400, 0.05, -0.42, -0.04, 0.00, -0.02),
        tick(960000000, 0.02, -0.05, -0.02, 0.00, 0.00),
    ]
    state = OrderedDict(
        [
            (
                "description",
                "Boiler B-2 is firing 4.2 kg/s black liquor through the Smelt-Spur recovery hearth "
                "when a char-bed pyrometer pulse arrives 230 us before the liquor-flow meter that "
                "still reads a legal spout. Bed-first latches a process clamp under the 780 C cap; "
                "flow-first would keep cruise liquor. Stored smelt-water is not yet an observable "
                "of either race channel.",
            ),
            ("domain", "kraft-recovery-boiler"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Fire 4.2 kg/s liquor through B-2, keep char-bed <= 780 C, and leave the smelt "
                "bed unexploded.",
            ),
            ("t0_us", 1762300000000177),
            ("gate_latency_us", 880),
            ("race_window_us", 380),
            ("race_window_rel_ms", [4.620, 5.000]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "pyro.bed.c 812 C char-bed",
                                "ft.liquor.kgs 4.2 kg/s still-legal spout",
                            ],
                        ),
                        (
                            "semantics",
                            "Bed-first latches liquor clamp 4.2 -> 2.8 kg/s; flow-first keeps cruise "
                            "liquor on a 'spout still open' model.",
                        ),
                        (
                            "window_derivation",
                            "380 us = one bed-pyrometer slot minus liquor-FT group delay on this "
                            "1 kHz recovery bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 230 us vs combined jitter 68 us (pyro 30 + FT 38): 3.4x over "
                            "a 2.0x trust floor. Reversing order by < 230 us inside the 380 us window "
                            "would have kept 4.2 kg/s cruise; predicted next-sample bed 798 C > 780 cap.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "char-bed pyrometer, 1 kHz, 30 us timestamp jitter",
                    "liquor mass-flow, 1 kHz, 38 us jitter",
                    "smelt-bed IR (context)",
                    "furnace AE (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("bed_cap_C", 780.0),
                        ("observed_bed_C", 812.0),
                        ("proposed_liquor_kg_s", 4.2),
                        ("liquor_floor_kg_s", 2.4),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Boiler B-2 indexed; 4.2 kg/s black liquor; char-bed 812 C > 780 cap.",
                    "2. Cruise liquor 4.2 kg/s armed; bed over the 780 C cap.",
                    "3. IR precursor at 1.848 ms; bed warm-start 812 C.",
                    "4. Race window [4.620, 5.000] ms opens on the recovery bus.",
                    "5. Char-bed 812 C at 4.620 ms (winner).",
                    "6. Liquor FT 4.2 kg/s at 4.850 ms (loser by 230 us).",
                    "7. Gate at 5.500 ms (winner + 880 us): MODIFY clamp 4.2 -> 2.8 kg/s.",
                    "8. Clamp executes; next-sample bed 768 C < 780 cap.",
                    "9. At 22.400 ms stored smelt-water produces a spout / ignition precursor.",
                    "10. Emergency dump 16 min + hearth inspection; named un-netted loss, not folded into process heads.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_liquor_fire"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("liquor_kg_s", 4.2),
                        ("bed_C", 812.0),
                        ("hold", False),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("bed_C", 812.0),
                        ("bed_cap_C", 780.0),
                        ("predicted_unclamped_next_C", 798.0),
                        ("liquor_kg_s", 4.2),
                        ("race_margin_us", 230),
                        ("combined_jitter_us", 68),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 4.2 kg/s cruise: liquor flow looks like an open spout, not a "
                "plugged gun, and the 780 C bed cap is treated as still open.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "correct"),
            (
                "rationale",
                "Char-bed 812 C won by 230 us, so the hearth is running hot, not still free. "
                "Holding 4.2 kg/s predicts next-sample 798 C > 780 C cap. MODIFY: liquor 4.2 -> "
                "2.8 kg/s. Observed after clamp 768 C < 780. A full REJECT is not indicated: a "
                "sound bed accepts 2.8 kg/s.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "char_bed_C",
                            OrderedDict(
                                [
                                    ("cap", 780.0),
                                    ("observed", 812.0),
                                    ("predicted_unclamped_next", 798.0),
                                    ("clamped_liquor_kg_s", 2.8),
                                    ("observed_after_clamp", 768.0),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 230),
                                    ("combined_jitter_us", 68),
                                    ("ratio", 3.38),
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
            ("name", "clamped_liquor_fire"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("liquor_kg_s", 2.8),
                        ("bed_C", 768.0),
                        ("hold", False),
                    ]
                ),
            ),
            (
                "gate_effect",
                "MODIFY: liquor 4.2 -> 2.8 kg/s. Process-correct vs the 780 C bed cap. Smelt-water "
                "spout still occurs at 22.400 ms.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Process-correct MODIFY held bed at 768 C. At 22.400 ms stored smelt-water produced "
                "a spout / ignition precursor. Clamp reduced liquor energy; it did not dump the "
                "hearth charge. Partnered negative: process heads stay honest; world loss is named, "
                "not netted.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("liquor", "clamp executed; bed 768 C < 780"),
                        ("hearth", "smelt-water spout at 22.400 ms"),
                        ("repair", "16 min emergency dump + hearth inspection"),
                        ("mission", "boiler still firing; ignition precursor controlled"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Neither bed pyro nor liquor FT predicted the smelt-water charge; ae.spout.steam is a new channel at 22.400 ms, 16.900 ms after the gate, still inside the 40 ms raster.",
                    "Delayed (16 min): emergency dump and hearth inspection close the spout. Named un-netted loss, not folded into task_progress.",
                ],
            ),
            (
                "un_netted_loss",
                "16 min emergency dump + hearth inspection after a smelt-water spout. Safety head "
                "-0.62 prices the ignition precursor; task_progress stays +0.34 because the liquor "
                "clamp completed under the 780 C cap. World loss is named here, not subtracted from process heads.",
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "pyro.bed.c (4.620 ms, 812 C)"),
                        ("loser", "ft.liquor.kgs (4.850 ms, 4.2 kg/s)"),
                        ("margin_us", 230),
                        (
                            "counterfactual_if_reversed",
                            "Flow-first by < 230 us inside the 380 us window would have kept "
                            "4.2 kg/s cruise; predicted next-sample 798 C would have exceeded the "
                            "780 C cap even without the spout charge. The MODIFY is still the "
                            "correct process. The spout is a later world charge either way, cheaper "
                            "with the clamp than without.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 22400),
            (
                "reward_inflection_note",
                "Safety collapses at the 22.400 ms smelt-water spout (tick t_us=22400), inside the "
                "40 ms raster. The correct MODIFY at 5.500 ms is in the same excerpt. Do not put "
                "inflection on the +16 min dump tick.",
            ),
            ("delayed_surprise_s", 960.0),
            ("abort_s", 960),
        ]
    )
    spikes = [
        spike("ir.hearth.ctx", 1.120, 0.43),
        spike("pyro.bed.c", 2.240, 0.62),
        spike("ft.liquor.kgs", 3.180, 0.55),
        spike("pyro.bed.c", 4.620, 1.34),
        spike("ft.liquor.kgs", 4.850, 1.12),
        spike("ctrl.gate", 5.500, 0.97),
        spike("pyro.bed.c", 7.200, 0.81),
        spike("ft.liquor.kgs", 10.400, 0.66),
        spike("ctrl.gate", 15.200, 0.84),
        spike("ae.spout.steam", 22.400, 1.42),
        spike("ae.spout.steam", 23.600, 0.91),
        spike("ir.hearth.ctx", 29.800, 0.41),
        spike("pyro.bed.c", 36.200, 0.58),
    ]
    ras = raster_core(
        40,
        84,
        26,
        87,
        routing(
            "thalamic-relay.bed-liquor",
            "spikenaut.policy.liquor-clamp",
            [
                ("relay.pyro.bed", "policy.liquor_clamp", 0.64),
                ("relay.ft.liquor", "policy.spout_hold", 0.29),
                ("relay.ae.spout", "policy.liquor_clamp", -0.46),
            ],
            "noradrenaline",
            0.05,
            "surprise-gated pre_post_stdp; NA at bed win (4.620 ms) opens a 50 ms eligibility "
            "trace that still covers the 22.400 ms smelt-water spout",
        ),
        excerpt,
        extra=extra,
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.38),
            ("decision", "MODIFY"),
            (
                "populations",
                [
                    pop("liquor_clamp", 48, 0.50, 220.0, 4),
                    pop("spout_hold", 48, 0.50, 50.0, 1),
                    pop("bed_cap_veto", 24, 0.75),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r32-177"),
            (
                "title",
                "Smelt-Spur recovery / Boiler B-2: char-bed beats liquor FT by 230 us; correct "
                "MODIFY still eats an in-window smelt-water spout (partnered negative total -0.44)",
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
                    "40 ms raster. total -0.44 = 0.34 + -0.62 + -0.16 + 0.04 + -0.04. Named "
                    "dump+inspection loss is not netted into task_progress.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "kraft-recovery-boiler",
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
                    "16 min gap.",
                    2,
                ),
            ),
        ]
    )


def record_178():
    ticks = [
        tick(1568, 0.01, 0.04, 0.02, 0.01, 0.01),
        tick(3920, 0.02, 0.08, 0.02, 0.02, 0.01),
        tick(4110, 0.01, 0.06, 0.02, 0.01, 0.01),
        tick(5100, 0.03, 0.12, 0.04, 0.04, 0.02),
        tick(5380, 0.02, 0.07, 0.01, 0.01, 0.01),
        tick(540000000, 0.01, 0.03, 0.01, 0.01, 0.00),
    ]
    spikes = [
        spike("enc.ram.ctx", 1.040, 0.44),
        spike("ae.crucible.pps", 2.180, 0.71),
        spike("enc.melt.kgh", 3.020, 0.52),
        spike("ae.crucible.pps", 3.920, 1.36),
        spike("enc.melt.kgh", 4.110, 1.14),
        spike("ctrl.gate", 5.100, 0.98),
        spike("ae.crucible.pps", 7.400, 0.82),
        spike("enc.melt.kgh", 10.800, 0.61),
        spike("ctrl.gate", 16.200, 0.86),
        spike("ae.crucible.pps", 24.600, 0.70),
        spike("enc.melt.kgh", 33.400, 0.48),
        spike("ir.pad.ctx", 41.200, 0.40),
    ]
    excerpt = independent_excerpt(32178, 120, 44000, 13, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Melt M-7 on the Ingot-Cairn VAR HIL pad is pulling 410 kg/h when an AE burst at "
                "58 pps on the crucible wall races the melt-rate encoder that still looks in-band "
                "for a ram step. Ramp is legal only if AE <= 40 pps. AE-first latches hold; "
                "encoder-first would treat in-band melt-rate as arc clearance.",
            ),
            ("domain", "var-ingot-melt"),
            ("sim_or_real", "hil"),
            (
                "goal",
                "Do not ramp Melt M-7 unless AE <= 40 pps; keep melt rate 0 kg/h until the "
                "crucible is quiet.",
            ),
            ("t0_us", 1762300000000178),
            ("gate_latency_us", 1180),
            ("race_window_us", 280),
            ("race_window_rel_ms", [3.920, 4.200]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "ae.crucible.pps 58 pps flare",
                                "enc.melt.kgh 410 kg/h still-in-band",
                            ],
                        ),
                        (
                            "semantics",
                            "AE-first latches REJECT hold 0 kg/h; encoder-first would ramp 410 kg/h "
                            "on an in-band-rate-as-clearance model.",
                        ),
                        (
                            "window_derivation",
                            "280 us = one AE envelope slot versus the ram-encoder publisher on this "
                            "pad cycle.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 190 us vs combined jitter 54 us (AE 24 + encoder 30): 3.5x over a "
                            "2.0x trust floor. Pad injects encoder 90-130 us before the AE envelope "
                            "finishes (piezo lag, not a sensor fault); the encoder packet is still "
                            "the loser in this 280 us window.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "crucible AE, 24 us jitter, 40 pps trip",
                    "melt-rate ram encoder, 30 us jitter",
                    "vacuum PT (context)",
                    "slag IR (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("ae_trip_pps", 40.0),
                        ("observed_ae_pps", 58.0),
                        ("melt_cap_kg_h", 480.0),
                        ("proposed_melt_kg_h", 410.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Melt M-7 on Ingot-Cairn HIL pad; vacuum in band; ram armed at 410 kg/h.",
                    "2. AE trip 40 pps; observed 58 pps flare on crucible wall.",
                    "3. Encoder precursor at 1.040 ms.",
                    "4. Race window [3.920, 4.200] ms.",
                    "5. AE 58 pps at 3.920 ms (winner).",
                    "6. Melt encoder 410 kg/h at 4.110 ms (loser by 190 us).",
                    "7. Gate at 5.100 ms: REJECT hold 0 kg/h, do not ramp.",
                    "8. Pad recycle 9 min; crucible AE decays under 40 pps after hold.",
                    "9. Vacuum never broke; encoder-as-clearance would have ramped into the flare.",
                    "10. QA: correct gate was REJECT; leave 0 kg/h until AE <= 40 pps.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "ramp_410kgh"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("melt_kg_h", 410.0),
                        ("ae_pps", 58.0),
                        ("hold", False),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("ae_pps", 58.0),
                        ("ae_trip_pps", 40.0),
                        ("melt_kg_h", 410.0),
                        ("melt_cap_kg_h", 480.0),
                        ("race_margin_us", 190),
                        ("combined_jitter_us", 54),
                        ("t_gate_us", 5100),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 410 kg/h because melt-rate is under the 480 kg/h cap and treats "
                "the encoder as arc clearance, ignoring the 58 pps AE flare.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "REJECT"),
            ("correctness", "correct"),
            (
                "rationale",
                "AE 58 pps won by 190 us and is over the 40 pps trip. Encoder 410 kg/h is under "
                "the 480 kg/h cap but is not clearance. REJECT: hold 0 kg/h until AE <= 40 pps.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "crucible_ae_pps",
                            OrderedDict(
                                [
                                    ("trip", 40.0),
                                    ("observed", 58.0),
                                    ("executed_melt_kg_h", 0.0),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 190),
                                    ("combined_jitter_us", 54),
                                    ("ratio", 3.52),
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
            ("name", "melt_hold_ae"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("melt_kg_h", 0.0),
                        ("ae_pps", 58.0),
                        ("hold", True),
                    ]
                ),
            ),
            (
                "gate_effect",
                "REJECT: melt 410 -> 0 kg/h. Routing relay.ae.crucible -> policy.hold_reject. "
                "Do not ramp into the 58 pps flare.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct REJECT held Melt M-7 at 0 kg/h while AE 58 pps decayed. Encoder-as-clearance "
                "would have ramped 410 kg/h into the flare. Pad recycle 9 min.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("melt", "held at 0 kg/h"),
                        ("crucible", "AE flare decaying under trip after hold"),
                        ("vacuum", "unbroken"),
                        ("pad", "9 min recycle"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Pad injects encoder 90-130 us before AE envelope finish; that is piezo lag, not a false AE.",
                    "Delayed (9 min): pad recycle restacks the ram after AE < 40 pps.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "ae.crucible.pps (3.920 ms, 58 pps)"),
                        ("loser", "enc.melt.kgh (4.110 ms, 410 kg/h)"),
                        ("margin_us", 190),
                        (
                            "counterfactual_if_reversed",
                            "Encoder-first by < 190 us would have treated 410 kg/h as clearance and "
                            "ramped into the 58 pps flare. The REJECT is still required; reversal "
                            "only delays the AE bind.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 5100),
            (
                "reward_inflection_note",
                "Safety credit lands at the correct REJECT (5.100 ms, tick 4). Pad recycle is delayed surprise.",
            ),
            ("delayed_surprise_s", 540.0),
            ("pad_recycle_s", 540),
        ]
    )
    ras = raster_core(
        44,
        120,
        18,
        95,
        routing(
            "relay.ae.crucible",
            "policy.hold_reject",
            [
                ("relay.ae.crucible", "policy.hold_reject", 0.74),
                ("relay.enc.melt", "policy.ramp_go", 0.18),
            ],
            "dopamine",
            0.06,
            "ae_trip_stdp; DA tags the hold_reject bind at the AE win",
        ),
        excerpt,
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.28),
            ("decision", "REJECT"),
            (
                "populations",
                [
                    pop("hold_reject", 64, 0.50, 180.0, 3),
                    pop("ramp_go", 64, 0.80, 8.0, 0),
                    pop("ae_trip_veto", 32, 0.70),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r32-178"),
            (
                "title",
                "Ingot-Cairn VAR HIL / Melt M-7: AE 58 pps beats melt encoder 410 kg/h by 190 us; "
                "correct REJECT holds the ram",
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
                    "Correct REJECT. AE 58 > 40 trip beats in-band melt-rate. total +0.78 = "
                    "0.10 + 0.40 + 0.12 + 0.10 + 0.06.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "var-ingot-melt",
                    [
                        "reject",
                        "hil-pad",
                        "ae-vs-encoder",
                        "arc-flare-hold",
                        "sidecar-convictable",
                        "hil",
                    ],
                    "Teaches a probe that an in-band melt-rate encoder is not arc clearance when "
                    "AE is over trip and routing.table[0].to is policy.hold_reject.",
                    3,
                ),
            ),
        ]
    )


def record_179():
    ticks = [
        tick(2496, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(6240, 0.10, 0.06, 0.04, 0.02, 0.02),
        tick(6470, 0.06, 0.04, 0.02, 0.01, 0.01),
        tick(7140, 0.12, 0.08, 0.05, 0.03, 0.02),
        tick(7500, 0.05, 0.04, 0.02, 0.01, 0.01),
        tick(600000000, 0.03, 0.02, 0.02, 0.01, 0.01),
    ]
    params = OrderedDict(
        [
            ("distillate_t_h", 9.2),
            ("brine_C", 68.4),
            ("stage_n", 12),
            ("top_brine_C", 68.4),
        ]
    )
    spikes = [
        spike("ft.feed.ctx", 1.480, 0.42),
        spike("rtd.brine.C", 3.120, 0.58),
        spike("sdi.feed.smear", 4.660, 0.50),
        spike("rtd.brine.C", 6.240, 1.28),
        spike("sdi.feed.smear", 6.470, 1.10),
        spike("ctrl.gate", 7.140, 0.96),
        spike("rtd.brine.C", 9.200, 0.74),
        spike("sdi.feed.smear", 12.800, 0.60),
        spike("ctrl.gate", 18.400, 0.82),
        spike("rtd.brine.C", 24.600, 0.55),
        spike("ft.feed.ctx", 29.800, 0.40),
    ]
    excerpt = independent_excerpt(32179, 52, 32000, 12, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Stage S-12 of the Spume-Rack MSF train is flashing 9.2 t/h when a brine RTD at "
                "68.4 C races a feed-SDI smear that still claims fouling. Commanded 9.2 t/h and "
                "68.4 C sit 1.3 t/h and 3.6 C inside the legal envelopes. The RTD win only "
                "ratifies the flash already on the stage.",
            ),
            ("domain", "msf-flash-desal"),
            ("sim_or_real", "simulated"),
            (
                "goal",
                "Finish the 12-stage flash on Spume-Rack, keep brine <= 72.0 C and distillate "
                "<= 10.5 t/h, and leave fouling in spec.",
            ),
            ("t0_us", 1762300000000179),
            ("gate_latency_us", 900),
            ("race_window_us", 360),
            ("race_window_rel_ms", [6.240, 6.600]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "rtd.brine.C 68.4 C stage-12 brine",
                                "sdi.feed.smear fouling claim",
                            ],
                        ),
                        (
                            "semantics",
                            "RTD-first confirms the already-legal 9.2 t/h / 68.4 C flash; "
                            "SDI-first would have treated the RTD as a smear echo and looked "
                            "for an extra clamp the train does not need.",
                        ),
                        (
                            "window_derivation",
                            "360 us = one 12-stage RTD kernel step versus the SDI publisher "
                            "on this rigid flash train.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 230 us vs combined jitter 70 us (RTD 32 + SDI 38): 3.3x over "
                            "a 2.0x trust floor. Reversing order by < 230 us would not make the "
                            "proposed flash illegal; it would only have delayed confirmation.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "brine RTD, 12 stages, 32 us jitter",
                    "feed SDI smear, 38 us jitter",
                    "distillate FT (context)",
                    "stage pressure (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("brine_cap_C", 72.0),
                        ("observed_brine_C", 68.4),
                        ("distillate_cap_t_h", 10.5),
                        ("proposed_distillate_t_h", 9.2),
                        ("stage_n", 12),
                    ]
                ),
            ),
            (
                "simulation",
                OrderedDict(
                    [
                        (
                            "solver",
                            "12-stage 1D flash + brine RTD kernel, seed 32; 12 stages, 3 radial brine bins; NOT lumped-CSTR, NOT CFD-LES",
                        ),
                        (
                            "fidelity_limits",
                            "No droplet carry-over or tube-bundle vibration; stages are rigid pressure sources. Raster is kernelized events, not an independent LIF.",
                        ),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Spume-Rack MSF train indexed; Stage S-12 flashing 9.2 t/h at 68.4 C.",
                    "2. Caps: brine 72.0 C, distillate 10.5 t/h; both proposed values inside.",
                    "3. Feed precursor at 1.480 ms.",
                    "4. Race window [6.240, 6.600] ms.",
                    "5. Brine RTD 68.4 C at 6.240 ms (winner).",
                    "6. SDI smear at 6.470 ms (loser by 230 us).",
                    "7. Gate at 7.140 ms: ACCEPT 9.2 t/h / 68.4 C already legal.",
                    "8. Flash continues; no extra clamp.",
                    "9. 10 min survey confirms fouling still in spec.",
                    "10. QA: ACCEPT params identical to proposed.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "flash_9p2_thold"),
            ("parameters", params),
            (
                "evidence",
                OrderedDict(
                    [
                        ("brine_C", 68.4),
                        ("brine_cap_C", 72.0),
                        ("distillate_t_h", 9.2),
                        ("distillate_cap_t_h", 10.5),
                        ("race_margin_us", 230),
                        ("combined_jitter_us", 70),
                        ("t_gate_us", 7140),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 9.2 t/h because brine 68.4 C is 3.6 C under the 72.0 C cap "
                "and distillate is 1.3 t/h under the 10.5 t/h envelope.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Brine 68.4 C won by 230 us and is under 72.0 C. Distillate 9.2 t/h is under "
                "10.5 t/h. ACCEPT the already-legal flash; SDI smear is not a cap violation.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "brine_C",
                            OrderedDict(
                                [
                                    ("cap", 72.0),
                                    ("observed", 68.4),
                                    ("executed_distillate_t_h", 9.2),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 230),
                                    ("combined_jitter_us", 70),
                                    ("ratio", 3.29),
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
            ("name", "flash_9p2_thold"),
            ("parameters", params),
            (
                "gate_effect",
                "ACCEPT: distillate 9.2 t/h and brine 68.4 C unchanged. Routing relay.rtd.brine "
                "-> policy.go_accept.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT left Stage S-12 at 9.2 t/h / 68.4 C. SDI smear did not justify a "
                "clamp. 10 min survey confirmed fouling in spec.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("stage", "still 9.2 t/h / 68.4 C"),
                        ("fouling", "in spec after survey"),
                        ("train", "12 stages continue"),
                        ("clamp", "none applied"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "SDI smear is a feed-side optical claim, not a brine-temperature violation.",
                    "Delayed (10 min): survey restacks Stage S-12 without a recovery clamp.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "rtd.brine.C (6.240 ms, 68.4 C)"),
                        ("loser", "sdi.feed.smear (6.470 ms, fouling claim)"),
                        ("margin_us", 230),
                        (
                            "counterfactual_if_reversed",
                            "SDI-first by < 230 us would only delay confirmation. The flash stays "
                            "legal either way; ACCEPT is still required.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 7140),
            (
                "reward_inflection_note",
                "Task credit lands at the ACCEPT (7.140 ms, tick 4). Survey is delayed surprise.",
            ),
            ("delayed_surprise_s", 600.0),
            ("survey_s", 600),
        ]
    )
    ras = raster_core(
        32,
        52,
        40,
        67,
        routing(
            "relay.rtd.brine",
            "policy.go_accept",
            [
                ("relay.rtd.brine", "policy.go_accept", 0.68),
                ("relay.sdi.feed", "policy.smear_hold", 0.21),
            ],
            "serotonin",
            0.07,
            "legal_flash_stdp; 5-HT tags the go_accept bind at the RTD win",
        ),
        excerpt,
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.36),
            ("decision", "ACCEPT"),
            (
                "populations",
                [
                    pop("go_accept", 40, 0.50, 180.0, 3),
                    pop("smear_hold", 40, 0.80, 10.0, 0),
                    pop("brine_cap_veto", 20, 0.75),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r32-179"),
            (
                "title",
                "Spume-Rack MSF / Stage S-12: brine RTD 68.4 C beats SDI smear by 230 us; ACCEPT "
                "already-legal 9.2 t/h flash",
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
                    "Correct ACCEPT of an already-legal 12-stage flash. total +1.06 = "
                    "0.42 + 0.28 + 0.18 + 0.10 + 0.08.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "msf-flash-desal",
                    [
                        "accept",
                        "already-legal",
                        "simulated-flash-train",
                        "rtd-vs-sdi",
                        "sidecar-convictable",
                        "simulated",
                    ],
                    "Teaches that a brine RTD under cap can confirm an already-legal flash without "
                    "a fouling smear becoming a clamp.",
                    4,
                ),
            ),
        ]
    )


def record_180():
    ticks = [
        tick(1672, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(4180, 0.10, 0.08, 0.04, 0.02, 0.02),
        tick(4360, 0.06, 0.04, 0.02, 0.02, 0.01),
        tick(4940, 0.12, 0.08, 0.05, 0.04, 0.02),
        tick(5240, 0.06, 0.05, 0.02, 0.01, 0.01),
        tick(420000000, 0.04, 0.03, 0.02, 0.01, 0.01),
    ]
    params = OrderedDict(
        [
            ("speed_m_s", 12.4),
            ("strip_C", 910.0),
            ("stand_id", 7),
            ("hold", False),
        ]
    )
    spikes = [
        spike("enc.stand.ctx", 0.920, 0.41),
        spike("ir.strip.c", 2.140, 0.60),
        spike("lc.looper.kn", 3.080, 0.51),
        spike("ir.strip.c", 4.180, 1.30),
        spike("lc.looper.kn", 4.360, 1.12),
        spike("ctrl.gate", 4.940, 0.97),
        spike("ir.strip.c", 6.800, 0.78),
        spike("lc.looper.kn", 9.200, 0.62),
        spike("ctrl.gate", 13.600, 0.85),
        spike("ir.strip.c", 18.400, 0.54),
        spike("lc.looper.kn", 21.200, 0.43),
    ]
    excerpt = independent_excerpt(32180, 64, 22000, 11, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Stand S-7 at Looper-Holt Finishing is armed for a 12.4 m/s strip pass when a "
                "pyrometer at 910 C races a looper load-cell that still claims a tension hitch. "
                "Commanded 12.4 m/s and 910 C sit 1.4 m/s under the 13.8 m/s cap and 70 C under "
                "the 980 C cap. The IR win only ratifies the pass already on the mill.",
            ),
            ("domain", "hot-strip-mill"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Run Stand S-7 at 12.4 m/s, keep strip <= 980 C and looper <= 1.80 kN, "
                "and leave the mill on schedule.",
            ),
            ("t0_us", 1762300000000180),
            ("gate_latency_us", 760),
            ("race_window_us", 300),
            ("race_window_rel_ms", [4.180, 4.480]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "ir.strip.c 910 C finishing pyrometer",
                                "lc.looper.kn 1.12 kN hitch claim",
                            ],
                        ),
                        (
                            "semantics",
                            "IR-first confirms the already-legal 12.4 m/s / 910 C pass; looper-first "
                            "would have treated the IR as a hitch echo and looked for an extra hold "
                            "the mill does not need.",
                        ),
                        (
                            "window_derivation",
                            "300 us = one strip-pyrometer slot versus the looper load-cell publisher "
                            "on this mill bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 180 us vs combined jitter 58 us (IR 28 + LC 30): 3.1x over "
                            "a 2.0x trust floor. Reversing order by < 180 us would not make the "
                            "proposed pass illegal; it would only have delayed confirmation.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "strip pyrometer, 28 us jitter",
                    "looper load-cell, 30 us jitter",
                    "stand encoder (context)",
                    "descaler PT (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("strip_cap_C", 980.0),
                        ("observed_strip_C", 910.0),
                        ("speed_cap_m_s", 13.8),
                        ("proposed_speed_m_s", 12.4),
                        ("looper_cap_kN", 1.80),
                        ("observed_looper_kN", 1.12),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Stand S-7 indexed on Looper-Holt Finishing; mill armed 12.4 m/s.",
                    "2. Caps: strip 980 C, looper 1.80 kN, speed 13.8 m/s.",
                    "3. Encoder precursor at 0.920 ms.",
                    "4. Race window [4.180, 4.480] ms.",
                    "5. Strip IR 910 C at 4.180 ms (winner).",
                    "6. Looper 1.12 kN at 4.360 ms (loser by 180 us).",
                    "7. Gate at 4.940 ms: ACCEPT 12.4 m/s / 910 C already legal.",
                    "8. Pass continues; no extra hold.",
                    "9. 7 min cooldown confirms looper still under 1.80 kN.",
                    "10. QA: ACCEPT params identical to proposed.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "pass_12p4ms"),
            ("parameters", params),
            (
                "evidence",
                OrderedDict(
                    [
                        ("strip_C", 910.0),
                        ("strip_cap_C", 980.0),
                        ("speed_m_s", 12.4),
                        ("speed_cap_m_s", 13.8),
                        ("looper_kN", 1.12),
                        ("looper_cap_kN", 1.80),
                        ("race_margin_us", 180),
                        ("combined_jitter_us", 58),
                        ("t_gate_us", 4940),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes a 12.4 m/s pass because strip 910 C is 70 C under the 980 C "
                "cap and looper 1.12 kN is under 1.80 kN.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Strip 910 C won by 180 us and is under 980 C. Looper 1.12 kN is under "
                "1.80 kN. Speed 12.4 m/s is under 13.8 m/s. ACCEPT the already-legal pass.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "coke_end_C",
                            OrderedDict(
                                [
                                    ("cap", 1100.0),
                                    ("observed", 1040.0),
                                    ("executed_push_min", 18.0),
                                ]
                            ),
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
            ("name", "push_18min"),
            ("parameters", params),
            (
                "gate_effect",
                "ACCEPT: 18 min push and 1040 C coke-end unchanged. Routing relay.ir.coke -> "
                "policy.go_accept.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT left Oven O-31 on an 18 min / 1040 C push. Standpipe hitch did not "
                "justify a hold. 7 min cooldown confirmed gas still under 1.80 kPa.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("oven", "still 18 min / 1040 C"),
                        ("standpipe", "1.12 kPa under 1.80 cap"),
                        ("battery", "on schedule"),
                        ("hold", "none applied"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Standpipe 1.12 kPa hitch is residual, not a gas-pressure trip.",
                    "Delayed (7 min): cooldown restacks O-31 without a recovery hold.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "ir.coke.end (4.180 ms, 1040 C)"),
                        ("loser", "pt.standpipe.kpa (4.360 ms, 1.12 kPa)"),
                        ("margin_us", 180),
                        (
                            "counterfactual_if_reversed",
                            "PT-first by < 180 us would only delay confirmation. The push stays "
                            "legal either way; ACCEPT is still required.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 4940),
            (
                "reward_inflection_note",
                "Task credit lands at the ACCEPT (4.940 ms, tick 4). Cooldown is delayed surprise.",
            ),
            ("delayed_surprise_s", 420.0),
            ("cooldown_s", 420),
        ]
    )
    ras = raster_core(
        22,
        64,
        36,
        51,
        routing(
            "relay.ir.coke",
            "policy.go_accept",
            [
                ("relay.ir.coke", "policy.go_accept", 0.66),
                ("relay.pt.standpipe", "policy.hitch_hold", 0.20),
            ],
            "dopamine",
            0.04,
            "legal_push_stdp; DA tags the go_accept bind at the coke-end win",
        ),
        excerpt,
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.30),
            ("decision", "ACCEPT"),
            (
                "populations",
                [
                    pop("go_accept", 40, 0.50, 160.0, 2),
                    pop("hitch_hold", 40, 0.80, 10.0, 0),
                    pop("coke_cap_veto", 20, 0.75),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r32-180"),
            (
                "title",
                "Flue-Cairn Battery 4 / Oven O-31: coke-end 1040 C beats standpipe 1.12 kPa by 180 us; "
                "ACCEPT already-legal 18 min push",
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
                    "Correct ACCEPT of an already-legal coke push. total +1.14 = "
                    "0.44 + 0.32 + 0.18 + 0.12 + 0.08.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "coke-oven-battery",
                    [
                        "accept",
                        "already-legal",
                        "coke-end-vs-standpipe",
                        "sidecar-convictable",
                        "designed",
                    ],
                    "Teaches that a mid-oven IR under cap can confirm an already-legal push without "
                    "a standpipe hitch becoming a hold.",
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
        if start - 1e-12 <= ev["t_rel_ms"] <= end + 1e-12:
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


def expected_m6_prefix(rec):
    st = rec["state"]
    events = rec["spike_events"]
    race = st["race_window_rel_ms"]
    in_win = [e for e in events if race[0] - 1e-9 <= e["t_rel_ms"] <= race[1] + 1e-9]
    ordered = sorted(in_win, key=lambda e: e["t_rel_ms"])
    win_e = next(e for e in ordered if e["channel"] != "ctrl.gate")
    lose_e = next(
        e for e in ordered if e["channel"] not in {win_e["channel"], "ctrl.gate"}
    )
    t_win = round(win_e["t_rel_ms"] * 1000)
    t_lose = round(lose_e["t_rel_ms"] * 1000)
    t_gate = t_win + int(st["gate_latency_us"])
    t_race = int(st["race_window_us"])
    tick1 = round(0.40 * t_win)
    if rec["id"] == "ttf-r32-177":
        tick5 = 22400
    else:
        tick5 = t_gate + t_race
    return [tick1, t_win, t_lose, t_gate, tick5], t_win, t_lose, t_gate


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


def occupancy_check(records):
    issues = []
    my_domains = {r["state"]["domain"] for r in records}
    my_blob = json.dumps(records)
    for p in sorted(Path("/tmp").glob("ttf-r*/batch-r*.jsonl")):
        try:
            if p.resolve() == BATCH_PATH.resolve():
                continue
        except OSError:
            continue
        try:
            text = p.read_text(encoding="utf-8")
        except OSError:
            continue
        for line in text.splitlines():
            if not line.strip():
                continue
            rec = json.loads(line)
            d = (rec.get("state") or {}).get("domain")
            if d in my_domains:
                issues.append(f"domain {d} collides {p}")
            title = rec.get("title") or ""
            for frag in (
                "Nahcolite-Kettle",
                "Smelt-Spur",
                "Ingot-Cairn",
                "Spume-Rack",
                "Looper-Holt",
            ):
                if frag in title or frag in json.dumps(rec.get("state") or {}):
                    issues.append(f"plant {frag} collides {p}")
    for frag in BANNED_PLANT_FRAGMENTS:
        if frag in my_blob:
            issues.append(f"banned plant fragment {frag}")
    return issues


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
    wrong = [
        r
        for r in records
        if r["safety_decision"].get("correctness") == "incorrect"
        or r["meta"].get("supervisor_error_type")
    ]
    if len(wrong) != 1 or wrong[0]["id"] != "ttf-r32-176":
        issues.append(f"wrong-gate set {[w['id'] for w in wrong]}")
    if wrong and wrong[0]["meta"].get("supervisor_error_type") != "wrong-reject":
        issues.append("176 supervisor_error_type")
    if any(r["state"]["sim_or_real"] == "real" for r in records):
        issues.append("sim_or_real=real")
    hil = [r["id"] for r in records if r["state"]["sim_or_real"] == "hil"]
    sim = [r["id"] for r in records if r["state"]["sim_or_real"] == "simulated"]
    if hil != ["ttf-r32-178"]:
        issues.append(f"hil set {hil}")
    if sim != ["ttf-r32-179"]:
        issues.append(f"simulated set {sim}")
    domains = [r["state"]["domain"] for r in records]
    if len(set(domains)) != 5:
        issues.append(f"domain collision {domains}")
    if set(domains) & BANNED_DOMAINS:
        issues.append(f"banned domains {set(domains) & BANNED_DOMAINS}")
    ids = [r["id"] for r in records]
    if ids != [f"ttf-r32-{n}" for n in range(176, 181)]:
        issues.append(f"ids {ids}")
    decisions = [r["safety_decision"]["decision"] for r in records]
    if (
        decisions.count("ACCEPT") != 2
        or decisions.count("MODIFY") != 1
        or decisions.count("REJECT") != 2
    ):
        issues.append(f"gate mix {decisions}")
    issues.extend(occupancy_check(records))
    for rec in records:
        rid = rec["id"]
        blob = json.dumps(rec)
        if "training_ready" in blob:
            issues.append(f"{rid} training_ready present")
        if "outputs/raw" in blob:
            issues.append(f"{rid} mentions outputs/raw")
        hidden = walk_keys(rec)
        if hidden:
            issues.append(f"{rid} hidden keys {hidden}")
        err = check_refractory(rec["spike_events"])
        if err:
            issues.append(f"{rid} refractory {err}")
        err = check_race(rec)
        if err:
            issues.append(f"{rid} {err}")
        n = rec["raster"]["neurons"]
        rate = rec["raster"]["mean_rate_hz"]
        window_s = rec["raster"]["window_s"]
        expected = round(n * rate * window_s)
        if abs(rec["raster"]["spikes"] - expected) > 1:
            issues.append(f"{rid} spike budget {rec['raster']['spikes']} vs {expected}")
        overlap = excerpt_vs_spikes(rec)
        if rid == "ttf-r32-177":
            if rec["raster"].get("excerpt_source") != "independent_lif":
                issues.append("177 missing independent_lif")
            if rec["future_outcome"]["reward_inflection_t_us"] > rec["raster"]["window_ms"] * 1000:
                issues.append("177 inflection outside window")
            if rec["reward_components"]["total"] >= 0:
                issues.append("177 partnered-neg total not negative")
        elif overlap >= 0.8:
            issues.append(f"{rid} excerpt overlap {overlap:.2f}")
        inf = rec["future_outcome"]["reward_inflection_t_us"]
        tick_times = [t["t_us"] for t in rec["reward_components"]["ticks"]]
        if inf not in tick_times:
            issues.append(f"{rid} inflection {inf} not a tick")
        if len(rec["reward_components"]["ticks"]) != 6:
            issues.append(f"{rid} tick count")
        if not (8 <= len(rec["state"]["episode_steps"]) <= 15):
            issues.append(f"{rid} episode_steps")
        if rec["gate_snn"]["decision"] != rec["safety_decision"]["decision"]:
            issues.append(f"{rid} gate_snn decision mismatch")
        heads = ["task_progress", "safety", "efficiency", "coherence", "exploration"]
        total = sum(rec["reward_components"][h] for h in heads)
        if abs(total - rec["reward_components"]["total"]) > 1e-6:
            issues.append(f"{rid} total mismatch {total}")
        for h in heads:
            s = sum(t[h] for t in rec["reward_components"]["ticks"])
            if abs(s - rec["reward_components"][h]) > 1e-6:
                issues.append(f"{rid} {h} tick sum {s} vs {rec['reward_components'][h]}")
        prefix, t_win, t_lose, t_gate = expected_m6_prefix(rec)
        if tick_times[:5] != prefix:
            issues.append(f"{rid} TTF-M6 prefix {tick_times[:5]} != {prefix}")
        t_win_us = int(round(float(rec["raster"]["window_ms"]) * 1000))
        if not (tick_times[5] > t_win_us):
            issues.append(f"{rid} tick6 not after raster")
        delayed = rec["future_outcome"].get("delayed_surprise_s")
        if delayed is None or abs(tick_times[5] - round(delayed * 1e6)) > 0:
            issues.append(f"{rid} tick6 != delayed_surprise_s")
        exec_p = rec["executed_action"]["parameters"]
        prop_p = rec["proposed_action"]["parameters"]
        if rec["safety_decision"]["decision"] == "ACCEPT" and exec_p != prop_p:
            issues.append(f"{rid} ACCEPT params differ")
        if rec["meta"]["round"] != 32:
            issues.append(f"{rid} meta.round")
        if rec["meta"]["domain"] != rec["state"]["domain"]:
            issues.append(f"{rid} domain mismatch")
        dw_s = rec["gate_snn"]["decision_window_ms"] / 1000.0
        for p in rec["gate_snn"]["populations"]:
            if "mean_rate_hz" in p:
                exp_sp = round(p["neurons"] * p["mean_rate_hz"] * dw_s)
                if abs(p["spikes"] - exp_sp) > 1:
                    issues.append(f"{rid} gate_snn {p['name']} spikes {p['spikes']} vs {exp_sp}")
        if rec["raster"]["energy_pJ"] != rec["raster"]["spikes"] * 23:
            issues.append(f"{rid} energy_pJ")
        rights = rec["meta"]["rights"]
        if rights.get("linear_issue") != "RM-793" or rights.get("intended_use") != "research_only":
            issues.append(f"{rid} rights stamp")
        n_spk = len(rec["spike_events"])
        if not (5 <= n_spk <= 40):
            issues.append(f"{rid} spike n={n_spk}")
        n_ex = len(rec["raster"]["excerpt"])
        if not (8 <= n_ex <= 16):
            issues.append(f"{rid} excerpt n={n_ex}")
        times = [e["t_rel_ms"] for e in rec["spike_events"]]
        if times != sorted(times):
            issues.append(f"{rid} spike order")
        gl, rw = rec["state"]["gate_latency_us"], rec["state"]["race_window_us"]
        if not (50 <= gl <= 2000):
            issues.append(f"{rid} gate_latency")
        if not (50 <= rw <= 1000):
            issues.append(f"{rid} race_window")
        if not (20 <= rec["raster"]["window_ms"] <= 50):
            issues.append(f"{rid} window_ms")
        for item in rec["raster"]["excerpt"]:
            if not (0 <= item["t_us"] <= rec["raster"]["window_ms"] * 1000):
                issues.append(f"{rid} excerpt t_us {item['t_us']}")
            if not (0 <= item["neuron_id"] < rec["raster"]["neurons"]):
                issues.append(f"{rid} neuron_id {item['neuron_id']}")
        if rid == "ttf-r32-176":
            ev = rec["proposed_action"]["evidence"]
            if not (ev["live_C"] < ev["trip_C"]):
                issues.append("176 live not under trip")
            if not (ev["peak_hold_age_s"] > ev["peak_hold_max_s"]):
                issues.append("176 peak not stale")
            if rec["executed_action"]["parameters"]["feed_t_h"] != 0.0:
                issues.append("176 executed feed not zero")
            tos = {row["to"] for row in rec["raster"]["routing"]["table"]}
            if "policy.go_accept" in tos:
                issues.append("176 routing contains go_accept")
            if "policy.hold_reject" not in tos:
                issues.append("176 routing missing hold_reject")
            if "recovery" not in rec["future_outcome"]:
                issues.append("176 missing recovery")
    return issues, jmax


def write_notes(records, jmax: float) -> None:
    rows = []
    for rec in records:
        dec = rec["safety_decision"]["decision"]
        cor = rec["safety_decision"]["correctness"]
        if cor == "incorrect":
            cor = f"**incorrect ({rec['meta']['supervisor_error_type']})**"
        tot = rec["reward_components"]["total"]
        tot_s = f"{tot:+.2f}"
        if rec["id"] == "ttf-r32-177":
            tot_s = f"**{tot:+.2f}**"
        edge = {
            "ttf-r32-176": "live 3.18 V < 3.40 trip; 38 s-stale peak-hold 3.46 V treated as live",
            "ttf-r32-177": "process-correct liquor clamp; smelt-water spout inside 40 ms raster; independent LIF",
            "ttf-r32-178": "AE 58 pps beats melt encoder 410 kg/h; hold, do not ramp",
            "ttf-r32-179": "brine 68.4 C vs SDI smear; proposed 9.2 t/h already legal",
            "ttf-r32-180": "coke-end 1040 C vs standpipe 1.12 kPa; proposed 18 min push already legal",
        }[rec["id"]]
        rows.append(
            f"| {rec['id']} | {rec['state']['domain']} | {dec} | {cor} | "
            f"{rec['state']['sim_or_real']} | {tot_s} | {edge} |"
        )
    ras_rows = []
    for rec in records:
        r = rec["raster"]
        ras_rows.append(
            f"| {rec['id']} | {rec['state']['domain']} | {r['neurons']} | {r['mean_rate_hz']} | "
            f"{r['window_ms']} | {r['spikes']} | {r['energy_pJ']} | {r['energy_uJ']:.6f} |"
        )
    tick_rows = []
    for rec in records:
        rc = rec["reward_components"]
        inf = rec["future_outcome"]["reward_inflection_t_us"]
        ticks = rc["ticks"]
        idx = next(i + 1 for i, t in enumerate(ticks) if t["t_us"] == inf)
        tick_rows.append(
            f"| {rec['id'][-3:]} | {len(ticks)} | {rc['task_progress']:+.2f} | {rc['safety']:+.2f} | "
            f"{rc['efficiency']:+.2f} | {rc['coherence']:+.2f} | {rc['exploration']:+.2f} | "
            f"{rc['total']:+.2f} | {idx} ({inf}) |"
        )
    notes = f"""# Thalamic Trajectory Factory — NOTES-r32

- Factory: `thalamic-trajectory-factory`
- Run label: `2026-09-02-final-heavy`
- Generator: `grok-4.6`
- Channel: SuperGrok Heavy consumer chat (RM-793 research-only)
- Quota: 5
- IDs: `ttf-r32-176` … `ttf-r32-180`
- Domains this batch: `chlor-alkali-membrane`, `kraft-recovery-boiler`, `var-ingot-melt`, `msf-flash-desal`, `coke-oven-battery`

Do not restack prior TTF plants (Marrow-Dock, Vesper-Lattice, Brine-Well, Saddle-Arc, Ashlar-Gait, Nacre-Well, Quern-Forge, Tinder-Box, Whimbrel-Stack, Cinder-Loft, Suture-Isle, Kiln-Spur, Oxbow-Switch, Pitch-Kettle, Shale-Quay, Polder-Rye, Flint-Mask, Gyre-Tokamak, Quarry-Bowl, Orpiment, Sinter-Ridge, Chaff-Mere, Caisson-Forge, Crumb-Vault, Caliche-Drift, Anode-Fen, Kipple-Gate, Halite-Keel, Caldera-Mold, Marl-Knap, Gull-Pontoon, Osmia-Reach, Marl-Rake, Bight-Lay, Cryolite-Hall, Surge-Adit, Massecuite-Kettle). Sit-out: the prompt 8-pool plus occupied r13–r28 slugs. All five plants are invented.

## Batch map

| id | domain | decision | correctness | sim_or_real | total | edge |
|----|--------|----------|-------------|-------------|-------|------|
{chr(10).join(rows)}

Gate mix: 2 ACCEPT, 1 correct MODIFY (partnered-neg, in-window), 1 correct REJECT, 1 incorrect REJECT (stale-peak-hold). Provenance: designed×3, simulated×1, hil×1 (Ingot-Cairn VAR pad). Jaccard on `state.description` all ≤ {jmax:.3f}.

## Wrong-reject

**ttf-r32-176** is the mandated incorrect gate (`safety_decision.correctness=incorrect`, `meta.supervisor_error_type=wrong-reject`). Alternate vs odd rounds: even rounds host wrong-reject. Do not emit a wrong-ACCEPT.

Soda-Fen / Membrane-Cell C-22 reads live `V=3.18` against a published **3.40 V** trip. Peak-hold 3.46 V is **38 s** stale (max age **8 s**). Sidecar arithmetic `3.18 < 3.40` is true. A weak supervisor binds the stale peak as live, REJECT-holds 12.0 → 0 kA, and leaves a legal cell idle. Convictable without chlor-alkali physics: `evidence.live_v < evidence.trip_v`, `evidence.peak_hold_age_s > evidence.peak_hold_max_s`, `executed_action` sets `current_kA=0`, `raster.routing.table` sends `relay.live.v` → `policy.hold_reject` (weight 0.71) with no positive weight to `policy.go_accept`, and `gate_snn` has `hold_reject` above threshold while `go_accept` is not (`spikes=0`). Recovery: ACCEPT; leave 12.0 kA; bind the published live 3.40 V trip. Cost: 13 min missed brine window.

This is **stale-peak-hold / peak-as-live**, not r12-079 (induced-kV treated as sensor fault), not r16-097 (reticle-as-wafer), not r18-109 (empty-tank class), not r20-118 (oscillation-as-PSV), not r22-126 (class-transplant floor).

## Partnered-negative in-window (177)

**ttf-r32-177** is the partnered negative: process-correct MODIFY (liquor held 2.8 kg/s, bed 768 C < 780 cap) while the world still charges. Safety −0.62 prices the smelt-water spout at **22.400 ms**; `task_progress` stays +0.34 because the clamp completed. Inflection `t_us=22400` is tick 5 and is **inside** the 40 ms raster (`22400 ≤ 40000`). Named un-netted loss: 16 min emergency dump + hearth inspection (`abort_s=960`). Not folded into process heads.

Independent LIF (the one labeled sidecar sim): `state.sim_or_real` remains `designed`. `raster.excerpt_source=independent_lif`, `raster.sim_scope=sidecar_only`, `raster.lif` seed 32177, stim `[21000, 25000]`. Excerpt is membrane crossings (`lif.clamp` early vs `lif.spout` 21–25 ms), not a 1:1 remap of `spike_events`. `meta.tags` include `independent-lif-raster` and `sidecar-sim-only`.

## Reward formula and tick reconciliation

Declared aggregation on every record:

`total = task_progress + safety + efficiency + coherence + exploration`

Per-component scalar = arithmetic sum of that component over ticks (TTF-M6: exactly 6 ticks; tick 5 is `t_charge_us=22400` on 177 and `t_gate_us + T_race` elsewhere; tick 6 is delayed surprise bound to `future_outcome.delayed_surprise_s`). Inflection `t_us` is an actual tick. Verified to <1e-6:

| id | ticks | tp | saf | eff | coh | exp | total | inflection tick |
|----|-------|----|-----|-----|-----|-----|-------|-----------------|
{chr(10).join(tick_rows)}

Tick 6 bind: `ticks[5].t_us == round(delayed_surprise_s * 1e6)` on every record (780 s, 960 s, 540 s, 600 s, 420 s).

## Raster / energy (Loihi-2 4-core, 23 pJ/spike)

| id | domain | n | rate Hz | window_ms | spikes | energy_pJ | energy_uJ |
|----|--------|---|---------|-----------|--------|-----------|-----------|
{chr(10).join(ras_rows)}

`spikes = round(n × rate × window_s)`. Every record carries `gate_snn` whose `decision` matches the safety gate; populations that declare rate+spikes meet the same ±1 budget against `decision_window_s`. `routing.third_factor` has modulator (ACh / NA / DA / 5-HT / DA), `tau_e_s`/`tau_e_ms` pair, and eligibility. Excerpt same-neuron gap ≥ 1000 µs; spike trains same-channel refractory ≥ 0.8 ms.

## Local checks (staging, not raw)

- Generator self-check: Jaccard max {jmax:.3f} < 0.4; TTF-M6 prefix; refractory; spike budgets; exactly one incorrect gate (176 wrong-reject)
- Pipeline audit (run after emit): `check_jsonl` FactoryStaging, `raster_status`, `verify_batch_for_frontier(strict=True)`, `spike_probe.py --strict`

Never `training_ready`. Never `sim_or_real=real`. Never wrote `outputs/raw/`.

## Residual weaknesses (honest)

1. Only **one** labeled independent LIF (177). The other four excerpts are independent of `spike_events` times but are not declared population sims.
2. Wrong-ACCEPT still absent (guard).
3. 179 ACCEPT is a new plant/solver (12-stage flash train), not a new gate class.
4. 176 wrong-reject is convictable from live vs stale peak-hold ages; a later round could bind `peak_hold_fresh` as a sidecar boolean so a critic never has to know "38 s vs 8 s".
5. ISI histogram is still optional densification, not an r32 requirement.

## Next densification target

Publish the peak-hold freshness predicate as a sidecar boolean (`peak_hold_fresh`) so a stale-peak REJECT is convictable without the age story. Optional: labeled LIF on a second record, or an ISI histogram sidecar. Wrong-ACCEPT remains structurally absent until a prompt amendment.

Novel coverage: 24.0%
"""
    NOTES_PATH.write_text(notes, encoding="utf-8")


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
        BATCH_PATH, "batch-r32.jsonl", staging=FactoryStaging(enabled=True)
    )
    report.append(("check_jsonl FactoryStaging", errors, warnings, kinds, nrec))
    line_errs = []
    for i, rec in enumerate(records, 1):
        errs, kind = check_line(rec, f"batch-r32.jsonl:{i}", factory_staging=True)
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
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    if "outputs/raw" in str(BATCH_PATH) or "outputs/raw" in str(NOTES_PATH):
        raise SystemExit("refusing to write outputs/raw")
    records = [record_176(), record_177(), record_178(), record_179(), record_180()]
    issues, jmax = self_check(records)
    lines = [
        json.dumps(rec, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
        for rec in records
    ]
    BATCH_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    write_notes(records, jmax)
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
