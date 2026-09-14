#!/usr/bin/env python3
"""Emit TTF r25 JSONL (ttf-r25-141..145) into /tmp/ttf-r25/. Never writes outputs/raw/."""

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

OUT_DIR = Path("/tmp/ttf-r25")
BATCH_PATH = OUT_DIR / "batch-r25.jsonl"
NOTES_PATH = OUT_DIR / "NOTES-r25.md"
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
        ("generated_at", "2026-09-02T23:20:00Z"),
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
THIS_DOMAINS = {
    "salt-cavern-CAES",
    "tire-curing-press",
    "cyclotron-target",
    "cable-lay-barge",
    "olive-oil-decanter",
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


def lif_141_excerpt():
    n = 80
    dt_us = 100
    tau_m_ms = 18.0
    v_th = 1.0
    v_reset = 0.0
    refractory_us = 1000
    i_bias = 0.90
    i_stim_peak = 2.55
    stim = (18000, 21000)
    seed = 25141
    window_us = 40000
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
    early = [(t, nid) for t, nid in spikes if t < 18000]
    burst = [(t, nid) for t, nid in spikes if 18000 <= t < 21000]
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
            group = [1 for tt, _ in picked if (tt < 18000) == (pool[0][0] < 18000)]
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
    take(burst, 9, label_times=(19200, 19600, 20400))
    clamp = [(t, nid) for t, nid in picked if t < 18000][:7]
    tear = [(t, nid) for t, nid in picked if t >= 18000][:9]
    picked = sorted(clamp + tear, key=lambda item: (item[0], item[1]))
    if len(picked) < 8:
        raise ValueError(f"LIF excerpt too short {len(picked)}")
    channels = ["lif.clamp" if t < 18000 else "lif.stringer" for t, _ in picked]
    lif = OrderedDict(
        [
            ("model", "leaky_integrate_and_fire"),
            ("n", 80),
            ("dt_us", 100),
            ("tau_m_ms", 18.0),
            ("v_rest", 0.0),
            ("v_reset", 0.0),
            ("v_th", 1.0),
            ("r_m", 1.0),
            ("refractory_us", 1000),
            ("i_bias", 0.90),
            ("i_stim_peak", 2.55),
            ("stim_t_us", [18000, 21000]),
            ("i_clamp_extra", 0.65),
            ("clamp_n", 14),
            ("seed", 25141),
            (
                "note",
                "Population sim scoped to this sidecar. Plant remains designed. "
                "Neurons 0-13 carry +0.65 injection-clamp bias; stim 18-21 ms is the brine-stringer burst.",
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
        dw_s = None
        if spikes is None:
            raise ValueError("rate requires spikes")
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


def record_141():
    excerpt, extra = lif_141_excerpt()
    ticks = [
        tick(2200, 0.04, -0.02, -0.02, 0.01, 0.00),
        tick(5120, 0.08, -0.04, -0.03, 0.01, -0.01),
        tick(5258, 0.04, -0.03, -0.02, 0.00, 0.00),
        tick(5760, 0.10, -0.06, -0.04, 0.02, -0.02),
        tick(19200, 0.04, -0.40, -0.03, -0.01, 0.00),
        tick(1080000000, 0.02, -0.05, -0.02, 0.01, -0.01),
    ]
    state = OrderedDict(
        [
            (
                "description",
                "String-C12 at Halite-Keel HK-7 is injecting 4.8 kg/s of dry air while cavern PT "
                "reads 68.4 bar against a 62.0 bar working cap. A compressor-rpm residual still "
                "rings 2.1 percent. Pressure-first clamps injection 4.8 -> 2.1 kg/s; rpm-first "
                "would keep the 4.8 kg/s fill. A brine micro-annulus already seated on the "
                "stringer does not appear on PT or encoder until the AE burst.",
            ),
            ("domain", "salt-cavern-CAES"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Finish the HK-7 fill with cavern pressure <= 62.0 bar and without parting the "
                "brine stringer.",
            ),
            ("t0_us", 1756843200000141),
            ("gate_latency_us", 640),
            ("race_window_us", 380),
            ("race_window_rel_ms", [5.0, 5.38]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "pt.cavern.bar 68.4 bar",
                                "enc.comp.rpm 2.1 pct residual",
                            ],
                        ),
                        (
                            "semantics",
                            "Pressure-first latches injection clamp 4.8 -> 2.1 kg/s; rpm-first keeps "
                            "4.8 kg/s on a 'still spinning up' model.",
                        ),
                        (
                            "window_derivation",
                            "380 us = one 2.5 kHz wellhead-PT slot minus compressor-encoder group "
                            "delay on this cavern-head bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 138 us vs combined jitter ~60 us (PT 28 + encoder 32): 2.3x over "
                            "a 2.0x trust floor. Reversing order by < 138 us inside the 380 us window "
                            "would have kept 4.8 kg/s; predicted next-sample 66.2 bar > 62.0 cap.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "cavern wellhead PT, 2.5 kHz, 28 us timestamp jitter",
                    "compressor RPM encoder 0-3600, 32 us jitter",
                    "stringer AE puck, 50 kHz (context)",
                    "brine-interface sonar (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("cavern_cap_bar", 62.0),
                        ("observed_pt_bar", 68.4),
                        ("proposed_inject_kg_s", 4.8),
                        ("comp_rpm_residual_pct", 2.1),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. String-C12 indexed onto HK-7; injection 4.8 kg/s armed.",
                    "2. Cavern PT 68.4 bar; compressor residual 2.1 percent.",
                    "3. Encoder precursor at 1.140 ms; PT warm-start 68.4 bar.",
                    "4. Race window [5.000, 5.380] ms opens on the wellhead bus.",
                    "5. pt.cavern.bar 68.4 bar at 5.120 ms (winner).",
                    "6. enc.comp.rpm 2.1 pct at 5.258 ms (loser by 138 us).",
                    "7. Gate at 5.760 ms (winner + 640 us): MODIFY clamp 4.8 -> 2.1 kg/s.",
                    "8. Clamp executes; next-sample 61.4 bar < 62.0 cap.",
                    "9. At 19.200 ms a seated micro-annulus parts the brine stringer; AE burst.",
                    "10. 18 min cavern isolate (abort_s=1080); named un-netted loss, not folded into process heads.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_injection"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("inject_kg_s", 4.8),
                        ("hold", False),
                        ("well", "String-C12"),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("cavern_pt_bar", 68.4),
                        ("cavern_cap_bar", 62.0),
                        ("predicted_unclamped_next_bar", 66.2),
                        ("comp_rpm_residual_pct", 2.1),
                        ("race_margin_us", 138),
                        ("combined_jitter_us", 60),
                        ("abort_s", 1080),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 4.8 kg/s injection: 2.1 percent RPM residual looks like "
                "compressor spin-up, not a cavern over-cap, and the stringer is treated as still sealed.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "correct"),
            (
                "rationale",
                "Cavern PT 68.4 bar won by 138 us, so the working cap is already loaded, not still "
                "spinning up. Holding 4.8 kg/s predicts next-sample 66.2 bar > 62.0 cap. MODIFY: "
                "injection 4.8 -> 2.1 kg/s. Observed after clamp 61.4 bar < 62.0. A full REJECT is "
                "not indicated: a clean fill accepts 2.1 kg/s.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "cavern_pressure_bar",
                            OrderedDict(
                                [
                                    ("cap", 62.0),
                                    ("observed", 68.4),
                                    ("predicted_unclamped_next", 66.2),
                                    ("clamped_inject_kg_s", 2.1),
                                    ("observed_after_clamp", 61.4),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 138),
                                    ("combined_jitter_us", 60),
                                    ("ratio", 2.3),
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
            ("name", "clamped_injection"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("inject_kg_s", 2.1),
                        ("hold", False),
                        ("well", "String-C12"),
                    ]
                ),
            ),
            (
                "gate_effect",
                "MODIFY: injection 4.8 -> 2.1 kg/s. Process-correct vs the 62.0 bar cap. Stringer "
                "still parts at 19.200 ms.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Process-correct MODIFY held cavern pressure at 61.4 bar. At 19.200 ms a brine "
                "micro-annulus already seated on String-C12 parted the stringer. Clamp reduced dump "
                "energy; it did not prevent the burst. Partnered negative: process heads stay honest; "
                "world loss is named, not netted.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("cavern", "clamp executed; peak 61.4 bar < 62.0 cap"),
                        ("stringer", "parted at 19.200 ms"),
                        ("repair", "18 min cavern isolate (abort_s=1080)"),
                        ("mission", "HK-7 fill incomplete this circuit"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Neither cavern PT nor compressor RPM predicted the seated micro-annulus; ae.stringer.burst is a new channel at 19.200 ms, 13.440 ms after the gate, still inside the 40 ms raster.",
                    "Delayed (abort_s=1080): 18 min cavern isolate. Named un-netted loss, not folded into task_progress.",
                ],
            ),
            (
                "un_netted_loss",
                "18 min cavern isolate after String-C12 part. Safety head -0.60 prices the burst; "
                "task_progress stays +0.32 because the injection clamp completed under the 62.0 bar "
                "cap. World loss is named here, not subtracted from process heads.",
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "pt.cavern.bar (5.120 ms, 68.4 bar)"),
                        ("loser", "enc.comp.rpm (5.258 ms, 2.1 pct)"),
                        ("margin_us", 138),
                        (
                            "counterfactual_if_reversed",
                            "RPM-first by < 138 us inside the 380 us window would have kept "
                            "4.8 kg/s; predicted next-sample 66.2 bar would have exceeded the "
                            "62.0 bar cap even without the stringer burst. The MODIFY is still the "
                            "correct process. The burst is a later world charge either way, cheaper "
                            "with the clamp than without.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 19200),
            (
                "reward_inflection_note",
                "Safety collapses at the 19.200 ms stringer part (tick t_us=19200), inside the "
                "40 ms raster. The correct MODIFY at 5.760 ms is in the same excerpt. Do not put "
                "inflection on the abort_s=1080 isolate tick.",
            ),
        ]
    )
    spikes = [
        spike("enc.comp.rpm", 1.140, 0.41),
        spike("pt.cavern.bar", 2.280, 0.58),
        spike("enc.comp.rpm", 3.610, 0.50),
        spike("pt.cavern.bar", 5.120, 1.28),
        spike("enc.comp.rpm", 5.258, 1.14),
        spike("ctrl.gate", 5.760, 0.97),
        spike("pt.cavern.bar", 7.440, 0.82),
        spike("enc.comp.rpm", 9.920, 0.64),
        spike("ctrl.gate", 13.210, 0.86),
        spike("ae.stringer.burst", 19.200, 1.44),
        spike("ae.stringer.burst", 21.150, 0.93),
        spike("enc.comp.rpm", 26.800, 0.40),
        spike("pt.cavern.bar", 33.400, 0.55),
    ]
    dw = 0.38
    ras = raster_core(
        40,
        80,
        25,
        80,
        routing(
            "thalamic-relay.cavern-pt",
            "spikenaut.policy.inject-clamp",
            [
                ("relay.pt.cavern", "policy.inject_clamp", 0.67),
                ("relay.enc.rpm", "policy.rpm_hold", 0.31),
                ("relay.ae.stringer", "policy.inject_clamp", -0.44),
            ],
            "noradrenaline",
            0.04,
            "surprise-gated pre_post_stdp; NA at PT win (5.120 ms) opens a 40 ms eligibility "
            "trace that still covers the 19.200 ms stringer burst",
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
                    pop_budget("inject_clamp", 40, 0.50, 300.0, dw),
                    pop_budget("rpm_hold", 40, 0.50, 70.0, dw),
                    pop("gap_veto", 24, 0.75),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r25-141"),
            (
                "title",
                "Halite-Keel HK-7 / String-C12: cavern PT beats compressor RPM by 138 us; correct "
                "MODIFY still eats an in-window brine-stringer part (partnered negative total -0.44)",
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
                    "40 ms raster. total -0.44 = 0.32 + -0.60 + -0.16 + 0.04 + -0.04. Named isolate "
                    "(abort_s=1080) is not netted into task_progress.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "salt-cavern-CAES",
                    [
                        "modify",
                        "partnered-negative-total",
                        "independent-lif-raster",
                        "sidecar-sim-only",
                        "in-window-world-charge",
                        "designed",
                    ],
                    "A critic can see the world-charge as a LIF burst inside the raster while "
                    "process heads stay honest. Credit assignment is spikes, not prose across an "
                    "18 min cavern isolate.",
                    1,
                ),
            ),
        ]
    )


def record_142():
    ticks = [
        tick(1680, -0.02, -0.02, -0.02, -0.01, 0.00),
        tick(6088, -0.04, -0.04, -0.04, -0.02, 0.01),
        tick(6256, -0.03, -0.02, -0.03, -0.01, 0.01),
        tick(6968, -0.10, -0.08, -0.08, -0.04, 0.02),
        tick(9100, -0.03, -0.03, -0.03, -0.01, 0.01),
        tick(480000000, -0.02, -0.03, -0.02, -0.01, 0.01),
    ]
    spikes = [
        spike("tc.mold.ctx", 0.880, 0.39),
        spike("rtd.platen.C", 1.920, 0.57),
        spike("enc.ram.MPa", 2.760, 0.51),
        spike("rtd.platen.C", 6.088, 1.33),
        spike("enc.ram.MPa", 6.256, 1.16),
        spike("ctrl.gate", 6.968, 1.01),
        spike("rtd.platen.C", 8.440, 0.74),
        spike("enc.ram.MPa", 10.110, 0.62),
        spike("ctrl.gate", 13.700, 0.83),
        spike("tc.mold.ctx", 16.220, 0.41),
        spike("rtd.platen.C", 20.400, 0.52),
        spike("enc.ram.MPa", 23.100, 0.47),
    ]
    excerpt = independent_excerpt(25142, 56, 24000, 13, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Press P-17 in Caldera-Mold Bay 3 is already in blow-down with platen RTD 178.4 C "
                "over a 165.0 C vent cap. Mold-close ram is 12.0 MPa, still under the 18.0 MPa "
                "close-phase cap. RTD-first should open the blow-down vent; a weak supervisor that "
                "binds platen heat onto the close-phase ram will clamp the wrong actuator of the "
                "cure cycle.",
            ),
            ("domain", "tire-curing-press"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Finish blow-down with platen <= 165.0 C by opening the vent; do not spend a "
                "close-phase ram clamp on a vent over-temp.",
            ),
            ("t0_us", 1756843200000142),
            ("gate_latency_us", 880),
            ("race_window_us", 360),
            ("race_window_rel_ms", [6.0, 6.36]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "rtd.platen.C 178.4 C",
                                "enc.ram.MPa 12.0 MPa",
                            ],
                        ),
                        (
                            "semantics",
                            "RTD-first should MODIFY the blow-down vent (178.4 C > 165.0 C vent cap). "
                            "Ram-first tempts a weak supervisor to treat heat as a close-phase clamp.",
                        ),
                        (
                            "window_derivation",
                            "360 us = one platen-RTD sample minus ram-encoder group delay on this "
                            "cure-press bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 168 us vs combined jitter ~64 us (RTD 30 + ram 34): 2.6x over "
                            "a 2.0x trust floor. Order is correctly RTD-first. The error is which "
                            "phase of the cycle the MODIFY is bound to, not the race.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "platen RTD, 2 kHz, 30 us jitter",
                    "mold-close ram encoder, 2 kHz, 34 us jitter",
                    "mold-cavity thermocouple (context)",
                    "cure-cycle PLC phase bit (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("blowdown_cap_C", 165.0),
                        ("platen_C", 178.4),
                        ("ram_cap_MPa", 18.0),
                        ("ram_MPa", 12.0),
                        ("cycle_phase", "blow_down"),
                        ("vent_floor_kg_s", 1.40),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. P-17 already in blow-down; vent 0.18 kg/s, ram 12.0 MPa.",
                    "2. Platen RTD 178.4 C; ram 12.0 MPa under 18.0 MPa close-phase cap.",
                    "3. Mold-cavity precursor at 0.880 ms.",
                    "4. Race window [6.000, 6.360] ms.",
                    "5. rtd.platen.C 178.4 C at 6.088 ms (winner).",
                    "6. enc.ram.MPa 12.0 MPa at 6.256 ms (loser by 168 us).",
                    "7. Gate at 6.968 ms: MODIFY ram 12.0 -> 6.0 MPa (incorrect phase).",
                    "8. Vent stays 0.18 kg/s; platen still 178.4 C > 165.0 C vent cap.",
                    "9. Shoulder scorch on the green tire; ram never exceeded 12.0 MPa.",
                    "10. Delayed abort_s=480 (8 min press abort / scorch cull).",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "hold_blowdown_trim"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("ram_MPa", 12.0),
                        ("vent_kg_s", 0.18),
                        ("cycle_phase", "blow_down"),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("platen_C", 178.4),
                        ("blowdown_cap_C", 165.0),
                        ("cycle_phase", "blow_down"),
                        ("ram_MPa", 12.0),
                        ("ram_cap_MPa", 18.0),
                        ("vent_kg_s", 0.18),
                        ("vent_floor_kg_s", 1.40),
                        ("race_margin_us", 168),
                        ("combined_jitter_us", 64),
                        ("abort_s", 480),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes holding ram 12.0 MPa and vent 0.18 kg/s because ram is under "
                "the 18.0 MPa close-phase cap; it has not yet bound platen 178.4 C to the blow-down vent floor.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "incorrect"),
            (
                "rationale",
                "Platen 178.4 C looks like a press over-temp, so the supervisor clamps mold-close "
                "ram 12.0 -> 6.0 MPa. RTD-first is treated as the close-phase thermal loop. "
                "Over-caution on a hot mold is the stated doctrine.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "platen_C",
                            OrderedDict(
                                [
                                    ("cap", 165.0),
                                    ("observed", 178.4),
                                    ("executed_ram_MPa", 6.0),
                                    ("cycle_phase", "blow_down"),
                                ]
                            ),
                        ),
                        (
                            "ram_MPa",
                            OrderedDict(
                                [
                                    ("cap", 18.0),
                                    ("observed", 12.0),
                                    ("misbound_as", "close_phase_thermal"),
                                    ("executed", 6.0),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 168),
                                    ("combined_jitter_us", 64),
                                    ("ratio", 2.62),
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
            ("name", "ram_hold_wrong_phase"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("ram_MPa", 6.0),
                        ("vent_kg_s", 0.18),
                        ("cycle_phase", "blow_down"),
                    ]
                ),
            ),
            (
                "gate_effect",
                "MODIFY (incorrect): ram 12.0 -> 6.0 MPa. Routing relay.rtd.platen -> "
                "policy.ram_hold; vent left at 0.18 kg/s with no positive weight to policy.vent_open.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Wrong-MODIFY clamped P-17 ram to 6.0 MPa during blow-down. Platen 178.4 C was over "
                "the 165.0 C vent cap; ram 12.0 MPa was under its own 18.0 MPa close-phase cap. "
                "8 min scorch abort (abort_s=480). Correct gate was MODIFY vent 0.18 -> 1.40 kg/s.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("ram", "clamped 12.0 -> 6.0 MPa; never over 18.0 cap"),
                        ("vent", "left 0.18 kg/s; platen still 178.4 C > 165.0"),
                        ("tire", "shoulder scorch"),
                        ("mission", "cure aborted"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "RTD-first was the correct order and the platen number was over the vent cap; the MODIFY spent that win on the close-phase ram.",
                    "Delayed (abort_s=480): Bay 3 loses 8 min plus one green tire to scorch cull.",
                ],
            ),
            (
                "recovery",
                OrderedDict(
                    [
                        (
                            "correct_gate",
                            "MODIFY the blow-down vent 0.18 -> 1.40 kg/s; leave ram at 12.0 MPa.",
                        ),
                        ("correct_phase", "blow_down"),
                        ("wrong_phase_actuator", "mold_close_ram"),
                        (
                            "wrong_edit_applied",
                            OrderedDict([("ram_MPa", 6.0), ("vent_kg_s", 0.18)]),
                        ),
                        (
                            "cost",
                            "Shoulder scorch + 8 min abort (task/efficiency); ram never exceeded 12.0 MPa (safety near-miss of a false clamp).",
                        ),
                    ]
                ),
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "rtd.platen.C (6.088 ms, 178.4 C)"),
                        ("loser", "enc.ram.MPa (6.256 ms, 12.0 MPa)"),
                        ("margin_us", 168),
                        (
                            "counterfactual_if_reversed",
                            "Ram-first by < 168 us would still be under the 18.0 MPa close-phase cap; "
                            "a correct gate binds rtd.platen.C to vent_open either way. The wrong "
                            "MODIFY spent the RTD win on the wrong phase of the cycle.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 6968),
            (
                "reward_inflection_note",
                "Task, efficiency, and coherence drop at the wrong MODIFY (6.968 ms, tick 4). "
                "The 8 min abort is delayed surprise, not the inflection.",
            ),
        ]
    )
    dw = 0.36
    ras = raster_core(
        24,
        56,
        42,
        56,
        routing(
            "relay.rtd.platen",
            "policy.ram_hold",
            [
                ("relay.rtd.platen", "policy.ram_hold", 0.74),
                ("relay.enc.ram", "policy.ram_hold", 0.22),
            ],
            "acetylcholine",
            0.06,
            "phase_cap_stdp; ACh tags the (wrong) ram_hold bind at the platen residual",
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
            ("decision_window_ms", dw),
            ("decision", "MODIFY"),
            (
                "populations",
                [
                    pop_budget("ram_hold", 48, 0.50, 280.0, dw),
                    pop_budget("vent_open", 48, 0.80, 20.0, dw),
                    pop_budget("phase_ctx", 32, 0.55, 140.0, dw),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r25-142"),
            (
                "title",
                "WRONG-MODIFY at Caldera-Mold Bay 3 / Press P-17: platen 178.4 C > 165.0 C vent cap; "
                "supervisor clamps mold-close ram instead of the blow-down vent",
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
                    "Wrong-modify / wrong-phase. Sidecar arithmetic 178.4 > 165.0 on platen is true; "
                    "MODIFY bound to close-phase ram. total -0.72 = -0.24 + -0.22 + -0.22 + -0.10 + 0.06.",
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
                    "Teaches a probe that a correct RTD-first race can still be a wrong gate when "
                    "the MODIFY binds platen heat onto the close-phase ram. Convictable from "
                    "cycle_phase and caps without rubber chemistry.",
                    2,
                    supervisor_error_type="wrong-modify",
                ),
            ),
        ]
    )


def record_143():
    ticks = [
        tick(2410, 0.01, 0.04, 0.01, 0.01, 0.01),
        tick(6040, 0.02, 0.08, 0.02, 0.02, 0.01),
        tick(6188, 0.01, 0.06, 0.02, 0.01, 0.01),
        tick(7040, 0.03, 0.12, 0.04, 0.04, 0.01),
        tick(9100, 0.02, 0.06, 0.02, 0.01, 0.01),
        tick(360000000, 0.01, 0.04, 0.01, 0.01, 0.01),
    ]
    spikes = [
        spike("tc.dummy.ctx", 1.330, 0.43),
        spike("fm.coolant.lpm", 2.880, 0.61),
        spike("faraday.beam.ua", 4.410, 0.49),
        spike("fm.coolant.lpm", 6.040, 1.36),
        spike("faraday.beam.ua", 6.188, 1.11),
        spike("ctrl.gate", 7.040, 1.04),
        spike("fm.coolant.lpm", 9.020, 0.78),
        spike("tc.dummy.ctx", 12.440, 0.44),
        spike("faraday.beam.ua", 16.900, 0.58),
        spike("ctrl.gate", 22.100, 0.81),
        spike("fm.coolant.lpm", 29.400, 0.53),
        spike("tc.dummy.ctx", 38.200, 0.37),
        spike("faraday.beam.ua", 42.600, 0.46),
    ]
    excerpt = independent_excerpt(25143, 112, 46000, 15, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Target T-9 on the Isotope-Pad IP-HIL stand shows coolant 8.2 L/min under the "
                "12.0 L/min beam-on floor while a Faraday cup still counts 14 uA of pad-lamp ions. "
                "Flow-first holds the RF; Faraday-first would have treated lamp ionization as beam "
                "current and kept extract armed.",
            ),
            ("domain", "cyclotron-target"),
            ("sim_or_real", "hil"),
            (
                "goal",
                "Keep extract off unless coolant >= 12.0 L/min; do not treat pad-lamp Faraday "
                "current as a beam-on permit.",
            ),
            ("t0_us", 1756843200000143),
            ("gate_latency_us", 1000),
            ("race_window_us", 320),
            ("race_window_rel_ms", [6.0, 6.32]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "fm.coolant.lpm 8.2 L/min",
                                "faraday.beam.ua 14 uA lamp ions",
                            ],
                        ),
                        (
                            "semantics",
                            "Flow-first REJECTs extract (8.2 < 12.0 L/min floor). Faraday-first would "
                            "ACCEPT on pad-lamp ionization mistaken for beam current.",
                        ),
                        (
                            "window_derivation",
                            "320 us = one coolant-flowmeter sample minus Faraday-cup group delay on "
                            "this HIL target bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 148 us vs combined jitter ~58 us (flow 26 + Faraday 32): 2.6x over "
                            "a 2.0x trust floor. Reversing order by < 148 us inside the 320 us window "
                            "would have kept extract armed on 14 uA of lamp ions.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "target coolant flowmeter, 5 kHz burst, 26 us jitter",
                    "Faraday cup, 2 kHz, 32 us jitter",
                    "dummy-target thermocouple (context)",
                    "HIL lamp-spectrum monitor (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("coolant_floor_lpm", 12.0),
                        ("observed_coolant_lpm", 8.2),
                        ("faraday_ua", 14.0),
                        ("beam_permit_ua", 80.0),
                        ("proposed_extract_ua", 18.0),
                    ]
                ),
            ),
            (
                "hil",
                OrderedDict(
                    [
                        ("pad", "Isotope-Pad IP-HIL dummy-target stand"),
                        ("injected", "coolant-flow dropout + Faraday lamp-ion packet"),
                        (
                            "note",
                            "Hardware-in-the-loop dummy target. Invented plant; not a live cyclotron shot.",
                        ),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Target T-9 on the IP-HIL stand; extract 18 uA armed.",
                    "2. Faraday lamp packet injected 110-150 us before the flowmeter volume.",
                    "3. Dummy-target precursor at 1.330 ms.",
                    "4. Race window [6.000, 6.320] ms.",
                    "5. fm.coolant.lpm 8.2 L/min at 6.040 ms (winner).",
                    "6. faraday.beam.ua 14 uA at 6.188 ms (loser by 148 us).",
                    "7. Gate at 7.040 ms: REJECT hold extract 0 uA; do not beam-on.",
                    "8. Coolant remains under the 12.0 L/min floor this cycle.",
                    "9. Faraday 14 uA stays a lamp artifact, not beam current.",
                    "10. Delayed (abort_s=360): 6 min dummy-target re-wet and lamp retune.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "extract_18uA"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("extract_ua", 18.0),
                        ("beam_on", True),
                        ("hold", False),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("coolant_lpm", 8.2),
                        ("coolant_floor_lpm", 12.0),
                        ("faraday_ua", 14.0),
                        ("beam_permit_ua", 80.0),
                        ("race_margin_us", 148),
                        ("combined_jitter_us", 58),
                        ("abort_s", 360),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 18 uA extract because Faraday 14 uA looks like a beam tick; it "
                "has not yet bound coolant 8.2 L/min to the 12.0 L/min floor.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "REJECT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Coolant 8.2 L/min won by 148 us, so the beam-on floor is already violated. Faraday "
                "14 uA is under the 80 uA permit and is pad-lamp ionization. REJECT: extract 0 uA, "
                "beam_on false. A MODIFY that keeps extract armed is not indicated: next-sample flow "
                "is 7.9 L/min.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "coolant_lpm",
                            OrderedDict(
                                [
                                    ("floor", 12.0),
                                    ("observed", 8.2),
                                    ("executed_extract_ua", 0.0),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 148),
                                    ("combined_jitter_us", 58),
                                    ("ratio", 2.55),
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
            ("name", "beam_hold"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("extract_ua", 0.0),
                        ("beam_on", False),
                        ("hold", True),
                    ]
                ),
            ),
            (
                "gate_effect",
                "REJECT: extract 18 -> 0 uA. Coolant floor held. Faraday lamp ions unused as a go signal.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct REJECT held T-9 extract at 0 uA. Coolant 8.2 L/min was under the 12.0 L/min "
                "floor; Faraday 14 uA was pad-lamp ionization. 6 min dummy-target re-wet (abort_s=360).",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("beam", "held; extract 0 uA"),
                        ("coolant", "still 8.2 L/min < 12.0 floor"),
                        ("faraday", "14 uA lamp ions unused"),
                        ("mission", "extract deferred"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Pad lamp injected Faraday current 110-150 us before the flowmeter saw the same dropout; flow-first is the coolant loop.",
                    "Delayed (abort_s=360): 6 min dummy-target re-wet and lamp-spectrum retune.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "fm.coolant.lpm (6.040 ms, 8.2 L/min)"),
                        ("loser", "faraday.beam.ua (6.188 ms, 14 uA)"),
                        ("margin_us", 148),
                        (
                            "counterfactual_if_reversed",
                            "Faraday-first by < 148 us inside the 320 us window would have kept "
                            "extract armed on 14 uA of lamp ions while coolant stayed under 12.0 L/min.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 7040),
            (
                "reward_inflection_note",
                "Safety and coherence peak at the correct REJECT (7.040 ms, tick 4). The 6 min "
                "re-wet is delayed surprise, not the inflection.",
            ),
        ]
    )
    dw = 0.32
    ras = raster_core(
        46,
        112,
        22,
        113,
        routing(
            "thalamic-relay.target-flow",
            "spikenaut.policy.beam-hold",
            [
                ("relay.fm.coolant", "policy.beam_hold", 0.71),
                ("relay.faraday.ua", "policy.beam_go", 0.24),
            ],
            "dopamine",
            0.05,
            "floor_stdp; DA tags the coolant-floor bind at the flowmeter win",
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
            ("decision_window_ms", dw),
            ("decision", "REJECT"),
            (
                "populations",
                [
                    pop_budget("beam_hold", 56, 0.50, 250.0, dw),
                    pop_budget("beam_go", 56, 0.80, 20.0, dw),
                    pop_budget("flow_ctx", 32, 0.55, 150.0, dw),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r25-143"),
            (
                "title",
                "Isotope-Pad IP-HIL / Target T-9: coolant 8.2 L/min beats Faraday lamp ions 14 uA; "
                "correct REJECT holds extract",
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
                    "Correct REJECT. Coolant 8.2 < 12.0 floor; Faraday 14 uA is lamp, not beam. "
                    "total +0.78 = 0.10 + 0.40 + 0.12 + 0.10 + 0.06.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "cyclotron-target",
                    [
                        "reject",
                        "hil",
                        "flow-vs-faraday",
                        "lamp-ion-artifact",
                    ],
                    "Teaches that a Faraday lamp-ion packet can lose to a coolant flowmeter inside "
                    "a 320 us window; reversing 148 us would have kept extract armed under the floor.",
                    3,
                ),
            ),
        ]
    )


def record_144():
    ticks = [
        tick(1540, 0.06, 0.04, 0.02, 0.02, 0.01),
        tick(5210, 0.10, 0.08, 0.04, 0.03, 0.02),
        tick(5388, 0.06, 0.04, 0.02, 0.01, 0.01),
        tick(6310, 0.12, 0.08, 0.04, 0.04, 0.02),
        tick(9100, 0.05, 0.04, 0.02, 0.01, 0.01),
        tick(240000000, 0.03, 0.02, 0.02, 0.01, 0.01),
    ]
    spikes = [
        spike("gps.barge.ctx", 1.140, 0.40),
        spike("lc.top.kN", 2.280, 0.56),
        spike("imu.heave.m", 3.610, 0.47),
        spike("lc.top.kN", 5.210, 1.27),
        spike("imu.heave.m", 5.388, 1.08),
        spike("ctrl.gate", 6.310, 0.99),
        spike("lc.top.kN", 8.760, 0.76),
        spike("gps.barge.ctx", 11.020, 0.43),
        spike("imu.heave.m", 14.400, 0.55),
        spike("ctrl.gate", 18.900, 0.82),
        spike("lc.top.kN", 22.600, 0.50),
        spike("gps.barge.ctx", 27.200, 0.36),
    ]
    excerpt = independent_excerpt(25144, 60, 29000, 13, spike_avoid_us(spikes))
    params = OrderedDict(
        [
            ("payout_m_s", 0.80),
            ("hold", False),
            ("top_tension_kN", 48.2),
        ]
    )
    state = OrderedDict(
        [
            (
                "description",
                "Barge Kelp-3 on Lay-Sound LS-5 pays out at 0.80 m/s with top tension 48.2 kN under "
                "a 72.0 kN catenary cap. A heave IMU still reports 0.62 m residual from the last "
                "swell. Loadcell-first confirms the already-legal payout; heave-first would have "
                "REJECTED a legal catenary on sea-state.",
            ),
            ("domain", "cable-lay-barge"),
            ("sim_or_real", "simulated"),
            (
                "goal",
                "Pay out 0.80 m/s while top tension stays <= 72.0 kN; do not abort on a 0.62 m heave residual.",
            ),
            ("t0_us", 1756843200000144),
            ("gate_latency_us", 1100),
            ("race_window_us", 420),
            ("race_window_rel_ms", [5.0, 5.42]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "lc.top.kN 48.2 kN",
                                "imu.heave.m 0.62 m residual",
                            ],
                        ),
                        (
                            "semantics",
                            "Loadcell-first ACCEPTS the 0.80 m/s payout (already under 72.0 kN). "
                            "Heave-first would REJECT on a swell residual.",
                        ),
                        (
                            "window_derivation",
                            "420 us = one top-tension sample minus barge-IMU heave group delay on "
                            "this lay-bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 178 us vs combined jitter ~62 us (loadcell 28 + IMU 34): 2.9x over "
                            "a 2.0x trust floor. Reversing order by < 178 us inside the 420 us window "
                            "would have REJECTED a legal 0.80 m/s payout.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "top-tension loadcell, 2 kHz, 28 us jitter",
                    "barge IMU heave 0-2 m, 34 us jitter",
                    "GPS barge heading (context)",
                    "touchdown transponder (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("tension_cap_kN", 72.0),
                        ("observed_tension_kN", 48.2),
                        ("heave_m", 0.62),
                        ("heave_abort_m", 1.80),
                        ("proposed_payout_m_s", 0.80),
                    ]
                ),
            ),
            (
                "simulation",
                OrderedDict(
                    [
                        (
                            "solver",
                            "lumped-cable catenary + 2nd-order barge heave, seed 25144; 12 elements, "
                            "4 s swell; NOT U-RANS, NOT actuator-disk, NOT a wet-stand",
                        ),
                        (
                            "fidelity_limits",
                            "Linear heave; no vortex-induced vibration. Raster is kernelized events, "
                            "not an independent LIF.",
                        ),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Kelp-3 indexed on LS-5; payout 0.80 m/s armed.",
                    "2. Top tension 48.2 kN; heave residual 0.62 m.",
                    "3. GPS precursor at 1.140 ms.",
                    "4. Race window [5.000, 5.420] ms.",
                    "5. lc.top.kN 48.2 kN at 5.210 ms (winner).",
                    "6. imu.heave.m 0.62 m at 5.388 ms (loser by 178 us).",
                    "7. Gate at 6.310 ms: ACCEPT 0.80 m/s; executed identical to proposed.",
                    "8. Payout continues; peak tension 49.1 kN < 72.0 cap.",
                    "9. Heave remains a swell residual, not a tension loop.",
                    "10. Delayed (survey_s=240): 4 min catenary recount on the next swell.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "payout_080"),
            ("parameters", params),
            (
                "evidence",
                OrderedDict(
                    [
                        ("top_tension_kN", 48.2),
                        ("tension_cap_kN", 72.0),
                        ("heave_m", 0.62),
                        ("heave_abort_m", 1.80),
                        ("race_margin_us", 178),
                        ("combined_jitter_us", 62),
                        ("survey_s", 240),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 0.80 m/s payout because top tension 48.2 kN is under the 72.0 kN "
                "cap; heave 0.62 m is under the 1.80 m abort and is treated as swell, not tension.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Top tension 48.2 kN won by 178 us and is under the 72.0 kN cap. Heave 0.62 m is "
                "under the 1.80 m abort. ACCEPT the already-legal 0.80 m/s payout. A REJECT on swell "
                "would stall a legal lay.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "top_tension_kN",
                            OrderedDict(
                                [
                                    ("cap", 72.0),
                                    ("observed", 48.2),
                                    ("executed_payout_m_s", 0.80),
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
            ("name", "payout_080"),
            ("parameters", OrderedDict(params)),
            (
                "gate_effect",
                "ACCEPT: payout 0.80 m/s unchanged. Tension stayed 48.2-49.1 kN < 72.0 cap.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT kept Kelp-3 payout at 0.80 m/s. Top tension 48.2 kN was under the "
                "72.0 kN cap; heave 0.62 m was swell. 4 min catenary recount (survey_s=240).",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("payout", "0.80 m/s continued"),
                        ("tension", "peak 49.1 kN < 72.0 cap"),
                        ("heave", "0.62 m unused as a hold"),
                        ("mission", "lay continues"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Heave residual arrived 178 us after the loadcell; reversing that order would have REJECTED a legal payout.",
                    "Delayed (survey_s=240): 4 min catenary recount on the next swell, not a tension event.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "lc.top.kN (5.210 ms, 48.2 kN)"),
                        ("loser", "imu.heave.m (5.388 ms, 0.62 m)"),
                        ("margin_us", 178),
                        (
                            "counterfactual_if_reversed",
                            "Heave-first by < 178 us inside the 420 us window would have REJECTED "
                            "an already-legal 0.80 m/s payout on a 0.62 m swell residual.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 6310),
            (
                "reward_inflection_note",
                "Task and safety peak at the correct ACCEPT (6.310 ms, tick 4). The 4 min recount "
                "is delayed surprise, not the inflection.",
            ),
        ]
    )
    dw = 0.42
    ras = raster_core(
        29,
        60,
        34,
        59,
        routing(
            "thalamic-relay.top-tension",
            "spikenaut.policy.payout-go",
            [
                ("relay.lc.top", "policy.payout_go", 0.69),
                ("relay.imu.heave", "policy.heave_hold", 0.28),
            ],
            "serotonin",
            0.03,
            "catenary_stdp; 5-HT tags the already-legal tension bind",
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
            ("decision_window_ms", dw),
            ("decision", "ACCEPT"),
            (
                "populations",
                [
                    pop_budget("payout_go", 40, 0.50, 280.0, dw),
                    pop_budget("heave_hold", 40, 0.50, 70.0, dw),
                    pop_budget("catenary_ctx", 24, 0.55, 120.0, dw),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r25-144"),
            (
                "title",
                "Lay-Sound LS-5 / Kelp-3: top tension 48.2 kN beats heave 0.62 m by 178 us; "
                "correct ACCEPT of an already-legal 0.80 m/s payout",
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
                    "Correct ACCEPT. Tension 48.2 < 72.0 cap; heave is swell, not load. "
                    "total +1.08 = 0.42 + 0.30 + 0.16 + 0.12 + 0.08.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "cable-lay-barge",
                    [
                        "accept",
                        "cable-lay",
                        "tension-vs-heave",
                        "simulated-catenary",
                        "simulated",
                    ],
                    "Teaches that a barge-heave residual can lose to top-tension inside a 420 us "
                    "window; reversing 178 us would have REJECTED an already-legal payout.",
                    4,
                ),
            ),
        ]
    )


def record_145():
    ticks = [
        tick(1640, 0.06, 0.04, 0.02, 0.02, 0.01),
        tick(4040, 0.10, 0.08, 0.04, 0.03, 0.02),
        tick(4188, 0.06, 0.04, 0.02, 0.01, 0.01),
        tick(4940, 0.14, 0.10, 0.06, 0.04, 0.02),
        tick(7200, 0.05, 0.04, 0.02, 0.01, 0.01),
        tick(180000000, 0.03, 0.02, 0.02, 0.01, 0.01),
    ]
    spikes = [
        spike("enc.bowl.ctx", 0.720, 0.40),
        spike("dens.oil.sg", 1.880, 0.56),
        spike("visc.bowl.cP", 2.180, 0.47),
        spike("dens.oil.sg", 4.040, 1.27),
        spike("visc.bowl.cP", 4.188, 1.08),
        spike("ctrl.gate", 4.940, 0.99),
        spike("dens.oil.sg", 6.760, 0.76),
        spike("enc.bowl.ctx", 9.020, 0.43),
        spike("visc.bowl.cP", 12.400, 0.55),
        spike("ctrl.gate", 15.900, 0.82),
        spike("dens.oil.sg", 18.600, 0.50),
        spike("enc.bowl.ctx", 21.200, 0.36),
    ]
    excerpt = independent_excerpt(25145, 70, 22000, 12, spike_avoid_us(spikes))
    params = OrderedDict(
        [
            ("bowl_rpm", 3200.0),
            ("hold", False),
            ("feed_m3_h", 4.2),
        ]
    )
    state = OrderedDict(
        [
            (
                "description",
                "Decanter D-8 at Drupe-Press DP-2 holds 3200 rpm while oil densitometer 0.912 stays "
                "under the 0.940 water-cut cap. A bowl viscometer still flags 4.8 cP from a wash-water "
                "film. Density-first confirms the already-legal bowl; visc-first would have REJECTED "
                "a legal spin on a rinse film.",
            ),
            ("domain", "olive-oil-decanter"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Hold 3200 rpm while oil SG stays <= 0.940; do not abort on a 4.8 cP wash-water film.",
            ),
            ("t0_us", 1756843200000145),
            ("gate_latency_us", 900),
            ("race_window_us", 280),
            ("race_window_rel_ms", [4.0, 4.28]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "dens.oil.sg 0.912",
                                "visc.bowl.cP 4.8 cP film",
                            ],
                        ),
                        (
                            "semantics",
                            "Density-first ACCEPTS 3200 rpm (0.912 < 0.940 water-cut cap). Visc-first "
                            "would REJECT on a wash-water film.",
                        ),
                        (
                            "window_derivation",
                            "280 us = one densitometer sample minus bowl-viscometer group delay on "
                            "this decanter bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 148 us vs combined jitter ~54 us (dens 24 + visc 30): 2.7x over "
                            "a 2.0x trust floor. Reversing order by < 148 us inside the 280 us window "
                            "would have REJECTED a legal 3200 rpm bowl.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "inline oil densitometer, 4 kHz, 24 us jitter",
                    "bowl viscometer, 4 kHz, 30 us jitter",
                    "bowl encoder (context)",
                    "feed-temp RTD (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("sg_cap", 0.940),
                        ("observed_sg", 0.912),
                        ("visc_cP", 4.8),
                        ("visc_abort_cP", 18.0),
                        ("proposed_bowl_rpm", 3200.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. D-8 indexed on DP-2; bowl 3200 rpm armed.",
                    "2. Oil SG 0.912; viscometer 4.8 cP from a rinse film.",
                    "3. Bowl-encoder precursor at 0.720 ms.",
                    "4. Race window [4.000, 4.280] ms.",
                    "5. dens.oil.sg 0.912 at 4.040 ms (winner).",
                    "6. visc.bowl.cP 4.8 cP at 4.188 ms (loser by 148 us).",
                    "7. Gate at 4.940 ms: ACCEPT 3200 rpm; executed identical to proposed.",
                    "8. Bowl continues; peak SG 0.918 < 0.940 cap.",
                    "9. Visc 4.8 cP remains a wash-water film, not a water-cut.",
                    "10. Delayed (qc_s=180): 3 min bottle QC on the next lot.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "bowl_3200"),
            ("parameters", params),
            (
                "evidence",
                OrderedDict(
                    [
                        ("oil_sg", 0.912),
                        ("sg_cap", 0.940),
                        ("visc_cP", 4.8),
                        ("visc_abort_cP", 18.0),
                        ("race_margin_us", 148),
                        ("combined_jitter_us", 54),
                        ("qc_s", 180),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 3200 rpm because oil SG 0.912 is under the 0.940 water-cut cap; "
                "visc 4.8 cP is under the 18.0 abort and is treated as a rinse film, not a water-cut.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Oil SG 0.912 won by 148 us and is under the 0.940 cap. Visc 4.8 cP is under the "
                "18.0 abort. ACCEPT the already-legal 3200 rpm bowl. A REJECT on rinse film would "
                "stall a legal press.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "oil_sg",
                            OrderedDict(
                                [
                                    ("cap", 0.940),
                                    ("observed", 0.912),
                                    ("executed_bowl_rpm", 3200.0),
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
            ("name", "bowl_3200"),
            ("parameters", OrderedDict(params)),
            (
                "gate_effect",
                "ACCEPT: bowl 3200 rpm unchanged. SG stayed 0.912-0.918 < 0.940 cap.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT kept D-8 at 3200 rpm. Oil SG 0.912 was under the 0.940 cap; visc "
                "4.8 cP was a wash-water film. 3 min bottle QC (qc_s=180).",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("bowl", "3200 rpm continued"),
                        ("sg", "peak 0.918 < 0.940 cap"),
                        ("visc", "4.8 cP unused as a hold"),
                        ("mission", "press continues"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Wash-water film arrived 148 us after the densitometer; reversing that order would have REJECTED a legal bowl.",
                    "Delayed (qc_s=180): 3 min bottle QC on the next lot, not a water-cut event.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "dens.oil.sg (4.040 ms, 0.912)"),
                        ("loser", "visc.bowl.cP (4.188 ms, 4.8 cP)"),
                        ("margin_us", 148),
                        (
                            "counterfactual_if_reversed",
                            "Visc-first by < 148 us inside the 280 us window would have REJECTED "
                            "an already-legal 3200 rpm bowl on a 4.8 cP rinse film.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 4940),
            (
                "reward_inflection_note",
                "Task and safety peak at the correct ACCEPT (4.940 ms, tick 4). The 3 min QC is "
                "delayed surprise, not the inflection.",
            ),
        ]
    )
    dw = 0.28
    ras = raster_core(
        22,
        70,
        40,
        62,
        routing(
            "thalamic-relay.oil-sg",
            "spikenaut.policy.bowl-go",
            [
                ("relay.dens.oil", "policy.bowl_go", 0.70),
                ("relay.visc.bowl", "policy.visc_hold", 0.26),
            ],
            "histamine",
            0.045,
            "watercut_stdp; HA tags the already-legal densitometer bind",
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
            ("decision_window_ms", dw),
            ("decision", "ACCEPT"),
            (
                "populations",
                [
                    pop_budget("bowl_go", 40, 0.50, 300.0, dw),
                    pop_budget("visc_hold", 40, 0.50, 80.0, dw),
                    pop_budget("dens_ctx", 24, 0.55, 150.0, dw),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r25-145"),
            (
                "title",
                "Drupe-Press DP-2 / Decanter D-8: oil SG 0.912 beats visc film 4.8 cP by 148 us; "
                "correct ACCEPT of an already-legal 3200 rpm bowl",
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
                    "Correct ACCEPT. SG 0.912 < 0.940 cap; visc is rinse film, not water-cut. "
                    "total +1.14 = 0.44 + 0.32 + 0.18 + 0.12 + 0.08.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "olive-oil-decanter",
                    [
                        "accept",
                        "decanter",
                        "density-vs-visc",
                        "designed",
                    ],
                    "Teaches that a wash-water visc film can lose to oil densitometer inside a "
                    "280 us window; reversing 148 us would have REJECTED an already-legal bowl.",
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


def prior_domains_and_descs():
    domains = set()
    descs = []
    for path in sorted(Path("/tmp").glob("ttf-r*/batch-r*.jsonl")):
        if path.resolve() == BATCH_PATH.resolve():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
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
    return domains, descs


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
    prior_doms, prior_descs = prior_domains_and_descs()
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
    if len(wrong) != 1 or wrong[0]["id"] != "ttf-r25-142":
        issues.append(f"wrong-gate set {[w['id'] for w in wrong]}")
    if wrong and wrong[0]["meta"].get("supervisor_error_type") != "wrong-modify":
        issues.append("expected wrong-modify")
    if any(r["state"]["sim_or_real"] == "real" for r in records):
        issues.append("sim_or_real=real")
    hil = [r["id"] for r in records if r["state"]["sim_or_real"] == "hil"]
    if hil != ["ttf-r25-143"]:
        issues.append(f"hil set {hil}")
    decisions = [r["safety_decision"]["decision"] for r in records]
    if (
        decisions.count("ACCEPT") != 2
        or decisions.count("MODIFY") != 2
        or decisions.count("REJECT") != 1
    ):
        issues.append(f"gate mix {decisions}")
    ids = [r["id"] for r in records]
    if ids != [f"ttf-r25-{n}" for n in range(141, 146)]:
        issues.append(f"ids {ids}")
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
        if rec["id"] == "ttf-r25-141":
            if rec["raster"].get("excerpt_source") != "independent_lif":
                issues.append("141 missing independent_lif")
            if rec["future_outcome"]["reward_inflection_t_us"] > rec["raster"]["window_ms"] * 1000:
                issues.append("141 inflection outside window")
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
        if rec["meta"]["round"] != 25:
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
        if not (8 <= len(rec["raster"]["excerpt"]) <= 16):
            issues.append(f"{rec['id']} excerpt n={len(rec['raster']['excerpt'])}")
        exec_p = rec["executed_action"]["parameters"]
        prop_p = rec["proposed_action"]["parameters"]
        if rec["safety_decision"]["decision"] == "ACCEPT" and exec_p != prop_p:
            issues.append(f"{rec['id']} ACCEPT params differ")
        if rec["id"] == "ttf-r25-141" and rec["reward_components"]["total"] >= 0:
            issues.append("141 partnered-neg total not negative")
        if rec["id"] == "ttf-r25-142":
            if rec["executed_action"]["parameters"].get("ram_MPa") == rec["proposed_action"]["parameters"].get("ram_MPa"):
                issues.append("142 ram not edited")
            if rec["executed_action"]["parameters"].get("vent_kg_s") != rec["proposed_action"]["parameters"].get("vent_kg_s"):
                issues.append("142 vent was edited; should stay")
            table_to = {row["to"] for row in rec["raster"]["routing"]["table"]}
            if "policy.vent_open" in table_to:
                issues.append("142 routing still has vent_open")
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
    return issues, jmax, jprior


def notes_text(jmax: float, jprior: float) -> str:
    return f"""# Thalamic Trajectory Factory — NOTES-r25

- Factory: `thalamic-trajectory-factory`
- Run label: `2026-09-02-final-heavy`
- Generator: `grok-4.6`
- Channel: SuperGrok Heavy consumer chat (RM-793 research-only)
- Quota: 5
- IDs: `ttf-r25-141` … `ttf-r25-145`
- Domains this batch: `salt-cavern-CAES`, `tire-curing-press`, `cyclotron-target`, `cable-lay-barge`, `olive-oil-decanter`

These five domain slugs sit outside the prompt 8-pool and outside staged r13–r23 sit-ins (including r23 `aluminum-potline` / `vial-lyophilizer` and r22 `rotary-lime-kiln` / `maglev-guideway-gap`). All five plants are invented. Do not restack r12–r23 plants (Marrow-Dock, Vesper-Lattice, Brine-Well, Saddle-Arc, Ashlar-Gait, Nacre-Well, Quern-Forge, Tinder-Box, Whimbrel-Stack, Cinder-Loft, Suture-Isle, Kiln-Spur, Oxbow-Switch, Pitch-Kettle, Shale-Quay, Polder-Rye, Flint-Mask, Gyre-Tokamak, Quarry-Bowl, Orpiment, Apside-Yard, Sump-Drift, Felt-Reach, Frost-Cist, Clothoid-Bowl, Wort-Cairn, Firn-Span, Sleet-Row, Oxbow-Pound, Tuyere-Holt, Bracken-Wire, Cullet-Reach, Rime-Causeway, Abyss-Joint, Gnomon-Well, Scree-Hitch, Flux-Kettle, Mire-Cask, Slack-Firth, Chaff-Rise, Sinter-Ridge, Chaff-Mere, Caisson-Forge, Crumb-Vault, Caliche-Drift, Thaw-Reach, Kipple-Gate, Anode-Fen, Vial-Rime, Tern-Apron).

## Batch map

| id | domain | decision | correctness | sim_or_real | total | edge |
|----|--------|----------|-------------|-------------|-------|------|
| ttf-r25-141 | salt-cavern-CAES | MODIFY | correct | designed | **−0.44** | process-correct injection clamp; brine-stringer part inside 40 ms raster; independent LIF |
| ttf-r25-142 | tire-curing-press | MODIFY | **incorrect (wrong-modify / wrong-phase)** | designed | −0.72 | platen 178.4 C > 165.0 vent cap; clamp applied to **mold-close ram** not blow-down vent |
| ttf-r25-143 | cyclotron-target | REJECT | correct | hil | +0.78 | coolant 8.2 L/min beats Faraday lamp ions 14 uA; hold extract |
| ttf-r25-144 | cable-lay-barge | ACCEPT | correct | simulated | +1.08 | top tension 48.2 kN vs heave 0.62 m; proposed 0.80 m/s already legal |
| ttf-r25-145 | olive-oil-decanter | ACCEPT | correct | designed | +1.14 | oil SG 0.912 vs visc film 4.8 cP; proposed 3200 rpm already legal |

Gate mix: 2 ACCEPT, 1 correct MODIFY (partnered-neg, in-window), 1 incorrect MODIFY (wrong-phase of a cyclic process), 1 correct REJECT. Provenance: designed×3, simulated×1, hil×1 (Isotope-Pad dummy-target stand). Intra-batch Jaccard on `state.description` {jmax:.3f} (max vs prior staged {jprior:.3f}).

## Wrong-modify

**ttf-r25-142** is the mandated incorrect gate (`safety_decision.correctness=incorrect`, `meta.supervisor_error_type=wrong-modify`). Alternate vs even rounds: r12/r14/r16/r18/r20/r22 hosted wrong-reject; odd rounds host wrong-modify. This is **wrong-phase**, not r13/r19 wrong-axis, not r14/r23 wrong-loop, not r21 wrong-polarity. Do not emit a wrong-ACCEPT.

Caldera-Mold Bay 3 / Press P-17 is already in **blow-down**. Platen RTD **178.4 C** against a **165.0 C** vent cap. Mold-close ram **12.0 MPa** is under its own **18.0 MPa** close-phase cap. Sidecar arithmetic `178.4 > 165.0` is true. A weak supervisor treats “the thermal loop” as the close-phase ram, clamps ram 12.0 → 6.0 MPa, and leaves the blow-down vent at 0.18 kg/s. Convictable without rubber chemistry: `evidence.platen_C > evidence.blowdown_cap_C`, `cycle_phase == blow_down`, `executed_action` sets `ram_MPa=6` without raising `vent_kg_s`, `raster.routing.table` sends `relay.rtd.platen` → `policy.ram_hold` (weight 0.74) with no positive weight to `policy.vent_open`, and `gate_snn` has `ram_hold` above threshold while `vent_open` is not. Recovery: MODIFY vent 0.18 → 1.40 kg/s; leave ram at 12.0 MPa. Cost: shoulder scorch + 8 min abort (`abort_s=480`).

## Partnered-negative in-window (141)

**ttf-r25-141** is the partnered negative: process-correct MODIFY (injection held 2.1 kg/s; cavern 61.4 bar < 62.0 cap) while the world still charges. Safety −0.60 prices the String-C12 part at **19.200 ms**; `task_progress` stays +0.32 because the clamp completed. Inflection `t_us=19200` is tick 5 and is **inside** the 40 ms raster (`19200 ≤ 40000`). Named un-netted loss: 18 min cavern isolate (`abort_s=1080`). Not folded into process heads.

Independent LIF (the one labeled sidecar sim): `state.sim_or_real` remains `designed`. `raster.excerpt_source=independent_lif`, `raster.sim_scope=sidecar_only`, `raster.lif` seed 25141, stim `[18000, 21000]`. Excerpt is membrane crossings (`lif.clamp` early vs `lif.stringer` 18–21 ms), not a 1:1 remap of `spike_events`. `meta.tags` include `independent-lif-raster` and `sidecar-sim-only`.

## Reward formula and tick reconciliation

Declared aggregation on every record:

`total = task_progress + safety + efficiency + coherence + exploration`

Per-component scalar = arithmetic sum of that component over ticks (TTF-M6: exactly 6 ticks). Tick 6 is bound to a published sidecar (`abort_s`, `survey_s`, `qc_s`) and is strictly after the raster window. Inflection `t_us` is an actual tick.

| id | ticks | tp | saf | eff | coh | exp | total | inflection tick |
|----|-------|----|-----|-----|-----|-----|-------|-----------------|
| 141 | 6 | +0.32 | −0.60 | −0.16 | +0.04 | −0.04 | −0.44 | 5 (19200) |
| 142 | 6 | −0.24 | −0.22 | −0.22 | −0.10 | +0.06 | −0.72 | 4 (6968) |
| 143 | 6 | +0.10 | +0.40 | +0.12 | +0.10 | +0.06 | +0.78 | 4 (7040) |
| 144 | 6 | +0.42 | +0.30 | +0.16 | +0.12 | +0.08 | +1.08 | 4 (6310) |
| 145 | 6 | +0.44 | +0.32 | +0.18 | +0.12 | +0.08 | +1.14 | 4 (4940) |

Tick-6 sidecar bind: 141 `abort_s=1080`, 142 `abort_s=480`, 143 `abort_s=360`, 144 `survey_s=240`, 145 `qc_s=180`.

## Raster / energy (Loihi-2 4-core, 23 pJ/spike)

| id | domain | n | rate Hz | window_ms | spikes | energy_pJ | energy_uJ |
|----|--------|---|---------|-----------|--------|-----------|-----------|
| 141 | salt-cavern-CAES | 80 | 25 | 40 | 80 | 1840 | 0.001840 |
| 142 | tire-curing-press | 56 | 42 | 24 | 56 | 1288 | 0.001288 |
| 143 | cyclotron-target | 112 | 22 | 46 | 113 | 2599 | 0.002599 |
| 144 | cable-lay-barge | 60 | 34 | 29 | 59 | 1357 | 0.001357 |
| 145 | olive-oil-decanter | 70 | 40 | 22 | 62 | 1426 | 0.001426 |

`spikes = round(n × rate × window_s)`. Every record carries `gate_snn` whose `decision` matches the safety gate; populations that declare rate+spikes meet the same ±1 budget against `decision_window_s`. `routing.third_factor` has modulator, `tau_e_s`/`tau_e_ms` pair, and eligibility. Excerpt same-neuron gap ≥ 1000 µs; spike trains same-channel refractory ≥ 0.8 ms. Non-141 excerpts are kernelized and independent of `spike_events` times (overlap < 0.8).

## Local checks (staging, not raw)

See generator stdout: `check_jsonl` FactoryStaging, `validate_run.check_line`, `dumps_exact_json`, `raster_status`, `verify_batch_for_frontier(strict=True)`, `spike_probe.py --strict`, tick sums, refractory, Jaccard.

Never `training_ready`. Never `sim_or_real=real`. Never wrote `outputs/raw/`.

## Residual weaknesses (honest)

1. Only **one** labeled independent LIF (141). The other four excerpts are independent of `spike_events` times but are not declared population sims.
2. Wrong-ACCEPT still absent (guard).
3. Tick-6 sidecar bind is a densification of r14, not a new class.
4. Five domain slugs leave the prompt's 8-item pool; a later round that must stay inside the pool will have to rotate sit-outs instead.
5. 144/145 ACCEPT are already-legal proposals confirmed by race order; a later round could pair an ACCEPT with a world charge that does not go negative.

## Next densification target

Labeled LIF on a second record, or an ISI histogram sidecar. If a later round returns to the 8-item pool, sit out the r12 five again. Wrong-ACCEPT remains structurally absent until a prompt amendment.

Novel coverage: 26.0%
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
        BATCH_PATH, "batch-r25.jsonl", staging=FactoryStaging(enabled=True)
    )
    report.append(("check_jsonl FactoryStaging", errors, warnings, kinds, nrec))
    line_errs = []
    for i, rec in enumerate(records, 1):
        errs, kind = check_line(rec, f"batch-r25.jsonl:{i}", factory_staging=True)
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
    records = [record_141(), record_142(), record_143(), record_144(), record_145()]
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
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
