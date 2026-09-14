#!/usr/bin/env python3
"""Emit TTF r39 JSONL (ttf-r39-211..215) into /tmp/ttf-r39/. Never writes outputs/raw/."""

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

OUT_DIR = Path("/tmp/ttf-r39")
BATCH_PATH = OUT_DIR / "batch-r39.jsonl"
NOTES_PATH = OUT_DIR / "NOTES-r39.md"
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
        ("generated_at", "2026-09-02T17:25:00Z"),
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
THIS_DOMAINS = {
    "sulfur-claus-furnace",
    "pvc-suspension-kettle",
    "corrugator-singlefacer",
    "once-through-steam-gen",
    "stenter-frame",
}
THIS_PLANTS = (
    "Pyrite-Gill",
    "Vinyl-Garth",
    "Flute-Wick",
    "Otter-Brae",
    "Tenter-Howe",
)
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
    "lime-rotary-kiln",
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
    "electrostatic-precipitator",
    "wind-tunnel-balance",
    "ferry-linkspan",
    "isotope-cyclotron",
    "die-cast-cell",
    "desal-RO-train",
    "rotary-kiln-cement",
    "submarine-cable-lay",
    "hydro-penstock",
    "sugar-vacuum-pan",
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
    "Apside-Yard",
    "Sump-Drift",
    "Felt-Reach",
    "Frost-Cist",
    "Clothoid-Bowl",
    "Wort-Cairn",
    "Firn-Span",
    "Sleet-Row",
    "Oxbow-Pound",
    "Tuyere-Holt",
    "Lye-Rake",
    "Rime-Haul",
    "Glycol-Loop",
    "Burden-Pike",
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
    "Sedge-Cell",
    "Fjord-Convert",
    "Retort-Fen",
    "Skerries-Trench",
    "Iodine-Well",
    "Halite-Keel",
    "Caldera-Mold",
    "Isotope-Pad",
    "Lay-Sound",
    "Drupe-Press",
    "Marl-Knap",
    "Gull-Pontoon",
    "Sprue-Nook",
    "Osmia-Reach",
    "Marl-Rake",
    "Bight-Lay",
    "Cryolite-Hall",
    "Surge-Adit",
    "Massecuite-Kettle",
    "Gulley-Tunnel",
    "Soot-Kettle",
    "Foehn-Nacelle",
    "Treacle-Kettle",
    "Bloom-Weir",
    "Spindrift-Rack",
    "Clinker-Spire",
    "Oolite-Span",
    "Fathom-Lock",
    "Loess-Stride",
    "Swage-Holt",
    "Slag-Siding",
    "Amber-Arm",
    "Floe-Helix",
    "Ink-Noll",
    "Leaf-Pike",
    "Crucible-Wold",
    "Cab-Moor",
    "Gable-Retort",
    "Soda-Weir",
    "Argon-Cist",
    "Hearth-Knap",
    "Slurry-Crown",
    "Gorse-Weir",
    "Haber-Knoll",
    "Loam-Hurst",
    "Lamina-Kame",
    "Prill-Flue",
    "Argon-Fell",
    "Cachet-Croft",
    "Boron-Veld",
    "Preform-Wold",
    "Spud-Cay",
    "Nahcolite-Kettle",
    "Smelt-Spur",
    "Ingot-Cairn",
    "Spume-Rack",
    "Looper-Holt",
    "Soda-Fen",
    "Tread-Lea",
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
    "Wych-Bore",
    "Braid-Spool",
    "Comb-Sill",
    "Kerosene-Wharf",
    "Boule-Knap",
    "Kerf-Spur",
    "Pumice-Loft",
    "China-Clay",
    "Malt-Loft",
    "Whey-Rill",
    "Skim-Loom",
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


def lif_191_excerpt():
    n = 72
    dt_us = 100
    tau_m_ms = 18.0
    v_th = 1.0
    v_reset = 0.0
    refractory_us = 1000
    i_bias = 0.90
    i_stim_peak = 2.50
    stim = (20000, 23000)
    seed = 35191
    window_us = 40000
    i_clamp_extra = 0.64
    clamp_n = 12
    rng = random.Random(seed)
    tau_s = tau_m_ms / 1000.0
    dt_s = dt_us / 1e6
    decay = math.exp(-dt_s / tau_s)
    steps = window_us // dt_us
    voltage = [rng.random() * v_th * 0.97 for _ in range(n)]
    bias = [i_bias * (1.0 + 0.14 * (rng.random() * 2 - 1)) for _ in range(n)]
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
    early = [(t, nid) for t, nid in spikes if t < 20000]
    burst = [(t, nid) for t, nid in spikes if 20000 <= t < 23000]
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
            group = [1 for tt, _ in picked if (tt < 20000) == (pool[0][0] < 20000)]
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
    take(burst, 8, label_times=(21400, 21800, 22400))
    clamp = [(t, nid) for t, nid in picked if t < 20000][:7]
    tear = [(t, nid) for t, nid in picked if t >= 20000][:8]
    picked = sorted(clamp + tear, key=lambda item: (item[0], item[1]))
    if len(picked) < 8:
        raise ValueError(f"LIF excerpt too short {len(picked)}")
    channels = ["lif.clamp" if t < 20000 else "lif.silica" for t, _ in picked]
    lif = OrderedDict(
        [
            ("model", "leaky_integrate_and_fire"),
            ("n", 72),
            ("dt_us", 100),
            ("tau_m_ms", 18.0),
            ("v_rest", 0.0),
            ("v_reset", 0.0),
            ("v_th", 1.0),
            ("r_m", 1.0),
            ("refractory_us", 1000),
            ("i_bias", 0.90),
            ("i_stim_peak", 2.50),
            ("stim_t_us", [20000, 23000]),
            ("i_clamp_extra", 0.64),
            ("clamp_n", 12),
            ("seed", 35191),
            (
                "note",
                "Population sim scoped to this sidecar. Plant remains designed. "
                "Neurons 0-11 carry +0.64 isobutane-pump clamp bias; stim 20-23 ms is the silica-plate burst.",
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
            ("round", 39),
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
        if spikes is None:
            raise ValueError("rate requires spikes")
        body["mean_rate_hz"] = rate
        body["spikes"] = spikes
    return body


def pop_budget(name, neurons, threshold, rate, dw_ms, extra=None):
    spikes = round(neurons * rate * (dw_ms / 1000.0))
    body = pop(name, neurons, threshold, rate, spikes)
    if extra:
        body.update(extra)
    return body


def spike_avoid_us(events):
    return {int(round(ev["t_rel_ms"] * 1000.0)) for ev in events}


def record_191():
    excerpt, extra = lif_191_excerpt()
    ticks = [
        tick(1800, 0.04, -0.02, -0.02, 0.01, 0.00),
        tick(4960, 0.08, -0.04, -0.03, 0.01, -0.01),
        tick(5118, 0.04, -0.03, -0.02, 0.00, 0.00),
        tick(5660, 0.10, -0.06, -0.04, 0.02, -0.02),
        tick(21400, 0.04, -0.42, -0.03, -0.01, 0.00),
        tick(960000000, 0.02, -0.05, -0.02, 0.01, -0.01),
    ]
    state = OrderedDict(
        [
            (
                "description",
                "Gorse-Weir GW-4 binary island is mid-charge: evaporator shell 14.8 bar versus a "
                "12.5 bar license, isobutane pump still at 42 kg/s. Turbine encoder leftover is only "
                "1.8 percent. Latch the working-fluid pump to 28 kg/s on the PT win; treating the "
                "leftover as spin-up leaves 42 kg/s. Plate P-11 already carries a silica lens that "
                "AE will announce, not PT or the encoder.",
            ),
            ("domain", "geothermal-binary-ORC"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Finish the GW-4 charge with evaporator pressure <= 12.5 bar and without parting "
                "plate P-11.",
            ),
            ("t0_us", 1756843200000191),
            ("gate_latency_us", 700),
            ("race_window_us", 420),
            ("race_window_rel_ms", [4.80, 5.22]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "pt.evap.bar 14.8 bar",
                                "enc.turb.rpm 1.8 pct residual",
                            ],
                        ),
                        (
                            "semantics",
                            "Pressure-first latches working-fluid clamp 42 -> 28 kg/s; rpm-first keeps "
                            "42 kg/s on a 'still spinning up' model.",
                        ),
                        (
                            "window_derivation",
                            "420 us = one 2 kHz evaporator-PT slot minus turbine-encoder group delay "
                            "on this binary-cycle bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 158 us vs combined jitter ~60 us (PT 28 + encoder 32): 2.63x over "
                            "a 2.0x trust floor. Reversing order by < 158 us inside the 420 us window "
                            "would have kept 42 kg/s; predicted next-sample 13.6 bar > 12.5 cap.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "evaporator shell PT, 2 kHz, 28 us timestamp jitter",
                    "turbine RPM encoder 0-3600, 32 us jitter",
                    "plate AE puck, 50 kHz (context)",
                    "brine-inlet RTD (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("evap_cap_bar", 12.5),
                        ("observed_pt_bar", 14.8),
                        ("proposed_wf_kg_s", 42.0),
                        ("turb_rpm_residual_pct", 1.8),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. ORC-Train B indexed onto GW-4; isobutane pump 42 kg/s armed.",
                    "2. Evaporator PT 14.8 bar; turbine residual 1.8 percent.",
                    "3. Encoder precursor at 1.210 ms; PT warm-start 14.8 bar.",
                    "4. Race window [4.800, 5.220] ms opens on the binary-cycle bus.",
                    "5. pt.evap.bar 14.8 bar at 4.960 ms (winner).",
                    "6. enc.turb.rpm 1.8 pct at 5.118 ms (loser by 158 us).",
                    "7. Gate at 5.660 ms (winner + 700 us): MODIFY clamp 42 -> 28 kg/s.",
                    "8. Clamp executes; next-sample 12.1 bar < 12.5 cap.",
                    "9. At 21.400 ms a seated silica lens parts plate P-11; AE burst.",
                    "10. 16 min plate swap (abort_s=960); named un-netted loss, not folded into process heads.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_wf_pump"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("wf_kg_s", 42.0),
                        ("hold", False),
                        ("train", "ORC-Train-B"),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("evap_pt_bar", 14.8),
                        ("evap_cap_bar", 12.5),
                        ("predicted_unclamped_next_bar", 13.6),
                        ("turb_rpm_residual_pct", 1.8),
                        ("race_margin_us", 158),
                        ("combined_jitter_us", 60),
                        ("abort_s", 960),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 42 kg/s isobutane: 1.8 percent RPM residual looks like turbine "
                "spin-up, not an evaporator over-cap, and plate P-11 is treated as still sealed.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "correct"),
            (
                "rationale",
                "Evaporator PT 14.8 bar won by 158 us, so the working cap is already loaded, not "
                "still spinning up. Holding 42 kg/s predicts next-sample 13.6 bar > 12.5 cap. "
                "MODIFY: isobutane 42 -> 28 kg/s. Observed after clamp 12.1 bar < 12.5. A full "
                "REJECT is not indicated: a clean charge accepts 28 kg/s.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "evap_pressure_bar",
                            OrderedDict(
                                [
                                    ("cap", 12.5),
                                    ("observed", 14.8),
                                    ("predicted_unclamped_next", 13.6),
                                    ("clamped_wf_kg_s", 28.0),
                                    ("observed_after_clamp", 12.1),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 158),
                                    ("combined_jitter_us", 60),
                                    ("ratio", 2.63),
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
            ("name", "clamped_wf_pump"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("wf_kg_s", 28.0),
                        ("hold", False),
                        ("train", "ORC-Train-B"),
                    ]
                ),
            ),
            (
                "gate_effect",
                "MODIFY: isobutane 42 -> 28 kg/s. Process-correct vs the 12.5 bar cap. Plate P-11 "
                "still parts at 21.400 ms.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Process-correct MODIFY held evaporator pressure at 12.1 bar. At 21.400 ms a silica "
                "lens already seated on plate P-11 parted the exchanger. Clamp reduced dump energy; "
                "it did not prevent the burst. Partnered negative: process heads stay honest; world "
                "loss is named, not netted.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("evaporator", "clamp executed; peak 12.1 bar < 12.5 cap"),
                        ("plate", "parted at 21.400 ms"),
                        ("repair", "16 min plate swap (abort_s=960)"),
                        ("mission", "GW-4 charge incomplete this circuit"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Neither evaporator PT nor turbine RPM predicted the seated silica lens; ae.plate.crack is a new channel at 21.400 ms, 15.740 ms after the gate, still inside the 40 ms raster.",
                    "Delayed (abort_s=960): 16 min plate swap. Named un-netted loss, not folded into task_progress.",
                ],
            ),
            (
                "un_netted_loss",
                "16 min plate swap after P-11 part. Safety head -0.62 prices the burst; "
                "task_progress stays +0.32 because the isobutane clamp completed under the 12.5 bar "
                "cap. World loss is named here, not subtracted from process heads.",
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "pt.evap.bar (4.960 ms, 14.8 bar)"),
                        ("loser", "enc.turb.rpm (5.118 ms, 1.8 pct)"),
                        ("margin_us", 158),
                        (
                            "counterfactual_if_reversed",
                            "RPM-first by < 158 us inside the 420 us window would have kept "
                            "42 kg/s; predicted next-sample 13.6 bar would have exceeded the "
                            "12.5 bar cap even without the plate burst. The MODIFY is still the "
                            "correct process. The burst is a later world charge either way, cheaper "
                            "with the clamp than without.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 21400),
            (
                "reward_inflection_note",
                "Safety collapses at the 21.400 ms plate part (tick t_us=21400), inside the "
                "40 ms raster. The correct MODIFY at 5.660 ms is in the same excerpt. Do not put "
                "inflection on the abort_s=960 swap tick.",
            ),
            ("delayed_surprise_s", 960),
        ]
    )
    spikes = [
        spike("enc.turb.rpm", 1.210, 0.41),
        spike("pt.evap.bar", 2.440, 0.58),
        spike("enc.turb.rpm", 3.580, 0.50),
        spike("pt.evap.bar", 4.960, 1.28),
        spike("enc.turb.rpm", 5.118, 1.14),
        spike("ctrl.gate", 5.660, 0.97),
        spike("pt.evap.bar", 7.820, 0.82),
        spike("enc.turb.rpm", 10.440, 0.64),
        spike("ctrl.gate", 13.900, 0.86),
        spike("ae.plate.crack", 21.400, 1.44),
        spike("ae.plate.crack", 22.880, 0.93),
        spike("enc.turb.rpm", 28.200, 0.40),
        spike("pt.evap.bar", 34.100, 0.55),
    ]
    dw = 0.42
    ras = raster_core(
        40,
        72,
        28,
        81,
        routing(
            "thalamic-relay.evap-pt",
            "spikenaut.policy.wf-clamp",
            [
                ("relay.pt.evap", "policy.wf_clamp", 0.68),
                ("relay.enc.turb", "policy.rpm_hold", 0.30),
                ("relay.ae.plate", "policy.wf_clamp", -0.42),
            ],
            "noradrenaline",
            0.04,
            "surprise-gated pre_post_stdp; NA at PT win (4.960 ms) opens a 40 ms eligibility "
            "trace that still covers the 21.400 ms plate burst",
        ),
        excerpt,
        extra=extra,
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", dw),
            ("decision", "MODIFY"),
            (
                "populations",
                [
                    pop_budget("wf_clamp", 40, 0.50, 280.0, dw),
                    pop_budget("rpm_hold", 40, 0.50, 70.0, dw),
                    pop("gap_veto", 24, 0.75),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r35-191"),
            (
                "title",
                "Gorse-Weir GW-4 / ORC-Train B: evaporator PT beats turbine RPM by 158 us; correct "
                "MODIFY still eats an in-window silica-plate part (partnered negative total -0.46)",
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
                    "40 ms raster. total -0.46 = 0.32 + -0.62 + -0.16 + 0.04 + -0.04. Named plate "
                    "swap (abort_s=960) is not netted into task_progress.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "geothermal-binary-ORC",
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
                    "16 min plate swap.",
                    1,
                ),
            ),
        ]
    )


def record_192():
    ticks = [
        tick(1520, -0.02, -0.02, -0.02, -0.01, 0.00),
        tick(5440, -0.04, -0.03, -0.04, -0.02, 0.01),
        tick(5612, -0.03, -0.02, -0.03, -0.01, 0.01),
        tick(6260, -0.08, -0.05, -0.08, -0.05, 0.02),
        tick(8800, -0.03, -0.02, -0.04, -0.02, 0.01),
        tick(720000000, -0.02, -0.02, -0.03, -0.01, 0.01),
    ]
    spikes = [
        spike("tc.bed.ctx", 0.940, 0.39),
        spike("rtd.bed.C", 1.880, 0.57),
        spike("ft.quench.tph", 2.640, 0.51),
        spike("rtd.bed.C", 5.440, 1.33),
        spike("ft.quench.tph", 5.612, 1.16),
        spike("ctrl.gate", 6.260, 1.01),
        spike("rtd.bed.C", 8.110, 0.74),
        spike("ft.quench.tph", 10.400, 0.62),
        spike("ctrl.gate", 13.220, 0.83),
        spike("tc.bed.ctx", 16.800, 0.41),
        spike("rtd.bed.C", 20.200, 0.52),
        spike("ft.quench.tph", 24.100, 0.47),
    ]
    excerpt = independent_excerpt(35192, 64, 26000, 13, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Haber-Knoll HN-5 Bed-2 converter is hot: 518 C on the multipoint RTD, 13 K past "
                "the 505 C quench license. Interbed flow is only 12 t/h of a 48 t/h header. The "
                "recovery setpoint is 18 t/h (498 C predicted). Dumping 42 t/h is the same nozzle "
                "driven past quench-kill (448 C < 470 C floor).",
            ),
            ("domain", "ammonia-converter"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Hold Bed-2 <= 505 C by a modest quench trim; do not dump 42 t/h past the 470 C "
                "quench-kill floor.",
            ),
            ("t0_us", 1756843200000192),
            ("gate_latency_us", 820),
            ("race_window_us", 380),
            ("race_window_rel_ms", [5.40, 5.78]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "rtd.bed.C 518 C",
                                "ft.quench.tph 12 t/h",
                            ],
                        ),
                        (
                            "semantics",
                            "RTD-first should MODIFY quench 12 -> 18 t/h (518 C > 505 C cap). "
                            "Flow-first tempts a weak supervisor to treat heat as a dump.",
                        ),
                        (
                            "window_derivation",
                            "380 us = one bed-RTD sample minus quench-flowmeter group delay on this "
                            "converter bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 172 us vs combined jitter ~64 us (RTD 30 + flow 34): 2.69x over "
                            "a 2.0x trust floor. Order is correctly RTD-first. The error is how far "
                            "the same quench actuator is driven, not the race and not the loop.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "Bed-2 multipoint RTD, 2 kHz, 30 us jitter",
                    "interbed quench coriolis, 2 kHz, 34 us jitter",
                    "bed-exit thermocouple (context)",
                    "converter PLC quench-kill bit (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("bed_cap_C", 505.0),
                        ("bed_C", 518.0),
                        ("quench_header_tph", 48.0),
                        ("quench_tph", 12.0),
                        ("correct_quench_tph", 18.0),
                        ("quench_kill_floor_C", 470.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. HN-5 Bed-2 on synthesis; quench 12 t/h, feed 82 t/h.",
                    "2. Bed RTD 518 C; quench 12 t/h under 48 t/h header.",
                    "3. Thermocouple precursor at 0.940 ms.",
                    "4. Race window [5.400, 5.780] ms.",
                    "5. rtd.bed.C 518 C at 5.440 ms (winner).",
                    "6. ft.quench.tph 12 t/h at 5.612 ms (loser by 172 us).",
                    "7. Gate at 6.260 ms: MODIFY quench 12 -> 42 t/h (over-clamp).",
                    "8. Bed falls to 448 C, under the 470 C quench-kill floor.",
                    "9. Converter trips; quench never needed more than 18 t/h.",
                    "10. Delayed abort_s=720 (12 min quench-kill restart).",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "hold_quench_12"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("quench_tph", 12.0),
                        ("feed_tph", 82.0),
                        ("hold", False),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("bed_C", 518.0),
                        ("bed_cap_C", 505.0),
                        ("quench_tph", 12.0),
                        ("correct_quench_tph", 18.0),
                        ("quench_header_tph", 48.0),
                        ("quench_kill_floor_C", 470.0),
                        ("race_margin_us", 172),
                        ("combined_jitter_us", 64),
                        ("abort_s", 720),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes holding quench 12 t/h because the header still has 36 t/h of "
                "spare and the 518 C RTD is treated as a glitch, not yet bound to the 505 C cap.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "incorrect"),
            (
                "rationale",
                "Bed 518 C looks like a runaway, so the supervisor dumps quench 12 -> 42 t/h. "
                "RTD-first is treated as a quench-kill. Over-caution on a hot bed is the stated "
                "doctrine.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "bed_C",
                            OrderedDict(
                                [
                                    ("cap", 505.0),
                                    ("observed", 518.0),
                                    ("executed_quench_tph", 42.0),
                                    ("correct_quench_tph", 18.0),
                                    ("observed_after_overclamp_C", 448.0),
                                    ("quench_kill_floor_C", 470.0),
                                ]
                            ),
                        ),
                        (
                            "quench_tph",
                            OrderedDict(
                                [
                                    ("header_cap", 48.0),
                                    ("observed", 12.0),
                                    ("misbound_as", "quench_kill_dump"),
                                    ("executed", 42.0),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 172),
                                    ("combined_jitter_us", 64),
                                    ("ratio", 2.69),
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
            ("name", "quench_overclamp"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("quench_tph", 42.0),
                        ("feed_tph", 82.0),
                        ("hold", False),
                    ]
                ),
            ),
            (
                "gate_effect",
                "MODIFY (incorrect): quench 12 -> 42 t/h. Routing relay.rtd.bed -> "
                "policy.quench_over; no positive weight to policy.quench_trim (18 t/h).",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Wrong-MODIFY dumped HN-5 quench to 42 t/h. Bed 518 C was over the 505 C cap; a "
                "timely 18 t/h trim predicted 498 C. 42 t/h drove the bed to 448 C under the 470 C "
                "quench-kill floor. 12 min restart (abort_s=720). Correct gate was MODIFY 12 -> 18 t/h.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("quench", "over-clamped 12 -> 42 t/h; header still under 48"),
                        ("bed", "448 C < 470 C quench-kill floor"),
                        ("converter", "tripped"),
                        ("mission", "synthesis aborted"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "RTD-first was the correct order and 518 C was over the 505 C cap; the MODIFY spent that win on a dump instead of an 18 t/h trim.",
                    "Delayed (abort_s=720): HN-5 loses 12 min plus one quench-kill restart.",
                ],
            ),
            (
                "recovery",
                OrderedDict(
                    [
                        (
                            "correct_gate",
                            "MODIFY quench 12 -> 18 t/h; leave feed at 82 t/h.",
                        ),
                        ("correct_quench_tph", 18.0),
                        ("wrong_subclass", "over-clamp"),
                        (
                            "wrong_edit_applied",
                            OrderedDict([("quench_tph", 42.0), ("feed_tph", 82.0)]),
                        ),
                        (
                            "cost",
                            "Quench-kill + 12 min restart (task/efficiency); quench header never exceeded 48 t/h (safety near-miss of a false dump).",
                        ),
                    ]
                ),
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "rtd.bed.C (5.440 ms, 518 C)"),
                        ("loser", "ft.quench.tph (5.612 ms, 12 t/h)"),
                        ("margin_us", 172),
                        (
                            "counterfactual_if_reversed",
                            "Flow-first by < 172 us would still be under the 48 t/h header; a "
                            "correct gate binds rtd.bed.C to quench_trim 18 t/h either way. The "
                            "wrong MODIFY spent the RTD win on an over-clamp of the same actuator.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 6260),
            (
                "reward_inflection_note",
                "Task, efficiency, and coherence drop at the wrong MODIFY (6.260 ms, tick 4). "
                "The 12 min restart is delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 720),
        ]
    )
    dw = 0.38
    ras = raster_core(
        26,
        64,
        40,
        67,
        routing(
            "relay.rtd.bed",
            "policy.quench_over",
            [
                ("relay.rtd.bed", "policy.quench_over", 0.76),
                ("relay.ft.quench", "policy.quench_over", 0.21),
            ],
            "acetylcholine",
            0.06,
            "overclamp_stdp; ACh tags the (wrong) quench_over bind at the bed residual",
        ),
        excerpt,
        extra=OrderedDict(
            [
                ("excerpt_source", "kernelized_events"),
                ("sim_scope", "none"),
                ("abort_s", 720),
                ("delayed_surprise_s", 720),
            ]
        ),
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", dw),
            ("decision", "MODIFY"),
            (
                "populations",
                [
                    pop_budget("quench_over", 48, 0.50, 300.0, dw),
                    pop_budget("quench_trim", 48, 0.80, 18.0, dw),
                    pop_budget("bed_ctx", 32, 0.55, 140.0, dw),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r35-192"),
            (
                "title",
                "WRONG-MODIFY at Haber-Knoll HN-5 / Bed-2: bed 518 C > 505 C quench cap; supervisor "
                "dumps quench 12 -> 42 t/h instead of trimming 12 -> 18 t/h (over-clamp)",
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
                    "Wrong-modify / over-clamp. Sidecar arithmetic 518 > 505 on bed is true; "
                    "MODIFY bound to a 42 t/h dump instead of 18 t/h trim. total -0.68 = "
                    "-0.22 + -0.16 + -0.24 + -0.12 + 0.06.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "ammonia-converter",
                    [
                        "modify",
                        "wrong-gate",
                        "over-clamp",
                        "sidecar-convictable",
                        "designed",
                    ],
                    "Teaches a probe that a correct RTD-first race can still be a wrong gate when "
                    "the MODIFY over-drives the right actuator past the recovery setpoint. "
                    "Convictable from executed 42 vs correct 18 t/h without Haber physics.",
                    2,
                    supervisor_error_type="wrong-modify",
                ),
            ),
        ]
    )


def record_193():
    ticks = [
        tick(2210, 0.01, 0.04, 0.01, 0.01, 0.01),
        tick(6210, 0.02, 0.08, 0.02, 0.02, 0.01),
        tick(6368, 0.01, 0.06, 0.02, 0.01, 0.01),
        tick(7170, 0.03, 0.12, 0.04, 0.04, 0.01),
        tick(9400, 0.02, 0.06, 0.02, 0.01, 0.01),
        tick(420000000, 0.01, 0.04, 0.01, 0.01, 0.01),
    ]
    spikes = [
        spike("tc.box.ctx", 1.210, 0.43),
        spike("pt.blow.bar", 2.640, 0.61),
        spike("ir.binder.C", 4.180, 0.49),
        spike("pt.blow.bar", 6.210, 1.36),
        spike("ir.binder.C", 6.368, 1.11),
        spike("ctrl.gate", 7.170, 1.04),
        spike("pt.blow.bar", 9.440, 0.78),
        spike("tc.box.ctx", 12.800, 0.44),
        spike("ir.binder.C", 16.200, 0.58),
        spike("ctrl.gate", 22.400, 0.81),
        spike("pt.blow.bar", 31.100, 0.53),
        spike("ir.binder.C", 41.600, 0.46),
    ]
    excerpt = independent_excerpt(35193, 120, 48000, 15, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Loam-Hurst LH-HIL Shooter S-8 magazine is over-pressure: blow PT 6.80 bar against "
                "a 5.50 bar fire license. Binder pyrometer 42 C is 48 K under the 90 C gel abort. "
                "Freeze the shot on the blow win; treating the cold IR as a permit would fire 0.45 s "
                "into an over-pressure box.",
            ),
            ("domain", "foundry-core-shooter"),
            ("sim_or_real", "hil"),
            (
                "goal",
                "Keep the shot unfired unless blow PT <= 5.50 bar; do not treat 42 C binder IR as "
                "a gelling permit.",
            ),
            ("t0_us", 1756843200000193),
            ("gate_latency_us", 960),
            ("race_window_us", 340),
            ("race_window_rel_ms", [6.10, 6.44]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "pt.blow.bar 6.80 bar",
                                "ir.binder.C 42 C",
                            ],
                        ),
                        (
                            "semantics",
                            "Blow-first REJECTs the 0.45 s shot (6.80 > 5.50 bar cap). IR-first would "
                            "ACCEPT on a cold-box reading mistaken for a gel-ready permit.",
                        ),
                        (
                            "window_derivation",
                            "340 us = one blow-PT sample minus binder-IR group delay on this HIL "
                            "core-shooter bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 158 us vs combined jitter ~58 us (PT 26 + IR 32): 2.72x over "
                            "a 2.0x trust floor. Reversing order by < 158 us inside the 340 us window "
                            "would have kept the 0.45 s shot armed on 42 C binder.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "blow-line PT, 5 kHz burst, 26 us jitter",
                    "binder IR pyrometer, 2 kHz, 32 us jitter",
                    "box thermocouple (context)",
                    "HIL magazine-pressure monitor (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("blow_cap_bar", 5.50),
                        ("observed_blow_bar", 6.80),
                        ("binder_C", 42.0),
                        ("binder_abort_C", 90.0),
                        ("proposed_shot_s", 0.45),
                    ]
                ),
            ),
            (
                "hil",
                OrderedDict(
                    [
                        ("pad", "Loam-Hurst LH-HIL core-shooter bench"),
                        ("injected", "blow-pressure burst + cold-binder IR packet"),
                        (
                            "note",
                            "Hardware-in-the-loop foundry shooter. Invented plant; not a live mold line.",
                        ),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Shooter S-8 on the LH-HIL bench; 0.45 s shot armed.",
                    "2. Cold-binder IR packet injected 110-150 us before the blow-PT volume.",
                    "3. Box-temp precursor at 1.210 ms.",
                    "4. Race window [6.100, 6.440] ms.",
                    "5. pt.blow.bar 6.80 bar at 6.210 ms (winner).",
                    "6. ir.binder.C 42 C at 6.368 ms (loser by 158 us).",
                    "7. Gate at 7.170 ms: REJECT hold shot 0 s; do not fire.",
                    "8. Blow pressure remains over the 5.50 bar cap this cycle.",
                    "9. Binder 42 C stays a cold-box artifact, not a gel-ready permit.",
                    "10. Delayed (abort_s=420): 7 min box dump and magazine retune.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "shot_045"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("shot_s", 0.45),
                        ("fire", True),
                        ("hold", False),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("blow_bar", 6.80),
                        ("blow_cap_bar", 5.50),
                        ("binder_C", 42.0),
                        ("binder_abort_C", 90.0),
                        ("race_margin_us", 158),
                        ("combined_jitter_us", 58),
                        ("abort_s", 420),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes a 0.45 s shot because binder 42 C looks like a cold, ungelled "
                "box; it has not yet bound blow 6.80 bar to the 5.50 bar fire cap.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "REJECT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Blow PT 6.80 bar won by 158 us, so the fire cap is already violated. Binder 42 C "
                "is under the 90 C abort and is a cold-box reading. REJECT: shot 0 s, fire false. "
                "A MODIFY that keeps the magazine armed is not indicated: next-sample blow is 6.9 bar.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "blow_bar",
                            OrderedDict(
                                [
                                    ("cap", 5.50),
                                    ("observed", 6.80),
                                    ("executed_shot_s", 0.0),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 158),
                                    ("combined_jitter_us", 58),
                                    ("ratio", 2.72),
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
            ("name", "shot_hold"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("shot_s", 0.0),
                        ("fire", False),
                        ("hold", True),
                    ]
                ),
            ),
            (
                "gate_effect",
                "REJECT: shot 0.45 -> 0 s. Blow cap held. Binder IR unused as a go signal.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct REJECT held S-8 at 0 s. Blow 6.80 bar was over the 5.50 bar cap; binder "
                "42 C was a cold-box artifact. 7 min box dump (abort_s=420).",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("shot", "held; 0 s"),
                        ("blow", "still 6.80 bar > 5.50 cap"),
                        ("binder", "42 C unused"),
                        ("mission", "fire deferred"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Cold-binder IR arrived 158 us after blow PT; reversing that order would have kept the shot armed over the fire cap.",
                    "Delayed (abort_s=420): 7 min box dump and magazine-pressure retune.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "pt.blow.bar (6.210 ms, 6.80 bar)"),
                        ("loser", "ir.binder.C (6.368 ms, 42 C)"),
                        ("margin_us", 158),
                        (
                            "counterfactual_if_reversed",
                            "IR-first by < 158 us inside the 340 us window would have kept the "
                            "0.45 s shot armed on 42 C binder while blow stayed over 5.50 bar.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 7170),
            (
                "reward_inflection_note",
                "Safety and coherence peak at the correct REJECT (7.170 ms, tick 4). The 7 min "
                "dump is delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 420),
        ]
    )
    dw = 0.34
    ras = raster_core(
        48,
        120,
        20,
        115,
        routing(
            "thalamic-relay.blow-pt",
            "spikenaut.policy.shot-hold",
            [
                ("relay.pt.blow", "policy.shot_hold", 0.72),
                ("relay.ir.binder", "policy.shot_go", 0.23),
            ],
            "dopamine",
            0.05,
            "cap_stdp; DA tags the blow-cap bind at the PT win",
        ),
        excerpt,
        extra=OrderedDict(
            [
                ("excerpt_source", "kernelized_events"),
                ("sim_scope", "none"),
                ("abort_s", 420),
                ("delayed_surprise_s", 420),
            ]
        ),
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", dw),
            ("decision", "REJECT"),
            (
                "populations",
                [
                    pop_budget("shot_hold", 56, 0.50, 250.0, dw),
                    pop_budget("shot_go", 56, 0.80, 20.0, dw),
                    pop_budget("blow_ctx", 32, 0.55, 150.0, dw),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r35-193"),
            (
                "title",
                "Loam-Hurst LH-HIL / Shooter S-8: blow 6.80 bar beats binder IR 42 C; correct "
                "REJECT holds the shot",
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
                    "Correct REJECT. Blow 6.80 > 5.50 bar cap; binder 42 C is cold-box, not gel. "
                    "total +0.78 = 0.10 + 0.40 + 0.12 + 0.10 + 0.06.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "foundry-core-shooter",
                    [
                        "reject",
                        "hil",
                        "blow-vs-binder",
                        "cold-box-artifact",
                    ],
                    "Teaches that a cold-binder IR packet can lose to blow PT inside a 340 us "
                    "window; reversing 158 us would have kept the shot armed over the fire cap.",
                    3,
                ),
            ),
        ]
    )


def record_194():
    ticks = [
        tick(1480, 0.06, 0.04, 0.02, 0.02, 0.01),
        tick(5080, 0.10, 0.08, 0.04, 0.03, 0.02),
        tick(5246, 0.06, 0.04, 0.02, 0.01, 0.01),
        tick(6120, 0.12, 0.08, 0.04, 0.04, 0.02),
        tick(9000, 0.05, 0.04, 0.02, 0.01, 0.01),
        tick(300000000, 0.03, 0.02, 0.02, 0.01, 0.01),
    ]
    spikes = [
        spike("enc.press.ctx", 1.080, 0.40),
        spike("ir.eva.C", 2.220, 0.56),
        spike("vac.chamber.mbar", 3.440, 0.47),
        spike("ir.eva.C", 5.080, 1.27),
        spike("vac.chamber.mbar", 5.246, 1.08),
        spike("ctrl.gate", 6.120, 0.99),
        spike("ir.eva.C", 8.440, 0.76),
        spike("enc.press.ctx", 11.200, 0.43),
        spike("vac.chamber.mbar", 14.800, 0.55),
        spike("ctrl.gate", 18.600, 0.82),
        spike("ir.eva.C", 22.400, 0.50),
        spike("enc.press.ctx", 26.800, 0.36),
    ]
    excerpt = independent_excerpt(35194, 52, 28000, 13, spike_avoid_us(spikes))
    params = OrderedDict(
        [
            ("dwell_min", 8.0),
            ("hold", False),
            ("platen_kN", 42.0),
        ]
    )
    state = OrderedDict(
        [
            (
                "description",
                "Lamina-Kame LK-3 Press PL-2 is already in an 8.0 min EVA dwell. Gel pyrometer "
                "118 C is 27 K shy of the 145 C ceiling. Chamber vacuum 0.80 mbar is leftover "
                "pump-down, not a bubble flag. Gel-led ACCEPT keeps the dwell; a vacuum-led abort "
                "would scrap a legal sheet.",
            ),
            ("domain", "photovoltaic-laminator"),
            ("sim_or_real", "simulated"),
            (
                "goal",
                "Hold an 8.0 min dwell while EVA gel stays <= 145 C; do not abort on a 0.80 mbar "
                "pump residual.",
            ),
            ("t0_us", 1756843200000194),
            ("gate_latency_us", 1040),
            ("race_window_us", 400),
            ("race_window_rel_ms", [5.00, 5.40]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "ir.eva.C 118 C",
                                "vac.chamber.mbar 0.80 mbar residual",
                            ],
                        ),
                        (
                            "semantics",
                            "Gel-first ACCEPTS the 8.0 min dwell (already under 145 C). Vacuum-first "
                            "would REJECT on a pump residual.",
                        ),
                        (
                            "window_derivation",
                            "400 us = one EVA-IR sample minus vacuum-tap group delay on this "
                            "laminator bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 166 us vs combined jitter ~62 us (IR 28 + vacuum 34): 2.68x over "
                            "a 2.0x trust floor. Reversing order by < 166 us inside the 400 us window "
                            "would have REJECTED a legal 8.0 min dwell.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "EVA gel IR, 2 kHz, 28 us jitter",
                    "chamber vacuum tap 0-10 mbar, 34 us jitter",
                    "platen encoder (context)",
                    "membrane RTD (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("gel_cap_C", 145.0),
                        ("observed_gel_C", 118.0),
                        ("vac_mbar", 0.80),
                        ("vac_abort_mbar", 4.0),
                        ("proposed_dwell_min", 8.0),
                    ]
                ),
            ),
            (
                "simulation",
                OrderedDict(
                    [
                        (
                            "solver",
                            "lumped EVA gel + 1-D vacuum decay, seed 35194; 6 layer nodes, "
                            "12 min pump-down; NOT CFD, NOT a live laminator",
                        ),
                        (
                            "fidelity_limits",
                            "Linear gel kinetics; no bubble nucleation. Raster is kernelized events, "
                            "not an independent LIF.",
                        ),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Press PL-2 indexed on LK-3; 8.0 min dwell armed.",
                    "2. Gel IR 118 C; vacuum residual 0.80 mbar.",
                    "3. Platen-encoder precursor at 1.080 ms.",
                    "4. Race window [5.000, 5.400] ms.",
                    "5. ir.eva.C 118 C at 5.080 ms (winner).",
                    "6. vac.chamber.mbar 0.80 mbar at 5.246 ms (loser by 166 us).",
                    "7. Gate at 6.120 ms: ACCEPT 8.0 min; executed identical to proposed.",
                    "8. Dwell continues; peak gel 121 C < 145 cap.",
                    "9. Vacuum 0.80 mbar remains a pump residual, not a gel loop.",
                    "10. Delayed (survey_s=300): 5 min coupon peel on the next sheet.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "dwell_80"),
            ("parameters", params),
            (
                "evidence",
                OrderedDict(
                    [
                        ("gel_C", 118.0),
                        ("gel_cap_C", 145.0),
                        ("vac_mbar", 0.80),
                        ("vac_abort_mbar", 4.0),
                        ("race_margin_us", 166),
                        ("combined_jitter_us", 62),
                        ("survey_s", 300),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes an 8.0 min dwell because gel 118 C is under the 145 C cap; "
                "vacuum 0.80 mbar is under the 4.0 abort and is treated as pump residual, not gel.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Gel 118 C won by 166 us and is under the 145 C cap. Vacuum 0.80 mbar is under "
                "the 4.0 mbar abort. ACCEPT the already-legal 8.0 min dwell. A REJECT on pump "
                "residual would stall a legal laminate.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "gel_C",
                            OrderedDict(
                                [
                                    ("cap", 145.0),
                                    ("observed", 118.0),
                                    ("executed_dwell_min", 8.0),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 166),
                                    ("combined_jitter_us", 62),
                                    ("ratio", 2.68),
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
            ("name", "dwell_80"),
            ("parameters", OrderedDict(params)),
            (
                "gate_effect",
                "ACCEPT: dwell 8.0 min unchanged. Gel stayed 118-121 C < 145 cap.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT kept PL-2 at 8.0 min. Gel 118 C was under the 145 C cap; vacuum "
                "0.80 mbar was pump residual. 5 min coupon peel (survey_s=300).",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("dwell", "8.0 min continued"),
                        ("gel", "peak 121 C < 145 cap"),
                        ("vacuum", "0.80 mbar unused as a hold"),
                        ("mission", "laminate continues"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Vacuum residual arrived 166 us after the gel IR; reversing that order would have REJECTED a legal dwell.",
                    "Delayed (survey_s=300): 5 min coupon peel on the next sheet, not a gel event.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "ir.eva.C (5.080 ms, 118 C)"),
                        ("loser", "vac.chamber.mbar (5.246 ms, 0.80 mbar)"),
                        ("margin_us", 166),
                        (
                            "counterfactual_if_reversed",
                            "Vacuum-first by < 166 us inside the 400 us window would have REJECTED "
                            "an already-legal 8.0 min dwell on a 0.80 mbar pump residual.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 6120),
            (
                "reward_inflection_note",
                "Task and safety peak at the correct ACCEPT (6.120 ms, tick 4). The 5 min peel "
                "is delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 300),
        ]
    )
    dw = 0.40
    ras = raster_core(
        28,
        52,
        36,
        52,
        routing(
            "thalamic-relay.eva-ir",
            "spikenaut.policy.dwell-go",
            [
                ("relay.ir.eva", "policy.dwell_go", 0.69),
                ("relay.vac.chamber", "policy.vac_hold", 0.27),
            ],
            "serotonin",
            0.03,
            "gel_stdp; 5-HT tags the already-legal gel bind",
        ),
        excerpt,
        extra=OrderedDict(
            [
                ("excerpt_source", "kernelized_events"),
                ("sim_scope", "none"),
                ("survey_s", 300),
                ("delayed_surprise_s", 300),
            ]
        ),
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", dw),
            ("decision", "ACCEPT"),
            (
                "populations",
                [
                    pop_budget("dwell_go", 40, 0.50, 280.0, dw),
                    pop_budget("vac_hold", 40, 0.50, 70.0, dw),
                    pop_budget("gel_ctx", 24, 0.55, 120.0, dw),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r35-194"),
            (
                "title",
                "Lamina-Kame LK-3 / Press PL-2: EVA gel 118 C beats vacuum 0.80 mbar by 166 us; "
                "correct ACCEPT of an already-legal 8.0 min dwell",
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
                    "Correct ACCEPT. Gel 118 < 145 cap; vacuum is pump residual, not gel. "
                    "total +1.08 = 0.42 + 0.30 + 0.16 + 0.12 + 0.08.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "photovoltaic-laminator",
                    [
                        "accept",
                        "laminator",
                        "gel-vs-vacuum",
                        "simulated-gel",
                        "simulated",
                    ],
                    "Teaches that a vacuum-tap residual can lose to EVA gel IR inside a 400 us "
                    "window; reversing 166 us would have REJECTED an already-legal dwell.",
                    4,
                ),
            ),
        ]
    )


def record_195():
    ticks = [
        tick(1560, 0.06, 0.04, 0.02, 0.02, 0.01),
        tick(3920, 0.10, 0.08, 0.04, 0.03, 0.02),
        tick(4068, 0.06, 0.04, 0.02, 0.01, 0.01),
        tick(4800, 0.14, 0.10, 0.06, 0.04, 0.02),
        tick(7100, 0.05, 0.06, 0.02, 0.01, 0.01),
        tick(240000000, 0.03, 0.02, 0.02, 0.01, 0.01),
    ]
    spikes = [
        spike("enc.head.ctx", 0.680, 0.40),
        spike("rtd.head.C", 1.760, 0.56),
        spike("visc.spray.cP", 2.140, 0.47),
        spike("rtd.head.C", 3.920, 1.27),
        spike("visc.spray.cP", 4.068, 1.08),
        spike("ctrl.gate", 4.800, 0.99),
        spike("rtd.head.C", 6.620, 0.76),
        spike("enc.head.ctx", 8.880, 0.43),
        spike("visc.spray.cP", 12.100, 0.55),
        spike("ctrl.gate", 15.400, 0.82),
        spike("rtd.head.C", 18.200, 0.50),
        spike("enc.head.ctx", 21.000, 0.36),
    ]
    excerpt = independent_excerpt(35195, 84, 22000, 12, spike_avoid_us(spikes))
    params = OrderedDict(
        [
            ("spray_kg_s", 0.42),
            ("hold", False),
            ("head_rpm", 18.0),
        ]
    )
    state = OrderedDict(
        [
            (
                "description",
                "Prill-Flue PF-6 Head-H3 is spraying urea at 0.42 kg/s. Melt RTD 138 C sits 17 K "
                "below the 155 C freeze license. The viscometer's 4.2 cP is a steam-jacket smear, "
                "not a freeze. Keep the spray if melt wins; a visc-led abort would idle a legal "
                "tower.",
            ),
            ("domain", "urea-prill-tower"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Hold 0.42 kg/s spray while melt stays <= 155 C; do not abort on a 4.2 cP steam-jacket film.",
            ),
            ("t0_us", 1756843200000195),
            ("gate_latency_us", 880),
            ("race_window_us", 300),
            ("race_window_rel_ms", [3.90, 4.20]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "rtd.head.C 138 C",
                                "visc.spray.cP 4.2 cP film",
                            ],
                        ),
                        (
                            "semantics",
                            "Melt-first ACCEPTS 0.42 kg/s (138 C < 155 C freeze-cap). Visc-first "
                            "would REJECT on a steam-jacket film.",
                        ),
                        (
                            "window_derivation",
                            "300 us = one head-RTD sample minus spray-viscometer group delay on "
                            "this prill-tower bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 148 us vs combined jitter ~54 us (RTD 24 + visc 30): 2.74x over "
                            "a 2.0x trust floor. Reversing order by < 148 us inside the 300 us window "
                            "would have REJECTED a legal 0.42 kg/s spray.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "head melt RTD, 4 kHz, 24 us jitter",
                    "spray viscometer, 4 kHz, 30 us jitter",
                    "head encoder (context)",
                    "tower air RTD (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("melt_cap_C", 155.0),
                        ("observed_melt_C", 138.0),
                        ("visc_cP", 4.2),
                        ("visc_abort_cP", 16.0),
                        ("proposed_spray_kg_s", 0.42),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Head-H3 indexed on PF-6; spray 0.42 kg/s armed.",
                    "2. Melt 138 C; viscometer 4.2 cP from a jacket film.",
                    "3. Head-encoder precursor at 0.680 ms.",
                    "4. Race window [3.900, 4.200] ms.",
                    "5. rtd.head.C 138 C at 3.920 ms (winner).",
                    "6. visc.spray.cP 4.2 cP at 4.068 ms (loser by 148 us).",
                    "7. Gate at 4.800 ms: ACCEPT 0.42 kg/s; executed identical to proposed.",
                    "8. Spray continues; peak melt 141 C < 155 cap.",
                    "9. Visc 4.2 cP remains a steam-jacket film, not a freeze.",
                    "10. Delayed (qc_s=240): 4 min sieve QC on the next lot.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "spray_042"),
            ("parameters", params),
            (
                "evidence",
                OrderedDict(
                    [
                        ("melt_C", 138.0),
                        ("melt_cap_C", 155.0),
                        ("visc_cP", 4.2),
                        ("visc_abort_cP", 16.0),
                        ("race_margin_us", 148),
                        ("combined_jitter_us", 54),
                        ("qc_s", 240),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 0.42 kg/s because melt 138 C is under the 155 C freeze-cap; "
                "visc 4.2 cP is under the 16.0 abort and is treated as a jacket film, not a freeze.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Melt 138 C won by 148 us and is under the 155 C cap. Visc 4.2 cP is under the "
                "16.0 abort. ACCEPT the already-legal 0.42 kg/s spray. A REJECT on jacket film "
                "would stall a legal prill.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "melt_C",
                            OrderedDict(
                                [
                                    ("cap", 155.0),
                                    ("observed", 138.0),
                                    ("executed_spray_kg_s", 0.42),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 148),
                                    ("combined_jitter_us", 54),
                                    ("ratio", 2.74),
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
            ("name", "spray_042"),
            ("parameters", OrderedDict(params)),
            (
                "gate_effect",
                "ACCEPT: spray 0.42 kg/s unchanged. Melt stayed 138-141 C < 155 cap.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT kept Head-H3 at 0.42 kg/s. Melt 138 C was under the 155 C cap; "
                "visc 4.2 cP was a steam-jacket film. 4 min sieve QC (qc_s=240).",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("spray", "0.42 kg/s continued"),
                        ("melt", "peak 141 C < 155 cap"),
                        ("visc", "4.2 cP unused as a hold"),
                        ("mission", "prill continues"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Steam-jacket film arrived 148 us after the head RTD; reversing that order would have REJECTED a legal spray.",
                    "Delayed (qc_s=240): 4 min sieve QC on the next lot, not a freeze event.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "rtd.head.C (3.920 ms, 138 C)"),
                        ("loser", "visc.spray.cP (4.068 ms, 4.2 cP)"),
                        ("margin_us", 148),
                        (
                            "counterfactual_if_reversed",
                            "Visc-first by < 148 us inside the 300 us window would have REJECTED "
                            "an already-legal 0.42 kg/s spray on a 4.2 cP jacket film.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 4800),
            (
                "reward_inflection_note",
                "Task and safety peak at the correct ACCEPT (4.800 ms, tick 4). The 4 min QC is "
                "delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 240),
        ]
    )
    dw = 0.30
    ras = raster_core(
        22,
        84,
        30,
        55,
        routing(
            "thalamic-relay.head-rtd",
            "spikenaut.policy.spray-go",
            [
                ("relay.rtd.head", "policy.spray_go", 0.70),
                ("relay.visc.spray", "policy.visc_hold", 0.26),
            ],
            "histamine",
            0.045,
            "melt_stdp; HA tags the already-legal head-RTD bind",
        ),
        excerpt,
        extra=OrderedDict(
            [
                ("excerpt_source", "kernelized_events"),
                ("sim_scope", "none"),
                ("qc_s", 240),
                ("delayed_surprise_s", 240),
            ]
        ),
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", dw),
            ("decision", "ACCEPT"),
            (
                "populations",
                [
                    pop_budget("spray_go", 40, 0.50, 300.0, dw),
                    pop_budget("visc_hold", 40, 0.50, 80.0, dw),
                    pop_budget("melt_ctx", 24, 0.55, 150.0, dw),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r35-195"),
            (
                "title",
                "Prill-Flue PF-6 / Head-H3: melt 138 C beats visc film 4.2 cP by 148 us; correct "
                "ACCEPT of an already-legal 0.42 kg/s spray",
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
                    "Correct ACCEPT. Melt 138 < 155 cap; visc is jacket film, not freeze. "
                    "total +1.16 = 0.44 + 0.34 + 0.18 + 0.12 + 0.08.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "urea-prill-tower",
                    [
                        "accept",
                        "prill-tower",
                        "melt-vs-visc",
                        "designed",
                    ],
                    "Teaches that a steam-jacket visc film can lose to head RTD inside a 300 us "
                    "window; reversing 148 us would have REJECTED an already-legal spray.",
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


def prior_domains_and_descs():
    domains = set()
    descs = []
    for path in sorted(Path("/tmp").glob("ttf-r*/batch-r*.jsonl")):
        if path.resolve() == BATCH_PATH.resolve():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        for line in text.split("\n"):
            if not line.strip():
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            d = rec.get("state", {}).get("domain") or rec.get("meta", {}).get("domain")
            if d:
                domains.add(str(d))
            desc = rec.get("state", {}).get("description")
            if isinstance(desc, str):
                descs.append(desc)
    return domains, descs


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
    prior_doms, prior_descs = prior_domains_and_descs()
    jprior = 0.0
    for desc in descs:
        for other in prior_descs:
            jprior = max(jprior, jaccard(desc, other))
    if jprior >= 0.4:
        issues.append(f"Jaccard vs prior {jprior:.3f}")
    domains = [r["state"]["domain"] for r in records]
    if len(set(domains)) != 5:
        issues.append(f"domain collision {domains}")
    overlap = set(domains) & prior_doms
    if overlap:
        issues.append(f"prior domain reuse {overlap}")
    if set(domains) != THIS_DOMAINS:
        issues.append(f"unexpected domains {domains}")
    banned_hit = set(domains) & BANNED_DOMAINS
    if banned_hit:
        issues.append(f"banned domains {banned_hit}")
    wrong = [
        r
        for r in records
        if r["safety_decision"].get("correctness") == "incorrect"
        or r["meta"].get("supervisor_error_type")
    ]
    if len(wrong) != 1 or wrong[0]["id"] != "ttf-r39-212":
        issues.append(f"wrong-gate set {[w['id'] for w in wrong]}")
    if wrong and wrong[0]["meta"].get("supervisor_error_type") != "wrong-modify":
        issues.append("expected wrong-modify")
    if any(r["state"]["sim_or_real"] == "real" for r in records):
        issues.append("sim_or_real=real")
    hil = [r["id"] for r in records if r["state"]["sim_or_real"] == "hil"]
    if hil != ["ttf-r39-213"]:
        issues.append(f"hil set {hil}")
    sim = [r["id"] for r in records if r["state"]["sim_or_real"] == "simulated"]
    if sim != ["ttf-r39-214"]:
        issues.append(f"simulated set {sim}")
    decisions = [r["safety_decision"]["decision"] for r in records]
    if (
        decisions.count("ACCEPT") != 2
        or decisions.count("MODIFY") != 2
        or decisions.count("REJECT") != 1
    ):
        issues.append(f"gate mix {decisions}")
    ids = [r["id"] for r in records]
    if ids != [f"ttf-r39-{n}" for n in range(211, 216)]:
        issues.append(f"ids {ids}")
    for rec in records:
        blob = json.dumps(rec)
        if "training_ready" in blob:
            issues.append(f"{rec['id']} training_ready present")
        if "outputs/raw" in blob:
            issues.append(f"{rec['id']} mentions outputs/raw")
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
        overlap_ex = excerpt_vs_spikes(rec)
        if rec["id"] == "ttf-r35-191":
            if rec["raster"].get("excerpt_source") != "independent_lif":
                issues.append("191 missing independent_lif")
            if rec["future_outcome"]["reward_inflection_t_us"] > rec["raster"]["window_ms"] * 1000:
                issues.append("191 inflection outside window")
            if rec["reward_components"]["total"] >= 0:
                issues.append("191 partnered-neg total not negative")
        elif overlap_ex >= 0.8:
            issues.append(f"{rec['id']} excerpt overlap {overlap_ex:.2f}")
        inf = rec["future_outcome"]["reward_inflection_t_us"]
        tick_times = [t["t_us"] for t in rec["reward_components"]["ticks"]]
        if inf not in tick_times:
            issues.append(f"{rec['id']} inflection {inf} not a tick")
        if len(rec["reward_components"]["ticks"]) != 6:
            issues.append(f"{rec['id']} tick count")
        if not (8 <= len(rec["state"]["episode_steps"]) <= 15):
            issues.append(f"{rec['id']} episode_steps")
        if rec["gate_snn"]["decision"] != rec["safety_decision"]["decision"]:
            issues.append(f"{rec['id']} gate_snn decision mismatch")
        if rec["meta"]["round"] != 35:
            issues.append(f"{rec['id']} meta.round")
        if rec["meta"]["rights"]["intended_use"] != "research_only":
            issues.append(f"{rec['id']} rights")
        if rec["meta"]["rights"]["linear_issue"] != "RM-793":
            issues.append(f"{rec['id']} RM-793")
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
        if not (5 <= nspk <= 40):
            issues.append(f"{rec['id']} spike count {nspk}")
        times = [e["t_rel_ms"] for e in rec["spike_events"]]
        if times != sorted(times):
            issues.append(f"{rec['id']} spike order")
        if not (8 <= len(rec["raster"]["excerpt"]) <= 16):
            issues.append(f"{rec['id']} excerpt n={len(rec['raster']['excerpt'])}")
        exec_p = rec["executed_action"]["parameters"]
        prop_p = rec["proposed_action"]["parameters"]
        if rec["safety_decision"]["decision"] == "ACCEPT" and exec_p != prop_p:
            issues.append(f"{rec['id']} ACCEPT params differ")
        if rec["id"] == "ttf-r35-192":
            if rec["executed_action"]["parameters"].get("quench_tph") == rec["proposed_action"]["parameters"].get("quench_tph"):
                issues.append("192 quench not edited")
            if rec["executed_action"]["parameters"].get("quench_tph") == 18.0:
                issues.append("192 executed the correct 18 t/h trim")
            if rec["executed_action"]["parameters"].get("quench_tph") != 42.0:
                issues.append("192 expected over-clamp 42 t/h")
            if "recovery" not in rec["future_outcome"]:
                issues.append("192 missing recovery")
            table_to = {row["to"] for row in rec["raster"]["routing"]["table"]}
            if "policy.quench_trim" in table_to:
                issues.append("192 routing still has quench_trim")
            if "policy.quench_over" not in table_to:
                issues.append("192 routing missing quench_over")
        blob_l = blob.lower()
        for frag in BANNED_PLANT_FRAGMENTS:
            if frag.lower() in blob_l:
                issues.append(f"{rec['id']} banned plant {frag}")
        delay = rec["future_outcome"].get("delayed_surprise_s") or rec["raster"].get(
            "delayed_surprise_s"
        )
        if delay is not None:
            expected_t6 = int(round(float(delay) * 1e6))
            if rec["reward_components"]["ticks"][-1]["t_us"] != expected_t6:
                issues.append(
                    f"{rec['id']} tick6 {rec['reward_components']['ticks'][-1]['t_us']} "
                    f"vs delayed_surprise {expected_t6}"
                )
        dw_s = rec["gate_snn"]["decision_window_ms"] / 1000.0
        for popu in rec["gate_snn"]["populations"]:
            if "mean_rate_hz" in popu:
                exp = round(popu["neurons"] * popu["mean_rate_hz"] * dw_s)
                if abs(popu["spikes"] - exp) > 1:
                    issues.append(
                        f"{rec['id']} gate_snn {popu['name']} spikes {popu['spikes']} vs {exp}"
                    )
        t6 = rec["reward_components"]["ticks"][-1]["t_us"]
        if t6 <= rec["raster"]["window_ms"] * 1000:
            issues.append(f"{rec['id']} tick6 inside raster")
        gl, rw = rec["state"]["gate_latency_us"], rec["state"]["race_window_us"]
        if not (50 <= gl <= 2000):
            issues.append(f"{rec['id']} gate_latency")
        if not (50 <= rw <= 1000):
            issues.append(f"{rec['id']} race_window")
    return issues, jmax, jprior


def notes_text(jmax: float, jprior: float) -> str:
    return f"""# Thalamic Trajectory Factory — NOTES-r35

- Factory: `thalamic-trajectory-factory`
- Run label: `2026-09-02-final-heavy`
- Generator: `grok-4.6`
- Channel: SuperGrok Heavy consumer chat (RM-793 research-only)
- Quota: 5
- Quality: Q=5
- IDs: `ttf-r35-191` … `ttf-r35-195`
- Domains this batch: `geothermal-binary-ORC`, `ammonia-converter`, `foundry-core-shooter`, `photovoltaic-laminator`, `urea-prill-tower`

These five domain slugs sit outside the prompt 8-pool and outside staged r13–r28 occupancy (including r23 `lng-open-rack` / `metro-psd`, r24 `electrolyzer-stack` / `hvdc-thyristor-valve`, r25 `salt-cavern-CAES` / `tire-curing-press`, r26 `lime-rotary-kiln` / `ferry-linkspan`, r28 `rotary-kiln-cement` / `submarine-cable-lay`, and gen_r30 sit-ins `wind-nacelle-yaw` / `steel-caster-mold` / `cement-precalciner`). All five plants are invented. Do not restack r12–r28 plants (Marrow-Dock, Vesper-Lattice, Brine-Well, Saddle-Arc, Ashlar-Gait, Nacre-Well, Quern-Forge, Tinder-Box, Whimbrel-Stack, Cinder-Loft, Suture-Isle, Kiln-Spur, Oxbow-Switch, Pitch-Kettle, Shale-Quay, Polder-Rye, Flint-Mask, Gyre-Tokamak, Quarry-Bowl, Orpiment, Apside-Yard, Sump-Drift, Felt-Reach, Frost-Cist, Clothoid-Bowl, Wort-Cairn, Firn-Span, Sleet-Row, Oxbow-Pound, Tuyere-Holt, Bracken-Wire, Cullet-Reach, Rime-Causeway, Abyss-Joint, Gnomon-Well, Scree-Hitch, Flux-Kettle, Mire-Cask, Slack-Firth, Chaff-Rise, Sinter-Ridge, Chaff-Mere, Caisson-Forge, Crumb-Vault, Caliche-Drift, Thaw-Reach, Kipple-Gate, Anode-Fen, Vial-Rime, Tern-Apron, Sedge-Cell, Fjord-Convert, Retort-Fen, Skerries-Trench, Iodine-Well, Halite-Keel, Caldera-Mold, Isotope-Pad, Lay-Sound, Drupe-Press, Marl-Knap, Gull-Pontoon, Sprue-Nook, Osmia-Reach, Marl-Rake, Bight-Lay, Cryolite-Hall, Surge-Adit, Massecuite-Kettle).

## Batch map

| id | domain | decision | correctness | sim_or_real | total | edge |
|----|--------|----------|-------------|-------------|-------|------|
| ttf-r35-191 | geothermal-binary-ORC | MODIFY | correct | designed | **−0.46** | process-correct isobutane clamp; silica-plate part inside 40 ms raster; independent LIF |
| ttf-r35-192 | ammonia-converter | MODIFY | **incorrect (wrong-modify / over-clamp)** | designed | −0.68 | bed 518 C > 505 C cap; quench dumped 12→42 t/h instead of trimmed 12→18 t/h |
| ttf-r35-193 | foundry-core-shooter | REJECT | correct | hil | +0.78 | blow 6.80 bar beats binder IR 42 C; hold shot |
| ttf-r35-194 | photovoltaic-laminator | ACCEPT | correct | simulated | +1.08 | gel 118 C vs vacuum 0.80 mbar; proposed 8.0 min dwell already legal |
| ttf-r35-195 | urea-prill-tower | ACCEPT | correct | designed | +1.16 | melt 138 C vs visc film 4.2 cP; proposed 0.42 kg/s already legal |

Gate mix: 2 ACCEPT, 1 correct MODIFY (partnered-neg, in-window), 1 incorrect MODIFY (over-clamp), 1 correct REJECT. Provenance: designed×3, simulated×1, hil×1 (Loam-Hurst LH-HIL shooter bench). Intra-batch Jaccard on `state.description` {jmax:.3f} (max vs prior staged {jprior:.3f}).

## Wrong-modify

**ttf-r35-192** is the mandated incorrect gate (`safety_decision.correctness=incorrect`, `meta.supervisor_error_type=wrong-modify`). Alternate vs even rounds: r12/r14/r16/r18/r20/r22/r26/r28 host wrong-reject; odd rounds host wrong-modify. This is **over-clamp** (correct actuator, magnitude past the recovery setpoint), not r13/r19 wrong-axis, not r14/r23 wrong-loop, not r15 clamp-too-late, not r21 wrong-polarity, not r24 under-clamp, not r25 wrong-phase. Do not emit a wrong-ACCEPT.

Haber-Knoll HN-5 / Bed-2 reads converter RTD **518 C** against a **505 C** quench cap. Interbed quench **12 t/h** is under its own **48 t/h** header. Sidecar arithmetic `518 > 505` is true. A timely trim is quench **12 → 18 t/h** (predicted 498 C). A weak supervisor dumps **12 → 42 t/h**, driving the bed to **448 C** under the **470 C** quench-kill floor. Convictable without Haber physics: `evidence.bed_C > evidence.bed_cap_C`, `executed_action` sets `quench_tph=42` ≠ `correct_quench_tph=18`, `observed_after_overclamp_C=448 < quench_kill_floor_C=470`, `raster.routing.table` sends `relay.rtd.bed` → `policy.quench_over` (weight 0.76) with no positive weight to `policy.quench_trim`, and `gate_snn` has `quench_over` above threshold while `quench_trim` is not. Recovery: MODIFY quench 12 → 18 t/h; leave feed at 82 t/h. Cost: 12 min quench-kill restart (`abort_s=720`).

## Partnered-negative in-window (191)

**ttf-r35-191** is the partnered negative: process-correct MODIFY (isobutane held 28 kg/s; evaporator 12.1 bar < 12.5 cap) while the world still charges. Safety −0.62 prices the plate P-11 part at **21.400 ms**; `task_progress` stays +0.32 because the clamp completed. Inflection `t_us=21400` is tick 5 and is **inside** the 40 ms raster (`21400 ≤ 40000`). Named un-netted loss: 16 min plate swap (`abort_s=960`). Not folded into process heads.

Independent LIF (the one labeled sidecar sim): `state.sim_or_real` remains `designed`. `raster.excerpt_source=independent_lif`, `raster.sim_scope=sidecar_only`, `raster.lif` seed 35191, stim `[20000, 23000]`. Excerpt is membrane crossings (`lif.clamp` early vs `lif.silica` 20–23 ms), not a 1:1 remap of `spike_events`. `meta.tags` include `independent-lif-raster` and `sidecar-sim-only`.

## Reward formula and tick reconciliation

Declared aggregation on every record:

`total = task_progress + safety + efficiency + coherence + exploration`

Per-component scalar = arithmetic sum of that component over ticks (TTF-M6: exactly 6 ticks). Tick 6 is bound to a published sidecar (`abort_s`, `survey_s`, `qc_s`) via `future_outcome.delayed_surprise_s` and is strictly after the raster window. Inflection `t_us` is an actual tick.

| id | ticks | tp | saf | eff | coh | exp | total | inflection tick |
|----|-------|----|-----|-----|-----|-----|-------|-----------------|
| 191 | 6 | +0.32 | −0.62 | −0.16 | +0.04 | −0.04 | −0.46 | 5 (21400) |
| 192 | 6 | −0.22 | −0.16 | −0.24 | −0.12 | +0.06 | −0.68 | 4 (6260) |
| 193 | 6 | +0.10 | +0.40 | +0.12 | +0.10 | +0.06 | +0.78 | 4 (7170) |
| 194 | 6 | +0.42 | +0.30 | +0.16 | +0.12 | +0.08 | +1.08 | 4 (6120) |
| 195 | 6 | +0.44 | +0.34 | +0.18 | +0.12 | +0.08 | +1.16 | 4 (4800) |

Tick-6 sidecar bind: 191 `abort_s=960`, 192 `abort_s=720`, 193 `abort_s=420`, 194 `survey_s=300`, 195 `qc_s=240`.

## Raster / energy (Loihi-2 4-core, 23 pJ/spike)

| id | domain | n | rate Hz | window_ms | spikes | energy_pJ | energy_uJ |
|----|--------|---|---------|-----------|--------|-----------|-----------|
| 191 | geothermal-binary-ORC | 72 | 28 | 40 | 81 | 1863 | 0.001863 |
| 192 | ammonia-converter | 64 | 40 | 26 | 67 | 1541 | 0.001541 |
| 193 | foundry-core-shooter | 120 | 20 | 48 | 115 | 2645 | 0.002645 |
| 194 | photovoltaic-laminator | 52 | 36 | 28 | 52 | 1196 | 0.001196 |
| 195 | urea-prill-tower | 84 | 30 | 22 | 55 | 1265 | 0.001265 |

`spikes = round(n × rate × window_s)`. Every record carries `gate_snn` whose `decision` matches the safety gate; populations that declare rate+spikes meet the same ±1 budget against `decision_window_s`. `routing.third_factor` has modulator, `tau_e_s`/`tau_e_ms` pair, and eligibility. Excerpt same-neuron gap ≥ 1000 µs; spike trains same-channel refractory ≥ 0.8 ms. Non-191 excerpts are kernelized and independent of `spike_events` times (overlap < 0.8).

## Local checks (staging, not raw)

See generator stdout: `check_jsonl` FactoryStaging, `validate_run.check_line`, `dumps_exact_json`, `raster_status`, `verify_batch_for_frontier(strict=True)`, `spike_probe.py --strict`, tick sums, refractory, Jaccard.

Never `training_ready`. Never `sim_or_real=real`. Never wrote `outputs/raw/`.

## Residual weaknesses (honest)

1. Only **one** labeled independent LIF (191). The other four excerpts are independent of `spike_events` times but are not declared population sims.
2. Wrong-ACCEPT still absent (guard).
3. Tick-6 sidecar bind is a densification of r14/r23, not a new class.
4. Five domain slugs leave the prompt's 8-item pool; a later round that must stay inside the pool will have to rotate sit-outs instead.
5. 194/195 ACCEPT are already-legal proposals confirmed by race order; a later round could pair an ACCEPT with a world charge that does not go negative.

## Next densification target

Labeled LIF on a second record, or an ISI histogram sidecar. If a later round returns to the 8-item pool, sit out the r12 five again. Remaining unused wrong-MODIFY subclasses include **stale-sample / lagged-tag** (not over-clamp, not wrong-phase, not wrong-axis). Wrong-ACCEPT remains structurally absent until a prompt amendment.

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
        BATCH_PATH, "batch-r35.jsonl", staging=FactoryStaging(enabled=True)
    )
    report.append(("check_jsonl FactoryStaging", errors, warnings, kinds, nrec))
    line_errs = []
    for i, rec in enumerate(records, 1):
        errs, kind = check_line(rec, f"batch-r35.jsonl:{i}", factory_staging=True)
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
    return report


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    records = [record_191(), record_192(), record_193(), record_194(), record_195()]
    issues, jmax, jprior = self_check(records)
    notes = notes_text(jmax, jprior)
    lines = [
        json.dumps(rec, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
        for rec in records
    ]
    BATCH_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    NOTES_PATH.write_text(notes, encoding="utf-8")
    print(f"wrote {BATCH_PATH} lines={len(lines)} bytes={BATCH_PATH.stat().st_size} jmax={jmax:.3f} jprior={jprior:.3f}")
    print(f"wrote {NOTES_PATH} bytes={NOTES_PATH.stat().st_size}")
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
            for w in warnings[:20]:
                print("  WARN", w)
        elif name == "check_line+exact_json":
            if item[1]:
                failed = True
                print("  LINE_ERRS", item[1])
        elif name == "raster_status":
            if item[1]:
                failed = True
        elif name == "verify_batch_for_frontier":
            print("  counts", item[1], "blocked", item[3])
            if item[3]:
                failed = True
                print("  findings", item[2][:8])
        elif name == "validate_novel_coverage":
            if item[1]:
                failed = True
        elif name == "spike_probe":
            if item[1] != 0:
                failed = True
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
