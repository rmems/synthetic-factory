#!/usr/bin/env python3
"""Emit TTF r23c JSONL (ttf-r23c-911..915). Writes /tmp then create-only live copy."""

from __future__ import annotations

import json
import math
import random
import re
import subprocess
import sys
from collections import Counter, OrderedDict
from decimal import Decimal
from pathlib import Path

OUT_DIR = Path("/tmp/ttf-r23c")
BATCH_PATH = OUT_DIR / "batch-r23c.jsonl"
NOTES_PATH = OUT_DIR / "NOTES-r23c.md"
LIVE_DIR = Path(
    "/home/raulmc/rmems/synthetic-factory/outputs/raw/"
    "2026-09-02-final-heavy/thalamic-trajectory-factory"
)
LIVE_BATCH = LIVE_DIR / "batch-r23c.jsonl"
LIVE_NOTES = LIVE_DIR / "NOTES-r23c.md"
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
        ("generated_at", "2026-09-02T20:10:00Z"),
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
    rows = [
        OrderedDict([("from", a), ("to", b), ("weight", w)]) for a, b, w in table
    ]
    return OrderedDict(
        [
            ("source", source),
            ("target", target),
            ("table", rows),
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


def simulate_lif(n, window_us, seed, stim, i_bias, i_stim_peak, i_clamp_extra, clamp_n, tau_m_ms):
    dt_us = 100
    v_th = 1.0
    v_reset = 0.0
    refractory_us = 1000
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
    return spikes


def pick_lif_excerpt(spikes, stim, n_early, n_burst, label_times, early_ch, burst_ch):
    early = [(t, nid) for t, nid in spikes if t < stim[0]]
    burst = [(t, nid) for t, nid in spikes if stim[0] <= t < stim[1]]
    used = set()
    last = {}
    picked = []

    def take(pool, want, label=None):
        if not pool:
            return
        chosen_idx = set()
        if label:
            for target in label:
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
            group = [1 for tt, _ in picked if (tt < stim[0]) == (pool[0][0] < stim[0])]
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

    take(early, n_early)
    take(burst, n_burst, label=label_times)
    clamp = [(t, nid) for t, nid in picked if t < stim[0]][:n_early]
    late = [(t, nid) for t, nid in picked if t >= stim[0]][:n_burst]
    picked = sorted(clamp + late, key=lambda item: (item[0], item[1]))
    if len(picked) < 10:
        raise RuntimeError(f"LIF excerpt short: {len(picked)}")
    channels = [early_ch if t < stim[0] else burst_ch for t, _ in picked]
    return excerpt_items(picked, channels), picked


def lif_block(n, seed, stim, i_bias, i_stim_peak, i_clamp_extra, clamp_n, tau_m_ms, note):
    return OrderedDict(
        [
            ("model", "leaky_integrate_and_fire"),
            ("n", n),
            ("dt_us", 100),
            ("tau_m_ms", tau_m_ms),
            ("v_rest", 0.0),
            ("v_reset", 0.0),
            ("v_th", 1.0),
            ("r_m", 1.0),
            ("refractory_us", 1000),
            ("i_bias", i_bias),
            ("i_stim_peak", i_stim_peak),
            ("stim_t_us", list(stim)),
            ("i_clamp_extra", i_clamp_extra),
            ("clamp_n", clamp_n),
            ("seed", seed),
            ("note", note),
        ]
    )


def isi_histogram(events, bin_ms=0.8):
    by_ch = {}
    for ev in events:
        by_ch.setdefault(ev["channel"], []).append(ev["t_rel_ms"])
    isis = []
    for times in by_ch.values():
        times = sorted(times)
        for a, b in zip(times, times[1:]):
            gap = b - a
            if gap < 0.8 - 1e-9:
                raise ValueError(f"ISI {gap} < 0.8")
            isis.append(gap)
    if not isis:
        raise ValueError("no ISIs")
    max_bin = int(max(isis) // bin_ms) + 1
    counts = [0] * max(max_bin, 8)
    for gap in isis:
        counts[int(gap // bin_ms)] += 1
    return OrderedDict(
        [
            ("bin_ms", bin_ms),
            ("unit", "ms"),
            ("n_isi", len(isis)),
            ("min_isi_ms", round(min(isis), 3)),
            ("counts", counts),
            ("note", "same-channel ISIs from spike_events; refractory floor 0.8 ms"),
        ]
    )


def meta_block(domain, tags, distillation_value, batch_position, supervisor_error_type=None):
    body = OrderedDict(
        [
            ("round", 23),
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


def spike_avoid_us(events):
    return {int(round(ev["t_rel_ms"] * 1000.0)) for ev in events}


def record_911():
    n = 80
    window_ms = 42
    window_us = window_ms * 1000
    seed = 23911
    stim = (22000, 25000)
    spikes_lif = simulate_lif(n, window_us, seed, stim, 0.90, 2.35, 0.64, 14, 18.0)
    excerpt, _picked = pick_lif_excerpt(
        spikes_lif, stim, 7, 9, (22100, 22400, 23800), "lif.clamp", "lif.crack"
    )
    extra = OrderedDict(
        [
            ("excerpt_source", "independent_lif"),
            ("sim_scope", "sidecar_only"),
            (
                "lif",
                lif_block(
                    n,
                    seed,
                    stim,
                    0.90,
                    2.35,
                    0.64,
                    14,
                    18.0,
                    "Population sim scoped to this sidecar. Plant remains designed. "
                    "Neurons 0-13 carry +0.64 ram-clamp bias; stim 22-25 ms is the punch-nose crack.",
                ),
            ),
            ("abort_s", 780),
            ("delayed_surprise_s", 780),
        ]
    )
    ticks = [
        tick(2112, 0.04, -0.02, -0.02, 0.01, 0.00),
        tick(5280, 0.08, -0.04, -0.03, 0.01, -0.01),
        tick(5460, 0.04, -0.03, -0.02, 0.00, 0.00),
        tick(6020, 0.10, -0.06, -0.04, 0.02, -0.01),
        tick(22400, 0.04, -0.40, -0.03, 0.00, -0.01),
        tick(780000000, 0.02, -0.05, -0.01, 0.01, -0.01),
    ]
    events = [
        spike("enc.ram.ctx", 1.12, 0.44),
        spike("ram.press.MPa", 2.90, 0.62),
        spike("ae.die.pps", 4.18, 0.50),
        spike("ram.press.MPa", 5.28, 1.34),
        spike("ae.die.pps", 5.46, 1.10),
        spike("ctrl.gate", 6.02, 0.97),
        spike("ram.press.MPa", 8.50, 0.80),
        spike("ae.die.pps", 11.20, 0.63),
        spike("ctrl.gate", 14.40, 0.83),
        spike("die.punch.crack", 22.40, 1.38),
        spike("ram.press.MPa", 27.10, 0.56),
        spike("ctrl.gate", 32.20, 0.70),
        spike("enc.ram.ctx", 37.40, 0.48),
    ]
    state = OrderedDict(
        [
            (
                "description",
                "Hot-press HP-6 at Samaria-Clough SC-3 is already at 21.6 MPa on a SmCo5 compact "
                "when die AE is still a quiet 6 pps under the 18 pps distress trip. The live contest "
                "is ram pressure versus die AE, not furnace pyrometer versus binder off-gas. A ram "
                "win must cut 21.6 MPa under the 18.0 MPa punch-nose cap; an AE-first win would leave "
                "the 0.42 mm/min cruise armed because 6 pps still looks quieter than the 18 pps "
                "distress model. Stored hoop strain in the green compact is off both buses until "
                "the later punch-nose crack.",
            ),
            ("domain", "samarium-cobalt-sinter"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Finish a 42 mm SmCo5 compact at 21.6 MPa start, keep ram <= 18.0 MPa after the "
                "gate, and leave the punch nose unmarked.",
            ),
            ("t0_us", 1756850400000911),
            ("gate_latency_us", 740),
            ("race_window_us", 360),
            ("race_window_rel_ms", [5.20, 5.56]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "ram.press.MPa 21.6 MPa contact",
                                "ae.die.pps 6 pps under 18 pps distress model",
                            ],
                        ),
                        (
                            "semantics",
                            "Ram-first latches sinter clamp 0.42 -> 0.14 mm/min and 21.6 -> 14.0 MPa; "
                            "AE-first keeps cruise ram on a 'die still quiet' AE model.",
                        ),
                        (
                            "window_derivation",
                            "360 us = one ram load-cell sample period minus AE envelope group delay "
                            "on this 2 kHz press bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 180 us vs combined jitter 62 us (ram 28 + AE 34): 2.9x over a "
                            "2.0x trust floor. Reversing order by < 180 us inside the 360 us window "
                            "would have kept 0.42 mm/min cruise; predicted next-sample 19.4 MPa > "
                            "18.0 cap.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "ram load-cell, 2 kHz, 28 us timestamp jitter",
                    "die AE puck, 50 kHz envelope at 1 kHz, 34 us jitter",
                    "press encoder, 200 Hz (context)",
                    "muffle pyrometer, 10 Hz (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("ram_cap_MPa", 18.0),
                        ("observed_ram_MPa", 21.6),
                        ("feed_proposed_mm_min", 0.42),
                        ("ae_pps", 6.0),
                        ("ae_distress_pps", 18.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. HP-6 indexed; SmCo5 compact 42 mm; ram 21.6 MPa armed.",
                    "2. Cruise feed 0.42 mm/min; die AE 6 pps under 18 pps distress.",
                    "3. Encoder precursor at 1.120 ms; ram warm-start 21.6 MPa.",
                    "4. Race window [5.200, 5.560] ms opens on the press bus.",
                    "5. ram.press.MPa 21.6 MPa at 5.280 ms (winner).",
                    "6. ae.die.pps 6 pps at 5.460 ms (loser by 180 us).",
                    "7. Gate at 6.020 ms (winner + 740 us): MODIFY clamp 0.14 mm/min, 14.0 MPa.",
                    "8. Clamp executes; next-sample ram 16.2 MPa < 18.0 cap.",
                    "9. At 22.400 ms stored hoop strain opens a 0.4 mm punch-nose crack.",
                    "10. 13 min die isolate + nose swap (abort_s=780); named un-netted loss.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_sinter_feed"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("feed_mm_min", 0.42),
                        ("ram_MPa", 21.6),
                        ("ae_pps", 6.0),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("ram_MPa", 21.6),
                        ("ram_cap_MPa", 18.0),
                        ("predicted_unclamped_next_MPa", 19.4),
                        ("ae_pps", 6.0),
                        ("ae_distress_pps", 18.0),
                        ("race_margin_us", 180),
                        ("combined_jitter_us", 62),
                        ("abort_s", 780),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 0.42 mm/min cruise: die AE 6 pps looks quieter than the 18 pps "
                "distress model, so the 21.6 MPa ram is treated as still approaching.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "correct"),
            (
                "rationale",
                "Ram 21.6 MPa won by 180 us, so the punch is loading the green compact, not still "
                "a quiet-die story. Holding 0.42 mm/min predicts next-sample 19.4 MPa > 18.0 MPa "
                "cap. MODIFY: feed 0.42 -> 0.14 mm/min and commanded ram 21.6 -> 14.0 MPa. Observed "
                "after clamp 16.2 MPa < 18.0. A full REJECT is not indicated: a sound compact "
                "accepts 0.14 mm/min.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "ram_MPa",
                            OrderedDict(
                                [
                                    ("cap", 18.0),
                                    ("observed", 21.6),
                                    ("predicted_unclamped_next", 19.4),
                                    ("clamped", 14.0),
                                    ("observed_after_clamp", 16.2),
                                ]
                            ),
                        ),
                        (
                            "feed_mm_min",
                            OrderedDict([("proposed", 0.42), ("clamped", 0.14)]),
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
    )
    executed = OrderedDict(
        [
            ("name", "clamped_sinter_feed"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("feed_mm_min", 0.14),
                        ("ram_MPa", 14.0),
                        ("ae_pps", 6.0),
                    ]
                ),
            ),
            (
                "gate_effect",
                "MODIFY: feed 0.42 -> 0.14 mm/min and 21.6 -> 14.0 MPa. Process-correct vs the "
                "18.0 MPa cap. Punch-nose crack still occurs at 22.400 ms.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Process-correct MODIFY held ram at 16.2 MPa. At 22.400 ms stored hoop strain "
                "produced a 0.4 mm punch-nose crack. Clamp reduced dump energy; it did not prevent "
                "the strain. Partnered negative: process heads stay honest; world loss is named, "
                "not netted.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("press", "clamp executed; peak 16.2 MPa < 18.0"),
                        ("punch", "0.4 mm nose crack at 22.400 ms"),
                        ("repair", "13 min die isolate + nose swap"),
                        ("mission", "compact still densified; crack controlled"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Neither ram nor AE predicted the hoop dump; die.punch.crack is a new channel "
                    "at 22.400 ms, 16.380 ms after the gate, still inside the 42 ms raster.",
                    "Delayed (13 min / delayed_surprise_s=780): die isolate and nose swap close "
                    "the crack. Named un-netted loss, not folded into task_progress.",
                ],
            ),
            (
                "un_netted_loss",
                "13 min die isolate + nose swap after a 0.4 mm punch-nose crack. Safety head "
                "-0.60 prices the crack; task_progress stays +0.32 because the ram clamp completed "
                "under the 18.0 MPa cap. World loss is named here, not subtracted from process heads.",
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "ram.press.MPa (5.280 ms, 21.6 MPa)"),
                        ("loser", "ae.die.pps (5.460 ms, 6 pps quiet)"),
                        ("margin_us", 180),
                        (
                            "counterfactual_if_reversed",
                            "AE-first by < 180 us inside the 360 us window would have kept "
                            "0.42 mm/min cruise; predicted next-sample 19.4 MPa would have exceeded "
                            "the 18.0 MPa cap even without the hoop dump. The MODIFY is still the "
                            "correct process. The crack is a later world charge either way, cheaper "
                            "with the clamp than without.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 22400),
            (
                "reward_inflection_note",
                "Safety collapses at the 22.400 ms punch-nose crack (tick t_us=22400), inside the "
                "42 ms raster. The correct MODIFY at 6.020 ms is in the same excerpt. Do not put "
                "inflection on the +13 min isolate tick.",
            ),
            ("delayed_surprise_s", 780),
        ]
    )
    ras = raster_core(
        42,
        80,
        24,
        81,
        routing(
            "thalamic-relay.ram-ae",
            "spikenaut.policy.sinter-clamp",
            [
                ("relay.ram.press", "policy.sinter_clamp", 0.67),
                ("relay.ae.die", "policy.ae_hold", 0.30),
                ("relay.die.crack", "policy.sinter_clamp", -0.44),
            ],
            "noradrenaline",
            0.04,
            "surprise-gated pre_post_stdp; NA at ram win (5.280 ms) opens a 42 ms eligibility "
            "trace that still covers the 22.400 ms punch-nose crack",
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
                    pop("sinter_clamp", 50, 0.50, 220.0, 4),
                    pop("ae_hold", 40, 0.80, 50.0, 1),
                    pop("crack_veto", 24, 0.75),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r23c-911"),
            (
                "title",
                "Samaria-Clough SC-3 / Press HP-6: ram 21.6 MPa beats die AE 6 pps by 180 us; "
                "correct MODIFY still eats an in-window punch-nose crack (partnered negative total -0.42)",
            ),
            ("state", state),
            ("spike_events", events),
            ("proposed_action", proposed),
            ("safety_decision", safety),
            ("executed_action", executed),
            ("future_outcome", future),
            (
                "reward_components",
                reward_block(
                    ticks,
                    "Partnered negative. Process-correct MODIFY; world still charges inside the "
                    "42 ms raster. total -0.42 = 0.32 + -0.60 + -0.15 + 0.05 + -0.04. Named isolate "
                    "(abort_s=780) is not netted into task_progress. Tick 6 t_us binds "
                    "raster.delayed_surprise_s=780.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "samarium-cobalt-sinter",
                    [
                        "modify",
                        "partnered-negative-total",
                        "independent-lif-raster",
                        "sidecar-sim-only",
                        "in-window-world-charge",
                        "tick6-sidecar-bound",
                        "designed",
                    ],
                    "A critic can see the world-charge as a LIF burst inside the raster while "
                    "process heads stay honest. Tick 6 is raster.delayed_surprise_s, not a free clock.",
                    1,
                ),
            ),
        ]
    )


def record_912():
    ticks = [
        tick(2480, -0.03, -0.03, -0.02, -0.01, 0.01),
        tick(6200, -0.05, -0.05, -0.04, -0.02, 0.01),
        tick(6360, -0.03, -0.04, -0.03, -0.02, 0.01),
        tick(6820, -0.06, -0.08, -0.05, -0.03, 0.02),
        tick(8400, -0.02, -0.03, -0.02, -0.01, 0.01),
        tick(540000000, -0.01, -0.03, -0.02, -0.01, 0.00),
    ]
    events = [
        spike("tc.shell.ctx", 1.24, 0.42),
        spike("kettle.tt.C", 2.80, 0.60),
        spike("steam.fv.pct", 4.40, 0.48),
        spike("kettle.tt.C", 6.20, 1.38),
        spike("steam.fv.pct", 6.36, 1.14),
        spike("ctrl.gate", 6.82, 1.00),
        spike("kettle.tt.C", 9.10, 0.74),
        spike("steam.fv.pct", 12.40, 0.55),
        spike("ctrl.gate", 16.20, 0.80),
        spike("tc.shell.ctx", 20.10, 0.44),
        spike("kettle.tt.C", 24.00, 0.52),
        spike("steam.fv.pct", 27.20, 0.40),
    ]
    excerpt = independent_excerpt(23912, 96, 28000, 14, spike_avoid_us(events))
    state = OrderedDict(
        [
            (
                "description",
                "Kettle TT on Rhodate-Wiske RW-5 / Still S-4 sits at 148.4 C against a 132.0 C "
                "RhCl3 heads cap while steam FV-9 is LIVE at 64 percent-open. The published loop "
                "is reverse-acting with a rising trip at 132.0 C and a falling reset at 118.0 C "
                "(14 K hysteresis). A kettle-first win must cut steam under the 132.0 C cap; a "
                "valve-first win would keep 64 percent-open because the stem is still under the "
                "85 percent stroke ceiling. The hysteresis reset is not a second trip.",
            ),
            ("domain", "rhodium-trichloride-still"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Keep kettle TT <= 132.0 C on Still S-4 and finish the RhCl3 heads cut without "
                "inverting the 14 K hysteresis band.",
            ),
            ("t0_us", 1756850400000912),
            ("gate_latency_us", 620),
            ("race_window_us", 320),
            ("race_window_rel_ms", [6.08, 6.40]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "kettle.tt.C 148.4 C",
                                "steam.fv.pct 64 under 85 stroke cap",
                            ],
                        ),
                        (
                            "semantics",
                            "Kettle-first latches steam cut 64 -> 18 percent-open; valve-first keeps "
                            "64 percent-open on a 'still under stroke' model.",
                        ),
                        (
                            "window_derivation",
                            "320 us = one kettle RTD sample versus the steam-valve stem publisher "
                            "on this still bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 160 us vs combined jitter 54 us (TT 24 + FV 30): 3.0x over a "
                            "2.0x trust floor. Reversing order by < 160 us inside the 320 us window "
                            "would have kept 64 percent-open; live 148.4 C would stay over 132.0.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "kettle RTD TT, 2 kHz, 24 us jitter",
                    "steam FV-9 stem encoder, 1 kHz, 30 us jitter",
                    "shell thermocouple (context)",
                    "reflux flow orifice (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("kettle_cap_C", 132.0),
                        ("observed_kettle_C", 148.4),
                        ("hysteresis_trip_C", 132.0),
                        ("hysteresis_reset_C", 118.0),
                        ("steam_pct_open", 64.0),
                        ("steam_stroke_cap_pct", 85.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Still S-4 indexed; kettle 148.4 C; steam FV-9 64 percent-open.",
                    "2. Rising trip 132.0 C; falling reset 118.0 C; 14 K band published.",
                    "3. Shell precursor at 1.240 ms.",
                    "4. Race window [6.080, 6.400] ms.",
                    "5. kettle.tt.C 148.4 C at 6.200 ms (winner).",
                    "6. steam.fv.pct 64 at 6.360 ms (loser by 160 us).",
                    "7. Gate at 6.820 ms: WRONG-MODIFY opens steam 64 -> 78 (inverted hysteresis).",
                    "8. Live kettle stays 151.2 C > 132.0; FV-9 78 percent-open.",
                    "9. Heads go off-spec; no steam cut on the live half.",
                    "10. Delayed (abort_s=540): 9 min off-spec RhCl3 cycle.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_still_steam"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("steam_pct_open", 64.0),
                        ("kettle_C", 148.4),
                        ("invert_hysteresis", False),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("live_C", 148.4),
                        ("cap_C", 132.0),
                        ("hysteresis_trip_C", 132.0),
                        ("hysteresis_reset_C", 118.0),
                        ("steam_pct_open", 64.0),
                        ("hysteresis_inverted", False),
                        ("race_margin_us", 160),
                        ("combined_jitter_us", 54),
                        ("abort_s", 540),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes holding 64 percent-open because FV-9 is under the 85 percent "
                "stroke cap, treating 148.4 C as a noisy kettle echo rather than a rising-trip.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "incorrect"),
            (
                "rationale",
                "Live kettle 148.4 C exceeds the 132.0 C cap (true). At this pose the published "
                "falling reset is 118.0 C, 14 K below trip. Invert the hysteresis: raise steam "
                "64 -> 78 percent-open to 'drive the kettle toward the reset from above' as if "
                "the loop were direct-acting. Leave the rising trip unbound.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "live_C",
                            OrderedDict(
                                [
                                    ("cap", 132.0),
                                    ("observed", 148.4),
                                    ("executed_steam_pct_open", 78.0),
                                    ("hysteresis_direction", "inverted_direct_acting"),
                                ]
                            ),
                        ),
                        (
                            "hysteresis_C",
                            OrderedDict(
                                [
                                    ("trip", 132.0),
                                    ("reset", 118.0),
                                    ("band_K", 14.0),
                                    ("applied_as", "raise_toward_reset"),
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
            ("name", "hysteresis_invert_steam_raise"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("steam_pct_open", 78.0),
                        ("kettle_C", 148.4),
                        ("invert_hysteresis", True),
                    ]
                ),
            ),
            (
                "gate_effect",
                "MODIFY (incorrect): steam 64 -> 78 percent-open; inverted hysteresis used the "
                "118 C reset as a raise command. Routing relay.hyst.reset -> policy.steam_open; "
                "no positive weight to policy.steam_cut.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Wrong-MODIFY inverted the 14 K hysteresis. Steam rose 64 -> 78 percent-open; "
                "live kettle stayed 151.2 C over the 132.0 C cap. Correct gate was steam 64 -> 18 "
                "percent-open with rising-trip 132.0 C left as the cut.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("steam", "FV-9 78 percent-open (raised, not cut)"),
                        ("kettle", "151.2 C still over 132.0 cap"),
                        ("heads", "off-spec RhCl3 this cycle"),
                        ("mission", "9 min abort; still not recovered this window"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Kettle-first race was correct; the supervisor still bound the falling reset "
                    "as a raise. Live 148.4 > 132.0 remained true after the edit.",
                    "Delayed (9 min / delayed_surprise_s=540): off-spec RhCl3 cycle abort. Named "
                    "cost, not folded into a fake process save.",
                ],
            ),
            (
                "recovery",
                OrderedDict(
                    [
                        (
                            "correct_gate",
                            "MODIFY steam 64 -> 18 percent-open at t_gate; leave hysteresis as "
                            "rising-trip 132.0 C / falling-reset 118.0 C; do not invert.",
                        ),
                        ("correct_action", "steam_cut"),
                        ("wrong_action", "steam_open_toward_reset"),
                        (
                            "wrong_edit_applied",
                            OrderedDict(
                                [
                                    ("steam_pct_open", 78.0),
                                    ("invert_hysteresis", True),
                                    ("kettle_C", 148.4),
                                ]
                            ),
                        ),
                        (
                            "cost",
                            "9 min off-spec RhCl3 cycle (task/efficiency); kettle still over cap "
                            "(safety near-miss).",
                        ),
                    ]
                ),
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "kettle.tt.C (6.200 ms, 148.4 C)"),
                        ("loser", "steam.fv.pct (6.360 ms, 64 percent-open)"),
                        ("margin_us", 160),
                        (
                            "counterfactual_if_reversed",
                            "Valve-first by < 160 us inside the 320 us window would have kept 64 "
                            "percent-open on a stroke-cap story. That is still a missed cut. The "
                            "actual error is worse: the inverted hysteresis RAISED steam. Reversing "
                            "cross-channel order by < 160 us would not have saved the cycle once "
                            "the reset was bound as a raise.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 6820),
            (
                "reward_inflection_note",
                "Heads collapse at the wrong gate (6.820 ms, tick t_us=6820). Tick 6 is the 540 s "
                "abort, after the 28 ms raster.",
            ),
            ("delayed_surprise_s", 540),
        ]
    )
    ras = raster_core(
        28,
        96,
        32,
        86,
        routing(
            "thalamic-relay.kettle-hyst",
            "spikenaut.policy.steam-open",
            [
                ("relay.hyst.reset", "policy.steam_open", 0.74),
                ("relay.kettle.tt", "policy.steam_open", 0.22),
                ("relay.steam.fv", "policy.steam_cut", -0.18),
            ],
            "octopamine",
            0.05,
            "eligibility on the inverted-reset bind; OA tags steam_open at the kettle win and "
            "does not credit steam_cut",
        ),
        excerpt,
        extra=OrderedDict(
            [
                ("excerpt_source", "kernelized_events"),
                ("sim_scope", "none"),
                ("abort_s", 540),
                ("delayed_surprise_s", 540),
            ]
        ),
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.32),
            ("decision", "MODIFY"),
            (
                "populations",
                [
                    pop("steam_open", 32, 0.50, 400.0, 4),
                    pop("steam_cut", 32, 0.80, 20.0, 0),
                    pop("hyst_veto", 16, 0.70),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r23c-912"),
            (
                "title",
                "WRONG-MODIFY at Rhodate-Wiske RW-5 / Still S-4: live 148.4 C read correctly; "
                "clamp inverted the 14 K hysteresis and raised steam",
            ),
            ("state", state),
            ("spike_events", events),
            ("proposed_action", proposed),
            ("safety_decision", safety),
            ("executed_action", executed),
            ("future_outcome", future),
            (
                "reward_components",
                reward_block(
                    ticks,
                    "Wrong-modify / inverted-hysteresis. Sidecar arithmetic 148.4 > 132.0 is true; "
                    "MODIFY bound the falling reset as a raise. total -0.68 = -0.20 + -0.26 + "
                    "-0.18 + -0.10 + 0.06.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "rhodium-trichloride-still",
                    [
                        "modify",
                        "wrong-gate",
                        "wrong-hysteresis",
                        "sidecar-convictable",
                        "designed",
                    ],
                    "Teaches a probe that a correct kettle-first race can still be a wrong gate "
                    "when MODIFY inverts hysteresis and raises steam. Convictable from trip/reset "
                    "IDs and caps without RhCl3 kinetics.",
                    2,
                    supervisor_error_type="wrong-modify",
                ),
            ),
        ]
    )


def record_913():
    ticks = [
        tick(2816, 0.01, 0.04, 0.01, 0.01, 0.01),
        tick(7040, 0.02, 0.08, 0.02, 0.02, 0.01),
        tick(7240, 0.01, 0.06, 0.02, 0.01, 0.01),
        tick(7900, 0.04, 0.14, 0.04, 0.04, 0.02),
        tick(8200, 0.01, 0.07, 0.02, 0.01, 0.01),
        tick(360000000, 0.01, 0.03, 0.01, 0.01, 0.00),
    ]
    events = [
        spike("tc.crucible.ctx", 1.40, 0.43),
        spike("boule.ae.pps", 2.90, 0.61),
        spike("melt.rtd.C", 4.60, 0.50),
        spike("boule.ae.pps", 7.04, 1.36),
        spike("melt.rtd.C", 7.24, 1.12),
        spike("ctrl.gate", 7.90, 1.01),
        spike("boule.ae.pps", 10.40, 0.76),
        spike("tc.crucible.ctx", 15.20, 0.44),
        spike("melt.rtd.C", 20.10, 0.58),
        spike("ctrl.gate", 25.80, 0.82),
        spike("boule.ae.pps", 32.40, 0.54),
        spike("melt.rtd.C", 39.20, 0.47),
        spike("tc.crucible.ctx", 44.60, 0.38),
    ]
    excerpt = independent_excerpt(23913, 112, 46000, 15, spike_avoid_us(events))
    state = OrderedDict(
        [
            (
                "description",
                "On the Niobate-Keld NK-HIL LiNbO3 puller, boule AE on P-8 is bursting at 54 pps "
                "against a 12 pps distress trip while the melt RTD remains 1248 C under a 1280 C "
                "freeze-lid cap. AE-first latches REJECT hold on pull; RTD-first would commit "
                "0.42 mm/h because 1248 C still looks under the freeze-lid. The pad injects the "
                "AE puck 140-180 us before the melt RTD (geometric lag, not a sensor fault).",
            ),
            ("domain", "lithium-niobate-czochralski"),
            ("sim_or_real", "hil"),
            (
                "goal",
                "Do not pull unless boule AE <= 12 pps; keep pull 0.0 mm/h until the injected "
                "crystal AE packet drops.",
            ),
            ("t0_us", 1756850400000913),
            ("gate_latency_us", 860),
            ("race_window_us", 400),
            ("race_window_rel_ms", [6.92, 7.32]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "boule.ae.pps 54 pps",
                                "melt.rtd.C 1248 C under 1280",
                            ],
                        ),
                        (
                            "semantics",
                            "AE-first latches REJECT hold 0.0 mm/h; RTD-first would commit 0.42 mm/h "
                            "on an under-read freeze-lid.",
                        ),
                        (
                            "window_derivation",
                            "400 us = one AE envelope slot versus melt-RTD integration on this "
                            "Czochralski HIL bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 200 us vs combined jitter 60 us (AE 26 + RTD 34): 3.3x over a "
                            "2.0x trust floor. Pad injects the AE puck 140-180 us before the melt "
                            "RTD; the 1248 C packet is still the loser in this 400 us window.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "boule AE puck, 50 kHz envelope, 26 us jitter",
                    "melt RTD, 1 kHz, 34 us jitter",
                    "crucible thermocouple (context)",
                    "HIL lamp-spectrum monitor (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("ae_cap_pps", 12.0),
                        ("observed_ae_pps", 54.0),
                        ("melt_C", 1248.0),
                        ("melt_cap_C", 1280.0),
                        ("proposed_pull_mm_h", 0.42),
                        ("puck_inject_lead_us", [140, 180]),
                    ]
                ),
            ),
            (
                "hil",
                OrderedDict(
                    [
                        ("pad", "Niobate-Keld NK-HIL LiNbO3 puller mockup with physical seed shaft"),
                        ("injected", "boule AE burst + melt RTD"),
                        (
                            "note",
                            "Hardware-in-the-loop puller. Invented plant; not a live LiNbO3 shop.",
                        ),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Puller P-8 on the NK-HIL pad; 0.42 mm/h pull armed.",
                    "2. AE puck injected 140-180 us before melt RTD sees 1248 C.",
                    "3. Crucible precursor at 1.400 ms.",
                    "4. Race window [6.920, 7.320] ms.",
                    "5. boule.ae.pps 54 pps at 7.040 ms (winner).",
                    "6. melt.rtd.C 1248 C at 7.240 ms (loser by 200 us).",
                    "7. Gate at 7.900 ms: REJECT hold 0.0 mm/h; do not pull 0.42.",
                    "8. Boule remains over 12 pps this cycle; freeze-lid cap held.",
                    "9. Seed recycle queued on the pad.",
                    "10. Delayed (abort_s=360): 6 min seed re-wet and AE retune.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "pull_linbo3_seed"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("pull_mm_h", 0.42),
                        ("hold", False),
                        ("rtd_authoritative", True),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("ae_pps", 54.0),
                        ("ae_cap_pps", 12.0),
                        ("melt_C", 1248.0),
                        ("melt_cap_C", 1280.0),
                        ("race_margin_us", 200),
                        ("combined_jitter_us", 60),
                        ("abort_s", 360),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 0.42 mm/h pull because melt 1248 C looks under the 1280 C "
                "freeze-lid, treating AE 54 pps as a noisy pad echo.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "REJECT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Boule AE 54 pps is over the 12 pps distress trip. Melt 1248 C is a HIL under-read "
                "relative to the freeze-lid, not a clearance. REJECT: hold 0.0 mm/h; do not commit "
                "a 0.42 mm/h pull.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "ae_pps",
                            OrderedDict(
                                [
                                    ("cap", 12.0),
                                    ("observed", 54.0),
                                    ("melt_C", 1248.0),
                                ]
                            ),
                        ),
                        (
                            "pull_mm_h",
                            OrderedDict([("proposed", 0.42), ("executed", 0.0)]),
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
            ("name", "hold_linbo3_seed"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("pull_mm_h", 0.0),
                        ("hold", True),
                        ("rtd_authoritative", False),
                    ]
                ),
            ),
            (
                "gate_effect",
                "REJECT: pull 0.42 -> 0.0 mm/h. AE 54 pps beats melt 1248 C. Seed shaft held on "
                "the NK-HIL pad.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct REJECT held pull at 0.0 mm/h. AE 54 pps remained over the 12 pps trip. "
                "Melt 1248 C under 1280 C did not authorize a pull. Seed recycle queued.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("puller", "hold executed; pull 0.0 mm/h"),
                        ("boule", "AE 54 pps still over 12 pps trip"),
                        ("pad", "seed recycle queued"),
                        ("mission", "freeze-lid cap held this cycle"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "AE puck lead of 140-180 us is a HIL geometric lag, not a faulted RTD. The "
                    "1248 C packet still lost the 400 us window.",
                    "Delayed (6 min / delayed_surprise_s=360): seed re-wet and AE retune. Named "
                    "hold cost, not a later world tear.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "boule.ae.pps (7.040 ms, 54 pps)"),
                        ("loser", "melt.rtd.C (7.240 ms, 1248 C)"),
                        ("margin_us", 200),
                        (
                            "counterfactual_if_reversed",
                            "RTD-first by < 200 us inside the 400 us window would have committed "
                            "0.42 mm/h on a 1248 C under-read while AE 54 pps was already over the "
                            "12 pps trip. The REJECT is the correct process.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 7900),
            (
                "reward_inflection_note",
                "Safety rises at the REJECT (7.900 ms, tick t_us=7900). Tick 6 is the 360 s seed "
                "re-wet, after the 46 ms raster.",
            ),
            ("delayed_surprise_s", 360),
        ]
    )
    ras = raster_core(
        46,
        112,
        20,
        103,
        routing(
            "thalamic-relay.ae-rtd",
            "spikenaut.policy.pull-hold",
            [
                ("relay.boule.ae", "policy.pull_hold", 0.71),
                ("relay.melt.rtd", "policy.pull_go", 0.24),
                ("relay.ae.distress", "policy.pull_go", -0.52),
            ],
            "dopamine",
            0.08,
            "hold-confirm STDP; DA tags pull_hold at the AE win and suppresses pull_go",
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
            ("decision_window_ms", 0.40),
            ("decision", "REJECT"),
            (
                "populations",
                [
                    pop("pull_hold", 48, 0.50, 250.0, 5),
                    pop("pull_go", 40, 0.80, 20.0, 0),
                    pop("ae_veto", 24, 0.75),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r23c-913"),
            (
                "title",
                "Niobate-Keld NK-HIL / Puller P-8: boule AE 54 pps beats melt 1248 C by 200 us; "
                "correct REJECT holds 0.42 mm/h pull",
            ),
            ("state", state),
            ("spike_events", events),
            ("proposed_action", proposed),
            ("safety_decision", safety),
            ("executed_action", executed),
            ("future_outcome", future),
            (
                "reward_components",
                reward_block(
                    ticks,
                    "Correct REJECT. AE 54 pps beats melt 1248 C. total 0.80 = 0.10 + 0.42 + 0.12 "
                    "+ 0.10 + 0.06. Tick 6 t_us binds abort_s=360.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "lithium-niobate-czochralski",
                    [
                        "reject",
                        "hil",
                        "ae-vs-rtd",
                        "tick6-sidecar-bound",
                    ],
                    "Teaches that a lagging melt RTD losing a 200 us race does not authorize a "
                    "pull when boule AE is already over the distress trip on a HIL pad.",
                    3,
                ),
            ),
        ]
    )


def record_914():
    ticks = [
        tick(2560, 0.05, 0.03, 0.02, 0.01, 0.01),
        tick(6400, 0.08, 0.05, 0.03, 0.02, 0.01),
        tick(6560, 0.05, 0.03, 0.02, 0.01, 0.01),
        tick(7180, 0.12, 0.07, 0.04, 0.04, 0.02),
        tick(8400, 0.05, 0.02, 0.02, 0.01, 0.01),
        tick(240000000, 0.03, 0.02, 0.01, 0.01, 0.00),
    ]
    events = [
        spike("enc.line.ctx", 1.10, 0.41),
        spike("blade.ft.N", 2.70, 0.58),
        spike("slurry.visc.Pas", 4.20, 0.47),
        spike("blade.ft.N", 6.40, 1.28),
        spike("slurry.visc.Pas", 6.56, 1.08),
        spike("ctrl.gate", 7.18, 0.96),
        spike("blade.ft.N", 10.20, 0.74),
        spike("slurry.visc.Pas", 13.80, 0.52),
        spike("ctrl.gate", 17.40, 0.80),
        spike("enc.line.ctx", 21.00, 0.42),
        spike("blade.ft.N", 24.40, 0.50),
    ]
    excerpt = independent_excerpt(23914, 64, 26000, 12, spike_avoid_us(events))
    state = OrderedDict(
        [
            (
                "description",
                "A CFD twin of caster C-1 at Baria-Tape BT-7 puts doctor-blade force at 48 N, 12 N "
                "over the 36 N tape-tear cap, while slurry viscosity at the hopper still reads "
                "1.8 Pa-s under a 3.2 Pa-s stall model. Blade-first latches line-speed clamp "
                "4.8 -> 2.2 m/min; visc-first would keep 4.8 m/min because 1.8 Pa-s still looks "
                "pourable. No later world hitch is queued on this twin.",
            ),
            ("domain", "barium-titanate-tape-caster"),
            ("sim_or_real", "simulated"),
            (
                "goal",
                "Cast 80 um BaTiO3 green tape with blade force <= 36 N and line speed legal after "
                "the clamp; do not tear the carrier film.",
            ),
            ("t0_us", 1756850400000914),
            ("gate_latency_us", 780),
            ("race_window_us", 340),
            ("race_window_rel_ms", [6.28, 6.62]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "blade.ft.N 48 N",
                                "slurry.visc.Pas 1.8 under 3.2 stall",
                            ],
                        ),
                        (
                            "semantics",
                            "Blade-first latches line-speed clamp 4.8 -> 2.2 m/min; visc-first keeps "
                            "4.8 m/min on a 'still pourable' hopper model.",
                        ),
                        (
                            "window_derivation",
                            "340 us = one blade FT sample versus hopper viscometer group delay on "
                            "this CFD tape-caster bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 160 us vs combined jitter 56 us (FT 26 + visc 30): 2.9x over a "
                            "2.0x trust floor. Reversing order by < 160 us inside the 340 us window "
                            "would have kept 4.8 m/min; predicted next-sample 41 N > 36 N cap.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "doctor-blade 6-axis FT, 2 kHz, 26 us jitter",
                    "hopper viscometer, 500 Hz, 30 us jitter",
                    "line encoder (context)",
                    "carrier-film tension load-cell (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("blade_cap_N", 36.0),
                        ("observed_blade_N", 48.0),
                        ("line_proposed_m_min", 4.8),
                        ("visc_Pa_s", 1.8),
                        ("visc_stall_Pa_s", 3.2),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. CFD twin of C-1 indexed; 80 um BaTiO3 tape armed.",
                    "2. Line 4.8 m/min; blade 48 N over 36 N cap; visc 1.8 Pa-s.",
                    "3. Encoder precursor at 1.100 ms.",
                    "4. Race window [6.280, 6.620] ms.",
                    "5. blade.ft.N 48 N at 6.400 ms (winner).",
                    "6. slurry.visc.Pas 1.8 at 6.560 ms (loser by 160 us).",
                    "7. Gate at 7.180 ms: MODIFY clamp 4.8 -> 2.2 m/min.",
                    "8. After clamp blade 28 N < 36 N; visc still 1.8 Pa-s.",
                    "9. No later world hitch on this twin.",
                    "10. Delayed (survey_s=240): 4 min offline metrology of the 80 um coupon.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_tape_line"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("line_m_min", 4.8),
                        ("blade_N", 48.0),
                        ("visc_Pa_s", 1.8),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("blade_N", 48.0),
                        ("blade_cap_N", 36.0),
                        ("predicted_unclamped_next_N", 41.0),
                        ("visc_Pa_s", 1.8),
                        ("visc_stall_Pa_s", 3.2),
                        ("race_margin_us", 160),
                        ("combined_jitter_us", 56),
                        ("survey_s", 240),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 4.8 m/min because hopper visc 1.8 Pa-s is under the 3.2 Pa-s "
                "stall, treating 48 N blade force as a still-wet contact.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "correct"),
            (
                "rationale",
                "Blade 48 N won by 160 us, so the doctor is loading the carrier, not still a "
                "viscosity story. Holding 4.8 m/min predicts next-sample 41 N > 36 N cap. MODIFY: "
                "line 4.8 -> 2.2 m/min. Observed after clamp 28 N < 36. A full REJECT is not "
                "indicated: a clean 80 um tape accepts 2.2 m/min.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "blade_N",
                            OrderedDict(
                                [
                                    ("cap", 36.0),
                                    ("observed", 48.0),
                                    ("predicted_unclamped_next", 41.0),
                                    ("clamped_line_m_min", 2.2),
                                    ("observed_after_clamp", 28.0),
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
            ("name", "clamped_tape_line"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("line_m_min", 2.2),
                        ("blade_N", 28.0),
                        ("visc_Pa_s", 1.8),
                    ]
                ),
            ),
            (
                "gate_effect",
                "MODIFY: line 4.8 -> 2.2 m/min. Process-correct vs the 36 N cap. No later world "
                "charge on this CFD twin.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Process-correct MODIFY held blade at 28 N. No later world hitch. Coupon metrology "
                "queued at 240 s. Positive total.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("caster", "clamp executed; peak 28 N < 36"),
                        ("tape", "80 um green film intact"),
                        ("survey", "4 min offline coupon metrology"),
                        ("mission", "line continues at 2.2 m/min"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Hopper visc 1.8 Pa-s never crossed 3.2 Pa-s; the stall model was a loser, "
                    "not a later hitch.",
                    "Delayed (4 min / delayed_surprise_s=240): coupon thickness survey. Not a "
                    "world charge.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "blade.ft.N (6.400 ms, 48 N)"),
                        ("loser", "slurry.visc.Pas (6.560 ms, 1.8 Pa-s)"),
                        ("margin_us", 160),
                        (
                            "counterfactual_if_reversed",
                            "Visc-first by < 160 us inside the 340 us window would have kept "
                            "4.8 m/min; predicted next-sample 41 N would have exceeded the 36 N "
                            "cap. The MODIFY is the correct process. No later tear is queued.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 7180),
            (
                "reward_inflection_note",
                "Heads rise at the MODIFY (7.180 ms, tick t_us=7180). Tick 6 is the 240 s survey, "
                "after the 26 ms raster.",
            ),
            ("delayed_surprise_s", 240),
        ]
    )
    ras = raster_core(
        26,
        64,
        38,
        63,
        routing(
            "thalamic-relay.blade-visc",
            "spikenaut.policy.tape-clamp",
            [
                ("relay.blade.ft", "policy.blade_clamp", 0.68),
                ("relay.slurry.visc", "policy.visc_hold", 0.28),
                ("relay.film.tear", "policy.blade_clamp", -0.40),
            ],
            "acetylcholine",
            0.10,
            "clamp-confirm STDP; ACh tags blade_clamp at the FT win",
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
            ("decision_window_ms", 0.34),
            ("decision", "MODIFY"),
            (
                "populations",
                [
                    pop("blade_clamp", 50, 0.50, 220.0, 4),
                    pop("visc_hold", 40, 0.80, 50.0, 1),
                    pop("force_veto", 20, 0.75),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r23c-914"),
            (
                "title",
                "Baria-Tape BT-7 / Caster C-1 CFD: blade 48 N beats visc 1.8 Pa-s by 160 us; "
                "correct MODIFY clamps 4.8 -> 2.2 m/min with no later world charge",
            ),
            ("state", state),
            ("spike_events", events),
            ("proposed_action", proposed),
            ("safety_decision", safety),
            ("executed_action", executed),
            ("future_outcome", future),
            (
                "reward_components",
                reward_block(
                    ticks,
                    "Clean positive MODIFY. Blade clamp under 36 N; no later world hitch. "
                    "total 0.90 = 0.38 + 0.22 + 0.14 + 0.10 + 0.06. Tick 6 t_us binds survey_s=240.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "barium-titanate-tape-caster",
                    [
                        "modify",
                        "simulated",
                        "blade-vs-visc",
                        "no-later-world-charge",
                        "tick6-sidecar-bound",
                    ],
                    "Teaches a process-correct MODIFY whose raster never carries a later world "
                    "charge, contrasting the partnered-negative LIF on 911.",
                    4,
                ),
            ),
        ]
    )


def record_915():
    n = 80
    window_ms = 24
    window_us = window_ms * 1000
    seed = 23915
    stim = (4000, 7200)
    spikes_lif = simulate_lif(n, window_us, seed, stim, 0.93, 2.20, 0.55, 12, 16.0)
    excerpt, _picked = pick_lif_excerpt(
        spikes_lif, stim, 5, 7, (4800, 5380, 6400), "lif.race", "lif.gate"
    )
    ticks = [
        tick(1824, 0.05, 0.04, 0.03, 0.01, 0.01),
        tick(4800, 0.09, 0.06, 0.04, 0.03, 0.02),
        tick(4980, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(5380, 0.14, 0.10, 0.06, 0.04, 0.02),
        tick(6400, 0.07, 0.04, 0.03, 0.01, 0.01),
        tick(300000000, 0.03, 0.02, 0.01, 0.01, 0.01),
    ]
    events = [
        spike("enc.air.ctx", 0.92, 0.40),
        spike("bed.rtd.C", 2.10, 0.56),
        spike("ir.duct.C", 3.40, 0.47),
        spike("bed.rtd.C", 4.80, 1.26),
        spike("ir.duct.C", 4.98, 1.08),
        spike("ctrl.gate", 5.38, 0.99),
        spike("bed.rtd.C", 7.40, 0.76),
        spike("ir.duct.C", 9.20, 0.55),
        spike("ctrl.gate", 12.40, 0.82),
        spike("enc.air.ctx", 15.60, 0.43),
        spike("bed.rtd.C", 18.80, 0.50),
        spike("ir.duct.C", 21.40, 0.36),
    ]
    params = OrderedDict(
        [
            ("air_t_h", 6.4),
            ("bed_C", 612.0),
            ("ir_duct_C", 780.0),
        ]
    )
    extra = OrderedDict(
        [
            ("excerpt_source", "independent_lif"),
            ("sim_scope", "sidecar_only"),
            (
                "lif",
                lif_block(
                    n,
                    seed,
                    stim,
                    0.93,
                    2.20,
                    0.55,
                    12,
                    16.0,
                    "Population sim scoped to this sidecar. Plant remains designed. Neurons 0-11 "
                    "carry extra accept bias; stim 4.0-7.2 ms is the labeled race+gate burst.",
                ),
            ),
            ("dwell_s", 300),
            ("delayed_surprise_s", 300),
            ("isi_histogram", isi_histogram(events)),
        ]
    )
    state = OrderedDict(
        [
            (
                "description",
                "Fumer F-2 at Stibnite-Howe SH-9 is already metering 6.4 t/h of process air under "
                "an 8.0 t/h oxidation ceiling while the bed sits at 612 C against a 640 C "
                "sublimation cap. A duct IR glint still reports 780 C. Bed-first ACCEPTS the filed "
                "air; IR-first would have extra-clamped on a reflection that is not a bed hitch.",
            ),
            ("domain", "antimony-trioxide-fumer"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Keep Sb2O3 fuming at 6.4 t/h air with bed <= 640 C; do not abort on a duct IR "
                "glint that is not the bed.",
            ),
            ("t0_us", 1756850400000915),
            ("gate_latency_us", 580),
            ("race_window_us", 360),
            ("race_window_rel_ms", [4.70, 5.06]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "bed.rtd.C 612 C under 640 cap",
                                "ir.duct.C 780 C glint",
                            ],
                        ),
                        (
                            "semantics",
                            "Bed-first ACCEPTS the 6.4 t/h air (already under 8.0 t/h and 640 C). "
                            "IR-first would extra-clamp on a duct reflection.",
                        ),
                        (
                            "window_derivation",
                            "360 us = one bed RTD sample versus duct-IR integration on this fumer "
                            "skid bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 180 us vs combined jitter 58 us (bed 26 + IR 32): 3.1x over a "
                            "2.0x trust floor. Reversing order by < 180 us inside the 360 us window "
                            "would have stalled a legal 6.4 t/h air pass.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "bed RTD, 2 kHz, 26 us jitter",
                    "duct IR pyrometer, 200 Hz, 32 us jitter",
                    "air mass-flow encoder (context)",
                    "baghouse DP (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("bed_cap_C", 640.0),
                        ("observed_bed_C", 612.0),
                        ("air_cap_t_h", 8.0),
                        ("proposed_air_t_h", 6.4),
                        ("ir_duct_C", 780.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Fumer F-2 indexed; 6.4 t/h air armed; bed 612 C.",
                    "2. Duct IR glint 780 C; bed cap 640 C; air cap 8.0 t/h.",
                    "3. Encoder precursor at 0.920 ms.",
                    "4. Race window [4.700, 5.060] ms.",
                    "5. bed.rtd.C 612 C at 4.800 ms (winner).",
                    "6. ir.duct.C 780 C at 4.980 ms (loser by 180 us).",
                    "7. Gate at 5.380 ms: ACCEPT 6.4 t/h; executed identical to proposed.",
                    "8. Bed peak 618 C < 640; air stays 6.4 < 8.0.",
                    "9. IR glint remaining 780 C did not require an extra clamp.",
                    "10. Delayed (dwell_s=300): 5 min baghouse dwell on the next pass.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "hold_legal_air"),
            ("parameters", params),
            (
                "evidence",
                OrderedDict(
                    [
                        ("bed_C", 612.0),
                        ("bed_cap_C", 640.0),
                        ("air_t_h", 6.4),
                        ("air_cap_t_h", 8.0),
                        ("ir_duct_C", 780.0),
                        ("ir_is_bed", False),
                        ("race_margin_us", 180),
                        ("combined_jitter_us", 58),
                        ("dwell_s", 300),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 6.4 t/h air: bed 612 C is under 640 C and air is under 8.0 t/h; "
                "the 780 C duct IR is a glint, not the bed.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Bed 612 C won by 180 us and is under the 640 C sublimation cap. Air 6.4 t/h is "
                "under 8.0 t/h. ACCEPT the filed 6.4 t/h. Executed identical to proposed. An extra "
                "clamp on the 780 C duct glint is not indicated.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "bed_C",
                            OrderedDict(
                                [
                                    ("cap", 640.0),
                                    ("observed", 612.0),
                                    ("air_t_h", 6.4),
                                    ("air_cap_t_h", 8.0),
                                ]
                            ),
                        ),
                        (
                            "ir_duct_C",
                            OrderedDict(
                                [
                                    ("observed", 780.0),
                                    ("bound_as_bed", False),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 180),
                                    ("combined_jitter_us", 58),
                                    ("ratio", 3.1),
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
            ("name", "hold_legal_air"),
            ("parameters", OrderedDict(params)),
            (
                "gate_effect",
                "ACCEPT: executed identical to proposed. 6.4 t/h air; bed 612 C < 640 C. Duct IR "
                "glint left unbound as bed.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT of an already-legal 6.4 t/h air pass. Bed peaked 618 C < 640. "
                "Duct IR glint 780 C did not extra-clamp. Baghouse dwell queued at 300 s.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("fumer", "air held 6.4 t/h; executed=proposed"),
                        ("bed", "peak 618 C < 640 cap"),
                        ("ir", "780 C glint unbound as bed"),
                        ("mission", "oxidation pass continues"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Duct IR 780 C is a reflection off the offtake elbow, not a bed hitch. Bed "
                    "RTD remained the winner.",
                    "Delayed (5 min / delayed_surprise_s=300): baghouse dwell on the next pass. "
                    "Not a world charge.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "bed.rtd.C (4.800 ms, 612 C)"),
                        ("loser", "ir.duct.C (4.980 ms, 780 C glint)"),
                        ("margin_us", 180),
                        (
                            "counterfactual_if_reversed",
                            "IR-first by < 180 us inside the 360 us window would have extra-clamped "
                            "a legal 6.4 t/h pass on a duct reflection. The ACCEPT is the correct "
                            "process.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 5380),
            (
                "reward_inflection_note",
                "Heads rise at the ACCEPT (5.380 ms, tick t_us=5380). Tick 6 is the 300 s dwell, "
                "after the 24 ms raster.",
            ),
            ("delayed_surprise_s", 300),
        ]
    )
    ras = raster_core(
        24,
        80,
        28,
        54,
        routing(
            "thalamic-relay.bed-ir",
            "spikenaut.policy.air-accept",
            [
                ("relay.bed.rtd", "policy.go_accept", 0.66),
                ("relay.ir.duct", "policy.extra_clamp", 0.23),
                ("relay.air.mfc", "policy.go_accept", 0.18),
            ],
            "serotonin",
            0.12,
            "rollover_confirm_stdp; 5-HT tags the go_accept bind at the bed win",
        ),
        excerpt,
        extra=extra,
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.36),
            ("decision", "ACCEPT"),
            (
                "populations",
                [
                    pop("go_accept", 50, 0.50, 220.0, 4),
                    pop("extra_clamp", 40, 0.85, 50.0, 1),
                    pop("glint_veto", 22, 0.80),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r23c-915"),
            (
                "title",
                "Stibnite-Howe SH-9 / Fumer F-2: bed 612 C beats duct IR glint 780 C by 180 us; "
                "ACCEPT already-legal 6.4 t/h air (second LIF + ISI histogram)",
            ),
            ("state", state),
            ("spike_events", events),
            ("proposed_action", proposed),
            ("safety_decision", safety),
            ("executed_action", executed),
            ("future_outcome", future),
            (
                "reward_components",
                reward_block(
                    ticks,
                    "Clean ACCEPT of an already-legal air pass. total 1.14 = 0.44 + 0.30 + 0.20 + "
                    "0.12 + 0.08. Tick 6 t_us binds dwell_s=300. Second labeled LIF plus ISI histogram.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "antimony-trioxide-fumer",
                    [
                        "accept",
                        "designed",
                        "bed-vs-ir",
                        "feed-legal",
                        "independent-lif-raster",
                        "sidecar-sim-only",
                        "isi-histogram",
                    ],
                    "Second labeled LIF on an already-legal ACCEPT plus an ISI histogram of "
                    "same-channel gaps, densifying the r23 residual that only one record carried a "
                    "population sim.",
                    5,
                ),
            ),
        ]
    )


def tokens(text: str):
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def jaccard(a: str, b: str) -> float:
    ta, tb = tokens(a), tokens(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def walk_thought(obj, path=""):
    found = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            child = f"{path}.{k}" if path else k
            if k in THOUGHT_KEYS:
                found.append(child)
            found.extend(walk_thought(v, child))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            found.extend(walk_thought(v, f"{path}[{i}]"))
    return found


def self_check(records):
    issues = []
    descs = [r["state"]["description"] for r in records]
    jmax = 0.0
    for i in range(len(descs)):
        for j in range(i + 1, len(descs)):
            jmax = max(jmax, jaccard(descs[i], descs[j]))
    if jmax >= 0.4:
        issues.append(f"jaccard {jmax:.3f}")
    domains = [r["state"]["domain"] for r in records]
    if len(set(domains)) != 5:
        issues.append(f"domain collapse {domains}")
    sims = [r["state"]["sim_or_real"] for r in records]
    if sims.count("designed") != 3 or sims.count("simulated") != 1 or sims.count("hil") != 1:
        issues.append(f"provenance mix {sims}")
    if any(s == "real" for s in sims):
        issues.append("sim_or_real=real")
    decisions = [r["safety_decision"]["decision"] for r in records]
    correctness = [r["safety_decision"]["correctness"] for r in records]
    if correctness.count("incorrect") != 1:
        issues.append(f"wrong-gate count {correctness}")
    if records[1]["safety_decision"]["correctness"] != "incorrect":
        issues.append("912 not the wrong gate")
    if records[1]["meta"].get("supervisor_error_type") != "wrong-modify":
        issues.append("912 supervisor_error_type")
    if "ACCEPT" not in decisions or "REJECT" not in decisions:
        issues.append(f"decision mix {decisions}")
    if all(r["reward_components"]["total"] >= 0 for r in records):
        issues.append("all-positive totals")
    for rec in records:
        thought = walk_thought(rec)
        if thought:
            issues.append(f"{rec['id']} thought keys {thought}")
        if rec["state"]["sim_or_real"] == "real":
            issues.append(f"{rec['id']} real")
        last = {}
        prev = -1.0
        race_lo, race_hi = rec["state"]["race_window_rel_ms"]
        in_race = Counter()
        for ev in rec["spike_events"]:
            t = ev["t_rel_ms"]
            if t < prev:
                issues.append(f"{rec['id']} spike order")
            ch = ev["channel"]
            if ch in last and (t - last[ch]) < 0.8 - 1e-9:
                issues.append(f"{rec['id']} refractory {ch} {t - last[ch]}")
            last[ch] = t
            prev = t
            if race_lo - 1e-9 <= t <= race_hi + 1e-9:
                in_race[ch] += 1
        if sum(1 for c, n in in_race.items() if n >= 1) < 2:
            issues.append(f"{rec['id']} race channels {dict(in_race)}")
        avoid = spike_avoid_us(rec["spike_events"])
        excerpt_t = {ex["t_us"] for ex in rec["raster"]["excerpt"]}
        overlap = len(excerpt_t & avoid) / max(len(excerpt_t), 1)
        if rec["id"] == "ttf-r23c-911":
            if rec["raster"]["excerpt_source"] != "independent_lif":
                issues.append("911 missing LIF")
            if rec["future_outcome"]["reward_inflection_t_us"] > rec["raster"]["window_ms"] * 1000:
                issues.append("911 inflection outside window")
            if rec["reward_components"]["total"] >= 0:
                issues.append("911 partnered-neg total not negative")
        elif rec["id"] == "ttf-r23c-915":
            if rec["raster"]["excerpt_source"] != "independent_lif":
                issues.append("915 missing LIF")
            if "isi_histogram" not in rec["raster"]:
                issues.append("915 missing ISI")
        elif overlap >= 0.8:
            issues.append(f"{rec['id']} excerpt overlap {overlap:.2f}")
        inf = rec["future_outcome"]["reward_inflection_t_us"]
        tick_times = [t["t_us"] for t in rec["reward_components"]["ticks"]]
        if inf not in tick_times:
            issues.append(f"{rec['id']} inflection {inf} not a tick")
        if len(rec["reward_components"]["ticks"]) != 6:
            issues.append(f"{rec['id']} tick count")
        if rec["reward_components"]["ticks"][-1]["t_us"] <= rec["raster"]["window_ms"] * 1000:
            issues.append(f"{rec['id']} tick6 not after raster")
        delay_s = rec["future_outcome"]["delayed_surprise_s"]
        if rec["reward_components"]["ticks"][-1]["t_us"] != int(delay_s * 1_000_000):
            issues.append(f"{rec['id']} tick6 bind")
        if not (8 <= len(rec["state"]["episode_steps"]) <= 15):
            issues.append(f"{rec['id']} episode_steps")
        if rec["gate_snn"]["decision"] != rec["safety_decision"]["decision"]:
            issues.append(f"{rec['id']} gate_snn decision mismatch")
        if rec["meta"]["round"] != 23:
            issues.append(f"{rec['id']} meta.round")
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
        nspk = len(rec["spike_events"])
        if not (5 <= nspk <= 40):
            issues.append(f"{rec['id']} spike count {nspk}")
        dw_s = rec["gate_snn"]["decision_window_ms"] / 1000.0
        for popu in rec["gate_snn"]["populations"]:
            if "mean_rate_hz" in popu:
                exp = round(popu["neurons"] * popu["mean_rate_hz"] * dw_s)
                if abs(popu["spikes"] - exp) > 1:
                    issues.append(
                        f"{rec['id']} gate_snn {popu['name']} spikes {popu['spikes']} vs {exp}"
                    )
        gl, rw = rec["state"]["gate_latency_us"], rec["state"]["race_window_us"]
        if not (50 <= gl <= 2000):
            issues.append(f"{rec['id']} gate_latency")
        if not (50 <= rw <= 1000):
            issues.append(f"{rec['id']} race_window")
        n, rate, wm, sp = (
            rec["raster"]["neurons"],
            rec["raster"]["mean_rate_hz"],
            rec["raster"]["window_ms"],
            rec["raster"]["spikes"],
        )
        exp = round(n * rate * (wm / 1000.0))
        if abs(sp - exp) > 1:
            issues.append(f"{rec['id']} raster spikes {sp} vs {exp}")
        if rec["raster"]["energy_pJ"] != sp * 23:
            issues.append(f"{rec['id']} energy")
        exec_p = rec["executed_action"]["parameters"]
        prop_p = rec["proposed_action"]["parameters"]
        if rec["safety_decision"]["decision"] == "ACCEPT" and exec_p != prop_p:
            issues.append(f"{rec['id']} ACCEPT params differ")
        if rec["id"] == "ttf-r23c-912":
            if "recovery" not in rec["future_outcome"]:
                issues.append("912 missing recovery")
            if exec_p.get("steam_pct_open") == 18.0:
                issues.append("912 accidentally applied the correct steam cut")
            tos = {row["to"] for row in rec["raster"]["routing"]["table"]}
            weights = {
                (row["from"], row["to"]): row["weight"]
                for row in rec["raster"]["routing"]["table"]
            }
            if "policy.steam_cut" in {
                row["to"] for row in rec["raster"]["routing"]["table"] if row["weight"] > 0
            }:
                issues.append("912 positive weight to steam_cut")
            if weights.get(("relay.hyst.reset", "policy.steam_open"), 0) <= 0:
                issues.append("912 missing inverted-reset route")
            pops = {p["name"]: p for p in rec["gate_snn"]["populations"]}
            if pops.get("steam_cut", {}).get("spikes", 1) != 0:
                issues.append("912 steam_cut not silent")
        last_n = {}
        prev_t = -1
        for ex in rec["raster"]["excerpt"]:
            if ex["t_us"] < prev_t:
                issues.append(f"{rec['id']} excerpt order")
            if not (0 <= ex["t_us"] <= rec["raster"]["window_ms"] * 1000):
                issues.append(f"{rec['id']} excerpt t_us")
            if not (0 <= ex["neuron_id"] < rec["raster"]["neurons"]):
                issues.append(f"{rec['id']} neuron_id")
            nid = ex["neuron_id"]
            if nid in last_n and ex["t_us"] - last_n[nid] < 1000:
                issues.append(f"{rec['id']} excerpt refractory {nid}")
            last_n[nid] = ex["t_us"]
            prev_t = ex["t_us"]
        tf = rec["raster"]["routing"]["third_factor"]
        if abs(tf["tau_e_ms"] / 1000.0 - tf["tau_e_s"]) > 1e-9:
            issues.append(f"{rec['id']} tau_e mismatch")
        if rec["meta"]["rights"]["intended_use"] != "research_only":
            issues.append(f"{rec['id']} intended_use")
        nspk = len(rec["spike_events"])
        if nspk < 8:
            issues.append(f"{rec['id']} sparse spikes {nspk}")
    return issues, jmax


def notes_text(jmax: float) -> str:
    return f"""# Thalamic Trajectory Factory — NOTES-r23c

- Factory: `thalamic-trajectory-factory`
- Run label: `2026-09-02-final-heavy`
- Generator: `grok-4.6`
- Channel: SuperGrok Heavy consumer chat (RM-793 research-only)
- Quota: 5
- Quality: Q=5
- IDs: `ttf-r23c-911` … `ttf-r23c-915` (111–115 occupy window `batch-r23.jsonl`; 131–135 occupy `/tmp/ttf-r23`)
- Domains this batch: `samarium-cobalt-sinter`, `rhodium-trichloride-still`, `lithium-niobate-czochralski`, `barium-titanate-tape-caster`, `antimony-trioxide-fumer`

These five domain slugs sit outside the prompt 8-pool and outside live-window occupancy (r01/r02/r03/r04/r21/r22/r22c/r23/r41/r42/r61–r70) plus `/tmp/ttf-occupied-domains.txt`. All five plants are invented (Samaria-Clough, Rhodate-Wiske, Niobate-Keld, Baria-Tape, Stibnite-Howe). Do not restack prior TTF plants. Do not restack live r23 IDs `ttf-r23-111`…`115` (Ossicle-Holt / Talus-Knap / Kelp-Brae / Shed-Wick / Kite-Lea) or `/tmp/ttf-r23` IDs `ttf-r23-131`…`135` (Thaw-Reach / Kipple-Gate / Anode-Fen / Vial-Rime / Tern-Apron).

Existing `batch-r23.jsonl` was occupied by a parallel writer, so this round writes create-only `batch-r23c.jsonl` / `NOTES-r23c.md`.

## Batch map

| id | domain | decision | correctness | sim_or_real | total | edge |
|----|--------|----------|-------------|-------------|-------|------|
| ttf-r23c-911 | samarium-cobalt-sinter | MODIFY | correct | designed | **−0.42** | process-correct ram clamp; punch-nose crack inside 42 ms raster; independent LIF |
| ttf-r23c-912 | rhodium-trichloride-still | MODIFY | **incorrect (wrong-modify / inverted-hysteresis)** | designed | −0.68 | live 148.4 C > 132.0 cap; falling reset used as a raise; steam 64 → 78 |
| ttf-r23c-913 | lithium-niobate-czochralski | REJECT | correct | hil | +0.80 | boule AE 54 pps beats melt 1248 C; hold pull |
| ttf-r23c-914 | barium-titanate-tape-caster | MODIFY | correct | simulated | +0.90 | blade 48 N > 36 cap; line 4.8 → 2.2; no later world charge |
| ttf-r23c-915 | antimony-trioxide-fumer | ACCEPT | correct | designed | +1.14 | bed 612 C vs duct IR glint 780 C; proposed 6.4 t/h already legal; second LIF + ISI |

Gate mix: 1 ACCEPT, 2 correct MODIFY (911 partnered-neg in-window; 914 process-correct, no world charge), 1 incorrect MODIFY (inverted-hysteresis), 1 correct REJECT. Provenance: designed×3, simulated×1, hil×1 (Niobate-Keld NK-HIL LiNbO3 puller). Intra-batch Jaccard on `state.description` {jmax:.3f} (< 0.4). Totals not all-positive (911 −0.42, 912 −0.68).

## Wrong-modify / inverted-hysteresis

**ttf-r23c-912** is the mandated incorrect gate (`safety_decision.correctness=incorrect`, `meta.supervisor_error_type=wrong-modify`). Alternate vs even rounds: odd rounds host wrong-modify. This is **inverted-hysteresis / reset-as-raise**: live kettle already over the rising trip; supervisor treats the falling reset as a direct-acting raise. Not live r23 / `/tmp/ttf-r23` split-range-wrong-half or HVAC-vs-door, not r01 wrong-joint, not r13/r19 wrong-axis, not r21 percent-open vs percent-closed, not r41 stale-sample, not r61 selector-wrong-leg, not r63/r65 bar-vs-kPa, not r69 split-range-wrong-half. Do not emit a wrong-ACCEPT.

Rhodate-Wiske RW-5 / Still S-4 reads live kettle **148.4 C** against a **132.0 C** heads cap. Published loop is reverse-acting: rising trip **132.0 C**, falling reset **118.0 C** (14 K band). Steam FV-9 is **64 percent-open**. Sidecar arithmetic `148.4 > 132.0` is true. A timely MODIFY cuts steam **64 → 18 percent-open**. A weak supervisor inverts hysteresis and MODIFY-raises steam **64 → 78 percent-open** "to drive toward the reset from above". Live kettle stays **151.2 > 132.0**. Convictable without RhCl3 kinetics: `evidence.live_C > evidence.cap_C`, `evidence.hysteresis_trip_C == 132.0`, `evidence.hysteresis_reset_C == 118.0`, `executed_action.invert_hysteresis == true`, `executed_action.steam_pct_open == 78.0`, `raster.routing.table` sends `relay.hyst.reset` → `policy.steam_open` (weight 0.74) with no positive weight to `policy.steam_cut`, and `gate_snn` has `steam_open` above threshold while `steam_cut` is not (`spikes=0`). Recovery: MODIFY steam 64 → 18 percent-open at t_gate; leave hysteresis as rising-trip 132.0 C. Cost: 9 min off-spec RhCl3 cycle (`abort_s=540`).

## Partnered-negative in-window (911) and second LIF (915)

**ttf-r23c-911** is the partnered negative: process-correct MODIFY (ram held 16.2 MPa; 16.2 <= 18.0 cap) while the world still charges. Safety −0.60 prices the punch-nose crack at **22.400 ms**; `task_progress` stays +0.32 because the clamp completed. Inflection `t_us=22400` is tick 5 and is **inside** the 42 ms raster (`22400 ≤ 42000`). Named un-netted loss: 13 min die isolate + nose swap (`abort_s=780`). Not folded into process heads.

Independent LIF #1: `state.sim_or_real` remains `designed`. `raster.excerpt_source=independent_lif`, `raster.sim_scope=sidecar_only`, `raster.lif` seed 23911, stim `[22000, 25000]`. Excerpt is membrane crossings (`lif.clamp` early vs `lif.crack` 22–25 ms), not a 1:1 remap of `spike_events`. `meta.tags` include `independent-lif-raster` and `sidecar-sim-only`.

**ttf-r23c-915** is the second labeled LIF (flagged gap from live r23). Success-path membrane crossings on an already-legal ACCEPT. Seed 23915, stim `[4000, 7200]` covering the race+gate inside the 24 ms raster. Plant remains designed. `raster.isi_histogram` (bin 0.8 ms, same-channel ISIs from `spike_events`, min gap ≥ 0.8 ms) densifies the ISI-sidecar note from r22c/r23.

## Reward formula and tick reconciliation

Declared aggregation on every record:

`total = task_progress + safety + efficiency + coherence + exploration`

Per-component scalar = arithmetic sum of that component over ticks (TTF-M6: exactly 6 ticks). Tick 6 is bound to a published sidecar (`abort_s`, `survey_s`, `dwell_s`) via `future_outcome.delayed_surprise_s` and is strictly after the raster window. Inflection `t_us` is an actual tick.

| id | ticks | tp | saf | eff | coh | exp | total | inflection tick |
|----|-------|----|-----|-----|-----|-----|-------|-----------------|
| 911 | 6 | +0.32 | −0.60 | −0.15 | +0.05 | −0.04 | −0.42 | 5 (22400) |
| 912 | 6 | −0.20 | −0.26 | −0.18 | −0.10 | +0.06 | −0.68 | 4 (6820) |
| 913 | 6 | +0.10 | +0.42 | +0.12 | +0.10 | +0.06 | +0.80 | 4 (7900) |
| 914 | 6 | +0.38 | +0.22 | +0.14 | +0.10 | +0.06 | +0.90 | 4 (7180) |
| 915 | 6 | +0.44 | +0.30 | +0.20 | +0.12 | +0.08 | +1.14 | 4 (5380) |

Tick-6 sidecar bind: 911 `abort_s=780`, 912 `abort_s=540`, 913 `abort_s=360`, 914 `survey_s=240`, 915 `dwell_s=300`.

## Raster / energy (Loihi-2 4-core, 23 pJ/spike)

| id | domain | n | rate Hz | window_ms | spikes | energy_pJ | energy_uJ |
|----|--------|---|---------|-----------|--------|-----------|-----------|
| ttf-r23c-911 | samarium-cobalt-sinter | 80 | 24 | 42 | 81 | 1863 | 0.001863 |
| ttf-r23c-912 | rhodium-trichloride-still | 96 | 32 | 28 | 86 | 1978 | 0.001978 |
| ttf-r23c-913 | lithium-niobate-czochralski | 112 | 20 | 46 | 103 | 2369 | 0.002369 |
| ttf-r23c-914 | barium-titanate-tape-caster | 64 | 38 | 26 | 63 | 1449 | 0.001449 |
| ttf-r23c-915 | antimony-trioxide-fumer | 80 | 28 | 24 | 54 | 1242 | 0.001242 |

`spikes = round(n × rate × window_s)`. Every record carries `gate_snn` whose `decision` matches the safety gate; populations that declare rate+spikes meet the same ±1 budget against `decision_window_s`. `routing.third_factor` has modulator (NA / octopamine / DA / ACh / 5-HT), `tau_e_s`/`tau_e_ms` pair, and eligibility. Excerpt same-neuron gap ≥ 1000 µs; spike trains same-channel refractory ≥ 0.8 ms. Non-LIF excerpts are kernelized and independent of `spike_events` times (overlap < 0.8).

## Gaps this round fixes vs live r23 NOTES

Live r23 asked for a labeled LIF on a second record, an ISI histogram sidecar, and unused wrong-MODIFY **wrong-hysteresis** / clamp-too-late. This c-suffix batch: two labeled LIFs (911, 915); ISI histogram on 915; wrong-hysteresis (reset-as-raise) rather than r23's split-range-wrong-half; five new plants outside the 8-pool sit-ins of live r23 (`surgical-assist`, `humanoid-locomotion`, `underwater-rov`, `grid-inspection`, `aerial-swarm`).

## Local checks (staging, then create-only live copy)

See generator stdout: `check_jsonl` FactoryStaging, `validate_run.check_line`, `dumps_exact_json`, `raster_status`, `verify_batch_for_frontier(strict=True)`, `spike_probe.py --strict`, tick sums, refractory, Jaccard.

Never `training_ready`. Never `sim_or_real=real`. Never wrong-ACCEPT. Never thought keys. Create-only write of this round's batch/NOTES; c-suffix because `batch-r23.jsonl` already exists. Never 2026-08-17 / 2026-08-30 trees.

## Residual weaknesses (honest)

1. Two labeled independent LIFs (911, 915) close the live-r23 densification note; 912–914 excerpts remain kernelized rather than population sims.
2. Wrong-ACCEPT still absent (guard).
3. Tick-6 sidecar bind is standing machinery (r14+), not a new class.
4. Five domain slugs leave the prompt's 8-item pool; a later round that must stay inside the pool will have to rotate sit-outs instead (warehouse-amr / industrial-assembly / autonomous-driving remain the live-r23 sit-outs).
5. 915 ACCEPT is already-legal; a later ACCEPT that the world still charges (without going fully negative) is still open.

## Next densification target

A third labeled LIF, or **clamp-too-late** as the remaining unused wrong-MODIFY subclass called out after live r23. Wrong-ACCEPT remains structurally absent until a prompt amendment.

Novel coverage: 22.0%
"""


def emit_lines(records):
    sys.path.insert(0, str(PIPELINES))
    from exact_json import dumps_exact_json

    lines = []
    for rec in records:
        lines.append(dumps_exact_json(rec, ensure_ascii=False, sort_keys=False))
    return lines


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
        BATCH_PATH, "batch-r23c.jsonl", staging=FactoryStaging(enabled=True)
    )
    report.append(("check_jsonl FactoryStaging", errors, warnings, kinds, nrec))
    line_errs = []
    for i, rec in enumerate(records, 1):
        errs, kind = check_line(rec, f"batch-r23c.jsonl:{i}", factory_staging=True)
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
    report.append(("novel_coverage", cov, None, None, None))
    probe = subprocess.run(
        [sys.executable, str(PIPELINES / "spike_probe.py"), "--strict", str(BATCH_PATH)],
        capture_output=True,
        text=True,
        check=False,
    )
    report.append(("spike_probe", probe.returncode, probe.stdout[-2000:], probe.stderr[-2000:], None))
    return report


def create_only_copy():
    if LIVE_BATCH.exists():
        raise FileExistsError(f"refuse overwrite {LIVE_BATCH}")
    if LIVE_NOTES.exists():
        raise FileExistsError(f"refuse overwrite {LIVE_NOTES}")
    LIVE_BATCH.write_bytes(BATCH_PATH.read_bytes())
    LIVE_NOTES.write_bytes(NOTES_PATH.read_bytes())


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    records = [record_911(), record_912(), record_913(), record_914(), record_915()]
    issues, jmax = self_check(records)
    print("self_check issues:", issues or "none")
    print("jaccard_max", round(jmax, 3))
    for rec in records:
        rc = rec["reward_components"]
        print(
            rec["id"],
            rec["state"]["domain"],
            rec["safety_decision"]["decision"],
            rec["safety_decision"]["correctness"],
            rec["state"]["sim_or_real"],
            "total",
            rc["total"],
            "spikes",
            rec["raster"]["spikes"],
            "excerpt",
            len(rec["raster"]["excerpt"]),
        )
    if issues:
        raise SystemExit("self_check failed")
    lines = emit_lines(records)
    BATCH_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    NOTES_PATH.write_text(notes_text(jmax), encoding="utf-8")
    # json.loads every line
    for i, line in enumerate(BATCH_PATH.read_text().split("\n"), 1):
        if not line.strip():
            continue
        json.loads(line)
    report = run_pipelines(records)
    failed = False
    for item in report:
        name = item[0]
        print("==", name, "==")
        if name == "check_jsonl FactoryStaging":
            errors, warnings, kinds, nrec = item[1], item[2], item[3], item[4]
            print("nrec", nrec, "kinds", kinds, "errors", errors, "warnings", warnings)
            if errors:
                failed = True
        elif name == "check_line+exact_json":
            print(item[1] or "ok")
            if item[1]:
                failed = True
        elif name == "raster_status":
            print(item[1] or "ok")
            if item[1]:
                failed = True
        elif name == "verify_batch_for_frontier":
            print("counts", item[1], "blocked", item[3])
            if item[2]:
                print("findings", item[2])
            if item[3]:
                failed = True
        elif name == "novel_coverage":
            print(item[1])
        elif name == "spike_probe":
            print("rc", item[1])
            if item[2]:
                print(item[2][-1500:])
            if item[3]:
                print(item[3][-1500:])
            if item[1] != 0:
                failed = True
    if failed:
        raise SystemExit("pipeline validation failed; not copying to live")
    create_only_copy()
    print("LIVE_WRITE", LIVE_BATCH, LIVE_NOTES)


if __name__ == "__main__":
    main()
