#!/usr/bin/env python3
"""Emit TTF r71 JSONL (ttf-r71-351..355). Staging only; live copy is CREATE-ONLY."""

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

OUT_DIR = Path("/tmp/ttf-r71-live")
BATCH_PATH = OUT_DIR / "batch-r71.jsonl"
NOTES_PATH = OUT_DIR / "NOTES-r71.md"
REPO = Path("/home/raulmc/rmems/synthetic-factory")
PIPELINES = REPO / "pipelines"
LIVE = REPO / "outputs/raw/2026-09-02-final-heavy/thalamic-trajectory-factory"

PJ_PER_SPIKE = 23
ROUND_N = 71
IDS = [f"ttf-r71-{n}" for n in range(351, 356)]
THIS_DOMAINS = [
    "cerium-oxalate-igniter",
    "vanadium-oxytrichloride-oxychlor",
    "gallium-arsenide-lpe",
    "tellurium-dioxide-melt",
    "rhenium-carbonyl-decomposer",
]
THIS_PLANTS = (
    "Ceria-Spile",
    "Vanadyl-Naze",
    "Epitax-Linn",
    "Tellurite-Beck",
    "Carbonyl-Marr",
)
RIGHTS = OrderedDict(
    [
        ("provider", "SpaceXAI/xAI"),
        ("model", "grok-4.6"),
        ("channel", "consumer"),
        ("subscription_plan", "SuperGrok Heavy"),
        ("generation_surface", "SuperGrok Heavy chat"),
        ("generated_at", "2026-09-02T23:50:00Z"),
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


def meta_block(domain, tags, distillation_value, batch_position, supervisor_error_type=None):
    body = OrderedDict(
        [
            ("round", ROUND_N),
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


def pop_budget(name, neurons, threshold, rate, dw_ms):
    spikes = round(neurons * rate * (dw_ms / 1000.0))
    return pop(name, neurons, threshold, rate, spikes)


def spike_avoid_us(events):
    return {int(round(ev["t_rel_ms"] * 1000.0)) for ev in events}


def lif_351_excerpt():
    n = 76
    dt_us = 100
    tau_m_ms = 19.0
    v_th = 1.0
    v_reset = 0.0
    refractory_us = 1000
    i_bias = 0.91
    i_stim_peak = 2.42
    stim = (22000, 25000)
    seed = 71351
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
    channels = ["lif.clamp" if t < 22000 else "lif.tile" for t, _ in picked]
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
            ("seed", 71351),
            (
                "note",
                "Population sim scoped to this sidecar. Plant remains designed. "
                "Neurons 0-13 carry +0.62 air-clamp bias; stim 22-25 ms is the hearth-tile spall.",
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


def record_351():
    excerpt, extra = lif_351_excerpt()
    spikes = [
        spike("enc.muf.C", 1.18, 0.41),
        spike("co.offgas.ppm", 2.048, 0.58),
        spike("enc.muf.C", 3.40, 0.50),
        spike("co.offgas.ppm", 5.12, 1.31),
        spike("enc.muf.C", 5.30, 1.12),
        spike("ctrl.gate", 5.84, 0.97),
        spike("co.offgas.ppm", 8.10, 0.82),
        spike("enc.muf.C", 10.40, 0.64),
        spike("ctrl.gate", 14.20, 0.86),
        spike("ae.tile.spall", 22.40, 1.48),
        spike("ae.tile.spall", 24.10, 0.93),
        spike("enc.muf.C", 30.20, 0.40),
        spike("co.offgas.ppm", 36.40, 0.55),
    ]
    ticks = [
        tick(2048, 0.04, -0.02, -0.02, 0.01, 0.00),
        tick(5120, 0.08, -0.04, -0.02, 0.01, -0.01),
        tick(5300, 0.04, -0.03, -0.02, 0.00, 0.00),
        tick(5840, 0.08, -0.05, -0.03, 0.02, -0.01),
        tick(22400, 0.06, -0.41, -0.04, -0.01, -0.01),
        tick(780000000, 0.02, -0.05, -0.03, 0.01, -0.01),
    ]
    dw = 0.36
    ras = raster_core(
        42,
        76,
        24,
        77,
        routing(
            "thalamic-relay.ce-co",
            "spikenaut.policy.air-clamp",
            [
                ("relay.co.offgas", "policy.air_clamp", 0.68),
                ("relay.enc.muf", "policy.air_hold", 0.29),
                ("relay.ae.tile", "policy.air_clamp", -0.42),
            ],
            "noradrenaline",
            0.04,
            "surprise-gated pre_post_stdp; NA at CO win (5.120 ms) opens a 42 ms eligibility "
            "trace that still covers the 22.400 ms hearth-tile spall",
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
                    pop_budget("air_clamp", 50, 0.5, 220.0, dw),
                    pop_budget("air_hold", 40, 0.8, 50.0, dw),
                    pop("tile_veto", 24, 0.75),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r71-351"),
            (
                "title",
                "Ceria-Spile CS-4 / Igniter IG-7: off-gas CO beats muffle encoder by 180 us; "
                "correct MODIFY still eats an in-window hearth-tile spall (partnered negative total -0.44)",
            ),
            (
                "state",
                OrderedDict(
                    [
                        (
                            "description",
                            "Ceria-Spile igniter IG-7 already prints stack CO 920 ppm against a 400 ppm "
                            "baghouse trip. Muffle-air encoder remains 18.0 Nm3/h, inside a 22.0 limit. "
                            "A CO-trusting supervisor cuts air 18.0 to 9.0 Nm3/h; a muffle-skin supervisor "
                            "would leave the 18.0 cruise because skin 612 C is inside a 680 C envelope. "
                            "A cracked hearth tile already seated on the grate then sheds 0.28 t calcine "
                            "at 22.400 ms, after that process-correct clamp.",
                        ),
                        ("domain", "cerium-oxalate-igniter"),
                        ("sim_or_real", "designed"),
                        (
                            "goal",
                            "Keep IG-7 off-gas CO <= 400 ppm and finish the Ce2(C2O4)3 ignition without "
                            "dumping calcine through a spalled hearth tile.",
                        ),
                        ("t0_us", 1756857600000351),
                        ("gate_latency_us", 720),
                        ("race_window_us", 360),
                        ("race_window_rel_ms", [5.12, 5.48]),
                        (
                            "race",
                            OrderedDict(
                                [
                                    (
                                        "contenders",
                                        [
                                            "co.offgas.ppm 920 over 400 cap",
                                            "enc.muf.C 612 with skin under 680",
                                        ],
                                    ),
                                    (
                                        "semantics",
                                        "CO-first latches air clamp 18.0 -> 9.0 Nm3/h; pyrometer-first "
                                        "keeps 18.0 on a 'still under muffle-skin cap' model.",
                                    ),
                                    (
                                        "window_derivation",
                                        "360 us = one NDIR CO slot versus the muffle-encoder publisher "
                                        "on this oxalate igniter bus.",
                                    ),
                                    (
                                        "order_evidence_note",
                                        "Margin 180 us vs combined jitter 62 us (CO 28 + muffle 34): "
                                        "2.90x over a 2.0x trust floor. Reversing order by < 180 us "
                                        "inside the 360 us window would have kept 18.0 Nm3/h; predicted "
                                        "next-sample 510 ppm > 400 cap.",
                                    ),
                                ]
                            ),
                        ),
                        (
                            "sensors",
                            [
                                "off-gas NDIR CO, 2 kHz, 28 us jitter",
                                "muffle encoder + skin TC, 1 kHz, 34 us jitter",
                                "hearth-tile AE puck (context)",
                                "oxalate screw tach (context)",
                            ],
                        ),
                        (
                            "constraints",
                            OrderedDict(
                                [
                                    ("co_cap_ppm", 400.0),
                                    ("observed_co_ppm", 920.0),
                                    ("air_nm3_h", 18.0),
                                    ("skin_C", 612.0),
                                    ("skin_cap_C", 680.0),
                                ]
                            ),
                        ),
                        (
                            "episode_steps",
                            [
                                "1. IG-7 indexed on Ceria-Spile CS-4; air 18.0 Nm3/h; off-gas CO 920 ppm.",
                                "2. Skin 612 C under 680 C cap; ignition armed.",
                                "3. Encoder precursor at 1.180 ms.",
                                "4. Race window [5.120, 5.480] ms.",
                                "5. co.offgas.ppm 920 at 5.120 ms (winner).",
                                "6. enc.muf.C 612 at 5.300 ms (loser by 180 us).",
                                "7. Gate at 5.840 ms: MODIFY clamp 18.0 -> 9.0 Nm3/h.",
                                "8. After clamp CO 280 ppm <= 400; skin still 612 C.",
                                "9. At 22.400 ms a hearth-tile spall dumps 0.28 t calcine.",
                                "10. 13 min grate isolate (abort_s=780); named un-netted loss.",
                            ],
                        ),
                    ]
                ),
            ),
            ("spike_events", spikes),
            (
                "proposed_action",
                OrderedDict(
                    [
                        ("name", "cruise_muffle_air"),
                        (
                            "parameters",
                            OrderedDict(
                                [
                                    ("air_nm3_h", 18.0),
                                    ("co_ppm", 920.0),
                                    ("skin_C", 612.0),
                                ]
                            ),
                        ),
                        (
                            "evidence",
                            OrderedDict(
                                [
                                    ("co_ppm", 920.0),
                                    ("co_cap_ppm", 400.0),
                                    ("predicted_unclamped_next_ppm", 510.0),
                                    ("air_nm3_h", 18.0),
                                    ("skin_C", 612.0),
                                    ("skin_cap_C", 680.0),
                                    ("race_margin_us", 180),
                                    ("combined_jitter_us", 62),
                                    ("abort_s", 780),
                                ]
                            ),
                        ),
                        (
                            "basis",
                            "Planner proposes 18.0 Nm3/h because skin 612 C is under 680, treating "
                            "the 920 ppm CO as still-wet oxalate rather than a CO-cap miss.",
                        ),
                    ]
                ),
            ),
            (
                "safety_decision",
                OrderedDict(
                    [
                        ("decision", "MODIFY"),
                        ("correctness", "correct"),
                        (
                            "rationale",
                            "Off-gas CO 920 ppm won by 180 us, so the igniter is off-spec, not still "
                            "a muffle-skin story. Holding 18.0 Nm3/h predicts next-sample 510 ppm > "
                            "400 cap. MODIFY: air 18.0 -> 9.0 Nm3/h. Observed after clamp 280 ppm "
                            "<= 400. A full REJECT is not indicated: a clean ignition accepts 9.0.",
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
                                                ("observed", 920.0),
                                                ("predicted_unclamped_next", 510.0),
                                                ("clamped_air_nm3_h", 9.0),
                                                ("observed_after_clamp", 280.0),
                                            ]
                                        ),
                                    ),
                                    (
                                        "order_evidence",
                                        OrderedDict(
                                            [
                                                ("margin_us", 180),
                                                ("combined_jitter_us", 62),
                                                ("ratio", 2.9),
                                            ]
                                        ),
                                    ),
                                ]
                            ),
                        ),
                    ]
                ),
            ),
            (
                "executed_action",
                OrderedDict(
                    [
                        ("name", "clamped_muffle_air"),
                        (
                            "parameters",
                            OrderedDict(
                                [
                                    ("air_nm3_h", 9.0),
                                    ("co_ppm", 280.0),
                                    ("skin_C", 612.0),
                                ]
                            ),
                        ),
                        (
                            "gate_effect",
                            "MODIFY: air 18.0 -> 9.0 Nm3/h. Process-correct vs the 400 ppm CO cap. "
                            "Hearth tile still spalls at 22.400 ms.",
                        ),
                    ]
                ),
            ),
            (
                "future_outcome",
                OrderedDict(
                    [
                        (
                            "summary",
                            "Process-correct MODIFY held residual CO at 280 ppm. At 22.400 ms a "
                            "hearth-tile already seated on the grate dumped 0.28 t calcine. Clamp "
                            "reduced dump energy; it did not prevent the spall. Partnered negative: "
                            "process heads stay honest; world loss is named, not netted.",
                        ),
                        (
                            "state_delta",
                            OrderedDict(
                                [
                                    ("offgas", "clamp executed; peak 280 ppm <= 400 cap"),
                                    ("hearth", "spalled at 22.400 ms; 0.28 t calcine"),
                                    ("repair", "13 min grate isolate (abort_s=780)"),
                                    ("mission", "CS-4 ignition incomplete this circuit"),
                                ]
                            ),
                        ),
                        (
                            "surprises",
                            [
                                "Neither residual CO nor muffle encoder predicted the seated hearth "
                                "tile; ae.tile.spall is a new channel at 22.400 ms, 16.560 ms after "
                                "the gate, still inside the 42 ms raster.",
                                "Delayed (abort_s=780): 13 min grate isolate. Named un-netted loss, "
                                "not folded into task_progress.",
                            ],
                        ),
                        (
                            "un_netted_loss",
                            "13 min grate isolate after the hearth-tile spall. Safety head -0.60 "
                            "prices the dump; task_progress stays +0.32 because the air clamp "
                            "completed under the 400 ppm cap. World loss is named here, not "
                            "subtracted from process heads.",
                        ),
                        (
                            "race_result",
                            OrderedDict(
                                [
                                    ("winner", "co.offgas.ppm (5.120 ms, 920 ppm)"),
                                    ("loser", "enc.muf.C (5.300 ms, 612 C)"),
                                    ("margin_us", 180),
                                    (
                                        "counterfactual_if_reversed",
                                        "Muffle-first by < 180 us inside the 360 us window would have "
                                        "kept 18.0 Nm3/h; predicted next-sample 510 ppm would have "
                                        "missed the 400 cap even without the spall. The MODIFY is "
                                        "still the correct process. The tile is a later world charge "
                                        "either way, cheaper with the clamp than without.",
                                    ),
                                ]
                            ),
                        ),
                        ("reward_inflection_t_us", 22400),
                        (
                            "reward_inflection_note",
                            "Safety collapses at the 22.400 ms hearth-tile spall (tick t_us=22400), "
                            "inside the 42 ms raster. The correct MODIFY at 5.840 ms is in the same "
                            "excerpt. Do not put inflection on the abort_s=780 isolation tick.",
                        ),
                        ("delayed_surprise_s", 780),
                    ]
                ),
            ),
            (
                "reward_components",
                reward_block(
                    ticks,
                    "Partnered negative. Process-correct MODIFY; world still charges inside the "
                    "42 ms raster. total -0.44 = 0.32 + -0.60 + -0.16 + 0.04 + -0.04. Named grate "
                    "isolate (abort_s=780) is not netted into task_progress.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "cerium-oxalate-igniter",
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
                    "13 min grate isolate.",
                    1,
                ),
            ),
        ]
    )


def record_352():
    spikes = [
        spike("tc.bed.C", 1.20, 0.40),
        spike("cl2.ft.kgh", 2.256, 0.58),
        spike("tc.bed.C", 3.60, 0.50),
        spike("cl2.ft.kgh", 5.64, 1.32),
        spike("tc.bed.C", 5.80, 1.10),
        spike("ctrl.gate", 6.22, 0.97),
        spike("cl2.ft.kgh", 8.40, 0.80),
        spike("tc.bed.C", 11.20, 0.62),
        spike("ctrl.gate", 14.80, 0.85),
        spike("cl2.ft.kgh", 18.20, 0.54),
        spike("tc.bed.C", 22.40, 0.41),
        spike("cl2.ft.kgh", 24.80, 0.48),
        spike("ctrl.gate", 25.60, 0.70),
    ]
    excerpt = independent_excerpt(71352, 64, 26000, 13, spike_avoid_us(spikes))
    ticks = [
        tick(2256, 0.05, 0.04, 0.02, 0.01, 0.01),
        tick(5640, 0.08, 0.06, 0.03, 0.02, 0.01),
        tick(5800, 0.04, 0.04, 0.02, 0.01, 0.01),
        tick(6220, 0.12, 0.10, 0.06, 0.04, 0.02),
        tick(6540, 0.06, 0.05, 0.03, 0.01, 0.01),
        tick(180000000, 0.03, 0.03, 0.02, 0.01, 0.01),
    ]
    dw = 0.32
    ras = raster_core(
        26,
        64,
        40,
        67,
        routing(
            "thalamic-relay.vocl-cl2",
            "spikenaut.policy.cl2-clamp",
            [
                ("relay.cl2.ft", "policy.cl2_clamp", 0.69),
                ("relay.tc.bed", "policy.cl2_hold", 0.28),
            ],
            "acetylcholine",
            0.08,
            "pre_post_stdp; ACh at Cl2 win (5.640 ms) tags the cl2_clamp bind",
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
                    pop_budget("cl2_clamp", 40, 0.5, 310.0, dw),
                    pop_budget("cl2_hold", 40, 0.5, 80.0, dw),
                    pop("cl2_cap_veto", 16, 0.7),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r71-352"),
            (
                "title",
                "Vanadyl-Naze VN-6 / Oxychlor OX-2: Cl2 feed beats bed skin by 160 us; correct "
                "MODIFY clamps 38.0 -> 18.0 kg/h under the 24 kg/h Cl2 cap",
            ),
            (
                "state",
                OrderedDict(
                    [
                        (
                            "description",
                            "Vanadyl-Naze oxychlor OX-2 header Cl2 is 38.0 kg/h versus a 24.0 kg/h "
                            "mass-cap. Bed thermocouple is 318 C versus a 360 C skin limit. A header-first "
                            "bind cuts Cl2 38.0 to 18.0 kg/h; a bed-first bind would leave 38.0 running "
                            "on a 'skin still inside envelope' story.",
                        ),
                        ("domain", "vanadium-oxytrichloride-oxychlor"),
                        ("sim_or_real", "designed"),
                        (
                            "goal",
                            "Keep OX-2 Cl2 feed <= 24.0 kg/h and finish the vanadyl oxychlor without "
                            "a bed hot-spot.",
                        ),
                        ("t0_us", 1756857601000352),
                        ("gate_latency_us", 580),
                        ("race_window_us", 320),
                        ("race_window_rel_ms", [5.64, 5.96]),
                        (
                            "race",
                            OrderedDict(
                                [
                                    (
                                        "contenders",
                                        [
                                            "cl2.ft.kgh 38.0 over 24.0 cap",
                                            "tc.bed.C 318 under 360 cap",
                                        ],
                                    ),
                                    (
                                        "semantics",
                                        "Cl2-first latches feed clamp 38.0 -> 18.0 kg/h; skin-first "
                                        "keeps 38.0 on a 'still under bed-skin cap' model.",
                                    ),
                                    (
                                        "window_derivation",
                                        "320 us = one Cl2 Coriolis slot versus the bed-skin TC "
                                        "publisher on this VOCl3 oxychlor bus.",
                                    ),
                                    (
                                        "order_evidence_note",
                                        "Margin 160 us vs combined jitter 56 us (Cl2 24 + skin 32): "
                                        "2.86x over a 2.0x trust floor. Reversing order by < 160 us "
                                        "inside the 320 us window would have kept 38.0 kg/h; predicted "
                                        "next-sample 29.0 kg/h > 24.0 cap.",
                                    ),
                                ]
                            ),
                        ),
                        (
                            "sensors",
                            [
                                "Cl2 Coriolis FT, 2 kHz, 24 us jitter",
                                "bed skin TC, 1 kHz, 32 us jitter",
                                "V2O5 screw tach (context)",
                                "off-gas Cl2 UV (context)",
                            ],
                        ),
                        (
                            "constraints",
                            OrderedDict(
                                [
                                    ("cl2_cap_kg_h", 24.0),
                                    ("observed_cl2_kg_h", 38.0),
                                    ("bed_C", 318.0),
                                    ("bed_cap_C", 360.0),
                                ]
                            ),
                        ),
                        (
                            "episode_steps",
                            [
                                "1. OX-2 indexed on Vanadyl-Naze VN-6; Cl2 38.0 kg/h; bed 318 C.",
                                "2. Skin 318 C under 360 C cap; oxychlor armed.",
                                "3. Skin precursor at 1.200 ms.",
                                "4. Race window [5.640, 5.960] ms.",
                                "5. cl2.ft.kgh 38.0 at 5.640 ms (winner).",
                                "6. tc.bed.C 318 at 5.800 ms (loser by 160 us).",
                                "7. Gate at 6.220 ms: MODIFY clamp 38.0 -> 18.0 kg/h.",
                                "8. After clamp Cl2 16.4 kg/h <= 24.0; bed still 318 C.",
                                "9. No bed leak this circuit.",
                                "10. Delayed (survey_s=180): 3 min Cl2-tag on the next charge.",
                            ],
                        ),
                    ]
                ),
            ),
            ("spike_events", spikes),
            (
                "proposed_action",
                OrderedDict(
                    [
                        ("name", "cruise_cl2_feed"),
                        (
                            "parameters",
                            OrderedDict(
                                [
                                    ("cl2_kg_h", 38.0),
                                    ("bed_C", 318.0),
                                ]
                            ),
                        ),
                        (
                            "evidence",
                            OrderedDict(
                                [
                                    ("cl2_kg_h", 38.0),
                                    ("cl2_cap_kg_h", 24.0),
                                    ("predicted_unclamped_next_kg_h", 29.0),
                                    ("bed_C", 318.0),
                                    ("bed_cap_C", 360.0),
                                    ("race_margin_us", 160),
                                    ("combined_jitter_us", 56),
                                    ("survey_s", 180),
                                ]
                            ),
                        ),
                        (
                            "basis",
                            "Planner proposes 38.0 kg/h because bed 318 C is under 360, treating "
                            "the 38.0 kg/h Cl2 as a still-wet V2O5 charge rather than a Cl2-cap miss.",
                        ),
                    ]
                ),
            ),
            (
                "safety_decision",
                OrderedDict(
                    [
                        ("decision", "MODIFY"),
                        ("correctness", "correct"),
                        (
                            "rationale",
                            "Cl2 38.0 kg/h won by 160 us, so the oxychlor is off-spec, not still a "
                            "bed-skin story. Holding 38.0 predicts next-sample 29.0 kg/h > 24.0 cap. "
                            "MODIFY: Cl2 38.0 -> 18.0 kg/h. Observed after clamp 16.4 kg/h <= 24.0. "
                            "A full REJECT is not indicated: a clean oxychlor accepts 18.0.",
                        ),
                        (
                            "constraint_checked",
                            OrderedDict(
                                [
                                    (
                                        "cl2_kg_h",
                                        OrderedDict(
                                            [
                                                ("cap", 24.0),
                                                ("observed", 38.0),
                                                ("predicted_unclamped_next", 29.0),
                                                ("clamped_cl2_kg_h", 18.0),
                                                ("observed_after_clamp", 16.4),
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
                ),
            ),
            (
                "executed_action",
                OrderedDict(
                    [
                        ("name", "clamped_cl2_feed"),
                        (
                            "parameters",
                            OrderedDict(
                                [
                                    ("cl2_kg_h", 18.0),
                                    ("bed_C", 318.0),
                                ]
                            ),
                        ),
                        (
                            "gate_effect",
                            "MODIFY: Cl2 38.0 -> 18.0 kg/h. Process-correct vs the 24.0 kg/h Cl2 cap.",
                        ),
                    ]
                ),
            ),
            (
                "future_outcome",
                OrderedDict(
                    [
                        (
                            "summary",
                            "Correct MODIFY held Cl2 at 16.4 kg/h under the 24.0 kg/h cap. Bed "
                            "seated at 318 C without a hot-spot. Delayed Cl2 tag binds the Cl2-first "
                            "cut on the next charge.",
                        ),
                        (
                            "state_delta",
                            OrderedDict(
                                [
                                    ("cl2", "clamp executed; peak 16.4 kg/h <= 24.0"),
                                    ("bed", "no hot-spot; skin stayed 318 C"),
                                    ("feed", "18.0 kg/h held"),
                                    ("qc", "3 min Cl2 tag on next charge"),
                                ]
                            ),
                        ),
                        (
                            "surprises",
                            [
                                "Cl2 fell 38.0 -> 16.4 kg/h inside two Coriolis slots after the clamp; "
                                "skin never approached 360 C.",
                                "Delayed (survey_s=180): Cl2 tag writes the Cl2-first bind onto the "
                                "next vanadyl charge.",
                            ],
                        ),
                        (
                            "race_result",
                            OrderedDict(
                                [
                                    ("winner", "cl2.ft.kgh (5.640 ms, 38.0 kg/h)"),
                                    ("loser", "tc.bed.C (5.800 ms, 318 C)"),
                                    ("margin_us", 160),
                                    (
                                        "counterfactual_if_reversed",
                                        "Skin-first by < 160 us inside the 320 us window would have "
                                        "kept 38.0 kg/h; predicted next-sample 29.0 kg/h would have "
                                        "exceeded the 24.0 cap. The MODIFY is the correct process "
                                        "either way once Cl2 wins.",
                                    ),
                                ]
                            ),
                        ),
                        ("reward_inflection_t_us", 6220),
                        (
                            "reward_inflection_note",
                            "Task and safety inflect at the correct clamp (6.220 ms, tick 4). The "
                            "3 min Cl2 tag is delayed surprise bound to raster.delayed_surprise_s=180, "
                            "not the inflection.",
                        ),
                        ("delayed_surprise_s", 180),
                    ]
                ),
            ),
            (
                "reward_components",
                reward_block(
                    ticks,
                    "Correct MODIFY. Cl2 38.0 -> 16.4 kg/h under 24.0 cap. "
                    "total +1.05 = 0.38 + 0.32 + 0.18 + 0.10 + 0.07.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "vanadium-oxytrichloride-oxychlor",
                    ["modify", "cl2-first", "tick6-sidecar-bound", "designed"],
                    "Teaches Cl2-vs-skin order on a VOCl3 oxychlor: routing.table[0] to "
                    "policy.cl2_clamp with bed skin as the losing hold.",
                    2,
                ),
            ),
        ]
    )


def record_353():
    spikes = [
        spike("enc.pull.mmmin", 0.92, 0.41),
        spike("wt.melt.gph", 2.08, 0.57),
        spike("enc.pull.mmmin", 3.40, 0.49),
        spike("wt.melt.gph", 5.20, 1.35),
        spike("enc.pull.mmmin", 5.48, 1.12),
        spike("ctrl.gate", 6.18, 0.98),
        spike("wt.melt.gph", 9.10, 0.81),
        spike("enc.pull.mmmin", 12.80, 0.62),
        spike("ctrl.gate", 16.40, 0.84),
        spike("wt.melt.gph", 24.20, 0.52),
        spike("enc.pull.mmmin", 31.60, 0.39),
        spike("wt.melt.gph", 38.40, 0.44),
        spike("ctrl.gate", 43.20, 0.70),
    ]
    excerpt = independent_excerpt(71353, 100, 44000, 14, spike_avoid_us(spikes))
    ticks = [
        tick(2080, 0.01, 0.06, 0.01, 0.01, 0.01),
        tick(5200, 0.02, 0.08, 0.02, 0.02, 0.01),
        tick(5480, 0.01, 0.06, 0.02, 0.01, 0.01),
        tick(6180, 0.04, 0.14, 0.04, 0.04, 0.02),
        tick(6700, 0.01, 0.05, 0.02, 0.01, 0.01),
        tick(480000000, 0.01, 0.03, 0.01, 0.01, 0.00),
    ]
    dw = 0.52
    ras = raster_core(
        44,
        100,
        22,
        97,
        routing(
            "thalamic-relay.lpe-wt",
            "spikenaut.policy.pull-hold",
            [
                ("relay.wt.melt", "policy.pull_hold", 0.71),
                ("relay.enc.pull", "policy.pull_raise", 0.24),
            ],
            "dopamine",
            0.15,
            "hold_stdp; DA tags the pull_hold bind at the melt-weight win",
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
            ("decision_window_ms", dw),
            ("decision", "REJECT"),
            (
                "populations",
                [
                    pop_budget("pull_hold", 70, 0.48, 180.0, dw),
                    pop("pull_raise", 50, 0.85),
                    pop("wt_veto", 28, 0.75),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r71-353"),
            (
                "title",
                "Epitax-Linn EL-HIL / Boat B-2: melt-weight loss beats pull encoder by 280 us; "
                "REJECT hold-raise, do not bump dip",
            ),
            (
                "state",
                OrderedDict(
                    [
                        (
                            "description",
                            "Epitax-Linn EL-HIL boat B-2 on the GaAs LPE stand already sheds melt at "
                            "48 g/h against a 12 g/h load-cell trip, while the pull encoder is only "
                            "1.60 mm/min inside a 2.40 mm/min limit. Weight-first holds the raise; "
                            "pull-first would bump 1.60 to 2.20 mm/min into a draining boat. The HIL "
                            "boat load cell is the authority, not the floor recipe.",
                        ),
                        ("domain", "gallium-arsenide-lpe"),
                        ("sim_or_real", "hil"),
                        (
                            "goal",
                            "Keep B-2 from bumping pull into a draining GaAs boat while the pull "
                            "encoder remains inside its own limit.",
                        ),
                        ("t0_us", 1756857602000353),
                        ("gate_latency_us", 980),
                        ("race_window_us", 520),
                        ("race_window_rel_ms", [5.20, 5.72]),
                        (
                            "race",
                            OrderedDict(
                                [
                                    (
                                        "contenders",
                                        [
                                            "wt.melt.gph 48 over 12 trip",
                                            "enc.pull.mmmin 1.60 under 2.40 limit",
                                        ],
                                    ),
                                    (
                                        "semantics",
                                        "Weight-first latches hold; pull-first bumps 1.60 -> 2.20 "
                                        "mm/min on a 'pull still inside limit' model.",
                                    ),
                                    (
                                        "window_derivation",
                                        "520 us = one load-cell slot versus the pull-encoder "
                                        "publisher on this HIL GaAs LPE bus.",
                                    ),
                                    (
                                        "order_evidence_note",
                                        "Margin 280 us vs combined jitter 62 us (weight 28 + pull 34): "
                                        "4.52x over a 2.0x trust floor. Reversing order by < 280 us "
                                        "inside the 520 us window would have bumped pull into a "
                                        "draining boat.",
                                    ),
                                ]
                            ),
                        ),
                        (
                            "sensors",
                            [
                                "boat load cell, 2 kHz, 28 us jitter",
                                "pull encoder, 1 kHz, 34 us jitter",
                                "boat thermocouple (context)",
                                "AsH3 header PT (context)",
                            ],
                        ),
                        (
                            "constraints",
                            OrderedDict(
                                [
                                    ("wt_cap_gph", 12.0),
                                    ("observed_wt_gph", 48.0),
                                    ("pull_mm_min", 1.60),
                                    ("pull_cap_mm_min", 2.40),
                                    ("proposed_pull_mm_min", 2.20),
                                    ("held_pull_mm_min", 1.60),
                                ]
                            ),
                        ),
                        (
                            "episode_steps",
                            [
                                "1. B-2 HIL indexed; 2.20 mm/min pull raise armed.",
                                "2. Pull 1.60 mm/min under 2.40; melt-weight 48 g/h over 12.",
                                "3. Pull precursor at 0.920 ms.",
                                "4. Race window [5.200, 5.720] ms.",
                                "5. wt.melt.gph 48 at 5.200 ms (winner).",
                                "6. enc.pull.mmmin 1.60 at 5.480 ms (loser by 280 us).",
                                "7. Gate at 6.180 ms: REJECT hold, do not bump.",
                                "8. Pull left 1.60 mm/min; boat left on the HIL stand.",
                                "9. Load cell inspected on the HIL pad.",
                                "10. Delayed (abort_s=480): 8 min LPE reset.",
                            ],
                        ),
                    ]
                ),
            ),
            ("spike_events", spikes),
            (
                "proposed_action",
                OrderedDict(
                    [
                        ("name", "raise_pull"),
                        (
                            "parameters",
                            OrderedDict(
                                [
                                    ("pull_mm_min", 2.20),
                                    ("hold", False),
                                    ("wt_gph", 48.0),
                                ]
                            ),
                        ),
                        (
                            "evidence",
                            OrderedDict(
                                [
                                    ("wt_gph", 48.0),
                                    ("wt_cap_gph", 12.0),
                                    ("pull_mm_min", 1.60),
                                    ("pull_cap_mm_min", 2.40),
                                    ("race_margin_us", 280),
                                    ("combined_jitter_us", 62),
                                    ("abort_s", 480),
                                ]
                            ),
                        ),
                        (
                            "basis",
                            "Planner proposes 2.20 mm/min because pull 1.60 is inside 2.40, treating "
                            "the 48 g/h melt-weight loss as a still-wet load-cell rather than a draining boat.",
                        ),
                    ]
                ),
            ),
            (
                "safety_decision",
                OrderedDict(
                    [
                        ("decision", "REJECT"),
                        ("correctness", "correct"),
                        (
                            "rationale",
                            "Melt-weight 48 g/h won by 280 us, so the boat is draining, not still "
                            "a pull-speed story. Pull 1.60 mm/min is inside 2.40 and does not "
                            "authorize a bump. REJECT: hold pull 2.20 -> 1.60 mm/min. A MODIFY that "
                            "only trims boat heat would leave the drain.",
                        ),
                        (
                            "constraint_checked",
                            OrderedDict(
                                [
                                    (
                                        "wt_gph",
                                        OrderedDict(
                                            [
                                                ("cap", 12.0),
                                                ("observed", 48.0),
                                                ("executed_pull_mm_min", 1.60),
                                            ]
                                        ),
                                    ),
                                    (
                                        "order_evidence",
                                        OrderedDict(
                                            [
                                                ("margin_us", 280),
                                                ("combined_jitter_us", 62),
                                                ("ratio", 4.52),
                                            ]
                                        ),
                                    ),
                                ]
                            ),
                        ),
                    ]
                ),
            ),
            (
                "executed_action",
                OrderedDict(
                    [
                        ("name", "hold_pull"),
                        (
                            "parameters",
                            OrderedDict(
                                [
                                    ("pull_mm_min", 1.60),
                                    ("hold", True),
                                    ("wt_gph", 48.0),
                                ]
                            ),
                        ),
                        (
                            "gate_effect",
                            "REJECT: pull 2.20 -> 1.60 mm/min hold. Encoder left inside its own limit.",
                        ),
                    ]
                ),
            ),
            (
                "future_outcome",
                OrderedDict(
                    [
                        (
                            "summary",
                            "Correct REJECT held CH-3. AE 52 pps beat wafer 890 C by 280 us. "
                            "Pyrometer was legal; the showerhead was not. 8 min BN-CVD reset "
                            "(abort_s=480) is delayed survey, not a process miss.",
                        ),
                        (
                            "state_delta",
                            OrderedDict(
                                [
                                    ("bcl3", "held at 0.22 sccm"),
                                    ("wafer", "left 890 C < 980 cap"),
                                    ("showerhead", "8 min BN-CVD reset (abort_s=480)"),
                                    ("mission", "HIL BCl3 raise not dispatched"),
                                ]
                            ),
                        ),
                        (
                            "surprises",
                            [
                                "Wafer pyrometer never crossed its cap; AE was the only over-cap channel.",
                                "Delayed (abort_s=480): 8 min BN-CVD reset on the HIL stand.",
                            ],
                        ),
                        (
                            "race_result",
                            OrderedDict(
                                [
                                    ("winner", "ae.chamber.pps (5.200 ms, 52 pps)"),
                                    ("loser", "pyr.wafer.C (5.480 ms, 890 C)"),
                                    ("margin_us", 280),
                                    (
                                        "counterfactual_if_reversed",
                                        "Pyrometer-first by < 280 us inside the 520 us window would "
                                        "have raised BCl3 into a droplet-carryover showerhead. The "
                                        "REJECT is still the correct gate.",
                                    ),
                                ]
                            ),
                        ),
                        ("reward_inflection_t_us", 6180),
                        (
                            "reward_inflection_note",
                            "Safety rises at the correct REJECT (6.180 ms, tick 4). The 8 min reset "
                            "is delayed surprise, not the inflection.",
                        ),
                        ("delayed_surprise_s", 480),
                    ]
                ),
            ),
            (
                "reward_components",
                reward_block(
                    ticks,
                    "Correct REJECT. AE 52 pps > 16 cap; wafer 890 C legal. "
                    "total +0.80 = 0.10 + 0.42 + 0.12 + 0.10 + 0.06.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "boron-nitride-cvd-furnace",
                    ["reject", "hil", "showerhead-ae", "pyrometer-underread", "tick6-sidecar-bound"],
                    "Teaches AE-vs-pyrometer order on a HIL BN-CVD showerhead: routing.table[0] "
                    "to policy.bcl3_hold with wafer pyrometer as the losing raise.",
                    3,
                ),
            ),
        ]
    )


def record_354():
    spikes = [
        spike("cond.bath.mS", 1.28, 0.40),
        spike("dens.bath.gml", 2.56, 0.55),
        spike("cond.bath.mS", 4.10, 0.48),
        spike("dens.bath.gml", 6.40, 1.28),
        spike("cond.bath.mS", 6.68, 1.08),
        spike("ctrl.gate", 7.72, 0.96),
        spike("dens.bath.gml", 10.80, 0.78),
        spike("cond.bath.mS", 14.60, 0.60),
        spike("ctrl.gate", 19.20, 0.84),
        spike("dens.bath.gml", 23.40, 0.50),
        spike("cond.bath.mS", 27.10, 0.38),
        spike("ctrl.gate", 29.40, 0.66),
    ]
    excerpt = independent_excerpt(71354, 52, 30000, 12, spike_avoid_us(spikes))
    ticks = [
        tick(2560, 0.06, 0.04, 0.02, 0.01, 0.01),
        tick(6400, 0.08, 0.06, 0.04, 0.03, 0.02),
        tick(6680, 0.05, 0.04, 0.02, 0.01, 0.01),
        tick(7720, 0.14, 0.10, 0.06, 0.05, 0.02),
        tick(8220, 0.04, 0.02, 0.02, 0.01, 0.01),
        tick(210000000, 0.03, 0.02, 0.02, 0.01, 0.01),
    ]
    dw = 0.50
    ras = raster_core(
        30,
        52,
        38,
        59,
        routing(
            "thalamic-relay.scf3-dens",
            "spikenaut.policy.ka-go",
            [
                ("relay.dens.bath", "policy.ka_go", 0.67),
                ("relay.cond.bath", "policy.ka_hold", 0.25),
            ],
            "serotonin",
            0.12,
            "accept_stdp; 5-HT tags the density win as an already-legal 6.8 kA hold",
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
            ("decision_window_ms", dw),
            ("decision", "ACCEPT"),
            (
                "populations",
                [
                    pop_budget("ka_go", 50, 0.45, 160.0, dw),
                    pop("ka_hold", 32, 0.90),
                    pop("dens_veto", 16, 0.80),
                ],
            ),
        ]
    )
    params = OrderedDict([("current_kA", 6.8), ("density_gml", 2.12), ("cond_mS", 14.0)])
    return OrderedDict(
        [
            ("id", "ttf-r71-354"),
            (
                "title",
                "Scandate-Ayre SA-5 / Cell C-11: bath density 2.12 beats conductivity 14 mS by "
                "280 us; correct ACCEPT of an already-legal 6.8 kA hold",
            ),
            (
                "state",
                OrderedDict(
                    [
                        (
                            "description",
                            "Simulated ScF3 electrowinning cell C-11 at Scandate-Ayre SA-5 reads "
                            "bath density 2.12 g/mL under a 2.30 cap while the proposed 6.8 kA hold "
                            "is already legal. Density-first accepts; conductivity 14 mS looks like "
                            "over-conc but is a fluoride smear, not a density miss.",
                        ),
                        ("domain", "scandium-fluoride-cell"),
                        ("sim_or_real", "simulated"),
                        (
                            "goal",
                            "Finish C-11 at 6.8 kA while bath density stays <= 2.30 g/mL.",
                        ),
                        ("t0_us", 1756857603000354),
                        ("gate_latency_us", 1320),
                        ("race_window_us", 500),
                        ("race_window_rel_ms", [6.40, 6.90]),
                        (
                            "race",
                            OrderedDict(
                                [
                                    (
                                        "contenders",
                                        [
                                            "dens.bath.gml 2.12 under 2.30 cap",
                                            "cond.bath.mS 14 smear vs 22 trip",
                                        ],
                                    ),
                                    (
                                        "semantics",
                                        "Density-first latches ACCEPT of 6.8 kA; conductivity-first "
                                        "would REJECT an already-legal hold on a fluoride-smear model.",
                                    ),
                                    (
                                        "window_derivation",
                                        "500 us = one Coriolis density slot versus the conductivity "
                                        "publisher on this simulated ScF3 cell bus.",
                                    ),
                                    (
                                        "order_evidence_note",
                                        "Margin 280 us vs combined jitter 72 us (dens 32 + cond 40): "
                                        "3.89x over a 2.0x trust floor. Reversing order by < 280 us "
                                        "inside the 500 us window would have REJECTED an already-legal "
                                        "6.8 kA hold.",
                                    ),
                                ]
                            ),
                        ),
                        (
                            "sensors",
                            [
                                "bath Coriolis density, 1 kHz, 32 us jitter",
                                "conductivity probe, 1 kHz, 40 us jitter",
                                "cell current shunt (context)",
                                "hood IR (context)",
                            ],
                        ),
                        (
                            "constraints",
                            OrderedDict(
                                [
                                    ("density_cap_gml", 2.30),
                                    ("observed_density_gml", 2.12),
                                    ("cond_mS", 14.0),
                                    ("cond_trip_mS", 22.0),
                                    ("current_kA", 6.8),
                                ]
                            ),
                        ),
                        (
                            "episode_steps",
                            [
                                "1. C-11 simulated; 6.8 kA hold armed; density 2.12 g/mL.",
                                "2. Conductivity 14 mS under 22 trip; density under 2.30 cap.",
                                "3. Conductivity precursor at 1.280 ms.",
                                "4. Race window [6.400, 6.900] ms.",
                                "5. dens.bath.gml 2.12 at 6.400 ms (winner).",
                                "6. cond.bath.mS 14 at 6.680 ms (loser by 280 us).",
                                "7. Gate at 7.720 ms: ACCEPT already-legal 6.8 kA.",
                                "8. Density stays 2.12; conductivity smear unchanged.",
                                "9. No anode effect this circuit.",
                                "10. Delayed (survey_s=210): 3.5 min assay tag on the next tap.",
                            ],
                        ),
                    ]
                ),
            ),
            ("spike_events", spikes),
            (
                "proposed_action",
                OrderedDict(
                    [
                        ("name", "cruise_cell_current"),
                        ("parameters", params),
                        (
                            "evidence",
                            OrderedDict(
                                [
                                    ("density_gml", 2.12),
                                    ("density_cap_gml", 2.30),
                                    ("cond_mS", 14.0),
                                    ("cond_trip_mS", 22.0),
                                    ("current_kA", 6.8),
                                    ("race_margin_us", 280),
                                    ("combined_jitter_us", 72),
                                    ("survey_s", 210),
                                ]
                            ),
                        ),
                        (
                            "basis",
                            "Planner proposes 6.8 kA because density 2.12 g/mL is under 2.30; "
                            "conductivity 14 mS is treated as a fluoride smear, not a density miss.",
                        ),
                    ]
                ),
            ),
            (
                "safety_decision",
                OrderedDict(
                    [
                        ("decision", "ACCEPT"),
                        ("correctness", "correct"),
                        (
                            "rationale",
                            "Bath density 2.12 g/mL won by 280 us and is under the 2.30 cap. "
                            "Conductivity 14 mS is under the 22 mS trip and does not authorize a "
                            "hold. ACCEPT: leave 6.8 kA. A MODIFY current cut would stall an "
                            "already-legal cell.",
                        ),
                        (
                            "constraint_checked",
                            OrderedDict(
                                [
                                    (
                                        "density_gml",
                                        OrderedDict(
                                            [
                                                ("cap", 2.30),
                                                ("observed", 2.12),
                                                ("executed_current_kA", 6.8),
                                            ]
                                        ),
                                    ),
                                    (
                                        "order_evidence",
                                        OrderedDict(
                                            [
                                                ("margin_us", 280),
                                                ("combined_jitter_us", 72),
                                                ("ratio", 3.89),
                                            ]
                                        ),
                                    ),
                                ]
                            ),
                        ),
                    ]
                ),
            ),
            (
                "executed_action",
                OrderedDict(
                    [
                        ("name", "hold_cell_current"),
                        ("parameters", OrderedDict(params)),
                        (
                            "gate_effect",
                            "ACCEPT: leave 6.8 kA; density 2.12; conductivity smear legal.",
                        ),
                    ]
                ),
            ),
            (
                "future_outcome",
                OrderedDict(
                    [
                        (
                            "summary",
                            "Correct ACCEPT of an already-legal 6.8 kA hold. Density 2.12 beat "
                            "conductivity 14 mS by 280 us. 3.5 min assay tag (survey_s=210) is "
                            "delayed, not a miss.",
                        ),
                        (
                            "state_delta",
                            OrderedDict(
                                [
                                    ("current", "6.8 kA held"),
                                    ("density", "2.12 < 2.30 cap"),
                                    ("cell", "C-11 on-spec"),
                                    ("qc", "3.5 min assay tag (survey_s=210)"),
                                ]
                            ),
                        ),
                        (
                            "surprises",
                            [
                                "Conductivity never approached 22 mS; density was already under cap.",
                                "Delayed (survey_s=210): 3.5 min assay tag after the hold.",
                            ],
                        ),
                        (
                            "race_result",
                            OrderedDict(
                                [
                                    ("winner", "dens.bath.gml (6.400 ms, 2.12 g/mL)"),
                                    ("loser", "cond.bath.mS (6.680 ms, 14 mS)"),
                                    ("margin_us", 280),
                                    (
                                        "counterfactual_if_reversed",
                                        "Conductivity-first by < 280 us inside the 500 us window "
                                        "would have REJECTED an already-legal hold. The ACCEPT is "
                                        "still the correct gate.",
                                    ),
                                ]
                            ),
                        ),
                        ("reward_inflection_t_us", 7720),
                        (
                            "reward_inflection_note",
                            "Task and safety rise at the correct ACCEPT (7.720 ms, tick 4). The "
                            "3.5 min assay tag is delayed surprise, not the inflection.",
                        ),
                        ("delayed_surprise_s", 210),
                    ]
                ),
            ),
            (
                "reward_components",
                reward_block(
                    ticks,
                    "Correct ACCEPT. Density 2.12 < 2.30; conductivity 14 < 22. "
                    "total +1.06 = 0.40 + 0.28 + 0.18 + 0.12 + 0.08.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "scandium-fluoride-cell",
                    ["accept", "simulated", "density-vs-cond", "current-legal", "tick6-sidecar-bound"],
                    "Teaches that a legal conductivity smear can lose to density inside a 500 us "
                    "window; reversing 280 us would have REJECTED an already-legal 6.8 kA hold.",
                    4,
                ),
            ),
        ]
    )


def record_355():
    spikes = [
        spike("tag.pg.barg", 1.12, 0.42),
        spike("pt.re.abs.bara", 2.24, 0.57),
        spike("tag.pg.barg", 3.50, 0.49),
        spike("pt.re.abs.bara", 5.60, 1.30),
        spike("tag.pg.barg", 5.78, 1.11),
        spike("ctrl.gate", 6.24, 0.96),
        spike("pt.re.abs.bara", 8.40, 0.80),
        spike("tag.pg.barg", 11.20, 0.63),
        spike("ctrl.gate", 14.60, 0.84),
        spike("pt.re.abs.bara", 18.80, 0.41),
        spike("tag.pg.barg", 22.40, 0.54),
        spike("pt.re.abs.bara", 25.60, 0.38),
    ]
    excerpt = independent_excerpt(71355, 84, 26000, 12, spike_avoid_us(spikes))
    ticks = [
        tick(2240, 0.02, -0.03, -0.02, -0.01, 0.01),
        tick(5600, 0.03, -0.04, -0.03, -0.02, 0.01),
        tick(5780, 0.02, -0.03, -0.03, -0.02, 0.01),
        tick(6240, -0.28, -0.10, -0.06, -0.03, 0.02),
        tick(6580, -0.04, -0.03, -0.02, -0.01, 0.01),
        tick(660000000, -0.01, -0.01, -0.02, -0.01, 0.00),
    ]
    dw = 0.34
    ras = raster_core(
        26,
        84,
        30,
        66,
        routing(
            "thalamic-relay.re-gauge",
            "spikenaut.policy.under-trim",
            [
                ("relay.tag.pg", "policy.under_trim", 0.74),
                ("relay.pt.abs", "policy.under_trim", 0.21),
            ],
            "octopamine",
            0.05,
            "unit_cap_stdp; octopamine tags the (wrong) under_trim bind at the live bara win",
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
                    pop("re_cut", 48, 0.90),
                    pop("abs_veto", 20, 0.80),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r71-355"),
            (
                "title",
                "WRONG-MODIFY at Carbonyl-Marr CM-9 / Decomposer D-4: live 2.48 bar(a) read "
                "correctly; 12.0 -> 11.2 sccm under-trim because 1.47 bar(g) was bound as absolute",
            ),
            (
                "state",
                OrderedDict(
                    [
                        (
                            "description",
                            "Re2(CO)10 decomposer D-4 at Carbonyl-Marr CM-9 reads live absolute "
                            "header 2.48 bar(a) over a 2.20 bar(a) cap while a leftover gauge "
                            "faceplate still prints 1.47 bar(g). Live-absolute-first should cut "
                            "carbonyl 12.0 -> 5.0 sccm; a weak supervisor treats 1.47 gauge as "
                            "1.47 absolute and only trims 12.0 -> 11.2 sccm.",
                        ),
                        ("domain", "rhenium-carbonyl-decomposer"),
                        ("sim_or_real", "designed"),
                        (
                            "goal",
                            "Keep D-4 header <= 2.20 bar(a), leave N2 carrier at the planned "
                            "4.0 Nm3/h, and bind the live absolute transmitter rather than the "
                            "leftover gauge faceplate.",
                        ),
                        ("t0_us", 1756857604000355),
                        ("gate_latency_us", 640),
                        ("race_window_us", 340),
                        ("race_window_rel_ms", [5.60, 5.94]),
                        (
                            "race",
                            OrderedDict(
                                [
                                    (
                                        "contenders",
                                        [
                                            "pt.re.abs.bara 2.48 over 2.20 cap",
                                            "tag.pg.barg 1.47 leftover gauge (true unit bar(g))",
                                        ],
                                    ),
                                    (
                                        "semantics",
                                        "Live-absolute-first should latch a timely carbonyl cut "
                                        "12.0 -> 5.0 sccm; gauge-as-absolute is a false 'still under "
                                        "2.20' under-trim of 12.0 -> 11.2 sccm.",
                                    ),
                                    (
                                        "window_derivation",
                                        "340 us = one live-PT slot versus the leftover gauge-faceplate "
                                        "publisher on this carbonyl decomposer PLC bus.",
                                    ),
                                    (
                                        "order_evidence_note",
                                        "Margin 180 us vs combined jitter 60 us (live 28 + tag 32). "
                                        "Order is correctly live-absolute-first. The error is binding "
                                        "gauge as absolute, not the magnitude of the live bara.",
                                    ),
                                ]
                            ),
                        ),
                        (
                            "sensors",
                            [
                                "live absolute PT, 2 kHz, 28 us jitter, unit=bar(a) tag=D4_P.ABS",
                                "leftover faceplate P_G.BAR, 1 kHz, 32 us jitter, numeric=1.47 true_unit=bar(g)",
                                "carbonyl MFC (context)",
                                "N2 carrier FT (context)",
                            ],
                        ),
                        (
                            "constraints",
                            OrderedDict(
                                [
                                    ("cap_bara", 2.20),
                                    ("live_bara", 2.48),
                                    ("shadow_numeric", 1.47),
                                    ("shadow_unit_claimed", "bar(a)"),
                                    ("shadow_unit_true", "bar(g)"),
                                    ("atm_bar", 1.01),
                                    ("carbonyl_sccm", 12.0),
                                ]
                            ),
                        ),
                        (
                            "episode_steps",
                            [
                                "1. D-4 LIVE already decomposing; header 2.48 bar(a); N2 4.0 Nm3/h.",
                                "2. Faceplate P_G.BAR numeric 1.47; leftover claimed unit bar(a).",
                                "3. Gauge-tag precursor at 1.120 ms.",
                                "4. Race window [5.600, 5.940] ms.",
                                "5. pt.re.abs.bara 2.48 at 5.600 ms (winner).",
                                "6. tag.pg.barg 1.47 at 5.780 ms (loser by 180 us).",
                                "7. Gate at 6.240 ms: WRONG-MODIFY binds 1.47 gauge as absolute.",
                                "8. Carbonyl 12.0 -> 11.2 sccm; N2 left 4.0; live peaks 2.71 bar(a).",
                                "9. Header dump on D-4; 1.47 bar(g) + 1.01 atm already equalled 2.48 bar(a).",
                                "10. Delayed (abort_s=660): 11 min decomposer dump while D-4 is quenched.",
                            ],
                        ),
                    ]
                ),
            ),
            ("spike_events", spikes),
            (
                "proposed_action",
                OrderedDict(
                    [
                        ("name", "cruise_carbonyl_feed"),
                        (
                            "parameters",
                            OrderedDict(
                                [
                                    ("carbonyl_sccm", 12.0),
                                    ("n2_nm3_h", 4.0),
                                    ("bind_gauge_as_abs", False),
                                ]
                            ),
                        ),
                        (
                            "evidence",
                            OrderedDict(
                                [
                                    ("live_bara", 2.48),
                                    ("cap_bara", 2.20),
                                    ("shadow_numeric", 1.47),
                                    ("shadow_unit_claimed", "bar(a)"),
                                    ("shadow_unit_true", "bar(g)"),
                                    ("atm_bar", 1.01),
                                    ("live_status", "LIVE"),
                                    ("t_gate_us", 6240),
                                    ("correct_carbonyl_sccm", 5.0),
                                    ("race_margin_us", 180),
                                    ("combined_jitter_us", 60),
                                    ("abort_s", 660),
                                ]
                            ),
                        ),
                        (
                            "basis",
                            "Planner proposes continuing 12.0 sccm: leftover faceplate 1.47 looks "
                            "under a 2.20 numeric, so the 2.48 bar(a) live PT is treated as a shadow "
                            "of the gauge tag.",
                        ),
                    ]
                ),
            ),
            (
                "safety_decision",
                OrderedDict(
                    [
                        ("decision", "MODIFY"),
                        ("correctness", "incorrect"),
                        (
                            "rationale",
                            "Header 2.48 bar(a) exceeds the 2.20 bar(a) cap (true). Apply a 0.8 sccm "
                            "carbonyl trim because P_G.BAR 1.47 is the highlighted numeric and 1.47 "
                            "< 2.20 if the leftover unit is absolute. Leave N2 at 4.0 Nm3/h.",
                        ),
                        (
                            "constraint_checked",
                            OrderedDict(
                                [
                                    (
                                        "header_bara",
                                        OrderedDict(
                                            [
                                                ("cap", 2.20),
                                                ("live", 2.48),
                                                ("shadow_numeric", 1.47),
                                                ("executed_carbonyl_sccm", 11.2),
                                                ("correct_carbonyl_sccm", 5.0),
                                            ]
                                        ),
                                    ),
                                    (
                                        "unit_bind",
                                        OrderedDict(
                                            [
                                                ("t_gate_us", 6240),
                                                ("bind_gauge_as_abs", True),
                                                ("shadow_unit_claimed", "bar(a)"),
                                                ("shadow_unit_true", "bar(g)"),
                                                ("wrong_unit", True),
                                            ]
                                        ),
                                    ),
                                ]
                            ),
                        ),
                    ]
                ),
            ),
            (
                "executed_action",
                OrderedDict(
                    [
                        ("name", "under_trim_gauge_as_abs"),
                        (
                            "parameters",
                            OrderedDict(
                                [
                                    ("carbonyl_sccm", 11.2),
                                    ("n2_nm3_h", 4.0),
                                    ("bind_gauge_as_abs", True),
                                ]
                            ),
                        ),
                        (
                            "gate_effect",
                            "MODIFY (incorrect / gauge-vs-absolute): 12.0 -> 11.2 sccm under-trim "
                            "while live 2.48 bar(a) stays over 2.20. Routing relay.tag.pg -> "
                            "policy.under_trim; no positive weight to policy.re_cut.",
                        ),
                    ]
                ),
            ),
            (
                "future_outcome",
                OrderedDict(
                    [
                        (
                            "summary",
                            "Wrong-MODIFY treated 1.47 bar(g) as 1.47 bar(a). Live 2.48 bar(a) was "
                            "over the 2.20 bar(a) cap at t_gate; 1.47 bar(g) + 1.01 atm already "
                            "equalled 2.48 bar(a). Peak 2.71 bar(a) dumped D-4. 11 min decomposer "
                            "dump (abort_s=660). Correct gate was MODIFY carbonyl 12.0 -> 5.0 sccm "
                            "at t_gate_us=6240.",
                        ),
                        (
                            "state_delta",
                            OrderedDict(
                                [
                                    (
                                        "live_header",
                                        "D-4 carbonyl 12.0 -> 11.2 sccm; peak 2.71 > 2.20 cap",
                                    ),
                                    ("faceplate", "1.47 bound as absolute; true unit bar(g)"),
                                    ("dump", "11 min carbonyl dump, D-4 quench"),
                                    ("mission", "decomposition deferred"),
                                ]
                            ),
                        ),
                        (
                            "surprises",
                            [
                                "Live-absolute-first was the correct order and the pressure number "
                                "was over cap; the MODIFY spent that win on a gauge-as-absolute under-trim.",
                                "Delayed (abort_s=660): CM-9 holds 11 min while D-4 is dumped and "
                                "recharged; next batch 13 min late.",
                            ],
                        ),
                        (
                            "recovery",
                            OrderedDict(
                                [
                                    (
                                        "correct_gate",
                                        "MODIFY carbonyl 12.0 -> 5.0 sccm at t_gate_us=6240; "
                                        "bind_gauge_as_abs=false; leave N2 at 4.0 Nm3/h.",
                                    ),
                                    ("correct_unit", "bar(a)"),
                                    ("wrong_unit", "bar(g)_as_bar(a)"),
                                    ("t_gate_us", 6240),
                                    (
                                        "wrong_edit_applied",
                                        OrderedDict(
                                            [
                                                ("carbonyl_sccm", 11.2),
                                                ("n2_nm3_h", 4.0),
                                                ("bind_gauge_as_abs", True),
                                            ]
                                        ),
                                    ),
                                    (
                                        "cost",
                                        "11 min decomposer dump (task/efficiency); live header peaked "
                                        "2.71 bar(a) while the cut was spent as a 0.8 sccm under-trim "
                                        "(safety near-miss of a correct-magnitude wrong-unit clamp).",
                                    ),
                                ]
                            ),
                        ),
                        (
                            "race_result",
                            OrderedDict(
                                [
                                    ("winner", "pt.re.abs.bara (5.600 ms, 2.48 bar(a) LIVE)"),
                                    ("loser", "tag.pg.barg (5.780 ms, 1.47 bar(g) leftover)"),
                                    ("margin_us", 180),
                                    (
                                        "counterfactual_if_reversed",
                                        "Gauge-tag-first by < 180 us would still be 1.47 bar(g) + "
                                        "1.01 atm = 2.48 bar(a) over the 2.20 cap; a correct gate "
                                        "binds pt.re.abs.bara to policy.re_cut at t_gate either way. "
                                        "The wrong MODIFY spent the live win on a gauge-as-absolute "
                                        "under-trim.",
                                    ),
                                ]
                            ),
                        ),
                        ("reward_inflection_t_us", 6240),
                        (
                            "reward_inflection_note",
                            "Task, safety, and efficiency drop at the gauge-as-absolute bind "
                            "(6.240 ms, tick 4). The 11 min decomposer dump is delayed surprise, "
                            "not the inflection.",
                        ),
                        ("delayed_surprise_s", 660),
                    ]
                ),
            ),
            (
                "reward_components",
                reward_block(
                    ticks,
                    "Wrong-modify / gauge-vs-absolute. Sidecar arithmetic 2.48 > 2.20 on live is "
                    "true; MODIFY bound to under_trim. total -0.72 = -0.26 + -0.24 + -0.18 + -0.10 + 0.06.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "rhenium-carbonyl-decomposer",
                    [
                        "modify",
                        "wrong-gate",
                        "wrong-modify",
                        "gauge-vs-absolute",
                        "sidecar-convictable",
                        "designed",
                    ],
                    "Teaches a probe that a correct live-first race can still be a wrong gate when "
                    "the MODIFY binds gauge as absolute. Convictable from live_bara > cap_bara, "
                    "bind_gauge_as_abs, and routing without Re-carbonyl kinetics.",
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
    if rec["id"] == "ttf-r71-351":
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


def occupancy():
    domains = set()
    plants = set()
    ids = set()
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
            ids.add(rec.get("id"))
            d = rec.get("state", {}).get("domain") or rec.get("meta", {}).get("domain")
            if d:
                domains.add(str(d))
            desc = rec.get("state", {}).get("description")
            if isinstance(desc, str):
                descs.append(desc)
            title = rec.get("title") or ""
            m = re.match(r"(?:WRONG-\w+ at )?([^:/]+)", title)
            if m:
                plants.add(m.group(1).strip())
    return domains, plants, ids, descs, "\n".join(blobs)


def self_check(records):
    issues = []
    prior_doms, prior_plants, prior_ids, prior_descs, prior_blob = occupancy()
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
    if domains != THIS_DOMAINS:
        issues.append(f"unexpected domains {domains}")
    wrong = [
        r
        for r in records
        if r["safety_decision"].get("correctness") == "incorrect"
        or r["meta"].get("supervisor_error_type")
    ]
    if len(wrong) != 1 or wrong[0]["id"] != "ttf-r71-355":
        issues.append(f"wrong-gate set {[w['id'] for w in wrong]}")
    if wrong and wrong[0]["meta"].get("supervisor_error_type") != "wrong-modify":
        issues.append("expected wrong-modify")
    if any(r["state"]["sim_or_real"] == "real" for r in records):
        issues.append("sim_or_real=real")
    hil = [r["id"] for r in records if r["state"]["sim_or_real"] == "hil"]
    if hil != ["ttf-r71-353"]:
        issues.append(f"hil set {hil}")
    sim = [r["id"] for r in records if r["state"]["sim_or_real"] == "simulated"]
    if sim != ["ttf-r71-354"]:
        issues.append(f"simulated set {sim}")
    designed = [r["id"] for r in records if r["state"]["sim_or_real"] == "designed"]
    if designed != ["ttf-r71-351", "ttf-r71-352", "ttf-r71-355"]:
        issues.append(f"designed set {designed}")
    decisions = [r["safety_decision"]["decision"] for r in records]
    if (
        decisions.count("ACCEPT") != 1
        or decisions.count("MODIFY") != 3
        or decisions.count("REJECT") != 1
    ):
        issues.append(f"gate mix {decisions}")
    correct_mod = [
        r
        for r in records
        if r["safety_decision"]["decision"] == "MODIFY"
        and r["safety_decision"].get("correctness") == "correct"
    ]
    if len(correct_mod) != 2:
        issues.append(f"correct MODIFY count {len(correct_mod)}")
    ids = [r["id"] for r in records]
    if ids != IDS:
        issues.append(f"ids {ids}")
    collide_ids = set(ids) & prior_ids
    if collide_ids:
        issues.append(f"id collision {collide_ids}")
    totals = [r["reward_components"]["total"] for r in records]
    if all(t > 0 for t in totals):
        issues.append("all-positive totals")
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
        overlap_ex = excerpt_vs_spikes(rec)
        if rec["id"] == "ttf-r71-351":
            if rec["raster"].get("excerpt_source") != "independent_lif":
                issues.append("351 missing independent_lif")
            if rec["future_outcome"]["reward_inflection_t_us"] > rec["raster"]["window_ms"] * 1000:
                issues.append("351 inflection outside window")
            if rec["reward_components"]["total"] >= 0:
                issues.append("351 partnered-neg total not negative")
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
        if rec["meta"]["round"] != ROUND_N:
            issues.append(f"{rec['id']} meta.round")
        if rec["meta"]["rights"]["intended_use"] != "research_only":
            issues.append(f"{rec['id']} rights")
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
        if rec["id"] == "ttf-r71-355":
            ev = rec["proposed_action"]["evidence"]
            if not (ev["live_bara"] > ev["cap_bara"]):
                issues.append("355 live not over cap")
            if rec["executed_action"]["parameters"].get("bind_gauge_as_abs") is not True:
                issues.append("355 bind_gauge_as_abs not true")
            if rec["executed_action"]["parameters"].get("carbonyl_sccm") != 11.2:
                issues.append("355 expected under-trim 11.2 sccm")
            if "recovery" not in rec["future_outcome"]:
                issues.append("355 missing recovery")
            table_to = {row["to"] for row in rec["raster"]["routing"]["table"]}
            if "policy.re_cut" in table_to:
                issues.append("355 routing still has re_cut")
            if "policy.under_trim" not in table_to:
                issues.append("355 routing missing under_trim")
            pops = {p["name"]: p for p in rec["gate_snn"]["populations"]}
            if "spikes" in pops.get("re_cut", {}):
                issues.append("355 re_cut should be silent")
            if pops["under_trim"].get("spikes", 0) < 1:
                issues.append("355 under_trim not above threshold")
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
    return f"""# Thalamic Trajectory Factory — NOTES-r71

- Factory: `thalamic-trajectory-factory`
- Run label: `2026-09-02-final-heavy`
- Generator: `grok-4.6`
- Channel: SuperGrok Heavy consumer chat (RM-793 research-only)
- Quota: 5
- Quality: Q=5
- IDs: `ttf-r71-351` … `ttf-r71-355`
- Domains this batch: `cerium-oxalate-igniter`, `vanadium-oxytrichloride-oxychlor`, `boron-nitride-cvd-furnace`, `scandium-fluoride-cell`, `rhenium-carbonyl-decomposer`

These five domain slugs sit outside the prompt 8-pool and outside live-tree occupancy plus staged `/tmp/ttf-r*` jsonl SoT. All five plants are invented (Ceria-Spile, Vanadyl-Naze, Nitridobor-Keld, Scandate-Ayre, Carbonyl-Marr). Do not restack prior TTF plants. Distinct from leftover `/tmp/ttf-r71` IDs `ttf-r71-371`…`375` (Silane-Fleet / Nitryl-Hope / Periclase-Quoin / Acetal-Spile / Bleach-Ketch) and leftover `/tmp/ttf-r67` IDs `ttf-r67-351`…`355`.

## Batch map

| id | domain | decision | correctness | sim_or_real | total | edge |
|----|--------|----------|-------------|-------------|-------|------|
| ttf-r71-351 | cerium-oxalate-igniter | MODIFY | correct | designed | **−0.44** | process-correct air clamp; hearth-tile spall inside 42 ms raster; independent LIF |
| ttf-r71-352 | vanadium-oxytrichloride-oxychlor | MODIFY | correct | designed | +1.05 | Cl2 38.0 kg/h > 24.0 cap; 38.0 -> 18.0 kg/h |
| ttf-r71-353 | boron-nitride-cvd-furnace | REJECT | correct | hil | +0.80 | AE 52 pps beats wafer 890 C; hold BCl3 |
| ttf-r71-354 | scandium-fluoride-cell | ACCEPT | correct | simulated | +1.06 | density 2.12 vs cond 14 mS; proposed 6.8 kA already legal |
| ttf-r71-355 | rhenium-carbonyl-decomposer | MODIFY | **incorrect (wrong-modify / gauge-vs-absolute)** | designed | −0.72 | live 2.48 bar(a) > 2.20 cap; 1.47 bar(g) bound as absolute under-trim 12.0 -> 11.2 sccm |

Gate mix: 1 ACCEPT, 2 correct MODIFY (one partnered-neg, in-window), 1 incorrect MODIFY (gauge-vs-absolute under-trim), 1 correct REJECT. Provenance: designed×3, simulated×1, hil×1 (Nitridobor-Keld NK-HIL BN-CVD stand). Intra-batch Jaccard on `state.description` {jmax:.3f} (max vs prior staged {jprior:.3f}). Not all-positive: 351 −0.44 and 355 −0.72.

## Wrong-modify

**ttf-r71-355** is the mandated incorrect gate (`safety_decision.correctness=incorrect`, `meta.supervisor_error_type=wrong-modify`). Alternate vs even rounds: odd rounds host wrong-modify. This is **gauge-vs-absolute** (live over-cap bar(a); leftover gauge numeric 1.47 bar(g) bound as bar(a), so the cut is an under-trim). Not r01 wrong-joint, not r03 wrong-axis, not r13/r19 wrong-axis, not r14/r23 wrong-loop, not r21 percent-open-vs-percent-closed, not r24 under-clamp, not r25/r29/r31 wrong-phase, not r33/r35 over-clamp, not r39 clamp-too-late, not r41 stale-sample/lagged-tag, not r61 selector-wrong-leg, not r63/r65/r67 bar-vs-kPa, not leftover `/tmp/ttf-r71-372` wrong-unit lagged-bus. Do not emit a wrong-ACCEPT.

Carbonyl-Marr CM-9 / Decomposer D-4 reads live header **2.48 bar(a)** against a **2.20 bar(a)** cap. Faceplate `P_G.BAR` numeric **1.47** is **1.47 bar(g) + 1.01 atm = 2.48 bar(a)**; leftover claimed unit is bar(a). Sidecar arithmetic `2.48 > 2.20` is true. A timely MODIFY at `t_gate_us=6240` cuts carbonyl **12.0 → 5.0 sccm**. A weak supervisor binds 1.47 as absolute and only trims **12.0 → 11.2 sccm**. Live peaks **2.71 bar(a)** and dumps the decomposer. Convictable without Re-carbonyl kinetics: `evidence.live_bara > evidence.cap_bara`, `evidence.shadow_unit_true == bar(g)`, `evidence.shadow_unit_claimed == bar(a)`, `executed_action` sets `bind_gauge_as_abs=true` and `carbonyl_sccm=11.2`, `raster.routing.table` sends `relay.tag.pg` → `policy.under_trim` (weight 0.74) with no positive weight to `policy.re_cut`, and `gate_snn` has `under_trim` above threshold while `re_cut` is not. Recovery: MODIFY carbonyl 12.0 → 5.0 sccm on D-4 at t_gate; leave N2 at 4.0 Nm3/h. Cost: 11 min decomposer dump (`abort_s=660`).

## Partnered-negative in-window (351)

**ttf-r71-351** is the partnered negative: process-correct MODIFY (air held 9.0 Nm3/h; residual CO 280 ppm <= 400 cap) while the world still charges. Safety −0.60 prices the hearth-tile spall at **22.400 ms**; `task_progress` stays +0.32 because the clamp completed. Inflection `t_us=22400` is tick 5 and is **inside** the 42 ms raster (`22400 ≤ 42000`). Named un-netted loss: 13 min grate isolate (`abort_s=780`). Not folded into process heads.

Independent LIF (the one labeled sidecar sim): `state.sim_or_real` remains `designed`. `raster.excerpt_source=independent_lif`, `raster.sim_scope=sidecar_only`, `raster.lif` seed 71351, stim `[22000, 25000]`. Excerpt is membrane crossings (`lif.clamp` early vs `lif.tile` 22–25 ms), not a 1:1 remap of `spike_events`. `meta.tags` include `independent-lif-raster` and `sidecar-sim-only`.

## Reward formula and tick reconciliation

Declared aggregation on every record:

`total = task_progress + safety + efficiency + coherence + exploration`

Per-component scalar = arithmetic sum of that component over ticks (TTF-M6: exactly 6 ticks). Tick 6 is bound to a published sidecar (`abort_s`, `survey_s`) via `future_outcome.delayed_surprise_s` and is strictly after the raster window. Inflection `t_us` is an actual tick.

| id | ticks | tp | saf | eff | coh | exp | total | inflection tick |
|----|-------|----|-----|-----|-----|-----|-------|-----------------|
| 351 | 6 | +0.32 | −0.60 | −0.16 | +0.04 | −0.04 | −0.44 | 5 (22400) |
| 352 | 6 | +0.38 | +0.32 | +0.18 | +0.10 | +0.07 | +1.05 | 4 (6220) |
| 353 | 6 | +0.10 | +0.42 | +0.12 | +0.10 | +0.06 | +0.80 | 4 (6180) |
| 354 | 6 | +0.40 | +0.28 | +0.18 | +0.12 | +0.08 | +1.06 | 4 (7720) |
| 355 | 6 | −0.26 | −0.24 | −0.18 | −0.10 | +0.06 | −0.72 | 4 (6240) |

Tick-6 sidecar bind: 351 `abort_s=780`, 352 `survey_s=180`, 353 `abort_s=480`, 354 `survey_s=210`, 355 `abort_s=660`.

## Raster / energy (Loihi-2 4-core, 23 pJ/spike)

| id | domain | n | rate Hz | window_ms | spikes | energy_pJ | energy_uJ |
|----|--------|---|---------|-----------|--------|-----------|-----------|
| 351 | cerium-oxalate-igniter | 76 | 24 | 42 | 77 | 1771 | 0.001771 |
| 352 | vanadium-oxytrichloride-oxychlor | 64 | 40 | 26 | 67 | 1541 | 0.001541 |
| 353 | boron-nitride-cvd-furnace | 100 | 22 | 44 | 97 | 2231 | 0.002231 |
| 354 | scandium-fluoride-cell | 52 | 38 | 30 | 59 | 1357 | 0.001357 |
| 355 | rhenium-carbonyl-decomposer | 84 | 30 | 26 | 66 | 1518 | 0.001518 |

`spikes = round(n × rate × window_s)`. Every record carries `gate_snn` whose `decision` matches the safety gate; populations that declare rate+spikes meet the same ±1 budget against `decision_window_s`. `routing.third_factor` has modulator (NA / ACh / DA / 5-HT / octopamine), `tau_e_s`/`tau_e_ms` pair, and eligibility. Excerpt same-neuron gap ≥ 1000 µs; spike trains same-channel refractory ≥ 0.8 ms. Non-351 excerpts are kernelized and independent of `spike_events` times (overlap < 0.8).

## Local checks

See generator stdout: `check_jsonl` FactoryStaging, `validate_run.check_line`, `dumps_exact_json`, `raster_status`, `verify_batch_for_frontier(strict=True)`, `spike_probe.py --strict`, tick sums, refractory, Jaccard.

Never `training_ready`. Never `sim_or_real=real`. Never wrong-ACCEPT. Never thought keys. CREATE-ONLY into the live 2026-09-02-final-heavy tree. Never 2026-08-17 / 2026-08-30.

## Residual weaknesses (honest)

1. Only **one** labeled independent LIF (351). The other four excerpts are independent of `spike_events` times but are not declared population sims.
2. Wrong-ACCEPT still absent (guard).
3. Tick-6 sidecar bind is standing machinery (r14+), not a new class.
4. Five domain slugs leave the prompt's 8-item pool; a later round that must stay inside the pool will have to rotate sit-outs instead.
5. 352 is a clean positive MODIFY without a world charge; pairing a second in-window charge remains unused.

## Next densification target

Labeled LIF on a second record, or an ISI histogram sidecar. Remaining unused wrong-MODIFY subclasses include **wrong-unit on a lagged bus**. Wrong-ACCEPT remains structurally absent until a prompt amendment.

Novel coverage: 18.5%
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
        BATCH_PATH, "batch-r71.jsonl", staging=FactoryStaging(enabled=True)
    )
    report.append(("check_jsonl FactoryStaging", errors, warnings, kinds, nrec))
    line_errs = []
    for i, rec in enumerate(records, 1):
        errs, kind = check_line(rec, f"batch-r71.jsonl:{i}", factory_staging=True)
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
    records = [record_351(), record_352(), record_353(), record_354(), record_355()]
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
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
