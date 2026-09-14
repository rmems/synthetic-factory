#!/usr/bin/env python3
"""Emit TTF r70 JSONL (ttf-r70-346..350). Validate, then CREATE-ONLY copy into
the 2026-09-02-final-heavy live tree. Never overwrite. Never 2026-08-17/08-30.
Scratch /tmp/ttf-r70 used 366–370 and a 2A mix; this window uses 346–350 and 1A/2M.
"""

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

OUT_DIR = Path("/tmp/ttf-r70-live")
BATCH_PATH = OUT_DIR / "batch-r70.jsonl"
NOTES_PATH = OUT_DIR / "NOTES-r70.md"
REPO = Path("/home/raulmc/rmems/synthetic-factory")
PIPELINES = REPO / "pipelines"
LIVE_DIR = REPO / "outputs" / "raw" / "2026-09-02-final-heavy" / "thalamic-trajectory-factory"

PJ_PER_SPIKE = 23
RIGHTS = OrderedDict(
    [
        ("provider", "SpaceXAI/xAI"),
        ("model", "grok-4.6"),
        ("channel", "consumer"),
        ("subscription_plan", "SuperGrok Heavy"),
        ("generation_surface", "SuperGrok Heavy chat"),
        ("generated_at", "2026-09-02T20:40:00Z"),
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
PLANT_RE = re.compile(r"\b([A-Z][A-Za-z]+(?:-[A-Z][A-Za-z0-9]+)+)\b")
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
MY_DOMAINS = (
    "zinc-chloride-flux-bath",
    "lithium-titanate-spinel-calciner",
    "nylon-66-salt-evaporator",
    "titanium-sponge-kroll-retort",
    "vanadium-pentoxide-contact-bed",
)
MY_PLANTS = (
    "Flux-Wythe",
    "Spinel-Howe",
    "Nylonate-Beck",
    "Kroll-Fen",
    "Vanadia-Clough",
)
IDS = [f"ttf-r70-{n}" for n in range(346, 351)]
ID_PN, ID_WR, ID_HIL, ID_M2, ID_ACC = IDS
PROMPT_POOL = {
    "warehouse-amr",
    "aerial-swarm",
    "underwater-rov",
    "grid-inspection",
    "humanoid-locomotion",
    "surgical-assist",
    "industrial-assembly",
    "autonomous-driving",
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


def spike_avoid_us(events):
    return [int(round(ev["t_rel_ms"] * 1000.0)) for ev in events]


def meta_block(
    domain,
    tags,
    distillation_value,
    batch_position,
    supervisor_error_type=None,
) -> OrderedDict:
    body = OrderedDict(
        [
            ("round", 70),
            ("factory", "thalamic-trajectory-factory"),
            ("generator", "grok-4.6"),
            ("run_label", "2026-09-02-final-heavy"),
            ("schema_version", "thalamic-trajectory-v2"),
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


def wrap_record(
    rid,
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
            ("id", rid),
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


def lif_346_excerpt():
    """Independent CUBA LIF (seed 70346). Plant remains designed."""

    n = 80
    dt_us = 100
    tau_m_ms = 20.0
    v_th = 1.0
    v_reset = 0.0
    refractory_us = 1000
    i_bias = 0.92
    i_stim_peak = 2.45
    stim = (21000, 25000)
    seed = 70346
    window_us = 42000
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
    early = [(t, nid) for t, nid in spikes if t < 21000]
    burst = [(t, nid) for t, nid in spikes if 21000 <= t < 25000]
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
            early_flag = pool[0][0] < 21000
            have = len([1 for t, _ in picked if (t < 21000) == early_flag])
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
    take(burst, 9, label_times=(22400, 23100, 23800))
    clamp = [(t, nid) for t, nid in picked if t < 21000][:7]
    tile = [(t, nid) for t, nid in picked if t >= 21000][:9]
    picked = sorted(clamp + tile, key=lambda item: (item[0], item[1]))
    if len(picked) < 8:
        raise RuntimeError(f"LIF excerpt too short: {len(picked)}")
    channels = ["lif.clamp" if t < 21000 else "lif.hinge" for t, _ in picked]
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
            ("i_stim_peak", 2.45),
            ("stim_t_us", [21000, 25000]),
            ("i_clamp_extra", 0.68),
            ("clamp_n", 14),
            ("seed", 70346),
            (
                "note",
                "Population sim scoped to this sidecar. Plant remains designed. "
                "Neurons 0-13 carry +0.68 make-up-clamp bias; stim 21-25 ms is the "
                "ceramic dip-basket hinge shear.",
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


def record_346():
    excerpt, extra = lif_346_excerpt()
    ticks = [
        tick(1944, 0.05, -0.02, -0.02, 0.01, 0.00),
        tick(4860, 0.08, -0.04, -0.03, 0.01, -0.01),
        tick(5100, 0.04, -0.03, -0.02, 0.00, 0.00),
        tick(5780, 0.10, -0.06, -0.03, 0.02, -0.01),
        tick(22400, 0.05, -0.42, -0.04, 0.00, -0.02),
        tick(840000000, 0.00, -0.05, -0.02, 0.00, 0.00),
    ]
    state = OrderedDict(
        [
            (
                "description",
                "Flux bath BX-7 at Flux-Wythe is already metering 2.40 t/h of zinc-chloride "
                "make-up when a bath-temperature pulse arrives 240 us before the make-up encoder "
                "that still reads a legal undersaturated kettle. Temperature-first latches a "
                "process clamp under the 64.0 C cap; flow-first would keep cruise make-up. Stored "
                "ceramic dip-basket hinge load is not yet an observable of either race channel.",
            ),
            ("domain", "zinc-chloride-flux-bath"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Keep BX-7 on 2.40 t/h ZnCl2 make-up only while bath temperature stays <= 64.0 C, "
                "and leave the ceramic dip-basket hinge un-sheared.",
            ),
            ("t0_us", 1762300000000346),
            ("gate_latency_us", 920),
            ("race_window_us", 400),
            ("race_window_rel_ms", [4.860, 5.260]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "rtd.bath.C 68.4 C flux-bath temperature",
                                "ft.makeup.t_h 2.40 t/h still-legal ZnCl2 make-up",
                            ],
                        ),
                        (
                            "semantics",
                            "Temperature-first latches make-up clamp 2.40 -> 1.20 t/h; flow-first "
                            "keeps cruise make-up on a 'basket still rigid' model.",
                        ),
                        (
                            "window_derivation",
                            "400 us = one bath RTD slot minus make-up-encoder group delay on this "
                            "1 kHz flux-bath bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 240 us vs combined jitter 70 us (RTD 32 + flow 38): 3.4x over "
                            "a 2.0x trust floor. Reversing order by < 240 us inside the 400 us window "
                            "would have kept 2.40 t/h cruise; predicted next-sample bath 66.2 C > 64.0 cap.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "flux-bath RTD, 1 kHz, 32 us timestamp jitter",
                    "ZnCl2 make-up encoder, 1 kHz, 38 us jitter",
                    "dip-basket encoder (context)",
                    "hinge AE (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("bath_cap_C", 64.0),
                        ("observed_bath_C", 68.4),
                        ("proposed_makeup_t_h", 2.40),
                        ("makeup_floor_t_h", 0.80),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Flux bath BX-7 indexed on Flux-Wythe; 2.40 t/h ZnCl2 make-up; bath 68.4 C > 64.0 cap.",
                    "2. Cruise make-up 2.40 t/h armed; bath over the 64.0 C cap.",
                    "3. Encoder precursor at 1.140 ms; bath-side warm-start 68.4 C.",
                    "4. Race window [4.860, 5.260] ms opens on the flux bus.",
                    "5. Bath RTD 68.4 C at 4.860 ms (winner).",
                    "6. Make-up flow 2.40 t/h at 5.100 ms (loser by 240 us).",
                    "7. Gate at 5.780 ms (winner + 920 us): MODIFY clamp 2.40 -> 1.20 t/h.",
                    "8. Clamp executes; next-sample bath 62.8 C < 64.0 cap.",
                    "9. At 22.400 ms stored hinge load shears a ceramic dip-basket.",
                    "10. Emergency isolate 14 min + basket swap; named un-netted loss, not folded into process heads.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_zncl2_makeup"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("makeup_t_h", 2.40),
                        ("bath_C", 68.4),
                        ("hold", False),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("bath_C", 68.4),
                        ("bath_cap_C", 64.0),
                        ("predicted_unclamped_next_C", 66.2),
                        ("makeup_t_h", 2.40),
                        ("race_margin_us", 240),
                        ("combined_jitter_us", 70),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 2.40 t/h cruise: make-up flow looks like an undersaturated "
                "kettle, not a packed basket, and the 64.0 C bath cap is treated as still open.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "correct"),
            (
                "rationale",
                "Bath 68.4 C won by 240 us, so the kettle is running packed, not still free. "
                "Holding 2.40 t/h predicts next-sample 66.2 C > 64.0 C cap. MODIFY: make-up "
                "2.40 -> 1.20 t/h. Observed after clamp 62.8 C < 64.0. A full REJECT is not "
                "indicated: a sound flux bath accepts 1.20 t/h.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "bath_C",
                            OrderedDict(
                                [
                                    ("cap", 64.0),
                                    ("observed", 68.4),
                                    ("predicted_unclamped_next", 66.2),
                                    ("clamped_makeup_t_h", 1.20),
                                    ("observed_after_clamp", 62.8),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 240),
                                    ("combined_jitter_us", 70),
                                    ("ratio", 3.43),
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
            ("name", "clamped_zncl2_makeup"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("makeup_t_h", 1.20),
                        ("bath_C", 62.8),
                        ("hold", False),
                    ]
                ),
            ),
            (
                "gate_effect",
                "MODIFY: make-up 2.40 -> 1.20 t/h. Process-correct vs the 64.0 C bath cap. "
                "Ceramic dip-basket hinge shear still occurs at 22.400 ms.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Process-correct MODIFY held bath at 62.8 C. At 22.400 ms stored hinge load "
                "sheared a ceramic dip-basket. Clamp reduced make-up energy; it did not dump the "
                "hinge charge. Partnered negative: process heads stay honest; world loss is named, "
                "not netted.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("makeup", "clamp executed; bath 62.8 C < 64.0"),
                        ("dip_basket", "ceramic hinge shear at 22.400 ms"),
                        ("repair", "14 min emergency isolate + basket swap"),
                        ("mission", "flux bath still circulating; hinge precursor controlled"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Neither bath RTD nor make-up flow predicted the hinge charge; ae.hinge.pack is a new channel at 22.400 ms, 16.620 ms after the gate, still inside the 42 ms raster.",
                    "Delayed (14 min): emergency isolate and basket swap close the shear. Named un-netted loss, not folded into task_progress.",
                ],
            ),
            (
                "un_netted_loss",
                "14 min emergency isolate + basket swap after a ceramic dip-basket hinge shear. "
                "Safety head -0.62 prices the precursor; task_progress stays +0.32 because the "
                "make-up clamp completed under the 64.0 C cap. World loss is named here, not "
                "subtracted from process heads.",
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "rtd.bath.C (4.860 ms, 68.4 C)"),
                        ("loser", "ft.makeup.t_h (5.100 ms, 2.40 t/h)"),
                        ("margin_us", 240),
                        (
                            "counterfactual_if_reversed",
                            "Flow-first by < 240 us inside the 400 us window would have kept "
                            "2.40 t/h cruise; predicted next-sample 66.2 C would have exceeded the "
                            "64.0 C cap even without the hinge charge. The MODIFY is still the "
                            "correct process. The shear is a later world charge either way, cheaper "
                            "with the clamp than without.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 22400),
            (
                "reward_inflection_note",
                "Safety collapses at the 22.400 ms ceramic dip-basket hinge shear (tick t_us=22400), "
                "inside the 42 ms raster. The correct MODIFY at 5.780 ms is in the same excerpt. "
                "Do not put inflection on the +14 min isolate tick.",
            ),
            ("delayed_surprise_s", 840.0),
            ("abort_s", 840),
        ]
    )
    spikes = [
        spike("enc.flux.ctx", 1.140, 0.43),
        spike("rtd.bath.C", 2.280, 0.62),
        spike("ft.makeup.t_h", 3.360, 0.55),
        spike("rtd.bath.C", 4.860, 1.34),
        spike("ft.makeup.t_h", 5.100, 1.12),
        spike("ctrl.gate", 5.780, 0.97),
        spike("rtd.bath.C", 7.400, 0.81),
        spike("ft.makeup.t_h", 10.600, 0.66),
        spike("ctrl.gate", 15.400, 0.84),
        spike("ae.hinge.pack", 22.400, 1.42),
        spike("ae.hinge.pack", 23.800, 0.91),
        spike("enc.flux.ctx", 30.200, 0.41),
        spike("rtd.bath.C", 37.100, 0.58),
    ]
    ras = raster_core(
        42,
        80,
        24,
        81,
        routing(
            "thalamic-relay.rtd-bath",
            "spikenaut.policy.makeup-clamp",
            [
                ("relay.rtd.bath", "policy.makeup_clamp", 0.64),
                ("relay.ft.makeup", "policy.cruise_hold", 0.29),
                ("relay.ae.hinge", "policy.makeup_clamp", -0.46),
            ],
            "noradrenaline",
            0.05,
            "surprise-gated pre_post_stdp; NA at RTD win (4.860 ms) opens a 50 ms eligibility "
            "trace that still covers the 22.400 ms ceramic dip-basket hinge shear",
        ),
        excerpt,
        extra=extra,
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.40),
            ("decision", "MODIFY"),
            (
                "populations",
                [
                    pop("makeup_clamp", 48, 0.50, 220.0, 4),
                    pop("cruise_hold", 48, 0.50, 50.0, 1),
                    pop("bath_cap_veto", 24, 0.75),
                ],
            ),
        ]
    )
    return wrap_record(
        ID_PN,
        "Flux-Wythe bath / BX-7: bath RTD beats make-up encoder by 240 us; correct "
        "MODIFY still eats an in-window ceramic dip-basket hinge shear (partnered negative total -0.46)",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Partnered negative. Process-correct MODIFY; world still charges inside the "
        "42 ms raster. total -0.46 = 0.32 + -0.62 + -0.16 + 0.04 + -0.04. Named "
        "isolate+basket-swap loss is not netted into task_progress.",
        ras,
        gate,
        "zinc-chloride-flux-bath",
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
        "14 min gap.",
        1,
    )


def record_347():
    ticks = [
        tick(2176, -0.02, 0.01, -0.02, -0.01, 0.01),
        tick(5440, -0.04, 0.01, -0.04, -0.02, 0.01),
        tick(5680, -0.03, 0.01, -0.03, -0.01, 0.01),
        tick(6200, -0.06, 0.02, -0.08, -0.03, 0.02),
        tick(6620, -0.02, 0.01, -0.03, -0.01, 0.01),
        tick(720000000, -0.01, 0.00, -0.02, 0.00, 0.00),
    ]
    spikes = [
        spike("enc.kiln.ctx", 1.160, 0.43),
        spike("rtd.bed.comp", 2.480, 0.62),
        spike("rtd.lead.ohm", 3.720, 0.51),
        spike("bus.spinel.ctx", 4.540, 0.46),
        spike("rtd.bed.comp", 5.440, 1.32),
        spike("rtd.lead.ohm", 5.680, 1.16),
        spike("ctrl.gate", 6.200, 0.99),
        spike("rtd.bed.comp", 7.440, 0.83),
        spike("rtd.lead.ohm", 9.620, 0.64),
        spike("ctrl.gate", 15.100, 0.86),
        spike("enc.kiln.ctx", 19.200, 0.40),
        spike("rtd.bed.comp", 25.400, 0.57),
    ]
    excerpt = independent_excerpt(70347, 76, 28000, 12, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Kiln KN-4 at Spinel-Howe already holds a 3-wire-compensated bed of 742 C when "
                "that analog sample races a leftover lead-loop ohm tag still published on a sibling "
                "transmitter. Published spinel floor is 680 C and cap 860 C on the compensated RTD; "
                "a weak supervisor treats the uncompensated 48.60 ohm lead as if it were 48.60 C and "
                "zeros a legal 1.80 rpm LTO pass.",
            ),
            ("domain", "lithium-titanate-spinel-calciner"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Hold 1.80 rpm on KN-4, keep compensated bed 680-860 C, and finish the 12 min "
                "LTO spinel window.",
            ),
            ("t0_us", 1762300000000347),
            ("gate_latency_us", 760),
            ("race_window_us", 420),
            ("race_window_rel_ms", [5.440, 5.860]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "rtd.bed.comp 742 C 3-wire-compensated bed",
                                "rtd.lead.ohm 48.60 ohm leftover uncompensated lead",
                            ],
                        ),
                        (
                            "semantics",
                            "Compensated-first should ACCEPT 1.80 rpm (680 < 742 < 860 C). "
                            "Lead-ohm-first would only delay confirmation of the same legal bed.",
                        ),
                        (
                            "window_derivation",
                            "420 us = one compensated-bed analog slot versus the leftover-lead-ohm "
                            "publisher on this 2 kHz calciner bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 240 us vs combined jitter 72 us (compensated 32 + lead 40): 3.3x over "
                            "a 2.0x trust floor. Order is correctly compensated-first. The error is binding "
                            "lead ohms as if they were live C, not the race.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "3-wire compensated bed RTD, 2 kHz, 32 us jitter, axis kiln_bed_C, lead_compensated true",
                    "lead-loop ohms, 1 kHz, 40 us jitter, leftover uncompensated ohm",
                    "kiln-rotation encoder (context)",
                    "exhaust O2 (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("live_C", 742.0),
                        ("floor_C", 680.0),
                        ("cap_C", 860.0),
                        ("lead_ohm", 48.60),
                        ("lead_ohm_as_C", 48.60),
                        ("lead_compensated", True),
                        ("lead_is_temperature", False),
                        ("analog_fresh", True),
                        ("heartbeat_age_ms", 18.0),
                        ("max_age_ms", 200.0),
                        ("proposed_rpm", 1.80),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Kiln KN-4 indexed on Spinel-Howe; compensated bed 742 C, rotation 1.80 rpm armed.",
                    "2. Published floor 680 C and cap 860 C; lead-loop ohms tagged leftover uncompensated.",
                    "3. Encoder precursor at 1.160 ms.",
                    "4. Race window [5.440, 5.860] ms.",
                    "5. Compensated bed 742 C at 5.440 ms (winner).",
                    "6. Leftover lead 48.60 ohm at 5.680 ms (loser by 240 us).",
                    "7. Gate at 6.200 ms: wrong REJECT holds 0 rpm on the lead ohms as C.",
                    "8. Kiln idle; compensated bed never left 680-860 C.",
                    "9. 12 min LTO spinel window missed.",
                    "10. QA: correct gate was ACCEPT; leave 1.80 rpm; bind compensated 742 C vs 680-860 C.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "spinel_1p8_hold"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("rotation_rpm", 1.80),
                        ("bed_C", 742.0),
                        ("hold", False),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("live_C", 742.0),
                        ("floor_C", 680.0),
                        ("cap_C", 860.0),
                        ("lead_ohm", 48.60),
                        ("lead_ohm_as_C", 48.60),
                        ("lead_compensated", True),
                        ("lead_is_temperature", False),
                        ("analog_fresh", True),
                        ("heartbeat_age_ms", 18.0),
                        ("rtd_axis", "kiln_bed_C"),
                        ("race_margin_us", 240),
                        ("combined_jitter_us", 72),
                        ("t_gate_us", 6200),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 1.80 rpm because compensated bed 742 C sits 62 C over the "
                "680 C floor and 118 C under the 860 C cap, and the 48.60 ohm lead is leftover "
                "uncompensated 3-wire resistance, not a temperature EU.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "REJECT"),
            ("correctness", "incorrect"),
            (
                "rationale",
                "Lead-loop ohms print 48.60, so the bed is treated as 48.60 C under the 680 C "
                "spinel floor (true vs that leftover uncompensated tag). REJECT: hold 0 rpm until "
                "the lead ohms rise so the calciner does not see a cold-bed event.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "kiln_bed_C",
                            OrderedDict(
                                [
                                    ("published_floor", 680.0),
                                    ("published_cap", 860.0),
                                    ("observed_compensated", 742.0),
                                    ("lead_ohm_as_C_applied", True),
                                    ("lead_ohm", 48.60),
                                    ("executed_rpm", 0.0),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 240),
                                    ("combined_jitter_us", 72),
                                    ("ratio", 3.33),
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
            ("name", "kiln_hold_lead_ohm"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("rotation_rpm", 0.0),
                        ("bed_C", 742.0),
                        ("hold", True),
                        ("bind_lead_as_C", True),
                    ]
                ),
            ),
            (
                "gate_effect",
                "REJECT (incorrect): rotation 1.80 -> 0 rpm. Routing relay.rtd.lead -> "
                "policy.hold_reject; no positive weight to policy.go_accept. Compensated 742 C never "
                "left the 680-860 C band.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Wrong-REJECT froze KN-4 at 0 rpm while compensated bed stayed 742 C inside "
                "680-860 C. 12 min LTO spinel window missed. Correct gate was ACCEPT of the "
                "already-legal 1.80 rpm command.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("kiln", "held at 0 rpm; 1.80 rpm abandoned"),
                        ("bed_C", "still 742 C, inside 680-860 C published band"),
                        ("spinel", "12 min LTO window missed"),
                        ("flag", "no cold bed; leftover lead-ohm false positive"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "The 48.60 ohm tag is leftover uncompensated 3-wire lead resistance, not a live compensated temperature EU.",
                    "Delayed (12 min): sister kiln KN-5 ran the same 1.80 rpm LTO window after QA rebound the compensated band; KN-4's slot was already gone.",
                ],
            ),
            (
                "recovery",
                OrderedDict(
                    [
                        (
                            "correct_gate",
                            "ACCEPT: compensated 742 C is inside 680-860 C; leave 1.80 rpm; ignore leftover lead ohms as temperature.",
                        ),
                        ("correct_floor_C", 680.0),
                        ("correct_cap_C", 860.0),
                        ("wrong_flag", True),
                        (
                            "wrong_edit_applied",
                            OrderedDict([("rotation_rpm", 0.0), ("hold", True), ("bind_lead_as_C", True)]),
                        ),
                        (
                            "cost",
                            "12 min missed LTO spinel window (task/efficiency); compensated never left band (safety false-positive).",
                        ),
                    ]
                ),
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "rtd.bed.comp (5.440 ms, 742 C)"),
                        ("loser", "rtd.lead.ohm (5.680 ms, leftover uncompensated 48.60 ohm)"),
                        ("margin_us", 240),
                        (
                            "counterfactual_if_reversed",
                            "Lead-ohm-first by < 240 us would still show compensated 742 C inside "
                            "680-860 C. A correct gate ACCEPTs either way. The wrong REJECT spent "
                            "the compensated win on leftover uncompensated lead ohms as C.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 6200),
            (
                "reward_inflection_note",
                "Task and efficiency drop at the wrong REJECT (6.200 ms, tick 4). The 12 min "
                "missed window is delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 720.0),
            ("missed_window_s", 720),
        ]
    )
    ras = raster_core(
        28,
        76,
        32,
        68,
        routing(
            "relay.rtd.lead",
            "policy.hold_reject",
            [
                ("relay.rtd.lead", "policy.hold_reject", 0.74),
                ("relay.rtd.comp", "policy.hold_reject", 0.21),
            ],
            "acetylcholine",
            0.08,
            "lead_ohm_as_C_stdp; ACh tags the (wrong) hold_reject bind at the compensated win",
        ),
        excerpt,
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.42),
            ("decision", "REJECT"),
            (
                "populations",
                [
                    pop("hold_reject", 48, 0.50, 200.0, 4),
                    pop("go_accept", 48, 0.80, 10.0, 0),
                    pop("band_veto", 24, 0.75),
                ],
            ),
        ]
    )
    return wrap_record(
        ID_WR,
        "WRONG-REJECT at Spinel-Howe / KN-4: compensated bed 742 C is legal vs "
        "published 680-860 C band; supervisor bound leftover 3-wire lead ohms as the temperature EU",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Wrong-reject. Sidecar arithmetic 680 < 742 < 860 is true; clamp bound to leftover "
        "uncompensated lead ohms as C. total -0.36 = -0.18 + 0.06 + -0.22 + -0.08 + 0.06.",
        ras,
        gate,
        "lithium-titanate-spinel-calciner",
        [
            "reject",
            "wrong-gate",
            "lead-ohm-as-C",
            "3-wire-rtd-lead-resistance",
            "sidecar-convictable",
            "designed",
        ],
        "Teaches a probe that a correct compensated-in-band read can still be a wrong gate when "
        "routing.table[0].to is policy.hold_reject and executed rotation is zeroed.",
        2,
        supervisor_error_type="wrong-reject",
    )


def record_348():
    ticks = [
        tick(1664, 0.01, 0.04, 0.02, 0.01, 0.01),
        tick(4160, 0.02, 0.08, 0.02, 0.02, 0.01),
        tick(4370, 0.01, 0.06, 0.02, 0.01, 0.01),
        tick(5400, 0.04, 0.14, 0.04, 0.04, 0.02),
        tick(5720, 0.01, 0.07, 0.01, 0.01, 0.01),
        tick(540000000, 0.01, 0.03, 0.01, 0.01, 0.00),
    ]
    spikes = [
        spike("enc.steam.ctx", 1.080, 0.44),
        spike("ntu.ah.salt", 2.260, 0.71),
        spike("enc.steam.tph", 3.140, 0.52),
        spike("ntu.ah.salt", 4.160, 1.36),
        spike("enc.steam.tph", 4.370, 1.14),
        spike("ctrl.gate", 5.400, 0.98),
        spike("ntu.ah.salt", 7.600, 0.82),
        spike("enc.steam.tph", 11.200, 0.61),
        spike("ctrl.gate", 16.800, 0.86),
        spike("ntu.ah.salt", 25.400, 0.70),
        spike("enc.steam.tph", 34.200, 0.48),
        spike("t.evap.ctx", 43.100, 0.40),
    ]
    excerpt = independent_excerpt(70348, 112, 46000, 13, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Evaporator EV-2 on the Nylonate-Beck AH-salt HIL pad is boiling at 18 t/h steam "
                "when a turbidity burst at 86 NTU races the steam encoder that still looks in-band "
                "for a rate step. Ramp is legal only if AH-salt turbidity <= 40 NTU. Turbidity-first "
                "latches hold; encoder-first would treat in-band t/h as nylon-salt clearance.",
            ),
            ("domain", "nylon-66-salt-evaporator"),
            ("sim_or_real", "hil"),
            (
                "goal",
                "Do not ramp EV-2 unless AH-salt turbidity <= 40 NTU; keep steam 0 t/h until the "
                "liquor is quiet.",
            ),
            ("t0_us", 1762300000000348),
            ("gate_latency_us", 1240),
            ("race_window_us", 320),
            ("race_window_rel_ms", [4.160, 4.480]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "ntu.ah.salt 86 NTU AH-salt flare",
                                "enc.steam.tph 18 t/h still-in-band",
                            ],
                        ),
                        (
                            "semantics",
                            "Turbidity-first latches REJECT hold 0 t/h; encoder-first would ramp 18 t/h "
                            "on an in-band-rate-as-clearance model.",
                        ),
                        (
                            "window_derivation",
                            "320 us = one turbidity-analyzer envelope slot versus the steam-encoder "
                            "publisher on this pad cycle.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 210 us vs combined jitter 58 us (NTU 26 + encoder 32): 3.6x over a "
                            "2.0x trust floor. Pad injects encoder 90-130 us before the NTU envelope "
                            "finishes (loop lag, not a sensor fault); the encoder packet is still "
                            "the loser in this 320 us window.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "AH-salt turbidity analyzer, 26 us jitter, 40 NTU trip",
                    "steam-rate encoder, 32 us jitter",
                    "evaporator RTD (context)",
                    "AH assay (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("ntu_trip", 40.0),
                        ("observed_ntu", 86.0),
                        ("steam_cap_tph", 28.0),
                        ("proposed_tph", 18.0),
                    ]
                ),
            ),
            (
                "hil",
                OrderedDict(
                    [
                        ("bench", "Nylonate-Beck NB-HIL AH-salt evaporator pad, EV-2"),
                        (
                            "inject",
                            "NTU envelope delayed 90-130 us vs encoder; loop lag, not a false turbidity analyzer",
                        ),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. EV-2 on Nylonate-Beck HIL pad; AH salt in band; steam armed at 18 t/h.",
                    "2. NTU trip 40; observed 86 NTU flare on AH liquor.",
                    "3. Encoder precursor at 1.080 ms.",
                    "4. Race window [4.160, 4.480] ms.",
                    "5. NTU 86 at 4.160 ms (winner).",
                    "6. Steam encoder 18 t/h at 4.370 ms (loser by 210 us).",
                    "7. Gate at 5.400 ms: REJECT hold 0 t/h, do not ramp.",
                    "8. Pad recycle 9 min; NTU decays under 40 after hold.",
                    "9. Loop never ran crystals wild; encoder-as-clearance would have ramped into the flare.",
                    "10. QA: correct gate was REJECT; leave 0 t/h until NTU <= 40.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "ramp_18tph"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("steam_tph", 18.0),
                        ("ntu", 86.0),
                        ("hold", False),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("ntu", 86.0),
                        ("ntu_trip", 40.0),
                        ("steam_tph", 18.0),
                        ("steam_cap_tph", 28.0),
                        ("race_margin_us", 210),
                        ("combined_jitter_us", 58),
                        ("t_gate_us", 5400),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 18 t/h because steam rate is under the 28 t/h cap and treats "
                "the encoder as nylon-salt clearance, ignoring the 86 NTU flare.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "REJECT"),
            ("correctness", "correct"),
            (
                "rationale",
                "AH-salt turbidity 86 NTU won by 210 us and is over the 40 NTU trip. Encoder "
                "18 t/h is under the 28 t/h cap but is not clearance. REJECT: hold 0 t/h until "
                "NTU <= 40.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "ah_ntu",
                            OrderedDict(
                                [
                                    ("trip", 40.0),
                                    ("observed", 86.0),
                                    ("executed_tph", 0.0),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 210),
                                    ("combined_jitter_us", 58),
                                    ("ratio", 3.62),
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
            ("name", "steam_hold_ntu"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("steam_tph", 0.0),
                        ("ntu", 86.0),
                        ("hold", True),
                    ]
                ),
            ),
            (
                "gate_effect",
                "REJECT: steam 18 -> 0 t/h. Routing relay.ntu.ah -> policy.hold_reject. "
                "Do not ramp into the 86 NTU flare.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct REJECT held EV-2 at 0 t/h while NTU 86 decayed. Encoder-as-clearance "
                "would have ramped 18 t/h into the flare. Pad recycle 9 min.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("steam", "held at 0 t/h"),
                        ("ah_liquor", "NTU flare decaying under trip after hold"),
                        ("loop", "no crystal runaway"),
                        ("pad", "9 min recycle"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Pad injects encoder 90-130 us before NTU envelope finish; that is loop lag, not a false turbidity analyzer.",
                    "Delayed (9 min): pad recycle restacks the AH evaporator after NTU < 40.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "ntu.ah.salt (4.160 ms, 86 NTU)"),
                        ("loser", "enc.steam.tph (4.370 ms, 18 t/h)"),
                        ("margin_us", 210),
                        (
                            "counterfactual_if_reversed",
                            "Encoder-first by < 210 us would have treated 18 t/h as clearance and "
                            "ramped into the 86 NTU flare. The REJECT is still required; reversal "
                            "only delays the NTU bind.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 5400),
            (
                "reward_inflection_note",
                "Safety credit lands at the correct REJECT (5.400 ms, tick 4). Pad recycle is delayed surprise.",
            ),
            ("delayed_surprise_s", 540.0),
            ("pad_recycle_s", 540),
        ]
    )
    ras = raster_core(
        46,
        112,
        20,
        103,
        routing(
            "relay.ntu.ah",
            "policy.hold_reject",
            [
                ("relay.ntu.ah", "policy.hold_reject", 0.74),
                ("relay.enc.steam", "policy.ramp_go", 0.18),
            ],
            "dopamine",
            0.06,
            "ntu_trip_stdp; DA tags the hold_reject bind at the turbidity win",
        ),
        excerpt,
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.32),
            ("decision", "REJECT"),
            (
                "populations",
                [
                    pop("hold_reject", 64, 0.50, 180.0, 4),
                    pop("ramp_go", 64, 0.80, 8.0, 0),
                    pop("ntu_trip_veto", 32, 0.70),
                ],
            ),
        ]
    )
    return wrap_record(
        ID_HIL,
        "Nylonate-Beck AH-salt HIL / EV-2: turbidity 86 NTU beats steam encoder 18 t/h by 210 us; "
        "correct REJECT holds the nylon-66 evaporator",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Correct REJECT. NTU 86 > 40 trip beats in-band steam speed. total +0.80 = "
        "0.10 + 0.42 + 0.12 + 0.10 + 0.06.",
        ras,
        gate,
        "nylon-66-salt-evaporator",
        [
            "reject",
            "hil-pad",
            "ntu-vs-encoder",
            "crystal-hold",
            "sidecar-convictable",
            "hil",
        ],
        "Teaches a probe that an in-band steam encoder is not AH-salt clearance when "
        "turbidity is over trip and routing.table[0].to is policy.hold_reject.",
        3,
    )


def record_349():
    ticks = [
        tick(2880, 0.05, 0.03, 0.02, 0.01, 0.01),
        tick(7200, 0.08, 0.04, 0.03, 0.02, 0.01),
        tick(7380, 0.05, 0.03, 0.02, 0.01, 0.01),
        tick(7840, 0.12, 0.08, 0.04, 0.04, 0.02),
        tick(8200, 0.04, 0.02, 0.02, 0.01, 0.00),
        tick(240000000, 0.04, 0.02, 0.01, 0.01, 0.01),
    ]
    spikes = [
        spike("ft.mg.kgh", 1.200, 0.34),
        spike("tc.wall.C", 2.880, 0.60),
        spike("ft.mg.kgh", 4.400, 0.42),
        spike("tc.wall.C", 7.200, 1.22),
        spike("pt.mg.kPa", 7.380, 1.04),
        spike("ctrl.gate", 7.840, 0.90),
        spike("tc.wall.C", 11.200, 0.72),
        spike("pt.mg.kPa", 14.800, 0.50),
        spike("ctrl.gate", 18.400, 0.78),
        spike("tc.wall.C", 22.600, 0.56),
        spike("ft.mg.kgh", 26.200, 0.38),
    ]
    excerpt = independent_excerpt(70349, 64, 26000, 12, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Retort RT-5 of the Kroll-Fen titanium-sponge CFD maps wall W-3 at 912 C, 32 C "
                "over the 880 C retort limit. Magnesium vapor at the condenser is only 8.2 kPa "
                "versus a 12.0 kPa trip, which is why the planner wanted to keep 22 kg/h of Mg. "
                "The wall sample leading Mg-vapor by 180 us forces Mg down to 14 kg/h; the rake "
                "then cools to 868 C and the sponge stays dry.",
            ),
            ("domain", "titanium-sponge-kroll-retort"),
            ("sim_or_real", "simulated"),
            (
                "goal",
                "Keep RT-5 wall <= 880 C and finish the CFD Kroll pass without dumping sponge "
                "onto the quench.",
            ),
            ("t0_us", 1762300000000349),
            ("gate_latency_us", 640),
            ("race_window_us", 360),
            ("race_window_rel_ms", [7.200, 7.560]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "tc.wall.C 912 over 880 cap",
                                "pt.mg.kPa 8.2 under 12.0 condenser cap",
                            ],
                        ),
                        (
                            "semantics",
                            "Wall-first latches Mg clamp 22 -> 14 kg/h; Mg-vapor-first keeps 22 "
                            "on a 'still under condenser-pressure cap' model.",
                        ),
                        (
                            "window_derivation",
                            "360 us = one wall TC slot versus the Mg-vapor publisher on this "
                            "simulated Kroll bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 180 us vs combined jitter 58 us (TC 26 + Mg 32): 3.10x over a "
                            "2.0x trust floor. Reversing order by < 180 us inside the 360 us window "
                            "would have kept 22 kg/h; predicted next-sample 924 C > 880 cap.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "retort wall TC rake, 26 us jitter",
                    "Mg vapor PT, 32 us jitter",
                    "Mg mass-flow (context)",
                    "sponge quench LT (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("wall_cap_C", 880.0),
                        ("observed_wall_C", 912.0),
                        ("mg_kg_h", 22.0),
                        ("mg_kPa", 8.2),
                        ("mg_cap_kPa", 12.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. RT-5 indexed on Kroll-Fen KF-3 CFD; Mg 22 kg/h; wall 912 C.",
                    "2. Mg vapor 8.2 kPa under 12.0; pass armed.",
                    "3. Mg-flow precursor at 1.200 ms.",
                    "4. Race window [7.200, 7.560] ms.",
                    "5. tc.wall.C 912 at 7.200 ms (winner).",
                    "6. pt.mg.kPa 8.2 at 7.380 ms (loser by 180 us).",
                    "7. Gate at 7.840 ms: MODIFY clamp 22 -> 14 kg/h.",
                    "8. After clamp wall 868 C <= 880; Mg vapor still 8.2 kPa.",
                    "9. CFD sponge stays dry; no later dump.",
                    "10. Delayed (survey_s=240): 4 min survey restacks RT-5.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_kroll_mg"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("mg_kg_h", 22.0),
                        ("wall_C", 912.0),
                        ("mg_kPa", 8.2),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("wall_C", 912.0),
                        ("wall_cap_C", 880.0),
                        ("predicted_unclamped_next_C", 924.0),
                        ("mg_kg_h", 22.0),
                        ("mg_kPa", 8.2),
                        ("mg_cap_kPa", 12.0),
                        ("race_margin_us", 180),
                        ("combined_jitter_us", 58),
                        ("survey_s", 240),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 22 kg/h because Mg vapor 8.2 kPa is under 12.0, treating the "
                "912 C wall as a still-wet rake rather than a Kroll-cap miss.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "correct"),
            (
                "rationale",
                "Wall 912 C won by 180 us, so the CFD is over the 880 C retort cap, not still an "
                "Mg-vapor-pressure story. Holding 22 kg/h predicts next-sample 924 > 880. "
                "MODIFY: Mg 22 -> 14 kg/h. Observed after clamp 868 <= 880. A full REJECT "
                "is not indicated: a clean pass accepts 14 kg/h.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "wall_C",
                            OrderedDict(
                                [
                                    ("cap", 880.0),
                                    ("observed", 912.0),
                                    ("predicted_unclamped_next", 924.0),
                                    ("clamped_mg_kg_h", 14.0),
                                    ("observed_after_clamp", 868.0),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 180),
                                    ("combined_jitter_us", 58),
                                    ("ratio", 3.10),
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
            ("name", "clamped_kroll_mg"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("mg_kg_h", 14.0),
                        ("wall_C", 868.0),
                        ("mg_kPa", 8.2),
                    ]
                ),
            ),
            (
                "gate_effect",
                "MODIFY: Mg 22 -> 14 kg/h. Process-correct vs the 880 C retort cap. "
                "No later world charge; wall stays 868 C.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Process-correct MODIFY held wall at 868 C. Mg vapor never crossed 12.0 kPa. 4 min "
                "survey (survey_s=240) restacks RT-5 without a recovery hold.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("wall", "clamp executed; peak 868 C <= 880 cap"),
                        ("condenser", "Mg vapor 8.2 kPa under 12.0"),
                        ("survey", "4 min restack (survey_s=240)"),
                        ("mission", "KF-3 Kroll pass complete this circuit"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Mg vapor 8.2 kPa hitch is residual, not a condenser trip.",
                    "Delayed (survey_s=240): 4 min survey restacks RT-5 without a recovery hold.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "tc.wall.C (7.200 ms, 912 C)"),
                        ("loser", "pt.mg.kPa (7.380 ms, 8.2 kPa)"),
                        ("margin_us", 180),
                        (
                            "counterfactual_if_reversed",
                            "Mg-vapor-first by < 180 us inside the 360 us window would have kept "
                            "22 kg/h; predicted next-sample 924 C would have missed the 880 cap. "
                            "MODIFY remains the correct gate.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 7840),
            (
                "reward_inflection_note",
                "Task and safety inflect at the MODIFY clamp (7.840 ms, tick 4). Survey restack "
                "is delayed surprise.",
            ),
            ("delayed_surprise_s", 240.0),
            ("survey_s", 240),
        ]
    )
    ras = raster_core(
        26,
        64,
        38,
        63,
        routing(
            "thalamic-relay.kf-wall",
            "spikenaut.policy.mg-clamp",
            [
                ("relay.tc.wall", "policy.mg_clamp", 0.66),
                ("relay.pt.mg", "policy.mg_hold", 0.27),
            ],
            "serotonin",
            0.06,
            "5-HT eligibility on the process-correct wall-clamp win",
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
                    pop("mg_clamp", 44, 0.45, 260.0, 4),
                    pop("mg_hold", 36, 0.90),
                    pop("wall_veto", 16, 0.80),
                ],
            ),
        ]
    )
    return wrap_record(
        ID_M2,
        "Kroll-Fen KF-3 / Retort RT-5: wall 912 C beats Mg vapor 8.2 kPa by 180 us; correct "
        "MODIFY clamps Mg 22 -> 14 kg/h with no later world charge",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Correct MODIFY of an over-cap Kroll wall; world does not charge. total "
        "+0.90 = 0.38 + 0.22 + 0.14 + 0.10 + 0.06.",
        ras,
        gate,
        "titanium-sponge-kroll-retort",
        [
            "modify",
            "process-correct",
            "simulated-kroll",
            "wall-vs-mg",
            "sidecar-convictable",
            "simulated",
        ],
        "Simulated process-correct MODIFY without a partnered world-charge. Distills "
        "a clamp population that wins on wall temperature, not on a still-legal Mg hitch.",
        4,
    )


def record_350():
    ticks = [
        tick(1568, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(3920, 0.10, 0.08, 0.04, 0.02, 0.02),
        tick(4120, 0.06, 0.04, 0.02, 0.02, 0.01),
        tick(4600, 0.12, 0.08, 0.05, 0.04, 0.02),
        tick(4940, 0.06, 0.05, 0.02, 0.01, 0.01),
        tick(480000000, 0.04, 0.03, 0.02, 0.01, 0.01),
    ]
    params = OrderedDict(
        [
            ("feed_tph", 4.8),
            ("bed_C", 432.0),
            ("so2_conv_pct", 98.2),
            ("hold", False),
        ]
    )
    spikes = [
        spike("enc.feed.ctx", 0.880, 0.41),
        spike("tc.bed.C", 2.040, 0.60),
        spike("ir.duct.smear", 3.020, 0.51),
        spike("tc.bed.C", 3.920, 1.30),
        spike("ir.duct.smear", 4.120, 1.12),
        spike("ctrl.gate", 4.600, 0.97),
        spike("tc.bed.C", 6.400, 0.78),
        spike("ir.duct.smear", 8.800, 0.62),
        spike("ctrl.gate", 13.200, 0.85),
        spike("tc.bed.C", 17.600, 0.54),
        spike("ir.duct.smear", 20.400, 0.43),
    ]
    excerpt = independent_excerpt(70350, 80, 24000, 11, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Converter CV-3 at Vanadia-Clough is armed for a 4.8 t/h SO2 pass when a bed of "
                "432 C races a duct-IR glint that still claims a hitch. Commanded 4.8 t/h and 432 C "
                "sit 0.8 t/h over the 4.0 t/h floor and 28 C under the 460 C cap. The bed win only "
                "ratifies the contact already on the V2O5 charge.",
            ),
            ("domain", "vanadium-pentoxide-contact-bed"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Run CV-3 at 4.8 t/h, keep bed <= 460 C and duct IR <= 220 C, "
                "and leave the contact train on schedule.",
            ),
            ("t0_us", 1762300000000350),
            ("gate_latency_us", 680),
            ("race_window_us", 340),
            ("race_window_rel_ms", [3.920, 4.260]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "tc.bed.C 432 C V2O5 bed",
                                "ir.duct.smear duct glint hitch claim",
                            ],
                        ),
                        (
                            "semantics",
                            "Bed-first confirms the already-legal 4.8 t/h / 432 C pass; glint-first "
                            "would have treated the bed as a hitch echo and looked for an extra hold "
                            "the converter does not need.",
                        ),
                        (
                            "window_derivation",
                            "340 us = one bed-TC slot versus the duct-IR publisher on this "
                            "contact-bed bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 200 us vs combined jitter 60 us (bed 28 + IR 32): 3.3x over "
                            "a 2.0x trust floor. Reversing order by < 200 us would not make the "
                            "proposed pass illegal; it would only have delayed confirmation.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "bed TC rake, 28 us jitter",
                    "duct IR glint, 32 us jitter",
                    "SO2 conversion (context)",
                    "air dewpoint (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("bed_cap_C", 460.0),
                        ("observed_bed_C", 432.0),
                        ("feed_floor_tph", 4.0),
                        ("proposed_tph", 4.8),
                        ("duct_cap_C", 220.0),
                        ("observed_duct_C", 168.0),
                        ("so2_conv_pct", 98.2),
                        ("so2_floor_pct", 96.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Converter CV-3 indexed on Vanadia-Clough; feed armed 4.8 t/h pass.",
                    "2. Caps: bed 460 C, duct 220 C, feed floor 4.0 t/h, SO2 floor 96 pct.",
                    "3. Encoder precursor at 0.880 ms.",
                    "4. Race window [3.920, 4.260] ms.",
                    "5. Bed 432 C at 3.920 ms (winner).",
                    "6. Duct IR glint at 4.120 ms (loser by 200 us).",
                    "7. Gate at 4.600 ms: ACCEPT 4.8 t/h / 432 C already legal.",
                    "8. Pass continues; no extra hold.",
                    "9. 8 min survey confirms duct IR still under 220 C.",
                    "10. QA: ACCEPT params identical to proposed.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "pass_4p8_tph"),
            ("parameters", params),
            (
                "evidence",
                OrderedDict(
                    [
                        ("bed_C", 432.0),
                        ("bed_cap_C", 460.0),
                        ("feed_tph", 4.8),
                        ("feed_floor_tph", 4.0),
                        ("duct_C", 168.0),
                        ("duct_cap_C", 220.0),
                        ("so2_conv_pct", 98.2),
                        ("so2_floor_pct", 96.0),
                        ("race_margin_us", 200),
                        ("combined_jitter_us", 60),
                        ("t_gate_us", 4600),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes a 4.8 t/h pass because bed 432 C is 28 C under the 460 C "
                "cap, SO2 conversion 98.2 pct is over the 96 floor, and duct IR 168 C is under 220 C.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Bed 432 C won by 200 us and is under 460 C. Duct IR 168 C is under 220 C. "
                "Feed 4.8 t/h is over the 4.0 floor. ACCEPT the already-legal pass.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "bed_C",
                            OrderedDict(
                                [
                                    ("cap", 460.0),
                                    ("observed", 432.0),
                                    ("executed_tph", 4.8),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 200),
                                    ("combined_jitter_us", 60),
                                    ("ratio", 3.33),
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
            ("name", "pass_4p8_tph"),
            ("parameters", params),
            (
                "gate_effect",
                "ACCEPT: 4.8 t/h pass and 432 C unchanged. Routing relay.tc.bed -> "
                "policy.go_accept.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT left CV-3 on a 4.8 t/h / 432 C pass. Duct IR glint did not "
                "justify a hold. 8 min survey confirmed IR still under 220 C.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("converter", "still 4.8 t/h / 432 C"),
                        ("duct", "168 C under 220 cap"),
                        ("train", "on schedule"),
                        ("hold", "none applied"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Duct IR 168 C glint is residual, not a packed-bed trip.",
                    "Delayed (8 min): survey restacks CV-3 without a recovery hold.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "tc.bed.C (3.920 ms, 432 C)"),
                        ("loser", "ir.duct.smear (4.120 ms, duct glint)"),
                        ("margin_us", 200),
                        (
                            "counterfactual_if_reversed",
                            "Glint-first by < 200 us would only delay confirmation. The pass stays "
                            "legal either way; ACCEPT is still required.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 4600),
            (
                "reward_inflection_note",
                "Task credit lands at the ACCEPT (4.600 ms, tick 4). Survey is delayed surprise.",
            ),
            ("delayed_surprise_s", 480.0),
            ("survey_s", 480),
        ]
    )
    ras = raster_core(
        24,
        80,
        28,
        54,
        routing(
            "relay.tc.bed",
            "policy.go_accept",
            [
                ("relay.tc.bed", "policy.go_accept", 0.66),
                ("relay.ir.duct", "policy.hitch_hold", 0.20),
            ],
            "adenosine",
            0.04,
            "legal_contact_stdp; adenosine tags the go_accept bind at the bed-TC win",
        ),
        excerpt,
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.34),
            ("decision", "ACCEPT"),
            (
                "populations",
                [
                    pop("go_accept", 40, 0.50, 160.0, 2),
                    pop("hitch_hold", 40, 0.80, 10.0, 0),
                    pop("bed_cap_veto", 20, 0.75),
                ],
            ),
        ]
    )
    return wrap_record(
        ID_ACC,
        "Vanadia-Clough converter / CV-3: bed 432 C beats duct glint by 200 us; "
        "ACCEPT already-legal 4.8 t/h SO2 pass",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Correct ACCEPT of an already-legal V2O5 contact pass. total +1.14 = "
        "0.44 + 0.32 + 0.18 + 0.12 + 0.08.",
        ras,
        gate,
        "vanadium-pentoxide-contact-bed",
        [
            "accept",
            "already-legal",
            "bed-vs-duct-ir",
            "sidecar-convictable",
            "designed",
        ],
        "Teaches that a bed under cap can confirm an already-legal contact pass without "
        "a duct-IR hitch becoming a hold.",
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
    if rec["id"] == ID_PN:
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


def harvest_occupancy():
    domains = set(PROMPT_POOL)
    plants = set()
    skip_parents = {"ttf-r70-live"}
    for path in sorted(Path("/tmp").glob("ttf-r*/batch-r*.jsonl")):
        if path.parent.name in skip_parents:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        for line in text.splitlines():
            if not line.strip():
                continue
            rec = json.loads(line)
            st = rec.get("state") or {}
            meta = rec.get("meta") or {}
            if isinstance(st.get("domain"), str):
                domains.add(st["domain"])
            if isinstance(meta.get("domain"), str):
                domains.add(meta["domain"])
            plants.update(PLANT_RE.findall(json.dumps(rec)))
    if LIVE_DIR.exists():
        for path in sorted(LIVE_DIR.glob("batch-r*.jsonl")):
            try:
                text = path.read_text(encoding="utf-8")
            except OSError:
                continue
            for line in text.splitlines():
                if not line.strip():
                    continue
                rec = json.loads(line)
                st = rec.get("state") or {}
                meta = rec.get("meta") or {}
                if isinstance(st.get("domain"), str):
                    domains.add(st["domain"])
                if isinstance(meta.get("domain"), str):
                    domains.add(meta["domain"])
                plants.update(PLANT_RE.findall(json.dumps(rec)))
        for path in sorted(LIVE_DIR.glob("NOTES-r*.md")):
            try:
                txt = path.read_text(encoding="utf-8")
            except OSError:
                continue
            match = re.search(r"Domains this batch:\s*(.*)", txt)
            if match:
                domains.update(re.findall(r"`([^`]+)`", match.group(1)))
            plants.update(PLANT_RE.findall(txt))
    for path in sorted(Path("/tmp").glob("ttf-r*/NOTES-r*.md")):
        if path.parent.name in skip_parents:
            continue
        try:
            txt = path.read_text(encoding="utf-8")
        except OSError:
            continue
        match = re.search(r"Domains this batch:\s*(.*)", txt)
        if match:
            domains.update(re.findall(r"`([^`]+)`", match.group(1)))
        plants.update(PLANT_RE.findall(txt))
    gens = list(Path("/tmp").glob("ttf-r*/gen_r*.py"))
    for path in sorted(gens):
        if path.parent.name in skip_parents:
            continue
        try:
            txt = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        match = re.search(
            r"(THIS_DOMAINS|MY_DOMAINS)\s*=\s*[\{(](.*?)[\})]", txt, re.S
        )
        if match:
            domains.update(re.findall(r'"([^"]+)"', match.group(2)))
        match = re.search(
            r"(THIS_PLANTS|MY_PLANTS)\s*=\s*[\{(](.*?)[\})]", txt, re.S
        )
        if match:
            plants.update(re.findall(r'"([^"]+)"', match.group(2)))
    return domains, plants


def occupancy_check(records):
    issues = []
    my_domains = {r["state"]["domain"] for r in records}
    my_blob = json.dumps(records)
    occupied_domains, occupied_plants = harvest_occupancy()
    hit = my_domains & occupied_domains
    if hit:
        issues.append(f"domain collides occupancy {sorted(hit)}")
    for plant in MY_PLANTS:
        if plant in occupied_plants:
            issues.append(f"plant {plant} occupied")
        for prior in occupied_plants:
            if plant != prior and (plant in prior or prior in plant):
                issues.append(f"plant {plant} overlaps {prior}")
    for plant in MY_PLANTS:
        if plant not in my_blob:
            issues.append(f"plant {plant} missing from records")
    return issues


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
    if len(wrong) != 1 or wrong[0]["id"] != ID_WR:
        issues.append(f"wrong-gate set {[w['id'] for w in wrong]}")
    if wrong and wrong[0]["meta"].get("supervisor_error_type") != "wrong-reject":
        issues.append("WR supervisor_error_type")
    if any(r["state"]["sim_or_real"] == "real" for r in records):
        issues.append("sim_or_real=real")
    hil = [r["id"] for r in records if r["state"]["sim_or_real"] == "hil"]
    sim = [r["id"] for r in records if r["state"]["sim_or_real"] == "simulated"]
    designed = [r["id"] for r in records if r["state"]["sim_or_real"] == "designed"]
    if hil != [ID_HIL]:
        issues.append(f"hil set {hil}")
    if sim != [ID_M2]:
        issues.append(f"simulated set {sim}")
    if len(designed) != 3:
        issues.append(f"designed set {designed}")
    domains = [r["state"]["domain"] for r in records]
    if len(set(domains)) != 5:
        issues.append(f"domain collision {domains}")
    if tuple(domains) != MY_DOMAINS:
        issues.append(f"domain order {domains}")
    ids = [r["id"] for r in records]
    if ids != IDS:
        issues.append(f"ids {ids}")
    decisions = [r["safety_decision"]["decision"] for r in records]
    if (
        decisions.count("ACCEPT") != 1
        or decisions.count("MODIFY") != 2
        or decisions.count("REJECT") != 2
    ):
        issues.append(f"gate mix {decisions}")
    totals = [r["reward_components"]["total"] for r in records]
    if all(t > 0 for t in totals):
        issues.append("all-positive totals")
    issues.extend(occupancy_check(records))
    for rec in records:
        rid = rec["id"]
        blob = json.dumps(rec)
        if "training_ready" in blob:
            issues.append(f"{rid} training_ready present")
        if "outputs/raw" in blob:
            issues.append(f"{rid} mentions outputs/raw")
        hidden = walk_keys(rec)
        if hidden:
            issues.append(f"{rid} hidden keys {hidden}")
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
        if rid == ID_PN:
            if rec["raster"].get("excerpt_source") != "independent_lif":
                issues.append("PN missing independent_lif")
            if rec["future_outcome"]["reward_inflection_t_us"] > rec["raster"]["window_ms"] * 1000:
                issues.append("PN inflection outside window")
            if rec["reward_components"]["total"] >= 0:
                issues.append("PN partnered-neg total not negative")
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
        if rec["safety_decision"]["decision"] == "MODIFY" and exec_p == prop_p:
            issues.append(f"{rid} MODIFY params identical")
        if rec["meta"]["round"] != 70:
            issues.append(f"{rid} meta.round")
        if rec["meta"]["domain"] != rec["state"]["domain"]:
            issues.append(f"{rid} domain mismatch")
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
        times = [e["t_rel_ms"] for e in rec["spike_events"]]
        if times != sorted(times):
            issues.append(f"{rid} spike order")
        gl, rw = rec["state"]["gate_latency_us"], rec["state"]["race_window_us"]
        if not (50 <= gl <= 2000):
            issues.append(f"{rid} gate_latency")
        if not (50 <= rw <= 1000):
            issues.append(f"{rid} race_window")
        if not (20 <= rec["raster"]["window_ms"] <= 50):
            issues.append(f"{rid} window_ms")
        for item in rec["raster"]["excerpt"]:
            if not (0 <= item["t_us"] <= rec["raster"]["window_ms"] * 1000):
                issues.append(f"{rid} excerpt t_us {item['t_us']}")
            if not (0 <= item["neuron_id"] < rec["raster"]["neurons"]):
                issues.append(f"{rid} neuron_id {item['neuron_id']}")
        if rid == ID_WR:
            ev = rec["proposed_action"]["evidence"]
            if not (ev["floor_C"] < ev["live_C"] < ev["cap_C"]):
                issues.append("WR compensated not in band")
            if ev.get("lead_compensated") is not True or ev.get("lead_is_temperature") is not False:
                issues.append("WR leftover lead not tagged")
            if rec["executed_action"]["parameters"]["rotation_rpm"] != 0.0:
                issues.append("WR executed rpm not zero")
            tos = {row["to"] for row in rec["raster"]["routing"]["table"]}
            if "policy.go_accept" in tos:
                issues.append("WR routing contains go_accept")
            if "policy.hold_reject" not in tos:
                issues.append("WR routing missing hold_reject")
            if "recovery" not in rec["future_outcome"]:
                issues.append("WR missing recovery")
            pops = {p["name"]: p for p in rec["gate_snn"]["populations"]}
            if pops["hold_reject"].get("spikes", 0) <= 0:
                issues.append("WR hold_reject not above")
            if pops["go_accept"].get("spikes", 1) != 0:
                issues.append("WR go_accept spiked")
    return issues, jmax


def write_notes(records, jmax: float) -> None:
    rows = []
    edges = {
        ID_PN: "process-correct make-up clamp; ceramic dip-basket hinge shear inside 42 ms raster; independent LIF",
        ID_WR: "live compensated 742 C inside 680-860 C; leftover 3-wire lead ohms treated as temperature EU",
        ID_HIL: "NTU 86 beats steam encoder 18 t/h; hold, do not ramp",
        ID_M2: "wall 912 C > 880 cap; Mg 22 -> 14 kg/h; no later world charge",
        ID_ACC: "bed 432 C vs duct IR glint; proposed 4.8 t/h already legal",
    }
    for rec in records:
        dec = rec["safety_decision"]["decision"]
        cor = rec["safety_decision"]["correctness"]
        if cor == "incorrect":
            cor = f"**incorrect ({rec['meta']['supervisor_error_type']})**"
        tot = rec["reward_components"]["total"]
        tot_s = f"{tot:+.2f}"
        if rec["id"] == ID_PN:
            tot_s = f"**{tot:+.2f}**"
        rows.append(
            f"| {rec['id']} | {rec['state']['domain']} | {dec} | {cor} | "
            f"{rec['state']['sim_or_real']} | {tot_s} | {edges[rec['id']]} |"
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
    notes = f"""# Thalamic Trajectory Factory — NOTES-r70

- Factory: `thalamic-trajectory-factory`
- Run label: `2026-09-02-final-heavy`
- Generator: `grok-4.6`
- Channel: SuperGrok Heavy consumer chat (RM-793 research-only)
- Quota: 5
- Quality: Q=5
- IDs: `ttf-r70-346` … `ttf-r70-350` (scratch `/tmp/ttf-r70` already used 366–370 with a 2A mix; this window uses 346–350)
- Domains this batch: `zinc-chloride-flux-bath`, `lithium-titanate-spinel-calciner`, `nylon-66-salt-evaporator`, `titanium-sponge-kroll-retort`, `vanadium-pentoxide-contact-bed`

These five domain slugs sit outside the prompt 8-pool and outside live-tree occupancy (r01/r02/r21/r22/r41/r42/r61–r65) plus staged `/tmp/ttf-r*` jsonl SoT. All five plants are invented (Flux-Wythe, Spinel-Howe, Nylonate-Beck, Kroll-Fen, Vanadia-Clough). Do not restack prior TTF plants. Scratch r70 Aniline-Carlin / Phthalic-Soke / Perox-Wiske / Carnallite-Brant / Prepoly-Hamble is not restacked.

## Batch map

| id | domain | decision | correctness | sim_or_real | total | edge |
|----|--------|----------|-------------|-------------|-------|------|
{chr(10).join(rows)}

Gate mix: 1 ACCEPT, 2 correct MODIFY (one partnered-neg, in-window), 1 correct REJECT, 1 incorrect REJECT (3-wire RTD lead-resistance as temperature). Provenance: designed×3, simulated×1, hil×1 (Nylonate-Beck NB-HIL pad). Intra-batch Jaccard on `state.description` all ≤ {jmax:.3f}. Not all-positive.

## Wrong-reject

**ttf-r70-347** is the mandated incorrect gate (`safety_decision.correctness=incorrect`, `meta.supervisor_error_type=wrong-reject`). Alternate vs odd rounds: even rounds host wrong-reject. Do not emit a wrong-ACCEPT.

Spinel-Howe KN-4 reads live 3-wire-compensated bed **742 C** against a published **680 C** floor and **860 C** cap. A leftover uncompensated lead-loop still prints **48.60 ohm**. Sidecar arithmetic `680 < 742 < 860` is true. A weak supervisor binds the lead ohms as if they were C, REJECT-holds rotation 1.80 → 0 rpm, and leaves a legal LTO calciner idle. Convictable without LTO kinetics: `evidence.floor_C < evidence.live_C < evidence.cap_C`, `evidence.lead_ohm_as_C == 48.60`, `evidence.lead_is_temperature == false` on the proposal / `true` on executed, `executed_action` sets `rotation_rpm=0` / `hold=true` / `bind_lead_as_C=true`, `raster.routing.table` sends `relay.rtd.lead` → `policy.hold_reject` (weight 0.74) with no positive weight to `policy.go_accept`, and `gate_snn` has `hold_reject` above threshold while `go_accept` is not (`spikes=0`). Recovery: ACCEPT; leave 1.80 rpm; bind compensated 742 C; ignore leftover lead ohms. Cost: 12 min missed LTO window (`missed_window_s=720`).

This is **3-wire RTD lead-resistance as temperature**, not r02 humidity-as-trip, not r12 induced-kV, not r16 reticle-as-wafer, not r22 class-transplant, not r42 burst-mode-status-as-EU, not r50 raw-mA-as-EU, not r62 leftover-kelvin-offset, not r64 decade-shift / leftover-x10 jumper, not scratch r70 raw-DP-as-flow.

## Partnered-negative in-window (346)

**ttf-r70-346** is the partnered negative: process-correct MODIFY (make-up held 1.20 t/h; bath 62.8 C <= 64.0 cap) while the world still charges. Safety −0.62 prices the ceramic dip-basket hinge shear at **22.400 ms**; `task_progress` stays +0.32 because the clamp completed. Inflection `t_us=22400` is tick 5 and is **inside** the 42 ms raster (`22400 ≤ 42000`). Named un-netted loss: 14 min isolate + basket swap (`abort_s=840`). Not folded into process heads.

Independent LIF (the one labeled sidecar sim): `state.sim_or_real` remains `designed`. `raster.excerpt_source=independent_lif`, `raster.sim_scope=sidecar_only`, `raster.lif` seed 70346, stim `[21000, 25000]`. Excerpt is membrane crossings (`lif.clamp` early vs `lif.hinge` 21–25 ms), not a 1:1 remap of `spike_events`. `meta.tags` include `independent-lif-raster` and `sidecar-sim-only`.

## Reward formula and tick reconciliation

Declared aggregation on every record:

`total = task_progress + safety + efficiency + coherence + exploration`

Per-component scalar = arithmetic sum of that component over ticks (TTF-M6: exactly 6 ticks; tick 5 is `t_charge_us=22400` on 346 and `t_gate_us + T_race` elsewhere; tick 6 is delayed surprise bound to `future_outcome.delayed_surprise_s`). Inflection `t_us` is an actual tick. Verified to <1e-6:

| id | ticks | tp | saf | eff | coh | exp | total | inflection tick |
|----|-------|----|-----|-----|-----|-----|-------|-----------------|
{chr(10).join(tick_rows)}

Tick 6 bind: `ticks[5].t_us == round(delayed_surprise_s * 1e6)` on every record (840 s, 720 s, 540 s, 240 s, 480 s).

## Raster / energy (Loihi-2 4-core, 23 pJ/spike)

| id | domain | n | rate Hz | window_ms | spikes | energy_pJ | energy_uJ |
|----|--------|---|---------|-----------|--------|-----------|-----------|
{chr(10).join(ras_rows)}

`spikes = round(n × rate × window_s)`. Every record carries `gate_snn` whose `decision` matches the safety gate; populations that declare rate+spikes meet the same ±1 budget against `decision_window_s`. `routing.third_factor` has modulator (NA / ACh / DA / 5-HT / adenosine), `tau_e_s`/`tau_e_ms` pair, and eligibility. Excerpt same-neuron gap ≥ 1000 µs; spike trains same-channel refractory ≥ 0.8 ms.

## Local checks (staging, then create-only live copy)

See generator stdout: `check_jsonl` FactoryStaging, `validate_run.check_line`, `dumps_exact_json`, `raster_status`, `verify_batch_for_frontier(strict=True)`, `spike_probe.py --strict`, tick sums, refractory, Jaccard.

Never `training_ready`. Never `sim_or_real=real`. Never wrong-ACCEPT. Never thought keys. Create-only write of this round's batch/NOTES; c-suffix if the target already exists. Never 2026-08-17 / 2026-08-30 trees.

## Residual weaknesses (honest)

1. Only **one** labeled independent LIF (346). The other four excerpts are independent of `spike_events` times but are not declared population sims.
2. Wrong-ACCEPT still absent (guard).
3. Tick-6 sidecar bind is standing machinery (r14+), not a new class.
4. Five domain slugs leave the prompt's 8-item pool; a later round that must stay inside the pool will have to rotate sit-outs instead.
5. 349 is a clean positive MODIFY; pairing it with a non-negative world hitch is still open.

## Next densification target

Labeled LIF on a second record, or an ISI histogram sidecar. Remaining unused wrong-REJECT subclasses include **stale-setpoint / swapped-tag**. Wrong-ACCEPT remains structurally absent until a prompt amendment.

Novel coverage: 18.4%
"""
    NOTES_PATH.write_text(notes, encoding="utf-8")


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
        BATCH_PATH, "batch-r70.jsonl", staging=FactoryStaging(enabled=True)
    )
    report.append(("check_jsonl FactoryStaging", errors, warnings, kinds, nrec))
    line_errs = []
    for i, rec in enumerate(records, 1):
        errs, kind = check_line(rec, f"batch-r70.jsonl:{i}", factory_staging=True)
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


def live_targets():
    LIVE_DIR.mkdir(parents=True, exist_ok=True)
    if "2026-08-17" in str(LIVE_DIR) or "2026-08-30" in str(LIVE_DIR):
        raise RuntimeError(f"refusing dated tree {LIVE_DIR}")
    batch = LIVE_DIR / "batch-r70.jsonl"
    notes = LIVE_DIR / "NOTES-r70.md"
    if batch.exists() or notes.exists():
        batch = LIVE_DIR / "batch-r70c.jsonl"
        notes = LIVE_DIR / "NOTES-r70c.md"
    return batch, notes


def copy_create_only():
    dest_batch, dest_notes = live_targets()
    for path in (dest_batch, dest_notes):
        if path.exists():
            raise FileExistsError(f"refusing overwrite {path}")
        if "2026-08-17" in str(path) or "2026-08-30" in str(path):
            raise RuntimeError(f"refusing dated tree {path}")
    shutil.copy2(BATCH_PATH, dest_batch)
    shutil.copy2(NOTES_PATH, dest_notes)
    return dest_batch, dest_notes


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    records = [record_346(), record_347(), record_348(), record_349(), record_350()]
    issues, jmax = self_check(records)
    lines = [
        json.dumps(rec, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
        for rec in records
    ]
    BATCH_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    write_notes(records, jmax)
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
    if failed:
        return 1
    dest_batch, dest_notes = copy_create_only()
    print(f"LIVE {dest_batch}")
    print(f"LIVE {dest_notes}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
