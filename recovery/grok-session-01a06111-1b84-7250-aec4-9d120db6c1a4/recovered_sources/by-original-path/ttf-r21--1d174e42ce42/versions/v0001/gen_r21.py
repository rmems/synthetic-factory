#!/usr/bin/env python3
"""Emit TTF r21 JSONL (ttf-r21-121..125) into /tmp/ttf-r21/. Never writes outputs/raw/."""

from __future__ import annotations

import json
import math
import random
import re
import sys
from collections import OrderedDict
from decimal import Decimal
from pathlib import Path

OUT_DIR = Path("/tmp/ttf-r21")
BATCH_PATH = OUT_DIR / "batch-r21.jsonl"
NOTES_PATH = OUT_DIR / "NOTES-r21.md"

PJ_PER_SPIKE = 23
RIGHTS = OrderedDict(
    [
        ("provider", "SpaceXAI/xAI"),
        ("model", "grok-4.6"),
        ("channel", "consumer"),
        ("subscription_plan", "SuperGrok Heavy"),
        ("generation_surface", "SuperGrok Heavy chat"),
        ("generated_at", "2026-09-02T22:15:00Z"),
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


def D(*parts: str) -> float:
    acc = Decimal("0")
    for part in parts:
        acc += Decimal(part)
    return float(acc)


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


def lif_121_excerpt():
    """Independent CUBA LIF (seed 21121). Plant remains designed."""

    n = 68
    dt_us = 100
    tau_m_ms = 20.0
    v_th = 1.0
    v_reset = 0.0
    refractory_us = 1000
    i_bias = 0.90
    i_stim_peak = 2.2
    stim = (25000, 28000)
    seed = 21121
    window_us = 34000
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
    early = [(t, nid) for t, nid in spikes if t < 25000]
    burst = [(t, nid) for t, nid in spikes if 25000 <= t < 28000]
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
            early_count = len([1 for t, _ in picked if t < 25000])
            burst_count = len([1 for t, _ in picked if t >= 25000])
            if pool[0][0] < 25000 and early_count >= want:
                break
            if pool[0][0] >= 25000 and burst_count >= want:
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
    take(burst, 9, label_times=(26800, 27100, 27600))
    picked.sort(key=lambda item: (item[0], item[1]))
    clamp = [(t, n) for t, n in picked if t < 25000][:7]
    seize = [(t, n) for t, n in picked if t >= 25000][:9]
    picked = sorted(clamp + seize, key=lambda item: (item[0], item[1]))
    if len(picked) < 8:
        raise RuntimeError(f"LIF excerpt too short: {len(picked)} (early={len(early)} burst={len(burst)})")
    channels = ["lif.clamp" if t < 25000 else "lif.seize" for t, _ in picked]
    lif = OrderedDict(
        [
            ("model", "leaky_integrate_and_fire"),
            ("n", 68),
            ("dt_us", 100),
            ("tau_m_ms", 20.0),
            ("v_rest", 0.0),
            ("v_reset", 0.0),
            ("v_th", 1.0),
            ("r_m", 1.0),
            ("refractory_us", 1000),
            ("i_bias", 0.90),
            ("i_stim_peak", 2.2),
            ("stim_t_us", [25000, 28000]),
            ("i_clamp_extra", 0.68),
            ("clamp_n", 14),
            ("seed", 21121),
            (
                "note",
                "Population sim scoped to this sidecar. Plant remains designed. "
                "Neurons 0-13 carry +0.68 clamp-pathway bias; stim 25-28 ms is the sheave-seize burst.",
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
    return excerpt_items(picked, channels), extra, spikes


def meta_block(
    domain,
    tags,
    distillation_value,
    batch_position,
    supervisor_error_type=None,
) -> OrderedDict:
    body = OrderedDict(
        [
            ("round", 21),
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


def pack(
    rec_id,
    title,
    state,
    spikes,
    proposed,
    safety,
    executed,
    future,
    ticks,
    notes,
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
            ("reward_components", reward_block(ticks, notes)),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    domain,
                    tags,
                    distillation,
                    batch_position,
                    supervisor_error_type=supervisor_error_type,
                ),
            ),
        ]
    )


def record_121():
    excerpt, extra, _lif_spikes = lif_121_excerpt()
    ticks = [
        tick(2856, 0.05, -0.02, -0.02, 0.01, 0.00),
        tick(7140, 0.08, -0.04, -0.03, 0.01, -0.01),
        tick(7380, 0.04, -0.03, -0.02, 0.00, 0.00),
        tick(8000, 0.10, -0.06, -0.03, 0.02, -0.01),
        tick(26800, 0.05, -0.36, -0.03, 0.01, -0.02),
        tick(960000000, 0.02, -0.05, -0.02, 0.00, 0.00),
    ]
    state = OrderedDict(
        [
            (
                "description",
                "Corrie-6 hangs on the Scree-Hitch FH-2 32-degree incline, 410 m up the 840 m "
                "track, when a haul-rope load cell reports 118 kN against a 110 kN tension cap. "
                "The bull-wheel encoder is still inside its 2.4 m/s cruise band. Load-first "
                "latches a process clamp under the cap; sheave-first would keep cruise haul. "
                "Stored heat in the downhill sheave bearing is not yet an observable of either "
                "race channel.",
            ),
            ("domain", "funicular"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Bring Corrie-6 to the upper landing, keep haul-rope tension <= 110 kN, and "
                "leave the downhill sheave unmarked.",
            ),
            ("t0_us", 1756794621000121),
            ("gate_latency_us", 860),
            ("race_window_us", 440),
            ("race_window_rel_ms", [7.0, 7.44]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "load.haul.n 118 kN pulse",
                                "enc.sheave.omega 2.4 m/s cruise band",
                            ],
                        ),
                        (
                            "semantics",
                            "Load-first latches haul clamp 118 -> 96 kN and 2.4 -> 1.1 m/s; "
                            "sheave-first keeps cruise haul on a 'still in band' model.",
                        ),
                        (
                            "window_derivation",
                            "440 us = one 2 kHz load-cell slot minus sheave-encoder group delay "
                            "on this haul PLC bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 240 us vs combined jitter ~76 us (load 34 + encoder 42): 3.2x "
                            "over a 2.0x trust floor. Reversing order by < 240 us inside the 440 us "
                            "window would have kept 118 kN cruise; predicted next-sample 114 kN > "
                            "110 kN cap.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "haul-rope load cell, 2 kHz, 34 us timestamp jitter",
                    "bull-wheel encoder, 1 kHz, 42 us jitter",
                    "sheave bearing AE puck, 200 Hz (context)",
                    "track-position encoder (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("haul_cap_kN", 110.0),
                        ("proposed_haul_kN", 118.0),
                        ("haul_rate_proposed_m_s", 2.4),
                        ("incline_deg", 32.0),
                        ("track_m", 840.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Corrie-6 indexed 410 m up FH-2; downhill sheave warm, haul 118 kN.",
                    "2. Cruise haul 118 kN at 2.4 m/s armed; encoder still in band.",
                    "3. Track-enc precursor at 1.420 ms; load-cell warm-start 118 kN.",
                    "4. Race window [7.000, 7.440] ms opens on the haul PLC bus.",
                    "5. Load cell 118 kN at 7.140 ms (winner).",
                    "6. Sheave encoder 2.4 m/s at 7.380 ms (loser by 240 us).",
                    "7. Gate at 8.000 ms (winner + 860 us): MODIFY clamp 96 kN, 1.1 m/s.",
                    "8. Clamp executes; next-sample tension 101 kN < 110 cap.",
                    "9. At 26.800 ms stored sheave-bearing heat seizes the downhill wheel; AE burst.",
                    "10. Car-evac 16 min + bearing swap; named un-netted loss, not folded into process heads.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_incline_haul"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("haul_kN", 118.0),
                        ("speed_m_s", 2.4),
                        ("brake_hold", False),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("haul_kN", 118.0),
                        ("haul_cap_kN", 110.0),
                        ("predicted_unclamped_next_kN", 114.0),
                        ("sheave_omega_m_s", 2.4),
                        ("race_margin_us", 240),
                        ("combined_jitter_us", 76),
                        ("t_charge_us", 26800),
                        ("delayed_surprise_s", 960.0),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 118 kN cruise at 2.4 m/s: the bull-wheel encoder is still in "
                "band, and the 410 m remaining climb is treated as open track.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "correct"),
            (
                "rationale",
                "Haul load 118 kN won by 240 us, so the rope is loading, not still cruising. "
                "Holding 118 kN predicts next-sample 114 kN > 110 kN cap. MODIFY: haul 118 -> "
                "96 kN and 2.4 -> 1.1 m/s. Observed after clamp 101 kN < 110. A full REJECT is "
                "not indicated: the incline accepts 96 kN.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "haul_kN",
                            OrderedDict(
                                [
                                    ("cap", 110.0),
                                    ("observed", 118.0),
                                    ("predicted_unclamped_next", 114.0),
                                    ("clamped", 96.0),
                                    ("observed_after_clamp", 101.0),
                                ]
                            ),
                        ),
                        (
                            "speed_m_s",
                            OrderedDict([("proposed", 2.4), ("clamped", 1.1)]),
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
            ("name", "clamped_incline_haul"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("haul_kN", 96.0),
                        ("speed_m_s", 1.1),
                        ("brake_hold", False),
                    ]
                ),
            ),
            (
                "gate_effect",
                "MODIFY: haul 118 -> 96 kN and 2.4 -> 1.1 m/s. Process-correct vs the 110 kN "
                "cap. Sheave-bearing seize still occurs at 26.800 ms.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Process-correct MODIFY held haul at 101 kN. At 26.800 ms stored bearing heat "
                "seized the downhill sheave. Clamp reduced dump energy; it did not dump the "
                "bearing. Partnered negative: process heads stay honest; world loss is named, "
                "not netted.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("rope", "clamp executed; peak 101 kN < 110"),
                        ("sheave", "downhill bearing seize at 26.800 ms"),
                        ("evac", "16 min car-evac + bearing swap"),
                        ("mission", "car stopped 390 m short of the landing"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Neither load cell nor sheave encoder predicted the bearing charge; bearing.ae.seize is a new channel at 26.800 ms, 18.800 ms after the gate, still inside the 34 ms raster.",
                    "Delayed (16 min): car-evac and downhill-sheave swap. Named un-netted loss, not folded into task_progress.",
                ],
            ),
            (
                "un_netted_loss",
                "16 min car-evac + downhill sheave bearing swap after a seize at 26.800 ms. "
                "Safety head -0.56 prices the seize; task_progress stays +0.34 because the haul "
                "clamp completed under the 110 kN cap. World loss is named here, not subtracted "
                "from process heads.",
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "load.haul.n (7.140 ms, 118 kN)"),
                        ("loser", "enc.sheave.omega (7.380 ms, 2.4 m/s cruise band)"),
                        ("margin_us", 240),
                        (
                            "counterfactual_if_reversed",
                            "Sheave-first by < 240 us inside the 440 us window would have kept "
                            "118 kN cruise; predicted next-sample 114 kN would have exceeded the "
                            "110 kN cap even without the bearing charge. The MODIFY is still the "
                            "correct process. The seize is a later world charge either way, cheaper "
                            "with the clamp than without.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 26800),
            (
                "reward_inflection_note",
                "Safety collapses at the 26.800 ms sheave-bearing seize (tick t_us=26800), inside "
                "the 34 ms raster. The correct MODIFY at 8.000 ms is in the same excerpt. Do not "
                "put inflection on the +16 min evac tick.",
            ),
            ("delayed_surprise_s", 960.0),
        ]
    )
    spikes = [
        spike("encoder.pos.ctx", 1.420, 0.44),
        spike("load.haul.n", 2.880, 0.61),
        spike("enc.sheave.omega", 3.640, 0.52),
        spike("ctrl.brake.ctx", 4.510, 0.47),
        spike("load.haul.n", 7.140, 1.31),
        spike("enc.sheave.omega", 7.380, 1.18),
        spike("ctrl.gate", 8.000, 0.99),
        spike("load.haul.n", 9.220, 0.84),
        spike("enc.sheave.omega", 11.040, 0.66),
        spike("ctrl.gate", 14.880, 0.88),
        spike("bearing.ae.seize", 26.800, 1.42),
        spike("bearing.ae.seize", 28.150, 0.91),
        spike("encoder.pos.ctx", 31.200, 0.41),
        spike("load.haul.n", 33.100, 0.58),
    ]
    ras = raster_core(
        34,
        68,
        26,
        60,
        routing(
            "thalamic-relay.haul-sheave",
            "spikenaut.policy.haul-clamp",
            [
                ("relay.haul.n", "policy.haul_clamp", 0.66),
                ("relay.sheave.omega", "policy.cruise_hold", 0.31),
                ("relay.bearing.seize", "policy.haul_clamp", -0.44),
            ],
            "noradrenaline",
            0.05,
            "surprise-gated pre_post_stdp; NA at load win (7.140 ms) opens a 50 ms eligibility "
            "trace that still covers the 26.800 ms seize",
        ),
        excerpt,
        extra=extra,
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.44),
            ("decision", "MODIFY"),
            (
                "populations",
                [
                    pop("haul_clamp", 48, 0.50, 280.0, 6),
                    pop("cruise_hold", 48, 0.50, 90.0, 2),
                    pop("haul_cap_veto", 24, 0.75),
                ],
            ),
        ]
    )
    return pack(
        "ttf-r21-121",
        "Scree-Hitch FH-2 / Corrie-6: haul load-cell beats sheave encoder by 240 us; "
        "correct MODIFY still eats an in-window sheave-bearing seize (partnered negative total -0.36)",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Partnered negative. Process-correct MODIFY; world still charges inside the "
        "34 ms raster. total -0.36 = 0.34 + -0.56 + -0.15 + 0.05 + -0.04. Named "
        "evac+bearing loss is not netted into task_progress.",
        ras,
        gate,
        "funicular",
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
        "minute-scale evac gap.",
        1,
    )


def record_122():
    ticks = [
        tick(2072, -0.03, -0.02, -0.02, -0.01, 0.01),
        tick(5180, -0.05, -0.03, -0.04, -0.02, 0.01),
        tick(5490, -0.03, -0.02, -0.03, -0.01, 0.01),
        tick(5890, -0.08, -0.08, -0.08, -0.04, 0.02),
        tick(6470, -0.03, -0.03, -0.03, -0.01, 0.01),
        tick(660000000, -0.02, -0.02, -0.02, -0.01, 0.00),
    ]
    excerpt = excerpt_items(
        [
            (620, 5),
            (2100, 21),
            (3900, 44),
            (5600, 9),
            (7400, 61),
            (9300, 14),
            (11200, 37),
            (13400, 70),
            (15700, 3),
            (18100, 28),
            (20600, 52),
            (22900, 17),
            (25100, 66),
            (27300, 8),
        ]
    )
    state = OrderedDict(
        [
            (
                "description",
                "Solder-Kite SK-3 already sits 6.6 C over the 245.0 C peak cap in Flux-Kettle "
                "Cell FK-9 zone 4 when the type-K thermocouple reports 251.6 C against a still-green "
                "belt encoder. Thermocouple-first should bind a heater clamp; a weak supervisor "
                "instead treats the couple as inverted and raises heater percent.",
            ),
            ("domain", "PCB-reflow"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Hold the 8-zone lead-free profile through liquidus, keep peak temperature <= "
                "245.0 C, and leave heater percent at the planned 68.",
            ),
            ("t0_us", 1756794622000122),
            ("gate_latency_us", 710),
            ("race_window_us", 580),
            ("race_window_rel_ms", [5.0, 5.58]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "tc.peak.zone4 251.6 C",
                                "enc.belt.x still-in-window",
                            ],
                        ),
                        (
                            "semantics",
                            "TC-first should latch heater clamp 68 -> 52 pct; belt-first is a false "
                            "'profile still legal' bind. The error here is not the race: it is the "
                            "sign of the heater edit after TC wins.",
                        ),
                        (
                            "window_derivation",
                            "580 us = one zone-4 TC ADC slot versus the belt-encoder publisher on "
                            "this 1 kHz oven bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 310 us vs combined jitter 82 us (TC 40 + encoder 42). Order is "
                            "correctly TC-first. The error is heater polarity, not the race and not "
                            "the actuator.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "type-K thermocouple zone 4, 2 kHz, 40 us jitter, axis tc.peak.zone4",
                    "reflow-belt encoder, 1 kHz, 42 us jitter",
                    "muffle pyrometer (context)",
                    "heater-SCR current (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("reflow_cap_C", 245.0),
                        ("observed_t_peak_C", 251.6),
                        ("clamp_channel", "tc.peak.zone4"),
                        ("heater_pct_planned", 68.0),
                        ("correct_heater_pct", 52.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. SK-3 indexed; panel in zone 4; peak 251.6 C vs 245.0 C cap.",
                    "2. Heater planned 68 pct; belt encoder still in window.",
                    "3. Belt precursor at 1.210 ms.",
                    "4. Race window [5.000, 5.580] ms.",
                    "5. TC peak 251.6 C at 5.180 ms (winner).",
                    "6. Belt encoder at 5.490 ms (loser by 310 us).",
                    "7. Gate at 5.890 ms: wrong MODIFY raises heater 68 -> 82 pct; T stays 251.6 C.",
                    "8. Next liquidus dwell overshoots to 258.4 C; interlock trips.",
                    "9. Oven abort 11 min; one panel scrap.",
                    "10. QA: correct gate was MODIFY heater 68 -> 52 pct on tc.peak.zone4, leave belt speed.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "hold_zone4_profile"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("heater_pct", 68.0),
                        ("belt_mm_s", 12.0),
                        ("zone4_C", 251.6),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("t_peak_C", 251.6),
                        ("reflow_cap_C", 245.0),
                        ("clamp_channel", "tc.peak.zone4"),
                        ("proposed_heater_pct", 68.0),
                        ("correct_heater_pct", 52.0),
                        ("polarity_true", "normal"),
                        ("t_gate_us", 5890),
                        ("race_margin_us", 310),
                        ("combined_jitter_us", 82),
                        ("delayed_surprise_s", 660.0),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes continuing the 68 pct heater through the next liquidus dwell "
                "at the observed 251.6 C. The TC read is on zone-4 peak, not an inverted couple.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "incorrect"),
            (
                "rationale",
                "T 251.6 C exceeds the 245.0 C peak cap (true). Cold-junction compensation on "
                "this type-K looks low, so the couple is treated as inverted: raising heater "
                "68 -> 82 pct should 'correct' the sign and pull the indicated peak down. Belt "
                "speed is left at 12 mm/s.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "zone4_C",
                            OrderedDict(
                                [
                                    ("cap", 245.0),
                                    ("observed", 251.6),
                                    ("executed", 251.6),
                                    ("clamp_channel", "tc.peak.zone4"),
                                ]
                            ),
                        ),
                        (
                            "heater_pct",
                            OrderedDict(
                                [
                                    ("planned", 68.0),
                                    ("correct_clamp", 52.0),
                                    ("clamped_wrong", 82.0),
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
            ("name", "heater_boost_wrong_polarity"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("heater_pct", 82.0),
                        ("belt_mm_s", 12.0),
                        ("zone4_C", 251.6),
                    ]
                ),
            ),
            (
                "gate_effect",
                "MODIFY (incorrect): heater 68 -> 82 pct; zone-4 left at 251.6 C then overshoots. "
                "Routing relay.tc.peak -> policy.heater_boost; no positive weight to "
                "policy.heater_clamp.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Wrong-MODIFY raised heater percent while zone-4 was already 251.6 C over the "
                "245.0 C cap. Peak 258.4 C; 11 min interlock abort; one panel scrap. Correct "
                "gate was MODIFY heater 68 -> 52 pct on tc.peak.zone4, belt speed unchanged.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("heater", "boosted to 82 pct; planned 68 pct abandoned"),
                        ("zone4", "still 251.6 C then 258.4 C, over 245.0 C cap"),
                        ("panel", "liquidus overshoot; panel scrap"),
                        ("oven", "11 min abort"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Raising heater percent did not invert the TC; indicated peak climbed with SCR duty.",
                    "Delayed (11 min): FK-9 abort while adjacent cells wait on the scrap panel; interlock log closed.",
                ],
            ),
            (
                "recovery",
                OrderedDict(
                    [
                        (
                            "correct_gate",
                            "MODIFY on tc.peak.zone4: heater 68 -> 52 pct at t_gate_us=5890; leave belt 12 mm/s.",
                        ),
                        ("correct_edit", "heater_pct 68 -> 52 (reduce)"),
                        ("wrong_edit", "heater_pct 68 -> 82 (raise / sign-flip)"),
                        (
                            "wrong_edit_applied",
                            OrderedDict([("heater_pct", 82.0), ("zone4_C", 251.6)]),
                        ),
                        (
                            "cost",
                            "6.8 C overshoot + 11 min abort + 1 panel scrap (task/efficiency); peak still over cap (safety near-miss).",
                        ),
                    ]
                ),
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "tc.peak.zone4 (5.180 ms, 251.6 C)"),
                        ("loser", "enc.belt.x (5.490 ms, still-in-window)"),
                        ("margin_us", 310),
                        (
                            "counterfactual_if_reversed",
                            "Belt-first by < 310 us would still be under the belt-window; a correct "
                            "gate binds TC to heater_clamp either way. The wrong MODIFY spent the TC "
                            "win on a sign-flipped heater boost.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 5890),
            (
                "reward_inflection_note",
                "Task, safety, and efficiency drop at the wrong boost (5.890 ms, tick 4). The 11 min abort is delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 660.0),
        ]
    )
    spikes = [
        spike("enc.belt.x", 1.210, 0.43),
        spike("tc.peak.zone4", 2.640, 0.62),
        spike("enc.belt.x", 3.880, 0.55),
        spike("pyro.muffle.ctx", 4.420, 0.41),
        spike("tc.peak.zone4", 5.180, 1.34),
        spike("enc.belt.x", 5.490, 1.12),
        spike("ctrl.gate", 5.890, 0.97),
        spike("tc.peak.zone4", 7.220, 0.81),
        spike("enc.belt.x", 8.880, 0.66),
        spike("ctrl.gate", 12.400, 0.84),
        spike("tc.peak.zone4", 16.800, 0.58),
        spike("enc.belt.x", 21.110, 0.39),
        spike("pyro.muffle.ctx", 25.400, 0.36),
    ]
    ras = raster_core(
        28,
        92,
        24,
        62,
        routing(
            "relay.tc.peak",
            "policy.heater_boost",
            [
                ("relay.tc.peak", "policy.heater_boost", 0.73),
                ("enc.belt.x", "policy.heater_boost", 0.18),
            ],
            "acetylcholine",
            0.08,
            "force_cap_stdp; ACh tags the (wrong) heater_boost bind at the TC win",
        ),
        excerpt,
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.58),
            ("decision", "MODIFY"),
            (
                "populations",
                [
                    pop("heater_boost", 48, 0.50, 250.0, 7),
                    pop("heater_clamp", 48, 0.80, 15.0, 0),
                    pop("pop_tc_peak", 32, 0.55, 180.0, 3),
                ],
            ),
        ]
    )
    return pack(
        "ttf-r21-122",
        "WRONG-MODIFY at Flux-Kettle FK-9 / Solder-Kite SK-3: T 251.6 C read correctly; "
        "heater raised 68 -> 82 pct (sign-flip) instead of clamped 68 -> 52 pct",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Wrong-modify / wrong-polarity. Sidecar arithmetic 251.6 > 245.0 is true; heater "
        "edit has the wrong sign. total -0.70 = -0.24 + -0.20 + -0.22 + -0.10 + 0.06.",
        ras,
        gate,
        "PCB-reflow",
        [
            "modify",
            "wrong-gate",
            "wrong-polarity",
            "sidecar-convictable",
            "designed",
        ],
        "Teaches a probe that a correct T>cap read can still be a wrong gate when "
        "routing.table[0].to is policy.heater_boost and executed heater_pct increases.",
        2,
        supervisor_error_type="wrong-modify",
    )


def record_123():
    ticks = [
        tick(1656, 0.01, 0.04, 0.02, 0.01, 0.01),
        tick(4140, 0.02, 0.08, 0.03, 0.02, 0.01),
        tick(4310, 0.01, 0.06, 0.02, 0.01, 0.01),
        tick(5460, 0.04, 0.12, 0.03, 0.03, 0.01),
        tick(5730, 0.02, 0.05, 0.02, 0.01, 0.01),
        tick(780000000, 0.01, 0.03, 0.01, 0.01, 0.00),
    ]
    excerpt = excerpt_items(
        [
            (800, 6),
            (2400, 19),
            (4100, 41),
            (5900, 3),
            (7800, 28),
            (9900, 11),
            (12200, 47),
            (14800, 8),
            (17600, 33),
            (20700, 21),
            (24100, 44),
            (27800, 2),
            (31800, 36),
            (36100, 14),
            (40800, 49),
            (44900, 9),
        ]
    )
    state = OrderedDict(
        [
            (
                "description",
                "Bog-Drum BD-7 at Mire-Cask MC-4 is souring: headspace H2S IR reads 84 ppm "
                "against a 50 ppm recirc-feed latch, and the digestate pH probe is 6.92 versus "
                "a 7.10 floor. H2S-first latches hold; pH-first would treat a 6.92 reading as "
                "still-mesophilic and keep the 18 m3/h feed.",
            ),
            ("domain", "anaerobic-digester"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Do not recirc-boost or feed unless H2S < 50 ppm and pH >= 7.10; keep the "
                "biogas flare lit.",
            ),
            ("t0_us", 1756794623000123),
            ("gate_latency_us", 1320),
            ("race_window_us", 270),
            ("race_window_rel_ms", [4.1, 4.37]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "ir.h2s.head 84 ppm",
                                "ph.digest.probe 6.92",
                            ],
                        ),
                        (
                            "semantics",
                            "H2S-first latches REJECT hold feed 0.0 m3/h and recirc-boost off; "
                            "pH-first would keep 18 m3/h on a still-mesophilic model.",
                        ),
                        (
                            "window_derivation",
                            "270 us = one NDIR H2S burst slot versus the pH-probe publisher on "
                            "this 2800 m3 CSTR cycle.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 170 us vs combined jitter ~52 us (IR 24 + pH 28): 3.3x over a "
                            "2.0x trust floor. Reversing order by < 170 us would have kept 18 m3/h "
                            "feed into a sour headspace.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "NDIR H2S headspace, 20 Hz burst, 24 us jitter",
                    "digestate pH probe, 28 us jitter",
                    "recirc-flow meter (context)",
                    "flare-stack thermocouple (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("h2s_cap_ppm", 50.0),
                        ("observed_h2s_ppm", 84.0),
                        ("ph_floor", 7.10),
                        ("observed_ph", 6.92),
                        ("proposed_feed_m3_h", 18.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. BD-7 at MC-4; 2800 m3 mesophilic CSTR; flare lit.",
                    "2. Headspace H2S 84 ppm; pH 6.92; proposed feed 18 m3/h.",
                    "3. Recirc precursor at 1.088 ms.",
                    "4. Race window [4.100, 4.370] ms.",
                    "5. H2S IR 84 ppm at 4.140 ms (winner).",
                    "6. pH probe 6.92 at 4.310 ms (loser by 170 us).",
                    "7. Gate at 5.460 ms: REJECT hold feed 0.0 m3/h; recirc-boost off; flare stays.",
                    "8. Caps held; drum not fed this cycle.",
                    "9. Sour-gas purge queued.",
                    "10. Delayed (13 min): 13 min sour-gas purge + lime recirc before the next feed window.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "continue_mesophilic_feed"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("feed_m3_h", 18.0),
                        ("recirc_boost", True),
                        ("flare", True),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("h2s_ppm", 84.0),
                        ("h2s_cap_ppm", 50.0),
                        ("ph", 6.92),
                        ("ph_floor", 7.10),
                        ("race_margin_us", 170),
                        ("combined_jitter_us", 52),
                        ("delayed_surprise_s", 780.0),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 18 m3/h feed with recirc-boost because pH 6.92 is treated as "
                "still mesophilic and H2S is not yet bound as a feed latch.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "REJECT"),
            ("correctness", "correct"),
            (
                "rationale",
                "H2S 84 ppm won by 170 us and is over the 50 ppm recirc-feed latch; pH 6.92 is "
                "under the 7.10 floor. REJECT: hold feed 0.0 m3/h, recirc-boost off, keep the "
                "flare. A MODIFY that only slows feed still shoves sour headspace.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "h2s_ppm",
                            OrderedDict([("cap", 50.0), ("observed", 84.0)]),
                        ),
                        (
                            "ph",
                            OrderedDict([("floor", 7.10), ("observed", 6.92)]),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 170),
                                    ("combined_jitter_us", 52),
                                    ("ratio", 3.27),
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
            ("name", "hold_feed_keep_flare"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("feed_m3_h", 0.0),
                        ("recirc_boost", False),
                        ("flare", True),
                    ]
                ),
            ),
            (
                "gate_effect",
                "REJECT: feed 18 -> 0.0 m3/h, recirc-boost off, flare held. Caps held this cycle.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "REJECT held feed and recirc-boost. Headspace H2S stayed over the 50 ppm latch "
                "this cycle; flare stayed lit. Task incomplete (drum not fed); caps held.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("feed", "held 0.0 m3/h"),
                        ("recirc", "boost off"),
                        ("flare", "lit"),
                        ("drum", "not fed this cycle; sour-gas purge queued"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "pH 6.92 was not a probe fault: volatile-fatty-acid rise matched the H2S IR within 2 min.",
                    "Delayed (13 min): sour-gas purge plus lime recirc before the next feed window.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "ir.h2s.head (4.140 ms, 84 ppm)"),
                        ("loser", "ph.digest.probe (4.310 ms, 6.92)"),
                        ("margin_us", 170),
                        (
                            "counterfactual_if_reversed",
                            "pH-first by < 170 us inside the 270 us window would have kept 18 m3/h "
                            "feed into a sour headspace over the 50 ppm H2S latch.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 5460),
            (
                "reward_inflection_note",
                "Safety steps up at the REJECT gate (5.460 ms, tick 4) as the feed latch holds.",
            ),
            ("delayed_surprise_s", 780.0),
        ]
    )
    spikes = [
        spike("ph.digest.probe", 1.088, 0.44),
        spike("ir.h2s.head", 2.410, 0.60),
        spike("ph.digest.probe", 3.220, 0.53),
        spike("recirc.flow.ctx", 3.880, 0.46),
        spike("ir.h2s.head", 4.140, 1.27),
        spike("ph.digest.probe", 4.310, 1.09),
        spike("ctrl.gate", 5.460, 0.98),
        spike("ir.h2s.head", 6.880, 0.80),
        spike("ph.digest.probe", 8.440, 0.64),
        spike("flare.stack.ctx", 11.020, 0.48),
        spike("ctrl.gate", 14.880, 0.86),
        spike("recirc.flow.ctx", 18.210, 0.40),
        spike("ir.h2s.head", 22.400, 0.55),
        spike("ph.digest.probe", 31.050, 0.37),
    ]
    ras = raster_core(
        46,
        52,
        38,
        91,
        routing(
            "thalamic-relay.h2s-ph",
            "spikenaut.policy.feed-hold",
            [
                ("relay.h2s.head", "policy.feed_hold", 0.69),
                ("relay.ph.probe", "policy.feed_go", 0.28),
                ("relay.flare.stack", "policy.feed_hold", 0.22),
            ],
            "serotonin",
            0.10,
            "pre_post_stdp; 5-HT at H2S win tags feed_hold, reward at cap-held",
        ),
        excerpt,
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.27),
            ("decision", "REJECT"),
            (
                "populations",
                [
                    pop("hold_reject", 64, 0.50, 300.0, 5),
                    pop("feed_go", 64, 0.50, 60.0, 1),
                    pop("h2s_latch_veto", 32, 0.80),
                ],
            ),
        ]
    )
    return pack(
        "ttf-r21-123",
        "Mire-Cask MC-4 / Bog-Drum BD-7: H2S IR beats pH probe by 170 us; REJECT hold feed 0.0 m3/h",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Clean REJECT. Task incomplete (drum not fed); cap held. "
        "total 0.76 = 0.11 + 0.38 + 0.13 + 0.09 + 0.05.",
        ras,
        gate,
        "anaerobic-digester",
        [
            "reject",
            "designed",
            "h2s-latch",
            "sour-headspace",
            "feed-hold",
        ],
        "Teaches that a still-mesophilic pH reading is not a feed clearance when headspace H2S is over the recirc latch.",
        3,
    )


def record_124():
    ticks = [
        tick(3220, 0.05, 0.03, 0.02, 0.01, 0.01),
        tick(8050, 0.08, 0.05, 0.03, 0.02, 0.02),
        tick(8280, 0.05, 0.04, 0.02, 0.02, 0.01),
        tick(8530, 0.12, 0.10, 0.05, 0.03, 0.01),
        tick(8920, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(540000000, 0.04, 0.03, 0.02, 0.01, 0.01),
    ]
    excerpt = excerpt_items(
        [
            (900, 11),
            (3400, 47),
            (6100, 3),
            (8800, 90),
            (11600, 28),
            (14700, 71),
            (18100, 8),
            (21800, 104),
            (25700, 33),
            (29800, 66),
            (33600, 15),
            (37200, 88),
            (39100, 5),
            (39900, 52),
        ]
    )
    params = OrderedDict(
        [
            ("vane_deg", 18.0),
            ("q_m3_s", 92.0),
            ("sluice_n", 14),
            ("sigma", 0.34),
        ]
    )
    state = OrderedDict(
        [
            (
                "description",
                "Ebb-Latch EL-4 on Slack-Firth SF-6 holds fourteen sluices on the ebb generation "
                "cycle when a turbine-throat flow meter reports 92 m3/s 230 us before the staff "
                "gauge sees a 3.1 m ebb crest. The proposed vane already sits at 18 deg, keeping "
                "Q 92 < 105 m3/s and cavitation sigma 0.34 over the 0.28 floor. Flow-first "
                "confirms that vane; it does not require a further clamp.",
            ),
            ("domain", "tidal-barrage"),
            ("sim_or_real", "simulated"),
            (
                "goal",
                "Hold ebb generation on fourteen sluices, keep turbine Q <= 105 m3/s, and keep "
                "cavitation sigma >= 0.28.",
            ),
            ("t0_us", 1756794624000124),
            ("gate_latency_us", 480),
            ("race_window_us", 390),
            ("race_window_rel_ms", [8.0, 8.39]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "load.turbine.q 92 m3/s",
                                "staff.ebb.crest 3.1 m",
                            ],
                        ),
                        (
                            "semantics",
                            "Flow-first confirms the already-legal 18 deg vane that keeps Q 92 < "
                            "105 and sigma 0.34 >= 0.28; crest-first would have treated the pulse "
                            "as a staff-only tide bump and looked for an extra clamp the vane does "
                            "not need.",
                        ),
                        (
                            "window_derivation",
                            "390 us = one throat-meter slot versus the staff-gauge front on this "
                            "14-sluice ebb cycle.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 230 us vs combined jitter 70 us (flow 32 + staff 38): 3.3x over "
                            "a 2.0x trust floor. Reversing order by < 230 us would not make the "
                            "proposed vane illegal; it would only have delayed confirmation.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "turbine-throat flow meter, 32 us jitter",
                    "ebb staff gauge, 38 us jitter",
                    "vane encoder (context)",
                    "nacelle IMU (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("q_cap_m3_s", 105.0),
                        ("observed_q_m3_s", 92.0),
                        ("sigma_floor", 0.28),
                        ("observed_sigma", 0.34),
                        ("vane_deg", 18.0),
                        ("sluice_n", 14),
                    ]
                ),
            ),
            (
                "simulation",
                OrderedDict(
                    [
                        (
                            "solver",
                            "shallow-water Saint-Venant + turbine BEM, seed 21; 14 sluices, 8 phase bins, 5 radial stations; NOT linear-potential WEC, NOT Morison-only, NOT three-body latching",
                        ),
                        (
                            "fidelity_limits",
                            "Rigid sluice leaves; no cavitation bubble collapse; PTO is a two-state vane. Raster is kernelized events, not an independent LIF.",
                        ),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. EL-4 on SF-6; fourteen sluices on ebb generation.",
                    "2. Proposed vane 18 deg; Q 92 m3/s; sigma 0.34.",
                    "3. IMU precursor at 1.540 ms.",
                    "4. Race window [8.000, 8.390] ms.",
                    "5. Throat flow 92 m3/s at 8.050 ms (winner).",
                    "6. Staff crest 3.1 m at 8.280 ms (loser by 230 us).",
                    "7. Gate at 8.530 ms: ACCEPT; executed identical to proposed.",
                    "8. Q held 92 < 105; sigma 0.34 >= 0.28.",
                    "9. Ebb generation continues.",
                    "10. Delayed (9 min): tide-table policy requires phase-bin tags on staff fusion.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "ebb_vane_hold"),
            ("parameters", params),
            (
                "evidence",
                OrderedDict(
                    [
                        ("q_m3_s", 92.0),
                        ("q_cap_m3_s", 105.0),
                        ("sigma", 0.34),
                        ("sigma_floor", 0.28),
                        ("vane_deg", 18.0),
                        ("race_margin_us", 230),
                        ("combined_jitter_us", 70),
                        ("delayed_surprise_s", 540.0),
                    ]
                ),
            ),
            (
                "basis",
                "Planner already includes an 18 deg vane that keeps Q 92 < 105 m3/s and sigma "
                "0.34 >= 0.28. Unclamped 118 m3/s is not the proposal.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Throat flow 92 m3/s won by 230 us and is 13 m3/s under the 105 m3/s cap; "
                "sigma 0.34 is over the 0.28 floor. ACCEPT the 18 deg vane. A further clamp "
                "would dump generation without a constraint violation.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "q_m3_s",
                            OrderedDict([("cap", 105.0), ("observed", 92.0)]),
                        ),
                        (
                            "sigma",
                            OrderedDict([("floor", 0.28), ("observed", 0.34)]),
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
            ("name", "ebb_vane_hold"),
            ("parameters", OrderedDict(params.items())),
            (
                "gate_effect",
                "ACCEPT: executed identical to proposed_action; 18 deg vane and 92 m3/s held.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "EL-4 completed the ebb hold with Q 92 m3/s and sigma 0.34; no extra clamp. "
                "Flow-authoritative under ebb-generation mode confirmed.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("sluices", "fourteen held on ebb"),
                        ("turbine", "Q 92 m3/s; vane 18 deg"),
                        ("policy", "flow-authoritative under ebb-generation"),
                        ("near_miss_log", "none; sigma 0.34"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "The 3.1 m staff crest was not a calibration fault: a seiche can raise the staff while throat Q stays under cap.",
                    "Delayed (9 min): sister sluice EL-5 logged the same flow-vs-staff disagreement; barrage policy tagged phase bins on staff fusion.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "load.turbine.q (8.050 ms, 92 m3/s)"),
                        ("loser", "staff.ebb.crest (8.280 ms, 3.1 m)"),
                        ("margin_us", 230),
                        (
                            "counterfactual_if_reversed",
                            "Staff-first by < 230 us inside the 390 us window would not have made "
                            "the 18 deg vane illegal; it would only have delayed confirmation of an "
                            "already-legal hold.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 8530),
            (
                "reward_inflection_note",
                "Safety and efficiency both step up at the ACCEPT gate (8.530 ms, tick 4) as the vane hold locks in.",
            ),
            ("delayed_surprise_s", 540.0),
        ]
    )
    spikes = [
        spike("imu.nacelle.ctx", 1.540, 0.44),
        spike("load.turbine.q", 3.220, 0.60),
        spike("staff.ebb.crest", 4.880, 0.53),
        spike("enc.vane.ctx", 6.110, 0.46),
        spike("load.turbine.q", 8.050, 1.27),
        spike("staff.ebb.crest", 8.280, 1.09),
        spike("ctrl.gate", 8.530, 0.98),
        spike("load.turbine.q", 10.220, 0.80),
        spike("staff.ebb.crest", 12.440, 0.64),
        spike("ctrl.gate", 16.880, 0.86),
        spike("enc.vane.ctx", 22.010, 0.48),
        spike("imu.nacelle.ctx", 28.400, 0.40),
        spike("load.turbine.q", 35.200, 0.55),
        spike("staff.ebb.crest", 38.050, 0.37),
    ]
    ras = raster_core(
        40,
        112,
        19,
        85,
        routing(
            "thalamic-relay.turbine-staff",
            "spikenaut.policy.vane-hold",
            [
                ("relay.turbine.q", "policy.vane_hold", 0.63),
                ("relay.staff.crest", "policy.extra_clamp", 0.29),
                ("relay.vane.enc", "policy.vane_hold", 0.21),
            ],
            "dopamine",
            0.14,
            "pre_post_stdp; DA at flow win tags vane_hold, reward at ebb-clear",
        ),
        excerpt,
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.39),
            ("decision", "ACCEPT"),
            (
                "populations",
                [
                    pop("vane_accept", 80, 0.50, 200.0, 6),
                    pop("extra_clamp", 80, 0.50, 40.0, 1),
                    pop("q_cap_veto", 24, 0.80),
                ],
            ),
        ]
    )
    return pack(
        "ttf-r21-124",
        "Slack-Firth SF-6 / Ebb-Latch EL-4: throat flow beats staff crest by 230 us; ACCEPT 18 deg vane",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Clean ACCEPT. Tick columns sum to the five heads; total 1.04 = 0.40+0.29+0.17+0.11+0.07.",
        ras,
        gate,
        "tidal-barrage",
        [
            "accept",
            "simulated",
            "ebb-generation",
            "turbine-vs-staff",
            "vane-hold",
        ],
        "Teaches that a staff-gauge crest can lose to a throat flow meter when the proposed vane is already under Q and sigma floors.",
        4,
    )


def record_125():
    ticks = [
        tick(2488, 0.05, 0.03, 0.02, 0.01, 0.01),
        tick(6220, 0.09, 0.06, 0.03, 0.02, 0.02),
        tick(6410, 0.05, 0.04, 0.02, 0.01, 0.01),
        tick(6530, 0.13, 0.10, 0.05, 0.03, 0.02),
        tick(6860, 0.07, 0.05, 0.02, 0.02, 0.01),
        tick(420000000, 0.04, 0.03, 0.02, 0.01, 0.01),
    ]
    excerpt = excerpt_items(
        [
            (700, 4),
            (2400, 18),
            (4100, 51),
            (5900, 9),
            (7700, 33),
            (9600, 12),
            (11600, 60),
            (13700, 2),
            (15900, 41),
            (18200, 21),
            (20400, 55),
            (20900, 7),
        ]
    )
    params = OrderedDict(
        [
            ("belt_m_s", 1.8),
            ("dust_mg_m3", 18.4),
            ("boot_C", 41.0),
        ]
    )
    state = OrderedDict(
        [
            (
                "description",
                "Auger-9 on the Chaff-Rise CR-HIL stand sees 18.4 mg/m3 laser dust against a "
                "20.0 mg/m3 belt-speed latch while the boot pyrometer is 41 C, still under the "
                "65 C warn. Laser-first latches the 1.8 m/s hold; pyro-first would treat a cool "
                "boot as spare capacity and raise the belt to 2.4 m/s.",
            ),
            ("domain", "grain-elevator"),
            ("sim_or_real", "hil"),
            (
                "goal",
                "Hold bucket-leg Auger-9 at 1.8 m/s, keep dust <= 20.0 mg/m3, and keep boot "
                "temperature <= 65 C.",
            ),
            ("t0_us", 1756794625000125),
            ("gate_latency_us", 310),
            ("race_window_us", 330),
            ("race_window_rel_ms", [6.15, 6.48]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "laser.dust.mg 18.4 mg/m3",
                                "pyro.boot.T 41 C",
                            ],
                        ),
                        (
                            "semantics",
                            "Laser-first latches 1.8 m/s hold; pyro-first would raise belt to "
                            "2.4 m/s on a cool-boot-as-capacity model.",
                        ),
                        (
                            "window_derivation",
                            "330 us = one laser-dust slot versus the boot-pyrometer publisher on "
                            "this HIL stand bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 190 us vs combined jitter 60 us (laser 26 + pyro 34): 3.2x over "
                            "a 2.0x trust floor. Stand injects pyro 70-100 us before the laser sees "
                            "the boot neck (thermal lag of the mock boot, not a sensor fault); the "
                            "pyro packet is still the loser in this 330 us window.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "laser dust photometer, 26 us jitter (real on stand)",
                    "boot pyrometer, 34 us jitter (mock muffle)",
                    "belt encoder (context, synthetic plant)",
                    "boot-level paddle (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("dust_cap_mg_m3", 20.0),
                        ("observed_dust_mg_m3", 18.4),
                        ("boot_cap_C", 65.0),
                        ("observed_boot_C", 41.0),
                        ("proposed_belt_m_s", 1.8),
                        ("pyro_inject_lead_us", [70, 100]),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Auger-9 on CR-HIL; real laser dust + furnace-mock boot; synthetic belt plant.",
                    "2. Dust 18.4 mg/m3; boot 41 C; proposed 1.8 m/s hold.",
                    "3. Belt-enc precursor at 1.088 ms.",
                    "4. Race window [6.150, 6.480] ms.",
                    "5. Laser dust 18.4 mg/m3 at 6.220 ms (winner).",
                    "6. Boot pyro 41 C at 6.410 ms (loser by 190 us).",
                    "7. Gate at 6.530 ms: ACCEPT 1.8 m/s hold.",
                    "8. Dust stays 18.4 < 20.0; boot 41 < 65.",
                    "9. Leg cleared this cycle.",
                    "10. Delayed (7 min): sister-leg policy tags laser-dust as belt-authoritative vs cool-boot.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "belt_hold_1p8"),
            ("parameters", params),
            (
                "evidence",
                OrderedDict(
                    [
                        ("dust_mg_m3", 18.4),
                        ("dust_cap_mg_m3", 20.0),
                        ("boot_C", 41.0),
                        ("boot_cap_C", 65.0),
                        ("race_margin_us", 190),
                        ("combined_jitter_us", 60),
                        ("delayed_surprise_s", 420.0),
                    ]
                ),
            ),
            (
                "basis",
                "Laser dust 18.4 mg/m3 is under the 20.0 mg/m3 latch and boot 41 C is under "
                "65 C; 1.8 m/s hold is already legal. Unclamped 2.4 m/s is not the proposal.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Laser dust 18.4 mg/m3 won by 190 us and is 1.6 mg/m3 under the 20.0 mg/m3 "
                "latch; boot 41 C is under 65 C. ACCEPT the 1.8 m/s hold. A 2.4 m/s pyro-holdover "
                "would violate the dust latch if the cool boot were believed.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "dust_mg_m3",
                            OrderedDict([("cap", 20.0), ("observed", 18.4)]),
                        ),
                        (
                            "boot_C",
                            OrderedDict([("cap", 65.0), ("observed", 41.0)]),
                        ),
                        (
                            "speed_m_s",
                            OrderedDict([("cap", 2.0), ("commanded", 1.8)]),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 190),
                                    ("combined_jitter_us", 60),
                                    ("ratio", 3.17),
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
            ("name", "belt_hold_1p8"),
            ("parameters", OrderedDict(params.items())),
            (
                "gate_effect",
                "ACCEPT: executed identical to proposed_action; 1.8 m/s belt hold.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Auger-9 completed the HIL cycle with dust 18.4 mg/m3 and boot 41 C; no speed "
                "raise. Laser-authoritative under dust-present mode confirmed.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("leg", "cycle cleared; boot not over-temp"),
                        ("belt", "1.8 m/s held"),
                        ("policy", "laser-authoritative under dust-present mode"),
                        ("near_miss_log", "none; dust 18.4 < 20.0"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "The 41 C boot was not a calibration fault: the mock muffle lags the laser neck by 70-100 us on this stand.",
                    "Delayed (7 min): sister-leg Auger-10 logged the same laser-vs-pyro disagreement; house policy tagged laser-dust as belt-authoritative.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "laser.dust.mg (6.220 ms, 18.4 mg/m3)"),
                        ("loser", "pyro.boot.T (6.410 ms, 41 C)"),
                        ("margin_us", 190),
                        (
                            "counterfactual_if_reversed",
                            "Pyro-first by < 190 us inside the 330 us window would have raised "
                            "belt to 2.4 m/s on a cool-boot-as-capacity model and closed on the "
                            "20.0 mg/m3 dust latch.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 6530),
            (
                "reward_inflection_note",
                "Safety and efficiency both step up at the ACCEPT gate (6.530 ms, tick 4) as the 1.8 m/s hold locks in over a 2.4 m/s raise.",
            ),
            ("delayed_surprise_s", 420.0),
        ]
    )
    spikes = [
        spike("belt.enc.ctx", 1.088, 0.44),
        spike("laser.dust.mg", 2.640, 0.60),
        spike("pyro.boot.T", 3.880, 0.53),
        spike("boot.level.ctx", 4.510, 0.46),
        spike("laser.dust.mg", 6.220, 1.27),
        spike("pyro.boot.T", 6.410, 1.09),
        spike("ctrl.gate", 6.530, 0.98),
        spike("laser.dust.mg", 8.110, 0.80),
        spike("pyro.boot.T", 9.880, 0.64),
        spike("ctrl.gate", 13.200, 0.86),
        spike("boot.level.ctx", 16.440, 0.48),
        spike("belt.enc.ctx", 19.050, 0.40),
    ]
    ras = raster_core(
        21,
        76,
        33,
        53,
        routing(
            "thalamic-relay.dust-pyro",
            "spikenaut.policy.belt-hold",
            [
                ("relay.laser.dust", "policy.belt_hold", 0.64),
                ("relay.pyro.boot", "policy.belt_raise", 0.27),
                ("relay.boot.level", "policy.belt_raise", -0.22),
            ],
            "histamine",
            0.06,
            "pre_post_stdp; histamine at laser win tags belt_hold, reward at cycle-clear",
        ),
        excerpt,
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.33),
            ("decision", "ACCEPT"),
            (
                "populations",
                [
                    pop("belt_accept", 32, 0.50, 240.0, 3),
                    pop("boot_hold", 32, 0.50, 80.0, 1),
                    pop("dust_latch_veto", 16, 0.80),
                ],
            ),
        ]
    )
    return pack(
        "ttf-r21-125",
        "Chaff-Rise CR-HIL / Auger-9: laser dust beats boot pyro by 190 us; ACCEPT 1.8 m/s belt hold",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Clean ACCEPT. Tick columns sum to the five heads; total 1.08 = 0.43+0.31+0.16+0.10+0.08.",
        ras,
        gate,
        "grain-elevator",
        [
            "accept",
            "hil",
            "laser-dust",
            "boot-pyro",
            "belt-hold",
        ],
        "Teaches that a cool boot pyrometer is not spare belt capacity when laser dust is the latch; reversing 190 us would have selected an illegal 2.4 m/s raise.",
        5,
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
    if len(wrong) != 1 or wrong[0]["id"] != "ttf-r21-122":
        issues.append(f"wrong-gate set {[w['id'] for w in wrong]}")
    if any(r["state"]["sim_or_real"] == "real" for r in records):
        issues.append("sim_or_real=real")
    expected_ids = [f"ttf-r21-{n}" for n in range(121, 126)]
    if [r["id"] for r in records] != expected_ids:
        issues.append(f"ids {[r['id'] for r in records]}")
    domains = [r["state"]["domain"] for r in records]
    if domains != [
        "funicular",
        "PCB-reflow",
        "anaerobic-digester",
        "tidal-barrage",
        "grain-elevator",
    ]:
        issues.append(f"domains {domains}")
    if len(set(domains)) != 5:
        issues.append("domain collision")
    for rec in records:
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
        if rec["id"] == "ttf-r21-121":
            if rec["raster"].get("excerpt_source") != "independent_lif":
                issues.append("121 missing independent_lif")
            if rec["future_outcome"]["reward_inflection_t_us"] > rec["raster"]["window_ms"] * 1000:
                issues.append("121 inflection outside window")
            if rec["state"]["sim_or_real"] != "designed":
                issues.append("121 plant not designed")
        elif overlap >= 0.8:
            issues.append(f"{rec['id']} excerpt overlap {overlap:.2f}")
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
        heads = ["task_progress", "safety", "efficiency", "coherence", "exploration"]
        total = sum(rec["reward_components"][h] for h in heads)
        if abs(total - rec["reward_components"]["total"]) > 1e-6:
            issues.append(f"{rec['id']} total mismatch {total}")
        for h in heads:
            s = sum(t[h] for t in rec["reward_components"]["ticks"])
            if abs(s - rec["reward_components"][h]) > 1e-6:
                issues.append(f"{rec['id']} {h} tick sum {s} vs {rec['reward_components'][h]}")
        blob = json.dumps(rec)
        if "training_ready" in blob:
            issues.append(f"{rec['id']} training_ready present")
        if rec["meta"]["round"] != 21:
            issues.append(f"{rec['id']} meta.round")
        if rec["meta"]["rights"]["intended_use"] != "research_only":
            issues.append(f"{rec['id']} rights")
        if rec["meta"]["rights"]["linear_issue"] != "RM-793":
            issues.append(f"{rec['id']} RM-793")
        exec_p = rec["executed_action"]["parameters"]
        prop_p = rec["proposed_action"]["parameters"]
        if rec["safety_decision"]["decision"] == "ACCEPT" and exec_p != prop_p:
            issues.append(f"{rec['id']} ACCEPT params differ")
        ds = rec["future_outcome"].get("delayed_surprise_s")
        ev_ds = rec["proposed_action"]["evidence"].get("delayed_surprise_s")
        if ds is None or ev_ds is None or abs(ds - ev_ds) > 1e-9:
            issues.append(f"{rec['id']} delayed_surprise_s mismatch")
        if tick_times[5] != int(round(ds * 1e6)):
            issues.append(f"{rec['id']} tick6 bind {tick_times[5]} vs {round(ds * 1e6)}")
        t_win = round(
            min(
                e["t_rel_ms"]
                for e in rec["spike_events"]
                if rec["state"]["race_window_rel_ms"][0]
                <= e["t_rel_ms"]
                <= rec["state"]["race_window_rel_ms"][1]
                and e["channel"] != "ctrl.gate"
            )
            * 1000
        )
        t_gate = t_win + rec["state"]["gate_latency_us"]
        T_race = rec["state"]["race_window_us"]
        T_win = int(round(float(rec["raster"]["window_ms"]) * 1000))
        if tick_times[0] != round(0.40 * t_win):
            issues.append(f"{rec['id']} tick1 {tick_times[0]} vs {round(0.40 * t_win)}")
        if tick_times[3] != t_gate:
            issues.append(f"{rec['id']} tick4 {tick_times[3]} vs {t_gate}")
        if rec["id"] == "ttf-r21-121":
            if tick_times[4] != 26800:
                issues.append("121 tick5")
        elif tick_times[4] != t_gate + T_race:
            issues.append(f"{rec['id']} tick5 {tick_times[4]} vs {t_gate + T_race}")
        if not (tick_times[5] > T_win):
            issues.append(f"{rec['id']} tick6 not > T_win")
        dw = rec["gate_snn"]["decision_window_ms"]
        if abs(dw - rec["state"]["race_window_us"] / 1000.0) > 1e-9:
            issues.append(f"{rec['id']} decision_window_ms")
        for p in rec["gate_snn"]["populations"]:
            if "mean_rate_hz" in p:
                expected_sp = round(p["neurons"] * p["mean_rate_hz"] * (dw / 1000.0))
                if abs(p["spikes"] - expected_sp) > 1:
                    issues.append(f"{rec['id']} pop {p['name']} {p['spikes']} vs {expected_sp}")
        tau_s = rec["raster"]["routing"]["third_factor"]["tau_e_s"]
        tau_ms = rec["raster"]["routing"]["third_factor"]["tau_e_ms"]
        if abs(tau_ms / 1000.0 - tau_s) > 1e-9:
            issues.append(f"{rec['id']} tau_e mismatch")
        if rec["raster"]["energy_pJ"] != rec["raster"]["spikes"] * 23:
            issues.append(f"{rec['id']} energy_pJ")
        if rec["id"] == "ttf-r21-122":
            ev = rec["proposed_action"]["evidence"]
            ex = rec["executed_action"]["parameters"]
            if not (ev["t_peak_C"] > ev["reflow_cap_C"]):
                issues.append("122 T not over cap")
            if not (ex["heater_pct"] > ev["proposed_heater_pct"]):
                issues.append("122 heater not raised")
            table = rec["raster"]["routing"]["table"]
            if not any(
                e["from"] == "relay.tc.peak" and e["to"] == "policy.heater_boost" and e["weight"] > 0
                for e in table
            ):
                issues.append("122 routing")
            if any(
                e["to"] == "policy.heater_clamp" and e["weight"] > 0 for e in table
            ):
                issues.append("122 positive heater_clamp")
            pops = {p["name"]: p for p in rec["gate_snn"]["populations"]}
            if pops["heater_boost"]["spikes"] <= 0 or pops["heater_clamp"]["spikes"] != 0:
                issues.append("122 gate_snn polarity")
            if rec["safety_decision"]["decision"] != "MODIFY":
                issues.append("122 decision")
            recov = rec["future_outcome"].get("recovery") or {}
            if "52" not in str(recov.get("correct_gate", "")):
                issues.append("122 recovery")
    return issues, jmax


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    records = [record_121(), record_122(), record_123(), record_124(), record_125()]
    issues, jmax = self_check(records)
    lines = [
        json.dumps(rec, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
        for rec in records
    ]
    BATCH_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {BATCH_PATH} lines={len(lines)} jmax={jmax:.3f}")
    print(f"bytes={BATCH_PATH.stat().st_size}")
    if issues:
        print("SELF_CHECK_ISSUES:")
        for item in issues:
            print(" -", item)
        return 1
    print("SELF_CHECK_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
