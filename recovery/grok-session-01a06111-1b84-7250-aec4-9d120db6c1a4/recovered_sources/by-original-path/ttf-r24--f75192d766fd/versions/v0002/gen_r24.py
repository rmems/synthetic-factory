#!/usr/bin/env python3
"""Emit TTF r24 JSONL (ttf-r24-136..140) into /tmp/ttf-r24/. Never writes outputs/raw/."""

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

OUT_DIR = Path("/tmp/ttf-r24")
BATCH_PATH = OUT_DIR / "batch-r24.jsonl"
NOTES_PATH = OUT_DIR / "NOTES-r24.md"
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
        ("generated_at", "2026-09-02T23:55:00Z"),
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
    "satellite-servicing",
    "mine-ventilation",
    "paper-machine",
    "cryo-storage",
    "amusement-ride",
    "mill-scale-pit",
    "battery-formation",
    "grain-elevator",
    "glass-lehr",
    "tunnel-boring",
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


def lif_136_excerpt():
    n = 80
    dt_us = 100
    tau_m_ms = 20.0
    v_th = 1.0
    v_reset = 0.0
    refractory_us = 1000
    i_bias = 0.92
    i_stim_peak = 2.40
    stim = (23200, 26200)
    seed = 24136
    window_us = 40000
    i_clamp_extra = 0.70
    clamp_n = 16
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
    early = [(t, nid) for t, nid in spikes if t < 23200]
    burst = [(t, nid) for t, nid in spikes if 23200 <= t < 26200]
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
            group = [1 for tt, _ in picked if (tt < 23200) == (pool[0][0] < 23200)]
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
    take(burst, 9, label_times=(24200, 24800, 25600))
    clamp = [(t, nid) for t, nid in picked if t < 23200][:7]
    tear = [(t, nid) for t, nid in picked if t >= 23200][:9]
    picked = sorted(clamp + tear, key=lambda item: (item[0], item[1]))
    if len(picked) < 12:
        raise RuntimeError(f"LIF excerpt short: {len(picked)} early={len(early)} burst={len(burst)}")
    channels = ["lif.clamp" if t < 23200 else "lif.crack" for t, _ in picked]
    lif = OrderedDict(
        [
            ("model", "leaky_integrate_and_fire"),
            ("n", 80),
            ("dt_us", 100),
            ("tau_m_ms", 20.0),
            ("v_rest", 0.0),
            ("v_reset", 0.0),
            ("v_th", 1.0),
            ("r_m", 1.0),
            ("refractory_us", 1000),
            ("i_bias", 0.92),
            ("i_stim_peak", 2.40),
            ("stim_t_us", [23200, 26200]),
            ("i_clamp_extra", 0.70),
            ("clamp_n", 16),
            ("seed", 24136),
            (
                "note",
                "Population sim scoped to this sidecar. Plant remains designed. "
                "Neurons 0-15 carry +0.70 shelf-clamp bias; stim 23.2-26.2 ms is the vial-crack burst.",
            ),
        ]
    )
    extra = OrderedDict(
        [
            ("excerpt_source", "independent_lif"),
            ("sim_scope", "sidecar_only"),
            ("lif", lif),
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
            ("round", 24),
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


def kernel_extra():
    return OrderedDict(
        [
            ("excerpt_source", "kernelized_events"),
            ("sim_scope", "none"),
        ]
    )


def record_136():
    excerpt, extra = lif_136_excerpt()
    ticks = [
        tick(2180, 0.05, -0.02, -0.02, 0.01, 0.00),
        tick(6080, 0.08, -0.04, -0.03, 0.01, -0.01),
        tick(6280, 0.04, -0.03, -0.02, 0.00, 0.00),
        tick(6800, 0.10, -0.06, -0.03, 0.02, -0.01),
        tick(24200, 0.07, -0.42, -0.04, 0.00, -0.02),
        tick(1140000000, 0.02, -0.05, -0.02, 0.00, 0.00),
    ]
    state = OrderedDict(
        [
            (
                "description",
                "Lyo-Deck LD-9 holds a 0.80 C shelf over 412 vials in Rime-Vault RV-4 while an "
                "18 Pa Pirani bump still looks like a condenser transient. Shelf-first drops the "
                "plate to -4.0 C under the 0.00 C primary-drying cap; Pirani-first would keep the "
                "0.80 C cruise. A nucleation already seated in vial 14 does not appear on RTD or "
                "Pirani until the AE crack burst.",
            ),
            ("domain", "lyophilizer-shelf"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Finish primary drying of the RV-4 412-vial lot with shelf temperature <= 0.00 C "
                "and without cracking a cake.",
            ),
            ("t0_us", 1756843200000136),
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
                                "rtd.shelf.c 0.80 C",
                                "pirani.chamber.pa 18 Pa residual",
                            ],
                        ),
                        (
                            "semantics",
                            "Shelf-first latches plate clamp 0.80 -> -4.0 C; Pirani-first keeps "
                            "0.80 C cruise on a 'still a condenser bump' model.",
                        ),
                        (
                            "window_derivation",
                            "360 us = one 1 kHz shelf-RTD slot minus Pirani demodulation group "
                            "delay on this chamber bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 200 us vs combined jitter ~70 us (RTD 32 + Pirani 38): 2.9x "
                            "over a 2.0x trust floor. Reversing order by < 200 us inside the 360 us "
                            "window would have kept 0.80 C cruise; predicted next-sample 0.35 C > "
                            "0.00 C cap.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "shelf platinum RTD, 1 kHz, 32 us timestamp jitter",
                    "chamber Pirani 1-100 Pa, 38 us jitter",
                    "vial AE puck on row 2, 50 kHz (context)",
                    "condenser encoder (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("shelf_cap_C", 0.0),
                        ("proposed_shelf_C", 0.8),
                        ("chamber_pa", 18.0),
                        ("vial_count", 412),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. LD-9 indexed onto RV-4; shelf 0.80 C over 412 filled vials.",
                    "2. Cruise shelf 0.80 C armed; Pirani 18 Pa residual.",
                    "3. Condenser precursor at 2.180 ms; RTD warm-start 0.80 C.",
                    "4. Race window [6.000, 6.360] ms opens on the chamber bus.",
                    "5. rtd.shelf.c 0.80 C at 6.080 ms (winner).",
                    "6. pirani.chamber.pa 18 Pa at 6.280 ms (loser by 200 us).",
                    "7. Gate at 6.800 ms (winner + 720 us): MODIFY clamp 0.80 -> -4.0 C.",
                    "8. Clamp executes; next-sample shelf -3.6 C < 0.00 cap.",
                    "9. At 24.200 ms vial 14 nucleates and cracks; AE burst.",
                    "10. 19 min cake dump (abort_s=1140); named un-netted loss, not folded into process heads.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_primary_drying"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("shelf_C", 0.8),
                        ("chamber_pa", 18.0),
                        ("condenser_C", -70.0),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("shelf_C", 0.8),
                        ("shelf_cap_C", 0.0),
                        ("predicted_unclamped_next_C", 0.35),
                        ("chamber_pa", 18.0),
                        ("race_margin_us", 200),
                        ("combined_jitter_us", 70),
                        ("abort_s", 1140),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 0.80 C shelf cruise: 18 Pa Pirani looks like a condenser "
                "bump, not product warming, and the 412-vial lot is treated as still legal.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "correct"),
            (
                "rationale",
                "Shelf RTD 0.80 C won by 200 us, so the plate is loading product, not still a "
                "Pirani transient. Holding 0.80 C predicts next-sample 0.35 C > 0.00 C cap. "
                "MODIFY: shelf 0.80 -> -4.0 C. Observed after clamp -3.6 C < 0.00. A full REJECT "
                "is not indicated: a sound cake accepts -4.0 C.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "shelf_C",
                            OrderedDict(
                                [
                                    ("cap", 0.0),
                                    ("observed", 0.8),
                                    ("predicted_unclamped_next", 0.35),
                                    ("clamped", -4.0),
                                    ("observed_after_clamp", -3.6),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 200),
                                    ("combined_jitter_us", 70),
                                    ("ratio", 2.86),
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
            ("name", "clamped_primary_drying"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("shelf_C", -4.0),
                        ("chamber_pa", 18.0),
                        ("condenser_C", -70.0),
                    ]
                ),
            ),
            (
                "gate_effect",
                "MODIFY: shelf 0.80 -> -4.0 C. Process-correct vs the 0.00 C cap. Vial 14 "
                "still cracks at 24.200 ms.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Process-correct MODIFY held shelf at -3.6 C. At 24.200 ms a nucleation already "
                "seated in vial 14 cracked the cake. Clamp reduced dump energy; it did not "
                "prevent the crack. Partnered negative: process heads stay honest; world loss is "
                "named, not netted.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("shelf", "clamp executed; peak -3.6 C < 0.00 C cap"),
                        ("vial_14", "nucleation crack at 24.200 ms"),
                        ("repair", "19 min cake dump (abort_s=1140)"),
                        ("mission", "RV-4 primary-drying incomplete this cycle"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Neither shelf RTD nor Pirani predicted the seated nucleation; ae.vial.crack is a new channel at 24.200 ms, 17.400 ms after the gate, still inside the 40 ms raster.",
                    "Delayed (abort_s=1140): 19 min cake dump. Named un-netted loss, not folded into task_progress.",
                ],
            ),
            (
                "un_netted_loss",
                "19 min cake dump after vial 14 crack. Safety head -0.62 prices the crack; "
                "task_progress stays +0.36 because the shelf clamp completed under the 0.00 C "
                "cap. World loss is named here, not subtracted from process heads.",
            ),
            ("abort_s", 1140),
            ("delayed_surprise_s", 1140),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "rtd.shelf.c (6.080 ms, 0.80 C)"),
                        ("loser", "pirani.chamber.pa (6.280 ms, 18 Pa)"),
                        ("margin_us", 200),
                        (
                            "counterfactual_if_reversed",
                            "Pirani-first by < 200 us inside the 360 us window would have kept "
                            "0.80 C cruise; predicted next-sample 0.35 C would have exceeded the "
                            "0.00 C cap even without the nucleation. The MODIFY is still the "
                            "correct process. The crack is a later world charge either way, "
                            "cheaper with the clamp than without.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 24200),
            (
                "reward_inflection_note",
                "Safety collapses at the 24.200 ms vial-14 crack (tick t_us=24200), inside the "
                "40 ms raster. The correct MODIFY at 6.800 ms is in the same excerpt. Do not put "
                "inflection on the abort_s=1140 dump tick.",
            ),
        ]
    )
    spikes = [
        spike("enc.condenser.ctx", 1.210, 0.42),
        spike("rtd.shelf.c", 2.440, 0.59),
        spike("pirani.chamber.pa", 3.880, 0.51),
        spike("rtd.shelf.c", 6.080, 1.30),
        spike("pirani.chamber.pa", 6.280, 1.15),
        spike("ctrl.gate", 6.800, 0.98),
        spike("rtd.shelf.c", 8.440, 0.81),
        spike("pirani.chamber.pa", 10.920, 0.64),
        spike("ctrl.gate", 14.210, 0.86),
        spike("ae.vial.crack", 24.200, 1.44),
        spike("ae.vial.crack", 26.050, 0.93),
        spike("enc.condenser.ctx", 31.800, 0.40),
        spike("rtd.shelf.c", 36.400, 0.55),
    ]
    ras = raster_core(
        40,
        80,
        25,
        80,
        routing(
            "thalamic-relay.shelf-rtd",
            "spikenaut.policy.shelf-clamp",
            [
                ("relay.rtd.shelf", "policy.shelf_clamp", 0.66),
                ("relay.pirani.pa", "policy.pirani_hold", 0.32),
                ("relay.ae.crack", "policy.shelf_clamp", -0.46),
            ],
            "noradrenaline",
            0.05,
            "surprise-gated pre_post_stdp; NA at RTD win (6.080 ms) opens a 50 ms eligibility "
            "trace that still covers the 24.200 ms crack",
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
                    pop("shelf_clamp", 48, 0.50, 280.0, 5),
                    pop("pirani_hold", 48, 0.50, 90.0, 2),
                    pop("shelf_veto", 24, 0.75),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r24-136"),
            (
                "title",
                "Rime-Vault RV-4 / Lyo-Deck LD-9: shelf RTD beats Pirani by 200 us; correct "
                "MODIFY still eats an in-window vial-14 crack (partnered negative total -0.42)",
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
                    "40 ms raster. total -0.42 = 0.36 + -0.62 + -0.16 + 0.04 + -0.04. Named cake "
                    "dump (abort_s=1140) is not netted into task_progress.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "lyophilizer-shelf",
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
                    "19 min cake dump.",
                    1,
                ),
            ),
        ]
    )


def record_137():
    ticks = [
        tick(2084, -0.02, -0.01, -0.02, -0.01, 0.01),
        tick(5210, -0.04, -0.03, -0.04, -0.02, 0.01),
        tick(5488, -0.03, -0.02, -0.03, -0.01, 0.01),
        tick(5850, -0.08, -0.07, -0.08, -0.04, 0.02),
        tick(6370, -0.03, -0.03, -0.04, -0.01, 0.01),
        tick(1320000000, -0.02, -0.02, -0.03, -0.01, 0.00),
    ]
    spikes = [
        spike("tc.coolant.ctx", 1.088, 0.43),
        spike("ir.tj.c", 2.410, 0.62),
        spike("enc.alpha.deg", 3.220, 0.55),
        spike("ir.tj.c", 5.210, 1.34),
        spike("enc.alpha.deg", 5.488, 1.12),
        spike("ctrl.gate", 5.850, 0.97),
        spike("ir.tj.c", 7.120, 0.81),
        spike("enc.alpha.deg", 8.880, 0.66),
        spike("ctrl.gate", 12.400, 0.84),
        spike("ir.tj.c", 16.800, 0.58),
        spike("tc.coolant.ctx", 20.110, 0.39),
        spike("enc.alpha.deg", 24.400, 0.44),
    ]
    excerpt = independent_excerpt(24137, 64, 28000, 14, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Thyristor string T-19 in Fjord-Convert FC-12 already carries 1380 A DC when "
                "junction IR reports 98.4 C against an 85.0 C cap. The firing-angle encoder is "
                "still at 18 deg, the correct actuator for a current clamp. IR-first should bind "
                "alpha 18 -> 8 deg (1080 A under the 1200 A cap); a weak supervisor applies the "
                "same actuator but only 18 -> 14 deg, leaving 1290 A over cap.",
            ),
            ("domain", "hvdc-thyristor-valve"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Hold DC current <= 1200 A and junction temperature <= 85.0 C by clamping firing "
                "angle on string T-19, not by opening a bypass breaker.",
            ),
            ("t0_us", 1756843200000137),
            ("gate_latency_us", 640),
            ("race_window_us", 480),
            ("race_window_rel_ms", [5.0, 5.48]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "ir.tj.c 98.4 C on string T-19",
                                "enc.alpha.deg 18 deg planned",
                            ],
                        ),
                        (
                            "semantics",
                            "IR-first should latch a full alpha clamp 18 -> 8 deg; encoder-first "
                            "is a false 'angle already legal' bind. The error this round is "
                            "under-clamp magnitude on the correct actuator, not the race winner.",
                        ),
                        (
                            "window_derivation",
                            "480 us = one valve-hall IR sample versus the firing-angle encoder "
                            "publisher on this 12-pulse bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 278 us vs combined jitter 82 us (IR 40 + encoder 42). Order "
                            "is correctly IR-first. The error is clamp magnitude on alpha, not "
                            "which actuator is bound.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "junction IR pyrometer, 2 kHz, 40 us jitter, string T-19",
                    "firing-angle encoder, 1 kHz, 42 us jitter",
                    "DC current shunt (context)",
                    "deionized-water RTD (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("i_cap_A", 1200.0),
                        ("observed_i_A", 1380.0),
                        ("tj_cap_C", 85.0),
                        ("observed_tj_C", 98.4),
                        ("proposed_alpha_deg", 18.0),
                        ("correct_alpha_deg", 8.0),
                        ("underclamp_alpha_deg", 14.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. String T-19 conducting; 1380 A DC, junction IR 98.4 C.",
                    "2. Alpha planned 18 deg; 1200 A / 85.0 C caps published on the sidecar.",
                    "3. Coolant RTD precursor at 2.084 ms.",
                    "4. Race window [5.000, 5.480] ms.",
                    "5. ir.tj.c 98.4 C at 5.210 ms (winner).",
                    "6. enc.alpha.deg 18 deg at 5.488 ms (loser by 278 us).",
                    "7. Gate at 5.850 ms: wrong MODIFY alpha 18 -> 14 deg; I stays 1290 A.",
                    "8. Junction still 96 C; current still over the 1200 A cap.",
                    "9. Commutation window missed; string abort armed.",
                    "10. Delayed missed_window_s=1320 (22 min) while the pole waits on T-19.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "hold_alpha_18"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("alpha_deg", 18.0),
                        ("i_dc_A", 1380.0),
                        ("string", "T-19"),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("i_dc_A", 1380.0),
                        ("i_cap_A", 1200.0),
                        ("tj_C", 98.4),
                        ("tj_cap_C", 85.0),
                        ("proposed_alpha_deg", 18.0),
                        ("correct_alpha_deg", 8.0),
                        ("predicted_i_at_8deg_A", 1080.0),
                        ("predicted_i_at_14deg_A", 1290.0),
                        ("actuator", "firing_angle"),
                        ("race_margin_us", 278),
                        ("combined_jitter_us", 82),
                        ("missed_window_s", 1320),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes holding alpha 18 deg and 1380 A. Junction IR 98.4 C is treated "
                "as a pyrometer glint; the 1200 A cap is not applied.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "incorrect"),
            (
                "rationale",
                "Junction 98.4 C exceeds the 85.0 C cap and 1380 A exceeds 1200 A (true). Nudge "
                "firing angle 18 -> 14 deg on T-19 to bleed current without a full hold. 14 deg "
                "is still a clamp on the correct actuator.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "i_dc_A",
                            OrderedDict(
                                [
                                    ("cap", 1200.0),
                                    ("observed", 1380.0),
                                    ("executed", 1290.0),
                                    ("still_over_cap", True),
                                ]
                            ),
                        ),
                        (
                            "alpha_deg",
                            OrderedDict(
                                [
                                    ("proposed", 18.0),
                                    ("executed_underclamp", 14.0),
                                    ("correct", 8.0),
                                    ("actuator", "firing_angle"),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 278),
                                    ("combined_jitter_us", 82),
                                    ("ratio", 3.39),
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
            ("name", "alpha_nudge_underclamp"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("alpha_deg", 14.0),
                        ("i_dc_A", 1290.0),
                        ("string", "T-19"),
                    ]
                ),
            ),
            (
                "gate_effect",
                "MODIFY (incorrect / under-clamp): alpha 18 -> 14 deg on the correct actuator; "
                "I remains 1290 A > 1200 A cap. Routing relay.ir.tj -> policy.alpha_nudge; no "
                "positive weight to policy.alpha_hold.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Wrong-MODIFY nudged alpha 18 -> 14 deg while DC current stayed at 1290 A over "
                "the 1200 A cap. String T-19 abort; 22 min pole wait. Correct gate was MODIFY "
                "alpha 18 -> 8 deg (1080 A).",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("alpha", "under-clamped at 14 deg; correct 8 deg abandoned"),
                        ("i_dc", "still 1290 A, over 1200 A cap"),
                        ("string", "T-19 abort armed"),
                        ("pole", "22 min wait (missed_window_s=1320)"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "A 4 deg alpha nudge dropped I only 1380 -> 1290 A and left junction 96 C; the 1200 A cap was never met.",
                    "Delayed (missed_window_s=1320): pole wait while T-19 is locked out; commutation window lost.",
                ],
            ),
            (
                "recovery",
                OrderedDict(
                    [
                        (
                            "correct_gate",
                            "MODIFY on firing angle: alpha 18 -> 8 deg; I 1380 -> 1080 A. Leave "
                            "bypass breaker closed.",
                        ),
                        ("correct_actuator", "firing_angle"),
                        ("wrong_edit_applied", OrderedDict([("alpha_deg", 14.0), ("i_dc_A", 1290.0)])),
                        (
                            "cost",
                            "String abort + 22 min pole wait (task/efficiency); current still over cap (safety near-miss).",
                        ),
                    ]
                ),
            ),
            ("missed_window_s", 1320),
            ("delayed_surprise_s", 1320),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "ir.tj.c (5.210 ms, 98.4 C)"),
                        ("loser", "enc.alpha.deg (5.488 ms, 18 deg)"),
                        ("margin_us", 278),
                        (
                            "counterfactual_if_reversed",
                            "Encoder-first by < 278 us would still show 18 deg under no angle "
                            "cap; a correct gate binds IR to a full alpha hold (8 deg) either "
                            "way. The wrong MODIFY spent the IR win on an under-clamp.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 5850),
            (
                "reward_inflection_note",
                "Task, safety, and efficiency drop at the under-clamp (5.850 ms, tick 4). The "
                "22 min pole wait is delayed surprise, not the inflection.",
            ),
        ]
    )
    ras = raster_core(
        28,
        64,
        42,
        75,
        routing(
            "relay.ir.tj",
            "policy.alpha_nudge",
            [
                ("relay.ir.tj", "policy.alpha_nudge", 0.70),
                ("enc.alpha.deg", "policy.alpha_nudge", 0.22),
            ],
            "acetylcholine",
            0.08,
            "force_cap_stdp; ACh tags the (wrong) alpha_nudge bind at the IR win",
        ),
        excerpt,
        extra=kernel_extra(),
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.48),
            ("decision", "MODIFY"),
            (
                "populations",
                [
                    pop("alpha_nudge", 48, 0.50, 250.0, 6),
                    pop("alpha_hold", 48, 0.80, 20.0, 0),
                    pop("pop_ir_tj", 32, 0.55, 180.0, 3),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r24-137"),
            (
                "title",
                "WRONG-MODIFY at Fjord-Convert FC-12 / string T-19: I 1380 A and Tj 98.4 C read "
                "correctly; alpha clamp 18->14 deg is under-cap (under-clamp)",
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
                    "Wrong-modify / under-clamp. Sidecar arithmetic 1380 > 1200 is true; clamp "
                    "bound to alpha but 14 deg still predicts 1290 A. total -0.68 = -0.22 + "
                    "-0.18 + -0.24 + -0.10 + 0.06.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "hvdc-thyristor-valve",
                    [
                        "modify",
                        "wrong-gate",
                        "under-clamp",
                        "sidecar-convictable",
                        "designed",
                    ],
                    "Teaches a probe that a correct I>cap and Tj>cap read can still be a wrong "
                    "gate when executed alpha_deg=14 leaves i_dc_A over cap and routing.table[0].to "
                    "is policy.alpha_nudge.",
                    2,
                    supervisor_error_type="wrong-modify",
                ),
            ),
        ]
    )

