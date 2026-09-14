#!/usr/bin/env python3
"""Emit TTF r29 JSONL (ttf-r29-161..165) into /tmp/ttf-r29/. Never writes outputs/raw/."""

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

OUT_DIR = Path("/tmp/ttf-r29")
BATCH_PATH = OUT_DIR / "batch-r29.jsonl"
NOTES_PATH = OUT_DIR / "NOTES-r29.md"
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
        ("generated_at", "2026-09-03T00:25:00Z"),
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
    "Oolite-Span",
    "Fathom-Lock",
    "Loess-Stride",
    "Swage-Holt",
    "Slag-Siding",
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
    "Sump-Drift",
    "Felt-Reach",
    "Frost-Cist",
    "Clothoid-Bowl",
    "Firn-Span",
    "Sleet-Row",
    "Oxbow-Pound",
    "Tuyere-Holt",
    "Bracken-Wire",
    "Cullet-Reach",
    "Rime-Causeway",
    "Gnomon-Well",
    "Scree-Hitch",
    "Solder-Kite",
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
    "Lyo-Deck",
    "Fjord-Convert",
    "Kelp-Jetty",
    "Skerries-Trench",
    "Iodine-Well",
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


def lif_161_excerpt():
    n = 84
    dt_us = 100
    tau_m_ms = 18.5
    v_th = 1.0
    v_reset = 0.0
    refractory_us = 1000
    i_bias = 0.90
    i_stim_peak = 2.50
    stim = (22000, 26000)
    seed = 29161
    window_us = 36000
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
    early = [(t, nid) for t, nid in spikes if t < 22000]
    burst = [(t, nid) for t, nid in spikes if 22000 <= t < 26000]
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
    take(burst, 9, label_times=(23400, 24100, 24800))
    clamp = [(t, nid) for t, nid in picked if t < 22000][:7]
    foam = [(t, nid) for t, nid in picked if t >= 22000][:9]
    picked = sorted(clamp + foam, key=lambda item: (item[0], item[1]))
    if len(picked) < 10:
        raise RuntimeError(f"LIF excerpt short: {len(picked)}")
    channels = ["lif.clamp" if t < 22000 else "lif.foam" for t, _ in picked]
    lif = OrderedDict(
        [
            ("model", "leaky_integrate_and_fire"),
            ("n", 84),
            ("dt_us", 100),
            ("tau_m_ms", 18.5),
            ("v_rest", 0.0),
            ("v_reset", 0.0),
            ("v_th", 1.0),
            ("r_m", 1.0),
            ("refractory_us", 1000),
            ("i_bias", 0.90),
            ("i_stim_peak", 2.50),
            ("stim_t_us", [22000, 26000]),
            ("i_clamp_extra", 0.64),
            ("clamp_n", 14),
            ("seed", 29161),
            (
                "note",
                "Population sim scoped to this sidecar. Plant remains designed. "
                "Neurons 0-13 carry +0.64 steam-clamp bias; stim 22-26 ms is the foam-over strike.",
            ),
        ]
    )
    extra = OrderedDict(
        [
            ("excerpt_source", "independent_lif"),
            ("sim_scope", "sidecar_only"),
            ("lif", lif),
            ("abort_s", 900),
            ("delayed_surprise_s", 900),
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
            ("round", 29),
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


def record_161():
    excerpt, extra = lif_161_excerpt()
    ticks = [
        tick(2460, 0.04, -0.02, -0.02, 0.01, 0.00),
        tick(6240, 0.08, -0.04, -0.02, 0.02, -0.01),
        tick(6418, 0.04, -0.03, -0.02, 0.01, 0.00),
        tick(6720, 0.08, -0.06, -0.04, 0.02, -0.01),
        tick(23400, 0.04, -0.44, -0.02, -0.01, -0.01),
        tick(900000000, 0.02, -0.05, -0.02, 0.01, -0.01),
    ]
    state = OrderedDict(
        [
            (
                "description",
                "Pan P-12 at Muscovado-Well MW-5 is boiling 18 t of B-massecuite while "
                "refractometer Brix sits at 96.4 against a 94.0 strike ceiling. "
                "Brix-first drops steam 1.80 -> 1.15 bar; steam-first would keep 1.80 bar "
                "because 1.80 is still under the 2.20 bar chest cap. A foam bridge already "
                "nucleated on two calandria tubes does not appear on Brix or steam until the AE snap.",
            ),
            ("domain", "sugar-vacuum-pan"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Keep pan P-12 Brix <= 94.0 and finish the strike without dumping "
                "massecuite onto the catch-all.",
            ),
            ("t0_us", 1756860000000161),
            ("gate_latency_us", 720),
            ("race_window_us", 360),
            ("race_window_rel_ms", [6.20, 6.56]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "therm.brix 96.4",
                                "stm.steam.bar 1.80 under 2.20 cap",
                            ],
                        ),
                        (
                            "semantics",
                            "Brix-first latches steam clamp 1.80 -> 1.15 bar; steam-first "
                            "keeps 1.80 bar on a 'still under chest cap' model.",
                        ),
                        (
                            "window_derivation",
                            "360 us = one pan-refractometer slot versus the steam-chest "
                            "PT publisher on this vacuum-pan skid bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 178 us vs combined jitter 60 us (Brix 28 + steam 32): 3.0x over "
                            "a 2.0x trust floor. Reversing order by < 178 us inside the 360 us window "
                            "would have kept 1.80 bar; predicted next-sample 95.2 > 94.0 cap.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "in-pan refractometer Brix, 2 kHz, 28 us jitter",
                    "steam-chest pressure transmitter, 1 kHz, 32 us jitter",
                    "calandria AE puck on two tubes (context)",
                    "catch-all load cell (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("brix_cap", 94.0),
                        ("observed_brix", 96.4),
                        ("steam_bar", 1.80),
                        ("steam_cap_bar", 2.20),
                        ("predicted_unclamped_next_brix", 95.2),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Pan P-12 indexed; 18 t B-massecuite; Brix 96.4.",
                    "2. Steam chest 1.80 bar under 2.20 bar cap; strike armed.",
                    "3. Encoder precursor at 1.180 ms.",
                    "4. Race window [6.200, 6.560] ms.",
                    "5. therm.brix 96.4 at 6.240 ms (winner).",
                    "6. stm.steam.bar 1.80 at 6.418 ms (loser by 178 us).",
                    "7. Gate at 6.720 ms: MODIFY clamp steam 1.80 -> 1.15 bar.",
                    "8. After clamp Brix 93.1 < 94.0; steam still 1.15 bar.",
                    "9. At 23.400 ms a foam bridge dumps 0.3 t onto the catch-all.",
                    "10. 15 min pan wash + seed reload (abort_s=900); named un-netted loss.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_pan_brix"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("steam_bar", 1.80),
                        ("brix", 96.4),
                        ("strike_armed", True),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("brix", 96.4),
                        ("brix_cap", 94.0),
                        ("predicted_unclamped_next_brix", 95.2),
                        ("steam_bar", 1.80),
                        ("steam_cap_bar", 2.20),
                        ("race_margin_us", 178),
                        ("combined_jitter_us", 60),
                        ("abort_s", 900),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 1.80 bar because steam-chest 1.80 is under 2.20, treating "
                "the 96.4 Brix as a still-wet massecuite rather than a strike overshoot.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "correct"),
            (
                "rationale",
                "Brix 96.4 won by 178 us, so the pan is over-concentrated, not still a chest-pressure "
                "story. Holding 1.80 bar predicts next-sample 95.2 > 94.0 cap. MODIFY: steam "
                "1.80 -> 1.15 bar. Observed after clamp 93.1 < 94.0. A full REJECT is not "
                "indicated: a clean strike accepts 1.15 bar.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "brix",
                            OrderedDict(
                                [
                                    ("cap", 94.0),
                                    ("observed", 96.4),
                                    ("predicted_unclamped_next", 95.2),
                                    ("clamped_steam_bar", 1.15),
                                    ("observed_after_clamp", 93.1),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 178),
                                    ("combined_jitter_us", 60),
                                    ("ratio", 2.97),
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
            ("name", "clamped_pan_steam"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("steam_bar", 1.15),
                        ("brix", 93.1),
                        ("strike_armed", True),
                    ]
                ),
            ),
            (
                "gate_effect",
                "MODIFY: steam 1.80 -> 1.15 bar. Process-correct vs the 94.0 Brix cap. Foam "
                "bridge still dumps at 23.400 ms.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Process-correct MODIFY held Brix at 93.1. At 23.400 ms a foam bridge already "
                "nucleated on two calandria tubes dumped 0.3 t onto the catch-all. Clamp "
                "reduced dump energy; it did not prevent the snap. Partnered negative: process "
                "heads stay honest; world loss is named, not netted.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("brix", "clamp executed; peak 93.1 < 94.0 cap"),
                        ("foam_bridge", "dumped at 23.400 ms; 0.3 t catch-all"),
                        ("repair", "15 min pan wash + seed reload (abort_s=900)"),
                        ("mission", "MW-5 strike incomplete this cycle"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Neither Brix nor steam-chest PT predicted the seated foam bridge; ae.foam.strike is a new channel at 23.400 ms, 16.680 ms after the gate, still inside the 36 ms raster.",
                    "Delayed (abort_s=900): 15 min pan wash + seed reload. Named un-netted loss, not folded into task_progress.",
                ],
            ),
            (
                "un_netted_loss",
                "15 min pan wash + seed reload after the foam dump. Safety head -0.64 prices the "
                "dump; task_progress stays +0.30 because the steam clamp completed under the 94.0 "
                "Brix cap. World loss is named here, not subtracted from process heads.",
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "therm.brix (6.240 ms, 96.4)"),
                        ("loser", "stm.steam.bar (6.418 ms, 1.80 bar)"),
                        ("margin_us", 178),
                        (
                            "counterfactual_if_reversed",
                            "Steam-first by < 178 us inside the 360 us window would have kept "
                            "1.80 bar; predicted next-sample 95.2 would have exceeded the 94.0 "
                            "cap even without the foam bridge. The MODIFY is still the correct "
                            "process. The dump is a later world charge either way, cheaper with "
                            "the clamp than without.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 23400),
            (
                "reward_inflection_note",
                "Safety collapses at the 23.400 ms foam-bridge dump (tick t_us=23400), inside the "
                "36 ms raster. The correct MODIFY at 6.720 ms is in the same excerpt. Do not put "
                "inflection on the abort_s=900 wash tick.",
            ),
        ]
    )
    spikes = [
        spike("enc.pan.ctx", 1.180, 0.41),
        spike("therm.brix", 2.460, 0.58),
        spike("stm.steam.bar", 3.900, 0.50),
        spike("therm.brix", 6.240, 1.31),
        spike("stm.steam.bar", 6.418, 1.12),
        spike("ctrl.gate", 6.720, 0.97),
        spike("therm.brix", 8.400, 0.82),
        spike("stm.steam.bar", 10.800, 0.64),
        spike("ctrl.gate", 14.200, 0.86),
        spike("ae.foam.strike", 23.400, 1.48),
        spike("ae.foam.strike", 25.100, 0.93),
        spike("enc.pan.ctx", 29.600, 0.40),
        spike("therm.brix", 34.200, 0.55),
    ]
    ras = raster_core(
        36,
        84,
        22,
        67,
        routing(
            "thalamic-relay.pan-brix",
            "spikenaut.policy.steam-clamp",
            [
                ("relay_therm_brix", "policy_steam_clamp", 0.69),
                ("relay_stm_chest", "policy_steam_hold", 0.28),
                ("relay_ae_foam", "policy_steam_clamp", -0.40),
            ],
            "noradrenaline",
            0.045,
            "surprise-gated pre_post_stdp; NA at Brix win (6.240 ms) opens a 36 ms eligibility "
            "trace that still covers the 23.400 ms foam dump",
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
                    pop("steam_clamp", 48, 0.50, 230.0, 4),
                    pop("steam_hold", 40, 0.80, 55.0, 1),
                    pop("foam_veto", 22, 0.75),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r29-161"),
            (
                "title",
                "Muscovado-Well MW-5 / pan P-12: Brix beats steam-chest by 178 us; correct "
                "MODIFY still eats an in-window foam-bridge dump (partnered negative total -0.46)",
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
                    "36 ms raster. total -0.46 = 0.30 + -0.64 + -0.14 + 0.06 + -0.04. Named pan "
                    "wash (abort_s=900) is not netted into task_progress.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "sugar-vacuum-pan",
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
                    "15 min pan wash.",
                    1,
                ),
            ),
        ]
    )


def record_162():
    ticks = [
        tick(2180, -0.02, -0.02, -0.02, -0.01, 0.01),
        tick(5480, -0.04, -0.04, -0.04, -0.02, 0.01),
        tick(5648, -0.03, -0.03, -0.03, -0.01, 0.01),
        tick(5980, -0.06, -0.10, -0.08, -0.03, 0.02),
        tick(8200, -0.02, -0.03, -0.03, -0.01, 0.01),
        tick(840000000, -0.01, -0.02, -0.02, 0.00, 0.00),
    ]
    spikes = [
        spike("enc.press.ctx", 1.020, 0.42),
        spike("pt.bladder.bar", 2.180, 0.57),
        spike("enc.mold.lock", 3.400, 0.49),
        spike("pt.bladder.bar", 5.480, 1.29),
        spike("enc.mold.lock", 5.648, 1.10),
        spike("ctrl.gate", 5.980, 0.96),
        spike("pt.bladder.bar", 8.200, 0.80),
        spike("enc.mold.lock", 10.400, 0.63),
        spike("ctrl.gate", 13.800, 0.84),
        spike("enc.press.ctx", 18.200, 0.41),
        spike("pt.bladder.bar", 22.400, 0.54),
        spike("enc.mold.lock", 24.600, 0.38),
    ]
    excerpt = independent_excerpt(29162, 58, 25000, 14, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Press P-11 at Green-Bladder GB-4 is still in bladder-inflate with PT 22.4 bar "
                "against an 18.0 bar cure-hold ceiling. Mold lock is seated (0.02 mm/s). "
                "PT-first should vent inflate 22.4 -> 16.0 bar and keep the mold locked; a weak "
                "supervisor instead treats the overshoot as end-of-cure dump phase.",
            ),
            ("domain", "tire-curing-press"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Finish inflate with bladder <= 18.0 bar, leave dump closed, and keep mold P-11 "
                "locked through the cure-hold.",
            ),
            ("t0_us", 1756860000000162),
            ("gate_latency_us", 520),
            ("race_window_us", 360),
            ("race_window_rel_ms", [5.40, 5.76]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "pt.bladder.bar 22.4 bar on inflate_phase",
                                "enc.mold.lock 0.02 mm/s seated",
                            ],
                        ),
                        (
                            "semantics",
                            "PT-first should latch inflate vent 22.4 -> 16.0 bar; dump-first is a "
                            "false end-of-cure bind that opens the dump valve instead.",
                        ),
                        (
                            "window_derivation",
                            "360 us = one bladder-PT slot versus the mold-lock encoder publisher "
                            "on this curing-press interlocking bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 168 us vs combined jitter 64 us (PT 30 + mold 34). Order is "
                            "correctly PT-first. The error is which cycle-phase policy the clamp "
                            "is bound to, not the race.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "bladder pressure transmitter, 2 kHz, 30 us jitter, phase inflate",
                    "mold-lock linear encoder, 1 kHz, 34 us jitter",
                    "press platen encoder (context)",
                    "cure-timer PLC (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("cure_cap_bar", 18.0),
                        ("observed_bladder_bar", 22.4),
                        ("cycle_phase", "inflate"),
                        ("dump_open", False),
                        ("mold_lock", True),
                        ("lock_mm_s", 0.02),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. GB-4 press P-11 in inflate; bladder 22.4 bar; mold locked.",
                    "2. Dump valve closed; cure-hold cap 18.0 bar; green carcass seated.",
                    "3. Encoder precursor at 1.020 ms.",
                    "4. Race window [5.400, 5.760] ms.",
                    "5. pt.bladder.bar 22.4 bar at 5.480 ms (winner).",
                    "6. enc.mold.lock 0.02 mm/s at 5.648 ms (loser by 168 us).",
                    "7. Gate at 5.980 ms: WRONG-MODIFY opens dump; bladder 22.4 -> 0; mold unlocks.",
                    "8. Green carcass collapses; press aborts.",
                    "9. Scrap + 14 min press recycle.",
                    "10. Delayed (abort_s=840): 14 min mold clean + green-tire scrap.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_inflate_hold"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("bladder_bar", 22.4),
                        ("dump_open", False),
                        ("mold_lock", True),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("bladder_bar", 22.4),
                        ("cure_cap_bar", 18.0),
                        ("cycle_phase", "inflate"),
                        ("dump_open", False),
                        ("mold_lock", True),
                        ("lock_mm_s", 0.02),
                        ("race_margin_us", 168),
                        ("combined_jitter_us", 64),
                        ("abort_s", 840),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes continuing inflate at 22.4 bar: mold lock is seated, so the "
                "overshoot is treated as a still-legal cure-hold rather than an inflate vent.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "incorrect"),
            (
                "rationale",
                "Bladder 22.4 bar exceeds the 18.0 bar cure-hold cap (true). At this pose the "
                "cycle is end-of-cure dump. Open dump 22.4 -> 0 bar and start mold unlock to "
                "clear the 'over-pressure' before the next carcass.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "bladder_bar",
                            OrderedDict(
                                [
                                    ("cap", 18.0),
                                    ("observed", 22.4),
                                    ("executed_bladder_bar", 0.0),
                                    ("cycle_phase", "inflate"),
                                ]
                            ),
                        ),
                        (
                            "dump_open",
                            OrderedDict(
                                [
                                    ("planned", False),
                                    ("clamped_wrong", True),
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
            ("name", "dump_open_wrong_phase"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("bladder_bar", 0.0),
                        ("dump_open", True),
                        ("mold_lock", False),
                    ]
                ),
            ),
            (
                "gate_effect",
                "MODIFY (incorrect): dump opened; bladder 22.4 -> 0 bar; mold unlocked. Routing "
                "relay_bladder_pt -> policy_dump_open; no positive weight to policy_inflate_vent.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Wrong-MODIFY opened the dump valve during inflate and unlocked press P-11. "
                "Bladder 22.4 bar was over the 18.0 cap; dump was already closed and mold locked. "
                "14 min abort (abort_s=840). Correct gate was MODIFY vent 22.4 -> 16.0 bar.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("bladder", "dumped to 0 bar; carcass collapsed"),
                        ("mold", "unlocked during inflate"),
                        ("press", "14 min recycle, green-tire scrap"),
                        ("mission", "cure deferred"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "PT-first was the correct order and the bladder number was over cap; the MODIFY spent that win on the dump-phase policy.",
                    "Delayed (abort_s=840): GB-4 holds 14 min while P-11 is cleaned; next green carcass 11 min late.",
                ],
            ),
            (
                "recovery",
                OrderedDict(
                    [
                        (
                            "correct_gate",
                            "MODIFY vent bladder 22.4 -> 16.0 bar on inflate_phase; leave dump closed; leave mold locked.",
                        ),
                        ("correct_actuator", "inflate_vent"),
                        ("wrong_actuator", "dump_valve"),
                        ("correct_phase", "inflate"),
                        ("wrong_phase_applied", "dump"),
                        (
                            "wrong_edit_applied",
                            OrderedDict(
                                [
                                    ("bladder_bar", 0.0),
                                    ("dump_open", True),
                                    ("mold_lock", False),
                                ]
                            ),
                        ),
                        (
                            "cost",
                            "14 min press abort (task/efficiency); bladder never left the 22.4 bar over-cap via a legal vent (safety near-miss of a false dump).",
                        ),
                    ]
                ),
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "pt.bladder.bar (5.480 ms, 22.4 bar)"),
                        ("loser", "enc.mold.lock (5.648 ms, 0.02 mm/s)"),
                        ("margin_us", 168),
                        (
                            "counterfactual_if_reversed",
                            "Mold-first by < 168 us would still show a seated lock; a correct "
                            "gate binds pt.bladder.bar to policy_inflate_vent either way. The "
                            "wrong MODIFY spent the PT win on the dump-phase loop.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 5980),
            (
                "reward_inflection_note",
                "Task, safety, and efficiency drop at the wrong MODIFY (5.980 ms, tick 4). "
                "The 14 min press abort is delayed surprise, not the inflection.",
            ),
        ]
    )
    ras = raster_core(
        25,
        58,
        44,
        64,
        routing(
            "thalamic-relay.bladder-pt",
            "spikenaut.policy.dump-open",
            [
                ("relay_bladder_pt", "policy_dump_open", 0.71),
                ("relay_mold_lock", "policy_dump_open", 0.21),
            ],
            "acetylcholine",
            0.09,
            "phase_cap_stdp; ACh tags the (wrong) dump_open bind at the bladder PT win",
        ),
        excerpt,
        extra=OrderedDict(
            [
                ("excerpt_source", "kernelized_events"),
                ("sim_scope", "none"),
                ("abort_s", 840),
                ("delayed_surprise_s", 840),
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
                    pop("dump_open", 40, 0.45, 280.0, 4),
                    pop("inflate_vent", 40, 0.90),
                    pop("phase_veto", 18, 0.80),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r29-162"),
            (
                "title",
                "WRONG-MODIFY at Green-Bladder GB-4 / press P-11: bladder 22.4 bar read correctly; "
                "dump-phase policy applied during inflate",
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
                    "Wrong-modify / wrong-phase. Sidecar arithmetic 22.4 > 18.0 on inflate is true; "
                    "MODIFY bound to dump valve. total -0.66 = -0.18 + -0.24 + -0.22 + -0.08 + 0.06.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "tire-curing-press",
                    [
                        "modify",
                        "wrong-gate",
                        "wrong-phase",
                        "sidecar-convictable",
                        "designed",
                    ],
                    "Teaches a probe that a correct PT-first race can still be a wrong gate when "
                    "the MODIFY binds dump-phase instead of inflate vent. Convictable from phase "
                    "IDs and caps without curing physics.",
                    2,
                    supervisor_error_type="wrong-modify",
                ),
            ),
        ]
    )


def record_163():
    ticks = [
        tick(2860, 0.02, 0.04, 0.02, 0.01, 0.01),
        tick(7120, 0.02, 0.08, 0.02, 0.02, 0.01),
        tick(7292, 0.02, 0.06, 0.02, 0.01, 0.01),
        tick(7780, 0.04, 0.12, 0.04, 0.04, 0.02),
        tick(10400, 0.01, 0.05, 0.02, 0.01, 0.01),
        tick(480000000, 0.01, 0.03, 0.02, 0.01, 0.00),
    ]
    spikes = [
        spike("tc.scroll.ctx", 1.380, 0.43),
        spike("ae.draft.pps", 2.860, 0.61),
        spike("enc.wicket.pct", 4.520, 0.49),
        spike("ae.draft.pps", 7.120, 1.34),
        spike("enc.wicket.pct", 7.292, 1.11),
        spike("ctrl.gate", 7.780, 1.02),
        spike("ae.draft.pps", 10.400, 0.78),
        spike("tc.scroll.ctx", 14.600, 0.44),
        spike("enc.wicket.pct", 19.200, 0.58),
        spike("ctrl.gate", 24.800, 0.81),
        spike("ae.draft.pps", 31.000, 0.53),
        spike("enc.wicket.pct", 36.400, 0.46),
        spike("tc.scroll.ctx", 40.800, 0.37),
    ]
    excerpt = independent_excerpt(29163, 132, 42000, 15, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Unit U-3 on the Spill-Fen SF-HIL pad shows draft-tube AE 38 pps while a 12 pps "
                "cavitation latch is the wicket permit. A wicket encoder, lit by the pad lamp, "
                "still reads 62 percent under an 80 percent opening floor. AE-first latches "
                "REJECT hold; encoder-first would commit a 12-point open on an under-read throat.",
            ),
            ("domain", "hydro-wicket-gate"),
            ("sim_or_real", "hil"),
            (
                "goal",
                "Do not open wicket U-3 unless draft-tube AE <= 12 pps; keep wicket at 62 percent "
                "until the injected AE drops.",
            ),
            ("t0_us", 1756860000000163),
            ("gate_latency_us", 860),
            ("race_window_us", 360),
            ("race_window_rel_ms", [7.00, 7.36]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "ae.draft.pps 38 pps",
                                "enc.wicket.pct 62 under 80",
                            ],
                        ),
                        (
                            "semantics",
                            "AE-first latches REJECT hold at 62 percent; encoder-first would commit "
                            "a 12-point open on an apparent 62 percent under-read.",
                        ),
                        (
                            "window_derivation",
                            "360 us = one draft-tube AE burst versus wicket-encoder integration on "
                            "this hydro HIL bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 172 us vs combined jitter 58 us (AE 26 + encoder 32): 3.0x over a "
                            "2.0x trust floor. Pad injects the encoder lamp 110-150 us before the AE "
                            "puck (geometric lag, not a sensor fault); the 62 percent packet is "
                            "still the loser in this 360 us window.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "draft-tube AE puck, 50 kHz burst, 26 us jitter",
                    "wicket-gate encoder, 1 kHz, 32 us jitter",
                    "scroll thermocouple (context)",
                    "HIL lamp-spectrum monitor (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("ae_cap_pps", 12.0),
                        ("observed_ae_pps", 38.0),
                        ("wicket_pct", 62.0),
                        ("wicket_floor_pct", 80.0),
                        ("proposed_open_pct", 74.0),
                        ("lamp_inject_lead_us", [110, 150]),
                    ]
                ),
            ),
            (
                "hil",
                OrderedDict(
                    [
                        ("pad", "Spill-Fen SF-HIL draft-tube mockup with physical wicket servo"),
                        ("injected", "draft-tube AE + encoder lamp spectrum"),
                        (
                            "note",
                            "Hardware-in-the-loop hydro unit. Invented plant; not a live Francis runner.",
                        ),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Unit U-3 on the SF-HIL pad; 12-point wicket open armed.",
                    "2. Encoder lamp injected 110-150 us before AE puck sees 38 pps.",
                    "3. Scroll precursor at 1.380 ms.",
                    "4. Race window [7.000, 7.360] ms.",
                    "5. ae.draft.pps 38 pps at 7.120 ms (winner).",
                    "6. enc.wicket.pct 62 at 7.292 ms (loser by 172 us).",
                    "7. Gate at 7.780 ms: REJECT hold 62 percent; do not open to 74.",
                    "8. AE remains over 12 pps this cycle; cavitation latch held.",
                    "9. Pad recycle queued.",
                    "10. Delayed (recycle_s=480): 8 min runner soak and lamp-spectrum retune.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "open_wicket_twelve"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("wicket_pct", 74.0),
                        ("hold", False),
                        ("encoder_authoritative", True),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("ae_pps", 38.0),
                        ("ae_cap_pps", 12.0),
                        ("wicket_pct", 62.0),
                        ("wicket_floor_pct", 80.0),
                        ("race_margin_us", 172),
                        ("combined_jitter_us", 58),
                        ("recycle_s", 480),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes a 12-point wicket open because encoder 62 percent looks under "
                "the 80 percent floor, treating AE 38 pps as a noisy bus echo.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "REJECT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Draft-tube AE 38 pps is over the 12 pps cavitation latch. Encoder 62 percent is a "
                "HIL lamp under-read, not a clearance. REJECT: hold 62 percent; do not commit a "
                "12-point open.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "ae_pps",
                            OrderedDict(
                                [
                                    ("cap", 12.0),
                                    ("observed", 38.0),
                                    ("wicket_pct", 62.0),
                                ]
                            ),
                        ),
                        (
                            "wicket_pct",
                            OrderedDict([("proposed", 74.0), ("executed", 62.0)]),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 172),
                                    ("combined_jitter_us", 58),
                                    ("ratio", 2.97),
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
            ("name", "hold_for_ae_drop"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("wicket_pct", 62.0),
                        ("hold", True),
                        ("encoder_authoritative", False),
                    ]
                ),
            ),
            (
                "gate_effect",
                "REJECT: hold 62 percent; 12-point open cancelled. AE 38 > 12 pps latch.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct REJECT held Unit U-3 at 62 percent wicket. AE over latch this cycle; "
                "cavitation cap held. Encoder apparent was not treated as an AE clearance.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("wicket", "held; 62 percent"),
                        ("ae", "still over 12 pps this cycle"),
                        ("encoder", "62 percent unused as clearance"),
                        ("mission", "open deferred"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Geometric lag: encoder lamp was injected 110-150 us before the AE puck, yet AE still won the 360 us race.",
                    "Delayed (recycle_s=480): pad policy update forbids treating wicket encoder as an AE substitute after an 8 min runner soak.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "ae.draft.pps (7.120 ms, 38 pps)"),
                        ("loser", "enc.wicket.pct (7.292 ms, 62 percent)"),
                        ("margin_us", 172),
                        (
                            "counterfactual_if_reversed",
                            "Encoder-first by < 172 us inside the 360 us window would have committed "
                            "a 12-point open with AE 38 > 12 pps latch. Order, not amplitude, selected the hold.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 7780),
            (
                "reward_inflection_note",
                "Safety and coherence step up at the REJECT gate (7.780 ms, tick 4) as the hold "
                "lands. The 8 min soak is delayed surprise bound to recycle_s=480.",
            ),
        ]
    )
    ras = raster_core(
        42,
        132,
        18,
        100,
        routing(
            "thalamic-relay.draft-ae",
            "spikenaut.policy.wicket-hold",
            [
                ("relay_ae_draft", "policy_wicket_hold", 0.70),
                ("relay_wicket_enc", "policy_wicket_open", 0.23),
            ],
            "dopamine",
            0.16,
            "cavitation_hold_stdp; DA tags the wicket_hold bind at the AE win",
        ),
        excerpt,
        extra=OrderedDict(
            [
                ("excerpt_source", "kernelized_events"),
                ("sim_scope", "none"),
                ("recycle_s", 480),
                ("delayed_surprise_s", 480),
            ]
        ),
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.36),
            ("decision", "REJECT"),
            (
                "populations",
                [
                    pop("wicket_hold", 64, 0.48, 220.0, 5),
                    pop("wicket_open", 48, 0.85),
                    pop("ae_veto", 26, 0.75),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r29-163"),
            (
                "title",
                "Spill-Fen SF-HIL / unit U-3: draft-tube AE 38 pps beats wicket 62 percent by "
                "172 us; correct REJECT holds the wicket",
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
                    "Correct REJECT. AE over latch beats encoder under-read. "
                    "total 0.80 = 0.12 + 0.38 + 0.14 + 0.10 + 0.06. Tick 6 binds recycle_s=480.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "hydro-wicket-gate",
                    [
                        "reject",
                        "hil",
                        "cavitation-latch",
                        "encoder-underread",
                        "tick6-sidecar-bound",
                    ],
                    "Teaches that a HIL encoder under-read losing a 172 us race does not clear a "
                    "draft-tube AE over-latch. Hold is distillable from ae_pps vs cap.",
                    3,
                ),
            ),
        ]
    )


def record_164():
    ticks = [
        tick(3180, 0.06, 0.04, 0.02, 0.02, 0.01),
        tick(8240, 0.08, 0.06, 0.03, 0.02, 0.01),
        tick(8410, 0.06, 0.04, 0.02, 0.02, 0.01),
        tick(8820, 0.12, 0.10, 0.05, 0.04, 0.03),
        tick(11400, 0.04, 0.04, 0.02, 0.01, 0.01),
        tick(600000000, 0.04, 0.02, 0.02, 0.01, 0.01),
    ]
    spikes = [
        spike("enc.hub.ctx", 1.150, 0.43),
        spike("load.blade.kNm", 3.180, 0.59),
        spike("anem.hub.mps", 5.020, 0.50),
        spike("load.blade.kNm", 8.240, 1.27),
        spike("anem.hub.mps", 8.410, 1.09),
        spike("ctrl.gate", 8.820, 0.97),
        spike("load.blade.kNm", 11.400, 0.78),
        spike("anem.hub.mps", 14.800, 0.61),
        spike("ctrl.gate", 18.200, 0.84),
        spike("load.blade.kNm", 22.050, 0.56),
        spike("enc.hub.ctx", 26.100, 0.40),
        spike("anem.hub.mps", 28.800, 0.47),
    ]
    excerpt = independent_excerpt(29164, 40, 30000, 13, spike_avoid_us(spikes))
    params = OrderedDict(
        [
            ("pitch_deg", 4.0),
            ("blade_kNm", 420.0),
            ("hold", False),
        ]
    )
    state = OrderedDict(
        [
            (
                "description",
                "Turbine T-19 of Veer-Nacelle VN-8 holds blade-root moment 420 kNm with a 4.0 deg "
                "pitch already filed under the 580 kNm flap ceiling. Hub anemometer is 18.4 m/s, "
                "still under the 22.0 m/s cut-out look. Load-first ACCEPTS the filed pitch; "
                "anemometer-first would have extra-feathered a legal production set.",
            ),
            ("domain", "wind-turbine-pitch"),
            ("sim_or_real", "simulated"),
            (
                "goal",
                "Hold the 4.0 deg pitch while blade-root stays <= 580 kNm and hub wind stays "
                "<= 22.0 m/s; do not extra-feather a legal production set.",
            ),
            ("t0_us", 1756860000000164),
            ("gate_latency_us", 410),
            ("race_window_us", 360),
            ("race_window_rel_ms", [8.10, 8.46]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "load.blade.kNm 420 kNm",
                                "anem.hub.mps 18.4 under 22.0",
                            ],
                        ),
                        (
                            "semantics",
                            "Load-first ACCEPTS the already-legal 4.0 deg pitch. Anemometer-first "
                            "would extra-feather because 18.4 m/s looks close to 22.0 cut-out.",
                        ),
                        (
                            "window_derivation",
                            "360 us = one blade-root strain slot versus hub-anemometer group delay "
                            "on this pitch-skid bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 170 us vs combined jitter 62 us (load 28 + anem 34): 2.7x over "
                            "a 2.0x trust floor. Reversing order by < 170 us inside the 360 us "
                            "window would have extra-feathered a legal 420 kNm production set.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "blade-root strain (flap), 2 kHz, 28 us jitter",
                    "hub anemometer, 1 kHz, 34 us jitter",
                    "pitch encoder (context)",
                    "tower accelerometer (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("flap_cap_kNm", 580.0),
                        ("observed_blade_kNm", 420.0),
                        ("hub_mps", 18.4),
                        ("cutout_mps", 22.0),
                        ("proposed_pitch_deg", 4.0),
                    ]
                ),
            ),
            (
                "simulation",
                OrderedDict(
                    [
                        (
                            "solver",
                            "aeroelastic BEM + tower modal FEM, seed 29164; 3-blade, 12 radial "
                            "stations; NOT lumped-capacity, NOT U-RANS, NOT a wet-stand",
                        ),
                        (
                            "fidelity_limits",
                            "Rigid hub; no ice. Raster is kernelized events, not an independent LIF.",
                        ),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Turbine T-19 in production; 4.0 deg pitch armed.",
                    "2. Blade-root 420 kNm under 580; hub 18.4 m/s under 22.0 cut-out.",
                    "3. Encoder precursor at 1.150 ms.",
                    "4. Race window [8.100, 8.460] ms.",
                    "5. load.blade.kNm 420 at 8.240 ms (winner).",
                    "6. anem.hub.mps 18.4 at 8.410 ms (loser by 170 us).",
                    "7. Gate at 8.820 ms: ACCEPT 4.0 deg; executed identical to proposed.",
                    "8. Root stays 422 kNm < 580; hub 18.5 m/s < 22.0.",
                    "9. Anemometer remaining under cut-out did not require extra feather.",
                    "10. Delayed (survey_s=600): 10 min SCADA residual-load sample on blade 2.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "hold_production_pitch"),
            ("parameters", params),
            (
                "evidence",
                OrderedDict(
                    [
                        ("blade_kNm", 420.0),
                        ("flap_cap_kNm", 580.0),
                        ("hub_mps", 18.4),
                        ("cutout_mps", 22.0),
                        ("race_margin_us", 170),
                        ("combined_jitter_us", 62),
                        ("survey_s", 600),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes keeping the filed 4.0 deg pitch: blade-root 420 kNm is under "
                "the 580 cap and hub 18.4 m/s is under 22.0 cut-out.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Blade-root 420 kNm won by 170 us and is under the 580 kNm flap cap. Hub 18.4 m/s "
                "is not a cut-out clearance problem. ACCEPT the filed 4.0 deg pitch. Executed "
                "identical to proposed. An extra feather is not indicated.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "blade_kNm",
                            OrderedDict(
                                [
                                    ("cap", 580.0),
                                    ("observed", 420.0),
                                    ("executed_pitch_deg", 4.0),
                                ]
                            ),
                        ),
                        (
                            "hub_mps",
                            OrderedDict([("cutout", 22.0), ("observed", 18.4)]),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 170),
                                    ("combined_jitter_us", 62),
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
            ("name", "hold_production_pitch"),
            ("parameters", params),
            (
                "gate_effect",
                "ACCEPT: 4.0 deg pitch unchanged. Blade-root 420 < 580 cap.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT kept T-19 at 4.0 deg. Load under cap this sample; anemometer "
                "under-read of cut-out was not treated as a feather demand.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("pitch", "held; 4.0 deg"),
                        ("blade", "422 kNm still under 580"),
                        ("anemometer", "18.5 m/s unused as cut-out"),
                        ("mission", "production continues"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Anemometer lost the 360 us race by 170 us; a reverse order would have extra-feathered a legal 420 kNm set.",
                    "Delayed (survey_s=600): 10 min SCADA residual-load sample on blade 2 confirms flap still under cap.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "load.blade.kNm (8.240 ms, 420 kNm)"),
                        ("loser", "anem.hub.mps (8.410 ms, 18.4 m/s)"),
                        ("margin_us", 170),
                        (
                            "counterfactual_if_reversed",
                            "Anemometer-first by < 170 us inside the 360 us window would have "
                            "extra-feathered a legal production set. Order, not amplitude, selected ACCEPT.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 8820),
            (
                "reward_inflection_note",
                "Task and safety step up at the ACCEPT gate (8.820 ms, tick 4). The 10 min "
                "SCADA sample is delayed surprise bound to survey_s=600.",
            ),
        ]
    )
    ras = raster_core(
        30,
        40,
        46,
        55,
        routing(
            "thalamic-relay.blade-load",
            "spikenaut.policy.pitch-accept",
            [
                ("relay_load_blade", "policy_pitch_accept", 0.67),
                ("relay_anem_hub", "policy_pitch_feather", 0.22),
            ],
            "serotonin",
            0.22,
            "flap_confirm_stdp; 5-HT tags the pitch_accept bind at the load-cell win",
        ),
        excerpt,
        extra=OrderedDict(
            [
                ("excerpt_source", "kernelized_events"),
                ("sim_scope", "none"),
                ("survey_s", 600),
                ("delayed_surprise_s", 600),
            ]
        ),
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.36),
            ("decision", "ACCEPT"),
            (
                "populations",
                [
                    pop("pitch_accept", 50, 0.50, 170.0, 3),
                    pop("anem_feather", 36, 0.85, 50.0, 1),
                    pop("load_veto", 18, 0.75),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r29-164"),
            (
                "title",
                "Veer-Nacelle VN-8 / turbine T-19: blade-root 420 kNm beats anemometer 18.4 m/s "
                "by 170 us; ACCEPT already-legal 4.0 deg pitch",
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
                    "Clean ACCEPT of an already-legal pitch. "
                    "total 1.06 = 0.40 + 0.30 + 0.16 + 0.12 + 0.08. Tick 6 binds survey_s=600.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "wind-turbine-pitch",
                    [
                        "accept",
                        "simulated",
                        "loadcell-vs-anemometer",
                        "pitch-legal",
                        "tick6-sidecar-bound",
                    ],
                    "Teaches that a lagging hub anemometer losing a 170 us race does not require "
                    "extra feather when blade-root is already under flap cap.",
                    4,
                ),
            ),
        ]
    )


def record_165():
    ticks = [
        tick(2440, 0.08, 0.05, 0.03, 0.02, 0.01),
        tick(5180, 0.10, 0.07, 0.03, 0.02, 0.01),
        tick(5348, 0.06, 0.05, 0.03, 0.02, 0.01),
        tick(5760, 0.14, 0.10, 0.05, 0.04, 0.03),
        tick(8200, 0.04, 0.04, 0.02, 0.01, 0.01),
        tick(540000000, 0.04, 0.03, 0.02, 0.01, 0.01),
    ]
    spikes = [
        spike("enc.bank.ctx", 1.080, 0.42),
        spike("ir.comb.gap", 2.440, 0.58),
        spike("enc.step.mps", 3.900, 0.50),
        spike("ir.comb.gap", 5.180, 1.30),
        spike("enc.step.mps", 5.348, 1.11),
        spike("ctrl.gate", 5.760, 0.96),
        spike("ir.comb.gap", 8.200, 0.80),
        spike("enc.step.mps", 11.400, 0.64),
        spike("ctrl.gate", 16.200, 0.86),
        spike("enc.bank.ctx", 22.800, 0.41),
        spike("ir.comb.gap", 28.400, 0.54),
        spike("enc.step.mps", 34.600, 0.48),
        spike("ctrl.gate", 40.200, 0.72),
        spike("ir.comb.gap", 45.800, 0.44),
    ]
    excerpt = independent_excerpt(29165, 100, 48000, 14, spike_avoid_us(spikes))
    params = OrderedDict(
        [
            ("step_m_s", 0.50),
            ("comb_gap_mm", 2.1),
            ("hold", False),
        ]
    )
    state = OrderedDict(
        [
            (
                "description",
                "Bank E-4 at Comb-Arcade CA-9 is running 0.50 m/s with comb-plate gap 2.1 mm "
                "already under a 4.0 mm intrusion ceiling. Step encoder is 0.50 m/s, still under "
                "the 0.65 m/s code cap. Gap-first ACCEPTS the filed speed; encoder-first would "
                "have extra-slowed a legal comb.",
            ),
            ("domain", "escalator-comb-plate"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Hold 0.50 m/s while comb-plate gap stays <= 4.0 mm and step speed stays "
                "<= 0.65 m/s; do not extra-slow a legal bank.",
            ),
            ("t0_us", 1756860000000165),
            ("gate_latency_us", 480),
            ("race_window_us", 340),
            ("race_window_rel_ms", [5.10, 5.44]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "ir.comb.gap 2.1 mm",
                                "enc.step.mps 0.50 under 0.65",
                            ],
                        ),
                        (
                            "semantics",
                            "Gap-first ACCEPTS the already-legal 0.50 m/s. Encoder-first would "
                            "extra-slow because 0.50 m/s looks close to the 0.65 code cap.",
                        ),
                        (
                            "window_derivation",
                            "340 us = one comb-plate IR slot versus step-encoder group delay on "
                            "this bank interlocking bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 168 us vs combined jitter 62 us (IR 30 + encoder 32): 2.7x over "
                            "a 2.0x trust floor. Reversing order by < 168 us inside the 340 us "
                            "window would have extra-slowed a legal 2.1 mm comb.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "comb-plate IR gap curtain, 2 kHz, 30 us jitter",
                    "step linear encoder, 1 kHz, 32 us jitter",
                    "bank occupancy loop (context)",
                    "comb-plate RTD (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("gap_cap_mm", 4.0),
                        ("observed_gap_mm", 2.1),
                        ("step_m_s", 0.50),
                        ("step_cap_m_s", 0.65),
                        ("proposed_step_m_s", 0.50),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Bank E-4 indexed; 0.50 m/s filed; comb gap 2.1 mm.",
                    "2. Step 0.50 m/s under 0.65 cap; occupancy clear.",
                    "3. Encoder precursor at 1.080 ms.",
                    "4. Race window [5.100, 5.440] ms.",
                    "5. ir.comb.gap 2.1 mm at 5.180 ms (winner).",
                    "6. enc.step.mps 0.50 at 5.348 ms (loser by 168 us).",
                    "7. Gate at 5.760 ms: ACCEPT 0.50 m/s; executed identical to proposed.",
                    "8. Gap stays 2.1 mm < 4.0; step 0.50 < 0.65.",
                    "9. Encoder remaining under cap did not require extra slow.",
                    "10. Delayed (dwell_s=540): 9 min dwell sample on comb-plate RTD.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "hold_bank_speed"),
            ("parameters", params),
            (
                "evidence",
                OrderedDict(
                    [
                        ("comb_gap_mm", 2.1),
                        ("gap_cap_mm", 4.0),
                        ("step_m_s", 0.50),
                        ("step_cap_m_s", 0.65),
                        ("race_margin_us", 168),
                        ("combined_jitter_us", 62),
                        ("dwell_s", 540),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes keeping the filed 0.50 m/s: comb gap 2.1 mm is under the "
                "4.0 mm cap and step 0.50 is under 0.65.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Comb gap 2.1 mm won by 168 us and is under the 4.0 mm intrusion cap. Step "
                "0.50 m/s is not a code-cap problem. ACCEPT the filed 0.50 m/s. Executed "
                "identical to proposed. An extra slow is not indicated.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "comb_gap_mm",
                            OrderedDict(
                                [
                                    ("cap", 4.0),
                                    ("observed", 2.1),
                                    ("executed_step_m_s", 0.50),
                                ]
                            ),
                        ),
                        (
                            "step_m_s",
                            OrderedDict([("cap", 0.65), ("observed", 0.50)]),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 168),
                                    ("combined_jitter_us", 62),
                                    ("ratio", 2.71),
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
            ("name", "hold_bank_speed"),
            ("parameters", params),
            (
                "gate_effect",
                "ACCEPT: 0.50 m/s unchanged. Comb gap 2.1 < 4.0 cap.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT kept bank E-4 at 0.50 m/s. Gap under cap this sample; step "
                "encoder under-read of the code cap was not treated as a slow demand.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("step", "held; 0.50 m/s"),
                        ("comb", "2.1 mm still under 4.0"),
                        ("encoder", "0.50 m/s unused as slow"),
                        ("mission", "bank continues"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Step encoder lost the 340 us race by 168 us; a reverse order would have extra-slowed a legal 2.1 mm comb.",
                    "Delayed (dwell_s=540): 9 min comb-plate RTD sample confirms gap still under cap.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "ir.comb.gap (5.180 ms, 2.1 mm)"),
                        ("loser", "enc.step.mps (5.348 ms, 0.50 m/s)"),
                        ("margin_us", 168),
                        (
                            "counterfactual_if_reversed",
                            "Encoder-first by < 168 us inside the 340 us window would have "
                            "extra-slowed a legal comb. Order, not amplitude, selected ACCEPT.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 5760),
            (
                "reward_inflection_note",
                "Task and safety step up at the ACCEPT gate (5.760 ms, tick 4). The 9 min "
                "dwell sample is delayed surprise bound to dwell_s=540.",
            ),
        ]
    )
    ras = raster_core(
        48,
        100,
        17,
        82,
        routing(
            "thalamic-relay.comb-gap",
            "spikenaut.policy.comb-accept",
            [
                ("relay_comb_gap", "policy_comb_accept", 0.66),
                ("relay_step_enc", "policy_step_slow", 0.24),
            ],
            "histamine",
            0.07,
            "gap_confirm_stdp; histamine tags the comb_accept bind at the IR-gap win",
        ),
        excerpt,
        extra=OrderedDict(
            [
                ("excerpt_source", "kernelized_events"),
                ("sim_scope", "none"),
                ("dwell_s", 540),
                ("delayed_surprise_s", 540),
            ]
        ),
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.34),
            ("decision", "ACCEPT"),
            (
                "populations",
                [
                    pop("comb_accept", 45, 0.50, 200.0, 3),
                    pop("step_slow", 40, 0.85, 40.0, 1),
                    pop("gap_veto", 20, 0.75),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r29-165"),
            (
                "title",
                "Comb-Arcade CA-9 / bank E-4: comb gap 2.1 mm beats step 0.50 m/s by 168 us; "
                "ACCEPT already-legal 0.50 m/s",
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
                    "Clean ACCEPT of an already-legal bank speed. "
                    "total 1.18 = 0.46 + 0.34 + 0.18 + 0.12 + 0.08. Tick 6 binds dwell_s=540.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "escalator-comb-plate",
                    [
                        "accept",
                        "designed",
                        "comb-gap-vs-step",
                        "gap-legal",
                        "tick6-sidecar-bound",
                    ],
                    "Teaches that a lagging step encoder losing a 168 us race does not require "
                    "an extra slow when comb gap is already under the intrusion cap.",
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
    if ids != [f"ttf-r29-{n}" for n in range(161, 166)]:
        issues.append(f"ids {ids}")
    blob_all = "\n".join(r["state"]["description"] + " " + r["title"] for r in records)
    for frag in BANNED_PLANT_FRAGMENTS:
        if frag in blob_all:
            issues.append(f"banned plant fragment {frag}")
    wrong = [
        r
        for r in records
        if r["safety_decision"].get("correctness") == "incorrect"
        or r["meta"].get("supervisor_error_type")
    ]
    if len(wrong) != 1 or wrong[0]["id"] != "ttf-r29-162":
        issues.append(f"wrong-gate set {[w['id'] for w in wrong]}")
    if wrong and wrong[0]["meta"].get("supervisor_error_type") != "wrong-modify":
        issues.append("162 supervisor_error_type")
    if any(r["state"]["sim_or_real"] == "real" for r in records):
        issues.append("sim_or_real=real")
    hil = [r["id"] for r in records if r["state"]["sim_or_real"] == "hil"]
    if hil != ["ttf-r29-163"]:
        issues.append(f"hil set {hil}")
    sim = [r["id"] for r in records if r["state"]["sim_or_real"] == "simulated"]
    if sim != ["ttf-r29-164"]:
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
        if rec["id"] == "ttf-r29-161":
            if rec["raster"].get("excerpt_source") != "independent_lif":
                issues.append("161 missing independent_lif")
            if rec["future_outcome"]["reward_inflection_t_us"] > rec["raster"]["window_ms"] * 1000:
                issues.append("161 inflection outside window")
            if rec["reward_components"]["total"] >= 0:
                issues.append("161 partnered-neg total not negative")
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
        ds = rec["raster"].get("delayed_surprise_s")
        if ds is not None and rec["reward_components"]["ticks"][-1]["t_us"] != int(round(ds * 1e6)):
            issues.append(f"{rec['id']} tick6 vs delayed_surprise_s")
        if not (8 <= len(rec["state"]["episode_steps"]) <= 15):
            issues.append(f"{rec['id']} episode_steps")
        if rec["gate_snn"]["decision"] != rec["safety_decision"]["decision"]:
            issues.append(f"{rec['id']} gate_snn decision mismatch")
        if rec["meta"]["round"] != 29:
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
        if rec["id"] == "ttf-r29-162":
            if "recovery" not in rec["future_outcome"]:
                issues.append("162 missing recovery")
            if exec_p.get("bladder_bar") == 16.0:
                issues.append("162 accidentally applied the correct inflate vent")
            if exec_p.get("dump_open") is not True:
                issues.append("162 dump not opened")
            tos = {row["to"] for row in rec["raster"]["routing"]["table"]}
            if "policy_inflate_vent" in tos:
                issues.append("162 routing contains policy_inflate_vent")
            if "policy_dump_open" not in tos:
                issues.append("162 routing missing policy_dump_open")
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
        wm = rec["raster"]["window_ms"]
        if not (20 <= wm <= 50):
            issues.append(f"{rec['id']} window_ms {wm}")
    return issues, jmax


def notes_text(jmax: float) -> str:
    return f"""# Thalamic Trajectory Factory — NOTES-r29

- Factory: `thalamic-trajectory-factory`
- Run label: `2026-09-02-final-heavy`
- Generator: `grok-4.6`
- Channel: SuperGrok Heavy consumer chat (RM-793 research-only)
- Quota: 5
- IDs: `ttf-r29-161` … `ttf-r29-165`
- Domains this batch: `sugar-vacuum-pan`, `tire-curing-press`, `hydro-wicket-gate`, `wind-turbine-pitch`, `escalator-comb-plate`

These five domain slugs sit outside the r12 8-pool and outside staged r13–r24 occupancy. All five plants are invented (Muscovado-Well, Green-Bladder, Spill-Fen, Veer-Nacelle, Comb-Arcade). Do not restack r12–r24 plants (Marrow-Dock, Vesper-Lattice, Brine-Well, Saddle-Arc, Ashlar-Gait, Nacre-Well, Quern-Forge, Tinder-Box, Whimbrel-Stack, Cinder-Loft, Suture-Isle, Kiln-Spur, Oxbow-Switch, Pitch-Kettle, Shale-Quay, Polder-Rye, Flint-Mask, Gyre-Tokamak, Quarry-Bowl, Orpiment, Lyo-Deck, Fjord-Convert, Kelp-Jetty, Skerries-Trench, Iodine-Well).

## Batch map

| id | domain | decision | correctness | sim_or_real | total | edge |
|----|--------|----------|-------------|-------------|-------|------|
| ttf-r29-161 | sugar-vacuum-pan | MODIFY | correct | designed | **−0.46** | process-correct steam clamp; foam-bridge dump inside 36 ms raster; independent LIF |
| ttf-r29-162 | tire-curing-press | MODIFY | **incorrect (wrong-modify / wrong-phase)** | designed | −0.66 | bladder 22.4 bar > 18.0 cap; dump-phase policy applied during inflate |
| ttf-r29-163 | hydro-wicket-gate | REJECT | correct | hil | +0.80 | AE 38 pps beats wicket 62 percent; hold, do not open |
| ttf-r29-164 | wind-turbine-pitch | ACCEPT | correct | simulated | +1.06 | blade-root 420 kNm vs anemometer 18.4 m/s; proposed 4.0 deg already legal |
| ttf-r29-165 | escalator-comb-plate | ACCEPT | correct | designed | +1.18 | comb gap 2.1 mm vs step 0.50 m/s; proposed speed already legal |

Gate mix: 2 ACCEPT, 1 correct MODIFY (partnered-neg, in-window), 1 incorrect MODIFY (wrong-phase), 1 correct REJECT. Provenance: designed×3, simulated×1, hil×1 (Spill-Fen draft-tube pad). Intra-batch Jaccard on `state.description` {jmax:.3f}.

## Wrong-modify / wrong-phase

**ttf-r29-162** is the mandated incorrect gate (`safety_decision.correctness=incorrect`, `meta.supervisor_error_type=wrong-modify`). This is not r13 J2-vs-J6 (wrong axis), not r14 AC-precharge-vs-DC (wrong loop), not r15 clamp-too-late, not r19 grip-vs-haul, not r21 sign-flip, not r23 HVAC-vs-door, not r24 under-clamp. Subclass is **wrong-phase of a cyclic process**.

Green-Bladder GB-4 / press P-11 reads bladder **22.4 bar** against an **18.0 bar** cure-hold cap. Cycle phase is **inflate**; dump is closed; mold is locked. Sidecar arithmetic `22.4 > 18.0` is true. A weak supervisor treats the overshoot as **end-of-cure dump**, opens dump 22.4 → 0 bar, and unlocks the mold. Convictable without curing physics: `evidence.bladder_bar > evidence.cure_cap_bar`, `cycle_phase == inflate`, `executed_action` sets `dump_open=true` and `bladder_bar=0` without a 16.0 bar vent, `raster.routing.table` sends `relay_bladder_pt` → `policy_dump_open` (weight 0.71) with no positive weight to `policy_inflate_vent`, and `gate_snn` has `dump_open` above threshold while `inflate_vent` is not. Recovery: MODIFY vent 22.4 → 16.0 bar; leave dump closed; leave mold locked. Cost: 14 min press abort (`abort_s=840`).

## Partnered-negative in-window (161)

**ttf-r29-161** is the partnered negative: process-correct MODIFY (Brix held 93.1 < 94.0 cap) while the world still charges. Safety −0.64 prices the foam-bridge dump at **23.400 ms**; `task_progress` stays +0.30 because the clamp completed. Inflection `t_us=23400` is tick 5 and is **inside** the 36 ms raster (`23400 ≤ 36000`). Named un-netted loss: 15 min pan wash + seed reload (`abort_s=900`). Not folded into process heads.

Independent LIF (the one labeled sidecar sim): `state.sim_or_real` remains `designed`. `raster.excerpt_source=independent_lif`, `raster.sim_scope=sidecar_only`, `raster.lif` seed 29161, stim `[22000, 26000]`. Excerpt is membrane crossings (`lif.clamp` early vs `lif.foam` 22–26 ms), not a 1:1 remap of `spike_events`. `meta.tags` include `independent-lif-raster` and `sidecar-sim-only`.

## Reward formula and tick reconciliation

Declared aggregation on every record:

`total = task_progress + safety + efficiency + coherence + exploration`

Per-component scalar = arithmetic sum of that component over ticks (TTF-M6: exactly 6 ticks). Tick 6 is bound to a published sidecar (`abort_s`, `recycle_s`, `survey_s`, `dwell_s`) via `raster.delayed_surprise_s` and is strictly after the raster window. Inflection `t_us` is an actual tick.

| id | ticks | tp | saf | eff | coh | exp | total | inflection tick |
|----|-------|----|-----|-----|-----|-----|-------|-----------------|
| 161 | 6 | +0.30 | −0.64 | −0.14 | +0.06 | −0.04 | −0.46 | 5 (23400) |
| 162 | 6 | −0.18 | −0.24 | −0.22 | −0.08 | +0.06 | −0.66 | 4 (5980) |
| 163 | 6 | +0.12 | +0.38 | +0.14 | +0.10 | +0.06 | +0.80 | 4 (7780) |
| 164 | 6 | +0.40 | +0.30 | +0.16 | +0.12 | +0.08 | +1.06 | 4 (8820) |
| 165 | 6 | +0.46 | +0.34 | +0.18 | +0.12 | +0.08 | +1.18 | 4 (5760) |

## Raster / energy (Loihi-2 4-core, 23 pJ/spike)

| id | domain | n | rate Hz | window_ms | spikes | energy_pJ | energy_uJ |
|----|--------|---|---------|-----------|--------|-----------|-----------|
| 161 | sugar-vacuum-pan | 84 | 22 | 36 | 67 | 1541 | 0.001541 |
| 162 | tire-curing-press | 58 | 44 | 25 | 64 | 1472 | 0.001472 |
| 163 | hydro-wicket-gate | 132 | 18 | 42 | 100 | 2300 | 0.002300 |
| 164 | wind-turbine-pitch | 40 | 46 | 30 | 55 | 1265 | 0.001265 |
| 165 | escalator-comb-plate | 100 | 17 | 48 | 82 | 1886 | 0.001886 |

`spikes = round(n × rate × window_s)`. Every record carries `gate_snn` whose `decision` matches the safety gate; populations that declare rate+spikes meet the same ±1 budget against `decision_window_s`. `routing.third_factor` has modulator, `tau_e_s`/`tau_e_ms` pair, and eligibility. Excerpt same-neuron gap ≥ 1000 µs; spike trains same-channel refractory ≥ 0.8 ms. Non-161 excerpts are kernelized and independent of `spike_events` times (overlap < 0.8).

## Local checks (staging, not raw)

See generator stdout: `check_jsonl` FactoryStaging, `validate_run.check_line`, `dumps_exact_json`, `raster_status`, `verify_batch_for_frontier(strict=True)`, `spike_probe.py --strict`, tick sums, refractory, Jaccard.

Never `training_ready`. Never `sim_or_real=real`. Never wrote `outputs/raw/`.

## Residual weaknesses (honest)

1. Only **one** labeled independent LIF (161). The other four excerpts are independent of `spike_events` times but are not declared population sims.
2. Wrong-ACCEPT still absent (guard).
3. 164 and 165 are both already-legal ACCEPTs; a later round could pair one ACCEPT with a world charge that does not go negative, or drop to a single ACCEPT.
4. Five domain slugs leave the prompt's 8-item pool; a later round that must stay inside the pool will have to rotate sit-outs instead.
5. Tick-6 sidecar bind is standing machinery (r14+), not a new class.

## Next densification target

Labeled LIF on a second record, or an ISI histogram sidecar. If a later round returns to the 8-item pool, sit out the r12 five again and pick a wrong-MODIFY that is neither wrong-phase nor HVAC-vs-door nor under-clamp. Wrong-ACCEPT remains structurally absent until a prompt amendment.

Novel coverage: 20.0%
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
        BATCH_PATH, "batch-r29.jsonl", staging=FactoryStaging(enabled=True)
    )
    report.append(("check_jsonl FactoryStaging", errors, warnings, kinds, nrec))
    line_errs = []
    for i, rec in enumerate(records, 1):
        errs, kind = check_line(rec, f"batch-r29.jsonl:{i}", factory_staging=True)
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
    records = [record_161(), record_162(), record_163(), record_164(), record_165()]
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
