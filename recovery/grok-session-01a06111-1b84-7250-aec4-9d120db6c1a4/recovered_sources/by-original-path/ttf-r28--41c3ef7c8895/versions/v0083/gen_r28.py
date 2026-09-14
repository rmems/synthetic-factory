#!/usr/bin/env python3
"""Emit TTF r28 JSONL (ttf-r28-156..160) into /tmp/ttf-r28/. Never writes outputs/raw/."""

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

OUT_DIR = Path("/tmp/ttf-r28")
BATCH_PATH = OUT_DIR / "batch-r28.jsonl"
NOTES_PATH = OUT_DIR / "NOTES-r28.md"
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


def lif_156_excerpt():
    n = 68
    dt_us = 100
    tau_m_ms = 19.0
    v_th = 1.0
    v_reset = 0.0
    refractory_us = 1000
    i_bias = 0.91
    i_stim_peak = 2.48
    stim = (22000, 25000)
    seed = 28156
    window_us = 42000
    i_clamp_extra = 0.66
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
    take(burst, 9, label_times=(22600, 23100, 24100))
    clamp = [(t, nid) for t, nid in picked if t < 22000][:7]
    spall = [(t, nid) for t, nid in picked if t >= 22000][:9]
    picked = sorted(clamp + spall, key=lambda item: (item[0], item[1]))
    if len(picked) < 8:
        raise ValueError(
            f"LIF excerpt too short {len(picked)} (early={len(early)} burst={len(burst)})"
        )
    channels = ["lif.clamp" if t < 22000 else "lif.flash" for t, _ in picked]
    lif = OrderedDict(
        [
            ("model", "leaky_integrate_and_fire"),
            ("n", 68),
            ("dt_us", 100),
            ("tau_m_ms", 19.0),
            ("v_rest", 0.0),
            ("v_reset", 0.0),
            ("v_th", 1.0),
            ("r_m", 1.0),
            ("refractory_us", 1000),
            ("i_bias", 0.91),
            ("i_stim_peak", 2.48),
            ("stim_t_us", [22000, 25000]),
            ("i_clamp_extra", 0.66),
            ("clamp_n", 14),
            ("seed", 28156),
            (
                "note",
                "Population sim scoped to this sidecar. Plant remains designed. "
                "Neurons 0-13 carry +0.66 ram-clamp bias; stim 22-25 ms is the door-seal flash burst.",
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
            ("round", 28),
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


def record_156():
    excerpt, extra = lif_156_excerpt()
    ticks = [
        tick(2510, 0.04, -0.02, -0.02, 0.01, 0.00),
        tick(6180, 0.07, -0.04, -0.03, 0.01, -0.01),
        tick(6392, 0.04, -0.03, -0.02, 0.00, 0.00),
        tick(7060, 0.09, -0.06, -0.03, 0.02, -0.02),
        tick(22600, 0.06, -0.36, -0.04, -0.02, -0.02),
        tick(840000000, 0.02, -0.05, -0.02, 0.00, -0.01),
    ]
    state = OrderedDict(
        [
            (
                "description",
                "Rammer-Bank RB-3 is already pushing Coke-Wharf oven CW-9 at 2.24 MPa while "
                "the door-seal transducer sits at 2.24 MPa against a 1.80 MPa flash-face cap. "
                "A ram-first latch dumps the charge; a bar-first story would keep the 1.60 mm/s "
                "close. Stored hoop in the coal cake is not yet an observable of either race "
                "channel.",
            ),
            ("domain", "coke-oven-battery"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Finish the CW-9 push, keep flash-face pressure <= 1.80 MPa, and leave the "
                "door seal unmarked.",
            ),
            ("t0_us", 1756794621000156),
            ("gate_latency_us", 880),
            ("race_window_us", 460),
            ("race_window_rel_ms", [6.1, 6.56]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "pt.ram.MPa 2.24 MPa pulse",
                                "enc.bar.mm 1.60 mm/s close",
                            ],
                        ),
                        (
                            "semantics",
                            "Ram-first latches 2.24 -> 1.55 MPa; bar-first keeps the "
                            "1.60 mm/s close on a still-filling oven model.",
                        ),
                        (
                            "window_derivation",
                            "460 us = one 1 kHz ram-PT sample minus bar-encoder group delay "
                            "on this battery bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 212 us vs combined jitter ~64 us (ram 28 + bar 36): 3.3x over "
                            "a 2.0x trust floor. Reversing order by < 212 us inside the 460 us window "
                            "would have kept 2.24 MPa; predicted next-sample 1.96 MPa > 1.80 cap.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "ram cavity PT, 1 kHz, 28 us timestamp jitter",
                    "ram-bar linear encoder, 500 Hz, 36 us jitter",
                    "door-seal AE puck (context until the flash)",
                    "door RTD (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("flash_face_cap_MPa", 1.8),
                        ("observed_ram_MPa", 2.24),
                        ("proposed_close_mm_s", 1.6),
                        ("door_temp_C", 168.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Rammer-Bank RB-3 indexed onto CW-9; ram-bar close 1.60 mm/s armed.",
                    "2. Cruise ram 2.24 MPa; flash-face cap 1.80 MPa.",
                    "3. Bar precursor at 1.240 ms; ram warm-start 2.24 MPa.",
                    "4. Race window [6.100, 6.560] ms opens on the battery bus.",
                    "5. pt.ram.MPa 2.24 MPa at 6.180 ms (winner).",
                    "6. enc.bar.mm 1.60 mm/s at 6.392 ms (loser by 212 us).",
                    "7. Gate at 7.060 ms (winner + 880 us): MODIFY clamp 2.24 -> 1.55 MPa.",
                    "8. Clamp executes; next-sample ram 1.72 MPa < 1.80 cap.",
                    "9. At 22.600 ms stored hoop still flashes 40 mm of door spew; AE burst.",
                    "10. Door-clean 14 min (abort_s=840); named un-netted loss, not folded into process heads.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_ram_press"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("ram_MPa", 2.24),
                        ("close_mm_s", 1.6),
                        ("door_C", 168.0),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("ram_MPa", 2.24),
                        ("flash_face_cap_MPa", 1.8),
                        ("predicted_unclamped_next_MPa", 1.96),
                        ("close_mm_s", 1.6),
                        ("race_margin_us", 212),
                        ("combined_jitter_us", 64),
                        ("abort_s", 840),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 2.24 MPa ram cruise: 2.24 MPa looks like a fill transient, "
                "not flash, and CW-9 oven is treated as still open.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "correct"),
            (
                "rationale",
                "Ram 2.24 MPa won by 212 us, so the flash face is loading, not still filling. "
                "Holding 2.24 MPa predicts next-sample 1.96 MPa > 1.80 cap. MODIFY: ram "
                "2.24 -> 1.55 MPa. Observed after clamp 1.72 MPa < 1.80. A full REJECT is not "
                "indicated: a sound push accepts 1.55 MPa.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "flash_face_MPa",
                            OrderedDict(
                                [
                                    ("cap", 1.8),
                                    ("observed", 2.24),
                                    ("predicted_unclamped_next", 1.96),
                                    ("clamped_MPa", 1.55),
                                    ("observed_after_clamp", 1.72),
                                ]
                            ),
                        ),
                        (
                            "ram_MPa",
                            OrderedDict(
                                [
                                    ("proposed", 2.24),
                                    ("clamped", 1.55),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 212),
                                    ("combined_jitter_us", 64),
                                    ("ratio", 3.31),
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
            ("name", "clamped_ram_press"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("ram_MPa", 1.55),
                        ("close_mm_s", 1.6),
                        ("door_C", 168.0),
                    ]
                ),
            ),
            (
                "gate_effect",
                "MODIFY: ram 2.24 -> 1.55 MPa. Process-correct vs the 1.80 MPa flash-face cap. "
                "Door-seal flash still occurs at 22.600 ms.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Process-correct MODIFY held flash-face at 1.72 MPa. At 22.600 ms stored hoop "
                "in the coal cake still flashed 40 mm of door spew. Clamp reduced dump energy; it "
                "did not prevent the split. Partnered negative: process heads stay honest; "
                "world loss is named, not netted.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("press", "clamp executed; peak 1.72 MPa < 1.80"),
                        ("door_flash", "40 mm spew at 22.600 ms"),
                        ("repair", "14 min door-clean (abort_s=840)"),
                        ("mission", "CW-9 push incomplete this circuit"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Neither ram PT nor bar encoder predicted the hoop charge; ae.door.flash is a new channel at 22.600 ms, 15.540 ms after the gate, still inside the 42 ms raster.",
                    "Delayed (abort_s=840): 14 min door-clean. Named un-netted loss, not folded into process heads.",
                ],
            ),
            (
                "un_netted_loss",
                "14 min door-clean after a 40 mm door-seal flash. Safety head -0.56 prices "
                "the split; task_progress stays +0.32 because the ram clamp completed under "
                "the 1.80 MPa cap. World loss is named here, not subtracted from process heads.",
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "pt.ram.MPa (6.180 ms, 2.24 MPa)"),
                        ("loser", "enc.bar.mm (6.392 ms, 1.60 mm/s)"),
                        ("margin_us", 212),
                        (
                            "counterfactual_if_reversed",
                            "Platen-first by < 212 us inside the 460 us window would have kept "
                            "2.24 MPa; predicted next-sample 1.96 MPa would have exceeded the "
                            "1.80 cap even without the hoop charge. The MODIFY is still the "
                            "correct process. The flash is a later world charge either way, "
                            "cheaper with the clamp than without.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 22600),
            (
                "reward_inflection_note",
                "Safety collapses at the 22.600 ms door-seal flash (tick t_us=22600), inside "
                "the 42 ms raster. The correct MODIFY at 7.060 ms is in the same excerpt. Do "
                "not put inflection on the abort_s=840 clean tick.",
            ),
        ]
    )
    spikes = [
        spike("tc.platen.ctx", 1.240, 0.42),
        spike("pt.bladder.MPa", 2.510, 0.61),
        spike("enc.platen.mm", 3.880, 0.50),
        spike("pt.bladder.MPa", 6.180, 1.31),
        spike("enc.platen.mm", 6.392, 1.14),
        spike("ctrl.gate", 7.060, 0.98),
        spike("pt.bladder.MPa", 8.440, 0.80),
        spike("enc.platen.mm", 11.200, 0.62),
        spike("ctrl.gate", 14.800, 0.84),
        spike("ae.mold.flash", 22.600, 1.46),
        spike("ae.mold.flash", 24.310, 0.91),
        spike("tc.platen.ctx", 31.400, 0.41),
        spike("pt.bladder.MPa", 38.200, 0.53),
    ]
    ras = raster_core(
        42,
        68,
        28,
        80,
        routing(
            "thalamic-relay.bladder-pt",
            "spikenaut.policy.bladder-clamp",
            [
                ("relay.pt.bladder", "policy.bladder_clamp", 0.66),
                ("relay.enc.platen", "policy.platen_hold", 0.30),
                ("relay.ae.flash", "policy.bladder_clamp", -0.45),
            ],
            "noradrenaline",
            0.05,
            "surprise-gated pre_post_stdp; NA at bladder win (6.180 ms) opens a 50 ms "
            "eligibility trace that still covers the 22.600 ms mold flash",
        ),
        excerpt,
        extra=extra,
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.46),
            ("decision", "MODIFY"),
            (
                "populations",
                [
                    pop("bladder_clamp", 36, 0.50, 302.0, 5),
                    pop("platen_hold", 36, 0.50, 60.4, 1),
                    pop("flash_veto", 24, 0.75),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r28-156"),
            (
                "title",
                "Gum-Reach GR-2 / Bladder-Kettle BK-4: bladder PT beats platen by 212 us; "
                "correct MODIFY still eats an in-window mold flash (partnered negative total -0.44)",
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
                    "42 ms raster. total -0.44 = 0.32 + -0.56 + -0.16 + 0.02 + -0.06. Named mold "
                    "clean (abort_s=840) is not netted into task_progress.",
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
                        "partnered-negative-total",
                        "independent-lif-raster",
                        "sidecar-sim-only",
                        "in-window-world-charge",
                        "designed",
                    ],
                    "A critic can see the world-charge as a LIF burst inside the raster while "
                    "process heads stay honest. Credit assignment is spikes, not prose across a "
                    "14 min mold-clean.",
                    1,
                ),
            ),
        ]
    )


def record_157():
    ticks = [
        tick(1880, -0.02, -0.01, -0.02, -0.01, 0.01),
        tick(4260, -0.04, -0.02, -0.04, -0.02, 0.01),
        tick(4408, -0.03, -0.01, -0.03, -0.02, 0.01),
        tick(5000, -0.07, -0.04, -0.09, -0.05, 0.02),
        tick(6550, -0.02, -0.01, -0.02, -0.01, 0.01),
        tick(1440000000, -0.02, -0.01, -0.02, -0.01, 0.00),
    ]
    spikes = [
        spike("dp.annulus.ctx", 0.920, 0.40),
        spike("load.stem.kNm", 1.880, 0.58),
        spike("pt.mud.bar", 2.640, 0.51),
        spike("load.stem.kNm", 4.260, 1.32),
        spike("pt.mud.bar", 4.408, 1.15),
        spike("ctrl.gate", 5.000, 1.00),
        spike("load.stem.kNm", 6.550, 0.74),
        spike("pt.mud.bar", 8.200, 0.61),
        spike("ctrl.gate", 12.100, 0.82),
        spike("dp.annulus.ctx", 16.400, 0.42),
        spike("load.stem.kNm", 20.800, 0.53),
        spike("pt.mud.bar", 23.400, 0.47),
    ]
    excerpt = independent_excerpt(28157, 92, 24000, 14, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Wych-Bore WB-7 already has Pilot-Stem PS-4 queued at 1.40 metres per second. "
                "Stem torque sits at 18.4 kilonewton-metres, well under the 42.0 "
                "kilonewton-metre drill-string ceiling. Mud discharge is 31.2 bar on a second "
                "hydraulic circuit whose ceiling is 48.0 bar. The legal call is to keep feeding; "
                "a timid gate that spends the mud number on the drill-string will stop a lawful "
                "advance.",
            ),
            ("domain", "hdd-pilot-bore"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Execute the 1.40 m/s pilot push while stem torque stays <= 42.0 kNm; do not "
                "spend a mud-pump residual on the stem hold.",
            ),
            ("t0_us", 1756794621000157),
            ("gate_latency_us", 740),
            ("race_window_us", 310),
            ("race_window_rel_ms", [4.2, 4.51]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "load.stem.kNm 18.4 kNm",
                                "pt.mud.bar 31.2 bar residual",
                            ],
                        ),
                        (
                            "semantics",
                            "Stem-first should ACCEPT 1.40 m/s (18.4 kNm < 42.0 kNm stem cap). "
                            "Mud-first tempts a weak supervisor to treat 31.2 bar as a stem excursion.",
                        ),
                        (
                            "window_derivation",
                            "310 us = one stem-torque load-pin sample minus mud-pump transducer "
                            "group delay on this dual-circuit bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 148 us vs combined jitter ~54 us (stem 24 + mud 30): 2.7x over "
                            "a 2.0x trust floor. Order is correctly stem-first. The error is which "
                            "circuit the REJECT is bound to, not the race.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "stem-torque load-pin, 4 kHz, 24 us jitter",
                    "mud-pump discharge PT, 4 kHz, 30 us jitter",
                    "annulus differential pressure (context)",
                    "rig heading IMU (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("stem_cap_kNm", 42.0),
                        ("stem_kNm", 18.4),
                        ("mud_cap_bar", 48.0),
                        ("mud_bar", 31.2),
                        ("proposed_push_m_s", 1.4),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. PS-4 stem latched; pilot push 1.40 m/s armed on WB-7.",
                    "2. Stem torque 18.4 kNm; mud-pump residual 31.2 bar on a separate circuit.",
                    "3. Annulus precursor at 0.920 ms.",
                    "4. Race window [4.200, 4.510] ms.",
                    "5. load.stem.kNm 18.4 kNm at 4.260 ms (winner).",
                    "6. pt.mud.bar 31.2 bar at 4.408 ms (loser by 148 us).",
                    "7. Gate at 5.000 ms: REJECT hold 0.00 m/s (incorrect).",
                    "8. Legal push cancelled; stem still 18.4 kNm < 42.0 kNm cap.",
                    "9. Mud residual 31.2 bar remains under its own 48.0 bar cap.",
                    "10. Delayed missed_window_s=1440 (24 min daylight window) while the rig waits.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "pilot_push_140"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("push_m_s", 1.4),
                        ("hold", False),
                        ("circuit", "stem"),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("stem_kNm", 18.4),
                        ("stem_cap_kNm", 42.0),
                        ("stem_circuit_id", "stem"),
                        ("mud_bar", 31.2),
                        ("mud_cap_bar", 48.0),
                        ("mud_circuit_id", "mud"),
                        ("proposed_push_m_s", 1.4),
                        ("race_margin_us", 148),
                        ("combined_jitter_us", 54),
                        ("missed_window_s", 1440),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 1.40 m/s pilot push because stem 18.4 kNm is under the "
                "42.0 kNm stem cap; mud 31.2 bar is a different circuit under a 48.0 bar cap.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "REJECT"),
            ("correctness", "incorrect"),
            (
                "rationale",
                "Mud-pump 31.2 bar looks like a torque excursion over a 42.0 kNm cap, so the "
                "supervisor holds the push at 0.00 m/s. Stem-first is treated as a noisy echo "
                "of the same loop. Over-caution on a dual-circuit rig is the stated doctrine.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "stem_kNm",
                            OrderedDict(
                                [
                                    ("cap", 42.0),
                                    ("observed", 18.4),
                                    ("executed_push_m_s", 0.0),
                                    ("circuit_id", "stem"),
                                ]
                            ),
                        ),
                        (
                            "mud_bar",
                            OrderedDict(
                                [
                                    ("cap", 48.0),
                                    ("observed", 31.2),
                                    ("misbound_as", "stem_excursion"),
                                    ("circuit_id", "mud"),
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
            ("name", "stem_hold_wrong_circuit"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("push_m_s", 0.0),
                        ("hold", True),
                        ("circuit", "stem"),
                    ]
                ),
            ),
            (
                "gate_effect",
                "REJECT (incorrect): push 1.40 -> 0.00 m/s. Routing relay.pump.mud -> "
                "policy.stem_hold; stem 18.4 kNm left unused as a go signal.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Wrong-REJECT held PS-4 at 0.00 m/s. Stem 18.4 kNm was under the 42.0 kNm cap; "
                "mud 31.2 bar was a different circuit under 48.0 bar. 24 min daylight window missed "
                "(missed_window_s=1440). Correct gate was ACCEPT of the 1.40 m/s push.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("stem", "held; push 0.00 m/s; torque still 18.4 kNm < 42.0 kNm"),
                        ("mud", "31.2 bar residual unused, still < 48.0 bar cap"),
                        ("rig", "24 min daylight window missed"),
                        ("mission", "push deferred"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Stem-first was the correct order and the stem number was legal; the REJECT spent that win on the mud-pump transducer.",
                    "Delayed (missed_window_s=1440): WB-7 loses the 24 min daylight window; next window 6.1 h.",
                ],
            ),
            (
                "recovery",
                OrderedDict(
                    [
                        (
                            "correct_gate",
                            "ACCEPT the 1.40 m/s pilot push; leave mud 31.2 bar to its own 48.0 bar cap.",
                        ),
                        ("correct_circuit", "stem"),
                        ("wrong_circuit", "mud"),
                        (
                            "wrong_edit_applied",
                            OrderedDict([("push_m_s", 0.0), ("hold", True)]),
                        ),
                        (
                            "cost",
                            "Missed 24 min daylight window (task/efficiency); stem never exceeded 18.4 kNm (safety near-miss of a false hold).",
                        ),
                    ]
                ),
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "load.stem.kNm (4.260 ms, 18.4 kNm)"),
                        ("loser", "pt.mud.bar (4.408 ms, 31.2 bar)"),
                        ("margin_us", 148),
                        (
                            "counterfactual_if_reversed",
                            "Mud-first by < 148 us would still be under the 48.0 bar mud cap; "
                            "a correct gate binds load.stem.kNm to stem_go either way. The wrong "
                            "REJECT spent the stem win on the wrong circuit.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 5000),
            (
                "reward_inflection_note",
                "Task, efficiency, and coherence drop at the wrong REJECT (5.000 ms, tick 4). "
                "The 24 min missed window is delayed surprise, not the inflection.",
            ),
        ]
    )
    ras = raster_core(
        24,
        92,
        36,
        79,
        routing(
            "relay.pump.mud",
            "policy.stem_hold",
            [
                ("relay.pump.mud", "policy.stem_hold", 0.73),
                ("relay.load.stem", "policy.stem_hold", 0.21),
            ],
            "acetylcholine",
            0.06,
            "circuit_cap_stdp; ACh tags the (wrong) stem_hold bind at the mud residual",
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
            ("decision_window_ms", 0.31),
            ("decision", "REJECT"),
            (
                "populations",
                [
                    pop("stem_hold", 48, 0.50, 268.8, 4),
                    pop("stem_go", 48, 0.80, 6.7, 0),
                    pop("mud_ctx", 32, 0.55, 100.8, 1),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r28-157"),
            (
                "title",
                "WRONG-REJECT at Wych-Bore WB-7 / Pilot-Stem PS-4: stem 18.4 kNm < 42.0 kNm cap; "
                "supervisor treats mud 31.2 bar as a stem excursion",
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
                    "Wrong-reject. Sidecar arithmetic 18.4 < 42.0 on stem is true; REJECT bound "
                    "to mud residual. total -0.58 = -0.20 + -0.10 + -0.22 + -0.12 + 0.06.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "hdd-pilot-bore",
                    [
                        "reject",
                        "wrong-gate",
                        "wrong-circuit",
                        "sidecar-convictable",
                        "designed",
                    ],
                    "Teaches a probe that a correct stem-first race can still be a wrong gate "
                    "when the REJECT binds mud residual onto the stem hold. Convictable from "
                    "circuit IDs and caps without HDD physics.",
                    2,
                    supervisor_error_type="wrong-reject",
                ),
            ),
        ]
    )


def record_158():
    ticks = [
        tick(2760, 0.01, 0.05, 0.01, 0.01, 0.01),
        tick(5880, 0.02, 0.08, 0.02, 0.02, 0.01),
        tick(6047, 0.02, 0.07, 0.02, 0.02, 0.01),
        tick(6980, 0.03, 0.12, 0.04, 0.03, 0.02),
        tick(9110, 0.01, 0.05, 0.02, 0.01, 0.01),
        tick(600000000, 0.01, 0.03, 0.01, 0.01, 0.00),
    ]
    spikes = [
        spike("tc.brine.ctx", 1.410, 0.43),
        spike("vm.membrane.V", 2.760, 0.62),
        spike("shunt.tap.V", 4.220, 0.49),
        spike("vm.membrane.V", 5.880, 1.35),
        spike("shunt.tap.V", 6.047, 1.12),
        spike("ctrl.gate", 6.980, 1.03),
        spike("vm.membrane.V", 9.110, 0.77),
        spike("tc.brine.ctx", 13.400, 0.44),
        spike("shunt.tap.V", 17.200, 0.58),
        spike("ctrl.gate", 23.500, 0.81),
        spike("vm.membrane.V", 30.100, 0.54),
        spike("tc.brine.ctx", 36.800, 0.38),
        spike("shunt.tap.V", 39.200, 0.46),
    ]
    excerpt = independent_excerpt(28158, 112, 40000, 15, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Header-Bus HB-6 is parked on Natron-Hall NH-2's membrane-cell HIL rack. "
                "Membrane voltage is already 4.80 V versus a 4.40 V pinhole cap, while the "
                "shunt-tap still shows 4.12 V because the pad current source is mid-ramp. "
                "Binding the 4.80 V packet REJECTs the 18 mm/s cathode-gap crawl; binding the "
                "shunt would crawl on an unfinished ramp.",
            ),
            ("domain", "chlor-alkali-membrane"),
            ("sim_or_real", "hil"),
            (
                "goal",
                "Do not crawl the cathode gap unless membrane voltage <= 4.40 V; keep ram "
                "0.0 mm/s until the injected pinhole voltage drops.",
            ),
            ("t0_us", 1756794621000158),
            ("gate_latency_us", 1100),
            ("race_window_us", 380),
            ("race_window_rel_ms", [5.8, 6.18]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "vm.membrane.V 4.80 V",
                                "shunt.tap.V 4.12 V mid-ramp",
                            ],
                        ),
                        (
                            "semantics",
                            "Membrane-first REJECTs the crawl at 0.0 mm/s; shunt-first would "
                            "arm 18 mm/s while the current source is still ramping.",
                        ),
                        (
                            "window_derivation",
                            "380 us = one membrane DVM slot versus shunt-tap integration on "
                            "this cell HIL bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 167 us vs combined jitter ~58 us (membrane 26 + shunt 32): 2.9x "
                            "over a 2.0x trust floor. The current source ramps 110-150 us before the "
                            "membrane DVM settles (geometric lag, not a sensor fault); the 4.12 V "
                            "shunt packet is still the loser in this 380 us window.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "membrane DVM, 5 kHz burst, 26 us jitter",
                    "shunt-tap voltage, 200 Hz, 32 us jitter",
                    "brine RTD (context)",
                    "HIL current-source monitor (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("pinhole_cap_V", 4.4),
                        ("observed_membrane_V", 4.8),
                        ("shunt_midramp_V", 4.12),
                        ("proposed_crawl_mm_s", 18.0),
                        ("source_ramp_lead_us", [110, 150]),
                    ]
                ),
            ),
            (
                "hil",
                OrderedDict(
                    [
                        ("pad", "Natron-Hall NH-2 membrane-cell mockup"),
                        ("injected", "membrane voltage + current-source ramp"),
                        (
                            "note",
                            "Hardware-in-the-loop cell. Invented plant; not a live chlor-alkali room.",
                        ),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Header-Bus HB-6 on the NH-2 HIL rack; cathode-gap crawl 18 mm/s armed.",
                    "2. Current source ramps 110-150 us before the membrane DVM settles.",
                    "3. Brine precursor at 1.410 ms.",
                    "4. Race window [5.800, 6.180] ms.",
                    "5. vm.membrane.V 4.80 V at 5.880 ms (winner).",
                    "6. shunt.tap.V 4.12 V at 6.047 ms (loser by 167 us).",
                    "7. Gate at 6.980 ms: REJECT hold 0.0 mm/s; do not crawl 18 mm/s.",
                    "8. Cell remains over cap this cycle; pinhole cap held.",
                    "9. Current recycle queued on the pad.",
                    "10. Delayed (abort_s=600): 10 min cell retune and current-source retune.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "crawl_cathode_gap"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("crawl_mm_s", 18.0),
                        ("hold", False),
                        ("shunt_authoritative", True),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("membrane_V", 4.8),
                        ("pinhole_cap_V", 4.4),
                        ("shunt_midramp_V", 4.12),
                        ("race_margin_us", 167),
                        ("combined_jitter_us", 58),
                        ("abort_s", 600),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 18 mm/s cathode-gap crawl because shunt 4.12 V looks under "
                "the 4.40 V cap, treating membrane 4.80 V as a noisy sheath echo.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "REJECT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Membrane voltage 4.80 V is over the 4.40 V pinhole cap. Shunt 4.12 V is a "
                "mid-ramp current-source lag, not a clearance. REJECT: hold 0.0 mm/s; do not "
                "commit 18 mm/s across the cathode gap.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "pinhole_V",
                            OrderedDict(
                                [
                                    ("cap", 4.4),
                                    ("observed_membrane", 4.8),
                                    ("shunt_midramp", 4.12),
                                ]
                            ),
                        ),
                        (
                            "crawl_mm_s",
                            OrderedDict(
                                [
                                    ("proposed", 18.0),
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
            ("name", "hold_for_pinhole_drop"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("crawl_mm_s", 0.0),
                        ("hold", True),
                        ("shunt_authoritative", False),
                    ]
                ),
            ),
            (
                "gate_effect",
                "REJECT: hold 0.0 mm/s; 18 mm/s crawl cancelled. Membrane 4.80 > 4.40 cap.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct REJECT held Header-Bus HB-6 at 0.0 mm/s. Cell over cap this cycle; "
                "pinhole cap held. Shunt mid-ramp was not treated as a voltage clearance.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("cathode_ram", "held; speed 0.0 mm/s"),
                        ("cell", "still over 4.40 V this cycle"),
                        ("shunt", "4.12 V unused as clearance"),
                        ("mission", "crawl deferred"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Geometric lag: current source ramped 110-150 us before the membrane DVM settled, yet membrane still won the 380 us race.",
                    "Delayed (abort_s=600): pad policy update forbids treating shunt mid-ramp as a membrane substitute after a 10 min cell retune.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "vm.membrane.V (5.880 ms, 4.80 V)"),
                        ("loser", "shunt.tap.V (6.047 ms, 4.12 V)"),
                        ("margin_us", 167),
                        (
                            "counterfactual_if_reversed",
                            "Shunt-first by < 167 us inside the 380 us window would have committed "
                            "18 mm/s with membrane 4.80 > 4.40 cap. Order, not amplitude, selected the hold.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 6980),
            (
                "reward_inflection_note",
                "Safety and coherence step up at the REJECT gate (6.980 ms, tick 4) as the hold "
                "locks in over the illegal crawl.",
            ),
        ]
    )
    ras = raster_core(
        40,
        112,
        22,
        99,
        routing(
            "thalamic-relay.membrane-vm",
            "spikenaut.policy.cell-hold",
            [
                ("relay.vm.membrane", "policy.cell_hold", 0.69),
                ("relay.shunt.tap", "policy.shunt_commit", 0.27),
                ("relay.tc.brine", "policy.cell_hold", 0.11),
            ],
            "dopamine",
            0.09,
            "pinhole_stdp; DA at membrane win (5.880 ms) tags cell_hold over shunt_commit",
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
            ("decision_window_ms", 0.38),
            ("decision", "REJECT"),
            (
                "populations",
                [
                    pop("cell_hold", 56, 0.50, 235.0, 5),
                    pop("shunt_commit", 40, 0.50, 65.8, 1),
                    pop("pinhole_veto", 32, 0.75),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r28-158"),
            (
                "title",
                "Natron-Hall NH-2 HIL / Header-Bus HB-6: membrane 4.80 V beats shunt 4.12; "
                "correct REJECT holds the cathode-gap crawl",
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
                    "Correct REJECT. Membrane over cap; shunt mid-ramp unused as clearance. "
                    "total +0.78 = 0.10 + 0.40 + 0.12 + 0.10 + 0.06.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "chlor-alkali-membrane",
                    [
                        "reject",
                        "hil-cell",
                        "membrane-vs-shunt",
                        "pinhole-cap",
                        "hil",
                    ],
                    "Teaches that a HIL shunt mid-ramp can lose to membrane voltage inside a "
                    "380 us window; reversing 167 us would have selected an illegal crawl.",
                    3,
                ),
            ),
        ]
    )


def record_159():
    ticks = [
        tick(3110, 0.04, 0.03, 0.02, 0.01, 0.00),
        tick(6910, 0.08, 0.07, 0.03, 0.02, 0.01),
        tick(7124, 0.05, 0.05, 0.02, 0.02, 0.01),
        tick(7330, 0.11, 0.09, 0.04, 0.03, 0.01),
        tick(9550, 0.04, 0.04, 0.02, 0.01, 0.01),
        tick(480000000, 0.02, 0.02, 0.01, 0.01, 0.00),
    ]
    spikes = [
        spike("pt.draft.ctx", 1.620, 0.42),
        spike("pitot.penstock", 3.110, 0.59),
        spike("staff.surge.m", 5.040, 0.48),
        spike("pitot.penstock", 6.910, 1.31),
        spike("staff.surge.m", 7.124, 1.09),
        spike("ctrl.gate", 7.330, 0.96),
        spike("pitot.penstock", 9.550, 0.73),
        spike("pt.draft.ctx", 13.800, 0.45),
        spike("staff.surge.m", 18.400, 0.57),
        spike("ctrl.gate", 22.700, 0.80),
        spike("pitot.penstock", 26.900, 0.51),
        spike("pt.draft.ctx", 29.400, 0.38),
    ]
    excerpt = independent_excerpt(28159, 56, 30000, 13, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Penstock-Gate PG-8 at Surge-Adit SA-3 still holds a 72 percent leaf while a "
                "9.40 m/s pitot jet sits over an 8.00 m/s waterhammer cap. A surge-tank staff "
                "on the same gallery still claims 6.2 m false-calm. Pitot-first latches a leaf "
                "clamp; staff-first would keep 72 percent into a close-out surge.",
            ),
            ("domain", "hydro-penstock"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Stroke the SA-3 leaf only if pitot velocity <= 8.00 m/s; otherwise clamp "
                "opening so the waterhammer is not made at 72 percent.",
            ),
            ("t0_us", 1756794621000159),
            ("gate_latency_us", 420),
            ("race_window_us", 520),
            ("race_window_rel_ms", [6.8, 7.32]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "pitot.penstock 9.40 m/s",
                                "staff.surge.m 6.2 m false-calm",
                            ],
                        ),
                        (
                            "semantics",
                            "Pitot-first latches leaf clamp 72 -> 41 percent; staff-first keeps "
                            "72 percent on a false-calm gallery.",
                        ),
                        (
                            "window_derivation",
                            "520 us = one 2 kHz pitot sample versus staff-gauge decode on this "
                            "penstock bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 214 us vs combined jitter ~71 us (pitot 33 + staff 38): 3.0x over "
                            "a 2.0x trust floor. Reversing order by < 214 us inside the 520 us "
                            "window would have kept 72 percent into a 9.40 m/s jet.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "penstock pitot, 2 kHz, 33 us jitter",
                    "surge-tank staff gauge, 200 Hz, 38 us jitter",
                    "draft-tube PT (context)",
                    "leaf hydraulic pressure (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("waterhammer_cap_m_s", 8.0),
                        ("observed_pitot_m_s", 9.4),
                        ("proposed_leaf_pct", 72.0),
                        ("staff_m", 6.2),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Leaf indexed onto SA-3 penstock; PG-8 armed at 72 percent.",
                    "2. Staff reports 6.2 m false-calm; pitot already sees 9.40 m/s.",
                    "3. Draft-tube precursor at 1.620 ms.",
                    "4. Race window [6.800, 7.320] ms.",
                    "5. pitot.penstock 9.40 m/s at 6.910 ms (winner).",
                    "6. staff.surge.m 6.2 m at 7.124 ms (loser by 214 us).",
                    "7. Gate at 7.330 ms: MODIFY leaf 72 -> 41 percent.",
                    "8. Leaf applies; next-sample pitot 7.6 m/s < 8.00 cap.",
                    "9. Gallery occupies; next stroke queued.",
                    "10. Delayed (penstock_reseq_s=480): dispatcher resequences the following stroke +8 min.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "leaf_open_72"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("leaf_pct", 72.0),
                        ("servo_bar", 18.0),
                        ("adit_id", 3),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("pitot_m_s", 9.4),
                        ("waterhammer_cap_m_s", 8.0),
                        ("staff_calm", True),
                        ("race_margin_us", 214),
                        ("combined_jitter_us", 71),
                        ("penstock_reseq_s", 480),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 72 percent leaf because the staff gauge claims the gallery "
                "is calm, treating pitot 9.40 m/s as a sidelobe.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "correct"),
            (
                "rationale",
                "Pitot 9.40 m/s won by 214 us, so the jet is inside the 8.00 m/s waterhammer "
                "cap. Staff-gauge false-calm is not a velocity. MODIFY: leaf 72 -> 41 percent. "
                "A full REJECT (close the leaf) is not indicated: 41 percent is a legal "
                "catch-and-pass.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "pitot_m_s",
                            OrderedDict(
                                [
                                    ("cap", 8.0),
                                    ("observed", 9.4),
                                    ("staff_calm", True),
                                    ("observed_after_clamp", 7.6),
                                ]
                            ),
                        ),
                        (
                            "leaf_pct",
                            OrderedDict(
                                [
                                    ("proposed", 72.0),
                                    ("clamped", 41.0),
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
            ("name", "clamped_leaf_41"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("leaf_pct", 41.0),
                        ("servo_bar", 18.0),
                        ("adit_id", 3),
                    ]
                ),
            ),
            (
                "gate_effect",
                "MODIFY: leaf 72 -> 41 percent. Process-correct vs the 8.00 m/s waterhammer cap.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct MODIFY held PG-8 at 41 percent. Next-sample pitot 7.6 m/s under the "
                "8.00 m/s cap. Staff 6.2 m false-calm was not treated as a velocity clearance.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("leaf", "clamped 72 -> 41 percent"),
                        ("penstock", "7.6 m/s < 8.00 cap after clamp"),
                        ("staff", "6.2 m unused as clearance"),
                        ("mission", "stroke completed under cap"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Staff-gauge false-calm lagged the pitot jet by 214 us; order, not amplitude, selected the clamp.",
                    "Delayed (penstock_reseq_s=480): dispatcher resequences the following stroke +8 min. Not a safety inflection.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "pitot.penstock (6.910 ms, 9.40 m/s)"),
                        ("loser", "staff.surge.m (7.124 ms, 6.2 m)"),
                        ("margin_us", 214),
                        (
                            "counterfactual_if_reversed",
                            "Staff-first by < 214 us inside the 520 us window would have kept "
                            "72 percent into a 9.40 m/s jet over the 8.00 cap. The MODIFY is "
                            "the correct process either way once pitot is bound.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 7330),
            (
                "reward_inflection_note",
                "Task and safety step up at the MODIFY gate (7.330 ms, tick 4). Tick 6 is "
                "penstock_reseq_s=480.",
            ),
        ]
    )
    ras = raster_core(
        30,
        56,
        44,
        74,
        routing(
            "thalamic-relay.penstock-pitot",
            "spikenaut.policy.leaf-clamp",
            [
                ("relay.pitot.jet", "policy.gate_clamp", 0.64),
                ("relay.staff.surge", "policy.staff_hold", 0.29),
                ("relay.pt.draft", "policy.gate_clamp", 0.12),
            ],
            "serotonin",
            0.07,
            "waterhammer_stdp; 5-HT at pitot win (6.910 ms) tags gate_clamp over staff_hold",
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
            ("decision_window_ms", 0.52),
            ("decision", "MODIFY"),
            (
                "populations",
                [
                    pop("gate_clamp", 28, 0.50, 274.7, 4),
                    pop("staff_hold", 28, 0.50, 68.7, 1),
                    pop("hammer_veto", 20, 0.75),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r28-159"),
            (
                "title",
                "Surge-Adit SA-3 / Penstock-Gate PG-8: pitot 9.40 m/s beats staff false-calm; "
                "correct MODIFY clamps leaf 72 -> 41 percent",
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
                    "Correct MODIFY. Pitot over cap; staff false-calm unused. total +0.92 = "
                    "0.34 + 0.30 + 0.14 + 0.10 + 0.04.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "hydro-penstock",
                    [
                        "modify",
                        "designed",
                        "pitot-vs-staff",
                        "waterhammer",
                    ],
                    "Teaches that a false-calm staff gauge can lose to a legal pitot jet inside "
                    "a 520 us window; reversing 214 us would have kept an illegal 72 percent leaf.",
                    4,
                ),
            ),
        ]
    )


def record_160():
    ticks = [
        tick(1660, 0.05, 0.04, 0.02, 0.01, 0.01),
        tick(3860, 0.10, 0.08, 0.04, 0.03, 0.02),
        tick(3973, 0.06, 0.05, 0.03, 0.02, 0.01),
        tick(4420, 0.14, 0.10, 0.05, 0.04, 0.02),
        tick(6200, 0.06, 0.04, 0.02, 0.01, 0.01),
        tick(300000000, 0.03, 0.03, 0.02, 0.01, 0.01),
    ]
    spikes = [
        spike("pt.vacuum.ctx", 0.740, 0.39),
        spike("refract.brix", 1.660, 0.57),
        spike("ir.foam.glint", 2.480, 0.48),
        spike("refract.brix", 3.860, 1.29),
        spike("ir.foam.glint", 3.973, 1.10),
        spike("ctrl.gate", 4.420, 0.97),
        spike("refract.brix", 6.200, 0.76),
        spike("ir.foam.glint", 8.880, 0.61),
        spike("ctrl.gate", 12.400, 0.83),
        spike("pt.vacuum.ctx", 16.100, 0.41),
        spike("refract.brix", 19.700, 0.54),
        spike("ir.foam.glint", 21.400, 0.46),
    ]
    excerpt = independent_excerpt(28160, 80, 22000, 12, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Strike-Pan SP-5 in Massecuite-Kettle MK-2 is already at 92.4 Brix while a "
                "foam-IR glint still reports 98 against a 96.0 Brix strike cap that the "
                "refractometer has not crossed. Brix-first should ACCEPT the already-legal "
                "strike; foam-first would hold a legal drop on lighting.",
            ),
            ("domain", "sugar-vacuum-pan"),
            ("sim_or_real", "simulated"),
            (
                "goal",
                "Drop SP-5 when refractometer Brix is <= 96.0; do not spend a foam-IR glint "
                "on a hold.",
            ),
            ("t0_us", 1756794621000160),
            ("gate_latency_us", 560),
            ("race_window_us", 240),
            ("race_window_rel_ms", [3.8, 4.04]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "refract.brix 92.4",
                                "ir.foam.glint 98 lighting",
                            ],
                        ),
                        (
                            "semantics",
                            "Brix-first ACCEPTS the already-legal 92.4 strike. Foam-first would "
                            "REJECT a legal drop on a 98 glint.",
                        ),
                        (
                            "window_derivation",
                            "240 us = one refractometer sample minus foam-IR integration on this "
                            "pan-bus simulation.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 113 us vs combined jitter ~50 us (refract 22 + IR 28): 2.3x over "
                            "a 2.0x trust floor. Reversing order by < 113 us inside the 240 us "
                            "window would have invented a foam hold on an already-legal 92.4 Brix.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "inline refractometer Brix, 2 kHz, 22 us jitter",
                    "foam-IR camera, 200 Hz, 28 us jitter",
                    "vacuum PT (context)",
                    "calandria steam flow (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("brix_cap", 96.0),
                        ("observed_brix", 92.4),
                        ("foam_ir_glint", 98.0),
                        ("proposed_strike", True),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. SP-5 seeded; massecuite at 92.4 Brix under 96.0 cap.",
                    "2. Foam-IR glint 98 from calandria lighting, not solids.",
                    "3. Vacuum precursor at 0.740 ms.",
                    "4. Race window [3.800, 4.040] ms.",
                    "5. refract.brix 92.4 at 3.860 ms (winner).",
                    "6. ir.foam.glint 98 at 3.973 ms (loser by 113 us).",
                    "7. Gate at 4.420 ms: ACCEPT strike as proposed.",
                    "8. Drop executes; Brix remains 92.4 < 96.0.",
                    "9. Pan emptied; next strike queued.",
                    "10. Delayed (strike_hold_s=300): 5 min crystal-size survey. Not a safety inflection.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "strike_drop_sp5"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("strike", True),
                        ("hold", False),
                        ("vacuum_kPa", 18.0),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("brix", 92.4),
                        ("brix_cap", 96.0),
                        ("foam_ir_glint", 98.0),
                        ("race_margin_us", 113),
                        ("combined_jitter_us", 50),
                        ("strike_hold_s", 300),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes the strike because refractometer 92.4 is under the 96.0 "
                "cap; foam-IR 98 is lighting, not load.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Refractometer 92.4 Brix is under the 96.0 strike cap. Foam-IR 98 is a "
                "calandria glint, not solids. ACCEPT the proposed drop; do not invent a hold.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "brix",
                            OrderedDict(
                                [
                                    ("cap", 96.0),
                                    ("observed", 92.4),
                                    ("foam_ir_glint", 98.0),
                                ]
                            ),
                        ),
                        (
                            "strike",
                            OrderedDict(
                                [
                                    ("proposed", True),
                                    ("executed", True),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 113),
                                    ("combined_jitter_us", 50),
                                    ("ratio", 2.26),
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
            ("name", "strike_drop_sp5"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("strike", True),
                        ("hold", False),
                        ("vacuum_kPa", 18.0),
                    ]
                ),
            ),
            (
                "gate_effect",
                "ACCEPT: proposed strike executed unchanged. Brix 92.4 < 96.0; foam glint unused.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT dropped SP-5 at 92.4 Brix. Foam-IR 98 was lighting, not load. "
                "The proposal was already legal; reversing 113 us would have invented a hold.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("pan", "strike executed; Brix 92.4 < 96.0"),
                        ("foam_ir", "98 glint unused as solids"),
                        ("vacuum", "held 18.0 kPa through the drop"),
                        ("mission", "strike committed"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Foam-IR 98 is a legal lighting glint, not a high-Brix alarm; brix-first discarded a false hold.",
                    "Delayed (5 min / strike_hold_s=300): crystal-size survey. Not a safety inflection.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "refract.brix (3.860 ms, 92.4)"),
                        ("loser", "ir.foam.glint (3.973 ms, 98 lighting)"),
                        ("margin_us", 113),
                        (
                            "counterfactual_if_reversed",
                            "Foam-first by < 113 us inside the 240 us window would have held "
                            "the drop on a false high-Brix story. The proposal was already "
                            "under the 96.0 cap, so the correct gate is still ACCEPT.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 4420),
            (
                "reward_inflection_note",
                "Task and safety step up at the ACCEPT gate (4.420 ms, tick 4). Tick 6 is "
                "strike_hold_s=300.",
            ),
        ]
    )
    ras = raster_core(
        22,
        80,
        32,
        56,
        routing(
            "thalamic-relay.pan-brix",
            "spikenaut.policy.strike-accept",
            [
                ("relay.refract.brix", "policy.strike_go", 0.62),
                ("relay.ir.foam", "policy.foam_hold", 0.28),
                ("relay.pt.vacuum", "policy.strike_go", 0.14),
            ],
            "adenosine",
            0.16,
            "pre_post_stdp; adenosine at brix win (3.860 ms) opens 160 ms eligibility covering the 4.420 ms accept",
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
            ("decision_window_ms", 0.24),
            ("decision", "ACCEPT"),
            (
                "populations",
                [
                    pop("strike_go", 40, 0.50, 312.5, 3),
                    pop("foam_hold", 40, 0.50, 20.8, 0),
                    pop("brix_cap_veto", 20, 0.80),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r28-160"),
            (
                "title",
                "Massecuite-Kettle MK-2 / Strike-Pan SP-5: refractometer 92.4 beats foam-IR "
                "glint; correct ACCEPT of an already-legal strike (total +1.16)",
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
                    "Correct ACCEPT. Brix 92.4 < 96.0; foam glint is lighting, not load. "
                    "total +1.16 = 0.44 + 0.34 + 0.18 + 0.12 + 0.08.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "sugar-vacuum-pan",
                    [
                        "accept",
                        "simulated-lighting",
                        "brix-vs-foam",
                        "strike",
                        "simulated",
                    ],
                    "Teaches that a foam-IR lighting glint can lose to a legal refractometer "
                    "inside a 240 us window; reversing 113 us would have invented a hold on an "
                    "already-legal strike.",
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
    for prior in Path("/tmp").glob("ttf-r*/batch-r*.jsonl"):
        if prior.resolve() == BATCH_PATH.resolve():
            continue
        try:
            prior_lines = prior.read_text(encoding="utf-8").splitlines()
        except OSError:
            continue
        for line in prior_lines:
            if not line.strip():
                continue
            prec = json.loads(line)
            pdesc = prec.get("state", {}).get("description", "")
            pid = prec.get("id", prior.name)
            for rec in records:
                val = jaccard(rec["state"]["description"], pdesc)
                jmax = max(jmax, val)
                if val >= 0.4:
                    issues.append(f"Jaccard {rec['id']}/{pid} = {val:.3f}")
    domains = [r["state"]["domain"] for r in records]
    if len(set(domains)) != 5:
        issues.append(f"domain collision {domains}")
    banned = {
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
        "brewery-CIP",
        "ski-lift",
        "data-center-CDU",
        "canal-lock",
        "blast-furnace",
        "aluminum-potline",
        "subsea-cable-plough",
        "rotary-lime-kiln",
        "lng-open-rack",
        "metro-psd",
        "vial-lyophilizer",
        "sts-quay-crane",
        "lyophilizer-shelf",
        "hvdc-thyristor-valve",
        "lng-unloading-arm",
        "cyclotron-target",
        "maglev-guideway-gap",
        "grain-elevator-leg",
        "hyperbaric-weld-habitat",
        "tunnel-oven-bakery",
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
        "grain-elevator",
        "rotary-kiln-cement",
        "submarine-cable-lay",
    }
    if set(domains) & banned:
        issues.append(f"banned domains {set(domains) & banned}")
    wrong = [
        r
        for r in records
        if r["safety_decision"].get("correctness") == "incorrect"
        or r["meta"].get("supervisor_error_type")
    ]
    if len(wrong) != 1 or wrong[0]["id"] != "ttf-r28-157":
        issues.append(f"wrong-gate set {[w['id'] for w in wrong]}")
    if any(r["state"]["sim_or_real"] == "real" for r in records):
        issues.append("sim_or_real=real")
    hil = [r["id"] for r in records if r["state"]["sim_or_real"] == "hil"]
    if hil != ["ttf-r28-158"]:
        issues.append(f"hil set {hil}")
    decisions = [r["safety_decision"]["decision"] for r in records]
    if decisions.count("ACCEPT") != 1 or decisions.count("MODIFY") != 2 or decisions.count("REJECT") != 2:
        issues.append(f"gate mix {decisions}")
    expected_ids = [f"ttf-r28-{n}" for n in range(156, 161)]
    if [r["id"] for r in records] != expected_ids:
        issues.append(f"ids {[r['id'] for r in records]}")
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
        if rec["id"] == "ttf-r28-156":
            if rec["raster"].get("excerpt_source") != "independent_lif":
                issues.append("156 missing independent_lif")
            if rec["future_outcome"]["reward_inflection_t_us"] > rec["raster"]["window_ms"] * 1000:
                issues.append("156 inflection outside window")
            if rec["reward_components"]["total"] >= 0:
                issues.append("156 partnered-neg total not negative")
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
        if rec["meta"]["round"] != 28:
            issues.append(f"{rec['id']} meta.round")
        if rec["meta"]["rights"]["intended_use"] != "research_only":
            issues.append(f"{rec['id']} rights")
        if rec["meta"]["rights"]["linear_issue"] != "RM-793":
            issues.append(f"{rec['id']} RM-793")
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
        dw_s = rec["gate_snn"]["decision_window_ms"] / 1000.0
        for popu in rec["gate_snn"]["populations"]:
            if "mean_rate_hz" in popu:
                exp = round(popu["neurons"] * popu["mean_rate_hz"] * dw_s)
                if abs(popu["spikes"] - exp) > 1:
                    issues.append(
                        f"{rec['id']} gate_snn {popu['name']} spikes {popu['spikes']} vs {exp}"
                    )
        if not (8 <= len(rec["raster"]["excerpt"]) <= 16):
            issues.append(f"{rec['id']} excerpt n={len(rec['raster']['excerpt'])}")
        if rec["state"]["sim_or_real"] not in {"designed", "simulated", "hil"}:
            issues.append(f"{rec['id']} provenance")
        table_tos = {row["to"] for row in rec["raster"]["routing"]["table"]}
        if rec["id"] == "ttf-r28-157":
            if "policy.stem_go" in table_tos:
                issues.append("157 routing has stem_go")
            if "policy.stem_hold" not in table_tos:
                issues.append("157 missing stem_hold routing")
        win_ms = rec["raster"]["window_ms"]
        if not (20 <= win_ms <= 50):
            issues.append(f"{rec['id']} window_ms {win_ms}")
        for item in rec["raster"]["excerpt"]:
            if not (0 <= item["t_us"] <= win_ms * 1000):
                issues.append(f"{rec['id']} excerpt t_us {item['t_us']}")
            if not (0 <= item["neuron_id"] < rec["raster"]["neurons"]):
                issues.append(f"{rec['id']} neuron_id {item['neuron_id']}")
    notes_hits = [ln for ln in NOTES.splitlines() if ln.strip().lower().startswith("novel coverage")]
    if notes_hits != ["Novel coverage: 24.0%"]:
        issues.append(f"novel coverage lines {notes_hits}")
    return issues, jmax


NOTES = """# Thalamic Trajectory Factory — NOTES-r28

- Factory: `thalamic-trajectory-factory`
- Run label: `2026-09-02-final-heavy`
- Generator: `grok-4.6`
- Channel: SuperGrok Heavy consumer chat (RM-793 research-only)
- Quota: 5
- IDs: `ttf-r28-156` … `ttf-r28-160`
- Domains this batch: `tire-curing-press`, `hdd-pilot-bore`, `chlor-alkali-membrane`, `hydro-penstock`, `sugar-vacuum-pan`

These five domain slugs sit outside the r12 set and outside staged r13–r24 occupancy (including r22 `rotary-lime-kiln`, r23 `aluminum-potline`, r24 `subsea-cable-plough`). All five plants are invented. Do not restack r12–r24 plants (Marrow-Dock, Vesper-Lattice, Brine-Well, Saddle-Arc, Ashlar-Gait, Nacre-Well, Quern-Forge, Tinder-Box, Whimbrel-Stack, Cinder-Loft, Oolite-Span, Fathom-Lock, Loess-Stride, Swage-Holt, Slag-Siding, Kiln-Spur, Suture-Isle, Oxbow-Switch, Pitch-Kettle, Shale-Quay, Polder-Rye, Flint-Mask, Gyre-Tokamak, Quarry-Bowl, Amber-Arm, Wort-Cairn, Firn-Span, Sleet-Row, Oxbow-Pound, Tuyere-Holt, Lye-Rake, Rime-Haul, Glycol-Loop, Tiller-9, Burden-Pike, Grapple-K4, Apside-Yard, Sump-Drift, Felt-Reach, Frost-Cist, Clothoid-Bowl, Bracken-Wire, Cullet-Reach, Rime-Causeway, Abyss-Joint, Gnomon-Well, Scree-Hitch, Solder-Kite, Bog-Drum, Ebb-Latch, Chaff-Rise, Sinter-Ridge, Chaff-Mere, Caisson-Forge, Crumb-Vault, Caliche-Drift, Thaw-Reach, Kipple-Gate, Anode-Fen, Vial-Rime, Tern-Apron, Lyo-Deck, Fjord-Convert, Kelp-Jetty, Skerries-Trench, Iodine-Well).

## Batch map

| id | domain | decision | correctness | sim_or_real | total | edge |
|----|--------|----------|-------------|-------------|-------|------|
| ttf-r28-156 | tire-curing-press | MODIFY | correct | designed | **−0.44** | process-correct bladder clamp; mold flash inside 42 ms raster; independent LIF |
| ttf-r28-157 | hdd-pilot-bore | REJECT | **incorrect (wrong-reject)** | designed | −0.58 | stem 18.4 kNm < 42.0 cap; supervisor treats mud 31.2 bar as stem excursion |
| ttf-r28-158 | chlor-alkali-membrane | REJECT | correct | hil | +0.78 | membrane 4.80 V beats shunt 4.12; hold, do not crawl |
| ttf-r28-159 | hydro-penstock | MODIFY | correct | designed | +0.92 | pitot 9.40 m/s vs staff false-calm; clamp leaf 72 → 41 percent |
| ttf-r28-160 | sugar-vacuum-pan | ACCEPT | correct | simulated | +1.16 | Brix 92.4 vs foam-IR glint 98; proposed strike already legal |

Gate mix: 1 ACCEPT, 2 MODIFY, 1 correct REJECT, 1 incorrect REJECT (wrong-reject). Provenance: designed×3, simulated×1, hil×1 (Natron-Hall NH-2 membrane-cell mockup). Jaccard on `state.description` must stay < 0.4 vs intra-batch and vs staged r13–r24.

## Wrong-reject

**ttf-r28-157** is the mandated incorrect gate (`safety_decision.correctness=incorrect`, `meta.supervisor_error_type=wrong-reject`). Alternate vs odd rounds: r12/r14/r16/r18/r20/r22/r24/r26/r28 host wrong-reject; r13/r15/r17/r19/r21/r23/r25/r27 host wrong-modify. Do not emit a wrong-ACCEPT.

Wych-Bore WB-7 / Pilot-Stem PS-4 reads stem-torque `18.4 kNm` against a **42.0 kNm** stem cap. Mud-pump residual is **31.2 bar** on a different circuit whose cap is **48.0 bar**. Sidecar arithmetic `18.4 < 42.0` is true. A weak supervisor treats “the load loop” as one circuit, REJECTs the 1.40 m/s push, and holds stem. Convictable without HDD physics: `evidence.stem_kNm < evidence.stem_cap_kNm`, `stem_circuit_id == stem`, `mud_circuit_id == mud`, `executed_action` sets `push_m_s=0` without a stem over-cap, `raster.routing.table` sends `relay.pump.mud` → `policy.stem_hold` (weight 0.73) with no positive weight to `policy.stem_go`, and `gate_snn` has `stem_hold` above threshold while `stem_go` is not. Recovery: ACCEPT the 1.40 m/s push; leave mud 31.2 bar to its own 48.0 bar cap. Cost: missed 24 min daylight window (`missed_window_s=1440`).

## Partnered-negative in-window (156)

**ttf-r28-156** is the partnered negative: process-correct MODIFY (flash-face held 1.72 MPa < 1.80 cap) while the world still charges. Safety −0.56 prices the 40 mm mold flash at **22.600 ms**; `task_progress` stays +0.32 because the clamp completed. Inflection `t_us=22600` is tick 5 and is **inside** the 42 ms raster (`22600 ≤ 42000`). Named un-netted loss: 14 min mold-clean (`abort_s=840`). Not folded into process heads.

Independent LIF (the one labeled sidecar sim): `state.sim_or_real` remains `designed`. `raster.excerpt_source=independent_lif`, `raster.sim_scope=sidecar_only`, `raster.lif` seed 28156, stim `[22000, 25000]`. Excerpt is membrane crossings (`lif.clamp` early vs `lif.flash` 22–25 ms), not a 1:1 remap of `spike_events`. `meta.tags` include `independent-lif-raster` and `sidecar-sim-only`.

## Reward formula and tick reconciliation

Declared aggregation on every record:

`total = task_progress + safety + efficiency + coherence + exploration`

Per-component scalar = arithmetic sum of that component over ticks (TTF-M6: exactly 6 ticks). Tick 6 is bound to a published sidecar (`abort_s`, `missed_window_s`, `penstock_reseq_s`, `strike_hold_s`) and is strictly after the raster window. Inflection `t_us` is an actual tick.

| id | ticks | tp | saf | eff | coh | exp | total | inflection tick |
|----|-------|----|-----|-----|-----|-----|-------|-----------------|
| 156 | 6 | +0.32 | −0.56 | −0.16 | +0.02 | −0.06 | −0.44 | 5 (22600) |
| 157 | 6 | −0.20 | −0.10 | −0.22 | −0.12 | +0.06 | −0.58 | 4 (5000) |
| 158 | 6 | +0.10 | +0.40 | +0.12 | +0.10 | +0.06 | +0.78 | 4 (6980) |
| 159 | 6 | +0.34 | +0.30 | +0.14 | +0.10 | +0.04 | +0.92 | 4 (7330) |
| 160 | 6 | +0.44 | +0.34 | +0.18 | +0.12 | +0.08 | +1.16 | 4 (4420) |

Tick-6 sidecar bind: 156 `abort_s=840`, 157 `missed_window_s=1440`, 158 `abort_s=600`, 159 `penstock_reseq_s=480`, 160 `strike_hold_s=300`.

## Raster / energy (Loihi-2 4-core, 23 pJ/spike)

| id | domain | n | rate Hz | window_ms | spikes | energy_pJ | energy_uJ |
|----|--------|---|---------|-----------|--------|-----------|-----------|
| 156 | tire-curing-press | 68 | 28 | 42 | 80 | 1840 | 0.001840 |
| 157 | hdd-pilot-bore | 92 | 36 | 24 | 79 | 1817 | 0.001817 |
| 158 | chlor-alkali-membrane | 112 | 22 | 40 | 99 | 2277 | 0.002277 |
| 159 | hydro-penstock | 56 | 44 | 30 | 74 | 1702 | 0.001702 |
| 160 | sugar-vacuum-pan | 80 | 32 | 22 | 56 | 1288 | 0.001288 |

`spikes = round(n × rate × window_s)`. Every record carries `gate_snn` whose `decision` matches the safety gate; populations that declare rate+spikes meet the same ±1 budget against `decision_window_s`. `routing.third_factor` has modulator (NA / ACh / DA / 5-HT / adenosine), `tau_e_s`/`tau_e_ms` pair, and eligibility. Excerpt same-neuron gap ≥ 1000 µs; spike trains same-channel refractory ≥ 0.8 ms. Non-156 excerpts are kernelized and independent of `spike_events` times (overlap < 0.8).

## Local checks (staging, not raw)

See generator stdout: `check_jsonl` FactoryStaging, `validate_run.check_line`, `dumps_exact_json`, `raster_status`, `verify_batch_for_frontier(strict=True)`, `spike_probe.py --strict`, tick sums, refractory, Jaccard.

Never `training_ready`. Never `sim_or_real=real`. Never wrote `outputs/raw/`.

## Residual weaknesses (honest)

1. Only **one** labeled independent LIF (156). The other four excerpts are independent of `spike_events` times but are not declared population sims.
2. Wrong-ACCEPT still absent (guard).
3. Tick-6 sidecar bind is a densification of r14/r16, not a new class.
4. Five domain slugs leave the prompt's 8-item pool; a later round that must stay inside the pool will have to rotate sit-outs instead.
5. 157 wrong-reject is sidecar-convictable (routing `to` / circuit IDs) but still the same error *class* as r16-097 (wrong-stage mixup).
6. 160 ACCEPT is an already-legal proposal confirmed by race order; a later round could pair an ACCEPT with a world charge that does not go negative.

## Next densification target

Labeled LIF on a second record, or an ISI histogram sidecar. If a later round returns to the 8-item pool, sit out the r12 five again and pick a wrong-MODIFY that is neither J2-axis nor a stage/drum mixup (wrong-phase of a cyclic process). Wrong-ACCEPT remains structurally absent until a prompt amendment.

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
        BATCH_PATH, "batch-r28.jsonl", staging=FactoryStaging(enabled=True)
    )
    report.append(("check_jsonl FactoryStaging", errors, warnings, kinds, nrec))
    line_errs = []
    for i, rec in enumerate(records, 1):
        errs, kind = check_line(rec, f"batch-r28.jsonl:{i}", factory_staging=True)
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
    records = [record_156(), record_157(), record_158(), record_159(), record_160()]
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
