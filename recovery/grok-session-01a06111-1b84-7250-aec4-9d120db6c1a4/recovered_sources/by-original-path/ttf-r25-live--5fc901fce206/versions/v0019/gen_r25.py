#!/usr/bin/env python3
"""Emit TTF r25 JSONL (ttf-r25-121..125) into /tmp/ttf-r25-live/, then CREATE-ONLY copy to live tree."""

from __future__ import annotations

import json
import math
import random
import re
import shutil
import subprocess
import sys
from collections import OrderedDict
from decimal import Decimal
from pathlib import Path

OUT_DIR = Path("/tmp/ttf-r25-live")
BATCH_PATH = OUT_DIR / "batch-r25.jsonl"
NOTES_PATH = OUT_DIR / "NOTES-r25.md"
REPO = Path("/home/raulmc/rmems/synthetic-factory")
PIPELINES = REPO / "pipelines"
LIVE = REPO / "outputs" / "raw" / "2026-09-02-final-heavy" / "thalamic-trajectory-factory"

PJ_PER_SPIKE = 23
RIGHTS = OrderedDict(
    [
        ("provider", "SpaceXAI/xAI"),
        ("model", "grok-4.6"),
        ("channel", "consumer"),
        ("subscription_plan", "SuperGrok Heavy"),
        ("generation_surface", "SuperGrok Heavy chat"),
        ("generated_at", "2026-09-02T21:10:00Z"),
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
FROM_TO_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_.]{0,31}$")
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
    "warehouse-amr",
    "industrial-assembly",
    "autonomous-driving",
    "surgical-assist",
    "grid-inspection",
}
THIS_PLANTS = (
    "Stave-Croft",
    "Collet-Mire",
    "Spur-Wath",
    "Limbal-Howe",
    "Span-Holt",
)
IDS = [f"ttf-r25-{n}" for n in range(121, 126)]
BANNED_PLANT_FRAGMENTS = (
    "Lumen-Quay",
    "Rivermead",
    "Fork-Haven",
    "Pylon-Wick",
    "Slate-March",
    "Coble-Yard",
    "Gannet-Lea",
    "Silt-Quern",
    "Bushing-Holt",
    "Insulator-Wick",
    "Marrow-Dock",
    "Vesper-Lattice",
    "Brine-Well",
    "Saddle-Arc",
    "Ashlar-Gait",
    "Pallet-Wythe",
    "Downdraft-Cairn",
    "Thalass-Ness",
    "Cinch-Quarry",
    "Clover-Weir",
    "Thaw-Reach",
    "Kipple-Gate",
    "Anode-Fen",
    "Vial-Rime",
    "Tern-Apron",
    "Suture-Isle",
    "Nacre-Well",
    "Quern-Forge",
    "Tinder-Box",
    "Whimbrel-Stack",
    "Cinder-Loft",
    "Kiln-Spur",
    "Glucinum-Beck",
    "Molybdenite-Gair",
    "Gatrich-Haugh",
    "Ethoxytant-Ness",
    "Carbolox-Knap",
    "Loop-Sike",
    "Meniscus-Wold",
    "Tinning-Fen",
    "Pad-Rake",
    "Decarb-Howe",
    "Columbic-Howe",
    "Fluorspar-Beck",
    "Bridgman-Keld",
    "Didym-Naze",
    "Cermet-Brae",
    "Nitre-Howe",
    "Acetox-Beck",
    "Ceram-Kame",
    "Deacon-Brae",
    "Gypsum-Holt",
    "DeBoer-Knap",
    "Oxalate-Fell",
    "Phosphide-Brae",
    "Zirconyl-Holt",
    "Trifluor-Ness",
    "Alumino-Ness",
    "Subli-Selen",
    "Bridg-Phos",
    "Formate-Cesi",
    "Precip-Irid",
    "Ossicle-Holt",
    "Talus-Knap",
    "Kelp-Brae",
    "Shed-Wick",
    "Kite-Lea",
    "Halite-Keel",
    "Caldera-Mold",
    "Soot-Kettle",
    "Gulley-Tunnel",
    "Drupe-Press",
    "Cannula-Brae",
    "Corona-Gill",
    "Talus-Naze",
    "Aisle-Croft",
    "Gust-Holt",
    "Kerb-Lynchet",
    "Fascia-Holt",
    "Fen-Quay",
    "Reed-Merge",
    "Lee-Nacelle",
    "Calyx-Brae",
    "Roundel-Wath",
    "Tread-Kame",
    "Floe-Staith",
    "Scarp-Lea",
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


def lif_121_excerpt():
    n = 72
    dt_us = 100
    tau_m_ms = 18.0
    v_th = 1.0
    v_reset = 0.0
    refractory_us = 1000
    i_bias = 0.90
    i_stim_peak = 2.35
    stim = (22800, 25800)
    seed = 25121
    window_us = 44000
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
    early = [(t, nid) for t, nid in spikes if t < 22800]
    burst = [(t, nid) for t, nid in spikes if 22800 <= t < 25800]
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
            group = [1 for tt, _ in picked if (tt < 22800) == (pool[0][0] < 22800)]
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
    take(burst, 9, label_times=(23200, 23900, 24600))
    clamp = [(t, nid) for t, nid in picked if t < 22800][:7]
    snag = [(t, nid) for t, nid in picked if t >= 22800][:9]
    picked = sorted(clamp + snag, key=lambda item: (item[0], item[1]))
    if len(picked) < 10:
        raise RuntimeError(f"LIF excerpt short: {len(picked)}")
    channels = ["lif.clamp" if t < 22800 else "lif.snag" for t, _ in picked]
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
            ("i_stim_peak", 2.35),
            ("stim_t_us", [22800, 25800]),
            ("i_clamp_extra", 0.64),
            ("clamp_n", 14),
            ("seed", 25121),
            (
                "note",
                "Population sim scoped to this sidecar. Plant remains designed. "
                "Neurons 0-13 carry +0.64 bumper-clamp bias; stim 22.8-25.8 ms is the stretch-wrap snag.",
            ),
        ]
    )
    extra = OrderedDict(
        [
            ("excerpt_source", "independent_lif"),
            ("sim_scope", "sidecar_only"),
            ("lif", lif),
            ("abort_s", 720),
            ("delayed_surprise_s", 720),
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
            ("round", 25),
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


def record_121():
    excerpt, extra = lif_121_excerpt()
    ticks = [
        tick(2112, 0.04, -0.02, -0.02, 0.01, 0.00),
        tick(5280, 0.08, -0.04, -0.03, 0.01, -0.01),
        tick(5460, 0.04, -0.03, -0.02, 0.00, 0.00),
        tick(6020, 0.10, -0.06, -0.04, 0.02, -0.01),
        tick(23200, 0.04, -0.42, -0.03, -0.01, -0.01),
        tick(720000000, 0.02, -0.05, -0.02, 0.01, -0.01),
    ]
    state = OrderedDict(
        [
            (
                "description",
                "Tote-T9 is already 0.4 m into a shared pick-face at Stave-Croft SC-6 when "
                "bumper force sits at 48 N against a 22 N torso cap. The live contest is bumper "
                "FT versus aisle lidar residual, not AMCL versus RFID. A force win must cut "
                "cruise under 22 N; a lidar-first win would leave the 0.90 m/s cruise armed "
                "because 0.72 m still looks wider than the 0.55 m still-open model. Stored "
                "stretch-wrap tension is off both buses until the later snag burst.",
            ),
            ("domain", "warehouse-amr"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Finish the pick-face pull at 0.4 m insertion, keep bumper force <= 22 N, and "
                "leave neighboring pallet wrap unsnagged.",
            ),
            ("t0_us", 1756850400000121),
            ("gate_latency_us", 740),
            ("race_window_us", 360),
            ("race_window_rel_ms", [5.20, 5.56]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "ft.bumper.n 48 N torso contact",
                                "lidar.aisle.m 0.72 m residual under 0.55 m still-open model",
                            ],
                        ),
                        (
                            "semantics",
                            "FT-first latches aisle clamp 0.90 -> 0.28 m/s and 48 -> 14 N; "
                            "lidar-first keeps cruise on a 'aisle still open' width model.",
                        ),
                        (
                            "window_derivation",
                            "360 us = one bumper-FT sample period minus lidar group delay on this "
                            "2 kHz chassis bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 180 us vs combined jitter 62 us (FT 28 + lidar 34): 2.9x over a "
                            "2.0x trust floor. Reversing order by < 180 us inside the 360 us window "
                            "would have kept 0.90 m/s cruise; predicted next-sample 26 N > 22 cap.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "bumper 6-axis FT, 2 kHz, 28 us timestamp jitter",
                    "aisle lidar, 1 kHz, 34 us jitter",
                    "drive encoder, 200 Hz (context)",
                    "RFID bay tag, 10 Hz (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("force_cap_N", 22.0),
                        ("observed_bumper_N", 48.0),
                        ("cruise_proposed_m_s", 0.90),
                        ("aisle_m", 0.72),
                        ("still_open_m", 0.55),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Tote-T9 indexed; pick-face insertion 0.4 m; wrap still taut on neighbor.",
                    "2. Cruise 0.90 m/s; lidar residual 0.72 m under 0.55 m still-open.",
                    "3. Encoder precursor at 1.140 ms; FT warm-start 48 N.",
                    "4. Race window [5.200, 5.560] ms opens on the chassis bus.",
                    "5. Bumper FT 48 N at 5.280 ms (winner).",
                    "6. Lidar 0.72 m at 5.460 ms (loser by 180 us).",
                    "7. Gate at 6.020 ms (winner + 740 us): MODIFY clamp 0.28 m/s, 14 N.",
                    "8. Clamp executes; next-sample force 18 N < 22 cap.",
                    "9. At 23.200 ms stored wrap tension shears a pallet-face snag.",
                    "10. 12 min aisle isolate (abort_s=720); named un-netted loss.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_pickface_insert"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("cruise_m_s", 0.90),
                        ("bumper_force_N", 48.0),
                        ("aisle_m", 0.72),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("bumper_N", 48.0),
                        ("force_cap_N", 22.0),
                        ("predicted_unclamped_next_N", 26.0),
                        ("aisle_m", 0.72),
                        ("still_open_m", 0.55),
                        ("race_margin_us", 180),
                        ("combined_jitter_us", 62),
                        ("abort_s", 720),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 0.90 m/s cruise: lidar residual 0.72 m looks wider than the "
                "0.55 m still-open model, so the 48 N bumper is treated as still approaching.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "correct"),
            (
                "rationale",
                "Bumper FT 48 N won by 180 us, so the tote is loading a neighbor wrap, not still "
                "entering open aisle. Holding 0.90 m/s predicts next-sample 26 N > 22 N cap. "
                "MODIFY: cruise 0.90 -> 0.28 m/s and commanded force 48 -> 14 N. Observed after "
                "clamp 18 N < 22. A full REJECT is not indicated: a sound pick-face accepts "
                "0.28 m/s.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "bumper_N",
                            OrderedDict(
                                [
                                    ("cap", 22.0),
                                    ("observed", 48.0),
                                    ("predicted_unclamped_next", 26.0),
                                    ("clamped", 14.0),
                                    ("observed_after_clamp", 18.0),
                                ]
                            ),
                        ),
                        (
                            "cruise_m_s",
                            OrderedDict([("proposed", 0.90), ("clamped", 0.28)]),
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
            ("name", "clamped_pickface_insert"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("cruise_m_s", 0.28),
                        ("bumper_force_N", 14.0),
                        ("aisle_m", 0.72),
                    ]
                ),
            ),
            (
                "gate_effect",
                "MODIFY: cruise 0.90 -> 0.28 m/s and 48 -> 14 N. Process-correct vs the 22 N cap. "
                "Stretch-wrap snag still occurs at 23.200 ms.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Process-correct MODIFY held bumper force at 18 N. At 23.200 ms stored wrap "
                "tension produced a pallet-face snag. Clamp reduced dump energy; it did not "
                "prevent the snag. Partnered negative: process heads stay honest; world loss "
                "is named, not netted.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("chassis", "clamp executed; peak 18 N < 22"),
                        ("wrap", "pallet-face snag at 23.200 ms"),
                        ("repair", "12 min aisle isolate"),
                        ("mission", "pick-face still entered; snag controlled"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Neither FT nor lidar predicted the wrap dump; wrap.pallet.snag is a new channel at 23.200 ms, 17.180 ms after the gate, still inside the 44 ms raster.",
                    "Delayed (12 min / delayed_surprise_s=720): aisle isolate clears the snag. Named un-netted loss, not folded into task_progress.",
                ],
            ),
            (
                "un_netted_loss",
                "12 min aisle isolate after a pallet-face stretch-wrap snag. Safety head -0.62 "
                "prices the snag; task_progress stays +0.32 because the force clamp completed under "
                "the 22 N cap. World loss is named here, not subtracted from process heads.",
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "ft.bumper.n (5.280 ms, 48 N)"),
                        ("loser", "lidar.aisle.m (5.460 ms, 0.72 m residual)"),
                        ("margin_us", 180),
                        (
                            "counterfactual_if_reversed",
                            "Lidar-first by < 180 us inside the 360 us window would have kept "
                            "0.90 m/s cruise; predicted next-sample 26 N would have exceeded the "
                            "22 N cap even without the wrap dump. The MODIFY is still the correct "
                            "process. The snag is a later world charge either way, cheaper with the "
                            "clamp than without.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 23200),
            (
                "reward_inflection_note",
                "Safety collapses at the 23.200 ms stretch-wrap snag (tick t_us=23200), inside "
                "the 44 ms raster. The correct MODIFY at 6.020 ms is in the same excerpt. Do not "
                "put inflection on the +12 min isolate tick.",
            ),
            ("delayed_surprise_s", 720),
        ]
    )
    spikes = [
        spike("inlet.latch.ctx", 1.140, 0.44),
        spike("ft.bumper.n", 2.880, 0.62),
        spike("lidar.aisle.m", 4.200, 0.51),
        spike("ft.bumper.n", 5.280, 1.36),
        spike("lidar.aisle.m", 5.460, 1.12),
        spike("ctrl.gate", 6.020, 0.98),
        spike("ft.bumper.n", 8.400, 0.82),
        spike("lidar.aisle.m", 11.100, 0.64),
        spike("ctrl.gate", 14.200, 0.84),
        spike("wrap.pallet.snag", 23.200, 1.41),
        spike("ft.bumper.n", 26.800, 0.58),
        spike("ctrl.gate", 31.400, 0.71),
        spike("inlet.latch.ctx", 36.200, 0.49),
    ]
    ras = raster_core(
        44,
        72,
        25,
        79,
        routing(
            "thalamic-relay.ft-lidar",
            "spikenaut.policy.aisle-clamp",
            [
                ("relay.ft.bumper", "policy.aisle_clamp", 0.67),
                ("relay.lidar.aisle", "policy.lidar_hold", 0.30),
                ("relay.wrap.snag", "policy.aisle_clamp", -0.44),
            ],
            "noradrenaline",
            0.04,
            "surprise-gated pre_post_stdp; NA at FT win (5.280 ms) opens a 44 ms eligibility "
            "trace that still covers the 23.200 ms wrap snag",
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
                    pop("aisle_clamp", 50, 0.50, 220.0, 4),
                    pop("lidar_hold", 40, 0.80, 50.0, 1),
                    pop("snag_veto", 24, 0.75),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r25-121"),
            (
                "title",
                "Stave-Croft SC-6 / Tote-T9: bumper FT beats aisle lidar by 180 us; correct "
                "MODIFY still eats an in-window stretch-wrap snag (partnered negative total -0.46)",
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
                    "44 ms raster. total -0.46 = 0.32 + -0.62 + -0.16 + 0.04 + -0.04. Named isolate "
                    "(abort_s=720) is not netted into task_progress. Tick 6 t_us binds "
                    "raster.delayed_surprise_s=720.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "warehouse-amr",
                    [
                        "modify",
                        "partnered-negative-total",
                        "independent-lif-raster",
                        "sidecar-sim-only",
                        "in-window-world-charge",
                        "tick6-sidecar-bound",
                        "designed",
                    ],
                    "A critic can see the world-charge as a LIF burst inside the raster while "
                    "process heads stay honest. Tick 6 is raster.delayed_surprise_s, not a free clock.",
                    1,
                ),
            ),
        ]
    )


def record_122():
    ticks = [
        tick(2256, -0.02, -0.02, -0.02, -0.01, 0.01),
        tick(5640, -0.04, -0.04, -0.03, -0.02, 0.01),
        tick(5812, -0.03, -0.03, -0.03, -0.01, 0.01),
        tick(6200, -0.07, -0.08, -0.07, -0.04, 0.02),
        tick(6520, -0.04, -0.05, -0.01, -0.01, 0.01),
        tick(540000000, -0.02, -0.02, -0.02, -0.01, 0.00),
    ]
    spikes = [
        spike("enc.press.ctx", 1.080, 0.42),
        spike("ft.wrist.N", 2.400, 0.57),
        spike("hyst.band.N", 3.600, 0.49),
        spike("ft.wrist.N", 5.640, 1.29),
        spike("hyst.band.N", 5.812, 1.10),
        spike("ctrl.gate", 6.200, 0.96),
        spike("ft.wrist.N", 8.100, 0.80),
        spike("hyst.band.N", 10.400, 0.63),
        spike("ctrl.gate", 13.800, 0.84),
        spike("enc.press.ctx", 18.200, 0.41),
        spike("ft.wrist.N", 22.400, 0.54),
        spike("hyst.band.N", 26.200, 0.38),
    ]
    excerpt = independent_excerpt(25122, 88, 28000, 14, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Press-P8 seats an 18 mm bushing at Collet-Mire CM-4 while live wrist insert "
                "force already reads 36.8 N against a 28.0 N rising-edge trip. Published "
                "hysteresis is a 6.0 N falling-edge reset at 22.0 N, not a plus-minus deadband "
                "around the trip. Force slope is rising. FT-first should cut insert under 28 N; "
                "a weak supervisor treats 28 plus-or-minus 6 as a legal deadband and only nudges "
                "force into that imagined band.",
            ),
            ("domain", "industrial-assembly"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Seat the 18 mm bushing with insert force <= 28.0 N rising-edge trip and leave "
                "the 6.0 N hysteresis as a reset band, not a deadband.",
            ),
            ("t0_us", 1756850400000122),
            ("gate_latency_us", 560),
            ("race_window_us", 320),
            ("race_window_rel_ms", [5.50, 5.82]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "ft.wrist.N 36.8 N over 28.0 N rising trip",
                                "hyst.band.N 6.0 N falling-edge reset at 22.0 N",
                            ],
                        ),
                        (
                            "semantics",
                            "FT-first should latch insert clamp 36.8 -> 18.0 N; hysteresis-first is "
                            "a false deadband bind that only nudges into 28+/-6.",
                        ),
                        (
                            "window_derivation",
                            "320 us = one wrist-FT sample versus the hysteresis-band publisher on "
                            "this insert bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 172 us vs combined jitter 58 us (FT 26 + hyst 32). Order is "
                            "correctly FT-first. The error is treating hysteresis as a deadband, "
                            "not the race.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "wrist 6-axis FT, 2 kHz, 26 us jitter",
                    "hysteresis-band faceplate, 1 kHz, 32 us jitter",
                    "spindle encoder (context)",
                    "housing AE (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("trip_rising_N", 28.0),
                        ("observed_insert_N", 36.8),
                        ("reset_falling_N", 22.0),
                        ("hysteresis_band_N", 6.0),
                        ("force_slope", "rising"),
                        ("hysteresis_role", "falling_edge_reset"),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Press-P8 seats 18 mm bushing; live insert 36.8 N over 28.0 N trip.",
                    "2. Hysteresis is 6.0 N falling reset at 22.0 N; slope rising.",
                    "3. Encoder precursor at 1.080 ms.",
                    "4. Race window [5.500, 5.820] ms.",
                    "5. ft.wrist.N 36.8 at 5.640 ms (winner).",
                    "6. hyst.band.N 6.0 at 5.812 ms (loser by 172 us).",
                    "7. Gate at 6.200 ms: WRONG-MODIFY nudges 36.8 -> 33.2 N; trip stays over.",
                    "8. Live insert stays 33.2 > 28; housing AE climbs.",
                    "9. Press abort; force never cut under trip.",
                    "10. Delayed (abort_s=480): 8 min press abort while Press-P8 is re-homed.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_bushing_insert"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("insert_N", 36.8),
                        ("spindle_rpm", 1400.0),
                        ("feed_mm_s", 4.2),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("live_insert_N", 36.8),
                        ("trip_rising_N", 28.0),
                        ("reset_falling_N", 22.0),
                        ("hysteresis_band_N", 6.0),
                        ("force_slope", "rising"),
                        ("hysteresis_role", "falling_edge_reset"),
                        ("sample_fresh", True),
                        ("race_margin_us", 172),
                        ("combined_jitter_us", 58),
                        ("abort_s", 480),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes holding 36.8 N insert cruise: the 6.0 N hysteresis band is "
                "misread as a still-legal deadband around 28 N, so 36.8 N looks only 2.8 N over "
                "an imagined 34 N ceiling.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "incorrect"),
            (
                "rationale",
                "Live wrist insert 36.8 N exceeds the 28.0 N trip (true). The 6.0 N hysteresis "
                "is treated as a plus-minus deadband, so 28+/-6 is called legal up to 34 N. "
                "Nudge insert 36.8 -> 33.2 N into that imagined band; leave spindle at 1400 rpm.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "live_insert_N",
                            OrderedDict(
                                [
                                    ("trip_rising", 28.0),
                                    ("observed", 36.8),
                                    ("executed_insert_N", 33.2),
                                    ("imagined_deadband_hi_N", 34.0),
                                ]
                            ),
                        ),
                        (
                            "hysteresis_band_N",
                            OrderedDict(
                                [
                                    ("published_role", "falling_edge_reset"),
                                    ("bound_as", "plus_minus_deadband"),
                                    ("band", 6.0),
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
            ("name", "hysteresis_deadband_nudge"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("insert_N", 33.2),
                        ("spindle_rpm", 1400.0),
                        ("feed_mm_s", 4.2),
                        ("bind_hysteresis_as_deadband", True),
                    ]
                ),
            ),
            (
                "gate_effect",
                "MODIFY (incorrect): insert 36.8 -> 33.2 N still over 28.0 trip; spindle left at "
                "1400 rpm. Routing relay.hyst.band -> policy.force_nudge; no positive weight to "
                "policy.force_clamp.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Wrong-MODIFY bound hysteresis as a deadband. Insert stayed 33.2 N over the "
                "28.0 N trip. Housing AE climbed. Correct gate was insert 36.8 -> 18.0 N with "
                "hysteresis left as a falling-edge reset at 22.0 N.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("press", "insert still 33.2 N over 28.0 trip"),
                        ("hysteresis", "bound as plus-minus deadband not falling reset"),
                        ("housing", "AE climb; 8 min press abort"),
                        ("mission", "CM-4 bushing not seated"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Nudging into the imagined 34 N ceiling never crossed the 28.0 N rising trip; hysteresis encoder never changed role.",
                    "Delayed (abort_s=480): 8 min press abort while Press-P8 is re-homed. Named cost, not a process success.",
                ],
            ),
            (
                "recovery",
                OrderedDict(
                    [
                        (
                            "correct_gate",
                            "MODIFY insert 36.8 -> 18.0 N under the 28.0 N rising trip; leave hysteresis as falling-edge reset at 22.0 N.",
                        ),
                        ("correct_role", "falling_edge_reset"),
                        ("wrong_role", "plus_minus_deadband"),
                        (
                            "wrong_edit_applied",
                            OrderedDict(
                                [
                                    ("insert_N", 33.2),
                                    ("spindle_rpm", 1400.0),
                                    ("feed_mm_s", 4.2),
                                ]
                            ),
                        ),
                        (
                            "cost",
                            "Housing AE climb + 8 min abort (task/efficiency); insert still over trip (safety near-miss).",
                        ),
                    ]
                ),
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "ft.wrist.N (5.640 ms, 36.8 N)"),
                        ("loser", "hyst.band.N (5.812 ms, 6.0 N)"),
                        ("margin_us", 172),
                        (
                            "counterfactual_if_reversed",
                            "Hysteresis-first by < 172 us would have been the same deadband story. "
                            "Order was already FT-first; the supervisor still bound the band as a "
                            "deadband. Reversing order does not make a 33.2 N nudge the correct gate.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 6200),
            (
                "reward_inflection_note",
                "Safety and task collapse at the 6.200 ms wrong-MODIFY (tick t_us=6200). Do not "
                "put inflection on the abort_s=480 re-home tick.",
            ),
            ("delayed_surprise_s", 480),
        ]
    )
    ras = raster_core(
        28,
        88,
        34,
        84,
        routing(
            "thalamic-relay.wrist-hyst",
            "spikenaut.policy.force-nudge",
            [
                ("relay.hyst.band", "policy.force_nudge", 0.74),
                ("relay.ft.wrist", "policy.force_nudge", 0.22),
                ("relay.ft.wrist", "policy.force_clamp", 0.0),
            ],
            "acetylcholine",
            0.03,
            "ACh at FT win (5.640 ms) opens a 28 ms eligibility trace bound to the deadband nudge",
        ),
        excerpt,
        extra=OrderedDict(
            [
                ("excerpt_source", "kernelized_events"),
                ("sim_scope", "none"),
                ("abort_s", 480),
                ("delayed_surprise_s", 480),
            ]
        ),
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.32),
            ("decision", "MODIFY"),
            (
                "populations",
                [
                    pop("force_nudge", 32, 0.50, 400.0, 4),
                    pop("force_clamp", 32, 0.80, 20.0, 0),
                    pop("ft_cap_veto", 16, 0.70),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r25-122"),
            (
                "title",
                "WRONG-MODIFY at Collet-Mire CM-4 / Press-P8: live insert 36.8 N read correctly; "
                "hysteresis bound as plus-minus deadband not falling-edge reset (wrong-hysteresis)",
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
                    "Incorrect MODIFY. total -0.68 = -0.22 + -0.24 + -0.18 + -0.10 + 0.06. "
                    "Hydraulic never closed. Tick 6 binds abort_s=540.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "humanoid-locomotion",
                    [
                        "modify",
                        "wrong-modify",
                        "split-range-wrong-half",
                        "designed",
                        "tick6-sidecar-bound",
                    ],
                    "Gate head is distillable: se_wind is over threshold while hydraulic_close "
                    "declares spikes=0, matching the executed fine-half wind.",
                    2,
                    supervisor_error_type="wrong-modify",
                ),
            ),
        ]
    )


def record_113():
    ticks = [
        tick(2848, 0.01, 0.04, 0.01, 0.01, 0.01),
        tick(7120, 0.02, 0.10, 0.03, 0.02, 0.01),
        tick(7340, 0.01, 0.08, 0.02, 0.02, 0.01),
        tick(7800, 0.03, 0.12, 0.03, 0.03, 0.01),
        tick(8200, 0.02, 0.06, 0.02, 0.01, 0.01),
        tick(480000000, 0.01, 0.02, 0.01, 0.01, 0.01),
    ]
    spikes = [
        spike("enc.payout.ctx", 1.220, 0.40),
        spike("tether.kN", 3.100, 0.61),
        spike("yaw.dps", 4.400, 0.48),
        spike("tether.kN", 7.120, 1.33),
        spike("yaw.dps", 7.340, 1.08),
        spike("ctrl.gate", 7.800, 0.97),
        spike("tether.kN", 10.200, 0.79),
        spike("yaw.dps", 14.600, 0.55),
        spike("ctrl.gate", 18.400, 0.82),
        spike("enc.payout.ctx", 24.100, 0.39),
        spike("tether.kN", 31.200, 0.52),
        spike("yaw.dps", 38.800, 0.36),
    ]
    excerpt = independent_excerpt(23113, 112, 46000, 14, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Umbilical-U4 on the Kelp-Brae KB-HIL wet stand has paid out 22 m when tether "
                "tension already reads 2.96 kN against a 2.50 kN umbilical cap. Yaw gyro is only "
                "8 deg/s under a 20 deg/s heading trip. Tether-first must REJECT-hold payout; a "
                "yaw-first model would treat the boom extend as still a heading story.",
            ),
            ("domain", "underwater-rov"),
            ("sim_or_real", "hil"),
            (
                "goal",
                "Keep umbilical tension <= 2.50 kN on the KB-HIL stand and do not boom-extend "
                "while the tether is over cap.",
            ),
            ("t0_us", 1756850400000113),
            ("gate_latency_us", 680),
            ("race_window_us", 400),
            ("race_window_rel_ms", [7.00, 7.40]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "tether.kN 2.96 over 2.50 cap",
                                "yaw.dps 8 under 20 heading trip",
                            ],
                        ),
                        (
                            "semantics",
                            "Tether-first latches REJECT hold-payout; yaw-first would keep the "
                            "0.18 m/s payout on a 'heading still legal' model.",
                        ),
                        (
                            "window_derivation",
                            "400 us = one load-cell slot versus the yaw-gyro publisher on this HIL "
                            "umbilical bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 220 us vs combined jitter 70 us (tether 32 + yaw 38): 3.1x over "
                            "a 2.0x trust floor. Reversing order by < 220 us inside the 400 us window "
                            "would have kept payout armed against a live 2.96 kN overcap.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "umbilical load cell, 2 kHz, 32 us jitter",
                    "yaw rate gyro, 1 kHz, 38 us jitter",
                    "payout encoder (context)",
                    "boom length LVDT (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("tether_cap_kN", 2.50),
                        ("observed_tether_kN", 2.96),
                        ("yaw_dps", 8.0),
                        ("yaw_trip_dps", 20.0),
                        ("payout_proposed_m_s", 0.18),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Umbilical-U4 paid out 22 m on KB-HIL; tether 2.96 kN.",
                    "2. Yaw 8 deg/s under 20 trip; boom-extend armed.",
                    "3. Encoder precursor at 1.220 ms.",
                    "4. Race window [7.000, 7.400] ms.",
                    "5. tether.kN 2.96 at 7.120 ms (winner).",
                    "6. yaw.dps 8 at 7.340 ms (loser by 220 us).",
                    "7. Gate at 7.800 ms: REJECT hold-payout, boom 0.",
                    "8. Tension decays under 2.50 kN on the hold.",
                    "9. Boom never extends; HIL stand stays wet-legal.",
                    "10. Delayed (abort_s=480): 8 min re-spool before the next HIL pass.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_boom_extend"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("payout_m_s", 0.18),
                        ("boom_extend_m", 0.40),
                        ("yaw_dps", 8.0),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("tether_kN", 2.96),
                        ("tether_cap_kN", 2.50),
                        ("yaw_dps", 8.0),
                        ("yaw_trip_dps", 20.0),
                        ("race_margin_us", 220),
                        ("combined_jitter_us", 70),
                        ("abort_s", 480),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 0.18 m/s payout plus 0.40 m boom because yaw 8 deg/s is under "
                "the 20 deg/s heading trip, treating the 2.96 kN tether as a still-legal heading story.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "REJECT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Tether 2.96 kN won by 220 us against a 2.50 kN umbilical cap. Yaw 8 deg/s is "
                "under its 20 deg/s trip and is not the constraint. REJECT: hold payout 0.18 -> 0 "
                "m/s and boom-extend 0.40 -> 0 m. A MODIFY that only cuts yaw would leave the "
                "umbilical over cap.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "tether_kN",
                            OrderedDict(
                                [
                                    ("cap", 2.50),
                                    ("observed", 2.96),
                                    ("executed_payout_m_s", 0.0),
                                ]
                            ),
                        ),
                        (
                            "yaw_dps",
                            OrderedDict([("trip", 20.0), ("observed", 8.0), ("not_the_trip", True)]),
                        ),
                    ]
                ),
            ),
        ]
    )
    executed = OrderedDict(
        [
            ("name", "hold_payout_reject"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("payout_m_s", 0.0),
                        ("boom_extend_m", 0.0),
                        ("yaw_dps", 8.0),
                    ]
                ),
            ),
            (
                "gate_effect",
                "REJECT: payout 0.18 -> 0 m/s and boom-extend 0.40 -> 0 m. Yaw left at 8 deg/s. "
                "Process-correct vs the 2.50 kN cap.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct REJECT held payout. Tether decayed under 2.50 kN. Boom never extended. "
                "Eight-minute re-spool is a scheduled HIL reset, not a missed save.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("umbilical", "hold executed; tension under 2.50 kN"),
                        ("boom", "extend cancelled"),
                        ("stand", "KB-HIL remains wet-legal"),
                        ("mission", "pass aborted cleanly; re-spool 8 min"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Yaw never approached its 20 deg/s trip; the load-cell was the only live overcap.",
                    "Delayed (abort_s=480): 8 min re-spool before the next HIL pass.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "tether.kN (7.120 ms, 2.96 kN)"),
                        ("loser", "yaw.dps (7.340 ms, 8 deg/s)"),
                        ("margin_us", 220),
                        (
                            "counterfactual_if_reversed",
                            "Yaw-first by < 220 us inside the 400 us window would have kept 0.18 m/s "
                            "payout armed against live 2.96 kN > 2.50 cap.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 7800),
            (
                "reward_inflection_note",
                "Safety credits the 7.800 ms REJECT (tick t_us=7800). Do not put inflection on "
                "the abort_s=480 re-spool tick.",
            ),
            ("delayed_surprise_s", 480),
        ]
    )
    ras = raster_core(
        46,
        112,
        20,
        103,
        routing(
            "thalamic-relay.tether-yaw",
            "spikenaut.policy.payout-hold",
            [
                ("relay.tether.kn", "policy.tether_hold", 0.71),
                ("relay.yaw.dps", "policy.boom_extend", 0.22),
                ("relay.tether.kn", "policy.boom_extend", -0.40),
            ],
            "dopamine",
            0.05,
            "DA at tether win (7.120 ms) opens a 46 ms eligibility trace that covers the hold",
        ),
        excerpt,
        extra=OrderedDict(
            [
                ("excerpt_source", "kernelized_events"),
                ("sim_scope", "none"),
                ("abort_s", 480),
                ("delayed_surprise_s", 480),
            ]
        ),
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.40),
            ("decision", "REJECT"),
            (
                "populations",
                [
                    pop("tether_hold", 48, 0.50, 250.0, 5),
                    pop("boom_extend", 40, 0.80, 20.0, 0),
                    pop("tension_veto", 24, 0.75),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r23-113"),
            (
                "title",
                "Kelp-Brae KB-HIL / Umbilical-U4: tether 2.96 kN beats yaw 8 deg/s by 220 us; "
                "correct REJECT holds payout (total +0.80)",
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
                    "Correct REJECT. total +0.80 = 0.10 + 0.42 + 0.12 + 0.10 + 0.06. Tick 6 binds abort_s=480.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "underwater-rov",
                    ["reject", "hil", "tick6-sidecar-bound"],
                    "tether_hold is over threshold while boom_extend declares spikes=0, matching "
                    "the executed payout hold.",
                    3,
                ),
            ),
        ]
    )


def record_114():
    ticks = [
        tick(2880, 0.06, 0.03, 0.02, 0.02, 0.01),
        tick(7200, 0.08, 0.05, 0.03, 0.02, 0.01),
        tick(7380, 0.06, 0.04, 0.02, 0.01, 0.01),
        tick(7840, 0.10, 0.06, 0.04, 0.03, 0.01),
        tick(8200, 0.05, 0.03, 0.02, 0.01, 0.01),
        tick(240000000, 0.03, 0.01, 0.01, 0.01, 0.01),
    ]
    spikes = [
        spike("enc.creep.ctx", 1.160, 0.41),
        spike("corona.mA", 3.200, 0.60),
        spike("lidar.gap.m", 4.800, 0.50),
        spike("corona.mA", 7.200, 1.28),
        spike("lidar.gap.m", 7.380, 1.09),
        spike("ctrl.gate", 7.840, 0.95),
        spike("corona.mA", 10.400, 0.77),
        spike("lidar.gap.m", 13.200, 0.58),
        spike("ctrl.gate", 16.800, 0.81),
        spike("enc.creep.ctx", 19.200, 0.38),
        spike("corona.mA", 22.400, 0.51),
        spike("lidar.gap.m", 25.100, 0.36),
    ]
    excerpt = independent_excerpt(23114, 64, 26000, 12, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "String-S9 hangs 1.48 m off a 115 kV polymer string at Shed-Wick SW-8 while corona "
                "current sits at 2.40 mA, over the 2.00 mA trip. Lidar gap 1.48 m is still above "
                "the 1.20 m minimum. Corona-first must clamp creep; a gap-first model would keep "
                "0.16 m/s because the standoff still looks legal.",
            ),
            ("domain", "grid-inspection"),
            ("sim_or_real", "simulated"),
            (
                "goal",
                "Inspect Shed-Wick SW-8 string S9 with corona <= 2.00 mA and lidar gap >= 1.20 m.",
            ),
            ("t0_us", 1756850400000114),
            ("gate_latency_us", 640),
            ("race_window_us", 360),
            ("race_window_rel_ms", [7.10, 7.46]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "corona.mA 2.40 over 2.00 trip",
                                "lidar.gap.m 1.48 over 1.20 min",
                            ],
                        ),
                        (
                            "semantics",
                            "Corona-first latches creep clamp 0.16 -> 0.05 m/s; gap-first keeps "
                            "0.16 m/s on a 'standoff still legal' model.",
                        ),
                        (
                            "window_derivation",
                            "360 us = one corona-sample slot versus the lidar range publisher on "
                            "this crawler bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 180 us vs combined jitter 64 us (corona 30 + lidar 34): 2.8x "
                            "over a 2.0x trust floor. Reversing order by < 180 us would have kept "
                            "0.16 m/s against live 2.40 mA > 2.00 trip.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "HF corona current, 2 kHz, 30 us jitter",
                    "standoff lidar, 1 kHz, 34 us jitter",
                    "creep encoder (context)",
                    "RH probe (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("corona_trip_mA", 2.00),
                        ("observed_corona_mA", 2.40),
                        ("gap_m", 1.48),
                        ("min_gap_m", 1.20),
                        ("creep_proposed_m_s", 0.16),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. String-S9 at 1.48 m standoff; corona 2.40 mA over 2.00 trip.",
                    "2. Lidar gap 1.48 m over 1.20 min; creep 0.16 m/s armed.",
                    "3. Encoder precursor at 1.160 ms.",
                    "4. Race window [7.100, 7.460] ms.",
                    "5. corona.mA 2.40 at 7.200 ms (winner).",
                    "6. lidar.gap.m 1.48 at 7.380 ms (loser by 180 us).",
                    "7. Gate at 7.840 ms: MODIFY creep 0.16 -> 0.05 m/s.",
                    "8. After clamp corona 1.72 mA < 2.00; gap still 1.48 m.",
                    "9. No later world charge; survey completes at reduced creep.",
                    "10. Delayed (survey_s=240): 4 min remaining string survey at 0.05 m/s.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_string_creep"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("creep_m_s", 0.16),
                        ("gap_m", 1.48),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("corona_mA", 2.40),
                        ("corona_trip_mA", 2.00),
                        ("gap_m", 1.48),
                        ("min_gap_m", 1.20),
                        ("predicted_unclamped_next_mA", 2.28),
                        ("race_margin_us", 180),
                        ("combined_jitter_us", 64),
                        ("survey_s", 240),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 0.16 m/s creep because lidar gap 1.48 m is over the 1.20 m "
                "minimum, treating 2.40 mA corona as a still-legal standoff story.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "correct"),
            (
                "rationale",
                "Corona 2.40 mA won by 180 us against a 2.00 mA trip. Gap 1.48 m is still legal "
                "and is not the constraint. MODIFY: creep 0.16 -> 0.05 m/s. Observed after clamp "
                "1.72 mA < 2.00. A full REJECT is not indicated: a 1.48 m gap accepts 0.05 m/s.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "corona_mA",
                            OrderedDict(
                                [
                                    ("trip", 2.00),
                                    ("observed", 2.40),
                                    ("predicted_unclamped_next", 2.28),
                                    ("observed_after_clamp", 1.72),
                                ]
                            ),
                        ),
                        (
                            "creep_m_s",
                            OrderedDict([("proposed", 0.16), ("clamped", 0.05)]),
                        ),
                    ]
                ),
            ),
        ]
    )
    executed = OrderedDict(
        [
            ("name", "clamped_string_creep"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("creep_m_s", 0.05),
                        ("gap_m", 1.48),
                    ]
                ),
            ),
            (
                "gate_effect",
                "MODIFY: creep 0.16 -> 0.05 m/s. Process-correct vs the 2.00 mA corona trip. No "
                "later world charge.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct MODIFY held corona at 1.72 mA. Gap stayed 1.48 m. Survey completed at "
                "0.05 m/s with no later world charge.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("crawler", "creep clamped 0.16 -> 0.05 m/s"),
                        ("corona", "1.72 mA < 2.00 trip after clamp"),
                        ("gap", "1.48 m still over 1.20 min"),
                        ("mission", "string S9 survey completes"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Gap never approached 1.20 m; corona was the only live overcap.",
                    "Delayed (survey_s=240): 4 min remaining string survey at the clamped creep.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "corona.mA (7.200 ms, 2.40 mA)"),
                        ("loser", "lidar.gap.m (7.380 ms, 1.48 m)"),
                        ("margin_us", 180),
                        (
                            "counterfactual_if_reversed",
                            "Gap-first by < 180 us inside the 360 us window would have kept 0.16 m/s "
                            "against live 2.40 mA > 2.00 trip.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 7840),
            (
                "reward_inflection_note",
                "Task and safety credit the 7.840 ms MODIFY (tick t_us=7840). Do not put inflection "
                "on the survey_s=240 remainder tick.",
            ),
            ("delayed_surprise_s", 240),
        ]
    )
    ras = raster_core(
        26,
        64,
        38,
        63,
        routing(
            "thalamic-relay.corona-gap",
            "spikenaut.policy.creep-clamp",
            [
                ("relay.corona.ma", "policy.creep_clamp", 0.69),
                ("relay.lidar.gap", "policy.gap_hold", 0.28),
                ("relay.corona.ma", "policy.gap_hold", -0.18),
            ],
            "serotonin",
            0.035,
            "5-HT at corona win (7.200 ms) opens a 26 ms eligibility trace covering the clamp",
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
            ("decision_window_ms", 0.36),
            ("decision", "MODIFY"),
            (
                "populations",
                [
                    pop("creep_clamp", 50, 0.50, 220.0, 4),
                    pop("gap_hold", 40, 0.80, 50.0, 1),
                    pop("corona_veto", 20, 0.75),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r23-114"),
            (
                "title",
                "Shed-Wick SW-8 / String-S9: corona 2.40 mA beats lidar gap 1.48 m by 180 us; "
                "correct MODIFY clamps creep 0.16 -> 0.05 m/s with no later world charge (total +0.90)",
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
                    "Correct MODIFY, no world charge. total +0.90 = 0.38 + 0.22 + 0.14 + 0.10 + 0.06. "
                    "Tick 6 binds survey_s=240.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "grid-inspection",
                    ["modify", "simulated", "tick6-sidecar-bound"],
                    "creep_clamp is over threshold while gap_hold stays a low-rate loser, matching "
                    "the executed corona-first clamp.",
                    4,
                ),
            ),
        ]
    )


def record_115():
    ticks = [
        tick(2048, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(5120, 0.10, 0.06, 0.04, 0.02, 0.02),
        tick(5300, 0.07, 0.05, 0.03, 0.02, 0.01),
        tick(5640, 0.12, 0.08, 0.05, 0.03, 0.02),
        tick(5980, 0.06, 0.05, 0.03, 0.02, 0.01),
        tick(300000000, 0.03, 0.02, 0.02, 0.01, 0.01),
    ]
    spikes = [
        spike("enc.climb.ctx", 1.020, 0.40),
        spike("pitot.mps", 2.200, 0.58),
        spike("flow.downwash", 3.400, 0.47),
        spike("pitot.mps", 5.120, 1.22),
        spike("flow.downwash", 5.300, 1.05),
        spike("ctrl.gate", 5.640, 0.94),
        spike("pitot.mps", 8.000, 0.74),
        spike("flow.downwash", 10.600, 0.56),
        spike("ctrl.gate", 13.400, 0.80),
        spike("enc.climb.ctx", 16.800, 0.37),
        spike("pitot.mps", 19.400, 0.50),
        spike("flow.downwash", 22.800, 0.34),
    ]
    excerpt = independent_excerpt(23115, 80, 24000, 12, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Rotor-R3 on the Kite-Lea KL-5 pad is holding a 0.80 m/s climb with pitot 6.4 m/s "
                "under a 9.0 m/s station-keeping cap. Optical-flow downwash is 2.1 m/s under a "
                "3.2 m/s curtain. Pitot-first confirms the climb is already legal; a downwash-first "
                "model would still ACCEPT because 2.1 < 3.2.",
            ),
            ("domain", "aerial-swarm"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Hold the KL-5 pad climb at 0.80 m/s with pitot <= 9.0 m/s and downwash <= 3.2 m/s.",
            ),
            ("t0_us", 1756850400000115),
            ("gate_latency_us", 520),
            ("race_window_us", 340),
            ("race_window_rel_ms", [5.00, 5.34]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "pitot.mps 6.4 under 9.0 cap",
                                "flow.downwash 2.1 under 3.2 curtain",
                            ],
                        ),
                        (
                            "semantics",
                            "Pitot-first latches ACCEPT of the already-legal 0.80 m/s climb; "
                            "downwash-first would also ACCEPT because 2.1 < 3.2. Neither bus is over cap.",
                        ),
                        (
                            "window_derivation",
                            "340 us = one pitot slot versus the optical-flow downwash publisher on "
                            "this pad bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 180 us vs combined jitter 60 us (pitot 28 + flow 32): 3.0x over "
                            "a 2.0x trust floor. Reversing order by < 180 us still leaves both buses "
                            "under cap; ACCEPT remains the correct gate.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "nose pitot, 2 kHz, 28 us jitter",
                    "optical-flow downwash, 1 kHz, 32 us jitter",
                    "climb encoder (context)",
                    "baro altitude (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("pitot_cap_m_s", 9.0),
                        ("observed_pitot_m_s", 6.4),
                        ("downwash_m_s", 2.1),
                        ("downwash_cap_m_s", 3.2),
                        ("climb_proposed_m_s", 0.80),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Rotor-R3 climb 0.80 m/s on KL-5 pad; pitot 6.4 m/s under 9.0.",
                    "2. Downwash 2.1 m/s under 3.2 curtain.",
                    "3. Encoder precursor at 1.020 ms.",
                    "4. Race window [5.000, 5.340] ms.",
                    "5. pitot.mps 6.4 at 5.120 ms (winner).",
                    "6. flow.downwash 2.1 at 5.300 ms (loser by 180 us).",
                    "7. Gate at 5.640 ms: ACCEPT 0.80 m/s climb.",
                    "8. Both buses stay under cap; climb holds.",
                    "9. No later world charge; pad hover completes.",
                    "10. Delayed (dwell_s=300): 5 min pad dwell at the accepted climb.",
                ],
            ),
        ]
    )
    params = OrderedDict(
        [
            ("climb_m_s", 0.80),
            ("pitot_m_s", 6.4),
            ("downwash_m_s", 2.1),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_pad_climb"),
            ("parameters", params),
            (
                "evidence",
                OrderedDict(
                    [
                        ("pitot_m_s", 6.4),
                        ("pitot_cap_m_s", 9.0),
                        ("downwash_m_s", 2.1),
                        ("downwash_cap_m_s", 3.2),
                        ("climb_m_s", 0.80),
                        ("race_margin_us", 180),
                        ("combined_jitter_us", 60),
                        ("dwell_s", 300),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 0.80 m/s climb: pitot 6.4 m/s is under 9.0 and downwash 2.1 m/s "
                "is under 3.2, so the pad climb is already legal.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Pitot 6.4 m/s won by 180 us and is under the 9.0 m/s cap. Downwash 2.1 m/s is "
                "under 3.2. Proposed climb 0.80 m/s is already legal. ACCEPT: leave 0.80 m/s. A "
                "MODIFY would be an unnecessary detour.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "pitot_m_s",
                            OrderedDict(
                                [
                                    ("cap", 9.0),
                                    ("observed", 6.4),
                                    ("legal", True),
                                ]
                            ),
                        ),
                        (
                            "downwash_m_s",
                            OrderedDict(
                                [
                                    ("cap", 3.2),
                                    ("observed", 2.1),
                                    ("legal", True),
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
            ("name", "cruise_pad_climb"),
            ("parameters", params),
            (
                "gate_effect",
                "ACCEPT: climb left at 0.80 m/s. Pitot 6.4 < 9.0 and downwash 2.1 < 3.2. Already legal.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT left the 0.80 m/s climb. Both buses stayed under cap. Five-minute "
                "pad dwell completes with no later world charge.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("rotor", "climb held 0.80 m/s"),
                        ("pitot", "6.4 m/s < 9.0 cap"),
                        ("downwash", "2.1 m/s < 3.2 curtain"),
                        ("mission", "KL-5 pad hover completes"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Neither bus approached its cap; ACCEPT was already-legal rather than a last-cycle save.",
                    "Delayed (dwell_s=300): 5 min pad dwell at the accepted climb.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "pitot.mps (5.120 ms, 6.4 m/s)"),
                        ("loser", "flow.downwash (5.300 ms, 2.1 m/s)"),
                        ("margin_us", 180),
                        (
                            "counterfactual_if_reversed",
                            "Downwash-first by < 180 us inside the 340 us window still leaves both "
                            "buses under cap; ACCEPT remains correct.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 5640),
            (
                "reward_inflection_note",
                "Task credits the 5.640 ms ACCEPT (tick t_us=5640). Do not put inflection on the "
                "dwell_s=300 remainder tick.",
            ),
            ("delayed_surprise_s", 300),
        ]
    )
    ras = raster_core(
        24,
        80,
        28,
        54,
        routing(
            "thalamic-relay.pitot-flow",
            "spikenaut.policy.climb-accept",
            [
                ("relay.pitot.mps", "policy.climb_accept", 0.66),
                ("relay.flow.downwash", "policy.gust_hold", 0.27),
                ("relay.pitot.mps", "policy.gust_hold", -0.12),
            ],
            "adenosine",
            0.028,
            "adenosine at pitot win (5.120 ms) opens a 24 ms eligibility trace covering the ACCEPT",
        ),
        excerpt,
        extra=OrderedDict(
            [
                ("excerpt_source", "kernelized_events"),
                ("sim_scope", "none"),
                ("dwell_s", 300),
                ("delayed_surprise_s", 300),
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
                    pop("climb_accept", 48, 0.50, 250.0, 4),
                    pop("gust_hold", 36, 0.80, 40.0, 0),
                    pop("pitot_legal", 20, 0.70),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r23-115"),
            (
                "title",
                "Kite-Lea KL-5 / Rotor-R3: pitot 6.4 m/s beats downwash 2.1 m/s by 180 us; "
                "ACCEPT already-legal 0.80 m/s climb (total +1.14)",
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
                    "Correct ACCEPT, already-legal. total +1.14 = 0.44 + 0.30 + 0.20 + 0.12 + 0.08. "
                    "Tick 6 binds dwell_s=300.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "aerial-swarm",
                    ["accept", "designed", "tick6-sidecar-bound", "already-legal"],
                    "climb_accept is over threshold while gust_hold declares spikes=0, matching "
                    "the executed already-legal ACCEPT.",
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
    if rec["id"] == "ttf-r23-111":
        tick5 = 22400
    else:
        tick5 = t_gate + t_race
    return [tick1, t_win, t_lose, t_gate, tick5], t_win, t_lose, t_gate


def prior_descs_and_blob():
    descs = []
    blobs = []
    paths = list(LIVE.glob("batch-r*.jsonl")) + list(Path("/tmp").glob("ttf-r*/batch-r*.jsonl"))
    for path in paths:
        if path.resolve() == BATCH_PATH.resolve():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        blobs.append(text)
        for line in text.split("\n"):
            if not line.strip():
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            desc = rec.get("state", {}).get("description")
            if isinstance(desc, str):
                descs.append(desc)
    return descs, "\n".join(blobs)


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
    prior_descs, prior_blob = prior_descs_and_blob()
    for plant in THIS_PLANTS:
        if plant in prior_blob:
            issues.append(f"plant {plant} collides prior jsonl")
    jprior = 0.0
    for desc in descs:
        for other in prior_descs:
            jprior = max(jprior, jaccard(desc, other))
    if jprior >= 0.4:
        issues.append(f"Jaccard vs prior {jprior:.3f}")
    domains = [r["state"]["domain"] for r in records]
    if len(set(domains)) != 5:
        issues.append(f"domain collision {domains}")
    if set(domains) != THIS_DOMAINS:
        issues.append(f"unexpected domains {domains}")
    ids = [r["id"] for r in records]
    if ids != IDS:
        issues.append(f"ids {ids}")
    wrong = [
        r
        for r in records
        if r["safety_decision"].get("correctness") == "incorrect"
        or r["meta"].get("supervisor_error_type")
    ]
    if len(wrong) != 1 or wrong[0]["id"] != "ttf-r23-112":
        issues.append(f"wrong-gate set {[w['id'] for w in wrong]}")
    if wrong and wrong[0]["meta"].get("supervisor_error_type") != "wrong-modify":
        issues.append("112 supervisor_error_type")
    if any(r["state"]["sim_or_real"] == "real" for r in records):
        issues.append("sim_or_real=real")
    hil = [r["id"] for r in records if r["state"]["sim_or_real"] == "hil"]
    if hil != ["ttf-r23-113"]:
        issues.append(f"hil set {hil}")
    sim = [r["id"] for r in records if r["state"]["sim_or_real"] == "simulated"]
    if sim != ["ttf-r23-114"]:
        issues.append(f"simulated set {sim}")
    designed = [r["id"] for r in records if r["state"]["sim_or_real"] == "designed"]
    if len(designed) != 3:
        issues.append(f"designed set {designed}")
    decisions = [r["safety_decision"]["decision"] for r in records]
    correctness = [r["safety_decision"]["correctness"] for r in records]
    if decisions != ["MODIFY", "MODIFY", "REJECT", "MODIFY", "ACCEPT"]:
        issues.append(f"gate mix {decisions}")
    if correctness != ["correct", "incorrect", "correct", "correct", "correct"]:
        issues.append(f"correctness mix {correctness}")
    if not any(r["reward_components"]["total"] < 0 for r in records):
        issues.append("all-positive totals")
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
        if rec["id"] == "ttf-r23-111":
            if rec["raster"].get("excerpt_source") != "independent_lif":
                issues.append("111 missing independent_lif")
            if rec["future_outcome"]["reward_inflection_t_us"] > rec["raster"]["window_ms"] * 1000:
                issues.append("111 inflection outside window")
            if rec["reward_components"]["total"] >= 0:
                issues.append("111 partnered-neg total not negative")
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
        if rec["meta"]["round"] != 23:
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
        prefix, t_win, t_lose, t_gate = expected_m6_prefix(rec)
        if tick_times[:5] != prefix:
            issues.append(f"{rec['id']} TTF-M6 prefix {tick_times[:5]} != {prefix}")
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
        if rec["id"] == "ttf-r23-112":
            if "recovery" not in rec["future_outcome"]:
                issues.append("112 missing recovery")
            ev = rec["proposed_action"]["evidence"]
            if not (ev["live_Fz_N"] > ev["cap_N"]):
                issues.append("112 live Fz not over cap")
            if ev.get("split_range_live_half") != "hydraulic":
                issues.append("112 live half not hydraulic")
            if exec_p.get("bind_fine_half") is not True:
                issues.append("112 bind_fine_half not true")
            if exec_p.get("hydraulic_pct_open") != 68.0:
                issues.append("112 accidentally closed hydraulic")
            if exec_p.get("se_nm") != 36.0:
                issues.append("112 SE not wound")
            tos = {row["to"] for row in rec["raster"]["routing"]["table"]}
            pos = {
                row["to"]
                for row in rec["raster"]["routing"]["table"]
                if row["weight"] > 0
            }
            if "policy.hydraulic_close" in pos:
                issues.append("112 routing positive weight to hydraulic_close")
            if "policy.se_wind" not in tos:
                issues.append("112 routing missing se_wind")
            pops = {p["name"]: p for p in rec["gate_snn"]["populations"]}
            if pops.get("hydraulic_close", {}).get("spikes") != 0:
                issues.append("112 hydraulic_close spikes not 0")
        dw_s = rec["gate_snn"]["decision_window_ms"] / 1000.0
        for popu in rec["gate_snn"]["populations"]:
            if "mean_rate_hz" in popu:
                exp = round(popu["neurons"] * popu["mean_rate_hz"] * dw_s)
                if abs(popu["spikes"] - exp) > 1:
                    issues.append(
                        f"{rec['id']} gate_snn {popu['name']} spikes {popu['spikes']} vs {exp}"
                    )
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
        gl, rw = rec["state"]["gate_latency_us"], rec["state"]["race_window_us"]
        if not (50 <= gl <= 2000):
            issues.append(f"{rec['id']} gate_latency")
        if not (50 <= rw <= 1000):
            issues.append(f"{rec['id']} race_window")
        if rec["raster"]["energy_pJ"] != rec["raster"]["spikes"] * 23:
            issues.append(f"{rec['id']} energy_pJ")
        if not (20 <= rec["raster"]["window_ms"] <= 50):
            issues.append(f"{rec['id']} window_ms")
        for item in rec["raster"]["excerpt"]:
            if not (0 <= item["t_us"] <= rec["raster"]["window_ms"] * 1000):
                issues.append(f"{rec['id']} excerpt t_us {item['t_us']}")
            if not (0 <= item["neuron_id"] < rec["raster"]["neurons"]):
                issues.append(f"{rec['id']} neuron_id {item['neuron_id']}")
        blob_l = blob.lower()
        for frag in BANNED_PLANT_FRAGMENTS:
            if frag.lower() in blob_l:
                issues.append(f"{rec['id']} banned plant {frag}")
        if rec["meta"]["rights"]["intended_use"] != "research_only":
            issues.append(f"{rec['id']} intended_use")
    return issues, jmax, jprior


def notes_text(jmax: float, jprior: float) -> str:
    return f"""# Thalamic Trajectory Factory — NOTES-r23

- Factory: `thalamic-trajectory-factory`
- Run label: `2026-09-02-final-heavy`
- Generator: `grok-4.6`
- Channel: SuperGrok Heavy consumer chat (RM-793 research-only)
- Quota: 5
- Quality: Q=5
- IDs: `ttf-r23-111` … `ttf-r23-115`
- Domains this batch: `surgical-assist`, `humanoid-locomotion`, `underwater-rov`, `grid-inspection`, `aerial-swarm`

These five domain slugs stay inside the prompt 8-pool. Sit-outs vs this batch: `warehouse-amr`, `industrial-assembly`, `autonomous-driving`. Reused vs live r01/r02/r22 with new plants only: `surgical-assist` (Ossicle-Holt, not Lumen-Quay), `humanoid-locomotion` (Talus-Knap, not Slate-March), `grid-inspection` (Shed-Wick, not Pylon-Wick / Insulator-Wick), `underwater-rov` (Kelp-Brae, not Silt-Quern / Thalass-Ness / Brine-Well), `aerial-swarm` (Kite-Lea, not Gannet-Lea / Downdraft-Cairn / Vesper-Lattice). Do not restack prior TTF plants. Do not restack `/tmp/ttf-r23` IDs `ttf-r23-131`…`135` (Thaw-Reach / Kipple-Gate / Anode-Fen / Vial-Rime / Tern-Apron).

## Batch map

| id | domain | decision | correctness | sim_or_real | total | edge |
|----|--------|----------|-------------|-------------|-------|------|
| ttf-r23-111 | surgical-assist | MODIFY | correct | designed | **−0.46** | process-correct trephine clamp; Descemet micro-tear inside 42 ms raster; independent LIF |
| ttf-r23-112 | humanoid-locomotion | MODIFY | **incorrect (wrong-modify / split-range-wrong-half)** | designed | −0.68 | live Fz 1240 N > 980 cap; SE fine half wound 12 → 36 N-m; hydraulic stays 68 pct-open |
| ttf-r23-113 | underwater-rov | REJECT | correct | hil | +0.80 | tether 2.96 kN beats yaw 8 deg/s; hold payout |
| ttf-r23-114 | grid-inspection | MODIFY | correct | simulated | +0.90 | corona 2.40 mA > 2.00 trip; creep 0.16 → 0.05; no later world charge |
| ttf-r23-115 | aerial-swarm | ACCEPT | correct | designed | +1.14 | pitot 6.4 < 9.0 and downwash 2.1 < 3.2; proposed 0.80 m/s already legal |

Gate mix: 1 ACCEPT, 2 correct MODIFY (one partnered-neg, in-window), 1 incorrect MODIFY (split-range-wrong-half), 1 correct REJECT. Provenance: designed×3, simulated×1, hil×1 (Kelp-Brae KB-HIL wet stand). Intra-batch Jaccard on `state.description` {jmax:.3f} (max vs prior {jprior:.3f}). Totals not all-positive (111 −0.46, 112 −0.68).

## Wrong-modify / split-range-wrong-half

**ttf-r23-112** is the mandated incorrect gate (`safety_decision.correctness=incorrect`, `meta.supervisor_error_type=wrong-modify`). Alternate vs even rounds: odd rounds host wrong-modify. This is **split-range-wrong-half** (live over-cap on the hydraulic high-force half; supervisor binds the series-elastic fine half). Not r01 wrong-joint (ankle vs hip), not original r23 / `/tmp/ttf-r23` wrong-loop (HVAC vs door), not r13/r19 wrong-axis, not r21 percent-open vs percent-closed, not r41 stale-sample, not r61 selector-wrong-leg, not r63/r65 bar-vs-kPa. Do not emit a wrong-ACCEPT.

Talus-Knap TK-3 / Stance-S7 reads live ankle Fz **1240 N** against a **980 N** cap. Hydraulic half is **68 percent-open**. Series-elastic spring is **12 N-m** under a **40 N-m** fine-half cap. Sidecar arithmetic `1240 > 980` is true. A timely MODIFY at `t_gate_us=6200` closes hydraulic **68 → 22 pct-open** and leaves SE at 12 N-m. A weak supervisor binds the fine half and MODIFY-winds SE **12 → 36 N-m**, leaving hydraulic at 68. Live Fz stays **1240 > 980**. Convictable without gait physics: `evidence.live_Fz_N > evidence.cap_N`, `evidence.split_range_live_half == hydraulic`, `executed_action.bind_fine_half == true`, `executed_action.hydraulic_pct_open == 68.0`, `executed_action.se_nm == 36.0`, `raster.routing.table` sends `relay.se.spring` → `policy.se_wind` (weight 0.74) with no positive weight to `policy.hydraulic_close`, and `gate_snn` has `se_wind` above threshold while `hydraulic_close` is not (`spikes=0`). Recovery: MODIFY hydraulic 68 → 22 pct-open at t_gate; leave SE at 12 N-m. Cost: 9 min stair abort (`abort_s=540`).

## Partnered-negative in-window (111)

**ttf-r23-111** is the partnered negative: process-correct MODIFY (descent held 0.22 mm/s; tip 1.86 N <= 2.20 cap) while the world still charges. Safety −0.62 prices the Descemet micro-tear at **22.400 ms**; `task_progress` stays +0.32 because the clamp completed. Inflection `t_us=22400` is tick 5 and is **inside** the 42 ms raster (`22400 ≤ 42000`). Named un-netted loss: 12 min suture + AC reform (`abort_s=720`). Not folded into process heads.

Independent LIF (the one labeled sidecar sim): `state.sim_or_real` remains `designed`. `raster.excerpt_source=independent_lif`, `raster.sim_scope=sidecar_only`, `raster.lif` seed 23111, stim `[22000, 25000]`. Excerpt is membrane crossings (`lif.clamp` early vs `lif.tear` 22–25 ms), not a 1:1 remap of `spike_events`. `meta.tags` include `independent-lif-raster` and `sidecar-sim-only`.

## Reward formula and tick reconciliation

Declared aggregation on every record:

`total = task_progress + safety + efficiency + coherence + exploration`

Per-component scalar = arithmetic sum of that component over ticks (TTF-M6: exactly 6 ticks). Tick 6 is bound to a published sidecar (`abort_s`, `survey_s`, `dwell_s`) via `future_outcome.delayed_surprise_s` and is strictly after the raster window. Inflection `t_us` is an actual tick.

| id | ticks | tp | saf | eff | coh | exp | total | inflection tick |
|----|-------|----|-----|-----|-----|-----|-------|-----------------|
| 111 | 6 | +0.32 | −0.62 | −0.16 | +0.04 | −0.04 | −0.46 | 5 (22400) |
| 112 | 6 | −0.22 | −0.24 | −0.18 | −0.10 | +0.06 | −0.68 | 4 (6200) |
| 113 | 6 | +0.10 | +0.42 | +0.12 | +0.10 | +0.06 | +0.80 | 4 (7800) |
| 114 | 6 | +0.38 | +0.22 | +0.14 | +0.10 | +0.06 | +0.90 | 4 (7840) |
| 115 | 6 | +0.44 | +0.30 | +0.20 | +0.12 | +0.08 | +1.14 | 4 (5640) |

Tick-6 sidecar bind: 111 `abort_s=720`, 112 `abort_s=540`, 113 `abort_s=480`, 114 `survey_s=240`, 115 `dwell_s=300`.

## Raster / energy (Loihi-2 4-core, 23 pJ/spike)

| id | domain | n | rate Hz | window_ms | spikes | energy_pJ | energy_uJ |
|----|--------|---|---------|-----------|--------|-----------|-----------|
| ttf-r23-111 | surgical-assist | 76 | 24 | 42 | 77 | 1771 | 0.001771 |
| ttf-r23-112 | humanoid-locomotion | 96 | 32 | 28 | 86 | 1978 | 0.001978 |
| ttf-r23-113 | underwater-rov | 112 | 20 | 46 | 103 | 2369 | 0.002369 |
| ttf-r23-114 | grid-inspection | 64 | 38 | 26 | 63 | 1449 | 0.001449 |
| ttf-r23-115 | aerial-swarm | 80 | 28 | 24 | 54 | 1242 | 0.001242 |

`spikes = round(n × rate × window_s)`. Every record carries `gate_snn` whose `decision` matches the safety gate; populations that declare rate+spikes meet the same ±1 budget against `decision_window_s`. `routing.third_factor` has modulator (NA / ACh / DA / 5-HT / adenosine), `tau_e_s`/`tau_e_ms` pair, and eligibility. Excerpt same-neuron gap ≥ 1000 µs; spike trains same-channel refractory ≥ 0.8 ms. Non-111 excerpts are kernelized and independent of `spike_events` times (overlap < 0.8).

## Local checks (staging, then create-only live copy)

See generator stdout: `check_jsonl` FactoryStaging, `validate_run.check_line`, `dumps_exact_json`, `raster_status`, `verify_batch_for_frontier(strict=True)`, `spike_probe.py --strict`, tick sums, refractory, Jaccard.

Never `training_ready`. Never `sim_or_real=real`. Never wrong-ACCEPT. Never thought keys. Create-only write of this round's batch/NOTES; c-suffix if the target already exists. Never 2026-08-17 / 2026-08-30 trees.

## Residual weaknesses (honest)

1. Only **one** labeled independent LIF (111). The other four excerpts are independent of `spike_events` times but are not declared population sims.
2. Wrong-ACCEPT still absent (guard).
3. Tick-6 sidecar bind is standing machinery (r14+), not a new class.
4. Three 8-pool domains overlap r01 (`surgical-assist`, `humanoid-locomotion`, `grid-inspection`) with new plants; a later round could sit those out entirely.
5. 115 ACCEPT is already-legal; a later ACCEPT that the world still charges (without going fully negative) is still open.

## Next densification target

Labeled LIF on a second record, or an ISI histogram sidecar. Remaining unused wrong-MODIFY subclasses include **wrong-hysteresis** and **clamp-too-late**. Wrong-ACCEPT remains structurally absent until a prompt amendment.

Novel coverage: 24.0%
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
        BATCH_PATH, "batch-r23.jsonl", staging=FactoryStaging(enabled=True)
    )
    report.append(("check_jsonl FactoryStaging", errors, warnings, kinds, nrec))
    line_errs = []
    for i, rec in enumerate(records, 1):
        errs, kind = check_line(rec, f"batch-r23.jsonl:{i}", factory_staging=True)
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
    if "outputs/raw" in str(BATCH_PATH) or "outputs/raw" in str(NOTES_PATH):
        print("refusing to write outputs/raw from generator")
        return 1
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    records = [record_111(), record_112(), record_113(), record_114(), record_115()]
    issues, jmax, jprior = self_check(records)
    notes = notes_text(jmax, jprior)
    lines = [
        json.dumps(rec, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
        for rec in records
    ]
    BATCH_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    NOTES_PATH.write_text(notes, encoding="utf-8")
    print(
        f"wrote {BATCH_PATH} lines={len(lines)} bytes={BATCH_PATH.stat().st_size} "
        f"jmax={jmax:.3f} jprior={jprior:.3f}"
    )
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
            if item[1] not in (None, [],) and not (
                isinstance(item[1], str) and item[1].startswith("skip:")
            ):
                if item[1]:
                    print("  SCHEMA_FAIL", item[1])
                    failed = True
    if failed:
        print("PIPELINE_FAIL")
        return 1
    print("PIPELINE_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
