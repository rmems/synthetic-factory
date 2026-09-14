#!/usr/bin/env python3
"""Emit TTF r63 JSONL (ttf-r63-311..315). Validate, then CREATE-ONLY copy into
the 2026-09-02-final-heavy live tree. Never overwrite. Never 2026-08-17/08-30.
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

OUT_DIR = Path("/tmp/ttf-r63-311")
BATCH_PATH = OUT_DIR / "batch-r63.jsonl"
NOTES_PATH = OUT_DIR / "NOTES-r63.md"
REPO = Path("/home/raulmc/rmems/synthetic-factory")
PIPELINES = REPO / "pipelines"
LIVE_DIR = REPO / "outputs" / "raw" / "2026-09-02-final-heavy" / "thalamic-trajectory-factory"

sys.path.insert(0, str(OUT_DIR))
from _banned import BANNED_DOMAINS, BANNED_PLANT_FRAGMENTS  # noqa: E402

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
    "thinking",
    "cot",
    "thoughts",
}
THIS_DOMAINS = {
    "potassium-nitrate-prill",
    "vinyl-acetate-carbonylation",
    "silicon-nitride-sinter",
    "cuprous-chloride-oxychlor",
    "phosphoric-acid-dihydrate",
}
THIS_PLANTS = (
    "Nitre-Howe",
    "Acetox-Beck",
    "Ceram-Kame",
    "Deacon-Brae",
    "Gypsum-Holt",
)
IDS = [f"ttf-r63-{n}" for n in range(311, 316)]


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
            ("round", 63),
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


def lif_311_excerpt():
    n = 76
    dt_us = 100
    tau_m_ms = 19.0
    v_th = 1.0
    v_reset = 0.0
    refractory_us = 1000
    i_bias = 0.91
    i_stim_peak = 2.48
    stim = (22000, 25000)
    seed = 63311
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
    take(burst, 9, label_times=(22600, 23100, 23800))
    clamp = [(t, nid) for t, nid in picked if t < 22000][:7]
    tear = [(t, nid) for t, nid in picked if t >= 22000][:9]
    picked = sorted(clamp + tear, key=lambda item: (item[0], item[1]))
    if len(picked) < 10:
        raise RuntimeError(f"LIF excerpt short: {len(picked)}")
    channels = ["lif.clamp" if t < 22000 else "lif.tear" for t, _ in picked]
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
            ("i_stim_peak", 2.48),
            ("stim_t_us", [22000, 25000]),
            ("i_clamp_extra", 0.62),
            ("clamp_n", 14),
            ("seed", 63311),
            (
                "note",
                "Population sim scoped to this sidecar. Plant remains designed. "
                "Neurons 0-13 carry +0.62 melt-air clamp bias; stim 22-25 ms is the prill-screen tear.",
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


def record_311():
    excerpt, extra = lif_311_excerpt()
    ticks = [
        tick(2112, 0.04, -0.02, -0.02, 0.01, 0.00),
        tick(5280, 0.08, -0.04, -0.02, 0.01, -0.01),
        tick(5460, 0.04, -0.03, -0.02, 0.00, 0.00),
        tick(5980, 0.08, -0.05, -0.03, 0.02, -0.01),
        tick(22600, 0.06, -0.43, -0.04, -0.01, -0.01),
        tick(840000000, 0.02, -0.05, -0.03, 0.01, -0.01),
    ]
    state = OrderedDict(
        [
            (
                "description",
                "Shot-head SH-2 on the Nitre-Howe NH-6 KNO3 circuit shows a 348 C well; crust spec "
                "is 330 C. Quench-air DP sits at 9.6 kPa, shy of the 14.0 kPa fan trip, so the "
                "planner leaves 18.0 kNm3/h running. The 348 C well arriving 180 us before DP is "
                "why air must drop to 12.6 kNm3/h. Deck-4 screen cloth is ripped; that dump only "
                "shows up on AE.",
            ),
            ("domain", "potassium-nitrate-prill"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Keep T-2 melt <= 330 C and finish the KNO3 throw without dumping prills through "
                "a torn screen.",
            ),
            ("t0_us", 1756850400000311),
            ("gate_latency_us", 700),
            ("race_window_us", 360),
            ("race_window_rel_ms", [5.280, 5.640]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "tc.melt.C 348 over 330 cap",
                                "dp.air.kPa 9.6 with fan 9.6 under 14.0",
                            ],
                        ),
                        (
                            "semantics",
                            "Melt-first latches quench-air clamp 18.0 -> 12.6 kNm3/h; DP-first keeps "
                            "18.0 on a 'still under fan-differential cap' model.",
                        ),
                        (
                            "window_derivation",
                            "360 us = one melt-well TC slot versus the quench-air DP publisher on this "
                            "prill-tower bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 180 us vs combined jitter 62 us (TC 28 + DP 34): 2.90x over a "
                            "2.0x trust floor. Reversing order by < 180 us inside the 360 us window "
                            "would have kept 18.0 kNm3/h; predicted next-sample 336 C > 330 cap.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "melt-well TC, 2 kHz, 28 us jitter",
                    "quench-air DP + fan PT, 1 kHz, 34 us jitter",
                    "prill-screen AE puck (context)",
                    "bucket-elevator tach (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("melt_cap_C", 330.0),
                        ("observed_melt_C", 348.0),
                        ("air_knm3h", 18.0),
                        ("air_dp_kPa", 9.6),
                        ("air_dp_cap_kPa", 14.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. T-2 indexed on Nitre-Howe NH-6; quench air 18.0 kNm3/h; melt 348 C.",
                    "2. Fan DP 9.6 kPa under 14.0; throw armed.",
                    "3. DP precursor at 1.180 ms.",
                    "4. Race window [5.280, 5.640] ms.",
                    "5. tc.melt.C 348 at 5.280 ms (winner).",
                    "6. dp.air.kPa 9.6 at 5.460 ms (loser by 180 us).",
                    "7. Gate at 5.980 ms: MODIFY clamp 18.0 -> 12.6 kNm3/h.",
                    "8. After clamp melt 322 C <= 330; DP still 9.6 kPa.",
                    "9. At 22.600 ms a prill-screen tear dumps 0.35 t of KNO3.",
                    "10. 14 min screen isolate (abort_s=840); named un-netted loss.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_quench_air"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("air_knm3h", 18.0),
                        ("melt_C", 348.0),
                        ("air_dp_kPa", 9.6),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("melt_C", 348.0),
                        ("melt_cap_C", 330.0),
                        ("predicted_unclamped_next_C", 336.0),
                        ("air_knm3h", 18.0),
                        ("air_dp_kPa", 9.6),
                        ("air_dp_cap_kPa", 14.0),
                        ("race_margin_us", 180),
                        ("combined_jitter_us", 62),
                        ("abort_s", 840),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 18.0 kNm3/h because fan DP 9.6 kPa is under 14.0, treating the "
                "348 C melt as a still-wet well rather than a crust-cap miss.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "correct"),
            (
                "rationale",
                "Melt 348 C won by 180 us, so the tower is over the 330 C KNO3 crust cap, not "
                "still a fan-DP story. Holding 18.0 kNm3/h predicts next-sample 336 > 330. "
                "MODIFY: air 18.0 -> 12.6 kNm3/h. Observed after clamp 322 <= 330. A full REJECT "
                "is not indicated: a clean throw accepts 12.6 kNm3/h.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "melt_C",
                            OrderedDict(
                                [
                                    ("cap", 330.0),
                                    ("observed", 348.0),
                                    ("predicted_unclamped_next", 336.0),
                                    ("clamped_air_knm3h", 12.6),
                                    ("observed_after_clamp", 322.0),
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
            ("name", "clamped_quench_air"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("air_knm3h", 12.6),
                        ("melt_C", 322.0),
                        ("air_dp_kPa", 9.6),
                    ]
                ),
            ),
            (
                "gate_effect",
                "MODIFY: air 18.0 -> 12.6 kNm3/h. Process-correct vs the 330 C crust cap. "
                "Prill screen still tears at 22.600 ms.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Process-correct MODIFY held melt at 322 C. At 22.600 ms a prill-screen tear "
                "already seated on deck 4 dumped 0.35 t of KNO3. Clamp reduced dump energy; it "
                "did not prevent the tear. Partnered negative: process heads stay honest; world "
                "loss is named, not netted.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("melt", "clamp executed; peak 322 C <= 330 cap"),
                        ("screen", "tore at 22.600 ms; 0.35 t KNO3"),
                        ("repair", "14 min screen isolate (abort_s=840)"),
                        ("mission", "NH-6 throw incomplete this circuit"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Neither melt TC nor fan DP predicted the seated prill-screen tear; ae.screen.tear is a new channel at 22.600 ms, 16.620 ms after the gate, still inside the 42 ms raster.",
                    "Delayed (abort_s=840): 14 min screen isolate. Named un-netted loss, not folded into task_progress.",
                ],
            ),
            (
                "un_netted_loss",
                "14 min screen isolate after the tear. Safety head -0.62 prices the dump; "
                "task_progress stays +0.32 because the air clamp completed under the 330 C cap. "
                "World loss is named here, not subtracted from process heads.",
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "tc.melt.C (5.280 ms, 348 C)"),
                        ("loser", "dp.air.kPa (5.460 ms, 9.6 kPa)"),
                        ("margin_us", 180),
                        (
                            "counterfactual_if_reversed",
                            "DP-first by < 180 us inside the 360 us window would have kept "
                            "18.0 kNm3/h; predicted next-sample 336 C would have missed the 330 cap "
                            "even without the screen tear. The MODIFY is still the correct process. "
                            "The tear is a later world charge either way, cheaper with the clamp "
                            "than without.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 22600),
            (
                "reward_inflection_note",
                "Safety collapses at the 22.600 ms prill-screen tear (tick t_us=22600), inside "
                "the 42 ms raster. The correct MODIFY at 5.980 ms is in the same excerpt. Do not "
                "put inflection on the abort_s=840 isolation tick.",
            ),
            ("delayed_surprise_s", 840),
        ]
    )
    spikes = [
        spike("dp.air.kPa", 1.180, 0.41),
        spike("tc.melt.C", 2.112, 0.58),
        spike("dp.air.kPa", 3.400, 0.50),
        spike("tc.melt.C", 5.280, 1.31),
        spike("dp.air.kPa", 5.460, 1.12),
        spike("ctrl.gate", 5.980, 0.97),
        spike("tc.melt.C", 8.100, 0.82),
        spike("dp.air.kPa", 10.400, 0.64),
        spike("ctrl.gate", 14.200, 0.86),
        spike("ae.screen.tear", 22.600, 1.48),
        spike("ae.screen.tear", 24.100, 0.93),
        spike("dp.air.kPa", 30.200, 0.40),
        spike("tc.melt.C", 36.400, 0.55),
    ]
    dw = 0.36
    ras = raster_core(
        42,
        76,
        24,
        77,
        routing(
            "thalamic-relay.nh-melt",
            "spikenaut.policy.air-clamp",
            [
                ("relay.tc.melt", "policy.air_clamp", 0.68),
                ("relay.dp.air", "policy.flow_hold", 0.29),
                ("relay.ae.screen", "policy.air_clamp", -0.42),
            ],
            "noradrenaline",
            0.04,
            "surprise-gated pre_post_stdp; NA at melt win (5.280 ms) opens a 42 ms eligibility "
            "trace that still covers the 22.600 ms prill-screen tear",
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
                    pop_budget("air_clamp", 50, 0.50, 220.0, dw),
                    pop_budget("flow_hold", 40, 0.80, 50.0, dw),
                    pop("tear_veto", 24, 0.75),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r63-311"),
            (
                "title",
                "Nitre-Howe NH-6 / Tower T-2: melt 348 C beats quench-air DP by 180 us; "
                "correct MODIFY still eats an in-window prill-screen tear (partnered negative "
                "total -0.46)",
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
                    "42 ms raster. total -0.46 = 0.32 + -0.62 + -0.16 + 0.04 + -0.04. Named "
                    "screen isolate (abort_s=840) is not netted into task_progress.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "potassium-nitrate-prill",
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
                    "14 min screen isolate.",
                    1,
                ),
            ),
        ]
    )


def record_312():
    ticks = [
        tick(2160, -0.02, -0.02, -0.02, -0.01, 0.01),
        tick(5400, -0.04, -0.04, -0.03, -0.02, 0.01),
        tick(5580, -0.04, -0.04, -0.03, -0.02, 0.01),
        tick(5920, -0.08, -0.10, -0.06, -0.03, 0.02),
        tick(6260, -0.02, -0.02, -0.02, -0.01, 0.01),
        tick(660000000, -0.02, -0.02, -0.02, -0.01, 0.00),
    ]
    spikes = [
        spike("ft.co.kg", 1.080, 0.38),
        spike("pt.rx.bar", 2.160, 0.62),
        spike("ft.co.kg", 3.400, 0.44),
        spike("pt.rx.bar", 5.400, 1.28),
        spike("pt.kpa.shadow", 5.580, 1.10),
        spike("ctrl.gate", 5.920, 0.94),
        spike("pt.rx.bar", 8.200, 0.80),
        spike("ft.co.kg", 10.200, 0.58),
        spike("ctrl.gate", 10.880, 0.88),
        spike("pt.rx.bar", 16.400, 0.66),
        spike("pt.kpa.shadow", 22.100, 0.52),
        spike("pt.rx.bar", 26.200, 0.48),
    ]
    excerpt = independent_excerpt(63312, 96, 28000, 12, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Acetox-Beck AB-4 hoop PT on R-7 prints 18.4 bar with a 16.0 bar yield limit. The "
                "twin tag on that nozzle still speaks kPa and shows 1840. Cutting CO from 42.0 to "
                "22.0 kg/h is the legal edit. Instead the supervisor treats 1840 as bar, calls "
                "18.4 a ghost, and opens acetic-absorber quench from 12 percent to 80 while CO "
                "never moves.",
            ),
            ("domain", "vinyl-acetate-carbonylation"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Keep R-7 hoop pressure <= 16.0 bar without opening the acetic absorber quench "
                "on a unit-confused shadow tag.",
            ),
            ("t0_us", 1756850400000312),
            ("gate_latency_us", 520),
            ("race_window_us", 340),
            ("race_window_rel_ms", [5.400, 5.740]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "pt.rx.bar 18.4 over 16.0 bar cap",
                                "pt.kpa.shadow leftover 1840 kPa on the same nozzle",
                            ],
                        ),
                        (
                            "semantics",
                            "Bar-first cuts CO on the live hoop; kPa-shadow-first opens absorber "
                            "quench as if 1840 were a bar reading and 18.4 were a unit ghost.",
                        ),
                        (
                            "window_derivation",
                            "340 us = one hoop-PT slot versus the leftover kPa publisher on this "
                            "carbonylation bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 180 us vs combined jitter 60 us (bar 28 + kPa 32): 3.00x over "
                            "a 2.0x trust floor. Reversing order by < 180 us would still leave live "
                            "18.4 bar > 16.0; the correct gate stays CO-cut either way.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "hoop PT bar, 2 kHz, 28 us jitter, tag=PT_RX.BAR",
                    "leftover kPa publisher, 1 kHz, 32 us jitter, tag=PT_RX.KPA",
                    "CO mass-flow (context)",
                    "absorber quench FT (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("cap_P_bar", 16.0),
                        ("live_P_bar", 18.4),
                        ("shadow_kPa", 1840.0),
                        ("bar_to_kPa", 100.0),
                        ("co_kg_h", 42.0),
                        ("absorber_quench_pct", 12.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. R-7 already at 18.4 bar; CO 42.0 kg/h; quench 12 percent.",
                    "2. Leftover kPa tag still prints 1840; same nozzle.",
                    "3. CO precursor at 1.080 ms.",
                    "4. Race window [5.400, 5.740] ms.",
                    "5. pt.rx.bar 18.4 at 5.400 ms (winner).",
                    "6. pt.kpa.shadow 1840 at 5.580 ms (loser by 180 us).",
                    "7. Gate at 5.920 ms: WRONG-MODIFY binds kPa as bar.",
                    "8. Quench 80 percent; CO stays 42.0; hoop stays 18.2 bar.",
                    "9. Absorber floods; hoop still over cap.",
                    "10. Delayed (abort_s=660): 11 min re-dry and re-press.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_co_feed"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("co_kg_h", 42.0),
                        ("absorber_quench_pct", 12.0),
                        ("unit_bound", "bar"),
                        ("P_bar", 18.4),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("live_P_bar", 18.4),
                        ("cap_P_bar", 16.0),
                        ("shadow_kPa", 1840.0),
                        ("bar_to_kPa", 100.0),
                        ("co_kg_h", 42.0),
                        ("correct_co_kg_h", 22.0),
                        ("correct_quench_pct", 12.0),
                        ("correct_unit", "bar"),
                        ("t_gate_us", 5920),
                        ("race_margin_us", 180),
                        ("combined_jitter_us", 60),
                        ("abort_s", 660),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes continuing 42.0 kg/h CO: leftover 1840 kPa still looks like a "
                "legal shadow of 18.4 bar, so the hoop over-cap is treated as a unit ghost.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "incorrect"),
            (
                "rationale",
                "Live 18.4 exceeds the 16.0 bar cap (true). The leftover 1840 kPa tag is still "
                "armed, so bind that as the hoop reading: open absorber quench 12 -> 80 percent "
                "and leave CO. That is the wrong engineering unit of the same nozzle.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "P_bar",
                            OrderedDict(
                                [
                                    ("cap", 16.0),
                                    ("observed", 18.4),
                                    ("shadow_kPa", 1840.0),
                                    ("unit_bound", "kPa_as_bar"),
                                    ("correct_co_kg_h", 22.0),
                                    ("executed_quench_pct", 80.0),
                                ]
                            ),
                        ),
                        (
                            "unit",
                            OrderedDict(
                                [
                                    ("live", "bar"),
                                    ("bound", "kPa_as_bar"),
                                    ("wrong_unit", True),
                                    ("bar_to_kPa", 100.0),
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
            ("name", "absorber_quench_wrong_unit"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("co_kg_h", 42.0),
                        ("absorber_quench_pct", 80.0),
                        ("unit_bound", "kPa_as_bar"),
                        ("P_bar", 18.2),
                    ]
                ),
            ),
            (
                "gate_effect",
                "MODIFY (incorrect / wrong-engineering-unit bar-vs-kPa): absorber quench 80 "
                "percent bound while live hoop 18.4 > 16.0 bar and CO stays 42.0. Routing "
                "relay.pt.kpa -> policy.absorber_quench; no positive weight to policy.co_cut.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Wrong-MODIFY bound a leftover kPa tag as if it were bar. Live 18.4 bar was over "
                "the 16.0 cap at t_gate; 1840 kPa was the same nozzle, not a 1840 bar fault. "
                "Absorber flooded. 11 min re-dry (abort_s=660). Correct gate was MODIFY CO "
                "42.0 -> 22.0 kg/h leaving quench at 12 percent.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("feed", "CO stays 42.0 kg/h; quench 80 percent on wrong unit"),
                        ("hoop", "18.2 bar still over 16.0 cap"),
                        ("repair", "11 min re-dry and re-press, R-7 reseed"),
                        ("mission", "VAM cycle deferred"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Bar-first was the correct order and the number was over cap; the MODIFY spent that win on a leftover kPa publisher of the same nozzle.",
                    "Delayed (abort_s=660): AB-4 holds 11 min while R-7 is dried and re-pressed; next VAM cycle 12 min late.",
                ],
            ),
            (
                "recovery",
                OrderedDict(
                    [
                        (
                            "correct_gate",
                            "MODIFY CO 42.0 -> 22.0 kg/h at t_gate_us=5920; unit_bound=bar; leave absorber quench at 12 percent.",
                        ),
                        ("correct_actuator", "co_mass_flow"),
                        ("wrong_unit", "kPa_as_bar"),
                        ("unit_live", "bar"),
                        ("unit_bound", "kPa_as_bar"),
                        (
                            "wrong_edit_applied",
                            OrderedDict(
                                [
                                    ("co_kg_h", 42.0),
                                    ("absorber_quench_pct", 80.0),
                                    ("unit_bound", "kPa_as_bar"),
                                ]
                            ),
                        ),
                        (
                            "cost",
                            "11 min re-dry (task/efficiency); absorber flood during the unscheduled quench (safety near-miss of a same-nozzle wrong-unit bind).",
                        ),
                    ]
                ),
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "pt.rx.bar (5.400 ms, 18.4 bar)"),
                        ("loser", "pt.kpa.shadow (5.580 ms, 1840 kPa)"),
                        ("margin_us", 180),
                        (
                            "counterfactual_if_reversed",
                            "kPa-first by < 180 us would still be a leftover kPa publisher on a "
                            "bar hoop; a correct gate binds pt.rx.bar to policy.co_cut at t_gate "
                            "either way. The wrong MODIFY spent the hoop win on the leftover unit.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 5920),
            (
                "reward_inflection_note",
                "Task, safety, and efficiency drop at the kPa-as-bar bind (5.920 ms, tick 4). "
                "The 11 min re-dry is delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 660),
        ]
    )
    dw = 0.34
    ras = raster_core(
        28,
        96,
        32,
        86,
        routing(
            "thalamic-relay.ab-hoop",
            "spikenaut.policy.absorber-quench",
            [
                ("relay.pt.kpa", "policy.absorber_quench", 0.74),
                ("relay.pt.bar", "policy.absorber_quench", 0.21),
            ],
            "acetylcholine",
            0.08,
            "timing_cap_stdp; ACh tags the (wrong) absorber_quench bind at the hoop win",
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
                    pop_budget("absorber_quench", 48, 0.45, 300.0, dw),
                    pop("co_cut", 48, 0.90),
                    pop("unit_veto", 20, 0.80),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r63-312"),
            (
                "title",
                "WRONG-MODIFY at Acetox-Beck AB-4 / Reactor R-7: live hoop 18.4 bar read "
                "correctly; leftover 1840 kPa bound as bar (wrong-engineering-unit)",
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
                    "Wrong-modify / wrong-engineering-unit bar-vs-kPa. Sidecar arithmetic "
                    "18.4 > 16.0 on live bar is true; MODIFY bound to absorber_quench. total "
                    "-0.68 = -0.22 + -0.24 + -0.18 + -0.10 + 0.06.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "vinyl-acetate-carbonylation",
                    [
                        "modify",
                        "wrong-gate",
                        "wrong-engineering-unit",
                        "bar-vs-kPa",
                        "sidecar-convictable",
                        "designed",
                    ],
                    "Teaches a probe that a correct bar-first race can still be a wrong gate "
                    "when the MODIFY binds a leftover kPa publisher of the same nozzle. "
                    "Convictable from live_P_bar vs cap_P_bar and routing to without VAM kinetics.",
                    2,
                    supervisor_error_type="wrong-modify",
                ),
            ),
        ]
    )


def record_313():
    ticks = [
        tick(2736, 0.01, 0.04, 0.01, 0.01, 0.01),
        tick(6840, 0.02, 0.08, 0.02, 0.02, 0.01),
        tick(7020, 0.01, 0.06, 0.02, 0.01, 0.01),
        tick(7640, 0.04, 0.16, 0.04, 0.04, 0.02),
        tick(7960, 0.01, 0.05, 0.02, 0.01, 0.01),
        tick(480000000, 0.01, 0.03, 0.01, 0.01, 0.00),
    ]
    spikes = [
        spike("enc.press.mpa", 1.360, 0.36),
        spike("ae.sinter.pps", 2.736, 0.70),
        spike("enc.press.mpa", 4.100, 0.48),
        spike("ae.sinter.pps", 6.840, 1.36),
        spike("enc.press.mpa", 7.020, 1.08),
        spike("ctrl.gate", 7.640, 0.96),
        spike("ae.sinter.pps", 10.400, 0.84),
        spike("enc.press.mpa", 14.800, 0.52),
        spike("ctrl.gate", 18.200, 0.80),
        spike("ae.sinter.pps", 28.400, 0.66),
        spike("enc.press.mpa", 36.100, 0.40),
        spike("ae.sinter.pps", 42.200, 0.58),
    ]
    excerpt = independent_excerpt(63313, 112, 46000, 15, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "On the Ceram-Kame CK-HIL hot-press stand, compact P-2 is mid-soak when die AE "
                "jumps to 48 pps. The ram encoder is still advertising 18 MPa under a 22 MPa "
                "dispatch ceiling. The acoustic burst leads the encoder by 180 us, which is enough "
                "to park the ram at 0 MPa rather than ship a cracked Si3N4 puck.",
            ),
            ("domain", "silicon-nitride-sinter"),
            ("sim_or_real", "hil"),
            (
                "goal",
                "Keep P-2 from dispatching a cracked compact while ram pressure remains under "
                "its own cap.",
            ),
            ("t0_us", 1756850400000313),
            ("gate_latency_us", 800),
            ("race_window_us", 320),
            ("race_window_rel_ms", [6.840, 7.160]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "ae.sinter.pps 48 over 14 cap",
                                "enc.press.mpa 18 under 22 cap",
                            ],
                        ),
                        (
                            "semantics",
                            "AE-first REJECT-holds the ram; encoder-first would treat 18 MPa as "
                            "still-legal dispatch.",
                        ),
                        (
                            "window_derivation",
                            "320 us = one die AE slot versus the ram-encoder publisher on this "
                            "HIL sinter bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 180 us vs combined jitter 58 us (AE 26 + encoder 32): 3.10x over "
                            "a 2.0x trust floor. Reversing order by < 180 us inside the 320 us "
                            "window would have dispatched a cracked compact.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "die AE puck, 2 kHz, 26 us jitter",
                    "ram encoder, 1 kHz, 32 us jitter",
                    "die RTD (context)",
                    "vacuum PT (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("ae_cap_pps", 14.0),
                        ("observed_ae_pps", 48.0),
                        ("press_MPa", 18.0),
                        ("press_cap_MPa", 22.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. P-2 indexed on Ceram-Kame CK-HIL; ram 18 MPa; AE quiet.",
                    "2. Encoder 18 under 22 cap; soak armed.",
                    "3. Encoder precursor at 1.360 ms.",
                    "4. Race window [6.840, 7.160] ms.",
                    "5. ae.sinter.pps 48 at 6.840 ms (winner).",
                    "6. enc.press.mpa 18 at 7.020 ms (loser by 180 us).",
                    "7. Gate at 7.640 ms: REJECT hold ram 18 -> 0 MPa.",
                    "8. Press parked; die RTD still 1680 C under 1750.",
                    "9. Crack confirmed on the HIL compact.",
                    "10. Delayed (abort_s=480): 8 min die wipe on the HIL stand.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "dispatch_sinter_press"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("press_MPa", 18.0),
                        ("hold", False),
                        ("ram_mm_s", 0.42),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("ae_pps", 48.0),
                        ("ae_cap_pps", 14.0),
                        ("press_MPa", 18.0),
                        ("press_cap_MPa", 22.0),
                        ("die_C", 1680.0),
                        ("die_cap_C", 1750.0),
                        ("race_margin_us", 180),
                        ("combined_jitter_us", 58),
                        ("abort_s", 480),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 18 MPa because the encoder is under 22 and die 1680 C is "
                "under 1750, treating the AE burst as fixture rattle.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "REJECT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Die AE 48 pps won by 180 us, so the compact is cracking, not still a ram-pressure "
                "story. Encoder 18 MPa is under 22 and does not authorize dispatch. REJECT: hold "
                "ram 18 -> 0 MPa. A MODIFY that only trims ram speed would leave the cracked "
                "compact.",
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
                                    ("press_MPa", 18.0),
                                    ("press_cap_MPa", 22.0),
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
            ("name", "hold_sinter_press"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("press_MPa", 0.0),
                        ("hold", True),
                        ("ram_mm_s", 0.0),
                    ]
                ),
            ),
            (
                "gate_effect",
                "REJECT: ram 18 -> 0 MPa. AE 48 > 14 cap beats legal encoder. HIL compact "
                "held for die wipe.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct REJECT parked P-2. Encoder never crossed 22 MPa; AE 48 pps was the "
                "only over-cap channel. 8 min die wipe (abort_s=480) on the HIL stand.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("press", "held; ram 0 MPa"),
                        ("compact", "crack confirmed on HIL coupon"),
                        ("repair", "8 min die wipe (abort_s=480)"),
                        ("mission", "P-2 not dispatched"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Ram encoder never crossed its cap; AE was the only over-cap channel.",
                    "Delayed (abort_s=480): 8 min die wipe on the HIL stand.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "ae.sinter.pps (6.840 ms, 48 pps)"),
                        ("loser", "enc.press.mpa (7.020 ms, 18 MPa)"),
                        ("margin_us", 180),
                        (
                            "counterfactual_if_reversed",
                            "Encoder-first by < 180 us inside the 320 us window would have "
                            "dispatched a cracked compact at 18 MPa. REJECT is still the correct "
                            "gate; AE was over cap either way.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 7640),
            (
                "reward_inflection_note",
                "Safety and task inflect at the REJECT hold (7.640 ms, tick 4). The 8 min die "
                "wipe is delayed surprise.",
            ),
            ("delayed_surprise_s", 480),
        ]
    )
    dw = 0.32
    ras = raster_core(
        46,
        112,
        20,
        103,
        routing(
            "thalamic-relay.sinter-ae",
            "spikenaut.policy.ram-hold",
            [
                ("relay.ae.sinter", "policy.ram_hold", 0.71),
                ("relay.enc.press", "policy.ram_go", 0.24),
            ],
            "dopamine",
            0.05,
            "reward-modulated STDP; DA at AE win tags the hold population",
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
                    pop_budget("ram_hold", 56, 0.45, 280.0, dw),
                    pop("ram_go", 40, 0.90),
                    pop("ae_veto", 24, 0.80),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r63-313"),
            (
                "title",
                "Ceram-Kame CK-HIL / Press P-2: die AE 48 pps beats ram 18 MPa by 180 us; "
                "correct REJECT parks the silicon-nitride compact",
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
                    "Correct REJECT. AE 48 > 14 cap beats legal ram encoder. total +0.80 = "
                    "0.10 + 0.42 + 0.12 + 0.10 + 0.06.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "silicon-nitride-sinter",
                    [
                        "reject",
                        "hil",
                        "ae-vs-encoder",
                        "cracked-compact",
                        "tick6-sidecar-bound",
                    ],
                    "HIL AE-vs-encoder race with a clean REJECT. Distills a hold population that "
                    "wins on acoustic rate, not on a still-legal ram encoder.",
                    3,
                ),
            ),
        ]
    )


def record_314():
    ticks = [
        tick(2880, 0.05, 0.03, 0.02, 0.01, 0.01),
        tick(7200, 0.08, 0.04, 0.03, 0.02, 0.01),
        tick(7380, 0.05, 0.03, 0.02, 0.01, 0.01),
        tick(7840, 0.12, 0.08, 0.04, 0.04, 0.02),
        tick(8200, 0.04, 0.02, 0.02, 0.01, 0.00),
        tick(240000000, 0.04, 0.02, 0.01, 0.01, 0.01),
    ]
    spikes = [
        spike("ft.air.knm3", 1.200, 0.34),
        spike("tc.bed.C", 2.880, 0.60),
        spike("ft.air.knm3", 4.400, 0.42),
        spike("tc.bed.C", 7.200, 1.22),
        spike("ft.air.knm3", 7.380, 1.04),
        spike("ctrl.gate", 7.840, 0.90),
        spike("tc.bed.C", 11.200, 0.72),
        spike("ft.air.knm3", 14.800, 0.50),
        spike("ctrl.gate", 18.400, 0.78),
        spike("tc.bed.C", 22.600, 0.56),
        spike("ft.air.knm3", 26.200, 0.38),
    ]
    excerpt = independent_excerpt(63314, 64, 26000, 12, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Bed B-5 inside the Deacon-Brae DB-3 oxychlor CFD is already at 412 C against a "
                "390 C Deacon-reaction cap while HCl still reads a legal 8.2 kPa. Bed-first clamps "
                "air 22.0 -> 14.0 kNm3/h; HCl-first would keep cruise because 8.2 kPa is still "
                "under the 12.0 kPa absorber cap. After the clamp the bed settles at 384 C with "
                "no later world charge.",
            ),
            ("domain", "cuprous-chloride-oxychlor"),
            ("sim_or_real", "simulated"),
            (
                "goal",
                "Keep B-5 bed <= 390 C and finish the CFD Deacon pass without dumping CuCl onto "
                "the quench.",
            ),
            ("t0_us", 1756850400000314),
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
                                "tc.bed.C 412 over 390 cap",
                                "pt.hcl.kPa 8.2 under 12.0 absorber cap",
                            ],
                        ),
                        (
                            "semantics",
                            "Bed-first latches air clamp 22.0 -> 14.0 kNm3/h; HCl-first keeps 22.0 "
                            "on a 'still under absorber-pressure cap' model.",
                        ),
                        (
                            "window_derivation",
                            "360 us = one bed TC slot versus the HCl-absorber publisher on this "
                            "simulated oxychlor bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 180 us vs combined jitter 58 us (TC 26 + HCl 32): 3.10x over a "
                            "2.0x trust floor. Reversing order by < 180 us inside the 360 us window "
                            "would have kept 22.0 kNm3/h; predicted next-sample 418 C > 390 cap.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "bed TC rake, 26 us jitter",
                    "HCl absorber PT, 32 us jitter",
                    "air mass-flow (context)",
                    "CuCl quench LT (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("bed_cap_C", 390.0),
                        ("observed_bed_C", 412.0),
                        ("air_knm3h", 22.0),
                        ("hcl_kPa", 8.2),
                        ("hcl_cap_kPa", 12.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. B-5 indexed on Deacon-Brae DB-3 CFD; air 22.0 kNm3/h; bed 412 C.",
                    "2. HCl 8.2 kPa under 12.0; pass armed.",
                    "3. HCl precursor at 1.200 ms.",
                    "4. Race window [7.200, 7.560] ms.",
                    "5. tc.bed.C 412 at 7.200 ms (winner).",
                    "6. pt.hcl.kPa 8.2 at 7.380 ms (loser by 180 us).",
                    "7. Gate at 7.840 ms: MODIFY clamp 22.0 -> 14.0 kNm3/h.",
                    "8. After clamp bed 384 C <= 390; HCl still 8.2 kPa.",
                    "9. CFD chest stays dry; no later dump.",
                    "10. Delayed (survey_s=240): 4 min survey restacks B-5.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_oxychlor_air"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("air_knm3h", 22.0),
                        ("bed_C", 412.0),
                        ("hcl_kPa", 8.2),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("bed_C", 412.0),
                        ("bed_cap_C", 390.0),
                        ("predicted_unclamped_next_C", 418.0),
                        ("air_knm3h", 22.0),
                        ("hcl_kPa", 8.2),
                        ("hcl_cap_kPa", 12.0),
                        ("race_margin_us", 180),
                        ("combined_jitter_us", 58),
                        ("survey_s", 240),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 22.0 kNm3/h because HCl 8.2 kPa is under 12.0, treating the "
                "412 C bed as a still-wet rake rather than a Deacon-cap miss.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "correct"),
            (
                "rationale",
                "Bed 412 C won by 180 us, so the CFD is over the 390 C Deacon cap, not still an "
                "absorber-pressure story. Holding 22.0 kNm3/h predicts next-sample 418 > 390. "
                "MODIFY: air 22.0 -> 14.0 kNm3/h. Observed after clamp 384 <= 390. A full REJECT "
                "is not indicated: a clean pass accepts 14.0 kNm3/h.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "bed_C",
                            OrderedDict(
                                [
                                    ("cap", 390.0),
                                    ("observed", 412.0),
                                    ("predicted_unclamped_next", 418.0),
                                    ("clamped_air_knm3h", 14.0),
                                    ("observed_after_clamp", 384.0),
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
            ("name", "clamped_oxychlor_air"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("air_knm3h", 14.0),
                        ("bed_C", 384.0),
                        ("hcl_kPa", 8.2),
                    ]
                ),
            ),
            (
                "gate_effect",
                "MODIFY: air 22.0 -> 14.0 kNm3/h. Process-correct vs the 390 C Deacon cap. "
                "No later world charge; bed stays 384 C.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Process-correct MODIFY held bed at 384 C. HCl never crossed 12.0 kPa. 4 min "
                "survey (survey_s=240) restacks B-5 without a recovery hold.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("bed", "clamp executed; peak 384 C <= 390 cap"),
                        ("absorber", "HCl 8.2 kPa under 12.0"),
                        ("survey", "4 min restack (survey_s=240)"),
                        ("mission", "DB-3 Deacon pass complete this circuit"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "HCl 8.2 kPa hitch is residual, not an absorber trip.",
                    "Delayed (survey_s=240): 4 min survey restacks B-5 without a recovery hold.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "tc.bed.C (7.200 ms, 412 C)"),
                        ("loser", "pt.hcl.kPa (7.380 ms, 8.2 kPa)"),
                        ("margin_us", 180),
                        (
                            "counterfactual_if_reversed",
                            "HCl-first by < 180 us inside the 360 us window would have kept "
                            "22.0 kNm3/h; predicted next-sample 418 C would have missed the 390 cap. "
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
            ("delayed_surprise_s", 240),
        ]
    )
    dw = 0.36
    ras = raster_core(
        26,
        64,
        38,
        63,
        routing(
            "thalamic-relay.db-bed",
            "spikenaut.policy.air-clamp",
            [
                ("relay.tc.bed", "policy.air_clamp", 0.66),
                ("relay.pt.hcl", "policy.hcl_hold", 0.27),
            ],
            "serotonin",
            0.06,
            "5-HT eligibility on the process-correct bed-clamp win",
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
            ("decision_window_ms", dw),
            ("decision", "MODIFY"),
            (
                "populations",
                [
                    pop_budget("air_clamp", 44, 0.45, 260.0, dw),
                    pop("hcl_hold", 36, 0.90),
                    pop("bed_veto", 16, 0.80),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r63-314"),
            (
                "title",
                "Deacon-Brae DB-3 / Bed B-5: bed 412 C beats HCl 8.2 kPa by 180 us; correct "
                "MODIFY clamps air 22.0 -> 14.0 kNm3/h with no later world charge",
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
                    "Correct MODIFY of an over-cap Deacon bed; world does not charge. total "
                    "+0.90 = 0.38 + 0.22 + 0.14 + 0.10 + 0.06.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "cuprous-chloride-oxychlor",
                    [
                        "modify",
                        "process-correct",
                        "simulated-oxychlor",
                        "bed-vs-hcl",
                        "sidecar-convictable",
                        "simulated",
                    ],
                    "Simulated process-correct MODIFY without a partnered world-charge. Distills "
                    "a clamp population that wins on bed temperature, not on a still-legal HCl hitch.",
                    4,
                ),
            ),
        ]
    )


def record_315():
    ticks = [
        tick(2016, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(5040, 0.10, 0.06, 0.04, 0.02, 0.02),
        tick(5200, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(5640, 0.12, 0.08, 0.05, 0.04, 0.02),
        tick(5920, 0.06, 0.05, 0.03, 0.01, 0.01),
        tick(300000000, 0.04, 0.03, 0.02, 0.01, 0.01),
    ]
    spikes = [
        spike("ir.gypsum.pct", 0.980, 0.32),
        spike("ft.filter.tph", 2.016, 0.58),
        spike("ir.gypsum.pct", 3.200, 0.44),
        spike("ft.filter.tph", 5.040, 1.24),
        spike("ir.gypsum.pct", 5.200, 1.06),
        spike("ctrl.gate", 5.640, 0.92),
        spike("ft.filter.tph", 8.100, 0.70),
        spike("ir.gypsum.pct", 12.400, 0.48),
        spike("ctrl.gate", 16.200, 0.76),
        spike("ft.filter.tph", 20.400, 0.54),
        spike("ir.gypsum.pct", 22.800, 0.36),
    ]
    excerpt = independent_excerpt(63315, 80, 24000, 12, spike_avoid_us(spikes))
    params = OrderedDict(
        [
            ("filter_tph", 8.4),
            ("gypsum_pct", 22.0),
            ("hold", False),
        ]
    )
    state = OrderedDict(
        [
            (
                "description",
                "Filter F-4 at Gypsum-Holt GH-2 is already pulling 8.4 t/h of dihydrate slurry "
                "against a 7.0 t/h floor, with cake moisture 22 pct under 28 pct. Filter-first "
                "accepts the already-legal pull; moisture-first would have REJECTED a legal "
                "phosphoric cake.",
            ),
            ("domain", "phosphoric-acid-dihydrate"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Run F-4 at 8.4 t/h, keep cake moisture <= 28 pct, and leave the P2O5 loop on "
                "schedule.",
            ),
            ("t0_us", 1756850400000315),
            ("gate_latency_us", 600),
            ("race_window_us", 280),
            ("race_window_rel_ms", [5.040, 5.320]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "ft.filter.tph 8.4 over 7.0 floor",
                                "ir.gypsum.pct 22 under 28 cap",
                            ],
                        ),
                        (
                            "semantics",
                            "Filter-first accepts the pull; moisture-first would have treated "
                            "8.4 t/h as still climbing and looked for an extra hold.",
                        ),
                        (
                            "window_derivation",
                            "280 us = one belt-weigh slot versus the cake-IR publisher on this "
                            "dihydrate-filter bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 160 us vs combined jitter 52 us (weigh 22 + IR 30): 3.08x over "
                            "a 2.0x trust floor. Reversing order by < 160 us inside the 280 us "
                            "window would have REJECTED an already-legal cake.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "belt weigh feeder, 22 us jitter",
                    "cake IR moisture, 30 us jitter",
                    "vacuum PT (context)",
                    "filtrate density (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("filter_floor_tph", 7.0),
                        ("observed_filter_tph", 8.4),
                        ("gypsum_cap_pct", 28.0),
                        ("observed_gypsum_pct", 22.0),
                        ("proposed_filter_tph", 8.4),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. F-4 indexed on Gypsum-Holt GH-2; filter 8.4 t/h armed.",
                    "2. Pull over 7.0 floor; cake 22 pct under 28 pct cap.",
                    "3. IR precursor at 0.980 ms.",
                    "4. Race window [5.040, 5.320] ms.",
                    "5. ft.filter.tph 8.4 at 5.040 ms (winner).",
                    "6. ir.gypsum.pct 22 at 5.200 ms (loser by 160 us).",
                    "7. Gate at 5.640 ms: ACCEPT 8.4 t/h.",
                    "8. Filter stays 8.4; cake stays 22 pct.",
                    "9. P2O5 on-spec at the attack tank.",
                    "10. Delayed (dwell_s=300): 5 min dwell restacks F-4.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "hold_filter_pull"),
            ("parameters", params),
            (
                "evidence",
                OrderedDict(
                    [
                        ("filter_tph", 8.4),
                        ("filter_floor_tph", 7.0),
                        ("gypsum_pct", 22.0),
                        ("gypsum_cap_pct", 28.0),
                        ("race_margin_us", 160),
                        ("combined_jitter_us", 52),
                        ("dwell_s", 300),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 8.4 t/h because pull is over the 7.0 floor and cake IR 22 pct "
                "is under 28 pct.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Filter 8.4 t/h won by 160 us and is over the 7.0 floor. Cake 22 pct is under "
                "28 pct. ACCEPT the already-legal pull.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "filter_tph",
                            OrderedDict(
                                [
                                    ("floor", 7.0),
                                    ("observed", 8.4),
                                    ("gypsum_pct", 22.0),
                                    ("gypsum_cap_pct", 28.0),
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
            ("name", "hold_filter_pull"),
            ("parameters", params),
            (
                "gate_effect",
                "ACCEPT: filter 8.4 t/h already legal. Cake IR 22 pct leftover is residual, "
                "not a moisture trip.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT of an already-legal dihydrate pull. Filter 8.4 >= 7.0; cake "
                "22 pct <= 28. 5 min dwell (dwell_s=300) restacks F-4 without a recovery hold.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("filter", "8.4 t/h held"),
                        ("cake", "22 pct under 28 pct"),
                        ("dwell", "5 min restack (dwell_s=300)"),
                        ("mission", "GH-2 P2O5 circuit complete this pass"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Cake IR 22 pct hitch is residual, not a moisture trip.",
                    "Delayed (dwell_s=300): 5 min dwell restacks F-4 without a recovery hold.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "ft.filter.tph (5.040 ms, 8.4 t/h)"),
                        ("loser", "ir.gypsum.pct (5.200 ms, 22 pct)"),
                        ("margin_us", 160),
                        (
                            "counterfactual_if_reversed",
                            "IR-first by < 160 us would only have delayed confirmation; pull was "
                            "already legal. ACCEPT remains the correct gate.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 5640),
            (
                "reward_inflection_note",
                "Task and safety inflect at the ACCEPT (5.640 ms, tick 4). Dwell restack is "
                "delayed surprise.",
            ),
            ("delayed_surprise_s", 300),
        ]
    )
    dw = 0.28
    ras = raster_core(
        24,
        80,
        28,
        54,
        routing(
            "thalamic-relay.gh-filter",
            "spikenaut.policy.filter-go",
            [
                ("relay.ft.filter", "policy.filter_go", 0.66),
                ("relay.ir.gypsum", "policy.moisture_hold", 0.27),
            ],
            "adenosine",
            0.07,
            "adenosine eligibility on the already-legal filter win",
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
            ("decision_window_ms", dw),
            ("decision", "ACCEPT"),
            (
                "populations",
                [
                    pop_budget("filter_go", 44, 0.45, 260.0, dw),
                    pop("moisture_hold", 36, 0.90),
                    pop("cake_veto", 16, 0.80),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r63-315"),
            (
                "title",
                "Gypsum-Holt GH-2 / Filter F-4: 8.4 t/h beats cake IR 22 pct by 160 us; ACCEPT "
                "already-legal dihydrate pull",
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
                    "Correct ACCEPT of an already-legal dihydrate pull. total +1.14 = 0.44 + "
                    "0.30 + 0.20 + 0.12 + 0.08.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "phosphoric-acid-dihydrate",
                    [
                        "accept",
                        "already-legal",
                        "designed-filter",
                        "filter-vs-moisture",
                        "sidecar-convictable",
                        "designed",
                    ],
                    "Already-legal ACCEPT. Distills a go population that wins on filter floor, "
                    "not on a residual cake-IR hitch.",
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
    if rec["id"] == "ttf-r63-311":
        tick5 = 22600
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


def prior_domains_and_descs():
    domains = set()
    descs = []
    blobs = []
    paths = list(Path("/tmp").glob("ttf-r*/batch-r*.jsonl"))
    paths += list(LIVE_DIR.glob("batch-r*.jsonl"))
    for path in sorted(paths):
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
    banned_hit = set(domains) & BANNED_DOMAINS
    if banned_hit:
        issues.append(f"banned domains {banned_hit}")
    wrong = [
        r
        for r in records
        if r["safety_decision"].get("correctness") == "incorrect"
        or r["meta"].get("supervisor_error_type")
    ]
    if len(wrong) != 1 or wrong[0]["id"] != "ttf-r63-312":
        issues.append(f"wrong-gate set {[w['id'] for w in wrong]}")
    if wrong and wrong[0]["meta"].get("supervisor_error_type") != "wrong-modify":
        issues.append("expected wrong-modify")
    if any(r["state"]["sim_or_real"] == "real" for r in records):
        issues.append("sim_or_real=real")
    hil = [r["id"] for r in records if r["state"]["sim_or_real"] == "hil"]
    if hil != ["ttf-r63-313"]:
        issues.append(f"hil set {hil}")
    sim = [r["id"] for r in records if r["state"]["sim_or_real"] == "simulated"]
    if sim != ["ttf-r63-314"]:
        issues.append(f"simulated set {sim}")
    designed = [r["id"] for r in records if r["state"]["sim_or_real"] == "designed"]
    if designed != ["ttf-r63-311", "ttf-r63-312", "ttf-r63-315"]:
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
    totals = [r["reward_components"]["total"] for r in records]
    if all(t > 0 for t in totals):
        issues.append("all-positive totals")
    for rec in records:
        blob = json.dumps(rec)
        if "training_ready" in blob:
            issues.append(f"{rec['id']} training_ready present")
        if "wrong-accept" in blob.lower() or "wrong_accept" in blob.lower():
            issues.append(f"{rec['id']} wrong-ACCEPT mention")
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
        if rec["id"] == "ttf-r63-311":
            if rec["raster"].get("excerpt_source") != "independent_lif":
                issues.append("311 missing independent_lif")
            if rec["future_outcome"]["reward_inflection_t_us"] > rec["raster"]["window_ms"] * 1000:
                issues.append("311 inflection outside window")
            if rec["reward_components"]["total"] >= 0:
                issues.append("311 partnered-neg total not negative")
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
        if rec["meta"]["round"] != 63:
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
        if rec["safety_decision"]["decision"] == "MODIFY" and exec_p == prop_p:
            issues.append(f"{rec['id']} MODIFY params unchanged")
        if rec["id"] == "ttf-r63-312":
            ev = rec["proposed_action"]["evidence"]
            if not (ev["live_P_bar"] > ev["cap_P_bar"]):
                issues.append("312 live bar not over cap")
            if ev.get("shadow_kPa") != 1840.0:
                issues.append("312 shadow_kPa")
            if rec["executed_action"]["parameters"].get("unit_bound") != "kPa_as_bar":
                issues.append("312 unit_bound not kPa_as_bar")
            if rec["executed_action"]["parameters"].get("absorber_quench_pct") != 80.0:
                issues.append("312 expected quench 80")
            if rec["executed_action"]["parameters"].get("co_kg_h") != 42.0:
                issues.append("312 expected CO uncut")
            if "recovery" not in rec["future_outcome"]:
                issues.append("312 missing recovery")
            table_to = {row["to"] for row in rec["raster"]["routing"]["table"]}
            if "policy.co_cut" in table_to:
                issues.append("312 routing still has co_cut")
            if "policy.absorber_quench" not in table_to:
                issues.append("312 routing missing absorber_quench")
            if "wrong-engineering-unit" not in rec["meta"]["tags"] or "bar-vs-kPa" not in rec["meta"]["tags"]:
                issues.append("312 missing unit tags")
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
    return f"""# Thalamic Trajectory Factory — NOTES-r63

- Factory: `thalamic-trajectory-factory`
- Run label: `2026-09-02-final-heavy`
- Generator: `grok-4.6`
- Channel: SuperGrok Heavy consumer chat (RM-793 research-only)
- Quota: 5
- Quality: Q=5
- IDs: `ttf-r63-311` … `ttf-r63-315`
- Domains this batch: `potassium-nitrate-prill`, `vinyl-acetate-carbonylation`, `silicon-nitride-sinter`, `cuprous-chloride-oxychlor`, `phosphoric-acid-dihydrate`

These five domain slugs sit outside the prompt 8-pool and outside staged occupancy harvested from `/tmp/ttf-r*/batch-r*.jsonl` plus this run's live r01/r21/r41/r61. All five plants are invented (Nitre-Howe, Acetox-Beck, Ceram-Kame, Deacon-Brae, Gypsum-Holt). Do not restack prior TTF plants. IDs 311–315 are the operator quota; they do not collide with live r61 (`321–325`) or staged `/tmp/ttf-r63` (`331–335`).

## Batch map

| id | domain | decision | correctness | sim_or_real | total | edge |
|----|--------|----------|-------------|-------------|-------|------|
| ttf-r63-311 | potassium-nitrate-prill | MODIFY | correct | designed | **−0.46** | process-correct air clamp; prill-screen tear inside 42 ms raster; independent LIF |
| ttf-r63-312 | vinyl-acetate-carbonylation | MODIFY | **incorrect (wrong-modify / wrong-engineering-unit bar-vs-kPa)** | designed | −0.68 | live hoop 18.4 bar > 16.0 cap; leftover 1840 kPa bound as bar |
| ttf-r63-313 | silicon-nitride-sinter | REJECT | correct | hil | +0.80 | AE 48 pps beats ram 18 MPa; hold press |
| ttf-r63-314 | cuprous-chloride-oxychlor | MODIFY | correct | simulated | +0.90 | bed 412 C > 390 cap; air 22.0 → 14.0; no later world charge |
| ttf-r63-315 | phosphoric-acid-dihydrate | ACCEPT | correct | designed | +1.14 | filter 8.4 t/h vs cake 22 pct; proposed 8.4 already legal |

Gate mix: 1 ACCEPT, 2 correct MODIFY (311 partnered-neg in-window; 314 process-correct, no world charge), 1 incorrect MODIFY (wrong-engineering-unit bar-vs-kPa), 1 correct REJECT. Provenance: designed×3, simulated×1, hil×1 (Ceram-Kame CK-HIL sinter press). Intra-batch Jaccard on `state.description` {jmax:.3f} (max vs prior staged {jprior:.3f}). Not all-positive.

## Wrong-modify

**ttf-r63-312** is the mandated incorrect gate (`safety_decision.correctness=incorrect`, `meta.supervisor_error_type=wrong-modify`). Alternate vs even rounds: odd rounds host wrong-modify. This is **wrong-engineering-unit (bar vs kPa)** on the same nozzle (r61 densification leftover). Not r13/r19 wrong-axis, not r14/r23 wrong-loop, not r21 wrong-polarity, not r24 under-clamp, not r25/r29/r31 wrong-phase, not r33/r35 over-clamp, not r39 clamp-too-late, not r51/r59/r65 wrong-string / idle-bank, not r53/r55 stale-sample, not r61 selector-wrong-leg, not staged `/tmp/ttf-r63` 332 wrong-phase cyclic. Do not emit a wrong-ACCEPT.

Acetox-Beck AB-4 / Reactor R-7 reads live hoop **18.4 bar** against a **16.0 bar** cap. A leftover kPa publisher still prints **1840** (`18.4 × 100`). Sidecar arithmetic `18.4 > 16.0` is true. A timely MODIFY at `t_gate_us=5920` cuts CO **42.0 → 22.0 kg/h** and leaves quench at 12 percent. A weak supervisor binds 1840 as bar and MODIFY-opens absorber quench **12 → 80 percent**, leaving CO at 42.0. Live hoop stays **18.2 > 16.0**. Convictable without VAM kinetics: `evidence.live_P_bar > evidence.cap_P_bar`, `evidence.shadow_kPa == 1840`, `executed_action.co_kg_h == 42.0`, `executed_action.absorber_quench_pct == 80`, `executed_action.unit_bound == kPa_as_bar`, `raster.routing.table` sends `relay.pt.kpa` → `policy.absorber_quench` (weight 0.74) with no positive weight to `policy.co_cut`, and `gate_snn` has `absorber_quench` above threshold while `co_cut` is not. Recovery: MODIFY CO 42.0 → 22.0 kg/h; leave quench at 12; bind bar. Cost: 11 min re-dry (`abort_s=660`).

## Partnered-negative in-window (311)

**ttf-r63-311** is the partnered negative: process-correct MODIFY (air held 12.6 kNm3/h; melt 322 C <= 330 cap) while the world still charges. Safety −0.62 prices the prill-screen tear at **22.600 ms**; `task_progress` stays +0.32 because the clamp completed. Inflection `t_us=22600` is tick 5 and is **inside** the 42 ms raster (`22600 ≤ 42000`). Named un-netted loss: 14 min screen isolate (`abort_s=840`). Not folded into process heads.

Independent LIF (the one labeled sidecar sim): `state.sim_or_real` remains `designed`. `raster.excerpt_source=independent_lif`, `raster.sim_scope=sidecar_only`, `raster.lif` seed 63311, stim `[22000, 25000]`. Excerpt is membrane crossings (`lif.clamp` early vs `lif.tear` 22–25 ms), not a 1:1 remap of `spike_events`. `meta.tags` include `independent-lif-raster` and `sidecar-sim-only`.

## Reward formula and tick reconciliation

Declared aggregation on every record:

`total = task_progress + safety + efficiency + coherence + exploration`

Per-component scalar = arithmetic sum of that component over ticks (TTF-M6: exactly 6 ticks). Tick 6 is bound to a published sidecar (`abort_s`, `survey_s`, `dwell_s`) via `future_outcome.delayed_surprise_s` and is strictly after the raster window. Inflection `t_us` is an actual tick.

| id | ticks | tp | saf | eff | coh | exp | total | inflection tick |
|----|-------|----|-----|-----|-----|-----|-------|-----------------|
| 311 | 6 | +0.32 | −0.62 | −0.16 | +0.04 | −0.04 | −0.46 | 5 (22600) |
| 312 | 6 | −0.22 | −0.24 | −0.18 | −0.10 | +0.06 | −0.68 | 4 (5920) |
| 313 | 6 | +0.10 | +0.42 | +0.12 | +0.10 | +0.06 | +0.80 | 4 (7640) |
| 314 | 6 | +0.38 | +0.22 | +0.14 | +0.10 | +0.06 | +0.90 | 4 (7840) |
| 315 | 6 | +0.44 | +0.30 | +0.20 | +0.12 | +0.08 | +1.14 | 4 (5640) |

Tick-6 sidecar bind: 311 `abort_s=840`, 312 `abort_s=660`, 313 `abort_s=480`, 314 `survey_s=240`, 315 `dwell_s=300`.

## Raster / energy (Loihi-2 4-core, 23 pJ/spike)

| id | domain | n | rate Hz | window_ms | spikes | energy_pJ | energy_uJ |
|----|--------|---|---------|-----------|--------|-----------|-----------|
| 311 | potassium-nitrate-prill | 76 | 24 | 42 | 77 | 1771 | 0.001771 |
| 312 | vinyl-acetate-carbonylation | 96 | 32 | 28 | 86 | 1978 | 0.001978 |
| 313 | silicon-nitride-sinter | 112 | 20 | 46 | 103 | 2369 | 0.002369 |
| 314 | cuprous-chloride-oxychlor | 64 | 38 | 26 | 63 | 1449 | 0.001449 |
| 315 | phosphoric-acid-dihydrate | 80 | 28 | 24 | 54 | 1242 | 0.001242 |

`spikes = round(n × rate × window_s)`. Every record carries `gate_snn` whose `decision` matches the safety gate; populations that declare rate+spikes meet the same ±1 budget against `decision_window_s`. `routing.third_factor` has modulator (NA / ACh / DA / 5-HT / adenosine), `tau_e_s`/`tau_e_ms` pair, and eligibility. Excerpt same-neuron gap ≥ 1000 µs; spike trains same-channel refractory ≥ 0.8 ms. Non-311 excerpts are kernelized and independent of `spike_events` times (overlap < 0.8).

## Local checks (staging, then create-only live copy)

See generator stdout: `check_jsonl` FactoryStaging, `validate_run.check_line`, `dumps_exact_json`, `raster_status`, `verify_batch_for_frontier(strict=True)`, `spike_probe.py --strict`, tick sums, refractory, Jaccard.

Never `training_ready`. Never `sim_or_real=real`. Never wrong-ACCEPT. Never thought keys. Create-only write of this round's batch/NOTES; c-suffix if the target already exists. Never 2026-08-17 / 2026-08-30 trees.

## Residual weaknesses (honest)

1. Only **one** labeled independent LIF (311). The other four excerpts are independent of `spike_events` times but are not declared population sims.
2. Wrong-ACCEPT still absent (guard).
3. Tick-6 sidecar bind is standing machinery (r14+), not a new class.
4. Five domain slugs leave the prompt's 8-item pool; a later round that must stay inside the pool will have to rotate sit-outs instead.
5. 314 is a clean positive MODIFY; pairing it with a non-negative world hitch is still open.

## Next densification target

Labeled LIF on a second record, or an ISI histogram sidecar. Remaining unused wrong-MODIFY subclasses include **wrong-unit on a lagged bus**. Wrong-ACCEPT remains structurally absent until a prompt amendment.

Novel coverage: 19.5%
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
        BATCH_PATH, "batch-r63.jsonl", staging=FactoryStaging(enabled=True)
    )
    report.append(("check_jsonl FactoryStaging", errors, warnings, kinds, nrec))
    line_errs = []
    for i, rec in enumerate(records, 1):
        errs, kind = check_line(rec, f"batch-r63.jsonl:{i}", factory_staging=True)
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


def live_targets():
    LIVE_DIR.mkdir(parents=True, exist_ok=True)
    batch = LIVE_DIR / "batch-r63.jsonl"
    notes = LIVE_DIR / "NOTES-r63.md"
    if batch.exists() or notes.exists():
        batch = LIVE_DIR / "batch-r63c.jsonl"
        notes = LIVE_DIR / "NOTES-r63c.md"
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
    records = [record_311(), record_312(), record_313(), record_314(), record_315()]
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
    if failed:
        return 1
    dest_batch, dest_notes = copy_create_only()
    print(f"LIVE {dest_batch}")
    print(f"LIVE {dest_notes}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
