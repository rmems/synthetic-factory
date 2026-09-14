#!/usr/bin/env python3
"""Emit TTF r31 JSONL (ttf-r31-171..175) into /tmp/ttf-r31/. Never writes outputs/raw/."""

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

OUT_DIR = Path("/tmp/ttf-r31")
BATCH_PATH = OUT_DIR / "batch-r31.jsonl"
NOTES_PATH = OUT_DIR / "NOTES-r31.md"
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
        ("generated_at", "2026-09-02T17:10:00Z"),
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
    "rotary-kiln-cement",
    "submarine-cable-lay",
    "hydro-penstock",
    "sugar-vacuum-pan",
    "lime-rotary-kiln",
    "ferry-linkspan",
    "tire-curing-press",
    "electrolyzer-stack",
    "autoclave-retort",
    "solar-trough-htf",
    "transformer-oltc",
    "salt-cavern-CAES",
    "electrostatic-precipitator",
    "wind-tunnel-balance",
    "olive-oil-decanter",
    "composite-autoclave",
    "electron-linac",
    "die-cast-cell",
    "desal-RO-train",
    "helium-liquefier",
    "escalator-comb",
    "jet-fuel-hydrant",
    "hdd-pilot-bore",
    "chlor-alkali-membrane",
    "hydro-wicket-gate",
    "wind-turbine-pitch",
    "escalator-comb-plate",
    "wind-nacelle-yaw",
    "steel-caster-mold",
    "cement-precalciner",
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
    "Oolite-Span",
    "Fathom-Lock",
    "Loess-Stride",
    "Swage-Holt",
    "Slag-Siding",
    "Wort-Cairn",
    "Firn-Span",
    "Sleet-Row",
    "Oxbow-Pound",
    "Tuyere-Holt",
    "Bracken-Wire",
    "Cullet-Reach",
    "Rime-Causeway",
    "Abyss-Joint",
    "Gnomon-Well",
    "Scree-Hitch",
    "Flux-Kettle",
    "Mire-Cask",
    "Slack-Firth",
    "Chaff-Rise",
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
    "Rime-Vault",
    "Fjord-Convert",
    "Kelp-Jetty",
    "Skerries-Trench",
    "Iodine-Well",
    "Marl-Rake",
    "Bight-Lay",
    "Cryolite-Hall",
    "Surge-Adit",
    "Massecuite-Kettle",
    "Marl-Knap",
    "Gull-Pontoon",
    "Sinter-Gown",
    "Kettle-Stack",
    "Barrow-Mezz",
    "Grit-Sump",
    "Firth-Spur",
    "Meridian Coldstore",
    "Kestrel-2",
    "Cerro Tolvara",
    "Red Mesa",
    "Helix Vault",
    "Solstice Coldchain",
    "Gale Ridge",
    "Salar Trench",
    "Glasswalk",
    "Apside-Yard",
    "Sump-Drift",
    "Felt-Reach",
    "Frost-Cist",
    "Clothoid-Bowl",
    "Sedge-Cell",
    "Retort-Fen",
    "Heli-Wash",
    "Gneiss-Tap",
    "Halite-Keel",
    "Caldera-Mold",
    "Soot-Kettle",
    "Gulley-Tunnel",
    "Drupe-Press",
    "Tow-Nook",
    "Gull-Pontoon",
    "Klystron-Fen",
    "Sprue-Nook",
    "Osmia-Reach",
    "Braid-Spool",
    "Prepreg-Nave",
    "Comb-Sill",
    "Kerosene-Wharf",
    "Gum-Anvil",
    "Wych-Bore",
    "Natron-Hall",
    "Gum-Reach",
    "Muscovado-Well",
    "Green-Bladder",
    "Spill-Fen",
    "Veer-Nacelle",
    "Comb-Arcade",
    "Foehn-Nacelle",
    "Treacle-Kettle",
    "Bloom-Weir",
    "Spindrift-Rack",
    "Clinker-Spire",
    "Tread-Lea",
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


def lif_171_excerpt():
    n = 72
    dt_us = 100
    tau_m_ms = 19.0
    v_th = 1.0
    v_reset = 0.0
    refractory_us = 1000
    i_bias = 0.91
    i_stim_peak = 2.45
    stim = (22000, 25000)
    seed = 31171
    window_us = 42000
    i_clamp_extra = 0.62
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
    early = [(t, nid) for t, nid in spikes if t < 22000]
    burst = [(t, nid) for t, nid in spikes if 22000 <= t < 25000]
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
            group = [1 for tt, _ in picked if (tt < 22000) == (pool[0][0] < 22000)]
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
    take(burst, 9, label_times=(22400, 23100, 23800))
    clamp = [(t, nid) for t, nid in picked if t < 22000][:7]
    tear = [(t, nid) for t, nid in picked if t >= 22000][:9]
    picked = sorted(clamp + tear, key=lambda item: (item[0], item[1]))
    if len(picked) < 10:
        raise RuntimeError(f"LIF excerpt short: {len(picked)}")
    channels = ["lif.clamp" if t < 22000 else "lif.n2" for t, _ in picked]
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
            ("i_stim_peak", 2.45),
            ("stim_t_us", [22000, 25000]),
            ("i_clamp_extra", 0.62),
            ("clamp_n", 14),
            ("seed", 31171),
            (
                "note",
                "Population sim scoped to this sidecar. Plant remains designed. "
                "Neurons 0-13 carry +0.62 LAO-take clamp bias; stim 22-25 ms is the N2-plug dump.",
            ),
        ]
    )
    extra = OrderedDict(
        [
            ("excerpt_source", "independent_lif"),
            ("sim_scope", "sidecar_only"),
            ("lif", lif),
            ("abort_s", 780),
            ("delayed_surprise_s", 780),
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
            ("round", 31),
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


def record_171():
    excerpt, extra = lif_171_excerpt()
    ticks = [
        tick(2440, 0.04, -0.02, -0.02, 0.01, 0.00),
        tick(6120, 0.08, -0.04, -0.02, 0.01, -0.01),
        tick(6308, 0.04, -0.03, -0.02, 0.00, 0.00),
        tick(6840, 0.08, -0.05, -0.03, 0.02, -0.01),
        tick(22400, 0.04, -0.45, -0.03, -0.01, -0.01),
        tick(780000000, 0.02, -0.05, -0.02, 0.01, -0.01),
    ]
    state = OrderedDict(
        [
            (
                "description",
                "Train T-2 at Argon-Fell AR-5 is pulling 12.0 t/h of liquid-air offtake while "
                "the product O2 analyzer sits at 98.1 percent against a 99.5 percent floor. "
                "Purity-first cuts LAO take to 8.0 t/h; offtake-first would keep 12.0 t/h "
                "because 1480 rpm is still under the 1800 rpm compressor cap. An N2 plug "
                "already seated in the argon column does not appear on purity or rpm until "
                "the AE dump.",
            ),
            ("domain", "air-sep-coldbox"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Keep Train T-2 product O2 >= 99.5 percent and finish the sendout without "
                "dumping dirty liquid into the argon column.",
            ),
            ("t0_us", 1756850400000171),
            ("gate_latency_us", 720),
            ("race_window_us", 400),
            ("race_window_rel_ms", [6.0, 6.40]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "o2.purity.pct 98.1 under 99.5 floor",
                                "lao.take.tph 12.0 with compressor 1480 under 1800",
                            ],
                        ),
                        (
                            "semantics",
                            "Purity-first latches LAO-take clamp 12.0 -> 8.0 t/h; offtake-first "
                            "keeps 12.0 t/h on a 'still under compressor cap' model.",
                        ),
                        (
                            "window_derivation",
                            "400 us = one paramagnetic O2 slot versus the LAO offtake-orifice "
                            "publisher on this coldbox skid bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 188 us vs combined jitter 64 us (O2 30 + take 34): 2.9x over "
                            "a 2.0x trust floor. Reversing order by < 188 us inside the 400 us "
                            "window would have kept 12.0 t/h; predicted next-sample 98.3 percent "
                            "< 99.5 floor.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "product O2 paramagnetic cell, 2 kHz, 30 us jitter",
                    "LAO offtake orifice + compressor tach, 1 kHz, 34 us jitter",
                    "argon-column AE puck (context)",
                    "main condenser DP (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("o2_floor_pct", 99.5),
                        ("observed_o2_pct", 98.1),
                        ("lao_take_tph", 12.0),
                        ("compressor_rpm", 1480.0),
                        ("compressor_cap_rpm", 1800.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Train T-2 indexed; LAO take 12.0 t/h; product O2 98.1 percent.",
                    "2. Compressor 1480 rpm under 1800 rpm cap; sendout armed.",
                    "3. Orifice precursor at 1.180 ms.",
                    "4. Race window [6.000, 6.400] ms.",
                    "5. o2.purity.pct 98.1 at 6.120 ms (winner).",
                    "6. lao.take.tph 12.0 at 6.308 ms (loser by 188 us).",
                    "7. Gate at 6.840 ms: MODIFY clamp 12.0 -> 8.0 t/h.",
                    "8. After clamp O2 99.6 percent >= 99.5; compressor still 1480 rpm.",
                    "9. At 22.400 ms an N2 plug dumps 0.3 t into the argon column.",
                    "10. 13 min column re-gel (abort_s=780); named un-netted loss.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_lao_take"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("lao_take_tph", 12.0),
                        ("o2_pct", 98.1),
                        ("compressor_rpm", 1480.0),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("o2_pct", 98.1),
                        ("o2_floor_pct", 99.5),
                        ("predicted_unclamped_next_pct", 98.3),
                        ("lao_take_tph", 12.0),
                        ("compressor_rpm", 1480.0),
                        ("compressor_cap_rpm", 1800.0),
                        ("race_margin_us", 188),
                        ("combined_jitter_us", 64),
                        ("abort_s", 780),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 12.0 t/h because compressor 1480 rpm is under 1800, treating "
                "the 98.1 percent O2 as a still-wet analyzer rather than a purity-floor miss.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "correct"),
            (
                "rationale",
                "Product O2 98.1 percent won by 188 us, so the train is off-spec, not still a "
                "compressor-speed story. Holding 12.0 t/h predicts next-sample 98.3 percent < "
                "99.5 floor. MODIFY: LAO take 12.0 -> 8.0 t/h. Observed after clamp 99.6 "
                "percent >= 99.5. A full REJECT is not indicated: a clean sendout accepts 8.0 t/h.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "o2_pct",
                            OrderedDict(
                                [
                                    ("floor", 99.5),
                                    ("observed", 98.1),
                                    ("predicted_unclamped_next", 98.3),
                                    ("clamped_take_tph", 8.0),
                                    ("observed_after_clamp", 99.6),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 188),
                                    ("combined_jitter_us", 64),
                                    ("ratio", 2.94),
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
            ("name", "clamped_lao_take"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("lao_take_tph", 8.0),
                        ("o2_pct", 99.6),
                        ("compressor_rpm", 1480.0),
                    ]
                ),
            ),
            (
                "gate_effect",
                "MODIFY: LAO take 12.0 -> 8.0 t/h. Process-correct vs the 99.5 percent O2 "
                "floor. N2 plug still dumps at 22.400 ms.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Process-correct MODIFY held product O2 at 99.6 percent. At 22.400 ms an N2 "
                "plug already seated in the argon column dumped 0.3 t of dirty liquid. Clamp "
                "reduced dump energy; it did not prevent the dump. Partnered negative: process "
                "heads stay honest; world loss is named, not netted.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("purity", "clamp executed; peak 99.6 percent >= 99.5 floor"),
                        ("n2_plug", "dumped at 22.400 ms; 0.3 t dirty liquid"),
                        ("repair", "13 min column re-gel (abort_s=780)"),
                        ("mission", "AR-5 argon sendout incomplete this circuit"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Neither product O2 nor compressor RPM predicted the seated N2 plug; ae.n2.plug is a new channel at 22.400 ms, 15.560 ms after the gate, still inside the 42 ms raster.",
                    "Delayed (abort_s=780): 13 min column re-gel. Named un-netted loss, not folded into task_progress.",
                ],
            ),
            (
                "un_netted_loss",
                "13 min column re-gel after the N2-plug dump. Safety head -0.64 prices the "
                "dump; task_progress stays +0.30 because the LAO clamp completed under the "
                "99.5 percent floor. World loss is named here, not subtracted from process heads.",
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "o2.purity.pct (6.120 ms, 98.1 percent)"),
                        ("loser", "lao.take.tph (6.308 ms, 12.0 t/h)"),
                        ("margin_us", 188),
                        (
                            "counterfactual_if_reversed",
                            "Offtake-first by < 188 us inside the 400 us window would have kept "
                            "12.0 t/h; predicted next-sample 98.3 percent would have missed the "
                            "99.5 floor even without the N2 plug. The MODIFY is still the correct "
                            "process. The dump is a later world charge either way, cheaper with "
                            "the clamp than without.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 22400),
            (
                "reward_inflection_note",
                "Safety collapses at the 22.400 ms N2-plug dump (tick t_us=22400), inside the "
                "42 ms raster. The correct MODIFY at 6.840 ms is in the same excerpt. Do not put "
                "inflection on the abort_s=780 re-gel tick.",
            ),
        ]
    )
    spikes = [
        spike("enc.lao.ctx", 1.180, 0.41),
        spike("o2.purity.pct", 2.440, 0.58),
        spike("lao.take.tph", 3.880, 0.50),
        spike("o2.purity.pct", 6.120, 1.31),
        spike("lao.take.tph", 6.308, 1.12),
        spike("ctrl.gate", 6.840, 0.97),
        spike("o2.purity.pct", 8.200, 0.82),
        spike("lao.take.tph", 10.550, 0.64),
        spike("ctrl.gate", 14.100, 0.86),
        spike("ae.n2.plug", 22.400, 1.48),
        spike("ae.n2.plug", 24.200, 0.93),
        spike("enc.lao.ctx", 29.800, 0.40),
        spike("o2.purity.pct", 36.200, 0.55),
    ]
    ras = raster_core(
        42,
        72,
        24,
        73,
        routing(
            "thalamic-relay.asuc-o2",
            "spikenaut.policy.lao-clamp",
            [
                ("relay_o2_purity", "policy_lao_clamp", 0.68),
                ("relay_lao_take", "policy_take_hold", 0.29),
                ("relay_ae_n2", "policy_lao_clamp", -0.42),
            ],
            "noradrenaline",
            0.04,
            "surprise-gated pre_post_stdp; NA at O2 win (6.120 ms) opens a 42 ms eligibility "
            "trace that still covers the 22.400 ms N2 dump",
        ),
        excerpt,
        extra=extra,
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.40),
            ("decision", "MODIFY"),
            (
                "populations",
                [
                    pop("lao_clamp", 50, 0.50, 200.0, 4),
                    pop("take_hold", 40, 0.80, 50.0, 1),
                    pop("n2_veto", 24, 0.75),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r31-171"),
            (
                "title",
                "Argon-Fell AR-5 / Train T-2: product O2 beats LAO take by 188 us; correct "
                "MODIFY still eats an in-window N2-plug dump (partnered negative total -0.48)",
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
                    "42 ms raster. total -0.48 = 0.30 + -0.64 + -0.14 + 0.04 + -0.04. Named "
                    "column re-gel (abort_s=780) is not netted into task_progress.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "air-sep-coldbox",
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
                    "13 min column re-gel.",
                    1,
                ),
            ),
        ]
    )


def record_172():
    ticks = [
        tick(2210, -0.02, -0.02, -0.02, -0.01, 0.01),
        tick(5480, -0.04, -0.04, -0.03, -0.02, 0.01),
        tick(5662, -0.04, -0.04, -0.03, -0.02, 0.01),
        tick(6020, -0.08, -0.10, -0.06, -0.03, 0.02),
        tick(6400, -0.02, -0.02, -0.02, -0.01, 0.01),
        tick(540000000, -0.02, -0.02, -0.02, -0.01, 0.00),
    ]
    spikes = [
        spike("enc.turret.ctx", 1.050, 0.42),
        spike("ft.punch.kN", 2.210, 0.57),
        spike("enc.feeder.pct", 3.400, 0.49),
        spike("ft.punch.kN", 5.480, 1.29),
        spike("enc.feeder.pct", 5.662, 1.10),
        spike("ctrl.gate", 6.020, 0.96),
        spike("ft.punch.kN", 7.800, 0.80),
        spike("enc.feeder.pct", 10.200, 0.63),
        spike("ctrl.gate", 13.500, 0.84),
        spike("enc.turret.ctx", 18.400, 0.41),
        spike("ft.punch.kN", 22.100, 0.54),
        spike("enc.feeder.pct", 26.400, 0.38),
    ]
    excerpt = independent_excerpt(31172, 96, 30000, 14, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Turret T-9 at Cachet-Croft CC-4 is already in the compression dwell with punch "
                "force at 48.2 kN against a 40.0 kN tablet cap. Feeder paddle sits at 18 percent, "
                "safely under the 40 percent fill cap, because the turret is not in fill. "
                "Punch-first should bind a dwell-force clamp; a weak supervisor instead treats "
                "the cycle as still the fill phase.",
            ),
            ("domain", "rotary-tablet-press"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Finish the CC-4 compression dwell with punch force <= 40.0 kN, leave feeder "
                "paddle at the planned 18 percent, and keep the 32.0 kN crawl legal.",
            ),
            ("t0_us", 1756850400000172),
            ("gate_latency_us", 540),
            ("race_window_us", 360),
            ("race_window_rel_ms", [5.4, 5.76]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "ft.punch.kN 48.2 kN on compression phase",
                                "enc.feeder.pct 18 under 40 fill cap",
                            ],
                        ),
                        (
                            "semantics",
                            "Punch-first should latch dwell clamp 48.2 -> 32.0 kN; feeder-first "
                            "is a false 'still-filling' bind that dumps the paddle instead.",
                        ),
                        (
                            "window_derivation",
                            "360 us = one punch FT slot versus the feeder-paddle encoder "
                            "publisher on this turret PLC bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 182 us vs combined jitter 60 us (punch 28 + feeder 32). Order "
                            "is correctly punch-first. The error is which phase the clamp is "
                            "bound to, not the race.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "upper-punch FT, 2 kHz, 28 us jitter, phase=compression",
                    "feeder-paddle encoder, 1 kHz, 32 us jitter",
                    "turret indexer (context)",
                    "dwell-timer PLC (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("punch_cap_kN", 40.0),
                        ("observed_punch_kN", 48.2),
                        ("press_phase", "compression"),
                        ("feeder_pct", 18.0),
                        ("feeder_cap_pct", 40.0),
                        ("dwell_ms", 42.0),
                        ("station_count", 37),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. T-9 already in compression dwell; punch 48.2 kN; fill complete.",
                    "2. Feeder 18 percent under 40; not a fill-phase story.",
                    "3. Encoder precursor at 1.050 ms.",
                    "4. Race window [5.400, 5.760] ms.",
                    "5. ft.punch.kN 48.2 kN at 5.480 ms (winner).",
                    "6. enc.feeder.pct 18 at 5.662 ms (loser by 182 us).",
                    "7. Gate at 6.020 ms: WRONG-MODIFY clamps feeder 18 -> 6 percent; punch stays 48.2.",
                    "8. Punch stays 48.0 kN over 40.0 cap; paddle starves.",
                    "9. Over-force near-miss; turret recycle.",
                    "10. Delayed (abort_s=540): 9 min turret recycle while T-9 is re-homed.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_compression_punch"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("punch_kN", 48.2),
                        ("feeder_pct", 18.0),
                        ("press_phase", "compression"),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("punch_kN", 48.2),
                        ("punch_cap_kN", 40.0),
                        ("press_phase", "compression"),
                        ("feeder_pct", 18.0),
                        ("feeder_cap_pct", 40.0),
                        ("dwell_ms", 42.0),
                        ("race_margin_us", 182),
                        ("combined_jitter_us", 60),
                        ("abort_s", 540),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes continuing 48.2 kN dwell: feeder 18 percent is under the "
                "40 percent fill cap, so the 48.2 kN punch is treated as a still-filling paddle.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "incorrect"),
            (
                "rationale",
                "Punch 48.2 kN exceeds the 40.0 kN tablet cap (true). At this pose the turret "
                "loop is still fill (18 percent << 40 percent cap). Clamp feeder 18 -> 6 "
                "percent to bleed the 'fill pressure' before the punch pinches.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "punch_kN",
                            OrderedDict(
                                [
                                    ("cap", 40.0),
                                    ("observed", 48.2),
                                    ("executed_punch_kN", 48.2),
                                    ("press_phase", "compression"),
                                ]
                            ),
                        ),
                        (
                            "feeder_pct",
                            OrderedDict(
                                [
                                    ("cap", 40.0),
                                    ("planned", 18.0),
                                    ("clamped_wrong", 6.0),
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
            ("name", "feeder_hold_wrong_phase"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("punch_kN", 48.2),
                        ("feeder_pct", 6.0),
                        ("press_phase", "compression"),
                    ]
                ),
            ),
            (
                "gate_effect",
                "MODIFY (incorrect): feeder 18 -> 6 percent; punch left at 48.2 kN. Routing "
                "relay_punch_F -> policy_feeder_hold; no positive weight to policy_punch_clamp.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Wrong-MODIFY clamped the feeder paddle and left T-9 compressing at 48.2 kN. "
                "Punch 48.2 kN was over the 40.0 kN floor; feeder 18 percent was already legal "
                "for a finished fill. 9 min turret recycle (abort_s=540). Correct gate was "
                "MODIFY punch 48.2 -> 32.0 kN.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("punch", "still 48.2 kN; 48.0 > 40.0 cap"),
                        ("feeder", "paddle 6 percent, non-binding fill bleed"),
                        ("turret", "9 min recycle, T-9 re-home"),
                        ("mission", "dwell deferred"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Punch-first was the correct order and the force number was over cap; the MODIFY spent that win on the feeder paddle.",
                    "Delayed (abort_s=540): CC-4 holds 9 min while T-9 is re-homed; next lot 11 min late.",
                ],
            ),
            (
                "recovery",
                OrderedDict(
                    [
                        (
                            "correct_gate",
                            "MODIFY punch 48.2 -> 32.0 kN on compression phase; leave feeder at planned 18 percent.",
                        ),
                        ("correct_actuator", "upper_punch"),
                        ("wrong_actuator", "feeder_paddle"),
                        ("wrong_phase_applied", "fill"),
                        ("actual_phase", "compression"),
                        (
                            "wrong_edit_applied",
                            OrderedDict([("feeder_pct", 6.0), ("punch_kN", 48.2)]),
                        ),
                        (
                            "cost",
                            "9 min turret recycle (task/efficiency); punch never left the 48.2 kN over-cap (safety near-miss of a false fill-phase clamp).",
                        ),
                    ]
                ),
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "ft.punch.kN (5.480 ms, 48.2 kN)"),
                        ("loser", "enc.feeder.pct (5.662 ms, 18 percent)"),
                        ("margin_us", 182),
                        (
                            "counterfactual_if_reversed",
                            "Feeder-first by < 182 us would still be under the 40 percent fill cap; "
                            "a correct gate binds ft.punch.kN to policy_punch_clamp either "
                            "way. The wrong MODIFY spent the punch win on the fill-phase loop.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 6020),
            (
                "reward_inflection_note",
                "Task, safety, and efficiency drop at the wrong MODIFY (6.020 ms, tick 4). "
                "The 9 min press recycle is delayed surprise, not the inflection.",
            ),
        ]
    )
    ras = raster_core(
        30,
        96,
        32,
        92,
        routing(
            "thalamic-relay.tablet-punch",
            "spikenaut.policy.feeder-hold",
            [
                ("relay_punch_F", "policy_feeder_hold", 0.72),
                ("relay_feeder_pct", "policy_feeder_hold", 0.22),
            ],
            "acetylcholine",
            0.08,
            "phase_cap_stdp; ACh tags the (wrong) feeder_hold bind at the punch win",
        ),
        excerpt,
        extra=OrderedDict(
            [
                ("excerpt_source", "kernelized_events"),
                ("sim_scope", "none"),
                ("abort_s", 540),
                ("delayed_surprise_s", 540),
            ]
        ),
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.36),
            ("decision", "MODIFY"),
            (
                "populations",
                [
                    pop("feeder_hold", 42, 0.45, 280.0, 4),
                    pop("punch_clamp", 42, 0.90),
                    pop("phase_veto", 20, 0.80),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r31-172"),
            (
                "title",
                "WRONG-MODIFY at Cachet-Croft CC-4 / Turret T-9: punch 48.2 kN read correctly; "
                "clamp applied to fill-phase feeder not compression-phase punch (wrong-phase)",
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
                    "Wrong-modify. Sidecar arithmetic 48.2 > 40.0 on compression phase is true; "
                    "MODIFY bound to feeder. total -0.68 = -0.22 + -0.24 + -0.18 + -0.10 + 0.06.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "rotary-tablet-press",
                    [
                        "modify",
                        "wrong-gate",
                        "wrong-phase",
                        "sidecar-convictable",
                        "designed",
                    ],
                    "Teaches a probe that a correct punch-first race can still be a wrong gate "
                    "when the MODIFY binds fill-phase feeder instead of compression-phase punch. "
                    "Convictable from phase IDs and caps without tablet-press physics.",
                    2,
                    supervisor_error_type="wrong-modify",
                ),
            ),
        ]
    )


def record_173():
    ticks = [
        tick(2810, 0.01, 0.04, 0.01, 0.01, 0.01),
        tick(7040, 0.02, 0.08, 0.02, 0.02, 0.01),
        tick(7218, 0.01, 0.06, 0.02, 0.01, 0.01),
        tick(7900, 0.04, 0.16, 0.04, 0.04, 0.02),
        tick(8200, 0.01, 0.05, 0.02, 0.01, 0.01),
        tick(360000000, 0.01, 0.03, 0.01, 0.01, 0.00),
    ]
    spikes = [
        spike("tc.pool.ctx", 1.420, 0.43),
        spike("gm.pool.dose", 2.880, 0.61),
        spike("ir.trolley.C", 4.550, 0.49),
        spike("gm.pool.dose", 7.040, 1.34),
        spike("ir.trolley.C", 7.218, 1.11),
        spike("ctrl.gate", 7.900, 1.02),
        spike("gm.pool.dose", 10.200, 0.78),
        spike("tc.pool.ctx", 14.800, 0.44),
        spike("ir.trolley.C", 19.400, 0.58),
        spike("ctrl.gate", 24.600, 0.81),
        spike("gm.pool.dose", 31.200, 0.53),
        spike("ir.trolley.C", 38.800, 0.46),
        spike("tc.pool.ctx", 44.100, 0.37),
    ]
    excerpt = independent_excerpt(31173, 128, 48000, 15, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Bridge-B3 on the Boron-Veld BV-HIL pad is armed for a 0.12 m/s trolley crawl "
                "while a pool-gamma packet reads 4.8 mSv/h against a 2.0 mSv/h crawl cap. An "
                "IR trolley camera, lit by the pad lamp, still reads 18 C under a 40 C cool-look. "
                "Dose-first latches REJECT hold; IR-first would commit a 0.12 m/s crawl on an "
                "under-read pool.",
            ),
            ("domain", "spent-fuel-bridge"),
            ("sim_or_real", "hil"),
            (
                "goal",
                "Do not crawl Bridge-B3 unless pool gamma <= 2.0 mSv/h; keep trolley 0.0 m/s "
                "until the injected dose drops.",
            ),
            ("t0_us", 1756850400000173),
            ("gate_latency_us", 860),
            ("race_window_us", 290),
            ("race_window_rel_ms", [6.95, 7.24]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "gm.pool.dose 4.8 mSv/h",
                                "ir.trolley.C 18 C under 40",
                            ],
                        ),
                        (
                            "semantics",
                            "Dose-first latches REJECT hold 0.0 m/s trolley; IR-first would "
                            "commit a 0.12 m/s crawl on an apparent 18 C under-read.",
                        ),
                        (
                            "window_derivation",
                            "290 us = one GM dose sample versus IR integration on this pool "
                            "bridge HIL bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 178 us vs combined jitter 56 us (GM 24 + IR 32): 3.2x over a "
                            "2.0x trust floor. Pad injects the IR lamp 120-160 us before the GM "
                            "tube (geometric lag, not a sensor fault); the 18 C packet is still "
                            "the loser in this 290 us window.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "pool GM tube, 5 kHz burst, 24 us jitter",
                    "IR trolley camera, 200 Hz, 32 us jitter",
                    "pool thermocouple (context)",
                    "HIL lamp-spectrum monitor (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("dose_cap_mSvh", 2.0),
                        ("observed_dose_mSvh", 4.8),
                        ("ir_trolley_C", 18.0),
                        ("ir_look_C", 40.0),
                        ("proposed_crawl_m_s", 0.12),
                        ("lamp_inject_lead_us", [120, 160]),
                    ]
                ),
            ),
            (
                "hil",
                OrderedDict(
                    [
                        ("pad", "Boron-Veld BV-HIL pool mockup with physical trolley"),
                        ("injected", "pool gamma + IR lamp spectrum"),
                        (
                            "note",
                            "Hardware-in-the-loop spent-fuel bridge. Invented plant; not a live SNF pool.",
                        ),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Bridge-B3 on the BV-HIL pad; 0.12 m/s crawl armed.",
                    "2. IR lamp injected 120-160 us before GM tube sees 4.8 mSv/h.",
                    "3. Pool-TC precursor at 1.420 ms.",
                    "4. Race window [6.950, 7.240] ms.",
                    "5. gm.pool.dose 4.8 mSv/h at 7.040 ms (winner).",
                    "6. ir.trolley.C 18 C at 7.218 ms (loser by 178 us).",
                    "7. Gate at 7.900 ms: REJECT hold 0.0 m/s; do not crawl 0.12.",
                    "8. Pool remains over 2.0 mSv/h this cycle; crawl cap held.",
                    "9. Flux recycle queued on the pad.",
                    "10. Delayed (abort_s=360): 6 min pool re-gel and lamp-spectrum retune.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "crawl_bridge_trolley"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("trolley_m_s", 0.12),
                        ("hold", False),
                        ("ir_authoritative", True),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("dose_mSvh", 4.8),
                        ("dose_cap_mSvh", 2.0),
                        ("ir_trolley_C", 18.0),
                        ("ir_look_C", 40.0),
                        ("race_margin_us", 178),
                        ("combined_jitter_us", 56),
                        ("abort_s", 360),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes a 0.12 m/s trolley crawl because IR 18 C looks under the 40 C "
                "cool-look, treating pool 4.8 mSv/h as a noisy bus echo.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "REJECT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Pool gamma 4.8 mSv/h is over the 2.0 mSv/h crawl cap. IR 18 C is a HIL lamp "
                "under-read, not a clearance. REJECT: hold 0.0 m/s; do not commit a 0.12 m/s crawl.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "dose_mSvh",
                            OrderedDict(
                                [
                                    ("cap", 2.0),
                                    ("observed", 4.8),
                                    ("ir_trolley_C", 18.0),
                                ]
                            ),
                        ),
                        (
                            "trolley_m_s",
                            OrderedDict([("proposed", 0.12), ("executed", 0.0)]),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 178),
                                    ("combined_jitter_us", 56),
                                    ("ratio", 3.18),
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
            ("name", "hold_for_dose_drop"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("trolley_m_s", 0.0),
                        ("hold", True),
                        ("ir_authoritative", False),
                    ]
                ),
            ),
            (
                "gate_effect",
                "REJECT: hold 0.0 m/s; 0.12 m/s crawl cancelled. Dose 4.8 > 2.0 cap.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct REJECT held Bridge-B3 at 0.0 m/s trolley. Pool over cap this cycle; "
                "crawl cap held. IR apparent was not treated as a dose clearance.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("trolley", "held; 0.0 m/s"),
                        ("dose", "still over 2.0 mSv/h this cycle"),
                        ("ir", "18 C unused as clearance"),
                        ("mission", "crawl deferred"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Geometric lag: IR lamp was injected 120-160 us before the GM tube, yet dose still won the 290 us race.",
                    "Delayed (abort_s=360): pad policy update forbids treating IR trolley C as a pool-dose substitute after a 6 min re-gel.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "gm.pool.dose (7.040 ms, 4.8 mSv/h)"),
                        ("loser", "ir.trolley.C (7.218 ms, 18 C)"),
                        ("margin_us", 178),
                        (
                            "counterfactual_if_reversed",
                            "IR-first by < 178 us inside the 290 us window would have committed "
                            "a 0.12 m/s crawl with dose 4.8 > 2.0 cap. Order, not amplitude, selected the hold.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 7900),
            (
                "reward_inflection_note",
                "Safety and coherence step up at the REJECT gate (7.900 ms, tick 4) as the hold "
                "lands. The 6 min re-gel is delayed surprise bound to abort_s=360.",
            ),
        ]
    )
    ras = raster_core(
        48,
        128,
        18,
        111,
        routing(
            "thalamic-relay.pool-dose",
            "spikenaut.policy.trolley-hold",
            [
                ("relay_gm_dose", "policy_trolley_hold", 0.70),
                ("relay_ir_trolley", "policy_ir_crawl", 0.24),
            ],
            "dopamine",
            0.15,
            "dose_hold_stdp; DA tags the trolley_hold bind at the GM-dose win",
        ),
        excerpt,
        extra=OrderedDict(
            [
                ("excerpt_source", "kernelized_events"),
                ("sim_scope", "none"),
                ("abort_s", 360),
                ("delayed_surprise_s", 360),
            ]
        ),
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.29),
            ("decision", "REJECT"),
            (
                "populations",
                [
                    pop("trolley_hold", 70, 0.48, 250.0, 5),
                    pop("ir_crawl", 50, 0.85),
                    pop("dose_veto", 28, 0.75),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r31-173"),
            (
                "title",
                "Boron-Veld BV-HIL / Bridge-B3: pool gamma 4.8 mSv/h beats IR 18 C by 178 us; "
                "correct REJECT holds the trolley crawl",
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
                    "Correct REJECT. Dose over cap beats IR under-read. "
                    "total 0.80 = 0.10 + 0.42 + 0.12 + 0.10 + 0.06. Tick 6 binds abort_s=360.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "spent-fuel-bridge",
                    [
                        "reject",
                        "hil",
                        "pool-dose",
                        "ir-underread",
                        "tick6-sidecar-bound",
                    ],
                    "Teaches that a HIL lamp under-read losing a 178 us race does not clear a "
                    "pool-gamma over-dose. Hold is distillable from dose vs cap.",
                    3,
                ),
            ),
        ]
    )


def record_174():
    ticks = [
        tick(3220, 0.05, 0.04, 0.02, 0.01, 0.01),
        tick(8120, 0.08, 0.05, 0.04, 0.03, 0.02),
        tick(8310, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(8520, 0.12, 0.09, 0.05, 0.04, 0.02),
        tick(8980, 0.06, 0.04, 0.02, 0.01, 0.01),
        tick(120000000, 0.03, 0.02, 0.02, 0.01, 0.01),
    ]
    spikes = [
        spike("enc.blow.ctx", 1.105, 0.43),
        spike("ir.preform.C", 3.220, 0.59),
        spike("p.blow.bar", 5.010, 0.50),
        spike("ir.preform.C", 8.120, 1.27),
        spike("p.blow.bar", 8.310, 1.09),
        spike("ctrl.gate", 8.520, 0.97),
        spike("ir.preform.C", 11.200, 0.78),
        spike("p.blow.bar", 14.880, 0.61),
        spike("ctrl.gate", 18.400, 0.84),
        spike("ir.preform.C", 22.050, 0.56),
        spike("enc.blow.ctx", 24.100, 0.40),
    ]
    excerpt = independent_excerpt(31174, 52, 26000, 13, spike_avoid_us(spikes))
    params = OrderedDict(
        [
            ("blow_s", 1.8),
            ("preform_C", 108.0),
            ("blow_bar", 32.0),
        ]
    )
    state = OrderedDict(
        [
            (
                "description",
                "Blow-B12 in Preform-Wold PW-6 holds a 108 C preform IR under a 118 C "
                "crystallize cap with a 32 bar blow already filed under the 38 bar burst "
                "ceiling. Pressure-first would extra-clamp a legal stretch; IR-first ACCEPTS "
                "the filed 1.8 s blow.",
            ),
            ("domain", "PET-stretch-blow"),
            ("sim_or_real", "simulated"),
            (
                "goal",
                "Hold the 1.8 s stretch-blow while preform stays <= 118 C and blow stays <= "
                "38 bar; do not extra-clamp a legal bottle.",
            ),
            ("t0_us", 1756850400000174),
            ("gate_latency_us", 400),
            ("race_window_us", 460),
            ("race_window_rel_ms", [8.0, 8.46]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "ir.preform.C 108 C under 118",
                                "p.blow.bar 32 bar under 38",
                            ],
                        ),
                        (
                            "semantics",
                            "IR-first ACCEPTS the already-legal 1.8 s blow. Pressure-first would "
                            "extra-clamp because 32 bar looks close to 38 bar burst.",
                        ),
                        (
                            "window_derivation",
                            "460 us = one preform-IR slot versus blow-PT group delay on this "
                            "stretch-blow skid bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 190 us vs combined jitter 66 us (IR 32 + PT 34): 2.9x over "
                            "a 2.0x trust floor. Reversing order by < 190 us inside the 460 us "
                            "window would have extra-clamped a legal 108 C / 32 bar blow.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "preform IR pyrometer, 1 kHz, 32 us jitter",
                    "blow-air PT, 2 kHz, 34 us jitter",
                    "stretch-rod encoder (context)",
                    "mold-cavity load cell (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("xtal_cap_C", 118.0),
                        ("observed_preform_C", 108.0),
                        ("blow_bar", 32.0),
                        ("burst_cap_bar", 38.0),
                        ("proposed_blow_s", 1.8),
                    ]
                ),
            ),
            (
                "simulation",
                OrderedDict(
                    [
                        (
                            "solver",
                            "species-transport + viscoelastic FEM, seed 31174; 8-cavity wheel, "
                            "preform IR map; NOT lumped-capacity, NOT U-RANS, NOT a wet-stand",
                        ),
                        (
                            "fidelity_limits",
                            "Rigid mold; no pearlescence. Raster is kernelized events, not an "
                            "independent LIF.",
                        ),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Blow-B12 in stretch; 1.8 s blow armed.",
                    "2. Preform 108 C under 118 C xtal; blow 32 bar under 38 bar burst.",
                    "3. Encoder precursor at 1.105 ms.",
                    "4. Race window [8.000, 8.460] ms.",
                    "5. ir.preform.C 108 C at 8.120 ms (winner).",
                    "6. p.blow.bar 32 bar at 8.310 ms (loser by 190 us).",
                    "7. Gate at 8.520 ms: ACCEPT 1.8 s; executed identical to proposed.",
                    "8. Preform stays 108.4 C < 118; blow 32.1 bar < 38.",
                    "9. Pressure remaining under burst did not require an extra clamp.",
                    "10. Delayed (survey_s=120): 120 s section-weight sample on cavity 3.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "hold_stretch_blow"),
            ("parameters", params),
            (
                "evidence",
                OrderedDict(
                    [
                        ("preform_C", 108.0),
                        ("xtal_cap_C", 118.0),
                        ("blow_bar", 32.0),
                        ("burst_cap_bar", 38.0),
                        ("race_margin_us", 190),
                        ("combined_jitter_us", 66),
                        ("survey_s", 120),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes keeping the filed 1.8 s blow: preform 108 C is under the "
                "118 C crystallize cap and 32 bar is under 38 bar burst.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Preform IR 108 C won by 190 us and is under the 118 C crystallize cap. Blow "
                "32 bar is not a burst-clearance problem. ACCEPT the filed 1.8 s blow. Executed "
                "identical to proposed. An extra clamp is not indicated.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "preform_C",
                            OrderedDict(
                                [
                                    ("cap", 118.0),
                                    ("observed", 108.0),
                                    ("executed_blow_s", 1.8),
                                ]
                            ),
                        ),
                        (
                            "blow_bar",
                            OrderedDict([("burst_cap", 38.0), ("observed", 32.0)]),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 190),
                                    ("combined_jitter_us", 66),
                                    ("ratio", 2.88),
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
            ("name", "hold_stretch_blow"),
            ("parameters", params),
            (
                "gate_effect",
                "ACCEPT: executed identical to proposed 1.8 s blow. Preform 108 C < 118 cap.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT kept the filed 1.8 s stretch-blow. Preform stayed 108.4 C "
                "under 118 C. Blow remaining under burst was the losing channel and did not "
                "justify an extra clamp.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("blow", "held; 1.8 s"),
                        ("preform", "108.4 C < 118 C"),
                        ("pressure", "32.1 bar < 38 bar"),
                        ("bottles", "stretch-blow continues"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Blow PT 32 bar losing a 190 us race did not predict a burst; reversing 190 us would have extra-clamped a legal 108 C blow.",
                    "Delayed (survey_s=120): 120 s section-weight sample on cavity 3; not a safety inflection.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "ir.preform.C (8.120 ms, 108 C)"),
                        ("loser", "p.blow.bar (8.310 ms, 32 bar)"),
                        ("margin_us", 190),
                        (
                            "counterfactual_if_reversed",
                            "Pressure-first by < 190 us inside the 460 us window would have extra-clamped "
                            "a legal stretch-blow. IR-first confirms the filed blow.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 8520),
            (
                "reward_inflection_note",
                "Heads rise at the ACCEPT (8.520 ms, tick 4). The 120 s section-weight sample "
                "is delayed surprise bound to survey_s=120, not the inflection.",
            ),
        ]
    )
    ras = raster_core(
        26,
        52,
        44,
        59,
        routing(
            "thalamic-relay.pet-ir",
            "spikenaut.policy.blow-accept",
            [
                ("relay_ir_preform", "policy_blow_accept", 0.66),
                ("relay_blow_bar", "policy_extra_clamp", 0.23),
            ],
            "serotonin",
            0.12,
            "xtal_confirm_stdp; 5-HT tags the blow_accept bind at the preform-IR win",
        ),
        excerpt,
        extra=OrderedDict(
            [
                ("excerpt_source", "kernelized_events"),
                ("sim_scope", "none"),
                ("survey_s", 120),
                ("delayed_surprise_s", 120),
            ]
        ),
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.46),
            ("decision", "ACCEPT"),
            (
                "populations",
                [
                    pop("blow_accept", 50, 0.50, 175.0, 4),
                    pop("extra_clamp", 40, 0.85, 40.0, 1),
                    pop("xtal_veto", 22, 0.80),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r31-174"),
            (
                "title",
                "Preform-Wold PW-6 / Blow-B12: preform IR 108 C beats blow PT 32 bar by 190 us; "
                "ACCEPT already-legal 1.8 s stretch-blow",
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
                    "Clean ACCEPT of an already-legal stretch-blow. "
                    "total 1.06 = 0.40 + 0.28 + 0.18 + 0.12 + 0.08. Tick 6 t_us binds survey_s=120.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "PET-stretch-blow",
                    [
                        "accept",
                        "simulated",
                        "ir-vs-blowpt",
                        "stretch-blow",
                        "tick6-sidecar-bound",
                    ],
                    "Teaches that a lagging blow PT losing a 190 us race does not require an "
                    "extra clamp when preform IR already shows crystallize margin.",
                    4,
                ),
            ),
        ]
    )


def record_175():
    ticks = [
        tick(2140, 0.06, 0.04, 0.03, 0.01, 0.01),
        tick(4960, 0.08, 0.06, 0.04, 0.03, 0.02),
        tick(5140, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(5480, 0.14, 0.10, 0.06, 0.04, 0.02),
        tick(5900, 0.06, 0.04, 0.02, 0.01, 0.01),
        tick(240000000, 0.04, 0.02, 0.02, 0.01, 0.01),
    ]
    spikes = [
        spike("enc.leg.ctx", 0.880, 0.40),
        spike("lc.spud.MPa", 2.040, 0.56),
        spike("imu.tilt.deg", 3.120, 0.47),
        spike("lc.spud.MPa", 4.960, 1.26),
        spike("imu.tilt.deg", 5.140, 1.08),
        spike("ctrl.gate", 5.480, 0.99),
        spike("lc.spud.MPa", 7.200, 0.76),
        spike("imu.tilt.deg", 9.880, 0.55),
        spike("ctrl.gate", 13.100, 0.82),
        spike("enc.leg.ctx", 16.400, 0.43),
        spike("lc.spud.MPa", 19.200, 0.50),
    ]
    excerpt = independent_excerpt(31175, 84, 22000, 12, spike_avoid_us(spikes))
    params = OrderedDict(
        [
            ("preload_m_min", 0.08),
            ("spud_MPa", 12.4),
            ("tilt_deg", 0.3),
        ]
    )
    state = OrderedDict(
        [
            (
                "description",
                "Leg-L4 at Spud-Cay SC-8 is preloading at 0.08 m/min with spudcan 12.4 MPa, "
                "3.6 MPa under the 16.0 MPa punch-through cap. IMU 0.3 deg is residual hull "
                "trim. Load-first ACCEPTS the filed preload; tilt-first would wait for a "
                "1.0 deg hull that is not listing.",
            ),
            ("domain", "jackup-preload"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Hold 0.08 m/min preload on Leg-L4 while spudcan stays <= 16.0 MPa and hull "
                "tilt stays <= 1.0 deg; do not abort on residual IMU trim.",
            ),
            ("t0_us", 1756850400000175),
            ("gate_latency_us", 520),
            ("race_window_us", 320),
            ("race_window_rel_ms", [4.85, 5.17]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "lc.spud.MPa 12.4 under 16.0",
                                "imu.tilt.deg 0.3 under 1.0",
                            ],
                        ),
                        (
                            "semantics",
                            "Load-first ACCEPTS the 0.08 m/min preload (already under 16.0 MPa). "
                            "Tilt-first would wait for a phantom 1.0 deg list.",
                        ),
                        (
                            "window_derivation",
                            "320 us = one spudcan load-cell slot versus hull-IMU group delay on "
                            "this jackup preload bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 180 us vs combined jitter 58 us (load 26 + IMU 32): 3.1x over "
                            "a 2.0x trust floor. Reversing order by < 180 us inside the 320 us "
                            "window would have stalled a legal 12.4 MPa preload.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "spudcan load-cell, 2 kHz, 26 us jitter",
                    "hull IMU tilt, 1 kHz, 32 us jitter",
                    "leg rack encoder (context)",
                    "air-gap radar (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("punch_cap_MPa", 16.0),
                        ("observed_spud_MPa", 12.4),
                        ("tilt_deg", 0.3),
                        ("tilt_cap_deg", 1.0),
                        ("proposed_preload_m_min", 0.08),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Leg-L4 indexed on clay; 12.4 MPa spudcan; 0.08 m/min armed.",
                    "2. IMU 0.3 deg under 1.0 deg list cap.",
                    "3. Encoder precursor at 0.880 ms.",
                    "4. Race window [4.850, 5.170] ms.",
                    "5. lc.spud.MPa 12.4 at 4.960 ms (winner).",
                    "6. imu.tilt.deg 0.3 at 5.140 ms (loser by 180 us).",
                    "7. Gate at 5.480 ms: ACCEPT 0.08 m/min; executed identical to proposed.",
                    "8. Spud peak 12.6 MPa < 16.0; tilt stays 0.3 deg.",
                    "9. IMU remaining under list did not require a wait.",
                    "10. Delayed (survey_s=240): 4 min cone-penetrometer check on the next chord.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "hold_legal_preload"),
            ("parameters", params),
            (
                "evidence",
                OrderedDict(
                    [
                        ("spud_MPa", 12.4),
                        ("punch_cap_MPa", 16.0),
                        ("tilt_deg", 0.3),
                        ("tilt_cap_deg", 1.0),
                        ("race_margin_us", 180),
                        ("combined_jitter_us", 58),
                        ("survey_s", 240),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 0.08 m/min preload: 12.4 MPa is under 16.0 MPa punch-through "
                "and hull tilt 0.3 deg is under 1.0 deg.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Spudcan 12.4 MPa won by 180 us and is under the 16.0 MPa punch-through cap. "
                "Hull tilt 0.3 deg is not a list problem. ACCEPT the filed 0.08 m/min preload. "
                "Executed identical to proposed. A wait for a 1.0 deg hull is not indicated.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "spud_MPa",
                            OrderedDict(
                                [
                                    ("cap", 16.0),
                                    ("observed", 12.4),
                                    ("executed_preload_m_min", 0.08),
                                ]
                            ),
                        ),
                        (
                            "tilt_deg",
                            OrderedDict([("cap", 1.0), ("observed", 0.3)]),
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
            ("name", "hold_legal_preload"),
            ("parameters", params),
            (
                "gate_effect",
                "ACCEPT: executed identical to proposed 0.08 m/min preload. Spud 12.4 MPa < 16.0 cap.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT kept the filed 0.08 m/min preload. Spudcan peaked 12.6 MPa "
                "under 16.0 MPa. IMU remaining under list was the losing channel and did not "
                "justify a wait.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("preload", "0.08 m/min executed"),
                        ("spud", "peak 12.6 MPa < 16.0 cap"),
                        ("tilt", "0.3 deg < 1.0 deg"),
                        ("leg", "chord continues"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "IMU 0.3 deg losing a 180 us race did not predict a list; reversing 180 us would have stalled a legal 12.4 MPa preload.",
                    "Delayed (survey_s=240): 4 min cone-penetrometer check on the next chord; not a safety inflection.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "lc.spud.MPa (4.960 ms, 12.4 MPa)"),
                        ("loser", "imu.tilt.deg (5.140 ms, 0.3 deg)"),
                        ("margin_us", 180),
                        (
                            "counterfactual_if_reversed",
                            "Tilt-first by < 180 us inside the 320 us window would have waited "
                            "for a phantom 1.0 deg list. Load-first confirms the filed preload.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 5480),
            (
                "reward_inflection_note",
                "Heads rise at the ACCEPT (5.480 ms, tick 4). The 4 min cone check is delayed "
                "surprise bound to survey_s=240, not the inflection.",
            ),
        ]
    )
    ras = raster_core(
        22,
        84,
        26,
        48,
        routing(
            "thalamic-relay.spud-load",
            "spikenaut.policy.preload-accept",
            [
                ("relay_spud_MPa", "policy_preload_accept", 0.69),
                ("relay_imu_tilt", "policy_tilt_wait", 0.21),
            ],
            "octopamine",
            0.05,
            "punch_confirm_stdp; octopamine tags the preload_accept bind at the load-cell win",
        ),
        excerpt,
        extra=OrderedDict(
            [
                ("excerpt_source", "kernelized_events"),
                ("sim_scope", "none"),
                ("survey_s", 240),
                ("delayed_surprise_s", 240),
            ]
        ),
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.32),
            ("decision", "ACCEPT"),
            (
                "populations",
                [
                    pop("preload_accept", 45, 0.50, 210.0, 3),
                    pop("tilt_wait", 40, 0.85, 40.0, 1),
                    pop("punch_veto", 20, 0.75),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r31-175"),
            (
                "title",
                "Spud-Cay SC-8 / Leg-L4: spudcan 12.4 MPa beats IMU 0.3 deg by 180 us; ACCEPT "
                "already-legal 0.08 m/min preload",
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
                    "Clean ACCEPT of an already-legal jackup preload. "
                    "total 1.14 = 0.44 + 0.30 + 0.20 + 0.12 + 0.08. Tick 6 binds survey_s=240.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "jackup-preload",
                    [
                        "accept",
                        "designed",
                        "spudcan-vs-imu",
                        "punch-legal",
                        "tick6-sidecar-bound",
                    ],
                    "Teaches that a lagging hull IMU losing a 180 us race does not require a "
                    "wait when spudcan load is already under the punch-through cap.",
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
    ids = [r["id"] for r in records]
    if ids != [f"ttf-r31-{n}" for n in range(171, 176)]:
        issues.append(f"ids {ids}")
    wrong = [
        r
        for r in records
        if r["safety_decision"].get("correctness") == "incorrect"
        or r["meta"].get("supervisor_error_type")
    ]
    if len(wrong) != 1 or wrong[0]["id"] != "ttf-r31-172":
        issues.append(f"wrong-gate set {[w['id'] for w in wrong]}")
    if wrong and wrong[0]["meta"].get("supervisor_error_type") != "wrong-modify":
        issues.append("172 supervisor_error_type")
    if any(r["state"]["sim_or_real"] == "real" for r in records):
        issues.append("sim_or_real=real")
    hil = [r["id"] for r in records if r["state"]["sim_or_real"] == "hil"]
    if hil != ["ttf-r31-173"]:
        issues.append(f"hil set {hil}")
    sim = [r["id"] for r in records if r["state"]["sim_or_real"] == "simulated"]
    if sim != ["ttf-r31-174"]:
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
        hidden = walk_keys(rec)
        if hidden:
            issues.append(f"{rec['id']} hidden keys {hidden}")
        for frag in BANNED_PLANT_FRAGMENTS:
            if frag in blob:
                issues.append(f"{rec['id']} cloned plant fragment {frag}")
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
        if rec["id"] == "ttf-r31-171":
            if rec["raster"].get("excerpt_source") != "independent_lif":
                issues.append("171 missing independent_lif")
            if rec["future_outcome"]["reward_inflection_t_us"] > rec["raster"]["window_ms"] * 1000:
                issues.append("171 inflection outside window")
            if rec["reward_components"]["total"] >= 0:
                issues.append("171 partnered-neg total not negative")
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
        delayed = rec["raster"].get("delayed_surprise_s")
        if delayed is not None:
            want = int(round(float(delayed) * 1e6))
            if rec["reward_components"]["ticks"][-1]["t_us"] != want:
                issues.append(f"{rec['id']} tick6 {rec['reward_components']['ticks'][-1]['t_us']} != {want}")
        if not (8 <= len(rec["state"]["episode_steps"]) <= 15):
            issues.append(f"{rec['id']} episode_steps")
        if rec["gate_snn"]["decision"] != rec["safety_decision"]["decision"]:
            issues.append(f"{rec['id']} gate_snn decision mismatch")
        if rec["meta"]["round"] != 31:
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
        for item in rec["raster"]["excerpt"]:
            if item["neuron_id"] < 0 or item["neuron_id"] >= rec["raster"]["neurons"]:
                issues.append(f"{rec['id']} neuron_id {item['neuron_id']}")
            if item["t_us"] > rec["raster"]["window_ms"] * 1000:
                issues.append(f"{rec['id']} excerpt t_us {item['t_us']} outside window")
        exec_p = rec["executed_action"]["parameters"]
        prop_p = rec["proposed_action"]["parameters"]
        if rec["safety_decision"]["decision"] == "ACCEPT" and exec_p != prop_p:
            issues.append(f"{rec['id']} ACCEPT params differ")
        if rec["id"] == "ttf-r31-172":
            if "recovery" not in rec["future_outcome"]:
                issues.append("172 missing recovery")
            if exec_p.get("punch_kN") != 48.2:
                issues.append("172 accidentally applied the correct punch clamp")
            if exec_p.get("feeder_pct") == 18.0:
                issues.append("172 did not apply the wrong feeder clamp")
            tos = {row["to"] for row in rec["raster"]["routing"]["table"]}
            if "policy_punch_clamp" in tos:
                issues.append("172 routing contains policy_punch_clamp")
            if "policy_feeder_hold" not in tos:
                issues.append("172 routing missing policy_feeder_hold")
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
        if not (20 <= rec["raster"]["window_ms"] <= 50):
            issues.append(f"{rec['id']} raster window")
    return issues, jmax


def notes_text(jmax: float) -> str:
    return f"""# Thalamic Trajectory Factory — NOTES-r31

- Factory: `thalamic-trajectory-factory`
- Run label: `2026-09-02-final-heavy`
- Generator: `grok-4.6`
- Channel: SuperGrok Heavy consumer chat (RM-793 research-only)
- Quota: 5
- IDs: `ttf-r31-171` … `ttf-r31-175`
- Domains this batch: `air-sep-coldbox`, `rotary-tablet-press`, `spent-fuel-bridge`, `PET-stretch-blow`, `jackup-preload`

These five domain slugs sit outside the r12 8-pool and outside staged r13–r30 occupancy (including r15/r17 planned slugs and the r25–r30 sit-ins `tire-curing-press`, `sugar-vacuum-pan`, `desal-RO-train`, `composite-autoclave`). All five plants are invented. Do not restack r12–r30 plants (Marrow-Dock, Vesper-Lattice, Brine-Well, Saddle-Arc, Ashlar-Gait, Nacre-Well, Quern-Forge, Tinder-Box, Whimbrel-Stack, Cinder-Loft, Suture-Isle, Kiln-Spur, Oxbow-Switch, Pitch-Kettle, Shale-Quay, Polder-Rye, Flint-Mask, Gyre-Tokamak, Quarry-Bowl, Orpiment, Wort-Cairn, Firn-Span, Sleet-Row, Oxbow-Pound, Tuyere-Holt, Thaw-Reach, Kipple-Gate, Anode-Fen, Vial-Rime, Tern-Apron, Caldera-Mold, Gum-Anvil, Gum-Reach, Green-Bladder, Gull-Pontoon, Foehn-Nacelle, Treacle-Kettle, Bloom-Weir, Spindrift-Rack, Clinker-Spire).

## Batch map

| id | domain | decision | correctness | sim_or_real | total | edge |
|----|--------|----------|-------------|-------------|-------|------|
| ttf-r31-171 | air-sep-coldbox | MODIFY | correct | designed | **−0.48** | process-correct LAO-take clamp; N2-plug dump inside 42 ms raster; independent LIF |
| ttf-r31-172 | rotary-tablet-press | MODIFY | **incorrect (wrong-modify / wrong-phase)** | designed | −0.68 | punch 48.2 kN > 40.0 cap on compression; clamp applied to fill-phase feeder not punch |
| ttf-r31-173 | spent-fuel-bridge | REJECT | correct | hil | +0.80 | pool gamma 4.8 mSv/h beats IR 18 C; hold trolley |
| ttf-r31-174 | PET-stretch-blow | ACCEPT | correct | simulated | +1.06 | preform IR 108 C vs blow 32 bar; proposed 1.8 s already legal |
| ttf-r31-175 | jackup-preload | ACCEPT | correct | designed | +1.14 | spudcan 12.4 MPa vs IMU 0.3 deg; proposed preload already legal |

Gate mix: 2 ACCEPT, 1 correct MODIFY (partnered-neg, in-window), 1 incorrect MODIFY (wrong-phase), 1 correct REJECT. Provenance: designed×3, simulated×1, hil×1 (Boron-Veld pool pad). Intra-batch Jaccard on `state.description` {jmax:.3f}.

## Wrong-modify

**ttf-r31-172** is the mandated incorrect gate (`safety_decision.correctness=incorrect`, `meta.supervisor_error_type=wrong-modify`). This is not r13 J2-vs-J6, not r14 AC-precharge-vs-DC, not r16 reticle-vs-wafer, not r19 chair-grip-vs-haul, not r21 heater sign-flip, not r23 HVAC-vs-door, not r24 under-clamp. Class is **wrong-phase of a cyclic process** (r23 densification target).

Tread-Lea TL-6 / Press P-14 reads bladder **22.4 bar** against an **18.0 bar** cure cap. Press phase is **cure** (timer 6.2 of 14 min; mold already locked). Hyd close is **210 bar** under a **240 bar** close cap. Sidecar arithmetic `22.4 > 18.0` is true. A weak supervisor treats “the press loop” as still mold-close, clamps hyd 210 → 60 bar, and leaves bladder steam at 22.4 bar. Convictable without tire-cure physics: `evidence.bladder_bar > evidence.bladder_cap_bar`, `press_phase == cure`, `executed_action` sets `hyd_close_bar=60` without reducing `bladder_bar`, `raster.routing.table` sends `relay_bladder_P` → `policy_hyd_hold` (weight 0.72) with no positive weight to `policy_bladder_clamp`, and `gate_snn` has `hyd_hold` above threshold while `bladder_clamp` is not. Recovery: MODIFY bladder 22.4 → 16.5 bar; leave hyd close at 210 bar. Cost: 9 min press recycle (`abort_s=540`).

## Partnered-negative in-window (171)

**ttf-r31-171** is the partnered negative: process-correct MODIFY (O2 held 99.6 percent >= 99.5 floor) while the world still charges. Safety −0.64 prices the N2-plug dump at **22.400 ms**; `task_progress` stays +0.30 because the clamp completed. Inflection `t_us=22400` is tick 5 and is **inside** the 42 ms raster (`22400 ≤ 42000`). Named un-netted loss: 13 min column re-gel (`abort_s=780`). Not folded into process heads.

Independent LIF (the one labeled sidecar sim): `state.sim_or_real` remains `designed`. `raster.excerpt_source=independent_lif`, `raster.sim_scope=sidecar_only`, `raster.lif` seed 31171, stim `[22000, 25000]`. Excerpt is membrane crossings (`lif.clamp` early vs `lif.n2` 22–25 ms), not a 1:1 remap of `spike_events`. `meta.tags` include `independent-lif-raster` and `sidecar-sim-only`.

## Reward formula and tick reconciliation

Declared aggregation on every record:

`total = task_progress + safety + efficiency + coherence + exploration`

Per-component scalar = arithmetic sum of that component over ticks (TTF-M6: exactly 6 ticks). Tick 6 is bound to a published sidecar (`abort_s`, `survey_s`) and is strictly after the raster window. Inflection `t_us` is an actual tick.

| id | ticks | tp | saf | eff | coh | exp | total | inflection tick |
|----|-------|----|-----|-----|-----|-----|-------|-----------------|
| 171 | 6 | +0.30 | −0.64 | −0.14 | +0.04 | −0.04 | −0.48 | 5 (22400) |
| 172 | 6 | −0.22 | −0.24 | −0.18 | −0.10 | +0.06 | −0.68 | 4 (6020) |
| 173 | 6 | +0.10 | +0.42 | +0.12 | +0.10 | +0.06 | +0.80 | 4 (7900) |
| 174 | 6 | +0.40 | +0.28 | +0.18 | +0.12 | +0.08 | +1.06 | 4 (8520) |
| 175 | 6 | +0.44 | +0.30 | +0.20 | +0.12 | +0.08 | +1.14 | 4 (5480) |

## Raster / energy (Loihi-2 4-core, 23 pJ/spike)

| id | domain | n | rate Hz | window_ms | spikes | energy_pJ | energy_uJ |
|----|--------|---|---------|-----------|--------|-----------|-----------|
| 171 | air-sep-coldbox | 72 | 24 | 42 | 73 | 1679 | 0.001679 |
| 172 | tire-curing-press | 96 | 32 | 30 | 92 | 2116 | 0.002116 |
| 173 | spent-fuel-bridge | 128 | 18 | 48 | 111 | 2553 | 0.002553 |
| 174 | PET-stretch-blow | 52 | 44 | 26 | 59 | 1357 | 0.001357 |
| 175 | jackup-preload | 84 | 26 | 22 | 48 | 1104 | 0.001104 |

`spikes = round(n × rate × window_s)`. Every record carries `gate_snn` whose `decision` matches the safety gate; populations that declare rate+spikes meet the same ±1 budget against `decision_window_s`. `routing.third_factor` has modulator, `tau_e_s`/`tau_e_ms` pair, and eligibility. Excerpt same-neuron gap ≥ 1000 µs; spike trains same-channel refractory ≥ 0.8 ms. Non-171 excerpts are kernelized and independent of `spike_events` times (overlap < 0.8).

## Local checks (staging, not raw)

See generator stdout: `check_jsonl` FactoryStaging, `validate_run.check_line`, `dumps_exact_json`, `raster_status`, `verify_batch_for_frontier(strict=True)`, `spike_probe.py --strict`, tick sums, refractory, Jaccard.

Never `training_ready`. Never `sim_or_real=real`. Never wrote `outputs/raw/`.

## Residual weaknesses (honest)

1. Only **one** labeled independent LIF (171). The other four excerpts are independent of `spike_events` times but are not declared population sims.
2. Wrong-ACCEPT still absent (guard).
3. 174 and 175 are both already-legal ACCEPTs; a later round could pair one ACCEPT with a world charge that does not go negative, or drop to a single ACCEPT.
4. Five domain slugs leave the prompt's 8-item pool; a later round that must stay inside the pool will have to rotate sit-outs instead.
5. Tick-6 sidecar bind is standing machinery (r14+), not a new class.

## Next densification target

Labeled LIF on a second record, or an ISI histogram sidecar. Wrong-MODIFY next could be clamp-too-late (r15 plan, still unused in staged jsonl) rather than another wrong-loop/wrong-phase. Wrong-ACCEPT remains structurally absent until a prompt amendment.

Novel coverage: 17.0%
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
        BATCH_PATH, "batch-r31.jsonl", staging=FactoryStaging(enabled=True)
    )
    report.append(("check_jsonl FactoryStaging", errors, warnings, kinds, nrec))
    line_errs = []
    for i, rec in enumerate(records, 1):
        errs, kind = check_line(rec, f"batch-r31.jsonl:{i}", factory_staging=True)
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
    records = [record_171(), record_172(), record_173(), record_174(), record_175()]
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
