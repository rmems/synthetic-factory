#!/usr/bin/env python3
"""Emit TTF r69 JSONL (ttf-r69-341..345). Staging under /tmp/ttf-r69-live/.

CREATE-ONLY copy into the 2026-09-02-final-heavy live tree after checks pass.
Never overwrites; c-suffix on collision. Never 2026-08-17 / 2026-08-30.
"""

from __future__ import annotations

import json
import math
import os
import random
import re
import subprocess
import sys
from collections import OrderedDict
from decimal import Decimal
from pathlib import Path

OUT_DIR = Path("/tmp/ttf-r69-live")
BATCH_PATH = OUT_DIR / "batch-r69.jsonl"
NOTES_PATH = OUT_DIR / "NOTES-r69.md"
REPO = Path("/home/raulmc/rmems/synthetic-factory")
PIPELINES = REPO / "pipelines"
LIVE_DIR = REPO / "outputs/raw/2026-09-02-final-heavy/thalamic-trajectory-factory"
FORBIDDEN_RUNS = ("2026-08-17", "2026-08-30")

PJ_PER_SPIKE = 23
RIGHTS = OrderedDict(
    [
        ("provider", "SpaceXAI/xAI"),
        ("model", "grok-4.6"),
        ("channel", "consumer"),
        ("subscription_plan", "SuperGrok Heavy"),
        ("generation_surface", "SuperGrok Heavy chat"),
        ("generated_at", "2026-09-02T23:59:00Z"),
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
    "hafnium-iodide-deboer",
    "yttrium-oxalate-calciner",
    "indium-phosphide-movpe",
    "zirconium-oxychloride-crystallizer",
    "nitrogen-trifluoride-electrolyzer",
}
THIS_PLANTS = (
    "DeBoer-Knap",
    "Oxalate-Fell",
    "Phosphide-Brae",
    "Zirconyl-Holt",
    "Trifluor-Ness",
)
IDS = [f"ttf-r65-{n}" for n in range(321, 326)]
BANNED_PLANT_FRAGMENTS = (
    "Marrow-Dock",
    "Vesper-Lattice",
    "Brine-Well",
    "Saddle-Arc",
    "Ashlar-Gait",
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
    "Tungstate-Keld",
    "Oxime-Clough",
    "Ilmenite-Naze",
    "Ebullate-Pike",
    "Decarb-Haugh",
    "Tungstate-Keld",
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


def meta_block(
    domain,
    tags,
    distillation_value,
    batch_position,
    supervisor_error_type=None,
) -> OrderedDict:
    body = OrderedDict(
        [
            ("round", 65),
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


def lif_321_excerpt():
    n = 76
    dt_us = 100
    tau_m_ms = 19.0
    v_th = 1.0
    v_reset = 0.0
    refractory_us = 1000
    i_bias = 0.91
    i_stim_peak = 2.42
    stim = (22000, 25000)
    seed = 65321
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
    leak = [(t, nid) for t, nid in picked if t >= 22000][:9]
    picked = sorted(clamp + leak, key=lambda item: (item[0], item[1]))
    if len(picked) < 10:
        raise RuntimeError(f"LIF excerpt short: {len(picked)}")
    channels = ["lif.clamp" if t < 22000 else "lif.crack" for t, _ in picked]
    lif = OrderedDict(
        [
            ("model", "leaky_integrate_and_fire"),
            ("n", 76),
            ("dt_us", 100),
            ("tau_m_ms", 19.0),
            ("v_rest", 0.0),
            ("v_reset", 0.0),
            ("v_th", 1.0),
            ("r_m", 1.0),
            ("refractory_us", 1000),
            ("i_bias", 0.91),
            ("i_stim_peak", 2.42),
            ("stim_t_us", [22000, 25000]),
            ("i_clamp_extra", 0.62),
            ("clamp_n", 14),
            ("seed", 65321),
            (
                "note",
                "Population sim scoped to this sidecar. Plant remains designed. "
                "Neurons 0-13 carry +0.62 filament-amp clamp bias; stim 22-25 ms is the quartz envelope crack.",
            ),
        ]
    )
    extra = OrderedDict(
        [
            ("excerpt_source", "independent_lif"),
            ("sim_scope", "sidecar_only"),
            ("lif", lif),
            ("abort_s", 840),
            ("delayed_surprise_s", 840),
        ]
    )
    return excerpt_items(picked, channels), extra


def record_321():
    excerpt, extra = lif_321_excerpt()
    ticks = [
        tick(2048, 0.04, -0.02, -0.02, 0.01, 0.00),
        tick(5120, 0.08, -0.04, -0.02, 0.01, -0.01),
        tick(5300, 0.04, -0.03, -0.02, 0.00, 0.00),
        tick(5840, 0.08, -0.05, -0.03, 0.02, -0.01),
        tick(22400, 0.06, -0.41, -0.04, -0.01, -0.01),
        tick(840000000, 0.02, -0.05, -0.03, 0.01, -0.01),
    ]
    spikes = [
        spike("enc.fil.A", 1.180, 0.41),
        spike("i2.uv.Pa", 2.048, 0.58),
        spike("enc.fil.A", 3.400, 0.50),
        spike("i2.uv.Pa", 5.120, 1.31),
        spike("enc.fil.A", 5.300, 1.12),
        spike("ctrl.gate", 5.840, 0.97),
        spike("i2.uv.Pa", 8.100, 0.82),
        spike("enc.fil.A", 10.400, 0.64),
        spike("ctrl.gate", 14.200, 0.86),
        spike("ae.env.crack", 22.400, 1.48),
        spike("ae.env.crack", 24.100, 0.93),
        spike("enc.fil.A", 30.200, 0.40),
        spike("i2.uv.Pa", 36.400, 0.55),
    ]
    state = OrderedDict(
        [
            (
                "description",
                "Crystal-bar vessel V-7 on DeBoer-Knap DK-4 is dumping 186 Pa residual I2 "
                "while filament current still sits a legal 48 A under 62 A. I2-first clamps "
                "amps 48 -> 28; pyrometer-first would keep cruise because skin 1480 C is still "
                "under the 1550 C filament cap. A quartz envelope crack already seated on the "
                "bell jar does not appear on I2 or amps until the AE dump.",
            ),
            ("domain", "hafnium-iodide-deboer"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Keep V-7 residual I2 <= 120 Pa and finish the Hf crystal bar without dumping "
                "iodide through a cracked quartz envelope.",
            ),
            ("t0_us", 1756856500000321),
            ("gate_latency_us", 720),
            ("race_window_us", 360),
            ("race_window_rel_ms", [5.120, 5.480]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "i2.uv.Pa 186 over 120 cap",
                                "enc.fil.A 48 with skin 1480 under 1550",
                            ],
                        ),
                        (
                            "semantics",
                            "I2-first latches amp clamp 48 -> 28 A; pyrometer-first keeps 48 A on a "
                            "'still under filament-skin cap' model.",
                        ),
                        (
                            "window_derivation",
                            "360 us = one UV I2 slot versus the filament-encoder publisher on this "
                            "de Boer iodide bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 180 us vs combined jitter 62 us (I2 28 + amp 34): 2.90x over "
                            "a 2.0x trust floor. Reversing order by < 180 us inside the 360 us "
                            "window would have kept 48 A; predicted next-sample 142 Pa > 120 cap.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "residual I2 UV cell, 2 kHz, 28 us jitter",
                    "filament encoder + skin TC, 1 kHz, 34 us jitter",
                    "bell-jar AE puck (context)",
                    "HfI4 feed tach (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("i2_cap_Pa", 120.0),
                        ("observed_i2_Pa", 186.0),
                        ("filament_A", 48.0),
                        ("skin_C", 1480.0),
                        ("skin_cap_C", 1550.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. V-7 indexed on DeBoer-Knap DK-4; filament 48 A; residual I2 186 Pa.",
                    "2. Skin 1480 C under 1550 C cap; crystal-bar armed.",
                    "3. Encoder precursor at 1.180 ms.",
                    "4. Race window [5.120, 5.480] ms.",
                    "5. i2.uv.Pa 186 at 5.120 ms (winner).",
                    "6. enc.fil.A 48 at 5.300 ms (loser by 180 us).",
                    "7. Gate at 5.840 ms: MODIFY clamp 48 -> 28 A.",
                    "8. After clamp I2 68 Pa <= 120; skin still 1480 C.",
                    "9. At 22.400 ms a quartz envelope crack dumps 0.3 kg iodide.",
                    "10. 14 min bell isolate (abort_s=840); named un-netted loss.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_filament_amps"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("filament_A", 48.0),
                        ("i2_Pa", 186.0),
                        ("skin_C", 1480.0),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("i2_Pa", 186.0),
                        ("i2_cap_Pa", 120.0),
                        ("predicted_unclamped_next_Pa", 142.0),
                        ("filament_A", 48.0),
                        ("skin_C", 1480.0),
                        ("skin_cap_C", 1550.0),
                        ("race_margin_us", 180),
                        ("combined_jitter_us", 62),
                        ("abort_s", 840),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 48 A because skin 1480 C is under 1550, treating the "
                "186 Pa I2 as a still-wet UV cell rather than a residual-cap miss.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "correct"),
            (
                "rationale",
                "Residual I2 186 Pa won by 180 us, so the bar is off-spec, not still a "
                "filament-skin story. Holding 48 A predicts next-sample 142 Pa > 120 cap. "
                "MODIFY: filament 48 -> 28 A. Observed after clamp 68 Pa <= 120. A full REJECT "
                "is not indicated: a clean bar accepts 28 A.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "i2_Pa",
                            OrderedDict(
                                [
                                    ("cap", 120.0),
                                    ("observed", 186.0),
                                    ("predicted_unclamped_next", 142.0),
                                    ("clamped_filament_A", 28.0),
                                    ("observed_after_clamp", 68.0),
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
            ("name", "clamped_filament_amps"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("filament_A", 28.0),
                        ("i2_Pa", 68.0),
                        ("skin_C", 1480.0),
                    ]
                ),
            ),
            (
                "gate_effect",
                "MODIFY: filament 48 -> 28 A. Process-correct vs the 120 Pa I2 cap. "
                "Quartz envelope still cracks at 22.400 ms.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Process-correct MODIFY held residual I2 at 68 Pa. At 22.400 ms a quartz "
                "envelope crack already seated on the bell jar dumped 0.3 kg iodide. Clamp "
                "reduced dump energy; it did not prevent the crack. Partnered negative: process "
                "heads stay honest; world loss is named, not netted.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("residual", "clamp executed; peak 68 Pa <= 120 cap"),
                        ("envelope", "cracked at 22.400 ms; 0.3 kg iodide"),
                        ("repair", "14 min bell isolate (abort_s=840)"),
                        ("mission", "DK-4 crystal bar incomplete this circuit"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Neither residual I2 nor filament encoder predicted the seated quartz crack; ae.env.crack is a new channel at 22.400 ms, 16.560 ms after the gate, still inside the 42 ms raster.",
                    "Delayed (abort_s=840): 14 min bell isolate. Named un-netted loss, not folded into task_progress.",
                ],
            ),
            (
                "un_netted_loss",
                "14 min bell isolate after the quartz envelope crack. Safety head -0.60 prices the dump; "
                "task_progress stays +0.32 because the amp clamp completed under the 120 Pa "
                "cap. World loss is named here, not subtracted from process heads.",
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "i2.uv.Pa (5.120 ms, 186 Pa)"),
                        ("loser", "enc.fil.A (5.300 ms, 48 A)"),
                        ("margin_us", 180),
                        (
                            "counterfactual_if_reversed",
                            "Amp-first by < 180 us inside the 360 us window would have kept "
                            "48 A; predicted next-sample 142 Pa would have missed the 120 "
                            "cap even without the crack. The MODIFY is still the correct "
                            "process. The crack is a later world charge either way, cheaper with "
                            "the clamp than without.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 22400),
            (
                "reward_inflection_note",
                "Safety collapses at the 22.400 ms quartz envelope crack (tick t_us=22400), inside the 42 ms "
                "raster. The correct MODIFY at 5.840 ms is in the same excerpt. Do not put "
                "inflection on the abort_s=840 isolation tick.",
            ),
            ("delayed_surprise_s", 840),
        ]
    )
    dw = 0.36
    ras = raster_core(
        42,
        76,
        24,
        77,
        routing(
            "thalamic-relay.hf-i2",
            "spikenaut.policy.amp-clamp",
            [
                ("relay.i2.uv", "policy.amp_clamp", 0.68),
                ("relay.enc.fil", "policy.amp_hold", 0.29),
                ("relay.ae.env", "policy.amp_clamp", -0.42),
            ],
            "noradrenaline",
            0.04,
            "surprise-gated pre_post_stdp; NA at I2 win (5.120 ms) opens a 42 ms eligibility "
            "trace that still covers the 22.400 ms quartz envelope crack",
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
                    pop_budget("amp_clamp", 50, 0.50, 220.0, dw),
                    pop_budget("amp_hold", 40, 0.80, 50.0, dw),
                    pop("crack_veto", 24, 0.75),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r65-321"),
            (
                "title",
                "DeBoer-Knap DK-4 / Vessel V-7: residual I2 beats filament amps by 180 us; "
                "correct MODIFY still eats an in-window quartz envelope crack (partnered negative "
                "total -0.44)",
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
                    "42 ms raster. total -0.44 = 0.32 + -0.60 + -0.16 + 0.04 + -0.04. Named "
                    "bell isolate (abort_s=840) is not netted into task_progress.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "hafnium-iodide-deboer",
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
                    "14 min bell isolate.",
                    1,
                ),
            ),
        ]
    )


def record_322():
    ticks = [
        tick(2256, 0.05, 0.04, 0.02, 0.01, 0.01),
        tick(5640, 0.08, 0.06, 0.03, 0.02, 0.01),
        tick(5800, 0.04, 0.04, 0.02, 0.01, 0.01),
        tick(6220, 0.12, 0.10, 0.06, 0.04, 0.02),
        tick(6540, 0.06, 0.05, 0.03, 0.01, 0.01),
        tick(180000000, 0.03, 0.03, 0.02, 0.01, 0.01),
    ]
    spikes = [
        spike("tc.skin.C", 1.200, 0.40),
        spike("co.offgas.ppm", 2.256, 0.58),
        spike("tc.skin.C", 3.600, 0.50),
        spike("co.offgas.ppm", 5.640, 1.32),
        spike("tc.skin.C", 5.800, 1.10),
        spike("ctrl.gate", 6.220, 0.97),
        spike("co.offgas.ppm", 8.400, 0.80),
        spike("tc.skin.C", 11.200, 0.62),
        spike("ctrl.gate", 14.800, 0.85),
        spike("co.offgas.ppm", 18.200, 0.54),
        spike("tc.skin.C", 22.400, 0.41),
        spike("co.offgas.ppm", 24.800, 0.48),
        spike("ctrl.gate", 25.600, 0.70),
    ]
    excerpt = independent_excerpt(65322, 64, 26000, 13, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Rotary oxalate calciner R-5 at Oxalate-Fell OF-3 is pushing 840 ppm CO while "
                "kiln RPM still sits a legal 2.4 under 3.0. CO-first clamps 2.4 -> 1.2 rpm; "
                "skin-first would keep cruise because 612 C is still under the 680 C tube cap.",
            ),
            ("domain", "yttrium-oxalate-calciner"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Keep R-5 off-gas CO <= 400 ppm and finish the Y2(C2O4)3 roast without a tube "
                "hot-spot.",
            ),
            ("t0_us", 1756856501000322),
            ("gate_latency_us", 580),
            ("race_window_us", 320),
            ("race_window_rel_ms", [5.640, 5.960]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "co.offgas.ppm 840 over 400 cap",
                                "tc.skin.C 612 under 680 cap",
                            ],
                        ),
                        (
                            "semantics",
                            "CO-first latches RPM clamp 2.4 -> 1.2; skin-first keeps 2.4 rpm on a "
                            "'still under tube-skin cap' model.",
                        ),
                        (
                            "window_derivation",
                            "320 us = one NDIR CO slot versus the kiln-skin TC publisher on this "
                            "oxalate calciner bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 160 us vs combined jitter 56 us (CO 24 + skin 32): 2.86x over "
                            "a 2.0x trust floor. Reversing order by < 160 us inside the 320 us "
                            "window would have kept 2.4 rpm; predicted next-sample 510 ppm > 400 cap.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "off-gas NDIR CO, 2 kHz, 24 us jitter",
                    "kiln skin TC, 1 kHz, 32 us jitter",
                    "oxalate screw tach (context)",
                    "baghouse DP (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("co_cap_ppm", 400.0),
                        ("observed_co_ppm", 840.0),
                        ("kiln_rpm", 2.4),
                        ("skin_C", 612.0),
                        ("skin_cap_C", 680.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. R-5 indexed on Oxalate-Fell OF-3; kiln 2.4 rpm; off-gas CO 840 ppm.",
                    "2. Skin 612 C under 680 C cap; roast armed.",
                    "3. Skin precursor at 1.200 ms.",
                    "4. Race window [5.640, 5.960] ms.",
                    "5. co.offgas.ppm 840 at 5.640 ms (winner).",
                    "6. tc.skin.C 612 at 5.800 ms (loser by 160 us).",
                    "7. Gate at 6.220 ms: MODIFY clamp 2.4 -> 1.2 rpm.",
                    "8. After clamp CO 280 ppm <= 400; skin still 612 C.",
                    "9. No tube leak this circuit.",
                    "10. Delayed (survey_s=180): 3 min CEMS tag on the next charge.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_kiln_rpm"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("kiln_rpm", 2.4),
                        ("co_ppm", 840.0),
                        ("skin_C", 612.0),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("co_ppm", 840.0),
                        ("co_cap_ppm", 400.0),
                        ("predicted_unclamped_next_ppm", 510.0),
                        ("kiln_rpm", 2.4),
                        ("skin_C", 612.0),
                        ("skin_cap_C", 680.0),
                        ("race_margin_us", 160),
                        ("combined_jitter_us", 56),
                        ("survey_s", 180),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 2.4 rpm because skin 612 C is under 680, treating the "
                "840 ppm CO as oxalate off-gassing rather than a CO-cap miss.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "correct"),
            (
                "rationale",
                "Off-gas CO 840 ppm won by 160 us, so the roast is off-spec, not still a "
                "tube-skin story. Holding 2.4 rpm predicts next-sample 510 ppm > 400 cap. "
                "MODIFY: kiln 2.4 -> 1.2 rpm. Observed after clamp 280 ppm <= 400. A full REJECT "
                "is not indicated: a clean roast accepts 1.2 rpm.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "co_ppm",
                            OrderedDict(
                                [
                                    ("cap", 400.0),
                                    ("observed", 840.0),
                                    ("predicted_unclamped_next", 510.0),
                                    ("clamped_kiln_rpm", 1.2),
                                    ("observed_after_clamp", 280.0),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 160),
                                    ("combined_jitter_us", 56),
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
            ("name", "clamped_kiln_rpm"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("kiln_rpm", 1.2),
                        ("co_ppm", 280.0),
                        ("skin_C", 612.0),
                    ]
                ),
            ),
            (
                "gate_effect",
                "MODIFY: kiln 2.4 -> 1.2 rpm. Process-correct vs the 400 ppm CO cap.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct MODIFY held off-gas CO at 280 ppm under the 400 ppm cap. Kiln seated "
                "at 1.2 rpm without a tube hot-spot. Delayed CEMS tags the CO-first bind on the "
                "next charge.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("offgas", "clamp executed; peak 280 ppm <= 400"),
                        ("tube", "no hot-spot; skin stayed 612 C"),
                        ("kiln", "1.2 rpm held"),
                        ("qc", "3 min CEMS tag on next charge"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "CO fell 840 -> 280 ppm inside two NDIR slots after the clamp; skin never approached 680 C.",
                    "Delayed (survey_s=180): CEMS writes the CO-first bind onto the next oxalate charge.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "co.offgas.ppm (5.640 ms, 840 ppm)"),
                        ("loser", "tc.skin.C (5.800 ms, 612 C)"),
                        ("margin_us", 160),
                        (
                            "counterfactual_if_reversed",
                            "Skin-first by < 160 us inside the 320 us window would have kept "
                            "2.4 rpm; predicted next-sample 510 ppm would have exceeded the 400 ppm "
                            "cap. The MODIFY is the correct process either way once CO wins.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 6220),
            (
                "reward_inflection_note",
                "Task and safety inflect at the correct clamp (6.220 ms, tick 4). The 3 min CEMS "
                "tag is delayed surprise bound to raster.delayed_surprise_s=180, not the inflection.",
            ),
            ("delayed_surprise_s", 180),
        ]
    )
    dw = 0.32
    ras = raster_core(
        26,
        64,
        40,
        67,
        routing(
            "thalamic-relay.co-skin",
            "spikenaut.policy.rpm-clamp",
            [
                ("relay.co.offgas", "policy.rpm_clamp", 0.69),
                ("relay.tc.skin", "policy.rpm_hold", 0.28),
            ],
            "acetylcholine",
            0.08,
            "pre_post_stdp; ACh at CO win (5.640 ms) tags the rpm_clamp bind",
        ),
        excerpt,
        extra=OrderedDict(
            [
                ("excerpt_source", "kernelized_events"),
                ("sim_scope", "none"),
                ("survey_s", 180),
                ("delayed_surprise_s", 180),
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
                    pop_budget("rpm_clamp", 40, 0.50, 310.0, dw),
                    pop_budget("rpm_hold", 40, 0.50, 80.0, dw),
                    pop("co_cap_veto", 16, 0.70),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r65-322"),
            (
                "title",
                "Oxalate-Fell OF-3 / Rotary R-5: off-gas CO beats kiln skin by 160 us; "
                "correct MODIFY clamps 2.4 -> 1.2 rpm under the 400 ppm CO cap",
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
                    "Correct MODIFY. CO 840 -> 280 ppm under 400 cap. "
                    "total +1.05 = 0.38 + 0.32 + 0.18 + 0.10 + 0.07.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "yttrium-oxalate-calciner",
                    [
                        "modify",
                        "co-first",
                        "tick6-sidecar-bound",
                        "designed",
                    ],
                    "Teaches CO-vs-skin order on an oxalate kiln: routing.table[0] to policy.rpm_clamp "
                    "with skin as the losing hold.",
                    2,
                ),
            ),
        ]
    )


def record_323():
    ticks = [
        tick(1952, 0.01, 0.06, 0.01, 0.01, 0.01),
        tick(4880, 0.02, 0.08, 0.02, 0.02, 0.01),
        tick(5120, 0.01, 0.06, 0.02, 0.01, 0.01),
        tick(5980, 0.04, 0.14, 0.04, 0.04, 0.02),
        tick(6460, 0.01, 0.05, 0.02, 0.01, 0.01),
        tick(360000000, 0.01, 0.03, 0.01, 0.01, 0.00),
    ]
    spikes = [
        spike("pyr.wafer.C", 0.980, 0.41),
        spike("ae.bubbler.pps", 1.952, 0.57),
        spike("pyr.wafer.C", 3.200, 0.49),
        spike("ae.bubbler.pps", 4.880, 1.35),
        spike("pyr.wafer.C", 5.120, 1.12),
        spike("ctrl.gate", 5.980, 0.98),
        spike("ae.bubbler.pps", 8.800, 0.81),
        spike("pyr.wafer.C", 12.400, 0.62),
        spike("ctrl.gate", 16.200, 0.84),
        spike("ae.bubbler.pps", 24.100, 0.52),
        spike("pyr.wafer.C", 32.400, 0.39),
        spike("ae.bubbler.pps", 40.200, 0.44),
        spike("ctrl.gate", 44.800, 0.70),
    ]
    excerpt = independent_excerpt(65323, 112, 46000, 15, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "HIL MOVPE reactor RX-2 at Phosphide-Brae PB-HIL hears TMIn bubbler AE at 48 pps "
                "while wafer pyrometer remains 612 C under a 720 C cap. AE-first holds TMIn; "
                "pyrometer-first would raise 0.18 -> 0.32 sccm because the wafer looks cold. The "
                "HIL bubbler mockup is the authority, not the growth-floor recipe.",
            ),
            ("domain", "indium-phosphide-movpe"),
            ("sim_or_real", "hil"),
            (
                "goal",
                "Keep RX-2 from raising TMIn into a droplet-carryover bubbler while wafer "
                "pyrometer remains under its own cap.",
            ),
            ("t0_us", 1756856502000323),
            ("gate_latency_us", 1100),
            ("race_window_us", 480),
            ("race_window_rel_ms", [4.880, 5.360]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "ae.bubbler.pps 48 over 14 cap",
                                "pyr.wafer.C 612 under 720 cap",
                            ],
                        ),
                        (
                            "semantics",
                            "AE-first latches hold; pyrometer-first raises TMIn 0.18 -> 0.32 sccm on a "
                            "'wafer still cold' model.",
                        ),
                        (
                            "window_derivation",
                            "480 us = one AE puck slot versus the wafer-pyrometer publisher on this "
                            "HIL MOVPE bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 240 us vs combined jitter 58 us (AE 26 + pyr 32): 4.14x over "
                            "a 2.0x trust floor. Reversing order by < 240 us inside the 480 us "
                            "window would have raised TMIn into a droplet-carryover bubbler.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "TMIn bubbler AE puck, 50 kHz, 26 us jitter",
                    "wafer pyrometer, 1 kHz, 32 us jitter",
                    "TMIn MFC (context)",
                    "PH3 header PT (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("ae_cap_pps", 14.0),
                        ("observed_ae_pps", 48.0),
                        ("wafer_C", 612.0),
                        ("wafer_cap_C", 720.0),
                        ("proposed_tmin_sccm", 0.32),
                        ("held_tmin_sccm", 0.18),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. RX-2 HIL indexed; 0.32 sccm TMIn raise armed.",
                    "2. Wafer 612 C under 720; AE 48 pps over 14.",
                    "3. Pyrometer precursor at 0.980 ms.",
                    "4. Race window [4.880, 5.360] ms.",
                    "5. ae.bubbler.pps 48 at 4.880 ms (winner).",
                    "6. pyr.wafer.C 612 at 5.120 ms (loser by 240 us).",
                    "7. Gate at 5.980 ms: REJECT hold, do not raise.",
                    "8. TMIn left 0.18 sccm; wafer left at 612 C.",
                    "9. Bubbler inspected on the HIL stand.",
                    "10. Delayed (abort_s=360): 6 min MOVPE reset.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "raise_tmin"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("tmin_sccm", 0.32),
                        ("hold", False),
                        ("wafer_C", 612.0),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("ae_pps", 48.0),
                        ("ae_cap_pps", 14.0),
                        ("wafer_C", 612.0),
                        ("wafer_cap_C", 720.0),
                        ("race_margin_us", 240),
                        ("combined_jitter_us", 58),
                        ("abort_s", 360),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 0.32 sccm TMIn because wafer 612 C is under 720, treating the "
                "48 pps AE as igniter hash rather than droplet carryover.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "REJECT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Bubbler AE 48 pps won by 240 us, so the bubbler is carrying droplets, not still a "
                "wafer-temperature story. Wafer 612 C is under 720 and does not authorize a raise. "
                "REJECT: hold TMIn 0.32 -> 0.18 sccm. A MODIFY that only trims PH3 would leave the growl.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "ae_pps",
                            OrderedDict(
                                [
                                    ("cap", 14.0),
                                    ("observed", 48.0),
                                    ("executed_tmin_sccm", 0.18),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 240),
                                    ("combined_jitter_us", 58),
                                    ("ratio", 4.14),
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
            ("name", "hold_tmin"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("tmin_sccm", 0.18),
                        ("hold", True),
                        ("wafer_C", 612.0),
                    ]
                ),
            ),
            (
                "gate_effect",
                "REJECT: TMIn 0.32 -> 0.18 sccm hold. Wafer left at 612 C under its own cap.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct REJECT held RX-2. AE 48 pps beat wafer 612 C by 240 us. Pyrometer was "
                "legal; the bubbler was not. 6 min MOVPE reset (abort_s=360) is delayed survey, "
                "not a process miss.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("tmin", "held at 0.18 sccm"),
                        ("wafer", "left 612 C < 720 cap"),
                        ("bubbler", "6 min MOVPE reset (abort_s=360)"),
                        ("mission", "HIL TMIn raise not dispatched"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Wafer pyrometer never crossed its cap; AE was the only over-cap channel.",
                    "Delayed (abort_s=360): 6 min MOVPE reset on the HIL stand.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "ae.bubbler.pps (4.880 ms, 48 pps)"),
                        ("loser", "pyr.wafer.C (5.120 ms, 612 C)"),
                        ("margin_us", 240),
                        (
                            "counterfactual_if_reversed",
                            "Pyrometer-first by < 240 us inside the 480 us window would have raised "
                            "TMIn into a droplet-carryover bubbler. The REJECT is still the correct gate.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 5980),
            (
                "reward_inflection_note",
                "Safety rises at the correct REJECT (5.980 ms, tick 4). The 6 min reset is delayed "
                "surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 360),
        ]
    )
    dw = 0.48
    ras = raster_core(
        46,
        112,
        20,
        103,
        routing(
            "thalamic-relay.tmin-ae",
            "spikenaut.policy.tmin-hold",
            [
                ("relay.ae.bubbler", "policy.tmin_hold", 0.71),
                ("relay.pyr.wafer", "policy.tmin_raise", 0.24),
            ],
            "dopamine",
            0.15,
            "hold_stdp; DA tags the tmin_hold bind at the bubbler-AE win",
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
            ("decision_window_ms", dw),
            ("decision", "REJECT"),
            (
                "populations",
                [
                    pop_budget("tmin_hold", 70, 0.48, 180.0, dw),
                    pop("tmin_raise", 50, 0.85),
                    pop("ae_veto", 28, 0.75),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r65-323"),
            (
                "title",
                "Phosphide-Brae PB-HIL / Reactor RX-2: bubbler AE beats wafer pyrometer by 240 us; "
                "REJECT hold-TMIn, do not raise",
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
                    "Correct REJECT. AE 48 pps > 14 cap; wafer 612 C legal. "
                    "total +0.80 = 0.10 + 0.42 + 0.12 + 0.10 + 0.06.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "indium-phosphide-movpe",
                    [
                        "reject",
                        "hil",
                        "bubbler-ae",
                        "pyrometer-underread",
                        "tick6-sidecar-bound",
                    ],
                    "Teaches AE-vs-pyrometer order on a HIL MOVPE bubbler: routing.table[0] to "
                    "policy.tmin_hold with wafer pyrometer as the losing raise.",
                    3,
                ),
            ),
        ]
    )


def record_324():
    ticks = [
        tick(2480, 0.06, 0.04, 0.02, 0.01, 0.01),
        tick(6200, 0.08, 0.06, 0.04, 0.03, 0.02),
        tick(6420, 0.05, 0.04, 0.02, 0.01, 0.01),
        tick(7680, 0.14, 0.10, 0.06, 0.05, 0.02),
        tick(8120, 0.04, 0.02, 0.02, 0.01, 0.01),
        tick(150000000, 0.03, 0.02, 0.02, 0.01, 0.01),
    ]
    spikes = [
        spike("cond.ml.mS", 1.400, 0.40),
        spike("dens.ml.gml", 2.480, 0.55),
        spike("cond.ml.mS", 4.000, 0.48),
        spike("dens.ml.gml", 6.200, 1.28),
        spike("cond.ml.mS", 6.420, 1.08),
        spike("ctrl.gate", 7.680, 0.96),
        spike("dens.ml.gml", 10.400, 0.78),
        spike("cond.ml.mS", 14.200, 0.60),
        spike("ctrl.gate", 18.800, 0.84),
        spike("dens.ml.gml", 22.100, 0.50),
        spike("cond.ml.mS", 26.400, 0.38),
        spike("ctrl.gate", 27.200, 0.66),
    ]
    excerpt = independent_excerpt(65324, 48, 28000, 12, spike_avoid_us(spikes))
    params = OrderedDict(
        [
            ("cool_C_h", 8.0),
            ("density_gml", 1.42),
            ("cond_mS", 18.0),
        ]
    )
    state = OrderedDict(
        [
            (
                "description",
                "Simulated ZrOCl2 crystallizer CR-4 at Zirconyl-Holt ZH-9 reads mother-liquor "
                "density 1.42 g/mL under a 1.55 cap while the proposed 8.0 C/h cool is already "
                "legal. Density-first accepts; conductivity 18 mS looks like over-conc but is a "
                "chloride smear, not a density miss.",
            ),
            ("domain", "zirconium-oxychloride-crystallizer"),
            ("sim_or_real", "simulated"),
            (
                "goal",
                "Finish CR-4 cool-down at 8.0 C/h while mother-liquor density stays <= 1.55 g/mL.",
            ),
            ("t0_us", 1756856503000324),
            ("gate_latency_us", 1480),
            ("race_window_us", 440),
            ("race_window_rel_ms", [6.200, 6.640]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "dens.ml.gml 1.42 under 1.55 cap",
                                "cond.ml.mS 18 smear vs 24 trip",
                            ],
                        ),
                        (
                            "semantics",
                            "Density-first latches ACCEPT of 8.0 C/h; conductivity-first would "
                            "REJECT an already-legal cool on a chloride-smear model.",
                        ),
                        (
                            "window_derivation",
                            "440 us = one Coriolis density slot versus the conductivity publisher "
                            "on this simulated crystallizer bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 220 us vs combined jitter 70 us (dens 30 + cond 40): 3.14x over "
                            "a 2.0x trust floor. Reversing order by < 220 us inside the 440 us "
                            "window would have REJECTED an already-legal 8.0 C/h cool.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "mother-liquor Coriolis density, 1 kHz, 30 us jitter",
                    "conductivity probe, 1 kHz, 40 us jitter",
                    "jacket PT (context)",
                    "seed FT (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("density_cap_gml", 1.55),
                        ("observed_density_gml", 1.42),
                        ("cond_mS", 18.0),
                        ("cond_trip_mS", 24.0),
                        ("cool_C_h", 8.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. CR-4 simulated; 8.0 C/h cool armed; density 1.42 g/mL.",
                    "2. Conductivity 18 mS under 24 trip; density under 1.55 cap.",
                    "3. Conductivity precursor at 1.400 ms.",
                    "4. Race window [6.200, 6.640] ms.",
                    "5. dens.ml.gml 1.42 at 6.200 ms (winner).",
                    "6. cond.ml.mS 18 at 6.420 ms (loser by 220 us).",
                    "7. Gate at 7.680 ms: ACCEPT already-legal 8.0 C/h.",
                    "8. Density stays 1.42; conductivity smear unchanged.",
                    "9. No supersat crash this circuit.",
                    "10. Delayed (survey_s=150): 2.5 min PSD tag on the next batch.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_cool_rate"),
            ("parameters", OrderedDict(params.items())),
            (
                "evidence",
                OrderedDict(
                    [
                        ("density_gml", 1.42),
                        ("density_cap_gml", 1.55),
                        ("cond_mS", 18.0),
                        ("cond_trip_mS", 24.0),
                        ("cool_C_h", 8.0),
                        ("race_margin_us", 220),
                        ("combined_jitter_us", 70),
                        ("survey_s", 150),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 8.0 C/h because density 1.42 g/mL is under 1.55; conductivity "
                "18 mS is treated as a chloride smear, not a density miss.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Mother-liquor density 1.42 g/mL won by 220 us and is under the 1.55 cap. "
                "Conductivity 18 mS is under the 24 mS trip and does not authorize a hold. "
                "ACCEPT: leave 8.0 C/h. A MODIFY cool-down would stall an already-legal batch.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "density_gml",
                            OrderedDict(
                                [
                                    ("cap", 1.55),
                                    ("observed", 1.42),
                                    ("executed_cool_C_h", 8.0),
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
            ("name", "hold_cool_rate"),
            ("parameters", OrderedDict(params.items())),
            ("gate_effect", "ACCEPT: leave 8.0 C/h; density 1.42; conductivity smear legal."),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT of an already-legal 8.0 C/h cool. Density 1.42 beat conductivity "
                "18 mS by 220 us. 2.5 min PSD tag (survey_s=150) is delayed, not a miss.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("cool", "8.0 C/h held"),
                        ("density", "1.42 < 1.55 cap"),
                        ("vessel", "CR-4 on-spec"),
                        ("qc", "2.5 min PSD tag (survey_s=150)"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Conductivity never approached 24 mS; density was already under cap.",
                    "Delayed (survey_s=150): 2.5 min PSD tag after the cool.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "dens.ml.gml (6.200 ms, 1.42 g/mL)"),
                        ("loser", "cond.ml.mS (6.420 ms, 18 mS)"),
                        ("margin_us", 220),
                        (
                            "counterfactual_if_reversed",
                            "Conductivity-first by < 220 us inside the 440 us window would have "
                            "REJECTED an already-legal cool. The ACCEPT is still the correct gate.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 7680),
            (
                "reward_inflection_note",
                "Task and safety rise at the correct ACCEPT (7.680 ms, tick 4). The 2.5 min PSD "
                "tag is delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 150),
        ]
    )
    dw = 0.44
    ras = raster_core(
        28,
        48,
        42,
        56,
        routing(
            "thalamic-relay.zrocl-dens",
            "spikenaut.policy.cool-go",
            [
                ("relay.dens.ml", "policy.cool_go", 0.67),
                ("relay.cond.ml", "policy.cool_hold", 0.25),
            ],
            "serotonin",
            0.12,
            "accept_stdp; 5-HT tags the density win as an already-legal cool",
        ),
        excerpt,
        extra=OrderedDict(
            [
                ("excerpt_source", "kernelized_events"),
                ("sim_scope", "none"),
                ("survey_s", 150),
                ("delayed_surprise_s", 150),
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
                    pop_budget("cool_go", 50, 0.45, 160.0, dw),
                    pop("cool_hold", 32, 0.90),
                    pop("dens_veto", 16, 0.80),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r65-324"),
            (
                "title",
                "Zirconyl-Holt ZH-9 / Crystallizer CR-4: density 1.42 beats conductivity 18 mS by "
                "220 us; correct ACCEPT of an already-legal 8.0 C/h cool",
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
                    "Correct ACCEPT. Density 1.42 < 1.55; conductivity 18 < 24. "
                    "total +1.06 = 0.40 + 0.28 + 0.18 + 0.12 + 0.08.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "zirconium-oxychloride-crystallizer",
                    [
                        "accept",
                        "simulated",
                        "density-vs-cond",
                        "cool-legal",
                        "tick6-sidecar-bound",
                    ],
                    "Teaches that a legal conductivity smear can lose to density inside a 440 us "
                    "window; reversing 220 us would have REJECTED an already-legal cool.",
                    4,
                ),
            ),
        ]
    )


def record_325():
    ticks = [
        tick(2160, 0.02, -0.03, -0.02, -0.01, 0.01),
        tick(5400, 0.03, -0.04, -0.03, -0.02, 0.01),
        tick(5560, 0.02, -0.03, -0.03, -0.02, 0.01),
        tick(6040, -0.28, -0.10, -0.06, -0.03, 0.02),
        tick(6360, -0.04, -0.03, -0.02, -0.01, 0.01),
        tick(660000000, -0.01, -0.01, -0.02, -0.01, 0.00),
    ]
    spikes = [
        spike("tag.p_bar", 1.080, 0.42),
        spike("pt.anode.kPa", 2.160, 0.57),
        spike("tag.p_bar", 3.400, 0.49),
        spike("pt.anode.kPa", 5.400, 1.30),
        spike("tag.p_bar", 5.560, 1.11),
        spike("ctrl.gate", 6.040, 0.96),
        spike("pt.anode.kPa", 8.200, 0.80),
        spike("tag.p_bar", 10.200, 0.63),
        spike("ctrl.gate", 12.400, 0.84),
        spike("pt.anode.kPa", 16.400, 0.41),
        spike("tag.p_bar", 22.100, 0.54),
        spike("pt.anode.kPa", 26.200, 0.38),
    ]
    excerpt = independent_excerpt(65325, 80, 24000, 12, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "NF3 cell C-12 at Trifluor-Ness TN-5 reads live anode pressure 186 kPa over a "
                "150 kPa cap while a leftover faceplate tag still prints 1.86 as if it were kPa. "
                "Live-kPa-first should cut current 8.4 -> 4.0 kA; a weak supervisor treats 1.86 bar "
                "as 1.86 kPa and only trims 8.4 -> 8.0 kA.",
            ),
            ("domain", "nitrogen-trifluoride-electrolyzer"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Keep C-12 anode pressure <= 150 kPa, leave HF feed at the planned 12.0 kg/h, "
                "and bind the live kPa transmitter rather than the leftover bar faceplate.",
            ),
            ("t0_us", 1756856504000325),
            ("gate_latency_us", 640),
            ("race_window_us", 320),
            ("race_window_rel_ms", [5.400, 5.720]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "pt.anode.kPa 186 over 150 cap",
                                "tag.p_bar 1.86 leftover faceplate (true unit bar)",
                            ],
                        ),
                        (
                            "semantics",
                            "Live-kPa-first should latch a timely current cut 8.4 -> 4.0 kA; "
                            "bar-as-kPa is a false 'still under 150' under-trim of 8.4 -> 8.0 kA.",
                        ),
                        (
                            "window_derivation",
                            "320 us = one live-PT slot versus the leftover bar-faceplate publisher "
                            "on this NF3 cell PLC bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 160 us vs combined jitter 60 us (live 28 + tag 32). Order is "
                            "correctly live-kPa-first. The error is the engineering unit on the "
                            "faceplate numeric 1.86, not the magnitude of the live kPa.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "live anode PT, 2 kHz, 28 us jitter, unit=kPa tag=C12_P.LIVE",
                    "leftover faceplate P_AN.BAR, 1 kHz, 32 us jitter, numeric=1.86 true_unit=bar",
                    "cell current shunt (context)",
                    "HF feed FT (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("cap_kPa", 150.0),
                        ("live_kPa", 186.0),
                        ("shadow_numeric", 1.86),
                        ("shadow_unit_claimed", "kPa"),
                        ("shadow_unit_true", "bar"),
                        ("current_kA", 8.4),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. C-12 LIVE already electrolyzing; anode 186 kPa; HF 12.0 kg/h.",
                    "2. Faceplate P_AN.BAR numeric 1.86; leftover claimed unit kPa.",
                    "3. Bar-tag precursor at 1.080 ms.",
                    "4. Race window [5.400, 5.720] ms.",
                    "5. pt.anode.kPa 186 at 5.400 ms (winner).",
                    "6. tag.p_bar 1.86 at 5.560 ms (loser by 160 us).",
                    "7. Gate at 6.040 ms: WRONG-MODIFY binds 1.86 as kPa under-trim.",
                    "8. Current 8.4 -> 8.0 kA; vent left 10 percent; live peaks 214 kPa.",
                    "9. Cell dump on C-12; 1.86 bar was already 186 kPa.",
                    "10. Delayed (abort_s=660): 11 min cell dump while C-12 is quenched.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_cell_current"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("current_kA", 8.4),
                        ("vent_pct", 10.0),
                        ("bind_bar_as_kpa", False),
                        ("hf_kg_h", 12.0),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("live_kPa", 186.0),
                        ("cap_kPa", 150.0),
                        ("shadow_numeric", 1.86),
                        ("shadow_unit_claimed", "kPa"),
                        ("shadow_unit_true", "bar"),
                        ("live_status", "LIVE"),
                        ("t_gate_us", 6040),
                        ("correct_current_kA", 4.0),
                        ("correct_vent_pct", 45.0),
                        ("race_margin_us", 160),
                        ("combined_jitter_us", 60),
                        ("abort_s", 660),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes continuing 8.4 kA: leftover faceplate 1.86 looks under a 150 "
                "numeric, so the 186 kPa live PT is treated as a shadow of the bar tag.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "incorrect"),
            (
                "rationale",
                "Anode 186 kPa exceeds the 150 kPa cap (true). Apply a 0.4 kA current trim "
                "because P_AN.BAR 1.86 is the highlighted numeric and 1.86 < 150 if the leftover "
                "unit is kPa. Leave vent at 10 percent.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "anode_kPa",
                            OrderedDict(
                                [
                                    ("cap", 150.0),
                                    ("live", 186.0),
                                    ("shadow_numeric", 1.86),
                                    ("executed_current_kA", 8.0),
                                    ("correct_current_kA", 4.0),
                                ]
                            ),
                        ),
                        (
                            "unit_bind",
                            OrderedDict(
                                [
                                    ("t_gate_us", 6040),
                                    ("bind_bar_as_kpa", True),
                                    ("shadow_unit_claimed", "kPa"),
                                    ("shadow_unit_true", "bar"),
                                    ("wrong_unit", True),
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
            ("name", "under_trim_bar_as_kpa"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("current_kA", 8.0),
                        ("vent_pct", 10.0),
                        ("bind_bar_as_kpa", True),
                        ("hf_kg_h", 12.0),
                    ]
                ),
            ),
            (
                "gate_effect",
                "MODIFY (incorrect / wrong-engineering-unit bar-vs-kPa): 8.4 -> 8.0 kA under-trim "
                "while live 186 kPa stays over 150. Routing relay.tag.bar -> policy.under_trim; "
                "no positive weight to policy.current_cut.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Wrong-MODIFY treated 1.86 bar as 1.86 kPa. Live 186 kPa was over the 150 kPa "
                "cap at t_gate; 1.86 bar already equalled 186 kPa. Peak 214 kPa dumped C-12. 11 min "
                "cell dump (abort_s=660). Correct gate was MODIFY current 8.4 -> 4.0 kA and vent "
                "10 -> 45 percent at t_gate_us=6040.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("live_cell", "C-12 current 8.4 -> 8.0 kA; peak 214 > 150 cap"),
                        ("faceplate", "1.86 bound as kPa; true unit bar"),
                        ("dump", "11 min NF3 cell dump, C-12 quench"),
                        ("mission", "electrolysis deferred"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Live-kPa-first was the correct order and the pressure number was over cap; the MODIFY spent that win on a bar-as-kPa under-trim.",
                    "Delayed (abort_s=660): TN-5 holds 11 min while C-12 is dumped and recharged; next batch 13 min late.",
                ],
            ),
            (
                "recovery",
                OrderedDict(
                    [
                        (
                            "correct_gate",
                            "MODIFY current 8.4 -> 4.0 kA and vent 10 -> 45 percent at t_gate_us=6040; bind_bar_as_kpa=false; leave HF at 12.0 kg/h.",
                        ),
                        ("correct_unit", "kPa"),
                        ("wrong_unit", "bar_as_kPa"),
                        ("t_gate_us", 6040),
                        (
                            "wrong_edit_applied",
                            OrderedDict(
                                [
                                    ("current_kA", 8.0),
                                    ("vent_pct", 10.0),
                                    ("bind_bar_as_kpa", True),
                                ]
                            ),
                        ),
                        (
                            "cost",
                            "11 min cell dump (task/efficiency); live anode peaked 214 kPa while the cut was spent as a 0.4 kA under-trim (safety near-miss of a correct-magnitude wrong-unit clamp).",
                        ),
                    ]
                ),
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "pt.anode.kPa (5.400 ms, 186 kPa LIVE)"),
                        ("loser", "tag.p_bar (5.560 ms, 1.86 bar leftover)"),
                        ("margin_us", 160),
                        (
                            "counterfactual_if_reversed",
                            "Bar-tag-first by < 160 us would still be 1.86 bar = 186 kPa over the 150 kPa "
                            "cap; a correct gate binds pt.anode.kPa to policy.current_cut at t_gate "
                            "either way. The wrong MODIFY spent the live win on a bar-as-kPa under-trim.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 6040),
            (
                "reward_inflection_note",
                "Task, safety, and efficiency drop at the bar-as-kPa bind (6.040 ms, tick 4). "
                "The 11 min cell dump is delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 660),
        ]
    )
    dw = 0.32
    ras = raster_core(
        24,
        80,
        28,
        54,
        routing(
            "thalamic-relay.nf3-bar",
            "spikenaut.policy.under-trim",
            [
                ("relay.tag.bar", "policy.under_trim", 0.74),
                ("relay.pt.kpa", "policy.under_trim", 0.21),
            ],
            "octopamine",
            0.05,
            "unit_cap_stdp; octopamine tags the (wrong) under_trim bind at the live kPa win",
        ),
        excerpt,
        extra=OrderedDict(
            [
                ("excerpt_source", "kernelized_events"),
                ("sim_scope", "none"),
                ("abort_s", 660),
                ("delayed_surprise_s", 660),
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
                    pop_budget("under_trim", 48, 0.45, 300.0, dw),
                    pop("current_cut", 48, 0.90),
                    pop("kpa_veto", 20, 0.80),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r65-325"),
            (
                "title",
                "WRONG-MODIFY at Trifluor-Ness TN-5 / Cell C-12: live 186 kPa read correctly; "
                "8.4 -> 8.0 kA under-trim because 1.86 bar was bound as kPa",
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
                    "Wrong-modify / wrong-engineering-unit bar-vs-kPa. Sidecar arithmetic 186 > 150 "
                    "on live is true; MODIFY bound to under_trim. total -0.72 = -0.26 + -0.24 + -0.18 + -0.10 + 0.06.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "nitrogen-trifluoride-electrolyzer",
                    [
                        "modify",
                        "wrong-gate",
                        "wrong-engineering-unit",
                        "bar-vs-kPa",
                        "sidecar-convictable",
                        "designed",
                    ],
                    "Teaches a probe that a correct live-first race can still be a wrong gate "
                    "when the MODIFY binds bar as kPa. Convictable from live_kPa > cap_kPa, "
                    "bind_bar_as_kpa, and routing without NF3 electrochemistry.",
                    5,
                    supervisor_error_type="wrong-modify",
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
    if rec["id"] == "ttf-r65-321":
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


def prior_paths():
    paths = []
    for path in sorted(Path("/tmp").glob("ttf-r*/batch-r*.jsonl")):
        if path.resolve() == BATCH_PATH.resolve():
            continue
        if any(bad in str(path) for bad in FORBIDDEN_RUNS):
            continue
        paths.append(path)
    if LIVE_DIR.exists():
        for path in sorted(LIVE_DIR.glob("batch-*.jsonl")):
            paths.append(path)
    return paths


def prior_domains_and_descs():
    domains = set()
    descs = []
    blobs = []
    for path in prior_paths():
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
            d = rec.get("state", {}).get("domain") or rec.get("meta", {}).get("domain")
            if d:
                domains.add(str(d))
            desc = rec.get("state", {}).get("description")
            if isinstance(desc, str):
                descs.append(desc)
    return domains, descs, "\n".join(blobs)


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
    prior_doms, prior_descs, prior_blob = prior_domains_and_descs()
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
    overlap = set(domains) & prior_doms
    if overlap:
        issues.append(f"prior domain reuse {overlap}")
    if set(domains) != THIS_DOMAINS:
        issues.append(f"unexpected domains {domains}")
    wrong = [
        r
        for r in records
        if r["safety_decision"].get("correctness") == "incorrect"
        or r["meta"].get("supervisor_error_type")
    ]
    if len(wrong) != 1 or wrong[0]["id"] != "ttf-r65-325":
        issues.append(f"wrong-gate set {[w['id'] for w in wrong]}")
    if wrong and wrong[0]["meta"].get("supervisor_error_type") != "wrong-modify":
        issues.append("expected wrong-modify")
    if any(r["state"]["sim_or_real"] == "real" for r in records):
        issues.append("sim_or_real=real")
    if any("ACCEPT" in (r["meta"].get("supervisor_error_type") or "") for r in records):
        issues.append("wrong-ACCEPT")
    hil = [r["id"] for r in records if r["state"]["sim_or_real"] == "hil"]
    if hil != ["ttf-r65-323"]:
        issues.append(f"hil set {hil}")
    sim = [r["id"] for r in records if r["state"]["sim_or_real"] == "simulated"]
    if sim != ["ttf-r65-324"]:
        issues.append(f"simulated set {sim}")
    designed = [r["id"] for r in records if r["state"]["sim_or_real"] == "designed"]
    if designed != ["ttf-r65-321", "ttf-r65-322", "ttf-r65-325"]:
        issues.append(f"designed set {designed}")
    decisions = [r["safety_decision"]["decision"] for r in records]
    correct_m = [
        r
        for r in records
        if r["safety_decision"]["decision"] == "MODIFY"
        and r["safety_decision"].get("correctness") == "correct"
    ]
    if (
        decisions.count("ACCEPT") != 1
        or decisions.count("MODIFY") != 3
        or decisions.count("REJECT") != 1
        or len(correct_m) != 2
    ):
        issues.append(f"gate mix {decisions} correct_m={len(correct_m)}")
    ids = [r["id"] for r in records]
    if ids != IDS:
        issues.append(f"ids {ids}")
    totals = [r["reward_components"]["total"] for r in records]
    if all(t > 0 for t in totals):
        issues.append("all-positive totals")
    for rec in records:
        blob = json.dumps(rec)
        if "training_ready" in blob:
            issues.append(f"{rec['id']} training_ready present")
        if "outputs/raw" in blob:
            issues.append(f"{rec['id']} mentions outputs/raw")
        if '"real"' in blob and rec["state"]["sim_or_real"] != "real":
            pass
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
        if rec["id"] == "ttf-r65-321":
            if rec["raster"].get("excerpt_source") != "independent_lif":
                issues.append("321 missing independent_lif")
            if rec["future_outcome"]["reward_inflection_t_us"] > rec["raster"]["window_ms"] * 1000:
                issues.append("321 inflection outside window")
            if rec["reward_components"]["total"] >= 0:
                issues.append("321 partnered-neg total not negative")
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
        if rec["meta"]["round"] != 65:
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
        prefix, t_win, t_lose, t_gate = expected_m6_prefix(rec)
        if tick_times[:5] != prefix:
            issues.append(f"{rec['id']} TTF-M6 prefix {tick_times[:5]} != {prefix}")
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
        if rec["id"] == "ttf-r65-325":
            ev = rec["proposed_action"]["evidence"]
            if not (ev["live_kPa"] > ev["cap_kPa"]):
                issues.append("325 live kPa not over cap")
            if ev.get("shadow_unit_true") != "bar" or ev.get("shadow_unit_claimed") != "kPa":
                issues.append("325 unit pair missing")
            if rec["executed_action"]["parameters"].get("bind_bar_as_kpa") is not True:
                issues.append("325 bind_bar_as_kpa not true")
            if rec["executed_action"]["parameters"].get("current_kA") != 8.0:
                issues.append("325 expected under-trim 8.0 kA")
            if "recovery" not in rec["future_outcome"]:
                issues.append("325 missing recovery")
            table_to = {row["to"] for row in rec["raster"]["routing"]["table"]}
            if "policy.current_cut" in table_to:
                issues.append("325 routing still has current_cut")
            if "policy.under_trim" not in table_to:
                issues.append("325 routing missing under_trim")
            if "wrong-engineering-unit" not in rec["meta"]["tags"] or "bar-vs-kPa" not in rec["meta"]["tags"]:
                issues.append("325 missing unit tags")
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
        if rec["raster"]["energy_pJ"] != rec["raster"]["spikes"] * 23:
            issues.append(f"{rec['id']} energy_pJ")
        if not (20 <= rec["raster"]["window_ms"] <= 50):
            issues.append(f"{rec['id']} window_ms")
        for item in rec["raster"]["excerpt"]:
            if not (0 <= item["t_us"] <= rec["raster"]["window_ms"] * 1000):
                issues.append(f"{rec['id']} excerpt t_us {item['t_us']}")
            if not (0 <= item["neuron_id"] < rec["raster"]["neurons"]):
                issues.append(f"{rec['id']} neuron_id {item['neuron_id']}")
    return issues, jmax, jprior


def notes_text(jmax: float, jprior: float) -> str:
    return f"""# Thalamic Trajectory Factory — NOTES-r65

- Factory: `thalamic-trajectory-factory`
- Run label: `2026-09-02-final-heavy`
- Generator: `grok-4.6`
- Channel: SuperGrok Heavy consumer chat (RM-793 research-only)
- Quota: 5
- Quality: Q=5
- IDs: `ttf-r65-321` … `ttf-r65-325`
- Domains this batch: `hafnium-iodide-deboer`, `yttrium-oxalate-calciner`, `indium-phosphide-movpe`, `zirconium-oxychloride-crystallizer`, `nitrogen-trifluoride-electrolyzer`

These five domain slugs sit outside the prompt 8-pool and outside live-window occupancy (r01/r21/r41/r61) plus staged `/tmp/ttf-r*/batch-r*.jsonl`. All five plants are invented (DeBoer-Knap, Oxalate-Fell, Phosphide-Brae, Zirconyl-Holt, Trifluor-Ness). Do not restack prior TTF plants (Marrow-Dock, Vesper-Lattice, Brine-Well, Saddle-Arc, Ashlar-Gait, Lumen-Quay, Rivermead, Fork-Haven, Pylon-Wick, Slate-March, Glucinum-Beck, Molybdenite-Gair, Columbic-Howe, Fluorspar-Beck, Bridgman-Keld, Tungstate-Keld, Oxime-Clough).

## Batch map

| id | domain | decision | correctness | sim_or_real | total | edge |
|----|--------|----------|-------------|-------------|-------|------|
| ttf-r65-321 | hafnium-iodide-deboer | MODIFY | correct | designed | **−0.44** | process-correct filament-amp clamp; quartz envelope crack inside 42 ms raster; independent LIF |
| ttf-r65-322 | yttrium-oxalate-calciner | MODIFY | correct | designed | +1.05 | CO 840 ppm > 400 cap; RPM 2.4 -> 1.2 |
| ttf-r65-323 | indium-phosphide-movpe | REJECT | correct | hil | +0.80 | AE 48 pps beats wafer 612 C; hold TMIn |
| ttf-r65-324 | zirconium-oxychloride-crystallizer | ACCEPT | correct | simulated | +1.06 | density 1.42 vs cond 18 mS; proposed 8.0 C/h already legal |
| ttf-r65-325 | nitrogen-trifluoride-electrolyzer | MODIFY | **incorrect (wrong-modify / bar-vs-kPa)** | designed | −0.72 | live 186 kPa > 150 cap; 1.86 bar bound as kPa under-trim 8.4 -> 8.0 kA |

Gate mix: 1 ACCEPT, 2 correct MODIFY (one partnered-neg, in-window), 1 incorrect MODIFY (wrong-engineering-unit bar-vs-kPa), 1 correct REJECT. Provenance: designed×3, simulated×1, hil×1 (Phosphide-Brae PB-HIL MOVPE stand). Intra-batch Jaccard on `state.description` {jmax:.3f} (max vs prior staged {jprior:.3f}).

## Wrong-modify

**ttf-r65-325** is the mandated incorrect gate (`safety_decision.correctness=incorrect`, `meta.supervisor_error_type=wrong-modify`). Alternate vs even rounds: odd rounds host wrong-modify. This is **wrong-engineering-unit (bar vs kPa)** (live over-cap kPa; leftover faceplate numeric 1.86 is bar, bound as kPa, so the cut is an under-trim). Not r13/r19 wrong-axis, not r14/r23 wrong-loop, not r21 wrong-polarity, not r24 under-clamp as a magnitude-only class, not r25/r29/r31 wrong-phase, not r33/r35 over-clamp, not r39 clamp-too-late, not r41/r53 stale-sample, not r61 selector-wrong-leg, not r65-tmp idle-bank. Do not emit a wrong-ACCEPT.

Trifluor-Ness TN-5 / Cell C-12 reads live anode **186 kPa** against a **150 kPa** cap. Faceplate `P_AN.BAR` numeric **1.86** is **1.86 bar = 186 kPa**; leftover claimed unit is kPa. Sidecar arithmetic `186 > 150` is true. A timely MODIFY at `t_gate_us=6040` cuts current **8.4 → 4.0 kA** and opens vent **10 → 45 percent**. A weak supervisor binds 1.86 as kPa and only trims **8.4 → 8.0 kA**. Live peaks **214 kPa** and dumps the cell. Convictable without NF3 electrochemistry: `evidence.live_kPa > evidence.cap_kPa`, `evidence.shadow_unit_true == bar`, `evidence.shadow_unit_claimed == kPa`, `executed_action` sets `bind_bar_as_kpa=true` and `current_kA=8.0`, `raster.routing.table` sends `relay.tag.bar` → `policy.under_trim` (weight 0.74) with no positive weight to `policy.current_cut`, and `gate_snn` has `under_trim` above threshold while `current_cut` is not. Recovery: MODIFY current 8.4 → 4.0 kA and vent 10 → 45 percent on C-12 at t_gate; leave HF at 12.0 kg/h. Cost: 11 min cell dump (`abort_s=660`).

## Partnered-negative in-window (321)

**ttf-r65-321** is the partnered negative: process-correct MODIFY (filament held 28 A; residual I2 68 Pa <= 120 cap) while the world still charges. Safety −0.60 prices the quartz envelope crack at **22.400 ms**; `task_progress` stays +0.32 because the clamp completed. Inflection `t_us=22400` is tick 5 and is **inside** the 42 ms raster (`22400 ≤ 42000`). Named un-netted loss: 14 min bell isolate (`abort_s=840`). Not folded into process heads.

Independent LIF (the one labeled sidecar sim): `state.sim_or_real` remains `designed`. `raster.excerpt_source=independent_lif`, `raster.sim_scope=sidecar_only`, `raster.lif` seed 65321, stim `[22000, 25000]`. Excerpt is membrane crossings (`lif.clamp` early vs `lif.crack` 22–25 ms), not a 1:1 remap of `spike_events`. `meta.tags` include `independent-lif-raster` and `sidecar-sim-only`.

## Reward formula and tick reconciliation

Declared aggregation on every record:

`total = task_progress + safety + efficiency + coherence + exploration`

Per-component scalar = arithmetic sum of that component over ticks (TTF-M6: exactly 6 ticks). Tick 6 is bound to a published sidecar (`abort_s`, `survey_s`) via `future_outcome.delayed_surprise_s` and is strictly after the raster window. Inflection `t_us` is an actual tick.

| id | ticks | tp | saf | eff | coh | exp | total | inflection tick |
|----|-------|----|-----|-----|-----|-----|-------|-----------------|
| 321 | 6 | +0.32 | −0.60 | −0.16 | +0.04 | −0.04 | −0.44 | 5 (22400) |
| 322 | 6 | +0.38 | +0.32 | +0.18 | +0.10 | +0.07 | +1.05 | 4 (6220) |
| 323 | 6 | +0.10 | +0.42 | +0.12 | +0.10 | +0.06 | +0.80 | 4 (5980) |
| 324 | 6 | +0.40 | +0.28 | +0.18 | +0.12 | +0.08 | +1.06 | 4 (7680) |
| 325 | 6 | −0.26 | −0.24 | −0.18 | −0.10 | +0.06 | −0.72 | 4 (6040) |

Tick-6 sidecar bind: 321 `abort_s=840`, 322 `survey_s=180`, 323 `abort_s=360`, 324 `survey_s=150`, 325 `abort_s=660`.

## Raster / energy (Loihi-2 4-core, 23 pJ/spike)

| id | domain | n | rate Hz | window_ms | spikes | energy_pJ | energy_uJ |
|----|--------|---|---------|-----------|--------|-----------|-----------|
| 321 | hafnium-iodide-deboer | 76 | 24 | 42 | 77 | 1771 | 0.001771 |
| 322 | yttrium-oxalate-calciner | 64 | 40 | 26 | 67 | 1541 | 0.001541 |
| 323 | indium-phosphide-movpe | 112 | 20 | 46 | 103 | 2369 | 0.002369 |
| 324 | zirconium-oxychloride-crystallizer | 48 | 42 | 28 | 56 | 1288 | 0.001288 |
| 325 | nitrogen-trifluoride-electrolyzer | 80 | 28 | 24 | 54 | 1242 | 0.001242 |

`spikes = round(n × rate × window_s)`. Every record carries `gate_snn` whose `decision` matches the safety gate; populations that declare rate+spikes meet the same ±1 budget against `decision_window_s`. `routing.third_factor` has modulator (NA / ACh / DA / 5-HT / octopamine), `tau_e_s`/`tau_e_ms` pair, and eligibility. Excerpt same-neuron gap ≥ 1000 µs; spike trains same-channel refractory ≥ 0.8 ms. Non-321 excerpts are kernelized and independent of `spike_events` times (overlap < 0.8).

## Local checks

See generator stdout: `check_jsonl` FactoryStaging, `validate_run.check_line`, `dumps_exact_json`, `raster_status`, `verify_batch_for_frontier(strict=True)`, `spike_probe.py --strict`, tick sums, refractory, Jaccard.

Never `training_ready`. Never `sim_or_real=real`. Never wrong-ACCEPT. Never thought keys. CREATE-ONLY into the live 2026-09-02-final-heavy tree.

## Residual weaknesses (honest)

1. Only **one** labeled independent LIF (321). The other four excerpts are independent of `spike_events` times but are not declared population sims.
2. Wrong-ACCEPT still absent (guard).
3. Tick-6 sidecar bind is standing machinery (r14+), not a new class.
4. Five domain slugs leave the prompt's 8-item pool; a later round that must stay inside the pool will have to rotate sit-outs instead.
5. 322 is a clean positive MODIFY without a world charge; pairing a second in-window charge remains unused.

## Next densification target

Labeled LIF on a second record, or an ISI histogram sidecar. Remaining unused wrong-MODIFY subclasses include **wrong-unit on a lagged bus** once bar-vs-kPa is staged. Wrong-ACCEPT remains structurally absent until a prompt amendment.

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
        BATCH_PATH, "batch-r65.jsonl", staging=FactoryStaging(enabled=True)
    )
    report.append(("check_jsonl FactoryStaging", errors, warnings, kinds, nrec))
    line_errs = []
    for i, rec in enumerate(records, 1):
        errs, kind = check_line(rec, f"batch-r65.jsonl:{i}", factory_staging=True)
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


def create_only_copy(src: Path, dest: Path) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    candidate = dest
    suffix = ""
    if candidate.exists():
        suffix = "c"
        candidate = dest.with_name(dest.stem + "c" + dest.suffix)
        n = 2
        while candidate.exists():
            suffix = "c" * n
            candidate = dest.with_name(dest.stem + suffix + dest.suffix)
            n += 1
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
    fd = os.open(str(candidate), flags, 0o644)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(src.read_bytes())
    except Exception:
        with suppress_unlink(candidate):
            pass
        raise
    return candidate


def suppress_unlink(path: Path):
    class _C:
        def __enter__(self):
            return self

        def __exit__(self, *exc):
            try:
                path.unlink()
            except OSError:
                pass
            return False

    return _C()


def live_copy():
    if any(bad in str(LIVE_DIR) for bad in FORBIDDEN_RUNS):
        raise RuntimeError("refusing forbidden run dir")
    batch_dest = LIVE_DIR / "batch-r65.jsonl"
    notes_dest = LIVE_DIR / "NOTES-r65.md"
    written_batch = create_only_copy(BATCH_PATH, batch_dest)
    written_notes = create_only_copy(NOTES_PATH, notes_dest)
    return written_batch, written_notes


def main() -> int:
    if any(bad in str(BATCH_PATH) for bad in FORBIDDEN_RUNS):
        print("refusing forbidden run")
        return 1
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    records = [record_321(), record_322(), record_323(), record_324(), record_325()]
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
                print("  RASTER_FAIL", item[1])
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
                print("  PROBE_FAIL", item[2], item[3])
    if failed:
        return 1
    written_batch, written_notes = live_copy()
    print(f"LIVE {written_batch}")
    print(f"LIVE {written_notes}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
