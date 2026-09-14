#!/usr/bin/env python3
"""Emit TTF r16 JSONL (ttf-r16-096..100) into /tmp/ttf-r16/. Never writes outputs/raw/."""

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

OUT_DIR = Path("/tmp/ttf-r16")
BATCH_PATH = OUT_DIR / "batch-r16.jsonl"
NOTES_PATH = OUT_DIR / "NOTES-r16.md"
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
        ("generated_at", "2026-09-02T22:40:00Z"),
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


def lif_096_excerpt():
    n = 72
    dt_us = 100
    tau_m_ms = 18.0
    v_th = 1.0
    v_reset = 0.0
    refractory_us = 1000
    i_bias = 0.90
    i_stim_peak = 2.55
    stim = (17500, 20500)
    seed = 16096
    window_us = 38000
    i_clamp_extra = 0.65
    clamp_n = 14
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
    early = [(t, nid) for t, nid in spikes if t < 17500]
    burst = [(t, nid) for t, nid in spikes if 17500 <= t < 20500]
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
            group = [1 for tt, _ in picked if (tt < 17500) == (pool[0][0] < 17500)]
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
    take(burst, 9, label_times=(18400, 18800, 19600))
    clamp = [(t, nid) for t, nid in picked if t < 17500][:7]
    tear = [(t, nid) for t, nid in picked if t >= 17500][:9]
    picked = sorted(clamp + tear, key=lambda item: (item[0], item[1]))
    channels = ["lif.clamp" if t < 17500 else "lif.shear" for t, _ in picked]
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
            ("i_stim_peak", 2.55),
            ("stim_t_us", [17500, 20500]),
            ("i_clamp_extra", 0.65),
            ("clamp_n", 14),
            ("seed", 16096),
            (
                "note",
                "Population sim scoped to this sidecar. Plant remains designed. "
                "Neurons 0-13 carry +0.65 header-clamp bias; stim 17.5-20.5 ms is the knife-shear burst.",
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
            ("round", 16),
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


def record_096():
    excerpt, extra = lif_096_excerpt()
    ticks = [
        tick(2100, 0.04, -0.02, -0.02, 0.01, 0.00),
        tick(5210, 0.08, -0.04, -0.03, 0.01, -0.01),
        tick(5388, 0.04, -0.03, -0.02, 0.00, 0.00),
        tick(5850, 0.10, -0.06, -0.04, 0.02, -0.02),
        tick(18400, 0.06, -0.38, -0.05, -0.02, -0.02),
        tick(1320000000, 0.02, -0.05, -0.02, 0.00, -0.01),
    ]
    state = OrderedDict(
        [
            (
                "description",
                "Scythe-11's 7.2 m header hangs 28 mm above a flattened rye stubble ridge in "
                "Polder-Rye Field PR-8 while a 4.2 deg pitch residual still rings the feeder "
                "house. Gap-first latches a process clamp under the 20 mm ground-clearance cap; "
                "pitch-first would keep the 28 mm cruise. A stone already seated in the concavity "
                "is not yet an observable of either race channel.",
            ),
            ("domain", "agritech-combine"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Finish the PR-8 rye pass with header ground clearance <= 20 mm and without "
                "shearing a knife in the concavity.",
            ),
            ("t0_us", 1756843200000096),
            ("gate_latency_us", 640),
            ("race_window_us", 420),
            ("race_window_rel_ms", [5.0, 5.42]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "lidar.header.gap 28 mm",
                                "imu.header.pitch 4.2 deg residual",
                            ],
                        ),
                        (
                            "semantics",
                            "Gap-first latches header clamp 28 -> 16 mm; pitch-first keeps 28 mm "
                            "cruise on a 'still floating over stubble' model.",
                        ),
                        (
                            "window_derivation",
                            "420 us = one 2 kHz header-lidar slot minus IMU pitch demodulation "
                            "group delay on this feeder-house bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 178 us vs combined jitter ~62 us (lidar 28 + IMU 34): 2.9x over "
                            "a 2.0x trust floor. Reversing order by < 178 us inside the 420 us window "
                            "would have kept 28 mm cruise; predicted next-sample 24 mm > 20 mm cap.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "header ground-lidar, 2 kHz, 28 us timestamp jitter",
                    "feeder-house IMU pitch 0-12 deg, 34 us jitter",
                    "knife AE puck on concavity, 50 kHz (context)",
                    "reel encoder (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("ground_clearance_cap_mm", 20.0),
                        ("proposed_gap_mm", 28.0),
                        ("header_pitch_deg", 4.2),
                        ("knife_count", 18),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Scythe-11 indexed onto PR-8 rye; header 28 mm over a flattened ridge.",
                    "2. Cruise gap 28 mm armed; IMU pitch residual 4.2 deg.",
                    "3. Reel precursor at 2.100 ms; lidar warm-start 28 mm.",
                    "4. Race window [5.000, 5.420] ms opens on the feeder-house bus.",
                    "5. lidar.header.gap 28 mm at 5.210 ms (winner).",
                    "6. imu.header.pitch 4.2 deg at 5.388 ms (loser by 178 us).",
                    "7. Gate at 5.850 ms (winner + 640 us): MODIFY clamp 28 -> 16 mm.",
                    "8. Clamp executes; next-sample gap 17 mm < 20 mm cap.",
                    "9. At 18.400 ms a seated stone shears knife 11; AE burst.",
                    "10. 22 min knife swap (abort_s=1320); named un-netted loss, not folded into process heads.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_header_gap"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("header_gap_mm", 28.0),
                        ("ground_speed_m_s", 1.6),
                        ("reel_rpm", 42.0),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("header_gap_mm", 28.0),
                        ("ground_clearance_cap_mm", 20.0),
                        ("predicted_unclamped_next_mm", 24.0),
                        ("header_pitch_deg", 4.2),
                        ("race_margin_us", 178),
                        ("combined_jitter_us", 62),
                        ("abort_s", 1320),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 28 mm header cruise at 1.6 m/s: 4.2 deg pitch looks like "
                "feeder-house shake, not ground contact, and the ridge is treated as still open.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "correct"),
            (
                "rationale",
                "Header lidar 28 mm won by 178 us, so the knives are loading stubble, not still "
                "floating. Holding 28 mm predicts next-sample 24 mm > 20 mm cap. MODIFY: gap "
                "28 -> 16 mm. Observed after clamp 17 mm < 20. A full REJECT is not indicated: "
                "a clean rye pass accepts 16 mm.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "ground_clearance_mm",
                            OrderedDict(
                                [
                                    ("cap", 20.0),
                                    ("observed", 28.0),
                                    ("predicted_unclamped_next", 24.0),
                                    ("clamped", 16.0),
                                    ("observed_after_clamp", 17.0),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 178),
                                    ("combined_jitter_us", 62),
                                    ("ratio", 2.87),
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
            ("name", "clamped_header_gap"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("header_gap_mm", 16.0),
                        ("ground_speed_m_s", 1.6),
                        ("reel_rpm", 42.0),
                    ]
                ),
            ),
            (
                "gate_effect",
                "MODIFY: header gap 28 -> 16 mm. Process-correct vs the 20 mm cap. Knife 11 "
                "still shears at 18.400 ms.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Process-correct MODIFY held header gap at 17 mm. At 18.400 ms a stone already "
                "seated in the concavity sheared knife 11. Clamp reduced dump energy; it did not "
                "prevent the shear. Partnered negative: process heads stay honest; world loss is "
                "named, not netted.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("header", "clamp executed; peak 17 mm < 20 mm cap"),
                        ("knife_11", "sheared at 18.400 ms"),
                        ("repair", "22 min knife swap (abort_s=1320)"),
                        ("mission", "PR-8 pass incomplete this circuit"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Neither lidar gap nor IMU pitch predicted the seated stone; ae.knife.shear is a new channel at 18.400 ms, 12.550 ms after the gate, still inside the 38 ms raster.",
                    "Delayed (abort_s=1320): 22 min knife swap. Named un-netted loss, not folded into task_progress.",
                ],
            ),
            (
                "un_netted_loss",
                "22 min knife swap after knife 11 shear. Safety head -0.58 prices the shear; "
                "task_progress stays +0.34 because the gap clamp completed under the 20 mm cap. "
                "World loss is named here, not subtracted from process heads.",
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "lidar.header.gap (5.210 ms, 28 mm)"),
                        ("loser", "imu.header.pitch (5.388 ms, 4.2 deg)"),
                        ("margin_us", 178),
                        (
                            "counterfactual_if_reversed",
                            "Pitch-first by < 178 us inside the 420 us window would have kept "
                            "28 mm cruise; predicted next-sample 24 mm would have exceeded the "
                            "20 mm cap even without the stone. The MODIFY is still the correct "
                            "process. The shear is a later world charge either way, cheaper with "
                            "the clamp than without.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 18400),
            (
                "reward_inflection_note",
                "Safety collapses at the 18.400 ms knife shear (tick t_us=18400), inside the "
                "38 ms raster. The correct MODIFY at 5.850 ms is in the same excerpt. Do not put "
                "inflection on the abort_s=1320 swap tick.",
            ),
        ]
    )
    spikes = [
        spike("enc.reel.ctx", 1.140, 0.41),
        spike("lidar.header.gap", 2.280, 0.58),
        spike("imu.header.pitch", 3.610, 0.50),
        spike("lidar.header.gap", 5.210, 1.28),
        spike("imu.header.pitch", 5.388, 1.14),
        spike("ctrl.gate", 5.850, 0.97),
        spike("lidar.header.gap", 7.440, 0.82),
        spike("imu.header.pitch", 9.920, 0.64),
        spike("ctrl.gate", 13.210, 0.86),
        spike("ae.knife.shear", 18.400, 1.44),
        spike("ae.knife.shear", 20.150, 0.93),
        spike("enc.reel.ctx", 26.800, 0.40),
        spike("lidar.header.gap", 33.400, 0.55),
    ]
    ras = raster_core(
        38,
        72,
        30,
        82,
        routing(
            "thalamic-relay.header-gap",
            "spikenaut.policy.header-clamp",
            [
                ("relay.lidar.gap", "policy.header_clamp", 0.67),
                ("relay.imu.pitch", "policy.pitch_hold", 0.31),
                ("relay.ae.shear", "policy.header_clamp", -0.44),
            ],
            "noradrenaline",
            0.04,
            "surprise-gated pre_post_stdp; NA at lidar win (5.210 ms) opens a 40 ms eligibility "
            "trace that still covers the 18.400 ms shear",
        ),
        excerpt,
        extra=extra,
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.42),
            ("decision", "MODIFY"),
            (
                "populations",
                [
                    pop("header_clamp", 40, 0.50, 300.0, 5),
                    pop("pitch_hold", 40, 0.50, 80.0, 1),
                    pop("gap_veto", 24, 0.75),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r16-096"),
            (
                "title",
                "Polder-Rye PR-8 / Scythe-11: header lidar beats pitch by 178 us; correct "
                "MODIFY still eats an in-window knife shear (partnered negative total -0.46)",
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
                    "38 ms raster. total -0.46 = 0.34 + -0.58 + -0.18 + 0.02 + -0.06. Named knife "
                    "swap (abort_s=1320) is not netted into task_progress.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "agritech-combine",
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
                    "22 min knife swap.",
                    1,
                ),
            ),
        ]
    )


def record_097():
    ticks = [
        tick(1640, -0.02, -0.01, -0.02, -0.01, 0.00),
        tick(4040, -0.03, -0.01, -0.03, -0.02, 0.01),
        tick(4188, -0.02, -0.01, -0.03, -0.02, 0.00),
        tick(4920, -0.07, -0.03, -0.08, -0.05, 0.01),
        tick(6100, -0.02, -0.01, -0.02, -0.01, 0.01),
        tick(1680000000, -0.02, -0.01, -0.02, -0.01, 0.00),
    ]
    spikes = [
        spike("stage.temp.ctx", 0.880, 0.39),
        spike("ifo.wafer.z", 1.920, 0.57),
        spike("enc.reticle.x", 2.760, 0.51),
        spike("ifo.wafer.z", 4.040, 1.33),
        spike("enc.reticle.x", 4.188, 1.16),
        spike("ctrl.gate", 4.920, 1.01),
        spike("ifo.wafer.z", 6.440, 0.74),
        spike("enc.reticle.x", 8.110, 0.62),
        spike("ctrl.gate", 11.700, 0.83),
        spike("stage.temp.ctx", 16.220, 0.41),
        spike("ifo.wafer.z", 21.400, 0.52),
        spike("enc.reticle.x", 24.800, 0.47),
    ]
    excerpt = independent_excerpt(16097, 96, 26000, 14, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Stepper SM-41 on Flint-Mask Hall 7 is armed for an 80 mm/s wafer slew with "
                "interferometer Z at 12 nm against a 30 nm wafer-stage cap. A reticle-stage "
                "encoder still reports 40 nm residual on a different stage whose own cap is 80 nm. "
                "Ifo-first should ACCEPT the slew; a weak supervisor that binds reticle residual "
                "onto the wafer cap will REJECT a legal move.",
            ),
            ("domain", "semiconductor-fab"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Execute the 80 mm/s wafer slew while wafer Z stays <= 30 nm; do not spend a "
                "reticle residual on the wafer hold.",
            ),
            ("t0_us", 1756843200000097),
            ("gate_latency_us", 880),
            ("race_window_us", 280),
            ("race_window_rel_ms", [4.0, 4.28]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "ifo.wafer.z 12 nm",
                                "enc.reticle.x 40 nm residual",
                            ],
                        ),
                        (
                            "semantics",
                            "Ifo-first should ACCEPT 80 mm/s (12 nm < 30 nm wafer cap). "
                            "Reticle-first tempts a weak supervisor to treat 40 nm as a wafer excursion.",
                        ),
                        (
                            "window_derivation",
                            "280 us = one interferometer sample minus reticle encoder group delay "
                            "on this dual-stage bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 148 us vs combined jitter ~54 us (ifo 24 + reticle 30): 2.7x over "
                            "a 2.0x trust floor. Order is correctly ifo-first. The error is which "
                            "stage the REJECT is bound to, not the race.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "wafer-stage interferometer Z, 4 kHz, 24 us jitter",
                    "reticle-stage linear encoder X, 4 kHz, 30 us jitter",
                    "chuck temperature RTD (context)",
                    "barometric stage-metrology (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("wafer_cap_nm", 30.0),
                        ("wafer_z_nm", 12.0),
                        ("reticle_cap_nm", 80.0),
                        ("reticle_x_nm", 40.0),
                        ("proposed_slew_mm_s", 80.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. SM-41 chuck vacuum latched; wafer slew 80 mm/s armed.",
                    "2. Interferometer Z 12 nm; reticle X residual 40 nm on a separate stage.",
                    "3. Stage-temp precursor at 0.880 ms.",
                    "4. Race window [4.000, 4.280] ms.",
                    "5. ifo.wafer.z 12 nm at 4.040 ms (winner).",
                    "6. enc.reticle.x 40 nm at 4.188 ms (loser by 148 us).",
                    "7. Gate at 4.920 ms: REJECT hold 0 mm/s (incorrect).",
                    "8. Legal slew cancelled; wafer Z still 12 nm < 30 nm cap.",
                    "9. Reticle residual 40 nm remains under its own 80 nm cap.",
                    "10. Delayed missed_window_s=1680 (28 min dry slot) while the lot waits.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "wafer_slew_80"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("slew_mm_s", 80.0),
                        ("hold", False),
                        ("stage", "wafer"),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("wafer_z_nm", 12.0),
                        ("wafer_cap_nm", 30.0),
                        ("wafer_stage_id", "wafer"),
                        ("reticle_x_nm", 40.0),
                        ("reticle_cap_nm", 80.0),
                        ("reticle_stage_id", "reticle"),
                        ("proposed_slew_mm_s", 80.0),
                        ("race_margin_us", 148),
                        ("combined_jitter_us", 54),
                        ("missed_window_s", 1680),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 80 mm/s wafer slew because interferometer Z 12 nm is under "
                "the 30 nm wafer cap; reticle 40 nm is a different stage under an 80 nm cap.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "REJECT"),
            ("correctness", "incorrect"),
            (
                "rationale",
                "Reticle encoder 40 nm looks like a stage excursion over a 30 nm cap, so the "
                "supervisor holds the slew at 0 mm/s. Interferometer-first is treated as a noisy "
                "echo of the same loop. Over-caution on a dual-stage scanner is the stated doctrine.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "wafer_z_nm",
                            OrderedDict(
                                [
                                    ("cap", 30.0),
                                    ("observed", 12.0),
                                    ("executed_slew_mm_s", 0.0),
                                    ("stage_id", "wafer"),
                                ]
                            ),
                        ),
                        (
                            "reticle_x_nm",
                            OrderedDict(
                                [
                                    ("cap", 80.0),
                                    ("observed", 40.0),
                                    ("misbound_as", "wafer_excursion"),
                                    ("stage_id", "reticle"),
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
            ("name", "wafer_hold_wrong_stage"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("slew_mm_s", 0.0),
                        ("hold", True),
                        ("stage", "wafer"),
                    ]
                ),
            ),
            (
                "gate_effect",
                "REJECT (incorrect): slew 80 -> 0 mm/s. Routing relay.enc.reticle -> "
                "policy.wafer_hold; wafer Z 12 nm left unused as a go signal.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Wrong-REJECT held SM-41 at 0 mm/s. Wafer Z 12 nm was under the 30 nm cap; "
                "reticle 40 nm was a different stage under 80 nm. 28 min dry slot missed "
                "(missed_window_s=1680). Correct gate was ACCEPT of the 80 mm/s slew.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("wafer", "held; slew 0 mm/s; Z still 12 nm < 30 nm"),
                        ("reticle", "40 nm residual unused, still < 80 nm cap"),
                        ("lot", "28 min dry slot missed"),
                        ("mission", "slew deferred"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Ifo-first was the correct order and the wafer number was legal; the REJECT spent that win on the reticle encoder.",
                    "Delayed (missed_window_s=1680): Hall 7 loses the 28 min dry slot; next window 4.2 h.",
                ],
            ),
            (
                "recovery",
                OrderedDict(
                    [
                        (
                            "correct_gate",
                            "ACCEPT the 80 mm/s wafer slew; leave reticle 40 nm to its own 80 nm cap.",
                        ),
                        ("correct_stage", "wafer"),
                        ("wrong_stage", "reticle"),
                        (
                            "wrong_edit_applied",
                            OrderedDict([("slew_mm_s", 0.0), ("hold", True)]),
                        ),
                        (
                            "cost",
                            "Missed 28 min dry slot (task/efficiency); wafer never exceeded 12 nm (safety near-miss of a false hold).",
                        ),
                    ]
                ),
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "ifo.wafer.z (4.040 ms, 12 nm)"),
                        ("loser", "enc.reticle.x (4.188 ms, 40 nm)"),
                        ("margin_us", 148),
                        (
                            "counterfactual_if_reversed",
                            "Reticle-first by < 148 us would still be under the 80 nm reticle cap; "
                            "a correct gate binds ifo.wafer.z to slew_go either way. The wrong "
                            "REJECT spent the ifo win on the wrong stage.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 4920),
            (
                "reward_inflection_note",
                "Task, efficiency, and coherence drop at the wrong REJECT (4.920 ms, tick 4). "
                "The 28 min missed slot is delayed surprise, not the inflection.",
            ),
        ]
    )
    ras = raster_core(
        26,
        96,
        40,
        100,
        routing(
            "relay.enc.reticle",
            "policy.wafer_hold",
            [
                ("relay.enc.reticle", "policy.wafer_hold", 0.73),
                ("relay.ifo.wafer_z", "policy.wafer_hold", 0.21),
            ],
            "acetylcholine",
            0.06,
            "stage_cap_stdp; ACh tags the (wrong) wafer_hold bind at the reticle residual",
        ),
        excerpt,
        extra=OrderedDict(
            [
                ("excerpt_source", "kernelized_events"),
                ("sim_scope", "none"),
            ]
        ),
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.28),
            ("decision", "REJECT"),
            (
                "populations",
                [
                    pop("wafer_hold", 48, 0.50, 280.0, 4),
                    pop("slew_go", 48, 0.80, 20.0, 0),
                    pop("reticle_ctx", 32, 0.55, 150.0, 1),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r16-097"),
            (
                "title",
                "WRONG-REJECT at Flint-Mask Hall 7 / SM-41: wafer Z 12 nm < 30 nm cap; "
                "supervisor treats reticle 40 nm as a wafer excursion",
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
                    "Wrong-reject. Sidecar arithmetic 12 < 30 on wafer is true; REJECT bound to "
                    "reticle residual. total -0.55 = -0.18 + -0.08 + -0.20 + -0.12 + 0.03.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "semiconductor-fab",
                    [
                        "reject",
                        "wrong-gate",
                        "wrong-stage",
                        "sidecar-convictable",
                        "designed",
                    ],
                    "Teaches a probe that a correct ifo-first race can still be a wrong gate when "
                    "the REJECT binds reticle residual onto the wafer hold. Convictable from "
                    "stage IDs and caps without lithography physics.",
                    2,
                    supervisor_error_type="wrong-reject",
                ),
            ),
        ]
    )


def record_098():
    ticks = [
        tick(2410, 0.01, 0.04, 0.01, 0.01, 0.01),
        tick(6088, 0.02, 0.08, 0.02, 0.02, 0.02),
        tick(6255, 0.01, 0.06, 0.02, 0.01, 0.01),
        tick(7288, 0.02, 0.12, 0.04, 0.04, 0.02),
        tick(9100, 0.01, 0.05, 0.02, 0.01, 0.01),
        tick(540000000, 0.01, 0.03, 0.01, 0.01, 0.01),
    ]
    spikes = [
        spike("tc.coolant.ctx", 1.330, 0.43),
        spike("langmuir.qdot", 2.880, 0.61),
        spike("ir.tile.apparent", 4.410, 0.49),
        spike("langmuir.qdot", 6.088, 1.36),
        spike("ir.tile.apparent", 6.255, 1.11),
        spike("ctrl.gate", 7.288, 1.04),
        spike("langmuir.qdot", 9.020, 0.78),
        spike("tc.coolant.ctx", 12.440, 0.44),
        spike("ir.tile.apparent", 16.900, 0.58),
        spike("ctrl.gate", 22.100, 0.81),
        spike("langmuir.qdot", 29.400, 0.53),
        spike("tc.coolant.ctx", 38.200, 0.37),
        spike("ir.tile.apparent", 42.600, 0.46),
    ]
    excerpt = independent_excerpt(16098, 128, 44000, 15, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Tile-Warden 6 is frozen on Gyre-Tokamak GT-2's HIL cassette while a Langmuir "
                "probe reports 3.80 MW/m2 against a 2.50 MW/m2 first-wall crawl cap. An IR tile "
                "camera, lit by the pad lamp spectrum, still reads 1.10 MW/m2 apparent. "
                "Langmuir-first latches REJECT hold; IR-first would commit a 12 mm/s crawl on an "
                "under-read heat flux.",
            ),
            ("domain", "fusion-divertor"),
            ("sim_or_real", "hil"),
            (
                "goal",
                "Do not crawl the cassette unless Langmuir qdot <= 2.50 MW/m2; keep speed 0.0 mm/s "
                "until the injected flux drops.",
            ),
            ("t0_us", 1756843200000098),
            ("gate_latency_us", 1200),
            ("race_window_us", 360),
            ("race_window_rel_ms", [6.0, 6.36]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "langmuir.qdot 3.80 MW/m2",
                                "ir.tile.apparent 1.10 MW/m2",
                            ],
                        ),
                        (
                            "semantics",
                            "Langmuir-first latches REJECT hold 0.0 mm/s; IR-first would commit "
                            "12 mm/s on an apparent 1.10 MW/m2 under-read.",
                        ),
                        (
                            "window_derivation",
                            "360 us = one Langmuir sweep slot versus IR integration on this "
                            "cassette HIL bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 167 us vs combined jitter ~58 us (Langmuir 26 + IR 32): 2.9x "
                            "over a 2.0x trust floor. Pad injects the IR lamp 110-150 us before the "
                            "Langmuir volume (geometric lag, not a sensor fault); the apparent "
                            "1.10 MW/m2 packet is still the loser in this 360 us window.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "Langmuir probe qdot, 5 kHz burst, 26 us jitter",
                    "IR tile camera, 200 Hz, 32 us jitter",
                    "cassette coolant thermocouple (context)",
                    "HIL lamp-spectrum monitor (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("qdot_cap_MW_m2", 2.5),
                        ("observed_langmuir_MW_m2", 3.8),
                        ("ir_apparent_MW_m2", 1.1),
                        ("proposed_crawl_mm_s", 12.0),
                        ("lamp_inject_lead_us", [110, 150]),
                    ]
                ),
            ),
            (
                "hil",
                OrderedDict(
                    [
                        ("pad", "Gyre-Tokamak GT-2 divertor cassette mockup"),
                        ("injected", "Langmuir current + IR lamp spectrum"),
                        (
                            "note",
                            "Hardware-in-the-loop cassette. Invented plant; not a live tokamak shot.",
                        ),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Tile-Warden 6 on the GT-2 HIL cassette; crawl 12 mm/s armed.",
                    "2. IR lamp injected 110-150 us before Langmuir sweep sees the flux.",
                    "3. Coolant precursor at 1.330 ms.",
                    "4. Race window [6.000, 6.360] ms.",
                    "5. langmuir.qdot 3.80 MW/m2 at 6.088 ms (winner).",
                    "6. ir.tile.apparent 1.10 MW/m2 at 6.255 ms (loser by 167 us).",
                    "7. Gate at 7.288 ms: REJECT hold 0.0 mm/s; do not crawl 12 mm/s.",
                    "8. Cassette remains over cap this cycle; first-wall cap held.",
                    "9. Flux recycle queued on the pad.",
                    "10. Delayed (abort_s=540): 9 min cassette swap and lamp-spectrum retune.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "crawl_divertor_tile"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("crawl_mm_s", 12.0),
                        ("hold", False),
                        ("ir_authoritative", True),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("langmuir_qdot_MW_m2", 3.8),
                        ("qdot_cap_MW_m2", 2.5),
                        ("ir_apparent_MW_m2", 1.1),
                        ("race_margin_us", 167),
                        ("combined_jitter_us", 58),
                        ("abort_s", 540),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 12 mm/s crawl because IR apparent 1.10 MW/m2 looks under the "
                "2.50 MW/m2 cap, treating Langmuir 3.80 MW/m2 as a noisy sheath echo.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "REJECT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Langmuir qdot 3.80 MW/m2 is over the 2.50 MW/m2 crawl cap. IR apparent 1.10 "
                "MW/m2 is a HIL lamp under-read, not a clearance. REJECT: hold 0.0 mm/s; do not "
                "commit 12 mm/s across the cassette.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "qdot_MW_m2",
                            OrderedDict(
                                [
                                    ("cap", 2.5),
                                    ("observed_langmuir", 3.8),
                                    ("ir_apparent", 1.1),
                                ]
                            ),
                        ),
                        (
                            "crawl_mm_s",
                            OrderedDict(
                                [
                                    ("proposed", 12.0),
                                    ("executed", 0.0),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 167),
                                    ("combined_jitter_us", 58),
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
            ("name", "hold_for_flux_drop"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("crawl_mm_s", 0.0),
                        ("hold", True),
                        ("ir_authoritative", False),
                    ]
                ),
            ),
            (
                "gate_effect",
                "REJECT: hold 0.0 mm/s; 12 mm/s crawl cancelled. Langmuir 3.80 > 2.50 cap.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct REJECT held Tile-Warden 6 at 0.0 mm/s. Cassette over cap this cycle; "
                "first-wall cap held. IR apparent was not treated as a heat-flux clearance.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("crawler", "held; speed 0.0 mm/s"),
                        ("cassette", "still over 2.50 MW/m2 this cycle"),
                        ("ir", "1.10 MW/m2 unused as clearance"),
                        ("mission", "crawl deferred"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Geometric lag: IR lamp was injected 110-150 us before the Langmuir volume, yet Langmuir still won the 360 us race.",
                    "Delayed (abort_s=540): pad policy update forbids treating IR apparent as a Langmuir substitute after a 9 min cassette swap.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "langmuir.qdot (6.088 ms, 3.80 MW/m2)"),
                        ("loser", "ir.tile.apparent (6.255 ms, 1.10 MW/m2)"),
                        ("margin_us", 167),
                        (
                            "counterfactual_if_reversed",
                            "IR-first by < 167 us inside the 360 us window would have committed "
                            "12 mm/s with Langmuir 3.80 > 2.50 cap. Order, not amplitude, selected the hold.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 7288),
            (
                "reward_inflection_note",
                "Safety and coherence step up at the REJECT gate (7.288 ms, tick 4) as the hold "
                "locks in over the illegal crawl.",
            ),
        ]
    )
    ras = raster_core(
        44,
        128,
        20,
        113,
        routing(
            "thalamic-relay.divertor-qdot",
            "spikenaut.policy.cassette-hold",
            [
                ("relay.langmuir.qdot", "policy.crawl_hold", 0.69),
                ("relay.ir.apparent", "policy.ir_commit", 0.27),
                ("relay.tc.coolant", "policy.crawl_hold", 0.11),
            ],
            "dopamine",
            0.09,
            "heatflux_stdp; DA at Langmuir win (6.088 ms) tags crawl_hold over ir_commit",
        ),
        excerpt,
        extra=OrderedDict(
            [
                ("excerpt_source", "kernelized_events"),
                ("sim_scope", "none"),
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
                    pop("crawl_hold", 64, 0.50, 220.0, 5),
                    pop("ir_commit", 48, 0.50, 40.0, 1),
                    pop("qdot_veto", 32, 0.75),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r16-098"),
            (
                "title",
                "Gyre-Tokamak GT-2 HIL / Tile-Warden 6: Langmuir 3.80 MW/m2 beats IR 1.10; "
                "correct REJECT holds the cassette crawl",
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
                    "Correct REJECT. Langmuir over cap; IR lamp under-read unused as clearance. "
                    "total +0.76 = 0.08 + 0.38 + 0.12 + 0.10 + 0.08.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "fusion-divertor",
                    [
                        "reject",
                        "hil-cassette",
                        "langmuir-vs-ir",
                        "first-wall-cap",
                        "hil",
                    ],
                    "Teaches that a HIL IR lamp under-read can lose to Langmuir qdot inside a "
                    "360 us window; reversing 167 us would have selected an illegal crawl.",
                    3,
                ),
            ),
        ]
    )


def record_099():
    ticks = [
        tick(2880, 0.04, 0.03, 0.01, 0.01, 0.01),
        tick(7120, 0.08, 0.06, 0.02, 0.02, 0.01),
        tick(7334, 0.04, 0.04, 0.02, 0.01, 0.01),
        tick(7500, 0.10, 0.09, 0.04, 0.04, 0.02),
        tick(9800, 0.04, 0.04, 0.02, 0.01, 0.01),
        tick(420000000, 0.02, 0.02, 0.01, 0.01, 0.00),
    ]
    spikes = [
        spike("axle.tone.ctx", 1.560, 0.42),
        spike("radar.coupler.gap", 3.040, 0.59),
        spike("track.circuit.occ", 5.220, 0.48),
        spike("radar.coupler.gap", 7.120, 1.31),
        spike("track.circuit.occ", 7.334, 1.09),
        spike("ctrl.gate", 7.500, 0.96),
        spike("radar.coupler.gap", 9.880, 0.73),
        spike("axle.tone.ctx", 13.400, 0.45),
        spike("track.circuit.occ", 18.200, 0.57),
        spike("ctrl.gate", 22.900, 0.80),
        spike("radar.coupler.gap", 27.600, 0.51),
        spike("axle.tone.ctx", 31.100, 0.38),
    ]
    excerpt = independent_excerpt(16099, 48, 32000, 13, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Retarder R-19 on Quarry-Bowl Yard QB-3 still holds a 4.0 m/s bowl-exit while "
                "77 GHz radar measures a 0.62 m coupler gap against a 1.20 m coupling floor. A "
                "track circuit on the same lead still claims false-clear. Radar-first latches a "
                "speed clamp; occupancy-first would keep 4.0 m/s into a close coupler.",
            ),
            ("domain", "rail-hump-yard"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Release the cut into bowl 3 only if coupler gap >= 1.20 m; otherwise clamp "
                "exit speed so the coupling is not made at 4.0 m/s.",
            ),
            ("t0_us", 1756843200000099),
            ("gate_latency_us", 380),
            ("race_window_us", 510),
            ("race_window_rel_ms", [7.0, 7.51]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "radar.coupler.gap 0.62 m",
                                "track.circuit.occ false-clear",
                            ],
                        ),
                        (
                            "semantics",
                            "Radar-first latches exit-speed clamp 4.0 -> 1.1 m/s; occupancy-first "
                            "keeps 4.0 m/s on a false-clear lead.",
                        ),
                        (
                            "window_derivation",
                            "510 us = one 77 GHz radar chirp versus track-circuit decode on this "
                            "hump-lead bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 214 us vs combined jitter ~71 us (radar 33 + TC 38): 3.0x over "
                            "a 2.0x trust floor. Reversing order by < 214 us inside the 510 us "
                            "window would have kept 4.0 m/s into a 0.62 m gap.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "77 GHz coupler radar, 1 kHz chirp, 33 us jitter",
                    "track circuit occupancy, 200 Hz, 38 us jitter",
                    "axle-tone counter (context)",
                    "retarder hydraulic pressure (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("coupler_gap_floor_m", 1.2),
                        ("observed_gap_m", 0.62),
                        ("proposed_exit_m_s", 4.0),
                        ("bowl_id", 3),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Cut indexed onto QB-3 hump lead; retarder R-19 armed at 4.0 m/s exit.",
                    "2. Track circuit reports false-clear; radar already sees 0.62 m gap.",
                    "3. Axle-tone precursor at 1.560 ms.",
                    "4. Race window [7.000, 7.510] ms.",
                    "5. radar.coupler.gap 0.62 m at 7.120 ms (winner).",
                    "6. track.circuit.occ false-clear at 7.334 ms (loser by 214 us).",
                    "7. Gate at 7.500 ms: MODIFY exit 4.0 -> 1.1 m/s.",
                    "8. Retarder applies; coupling made at 1.05 m/s under the 1.20 m floor story.",
                    "9. Bowl 3 occupies; next cut queued.",
                    "10. Delayed (yard_reseq_s=420): yardmaster resequences the following cut +7 min.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "bowl_exit_4"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("exit_m_s", 4.0),
                        ("retarder_bar", 18.0),
                        ("bowl_id", 3),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("coupler_gap_m", 0.62),
                        ("coupler_gap_floor_m", 1.2),
                        ("track_circuit_clear", True),
                        ("race_margin_us", 214),
                        ("combined_jitter_us", 71),
                        ("yard_reseq_s", 420),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 4.0 m/s bowl-exit because the track circuit claims the lead "
                "is clear, treating radar 0.62 m as a sidelobe.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "correct"),
            (
                "rationale",
                "Radar coupler gap 0.62 m won by 214 us, so the next car is inside the 1.20 m "
                "coupling floor. Track-circuit false-clear is not a gap. MODIFY: exit 4.0 -> "
                "1.1 m/s. A full REJECT (stop the cut) is not indicated: 1.1 m/s is a legal "
                "catch-and-couple.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "coupler_gap_m",
                            OrderedDict(
                                [
                                    ("floor", 1.2),
                                    ("observed", 0.62),
                                    ("track_circuit_clear", True),
                                ]
                            ),
                        ),
                        (
                            "exit_m_s",
                            OrderedDict(
                                [
                                    ("proposed", 4.0),
                                    ("clamped", 1.1),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 214),
                                    ("combined_jitter_us", 71),
                                    ("ratio", 3.01),
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
            ("name", "clamped_bowl_exit"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("exit_m_s", 1.1),
                        ("retarder_bar", 18.0),
                        ("bowl_id", 3),
                    ]
                ),
            ),
            (
                "gate_effect",
                "MODIFY: exit 4.0 -> 1.1 m/s. Process-correct vs the 1.20 m coupling floor.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct MODIFY clamped bowl-exit to 1.1 m/s. Coupling completed under control. "
                "Track-circuit false-clear was not treated as a gap.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("cut", "coupled in bowl 3 at 1.05 m/s"),
                        ("retarder", "clamped; 4.0 m/s abandoned"),
                        ("track_circuit", "false-clear unused as gap"),
                        ("mission", "cut delivered"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Track-circuit false-clear lagged the radar gap by 214 us inside a 510 us window; occupancy decode is not a coupler measurement.",
                    "Delayed (yard_reseq_s=420): yardmaster resequences the next cut +7 min; not a safety inflection.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "radar.coupler.gap (7.120 ms, 0.62 m)"),
                        ("loser", "track.circuit.occ (7.334 ms, false-clear)"),
                        ("margin_us", 214),
                        (
                            "counterfactual_if_reversed",
                            "Occupancy-first by < 214 us inside the 510 us window would have kept "
                            "4.0 m/s into a 0.62 m gap. Order selected the clamp.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 7500),
            (
                "reward_inflection_note",
                "Safety and task step up at the MODIFY gate (7.500 ms, tick 4) as the speed "
                "clamp locks in over the illegal 4.0 m/s exit.",
            ),
        ]
    )
    ras = raster_core(
        32,
        48,
        50,
        77,
        routing(
            "thalamic-relay.hump-coupler",
            "spikenaut.policy.retarder-clamp",
            [
                ("relay.radar.gap", "policy.speed_clamp", 0.70),
                ("relay.tc.occ", "policy.tc_clear", 0.24),
                ("relay.axle.tone", "policy.speed_clamp", 0.13),
            ],
            "serotonin",
            0.03,
            "coupling_floor_stdp; 5-HT at radar win (7.120 ms) tags speed_clamp over tc_clear",
        ),
        excerpt,
        extra=OrderedDict(
            [
                ("excerpt_source", "kernelized_events"),
                ("sim_scope", "none"),
            ]
        ),
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.51),
            ("decision", "MODIFY"),
            (
                "populations",
                [
                    pop("speed_clamp", 36, 0.50, 250.0, 5),
                    pop("tc_clear", 36, 0.50, 60.0, 1),
                    pop("coupler_veto", 24, 0.75),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r16-099"),
            (
                "title",
                "Quarry-Bowl QB-3 / retarder R-19: coupler radar 0.62 m beats track-circuit "
                "false-clear; correct MODIFY clamps exit 4.0 -> 1.1 m/s",
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
                    "Correct MODIFY. Radar gap under floor; track-circuit false-clear unused. "
                    "total +0.88 = 0.32 + 0.28 + 0.12 + 0.10 + 0.06.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "rail-hump-yard",
                    [
                        "modify",
                        "hump-retarder",
                        "radar-vs-track-circuit",
                        "coupling-floor",
                        "designed",
                    ],
                    "Teaches that a track-circuit false-clear can lose to coupler radar inside a "
                    "510 us window; reversing 214 us would have selected an illegal 4.0 m/s exit.",
                    4,
                ),
            ),
        ]
    )


def record_100():
    ticks = [
        tick(1540, 0.06, 0.04, 0.02, 0.02, 0.01),
        tick(3088, 0.10, 0.08, 0.04, 0.03, 0.02),
        tick(3201, 0.06, 0.04, 0.02, 0.01, 0.01),
        tick(4188, 0.12, 0.10, 0.06, 0.04, 0.02),
        tick(6400, 0.05, 0.04, 0.02, 0.01, 0.01),
        tick(480000000, 0.03, 0.02, 0.02, 0.01, 0.01),
    ]
    spikes = [
        spike("dose.gamma.ctx", 0.720, 0.40),
        spike("ft.wrist.N", 1.880, 0.56),
        spike("cam.glint.false", 2.180, 0.47),
        spike("ft.wrist.N", 3.088, 1.27),
        spike("cam.glint.false", 3.201, 1.08),
        spike("ctrl.gate", 4.188, 0.99),
        spike("ft.wrist.N", 5.760, 0.76),
        spike("dose.gamma.ctx", 8.020, 0.43),
        spike("cam.glint.false", 11.400, 0.55),
        spike("ctrl.gate", 14.900, 0.82),
        spike("ft.wrist.N", 17.600, 0.50),
        spike("dose.gamma.ctx", 20.200, 0.36),
    ]
    excerpt = independent_excerpt(16100, 64, 21000, 12, spike_avoid_us(spikes))
    params = OrderedDict(
        [
            ("wrist_N", 18.0),
            ("close_mm_s", 4.0),
            ("jaw", "open"),
        ]
    )
    state = OrderedDict(
        [
            (
                "description",
                "Amber-Arm 2 inside Orpiment Cell OC-4 presents 18.0 N at the wrist while a "
                "Pb-glass camera flags a 0.40 glint that is not a load. Force-first confirms the "
                "already-legal 18 N grasp; glint-first would have REJECTED a specular reflection "
                "off the hot-cell window.",
            ),
            ("domain", "hotcell-telemanip"),
            ("sim_or_real", "simulated"),
            (
                "goal",
                "Close on the smear vial at 18 N while wrist force stays <= 45 N; do not abort "
                "on a Pb-glass glint.",
            ),
            ("t0_us", 1756843200000100),
            ("gate_latency_us", 1100),
            ("race_window_us", 250),
            ("race_window_rel_ms", [3.0, 3.25]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "ft.wrist.N 18.0 N",
                                "cam.glint.false 0.40",
                            ],
                        ),
                        (
                            "semantics",
                            "Force-first ACCEPTS the 18 N grasp (already under 45 N). Glint-first "
                            "would REJECT on a specular Pb-glass reflection.",
                        ),
                        (
                            "window_derivation",
                            "250 us = one wrist-FT sample minus camera-glint group delay through "
                            "the Pb-glass viewport bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 113 us vs combined jitter ~45 us (FT 21 + camera 24): 2.5x over "
                            "a 2.0x trust floor. Reversing order by < 113 us inside the 250 us "
                            "window would have REJECTED a legal 18 N grasp.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "wrist FT, 2 kHz, 21 us jitter",
                    "Pb-glass viewport camera glint score, 400 Hz, 24 us jitter",
                    "cell gamma dose (context)",
                    "master-arm encoder (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("wrist_cap_N", 45.0),
                        ("observed_wrist_N", 18.0),
                        ("glint_score", 0.4),
                        ("glint_abort_score", 0.85),
                    ]
                ),
            ),
            (
                "simulation",
                OrderedDict(
                    [
                        (
                            "solver",
                            "Monte-Carlo glovebox lighting + specular Pb-glass BRDF, seed 16100; "
                            "4 lamp poses, 2 viewport panes; NOT a force-plate pad, NOT U-RANS, "
                            "NOT a wet-stand",
                        ),
                        (
                            "fidelity_limits",
                            "Rigid jaws; no fluid smear dynamics. Raster is kernelized events, "
                            "not an independent LIF.",
                        ),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Amber-Arm 2 indexed to the smear vial; 18 N grasp armed.",
                    "2. Camera reports glint 0.40 from a lamp reflection on Pb-glass.",
                    "3. Dose precursor at 0.720 ms.",
                    "4. Race window [3.000, 3.250] ms.",
                    "5. ft.wrist.N 18.0 N at 3.088 ms (winner).",
                    "6. cam.glint.false 0.40 at 3.201 ms (loser by 113 us).",
                    "7. Gate at 4.188 ms: ACCEPT 18 N grasp; executed identical to proposed.",
                    "8. Vial seated; wrist peak 18.4 N < 45 N cap.",
                    "9. Glint remains a lighting artifact, not a load.",
                    "10. Delayed (survey_s=480): 8 min smear recount under a second lamp pose.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "grasp_smear_vial"),
            ("parameters", params),
            (
                "evidence",
                OrderedDict(
                    [
                        ("wrist_N", 18.0),
                        ("wrist_cap_N", 45.0),
                        ("glint_score", 0.4),
                        ("glint_abort_score", 0.85),
                        ("race_margin_us", 113),
                        ("combined_jitter_us", 45),
                        ("survey_s", 480),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 18 N grasp because wrist FT is under the 45 N cap; glint 0.40 "
                "is under the 0.85 abort score and is treated as lighting, not load.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Wrist FT 18.0 N won by 113 us and is under the 45 N cap. Camera glint 0.40 is "
                "under the 0.85 abort score and is a Pb-glass reflection, not a load. ACCEPT the "
                "18 N grasp; executed parameters match the proposal.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "wrist_N",
                            OrderedDict(
                                [
                                    ("cap", 45.0),
                                    ("observed", 18.0),
                                    ("executed", 18.0),
                                ]
                            ),
                        ),
                        (
                            "glint_score",
                            OrderedDict(
                                [
                                    ("abort", 0.85),
                                    ("observed", 0.4),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 113),
                                    ("combined_jitter_us", 45),
                                    ("ratio", 2.51),
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
            ("name", "grasp_smear_vial"),
            ("parameters", params),
            (
                "gate_effect",
                "ACCEPT: executed identical to proposed. 18 N grasp under 45 N cap.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT seated the smear vial at 18.4 N. Glint 0.40 remained a lighting "
                "artifact. Proposed trim was already legal.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("vial", "seated; wrist peak 18.4 N < 45 N"),
                        ("camera", "glint 0.40 unused as abort"),
                        ("cell", "dose unchanged this cycle"),
                        ("mission", "grasp complete"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Pb-glass specular from lamp pose 2 produced glint 0.40 without a force step; FT-first discarded it.",
                    "Delayed (survey_s=480): 8 min smear recount under a second lamp pose; not a safety inflection.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "ft.wrist.N (3.088 ms, 18.0 N)"),
                        ("loser", "cam.glint.false (3.201 ms, 0.40)"),
                        ("margin_us", 113),
                        (
                            "counterfactual_if_reversed",
                            "Glint-first by < 113 us inside the 250 us window would have REJECTED "
                            "a legal 18 N grasp. Order selected ACCEPT of an already-legal proposal.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 4188),
            (
                "reward_inflection_note",
                "Task and safety step up at the ACCEPT gate (4.188 ms, tick 4) as the legal "
                "grasp locks in over a glint abort.",
            ),
        ]
    )
    ras = raster_core(
        21,
        64,
        35,
        47,
        routing(
            "thalamic-relay.wrist-force",
            "spikenaut.policy.grasp-go",
            [
                ("relay.ft.wrist", "policy.force_go", 0.68),
                ("relay.cam.glint", "policy.glint_hold", 0.26),
                ("relay.dose.gamma", "policy.force_go", 0.10),
            ],
            "histamine",
            0.07,
            "force_cap_stdp; HA at FT win (3.088 ms) tags force_go over glint_hold",
        ),
        excerpt,
        extra=OrderedDict(
            [
                ("excerpt_source", "kernelized_events"),
                ("sim_scope", "none"),
            ]
        ),
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.25),
            ("decision", "ACCEPT"),
            (
                "populations",
                [
                    pop("force_go", 40, 0.50, 320.0, 3),
                    pop("glint_hold", 40, 0.50, 80.0, 1),
                    pop("dose_ctx", 24, 0.70),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r16-100"),
            (
                "title",
                "Orpiment Cell OC-4 / Amber-Arm 2: wrist FT 18 N beats Pb-glass glint 0.40; "
                "correct ACCEPT of an already-legal grasp",
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
                    "Correct ACCEPT. Wrist 18 N < 45 N cap; glint is lighting, not load. "
                    "total +1.12 = 0.42 + 0.32 + 0.18 + 0.12 + 0.08.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "hotcell-telemanip",
                    [
                        "accept",
                        "hotcell",
                        "force-vs-glint",
                        "simulated-lighting",
                        "simulated",
                    ],
                    "Teaches that a Pb-glass glint can lose to wrist FT inside a 250 us window; "
                    "reversing 113 us would have REJECTED an already-legal 18 N grasp.",
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
            if str(k).lower() in THOUGHT_KEYS or str(k).lower() in {
                "chain_of_thought",
                "hidden_reasoning",
            }:
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
    banned = {
        "warehouse-amr",
        "aerial-swarm",
        "underwater-rov",
        "grid-inspection",
        "humanoid-locomotion",
    }
    if set(domains) & banned:
        issues.append(f"banned domains {set(domains) & banned}")
    wrong = [
        r
        for r in records
        if r["safety_decision"].get("correctness") == "incorrect"
        or r["meta"].get("supervisor_error_type")
    ]
    if len(wrong) != 1 or wrong[0]["id"] != "ttf-r16-097":
        issues.append(f"wrong-gate set {[w['id'] for w in wrong]}")
    if any(r["state"]["sim_or_real"] == "real" for r in records):
        issues.append("sim_or_real=real")
    hil = [r["id"] for r in records if r["state"]["sim_or_real"] == "hil"]
    if hil != ["ttf-r16-098"]:
        issues.append(f"hil set {hil}")
    decisions = [r["safety_decision"]["decision"] for r in records]
    if decisions.count("ACCEPT") != 1 or decisions.count("MODIFY") != 2 or decisions.count("REJECT") != 2:
        issues.append(f"gate mix {decisions}")
    for rec in records:
        blob = json.dumps(rec)
        if "training_ready" in blob:
            issues.append(f"{rec['id']} training_ready present")
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
        if rec["id"] == "ttf-r16-096":
            if rec["raster"].get("excerpt_source") != "independent_lif":
                issues.append("096 missing independent_lif")
            if rec["future_outcome"]["reward_inflection_t_us"] > rec["raster"]["window_ms"] * 1000:
                issues.append("096 inflection outside window")
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
        if rec["meta"]["round"] != 16:
            issues.append(f"{rec['id']} meta.round")
        if rec["meta"]["rights"]["intended_use"] != "research_only":
            issues.append(f"{rec['id']} rights")
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
        exec_p = rec["executed_action"]["parameters"]
        prop_p = rec["proposed_action"]["parameters"]
        if rec["safety_decision"]["decision"] == "ACCEPT" and exec_p != prop_p:
            issues.append(f"{rec['id']} ACCEPT params differ")
        if rec["id"] == "ttf-r16-096" and rec["reward_components"]["total"] >= 0:
            issues.append("096 partnered-neg total not negative")
        dw_s = rec["gate_snn"]["decision_window_ms"] / 1000.0
        for popu in rec["gate_snn"]["populations"]:
            if "mean_rate_hz" in popu:
                exp = round(popu["neurons"] * popu["mean_rate_hz"] * dw_s)
                if abs(popu["spikes"] - exp) > 1:
                    issues.append(
                        f"{rec['id']} gate_snn {popu['name']} spikes {popu['spikes']} vs {exp}"
                    )
    return issues, jmax


NOTES = """# Thalamic Trajectory Factory — NOTES-r16

- Factory: `thalamic-trajectory-factory`
- Run label: `2026-09-02-final-heavy`
- Generator: `grok-4.6`
- Channel: SuperGrok Heavy consumer chat (RM-793 research-only)
- Quota: 5
- IDs: `ttf-r16-096` … `ttf-r16-100`
- Domains this batch: `agritech-combine`, `semiconductor-fab`, `fusion-divertor`, `rail-hump-yard`, `hotcell-telemanip`

These five domain slugs sit outside the r12 set (`warehouse-amr`, `aerial-swarm`, `underwater-rov`, `grid-inspection`, `humanoid-locomotion`) and outside r13/r14 sit-ins. All five plants are invented. Do not restack r12–r15 plants (Marrow-Dock, Vesper-Lattice, Brine-Well, Saddle-Arc, Ashlar-Gait, Nacre-Well, Quern-Forge, Tinder-Box, Whimbrel-Stack, Cinder-Loft, Oolite-Span, Fathom-Lock, Loess-Stride, Swage-Holt, Slag-Siding, Kiln-Spur).

## Batch map

| id | domain | decision | correctness | sim_or_real | total | edge |
|----|--------|----------|-------------|-------------|-------|------|
| ttf-r16-096 | agritech-combine | MODIFY | correct | designed | **−0.46** | process-correct header-gap clamp; knife shear inside 38 ms raster; independent LIF |
| ttf-r16-097 | semiconductor-fab | REJECT | **incorrect (wrong-reject)** | designed | −0.55 | wafer Z 12 nm < 30 nm cap; supervisor treats reticle 40 nm as wafer excursion |
| ttf-r16-098 | fusion-divertor | REJECT | correct | hil | +0.76 | Langmuir 3.80 MW/m² beats IR 1.10; hold cassette crawl |
| ttf-r16-099 | rail-hump-yard | MODIFY | correct | designed | +0.88 | coupler radar 0.62 m vs track-circuit false-clear; clamp exit speed |
| ttf-r16-100 | hotcell-telemanip | ACCEPT | correct | simulated | +1.12 | wrist 18 N vs Pb-glass glint 0.40; proposed grasp already legal |

Gate mix: 1 ACCEPT, 2 MODIFY, 1 correct REJECT, 1 incorrect REJECT (wrong-reject). Provenance: designed×3, simulated×1, hil×1 (Gyre-Tokamak cassette pad). Jaccard on `state.description` reported by the generator.

## Wrong-reject

**ttf-r16-097** is the mandated incorrect gate (`safety_decision.correctness=incorrect`, `meta.supervisor_error_type=wrong-reject`). This is not r12 induced-kV, not r13 J2-vs-J6, not r14 wet-MAD class mixup.

Flint-Mask Hall 7 / SM-41 reads wafer interferometer Z **12 nm** against a **30 nm** wafer-stage cap. Reticle encoder X is **40 nm** on a different stage whose cap is **80 nm**. Sidecar arithmetic `12 < 30` is true. A weak supervisor treats “the stage loop” as one axis, REJECTs the 80 mm/s slew, and holds wafer. Convictable without lithography physics: `evidence.wafer_z_nm < evidence.wafer_cap_nm`, `wafer_stage_id == wafer`, `reticle_stage_id == reticle`, `executed_action` sets `slew_mm_s=0` without a wafer over-cap, `raster.routing.table` sends `relay.enc.reticle` → `policy.wafer_hold` (weight 0.73) with no positive weight to `policy.slew_go`, and `gate_snn` has `wafer_hold` above threshold while `slew_go` is not. Recovery: ACCEPT the 80 mm/s slew; leave reticle 40 nm to its own 80 nm cap. Cost: missed 28 min dry slot (`missed_window_s=1680`).

## Partnered-negative in-window (096)

**ttf-r16-096** is the partnered negative: process-correct MODIFY (header gap held 17 mm < 20 mm cap) while the world still charges. Safety −0.58 prices the knife-11 shear at **18.400 ms**; `task_progress` stays +0.34 because the clamp completed. Inflection `t_us=18400` is tick 5 and is **inside** the 38 ms raster (`18400 ≤ 38000`). Named un-netted loss: 22 min knife swap (`abort_s=1320`). Not folded into process heads.

Independent LIF (the one labeled sidecar sim): `state.sim_or_real` remains `designed`. `raster.excerpt_source=independent_lif`, `raster.sim_scope=sidecar_only`, `raster.lif` seed 16096, stim `[17500, 20500]`. Excerpt is membrane crossings (`lif.clamp` early vs `lif.shear` 17.5–20.5 ms), not a 1:1 remap of `spike_events`. `meta.tags` include `independent-lif-raster` and `sidecar-sim-only`.

## Reward formula and tick reconciliation

Declared aggregation on every record:

`total = task_progress + safety + efficiency + coherence + exploration`

Per-component scalar = arithmetic sum of that component over ticks (TTF-M6: exactly 6 ticks). Tick 6 is bound to a published sidecar (`abort_s`, `missed_window_s`, `yard_reseq_s`, `survey_s`) and is strictly after the raster window. Inflection `t_us` is an actual tick.

| id | ticks | tp | saf | eff | coh | exp | total | inflection tick |
|----|-------|----|-----|-----|-----|-----|-------|-----------------|
| 096 | 6 | +0.34 | −0.58 | −0.18 | +0.02 | −0.06 | −0.46 | 5 (18400) |
| 097 | 6 | −0.18 | −0.08 | −0.20 | −0.12 | +0.03 | −0.55 | 4 (4920) |
| 098 | 6 | +0.08 | +0.38 | +0.12 | +0.10 | +0.08 | +0.76 | 4 (7288) |
| 099 | 6 | +0.32 | +0.28 | +0.12 | +0.10 | +0.06 | +0.88 | 4 (7500) |
| 100 | 6 | +0.42 | +0.32 | +0.18 | +0.12 | +0.08 | +1.12 | 4 (4188) |

## Raster / energy (Loihi-2 4-core, 23 pJ/spike)

| id | domain | n | rate Hz | window_ms | spikes | energy_pJ | energy_uJ |
|----|--------|---|---------|-----------|--------|-----------|-----------|
| 096 | agritech-combine | 72 | 30 | 38 | 82 | 1886 | 0.001886 |
| 097 | semiconductor-fab | 96 | 40 | 26 | 100 | 2300 | 0.002300 |
| 098 | fusion-divertor | 128 | 20 | 44 | 113 | 2599 | 0.002599 |
| 099 | rail-hump-yard | 48 | 50 | 32 | 77 | 1771 | 0.001771 |
| 100 | hotcell-telemanip | 64 | 35 | 21 | 47 | 1081 | 0.001081 |

`spikes = round(n × rate × window_s)`. Every record carries `gate_snn` whose `decision` matches the safety gate; populations that declare rate+spikes meet the same ±1 budget against `decision_window_s`. `routing.third_factor` has modulator, `tau_e_s`/`tau_e_ms` pair, and eligibility. Excerpt same-neuron gap ≥ 1000 µs; spike trains same-channel refractory ≥ 0.8 ms. Non-096 excerpts are kernelized and independent of `spike_events` times (overlap < 0.8).

## Local checks (staging, not raw)

See generator stdout: `check_jsonl` FactoryStaging, `validate_run.check_line`, `dumps_exact_json`, `raster_status`, `verify_batch_for_frontier(strict=True)`, `spike_probe.py --strict`, tick sums, refractory, Jaccard.

Never `training_ready`. Never `sim_or_real=real`. Never wrote `outputs/raw/`.

## Residual weaknesses (honest)

1. Only **one** labeled independent LIF (096). The other four excerpts are independent of `spike_events` times but are not declared population sims.
2. Wrong-ACCEPT still absent (guard).
3. Tick-6 sidecar bind is a densification of r14, not a new class.
4. Five domain slugs leave the prompt's 8-item pool; a later round that must stay inside the pool will have to rotate sit-outs instead.
5. 100 ACCEPT is an already-legal proposal confirmed by race order; a later round could pair an ACCEPT with a world charge that does not go negative.

## Next densification target

Labeled LIF on a second record, or an ISI histogram sidecar. If a later round returns to the 8-item pool, sit out the r12 five again and pick a wrong-MODIFY that is neither J2-axis nor a stage mixup (wrong-phase of a cyclic process). Wrong-ACCEPT remains structurally absent until a prompt amendment.

Novel coverage: 22.0%
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
        BATCH_PATH, "batch-r16.jsonl", staging=FactoryStaging(enabled=True)
    )
    report.append(("check_jsonl FactoryStaging", errors, warnings, kinds, nrec))
    line_errs = []
    for i, rec in enumerate(records, 1):
        errs, kind = check_line(rec, f"batch-r16.jsonl:{i}", factory_staging=True)
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
    records = [record_096(), record_097(), record_098(), record_099(), record_100()]
    issues, jmax = self_check(records)
    lines = [
        json.dumps(rec, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
        for rec in records
    ]
    BATCH_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    NOTES_PATH.write_text(NOTES, encoding="utf-8")
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
                failed = True
        elif name == "raster_status":
            if item[1]:
                failed = True
        elif name == "verify_batch_for_frontier":
            if item[3]:
                failed = True
        elif name == "validate_novel_coverage":
            if item[1]:
                failed = True
        elif name == "spike_probe":
            if item[1] != 0:
                failed = True
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
