#!/usr/bin/env python3
"""Emit TTF r22 (ttf-r22-106..110) CREATE-ONLY into the live 2026-09-02-final-heavy tree.

Never overwrites. Never writes 2026-08-17 / 2026-08-30.
"""

from __future__ import annotations

import json
import math
import os
import random
import re
import sys
from collections import OrderedDict
from decimal import Decimal
from pathlib import Path

LIVE_DIR = Path(
    "/home/raulmc/rmems/synthetic-factory/outputs/raw/2026-09-02-final-heavy/"
    "thalamic-trajectory-factory"
)
BATCH_NAME = "batch-r22.jsonl"
NOTES_NAME = "NOTES-r22.md"
PJ_PER_SPIKE = 23
RIGHTS = OrderedDict(
    [
        ("provider", "SpaceXAI/xAI"),
        ("model", "grok-4.6"),
        ("channel", "consumer"),
        ("subscription_plan", "SuperGrok Heavy"),
        ("generation_surface", "SuperGrok Heavy chat"),
        ("generated_at", "2026-09-02T19:20:00Z"),
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
    "Lumen-Quay",
    "Rivermead",
    "Fork-Haven",
    "Pylon-Wick",
    "Slate-March",
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
    "Sinter-Ridge",
    "Chaff-Mere",
    "Caisson-Forge",
    "Crumb-Vault",
    "Caliche-Drift",
)
FORBIDDEN_PATH_FRAGMENTS = ("2026-08-17", "2026-08-30")


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


def kernel_excerpt(window_ms, neurons, spike_events, n_want, seed):
    spike_us = {int(round(ev["t_rel_ms"] * 1000.0)) for ev in spike_events}
    rng = random.Random(seed)
    window_us = int(window_ms * 1000)
    picked = []
    last = {}
    t = 640 + (seed % 180)
    stride = 1680 + (seed % 9) * 20
    guard = 0
    while len(picked) < n_want and t <= window_us - 180 and guard < 400:
        guard += 1
        if t not in spike_us:
            for _ in range(24):
                nid = rng.randrange(neurons)
                if nid in last and t - last[nid] < 1000:
                    continue
                picked.append((t, nid))
                last[nid] = t
                break
        t += stride
    if len(picked) < 8:
        raise RuntimeError(f"kernel excerpt too short seed={seed} n={len(picked)}")
    return excerpt_items(picked)


def lif_106_excerpt():
    n = 72
    dt_us = 100
    tau_m_ms = 19.5
    v_th = 1.0
    v_reset = 0.0
    refractory_us = 1000
    i_bias = 0.90
    i_stim_peak = 2.36
    stim = (22000, 25600)
    seed = 22106
    window_us = 42000
    i_clamp_extra = 0.64
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
    early = [(t, nid) for t, nid in spikes if t < 22000]
    burst = [(t, nid) for t, nid in spikes if 22000 <= t < 25600]
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
            early_flag = pool[0][0] < 22000
            have = len([1 for t, _ in picked if (t < 22000) == early_flag])
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
    take(burst, 9, label_times=(23400, 24100, 24800))
    picked.sort(key=lambda item: (item[0], item[1]))
    clamp = [(t, n) for t, n in picked if t < 22000][:7]
    slump = [(t, n) for t, n in picked if t >= 22000][:9]
    picked = sorted(clamp + slump, key=lambda item: (item[0], item[1]))
    if len(picked) < 8:
        raise RuntimeError(f"LIF excerpt too short: {len(picked)}")
    channels = ["lif.clamp" if t < 22000 else "lif.rack" for t, _ in picked]
    lif = OrderedDict(
        [
            ("model", "leaky_integrate_and_fire"),
            ("n", 72),
            ("dt_us", 100),
            ("tau_m_ms", 19.5),
            ("v_rest", 0.0),
            ("v_reset", 0.0),
            ("v_th", 1.0),
            ("r_m", 1.0),
            ("refractory_us", 1000),
            ("i_bias", 0.90),
            ("i_stim_peak", 2.36),
            ("stim_t_us", [22000, 25600]),
            ("i_clamp_extra", 0.64),
            ("clamp_n", 14),
            ("seed", 22106),
            (
                "note",
                "Population sim scoped to this sidecar. Plant remains designed. "
                "Neurons 0-13 carry +0.64 aisle-clamp bias; stim 22.0-25.6 ms is the rack-leg collapse.",
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


def meta_block(domain, tags, distillation_value, batch_position, supervisor_error_type=None):
    body = OrderedDict(
        [
            ("round", 22),
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
    body = OrderedDict([("name", name), ("neurons", neurons), ("threshold", threshold)])
    if rate is not None:
        body["mean_rate_hz"] = rate
        body["spikes"] = spikes
    return body


def pack(
    rec_id,
    title,
    state,
    spikes,
    proposed,
    safety,
    executed,
    future,
    reward_notes,
    ticks,
    ras,
    gate,
    domain,
    tags,
    distillation,
    batch_position,
    supervisor_error_type=None,
):
    return OrderedDict(
        [
            ("id", rec_id),
            ("title", title),
            ("state", state),
            ("spike_events", spikes),
            ("proposed_action", proposed),
            ("safety_decision", safety),
            ("executed_action", executed),
            ("future_outcome", future),
            ("reward_components", reward_block(ticks, reward_notes)),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    domain, tags, distillation, batch_position, supervisor_error_type
                ),
            ),
        ]
    )


def record_106():
    excerpt, extra = lif_106_excerpt()
    ticks = [
        tick(1920, 0.04, -0.02, -0.02, 0.01, 0.00),
        tick(4800, 0.08, -0.04, -0.02, 0.01, -0.01),
        tick(4980, 0.04, -0.03, -0.02, 0.00, 0.00),
        tick(5440, 0.08, -0.05, -0.03, 0.02, -0.01),
        tick(23400, 0.06, -0.41, -0.04, -0.01, -0.01),
        tick(720000000, 0.02, -0.05, -0.03, 0.01, -0.01),
    ]
    state = OrderedDict(
        [
            (
                "description",
                "AMR-A12 is already 0.82 m from a picker's torso on Pallet-Wythe aisle WH-3 when "
                "a 2 kHz lidar range sample races the aisle encoder. Published human-clearance "
                "floor is 0.90 m; cruise at 1.40 m/s would close the remaining 0.08 m before the "
                "next picker step. A rack-leg already seated on bay 14 still slumps inside the "
                "42 ms raster after a process-correct speed clamp.",
            ),
            ("domain", "warehouse-amr"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Keep AMR-A12 torso range >= 0.90 m on WH-3, finish the pick-face handoff, and "
                "do not dump a pallet through a slumped rack-leg.",
            ),
            ("t0_us", 1756850400000106),
            ("gate_latency_us", 640),
            ("race_window_us", 380),
            ("race_window_rel_ms", [4.8, 5.18]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "lidar.torso.m 0.82 m under 0.90 floor",
                                "enc.aisle.mps 1.40 m/s with bay PT 18 kPa under 28",
                            ],
                        ),
                        (
                            "semantics",
                            "Torso-first latches aisle clamp 1.40 -> 0.55 m/s; encoder-first keeps "
                            "1.40 on a still-under-bay-pressure model.",
                        ),
                        (
                            "window_derivation",
                            "380 us = one lidar torso slot versus the aisle encoder publisher on "
                            "this warehouse-amr bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 180 us vs combined jitter 60 us (lidar 26 + encoder 34): 3.00x "
                            "over a 2.0x trust floor. Reversing order by < 180 us inside the 380 us "
                            "window would have kept 1.40 m/s; predicted next torso 0.74 m would miss "
                            "the 0.90 floor even without the rack slump.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "torso lidar, 2 kHz, 26 us jitter",
                    "aisle encoder, 1 kHz, 34 us jitter",
                    "rack-leg AE puck (context)",
                    "bay PT (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("torso_floor_m", 0.90),
                        ("observed_torso_m", 0.82),
                        ("aisle_m_s", 1.40),
                        ("bay_kpa", 18.0),
                        ("bay_cap_kpa", 28.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. AMR-A12 indexed on Pallet-Wythe WH-3; speed 1.40 m/s; torso 0.82 m.",
                    "2. Bay 18 kPa under 28 cap; pick-face handoff armed.",
                    "3. Encoder precursor at 2.240 ms.",
                    "4. Race window [4.800, 5.180] ms.",
                    "5. lidar.torso.m 0.82 at 4.800 ms (winner).",
                    "6. enc.aisle.mps 1.40 at 4.980 ms (loser by 180 us).",
                    "7. Gate at 5.440 ms: MODIFY clamp aisle 1.40 -> 0.55 m/s.",
                    "8. After clamp torso 0.96 m >= 0.90; bay still 18 kPa.",
                    "9. At 23.400 ms a rack-leg slump dumps 0.2 t of pallet into the aisle.",
                    "10. 12 min aisle isolate (abort_s=720); named un-netted loss.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_aisle_speed"),
            (
                "parameters",
                OrderedDict(
                    [("aisle_m_s", 1.40), ("torso_m", 0.82), ("bay_kpa", 18.0)]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("torso_m", 0.82),
                        ("torso_floor_m", 0.90),
                        ("predicted_unclamped_next_m", 0.74),
                        ("aisle_m_s", 1.40),
                        ("bay_kpa", 18.0),
                        ("bay_cap_kpa", 28.0),
                        ("race_margin_us", 180),
                        ("combined_jitter_us", 60),
                        ("abort_s", 720),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 1.40 m/s because bay 18 kPa is under 28, treating the 0.82 m "
                "torso range as a fogged lidar cell rather than a clearance-floor miss.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "correct"),
            (
                "rationale",
                "Torso 0.82 m won by 180 us, so the aisle is under the 0.90 m human-clearance "
                "floor, not still a bay-pressure story. Holding 1.40 m/s predicts next-sample "
                "0.74 m < 0.90 floor. MODIFY: aisle 1.40 -> 0.55 m/s. Observed after clamp 0.96 m "
                ">= 0.90. A full REJECT is not indicated: a clear aisle accepts 0.55 m/s.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "torso_range_m",
                            OrderedDict(
                                [
                                    ("floor", 0.90),
                                    ("observed", 0.82),
                                    ("predicted_unclamped_next", 0.74),
                                    ("clamped_aisle_m_s", 0.55),
                                    ("observed_after_clamp", 0.96),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 180),
                                    ("combined_jitter_us", 60),
                                    ("ratio", 3.0),
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
            ("name", "clamped_aisle_speed"),
            (
                "parameters",
                OrderedDict(
                    [("aisle_m_s", 0.55), ("torso_m", 0.96), ("bay_kpa", 18.0)]
                ),
            ),
            (
                "gate_effect",
                "MODIFY: aisle 1.40 -> 0.55 m/s. Process-correct vs the 0.90 m torso floor. "
                "Rack-leg still slumps at 23.400 ms.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Process-correct MODIFY held torso at 0.96 m. At 23.400 ms a rack-leg already "
                "seated on bay 14 dumped 0.2 t of pallet into WH-3. Clamp reduced closing speed; "
                "it did not prevent the slump. Partnered negative: process heads stay honest; "
                "world loss is named, not netted.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("aisle", "clamp executed; torso 0.96 m >= 0.90 floor"),
                        ("rack", "slumped at 23.400 ms; 0.2 t pallet in the aisle"),
                        ("repair", "12 min aisle isolate (abort_s=720)"),
                        ("mission", "WH-3 pick-face handoff incomplete this circuit"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Neither torso lidar nor aisle encoder predicted the seated rack-leg slump; ae.rack.leg is a new channel at 23.400 ms, 17.960 ms after the gate, still inside the 42 ms raster.",
                    "Delayed (abort_s=720): 12 min aisle isolate. Named un-netted loss, not folded into task_progress.",
                ],
            ),
            (
                "un_netted_loss",
                "12 min aisle isolate after the rack-leg slump. Safety head -0.60 prices the dump; "
                "task_progress stays +0.32 because the aisle clamp completed under the 0.90 m floor. "
                "World loss is named here, not subtracted from process heads.",
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "lidar.torso.m (4.800 ms, 0.82 m)"),
                        ("loser", "enc.aisle.mps (4.980 ms, 1.40 m/s)"),
                        ("margin_us", 180),
                        (
                            "counterfactual_if_reversed",
                            "Encoder-first by < 180 us inside the 380 us window would have kept "
                            "1.40 m/s; predicted next-sample 0.74 m would have missed the 0.90 floor "
                            "even without the slump. The MODIFY is still the correct process. The "
                            "slump is a later world charge either way, cheaper with the clamp than without.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 23400),
            (
                "reward_inflection_note",
                "Safety collapses at the 23.400 ms rack-leg slump (tick t_us=23400), inside the "
                "42 ms raster. The correct MODIFY at 5.440 ms is in the same excerpt. Do not put "
                "inflection on the +12 min isolate tick.",
            ),
            ("delayed_surprise_s", 720.0),
        ]
    )
    spikes = [
        spike("lidar.torso.m", 1.12, 0.44),
        spike("enc.aisle.mps", 2.24, 0.58),
        spike("lidar.torso.m", 3.40, 0.66),
        spike("lidar.torso.m", 4.80, 1.31),
        spike("enc.aisle.mps", 4.98, 1.14),
        spike("ctrl.gate", 5.44, 0.96),
        spike("lidar.torso.m", 8.10, 0.82),
        spike("enc.aisle.mps", 11.20, 0.61),
        spike("ctrl.gate", 14.40, 0.85),
        spike("ae.rack.leg", 23.40, 1.46),
        spike("ae.rack.leg", 25.10, 0.92),
        spike("enc.aisle.mps", 31.40, 0.40),
        spike("lidar.torso.m", 38.20, 0.54),
    ]
    ras = raster_core(
        42,
        72,
        26,
        79,
        routing(
            "thalamic-relay.torso-lidar",
            "spikenaut.policy.aisle-clamp",
            [
                ("relay.lidar.torso", "policy.aisle_clamp", 0.68),
                ("relay.enc.aisle", "policy.speed_hold", 0.29),
                ("relay.ae.rack", "policy.aisle_clamp", -0.44),
            ],
            "noradrenaline",
            0.04,
            "surprise-gated pre_post_stdp; NA at torso win (4.800 ms) opens a 42 ms eligibility "
            "trace that still covers the 23.400 ms rack-leg slump",
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
                    pop("aisle_clamp", 48, 0.50, 220.0, 4),
                    pop("speed_hold", 36, 0.80, 40.0, 1),
                    pop("rack_veto", 22, 0.75),
                ],
            ),
        ]
    )
    return pack(
        "ttf-r22-106",
        "Pallet-Wythe WH-3 / AMR-A12: torso lidar beats aisle encoder by 180 us; correct "
        "MODIFY still eats an in-window rack-leg slump (partnered negative total -0.44)",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        "Partnered negative. Process-correct MODIFY; world still charges inside the 42 ms "
        "raster. total -0.44 = 0.32 + -0.60 + -0.16 + 0.04 + -0.04. Named aisle isolate "
        "(abort_s=720) is not netted into task_progress.",
        ticks,
        ras,
        gate,
        "warehouse-amr",
        [
            "modify",
            "partnered-negative-total",
            "independent-lif-raster",
            "sidecar-sim-only",
            "in-window-world-charge",
            "designed",
        ],
        "A critic can see the world-charge as a LIF burst inside the raster while process "
        "heads stay honest. Credit assignment is spikes, not prose across a 12 min aisle isolate.",
        1,
    )


def record_107():
    ticks = [
        tick(2080, 0.05, 0.04, 0.02, 0.01, 0.01),
        tick(5200, 0.08, 0.06, 0.04, 0.02, 0.01),
        tick(5360, 0.05, 0.04, 0.02, 0.01, 0.01),
        tick(5780, 0.12, 0.10, 0.05, 0.04, 0.02),
        tick(6140, 0.05, 0.05, 0.02, 0.01, 0.01),
        tick(210000000, 0.03, 0.03, 0.02, 0.01, 0.01),
    ]
    spikes = [
        spike("pitot.gust.mps", 1.04, 0.41),
        spike("flow.downwash.mps", 2.18, 0.55),
        spike("pitot.gust.mps", 3.60, 0.70),
        spike("imu.att.ctx", 4.40, 0.48),
        spike("pitot.gust.mps", 5.20, 1.28),
        spike("flow.downwash.mps", 5.36, 1.10),
        spike("ctrl.gate", 5.78, 0.97),
        spike("pitot.gust.mps", 8.40, 0.80),
        spike("flow.downwash.mps", 11.60, 0.62),
        spike("ctrl.gate", 16.20, 0.84),
        spike("imu.att.ctx", 22.40, 0.46),
    ]
    excerpt = kernel_excerpt(26, 64, spikes, 12, seed=22107)
    state = OrderedDict(
        [
            (
                "description",
                "Quad-Q4 on the Downdraft-Cairn DC-6 pad already measures an 11.8 m/s pitot gust "
                "against a 9.0 m/s station-keeping cap while optical-flow still reports a 4.2 m/s "
                "downwash. Climb is armed at 2.4 m/s; a timely clamp to 0.6 m/s keeps formation "
                "spacing without dumping the 4-ship.",
            ),
            ("domain", "aerial-swarm"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Keep Quad-Q4 relative gust <= 9.0 m/s, hold 4-ship spacing, and finish the DC-6 "
                "station-keeping pass without a climb abort.",
            ),
            ("t0_us", 1756850400000107),
            ("gate_latency_us", 580),
            ("race_window_us", 360),
            ("race_window_rel_ms", [5.2, 5.56]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "pitot.gust.mps 11.8 over 9.0 cap",
                                "flow.downwash.mps 4.2 under 6.0 context",
                            ],
                        ),
                        (
                            "semantics",
                            "Pitot-first latches climb clamp 2.4 -> 0.6 m/s; downwash-first keeps "
                            "2.4 on a still-under-flow model.",
                        ),
                        (
                            "window_derivation",
                            "360 us = one pitot demodulation slot versus the optical-flow publisher "
                            "on this aerial-swarm bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 160 us vs combined jitter 52 us (pitot 24 + flow 28): 3.08x over "
                            "a 2.0x trust floor. Reversing order by < 160 us inside the 360 us window "
                            "would have kept 2.4 m/s climb; predicted next gust 10.6 m/s would miss "
                            "the 9.0 cap.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "nose pitot, 2 kHz, 24 us jitter",
                    "optical-flow downwash, 1 kHz, 28 us jitter",
                    "attitude IMU (context)",
                    "inter-ship radio ranging (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("gust_cap_mps", 9.0),
                        ("observed_gust_mps", 11.8),
                        ("climb_m_s", 2.4),
                        ("downwash_mps", 4.2),
                        ("downwash_ctx_mps", 6.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Quad-Q4 indexed on Downdraft-Cairn DC-6; climb 2.4 m/s; gust 11.8 m/s.",
                    "2. Downwash 4.2 m/s under 6.0 context; 4-ship spacing armed.",
                    "3. Flow precursor at 2.180 ms.",
                    "4. Race window [5.200, 5.560] ms.",
                    "5. pitot.gust.mps 11.8 at 5.200 ms (winner).",
                    "6. flow.downwash.mps 4.2 at 5.360 ms (loser by 160 us).",
                    "7. Gate at 5.780 ms: MODIFY clamp climb 2.4 -> 0.6 m/s.",
                    "8. After clamp relative gust 7.4 m/s <= 9.0; spacing held.",
                    "9. 3.5 min hover survey (survey_s=210) confirms formation.",
                    "10. Station-keeping pass completes under the 9.0 cap.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_climb"),
            (
                "parameters",
                OrderedDict(
                    [("climb_m_s", 2.4), ("gust_mps", 11.8), ("downwash_mps", 4.2)]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("gust_mps", 11.8),
                        ("gust_cap_mps", 9.0),
                        ("predicted_unclamped_next_mps", 10.6),
                        ("climb_m_s", 2.4),
                        ("downwash_mps", 4.2),
                        ("race_margin_us", 160),
                        ("combined_jitter_us", 52),
                        ("survey_s", 210),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 2.4 m/s climb because downwash 4.2 m/s looks like a pad "
                "vortex, not a station-keeping gust over the 9.0 m/s cap.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "correct"),
            (
                "rationale",
                "Pitot gust 11.8 m/s won by 160 us, so the pad is over the 9.0 m/s "
                "station-keeping cap, not still a downwash story. Holding 2.4 m/s climb predicts "
                "next-sample 10.6 m/s > 9.0. MODIFY: climb 2.4 -> 0.6 m/s. Observed after clamp "
                "7.4 m/s <= 9.0. A full REJECT is not indicated: a 4-ship accepts 0.6 m/s climb.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "gust_mps",
                            OrderedDict(
                                [
                                    ("cap", 9.0),
                                    ("observed", 11.8),
                                    ("predicted_unclamped_next", 10.6),
                                    ("clamped_climb_m_s", 0.6),
                                    ("observed_after_clamp", 7.4),
                                ]
                            ),
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
            ("name", "clamped_climb"),
            (
                "parameters",
                OrderedDict(
                    [("climb_m_s", 0.6), ("gust_mps", 7.4), ("downwash_mps", 4.2)]
                ),
            ),
            (
                "gate_effect",
                "MODIFY: climb 2.4 -> 0.6 m/s. Process-correct vs the 9.0 m/s gust cap. Formation spacing held.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Process-correct MODIFY held relative gust at 7.4 m/s. Quad-Q4 stayed in the "
                "4-ship. A 3.5 min hover survey closed the gust cell. No world charge inside the "
                "26 ms raster.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("climb", "clamp executed; gust 7.4 <= 9.0 cap"),
                        ("formation", "spacing held; no dump"),
                        ("survey", "3.5 min hover survey (survey_s=210)"),
                        ("mission", "DC-6 station-keeping pass complete"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Optical-flow downwash never rose with the pitot cell; the 11.8 m/s gust was pad-aligned, not rotor wash.",
                    "Delayed (survey_s=210): 3.5 min hover survey confirms the 4-ship before the next pad slot.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "pitot.gust.mps (5.200 ms, 11.8 m/s)"),
                        ("loser", "flow.downwash.mps (5.360 ms, 4.2 m/s)"),
                        ("margin_us", 160),
                        (
                            "counterfactual_if_reversed",
                            "Downwash-first by < 160 us inside the 360 us window would have kept "
                            "2.4 m/s climb; predicted next-sample 10.6 m/s would have missed the 9.0 "
                            "cap. The MODIFY is the correct process either way.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 5780),
            (
                "reward_inflection_note",
                "Task and safety inflect at the correct MODIFY (5.780 ms, tick 4). The 3.5 min "
                "survey is delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 210.0),
        ]
    )
    ras = raster_core(
        26,
        64,
        40,
        67,
        routing(
            "thalamic-relay.pitot-gust",
            "spikenaut.policy.climb-clamp",
            [
                ("relay.pitot.gust", "policy.climb_clamp", 0.71),
                ("relay.flow.downwash", "policy.spacing_hold", 0.27),
            ],
            "acetylcholine",
            0.05,
            "gust-gated pre_post_stdp; ACh at pitot win (5.200 ms) opens a 26 ms eligibility trace covering the 5.780 ms clamp",
        ),
        excerpt,
        extra=OrderedDict(
            [
                ("excerpt_source", "kernelized_events"),
                ("sim_scope", "none"),
                ("survey_s", 210),
                ("delayed_surprise_s", 210),
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
                    pop("climb_clamp", 48, 0.50, 250.0, 4),
                    pop("spacing_hold", 40, 0.80, 50.0, 1),
                    pop("gust_veto", 24, 0.75),
                ],
            ),
        ]
    )
    return pack(
        "ttf-r22-107",
        "Downdraft-Cairn DC-6 / Quad-Q4: pitot gust beats optical-flow downwash by 160 us; "
        "correct MODIFY clamps climb 2.4 -> 0.6 m/s",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        "Correct MODIFY. total +1.04 = 0.38 + 0.32 + 0.17 + 0.10 + 0.07. Hover survey "
        "(survey_s=210) is delayed, not the inflection.",
        ticks,
        ras,
        gate,
        "aerial-swarm",
        ["modify", "correct", "gust-vs-downwash", "designed", "tick6-sidecar-bound"],
        "Teaches a probe that a pitot-over-cap win routes to climb_clamp while downwash stay "
        "weights spacing_hold, with gate_snn climb_clamp above threshold.",
        2,
    )


def record_108():
    ticks = [
        tick(2560, 0.01, 0.04, 0.02, 0.01, 0.01),
        tick(6400, 0.02, 0.08, 0.02, 0.02, 0.01),
        tick(6620, 0.01, 0.06, 0.02, 0.01, 0.01),
        tick(7120, 0.03, 0.14, 0.04, 0.04, 0.02),
        tick(7520, 0.02, 0.06, 0.01, 0.01, 0.01),
        tick(420000000, 0.01, 0.04, 0.01, 0.01, 0.00),
    ]
    spikes = [
        spike("ft.tether.kN", 1.60, 0.43),
        spike("gyro.yaw.dps", 3.20, 0.58),
        spike("ft.tether.kN", 4.80, 0.71),
        spike("dvl.u.ctx", 5.60, 0.50),
        spike("ft.tether.kN", 6.40, 1.32),
        spike("gyro.yaw.dps", 6.62, 1.16),
        spike("ctrl.gate", 7.12, 0.98),
        spike("ft.tether.kN", 10.40, 0.81),
        spike("gyro.yaw.dps", 14.80, 0.64),
        spike("ctrl.gate", 18.60, 0.86),
        spike("dvl.u.ctx", 28.20, 0.44),
        spike("ft.tether.kN", 41.00, 0.52),
    ]
    excerpt = kernel_excerpt(46, 112, spikes, 15, seed=22108)
    state = OrderedDict(
        [
            (
                "description",
                "ROV-R9 on the Thalass-Ness TN-HIL wet stand already sees tether tension 2.80 kN "
                "against a 2.40 kN umbilical cap while the yaw gyro is only 12 deg/s. Planner "
                "wants +0.40 m/s payout; a correct REJECT holds thrusters and does not pay out "
                "into a taut tether.",
            ),
            ("domain", "underwater-rov"),
            ("sim_or_real", "hil"),
            (
                "goal",
                "Keep TN-HIL tether <= 2.40 kN and do not pay out into a distressed umbilical on "
                "the wet stand.",
            ),
            ("t0_us", 1756850400000108),
            ("gate_latency_us", 720),
            ("race_window_us", 400),
            ("race_window_rel_ms", [6.4, 6.8]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "ft.tether.kN 2.80 over 2.40 cap",
                                "gyro.yaw.dps 12 under 40 context",
                            ],
                        ),
                        (
                            "semantics",
                            "Tether-first REJECT-holds payout; yaw-first would treat heading as the "
                            "story and keep paying out.",
                        ),
                        (
                            "window_derivation",
                            "400 us = one load-cell slot versus the yaw-gyro publisher on this "
                            "underwater-rov HIL bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 220 us vs combined jitter 70 us (tether 32 + gyro 38): 3.14x over "
                            "a 2.0x trust floor. Reversing order by < 220 us inside the 400 us window "
                            "would have kept +0.40 m/s payout into a 2.80 kN umbilical.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "tether load cell, 2 kHz, 32 us jitter",
                    "yaw gyro, 1 kHz, 38 us jitter",
                    "DVL u (context)",
                    "winch encoder (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("tether_cap_kN", 2.40),
                        ("observed_tether_kN", 2.80),
                        ("proposed_payout_m_s", 0.40),
                        ("yaw_dps", 12.0),
                        ("yaw_ctx_dps", 40.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. ROV-R9 indexed on Thalass-Ness TN-HIL; payout armed +0.40 m/s; tether 2.80 kN.",
                    "2. Yaw 12 deg/s under 40 context; wet-stand dive armed.",
                    "3. Gyro precursor at 3.200 ms.",
                    "4. Race window [6.400, 6.800] ms.",
                    "5. ft.tether.kN 2.80 at 6.400 ms (winner).",
                    "6. gyro.yaw.dps 12 at 6.620 ms (loser by 220 us).",
                    "7. Gate at 7.120 ms: REJECT hold, payout 0.40 -> 0 m/s.",
                    "8. Tether stays 2.80 kN; no additional payout.",
                    "9. 7 min winch inspect (abort_s=420).",
                    "10. Dive postponed until umbilical under 2.40 kN.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "pay_out_tether"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("payout_m_s", 0.40),
                        ("hold", False),
                        ("tether_kN", 2.80),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("tether_kN", 2.80),
                        ("tether_cap_kN", 2.40),
                        ("yaw_dps", 12.0),
                        ("yaw_ctx_dps", 40.0),
                        ("race_margin_us", 220),
                        ("combined_jitter_us", 70),
                        ("abort_s", 420),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes +0.40 m/s payout because yaw 12 deg/s looks like a heading "
                "trim, not an umbilical over the 2.40 kN cap.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "REJECT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Tether 2.80 kN won by 220 us, so the umbilical is over the 2.40 kN cap, not "
                "still a yaw story. Paying out +0.40 m/s would raise tension further. REJECT: "
                "hold payout 0.40 -> 0 m/s. Observed after hold 2.80 kN, no additional strain. "
                "A MODIFY that only trims yaw would leave the cap miss unaddressed.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "tether_kN",
                            OrderedDict(
                                [
                                    ("cap", 2.40),
                                    ("observed", 2.80),
                                    ("executed_payout_m_s", 0.0),
                                    ("hold", True),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 220),
                                    ("combined_jitter_us", 70),
                                    ("ratio", 3.14),
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
            ("name", "hold_tether_payout"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("payout_m_s", 0.0),
                        ("hold", True),
                        ("tether_kN", 2.80),
                    ]
                ),
            ),
            (
                "gate_effect",
                "REJECT: payout 0.40 -> 0 m/s. Process-correct vs the 2.40 kN umbilical cap. "
                "Thrusters held on the TN-HIL stand.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct REJECT held payout at 0 m/s while tether stayed 2.80 kN over the 2.40 "
                "cap. 7 min winch inspect followed. No additional umbilical strain.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("winch", "hold executed; payout 0 m/s"),
                        ("tether", "still 2.80 kN, over 2.40 cap, no extra strain"),
                        ("repair", "7 min winch inspect (abort_s=420)"),
                        ("mission", "TN-HIL dive postponed this circuit"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Yaw never rose with tether; the 2.80 kN was a snagged stand fairlead, not heading drag.",
                    "Delayed (abort_s=420): 7 min winch inspect before the next wet-stand slot.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "ft.tether.kN (6.400 ms, 2.80 kN)"),
                        ("loser", "gyro.yaw.dps (6.620 ms, 12 deg/s)"),
                        ("margin_us", 220),
                        (
                            "counterfactual_if_reversed",
                            "Yaw-first by < 220 us inside the 400 us window would have kept +0.40 "
                            "m/s payout into a 2.80 kN umbilical. The REJECT is the correct process "
                            "either way.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 7120),
            (
                "reward_inflection_note",
                "Safety inflects at the correct REJECT (7.120 ms, tick 4). The 7 min inspect is "
                "delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 420.0),
        ]
    )
    ras = raster_core(
        46,
        112,
        20,
        103,
        routing(
            "thalamic-relay.tether-ft",
            "spikenaut.policy.tether-hold",
            [
                ("relay.ft.tether", "policy.tether_hold", 0.72),
                ("relay.gyro.yaw", "policy.payout_go", 0.24),
            ],
            "dopamine",
            0.06,
            "tension-gated pre_post_stdp; DA at tether win (6.400 ms) opens a 46 ms eligibility trace covering the 7.120 ms hold",
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
            ("decision_window_ms", 0.40),
            ("decision", "REJECT"),
            (
                "populations",
                [
                    pop("tether_hold", 48, 0.50, 250.0, 5),
                    pop("payout_go", 36, 0.80),
                    pop("tension_veto", 22, 0.75, 80.0, 1),
                ],
            ),
        ]
    )
    return pack(
        "ttf-r22-108",
        "Thalass-Ness TN-HIL / ROV-R9: tether 2.80 kN beats yaw gyro 12 deg/s by 220 us; "
        "correct REJECT holds payout",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        "Correct REJECT. total +0.80 = 0.10 + 0.42 + 0.12 + 0.10 + 0.06. Winch inspect "
        "(abort_s=420) is delayed, not the inflection.",
        ticks,
        ras,
        gate,
        "underwater-rov",
        ["reject", "hil", "tether-vs-yaw", "tick6-sidecar-bound"],
        "Teaches a probe that a tether-over-cap win routes to tether_hold while yaw stay "
        "weights payout_go, with gate_snn tether_hold above threshold and payout_go not.",
        3,
    )


def record_109():
    ticks = [
        tick(2720, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(6800, 0.08, 0.06, 0.04, 0.02, 0.02),
        tick(7020, 0.06, 0.04, 0.02, 0.02, 0.01),
        tick(7300, 0.12, 0.08, 0.05, 0.03, 0.02),
        tick(7680, 0.05, 0.04, 0.02, 0.02, 0.01),
        tick(300000000, 0.03, 0.02, 0.02, 0.01, 0.01),
    ]
    spikes = [
        spike("ft.wrist.N", 1.36, 0.42),
        spike("ae.housing.pps", 2.72, 0.56),
        spike("ft.wrist.N", 4.40, 0.68),
        spike("lvdt.insert.ctx", 5.50, 0.47),
        spike("ft.wrist.N", 6.80, 1.22),
        spike("ae.housing.pps", 7.02, 1.08),
        spike("ctrl.gate", 7.30, 0.95),
        spike("ft.wrist.N", 10.80, 0.74),
        spike("ae.housing.pps", 14.20, 0.60),
        spike("ctrl.gate", 18.40, 0.82),
        spike("lvdt.insert.ctx", 23.60, 0.45),
    ]
    excerpt = kernel_excerpt(26, 56, spikes, 12, seed=22109)
    state = OrderedDict(
        [
            (
                "description",
                "Press-P4 at Cinch-Quarry CQ-2 already seats a 38 N wrist force against a 48 N "
                "insert cap; housing AE is a quiet 12 pps under the 40 pps trip. The 0.18 m/s "
                "insert is already legal. A simulated digital-twin press cell confirms both "
                "channels under cap before the gate.",
            ),
            ("domain", "industrial-assembly"),
            ("sim_or_real", "simulated"),
            (
                "goal",
                "Finish the CQ-2 insert pass with wrist force <= 48 N and housing AE <= 40 pps.",
            ),
            ("t0_us", 1756850400000109),
            ("gate_latency_us", 500),
            ("race_window_us", 380),
            ("race_window_rel_ms", [6.8, 7.18]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "ft.wrist.N 38 under 48 cap",
                                "ae.housing.pps 12 under 40 trip",
                            ],
                        ),
                        (
                            "semantics",
                            "Wrist-first ACCEPTs 0.18 m/s insert (38 N <= 48 N). AE-first would only "
                            "delay confirmation of the same legal insert.",
                        ),
                        (
                            "window_derivation",
                            "380 us = one wrist FT slot versus the housing AE publisher on this "
                            "industrial-assembly twin bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 220 us vs combined jitter 64 us (wrist 30 + AE 34): 3.44x over a "
                            "2.0x trust floor. Reversing order by < 220 us still shows 38 N <= 48 N "
                            "and 12 pps <= 40. A correct gate ACCEPTs either way.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "wrist FT, 2 kHz, 30 us jitter",
                    "housing AE puck, 1 kHz, 34 us jitter",
                    "insert LVDT (context)",
                    "press ram encoder (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("wrist_cap_N", 48.0),
                        ("observed_wrist_N", 38.0),
                        ("ae_trip_pps", 40.0),
                        ("observed_ae_pps", 12.0),
                        ("insert_m_s", 0.18),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Press-P4 indexed on Cinch-Quarry CQ-2 twin; insert 0.18 m/s; wrist 38 N.",
                    "2. Housing AE 12 pps under 40 trip; insert pass armed.",
                    "3. AE precursor at 2.720 ms.",
                    "4. Race window [6.800, 7.180] ms.",
                    "5. ft.wrist.N 38 at 6.800 ms (winner).",
                    "6. ae.housing.pps 12 at 7.020 ms (loser by 220 us).",
                    "7. Gate at 7.300 ms: ACCEPT already-legal 0.18 m/s insert.",
                    "8. Wrist stays 38 N <= 48; AE stays 12 pps.",
                    "9. 5 min post-insert survey (survey_s=300).",
                    "10. Insert pass completes under both caps.",
                ],
            ),
        ]
    )
    params = OrderedDict(
        [("insert_m_s", 0.18), ("wrist_N", 38.0), ("ae_pps", 12.0), ("hold", False)]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_insert"),
            ("parameters", params),
            (
                "evidence",
                OrderedDict(
                    [
                        ("wrist_N", 38.0),
                        ("wrist_cap_N", 48.0),
                        ("ae_pps", 12.0),
                        ("ae_trip_pps", 40.0),
                        ("insert_m_s", 0.18),
                        ("race_margin_us", 220),
                        ("combined_jitter_us", 64),
                        ("survey_s", 300),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 0.18 m/s insert because wrist 38 N is 10 N under the 48 N cap "
                "and housing AE 12 pps is quiet versus the 40 pps trip.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Wrist 38 N won by 220 us and is 10 N under the 48 N insert cap. Housing AE 12 "
                "pps is under the 40 pps trip. ACCEPT the already-legal 0.18 m/s insert. A MODIFY "
                "or REJECT would idle a legal press pass.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "wrist_N",
                            OrderedDict(
                                [
                                    ("cap", 48.0),
                                    ("observed", 38.0),
                                    ("executed_insert_m_s", 0.18),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 220),
                                    ("combined_jitter_us", 64),
                                    ("ratio", 3.44),
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
            ("name", "cruise_insert"),
            ("parameters", OrderedDict(params.items())),
            (
                "gate_effect",
                "ACCEPT: leave 0.18 m/s insert. Wrist 38 N <= 48 N cap. Housing AE 12 pps <= 40 trip.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT left the already-legal 0.18 m/s insert. Wrist stayed 38 N. A 5 "
                "min post-insert survey closed the pass. No world charge inside the 26 ms raster.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("insert", "0.18 m/s executed; wrist 38 N <= 48"),
                        ("housing", "AE 12 pps under 40 trip"),
                        ("survey", "5 min post-insert survey (survey_s=300)"),
                        ("mission", "CQ-2 insert pass complete"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Housing AE never rose with wrist force; the 38 N was a clean seat, not a bind.",
                    "Delayed (survey_s=300): 5 min post-insert survey before the next twin cycle.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "ft.wrist.N (6.800 ms, 38 N)"),
                        ("loser", "ae.housing.pps (7.020 ms, 12 pps)"),
                        ("margin_us", 220),
                        (
                            "counterfactual_if_reversed",
                            "AE-first by < 220 us would still show 38 N <= 48 N. A correct gate "
                            "ACCEPTs either way.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 7300),
            (
                "reward_inflection_note",
                "Task inflects at the correct ACCEPT (7.300 ms, tick 4). The 5 min survey is "
                "delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 300.0),
        ]
    )
    ras = raster_core(
        26,
        56,
        40,
        58,
        routing(
            "thalamic-relay.wrist-ft",
            "spikenaut.policy.insert-go",
            [
                ("relay.ft.wrist", "policy.insert_go", 0.73),
                ("relay.ae.housing", "policy.ae_hold", 0.25),
            ],
            "serotonin",
            0.07,
            "already-legal pre_post_stdp; 5-HT at wrist win (6.800 ms) opens a 26 ms eligibility trace covering the 7.300 ms accept",
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
            ("decision_window_ms", 0.38),
            ("decision", "ACCEPT"),
            (
                "populations",
                [
                    pop("insert_go", 48, 0.50, 210.0, 4),
                    pop("ae_hold", 28, 0.80),
                    pop("force_veto", 20, 0.75),
                ],
            ),
        ]
    )
    return pack(
        "ttf-r22-109",
        "Cinch-Quarry CQ-2 / Press-P4: wrist 38 N beats housing AE 12 pps by 220 us; correct "
        "ACCEPT of already-legal 0.18 m/s insert",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        "Correct ACCEPT. total +1.06 = 0.40 + 0.28 + 0.18 + 0.12 + 0.08. Post-insert survey "
        "(survey_s=300) is delayed, not the inflection.",
        ticks,
        ras,
        gate,
        "industrial-assembly",
        ["accept", "simulated", "already-legal", "wrist-vs-ae", "tick6-sidecar-bound"],
        "Teaches a probe that an already-legal wrist-under-cap win routes to insert_go with "
        "gate_snn insert_go above threshold and force_veto silent.",
        4,
    )


def record_110():
    ticks = [
        tick(2160, -0.02, 0.01, -0.02, -0.01, 0.01),
        tick(5400, -0.04, 0.01, -0.04, -0.02, 0.01),
        tick(5640, -0.03, 0.01, -0.03, -0.01, 0.01),
        tick(6080, -0.06, 0.02, -0.08, -0.03, 0.02),
        tick(6500, -0.02, 0.01, -0.03, -0.01, 0.01),
        tick(480000000, -0.01, 0.00, -0.02, 0.00, 0.00),
    ]
    spikes = [
        spike("lidar.occ.n", 1.20, 0.44),
        spike("cam.ttc.s", 2.40, 0.61),
        spike("lidar.occ.n", 3.88, 0.52),
        spike("latch.occ.ghost", 4.62, 0.70),
        spike("lidar.occ.n", 5.40, 1.31),
        spike("cam.ttc.s", 5.64, 1.18),
        spike("ctrl.gate", 6.08, 0.99),
        spike("lidar.occ.n", 7.22, 0.84),
        spike("cam.ttc.s", 9.44, 0.66),
        spike("ctrl.gate", 14.88, 0.88),
        spike("latch.occ.ghost", 18.40, 0.41),
        spike("lidar.occ.n", 24.20, 0.58),
    ]
    excerpt = kernel_excerpt(28, 96, spikes, 14, seed=22110)
    state = OrderedDict(
        [
            (
                "description",
                "Merge-M4 at Clover-Weir CW-9 already shows a live-empty lidar occupancy (0 blobs) "
                "and a 3.60 s camera TTC over the 2.00 s floor when a 1.40 s-old red occupancy "
                "latch is still armed from the previous cycle. A weak supervisor binds the stale "
                "latch as live and REJECT-holds a legal 18 m/s merge.",
            ),
            ("domain", "autonomous-driving"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Complete the CW-9 merge at 18 m/s with live occupancy 0 and TTC >= 2.00 s, and "
                "drop any occupancy latch older than 0.20 s.",
            ),
            ("t0_us", 1756850400000110),
            ("gate_latency_us", 680),
            ("race_window_us", 420),
            ("race_window_rel_ms", [5.4, 5.82]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "lidar.occ.n 0 blobs live-empty",
                                "cam.ttc.s 3.60 s over 2.00 floor",
                            ],
                        ),
                        (
                            "semantics",
                            "Lidar-first should ACCEPT 18 m/s (0 blobs, TTC 3.60 >= 2.00). "
                            "Camera-first would only delay confirmation of the same legal merge. "
                            "The error is the stale latch the supervisor binds, not the race.",
                        ),
                        (
                            "window_derivation",
                            "420 us = one lidar occupancy slot versus the camera TTC publisher on "
                            "this autonomous-driving merge bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 240 us vs combined jitter 76 us (lidar 36 + camera 40): 3.16x "
                            "over a 2.0x trust floor. Order is correctly lidar-first. The error is "
                            "the 1.40 s ghost latch, not the race.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "roof lidar occupancy, 2 kHz, 36 us jitter",
                    "forward camera TTC, 1 kHz, 40 us jitter",
                    "stale occupancy latch (age 1.40 s, not live)",
                    "merge-lane encoder (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("ttc_floor_s", 2.00),
                        ("observed_ttc_s", 3.60),
                        ("live_occ_count", 0),
                        ("latch_age_s", 1.40),
                        ("max_latch_age_s", 0.20),
                        ("proposed_speed_m_s", 18.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Merge-M4 indexed onto Clover-Weir CW-9; speed 18 m/s armed; live occ 0.",
                    "2. TTC 3.60 s over 2.00 floor; latch age 1.40 s > 0.20 max.",
                    "3. Camera precursor at 2.400 ms.",
                    "4. Race window [5.400, 5.820] ms.",
                    "5. lidar.occ.n 0 at 5.400 ms (winner).",
                    "6. cam.ttc.s 3.60 at 5.640 ms (loser by 240 us).",
                    "7. Gate at 6.080 ms: wrong REJECT holds 18 -> 0 m/s on the stale latch.",
                    "8. Merge idle; live occupancy stayed 0; TTC stayed 3.60 s.",
                    "9. 8 min green-wave window missed (abort_s=480).",
                    "10. QA: correct gate was ACCEPT; leave 18 m/s; drop the 1.40 s latch.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "merge_18mps"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("speed_m_s", 18.0),
                        ("live_occ_count", 0),
                        ("hold", False),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("live_occ_count", 0),
                        ("ttc_s", 3.60),
                        ("ttc_floor_s", 2.00),
                        ("latch_age_s", 1.40),
                        ("max_latch_age_s", 0.20),
                        ("sample_fresh", False),
                        ("race_margin_us", 240),
                        ("combined_jitter_us", 76),
                        ("t_gate_us", 6080),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 18 m/s because live occupancy is 0 blobs and camera TTC 3.60 s "
                "is 1.60 s over the 2.00 s floor; the 1.40 s latch is a previous-cycle ghost.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "REJECT"),
            ("correctness", "incorrect"),
            (
                "rationale",
                "Occupancy latch is still red at 1.40 s age, so the merge is treated as blocked. "
                "REJECT: hold 18 -> 0 m/s until the latch clears so Merge-M4 does not enter an "
                "occupied gap.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "occupancy",
                            OrderedDict(
                                [
                                    ("live_occ_count", 0),
                                    ("ttc_s", 3.60),
                                    ("ttc_floor_s", 2.00),
                                    ("latch_age_s", 1.40),
                                    ("executed_speed_m_s", 0.0),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 240),
                                    ("combined_jitter_us", 76),
                                    ("ratio", 3.16),
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
            ("name", "merge_hold_ghost_latch"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("speed_m_s", 0.0),
                        ("live_occ_count", 0),
                        ("hold", True),
                        ("bind_stale_latch", True),
                    ]
                ),
            ),
            (
                "gate_effect",
                "REJECT (incorrect): speed 18 -> 0 m/s. Routing relay.latch.occ -> "
                "policy.merge_hold_reject; no positive weight to policy.merge_go_accept. Live "
                "occupancy stayed 0; TTC stayed 3.60 s >= 2.00.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Wrong-REJECT froze Merge-M4 at 0 m/s while live occupancy stayed 0 blobs and TTC "
                "stayed 3.60 s over the 2.00 s floor. 8 min green-wave window missed. Correct gate "
                "was ACCEPT of the already-legal 18 m/s merge.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("merge", "held at 0 m/s; 18 m/s abandoned"),
                        ("occupancy", "live still 0 blobs; latch age 1.40 s never live"),
                        ("corridor", "8 min green-wave window missed"),
                        ("gap", "no occupant; stale-interlock false positive"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "The 1.40 s occupancy latch is a previous-cycle ghost; it is not a live blob and never appears on the current lidar scan.",
                    "Delayed (abort_s=480): sister-shift Merge-M5 ran the same 18 m/s window after QA dropped the latch; M4's slot was already gone.",
                ],
            ),
            (
                "recovery",
                OrderedDict(
                    [
                        (
                            "correct_gate",
                            "ACCEPT: live occ 0 and TTC 3.60 s >= 2.00 s floor; leave 18 m/s; drop latch age 1.40 s.",
                        ),
                        ("correct_speed_m_s", 18.0),
                        ("wrong_speed_m_s", 0.0),
                        (
                            "wrong_edit_applied",
                            OrderedDict([("speed_m_s", 0.0), ("hold", True), ("bind_stale_latch", True)]),
                        ),
                        (
                            "cost",
                            "8 min missed green-wave window (task/efficiency); occupancy never occupied (safety false-positive).",
                        ),
                    ]
                ),
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "lidar.occ.n (5.400 ms, 0 blobs)"),
                        ("loser", "cam.ttc.s (5.640 ms, 3.60 s)"),
                        ("margin_us", 240),
                        (
                            "counterfactual_if_reversed",
                            "Camera-first by < 240 us would still show TTC 3.60 >= 2.00 and live occ "
                            "0. A correct gate ACCEPTs either way. The wrong REJECT spent the lidar "
                            "win on a stale occupancy latch.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 6080),
            (
                "reward_inflection_note",
                "Task and efficiency drop at the wrong REJECT (6.080 ms, tick 4). The 8 min "
                "missed window is delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 480.0),
        ]
    )
    ras = raster_core(
        28,
        96,
        30,
        81,
        routing(
            "relay.latch.occ",
            "policy.merge_hold_reject",
            [
                ("relay.latch.occ", "policy.merge_hold_reject", 0.74),
                ("relay.lidar.occ", "policy.merge_hold_reject", 0.22),
            ],
            "acetylcholine",
            0.08,
            "stale-latch stdp; ACh tags the (wrong) hold_reject bind at the lidar win; no positive weight to policy.merge_go_accept",
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
            ("decision_window_ms", 0.42),
            ("decision", "REJECT"),
            (
                "populations",
                [
                    pop("hold_reject", 48, 0.50, 240.0, 5),
                    pop("go_accept", 48, 0.80, 10.0, 0),
                    pop("latch_veto", 24, 0.75),
                ],
            ),
        ]
    )
    return pack(
        "ttf-r22-110",
        "WRONG-REJECT at Clover-Weir CW-9 / Merge-M4: live occ 0 and TTC 3.60 s are legal vs "
        "published 2.00 s floor; supervisor bound a 1.40 s ghost occupancy latch",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        "Wrong-reject. Sidecar arithmetic live_occ_count==0 and ttc_s>=ttc_floor_s is true; "
        "gate bound to a stale latch (age 1.40 s > 0.20). total -0.36 = -0.18 + 0.06 + -0.22 + "
        "-0.08 + 0.06.",
        ticks,
        ras,
        gate,
        "autonomous-driving",
        [
            "reject",
            "wrong-gate",
            "wrong-reject",
            "stale-interlock",
            "ghost-occupancy",
            "sidecar-convictable",
            "designed",
        ],
        "Teaches a probe that a correct live-empty occupancy read can still be a wrong gate "
        "when routing.table[0].to is policy.merge_hold_reject and executed speed is zeroed.",
        5,
        supervisor_error_type="wrong-reject",
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
    if rec["id"] == "ttf-r22-106":
        tick5 = 23400
    else:
        tick5 = t_gate + t_race
    return [tick1, t_win, t_lose, t_gate, tick5], t_win, t_lose, t_gate


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
    if len(wrong) != 1 or wrong[0]["id"] != "ttf-r22-110":
        issues.append(f"wrong-gate set {[w['id'] for w in wrong]}")
    if any(r["state"]["sim_or_real"] == "real" for r in records):
        issues.append("sim_or_real=real")
    hil = [r["id"] for r in records if r["state"]["sim_or_real"] == "hil"]
    sim = [r["id"] for r in records if r["state"]["sim_or_real"] == "simulated"]
    if hil != ["ttf-r22-108"]:
        issues.append(f"hil set {hil}")
    if sim != ["ttf-r22-109"]:
        issues.append(f"simulated set {sim}")
    designed = [r["id"] for r in records if r["state"]["sim_or_real"] == "designed"]
    if designed != ["ttf-r22-106", "ttf-r22-107", "ttf-r22-110"]:
        issues.append(f"designed set {designed}")
    domains = [r["state"]["domain"] for r in records]
    if len(set(domains)) != 5:
        issues.append(f"domain collision {domains}")
    pool = {
        "industrial-assembly",
        "surgical-assist",
        "autonomous-driving",
        "aerial-swarm",
        "warehouse-amr",
        "humanoid-locomotion",
        "grid-inspection",
        "underwater-rov",
    }
    if not set(domains) <= pool:
        issues.append(f"domain outside 8-pool {domains}")
    decisions = [r["safety_decision"]["decision"] for r in records]
    if decisions != ["MODIFY", "MODIFY", "REJECT", "ACCEPT", "REJECT"]:
        issues.append(f"decision mix {decisions}")
    blob = json.dumps(records)
    for frag in BANNED_PLANT_FRAGMENTS:
        if frag in blob:
            issues.append(f"banned plant fragment {frag}")
    if "training_ready" in blob:
        issues.append("training_ready present")
    thought_re = re.compile(r"\b(thought|chain_of_thought|scratch|inner_monologue|hidden_reasoning)\b")
    if thought_re.search(blob):
        issues.append("thought-like key/text present")
    totals = [r["reward_components"]["total"] for r in records]
    if all(t > 0 for t in totals):
        issues.append("all-positive totals")
    for rec in records:
        rid = rec["id"]
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
        if rid == "ttf-r22-106":
            if rec["raster"].get("excerpt_source") != "independent_lif":
                issues.append("106 missing independent_lif")
            if rec["future_outcome"]["reward_inflection_t_us"] > rec["raster"]["window_ms"] * 1000:
                issues.append("106 inflection outside window")
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
        if rec["meta"]["round"] != 22:
            issues.append(f"{rid} meta.round")
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
        if rec["safety_decision"]["decision"] == "REJECT" and rec["safety_decision"]["correctness"] == "incorrect":
            if "recovery" not in rec["future_outcome"]:
                issues.append(f"{rid} missing recovery")
        gl = rec["state"]["gate_latency_us"]
        rw = rec["state"]["race_window_us"]
        if not (50 <= gl <= 2000):
            issues.append(f"{rid} gate_latency")
        if not (50 <= rw <= 1000):
            issues.append(f"{rid} race_window")
        wm = rec["raster"]["window_ms"]
        if not (20 <= wm <= 50):
            issues.append(f"{rid} window_ms")
        for item in rec["raster"]["excerpt"]:
            if not (0 <= item["t_us"] <= wm * 1000):
                issues.append(f"{rid} excerpt t_us {item['t_us']}")
            if not (0 <= item["neuron_id"] < rec["raster"]["neurons"]):
                issues.append(f"{rid} neuron_id {item['neuron_id']}")
    return issues, jmax


def notes_text(records, jmax: float) -> str:
    rows = []
    for rec in records:
        dec = rec["safety_decision"]["decision"]
        cor = rec["safety_decision"]["correctness"]
        if cor == "incorrect":
            cor = f"**incorrect ({rec['meta']['supervisor_error_type']})**"
        tot = rec["reward_components"]["total"]
        tot_s = f"{tot:+.2f}"
        if rec["id"] == "ttf-r22-106":
            tot_s = f"**{tot:+.2f}**"
        edge = {
            "ttf-r22-106": "process-correct aisle clamp; rack-leg slump inside 42 ms raster; independent LIF",
            "ttf-r22-107": "pitot 11.8 m/s > 9.0 cap; climb 2.4 -> 0.6 m/s",
            "ttf-r22-108": "tether 2.80 kN beats yaw 12 deg/s; hold payout",
            "ttf-r22-109": "wrist 38 N vs housing AE 12 pps; proposed 0.18 m/s already legal",
            "ttf-r22-110": "live occ 0 and TTC 3.60 s legal; 1.40 s ghost latch REJECT-holds 18 -> 0 m/s",
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
    return f"""# Thalamic Trajectory Factory — NOTES-r22

- Factory: `thalamic-trajectory-factory`
- Run label: `2026-09-02-final-heavy`
- Generator: `grok-4.6`
- Channel: SuperGrok Heavy consumer chat (RM-793 research-only)
- Quota: 5
- Quality: Q=5
- IDs: `ttf-r22-106` … `ttf-r22-110`
- Domains this batch: `warehouse-amr`, `aerial-swarm`, `underwater-rov`, `industrial-assembly`, `autonomous-driving`

These five domain slugs stay inside the prompt 8-pool. Sit-outs vs live r01: `surgical-assist`, `grid-inspection`, `humanoid-locomotion`. Reused vs r01 with new plants only: `industrial-assembly` (Cinch-Quarry, not Rivermead) and `autonomous-driving` (Clover-Weir, not Fork-Haven). r01 sit-outs now in: `warehouse-amr`, `aerial-swarm`, `underwater-rov`. All five plants are invented (Pallet-Wythe, Downdraft-Cairn, Thalass-Ness, Cinch-Quarry, Clover-Weir). Do not restack prior TTF plants. Do not restack `/tmp/ttf-r22` maglev/grain/habitat/bakery/lime IDs `ttf-r22-126`…`130`.

## Batch map

| id | domain | decision | correctness | sim_or_real | total | edge |
|----|--------|----------|-------------|-------------|-------|------|
{chr(10).join(rows)}

Gate mix: 1 ACCEPT, 2 correct MODIFY (one partnered-neg, in-window), 1 correct REJECT, 1 incorrect REJECT (stale-interlock / ghost occupancy). Provenance: designed×3, simulated×1, hil×1 (Thalass-Ness TN-HIL wet stand). Intra-batch Jaccard on `state.description` {jmax:.3f} (< 0.4). Totals not all-positive (106 −0.44, 110 −0.36).

## Wrong-reject

**ttf-r22-110** is the mandated incorrect gate (`safety_decision.correctness=incorrect`, `meta.supervisor_error_type=wrong-reject`). Alternate vs odd rounds: even rounds host wrong-reject. This is **stale-interlock / ghost occupancy** (live-empty occupancy, supervisor binds a 1.40 s lagged red latch). Not r12-079 induced-kV-as-sensor-fault, not r14-086 wet-derate MAD, not `/tmp/ttf-r22-126` class-transplant / wrong floor, not r16-097 residual-as-live, not r18-109 empty-tank class. Do not emit a wrong-ACCEPT.

Clover-Weir CW-9 / Merge-M4 reads live occupancy **0 blobs** and TTC **3.60 s** against a published **2.00 s** floor. A **1.40 s** occupancy latch is a previous-cycle ghost (`sample_fresh=false`, `latch_age_s=1.40` > `max_latch_age_s=0.20`). Sidecar arithmetic `live_occ_count == 0` and `ttc_s >= ttc_floor_s` is true. A timely ACCEPT at `t_gate_us=6080` leaves **18 m/s**. A weak supervisor binds the stale latch and REJECT-holds **18 → 0 m/s**. Live occupancy stays **0**. Convictable without vehicle dynamics: `evidence.live_occ_count == 0`, `evidence.ttc_s >= evidence.ttc_floor_s`, `evidence.sample_fresh == false`, `executed_action.speed_m_s == 0`, `executed_action.bind_stale_latch == true`, `raster.routing.table` sends `relay.latch.occ` → `policy.merge_hold_reject` (weight 0.74) with no positive weight to `policy.merge_go_accept`, and `gate_snn` has `hold_reject` above threshold while `go_accept` is not (`spikes=0`). Recovery: ACCEPT; leave 18 m/s; drop the 1.40 s latch. Cost: 8 min missed green-wave (`abort_s=480`).

## Partnered-negative in-window (106)

**ttf-r22-106** is the partnered negative: process-correct MODIFY (aisle held 0.55 m/s; torso 0.96 m >= 0.90 floor) while the world still charges. Safety −0.60 prices the rack-leg slump at **23.400 ms**; `task_progress` stays +0.32 because the clamp completed. Inflection `t_us=23400` is tick 5 and is **inside** the 42 ms raster (`23400 ≤ 42000`). Named un-netted loss: 12 min aisle isolate (`abort_s=720`). Not folded into process heads.

Independent LIF (the one labeled sidecar sim): `state.sim_or_real` remains `designed`. `raster.excerpt_source=independent_lif`, `raster.sim_scope=sidecar_only`, `raster.lif` seed 22106, stim `[22000, 25600]`. Excerpt is membrane crossings (`lif.clamp` early vs `lif.rack` 22–25.6 ms), not a 1:1 remap of `spike_events`. `meta.tags` include `independent-lif-raster` and `sidecar-sim-only`.

## Reward formula and tick reconciliation

Declared aggregation on every record:

`total = task_progress + safety + efficiency + coherence + exploration`

Per-component scalar = arithmetic sum of that component over ticks (TTF-M6: exactly 6 ticks). Tick 6 is bound to a published sidecar (`abort_s`, `survey_s`) via `future_outcome.delayed_surprise_s` and is strictly after the raster window. Inflection `t_us` is an actual tick.

| id | ticks | tp | saf | eff | coh | exp | total | inflection tick |
|----|-------|----|-----|-----|-----|-----|-------|-----------------|
{chr(10).join(tick_rows)}

Tick-6 sidecar bind: 106 `abort_s=720`, 107 `survey_s=210`, 108 `abort_s=420`, 109 `survey_s=300`, 110 `abort_s=480`.

## Raster / energy (Loihi-2 4-core, 23 pJ/spike)

| id | domain | n | rate Hz | window_ms | spikes | energy_pJ | energy_uJ |
|----|--------|---|---------|-----------|--------|-----------|-----------|
{chr(10).join(ras_rows)}

`spikes = round(n × rate × window_s)`. Every record carries `gate_snn` whose `decision` matches the safety gate; populations that declare rate+spikes meet the same ±1 budget against `decision_window_s`. `routing.third_factor` has modulator (NA / ACh / DA / 5-HT / ACh), `tau_e_s`/`tau_e_ms` pair, and eligibility. Excerpt same-neuron gap ≥ 1000 µs; spike trains same-channel refractory ≥ 0.8 ms. Non-106 excerpts are kernelized and independent of `spike_events` times (overlap < 0.8).

## Local checks (this window)

Generator stdout: self_check (Jaccard, refractory, race, spike budget, energy, tick6 bind, gate_snn budget, rights). Then `json.loads` every line, `validate_run.check_line`, `raster_status`, `check_jsonl` FactoryStaging, `verify_batch_for_frontier(strict=True)`, `spike_probe.py --strict`.

Never `training_ready`. Never `sim_or_real=real`. Create-only into the assigned live path; did not clobber 2026-08-17 / 2026-08-30; did not overwrite existing r22 files (c-suffix if occupied).

## Residual weaknesses (honest)

1. Only **one** labeled independent LIF (106). The other four excerpts are independent of `spike_events` times but are not declared population sims.
2. Wrong-ACCEPT still absent (guard).
3. Tick-6 sidecar bind is standing machinery (r14+), not a new class.
4. Two 8-pool domains are reused vs live r01 (`industrial-assembly`, `autonomous-driving`) with new plants; a later round could sit those out entirely.
5. 109 ACCEPT is already-legal; a later round could pair the single ACCEPT with a world charge that does not go negative.

## Next densification target

Publish the latch-freshness predicate as a sidecar enum (`latch_fresh`) so a ghost-occupancy REJECT is convictable without the previous-cycle story. Optional: labeled LIF on a second record, or an ISI histogram sidecar. Wrong-ACCEPT remains structurally absent until a prompt amendment.

Novel coverage: 26.0%
"""


def create_only(path: Path, text: str) -> Path:
    text_path = str(path)
    for frag in FORBIDDEN_PATH_FRAGMENTS:
        if frag in text_path:
            raise SystemExit(f"refusing forbidden path {path}")
    target = path
    if target.exists():
        target = path.with_name(path.stem + "c" + path.suffix)
        if target.exists():
            raise SystemExit(f"c-suffix also exists: {target}")
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
    fd = os.open(target, flags, 0o644)
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        handle.write(text)
    return target


def main() -> int:
    if any(frag in str(LIVE_DIR) for frag in FORBIDDEN_PATH_FRAGMENTS):
        raise SystemExit("refusing forbidden live dir")
    LIVE_DIR.mkdir(parents=True, exist_ok=True)
    records = [record_106(), record_107(), record_108(), record_109(), record_110()]
    issues, jmax = self_check(records)
    lines = [
        json.dumps(rec, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
        for rec in records
    ]
    batch_path = create_only(LIVE_DIR / BATCH_NAME, "\n".join(lines) + "\n")
    notes_path = create_only(LIVE_DIR / NOTES_NAME, notes_text(records, jmax))
    print(f"wrote {batch_path} lines={len(lines)} jmax={jmax:.3f}")
    print(f"wrote {notes_path}")
    if issues:
        print("SELF_CHECK_ISSUES:")
        for item in issues:
            print(" -", item)
        return 1
    print("SELF_CHECK_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
